"""
Gochara (V1.8 Parts 1-7)
--------------------------
The transit rules, tested against the verses rather than against themselves.

WHAT THE TABLE TESTS ARE FOR

    `MoonFrameTableTest` asserts each row of Phaladīpikā 26.3-8 as a
    literal. That is deliberately dumb: the value of the assertion is that
    a human with the verse can check it in a minute, which is not true of a
    test that recomputes the table from the same data the table came from.

    The literals below were established from TWO witnesses, and the two
    disagree in exactly two places. Both disagreements are encoded as
    tests, so a future edit that quietly restores the corrupt reading
    fails here with the reason attached.

THE TEST THAT MATTERS MOST

    `StrictEligibilityTest`. Part 7: "A located source alone is NOT
    permission." Three releases refused transits on that principle, and the
    release that finally admits one is the release where the principle is
    easiest to quietly drop.
"""

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.gochara import (
    DASHA_LORD_RULE, GocharaVerdict, MOON_FRAME_RULES, NODE_RULES,
    NODES_CAUSE_VEDHA_DEFAULT, RULE_DASHA_LORD, RULE_MOON_FRAME,
    STRENGTH_THRESHOLD, TransitReference, WitnessAgreement, all_rules,
    evaluate_gochara, evaluate_moon_frame, evaluate_vedha, moon_frame_rule,
    rule_summary, strict_eligible_judgements, vedha_table,
)
from engine.gochara.models import GocharaRule
from engine.planets import JyotishChart, jde_from_datetime
from engine.sources.registry import conflict_by_id, evidence_for
from engine.strength import compute_shadbala
from engine.synthesis import SynthesisProfile, synthesise
from engine.timing.vimshottari import from_chart
from engine.transits import get_transit_snapshot

# The documented worked example, so the gochara results below are about a
# chart every other suite already pins.
BIRTH_LOCAL = datetime.datetime(1988, 8, 30, 20, 18)
BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)

_STATE: dict = {}


def setUpModule():
    chart = JyotishChart(
        jde=jde_from_datetime(BIRTH_UTC), lat=26.9124, lon=75.7873,
        ayanamsha_system="lahiri", true_node=True)
    features = build_chart_features(chart)
    # 20.34's natal-strength condition reads Shadbala, so it has to be
    # attached or every judgement would report the condition unmeasurable
    # and the rule would appear never to fire.
    features.shadbala = compute_shadbala(chart, features, birth=BIRTH_UTC)
    _STATE["chart"] = chart
    _STATE["features"] = features
    _STATE["dasha"] = from_chart(chart, BIRTH_UTC)


# ── Parts 3 and 4: the tables, against the verses ───────────────────────────

