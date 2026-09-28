"""
Multi-chart regression suite (V1.2 Part 14)
--------------------------------------------
Eight unrelated natal charts spanning 1901 to 2033, both hemispheres, the
equator to 64 degrees north, and a spread of planetary configurations.

WHY MORE THAN ONE CHART
    A single regression case can be satisfied by a formula that is wrong
    everywhere else. The Jaipur 1988 chart is retained — it is the documented
    example — but it is no longer the only witness, and nothing in the engine
    may be tuned to suit it.

SEPARATION OF EXPECTATIONS (the Part 14 requirement)
    ASTRONOMICAL expectations live in tests/fixtures/regression_charts.json,
    generated from the Swiss Ephemeris. They are facts about the sky.

    ASTROLOGICAL expectations live in this file, as code. They are
    consequences of rules this engine implements.

    Keeping them apart means a yoga rule change cannot quietly rewrite an
    ephemeris expectation to make itself pass, and an ephemeris change cannot
    hide behind a rule expectation.
"""

# V1.2.

import datetime
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import JyotishChart, jde_from_datetime
from engine.rules import evaluate_rules
from engine.timing import from_chart as dasha_from_chart
from engine.uncertainty import ACCURACY_ARCMIN

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "regression_charts.json")

PLANETS = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani",
           "Rahu", "Ketu"]

# Per-body tolerance in arcseconds, set just above the measured envelope so a
# regression is caught but a known limitation is not reported as a failure.
TOLERANCE_ARCSEC = {
    "Surya": 40.0, "Chandra": 15.0, "Mangal": 15.0, "Budha": 20.0,
    "Guru": 8.0, "Shukra": 45.0, "Shani": 10.0, "Rahu": 75.0, "Ketu": 75.0,
}

LAGNA_TOLERANCE_ARCSEC = 10.0


def arc_difference(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0) * 3600.0


def load_charts() -> list[dict]:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)["charts"]


def build(case: dict) -> JyotishChart:
    return JyotishChart(jde=case["jd_ut"], lat=case["latitude"],
                        lon=case["longitude"], ayanamsha_system="lahiri",
                        true_node=True)


class AstronomicalRegressionTest(unittest.TestCase):
    """ASTRONOMICAL FACT — externally benchmarked against Swiss Ephemeris."""

    @classmethod
    def setUpClass(cls):
        cls.cases = load_charts()
        cls.charts = {case["id"]: build(case) for case in cls.cases}

    def test_fixture_spans_the_intended_variety(self):
        years = sorted(int(c["birth_local"][:4]) for c in self.cases)
        latitudes = [c["latitude"] for c in self.cases]
        longitudes = [c["longitude"] for c in self.cases]
        self.assertGreaterEqual(len(self.cases), 6)
        self.assertLess(years[0], 1950)
        self.assertGreater(years[-1], 2025)
        self.assertLess(min(latitudes), -30, "needs a southern chart")
        self.assertGreater(max(latitudes), 60, "needs a high-latitude chart")
        self.assertLess(min(longitudes), -50, "needs a western chart")
        self.assertGreater(max(longitudes), 100, "needs an eastern chart")

    def test_ayanamsha(self):
        from engine import ephemeris as eph
        for case in self.cases:
            jd_tt = eph.jd_ut_to_tt(case["jd_ut"])
            with self.subTest(chart=case["id"]):
                error = abs(eph.ayanamsha(jd_tt, "lahiri")
                            - case["ayanamsha_lahiri"]) * 3600
                self.assertLess(error, 0.5)

    def test_sidereal_longitudes(self):
        for case in self.cases:
            chart = self.charts[case["id"]]
            for body in PLANETS:
                expected = case["bodies"][body]["sidereal"]
                error = arc_difference(chart.planets[body].longitude, expected)
                with self.subTest(chart=case["id"], body=body):
                    self.assertLess(
                        error, TOLERANCE_ARCSEC[body],
                        f"{body} off by {error:.1f}\" in {case['id']}")

    def test_jupiter_and_saturn_are_now_arcsecond_accurate(self):
        """The V1.2 upgrade, demonstrated on charts it was not tuned against."""
        for case in self.cases:
            chart = self.charts[case["id"]]
            for body in ("Guru", "Shani"):
                error = arc_difference(chart.planets[body].longitude,
                                       case["bodies"][body]["sidereal"])
                with self.subTest(chart=case["id"], body=body):
                    self.assertLess(error, 10.0)

    def test_sign_nakshatra_and_pada(self):
        for case in self.cases:
            chart = self.charts[case["id"]]
            for body in PLANETS:
                expected = case["bodies"][body]
                position = chart.planets[body]
                with self.subTest(chart=case["id"], body=body):
                    self.assertEqual(position.rashi, expected["sign"])
                    self.assertEqual(position.nakshatra, expected["nakshatra"])
                    self.assertEqual(position.pada, expected["pada"])

    def test_lagna(self):
        for case in self.cases:
            chart = self.charts[case["id"]]
            expected = case["lagna"]
            with self.subTest(chart=case["id"]):
                self.assertLess(
                    arc_difference(chart.lagna.longitude, expected["sidereal"]),
                    LAGNA_TOLERANCE_ARCSEC)
                self.assertEqual(chart.lagna.rashi, expected["sign"])
                self.assertEqual(chart.lagna.nakshatra, expected["nakshatra"])
                self.assertEqual(chart.lagna.pada, expected["pada"])

    def test_retrograde_states(self):
        for case in self.cases:
            chart = self.charts[case["id"]]
            for body in ("Mangal", "Budha", "Guru", "Shukra", "Shani"):
                expected = case["bodies"][body]
                position = chart.planets[body]
                if abs(expected["speed"]) < 0.005:
                    # Too near a station for the engine to resolve; it should
                    # say so rather than guess.
                    with self.subTest(chart=case["id"], body=body):
                        self.assertTrue(position.is_stationary)
                    continue
                with self.subTest(chart=case["id"], body=body):
                    self.assertEqual(position.is_retrograde,
                                     expected["retrograde"])

    def test_delta_t(self):
        from engine import ephemeris as eph
        for case in self.cases:
            year = int(case["birth_local"][:4])
            tolerance = 1.0 if year <= 2026 else 30.0
            with self.subTest(chart=case["id"]):
                self.assertAlmostEqual(eph.delta_t_seconds(case["jd_ut"]),
                                       case["delta_t_seconds"], delta=tolerance)

    def test_nodes_are_exactly_opposite(self):
        for case in self.cases:
            chart = self.charts[case["id"]]
            with self.subTest(chart=case["id"]):
                separation = abs(chart.planets["Rahu"].longitude
                                 - chart.planets["Ketu"].longitude)
                self.assertAlmostEqual(separation, 180.0, places=6)


