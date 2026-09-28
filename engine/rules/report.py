"""
YOGA ANALYSIS report section (Part 14)
--------------------------------------
Renders rule results. For every combination that formed, the report shows why
it formed, what cancelled it if anything did, which modifiers set its strength
band, and the source it comes from.

Combinations that did not form are summarised rather than listed in full: the
catalog evaluates every kendra-trikona and dhana pair in both directions, so
the absent list is long and mostly uninformative. `show_absent=True` prints it
in full, including the clause that failed, which is what makes a negative
result auditable.

No narrative text is generated. Each entry states the classical condition and
stops.
"""

from __future__ import annotations

from collections import Counter

from .catalog import RULE_PROFILES
from .engine import YogaResult, YogaStatus

_WIDTH = 100
_RULE = "─"

_STATUS_MARK = {
    YogaStatus.PRESENT_AND_STRONG: "++",
    YogaStatus.PRESENT: " +",
    YogaStatus.PRESENT_BUT_WEAKENED: " ~",
    YogaStatus.PRESENT_BUT_CANCELLED: " x",
    YogaStatus.ABSENT: " ·",
}


def format_yoga_report(results: list[YogaResult],
                       profile: str,
                       show_absent: bool = False) -> str:
    """The YOGA ANALYSIS block."""
    lines: list[str] = []
    add = lines.append

    present = [r for r in results if r.present]
    absent = [r for r in results if not r.present]
    counts = Counter(r.status for r in results)

    add("")
    add("═" * _WIDTH)
    add("  YOGA ANALYSIS  (rule-driven — formation, cancellation and strength "
        "evaluated separately)")
    add("═" * _WIDTH)
    add(f"  Rule profile : {profile} — {RULE_PROFILES.get(profile, '')}")
    add(f"  Rules tested : {len(results)}")
    add(f"  Outcome      : "
        + ", ".join(
            f"{status.value} {counts[status]}"
            for status in (YogaStatus.PRESENT_AND_STRONG, YogaStatus.PRESENT,
                           YogaStatus.PRESENT_BUT_WEAKENED,
                           YogaStatus.PRESENT_BUT_CANCELLED, YogaStatus.ABSENT)
            if counts[status]))

    if not present:
        add("")
        add("  No combination in this profile formed in this chart.")
    else:
        add("")
        add("  COMBINATIONS FORMED")
        add("  " + _RULE * (_WIDTH - 2))

    for result in present:
        add("")
        add(f"  {_STATUS_MARK[result.status]} {result.name}")
        add(f"       status     : {result.status.value}")
        add(f"       category   : {result.category}")
        add(f"       source     : {result.source}  [{result.tradition}]")
        add(f"       rule id    : {result.id}")
        if result.variant_of:
            add(f"       variant of : {result.variant_of} — a different "
                f"authority's reading, not the same combination")
        add(f"       condition  : {result.explanation}")
        if result.planets:
            add(f"       grahas     : {', '.join(result.planets)}")
        if result.houses:
            add(f"       bhavas     : "
                f"{', '.join(str(h) for h in sorted(set(result.houses)))}")

        add("       matched    :")
        for clause in result.conditions_met:
            add(f"           ✓ {clause}")
        if result.conditions_failed:
            add("       not matched:")
            for clause in result.conditions_failed:
                add(f"           · {clause}")

        if result.cancellations_found:
            add("       CANCELLED BY:")
            for clause in result.cancellations_found:
                add(f"           ✗ {clause}")
        else:
            add("       cancellations: none apply")

        if result.engine_strength_score is not None:
            add(f"       engine score: "
                f"{round(result.engine_strength_score * 100)}/100 "
                f"({result.engine_strength_band})")
            add(f"       score type  : {result.score_type} — "
                f"classical_measure={result.classical_measure}. This is a "
                f"software ranking used to order findings within one chart; "
                f"no classical text scores yogas numerically, and the score "
                f"plays no part in whether the yoga is present.")
        if result.modifiers:
            add("       modifiers  :")
            for modifier in result.modifiers:
                add(f"           {modifier.describe()}")
        if result.notes:
            add(f"       note       : {result.notes}")

    # ── absent ───────────────────────────────────────────────────────────────
    add("")
    add(f"  COMBINATIONS NOT FORMED ({len(absent)})")
    add("  " + _RULE * (_WIDTH - 2))
    if show_absent:
        for result in absent:
            add(f"   · {result.name}")
            for clause in result.conditions_failed:
                add(f"       failed: {clause}")
    else:
        by_category: dict[str, list[str]] = {}
        for result in absent:
            by_category.setdefault(result.category, []).append(result.name)
        for category, names in sorted(by_category.items()):
            add(f"   {category:<14} {len(names)} rule(s)")
        add("")
        add("   Run with --show-absent-yogas for the failed clause of each.")

    add("")
    add("  ++ present and strong    + present    ~ present but weakened")
    add("  x  present but cancelled · absent")
    add("  engine_strength_score is a SOFTWARE HEURISTIC (0-100) used only to "
        "order findings")
    add("  within one chart. It is not a classical measure and never decides "
        "presence.")
    add("═" * _WIDTH)
    return "\n".join(lines)
