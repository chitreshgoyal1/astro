"""
Gochara rule tables (V1.8 Parts 1, 3, 4, 9, 10)
-------------------------------------------------
The verses, transcribed as data.

WHY THESE ARE TABLES AND NOT CODE

    Part 3 asks for the house rules declaratively. The reason is that a
    table can be CHECKED BY A HUMAN READING THE VERSE, and a rule expressed
    as control flow cannot. `tests/test_gochara.py` asserts each row against
    the verse in the docstring below it, so a future edit that widens a list
    has to argue with a citation rather than with a test that was quietly
    updated.

HOW THE TABLES WERE ESTABLISHED

    Phaladīpikā 26 states each graha's favourable houses TWICE — once in the
    summary verse 26.2 and again in the per-graha verses 26.3-8, which also
    append the vedha houses. The two statements cross-check, and that is
    what resolved the one genuinely ambiguous syllable in 26.2 (Mercury's
    list) without guessing: 26.6 spells the same list out unambiguously.

    Two readings in the ITRANS witness are corrupt. Both were repaired from
    a second edition, and one of them — Mercury's final vedha house — could
    be rejected on internal grounds first, since the corrupt reading pairs
    the 11th with itself. See `editions.PD_SASTRI_1950`.

WHAT THE TEXT DOES NOT SAY, AND SO NEITHER DOES THIS MODULE

    26.3-8 state which houses are FAVOURABLE. They do not state that the
    remaining houses are unfavourable, and this module does not infer it:
    `unfavourable_houses` is empty for every graha in the chapter-26 table,
    and the verdict for a graha outside its favourable list is NOT_STATED.
    The inference is tempting, cheap and unsupported — Venus is favourable
    in nine houses of twelve, and reading the other three as evil would be
    this engine's doctrine rather than Mantreśvara's.

    26.9-24 DO give per-graha per-house effects, several of them plainly
    unfavourable. They are prose effects, Part 3 forbids turning house
    membership directly into prose, and they are recorded as located and
    unimplemented rather than paraphrased into the engine's own words.
"""

from __future__ import annotations

from ..sources.editions import (
    PD_20_GOCHARA_FROM_LAGNA, PD_26_GOCHARA, PD_26_VEDHA_TABLE,
    PD_EN_20_SASTRI, PD_EN_26_SASTRI,
)
from .models import GocharaRule, TransitReference, WitnessAgreement

METHODOLOGY_ID = "gochara_phaladipika_v18"

# The profile these rules belong to. They are Phaladīpikā's, not BPHS's, and
# the engine's default rule profile is Parāśarī — so a caller selecting a
# strictly Parāśarī methodology is entitled to know that its transit
# judgement comes from a different author.
GOCHARA_PROFILE = "phaladipika_gochara"

RULE_MOON_FRAME = "gochara_vedha_from_moon"
RULE_DASHA_LORD = "gochara_dasha_lord_from_lagna"

_MOON_SOURCES = (PD_26_GOCHARA.id, PD_26_VEDHA_TABLE.id, PD_EN_26_SASTRI.id)
_LAGNA_SOURCES = (PD_20_GOCHARA_FROM_LAGNA.id, PD_EN_20_SASTRI.id)

# Phaladīpikā 26.2, closing clause: `sarve 'py upāntasthitāḥ` — every graha
# is favourable in the 11th. Applied to all seven, and already present in
# each per-graha verse, so it is recorded here as provenance rather than
# added to the tables a second time.
UNIVERSAL_FAVOURABLE_HOUSE = 11


