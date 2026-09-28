"""
Extended Yoga catalog (V1.2 Part 10)
-------------------------------------
Tests the combinations added in V1.2. The pattern is the same as V1.1's: for
each rule, a chart built to satisfy it, and — more importantly — a chart that
is one clause short and must NOT trigger it.

The negative cases carry the weight. A rule that fires on the right chart has
shown only half of what it needs to show.
"""

# V1.2.

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import JyotishChart
from engine.rules import (
    RULE_PROFILES, YogaStatus, all_rules, rule_by_id, rules_for_profile,
)

MESHA, VRISHABHA, MITHUNA, KARKA = 0, 1, 2, 3
SIMHA, KANYA, TULA, VRISHCHIKA = 4, 5, 6, 7
DHANU, MAKARA, KUMBHA, MEENA = 8, 9, 10, 11

ALL_GRAHAS = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra",
              "Shani", "Rahu", "Ketu"]


def features_for(lagna_sign: int, placements: dict, retrograde=None):
    longitudes = {}
    for planet, value in placements.items():
        longitudes[planet] = (value * 30.0 + 15.0
                              if isinstance(value, int) and 0 <= value <= 11
                              else float(value))
    chart = JyotishChart.from_sidereal_longitudes(
        lagna_lon=lagna_sign * 30.0 + 15.0,
        planet_lons=longitudes,
        retrograde=retrograde or set())
    return build_chart_features(chart)


def result_for(rule_id: str, features, profile: str = "parashari"):
    rule = rule_by_id(rule_id, profile)
    assert rule is not None, f"no rule with id {rule_id} in profile {profile}"
    return rule.evaluate(features)


class CatalogIntegrityTest(unittest.TestCase):

    def test_all_requested_families_are_present(self):
        """Every family the V1.2 brief lists must exist in the catalog."""
        ids = {rule.id for rule in rules_for_profile("parashari_extended")}
        prefixes = [
            "raja_yoga_", "dhana_yoga_", "vipareeta_", "parivartana_",
            "neecha_bhanga_", "neecha_bhanga_raja_", "gajakesari",
            "kemadruma_bhanga_", "adhi_yoga", "amala_yoga", "sunapha",
            "anapha", "durudhara", "vesi", "vasi", "ubhayachari",
            "lakshmi_yoga", "saraswati_yoga", "dharma_karmadhipati",
        ]
        for prefix in prefixes:
            with self.subTest(family=prefix):
                self.assertTrue(
                    any(i.startswith(prefix) for i in ids),
                    f"no rule found for the {prefix} family")

    def test_catalog_grew_without_losing_v11_rules(self):
        ids = {rule.id for rule in all_rules()}
        for v11_id in ("mahapurusha_bhadra", "budha_aditya", "chandra_mangala",
                       "gajakesari", "kemadruma", "dharma_karmadhipati_conjunction",
                       "dhana_yoga_2_11_placement"):
            with self.subTest(rule=v11_id):
                self.assertIn(v11_id, ids)
        self.assertGreaterEqual(len(ids), 110)

    def test_ids_unique_across_every_profile(self):
        for profile in RULE_PROFILES:
            ids = [rule.id for rule in rules_for_profile(profile)]
            with self.subTest(profile=profile):
                self.assertEqual(len(ids), len(set(ids)))

    def test_every_new_rule_is_fully_specified(self):
        for rule in rules_for_profile("parashari_extended"):
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.id)
                self.assertTrue(rule.name)
                self.assertTrue(rule.category)
                self.assertTrue(rule.tradition)
                self.assertTrue(rule.source)
                self.assertTrue(rule.explanation)
                self.assertTrue(rule.conditions_all or rule.conditions_any)

    def test_untraced_sources_are_labelled_as_such(self):
        """Part 10: do not name a text that may not contain the rule."""
        for rule in rules_for_profile("parashari_extended"):
            if rule.tradition in ("Variant reading", "Alternate reading",
                                  "Variant attribution"):
                with self.subTest(rule=rule.id):
                    self.assertNotIn("BPHS ch.", rule.source)

    def test_variants_declare_their_parent(self):
        core = {rule.id for rule in rules_for_profile("parashari")}
        for rule in rules_for_profile("parashari_extended"):
            if rule.variant_of:
                with self.subTest(rule=rule.id):
                    self.assertIn(rule.variant_of, core)
                    self.assertNotEqual(rule.id, rule.variant_of)

    def test_vipareeta_strict_profile_swaps_rather_than_duplicates(self):
        """
        Renamed in V1.3: this profile is about ONE strict reading of
        Vipareeta Raja Yoga, not about evidence. `parashari_strict` now means
        the evidence-gated profile — see test_sources.py.
        """
        strict = {r.id for r in rules_for_profile("parashari_vipareeta_strict")}
        self.assertNotIn("vipareeta_harsha", strict)
        self.assertIn("vipareeta_harsha_strict", strict)


