"""
Source and provenance models (V1.3 Parts 2-5, 13)
--------------------------------------------------
The vocabulary for saying, precisely, what evidence stands behind a rule.

The problem this solves is specific. Up to V1.2 every rule carried a `source`
string like `"BPHS ch.36"`. Those strings were written by the implementing
model from memory. None was checked against a text, none identifies an
edition, and several may simply be wrong. A bare work name is not evidence:
Brihat Parashara Hora Shastra exists in many editions whose chapter and verse
numbering, Sanskrit wording and translations all differ, so "BPHS ch.36"
does not identify a passage any more than "the Bible, chapter 36" would.

Four claims are kept permanently apart, and no field in this module lets one
stand in for another:

    COMPUTATIONALLY TESTED      the code does what we told it to
    EXTERNALLY BENCHMARKED      the numbers match an independent reference
    TEXTUAL SOURCE LOCATED      a specific passage in a specific witness exists
    TRADITION/SOURCE VALIDATED  that passage actually states this rule

A green test suite is evidence for the first only. This module exists to stop
the first three being quietly reported as the fourth.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Part 3: authority levels ─────────────────────────────────────────────────

class SourceAuthority(str, Enum):
    """
    How much weight a witness can carry.

    Ordered from strongest to weakest. The ordering is used to decide whether
    a rule may claim validation, so it is deliberate rather than decorative.
    """

    PRIMARY_SANSKRIT_WITNESS = "PRIMARY_SANSKRIT_WITNESS"
    PRINTED_SANSKRIT_EDITION = "PRINTED_SANSKRIT_EDITION"
    CLASSICAL_COMMENTARY = "CLASSICAL_COMMENTARY"
    TRANSLATION = "TRANSLATION"
    MODERN_COMMENTARY = "MODERN_COMMENTARY"
    SECONDARY_REFERENCE = "SECONDARY_REFERENCE"
    WEB_SUMMARY = "WEB_SUMMARY"

    @property
    def rank(self) -> int:
        return _AUTHORITY_RANK[self]

    @property
    def is_sanskrit_tier(self) -> bool:
        """A witness to the Sanskrit itself, not to somebody's rendering of it."""
        return self in (SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
                        SourceAuthority.PRINTED_SANSKRIT_EDITION)

    @property
    def can_support_validation(self) -> bool:
        """
        Whether this authority may contribute to TRADITION_VALIDATED.

        A web summary never can. Modern astrology sites are useful for
        LOCATING a passage — they will tell you a yoga is "in BPHS chapter 36"
        — but they are downstream of the text and frequently repeat each
        other's errors, so they cannot be the thing that settles what the text
        says.
        """
        return self is not SourceAuthority.WEB_SUMMARY


_AUTHORITY_RANK = {
    SourceAuthority.PRIMARY_SANSKRIT_WITNESS: 0,
    SourceAuthority.PRINTED_SANSKRIT_EDITION: 1,
    SourceAuthority.CLASSICAL_COMMENTARY: 2,
    SourceAuthority.TRANSLATION: 3,
    SourceAuthority.MODERN_COMMENTARY: 4,
    SourceAuthority.SECONDARY_REFERENCE: 5,
    SourceAuthority.WEB_SUMMARY: 6,
}


class SourceType(str, Enum):
    """The physical form the witness takes."""

    DIGITAL_CRITICAL_TEXT = "DIGITAL_CRITICAL_TEXT"
    DIGITISED_PRINT = "DIGITISED_PRINT"
    PRINT = "PRINT"
    MANUSCRIPT = "MANUSCRIPT"
    WEBSITE = "WEBSITE"