def _moon_rule(planet: str, favourable: tuple[int, ...],
               vedha: tuple[int, ...], *,
               exempt: tuple[str, ...] = (),
               exemption_reason: str = "",
               textual: str = "", notes: str = "") -> GocharaRule:
    """
    One row of the chapter-26 table.

    `favourable` and `vedha` are given IN THE VERSE'S OWN ORDER and zipped
    here, because that is how the verse pairs them: 26.3 names the Sun's
    houses 11, 3, 10, 6 and then 5, 9, 4, 12. Sorting either list before
    pairing would silently re-pair every entry, which is why the tables
    below are not written in ascending order even where that would read
    more tidily.
    """
    if len(favourable) != len(vedha):
        raise ValueError(
            f"{planet}: {len(favourable)} favourable houses but "
            f"{len(vedha)} vedha houses — the verse pairs them positionally")
    return GocharaRule(
        planet=planet,
        reference_frame=TransitReference.MOON,
        favourable_houses=favourable,
        unfavourable_houses=(),
        vedha_pairs=dict(zip(favourable, vedha)),
        vedha_exempt_planets=exempt,
        exemption_reason=exemption_reason,
        source_ref_ids=_MOON_SOURCES,
        validation_status="IMPLEMENTATION_MATCHED",
        witness_agreement=WitnessAgreement.SAME_WORK_SECOND_EDITION,
        methodology_profile=GOCHARA_PROFILE,
        rule_id=RULE_MOON_FRAME,
        textual_condition=textual,
        software_condition=(
            f"{planet}'s house counted inclusively from the natal Chandra's "
            f"rashi is in {list(favourable)}; the paired vedha house is "
            f"unoccupied by any transiting graha other than "
            f"{list(exempt) or 'none'}."),
        notes=notes,
    )


_SUN_SATURN_EXEMPTION = (
    "26.3 `vyarkibhiḥ` — by grahas OTHER THAN Saturn. Sastri's note gives "
    "the reason the text assumes: there is no vedha between father and son, "
    "and Saturn is the Sun's son. 26.5 states the converse for Saturn.")

_MOON_MERCURY_EXEMPTION = (
    "26.4 `vibudhaiḥ` and 26.6 `vividhubhiḥ` — by grahas OTHER THAN "
    "Mercury, and other than the Moon, respectively. The pair is reciprocal "
    "in the same way the Sun/Saturn pair is; no reason is given.")


# ── Phaladīpikā 26.3-8, the table ───────────────────────────────────────────

