"""
Bhava Chalit (V1.4 Parts 12-15, 24)
-------------------------------------
The tests that matter here are the SEPARATION tests.

Part 13 is explicit: moving a graha into a different bhava must not change
its sign, its sign lord, the houses it owns, its dignity, its navamsha or any
other varga. Those are properties of the zodiac. If Bhava Chalit leaks into
them, every downstream rule silently changes its answer.

So most of this module compares a chart computed with and without a bhava
system and asserts that everything except the bhava column is byte-identical.
"""

# V1.4.

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.houses import (
    HOUSE_PROFILES, WHOLE_SIGN, ReferenceSpace, build_bhava_chart,
    equal_from_lagna, placidus, porphyry, sripati,
)
from engine.planets import JyotishChart, jde_from_datetime

BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)


def natal():
    return JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                        lat=26.9124, lon=75.7873)


class SystemTest(unittest.TestCase):

    ASC = 345.78
    MC = 255.0

    def test_all_systems_return_twelve_madhyas(self):
        for name, builder in (("equal", equal_from_lagna),
                              ("sripati", sripati), ("porphyry", porphyry)):
            madhyas = builder(ascendant=self.ASC, midheaven=self.MC)
            with self.subTest(system=name):
                self.assertEqual(sorted(madhyas), list(range(1, 13)))
                for value in madhyas.values():
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLess(value, 360.0)

    def test_first_madhya_is_the_ascendant(self):
        """The Lagna degree is the bhava MADHYA, per the design decision."""
        for builder in (equal_from_lagna, sripati, porphyry):
            madhyas = builder(ascendant=self.ASC, midheaven=self.MC)
            with self.subTest(system=builder.__name__):
                self.assertAlmostEqual(madhyas[1], self.ASC, places=9)

    def test_quadrant_systems_place_the_angles_exactly(self):
        for builder in (sripati, porphyry):
            madhyas = builder(ascendant=self.ASC, midheaven=self.MC)
            with self.subTest(system=builder.__name__):
                self.assertAlmostEqual(madhyas[10], self.MC, places=9)
                self.assertAlmostEqual(madhyas[7], (self.ASC + 180) % 360,
                                       places=9)
                self.assertAlmostEqual(madhyas[4], (self.MC + 180) % 360,
                                       places=9)

    def test_equal_system_ignores_the_midheaven(self):
        first = equal_from_lagna(ascendant=self.ASC, midheaven=self.MC)
        second = equal_from_lagna(ascendant=self.ASC, midheaven=0.0)
        self.assertEqual(first, second)

    def test_equal_houses_are_exactly_thirty_degrees_apart(self):
        madhyas = equal_from_lagna(ascendant=self.ASC)
        for house in range(1, 12):
            with self.subTest(house=house):
                gap = (madhyas[house + 1] - madhyas[house]) % 360.0
                self.assertAlmostEqual(gap, 30.0, places=9)

    def test_placidus_refuses_above_the_polar_circle(self):
        """A loud failure beats a confident wrong answer."""
        with self.assertRaises(ValueError) as caught:
            placidus(self.ASC, self.MC, latitude=70.0)
        self.assertIn("undefined", str(caught.exception))

    def test_placidus_needs_a_latitude(self):
        with self.assertRaises(ValueError):
            placidus(self.ASC, self.MC, latitude=None)

    def test_unknown_system_is_rejected(self):
        with self.assertRaises(ValueError):
            build_bhava_chart(natal(), "astrolabe")


