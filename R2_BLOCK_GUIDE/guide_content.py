"""Human-authored circuit reasoning for the B2–B15 review guide."""
from html import escape as E

TITLES={
2:"AUX_5V · 상시 보조 전원",3:"VBAT · 제어 가능한 3.8V 전원",
4:"CTRL_3V3 · 제어 회로용 LDO",5:"DIG / VDDI / VCI · LDO와 피드백 선택",
6:"VDDIO1V2 / SYS_1V8 · 보조 LDO",7:"양전압 10채널 · INA228 측정",
8:"VGL1·2 · 부유 전원과 절연 측정",9:"MOSCATO · 임시 PMIC 인터페이스",
10:"테스트포인트 · 측정 위치 지도",11:"MCU · 전원·클록·리셋·디버그",
12:"USB-C · 데이터 절연과 ESD",13:"3.3V → 1.8V · 제어 신호 변환",
14:"DUT 헤더 · 12채널 출력 연결",15:"LED · 서비스 패드·기구 요소"}

SOURCES={
"buck":("TI TPS62130A · SLVSAG7F","https://www.ti.com/lit/ds/symlink/tps62130a.pdf", "p.3 핀, p.5 전기 특성, p.14~17 출력·LC·SS 설정"),
"ldo":("TI TPS7A90 · SBVS324B","https://www.ti.com/lit/ds/symlink/tps7a90.pdf","p.3 핀, p.6~7 특성, §6.3.6 기동, §7.1.3 커패시터"),
"ina":("TI INA228 · SLYS021A","https://www.ti.com/lit/ds/symlink/ina228.pdf","p.3 핀, p.5 범위, §7.3.5 교정, §7.5.1 주소, §8.1 응용"),
"iso":("TI ISO164x · SLLSFC2D","https://www.ti.com/lit/ds/symlink/iso1641.pdf","16-DW 핀표, ISO1641의 단방향 SCL, 응용의 풀업·부하 조건"),
"float":("TI TPS7A16 · SBVS171F","https://www.ti.com/lit/ds/symlink/tps7a16.pdf","핀 기능, 고정 출력 DNC, 입력/출력 커패시터"),
"rfm":("RECOM RFM · Rev 0/2018","https://recom-power.com/pdf/Econoline/RFM.pdf","p.1 부하 조건, p.2 regulation, p.3 EMC 제안, p.4 핀"),
"coil":("Coilcraft XFL4020 · 2026-03-10","https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf","2.2µH 행의 DCR/Isat 조건; Isat와 Irms 구별"),
"mcu":("ST STM32F072x8/xB · DS9826 Rev6","https://www.st.com/resource/en/datasheet/stm32f072cb.pdf","공식 검색 색인·제품 페이지 확인; 이번 직접 PDF 확보 실패 → 패키지 상세 재대조 미완료"),
"mcu_product":("ST STM32F072CB 공식 제품","https://www.st.com/en/microcontrollers-microprocessors/stm32f072cb.html","48MHz, USB FS, SWD, 전원 범위"),
"usb":("Analog Devices ADuM4160 · Rev E","https://www.analog.com/media/en/technical-documentation/data-sheets/ADuM4160.pdf","p.8~9 핀 기능, p.11~12 전원 연결과 full-speed 응용"),
"esd2":("TI TPD2EUSB30","https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf","DRT 핀, 양 채널 USB ESD 배치"),
"esd1":("TI TPD1E10B06","https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf","DPY 두 단자, ESD 동작과 정격"),
"gct":("GCT USB4105 제품 사양","https://gct.co/files/specs/usb4105-spec.pdf","로컬 history/R2_FIX_003/usb4105.pdf 제조사 도면과 기존 수정 기록 사용; 온라인 사양 직접 확보 실패"),
"level":("TI SN74AXC2T45 · SCES880D","https://www.ti.com/lit/ds/symlink/sn74axc2t45.pdf","DCT 핀, DIR 진리표, 전원 차단 고임피던스"),
"header":("Samtec TSW 시리즈","https://suddendocs.samtec.com/catalog_english/tsw_th.pdf","행 옵션 S/D, 2.54mm 피치; 정확한 구매옵션·상대 커넥터 별도 확인"),
"kicad":("KiCad 공식 ERC 설명","https://docs.kicad.org/9.0/en/eeschema/eeschema.html","PWR_FLAG·핀 전기 유형; 물리 동작의 증명과 구분")
}
def ref(key):
 title,url,where=SOURCES[key]
 return f'<a class="source" href="{url}" target="_blank">{E(title)} — {E(where)}</a>'
