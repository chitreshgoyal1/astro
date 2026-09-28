"""
Synthesis vocabulary (V1.5 Parts 3, 6, 7, 14, 15, 16, 18, 19, 20, 21)
-----------------------------------------------------------------------
The types the deterministic synthesis layer speaks in.

FIVE KINDS OF STATEMENT, KEPT APART

    ASTRONOMICAL FACT           where a graha is
    ASTROLOGICAL FEATURE        that it aspects the 10th, is combust, owns
                                the 4th — mechanical consequences of the
                                above under a named convention
    TEXTUAL RULE                what a located witness states
    SOFTWARE SYNTHESIS HEURISTIC  how this engine combines the above
    INTERPRETATION              what it means for a person

This module defines the fourth. Every enum in it is an engine convention and
none is a classical category: no text grades a domain INACTIVE or BACKGROUND,
and no text assigns MEDIUM confidence to anything. The names are chosen to be
obviously software vocabulary — `activation_level` rather than `phala`, and
ordinal bands rather than numbers — so that a reader is never invited to
mistake the output for a quotation.

The fifth kind, INTERPRETATION, is not produced here and is not produced
anywhere in V1.5.

WHAT IS DELIBERATELY ABSENT

    A probability. Part 15 and Part 20 both forbid one, for the same reason:
    this engine has never been tested against an outcome, so any number it
    printed next to "marriage" would be invented. `ActivationLevel` is
    ordinal, `EvidenceConfidence` is ordinal, and neither is a likelihood.
    Nothing in this module multiplies into a percentage, and a test asserts
    that no serialised field name implies one.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ── Part 3: eligibility ──────────────────────────────────────────────────────

class PredictionEligibility(str, Enum):
    """
    How far a rule is allowed to influence synthesis.

    Presence in the catalog buys nothing. This is computed from the source
    registry rather than declared, so a rule cannot be promoted by editing a
    list — only by producing evidence.
    """

    VERIFIED_STRICT = "VERIFIED_STRICT"
    SOURCE_LOCATED = "SOURCE_LOCATED"
    EXPERIMENTAL = "EXPERIMENTAL"
    DISABLED = "DISABLED"

    @property
    def rank(self) -> int:
        return _ELIGIBILITY_RANK[self]


_ELIGIBILITY_RANK = {
    PredictionEligibility.DISABLED: 0,
    PredictionEligibility.EXPERIMENTAL: 1,
    PredictionEligibility.SOURCE_LOCATED: 2,
    PredictionEligibility.VERIFIED_STRICT: 3,
}

ELIGIBILITY_MEANING = {
    PredictionEligibility.VERIFIED_STRICT:
        "Admitted to the evidence-gated rule profile: a Sanskrit-tier witness "
        "with an edition and a locator, a textual condition, a software "
        "condition mapped to it, a test, and no registered conflict.",
    PredictionEligibility.SOURCE_LOCATED:
        "A witness has been located and read, and something is still open — "
        "witnesses disagree, or the mapping is not complete. Usable where the "
        "profile says so, never in strict.",
    PredictionEligibility.EXPERIMENTAL:
        "No located witness, or a known divergence from one. In common use "
        "and unverified. Admitted only to the experimental profile, and the "
        "output says so.",
    PredictionEligibility.DISABLED:
        "Must not influence synthesis at any profile. Reserved for rules "
        "whose implementation is known to contradict the text they cite.",
}


class SynthesisProfile(str, Enum):
    """Part 21. Every result states which of these produced it."""

    STRICT = "strict"
    STANDARD = "standard"
    EXPERIMENTAL = "experimental"

    @property
    def admits(self) -> tuple[PredictionEligibility, ...]:
        return _PROFILE_ADMITS[self]

    def accepts(self, eligibility: PredictionEligibility) -> bool:
        return eligibility in self.admits


_PROFILE_ADMITS: dict[SynthesisProfile, tuple[PredictionEligibility, ...]] = {
    SynthesisProfile.STRICT: (
        PredictionEligibility.VERIFIED_STRICT,),
    SynthesisProfile.STANDARD: (
        PredictionEligibility.VERIFIED_STRICT,
        PredictionEligibility.SOURCE_LOCATED),
    SynthesisProfile.EXPERIMENTAL: (
        PredictionEligibility.VERIFIED_STRICT,
        PredictionEligibility.SOURCE_LOCATED,
        PredictionEligibility.EXPERIMENTAL),
}

PROFILE_MEANING = {
    SynthesisProfile.STRICT:
        "Only evidence-qualified rules. Small, and often silent on a domain "
        "entirely. A blank strict result is a real answer: it says this "
        "engine has no sourced basis for saying anything.",
    SynthesisProfile.STANDARD:
        "Documented methodology plus implementation-matched sources where "
        "available. The default, and still not a claim of validation.",
    SynthesisProfile.EXPERIMENTAL:
        "Includes explicitly unverified rules. Every result carries the "
        "profile, so an experimental finding can never be quoted as though "
        "it were a strict one.",
}


# ── Part 7: evidence direction ───────────────────────────────────────────────

class EvidenceDirection(str, Enum):
    """
    SOFTWARE SYNTHESIS LABELS, not classical quotations.

    No text says a placement is "SUPPORTIVE". These four words are how this
    engine records the sign of a factor so that supportive and challenging
    evidence can be reported side by side (Part 16) instead of being averaged
    into a verdict.
    """

    SUPPORTIVE = "SUPPORTIVE"
    CHALLENGING = "CHALLENGING"
    MIXED = "MIXED"
    NEUTRAL = "NEUTRAL"


class EvidenceConfidence(str, Enum):
    """
    Part 20. How much weight the evidence itself can bear.

    Deliberately NOT a probability and deliberately independent of
    ActivationLevel: a domain can be STRONGLY_ACTIVE with LOW confidence when
    the activation rests on a D60 placement and the birth time is known only
    to the minute.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNRESOLVED = "UNRESOLVED"

    @property
    def rank(self) -> int:
        return _CONFIDENCE_RANK[self]


