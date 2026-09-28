"""
BIRTH-TIME SENSITIVITY report section (V1.4 Part 22)
------------------------------------------------------
Shows unstable boundaries. Facts only, and explicitly not rectification.
"""

from __future__ import annotations

from .models import SensitivityReport

_WIDTH = 100
_RULE = "─"


def format_sensitivity_report(report: SensitivityReport) -> str:
    lines: list[str] = []
    add = lines.append

    add("")
    add("═" * _WIDTH)
    add("  BIRTH-TIME SENSITIVITY  (what changes near the stated time)")
    add("═" * _WIDTH)
    add(f"  Birth (UTC)  : {report.birth_utc.isoformat()}")
    add(f"  Scan step    : {report.scan_step_seconds}s, refined to 1s")
    add(f"  Watching     : Lagna sign/nakshatra/pada, "
        f"{'/'.join(report.watched_vargas)} Lagnas, graha "
        + ("bhavas" if report.bhava_system and
           report.bhava_system != "whole_sign" else "houses"))

    add("")
    add(f"  {'Window':<10}{'Stable?':<10}Changes")
    add("  " + _RULE * (_WIDTH - 2))
    for window in report.windows:
        if window.stable:
            add(f"  ±{window.window_minutes:<9}{'yes':<10}—")
            continue
        first = window.changes[0]
        add(f"  ±{window.window_minutes:<9}{'NO':<10}{first.describe()}")
        for change in window.changes[1:]:
            add(f"  {'':<20}{change.describe()}")

    add("")
    largest = report.tightest_stable_window
    if largest is None:
        add("  Nothing is stable even in the tightest window tested. Every "
            "classification")
        add("  listed above depends on the recorded birth time being exact.")
    else:
        add(f"  Everything watched is stable within ±{largest} minute(s).")

    add("")
    add("  This is NOT rectification. No birth time is suggested, preferred "
        "or scored.")
    add("  An unstable item rests on the clock as much as on the sky; verify "
        "the recorded")
    add("  time before relying on it.")
    add("═" * _WIDTH)
    return "\n".join(lines)
