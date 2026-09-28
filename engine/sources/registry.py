"""
Source registry (V1.3 Parts 2, 6, 8, 10, 11, 17)
-------------------------------------------------
The audit itself: what evidence exists for each shipped rule and each Varga
convention.

THE V1.5 HEADLINE, STATED PLAINLY

    Sanskrit witnesses now exist for Bṛhat Parāśara Horā Śāstra, Phaladīpikā
    and Jātaka Pārijāta, alongside the Bṛhajjātaka obtained in V1.3. The
    ~110-rule corpus has been audited against them chapter by chapter.

    THE CENTRAL FINDING IS ABOUT CITATIONS, NOT DOCTRINE. Most of the rules
    describe combinations that really are in the texts. Almost none of them
    cited the right place. The engine's Raja Yogas said "BPHS ch.36"; the
    generic kendra-trikona rule is at 34.11-13 and 41.28, and ch.36 is the
    vividha-yoga chapter. The Dhana Yogas said "ch.40"; ch.40 is the
    rāja-sambandha chapter and the dhana chapter is 41, which does not
    contain the rule the engine implements. The Moon yogas said "ch.34";
    they are at 37.7. Of the legacy citations checked, ONE named the correct
    chapter: ch.75 for the Pañca Mahāpuruṣa yogas.

    SEVEN GROUPS DIVERGE FROM THE TEXT THAT WAS FOUND. Those are marked
    IMPLEMENTATION_DIVERGES, which is a statement about the code and not
    about the evidence. Corrected readings are implemented as separate rules
    in the `parashari_textual` profile rather than edited into the existing
    ones, so both readings remain available and nothing changed silently.

    Nothing in this engine is TRADITION_VALIDATED. Two rules now reach
    VALIDATED_FOR_PROFILE, which is the highest status the engine can reach
    without a human closing the outstanding questions.

WHY UNVERIFIED RULES ARE NOT DELETED

    A rule being untraced is not the same as a rule being wrong. The Pañca
    Mahāpuruṣa yogas are taught everywhere and are almost certainly attested
    somewhere; this engine simply has not seen that text. Deleting them would
    trade a known unknown for a silent gap. They are kept, classified, and
    excluded from the strict profile.

WHAT WAS DELIBERATELY NOT DONE

    No citation was invented to fill a gap, and no Sanskrit ambiguity was
    resolved by choosing the reading that happens to match the code. Where the
    text is unclear the question is queued for a human instead — see
    REVIEW_QUEUE below.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional

from .editions import (
    ALL_WITNESSES, BJ_1_6_NAVAMSHA, BJ_1_7_TRIMSHAMSHA, BJ_12_NABHASA,
    BJ_13_2_ADHIYOGA, BJ_13_3_CANDRA_YOGAS, BPHS_27_SHADBALA,
    BPHS_66_ASHTAKAVARGA, BPHS_SA_34_YOGAKARAKA, BPHS_SA_36_3_GAJAKESARI,
    BPHS_SA_36_5_AMALA, BPHS_SA_36_27_LAKSHMI, BPHS_SA_36_37_LAGNADHIYOGA,
    BPHS_SA_37_5_ADHIYOGA, BPHS_SA_37_7_CANDRA_YOGAS,
    BPHS_SA_37_11_KEMADRUMA, BPHS_SA_38_1_RAVI_YOGAS, BPHS_SA_39_19_VIPAREETA,
    BPHS_SA_41_28_RAJAYOGA, BPHS_SA_75_1_MAHAPURUSHA, BPHS_SANSKRIT_SD,
    BRIHAJJATAKA_GRETIL, JATAKA_PARIJATA_SD, JP_59_MAHAPURUSHA,
    JP_83_CANDRA_YOGAS, JP_114_LAGNADHIYOGA, JP_116_GAJAKESARI,
    PD_6_21_LAKSHMI, PD_6_26_SARASVATI, PD_6_57_VIPAREETA,
    PD_20_GOCHARA_FROM_LAGNA, PD_26_GOCHARA, PD_26_VEDHA_TABLE,
    PD_EN_20_SASTRI, PD_EN_26_SASTRI, PHALADEEPIKA_SD,
    QUOTATION_WITNESSES, RESOLVED_UNAVAILABLE_WORKS, UNAVAILABLE_WORKS,
    witness_by_id,
)
from .models import (
    ReviewItem, ReviewReason, RuleClassification, RuleEvidence, SourceConflict,
    SourceWitness, ValidationStatus, today,
)

# 1.7.0 (V1.8): ADDED four gochara witnesses — the chapter-26 vedha table,
# the 1950 printed edition, and its renderings of chapters 26 and 20 — plus
# two calculation evidence records for the implemented gochara rules and one
# conflict recording a corrupt reading in the digital witness. Additive; no
# existing record changed meaning.
#
# 1.6.0 (V1.7): ADDED four witnesses — the BPHS varga-signification
# passage in Sanskrit and in translation, and the two Phaladīpikā gochara
# passages. Nothing was removed and no existing record changed meaning, so
# a minor bump. V1.6 added witnesses without bumping this, which was an
# oversight: a consumer comparing two charts had no way to see that the
# registry behind them differed.
REGISTRY_VERSION = "1.7.0"
REVIEWED_ON = "2026-09-28"

#: The release doing the auditing NOW. Reported in the summary so a reader
#: knows which release produced the current numbers.
#:
#: NOT stamped on any record. V1.7 learned why — see AUDITED_V15 below — and
#: then stamped its own new records with it anyway, which would have made
#: V1.8 claim to have audited V1.7's gochara work. Every `audited_in` now
#: takes a frozen per-release constant.
AUDIT_RELEASE = "V1.8"

#: The release that located and implemented the gochara rules.
AUDITED_V18 = "V1.8"

#: The release that audited the V1.5 rule corpus.
#:
#: V1.5 stamped those 33 records with `AUDIT_RELEASE`, a constant that
#: moves with each release — so the first release to bump it retroactively
#: claimed to have re-audited work it had not touched. `audited_in` records
#: WHEN a record was examined, which does not change because the calendar
#: did. Each release's value is written out and frozen.
AUDITED_V15 = "V1.5"

# ── Part 11 and 7: conflicts ─────────────────────────────────────────────────

CONFLICTS: tuple[SourceConflict, ...] = (
    # V1.8. Not a doctrinal conflict — a TRANSMISSION one, and the first of
    # its kind in this registry. Two witnesses to the same work disagree
    # about two words, and the disagreement is resolvable rather than live,
    # which is why it is recorded as RESOLVED and why the resolution names
    # the evidence rather than the authority.
    SourceConflict(
        id="GOCHARA_MERCURY_VEDHA_READING",
        topic="Mercury's sixth vedha house, and Venus's eighth",
        witness_a="PD_SA_26.2-8_GOCHARA_VEDHA",
        witness_b="PD_EN_26.1-8_SASTRI",
        difference=(
            "Phaladīpikā 26.6 pairs Mercury's six favourable houses with six "
            "vedha houses positionally. The ITRANS witness ends the list "
            "with `prApti`, the 11th; the 1950 printed edition gives the "
            "12th. 26.8 has a smaller divergence: the ITRANS text reads "
            "`vari`, water and so the 4th, where the printed edition and "
            "the pairing require `ari`, enemy, the 6th."),
        software_profiles_affected=("phaladipika_gochara",),
        resolution_status="RESOLVED_AGAINST_DIGITAL_WITNESS",
        resolution_note=(
            "The Mercury reading is settled WITHOUT appeal to either "
            "witness's authority, because the corrupt reading is "
            "self-refuting: pairing the 11th with the 11th would assert "
            "that Mercury's transit of the 11th is obstructed by a graha "
            "standing where Mercury already stands. The printed edition "
            "then supplies the 12th, which is consistent. "
            "The Venus reading is settled the ordinary way — the printed "
            "edition against a volunteer transliteration — and is the "
            "weaker of the two resolutions. "
            "Note what this does NOT establish. Both witnesses are "
            "Phaladīpikā, so this is the same work speaking twice and is "
            "recorded as SAME_WORK_SECOND_EDITION, not as independent "
            "corroboration of the doctrine."),
    ),
    SourceConflict(
        id="KEMADRUMA_BHANGA_EXTENT",
        topic="Which conditions cancel Kemadruma",
        witness_a="BJ_13.3_CANDRA_YOGAS",
        witness_b="BJ_13.3_CANDRA_YOGAS (second half, reported opinion)",
        difference=(
            "Bṛhajjātaka 13.3 states that Kemadruma is not accepted when the "
            "Moon is in a kendra or conjoined with a graha, and then reports "
            "a further opinion involving kendras and navāṃśas which it "
            "appears to set aside as not well established. The engine "
            "implements four cancellation clauses, which is wider than the "
            "first reading and overlaps the second. The verse itself is thus "
            "a witness to a disagreement that was already live."),
        software_profiles_affected=("parashari", "parashari_extended",
                                    "parashari_strict"),
        resolution_status="RESOLVED_AGAINST_IMPLEMENTATION",
        resolution_note=(
            "V1.5 settles the part that was actually open. The V1.3 note "
            "asked what Bṛhajjātaka 13.3's second half concedes and what it "
            "rejects. Jātaka Pārijāta 83 quotes the verse in full, under the "
            "heading horāyām, and preserves the closing judgement: "
            "ukti-prasiddhā na te — 'those are not well established'. The "
            "kendra/navāṃśa opinion is therefore REPORTED AND REJECTED by the "
            "witness, not endorsed. Independently, BPHS 37.11 gives its own "
            "two conditions and explicitly excludes the Moon itself from "
            "counting (vinā candraṃ). The engine's four cancellation clauses "
            "are wider than either witness, and one of them — the Moon in a "
            "kendra from the Lagna — is contradicted outright. Behaviour is "
            "unchanged; `kemadruma_textual` implements the located reading."),
    ),
    SourceConflict(
        id="SUNAPHA_NODE_EXCLUSION",
        topic="Whether Rahu and Ketu count as company for the Moon yogas",
        witness_a="BJ_13.3_CANDRA_YOGAS and BPHS_SA_37.7_CANDRA_YOGAS",
        witness_b="Engine implementation (V1.1-V1.4), source unrecorded",
        difference=(
            "Bṛhajjātaka 13.3 excludes only the Sun (hitvā arkaṃ). Bṛhat "
            "Parāśara Horā Śāstra 37.7 excludes only the Sun (sūryaṃ binā). "
            "Two independent works, two different phrasings, the same single "
            "exclusion. The engine additionally excludes Rahu and Ketu."),
        software_profiles_affected=("parashari", "parashari_extended"),
        resolution_status="RESOLVED_AGAINST_IMPLEMENTATION",
        resolution_note=(
            "V1.5 reclassifies this. It was registered in V1.3 as a conflict "
            "between a witness and the engine, on one witness and no "
            "counter-witness. A second independent Sanskrit witness has now "
            "been read and agrees with the first, and no witness anywhere "
            "supports excluding the nodes. That makes this not a disagreement "
            "among sources but a DEFECT IN THE CODE, and the affected rules "
            "are marked IMPLEMENTATION_DIVERGES accordingly. The legacy rules "
            "keep their behaviour so that no V1.4 result changes without "
            "notice; `sunapha_textual`, `anapha_textual` and "
            "`durudhara_textual` implement the located reading."),
    ),
    SourceConflict(
        id="LAKSHMI_YOGA_DEFINITION",
        topic="What Lakṣmī Yoga requires",
        witness_a="BPHS_SA_36.27_LAKSHMI",
        witness_b="PD_6.21_LAKSHMI",
        difference=(
            "BPHS 36.27: the 9th lord in a kendra, in moolatrikona, or in "
            "own sign or exaltation, together with a STRONG LAGNA LORD. "
            "Phaladīpikā 6.21: the 9th lord AND VENUS, both in own sign or "
            "exaltation, both in a kendra or trikoṇa. These are not variant "
            "phrasings of one rule. They require different planets and would "
            "fire on different charts."),
        software_profiles_affected=("parashari_extended", "parashari_textual"),
        resolution_status="MODELLED_AS_TWO_RULES",
        resolution_note=(
            "Not resolved, and deliberately not resolvable by preference. "
            "Both are live readings in named witnesses, so V1.5 ships both: "
            "`lakshmi_yoga_bphs` and `lakshmi_yoga_phaladeepika`. The V1.1 "
            "rule `lakshmi_yoga` matched neither and is retained, marked, and "
            "excluded from strict synthesis."),
    ),
    SourceConflict(
        id="MAHAPURUSHA_STRENGTH_REQUIREMENT",
        topic="Whether a Mahāpuruṣa graha must additionally be strong",
        witness_a="BPHS_SA_75.1_MAHAPURUSHA",
        witness_b="JP_59_MAHAPURUSHA",
        difference=(
            "The two witnesses AGREE with each other and disagree with the "
            "engine. BPHS 75.1 requires the graha to be balibhiḥ; Jātaka "
            "Pārijāta 59 requires baliṣṭhāḥ. Both mean strong, and both are "
            "stated as a condition of formation alongside the dignity and "
            "the kendra. The engine requires dignity and kendra only. They "
            "differ from each other on the dignity SET: BPHS gives own sign "
            "and exaltation, Jātaka Pārijāta adds moolatrikona — so the "
            "engine's inclusion of moolatrikona is attested, by one of them."),
        software_profiles_affected=("parashari", "parashari_textual"),
        resolution_status="PARTIALLY_RESOLVED",
        resolution_note=(
            "The strength requirement is not in dispute between the witnesses "
            "and V1.5 implements it, in `mahapurusha_*_textual`, using "
            "Shadbala — which exists only because V1.4 built it, and which "
            "gives the engine a defensible reading of balibhiḥ for the first "
            "time. The dignity set remains genuinely divergent between the "
            "two works and is left as it is, following the wider reading and "
            "saying so."),
    ),
    SourceConflict(
        id="GAJAKESARI_REFERENCE_FRAME",
        topic="Whether Gajakesari is counted from the Lagna or only the Moon",
        witness_a="BPHS_SA_36.3_GAJAKESARI",
        witness_b="JP_116_GAJAKESARI",
        difference=(
            "BPHS 36.3 allows a kendra from the Lagna OR from the Moon "
            "(lagnāc candrād vā). Jātaka Pārijāta 116 gives only from the "
            "Moon (mṛgāṅkāt). Both additionally require Jupiter to be free of "
            "debilitation and combustion, and BPHS also of enemy signs; both "
            "requirements are absent from the engine's rule."),
        software_profiles_affected=("parashari", "parashari_textual"),
        resolution_status="MODELLED_AS_TWO_RULES",
        resolution_note=(
            "The reference frame is a real disagreement and is modelled as "
            "two rules. The freedom-from-affliction requirement is NOT in "
            "disagreement — both witnesses state it — so it is implemented in "
            "both textual variants."),
    ),
    SourceConflict(
        id="PUTRAKARAKA_ATTRIBUTION",
        topic="Which graha is the natural significator of children",
        witness_a="BPHS_SA_32.18-21_STHIRA_KARAKA",
        witness_b="Standard modern practice, no witness located",
        difference=(
            "BPHS 32.20 reads `guroḥ pitāmahaḥ śukrāt patiḥ putraḥ "
            "śanaiścarāt` — from Jupiter the paternal grandfather, from "
            "Venus the spouse, from Saturn the SON. Modern practice makes "
            "Jupiter the putrakāraka near-universally. This witness gives "
            "Jupiter a different relative entirely and assigns the son to "
            "Saturn."),
        software_profiles_affected=("parashari_bhava_mapping_v15",),
        resolution_status="UNRESOLVED",
        resolution_note=(
            "The CHILDREN domain carries both attributions, Saturn with the "
            "BPHS locator and Jupiter marked as an unlocated modern "
            "convention, and neither is dropped. Two cautions before anyone "
            "treats this as BPHS overturning modern practice. First, the "
            "sthira kārakas of 32.18-21 are a list of relatives for a "
            "specific purpose, and may not be intended as the general "
            "significators the modern list is used as. Second, the exemplar "
            "behind this transliteration is not identified, and a "
            "single-word variant is exactly the kind of thing that differs "
            "between editions. A Sanskritist with two printed editions "
            "settles this in an afternoon; this engine should not settle it "
            "at all."),
    ),
    SourceConflict(
        id="MAHAPURUSHA_DIGNITY_SET",
        topic="Which dignities qualify a graha for a Mahāpuruṣa yoga",
        witness_a="BPHS_SA_75.1_MAHAPURUSHA",
        witness_b="JP_59_MAHAPURUSHA",
        difference=(
            "BPHS 75.1 gives sva-bha and ucca — own sign and exaltation. "
            "Jātaka Pārijāta 59 gives mūlatrikoṇa, nija and tuṅga — "
            "moolatrikona, own sign and exaltation. Moolatrikona is in one "
            "and not the other, and it is not a rare case: it covers a "
            "specific arc of a graha's own sign that many charts land in."),
        software_profiles_affected=("parashari", "parashari_textual"),
        resolution_status="UNRESOLVED",
        resolution_note=(
            "Both readings ship in the same rule, following the wider set, "
            "which is a compromise and is named as one. The consequence is "
            "deliberate: `mahapurusha_*_textual` carries this conflict and is "
            "therefore NOT admitted to the evidence-gated strict profile. A "
            "rule whose formation condition two witnesses state differently "
            "does not belong in a profile that claims settled provenance, "
            "however well-sourced the rest of it is."),
    ),
    SourceConflict(
        id="OJHAYUGMA_VIRUPA_VALUE",
        topic="Whether Ojhayugma Bala is 15 or 35 virupas per placement",
        witness_a="BPHS_27_SHADBALA (verse 4.5)",
        witness_b="BPHS_27_SHADBALA (Santhanam's note beneath it)",
        difference=(
            "The verse says 'a quarter of Rupa (i.e. 15 Virupas)'. The "
            "translator's note immediately below says 35 Virupas. Fifteen is "
            "a quarter of sixty and thirty-five is not, so the note is an "
            "OCR or typesetting error and the engine follows the verse."),
        software_profiles_affected=("bphs_santhanam_ch27",),
        resolution_status="RESOLVED_BY_ARITHMETIC",
        resolution_note=(
            "Resolved on internal evidence rather than by preference: a "
            "quarter of a rupa is 15 by definition. A second witness would "
            "still be worth having."),
    ),
    SourceConflict(
        id="AHARGANA_EPOCH_UNFIXED",
        topic="The epoch for Varsha and Masa Bala",
        witness_a="BPHS_27_SHADBALA (verse 13)",
        witness_b="None — the edition's printed speculum",
        difference=(
            "Varsha and Masa Bala need an Ahargana, a day count from an "
            "epoch of creation. The witness describes the method but fixes "
            "the epoch only through a 'Speculum of Abbreviated Aharganas' "
            "belonging to that printing, not to the text. Another edition's "
            "speculum would give different year and month lords."),
        software_profiles_affected=("bphs_santhanam_ch27/ahargana_kali_epoch",),
        resolution_status="UNRESOLVED",
        resolution_note=(
            "The engine uses a stated Kali Yuga epoch so the arithmetic is "
            "reproducible, and flags both components as approximations. It "
            "does not claim they match any particular edition."),
    ),
    SourceConflict(
        id="BPHS_EDITION_UNIDENTIFIED",
        topic="Which BPHS the engine's ~100 yoga citations refer to",
        witness_a="BPHS_SANTHANAM_V1 / V2 (obtained in V1.4)",
        witness_b="The edition those citations were written against — unknown",
        difference=(
            "BPHS is a textual tradition, not one document: chapter division, "
            "verse numbering, Sanskrit readings and translations all differ "
            "between editions. The engine's citations name no edition, so "
            "they do not identify a passage even in principle."),
        software_profiles_affected=("parashari", "parashari_extended",
                                    "parashari_strict"),
        resolution_status="RESOLVED_BY_AUDIT",
        resolution_note=(
            "V1.5 completed the chapter-by-chapter audit this entry was "
            "waiting for, against a Sanskrit witness rather than the "
            "translation. The answer is that the citations referred to no "
            "edition, because they were not derived from one: with a single "
            "exception (ch.75) every chapter number checked was wrong, and "
            "wrong in a way no edition variance explains — ch.36 for a rule "
            "at 34.11, ch.40 for a rule at 41.28, ch.34 for a rule at 37.7. "
            "They were written from memory and are now replaced by locators "
            "into a named, checksummed witness. What REMAINS open is which "
            "printed exemplar that witness transliterates; see the review "
            "queue."),
    ),
    SourceConflict(
        id="DHANA_YOGA_NOT_LOCATED",
        topic="Whether BPHS states the engine's generic Dhana Yoga rule",
        witness_a="BPHS_SANSKRIT_SD ch.41, read in full",
        witness_b="Engine implementation (V1.1-V1.4), source unrecorded",
        difference=(
            "The engine generates 30 Dhana Yogas from relationships among the "
            "lords of the 1st, 2nd, 5th, 9th and 11th, citing 'BPHS ch.40'. "
            "Chapter 40 is rāja-sambandha-yoga and contains nothing of the "
            "kind. Chapter 41, viśeṣa-dhana-yoga, IS the wealth chapter, and "
            "what it contains at 41.2-15 is a different rule set entirely: "
            "specific grahas in specific houses in their own signs, house by "
            "house. The one point of contact is 41.16, which names the lords "
            "of the 9th and 5th as wealth-givers."),
        software_profiles_affected=("parashari", "parashari_extended"),
        resolution_status="UNRESOLVED_ABSENCE",
        resolution_note=(
            "This is a negative result and is recorded as one. The wealth "
            "chapter was read and the rule is not in it. That does not make "
            "the rule wrong — it is standard in modern Parāśarī practice and "
            "may well be in Sārāvalī or Phaladīpikā, neither of which has "
            "been searched for it — but the engine can no longer claim BPHS "
            "for it. The 30 rules stay, reclassified from UNVERIFIED to "
            "TRADITIONAL_MODERN_CONVENTION, which is a more accurate "
            "description of what they are."),
    ),
)


def conflict_by_id(conflict_id: str) -> SourceConflict:
    for conflict in CONFLICTS:
        if conflict.id == conflict_id:
            return conflict
    raise KeyError(f"No registered conflict with id '{conflict_id}'")


# ── Part 17: the human review queue ──────────────────────────────────────────

REVIEW_QUEUE: tuple[ReviewItem, ...] = (
    # ── V1.8 gochara ────────────────────────────────────────────────────
    ReviewItem(
        subject="gochara/vedha_from_moon — nodes as obstructors",
        reason=ReviewReason.UNCLEAR_EXCEPTION,
        question=(
            "Phaladīpikā 26.3-8 name the obstructing bodies `khecharaiḥ` "
            "and `grahaiḥ` without enumerating them. Do Rāhu and Ketu cause "
            "vedha? 26.2 treats the nodes as transiting grahas with results "
            "of their own, which argues that they do — but does either "
            "witness or a commentary settle it?"),
        current_behaviour=(
            "The nodes DO cause vedha. The decision is a named, defaulted "
            "parameter on evaluate_vedha rather than a membership test, and "
            "every run records which way it was set."),
        raised_on="2026-09-28",
    ),
    ReviewItem(
        subject="gochara/vedha_from_moon — node vedha table",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "26.2 gives Rāhu and Ketu the Sun's favourable houses "
            "(`tigmāṃśuvad bhoginau`). Neither witness gives them a vedha "
            "table, and neither says whether the Sun's exemption from "
            "Saturn's vedha travels with the houses. Does a commentary or "
            "another work supply the missing half?"),
        current_behaviour=(
            "The nodes carry the Sun's four favourable houses and an EMPTY "
            "vedha table. The Sun's row is deliberately not copied across, "
            "and the missing layer bars the node rules from strict "
            "synthesis."),
        raised_on="2026-09-28",
    ),
    ReviewItem(
        subject="gochara/dasha_lord_from_lagna — `balānvita`",
        reason=ReviewReason.UNCLEAR_EXCEPTION,
        question=(
            "Phaladīpikā 20.34 conditions the result on the daśā lord being "
            "`balānvita`, endowed with strength at birth, and names no "
            "measure. Is BPHS 27's required-virūpa threshold an acceptable "
            "reading of Mantreśvara's word, or does Phaladīpikā have its "
            "own strength standard elsewhere in the text?"),
        current_behaviour=(
            "Shadbala ratio >= 1.0 against BPHS 27's requirement table. The "
            "textual qualification and the software interpretation are "
            "stored as separate fields on NatalStrengthCondition so the "
            "substitution is visible wherever the evidence is read."),
        raised_on="2026-09-28",
    ),
    ReviewItem(
        subject="Varga:D30/parashari",
        reason=ReviewReason.NUMERIC_ENCODING_UNRESOLVED,
        question=(
            "Bṛhajjātaka 1.7 gives the triṃśāṃśa lord order clearly, but the "
            "degree spans of the five portions are not transparently readable "
            "in the verse — they appear to be encoded in word-numerals "
            "(pavana, samīraṇa …). Does this verse state the 5/5/8/7/5 "
            "division the engine implements?"),
        current_behaviour=(
            "Engine uses 5/5/8/7/5 degrees for odd rashis and the reversed "
            "order with 5/7/8/5/5 for even ones."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="yoga:sunapha / anapha / durudhara / kemadruma",
        reason=ReviewReason.SANSKRIT_AMBIGUITY,
        question=(
            "In BJ 13.3 'sva.antya.ubhaya.sthaiḥ grahaiḥ', the engine reads "
            "sva as the 2nd house from the Moon, antya as the 12th and "
            "ubhaya as both. The term 'sva' has other possible referents. "
            "Does a commentary confirm the 2nd-house reading?"),
        current_behaviour=(
            "2nd from the Moon gives Sunaphā, 12th gives Anaphā, both give "
            "Durudhurā, neither gives Kemadruma."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="yoga:kemadruma + bhanga clauses",
        reason=ReviewReason.UNCLEAR_EXCEPTION,
        question=(
            "BJ 13.3's second half appears to give two cancellations (Moon "
            "angular; Moon conjoined) and then report and possibly reject a "
            "further opinion. The engine implements four clauses. Which are "
            "attested, and by which witness?"),
        current_behaviour=(
            "Four cancellation clauses: graha in a kendra from the Lagna; "
            "graha in a kendra from the Moon; Moon itself in a kendra from "
            "the Lagna; Moon receiving benefic drishti."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="yoga:sunapha / anapha / durudhara / kemadruma",
        reason=ReviewReason.UNCLEAR_EXCEPTION,
        question=(
            "BJ 13.3 excludes only the Sun. On whose authority do Rahu and "
            "Ketu also not count as company?"),
        current_behaviour="Sun, Rahu and Ketu are all excluded.",
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="yoga:mahapurusha_* (all five)",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "The Pañca Mahāpuruṣa yogas are NOT in Bṛhajjātaka. They are "
            "commonly attributed to Sārāvalī and to Phaladīpikā. Which text, "
            "which edition, which verses?"),
        current_behaviour=(
            "Implemented as own-sign/exaltation/moolatrikona in a kendra from "
            "the Lagna, cancelled by combustion."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="yoga:vesi / vasi / ubhayachari",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "The Sun-relative counterparts of the Moon yogas are not present "
            "in Bṛhajjātaka under these names, although the Moon set is. "
            "Where are they first attested?"),
        current_behaviour=(
            "Implemented as the Moon set but from the Sun, excluding the Moon "
            "and the nodes."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="yoga:raja_yoga_* and dhana_yoga_* (63 generated rules)",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "These are generated combinatorially from the principle that a "
            "kendra lord related to a trikona lord yields Raja Yoga, and that "
            "lords of 1/2/5/9/11 related yield Dhana Yoga. Does any text "
            "enumerate them this way, or is the enumeration the engine's?"),
        current_behaviour=(
            "33 Raja and 31 Dhana rules generated from house pairs times "
            "three relationship modes."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="Varga:D2/parashari",
        reason=ReviewReason.SANSKRIT_AMBIGUITY,
        question=(
            "The engine returns a rashi (Simha or Karka). Sources are read "
            "both ways and the difference propagates into every downstream "
            "feature. Does the horā rule yield a RASHI or a LORD?"),
        current_behaviour="Returns Simha or Karka as a rashi.",
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="Varga:D10/parashari",
        reason=ReviewReason.TRANSLATION_DISAGREEMENT,
        question=(
            "Both readings circulate. For even rashis, does the daśāṃśa "
            "count from the 9th from the sign, as the engine has it, or from "
            "the 8th?"),
        current_behaviour="Odd from the sign itself, even from the 9th.",
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="Varga:D16 / D20 / D24 / D27 / D40 / D45 / D60",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "No witness has been located for the starting-sign conventions of "
            "these seven charts. Which text states each, and does it agree "
            "with the engine?"),
        current_behaviour=(
            "Starting signs by movability, parity or element as documented in "
            "engine/varga_metadata.py."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="calculation:ashtakavarga/bhinna (six tables)",
        reason=ReviewReason.MANUSCRIPT_DISAGREEMENT,
        question=(
            "The Sun's bindu table was read from BPHS 66.43-45 and matches. "
            "The tables for the Moon, Mars, Mercury, Jupiter, Venus and "
            "Saturn are in the same chapter but their OCR is damaged. Do "
            "they match the standard tables the engine implements?"),
        current_behaviour=(
            "Standard tables, whose totals (48/49/39/54/56/52/39) all match "
            "the classical figures — an independent arithmetic check."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="calculation:shadbala/kala_bala (varsha and masa)",
        reason=ReviewReason.NUMERIC_ENCODING_UNRESOLVED,
        question=(
            "Varsha and Masa Bala need an Ahargana epoch that the witness "
            "supplies through a printed speculum rather than through the "
            "text. Which epoch does that speculum imply?"),
        current_behaviour=(
            "A stated Kali Yuga epoch (JD 588465.5), with both components "
            "flagged as approximations."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="calculation:shadbala/kala_bala (tribhaga)",
        reason=ReviewReason.UNCLEAR_EXCEPTION,
        question=(
            "Tribhaga Bala divides the day and the night into thirds, which "
            "needs real sunrise and sunset. The engine does not yet compute "
            "them. Should the thirds be reckoned from true local sunrise?"),
        current_behaviour="Sunrise and sunset assumed at 06:00 and 18:00.",
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="calculation:shadbala/dig_bala",
        reason=ReviewReason.UNCLEAR_REFERENCE_FRAME,
        question=(
            "The witness says 'cusp', which under a quadrant system is a "
            "bhava madhya. This engine defaults to whole-sign houses, which "
            "have no distinct madhya. Should Dig Bala be measured from the "
            "angles, as implemented, or from bhava madhyas when a bhava "
            "chart exists?"),
        current_behaviour=(
            "Measured from the Ascendant and Midheaven; uses bhava madhyas "
            "when supplied, and says which in the profile."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="calculation:houses/sripati",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "No witness has been located for any house system. Which text "
            "states the Sripati construction, and does it place the Lagna "
            "degree at the bhava madhya or at the cusp?"),
        current_behaviour=(
            "Quadrant trisection with the Lagna degree as the 1st madhya."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="engine:BPHS yoga citations (~100)",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "Roughly a hundred rules cite BPHS chapters. Those strings were "
            "written from memory and have never been checked. Which are "
            "correct, and against which edition?"),
        current_behaviour=(
            "Citations retained on the rules but classified UNVERIFIED."),
        raised_on=REVIEWED_ON,
    ),

    # ── V1.5 ────────────────────────────────────────────────────────────────
    ReviewItem(
        subject="Witness:BPHS_SANSKRIT_SD",
        reason=ReviewReason.MANUSCRIPT_DISAGREEMENT,
        question=(
            "Which printed edition of Bṛhat Parāśara Horā Śāstra does the "
            "sanskritdocuments.org transliteration reproduce?"),
        current_behaviour=(
            "Registered as PRINTED_SANSKRIT_EDITION on the strength of being "
            "Sanskrit, with the exemplar recorded as unidentified. The whole "
            "V1.5 audit rests on this witness's chapter numbering, and BPHS "
            "chapter numbering is exactly the thing that varies between "
            "editions — so the audit's locators are only as stable as this "
            "question's answer."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="raja_yoga_* (all 36)",
        reason=ReviewReason.UNCLEAR_EXCEPTION,
        question=(
            "Does BPHS 34.15 negate a kendra-trikoṇa Rājayoga whenever either "
            "lord also owns a dusthana, or only when the dusthana lordship is "
            "that lord's dominant one?"),
        current_behaviour=(
            "The 36 generated rules implement no exception at all. "
            "`raja_yoga_*_textual` implements the strict reading — any "
            "dusthana ownership by either lord cancels — which is the wider "
            "of the two and may over-cancel. The answer changes results on "
            "most charts, since the 6th, 8th or 12th is owned by a kendra or "
            "trikoṇa lord in the majority of ascendants."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="mahapurusha_*_textual",
        reason=ReviewReason.UNCLEAR_REFERENCE_FRAME,
        question=(
            "What did balibhiḥ / baliṣṭhāḥ mean to these authors, and is "
            "Shadbala reaching its required minimum a faithful reading of it?"),
        current_behaviour=(
            "The textual variants require the graha's Shadbala total to reach "
            "the requirement stated in BPHS 27.32-33. That is a defensible "
            "choice and it is a CHOICE: the Mahāpuruṣa verses do not say "
            "which measure of strength they mean, and Shadbala is a different "
            "chapter of a different work from Jātaka Pārijāta 59. An engine "
            "convention is doing work here that a text has not authorised."),
        blocking=True,
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="vipareeta_harsha / vipareeta_sarala / vipareeta_vimala",
        reason=ReviewReason.COMMENTARY_REQUIRED,
        question=(
            "Phaladīpikā 6.57 makes the twelve bhāva-lord yogas fire when the "
            "lord is duḥstha OR afflicted by malefics — so is Harṣa present "
            "when the 6th lord is merely aspected by a malefic in a good "
            "house?"),
        current_behaviour=(
            "The engine requires the 6th, 8th or 12th lord to OCCUPY a "
            "dusthana, and ignores the affliction limb of the verse entirely. "
            "Reading the verse literally would fire these yogas far more "
            "often than any practitioner would accept, which is itself a "
            "reason to think a commentary is constraining it."),
        raised_on=REVIEWED_ON,
    ),
    ReviewItem(
        subject="dhana_yoga_* (all 30)",
        reason=ReviewReason.NO_WITNESS_AVAILABLE,
        question=(
            "Which text, if any, states the generic 1st/2nd/5th/9th/11th "
            "lord-relationship Dhana Yoga that the engine implements?"),
        current_behaviour=(
            "Reclassified in V1.5 from UNVERIFIED to "
            "TRADITIONAL_MODERN_CONVENTION after BPHS ch.41 was read in full "
            "and found to contain a different rule set. Sārāvalī is the "
            "obvious next place to look and has not been read."),
        raised_on=REVIEWED_ON,
    ),
)


# ── Part 6, 10: rule evidence ────────────────────────────────────────────────

def _evidence(subject, **kwargs) -> RuleEvidence:
    kwargs.setdefault("last_reviewed", REVIEWED_ON)
    return RuleEvidence(subject=subject, **kwargs)


_MOON_YOGA_DIVERGENCE = (
    "The engine excludes Rahu and Ketu from counting as company for the Moon. "
    "Neither witness excludes anything but the Sun. Two independent Sanskrit "
    "works were read and both say the same thing, so this is not a gap in the "
    "evidence but a difference between the code and the text.")

_LOCATED: tuple[RuleEvidence, ...] = (
    # ── Moon yogas ──────────────────────────────────────────────────────────
    # V1.3 could only say "one witness says X and we do Y, unresolved". V1.5
    # has a second independent witness saying X, so the question is closed and
    # the status changes from an evidential one to a factual one about the
    # code. The rules are not edited; see `*_textual` for the located reading.
    _evidence(
        "sunapha",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
        witness_ids=(BJ_13_3_CANDRA_YOGAS.id, BPHS_SA_37_7_CANDRA_YOGAS.id,
                     JP_83_CANDRA_YOGAS.id),
        quotation_of=(JP_83_CANDRA_YOGAS.id,),
        rule_profile="parashari",
        reference_frame="Moon",
        textual_condition=(
            "Excluding the Sun, grahas situated in the 2nd from the Moon "
            "constitute Sunaphā. BJ 13.3 hitvārkaṃ; BPHS 37.7 sūryaṃ binā."),
        software_condition=(
            "Any of Mangal, Budha, Guru, Shukra, Shani occupies the house at "
            "inclusive distance 2 from Chandra's house — the nodes excluded."),
        textual_summary=(
            "Both witnesses name Sunaphā, Anaphā and Durudharā together, "
            "formed by grahas in the 2nd, the 12th, or both from the Moon, "
            "with the Sun and only the Sun expressly excluded."),
        divergence=_MOON_YOGA_DIVERGENCE,
        corrected_by="sunapha_textual",
        audited_in=AUDITED_V15,
        ambiguities=("reading of 'sva' as the 2nd house",),
        conflicts=("SUNAPHA_NODE_EXCLUSION",),
        implementation_test="tests/test_yoga_catalog_v12.py::LunarCompanyTest",
        needs_human_review=True,
        review_reasons=("SANSKRIT_AMBIGUITY",),
        interpretive_notes=(
            "The legacy citation was 'BPHS ch.34'. The passage is at BPHS "
            "37.7; ch.34 is the yogakāraka chapter and contains no Moon "
            "yoga."),
    ),
    _evidence(
        "anapha",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
        witness_ids=(BJ_13_3_CANDRA_YOGAS.id, BPHS_SA_37_7_CANDRA_YOGAS.id,
                     JP_83_CANDRA_YOGAS.id),
        quotation_of=(JP_83_CANDRA_YOGAS.id,),
        rule_profile="parashari",
        reference_frame="Moon",
        textual_condition=(
            "Excluding the Sun, grahas situated in the 12th from the Moon "
            "constitute Anaphā."),
        software_condition=(
            "Any of the five tara grahas occupies the house at inclusive "
            "distance 12 from Chandra's house — the nodes excluded."),
        textual_summary="See BJ 13.3 and BPHS 37.7, the same rule in both.",
        divergence=_MOON_YOGA_DIVERGENCE,
        corrected_by="anapha_textual",
        audited_in=AUDITED_V15,
        ambiguities=("reading of 'antya' as the 12th house",),
        conflicts=("SUNAPHA_NODE_EXCLUSION",),
        implementation_test="tests/test_yoga_catalog_v12.py::LunarCompanyTest",
        needs_human_review=True,
        review_reasons=("SANSKRIT_AMBIGUITY",),
    ),
    _evidence(
        "durudhara",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
        witness_ids=(BJ_13_3_CANDRA_YOGAS.id, BPHS_SA_37_7_CANDRA_YOGAS.id,
                     JP_83_CANDRA_YOGAS.id),
        quotation_of=(JP_83_CANDRA_YOGAS.id,),
        rule_profile="parashari",
        reference_frame="Moon",
        textual_condition=(
            "Excluding the Sun, grahas in BOTH the 2nd and the 12th from the "
            "Moon constitute Durudharā."),
        software_condition=(
            "Both houses at inclusive distance 2 and 12 from Chandra are "
            "occupied by tara grahas — the nodes excluded."),
        textual_summary="See BJ 13.3 and BPHS 37.7.",
        divergence=_MOON_YOGA_DIVERGENCE,
        corrected_by="durudhara_textual",
        audited_in=AUDITED_V15,
        conflicts=("SUNAPHA_NODE_EXCLUSION",),
        implementation_test="tests/test_yoga_catalog_v12.py::LunarCompanyTest",
        needs_human_review=True,
        review_reasons=("SANSKRIT_AMBIGUITY",),
        interpretive_notes=(
            "Spelling: the engine has 'durudhara', BJ has durudhurā and BPHS "
            "37.7 duradharā. The witnesses do not agree with each other on "
            "the spelling either. Not a substantive difference."),
    ),
    _evidence(
        "kemadruma",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
        witness_ids=(BJ_13_3_CANDRA_YOGAS.id, BPHS_SA_37_11_KEMADRUMA.id,
                     JP_83_CANDRA_YOGAS.id),
        quotation_of=(JP_83_CANDRA_YOGAS.id,),
        rule_profile="parashari",
        reference_frame="Moon",
        textual_condition=(
            "BPHS 37.11: Kemadruma arises when no graha other than the Sun "
            "occupies the 1st, 2nd or 12th from the Moon, AND no graha other "
            "than the Moon occupies a kendra from the Lagna. BJ 13.3: not "
            "accepted when the Moon is in a kendra or conjoined with a graha; "
            "a further kendra/navāṃśa opinion is reported and rejected as "
            "ukti-prasiddhā na te."),
        software_condition=(
            "No tara graha in the 2nd or 12th from Chandra; cancelled by any "
            "of four clauses, two of which no witness states and one of "
            "which BPHS 37.11 contradicts."),
        textual_summary=(
            "Kemadruma is the negative case of the preceding three yogas. "
            "Both witnesses give cancellations and the two sets do not "
            "coincide; BJ additionally records, and dismisses, a third set."),
        divergence=(
            "Of the engine's four bhanga clauses: kendra-from-Lagna is "
            "supported by BPHS 37.11; conjunction with a graha is supported "
            "by BJ 13.3 and by BPHS's inclusion of the 1st house; a graha in "
            "a kendra from the MOON is stated by neither; and the Moon itself "
            "in a kendra from the Lagna is CONTRADICTED by BPHS 37.11, which "
            "excludes the Moon from the grahas that count (vinā candraṃ). "
            "The engine also excludes the nodes from the 2nd and 12th, as in "
            "the other Moon yogas."),
        corrected_by="kemadruma_textual",
        audited_in=AUDITED_V15,
        conflicts=("KEMADRUMA_BHANGA_EXTENT", "SUNAPHA_NODE_EXCLUSION"),
        implementation_test="tests/test_yoga_engine.py::KemadrumaTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION", "SANSKRIT_AMBIGUITY"),
    ),

    # ── Adhi Yoga: the best-attested rule in the engine ─────────────────────
    _evidence(
        "adhi_yoga",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.VALIDATED_FOR_PROFILE,
        witness_ids=(BJ_13_2_ADHIYOGA.id, BPHS_SA_37_5_ADHIYOGA.id,
                     JP_114_LAGNADHIYOGA.id),
        rule_profile="parashari",
        reference_frame="Moon",
        textual_condition=(
            "Benefics in the 6th, 7th and 8th from the Moon constitute "
            "Adhiyoga."),
        software_condition=(
            "Guru, Shukra and Budha occupy the houses at inclusive distances "
            "6, 7 and 8 from Chandra, all three being occupied."),
        textual_summary=(
            "Three works give this rule, and two of them give it "
            "independently. BJ 13.2 names the houses smara, ari and nidhana; "
            "BPHS 37.5 names them randhra, ari and kāma; Jātaka Pārijāta 113 "
            "repeats BJ's vocabulary and heads it candrādhiyoga. Different "
            "words for the same three houses from the same reference point."),
        audited_in=AUDITED_V15,
        ambiguities=(
            "whether every one of the three houses must be occupied, or only "
            "that the benefics fall among them",),
        implementation_test="tests/test_yoga_catalog_v12.py::AdhiAndAmalaTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "VALIDATED_FOR_PROFILE and not TRADITION_VALIDATED, for one "
            "reason: the ambiguity above is unresolved, and it is not "
            "academic — it decides whether the yoga is rare or common. The "
            "engine requires all three houses occupied, which is the strict "
            "reading. The legacy citation was 'BPHS ch.36'; the BPHS passage "
            "is at 37.5."),
    ),

    # ── Amala ───────────────────────────────────────────────────────────────
    _evidence(
        "amala_yoga",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.SECOND_WITNESS_CHECKED,
        witness_ids=(BPHS_SA_36_5_AMALA.id, JATAKA_PARIJATA_SD.id),
        rule_profile="parashari_extended",
        reference_frame="Lagna or Moon",
        textual_condition=(
            "Benefics ALONE (kevalaiḥ) in the 10th from the Lagna or from the "
            "Moon."),
        software_condition=(
            "The 10th from the Lagna is occupied, every occupant is a natural "
            "benefic, and no malefic occupies it."),
        textual_summary=(
            "BPHS 36.5 and Jātaka Pārijāta's amalāyoga verse agree: a benefic "
            "in the 10th counted from the Moon or the Lagna. BPHS's kevalaiḥ "
            "makes the exclusivity explicit, which is what the engine "
            "implements."),
        audited_in=AUDITED_V15,
        known_variants=(
            "reference frame: the engine counts from the Lagna only, while "
            "both witnesses allow the Moon as well",),
        implementation_test="tests/test_yoga_catalog_v12.py::AdhiAndAmalaTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_REFERENCE_FRAME",),
        interpretive_notes=(
            "Not raised to VALIDATED_FOR_PROFILE because the engine "
            "implements only half the reference frame both witnesses give. "
            "That is a narrowing rather than an error — every chart the "
            "engine reports is one the text would accept — but it is not a "
            "match. The legacy citation 'BPHS ch.36' named the right chapter, "
            "by coincidence rather than by checking: the verse is 36.5 and "
            "the citation gave no verse."),
    ),
)

# ── V1.5 Part 1: the rest of the corpus ──────────────────────────────────────
#
# Every remaining shipped rule was checked against the Sanskrit witnesses
# obtained in V1.5. The result splits four ways, and the split is the finding:
#
#   LOCATED AND MATCHING        the text was found and the code does it
#   LOCATED AND DIVERGING       the text was found and the code does not
#   LOCATED ELSEWHERE           the rule is real, the citation was wrong
#   READ AND ABSENT             the cited chapter was read and does not
#                               contain the rule — a negative result, which
#                               is evidence and is recorded as such
#
# The fourth category is the one that did not exist before V1.5. "UNVERIFIED"
# covers both "we never looked" and "we looked and it isn't there", and those
# are very different states to leave a reader in.

_MAHAPURUSHA_PLANETS = {
    "ruchaka": "Mangal", "bhadra": "Budha", "hamsa": "Guru",
    "malavya": "Shukra", "shasha": "Shani",
}


def _mahapurusha_evidence() -> list[RuleEvidence]:
    out = []
    for key, planet in _MAHAPURUSHA_PLANETS.items():
        out.append(_evidence(
            f"mahapurusha_{key}",
            classification=RuleClassification.CLASSICAL_VARIANT,
            validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
            witness_ids=(BPHS_SA_75_1_MAHAPURUSHA.id, JP_59_MAHAPURUSHA.id),
            rule_profile="parashari",
            reference_frame="Lagna",
            textual_condition=(
                f"{planet} in a kendra, in own sign or exaltation (Jātaka "
                f"Pārijāta 59 adds moolatrikona), AND STRONG — balibhiḥ at "
                f"BPHS 75.1, baliṣṭhāḥ at JP 59."),
            software_condition=(
                f"{planet} is in own sign, moolatrikona or exaltation AND "
                f"occupies a kendra from the Lagna. Cancelled if combust."),
            textual_summary=(
                "The five yogas are named together in one verse in each "
                "witness, assigned to Mars, Mercury, Jupiter, Venus and "
                "Saturn in that order."),
            divergence=(
                "The strength requirement is missing. Both witnesses state it "
                "and they are otherwise independent, so this is the clearest "
                "single correctable finding of the V1.5 audit. The engine "
                "instead cancels on combustion, which neither witness "
                "mentions here."),
            corrected_by=f"mahapurusha_{key}_textual",
            audited_in=AUDITED_V15,
            known_variants=(
                "dignity set: BPHS gives own sign and exaltation, Jātaka "
                "Pārijāta adds moolatrikona; the engine follows the wider "
                "reading",),
            conflicts=("MAHAPURUSHA_STRENGTH_REQUIREMENT",),
            implementation_test="tests/test_yoga_engine.py::MahapurushaTest",
            needs_human_review=True,
            review_reasons=("UNCLEAR_REFERENCE_FRAME",),
            interpretive_notes=(
                "The legacy citation 'BPHS ch.75' is the ONLY one in the "
                "whole corpus that named the correct chapter. V1.3 recorded "
                "that these yogas are demonstrably absent from Bṛhajjātaka "
                "and guessed at Sārāvalī; the answer was BPHS all along."),
        ))
    return out


def _generated_family_evidence(prefix: str, count_note: str, **kwargs
                               ) -> RuleEvidence:
    """One shared evidence record for a combinatorially generated family."""
    return _evidence(prefix, **kwargs)


_V15_AUDITED: tuple[RuleEvidence, ...] = tuple(_mahapurusha_evidence()) + (

    # ── Sun yogas: located, wrong chapter, and a narrower graha set ─────────
    _evidence(
        "vesi",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_38_1_RAVI_YOGAS.id,),
        rule_profile="parashari",
        reference_frame="Sun",
        textual_condition=(
            "Grahas — kujādi, 'Mars and the rest' — in the 2nd from the Sun, "
            "the Moon excluded (vinā candraṃ), constitute Veśi."),
        software_condition=(
            "A tara graha other than Chandra occupies the house at inclusive "
            "distance 2 from Surya's house."),
        textual_summary=(
            "BPHS 38.1 names Veśi, Vośi and Ubhayacarī together, from the "
            "2nd, the 12th and both from the Sun."),
        audited_in=AUDITED_V15,
        ambiguities=(
            "whether kujādi denotes exactly the five tara grahas or any graha "
            "from Mars onward in the traditional order",),
        implementation_test="tests/test_yoga_catalog_v12.py::SolarCompanyTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "Note the contrast with the Moon yogas, which is why the node "
            "question matters: there the text excludes the SUN and the engine "
            "adds the nodes, which is a divergence. Here the text excludes "
            "the MOON and enumerates from Mars, so excluding the nodes is a "
            "defensible reading of kujādi rather than an addition. Same "
            "engine behaviour, different textual standing. Legacy citation "
            "'BPHS ch.34' was wrong; the passage is 38.1."),
    ),
    _evidence(
        "vasi",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_38_1_RAVI_YOGAS.id,),
        rule_profile="parashari", reference_frame="Sun",
        textual_condition=(
            "Grahas in the 12th from the Sun, the Moon excluded, constitute "
            "Vośi."),
        software_condition=(
            "A tara graha other than Chandra occupies the house at inclusive "
            "distance 12 from Surya's house."),
        textual_summary="See BPHS 38.1.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_yoga_catalog_v12.py::SolarCompanyTest",
        needs_human_review=True, review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "The witness spells this vośi; the engine has 'vasi'. Both "
            "spellings are current in the literature."),
    ),
    _evidence(
        "ubhayachari",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_38_1_RAVI_YOGAS.id,),
        rule_profile="parashari", reference_frame="Sun",
        textual_condition=(
            "Grahas in BOTH the 2nd and the 12th from the Sun, the Moon "
            "excluded, constitute Ubhayacarī."),
        software_condition=(
            "Both houses at inclusive distance 2 and 12 from Surya are "
            "occupied by tara grahas other than Chandra."),
        textual_summary="See BPHS 38.1.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_yoga_catalog_v12.py::SolarCompanyTest",
        needs_human_review=True, review_reasons=("UNCLEAR_EXCEPTION",),
    ),

    # ── Gajakesari ─────────────────────────────────────────────────────────
    _evidence(
        "gajakesari",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
        witness_ids=(BPHS_SA_36_3_GAJAKESARI.id, JP_116_GAJAKESARI.id),
        rule_profile="parashari",
        reference_frame="Moon (Jātaka Pārijāta) or Lagna/Moon (BPHS)",
        textual_condition=(
            "Jupiter in a kendra — from the Moon per JP 116, from the Lagna "
            "or the Moon per BPHS 36.3 — conjoined with or aspected by "
            "benefics (BPHS), and free of debilitation, combustion and, in "
            "BPHS, enemy signs."),
        software_condition=(
            "Guru occupies a kendra counted from Chandra. No dignity, "
            "combustion or benefic-association condition is applied."),
        textual_summary=(
            "Both witnesses give the yoga its name in the same words — "
            "gajakesarī — and both hedge it with conditions on Jupiter's "
            "condition that the engine does not implement."),
        divergence=(
            "The engine tests placement only. Both witnesses additionally "
            "require Jupiter to be free of debilitation and combustion, and "
            "BPHS 36.3 also of enemy signs and requires benefic association. "
            "Gajakesari is consequently reported far more often than either "
            "text would allow."),
        corrected_by="gajakesari_textual_bphs / "
                     "gajakesari_textual_jataka_parijata",
        audited_in=AUDITED_V15,
        conflicts=("GAJAKESARI_REFERENCE_FRAME",),
        implementation_test="tests/test_yoga_engine.py::GajakesariTest",
        needs_human_review=True,
        review_reasons=("TRANSLATION_DISAGREEMENT",),
        interpretive_notes=(
            "Legacy citation 'BPHS ch.34' was wrong; the passage is 36.3."),
    ),

    # ── Raja Yogas: right doctrine, wrong citation, missing exception ──────
    _evidence(
        "raja_yoga_generated",
        kind="rule_family",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_DIVERGES,
        witness_ids=(BPHS_SA_34_YOGAKARAKA.id, BPHS_SA_41_28_RAJAYOGA.id),
        rule_profile="parashari",
        reference_frame="Lagna",
        textual_condition=(
            "BPHS 34.11-12: a kendra lord and a trikoṇa lord in each other's "
            "houses, together in one sign, or in mutual FULL aspect "
            "(pūrṇa-dṛṣṭyā), become yogakāraka. BPHS 34.15: not when those "
            "lords also own dusthanas. BPHS 41.28: kendra is Viṣṇu's place, "
            "trikoṇa Lakṣmī's, and Rājayoga comes from their lords' "
            "sambandha."),
        software_condition=(
            "36 generated rules, one per (kendra, trikoṇa, mode) with the "
            "1st house not paired with itself, where mode is conjunction, "
            "mutual aspect or exchange. No exception is applied."),
        textual_summary=(
            "The doctrine the engine implements is squarely in the text, and "
            "the text enumerates exactly the three modes the engine "
            "generates — which is a better result than the citation deserved."),
        divergence=(
            "Two differences. The exception at BPHS 34.15 is not implemented "
            "at all, and it is not a marginal clause: on most ascendants at "
            "least one kendra or trikoṇa lord also owns a dusthana. And the "
            "witness says pūrṇa-dṛṣṭyā, full aspect, where the engine's "
            "mutual_aspect mode accepts any graha drishti including the "
            "partial special aspects."),
        corrected_by="raja_yoga_*_textual",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_rule_audit.py::RajaYogaAuditTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "Legacy citation 'BPHS ch.36 (Raja Yoga Adhyaya)' is wrong twice "
            "over: ch.36 is vividha-yoga, and ch.39, which IS titled "
            "rājayogādhyāya, is largely Jaimini material — kārakāṃśa, "
            "ātmakāraka, ārūḍha — and not the source of this rule either. "
            "This one evidence record covers all 36 generated rules; they "
            "share a condition shape and a source."),
    ),

    # ── Dhana Yogas: read and absent ───────────────────────────────────────
    _evidence(
        "dhana_yoga_generated",
        kind="rule_family",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.UNVERIFIED,
        witness_ids=(),
        rule_profile="parashari",
        reference_frame="Lagna",
        software_condition=(
            "30 generated rules over relationships among the lords of the "
            "1st, 2nd, 5th, 9th and 11th, plus one placement rule."),
        textual_summary=(
            "NEGATIVE RESULT. BPHS ch.41, viśeṣa-dhana-yoga, was read in "
            "full. It gives wealth combinations as specific grahas in "
            "specific houses in their own signs (41.2-15), not as "
            "relationships among house lords. The single point of contact is "
            "41.16, where the lords of the 9th and 5th are called "
            "wealth-givers. Chapter 40, which the engine cited, is "
            "rāja-sambandha-yoga and concerns royal patronage."),
        audited_in=AUDITED_V15,
        conflicts=("DHANA_YOGA_NOT_LOCATED",),
        needs_human_review=True,
        review_reasons=("NO_WITNESS_AVAILABLE",),
        interpretive_notes=(
            "Left UNVERIFIED rather than marked as diverging, because there "
            "is no located text to diverge from — the rule is simply not in "
            "the chapter it claimed. The classification moves from UNVERIFIED "
            "to TRADITIONAL_MODERN_CONVENTION, which says what these rules "
            "actually are: standard modern Parāśarī practice with no located "
            "classical statement."),
    ),
    _evidence(
        "dhana_yoga_2_11_placement",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.UNVERIFIED,
        rule_profile="parashari",
        software_condition=(
            "The 2nd lord occupies the 11th and the 11th lord the 2nd."),
        textual_summary=(
            "NEGATIVE RESULT. Cited as 'BPHS ch.40.4'. BPHS 40.4 concerns the "
            "amātyakāraka being strong and well-placed, and says nothing "
            "about the 2nd or 11th lords."),
        audited_in=AUDITED_V15,
        conflicts=("DHANA_YOGA_NOT_LOCATED",),
        needs_human_review=True, review_reasons=("NO_WITNESS_AVAILABLE",),
    ),
    _evidence(
        "chandra_mangala",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.UNVERIFIED,
        rule_profile="parashari",
        software_condition="Chandra and Mangal occupy the same rashi.",
        textual_summary=(
            "NEGATIVE RESULT. Cited as 'BPHS ch.40.9'. BPHS 40.9 concerns the "
            "amātyakāraka and the lord of the janma rāśi. The combination is "
            "not in the chandra-yoga chapter (37) either, which was read in "
            "full."),
        audited_in=AUDITED_V15,
        needs_human_review=True, review_reasons=("NO_WITNESS_AVAILABLE",),
    ),
    _evidence(
        "budha_aditya",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.UNVERIFIED,
        rule_profile="parashari",
        software_condition="Budha and Surya occupy the same rashi.",
        textual_summary=(
            "NEGATIVE RESULT. Cited as 'BPHS ch.34'. Chapter 34 is "
            "yogakāraka and contains no such combination; chapter 38, the "
            "ravi-yoga chapter, gives Veśi, Vośi and Ubhayacarī and not this."),
        audited_in=AUDITED_V15,
        needs_human_review=True, review_reasons=("NO_WITNESS_AVAILABLE",),
    ),

    # ── Vipareeta: real, and in the other book ─────────────────────────────
    _evidence(
        "vipareeta_harsha",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(PD_6_57_VIPAREETA.id,),
        rule_profile="parashari_extended", reference_frame="Lagna",
        textual_condition=(
            "Phaladīpikā 6.57 names twelve yogas after the twelve bhāvas, "
            "arising when a bhāva's lord is duḥstha or is conjoined with or "
            "aspected by malefics. The sixth of the twelve is Harṣa."),
        software_condition=(
            "The 6th lord occupies the 6th, 8th or 12th house."),
        textual_summary=(
            "The names Harṣa, Sarala and Vimala belong to a single "
            "Phaladīpikā verse that names all twelve, in bhāva order, with "
            "their phala following at 6.58 onwards."),
        audited_in=AUDITED_V15,
        ambiguities=(
            "the verse gives duḥstha OR malefic affliction; the engine "
            "implements only the first limb",),
        implementation_test="tests/test_yoga_catalog_v12.py::VipareetaTest",
        needs_human_review=True,
        review_reasons=("COMMENTARY_REQUIRED",),
        interpretive_notes=(
            "The legacy citation was 'BPHS ch.36; Phaladeepika ch.6.38'. The "
            "second half was close — right chapter, wrong verse. The first "
            "half is wrong in a more interesting way: the three names occur "
            "NOWHERE in the Sanskrit BPHS, which was searched in full. BPHS "
            "does have a dusthana-lord rule at 39.19-20, but it is a single "
            "combined condition requiring all three lords afflicted together "
            "with a strong Lagna lord, and it is unnamed."),
    ),
    _evidence(
        "vipareeta_sarala",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(PD_6_57_VIPAREETA.id,),
        rule_profile="parashari_extended", reference_frame="Lagna",
        textual_condition=(
            "The eighth of the twelve bhāva-lord yogas of Phaladīpikā 6.57; "
            "phala at 6.65."),
        software_condition="The 8th lord occupies the 6th, 8th or 12th house.",
        textual_summary="See PD 6.57.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_yoga_catalog_v12.py::VipareetaTest",
        needs_human_review=True, review_reasons=("COMMENTARY_REQUIRED",),
    ),
    _evidence(
        "vipareeta_vimala",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(PD_6_57_VIPAREETA.id,),
        rule_profile="parashari_extended", reference_frame="Lagna",
        textual_condition=(
            "The twelfth of the twelve bhāva-lord yogas of Phaladīpikā 6.57."),
        software_condition="The 12th lord occupies the 6th, 8th or 12th house.",
        textual_summary="See PD 6.57.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_yoga_catalog_v12.py::VipareetaTest",
        needs_human_review=True, review_reasons=("COMMENTARY_REQUIRED",),
    ),

    # ── Lakshmi and Saraswati ──────────────────────────────────────────────
    _evidence(
        "lakshmi_yoga",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.CONFLICTING_SOURCES,
        witness_ids=(BPHS_SA_36_27_LAKSHMI.id, PD_6_21_LAKSHMI.id),
        rule_profile="parashari_extended", reference_frame="Lagna",
        textual_condition=(
            "BPHS 36.27: the 9th lord in a kendra, moolatrikona, own sign or "
            "exaltation, with a strong Lagna lord. Phaladīpikā 6.21: the 9th "
            "lord AND Venus, both dignified and both angular or trinal."),
        software_condition=(
            "The V1.1 rule tests the 9th lord's dignity and placement without "
            "either the Lagna-lord strength of BPHS or the Venus condition "
            "of Phaladīpikā."),
        textual_summary=(
            "Two witnesses, two genuinely different rules sharing a name."),
        audited_in=AUDITED_V15,
        conflicts=("LAKSHMI_YOGA_DEFINITION",),
        corrected_by="lakshmi_yoga_bphs / lakshmi_yoga_phaladeepika",
        implementation_test="tests/test_rule_audit.py::LakshmiConflictTest",
        needs_human_review=True,
        review_reasons=("TRANSLATION_DISAGREEMENT",),
        interpretive_notes=(
            "The shipped rule matches neither witness, so it is not a variant "
            "reading of either — it is a third thing. Both located readings "
            "are implemented separately; this one is retained for "
            "compatibility and excluded from strict synthesis."),
    ),
    _evidence(
        "saraswati_yoga",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(PD_6_26_SARASVATI.id,),
        rule_profile="parashari_extended", reference_frame="Lagna",
        textual_condition=(
            "Venus, Jupiter and Mercury in kendras, trikoṇas or the 2nd, "
            "with Jupiter additionally in own, exalted or friendly sign and "
            "strong (vīryage)."),
        software_condition=(
            "Guru, Shukra and Budha each occupy a kendra, a trikona or the "
            "2nd. The engine does not test Jupiter's dignity or strength."),
        textual_summary=(
            "One verse, Phaladīpikā 6.26, with the phala following."),
        divergence=(
            "The verse's second limb — Jupiter dignified AND strong — is not "
            "implemented."),
        audited_in=AUDITED_V15,
        implementation_test="tests/test_yoga_catalog_v12.py::SaraswatiTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "Legacy citation 'Phaladeepika ch.6.33; Jataka Parijata' — the "
            "verse is 6.26, and no Sarasvatī yoga was found in Jātaka "
            "Pārijāta. Kept at RULE_INTERPRETATION_MAPPED rather than marked "
            "as diverging: the omission narrows nothing and widens the rule, "
            "but it is a single clause of one verse and the corrected form is "
            "not yet implemented."),
    ),

    # ── Neecha Bhanga ──────────────────────────────────────────────────────
    _evidence(
        "neecha_bhanga_family",
        kind="rule_family",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.UNVERIFIED,
        rule_profile="parashari",
        software_condition=(
            "Seven cancellation rules and seven Neecha Bhanga Raja Yoga "
            "rules, one per graha, on dispositor and exaltation-lord "
            "placement in kendras."),
        textual_summary=(
            "NEGATIVE RESULT. Cited as 'BPHS ch.75', which is the "
            "pañca-mahāpuruṣa chapter and has nothing to do with "
            "debilitation cancellation. The full Sanskrit BPHS was searched "
            "for nīcabhaṅga and the compound does not occur; chapters 9 and "
            "10 are ariṣṭa and ariṣṭabhaṅga, which concern early death, not "
            "debilitation."),
        audited_in=AUDITED_V15,
        needs_human_review=True, review_reasons=("NO_WITNESS_AVAILABLE",),
        interpretive_notes=(
            "Covers all 14 neecha_bhanga_* rules. The doctrine is universal "
            "in modern practice and its classical home has not been found."),
    ),
    _evidence(
        "dharma_karmadhipati_family",
        kind="rule_family",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(BPHS_SA_34_YOGAKARAKA.id,),
        rule_profile="parashari", reference_frame="Lagna",
        textual_condition=(
            "The 9th is a trikoṇa and the 10th a kendra, so the pair falls "
            "under the general rule of BPHS 34.11-12 and 41.28. BPHS 39.37 "
            "additionally names the 4th and 10th lords joined with the 5th or "
            "9th lord as giving royalty."),
        software_condition=(
            "Three rules over the 9th and 10th lords by conjunction, mutual "
            "aspect and exchange."),
        textual_summary=(
            "Attested as an instance of the general kendra-trikoṇa rule "
            "rather than under its own name, which no witness uses."),
        audited_in=AUDITED_V15,
        needs_human_review=True, review_reasons=("COMMENTARY_REQUIRED",),
        interpretive_notes=(
            "The engine's note calls this 'the strongest of the Raja Yogas'. "
            "No located witness says so or singles the pair out at all. That "
            "claim is a software convention and is marked as one."),
    ),
)

# ── V1.5 Part 2: evidence for the corrected rules ────────────────────────────
#
# These are the rules written FROM the witnesses rather than checked against
# them, and they are the reason the evidence-gated strict profile stops being
# a single rule. Note which of them do NOT get in: wherever two witnesses
# state a formation condition differently — Gajakesari's reference frame, the
# Mahāpuruṣa dignity set, Lakṣmī's whole definition — the rule carries the
# conflict and is excluded. Good sourcing is not the same as settled sourcing.

_MAHAPURUSHA_TEXTUAL_CONDITION = (
    "In own sign, moolatrikona or exaltation (JP 59; BPHS 75.1 omits "
    "moolatrikona), in a kendra, and strong — balibhiḥ / baliṣṭhāḥ.")


def _mahapurusha_textual_evidence() -> list[RuleEvidence]:
    out = []
    for key, planet in _MAHAPURUSHA_PLANETS.items():
        out.append(_evidence(
            f"mahapurusha_{key}_textual",
            classification=RuleClassification.CLASSICAL_VARIANT,
            validation_status=ValidationStatus.CONFLICTING_SOURCES,
            witness_ids=(BPHS_SA_75_1_MAHAPURUSHA.id, JP_59_MAHAPURUSHA.id),
            rule_profile="parashari_textual",
            reference_frame="Lagna",
            textual_condition=_MAHAPURUSHA_TEXTUAL_CONDITION,
            software_condition=(
                f"{planet} has own_sign, moolatrikona or exalted dignity, "
                f"occupies a kendra from the Lagna, and its Shadbala total "
                f"is at or above the BPHS 27.32-33 requirement."),
            textual_summary=(
                "Implements the strength clause the default rule omits. The "
                "dignity set follows the wider of the two witnesses."),
            audited_in=AUDITED_V15,
            conflicts=("MAHAPURUSHA_DIGNITY_SET",),
            ambiguities=(
                "balibhiḥ is read as Shadbala at or above requirement; no "
                "witness says which measure of strength is meant",),
            implementation_test=(
                "tests/test_rule_audit.py::MahapurushaTextualTest"),
            needs_human_review=True,
            review_reasons=("UNCLEAR_REFERENCE_FRAME",),
            interpretive_notes=(
                "Reading balibhiḥ as Shadbala is an ENGINE CONVENTION, not a "
                "textual one, and it is doing real work: it decides whether "
                "the yoga forms. It is defensible — Shadbala is BPHS's own "
                "measure of graha strength, from ch.27 of the same work — and "
                "it is not what the verse says."),
        ))
    return out


_V15_TEXTUAL: tuple[RuleEvidence, ...] = tuple(
    _mahapurusha_textual_evidence()) + (

    _evidence(
        "sunapha_textual",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_37_7_CANDRA_YOGAS.id, BJ_13_3_CANDRA_YOGAS.id),
        rule_profile="parashari_textual", reference_frame="Moon",
        textual_condition=(
            "Excluding the Sun, a graha in the 2nd from the Moon constitutes "
            "Sunaphā."),
        software_condition=(
            "Any of Mangal, Budha, Guru, Shukra, Shani, Rahu or Ketu occupies "
            "the house at inclusive distance 2 from Chandra's house."),
        textual_summary="BPHS 37.7 and BJ 13.3, agreeing.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_rule_audit.py::MoonYogaTextualTest",
        needs_human_review=False,
    ),
    _evidence(
        "anapha_textual",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_37_7_CANDRA_YOGAS.id, BJ_13_3_CANDRA_YOGAS.id),
        rule_profile="parashari_textual", reference_frame="Moon",
        textual_condition=(
            "Excluding the Sun, a graha in the 12th from the Moon constitutes "
            "Anaphā."),
        software_condition=(
            "Any graha but Surya and Chandra occupies the house at inclusive "
            "distance 12 from Chandra's house."),
        textual_summary="BPHS 37.7 and BJ 13.3, agreeing.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_rule_audit.py::MoonYogaTextualTest",
        needs_human_review=False,
    ),
    _evidence(
        "durudhara_textual",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_37_7_CANDRA_YOGAS.id, BJ_13_3_CANDRA_YOGAS.id),
        rule_profile="parashari_textual", reference_frame="Moon",
        textual_condition=(
            "Excluding the Sun, grahas in both the 2nd and the 12th from the "
            "Moon constitute Durudharā."),
        software_condition=(
            "Both houses at inclusive distance 2 and 12 from Chandra are "
            "occupied by grahas other than Surya."),
        textual_summary="BPHS 37.7 and BJ 13.3, agreeing.",
        audited_in=AUDITED_V15,
        implementation_test="tests/test_rule_audit.py::MoonYogaTextualTest",
        needs_human_review=False,
    ),
    _evidence(
        "kemadruma_textual",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.CONFLICTING_SOURCES,
        witness_ids=(BPHS_SA_37_11_KEMADRUMA.id, BJ_13_3_CANDRA_YOGAS.id),
        rule_profile="parashari_textual", reference_frame="Moon",
        textual_condition=(
            "BPHS 37.11: no graha but the Sun in the 1st, 2nd or 12th from "
            "the Moon, and no graha but the Moon in a kendra from the Lagna."),
        software_condition=(
            "Isolation across the 1st, 2nd and 12th from Chandra with Surya "
            "excluded; cancelled by any graha other than Chandra in a kendra "
            "from the Lagna."),
        textual_summary=(
            "Follows BPHS 37.11 exactly. Bṛhajjātaka 13.3 gives a different "
            "cancellation set — the Moon in a kendra, or conjoined with a "
            "graha — and the two do not coincide."),
        audited_in=AUDITED_V15,
        conflicts=("KEMADRUMA_BHANGA_EXTENT",),
        implementation_test="tests/test_rule_audit.py::KemadrumaTextualTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "Kept at CONFLICTING_SOURCES, and therefore out of the strict "
            "profile, even though it faithfully implements one witness. "
            "Implementing one of two disagreeing readings resolves nothing; "
            "it just picks a side quietly."),
    ),
    _evidence(
        "gajakesari_textual_bphs",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.CONFLICTING_SOURCES,
        witness_ids=(BPHS_SA_36_3_GAJAKESARI.id,),
        rule_profile="parashari_textual", reference_frame="Lagna or Moon",
        textual_condition=(
            "Jupiter in a kendra from the Lagna or the Moon, conjoined with "
            "or aspected by benefics, free of debilitation, combustion and "
            "enemy signs."),
        software_condition=(
            "Guru in a kendra counted from either the Lagna or Chandra; at "
            "least one natural benefic conjunct or aspecting; not "
            "debilitated, not combust, not in an enemy sign."),
        textual_summary="BPHS 36.3.",
        audited_in=AUDITED_V15,
        conflicts=("GAJAKESARI_REFERENCE_FRAME",),
        implementation_test="tests/test_rule_audit.py::GajakesariTextualTest",
        needs_human_review=True,
        review_reasons=("TRANSLATION_DISAGREEMENT",),
    ),
    _evidence(
        "gajakesari_textual_jataka_parijata",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.CONFLICTING_SOURCES,
        witness_ids=(JP_116_GAJAKESARI.id,),
        rule_profile="parashari_textual", reference_frame="Moon",
        textual_condition=(
            "Jupiter in a kendra from the Moon, free of debilitation and "
            "combustion."),
        software_condition=(
            "Guru in a kendra counted from Chandra; not debilitated, not "
            "combust."),
        textual_summary="Jātaka Pārijāta 116.",
        audited_in=AUDITED_V15,
        conflicts=("GAJAKESARI_REFERENCE_FRAME",),
        implementation_test="tests/test_rule_audit.py::GajakesariTextualTest",
        needs_human_review=True,
        review_reasons=("TRANSLATION_DISAGREEMENT",),
    ),
    _evidence(
        "raja_yoga_textual_family",
        kind="rule_family",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_SA_34_YOGAKARAKA.id, BPHS_SA_41_28_RAJAYOGA.id),
        rule_profile="parashari_textual", reference_frame="Lagna",
        textual_condition=(
            "BPHS 34.11-12: kendra lord and trikoṇa lord in each other's "
            "houses, together in one sign, or in mutual FULL aspect. "
            "BPHS 34.15: not when either also owns a dusthana. "
            "BPHS 41.28: kendra is Viṣṇu's place, trikoṇa Lakṣmī's, and "
            "Rājayoga comes from the sambandha of their lords."),
        software_condition=(
            "36 rules over (kendra, trikoṇa, mode) with mode in conjunction, "
            "full mutual aspect and exchange; each cancelled when either "
            "participating lord also owns the 6th, 8th or 12th."),
        textual_summary=(
            "The generic Rājayoga, with both the aspect qualification and the "
            "exception the default rules omit."),
        audited_in=AUDITED_V15,
        implementation_test="tests/test_rule_audit.py::RajaYogaTextualTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "IMPLEMENTATION_MATCHED with an outstanding review question, "
            "which is a combination worth reading carefully: the code does "
            "what this engine understands the verse to say, and whether that "
            "understanding of 34.15 is right is exactly what the review item "
            "asks. The status tracks the mapping, not the exegesis — which is "
            "why TRADITION_VALIDATED, and only it, requires review closed."),
    ),
    _evidence(
        "lakshmi_yoga_bphs",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.CONFLICTING_SOURCES,
        witness_ids=(BPHS_SA_36_27_LAKSHMI.id,),
        rule_profile="parashari_textual", reference_frame="Lagna",
        textual_condition=(
            "The 9th lord in a kendra, moolatrikona, own sign or exaltation, "
            "with a strong Lagna lord."),
        software_condition=(
            "The 9th lord has own_sign, moolatrikona or exalted dignity and "
            "occupies a kendra or trikona; the Lagna lord's Shadbala is at or "
            "above its requirement."),
        textual_summary="BPHS 36.27.",
        audited_in=AUDITED_V15,
        conflicts=("LAKSHMI_YOGA_DEFINITION",),
        implementation_test="tests/test_rule_audit.py::LakshmiConflictTest",
        needs_human_review=True,
        review_reasons=("TRANSLATION_DISAGREEMENT",),
    ),
    _evidence(
        "lakshmi_yoga_phaladeepika",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.CONFLICTING_SOURCES,
        witness_ids=(PD_6_21_LAKSHMI.id,),
        rule_profile="parashari_textual", reference_frame="Lagna",
        textual_condition=(
            "The 9th lord and Venus, both in own sign or exaltation, both in "
            "a kendra or trikoṇa."),
        software_condition=(
            "The 9th lord and Shukra each have own_sign or exalted dignity "
            "and each occupy a kendra or trikona."),
        textual_summary="Phaladīpikā 6.21.",
        audited_in=AUDITED_V15,
        conflicts=("LAKSHMI_YOGA_DEFINITION",),
        implementation_test="tests/test_rule_audit.py::LakshmiConflictTest",
        needs_human_review=True,
        review_reasons=("TRANSLATION_DISAGREEMENT",),
    ),
)

# Varga evidence.
_CALCULATION_LOCATED: tuple[RuleEvidence, ...] = (
    _evidence(
        "shadbala/sthana_bala",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_27_SHADBALA.id,),
        reference_frame="the graha's own longitude and house",
        textual_condition=(
            "Positional strength from five sources: proximity to exaltation, "
            "dignity across seven vargas, odd/even rashi and navamsha, "
            "angular placement, and decanate by gender group."),
        software_condition=(
            "uchcha (arc from deep debilitation / 3) + saptavargaja (7 vargas "
            "x 2-45 virupas) + ojhayugma (15 x 2) + kendradi (60/30/15) + "
            "drekkana (15)."),
        textual_summary=(
            "BPHS 27.1-6 states each subcomponent and works the Uchcha Bala "
            "example numerically, which the implementation reproduces."),
        implementation_test="tests/test_strength.py::UchchaBalaTest",
        interpretive_notes=(
            "The strongest sourcing in this engine after the D9 rule: the "
            "witness gives a worked example, and the code reproduces its "
            "number exactly."),
    ),
    _evidence(
        "shadbala/dig_bala",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_27_SHADBALA.id,),
        reference_frame="the four angles",
        textual_condition=(
            "Deduct the opposite cusp from the graha's longitude, fold above "
            "180, divide by 3. Sun and Mars are strongest on the 10th, "
            "Jupiter and Mercury on the 1st, Venus and the Moon on the 4th, "
            "Saturn on the 7th."),
        software_condition=(
            "arc from the weak-point cusp / 3, cusps taken from the "
            "Ascendant and Midheaven."),
        textual_summary=(
            "BPHS 27.7 with a worked example: Saturn on the 7th cusp scores "
            "one rupa, on the ascendant zero."),
        ambiguities=(
            "whether 'cusp' means a bhava madhya or an angle, under a "
            "whole-sign default",),
        implementation_test="tests/test_strength.py::DigBalaTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_REFERENCE_FRAME",),
    ),
    _evidence(
        "shadbala/kala_bala",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(BPHS_27_SHADBALA.id,),
        reference_frame="the birth moment",
        textual_condition=(
            "Temporal strength from nathonnatha, paksha, tribhaga, "
            "varsha/masa/dina/hora, ayana and yuddha."),
        software_condition=(
            "Six subcomponents; dina and hora exact, varsha and masa on a "
            "stated Ahargana epoch, tribhaga on assumed 06:00/18:00 "
            "sunrise/sunset."),
        textual_summary="BPHS 27.8-20.",
        ambiguities=("Ahargana epoch", "sunrise and sunset times",
                     "the declination-to-virupa mapping for ayana bala"),
        conflicts=("AHARGANA_EPOCH_UNFIXED",),
        implementation_test="tests/test_strength.py::KalaBalaTest",
        needs_human_review=True,
        review_reasons=("NUMERIC_ENCODING_UNRESOLVED",),
        interpretive_notes=(
            "Stops at RULE_INTERPRETATION_MAPPED because two subcomponents "
            "rest on conventions the witness does not fix."),
    ),
    _evidence(
        "shadbala/naisargika_bala",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BPHS_27_SHADBALA.id,),
        reference_frame="none — a constant per graha",
        textual_condition=(
            "Divide one rupa by seven and multiply by 1 to 7 for Saturn, "
            "Mars, Mercury, Jupiter, Venus, the Moon and the Sun."),
        software_condition="(60 / 7) x rank, ranks exactly as stated.",
        textual_summary="BPHS 27.14, stated as an explicit formula.",
        implementation_test="tests/test_strength.py::NaisargikaAndDrikTest",
    ),
    _evidence(
        "shadbala/drik_bala",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(BPHS_27_SHADBALA.id,),
        reference_frame="drishti received by the graha",
        textual_condition=(
            "Deduct a quarter of the drishti pinda for a malefic aspect, add "
            "a quarter for a benefic, and add the whole aspect of Mercury "
            "and Jupiter."),
        software_condition=(
            "+/-15 virupas per aspecting graha by natural nature, 60 for "
            "Mercury and Jupiter, consuming the feature layer's aspects."),
        textual_summary="BPHS 27.19.",
        ambiguities=(
            "what the drishti pinda is before the quarter is taken",),
        implementation_test="tests/test_strength.py::NaisargikaAndDrikTest",
        needs_human_review=True,
        review_reasons=("SANSKRIT_AMBIGUITY",),
    ),
    _evidence(
        "ashtakavarga/bhinna",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(BPHS_66_ASHTAKAVARGA.id,),
        reference_frame="each of eight contributors",
        textual_condition=(
            "For each graha, the houses counted from each of the eight "
            "reference points that are rekhaprada (benefic)."),
        software_condition=(
            "Eight contributor rows per graha; a bindu added to the sign at "
            "each listed house from each contributor's sign."),
        textual_summary=(
            "BPHS 66. The Sun's table at verses 43-45 was read and transposed "
            "and matches the implementation exactly. The other six are in the "
            "same chapter but their OCR is damaged."),
        ambiguities=("per-graha verification for six of the seven tables",),
        implementation_test="tests/test_ashtakavarga.py::TableIntegrityTest",
        needs_human_review=True,
        review_reasons=("MANUSCRIPT_DISAGREEMENT",),
        interpretive_notes=(
            "The classical totals (48/49/39/54/56/52/39, sarva 337) are an "
            "independent arithmetic check on the tables and all seven pass, "
            "which is evidence the tables are right even where the OCR could "
            "not be read."),
    ),
    _evidence(
        "ashtakavarga/reductions",
        kind="calculation",
        classification=RuleClassification.UNVERIFIED,
        validation_status=ValidationStatus.UNVERIFIED,
        witness_ids=(),
        textual_condition="",
        software_condition=(
            "Trikona sodhana then Ekadhipatya sodhana, off by default."),
        textual_summary="",
        ambiguities=("zero-bindu trine handling",
                     "single-occupancy lordship handling"),
        implementation_test="tests/test_ashtakavarga.py::ReductionTest",
        needs_human_review=True,
        review_reasons=("MANUSCRIPT_DISAGREEMENT", "COMMENTARY_REQUIRED"),
        interpretive_notes=(
            "Implemented but NOT applied by default. The witness's OCR of "
            "these verses is damaged and traditions differ on the edge "
            "cases, so applying them silently would be wrong."),
    ),
    _evidence(
        "houses/sripati",
        kind="calculation",
        classification=RuleClassification.TRADITIONAL_MODERN_CONVENTION,
        validation_status=ValidationStatus.UNVERIFIED,
        witness_ids=(),
        reference_frame="the four angles",
        textual_condition="",
        software_condition=(
            "Quadrant trisection giving bhava madhyas; sandhis midway "
            "between adjacent madhyas; the Lagna degree is the 1st madhya."),
        textual_summary="",
        ambiguities=("whether the Lagna degree is the madhya or the cusp",
                     "whether bhava lordship follows the madhya's rashi"),
        implementation_test="tests/test_houses.py::CuspTest",
        needs_human_review=True,
        review_reasons=("NO_WITNESS_AVAILABLE", "UNCLEAR_REFERENCE_FRAME"),
        interpretive_notes=(
            "No witness located for any house system in this build. The "
            "madhya convention follows BHAVA_CHALIT_DESIGN.md, which reasoned "
            "from secondary sources rather than from a text."),
    ),
)

# ── V1.8: gochara ───────────────────────────────────────────────────────────
#
# Four releases in the making, and the shape of the record matters as much
# as its content. Both rules reach IMPLEMENTATION_MATCHED. Only one of them
# can carry a strict prediction, and the reason is not evidential — it is
# that Phaladīpikā 26 judges a transit without naming a bhāva, so there is
# nowhere for its verdict to go.

_GOCHARA_LOCATED: tuple[RuleEvidence, ...] = (
    _evidence(
        "gochara/vedha_from_moon",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(PD_26_GOCHARA.id, PD_26_VEDHA_TABLE.id,
                     PD_EN_26_SASTRI.id),
        rule_profile="phaladipika_gochara",
        reference_frame="Moon",
        textual_condition=(
            "26.1: the candra-lagna is primary in transits. 26.2 gives each "
            "graha's favourable houses from it, adds the 11th for all, and "
            "gives the nodes the Sun's. 26.3-8 pair each list positionally "
            "with vedha houses that cancel it, exempting Saturn against the "
            "Sun and Mercury against the Moon, reciprocally."),
        software_condition=(
            "engine.gochara.rules.MOON_FRAME_RULES holds seven tables of "
            "favourable houses and 36 vedha pairs, evaluated against "
            "house_from_natal_moon. Exemptions are per-rule and are not "
            "generalised."),
        textual_summary=(
            "Favourable transit houses from the Moon, each cancellable by a "
            "graha standing in a specified counter-house."),
        known_variants=(
            "The ITRANS witness reads `prApti` (11th) for Mercury's sixth "
            "vedha house, which would pair the 11th with itself; the "
            "printed edition reads the 12th.",
            "The ITRANS witness reads `vari` (4th) for Venus's eighth vedha "
            "house where the pairing and the printed edition require `ari`, "
            "the 6th."),
        ambiguities=(
            "Whether Rahu and Ketu cause vedha to other grahas. The verses "
            "say `khecharaiḥ`/`grahaiḥ` and do not enumerate.",
            "Whether the Sun's exemption from Saturn's vedha travels to the "
            "nodes along with the Sun's favourable houses."),
        conflicts=("GOCHARA_MERCURY_VEDHA_READING",),
        implementation_test="tests/test_gochara.py::MoonFrameTableTest",
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION", "NO_WITNESS_AVAILABLE"),
        audited_in=AUDITED_V18,
        interpretive_notes=(
            "Implemented and NOT strict-eligible, which is an unusual "
            "combination and a deliberate one. The chapter judges a transit "
            "favourable or obstructed in the Chandra's frame; it does not "
            "say which affairs the transit bears on. The bhāva "
            "significations this engine holds are stated from the Lagna in "
            "BPHS 11, so there is no sourced path from this verdict to a "
            "life area. 26.9-24 do give per-house effects and are not "
            "implemented — see engine.gochara.rules.UNIMPLEMENTED_LAYERS."),
    ),
    _evidence(
        "gochara/dasha_lord_from_lagna",
        kind="calculation",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(PD_20_GOCHARA_FROM_LAGNA.id, PD_EN_20_SASTRI.id),
        rule_profile="phaladipika_gochara",
        reference_frame="Lagna",
        textual_condition=(
            "Phaladīpikā 20.34: the lord of the daśā in progress, transiting "
            "its own sign, exaltation or a friend's house, nourishes the "
            "bhāva it reaches counted from the lagna — provided it was also "
            "endowed with strength at birth. 20.35: the same lord, weak, "
            "combust, debilitated or in an enemy's house AT BIRTH, destroys "
            "whichever bhāva it transits, with no condition on the "
            "transited sign."),
        software_condition=(
            "engine.gochara.engine.evaluate_dasha_lord reads the running "
            "Vimshottari stack, tests the transited rashi with "
            "engine.features.dignity and .relationships, and reads the "
            "existing Shadbala result for the natal condition. The affected "
            "bhāva is house_from_natal_lagna."),
        textual_summary=(
            "Natal → Daśā → Transit: the transiting graha must be the "
            "running daśā lord, and its natal strength decides whether the "
            "bhāva it reaches is nourished or damaged."),
        ambiguities=(
            "`balānvita`, endowed with strength, names no number. The engine "
            "substitutes BPHS 27's own required-virūpa threshold, which is a "
            "different work's measure applied to this work's condition.",),
        implementation_test=(
            "tests/test_gochara.py::DashaLordRuleTest"),
        audited_in=AUDITED_V18,
        needs_human_review=True,
        review_reasons=("UNCLEAR_EXCEPTION",),
        interpretive_notes=(
            "The first rule in this engine's history by which a transit may "
            "carry a STRICT prediction. It qualifies because every clause "
            "the verses state is implemented and because the verse names "
            "the bhāva itself, so the domain is reached through the "
            "separately-sourced BPHS 11 house significations rather than by "
            "inference. V1.5 built the Natal → Daśā → Transit hierarchy as "
            "a software convention and said so; this is the witness that a "
            "classical text states it."),
    ),
)

_VARGA_LOCATED: tuple[RuleEvidence, ...] = (
    _evidence(
        "D9/standard",
        kind="varga",
        classification=RuleClassification.CLASSICAL_SOURCE_VALIDATED,
        validation_status=ValidationStatus.IMPLEMENTATION_MATCHED,
        witness_ids=(BJ_1_6_NAVAMSHA.id,),
        reference_frame="the occupied rashi",
        textual_condition=(
            "The navāṃśa is counted from Meṣa, Makara, Tulā or Karka "
            "according to the occupied rashi."),
        software_condition=(
            "Fire rashis count from Mesha, earth from Makara, air from Tula, "
            "water from Karka; nine equal parts of 3 degrees 20 minutes."),
        textual_summary=(
            "BJ 1.6 names the four starting rashis explicitly: aja, mṛga, "
            "taulī and candra-bhavana."),
        implementation_test="tests/test_vargas_golden.py",
        interpretive_notes=(
            "The strongest Varga result in this audit. The four starting "
            "signs are named in the verse, and the engine's mapping of "
            "element-group to starting sign follows from them directly."),
    ),
    _evidence(
        "D30/parashari",
        kind="varga",
        classification=RuleClassification.CLASSICAL_VARIANT,
        validation_status=ValidationStatus.RULE_INTERPRETATION_MAPPED,
        witness_ids=(BJ_1_7_TRIMSHAMSHA.id,),
        reference_frame="the occupied rashi, by parity",
        textual_condition=(
            "The triṃśāṃśa portions belong to Maṅgala, Śani, Guru, Budha and "
            "Śukra, the order reversed in even rashis."),
        software_condition=(
            "Unequal portions of 5/5/8/7/5 degrees for odd rashis mapping to "
            "Mesha, Kumbha, Dhanu, Mithuna, Tula; reversed with the lords' "
            "other rashis for even ones."),
        textual_summary=(
            "BJ 1.7 gives the five lords in order and the odd/even reversal. "
            "The degree spans are not transparently readable in the verse."),
        ambiguities=("degree spans of the five portions",),
        implementation_test="tests/test_vargas_golden.py",
        needs_human_review=True,
        review_reasons=("NUMERIC_ENCODING_UNRESOLVED",),
        interpretive_notes=(
            "Lord order and parity reversal are attested; the 5/5/8/7/5 "
            "division is not confirmed from this witness, so the status stops "
            "at RULE_INTERPRETATION_MAPPED rather than IMPLEMENTATION_MATCHED."),
    ),
)


# ── Everything else: honest defaults ─────────────────────────────────────────

_UNVERIFIED_NOTE = (
    "No textual witness examined. The citation this rule carries was written "
    "from memory during implementation and has never been checked against an "
    "edition. The rule may well be correct and is in common use; nothing "
    "about it has been verified here.")

_GENERATED_NOTE = (
    "Generated combinatorially by the engine from a stated principle rather "
    "than transcribed from an enumeration in a text. Whether any text "
    "enumerates the combinations this way is an open question."
)


def _default_evidence(subject: str, kind: str = "yoga") -> RuleEvidence:
    """
    What a rule gets when nothing has been checked.

    Deliberately not silent: an unverified rule carries the reason it is
    unverified, so a reader of the evidence never has to guess whether the
    blank means "fine" or "unexamined".
    """
    generated = subject.startswith(("raja_yoga_", "dhana_yoga_",
                                    "dharma_karmadhipati_",
                                    "neecha_bhanga_", "vipareeta_"))
    return RuleEvidence(
        subject=subject,
        kind=kind,
        classification=RuleClassification.UNVERIFIED,
        validation_status=ValidationStatus.UNVERIFIED,
        interpretive_notes=_GENERATED_NOTE if generated else _UNVERIFIED_NOTE,
        needs_human_review=True,
        review_reasons=("NO_WITNESS_AVAILABLE",),
        last_reviewed=REVIEWED_ON,
    )


_EVIDENCE: dict[str, RuleEvidence] = {
    evidence.subject: evidence
    for evidence in (_LOCATED + _V15_AUDITED + _V15_TEXTUAL + _VARGA_LOCATED
                     + _CALCULATION_LOCATED + _GOCHARA_LOCATED)
}

# Families generated combinatorially from one principle share one source, so
# they share one evidence record rather than carrying 36 identical copies.
# Longest prefix wins, so `raja_yoga_k1_t5_conjunction` resolves to the raja
# family and not to some shorter accidental match.
_RULE_FAMILIES: tuple[tuple[str, str, str], ...] = (
    # (prefix, suffix, family). The suffix matters as much as the prefix:
    # `raja_yoga_k1_t5_conjunction` and `raja_yoga_k1_t5_conjunction_textual`
    # share a prefix and have opposite evidence — one diverges from BPHS
    # 34.11-15 and the other was written from it. Matching on the prefix
    # alone would report every corrected rule as diverging from the text it
    # was corrected to match.
    ("raja_yoga_k", "_textual", "raja_yoga_textual_family"),
    ("raja_yoga_k", "", "raja_yoga_generated"),
    ("dhana_yoga_h", "", "dhana_yoga_generated"),
    ("neecha_bhanga_", "", "neecha_bhanga_family"),
    ("dharma_karmadhipati_", "", "dharma_karmadhipati_family"),
)


def family_of(subject: str) -> Optional[str]:
    """The shared-evidence family a generated rule belongs to, if any."""
    for prefix, suffix, family in _RULE_FAMILIES:
        if subject.startswith(prefix) and subject.endswith(suffix):
            return family
    return None


def evidence_for(subject: str, kind: str = "yoga") -> RuleEvidence:
    """
    Evidence for a rule id or 'Dn/convention' key; never None.

    A generated rule inherits its family's record, with `subject` rewritten to
    the rule's own id so that a caller reporting the evidence names the rule
    it asked about rather than the family.
    """
    direct = _EVIDENCE.get(subject)
    if direct is not None:
        return direct

    family = family_of(subject)
    if family is not None and family in _EVIDENCE:
        return replace(_EVIDENCE[family], subject=subject, kind=kind)

    return _default_evidence(subject, kind)


def has_recorded_evidence(subject: str) -> bool:
    return subject in _EVIDENCE


def witnesses_for(subject: str) -> list[SourceWitness]:
    evidence = evidence_for(subject)
    return [witness_by_id(wid) for wid in evidence.witness_ids]


def all_recorded_evidence() -> tuple[RuleEvidence, ...]:
    return tuple(_EVIDENCE.values())


def all_witnesses() -> tuple[SourceWitness, ...]:
    return ALL_WITNESSES


def registry_summary() -> dict:
    """Counts for the snapshot and the report."""
    from ..rules import all_rules
    from ..vargas import VARGA_ORDER, VARGA_SPECS

    rule_ids = [rule.id for rule in all_rules()]
    varga_keys = [f"{chart}/{convention}"
                  for chart in VARGA_ORDER
                  for convention in VARGA_SPECS[chart].conventions]

    def tally(subjects: Iterable[str], kind: str) -> dict:
        counts: dict[str, int] = {}
        for subject in subjects:
            status = evidence_for(subject, kind).validation_status.value
            counts[status] = counts.get(status, 0) + 1
        return counts

    calculations = [e for e in _EVIDENCE.values() if e.kind == "calculation"]
    calculation_counts: dict[str, int] = {}
    for evidence in calculations:
        key = evidence.validation_status.value
        calculation_counts[key] = calculation_counts.get(key, 0) + 1

    return {
        "registry_version": REGISTRY_VERSION,
        "reviewed_on": REVIEWED_ON,
        "calculation_modules_total": len(calculations),
        "calculations_by_status": calculation_counts,
        "witnesses_registered": len(ALL_WITNESSES),
        "sanskrit_tier_witnesses": sum(
            1 for w in ALL_WITNESSES if w.authority.is_sanskrit_tier),
        "works_without_any_witness": sorted(UNAVAILABLE_WORKS),
        "rules_total": len(rule_ids),
        "rules_by_status": tally(rule_ids, "yoga"),
        "varga_conventions_total": len(varga_keys),
        "vargas_by_status": tally(varga_keys, "varga"),
        "conflicts": len(CONFLICTS),
        "open_review_items": sum(1 for item in REVIEW_QUEUE if item.blocking),
        "tradition_validated": 0,
    }