class AstrologicalRegressionTest(unittest.TestCase):
    """
    CALCULATED ASTROLOGICAL FEATURE and TRADITION-SPECIFIC RULE.

    These assertions are about internal consistency and stability, not about
    astronomy. They are deliberately structural: asserting that a particular
    chart 'has Gajakesari' would pin a rule reading rather than test the
    engine, and would have to be rewritten every time the catalog grew.
    """

    @classmethod
    def setUpClass(cls):
        cls.cases = load_charts()
        cls.features = {case["id"]: build_chart_features(build(case))
                        for case in cls.cases}

    def test_every_chart_produces_a_complete_feature_set(self):
        for case in self.cases:
            features = self.features[case["id"]]
            with self.subTest(chart=case["id"]):
                self.assertEqual(len(features.planets), 9)
                self.assertEqual(len(features.houses), 12)
                self.assertEqual(len(features.house_lords), 12)

    def test_houses_are_consistent_with_signs_in_every_chart(self):
        for case in self.cases:
            features = self.features[case["id"]]
            for name, graha in features.planets.items():
                expected = ((graha.sign - features.lagna_sign) % 12) + 1
                with self.subTest(chart=case["id"], graha=name):
                    self.assertEqual(graha.house, expected)

    def test_house_lords_invert_to_ownership_in_every_chart(self):
        for case in self.cases:
            features = self.features[case["id"]]
            for house, lord in features.house_lords.items():
                with self.subTest(chart=case["id"], house=house):
                    self.assertIn(house, features.houses_owned_by(lord))

    def test_every_chart_evaluates_the_whole_catalog(self):
        from engine.rules import all_rules
        expected = len(all_rules())
        for case in self.cases:
            with self.subTest(chart=case["id"]):
                results = evaluate_rules(self.features[case["id"]])
                self.assertEqual(len(results), expected)

    def test_present_yogas_always_cite_a_matched_condition(self):
        for case in self.cases:
            for result in evaluate_rules(self.features[case["id"]]):
                if not result.present:
                    continue
                with self.subTest(chart=case["id"], rule=result.id):
                    self.assertTrue(result.conditions_met)
                    self.assertTrue(result.source)

    def test_charts_differ_from_one_another(self):
        """
        Guards against a bug that would make every chart identical — which
        would otherwise let all the structural tests above pass.
        """
        signatures = set()
        for case in self.cases:
            features = self.features[case["id"]]
            signatures.add(tuple(
                (name, graha.sign) for name, graha in sorted(
                    features.planets.items())))
        self.assertEqual(len(signatures), len(self.cases))

    def test_yoga_findings_differ_between_charts(self):
        found = []
        for case in self.cases:
            present = frozenset(
                r.id for r in evaluate_rules(self.features[case["id"]])
                if r.present)
            found.append(present)
        self.assertGreater(len(set(found)), 1,
                           "every chart produced the same yogas")

    def test_boundary_warnings_are_computed_for_every_chart(self):
        for case in self.cases:
            features = self.features[case["id"]]
            with self.subTest(chart=case["id"]):
                self.assertIn("bodies_with_warnings", features.uncertainty)
                for name, graha in features.planets.items():
                    self.assertIsNotNone(graha.uncertainty)
                    self.assertEqual(graha.uncertainty.accuracy_arcmin,
                                     ACCURACY_ARCMIN[name])


