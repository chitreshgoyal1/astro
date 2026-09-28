"""
Transit interface feasibility (V1.3 Part 21)
---------------------------------------------
Part 21 asks for interfaces only, and for confidence that the existing
ChartSnapshot and dasha API can feed a future transit engine cleanly.

These tests turn that confidence into something checked. They construct the
proposed V1.4 objects from what the engine produces TODAY — a real snapshot, a
real dasha tree, real features computed at a non-natal moment — and assert the
pieces fit. If a later change breaks the seam, it breaks here rather than in
V1.4 when a transit engine is half written.

No prediction is computed and none is tested. The last test in this module
asserts that, so the boundary stays where the brief put it.
"""

# V1.3.

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features, parashari_profile
from engine.planets import JyotishChart, jde_from_datetime
from engine.rules import evaluate_rules
from engine.snapshot import build_snapshot
from engine.timing import compute_vimshottari
from engine.transit_interface import (
    OUT_OF_SCOPE_FOR_V1_3, REQUIRED_DASHA_METHODS, REQUIRED_NATAL_SECTIONS,
    TimingContext, TransitAspect, TransitSnapshot, dasha_api_is_sufficient,
    natal_snapshot_is_sufficient,
)
from engine.uncertainty import assess_position

BIRTH_LOCAL = datetime.datetime(1988, 8, 30, 20, 18)
BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)
TRANSIT_MOMENT = datetime.datetime(2030, 6, 10, 12, 0)


def natal_chart() -> JyotishChart:
    return JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                        lat=26.9124, lon=75.7873)


def natal_snapshot() -> dict:
    chart = natal_chart()
    features = build_chart_features(chart)
    return build_snapshot(
        chart, features=features, yoga_results=evaluate_rules(features),
        dasha=compute_vimshottari(chart.planets["Chandra"].longitude,
                                  BIRTH_LOCAL, depth=2),
        birth_datetime=BIRTH_LOCAL, rule_profile="parashari").to_dict()


class SnapshotSufficiencyTest(unittest.TestCase):
    """Can a transit engine be built on the snapshot as it stands?"""

    @classmethod
    def setUpClass(cls):
        cls.snapshot = natal_snapshot()

    def test_snapshot_carries_every_required_section(self):
        sufficient, missing = natal_snapshot_is_sufficient(self.snapshot)
        self.assertTrue(sufficient, f"snapshot is missing {missing}")

    def test_required_sections_are_non_empty(self):
        for section in REQUIRED_NATAL_SECTIONS:
            with self.subTest(section=section):
                self.assertTrue(self.snapshot[section])

    def test_natal_longitudes_are_available_for_comparison(self):
        """A transit engine needs a number per graha, not just a sign name."""
        for name, entry in self.snapshot["planets"].items():
            with self.subTest(graha=name):
                self.assertIsInstance(entry["longitude"], float)
        self.assertIsInstance(self.snapshot["lagna"]["longitude"], float)

    def test_natal_house_frame_is_available(self):
        houses = self.snapshot["houses"]
        self.assertEqual(len(houses), 12)
        for number, bhava in houses.items():
            with self.subTest(house=number):
                self.assertIn("sign_index", bhava)

    def test_methodology_travels_with_the_snapshot(self):
        """A transit result must be able to name the methodology it assumed."""
        methodology = self.snapshot["methodology"]
        self.assertIn("rule_profile", methodology)
        self.assertIn("source_registry_version", methodology)


class DashaApiSufficiencyTest(unittest.TestCase):

    def setUp(self):
        chart = natal_chart()
        self.dasha = compute_vimshottari(
            chart.planets["Chandra"].longitude, BIRTH_LOCAL, depth=3)

    def test_dasha_exposes_every_required_query(self):
        sufficient, missing = dasha_api_is_sufficient(self.dasha)
        self.assertTrue(sufficient, f"dasha API is missing {missing}")

    def test_stack_resolves_at_an_arbitrary_future_moment(self):
        stack = self.dasha.get_dasha_stack_at(TRANSIT_MOMENT)
        self.assertTrue(stack["in_range"])
        for level in ("mahadasha", "antardasha", "pratyantardasha"):
            with self.subTest(level=level):
                self.assertIsNotNone(stack[level])

    def test_periods_between_supports_a_scanning_engine(self):
        """
        A transit engine will want the periods overlapping a window, which is
        how dasha and transit get combined later.
        """
        window_start = datetime.datetime(2030, 1, 1)
        window_end = datetime.datetime(2031, 1, 1)
        for level in ("mahadasha", "antardasha", "pratyantardasha"):
            with self.subTest(level=level):
                periods = self.dasha.get_periods_between(
                    window_start, window_end, level=level)
                self.assertTrue(periods)


