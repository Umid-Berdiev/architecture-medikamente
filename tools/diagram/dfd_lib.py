"""Minimal builder for Gane-Sarson data flow diagrams in draw.io XML.

Each Diagram holds one or more pages; each page holds external entities, processes,
data stores, data flows, trust boundaries and callout notes. The XML is written
uncompressed so it can be diffed and opened in draw.io or diagrams.net.
"""
import html
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---------------------------------------------------------------- styles
S_ENTITY = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#E6E6E6;strokeColor=#666666;"
            "fontStyle=1;fontSize=11;")
S_EXT_SYSTEM = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#666666;"
                "fontStyle=1;fontSize=11;dashed=1;")
S_PROCESS = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;"
             "arcSize=18;fontSize=11;")
S_STORE = ("shape=partialRectangle;whiteSpace=wrap;html=1;right=0;fillColor=#FFF2CC;"
           "strokeColor=#D6B656;align=left;spacingLeft=10;fontSize=11;")
S_STORE_SHADOW = ("shape=partialRectangle;whiteSpace=wrap;html=1;right=0;fillColor=#FFE6CC;"
                  "strokeColor=#D79B00;align=left;spacingLeft=10;fontSize=11;dashed=1;")
S_FLOW = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;"
          "strokeColor=#333333;strokeWidth=1.2;fontSize=10;labelBackgroundColor=#FFFFFF;"
          "jettySize=auto;orthogonalLoop=1;")
S_FLOW_MANUAL = S_FLOW + "dashed=1;dashPattern=4 3;strokeColor=#7F7F7F;"
S_RISK = ("shape=note;whiteSpace=wrap;html=1;fillColor=#F8CECC;strokeColor=#B85450;"
          "fontSize=9;align=left;spacingLeft=4;spacingTop=2;size=10;verticalAlign=top;")
S_CONTROL = ("shape=note;whiteSpace=wrap;html=1;fillColor=#D5E8D4;strokeColor=#82B366;"
             "fontSize=9;align=left;spacingLeft=4;spacingTop=2;size=10;verticalAlign=top;")
S_INFO = ("shape=note;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#999999;"
          "fontSize=9;align=left;spacingLeft=4;spacingTop=2;size=10;verticalAlign=top;")
S_BOUNDARY = ("rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 4;fillColor=none;"
              "strokeColor=#9673A6;strokeWidth=1.5;verticalAlign=top;align=left;fontStyle=2;"
              "fontColor=#9673A6;spacingLeft=8;spacingTop=2;fontSize=11;")
S_TITLE = "text;html=1;align=left;verticalAlign=top;fontSize=16;fontStyle=1;strokeColor=none;fillColor=none;"
S_TEXT = "text;html=1;align=left;verticalAlign=top;fontSize=10;strokeColor=none;fillColor=none;whiteSpace=wrap;"
S_LINK = ("edgeStyle=none;html=1;endArrow=none;dashed=1;dashPattern=1 2;strokeColor=#999999;"
          "strokeWidth=1;")


def esc(text):
    return html.escape(text, quote=False)


