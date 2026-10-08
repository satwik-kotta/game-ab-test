"""Inject outputs/results.json into the dashboard template -> dashboard/index.html"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
data = (ROOT / "outputs" / "results.json").read_text()
html = (ROOT / "dashboard" / "template.html").read_text().replace("__DATA__", data)
(ROOT / "dashboard" / "index.html").write_text(html)
print("wrote dashboard/index.html")