_CONFIDENCE_RANK = {
    EvidenceConfidence.UNRESOLVED: 0,
    EvidenceConfidence.LOW: 1,
    EvidenceConfidence.MEDIUM: 2,
    EvidenceConfidence.HIGH: 3,
}


def weakest_confidence(values) -> EvidenceConfidence:
    """A conclusion is no more confident than its least confident input."""
    values = list(values)
    if not values:
        return EvidenceConfidence.UNRESOLVED
    return min(values, key=lambda c: c.rank)


# ── Part 15: activation ──────────────────────────────────────────────────────

class ActivationLevel(str, Enum):
    """
    SOFTWARE SYNTHESIS CONVENTION. Ordinal, reproducible, not a probability.

    MIXED is not a point on the scale. It records that supportive and
    challenging evidence are both substantial, which is a different statement
    from "moderately active" and must not collapse into one.
    """

    INACTIVE = "INACTIVE"
    BACKGROUND = "BACKGROUND"
    ACTIVE = "ACTIVE"
    STRONGLY_ACTIVE = "STRONGLY_ACTIVE"
    MIXED = "MIXED"


ACTIVATION_MEANING = {
    ActivationLevel.INACTIVE:
        "No natal indication for this domain, or none that the active "
        "profile admits.",
    ActivationLevel.BACKGROUND:
        "A natal indication exists and nothing currently activates it.",
    ActivationLevel.ACTIVE:
        "A natal indication exists and the current dasha activates it.",
    ActivationLevel.STRONGLY_ACTIVE:
        "Natal indication, dasha activation and transit trigger agree.",
    ActivationLevel.MIXED:
        "Substantial evidence in both directions. Reported as such rather "
        "than resolved.",
}


# ── Part 7: the evidence record ──────────────────────────────────────────────

class EvidenceLayer(str, Enum):
    """Which layer of the Part 14 hierarchy produced a piece of evidence."""

    NATAL = "NATAL"
    DASHA = "DASHA"
    TRANSIT = "TRANSIT"


@dataclass(frozen=True)
class DomainEvidence:
    """
    One factor bearing on one domain.

    `explanation_key` is a stable identifier for the KIND of factor, not a
    sentence. Part 29 reserves verbalisation for a later LLM layer, and a key
    is what that layer will need; `explanation` carries the engine's own
    plain rendering for the text report, and neither is a prediction.

    `magnitude` is an engine weight in [0, 1] and is labelled
    SOFTWARE_HEURISTIC wherever it is serialised. Part 10 requires that: no
    text assigns a number to "the 10th lord is exalted".
    """

    domain: str
    factor_id: str
    layer: EvidenceLayer
    source_type: str                     # "house_lord" | "yoga" | "shadbala" …
    direction: EvidenceDirection
    magnitude: float
    confidence: EvidenceConfidence
    explanation_key: str
    explanation: str = ""
    planets: tuple[str, ...] = ()
    houses: tuple[int, ...] = ()
    chart: str = "D1"
    source_ref_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    methodology_id: str = ""
    calculation_ids: tuple[str, ...] = ()
    eligibility: PredictionEligibility = PredictionEligibility.EXPERIMENTAL
    weighting_basis: str = "SOFTWARE_HEURISTIC"
    reliability_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "factor_id": self.factor_id,
            "layer": self.layer.value,
            "source_type": self.source_type,
            "direction": self.direction.value,
            "magnitude": round(self.magnitude, 3),
            "weighting_basis": self.weighting_basis,
            "confidence": self.confidence.value,
            "explanation_key": self.explanation_key,
            "explanation": self.explanation,
            "planets": list(self.planets),
            "houses": list(self.houses),
            "chart": self.chart,
            "source_ref_ids": list(self.source_ref_ids),
            "rule_ids": list(self.rule_ids),
            "methodology_id": self.methodology_id,
            "calculation_ids": list(self.calculation_ids),
            "prediction_eligibility": self.eligibility.value,
            "reliability_warnings": list(self.reliability_warnings),
        }


