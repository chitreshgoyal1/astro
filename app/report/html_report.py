"""
HTML report (V1.7 Parts 20, 22, 24, 36)
=========================================
The same ReportDocument, rendered as a single self-contained page.

WHY THIS EXISTS AND WHAT IT IS FOR

    Two things the PDF writer cannot do, and one it should not have to.

    1. DEVANAGARI. The PDF's Latin base-14 faces have no Devanagari
       glyphs, and rendering Hindi properly needs an embedded font AND a
       shaper — Devanagari reorders matras and forms conjuncts, so correct
       code points in encoding order still come out visibly wrong. A
       browser already has both. The Hindi report is an HTML report, and
       it is complete rather than a placeholder.

    2. SELECTABLE, SEARCHABLE, REFLOWING TEXT at whatever size the reader
       wants, which Part 36 asks for and a fixed A4 page cannot give.

    3. It costs almost nothing: the document is already structured, so
       this is a second backend over the same blocks, not a second report.

SELF-CONTAINED, AND OFFLINE

    One file. The stylesheet is inlined, the charts are inline SVG, and
    there is no script, no font request and no image reference. It opens
    from a USB stick on a machine that has never been online, which is
    what Part 34 asks of the whole pipeline.

DETERMINISM

    Same blocks in, same bytes out. No timestamp is written into the markup
    beyond the one the document itself carries, so Part 39's end-to-end
    comparison works on this output as it does on the PDF.
"""

from __future__ import annotations

import html as _html
from typing import Optional

from ..visual.svg import scene_to_svg
from .pdf import IAST_TO_ASCII   # noqa: F401  (documented contrast, see below)

#: The print stylesheet. Deliberately close to the PDF's typography so the
#: two renderings of a report look like the same document — same serif for
#: reading, same sans for structure, same restrained palette.
#:
#: Note what is NOT here: `IAST_TO_ASCII` is imported above only to make
#: the contrast explicit and is never applied. HTML is UTF-8, so the
#: Sanskrit citations keep their diacritics here and lose them only in the
#: PDF, where the encoding cannot carry them.
STYLESHEET = """
:root {
  --ink:#1d1f23; --muted:#5b6068; --rule:#d8dade; --panel:#f6f6f4;
  --warn:#8a4b06; --warn-bg:#fdf6ec; --limit:#2f3338;
}
* { box-sizing:border-box; }
body {
  margin:0 auto; padding:2.6rem 1.6rem 5rem; max-width:52rem;
  font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,
              'Noto Serif','Noto Serif Devanagari',serif;
  font-size:1rem; line-height:1.6; color:var(--ink); background:#fff;
}
h1 { font-size:2rem; margin:0 0 .3rem; }
h2 {
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',
              'Noto Sans Devanagari',sans-serif;
  font-size:1.4rem; margin:2.4rem 0 .6rem; padding-bottom:.3rem;
  border-bottom:1px solid var(--rule);
}
h3 {
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',
              'Noto Sans Devanagari',sans-serif;
  font-size:1.05rem; margin:1.6rem 0 .4rem;
}
h4 { font-size:.85rem; text-transform:uppercase; letter-spacing:.04em;
     color:var(--muted); margin:1.2rem 0 .3rem; }
p { margin:0 0 .8rem; }
p.lead { font-size:1.1rem; }
p.small, p.note, .note { color:var(--muted); font-size:.87rem; }
table { border-collapse:collapse; width:100%; margin:.5rem 0 1.4rem;
        font-size:.87rem;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',
                    'Noto Sans Devanagari',sans-serif; }
caption { text-align:left; color:var(--muted); font-size:.82rem;
          padding-bottom:.3rem; }
th,td { border-bottom:1px solid var(--rule); padding:.35rem .5rem;
        text-align:left; vertical-align:top; }
th { background:var(--panel); font-weight:600; font-size:.8rem; }
td.right,th.right { text-align:right; }
td.centre,th.centre { text-align:center; }
dl { display:grid; grid-template-columns:max-content 1fr; gap:.15rem 1.2rem;
     margin:0 0 1.2rem; font-size:.93rem; }
dt { color:var(--muted);
     font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',
                 'Noto Sans Devanagari',sans-serif; font-size:.82rem; }
dd { margin:0; }
aside { border-left:3px solid var(--muted); background:var(--panel);
        padding:.7rem .9rem; margin:1rem 0; font-size:.93rem; }
aside.warning { border-left-color:var(--warn); background:var(--warn-bg); }
aside.limit { border-left-color:var(--limit); }
aside p:last-child { margin-bottom:0; }
figure { margin:1.2rem 0; text-align:center; }
figure svg { width:100%; max-width:22rem; height:auto; }
figcaption { color:var(--muted); font-size:.85rem; padding-top:.4rem; }
ul { margin:.2rem 0 1rem; padding-left:1.3rem; }
li { margin-bottom:.25rem; }
footer { border-top:1px solid var(--rule); margin-top:3rem; padding-top:1rem;
         color:var(--muted); font-size:.82rem; }
@media print {
  body { max-width:none; padding:0; font-size:10.5pt; }
  h2 { page-break-after:avoid; }
  table,figure,aside { page-break-inside:avoid; }
}
"""

