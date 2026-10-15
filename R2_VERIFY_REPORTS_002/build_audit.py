import json, hashlib, csv
from pathlib import Path
import xml.etree.ElementTree as ET

base = Path(__file__).resolve().parent.parent
out = Path(__file__).resolve().parent
source = base / 'CurrentBoard_R2_Desktop_Handoff/DDI_Phase2_2_R2_12CH'
manifest = json.loads((source.parent / 'R2_HANDOFF/SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
integrity = []
for name, item in manifest['original_files'].items():
    path = source.parent / name
    integrity.append({'file': name, 'match': hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']})
(out / 'source_integrity.json').write_text(json.dumps(integrity, indent=2), encoding='utf-8')
root = ET.parse(out / 'verified_netlist.xml').getroot()
pin_net = {n.attrib['ref']+'.'+n.attrib['pin']: net.attrib['name'].split('/')[-1] for net in root.findall('./nets/net') for n in net.findall('node')}
fw = json.loads((source / 'firmware_definitions.json').read_text(encoding='utf-8'))
rows=[]
for c in fw['channels']:
    ref=c['ref']
    row={k:c[k] for k in ('ref','rail','bus','address_7bit','shunt_ref','R_ohm')}
    row.update({str(i):pin_net.get(ref+'.'+str(i)) for i in range(1,11)})
    rows.append(row)
with (out/'channel_pin_audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary=json.loads((out/'verification_summary.json').read_text(encoding='utf-8'))
erc=json.loads((out/'erc_configured.json').read_text(encoding='utf-8'))
lines=['R2 로컬 검증 결과 — 2026-10-15 (KST)', '',
'판정: FAIL_OR_UNVERIFIED / 제작 HOLD',
'로컬 터미널·파일 접근 확인. KiCad CLI: C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli.exe, 버전 10.0.7.',
'Python 3.12.14. 기존 8.0.9 검증과 다른 버전이며 8.0.9 재현 검증은 수행하지 않았다.',
f'SOURCE_MANIFEST 원본 {len(integrity)}개: 검증 후 SHA256 전부 일치 = {all(x["match"] for x in integrity)}.',
'원본·계약·BOM·펌웨어·기존 검사 스크립트 수정 없음. GitHub 쓰기/push 없음.',
'입력은 시작 시 이미 Git 미추적 상태였다. 결과와 작업 복사본은 원본 외부에만 생성했다.', '',
'기존 verify_r2_directory.py가 수정하지 않은 verify_r2.py 핵심 비교 함수를 호출했다.',
'001 실행: 자식 프로세스 PATH 전달 문제로 KiCad 탐색 실패. 네이티브 결과 생성 전 중단.',
'002 실행: Python 내부에서 실행 환경을 명시하여 해결. 새 넷리스트 export exit 0, ERC exit 5.',
'설정은 R2_VERIFY_ENV_001에 격리. HKCU\\Software\\kicad-cli 레지스트리 접근 경고는 로그에 보존.',
f'검사 {summary["checks_executed"]}개. 실제 부품 379개, 계약 명명 net 190개, NC 19핀, copper bridge 선언 25개 일치.',
'전체 36개 계층 시트의 네이티브 ERC 결과 존재. B8_VGL2 시트 위반 0개.',
'named net/핀 집합 불일치 0건. BOM 대 계약 불일치 0건. C 헤더 대 JSON, 션트 값 대 네이티브 불일치 0건.', '',
'Value 불일치 (계약·BOM 기대값 → 실제 회로도):']
for e in summary['errors']:
    if e['check']=='native Value':
        d=e['detail']; lines.append(f'- {d["ref"]}: {d["expected"]} → {d["actual"]}')
lines += ['', 'ERC: 최초 26 warning / 0 error. 설치된 기본 footprint 전역 테이블과 KICAD10_FOOTPRINT_DIR를 설정한 후 별도 재실행: 8 warning / 0 error.',
'최초 증거는 보존했으며 erc_configured.json에 재실행 결과를 저장했다. 18건은 라이브러리 탐색 설정으로 해소됐다.',
'남은 경고:']
for s in erc['sheets']:
    for v in s['violations']:
        lines.append('- '+s['path']+' '+v['type']+': '+v['description']+'; '+str(v['items']))
lines += ['', 'J1200 footprint: Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A가 설치 라이브러리에 없음. 임의 대체하지 않았다.',
'7개 isolated label은 루트에 남은 VGL/VGH/AVDDH2 이전 이름이다. 핀 net 대조는 통과하지만 경고를 면제하지 않았다.',
'기존 프로젝트에서 비활성인 ERC 규칙: '+', '.join(x['key'] for x in erc['ignored_checks'])+'. --severity-all은 비활성 규칙을 다시 켜지 않는다. 전체 규칙 무예외 PASS가 아니다.', '',
'주요 핀·구조 확인:',
'- U840.1=GND_F, .2=F_3V3, .4=I2C2_SDA_F, .5=I2C2_SCL_F, .6=F_3V3, .7=GND_F.',
'- U840.9=VGL2_INA_N, .10=VGL2_INA_P. U820과 절연 도메인 공유. GND_F와 시스템 GND는 별도 논리 net.',
'- U520.1/.2=VDDI_SRC, R526.1=VDDI_SRC, R525.1=VDDI_DUT; R525/526.2=VDDI_FB_SEL. R525 DNP / R526 FIT 일치.',
'- U520.3=VDDI_FB; 전체 FB 저항망의 계약 대비 연결도 일치. VDDI_SRC는 U710/U780/U790 공급 공통점.',
'- AVDDH2_SRC는 U740/U760 공통 공급, VGH_SRC는 U750/U770 공통 공급. S/O 합산 및 GM 분리 12채널 유지.',
'- 헤더: J1400.3 VDDI_DUT, J1403.1 LPDP, .3 OSC, .5 AVDDH2_GM, .7 VGH2; J1401.3 AVDDH2_S_O; J1402.1 VGL1; J1404.1 VGL2.',
'- INA A1(.1)/A0(.2), SDA(.4)/SCL(.5), VS(.6)/GND(.7), sense(.9/.10)는 channel_pin_audit.csv에 12개 모두 기록했다.',
'- 주소 스트랩은 계약의 각 Ref.pin/net과 일치한다. 기존 검사기의 주소 검사는 JSON 내 유일성/C 헤더 일치이며 실제 IC 주소 디코딩·물리 핀맵 독립 승인은 아니다.',
'- 25개 copper bridge의 논리 net 선언 일치. 실제 PCB copper/Kelvin 배선 검증은 아니다.', '',
'다음 해결 대상: Value 표기 5건 정합성, 남은 이전 라벨 7개, J1200 정확한 footprint/MPN 확인. 원본에는 수정하지 않았다.',
'피크·기동·열·공급 안정도·정확도·실측·PCB DRC·완성 펌웨어 검증은 미완료이며 제작 HOLD 유지.']
(out/'RESULT_KO.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Source integrity:',len(integrity),all(x['match'] for x in integrity))
print('Report:',out/'RESULT_KO.txt')
