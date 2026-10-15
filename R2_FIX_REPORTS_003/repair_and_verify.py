"""Create a new R2 repair copy and run unchanged handoff verification tools."""
import copy, csv, hashlib, io, json, os, re, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = BASE / 'CurrentBoard_R2_Desktop_Handoff/DDI_Phase2_2_R2_12CH'
PROJECT = BASE / 'R2_REPAIRED_003'
TOOLS = SOURCE.parent / 'R2_HANDOFF/tools'
KICAD = Path(r'C:\Program Files\KiCad\10.0')
FOOTNAME = 'USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'
LOCALNAME = FOOTNAME + '_S1'
OLD_FP = 'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A'
NEW_FP = 'DDI_R2_Local:' + LOCALNAME
RENAMES = {
    'AVDDH2_SNS_SRC': 'AVDDH2_S_O_SNS_SRC', 'AVDDH2_SNS_DUT': 'AVDDH2_S_O_SNS_DUT',
    'VGH_SNS_SRC': 'VGH1_SNS_SRC', 'VGH_SNS_DUT': 'VGH1_SNS_DUT',
    'VGL_SNS_SRC': 'VGL1_SNS_SRC', 'VGL_SNS_DUT': 'VGL1_SNS_DUT',
    'ALERT_VGL_N': 'ALERT_VGL1_N',
}
TP_MOVES = {'TP1027': 'AVDDH2_S_O_SNS_SRC', 'TP1028': 'AVDDH2_S_O_SNS_DUT',
            'TP1031': 'VGH1_SNS_SRC', 'TP1032': 'VGH1_SNS_DUT',
            'TP1035': 'VGL1_SNS_SRC', 'TP1036': 'VGL1_SNS_DUT', 'TP1069': 'ALERT_VGL1_N'}
VALUES = {'J1403': 'EXPANSION / 2x6', 'J1404': 'VGL2 / 1x2',
          'TP1026': 'AVDDH2_S_O_DUT', 'TP1030': 'VGH1_DUT', 'TP1034': 'VGL1_DUT', **TP_MOVES}

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def replace_exact(obj):
    if isinstance(obj,str): return RENAMES.get(obj,obj)
    if isinstance(obj,list): return [replace_exact(x) for x in obj]
    if isinstance(obj,dict): return {k:replace_exact(v) for k,v in obj.items()}
    return obj

assert not PROJECT.exists(), 'Refusing overwrite'
manifest=load(SOURCE.parent/'R2_HANDOFF/SOURCE_MANIFEST.json')['original_files']
assert all(digest(SOURCE.parent/k)==v['sha256'] for k,v in manifest.items())
shutil.copytree(SOURCE, PROJECT)
for p in PROJECT.glob('*.kicad_sch'):
    original=p.read_text(encoding='utf-8')
    lines=original.splitlines(keepends=True)
    for i,line in enumerate(lines):
        if line.startswith('(symbol (lib_id '):
            ref=re.search(r'\(property "Reference" "([^"]+)"',line).group(1)
            if ref in VALUES:
                line,n=re.subn(r'\(property "Value" "[^"]*"','(property "Value" "'+VALUES[ref]+'"',line,count=1)
                assert n==1
            if ref=='J1200':
                assert line.count(OLD_FP)==2
                line=line.replace(OLD_FP,NEW_FP).replace('(property "Datasheet" ""','(property "Datasheet" "https://gct.co/files/drawings/usb4105.pdf"')
            lines[i]=line
        elif line.startswith('(global_label '):
            for old,new in RENAMES.items():
                lines[i]=lines[i].replace('(global_label "'+old+'"','(global_label "'+new+'"')
    updated=''.join(lines)
    if updated!=original: p.write_text(updated,encoding='utf-8',newline='\n')

model=replace_exact(load(PROJECT/'source_contract.json'))
for c in model['components']:
    if c['ref'] in VALUES: c['Value']=VALUES[c['ref']]
    if c['ref']=='J1200': c['Footprint']=NEW_FP
