"""
Bhinnashtakavarga — the individual charts (V1.4 Part 10)
----------------------------------------------------------
For one graha, count a bindu in every sign that is a benefic place counted
from each of the eight reference points.

    For each contributor C (seven grahas and the Lagna):
        for each house h in TABLE[graha][C]:
            the sign at (sign_of(C) + h - 1) gets one bindu

Deterministic, with no interpretation attached. A sign ends with between 0
and 8 bindus, and the whole chart sums to the graha's classical total.
"""

from __future__ import annotations

from .models import (
    AV_GRAHAS, BINDU_TABLES, CONTRIBUTORS, WITNESS, BhinnaAshtakavarga,
)


def compute_bhinna(planet: str, reference_signs: dict[str, int]
                   ) -> BhinnaAshtakavarga:
    """
    One graha's ashtakavarga.

    `reference_signs` maps each of the eight contributors to its sidereal
    sign index, the Lagna included.
    """
    if planet not in BINDU_TABLES:
        raise ValueError(
            f"No ashtakavarga table for '{planet}'. "
            f"Available: {', '.join(AV_GRAHAS)}")

    table = BINDU_TABLES[planet]
    bindus = {sign: 0 for sign in range(12)}
    contributions: dict[str, tuple[int, ...]] = {}

    for contributor in CONTRIBUTORS:
        base = reference_signs.get(contributor)
        if base is None:
            continue
        signs = []
        for house in table[contributor]:
            sign = (base + house - 1) % 12
            bindus[sign] += 1
            signs.append(sign)
        contributions[contributor] = tuple(sorted(signs))

    return BhinnaAshtakavarga(
        planet=planet,
        bindus_by_sign=bindus,
        contributions=contributions,
        source_ref_ids=WITNESS,
        validation_status="TEXT_LOCATED",
    )


def compute_all_bhinna(reference_signs: dict[str, int]
                       ) -> dict[str, BhinnaAshtakavarga]:
    """Every graha's ashtakavarga."""
    return {planet: compute_bhinna(planet, reference_signs)
            for planet in AV_GRAHAS}


def reference_signs_from_chart(chart) -> dict[str, int]:
    """
    The eight reference points from a JyotishChart.

    Rahu and Ketu are not contributors in the classical scheme and are
    excluded; the Lagna is, and is taken from its sidereal sign.
    """
    signs = {name: position.rashi_index
             for name, position in chart.planets.items()
             if name in BINDU_TABLES}
    signs["Lagna"] = chart.lagna.rashi_index
    return signs
