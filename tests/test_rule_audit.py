"""
The V1.5 rule audit, as tests (Parts 1, 2, 23)
------------------------------------------------
These pin the audit's FINDINGS, not merely that the code runs.

Two kinds of test live here and they are worth telling apart.

    The first kind asserts that a corrected rule behaves as the located
    witness says. Those are ordinary behavioural tests.

    The second kind asserts that a DIVERGENCE IS STILL RECORDED. Those look
    strange — a test that insists the engine still does something the text
    does not — and they are the more important of the two. V1.5 deliberately
    did not edit the diverging rules, so the only thing standing between a
    future release and a silent "fix" that loses the finding is a test
    saying the divergence is known and declared.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.features import build_chart_features, parashari_profile
from engine.rules import evaluate_rules, rules_for_profile
from engine.rules.catalog import TEXTUAL_PROFILE, rule_by_id
from engine.rules.catalog_textual import (
    SUPERSEDED_BY_TEXTUAL, MAHAPURUSHA_STRENGTH_RATIO, textual_rules,
)
from engine.sources import (
    ValidationStatus, conflict_by_id, evidence_for, witnesses_for,
)


# ── Part 1: the citation finding ─────────────────────────────────────────────

class CitationAuditTest(unittest.TestCase):
    """
    The headline result: the legacy citations did not identify passages.

    Each pair below is (rule id, the chapter its V1.1 citation named). The
    audit found the actual passage elsewhere in every case but one.
    """

    WRONG_CHAPTER = {
        "sunapha": ("34", "37.7"),
        "anapha": ("34", "37.7"),
        "durudhara": ("34", "37.7"),
        "kemadruma": ("34", "37.11"),
        "adhi_yoga": ("36", "37.5"),
        "gajakesari": ("34", "36.3"),
        "raja_yoga_k1_t5_conjunction": ("36", "34.11"),
    }

    def test_located_passage_is_not_the_cited_chapter(self):
        for rule_id, (cited, actual) in self.WRONG_CHAPTER.items():
            with self.subTest(rule=rule_id):
                rule = rule_by_id(rule_id)
                self.assertIsNotNone(rule)
                self.assertIn(
                    f"ch.{cited}", rule.source,
                    "the legacy citation string should still say what it "
                    "always said; it is evidence of what was claimed")
                witnesses = witnesses_for(rule_id)
                self.assertTrue(
                    witnesses, "V1.5 located a witness for this rule")
                located = {w.locator or "" for w in witnesses}
                self.assertTrue(
                    any(actual in loc for loc in located),
                    f"expected a witness at {actual}, got {sorted(located)}")

    def test_mahapurusha_citation_was_the_one_that_was_right(self):
        """
        Exactly one legacy citation named the correct chapter.

        Worth a test of its own because it is the counter-example that keeps
        the finding honest: the citations were not uniformly wrong, they were
        unchecked, and an unchecked citation is sometimes right.
        """
        rule = rule_by_id("mahapurusha_hamsa")
        self.assertIn("ch.75", rule.source)
        locators = {w.locator or "" for w in witnesses_for("mahapurusha_hamsa")}
        self.assertTrue(any("75.1" in loc for loc in locators), locators)


# ── Part 1: negative results ─────────────────────────────────────────────────

class NegativeResultTest(unittest.TestCase):
    """
    "We read the chapter and the rule is not in it" is a finding.

    It is recorded differently from "we never looked", and the difference is
    the reason `textual_summary` carries the words NEGATIVE RESULT.
    """

    ABSENT = ("dhana_yoga_h1_h2_conjunction", "dhana_yoga_2_11_placement",
              "chandra_mangala", "budha_aditya", "neecha_bhanga_guru")

    def test_read_and_absent_rules_carry_no_witness(self):
        for rule_id in self.ABSENT:
            with self.subTest(rule=rule_id):
                evidence = evidence_for(rule_id)
                self.assertIs(evidence.validation_status,
                              ValidationStatus.UNVERIFIED)
                self.assertFalse(evidence.witness_ids)
                self.assertIn("NEGATIVE RESULT", evidence.textual_summary)

    def test_dhana_yogas_were_reclassified_not_deleted(self):
        """
        BPHS ch.41 does not contain the engine's Dhana Yogas. All 30 stay.

        Deleting them would trade a known unknown for a silent gap, which is
        the reasoning V1.3 recorded for keeping unverified rules and it still
        applies. What changed is the classification.
        """
        dhana = [r for r in rules_for_profile("parashari")
                 if r.id.startswith("dhana_yoga_h")]
        self.assertEqual(len(dhana), 30)
        for rule in dhana:
            with self.subTest(rule=rule.id):
                self.assertEqual(
                    evidence_for(rule.id).classification.value,
                    "TRADITIONAL_MODERN_CONVENTION")

    def test_conflict_records_that_the_chapter_was_read(self):
        conflict = conflict_by_id("DHANA_YOGA_NOT_LOCATED")
        self.assertEqual(conflict.resolution_status, "UNRESOLVED_ABSENCE")
        self.assertIn("41", conflict.difference)


# ── Part 2: divergences are declared, not fixed in place ─────────────────────

class DivergenceIsDeclaredTest(unittest.TestCase):

    DIVERGING = ("sunapha", "anapha", "durudhara", "kemadruma", "gajakesari",
                 "mahapurusha_ruchaka", "raja_yoga_k1_t5_conjunction")

    def test_every_divergence_states_what_differs(self):
        for rule_id in self.DIVERGING:
            with self.subTest(rule=rule_id):
                evidence = evidence_for(rule_id)
                self.assertIs(evidence.validation_status,
                              ValidationStatus.IMPLEMENTATION_DIVERGES)
                self.assertTrue(evidence.textual_condition.strip())
                self.assertTrue(
                    evidence.divergence.strip(),
                    "a divergence claim must say what the code does instead")
                self.assertTrue(evidence.corrected_by)
                self.assertEqual(evidence.audited_in, "V1.5")

    def test_diverging_rules_still_behave_as_they_did(self):
        """
        V1.4 behaviour is unchanged. Part 2: never silently edit yoga logic.

        The corrected reading lives in `parashari_textual`; the default
        profile still contains the rule the audit criticised, doing what it
        has always done.
        """
        for rule_id in self.DIVERGING:
            with self.subTest(rule=rule_id):
                self.assertIsNotNone(rule_by_id(rule_id, "parashari"))

    def test_every_divergence_has_a_corrected_rule_that_exists(self):
        textual = {r.id for r in textual_rules()}
        for rule_id in self.DIVERGING:
            with self.subTest(rule=rule_id):
                corrected = evidence_for(rule_id).corrected_by
                if "*" in corrected:
                    prefix = corrected.split("*")[0]
                    self.assertTrue(
                        any(t.startswith(prefix) for t in textual),
                        f"no textual rule matching {corrected}")
                else:
                    self.assertIn(corrected.split(" / ")[0], textual)


# ── the corrected rules ──────────────────────────────────────────────────────

def _chart(year=1988, month=8, day=30, hour=14, minute=48,
           lat=26.9124, lon=75.7873):
    import datetime
    from engine.planets import JyotishChart, jde_from_datetime
    return JyotishChart(
        jde=jde_from_datetime(
            datetime.datetime(year, month, day, hour, minute)),
        lat=lat, lon=lon)


def _features(chart=None, with_shadbala=False):
    import datetime
    chart = chart or _chart()
    features = build_chart_features(
        chart, aspect_profile=parashari_profile("none"))
    if with_shadbala:
        from engine.strength import compute_shadbala
        features.shadbala = compute_shadbala(
            chart, features, birth=datetime.datetime(1988, 8, 30, 14, 48))
    return features


class MoonYogaTextualTest(unittest.TestCase):
    """BPHS 37.7 and BJ 13.3: the Sun is the only exclusion."""

    def test_textual_rule_counts_the_nodes_as_company(self):
        rule = rule_by_id("sunapha_textual", TEXTUAL_PROFILE)
        self.assertIsNotNone(rule)
        text = " ".join(c.label for c in rule.conditions_all)
        self.assertIn("other than Surya", text)
        self.assertNotIn("Rahu", rule.explanation)

    def test_default_and_textual_rules_can_disagree(self):
        """
        The two readings are not interchangeable, and a chart proves it.

        Constructed rather than searched for: the point is that the
        difference is REAL and observable, not that this particular nativity
        is interesting.
        """
        from engine.rules.engine import evaluate_rule
        found = False
        for day in range(1, 29):
            features = _features(_chart(1990, 6, day, 6, 0))
            default = evaluate_rule(rule_by_id("sunapha"), features)
            textual = evaluate_rule(
                rule_by_id("sunapha_textual", TEXTUAL_PROFILE), features)
            if default.present != textual.present:
                found = True
                # The textual rule is the wider one: it counts more grahas as
                # company, so it can only ever be present where the default
                # is, never the reverse.
                self.assertTrue(
                    textual.present,
                    "the located reading excludes fewer grahas, so it cannot "
                    "be absent where the narrower default rule is present")
                break
        self.assertTrue(
            found,
            "if no chart in a month distinguishes the readings the audit "
            "finding would be untestable")


class KemadrumaTextualTest(unittest.TestCase):

    def test_moon_in_kendra_no_longer_cancels(self):
        """
        BPHS 37.11's `vinā candraṃ` reverses one of the engine's clauses.

        The default rule cancels Kemadruma when the Moon itself occupies a
        kendra from the Lagna. The witness expressly excludes the Moon from
        the grahas that count.
        """
        rule = rule_by_id("kemadruma_textual", TEXTUAL_PROFILE)
        self.assertIsNotNone(rule)
        self.assertEqual(len(rule.cancellation_conditions), 1)
        self.assertIn("other than Chandra",
                      rule.cancellation_conditions[0].label)

    def test_default_rule_keeps_its_four_clauses(self):
        rule = rule_by_id("kemadruma")
        self.assertEqual(len(rule.cancellation_conditions), 4)

    def test_conflict_records_the_quotation_evidence(self):
        conflict = conflict_by_id("KEMADRUMA_BHANGA_EXTENT")
        self.assertEqual(conflict.resolution_status,
                         "RESOLVED_AGAINST_IMPLEMENTATION")
        self.assertIn("ukti-prasiddhā na te", conflict.resolution_note)


class MahapurushaTextualTest(unittest.TestCase):
    """Both witnesses require strength; the default rule does not test it."""

    def test_textual_rule_requires_strength(self):
        rule = rule_by_id("mahapurusha_hamsa_textual", TEXTUAL_PROFILE)
        self.assertIsNotNone(rule)
        labels = [c.label for c in rule.conditions_all]
        self.assertIn("Guru is strong (balibhiḥ)", labels)
        self.assertEqual(len(labels), 3)

    def test_strength_condition_fails_closed_without_shadbala(self):
        """
        No Shadbala means the yoga is not established, not that it forms.

        Strength is in the FORMATION clause in both witnesses, so a chart
        where it was never measured is a chart where the yoga has not been
        shown to form. Reporting it present would silently drop the very
        clause this rule exists to add.
        """
        from engine.rules.engine import evaluate_rule
        features = _features(with_shadbala=False)
        self.assertIsNone(features.shadbala)
        rule = rule_by_id("mahapurusha_hamsa_textual", TEXTUAL_PROFILE)
        result = evaluate_rule(rule, features)
        self.assertFalse(result.present)
        self.assertTrue(
            any("cannot be established" in f for f in result.conditions_failed))

    def test_strength_is_read_from_shadbala_when_present(self):
        from engine.rules.engine import evaluate_rule
        features = _features(with_shadbala=True)
        for key, planet in (("ruchaka", "Mangal"), ("shasha", "Shani")):
            with self.subTest(yoga=key):
                rule = rule_by_id(f"mahapurusha_{key}_textual",
                                  TEXTUAL_PROFILE)
                result = evaluate_rule(rule, features)
                ratio = features.shadbala_ratio(planet)
                self.assertIsNotNone(ratio)
                said = " ".join(result.conditions_met
                                + result.conditions_failed)
                self.assertIn(f"{ratio:.2f}x", said)

    def test_dignity_set_disagreement_is_registered(self):
        conflict = conflict_by_id("MAHAPURUSHA_DIGNITY_SET")
        self.assertEqual(conflict.resolution_status, "UNRESOLVED")
        for rule in textual_rules():
            if not rule.id.startswith("mahapurusha_"):
                continue
            with self.subTest(rule=rule.id):
                self.assertIn("MAHAPURUSHA_DIGNITY_SET",
                              evidence_for(rule.id).conflicts)


class GajakesariTextualTest(unittest.TestCase):

    def test_both_readings_ship(self):
        ids = {r.id for r in textual_rules()}
        self.assertIn("gajakesari_textual_bphs", ids)
        self.assertIn("gajakesari_textual_jataka_parijata", ids)

    def test_bphs_reading_allows_the_lagna_as_reference(self):
        rule = rule_by_id("gajakesari_textual_bphs", TEXTUAL_PROFILE)
        labels = [c.label for c in rule.conditions_all]
        self.assertIn("Guru in a kendra from the Lagna or from Chandra",
                      labels)

    def test_both_readings_require_guru_unafflicted(self):
        for rule_id in ("gajakesari_textual_bphs",
                        "gajakesari_textual_jataka_parijata"):
            with self.subTest(rule=rule_id):
                rule = rule_by_id(rule_id, TEXTUAL_PROFILE)
                labels = " ".join(c.label for c in rule.conditions_all)
                self.assertIn("free of", labels)

    def test_default_rule_tests_placement_only(self):
        rule = rule_by_id("gajakesari")
        self.assertEqual(len(rule.conditions_all), 1)


class RajaYogaTextualTest(unittest.TestCase):

    def test_bphs_34_15_exception_is_applied(self):
        rule = rule_by_id("raja_yoga_k1_t5_conjunction_textual",
                          TEXTUAL_PROFILE)
        self.assertIsNotNone(rule)
        self.assertEqual(len(rule.cancellation_conditions), 1)
        self.assertIn("34.15", rule.cancellation_conditions[0].label)

    def test_default_rules_have_no_exception(self):
        rule = rule_by_id("raja_yoga_k1_t5_conjunction")
        self.assertEqual(rule.cancellation_conditions, [])

    def test_aspect_mode_requires_full_drishti(self):
        """
        `pūrṇa-dṛṣṭyā` in BPHS 34.12 is not satisfied by a partial aspect.
        """
        ids = {r.id for r in textual_rules()}
        self.assertIn("raja_yoga_k1_t5_full_mutual_aspect_textual", ids)
        self.assertNotIn("raja_yoga_k1_t5_mutual_aspect_textual", ids)

    def test_exception_does_not_fire_on_the_regression_chart(self):
        """
        A negative result, pinned so it is not mistaken for the clause
        failing to work.

        The regression nativity is Meena lagna. Its 4th and 7th lord is
        Budha, owning no dusthana; its 5th lord is Chandra, owning only the
        5th; its 9th lord is Mangal, owning the 2nd and the 9th. No
        participating lord owns the 6th, 8th or 12th, so BPHS 34.15 has
        nothing to bite on and the four Raja Yogas stand in both profiles.

        This is exactly why the exception needed a constructed chart to test
        — see `test_exception_cancels_when_a_lord_owns_a_dusthana`.
        """
        features = _features()
        default = [r for r in evaluate_rules(features, "parashari")
                   if r.id.startswith("raja_yoga_k") and r.present]
        textual = [r for r in evaluate_rules(features, TEXTUAL_PROFILE)
                   if r.id.startswith("raja_yoga_k") and r.present]
        self.assertEqual(len(default), 4)
        self.assertEqual(len(textual), 4)
        self.assertEqual(
            [r.status.value for r in textual],
            ["PRESENT_AND_STRONG"] * 4)

    def test_exception_cancels_when_a_lord_owns_a_dusthana(self):
        """
        Mesha lagna: Mangal rules the 1st AND the 8th.

        So a Raja Yoga between the 1st lord and the 5th lord has a
        participating graha that also owns a dusthana, and BPHS 34.15 says
        the relationship alone does not give the yoga. The default rule
        reports it formed and uncancelled; the textual rule reports it
        formed and cancelled. Both agree it FORMED — the exception is a
        cancellation, not a denial of formation, which is the distinction
        the rule engine has kept since V1.1.
        """
        from engine.rules.engine import evaluate_rule
        from tests.synthetic import synthetic_features

        # Mesha lagna (0). 1st lord Mangal and 5th lord Surya together in
        # Simha (4), the 5th house.
        features = synthetic_features(
            lagna_sign=0, placements={"Mangal": 4, "Surya": 4})
        self.assertEqual(features.houses_owned_by("Mangal"), [1, 8])

        default = evaluate_rule(
            rule_by_id("raja_yoga_k1_t5_conjunction"), features)
        textual = evaluate_rule(
            rule_by_id("raja_yoga_k1_t5_conjunction_textual",
                       TEXTUAL_PROFILE), features)

        self.assertTrue(default.present)
        self.assertTrue(textual.present)
        self.assertEqual(default.cancellations_found, [])
        self.assertTrue(textual.cancellations_found)
        self.assertIn("34.15", textual.cancellations_found[0])
        self.assertEqual(textual.status.value, "PRESENT_BUT_CANCELLED")
        self.assertFalse(textual.effective)

    def test_full_aspect_requirement_rejects_a_partial_drishti(self):
        """
        `pūrṇa-dṛṣṭyā` at BPHS 34.12, tested rather than merely named.

        Two lords in mutual aspect where BOTH aspects are partial: the
        default rule accepts it, the textual rule does not.
        """
        from engine.rules.engine import evaluate_rule
        from tests.synthetic import synthetic_features

        # Mesha lagna. 4th lord Chandra in Karka (3), 9th lord Guru in
        # Dhanu (8), with partial mutual drishti declared explicitly.
        features = synthetic_features(
            lagna_sign=0,
            placements={"Chandra": 3, "Guru": 8},
            aspects=(("Chandra", 8, False), ("Guru", 3, False)))

        default = evaluate_rule(
            rule_by_id("raja_yoga_k4_t9_mutual_aspect"), features)
        textual = evaluate_rule(
            rule_by_id("raja_yoga_k4_t9_full_mutual_aspect_textual",
                       TEXTUAL_PROFILE), features)
        self.assertTrue(
            default.present,
            "the default rule accepts any graha drishti")
        self.assertFalse(
            textual.present,
            "the located reading requires full drishti")

    def test_all_36_textual_raja_yogas_exist(self):
        ids = {r.id for r in textual_rules() if r.id.startswith("raja_yoga_")}
        self.assertEqual(len(ids), 33)


class LakshmiConflictTest(unittest.TestCase):
    """Two witnesses, two different rules, one name."""

    def test_both_readings_ship_separately(self):
        ids = {r.id for r in textual_rules()}
        self.assertIn("lakshmi_yoga_bphs", ids)
        self.assertIn("lakshmi_yoga_phaladeepika", ids)

    def test_phaladeepika_reading_requires_venus(self):
        rule = rule_by_id("lakshmi_yoga_phaladeepika", TEXTUAL_PROFILE)
        self.assertIn("Shukra", rule.planets_involved)

    def test_bphs_reading_requires_a_strong_lagna_lord(self):
        rule = rule_by_id("lakshmi_yoga_bphs", TEXTUAL_PROFILE)
        labels = [c.label for c in rule.conditions_all]
        self.assertIn("the Lagna lord is strong (balāḍhya)", labels)

    def test_the_shipped_v11_rule_matches_neither(self):
        evidence = evidence_for("lakshmi_yoga")
        self.assertIs(evidence.validation_status,
                      ValidationStatus.CONFLICTING_SOURCES)
        self.assertIn("LAKSHMI_YOGA_DEFINITION", evidence.conflicts)

    def test_conflict_is_modelled_not_resolved(self):
        conflict = conflict_by_id("LAKSHMI_YOGA_DEFINITION")
        self.assertEqual(conflict.resolution_status, "MODELLED_AS_TWO_RULES")


# ── the textual profile ──────────────────────────────────────────────────────

class TextualProfileTest(unittest.TestCase):

    def test_profile_substitutes_rather_than_adds(self):
        """
        One combination, one finding. A chart must not report both readings
        of Gajakesari as if they were two separate discoveries.
        """
        ids = {r.id for r in rules_for_profile(TEXTUAL_PROFILE)}
        for superseded in SUPERSEDED_BY_TEXTUAL:
            with self.subTest(rule=superseded):
                self.assertNotIn(superseded, ids)

    def test_profile_is_smaller_than_the_default(self):
        """
        A located reading that narrows a rule is still a narrowing.

        Worth pinning because the intuitive expectation runs the other way:
        more sourcing sounds like more rules, and here it means fewer and
        stricter ones.
        """
        self.assertLess(len(rules_for_profile(TEXTUAL_PROFILE)),
                        len(rules_for_profile("parashari")))

    def test_every_textual_rule_names_its_witness_in_its_source(self):
        for rule in textual_rules():
            with self.subTest(rule=rule.id):
                self.assertIn("witness", rule.source.lower())
                self.assertTrue(evidence_for(rule.id).witness_ids)

    def test_every_textual_rule_declares_what_it_varies_from(self):
        default = {r.id for r in rules_for_profile("parashari_extended")}
        for rule in textual_rules():
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.variant_of)
                self.assertIn(rule.variant_of, default)


if __name__ == "__main__":
    unittest.main()
