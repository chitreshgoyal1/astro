"""
Bhava models (V1.4 Parts 12-14)
---------------------------------
Two house representations that coexist and never merge.

THE RULE THIS PACKAGE ENFORCES

    A graha's RASHI, its sign lord, its dignity, its vargas and the houses it
    OWNS are properties of the zodiac. None of them changes because a
    different house-division scheme was selected.

    What changes is which BHAVA the graha falls in. That is one fact, and it
    is reported alongside the rashi house rather than instead of it — so a
    graha can be in the 5th rashi house and the 4th bhava, and both readings
    stay visible.

    `PlanetPlacement` therefore carries rashi_sign, rashi_house and
    bhava_house as three separate fields. Code that wants one must say which.

NAMING (Part 14)

    The house system is named — "sripati", "equal_from_lagna", "porphyry" —
    never just "bhava chalit", because several cusp methods exist and calling
    the result by the category would hide which was used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..planets import RASHI_LORDS, RASHI_NAMES


@dataclass(frozen=True)
class BhavaCusp:
    """
    One bhava: its centre, its span, and the rashi its centre falls in.

    `madhya` is the bhava madhya, the most sensitive point. `start` and `end`
    are the sandhis — the junctions with the neighbouring bhavas — so a bhava
    is the arc between them, centred on the madhya.
    """

    house: int
    madhya: float
    start: float
    end: float
    sign: int
    sign_lord: str
    secondary_sign: Optional[int] = None

    @property
    def span(self) -> float:
        """Arc length in degrees, handling the wrap at 360."""
        return (self.end - self.start) % 360.0

    def contains(self, longitude: float) -> bool:
        """Whether a longitude falls in this bhava, wrap included."""
        offset = (longitude - self.start) % 360.0
        return offset < self.span

    def to_dict(self) -> dict:
        data = {
            "house": self.house,
            "madhya": round(self.madhya, 6),
            "start": round(self.start, 6),
            "end": round(self.end, 6),
            "span": round(self.span, 6),
            "sign": RASHI_NAMES[self.sign],
            "sign_index": self.sign,
            "sign_lord": self.sign_lord,
        }
        if self.secondary_sign is not None:
            data["secondary_sign"] = RASHI_NAMES[self.secondary_sign]
            data["secondary_sign_index"] = self.secondary_sign
            data["secondary_note"] = (
                "This bhava spans two rashis. Its lord is taken from the "
                "rashi its madhya falls in; the other is recorded, not "
                "dropped.")
        return data


@dataclass(frozen=True)
class PlanetPlacement:
    """
    One graha in both representations at once.

    The whole point of this class is that `rashi_house` and `bhava_house` are
    separate fields which may differ. `moved` says whether they do.
    """

    planet: str
    longitude: float
    rashi_sign: int
    rashi_house: int
    bhava_house: int

    @property
    def moved(self) -> bool:
        return self.rashi_house != self.bhava_house

    @property
    def rashi_sign_name(self) -> str:
        return RASHI_NAMES[self.rashi_sign]

    @property
    def rashi_sign_lord(self) -> str:
        """Unchanged by the house system: lordship is a property of the sign."""
        return RASHI_LORDS[RASHI_NAMES[self.rashi_sign]]

    def describe(self) -> str:
        if not self.moved:
            return f"{self.planet}: rashi house {self.rashi_house}, unmoved"
        return (f"{self.planet}: rashi house {self.rashi_house}, "
                f"bhava house {self.bhava_house}")

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "longitude": round(self.longitude, 6),
            "rashi_sign": self.rashi_sign_name,
            "rashi_sign_index": self.rashi_sign,
            "rashi_sign_lord": self.rashi_sign_lord,
            "rashi_house": self.rashi_house,
            "bhava_house": self.bhava_house,
            "moved": self.moved,
        }


@dataclass
class BhavaChart:
    """A complete bhava representation, held beside the rashi chart."""

    system: str
    profile_id: str
    cusps: dict[int, BhavaCusp] = field(default_factory=dict)
    placements: dict[str, PlanetPlacement] = field(default_factory=dict)
    near_sandhi: list[str] = field(default_factory=list)
    source_ref_ids: tuple[str, ...] = ()
    validation_status: str = "UNVERIFIED"
    warnings: list[str] = field(default_factory=list)

    @property
    def divergences(self) -> list[str]:
        """Grahas whose bhava differs from their rashi house."""
        return [placement.describe()
                for placement in self.placements.values() if placement.moved]

    @property
    def moved_planets(self) -> list[str]:
        return [name for name, placement in self.placements.items()
                if placement.moved]

    def bhava_of(self, planet: str) -> Optional[int]:
        placement = self.placements.get(planet)
        return None if placement is None else placement.bhava_house

    def occupants(self, house: int) -> list[str]:
        return sorted(name for name, placement in self.placements.items()
                      if placement.bhava_house == house)

    def madhyas(self) -> dict[int, float]:
        return {house: cusp.madhya for house, cusp in self.cusps.items()}

    def to_dict(self) -> dict:
        return {
            "system": self.system,
            "profile_id": self.profile_id,
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status,
            "cusps": {str(h): c.to_dict() for h, c in sorted(self.cusps.items())},
            "placements": {n: p.to_dict()
                           for n, p in sorted(self.placements.items())},
            "divergences": self.divergences,
            "moved_planets": self.moved_planets,
            "near_sandhi": list(self.near_sandhi),
            "warnings": list(self.warnings),
            "note": (
                "This is a SEPARATE representation from the rashi chart. "
                "Sign, sign lord, dignity, vargas and houses owned are "
                "properties of the zodiac and are unaffected by it."),
        }
