# B1–B15 회로 해설서

[ALL_BLOCKS_GUIDE.html](ALL_BLOCKS_GUIDE.html)을 다운로드해 브라우저에서 열면 15개 블록을 탭으로 읽을 수 있습니다. HTML 본문과 연결도는 한 파일에 포함되어 있으며 인터넷 없이 작동합니다. 출처·원본 링크에는 인터넷 또는 저장소 폴더 구조가 필요합니다.

현재 입력은 `R2_REPAIRED_006`과 `R2_FIX_REPORTS_006/native/verified_netlist.xml`입니다. R525 DNP / R526 FIT 표기 정정을 반영했습니다. VDDI·LPDP·OSC 공통 공급원은 U520/VDDI_SRC이며 DIG/U500과 별개입니다. B9는 미확정 인터페이스이고 제조사 자료 확보가 미완료인 항목은 본문에 표시했습니다.

## 재생성

저장소 루트에서 Python과 Node.js를 사용합니다. Node 의존성은 이 폴더에서 `npm install`로 설치합니다. 회로도 변경 뒤에는 먼저 새 네이티브 검증을 수행하고 생성기 입력 경로를 갱신해야 합니다.

```text
python R2_BLOCK_GUIDE/build_b1.py
python R2_BLOCK_GUIDE/build_all.py prepare
node R2_BLOCK_GUIDE/render_diagrams.cjs
python R2_BLOCK_GUIDE/build_all.py --assemble
node R2_BLOCK_GUIDE/check_b1.cjs
node R2_BLOCK_GUIDE/check_all.cjs
```

화면 검사는 로컬 Microsoft Edge를 사용합니다. 다른 위치에 설치된 Playwright는 `PLAYWRIGHT_MODULE`로 지정할 수 있습니다. Graphviz SVG는 `@viz-js/viz` 3.12.0으로 생성하며 최종 HTML 실행에는 이 라이브러리가 필요하지 않습니다.

`ALL_BLOCKS_EVIDENCE.json`은 입력 해시·핀 대조·연결도 범위, `ALL_BLOCKS_QA.json`은 탭과 연결도 UI 검사 결과입니다. 제조사 PDF 캐시와 화면 캡처는 로컬에 보관하고, 출처 링크와 생성 도구는 저장소에 포함합니다.
