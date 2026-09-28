"""
Life domains (V1.6 Parts 1, 2, 3, 6)
--------------------------------------
Declarative mappings from a life domain to the chart factors that bear on it,
each factor carrying its own provenance.

WHAT CHANGED IN V1.6, AND WHY IT MATTERS

    V1.5 shipped this module with a line saying that no house mapping had a
    located witness and that this was the engine's largest gap. It was.

    V1.6 read BPHS chapter 11 — `bhāvaviveka`, the house-signification
    chapter — which turns out to be exactly the list the domain model needed
    and to have been sitting in a file the engine already held. Twelve
    verses, one per bhāva, each naming what is to be examined from it. Most
    of the mappings are attested in a single word:

        11.11  vṛtti          livelihood          → CAREER, 10th
        11.8   jāyā           wife                → MARRIAGE, 7th
        11.6   putra          children            → CHILDREN, 5th
        11.12  āya            income              → FINANCE, 11th
        11.3   kuṭumba        family              → FAMILY, 2nd
        11.4   bhrātṛ         brother             → SIBLINGS, 3rd
        11.5   kṣetra, gṛha   land, house         → PROPERTY, 4th
        11.9   āyus           longevity           → LONGEVITY, 8th
        11.10  dharma         dharma              → SPIRITUALITY, 9th
        11.8   vāṇijya        trade               → BUSINESS, 7th

    Two of V1.5's mappings were WRONG and are corrected here. Two more were
    right for a reason V1.5 had not found.

THE CORRECTIONS

    EDUCATION was mapped to the 4th. BPHS 11.6 puts `vidyā` — learning — and
    `buddhi` — the intellect — at the FIFTH, alongside children. The 4th
    gets vehicles, relatives, the mother's comfort, treasure, land and
    house. The engine had followed a modern convention that the text does
    not support.

    RELATIONSHIPS was a separate domain with the same primary house as
    MARRIAGE. BPHS 11.8 gives `jāyā`, the wife, specifically. There is no
    located warrant for a general "relationships" domain distinct from
    marriage, so it keeps its mapping, is marked as having no house witness,
    and cannot enter strict synthesis.

FIVE FACTOR TYPES, NOT ONE (Part 3)

    A domain no longer has "a house" and "some karakas". It has a list of
    DomainMappingEvidence, each declaring which of five kinds of claim it
    makes and how far that claim has been traced. Career has a sourced HOUSE
    factor, a sourced HOUSE_LORD factor, and an UNSOURCED VARGA factor — and
    a reader can see which is which.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..houses.profiles import ReferenceSpace
from ..sources import ValidationStatus
from .domain_evidence import (
    DomainMappingEvidence, FactorType, MappingClassification,
    classification_counts, coverage, qualified_factors,
)


class Domain(str, Enum):
    """Part 6's initial domains."""

    CAREER = "CAREER"
    FINANCE = "FINANCE"
    WEALTH = "WEALTH"
    MARRIAGE = "MARRIAGE"
    RELATIONSHIPS = "RELATIONSHIPS"
    CHILDREN = "CHILDREN"
    EDUCATION = "EDUCATION"
    PROPERTY = "PROPERTY"
    HEALTH = "HEALTH"
    LONGEVITY = "LONGEVITY"
    FAMILY = "FAMILY"
    SIBLINGS = "SIBLINGS"
    TRAVEL = "TRAVEL"
    FOREIGN_RESIDENCE = "FOREIGN_RESIDENCE"
    SPIRITUALITY = "SPIRITUALITY"
    BUSINESS = "BUSINESS"
    LITIGATION = "LITIGATION"


HIGH_STAKES_DOMAINS = (Domain.HEALTH, Domain.LONGEVITY)

HIGH_STAKES_NOTE = (
    "Part 24: domain-level activation only. This engine does not and will "
    "not output a diagnosis, a disease, a date of death, or a probability of "
    "any of them. The underlying house and graha calculations are retained "
    "for completeness and are not converted into a claim about a person.")

# Witness ids, named once.
BHAVAVIVEKA = "BPHS_SA_11.2-13_BHAVAVIVEKA"
BHAVA_LORD = "BPHS_SA_11.14-16_BHAVA_STRENGTH"
KARMA_CH21 = "BPHS_SA_21.1-8_KARMABHAVA"
VYAYA_CH23 = "BPHS_SA_23.9-11_VYAYABHAVA"
BHAVESHA_CH24 = "BPHS_SA_24_BHAVESHAPHALA"
STHIRA_KARAKA = "BPHS_SA_32.18-21_STHIRA_KARAKA"
BHAVA_KARAKA = "BPHS_SA_32.22-24_BHAVA_KARAKA"
VARGAVIVEKA = "BPHS_SA_7.1-8_VARGAVIVEKA"

MATCHED = ValidationStatus.IMPLEMENTATION_MATCHED
MAPPED = ValidationStatus.RULE_INTERPRETATION_MAPPED
UNVERIFIED = ValidationStatus.UNVERIFIED

# V1.6 shipped this note on all eleven varga mappings. It was wrong, and it
# is kept verbatim so that the correction is legible rather than tidied
# away — the same treatment RESOLVED_UNAVAILABLE_WORKS gives the works V1.4
# declared unavailable.
_VARGA_UNSOURCED_V16 = (
    "The assignment of this divisional chart to this topic is standard "
    "modern practice. BPHS ch.6-7 give the shodashavarga and how to compute "
    "them; no passage located in any witness this engine holds assigns a "
    "varga to a life area. Not source-qualified, so it cannot carry strict "
    "synthesis.")

# WHAT V1.7 FOUND (Part 29)
#
#     BPHS 7.1-6, `vargavivekādhyāya`, assigns a subject to each of the
#     sixteen divisions in a single passage. V1.6 read chapter 6, found
#     only the computations, and concluded no such passage existed. It is
#     in the next chapter of the same file.
#
#     Locating it does NOT make every conventional mapping correct. Five
#     of the engine's eleven match the verse exactly; two are narrower or
#     broader than what it says; four are not in it at all, and one of
#     those — D4 for property — is contradicted, because the verse gives
#     D4 to bhāgya, fortune.
#
#     So the passage RAISES some mappings and CONVICTS others. A mapping is
#     source-qualified only where the verse states the engine's own claim.

