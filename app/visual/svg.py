"""
SVG backend (V1.7 Parts 7, 36)
================================
Scene to SVG text. No dependency, no file handling, no astrology.

DETERMINISM

    Attributes are written in a fixed order, numbers are already rounded by
    the scene, and nothing here consults the clock or the environment. The
    same scene always produces byte-identical SVG, which is what lets the
    visual regression tests hash the output instead of eyeballing it.

ACCESSIBILITY (Part 36)

    Every chart carries `<title>` and `<desc>` built from the scene's own
    description, and the root element is marked `role="img"` with
    `aria-labelledby`. A screen reader gets the twelve houses and their
    contents as a sentence; it does not get a shape it cannot interpret.
"""

from __future__ import annotations

import html

from .scene import Line, Polygon, Rect, Scene, Text

#: The font stack. A system stack rather than a web font: the application
#: runs offline and a font that has to be fetched is a chart that does not
#: draw. The PDF backend maps these onto its own embedded faces.
FONT_STACK = ("'Iowan Old Style','Palatino Linotype',Palatino,Georgia,"
              "'Noto Serif',serif")

_ANCHOR = {"start": "start", "middle": "middle", "end": "end"}
_BASELINE = {"baseline": "alphabetic", "middle": "central",
             "hanging": "hanging"}


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _fmt(value: float) -> str:
    """Trim a trailing '.0' so the output reads like a drawing, not a dump."""
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text or "0"


def _line(element: Line) -> str:
    return (f'<line x1="{_fmt(element.x1)}" y1="{_fmt(element.y1)}" '
            f'x2="{_fmt(element.x2)}" y2="{_fmt(element.y2)}" '
            f'stroke="{_esc(element.colour)}" '
            f'stroke-width="{_fmt(element.width)}" />')


def _polygon(element: Polygon) -> str:
    points = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in element.points)
    fill = element.fill or "none"
    stroke = element.stroke or "none"
    return (f'<polygon points="{points}" fill="{_esc(fill)}" '
            f'stroke="{_esc(stroke)}" stroke-width="{_fmt(element.width)}" />')


def _rect(element: Rect) -> str:
    fill = element.fill or "none"
    stroke = element.stroke or "none"
    radius = (f' rx="{_fmt(element.radius)}"' if element.radius else "")
    return (f'<rect x="{_fmt(element.x)}" y="{_fmt(element.y)}" '
            f'width="{_fmt(element.width)}" height="{_fmt(element.height)}"'
            f'{radius} fill="{_esc(fill)}" stroke="{_esc(stroke)}" '
            f'stroke-width="{_fmt(element.stroke_width)}" />')


def _text(element: Text) -> str:
    style = ' font-style="italic"' if element.italic else ""
    weight = (f' font-weight="{_esc(element.weight)}"'
              if element.weight != "normal" else "")
    role = f' data-role="{_esc(element.role)}"' if element.role else ""
    return (f'<text x="{_fmt(element.x)}" y="{_fmt(element.y)}" '
            f'font-size="{_fmt(element.size)}" '
            f'text-anchor="{_ANCHOR.get(element.anchor, "middle")}" '
            f'dominant-baseline="{_BASELINE.get(element.baseline, "central")}"'
            f'{weight}{style} fill="{_esc(element.colour)}"{role}>'
            f'{_esc(element.text)}</text>')


_WRITERS = ((Line, _line), (Polygon, _polygon), (Rect, _rect), (Text, _text))


def element_to_svg(element) -> str:
    for kind, writer in _WRITERS:
        if isinstance(element, kind):
            return writer(element)
    raise TypeError(f"no SVG writer for {type(element).__name__}")


def scene_to_svg(scene: Scene, element_id: str = "kundli",
                 class_name: str = "kundli") -> str:
    """
    One scene as a standalone `<svg>` element.

    Scales with its container — width and height are expressed only in the
    viewBox — so the same markup serves a thumbnail and a full-page chart,
    and text scales with it rather than staying fixed while the chart grows
    (Part 36 asks for scalable text).
    """
    body = "\n  ".join(element_to_svg(e) for e in scene.elements)
    title_id, desc_id = f"{element_id}-title", f"{element_id}-desc"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_fmt(scene.width)} {_fmt(scene.height)}" '
        f'class="{_esc(class_name)}" role="img" '
        f'aria-labelledby="{title_id} {desc_id}" '
        f'font-family="{FONT_STACK}">\n'
        f'  <title id="{title_id}">{_esc(scene.title)}</title>\n'
        f'  <desc id="{desc_id}">{_esc(scene.description)}</desc>\n'
        f'  {body}\n'
        f'</svg>')


def scene_to_svg_document(scene: Scene) -> str:
    """A complete .svg file, for saving a chart on its own."""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + scene_to_svg(scene) + "\n")
