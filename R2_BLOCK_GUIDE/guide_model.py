"""Validated extraction and explanations of actual connections, not a new circuit."""
from pathlib import Path
import json,csv,re,hashlib,collections
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"R2_BLOCK_GUIDE"
PROJECT=ROOT/"R2_REPAIRED_006"
MODEL=json.loads((PROJECT/"source_contract.json").read_text(encoding="utf-8"))
C={c["ref"]:c for c in MODEL["components"]}
FW=json.loads((PROJECT/"firmware_definitions.json").read_text(encoding="utf-8"))
XML=ET.parse(ROOT/"R2_FIX_REPORTS_006/native/verified_netlist.xml")
PINS={p.get("ref")+"."+p.get("pin"):n.get("name") for n in XML.findall("./nets/net") for p in n.findall("node")}
NETS=collections.defaultdict(list)
for pin,net in PINS.items():NETS[net].append(pin)
COMPXML={c.get("ref"):c for c in XML.findall("./components/comp")}
POP_CONFLICTS={r for r,x in COMPXML.items() if r in C and
 ("[DNP]" in x.findtext("value","")) != (C[r]["Population"]=="DNP")}
BOM={r["RefDes"]:r for r in csv.DictReader((PROJECT/"BOM.csv").read_text(encoding="utf-8-sig").splitlines())}
def block(c):return int(re.match(r"B(\d+)",c["block"])[1])
def short(n):return n.split("/")[-1]
def net(c,p):
 return PINS.get(c["ref"]+"."+p["number"],p["net"])
def validate():
 manifest=json.loads((ROOT/"R2_FIX_REPORTS_006/native/input_manifest.json").read_text(encoding="utf-8"))
 for name,data in manifest.items():assert hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()==data["sha256"],name
 count=0
 for c in C.values():
  if c["ref"].startswith("#"):continue
  if c["ref"] in BOM:
   assert BOM[c["ref"]]["Value"]==c["Value"],c["ref"]
   assert BOM[c["ref"]]["MPN"]==c["MPN"],c["ref"]
  x=COMPXML.get(c["ref"])
  if x is not None:assert x.findtext("value").removesuffix(" [DNP]")==c["Value"],c["ref"]
  for p in c["pins"]:
   key=c["ref"]+"."+p["number"]
   assert key in PINS,key
   actual=short(PINS[key]);expected=p["net"]
   assert actual==expected or (expected=="NC" and actual.startswith("unconnected-")),(key,actual,expected)
   count+=1
 # All firmware pins agree with the physical current MCU netlist.
 for p in FW["pins"]:assert short(PINS["U1100."+p["number"]])==p["net"]
 for ch in FW["channels"]:
  assert C[ch["shunt_ref"]]["Value"] in ("20R","100R","3.01R")
  assert abs(ch["full_scale_current_A"]*ch["R_ohm"]-.16384)<1e-10
 return {"unchanged_input_files":len(manifest),"matched_pins":count,"channels":len(FW["channels"]),"population_label_conflicts":sorted(POP_CONFLICTS),"native_export_rerun":True}

