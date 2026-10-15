#!/usr/bin/env python3
"""Verify a checked-in R2 directory; preserve the source and reuse R2 checks.

This adapter changes input handling only. Native results are newly generated
in --out. A PASS is not electrical, bench, independent-review or production approval.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
import verify_r2 as core


def inventory(root: Path) -> dict:
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Missing project directory or symbolic-link root: ' + str(root))
    result = {}
    total = 0
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symbolic links are not accepted: ' + str(path))
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError('Not a regular project file: ' + str(path))
        size = path.stat().st_size
        total += size
        if total > 100 * 1024 * 1024 or len(result) >= 10000:
            raise ValueError('Project exceeds the input safety limit')
        result[path.relative_to(root).as_posix()] = {'size': size, 'sha256': core.sha256(path)}
    if core.SCHEMATIC not in result:
        raise ValueError('Root schematic is missing: ' + core.SCHEMATIC)
    for name in ('source_contract.json', 'BOM.csv', 'firmware_definitions.json',
                 'Firmware_Definitions.h', 'sym-lib-table', 'fp-lib-table'):
        if name not in result:
            raise ValueError('Required project file is missing: ' + name)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--expected-kicad', default='8.0.9')
    parser.add_argument('--work', type=Path, default=Path('.kicad-ci-work'))
    parser.add_argument('--out', type=Path, default=Path('reports'))
    args = parser.parse_args()
    source, work, out = args.project.absolute(), args.work.resolve(), args.out.resolve()
    if (source == work or source == out or work == out or
            source in work.parents or source in out.parents or
            work in source.parents or out in source.parents or
            work in out.parents or out in work.parents):
        parser.error('Project, work and report directories must be disjoint')
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'verification_summary.json').exists():
        print('Refusing to overwrite prior verification evidence', file=sys.stderr)
        return 2
    checks = core.Checks()
    manifest = None
    summary = {
        'status': 'UNVERIFIED', 'input_mode': 'repository_directory',
        'input_directory': str(source),
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'commit_sha': os.environ.get('GITHUB_SHA'), 'branch_ref': os.environ.get('GITHUB_REF'),
        'run_id': os.environ.get('GITHUB_RUN_ID'), 'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
        'adapter_sha256': core.sha256(Path(__file__)),
        'checker_sha256': core.sha256(Path(core.__file__)),
        'limits': dict(core.LIMITS), 'commands': {},
    }
    try:
        manifest = inventory(source)
        (out / 'input_manifest.json').write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        summary['input_file_count'] = len(manifest)
        if work.exists():
            raise RuntimeError('Work directory exists; refusing stale-output reuse')
        shutil.copytree(source, work)
        if inventory(work) != manifest:
            raise RuntimeError('Working copy differs from the checked-in source')
        schematic = work / core.SCHEMATIC
        exe = shutil.which('kicad-cli')
        if not exe:
            raise RuntimeError('kicad-cli is not installed; native verification has not run')
        version = subprocess.run([exe, 'version'], capture_output=True, text=True,
                                 check=True, timeout=30).stdout.strip()
        summary['kicad_version'] = version
        (out / 'kicad-version.txt').write_text(version + '\n', encoding='utf-8')
        if not re.match(re.escape(args.expected_kicad) + r'(?:$|[^0-9.])', version):
            raise RuntimeError('KiCad baseline version mismatch: ' + version)
        netlist, erc = out / 'verified_netlist.xml', out / 'erc_report.json'
        if netlist.exists() or erc.exists():
            raise RuntimeError('Refusing to reuse existing native output')
        net_code = core.run_command(
            [exe, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(netlist), str(schematic)],
            work, out / 'netlist-export.log')
        erc_code = core.run_command(
            [exe, 'sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations',
             '-o', str(erc), str(schematic)], work, out / 'erc.log')
        summary['commands'] = {'native_netlist_exit_code': net_code, 'native_erc_exit_code': erc_code}
        checks.require(net_code == 0 and netlist.is_file(), 'native netlist export succeeded', net_code)
        checks.require(erc_code == 0 and erc.is_file(), 'native ERC succeeded without violations', erc_code)
        if net_code == 0 and netlist.is_file():
            model = json.loads((work / 'source_contract.json').read_text(encoding='utf-8'))
            root, components, native, counts = core.compare_native(model, netlist, checks)
            summary['counts'] = counts
            checks.require(Path(root.findtext('./design/source', '')).resolve() == schematic.resolve(),
                           'native XML source path', root.findtext('./design/source'))
            core.compare_bom(work, components, checks)
            core.compare_firmware(work, components, native, checks)
        if erc.is_file():
            report = json.loads(erc.read_text(encoding='utf-8'))
            sheets = report.get('sheets')
            checks.require(isinstance(sheets, list) and bool(sheets), 'ERC has sheet results')
            violations = [v for sheet in (sheets or []) for v in sheet.get('violations', [])]
            summary['erc'] = {'sheet_count': len(sheets or []), 'violation_count': len(violations),
                              'severity_counts': dict(Counter(v.get('severity', 'unspecified') for v in violations))}
            checks.require(not violations, 'ERC violations including exclusions', violations)
        changed = [name for name, item in manifest.items()
                   if not (work / name).is_file() or core.sha256(work / name) != item['sha256']]
        checks.require(not changed, 'working source files unchanged by verification', changed)
    except Exception as exc:
        checks.errors.append({'check': 'execution or input error', 'detail': str(exc)})
        (out / 'exception.log').write_text(traceback.format_exc(), encoding='utf-8')
        print(traceback.format_exc(), file=sys.stderr)
    finally:
        if manifest is not None:
            try:
                checks.require(inventory(source) == manifest, 'checked-in project unchanged')
            except Exception as exc:
                checks.errors.append({'check': 'source integrity after verification', 'detail': str(exc)})
    summary['checks_executed'] = checks.executed
    summary['errors'] = checks.errors
    summary['status'] = 'FAIL_OR_UNVERIFIED' if checks.errors else 'SCHEMATIC_CHECKS_PASS_HARDWARE_HOLD'
    summary['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (out / 'verification_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    brief = f"Status: {summary['status']}\nChecks: {checks.executed}\nIssues: {len(checks.errors)}\nProduction: HOLD\n"
    (out / 'SUMMARY.txt').write_text(brief, encoding='utf-8')
    print(brief, flush=True)
    for issue in checks.errors[:30]:
        print(json.dumps(issue, ensure_ascii=False), flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write('## R2 directory verification\n\n```text\n' + brief + '```\n')
            stream.write('This is not hardware, independent-review or production approval.\n')
    return 1 if checks.errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
