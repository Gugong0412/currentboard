DDI Current Board - Phase 2-2 KiCad schematic
작성: 2026-10-11 / KiCad 8.0.9에서 검증

열기
1. ZIP 전체를 한 폴더에 압축 해제합니다. 하위 폴더와 라이브러리 파일을 함께 유지합니다.
2. KiCad 8.x에서 DDI_Phase2_2.kicad_pro를 엽니다.
3. 회로도 편집기를 열고 루트 시트에서 원하는 기능 시트를 더블클릭합니다.
4. KiCad가 없으면 DDI_Phase2_2_Schematic.pdf를 엽니다.

범위
- Phase2-2 B1~B15 전체. 루트1 + 기능 시트30 = 총31시트.
- 입력 OVP/UVLO: R100/R101/R102=110k/4.99k/10k.
- 입력 C500/C520/C540/C600/C620=10uF; C501/C521/C541/C601/C621 삭제.
- MCU48pin, HSE, SWD, USB-C/ADuM4160, AXC level shifter, DUT header, LED/기구 포함.
- 이전 Phase2-1 파일은 수정하지 않았습니다.
- 글로벌 라벨은 시트 전체 연결, 로컬 라벨은 해당 시트 안에서만 연결합니다.
- 부품이 선으로 연속 배치되지 않은 부분도 같은 이름의 라벨로 연결됩니다.

검증
- source_contract.json: Phase2-2 원본 계약. 344개 항목, 897개 핀, 151개 named net.
- KiCad CLI에서 새로 내보낸 verified_netlist.xml과 모든 named net의 Ref.pin 집합 대조: PASS.
- NC19개도 각각 고립된 핀으로 검증했습니다. NC라는 공통넷은 없습니다.
- 실제 KiCad 8.0.9 ERC: 오류0, 경고0, 제외 규칙0.
- 회로도 추가항목: #FLG1100 하나. MCU_VDDA의1ohm 필터 뒤 전원 공급을 ERC에 선언합니다.
  구매 부품/PCB 실장 대상이 아니며 실제 연결 변경이 아닙니다.
  schematic_additions.json에 구분하고 원본 계약은 변경하지 않았습니다.
- 총 배치345개 중 power flag9개. 그 외에는 기계홀/실크/TP 등 비구매 항목도 포함합니다.
- verification_summary.json 및 erc_report.json에 결과를 보관했습니다.

라이브러리 및 풋프린트
- DDI_Project.kicad_sym은 계약의 핀 번호를 명시한 프로젝트 전용 기능 심볼입니다.
  모든 심볼은 회로도에도 내장되어 있어 외부 심볼 라이브러리 없이 열 수 있습니다.
  심볼 모양은 실제 패키지의 외관/배치도가 아닙니다.
- sym-lib-table/fp-lib-table은 프로젝트 상대 경로를 사용합니다.
- 확인된 기존 풋프린트 일부는 DDI_Verified.pretty에 동봉했습니다.
- 기타 정식 KiCad 풋프린트 이름은 KiCad 기본 풋프린트 패키지를 사용합니다.
- Project:/USER_PROVIDED/확인 필요 항목의 실제 Footprint 필드는 비워 두고
  RequestedFootprint에 원 요구사항을 보존했습니다. 19개 할당 보류 항목은
  pending_footprints.json에서 확인하십시오. 이번 산출물은 PCB 레이아웃이 아닙니다.
- 4단자 Kelvin shunt 심볼은 물리2단자+논리4pad 구조이며 copper_bridges 계약에 맞춰
  커스텀 풋프린트 구현이 필요합니다. 심볼을 단순2pin저항으로 바꾸면 계약이 달라집니다.
- USB shell의4개 stake는 S1 공통 pad number로 구현하는 계약입니다.

제작 전에 남은 사항
- MOSCATO U900은 물리핀 번호가 확정되지 않은 논리 placeholder입니다.
- DUT/MOSCATO 전원 인가/제거 순서와 reset/settling 시간은 제조사 자료로 확정해야 합니다.
- 미확정 패키지/MPN, MLCC 유효용량, USB/clock/열/OVP 과도응답을 검증해야 합니다.
- GND_F는 VGL floating domain이며 시스템 GND와 합치지 않습니다.
- USB_GND와 시스템 GND도 직접 합치지 않습니다.
- ERC와 계약 대조 통과가 실제 성능 검증 또는 제작 승인 의미는 아닙니다.
- 상세 계산/BOM/펌웨어/리스크는 동봉 HTML을 참고하십시오.

재검증 (KiCad CLI가 PATH에 있는 환경)
kicad-cli sch export netlist --format kicadxml -o verified_netlist.xml DDI_Phase2_2.kicad_sch
kicad-cli sch erc --format json -o erc_report.json DDI_Phase2_2.kicad_sch
python validate_project.py
kicad-cli sch export pdf -o DDI_Phase2_2_Schematic.pdf DDI_Phase2_2.kicad_sch

변경 뒤에는 위 파일을 다시 생성하십시오. 동봉 검증은 현재 버전의 회로도 기준입니다.
