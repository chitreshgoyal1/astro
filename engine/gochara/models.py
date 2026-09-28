"""
Gochara models (V1.8 Parts 1-6)
---------------------------------
The vocabulary for transit JUDGEMENT, as distinct from transit FACT.

WHY THIS IS A SEPARATE PACKAGE

    `engine.transits` answers "where is Shani and what does it touch". That
    is astronomy plus geometry, it has been externally benchmarked, and it
    says nothing about whether any of it is favourable.

    This package answers "does a located text say that placement is
    favourable, and is that judgement obstructed". That is a TEXTUAL RULE.
    Keeping them in one module would have let the second borrow the first's
    benchmark, which is precisely the substitution the project forbids:
    the positions being correct to the arcsecond is not evidence that
    Phaladīpikā says what we think it says.

THE ORDER PART 1 REQUIRES

    1. reference frame          TransitReference
    2. transit house position   GocharaPlacement
    3. favourable placement     GocharaRule.favourable_houses
    4. vedha / obstruction      VedhaResult
    5. dasha-lord condition     GocharaActivation.is_*_lord
    6. natal strength condition GocharaActivation.natal_strength
    7. synthesis eligibility    GocharaJudgement.strict_eligible

    Each step is a separate object with its own `source_ref_ids`, because
    Part 1 forbids a later rule erasing the provenance of an earlier one. A
    vedha that cancels a favourable placement does not delete the placement:
    `GocharaJudgement` carries both, and the reader can see which verse
    supplied which half of the answer.

WHAT IS DELIBERATELY ABSENT

    There is no field here for what a transit MEANS in words. Phaladīpikā
    26.9-24 does give per-graha per-house effects, and encoding them would
    turn house membership directly into prose, which Part 3 forbids. Those
    verses are recorded in the registry as located and unimplemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional


# ── Part 2: the reference frame ──────────────────────────────────────────────

class TransitReference(str, Enum):
    """
    The point transits are counted FROM.

    Part 2 requires this to be explicit on every rule, and the reason is not
    hypothetical. The two rules this engine implements disagree about it.
    Phaladīpikā 26.1 says the candra-lagna is primary in transits and gives
    its favourable-house table from the Moon; Phaladīpikā 20.34 counts the
    daśā lord's transit `vilagnāt`, from the Lagna. Evaluating either table
    in the other's frame would produce confident, well-tested, wrong answers.
    """

    MOON = "MOON"
    LAGNA = "LAGNA"
    BOTH = "BOTH"
    OTHER = "OTHER"

    @property
    def label(self) -> str:
        return _REFERENCE_LABELS[self]


_REFERENCE_LABELS = {
    TransitReference.MOON: "counted from the natal Chandra",
    TransitReference.LAGNA: "counted from the natal Lagna",
    TransitReference.BOTH: "counted from both the natal Lagna and Chandra",
    TransitReference.OTHER: "counted from another point",
}


# ── Part 10: how many witnesses stand behind a rule ──────────────────────────

class WitnessAgreement(str, Enum):
    """
    Part 10's third axis, kept apart from ValidationStatus.

    ValidationStatus asks how far one rule has been TRACED. This asks how
    many voices were heard, and Part 10 is explicit that a single-witness
    rule must not be downgraded merely for being single-witness. So it is
    recorded rather than scored.

    SAME_WORK_SECOND_EDITION is the distinction the V1.8 gochara audit
    forced into existence. A second edition of Phaladīpikā is not a second
    voice on doctrine — it is the same work speaking again — but it IS
    decisive about a READING, and it settled two corrupt words in the
    digital witness. Collapsing it into MULTI_WITNESS_MATCHED would have
    claimed independent doctrinal support the engine does not have;
    collapsing it into SINGLE_WITNESS_MATCHED would have thrown away the
    textual-critical work that fixed the table.
    """

    SINGLE_WITNESS_MATCHED = "SINGLE_WITNESS_MATCHED"
    SAME_WORK_SECOND_EDITION = "SAME_WORK_SECOND_EDITION"
    MULTI_WITNESS_MATCHED = "MULTI_WITNESS_MATCHED"
    CONFLICTING_WITNESSES = "CONFLICTING_WITNESSES"

    @property
    def is_independent(self) -> bool:
        """Whether a second INDEPENDENT WORK agrees."""
        return self is WitnessAgreement.MULTI_WITNESS_MATCHED


# ── Part 3: the declarative rule ─────────────────────────────────────────────

@dataclass(frozen=True)
class GocharaRule:
    """
    One graha's transit table, as the text states it.

    Part 3 asks for this declaratively, and the point of that is testability:
    `favourable_houses` can be compared against a verse by a human reading
    both, which is not true of a rule expressed as control flow.

    `vedha_pairs` maps each favourable house to the house whose occupation
    obstructs it. It is a mapping rather than two parallel tuples because the
    verses state it positionally — Phaladīpikā 26.3 lists the Sun's houses
    11, 3, 10, 6 and then its vedha houses 5, 9, 4, 12 in that order — and a
    positional pairing held in two tuples is one careless edit away from
    silently re-pairing every entry.
    """

    planet: str
    reference_frame: TransitReference
    favourable_houses: tuple[int, ...] = ()
    unfavourable_houses: tuple[int, ...] = ()
    vedha_pairs: Mapping[int, int] = field(default_factory=dict)

    # Part 4: "If the textual source has planet-specific exceptions, encode
    # them explicitly." Two are stated, and they are reciprocal: the Sun
    # suffers no vedha from Saturn (26.3, father and son), the Moon none from
    # Mercury (26.4), Saturn none from the Sun (26.5), Mercury none from the
    # Moon (26.6). Nothing licenses generalising these to other pairs, so
    # nothing does.
    vedha_exempt_planets: tuple[str, ...] = ()
    exemption_reason: str = ""

    source_ref_ids: tuple[str, ...] = ()
    validation_status: str = "UNVERIFIED"
    witness_agreement: WitnessAgreement = (
        WitnessAgreement.SINGLE_WITNESS_MATCHED)
    methodology_profile: str = ""
    rule_id: str = ""
    textual_condition: str = ""
    software_condition: str = ""
    notes: str = ""

    def is_favourable_house(self, house: int) -> bool:
        return house in self.favourable_houses

    def vedha_house_for(self, house: int) -> Optional[int]:
        return self.vedha_pairs.get(house)

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "rule_id": self.rule_id,
            "reference_frame": self.reference_frame.value,
            "favourable_houses": list(self.favourable_houses),
            "unfavourable_houses": list(self.unfavourable_houses),
            "vedha_pairs": {str(k): v
                            for k, v in sorted(self.vedha_pairs.items())},
            "vedha_exempt_planets": list(self.vedha_exempt_planets),
            "exemption_reason": self.exemption_reason,
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status,
            "witness_agreement": self.witness_agreement.value,
            "methodology_profile": self.methodology_profile,
            "textual_condition": self.textual_condition,
            "software_condition": self.software_condition,
            "notes": self.notes,
        }


# ── Part 3 result: where the graha stands in the rule's own frame ────────────

@dataclass(frozen=True)
class GocharaPlacement:
    """
    One graha's position in one rule's reference frame, judged by that rule.

    `favourable` is Optional on purpose. False means the text places this
    house outside the graha's favourable list; None means the rule has no
    table for this graha at all, which is a different statement and must not
    be read as an unfavourable verdict.
    """

    planet: str
    reference_frame: TransitReference
    house: Optional[int]
    favourable: Optional[bool]
    rule_id: str = ""
    source_ref_ids: tuple[str, ...] = ()
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "reference_frame": self.reference_frame.value,
            "house": self.house,
            "favourable": self.favourable,
            "rule_id": self.rule_id,
            "source_ref_ids": list(self.source_ref_ids),
            "explanation": self.explanation,
        }


# ── Part 4: vedha as a first-class layer ─────────────────────────────────────

@dataclass(frozen=True)
class VedhaResult:
    """
    Whether a favourable transit is obstructed, and by what.

    Part 4 requires this as a first-class object rather than a boolean buried
    in an expression, and the field that earns the requirement is
    `exception_applied`: when Saturn stands in the Sun's vedha house the
    answer is "not obstructed", and the reason that is not simply "no planet
    there" has to survive into the record or the verdict becomes unreadable.
    """

    transit_planet: str
    transit_house: Optional[int]
    vedha_house: Optional[int]
    blocking_condition_present: bool = False
    blocking_planet: Optional[str] = None
    blocking_planets: tuple[str, ...] = ()
    exception_applied: Optional[str] = None
    exempted_planets: tuple[str, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    explanation: str = ""

    @property
    def obstructs(self) -> bool:
        return self.blocking_condition_present

    def to_dict(self) -> dict:
        return {
            "transit_planet": self.transit_planet,
            "transit_house": self.transit_house,
            "vedha_house": self.vedha_house,
            "blocking_condition_present": self.blocking_condition_present,
            "blocking_planet": self.blocking_planet,
            "blocking_planets": list(self.blocking_planets),
            "exception_applied": self.exception_applied,
            "exempted_planets": list(self.exempted_planets),
            "source_ref_ids": list(self.source_ref_ids),
            "explanation": self.explanation,
        }


# ── Part 6: natal strength, textual qualification kept from software reading ─

@dataclass(frozen=True)
class NatalStrengthCondition:
    """
    Phaladīpikā 20.34-35's `balānvita` condition, in two separated halves.

    Part 6 is emphatic: where the text says "strong" and does not name a
    numeric threshold, do not silently invent one. So the text's own words
    live in `textual_qualification` and the engine's operationalisation lives
    in `software_interpretation`, and the boolean `satisfied` is derived from
    the SECOND. A reader who disagrees with the threshold can see exactly
    what was substituted for the word and where.

    The threshold itself is not invented: it is BPHS 27's own required-virūpa
    table, which the Shadbala engine already computes. But BPHS's requirement
    is not Phaladīpikā's statement, and `measure_source_ref_ids` records that
    the measure comes from a different work than the rule.
    """

    planet: str
    textual_qualification: str
    software_interpretation: str
    satisfied: Optional[bool]
    measure: str = ""
    measured_value: Optional[float] = None
    threshold: Optional[float] = None
    measure_source_ref_ids: tuple[str, ...] = ()
    rule_source_ref_ids: tuple[str, ...] = ()
    afflictions: tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "textual_qualification": self.textual_qualification,
            "software_interpretation": self.software_interpretation,
            "satisfied": self.satisfied,
            "measure": self.measure,
            "measured_value": self.measured_value,
            "threshold": self.threshold,
            "measure_source_ref_ids": list(self.measure_source_ref_ids),
            "rule_source_ref_ids": list(self.rule_source_ref_ids),
            "afflictions": list(self.afflictions),
            "note": self.note,
        }


# ── Part 5: the dasha-conditioned activation ─────────────────────────────────

@dataclass(frozen=True)
class GocharaActivation:
    """
    Part 5's record, with the Vimshottari stack read and not recomputed.

    The three `is_*_lord` flags come from `engine.timing.vimshottari` through
    the caller. Nothing in this package computes a dasha period; Part 5
    forbids duplicating that, and a second Vimshottari implementation would
    be the one nobody tests.
    """

    transit_planet: str
    is_mahadasha_lord: bool = False
    is_antardasha_lord: bool = False
    is_pratyantardasha_lord: bool = False
    natal_strength: Optional[NatalStrengthCondition] = None
    transit_rule_result: Optional[GocharaPlacement] = None
    vedha_result: Optional[VedhaResult] = None

    @property
    def is_any_dasha_lord(self) -> bool:
        return (self.is_mahadasha_lord or self.is_antardasha_lord
                or self.is_pratyantardasha_lord)

    @property
    def dasha_levels(self) -> tuple[str, ...]:
        levels = []
        if self.is_mahadasha_lord:
            levels.append("mahadasha")
        if self.is_antardasha_lord:
            levels.append("antardasha")
        if self.is_pratyantardasha_lord:
            levels.append("pratyantardasha")
        return tuple(levels)

    def to_dict(self) -> dict:
        return {
            "transit_planet": self.transit_planet,
            "is_mahadasha_lord": self.is_mahadasha_lord,
            "is_antardasha_lord": self.is_antardasha_lord,
            "is_pratyantardasha_lord": self.is_pratyantardasha_lord,
            "dasha_levels": list(self.dasha_levels),
            "natal_strength": (self.natal_strength.to_dict()
                               if self.natal_strength else None),
            "transit_rule_result": (self.transit_rule_result.to_dict()
                                    if self.transit_rule_result else None),
            "vedha_result": (self.vedha_result.to_dict()
                             if self.vedha_result else None),
        }


# ── Part 7: the judgement, and whether strict may use it ─────────────────────

class GocharaVerdict(str, Enum):
    """
    What a rule concluded. `OBSTRUCTED` is not `UNFAVOURABLE`.

    A favourable transit that suffers vedha has had its good result
    neutralised, which the verses say plainly; they do not say it becomes an
    evil result. Merging the two would be an interpretation, and it would be
    this engine's rather than the text's.
    """

    FAVOURABLE = "FAVOURABLE"
    OBSTRUCTED = "OBSTRUCTED"
    UNFAVOURABLE = "UNFAVOURABLE"
    NOT_STATED = "NOT_STATED"

    @property
    def is_positive(self) -> bool:
        return self is GocharaVerdict.FAVOURABLE


@dataclass(frozen=True)
class GocharaJudgement:
    """
    One rule's complete finding about one transiting graha.

    Carries every layer that produced it. Part 1: "Do not allow a later rule
    to erase the provenance of an earlier condition" — so `placement`,
    `vedha`, `activation` and `natal_strength` all survive into the record
    even when a later one overrode an earlier one's verdict.
    """

    rule_id: str
    transit_planet: str
    reference_frame: TransitReference
    verdict: GocharaVerdict
    placement: Optional[GocharaPlacement] = None
    vedha: Optional[VedhaResult] = None
    activation: Optional[GocharaActivation] = None
    natal_strength: Optional[NatalStrengthCondition] = None
    houses_affected: tuple[int, ...] = ()
    house_frame: TransitReference = TransitReference.LAGNA
    source_ref_ids: tuple[str, ...] = ()
    validation_status: str = "UNVERIFIED"
    witness_agreement: WitnessAgreement = (
        WitnessAgreement.SINGLE_WITNESS_MATCHED)
    strict_eligible: bool = False
    not_strict_because: tuple[str, ...] = ()
    explanation: str = ""
    explanation_key: str = ""
    explanation_args: Mapping[str, object] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    @property
    def attributes_to_houses(self) -> bool:
        """
        Whether this judgement may be attached to a domain at all.

        Phaladīpikā 26 judges a transit favourable or obstructed in the
        Moon's frame and does not say which affairs it bears on; the bhāva
        significations this engine holds are stated from the LAGNA. So 26
        produces a verdict with no houses, and a verdict with no houses
        cannot reach a domain. 20.34 names the bhāva explicitly and can.
        """
        return bool(self.houses_affected)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "transit_planet": self.transit_planet,
            "reference_frame": self.reference_frame.value,
            "verdict": self.verdict.value,
            "placement": self.placement.to_dict() if self.placement else None,
            "vedha": self.vedha.to_dict() if self.vedha else None,
            "activation": (self.activation.to_dict()
                           if self.activation else None),
            "natal_strength": (self.natal_strength.to_dict()
                               if self.natal_strength else None),
            "houses_affected": list(self.houses_affected),
            "house_frame": self.house_frame.value,
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status,
            "witness_agreement": self.witness_agreement.value,
            "strict_eligible": self.strict_eligible,
            "not_strict_because": list(self.not_strict_because),
            "explanation": self.explanation,
            "explanation_key": self.explanation_key,
            "limitations": list(self.limitations),
        }


@dataclass
class GocharaResult:
    """Everything one gochara evaluation produced, for one moment."""

    reference_frames: tuple[TransitReference, ...] = ()
    judgements: list = field(default_factory=list)
    unevaluated: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    methodology_id: str = ""

    def for_planet(self, planet: str) -> list:
        return [j for j in self.judgements if j.transit_planet == planet]

    def for_rule(self, rule_id: str) -> list:
        return [j for j in self.judgements if j.rule_id == rule_id]

    @property
    def strict_eligible(self) -> list:
        return [j for j in self.judgements if j.strict_eligible]

    def to_dict(self) -> dict:
        return {
            "methodology_id": self.methodology_id,
            "reference_frames": [f.value for f in self.reference_frames],
            "judgements": [j.to_dict() for j in self.judgements],
            "unevaluated": list(self.unevaluated),
            "notes": list(self.notes),
            "note": (
                "Textual transit rules from located witnesses. A verdict "
                "here is what a verse states about a placement, not a "
                "prediction and not a probability."),
        }
