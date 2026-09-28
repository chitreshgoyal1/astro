"""
RASHI VS BHAVA report section (V1.4 Part 22)
----------------------------------------------
Shows which grahas move and which do not. Facts only.
"""

from __future__ import annotations

from ..planets import RASHI_NAMES
from .models import BhavaChart

_WIDTH = 100
_RULE = "─"


def format_bhava_report(bhava: BhavaChart) -> str:
    lines: list[str] = []
    add = lines.append

    add("")
    add("═" * _WIDTH)
    add("  RASHI VS BHAVA PLACEMENTS  (two representations, held apart)")
    add("═" * _WIDTH)
    add(f"  House system : {bhava.system}  (profile {bhava.profile_id})")
    add(f"  Provenance   : {bhava.validation_status}"
        + (f"  refs {', '.join(bhava.source_ref_ids)}"
           if bhava.source_ref_ids else "  no witness located"))
    add("  Convention   : the Lagna degree is the bhava MADHYA; sandhis fall "
        "midway")
    add("                 between adjacent madhyas.")

    if bhava.warnings:
        add("")
        for warning in bhava.warnings:
            add(f"  ! {warning}")

    add("")
    add("  BHAVA CUSPS")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'House':<7}{'Madhya':>11}{'Start':>11}{'End':>11}{'Span':>9}"
        f"  {'Rashi':<12}{'Lord':<9}Spans two rashis?")
    for house in range(1, 13):
        cusp = bhava.cusps.get(house)
        if cusp is None:
            continue
        second = (RASHI_NAMES[cusp.secondary_sign]
                  if cusp.secondary_sign is not None else "—")
        add(f"  {house:<7}{cusp.madhya:>11.4f}{cusp.start:>11.4f}"
            f"{cusp.end:>11.4f}{cusp.span:>9.4f}  "
            f"{RASHI_NAMES[cusp.sign]:<12}{cusp.sign_lord:<9}{second}")

    add("")
    add("  PLACEMENTS")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Rashi':<12}{'Sign lord':<10}{'Rashi house':>12}"
        f"{'Bhava house':>13}   Moved?")
    for name, placement in bhava.placements.items():
        add(f"  {name:<9}{placement.rashi_sign_name:<12}"
            f"{placement.rashi_sign_lord:<10}{placement.rashi_house:>12}"
            f"{placement.bhava_house:>13}   "
            f"{'MOVED' if placement.moved else '—'}")

    add("")
    if bhava.moved_planets:
        add(f"  {len(bhava.moved_planets)} graha(s) fall in a different "
            f"bhava from their rashi house:")
        for divergence in bhava.divergences:
            add(f"    {divergence}")
    else:
        add("  No graha falls in a different bhava from its rashi house.")

    if bhava.near_sandhi:
        add("")
        add("  NEAR A SANDHI — bhava sensitive to the birth time")
        add("  " + _RULE * (_WIDTH - 2))
        for note in bhava.near_sandhi:
            add(f"    {note}")

    add("")
    add("  Sign, sign lord, dignity, vargas and houses owned are properties "
        "of the ZODIAC.")
    add("  They are unchanged by the house system. Only the bhava column "
        "above depends on it.")
    add("  Yoga rules are evaluated in RASHI space unless a rule declares "
        "otherwise.")
    add("═" * _WIDTH)
    return "\n".join(lines)