BUCK={
"SW":"스위칭 노드. 출력 인덕터를 거쳐 부하로 이어지므로 최종 DC 출력 넷과 다르다.",
"PG":"출력 상태를 MCU에 알리는 선. 외부 풀업이 High 레벨을 정한다.",
"FB":"출력의 저항 분압을 받아 목표 전압을 설정한다.",
"AGND":"제어 회로의 기준. 이 설계에서는 시스템 GND와 같은 넷이다.",
"PGND":"전력단 전류 귀환. AGND와 같은 넷이어도 PCB 귀환 경로는 고려해야 한다.",
"EP_GND":"방열 패드를 GND에 연결한다. 핀17은 프로젝트 패드 번호다.",
"FSW":"GND 고정으로 대표2.5MHz 설정. 주파수 선택 신호를 MCU로 제어하지 않는다.",
"DEF":"GND 고정으로 명목 출력 선택. +5% 조정 모드를 사용하지 않는다.",
"SS_TR":"3.3nF를 GND에 연결해 출력 기동 램프를 설정한다.",
"AVIN":"제어 전원 입력. PVIN과 같은 보호된12V이고100nF를 가까이 둔다.",
"PVIN":"전력 변환용 입력. 입력 MLCC와 스위칭 전류 루프를 구성한다.",
"VOS":"인덕터 뒤의 출력 전압을 직접 읽는 control-loop sense. FB 분압과 구별한다.",
"EN":"High면 활성. 실제 연결이 입력 전원인지 MCU 제어선인지 아래 넷으로 구분한다."}
LDO={
"IN":"상위 전원 입력. 같은 번호군의 로컬 입력 커패시터가 GND로 바이패스한다.",
"OUT":"로컬 출력 커패시터와 후단 부하에 전원을 전달한다. B5에서는 션트 앞 SRC다.",
"FB":"상단/하단 저항 사이를 감시한다. B5는 선택 점퍼에 따라 DUT 또는 SRC가 기준이며 VDDI는 SRC 전단을 선택한다.",
"PG":"출력 상태선. CTRL_3V3 풀업을 통해 MCU가 읽으며 정밀 안정화 완료 신호는 아니다.",
"SS_CTRL":"GND에 고정해 NR/SS 커패시터의 느린 충전 모드를 사용한다.",
"NR_SS":"100nF를 GND에 연결한 기준 잡음 감소/기동 설정점이다.",
"EN":"입력 전원 또는 MCU enable이 연결된다. 풀다운이 있는 채널은 기본 OFF다.",
"GND":"시스템 전압 기준과 귀환.", "EP_GND":"방열 패드를 시스템 GND에 연결한다."}
INA={
"A1":"A0와 조합해 I2C 주소를 선택한다. 실제 GND/VS/SDA/SCL 조합은 채널 표와 함께 확인한다.",
"A0":"A1과 함께 주소를 선택한다. MCU의 일반 GPIO 제어선이 아니다.",
"ALERT":"이상/진단 상태 출력. 로컬 풀업과 실제 MCU 연결 유무를 구분한다.",
"SDA":"선택된 I2C 버스의 양방향 데이터 선.",
"SCL":"선택된 I2C 버스의 클록 선.",
"VS":"IC 로직/아날로그 공급. B7은CTRL_3V3, B8은F_3V3.",
"GND":"IC가 전압을 재는 기준. B8은GND_F로 시스템 GND와 다르다.",
"VBUS":"버스 전압 샘플 입력. B7은소스 측, B8은시스템 GND를 부유 기준으로 읽는다.",
"IN_MINUS":"차동 션트 검출의 음 입력. B7은DUT sense, B8은source sense.",
"IN_PLUS":"차동 션트 검출의 양 입력. B7은source sense, B8은DUT sense."}
USB={
"VBUS1":"host의5V가 공급된다. 보드12V를 넣지 않는다.",
"VDD1":"측1 내부3.3V 기준·바이패스. PDEN/SPU가 이 레벨을 사용한다.",
"PDEN":"VDD1에 묶은 제어 입력. 원 데이터시트의 pull-down 동작 설정을 따른다.",
"SPU":"측1 속도를 High(full-speed)로 설정한다.",
"SPD":"측2 속도를 High(full-speed)로 설정한다. SPU와 일치시킨다.",
"VBUS2":"측2는3.3V 방식이므로VDD2와 함께CTRL_3V3에 연결한다.",
"VDD2":"보드3.3V를 직접 공급하고100nF로바이패스한다.",
"PIN":"MCU가 downstream pull-up 전달을 제어하는 attach 신호.100kΩ로기본Low.",
"GND1":"host측USB_GND. 보드GND와같이묶지않는다.",
"GND2":"보드측GND. host측USB_GND와분리.",
"UD_PLUS":"host쪽D+;24Ω직렬저항을거쳐커넥터와연결.",
"UD_MINUS":"host쪽D−;24Ω직렬저항을거쳐커넥터와연결.",
"DD_PLUS":"보드쪽D+;24Ω직렬저항을거쳐MCU와연결.",
"DD_MINUS":"보드쪽D−;24Ω직렬저항을거쳐MCU와연결."}
def pin_reason(c,p):
 n=p["name"];v=c["Value"];r=c["ref"];nt=p["net"]
 if nt=="NC":return "의도한 미연결. 다른 NC와 연결된 공통 전선이 아니며, 각 핀은 별개다." + (" 고정출력형 DNC에는 동박도 연결하지 않는다." if n=="DNC" else "")
 if "TPS62130" in v:return BUCK.get(n,"실제 넷으로 해당 역할의 외부 회로와 연결된다.")
 if "TPS7A9001" in v:return LDO.get(n,"LDO 제어·전원 연결.")
 if "INA228" in v:return INA[n]
 if r=="U1200":return USB[n]
 if r=="U900":return "임시 인터페이스 번호. 실제 PMIC 핀번호/정격으로 승인되지 않았다. "+({"VBAT":"B3의3.8V입력.","VDD1V8":"SYS_1V8입력.","VDDI_B":"SYS_1V8입력.","EN":"B13의1.8V enable."}.get(n,"다른 블록과 공유하는 "+nt+" 연결 계약."))
 if r=="U800":return {"VIN_MINUS":"절연 모듈 입력 기준은시스템GND.","VIN_PLUS":"AUX_5V에서전력을받는다.","VOUT_MINUS":"출력기준GND_F는NT800에서VGL_SRC에묶인다.","VOUT_PLUS":"비안정화5V출력. U810과최소부하R800에공급."}[n]
 if r=="U810":return {"IN":"RAW_5V_F를입력받는다.","EN":"입력RAW_5V_F에묶어로컬전원존재시활성.","OUT":"GND_F기준3.3V를공급.","PG":"R810으로F_3V3풀업된로컬상태선. TP1049로관찰.","GND":"VGL_SRC와결합된부유기준.","EP_GND":"방열패드도GND_F. 시스템GND에연결하지않는다."}.get(n,"고정출력 LDO의 해당핀 기능과 실제 연결을 대조한다.")
 if r=="U830":
  if n.startswith("SDA"):return "두 도메인 사이 양방향 I2C 데이터. 해당 측3.3V 풀업을 사용한다."
  if n.startswith("SCL"):return "시스템측SCL1→부유측SCL2의단방향클록경로. 역방향stretching을가정하지않는다."
  if n.startswith("VCC"):return "이 측의로컬3.3V전원. 반대측전원과구분한다."
  return "해당측의기준접지. GND1=GND, GND2=GND_F."
 if r=="U1300":return {"VCCA":"A측3.3V전원.","VCCB":"B측1.8V전원.","GND":"양측논리기준은공통GND;이칩은절연기가아니다.","DIR":"VCCA에묶어A→B로고정.","A1":"MCU의MOSCATO enable입력.","A2":"MCU의active-low reset입력.","B1":"1.8V enable출력.47Ω를거쳐전달.","B2":"1.8V reset출력.47Ω를거쳐전달."}[n]
 if r=="U1100":
  if n in ("VDD","VDDIO2","VBAT"):return "CTRL_3V3 전원. VBAT라는 핀 이름을 B3의3.8V VBAT 넷과 혼동하지 않는다."
  if n=="VDDA":return "0Ω R1103를 통해 CTRL_3V3에서 공급받는 아날로그 전원."
  if n in ("VSS","VSSA"):return "시스템 GND로 귀환."
  if n.startswith("PF"):return "8MHz 크리스털 발진 경로. 부하 커패시터/직렬 링크와 함께 읽는다."
  if n=="NRST":return "버튼·RC·SWD로 공유되는 active-low reset."
  if n=="BOOT0":return "10kΩ 풀다운과 서비스 헤더로 부팅 모드를 선택."
  if nt.startswith("PG") or nt=="PWR_FLT_N":return "전원 상태 입력. High 레벨은 각 회로의3.3V 풀업이 정한다."
  if nt.startswith("EN_"):return "해당 전원을 켜는 MCU 출력. 기본 OFF는 외부 풀다운으로 유지."
  if nt.startswith("ALERT"):return "INA228 진단 입력." + (" DIG은 TIM2 입력 캡처에도 사용한다." if n=="PA0" else "")
  if nt.startswith("I2C"):return "측정 IC와 통신. open-drain 설정 및 외부 풀업을 전제로 한다."
  if nt.startswith("USB_"):return "B12 USB 절연기와 데이터/attach 연결. 펌웨어 설정은 별도."
  if nt.startswith("SW"):return "SWD 디버그 신호.33Ω 링크를거쳐헤더로전달."
  if nt.startswith("LED"):return "B15 표시 LED를 High에서 켜는 구동 출력."
  if nt=="MCU_SPARE_PB9":return "예비GPIO. TP1503에만노출되며임의기능을할당하지않는다."
  return "B13으로 제어 신호를 전달해1.8V 레벨로 변환한다."
 if r.startswith("U120") and r!="U1200":return "커넥터측 신호의 ESD 우회 경로. 기준은 USB_GND이며 시스템 GND가 아니다."
 if r.startswith("J14"):return "DUT 외부 케이블로 "+nt+" 전달. 핀 이름보다 실제 넷을 결선 기준으로 사용한다."
 if r.startswith("TP"):return "이 넷을 직접 관찰하는 패드. 버퍼·격리 기능이 없어 프로브 부하가 추가된다."
 if r=="NT800":return "동박으로 VGL_SRC와 GND_F를 결합하는 유일한 기준 연결."
 if r.startswith("J"):return "커넥터 접점. "+nt+"에 연결되며 용도·보는 방향은 본문의 헤더 설명과 함께 확인한다."
 if len(c["pins"])==4 and r.startswith("R"):
  return {"1":"힘 전류 경로의 source 단자. 같은쪽3번과동박연결.","2":"힘 전류 경로의 DUT 단자. 같은쪽4번과동박연결.","3":"source Kelvin 검출.1번과동박연결.","4":"DUT Kelvin 검출.2번과동박연결."}[p["number"]]
 return part_reason(c)