merged={}
for net in model['nets']:
    if net['name'] in merged: merged[net['name']]['nodes'] += net['nodes']
    else: merged[net['name']]=copy.deepcopy(net)
model['nets']=sorted(merged.values(),key=lambda x:x['name'])
for net in model['nets']: net['nodes']=sorted(set(net['nodes']))
save(PROJECT/'source_contract.json',model)
placement=replace_exact(load(PROJECT/'placement_manifest.json'))
placement['global_nets']=sorted(set(placement['global_nets']))
save(PROJECT/'placement_manifest.json',placement)
with (PROJECT/'BOM.csv').open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f); columns=reader.fieldnames; rows=list(reader)
for row in rows:
    if row['RefDes'] in VALUES: row['Value']=VALUES[row['RefDes']]
    if row['RefDes']=='J1200': row['RequestedFootprint']=NEW_FP
with (PROJECT/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns); w.writeheader(); w.writerows(rows)

fp_source=KICAD/'share/kicad/footprints/Connector_USB.pretty'/f'{FOOTNAME}.kicad_mod'
fp=fp_source.read_text(encoding='utf-8')
assert fp.count('(pad "SH"')==4
adapted=fp.replace('(pad "SH"','(pad "S1"').replace('(footprint "'+FOOTNAME+'"','(footprint "'+LOCALNAME+'"').replace('(property "Value" "'+FOOTNAME+'"','(property "Value" "'+LOCALNAME+'"')
assert adapted.replace('(pad "S1"','(pad "SH"').replace(LOCALNAME,FOOTNAME)==fp
(PROJECT/'DDI_R2_Local.pretty').mkdir()
fp_dest=PROJECT/'DDI_R2_Local.pretty'/f'{LOCALNAME}.kicad_mod'
fp_dest.write_text(adapted,encoding='utf-8',newline='\n')
table=PROJECT/'fp-lib-table'
t=table.read_text(encoding='utf-8').rstrip()
table.write_text(t[:-1]+'\n(lib (name "DDI_R2_Local") (type "KiCad") (uri "${KIPRJMOD}/DDI_R2_Local.pretty") (options "") (descr "USB4105 KiCad 10 footprint; shield pad identifiers adapted to existing S1 symbol")))\n',encoding='utf-8')
(PROJECT/'J1200_FOOTPRINT_PROVENANCE.txt').write_text(
    'MPN retained: GCT USB4105-GF-A. GF = gold flash; A = tape/reel; no stake suffix = 0.95 mm.\n'
    'Manufacturer drawing: https://gct.co/files/drawings/usb4105.pdf, B4, 18/12/23, sheet 1.\n'
    'Product: https://gct.co/connector/usb4105\n'
    f'KiCad 10.0.7 source: {fp_source}\nSource SHA256: {digest(fp_source)}\n'
    'Changes: footprint/Value identifier suffix _S1; four SH pads renamed S1 to retain existing J1200.S1 USB_SHIELD. All geometry unchanged.\n'
    'KiCad library license: CC-BY-SA-4.0 with KiCad exception; see KiCad_Footprints_LICENSE.md.\n'
    'Manufacturer land pattern checked: 12 distinct SMT land positions, 16 contact pad IDs; 0.50 mm inner pitch; '
    '0.30/0.60 x 1.15 mm lands; shell x +/-4.32 mm; shell slots 0.60 x 1.70 and 0.60 x 1.40 mm; '
    'shell row spacing 4.18 mm; pegs diameter 0.65 mm, x +/-2.89 mm.\n'
    'Coincident pad pairs A1/B12, A4/B9, A9/B4, A12/B1 must have identical nets. Checked after fresh export.\n',encoding='utf-8')
save(OUT/'repair_manifest.json',{'source':str(SOURCE),'project':str(PROJECT),'net_renames':RENAMES,'testpoint_moves':TP_MOVES,'values':VALUES,'footprint':NEW_FP,'mpn':'USB4105-GF-A','footprint_source_sha256':digest(fp_source),'footprint_adapted_sha256':digest(fp_dest),'manufacturer_pdf_sha256':digest(OUT/'usb4105.pdf')})