class VipareetaRajaYogaTest(unittest.TestCase):
    """A dusthana lord fallen into a dusthana."""

    def test_harsha_forms_when_sixth_lord_is_in_a_dusthana(self):
        # Mesha Lagna: the 6th is Kanya, lord Budha. Put Budha in the 8th
        # (Vrishchika).
        features = features_for(MESHA, {"Budha": VRISHCHIKA, "Surya": MESHA})
        result = result_for("vipareeta_harsha", features)
        self.assertTrue(result.present)

    def test_absent_when_the_dusthana_lord_is_well_placed(self):
        # Budha (6th lord from Mesha) in the 1st.
        features = features_for(MESHA, {"Budha": MESHA, "Surya": VRISHABHA})
        self.assertFalse(result_for("vipareeta_harsha", features).present)

    def test_each_of_the_three_targets_its_own_house(self):
        for rule_id, house in (("vipareeta_harsha", 6),
                               ("vipareeta_sarala", 8),
                               ("vipareeta_vimala", 12)):
            rule = rule_by_id(rule_id)
            with self.subTest(rule=rule_id):
                self.assertEqual(rule.houses_involved, [house])

    def test_strict_reading_rejects_the_lords_own_dusthana(self):
        """
        Mesha Lagna: the 6th is Kanya, lord Budha. Budha in Kanya is the 6th
        lord in the 6th — accepted by the common reading, rejected by the
        strict one. This is exactly why they are separate rules.
        """
        features = features_for(MESHA, {"Budha": KANYA, "Surya": MESHA})
        self.assertTrue(result_for("vipareeta_harsha", features).present)
        self.assertFalse(
            result_for("vipareeta_harsha_strict", features,
                       profile="parashari_vipareeta_strict").present)

    def test_strict_reading_accepts_a_different_dusthana(self):
        features = features_for(MESHA, {"Budha": VRISHCHIKA, "Surya": MESHA})
        self.assertTrue(
            result_for("vipareeta_harsha_strict", features,
                       profile="parashari_vipareeta_strict").present)


class ParivartanaYogaTest(unittest.TestCase):

    def test_maha_parivartana(self):
        # Mesha Lagna: Mangal (1st/8th lord) in Vrishabha, Shukra (2nd/7th)
        # in Mesha — an exchange between the 1st and the 2nd.
        features = features_for(MESHA, {"Mangal": VRISHABHA, "Shukra": MESHA,
                                        "Surya": MITHUNA})
        result = result_for("parivartana_maha", features)
        self.assertTrue(result.present)
        self.assertEqual(sorted(result.planets), ["Mangal", "Shukra"])

    def test_dainya_parivartana_involves_a_dusthana(self):
        # Mesha Lagna: Budha rules the 3rd (Mithuna) and 6th (Kanya); Shani
        # rules the 10th (Makara) and 11th (Kumbha). Budha in Makara and
        # Shani in Kanya exchanges the 6th with the 10th.
        features = features_for(MESHA, {"Budha": MAKARA, "Shani": KANYA,
                                        "Surya": MESHA})
        self.assertTrue(result_for("parivartana_dainya", features).present)

    def test_absent_when_there_is_no_exchange(self):
        features = features_for(MESHA, {"Mangal": MESHA, "Shukra": VRISHABHA,
                                        "Surya": MITHUNA})
        for key in ("maha", "dainya", "khala"):
            with self.subTest(kind=key):
                self.assertFalse(
                    result_for(f"parivartana_{key}", features).present)