def part_reason(c):
 r=c["ref"];f=c["function"];v=c["Value"];ns=[p["net"] for p in c["pins"]]
 extra=" 기본 미실장이므로 실제 기본 동작에서는 열린 가지다." if c["Population"]=="DNP" else ""
 if r.startswith("TP"):return "관측 위치를 제공한다. 프로브 입력저항·정전용량이 원래 회로에 추가되므로 측정 부하를 평가한다."
 if r.startswith("H"):return "전기 핀이 없는 NPTH 장착홀. 구리 keepout과 금속 지지대의 절연 경계 침범은 PCB에서 확인한다."
 if r.startswith("LOGO"):return "전기 소자가 아닌 실크/표시 지시. 과거 revision 문자열은 제작 릴리스 승인으로 해석하지 않는다."
 if r=="NT800":return "출력 부유 전원의 기준을 VGL source에 고정하는 동박 연결. 시스템GND와 연결하는 부품이 아니다."
 if r.startswith("U"):return f"{v}의 기능은 본문과 모든 핀 표에 설명한다. 실제 외부 연결은 회로도·넷리스트에서 추출했다."
 if r.startswith("J"):return "외부 인터페이스의 접점 묶음. 핀 전체 표가 실제 전기 연결이며 케이블·기구 검증은 별도다."
 if r.startswith("Y"):return "8MHz 발진 기준. CL10pF에 맞춘12pF 두 개+기생4pF 가정이며 PCB 기동·구동전력 확인이 필요하다."
 if r.startswith("SW"):return "누르면 두 핀을 연결해 NRST를Low로 만든다."
 if r.startswith("L"):return "SW 펄스를 출력 전류로 평균화한다.2.2µH는 리플·응답·포화 여유를절충한 값; peak와DCR/온도를함께검토."
 if r.startswith("D"):return "A→K로 흐르는 표시 전류를 저항이 제한한다. LED의 Vf·밝기·극성은 정확한 구매품 선정 후 확인한다."
 if r.startswith("C"):
  if "CFF" in f:return "FB 상단 병렬의 feed-forward 조정 자리.100pF는루프검증전실장하지않는다."+extra
  if "soft-start" in f or "noise reduction" in f:return "기준/기동 설정 커패시터. 전원 벌크와 달리 충전전류와 기준전압으로 시간을 계산한다."+extra
  if "차동" in f:return "IN+–IN− 사이 차동 필터 후보. 기본0Ω직렬저항/미실장 상태에서 유한한 RC 차단주파수를 주장하지 않는다."+extra
  if v=="12p":return "크리스털 부하 용량. 두12pF 직렬 등가6pF에 기생4pF를 더해CL10pF를 맞춘 가정이다."
  if r=="C1109":return "NRST–GND에100nF. 외부10kΩ와명목1ms이나내부pull-up과문턱이실제reset파형을바꾼다."
  if v=="100n":return "표시된 전원과 해당 접지 사이의 가까운 바이패스. 빠른 전류 변화의 루프를 줄이려는100nF이며 배치/ESL도 중요하다."+extra
  return "표시된 전원선의 로컬 저장·바이패스 용량. 값이 커지면 droop는 줄지만 기동 충전 부담이 커진다. 명목값과DC바이어스후 유효용량을 구별한다."+extra
 if "FB 상단" in f:return "피드백 상단 저항. 직렬 조합을 합산해0.8V×(1+상단/하단)으로목표값을맞춘다."+extra
 if "FB 하단" in f:return "피드백 하단 저항. 분압비와정상분압전류를함께결정한다."+extra
 if "후단 FB" in f:return "DUT 쪽 피드백을 선택하는0Ω링크. 반대 SRC선택 링크와동시실장하면션트우회경로가생긴다."
 if "전단 FB" in f:return "SRC 쪽 피드백 대안. 후단링크 제거후전원OFF에서변경한다."+extra
 if "션트" in f:return "전류를 작은 전압으로 변환한다. I=V/R, P=I²R.1–3/2–4는각단자동박결합이며저항양끝은별개다."
 if "필터 직렬" in f:return "기본0Ω 검출 링크. 선택 저항을 넣으면 P/N을 맞추고 바이어스·gain·주파수응답을 재검토한다."
 if "pull-up" in f:return "오픈드레인 신호/버스의High를해당전원으로정한다. 값은Low전류와RC상승시간의절충이다."
 if "default OFF" in f:return "100kΩ로 enable 기본Low.3.3V High에서약33µA를소모한다."
 if "bleeder" in f:return "VBAT에상시연결된1kΩ방전부하.3.8mA/14.44mW이며외부역급전을차단하지는않는다."
 if r=="R800":return "절연 DC/DC의 약10% 최소 규정부하를 확보하려는220Ω.5V에서약22.7mA/114mW;0.5W요구."
 specific={
 "R1100":"외부10kΩ NRST 풀업. MCU 내부풀업과병렬이며C1109와reset필터를이룬다.",
 "R1101":"BOOT0를10kΩ로기본Low에둬일반Flash부팅을선택한다.",
 "R1102":"크리스털출력직렬0Ω조정자리. 실제drive/startup확인후변경.",
 "R1103":"CTRL_3V3와VDDA사이0Ω링크.1Ω RC필터가아니다.",
 "R1104":"SWDIO의33Ω직렬댐핑.디버거·배선파형으로확인.",
 "R1105":"SWCLK의33Ω직렬댐핑.디버거·배선파형으로확인.",
 "R1200":"CC1 독립5.1kΩ Rd. 방향별sink인식;CC2와합치지않는다.",
 "R1201":"CC2 독립5.1kΩ Rd. 방향별sink인식;CC1과합치지않는다.",
 "R1206":"USB실드를host측USB_GND에잇는0Ω.보드GND로절연을우회하지않는다.",
 "R1207":"ADuM PIN attach제어를100kΩ로기본Low.3.3V구동시33µA.",
 }
 if r in specific:return specific[r]
 if r in ["R1202","R1203","R1204","R1205"]:return "ADuM full-speed응용의24Ω직렬종단. D+/D−를균형있게배선하며DC분압용이아니다."
 if r in ["R1300","R1301"]:return "A측10kΩ풀다운. MCU high-Z시기본Low;3.3V에서0.33mA."
 if r in ["R1302","R1303"]:return "B측47Ω직렬댐핑.이저항자체가전원OFF격리를제공하지않는다."
 if r in ["R1304","R1305"]:return "B측10kΩ풀다운.출력high-Z시Low,8µA누설가정시80mV."
 if r.startswith("R150"):return "LED전류를(VSUPPLY−VF)/R로설정한다.VF가미확정이므로수치는조건부계산."
 return f"{f}. 실제두연결점과본문의계산조건을함께읽는다."+extra