class MoonFrameTableTest(unittest.TestCase):
    """
    Phaladīpikā 26.3-8, transcribed. Each expected pair below is
    (favourable house, vedha house) IN THE VERSE'S ORDER.
    """

    # 26.3 Sun; 26.4 Moon; 26.5 Mars and Saturn; 26.6 Mercury;
    # 26.7 Jupiter; 26.8 Venus.
    EXPECTED = {
        "Surya": ((11, 5), (3, 9), (10, 4), (6, 12)),
        "Chandra": ((7, 2), (1, 5), (6, 12), (11, 8), (10, 4), (3, 9)),
        "Mangal": ((3, 12), (11, 5), (6, 9)),
        "Budha": ((2, 5), (4, 3), (6, 9), (8, 1), (10, 8), (11, 12)),
        "Guru": ((2, 12), (11, 8), (9, 10), (5, 4), (7, 3)),
        "Shukra": ((1, 8), (2, 7), (3, 1), (4, 10), (5, 9), (8, 5),
                   (9, 11), (12, 6), (11, 3)),
        "Shani": ((3, 12), (11, 5), (6, 9)),
    }

    def test_every_row_matches_the_verse(self):
        for planet, pairs in self.EXPECTED.items():
            with self.subTest(planet=planet):
                rule = moon_frame_rule(planet)
                self.assertEqual(rule.favourable_houses,
                                 tuple(h for h, _ in pairs))
                self.assertEqual(
                    tuple((h, rule.vedha_pairs[h])
                          for h in rule.favourable_houses),
                    pairs)

    def test_every_graha_is_favourable_in_the_eleventh(self):
        """26.2 `sarve 'py upāntasthitāḥ` — all grahas, the 11th."""
        for rule in MOON_FRAME_RULES + NODE_RULES:
            with self.subTest(planet=rule.planet):
                self.assertIn(11, rule.favourable_houses)

    def test_the_two_exemptions_are_reciprocal_and_no_others_exist(self):
        """
        26.3/26.5 exempt Saturn against the Sun and the Sun against Saturn;
        26.4/26.6 exempt Mercury against the Moon and the Moon against
        Mercury. Part 4 forbids inventing symmetric rules, so the test
        pins that these four and only these four are encoded.
        """
        exemptions = {rule.planet: rule.vedha_exempt_planets
                      for rule in MOON_FRAME_RULES}
        self.assertEqual(exemptions["Surya"], ("Shani",))
        self.assertEqual(exemptions["Shani"], ("Surya",))
        self.assertEqual(exemptions["Chandra"], ("Budha",))
        self.assertEqual(exemptions["Budha"], ("Chandra",))
        for planet in ("Mangal", "Guru", "Shukra"):
            self.assertEqual(exemptions[planet], ())

    def test_mars_and_saturn_share_houses_but_not_exemptions(self):
        """
        26.5 gives Saturn the same houses as Mars and then adds an
        exemption Mars does not have. Copying the row wholesale would have
        lost that.
        """
        mars, saturn = moon_frame_rule("Mangal"), moon_frame_rule("Shani")
        self.assertEqual(mars.favourable_houses, saturn.favourable_houses)
        self.assertEqual(dict(mars.vedha_pairs), dict(saturn.vedha_pairs))
        self.assertNotEqual(mars.vedha_exempt_planets,
                            saturn.vedha_exempt_planets)

    def test_a_row_whose_lists_differ_in_length_is_rejected(self):
        """
        The verse pairs the lists positionally, so unequal lengths mean a
        misread verse rather than a shorter rule.
        """
        from engine.gochara.rules import _moon_rule

        with self.assertRaises(ValueError):
            _moon_rule("Surya", (11, 3, 10, 6), (5, 9, 4))


class CorruptReadingTest(unittest.TestCase):
    """
    The two places the digital witness is wrong, pinned so that a future
    edit restoring either has to argue with the reason.
    """

    def test_mercury_s_last_vedha_is_the_twelfth_not_the_eleventh(self):
        """
        The ITRANS text reads `prApti`, the 11th. That would pair the 11th
        with itself — asserting Mercury's transit of the 11th is obstructed
        by a graha standing where Mercury already stands — so the reading is
        self-refuting before any second witness is consulted.
        """
        rule = moon_frame_rule("Budha")
        self.assertEqual(rule.vedha_pairs[11], 12)
        self.assertNotEqual(rule.vedha_pairs[11], 11)

    def test_no_graha_is_ever_its_own_vedha_house(self):
        """The general form of the check that caught the corrupt reading."""
        for rule in all_rules():
            for house, vedha in rule.vedha_pairs.items():
                with self.subTest(planet=rule.planet, house=house):
                    self.assertNotEqual(house, vedha)

    def test_venus_eighth_vedha_is_the_sixth(self):
        """ITRANS `vari` (4th) against the printed edition's `ari` (6th)."""
        self.assertEqual(moon_frame_rule("Shukra").vedha_pairs[12], 6)

    def test_the_variant_is_registered_and_resolved(self):
        conflict = conflict_by_id("GOCHARA_MERCURY_VEDHA_READING")
        self.assertTrue(conflict.resolution_status.startswith("RESOLVED"))
        self.assertIn("self-refuting", conflict.resolution_note)

    def test_the_second_edition_is_not_claimed_as_independent(self):
        """
        Part 10. Two editions of Phaladīpikā are the same work speaking
        twice. They settle a reading; they do not corroborate doctrine.
        """
        for rule in all_rules():
            with self.subTest(planet=rule.planet):
                self.assertIs(rule.witness_agreement,
                              WitnessAgreement.SAME_WORK_SECOND_EDITION)
                self.assertFalse(rule.witness_agreement.is_independent)


