"""
Shadbala (V1.4 Parts 3-9, 24)
-------------------------------
Component-level tests, because a Shadbala total is a sum of six things and a
test that only checks the total would pass with two errors cancelling.

Where the witness works an example, the example is the test: BPHS 27.1 gives
the Sun at Pisces 12°15' against a debilitation point of Libra 10° yielding
50.75 virupas, and BPHS 27.7 gives Saturn on the 7th cusp at one rupa and on
the ascendant at zero. Both are asserted directly.
"""

# V1.4.

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import JyotishChart, jde_from_datetime
from engine.strength import (
    NAISARGIKA_VIRUPAS, REQUIRED_VIRUPAS, SHADBALA_GRAHAS, VIRUPAS_PER_RUPA,
    chesta_bala, compute_shadbala, dig_bala, drik_bala, kendradi_bala,
    motional_state, naisargika_bala, nathonnatha_bala, ojhayugma_bala,
    paksha_bala, saptavargaja_bala, sthana_bala, uchcha_bala, weakest_status,
)
from engine.strength.sthana_bala import SAPTAVARGA_CHARTS, drekkana_bala

BIRTH_LOCAL = datetime.datetime(1988, 8, 30, 20, 18)
BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)


def natal():
    return JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                        lat=26.9124, lon=75.7873)


class UchchaBalaTest(unittest.TestCase):
    """BPHS 27.1, including the witness's own worked example."""

    def test_witness_worked_example(self):
        """
        The witness: Sun at Pisces 12°15' (342.25°), deep debilitation Libra
        10° (190°), giving 152°15' / 3 = 50.75 virupas.
        """
        component = uchcha_bala("Surya", 342.25)
        self.assertAlmostEqual(component.value_virupa, 50.75, places=6)

    def test_maximum_at_exact_exaltation(self):
        """The Sun exalts at Mesha 10°, exactly opposite its debilitation."""
        self.assertAlmostEqual(uchcha_bala("Surya", 10.0).value_virupa,
                               60.0, places=6)

    def test_zero_at_exact_debilitation(self):
        self.assertAlmostEqual(uchcha_bala("Surya", 190.0).value_virupa,
                               0.0, places=6)

    def test_never_exceeds_one_rupa(self):
        for planet in SHADBALA_GRAHAS:
            for degrees in range(0, 360, 3):
                with self.subTest(planet=planet, longitude=degrees):
                    value = uchcha_bala(planet, float(degrees)).value_virupa
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLessEqual(value, 60.0 + 1e-9)

    def test_symmetric_about_the_axis(self):
        """Equal distances either side of debilitation give equal strength."""
        for offset in (10.0, 45.0, 120.0):
            with self.subTest(offset=offset):
                self.assertAlmostEqual(
                    uchcha_bala("Guru", (95.0 + offset) % 360).value_virupa,
                    uchcha_bala("Guru", (95.0 - offset) % 360).value_virupa,
                    places=6)

    def test_boundary_interpolation_is_continuous(self):
        """Part 4: the interpolation must not jump at the fold at 180°."""
        previous = uchcha_bala("Shani", 0.0).value_virupa
        for degrees in range(1, 360):
            value = uchcha_bala("Shani", float(degrees)).value_virupa
            with self.subTest(longitude=degrees):
                self.assertLess(abs(value - previous), 0.5)
            previous = value


class SaptavargajaBalaTest(unittest.TestCase):

    def test_seven_vargas_are_the_named_ones(self):
        self.assertEqual(SAPTAVARGA_CHARTS,
                         ("D1", "D2", "D3", "D7", "D9", "D12", "D30"))

    def test_one_subcomponent_per_varga(self):
        component = saptavargaja_bala("Guru", 100.0, {"Guru": 1}, {"Guru": 3})
        self.assertEqual(len(component.subcomponents), 7)

    def test_total_is_within_the_classical_range(self):
        """Seven vargas at 2 to 45 virupas each: 14 to 315."""
        chart = natal()
        features = build_chart_features(chart)
        houses = {n: g.house for n, g in features.planets.items()}
        signs = {n: g.sign for n, g in features.planets.items()}
        for planet in SHADBALA_GRAHAS:
            position = chart.planets[planet]
            with self.subTest(planet=planet):
                value = saptavargaja_bala(planet, position.longitude,
                                          houses, signs).value_virupa
                self.assertGreaterEqual(value, 14.0)
                self.assertLessEqual(value, 315.0)

    def test_own_sign_scores_higher_than_enemy_sign(self):
        houses = {"Surya": 1, "Shani": 7}
        signs = {"Surya": 4, "Shani": 9}
        own = saptavargaja_bala("Surya", 130.0, houses, signs)       # Simha
        enemy = saptavargaja_bala("Surya", 280.0, houses, signs)     # Makara
        self.assertGreater(own.value_virupa, enemy.value_virupa)


