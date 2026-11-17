"""C4 model shapes for draw.io, matching the notation of the course's as-is landscape diagram.

Elements are written as <object> cells with c4* attributes and placeholder labels, exactly like the
draw.io C4 shape library does, so the files stay editable in draw.io (Edit Data on any element).
"""
import html
import xml.etree.ElementTree as ET
from xml.dom import minidom

LABEL_NODE = ('<font style="font-size: 16px"><b>%c4Name%</b></font><div>[%c4Type%]</div><br>'
              '<div><font style="font-size: 11px"><font color="#cccccc">%c4Description%</font></div>')
LABEL_CONTAINER = ('<font style="font-size: 15px"><b>%c4Name%</b></font><div>[%c4Type%: %c4Technology%]</div><br>'
                   '<div><font style="font-size: 11px"><font color="#E6E6E6">%c4Description%</font></div>')
LABEL_BOUNDARY = ('<font style="font-size: 16px"><b><div style="text-align: left">%c4Name%</div></b></font>'
                  '<div style="text-align: left">[%c4Application%]</div>')
LABEL_REL = ('<div style="text-align: left"><div style="text-align: center"><b>%c4Description%</b></div>'
             '<div style="text-align: center">[%c4Technology%]</div></div>')
LABEL_REL_NOTECH = '<div style="text-align: left"><div style="text-align: center"><b>%c4Description%</b></div></div>'

S_PERSON = ("html=1;fontSize=11;dashed=0;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};fontColor=#ffffff;"
            "shape=mxgraph.c4.person2;align=center;metaEdit=1;"
            "points=[[0.5,0,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0]];resizable=0;")
S_BOX = ("rounded=1;whiteSpace=wrap;html=1;labelBackgroundColor=none;fillColor={fill};fontColor=#ffffff;align=center;"
         "arcSize=10;strokeColor={stroke};metaEdit=1;resizable=0;{extra}"
         "points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],"
         "[0,0.75,0],[0,0.5,0],[0,0.25,0]];")
S_DB = ("shape=cylinder3;size=15;whiteSpace=wrap;html=1;boundedLbl=1;rounded=0;labelBackgroundColor=none;"
        "fillColor={fill};fontSize=12;fontColor=#ffffff;align=center;strokeColor={stroke};metaEdit=1;{extra}")
S_BOUNDARY = ("rounded=1;fontSize=11;whiteSpace=wrap;html=1;dashed=1;arcSize=20;fillColor=none;strokeColor={stroke};"
              "fontColor=#333333;labelBackgroundColor=none;align=left;verticalAlign=bottom;labelBorderColor=none;"
              "spacingTop=0;spacing=10;dashPattern=8 4;metaEdit=1;rotatable=0;")
S_REL = ("endArrow=blockThin;html=1;fontSize=10;fontColor=#404040;strokeWidth=1;endFill=1;strokeColor=#828282;"
         "elbow=vertical;metaEdit=1;endSize=14;startSize=14;jumpStyle=arc;jumpSize=16;rounded=0;"
         "edgeStyle=orthogonalEdgeStyle;")
S_BADGE = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FFD966;strokeColor=#B38F00;fontColor=#333333;fontSize=9;"
           "fontStyle=1;arcSize=30;")
S_TEXT = "text;html=1;align=left;verticalAlign=top;fontSize=11;strokeColor=none;fillColor=none;whiteSpace=wrap;"
S_TITLE = "text;html=1;align=left;verticalAlign=top;fontSize=18;fontStyle=1;strokeColor=none;fillColor=none;"

# Colour palette: who is what on the diagram (explained in the legend).
COLORS = {
    "person": ("#083F75", "#06315C"),
    "person_ext": ("#6C6477", "#4D4D4D"),
    "system": ("#1061B0", "#0D5091"),
    "system_ext": ("#8C8496", "#736782"),
    "container": ("#23A2D9", "#0E7DAD"),        # domain / functional containers
    "privacy": ("#2E8B57", "#1F6B40"),          # new Privacy by Design blocks
    "analytics": ("#7B5EA7", "#5B4480"),        # analytics layer
    "legacy": ("#8C8496", "#736782"),           # existing systems kept in the landscape
    "channel": ("#438DD5", "#3C7FC0"),          # UI channels
}


def esc(t):
    return html.escape(t, quote=False)


