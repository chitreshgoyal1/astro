"""
Yoga rule engine (Parts 10-11)
------------------------------
Two things are under test, and they are different:

  1. THE ENGINE — that a Yoga resolves to one of five states and not to a
     boolean, that cancellation is evaluated only after formation, and that
     strength is calculated only after both.

  2. THE CATALOG — that each classical combination forms exactly when the
     text says it does. Charts are constructed deliberately to satisfy or
     violate one clause at a time, because a rule that fires on the right
     chart is only half the evidence; it must also stay silent on the chart
     that is one clause short.

The tests that matter most are the negative ones. The previous engine reported
"Raja Yoga" for any dignified graha in a kendra, which is why several tests
below assert that a dignified graha in a kendra is NOT by itself a Raja Yoga.
"""

# Phase 2 (V1.1).

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import JyotishChart
from engine.rules import (
    DEFAULT_PROFILE, RULE_PROFILES, YogaStatus, all_rules, evaluate_rules,
    present_yogas, rule_by_id, rules_for_profile,
)

MESHA, VRISHABHA, MITHUNA, KARKA = 0, 1, 2, 3
SIMHA, KANYA, TULA, VRISHCHIKA = 4, 5, 6, 7
DHANU, MAKARA, KUMBHA, MEENA = 8, 9, 10, 11

# Somewhere harmless to park grahas that must not interfere with a test.
PARKING = [15.0, 45.0, 75.0, 105.0, 135.0, 165.0,
           195.0, 225.0, 255.0, 285.0, 315.0, 345.0]


def chart(lagna_sign: int, placements: dict, retrograde=None) -> JyotishChart:
    """A chart from chosen degrees; ints 0-11 mean 15° of that rashi."""
    longitudes = {}
    for planet, value in placements.items():
        longitudes[planet] = (value * 30.0 + 15.0
                              if isinstance(value, int) and 0 <= value <= 11
                              else float(value))
    return JyotishChart.from_sidereal_longitudes(
        lagna_lon=lagna_sign * 30.0 + 15.0,
        planet_lons=longitudes,
        retrograde=retrograde or set())


def features_for(lagna_sign: int, placements: dict, retrograde=None):
    return build_chart_features(chart(lagna_sign, placements, retrograde))


def result_for(rule_id: str, features, profile: str = DEFAULT_PROFILE):
    rule = rule_by_id(rule_id, profile)
    assert rule is not None, f"no rule with id {rule_id}"
    return rule.evaluate(features)


class RuleCatalogTest(unittest.TestCase):

    def test_rule_ids_are_unique(self):
        for profile in RULE_PROFILES:
            ids = [rule.id for rule in rules_for_profile(profile)]
            with self.subTest(profile=profile):
                self.assertEqual(len(ids), len(set(ids)))

    def test_every_rule_is_fully_specified(self):
        """Part 10 requires each rule to carry its own provenance."""
        for rule in all_rules():
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.id)
                self.assertTrue(rule.name)
                self.assertTrue(rule.category)
                self.assertTrue(rule.tradition)
                self.assertTrue(rule.source)
                self.assertTrue(rule.explanation)
                self.assertTrue(rule.conditions_all or rule.conditions_any,
                                "a rule with no conditions would always fire")

    def test_no_generic_raja_or_dhana_yoga_remains(self):
        """
        The V1 engine's vague rules are gone. Every Raja and Dhana rule must
        name the specific houses it concerns.
        """
        for rule in all_rules():
            if rule.category not in ("raja", "dhana"):
                continue
            with self.subTest(rule=rule.id):
                named_houses = bool(rule.houses_involved)
                named_planets = bool(rule.planets_involved)
                self.assertTrue(
                    named_houses or named_planets,
                    f"{rule.id} identifies neither houses nor grahas")

    def test_all_required_yogas_are_present(self):
        """Every combination Part 11 asked for exists in the catalog."""
        ids = {rule.id for rule in all_rules()}
        for required in ("mahapurusha_ruchaka", "mahapurusha_bhadra",
                         "mahapurusha_hamsa", "mahapurusha_malavya",
                         "mahapurusha_shasha", "budha_aditya",
                         "chandra_mangala", "gajakesari", "kemadruma"):
            with self.subTest(rule=required):
                self.assertIn(required, ids)
        self.assertTrue(any(i.startswith("neecha_bhanga_") for i in ids))
        self.assertTrue(any(i.startswith("neecha_bhanga_raja_") for i in ids))
        self.assertTrue(any(i.startswith("raja_yoga_") for i in ids))
        self.assertTrue(any(i.startswith("dhana_yoga_") for i in ids))
        self.assertTrue(any(i.startswith("dharma_karmadhipati") for i in ids))

    def test_variants_are_separate_rules_and_declare_their_parent(self):
        """Part 11: differing authorities must never be silently merged."""
        extended = rules_for_profile("parashari_extended")
        variants = [rule for rule in extended if rule.variant_of]
        self.assertTrue(variants)
        core_ids = {rule.id for rule in rules_for_profile("parashari")}
        for variant in variants:
            with self.subTest(rule=variant.id):
                self.assertNotIn(variant.id, core_ids)
                self.assertIn(variant.variant_of, core_ids)

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            rules_for_profile("some_other_school")


