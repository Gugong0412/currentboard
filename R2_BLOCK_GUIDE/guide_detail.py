"""B1-level reading order and per-passive reasoning, tied to actual values/nets."""
from html import escape as E
import re
from guide_model import C, PINS, NETS, FW, block, short, part_reason
from guide_content import p,h,calc,table,note

FLOW={
2:["VIN_12V_PROT가 C200·C201·C202와 U200의 AVIN/PVIN에 도달합니다. EN도 이 입력에 연결되어 있습니다.",
   "U200의 SW 1·2·3번에서 나오는 펄스를 L200이 전류 변화로 받아 AUX_5V 출력으로 전달합니다.",
   "C203·C204가 출력 변동을 받아 주고 VOS는 인덕터 뒤의 AUX_5V를 직접 감시합니다.",
   "AUX_5V→R200→R201→R202→GND 분압의 FB를 제어합니다. R200/R201 사이의 넷은 FB가 아닙니다.",
   "C205가 기동 속도를 정하고 R203은 PG를 CTRL_3V3 논리 레벨로 만듭니다. PG가 있다고 부하 리플까지 측정되는 것은 아닙니다."],
3:["입력 바이패스·SW·L300·출력 C의 전력 경로는 B2와 같은 형식이고 출력 설정만 3.8V입니다.",
   "MCU가 EN_VBAT을 High로 만들어야 켜집니다. R304가 부팅 중 떠 있는 EN을 Low로 유지합니다.",
   "VBAT→R300→R301→R302→GND 분압으로 3.8V를 설정합니다. VOS는 이 VBAT를 직접 읽습니다.",
   "C305의 램프와 출력 용량·부하가 기동을 결정합니다. R303을 통해 PG_VBAT를 읽습니다.",
   "EN이 내려가도 출력 전압은 순간적으로 0V가 되지 않습니다. R305와 실제 부하가 저장 전하를 소모합니다."],
4:["AUX_5V가 U400 IN과 입력 MLCC에 도달하고 EN도 같은 AUX_5V를 받습니다.",
   "U400 OUT의 CTRL_3V3는 출력 C403·C404로 안정화되며 MCU와 제어 회로로 공급됩니다.",
   "R400+R401 / R402의 분압을 FB가 읽어 3.3V로 조정합니다.",
   "SS_CTRL=GND와 C405의 조합이 NR/SS 기동을 결정합니다. C406은 기본 미실장입니다.",
   "PG_CTRL_3V3의 풀업 전원도 CTRL_3V3입니다. 이 전원이 없을 때 PG에 외부 High가 생기지 않습니다."],
5:["CTRL_3V3가 U500·U520·U540의 IN으로 들어갑니다. 각 EN은 MCU가 제어하고 100kΩ이 기본 OFF를 만듭니다.",
   "각 LDO OUT의 로컬 출력 C 다음에 측정 션트가 있습니다. 로컬 C가 DUT 뒤에 있다고 읽으면 안 됩니다.",
   "DIG와 VCI는 R505/R545를 통해 DUT 뒤를 FB 분압 기준으로 선택합니다. R506/R546은 DNP입니다.",
   "VDDI는 R526을 통해 SRC 앞을 기준으로 선택합니다. R525는 DNP이고 LPDP·OSC도 이 SRC를 공유합니다.",
   "B7 INA228은 각 션트의 별도 Kelvin 단자 전압을 읽습니다. LDO 피드백과 INA 측정은 목적과 연결점이 다릅니다."],
6:["CTRL_3V3 입력에서 U600이 1.2V, U620이 1.8V를 만듭니다.",
   "R603/R623가 EN을 Low로 유지하고 MCU가 활성화합니다.",
   "각 OUT에 연결된 분압과 로컬 출력 C가 레귤레이션 루프를 이룹니다. B5와 달리 이 블록 자체에는 측정 션트가 없습니다.",
   "NR/SS 100nF가 기동·기준 잡음을 조정하며 CFF 100pF는 DNP입니다.",
   "SYS_1V8은 DUT뿐 아니라 B9·B13에도 전달됩니다. 그 부하와 전원 순서까지 합쳐 검토합니다."],
7:["먼저 선택한 채널의 SRC→션트→DUT 힘 전류 경로를 찾습니다.",
   "션트 3·4번 Kelvin 단자는 P/N의 0Ω 링크를 거쳐 INA228 IN+/IN−에 들어갑니다.",
   "IN+/IN− 사이 1nF는 기본 DNP입니다. 기본 동작에 실장 필터가 있다고 가정하지 않습니다.",
   "INA228 VS는 CTRL_3V3이고 VBUS는 해당 SRC입니다. 버스 전압과 션트 전압은 서로 다른 변환값입니다.",
   "A1/A0로 정한 주소를 통해 I2C1에서 레지스터를 읽습니다. ALERT는 직접 MCU 연결이 있는 6개 채널만 인터럽트 경로가 됩니다."],
8:["AUX_5V/GND가 U800을 구동합니다. 절연된 출력은 RAW_5V_F/GND_F이며 입력 접지와 연결되지 않습니다.",
   "NT800이 GND_F를 VGL_SRC에만 묶습니다. 따라서 로컬 전원의 절대 전위는 VGL_SRC와 함께 움직입니다.",
   "U810이 GND_F 기준 F_3V3를 만들고 VGL용 INA228·ISO1641의 부유 측을 공급합니다.",
   "VGL은 DUT→IN+, SRC→IN−이며 VBUS=시스템 GND입니다. 양전압 채널과 검출 극성이 다릅니다.",
   "MCU I2C2가 U830을 통과해 두 INA228을 polling합니다. 로컬 ALERT를 MCU까지 전달하는 별도 절연 신호선은 없습니다."],
9:["B3 VBAT와 B6 SYS_1V8, B13 EN이 임시 U900 인터페이스로 들어갑니다.",
   "출력으로 선언된 AVDDH1_SRC·AVDDH2_SRC·VGH_SRC·VGL_SRC가 각각 후단 션트들로 분기합니다.",
   "이 연결 계약만으로 내부 전력 변환 방식·출력 정격·기동 순서를 결정할 수 없습니다.",
   "실제 부품과 응용 회로를 받은 뒤 내부 회로·외부 R/L/C·핀 번호를 채우고 검증을 다시 해야 합니다."],
10:["측정하고 싶은 물리량에 맞춰 SRC, DUT, Kelvin, 전원 상태, 통신 중 패드 그룹을 고릅니다.",
    "넷 이름만 보지 말고 그 전압의 기준이 GND, PWR_RTN, GND_F, USB_GND 중 무엇인지 확인합니다.",
    "전압계/프로브의 입력저항과 정전용량을 원래 부하에 추가한 상태로 측정값을 해석합니다.",
    "션트 차동 측정과 단일 노드 전압 측정을 구분합니다. 한쪽 Kelvin 선을 접지로 단락하는 방식으로 재지 않습니다."],
11:["B4 CTRL_3V3가 MCU VDD·VDDIO2·VBAT 핀 및 R1103 뒤 VDDA를 공급합니다.",
    "NRST·BOOT0가 초기 상태를 정하고 크리스털 회로가 HSE 클록을 제공합니다. 전원만 연결되어도 펌웨어 실행이 보장되는 것은 아닙니다.",
    "MCU가 각 EN을 올리고 PG·PWR_FLT_N을 확인합니다. DUT 시퀀스는 아직 승인되지 않았습니다.",
    "I2C1/I2C2로 측정값을 읽고 직접 연결된 ALERT 입력은 필요한 이벤트 처리에 사용합니다.",
    "SWD는 별도 디버그 헤더, USB는 B12 절연 경로입니다. 둘의 연결·접지·전원 공급 관계를 구분합니다."],
12:["USB-C의 각 방향 접점에서 D+/D−가 각각 합쳐집니다. CC1/CC2는 독립 5.1kΩ Rd로 내려갑니다.",
    "D+/D−와 CC·VBUS의 ESD 전류는 USB_GND로 돌아갑니다. 측정 보드 GND로 넘기지 않습니다.",
    "host D±는 24Ω를 거쳐 U1200의 upstream으로 들어가고 절연 장벽을 통과합니다.",
    "보드 측 D±도 24Ω를 거쳐 MCU로 갑니다. 양쪽 전원과 속도 설정 핀은 각 도메인을 기준으로 합니다.",
    "MCU가 준비된 뒤 USB_ATTACH_3V3를 올립니다. R1207은 초기 detach 상태를 만듭니다."],
13:["CTRL_3V3와 SYS_1V8을 각각 VCCA/VCCB에 공급하고 각각의 100nF가 로컬 귀환 루프를 만듭니다.",
    "DIR=VCCA이므로 A1→B1, A2→B2 방향으로 고정됩니다.",
    "A측 10kΩ이 MCU high-Z의 입력 상태를 정합니다.",
    "출력의 47Ω 뒤 신호가 EN/RESET으로 나가고 B측 10kΩ은 출력 high-Z에서도 Low를 유지합니다.",
    "RESET_N의 Low는 reset 해제 상태가 아니라 assert 상태입니다. 전원 준비 후 순서를 적용합니다."],
14:["헤더별로 실제 DUT 전원 넷과 귀환 GND를 찾습니다.",
    "외부 케이블의 pin1·행 방향과 표의 번호를 대응합니다. 설명 그림의 좌우가 실물 커넥터 방향을 뜻하지 않습니다.",
    "VGL 헤더의 귀환은 시스템 GND입니다. B8 GND_F를 DUT 공통 접지로 사용하지 않습니다.",
    "부하 커패시터·배선 저항은 헤더 뒤에서 추가됩니다. 앞 LDO 안정성·션트 전압 강하와 함께 확인합니다."],
15:["POWER LED는 AUX_5V에서, STATUS/FAULT LED는 MCU GPIO에서 저항을 통해 전류를 받습니다.",
    "LED A(2)→K(1)→GND가 전류 방향입니다. 저항은 한계 전류를 설정합니다.",
    "서비스 TP는 기존 신호의 관측점이며 추가 기능을 생성하지 않습니다.",
    "홀·실크에는 전기 핀이 없습니다. 절연 경계와 기구·표시 검토는 PCB에서 별도로 수행합니다."]}

