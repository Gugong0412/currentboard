"""Produce one offline tabbed document from the unchanged final design."""
from pathlib import Path
import json,re,html,hashlib,collections
from guide_model import *
from guide_content import TITLES,story,table,ref,SOURCES
from html import escape as E

DIAG=OUT/"schematics";DIAG.mkdir(exist_ok=True)
from guide_detail import supplement
from draw_schematics import build as build_schematics
NETID={n:f"n{i}" for i,n in enumerate(sorted(NETS))}
GROUNDS={"GND","GND_F","USB_GND","PWR_RTN"}
def grouped(b):
 cs=[c for c in C.values() if block(c)==b and not c["ref"].startswith("#")]
 groups=collections.OrderedDict()
 if b==11:
  groups={"통합 전체":cs}
  sets={"전원":"U1100 C1100 C1101 C1102 C1103 C1104 R1103 C1105 C1106",
        "클록":"U1100 Y1100 R1102 C1107 C1108",
        "리셋·부트·SWD":"U1100 R1100 C1109 SW1100 R1101 J1101 R1104 R1105 J1100"}
  for label,refs in sets.items():groups[label]=[C[r] for r in refs.split()]
  return cs,groups
 if b==8:
  groups={"통합 전체":cs,"부유 전원":[c for c in cs if c["ref"] in "U800 C800 C801 R800 NT800 U810 R810 C810 C811 C812 C813".split()],
  "절연 I2C":[c for c in cs if c["ref"] in "U830 R830 R831 R832 R833 C830 C831 C832 C833".split()],
  "VGL1":[c for c in cs if c["ref"] in "R807 U820 R820 R821 R822 C820 C821 C822".split()],
  "VGL2":[c for c in cs if c["block"]=="B8_VGL2"]}
  return cs,groups
 if b==10:
  groups={"전체 TP":cs}
  for label,a,z in [("입력·공급",1000,1008),("션트·sense",1009,1036),("부유·상태",1037,1049),("제어·버스",1050,1062),("ALERT",1063,1069)]:
   groups[label]=[c for c in cs if a<=int(c["ref"][2:])<=z]
  return cs,groups
 if b==12:
  groups={"통합 전체":cs}
  groups["커넥터·ESD"]=[c for c in cs if c["ref"] in "J1200 R1200 R1201 R1202 R1203 R1206 U1201 U1202 U1203 U1204 C1200 C1205".split()]
  groups["절연기·MCU측"]=[c for c in cs if c["ref"] not in "J1200 R1200 R1201 R1206 U1201 U1202 U1203 U1204".split()]
  return cs,groups
 sheets=sorted(set(c["block"] for c in cs))
 if len(sheets)>1:groups["통합 전체"]=cs
 for sheet in sheets:
  members=[c for c in cs if c["block"]==sheet]
  if b==7:
   ch=next(ch for ch in FW["channels"] if ch["ref"] in {c["ref"] for c in members})
   sh=C[ch["shunt_ref"]]
   if sh not in members:members=members+[sh]  # contextual B5 shunt, labelled by source block
  groups[sheet]=members
 return cs,groups