class LunarCompanyTest(unittest.TestCase):
    """Sunapha, Anapha, Durudhara — and their relationship to Kemadruma."""

    def isolated(self):
        """Chandra in Mesha with the 2nd and 12th from it kept empty."""
        return features_for(
            KARKA, {"Chandra": MESHA, "Surya": SIMHA, "Mangal": SIMHA,
                    "Budha": KANYA, "Guru": TULA, "Shukra": KANYA,
                    "Shani": DHANU})

    def test_sunapha_needs_the_second_from_the_moon(self):
        features = features_for(KARKA, {"Chandra": MESHA, "Guru": VRISHABHA,
                                        "Surya": SIMHA})
        self.assertTrue(result_for("sunapha", features).present)
        self.assertFalse(result_for("anapha", features).present)

    def test_anapha_needs_the_twelfth_from_the_moon(self):
        features = features_for(KARKA, {"Chandra": MESHA, "Guru": MEENA,
                                        "Surya": SIMHA})
        self.assertTrue(result_for("anapha", features).present)
        self.assertFalse(result_for("sunapha", features).present)

    def test_durudhara_needs_both(self):
        both = features_for(KARKA, {"Chandra": MESHA, "Guru": VRISHABHA,
                                    "Shukra": MEENA, "Surya": SIMHA})
        self.assertTrue(result_for("durudhara", both).present)
        self.assertTrue(result_for("sunapha", both).present)
        self.assertTrue(result_for("anapha", both).present)

        one_only = features_for(KARKA, {"Chandra": MESHA, "Guru": VRISHABHA,
                                        "Surya": SIMHA})
        self.assertFalse(result_for("durudhara", one_only).present)

    def test_surya_does_not_count_as_company(self):
        """The classical exclusion, shared with Kemadruma."""
        features = features_for(
            KARKA, {"Chandra": MESHA, "Surya": VRISHABHA, "Mangal": SIMHA,
                    "Budha": SIMHA, "Guru": TULA, "Shukra": SIMHA,
                    "Shani": DHANU})
        self.assertFalse(result_for("sunapha", features).present)

    def test_they_are_the_complement_of_kemadruma(self):
        """
        Kemadruma is exactly the absence of Sunapha and Anapha. A chart cannot
        show Kemadruma forming alongside either.
        """
        isolated = self.isolated()
        self.assertTrue(result_for("kemadruma", isolated).present)
        self.assertFalse(result_for("sunapha", isolated).present)
        self.assertFalse(result_for("anapha", isolated).present)


class SolarCompanyTest(unittest.TestCase):

    def test_vesi_and_vasi(self):
        second = features_for(MESHA, {"Surya": MESHA, "Guru": VRISHABHA,
                                      "Chandra": SIMHA})
        self.assertTrue(result_for("vesi", second).present)
        self.assertFalse(result_for("vasi", second).present)

        twelfth = features_for(MESHA, {"Surya": MESHA, "Guru": MEENA,
                                       "Chandra": SIMHA})
        self.assertTrue(result_for("vasi", twelfth).present)
        self.assertFalse(result_for("vesi", twelfth).present)

    def test_ubhayachari_needs_both(self):
        features = features_for(MESHA, {"Surya": MESHA, "Guru": VRISHABHA,
                                        "Shukra": MEENA, "Chandra": SIMHA})
        self.assertTrue(result_for("ubhayachari", features).present)

    def test_chandra_does_not_count_as_company(self):
        features = features_for(MESHA, {"Surya": MESHA, "Chandra": VRISHABHA})
        self.assertFalse(result_for("vesi", features).present)


