import hashlib, json, os, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
base=Path(__file__).resolve().parent.parent
out=Path(__file__).resolve().parent
p=base/'R2_REPAIRED_003'
name='USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'
fp=p/'DDI_R2_Local.pretty'/f'{name}_S1.kicad_mod'
t=fp.read_text(encoding='utf-8')
assert t.count(name+'_S1.step')==1
fp.write_text(t.replace(name+'_S1.step',name+'.step'),encoding='utf-8',newline='\n')
original=Path(r'C:\Program Files\KiCad\10.0\share\kicad\footprints\Connector_USB.pretty')/f'{name}.kicad_mod'
assert fp.read_text(encoding='utf-8').replace('(pad "S1"','(pad "SH"').replace(name+'_S1',name)==original.read_text(encoding='utf-8')
env=os.environ.copy()
env['PATH']=r'C:\Program Files\KiCad\10.0\bin'+os.pathsep+env['PATH']
env['KICAD_CONFIG_HOME']=str(base/'R2_VERIFY_ENV_001/config')
env['KICAD_DOCUMENTS_HOME']=str(base/'R2_VERIFY_ENV_001/documents')
env['KICAD10_FOOTPRINT_DIR']=r'C:\Program Files\KiCad\10.0\share\kicad\footprints'
env['PYTHONIOENCODING']='utf-8'
checker=base/'CurrentBoard_R2_Desktop_Handoff/R2_HANDOFF/tools/verify_r2_directory.py'
r=subprocess.run([sys.executable,str(checker),'--project',str(p),'--work',str(base/'R2_VERIFY_WORK_004'),'--out',str(out/'native_final'),'--expected-kicad','10.0.7'],env=env,capture_output=True)
(out/'final_run.log').write_bytes(r.stdout+r.stderr)
assert r.returncode==0,r.stdout.decode('utf-8',errors='replace')
def graph(file):
    return {n.attrib['ref']+'.'+n.attrib['pin']:net.attrib['name'].split('/')[-1] for net in ET.parse(file).findall('./nets/net') for n in net.findall('node')}
before=graph(base/'R2_VERIFY_REPORTS_002/verified_netlist.xml')
after=graph(out/'native_final/verified_netlist.xml')
repair=json.loads((out/'repair_manifest.json').read_text(encoding='utf-8'))
for ref,net in repair['testpoint_moves'].items(): before[ref+'.1']=net
assert before==after
sha=lambda file: hashlib.sha256(file.read_bytes()).hexdigest()
source=base/'CurrentBoard_R2_Desktop_Handoff/DDI_Phase2_2_R2_12CH'
manifest=json.loads((source.parent/'R2_HANDOFF/SOURCE_MANIFEST.json').read_text(encoding='utf-8'))['original_files']
assert all(sha(source.parent/k)==v['sha256'] for k,v in manifest.items())
repair['footprint_adapted_sha256']=sha(fp)
repair['final_evidence']='native_final'
(out/'repair_manifest_final.json').write_text(json.dumps(repair,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
changes=[]
for f in sorted(p.rglob('*')):
    if f.is_file():
        rel=f.relative_to(p); old=source/rel
        if not old.exists() or sha(old)!=sha(f): changes.append({'file':str(rel),'before_sha256':sha(old) if old.exists() else None,'after_sha256':sha(f)})
(out/'changed_files_final.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
print('Final verifier: PASS; seven testpoint moves only; original 63 files intact; 3D model source path preserved.')