class NodeRuleTest(unittest.TestCase):
    """Part 4: "Do not invent symmetric Vedha rules unless sourced.\""""

    def test_the_nodes_take_the_suns_favourable_houses(self):
        """26.2 `tigmāṃśuvad bhoginau`."""
        sun = moon_frame_rule("Surya")
        for planet in ("Rahu", "Ketu"):
            with self.subTest(planet=planet):
                self.assertEqual(moon_frame_rule(planet).favourable_houses,
                                 sun.favourable_houses)

    def test_the_nodes_have_no_vedha_table(self):
        """
        The Sun's vedha row is one line away and is not copied. Neither
        witness gives the nodes one, and 26.2 transfers the RESULTS — that
        it also transfers the obstructions is exactly what is not stated.
        """
        for planet in ("Rahu", "Ketu"):
            with self.subTest(planet=planet):
                self.assertEqual(moon_frame_rule(planet).vedha_pairs, {})
                self.assertEqual(
                    moon_frame_rule(planet).vedha_exempt_planets, ())


# ── Part 4: vedha as a layer ────────────────────────────────────────────────

class VedhaTest(unittest.TestCase):

    def setUp(self):
        self.sun = moon_frame_rule("Surya")

    def test_an_empty_vedha_house_does_not_obstruct(self):
        result = evaluate_vedha(self.sun, 11, {"Guru": 3, "Shani": 7})
        self.assertFalse(result.blocking_condition_present)
        self.assertEqual(result.vedha_house, 5)
        self.assertIsNone(result.exception_applied)

    def test_an_occupied_vedha_house_obstructs_and_names_the_graha(self):
        result = evaluate_vedha(self.sun, 11, {"Guru": 5})
        self.assertTrue(result.blocking_condition_present)
        self.assertEqual(result.blocking_planet, "Guru")
        self.assertEqual(result.vedha_house, 5)

    def test_the_exempt_graha_does_not_obstruct_and_says_why(self):
        """
        Saturn in the Sun's vedha house produces "not obstructed" for a
        reason that has to survive into the record. A boolean could not
        carry it, which is why Part 4 asks for an object.
        """
        result = evaluate_vedha(self.sun, 11, {"Shani": 5})
        self.assertFalse(result.blocking_condition_present)
        self.assertEqual(result.exempted_planets, ("Shani",))
        self.assertIn("father and son", result.exception_applied)

    def test_an_exempt_and_a_blocking_graha_together_still_obstruct(self):
        result = evaluate_vedha(self.sun, 11, {"Shani": 5, "Mangal": 5})
        self.assertTrue(result.blocking_condition_present)
        self.assertEqual(result.blocking_planets, ("Mangal",))
        self.assertIsNone(result.exception_applied)

    def test_the_exemption_does_not_generalise_to_other_grahas(self):
        """Mercury is exempt against the Moon, not against the Sun."""
        result = evaluate_vedha(self.sun, 11, {"Budha": 5})
        self.assertTrue(result.blocking_condition_present)

    def test_the_node_decision_is_a_parameter_not_a_membership_test(self):
        on = evaluate_vedha(self.sun, 11, {"Rahu": 5},
                            nodes_cause_vedha=True)
        off = evaluate_vedha(self.sun, 11, {"Rahu": 5},
                             nodes_cause_vedha=False)
        self.assertTrue(on.blocking_condition_present)
        self.assertFalse(off.blocking_condition_present)
        self.assertTrue(NODES_CAUSE_VEDHA_DEFAULT)

    def test_a_graha_without_a_stated_vedha_house_is_not_obstructed(self):
        result = evaluate_vedha(moon_frame_rule("Rahu"), 11, {"Guru": 5})
        self.assertIsNone(result.vedha_house)
        self.assertFalse(result.blocking_condition_present)


