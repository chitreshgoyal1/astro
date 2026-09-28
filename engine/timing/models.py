"""
Timing models — canonical Vimshottari constants and period structures
----------------------------------------------------------------------
Every number the Vimshottari system depends on lives here, once. Nothing
duplicates the period lengths or the sequence: a second copy is a second thing
to get wrong.

Layer: TRADITION-SPECIFIC RULE. The 120-year cycle and its nine divisions are
classical (BPHS ch.46, Vimshottari Dasha Adhyaya). The *year length* used to
convert those years into calendar dates is NOT specified by the classical
texts in days, so it is an explicit, configurable convention — see YearLength.

Numerical policy
    All durations are held as exact Fractions of days and every boundary is
    computed as an offset from its parent's start. Nothing accumulates by
    repeated addition of rounded years or months, so children sum to their
    parent exactly rather than approximately.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

# ── The canonical cycle ──────────────────────────────────────────────────────
# BPHS ch.46. The order is fixed and the periods sum to 120 years.
# Sanskrit names are used internally, matching the rest of the engine.

DASHA_SEQUENCE: tuple[str, ...] = (
    "Ketu", "Shukra", "Surya", "Chandra", "Mangal",
    "Rahu", "Guru", "Shani", "Budha",
)

VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7,
    "Shukra": 20,      # Venus
    "Surya": 6,        # Sun
    "Chandra": 10,     # Moon
    "Mangal": 7,       # Mars
    "Rahu": 18,
    "Guru": 16,        # Jupiter
    "Shani": 19,       # Saturn
    "Budha": 17,       # Mercury
}

TOTAL_YEARS: int = sum(VIMSHOTTARI_YEARS.values())     # 120

ENGLISH_NAME: dict[str, str] = {
    "Ketu": "Ketu", "Shukra": "Venus", "Surya": "Sun", "Chandra": "Moon",
    "Mangal": "Mars", "Rahu": "Rahu", "Guru": "Jupiter", "Shani": "Saturn",
    "Budha": "Mercury",
}

assert TOTAL_YEARS == 120, "the Vimshottari cycle must total 120 years"
assert len(DASHA_SEQUENCE) == 9
assert set(DASHA_SEQUENCE) == set(VIMSHOTTARI_YEARS)

# The 27 nakshatras map onto the nine lords, repeating three times. Derived
# from the sequence rather than written out, so it cannot disagree with it.
NAKSHATRA_DASHA_LORD: tuple[str, ...] = tuple(
    DASHA_SEQUENCE[index % 9] for index in range(27))

NAKSHATRA_SPAN = Fraction(360, 27)      # 13°20' exactly


# ── Level hierarchy ──────────────────────────────────────────────────────────
# Adding Sukshma and Prana later means extending this tuple. The subdivision
# engine is level-agnostic and reads the order from here.

DASHA_LEVELS: tuple[str, ...] = (
    "mahadasha",        # 1
    "antardasha",       # 2  (bhukti)
    "pratyantardasha",  # 3
    "sukshma",          # 4  — supported by the engine, not built by default
    "prana",            # 5
)

LEVEL_INDEX: dict[str, int] = {name: i for i, name in enumerate(DASHA_LEVELS)}


def next_level(level: str) -> Optional[str]:
    """The level below this one, or None at the bottom of the hierarchy."""
    index = LEVEL_INDEX[level] + 1
    return DASHA_LEVELS[index] if index < len(DASHA_LEVELS) else None


# ── Year length convention ───────────────────────────────────────────────────

@dataclass(frozen=True)
class YearLength:
    """
    How many days a 'year' of a dasha period is worth.

    The classical texts state period lengths in years but do not define the
    year in days, so software must choose — and the choice shifts long-period
    boundaries by months. It is therefore named, configurable, and recorded in
    every result rather than buried in a constant.
    """

    name: str
    days: Fraction
    description: str

    @property
    def days_float(self) -> float:
        return float(self.days)


# 365.25 days. The usual choice in Jyotish software and the one that makes a
# 120-year cycle exactly 43,830 days.
JULIAN_YEAR = YearLength(
    "julian", Fraction(36525, 100),
    "365.25 days — the Julian year; the common default in Jyotish software")

# 365.2425 days, the mean Gregorian calendar year.
GREGORIAN_YEAR = YearLength(
    "gregorian", Fraction(3652425, 10000),
    "365.2425 days — the mean Gregorian calendar year")

# 365.25636 days, the time the Sun takes to return to the same fixed star.
# Arguably the most defensible for a sidereal system, and used by some schools.
SIDEREAL_YEAR = YearLength(
    "sidereal", Fraction(36525636, 100000),
    "365.25636 days — the sidereal year, the Sun's return to a fixed star")

# 360 days. The savana or 'astrological' year used by some traditions.
SAVANA_YEAR = YearLength(
    "savana", Fraction(360),
    "360 days — the savana year used by some traditions; note this makes the "
    "120-year cycle 43,200 days, about 1.7 calendar years shorter")

YEAR_LENGTHS: dict[str, YearLength] = {
    year.name: year for year in
    (JULIAN_YEAR, GREGORIAN_YEAR, SIDEREAL_YEAR, SAVANA_YEAR)
}

DEFAULT_YEAR_LENGTH = JULIAN_YEAR


def year_length(name: str) -> YearLength:
    if name not in YEAR_LENGTHS:
        raise ValueError(
            f"Unknown year-length convention '{name}'. "
            f"Available: {', '.join(sorted(YEAR_LENGTHS))}")
    return YEAR_LENGTHS[name]


# ── Periods ──────────────────────────────────────────────────────────────────

def _to_datetime(epoch: datetime.datetime, offset_days: Fraction
                 ) -> datetime.datetime:
    """
    Exact offset from an epoch, to microsecond resolution.

    The Fraction is converted once, at the very end of the arithmetic, so no
    intermediate rounding can accumulate.
    """
    microseconds = offset_days * 86_400_000_000
    return epoch + datetime.timedelta(
        microseconds=int(round(float(microseconds))))


@dataclass
class DashaPeriod:
    """
    One period at one level of the hierarchy.

    `start_offset_days` and `duration_days_exact` are the exact Fractions the
    period was built from; `start` and `end` are their datetime rendering.
    Subdivision always works from the exact values, never from the datetimes,
    so depth does not degrade precision.
    """

    level: str
    lord: str
    start: datetime.datetime
    end: datetime.datetime
    duration_days: float
    sequence_index: int
    parent_lord: Optional[str] = None
    ancestors: tuple[str, ...] = ()          # outermost first
    children: list["DashaPeriod"] = field(default_factory=list)

    # Exact internals, kept for further subdivision.
    start_offset_days: Fraction = Fraction(0)
    duration_days_exact: Fraction = Fraction(0)

    @property
    def mahadasha(self) -> str:
        return self.ancestors[0] if self.ancestors else self.lord

    @property
    def antardasha(self) -> Optional[str]:
        if self.level == "antardasha":
            return self.lord
        return self.ancestors[1] if len(self.ancestors) > 1 else None

    @property
    def pratyantardasha(self) -> Optional[str]:
        if self.level == "pratyantardasha":
            return self.lord
        return self.ancestors[2] if len(self.ancestors) > 2 else None

    @property
    def duration_years(self) -> float:
        return self.duration_days / 365.25

    def contains(self, moment: datetime.datetime) -> bool:
        """Half-open interval: a boundary instant belongs to the later period."""
        return self.start <= moment < self.end

    def overlaps(self, start: datetime.datetime,
                 end: datetime.datetime) -> bool:
        return self.start < end and start < self.end

    def path(self) -> list[str]:
        return list(self.ancestors) + [self.lord]

    def label(self) -> str:
        return " / ".join(self.path())

    def to_dict(self, include_children: bool = False) -> dict:
        data = {
            "level": self.level,
            "lord": self.lord,
            "lord_english": ENGLISH_NAME.get(self.lord, self.lord),
            "parent_lord": self.parent_lord,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_days": round(self.duration_days, 6),
            "sequence_index": self.sequence_index,
        }
        if self.ancestors:
            data["mahadasha"] = self.mahadasha
            if self.antardasha:
                data["antardasha"] = self.antardasha
        if include_children and self.children:
            data["children"] = [c.to_dict(include_children=True)
                                for c in self.children]
        return data

    def __str__(self) -> str:
        return (f"{self.level:<16} {self.label():<28} "
                f"{self.start:%Y-%m-%d} -> {self.end:%Y-%m-%d} "
                f"({self.duration_days:.2f} d)")
