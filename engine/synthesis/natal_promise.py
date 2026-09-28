"""
Natal promise (V1.5 Parts 7, 9, 10, 11)
-----------------------------------------
The first and load-bearing layer: what the birth chart itself indicates for a
domain, before any question of timing.

WHY THIS LAYER MUST EXIST SEPARATELY

    Part 14 forbids a transit from manufacturing a prediction. That rule is
    only enforceable if "what the natal chart promises" is a distinct object
    that a transit layer can find EMPTY. So natal promise is computed first,
    from the birth chart alone, and `engine.py` refuses to raise a domain
    above BACKGROUND when this returns nothing.

NO UNIVERSAL FORMULA

    Part 7 is explicit: do not hard-code one formula and call it classical.
    Each factor is modelled on its own, carries its own weight, its own
    confidence and its own provenance, and the engine reports the factors. A
    caller who disagrees with a weight can see exactly which factor it
    attached to.

    The weights ARE arbitrary. They are labelled SOFTWARE_HEURISTIC
    everywhere they surface. No text assigns a number to "the 10th lord is
    exalted", and the ordering they produce is this engine's, not a
    tradition's.

WHAT EACH FACTOR IS DRAWN FROM

    house occupancy, house lord placement and dignity, karakas, aspects on
    the house, Shadbala of the participating grahas, Ashtakavarga bindus in
    the house, functional nature, dispositors, and eligible Yogas. All of
    them are V1.1-V1.4 facts; nothing is recomputed here, because two
    implementations of "is Mars aspecting the 10th" eventually disagree.
"""

from __future__ import annotations

from typing import Optional

from ..varga_metadata import range_limitation
from .domain_evidence import FactorType
from .domains import Domain, DomainSpec, spec_for
from .eligibility import prediction_eligibility
from .models import (
    DomainEvidence, EvidenceConfidence, EvidenceDirection, EvidenceLayer,
    PredictionEligibility, SynthesisProfile, VargaEvidence,
)
from .reliability import (
    ChartReliability, admits_chart, chart_reliability, chart_warnings,
)

# ── SOFTWARE HEURISTIC weights ───────────────────────────────────────────────
#
# Every number below is an engine convention. They are gathered here rather
# than scattered through the code so that a reader can see the whole of the
# engine's editorial judgement in one screen, and so that changing it is a
# visible act.
W_LORD_DIGNITY_STRONG = 0.70
W_LORD_DIGNITY_WEAK = 0.60
W_LORD_PLACEMENT_GOOD = 0.55
W_LORD_PLACEMENT_DUSTHANA = 0.60
W_BENEFIC_OCCUPANT = 0.45
W_MALEFIC_OCCUPANT = 0.45
W_KARAKA_DIGNITY = 0.50
W_KARAKA_AFFLICTED = 0.45
W_BENEFIC_ASPECT = 0.35
W_MALEFIC_ASPECT = 0.35
W_SHADBALA = 0.50
W_ASHTAKAVARGA = 0.45
W_YOGA_STRONG = 0.85
W_YOGA_PRESENT = 0.65
W_YOGA_CANCELLED = 0.40
W_VARGA_CONFIRM = 0.40

METHODOLOGY_ID = "natal_promise_v15"

# Ashtakavarga thresholds.
#
# Part 11: bindu counts are FACTS and the thresholds are not. Twenty-eight is
# the arithmetic mean of the 337-point sarva total over twelve houses, so it
# is a defensible neutral point and it is not a classical statement. The
# classical thresholds that circulate (30+ good, 25- poor) are widely taught
# and this engine has not located them in BPHS ch.66, which it has read.
SARVA_NEUTRAL = 28.0
SARVA_STRONG = 32.0
SARVA_WEAK = 24.0
ASHTAKAVARGA_THRESHOLD_BASIS = (
    "SOFTWARE_HEURISTIC. 28 is the arithmetic mean of the 337-bindu sarva "
    "total across twelve houses. BPHS ch.66 was read in V1.4 and gives the "
    "bindu tables, not thresholds for judging them.")