# ── Part 2: frames ──────────────────────────────────────────────────────────

class ReferenceFrameTest(unittest.TestCase):

    def test_every_rule_declares_a_frame(self):
        for rule in all_rules():
            with self.subTest(planet=rule.planet):
                self.assertIsInstance(rule.reference_frame, TransitReference)

    def test_the_two_rules_use_different_frames(self):
        """
        Chapter 26 counts from the Moon and 20.34 `vilagnāt` from the
        Lagna. Evaluating either in the other's frame would produce
        confident wrong answers, because both frames yield 1-12.
        """
        self.assertIs(MOON_FRAME_RULES[0].reference_frame,
                      TransitReference.MOON)
        self.assertIs(DASHA_LORD_RULE.reference_frame,
                      TransitReference.LAGNA)

    def test_the_moon_frame_is_evaluated_against_the_moon(self):
        snapshot = get_transit_snapshot(
            datetime.datetime(2026, 9, 27, 12), natal_chart=_STATE["chart"])
        for judgement in evaluate_moon_frame(snapshot):
            with self.subTest(planet=judgement.transit_planet):
                position = snapshot.positions[judgement.transit_planet]
                self.assertEqual(judgement.placement.house,
                                 position.house_from_natal_moon)


# ── Parts 5 and 6: the dasha-lord rule ──────────────────────────────────────