class AdhiAndAmalaTest(unittest.TestCase):

    def test_adhi_yoga_needs_all_three_houses_from_the_moon(self):
        # Chandra in Mesha; the 6th, 7th and 8th from it are Kanya, Tula,
        # Vrishchika. Put the three benefics there.
        features = features_for(
            MESHA, {"Chandra": MESHA, "Budha": KANYA, "Shukra": TULA,
                    "Guru": VRISHCHIKA, "Surya": MESHA})
        self.assertTrue(result_for("adhi_yoga", features).present)

    def test_adhi_yoga_absent_when_one_house_is_empty(self):
        features = features_for(
            MESHA, {"Chandra": MESHA, "Budha": KANYA, "Shukra": TULA,
                    "Guru": MAKARA, "Surya": MESHA})
        result = result_for("adhi_yoga", features)
        self.assertFalse(result.present)
        self.assertTrue(any("empty" in c or "not every" in c
                            for c in result.conditions_failed))

    def test_adhi_from_lagna_is_a_separate_rule(self):
        self.assertIsNone(rule_by_id("adhi_yoga_from_lagna", "parashari"))
        variant = rule_by_id("adhi_yoga_from_lagna", "parashari_extended")
        self.assertIsNotNone(variant)
        self.assertEqual(variant.variant_of, "adhi_yoga")

    def test_amala_yoga_needs_a_benefic_in_the_tenth(self):
        features = features_for(MESHA, {"Guru": MAKARA, "Surya": MESHA})
        self.assertTrue(result_for("amala_yoga", features).present)

    def test_amala_absent_with_a_malefic_in_the_tenth(self):
        features = features_for(MESHA, {"Shani": MAKARA, "Surya": MESHA})
        self.assertFalse(result_for("amala_yoga", features).present)


class LakshmiAndSaraswatiTest(unittest.TestCase):

    def test_lakshmi_yoga_requires_both_lords_dignified(self):
        # Dhanu Lagna: the 9th is Simha (Surya), the 1st is Dhanu (Guru).
        # Surya in Simha (own) in the 9th, Guru in Dhanu (own) in the 1st.
        features = features_for(DHANU, {"Surya": SIMHA, "Guru": DHANU,
                                        "Chandra": MESHA})
        self.assertTrue(result_for("lakshmi_yoga", features).present)

    def test_lakshmi_absent_when_the_lagna_lord_is_undignified(self):
        features = features_for(DHANU, {"Surya": SIMHA, "Guru": VRISHABHA,
                                        "Chandra": MESHA})
        result = result_for("lakshmi_yoga", features)
        self.assertFalse(result.present)
        self.assertTrue(result.conditions_failed)

    def test_lakshmi_absent_when_the_ninth_lord_is_undignified(self):
        features = features_for(DHANU, {"Surya": TULA, "Guru": DHANU,
                                        "Chandra": MESHA})
        self.assertFalse(result_for("lakshmi_yoga", features).present)

    def test_saraswati_requires_all_three_benefics_well_placed(self):
        # Dhanu Lagna: Guru in Dhanu (1st, own), Shukra in Meena (4th),
        # Budha in Mithuna (7th).
        features = features_for(DHANU, {"Guru": DHANU, "Shukra": MEENA,
                                        "Budha": MITHUNA, "Surya": SIMHA})
        self.assertTrue(result_for("saraswati_yoga", features).present)

    def test_saraswati_absent_when_one_benefic_is_badly_placed(self):
        features = features_for(DHANU, {"Guru": DHANU, "Shukra": MEENA,
                                        "Budha": VRISHCHIKA, "Surya": SIMHA})
        self.assertFalse(result_for("saraswati_yoga", features).present)

    def test_saraswati_requires_guru_dignified(self):
        # All three in allowed houses, but Guru debilitated in Makara (2nd
        # from Dhanu).
        features = features_for(DHANU, {"Guru": MAKARA, "Shukra": MEENA,
                                        "Budha": MITHUNA, "Surya": SIMHA})
        result = result_for("saraswati_yoga", features)
        self.assertFalse(result.present)


