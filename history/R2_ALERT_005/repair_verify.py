import copy, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

B=Path(__file__).resolve().parent.parent
O=Path(__file__).resolve().parent
S=B/'R2_REPAIRED_003'
P=B/'R2_REPAIRED_005'
mapping={'ALERT_AVDDH2_N':'ALERT_AVDDH2_S_O_N','ALERT_VGH_N':'ALERT_VGH1_N'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}
assert not P.exists()
shutil.copytree(S,P)
changed=[]
for p in P.rglob('*'):
    if p.is_file() and p.suffix in ('.kicad_sch','.json','.csv','.h'):
        text=p.read_text(encoding='utf-8-sig')
        updated=text
        for old,new in mapping.items(): updated=updated.replace(old,new)
        if updated!=text:
            p.write_text(updated,encoding='utf-8-sig' if p.suffix=='.csv' else 'utf-8',newline='\n')
            changed.append(str(p.relative_to(P)))
m=load(P/'source_contract.json'); nets={}
for n in m['nets']:
    if n['name'] in nets: nets[n['name']]['nodes']+=n['nodes']
    else: nets[n['name']]=copy.deepcopy(n)
m['nets']=sorted(nets.values(),key=lambda n:n['name'])
for n in m['nets']: n['nodes']=sorted(set(n['nodes']))
save(P/'source_contract.json',m)
pl=load(P/'placement_manifest.json'); pl['global_nets']=sorted(set(pl['global_nets'])); save(P/'placement_manifest.json',pl)
env=os.environ.copy(); env['PATH']=r'C:\Program Files\KiCad\10.0\bin'+os.pathsep+env['PATH']
env['KICAD_CONFIG_HOME']=str(B/'R2_VERIFY_ENV_001/config')
env['KICAD_DOCUMENTS_HOME']=str(B/'R2_VERIFY_ENV_001/documents')
env['KICAD10_FOOTPRINT_DIR']=r'C:\Program Files\KiCad\10.0\share\kicad\footprints'
env['PYTHONIOENCODING']='utf-8'
r=subprocess.run([sys.executable,str(B/'CurrentBoard_R2_Desktop_Handoff/R2_HANDOFF/tools/verify_r2_directory.py'),'--project',str(P),'--work',str(B/'R2_VERIFY_WORK_005'),'--out',str(O/'native'),'--expected-kicad','10.0.7'],env=env,capture_output=True)
(O/'run.log').write_bytes(r.stdout+r.stderr)
print(r.stdout.decode('utf-8',errors='replace')[-1200:])
assert r.returncode==0
def graph(p):
    return {n.attrib['ref']+'.'+n.attrib['pin']:net.attrib['name'].split('/')[-1] for net in ET.parse(p).findall('./nets/net') for n in net.findall('node')}
g0=graph(B/'R2_FIX_REPORTS_003/native_final/verified_netlist.xml'); g1=graph(O/'native/verified_netlist.xml')
allowed={'U1100.39':'ALERT_AVDDH2_S_O_N','TP1067.1':'ALERT_AVDDH2_S_O_N','U1100.40':'ALERT_VGH1_N','TP1068.1':'ALERT_VGH1_N'}
expected=g0.copy(); expected.update(allowed); assert g1==expected
assert {str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}==before
original=B/'CurrentBoard_R2_Desktop_Handoff'
manifest=load(original/'R2_HANDOFF/SOURCE_MANIFEST.json')['original_files']
assert all(sha(original/k)==v['sha256'] for k,v in manifest.items())
assert load(S/'firmware_definitions.json')['channels']==load(P/'firmware_definitions.json')['channels']
for file in ('Firmware_Definitions.h','DDI_Phase2_2_R2.kicad_pro'):
    assert sha(S/file)==sha(P/file)
for net,required in [('ALERT_AVDDH2_S_O_N',{'U740.3','R742.2','TP1067.1','U1100.39'}),('ALERT_VGH1_N',{'U750.3','R752.2','TP1068.1','U1100.40'})]:
    assert {p for p,n in g1.items() if n==net}==required
alerts=[]
for c in load(P/'firmware_definitions.json')['channels']:
    net=g1[c['ref']+'.3']; nodes=sorted(p for p,n in g1.items() if n==net)
    alerts.append({'rail':c['rail'],'ina':c['ref'],'net':net,'nodes':nodes,'mcu_connected':any(p.startswith('U1100.') for p in nodes)})
assert sum(x['mcu_connected'] for x in alerts)==6
save(O/'delta_and_alert_audit.json',{'source_original_63_unchanged':True,'previous_repair_unchanged':True,'channel_definitions_unchanged':True,'erc_settings_unchanged':True,'changes':[{'pin':p,'before':g0[p],'after':g1[p]} for p in allowed],'all_alerts':alerts,'changed_files':changed})
print('PASS: exactly four pin/net moves; six MCU ALERT inputs; VGL domain unchanged.')