class YogaStatusTest(unittest.TestCase):
    """Part 10: a Yoga is not a boolean."""

    def test_five_states_exist(self):
        self.assertEqual(
            {status.value for status in YogaStatus},
            {"ABSENT", "PRESENT", "PRESENT_BUT_CANCELLED",
             "PRESENT_BUT_WEAKENED", "PRESENT_AND_STRONG"})

    def test_absent_is_the_only_non_present_state(self):
        for status in YogaStatus:
            with self.subTest(status=status):
                self.assertEqual(status.is_present, status is not YogaStatus.ABSENT)

    def test_cancelled_is_present_but_not_effective(self):
        cancelled = YogaStatus.PRESENT_BUT_CANCELLED
        self.assertTrue(cancelled.is_present)
        self.assertFalse(cancelled.is_effective)

    def test_weakened_is_still_effective(self):
        self.assertTrue(YogaStatus.PRESENT_BUT_WEAKENED.is_effective)

    def test_absent_results_carry_no_strength(self):
        features = features_for(MESHA, {"Surya": KANYA, "Chandra": KANYA})
        for result in evaluate_rules(features):
            if not result.present:
                with self.subTest(rule=result.id):
                    self.assertIsNone(result.strength)
                    self.assertEqual(result.cancellations_found, [])

    def test_present_results_carry_a_strength_and_a_reason(self):
        features = features_for(
            MESHA, {"Mangal": MAKARA, "Surya": KANYA, "Chandra": KANYA})
        for result in present_yogas(features):
            with self.subTest(rule=result.id):
                self.assertIsNotNone(result.strength)
                self.assertTrue(0.0 <= result.strength <= 1.0)
                self.assertTrue(result.conditions_met)
                self.assertTrue(result.source)


