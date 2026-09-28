"""
Deterministic synthesis (V1.5 Parts 14, 16, 21, 24, 29)
---------------------------------------------------------
Where the three layers meet, under one rule:

    Natal Promise  →  Dasha Activation  →  Transit Trigger

THE HIERARCHY IS A CONSTRAINT, NOT AN ORDERING

    It does not mean "consider these in this order". It means a lower layer
    cannot supply what a higher one lacks. A transit over the natal 10th in
    a chart with no career indication produces transit FACTS and no career
    evidence, and `_gated_transit_evidence` is where that is enforced —
    once, in one place, rather than trusted to every caller.

    The failure this prevents is the standard one in predictive software:
    Saturn arrives on the 7th cusp, the engine finds a "marriage transit",
    and a reader is told something about a chart that never indicated
    marriage in the first place.

PART 29: NO LLM DECIDES ANYTHING HERE

    Not which event is predicted, whether a yoga exists, which domain is
    activated, whether evidence is supportive, the timing window, or the
    confidence. Every one of those comes from the deterministic code in this
    package. Run twice on the same inputs it returns the same object, and a
    test asserts exactly that.

WHAT THIS MODULE STILL DOES NOT DO

    It does not say what any of it means. `SynthesisResult` has no field for
    a verdict, a recommendation or a sentence about a person's life, and
    V1.5 ships no module that produces one.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional, Sequence

from .activation import (
    DASHA_METHODOLOGY_ID, TRANSIT_METHODOLOGY_ID, activations_for_domain,
    dasha_activations_for_domain, dasha_stack_activations, transit_activation,
)
from ..gochara import (
    GocharaVerdict, evaluate_gochara, strict_eligible_judgements,
)
from ..gochara.rules import METHODOLOGY_ID as GOCHARA_METHODOLOGY_ID
from .domain_evidence import FactorType
from .domains import (
    DOMAINS, HIGH_STAKES_NOTE, Domain, domain_mapping_summary, spec_for,
)
from .eligibility import eligibility_summary, filter_results
from .evidence import build_lineage, evidence_appendix
from .models import (
    ActivationLevel, ChartReliability, DomainEvidence, EvidenceConfidence,
    EvidenceDirection, EvidenceLayer, PredictionEligibility, SynthesisProfile,
    SynthesisResult,
)
from .natal_promise import METHODOLOGY_ID as NATAL_METHODOLOGY_ID
from .natal_promise import evaluate_natal_promise
from .reliability import build_reliability
from .scoring import (
    activation_level, explain_activation, explain_confidence,
    synthesis_confidence,
)

# SOFTWARE HEURISTIC weights for the timing layers.
W_DASHA_LORD_OWNS_HOUSE = 0.70
W_DASHA_LORD_OCCUPIES = 0.55
W_DASHA_LORD_YOGA = 0.65
W_DASHA_LORD_WEAK = 0.45
W_TRANSIT_OVER_HOUSE = 0.35
W_TRANSIT_ON_NATAL_POINT = 0.45
W_TRANSIT_DASHA_LORD = 0.55

# V1.8. A transit admitted through a fully implemented located rule carries
# more weight than one admitted because the engine noticed a geometric
# relationship — but it is still a SOFTWARE HEURISTIC weight, and it is
# deliberately not the highest number in this table. The natal layer holds
# the promise; Phaladīpikā 20.34 says the daśā lord NOURISHES a bhāva, which
# is a modulation of something already there.
W_GOCHARA_SOURCED = 0.60


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


@dataclass
class SynthesisContext:
    """
    Everything one synthesis run consumed and produced.

    Separate from TimingContext, which is V1.4's factual object, and from the
    natal ChartSnapshot, which Part 25 requires to stay immutable and
    date-free.
    """

    moment: datetime.datetime
    profile: SynthesisProfile
    reliability: ChartReliability
    results: dict = field(default_factory=dict)
    dasha_activations: list = field(default_factory=list)
    transit_activations: list = field(default_factory=list)
    dasha_stack: dict = field(default_factory=dict)
    excluded_rules: list = field(default_factory=list)
    eligibility_counts: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    gochara: object = None

    def result_for(self, domain) -> Optional[SynthesisResult]:
        return self.results.get(spec_for(domain).domain.value)

    @property
    def active_domains(self) -> list:
        return [r for r in self.results.values()
                if r.activation is not ActivationLevel.INACTIVE]

    def to_dict(self) -> dict:
        return {
            "datetime": self.moment.isoformat(),
            "synthesis_profile": self.profile.value,
            "reliability": self.reliability.to_dict(),
            "dasha_stack": self.dasha_stack,
            "dasha_activation": [a.to_dict() for a in self.dasha_activations],
            "transit_activation": [
                a.to_dict() for a in self.transit_activations],
            "gochara": (self.gochara.to_dict() if self.gochara is not None
                        else None),
            "domain_results": {
                name: result.to_dict()
                for name, result in sorted(self.results.items())},
            "excluded_by_profile": list(self.excluded_rules),
            "rule_eligibility": self.eligibility_counts,
            "domain_model": domain_mapping_summary(),
            "warnings": list(self.warnings),
            "note": (
                "Deterministic synthesis. Activation bands and confidence "
                "bands are software conventions, not classical categories "
                "and not probabilities. No interpretation, no prose, no "
                "recommendation."),
        }


# ── the layer-gating rules ───────────────────────────────────────────────────

def _dasha_evidence(spec, activations, features,
                    profile: SynthesisProfile,
                    base_conf: EvidenceConfidence) -> list[DomainEvidence]:
    """Dasha evidence for one domain, from the running stack."""
    out: list[DomainEvidence] = []
    houses = set(spec.all_houses)

    # In strict, a dasha lord reaches a domain by two possible routes, and
    # each has to be sourced in its own right: it RULES a house whose
    # house-lord mapping is qualified, or it IS a kāraka whose attribution is
    # qualified. A Venus dasha bears on MARRIAGE for both reasons — BPHS 11.8
    # gives the 7th as jāyā and 32.23 gives the wife from Venus — and a
    # Mercury dasha bears on EDUCATION for neither, since the 4th-house
    # mapping V1.5 used was not located and Mercury's kāraka attribution is
    # to the maternal uncle.
    strict = profile is SynthesisProfile.STRICT
    qualified_karakas = {
        m.factor for m in spec.mappings
        if m.factor_type is FactorType.KARAKA and m.is_source_qualified}

    for activation in activations:
        if spec.domain.value not in activation.activated_domains:
            continue

        touched = sorted(set(activation.activated_houses) & houses)
        if strict:
            touched = [h for h in touched
                       if spec.qualifies_for_strict(FactorType.HOUSE_LORD, h)]
            if not touched and activation.planet not in qualified_karakas:
                continue
        if not touched:
            continue

        # A dasha lord owning the domain's primary house is a stronger
        # activation claim than one merely owning a secondary house, and
        # occupancy is weaker than lordship. Engine convention.
        if spec.primary_house in touched:
            weight = W_DASHA_LORD_OWNS_HOUSE
        elif activation.occupied_house in houses:
            weight = W_DASHA_LORD_OCCUPIES
        else:
            weight = W_DASHA_LORD_WEAK

        ratio = activation.strength_evidence.get("shadbala_ratio")
        direction = EvidenceDirection.SUPPORTIVE
        if activation.functional_nature == "malefic":
            direction = EvidenceDirection.CHALLENGING
        elif ratio is not None and ratio < 1.0:
            direction = EvidenceDirection.MIXED

        out.append(DomainEvidence(
            domain=spec.domain.value,
            factor_id=f"dasha_{activation.level}_{activation.planet}",
            layer=EvidenceLayer.DASHA, source_type="dasha_lord",
            direction=direction, magnitude=weight,
            confidence=min((activation.confidence, base_conf),
                           key=lambda c: c.rank),
            explanation_key="dasha_lord_activates_house",
            explanation=(
                f"{activation.level.capitalize()} lord {activation.planet} "
                f"rules or occupies the "
                f"{', '.join(_ordinal(h) for h in touched)}"
                + (f" and is {activation.functional_nature} for this Lagna"
                   if activation.functional_nature else "") + "."),
            planets=(activation.planet,), houses=tuple(touched),
            methodology_id=DASHA_METHODOLOGY_ID,
            calculation_ids=("timing/vimshottari",),
            eligibility=PredictionEligibility.EXPERIMENTAL))

        for rule_id in activation.yogas_activated:
            out.append(DomainEvidence(
                domain=spec.domain.value,
                factor_id=f"dasha_yoga_{activation.planet}_{rule_id}",
                layer=EvidenceLayer.DASHA, source_type="dasha_yoga",
                direction=EvidenceDirection.SUPPORTIVE,
                magnitude=W_DASHA_LORD_YOGA,
                confidence=base_conf,
                explanation_key="dasha_lord_carries_yoga",
                explanation=(
                    f"{activation.level.capitalize()} lord "
                    f"{activation.planet} participates in {rule_id}."),
                planets=(activation.planet,), rule_ids=(rule_id,),
                methodology_id=DASHA_METHODOLOGY_ID,
                calculation_ids=("timing/vimshottari", "rules/engine")))
    return out


def _gochara_evidence(spec, judgements, base_conf: EvidenceConfidence
                      ) -> tuple[list[DomainEvidence], list[str]]:
    """
    V1.8 Part 7. The only route by which a transit reaches STRICT synthesis.

    Three independent gates, and all three have to hold:

        the JUDGEMENT is strict-eligible          — every clause of the
                                                    located rule was
                                                    implemented and met
        the judgement NAMES A BHĀVA               — chapter 26 does not, so
                                                    it stops here
        the bhāva→domain mapping is SOURCED       — `qualifies_for_strict`,
                                                    the same gate the natal
                                                    and dasha layers use

    The third is the one that would be easiest to skip and is the reason
    V1.5's ladder exists. "Phaladīpikā 20.34 says the daśā lord nourishes
    the bhāva it transits" plus "this engine associates the 4th with
    property" does not make a sourced claim about property unless the second
    half is sourced too.
    """
    if not judgements:
        return [], []

    out: list[DomainEvidence] = []
    refused: list[str] = []

    for judgement in judgements:
        touched = sorted(
            house for house in judgement.houses_affected
            if spec.qualifies_for_strict(FactorType.HOUSE, house))
        if not touched:
            unsourced = sorted(judgement.houses_affected)
            if unsourced:
                refused.append(
                    f"{judgement.transit_planet}: {judgement.rule_id} names "
                    f"the {', '.join(_ordinal(h) for h in unsourced)}, and "
                    f"this domain's mapping for that bhāva is not "
                    f"source-qualified, so the transit does not reach it.")
            continue

        if judgement.verdict is GocharaVerdict.FAVOURABLE:
            direction = EvidenceDirection.SUPPORTIVE
        elif judgement.verdict is GocharaVerdict.UNFAVOURABLE:
            direction = EvidenceDirection.CHALLENGING
        else:
            # OBSTRUCTED means an auspicious result was cancelled. The
            # verses do not say it becomes an evil result, so it is not
            # recorded as one.
            direction = EvidenceDirection.NEUTRAL

        out.append(DomainEvidence(
            domain=spec.domain.value,
            factor_id=f"{judgement.rule_id}_{judgement.transit_planet}",
            layer=EvidenceLayer.TRANSIT, source_type="gochara_rule",
            direction=direction, magnitude=W_GOCHARA_SOURCED,
            confidence=base_conf,
            explanation_key=judgement.explanation_key,
            explanation=judgement.explanation,
            planets=(judgement.transit_planet,), houses=tuple(touched),
            methodology_id=GOCHARA_METHODOLOGY_ID,
            calculation_ids=("gochara/engine", "timing/vimshottari",
                             "strength/shadbala"),
            source_ref_ids=tuple(judgement.source_ref_ids),
            eligibility=PredictionEligibility.VERIFIED_STRICT,
            reliability_warnings=tuple(judgement.limitations)))

    return out, refused


def _gated_transit_evidence(spec, activations, natal_evidence,
                            base_conf: EvidenceConfidence,
                            strict: bool = False,
                            gochara_judgements=()
                            ) -> tuple[list[DomainEvidence], list[str]]:
    """
    Part 14's central constraint, in one place.

    Returns (evidence, notes). When the natal layer is empty the evidence
    list is empty too, and the note says so — a transit is recorded as a fact
    in the context and is refused as evidence for a domain the chart does not
    indicate.
    """
    if not natal_evidence:
        if activations:
            return [], [
                f"{len(activations)} transit relationship(s) touch this "
                f"domain and none contributes evidence: there is no natal "
                f"indication for a transit to activate. Part 14 — a transit "
                f"triggers a promise and cannot create one."]
        return [], []

    if strict:
        # CHANGED IN V1.8, after three releases of refusing.
        #
        # V1.5 refused because the house→domain mapping had no witness.
        # V1.6 found the mappings and still refused, because "the 10th
        # signifies career" and "a graha transiting the 10th affects career"
        # are different claims and only the first was located. V1.7 located
        # the second — Phaladīpikā 26 and 20.34-35 — and still refused,
        # because a located source is a specification, not permission.
        #
        # V1.8 implemented it. The refusal is now conditional on the rule
        # rather than blanket, and the condition is strict enough that
        # chapter 26 — the larger and more famous of the two passages —
        # still does not pass it. See `_gochara_evidence`.
        evidence, refused = _gochara_evidence(
            spec, gochara_judgements, base_conf)
        notes = list(refused)
        if not evidence:
            notes.append(
                "Strict synthesis admits no transit evidence for this "
                "domain. Transits reach strict only through a rule whose "
                "every located condition is implemented AND which names a "
                "bhāva; Phaladīpikā 26 judges the transit in the Chandra's "
                "frame without naming one, so it cannot reach a life area.")
        return evidence, notes

    out: list[DomainEvidence] = []
    for activation in activations:
        if activation.relation == "over_house_from_natal_moon":
            continue

        if activation.is_dasha_lord:
            weight = W_TRANSIT_DASHA_LORD
        elif activation.relation == "over_natal_house":
            weight = W_TRANSIT_OVER_HOUSE
        else:
            weight = W_TRANSIT_ON_NATAL_POINT

        out.append(DomainEvidence(
            domain=spec.domain.value,
            factor_id=(f"transit_{activation.transit_planet}_"
                       f"{activation.relation}_{activation.natal_target}"),
            layer=EvidenceLayer.TRANSIT, source_type="transit",
            direction=EvidenceDirection.NEUTRAL,
            magnitude=weight, confidence=base_conf,
            explanation_key=activation.relation,
            explanation=activation.explanation,
            planets=(activation.transit_planet,),
            houses=((activation.house_touched,)
                    if activation.house_touched else ()),
            methodology_id=TRANSIT_METHODOLOGY_ID,
            calculation_ids=("transits/calculator",
                             "transits/relationships"),
            eligibility=PredictionEligibility.EXPERIMENTAL,
            reliability_warnings=(
                "No Gochara rule is applied. This records that a transit "
                "touches the domain, not that it is favourable: the engine "
                "has no located source for transit judgement and V1.4 "
                "recorded Gochara, Vedha and Sade Sati as out of scope.",)))
    return out, []


# ── the entry point ──────────────────────────────────────────────────────────

def synthesise(features, *, moment: datetime.datetime,
               yoga_results=None,
               dasha=None,
               transit_snapshot=None,
               ashtakavarga=None,
               sensitivity=None,
               reliability: Optional[ChartReliability] = None,
               profile: SynthesisProfile = SynthesisProfile.STANDARD,
               domains: Optional[Sequence] = None,
               birth_time_precision_seconds: Optional[int] = None
               ) -> SynthesisContext:
    """
    Run deterministic synthesis for one moment.

    `features` is a ChartFeatures with Shadbala attached where available.
    Every other input may be None, and a missing input narrows the result
    rather than being fabricated: no dasha means no dasha layer, which caps
    every domain at BACKGROUND.
    """
    if isinstance(profile, str):
        profile = SynthesisProfile(profile)

    if reliability is None:
        kwargs = {}
        if birth_time_precision_seconds is not None:
            kwargs["birth_time_precision_seconds"] = (
                birth_time_precision_seconds)
            kwargs["precision_basis"] = "supplied by caller"
        reliability = build_reliability(sensitivity, **kwargs)

    context = SynthesisContext(
        moment=moment, profile=profile, reliability=reliability)
    context.warnings.extend(reliability.warnings)

    # Which rules the profile admits, recorded once for the whole run.
    if yoga_results:
        _admitted, excluded = filter_results(yoga_results, profile)
        context.excluded_rules = excluded
        context.eligibility_counts = eligibility_summary(
            r.id for r in yoga_results)

    # ── timing layers, computed once and shared across domains ──────────────
    dasha_lords: tuple = ()
    if dasha is not None:
        context.dasha_stack = dasha.get_dasha_stack_at(moment)
        context.dasha_activations = dasha_stack_activations(
            dasha, moment, features, yoga_results=yoga_results,
            profile=profile)
        dasha_lords = tuple(a.planet for a in context.dasha_activations)
    else:
        context.warnings.append(
            "No dasha was supplied, so no domain can rise above BACKGROUND: "
            "the activation hierarchy needs the dasha layer to reach ACTIVE.")

    if transit_snapshot is not None:
        context.transit_activations = transit_activation(
            transit_snapshot, features, dasha_lords=dasha_lords)

        # V1.8. The textual transit layer, computed ONCE for the whole run
        # rather than per domain: the rules are about a graha's placement,
        # not about a life area, and re-deriving them seventeen times would
        # have been both slower and an invitation to drift.
        context.gochara = evaluate_gochara(
            transit_snapshot, features, dasha_stack=context.dasha_stack)
        context.warnings.extend(context.gochara.notes)

    strict_gochara = (strict_eligible_judgements(context.gochara)
                      if context.gochara is not None else [])

    selected = list(domains) if domains else list(DOMAINS)

    for key in selected:
        spec = spec_for(key)
        natal, vargas, excluded = evaluate_natal_promise(
            spec.domain, features, yoga_results=yoga_results,
            ashtakavarga=ashtakavarga, reliability=reliability,
            profile=profile)

        base_conf = EvidenceConfidence.MEDIUM
        if natal:
            base_conf = max((e.confidence for e in natal),
                            key=lambda c: c.rank)

        dasha_ev = _dasha_evidence(
            spec, dasha_activations_for_domain(
                context.dasha_activations, spec.domain),
            features, profile, base_conf)

        transit_ev, gate_notes = _gated_transit_evidence(
            spec, activations_for_domain(
                context.transit_activations, spec.domain),
            natal, base_conf, strict=profile is SynthesisProfile.STRICT,
            gochara_judgements=strict_gochara)

        combined = natal + dasha_ev + transit_ev
        level = activation_level(combined)

        boundary = [
            f"{name} is at an unresolved astronomical boundary"
            for name in {p for e in combined for p in e.planets}
            if (features.planet(name) is not None
                and features.planet(name).boundary_warning)]

        confidence = synthesis_confidence(
            combined, vargas, reliability=reliability,
            boundary_warnings=boundary)

        warnings = list(gate_notes) + boundary
        for item in combined:
            warnings.extend(item.reliability_warnings)
        for varga in vargas:
            warnings.extend(varga.reliability_warnings)
        warnings.extend(reliability.warnings)

        methodology = {
            "domain_spec": spec.to_dict(),
            "natal": NATAL_METHODOLOGY_ID,
            "dasha": DASHA_METHODOLOGY_ID,
            "transit": TRANSIT_METHODOLOGY_ID,
            "gochara": GOCHARA_METHODOLOGY_ID,
            "activation": explain_activation(combined),
            "confidence": explain_confidence(combined, vargas, boundary),
            "profile": profile.value,
            "reference_space": spec.reference_space.value,
        }

        result = SynthesisResult(
            domain=spec.domain.value, profile=profile,
            activation=level, confidence=confidence,
            natal_evidence=natal, dasha_evidence=dasha_ev,
            transit_evidence=transit_ev, varga_evidence=vargas,
            methodology=methodology,
            source_ref_ids=tuple(sorted(
                {r for e in combined for r in e.source_ref_ids})),
            rule_ids=tuple(sorted(
                {r for e in combined for r in e.rule_ids})),
            reliability_warnings=sorted(set(warnings)),
            excluded_by_profile=excluded,
            notes=HIGH_STAKES_NOTE if spec.is_high_stakes else "")

        context.results[spec.domain.value] = result

    return context


def synthesis_lineages(context: SynthesisContext) -> list:
    return [build_lineage(r) for r in context.results.values()]


def synthesis_appendix(context: SynthesisContext) -> dict:
    return evidence_appendix(list(context.results.values()))
