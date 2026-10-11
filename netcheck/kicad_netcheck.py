#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDI 소비전류 측정보드 — KiCad 넷리스트 ↔ 설계 계약 대조 스크립트

사용법
------
1) KiCad 회로도 편집기에서 넷리스트 내보내기
     파일 → 내보내기 → 넷리스트 → "KiCad" 탭 → 내보내기  (→ *.net)
   (BOM용 XML(*.xml)도 읽을 수 있습니다.)

2) 실행
     python kicad_netcheck.py ddi_contract.json  board.net
     python kicad_netcheck.py DDI_Phase2_2_Integrated_Design.html board.net   # HTML 직접도 가능

   옵션
     --partial          그리는 도중 검사: 회로도에 아직 없는 부품은 오류로 치지 않음
     --blocks B5_DIG,B7_VDDI_DIG   지정 블록만 검사 (부분 검사 자동 적용)
     --csv report.csv   모든 결과를 CSV로 저장 (엑셀에서 열기)
     --no-fields        Value/Footprint/MPN 필드 비교 생략

검사 항목
---------
  [오류] 끊김     : 계약상 같은 넷인 핀들이 KiCad에서 서로 다른 넷으로 나뉨
  [오류] 단락     : 계약상 다른 넷인 핀들이 KiCad에서 한 넷으로 합쳐짐 (GND↔GND_F 등)
  [오류] NC 연결  : 계약상 미연결(NC)인 핀이 다른 핀과 연결됨
  [오류] 부품 누락 / 계약에 없는 부품·핀 / 미할당 RefDes(R?)
  [경고] 넷 이름  : GLOBAL 넷의 라벨 이름이 계약과 다름
  [경고] 필드     : Value / Footprint / MPN / DNP 불일치
  [정보] 이름 없는 넷(Net-(...)) 등

종료 코드: 오류 0건이면 0, 있으면 1
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# 데이터 구조
# ---------------------------------------------------------------------------


@dataclass
class Comp:
    ref: str
    value: str = ""
    footprint: str = ""
    fields: dict = field(default_factory=dict)  # 소문자 키
    dnp: bool = False
    sheet: str = ""


@dataclass
class Netlist:
    comps: dict  # ref -> Comp
    node_net: dict  # "REF.PIN" -> 넷 이름 (원본)
    net_nodes: dict  # 넷 이름 -> set("REF.PIN")


@dataclass
class Finding:
    level: str  # 오류 / 경고 / 정보
    kind: str
    target: str
    detail: str


# ---------------------------------------------------------------------------
# 계약 로더
# ---------------------------------------------------------------------------


def load_contract(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".html", ".htm") or text.lstrip().startswith("<"):
        m = re.search(
            r'<script[^>]*id="contract"[^>]*>(.*?)</script>', text, re.S
        )
        if not m:
            sys.exit(f"[중단] {path.name} 안에서 연결 계약(JSON)을 찾지 못했습니다.")
        text = m.group(1)
    return json.loads(text)


# ---------------------------------------------------------------------------
# KiCad 넷리스트 파서 (S-expression .net / XML)
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r'\(|\)|"((?:[^"\\]|\\.)*)"|[^\s()"]+')