class GajakesariVariantTest(unittest.TestCase):
    """Part 10: differing readings become separate profile ids."""

    def test_alternate_is_only_in_the_extended_profile(self):
        self.assertIsNone(rule_by_id("gajakesari_alternate", "parashari"))
        self.assertIsNotNone(
            rule_by_id("gajakesari_alternate", "parashari_extended"))

    def test_alternate_is_strictly_narrower(self):
        """
        Guru in a kendra from Chandra but not from the Lagna: the Parashari
        reading holds, the stricter one does not.
        """
        features = features_for(MESHA, {"Chandra": VRISHABHA, "Guru": SIMHA,
                                        "Surya": KANYA})
        self.assertTrue(result_for("gajakesari", features).present)
        self.assertFalse(
            result_for("gajakesari_alternate", features,
                       profile="parashari_extended").present)

    def test_both_hold_when_the_stricter_conditions_are_met(self):
        # Karka Lagna: Guru in Karka (1st, a kendra from the Lagna) and
        # Chandra in Karka too, so Guru is the 1st from Chandra — a kendra.
        # Guru in Karka is exalted.
        features = features_for(KARKA, {"Guru": KARKA, "Chandra": KARKA,
                                        "Surya": KANYA})
        self.assertTrue(result_for("gajakesari", features).present)
        self.assertTrue(
            result_for("gajakesari_alternate", features,
                       profile="parashari_extended").present)


class KemadrumaBhangaRuleTest(unittest.TestCase):
    """Each bhanga clause is also findable on its own."""

    def test_bhanga_rules_require_kemadruma_to_have_formed(self):
        """A chart with no Kemadruma cannot show a Kemadruma Bhanga."""
        features = features_for(KARKA, {"Chandra": MESHA, "Guru": VRISHABHA,
                                        "Surya": SIMHA})
        self.assertFalse(result_for("kemadruma", features).present)
        for key in ("kendra_lagna", "kendra_moon", "moon_kendra",
                    "benefic_drishti"):
            with self.subTest(clause=key):
                self.assertFalse(
                    result_for(f"kemadruma_bhanga_{key}", features).present)

    def test_bhanga_rule_fires_alongside_a_cancelled_kemadruma(self):
        features = features_for(
            MESHA, {"Chandra": MESHA, "Surya": SIMHA, "Mangal": SIMHA,
                    "Budha": KANYA, "Guru": TULA, "Shukra": KANYA,
                    "Shani": DHANU})
        kemadruma = result_for("kemadruma", features)
        self.assertEqual(kemadruma.status, YogaStatus.PRESENT_BUT_CANCELLED)
        bhanga = result_for("kemadruma_bhanga_moon_kendra", features)
        self.assertTrue(bhanga.present)

    def test_bhanga_rules_do_not_replace_the_kemadruma_result(self):
        """Both must be reported — the bhanga is additional, not a substitute."""
        features = features_for(
            MESHA, {"Chandra": MESHA, "Surya": SIMHA, "Mangal": SIMHA,
                    "Budha": KANYA, "Guru": TULA, "Shukra": KANYA,
                    "Shani": DHANU})
        from engine.rules import evaluate_rules
        present = {r.id for r in evaluate_rules(features) if r.present}
        self.assertIn("kemadruma", present)
        self.assertTrue(any(i.startswith("kemadruma_bhanga_")
                            for i in present))


class RobustnessTest(unittest.TestCase):
    """Every new rule must survive unusual charts without raising."""

    def test_every_rule_evaluates_on_many_charts(self):
        for profile in RULE_PROFILES:
            rules = rules_for_profile(profile)
            for lagna in range(0, 12, 3):
                for shift in (0, 5, 9):
                    longitudes = {
                        planet: ((lagna + shift + index) % 12) * 30.0 + 15.0
                        for index, planet in enumerate(ALL_GRAHAS)
                    }
                    chart = JyotishChart.from_sidereal_longitudes(
                        lagna_lon=lagna * 30.0 + 15.0, planet_lons=longitudes)
                    features = build_chart_features(chart)
                    with self.subTest(profile=profile, lagna=lagna, shift=shift):
                        for rule in rules:
                            rule.evaluate(features)

    def test_rules_survive_a_chart_with_one_graha(self):
        features = features_for(MESHA, {"Surya": SIMHA})
        for rule in rules_for_profile("parashari_extended"):
            with self.subTest(rule=rule.id):
                rule.evaluate(features)

    def test_rules_survive_all_grahas_in_one_rashi(self):
        features = features_for(
            MESHA, {p: 100.0 + i * 0.4 for i, p in enumerate(ALL_GRAHAS)})
        for rule in rules_for_profile("parashari_extended"):
            with self.subTest(rule=rule.id):
                rule.evaluate(features)


if __name__ == "__main__":
    unittest.main(verbosity=2)
