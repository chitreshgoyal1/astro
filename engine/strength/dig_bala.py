"""
Dig Bala — directional strength (V1.4 Part 5)
----------------------------------------------
BPHS 27.7-7.5, R. Santhanam translation (witness BPHS_27_SHADBALA):

    "Deduct the 4th house from the longitudes of Sun and Mars; the 7th house
     from that of Jupiter and Mercury; the 10th house from that of Venus and
     the Moon; and lastly the ascendant from that of Saturn. If the sum is
     above 180 degrees deduct the sum from 360. The sum arrived in either way
     be divided by 3."

So each graha has a point of zero directional strength — the cusp opposite
its strongest direction — and gains linearly with angular distance from it,
reaching 60 virupas (one rupa) at the strong point itself.

    Sun, Mars           strongest on the 10th, weakest on the 4th
    Jupiter, Mercury    strongest on the 1st, weakest on the 7th
    Venus, Moon         strongest on the 4th, weakest on the 10th
    Saturn              strongest on the 7th, weakest on the 1st

WHICH CUSP CONVENTION IS USED — stated explicitly, per Part 5.

    The witness says "house" and "cusp", and under a quadrant house system
    those are the bhava madhyas. This engine's default house system is
    WHOLE SIGN, which has no madhya distinct from the sign.

    The implementation therefore takes the reference points from the ANGLES
    themselves: the Ascendant longitude for the 1st, the Midheaven for the
    10th, and their opposites for the 7th and 4th. That is the quadrant
    reading, and it is independent of the whole-sign house assignment — which
    matters, because deriving it from whole-sign house boundaries would make
    Dig Bala jump discontinuously at sign changes.

    When a Bhava chart is supplied (V1.4 Part 12), its madhyas are used
    instead and `calculation_profile` says so.
"""

from __future__ import annotations

from typing import Optional

from .models import BalaComponent

WITNESS = ("BPHS_27_SHADBALA",)

# graha -> house number of its STRONGEST direction. The zero point is the
# opposite cusp, 180 degrees away.
STRONGEST_HOUSE = {
    "Surya": 10, "Mangal": 10,
    "Guru": 1, "Budha": 1,
    "Shukra": 4, "Chandra": 4,
    "Shani": 7,
}


def _fold(degrees: float) -> float:
    degrees %= 360.0
    return 360.0 - degrees if degrees > 180.0 else degrees


def angle_longitudes(ascendant: float,
                     midheaven: Optional[float] = None) -> dict[int, float]:
    """
    Longitudes of the four angles.

    With no Midheaven supplied the chart is treated as whole-sign-equal and
    the 10th is taken 90 degrees from the Ascendant. That is an APPROXIMATION
    — the true Midheaven is only 90 degrees from the Ascendant at the equator
    or at the equinoxes — and any component built on it is flagged.
    """
    if midheaven is None:
        midheaven = (ascendant + 270.0) % 360.0
    return {
        1: ascendant % 360.0,
        4: (midheaven + 180.0) % 360.0,
        7: (ascendant + 180.0) % 360.0,
        10: midheaven % 360.0,
    }


def dig_bala(planet: str, longitude: float, ascendant: float,
             midheaven: Optional[float] = None,
             bhava_madhyas: Optional[dict[int, float]] = None
             ) -> BalaComponent:
    """
    Directional strength in virupas, 0 to 60.

    `bhava_madhyas` overrides the angles when a Bhava chart is available, so
    the quadrant convention is explicit in the output rather than assumed.
    """
    strongest = STRONGEST_HOUSE.get(planet)
    if strongest is None:
        return BalaComponent(
            name="dig_bala", value_virupa=0.0,
            calculation_profile="bphs_santhanam_ch27",
            source_ref_ids=WITNESS, validation_status="UNVERIFIED",
            detail=f"{planet} has no assigned direction (nodes are excluded)")

    weakest = ((strongest + 6 - 1) % 12) + 1

    if bhava_madhyas:
        reference = bhava_madhyas.get(weakest)
        profile = "bphs_santhanam_ch27/bhava_madhya"
        approximate = False
        note = ""
    else:
        angles = angle_longitudes(ascendant, midheaven)
        reference = angles.get(weakest)
        profile = ("bphs_santhanam_ch27/angles"
                   if midheaven is not None
                   else "bphs_santhanam_ch27/angles_equal_approx")
        approximate = midheaven is None
        note = ("Midheaven not supplied; the 10th was taken 90 degrees from "
                "the Ascendant, which is exact only at the equator or the "
                "equinoxes." if approximate else "")

    if reference is None:
        return BalaComponent(
            name="dig_bala", value_virupa=0.0,
            calculation_profile=profile, source_ref_ids=WITNESS,
            validation_status="UNVERIFIED",
            detail=f"no reference cusp available for house {weakest}")

    arc = _fold(longitude - reference)
    return BalaComponent(
        name="dig_bala",
        value_virupa=arc / 3.0,
        calculation_profile=profile,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=(f"{arc:.4f}° from the {weakest}th cusp at "
                f"{reference:.4f}°, divided by 3 "
                f"(strongest on the {strongest}th)"),
        is_approximation=approximate,
        approximation_note=note,
    )