class DashaLordRuleTest(unittest.TestCase):

    def _at(self, when):
        snapshot = get_transit_snapshot(when, natal_chart=_STATE["chart"])
        stack = _STATE["dasha"].get_dasha_stack_at(when)
        return evaluate_gochara(snapshot, _STATE["features"],
                                dasha_stack=stack), stack

    def test_only_the_running_dasha_lords_are_judged(self):
        """
        20.34-35's subject is the daśā lord, not every transiting graha.
        Most grahas at any moment are outside the rule entirely.
        """
        result, stack = self._at(datetime.datetime(2011, 6, 15, 12))
        lords = {stack[level] for level in
                 ("mahadasha", "antardasha", "pratyantardasha")}
        judged = {j.transit_planet for j in result.for_rule(RULE_DASHA_LORD)}
        self.assertTrue(judged)
        self.assertTrue(judged <= lords)

    def test_no_dasha_means_the_rule_is_not_evaluated_at_all(self):
        snapshot = get_transit_snapshot(
            datetime.datetime(2011, 6, 15, 12), natal_chart=_STATE["chart"])
        result = evaluate_gochara(snapshot, _STATE["features"],
                                  dasha_stack=None)
        self.assertEqual(result.for_rule(RULE_DASHA_LORD), [])
        self.assertTrue(any("dasha lord" in note for note in result.notes))

    def test_the_rule_reaches_both_verdicts_over_a_lifetime(self):
        """
        A gate that never opens is not an implementation, and a gate that
        only ever opens one way is not this rule: 20.34 nourishes and 20.35
        destroys.
        """
        seen = set()
        for year in range(1989, 2061, 2):
            result, _ = self._at(datetime.datetime(year, 6, 15, 12))
            seen |= {j.verdict for j in result.for_rule(RULE_DASHA_LORD)}
        self.assertIn(GocharaVerdict.FAVOURABLE, seen)
        self.assertIn(GocharaVerdict.UNFAVOURABLE, seen)

    def test_the_destructive_form_needs_no_transit_dignity(self):
        """
        20.35 carries no condition on the transited sign — a daśā lord
        afflicted at birth damages whichever bhāva it reaches. The
        asymmetry is in both witnesses and is implemented as stated.
        """
        for year in range(1989, 2061, 2):
            result, _ = self._at(datetime.datetime(year, 6, 15, 12))
            for judgement in result.for_rule(RULE_DASHA_LORD):
                if judgement.verdict is not GocharaVerdict.UNFAVOURABLE:
                    continue
                with self.subTest(year=year, planet=judgement.transit_planet):
                    strength = judgement.natal_strength
                    self.assertTrue(strength.afflictions
                                    or strength.satisfied is False)
                return
        self.fail("no unfavourable judgement was produced to inspect")

    def test_the_textual_condition_and_its_software_reading_stay_apart(self):
        """
        Part 6: the verse says `balānvita` and names no number. The
        substitution has to be visible wherever the evidence is read, not
        collapsed into a boolean.
        """
        result, _ = self._at(datetime.datetime(2011, 6, 15, 12))
        judgements = result.for_rule(RULE_DASHA_LORD)
        self.assertTrue(judgements)
        for judgement in judgements:
            strength = judgement.natal_strength
            with self.subTest(planet=judgement.transit_planet):
                self.assertIn("balānvita", strength.textual_qualification)
                self.assertIn("BPHS 27", strength.software_interpretation)
                self.assertNotEqual(strength.measure_source_ref_ids,
                                    strength.rule_source_ref_ids)

    def test_the_strength_measure_is_reused_not_reinvented(self):
        """Part 6: "Do NOT invent a new strength calculation.\""""
        result, _ = self._at(datetime.datetime(2011, 6, 15, 12))
        for judgement in result.for_rule(RULE_DASHA_LORD):
            strength = judgement.natal_strength
            if strength.measured_value is None:
                continue
            with self.subTest(planet=judgement.transit_planet):
                self.assertEqual(
                    strength.measured_value,
                    round(_STATE["features"].shadbala_ratio(
                        judgement.transit_planet), 3))
                self.assertEqual(strength.threshold, STRENGTH_THRESHOLD)

    def test_an_unmeasurable_strength_is_not_a_failed_condition(self):
        """
        The nodes have no Shadbala. `satisfied is None` must not be read as
        False: a condition that could not be evaluated has not been passed
        OR failed, and either reading would be a claim.
        """
        result, _ = self._at(datetime.datetime(2026, 9, 27, 12))
        for judgement in result.for_rule(RULE_DASHA_LORD):
            if judgement.transit_planet not in ("Rahu", "Ketu"):
                continue
            with self.subTest(planet=judgement.transit_planet):
                self.assertIsNone(judgement.natal_strength.satisfied)
                self.assertIs(judgement.verdict, GocharaVerdict.NOT_STATED)
                self.assertFalse(judgement.strict_eligible)


# ── Part 7: the gate ────────────────────────────────────────────────────────

