"""
Documented worked example as a regression case (Part 13)
--------------------------------------------------------
    30 August 1988, 20:18 local, Jaipur, Lahiri ayanamsha, true node.

This is the example DOCUMENTATION.md publishes, so it is pinned here: every
position, nakshatra, pada, motion state, house, D9, D10 and Yoga condition is
asserted, and any change to the engine that moves one of them has to be a
deliberate decision rather than a surprise.

Where a value is checked against the Swiss Ephemeris it is checked at the
tolerance the engine's MEASURED accuracy supports, not tighter. Saturn is the
case that matters: it sits at 2°11' of Dhanu with a worst-case error near 10
arcmin, so its rashi is safe but its exact degree is not pinned hard.

The three Yoga claims the V1 documentation made are re-evaluated here through
the new engine, which is the substance of Part 13:

  * Bhadra Mahapurusha — confirmed, and now shown to rest on Budha being both
    exalted AND in its own rashi in a kendra.
  * "Raja Yoga" — the V1 engine reported this because a dignified graha sat in
    a kendra, which is not a Raja Yoga. Genuine Raja Yogas are present in this
    chart, but for a different and stated reason: real kendra-trikona lord
    relationships.
  * Kemadruma — forms, but is cancelled four times over. V1 reported it as
    simply present, which inverted its meaning.
"""

# Phase 2 (V1.1).

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.location import resolve_location
from engine.planets import JyotishChart, jde_from_datetime
from engine.rules import YogaStatus, evaluate_rules, present_yogas, rule_by_id

BIRTH_LOCAL = datetime.datetime(1988, 8, 30, 20, 18)
BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)

# Published in DOCUMENTATION.md section 10.
EXPECTED = {
    #          rashi        nakshatra           pada  house  retro
    "Surya":   ("Simha",     "Purva Phalguni",   1,    6,    False),
    "Chandra": ("Meena",     "Revati",           4,    1,    False),
    "Mangal":  ("Meena",     "Revati",           1,    1,    True),
    "Budha":   ("Kanya",     "Uttara Phalguni",  3,    7,    False),
    "Guru":    ("Vrishabha", "Rohini",           1,    3,    False),
    "Shukra":  ("Mithuna",   "Punarvasu",        3,    4,    False),
    "Shani":   ("Dhanu",     "Mula",             1,    10,   False),
    "Rahu":    ("Kumbha",    "Purva Bhadrapada", 1,    12,   False),
    "Ketu":    ("Simha",     "Purva Phalguni",   3,    6,    False),
}

# Degrees within the rashi. These are the SWISS EPHEMERIS values, held
# separately from the astrological expectations below so that an astronomical
# reference and a rule outcome can never be confused for one another.
#
# Guru and Shani changed in V1.2: the V1 engine put them at 11.528 and 2.188,
# which were wrong by 6.6 and 2.6 arcmin respectively. VSOP87A gives 11.4174
# and 2.2304, matching the reference to 0.3" and 1.1".
EXPECTED_DEGREES = {
    "Surya": 13.7362, "Chandra": 28.1197, "Mangal": 17.6522, "Budha": 5.9621,
    "Guru": 11.4174, "Shukra": 28.1540, "Shani": 2.2304,
}

# Degree tolerance per graha, from the measured accuracy profile. Jupiter and
# Saturn are loose because the Keplerian element set is loose for them.
# Per-graha tolerance, from the measured accuracy profile. Jupiter and Saturn
# are no longer the loose ones — Mars is now the least accurate body.
DEGREE_TOLERANCE = {
    "Surya": 0.01, "Chandra": 0.005, "Mangal": 0.005, "Budha": 0.005,
    "Guru": 0.005, "Shukra": 0.01, "Shani": 0.005,
}

EXPECTED_D9 = {
    "Surya": "Simha", "Chandra": "Meena", "Mangal": "Dhanu", "Budha": "Kumbha",
    "Guru": "Mesha", "Shukra": "Mithuna", "Shani": "Mesha",
}