env=os.environ.copy()
env['PATH']=str(KICAD/'bin')+os.pathsep+env['PATH']
env['KICAD_CONFIG_HOME']=str(BASE/'R2_VERIFY_ENV_001/config')
env['KICAD_DOCUMENTS_HOME']=str(BASE/'R2_VERIFY_ENV_001/documents')
env['KICAD10_FOOTPRINT_DIR']=str(KICAD/'share/kicad/footprints')
env['PYTHONIOENCODING']='utf-8'
cmd=[sys.executable,str(TOOLS/'verify_r2_directory.py'),'--project',str(PROJECT),'--work',str(BASE/'R2_VERIFY_WORK_003'),'--out',str(OUT/'native'),'--expected-kicad','10.0.7']
result=subprocess.run(cmd,env=env,capture_output=True)
(OUT/'verification_run.log').write_bytes(result.stdout+result.stderr)
print('Native verifier exit:',result.returncode)
print(result.stdout.decode('utf-8',errors='replace')[-2000:])

def native_graph(path):
    root=ET.parse(path).getroot()
    return root,{node.attrib['ref']+'.'+node.attrib['pin']:net.attrib['name'].split('/')[-1] for net in root.findall('./nets/net') for node in net.findall('node')}
before,before_pins=native_graph(BASE/'R2_VERIFY_REPORTS_002/verified_netlist.xml')
after,after_pins=native_graph(OUT/'native/verified_netlist.xml')
expected=before_pins.copy()
for ref,net in TP_MOVES.items(): expected[ref+'.1']=net
assert after_pins==expected,'Unexpected connectivity change'
assert {c.attrib['ref'] for c in before.findall('./components/comp')}=={c.attrib['ref'] for c in after.findall('./components/comp')}
for name in ('Firmware_Definitions.h','firmware_definitions.json','DDI_Phase2_2_R2.kicad_pro','DDI_Project.kicad_sym'):
    assert digest(SOURCE/name)==digest(PROJECT/name),name
for a,b in [('A1','B12'),('A4','B9'),('A9','B4'),('A12','B1')]:
    assert after_pins['J1200.'+a]==after_pins['J1200.'+b]
assert after_pins['J1200.S1']=='USB_SHIELD'
j=next(c for c in after.findall('./components/comp') if c.attrib['ref']=='J1200')
assert j.findtext('footprint')==NEW_FP
pads=re.findall(r'\(pad "([^"]*)"',adapted)
jpins={p['number'] for c in model['components'] if c['ref']=='J1200' for p in c['pins']}
assert set(pads)-{''}==jpins and pads.count('S1')==4
assert all(digest(SOURCE.parent/k)==v['sha256'] for k,v in manifest.items())
changes=[{'pin':p,'before':before_pins[p],'after':after_pins[p]} for p in sorted(after_pins) if before_pins[p]!=after_pins[p]]
save(OUT/'connectivity_delta.json',{'unexpected_changes':[],'changes':changes,'original_63_files_unchanged':True,'firmware_unchanged':True,'erc_rules_unchanged':True,'J1200_symbol_pad_set_match':True,'J1200_shield_pads':4,'J1200_coincident_pad_nets_match':True})
diffs=[]
for p in sorted(PROJECT.rglob('*')):
    if p.is_file():
        rel=p.relative_to(PROJECT); orig=SOURCE/rel
        if not orig.exists() or digest(orig)!=digest(p):
            diffs.append({'file':str(rel),'before_sha256':digest(orig) if orig.exists() else None,'after_sha256':digest(p)})
save(OUT/'changed_files.json',diffs)
print('Connectivity delta: exactly seven testpoint moves; source hashes preserved; J1200 pin/pad match.')
raise SystemExit(result.returncode)