MOON_FRAME_RULES: tuple[GocharaRule, ...] = (
    # 26.3  lAbha-vikrama-kha-shatruShu sthitaH shobhano ... divAkaraH |
    #       khecharaiH suta-tapo-jala-antya-gaiH vyArkibhir yadi na viddhyate
    _moon_rule(
        "Surya", (11, 3, 10, 6), (5, 9, 4, 12),
        exempt=("Shani",), exemption_reason=_SUN_SATURN_EXEMPTION,
        textual=("The Sun is auspicious in the 11th, 3rd, 10th and 6th from "
                 "the Moon, if the corresponding 5th, 9th, 4th and 12th are "
                 "not marred by the transit of any graha other than Saturn."),
    ),
    # 26.4  dyUna-janma-ripu-lAbha-kha-tri-gaH chandramAH shubhaphalapradaH |
    #       sva-Atmaja-antya-mR^iti-bandhu-dharma-gaiH vidhyate na vibudhaiH
    _moon_rule(
        "Chandra", (7, 1, 6, 11, 10, 3), (2, 5, 12, 8, 4, 9),
        exempt=("Budha",), exemption_reason=_MOON_MERCURY_EXEMPTION,
        textual=("The Moon gives good effect in the 7th, 1st, 6th, 11th, "
                 "10th and 3rd, if grahas other than Mercury do not transit "
                 "the corresponding 2nd, 5th, 12th, 8th, 4th and 9th."),
    ),
    # 26.5  vikrama-Aya-ripu-gaH kujaH shubhaH syAt tad antya-suta-dharma-gaiH
    _moon_rule(
        "Mangal", (3, 11, 6), (12, 5, 9),
        textual=("Mars in the 3rd, 11th and 6th gives good effect if the "
                 "12th, 5th and 9th respectively are free of transiting "
                 "grahas."),
        notes=("No exemption is stated for Mars. The Sun/Saturn and "
               "Moon/Mercury exemptions are not generalised to it."),
    ),
    # 26.6  sva-ambu-shatru-mR^iti-kha-Aya-gaH shubho j~naH ...
    #       ... vividhubhir yadi grahaiH
    _moon_rule(
        "Budha", (2, 4, 6, 8, 10, 11), (5, 3, 9, 1, 8, 12),
        exempt=("Chandra",), exemption_reason=_MOON_MERCURY_EXEMPTION,
        textual=("Mercury is auspicious in the 2nd, 4th, 6th, 8th, 10th and "
                 "11th, provided the corresponding 5th, 3rd, 9th, 1st, 8th "
                 "and 12th are not occupied by any graha other than the "
                 "Moon."),
        notes=("The 8th is both a favourable house for Mercury and the "
               "vedha house for its 10th. That is in both witnesses and is "
               "not a transcription slip — Venus's table has four such "
               "overlaps. The ITRANS witness ends this list with `prApti`, "
               "the 11th, which would pair the 11th with itself; the "
               "reading is rejected on internal grounds and the second "
               "edition supplies the 12th."),
    ),
    # 26.7  sva-Aya-dharma-tanaya-Asta-saMsthito nAkanAyakapurohitaH shubhaH |
    #       riHpha-randhra-kha-jala-tri-gair yadA vidhyate ... na hi
    _moon_rule(
        "Guru", (2, 11, 9, 5, 7), (12, 8, 10, 4, 3),
        textual=("Jupiter is good transiting the 2nd, 11th, 9th, 5th and "
                 "7th if the corresponding 12th, 8th, 10th, 4th and 3rd are "
                 "void of grahas."),
    ),
    # 26.8  A-sutA-aShTama-tapo-vyaya-Aya-go viddha Asphujid ashobhanaH |
    #       naidhana-Asta-tanu-karma-dharma-dhI-lAbha-(v)ari-sahaja-sthaiH
    _moon_rule(
        "Shukra", (1, 2, 3, 4, 5, 8, 9, 12, 11),
        (8, 7, 1, 10, 9, 5, 11, 6, 3),
        textual=("Venus transiting the 1st, 2nd, 3rd, 4th, 5th, 8th, 9th, "
                 "12th and 11th is spoilt if marred by grahas in the "
                 "corresponding 8th, 7th, 1st, 10th, 9th, 5th, 11th, 6th "
                 "and 3rd."),
        notes=("26.2 states Venus's favourable houses by exclusion — "
               "`khāstaripūn vihāya`, leaving aside the 10th, 7th and 6th — "
               "and 26.8 enumerates the remaining nine. The two agree, "
               "including 26.8's unusual ordering of the 12th before the "
               "11th, which is preserved because the vedha pairing depends "
               "on it. The ITRANS witness reads `vari` (the 4th) where the "
               "pairing requires `ari` (the 6th); the second edition gives "
               "the 6th."),
    ),
    # 26.5, second half: inasUnur apy asau — "Saturn also", same houses.
    _moon_rule(
        "Shani", (3, 11, 6), (12, 5, 9),
        exempt=("Surya",), exemption_reason=_SUN_SATURN_EXEMPTION,
        textual=("The same as Mars — the 3rd, 11th and 6th, with vedha from "
                 "the 12th, 5th and 9th — except that the Sun's transit of "
                 "those houses does not mar the effect."),
    ),
)


# ── The nodes: stated in verse 2, absent from verses 3-8 ────────────────────
#
# Part 4: "Do not invent symmetric Vedha rules unless sourced." This is the
# case that clause exists for. 26.2 closes `tigmāṃśuvad bhoginau` — the two
# serpents behave as the Sun — which gives Rahu and Ketu the Sun's four
# favourable houses. Neither witness gives them a vedha table, and neither
# says whether the Sun's Saturn exemption travels with the houses.
#
# Copying the Sun's vedha row across would be a one-line change, would look
# entirely reasonable, and would be an invention. So the nodes get their
# favourable houses, an empty vedha table, and a status that keeps them out
# of strict synthesis until a witness for the missing half is found.

