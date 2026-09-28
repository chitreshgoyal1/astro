"""
Transit calculation (V1.4 Part 17)
------------------------------------
Positions at an arbitrary moment, using the ephemeris the natal chart already
uses. There is no separate transit ephemeris and no second implementation of
anything: a transit chart is the same calculation pointed at a different
time.

That reuse is deliberate. It means transit positions inherit the same VSOP87
accuracy, the same uncertainty envelopes and the same retrograde derivation
as natal ones, and cannot drift away from them.
"""

from __future__ import annotations

import datetime
from typing import Optional

from ..planets import JyotishChart, PLANET_NAMES, jde_from_datetime
from ..uncertainty import assess_position
from .models import TransitPosition, TransitSnapshot


def _house_from(sign: int, reference_sign: Optional[int]) -> Optional[int]:
    if reference_sign is None:
        return None
    return ((sign - reference_sign) % 12) + 1


def compute_transit_positions(moment: datetime.datetime,
                              latitude: float = 0.0,
                              longitude: float = 0.0,
                              ayanamsha_system: str = "lahiri",
                              true_node: bool = True,
                              natal_lagna_sign: Optional[int] = None,
                              natal_moon_sign: Optional[int] = None
                              ) -> dict[str, TransitPosition]:
    """
    Transiting positions at `moment`, which must be UTC.

    Latitude and longitude only affect the Ascendant, which a transit chart
    does not use, so they default to the equator at Greenwich. They are
    accepted because a caller may want the transiting Lagna for other
    purposes.
    """
    chart = JyotishChart(jde=jde_from_datetime(moment),
                         lat=latitude, lon=longitude,
                         ayanamsha_system=ayanamsha_system,
                         true_node=true_node)

    positions: dict[str, TransitPosition] = {}
    for name in PLANET_NAMES:
        position = chart.planets.get(name)
        if position is None:
            continue
        positions[name] = TransitPosition(
            planet=name,
            longitude=position.longitude,
            sign=position.rashi_index,
            sign_name=position.rashi,
            degree_in_sign=position.degree_in_rashi,
            nakshatra=position.nakshatra,
            nakshatra_lord=position.nakshatra_lord,
            pada=position.pada,
            speed=position.speed,
            retrograde=position.is_retrograde,
            stationary=position.is_stationary,
            house_from_natal_lagna=_house_from(position.rashi_index,
                                               natal_lagna_sign),
            house_from_natal_moon=_house_from(position.rashi_index,
                                              natal_moon_sign),
        )
    return positions


def get_transit_snapshot(moment: datetime.datetime,
                         natal_chart=None,
                         natal_features=None,
                         ayanamsha_system: str = "lahiri",
                         true_node: bool = True,
                         node_aspects: str = "none",
                         orb_deg: float = 3.0) -> TransitSnapshot:
    """
    A complete transit snapshot for one moment.

    With a natal chart supplied, the transiting grahas are placed in the
    natal house frames and the transit-to-natal relationships are computed.
    Without one, the snapshot is still valid and simply carries positions.
    """
    natal_lagna_sign = None
    natal_moon_sign = None
    if natal_chart is not None:
        natal_lagna_sign = natal_chart.lagna.rashi_index
        moon = natal_chart.planets.get("Chandra")
        natal_moon_sign = moon.rashi_index if moon else None

    positions = compute_transit_positions(
        moment, ayanamsha_system=ayanamsha_system, true_node=true_node,
        natal_lagna_sign=natal_lagna_sign, natal_moon_sign=natal_moon_sign)

    uncertainty = {
        name: assess_position(name, position.longitude,
                              true_node=true_node).to_dict()
        for name, position in positions.items()
    }

    relationships = []
    if natal_chart is not None:
        from .relationships import compute_relationships
        relationships = compute_relationships(
            positions, natal_chart, node_aspects=node_aspects,
            orb_deg=orb_deg)

    return TransitSnapshot(
        moment=moment,
        calculation_settings={
            "zodiac": "sidereal",
            "ayanamsha": ayanamsha_system,
            "node": "true" if true_node else "mean",
            "node_aspects": node_aspects,
            "orb_deg": orb_deg,
        },
        positions=positions,
        natal_lagna_sign=natal_lagna_sign,
        natal_moon_sign=natal_moon_sign,
        relationships=relationships,
        uncertainty=uncertainty,
    )
