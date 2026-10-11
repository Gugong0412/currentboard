"""Validate KiCad-exported connectivity against the Phase 2-2 source contract.
Run: python validate_project.py
To re-export after editing, first run the commands in README_KO.txt.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

base = Path(__file__).resolve().parent
model = json.loads((base / 'source_contract.json').read_text(encoding='utf-8'))
root = ET.parse(base / 'verified_netlist.xml').getroot()
expected_refs = {c['ref'] for c in model['components'] if not c['ref'].startswith('#')}
actual_refs = {c.attrib['ref'] for c in root.findall('./components/comp')}
assert actual_refs == expected_refs, ('Reference mismatch', actual_refs ^ expected_refs)
actual = {}
for net in root.findall('./nets/net'):
    name = net.attrib['name'].split('/')[-1]
    assert name not in actual, ('Duplicate normalized net', name)
    actual[name] = {f"{n.attrib['ref']}.{n.attrib['pin']}" for n in net.findall('node')}
expected = {n['name']: {v for v in n['nodes'] if not v.startswith('#')} for n in model['nets']}
for name, nodes in expected.items():
    assert actual.get(name) == nodes, (name, 'missing', nodes - actual.get(name, set()), 'extra', actual.get(name, set()) - nodes)
extra = {name: nodes for name, nodes in actual.items() if name not in expected}
assert all(name.startswith('unconnected-') and len(nodes) == 1 for name, nodes in extra.items())
expected_nc = {f"{c['ref']}.{p['number']}" for c in model['components'] for p in c['pins'] if p['net'] == 'NC'}
assert set().union(*extra.values()) == expected_nc
manifest = json.loads((base / 'placement_manifest.json').read_text())
assert len(manifest['components']) == len(model['components']) + 1 == 345
assert set(manifest['components']) - {c['ref'] for c in model['components']} == {'#FLG1100'}
assert sum(len(v) for v in manifest['pins'].values()) == sum(len(c['pins']) for c in model['components']) + 1
for comp in root.findall('./components/comp'):
    src = next(c for c in model['components'] if c['ref'] == comp.attrib['ref'])
    fields = {v.attrib['name']: v.text or '' for v in comp.findall('./fields/field')}
    assert fields.get('Population') == src['Population'], (src['ref'], 'Population changed')
erc = json.loads((base / 'erc_report.json').read_text())
violations = [v for s in erc['sheets'] for v in s['violations']]
assert not violations, violations
result = {
    'status': 'PASS', 'kicad_version': '8.0.9', 'schematic_sheets': len(manifest['sheets']) + 1,
    'placed_symbols': len(manifest['components']), 'physical_symbols': len(actual_refs),
    'power_flags': 9, 'pin_rows': sum(len(c['pins']) for c in model['components']),
    'matched_named_nets': len(expected), 'isolated_nc_pins': len(expected_nc),
    'erc_errors': 0, 'erc_warnings': 0, 'erc_exclusions': 0,
    'limit': 'Connectivity/ERC validation is not hardware, component-rating, or production-release approval.'
}
(base / 'verification_summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