def _confidence_for(eligibility: PredictionEligibility,
                    chart_conf: EvidenceConfidence) -> EvidenceConfidence:
    """Evidence is no better than the weaker of its source and its chart."""
    by_source = {
        PredictionEligibility.VERIFIED_STRICT: EvidenceConfidence.HIGH,
        PredictionEligibility.SOURCE_LOCATED: EvidenceConfidence.MEDIUM,
        PredictionEligibility.EXPERIMENTAL: EvidenceConfidence.LOW,
        PredictionEligibility.DISABLED: EvidenceConfidence.UNRESOLVED,
    }[eligibility]
    return min((by_source, chart_conf), key=lambda c: c.rank)


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _evidence(spec: DomainSpec, factor_id: str, source_type: str,
              direction: EvidenceDirection, magnitude: float,
              confidence: EvidenceConfidence, explanation_key: str,
              explanation: str, **kwargs) -> DomainEvidence:
    return DomainEvidence(
        domain=spec.domain.value, factor_id=factor_id,
        layer=EvidenceLayer.NATAL, source_type=source_type,
        direction=direction, magnitude=magnitude, confidence=confidence,
        explanation_key=explanation_key, explanation=explanation,
        methodology_id=METHODOLOGY_ID, **kwargs)


# ── individual factors ───────────────────────────────────────────────────────

def _house_lord_factors(spec: DomainSpec, features,
                        base_conf: EvidenceConfidence) -> list[DomainEvidence]:
    out = []
    house = spec.primary_house
    lord = features.lord_of(house)
    if not lord:
        return out
    planet = features.planet(lord)
    if planet is None:
        return out

    if planet.exalted or planet.moolatrikona or planet.own_sign:
        out.append(_evidence(
            spec, f"lord{house}_dignity", "house_lord",
            EvidenceDirection.SUPPORTIVE, W_LORD_DIGNITY_STRONG, base_conf,
            "house_lord_dignified",
            f"The {_ordinal(house)} lord {lord} is {planet.dignity} in "
            f"{planet.sign_name}.",
            planets=(lord,), houses=(house,),
            calculation_ids=("features.dignity",)))
    elif planet.debilitated:
        out.append(_evidence(
            spec, f"lord{house}_debilitated", "house_lord",
            EvidenceDirection.CHALLENGING, W_LORD_DIGNITY_WEAK, base_conf,
            "house_lord_debilitated",
            f"The {_ordinal(house)} lord {lord} is debilitated in "
            f"{planet.sign_name}.",
            planets=(lord,), houses=(house,),
            calculation_ids=("features.dignity",)))

    dusthanas = (6, 8, 12)
    if planet.house in dusthanas and house not in dusthanas:
        out.append(_evidence(
            spec, f"lord{house}_in_dusthana", "house_lord",
            EvidenceDirection.CHALLENGING, W_LORD_PLACEMENT_DUSTHANA,
            base_conf, "house_lord_in_dusthana",
            f"The {_ordinal(house)} lord {lord} occupies the "
            f"{_ordinal(planet.house)}.",
            planets=(lord,), houses=(house, planet.house),
            calculation_ids=("features.lordships",)))
    elif planet.house in (1, 4, 5, 7, 9, 10, 11):
        out.append(_evidence(
            spec, f"lord{house}_well_placed", "house_lord",
            EvidenceDirection.SUPPORTIVE, W_LORD_PLACEMENT_GOOD, base_conf,
            "house_lord_well_placed",
            f"The {_ordinal(house)} lord {lord} occupies the "
            f"{_ordinal(planet.house)}.",
            planets=(lord,), houses=(house, planet.house),
            calculation_ids=("features.lordships",)))

    if planet.combust:
        out.append(_evidence(
            spec, f"lord{house}_combust", "house_lord",
            EvidenceDirection.CHALLENGING, W_LORD_DIGNITY_WEAK, base_conf,
            "house_lord_combust",
            f"The {_ordinal(house)} lord {lord} is combust at "
            f"{planet.sun_separation:.2f}° from Surya.",
            planets=(lord,), houses=(house,),
            calculation_ids=("features.combustion",)))
    return out


