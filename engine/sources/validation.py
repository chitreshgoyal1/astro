"""
Validation enforcement (V1.3 Parts 4, 6, 15)
---------------------------------------------
Turns the validation lifecycle from a label into a claim the code checks.

The failure this prevents: a status field is only worth anything if something
refuses to set it without the evidence. Otherwise `TRADITION_VALIDATED` is a
string that whoever typed it fastest gets to assert — which is exactly the
state V1.2 was in, with a hundred unchecked "BPHS ch.36" citations reading as
provenance.

So every status has a stated evidence requirement, `check_status` enforces it,
and a test asserts that every registered piece of evidence actually satisfies
the status it claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from .models import (
    RuleEvidence, SourceAuthority, SourceWitness, ValidationStatus,
)


@dataclass(frozen=True)
class Requirement:
    """One condition that must hold for a status to be claimable."""

    description: str
    test: Callable[[RuleEvidence, Sequence[SourceWitness]], bool]


def _has_witness(evidence, witnesses) -> bool:
    return bool(witnesses)


def _has_locator(evidence, witnesses) -> bool:
    return any(w.has_locator for w in witnesses)


def _identifies_edition(evidence, witnesses) -> bool:
    return any(w.has_locator and w.identifies_edition for w in witnesses)


def _translation_step_satisfied(evidence, witnesses) -> bool:
    """
    Either a translation witness is recorded, OR the original was read.

    Requiring a translation as a prerequisite for a rule whose Sanskrit
    witness is in hand would be backwards: reading the text itself is the
    stronger position, not a weaker one. The step exists to ensure that
    somebody checked the rendering against something, and reading the
    original satisfies that more directly than consulting a translator would.
    """
    return (any(w.authority is SourceAuthority.TRANSLATION for w in witnesses)
            or _has_sanskrit_tier_witness(evidence, witnesses))


def _has_textual_condition(evidence, witnesses) -> bool:
    return bool(evidence.textual_condition.strip())


def _has_software_mapping(evidence, witnesses) -> bool:
    return bool(evidence.software_condition.strip())


def _has_implementation_test(evidence, witnesses) -> bool:
    return bool(evidence.implementation_test.strip())


def _has_two_independent_witnesses(evidence, witnesses) -> bool:
    """
    Two witnesses to the same passage in the same edition are one witness.
    Independence is judged by the work they attest — and, since V1.5, by
    whether the later work is QUOTING the earlier one.

    Jātaka Pārijāta introduces its candra-yoga verse with the word `horāyām`,
    "in the Horā", and then reproduces Bṛhajjātaka 13.3. Counting that as a
    second work agreeing would be counting Varāhamihira twice. A compendium
    that names its source is evidence about how the source was READ, which is
    worth having and is not corroboration.
    """
    quoted = set(evidence.quotation_of)
    works = {w.work for w in witnesses
             if w.authority.can_support_validation and w.id not in quoted}
    return len(works) >= 2


def _profile_is_named(evidence, witnesses) -> bool:
    """VALIDATED_FOR_PROFILE is a claim about a profile, so name the profile."""
    return bool(evidence.rule_profile)


def _has_sanskrit_tier_witness(evidence, witnesses) -> bool:
    return any(w.authority.is_sanskrit_tier for w in witnesses)


def _no_behavioural_conflict(evidence, witnesses) -> bool:
    """
    A rule whose implementation is known to diverge is not 'matched'.

    V1.8 refines what "conflict" means here, because the registry gained a
    kind it had never held. Every conflict up to V1.7 was DOCTRINAL: two
    witnesses state different rules, no reading has been chosen, and any
    implementation therefore contradicts one of them. Barring
    IMPLEMENTATION_MATCHED is exactly right for those.

    The gochara audit produced a TRANSMISSION conflict instead — two
    editions of one work disagreeing about two words, where one reading is
    internally impossible. That is resolved, the implementation follows the
    resolution, and treating it like an open doctrinal dispute would mean a
    rule is penalised for having had its textual problem FOUND AND FIXED
    rather than overlooked.

    So a conflict blocks only while it is unresolved. The distinction is
    read from the conflict record, not from the rule asserting it is fine.
    """
    from .registry import conflict_by_id

    for conflict_id in evidence.conflicts:
        try:
            conflict = conflict_by_id(conflict_id)
        except KeyError:
            # An unregistered conflict id is worse than a registered one:
            # nothing says what it is or whether it was settled.
            return False
        if not conflict.resolution_status.startswith("RESOLVED"):
            return False
    return True


def _no_supporting_witness_is_web_only(evidence, witnesses) -> bool:
    """Part 3: a web summary can never be the thing that validates a rule."""
    supporting = [w for w in witnesses if w.authority.can_support_validation]
    return bool(supporting)


def _human_review_complete(evidence, witnesses) -> bool:
    return not evidence.needs_human_review


# Requirements are CUMULATIVE: a status requires its own row and every row
# below it on the ladder.
REQUIREMENTS: dict[ValidationStatus, tuple[Requirement, ...]] = {
    ValidationStatus.UNVERIFIED: (),
    ValidationStatus.TEXT_LOCATED: (
        Requirement("at least one witness is recorded", _has_witness),
    ),
    ValidationStatus.WITNESS_RECORDED: (
        Requirement("a witness identifies a passage, not merely a work",
                    _has_locator),
        Requirement("that witness identifies its edition", _identifies_edition),
        Requirement("at least one witness may support validation "
                    "(not web-summary only)", _no_supporting_witness_is_web_only),
    ),
    ValidationStatus.TRANSLATION_CHECKED: (
        Requirement("a translation witness is recorded, or the Sanskrit "
                    "original was read directly",
                    _translation_step_satisfied),
    ),
    ValidationStatus.RULE_INTERPRETATION_MAPPED: (
        Requirement("what the text states is written out as a textual condition",
                    _has_textual_condition),
    ),
    ValidationStatus.IMPLEMENTATION_MATCHED: (
        Requirement("the software condition is written out",
                    _has_software_mapping),
        Requirement("a test exercises the implementation",
                    _has_implementation_test),
        Requirement("no registered conflict says the implementation diverges "
                    "from the witness", _no_behavioural_conflict),
    ),
    ValidationStatus.SECOND_WITNESS_CHECKED: (
        Requirement("two independent works attest the rule "
                    "(a named quotation does not count as the second)",
                    _has_two_independent_witnesses),
    ),
    ValidationStatus.VALIDATED_FOR_PROFILE: (
        Requirement("a Sanskrit-tier witness is recorded",
                    _has_sanskrit_tier_witness),
        Requirement("the methodology profile the claim is scoped to is named",
                    _profile_is_named),
    ),
    ValidationStatus.TRADITION_VALIDATED: (
        Requirement("no human-review question is outstanding",
                    _human_review_complete),
    ),
}

# The ladder, in order, for cumulative checking.
_LADDER = (
    ValidationStatus.TEXT_LOCATED,
    ValidationStatus.WITNESS_RECORDED,
    ValidationStatus.TRANSLATION_CHECKED,
    ValidationStatus.RULE_INTERPRETATION_MAPPED,
    ValidationStatus.IMPLEMENTATION_MATCHED,
    ValidationStatus.SECOND_WITNESS_CHECKED,
    ValidationStatus.VALIDATED_FOR_PROFILE,
    ValidationStatus.TRADITION_VALIDATED,
)


def unmet_requirements(evidence: RuleEvidence,
                       witnesses: Sequence[SourceWitness],
                       status: Optional[ValidationStatus] = None
                       ) -> list[str]:
    """
    Requirements that the evidence does NOT satisfy for the given status.

    An empty list means the status is supportable. CONFLICTING_SOURCES is off
    the ladder: it asserts disagreement rather than progress, and needs only a
    registered conflict.
    """
    target = status or evidence.validation_status
    if target is ValidationStatus.UNVERIFIED:
        return []
    if target is ValidationStatus.CONFLICTING_SOURCES:
        return ([] if evidence.conflicts
                else ["a conflict id must be registered"])
    if target is ValidationStatus.IMPLEMENTATION_DIVERGES:
        # A divergence claim has to be earned in both directions: you must
        # have read a witness, and you must say what the code does instead.
        # Without the second half it is a shrug with a status attached.
        missing = []
        if not witnesses:
            missing.append("a witness must be recorded to diverge FROM")
        if not evidence.textual_condition.strip():
            missing.append("the textual condition must be written out")
        if not evidence.divergence.strip():
            missing.append("the divergence must be stated explicitly")
        return missing

    missing: list[str] = []
    for rung in _LADDER:
        for requirement in REQUIREMENTS[rung]:
            if not requirement.test(evidence, witnesses):
                missing.append(f"[{rung.value}] {requirement.description}")
        if rung is target:
            break
    return missing


def check_status(evidence: RuleEvidence,
                 witnesses: Sequence[SourceWitness]) -> bool:
    return not unmet_requirements(evidence, witnesses)


# ── Part 15: the strict profile threshold ────────────────────────────────────

# What a rule must reach to be allowed into `parashari_strict`.
#
# The word "strict" has to mean something enforceable, so it means this:
#
#   * a witness identified, with an edition and a passage locator;
#   * that witness at Sanskrit tier — a witness to the text, not to somebody's
#     rendering of it;
#   * the textual condition written out;
#   * the software condition written out and mapped to it;
#   * a test that exercises the implementation.
#
# It deliberately does NOT require TRADITION_VALIDATED, which additionally
# needs a second independent work and completed human review. Nothing in this
# engine meets that yet, and a strict profile that is empty by construction
# would teach nobody anything.
STRICT_PROFILE_MINIMUM = ValidationStatus.IMPLEMENTATION_MATCHED

STRICT_PROFILE_REQUIREMENTS = (
    "a witness with an edition and a passage locator",
    "that witness at PRIMARY_SANSKRIT_WITNESS or PRINTED_SANSKRIT_EDITION tier",
    "a written textual_condition",
    "a written software_condition",
    "a named implementation test",
)


def strict_profile_eligible(evidence: RuleEvidence,
                            witnesses: Sequence[SourceWitness]
                            ) -> tuple[bool, list[str]]:
    """
    Whether a rule may enter `parashari_strict`, and why not if it may not.

    Returns (eligible, reasons_it_is_not).
    """
    reasons: list[str] = []

    if evidence.validation_status is ValidationStatus.CONFLICTING_SOURCES:
        reasons.append(
            "witnesses conflict; a conflicted rule cannot sit in a strict "
            "profile without a chosen reading, which would hide the conflict")
        return False, reasons

    if evidence.validation_status is ValidationStatus.IMPLEMENTATION_DIVERGES:
        reasons.append(
            "the implementation is known to diverge from the located witness"
            + (f": {evidence.divergence}" if evidence.divergence else "")
            + (f" — the located reading is implemented by "
               f"'{evidence.corrected_by}'" if evidence.corrected_by else ""))
        return False, reasons

    if evidence.conflicts:
        reasons.append(
            "a registered conflict affects this rule: "
            + ", ".join(evidence.conflicts))

    if not evidence.validation_status.at_least(STRICT_PROFILE_MINIMUM):
        reasons.append(
            f"validation status is {evidence.validation_status.value}, "
            f"below the required {STRICT_PROFILE_MINIMUM.value}")

    if not _has_sanskrit_tier_witness(evidence, witnesses):
        reasons.append(
            "no Sanskrit-tier witness: a translation or a modern summary "
            "cannot establish what the text says")

    reasons.extend(unmet_requirements(evidence, witnesses,
                                      STRICT_PROFILE_MINIMUM))
    return (not reasons), reasons


# ── audit helpers ────────────────────────────────────────────────────────────

def highest_supportable_status(evidence: RuleEvidence,
                               witnesses: Sequence[SourceWitness]
                               ) -> ValidationStatus:
    """The best status the evidence would actually justify."""
    best = ValidationStatus.UNVERIFIED
    for rung in _LADDER:
        if unmet_requirements(evidence, witnesses, rung):
            break
        best = rung
    return best


def overclaimed(evidence: RuleEvidence,
                witnesses: Sequence[SourceWitness]) -> bool:
    """True when the declared status is higher than the evidence supports."""
    return bool(unmet_requirements(evidence, witnesses))
