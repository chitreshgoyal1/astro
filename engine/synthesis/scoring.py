"""
Activation and confidence (V1.5 Parts 15, 16, 20)
---------------------------------------------------
How evidence becomes an ordinal band, and why it never becomes a percentage.

EVERYTHING IN THIS MODULE IS A SOFTWARE SYNTHESIS HEURISTIC

    Not one rule here is classical. No text bands a domain into five levels,
    and no text grades evidence HIGH or LOW. These are engine conventions,
    named as such in every serialised record, and a test asserts that no
    output field implies a probability.

WHY ORDINAL AND NOT NUMERIC

    A number invites arithmetic that the underlying evidence cannot support.
    "0.82" next to a marriage domain reads as a likelihood to every reader
    who has ever seen a forecast, and this engine has never been tested
    against a single outcome. The bands are reproducible from the evidence —
    `explain_activation` shows exactly how — and they are deliberately
    coarse.

ACTIVATION AND CONFIDENCE ARE INDEPENDENT, AND THE BRIEF IS RIGHT THAT THEY
MUST BE

    STRONGLY_ACTIVE with LOW confidence is a valid and common combination: it
    says the rules fire loudly and the inputs they fire on are not firm. If
    confidence were folded into activation the reader would see a moderate
    result and could not tell whether that meant weak evidence or weak
    agreement.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .models import (
    ActivationLevel, DomainEvidence, EvidenceConfidence, EvidenceDirection,
    EvidenceLayer, PredictionEligibility, SynthesisProfile, VargaEvidence,
    weakest_confidence,
)

SCORING_METHODOLOGY_ID = "activation_bands_v15"

# How much supportive-minus-challenging weight, within a layer, counts as
# that layer contributing. SOFTWARE HEURISTIC.
LAYER_PRESENT_THRESHOLD = 0.30

# When both directions carry at least this share of the total weight, the
# result is MIXED rather than a level. Part 16: five supportive and four
# challenging must not read as "positive".
MIXED_SHARE = 0.35


def _layer_weight(evidence: Sequence[DomainEvidence],
                  layer: EvidenceLayer) -> tuple[float, float]:
    """(supportive, challenging) weight within one layer."""
    supportive = sum(e.magnitude for e in evidence
                     if e.layer is layer
                     and e.direction is EvidenceDirection.SUPPORTIVE)
    challenging = sum(e.magnitude for e in evidence
                      if e.layer is layer
                      and e.direction is EvidenceDirection.CHALLENGING)
    return supportive, challenging


def layer_is_present(evidence: Sequence[DomainEvidence],
                     layer: EvidenceLayer) -> bool:
    """
    Whether a layer contributed anything, regardless of direction.

    Total magnitude, not supportive-minus-challenging. The distinction is
    load-bearing: transit evidence is always recorded NEUTRAL, because this
    engine has no located source for judging a transit favourable and V1.4
    put Gochara out of scope. Summing only directional weight therefore made
    the transit layer permanently absent and STRONGLY_ACTIVE unreachable —
    the engine could never report all three layers agreeing, however plainly
    they did.
    """
    total = sum(e.magnitude for e in evidence if e.layer is layer)
    return total >= LAYER_PRESENT_THRESHOLD


def activation_level(evidence: Sequence[DomainEvidence]) -> ActivationLevel:
    """
    The Part 15 band, reproducible from the evidence.

    The hierarchy is Part 14's and is enforced here as well as in engine.py,
    because a band is the thing a reader remembers: a domain cannot reach
    ACTIVE without natal evidence, and cannot reach STRONGLY_ACTIVE without
    all three layers. A transit alone yields INACTIVE, whatever its weight.
    """
    natal = layer_is_present(evidence, EvidenceLayer.NATAL)
    dasha = layer_is_present(evidence, EvidenceLayer.DASHA)
    transit = layer_is_present(evidence, EvidenceLayer.TRANSIT)

    if not natal:
        return ActivationLevel.INACTIVE

    supportive = sum(e.magnitude for e in evidence
                     if e.direction is EvidenceDirection.SUPPORTIVE)
    challenging = sum(e.magnitude for e in evidence
                      if e.direction is EvidenceDirection.CHALLENGING)
    total = supportive + challenging
    if total > 0:
        weaker = min(supportive, challenging)
        if weaker / total >= MIXED_SHARE:
            return ActivationLevel.MIXED

    if natal and dasha and transit:
        return ActivationLevel.STRONGLY_ACTIVE
    if natal and dasha:
        return ActivationLevel.ACTIVE
    return ActivationLevel.BACKGROUND


def explain_activation(evidence: Sequence[DomainEvidence]) -> dict:
    """
    Part 17. Exactly how the band was reached, so it can be checked.
    """
    layers = {}
    for layer in EvidenceLayer:
        supportive, challenging = _layer_weight(evidence, layer)
        layers[layer.value] = {
            "supportive_weight": round(supportive, 3),
            "challenging_weight": round(challenging, 3),
            "total_weight": round(
                sum(e.magnitude for e in evidence if e.layer is layer), 3),
            "present": layer_is_present(evidence, layer),
            "factor_count": sum(1 for e in evidence if e.layer is layer),
        }
    supportive = sum(e.magnitude for e in evidence
                     if e.direction is EvidenceDirection.SUPPORTIVE)
    challenging = sum(e.magnitude for e in evidence
                      if e.direction is EvidenceDirection.CHALLENGING)
    total = supportive + challenging
    return {
        "methodology_id": SCORING_METHODOLOGY_ID,
        "basis": "SOFTWARE_HEURISTIC",
        "layers": layers,
        "supportive_weight": round(supportive, 3),
        "challenging_weight": round(challenging, 3),
        "minority_share": (round(min(supportive, challenging) / total, 3)
                           if total else 0.0),
        "mixed_threshold": MIXED_SHARE,
        "layer_present_threshold": LAYER_PRESENT_THRESHOLD,
        "rule": (
            "INACTIVE unless the natal layer is present. MIXED when the "
            "minority direction holds at least the mixed threshold of total "
            "weight. Otherwise BACKGROUND, ACTIVE or STRONGLY_ACTIVE "
            "according to how many layers are present. These bands are "
            "engine conventions and are not probabilities."),
    }


# ── Part 20: confidence ──────────────────────────────────────────────────────

def synthesis_confidence(evidence: Sequence[DomainEvidence],
                         varga_evidence: Sequence[VargaEvidence] = (),
                         reliability=None,
                         boundary_warnings: Sequence[str] = ()
                         ) -> EvidenceConfidence:
    """
    How much weight the conclusion can bear. NOT a probability.

    Five inputs, in the order Part 20 lists them: source-validation quality,
    birth-time stability, astronomical boundary certainty, how many
    independent layers agree, and whether the evidence conflicts.

    The combination is deliberately pessimistic — the result is capped by the
    weakest contributing factor rather than averaged — because an average
    lets one firm input disguise three shaky ones.
    """
    if not evidence:
        return EvidenceConfidence.UNRESOLVED

    # 1. Source quality: the best any single factor achieved, capped by the
    #    fact that most factors rest on unsourced house mappings.
    best_source = max((e.confidence for e in evidence),
                      key=lambda c: c.rank)

    # 2 and 3. Birth-time and boundary certainty arrive already folded into
    #    each factor's confidence by natal_promise, so the floor across all
    #    factors carries them.
    floor = weakest_confidence(e.confidence for e in evidence)

    # 4. Independent layers agreeing raises confidence by one step, but never
    #    above what the sources support.
    layers_present = sum(
        1 for layer in EvidenceLayer if layer_is_present(evidence, layer))

    confidence = floor
    if layers_present >= 2 and floor.rank < best_source.rank:
        confidence = EvidenceConfidence(
            _step_up(floor, ceiling=best_source))

    # 5. Conflicting evidence lowers it. A domain whose factors point both
    #    ways is not more certain for having more of them.
    supportive = sum(1 for e in evidence
                     if e.direction is EvidenceDirection.SUPPORTIVE)
    challenging = sum(1 for e in evidence
                      if e.direction is EvidenceDirection.CHALLENGING)
    if supportive and challenging:
        confidence = EvidenceConfidence(_step_down(confidence))

    # Varga evidence cannot raise confidence and can lower it: a D60
    # confirmation on an unresolved birth time is the textbook case from
    # Part 20.
    for varga in varga_evidence:
        if varga.reliability is EvidenceConfidence.LOW:
            confidence = EvidenceConfidence(_step_down(confidence))
            break

    if boundary_warnings:
        confidence = EvidenceConfidence(_step_down(confidence))

    return confidence


_ORDER = (EvidenceConfidence.UNRESOLVED, EvidenceConfidence.LOW,
          EvidenceConfidence.MEDIUM, EvidenceConfidence.HIGH)


def _step_up(value: EvidenceConfidence,
             ceiling: EvidenceConfidence) -> EvidenceConfidence:
    index = min(_ORDER.index(value) + 1, _ORDER.index(ceiling))
    return _ORDER[index]


def _step_down(value: EvidenceConfidence) -> EvidenceConfidence:
    return _ORDER[max(_ORDER.index(value) - 1, 0)]


def explain_confidence(evidence: Sequence[DomainEvidence],
                       varga_evidence: Sequence[VargaEvidence] = (),
                       boundary_warnings: Sequence[str] = ()) -> dict:
    """Part 17: the inputs to the confidence band, itemised."""
    supportive = sum(1 for e in evidence
                     if e.direction is EvidenceDirection.SUPPORTIVE)
    challenging = sum(1 for e in evidence
                      if e.direction is EvidenceDirection.CHALLENGING)
    return {
        "methodology_id": SCORING_METHODOLOGY_ID,
        "confidence_is_ordinal_band": True,
        "weakest_factor_confidence": (
            weakest_confidence(e.confidence for e in evidence).value
            if evidence else EvidenceConfidence.UNRESOLVED.value),
        "independent_layers_present": sum(
            1 for layer in EvidenceLayer if layer_is_present(evidence, layer)),
        "supportive_factors": supportive,
        "challenging_factors": challenging,
        "evidence_conflicts": bool(supportive and challenging),
        "low_reliability_vargas": [
            v.chart for v in varga_evidence
            if v.reliability is EvidenceConfidence.LOW],
        "boundary_warnings": list(boundary_warnings),
        "rule": (
            "Capped by the weakest contributing factor, raised at most one "
            "step when two or more independent layers agree, lowered when "
            "evidence conflicts, when a low-reliability varga contributes, "
            "or when an astronomical boundary is unresolved."),
    }