def _occupancy_factors(spec: DomainSpec, features,
                       base_conf: EvidenceConfidence) -> list[DomainEvidence]:
    out = []
    house = spec.primary_house
    bhava = features.houses.get(house)
    if bhava is None:
        return out
    for name in bhava.occupants:
        planet = features.planet(name)
        if planet is None:
            continue
        if planet.natural_benefic:
            out.append(_evidence(
                spec, f"h{house}_occupant_{name}", "occupancy",
                EvidenceDirection.SUPPORTIVE, W_BENEFIC_OCCUPANT, base_conf,
                "benefic_occupies_house",
                f"{name}, a natural benefic, occupies the {_ordinal(house)}.",
                planets=(name,), houses=(house,),
                calculation_ids=("features.occupancy",)))
        elif planet.natural_malefic:
            out.append(_evidence(
                spec, f"h{house}_occupant_{name}", "occupancy",
                EvidenceDirection.CHALLENGING, W_MALEFIC_OCCUPANT, base_conf,
                "malefic_occupies_house",
                f"{name}, a natural malefic, occupies the {_ordinal(house)}.",
                planets=(name,), houses=(house,),
                calculation_ids=("features.occupancy",)))
    return out


def _aspect_factors(spec: DomainSpec, features,
                    base_conf: EvidenceConfidence) -> list[DomainEvidence]:
    out = []
    house = spec.primary_house
    bhava = features.houses.get(house)
    if bhava is None:
        return out
    for name in bhava.aspecting_planets:
        planet = features.planet(name)
        if planet is None:
            continue
        if planet.natural_benefic:
            out.append(_evidence(
                spec, f"h{house}_aspect_{name}", "aspect",
                EvidenceDirection.SUPPORTIVE, W_BENEFIC_ASPECT, base_conf,
                "benefic_aspects_house",
                f"{name} casts graha drishti on the {_ordinal(house)}.",
                planets=(name,), houses=(house,),
                calculation_ids=("features.aspects",)))
        elif planet.natural_malefic:
            out.append(_evidence(
                spec, f"h{house}_aspect_{name}", "aspect",
                EvidenceDirection.CHALLENGING, W_MALEFIC_ASPECT, base_conf,
                "malefic_aspects_house",
                f"{name} casts graha drishti on the {_ordinal(house)}.",
                planets=(name,), houses=(house,),
                calculation_ids=("features.aspects",)))
    return out


def _karaka_factors(spec: DomainSpec, features,
                    base_conf: EvidenceConfidence) -> list[DomainEvidence]:
    out = []
    for karaka in spec.karakas:
        planet = features.planet(karaka.planet)
        if planet is None:
            continue
        # A karaka with a located witness is better evidence than one
        # without, and the difference shows in the confidence rather than
        # only in a footnote.
        conf = (base_conf if karaka.is_located
                else min((base_conf, EvidenceConfidence.LOW),
                         key=lambda c: c.rank))
        if planet.exalted or planet.own_sign or planet.moolatrikona:
            out.append(_evidence(
                spec, f"karaka_{karaka.planet}_dignified", "karaka",
                EvidenceDirection.SUPPORTIVE, W_KARAKA_DIGNITY, conf,
                "karaka_dignified",
                f"{karaka.planet}, karaka for {karaka.signifies}, is "
                f"{planet.dignity}.",
                planets=(karaka.planet,),
                source_ref_ids=karaka.source_ref_ids,
                calculation_ids=("features.dignity",)))
        elif planet.debilitated or planet.combust:
            state = "debilitated" if planet.debilitated else "combust"
            out.append(_evidence(
                spec, f"karaka_{karaka.planet}_afflicted", "karaka",
                EvidenceDirection.CHALLENGING, W_KARAKA_AFFLICTED, conf,
                "karaka_afflicted",
                f"{karaka.planet}, karaka for {karaka.signifies}, is {state}.",
                planets=(karaka.planet,),
                source_ref_ids=karaka.source_ref_ids,
                calculation_ids=("features.dignity",)))
    return out


