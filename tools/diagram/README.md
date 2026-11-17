# Diagram tooling

`dfd_lib.py` is a small builder for Gane-Sarson data flow diagrams in draw.io XML (uncompressed, so
the files diff cleanly and open in draw.io desktop or app.diagrams.net).

`gen_dfd.py` holds the content of the Task 1 diagrams: one file per process, two pages per file
(`as-is` with R-xx risk markers, `to-be` with C-xx control markers and target stores).

```bash
python3 tools/diagram/gen_dfd.py Task1/dfd
```

`render.py` renders every page of a `.drawio` file to PNG. There is no draw.io CLI on this machine,
so each page is embedded in a small HTML document that loads the diagrams.net viewer script and
headless Google Chrome takes a screenshot (device scale factor 2).

```bash
python3 tools/diagram/render.py Task1/dfd/*.drawio
```

Requirements: Python 3.9+, Google Chrome at `/Applications/Google Chrome.app`, network access to
`viewer.diagrams.net` for the viewer script.