STYLE="""
html{overflow-x:hidden}*{box-sizing:border-box}body{margin:0;overflow-x:hidden;color:#193744;background:#edf3f4;font:16px/1.85 'Malgun Gothic',Arial,sans-serif}
main{max-width:1300px;margin:auto;padding:35px 42px 80px}h1{font-size:34px;line-height:1.4;margin:8px 0 18px}h2{font-size:25px;margin:0 0 20px}h3{font-size:19px;margin:26px 0 10px}
p{margin:12px 0 18px}section{background:white;border:1px solid #d4e2e5;border-radius:14px;padding:28px;margin:22px 0}a{color:#057c84}
.eyebrow{font-size:13px;color:#087e80;font-weight:bold;letter-spacing:2px}.muted{color:#617783;font-size:13px}
.note{padding:18px;border-left:4px solid #0b9291;background:#eaf6f4;margin:20px 0}.warn{background:#fff5e4;border-color:#c28a29}
.formula{background:#173845;color:#effbfb;padding:20px;border-radius:9px;white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.9 Consolas,'Malgun Gothic',monospace}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:11px 12px;border-bottom:1px solid #dbe4e7;vertical-align:top;min-width:70px}th{background:#edf3f5;text-align:left;white-space:nowrap}td code{font-size:12px;overflow-wrap:anywhere}
.tablewrap{overflow:auto}.tablewrap td:last-child{min-width:230px}.source{display:inline-block;font-size:13px;margin:4px 6px 4px 0}
button,select,input{font:inherit;padding:8px 12px;border:1px solid #c1d5d8;border-radius:7px;background:white;color:#193744}button{cursor:pointer}input{max-width:100%;width:320px}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0}.diagram{overflow:auto;max-height:760px;border:1px solid #c4d8dd;border-radius:8px;background:white;overscroll-behavior:contain}
.drawing{width:100%;min-width:0;margin:auto}.drawing svg{width:100%;height:auto;display:block}.drawing .edge path{cursor:pointer}.drawing .node.net{cursor:pointer}
.diagram.is-focus .wire:not(.selected){opacity:.25}.diagram .wire.selected{stroke:#d04d20!important;stroke-width:4!important}
.netinfo{background:#f1f6f8;border:1px solid #d5e4e8;padding:12px;overflow-wrap:anywhere;font-size:13px;min-height:56px}
.chip{font-size:11px;padding:2px 6px;border-radius:4px;background:#fff0d9;color:#885a17}
.jump{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.jump a{font-size:13px;text-decoration:none;padding:5px 10px;background:white;border:1px solid #d4e2e5;border-radius:6px}
details{padding:12px;border:1px solid #dbe5e8;margin:14px 0;border-radius:8px}summary{cursor:pointer;font-weight:bold}section{scroll-margin-top:16px}
.netbtn{font-size:12px;padding:2px 5px;margin:2px 0;border:0;background:#e9f3f6;overflow-wrap:anywhere;max-width:260px;text-align:left}
.metrics{display:flex;flex-wrap:wrap;gap:12px}.metrics span{padding:10px 16px;background:#dcefeb;border-radius:7px}
@media(max-width:700px){main{padding:22px 15px}h1{font-size:26px}section{padding:20px 15px}.drawing{min-width:0}}
@media print{body{background:white;font-size:11px}main{padding:0;max-width:none}section{border-radius:0;padding:15px}.noprint,.toolbar,.jump{display:none}.diagram{overflow:visible;max-height:none}.drawing{width:100%!important;min-width:0}tr,.formula,.note{break-inside:avoid}.tablewrap{overflow:visible}table{font-size:10px}h1{font-size:26px}.formula{color:black;background:#f0f5f5}h2,h3{break-after:avoid}.diagram.is-focus .edge,.diagram.is-focus .node{opacity:1}}
"""
def endpoint_button(c,p):
 nk=net(c,p)
 if p["net"]=="NC":return "<code>미연결 / NC</code>"
 return f'<button class="netbtn" data-net="{E(NETID[nk])}">{E(nk)}</button>'
def channel_table(b,cs):
 channels=[ch for ch in FW["channels"] if ch["ref"] in {c["ref"] for c in cs}]
 if not channels:return ""
 rows=[]
 for ch in channels:
  c=C[ch["ref"]];a0=next(p["net"] for p in c["pins"] if p["name"]=="A0");a1=next(p["net"] for p in c["pins"] if p["name"]=="A1")
  al=PINS[c["ref"]+".3"];mcu=[x for x in NETS[al] if x.startswith("U1100.")]
  gpio=next((p["port"] for p in FW["pins"] if "U1100."+p["number"] in mcu),None)
  rows.append([ch["rail"],ch["ref"],f'{ch["shunt_ref"]} / {ch["R_ohm"]:g}Ω',f'I2C{ch["bus"]} / 0x{ch["address_7bit"]:02X}',f"A1={a1}<br>A0={a0}",f'±{ch["full_scale_current_A"]*1000:.5g}mA',gpio or "polling"])
 return '<h3>실제 채널 설정 / 펌웨어 대조</h3>'+table(["채널","IC","션트","주소","주소 핀","ADC full scale","MCU ALERT"],rows)
