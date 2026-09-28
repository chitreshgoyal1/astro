"""
Document assembly and text output (V1.6 Parts 15, 20, 25, 26, 33)
--------------------------------------------------------------------
Builds an InterpretationDocument from a PredictionSnapshot, and renders it
as plain text.

THREE MODES, ONE SOURCE (Part 25)

    SUMMARY     activation and confidence per domain, silent domains dropped
    DETAILED    evidence, timing and reliability as well
    TECHNICAL   plus rule ids, source ids and the evidence appendix

    They differ in how much is shown and never in what is claimed. A test
    asserts that the activation level for every domain is identical across
    all three, because a summary that rounded a finding would be a different
    document rather than a shorter one.

PART 15: SOURCES ARE AVAILABLE, NOT INTRUSIVE

    Verse numbers do not appear in summary or detailed prose. Technical mode
    prints the appendix, and the structured JSON always carries the ids, so
    the information is never lost — only kept out of the way of a reader who
    did not ask for it.

WHAT THIS MODULE MAY NOT DO (Part 10)

    Nothing here inspects a chart. Its input is a dict that came out of
    `PredictionSnapshot.to_dict()`; it could be read from a file written
    last year and the output would be identical. That property is what makes
    the determinism test meaningful.
"""

from __future__ import annotations

import datetime
import hashlib
from typing import Optional, Sequence

from . import grammar as G
from .domain_renderer import render_domain, should_include
from .models import (
    EXPECTED_PREDICTION_SCHEMA, DomainSection, InterpretationDocument,
    RenderedPhrase, ReportMode, TimingSection,
)
from .renderer import load_templates
from .timing_renderer import render_dasha_stack, render_event_candidate
from .warnings_renderer import render_document_warnings


def _phrase(templates, key, **args) -> RenderedPhrase:
    return RenderedPhrase(
        key=key,
        text=G.sentence(templates.render(key, **args), templates.grammar),
        args=args)


