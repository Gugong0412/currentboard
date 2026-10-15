"""Build the standalone diagram from the verified R2 native netlist."""
import hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
out=Path(__file__).resolve().parent
project=out.parent/'R2_REPAIRED_005'
model=json.loads((project/'source_contract.json').read_text(encoding='utf-8'))
components={c['ref']:c for c in model['components']}
root=ET.parse(out/'native/verified_netlist.xml')
nets={n.attrib['ref']+'.'+n.attrib['pin']:net.attrib['name'].split('/')[-1] for net in root.findall('./nets/net') for n in net.findall('node')}
fw=json.loads((project/'firmware_definitions.json').read_text(encoding='utf-8'))
order=['VDDI_DIG','VDDI','VDDI_LPDP','VDDI_OSC','VCI','AVDDH1','AVDDH2_S_O','AVDDH2_GM','VGH1','VGH2','VGL1','VGL2']
channels=[]
for rail in order:
    c=next(c for c in fw['channels'] if c['rail']==rail).copy()
    c['address']=f'0x{c["address_7bit"]:02X}'
    c['pins']={p['number']:{'name':p['name'],'net':nets[c['ref']+'.'+p['number']]} for p in components[c['ref']]['pins']}
    dut=rail+'_DUT'
    c['header']=next(k for k,v in nets.items() if k.startswith('J14') and v==dut)
    c['alert']=nets[c['ref']+'.3']
    c['alert_nodes']=[k for k,v in nets.items() if v==c['alert']]
    c['mcu']=next((k for k in c['alert_nodes'] if k.startswith('U1100.')),None)
    c['gpio']=next((p['name'] for p in components['U1100']['pins'] if c['mcu']==('U1100.'+p['number'])),None)
    channels.append(c)
data={'channels':channels,'sha256':hashlib.sha256((out/'native/verified_netlist.xml').read_bytes()).hexdigest(),'checks':8437}
template=(out/'explorer-template.html').read_text(encoding='utf-8')
assert '__R2_DATA__' in template
(out/'R2_INTERACTIVE_DIAGRAM.html').write_text(template.replace('__R2_DATA__',json.dumps(data,ensure_ascii=False)),encoding='utf-8')
print('Built standalone diagram:',len(channels),'channels; native header, address and ALERT mappings included.')
