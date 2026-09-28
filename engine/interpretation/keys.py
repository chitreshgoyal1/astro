"""
Interpretation keys (V1.6 Parts 11, 29)
-----------------------------------------
The semantic vocabulary that stands between the synthesis engine and any
particular language.

WHY KEYS AND NOT PARAGRAPHS

    Seventeen domains times five activation levels times four confidence
    bands times the presence or absence of each evidence type is a
    combinatorial space nobody can write paragraphs for. Worse, if anyone
    tried, the paragraphs would drift out of agreement with the structured
    result they claim to describe, and there would be no way to tell.

    So the renderer resolves a KEY plus ARGUMENTS. The key names a semantic
    state the engine actually computed; the arguments carry the specifics.
    A template supplies the sentence.

THE COMPLETENESS GUARANTEE (Part 29)

    `ALL_KEYS` enumerates every key the engine can emit. A test asserts that
    every one of them resolves in every shipped locale, and the renderer
    raises rather than falling back to generic text. Silent fallback is how
    a report ends up saying nothing in particular about a specific finding.

KEY SHAPE

    `<section>.<subject>.<state>`, lower case, dot separated. A domain may
    override any key by supplying it in its own template file — `career.json`
    can give `domain.activation.ACTIVE` a career-specific sentence — and the
    renderer falls back to `common.json` when it does not. That fallback is
    between TEMPLATE FILES, not to generic text, and the key must exist in
    one of them or the render fails.
"""

from __future__ import annotations

from typing import Iterable

# ── activation and confidence ────────────────────────────────────────────────

ACTIVATION_LEVELS = ("INACTIVE", "BACKGROUND", "ACTIVE", "STRONGLY_ACTIVE",
                     "MIXED")
CONFIDENCE_LEVELS = ("HIGH", "MEDIUM", "LOW", "UNRESOLVED")
DIRECTIONS = ("SUPPORTIVE", "CHALLENGING", "MIXED", "NEUTRAL")
PROFILES = ("strict", "standard", "experimental")

ACTIVATION = tuple(f"domain.activation.{level}" for level in ACTIVATION_LEVELS)
CONFIDENCE = tuple(f"confidence.{level}" for level in CONFIDENCE_LEVELS)
PROFILE = tuple(f"methodology.profile.{p}" for p in PROFILES)

# ── evidence phrases (Part 14) ───────────────────────────────────────────────
#
# One key per `explanation_key` the synthesis layer emits. These are the
# keys most likely to go missing when a future release adds a factor, which
# is exactly what the completeness test is for.

EVIDENCE_KEYS = (
    "evidence.house_lord_dignified",
    "evidence.house_lord_debilitated",
    "evidence.house_lord_in_dusthana",
    "evidence.house_lord_well_placed",
    "evidence.house_lord_combust",
    "evidence.benefic_occupies_house",
    "evidence.malefic_occupies_house",
    "evidence.benefic_aspects_house",
    "evidence.malefic_aspects_house",
    "evidence.karaka_dignified",
    "evidence.karaka_afflicted",
    "evidence.house_lord_shadbala",
    "evidence.sarvashtakavarga_bindus",
    "evidence.yoga_present",
    "evidence.dasha_lord_activates_house",
    "evidence.dasha_lord_carries_yoga",
    "evidence.over_natal_house",
    "evidence.over_house_from_natal_moon",
    "evidence.conjunct_natal_point",
    "evidence.graha_drishti_to_natal_point",
)

# ── section headings and framing ─────────────────────────────────────────────

SECTION_KEYS = (
    "section.natal_foundation",
    "section.supporting_factors",
    "section.challenging_factors",
    "section.dasha_activation",
    "section.transit_triggers",
    "section.timing_window",
    "section.reliability",
    "section.overall_activation",
    "section.varga_confirmation",
)

# ── contradiction (Part 16) ──────────────────────────────────────────────────

CONTRADICTION_KEYS = (
    "contradiction.both_present",
    # Summary mode shows no evidence lists, so the sentence that promises
    # them would be writing a cheque the document does not cash. Part 25
    # says the modes differ in how much they show and never in what they
    # claim, and "both are listed below" when nothing is listed below fails
    # that in the small.
    "contradiction.both_present_summary",
    "contradiction.supportive_only",
    "contradiction.challenging_only",
)

# ── timing (Part 17) ─────────────────────────────────────────────────────────

