"""
House systems (V1.4 Part 14)
------------------------------
Each function returns the twelve bhava MADHYAS — the centres — in degrees.
Sandhis and spans are derived from them in profiles.py, so a new system only
has to say where its centres are.

THE MADHYA CONVENTION, STATED

    BHAVA_CHALIT_DESIGN.md §2 settled this: the Indian tradition
    predominantly treats the Lagna degree as the bhava MADHYA, the centre of
    the first bhava, with the sandhi falling midway between adjacent madhyas.
    That is what these functions return.

    A cusp-start convention would place the Lagna at the beginning of the
    first house instead. It is a different model, not a refinement, and is
    not implemented — a system that wanted it would be a separate entry here.

PROVENANCE

    None of these is source-validated. Sripati is named for the tradition it
    belongs to, but no witness has been located for it in this build, and the
    profile says UNVERIFIED accordingly.
"""

from __future__ import annotations

import math
from typing import Optional


def _normalise(degrees: float) -> float:
    return degrees % 360.0


def _arc(start: float, end: float) -> float:
    """Forward arc from start to end, 0-360."""
    return (end - start) % 360.0


def equal_from_lagna(ascendant: float,
                     midheaven: Optional[float] = None,
                     **_ignored) -> dict[int, float]:
    """
    Twelve equal bhavas of 30 degrees, centred on the Lagna degree.

    Always defined, at every latitude, and the only system here that cannot
    produce a degenerate quadrant. The Midheaven is ignored by construction —
    which is the trade: simplicity for the loss of the real meridian.
    """
    return {house: _normalise(ascendant + (house - 1) * 30.0)
            for house in range(1, 13)}


def porphyry(ascendant: float, midheaven: float, **_ignored
             ) -> dict[int, float]:
    """
    Trisect each ecliptic quadrant, taking the trisection points as the
    bhava MADHYAS.

    The four angles are exact; the intermediate bhavas are unequal and share
    the quadrant between them.
    """
    descendant = _normalise(ascendant + 180.0)
    imum_coeli = _normalise(midheaven + 180.0)

    madhyas = {1: _normalise(ascendant), 4: imum_coeli,
               7: descendant, 10: _normalise(midheaven)}

    for start_house, start, end in (
        (1, madhyas[1], madhyas[4]),
        (4, madhyas[4], madhyas[7]),
        (7, madhyas[7], madhyas[10]),
        (10, madhyas[10], madhyas[1]),
    ):
        third = _arc(start, end) / 3.0
        madhyas[start_house + 1] = _normalise(start + third)
        madhyas[start_house + 2] = _normalise(start + 2 * third)

    return {house: madhyas[house] for house in range(1, 13)}


def sripati(ascendant: float, midheaven: float, **_ignored
            ) -> dict[int, float]:
    """
    The classical Indian quadrant system.

    Sripati and Porphyry trisect the same quadrants; they differ in what the
    trisection points ARE. Porphyry treats them as house beginnings and
    Sripati as house centres.

    Because this engine models madhyas throughout, and Porphyry's own cusps
    become Sripati's madhyas, the two produce the same madhya set here. They
    are kept as separate named systems because the distinction is real —
    their SANDHIS differ, and a future profile that reports cusps rather than
    centres would need them apart.
    """
    return porphyry(ascendant, midheaven)


def placidus(ascendant: float, midheaven: float,
             latitude: Optional[float] = None,
             obliquity: float = 23.4392911, **_ignored) -> dict[int, float]:
    """
    Time-based division of the diurnal and nocturnal semi-arcs.

    UNDEFINED above the polar circles, and unstable approaching them, because
    a degree of the ecliptic that never rises has no semi-arc to divide. This
    raises rather than returning a number, matching the discipline
    engine/location.py applies to unresolvable birthplaces: a loud failure
    beats a confident wrong answer.
    """
    if latitude is None:
        raise ValueError("Placidus needs the geographic latitude")
    if abs(latitude) >= 90.0 - obliquity:
        raise ValueError(
            f"Placidus is undefined at latitude {latitude:.4f}°: above "
            f"{90.0 - obliquity:.2f}° some ecliptic degrees never rise, so "
            f"they have no semi-arc to divide. Use sripati or "
            f"equal_from_lagna at this latitude.")

    ramc = math.radians(_right_ascension(midheaven, obliquity))
    phi = math.radians(latitude)
    eps = math.radians(obliquity)

    madhyas = {1: _normalise(ascendant), 10: _normalise(midheaven),
               7: _normalise(ascendant + 180.0),
               4: _normalise(midheaven + 180.0)}

    for house, fraction, offset in ((11, 1 / 3, 0), (12, 2 / 3, 0),
                                    (2, 2 / 3, math.pi), (3, 1 / 3, math.pi)):
        target = ramc + offset + fraction * math.pi / 2 * (1 if offset == 0 else -1)
        longitude = _ecliptic_from_ra(math.degrees(target) % 360.0, eps, phi,
                                      fraction)
        madhyas[house] = _normalise(longitude)

    for house in (5, 6, 8, 9):
        madhyas[house] = _normalise(madhyas[(house + 5) % 12 + 1] + 180.0)

    return {house: madhyas[house] for house in range(1, 13)}


def _right_ascension(longitude: float, obliquity: float) -> float:
    lam = math.radians(longitude)
    eps = math.radians(obliquity)
    return math.degrees(math.atan2(math.cos(eps) * math.sin(lam),
                                   math.cos(lam))) % 360.0


def _ecliptic_from_ra(right_ascension: float, eps: float, phi: float,
                      fraction: float) -> float:
    """Iterative solution for the ecliptic longitude at a Placidus cusp."""
    ra = math.radians(right_ascension)
    longitude = math.degrees(math.atan2(math.sin(ra),
                                        math.cos(ra) * math.cos(eps)))
    for _ in range(12):
        lam = math.radians(longitude)
        declination = math.asin(math.sin(eps) * math.sin(lam))
        try:
            ascensional = math.asin(
                max(-1.0, min(1.0, math.tan(phi) * math.tan(declination))))
        except ValueError:
            break
        longitude = math.degrees(
            math.atan2(math.sin(ra + ascensional * fraction),
                       math.cos(ra + ascensional * fraction) * math.cos(eps)))
    return longitude


HOUSE_SYSTEMS = {
    "equal_from_lagna": equal_from_lagna,
    "sripati": sripati,
    "porphyry": porphyry,
    "placidus": placidus,
}
