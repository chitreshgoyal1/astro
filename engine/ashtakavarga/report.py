"""
ASHTAKAVARGA report section (V1.4 Part 22)
--------------------------------------------
Bindus, by sign and by house. Nothing else.

Part 10 forbids attaching predictions such as "high bindus mean success", and
the report honours that: it prints counts and says what a count is.
"""

from __future__ import annotations

from ..planets import RASHI_NAMES
from .models import AV_GRAHAS, AshtakavargaSet

_WIDTH = 100
_RULE = "─"


def format_ashtakavarga_report(av: AshtakavargaSet) -> str:
    lines: list[str] = []
    add = lines.append

    add("")
    add("═" * _WIDTH)
    add("  ASHTAKAVARGA  (calculated bindu counts — no interpretation)")
    add("═" * _WIDTH)
    add(f"  Methodology : {av.methodology_profile}")
    add("  Source      : BPHS ch.66 (R. Santhanam translation, "
        "witness BPHS_66_ASHTAKAVARGA)")
    add("  Verified    : the Sun's table verse by verse; the other six are "
        "located but")
    add("                their OCR is damaged, so verification is incomplete.")

    if not av.bhinna:
        add("")
        for warning in av.warnings:
            add(f"  ! {warning}")
        add("═" * _WIDTH)
        return "\n".join(lines)

    # ── bhinna, sign by sign ────────────────────────────────────────────────
    add("")
    add("  BHINNASHTAKAVARGA — bindus per sign")
    add("  " + _RULE * (_WIDTH - 2))
    header = f"  {'Graha':<9}"
    for sign in range(12):
        header += f"{RASHI_NAMES[sign][:3]:>5}"
        
    add(header + f"{'Total':>8}")
    for planet in AV_GRAHAS:
        chart = av.bhinna.get(planet)
        if chart is None:
            continue
        row = f"  {planet:<9}"
        for sign in range(12):
            row += f"{chart.bindus_in_sign(sign):>5}"
        add(row + f"{chart.total:>8}")

    # ── sarva ───────────────────────────────────────────────────────────────
    if av.sarva is not None:
        add("  " + _RULE * (_WIDTH - 2))
        row = f"  {'SARVA':<9}"
        for sign in range(12):
            row += f"{av.sarva.bindus_in_sign(sign):>5}"
        add(row + f"{av.sarva.total:>8}")

        add("")
        add("  SARVASHTAKAVARGA — bindus per house from the Lagna")
        add("  " + _RULE * (_WIDTH - 2))
        add("  " + "".join(f"{h:>6}" for h in range(1, 13)))
        add("  " + "".join(
            f"{av.sarva.bindus_in_house(h, av.lagna_sign):>6}"
            for h in range(1, 13)))

    if av.reductions:
        add("")
        add("  REDUCTIONS (not applied by default — see the note)")
        add("  " + _RULE * (_WIDTH - 2))
        for planet, data in av.reductions.items():
            add(f"    {planet:<9} original {data['original_total']:>4}  "
                f"after reduction {data['reduced_total']:>4}  "
                f"[{data['validation_status']}]")

    if av.warnings:
        add("")
        for warning in av.warnings:
            add(f"  ! {warning}")

    add("")
    add("  A bindu is a benefic point contributed by one reference graha. "
        "Each sign in a")
    add("  bhinna chart holds 0-8; each sign in the sarva holds 0-56. The "
        "totals are fixed")
    add("  by the tables (48, 49, 39, 54, 56, 52, 39; sarva 337) and are an "
        "arithmetic")
    add("  invariant, not a property of the chart.")
    add("  NO CLAIM is made here that more bindus are better or fewer worse.")
    add("═" * _WIDTH)
    return "\n".join(lines)
