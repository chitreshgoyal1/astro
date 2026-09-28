"""
Transit-to-natal relationships (V1.4 Part 18)
-----------------------------------------------
Factual relationships between a transiting graha and a natal point.

THE SEPARATION PART 18 REQUIRES

    same_sign            the classical rashi relationship
    angular_separation   the degree proximity

    These are different claims and neither is computed from the other. Two
    grahas can share a rashi while 29 degrees apart, and can be one degree
    apart across a rashi boundary. Collapsing them would silently impose a
    modern orb on a classical sign-based rule — the same error the natal
    conjunction engine was built to avoid.

DRISHTI

    The transit graha's drishti onto natal points uses the SAME aspect
    profile as the natal engine, from engine/features/aspects.py. It is not
    recomputed here.
"""

from __future__ import annotations

from typing import Optional

from ..features.aspects import parashari_profile
from .models import TransitNatalRelationship


def _separation(first: float, second: float) -> float:
    """Shortest angular separation, 0-180."""
    return abs((first - second + 180.0) % 360.0 - 180.0)


def _house_distance(from_sign: int, to_sign: int) -> int:
    """Inclusive count from one rashi to another, 1-12."""
    return ((to_sign - from_sign) % 12) + 1


def compute_relationships(positions: dict, natal_chart,
                          node_aspects: str = "none",
                          orb_deg: float = 3.0
                          ) -> list[TransitNatalRelationship]:
    """
    Every transit-to-natal relationship worth recording.

    Covers each transiting graha against every natal graha and against the
    natal Lagna. Drishti is judged by inclusive house distance in the natal
    rashi frame, which is what graha drishti means.
    """
    profile = parashari_profile(node_aspects)
    results: list[TransitNatalRelationship] = []

    targets: list[tuple[str, str, int, float]] = [
        (name, "planet", position.rashi_index, position.longitude)
        for name, position in natal_chart.planets.items()
    ]
    targets.append(("Lagna", "lagna", natal_chart.lagna.rashi_index,
                    natal_chart.lagna.longitude))

    for transit_name, transit in positions.items():
        distances = profile.distances_for(transit_name)
        for target_name, kind, target_sign, target_longitude in targets:
            distance = _house_distance(transit.sign, target_sign)
            separation = _separation(transit.longitude, target_longitude)
            aspects = distance in distances

            results.append(TransitNatalRelationship(
                transit_planet=transit_name,
                natal_target=target_name,
                target_kind=kind,
                same_sign=transit.sign == target_sign,
                angular_separation=separation,
                house_distance=distance,
                graha_drishti=aspects,
                drishti_type=(_drishti_name(distance) if aspects else None),
                within_orb=separation <= orb_deg,
                orb_used=orb_deg,
            ))
    return results


_DRISHTI_NAMES = {
    3: "special_3rd", 4: "special_4th", 5: "special_5th", 7: "seventh",
    8: "special_8th", 9: "special_9th", 10: "special_10th",
}


def _drishti_name(distance: int) -> str:
    return _DRISHTI_NAMES.get(distance, f"distance_{distance}")


def significant_relationships(relationships: list,
                              include_same_sign: bool = True,
                              include_drishti: bool = True,
                              include_orb: bool = True) -> list:
    """
    Filter to relationships that hold at all.

    "Significant" here means "the relationship exists", not "it matters".
    Whether a transit matters is interpretation and is not decided here.
    """
    return [
        relationship for relationship in relationships
        if (include_same_sign and relationship.same_sign)
        or (include_drishti and relationship.graha_drishti)
        or (include_orb and relationship.within_orb)
    ]