def _sexpr(text: str):
    stack, cur = [], []
    for m in _TOKEN.finditer(text):
        tok = m.group(0)
        if tok == "(":
            stack.append(cur)
            cur = []
        elif tok == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(1) is not None:
            cur.append(m.group(1).replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(tok)
    return cur[0] if cur else []


def _kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def _val(node, name, default=""):
    k = _kids(node, name)
    if k and len(k[0]) > 1 and not isinstance(k[0][1], list):
        return k[0][1]
    return default


def parse_kicad_sexpr(text: str) -> Netlist:
    root = _sexpr(text)
    if not root or root[0] != "export":
        sys.exit("[중단] KiCad 넷리스트 형식이 아닙니다 (export 루트 없음).")
    comps = {}
    for block in _kids(root, "components"):
        for c in _kids(block, "comp"):
            ref = _val(c, "ref")
            comp = Comp(ref=ref, value=_val(c, "value"), footprint=_val(c, "footprint"))
            for fs in _kids(c, "fields"):
                for f in _kids(fs, "field"):
                    name = _val(f, "name")
                    v = next((x for x in f[1:] if not isinstance(x, list)), "")
                    comp.fields[name.lower()] = v
            for p in _kids(c, "property"):
                name = _val(p, "name").lower()
                comp.fields.setdefault(name, _val(p, "value"))
                if name == "dnp":
                    comp.dnp = True
                if name == "sheetname":
                    comp.sheet = _val(p, "value")
            comps[ref] = comp
    node_net, net_nodes = {}, defaultdict(set)
    for block in _kids(root, "nets"):
        for n in _kids(block, "net"):
            name = _val(n, "name")
            for nd in _kids(n, "node"):
                key = f"{_val(nd, 'ref')}.{_val(nd, 'pin')}"
                node_net[key] = name
                net_nodes[name].add(key)
    return Netlist(comps, node_net, dict(net_nodes))


def parse_kicad_xml(text: str) -> Netlist:
    root = ET.fromstring(text)
    comps = {}
    for c in root.iter("comp"):
        ref = c.get("ref", "")
        comp = Comp(ref=ref, value=c.findtext("value", ""), footprint=c.findtext("footprint", ""))
        for f in c.iter("field"):
            comp.fields[f.get("name", "").lower()] = (f.text or "")
        for p in c.iter("property"):
            name = p.get("name", "").lower()
            comp.fields.setdefault(name, p.get("value", ""))
            if name == "dnp":
                comp.dnp = True
            if name == "sheetname":
                comp.sheet = p.get("value", "")
        comps[ref] = comp
    node_net, net_nodes = {}, defaultdict(set)
    nets = root.find("nets")
    for n in (nets if nets is not None else []):
        name = n.get("name", "")
        for nd in n.iter("node"):
            key = f"{nd.get('ref')}.{nd.get('pin')}"
            node_net[key] = name
            net_nodes[name].add(key)
    return Netlist(comps, node_net, dict(net_nodes))


def load_netlist(path: Path) -> Netlist:
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_kicad_xml(text) if text.lstrip().startswith("<") else parse_kicad_sexpr(text)


# ---------------------------------------------------------------------------
# 정규화 도우미
# ---------------------------------------------------------------------------


def short_name(kicad_net: str) -> str:
    """'/B5_DIG/VDDI_DIG_FB' → 'VDDI_DIG_FB', 'VDDI_DIG_SRC' → 그대로."""
    return kicad_net.rstrip("/").split("/")[-1]


def is_auto(kicad_net: str) -> bool:
    s = short_name(kicad_net)
    return s.startswith("Net-(") or s.startswith("unconnected-(")


def norm_value(v: str) -> str:
    s = re.sub(r"\[\s*dnp\s*\]", "", (v or ""), flags=re.I)  # "100p [DNP]" 표기 허용
    s = s.strip().lower().replace(" ", "")
    s = s.replace("µ", "u").replace("μ", "u").replace("ω", "").replace("ohm", "")
    s = s.split("/")[0]  # "8MHz / CL10pF" → "8mhz"
    s = re.sub(r"^(\d+(?:\.\d+)?)r$", r"\1", s)  # 20R → 20
    s = re.sub(r"^(\d+)r(\d+)$", r"\1.\2", s)  # 3R01 → 3.01
    s = re.sub(r"(\d)(k|m|u|n|p)f$", r"\1\2", s)  # 100nF → 100n
    return s


def norm_fp(fp: str) -> str:
    fp = (fp or "").strip()
    return re.sub(r"\s*\(.*\)\s*$", "", fp)


def is_placeholder(s: str) -> bool:
    s = (s or "").strip()
    return (not s) or s in ("N/A", "USER_PROVIDED") or s.startswith("확인 필요") or "확인 필요" in s


# ---------------------------------------------------------------------------
# 대조
# ---------------------------------------------------------------------------


def compare(contract: dict, nl: Netlist, partial: bool, blocks: set | None, check_fields: bool):
    out: list[Finding] = []
    add = lambda lv, k, t, d: out.append(Finding(lv, k, t, d))

    # 계약 정리 (#FLG 등 가상 전원기호 제외)
    scope = {n["name"]: n.get("scope", "") for n in contract["nets"]}
    comps = [c for c in contract["components"] if not c["ref"].startswith("#")]
    if blocks:
        comps = [c for c in comps if c["block"] in blocks]
    cref = {c["ref"]: c for c in comps}
    all_contract_refs = {c["ref"] for c in contract["components"]}

    exp_node_net, nc_nodes = {}, set()
    for c in comps:
        for p in c["pins"]:
            key = f"{c['ref']}.{p['number']}"
            (nc_nodes.add(key) if p["net"] == "NC" else exp_node_net.__setitem__(key, p["net"]))

    # --- 부품 존재 ---
    present = {r for r in set(nl.comps) | {k.split(".")[0] for k in nl.node_net} if not r.startswith("#")}
    for ref in sorted(present):
        if "?" in ref:
            add("오류", "미할당 RefDes", ref, "Annotate(부품 번호 매기기)를 실행하고 계약 RefDes로 맞추세요")
    missing = sorted(r for r in cref if r not in present and cref[r]["pins"])
    if missing:
        if partial:
            add("정보", "미작성 부품", f"{len(missing)}개", ", ".join(missing[:40]) + (" …" if len(missing) > 40 else ""))
        else:
            for r in missing:
                add("오류", "부품 누락", r, f"{cref[r]['block']} / {cref[r]['Value']}")
    if not blocks:
        for r in sorted(present - all_contract_refs):
            if "?" not in r:
                add("오류", "계약에 없는 부품", r, "RefDes 오기 또는 계약 외 추가 부품")

    checked_refs = {r for r in cref if r in present}

    # --- 핀 단위: 계약에 없는 핀 / NC 핀 연결 ---
    for key, net in nl.node_net.items():
        ref = key.split(".")[0]
        if ref not in checked_refs:
            continue
        if key not in exp_node_net and key not in nc_nodes:
            add("오류", "계약에 없는 핀", key, f"KiCad 넷 '{short_name(net)}' — 심볼 핀 번호가 계약과 다른지 확인")
    for key in sorted(nc_nodes):
        net = nl.node_net.get(key)
        if net is None or net.startswith("unconnected-") or short_name(net).startswith("unconnected-"):
            continue
        others = sorted(n for n in nl.net_nodes.get(net, ()) if n != key)
        if others:
            add("오류", "NC 핀 연결", key, f"'{short_name(net)}' 에 {', '.join(others[:6])} 와 연결됨")

    # --- 계약 핀이 KiCad에 없음 ---
    exp_present = {k: v for k, v in exp_node_net.items() if k.split(".")[0] in checked_refs}
    for key in sorted(exp_present):
        if key not in nl.node_net:
            add("오류", "핀 미연결/없음", key, f"계약 넷 '{exp_present[key]}' — 배선 누락 또는 심볼 핀 번호 불일치")

    # --- 토폴로지 ---
    # KiCad 넷마다 '주인' 계약 넷(가장 많은 핀이 속한 넷)을 정한 뒤,
    #  · 주인이 아닌 소수 핀            → 핀 오결선 (핀 단위로 바로 고칠 수 있게)
    #  · 계약 넷 전체가 남의 넷에 흡수   → 넷 단락
    #  · 한 계약 넷이 '주인'인 KiCad 넷이 2개 이상 → 끊김
    GROUND = ("GND", "GND_F", "PWR_RTN", "USB_GND")
    exp_groups = defaultdict(set)
    for k, n in exp_present.items():
        if k in nl.node_net:
            exp_groups[n].add(k)
    owner = {}
    for an, nodes in nl.net_nodes.items():
        cnt = defaultdict(int)
        for k in nodes:
            if k in exp_present:
                cnt[exp_present[k]] += 1
        if cnt:
            owner[an] = max(sorted(cnt), key=lambda n: cnt[n])

    mapping = {}  # 계약 넷 → KiCad 넷(정상 1:1)
    for en, nodes in sorted(exp_groups.items()):
        by_actual = defaultdict(set)
        for k in nodes:
            by_actual[nl.node_net[k]].add(k)
        owned = [a for a in by_actual if owner.get(a) == en]
        for a, ks in by_actual.items():
            if owner.get(a) == en:
                continue
            # VGL 플로팅(_F, GND_F)과 시스템 쪽이 섞이면 절연이 깨짐
            cross = (en in GROUND or owner[a] in GROUND
                     or ("_F" in en or en.startswith("F_")) != ("_F" in owner[a] or owner[a].startswith("F_")))
            if ks == nodes:  # 계약 넷 전체가 다른 넷에 흡수
                sev = " ⚠ 접지/절연 경계 단락" if cross else ""
                add("오류", "넷 단락", f"{owner[a]} + {en}",
                    f"서로 다른 계약 넷 2개가 KiCad 넷 '{short_name(a)}' 하나로 합쳐짐{sev}")
            else:
                for k in sorted(ks):
                    sev = " ⚠ 접지/절연 경계 교차" if cross else ""
                    add("오류", "핀 오결선", k,
                        f"계약 '{en}' 이어야 하는데 '{owner[a]}' 쪽(KiCad '{short_name(a)}')에 연결됨{sev}")
        if len(owned) > 1:
            parts = "  |  ".join(
                f"[{short_name(a)}] {', '.join(sorted(by_actual[a])[:5])}{' …' if len(by_actual[a]) > 5 else ''}"
                for a in sorted(owned, key=lambda a: -len(by_actual[a]))
            )
            add("오류", "끊김", en, f"{len(owned)}조각으로 분리(배선/라벨 누락): {parts}")
        elif len(owned) == 1 and len(by_actual) == 1:
            mapping[en] = owned[0]
        elif len(owned) == 1:
            mapping[en] = owned[0]

    # --- 넷 이름 ---
    for en, an in sorted(mapping.items()):
        sn = short_name(an)
        if sn == en:
            continue
        if scope.get(en) == "GLOBAL":
            if is_auto(an):
                add("경고", "넷 이름 없음", en, f"GLOBAL 넷인데 라벨 없음(KiCad: {sn}) — global label '{en}' 추가 권장")
            else:
                add("경고", "넷 이름 불일치", en, f"KiCad 이름 '{sn}'")
        elif is_auto(an):
            add("정보", "로컬 넷 이름 없음", en, f"KiCad: {sn} (연결은 정상, 라벨 추가 권장)")
        else:
            add("경고", "넷 이름 불일치", en, f"KiCad 이름 '{sn}' (로컬 넷)")

    # --- 필드 ---
    if check_fields:
        lib_swaps = defaultdict(list)  # (계약 라이브러리 → KiCad 라이브러리) → refs
        for ref in sorted(checked_refs):
            c, k = cref[ref], nl.comps.get(ref)
            if k is None:
                continue
            ev, kv = c.get("Value", ""), k.value
            if not is_placeholder(ev) and norm_value(ev) != norm_value(kv):
                add("경고", "Value 불일치", ref, f"계약 '{ev}' / KiCad '{kv}'")
            ef, kf = norm_fp(c.get("Footprint", "")), norm_fp(k.footprint)
            if is_placeholder(ef) or ef == "N/A":
                pass
            elif not kf:
                add("경고", "Footprint 미지정", ref, f"PCB 전 지정 필요 — 계약 '{ef}' ({c.get('Value', '')})")
            elif ef != kf:
                elib, _, ename = ef.rpartition(":")
                klib, _, kname = kf.rpartition(":")
                if ename == kname:  # 풋프린트 이름은 같고 라이브러리만 다름 → 의도된 이동
                    lib_swaps[(elib or "(없음)", klib or "(없음)")].append(ref)
                else:
                    add("경고", "Footprint 불일치", ref, f"계약 '{ef}' / KiCad '{kf}'")
            em = c.get("MPN", "")
            km = k.fields.get("mpn", "")
            if not is_placeholder(em):
                if not km:
                    add("경고", "MPN 필드 없음", ref, f"계약 MPN '{em}' 입력 필요")
                elif km.strip() != em.strip():
                    add("경고", "MPN 불일치", ref, f"계약 '{em}' / KiCad '{km}'")
            pop = c.get("Population", "")
            kdnp = k.dnp or k.fields.get("population", "").upper() == "DNP"
            if pop == "DNP" and not kdnp:
                add("경고", "DNP 미표시", ref, "계약상 미실장(DNP)인데 KiCad에 DNP 표시 없음")
            if pop == "FIT" and kdnp:
                add("경고", "DNP 오표시", ref, "계약상 실장(FIT)인데 KiCad에 DNP로 표시됨")
        for (elib, klib), refs in sorted(lib_swaps.items()):
            add("정보", "라이브러리만 다름", f"{elib} → {klib}",
                f"{len(refs)}개, 풋프린트 이름은 동일 (예: {', '.join(refs[:6])}{' …' if len(refs) > 6 else ''})")

    # --- 설계 규칙 (계약과 별개로 반드시 지켜야 하는 것) ---
    def net_of(key):
        return short_name(nl.node_net[key]) if key in nl.node_net else None

    jumpers = [("R505", "R506"), ("R525", "R526"), ("R545", "R546")]
    for a, b in jumpers:
        if a in nl.comps and b in nl.comps:
            da = nl.comps[a].dnp or nl.comps[a].fields.get("population", "").upper() == "DNP"
            db = nl.comps[b].dnp or nl.comps[b].fields.get("population", "").upper() == "DNP"
            if da == db:
                state = "둘 다 실장 → 션트 우회(측정 불가)" if not da else "둘 다 미실장 → FB 개방(전압 폭주)"
                add("오류", "FB 점퍼 규칙", f"{a}/{b}", state)

    return out, checked_refs, exp_present


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------

ORDER = {"오류": 0, "경고": 1, "정보": 2}


def report(findings, checked_refs, exp_present, nl, csv_path):
    findings.sort(key=lambda f: (ORDER[f.level], f.kind, f.target))
    cnt = {lv: sum(1 for f in findings if f.level == lv) for lv in ORDER}
    print("=" * 72)
    print(" DDI 측정보드 넷리스트 대조 결과")
    print("=" * 72)
    print(f" 검사 부품 {len(checked_refs)}개 / 검사 핀 {len(exp_present)}개 / KiCad 넷 {len(nl.net_nodes)}개")
    print(f" 오류 {cnt['오류']}건 · 경고 {cnt['경고']}건 · 정보 {cnt['정보']}건")
    print("-" * 72)
    cur = None
    for f in findings:
        head = f"[{f.level}] {f.kind}"
        if head != cur:
            print(f"\n{head}")
            cur = head
        print(f"  - {f.target}: {f.detail}")
    if not findings:
        print("\n  계약과 완전히 일치합니다.")
    print()
    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as fp:
            w = csv.writer(fp)
            w.writerow(["등급", "종류", "대상", "내용"])
            for f in findings:
                w.writerow([f.level, f.kind, f.target, f.detail])
        print(f" CSV 저장: {csv_path}")
    return cnt["오류"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="KiCad 넷리스트 ↔ DDI 설계 계약 대조")
    ap.add_argument("contract", type=Path, help="ddi_contract.json 또는 설계 HTML")
    ap.add_argument("netlist", type=Path, help="KiCad 넷리스트 (.net 또는 .xml)")
    ap.add_argument("--partial", action="store_true", help="그리는 중: 없는 부품은 오류로 치지 않음")
    ap.add_argument("--blocks", default="", help="검사할 블록 (예: B5_DIG,B7_VDDI_DIG)")
    ap.add_argument("--csv", default="", help="결과 CSV 경로")
    ap.add_argument("--no-fields", action="store_true", help="Value/Footprint/MPN 비교 생략")
    a = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 한글 깨짐 방지

    contract = load_contract(a.contract)
    nl = load_netlist(a.netlist)
    blocks = {b.strip() for b in a.blocks.split(",") if b.strip()} or None
    if blocks:
        known = {c["block"] for c in contract["components"]}
        bad = blocks - known
        if bad:
            sys.exit(f"[중단] 알 수 없는 블록: {', '.join(sorted(bad))} (사용 가능: {', '.join(sorted(known))})")
    findings, refs, exp = compare(contract, nl, a.partial or bool(blocks), blocks, not a.no_fields)
    errors = report(findings, refs, exp, nl, a.csv)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
