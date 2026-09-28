"""
Chesta Bala — motional strength (V1.4 Part 7)
-----------------------------------------------
BPHS 27.18, R. Santhanam translation (witness BPHS_27_SHADBALA):

    "The Sun's Cheshta Bala will correspond to his Ayana Bala. The Moon's
     Paksha Bala will itself be her Cheshta Bala."

For the five tara grahas the strength follows the graha's motional STATE —
retrograde, stationary, slow, fast — which is exactly the information the
ephemeris already derives.

PART 7'S REQUIREMENT, HONOURED

    Retrogression is NOT inferred from sign movement and NOT read from a
    table of dates. It comes from `PlanetPosition.speed`, which
    engine/ephemeris.py computes as a central difference of the actual
    longitude, and from `is_stationary`, which is set when the measured speed
    falls below the engine's own resolution.

    That last point matters for the stationary case. The engine declines to
    call a direction when |speed| < 0.005 deg/day, because below that its own
    error envelope cannot resolve it. Chesta Bala therefore has a genuine
    "cannot tell" state, and it reports it rather than rounding to direct.
"""

from __future__ import annotations

from typing import Optional

from .models import BalaComponent

WITNESS = ("BPHS_27_SHADBALA",)
PROFILE = "bphs_santhanam_ch27"

# The classical eight-fold motional states (cheshta) and their virupas.
# Vakra (retrograde) is strongest; vikala (stationary) next.
CHESTA_VIRUPAS = {
    "vakra": 60.0,          # retrograde
    "anuvakra": 30.0,       # retrograde into the previous sign
    "vikala": 15.0,         # stationary
    "manda": 15.0,          # slow
    "mandatara": 30.0,      # very slow
    "sama": 30.0,           # mean speed
    "chara": 30.0,          # fast
    "atichara": 45.0,       # very fast
}

# Mean daily motion in degrees, used only to classify fast against slow.
MEAN_DAILY_MOTION = {
    "Mangal": 0.524, "Budha": 1.383, "Guru": 0.083,
    "Shukra": 1.202, "Shani": 0.034,
}

TARA_GRAHAS = tuple(MEAN_DAILY_MOTION)


def motional_state(planet: str, speed: float, stationary: bool) -> str:
    """
    Classify a graha's motion from its MEASURED speed.

    `stationary` comes from the ephemeris and means the engine cannot resolve
    the direction, not that the graha is classically at a station. The two
    usually coincide, and where they do not, the engine's limit is the honest
    thing to report.
    """
    if stationary:
        return "vikala"
    if speed < 0:
        return "vakra"
    mean = MEAN_DAILY_MOTION.get(planet)
    if mean is None:
        return "sama"
    ratio = speed / mean
    if ratio > 1.5:
        return "atichara"
    if ratio > 1.05:
        return "chara"
    if ratio < 0.5:
        return "mandatara"
    if ratio < 0.95:
        return "manda"
    return "sama"


def chesta_bala(planet: str, speed: float, stationary: bool,
                ayana_bala: Optional[BalaComponent] = None,
                paksha_bala: Optional[BalaComponent] = None
                ) -> BalaComponent:
    """
    Motional strength in virupas.

    The Sun and Moon take their values from components already computed, per
    the witness — they are not recomputed here, so the two can never disagree.
    """
    if planet == "Surya":
        value = ayana_bala.value_virupa if ayana_bala else 0.0
        return BalaComponent(
            name="chesta_bala", value_virupa=value,
            calculation_profile=PROFILE, source_ref_ids=WITNESS,
            validation_status="IMPLEMENTATION_MATCHED",
            detail="equal to the Sun's ayana bala, per BPHS 27.18")

    if planet == "Chandra":
        value = paksha_bala.value_virupa if paksha_bala else 0.0
        return BalaComponent(
            name="chesta_bala", value_virupa=value,
            calculation_profile=PROFILE, source_ref_ids=WITNESS,
            validation_status="IMPLEMENTATION_MATCHED",
            detail="equal to the Moon's paksha bala, per BPHS 27.18")

    state = motional_state(planet, speed, stationary)
    detail = (f"speed {speed:+.5f}°/day; state '{state}'")
    if state == "vikala":
        detail += (" — the engine cannot resolve the direction at this speed, "
                   "so the stationary value is used rather than a guess")

    return BalaComponent(
        name="chesta_bala",
        value_virupa=CHESTA_VIRUPAS[state],
        calculation_profile=PROFILE + "/eightfold_cheshta",
        source_ref_ids=WITNESS,
        validation_status="RULE_INTERPRETATION_MAPPED",
        detail=detail,
        approximation_note=(
            "The eight-fold cheshta classification and its virupa values are "
            "the standard reading; the witness describes the states but the "
            "thresholds between chara, sama and manda are not numerically "
            "fixed by it."),
    )