_ALIGN = {"right": "right", "centre": "centre"}


def _e(value) -> str:
    return _html.escape("" if value is None else str(value), quote=True)


def _table(block: dict) -> str:
    align = block.get("align") or []

    def cls(index: int) -> str:
        name = _ALIGN.get(align[index] if index < len(align) else "", "")
        return f' class="{name}"' if name else ""

    head = "".join(f'<th scope="col"{cls(i)}>{_e(c)}</th>'
                   for i, c in enumerate(block.get("columns", [])))
    body = "".join(
        "<tr>" + "".join(f"<td{cls(i)}>{_e(c)}</td>"
                         for i, c in enumerate(row)) + "</tr>"
        for row in block.get("rows", []))
    caption = (f"<caption>{_e(block['caption'])}</caption>"
               if block.get("caption") else "")
    return (f"<table>{caption}<thead><tr>{head}</tr></thead>"
            f"<tbody>{body}</tbody></table>")


def _block(block: dict, index: int) -> str:
    kind = block.get("block")
    if kind == "paragraph":
        style = block.get("style", "body")
        cls = f' class="{style}"' if style != "body" else ""
        return f"<p{cls}>{_e(block.get('text'))}</p>"
    if kind == "heading":
        level = min(4, max(2, block.get("level", 2) + 1))
        return f"<h{level}>{_e(block.get('text'))}</h{level}>"
    if kind == "table":
        return _table(block)
    if kind == "keyvalues":
        rows = "".join(f"<dt>{_e(k)}</dt><dd>{_e(v)}</dd>"
                       for k, v in block.get("pairs", []))
        caption = (f"<h4>{_e(block['caption'])}</h4>"
                   if block.get("caption") else "")
        notes = "".join(f'<p class="note">{_e(n)}</p>'
                        for n in block.get("notes", []))
        return f"{caption}<dl>{rows}</dl>{notes}"
    if kind == "callout":
        title = (f"<strong>{_e(block['title'])}</strong>"
                 if block.get("title") else "")
        return (f'<aside class="{_e(block.get("kind", "note"))}">{title}'
                f"<p>{_e(block.get('text'))}</p></aside>")
    if kind == "bullets":
        caption = (f"<h4>{_e(block['caption'])}</h4>"
                   if block.get("caption") else "")
        items = "".join(f"<li>{_e(i)}</li>" for i in block.get("items", []))
        return f"{caption}<ul>{items}</ul>"
    if kind == "chart":
        scene = block.get("scene")
        if not scene:
            return ""
        return (f"<figure>{_scene_svg(scene, index)}"
                f"<figcaption>{_e(block.get('caption'))}</figcaption>"
                f"</figure>")
    if kind == "pagebreak":
        return '<div style="page-break-after:always"></div>'
    raise ValueError(f"no HTML renderer for block type '{kind}'")


def _scene_svg(scene: dict, index: int) -> str:
    """
    A serialised scene back into SVG.

    The report holds scenes as dictionaries, because a ReportDocument must
    survive being written to JSON and read back. `scene_to_svg` wants the
    object, so the dict is wrapped in the smallest thing that satisfies it
    — which also proves the round trip the golden tests rely on.
    """
    from ..visual.scene import Line, Polygon, Rect, Scene, Text

    builders = {"line": Line, "polygon": Polygon, "rect": Rect, "text": Text}
    rebuilt = Scene(width=scene.get("width", 0), height=scene.get("height", 0),
                    title=scene.get("title", ""),
                    description=scene.get("description", ""))
    for element in scene.get("elements", []):
        data = dict(element)
        builder = builders.get(data.pop("kind", ""))
        if builder is None:
            continue
        if builder is Polygon:
            data["points"] = tuple(tuple(p) for p in data.get("points", ()))
        rebuilt.add(builder(**data))
    return scene_to_svg(rebuilt, element_id=f"kundli-{index}")


def render_html(document: dict, language: Optional[str] = None) -> str:
    """One self-contained HTML file for a serialised ReportDocument."""
    language = language or document.get("language") or "en"
    parts: list[str] = []
    counter = 0
    for section in document.get("sections", []):
        if section.get("id") != "cover" and section.get("title"):
            parts.append(f"<h2>{_e(section['title'])}</h2>")
        if section.get("subtitle"):
            parts.append(f'<p class="note">{_e(section["subtitle"])}</p>')
        for block in section.get("blocks", []):
            counter += 1
            parts.append(_block(block, counter))

    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{_e(language)}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_e(document.get('title'))}</title>"
        f"<style>{STYLESHEET}</style></head><body>"
        + "".join(parts)
        + "<footer><p>Generated by deterministic calculation and template "
          "substitution. No language model, no network, no prediction of "
          "events. Nothing in this build is tradition-validated.</p>"
          f"<p>{_e(document.get('generated'))}</p></footer>"
        "</body></html>\n")


def write_html(document: dict, path: str, language: Optional[str] = None
               ) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(render_html(document, language))
    return path
