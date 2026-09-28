"""
Drik Bala — aspectual strength (V1.4 Part 8)
----------------------------------------------
BPHS 27.19, R. Santhanam translation (witness BPHS_27_SHADBALA):

    "Reduce one fourth of the Drishti Pinda if a planet has malefic aspects
     on it and add a fourth if it is aspected by a benefic. Super add the
     entire aspect of Mercury and Jupiter."

PART 8'S REQUIREMENT, HONOURED

    This module does NOT compute aspects. It consumes the aspect facts the
    feature layer already derived, through `ChartFeatures.aspects_received`.

    The separation the brief asks for is the one between

        ASPECT FACT            Saturn aspects the 7th house  (features layer)
        STRENGTH EFFECT        that costs the occupant virupas  (here)

    If this module re-derived drishti it would eventually disagree with the
    yoga engine about who aspects whom, which is precisely the failure the
    features/rules split was introduced to prevent.
"""

from __future__ import annotations

from typing import Optional

from .models import BalaComponent

WITNESS = ("BPHS_27_SHADBALA",)
PROFILE = "bphs_santhanam_ch27"

# A full drishti is worth 60 virupas of drishti pinda; the rule takes a
# quarter of that, so 15 virupas per aspecting graha.
QUARTER_PINDA = 15.0

BENEFIC_BONUS = ("Budha", "Guru")


def drik_bala(planet: str, features) -> BalaComponent:
    """
    Aspectual strength in virupas, positive or negative.

    Every aspect falling on the graha is counted once, signed by the
    aspecting graha's natural benefic or malefic character, with Mercury and
    Jupiter contributing the full pinda rather than a quarter.
    """
    target = features.planet(planet)
    if target is None:
        return BalaComponent(
            name="drik_bala", value_virupa=0.0,
            calculation_profile=PROFILE, source_ref_ids=WITNESS,
            validation_status="UNVERIFIED",
            detail=f"{planet} is not in the chart")

    total = 0.0
    parts: list[BalaComponent] = []

    for source in sorted({a.source for a in target.aspects_received}):
        aspecting = features.planet(source)
        if aspecting is None or source == planet:
            continue

        full = source in BENEFIC_BONUS
        magnitude = 60.0 if full else QUARTER_PINDA

        if aspecting.natural_benefic:
            value = magnitude
            kind = "benefic"
        elif aspecting.natural_malefic:
            value = -magnitude
            kind = "malefic"
        else:
            value = 0.0
            kind = "neutral"

        total += value
        parts.append(BalaComponent(
            name=f"drishti_from_{source}",
            value_virupa=value,
            calculation_profile=PROFILE,
            source_ref_ids=WITNESS,
            validation_status="IMPLEMENTATION_MATCHED",
            detail=f"{kind} drishti"
                   + (" (full pinda: Mercury/Jupiter)" if full else
                      " (quarter pinda)")))

    return BalaComponent(
        name="drik_bala", value_virupa=total,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=(f"{len(parts)} drishti(s) received"
                if parts else "no drishti received"),
        subcomponents=tuple(parts))