NODE_RULES: tuple[GocharaRule, ...] = tuple(
    GocharaRule(
        planet=planet,
        reference_frame=TransitReference.MOON,
        favourable_houses=(11, 3, 10, 6),
        unfavourable_houses=(),
        vedha_pairs={},
        vedha_exempt_planets=(),
        source_ref_ids=_MOON_SOURCES,
        validation_status="RULE_INTERPRETATION_MAPPED",
        witness_agreement=WitnessAgreement.SAME_WORK_SECOND_EDITION,
        methodology_profile=GOCHARA_PROFILE,
        rule_id=RULE_MOON_FRAME,
        textual_condition=(
            "26.2 `tigmāṃśuvad bhoginau` — Rāhu and Ketu give results as "
            "the Sun does, which carries the Sun's favourable houses to "
            "them. No vedha houses are stated for either node, in either "
            "witness."),
        software_condition=(
            f"{planet}'s house from the natal Chandra is in [11, 3, 10, 6]. "
            f"No vedha is evaluated, because none is stated."),
        notes=(
            "Favourable houses located; vedha layer absent from the source. "
            "The Sun's vedha row is NOT copied across: 26.2 transfers the "
            "RESULTS, and whether it transfers the obstructions is exactly "
            "the question the text leaves open. Barred from strict "
            "synthesis for the missing layer, not for the missing evidence."),
    )
    for planet in ("Rahu", "Ketu")
)


# ── Phaladīpikā 20.34-35, the daśā-lord rule ────────────────────────────────
#
# A different rule in a different frame, and the reason Part 2 insists every
# rule declare its frame. Chapter 26 counts from the Moon. This counts
# `vilagnāt`, from the Lagna, and both witnesses say so.

DASHA_LORD_RULE = GocharaRule(
    planet="*",
    reference_frame=TransitReference.LAGNA,
    favourable_houses=(),
    unfavourable_houses=(),
    vedha_pairs={},
    vedha_exempt_planets=(),
    source_ref_ids=_LAGNA_SOURCES,
    validation_status="IMPLEMENTATION_MATCHED",
    witness_agreement=WitnessAgreement.SAME_WORK_SECOND_EDITION,
    methodology_profile=GOCHARA_PROFILE,
    rule_id=RULE_DASHA_LORD,
    textual_condition=(
        "20.34: the lord of the daśā in progress, transiting its own sign, "
        "its exaltation or a friend's house, nourishes the bhāva it reaches "
        "counted from the Lagna — PROVIDED it was also endowed with "
        "strength at birth. "
        "20.35: if that same lord was weak at birth, or combust, "
        "debilitated or in an enemy's house at birth, then whichever bhāva "
        "it reaches in transit it destroys. The destructive form carries no "
        "condition on the transited sign."),
    software_condition=(
        "The transiting graha is the lord of the running mahādaśā, "
        "antardaśā or pratyantardaśā as computed by "
        "engine.timing.vimshottari. Its transited rashi is tested for own "
        "sign / exaltation / natural friendship by engine.features.dignity "
        "and engine.features.relationships. Its natal strength is read from "
        "the existing Shadbala result. The affected bhāva is its house from "
        "the natal Lagna."),
    notes=(
        "Natal → Daśā → Transit, stated in a text. V1.5 built that "
        "hierarchy as a software convention and said so; this is the "
        "witness that it is also Mantreśvara's. "
        "Note what the rule does NOT license: it says nothing about grahas "
        "that are not the running daśā lord, which is most of them at any "
        "moment, and nothing about transits over natal points. Those remain "
        "engine conventions."),
)