TIMING_KEYS = (
    "timing.window_with_peak",
    "timing.window_without_peak",
    "timing.no_window",
    "timing.dasha_stack",
    "timing.event_candidate",
)

# ── reliability and birth time (Parts 18, 19) ────────────────────────────────

RELIABILITY_KEYS = (
    "reliability.birth_time_precision",
    "reliability.sensitivity_not_computed",
    "reliability.varga_unstable",
    "reliability.lagna_unstable",
    "reliability.boundary_unresolved",
    "reliability.depends_on_unstable_varga",
    # V1.8. Present since V1.6 as a hard-coded English sentence, which no
    # completeness test could see because it was never a key. Bumping the
    # prediction schema fired the branch and the Hindi document showed an
    # English line.
    "reliability.schema_mismatch",
)

# ── silence and gating (Part 31) ─────────────────────────────────────────────

SILENCE_KEYS = (
    "silence.insufficient_validated_evidence",
    "silence.no_natal_indication",
    "silence.transit_without_promise",
    "silence.excluded_by_profile",
)

# ── safety (Part 22) ─────────────────────────────────────────────────────────

SAFETY_KEYS = (
    "safety.health_scope",
    "safety.longevity_scope",
)

# ── methodology and appendix (Parts 15, 33) ──────────────────────────────────

METHODOLOGY_KEYS = (
    "methodology.statement",
    "methodology.domain_mapping_coverage",
    "methodology.not_validated",
    "appendix.heading",
    "appendix.source_row",
    "appendix.rule_row",
    "appendix.no_sources",
)

# ── document framing ─────────────────────────────────────────────────────────

DOCUMENT_KEYS = (
    "document.title",
    "document.birth_summary",
    "document.disclaimer",
    "document.generated_for",
)

# ── document furniture (V1.7 Part 26) ────────────────────────────────────────
#
# V1.6 defined `section.*` for the headings inside a domain and then printed
# English literals for them anyway, and the headings above the domains —
# "Interpretation", "Reliability", "Note" — had no keys at all. In an
# English-only build the difference was invisible.
#
# Hindi made it obvious in the first rendered document: fully translated
# sentences under headings reading "Supporting factors". Adding these keys
# is the fix, and the completeness test is what will stop the next locale
# inheriting the same gap.

HEADING_KEYS = (
    "heading.interpretation",
    "heading.reliability",
    "heading.note",
    "heading.rules",
    "heading.sources",
)

ALL_KEYS: tuple[str, ...] = (
    ACTIVATION + CONFIDENCE + PROFILE + EVIDENCE_KEYS + SECTION_KEYS
    + CONTRADICTION_KEYS + TIMING_KEYS + RELIABILITY_KEYS + SILENCE_KEYS
    + SAFETY_KEYS + METHODOLOGY_KEYS + DOCUMENT_KEYS + HEADING_KEYS
)


def activation_key(level: str) -> str:
    if level not in ACTIVATION_LEVELS:
        raise KeyError(
            f"unknown activation level '{level}'; expected one of "
            f"{', '.join(ACTIVATION_LEVELS)}")
    return f"domain.activation.{level}"


def confidence_key(level: str) -> str:
    if level not in CONFIDENCE_LEVELS:
        raise KeyError(
            f"unknown confidence level '{level}'; expected one of "
            f"{', '.join(CONFIDENCE_LEVELS)}")
    return f"confidence.{level}"


def evidence_key(explanation_key: str) -> str:
    """
    The template key for one piece of structured evidence.

    Raises on an unknown explanation key rather than inventing a phrase.
    Part 29: a missing key is a test failure, not a shrug — an evidence type
    the renderer cannot describe is one the reader would never learn about.
    """
    key = f"evidence.{explanation_key}"
    if key not in EVIDENCE_KEYS:
        raise KeyError(
            f"no interpretation key for evidence '{explanation_key}'. Add "
            f"'{key}' to keys.EVIDENCE_KEYS and to every locale's templates.")
    return key


def profile_key(profile: str) -> str:
    if profile not in PROFILES:
        raise KeyError(f"unknown synthesis profile '{profile}'")
    return f"methodology.profile.{profile}"


def missing_keys(available: Iterable[str]) -> list[str]:
    """Keys the engine can emit that a template set does not define."""
    have = set(available)
    return sorted(key for key in ALL_KEYS if key not in have)