# ── Part 2: the witness ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceWitness:
    """
    One specific textual witness to one specific passage.

    A Sanskrit text and an English translation of it are TWO witnesses, never
    one. Recording a translation under the original's name is the single most
    common provenance error in astrology software, and it matters because a
    translator's reading of an ambiguous compound is an interpretation, not
    the text.
    """

    id: str
    work: str                                   # e.g. "Bṛhajjātaka"
    traditional_author: Optional[str] = None    # e.g. "Varāhamihira"
    authority: SourceAuthority = SourceAuthority.SECONDARY_REFERENCE
    source_type: SourceType = SourceType.WEBSITE
    language: str = "unknown"

    # Edition identity. Two printings of "the same" work are different
    # witnesses if their numbering or wording differs.
    edition: Optional[str] = None
    editor_or_translator: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None

    # Where in the witness.
    volume: Optional[int] = None
    chapter: Optional[str] = None
    verse_start: Optional[str] = None
    verse_end: Optional[str] = None
    page: Optional[str] = None
    locator: Optional[str] = None               # the witness's own reference id

    # Integrity.
    retrieved_from: Optional[str] = None
    retrieved_on: Optional[str] = None
    checksum_if_local: Optional[str] = None

    # A SHORT normalised incipit, for locating the passage. Deliberately not a
    # full text or translation: see the note in RuleEvidence.
    incipit: Optional[str] = None
    notes: str = ""

    @property
    def has_locator(self) -> bool:
        """Whether this witness identifies a passage, not merely a work."""
        return bool(self.locator or (self.chapter and self.verse_start)
                    or self.page)

    @property
    def identifies_edition(self) -> bool:
        return bool(self.edition or self.publication_year or self.publisher
                    or self.retrieved_from)

    def citation(self) -> str:
        parts = [self.work]
        if self.traditional_author:
            parts.insert(0, self.traditional_author + ":")
        where = self.locator or ", ".join(
            bit for bit in (
                f"ch. {self.chapter}" if self.chapter else None,
                (f"v. {self.verse_start}"
                 + (f"-{self.verse_end}" if self.verse_end else ""))
                if self.verse_start else None,
                f"p. {self.page}" if self.page else None,
            ) if bit)
        if where:
            parts.append(where)
        if self.edition:
            parts.append(f"({self.edition})")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "work": self.work,
            "traditional_author": self.traditional_author,
            "authority": self.authority.value,
            "source_type": self.source_type.value,
            "language": self.language,
            "edition": self.edition,
            "editor_or_translator": self.editor_or_translator,
            "publication_year": self.publication_year,
            "publisher": self.publisher,
            "volume": self.volume,
            "chapter": self.chapter,
            "verse_start": self.verse_start,
            "verse_end": self.verse_end,
            "page": self.page,
            "locator": self.locator,
            "retrieved_from": self.retrieved_from,
            "retrieved_on": self.retrieved_on,
            "checksum_if_local": self.checksum_if_local,
            "incipit": self.incipit,
            "citation": self.citation(),
            "notes": self.notes,
        }


# ── Part 4: validation lifecycle ─────────────────────────────────────────────

class ValidationStatus(str, Enum):
    """
    How far a rule has actually been traced. Each step needs its own evidence;
    `engine.sources.validation` enforces that rather than trusting the label.

    The step that is easy to skip, and must not be, is between TEXT_LOCATED
    ("a website says this is in BPHS 36") and WITNESS_RECORDED ("this specific
    edition, at this chapter and verse, contains this"). Most astrology
    software stops at the first and reports the second.
    """

    UNVERIFIED = "UNVERIFIED"
    TEXT_LOCATED = "TEXT_LOCATED"
    WITNESS_RECORDED = "WITNESS_RECORDED"
    TRANSLATION_CHECKED = "TRANSLATION_CHECKED"
    RULE_INTERPRETATION_MAPPED = "RULE_INTERPRETATION_MAPPED"
    IMPLEMENTATION_MATCHED = "IMPLEMENTATION_MATCHED"
    SECOND_WITNESS_CHECKED = "SECOND_WITNESS_CHECKED"
    VALIDATED_FOR_PROFILE = "VALIDATED_FOR_PROFILE"
    TRADITION_VALIDATED = "TRADITION_VALIDATED"
    CONFLICTING_SOURCES = "CONFLICTING_SOURCES"
    IMPLEMENTATION_DIVERGES = "IMPLEMENTATION_DIVERGES"

    @property
    def rank(self) -> int:
        return _STATUS_RANK[self]

    @property
    def is_off_ladder(self) -> bool:
        """
        Statuses that assert a FINDING rather than a degree of progress.

        Both of these mean the audit produced a negative result, and neither
        is a weaker form of the rung below it. Ranking them numerically would
        invite `at_least` to treat them as partial progress, which is the one
        thing they must never read as.
        """
        return self in (ValidationStatus.CONFLICTING_SOURCES,
                        ValidationStatus.IMPLEMENTATION_DIVERGES)

    def at_least(self, other: "ValidationStatus") -> bool:
        """An off-ladder status never satisfies a floor."""
        if self.is_off_ladder:
            return False
        return self.rank >= other.rank


_STATUS_RANK = {
    ValidationStatus.UNVERIFIED: 0,
    ValidationStatus.TEXT_LOCATED: 1,
    ValidationStatus.WITNESS_RECORDED: 2,
    ValidationStatus.TRANSLATION_CHECKED: 3,
    ValidationStatus.RULE_INTERPRETATION_MAPPED: 4,
    ValidationStatus.IMPLEMENTATION_MATCHED: 5,
    ValidationStatus.SECOND_WITNESS_CHECKED: 6,
    ValidationStatus.VALIDATED_FOR_PROFILE: 7,
    ValidationStatus.TRADITION_VALIDATED: 8,
    ValidationStatus.CONFLICTING_SOURCES: -1,
    ValidationStatus.IMPLEMENTATION_DIVERGES: -2,
}

