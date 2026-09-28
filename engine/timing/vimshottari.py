"""
Vimshottari dasha engine (V1.2 Parts 4-8)
------------------------------------------
Deterministic, exact, and independent of any interpretation layer. Given the
Moon's sidereal longitude and the birth moment, it produces the full period
hierarchy with calendar dates.

Layer: TRADITION-SPECIFIC RULE (the cycle and proportions) resting on an
ASTRONOMICAL FACT (the Moon's longitude). No interpretation is attached — a
period is a span of time with a lord, and what that means for the native is
not decided here.

How it works
    The Moon's position within its nakshatra gives the fraction of the first
    mahadasha already elapsed at birth. That mahadasha therefore STARTS BEFORE
    BIRTH; the balance remaining at birth is what classical practice quotes.

    Every deeper level is the same operation applied again:

        child_duration = parent_duration * years[child_lord] / 120

    so one subdivision routine produces antardasha, pratyantardasha, and any
    level below without a separate calculation or a table of dates.

Precision
    All arithmetic is on exact Fractions of days, and every boundary is an
    offset from its parent's start rather than a running total. Consequently
    children sum to their parent exactly, the first child starts exactly at
    the parent's start, and the last child ends exactly at the parent's end —
    properties the test suite asserts rather than approximates.
"""

from __future__ import annotations

import datetime
from fractions import Fraction
from typing import Iterable, Optional

from .models import (
    DASHA_SEQUENCE, DEFAULT_YEAR_LENGTH, ENGLISH_NAME, NAKSHATRA_DASHA_LORD,
    NAKSHATRA_SPAN, TOTAL_YEARS, VIMSHOTTARI_YEARS, DashaPeriod, YearLength,
    _to_datetime, next_level, year_length,
)

# How many mahadashas to build by default: one full 120-year cycle.
DEFAULT_CYCLES = 1


# ── birth balance ────────────────────────────────────────────────────────────

def nakshatra_index(moon_longitude: float) -> int:
    """Index 0-26 of the nakshatra the Moon occupies."""
    return min(int((moon_longitude % 360.0) / float(NAKSHATRA_SPAN)), 26)


def birth_dasha_lord(moon_longitude: float) -> str:
    return NAKSHATRA_DASHA_LORD[nakshatra_index(moon_longitude)]


def elapsed_fraction(moon_longitude: float) -> Fraction:
    """
    Fraction of the birth nakshatra already traversed, as an exact Fraction.

    The float longitude is converted once, at full precision, and everything
    downstream stays exact.
    """
    longitude = Fraction(moon_longitude % 360.0).limit_denominator(10 ** 12)
    within = longitude % NAKSHATRA_SPAN
    return within / NAKSHATRA_SPAN


# ── generic subdivision ──────────────────────────────────────────────────────

def _sequence_from(lord: str) -> list[str]:
    """The nine lords in order, starting from the given one."""
    start = DASHA_SEQUENCE.index(lord)
    return [DASHA_SEQUENCE[(start + offset) % 9] for offset in range(9)]


def subdivide(parent: DashaPeriod, level: Optional[str] = None,
              epoch: Optional[datetime.datetime] = None) -> list[DashaPeriod]:
    """
    Divide a period into its nine sub-periods.

    This is the whole of Parts 6 and 7: antardasha and pratyantardasha are the
    same operation at different depths, not two calculations. A sub-period
    whose lord is L runs for `parent_duration * years[L] / 120`, and the
    sequence starts with the parent's own lord and continues cyclically.

    `epoch` is the datetime that offset zero corresponds to. When omitted the
    parent's own start is used, which is correct for any parent built by this
    module.
    """
    child_level = level or next_level(parent.level)
    if child_level is None:
        return []

    base = epoch if epoch is not None else _epoch_of(parent)
    children: list[DashaPeriod] = []
    offset = parent.start_offset_days

    for index, lord in enumerate(_sequence_from(parent.lord)):
        duration = (parent.duration_days_exact
                    * Fraction(VIMSHOTTARI_YEARS[lord], TOTAL_YEARS))
        child = DashaPeriod(
            level=child_level,
            lord=lord,
            start=_to_datetime(base, offset),
            end=_to_datetime(base, offset + duration),
            duration_days=float(duration),
            sequence_index=index,
            parent_lord=parent.lord,
            ancestors=parent.ancestors + (parent.lord,),
            start_offset_days=offset,
            duration_days_exact=duration,
        )
        children.append(child)
        offset += duration

    # The last child must land exactly on the parent's end. Fractions make
    # that exact, but assert it: a silent drift here would corrupt every
    # deeper level.
    assert offset == parent.start_offset_days + parent.duration_days_exact, (
        "subdivision did not sum to the parent duration")
    return children


