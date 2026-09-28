"""
VIMSHOTTARI DASHA report section
--------------------------------
Renders the period hierarchy. Facts only: a period is a span of time with a
lord, and no statement is made about what it brings.
"""

from __future__ import annotations

import datetime
from typing import Optional

from .models import ENGLISH_NAME
from .vimshottari import VimshottariDasha

_WIDTH = 100
_RULE = "─"


def _date(moment: datetime.datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M")


def _years(days: float) -> str:
    return f"{days / 365.25:.2f}y"


def format_dasha_report(dasha: VimshottariDasha,
                        today: Optional[datetime.datetime] = None,
                        antardasha_for_current: bool = True,
                        show_all_antardashas: bool = False) -> str:
    """The VIMSHOTTARI DASHA block."""
    lines: list[str] = []
    add = lines.append
    balance = dasha.balance_summary()

    add("")
    add("═" * _WIDTH)
    add("  VIMSHOTTARI DASHA  (calculated timing — no interpretation)")
    add("═" * _WIDTH)
    add(f"  Convention   : {dasha.years.name} year = "
        f"{float(dasha.years.days)} days — {dasha.years.description}")
    add(f"  Source       : BPHS ch.46; 120-year cycle, nine lords")
    add(f"  Moon         : {dasha.moon_longitude:.6f}° sidereal, "
        f"nakshatra index {dasha.nakshatra_index}")
    add(f"  Birth lord   : {balance['birth_dasha_lord']} "
        f"({ENGLISH_NAME[balance['birth_dasha_lord']]})")
    add(f"  Elapsed      : {balance['elapsed_fraction'] * 100:.4f}% of the "
        f"nakshatra, {balance['elapsed_days']:.2f} days")
    add(f"  Balance      : {balance['balance_days']:.2f} days "
        f"({balance['balance_years']:.4f} years) remaining at birth")
    add(f"  Period began : {balance['mahadasha_started'][:16].replace('T', ' ')}"
        f"  — before birth, by the elapsed portion")
    add(f"  Span         : {_date(dasha.start)} to {_date(dasha.end)}")

    # ── mahadashas ──────────────────────────────────────────────────────────
    add("")
    add("  MAHADASHA")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'#':<3}{'Lord':<10}{'English':<10}{'Start':<18}{'End':<18}"
        f"{'Days':>11}{'Years':>8}")
    for period in dasha.mahadashas:
        marker = ""
        if today is not None and period.contains(today):
            marker = "  <-- current"
        add(f"  {period.sequence_index:<3}{period.lord:<10}"
            f"{ENGLISH_NAME[period.lord]:<10}{_date(period.start):<18}"
            f"{_date(period.end):<18}{period.duration_days:>11.2f}"
            f"{_years(period.duration_days):>8}{marker}")

    # ── antardashas ─────────────────────────────────────────────────────────
    if show_all_antardashas:
        targets = dasha.mahadashas
    elif antardasha_for_current and today is not None:
        current = dasha.get_mahadasha_at(today)
        targets = [current] if current else []
    else:
        targets = dasha.mahadashas[:1]

    for maha in targets:
        if not maha.children:
            continue
        add("")
        add(f"  ANTARDASHA within the {maha.lord} mahadasha "
            f"({_date(maha.start)} to {_date(maha.end)})")
        add("  " + _RULE * (_WIDTH - 2))
        add(f"  {'#':<3}{'Lord':<10}{'English':<10}{'Start':<18}{'End':<18}"
            f"{'Days':>11}")
        for antar in maha.children:
            marker = ""
            if today is not None and antar.contains(today):
                marker = "  <-- current"
            add(f"  {antar.sequence_index:<3}{antar.lord:<10}"
                f"{ENGLISH_NAME[antar.lord]:<10}{_date(antar.start):<18}"
                f"{_date(antar.end):<18}{antar.duration_days:>11.2f}{marker}")

    # ── pratyantardasha for the current moment ──────────────────────────────
    if today is not None:
        current_antar = dasha.get_antardasha_at(today)
        if current_antar is not None and current_antar.children:
            add("")
            add(f"  PRATYANTARDASHA within {current_antar.mahadasha} / "
                f"{current_antar.lord}")
            add("  " + _RULE * (_WIDTH - 2))
            add(f"  {'#':<3}{'Lord':<10}{'Start':<18}{'End':<18}{'Days':>11}")
            for praty in current_antar.children:
                marker = ""
                if praty.contains(today):
                    marker = "  <-- current"
                add(f"  {praty.sequence_index:<3}{praty.lord:<10}"
                    f"{_date(praty.start):<18}{_date(praty.end):<18}"
                    f"{praty.duration_days:>11.2f}{marker}")

        stack = dasha.get_dasha_stack_at(today)
        add("")
        add(f"  STACK AT {_date(today)}")
        add("  " + _RULE * (_WIDTH - 2))
        if stack.get("in_range"):
            add(f"    mahadasha       {stack['mahadasha']}")
            add(f"    antardasha      {stack['antardasha']}")
            add(f"    pratyantardasha {stack['pratyantardasha']}")
        else:
            add(f"    {stack.get('note', 'outside the computed span')}")

    add("")
    add("  Dates are in the same time frame as the birth time supplied.")
    add("  Period boundaries are exact: children sum to their parent without "
        "rounding drift.")
    add("═" * _WIDTH)
    return "\n".join(lines)