def _shadbala_factors(spec: DomainSpec, features,
                      base_conf: EvidenceConfidence) -> list[DomainEvidence]:
    """
    Part 10. The ratio is retained, not reduced to a verdict.

    No rule here says "Shadbala > X means good". What it says is that the
    lord of the domain's primary house reaches, or fails to reach, the
    requirement BPHS 27.32-33 states for that graha — which is a comparison
    the witness itself defines, and the direction attached to it is the
    engine's.
    """
    out = []
    if features.shadbala is None:
        return out
    house = spec.primary_house
    lord = features.lord_of(house)
    if not lord:
        return out
    ratio = features.shadbala_ratio(lord)
    if ratio is None:
        return out

    result = getattr(features.shadbala, "results", {}).get(lord)
    status = getattr(result, "validation_status", "UNVERIFIED") if result \
        else "UNVERIFIED"
    detail = {
        "planet": lord,
        "total_virupa": round(getattr(result, "total_virupa", 0.0), 2),
        "required_virupa": getattr(result, "required_virupa", None),
        "ratio": round(ratio, 3),
        "component_status": status,
    }
    direction = (EvidenceDirection.SUPPORTIVE if ratio >= 1.0
                 else EvidenceDirection.CHALLENGING)
    out.append(_evidence(
        spec, f"shadbala_lord{house}", "shadbala", direction, W_SHADBALA,
        base_conf, "house_lord_shadbala",
        f"The {_ordinal(house)} lord {lord} has Shadbala {ratio:.2f}x its "
        f"BPHS 27.32 requirement "
        f"({detail['total_virupa']}/{detail['required_virupa']} virupas).",
        planets=(lord,), houses=(house,),
        source_ref_ids=("BPHS_27_SHADBALA",),
        calculation_ids=("shadbala/total",)))
    return out


def _ashtakavarga_factors(spec: DomainSpec, features, ashtakavarga,
                          base_conf: EvidenceConfidence
                          ) -> list[DomainEvidence]:
    """Part 11: the bindu count is the fact; the threshold is this engine's."""
    out = []
    if ashtakavarga is None:
        return out
    house = spec.primary_house
    try:
        bindus = ashtakavarga.sarva.bindus_in_house(
            house, ashtakavarga.lagna_sign)
    except Exception:
        return out
    if bindus is None:
        return out

    if bindus >= SARVA_STRONG:
        direction = EvidenceDirection.SUPPORTIVE
    elif bindus <= SARVA_WEAK:
        direction = EvidenceDirection.CHALLENGING
    else:
        direction = EvidenceDirection.NEUTRAL

    out.append(_evidence(
        spec, f"sarva_h{house}", "ashtakavarga", direction, W_ASHTAKAVARGA,
        base_conf, "sarvashtakavarga_bindus",
        f"The {_ordinal(house)} holds {bindus} sarvashtakavarga bindus "
        f"(engine neutral point {SARVA_NEUTRAL:g}).",
        houses=(house,), source_ref_ids=("BPHS_66_ASHTAKAVARGA",),
        calculation_ids=("ashtakavarga/sarva",),
        weighting_basis="SOFTWARE_HEURISTIC"))
    return out


