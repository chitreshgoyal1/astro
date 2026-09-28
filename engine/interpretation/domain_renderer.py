"""
Domain sections (V1.6 Parts 16, 20, 22, 31)
---------------------------------------------
Turns one domain's synthesis result into a readable section.

PART 16: CONTRADICTIONS SURVIVE

    Where supporting and challenging evidence both exist, both lists are
    rendered and a sentence says so. The renderer has no arithmetic for
    netting them off, because the synthesis layer already declined to do
    that and it would be a strange place to reintroduce it.

PART 31: SILENCE IS AN ANSWER

    A domain the active profile cannot speak about says so, in one of three
    distinct ways, because the three situations are genuinely different and
    a reader should be able to tell them apart:

        no evidence the profile admits      → insufficient validated evidence
        natal evidence, nothing activating  → BACKGROUND, rendered normally
        transits touching, no natal promise → the transit-without-promise line

    The third is the one worth having. It is the case where a naive engine
    announces a finding, and where saying nothing at all would leave a
    reader unable to tell that the engine looked.

PART 22: HEALTH AND LONGEVITY

    Both carry an explicit scope sentence, drawn from the template set so a
    translation cannot lose it. The domain template files for those two also
    supply their own activation wording, which is written to describe a
    calculated indication rather than a bodily state.
"""

from __future__ import annotations

from typing import Optional

from . import grammar as G
from . import keys as K
from .evidence_formatter import format_evidence
from .models import DomainSection, RenderedPhrase, ReportMode
from .timing_renderer import render_domain_timing
from .warnings_renderer import (
    render_boundary_warnings, render_confidence, render_domain_warnings,
)

# Domains whose sections carry a scope limit (Part 22).
SAFETY_KEYS = {
    "HEALTH": "safety.health_scope",
    "LONGEVITY": "safety.longevity_scope",
}


def _phrase(templates, key, domain=None, **args) -> RenderedPhrase:
    return RenderedPhrase(
        key=key,
        text=G.sentence(templates.render(key, domain=domain, **args),
                        templates.grammar),
        args=args)


def _evidence_phrases(items, templates, features, domain, mode):
    """Render a list of evidence records, preserving the engine's order."""
    if mode is ReportMode.SUMMARY:
        return []
    return [format_evidence(item, templates, features, domain)
            for item in items]


def render_domain(result, templates, *, reliability: dict,
                  candidates: list, features=None,
                  mode: ReportMode = ReportMode.DETAILED,
                  profile: str = "standard") -> DomainSection:
    """
    One domain section from one SynthesisResult dict.

    `result` is the serialised form from PredictionSnapshot, so this renderer
    never touches a live engine object and could be run against a stored
    snapshot months later.
    """
    domain = result["domain"]
    activation = result["activation"]
    confidence = result["confidence"]
    # The profile name is printed inside sentences, so it is a word the
    # locale owns rather than the engine identifier (V1.7 Part 25).
    profile = templates.term("profile", profile, default=profile)

    section = DomainSection(
        domain=domain,
        title=templates.domain_title(domain),
        activation=activation,
        confidence=confidence,
        source_ref_ids=tuple(result.get("source_ref_ids", ())),
        rule_ids=tuple(result.get("rule_ids", ())),
    )

    supportive = result.get("supportive", [])
    challenging = result.get("challenging", [])
    natal = result.get("natal_evidence", [])
    dasha = result.get("dasha_evidence", [])
    transits = result.get("transit_evidence", [])

    # ── Part 31: the three kinds of silence ─────────────────────────────────
    if activation == "INACTIVE":
        touching_transits = [
            w for w in result.get("reliability_warnings", [])
            if "no natal indication" in w]
        if touching_transits:
            section.silence = _phrase(
                templates, "silence.transit_without_promise", domain)
        elif not natal:
            section.silence = _phrase(
                templates, "silence.insufficient_validated_evidence", domain,
                profile=profile)
        else:
            section.silence = _phrase(
                templates, "silence.no_natal_indication", domain,
                profile=profile)
        if domain in SAFETY_KEYS:
            section.safety = _phrase(templates, SAFETY_KEYS[domain], domain)
        return section

    # ── Part 20: the section body ───────────────────────────────────────────
    section.overall = _phrase(
        templates, K.activation_key(activation), domain)
    section.confidence_phrase = render_confidence(confidence, templates,
                                                  domain)

    section.natal_foundation = _evidence_phrases(
        natal, templates, features, domain, mode)

    if supportive and challenging:
        # Summary mode does not print the two lists, so it gets a sentence
        # that does not promise them.
        section.contradiction = _phrase(
            templates,
            "contradiction.both_present" if mode.shows_evidence
            else "contradiction.both_present_summary",
            domain)
    elif supportive:
        section.contradiction = _phrase(
            templates, "contradiction.supportive_only", domain)
    elif challenging:
        section.contradiction = _phrase(
            templates, "contradiction.challenging_only", domain)

    section.supporting = _evidence_phrases(
        supportive, templates, features, domain, mode)
    section.challenging = _evidence_phrases(
        challenging, templates, features, domain, mode)
    section.dasha = _evidence_phrases(
        dasha, templates, features, domain, mode)
    section.transits = _evidence_phrases(
        transits, templates, features, domain, mode)

    section.timing = render_domain_timing(domain, candidates, templates)

    section.reliability = (
        render_domain_warnings(result, reliability, templates, domain)
        + render_boundary_warnings(result, templates, domain))

    if mode is not ReportMode.SUMMARY:
        excluded = result.get("excluded_by_profile", [])
        if excluded:
            section.reliability.append(_phrase(
                templates, "silence.excluded_by_profile", domain,
                count=len(excluded), profile=profile))

    if domain in SAFETY_KEYS:
        section.safety = _phrase(templates, SAFETY_KEYS[domain], domain)

    return section


def should_include(section: DomainSection, mode: ReportMode) -> bool:
    """
    Whether a section appears at all, per Part 31.

    Summary mode drops silent domains: a short document listing thirteen
    areas the engine declines to discuss buries the four it can. Detailed
    and technical keep them, because there the absence of a finding is
    itself information the reader came for.
    """
    if mode is ReportMode.SUMMARY:
        return not section.is_silent
    return True