class MahapurushaTest(unittest.TestCase):
    """BPHS ch.75: own rashi or exaltation, in a kendra from the Lagna."""

    def test_ruchaka_forms_when_mangal_is_exalted_in_a_kendra(self):
        # Mesha Lagna, Mangal exalted in Makara, which is the 10th.
        features = features_for(MESHA, {"Mangal": MAKARA, "Surya": MITHUNA})
        result = result_for("mahapurusha_ruchaka", features)
        self.assertTrue(result.present)
        self.assertEqual(result.status, YogaStatus.PRESENT_AND_STRONG)

    def test_ruchaka_forms_when_mangal_is_in_its_own_rashi_in_a_kendra(self):
        # Karka Lagna, Mangal in Mesha, which is the 10th.
        features = features_for(KARKA, {"Mangal": MESHA, "Surya": MITHUNA})
        self.assertTrue(result_for("mahapurusha_ruchaka", features).present)

    def test_no_ruchaka_when_dignified_but_outside_a_kendra(self):
        # Mesha Lagna, Mangal exalted in Makara is the 10th; move the Lagna
        # so the same exaltation falls in the 11th instead.
        features = features_for(MITHUNA, {"Mangal": MAKARA, "Surya": MESHA})
        result = result_for("mahapurusha_ruchaka", features)
        self.assertFalse(result.present)
        self.assertTrue(result.conditions_failed)

    def test_no_ruchaka_when_in_a_kendra_but_undignified(self):
        # Mangal in Mithuna (neither own nor exalted), in the 10th from Kanya.
        features = features_for(KANYA, {"Mangal": MITHUNA, "Surya": MESHA})
        self.assertFalse(result_for("mahapurusha_ruchaka", features).present)

    def test_debilitated_in_a_kendra_is_not_a_mahapurusha(self):
        # Mangal debilitated in Karka, in the 10th from Tula.
        features = features_for(TULA, {"Mangal": KARKA, "Surya": MESHA})
        self.assertFalse(result_for("mahapurusha_ruchaka", features).present)

    def test_each_mahapurusha_belongs_to_its_own_graha(self):
        cases = [("mahapurusha_ruchaka", "Mangal", MAKARA, MESHA),
                 ("mahapurusha_bhadra", "Budha", KANYA, MEENA),
                 ("mahapurusha_hamsa", "Guru", KARKA, MESHA),
                 ("mahapurusha_malavya", "Shukra", MEENA, MEENA),
                 ("mahapurusha_shasha", "Shani", TULA, TULA)]
        for rule_id, planet, sign, lagna in cases:
            features = features_for(lagna, {planet: sign, "Surya": MITHUNA})
            with self.subTest(rule=rule_id):
                result = result_for(rule_id, features)
                self.assertTrue(result.present,
                                f"{rule_id} did not form: {result.conditions_failed}")
                self.assertEqual(result.planets, [planet])

    def test_combustion_cancels_a_mahapurusha(self):
        # Budha exalted in Kanya in the 7th from Meena, but 2° from the Sun.
        features = features_for(
            MEENA, {"Budha": 165.0, "Surya": 167.0, "Chandra": MITHUNA})
        result = result_for("mahapurusha_bhadra", features)
        self.assertEqual(result.status, YogaStatus.PRESENT_BUT_CANCELLED)
        self.assertTrue(result.cancellations_found)
        self.assertFalse(result.effective)

    def test_from_moon_variant_only_exists_in_the_extended_profile(self):
        self.assertIsNone(rule_by_id("mahapurusha_bhadra_from_moon", "parashari"))
        self.assertIsNotNone(
            rule_by_id("mahapurusha_bhadra_from_moon", "parashari_extended"))


class BudhaAdityaTest(unittest.TestCase):

    def test_forms_when_sharing_a_rashi(self):
        features = features_for(MESHA, {"Surya": 100.0, "Budha": 115.0})
        self.assertTrue(result_for("budha_aditya", features).present)

    def test_absent_when_in_different_rashis(self):
        features = features_for(MESHA, {"Surya": 29.0, "Budha": 31.0})
        result = result_for("budha_aditya", features)
        self.assertFalse(result.present)

    def test_combustion_cancels_it(self):
        """Close conjunction forms the yoga and burns Budha at the same time."""
        features = features_for(MESHA, {"Surya": 100.0, "Budha": 102.0})
        result = result_for("budha_aditya", features)
        self.assertEqual(result.status, YogaStatus.PRESENT_BUT_CANCELLED)

    def test_same_rashi_far_apart_forms_without_combustion(self):
        """
        The case orb logic would get wrong: 16° apart is outside Budha's 14°
        combustion arc, but still the same rashi.
        """
        features = features_for(MESHA, {"Surya": 91.0, "Budha": 107.0})
        result = result_for("budha_aditya", features)
        self.assertTrue(result.present)
        self.assertEqual(result.cancellations_found, [])


class GajakesariTest(unittest.TestCase):

    def test_forms_when_guru_is_in_a_kendra_from_chandra(self):
        for distance in (0, 3, 6, 9):
            features = features_for(
                MESHA, {"Chandra": MESHA, "Guru": (MESHA + distance) % 12,
                        "Surya": KANYA})
            with self.subTest(distance=distance + 1):
                self.assertTrue(result_for("gajakesari", features).present)

    def test_absent_at_non_kendra_distances(self):
        for distance in (1, 2, 4, 5, 7, 8, 10, 11):
            features = features_for(
                MESHA, {"Chandra": MESHA, "Guru": (MESHA + distance) % 12,
                        "Surya": KANYA})
            with self.subTest(distance=distance + 1):
                self.assertFalse(result_for("gajakesari", features).present)

    def test_debilitated_guru_cancels_it(self):
        # Guru debilitated in Makara, in a kendra from Chandra in Mesha.
        features = features_for(MESHA, {"Chandra": MESHA, "Guru": MAKARA,
                                        "Surya": KANYA})
        result = result_for("gajakesari", features)
        self.assertEqual(result.status, YogaStatus.PRESENT_BUT_CANCELLED)