class StrictEligibilityTest(unittest.TestCase):
    """
    The load-bearing test Part 7 asks for.

    "A located source alone is NOT permission." Both rules are located,
    both reach IMPLEMENTATION_MATCHED, and only one of them may carry a
    strict prediction.
    """

    def setUp(self):
        when = datetime.datetime(2011, 6, 15, 12)
        snapshot = get_transit_snapshot(when, natal_chart=_STATE["chart"])
        self.result = evaluate_gochara(
            snapshot, _STATE["features"],
            dasha_stack=_STATE["dasha"].get_dasha_stack_at(when))

    def test_chapter_26_is_implemented_and_still_cannot_reach_a_domain(self):
        """
        The chapter judges the transit in the Chandra's frame and names no
        bhāva. The engine's bhāva significations are stated from the Lagna,
        so there is no sourced path from this verdict to a life area —
        which is a statement about the SOURCE, not about the code.
        """
        judgements = self.result.for_rule(RULE_MOON_FRAME)
        self.assertTrue(judgements)
        for judgement in judgements:
            with self.subTest(planet=judgement.transit_planet):
                self.assertEqual(judgement.houses_affected, ())
                self.assertFalse(judgement.attributes_to_houses)
                self.assertFalse(judgement.strict_eligible)
                self.assertTrue(judgement.not_strict_because)

    def test_chapter_26_reaches_implementation_matched_anyway(self):
        """Being unusable in strict is not the same as being unproven."""
        evidence = evidence_for("gochara/vedha_from_moon", kind="calculation")
        self.assertEqual(evidence.validation_status.value,
                         "IMPLEMENTATION_MATCHED")

    def test_only_the_dasha_lord_rule_is_strict_eligible(self):
        eligible = strict_eligible_judgements(self.result)
        self.assertTrue(eligible)
        for judgement in eligible:
            with self.subTest(planet=judgement.transit_planet):
                self.assertEqual(judgement.rule_id, RULE_DASHA_LORD)
                self.assertTrue(judgement.houses_affected)
                self.assertIsNot(judgement.verdict, GocharaVerdict.NOT_STATED)

    def test_a_not_stated_verdict_never_becomes_evidence(self):
        for judgement in strict_eligible_judgements(self.result):
            self.assertIsNot(judgement.verdict, GocharaVerdict.NOT_STATED)

    def test_provenance_of_every_layer_survives_into_the_judgement(self):
        """
        Part 1: "Do not allow a later rule to erase the provenance of an
        earlier condition." An obstructed transit still carries the
        placement that was obstructed.
        """
        obstructed = [j for j in self.result.for_rule(RULE_MOON_FRAME)
                      if j.verdict is GocharaVerdict.OBSTRUCTED]
        self.assertTrue(obstructed, "expected at least one obstruction")
        for judgement in obstructed:
            with self.subTest(planet=judgement.transit_planet):
                self.assertIsNotNone(judgement.placement)
                self.assertTrue(judgement.placement.favourable)
                self.assertIsNotNone(judgement.vedha)
                self.assertTrue(judgement.vedha.blocking_condition_present)

    def test_an_obstructed_transit_is_not_an_unfavourable_one(self):
        """
        The verses say vedha cancels an auspicious result. They do not say
        it produces an evil one, and merging the two would be this
        engine's doctrine rather than Mantreśvara's.
        """
        verdicts = {j.verdict for j in self.result.for_rule(RULE_MOON_FRAME)}
        self.assertNotIn(GocharaVerdict.UNFAVOURABLE, verdicts)

    def test_a_house_outside_the_favourable_list_is_not_declared_evil(self):
        for judgement in self.result.for_rule(RULE_MOON_FRAME):
            if judgement.placement.favourable:
                continue
            with self.subTest(planet=judgement.transit_planet):
                self.assertIs(judgement.verdict, GocharaVerdict.NOT_STATED)

    def test_the_chapter_26_rules_declare_no_unfavourable_houses(self):
        """
        26.3-8 state which houses are favourable and do not declare the
        rest unfavourable. Venus is favourable in nine of twelve; reading
        the other three as evil would be an inference the text does not
        make.
        """
        for rule in MOON_FRAME_RULES + NODE_RULES:
            with self.subTest(planet=rule.planet):
                self.assertEqual(rule.unfavourable_houses, ())


