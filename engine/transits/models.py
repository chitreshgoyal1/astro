"""
Transit models (V1.4 Parts 17, 18)
------------------------------------
Where the grahas are at a moment, and how that relates to a natal chart.

FACTS ONLY. A transit is a geometric relationship. Nothing here says a
transit is good, bad, timely or significant. The V1.3 interface module
already recorded that Gochara rules, Vedha, Ashtakavarga transit strength and
Sade Sati are out of scope until they have sources; that remains true.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TransitPosition:
    """One graha at one moment."""

    planet: str
    longitude: float
    sign: int
    sign_name: str
    degree_in_sign: float
    nakshatra: str
    nakshatra_lord: str
    pada: int
    speed: float
    retrograde: bool
    stationary: bool
    house_from_natal_lagna: Optional[int] = None
    house_from_natal_moon: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "longitude": round(self.longitude, 6),
            "sign": self.sign_name,
            "sign_index": self.sign,
            "degree_in_sign": round(self.degree_in_sign, 6),
            "nakshatra": self.nakshatra,
            "nakshatra_lord": self.nakshatra_lord,
            "pada": self.pada,
            "speed_deg_per_day": round(self.speed, 6),
            "retrograde": self.retrograde,
            "stationary": self.stationary,
            "house_from_natal_lagna": self.house_from_natal_lagna,
            "house_from_natal_moon": self.house_from_natal_moon,
        }


@dataclass(frozen=True)
class TransitNatalRelationship:
    """
    One factual relationship between a transiting graha and a natal point.

    Part 18 requires the classical sign/house relationship and the degree
    proximity to be kept apart, so `same_sign` and `angular_separation` are
    separate fields and neither is derived from the other. Two grahas can
    share a rashi while nearly 30 degrees apart, and can be a degree apart
    across a rashi boundary.
    """

    transit_planet: str
    natal_target: str                 # graha name or "Lagna"
    target_kind: str                  # "planet" | "lagna"
    same_sign: bool
    angular_separation: float
    house_distance: int               # inclusive count, 1-12
    graha_drishti: bool
    drishti_type: Optional[str] = None
    within_orb: bool = False
    orb_used: float = 0.0

    def to_dict(self) -> dict:
        return {
            "transit_planet": self.transit_planet,
            "natal_target": self.natal_target,
            "target_kind": self.target_kind,
            "same_sign": self.same_sign,
            "angular_separation": round(self.angular_separation, 4),
            "house_distance": self.house_distance,
            "graha_drishti": self.graha_drishti,
            "drishti_type": self.drishti_type,
            "within_orb": self.within_orb,
            "orb_used": self.orb_used,
        }


@dataclass
class TransitSnapshot:
    """The sky at one moment, expressed against a natal chart."""

    moment: datetime.datetime
    calculation_settings: dict = field(default_factory=dict)
    positions: dict = field(default_factory=dict)
    natal_lagna_sign: Optional[int] = None
    natal_moon_sign: Optional[int] = None
    relationships: list = field(default_factory=list)
    uncertainty: dict = field(default_factory=dict)

    @property
    def retrograde_states(self) -> dict:
        return {name: position.retrograde
                for name, position in self.positions.items()}

    @property
    def nakshatras(self) -> dict:
        return {name: position.nakshatra
                for name, position in self.positions.items()}

    def relationships_for(self, transit_planet: str) -> list:
        return [r for r in self.relationships
                if r.transit_planet == transit_planet]

    def to_dict(self) -> dict:
        return {
            "datetime": self.moment.isoformat(),
            "calculation_settings": self.calculation_settings,
            "planetary_positions": {n: p.to_dict()
                                    for n, p in self.positions.items()},
            "retrograde_states": self.retrograde_states,
            "nakshatras": self.nakshatras,
            "houses_from_natal_lagna": {
                n: p.house_from_natal_lagna
                for n, p in self.positions.items()},
            "houses_from_natal_moon": {
                n: p.house_from_natal_moon
                for n, p in self.positions.items()},
            "transit_to_natal": [r.to_dict() for r in self.relationships],
            "uncertainty": self.uncertainty,
            "note": (
                "Factual positions and relationships only. No Gochara rule, "
                "no benefic or malefic judgement, no prediction."),
        }


@dataclass(frozen=True)
class TransitEvent:
    """
    An astronomical state transition.

    Deliberately neutral: an ingress is an ingress. Part 19 forbids labelling
    events good or bad, and this vocabulary has no room to.
    """

    kind: str
    planet: str
    moment: datetime.datetime
    detail: str
    from_value: Optional[str] = None
    to_value: Optional[str] = None
    target: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "planet": self.planet,
            "datetime": self.moment.isoformat(),
            "detail": self.detail,
            "from": self.from_value,
            "to": self.to_value,
            "target": self.target,
        }


EVENT_KINDS = (
    "sign_ingress",
    "nakshatra_ingress",
    "station_retrograde",
    "station_direct",
    "exact_conjunction",
    "exact_aspect",
)