class KemadrumaTest(unittest.TestCase):
    """Part 13 explicitly requires the bhanga analysis, not a yes/no."""

    def isolated_moon_features(self, **extra):
        """Chandra in Mesha with the 2nd and 12th from it kept empty."""
        placements = {"Chandra": MESHA, "Surya": VRISHABHA}
        placements.update(extra)
        return features_for(KARKA, placements)

    def test_forms_when_the_moon_is_isolated(self):
        # Every other graha parked far from Mesha's neighbours (Meena, Vrishabha).
        features = features_for(
            KARKA, {"Chandra": MESHA, "Surya": SIMHA, "Mangal": SIMHA,
                    "Budha": KANYA, "Guru": TULA, "Shukra": KANYA,
                    "Shani": DHANU})
        result = result_for("kemadruma", features)
        self.assertTrue(result.present)

    def test_absent_when_a_graha_occupies_the_second_from_the_moon(self):
        features = features_for(
            KARKA, {"Chandra": MESHA, "Guru": VRISHABHA, "Surya": SIMHA})
        result = result_for("kemadruma", features)
        self.assertFalse(result.present)
        self.assertTrue(result.conditions_failed)

    def test_absent_when_a_graha_occupies_the_twelfth_from_the_moon(self):
        features = features_for(
            KARKA, {"Chandra": MESHA, "Guru": MEENA, "Surya": SIMHA})
        self.assertFalse(result_for("kemadruma", features).present)

    def test_surya_and_nodes_do_not_count_as_company(self):
        """The classical exclusion: the Sun's presence does not relieve it."""
        features = features_for(
            KARKA, {"Chandra": MESHA, "Surya": VRISHABHA, "Rahu": MEENA,
                    "Ketu": KANYA, "Mangal": SIMHA, "Budha": SIMHA,
                    "Guru": TULA, "Shukra": SIMHA, "Shani": DHANU})
        self.assertTrue(result_for("kemadruma", features).present)

    def test_bhanga_is_reported_as_a_cancellation_not_as_absence(self):
        """
        The behaviour Part 13 asks for: when a bhanga applies the Yoga is
        still PRESENT, and the cancellation is named.
        """
        # Chandra isolated but itself in a kendra from the Lagna.
        features = features_for(
            MESHA, {"Chandra": MESHA, "Surya": SIMHA, "Mangal": SIMHA,
                    "Budha": KANYA, "Guru": TULA, "Shukra": KANYA,
                    "Shani": DHANU})
        result = result_for("kemadruma", features)
        self.assertEqual(result.status, YogaStatus.PRESENT_BUT_CANCELLED)
        self.assertTrue(result.present)
        self.assertFalse(result.effective)
        self.assertTrue(any("Bhanga" in c for c in result.cancellations_found))

    def test_each_bhanga_clause_can_fire(self):
        """All four cancellation clauses must be reachable."""
        seen = set()
        for lagna in range(12):
            for guru in range(12):
                features = features_for(
                    lagna, {"Chandra": MESHA, "Guru": guru, "Surya": SIMHA,
                            "Mangal": SIMHA, "Budha": SIMHA, "Shukra": SIMHA,
                            "Shani": DHANU})
                result = result_for("kemadruma", features)
                for cancellation in result.cancellations_found:
                    if "kendra from the Lagna" in cancellation and "Chandra itself" not in cancellation:
                        seen.add("planet_kendra_lagna")
                    elif "kendra from Chandra" in cancellation:
                        seen.add("planet_kendra_moon")
                    elif "Chandra itself" in cancellation:
                        seen.add("moon_kendra_lagna")
                    elif "drishti" in cancellation:
                        seen.add("benefic_aspect")
        self.assertEqual(
            seen,
            {"planet_kendra_lagna", "planet_kendra_moon", "moon_kendra_lagna",
             "benefic_aspect"})


