"""
Vector scene (V1.7 Parts 7, 21, 38)
=====================================
A backend-neutral drawing: lines, polygons and text in a coordinate space,
with no idea what will draw them.

WHY NOT JUST EMIT SVG

    Part 7 asks for vector output usable in the UI, the PDF and print. SVG
    would serve the first; the PDF writer needs the same picture in
    PostScript operators. Generating both from one description means the
    kundli in the report is the kundli on the screen, and a visual
    regression test that pins the scene pins both at once.

DETERMINISM (Part 38)

    A scene is a tuple of frozen elements in the order they were added.
    There is no timestamp, no identifier generated from memory addresses,
    and no set iteration anywhere in construction, so the same model always
    produces the same scene and `scene_hash` is a usable fixture.

COORDINATES

    y grows DOWNWARD, as on a screen. The PDF backend flips it once, at the
    boundary, rather than every layout function having to know which way up
    the target is.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

#: Anchors for text placement. "middle" is the common case in a kundli,
#: where a label sits in the middle of a house.
ANCHORS = ("start", "middle", "end")

#: Vertical alignment relative to the given y.
BASELINES = ("baseline", "middle", "hanging")


@dataclass(frozen=True)
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = 1.0
    colour: str = "#000000"

    def to_dict(self) -> dict:
        return {"kind": "line", "x1": _r(self.x1), "y1": _r(self.y1),
                "x2": _r(self.x2), "y2": _r(self.y2),
                "width": self.width, "colour": self.colour}


@dataclass(frozen=True)
class Polygon:
    points: tuple[tuple[float, float], ...]
    fill: Optional[str] = None
    stroke: Optional[str] = "#000000"
    width: float = 1.0

    def to_dict(self) -> dict:
        return {"kind": "polygon",
                "points": [[_r(x), _r(y)] for x, y in self.points],
                "fill": self.fill, "stroke": self.stroke,
                "width": self.width}


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float
    fill: Optional[str] = None
    stroke: Optional[str] = "#000000"
    stroke_width: float = 1.0
    radius: float = 0.0

    def to_dict(self) -> dict:
        return {"kind": "rect", "x": _r(self.x), "y": _r(self.y),
                "width": _r(self.width), "height": _r(self.height),
                "fill": self.fill, "stroke": self.stroke,
                "stroke_width": self.stroke_width, "radius": self.radius}


@dataclass(frozen=True)
class Text:
    x: float
    y: float
    text: str
    size: float = 10.0
    anchor: str = "middle"
    baseline: str = "middle"
    weight: str = "normal"          # normal | bold
    italic: bool = False
    colour: str = "#000000"
    #: Marks text that carries meaning also encoded some other way, so an
    #: accessibility check can tell decoration from information (Part 36).
    role: str = ""

    def to_dict(self) -> dict:
        return {"kind": "text", "x": _r(self.x), "y": _r(self.y),
                "text": self.text, "size": self.size, "anchor": self.anchor,
                "baseline": self.baseline, "weight": self.weight,
                "italic": self.italic, "colour": self.colour,
                "role": self.role}


def _r(value: float) -> float:
    """
    Round to a tenth of a unit.

    Chart geometry is computed in floating point from divisions by 2 and 4,
    and a backend that printed 149.99999999999997 would make the golden
    fixtures depend on the platform's last bit. A tenth of a point is well
    below the resolution of anything that draws this.
    """
    return round(float(value) + 0.0, 4)


@dataclass
class Scene:
    """An ordered drawing in a fixed coordinate box."""

    width: float
    height: float
    elements: list = field(default_factory=list)
    title: str = ""
    #: A text equivalent of the picture, for readers who cannot see it
    #: (Part 36). Built by the layout code, which knows what it drew.
    description: str = ""

    def add(self, element) -> "Scene":
        self.elements.append(element)
        return self

    def extend(self, elements) -> "Scene":
        self.elements.extend(elements)
        return self

    def texts(self) -> list:
        return [e for e in self.elements if isinstance(e, Text)]

    def to_dict(self) -> dict:
        return {
            "width": _r(self.width), "height": _r(self.height),
            "title": self.title, "description": self.description,
            "elements": [e.to_dict() for e in self.elements],
        }

    def content_hash(self) -> str:
        """
        A stable fingerprint of the drawing.

        Used by the visual regression tests. It covers geometry and text and
        nothing else — no generation time, no file name, no ordering that
        depends on a dict — which is what makes a changed hash mean the
        picture changed.
        """
        payload = json.dumps(self.to_dict(), sort_keys=True,
                             ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