class OjhayugmaAndKendradiTest(unittest.TestCase):

    def test_ojhayugma_is_fifteen_per_placement(self):
        """
        Fifteen, not thirty-five. The witness's verse says a quarter rupa;
        its explanatory note says 35, which is not a quarter of 60 and is an
        OCR or typesetting error. The verse is followed.
        """
        component = ojhayugma_bala("Surya", 10.0)
        for part in component.subcomponents:
            with self.subTest(part=part.name):
                self.assertIn(part.value_virupa, (0.0, 15.0))
        self.assertLessEqual(component.value_virupa, 30.0)

    def test_venus_and_moon_gain_in_even_rashis(self):
        # Vrishabha (index 1) is an even rashi.
        self.assertGreater(ojhayugma_bala("Shukra", 40.0).value_virupa, 0.0)
        # Mesha (index 0) is odd, so Venus gains nothing there by rashi.
        rashi_part = [p for p in ojhayugma_bala("Shukra", 10.0).subcomponents
                      if p.name == "ojhayugma_rashi"][0]
        self.assertEqual(rashi_part.value_virupa, 0.0)

    def test_others_gain_in_odd_rashis(self):
        rashi_part = [p for p in ojhayugma_bala("Surya", 10.0).subcomponents
                      if p.name == "ojhayugma_rashi"][0]
        self.assertEqual(rashi_part.value_virupa, 15.0)

    def test_kendradi_values(self):
        for house, expected in ((1, 60.0), (4, 60.0), (7, 60.0), (10, 60.0),
                                (2, 30.0), (5, 30.0), (8, 30.0), (11, 30.0),
                                (3, 15.0), (6, 15.0), (9, 15.0), (12, 15.0)):
            with self.subTest(house=house):
                self.assertEqual(kendradi_bala("Guru", house).value_virupa,
                                 expected)

    def test_drekkana_by_gender_group(self):
        # Male grahas gain in the first decanate.
        self.assertEqual(drekkana_bala("Surya", 5.0).value_virupa, 15.0)
        self.assertEqual(drekkana_bala("Surya", 15.0).value_virupa, 0.0)
        # Female in the second.
        self.assertEqual(drekkana_bala("Shukra", 15.0).value_virupa, 15.0)
        # Neutral in the third.
        self.assertEqual(drekkana_bala("Budha", 25.0).value_virupa, 15.0)


class DigBalaTest(unittest.TestCase):
    """BPHS 27.7, including the witness's worked example."""

    ASC = 100.0
    MC = (ASC + 270.0) % 360.0

    def test_witness_example_saturn(self):
        """
        "Saturn exactly on the 7th cusp gets 1 Rupa, and exactly on the
        ascending degree gets zero Virupa."
        """
        on_seventh = dig_bala("Shani", (self.ASC + 180) % 360, self.ASC,
                              midheaven=self.MC)
        on_ascendant = dig_bala("Shani", self.ASC, self.ASC, midheaven=self.MC)
        self.assertAlmostEqual(on_seventh.value_virupa, 60.0, places=6)
        self.assertAlmostEqual(on_ascendant.value_virupa, 0.0, places=6)

    def test_each_graha_peaks_in_its_stated_direction(self):
        angles = {1: self.ASC, 4: (self.MC + 180) % 360,
                  7: (self.ASC + 180) % 360, 10: self.MC}
        for planet, house in (("Surya", 10), ("Mangal", 10), ("Guru", 1),
                              ("Budha", 1), ("Shukra", 4), ("Chandra", 4),
                              ("Shani", 7)):
            with self.subTest(planet=planet):
                value = dig_bala(planet, angles[house], self.ASC,
                                 midheaven=self.MC).value_virupa
                self.assertAlmostEqual(value, 60.0, places=6)

    def test_intermediate_arc_is_proportional(self):
        """Ninety degrees from the weak point is exactly half strength."""
        quarter = (self.ASC + 90.0) % 360.0
        self.assertAlmostEqual(
            dig_bala("Shani", quarter, self.ASC, midheaven=self.MC).value_virupa,
            30.0, places=6)

    def test_range_is_zero_to_sixty_everywhere(self):
        for planet in SHADBALA_GRAHAS:
            for degrees in range(0, 360, 5):
                with self.subTest(planet=planet, longitude=degrees):
                    value = dig_bala(planet, float(degrees), self.ASC,
                                     midheaven=self.MC).value_virupa
                    self.assertGreaterEqual(value, -1e-9)
                    self.assertLessEqual(value, 60.0 + 1e-9)

    def test_missing_midheaven_is_flagged_as_an_approximation(self):
        """Part 5: the cusp convention must be stated, not assumed."""
        exact = dig_bala("Surya", 200.0, self.ASC, midheaven=self.MC)
        approximate = dig_bala("Surya", 200.0, self.ASC, midheaven=None)
        self.assertFalse(exact.is_approximation)
        self.assertTrue(approximate.is_approximation)
        self.assertIn("equator", approximate.approximation_note)

    def test_bhava_madhyas_override_the_angles(self):
        madhyas = {house: (house - 1) * 30.0 for house in range(1, 13)}
        component = dig_bala("Shani", 0.0, self.ASC, midheaven=self.MC,
                             bhava_madhyas=madhyas)
        self.assertIn("bhava_madhya", component.calculation_profile)