_VARGA_NOT_IN_VERSE = (
    "BPHS 7.1-6 assigns a subject to each of the sixteen divisions and "
    "does not assign this one to this topic. The mapping is retained "
    "because it is standard modern practice, and it is recorded as "
    "MODERN_CONVENTION rather than classical. Not source-qualified.")


# Where a mapping's explanatory text belongs depends on whether there is a
# witness. With one, the text is what the PASSAGE states and goes in
# `textual_condition`. Without one, the text is the ENGINE explaining why it
# ships an unsourced mapping, and that is a note — putting it in
# `textual_condition` would dress an editorial decision as a quotation, and
# would let an unlocated mapping look identical to a located one at a glance.

# ── Part 9: classifying each mapping ────────────────────────────────────────
#
# Derived from the evidence the mapping already carries, rather than typed
# out per call site. A label written by hand beside a mapping is a label
# that can disagree with the mapping's own refs and status, and the whole
# point of the vocabulary is that it cannot.
#
# The one label that CANNOT be derived is CONTRADICTED: "the verse assigns
# this chart to something else" is not visible in the absence of a ref. It
# is passed explicitly, exactly once, for D4.

def _classify(refs, status, default) -> MappingClassification:
    if refs and status is MATCHED:
        return MappingClassification.TEXTUALLY_ATTESTED
    if refs:
        return MappingClassification.TEXTUALLY_DIFFERENT
    return default


def _split_text(text: str, refs) -> tuple[str, str]:
    """Return (textual_condition, notes) for a mapping."""
    return (text, "") if refs else ("", text)


def _house(domain: Domain, house: int, term: str, condition: str,
           primary: bool = True, refs=(BHAVAVIVEKA,),
           status=MATCHED, notes: str = "",
           classification=None, **kwargs) -> DomainMappingEvidence:
    textual, derived_notes = _split_text(condition, refs)
    return DomainMappingEvidence(
        domain=domain.value, factor_type=FactorType.HOUSE, factor=house,
        source_ref_ids=tuple(refs), validation_status=status,
        classification=classification or _classify(
            refs, status, MappingClassification.MODERN_CONVENTION),
        textual_term=term, textual_condition=textual,
        notes=notes or derived_notes,
        software_condition=(
            f"The {house}th bhāva, counted in RASHI space from the Lagna, is "
            f"treated as {'primary' if primary else 'secondary'} for "
            f"{domain.value}."),
        is_primary=primary, **kwargs)


def _lord(domain: Domain, house: int, condition: str,
          refs=(BHAVA_LORD, BHAVESHA_CH24), status=MATCHED,
          primary: bool = True, classification=None,
          **kwargs) -> DomainMappingEvidence:
    return DomainMappingEvidence(
        domain=domain.value, factor_type=FactorType.HOUSE_LORD,
        factor=house, source_ref_ids=tuple(refs), validation_status=status,
        classification=classification or _classify(
            refs, status, MappingClassification.MODERN_CONVENTION),
        textual_condition=condition,
        software_condition=(
            f"The dignity, placement, combustion and Shadbala of the lord of "
            f"the {house}th are treated as evidence for {domain.value}."),
        is_primary=primary, **kwargs)


def _karaka(domain: Domain, planet: str, term: str, condition: str,
            refs=(), status=UNVERIFIED, notes: str = "",
            classification=None, **kwargs) -> DomainMappingEvidence:
    textual, derived_notes = _split_text(condition, refs)
    return DomainMappingEvidence(
        domain=domain.value, factor_type=FactorType.KARAKA, factor=planet,
        source_ref_ids=tuple(refs), validation_status=status,
        classification=classification or _classify(
            refs, status, MappingClassification.TRADITIONAL_CONVENTION),
        textual_term=term, textual_condition=textual,
        notes=notes or derived_notes or condition,
        software_condition=(
            f"{planet}'s dignity and affliction are treated as evidence for "
            f"{domain.value}."),
        **kwargs)


def _varga(domain: Domain, chart: str, term: str = "", condition: str = "",
           refs=(), status=UNVERIFIED, notes: str = "",
           needs_human_review: bool = True, classification=None, **kwargs
           ) -> DomainMappingEvidence:
    """
    One divisional chart offered as confirmation for one domain.

    `refs` empty means the verse does not say this, and the mapping cannot
    carry strict synthesis however widely it is used. `status` below
    IMPLEMENTATION_MATCHED means the verse says something NEAR this — the
    subject is broader, narrower or glossed — which is located but still
    not qualified. The gate reads both; neither is argued around here.
    """
    textual, derived_notes = _split_text(condition, refs)
    return DomainMappingEvidence(
        domain=domain.value, factor_type=FactorType.VARGA, factor=chart,
        source_ref_ids=tuple(refs), validation_status=status,
        classification=classification or _classify(
            refs, status, MappingClassification.MODERN_CONVENTION),
        textual_term=term, textual_condition=textual,
        software_condition=(
            f"{chart} placements are used to confirm or qualify a "
            f"{domain.value} theme already present in D1."),
        notes=notes or derived_notes or _VARGA_NOT_IN_VERSE,
        needs_human_review=needs_human_review, **kwargs)


def _varga_attested(domain: Domain, chart: str, term: str, condition: str,
                    **kwargs) -> DomainMappingEvidence:
    """A varga whose subject in BPHS 7 IS the engine's domain."""
    return _varga(domain, chart, term=term, condition=condition,
                  refs=(VARGAVIVEKA,), status=MATCHED,
                  needs_human_review=False, **kwargs)


