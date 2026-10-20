"""Archive manufacturer PDFs for the explanatory guide, without editing design files."""
from pathlib import Path
import urllib.request, json, hashlib, concurrent.futures
import pypdf
ROOT=Path(__file__).parent
DEST=ROOT/"sources";DEST.mkdir(exist_ok=True)
URLS={
"tps62130a":"https://www.ti.com/lit/ds/symlink/tps62130a.pdf",
"tps7a90":"https://www.ti.com/lit/ds/symlink/tps7a90.pdf",
"ina228":"https://www.ti.com/lit/ds/symlink/ina228.pdf",
"iso1641":"https://www.ti.com/lit/ds/symlink/iso1641.pdf",
"tps7a16":"https://www.ti.com/lit/ds/symlink/tps7a16.pdf",
"sn74axc2t45":"https://www.ti.com/lit/ds/symlink/sn74axc2t45.pdf",
"adum4160":"https://www.analog.com/media/en/technical-documentation/data-sheets/ADuM4160.pdf",
"stm32f072":"https://www.st.com/resource/en/datasheet/stm32f072cb.pdf",
"rfm":"https://recom-power.com/pdf/Econoline/RFM.pdf",
"xfl4020":"https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf",
"tpd2eusb30":"https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf",
"tpd1e10b06":"https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf",
"tsw":"https://suddendocs.samtec.com/catalog_english/tsw_th.pdf",
"usb4105":"https://gct.co/files/specs/usb4105-spec.pdf",
}
def fetch(pair):
 k,u=pair; f=DEST/(k+".pdf")
 try:
  if not f.exists():
   b=urllib.request.urlopen(u,timeout=35).read()
   if not b.startswith(b"%PDF"):raise ValueError("Not PDF")
   f.write_bytes(b)
  reader=pypdf.PdfReader(f)
  pages=[p.extract_text() for p in reader.pages]
  if k=="stm32f072" and "STM32F072" not in pages[0]:raise ValueError("Wrong STM32 family returned")
  (DEST/(k+".txt")).write_text("\n".join(f"\n--- PAGE {i+1} ---\n{t}" for i,t in enumerate(pages)),encoding="utf-8")
  return k,{"url":u,"file":f.name,"pages":len(pages),"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"status":"downloaded","first_page":pages[0][:250]}
 except Exception as e:return k,{"url":u,"status":"unavailable","error":str(e)}
if __name__=="__main__":
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results=dict(pool.map(fetch,URLS.items()))
 (DEST/"manifest.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
 for k,v in results.items():print(k,v["status"],v.get("pages",v.get("error")))
