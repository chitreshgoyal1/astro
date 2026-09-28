"""
TimingContext (V1.4 Part 20)
------------------------------
The V1.3-designed seam, now implemented: for one datetime, the natal chart,
the dasha stack and the transit snapshot in a single factual object.

WHAT IT IS FOR

    A future timing rule will want all three at once, and should not have to
    reach back into the ephemeris to get them. The intended shape is

        def applies(context: TimingContext) -> RuleResult

    with the engine supplying the context and the rule reading facts from it.

WHAT IT DOES NOT CONTAIN

    No synthesis and no score. Part 20 is explicit, and V1.4 is a calculation
    release. A TimingContext says where the grahas are, which dasha is
    running and how the two relate geometrically. What that means is not
    computed, here or anywhere else in this build.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional

from .calculator import get_transit_snapshot
from .models import TransitSnapshot


@dataclass
class TimingContext:
    """Natal chart, dasha stack and transits for one moment."""

    moment: datetime.datetime
    natal_snapshot: dict = field(default_factory=dict)
    dasha_stack: dict = field(default_factory=dict)
    transit_snapshot: Optional[TransitSnapshot] = None

    @property
    def mahadasha(self) -> Optional[str]:
        return self.dasha_stack.get("mahadasha")

    @property
    def antardasha(self) -> Optional[str]:
        return self.dasha_stack.get("antardasha")

    @property
    def pratyantardasha(self) -> Optional[str]:
        return self.dasha_stack.get("pratyantardasha")

    @property
    def dasha_lords(self) -> list[str]:
        """The active lords, outermost first, skipping any that are absent."""
        return [lord for lord in (self.mahadasha, self.antardasha,
                                  self.pratyantardasha) if lord]

    def transits_of_dasha_lords(self) -> list:
        """
        Where the active dasha lords are transiting.

        A convenience for the future timing layer, which will almost always
        want exactly this. It selects; it does not judge.
        """
        if self.transit_snapshot is None:
            return []
        lords = set(self.dasha_lords)
        return [relationship
                for relationship in self.transit_snapshot.relationships
                if relationship.transit_planet in lords]

    def to_dict(self) -> dict:
        return {
            "date": self.moment.isoformat(),
            "dasha": {
                "mahadasha": self.mahadasha,
                "antardasha": self.antardasha,
                "pratyantardasha": self.pratyantardasha,
            },
            "transits": (self.transit_snapshot.to_dict()
                         if self.transit_snapshot else None),
            "natal_snapshot_schema": self.natal_snapshot.get("schema_version"),
            "note": (
                "A factual timing context: natal chart, dasha stack and "
                "transits for one moment. No synthesis and no score."),
        }


def build_timing_context(moment: datetime.datetime,
                         natal_snapshot: dict,
                         dasha=None,
                         natal_chart=None,
                         **transit_kwargs) -> TimingContext:
    """
    Assemble the context for one moment.

    `dasha` is a VimshottariDasha; `natal_chart` a JyotishChart. Either may
    be omitted, and the context is still valid with that part empty rather
    than fabricated.
    """
    stack = {}
    if dasha is not None:
        stack = dasha.get_dasha_stack_at(moment)

    transits = None
    if natal_chart is not None:
        transits = get_transit_snapshot(moment, natal_chart=natal_chart,
                                        **transit_kwargs)

    return TimingContext(
        moment=moment,
        natal_snapshot=natal_snapshot,
        dasha_stack=stack,
        transit_snapshot=transits,
    )
