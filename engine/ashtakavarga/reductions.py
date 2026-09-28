"""
Ashtakavarga reductions (V1.4 Parts 10, 11)
---------------------------------------------
Trikona and Ekadhipatya sodhana — the two classical reductions applied before
Pinda Sadhana.

WHY THESE ARE PROFILED RATHER THAN ASSUMED

    BPHS ch. 66 describes both, and the witness's OCR of those verses is
    among the damaged parts. More importantly, traditions differ over the
    exact treatment of several cases — notably what happens when one of the
    trine signs holds zero bindus, and how Ekadhipatya handles a lord owning
    one occupied and one empty sign.

    Part 11 is explicit that differing traditions must be separate profiles
    and must not be averaged. So the reductions are implemented under a named
    profile, marked UNVERIFIED, and are NOT applied by default. A caller that
    wants them asks for them and gets told what they rest on.
"""

from __future__ import annotations

from ..planets import OWN_SIGN, RASHI_LORDS, RASHI_NAMES
from .models import BhinnaAshtakavarga

REDUCTION_PROFILE = "bphs_ch66_unverified"

# Trines: each sign belongs to a group of three, 120 degrees apart.
TRINE_GROUPS = tuple(
    tuple((start + offset) % 12 for offset in (0, 4, 8))
    for start in range(4)
)


def trikona_sodhana(chart: BhinnaAshtakavarga) -> dict[int, int]:
    """
    Trine reduction.

    Within each group of three trine signs, subtract the smallest count from
    all three; where the smallest is zero, the group is set to zero.

    UNVERIFIED. The zero-handling in particular is a point on which sources
    are read differently, and no witness for it has been checked.
    """
    reduced = dict(chart.bindus_by_sign)
    for group in TRINE_GROUPS:
        values = [reduced.get(sign, 0) for sign in group]
        smallest = min(values)
        for sign in group:
            reduced[sign] = 0 if smallest == 0 else reduced[sign] - smallest
    return reduced


def ekadhipatya_sodhana(bindus: dict[int, int],
                        occupied_signs: set[int]) -> dict[int, int]:
    """
    Single-lordship reduction.

    Where one graha owns two signs, the pair is reduced according to which of
    them is occupied. The Sun and Moon own one sign each and are unaffected.

    UNVERIFIED, for the same reasons as above.
    """
    reduced = dict(bindus)
    for planet, signs in OWN_SIGN.items():
        if len(signs) != 2:
            continue
        first, second = signs
        first_occupied = first in occupied_signs
        second_occupied = second in occupied_signs

        if first_occupied and second_occupied:
            continue                      # both occupied: no reduction
        if not first_occupied and not second_occupied:
            smallest = min(reduced.get(first, 0), reduced.get(second, 0))
            reduced[first] = reduced[second] = smallest
        elif first_occupied:
            reduced[second] = 0
        else:
            reduced[first] = 0
    return reduced


def apply_reductions(chart: BhinnaAshtakavarga,
                     occupied_signs: set[int]) -> dict:
    """
    Both reductions in sequence, with their provenance attached.

    Returns the intermediate as well as the final figures, so a caller can
    see what each step did rather than only the end result.
    """
    after_trikona = trikona_sodhana(chart)
    after_ekadhipatya = ekadhipatya_sodhana(after_trikona, occupied_signs)
    return {
        "planet": chart.planet,
        "profile": REDUCTION_PROFILE,
        "validation_status": "UNVERIFIED",
        "note": (
            "Trikona and Ekadhipatya sodhana are implemented but NOT "
            "source-verified: the witness's OCR of these verses is damaged "
            "and traditions differ on the zero and single-occupancy cases. "
            "Not applied by default."),
        "original": dict(sorted(chart.bindus_by_sign.items())),
        "after_trikona": dict(sorted(after_trikona.items())),
        "after_ekadhipatya": dict(sorted(after_ekadhipatya.items())),
        "original_total": sum(chart.bindus_by_sign.values()),
        "reduced_total": sum(after_ekadhipatya.values()),
    }