@dataclass(frozen=True)
class VargaEvidence:
    """
    Part 9. A divisional chart CONFIRMING or qualifying a natal theme.

    A varga never originates a domain result here. `reliability` is derived
    from birth-time sensitivity, which is why D60 does not outrank D1 simply
    for being finer: a 39-second instability makes it the least reliable
    input in the chart, not the most precise one.
    """

    domain: str
    chart: str
    factor: str
    direction: EvidenceDirection
    reliability: EvidenceConfidence
    confirms: bool
    explanation: str = ""
    planets: tuple[str, ...] = ()
    methodology_id: str = ""
    source_ref_ids: tuple[str, ...] = ()
    reliability_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "chart": self.chart,
            "factor": self.factor,
            "direction": self.direction.value,
            "reliability": self.reliability.value,
            "confirms_natal_theme": self.confirms,
            "explanation": self.explanation,
            "planets": list(self.planets),
            "methodology_id": self.methodology_id,
            "source_ref_ids": list(self.source_ref_ids),
            "reliability_warnings": list(self.reliability_warnings),
        }


# ── Part 12: dasha activation ────────────────────────────────────────────────

@dataclass(frozen=True)
class DashaActivation:
    """What one dasha lord, at one level, activates. Facts, not prediction."""

    planet: str
    level: str                           # mahadasha | antardasha | …
    activated_houses: tuple[int, ...] = ()
    activated_domains: tuple[str, ...] = ()
    yogas_activated: tuple[str, ...] = ()
    occupied_house: Optional[int] = None
    dispositor_chain: tuple[str, ...] = ()
    functional_nature: str = ""
    strength_evidence: dict = field(default_factory=dict)
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    period_start: Optional[datetime.datetime] = None
    period_end: Optional[datetime.datetime] = None

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "level": self.level,
            "activated_houses": list(self.activated_houses),
            "activated_domains": list(self.activated_domains),
            "yogas_activated": list(self.yogas_activated),
            "occupied_house": self.occupied_house,
            "dispositor_chain": list(self.dispositor_chain),
            "functional_nature": self.functional_nature,
            "strength_evidence": self.strength_evidence,
            "confidence": self.confidence.value,
            "period_start": (self.period_start.isoformat()
                             if self.period_start else None),
            "period_end": (self.period_end.isoformat()
                           if self.period_end else None),
        }


# ── Part 13: transit activation ──────────────────────────────────────────────

@dataclass(frozen=True)
class TransitActivation:
    """
    One factual transit relationship, tagged with what it touches.

    Part 13: a transit TRIGGERS, it does not promise. Nothing in this record
    can create a domain result on its own, and `engine.py` enforces that.

    Degree proximity and the classical sign relationship are separate fields
    and neither is computed from the other, continuing the V1.4 discipline.
    """

    transit_planet: str
    relation: str                        # "over_natal_house" | "drishti" | …
    natal_target: str
    target_kind: str
    house_touched: Optional[int] = None
    domains_touched: tuple[str, ...] = ()
    same_sign: bool = False
    angular_separation: Optional[float] = None
    within_orb: bool = False
    graha_drishti: bool = False
    drishti_type: Optional[str] = None
    is_dasha_lord: bool = False
    retrograde: bool = False
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "transit_planet": self.transit_planet,
            "relation": self.relation,
            "natal_target": self.natal_target,
            "target_kind": self.target_kind,
            "house_touched": self.house_touched,
            "domains_touched": list(self.domains_touched),
            "same_sign": self.same_sign,
            "angular_separation": (None if self.angular_separation is None
                                   else round(self.angular_separation, 4)),
            "within_orb": self.within_orb,
            "graha_drishti": self.graha_drishti,
            "drishti_type": self.drishti_type,
            "is_dasha_lord": self.is_dasha_lord,
            "retrograde": self.retrograde,
            "explanation": self.explanation,
        }