def build_interpretation(prediction: dict, *,
                         language: str = "en",
                         mode: ReportMode = ReportMode.DETAILED,
                         features=None,
                         birth: Optional[dict] = None,
                         generated: Optional[datetime.datetime] = None,
                         domains: Optional[Sequence[str]] = None
                         ) -> InterpretationDocument:
    """
    Render a PredictionSnapshot into an InterpretationDocument.

    `generated` is injectable so that the determinism test can hold it
    fixed. Left to default it records the wall clock, which is the one
    field of the document that legitimately varies between runs.
    """
    if isinstance(mode, str):
        mode = ReportMode(mode)
    templates = load_templates(language)

    profile = prediction.get("methodology_profile", "standard")
    reliability = prediction.get("reliability", {})
    candidates = prediction.get("event_candidates", [])

    document = InterpretationDocument(
        generated=(generated or datetime.datetime.now()).isoformat(),
        language=language,
        report_mode=mode,
        profile=profile,
        generated_from_prediction_schema=prediction.get("schema_version"),
        natal_snapshot_id=prediction.get("natal_snapshot_id"),
        moment=prediction.get("datetime", ""),
    )

    if prediction.get("schema_version") != EXPECTED_PREDICTION_SCHEMA:
        # V1.8: this sentence was English no matter the language, because
        # the branch never fired until a schema bump made it fire. That is
        # the class of defect a second locale exists to find — see the
        # V1.7 notes on the four the Hindi work exposed — and the fix is
        # the same one: a key, in every locale, with named arguments.
        key = "reliability.schema_mismatch"
        args = {"found": prediction.get("schema_version"),
                "expected": EXPECTED_PREDICTION_SCHEMA}
        document.reliability_warnings.append(RenderedPhrase(
            key=key,
            text=G.sentence(templates.render(key, **args), templates.grammar),
            args=args))

    # ── birth summary and framing ───────────────────────────────────────────
    if birth:
        document.birth_summary = dict(birth)
        # The caller supplies an ISO date because that is what a snapshot
        # carries. A reader gets the date in their own calendar words —
        # `30 August 1988`, `30 अगस्त 1988` — and a date that cannot be
        # parsed is passed through unchanged rather than guessed at.
        birth_date = birth.get("date", "")
        try:
            birth_date = G.format_exact_date(birth_date,
                                             templates.month_names())
        except (ValueError, TypeError):
            pass
        document.methodology_summary.append(_phrase(
            templates, "document.birth_summary",
            name=birth.get("name", "the native"),
            birth_date=birth_date,
            birth_time=birth.get("time", ""),
            place=birth.get("place", "")))

    moment_text = G.format_exact_date(prediction.get("datetime"),
                                      templates.month_names())
    # The profile name appears INSIDE sentences, so it is vocabulary and
    # not an identifier. `document.profile` above keeps the engine's value;
    # this is the reader's word for it (V1.7 Part 25).
    profile_word = templates.term("profile", profile, default=profile)
    document.methodology_summary.append(_phrase(
        templates, "document.generated_for",
        date=moment_text, profile=profile_word))

    # ── Part 15: methodology, stated once and plainly ───────────────────────
    document.methodology_summary.append(_phrase(
        templates, "methodology.statement", profile=profile_word))
    document.methodology_summary.append(_phrase(
        templates, f"methodology.profile.{profile}"))
    document.methodology_summary.append(_phrase(
        templates, "methodology.not_validated"))

    document.disclaimer = _phrase(templates, "document.disclaimer")

    # ── reliability, document level ─────────────────────────────────────────
    document.reliability_warnings.extend(
        render_document_warnings(reliability, templates))

    # ── timing, document level ──────────────────────────────────────────────
    timing = TimingSection()
    stack = (prediction.get("dasha") or {}).get("stack", {})
    timing.dasha_stack = render_dasha_stack(stack, templates)
    if mode is not ReportMode.SUMMARY:
        for candidate in candidates:
            timing.event_candidates.append(
                render_event_candidate(candidate, templates))
    if timing.dasha_stack or timing.event_candidates:
        document.timing_sections = timing

    # ── domain sections ─────────────────────────────────────────────────────
    wanted = {d.upper() for d in domains} if domains else None
    results = prediction.get("domain_results", {})
    for name in sorted(results):
        if wanted and name not in wanted:
            continue
        section = render_domain(
            results[name], templates, reliability=reliability,
            candidates=candidates, features=features, mode=mode,
            profile=profile)
        if should_include(section, mode):
            document.domain_sections.append(section)

    # ── Part 33: the source appendix ────────────────────────────────────────
    if mode is ReportMode.TECHNICAL:
        document.technical_appendix = _build_appendix(prediction, templates)

    return document


def _build_appendix(prediction: dict, templates) -> dict:
    """
    Part 33: rule, witness, chapter, verse, validation status.

    Identifiers and citations only. No source passage is reproduced, here or
    anywhere else the engine writes — the licences on the Sanskrit texts and
    the copyright on the translation both forbid it, and a citation is what
    a reader needs in order to go and check.
    """
    appendix = prediction.get("evidence_appendix", {}) or {}
    sources = []
    for source in appendix.get("sources", []):
        if not source.get("resolved"):
            sources.append({"id": source["id"], "resolved": False,
                            "note": source.get("note", "")})
            continue
        sources.append({
            "id": source["id"],
            "citation": source.get("citation", ""),
            "work": source.get("work", ""),
            "authority": source.get("authority", ""),
            "edition": source.get("edition", ""),
        })

    return {
        "heading": templates.render("appendix.heading"),
        "sources": sources,
        "rules": appendix.get("rules", []),
        "methodologies": appendix.get("methodologies", []),
        "rule_eligibility": prediction.get("rule_eligibility", {}),
        "note": (
            "Identifiers and citations only. No source passage is reproduced "
            "in this engine's output."),
    }


# ── plain-text rendering ─────────────────────────────────────────────────────

_RULE = "─" * 78


def _heading(title: str) -> list[str]:
    return ["", _RULE, f"  {title.upper()}", _RULE]


