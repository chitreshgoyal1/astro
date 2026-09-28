"""
PLANETARY STRENGTH report section (V1.4 Part 22)
--------------------------------------------------
Component values and totals. No interpretation: a graha either meets its
classical requirement or it does not, and what that means for the native is
not decided here.
"""

from __future__ import annotations

from .models import ShadbalaSet

_WIDTH = 100
_RULE = "─"


def format_shadbala_report(shadbala: ShadbalaSet,
                           show_subcomponents: bool = False) -> str:
    lines: list[str] = []
    add = lines.append

    add("")
    add("═" * _WIDTH)
    add("  PLANETARY STRENGTH — SHADBALA  (calculated; no interpretation)")
    add("═" * _WIDTH)
    add(f"  Methodology : {shadbala.methodology_profile}")
    add("  Source      : BPHS ch.27 (R. Santhanam translation, "
        "witness BPHS_27_SHADBALA)")
    add(f"  Provenance  : {shadbala.validation_status} — inherited from the "
        f"weakest component")
    add("  Units       : virupa (1/60 rupa). Requirements are BPHS 27.32-33.")

    if not shadbala.results:
        add("")
        for warning in shadbala.warnings:
            add(f"  ! {warning}")
        add("═" * _WIDTH)
        return "\n".join(lines)

    if shadbala.warnings:
        add("")
        for warning in shadbala.warnings:
            add(f"  ! {warning}")

    add("")
    add("  COMPONENTS (virupas)")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Sthana':>9}{'Dig':>9}{'Kala':>9}{'Chesta':>9}"
        f"{'Naisarg':>9}{'Drik':>9}{'Total':>10}{'Req':>7}{'Ratio':>8}  Meets?")
    for result in shadbala.ranked():
        add(f"  {result.planet:<9}"
            f"{result.sthana_bala.value_virupa:>9.2f}"
            f"{result.dig_bala.value_virupa:>9.2f}"
            f"{result.kala_bala.value_virupa:>9.2f}"
            f"{result.chesta_bala.value_virupa:>9.2f}"
            f"{result.naisargika_bala.value_virupa:>9.2f}"
            f"{result.drik_bala.value_virupa:>9.2f}"
            f"{result.total_virupa:>10.2f}"
            f"{result.required_virupa:>7.0f}"
            f"{result.ratio:>8.3f}  {'yes' if result.meets_requirement else 'no'}")

    add("")
    add("  TOTALS IN RUPAS")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Total rupa':>12}{'Required':>11}{'Approximation?':>17}"
        f"  Notes")
    for result in shadbala.ranked():
        add(f"  {result.planet:<9}{result.total_rupa:>12.4f}"
            f"{result.required_rupa:>11.2f}"
            f"{('yes' if result.has_approximation else 'no'):>17}"
            f"  {'; '.join(result.notes) if result.notes else '—'}")

    if show_subcomponents:
        for result in shadbala.ranked():
            add("")
            add(f"  {result.planet} — subcomponents")
            add("  " + _RULE * (_WIDTH - 2))
            for component in result.components:
                add(f"    {component.name:<28}{component.value_virupa:>9.3f}"
                    f"   {component.detail}")
                for part in component.subcomponents:
                    flag = " *" if part.is_approximation else ""
                    add(f"      {part.name:<26}{part.value_virupa:>9.3f}{flag}"
                        f"   {part.detail}")

    add("")
    add("  * marks a value resting on a declared approximation — see the "
        "snapshot for the note.")
    add("  Shadbala is a calculated quantity, not a verdict. 'Meets' means the "
        "total reaches")
    add("  the requirement BPHS states for that graha; it says nothing about "
        "outcomes.")
    add("═" * _WIDTH)
    return "\n".join(lines)
