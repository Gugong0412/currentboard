# Current Board — PCB 착수 전 인수·검증 상태 (2026-10-13)

> **판정: PCB 제작 착수 보류(HOLD).** 이 문서는 기존 설계 결정을 변경하지 않으며, 2026-10-11 GitHub 스냅샷의 작업 상태와 다음 검증 게이트를 기록한다. 과거 ERC/넷리스트 합격은 실측 및 제작 승인이 아니다.

## 1. 기준 소스 / 버전

- 저장소: `Gugong0412/currentboard`, 기준 브랜치 `main`
- 이 문서 작성 전 기준 커밋: `f06bd7eb74f0cd9625022c07a0ec082299a467f3` (2026-10-11 22:22 KST)
- 단계별 설계: `DDI_Current_Board_Phase1_revB.html` → `DDI_Phase2_1_Detailed_Design.html` → `DDI_Phase2_2_Integrated_Design.html`
- 실제 회로도: `DDI_Phase2_2_KiCad/DDI_Phase2_2_KiCad/DDI_Phase2_2.kicad_sch` (루트+하위 30시트)
- 연결 계약 3종: HTML 내 `script#contract`, `.../source_contract.json`, `netcheck/ddi_contract.json`
- 대조 원본: `.../verified_netlist.xml`, `.../erc_report.json`, `.../verification_summary.json`, `.../pending_footprints.json`

## 2. 실제 확인된 완료 사항

- B1~B15 상세 설계 문서와 KiCad 계층 회로도 존재.
- GitHub에 저장된 과거 KiCad 8.0.9 검증: 31시트, 345개 배치 심볼(전원 플래그 포함), 물리 심볼 336개, 계약 핀 897개, 명명 넷 151개, NC 19핀, ERC 오류 0/경고 0/제외 0.
- **2026-10-13 별도 데이터 재대조**: GitHub에 커밋된 `verified_netlist.xml` 내 명명 넷 151개의 Ref.pin 집합이 `source_contract.json`과 전부 일치. 내보낸 총 170개 넷 중 추가 19개는 각 하나의 NC 핀만 포함함. ※ KiCad를 새로 실행한 결과가 아니라, GitHub에 있는 *기존 내보내기 파일*을 독립적으로 재검사한 결과.
- 세 연결 계약 JSON은 파싱 후 내용 동등.
- GitHub 외 별도 저장된 Phase 2-2 HTML(516,428바이트)의 Git blob SHA-1 `61bae2f6a49d14f85ebf8b4ba5c17a300f3190b3`는 GitHub `main`의 파일 SHA와 동일.
- `DDI_Phase2_2.net`와 `netcheck/board.net`는 저장소 트리에서 동일 blob SHA를 가짐.

## 3. 변경 없이 유지할 승인/선택 사항

- 12V/2A 단일 입력, AUX 및 CTRL_3V3 default-on; **DUT 레일만 MCU GPIO 제어**.
- 측정 레일 7개(VDDI_DIG, VDDI, VCI, AVDDH1, AVDDH2, VGH, VGL), 채널당 INA228+단일 Kelvin 션트; ADCRANGE=0, MODE=Ah (shunt-only continuous), VBUS는 션트 전단에서 창 전후 측정.
- Logic 션트: VDDI_DIG=20Ω, VDDI=20Ω, VCI=100Ω; 기본 구조 TPS7A90 LDO + 후단 FB remote sense, local FB 대체 선택 점퍼 유지.
- VGL: 소스측 플로팅 GND_F, RFM-0505S + TPS7A16 + ISO1641; 시스템 GND와 GND_F 단락 금지.
- TE 미사용. VDDI_DIG INA228 SOVL ALERT를 MCU 타이머 양에지 캡처로 검출하여 blank 직후 charge snapshot 동기.
- MCU STM32F072CBT6, USB 절연 ADuM4160, SN74AXC2T45 레벨시프터; active-low DDI RESET.
- 1장 시제품 부품/PCB/조립 100만원 목표(견적·실측 승인 아님).
- Phase 2-2 변경 F1~F3: OVP 약 15V/UVLO 약 10V 저항 변경, 보조 LDO 입력 커패시터 10µF, ISO1641 DW16 핀맵 대조 결과 유지.

## 4. 실장 풋프린트 보류: FIT 18개 / 물리 핀맵 미확정 PLACEHOLDER 1개

`pending_footprints.json`의 **19개 항목 중 18개가 FIT**, `U900` 한 개는 PLACEHOLDER. 루트 README의 '풋프린트 18개'는 FIT만 집계한 것으로 모순이 아님.