class CuspTest(unittest.TestCase):

    def setUp(self):
        self.bhava = build_bhava_chart(natal(), "sripati")

    def test_twelve_cusps(self):
        self.assertEqual(sorted(self.bhava.cusps), list(range(1, 13)))

    def test_cusps_tile_the_circle(self):
        """Spans must sum to exactly 360 degrees with no gap or overlap."""
        total = sum(cusp.span for cusp in self.bhava.cusps.values())
        self.assertAlmostEqual(total, 360.0, places=6)

    def test_every_longitude_falls_in_exactly_one_bhava(self):
        for degrees in range(0, 360, 3):
            matches = [house for house, cusp in self.bhava.cusps.items()
                       if cusp.contains(float(degrees))]
            with self.subTest(longitude=degrees):
                self.assertEqual(len(matches), 1)

    def test_madhya_lies_inside_its_own_bhava(self):
        for house, cusp in self.bhava.cusps.items():
            with self.subTest(house=house):
                self.assertTrue(cusp.contains(cusp.madhya))

    def test_sandhi_is_midway_between_adjacent_madhyas(self):
        for house in range(1, 13):
            following = 1 if house == 12 else house + 1
            first = self.bhava.cusps[house]
            second = self.bhava.cusps[following]
            with self.subTest(house=house):
                self.assertAlmostEqual(first.end, second.start, places=9)

    def test_bhava_lord_comes_from_the_madhya_sign(self):
        """Part 13: lordship is sign-based, taken from the madhya."""
        from engine.planets import RASHI_LORDS, RASHI_NAMES
        for house, cusp in self.bhava.cusps.items():
            expected = RASHI_LORDS[RASHI_NAMES[int(cusp.madhya // 30) % 12]]
            with self.subTest(house=house):
                self.assertEqual(cusp.sign_lord, expected)

    def test_bhavas_spanning_two_rashis_record_the_second(self):
        spanning = [c for c in self.bhava.cusps.values()
                    if c.secondary_sign is not None]
        for cusp in spanning:
            with self.subTest(house=cusp.house):
                self.assertNotEqual(cusp.secondary_sign, cusp.sign)
                self.assertIn("secondary_sign", cusp.to_dict())


class SeparationTest(unittest.TestCase):
    """
    PART 13, THE CRITICAL SECTION.

    Selecting a house system must change ONE thing: which bhava a graha falls
    in. Everything else is a property of the zodiac and must be untouched.
    """

    @classmethod
    def setUpClass(cls):
        cls.chart = natal()
        cls.baseline = build_chart_features(cls.chart)
        cls.bhava = build_bhava_chart(cls.chart, "sripati")

    def test_building_a_bhava_chart_does_not_mutate_the_rashi_chart(self):
        before = {name: (p.longitude, p.rashi_index, p.dignity)
                  for name, p in self.chart.planets.items()}
        build_bhava_chart(self.chart, "sripati")
        build_bhava_chart(self.chart, "equal_from_lagna")
        after = {name: (p.longitude, p.rashi_index, p.dignity)
                 for name, p in self.chart.planets.items()}
        self.assertEqual(before, after)

    def test_signs_are_unchanged(self):
        for name, placement in self.bhava.placements.items():
            with self.subTest(graha=name):
                self.assertEqual(placement.rashi_sign,
                                 self.chart.planets[name].rashi_index)

    def test_sign_lords_are_unchanged(self):
        for name, placement in self.bhava.placements.items():
            with self.subTest(graha=name):
                self.assertEqual(placement.rashi_sign_lord,
                                 self.chart.planets[name].rashi_lord)

    def test_features_are_identical_regardless_of_house_system(self):
        """
        The strongest form of the separation test: recompute the whole
        feature set after building bhava charts in several systems and
        require it to be unchanged.
        """
        for system in ("sripati", "equal_from_lagna", "porphyry"):
            build_bhava_chart(self.chart, system)
        after = build_chart_features(self.chart)

        for name, graha in self.baseline.planets.items():
            other = after.planets[name]
            with self.subTest(graha=name):
                self.assertEqual(graha.sign, other.sign)
                self.assertEqual(graha.house, other.house)
                self.assertEqual(graha.houses_owned, other.houses_owned)
                self.assertEqual(graha.dignity, other.dignity)
                self.assertEqual(graha.sign_lord, other.sign_lord)
                self.assertEqual(graha.vargas["D9"].sign,
                                 other.vargas["D9"].sign)
                self.assertEqual(graha.vargottama, other.vargottama)

    def test_house_lords_are_unchanged(self):
        after = build_chart_features(self.chart)
        self.assertEqual(self.baseline.house_lords, after.house_lords)

    def test_rashi_house_and_bhava_house_are_separate_fields(self):
        """Part 12: the difference must remain visible."""
        for placement in self.bhava.placements.values():
            data = placement.to_dict()
            self.assertIn("rashi_house", data)
            self.assertIn("bhava_house", data)
            self.assertIn("moved", data)

    def test_moved_flag_agrees_with_the_two_fields(self):
        for placement in self.bhava.placements.values():
            with self.subTest(graha=placement.planet):
                self.assertEqual(
                    placement.moved,
                    placement.rashi_house != placement.bhava_house)

    def test_yoga_rules_still_run_in_rashi_space(self):
        """
        Part 15: rules must not silently switch to bhava positions. The rule
        results must be identical whether or not a bhava chart was built.
        """
        from engine.rules import evaluate_rules
        before = {r.id: r.status for r in evaluate_rules(self.baseline)}
        build_bhava_chart(self.chart, "sripati")
        after = {r.id: r.status
                 for r in evaluate_rules(build_chart_features(self.chart))}
        self.assertEqual(before, after)

    def test_reference_space_vocabulary_exists(self):
        self.assertEqual({s.value for s in ReferenceSpace},
                         {"RASHI", "BHAVA", "BOTH", "CONFIGURABLE"})


class WholeSignTest(unittest.TestCase):
    """The degenerate case, where bhava and rashi coincide by definition."""

    def setUp(self):
        self.bhava = build_bhava_chart(natal(), WHOLE_SIGN)

    def test_nothing_ever_moves(self):
        self.assertEqual(self.bhava.moved_planets, [])
        for placement in self.bhava.placements.values():
            with self.subTest(graha=placement.planet):
                self.assertEqual(placement.rashi_house, placement.bhava_house)

    def test_cusps_are_whole_signs(self):
        for cusp in self.bhava.cusps.values():
            with self.subTest(house=cusp.house):
                self.assertAlmostEqual(cusp.span, 30.0, places=6)

    def test_it_says_so(self):
        self.assertTrue(any("bhava is the rashi" in w
                            for w in self.bhava.warnings))


class DivergenceTest(unittest.TestCase):
    """Part 12: report which grahas move and which do not."""

    def test_sripati_moves_at_least_one_graha_in_the_regression_chart(self):
        bhava = build_bhava_chart(natal(), "sripati")
        self.assertTrue(bhava.moved_planets)
        self.assertTrue(bhava.divergences)

    def test_divergences_name_both_house_numbers(self):
        bhava = build_bhava_chart(natal(), "sripati")
        for text in bhava.divergences:
            with self.subTest(text=text):
                self.assertIn("rashi house", text)
                self.assertIn("bhava house", text)

    def test_moved_planets_across_the_regression_charts(self):
        """
        Records how often the two representations disagree, across the eight
        unrelated charts. A number this useful should not be a surprise.
        """
        import json
        path = os.path.join(ROOT, "tests", "fixtures",
                            "regression_charts.json")
        with open(path, encoding="utf-8") as handle:
            charts = json.load(handle)["charts"]

        moved_anywhere = 0
        for case in charts:
            chart = JyotishChart(jde=case["jd_ut"], lat=case["latitude"],
                                 lon=case["longitude"])
            bhava = build_bhava_chart(chart, "sripati")
            moved_anywhere += len(bhava.moved_planets)
            with self.subTest(chart=case["id"]):
                # Whatever moves, the rashi side must be untouched.
                for name, placement in bhava.placements.items():
                    self.assertEqual(placement.rashi_sign,
                                     chart.planets[name].rashi_index)
        self.assertGreater(moved_anywhere, 0,
                           "Sripati should move at least one graha somewhere")

    def test_near_sandhi_grahas_are_flagged(self):
        """A graha near a junction has a birth-time-sensitive bhava."""
        bhava = build_bhava_chart(natal(), "sripati",
                                  sandhi_envelope_deg=5.0)
        for note in bhava.near_sandhi:
            self.assertIn("sandhi", note)


class ProfileTest(unittest.TestCase):

    def test_every_profile_declares_its_provenance(self):
        for profile_id, profile in HOUSE_PROFILES.items():
            with self.subTest(profile=profile_id):
                self.assertTrue(profile.name)
                self.assertTrue(profile.description)
                self.assertTrue(profile.tradition)
                self.assertTrue(profile.validation_status)

    def test_no_house_system_claims_source_validation(self):
        """Part 23: no new module ships with a fabricated citation."""
        for profile_id, profile in HOUSE_PROFILES.items():
            with self.subTest(profile=profile_id):
                self.assertEqual(profile.validation_status, "UNVERIFIED")
                self.assertEqual(profile.source_ref_ids, ())

    def test_system_is_named_not_called_bhava_chalit(self):
        """Part 14: name the cusp method, not the category."""
        for profile_id in HOUSE_PROFILES:
            with self.subTest(profile=profile_id):
                self.assertNotIn("bhava_chalit", profile_id)

    def test_chart_serialises(self):
        import json
        json.dumps(build_bhava_chart(natal(), "sripati").to_dict())


if __name__ == "__main__":
    unittest.main(verbosity=2)
