#!/usr/bin/env python3
"""Run fresh KiCad exports and check the approved R2 contract. No source writes.

Requires Python 3.10+ and kicad-cli 8.0.9. Only the standard library is used.
This checks stored intent against a native export; it is NOT electrical-rating,
physical-pinout, PCB, timing, calibration, or bench-performance approval.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timezone

SCHEMATIC = 'DDI_Phase2_2_R2.kicad_sch'
EXPECTED_RAILS = {'VDDI_DIG', 'VDDI', 'VDDI_LPDP', 'VDDI_OSC', 'VCI',
                  'AVDDH1', 'AVDDH2_S_O', 'AVDDH2_GM', 'VGH1', 'VGH2', 'VGL1', 'VGL2'}
LIMITS = {
    'hardware_performance_and_5uA_accuracy': 'UNVERIFIED',
    'manufacturer_physical_pinout_and_component_ratings': 'UNVERIFIED',
    'firmware_timing_register_math_and_actual_I2C_straps': 'UNVERIFIED',
    'physical_Kelvin_copper_and_PCB_DRC': 'UNVERIFIED',
    'production_release': 'HOLD',
    'independent_reviewer': 'NOT_PERFORMED',
}

class Checks:
    def __init__(self):
        self.errors: list[dict] = []
        self.executed = 0
    def require(self, condition: bool, check: str, detail=None):
        self.executed += 1
        if not condition:
            self.errors.append({'check': check, 'detail': detail})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_value(value: str) -> str:
    # A DNP annotation in Value is allowed; Population and native DNP are checked separately.
    return re.sub(r'\s*\[DNP\]', '', value, flags=re.I).strip()


def index_rows(rows: list[dict], key: str, checks: Checks, label: str) -> dict:
    result = {}
    for row in rows:
        k = str(row.get(key, ''))
        checks.require(bool(k) and k not in result, label + ': unique key', k)
        result[k] = row
    return result


def contract_graph(model: dict, checks: Checks):
    components = index_rows(model['components'], 'ref', checks, 'contract')
    net_rows = index_rows(model['nets'], 'name', checks, 'contract nets')
    pin_graph: dict[str, set[str]] = {}
    nc = set()
    for ref, component in components.items():
        seen = set()
        for pin in component['pins']:
            number = str(pin['number'])
            checks.require(number not in seen, 'duplicate contract pin', ref + '.' + number)
            seen.add(number)
            node = ref + '.' + number
            if pin['net'] == 'NC':
                if not ref.startswith('#'): nc.add(node)
            else:
                pin_graph.setdefault(pin['net'], set()).add(node)
    listed = {name: set(row['nodes']) for name, row in net_rows.items()}
    checks.require(set(listed) == set(pin_graph), 'contract net declarations',
                   sorted(set(listed) ^ set(pin_graph)))
    for name in set(listed) | set(pin_graph):
        checks.require(listed.get(name, set()) == pin_graph.get(name, set()),
                       'contract pin/net consistency', name)
    expected = {name: {node for node in nodes if not node.startswith('#')}
                for name, nodes in listed.items()}
    # Check declared copper bridges without electrically merging the two logical nets.
    for bridge in model.get('copper_bridges', []):
        ref = bridge['ref']
        pins = bridge.get('pins', [])
        nets = bridge.get('nets', [])
        checks.require(len(pins) == len(nets), 'bridge shape', bridge)
        pin_map = {str(p['number']): p['net'] for p in components.get(ref, {}).get('pins', [])}
        for pin, net in zip(pins, nets):
            checks.require(pin_map.get(str(pin)) == net, 'bridge pin/net declaration',
                           {'ref': ref, 'pin': pin, 'expected_net': net, 'actual_net': pin_map.get(str(pin))})
    return components, expected, nc


def parse_native(path: Path, checks: Checks):
    root = ET.parse(path).getroot()
    checks.require(root.tag == 'export', 'native XML export root', root.tag)
    components = {}
    for comp in root.findall('./components/comp'):
        ref = comp.attrib['ref']
        checks.require(ref not in components, 'duplicate native component', ref)
        fields = {f.attrib['name']: f.text or '' for f in comp.findall('./fields/field')}
        props = {p.attrib['name']: p.attrib.get('value', '') for p in comp.findall('property')}
        components[ref] = {'Value': comp.findtext('value', ''), 'fields': fields,
                           'dnp': 'dnp' in props and props['dnp'].lower() not in ('false', '0', 'no')}
    nets = {}
    node_net = {}
    for net in root.findall('./nets/net'):
        full_name = net.attrib['name']
        name = full_name.rstrip('/').rsplit('/', 1)[-1]
        checks.require(name not in nets, 'duplicate normalized native net', full_name)
        nodes = []
        for node in net.findall('node'):
            n = node.attrib['ref'] + '.' + node.attrib['pin']
            checks.require(n not in node_net, 'native pin appears more than once', n)
            node_net[n] = name
            nodes.append(n)
        nets[name] = set(nodes)
    return root, components, nets


def compare_native(model: dict, native: Path, checks: Checks):
    components, expected, nc = contract_graph(model, checks)
    root, actual_components, actual = parse_native(native, checks)
    refs = {r for r in components if not r.startswith('#')}
    checks.require(refs == set(actual_components), 'native component set',
                   {'missing': sorted(refs - set(actual_components)),
                    'extra': sorted(set(actual_components) - refs)})
    for name, nodes in expected.items():
        found = actual.get(name, set())
        checks.require(nodes == found, 'native named-net mismatch',
                       {'net': name, 'missing': sorted(nodes - found), 'extra': sorted(found - nodes)})
    extra = {name: nodes for name, nodes in actual.items() if name not in expected}
    actual_nc = set()
    for name, nodes in extra.items():
        checks.require(name.startswith('unconnected-') and len(nodes) == 1,
                       'unexpected native net', {'net': name, 'nodes': sorted(nodes)})
        actual_nc.update(nodes)
    checks.require(actual_nc == nc, 'native NC set',
                   {'missing': sorted(nc - actual_nc), 'extra': sorted(actual_nc - nc)})
    for ref in refs & set(actual_components):
        src, dst = components[ref], actual_components[ref]
        checks.require(normalized_value(src['Value']) == normalized_value(dst['Value']),
                       'native Value', {'ref': ref, 'expected': src['Value'], 'actual': dst['Value']})
        for name in ('MPN', 'Population', 'Manufacturer'):
            checks.require(src.get(name, '') == dst['fields'].get(name, ''),
                           'native ' + name, {'ref': ref, 'expected': src.get(name), 'actual': dst['fields'].get(name)})
        checks.require((src['Population'] == 'DNP') == dst['dnp'], 'native DNP flag', ref)
        checks.require(src.get('Footprint', '') == dst['fields'].get('RequestedFootprint', ''),
                       'native RequestedFootprint', ref)
    return root, components, actual_components, {
        'contract_components_including_virtual': len(components),
        'native_components_excluding_power_flags': len(actual_components),
        'contract_named_nets': len(expected), 'native_nets': len(actual),
        'contract_NC_pins': len(nc), 'native_NC_pins': len(actual_nc),
        'copper_bridge_declarations': len(model.get('copper_bridges', [])),
    }


def compare_bom(project: Path, components: dict, checks: Checks):
    with (project / 'BOM.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = index_rows(list(csv.DictReader(f)), 'RefDes', checks, 'BOM')
    checks.require(set(rows) == set(components), 'BOM reference set', sorted(set(rows) ^ set(components)))
    for ref in set(rows) & set(components):
        for column, key in [('Value', 'Value'), ('MPN', 'MPN'), ('Population', 'Population'),
                            ('RequestedFootprint', 'Footprint'), ('Manufacturer', 'Manufacturer')]:
            a, b = rows[ref].get(column, ''), str(components[ref].get(key, ''))
            if column == 'Value': a, b = normalized_value(a), normalized_value(b)
            checks.require(a == b, 'BOM field mismatch', {'ref': ref, 'field': column, 'bom': a, 'contract': b})


def ohms(value: str) -> float:
    value = normalized_value(value).replace('Ω', '').replace(' ', '')
    if re.fullmatch(r'\d+R\d+', value, re.I): value = re.sub('[Rr]', '.', value)
    elif value.lower().endswith('r'): value = value[:-1]
    return float(value)


def compare_firmware(project: Path, components: dict, native: dict, checks: Checks):
    firmware = json.loads((project / 'firmware_definitions.json').read_text(encoding='utf-8'))
    rows = index_rows(firmware['channels'], 'ref', checks, 'firmware')
    ina_refs = {r for r, c in components.items() if c.get('MPN', '').startswith('INA228')}
    checks.require(set(rows) == ina_refs, 'firmware INA reference set', sorted(set(rows) ^ ina_refs))
    checks.require({c['rail'] for c in rows.values()} == EXPECTED_RAILS and len(rows) == len(EXPECTED_RAILS),
                   'approved 12-channel rail set', sorted(c['rail'] for c in rows.values()))
    addresses = [(c['bus'], c['address_7bit']) for c in rows.values()]
    checks.require(len(set(addresses)) == len(addresses), 'firmware address uniqueness', addresses)
    for ref, row in rows.items():
        shunt = row['shunt_ref']
        checks.require(shunt in native, 'native firmware shunt exists', shunt)
        if shunt in native:
            checks.require(math.isclose(ohms(native[shunt]['Value']), row['R_ohm'], rel_tol=1e-12),
                           'native shunt vs firmware', {'ref': ref, 'shunt': shunt})
    # Compare the generated C channel table to JSON, not to assumed IC behavior.
    header = (project / 'Firmware_Definitions.h').read_text(encoding='utf-8')
    pattern = re.compile(r'\{\s*"(U\d+)"\s*,\s*"([^"]+)"\s*,([^{}]+)\}')
    parsed = {}
    keys = ['bus', 'address_7bit', 'R_ohm', 'CURRENT_LSB_A', 'ADC_CONFIG', 'SHUNT_CAL', 'SOVL']
    for ref, rail, payload in pattern.findall(header):
        parts = [p.strip().rstrip('uUlL') for p in payload.split(',')]
        checks.require(ref not in parsed and len(parts) == len(keys), 'C channel row format', ref)
        if len(parts) != len(keys): continue
        vals = [float(p) if i in (2, 3) else int(p, 0) for i, p in enumerate(parts)]
        parsed[ref] = {'rail': rail, **dict(zip(keys, vals))}
    checks.require(set(parsed) == set(rows), 'C/JSON channel reference set', sorted(set(parsed) ^ set(rows)))
    for ref in set(parsed) & set(rows):
        checks.require(parsed[ref]['rail'] == rows[ref]['rail'], 'C/JSON rail name', ref)
        for key in keys:
            checks.require(math.isclose(parsed[ref][key], rows[ref][key], rel_tol=1e-12, abs_tol=0),
                           'C/JSON channel field', {'ref': ref, 'field': key})


def run_command(args: list[str], cwd: Path, log: Path) -> int:
    print('+ ' + ' '.join(args), flush=True)
    try:
        result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace', timeout=300, check=False)
        log.write_text(result.stdout, encoding='utf-8')
        print(result.stdout, flush=True)
        return result.returncode
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b''
        if isinstance(output, bytes): output = output.decode('utf-8', errors='replace')
        log.write_text(output + '\nTIMEOUT: command was not retried.\n', encoding='utf-8')
        return 124


def extract_input(archive: Path, work: Path):
    if work.exists(): raise RuntimeError('Work directory already exists; refusing stale export reuse: ' + str(work))
    work.mkdir(parents=True)
    manifest = {}
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist()) > 100 * 1024 * 1024:
            raise ValueError('Archive is larger than the verification input safety limit')
        seen = set()
        for info in z.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in info.filename or ':' in info.filename:
                raise ValueError('Unsafe archive path: ' + info.filename)
            if info.filename in seen or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Duplicate path or symbolic link in archive: ' + info.filename)
            seen.add(info.filename)
            dest = work.joinpath(*name.parts)
            if info.is_dir(): dest.mkdir(parents=True, exist_ok=True); continue
            data = z.read(info)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            manifest[info.filename] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    schematics = list(work.rglob(SCHEMATIC))
    if len(schematics) != 1: raise ValueError('Expected exactly one R2 root schematic')
    return schematics[0], manifest


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zip', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--expected-kicad', default='8.0.9')
    p.add_argument('--work', type=Path, default=Path('.kicad-ci-work'))
    p.add_argument('--out', type=Path, default=Path('reports'))
    args = p.parse_args()
    out, work, archive = args.out.resolve(), args.work.resolve(), args.zip.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'verification_summary.json').exists():
        print('Refusing to overwrite a previous verification summary', file=sys.stderr); return 2
    checks = Checks()
    summary = {'status': 'UNVERIFIED', 'started_utc': datetime.now(timezone.utc).isoformat(),
               'commit_sha': os.environ.get('GITHUB_SHA'), 'branch_ref': os.environ.get('GITHUB_REF'),
               'run_id': os.environ.get('GITHUB_RUN_ID'), 'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
               'input_zip_name': archive.name, 'checker_sha256': sha256(Path(__file__)),
               'limits': LIMITS, 'commands': {}}
    try:
        digest = sha256(archive)
        summary['input_zip_sha256'] = digest
        if digest.lower() != args.expected_sha256.lower():
            raise ValueError('R2 ZIP hash mismatch: expected ' + args.expected_sha256 + '; got ' + digest)
        schematic, manifest = extract_input(archive, work)
        project = schematic.parent
        (out / 'input_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        exe = shutil.which('kicad-cli')
        if not exe: raise RuntimeError('kicad-cli is not installed; no native verification has run')
        version_result = subprocess.run([exe, 'version'], capture_output=True, text=True, timeout=30, check=True)
        version = version_result.stdout.strip()
        summary['kicad_version'] = version
        (out / 'kicad-version.txt').write_text(version + '\n', encoding='utf-8')
        if not re.match(re.escape(args.expected_kicad) + r'(?:$|[^0-9.])', version):
            raise RuntimeError('KiCad version does not match the approved verification baseline: ' + version)
        netlist, erc = out / 'verified_netlist.xml', out / 'erc_report.json'
        for target in (netlist, erc):
            if target.exists(): raise RuntimeError('Refusing to reuse existing native output: ' + str(target))
        export_code = run_command([exe, 'sch', 'export', 'netlist', '--format', 'kicadxml',
                                   '-o', str(netlist), str(schematic)], project, out / 'netlist-export.log')
        erc_code = run_command([exe, 'sch', 'erc', '--format', 'json', '--severity-all',
                                '--exit-code-violations', '-o', str(erc), str(schematic)],
                               project, out / 'erc.log')
        summary['commands'] = {'native_netlist_exit_code': export_code, 'native_erc_exit_code': erc_code}
        checks.require(export_code == 0 and netlist.is_file(), 'native netlist export succeeded', export_code)
        checks.require(erc_code == 0 and erc.is_file(), 'native ERC succeeded without violations', erc_code)
        if netlist.is_file() and export_code == 0:
            model = json.loads((project / 'source_contract.json').read_text(encoding='utf-8'))
            root, components, native, counts = compare_native(model, netlist, checks)
            summary['counts'] = counts
            checks.require(Path(root.findtext('./design/source', '')).resolve() == schematic.resolve(),
                           'native XML source path', root.findtext('./design/source'))
            compare_bom(project, components, checks)
            compare_firmware(project, components, native, checks)
        if erc.is_file():
            report = json.loads(erc.read_text(encoding='utf-8'))
            sheets = report.get('sheets')
            checks.require(isinstance(sheets, list) and bool(sheets), 'ERC has sheet results')
            violations = [v for s in (sheets or []) for v in s.get('violations', [])]
            summary['erc'] = {'sheet_count': len(sheets or []), 'violation_count': len(violations),
                              'severity_counts': dict(Counter(v.get('severity', 'unspecified') for v in violations))}
            checks.require(not violations, 'ERC violations including exclusions', violations)
        changed = [name for name, item in manifest.items()
                   if not (work / name).is_file() or sha256(work / name) != item['sha256']]
        checks.require(not changed, 'source files unchanged by verification', changed)
        checks.require(sha256(archive) == digest, 'original ZIP unchanged')
    except Exception as exc:
        checks.errors.append({'check': 'execution or input error', 'detail': str(exc)})
        (out / 'exception.log').write_text(traceback.format_exc(), encoding='utf-8')
        print(traceback.format_exc(), file=sys.stderr)
    summary['checks_executed'] = checks.executed
    summary['errors'] = checks.errors
    summary['status'] = 'FAIL_OR_UNVERIFIED' if checks.errors else 'SCHEMATIC_CHECKS_PASS_HARDWARE_HOLD'
    summary['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (out / 'verification_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    brief = f"Status: {summary['status']}\nChecks: {checks.executed}\nIssues: {len(checks.errors)}\nProduction: HOLD\n"
    (out / 'SUMMARY.txt').write_text(brief, encoding='utf-8')
    print(brief, flush=True)
    for issue in checks.errors[:30]: print(json.dumps(issue, ensure_ascii=False), flush=True)
    print('All issue details: reports/verification_summary.json', flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write('## R2 KiCad verification\n\n```text\n' + brief + '```\n')
            f.write('This result does not approve hardware performance or PCB production.\n')
    return 1 if checks.errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