class KalaBalaTest(unittest.TestCase):

    def test_mercury_always_has_full_nathonnatha(self):
        for hour in (0, 6, 12, 18, 23):
            with self.subTest(hour=hour):
                component = nathonnatha_bala(
                    "Budha", datetime.datetime(2000, 1, 1, hour))
                self.assertAlmostEqual(component.value_virupa, 60.0)

    def test_day_and_night_groups_are_complementary(self):
        moment = datetime.datetime(2000, 1, 1, 9, 0)
        day = nathonnatha_bala("Surya", moment).value_virupa
        night = nathonnatha_bala("Chandra", moment).value_virupa
        self.assertAlmostEqual(day + night, 60.0, places=6)

    def test_nathonnatha_peaks_at_noon_and_midnight(self):
        noon = nathonnatha_bala("Surya", datetime.datetime(2000, 1, 1, 12))
        midnight = nathonnatha_bala("Chandra", datetime.datetime(2000, 1, 1, 0))
        self.assertAlmostEqual(noon.value_virupa, 60.0, places=6)
        self.assertAlmostEqual(midnight.value_virupa, 60.0, places=6)

    def test_paksha_bala_benefic_and_malefic_are_complementary(self):
        benefic = paksha_bala("Guru", 0.0, 90.0).value_virupa
        malefic = paksha_bala("Shani", 0.0, 90.0).value_virupa
        self.assertAlmostEqual(benefic + malefic, 60.0, places=6)

    def test_moon_paksha_bala_is_doubled(self):
        """The witness states this explicitly."""
        moon = paksha_bala("Chandra", 0.0, 180.0).value_virupa
        self.assertAlmostEqual(moon, 120.0, places=6)

    def test_mercury_counts_as_malefic_in_malefic_company(self):
        """
        An elongation of 150 degrees, not 90: at exactly 90 the benefic value
        is 30 and the malefic complement is also 30, so the two readings
        coincide and the test would prove nothing.
        """
        alone = paksha_bala("Budha", 0.0, 150.0, conjunct_malefic=False)
        joined = paksha_bala("Budha", 0.0, 150.0, conjunct_malefic=True)
        self.assertAlmostEqual(alone.value_virupa, 50.0, places=6)
        self.assertAlmostEqual(joined.value_virupa, 10.0, places=6)

    def test_varsha_and_masa_are_flagged_as_approximations(self):
        """
        Part 6: an approximated subcomponent must say so rather than be
        quietly dropped or quietly guessed.
        """
        from engine.strength import varsha_masa_dina_hora_bala
        component = varsha_masa_dina_hora_bala("Guru", BIRTH_LOCAL)
        by_name = {p.name: p for p in component.subcomponents}
        self.assertTrue(by_name["varsha_bala"].is_approximation)
        self.assertTrue(by_name["masa_bala"].is_approximation)
        self.assertIn("Ahargana", by_name["varsha_bala"].approximation_note)
        # Dina and hora are exact.
        self.assertFalse(by_name["dina_bala"].is_approximation)
        self.assertFalse(by_name["hora_bala"].is_approximation)

    def test_exactly_one_graha_holds_each_of_dina_and_hora(self):
        from engine.strength import varsha_masa_dina_hora_bala
        for name in ("dina_bala", "hora_bala"):
            holders = [
                planet for planet in SHADBALA_GRAHAS
                if any(p.name == name and p.value_virupa > 0
                       for p in varsha_masa_dina_hora_bala(
                           planet, BIRTH_LOCAL).subcomponents)]
            with self.subTest(component=name):
                self.assertEqual(len(holders), 1)