class StrictSynthesisTest(unittest.TestCase):
    """
    The end-to-end consequence: for the first time, strict synthesis
    admits transit evidence — and admits it only from the qualified rule.
    """

    def _synthesise(self, when, profile):
        return synthesise(
            _STATE["features"], moment=when, dasha=_STATE["dasha"],
            transit_snapshot=get_transit_snapshot(
                when, natal_chart=_STATE["chart"]),
            profile=profile)

    def test_strict_now_admits_sourced_transit_evidence(self):
        context = self._synthesise(datetime.datetime(2011, 6, 15, 12),
                                   SynthesisProfile.STRICT)
        items = [item for result in context.results.values()
                 for item in result.transit_evidence]
        self.assertTrue(items, "strict should admit the dasha-lord rule")
        for item in items:
            with self.subTest(domain=item.domain):
                self.assertEqual(item.source_type, "gochara_rule")
                self.assertIn("PD_SA_20.34-37_DASHESHA_GOCHARA",
                              item.source_ref_ids)

    def test_strict_transit_evidence_only_reaches_sourced_houses(self):
        """
        The third gate. A located transit rule plus an unsourced
        house→domain mapping is not a sourced claim about that domain.
        """
        from engine.synthesis.domain_evidence import FactorType
        from engine.synthesis.domains import spec_for

        context = self._synthesise(datetime.datetime(2011, 6, 15, 12),
                                   SynthesisProfile.STRICT)
        for name, result in context.results.items():
            spec = spec_for(name)
            for item in result.transit_evidence:
                for house in item.houses:
                    with self.subTest(domain=name, house=house):
                        self.assertTrue(spec.qualifies_for_strict(
                            FactorType.HOUSE, house))

    def test_strict_still_admits_none_of_the_geometric_transit_evidence(self):
        """
        The V1.5-V1.7 relationships — a graha over a natal house, conjunct
        a natal point, aspecting one — remain engine conventions and remain
        out. Admitting the sourced rule did not open the door generally.
        """
        context = self._synthesise(datetime.datetime(2011, 6, 15, 12),
                                   SynthesisProfile.STRICT)
        for result in context.results.values():
            for item in result.transit_evidence:
                self.assertNotEqual(item.source_type, "transit")

    def test_standard_is_unchanged_by_the_gochara_layer(self):
        """
        The standard profile's transit evidence is the geometric layer it
        has always been. Adding a sourced rule must not silently re-weight
        the profile that never claimed a source.
        """
        context = self._synthesise(datetime.datetime(2011, 6, 15, 12),
                                   SynthesisProfile.STANDARD)
        kinds = {item.source_type for result in context.results.values()
                 for item in result.transit_evidence}
        self.assertEqual(kinds, {"transit"})

    def test_the_gochara_layer_is_computed_once_per_run(self):
        context = self._synthesise(datetime.datetime(2011, 6, 15, 12),
                                   SynthesisProfile.STRICT)
        self.assertIsNotNone(context.gochara)
        self.assertIn("gochara", context.to_dict())

    def test_synthesis_is_still_deterministic(self):
        when = datetime.datetime(2011, 6, 15, 12)
        first = self._synthesise(when, SynthesisProfile.STRICT).to_dict()
        second = self._synthesise(when, SynthesisProfile.STRICT).to_dict()
        self.assertEqual(first, second)


# ── the located-and-unimplemented record ────────────────────────────────────

class UnimplementedLayersTest(unittest.TestCase):

    def test_every_unimplemented_layer_says_why_and_cites(self):
        from engine.gochara import UNIMPLEMENTED_LAYERS

        self.assertTrue(UNIMPLEMENTED_LAYERS)
        for item in UNIMPLEMENTED_LAYERS:
            with self.subTest(locator=item["locator"]):
                self.assertTrue(item["why_not"].strip())
                self.assertTrue(item["source_ref_ids"])

    def test_the_per_house_effects_are_recorded_as_not_implemented(self):
        """
        Part 3: "Do not turn house membership directly into prose."
        26.9-24 is where prose would have come from, and the omission is
        recorded rather than left to be noticed.
        """
        from engine.gochara import UNIMPLEMENTED_LAYERS

        locators = {item["locator"] for item in UNIMPLEMENTED_LAYERS}
        self.assertIn("Phaladīpikā 26.9-24", locators)

    def test_the_rule_summary_reports_both_halves(self):
        summary = rule_summary()
        self.assertEqual(summary["vedha_pair_count"], 36)
        self.assertEqual(summary["grahas_without_vedha_table"],
                         ["Ketu", "Rahu"])
        self.assertTrue(summary["located_and_unimplemented"])

    def test_the_vedha_table_is_reportable(self):
        table = vedha_table()
        self.assertEqual(table["reference_frame"], "MOON")
        self.assertEqual(len(table["pairs"]["Shukra"]["favourable"]), 9)


if __name__ == "__main__":
    unittest.main()
