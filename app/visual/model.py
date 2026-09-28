"""
Chart visual model (V1.7 Part 7)
==================================
What a kundli renderer is given, and the complete list of what it is allowed
to know.

THE POINT OF THIS OBJECT

    A renderer that receives a chart can ask it questions. A renderer that
    receives this cannot: there is no method here that computes anything, no
    reference to a chart, and no way to reach the engine. Every value was
    decided upstream and written down.

    So `dignity_marker` is a string the engine already chose, not a rule the
    drawing code evaluates. `house` is the whole-sign house the engine
    assigned, not `(sign - lagna) % 12` worked out in a template. If a
    renderer needs a fact that is not on this object, the fix is to put it
    on the object — never to derive it where it is drawn.

WHY IT IS FROZEN AND JSON-NATIVE

    The same model feeds the screen, the PDF and the golden tests. Freezing
    it means the PDF cannot quietly differ from the screen because one of
    them adjusted a field; `to_dict` means a visual regression test can pin
    the model itself, separately from the geometry that draws it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

#: How much goes inside each house box (Part 8). Presentation only —
#: changing it never changes a placement.
DETAIL_LEVELS = ("COMPACT", "STANDARD", "DETAILED")

#: Chart styles. North Indian is implemented; the others are named here so
#: that a caller asking for one gets a clear refusal rather than a chart in
#: the wrong style (Part 6: style is presentation, never calculation).
CHART_STYLES = ("north_indian", "south_indian", "east_indian")


@dataclass(frozen=True)
class PlacedBody:
    """One graha or the Lagna, positioned and labelled."""

    name: str                       # engine key: "Guru"
    display: str                    # what to draw: "Gu" or "Guru"
    house: int                      # 1-12
    sign_index: int                 # 0-11
    sign_name: str = ""
    degree: Optional[float] = None  # degree within the sign, D1 only
    retrograde: bool = False
    combust: bool = False
    dignity_marker: str = ""        # "exalted" | "debilitated" | "own" | ...
    nakshatra: str = ""
    pada: Optional[int] = None
    is_lagna: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name, "display": self.display, "house": self.house,
            "sign_index": self.sign_index, "sign_name": self.sign_name,
            "degree": (round(self.degree, 4) if self.degree is not None
                       else None),
            "retrograde": self.retrograde, "combust": self.combust,
            "dignity_marker": self.dignity_marker,
            "nakshatra": self.nakshatra, "pada": self.pada,
            "is_lagna": self.is_lagna,
        }


@dataclass(frozen=True)
class HouseCell:
    """One bhava of the chart, with the sign that falls in it."""

    number: int                     # 1-12
    sign_index: int                 # 0-11
    sign_name: str
    lord: str = ""
    bodies: tuple[PlacedBody, ...] = ()

    def to_dict(self) -> dict:
        return {
            "number": self.number, "sign_index": self.sign_index,
            "sign_name": self.sign_name, "lord": self.lord,
            "bodies": [b.to_dict() for b in self.bodies],
        }


@dataclass(frozen=True)
class ChartVisualModel:
    """A single divisional chart, ready to draw."""

    chart_name: str                 # "D1"
    title: str                      # "Rashi (D1)"
    lagna_sign: int                 # 0-11
    lagna_sign_name: str
    houses: tuple[HouseCell, ...] = ()
    style: str = "north_indian"
    detail: str = "STANDARD"
    convention: str = ""            # which varga rule produced the placements
    #: Sentences to show beside the chart. Birth-time instability, mostly;
    #: Part 10 asks for it to be visible on the chart, not in a footnote.
    notes: tuple[str, ...] = ()
    subject: str = ""

    def house(self, number: int) -> Optional[HouseCell]:
        for cell in self.houses:
            if cell.number == number:
                return cell
        return None

    def bodies(self) -> tuple[PlacedBody, ...]:
        return tuple(b for cell in self.houses for b in cell.bodies)

    @property
    def is_crowded(self) -> bool:
        """Whether any house holds enough bodies to need compact drawing."""
        return any(len(cell.bodies) > 3 for cell in self.houses)

    def to_dict(self) -> dict:
        return {
            "chart_name": self.chart_name,
            "title": self.title,
            "lagna_sign": self.lagna_sign,
            "lagna_sign_name": self.lagna_sign_name,
            "style": self.style,
            "detail": self.detail,
            "convention": self.convention,
            "notes": list(self.notes),
            "subject": self.subject,
            "houses": [cell.to_dict() for cell in self.houses],
        }