def page(b,cs,diagrams):
 ov,body,review,sources=story(b,C,FW)
 flow,detail=supplement(b,cs)
 ov+=flow
 body+=detail
 # Pin table includes all physical endpoints, including passive components.
 pinrows=[]
 for c in cs:
  for p in c["pins"]:
   pinrows.append([E(c["ref"]),E(p["number"]),E(p["name"]),endpoint_button(c,p),E(pin_reason(c,p))])
 partrows=[]
 for c in cs:
  note=c["Note"]
  population=c["Population"] if c["ref"] not in POP_CONFLICTS else "충돌: BOM "+c["Population"]+" / Value "+COMPXML[c["ref"]].findtext("value")
  partrows.append([E(c["ref"])+f'<br><small>{E(c["block"])}</small>',E(c["Value"]),'<span class="chip">'+E(population)+'</span>',E(part_reason(c)),E(c["Rating"]),E(c["MPN"])+(f'<details><summary>원 설계 메모</summary>{E(note)}</details>' if note else "")])
 flags=[c for c in C.values() if block(c)==b and c["ref"].startswith("#")]
 flagshtml="<p class='muted'>ERC 가상 선언: "+", ".join(E(c["ref"]+" → "+c["pins"][0]["net"]) for c in flags)+". 전원 생성 부품이 아닙니다.</p>" if flags else ""
 interfaces=[]
 own={c["ref"] for c in cs}
 for nk in sorted({net(c,p) for c in cs for p in c["pins"] if p["net"]!="NC"}):
  ext=[x for x in NETS[nk] if x.rsplit(".",1)[0] not in own]
  if ext:
   if short(nk) in GROUNDS or len(ext)>16:description=", ".join(ext[:12])+f" … 총{len(ext)}개 핀"
   else:description=", ".join(ext)
   interfaces.append([E(nk),E(description)])
 diagrammeta=[dict(label=label,file=name+".svg") for label,name in diagrams]
 data={"diagrams":diagrammeta,"nets":{NETID[n]:{"name":n,"pins":NETS[n]} for n in NETS}}
 counts=f'<div class="metrics"><span>블록 항목 {len(cs)}개</span><span>실제 핀 {len(pinrows)}개</span><span>원본 보존 · 006 표기 수정</span></div>'
 sourceshtml="".join("<li>"+ref(k)+"</li>" for k in sources) if sources else "<li>이 블록에는 확정된 전용 IC 응용 데이터시트가 없습니다. 프로젝트 계약·BOM·저장된 네이티브 넷리스트를 근거로 설명했습니다.</li>"
 # Embed the authored application SVGs generated during prepare().
 svgs=[]
 for label,name in diagrams:
  f=DIAG/(name+".svg")
  if not f.exists():raise FileNotFoundError(f)
  svg=f.read_text(encoding="utf-8")
  svg=svg[svg.index("<svg"):]
  svg=re.sub(r'<\?xml.*?\?>|<!DOCTYPE.*?>','',svg,flags=re.S)
  svgs.append(svg)
 data["svgs"]=svgs
 options="".join(f'<option value="{i}">{E(label)}</option>' for i,(label,name) in enumerate(diagrams))
 doc=f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>B{b} · {TITLES[b]}</title><style>{STYLE}</style></head><body><main>