EXPECTED_D10 = {
    "Surya": "Dhanu", "Chandra": "Simha", "Mangal": "Mesha",
    "Budha": "Mithuna", "Guru": "Mesha", "Shukra": "Meena", "Shani": "Dhanu",
}


class BirthDataTest(unittest.TestCase):

    def test_jaipur_resolves_without_ambiguity(self):
        location = resolve_location(place="Jaipur", local_datetime=BIRTH_LOCAL)
        self.assertAlmostEqual(location.latitude, 26.9124, places=4)
        self.assertAlmostEqual(location.longitude, 75.7873, places=4)
        self.assertAlmostEqual(location.utc_offset_at_birth, 5.5)

    def test_local_time_converts_to_the_documented_utc(self):
        location = resolve_location(place="Jaipur", local_datetime=BIRTH_LOCAL)
        self.assertEqual(location.to_utc(BIRTH_LOCAL), BIRTH_UTC)


class ChartRegressionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chart = JyotishChart(
            jde=jde_from_datetime(BIRTH_UTC),
            lat=26.9124, lon=75.7873,
            ayanamsha_system="lahiri", true_node=True)
        cls.features = build_chart_features(cls.chart)

    # ── Lagna ────────────────────────────────────────────────────────────────

    def test_lagna(self):
        lagna = self.chart.lagna
        self.assertEqual(lagna.rashi, "Meena")
        self.assertAlmostEqual(lagna.degree_in_rashi, 15.784, delta=0.02)
        self.assertEqual(lagna.nakshatra, "Uttara Bhadrapada")
        self.assertEqual(lagna.pada, 4)
        self.assertEqual(lagna.rashi_lord, "Guru")

    def test_ayanamsha(self):
        """
        The V1 documentation printed 23.6946° for this moment. That was wrong
        by about 15 arcseconds: the Swiss Ephemeris gives 23.6987294 and the
        engine agrees to well under a milliarcsecond. The documented figure
        has been corrected; this pins the right one.
        """
        self.assertAlmostEqual(self.chart.ayanamsha, 23.6987294, delta=0.0001)

    def test_delta_t(self):
        self.assertAlmostEqual(self.chart.delta_t, 56.1, delta=1.0)

    # ── the nine grahas ──────────────────────────────────────────────────────

    def test_all_nine_grahas_present(self):
        self.assertEqual(sorted(self.chart.planets), sorted(EXPECTED))

    def test_rashi_nakshatra_and_pada(self):
        for name, (rashi, nakshatra, pada, _house, _retro) in EXPECTED.items():
            position = self.chart.planets[name]
            with self.subTest(graha=name):
                self.assertEqual(position.rashi, rashi)
                self.assertEqual(position.nakshatra, nakshatra)
                self.assertEqual(position.pada, pada)

    def test_degrees_within_measured_tolerance(self):
        for name, expected in EXPECTED_DEGREES.items():
            with self.subTest(graha=name):
                self.assertAlmostEqual(
                    self.chart.planets[name].degree_in_rashi, expected,
                    delta=DEGREE_TOLERANCE[name])

    def test_houses_from_lagna(self):
        for name, (_r, _n, _p, house, _retro) in EXPECTED.items():
            with self.subTest(graha=name):
                self.assertEqual(self.chart.house_of(name), house)
                self.assertEqual(self.features.planets[name].house, house)

    def test_mangal_is_retrograde(self):
        """
        Independently verifiable: Mars reached opposition on 28 September 1988,
        so it was retrograde in Pisces through late August.
        """
        self.assertTrue(self.chart.planets["Mangal"].is_retrograde)

    def test_shani_reads_as_stationary(self):
        """
        Saturn turned direct on 11 September 1988, twelve days after this
        birth, so its apparent motion here is below the engine's resolution
        and it is reported as stationary rather than as direct or retrograde.
        That is an honest statement of the engine's limit, not an ephemeris
        claim — see AUDIT.md.
        """
        shani = self.chart.planets["Shani"]
        self.assertTrue(shani.is_stationary)
        self.assertLess(abs(shani.speed), 0.005)

    def test_other_grahas_are_direct(self):
        for name, (_r, _n, _p, _h, retro) in EXPECTED.items():
            if name in ("Mangal", "Shani", "Rahu", "Ketu"):
                continue
            with self.subTest(graha=name):
                self.assertEqual(self.chart.planets[name].is_retrograde, retro)

    def test_budha_is_exalted(self):
        self.assertEqual(self.chart.planets["Budha"].dignity, "Uchcha")

    def test_surya_is_in_moolatrikona(self):
        self.assertEqual(self.chart.planets["Surya"].dignity, "Moolatrikona")

    def test_nodes_are_opposite(self):
        separation = abs(self.chart.planets["Rahu"].longitude
                         - self.chart.planets["Ketu"].longitude)
        self.assertAlmostEqual(separation, 180.0, places=6)

    def test_no_graha_is_combust(self):
        """Ketu is 6.65° from the Sun but is a shadow graha and never burns."""
        for name in EXPECTED:
            with self.subTest(graha=name):
                self.assertFalse(self.chart.planets[name].is_combust)
        ketu = self.features.planets["Ketu"]
        self.assertLess(ketu.sun_separation, 12.0)
        self.assertIsNone(ketu.combustion_orb)

    # ── divisional charts ────────────────────────────────────────────────────

    def test_d9_placements(self):
        for name, expected in EXPECTED_D9.items():
            with self.subTest(graha=name):
                self.assertEqual(
                    self.features.planets[name].vargas["D9"].sign_name, expected)

    def test_d10_placements(self):
        for name, expected in EXPECTED_D10.items():
            with self.subTest(graha=name):
                self.assertEqual(
                    self.features.planets[name].vargas["D10"].sign_name, expected)

    def test_vargottama_grahas(self):
        vargottama = {name for name, planet in self.features.planets.items()
                      if planet.vargottama}
        self.assertEqual(vargottama, {"Surya", "Chandra", "Shukra"})

    # ── features ─────────────────────────────────────────────────────────────

    def test_house_lords_for_this_lagna(self):
        self.assertEqual(self.features.house_lords, {
            1: "Guru", 2: "Mangal", 3: "Shukra", 4: "Budha", 5: "Chandra",
            6: "Surya", 7: "Budha", 8: "Shukra", 9: "Mangal", 10: "Guru",
            11: "Shani", 12: "Shani"})

    def test_chandra_and_mangal_share_the_first_house(self):
        conjunctions = [c for c in self.features.conjunctions
                        if {c.planet1, c.planet2} == {"Chandra", "Mangal"}]
        self.assertEqual(len(conjunctions), 1)
        self.assertTrue(conjunctions[0].same_sign)
        self.assertEqual(conjunctions[0].house, 1)

    def test_speeds_are_measured_for_a_calculated_chart(self):
        self.assertEqual(self.features.warnings, [])