# ── Part 14: the synthesis result ────────────────────────────────────────────

@dataclass
class SynthesisResult:
    """One domain, fully traced. Part 17: nothing here is a black box."""

    domain: str
    profile: SynthesisProfile
    activation: ActivationLevel
    confidence: EvidenceConfidence
    natal_evidence: list = field(default_factory=list)
    dasha_evidence: list = field(default_factory=list)
    transit_evidence: list = field(default_factory=list)
    varga_evidence: list = field(default_factory=list)
    methodology: dict = field(default_factory=dict)
    source_ref_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    reliability_warnings: list = field(default_factory=list)
    excluded_by_profile: list = field(default_factory=list)
    notes: str = ""

    @property
    def all_evidence(self) -> list:
        return (list(self.natal_evidence) + list(self.dasha_evidence)
                + list(self.transit_evidence))

    @property
    def supportive(self) -> list:
        return [e for e in self.all_evidence
                if e.direction is EvidenceDirection.SUPPORTIVE]

    @property
    def challenging(self) -> list:
        return [e for e in self.all_evidence
                if e.direction is EvidenceDirection.CHALLENGING]

    @property
    def has_conflicting_evidence(self) -> bool:
        """
        Part 16. True whenever ANY evidence runs both ways.

        Deliberately distinct from `ActivationLevel.MIXED`, which is the
        stronger claim that the two directions are close to balanced. Folding
        them together would mean either calling a domain MIXED on a single
        dissenting factor, or reporting eight supportive and three
        challenging factors with nothing to flag the three — and Part 16
        forbids the second.

        So both are published: this flag says the evidence is not unanimous,
        and the activation level says whether the disagreement is close
        enough to refuse a direction.
        """
        return bool(self.supportive) and bool(self.challenging)

    @property
    def mixed(self) -> bool:
        """Retained name for the Part 16 flag; see above."""
        return self.has_conflicting_evidence

    @property
    def has_natal_promise(self) -> bool:
        return bool(self.natal_evidence)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "synthesis_profile": self.profile.value,
            "activation": self.activation.value,
            "activation_is_software_convention": True,
            "confidence": self.confidence.value,
            "confidence_is_ordinal_band": True,
            "mixed": self.has_conflicting_evidence,
            "evidence_is_unanimous": not self.has_conflicting_evidence,
            "supportive": [e.to_dict() for e in self.supportive],
            "challenging": [e.to_dict() for e in self.challenging],
            "natal_evidence": [e.to_dict() for e in self.natal_evidence],
            "dasha_evidence": [e.to_dict() for e in self.dasha_evidence],
            "transit_evidence": [e.to_dict() for e in self.transit_evidence],
            "varga_evidence": [e.to_dict() for e in self.varga_evidence],
            "methodology": self.methodology,
            "source_ref_ids": list(self.source_ref_ids),
            "rule_ids": list(self.rule_ids),
            "reliability_warnings": list(self.reliability_warnings),
            "excluded_by_profile": list(self.excluded_by_profile),
            "notes": self.notes,
        }


# ── Parts 18 and 19: events and windows ──────────────────────────────────────

@dataclass(frozen=True)
class TimingWindow:
    """
    Part 19. A window with real boundaries, never an invented date.

    Every boundary here comes from something computed: a dasha period edge,
    a transit ingress, a station, or an exact aspect found by bisection. The
    `why` list names which, one entry per boundary, so a reader can check.
    """

    start: datetime.datetime
    end: datetime.datetime
    peak: Optional[datetime.datetime] = None
    why: tuple[str, ...] = ()
    boundary_sources: tuple[str, ...] = ()

    @property
    def duration_days(self) -> float:
        return (self.end - self.start).total_seconds() / 86400.0

    def contains(self, moment: datetime.datetime) -> bool:
        return self.start <= moment <= self.end

    def to_dict(self) -> dict:
        return {
            "window_start": self.start.isoformat(),
            "window_peak": self.peak.isoformat() if self.peak else None,
            "window_end": self.end.isoformat(),
            "duration_days": round(self.duration_days, 3),
            "why": list(self.why),
            "boundary_sources": list(self.boundary_sources),
        }


