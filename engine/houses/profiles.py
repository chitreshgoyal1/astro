"""
House-system profiles (V1.4 Parts 13, 14, 15)
-----------------------------------------------
Assembles a BhavaChart from a named system, and enforces the two rules that
keep the representations apart.

RULE 1 — LORDSHIP STAYS SIGN-BASED (Part 13)

    A bhava's lord is the lord of the rashi its MADHYA falls in. Where a
    bhava spans two rashis the second is recorded as `secondary_sign` and
    reported, never silently dropped.

    Nothing here touches a graha's sign, dignity, vargas or houses owned.
    Those are computed in engine/features/ from the zodiac and are not
    consulted, let alone modified, by this package.

RULE 2 — REFERENCE SPACE IS DECLARED, NOT ASSUMED (Part 15)

    `ReferenceSpace` names which representation a rule is evaluated in. The
    default for every existing yoga rule is RASHI, because that is what they
    were written against, and switching them silently would change a hundred
    unvalidated results at once.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from ..planets import RASHI_LORDS, RASHI_NAMES
from .models import BhavaChart, BhavaCusp, PlanetPlacement
from .systems import HOUSE_SYSTEMS

WHOLE_SIGN = "whole_sign"
DEFAULT_SYSTEM = WHOLE_SIGN


class ReferenceSpace(str, Enum):
    """
    Which house representation a rule is judged in (Part 15).

    RASHI is the default everywhere. A rule only moves off it when a witness
    establishes that it meant bhavas — which, as of V1.4, none has.
    """

    RASHI = "RASHI"
    BHAVA = "BHAVA"
    BOTH = "BOTH"
    CONFIGURABLE = "CONFIGURABLE"


@dataclass(frozen=True)
class HouseSystemProfile:
    """A named house system with its provenance."""

    id: str
    name: str
    system: str
    description: str
    tradition: str
    source_ref_ids: tuple[str, ...] = ()
    validation_status: str = "UNVERIFIED"
    needs_latitude: bool = False

    @property
    def is_whole_sign(self) -> bool:
        return self.system == WHOLE_SIGN


HOUSE_PROFILES: dict[str, HouseSystemProfile] = {
    WHOLE_SIGN: HouseSystemProfile(
        id=WHOLE_SIGN, name="Whole sign (Rashi)", system=WHOLE_SIGN,
        description=("The bhava is the rashi. The engine's default and the "
                     "basis of every existing rule."),
        tradition="Parashari",
        validation_status="UNVERIFIED"),
    "sripati": HouseSystemProfile(
        id="sripati", name="Sripati", system="sripati",
        description=("Each ecliptic quadrant trisected, the trisection "
                     "points taken as bhava madhyas. The angles are exact."),
        tradition="Sripati / Indian quadrant tradition",
        validation_status="UNVERIFIED"),
    "equal_from_lagna": HouseSystemProfile(
        id="equal_from_lagna", name="Equal from the Lagna",
        system="equal_from_lagna",
        description=("Twelve equal 30-degree bhavas centred on the Lagna "
                     "degree. Defined at every latitude."),
        tradition="Sama / equal-house usage",
        validation_status="UNVERIFIED"),
    "porphyry": HouseSystemProfile(
        id="porphyry", name="Porphyry", system="porphyry",
        description=("Quadrant trisection. Shares Sripati's madhyas in this "
                     "engine; retained as a distinct name because the "
                     "traditions differ over cusps."),
        tradition="Porphyry (Hellenistic)",
        validation_status="UNVERIFIED"),
    "placidus": HouseSystemProfile(
        id="placidus", name="Placidus", system="placidus",
        description=("Semi-arc division. Undefined above the polar circles "
                     "and raises there rather than guessing."),
        tradition="Placidus (Western)",
        validation_status="UNVERIFIED", needs_latitude=True),
}


def _midpoint(first: float, second: float) -> float:
    """Midpoint on the forward arc from first to second."""
    return (first + ((second - first) % 360.0) / 2.0) % 360.0


def build_bhava_chart(chart, system: str = "sripati",
                      latitude: Optional[float] = None,
                      sandhi_envelope_deg: float = 1.0) -> BhavaChart:
    """
    Build a bhava chart beside the rashi chart.

    `chart` is a JyotishChart and is READ ONLY — nothing here writes to it.
    `sandhi_envelope_deg` flags grahas lying within that many degrees of a
    junction, where the bhava assignment is sensitive to birth time.
    """
    profile = HOUSE_PROFILES.get(system)
    if profile is None:
        raise ValueError(
            f"Unknown house system '{system}'. "
            f"Available: {', '.join(sorted(HOUSE_PROFILES))}")

    warnings: list[str] = []
    ascendant = chart.lagna.longitude
    midheaven = getattr(chart, "midheaven", None)

    if profile.is_whole_sign:
        return _whole_sign_chart(chart, profile)

    if midheaven is None:
        midheaven = (ascendant + 270.0) % 360.0
        warnings.append(
            "No Midheaven available, so the 10th was taken 90 degrees from "
            "the Ascendant. That is exact only at the equator or the "
            "equinoxes, and the intermediate bhavas inherit the error.")

    builder: Callable = HOUSE_SYSTEMS[profile.system]
    madhyas = builder(ascendant=ascendant, midheaven=midheaven,
                      latitude=latitude)

    cusps: dict[int, BhavaCusp] = {}
    for house in range(1, 13):
        madhya = madhyas[house]
        previous = madhyas[12 if house == 1 else house - 1]
        following = madhyas[1 if house == 12 else house + 1]
        start = _midpoint(previous, madhya)
        end = _midpoint(madhya, following)

        sign = int(madhya // 30) % 12
        start_sign = int(start // 30) % 12
        secondary = start_sign if start_sign != sign else None

        cusps[house] = BhavaCusp(
            house=house, madhya=madhya, start=start, end=end,
            sign=sign, sign_lord=RASHI_LORDS[RASHI_NAMES[sign]],
            secondary_sign=secondary)

    placements: dict[str, PlanetPlacement] = {}
    near_sandhi: list[str] = []
    lagna_sign = chart.lagna.rashi_index

    for name, position in chart.planets.items():
        bhava = _house_containing(cusps, position.longitude)
        rashi_house = ((position.rashi_index - lagna_sign) % 12) + 1
        placements[name] = PlanetPlacement(
            planet=name,
            longitude=position.longitude,
            rashi_sign=position.rashi_index,
            rashi_house=rashi_house,
            bhava_house=bhava,
        )
        distance = _distance_to_nearest_sandhi(cusps, position.longitude)
        if distance <= sandhi_envelope_deg:
            near_sandhi.append(
                f"{name} is {distance * 60:.1f}' from a sandhi; its bhava is "
                f"sensitive to the birth time")

    return BhavaChart(
        system=profile.system, profile_id=profile.id, cusps=cusps,
        placements=placements, near_sandhi=near_sandhi,
        source_ref_ids=profile.source_ref_ids,
        validation_status=profile.validation_status, warnings=warnings)


def _whole_sign_chart(chart, profile: HouseSystemProfile) -> BhavaChart:
    """
    The degenerate case: bhava equals rashi, so nothing ever moves.

    Built rather than special-cased away, so a caller selecting whole-sign
    gets the same object shape and can compare systems uniformly.
    """
    lagna_sign = chart.lagna.rashi_index
    cusps = {}
    for house in range(1, 13):
        sign = (lagna_sign + house - 1) % 12
        cusps[house] = BhavaCusp(
            house=house, madhya=(sign * 30.0 + 15.0) % 360.0,
            start=sign * 30.0, end=(sign * 30.0 + 30.0) % 360.0,
            sign=sign, sign_lord=RASHI_LORDS[RASHI_NAMES[sign]])

    placements = {}
    for name, position in chart.planets.items():
        house = ((position.rashi_index - lagna_sign) % 12) + 1
        placements[name] = PlanetPlacement(
            planet=name, longitude=position.longitude,
            rashi_sign=position.rashi_index,
            rashi_house=house, bhava_house=house)

    return BhavaChart(
        system=WHOLE_SIGN, profile_id=profile.id, cusps=cusps,
        placements=placements, near_sandhi=[],
        validation_status=profile.validation_status,
        warnings=["Whole sign: the bhava is the rashi, so nothing moves."])


def _house_containing(cusps: dict[int, BhavaCusp], longitude: float) -> int:
    for house, cusp in cusps.items():
        if cusp.contains(longitude):
            return house
    # Unreachable when the cusps tile the circle, which they do by
    # construction; kept so a future system with a gap fails visibly.
    raise ValueError(
        f"longitude {longitude} fell outside every bhava — the cusps do not "
        f"tile the circle")


def _distance_to_nearest_sandhi(cusps: dict[int, BhavaCusp],
                                longitude: float) -> float:
    best = 360.0
    for cusp in cusps.values():
        for edge in (cusp.start, cusp.end):
            gap = abs((longitude - edge + 180.0) % 360.0 - 180.0)
            best = min(best, gap)
    return best