class YogaRegressionTest(unittest.TestCase):
    """Part 13: the V1 Yoga claims re-evaluated through the new engine."""

    @classmethod
    def setUpClass(cls):
        chart = JyotishChart(
            jde=jde_from_datetime(BIRTH_UTC), lat=26.9124, lon=75.7873,
            ayanamsha_system="lahiri", true_node=True)
        cls.features = build_chart_features(chart)
        cls.results = evaluate_rules(cls.features)
        cls.by_id = {result.id: result for result in cls.results}

    def test_bhadra_mahapurusha_confirmed(self):
        """
        The V1 report claimed Bhadra. It holds — and the new engine shows why:
        Budha is exalted AND in its own rashi (Kanya is both), in the 7th.
        """
        result = self.by_id["mahapurusha_bhadra"]
        self.assertTrue(result.present)
        self.assertEqual(result.status, YogaStatus.PRESENT_AND_STRONG)
        self.assertEqual(result.cancellations_found, [])
        self.assertTrue(any("exalted" in c for c in result.conditions_met))
        self.assertTrue(any("7th" in c for c in result.conditions_met))

    def test_no_other_mahapurusha_forms(self):
        for key in ("ruchaka", "hamsa", "malavya", "shasha"):
            with self.subTest(yoga=key):
                self.assertFalse(self.by_id[f"mahapurusha_{key}"].present)

    def test_chandra_mangala_confirmed(self):
        result = self.by_id["chandra_mangala"]
        self.assertTrue(result.present)
        self.assertTrue(any("share one rashi" in c
                            for c in result.conditions_met))

    def test_budha_aditya_absent(self):
        """Surya is in Simha and Budha in Kanya — different rashis."""
        self.assertFalse(self.by_id["budha_aditya"].present)

    def test_gajakesari_absent(self):
        """Guru is the 3rd from Chandra, not a kendra."""
        result = self.by_id["gajakesari"]
        self.assertFalse(result.present)
        self.assertTrue(any("not a kendra" in c
                            for c in result.conditions_failed))

    def test_kemadruma_forms_but_is_cancelled(self):
        """
        The V1 report listed Kemadruma as simply present, which reads as an
        affliction. It forms, but four separate bhanga clauses cancel it.
        """
        result = self.by_id["kemadruma"]
        self.assertTrue(result.present)
        self.assertEqual(result.status, YogaStatus.PRESENT_BUT_CANCELLED)
        self.assertFalse(result.effective)
        self.assertEqual(len(result.cancellations_found), 4)
        self.assertTrue(all("Bhanga" in c for c in result.cancellations_found))

    def test_genuine_raja_yogas_are_present_and_named(self):
        """
        V1 reported a generic "Raja Yoga" because a dignified graha sat in a
        kendra. Real Raja Yogas do exist here, but each names the kendra lord,
        the trikona lord and the relationship between them.
        """
        raja = [r for r in self.results if r.category == "raja" and r.present]
        self.assertTrue(raja, "expected genuine kendra-trikona Raja Yogas")
        for result in raja:
            with self.subTest(rule=result.id):
                self.assertTrue(result.conditions_met)
                self.assertTrue(result.houses or result.planets)
                self.assertIn("BPHS", result.source)

    def test_the_v1_generic_raja_yoga_rule_no_longer_exists(self):
        for result in self.results:
            with self.subTest(rule=result.id):
                self.assertNotEqual(result.name, "Raja Yoga")
                self.assertNotEqual(result.name, "Dhana Yoga")

    def test_budha_participates_in_the_raja_yogas(self):
        """
        Budha owns the 4th and 7th — both kendras — and aspects Chandra (5th
        lord) and Mangal (9th lord) from the 7th. That is the actual basis of
        the Raja Yoga in this chart.
        """
        raja = [r for r in self.results if r.category == "raja" and r.present]
        self.assertTrue(any("Budha" in r.planets for r in raja))

    def test_dhana_yogas_rest_on_lord_relationships(self):
        dhana = [r for r in self.results if r.category == "dhana" and r.present]
        for result in dhana:
            with self.subTest(rule=result.id):
                self.assertTrue(result.conditions_met)

    def test_no_neecha_bhanga_since_nothing_is_debilitated(self):
        for result in self.results:
            if not result.id.startswith("neecha_bhanga"):
                continue
            with self.subTest(rule=result.id):
                self.assertFalse(result.present)

    def test_every_present_yoga_cites_a_source(self):
        for result in present_yogas(self.features):
            with self.subTest(rule=result.id):
                self.assertTrue(result.source)
                self.assertTrue(result.tradition)
                self.assertTrue(result.explanation)

    def test_result_counts_are_stable(self):
        """
        Pins the overall shape of the analysis. A change here is fine, but it
        must be a deliberate one.
        """
        present = [r for r in self.results if r.present]
        cancelled = [r for r in present
                     if r.status == YogaStatus.PRESENT_BUT_CANCELLED]
        # V1.1 found 9 with a 90-rule catalog; V1.2 extends the catalog to 110
        # rules, so more combinations are detected in the same chart. The
        # count is pinned so a change has to be deliberate.
        self.assertEqual(len(present), 15)
        self.assertEqual(len(cancelled), 1)
        self.assertEqual(cancelled[0].id, "kemadruma")


if __name__ == "__main__":
    unittest.main(verbosity=2)