@dataclass(frozen=True)
class Karaka:
    """One significator, retained as a view onto the KARAKA mappings."""

    planet: str
    signifies: str
    validation_status: str = "UNVERIFIED"
    source_ref_ids: tuple[str, ...] = ()
    note: str = ""

    @property
    def is_located(self) -> bool:
        return bool(self.source_ref_ids)

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "signifies": self.signifies,
            "validation_status": self.validation_status,
            "source_ref_ids": list(self.source_ref_ids),
            "note": self.note,
        }


@dataclass(frozen=True)
class DomainSpec:
    """
    A domain's declarative mapping (Part 6's DomainDefinition).

    `mappings` is the authoritative list; the house and karaka accessors
    below are derived views, kept so that V1.5 callers and the report layer
    do not each re-implement the filtering.
    """

    domain: Domain
    label: str
    mappings: tuple[DomainMappingEvidence, ...] = ()
    challenging_houses: tuple[int, ...] = ()
    methodology_profile: str = "parashari_textual_v16"
    reference_space: ReferenceSpace = ReferenceSpace.RASHI
    house_system_compatibility: tuple[str, ...] = ("whole_sign",)
    relevant_yoga_categories: tuple[str, ...] = ()
    notes: str = ""

    # ── derived views ───────────────────────────────────────────────────────

    def factors(self, factor_type: FactorType, primary=None
                ) -> list[DomainMappingEvidence]:
        return [m for m in self.mappings
                if m.factor_type is factor_type
                and (primary is None or m.is_primary == primary)]

    @property
    def primary_house(self) -> int:
        houses = self.factors(FactorType.HOUSE, primary=True)
        return houses[0].factor if houses else 1

    @property
    def secondary_houses(self) -> tuple[int, ...]:
        return tuple(m.factor for m in self.factors(FactorType.HOUSE,
                                                    primary=False))

    @property
    def all_houses(self) -> tuple[int, ...]:
        return tuple(m.factor for m in self.factors(FactorType.HOUSE))

    @property
    def karakas(self) -> tuple[Karaka, ...]:
        return tuple(
            Karaka(planet=m.factor, signifies=m.textual_condition,
                   validation_status=m.validation_status.value,
                   source_ref_ids=m.source_ref_ids, note=m.notes)
            for m in self.factors(FactorType.KARAKA))

    @property
    def primary_vargas(self) -> tuple[str, ...]:
        return ("D1",) + tuple(
            m.factor for m in self.factors(FactorType.VARGA, primary=True))

    @property
    def optional_vargas(self) -> tuple[str, ...]:
        return tuple(m.factor for m in self.factors(FactorType.VARGA,
                                                    primary=False))

    @property
    def is_high_stakes(self) -> bool:
        return self.domain in HIGH_STAKES_DOMAINS

    # ── Part 7: the strict gate ─────────────────────────────────────────────

    @property
    def source_qualified_mappings(self) -> list[DomainMappingEvidence]:
        return qualified_factors(self.mappings)

    def qualifies_for_strict(self, factor_type: FactorType,
                             factor) -> bool:
        """
        Whether THIS factor may carry a strict prediction for THIS domain.

        The Part 7 question, asked at the granularity that matters. A chart
        can have a perfectly sound Shadbala figure for the 10th lord and
        that says nothing about career unless the 10th-lord→CAREER link is
        itself sourced — which, since V1.6, it is.
        """
        for mapping in self.mappings:
            if mapping.factor_type is factor_type and mapping.factor == factor:
                return mapping.is_source_qualified
        return False

    @property
    def strict_eligible(self) -> bool:
        return bool(self.source_qualified_mappings)

    def to_dict(self) -> dict:
        data = {
            "domain": self.domain.value,
            "label": self.label,
            "primary_house": self.primary_house,
            "secondary_houses": list(self.secondary_houses),
            "challenging_houses": list(self.challenging_houses),
            "karakas": [k.to_dict() for k in self.karakas],
            "primary_vargas": list(self.primary_vargas),
            "optional_vargas": list(self.optional_vargas),
            "methodology_profile": self.methodology_profile,
            "reference_space": self.reference_space.value,
            "house_system_compatibility":
                list(self.house_system_compatibility),
            "relevant_yoga_categories": list(self.relevant_yoga_categories),
            "mappings": [m.to_dict() for m in self.mappings],
            "coverage": coverage(self.mappings),
            "strict_eligible": self.strict_eligible,
            "notes": self.notes,
        }
        if self.is_high_stakes:
            data["output_constraint"] = HIGH_STAKES_NOTE
        return data


# ── the audited mappings ─────────────────────────────────────────────────────