class ChestaBalaTest(unittest.TestCase):
    """Part 7: motional state must come from measured speed."""

    def test_sun_takes_its_ayana_bala(self):
        from engine.strength.models import BalaComponent
        ayana = BalaComponent(name="ayana_bala", value_virupa=42.0,
                              calculation_profile="x")
        component = chesta_bala("Surya", 0.9, False, ayana_bala=ayana)
        self.assertAlmostEqual(component.value_virupa, 42.0)

    def test_moon_takes_its_paksha_bala(self):
        from engine.strength.models import BalaComponent
        paksha = BalaComponent(name="paksha_bala", value_virupa=77.0,
                               calculation_profile="x")
        component = chesta_bala("Chandra", 13.0, False, paksha_bala=paksha)
        self.assertAlmostEqual(component.value_virupa, 77.0)

    def test_retrograde_is_read_from_speed_not_from_signs(self):
        retrograde = chesta_bala("Shani", -0.05, False)
        direct = chesta_bala("Shani", 0.05, False)
        self.assertEqual(motional_state("Shani", -0.05, False), "vakra")
        self.assertGreater(retrograde.value_virupa, direct.value_virupa)

    def test_stationary_is_a_distinct_state(self):
        """
        Part 7 asks for explicit stationary edge cases. When the engine
        cannot resolve direction it must say so, not round to direct.
        """
        component = chesta_bala("Shani", 0.0001, True)
        self.assertEqual(motional_state("Shani", 0.0001, True), "vikala")
        self.assertIn("cannot resolve", component.detail)

    def test_stationary_overrides_a_negative_speed(self):
        self.assertEqual(motional_state("Guru", -0.0001, True), "vikala")

    def test_speed_classification_is_monotonic_in_speed(self):
        states = [motional_state("Budha", speed, False)
                  for speed in (0.1, 0.7, 1.383, 1.6, 2.5)]
        self.assertEqual(states[0], "mandatara")
        self.assertEqual(states[2], "sama")
        self.assertEqual(states[-1], "atichara")


class NaisargikaAndDrikTest(unittest.TestCase):

    def test_naisargika_follows_the_witness_order(self):
        order = sorted(NAISARGIKA_VIRUPAS, key=NAISARGIKA_VIRUPAS.get,
                       reverse=True)
        self.assertEqual(order, ["Surya", "Chandra", "Shukra", "Guru",
                                 "Budha", "Mangal", "Shani"])

    def test_naisargika_is_sixty_sevenths(self):
        self.assertAlmostEqual(NAISARGIKA_VIRUPAS["Surya"], 60.0, places=9)
        self.assertAlmostEqual(NAISARGIKA_VIRUPAS["Shani"], 60.0 / 7.0,
                               places=9)

    def test_naisargika_is_chart_independent(self):
        first = naisargika_bala("Guru").value_virupa
        second = naisargika_bala("Guru").value_virupa
        self.assertEqual(first, second)

    def test_drik_bala_consumes_aspects_rather_than_recomputing(self):
        """
        Part 8: the strength module must read the aspect facts the feature
        layer derived. Every graha cited must be one the features say aspects
        the target.
        """
        features = build_chart_features(natal())
        for planet in SHADBALA_GRAHAS:
            component = drik_bala(planet, features)
            aspecting = set(features.planet(planet).aspecting_planets)
            cited = {part.name.replace("drishti_from_", "")
                     for part in component.subcomponents}
            with self.subTest(planet=planet):
                self.assertTrue(cited <= aspecting)

    def test_drik_bala_signs_follow_benefic_and_malefic(self):
        features = build_chart_features(natal())
        for planet in SHADBALA_GRAHAS:
            for part in drik_bala(planet, features).subcomponents:
                source = part.name.replace("drishti_from_", "")
                graha = features.planet(source)
                with self.subTest(planet=planet, source=source):
                    if graha.natural_benefic:
                        self.assertGreater(part.value_virupa, 0)
                    elif graha.natural_malefic:
                        self.assertLess(part.value_virupa, 0)


class ShadbalaTotalTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chart = natal()
        cls.features = build_chart_features(cls.chart)
        cls.shadbala = compute_shadbala(cls.chart, cls.features,
                                        birth=BIRTH_LOCAL)

    def test_all_seven_grahas_present_and_nodes_absent(self):
        """The witness: "The nodes are not considered.\""""
        self.assertEqual(set(self.shadbala.results), set(SHADBALA_GRAHAS))
        self.assertNotIn("Rahu", self.shadbala.results)
        self.assertNotIn("Ketu", self.shadbala.results)

    def test_total_is_the_sum_of_the_six(self):
        for planet, result in self.shadbala.results.items():
            with self.subTest(planet=planet):
                self.assertAlmostEqual(
                    result.total_virupa,
                    sum(c.value_virupa for c in result.components), places=9)

    def test_rupa_conversion(self):
        for result in self.shadbala.results.values():
            with self.subTest(planet=result.planet):
                self.assertAlmostEqual(
                    result.total_rupa,
                    result.total_virupa / VIRUPAS_PER_RUPA, places=9)

    def test_requirements_match_the_witness(self):
        self.assertEqual(REQUIRED_VIRUPAS, {
            "Surya": 390.0, "Chandra": 360.0, "Mangal": 300.0,
            "Budha": 420.0, "Guru": 390.0, "Shukra": 330.0, "Shani": 300.0})

    def test_ratio_is_total_over_requirement(self):
        for result in self.shadbala.results.values():
            with self.subTest(planet=result.planet):
                self.assertAlmostEqual(
                    result.ratio,
                    result.total_virupa / result.required_virupa, places=9)

    def test_no_component_is_absurd(self):
        """A sanity floor and ceiling on each component."""
        for result in self.shadbala.results.values():
            for component in result.components:
                with self.subTest(planet=result.planet,
                                  component=component.name):
                    self.assertGreater(component.value_virupa, -200.0)
                    self.assertLess(component.value_virupa, 500.0)

    def test_intermediate_values_are_kept(self):
        """Part 3: never discard intermediates."""
        for result in self.shadbala.results.values():
            with self.subTest(planet=result.planet):
                self.assertTrue(result.sthana_bala.subcomponents)
                self.assertTrue(result.kala_bala.subcomponents)

    def test_missing_birth_time_produces_no_shadbala(self):
        """Kala Bala needs the time; a fabricated one would be worse."""
        result = compute_shadbala(self.chart, self.features, birth=None)
        self.assertEqual(result.results, {})
        self.assertTrue(any("birth datetime" in w for w in result.warnings))


class ProvenanceTest(unittest.TestCase):
    """Part 9: every component exposes its provenance, and totals inherit."""

    @classmethod
    def setUpClass(cls):
        chart = natal()
        cls.shadbala = compute_shadbala(chart, build_chart_features(chart),
                                        birth=BIRTH_LOCAL)

    def test_every_component_declares_profile_and_source(self):
        for result in self.shadbala.results.values():
            for component in result.components:
                with self.subTest(planet=result.planet,
                                  component=component.name):
                    self.assertTrue(component.calculation_profile)
                    self.assertTrue(component.validation_status)

    def test_components_cite_the_bphs_witness(self):
        for result in self.shadbala.results.values():
            with self.subTest(planet=result.planet):
                self.assertIn("BPHS_27_SHADBALA", result.source_ref_ids)

    def test_source_ref_resolves(self):
        from engine.sources import witness_by_id
        witness = witness_by_id("BPHS_27_SHADBALA")
        self.assertEqual(witness.chapter, "27")

    def test_total_inherits_the_weakest_component_status(self):
        """
        Part 9: a total must not be labelled better-validated than its worst
        constituent.
        """
        for result in self.shadbala.results.values():
            expected = weakest_status(result.components)
            with self.subTest(planet=result.planet):
                self.assertEqual(result.validation_status, expected)

    def test_nothing_claims_tradition_validated(self):
        """The witness is a TRANSLATION, so Sanskrit tier is unreachable."""
        for result in self.shadbala.results.values():
            for component in result.components:
                with self.subTest(planet=result.planet,
                                  component=component.name):
                    self.assertNotEqual(component.validation_status,
                                        "TRADITION_VALIDATED")

    def test_approximations_are_surfaced_on_the_total(self):
        for result in self.shadbala.results.values():
            with self.subTest(planet=result.planet):
                self.assertTrue(result.has_approximation,
                                "varsha/masa bala are approximations, so "
                                "every total should say so")

    def test_serialises(self):
        import json
        json.dumps(self.shadbala.to_dict())


if __name__ == "__main__":
    unittest.main(verbosity=2)