class C4Page:
    def __init__(self, name):
        self.name = name
        self.cells = []
        self.n = 0
        self.ids = {}

    def _id(self, key):
        self.n += 1
        cid = f"{self.name}-{self.n}"
        if key:
            self.ids[key] = cid
        return cid

    # ---- raw cell ------------------------------------------------------------
    def _obj(self, key, attrs, style, geo, front=False, edge=None):
        cid = self._id(key)
        rec = ("o", cid, attrs, style, geo, edge)
        if front:
            self.cells.insert(0, rec)
        else:
            self.cells.append(rec)
        return cid

    def _plain(self, value, style, x, y, w, h):
        cid = self._id(None)
        self.cells.append(("v", cid, value, style, {"x": x, "y": y, "width": w, "height": h}, None))
        return cid

    # ---- C4 elements ------------------------------------------------------------
    def person(self, key, name, desc, x, y, external=False, w=200, h=180):
        fill, stroke = COLORS["person_ext" if external else "person"]
        return self._obj(key, {"placeholders": "1", "c4Name": name, "c4Type": "Person", "c4Description": desc,
                               "label": LABEL_NODE}, S_PERSON.format(fill=fill, stroke=stroke),
                         {"x": x, "y": y, "width": w, "height": h})

    def system(self, key, name, desc, x, y, external=False, w=240, h=120, kind=None, badge=None):
        fill, stroke = COLORS[kind or ("system_ext" if external else "system")]
        cid = self._obj(key, {"placeholders": "1", "c4Name": name, "c4Type": "Software System",
                              "c4Description": desc, "label": LABEL_NODE},
                        S_BOX.format(fill=fill, stroke=stroke, extra=""), {"x": x, "y": y, "width": w, "height": h})
        if badge:
            self.badge(badge, x + w - 46, y - 9)
        return cid

    def container(self, key, name, tech, desc, x, y, w=220, h=110, kind="container", db=False, badge=None):
        fill, stroke = COLORS[kind]
        style = (S_DB if db else S_BOX).format(fill=fill, stroke=stroke, extra="")
        if db:
            h = max(h, 120)
        cid = self._obj(key, {"placeholders": "1", "c4Name": name, "c4Type": "Container", "c4Technology": tech,
                              "c4Description": desc, "label": LABEL_CONTAINER}, style,
                        {"x": x, "y": y, "width": w, "height": h})
        if badge:
            self.badge(badge, x + w - 46, y - 9)
        return cid

    def boundary(self, key, name, kind, x, y, w, h, stroke="#666666"):
        return self._obj(key, {"placeholders": "1", "c4Name": name, "c4Type": "SystemScopeBoundary",
                               "c4Application": kind, "label": LABEL_BOUNDARY},
                         S_BOUNDARY.format(stroke=stroke), {"x": x, "y": y, "width": w, "height": h}, front=True)

    def rel(self, src, dst, desc, tech="", exit_=None, entry=None, points=None, dashed=False, lab=None, key=None,
            color=None):
        style = S_REL
        if exit_:
            style += f"exitX={exit_[0]};exitY={exit_[1]};exitDx=0;exitDy=0;"
        if entry:
            style += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        if dashed:
            style += "dashed=1;dashPattern=6 4;"
        if color:
            style += f"strokeColor={color};fontColor={color};"
        attrs = {"placeholders": "1", "c4Type": "Relationship", "c4Description": desc,
                 "label": LABEL_REL if tech else LABEL_REL_NOTECH}
        if tech:
            attrs["c4Technology"] = tech
        return self._obj(key, attrs, style, {"points": points or [], "lab": lab}, edge=(self.ids[src], self.ids[dst]))

    def badge(self, text, x, y):
        return self._plain(esc(text), S_BADGE, x, y, 44, 18)

    def text(self, value, x, y, w, h):
        return self._plain(value, S_TEXT, x, y, w, h)

    def title(self, value, x=20, y=10, w=1200, h=30):
        return self._plain(f"<b>{esc(value)}</b>", S_TITLE, x, y, w, h)

    # ---- serialisation ------------------------------------------------------------
    def to_element(self):
        diagram = ET.Element("diagram", name=self.name, id=self.name)
        model = ET.SubElement(diagram, "mxGraphModel", dx="1400", dy="900", grid="1", gridSize="10", guides="1",
                              tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                              pageWidth="1654", pageHeight="1169", math="0", shadow="0")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        for kind, cid, a, style, geo, edge in self.cells:
            if kind == "v":
                c = ET.SubElement(root, "mxCell", id=cid, value=a, style=style, vertex="1", parent="1")
                ET.SubElement(c, "mxGeometry", x=str(geo["x"]), y=str(geo["y"]), width=str(geo["width"]),
                              height=str(geo["height"]), **{"as": "geometry"})
                continue
            obj = ET.SubElement(root, "object", id=cid, **a)
            if edge:
                c = ET.SubElement(obj, "mxCell", style=style, edge="1", parent="1", source=edge[0], target=edge[1])
                g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
                if geo.get("lab"):
                    g.set("x", str(geo["lab"][0]))
                    g.set("y", str(geo["lab"][1]))
                if geo["points"]:
                    arr = ET.SubElement(g, "Array", **{"as": "points"})
                    for px, py in geo["points"]:
                        ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
            else:
                c = ET.SubElement(obj, "mxCell", style=style, vertex="1", parent="1")
                ET.SubElement(c, "mxGeometry", x=str(geo["x"]), y=str(geo["y"]), width=str(geo["width"]),
                              height=str(geo["height"]), **{"as": "geometry"})
        return diagram


class C4Diagram:
    def __init__(self):
        self.pages = []

    def page(self, name):
        p = C4Page(name)
        self.pages.append(p)
        return p

    def write(self, path):
        mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device", pages=str(len(self.pages)))
        for p in self.pages:
            mxfile.append(p.to_element())
        raw = ET.tostring(mxfile, encoding="unicode")
        with open(path, "wb") as f:
            f.write(minidom.parseString(raw).toprettyxml(indent=" ", encoding="utf-8"))
