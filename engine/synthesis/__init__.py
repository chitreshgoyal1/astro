"""
Deterministic synthesis (V1.5)
--------------------------------
    context = synthesise(features, moment=when, yoga_results=yogas,
                         dasha=dasha, transit_snapshot=transits,
                         profile=SynthesisProfile.STANDARD)
    context.result_for("CAREER").activation      # ActivationLevel.ACTIVE
    candidates = event_candidates(context, dasha=dasha)

The first layer in this engine that COMBINES facts rather than computing
them. Five kinds of statement are kept apart throughout:

    ASTRONOMICAL FACT             engine/ephemeris.py
    ASTROLOGICAL FEATURE          engine/features/
    TEXTUAL RULE                  engine/rules/ + engine/sources/
    SOFTWARE SYNTHESIS HEURISTIC  this package
    INTERPRETATION                not implemented, in V1.5 or anywhere yet

Everything here is the fourth. The activation bands, the confidence bands,
the evidence weights and the domain mappings are engine conventions; no
classical text states any of them, and every serialised record says so.

THE THREE GUARANTEES

    1. A transit cannot create a natal promise. Part 14's hierarchy is
       enforced in `engine._gated_transit_evidence`, not left to callers.
    2. An unverified rule cannot influence strict synthesis. Eligibility is
       computed from the source registry, so a rule is promoted by producing
       evidence and by nothing else.
    3. No probability is emitted. Activation and confidence are ordinal, and
       a test asserts no output field implies a likelihood.
"""

from .activation import (
    dasha_activation, dasha_activations_for_domain, dasha_stack_activations,
    transit_activation,
)
from .domains import (
    DOMAINS, HIGH_STAKES_DOMAINS, Domain, DomainSpec, Karaka,
    domain_mapping_summary, domains_for_house, spec_for,
)
from .eligibility import (
    admits, describe, eligibility_reasons, eligibility_summary,
    filter_results, prediction_eligibility,
)
from .engine import SynthesisContext, synthesise, synthesis_appendix
from .events import (
    NO_EVENT_DOMAINS, candidates_for_domain, dasha_window, event_candidates,
)
from .evidence import (
    EvidenceLineage, build_lineage, evidence_appendix, resolve_rules,
    resolve_sources,
)
from .models import (
    ACTIVATION_MEANING, ELIGIBILITY_MEANING, PROFILE_MEANING, ActivationLevel,
    ChartReliability, DashaActivation, DomainEvidence, EventCandidate,
    EventType, EvidenceConfidence, EvidenceDirection, EvidenceLayer,
    PredictionEligibility, SynthesisProfile, SynthesisResult,
    TimingWindow, TransitActivation, VargaEvidence, weakest_confidence,
)
from .natal_promise import evaluate_natal_promise, varga_confirmation
from .reliability import (
    DEFAULT_PRECISION_SECONDS, PRECISION_FROM_HH_MM_SECONDS,
    admits_chart, build_reliability, chart_reliability, chart_warnings,
)
from .report import format_synthesis_report
from .scoring import (
    activation_level, explain_activation, explain_confidence,
    synthesis_confidence,
)
from .snapshot import (
    EXPECTED_NATAL_SCHEMA, SCHEMA_VERSION, PredictionSnapshot,
    build_prediction_snapshot, natal_snapshot_id,
)

__all__ = [
    "ACTIVATION_MEANING", "DEFAULT_PRECISION_SECONDS", "DOMAINS",
    "ELIGIBILITY_MEANING", "EXPECTED_NATAL_SCHEMA", "HIGH_STAKES_DOMAINS",
    "NO_EVENT_DOMAINS", "PRECISION_FROM_HH_MM_SECONDS", "PROFILE_MEANING",
    "SCHEMA_VERSION", "ActivationLevel", "ChartReliability",
    "DashaActivation", "Domain", "DomainEvidence", "DomainSpec",
    "EventCandidate", "EventType", "EvidenceConfidence", "EvidenceDirection",
    "EvidenceLayer", "EvidenceLineage", "Karaka", "PredictionEligibility",
    "PredictionSnapshot", "SynthesisContext", "SynthesisProfile",
    "SynthesisResult", "TimingWindow", "TransitActivation", "VargaEvidence",
    "activation_level", "admits", "admits_chart", "build_lineage",
    "build_prediction_snapshot", "build_reliability",
    "candidates_for_domain", "chart_reliability", "chart_warnings",
    "dasha_activation", "dasha_activations_for_domain",
    "dasha_stack_activations", "dasha_window", "describe",
    "domain_mapping_summary", "domains_for_house", "eligibility_reasons",
    "eligibility_summary", "evaluate_natal_promise", "event_candidates",
    "evidence_appendix", "explain_activation", "explain_confidence",
    "filter_results", "format_synthesis_report", "natal_snapshot_id",
    "prediction_eligibility", "resolve_rules", "resolve_sources",
    "spec_for", "synthesis_appendix", "synthesis_confidence", "synthesise",
    "transit_activation", "varga_confirmation", "weakest_confidence",
]