def value(v):
 m=re.fullmatch(r"([0-9.]+)([Rkmunp]?)(?:H|F)?",v)
 return float(m[1])*{"":1,"R":1,"k":1e3,"m":1e-3,"u":1e-6,"n":1e-9,"p":1e-12}[m[2]] if m else None

def application(c):
 r=c["ref"];f=c["function"];v=c["Value"];b=block(c);num=int(r[1:]) if r[1:].isdigit() else 0
 n=value(v);nets=[short(PINS[r+"."+q["number"]]) for q in c["pins"]]
 role=part_reason(c)
 change="";basis=""
 if r.startswith("R"):
  if "FB 상단" in f:
   basis="현재 값은 같은 분압망의 상단 직렬값을 합산해 계산합니다. 값 하나만 독립적인 출력 설정으로 해석하지 않습니다."
   change="하단을 고정하고 상단 합을 늘리면 설정 전압이 올라갑니다. 허용 오차·누설·노이즈도 함께 확인합니다."
  elif "FB 하단" in f:
   basis=f"기준 0.8V 가정: 분압 전류 = 0.8/{n:g} = {0.8/n*1e6:.3f}µA."
   change="상단을 고정하고 하단을 늘리면 설정 전압과 분압 전류가 내려갑니다. 두 저항을 같은 비율로 바꾸면 전압비는 같아도 전류는 바뀝니다."
  elif "션트" in f:
   basis=f"±163.84mV 범위에서 full scale = ±{.16384/n*1000:.5g}mA. 5µA 부하의 션트 전압은 {5e-6*n*1e6:g}µV."
   change="값을 키우면 미소전류 신호는 커지지만 전압 강하도 커지고 측정 가능 최대 전류는 낮아집니다. 저항 전력은 I²R입니다."
  elif "pull-up" in f:
   basis=f"3.3V, 출력 Low를 0V로 근사하면 {3.3/n*1e3:.3g}mA. VOL을 반영하면 (3.3−VOL)/R로 계산합니다."
   change="작은 값은 상승을 빠르게 하지만 Low 싱크 전류를 늘립니다. 큰 값은 소비전류를 줄이지만 버스/상태선 상승을 늦춥니다."
   if "I2C" in f:basis+=f" RC 30→70% 근사 tr≈0.8473RC: Cbus=100pF 예에서 {0.8473*n*100e-12*1e9:.0f}ns."
  elif "default OFF" in f or r=="R1207":
   basis=f"3.3V High일 때 풀다운 소비 = {3.3/n*1e6:.3g}µA. 실제 초기 상태는 구동기의 high-Z·누설까지 포함합니다."
   change="큰 저항은 High 상태 소비를 줄이지만 누설·잡음에 더 민감해집니다. 작은 저항은 구동기의 부담을 늘립니다."
  elif n==0:
   basis="0Ω은 지정된 두 넷을 이어 주는 실장 선택점입니다. 이상적인 0Ω이라고 해서 실제 접촉/패턴 저항까지 0은 아닙니다."
   change="임의로 제거하거나 다른 피드백 점퍼와 함께 실장하면 연결 구성이 달라집니다. 검증된 실장 상태를 유지합니다."
  elif r=="R800":
   basis="5V 기준 I=22.73mA, P=113.6mW. 4.75V에서는 21.59mA. 프로젝트 정격은 ≥0.5W입니다."
   change="큰 값은 발열을 줄이지만 저부하 조정 특성을 악화시킬 수 있습니다. 작은 값은 절연 모듈 입력전력과 열을 늘립니다."
  elif r=="R305":
   basis="3.8V에서 3.8mA, 14.44mW의 상시 부하입니다. 44µF만 고려하면 RC=44ms입니다."
   change="작게 하면 방전이 빨라지는 대신 켜진 동안 소비가 늘어납니다. 다른 장치의 역급전은 별도로 고려합니다."
  elif r in ["R1200","R1201"]:
   basis="USB-C sink의 CC1/CC2에 각각 독립 Rd=5.1kΩ을 둡니다. 양쪽 CC를 서로 단락하는 저항이 아닙니다."
   change="두 저항을 병렬로 합치거나 임의 값으로 바꾸면 방향별 연결 인식에 영향을 줍니다. PD 전압 협상을 구현하지 않습니다."
  elif r in ["R1202","R1203","R1204","R1205","R1104","R1105","R1302","R1303"]:
   basis=f"{v}의 직렬 저항으로 신호 에지를 감쇠합니다. 신호원의 출력 임피던스·배선·부하까지 합쳐 파형을 봅니다."
   change="크게 하면 링잉은 줄 수 있지만 에지가 느려집니다. 작게 하면 에지는 빨라지지만 반사가 커질 수 있습니다. DC 논리 레벨과 타이밍도 확인합니다."
  elif r in ["R1300","R1301","R1304","R1305"]:
   vv=3.3 if r in ["R1300","R1301"] else 1.8
   basis=f"{vv:g}V High에서 {vv/n*1e3:.2f}mA. 8µA 누설 가정 시 {8e-6*n*1000:g}mV가 저항 양단에 생깁니다."
   change="단순히 소비를 줄이려고 저항을 키우면 high-Z 상태의 Low 보장이 나빠질 수 있습니다. 실제 누설·VIL을 함께 비교합니다."
  elif r in ["R1100","R1101"]:
   basis="10kΩ은 외부 초기 상태를 정합니다. NRST는 내부 풀업·버튼·100nF, BOOT0는 서비스 헤더까지 함께 봅니다."
   change="Reset의 RC와 boot 선택은 서로 다른 기능입니다. 내부 회로와 문턱을 제외하고 정밀 시간/전압을 보증하지 않습니다."
  elif r.startswith("R150"):
   vv=5 if r=="R1500" else 3.3
   basis=f"Vf=2.0V 예: I=({vv:g}−2)/{n:g}={((vv-2)/n)*1e3:.3f}mA."
   change="값을 줄이면 LED 전류·밝기·GPIO 부하가 커집니다. 실제 Vf와 밝기 bin이 없으므로 확정 광도는 계산할 수 없습니다."
  else:
   basis="원 설계의 연결과 본문에 제시한 조건을 함께 적용합니다."
   change="변경 전에는 연결된 IC의 입력·출력 조건과 소비전류를 다시 대조해야 합니다."
 elif r.startswith("C"):
  if "soft-start" in f or "noise reduction" in f:
   ii=2.5e-6 if b in [2,3] else 6.2e-6;vv=1.25 if b in [2,3] else .8
   basis=f"대표 충전전류를 일정하다고 가정: t≈CV/I={n*vv/ii*1000:.2f}ms. 완전 안정화 시간과는 다릅니다."
   change="크게 하면 기동이 느려지고 충전 전류에 의한 램프가 완만해집니다. 작은 값은 더 빠르지만 기동 전류·시퀀스 여유를 재검토해야 합니다."
  elif "CFF" in f:
   basis="현재 100pF 자리만 있고 DNP이므로 기본 회로에서는 이 경로의 C=0으로 취급합니다."
   change="실장하면 피드백 전달함수와 기동 응답이 변합니다. 본문의 루프·부하 조건을 확인하기 전에는 값을 추천하거나 장착을 승인할 수 없습니다."
  elif "차동" in f:
   basis="1nF는 DNP입니다. 양쪽 직렬 10Ω와 1nF를 실장하는 가정에서만 fc≈1/[2π·20Ω·1nF]=7.96MHz입니다."
   change="필터 용량을 키우면 고주파는 더 줄지만 settling이 느려집니다. P/N 저항 불일치와 바이어스 오차·재교정을 함께 봅니다."
  elif r in ["C1107","C1108"]:
   basis="12pF 두 개의 직렬 등가는 6pF. CL10pF를 맞추려면 기생을 4pF로 가정한 계산입니다."
   change="부하 용량은 발진 주파수·기동 여유를 바꿉니다. 발진자·PCB 기생을 측정하지 않고 값만 크게 하여 잡음을 해결하지 않습니다."
  elif r=="C1109":
   basis="외부 10kΩ×100nF=1ms. 내부 NRST 풀업과 입력 문턱은 이 단순 식에서 제외되어 있습니다."
   change="크게 하면 reset 에지가 더 느려지고 디버거 동작에도 영향을 줄 수 있습니다. 보장 reset 펄스폭은 실제 신호로 확인합니다."
  else:
   basis=f"명목 {v}의 전하 저장 Q=CΔV. 1mA가 10µs 동안 이 C만 방전한다는 예에서 ΔV≈{1e-3*10e-6/n*1000:.3g}mV."
   change="이 계산은 ESR·ESL·상위 전원 응답을 제외합니다. 큰 명목값만으로 안정성이나 고주파 바이패스를 보증하지 않으며 DC 바이어스 후 유효용량을 확인합니다."
 return role,basis,change

