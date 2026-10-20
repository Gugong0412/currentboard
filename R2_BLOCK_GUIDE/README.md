# B1–B15 회로 해설서

[ALL_BLOCKS_GUIDE.html](ALL_BLOCKS_GUIDE.html)을 다운로드해 브라우저에서 열면 15개 블록을 탭으로 읽을 수 있습니다. HTML 본문과 연결도는 한 파일에 포함되어 있으며 인터넷 없이 작동합니다. 출처·원본 링크에는 인터넷 또는 저장소 폴더 구조가 필요합니다.

현재 입력은 `R2_REPAIRED_006`과 `R2_FIX_REPORTS_006/native/verified_netlist.xml`입니다. R525 DNP / R526 FIT 표기 정정을 반영했습니다. VDDI·LPDP·OSC 공통 공급원은 U520/VDDI_SRC이며 DIG/U500과 별개입니다. B9는 미확정 인터페이스이고 제조사 자료 확보가 미완료인 항목은 본문에 표시했습니다.

## 재생성

저장소 루트에서 Python과 Node.js를 사용합니다. Node 의존성은 이 폴더에서 `npm install`로 설치합니다. 회로도 변경 뒤에는 먼저 새 네이티브 검증을 수행하고 생성기 입력 경로를 갱신해야 합니다.

```text
python R2_BLOCK_GUIDE/build_b1.py
python R2_BLOCK_GUIDE/build_all.py prepare
python R2_BLOCK_GUIDE/build_all.py --assemble
python R2_BLOCK_GUIDE/publish_site.py
node R2_BLOCK_GUIDE/check_b1.cjs
node R2_BLOCK_GUIDE/check_all.cjs
node R2_BLOCK_GUIDE/check_drawings.cjs
```

화면 검사는 로컬 Microsoft Edge를 사용합니다. 다른 위치에 설치된 Playwright는 `PLAYWRIGHT_MODULE`로 지정할 수 있습니다. 현재 도식은 `draw_schematics.py`의 회로별 배치와 실제 넷리스트로 생성합니다. `prepare`가 이 생성기도 호출합니다. 이전 `diagrams/`와 `render_diagrams.cjs`는 과거 핀–넷 그래프 기록이며 현재 HTML에서 사용하지 않습니다.

B1은 승인된 문서를 그대로 포함합니다. B2–B15는 실제 소자 기호·배선의 통합 도식, 기능 흐름, 값 계산과 조건, 전체 R·C별 해설, 부품 목록, 핀 연결, 자료 출처를 제공합니다. 근거가 없는 선정 의도는 단정하지 않고 계산 가정과 확인 필요 사항을 구분합니다. B9 미확정 영역과 VGL1·2 polling은 유지합니다. `publish_site.py`는 같은 문서를 `docs/index.html`에 복사하면서 출처 경로를 GitHub 링크로 변환합니다.

`SCHEMATIC_DRAWING_AUDIT.json`은 33개 도식의 단자·넷 대조 결과이며, `DRAWING_LAYOUT_QA.json`의 빈 배열은 도식 글자 겹침·잘림 검사의 지적이 없음을 뜻합니다. 이 문서 개정은 회로 파일을 수정하지 않았으며 새 ERC 실행을 뜻하지 않습니다. 전기 검증은 006 보고서와 입력 해시를 참조합니다.

`ALL_BLOCKS_EVIDENCE.json`은 입력 해시·핀 대조·연결도 범위, `ALL_BLOCKS_QA.json`은 탭과 연결도 UI 검사 결과입니다. 제조사 PDF 캐시와 화면 캡처는 로컬에 보관하고, 출처 링크와 생성 도구는 저장소에 포함합니다.
