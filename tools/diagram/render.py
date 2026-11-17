"""Render every page of a .drawio file to PNG with headless Google Chrome.

There is no draw.io CLI on this machine, so each page is embedded into a small HTML
document that loads the diagrams.net viewer script, and Chrome takes a screenshot of it.

    python3 tools/diagram/render.py Task1/dfd/01-registration.drawio

Output: <file>-<n>-<page-name>.png next to the source file.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VIEWER = "https://viewer.diagrams.net/js/viewer-static.min.js"
SCALE = 2
MARGIN = 30


def page_bbox(diagram):
    xs, ys = [], []
    for g in diagram.iter("mxGeometry"):
        if g.get("x") is not None and g.get("width") is not None:
            x, y, w, h = (float(g.get(k)) for k in ("x", "y", "width", "height"))
            xs += [x, x + w]
            ys += [y, y + h]
        for p in g.iter("mxPoint"):
            if p.get("x") is not None:
                xs.append(float(p.get("x")))
                ys.append(float(p.get("y")))
    return min(xs), min(ys), max(xs), max(ys)


def render(path):
    tree = ET.parse(path)
    mxfile = tree.getroot()
    base = os.path.splitext(path)[0]
    for idx, diagram in enumerate(mxfile.findall("diagram")):
        single = ET.Element("mxfile")
        single.append(diagram)
        xml = ET.tostring(single, encoding="unicode")
        x0, y0, x1, y1 = page_bbox(diagram)
        w = int(x1 - x0 + 2 * MARGIN)
        h = int(y1 - y0 + 2 * MARGIN)
        cfg = {"xml": xml, "page": 0, "nav": False, "toolbar": None, "lightbox": False,
               "resize": False, "border": MARGIN, "highlight": "none", "zoom": 1}
        cfg_js = json.dumps(cfg).replace("</", "<\\/")
        html = ("<!doctype html><html><head><meta charset='utf-8'>"
                "<style>html,body{margin:0;padding:0;background:#fff;overflow:hidden}"
                f".mxgraph{{width:{w}px;height:{h}px}}</style></head><body>"
                "<div class='mxgraph'></div>"
                f"<script>document.querySelector('.mxgraph').setAttribute('data-mxgraph', JSON.stringify({cfg_js}));</script>"
                f"<script src='{VIEWER}'></script></body></html>")
        name = re.sub(r"[^\w\-]+", "_", diagram.get("name"))
        out = f"{base}-{idx + 1}-{name}.png"
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html)
            tmp = f.name
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               f"--window-size={w},{h}", f"--force-device-scale-factor={SCALE}",
               "--virtual-time-budget=8000", f"--screenshot={out}", f"file://{tmp}"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.unlink(tmp)
        print(out, f"{w}x{h}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        render(p)