def p(t):return f"<p>{t}</p>"
def h(t):return f"<h3>{t}</h3>"
def calc(t):return '<pre class="formula">'+E(t)+'</pre>'
def note(t):return '<div class="note">'+t+'</div>'
def warn(t):return '<div class="note warn">'+t+'</div>'
def table(head,rows):
 return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+E(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def story(b,C,FW):
 """Return overview, reasoning, review notes, references."""
 if b in [2,3]:
  n=200 if b==2 else 300; out='AUX_5V' if b==2 else 'VBAT';v=5 if b==2 else 3.8
  rt='523k + 2k = 525k' if b==2 else '374k + 1k = 375k'
  ov=p(f"<b>보호된 12V를 {v:g}V {out}로 낮추는 동기식 벅 전원입니다.</b> U{n}의 SW에서 생긴 스위칭 파형을 L{n}과 출력 커패시터가 평균화합니다. VOS는 실제 출력점을, FB는 저항 분압을 봅니다. 부품 자체의 3A 표기가 B1의 약 1.49A 입력 제한을 없애지는 않습니다.")
  ov+=p("AUX_5V는 B4의 MCU 전원과 B8의 절연 DC/DC를 먼저 살립니다. EN이 VIN_12V_PROT에 직접 연결된 상시 활성 구성입니다." if b==2 else "이름이 VBAT이지만 이 블록은 배터리 충전기가 아닙니다. MCU의 EN_VBAT으로 MOSCATO용 전원을 제어하고, R304가 MCU 초기 high-Z에서 OFF를 유지합니다.")
  body=h("출력값을 두 개의 상단 저항으로 맞추기")+p(f"R{n}과 R{n+1}은 직렬 상단 저항이며 중간점은 다른 부하에 연결되지 않습니다. 표준값 조합으로 목표 전압을 맞춘 것으로 해석됩니다. 하단 R{n+2}=100kΩ.")
  body+=calc(f"VOUT = 0.8 × (1 + RTOP / RBOTTOM)\nRTOP = {rt}Ω, RBOTTOM = 100kΩ\n→ VOUT = {v:g}V\n분압 전류 = 0.8 / 100k = 8µA\nR{n+3} PG pull-up: 3.3V / 10kΩ ≈ 0.33mA (Low일 때)")
  body+=p("FB 기준 0.8V, FSW=GND에서 대표 2.5MHz, DEF=GND에서 명목 출력입니다. PG는 3.3V로 풀업합니다. "+ref("buck"))
  body+=h("2.2µH 인덕터와 입출력 커패시터")+p(f"L{n}=2.2µH는 스위칭 한 주기마다 흐르는 전류 변화를 제한합니다. C{n}/C{n+1}=10µF 두 개는 펄스 입력 전류의 가까운 공급원이며 C{n+2}=100nF는 AVIN 근처 바이패스입니다. C{n+3}/C{n+4}=22µF 두 개는 출력 리플과 부하 변화를 받아 줍니다. 명목 합계 20µF/44µF와 DC 바이어스 후 유효용량은 구분합니다.")
  ripple=v*(1-v/12)/(2.2e-6*2.5e6)
  body+=calc(f"12V, 2.5MHz, 2.2µH를 가정한 CCM 근사\nD ≈ VOUT/VIN = {v/12:.3f}\nΔIL ≈ VOUT × (1 − VOUT/VIN) / (L × f) = {ripple:.3f}A p-p\nIL_PEAK ≈ ILOAD + {ripple/2:.3f}A\nLC 고유주파수(명목 44µF) ≈ 16.2kHz")
  body+=p("경부하에서는 이 연속전도(CCM) 식 그대로의 파형이 아닙니다. Coilcraft의 2.2µH 행은 10% 인덕턴스 감소 기준 Isat 3.1A, DCR 최대 24mΩ를 제시합니다. 정격 전류 한 숫자보다 실제 피크·온도·포화 기준을 함께 봐야 합니다. "+ref("coil"))
  body+=h("3.3nF 소프트스타트")+calc(f"C{n+5}=3.3nF\nSS 기준 약 1.25V, 충전 대표전류 2.5µA\n→ tSS ≈ 3.3nF × 1.25V / 2.5µA = 1.65ms")
  body+=p("이는 레귤레이터의 명목 램프 추정입니다. 입력이 B1을 통해 올라오는 시간, 기동 부하, PG 판정 지연을 합친 보드 전체 준비 시간은 아닙니다.")
  if b==3:
   body+=h("R304와 R305는 서로 다른 OFF 역할")+calc("R304 100kΩ: EN의 기본 Low. 3.3V High에서 33µA\nR305 1kΩ: 출력의 상시 방전 부하\n3.8V / 1kΩ = 3.8mA; 3.8²/1kΩ = 14.44mW\nC303+C304=44µF만 가정한 RC=44ms\n3.8V→0.38V: RC×ln(10)≈101ms")
   body+=p("R305는 출력 저장 전하를 줄이는 역할입니다. MOSCATO 입력 용량·외부 역급전이 있으면 위 방전 시간이 늘어나거나 아예 같은 지수함수로 내려가지 않습니다.")
  return ov,body,["정확한 MLCC MPN·DC 바이어스 곡선 미정. 계약의 유효용량 목표와 실구매품을 맞춰야 함.","전체 부하의 최악 입력전력, 인덕터 피크 전류, 열·PCB 루프와 기동 파형 검증 필요.","PG High는 정밀 전압·잡음·안정화 완료를 모두 보증하는 신호가 아님."],["buck","coil"]
 if b in [4,5,6]:
  ov=p({4:"<b>AUX_5V에서 CTRL_3V3를 만드는 제어용 LDO입니다.</b> MCU, INA228의 양전압 측 전원, USB 절연기 보드 측과 여러 LDO의 입력을 공급합니다. U400.EN=AUX_5V로 먼저 켜지는 구조입니다.",5:"<b>DIG·VDDI·VCI의 세 LDO와 션트 전후 피드백 선택 회로입니다.</b> DIG·VCI는 DUT 후단 피드백입니다. VDDI는 R525 미실장·R526 실장으로 SRC 전단을 선택합니다. 006에서 Value 표시도 이 상태와 맞췄습니다. 이 세 회로는 B7 측정 IC와 함께 읽어야 합니다.",6:"<b>VDDIO1V2와 SYS_1V8을 만드는 두 개의 LDO입니다.</b> 이 두 전원은 12개 INA228 측정 채널에 포함되지 않습니다. SYS_1V8은 MOSCATO 입력과 B13 레벨시프터의 B측 전원으로도 사용됩니다."}[b])
  configs={4:[(400,468750,150000,3.3)],5:[(500,82500,150000,1.24),(520,187499,150000,1.7999946667),(540,412499,150000,2.9999946667)],6:[(600,75000,150000,1.2),(620,187499,150000,1.7999946667)]}[b]
  rows=[]
  for n,rt,rb,v in configs:
   rows.append([f"U{n}",f"{rt/1000:g}kΩ",f"{rb/1000:g}kΩ",f"{v:.5f}V",f"{v/(rt+rb)*1e6:.3f}µA"])
  body=h("피드백 저항으로 정하는 전압")+p("TPS7A90의 기준 0.8V를 이용합니다. 아래는 실제 저항을 대입한 명목값이며 기준전압·저항·온도 오차를 제외했습니다. "+ref("ldo"))
  body+=calc("VSET = 0.8 × (1 + RTOP/RBOTTOM)\nIDIVIDER = VSET / (RTOP + RBOTTOM)")
  body+=table(["IC","상단 합","하단","설정 전압","분압 전류"],rows)
  body+=h("입출력 커패시터와 100nF NR/SS")
  body+=p("입력 커패시터는 상위 전원까지의 배선 인덕턴스 때문에 생기는 순간 전압 강하를 보완합니다. 출력의 22µF 두 개는 OUT에 직접 연결된 로컬 안정화 용량입니다. 일반 100nF 바이패스와 NR/SS의 100nF는 같은 값이어도 역할이 다릅니다.")
  body+=p("SS_CTRL=GND에서 NR/SS의 대표 충전 전류 6.2µA를 쓰면 100nF×0.8V/6.2µA≈12.9ms입니다. 4~9µA와 커패시터 ±10%만 반영한 단순 범위는 약 8~22ms이며, 완전한 안정화 보증 시간이 아닙니다.")
  body+=p("현재 TI Rev B의 §7.1.3은 권장 명목 입력/출력 용량에 50% 디레이팅을 고려했다고 설명합니다. 따라서 B5/B6의 명목 10µF 입력을 곧바로 ‘유효 10µF 미달’ 오류로 단정하지 않습니다. 프로젝트 요구인 입력 유효 ≥5µF, 출력 유효 합 ≥10µF 및 실제 파형을 함께 확인해야 합니다." if b!=4 else "B4는 입력 22µF 두 개와 출력 22µF 두 개를 두며 각각 유효 합 ≥10µF를 계약 목표로 삼았습니다. 실제 부품은 미선정입니다.")
  body+=p("C406/C506/C526/C546/C606/C626 중 해당 블록의 100pF는 <b>DNP</b> 조정 자리입니다. 기본 회로에서 열린 가지로 그렸습니다. 무조건 장착하면 기동·피드백 루프가 바뀌므로 ‘노이즈용 커패시터니까 넣자’고 결정하지 않습니다.")
  if b==5:
   body+=h("션트 전후 피드백의 전류·전압 해석")+p("DIG의 R505, VCI의 R545는 FIT이고 전단 R506/R546은 DNP입니다. VDDI는 BOM상 R525(DUT)가 DNP, R526(SRC)이 FIT이므로 전단 피드백입니다. 전단·후단 점퍼를 동시에 실장하면 0Ω 경로가 션트를 우회하므로 둘 중 하나만 선택해야 합니다.")
   body+=note("<b>R525·R526 표기 수정 완료 (006):</b> R525는 <code>0R [DNP]</code> / Population DNP, R526은 <code>0R</code> / Population FIT입니다. 실제 실장 플래그와 BOM은 원래 이 상태였으며 Value 표시 두 곳만 맞췄습니다. VDDI는 SRC 전단 피드백이므로 션트 전압 강하를 보상하지 않고, 분압 전류도 R527을 통과하지 않습니다. 기존 005 원본은 보존했습니다.")
   body+=calc("후단 피드백 DIG / VCI: VOUT_SRC ≈ VSET_DUT + ISHUNT × RSHUNT\nDIG: 1mA × 20Ω = 20mV 보상 필요\nVCI: 1mA × 100Ω = 100mV 보상 필요\n분압 전류 = 0.8V / 150kΩ = 5.333µA\n후단 구성에서는 ISHUNT에 피드백 분압 전류도 포함\n전단 피드백 VDDI (BOM 기준): VDUT ≈ VSET_SRC − IDUT × 20Ω\nVDDI 1mA 예: DUT는 명목 SRC보다 약20mV 낮음")
   body+=p("따라서 후단 피드백 채널에서 5µA 수준의 DUT를 측정하려면 5.333µA의 명목 분압 소비를 포함한 영점·온도 보정을 고려해야 합니다. DIG의 펌웨어 SOVL raw100µA와 명목 DUT 약94.667µA 구분도 이 때문입니다. VDDI는 현재 BOM대로면 이 분압 전류를 션트에서 읽지 않습니다. 1mA는 계산 예시이며 운전값 승인이 아닙니다.")
   body+=p("VDDI_SRC 1.8V는 VDDI·LPDP·OSC의 세 션트에 공통 공급됩니다. DIG 1.24V는 별도 U500 전원입니다. U520은 공통 SRC를 피드백하므로 세 분기의 각 DUT 전압 강하를 개별 보상하지 않습니다. 독립 전압 조정기 세 개로 해석하지 않습니다.")
   body+=h("저항 전력과 고장 전류는 별도 검토")+p("R507/R527은 1W 등급으로 보강된 기록이 있지만, 전류 제한 소자가 추가된 것은 아닙니다. 션트만 저항성 부하라고 놓아 3.3²/20≈0.545W를 계산할 수 있어도, 실제 고장에서는 LDO current limit·dropout·열 차단·동시 고장까지 달라집니다. INA 포화 상태의 값도 유효 측정으로 취급하면 안 됩니다.")
  else:
   vin=5 if b==4 else 3.3
   body+=h("LDO의 열과 enable")+calc(f"기본 열 근사: PD ≈ (VIN − VOUT) × IOUT\n"+("\n".join(f"U{n}: ({vin:g}−{v:.3f})V × 0.1A = {(vin-v)*.1:.3f}W (100mA 예시)" for n,rt,rb,v in configs)))
   body+=p("PG 풀업은 CTRL_3V3 기준입니다. "+("U400은 AUX_5V가 올라오면 활성화되므로 MCU 없이 기동할 수 있습니다." if b==4 else "R603/R623=100kΩ은 EN의 기본 OFF를 만들며, MCU가 High로 구동할 때 각각 약33µA를 추가 소모합니다."))
  return ov,body,["미소전류 구간의 실제 오차·누설은 데이터시트의 대표 부하 조건 정확도와 구별해야 함.","실구매 MLCC의 유효용량·ESR, 부하 케이블/커패시터가 있는 루프 안정성 및 기동 검증 필요.","PG만으로 안정화 완료를 판단하지 않음. 펌웨어 100ms guard도 실측 보증 최대 시간이 아님."],["ldo"]
 if b==7:
  ov=p("<b>양전압 10개 분기를 각 INA228로 읽는 블록입니다.</b> VGL 2개는 B8에 있어 합계가 승인된 12채널입니다. 전류 경로(FORCE)와 전압 검출 경로(SENSE)를 구분해 배선 저항이 션트값에 섞이는 것을 줄입니다.")
  body=h("고정 션트와 ADC 범위의 관계")+p("현재 펌웨어는 ADCRANGE=0입니다. INA228의 이 범위는 ±163.84mV, 션트 전압 한 LSB는 312.5nV입니다. "+ref("ina"))
  body+=calc("I ≈ VSHUNT / RSHUNT\nIFULLSCALE = 0.16384 / RSHUNT\n20Ω → ±8.192mA; 100Ω → ±1.6384mA; 3.01Ω → ±54.432mA\n전류 1 LSB: 312.5nV/R → 15.625nA / 3.125nA / 103.821nA\n이는 분해능 계산이며 실제 정확도·노이즈 바닥을 보증하지 않음")
  body+=p("큰 션트는 작은 전류를 더 큰 전압으로 바꾸지만 부하 전압 강하도 키웁니다. 예를 들어 20Ω·1mA는 20mV, 3.01Ω·50mA는 150.5mV와 7.525mW입니다. 후자는 이미 ADC full scale에 가깝습니다.")
  body+=h("4핀 션트가 실제로 뜻하는 것")+p("R507 등의 패드는 FORCE_SRC(1), FORCE_DUT(2), SENSE_SRC(3), SENSE_DUT(4)입니다. 실제 2단자 저항의 한쪽에서 1–3을, 다른 쪽에서 2–4를 동박으로 합칩니다. <b>저항의 양 끝 1–2를 합치는 net tie가 아닙니다.</b> 그림은 이 동박 연결을 점선으로 표시합니다. B5의 션트도 B7 그림에서 경계 부품으로 다시 보여 주되 중복 실장 부품이 아닙니다.")
  body+=h("입력 필터는 기본적으로 미실장")+p("R700/R701 등 P/N 직렬값은 기본 0Ω이고 C701 등 1nF는 DNP입니다. 따라서 기본 BOM을 ‘10Ω+1nF 필터’라고 읽으면 안 됩니다. 후보로 양쪽 10Ω와 1nF를 사용하면 차동 근사 fc=1/[2π×(10+10)Ω×1nF]≈7.96MHz지만, 입력 바이어스·저항 불일치가 추가 오차를 만들 수 있어 재교정 대상입니다.")
  body+=h("전원·I2C·ALERT")+p("각 채널 Cx00=100nF와 Cx02=1µF는 CTRL_3V3–GND의 로컬 바이패스입니다. A0/A1의 GND/VS/SDA/SCL 결합은 채널 주소 선택이며 신호 출력끼리의 오접속이 아닙니다. I2C1 풀업 R708/R709는 버스 전체에 한 쌍입니다.")
  body+=calc("2.2kΩ 풀업의 Low 전류 ≈ 3.3/2200 = 1.5mA\nRC 30→70% 상승시간 근사 tr≈0.8473×R×C\ntr=300ns라면 C≈161pF (수동 RC만 고려)\nDIG ALERT 4.7kΩ → 약0.702mA; 나머지 10kΩ → 0.33mA")
  body+=p("직접 MCU ALERT는 DIG·VDDI·VCI·AVDDH1·AVDDH2_S_O·VGH1의 6개입니다. LPDP·OSC·AVDDH2_GM·VGH2는 I2C polling입니다. ALERT 핀이 부품에 있다는 것과 MCU 입력까지 연결되었다는 것은 다릅니다.")
  body+=h("펌웨어와 션트값")+calc("SHUNT_CAL = 13107.2×10⁶ × CURRENT_LSB × RSHUNT\n현재 12채널 모두 SHUNT_CAL=4096\nCONFIG.ADCRANGE=0과 CURRENT_LSB·실제 저항값이 함께 맞아야 함")
  body+=p("측정 구간은 펌웨어 정책상 shunt-only를 유지합니다. VBUS는 양전압 채널에서 소스 쪽이므로 DUT 전압과 동일시하지 않습니다. VBUS/VSHUNT 스냅샷은 측정 창 밖에서 사용하며 clipping·stale data가 있으면 측정 창을 무효 처리하는 정책입니다.")
  return ov,body,["3.01Ω의 높은 full scale와 미소전류 정확도는 trade-off. 교정·노이즈·온도 실측 미완료.","MCU 직접 ALERT가 없는 채널의 fault 감지 지연은 polling 주기에 좌우됨.","DNP 필터와 0Ω 실장 상태를 유지하고 아날로그 full scale 초과를 산술 overflow 플래그만으로 판단하지 않음."],["ina"]
 if b==8:
  ov=p("<b>음전압 VGL을 기준으로 떠 있는 전원과 I2C 측정 회로입니다.</b> U800으로 절연된 전원을 만들고 NT800에서 GND_F를 VGL_SRC에 연결합니다. GND_F는 시스템 GND가 아닙니다. VGL1·VGL2는 합의한 대로 polling을 유지합니다.")
  body=h("전원 흐름과 최소 부하")+p("AUX_5V/GND → U800 RFM-0505S → RAW_5V_F/GND_F → U810 고정 3.3V LDO → F_3V3/GND_F 순서입니다. RFM은 비안정화 출력이며 10% 미만 부하에서 스펙이 보장되지 않을 수 있습니다. 기능절연 등급이므로 시스템 안전절연 인증과 구별합니다. "+ref("rfm"))
  body+=calc("R800=220Ω: 5V/220Ω=22.73mA, 5²/220=113.6mW\n4.75V와 저항 +1%: 4.75/222.2=21.38mA\n200mA 정격의 약10% 부하를 저항으로 확보하려는 선택\n저항 요구 ≥0.5W: 발열·온도 디레이팅 여유. 출력 전압은 5V 고정으로 보장되지 않음")
  body+=p("C800=10µF와 C801=100nF는 절연 모듈 입력 쪽입니다. 10µF의 유효용량이 제조사 EMC 제안 6.8µF 이상인지 확인해야 하며, 부품값이 같다고 EMC 시험을 통과한 것은 아닙니다.")
  body+=h("U810과 전압 기준")+p("U810의 IN/EN은 RAW_5V_F, GND/EP는 GND_F, OUT은 F_3V3입니다. 고정 3.3V형의 2번 DNC는 동박·GND에 연결하지 않습니다. C810 22µF+C811 100nF가 입력, C812 22µF+C813 100nF가 출력이며 출력은 최소 유효2.2µF 조건과 프로젝트 목표 유효10µF를 구분합니다. "+ref("float"))
  body+=calc("예: VGL_SRC=−8V(시스템 GND 기준)라면\nGND_F=−8V, F_3V3≈−4.7V (시스템 GND 기준)\n하지만 U820/U840이 보는 VS−GND_F는 +3.3V")
  body+=h("왜 VGL 측 IN+가 DUT에 연결되나?")+p("실제 R820/R840의 입력은 DUT sense→IN+, R821/R841은 source sense→IN−입니다. 음전원 부하의 귀환 전류 방향을 고려해 양의 측정값이 되도록 잡은 극성입니다. 두 VBUS 핀은 시스템 GND에 연결되어, 부유 기준에서 −VGL_SRC를 관찰합니다.")
  body+=calc("INA의 VBUS 읽기 ≈ 0 − VGL_SRC = |VGL_SRC|\nINA의 VSHUNT ≈ VGL_DUT − VGL_SRC\n시스템 기준 VGL_DUT ≈ −VBUS + VSHUNT\nI≈VSHUNT/20Ω, full scale≈8.192mA")
  body+=h("I2C 절연과 ALERT")+p("U830은 ISO1641DWR의 16핀 DW 배선입니다. 시스템 측 I2C2와 부유 측 I2C2_F의 SDA는 양방향, SCL은 시스템→부유 측 단방향입니다. 이 경로로 clock stretching을 역방향 전달한다고 가정하면 안 됩니다. "+ref("iso"))
  body+=p("R830/R831과 R832/R833은 각 도메인에서 2.2kΩ 풀업 한 쌍입니다. 양쪽 전원 모두 3.3V 차동 기준이지만 서로 같은 물리 전원은 아닙니다. C830/C831은 시스템 쪽, C832/C833은 부유 쪽 디커플링입니다. 161pF의 단순 RC 계산만으로 절연기 측 부하 조건을 승인하지 않고, 펌웨어가 둔 side1 80pF 가정도 유지합니다.")
  body+=p("U820/U840 ALERT는 각각 R822/R842로 F_3V3에 풀업되어 있습니다. U820 ALERT에는 TP1069가 있고 U840에는 별도 직접 MCU 연결이 없습니다. 두 신호 모두 절연기를 통과하지 않습니다. MCU는 절연 I2C를 통해 측정값·상태 레지스터를 읽습니다. 필터 1nF는 DNP, P/N 직렬값은0Ω입니다.")
  return ov,body,["접지형 계측기의 클립으로 GND_F와 시스템 GND를 연결하면 회로를 변경하는 셈. 차동/절연 측정 기준 확인.","RFM 출력의 무부하·최소 부하·최대 입력 조건, LDO 발열과 실구매 MLCC 검증 필요.","VGL 두 채널의 peak/inrush·정확도와 polling 진단 지연 검증 미완료."],["rfm","float","iso","ina"]
 if b==9:
  return p("<b>U900은 MOSCATO_PLACEHOLDER이며 실제 확정 PMIC가 아닙니다.</b> 이 블록은 다른 회로와 연결할 인터페이스 계약만 기록합니다."),h("현재 연결이 뜻하는 것")+p("VBAT는 B3의 3.8V, VDD1V8와 VDDI_B는 B6의 SYS_1V8, EN은 B13의 MOSCATO_EN_1V8입니다. AVDDH1_SRC·AVDDH2_SRC·VGH_SRC·VGL_SRC는 후단 측정 션트에 전달되는 공급원으로 선언되어 있습니다.")+p("핀1~9는 프로젝트 임시번호입니다. 실제 부품의 package pinout으로 보지 않습니다. AVDDH2는 S/O와 GM, VGH는1·2, VGL은1·2로 분기합니다. 이름이 나뉘어도 이 블록에서 독립된 전압 조정기가 생성된 것은 아닙니다.")+warn("실제 MPN·데이터시트·외부 인덕터/저항/커패시터·제어 시퀀스가 없으므로 출력 전압, 정격 전류, 필수 부품의 선정 이유를 만들어 적지 않았습니다. 실제 회로로 대체한 뒤 넷리스트와 전체 전원 순서를 재검증해야 합니다.")+h("B9에서 현재 계산할 수 없는 것")+p("승압/반전용 인덕터 리플, 보상망, 최소부하, startup, discharge, 출력 오차·노이즈는 입력 자료가 없습니다. 아래 모든 핀 표는 연결 계약을 설명하며 전기적 적합성 승인이 아닙니다."),["실제 부품 및 회로 제공이 B9 응용 해설 완료의 전제.","펌웨어 DUT_SEQUENCE_APPROVED=false 상태 유지.","B9가 임시 상태이므로 전체 보드의 제작 HOLD 유지."],[]
 if b==10:
  return p("<b>70개의 테스트포인트로 전원·Kelvin sense·상태·통신선을 관찰하는 블록입니다.</b> 테스트포인트가 전원을 만들거나 신호를 버퍼링하지는 않습니다."),h("측정 위치에 따라 달라지는 값")+p("SRC와 DUT는 션트를 기준으로 나뉘며, SNS_SRC/SNS_DUT는 저항의 단자 근처에서 따로 끌어온 검출선입니다. FORCE 전류를 테스트패드 경유로 흘리거나 긴 프로브 귀환 루프를 만들면 원래 측정 목적을 해칠 수 있습니다.")+calc("예시: 10MΩ 전압계가 3V DUT–GND에 연결되면\n추가 부하 = 3V / 10MΩ = 0.3µA\n5µA를 측정할 때 이는 6% 크기의 추가 부하\n(미터 입력 임피던스는 장비에 따라 다름)")+p("TP1002=PWR_RTN, TP1037=GND_F, TP1003=GND는 서로 다른 기준입니다. 특히 GND_F를 시스템 GND에 묶는 프로브 접지는 피해야 합니다. TP1038/1039의 전압은 GND_F 기준으로 읽어야 RAW_5V_F/F_3V3라는 뜻이 맞습니다.")+h("통신과 상태 확인")+p("TP1057~1062는 I2C1, I2C2와 절연 측 버스입니다. 프로브 용량도 버스 RC에 더해집니다. TP1067/1068은 수정된 AVDDH2_S_O/VGH1 ALERT이며, TP1069는 VGL1의 로컬 ALERT입니다. TP가 있다고 MCU 인터럽트 연결까지 있는 것은 아닙니다.")+p("이 블록에는 R/C 설정값이나 전용 IC 데이터시트가 없습니다. 패드의 실제 net endpoint와 연결된 원래 블록의 데이터시트가 근거입니다. 표의 핀1과 외부 연결 목록을 측정 체크리스트로 사용할 수 있습니다."),["장비 입력저항·프로브 정전용량·접지 방식까지 포함해 측정 부하를 평가.","테스트포인트 목록은 PCB 접근성·실크·프로브 간격 승인과 다름."],[]
 if b==11:
  ov=p("<b>STM32F072CBT6가 전원 enable, INA228 버스, USB, 상태 신호와 측정 타이밍을 제어합니다.</b> 핀 표는 MCU 48핀 전부와 주변 수동소자·헤더를 포함합니다.")
  body=h("3.3V 전원과 아날로그 전원")+p("C1100/1101/1102는 각각 MCU pin24/36/48 근처, C1103은 pin1 VBAT 근처의100nF입니다. MCU의 VBAT 핀은 이 보드에서 CTRL_3V3에 연결되어 있고, B3의 넷 이름 VBAT(3.8V)와 다릅니다. C1104=4.7µF는 공통 로컬 저장 용량입니다.")
  body+=p("R1103은0Ω 링크이며 CTRL_3V3→MCU_VDDA를 잇습니다. C1105=1µF/C1106=100nF가 VSSA/GND로 귀환합니다. 0Ω이므로 ‘1Ω RC 필터’로 계산하지 않습니다. 전원 정격과 기능은 ST 공식 제품 자료로 확인했습니다. "+ref("mcu_product"))
  body+=h("8MHz 크리스털과 12pF 두 개")+calc("프로젝트: Y1100 ABM3B-8.000MHZ-10-1-U-T, CL=10pF\nCL ≈ C1107×C1108/(C1107+C1108) + CSTRAY\n12pF×12pF/(12pF+12pF) + 가정 4pF = 10pF\n8MHz × PLL6 = 48MHz → 타이머 한 tick ≈20.833ns")
  body+=p("위 4pF는 핀·패턴의 기생용량 가정입니다. 실제 PCB에서 load pulling과 startup을 확인해야 합니다. R1102=0Ω은 초기 직렬 링크이며 크리스털 구동 전력·기동 여유를 보고 조정하는 자리입니다. 정확한 크리스털 구매품 drive level 자료는 이번에 확보하지 못해 프로젝트의 ≤100µW 요구만 표시합니다.")
  body+=h("리셋·부트·SWD")+calc("NRST: R1100=10kΩ, C1109=100nF → 외부 RC 명목1ms\nRESET 버튼을 누르면 NRST를 GND로 단락\nBOOT0: R1101=10kΩ로 기본 Low\nBOOT 서비스 헤더를 단락하면 CTRL_3V3를 BOOT0에 연결")
  body+=p("실제 reset 시간에는 내부 pull-up·문턱이 관여하므로 RC=1ms를 정밀 reset pulse 길이로 쓰지 않습니다. R1104/R1105=33Ω은 SWDIO/SWCLK 직렬 저항으로 링잉 완화를 노린 값이며 배선 길이와 debugger에 따라 확인합니다. J1100.1은 디버거 전압 감지 VTREF이고 보드에 전원을 밀어 넣는 핀이 아닙니다. 6번 SWO와7번 key 등 NC는 그대로 둡니다.")
  body+=h("GPIO를 기능별로 읽기")+p("EN_VBAT·EN_VDDI_DIG·EN_VDDI·EN_VCI·EN_VDDIO1V2·EN_SYS_1V8은 제어 출력입니다. PG와 PWR_FLT_N 및 6개 ALERT는 상태 입력입니다. I2C1은 양전압 10채널, I2C2는 VGL 측 절연기로 갑니다. PA0는 DIG ALERT와 TIM2 입력 캡처에 할당되어 있습니다. USB_ATTACH_3V3는 B12 attach를 제어합니다.")
  body+=warn("이번 ST 직접 다운로드는 시간 초과했고 웹 PDF 파서는 다른 F078 제목을 반환했습니다. 이를 F072 핀 검증 근거로 사용하지 않았습니다. 48핀 연결·기능은 실제 프로젝트/펌웨어와 대조했으며 DS9826 Rev6의 패키지 표 상세 재대조는 남은 항목입니다.")
  return ov,body,["크리스털 정확한 구매품 사양·PCB 기생·drive level·startup 검증 필요.","MCU DS9826 원문 패키지 표와 AF 매핑 재확인 항목을 남김.","전원 시퀀스·PG 지연·USB attach·고장 shutdown은 회로 연결만으로 구현 완료를 의미하지 않음."],["mcu","mcu_product"]
 if b==12:
  ov=p("<b>USB-C 데이터와 PC 접지를 보드의 측정 GND에서 분리하는 블록입니다.</b> USB 전력 전체를 보드로 공급하는 구조가 아니며, ADuM4160의 양측 전원은 각각 host VBUS와 CTRL_3V3입니다.")
  body=h("커넥터와 CC 저항")+p("J1200은 USB4105-GF-A이고 A6/B6은 D+, A7/B7은 D−로 각각 합쳐집니다. CC1과CC2는 서로 합치지 않고 R1200/R1201=5.1kΩ으로 USB_GND에 각각 내립니다. 뒤집어 꽂는 방향별 sink 인식을 위한 Rd 구성입니다. SBU A8/B8은 NC이며 PD 협상 회로는 없습니다.")
  body+=p("R1206=0Ω은 실드를 host측 USB_GND에 잇습니다. 네 shield stake는 하나의 S1 번호로 처리한 이전 수정본을 그대로 사용합니다. USB_GND를 GND/GND_F에 연결하는 부품은 이 회로에 없습니다. "+ref("gct"))
  body+=h("ADuM4160 양측 전원과 모드")+p("측1: VBUS1=USB_VBUS(5V), VDD1=USB_3V3_LOCAL은 내부 레귤레이터 쪽이며 C1201로 바이패스합니다. PDEN/SPU는 이 로컬3.3V에 연결됩니다. 측2: VBUS2와 VDD2를 모두 CTRL_3V3에 연결하고 SPD도 High입니다. 양측 full-speed 설정입니다. "+ref("usb"))
  body+=p("C1200/C1205는 host VBUS에100nF+1µF, C1201은 로컬 LDO에100nF입니다. C1202/C1203은 측2 각 전원 핀 근처100nF, C1204는1µF입니다. host VBUS 직접 명목용량은1.1µF이며 이것만으로 전체 USB compliance를 판정하지 않습니다.")
  body+=h("24Ω 직렬값과 attach")+p("R1202/R1203은 host D±, R1204/R1205는 MCU쪽 D±에 들어갑니다. ADuM full-speed 응용의 직렬 종단값24Ω를 따른 구성입니다. 두 데이터 선의 균형과 IC 가까운 위치가 중요하며 DC 전압 분배용 저항이 아닙니다.")
  body+=calc("R1207=100kΩ: PIN/USB_ATTACH_3V3의 기본 Low\nMCU가3.3V로 구동하면 풀다운 전류≈33µA\n초기 detach → USB 준비 후 MCU가 attach 허용")
  body+=h("ESD가 흐르는 경로")+p("U1201은 D+/D−→USB_GND, U1202/U1203은 각 CC→USB_GND, U1204는 VBUS→USB_GND에 붙습니다. 데이터 선에 전원을 공급하거나 USB PD 과전압을 지속 차단하는 부품은 아닙니다. 커넥터에 가깝고 host측 귀환 루프가 짧아야 합니다. "+ref("esd2")+" "+ref("esd1"))
  body+=p("절연은 신호 경로뿐 아니라 실드·mounting·계측기 접지까지 함께 유지해야 합니다. USB 절연 정격과 전체 시스템 안전 인증은 별개입니다.")
  return ov,body,["USB eye/배선 임피던스·ESD·attach 순서·양측 전원 off 조건 실측 필요.","GCT 원본 도면의 이전 로컬 사본은 보존. 실제 케이블·제조공차 확인은 별도.","USB와 보드 GND를 외부 장비가 우회 연결하는지 확인."],["usb","esd2","esd1","gct"]
 if b==13:
  ov=p("<b>MCU의3.3V EN/RESET을 MOSCATO·DUT용1.8V로 바꾸는 두 채널입니다.</b> SN74AXC2T45의 DIR을 VCCA에 묶어 A→B로 고정합니다. 이 부품에 별도의 OE 핀은 없습니다.")
  body=h("전원과 신호 경로")+p("VCCA=CTRL_3V3, VCCB=SYS_1V8입니다. C1300/C1301=100nF는 각각의 전원 로컬 바이패스입니다. A1→B1은 MOSCATO_EN, A2→B2는 DDI_RESET_N입니다. "+ref("level"))
  body+=h("양쪽 풀다운이 필요한 이유")+p("R1300/R1301=10kΩ은 MCU high-Z일 때 A측을 Low로 정합니다. R1304/R1305=10kΩ은 변환기 출력이 high-Z일 때 최종 B측 신호를 Low로 정합니다. EN Low는 꺼짐, RESET_N Low는 reset assert라는 서로 다른 기능을 같은 기본 Low로 달성합니다.")
  body+=calc("A측 High일 때 풀다운:3.3V/10kΩ=0.33mA\nB측 High일 때 풀다운:1.8V/10kΩ=0.18mA\n프로젝트 누설 가정8µA×10kΩ=80mV\nB측47Ω와10kΩ만 고려한 정적 High≈1.8×10000/10047=1.792V")
  body+=p("마지막 계산은 출력 구동 저항·부하를 제외한 설명용입니다. R1302/R1303=47Ω은 직렬 댐핑으로 링잉·과도 전류를 완화하려는 값입니다. 47Ω 자체가 전원-off 역급전을 차단하는 소자는 아닙니다. 전원-off 고임피던스는 IC의 해당 전원 조건과 Ioff 특성으로 판단합니다.")
  body+=h("제어 시퀀스에 미치는 영향")+p("SYS_1V8이 아직 없으면 B측 신호를 유효 High로 기대하지 않습니다. 먼저1.8V 전원을 확인하고 EN/RESET을 제어해야 합니다. 이미 만들어 둔 펌웨어 정책의 EN Low·RESET assert 순서는 실제 DUT 요구가 승인되어야 최종 확정됩니다.")
  return ov,body,["전원 순서·partial power-down·실부하 누설에서 안전한 기본 레벨 확인.","MCU/DUT의 실제 VIH/VIL과 파형으로47Ω을 검증.","DUT_SEQUENCE_APPROVED=false는 유지."],["level"]
 if b==14:
  ov=p("<b>생성·측정한 전원을 외부 DUT로 내보내는 다섯 헤더입니다.</b> 커넥터 정격과 회로 측정 full scale는 별개입니다. 이름이 옛 채널명인 핀도 실제 넷을 기준으로 읽습니다.")
  body=h("헤더별 역할")+table(["헤더","구성","역할"],[
   ["J1400","2×6","DIG·VDDI·VCI·VDDIO1V2·SYS_1V8·RESET_N과 인접 GND"],
   ["J1401","2×3","AVDDH1·AVDDH2_S_O·VGH1 / GND"],
   ["J1402","1×2","VGL1 / 시스템 GND"],
   ["J1403","2×6","LPDP·OSC·AVDDH2_GM·VGH2 및 GND"],
   ["J1404","1×2","VGL2 / 시스템 GND"]])
  body+=p("음전원 헤더의 귀환도 시스템 GND입니다. B8 내부의 GND_F를 DUT 공통 접지로 내보내지 않습니다. J1401의 심볼 이름 AVDDH2_DUT/VGH_DUT와 J1402의 VGL_DUT는 실제 넷 AVDDH2_S_O_DUT/VGH1_DUT/VGL1_DUT와 구분해 표에 모두 보입니다.")
  body+=h("접지 핀과 기구 구성")+p("전원 옆 GND 핀은 귀환 루프를 짧게 하기 위한 설계로 해석됩니다. 케이블에서 전원/귀환을 함께 보내는 배선이 중요합니다. Samtec TSW는2.54mm 피치이며 S/D가 행 수를 구분합니다. "+ref("header"))
  body+=p("프로젝트는 음전원과 양전원 헤더 간10mm 이상 분리와 서로 다른 핀수 등의 실수 완화를 기록했습니다. 이는 현재 회로도의 전기 연결에서 증명되는 치수가 아니므로 PCB/케이블에서 확인해야 합니다. 특히 J1403/J1404는 확장 제안 상태의 기구 검증 항목을 유지합니다.")
  body+=h("여기에는 R/C 계산이 없다")+p("헤더는 전압을 설정하거나 전류를 제한하지 않습니다. DUT 쪽 bulk cap·케이블 인덕턴스·접촉저항은 앞 블록의 기동/안정성/측정오차에 영향을 줍니다. <b>핀 전체 표가 실결선 기준</b>이며 짝 커넥터의 보는 방향과 pin1 표식을 대조해야 합니다.")
  return ov,body,["DUT 케이블 핀맵·반전·오삽입·pin1 표식 실물 검증 필요.","연결 가능한 부하전류는 션트/ADC/전원 정격으로 제한. 커넥터 정격만 보고 판단하지 않음.","J1403/J1404 기구·케이블 검증 미완료."],["header"]
 if b==15:
  ov=p("<b>전원·상태 LED, 추가 점검 패드, 장착홀과 실크 지시입니다.</b> 측정 전원에서 표시 LED 전류를 빼지 않도록 POWER는 AUX_5V, 나머지는 MCU GPIO에 연결했습니다.")
  body=h("LED 전류와 저항값")+calc("ILED ≈ (VSUPPLY − VF) / R\nVF=2.0V를 가정한 예시 (실제 LED MPN 미정)\nPOWER: (5−2)/3.3kΩ ≈0.91mA, PR≈2.73mW\nSTATUS/FAULT: (3.3−2)/1.5kΩ ≈0.87mA, PR≈1.13mW")
  body+=p("R1500은3.3kΩ, R1501/R1502는1.5kΩ입니다. D1500/1501/1502의1번 K는GND,2번 A는저항 쪽입니다. MCU가 LED_STATUS/LED_FAULT를 High로 만들면 전류를 공급하는 active-high 구조입니다. 적색과 녹색의 Vf·광효율이 다를 수 있어 동일 저항이 동일 밝기를 뜻하지 않습니다.")
  body+=h("추가 테스트패드와 기구 항목")+p("TP1500~1508은 NRST·BOOT0·VDDA·PB9 spare·USB attach·1.8V 제어·USB VBUS/GND를 관찰합니다. BOM 제외로 표시되어도 PCB에는 패드가 존재합니다. H1500~1503은3.2mm M3 NPTH이며 전기 핀이 없습니다. LOGO1500은 회로 소자가 아니라 실크 지시입니다.")
  body+=p("프로젝트의 홀 가장자리에서2mm 구리 keepout은 PCB에서 검증할 조건입니다. 금속 standoff가 USB 절연 경계나 GND_F를 시스템/섀시 접지에 묶지 않도록 봐야 합니다. LOGO1500의 REV C/날짜 문자열은 원본의 과거 지시를 그대로 보여 주며 최종 제품 revision을 승인한 것이 아닙니다.")
  body+=h("부품 선정 근거의 한계")+p("LED의 정확한 구매품이 없으므로 Vf 최악값·밝기·전류·극성을 제조사 표와 최종 대조할 수 없습니다. 위 계산은 설계 원리를 보이는 조건부 예시이고, 후보 부품의 데이터시트를 만들어 인용하지 않았습니다.")
  return ov,body,["LED MPN·광도·핀 극성 및 MCU GPIO 총전류 확인.","NPTH/keepout·실크·테스트패드 접근성은 PCB 검증 대상.","실크 revision/날짜는 제작 릴리스 때 별도로 정리해야 함."],[]
