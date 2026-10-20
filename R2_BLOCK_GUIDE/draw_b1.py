"""Single connected explanatory schematic; coordinates do not describe PCB placement."""
from pathlib import Path
from html import escape
p=Path(__file__).parent
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1040" role="img" aria-label="B1 전체 연결도"><style>text{font:18px Malgun Gothic,Arial;fill:#193b49}.wire{fill:none;stroke:#167d83;stroke-width:3}.part{fill:white;stroke:#193b49;stroke-width:2}.small{font-size:15px}.title{font-size:25px;font-weight:bold}</style><rect width="1600" height="1040" fill="#fff"/>']
def text(x,y,t,cls='',anchor='start'):
 s.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(t)}</text>')
def wire(*points):
 s.append('<polyline class="wire" points="'+' '.join(f'{x},{y}' for x,y in points)+'"/>')
def dot(x,y):s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#167d83"/>')
def ground(x,y):
 wire((x,y),(x,y+12))
 for off,w in [(12,18),(20,12),(28,6)]:wire((x-w,y+off),(x+w,y+off))
 text(x,y+50,'GND','small','middle')
def res(x,y,ref,val):
 s.append(f'<rect class="part" x="{x-10}" y="{y-27}" width="20" height="54"/>')
 text(x+20,y-4,ref);text(x+20,y+19,val,'small')
def cap(x,y,ref,val,polar=False):
 wire((x-18,y-8),(x+18,y-8));wire((x-18,y+8),(x+18,y+8))
 text(x+23,y-7,ref);text(x+23,y+16,val,'small')
 if polar:text(x-32,y-12,'+')
text(35,38,'B1 · 모든 부품을 연결한 통합 회로도','title')
text(35,66,'● = 연결점 · 점 없는 교차는 미접속 · 동일 GND 기호는 같은 넷 · RTN은 별도 넷','small')
# Jack and input power
s.append('<rect class="part" x="25" y="105" width="100" height="125" rx="8"/>')
text(40,132,'J100');text(40,157,'PJ-102AH','small')
text(108,184,'1','small');wire((125,180),(660,180),(660,280),(720,280));wire((660,240),(720,240));dot(660,240)
text(145,169,'VIN_12V_RAW')
text(108,210,'2','small');wire((125,205),(140,205),(140,320));ground(140,320)
text(35,256,'3 SWITCH → × NC','small')
for x,ref,val in [(230,'C100','100nF / 50V'),(360,'C104','4.7µF / 50V')]:
 wire((x,180),(x,252));cap(x,260,ref,val);wire((x,268),(x,320));ground(x,320);dot(x,180)
wire((530,180),(530,242));s.append('<rect class="part" x="505" y="242" width="50" height="46"/>')
text(530,270,'TVS','small','middle');text(566,258,'D100');text(566,280,'SMBJ18CA','small');wire((530,288),(530,320));ground(530,320);dot(530,180)
# Main IC body
s.append('<rect class="part" x="720" y="205" width="300" height="665" rx="15" fill="#eef8f8"/>')
text(870,325,'U100','title','middle');text(870,353,'TPS26600PWPR','','middle')
left={240:'1 IN',280:'2 IN',430:'3 UVLO',560:'5 OVP',700:'9 GND',760:'6 MODE',800:'8 RTN'}
for y,t in left.items():text(733,y-9,t)
right={240:'OUT 15',280:'OUT 16',400:'FLT 14',480:'NC 4',520:'NC 13',560:'SHDN 7',600:'IMON 10',660:'dVdT 12',760:'ILIM 11'}
for y,t in right.items():text(1008,y-9,t,anchor='end')
text(870,842,'17 EP / RTN','','middle')
# Divider separate below input shunts
wire((660,180),(660,395),(450,395),(450,403))
# Crossing at x660,240 &280 already same input; lower divider routes clear
res(450,430,'R100','110kΩ');wire((450,457),(450,480),(690,480),(690,430),(720,430));dot(450,480)
wire((450,480),(450,533));res(450,560,'R101','4.99kΩ')
wire((450,587),(450,610),(690,610),(690,560),(720,560));dot(450,610)
wire((450,610),(450,663));res(450,690,'R102','10kΩ');wire((450,717),(450,930))
text(35,460,'분압 사다리 / 입력 전압 감시')
text(35,493,'R100–R101 사이 → UVLO','small')
text(35,523,'R101–R102 사이 → OVP','small')
# GND and RTN, no crossings between ground and RTN
wire((720,700),(620,700),(620,715));ground(620,715)
wire((720,760),(670,760),(670,930));wire((720,800),(670,800));dot(670,800)
wire((870,870),(870,930));wire((450,930),(1340,930))
for x in [450,670,870,1160,1340]:dot(x,930)
text(735,960,'PWR_RTN · TP1002 · GND와 연결하지 않음')
# Output
wire((1020,240),(1080,240),(1080,180),(1510,180));wire((1020,280),(1080,280),(1080,240));dot(1080,240)
text(1160,155,'VIN_12V_PROT → B2 / B3 · TP1001')
for x,ref,val,pol in [(1220,'C102','47µF / 35V',True),(1400,'C103','100nF / 50V',False)]:
 wire((x,180),(x,242));cap(x,250,ref,val,pol);wire((x,258),(x,285));ground(x,285);dot(x,180)
# fault pull-up and MCU
wire((1020,400),(1490,400));text(1240,382,'PWR_FLT_N · TP1040')
wire((1130,315),(1130,333));res(1130,360,'R104','10kΩ');wire((1130,387),(1130,400));dot(1130,400)
text(1087,307,'CTRL_3V3','small')
text(1250,430,'→ U1100.4 / PC15 (3.3V 로직)','small')
for y in [480,520,560,600]:
 wire((1020,y),(1060,y));text(1065,y+6,'× NC')
# timing and current settings
wire((1020,660),(1160,660),(1160,732));cap(1160,740,'C101','100nF / 25V')
wire((1160,748),(1160,930))
wire((1020,760),(1340,760),(1340,803));res(1340,830,'R103','8.06kΩ');wire((1340,857),(1340,930))
s.append('<path d="M1149 760 H1171" stroke="white" stroke-width="10"/><path d="M1149 760 H1171" class="wire"/>')
text(1175,682,'PWR_DVDT','small');text(1355,785,'PWR_ILIM','small')
# virtual symbol notes with exact nets, no pretend hardware
text(35,845,'ERC 전용 · 실장하지 않는 심볼')
text(35,875,'#FLG0100 → VIN_12V_RAW','small')
text(35,900,'#FLG0101 → GND','small')
text(35,925,'#FLG0102 → PWR_RTN','small')
text(35,998,'TP1000=RAW · TP1003=GND · 테스트포인트와 MCU/B2/B3는 B1 밖의 연결을 표시한 것','small')
s.append('</svg>')
(p/'B1_CONNECTED.svg').write_text(''.join(s),encoding='utf-8')