class TransitSnapshotConstructionTest(unittest.TestCase):
    """
    Build the proposed V1.4 object from today's engine.

    This is the real feasibility test: if a transit snapshot can be assembled
    from existing parts with no new machinery, the seam is sound.
    """

    @classmethod
    def setUpClass(cls):
        cls.natal = natal_snapshot()
        cls.transit_chart = JyotishChart(
            jde=jde_from_datetime(TRANSIT_MOMENT),
            lat=26.9124, lon=75.7873)
        cls.transit_features = build_chart_features(cls.transit_chart)

    def build(self) -> TransitSnapshot:
        natal_lagna_sign = self.natal["lagna"]["sign_index"]
        natal_moon_sign = self.natal["planets"]["Chandra"]["sign_index"]

        planets, from_lagna, from_moon, uncertainty = {}, {}, {}, {}
        for name, graha in self.transit_features.planets.items():
            planets[name] = {
                "longitude": graha.longitude,
                "sign": graha.sign_name,
                "retrograde": graha.retrograde,
            }
            from_lagna[name] = ((graha.sign - natal_lagna_sign) % 12) + 1
            from_moon[name] = ((graha.sign - natal_moon_sign) % 12) + 1
            uncertainty[name] = assess_position(
                name, graha.longitude).to_dict()

        aspects = [
            TransitAspect(
                transiting=name,
                natal_target="Lagna",
                aspect_type="seventh",
                separation_deg=abs(
                    (graha.longitude - self.natal["lagna"]["longitude"] + 180)
                    % 360 - 180),
            )
            for name, graha in self.transit_features.planets.items()
        ]

        return TransitSnapshot(
            moment=TRANSIT_MOMENT,
            settings={"ayanamsha": "lahiri", "node": "true"},
            planets=planets,
            houses_from_lagna=from_lagna,
            houses_from_moon=from_moon,
            natal_aspects=self.natal["features"]["aspects"],
            transit_to_natal_aspects=aspects,
            uncertainty=uncertainty,
        )

    def test_transit_snapshot_constructs_from_existing_parts(self):
        snapshot = self.build()
        self.assertEqual(len(snapshot.planets), 9)
        self.assertEqual(len(snapshot.houses_from_lagna), 9)
        self.assertEqual(len(snapshot.houses_from_moon), 9)

    def test_the_two_house_frames_are_anchored_independently(self):
        """
        Transits are read from the Lagna and from the natal Moon, and the two
        frames generally disagree. Collapsing them would silently pick a
        tradition.

        The frames must differ by exactly the rotation between the natal
        Lagna rashi and the natal Moon rashi. In THIS chart both fall in
        Meena, so the rotation is zero and the frames coincide — which is
        correct, not a bug. Asserting the rotation rather than mere
        inequality tests the mechanism on any chart.
        """
        snapshot = self.build()
        offset = ((self.natal["lagna"]["sign_index"]
                   - self.natal["planets"]["Chandra"]["sign_index"]) % 12)
        for name in snapshot.houses_from_lagna:
            with self.subTest(graha=name):
                self.assertEqual(
                    (snapshot.houses_from_moon[name]
                     - snapshot.houses_from_lagna[name]) % 12,
                    offset)

    def test_the_frames_diverge_on_a_chart_where_lagna_and_moon_differ(self):
        """The companion to the above, on a chart where the rotation is real."""
        # Sydney 1962 from the regression fixtures: Lagna in Kanya, Moon in
        # Kumbha, so the rotation between the frames is five signs. Chosen
        # from the fixture set rather than guessed — two charts picked by eye
        # both turned out to have Lagna and Moon in the same rashi.
        natal = JyotishChart(jde=2437975.1979166665,
                             lat=-33.8688, lon=151.2093)
        lagna_sign = natal.lagna.rashi_index
        moon_sign = natal.planets["Chandra"].rashi_index
        self.assertNotEqual(lagna_sign, moon_sign,
                            "fixture chart must have Lagna and Moon apart")
        from_lagna, from_moon = {}, {}
        for name, graha in self.transit_features.planets.items():
            from_lagna[name] = ((graha.sign - lagna_sign) % 12) + 1
            from_moon[name] = ((graha.sign - moon_sign) % 12) + 1
        self.assertNotEqual(from_lagna, from_moon)

    def test_house_numbers_are_in_range(self):
        snapshot = self.build()
        for frame in (snapshot.houses_from_lagna, snapshot.houses_from_moon):
            for name, house in frame.items():
                with self.subTest(graha=name):
                    self.assertIn(house, range(1, 13))

    def test_uncertainty_envelopes_carry_into_transits(self):
        """
        A transiting Saturn on a sign boundary is as unresolved as a natal
        one. Reusing the feature layer means this comes for free.
        """
        snapshot = self.build()
        for name, entry in snapshot.uncertainty.items():
            with self.subTest(graha=name):
                self.assertIn("accuracy_arcmin", entry)
                self.assertIn("boundary_warning", entry)

    def test_snapshot_serialises(self):
        import json
        json.dumps(self.build().to_dict())

    def test_transit_positions_differ_from_natal(self):
        """Guards against accidentally computing the natal chart twice."""
        snapshot = self.build()
        for name, entry in snapshot.planets.items():
            natal_longitude = self.natal["planets"][name]["longitude"]
            with self.subTest(graha=name):
                self.assertNotAlmostEqual(entry["longitude"], natal_longitude,
                                          places=3)


