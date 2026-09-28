"""
Domain mapping evidence (V1.6 Parts 2, 3, 6, 7)
-------------------------------------------------
What stands behind the claim that a chart factor bears on a life domain.

THE GAP THIS CLOSES

    V1.5 shipped 17 domains and not one house mapping carried a witness. The
    consequence was visible in the synthesis layer: strict synthesis could
    speak about four domains, because the only source-qualified factor→domain
    links in the whole engine were kāraka attributions.

    V1.6 read BPHS chapter 11, which is the house-signification chapter, and
    chapters 21-24, which give the phala of the 10th, 11th and 12th and the
    doctrine of the house lords. Most of the mappings turn out to be
    attested, several in one word — `vṛtti` (livelihood) for the 10th,
    `jāyā` (wife) for the 7th, `putra` for the 5th.

FIVE FACTOR TYPES, KEPT APART (Part 3)

    HOUSE                 the bhāva signifies this area
    HOUSE_LORD            its lord's condition bears on the area
    KARAKA                a graha naturally signifies the area
    FUNCTIONAL_LORDSHIP   what the lord ALSO owns, for this Lagna
    VARGA                 a divisional chart refines the area

    These are different claims with different evidence and different
    strengths, and collapsing them into one "domain mapping" would hide
    which of them is actually sourced. BPHS 11.11 attests the HOUSE claim
    for career; BPHS 21.2 attests the HOUSE_LORD claim; no witness has been
    located for the VARGA claim that D10 refines career, and that shows.

WHAT THIS MODULE IS NOT

    It is not the mapping itself — that is `domains.py`. This is the
    vocabulary for saying how far each individual mapping has been traced,
    and the gate that decides which may enter strict synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..sources import ValidationStatus, witness_by_id


class FactorType(str, Enum):
    """Part 3: the five independent kinds of factor→domain link."""

    HOUSE = "HOUSE"
    HOUSE_LORD = "HOUSE_LORD"
    KARAKA = "KARAKA"
    FUNCTIONAL_LORDSHIP = "FUNCTIONAL_LORDSHIP"
    VARGA = "VARGA"


FACTOR_TYPE_MEANING = {
    FactorType.HOUSE:
        "The bhāva itself signifies this area of life. The strongest kind of "
        "mapping to source, because BPHS ch.11 states them as a list.",
    FactorType.HOUSE_LORD:
        "The condition of the bhāva's lord bears on the area. A separate "
        "claim from the house: BPHS 11.14-16 states it in general and ch.24 "
        "works it out lord by lord and house by house.",
    FactorType.KARAKA:
        "A graha naturally signifies the area, independently of which house "
        "it occupies or rules. BPHS ch.32 gives three different kāraka "
        "schemes, which do not agree with each other.",
    FactorType.FUNCTIONAL_LORDSHIP:
        "What the graha ALSO rules for this particular Lagna. BPHS 34.2-4 "
        "gives the kendrādhipatya doṣa and the malefic effect of the 3rd, "
        "6th and 11th lords.",
    FactorType.VARGA:
        "A divisional chart refines the area. The least sourced of the five: "
        "the named varga-to-topic assignments in common use (D10 career, D9 "
        "marriage, D7 children) have NOT been located in any witness this "
        "engine holds.",
}


class MappingClassification(str, Enum):
    """
    Part 9's vocabulary: what KIND of thing a factor→domain mapping is.

    A third axis, independent of the two the engine already carries.
    `ValidationStatus` says how far a mapping has been TRACED;
    `is_source_qualified` says whether it may carry a strict prediction.
    Neither can say that a located passage assigns the chart to something
    ELSE — which is the single most useful thing the V1.7 varga audit
    found, and which V1.7 could only record in prose.

    The distinction Part 9 insists on is between the last three:

        UNVERIFIED          nothing has been checked.
        TEXTUALLY_DIFFERENT the passage is about this chart and names a
                            different, adjacent subject. D10 is given
                            `mahat-phala`; "career" is the translator's
                            gloss, not the verse's word.
        CONTRADICTED        the passage assigns this chart to something the
                            mapping is not. BPHS 7.2 gives the caturthāṃśa
                            `bhāgya`, fortune — so D4-for-property is not
                            merely unattested, it is pointed elsewhere by
                            the one passage that speaks to it.

    A CONTRADICTED mapping still ships, because removing it would silently
    change every chart and because it is universal modern practice. It
    ships labelled.
    """

    TEXTUALLY_ATTESTED = "TEXTUALLY_ATTESTED"
    TEXTUALLY_DIFFERENT = "TEXTUALLY_DIFFERENT"
    TRADITIONAL_CONVENTION = "TRADITIONAL_CONVENTION"
    MODERN_CONVENTION = "MODERN_CONVENTION"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"

    @property
    def is_classical(self) -> bool:
        return self is MappingClassification.TEXTUALLY_ATTESTED


MAPPING_CLASSIFICATION_MEANING = {
    MappingClassification.TEXTUALLY_ATTESTED:
        "A located passage states this mapping. The verse's subject and the "
        "engine's domain are the same thing.",
    MappingClassification.TEXTUALLY_DIFFERENT:
        "A located passage speaks to this factor and names a different, "
        "usually adjacent, subject. Located without being qualified.",
    MappingClassification.TRADITIONAL_CONVENTION:
        "In continuous traditional use and not located in any witness this "
        "engine holds. Widely taught is not textually attested.",
    MappingClassification.MODERN_CONVENTION:
        "In common contemporary use, with no classical passage located for "
        "it in this form.",
    MappingClassification.UNVERIFIED:
        "Not yet classified against any source.",
    MappingClassification.CONTRADICTED:
        "A located passage assigns this factor to a DIFFERENT subject, so "
        "the mapping is not merely unattested but contradicted by the one "
        "passage that speaks to it. Retained, and labelled.",
}


@dataclass(frozen=True)
class DomainMappingEvidence:
    """
    One factor→domain link, with its provenance.

    `factor` is the thing itself — a house number, a graha name, a varga
    key — and `factor_type` says which of the five kinds of claim is being
    made about it. The pair is what carries the prediction, and the pair is
    what has to be sourced.
    """

    domain: str
    factor_type: FactorType
    factor: object
    source_ref_ids: tuple[str, ...] = ()
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    textual_term: str = ""          # the word in the text, e.g. "vṛtti"
    textual_condition: str = ""     # what the passage states
    software_condition: str = ""    # what the engine does with it
    notes: str = ""
    conflicts: tuple[str, ...] = ()
    needs_human_review: bool = False
    is_primary: bool = True
    classification: "MappingClassification" = (
        MappingClassification.UNVERIFIED)

    @property
    def is_located(self) -> bool:
        return bool(self.source_ref_ids)

    @property
    def is_contradicted(self) -> bool:
        """
        A located passage assigns this factor elsewhere.

        Kept as its own property rather than folded into
        `is_source_qualified`, which already returns False for it. The two
        answer different questions: "may this carry a strict prediction"
        and "did we look, and find the text saying something else".
        """
        return self.classification is MappingClassification.CONTRADICTED

    @property
    def is_source_qualified(self) -> bool:
        """
        Whether this link may carry a strict prediction (Part 7).

        Deliberately NOT the same as `is_located`. A mapping with a witness
        whose reading is disputed, or whose textual condition has not been
        written out, has been looked at rather than established.
        """
        if self.conflicts:
            return False
        if not self.source_ref_ids:
            return False
        if not self.textual_condition.strip():
            return False
        return self.validation_status.at_least(
            ValidationStatus.IMPLEMENTATION_MATCHED)

    def citations(self) -> list[str]:
        out = []
        for ref in self.source_ref_ids:
            try:
                out.append(witness_by_id(ref).citation())
            except KeyError:
                out.append(f"{ref} (unresolved)")
        return out

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "factor_type": self.factor_type.value,
            "factor": self.factor,
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status.value,
            "textual_term": self.textual_term,
            "textual_condition": self.textual_condition,
            "software_condition": self.software_condition,
            "is_primary": self.is_primary,
            "is_source_qualified": self.is_source_qualified,
            "classification": self.classification.value,
            "is_contradicted": self.is_contradicted,
            "conflicts": list(self.conflicts),
            "needs_human_review": self.needs_human_review,
            "notes": self.notes,
        }


def qualified_factors(mappings, factor_type: Optional[FactorType] = None
                      ) -> list[DomainMappingEvidence]:
    """Mappings that may carry strict predictions."""
    return [m for m in mappings
            if m.is_source_qualified
            and (factor_type is None or m.factor_type is factor_type)]


def coverage(mappings) -> dict:
    """Counts by factor type, for the domain report."""
    out: dict = {}
    for factor_type in FactorType:
        of_type = [m for m in mappings if m.factor_type is factor_type]
        out[factor_type.value] = {
            "total": len(of_type),
            "located": sum(1 for m in of_type if m.is_located),
            "source_qualified": sum(
                1 for m in of_type if m.is_source_qualified),
            "contradicted": sum(1 for m in of_type if m.is_contradicted),
        }
    return out


def classification_counts(mappings) -> dict:
    """Part 9's census, for the methodology screen and the audit."""
    counts = {c.value: 0 for c in MappingClassification}
    for mapping in mappings:
        counts[mapping.classification.value] += 1
    return counts
