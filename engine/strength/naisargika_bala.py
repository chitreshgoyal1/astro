"""
Naisargika Bala — natural strength (V1.4 Part 3)
--------------------------------------------------
BPHS 27.14, R. Santhanam translation (witness BPHS_27_SHADBALA):

    "Divide one Rupa (or 60 Virupas) by 7 and multiply the resultant product
     by 1 to 7 separately which will indicate the Natural Strength due to
     Saturn, Mars, Mercury, Jupiter, Venus, the Moon and the Sun,
     respectively."

The simplest of the six: a fixed constant per graha, independent of the chart.
It is the brightness order, Sun strongest.

The witness notes that although this appears between the Kala Bala verses, it
is an independent source of strength and not part of Kala Bala — which is why
it is a separate module rather than a Kala subcomponent.
"""

from __future__ import annotations

from .models import BalaComponent

WITNESS = ("BPHS_27_SHADBALA",)
PROFILE = "bphs_santhanam_ch27"

# Multiplier n in (60 / 7) * n, exactly as the witness states the order.
_RANK = {
    "Shani": 1, "Mangal": 2, "Budha": 3, "Guru": 4,
    "Shukra": 5, "Chandra": 6, "Surya": 7,
}

NAISARGIKA_VIRUPAS = {
    planet: (60.0 / 7.0) * rank for planet, rank in _RANK.items()
}


def naisargika_bala(planet: str) -> BalaComponent:
    """Natural strength in virupas. Constant for a given graha."""
    value = NAISARGIKA_VIRUPAS.get(planet)
    if value is None:
        return BalaComponent(
            name="naisargika_bala", value_virupa=0.0,
            calculation_profile=PROFILE, source_ref_ids=WITNESS,
            validation_status="UNVERIFIED",
            detail=f"{planet} is not among the seven (nodes are excluded)")
    return BalaComponent(
        name="naisargika_bala", value_virupa=value,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=f"(60 / 7) x {_RANK[planet]}")