def _yoga_factors(spec: DomainSpec, features, yoga_results,
                  profile: SynthesisProfile,
                  base_conf: EvidenceConfidence
                  ) -> tuple[list[DomainEvidence], list[dict]]:
    """
    Part 23's gate, applied. A yoga contributes only if its evidence allows.
    """
    out: list[DomainEvidence] = []
    excluded: list[dict] = []
    if not yoga_results:
        return out, excluded

    houses = set(spec.all_houses)
    for result in yoga_results:
        if not result.present:
            continue
        touches = (set(result.houses) & houses) or (
            result.category in spec.relevant_yoga_categories)
        if not touches:
            continue

        eligibility = prediction_eligibility(result.id)
        if not profile.accepts(eligibility):
            excluded.append({
                "rule_id": result.id, "name": result.name,
                "domain": spec.domain.value,
                "prediction_eligibility": eligibility.value,
                "reason": (
                    f"the {profile.value} profile does not admit "
                    f"{eligibility.value} rules"),
            })
            continue

        if result.status.value == "PRESENT_BUT_CANCELLED":
            direction = EvidenceDirection.MIXED
            weight = W_YOGA_CANCELLED
        elif result.status.value == "PRESENT_AND_STRONG":
            direction = EvidenceDirection.SUPPORTIVE
            weight = W_YOGA_STRONG
        elif result.category in ("arishta",):
            direction = EvidenceDirection.CHALLENGING
            weight = W_YOGA_PRESENT
        else:
            direction = EvidenceDirection.SUPPORTIVE
            weight = W_YOGA_PRESENT

        out.append(_evidence(
            spec, f"yoga_{result.id}", "yoga", direction, weight,
            _confidence_for(eligibility, base_conf), "yoga_present",
            f"{result.name}: {result.status.value}.",
            planets=tuple(result.planets), houses=tuple(result.houses),
            source_ref_ids=tuple(result.source_ref_ids),
            rule_ids=(result.id,), eligibility=eligibility,
            calculation_ids=("rules/engine",)))
    return out, excluded


# ── the strict gate ──────────────────────────────────────────────────────────

# Which kind of factor→domain link each evidence source_type travels along.
# This table is the whole of the Part 7 gate: it says, for each thing the
# engine can observe, WHICH mapping has to be sourced before that observation
# may carry a strict prediction.
_FACTOR_TYPE_OF: dict[str, FactorType] = {
    "house_lord": FactorType.HOUSE_LORD,
    "shadbala": FactorType.HOUSE_LORD,
    "occupancy": FactorType.HOUSE,
    "aspect": FactorType.HOUSE,
    "ashtakavarga": FactorType.HOUSE,
    "karaka": FactorType.KARAKA,
}


def _link_factor(item: DomainEvidence, factor_type: FactorType,
                 spec: DomainSpec):
    """The specific house or graha whose mapping has to be qualified."""
    if factor_type is FactorType.KARAKA:
        return item.planets[0] if item.planets else None
    return item.houses[0] if item.houses else spec.primary_house