def supplement(b,cs):
 flow=h("실제 연결을 따라 읽는 순서")+"<ol>"+''.join("<li>"+E(t)+"</li>" for t in FLOW[b])+"</ol>"
 rows=[]
 for c in cs:
  if not c["ref"].startswith(("R","C")):continue
  role,basis,change=application(c)
  nets=[short(PINS[c["ref"]+"."+q["number"]]) for q in c["pins"]]
  rows.append([E(c["ref"])+"<br>"+E(c["Value"])+" · "+E(c["Population"]),E(" ↔ ".join(nets[:2])),E(role),E(basis),E(change)])
 detail=h("R·C를 하나씩 읽기: 연결 → 현재 값 → 바꾸면 달라지는 점")
 detail+=p("아래 계산은 회로의 선택 이유를 이해하기 위한 조건부 해설입니다. 기록에 없는 선정 의도를 사실로 단정하지 않습니다. 원 설계에서 MPN이 미확정이면 정격·온도·누설·DC 바이어스 검증도 미완료입니다.")
 detail+='<div id="application-table">'+table(["부품 / 실장","두 연결점","역할","현재 값의 해석","값 변경의 영향 / 확인"],rows)+'</div>' if rows else p("이 블록에는 설정용 R·C가 없습니다. 없는 소자를 가정해 값 선정 설명을 만들지 않고, 아래 인터페이스·계측·기구 조건을 해설합니다.")
 extra=""
 if b in [7,8]:
  channels=[ch for ch in FW["channels"] if ch["ref"] in {c["ref"] for c in cs}]
  extra=h("미소전류 값이 숫자로 바뀌는 과정")+table(["채널","5µA의 Vshunt","ADC 1LSB 환산 전류","5µA에서의 션트 손실"],[
   [ch["rail"],f'{5e-6*ch["R_ohm"]*1e6:.3f}µV',f'{312.5e-9/ch["R_ohm"]*1e9:.3f}nA',f'{(5e-6)**2*ch["R_ohm"]*1e9:.3f}nW'] for ch in channels])
  extra+=p("ADC 한 코드의 전류 환산은 분해능입니다. 오프셋·잡음·션트 공차·온도·부하 누설을 포함한 정확도와 같지 않습니다. 예를 들어 20Ω에 1µV의 추가 오차가 생기면 50nA, 5µA의 1%가 됩니다. 이는 실제 오차가 1µV라는 주장이 아니라 민감도 계산입니다.")
 if b in [2,3,4,5,6]:
  extra+=h("명목 용량과 유효 용량을 구분하는 예")+calc("예: 명목 22µF 두 개 → 합계 44µF\n실제 사용 전압·온도에서 각각 30%만 남는 가정 → 합계 13.2µF\n이 30%는 특정 구매품의 보증값이 아니라 계산 예시\n실구매 MPN의 DC bias 곡선 + 온도 + 공차를 합쳐 판단")
  extra+=p("직접 연결된 출력 C와 케이블 뒤 DUT C는 같은 루프 위치가 아닙니다. 데이터시트의 안정성 조건은 실제 부하·배선·용량 범위로 다시 확인해야 합니다. 현재 문서는 회로를 변경하거나 새 용량을 승인하지 않습니다.")
 return flow,detail+extra
