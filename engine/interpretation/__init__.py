"""
Deterministic interpretation (V1.6)
-------------------------------------
    document = build_interpretation(prediction_snapshot.to_dict(),
                                    language="en",
                                    mode=ReportMode.DETAILED)
    print(format_interpretation(document))

The layer that turns structured synthesis into sentences, and the only one
in the engine that produces prose.

NO MODEL, NO NETWORK, NO RANDOMNESS

    Template substitution over a key and a dictionary of already-computed
    values. There is no language model, no generative component, no phrase
    variation, and nothing here reaches the network. The whole package runs
    offline and a test asserts it imports nothing that could.

WHAT IT MAY NOT DECIDE (Part 10)

    Whether a yoga exists, whether a graha is strong, which domain is
    activated, whether a transit matters, the confidence level, the timing
    window, or whether a factor is supportive. Every one of those was
    settled by an earlier deterministic layer, and this package is given
    the answers rather than the inputs — its argument is a serialised
    PredictionSnapshot, not a chart.

THE FIVE KINDS OF STATEMENT, AT THE END OF THE CHAIN

    ASTRONOMICAL FACT             engine/ephemeris.py
    ASTROLOGICAL FEATURE          engine/features/
    TEXTUAL RULE                  engine/rules/ + engine/sources/
    SOFTWARE SYNTHESIS            engine/synthesis/
    DETERMINISTIC INTERPRETATION  this package

    Readable prose is the least authoritative of the five and the easiest to
    mistake for the most. Every document says so in its own disclaimer.
"""

from .evidence_formatter import evidence_arguments, format_evidence
from .domain_renderer import render_domain, should_include
from .grammar import (
    duration_phrase, format_date, format_exact_date, house_name, join,
    ordinal, paragraph, planet_name, sentence, titlecase_domain,
)
from .keys import (
    ACTIVATION_LEVELS, ALL_KEYS, CONFIDENCE_LEVELS, activation_key,
    confidence_key, evidence_key, missing_keys, profile_key,
)
from .models import (
    EXPECTED_PREDICTION_SCHEMA, SCHEMA_VERSION, DomainSection,
    InterpretationDocument, RenderedPhrase, ReportMode, TimingSection,
)
from .renderer import (
    DEFAULT_LANGUAGE, TEMPLATE_ROOT, MissingTemplateArgument,
    MissingTemplateKey, TemplateError, TemplateSet, UnsupportedLocale,
    available_languages, completeness_report, load_templates,
    template_arguments,
)
from .report import (
    build_interpretation, format_interpretation, interpretation_hash,
)
from .timing_renderer import (
    render_dasha_stack, render_domain_timing, render_event_candidate,
    render_window,
)
from .warnings_renderer import (
    render_confidence, render_document_warnings, render_domain_warnings,
    unstable_charts,
)

__all__ = [
    "ACTIVATION_LEVELS", "ALL_KEYS", "CONFIDENCE_LEVELS", "DEFAULT_LANGUAGE",
    "EXPECTED_PREDICTION_SCHEMA", "SCHEMA_VERSION", "TEMPLATE_ROOT",
    "DomainSection", "InterpretationDocument", "MissingTemplateArgument",
    "MissingTemplateKey", "RenderedPhrase", "ReportMode", "TemplateError",
    "TemplateSet", "TimingSection", "UnsupportedLocale", "activation_key",
    "available_languages", "build_interpretation", "completeness_report",
    "confidence_key", "duration_phrase", "evidence_arguments",
    "evidence_key", "format_date", "format_evidence", "format_exact_date",
    "format_interpretation", "house_name", "interpretation_hash", "join",
    "load_templates", "missing_keys", "ordinal", "paragraph", "planet_name",
    "profile_key", "render_confidence", "render_dasha_stack",
    "render_document_warnings", "render_domain", "render_domain_timing",
    "render_domain_warnings", "render_event_candidate", "render_window",
    "sentence", "should_include", "template_arguments", "titlecase_domain",
    "unstable_charts",
]