def _strict_filter(spec: DomainSpec, evidence: list[DomainEvidence]
                   ) -> tuple[list[DomainEvidence], list[dict]]:
    """
    What survives in strict synthesis. The criterion is a single question.

    IS THE LINK FROM THIS FACTOR TO THIS DOMAIN WITNESSED?

    Not "is the factor sourced" — that question is too easy to pass and
    passing it proves nothing. The Shadbala of the 10th lord is a measured
    quantity computed from BPHS ch.27, a located witness whose worked
    examples the code reproduces exactly. None of that, on its own, is
    evidence that the 10th house has anything to do with CAREER, and it is
    the second step that carries the prediction.

    Letting a well-sourced measurement inherit strictness from the chain it
    happens to sit in is the exact laundering this project exists to
    prevent, and it is easy to do by accident: every factor here looks
    sourced if you only check the first step.

    WHAT CHANGED IN V1.6, AND WHAT DID NOT

        The criterion is unchanged. What changed is the answer, because the
        audit found the mappings. BPHS 11.11 gives the tenth house `vṛtti`,
        livelihood; BPHS 21.2 makes the strength of the tenth LORD bear on
        it. So a Shadbala factor on the 10th lord now passes for CAREER —
        on evidence, not by relaxation.

        It still fails for a domain whose mapping was not found. The 6th
        house's relevance to employment, the 4th's to education, the general
        RELATIONSHIPS domain: all located nowhere, all still excluded.

    The gate is per-factor, not per-domain. A domain can contribute its
    house-lord evidence to strict synthesis while its kāraka evidence is
    refused, and that is the common case.
    """
    kept: list[DomainEvidence] = []
    excluded: list[dict] = []

    for item in evidence:
        factor_type = _FACTOR_TYPE_OF.get(item.source_type)
        if factor_type is None:
            excluded.append({
                "factor_id": item.factor_id,
                "domain": spec.domain.value,
                "source_type": item.source_type,
                "reason": (
                    f"no factor→domain link type is declared for "
                    f"'{item.source_type}', so it cannot be shown to be "
                    f"source-qualified"),
            })
            continue

        factor = _link_factor(item, factor_type, spec)
        if factor is not None and spec.qualifies_for_strict(factor_type,
                                                            factor):
            kept.append(item)
            continue

        excluded.append({
            "factor_id": item.factor_id,
            "domain": spec.domain.value,
            "source_type": item.source_type,
            "factor_type": factor_type.value,
            "factor": factor,
            "reason": (
                f"strict synthesis requires a located witness for the link "
                f"from the factor to the domain, not merely for the factor. "
                f"The {factor_type.value} mapping {factor} → "
                f"{spec.domain.value} is not source-qualified."),
        })
    return kept, excluded


def strict_admissible_domains() -> list[str]:
    """
    Domains strict synthesis can say anything at all about.

    Exposed because it is a finding rather than an implementation detail.
    In V1.5 this was four domains, because the only source-qualified links
    in the engine were kāraka attributions. After the V1.6 bhāva audit it is
    sixteen — every domain except RELATIONSHIPS, which has no located house
    witness distinct from MARRIAGE.
    """
    from .domains import strict_domains
    return strict_domains()


# ── Part 9: varga confirmation ───────────────────────────────────────────────