class TimingRegressionTest(unittest.TestCase):
    """The dasha engine on every chart, not only the documented one."""

    @classmethod
    def setUpClass(cls):
        cls.cases = load_charts()

    def dasha_for(self, case: dict, depth: int = 3):
        birth = datetime.datetime.fromisoformat(case["birth_local"])
        return dasha_from_chart(build(case), birth, depth=depth)

    def test_every_chart_produces_a_valid_hierarchy(self):
        for case in self.cases:
            dasha = self.dasha_for(case, depth=2)
            with self.subTest(chart=case["id"]):
                self.assertEqual(len(dasha.mahadashas), 9)
                self.assertEqual(len(dasha.antardashas), 81)

    def test_birth_always_falls_in_the_first_mahadasha(self):
        for case in self.cases:
            birth = datetime.datetime.fromisoformat(case["birth_local"])
            dasha = self.dasha_for(case, depth=1)
            with self.subTest(chart=case["id"]):
                self.assertTrue(dasha.mahadashas[0].contains(birth))
                self.assertLessEqual(dasha.mahadashas[0].start, birth)

    def test_birth_lord_matches_the_moons_nakshatra(self):
        from engine.timing import NAKSHATRA_DASHA_LORD
        for case in self.cases:
            dasha = self.dasha_for(case, depth=1)
            expected = NAKSHATRA_DASHA_LORD[
                case["bodies"]["Chandra"]["nakshatra_index"]]
            with self.subTest(chart=case["id"]):
                self.assertEqual(dasha.birth_lord, expected)

    def test_no_gaps_at_any_level_in_any_chart(self):
        for case in self.cases:
            dasha = self.dasha_for(case, depth=3)
            with self.subTest(chart=case["id"]):
                for earlier, later in zip(dasha.mahadashas,
                                          dasha.mahadashas[1:]):
                    self.assertEqual(earlier.end, later.start)
                self.assertEqual(dasha.pratyantardashas[0].start, dasha.start)
                self.assertEqual(dasha.pratyantardashas[-1].end, dasha.end)

    def test_queries_resolve_across_each_chart_span(self):
        for case in self.cases:
            dasha = self.dasha_for(case, depth=3)
            span = dasha.end - dasha.start
            with self.subTest(chart=case["id"]):
                for fraction in (0.01, 0.25, 0.5, 0.75, 0.99):
                    moment = dasha.start + span * fraction
                    stack = dasha.get_dasha_stack_at(moment)
                    self.assertTrue(stack["in_range"])
                    self.assertIsNotNone(stack["pratyantardasha"])

    def test_leap_and_century_spanning_charts_stay_contiguous(self):
        """london_1901 and delhi_1947 both run across many leap years."""
        for chart_id in ("london_1901", "delhi_1947"):
            case = next(c for c in self.cases if c["id"] == chart_id)
            dasha = self.dasha_for(case, depth=2)
            with self.subTest(chart=chart_id):
                for antar in dasha.antardashas:
                    self.assertTrue(dasha.start <= antar.start < dasha.end)


class SnapshotRegressionTest(unittest.TestCase):
    """Every chart must serialise through the canonical contract."""

    def test_snapshot_builds_and_serialises_for_every_chart(self):
        from engine.snapshot import SCHEMA_VERSION, build_snapshot
        for case in load_charts():
            chart = build(case)
            birth = datetime.datetime.fromisoformat(case["birth_local"])
            features = build_chart_features(chart)
            snapshot = build_snapshot(
                chart, features=features,
                yoga_results=evaluate_rules(features),
                dasha=dasha_from_chart(chart, birth, depth=2),
                birth_datetime=birth, name=case["id"])
            with self.subTest(chart=case["id"]):
                data = snapshot.to_dict()
                self.assertEqual(data["schema_version"], SCHEMA_VERSION)
                json.dumps(data)
                self.assertEqual(len(data["planets"]), 9)
                self.assertEqual(len(data["houses"]), 12)
                self.assertTrue(data["timing"]["vimshottari"]["mahadashas"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
