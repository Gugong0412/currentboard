# DDI Current Board · R2 최종 작업본

검증된 **12채널** 회로도와 전원·측정·ALERT 연결을 모은 브랜치입니다. 현재 기준은 `R2_REPAIRED_006`이며 VGL1·2는 절연 I2C2 polling을 유지합니다.

웹에서 바로 보기: **[B1~B15 회로 해설서](https://gugong0412.github.io/currentboard/)**. GitHub Pages는 `main`의 `/docs`를 게시하며, 현재 작업 결과는 `main`에 반영되어 있습니다.

## 먼저 열기

| 목적 | 파일 |
|---|---|
| B1~B15 탭형 회로 해설서 | [ALL_BLOCKS_GUIDE.html](R2_BLOCK_GUIDE/ALL_BLOCKS_GUIDE.html) |
| 인터랙티브 HTML 블록도 | [R2_INTERACTIVE_DIAGRAM.html](R2_FIX_REPORTS_006/R2_INTERACTIVE_DIAGRAM.html) |
| GitHub에서 바로 보는 블록도 | [BLOCK_DIAGRAM.md](R2_FIX_REPORTS_006/BLOCK_DIAGRAM.md) |
| 최종 KiCad 프로젝트 | [DDI_Phase2_2_R2.kicad_pro](R2_REPAIRED_006/DDI_Phase2_2_R2.kicad_pro) |
| BOM | [BOM.csv](R2_REPAIRED_006/BOM.csv) |
| 최종 검증 증거 | [verification_summary.json](R2_FIX_REPORTS_006/native/verification_summary.json) |
| 변경 이력·정리 기록 | [history/README.md](history/README.md) |

**HTML 사용:** 다운로드한 파일을 브라우저에서 여세요. 서버·외부 라이브러리 없이 작동합니다. GitHub 파일 화면은 HTML을 실행하지 않습니다. 전원/채널/통신 탭, 채널별 상세, 확대·축소, 인쇄 기능을 제공합니다.

## 현재 상태

- 2026-10-20: R525 Value `0R [DNP]`, R526 Value `0R`로 실장 상태와 표시 일치. 배선·BOM·펌웨어 변경 없음.
- KiCad **10.0.7**, **8,437개 검사 통과**, ERC **36시트 오류·경고 0건**.
- 실제 부품 379개, 명명 넷 181개, NC 19핀, copper bridge 선언 25개.
- AVDDH2 S/O ALERT → MCU PB3, VGH1 ALERT → PB4 연결 복구.
- MCU 직접 ALERT 6채널. VGL1·2를 포함한 나머지 6채널은 전용 ALERT MCU 연결 없이 I2C polling 구성.
- 승인된 12채널·고정 션트·공통 공급원 분기·절연 도메인 유지.
- 기존 ERC 비활성 규칙을 유지한 결과입니다. 실측·PCB DRC·정확도·제작 승인은 미완료이며 **제작 HOLD**입니다.

`R2_REPAIRED_006`는 새 검증 입력과 바이트 동일합니다. 이전 원본 `R2_REPAIRED_005`와 검증 기록도 그대로 보존했습니다. 그 안의 이전 README 및 `R2_VALIDATION_STATUS.json`은 초안 생성 시점 기록이며 현재 상태는 위 최종 검증 증거를 따릅니다.

## 재검증·HTML 재생성

Python 3.10 이상과 KiCad CLI 10.0.7을 사용합니다. `kicad-cli`를 PATH에 등록하고 전역 footprint 테이블 및 `KICAD10_FOOTPRINT_DIR`를 설정하세요. work/out에는 존재하지 않는 새 폴더를 지정합니다.

```text
python tools/r2/verify_r2_directory.py --project R2_REPAIRED_006 --work R2_VERIFY_WORK_NEW --out R2_LOCAL_CHECK_NEW --expected-kicad 10.0.7
python R2_FIX_REPORTS_006/build_explorer.py
```

HTML은 최종 네이티브 넷리스트와 펌웨어 정의에서 생성하며 `explorer-template.html`이 편집 원본입니다. Playwright와 Edge가 설치된 환경에서는 `node R2_FIX_REPORTS_006/check_explorer.cjs`로 UI 동작을 검사합니다. `PLAYWRIGHT_MODULE`, `BROWSER_CHANNEL`로 설치 경로와 브라우저를 지정할 수 있습니다.

## 정리 원칙

최종 프로젝트·검증 증거·HTML과 도구를 유지하고, 요구사항·변경 기록·과거 검증 요약은 `history/`에 모았습니다. 구버전 설계 HTML, 중복 KiCad 프로젝트와 중간 넷리스트는 현재 브랜치에서 제거했습니다. 로컬 원본은 유지했고 제거 전 전체 자료는 커밋 `3569bfe`에서 복구할 수 있습니다. `main`과 Git 이력은 변경하지 않았습니다.