class TimingContextTest(unittest.TestCase):

    def test_timing_context_assembles_all_three_layers(self):
        chart = natal_chart()
        dasha = compute_vimshottari(
            chart.planets["Chandra"].longitude, BIRTH_LOCAL, depth=3)
        context = TimingContext(
            natal_snapshot=natal_snapshot(),
            dasha_stack=dasha.get_dasha_stack_at(TRANSIT_MOMENT),
            transit_snapshot=None,
            moment=TRANSIT_MOMENT,
        )
        self.assertIsNotNone(context.mahadasha)
        self.assertIsNotNone(context.antardasha)
        self.assertIsNotNone(context.pratyantardasha)

    def test_timing_context_serialises(self):
        import json
        chart = natal_chart()
        dasha = compute_vimshottari(
            chart.planets["Chandra"].longitude, BIRTH_LOCAL, depth=3)
        context = TimingContext(
            natal_snapshot=natal_snapshot(),
            dasha_stack=dasha.get_dasha_stack_at(TRANSIT_MOMENT),
            moment=TRANSIT_MOMENT)
        json.dumps(context.to_dict())


class ScopeBoundaryTest(unittest.TestCase):
    """Part 21 and Part 22: interfaces only. No prediction, no interpretation."""

    def test_module_computes_no_predictions(self):
        import engine.transit_interface as module
        with open(module.__file__, encoding="utf-8") as handle:
            source = handle.read().lower()
        for phrase in ("will bring", "the native", "auspicious result",
                       "predict", "favourable period", "remedy"):
            with self.subTest(phrase=phrase):
                # "predict" appears only in prose saying it is NOT done.
                if phrase == "predict":
                    self.assertNotIn("def predict", source)
                    continue
                self.assertNotIn(phrase, source)

    def test_out_of_scope_items_are_recorded(self):
        self.assertTrue(OUT_OF_SCOPE_FOR_V1_3)
        joined = " ".join(OUT_OF_SCOPE_FOR_V1_3).lower()
        for expected in ("gochara", "vedha", "ashtakavarga", "prediction"):
            with self.subTest(item=expected):
                self.assertIn(expected, joined)

    def test_no_gochara_rules_shipped(self):
        """No transit rule exists yet, in any profile."""
        from engine.rules import all_rules
        for rule in all_rules():
            with self.subTest(rule=rule.id):
                self.assertNotIn("transit", rule.id)
                self.assertNotIn("gochar", rule.id)

    def test_interfaces_are_data_only(self):
        """The dataclasses hold facts; they compute nothing."""
        snapshot = TransitSnapshot(moment=TRANSIT_MOMENT)
        self.assertEqual(snapshot.planets, {})
        self.assertEqual(snapshot.transit_to_natal_aspects, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