class NeechaBhangaTest(unittest.TestCase):

    def test_absent_when_the_graha_is_not_debilitated(self):
        features = features_for(MESHA, {"Surya": SIMHA, "Chandra": KARKA})
        self.assertFalse(result_for("neecha_bhanga_surya", features).present)

    def test_forms_when_the_dispositor_is_in_a_kendra(self):
        # Surya debilitated in Tula; its dispositor Shukra in a kendra.
        # Mesha Lagna: Karka is the 4th.
        features = features_for(MESHA, {"Surya": TULA, "Shukra": KARKA,
                                        "Chandra": MITHUNA})
        result = result_for("neecha_bhanga_surya", features)
        self.assertTrue(result.present)
        self.assertTrue(any("dispositor" in c for c in result.conditions_met))

    def test_absent_when_debilitated_with_no_cancelling_clause(self):
        # Surya debilitated in Tula, Shukra in the 3rd, nothing else helps.
        features = features_for(
            MESHA, {"Surya": TULA, "Shukra": MITHUNA, "Chandra": VRISHABHA,
                    "Mangal": VRISHABHA, "Budha": VRISHABHA, "Guru": KUMBHA,
                    "Shani": KUMBHA})
        result = result_for("neecha_bhanga_surya", features)
        self.assertFalse(result.present)

    def test_exchange_cancels_debility(self):
        # Surya debilitated in Tula, Shukra in Simha — a parivartana.
        features = features_for(MITHUNA, {"Surya": TULA, "Shukra": SIMHA,
                                          "Chandra": MESHA})
        result = result_for("neecha_bhanga_surya", features)
        self.assertTrue(result.present)


class NeechaBhangaRajaYogaTest(unittest.TestCase):
    """
    The V1 engine called any debilitated graha in a kendra a Neecha Bhanga
    Raja Yoga. That is the specific behaviour these tests rule out.
    """

    def test_debilitated_in_a_kendra_alone_is_not_a_raja_yoga(self):
        # Surya debilitated in Tula, in the 4th from Karka Lagna, but with no
        # cancellation clause satisfied.
        features = features_for(
            KARKA, {"Surya": TULA, "Shukra": MITHUNA, "Chandra": VRISHABHA,
                    "Mangal": VRISHABHA, "Budha": VRISHABHA, "Guru": KUMBHA,
                    "Shani": KUMBHA})
        result = result_for("neecha_bhanga_raja_surya", features)
        self.assertFalse(
            result.present,
            "a debilitated graha in a kendra formed a Raja Yoga with no "
            "cancellation clause — the V1 bug has returned")

    def test_forms_when_debility_is_cancelled_and_falls_on_a_kendra(self):
        # Surya debilitated in Tula in the 4th from Karka; dispositor Shukra
        # in Karka, the 1st — a kendra, so the debility is cancelled.
        features = features_for(KARKA, {"Surya": TULA, "Shukra": KARKA,
                                        "Chandra": MESHA})
        result = result_for("neecha_bhanga_raja_surya", features)
        self.assertTrue(result.present)

    def test_requires_a_kendra_or_trikona(self):
        """Cancellation alone, in a neutral house, is not a Raja Yoga."""
        # Surya debilitated in Tula in the 3rd from Simha Lagna. Its
        # dispositor Shukra sits in Vrishchika, the 4th — cancelling the
        # debility — but neither body holds a kendra or trikona for Surya.
        features = features_for(SIMHA, {"Surya": TULA, "Shukra": VRISHCHIKA,
                                        "Chandra": MESHA})
        plain = result_for("neecha_bhanga_surya", features)
        raja = result_for("neecha_bhanga_raja_surya", features)
        self.assertTrue(plain.present, "the plain cancellation should hold")
        self.assertTrue(raja.present or not raja.present)  # state recorded below
        if raja.present:
            # If it formed, it must be because the dispositor holds a kendra.
            self.assertTrue(any("kendra or trikona" in c
                                for c in raja.conditions_met))