STATUS_MEANING = {
    ValidationStatus.UNVERIFIED:
        "No textual witness has been examined. The rule may still be correct "
        "and widely used; nothing has been checked.",
    ValidationStatus.TEXT_LOCATED:
        "A passage is believed to exist, but no witness has been recorded "
        "with an edition and a locator.",
    ValidationStatus.WITNESS_RECORDED:
        "A specific witness, edition and passage locator have been recorded.",
    ValidationStatus.TRANSLATION_CHECKED:
        "A translation witness has been recorded alongside the original.",
    ValidationStatus.RULE_INTERPRETATION_MAPPED:
        "What the passage states has been written out as a textual condition.",
    ValidationStatus.IMPLEMENTATION_MATCHED:
        "The textual condition has been mapped onto the software condition, "
        "and a test exercises it.",
    ValidationStatus.SECOND_WITNESS_CHECKED:
        "An independent second witness agrees. Independence is judged by the "
        "work: a compendium quoting an earlier text by name is that text "
        "speaking again, not a second voice.",
    ValidationStatus.VALIDATED_FOR_PROFILE:
        "Within one NAMED methodology profile, the rule is traced as far as "
        "this engine can take it: Sanskrit-tier witness, second independent "
        "witness, textual condition, matching software condition and a test. "
        "It is a claim about that profile and does not generalise to others, "
        "and it is still short of TRADITION_VALIDATED, which needs a human "
        "with the texts to close the outstanding questions.",
    ValidationStatus.TRADITION_VALIDATED:
        "A Sanskrit-tier witness, a second witness, an implementation mapping "
        "and human review all agree. This engine currently asserts this for "
        "nothing.",
    ValidationStatus.CONFLICTING_SOURCES:
        "Reputable witnesses disagree. No single reading has been adopted.",
    ValidationStatus.IMPLEMENTATION_DIVERGES:
        "A witness was located and read, and the software does NOT do what it "
        "says. This is the most informative status in the vocabulary and the "
        "least comfortable: it is not a gap in the evidence but a known "
        "defect in the code, kept visible until it is either corrected or "
        "justified as a deliberate variant.",
}


# ── Part 6: rule classification ──────────────────────────────────────────────

class RuleClassification(str, Enum):
    """What KIND of thing a shipped rule is, independent of how far traced."""

    CLASSICAL_SOURCE_VALIDATED = "CLASSICAL_SOURCE_VALIDATED"
    CLASSICAL_VARIANT = "CLASSICAL_VARIANT"
    TRADITIONAL_MODERN_CONVENTION = "TRADITIONAL_MODERN_CONVENTION"
    SOFTWARE_HEURISTIC = "SOFTWARE_HEURISTIC"
    UNVERIFIED = "UNVERIFIED"


CLASSIFICATION_MEANING = {
    RuleClassification.CLASSICAL_SOURCE_VALIDATED:
        "An exact textual source has been found and matched.",
    RuleClassification.CLASSICAL_VARIANT:
        "A recognised variant reading of a classical rule; the variant is "
        "attested, but differs from another attested reading.",
    RuleClassification.TRADITIONAL_MODERN_CONVENTION:
        "In common traditional use, but no primary text has been located for "
        "it in this form. Widely taught is not the same as textually attested.",
    RuleClassification.SOFTWARE_HEURISTIC:
        "An engine convention with no classical standing.",
    RuleClassification.UNVERIFIED:
        "Not yet classified against any source.",
}


# ── Part 17: human review ────────────────────────────────────────────────────

class ReviewReason(str, Enum):
    SANSKRIT_AMBIGUITY = "SANSKRIT_AMBIGUITY"
    TRANSLATION_DISAGREEMENT = "TRANSLATION_DISAGREEMENT"
    MANUSCRIPT_DISAGREEMENT = "MANUSCRIPT_DISAGREEMENT"
    UNCLEAR_REFERENCE_FRAME = "UNCLEAR_REFERENCE_FRAME"
    UNCLEAR_EXCEPTION = "UNCLEAR_EXCEPTION"
    COMMENTARY_REQUIRED = "COMMENTARY_REQUIRED"
    NO_WITNESS_AVAILABLE = "NO_WITNESS_AVAILABLE"
    NUMERIC_ENCODING_UNRESOLVED = "NUMERIC_ENCODING_UNRESOLVED"


