# DDI 소비전류 측정보드

모바일 디스플레이 DDI의 전원 레일 7개(VDDI_DIG, VDDI, VCI, AVDDH1, AVDDH2, VGH, VGL)의 평균 소비전류를 측정하는 보드입니다.
120Hz / 1Hz 구동 조건에서 ±0.5% 정확도를 목표로 합니다.

- 측정: 채널별 단일 션트 + INA228 (VGL은 절연 플로팅 측정)
- 제어: STM32F072CBT6, USB 절연(ADuM4160), PC Python UI
- 전원: 12V 단일 입력, moscato(외부 PMIC)용 VBAT 3.8V/1A 생성

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `요구사항*.txt` | 초기 요구사항과 답변 |
| `current board 프롬프트*.txt` | 단계별 설계 AI 지시 프롬프트 |
| `DDI_Current_Board_Phase1*.html` | Phase 1: 아키텍처, 부품 선정, 오차 예산 (Rev.A / Rev.B) |
| `DDI_Phase2_1_Detailed_Design.html` | Phase 2-1: 전원부 + 측정 아날로그부 상세 설계 |
| `DDI_Phase2_2_Integrated_Design.html` | Phase 2-2: MCU·USB·레벨시프터·DUT 헤더 + 전체 통합 설계 |
| `DDI_Phase2_2_KiCad/` | KiCad 회로도 프로젝트, 넷리스트, BOM, 검증 기록 |
| `netcheck/` | KiCad 넷리스트 ↔ 설계 계약 자동 대조 스크립트 |

## 넷리스트 대조

```bash
cd netcheck
python kicad_netcheck.py ddi_contract.json board.net             # 전체 검사
python kicad_netcheck.py ddi_contract.json board.net --partial   # 작성 도중 검사
```
Windows에서는 `run_netcheck.bat`을 더블클릭해도 됩니다.

## 현재 상태 (2026-10-11)

- 회로도 연결: 설계 계약과 **오류 0건** (부품 336, 핀 870)
- 남은 작업: 커스텀 풋프린트 18개 지정 (4단자 션트 7, USB ESD 4, 인덕터 2 등), moscato 실제 핀맵 반영
- 다음 단계: PCB 레이아웃, 펌웨어, Python UI