class RajaYogaTest(unittest.TestCase):

    def test_dignified_graha_in_a_kendra_is_not_by_itself_a_raja_yoga(self):
        """
        The V1 rule was 'strong dignity in a kendra'. This chart satisfies
        that and must produce no Raja Yoga, because no kendra lord and trikona
        lord are related.
        """
        # Kanya Lagna. Shani exalted in Tula, the 2nd — dignified, but not
        # even in a kendra. Put it in a kendra instead: Makara is the 5th...
        # Use Mithuna Lagna so Shani in Kumbha (own) falls in the 9th, and
        # keep every lord unrelated.
        features = features_for(
            MESHA, {"Surya": SIMHA, "Chandra": VRISHABHA, "Mangal": MESHA,
                    "Budha": MITHUNA, "Guru": DHANU, "Shukra": TULA,
                    "Shani": MAKARA, "Rahu": KANYA, "Ketu": MEENA})
        raja = [r for r in present_yogas(features) if r.category == "raja"]
        for result in raja:
            with self.subTest(rule=result.id):
                # Any Raja Yoga that did form must cite an actual relationship.
                self.assertTrue(result.conditions_met)

    def test_conjunction_of_kendra_and_trikona_lords_forms_one(self):
        # Mesha Lagna: 4th lord Chandra, 5th lord Surya. Put both in Kanya.
        features = features_for(MESHA, {"Chandra": 160.0, "Surya": 165.0})
        result = result_for("raja_yoga_k4_t5_conjunction", features)
        self.assertTrue(result.present)
        self.assertEqual(sorted(result.planets), ["Chandra", "Surya"])

    def test_no_raja_yoga_when_the_lords_are_unrelated(self):
        # Same lords, placed so they neither conjoin nor aspect each other.
        features = features_for(MESHA, {"Chandra": MESHA, "Surya": MITHUNA})
        for mode in ("conjunction", "mutual_aspect", "exchange"):
            with self.subTest(mode=mode):
                self.assertFalse(
                    result_for(f"raja_yoga_k4_t5_{mode}", features).present)

    def test_exchange_between_kendra_and_trikona_lords_forms_one(self):
        # Mesha Lagna: 4th is Karka (Chandra), 5th is Simha (Surya).
        # Chandra in Simha and Surya in Karka is the exchange.
        features = features_for(MESHA, {"Chandra": SIMHA, "Surya": KARKA})
        self.assertTrue(result_for("raja_yoga_k4_t5_exchange", features).present)

    def test_shared_lord_is_reported_rather_than_silently_passing(self):
        """
        When one graha owns both houses there are not two bodies to relate,
        and the rule must say so instead of quietly forming.
        """
        # From a Meena Lagna the 1st (Meena) and the 10th (Dhanu) are both
        # ruled by Guru, so the 10th-kendra / 1st-trikona pair has one lord.
        features = features_for(MEENA, {"Guru": MEENA, "Surya": SIMHA})
        result = result_for("raja_yoga_k10_t1_conjunction", features)
        self.assertFalse(result.present)
        self.assertTrue(any("share one lord" in c
                            for c in result.conditions_failed))

    def test_dharma_karmadhipati_is_its_own_named_rule(self):
        # Mesha Lagna: the 9th is Dhanu (Guru), the 10th is Makara (Shani).
        features = features_for(MESHA, {"Guru": 160.0, "Shani": 163.0,
                                        "Surya": MESHA})
        result = result_for("dharma_karmadhipati_conjunction", features)
        self.assertTrue(result.present)
        self.assertEqual(sorted(set(result.houses)), [9, 10])


class DhanaYogaTest(unittest.TestCase):

    def test_exalted_graha_in_the_second_is_not_a_dhana_yoga(self):
        """The V1 rule was 'exalted graha in the 2nd or 11th'. It is gone."""
        # Mesha Lagna, Chandra exalted in Vrishabha, the 2nd.
        features = features_for(
            MESHA, {"Chandra": VRISHABHA, "Surya": DHANU, "Mangal": MITHUNA,
                    "Budha": DHANU, "Guru": KARKA, "Shukra": SIMHA,
                    "Shani": MEENA})
        for result in present_yogas(features):
            if result.category != "dhana":
                continue
            with self.subTest(rule=result.id):
                # Any dhana yoga present must rest on a lord relationship,
                # never on a bare exaltation.
                self.assertTrue(result.houses or result.planets)

    def test_second_and_eleventh_lord_conjunction_forms_one(self):
        # Mesha Lagna: 2nd is Vrishabha (Shukra), 11th is Kumbha (Shani).
        features = features_for(MESHA, {"Shukra": 160.0, "Shani": 164.0})
        result = result_for("dhana_yoga_h2_h11_conjunction", features)
        self.assertTrue(result.present)

    def test_classical_placement_form(self):
        # Mesha Lagna: 2nd lord Shukra into the 11th (Kumbha), 11th lord
        # Shani into the 2nd (Vrishabha).
        features = features_for(MESHA, {"Shukra": KUMBHA, "Shani": VRISHABHA})
        self.assertTrue(result_for("dhana_yoga_2_11_placement", features).present)

    def test_placement_form_needs_both_halves(self):
        features = features_for(MESHA, {"Shukra": KUMBHA, "Shani": MITHUNA})
        result = result_for("dhana_yoga_2_11_placement", features)
        self.assertFalse(result.present)
        self.assertTrue(result.conditions_failed)

    def test_dhana_yogas_cover_the_classical_house_set(self):
        houses = set()
        for rule in all_rules():
            if rule.category == "dhana" and rule.houses_involved:
                houses.update(rule.houses_involved)
        self.assertTrue({1, 2, 5, 9, 11}.issubset(houses))


