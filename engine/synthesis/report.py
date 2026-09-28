"""
Synthesis report (V1.5 Part 26)
---------------------------------
The human-readable rendering. Structured output read aloud, nothing added.

Every line here corresponds to a field computed elsewhere. The report has no
logic of its own beyond formatting and ordering, which is why Part 29 is safe
against it: nothing in this module decides anything.

Still no prose. "CAREER: ACTIVE (confidence MEDIUM), 4 supportive, 2
challenging" is a rendering of a data structure. "A promising period for your
career" would be an interpretation, and is not produced here or anywhere in
V1.5.
"""

from __future__ import annotations

from typing import Sequence

from .domains import HIGH_STAKES_NOTE, Domain, domain_mapping_summary
from .models import (
    ACTIVATION_MEANING, PROFILE_MEANING, ActivationLevel, EvidenceConfidence,
    EvidenceDirection, SynthesisProfile,
)

_RULE = "─" * 78


def _heading(title: str) -> list[str]:
    return ["", _RULE, f"  {title}", _RULE]


def format_synthesis_report(context, candidates: Sequence = (),
                            show_evidence: bool = True,
                            domain_filter=None) -> str:
    """The full Part 26 report for one synthesis run."""
    lines: list[str] = []

    # ── SYNTHESIS PROFILE ───────────────────────────────────────────────────
    lines.extend(_heading("SYNTHESIS PROFILE"))
    lines.append(f"  Profile      : {context.profile.value}")
    lines.append(f"  Moment       : {context.moment.isoformat()}")
    lines.append(f"  Meaning      : {PROFILE_MEANING[context.profile]}")
    if context.eligibility_counts:
        counts = ", ".join(f"{k} {v}" for k, v in
                           sorted(context.eligibility_counts.items()))
        lines.append(f"  Rule gate    : {counts}")
    if context.excluded_rules:
        lines.append(
            f"  Excluded     : {len(context.excluded_rules)} rule(s) the "
            f"profile does not admit")

    mapping = domain_mapping_summary()
    lines.append(
        f"  Domain model : {mapping['house_mappings_validated']}"
        f"/{mapping['house_mappings_total']} house mappings have a located "
        f"witness; {mapping['karakas_with_located_witness']}"
        f"/{mapping['karakas_total']} karakas do")

    # ── RELIABILITY WARNINGS ────────────────────────────────────────────────
    lines.extend(_heading("RELIABILITY WARNINGS"))
    reliability = context.reliability
    lines.append(
        f"  Birth time resolves to "
        f"{reliability.birth_time_precision_seconds}s "
        f"({reliability.precision_basis})")
    if not reliability.sensitivity_available:
        lines.append(
            "  Sensitivity was not computed. Nothing below has been shown to "
            "be stable; run with --birth-time-sensitivity to find out.")
    else:
        for chart, stable in (("D1", reliability.lagna_stable),
                              ("D9", reliability.d9_lagna_stable),
                              ("D10", reliability.d10_lagna_stable),
                              ("D60", reliability.d60_lagna_stable)):
            mark = "stable" if stable else "NOT RESOLVED by the entered time"
            lines.append(f"    {chart:<4} lagna : {mark}")
    for warning in reliability.warnings[:6]:
        lines.append(f"  • {warning}")

    # ── DASHA ACTIVATION ────────────────────────────────────────────────────
    lines.extend(_heading("DASHA ACTIVATION"))
    if not context.dasha_activations:
        lines.append("  No dasha supplied; no domain can rise above "
                     "BACKGROUND.")
    for activation in context.dasha_activations:
        houses = ", ".join(str(h) for h in activation.activated_houses)
        lines.append(
            f"  {activation.level:<16} {activation.planet:<8} "
            f"houses {houses}")
        if activation.strength_evidence:
            ratio = activation.strength_evidence.get("shadbala_ratio")
            lines.append(
                f"{'':>19}Shadbala {ratio:.2f}x requirement"
                if ratio is not None else "")
        if activation.yogas_activated:
            lines.append(
                f"{'':>19}yogas: "
                f"{', '.join(activation.yogas_activated)}")

    # ── TRANSIT TRIGGERS ────────────────────────────────────────────────────
    lines.extend(_heading("TRANSIT TRIGGERS"))
    if not context.transit_activations:
        lines.append("  No transit snapshot supplied.")
    else:
        lines.append(
            "  Factual relationships. No Gochara judgement is applied: the "
            "engine has no located source for transit interpretation.")
        for activation in context.transit_activations[:20]:
            marker = " (dasha lord)" if activation.is_dasha_lord else ""
            lines.append(f"  • {activation.explanation}{marker}")
        if len(context.transit_activations) > 20:
            lines.append(
                f"  … {len(context.transit_activations) - 20} more")

    # ── NATAL PROMISE and DOMAIN SYNTHESIS ──────────────────────────────────
    wanted = None
    if domain_filter:
        wanted = {Domain(d.upper()).value if isinstance(d, str) else d.value
                  for d in ([domain_filter]
                            if isinstance(domain_filter, str)
                            else domain_filter)}

    lines.extend(_heading("NATAL PROMISE"))
    for name, result in sorted(context.results.items()):
        if wanted and name not in wanted:
            continue
        if not result.has_natal_promise:
            continue
        lines.append(
            f"  {name:<20} {len(result.natal_evidence)} natal factor(s)")
        if show_evidence:
            for item in result.natal_evidence:
                lines.append(
                    f"      {_mark(item.direction)} {item.explanation}")

    lines.extend(_heading("DOMAIN SYNTHESIS"))
    lines.append(
        "  Activation and confidence are SOFTWARE CONVENTIONS, ordinal, and "
        "not probabilities.")
    lines.append("")
    for name, result in sorted(context.results.items()):
        if wanted and name not in wanted:
            continue
        if result.activation is ActivationLevel.INACTIVE and not wanted:
            continue
        mixed = "  [MIXED]" if result.mixed else ""
        lines.append(
            f"  {name:<20} {result.activation.value:<17} "
            f"confidence {result.confidence.value:<10}"
            f"+{len(result.supportive)} / -{len(result.challenging)}{mixed}")
        if show_evidence and result.mixed:
            # Part 16: both sides, never collapsed.
            for item in result.supportive:
                lines.append(f"      + {item.explanation}")
            for item in result.challenging:
                lines.append(f"      - {item.explanation}")
        for varga in result.varga_evidence:
            lines.append(
                f"      ~ {varga.chart}: {varga.factor} "
                f"[{varga.reliability.value}"
                f"{', confirms' if varga.confirms else ', diverges'}]")
        if result.notes:
            lines.append(f"      ! {result.notes}")

    # ── EVENT CANDIDATES ────────────────────────────────────────────────────
    lines.extend(_heading("EVENT CANDIDATES"))
    if not candidates:
        lines.append(
            "  None. A candidate needs an activated domain and a computable "
            "window; no window is invented to fill the gap.")
    for candidate in candidates:
        if wanted and candidate.domain not in wanted:
            continue
        window = candidate.window
        peak = f", peak {window.peak.date()}" if window.peak else ""
        lines.append(
            f"  {candidate.event_type.value:<28} "
            f"{window.start.date()} → {window.end.date()}{peak}")
        lines.append(
            f"{'':>4}activation {candidate.activation.value}, confidence "
            f"{candidate.confidence.value}, profile "
            f"{candidate.profile.value}")
        for why in window.why:
            lines.append(f"{'':>6}why: {why}")
        for warning in candidate.reliability_warnings[:3]:
            lines.append(f"{'':>6}! {warning}")

    lines.append("")
    lines.append(_RULE)
    lines.append(
        "  This is structured evidence, not a reading. No interpretation, "
        "no recommendation,")
    lines.append(
        "  no remedy and no probability is produced by this engine.")
    lines.append(_RULE)
    return "\n".join(line for line in lines if line is not None)


def _mark(direction: EvidenceDirection) -> str:
    return {
        EvidenceDirection.SUPPORTIVE: "+",
        EvidenceDirection.CHALLENGING: "-",
        EvidenceDirection.MIXED: "±",
        EvidenceDirection.NEUTRAL: "·",
    }[direction]
