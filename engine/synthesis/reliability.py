"""
Birth-time confidence gating (V1.5 Parts 4, 9)
------------------------------------------------
Turns the V1.4 sensitivity scan into a constraint on what synthesis is
allowed to lean on.

THE FINDING THIS EXISTS FOR

    V1.4 measured the regression chart and reported that its D60 Lagna
    changes 39 seconds after the stated birth time. The stated birth time
    came from a form field reading HH:MM.

    Those two facts together mean the D60 Lagna of that chart is not known.
    Not "known imprecisely" — not known. The engine can compute it to six
    decimal places and the sixth decimal place is a property of the
    arithmetic, not of the person.

    V1.4 printed the warning. V1.5 acts on it: D60-derived evidence in that
    chart is marked LOW_CONFIDENCE, and in the strict profile it is dropped.

WHAT THIS IS NOT

    Not rectification. Nothing here proposes a better birth time, scores
    candidate times, or prefers one. It reads the entered precision, reads
    what the scan found, and answers one question: is this classification
    resolved by what the user actually told us?
"""

from __future__ import annotations

from typing import Optional

from .models import ChartReliability, EvidenceConfidence

# What an entered birth time actually pins down.
#
# A user who types "14:32" has told us the minute. The seconds are not
# rounded-off precision the engine may recover; they were never supplied.
# Treating HH:MM as second-exact is how a chart acquires confidence nobody
# ever claimed for it.
PRECISION_FROM_HH_MM_SECONDS = 60
PRECISION_FROM_HH_MM_SS_SECONDS = 1

# A remembered or recorded time is usually worse than the field it was typed
# into. The engine does NOT assume this — it is offered for a caller who
# knows the provenance of the time and wants to say so.
PRECISION_STATED_TO_FIVE_MINUTES = 300
PRECISION_STATED_TO_QUARTER_HOUR = 900

DEFAULT_PRECISION_SECONDS = PRECISION_FROM_HH_MM_SECONDS

# Vargas whose Lagna the sensitivity engine watches.
WATCHED_CHARTS = ("D1", "D9", "D10", "D60")


def _item_key(item) -> str:
    return (getattr(item, "key", "") or "").lower()


def build_reliability(sensitivity=None,
                      birth_time_precision_seconds: int
                      = DEFAULT_PRECISION_SECONDS,
                      precision_basis: str = "birth time entered as HH:MM"
                      ) -> ChartReliability:
    """
    What the entered time supports, given what the scan found.

    `sensitivity` is a V1.4 SensitivityReport, or None. None does NOT mean
    stable: it means unmeasured, and every flag is left at its default with
    `sensitivity_available` False so a consumer can tell the two apart.
    """
    reliability = ChartReliability(
        birth_time_precision_seconds=birth_time_precision_seconds,
        precision_basis=precision_basis,
    )

    if sensitivity is None:
        reliability.warnings.append(
            "Birth-time sensitivity was not computed, so nothing here has "
            "been shown to be stable. Absence of a warning is not a "
            "guarantee of stability.")
        return reliability

    reliability.sensitivity_available = True

    # Everything that changes at an offset SMALLER than the entered precision
    # is unresolved by the input. An instability at +4 minutes matters if the
    # time is known to five minutes and not if it is known to the second.
    horizon = birth_time_precision_seconds
    unresolved = []
    for window in sensitivity.windows:
        for change in window.changes:
            if abs(change.offset_seconds) <= horizon:
                unresolved.append(change)

    seen = set()
    for change in unresolved:
        key = (change.key, change.offset_seconds)
        if key in seen:
            continue
        seen.add(key)
        reliability.unstable_items.append(change.to_dict())

        marker = _item_key(change)
        if "d60" in marker:
            reliability.d60_lagna_stable = False
        elif "d10" in marker:
            reliability.d10_lagna_stable = False
        elif "d9" in marker or "navamsha" in marker:
            reliability.d9_lagna_stable = False
        elif "bhava" in marker:
            reliability.bhava_stable = False
        elif "nakshatra" in marker or "pada" in marker:
            reliability.nakshatra_stable = False
        elif "lagna" in marker:
            reliability.lagna_stable = False

        reliability.warnings.append(
            f"{change.item} changes at {change.offset_text}, which is inside "
            f"the {birth_time_precision_seconds}s the entered birth time "
            f"resolves. That classification is not determined by the input.")

    if not unresolved:
        reliability.warnings.append(
            f"Nothing watched changes within {birth_time_precision_seconds}s "
            f"of the entered time.")

    return reliability


# ── Part 9: what a chart's evidence is worth ─────────────────────────────────

def chart_reliability(chart: str, reliability: ChartReliability
                      ) -> EvidenceConfidence:
    """
    The confidence ceiling for evidence drawn from one divisional chart.

    Part 9's rule — that D60 must not outrank D1 merely for being finer —
    falls out of this rather than being asserted: a finer varga subdivides
    the same uncertain Lagna into smaller pieces, so it is MORE sensitive to
    the unknown seconds, not less.
    """
    stable = reliability.chart_is_stable(chart)
    if stable is None:
        # Unmeasured. The divisor still tells us something: D60 divides each
        # rashi into sixty parts, so an unmeasured D60 deserves less trust
        # than an unmeasured D1 even with no scan to point at.
        return (EvidenceConfidence.LOW if chart in ("D30", "D60")
                else EvidenceConfidence.MEDIUM)
    if not stable:
        return EvidenceConfidence.LOW
    if not reliability.lagna_stable and chart != "D1":
        # Every varga is computed from the same longitude the Lagna is. If
        # the Lagna itself is unresolved, nothing derived from it is firmer.
        return EvidenceConfidence.LOW
    return EvidenceConfidence.HIGH


def chart_warnings(chart: str, reliability: ChartReliability) -> list[str]:
    """Reliability warnings that apply to evidence from this chart."""
    stable = reliability.chart_is_stable(chart)
    if stable is None:
        return [f"{chart} stability was not measured for this birth time."]
    if stable:
        return []
    return [
        f"{chart} Lagna is not resolved by the entered birth time "
        f"(precision {reliability.birth_time_precision_seconds}s); evidence "
        f"drawn from {chart} is marked LOW confidence."]


def admits_chart(chart: str, reliability: ChartReliability,
                 strict: bool) -> bool:
    """
    Whether a profile may use evidence from this chart at all.

    Strict synthesis drops a chart whose Lagna the birth time does not
    resolve. The standard and experimental profiles keep it and mark it LOW,
    because a flagged weak input is more useful to a reader than a silent
    omission — but strict is exactly the profile where that trade goes the
    other way.
    """
    if not strict:
        return True
    return chart_reliability(chart, reliability) is not EvidenceConfidence.LOW
