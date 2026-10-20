"""Copy the standalone guide to the existing GitHub Pages main/docs source."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "ALL_BLOCKS_GUIDE.html").read_text(encoding="utf-8")
base = "https://github.com/Gugong0412/currentboard/blob/main/"
source = source.replace('href=\\"../', 'href=\\"' + base)
for name in ("ALL_BLOCKS_EVIDENCE.json", "B1_EVIDENCE.json", "tps2660.pdf", "pj-102ah.pdf"):
    source = source.replace('href=\\"' + name, 'href=\\"' + base + "R2_BLOCK_GUIDE/" + name)
(root.parent / "docs" / "index.html").write_text(source, encoding="utf-8")
print("Updated docs/index.html: b1-style-v3")
