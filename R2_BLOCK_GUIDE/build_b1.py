"""Build a review-only B1 guide. Does not alter schematic or design inputs."""
from pathlib import Path
import json, hashlib, html, csv, runpy
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
project = ROOT / "R2_REPAIRED_006"
model = json.loads((project / "source_contract.json").read_text(encoding="utf-8"))
components = {c["ref"]: c for c in model["components"]}
b1 = [c for c in model["components"] if c["block"] == "B1" and not c["ref"].startswith("#")]
netfile = ROOT / "R2_FIX_REPORTS_006/native/verified_netlist.xml"
nets = {x.get("ref")+"."+x.get("pin"): n.get("name") for n in ET.parse(netfile).findall("./nets/net") for x in n.findall("node")}
sch = (project / "B1.kicad_sch").read_text(encoding="utf-8")
bom = {c["RefDes"]: c for c in csv.DictReader((project / "BOM.csv").read_text(encoding="utf-8-sig").splitlines())}
for c in b1:
    assert bom[c["ref"]]["Value"] == c["Value"]
    assert bom[c["ref"]]["MPN"] == c["MPN"]
    assert f'(property "Reference" "{c["ref"]}"' in sch
    assert f'(property "Value" "{c["Value"]}"' in sch
    for p in c["pins"]:
        actual = nets[c["ref"]+"."+p["number"]].split("/")[-1]
        assert actual == p["net"] or (p["net"] == "NC" and actual.startswith("unconnected-"))

reasons = {
"1":"J100에서 들어오는 원시 입력을 받는다. 2번과 같은 입력 넷이다.",
"2":"1번과 함께 VIN_12V_RAW에 연결한다. PCB에서도 두 입력 패드를 모두 연결해야 한다.",
"3":"R100 아래, R101 위의 분압을 감시한다. 입력이 너무 낮을 때 후단 동작을 막는 설정점이다.",
"4":"실제 무연결이다. 다른 신호를 경유시키는 패드로 사용하지 않는다.",
"5":"R101 아래, R102 위의 분압을 감시한다. R100~R102가 UVLO와 OVP를 함께 설정한다.",
"6":"RTN에 직접 연결되어 전류 제한·자동 재시도 구성을 선택한다. 현재 회로에 모드 선택 저항은 없다.",
"7":"외부 구동 없이 열어 둔 구성이다. 내부 바이어스로 기본 활성화되므로 MCU가 이 핀으로 전원을 끄는 경로는 없다.",
"8":"R102·R103·C101 및 MODE의 공통 기준이다. 시스템 GND와 별도 넷으로 유지한다.",
"9":"J100의 음극과 입력/출력 커패시터의 귀환점인 시스템 GND에 연결한다.",
"10":"개별 채널 측정과 별개인 eFuse 전체 전류 모니터 출력이다. 현재 저항·ADC 연결이 없어 이 신호로 전체 전류를 읽지 않는다.",
"11":"R103 8.06kΩ의 반대편은 RTN이다. 전원 직렬 저항이 아니라 전류 제한 설정 저항이다.",
"12":"C101 100nF를 RTN에 연결한다. 출력 전압 상승 속도를 설정하며 출력에 저장되는 에너지용 커패시터가 아니다.",
"13":"4번과 함께 무연결 처리되어 있다.",
"14":"R104를 통해 CTRL_3V3로 풀업된다. TP1040과 MCU U1100.4(PC15)가 같은 PWR_FLT_N 넷에 있다.",
"15":"보호된 전원을 C102·C103 및 B2/B3로 전달한다.",
"16":"15번과 같은 VIN_12V_PROT이다. 두 출력 패드를 모두 연결해야 한다.",
"17":"프로젝트의 방열 패드 번호다. RTN으로 연결하며 8번도 별도로 연결한다. 시스템 GND 면에 합치지 않는다.",
}
pinrows = "".join(f'<tr><td>{html.escape(p["number"])}</td><td>{html.escape(p["name"])}</td><td><code>{html.escape(nets["U100."+p["number"]])}</code></td><td>{reasons[p["number"]]}</td></tr>' for p in components["U100"]["pins"])
partsrows = "".join(f'<tr><td><b>{c["ref"]}</b></td><td>{html.escape(c["Value"])}</td><td>{html.escape(c["Rating"])}</td><td>{html.escape(c["MPN"])}</td></tr>' for c in b1)
evidence = {
    "created_kst":"2026-10-20", "scope":"B1 explanation sample only; no circuit changes",
    "inputs":{str(f.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(f.read_bytes()).hexdigest() for f in [project/"B1.kicad_sch",project/"source_contract.json",project/"BOM.csv",netfile]},
    "b1_physical_components":len(b1),"u100_pins":17,
    "connection_check":"B1 contract pins matched stored native netlist; references and values found in actual B1 sheet; BOM Value/MPN matched contract",
    "native_erc_rerun":True,
    "calculations":{
        "uv_on_V":1.19*124990/14990,"uv_off_V":1.1*124990/14990,
        "ov_off_V":1.19*124990/10000,"ov_recover_V":1.1*124990/10000,
        "current_limit_A":12000/8060,"ramp_eq2_ms":8000*12*100e-9*1000,
        "ramp_eq1_ms":12/(4.7e-6*24.6/100e-9)*1000,
        "direct_output_cap_nominal_uF":87.3,"cap_only_inrush_eq2_mA":87.3e-6*12/.0096*1000
    },
    "sources":[
        {"url":"https://www.ti.com/lit/ds/symlink/tps2660.pdf","revision":"SLVSDG2G Rev G, December 2019","local":"tps2660.pdf"},
        {"url":"https://www.sameskydevices.com/product/resource/pj-102ah.pdf","revision":"2024-09-12","local":"pj-102ah.pdf"},
        {"url":"https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf","access":"Official indexed table consulted; direct PDF URL currently redirects to page-not-found. Full local copy not obtained."}
    ]
}
template = (OUT / "b1-template.html").read_text(encoding="utf-8")
runpy.run_path(str(OUT / "draw_b1.py"))
for key,value in {"__DIAGRAM__":(OUT/"B1_CONNECTED.svg").read_text(encoding="utf-8"),"__PINS__":pinrows,"__PARTS__":partsrows,"__HASH__":evidence["inputs"]["R2_REPAIRED_006/B1.kicad_sch"]}.items():
    template = template.replace(key,value)
(OUT / "B1_GUIDE.html").write_text(template,encoding="utf-8")
(OUT / "B1_EVIDENCE.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"B1 guide built: {len(b1)} components, 17 IC pins; native connectivity matched.")