| 분류 | RefDes | 수량 | 다음 확인 항목 |
|---|---|---:|---|
| eFuse PWP16 EP | U100 | 1 | TPS26600PWPR 제조사 land pattern, 1~16+EP17, EP=RTN, 열비아 |
| 입력 전해 C | C102 | 1 | 실제 35V/47µF MPN 선정 후 body/pad/극성 확인 |
| XFL4020 인덕터 | L200, L300 | 2 | XFL4020-222MEC pad 치수/코트야드/극성·제조사 도면 |
| 4패드 Kelvin 분리 션트 | R507, R527, R547, R737, R747, R757, R807 | 7 | RT1206 2단자 물리 부품을 FORCE/SENSE 논리 4패드로 구현; copper bridge, 넷리스트/DRC 동시 확인 |
| 절연 DC/DC SIP4 | U800 | 1 | RFM-0505S pin pitch/body/pin 번호 및 절연 영역 |
| TPS7A16 DGN EP | U810 | 1 | 8핀+EP9 제조사 치수, 핀/EP GND_F 연결 |
| USB ESD DRT3 | U1201 | 1 | TPD2EUSB30DRTR 핀 1~3, 치수/실장 패드 |
| ESD DPY2 | U1202, U1203, U1204 | 3 | TPD1E10B06DPYR 핀 1~2, 치수/극성 |
| AXC SSOP8 DCT | U1300 | 1 | SN74AXC2T45DCTR SSOP-8 DCT 치수, 핀 1~8 |
| **MOSCATO 실물 제공 필요** | **U900** | **1 별도** | Confidential 실제 MPN/회로 입력·출력 핀 번호/footprint/제어·시퀀스 수령 후 논리 placeholder 교체 |

**상태:** 위 FIT 18개는 모두 아직 `pending_footprints.json`에 존재한다. 부품번호·패드번호·Land Pattern 확인 없이 자동 할당/제작 승인하지 않는다.

## 5. 추가 위험 및 확인 불가

**P0 / PCB 또는 DUT 전원 인가 전에 해결**
1. U900 MOSCATO 실제 핀맵·패키지·전원 특성·EN 동작 명시. 현재 1~9는 임시 논리 핀이다.
2. DDI/MOSCATO 제조사별 전원 인가·제거, RESET, settling time 확정. 그 전 자동 전체 시퀀스 승인 금지.
3. 모든 FIT 18개 풋프린트 확정, 특히 Kelvin FORCE/SENSE 분리, 전원부 노출패드, USB ESD 소형 패키지.
4. eFuse/OVP hot-plug·서지·후단 과도전압(정격/절대최대값) 검증.

**P1 / 시제품 검증**
- TPS7A90 저부하 정확도/원격 FB 루프 안정도; MLCC DC bias 후 유효용량.
- INA228 SOVL 펄스 양에지 검출, 1Hz 정수 프레임 동기, 미검출 유효성 플래그 및 교정.
- 독립 플로팅 GND_F 및 USB_GND 절연 경계, SYS_1V8 OFF 역급전.
- 열 편차(정밀 션트/INA 영역 목표 ≤5°C), USB enumeration, 120Hz·1Hz ±0.5% 평균전류 실측.
- 1장 부품+PCB+조립 실제 견적 100만원 이내 판정.

**현재 저장소에서 확인되지 않은 산출물**
- `.kicad_pcb` PCB 완성본, MCU 펌웨어 구현, PC Python UI 구현, 실측 로그/제작 승인서.
- 기존 Work 대화 원문의 마지막 지시 및 GitHub에 아직 커밋하지 않은 로컬 변경분. 본 파일은 커밋된 자료만 기준으로 한다.

## 6. 다음 실행 순서 / 판정 기준

1. **풋프린트 evidence matrix 완성:** 각 분류의 제조사 원본 도면/리비전/land pattern/패드 번호, 실제 MPN 및 선정된 KiCad footprint path를 기록. 미확인 항목은 미확인 유지.
2. **KiCad 전기 연결 불변 확인:** 각 실장 풋프린트의 pad number가 연결 계약과 일치하는지 점검. 4패드 Kelvin의 접합은 원본 `copper_bridges` 규칙을 준수. U900 논리 핀 → 실제 핀 전환 시 계약도 함께 버전 갱신.
3. **변경 후 재생성/재검증:** `kicad-cli sch export netlist` → `python validate_project.py`; `kicad-cli sch erc` → 오류/경고/제외 재평가; `python netcheck/kicad_netcheck.py ...` 재실행. *이전 PASS 재사용 금지*.
4. **PCB 설계 착수 게이트:** 18개 실장 풋프린트 미정 0, U900 실제 핀맵 확정, 위험 P0 근거 수집, 연결/핀/전원 경계 검증 완료.
5. PCB 작업 뒤 DRC/제조제약/열/기구 리뷰. 전기 성능은 실제 조립품 측정으로 별도 승인.

최종 구분: **연결 계약 대조 PASS / PCB 제작 승인 HOLD**.