def wrap(text, width=26):
    """Break a label into lines of roughly `width` characters at word boundaries."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return "<br>".join(esc(l) for l in lines)


class Page:
    def __init__(self, name):
        self.name = name
        self.cells = []  # (id, dict attrs, geometry dict, parent)
        self.n = 0
        self.ids = {}

    def _id(self, key=None):
        self.n += 1
        cid = f"{self.name}-{self.n}"
        if key:
            self.ids[key] = cid
        return cid

    def vertex(self, key, value, style, x, y, w, h):
        cid = self._id(key)
        self.cells.append(("v", cid, value, style, {"x": x, "y": y, "width": w, "height": h}, None))
        return cid

    def edge(self, src, dst, value, style, points=None, exit_=None, entry=None, key=None, lab=None):
        st = style
        if exit_:
            st += f"exitX={exit_[0]};exitY={exit_[1]};exitDx=0;exitDy=0;"
        if entry:
            st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        cid = self._id(key)
        self.cells.append(("e", cid, value, st, {"points": points or [], "lab": lab},
                           (self.ids[src], self.ids[dst])))
        return cid

    # ---- Gane-Sarson elements -------------------------------------------------
    def title(self, text, x=20, y=10, w=900, h=30):
        return self.vertex(None, f"<b>{esc(text)}</b>", S_TITLE, x, y, w, h)

    def text(self, text, x, y, w, h):
        return self.vertex(None, text, S_TEXT, x, y, w, h)

    def entity(self, key, name, x, y, w=140, h=60, sub=None, system=False):
        label = esc(name)
        if sub:
            label += f'<br><font style="font-size:9px;font-weight:normal;color:#555">{esc(sub)}</font>'
        return self.vertex(key, label, S_EXT_SYSTEM if system else S_ENTITY, x, y, w, h)

    def process(self, key, num, name, x, y, w=170, h=80, who=None):
        label = f'<b>{esc(num)}</b><br>{esc(name)}'
        if who:
            label += f'<br><font style="font-size:9px;color:#555">{esc(who)}</font>'
        return self.vertex(key, label, S_PROCESS, x, y, w, h)

    def store(self, key, num, name, x, y, w=200, h=50, sub=None, shadow=False):
        label = f'<b>{esc(num)}</b>&nbsp;&nbsp;{esc(name)}'
        if sub:
            label += f'<br><font style="font-size:9px;color:#555">{esc(sub)}</font>'
        return self.vertex(key, label, S_STORE_SHADOW if shadow else S_STORE, x, y, w, h)

    def flow(self, src, dst, label, manual=False, points=None, exit_=None, entry=None, lab=None, width=26):
        return self.edge(src, dst, wrap(label, width), S_FLOW_MANUAL if manual else S_FLOW,
                         points, exit_, entry, lab=lab)

    def boundary(self, name, x, y, w, h, bottom=False):
        cid = self._id(None)
        style = S_BOUNDARY + ("verticalAlign=bottom;" if bottom else "")
        # boundaries go to the front of the list so they render behind everything
        self.cells.insert(0, ("v", cid, esc(name), style, {"x": x, "y": y, "width": w, "height": h}, None))
        return cid

    def note(self, code, text, x, y, w=190, h=56, kind="risk", attach=None):
        style = {"risk": S_RISK, "control": S_CONTROL, "info": S_INFO}[kind]
        label = f"<b>{esc(code)}</b> {esc(text)}" if code else esc(text)
        key = f"note-{code or self.n}"
        cid = self.vertex(key, label, style, x, y, w, h)
        if attach:
            self.edge(key, attach, "", S_LINK)
        return cid

    def legend(self, x, y):
        self.text(("<b>Нотация (Gane-Sarson)</b><br>"
                   "Серый прямоугольник — внешняя сущность (человек/организация), пунктирный — внешняя система.<br>"
                   "Скруглённый голубой блок — процесс (номер, название, исполнитель).<br>"
                   "Жёлтый открытый блок — хранилище данных (D-номер); оранжевый пунктирный — "
                   "неучтённое («теневое») хранилище.<br>"
                   "Стрелка — поток данных; пунктирная — ручной/бумажный/голосовой канал.<br>"
                   "Красная заметка R-xx — проблемная зона (см. 02-security-audit.md); "
                   "зелёная C-xx — мера защиты (см. 05-controls.md)."), x, y, 620, 90)

    # ---- serialisation ------------------------------------------------------
    def to_element(self):
        diagram = ET.Element("diagram", name=self.name, id=self.name)
        model = ET.SubElement(diagram, "mxGraphModel", dx="1400", dy="900", grid="1", gridSize="10",
                              guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                              pageScale="1", pageWidth="1654", pageHeight="1169", math="0", shadow="0")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        for kind, cid, value, style, geo, ends in self.cells:
            if kind == "v":
                c = ET.SubElement(root, "mxCell", id=cid, value=value, style=style, vertex="1", parent="1")
                ET.SubElement(c, "mxGeometry", x=str(geo["x"]), y=str(geo["y"]), width=str(geo["width"]),
                              height=str(geo["height"]), **{"as": "geometry"})
            else:
                c = ET.SubElement(root, "mxCell", id=cid, value=value, style=style, edge="1", parent="1",
                                  source=ends[0], target=ends[1])
                g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
                if geo.get("lab"):
                    g.set("x", str(geo["lab"][0]))
                    g.set("y", str(geo["lab"][1]))
                if geo["points"]:
                    arr = ET.SubElement(g, "Array", **{"as": "points"})
                    for px, py in geo["points"]:
                        ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
        return diagram

    def bbox(self):
        xs, ys = [], []
        for kind, _, _, _, geo, _ in self.cells:
            if kind == "v":
                xs += [geo["x"], geo["x"] + geo["width"]]
                ys += [geo["y"], geo["y"] + geo["height"]]
            else:
                for px, py in geo["points"]:
                    xs.append(px)
                    ys.append(py)
        return min(xs), min(ys), max(xs), max(ys)


class Diagram:
    def __init__(self):
        self.pages = []

    def page(self, name):
        p = Page(name)
        self.pages.append(p)
        return p

    def write(self, path):
        mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device", pages=str(len(self.pages)))
        for p in self.pages:
            mxfile.append(p.to_element())
        raw = ET.tostring(mxfile, encoding="unicode")
        pretty = minidom.parseString(raw).toprettyxml(indent=" ", encoding="utf-8")
        with open(path, "wb") as f:
            f.write(pretty)


S_OFFPAGE = ("shape=offPageConnector;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#666666;"
             "fontSize=10;fontStyle=2;size=0.3;")


def offpage(self, key, text, x, y, w=150, h=60):
    """Off-page connector: reference to another process diagram."""
    return self.vertex(key, esc(text), S_OFFPAGE, x, y, w, h)


Page.offpage = offpage