def varga_confirmation(spec: DomainSpec, features,
                       reliability: ChartReliability,
                       profile: SynthesisProfile,
                       natal_direction: EvidenceDirection
                       ) -> list[VargaEvidence]:
    """
    Whether the domain's vargas agree with the D1 theme.

    A varga never originates a result. It confirms or qualifies one, which is
    why `natal_direction` is an input: the question asked is "does D10 agree
    with what D1 already said", not "what does D10 say".
    """
    out: list[VargaEvidence] = []
    strict = profile is SynthesisProfile.STRICT

    for chart in spec.primary_vargas:
        if chart == "D1":
            continue
        if not admits_chart(chart, reliability, strict):
            continue
        # V1.7 Part 29. The Part 7 laundering gate, applied to vargas.
        #
        # `admits_chart` asks whether the birth time DETERMINES this
        # divisional chart. That is a different question from whether the
        # link between this chart and this domain has a located source,
        # and until V1.7 nothing asked the second one — so a perfectly
        # stable D10 could carry a CAREER conclusion into strict synthesis
        # on a mapping that rested on nothing.
        #
        # V1.6 could not see this. No varga mapping was source-qualified
        # then, so the gate that was missing would have changed no result.
        # BPHS 7.1-6 qualified five of them, and the moment one qualifies
        # the other six need a gate to keep out.
        if strict and not spec.qualifies_for_strict(FactorType.VARGA, chart):
            continue

        varga_lord_sign = None
        lagnas = getattr(features, "varga_lagnas", {}) or {}
        varga_lagna = lagnas.get(chart)
        if varga_lagna is None:
            continue

        # The varga Lagna lord's dignity IN THAT VARGA is the confirming
        # fact. Kept deliberately narrow: a full feature set per varga is not
        # computed, and inventing one here would duplicate engine.features.
        lord = getattr(varga_lagna, "lord", None)
        if not lord:
            continue
        placement = None
        planet = features.planet(lord)
        if planet is not None:
            placement = planet.vargas.get(chart)
        if placement is None:
            continue

        dignified = (placement.exalted or placement.own_sign
                     or placement.moolatrikona)
        debilitated = placement.debilitated
        if not (dignified or debilitated):
            continue

        direction = (EvidenceDirection.SUPPORTIVE if dignified
                     else EvidenceDirection.CHALLENGING)
        out.append(VargaEvidence(
            domain=spec.domain.value, chart=chart,
            factor=f"{chart} lagna lord {lord} {placement.dignity_label()}",
            direction=direction,
            reliability=chart_reliability(chart, reliability),
            confirms=direction is natal_direction,
            explanation=(
                f"In {chart} the Lagna lord {lord} is "
                f"{placement.dignity_label()} in {placement.sign_name}."),
            planets=(lord,), methodology_id=METHODOLOGY_ID,
            reliability_warnings=tuple(
                chart_warnings(chart, reliability)
                # V1.8 Part 8. Measured, not asserted, and not a D2 special
                # case: a chart that cannot reach all twelve rashis cannot
                # express every dignity, so evidence drawn from it is
                # narrower than the same test elsewhere. D2 reaches two
                # rashis and can therefore only ever confirm, never
                # challenge — which a reader given a supportive D2 line has
                # to be told, beside the line rather than in a footnote.
                + ([range_limitation(chart)]
                   if range_limitation(chart) else []))))
    return out


# ── the entry point ──────────────────────────────────────────────────────────

def evaluate_natal_promise(domain, features, *, yoga_results=None,
                           ashtakavarga=None,
                           reliability: Optional[ChartReliability] = None,
                           profile: SynthesisProfile = SynthesisProfile.STANDARD
                           ) -> tuple[list[DomainEvidence], list[VargaEvidence],
                                      list[dict]]:
    """
    Structured natal evidence for one domain.

    Returns (evidence, varga_evidence, excluded_by_profile). An empty
    evidence list is a real answer and the caller must treat it as one: it
    means this engine finds no natal indication the active profile admits,
    and Part 14 forbids a transit from supplying the deficiency.
    """
    spec = spec_for(domain)
    if reliability is None:
        from .reliability import build_reliability
        reliability = build_reliability(None)

    base_conf = chart_reliability("D1", reliability)

    evidence: list[DomainEvidence] = []
    evidence.extend(_house_lord_factors(spec, features, base_conf))
    evidence.extend(_occupancy_factors(spec, features, base_conf))
    evidence.extend(_aspect_factors(spec, features, base_conf))
    evidence.extend(_karaka_factors(spec, features, base_conf))
    evidence.extend(_shadbala_factors(spec, features, base_conf))
    evidence.extend(_ashtakavarga_factors(spec, features, ashtakavarga,
                                          base_conf))
    yoga_evidence, excluded = _yoga_factors(spec, features, yoga_results,
                                            profile, base_conf)
    evidence.extend(yoga_evidence)

    if profile is SynthesisProfile.STRICT:
        evidence, strict_excluded = _strict_filter(spec, evidence)
        excluded.extend(strict_excluded)

    supportive = sum(1 for e in evidence
                     if e.direction is EvidenceDirection.SUPPORTIVE)
    challenging = sum(1 for e in evidence
                      if e.direction is EvidenceDirection.CHALLENGING)
    net = (EvidenceDirection.SUPPORTIVE if supportive >= challenging
           else EvidenceDirection.CHALLENGING)

    vargas = varga_confirmation(spec, features, reliability, profile, net)
    return evidence, vargas, excluded