DOMAINS: dict[Domain, DomainSpec] = {

    Domain.CAREER: DomainSpec(
        domain=Domain.CAREER, label="Career and profession",
        mappings=(
            _house(Domain.CAREER, 10, "vṛtti",
                   "BPHS 11.11: from the tenth are examined sovereignty, "
                   "the sky, LIVELIHOOD (vṛtti), honour, the father, "
                   "residence abroad and debt."),
            _lord(Domain.CAREER, 10,
                  "BPHS 21.2-4: a STRONG tenth lord (sabala) in exaltation, "
                  "own navāṃśa or own sign gives renown and good works; a "
                  "weak one gives deficiency in occupation; joined with "
                  "benefics it gives gain at the king's gate and in trade.",
                  refs=(KARMA_CH21, BHAVA_LORD, BHAVESHA_CH24)),
            _house(Domain.CAREER, 2, "dhana",
                   "BPHS 11.3: wealth and grain from the second.",
                   primary=False),
            _house(Domain.CAREER, 11, "āya",
                   "BPHS 11.12: income and increase from the eleventh.",
                   primary=False),
            _house(Domain.CAREER, 6, "śatru",
                   "BPHS 11.7: enemies and wounds from the sixth. Its "
                   "relevance to service and employment is a modern reading "
                   "and is NOT in the verse.",
                   primary=False, status=UNVERIFIED, refs=(),
                   needs_human_review=True),
            _karaka(Domain.CAREER, "Surya", "",
                    "Authority and station. Not in any located kāraka "
                    "scheme; BPHS 32.22 gives the Sun in the 9th for the "
                    "FATHER, which is a different claim.",
                    needs_human_review=True),
            _karaka(Domain.CAREER, "Shani", "",
                    "Labour and service. Not located; BPHS 32.24 gives "
                    "Saturn in the 8th for death.",
                    needs_human_review=True),
            # Located, NOT qualified. The verse gives D10 mahat-phala,
            # "great fruit" — Santhanam renders it "power (and position)"
            # and glosses it "i.e. livelihood etc." in a footnote. The
            # gloss is the translator's. Profession is a narrower claim
            # than the verse makes, so this is RULE_INTERPRETATION_MAPPED
            # and strict still declines it.
            _varga(Domain.CAREER, "D10", term="mahat-phala",
                   condition=(
                       "BPHS 7.3: daśamāṃśe mahatphalam — the great fruit "
                       "from the daśāṃśa. The verse does not say vṛtti, "
                       "the word 11.11 uses for livelihood."),
                   refs=(VARGAVIVEKA,), status=MAPPED),
            # BPHS 7.3 assigns D9 to the SPOUSE. Using it as a general
            # strength check on any domain is modern practice with no
            # support in the passage that assigns the vargas.
            _varga(Domain.CAREER, "D9", is_primary=False),
        ),
        challenging_houses=(8, 12),
        relevant_yoga_categories=("raja", "mahapurusha"),
        notes="Primary house and house lord both sourced; vargas are not."),

    Domain.FINANCE: DomainSpec(
        domain=Domain.FINANCE, label="Income and cash flow",
        mappings=(
            _house(Domain.FINANCE, 11, "āya",
                   "BPHS 11.12: from the eleventh are examined various "
                   "goods, INCOME (āya), increase and cattle."),
            _lord(Domain.FINANCE, 11,
                  "BPHS 24.11: the Lagna lord in the eleventh gives one "
                  "always possessed of gains."),
            _house(Domain.FINANCE, 2, "dhana",
                   "BPHS 11.3: wealth and grain from the second.",
                   primary=False),
            _house(Domain.FINANCE, 9, "bhāgya",
                   "BPHS 11.10: fortune (bhāgya) from the ninth.",
                   primary=False),
            _karaka(Domain.FINANCE, "Guru", "",
                    "Expansion and fortune. Not in a located kāraka scheme.",
                    needs_human_review=True),
            _karaka(Domain.FINANCE, "Shukra", "",
                    "Assets and comfort. BPHS 32.23 gives Venus in the 7th "
                    "for the WIFE, which is a different claim.",
                    needs_human_review=True),
        ),
        challenging_houses=(6, 12),
        relevant_yoga_categories=("dhana",),
        notes="Primary house and house lord sourced."),

    Domain.WEALTH: DomainSpec(
        domain=Domain.WEALTH, label="Accumulated wealth",
        mappings=(
            _house(Domain.WEALTH, 2, "dhana-dhānya",
                   "BPHS 11.3: from the second are examined WEALTH AND "
                   "GRAIN (dhana-dhānya), family, the death-net, enemies, "
                   "and metals and gems (dhātu-ratna)."),
            _lord(Domain.WEALTH, 2,
                  "BPHS 11.14-16: a bhāva conjoined with or aspected by "
                  "benefics or its own lord gives its comfort; where the "
                  "lord is destroyed or joined with the trika lords, the "
                  "bhāva's results are declared lost."),
            _house(Domain.WEALTH, 11, "āya",
                   "BPHS 11.12: income and increase from the eleventh.",
                   primary=False),
            _karaka(Domain.WEALTH, "Guru", "",
                    "Wealth. Not in a located kāraka scheme.",
                    needs_human_review=True),
            # V1.8 Part 8. The V1.7 audit found this in the passage and did
            # not add it, because adding a factor changes synthesis output
            # and V1.7 was a productization release. It is added here as the
            # verse states it and through the same gates as every other
            # varga mapping — no special case, no override.
            _varga_attested(
                Domain.WEALTH, "D2", "sampad",
                "BPHS 7.1: `horāyāṃ sampadādikam` — from the horā, wealth "
                "and the like. The verse's subject and the engine's domain "
                "are the same thing, and `sampad` is the same register as "
                "the `dhana` BPHS 11.3 gives the second house."),
        ),
        challenging_houses=(12, 6),
        relevant_yoga_categories=("dhana", "vipareeta_raja"),
        notes=(
            "BPHS 41.16 separately names the lords of the ninth and fifth as "
            "wealth-givers. The engine's generic Dhana Yoga lord-pair rule "
            "remains unlocated — see the DHANA_YOGA_NOT_LOCATED conflict.")),

    Domain.MARRIAGE: DomainSpec(
        domain=Domain.MARRIAGE, label="Marriage and partnership",
        mappings=(
            _house(Domain.MARRIAGE, 7, "jāyā",
                   "BPHS 11.8: from the seventh are examined the WIFE "
                   "(jāyā), road travel, trade, recovery of what is lost, "
                   "and the death of one's own body."),
            _lord(Domain.MARRIAGE, 7,
                  "BPHS 24.7: the Lagna lord in the seventh with a malefic "
                  "— the wife does not live; with a benefic, other results. "
                  "The house lord's condition bears on the marriage.",
                  refs=(BHAVESHA_CH24, BHAVA_LORD)),
            _karaka(Domain.MARRIAGE, "Shukra", "dārāḥ",
                    "BPHS 32.23: `dārāḥ śukrāc ca saptame` — the wife from "
                    "Venus, in the seventh. BPHS 32.20 independently gives "
                    "`śukrāt patiḥ`, the spouse from Venus, in the sthira "
                    "kāraka list. Two schemes in one chapter agreeing.",
                    refs=(BHAVA_KARAKA, STHIRA_KARAKA), status=MATCHED),
            _house(Domain.MARRIAGE, 2, "kuṭumba",
                   "BPHS 11.3: family from the second.", primary=False),
            _varga_attested(
                Domain.MARRIAGE, "D9", "kalatra",
                "BPHS 7.3: navamāṃśe kalatrāṇām — the spouse is examined "
                "from the navāṃśa. The verse's subject and the engine's "
                "domain are the same thing."),
        ),
        challenging_houses=(6, 8, 12),
        notes=(
            "The best-sourced domain in the engine: house, house lord and "
            "kāraka are each attested, and the kāraka twice in one chapter.")),

    Domain.RELATIONSHIPS: DomainSpec(
        domain=Domain.RELATIONSHIPS, label="Relationships generally",
        mappings=(
            _house(Domain.RELATIONSHIPS, 7, "",
                   "", primary=True, refs=(), status=UNVERIFIED,
                   needs_human_review=True,
                   notes=(
                       "NOT LOCATED. BPHS 11.8 gives the seventh as `jāyā` "
                       "— the wife — specifically. No witness has been "
                       "located for a general 'relationships' domain "
                       "distinct from marriage, and this domain is a modern "
                       "convenience. It keeps its mapping, cannot enter "
                       "strict synthesis, and says so.")),
            _house(Domain.RELATIONSHIPS, 11, "", "", primary=False, refs=(),
                   status=UNVERIFIED, needs_human_review=True,
                   notes=(
                       "NOT LOCATED. BPHS 11.12 gives the eleventh income, "
                       "increase and cattle. Its modern association with "
                       "friends and social circles is not in the verse.")),
            _karaka(Domain.RELATIONSHIPS, "Shukra", "",
                    "Attraction and union. The located Venus attributions "
                    "are to the WIFE specifically, not to relationships in "
                    "general.", needs_human_review=True),
        ),
        challenging_houses=(6, 12),
        notes=(
            "A domain with no located house witness. Retained because "
            "removing it would silently narrow the engine's output, and "
            "excluded from strict synthesis because nothing supports it.")),

    Domain.CHILDREN: DomainSpec(
        domain=Domain.CHILDREN, label="Children and progeny",
        mappings=(
            _house(Domain.CHILDREN, 5, "putra",
                   "BPHS 11.6: from the fifth are examined yantra and "
                   "mantra, learning, the faculty of intellect, and "
                   "CHILDREN (putra)."),
            _lord(Domain.CHILDREN, 5,
                  "BPHS 24.5: the Lagna lord in the fifth gives middling "
                  "happiness from children and loss of the firstborn.",
                  refs=(BHAVESHA_CH24, BHAVA_LORD)),
            _karaka(Domain.CHILDREN, "Guru", "putra",
                    "BPHS 32.23: `devejyāt pañcamāt putro` — the son from "
                    "Jupiter, in the fifth.",
                    refs=(BHAVA_KARAKA,), status=MATCHED),
            _karaka(Domain.CHILDREN, "Shani", "putra",
                    "BPHS 32.20: `putraḥ śanaiścarāt` — the son from "
                    "Saturn, in the sthira kāraka list. Retained as a "
                    "second reading; see the PUTRAKARAKA_ATTRIBUTION "
                    "conflict, which V1.6 resolved in favour of Jupiter on "
                    "the evidence of 32.23 without discarding this verse.",
                    refs=(STHIRA_KARAKA,), status=MAPPED,
                    conflicts=("PUTRAKARAKA_ATTRIBUTION",),
                    needs_human_review=True),
            _house(Domain.CHILDREN, 9, "bhāgya",
                   "BPHS 11.10: fortune from the ninth.", primary=False),
            _varga_attested(
                Domain.CHILDREN, "D7", "putra-pautra",
                "BPHS 7.2: putrapautrādikānāṃ vai cintanaṃ saptamāṃśake — "
                "sons, grandsons and the rest are considered from the "
                "saptāṃśa."),
        ),
        challenging_houses=(1, 4, 10),
        notes=(
            "The challenging houses are the common putra-bhāva reckoning "
            "and are NOT in any located verse.")),

    Domain.EDUCATION: DomainSpec(
        domain=Domain.EDUCATION, label="Education and learning",
        mappings=(
            _house(Domain.EDUCATION, 5, "vidyā",
                   "BPHS 11.6: from the fifth are examined yantra and "
                   "mantra, LEARNING (vidyā), and the faculty of intellect "
                   "(buddheś ca prabandhakam)."),
            _lord(Domain.EDUCATION, 5,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _house(Domain.EDUCATION, 4, "",
                   "", primary=False, refs=(), status=UNVERIFIED,
                   needs_human_review=True,
                   notes=(
                       "V1.5 made the FOURTH the primary house for "
                       "education. BPHS 11.5 gives the fourth vehicles, "
                       "relatives, the mother's comfort, treasure, land and "
                       "house — and no learning. The fourth is retained as "
                       "secondary, unsourced, because the modern "
                       "association is widespread; the primary has moved to "
                       "the fifth, where the text puts vidyā.")),
            _house(Domain.EDUCATION, 9, "dharma",
                   "BPHS 11.10: dharma from the ninth.", primary=False),
            _karaka(Domain.EDUCATION, "Budha", "",
                    "Intellect and articulation. BPHS 32.23 gives Mercury "
                    "in the 6th for the MATERNAL UNCLE, a different claim.",
                    needs_human_review=True),
            _karaka(Domain.EDUCATION, "Guru", "",
                    "Higher learning. Not in a located kāraka scheme.",
                    needs_human_review=True),
            _varga_attested(
                Domain.EDUCATION, "D24", "vidyā",
                "BPHS 7.5: vidyāyā vedabāhvaṃśe — learning from the "
                "twenty-fourth part. The same word, vidyā, that 11.6 puts "
                "in the fifth house.",
                is_primary=False),
        ),
        challenging_houses=(8, 12),
        relevant_yoga_categories=("vidya", "intellect"),
        notes=(
            "CORRECTED IN V1.6. The primary house moved from the 4th to the "
            "5th on the evidence of BPHS 11.6.")),

    Domain.PROPERTY: DomainSpec(
        domain=Domain.PROPERTY, label="Land, property and vehicles",
        mappings=(
            _house(Domain.PROPERTY, 4, "kṣetra, gṛha, vāhana",
                   "BPHS 11.5: from the fourth are examined VEHICLES "
                   "(vāhana), relatives, the mother's comfort, treasure "
                   "(nidhi), LAND (kṣetra) and HOUSE (gṛha)."),
            _lord(Domain.PROPERTY, 4,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _house(Domain.PROPERTY, 2, "dhana",
                   "BPHS 11.3: wealth from the second.", primary=False),
            _karaka(Domain.PROPERTY, "Mangal", "",
                    "Land. BPHS 32.23 gives Mars in the 3rd for the "
                    "BROTHER, a different claim.", needs_human_review=True),
            _karaka(Domain.PROPERTY, "Shukra", "",
                    "Vehicles and comfort. Not located for this.",
                    needs_human_review=True),
            # CONTRADICTED, not merely unsourced. BPHS 7.2 gives the
            # caturthāṃśa bhāgya — fortune — not land or house. The modern
            # reading of D4 as the property chart comes from the fourth
            # HOUSE, which 11.5 does give kṣetra and gṛha; the division
            # and the house have been conflated somewhere later. The
            # mapping ships because it is standard, and it is marked.
            _varga(Domain.PROPERTY, "D4", is_primary=False,
                   classification=MappingClassification.CONTRADICTED,
                   notes=(
                       "BPHS 7.2 assigns the caturthāṃśa to bhāgya, "
                       "fortune. It does not assign it to land or house. "
                       "This mapping is MODERN_CONVENTION and the located "
                       "verse points elsewhere, so it is not merely "
                       "unsourced — it disagrees with the one passage that "
                       "assigns the divisions.")),
        ),
        challenging_houses=(3, 8, 12),
        notes="House and house lord sourced; vehicles named in the verse."),

    Domain.HEALTH: DomainSpec(
        domain=Domain.HEALTH, label="Health and vitality",
        mappings=(
            _house(Domain.HEALTH, 1, "deha, balābala",
                   "BPHS 11.2: from the Lagna are examined the BODY (deha), "
                   "form, knowledge, complexion, STRENGTH AND WEAKNESS "
                   "(balābala), happiness and sorrow, and disposition."),
            _house(Domain.HEALTH, 6, "vraṇa",
                   "BPHS 11.7: from the sixth are examined the maternal "
                   "uncle, fear of death, enemies, and WOUNDS (vraṇādikān).",
                   primary=False),
            _lord(Domain.HEALTH, 1,
                  "BPHS 24.6: the Lagna lord in the sixth gives one devoid "
                  "of bodily comfort, and with malefics, affliction from "
                  "enemies.", refs=(BHAVESHA_CH24, BHAVA_LORD)),
            _karaka(Domain.HEALTH, "Surya", "",
                    "Vitality. Not in a located kāraka scheme.",
                    needs_human_review=True),
            # D6 is not one of the ṣoḍaśavarga at all. BPHS 6.2-4 lists
            # the sixteen and the ṣaṣṭhāṃśa is not among them, so there is
            # no verse to locate and no division in this engine's own
            # varga set either.
            _varga(Domain.HEALTH, "D6", is_primary=False,
                   notes=(
                       "D6 is not one of the sixteen divisions BPHS 6.2-4 "
                       "names, so BPHS 7 cannot assign it a subject and "
                       "this engine does not compute it. Retained only as "
                       "a record of the convention.")),
        ),
        challenging_houses=(6, 8, 12),
        notes=HIGH_STAKES_NOTE),

    Domain.LONGEVITY: DomainSpec(
        domain=Domain.LONGEVITY, label="Longevity factors",
        mappings=(
            _house(Domain.LONGEVITY, 8, "āyus",
                   "BPHS 11.9: from the eighth are examined LONGEVITY "
                   "(āyus), battle, enemies, the fort, and the wealth of "
                   "the dead."),
            _lord(Domain.LONGEVITY, 8,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _house(Domain.LONGEVITY, 1, "deha",
                   "BPHS 11.2: the body from the Lagna.", primary=False),
            _karaka(Domain.LONGEVITY, "Shani", "mṛtyu",
                    "BPHS 32.24: `mandād aṣṭamato mṛtyuḥ` — death from "
                    "Saturn, in the eighth.",
                    refs=(BHAVA_KARAKA,), status=MATCHED),
        ),
        challenging_houses=(2, 7),
        notes=HIGH_STAKES_NOTE),

    Domain.FAMILY: DomainSpec(
        domain=Domain.FAMILY, label="Family and domestic life",
        mappings=(
            _house(Domain.FAMILY, 2, "kuṭumba",
                   "BPHS 11.3: from the second are examined wealth and "
                   "grain, the FAMILY (kuṭumba), the death-net, enemies, "
                   "and metals and gems."),
            _lord(Domain.FAMILY, 2,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _house(Domain.FAMILY, 4, "bandhu",
                   "BPHS 11.5: RELATIVES (bandhu) and the mother's comfort "
                   "from the fourth.", primary=False),
            _karaka(Domain.FAMILY, "Chandra", "mātā",
                    "BPHS 32.22: `candrān mātā caturthake` — the mother "
                    "from the Moon, in the fourth.",
                    refs=(BHAVA_KARAKA,), status=MATCHED),
            _karaka(Domain.FAMILY, "Surya", "tāta",
                    "BPHS 32.22: `ravitaḥ puṇyabhe tātaḥ` — the father from "
                    "the Sun, in the ninth. BPHS 32.18 independently gives "
                    "the stronger of Sun and Venus as the pitṛkāraka; the "
                    "engine does not compute that comparison, so the "
                    "sthira reading is located but not implemented.",
                    refs=(BHAVA_KARAKA, STHIRA_KARAKA), status=MATCHED),
            # Located, NOT qualified. The verse gives D12 to PARENTS
            # specifically; the engine's FAMILY domain is wider than that,
            # and widening a verse is the error this audit exists to catch.
            _varga(Domain.FAMILY, "D12", term="pitṛ",
                   condition=(
                       "BPHS 7.3: dvādaśāṃśe tathā pitroḥ — the parents "
                       "from the twelfth part. Parents, not the household."),
                   refs=(VARGAVIVEKA,), status=MAPPED, is_primary=False),
        ),
        challenging_houses=(6, 12),
        notes="House, house lord and two karakas sourced."),

    Domain.SIBLINGS: DomainSpec(
        domain=Domain.SIBLINGS, label="Siblings",
        mappings=(
            _house(Domain.SIBLINGS, 3, "bhrātṛ",
                   "BPHS 11.4: from the third are examined valour "
                   "(vikrama), servants and BROTHERS (bhṛtya-bhrātrādi), "
                   "instruction, and travel."),
            _lord(Domain.SIBLINGS, 3,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _karaka(Domain.SIBLINGS, "Mangal", "bhrātā",
                    "BPHS 32.23: `kujāt tṛtīyato bhrātā` — the brother from "
                    "Mars, in the third. BPHS 32.19 independently gives the "
                    "sister and brother-in-law from Mars.",
                    refs=(BHAVA_KARAKA, STHIRA_KARAKA), status=MATCHED),
            _house(Domain.SIBLINGS, 11, "āya",
                   "BPHS 11.12: the eleventh. Its association with elder "
                   "siblings is a modern reading not in the verse.",
                   primary=False, refs=(), status=UNVERIFIED,
                   needs_human_review=True),
            _varga_attested(
                Domain.SIBLINGS, "D3", "bhrātṛja-saukhya",
                "BPHS 7.2: dreṣkāṇe bhrātṛjaṃ saukhyam — happiness arising "
                "from brothers, from the drekkāṇa.",
                is_primary=False),
        ),
        challenging_houses=(6, 12),
        notes="House, house lord and kāraka all sourced."),

    Domain.TRAVEL: DomainSpec(
        domain=Domain.TRAVEL, label="Travel and movement",
        mappings=(
            _house(Domain.TRAVEL, 3, "prayāṇa",
                   "BPHS 11.4: from the third are examined valour, "
                   "brothers, instruction and TRAVEL (upadeśa-prayāṇakam)."),
            _house(Domain.TRAVEL, 7, "adhva-prayāṇa",
                   "BPHS 11.8: from the seventh, ROAD TRAVEL "
                   "(adhva-prayāṇa) among other things.", primary=False),
            _house(Domain.TRAVEL, 9, "tīrthayātrā",
                   "BPHS 11.10: from the ninth, PILGRIMAGE (tīrthayātrā).",
                   primary=False),
            _lord(Domain.TRAVEL, 3,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _karaka(Domain.TRAVEL, "Chandra", "",
                    "Movement. Not in a located kāraka scheme.",
                    needs_human_review=True),
        ),
        challenging_houses=(4,),
        notes=(
            "Three houses attested, which is more than V1.5 assigned: the "
            "3rd for travel generally, the 7th for road travel and the 9th "
            "for pilgrimage. V1.5's 12th is not supported here.")),

    Domain.FOREIGN_RESIDENCE: DomainSpec(
        domain=Domain.FOREIGN_RESIDENCE, label="Foreign residence",
        mappings=(
            _house(Domain.FOREIGN_RESIDENCE, 12, "deśāntara",
                   "BPHS 23.11: with the twelfth lord joined by malefics, "
                   "the twelfth occupied by malefics and aspected by a "
                   "malefic, one goes from country to country (deśād "
                   "deśāntaraṃ gataḥ).", refs=(VYAYA_CH23,)),
            _lord(Domain.FOREIGN_RESIDENCE, 12,
                  "BPHS 23.11: the condition stated is of the twelfth LORD "
                  "as much as of the house.",
                  refs=(VYAYA_CH23, BHAVA_LORD)),
            _house(Domain.FOREIGN_RESIDENCE, 10, "pravāsa",
                   "BPHS 11.11: from the tenth are examined sovereignty, "
                   "livelihood, honour, the father, RESIDENCE ABROAD "
                   "(pravāsa) and debt.", primary=False),
            _house(Domain.FOREIGN_RESIDENCE, 9, "tīrthayātrā",
                   "BPHS 11.10: pilgrimage from the ninth.", primary=False),
            _karaka(Domain.FOREIGN_RESIDENCE, "Shani", "",
                    "Distance and separation. Not located for this.",
                    needs_human_review=True),
            _karaka(Domain.FOREIGN_RESIDENCE, "Rahu", "",
                    "The foreign and unfamiliar. Not located; the nodes "
                    "appear in no kāraka scheme this engine has read.",
                    needs_human_review=True),
        ),
        challenging_houses=(4,),
        notes=(
            "V1.5 mapped this to the 12th from convention. BPHS 23.11 turns "
            "out to support it in so many words, and BPHS 11.11 adds the "
            "10th via pravāsa — so the mapping was right and the engine had "
            "not known why.")),

    Domain.SPIRITUALITY: DomainSpec(
        domain=Domain.SPIRITUALITY, label="Dharma and spiritual life",
        mappings=(
            _house(Domain.SPIRITUALITY, 9, "dharma",
                   "BPHS 11.10: from the ninth are examined FORTUNE "
                   "(bhāgya), the brother-in-law, DHARMA, and PILGRIMAGE."),
            _lord(Domain.SPIRITUALITY, 9,
                  "BPHS 24.9: the Lagna lord in the ninth gives one "
                  "fortunate, devoted to Viṣṇu, eloquent.",
                  refs=(BHAVESHA_CH24, BHAVA_LORD)),
            _house(Domain.SPIRITUALITY, 12, "mokṣa",
                   "BPHS 23.10: with a benefic in the twelfth, its lord "
                   "exalted and benefics joining and aspecting, there is "
                   "MOKṢA without doubt.", primary=False, refs=(VYAYA_CH23,)),
            _house(Domain.SPIRITUALITY, 5, "yantra-mantra",
                   "BPHS 11.6: YANTRA AND MANTRA from the fifth.",
                   primary=False),
            _karaka(Domain.SPIRITUALITY, "Guru", "",
                    "Dharma and the teacher. Not in a located kāraka "
                    "scheme for this.", needs_human_review=True),
            _varga_attested(
                Domain.SPIRITUALITY, "D20", "upāsanā",
                "BPHS 7.4: upāsanāyā vijñānaṃ sādhyaṃ viṃśatibhāgake — "
                "knowledge of worship is to be obtained from the "
                "twentieth part.",
                is_primary=False),
        ),
        challenging_houses=(6,),
        notes=(
            "Four houses attested, including the fifth for yantra and "
            "mantra, which V1.5 did not have.")),

    Domain.BUSINESS: DomainSpec(
        domain=Domain.BUSINESS, label="Business and enterprise",
        mappings=(
            _house(Domain.BUSINESS, 7, "vāṇijya",
                   "BPHS 11.8: from the seventh are examined the wife, road "
                   "travel, TRADE (vāṇijya), and recovery of what is lost."),
            _lord(Domain.BUSINESS, 7,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _house(Domain.BUSINESS, 10, "vṛtti",
                   "BPHS 11.11: livelihood from the tenth; BPHS 21.4 links "
                   "the tenth lord with benefics to gain in TRADE "
                   "(vāṇijye).", primary=False, refs=(BHAVAVIVEKA,
                                                      KARMA_CH21)),
            _house(Domain.BUSINESS, 11, "āya",
                   "BPHS 11.12: income from the eleventh.", primary=False),
            _karaka(Domain.BUSINESS, "Budha", "",
                    "Trade. Not in a located kāraka scheme.",
                    needs_human_review=True),
            # BPHS 7.3 gives D10 mahat-phala. Nothing in the passage
            # connects a division to trade; 21.4 connects the tenth LORD
            # to gain in trade, which is a house-lord claim, not a varga.
            _varga(Domain.BUSINESS, "D10"),
        ),
        challenging_houses=(6, 8, 12),
        relevant_yoga_categories=("dhana",),
        notes=(
            "`vāṇijya` appears twice — at the seventh house in BPHS 11.8 "
            "and at the tenth lord in BPHS 21.4 — which is why both are "
            "mapped.")),

    Domain.LITIGATION: DomainSpec(
        domain=Domain.LITIGATION, label="Disputes and litigation",
        mappings=(
            _house(Domain.LITIGATION, 6, "śatru",
                   "BPHS 11.7: from the sixth are examined the maternal "
                   "uncle, fear of death, ENEMIES (śatrūn) and wounds."),
            _lord(Domain.LITIGATION, 6,
                  "BPHS 11.14-16: the bhāva lord's condition bears on the "
                  "bhāva's results.", refs=(BHAVA_LORD,)),
            _house(Domain.LITIGATION, 8, "raṇa, ripu",
                   "BPHS 11.9: from the eighth, BATTLE (raṇa) and ENEMIES "
                   "(ripu).", primary=False),
            _house(Domain.LITIGATION, 12, "vairi-vṛttānta",
                   "BPHS 11.13: from the twelfth, expenditure and NEWS OF "
                   "ENEMIES (vairi-vṛttānta).", primary=False),
            _karaka(Domain.LITIGATION, "Mangal", "",
                    "Conflict. Not in a located kāraka scheme for this.",
                    needs_human_review=True),
        ),
        challenging_houses=(1,),
        relevant_yoga_categories=("vipareeta_raja",),
        notes=(
            "Three houses attested for enemies and disputes. Note this "
            "domain is about conflict as the texts describe it, not about "
            "courts, which no verse mentions.")),
}


def spec_for(domain) -> DomainSpec:
    """The mapping for a Domain or its name."""
    if isinstance(domain, str):
        try:
            domain = Domain(domain.upper())
        except ValueError as exc:
            raise ValueError(
                f"Unknown domain '{domain}'. Available: "
                + ", ".join(d.value for d in Domain)) from exc
    return DOMAINS[domain]


def domains_for_house(house: int) -> list[Domain]:
    """Every domain the given bhava bears on, primary or secondary."""
    house = ((house - 1) % 12) + 1
    return [spec.domain for spec in DOMAINS.values()
            if house in spec.all_houses]


def strict_domains() -> list[str]:
    """
    Domains with at least one source-qualified factor→domain link.

    The V1.6 replacement for `strict_admissible_domains`, which could only
    ever answer "the ones with a located kāraka" because no house mapping
    had a witness.
    """
    return sorted(spec.domain.value for spec in DOMAINS.values()
                  if spec.strict_eligible)


def all_mappings() -> list[DomainMappingEvidence]:
    return [m for spec in DOMAINS.values() for m in spec.mappings]


def domain_mapping_summary() -> dict:
    """Part 8: the standing of the mappings, as data rather than prose."""
    mappings = all_mappings()
    houses = [m for m in mappings if m.factor_type is FactorType.HOUSE]
    karakas = [m for m in mappings if m.factor_type is FactorType.KARAKA]
    return {
        "domains": len(DOMAINS),
        "methodology_profile": "parashari_textual_v16",
        "reference_space": ReferenceSpace.RASHI.value,
        "mappings_total": len(mappings),
        "mappings_located": sum(1 for m in mappings if m.is_located),
        "mappings_source_qualified": sum(
            1 for m in mappings if m.is_source_qualified),
        "house_mappings_total": len(houses),
        "house_mappings_located": sum(1 for m in houses if m.is_located),
        "house_mappings_validated": sum(
            1 for m in houses if m.is_source_qualified),
        "karakas_total": len(karakas),
        "karakas_with_located_witness": sum(
            1 for m in karakas if m.is_located),
        "domains_strict_eligible": strict_domains(),
        "coverage_by_factor_type": coverage(mappings),
        "high_stakes_domains": [d.value for d in HIGH_STAKES_DOMAINS],
        "note": (
            "Every varga assignment is UNVERIFIED: no witness this engine "
            "holds assigns a divisional chart to a life area."),
    }
