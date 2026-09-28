"""
Prediction eligibility (V1.5 Parts 3, 21, 23)
----------------------------------------------
The gate between "this rule exists" and "this rule may influence a
prediction".

THE PROBLEM THIS SOLVES

    V1.4 shipped ~110 yoga rules, of which one had a located Sanskrit
    witness. If a synthesis layer simply consumed `yoga_results`, then
    Kemadruma — whose cancellation clauses the V1.5 audit found to be wider
    than any witness supports, one of them contradicted outright — would
    influence a marriage prediction exactly as much as Adhi Yoga, which three
    works attest. The output would carry no trace of the difference.

    So eligibility is COMPUTED FROM THE REGISTRY, never declared. There is no
    list in this module that a future release can quietly append to. To make
    a rule strict-eligible you must produce a witness.

PART 23, STATED AS CODE

    Before a legacy yoga contributes to STRICT synthesis:
        - textual source located          → witness_ids non-empty
        - software condition mapped       → software_condition non-empty
        - implementation matched          → status at least
                                            IMPLEMENTATION_MATCHED
        - no unresolved critical conflict → evidence.conflicts empty
        - valid prediction eligibility    → VERIFIED_STRICT

    All five are the conditions `strict_profile_eligible` already enforces
    for the `parashari_strict` rule profile, and that is deliberate: one
    definition of "strict", used by the catalog and by the synthesis layer,
    so the two can never drift into disagreeing about what the word means.
"""

from __future__ import annotations

from typing import Optional

from ..sources import (
    ValidationStatus, evidence_for, strict_profile_eligible, witnesses_for,
)
from .models import PredictionEligibility, SynthesisProfile


def prediction_eligibility(rule_id: str) -> PredictionEligibility:
    """
    How far this rule may influence synthesis. Derived, never declared.
    """
    evidence = evidence_for(rule_id)
    witnesses = witnesses_for(rule_id)

    # A rule whose implementation is known to contradict its own witness is
    # not merely unverified — it is wrong in a way that has been established.
    # It stays in the catalog, because the V1.5 audit's job was to find such
    # rules rather than to delete them, and it is barred from every profile.
    if evidence.validation_status is ValidationStatus.IMPLEMENTATION_DIVERGES:
        return PredictionEligibility.DISABLED

    eligible, _reasons = strict_profile_eligible(evidence, witnesses)
    if eligible:
        return PredictionEligibility.VERIFIED_STRICT

    if witnesses and evidence.textual_condition.strip():
        return PredictionEligibility.SOURCE_LOCATED

    return PredictionEligibility.EXPERIMENTAL


def eligibility_reasons(rule_id: str) -> list[str]:
    """Why a rule is not VERIFIED_STRICT. Empty when it is."""
    evidence = evidence_for(rule_id)
    if evidence.validation_status is ValidationStatus.IMPLEMENTATION_DIVERGES:
        return ["implementation diverges from the located witness"
                + (f": {evidence.divergence}" if evidence.divergence else "")]
    _eligible, reasons = strict_profile_eligible(
        evidence, witnesses_for(rule_id))
    return reasons


def admits(profile: SynthesisProfile, rule_id: str) -> bool:
    """Whether `profile` lets this rule contribute."""
    return profile.accepts(prediction_eligibility(rule_id))


def describe(rule_id: str) -> dict:
    """
    The Part 3 record, as the brief's example shows it.

        {"rule_id": ..., "prediction_eligibility": ...,
         "validation_status": ...}
    """
    evidence = evidence_for(rule_id)
    eligibility = prediction_eligibility(rule_id)
    record = {
        "rule_id": rule_id,
        "prediction_eligibility": eligibility.value,
        "validation_status": evidence.validation_status.value,
        "source_ref_ids": list(evidence.witness_ids),
    }
    if eligibility is not PredictionEligibility.VERIFIED_STRICT:
        record["not_strict_because"] = eligibility_reasons(rule_id)
    if evidence.corrected_by:
        record["corrected_by"] = evidence.corrected_by
    return record


def filter_results(results, profile: SynthesisProfile
                   ) -> tuple[list, list[dict]]:
    """
    Split yoga results into those the profile admits and those it does not.

    Returns (admitted, excluded), where `excluded` records each rejection with
    its reason. Part 23 allows an unverified yoga to appear in DIAGNOSTIC
    output while barred from strict synthesis, so the rejections are returned
    rather than dropped — a silently shorter list would hide the gate's work.
    """
    admitted = []
    excluded: list[dict] = []
    for result in results:
        eligibility = prediction_eligibility(result.id)
        if profile.accepts(eligibility):
            admitted.append(result)
        else:
            excluded.append({
                "rule_id": result.id,
                "name": result.name,
                "status": result.status.value,
                "prediction_eligibility": eligibility.value,
                "reasons": eligibility_reasons(result.id),
            })
    return admitted, excluded


def eligibility_summary(rule_ids) -> dict:
    """Counts by eligibility, for the report and the snapshot."""
    counts: dict[str, int] = {}
    for rule_id in rule_ids:
        key = prediction_eligibility(rule_id).value
        counts[key] = counts.get(key, 0) + 1
    return counts
