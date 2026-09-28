"""
Declarative Yoga rule engine (Part 10)
--------------------------------------
A Yoga is a named classical combination with a stated formation condition, an
attributable source, and — separately — its own cancellation and strength
rules. This engine keeps those three things apart on purpose:

    1. EXISTENCE      do the formation conditions hold?
    2. CANCELLATION   does a classical bhanga clause undo it?
    3. STRENGTH       only once it exists, how strong is it?

Running them together is what produced the previous engine's misleading
output, where "Raja Yoga present" meant only that some graha happened to be
dignified in a kendra. Existence is never inferred from strength here, and
strength is never calculated for a Yoga that does not exist.

A Yoga is therefore not a boolean. Its status is one of:

    ABSENT                  formation conditions not met
    PRESENT                 formed, no cancellation, no strength verdict
    PRESENT_BUT_CANCELLED   formed, but a bhanga clause applies
    PRESENT_BUT_WEAKENED    formed, undamaged, but materially weakened
    PRESENT_AND_STRONG      formed and reinforced

Where two authorities define a combination differently, they are represented
as separate rules in separate profiles rather than merged into one definition
that neither would recognise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Sequence

from ..features.models import ChartFeatures
from .conditions import Condition, ConditionResult


class YogaStatus(str, Enum):
    ABSENT = "ABSENT"
    PRESENT = "PRESENT"
    PRESENT_BUT_CANCELLED = "PRESENT_BUT_CANCELLED"
    PRESENT_BUT_WEAKENED = "PRESENT_BUT_WEAKENED"
    PRESENT_AND_STRONG = "PRESENT_AND_STRONG"

    @property
    def is_present(self) -> bool:
        return self is not YogaStatus.ABSENT

    @property
    def is_effective(self) -> bool:
        """Formed and not cancelled. Weakened still counts as operative."""
        return self.is_present and self is not YogaStatus.PRESENT_BUT_CANCELLED


@dataclass
class Modifier:
    """One strength adjustment, with the reason it applied."""

    name: str
    delta: float                 # positive strengthens, negative weakens
    reason: str

    def describe(self) -> str:
        return f"{self.delta:+.2f} {self.name} — {self.reason}"


# A modifier test returns a Modifier when it applies, or None.
ModifierTest = Callable[[ChartFeatures], Optional[Modifier]]


@dataclass
class YogaRule:
    """
    One classical combination.

    `conditions_all` must every one hold; `conditions_any` needs at least one,
    when supplied. Cancellations are evaluated only after formation, and
    modifiers only after that — see the module docstring.
    """

    id: str
    name: str
    category: str                       # raja | dhana | mahapurusha | ...
    tradition: str                      # e.g. "Parashari"
    source: str                         # citable text and chapter
    explanation: str
    conditions_all: list[Condition] = field(default_factory=list)
    conditions_any: list[Condition] = field(default_factory=list)
    cancellation_conditions: list[Condition] = field(default_factory=list)
    strength_modifiers: list[ModifierTest] = field(default_factory=list)
    planets_involved: list[str] = field(default_factory=list)
    houses_involved: list[int] = field(default_factory=list)
    variant_of: Optional[str] = None    # set when several authorities differ
    notes: str = ""

    # ── V1.3 provenance ─────────────────────────────────────────────────────
    # `source` above is a human-readable citation string and is NOT evidence:
    # every one of those strings was written from memory during implementation
    # and none was checked against an edition. The real provenance lives in
    # the source registry, keyed by rule id, and is reached through `evidence`.
    #
    # TEXT SAYS and SOFTWARE IMPLEMENTS are held apart there, deliberately:
    # an English paraphrase of a rule must never become the thing that stands
    # in for the witness.

    def evidence(self):
        """The registered RuleEvidence for this rule."""
        from ..sources import evidence_for
        return evidence_for(self.id)

    def witnesses(self):
        """Textual witnesses recorded for this rule, possibly none."""
        from ..sources import witnesses_for
        return witnesses_for(self.id)

    @property
    def validation_status(self):
        return self.evidence().validation_status

    @property
    def classification(self):
        return self.evidence().classification

    @property
    def source_refs(self) -> list[str]:
        return list(self.evidence().witness_ids)

    @property
    def textual_condition(self) -> str:
        """What the TEXT says, where a witness has been located."""
        return self.evidence().textual_condition

    @property
    def software_condition(self) -> str:
        """What the CODE does, written out for comparison with the above."""
        return self.evidence().software_condition

    @property
    def known_variants(self) -> list[str]:
        return list(self.evidence().known_variants)

    @property
    def conflicts(self) -> list[str]:
        return list(self.evidence().conflicts)

    @property
    def needs_human_review(self) -> bool:
        return self.evidence().needs_human_review

    def evaluate(self, features: ChartFeatures,
                 rule_profile: Optional[str] = None) -> "YogaResult":
        return evaluate_rule(self, features, rule_profile)


@dataclass
class YogaResult:
    """What the engine found, with every step of the reasoning retained."""

    id: str
    name: str
    category: str
    source: str
    tradition: str
    status: YogaStatus
    present: bool
    effective: bool
    explanation: str
    conditions_met: list[str] = field(default_factory=list)
    conditions_failed: list[str] = field(default_factory=list)
    cancellations_found: list[str] = field(default_factory=list)
    modifiers: list[Modifier] = field(default_factory=list)
    planets: list[str] = field(default_factory=list)
    houses: list[int] = field(default_factory=list)
    # SOFTWARE HEURISTIC — see the note on _BASE_SCORE below. Named
    # `engine_strength_score` so that no caller can mistake it for a classical
    # measure; `strength` remains as a read-only alias for V1.1 callers.
    engine_strength_score: Optional[float] = None
    engine_strength_band: str = ""
    variant_of: Optional[str] = None
    notes: str = ""

    # Fixed metadata, carried on every result so the score can never travel
    # without the disclaimer attached to it.
    score_type: str = "software_heuristic"
    classical_measure: bool = False

    # ── V1.3 provenance, carried on the RESULT ──────────────────────────────
    # So that a finding can never be read without its evidential standing. A
    # yoga reported as present with validation_status UNVERIFIED is a
    # different kind of statement from one backed by a located witness, and
    # the consumer must be able to tell them apart.
    rule_profile: Optional[str] = None
    validation_status: str = "UNVERIFIED"
    classification: str = "UNVERIFIED"
    source_ref_ids: list[str] = field(default_factory=list)
    textual_condition: str = ""
    conflicts: list[str] = field(default_factory=list)
    needs_human_review: bool = False

    @property
    def strength(self) -> Optional[float]:
        """Deprecated alias for `engine_strength_score` (V1.1 compatibility)."""
        return self.engine_strength_score

    @property
    def strength_label(self) -> str:
        """Deprecated alias for `engine_strength_band` (V1.1 compatibility)."""
        return self.engine_strength_band

    def describe(self) -> str:
        return f"{self.name}: {self.status.value}"

    def to_dict(self) -> dict:
        """JSON-native view for the chart snapshot."""
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "present": self.present,
            "effective": self.effective,
            "source": self.source,
            "tradition": self.tradition,
            "explanation": self.explanation,
            "conditions_met": list(self.conditions_met),
            "conditions_failed": list(self.conditions_failed),
            "cancellations_found": list(self.cancellations_found),
            "planets": list(self.planets),
            "houses": sorted(set(self.houses)),
            "variant_of": self.variant_of,
            "notes": self.notes,
            # Provenance travels with every finding.
            "rule_profile": self.rule_profile,
            "validation_status": self.validation_status,
            "classification": self.classification,
            "source_ref_ids": list(self.source_ref_ids),
            "needs_human_review": self.needs_human_review,
        }
        if self.textual_condition:
            data["textual_condition"] = self.textual_condition
        if self.conflicts:
            data["conflicts"] = list(self.conflicts)
        if self.engine_strength_score is not None:
            # 0-100 in the serialised form, as the V1.2 brief specifies.
            data["engine_strength_score"] = round(
                self.engine_strength_score * 100)
            data["engine_strength_band"] = self.engine_strength_band
            data["score_type"] = self.score_type
            data["classical_measure"] = self.classical_measure
            data["modifiers"] = [
                {"name": m.name, "delta": m.delta, "reason": m.reason}
                for m in self.modifiers]
        return data


# SOFTWARE HEURISTIC, not classical doctrine.
#
# No classical text scores a Yoga numerically. This number exists only to rank
# results within one chart so a reader is not handed forty findings in
# arbitrary order. It is deliberately NOT used to decide whether a Yoga
# exists: see the guarantee below.
#
# THE EXISTENCE GUARANTEE
#     A Yoga's presence never depends on this score. Formation is decided by
#     the rule's own conditions and nothing else; the score is computed
#     afterwards and only ever chooses between PRESENT, PRESENT_AND_STRONG and
#     PRESENT_BUT_WEAKENED — all three of which are present. The only thing
#     that can make a formed Yoga ineffective is an explicit cancellation
#     clause belonging to the rule. A test asserts this invariant.
_STRONG_AT = 0.70
_WEAK_BELOW = 0.40
_BASE_SCORE = 0.55


def _strength_band(score: float) -> str:
    if score >= _STRONG_AT:
        return "strong"
    if score < _WEAK_BELOW:
        return "weakened"
    return "moderate"


def evaluate_rule(rule: YogaRule, features: ChartFeatures,
                  rule_profile: Optional[str] = None) -> YogaResult:
    """Evaluate one rule: existence, then cancellation, then strength."""
    evidence = rule.evidence()
    provenance = {
        "rule_profile": rule_profile,
        "validation_status": evidence.validation_status.value,
        "classification": evidence.classification.value,
        "source_ref_ids": list(evidence.witness_ids),
        "textual_condition": evidence.textual_condition,
        "conflicts": list(evidence.conflicts),
        "needs_human_review": evidence.needs_human_review,
    }
    met: list[str] = []
    failed: list[str] = []
    planets: list[str] = list(rule.planets_involved)
    houses: list[int] = list(rule.houses_involved)

    def record(result: ConditionResult):
        for planet in result.planets:
            if planet and planet not in planets:
                planets.append(planet)
        for house in result.houses:
            if house and house not in houses:
                houses.append(house)

    # ── 1. existence ─────────────────────────────────────────────────────────
    all_hold = True
    for condition in rule.conditions_all:
        outcome = condition.evaluate(features)
        record(outcome)
        (met if outcome.met else failed).append(outcome.description)
        if not outcome.met:
            all_hold = False

    any_holds = True
    if rule.conditions_any:
        any_holds = False
        for condition in rule.conditions_any:
            outcome = condition.evaluate(features)
            record(outcome)
            if outcome.met:
                met.append(outcome.description)
                any_holds = True
            else:
                failed.append(outcome.description)

    if not (all_hold and any_holds):
        return YogaResult(
            id=rule.id, name=rule.name, category=rule.category,
            source=rule.source, tradition=rule.tradition,
            status=YogaStatus.ABSENT, present=False, effective=False,
            explanation=rule.explanation,
            conditions_met=met, conditions_failed=failed,
            planets=planets, houses=houses,
            variant_of=rule.variant_of, notes=rule.notes,
            **provenance,
        )

    # ── 2. cancellation ──────────────────────────────────────────────────────
    cancellations: list[str] = []
    for condition in rule.cancellation_conditions:
        outcome = condition.evaluate(features)
        if outcome.met:
            record(outcome)
            cancellations.append(outcome.description)

    # ── 3. strength, only now that the Yoga exists ───────────────────────────
    modifiers: list[Modifier] = []
    score = _BASE_SCORE
    for test in rule.strength_modifiers:
        modifier = test(features)
        if modifier is not None:
            modifiers.append(modifier)
            score += modifier.delta
    score = max(0.0, min(1.0, score))

    if cancellations:
        status = YogaStatus.PRESENT_BUT_CANCELLED
    elif score >= _STRONG_AT:
        status = YogaStatus.PRESENT_AND_STRONG
    elif score < _WEAK_BELOW:
        status = YogaStatus.PRESENT_BUT_WEAKENED
    else:
        status = YogaStatus.PRESENT

    return YogaResult(
        id=rule.id, name=rule.name, category=rule.category,
        source=rule.source, tradition=rule.tradition,
        status=status, present=True, effective=status.is_effective,
        explanation=rule.explanation,
        conditions_met=met, conditions_failed=failed,
        cancellations_found=cancellations, modifiers=modifiers,
        planets=planets, houses=houses,
        engine_strength_score=round(score, 3),
        engine_strength_band=_strength_band(score),
        variant_of=rule.variant_of, notes=rule.notes,
        **provenance,
    )


def evaluate_ruleset(rules: Sequence[YogaRule],
                     features: ChartFeatures,
                     rule_profile: Optional[str] = None) -> list[YogaResult]:
    """Evaluate every rule, present ones first, then by descending strength."""
    results = [evaluate_rule(rule, features, rule_profile) for rule in rules]
    results.sort(key=lambda r: (not r.present,
                                -(r.engine_strength_score or 0.0), r.name))
    return results