def format_interpretation(document: InterpretationDocument) -> str:
    """
    The document as plain text, in the shape Part 20 describes.

    EVERY HEADING COMES FROM THE LOCALE (V1.7 Part 26)

        V1.6 printed English literals here while the sentences beneath them
        were fully translated, which an English-only build could not show.
        The template set is reloaded from `document.language` rather than
        passed in, so an InterpretationDocument read back from a file
        formats in its own language with nothing else supplied.
    """
    mode = document.report_mode
    templates = load_templates(document.language)

    def label(key: str) -> str:
        return templates.template(key)

    lines: list[str] = []

    lines.extend(_heading(label("heading.interpretation")))
    for phrase in document.methodology_summary:
        lines.append(f"  {phrase.text}")

    if document.timing_sections and document.timing_sections.dasha_stack:
        lines.append("")
        lines.append(f"  {document.timing_sections.dasha_stack.text}")

    if document.reliability_warnings:
        lines.extend(_heading(label("heading.reliability")))
        for phrase in document.reliability_warnings:
            lines.append(f"  • {phrase.text}")

    for section in document.domain_sections:
        lines.extend(_heading(section.title))

        if section.is_silent:
            lines.append(f"  {section.silence.text}")
            if section.safety:
                lines.append(f"  {section.safety.text}")
            continue

        lines.append(f"  {section.overall.text}")
        if section.confidence_phrase:
            lines.append(f"  {section.confidence_phrase.text}")
        if section.contradiction:
            lines.append("")
            lines.append(f"  {section.contradiction.text}")

        for title, phrases in (
                (label("section.natal_foundation"), section.natal_foundation
                 if mode is ReportMode.TECHNICAL else []),
                (label("section.supporting_factors"), section.supporting),
                (label("section.challenging_factors"), section.challenging),
                (label("section.dasha_activation"), section.dasha),
                (label("section.transit_triggers"), section.transits)):
            if not phrases:
                continue
            lines.append("")
            lines.append(f"  {title}")
            for phrase in phrases:
                lines.append(f"    - {phrase.text}")

        if section.timing:
            lines.append("")
            lines.append(f"  {label('section.timing_window')}")
            for phrase in section.timing:
                lines.append(f"    - {phrase.text}")

        if section.reliability:
            lines.append("")
            lines.append(f"  {label('section.reliability')}")
            for phrase in section.reliability:
                lines.append(f"    ! {phrase.text}")

        if section.safety:
            lines.append("")
            lines.append(f"  {section.safety.text}")

        if mode is ReportMode.TECHNICAL and section.rule_ids:
            lines.append("")
            lines.append(
                f"  {label('heading.rules')}: "
                f"{', '.join(sorted(section.rule_ids))}")
        if mode is ReportMode.TECHNICAL and section.source_ref_ids:
            lines.append(
                f"  {label('heading.sources')}: "
                f"{', '.join(sorted(section.source_ref_ids))}")

    if document.technical_appendix:
        lines.extend(_heading(document.technical_appendix["heading"]))
        sources = document.technical_appendix["sources"]
        if not sources:
            lines.append(f"  {label('appendix.no_sources')}")
        for source in sources:
            if not source.get("resolved", True):
                lines.append(f"  ? {source['id']} — unresolved reference")
                continue
            lines.append(f"  • {source['citation']}  [{source['authority']}]")
        rules = document.technical_appendix.get("rules", [])
        if rules:
            lines.append("")
            for rule in rules:
                lines.append(
                    f"  • {rule['rule_id']}: {rule['validation_status']}, "
                    f"eligibility {rule['prediction_eligibility']}")

    lines.extend(_heading(label("heading.note")))
    lines.append(f"  {document.disclaimer.text}")
    lines.append(_RULE)
    return "\n".join(lines)


def interpretation_hash(document: InterpretationDocument) -> str:
    """
    A stable hash of the rendered content (Part 28).

    Excludes `generated`, which is a wall-clock timestamp and the one field
    that legitimately differs between two runs of the same input. Everything
    else must be byte-identical, and this is what the determinism test
    compares.
    """
    payload = document.to_dict()
    payload.pop("generated", None)
    import json
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                         default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
