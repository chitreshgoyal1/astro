"""
Parashari aspect engine (Part 5)
--------------------------------
Graha drishti as a configurable system. Every graha aspects the 7th house from
itself; Mangal, Guru and Shani additionally have special aspects. Houses are
counted inclusively in the classical way, so the graha's own house is 1 and the
opposite house is 7.

Rahu and Ketu are the deliberate gap. Traditions disagree sharply — some give
them no drishti at all, some give them Jupiter-like 5/7/9, some give 3/7/11,
some treat them as aspecting only the kendras. Rather than pick one silently,
the node convention is a named profile and the default (`none`) asserts nothing.
Any Yoga result that depends on a node aspect therefore carries the profile
name that produced it.

Rashi drishti (sign-to-sign aspects) is a different system and is not mixed in
here; it would be a separate profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import Aspect

ALL_GRAHAS = ("Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra",
              "Shani", "Rahu", "Ketu")

# Inclusive house distance -> aspect type name.
_TYPE_NAMES = {
    3: "special_3rd", 4: "special_4th", 5: "special_5th",
    7: "seventh", 8: "special_8th", 9: "special_9th",
    10: "special_10th", 11: "special_11th",
}


def _type_name(distance: int) -> str:
    return _TYPE_NAMES.get(distance, f"distance_{distance}")


@dataclass(frozen=True)
class AspectProfile:
    """
    A named drishti convention.

    `aspects` maps a graha to the inclusive house distances it aspects.
    `strengths` optionally overrides the 0.0-1.0 weight of a given distance for
    a given graha; anything unlisted is full strength.
    """

    name: str
    description: str
    aspects: dict[str, tuple[int, ...]]
    strengths: dict[tuple[str, int], float] = field(default_factory=dict)
    node_convention: str = "none"

    def distances_for(self, planet: str) -> tuple[int, ...]:
        return self.aspects.get(planet, ())

    def strength_of(self, planet: str, distance: int) -> float:
        return self.strengths.get((planet, distance), 1.0)


# Every classical graha aspects the 7th.
_SEVENTH_ONLY = (7,)

_PARASHARI_BASE: dict[str, tuple[int, ...]] = {
    "Surya": _SEVENTH_ONLY,
    "Chandra": _SEVENTH_ONLY,
    "Budha": _SEVENTH_ONLY,
    "Shukra": _SEVENTH_ONLY,
    "Mangal": (4, 7, 8),
    "Guru": (5, 7, 9),
    "Shani": (3, 7, 10),
}

# Named node conventions. `none` is the default and is the honest position:
# the engine reports that it made no claim, rather than making one quietly.
NODE_ASPECT_CONVENTIONS: dict[str, tuple[int, ...]] = {
    "none": (),
    "parashari_like": (5, 7, 9),     # follows Guru; common in several schools
    "kendra": (4, 7, 10),            # nodes aspect the kendras from themselves
}


def _build_parashari(node_convention: str) -> dict[str, tuple[int, ...]]:
    if node_convention not in NODE_ASPECT_CONVENTIONS:
        raise ValueError(
            f"Unknown node aspect convention '{node_convention}'. "
            f"Available: {', '.join(NODE_ASPECT_CONVENTIONS)}")
    table = dict(_PARASHARI_BASE)
    node_aspects = NODE_ASPECT_CONVENTIONS[node_convention]
    table["Rahu"] = node_aspects
    table["Ketu"] = node_aspects
    return table


def parashari_profile(node_convention: str = "none") -> AspectProfile:
    """The default drishti system, with an explicit choice for the nodes."""
    if node_convention not in NODE_ASPECT_CONVENTIONS:
        raise ValueError(
            f"Unknown node aspect convention '{node_convention}'. "
            f"Available: {', '.join(NODE_ASPECT_CONVENTIONS)}")
    return AspectProfile(
        name=f"parashari/nodes={node_convention}",
        description=(
            "All grahas aspect the 7th; Mangal also 4th and 8th; Guru also 5th "
            "and 9th; Shani also 3rd and 10th. "
            + {
                "none": "Rahu and Ketu are given no drishti.",
                "parashari_like": "Rahu and Ketu aspect the 5th, 7th and 9th.",
                "kendra": "Rahu and Ketu aspect the 4th, 7th and 10th.",
            }[node_convention]),
        aspects=_build_parashari(node_convention),
        node_convention=node_convention,
    )


DEFAULT_ASPECT_PROFILE = parashari_profile("none")


def compute_aspects(planet_houses: dict[str, int],
                    planet_signs: dict[str, int],
                    lagna_sign: int,
                    profile: Optional[AspectProfile] = None) -> list[Aspect]:
    """
    Every drishti cast in the chart.

    `planet_houses` maps graha -> whole-sign house, `planet_signs` maps graha ->
    sidereal sign index. Each returned Aspect names the house and sign aspected
    and the grahas standing there, so planet-to-planet aspects fall out of the
    same pass rather than being computed a second way.
    """
    active = profile or DEFAULT_ASPECT_PROFILE
    occupants: dict[int, list[str]] = {}
    for planet, house in planet_houses.items():
        occupants.setdefault(house, []).append(planet)

    results: list[Aspect] = []
    for planet in ALL_GRAHAS:
        house = planet_houses.get(planet)
        if house is None:
            continue
        for distance in active.distances_for(planet):
            target_house = ((house + distance - 2) % 12) + 1
            target_sign = (lagna_sign + target_house - 1) % 12
            strength = active.strength_of(planet, distance)
            targets = tuple(sorted(
                p for p in occupants.get(target_house, []) if p != planet))
            results.append(Aspect(
                source=planet,
                to_house=target_house,
                to_sign=target_sign,
                aspect_type=_type_name(distance),
                distance=distance,
                full=strength >= 1.0,
                strength=strength,
                targets=targets,
            ))
    return results


def aspects_to_dicts(aspects: list[Aspect]) -> list[dict]:
    """JSON-shaped view, as specified in the Part 5 interface."""
    return [
        {
            "from": a.source,
            "to_house": a.to_house,
            "aspect_type": a.aspect_type,
            "full": a.full,
            "targets": list(a.targets),
        }
        for a in aspects
    ]