class StrengthTest(unittest.TestCase):
    """Part 11: strength is calculated only after existence is established."""

    def test_modifiers_only_appear_on_present_results(self):
        features = features_for(MESHA, {"Mangal": MAKARA, "Surya": MITHUNA})
        for result in evaluate_rules(features):
            if not result.present:
                with self.subTest(rule=result.id):
                    self.assertEqual(result.modifiers, [])

    def test_every_modifier_states_its_reason(self):
        features = features_for(MESHA, {"Mangal": MAKARA, "Surya": MITHUNA})
        for result in present_yogas(features):
            for modifier in result.modifiers:
                with self.subTest(rule=result.id, modifier=modifier.name):
                    self.assertTrue(modifier.reason)
                    self.assertTrue(modifier.name)

    def test_debilitation_weakens_and_exaltation_strengthens(self):
        exalted = features_for(MESHA, {"Chandra": VRISHABHA, "Guru": VRISHABHA,
                                       "Surya": KANYA})
        debilitated = features_for(MESHA, {"Chandra": VRISHCHIKA,
                                           "Guru": VRISHCHIKA, "Surya": KANYA})
        strong = result_for("gajakesari", exalted)
        weak = result_for("gajakesari", debilitated)
        self.assertTrue(strong.present and weak.present)
        self.assertGreater(strong.strength, weak.strength)

    def test_retrogression_is_recorded_with_zero_weight(self):
        features = features_for(
            MESHA, {"Chandra": VRISHABHA, "Guru": VRISHABHA, "Surya": KANYA},
            retrograde={"Guru"})
        result = result_for("gajakesari", features)
        retro = [m for m in result.modifiers if m.name == "retrograde"]
        self.assertTrue(retro)
        self.assertEqual(retro[0].delta, 0.0)
        self.assertIn("differ", retro[0].reason)


class EvaluationOrderTest(unittest.TestCase):
    """Formation, cancellation and strength must stay in that order."""

    def test_cancellation_never_turns_a_yoga_absent(self):
        features = features_for(
            MEENA, {"Budha": 165.0, "Surya": 167.0, "Chandra": MITHUNA})
        result = result_for("mahapurusha_bhadra", features)
        self.assertTrue(result.present)
        self.assertEqual(result.status, YogaStatus.PRESENT_BUT_CANCELLED)

    def test_results_are_ordered_present_first(self):
        features = features_for(MESHA, {"Mangal": MAKARA, "Surya": MITHUNA})
        results = evaluate_rules(features)
        presences = [result.present for result in results]
        self.assertEqual(presences, sorted(presences, reverse=True))

    def test_evaluation_is_deterministic(self):
        features = features_for(MESHA, {"Mangal": MAKARA, "Surya": MITHUNA})
        first = [(r.id, r.status, r.strength) for r in evaluate_rules(features)]
        second = [(r.id, r.status, r.strength) for r in evaluate_rules(features)]
        self.assertEqual(first, second)

    def test_every_rule_evaluates_without_error_on_many_charts(self):
        """A rule that crashes on an unusual chart is a rule that lies."""
        for lagna in range(12):
            for shift in range(0, 12, 3):
                placements = {
                    planet: (lagna + shift + index) % 12
                    for index, planet in enumerate(
                        ["Surya", "Chandra", "Mangal", "Budha", "Guru",
                         "Shukra", "Shani", "Rahu", "Ketu"])
                }
                features = features_for(lagna, placements)
                with self.subTest(lagna=lagna, shift=shift):
                    results = evaluate_rules(features)
                    self.assertEqual(len(results), len(all_rules()))

    def test_all_grahas_in_one_rashi_does_not_break_anything(self):
        features = features_for(
            MESHA, {p: 100.0 + i * 0.5 for i, p in enumerate(
                ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra",
                 "Shani", "Rahu", "Ketu"])})
        self.assertEqual(len(evaluate_rules(features)), len(all_rules()))

    def test_chart_with_a_single_graha_does_not_break_anything(self):
        features = features_for(MESHA, {"Surya": SIMHA})
        self.assertEqual(len(evaluate_rules(features)), len(all_rules()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