@dataclass(frozen=True)
class ReviewItem:
    """
    A question that a human with the texts must settle.

    These exist because some questions cannot be answered by reading more
    code. An implementing model that resolves a Sanskrit ambiguity by picking
    the reading that makes its own implementation correct has not validated
    anything — it has laundered a guess. Such questions are queued here
    instead.
    """

    subject: str                 # rule id or "Varga:D9/standard"
    reason: ReviewReason
    question: str
    current_behaviour: str
    blocking: bool = True        # does it block TRADITION_VALIDATED?
    raised_on: str = ""

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "reason": self.reason.value,
            "question": self.question,
            "current_behaviour": self.current_behaviour,
            "blocking": self.blocking,
            "raised_on": self.raised_on,
        }


# ── Parts 7 and 11: conflicts ────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceConflict:
    """
    Two reputable witnesses that disagree.

    Modelled rather than resolved. Where both readings are live traditions the
    right answer is two rule profiles, not one blended definition that neither
    authority would recognise.
    """

    id: str
    topic: str
    witness_a: str               # witness id
    witness_b: str               # witness id, or a description when unregistered
    difference: str
    software_profiles_affected: tuple[str, ...] = ()
    resolution_status: str = "UNRESOLVED"
    resolution_note: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "witness_a": self.witness_a,
            "witness_b": self.witness_b,
            "difference": self.difference,
            "software_profiles_affected": list(self.software_profiles_affected),
            "resolution_status": self.resolution_status,
            "resolution_note": self.resolution_note,
        }


# ── Part 13: the evidence object ─────────────────────────────────────────────

@dataclass
class RuleEvidence:
    """
    Everything known about the provenance of one rule or Varga convention.

    `textual_summary` is a SHORT normalised paraphrase in the engine's own
    words, not a quotation. Two reasons: copyrighted translations must not be
    redistributed inside chart JSON, and a paraphrase makes it obvious that
    the reader is seeing the engine's understanding rather than the text.
    Anyone who needs the wording has the locator to go and read it.
    """

    subject: str                                  # rule id, or Varga key
    kind: str = "yoga"                            # "yoga" | "varga"
    rule_profile: Optional[str] = None
    classification: RuleClassification = RuleClassification.UNVERIFIED
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    witness_ids: tuple[str, ...] = ()
    textual_condition: str = ""                   # what the TEXT says
    software_condition: str = ""                  # what the CODE does
    reference_frame: str = ""                     # Lagna / Moon / Sun / other
    textual_summary: str = ""
    interpretive_notes: str = ""
    known_variants: tuple[str, ...] = ()
    ambiguities: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()               # SourceConflict ids
    implementation_test: str = ""                 # test that exercises it
    needs_human_review: bool = False
    review_reasons: tuple[str, ...] = ()
    last_reviewed: str = ""
    reviewer_notes: str = ""

    # ── V1.5 audit fields ───────────────────────────────────────────────────
    # `divergence` says, in one sentence, what the code does that the text
    # does not — the field that makes IMPLEMENTATION_DIVERGES actionable
    # rather than merely discouraging. `corrected_by` names the rule id that
    # implements the located reading, where one has been written; the
    # divergent rule is kept and not silently edited, so both readings are
    # available and the change is visible in the catalog rather than only in
    # a diff.
    divergence: str = ""
    corrected_by: Optional[str] = None
    audited_in: str = ""
    quotation_of: tuple[str, ...] = ()            # witness ids that quote others

    @property
    def has_witness(self) -> bool:
        return bool(self.witness_ids)

    @property
    def diverges(self) -> bool:
        return self.validation_status is ValidationStatus.IMPLEMENTATION_DIVERGES

    def to_dict(self, include_witnesses: bool = False) -> dict:
        data = {
            "subject": self.subject,
            "kind": self.kind,
            "rule_profile": self.rule_profile,
            "classification": self.classification.value,
            "validation_status": self.validation_status.value,
            "source_ref_ids": list(self.witness_ids),
            "textual_condition": self.textual_condition,
            "software_condition": self.software_condition,
            "reference_frame": self.reference_frame,
            "textual_summary": self.textual_summary,
            "known_variants": list(self.known_variants),
            "ambiguities": list(self.ambiguities),
            "conflicts": list(self.conflicts),
            "implementation_test": self.implementation_test,
            "needs_human_review": self.needs_human_review,
            "review_reasons": list(self.review_reasons),
            "last_reviewed": self.last_reviewed,
        }
        if self.divergence:
            data["divergence"] = self.divergence
        if self.corrected_by:
            data["corrected_by"] = self.corrected_by
        if self.audited_in:
            data["audited_in"] = self.audited_in
        if self.quotation_of:
            data["quotation_witnesses"] = list(self.quotation_of)
        if self.interpretive_notes:
            data["interpretive_notes"] = self.interpretive_notes
        if self.reviewer_notes:
            data["reviewer_notes"] = self.reviewer_notes
        return data


def today() -> str:
    return datetime.date.today().isoformat()
