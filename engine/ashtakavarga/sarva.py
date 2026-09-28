"""
Sarvashtakavarga — the combined chart (V1.4 Part 10)
------------------------------------------------------
The seven bhinna charts summed sign by sign. Each sign ends with between 0
and 56 bindus, and the whole sums to 337.

No interpretation. A high count is a high count.
"""

from __future__ import annotations

from .models import WITNESS, BhinnaAshtakavarga, Sarvashtakavarga


def compute_sarva(bhinna: dict[str, BhinnaAshtakavarga]) -> Sarvashtakavarga:
    """Sum the seven individual charts."""
    totals = {sign: 0 for sign in range(12)}
    for chart in bhinna.values():
        for sign, count in chart.bindus_by_sign.items():
            totals[sign] += count
    return Sarvashtakavarga(
        bindus_by_sign=totals,
        source_ref_ids=WITNESS,
        validation_status="TEXT_LOCATED",
    )


def sign_totals(sarva: Sarvashtakavarga) -> dict[int, int]:
    return dict(sorted(sarva.bindus_by_sign.items()))


def house_totals(sarva: Sarvashtakavarga, lagna_sign: int) -> dict[int, int]:
    """Bindus by house rather than by sign, counted from the Lagna."""
    return {house: sarva.bindus_in_house(house, lagna_sign)
            for house in range(1, 13)}