<header><div class="eyebrow">R2 CIRCUIT READING GUIDE / B{b:02d}</div><h1>{E(TITLES[b])}</h1>{counts}<p class="muted">2026-10-20 · R2_REPAIRED_006 · 1차 검토용 / 수치는 명목·명시한 조건의 계산입니다. 질문은 사용자 검토 후 별도 보강합니다.</p>
<div class="jump"><a href="#purpose">기능</a><a href="#circuit">통합 연결도</a><a href="#reasoning">값·동작 해설</a><a href="#parts">모든 부품</a><a href="#pins">모든 핀</a><a href="#review">검토 항목</a><a href="#sources">출처</a></div></header>
<section id="purpose"><h2>01 · 이 블록의 기능과 경계</h2>{ov}{channel_table(b,cs)}</section>
<section id="circuit"><h2>02 · 부품과 실제 넷을 합친 통합 연결도</h2>
<p>B1과 같은 회로 기호로 IC와 주변 R·C·L, 제어·피드백 경로를 함께 배치했습니다. <b>●는 접속점</b>이며 선의 교차만으로는 연결되지 않습니다. <b>같은 넷 이름은 전기적으로 연결</b>됩니다. 주황 점선 소자는 DNP, 션트의 금색 선은 같은 물리 단자의 동박 연결입니다. 핀 위치는 읽기 위한 기능 배치로 실제 패키지 방향이 아닙니다.</p>
<div class="toolbar"><select id="diagram-choice" aria-label="회로 범위">{options}</select><button id="fit">전체 보기</button><button id="zoom">확대</button><button id="clear-net">강조 해제</button><button id="print">이 블록 인쇄/PDF</button></div>
<p class="muted">‘통합 전체’에는 이 블록의 모든 전기 부품이 들어갑니다. 복잡한 블록은 같은 회로의 하위 범위를 골라 읽을 수 있습니다. 넷 이름이나 배선을 누르면 같은 넷의 연결선과 외부 블록 핀 목록을 확인할 수 있습니다.</p>
<div class="diagram"><div class="drawing" id="drawing"></div></div><div class="netinfo" id="net-info">넷 이름 또는 배선을 클릭해 전원·접지·신호의 연결을 따라가세요.</div>{flagshtml}
<details><summary>다른 블록으로 이어지는 넷</summary>{table(["실제 넷","외부 핀 (많으면 일부 표시)"],interfaces)}</details></section>
<section id="reasoning"><h2>03 · 값의 근거와 동작 해설</h2><p class="muted">연결 사실은 네이티브 넷리스트, 정격 조건은 출처, 계산은 본문의 가정에 근거합니다. 기록이 없는 선정 의도는 회로에서 추정한 설명입니다.</p>{body}</section>
<section id="parts"><h2>04 · 모든 부품의 역할과 선정 상태</h2><input class="filter noprint" data-table="parts-table" placeholder="부품 검색: 예 C203, 100n, DNP" aria-label="부품 검색"><div id="parts-table">{table(["부품 / 시트","값","실장","이 값·연결의 이유","프로젝트 요구 정격","MPN / 원 기록"],partrows)}</div></section>
<section id="pins"><h2>05 · 모든 핀의 연결 이유</h2><input class="filter noprint" data-table="pins-table" placeholder="핀 검색: 예 EN, FB, GND_F" aria-label="핀 검색"><p class="muted">IC·커넥터뿐 아니라 수동소자 핀도 포함했습니다. 넷 버튼은 위 연결도의 해당 경로를 강조합니다. 핀이 없는 기구/실크 항목은 부품 표에만 있습니다.</p><div id="pins-table">{table(["부품","핀","핀 이름","실제 네이티브 넷","연결 이유"],pinrows)}</div></section>
<section id="review"><h2>06 · 1차 검토 결과와 남은 확인</h2><ul>{"".join("<li>"+E(x)+"</li>" for x in review)}</ul><p>006 수정본은 R525·R526의 Value 표시만 BOM·실장 상태와 맞췄습니다. 기존 원본과 12채널 연결은 보존했습니다. KiCad 10.0.7로 새 넷리스트·ERC를 생성하여 8,437개 검사 통과, ERC 위반 0건을 확인했습니다. 실측 검증은 미완료입니다.</p></section>
<section id="sources"><h2>07 · 출처와 원본</h2><ul>{sourceshtml}</ul><p><a href="../R2_REPAIRED_006/BOM.csv">원 BOM</a> · <a href="../R2_REPAIRED_006/source_contract.json">연결 계약</a> · <a href="../R2_FIX_REPORTS_006/native/verified_netlist.xml">최종 네이티브 넷리스트</a> · <a href="ALL_BLOCKS_EVIDENCE.json">문서 대조 기록</a></p><p class="muted">본문과 SVG는 단일 HTML에 포함되어 오프라인에서도 표시됩니다. 출처 PDF·원본 파일 링크에는 인터넷 또는 같은 폴더 구조가 필요합니다.</p></section>
<footer class="muted">B{b} · 회로 설명용 / 생산 승인 문서 아님 · 실제 핀/값은 원본에서 추출 · 미확정 MPN과 DNP 유지</footer></main>
<script>const DATA={json.dumps(data,ensure_ascii=False).replace("</","<\\/")};</script><script>{JS}</script></body></html>"""
 return doc

JS=r"""
const drawing=document.querySelector('#drawing'),diagram=document.querySelector('.diagram');
function showDiagram(i){drawing.innerHTML=DATA.svgs[+i];fitDiagram();diagram.classList.remove('is-focus');document.querySelector('#net-info').textContent='넷 이름을 클릭해 연결을 확인하세요.'}
function selectNet(id){
 const net=DATA.nets[id];if(!net)return;
 diagram.classList.add('is-focus');drawing.querySelectorAll('.selected').forEach(e=>e.classList.remove('selected'));
 drawing.querySelectorAll('[data-net]').forEach(e=>{if(e.dataset.net===net.name)e.classList.add('selected')});
 document.querySelector('#net-info').textContent=net.name+' → '+net.pins.join(' · ');
}
drawing.addEventListener('click',e=>{const hit=e.target.closest('[data-net]');if(hit){const id=Object.keys(DATA.nets).find(k=>DATA.nets[k].name===hit.dataset.net);selectNet(id)}});
document.querySelectorAll('.netbtn').forEach(x=>x.onclick=()=>{const id=x.dataset.net;const found=[...drawing.querySelectorAll('[data-net]')].some(e=>e.dataset.net===DATA.nets[id].name);if(!found){document.querySelector('#diagram-choice').value=0;showDiagram(0)}selectNet(id);document.querySelector('#circuit').scrollIntoView({behavior:'smooth'})});
document.querySelector('#diagram-choice').onchange=e=>showDiagram(e.target.value);
function fitDiagram(){const svg=drawing.querySelector('svg');if(!svg)return;const v=svg.viewBox.baseVal;drawing.style.width=Math.min(diagram.clientWidth,v.width)+'px'}
document.querySelector('#fit').onclick=fitDiagram;
document.querySelector('#zoom').onclick=()=>drawing.style.width=Math.max(drawing.offsetWidth*1.4,1400)+'px';
document.querySelector('#clear-net').onclick=()=>{diagram.classList.remove('is-focus');drawing.querySelectorAll('.selected').forEach(e=>e.classList.remove('selected'))};
document.querySelectorAll('.filter').forEach(x=>x.oninput=()=>{document.querySelectorAll('#'+x.dataset.table+' tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(x.value.toLowerCase()))});
document.querySelector('#print').onclick=()=>{fitDiagram();diagram.classList.remove('is-focus');document.querySelectorAll('tr[hidden]').forEach(x=>x.hidden=false);window.print()};
showDiagram(0);
"""

def prepare():
 checked=validate();plans,diagram_checks=build_schematics()
 checked["native_export_rerun"]=False
 checked["native_verification_reference"]="R2_FIX_REPORTS_006/native/verification_summary.json (existing report; unchanged inputs)"
 evidence={"date_kst":"2026-10-20","scope":"B1–B15 authored application schematics and detailed explanation; design inputs unchanged","validation":checked,"diagrams":diagram_checks,
 "source_inputs":{str(f.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(f.read_bytes()).hexdigest() for f in [PROJECT/"source_contract.json",PROJECT/"BOM.csv",PROJECT/"firmware_definitions.json",ROOT/"R2_FIX_REPORTS_006/native/verified_netlist.xml"]},
 "known_incomplete":["B9 actual PMIC/MPN/application missing","MCU DS9826 package table direct-PDF recheck unavailable","Unselected passive/LED MPNs cannot be qualified","No bench measurements; existing 006 native ERC report retained, not rerun for this documentation revision"]}
 (OUT/"ALL_BLOCKS_EVIDENCE.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Prepared",len(diagram_checks),"diagrams;",checked)

def assemble():
 plans=json.loads((OUT/"diagram_plan.json").read_text(encoding="utf-8"));docs={}
 docs["B1"]=(OUT/"B1_GUIDE.html").read_text(encoding="utf-8")
 for b in range(2,16):
  cs,_=grouped(b);doc=page(b,cs,plans[str(b)])
  (OUT/f"B{b}_GUIDE.html").write_text(doc,encoding="utf-8");docs[f"B{b}"]=doc
 tabs="".join(f'<button role="tab" id="tab-B{b}" data-block="B{b}" aria-controls="document" aria-selected="false"><b>B{b}</b><span>{E({1:"입력 보호",**{x:TITLES[x].split(" · ")[0] for x in TITLES}}[b])}</span></button>' for b in range(1,16))
 index=[{"ref":c["ref"],"value":c["Value"],"block":"B"+str(block(c))} for c in C.values() if not c["ref"].startswith("#")]
 outer="""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="guide-revision" content="b1-style-v3"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R2 회로 해설서 · B1–B15</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf3f4;font:14px 'Malgun Gothic',Arial;color:#193744;height:100vh;display:flex;flex-direction:column}
header{background:#183845;color:white;padding:14px 22px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}h1{font-size:20px;margin:0}header small{color:#bed6dc}input{padding:8px 12px;border:1px solid #759ba6;border-radius:6px;width:240px;font:inherit}
#tabs{display:flex;flex-wrap:wrap;gap:6px;padding:10px 16px;background:#f4f8f9;border-bottom:1px solid #c7dce0}
#tabs button{background:white;border:1px solid #c6d9de;border-radius:7px;cursor:pointer;padding:7px 11px;color:#234b5a;text-align:left;font:inherit}
#tabs b{display:block;font-size:14px}#tabs span{font-size:11px;white-space:nowrap}
#tabs button[aria-selected=true]{background:#087e80;color:white;border-color:#087e80}iframe{border:0;width:100%;flex:1;min-height:0;background:#edf3f4}
#search-result{padding:7px 18px;background:#fff4da;display:none}#search-result button{margin:4px;padding:6px;cursor:pointer}
@media(max-width:650px){header{padding:12px;gap:8px}header h1{font-size:17px}header small{font-size:11px}#tabs{flex-wrap:nowrap;overflow:auto;padding:8px}#tabs button{flex-shrink:0}input{width:180px}}
</style></head><body><header><h1>R2 회로 해설서 · B1–B15</h1><small>12채널 최종 작업본 · 1차 검토 · 2026.10.20</small><input id="search" aria-label="전체 부품 찾기" placeholder="부품 찾기: U830, R507…"></header>
<nav id="tabs" role="tablist" aria-label="회로 블록">__TABS__</nav><div id="search-result"></div><iframe id="document" title="선택한 블록 해설" aria-labelledby="tab-B1"></iframe>
<script>const DOCS=__DOCS__,INDEX=__INDEX__;const frame=document.querySelector('#document');
function openBlock(id){if(!DOCS[id])id='B1';document.querySelectorAll('[data-block]').forEach(b=>{let active=b.dataset.block===id;b.setAttribute('aria-selected',active);b.tabIndex=active?0:-1});frame.srcdoc=DOCS[id];frame.setAttribute('aria-labelledby','tab-'+id);history.replaceState(null,'','#'+id)}
document.querySelectorAll('[data-block]').forEach(b=>{b.onclick=()=>openBlock(b.dataset.block);b.onkeydown=e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){let n=+b.dataset.block.slice(1)+(e.key==='ArrowRight'?1:-1);n=n<1?15:n>15?1:n;openBlock('B'+n);document.querySelector('#tab-B'+n).focus()}}});
document.querySelector('#search').oninput=e=>{const q=e.target.value.toUpperCase().trim(),box=document.querySelector('#search-result');box.replaceChildren();box.style.display=q?'block':'none';if(!q)return;const results=INDEX.filter(x=>x.ref.toUpperCase().includes(q)||x.value.toUpperCase().includes(q)).slice(0,18);if(!results.length)box.textContent='일치하는 부품이 없습니다.';results.forEach(x=>{let b=document.createElement('button');b.textContent=x.block+' · '+x.ref+' · '+x.value;b.onclick=()=>openBlock(x.block);box.append(b)})};
window.addEventListener('hashchange',()=>openBlock(location.hash.slice(1)));openBlock(location.hash.slice(1)||'B1');
</script></body></html>"""
 outer=outer.replace("__TABS__",tabs).replace("__DOCS__",json.dumps(docs,ensure_ascii=False).replace("</","<\\/")).replace("__INDEX__",json.dumps(index,ensure_ascii=False))
 (OUT/"ALL_BLOCKS_GUIDE.html").write_text(outer,encoding="utf-8")
 print("Assembled 15 tabs; standalone bytes",len(outer.encode("utf-8")))

if __name__=="__main__":
 import sys
 if "--assemble" in sys.argv:assemble()
 else:prepare()