# ── Located and deliberately not implemented ────────────────────────────────

UNIMPLEMENTED_LAYERS: tuple[dict, ...] = (
    {
        "locator": "Phaladīpikā 26.9-24",
        "subject": "per-graha per-house transit effects",
        "why_not": (
            "Prose effects — `sthānaprāpti` in the 3rd, `vittakṣaya` in the "
            "2nd, `kalatrakalaha` in the 7th. Part 3 forbids turning house "
            "membership directly into prose, and paraphrasing 16 verses of "
            "effects into the engine's own words would produce exactly the "
            "second astrology engine the brief forbids."),
        "source_ref_ids": [PD_26_GOCHARA.id],
    },
    {
        "locator": "Phaladīpikā 26.25",
        "subject": "which third of a rashi each graha gives results in",
        "why_not": (
            "A timing refinement within a sign. Implementable, and it would "
            "narrow the windows the transit scanner reports; deferred "
            "because it changes event timing and V1.8 froze the golden "
            "events."),
        "source_ref_ids": [PD_26_GOCHARA.id],
    },
    {
        "locator": "Phaladīpikā 26.26-48",
        "subject": "nakṣatra gochara, latta and the sarvatobhadra cakra",
        "why_not": (
            "A separate transit system on the 27 asterisms, not a "
            "refinement of the rashi one. Locating it is not the same as "
            "being ready to implement it."),
        "source_ref_ids": [PD_26_GOCHARA.id],
    },
    {
        "locator": "Phaladīpikā 26.41 / BPHS 66",
        "subject": "ashtakavarga bindus in the transited sign",
        "why_not": (
            "A third, independent transit method. The engine computes the "
            "bindu arithmetic and does not apply it to transits; joining "
            "them needs its own audit, not an assumption that two "
            "implemented halves make an implemented rule."),
        "source_ref_ids": [PD_26_GOCHARA.id, "BPHS_66_ASHTAKAVARGA"],
    },
    {
        "locator": "Phaladīpikā 20.36",
        "subject": "the Moon's transit relative to the daśā lord",
        "why_not": (
            "Located and readable — the Moon in the daśā lord's exaltation, "
            "friendly sign, 3rd, 6th, 10th, 11th, trine or 7th gives happy "
            "effects. Not implemented because its output is a general "
            "quality with no bhāva attached, so it could not reach a domain "
            "even if implemented. Recorded so the omission is visible."),
        "source_ref_ids": [PD_20_GOCHARA_FROM_LAGNA.id, PD_EN_20_SASTRI.id],
    },
)


# ── lookup ───────────────────────────────────────────────────────────────────

_BY_PLANET: dict[str, GocharaRule] = {
    rule.planet: rule for rule in MOON_FRAME_RULES + NODE_RULES}


def moon_frame_rule(planet: str):
    """The chapter-26 rule for one graha, or None if the text gives it none."""
    return _BY_PLANET.get(planet)


def all_rules() -> tuple[GocharaRule, ...]:
    return MOON_FRAME_RULES + NODE_RULES + (DASHA_LORD_RULE,)


def rule_summary() -> dict:
    """What the rule layer contains, for the snapshot and the report."""
    return {
        "methodology_id": METHODOLOGY_ID,
        "profile": GOCHARA_PROFILE,
        "reference_frames": sorted(
            {r.reference_frame.value for r in all_rules()}),
        "rules": [r.to_dict() for r in all_rules()],
        "grahas_with_vedha_table": sorted(
            r.planet for r in all_rules() if r.vedha_pairs),
        "grahas_without_vedha_table": sorted(
            r.planet for r in all_rules()
            if not r.vedha_pairs and r.planet != "*"),
        "vedha_pair_count": sum(len(r.vedha_pairs) for r in all_rules()),
        "located_and_unimplemented": [dict(item)
                                      for item in UNIMPLEMENTED_LAYERS],
    }
