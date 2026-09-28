"""
Ashtakavarga (V1.4)
---------------------
    av = compute_ashtakavarga(chart)
    av.sarva.bindus_in_house(7, av.lagna_sign)
    av.bhinna["Shani"].bindus_in_sign(9)

Deterministic bindu counting, with no interpretation attached. Source: BPHS
ch.66 in the R. Santhanam translation; the Sun's table verified verse by
verse, the rest located but not yet checked.
"""

from __future__ import annotations

from typing import Optional

from .bhinna import compute_all_bhinna, compute_bhinna, reference_signs_from_chart
from .models import (
    AV_GRAHAS, BINDU_TABLES, CLASSICAL_TOTALS, CONTRIBUTORS, SARVA_TOTAL,
    VERIFIED_AGAINST_WITNESS, AshtakavargaSet, BhinnaAshtakavarga,
    Sarvashtakavarga,
)
from .reductions import (
    REDUCTION_PROFILE, apply_reductions, ekadhipatya_sodhana, trikona_sodhana,
)
from .report import format_ashtakavarga_report
from .sarva import compute_sarva, house_totals, sign_totals


def compute_ashtakavarga(chart, include_reductions: bool = False
                         ) -> AshtakavargaSet:
    """
    Every ashtakavarga for a chart.

    `include_reductions` is off by default: the reductions are implemented
    but UNVERIFIED, and applying an unverified transform silently would be
    the opposite of what this engine is for.
    """
    references = reference_signs_from_chart(chart)
    warnings: list[str] = []

    missing = [c for c in CONTRIBUTORS if c not in references]
    if missing:
        warnings.append(
            "Missing reference points: " + ", ".join(missing)
            + ". Their contributions are omitted, so the totals will fall "
              "below the classical figures.")

    bhinna = compute_all_bhinna(references)
    sarva = compute_sarva(bhinna)

    reductions = {}
    if include_reductions:
        occupied = {position.rashi_index
                    for name, position in chart.planets.items()
                    if name in BINDU_TABLES}
        reductions = {planet: apply_reductions(chart_av, occupied)
                      for planet, chart_av in bhinna.items()}
        warnings.append(
            "Reductions were applied on request. They are UNVERIFIED: the "
            "witness's OCR of those verses is damaged and traditions differ.")

    return AshtakavargaSet(
        bhinna=bhinna,
        sarva=sarva,
        lagna_sign=chart.lagna.rashi_index,
        reductions=reductions,
        warnings=warnings,
    )


__all__ = [
    "AV_GRAHAS", "BINDU_TABLES", "CLASSICAL_TOTALS", "CONTRIBUTORS",
    "REDUCTION_PROFILE", "SARVA_TOTAL", "VERIFIED_AGAINST_WITNESS",
    "AshtakavargaSet", "BhinnaAshtakavarga", "Sarvashtakavarga",
    "apply_reductions", "compute_all_bhinna", "compute_ashtakavarga",
    "compute_bhinna", "compute_sarva", "ekadhipatya_sodhana",
    "format_ashtakavarga_report", "house_totals", "reference_signs_from_chart",
    "sign_totals", "trikona_sodhana",
]
