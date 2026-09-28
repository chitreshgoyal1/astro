"""
Transit engine interfaces (V1.3 Part 21) — DEFINITIONS ONLY
------------------------------------------------------------
Shapes that a future transit engine will produce and consume. Nothing here
predicts anything, and nothing here decides what a transit means.

WHAT THIS MODULE IS FOR

    The V1.3 brief asks for interface design rather than implementation, so
    that the existing ChartSnapshot and dasha API can be checked to feed a
    transit engine cleanly BEFORE that engine exists. This module is that
    check, made executable: the dataclasses below are constructible from what
    the engine already produces, and a test constructs them.

    That turns "the architecture should support transits later" from an
    assertion into something the test suite verifies.

WHAT THIS MODULE IS NOT

    * No interpretation. A transit is a geometric relationship between a
      moving graha and a natal position. What it portends is not computed
      here and is out of scope for V1.3 entirely.
    * No prediction, no event timing, no scoring of periods.
    * No Gochara rules — not the Moon-referenced benefic/malefic tables, not
      Vedha, not Ashtakavarga transit strength. Those are TRADITION-SPECIFIC
      RULES and would need source validation before implementation, exactly
      like the yoga catalog.

DESIGN NOTE

    A transit snapshot is a natal chart's machinery pointed at a different
    moment. Deliberately so: reusing the same feature layer means transit
    positions get the same uncertainty envelopes, the same aspect profile and
    the same provenance discipline for free, rather than growing a parallel
    implementation that drifts.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional

# ── What a transit engine will need from what already exists ─────────────────
#
# Checked by tests/test_transit_interface.py against the real objects:
#
#   ChartSnapshot           natal positions, houses, features, methodology
#   VimshottariDasha        get_dasha_stack_at(), get_periods_between()
#   build_chart_features()  the same feature derivation, at any moment
#   assess_position()       the same uncertainty envelopes
#   parashari_profile()     the same drishti conventions
#
# Nothing new is required from the existing layers. That was the question
# Part 21 asked, and the answer is recorded here rather than assumed.

REQUIRED_NATAL_SECTIONS = (
    "planets", "lagna", "houses", "calculation_settings", "methodology",
)

REQUIRED_DASHA_METHODS = (
    "get_mahadasha_at", "get_antardasha_at", "get_pratyantardasha_at",
    "get_dasha_stack_at", "get_periods_between",
)


@dataclass(frozen=True)
class TransitAspect:
    """
    One geometric relationship between a transiting graha and a natal point.

    `aspect_type` reuses the natal vocabulary (`seventh`, `special_4th`, …)
    so that a consumer does not have to learn a second one. `exact_within_deg`
    is the orb actually measured, not a verdict about significance.
    """

    transiting: str
    natal_target: str               # graha name, "Lagna", or "house:7"
    aspect_type: str
    separation_deg: float
    applying: Optional[bool] = None  # closing (True) or separating (False)
    exact_within_deg: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "transiting": self.transiting,
            "natal_target": self.natal_target,
            "aspect_type": self.aspect_type,
            "separation_deg": round(self.separation_deg, 4),
            "applying": self.applying,
            "exact_within_deg": self.exact_within_deg,
        }


@dataclass
class TransitSnapshot:
    """
    Where the grahas are at one moment, expressed against a natal chart.

    Three house frames are carried because Jyotish uses all three and they
    disagree: transits are read from the Lagna, from the natal Moon, and
    sometimes from the transiting Moon. Collapsing them to one would silently
    pick a tradition.
    """

    moment: datetime.datetime
    settings: dict = field(default_factory=dict)

    # Transiting positions, same shape as the natal `planets` section.
    planets: dict = field(default_factory=dict)

    # The transiting grahas placed in natal house frames.
    houses_from_lagna: dict = field(default_factory=dict)    # graha -> 1..12
    houses_from_moon: dict = field(default_factory=dict)     # graha -> 1..12

    # Relationships. `natal_aspects` is the natal chart's own aspect set,
    # carried so a consumer has both sides without re-deriving one.
    natal_aspects: list = field(default_factory=list)
    transit_to_natal_aspects: list = field(default_factory=list)

    # Numerical honesty travels with transits too.
    uncertainty: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "moment": self.moment.isoformat(),
            "settings": self.settings,
            "planets": self.planets,
            "houses_from_lagna": self.houses_from_lagna,
            "houses_from_moon": self.houses_from_moon,
            "natal_aspects": self.natal_aspects,
            "transit_to_natal_aspects": [
                aspect.to_dict() if isinstance(aspect, TransitAspect) else aspect
                for aspect in self.transit_to_natal_aspects],
            "uncertainty": self.uncertainty,
        }


@dataclass
class TimingContext:
    """
    Everything a timing rule would need about one moment, in one object.

    The intended shape of a future rule is:

        def applies(context: TimingContext) -> RuleResult

    with the rule reading natal facts, the dasha stack and the transit
    snapshot, and the engine supplying all three. A rule that reached back
    into the ephemeris itself would be recreating the V1.0 mistake the
    features/rules split was introduced to fix.
    """

    natal_snapshot: dict                       # ChartSnapshot.to_dict()
    dasha_stack: dict = field(default_factory=dict)
    transit_snapshot: Optional[TransitSnapshot] = None
    moment: Optional[datetime.datetime] = None

    @property
    def mahadasha(self) -> Optional[str]:
        return self.dasha_stack.get("mahadasha")

    @property
    def antardasha(self) -> Optional[str]:
        return self.dasha_stack.get("antardasha")

    @property
    def pratyantardasha(self) -> Optional[str]:
        return self.dasha_stack.get("pratyantardasha")

    def to_dict(self) -> dict:
        return {
            "moment": self.moment.isoformat() if self.moment else None,
            "natal_snapshot_schema": self.natal_snapshot.get("schema_version"),
            "dasha_stack": self.dasha_stack,
            "transit_snapshot": (self.transit_snapshot.to_dict()
                                 if self.transit_snapshot else None),
        }


# ── Feasibility check, run by the tests ──────────────────────────────────────

def natal_snapshot_is_sufficient(snapshot: dict) -> tuple[bool, list[str]]:
    """Whether a ChartSnapshot carries what a transit engine would need."""
    missing = [section for section in REQUIRED_NATAL_SECTIONS
               if section not in snapshot]
    return (not missing), missing


def dasha_api_is_sufficient(dasha) -> tuple[bool, list[str]]:
    """Whether the Vimshottari object exposes the queries a rule would need."""
    missing = [name for name in REQUIRED_DASHA_METHODS
               if not callable(getattr(dasha, name, None))]
    return (not missing), missing


OUT_OF_SCOPE_FOR_V1_3 = (
    "Gochara benefic/malefic tables from the Moon",
    "Vedha (obstruction) rules",
    "Ashtakavarga transit strength",
    "Sade Sati and other named Saturn periods",
    "Event prediction of any kind",
    "Dasha-transit combination scoring",
)