class EventType(str, Enum):
    """
    Part 18. Broad categories only.

    Part 24 governs what is NOT here: no death, no diagnosis, no pregnancy.
    HEALTH_ACTIVITY and LONGEVITY_FACTOR exist because the underlying
    calculation is preserved for scholarly completeness, and they are
    domain-level activation labels, not medical statements.
    """

    CAREER_CHANGE = "CAREER_CHANGE"
    CAREER_ADVANCEMENT = "CAREER_ADVANCEMENT"
    FINANCIAL_GAIN = "FINANCIAL_GAIN"
    FINANCIAL_PRESSURE = "FINANCIAL_PRESSURE"
    PROPERTY_ACTIVITY = "PROPERTY_ACTIVITY"
    RELATIONSHIP_ACTIVATION = "RELATIONSHIP_ACTIVATION"
    CHILDREN_ACTIVATION = "CHILDREN_ACTIVATION"
    EDUCATION_ACTIVITY = "EDUCATION_ACTIVITY"
    TRAVEL_ACTIVITY = "TRAVEL_ACTIVITY"
    FOREIGN_RESIDENCE_ACTIVITY = "FOREIGN_RESIDENCE_ACTIVITY"
    BUSINESS_ACTIVITY = "BUSINESS_ACTIVITY"
    LITIGATION_ACTIVITY = "LITIGATION_ACTIVITY"
    FAMILY_ACTIVITY = "FAMILY_ACTIVITY"
    SIBLING_ACTIVITY = "SIBLING_ACTIVITY"
    SPIRITUAL_ACTIVITY = "SPIRITUAL_ACTIVITY"
    HEALTH_ACTIVITY = "HEALTH_ACTIVITY"


@dataclass
class EventCandidate:
    """
    Part 18. A CANDIDATE: a window in which a domain is activated.

    Not a prediction and not prose. It says that this engine's rules place an
    activation of this domain in this window, and it carries everything
    needed to check that claim.
    """

    domain: str
    event_type: EventType
    window: TimingWindow
    activation: ActivationLevel
    confidence: EvidenceConfidence
    profile: SynthesisProfile
    evidence: list = field(default_factory=list)
    reliability_warnings: list = field(default_factory=list)
    source_ref_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    methodology_ids: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "event_type": self.event_type.value,
            "window": self.window.to_dict(),
            "activation": self.activation.value,
            "confidence": self.confidence.value,
            "synthesis_profile": self.profile.value,
            "evidence": [e.to_dict() for e in self.evidence],
            "reliability_warnings": list(self.reliability_warnings),
            "source_ref_ids": list(self.source_ref_ids),
            "rule_ids": list(self.rule_ids),
            "methodology_ids": list(self.methodology_ids),
            "notes": self.notes,
            "is_candidate_not_prediction": True,
        }


# ── Part 4: reliability ──────────────────────────────────────────────────────

@dataclass
class ChartReliability:
    """
    What the stated birth time can and cannot support.

    `birth_time_precision_seconds` is what the USER's input actually pins
    down, not what the arithmetic produces. An entered "14:32" is precise to
    a minute at best, and treating it as 14:32:00.000 is the single most
    common way astrology software manufactures confidence it has not earned.
    """

    birth_time_precision_seconds: int
    precision_basis: str = ""
    lagna_stable: bool = True
    d9_lagna_stable: bool = True
    d10_lagna_stable: bool = True
    d60_lagna_stable: bool = True
    bhava_stable: bool = True
    nakshatra_stable: bool = True
    unstable_items: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    sensitivity_available: bool = False

    def chart_is_stable(self, chart: str) -> Optional[bool]:
        """
        Whether a named divisional chart's Lagna holds within the precision.

        None means NOT MEASURED, never True. A caller that reads a missing
        measurement as stability would turn "we did not check" into "we
        checked and it is fine", which is the error this whole class exists
        to prevent.
        """
        if not self.sensitivity_available:
            return None
        return {
            "D1": self.lagna_stable,
            "D9": self.d9_lagna_stable,
            "D10": self.d10_lagna_stable,
            "D60": self.d60_lagna_stable,
        }.get(chart)

    def to_dict(self) -> dict:
        return {
            "birth_time_precision_seconds": self.birth_time_precision_seconds,
            "precision_basis": self.precision_basis,
            "sensitivity_available": self.sensitivity_available,
            "lagna_stable": self.lagna_stable,
            "nakshatra_stable": self.nakshatra_stable,
            "d9_lagna_stable": self.d9_lagna_stable,
            "d10_lagna_stable": self.d10_lagna_stable,
            "d60_lagna_stable": self.d60_lagna_stable,
            "bhava_stable": self.bhava_stable,
            "unstable_items": list(self.unstable_items),
            "warnings": list(self.warnings),
            "note": (
                "Describes what the ENTERED birth time supports. Not "
                "rectification: no time is suggested, preferred or scored."),
        }