def _epoch_of(period: DashaPeriod) -> datetime.datetime:
    """Recover the epoch that a period's offsets are measured from."""
    return _to_datetime(period.start, -period.start_offset_days)


# ── the tree ─────────────────────────────────────────────────────────────────

class VimshottariDasha:
    """
    The full period hierarchy for one birth.

    Construct once, then query. Building to `depth=3` (mahadasha ->
    antardasha -> pratyantardasha) yields 9 + 81 + 729 periods per cycle,
    which is cheap; deeper levels are available but not built by default.
    """

    def __init__(self,
                 moon_longitude: float,
                 birth: datetime.datetime,
                 depth: int = 3,
                 years: Optional[YearLength] = None,
                 cycles: int = DEFAULT_CYCLES):
        if depth < 1:
            raise ValueError("depth must be at least 1")
        self.moon_longitude = moon_longitude % 360.0
        self.birth = birth
        self.depth = depth
        self.years = years or DEFAULT_YEAR_LENGTH
        self.cycles = cycles

        self.nakshatra_index = nakshatra_index(self.moon_longitude)
        self.birth_lord = birth_dasha_lord(self.moon_longitude)
        self.elapsed_fraction = elapsed_fraction(self.moon_longitude)

        first_duration = (Fraction(VIMSHOTTARI_YEARS[self.birth_lord])
                          * self.years.days)
        self.elapsed_at_birth_days = self.elapsed_fraction * first_duration
        self.balance_at_birth_days = first_duration - self.elapsed_at_birth_days

        # The birth mahadasha began before birth, by the elapsed portion.
        self.cycle_start = _to_datetime(birth, -self.elapsed_at_birth_days)

        self.mahadashas: list[DashaPeriod] = self._build_mahadashas()
        if depth >= 2:
            self._build_below(self.mahadashas, depth)

    # ── construction ────────────────────────────────────────────────────────

    def _build_mahadashas(self) -> list[DashaPeriod]:
        periods: list[DashaPeriod] = []
        offset = Fraction(0)
        order = _sequence_from(self.birth_lord)
        index = 0
        for _cycle in range(self.cycles):
            for lord in order:
                duration = Fraction(VIMSHOTTARI_YEARS[lord]) * self.years.days
                periods.append(DashaPeriod(
                    level="mahadasha",
                    lord=lord,
                    start=_to_datetime(self.cycle_start, offset),
                    end=_to_datetime(self.cycle_start, offset + duration),
                    duration_days=float(duration),
                    sequence_index=index,
                    parent_lord=None,
                    ancestors=(),
                    start_offset_days=offset,
                    duration_days_exact=duration,
                ))
                offset += duration
                index += 1
        return periods

    def _build_below(self, periods: list[DashaPeriod], depth: int) -> None:
        current_depth = 1
        level_periods = periods
        while current_depth < depth:
            below: list[DashaPeriod] = []
            for period in level_periods:
                period.children = subdivide(period, epoch=self.cycle_start)
                below.extend(period.children)
            level_periods = below
            current_depth += 1

    # ── flat views ──────────────────────────────────────────────────────────

    def periods_at_level(self, level: str) -> list[DashaPeriod]:
        """Every period at one level, in chronological order."""
        result: list[DashaPeriod] = []

        def walk(nodes: Iterable[DashaPeriod]):
            for node in nodes:
                if node.level == level:
                    result.append(node)
                else:
                    walk(node.children)

        walk(self.mahadashas)
        return result

    @property
    def antardashas(self) -> list[DashaPeriod]:
        return self.periods_at_level("antardasha")

    @property
    def pratyantardashas(self) -> list[DashaPeriod]:
        return self.periods_at_level("pratyantardasha")

    # ── queries (Part 8) ────────────────────────────────────────────────────

    def _find(self, nodes: list[DashaPeriod],
              moment: datetime.datetime) -> Optional[DashaPeriod]:
        for node in nodes:
            if node.contains(moment):
                return node
        return None

    def get_mahadasha_at(self, moment: datetime.datetime) -> Optional[DashaPeriod]:
        return self._find(self.mahadashas, moment)

    def get_antardasha_at(self, moment: datetime.datetime) -> Optional[DashaPeriod]:
        maha = self.get_mahadasha_at(moment)
        return None if maha is None else self._find(maha.children, moment)

    def get_pratyantardasha_at(self, moment: datetime.datetime
                               ) -> Optional[DashaPeriod]:
        antar = self.get_antardasha_at(moment)
        return None if antar is None else self._find(antar.children, moment)

    def get_period_at(self, moment: datetime.datetime,
                      level: str) -> Optional[DashaPeriod]:
        """Period at any level, walking down only as far as needed."""
        node = self._find(self.mahadashas, moment)
        while node is not None and node.level != level:
            node = self._find(node.children, moment)
        return node

    def get_dasha_stack_at(self, moment: datetime.datetime) -> dict:
        """
        The full stack of lords in force at one moment.

        Returns the shape the V1.2 brief specifies, plus the period boundaries
        so a caller can tell how far into each level the moment sits.
        """
        maha = self.get_mahadasha_at(moment)
        antar = self.get_antardasha_at(moment)
        praty = self.get_pratyantardasha_at(moment)
        stack = {
            "date": moment.isoformat(),
            "mahadasha": maha.lord if maha else None,
            "antardasha": antar.lord if antar else None,
            "pratyantardasha": praty.lord if praty else None,
        }
        if maha is None:
            stack["in_range"] = False
            stack["note"] = ("outside the computed span "
                             f"({self.start.isoformat()} to {self.end.isoformat()})")
            return stack
        stack["in_range"] = True
        stack["periods"] = {
            period.level: {
                "lord": period.lord,
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
                "elapsed_fraction": round(
                    (moment - period.start) / (period.end - period.start), 6),
            }
            for period in (maha, antar, praty) if period is not None
        }
        return stack

    def get_periods_between(self, start: datetime.datetime,
                            end: datetime.datetime,
                            level: str = "mahadasha") -> list[DashaPeriod]:
        """Every period at `level` that overlaps the window, in order."""
        if end < start:
            raise ValueError("end must not precede start")
        return [p for p in self.periods_at_level(level) if p.overlaps(start, end)]

    # ── span ────────────────────────────────────────────────────────────────

    @property
    def start(self) -> datetime.datetime:
        return self.mahadashas[0].start

    @property
    def end(self) -> datetime.datetime:
        return self.mahadashas[-1].end

    # ── serialisation ───────────────────────────────────────────────────────

    def balance_summary(self) -> dict:
        """What classical practice quotes: the balance of dasha at birth."""
        total = Fraction(VIMSHOTTARI_YEARS[self.birth_lord]) * self.years.days
        return {
            "birth_nakshatra_index": self.nakshatra_index,
            "birth_dasha_lord": self.birth_lord,
            "birth_dasha_lord_english": ENGLISH_NAME[self.birth_lord],
            "elapsed_fraction": float(self.elapsed_fraction),
            "elapsed_days": float(self.elapsed_at_birth_days),
            "balance_days": float(self.balance_at_birth_days),
            "balance_years": float(self.balance_at_birth_days / self.years.days),
            "full_period_days": float(total),
            "mahadasha_started": self.cycle_start.isoformat(),
        }

    def to_dict(self, depth: Optional[int] = None) -> dict:
        """
        JSON-ready view. `depth` limits how far down the tree is serialised;
        the default follows however deep the tree was built.
        """
        limit = depth or self.depth

        def serialise(period: DashaPeriod, level_number: int) -> dict:
            data = period.to_dict()
            if level_number < limit and period.children:
                data["children"] = [serialise(child, level_number + 1)
                                    for child in period.children]
            return data

        return {
            "system": "vimshottari",
            "convention": {
                "year_length": self.years.name,
                "year_length_days": float(self.years.days),
                "year_length_note": self.years.description,
                "total_years": TOTAL_YEARS,
                "sequence": list(DASHA_SEQUENCE),
                "period_years": dict(VIMSHOTTARI_YEARS),
                "source": "BPHS ch.46 (Vimshottari Dasha Adhyaya)",
            },
            "moon_longitude": round(self.moon_longitude, 6),
            "birth": self.birth.isoformat(),
            "span": {"start": self.start.isoformat(), "end": self.end.isoformat()},
            "balance_at_birth": self.balance_summary(),
            "depth": limit,
            "mahadashas": [serialise(period, 1) for period in self.mahadashas],
        }


# ── convenience ──────────────────────────────────────────────────────────────

def compute_vimshottari(moon_longitude: float,
                        birth: datetime.datetime,
                        depth: int = 3,
                        year_length_name: str = DEFAULT_YEAR_LENGTH.name
                        ) -> VimshottariDasha:
    """Build the hierarchy from a Moon longitude and a birth moment."""
    return VimshottariDasha(moon_longitude=moon_longitude, birth=birth,
                            depth=depth, years=year_length(year_length_name))


def from_chart(chart, birth: datetime.datetime, depth: int = 3,
               year_length_name: str = DEFAULT_YEAR_LENGTH.name
               ) -> Optional[VimshottariDasha]:
    """Build from a JyotishChart, or None when the Moon is absent."""
    moon = chart.planets.get("Chandra")
    if moon is None:
        return None
    return compute_vimshottari(moon.longitude, birth, depth, year_length_name)
