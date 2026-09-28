"""
Transits, timing context and birth-time sensitivity (V1.4 Parts 16-20, 24)
----------------------------------------------------------------------------
Two modules that share a discipline: both report facts about time and neither
predicts anything.

The scope tests at the end matter as much as the calculation tests. V1.4 is a
calculation release, and the line between "Saturn enters Kumbha on this date"
and "this is a difficult period" is the line this whole engine is organised
around.
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
from engine.sensitivity import (
    DEFAULT_WINDOWS, WATCHED_VARGAS, analyse_birth_time,
    format_sensitivity_report,
)
from engine.timing import compute_vimshottari
from engine.transits import (
    EVENT_KINDS, build_timing_context, compute_transit_positions,
    get_transit_events_between, get_transit_snapshot, get_transits_between,
    significant_relationships,
)

BIRTH_LOCAL = datetime.datetime(1988, 8, 30, 20, 18)
BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)
MOMENT = datetime.datetime(2030, 6, 10, 12, 0)


def natal():
    return JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                        lat=26.9124, lon=75.7873)


# ── Part 17: transit positions ───────────────────────────────────────────────

class TransitPositionTest(unittest.TestCase):

    def setUp(self):
        self.snapshot = get_transit_snapshot(MOMENT, natal_chart=natal())

    def test_all_nine_grahas(self):
        self.assertEqual(len(self.snapshot.positions), 9)

    def test_positions_match_a_chart_built_at_the_same_moment(self):
        """
        The transit engine must reuse the natal ephemeris, not reimplement
        it. Building a chart directly at the same moment must agree exactly.
        """
        direct = JyotishChart(jde=jde_from_datetime(MOMENT), lat=0.0, lon=0.0)
        for name, position in self.snapshot.positions.items():
            with self.subTest(graha=name):
                self.assertAlmostEqual(position.longitude,
                                       direct.planets[name].longitude,
                                       places=9)

    def test_retrograde_and_nakshatra_are_carried(self):
        self.assertEqual(len(self.snapshot.retrograde_states), 9)
        self.assertEqual(len(self.snapshot.nakshatras), 9)
        for name, nakshatra in self.snapshot.nakshatras.items():
            with self.subTest(graha=name):
                self.assertTrue(nakshatra)

    def test_house_frames_from_natal_lagna_and_moon(self):
        for name, position in self.snapshot.positions.items():
            with self.subTest(graha=name):
                self.assertIn(position.house_from_natal_lagna, range(1, 13))
                self.assertIn(position.house_from_natal_moon, range(1, 13))

    def test_uncertainty_travels_with_transits(self):
        """Transit positions inherit the same measured envelopes."""
        for name, entry in self.snapshot.uncertainty.items():
            with self.subTest(graha=name):
                self.assertIn("accuracy_arcmin", entry)
                self.assertIn("boundary_warning", entry)

    def test_works_without_a_natal_chart(self):
        snapshot = get_transit_snapshot(MOMENT)
        self.assertEqual(len(snapshot.positions), 9)
        self.assertEqual(snapshot.relationships, [])

    def test_serialises(self):
        import json
        json.dumps(self.snapshot.to_dict())


# ── Part 18: transit-to-natal relationships ──────────────────────────────────

class RelationshipTest(unittest.TestCase):

    def setUp(self):
        self.natal = natal()
        self.snapshot = get_transit_snapshot(MOMENT, natal_chart=self.natal)

    def test_every_transit_against_every_natal_point(self):
        """Nine transiting grahas against nine natal grahas plus the Lagna."""
        self.assertEqual(len(self.snapshot.relationships), 9 * 10)

    def test_same_sign_and_separation_are_independent(self):
        """
        Part 18's requirement. There must exist a pair sharing a rashi while
        far apart, or far apart while close in degrees — otherwise the two
        fields are not really independent.
        """
        same_sign_far = [r for r in self.snapshot.relationships
                         if r.same_sign and r.angular_separation > 15.0]
        different_sign_close = [r for r in self.snapshot.relationships
                                if not r.same_sign
                                and r.angular_separation < 15.0]
        self.assertTrue(same_sign_far or different_sign_close,
                        "the two measures should be able to disagree")

    def test_same_sign_agrees_with_the_sign_indices(self):
        for relationship in self.snapshot.relationships:
            transit = self.snapshot.positions[relationship.transit_planet]
            if relationship.target_kind == "lagna":
                target_sign = self.natal.lagna.rashi_index
            else:
                target_sign = self.natal.planets[
                    relationship.natal_target].rashi_index
            with self.subTest(pair=(relationship.transit_planet,
                                    relationship.natal_target)):
                self.assertEqual(relationship.same_sign,
                                 transit.sign == target_sign)

    def test_separation_is_the_short_arc(self):
        for relationship in self.snapshot.relationships:
            with self.subTest(pair=(relationship.transit_planet,
                                    relationship.natal_target)):
                self.assertGreaterEqual(relationship.angular_separation, 0.0)
                self.assertLessEqual(relationship.angular_separation, 180.0)

    def test_house_distance_is_inclusive_one_to_twelve(self):
        for relationship in self.snapshot.relationships:
            with self.subTest(pair=(relationship.transit_planet,
                                    relationship.natal_target)):
                self.assertIn(relationship.house_distance, range(1, 13))

    def test_drishti_uses_the_shared_aspect_profile(self):
        """
        Part 18: drishti must come from the same profile as the natal engine.
        Every graha aspects the 7th, so a 7th-distance relationship must be
        flagged for any classical graha.
        """
        for relationship in self.snapshot.relationships:
            if relationship.transit_planet in ("Rahu", "Ketu"):
                continue
            if relationship.house_distance == 7:
                with self.subTest(pair=(relationship.transit_planet,
                                        relationship.natal_target)):
                    self.assertTrue(relationship.graha_drishti)

    def test_nodes_have_no_drishti_by_default(self):
        for relationship in self.snapshot.relationships:
            if relationship.transit_planet in ("Rahu", "Ketu"):
                with self.subTest(graha=relationship.transit_planet):
                    self.assertFalse(relationship.graha_drishti)

    def test_mars_special_aspects_are_honoured(self):
        for relationship in self.snapshot.relationships:
            if relationship.transit_planet != "Mangal":
                continue
            expected = relationship.house_distance in (4, 7, 8)
            with self.subTest(target=relationship.natal_target):
                self.assertEqual(relationship.graha_drishti, expected)

    def test_significant_filter_selects_only_relationships_that_hold(self):
        held = significant_relationships(self.snapshot.relationships)
        for relationship in held:
            with self.subTest(pair=(relationship.transit_planet,
                                    relationship.natal_target)):
                self.assertTrue(relationship.same_sign
                                or relationship.graha_drishti
                                or relationship.within_orb)


# ── Part 19: query and events ────────────────────────────────────────────────

class QueryTest(unittest.TestCase):

    def test_transits_between_returns_a_snapshot_per_step(self):
        start = datetime.datetime(2030, 1, 1)
        end = datetime.datetime(2030, 1, 11)
        snapshots = get_transits_between(start, end,
                                         datetime.timedelta(days=1))
        self.assertEqual(len(snapshots), 11)
        self.assertEqual(snapshots[0].moment, start)
        self.assertEqual(snapshots[-1].moment, end)

    def test_reversed_window_is_rejected(self):
        with self.assertRaises(ValueError):
            get_transits_between(datetime.datetime(2030, 2, 1),
                                 datetime.datetime(2030, 1, 1),
                                 datetime.timedelta(days=1))

    def test_zero_step_is_rejected(self):
        with self.assertRaises(ValueError):
            get_transits_between(datetime.datetime(2030, 1, 1),
                                 datetime.datetime(2030, 1, 2),
                                 datetime.timedelta(0))

    def test_sun_sign_ingress_is_found_and_dated(self):
        """
        The Sun changes rashi roughly monthly, so a 60-day window must contain
        at least one ingress, and the reported instant must be one where the
        sign genuinely differs a minute either side.
        """
        start = datetime.datetime(2030, 1, 1)
        end = datetime.datetime(2030, 3, 1)
        events = get_transit_events_between(start, end, planets=["Surya"],
                                            kinds=["sign_ingress"])
        self.assertTrue(events)
        for event in events:
            before = compute_transit_positions(
                event.moment - datetime.timedelta(minutes=2))["Surya"]
            after = compute_transit_positions(
                event.moment + datetime.timedelta(minutes=2))["Surya"]
            with self.subTest(when=event.moment):
                self.assertNotEqual(before.sign, after.sign)

    def test_nakshatra_ingress_is_found(self):
        events = get_transit_events_between(
            datetime.datetime(2030, 1, 1), datetime.datetime(2030, 1, 20),
            planets=["Surya"], kinds=["nakshatra_ingress"])
        self.assertTrue(events)

    def test_station_is_found_and_is_a_real_direction_change(self):
        """Mercury stations several times a year; catch one and verify it."""
        events = get_transit_events_between(
            datetime.datetime(2030, 1, 1), datetime.datetime(2030, 7, 1),
            planets=["Budha"],
            kinds=["station_retrograde", "station_direct"])
        self.assertTrue(events)
        for event in events:
            before = compute_transit_positions(
                event.moment - datetime.timedelta(hours=12))["Budha"]
            after = compute_transit_positions(
                event.moment + datetime.timedelta(hours=12))["Budha"]
            with self.subTest(when=event.moment):
                self.assertNotEqual(before.retrograde, after.retrograde)

    def test_events_are_chronological(self):
        events = get_transit_events_between(
            datetime.datetime(2030, 1, 1), datetime.datetime(2030, 4, 1),
            planets=["Surya", "Budha"])
        moments = [event.moment for event in events]
        self.assertEqual(moments, sorted(moments))

    def test_event_kinds_are_from_the_declared_vocabulary(self):
        events = get_transit_events_between(
            datetime.datetime(2030, 1, 1), datetime.datetime(2030, 3, 1),
            planets=["Surya"])
        for event in events:
            with self.subTest(kind=event.kind):
                self.assertIn(event.kind, EVENT_KINDS)

    def test_kind_filter_is_honoured(self):
        events = get_transit_events_between(
            datetime.datetime(2030, 1, 1), datetime.datetime(2030, 3, 1),
            planets=["Surya"], kinds=["sign_ingress"])
        for event in events:
            self.assertEqual(event.kind, "sign_ingress")


# ── Part 20: timing context ──────────────────────────────────────────────────

class TimingContextTest(unittest.TestCase):

    def setUp(self):
        self.natal = natal()
        self.dasha = compute_vimshottari(
            self.natal.planets["Chandra"].longitude, BIRTH_LOCAL, depth=3)
        self.context = build_timing_context(
            MOMENT, {"schema_version": "1.2.0"},
            dasha=self.dasha, natal_chart=self.natal)

    def test_all_three_layers_present(self):
        self.assertIsNotNone(self.context.mahadasha)
        self.assertIsNotNone(self.context.antardasha)
        self.assertIsNotNone(self.context.pratyantardasha)
        self.assertIsNotNone(self.context.transit_snapshot)

    def test_dasha_stack_agrees_with_the_dasha_engine(self):
        expected = self.dasha.get_dasha_stack_at(MOMENT)
        self.assertEqual(self.context.mahadasha, expected["mahadasha"])
        self.assertEqual(self.context.antardasha, expected["antardasha"])

    def test_shape_matches_the_brief(self):
        data = self.context.to_dict()
        self.assertIn("date", data)
        self.assertIn("dasha", data)
        self.assertIn("transits", data)
        for level in ("mahadasha", "antardasha", "pratyantardasha"):
            self.assertIn(level, data["dasha"])

    def test_dasha_lord_transits_are_selectable(self):
        lords = set(self.context.dasha_lords)
        for relationship in self.context.transits_of_dasha_lords():
            with self.subTest(graha=relationship.transit_planet):
                self.assertIn(relationship.transit_planet, lords)

    def test_works_without_a_dasha_or_a_chart(self):
        bare = build_timing_context(MOMENT, {"schema_version": "1.2.0"})
        self.assertEqual(bare.dasha_stack, {})
        self.assertIsNone(bare.transit_snapshot)

    def test_carries_no_score(self):
        """
        Part 20: no synthesis score yet.

        Checks for score-bearing FIELDS rather than the substring, because
        the context's own disclaimer note contains the word "score" — which
        is exactly the sort of false positive a crude substring test invites.
        """
        def walk(node, path="root"):
            if isinstance(node, dict):
                for key, value in node.items():
                    lowered = key.lower()
                    for banned in ("score", "rating", "favourab", "auspicio",
                                   "verdict"):
                        self.assertNotIn(
                            banned, lowered,
                            f"{path}.{key} looks like a synthesis verdict")
                    walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")

        walk(self.context.to_dict())

    def test_serialises(self):
        import json
        json.dumps(self.context.to_dict())


# ── Part 16: birth-time sensitivity ──────────────────────────────────────────

class SensitivityTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = analyse_birth_time(BIRTH_UTC, 26.9124, 75.7873)

    def test_all_default_windows_are_reported(self):
        self.assertEqual([w.window_minutes for w in self.report.windows],
                         sorted(DEFAULT_WINDOWS))

    def test_watches_the_items_the_brief_names(self):
        keys = set(self.report.baseline)
        for expected in ("lagna_sign", "lagna_nakshatra", "lagna_pada"):
            with self.subTest(item=expected):
                self.assertIn(expected, keys)
        for varga in WATCHED_VARGAS:
            with self.subTest(varga=varga):
                self.assertIn(f"{varga}_lagna", keys)

    def test_d60_lagna_is_unstable_in_the_regression_chart(self):
        """
        A real finding, pinned: the D60 Lagna of the documented example
        changes well inside a minute of the stated birth time.
        """
        tightest = self.report.windows[0]
        self.assertFalse(tightest.stable)
        self.assertTrue(any("D60" in change.item
                            for change in tightest.changes))

    def test_changes_are_ordered_by_proximity(self):
        for window in self.report.windows:
            offsets = [abs(c.offset_seconds) for c in window.changes
                       if c.key != "rules"]
            with self.subTest(window=window.window_minutes):
                self.assertEqual(offsets, sorted(offsets))

    def test_a_change_in_a_small_window_appears_in_every_larger_one(self):
        for smaller, larger in zip(self.report.windows,
                                   self.report.windows[1:]):
            smaller_keys = {c.key for c in smaller.changes}
            larger_keys = {c.key for c in larger.changes}
            with self.subTest(window=smaller.window_minutes):
                self.assertTrue(smaller_keys <= larger_keys)

    def test_reported_offsets_are_real_crossings(self):
        """
        At the reported offset the value must differ from the baseline, and
        a few seconds earlier it must not. That is what makes the number a
        crossing rather than a sampling artefact.
        """
        from engine.vargas import VargaConfig
        from engine.sensitivity.birth_time import _signature
        config = VargaConfig()

        def signature(offset):
            moment = BIRTH_UTC + datetime.timedelta(seconds=offset)
            chart = JyotishChart(jde=jde_from_datetime(moment),
                                 lat=26.9124, lon=75.7873)
            return _signature(chart, config, None)

        baseline = signature(0)
        for change in self.report.windows[-1].changes:
            if change.key == "rules":
                continue
            offset = change.offset_seconds
            step = 2 if offset > 0 else -2
            with self.subTest(item=change.item):
                self.assertNotEqual(signature(offset)[change.key],
                                    baseline[change.key])
                self.assertEqual(signature(offset - step)[change.key],
                                 baseline[change.key])

    def test_a_stable_chart_reports_stable(self):
        """
        A chart far from any boundary should be stable in a tight window.
        Uses a one-minute window and watches only the Lagna sign, which
        changes roughly every two hours.
        """
        report = analyse_birth_time(
            datetime.datetime(2000, 6, 15, 6, 0), 0.0, 0.0, windows=(1,))
        tightest = report.windows[0]
        self.assertFalse(any(c.key == "lagna_sign" for c in tightest.changes))

    def test_report_states_it_is_not_rectification(self):
        text = format_sensitivity_report(self.report)
        self.assertIn("NOT rectification", text)

    def test_serialises(self):
        import json
        data = self.report.to_dict()
        json.dumps(data)
        self.assertIn("NOT rectification", data["note"])


# ── Part 25: scope ───────────────────────────────────────────────────────────

class ScopeTest(unittest.TestCase):
    """V1.4 is a calculation release. These assert the line held."""

    def test_no_gochara_rules_shipped(self):
        from engine.rules import all_rules
        for rule in all_rules():
            with self.subTest(rule=rule.id):
                for banned in ("transit", "gochar", "sade", "vedha"):
                    self.assertNotIn(banned, rule.id.lower())

    def test_transit_modules_contain_no_judgement_vocabulary(self):
        import engine.transits.calculator as calculator
        import engine.transits.query as query
        import engine.transits.relationships as relationships
        for module in (calculator, query, relationships):
            with open(module.__file__, encoding="utf-8") as handle:
                source = handle.read().lower()
            with self.subTest(module=module.__name__):
                for banned in ("auspicious", "inauspicious", "malefic period",
                               "will bring", "the native will"):
                    self.assertNotIn(banned, source)

    def test_no_event_carries_a_verdict(self):
        events = get_transit_events_between(
            datetime.datetime(2030, 1, 1), datetime.datetime(2030, 3, 1),
            planets=["Surya"])
        for event in events:
            data = event.to_dict()
            with self.subTest(kind=event.kind):
                self.assertNotIn("good", data)
                self.assertNotIn("bad", data)
                self.assertNotIn("score", data)

    def test_sensitivity_never_suggests_a_time(self):
        import json
        blob = json.dumps(
            analyse_birth_time(BIRTH_UTC, 26.9124, 75.7873,
                               windows=(1,)).to_dict()).lower()
        for banned in ("rectif", "suggested time", "corrected time",
                       "likely birth"):
            with self.subTest(phrase=banned):
                self.assertNotIn(banned, blob.replace("not rectification", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
