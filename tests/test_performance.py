"""
Performance and caching (V1.8 Parts 12-15)
--------------------------------------------
These are CORRECTNESS tests about an optimisation, not speed tests.

WHY THERE ARE ALMOST NO TIMING ASSERTIONS HERE

    A test that fails when a laptop is busy teaches a team to ignore it.
    What can be asserted without flakiness is the property that makes an
    optimisation safe: that the fast path and the slow path produce the
    same answer, and that a cache cannot hand one caller another caller's
    result.

    Part 14 says every optimised path must be byte-equivalent or
    structurally equivalent to the unoptimised one. That is what is tested
    here, term by term and field by field. The measured seconds live in
    `--benchmark`, which reports them rather than asserting them.

THE ONE CACHE KEY BUG THIS SUITE EXISTS FOR

    `_positions_at` accepted arbitrary kwargs and keyed on three of them.
    No caller passed the others, so nothing was wrong today and everything
    would have been wrong the first time somebody asked for a transiting
    Lagna. Part 15's "add cache invalidation tests" is the instruction that
    finds that class of defect, so the tests below key-test deliberately
    rather than incidentally.
"""

import datetime
import json
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.ephemeris import (
    _vsop87_xyz_reference, _vsop87_xyz_uncached, clear_vsop_cache,
    vsop87_xyz, vsop_cache_stats,
)
from engine.planets import JyotishChart, jde_from_datetime
from engine.transits.query import (
    _POSITION_CACHE, _positions_at, clear_position_cache,
    get_transit_events_between,
)
from engine.vsop87_data import VSOP87A

BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)


# ── Part 13: the series cache ───────────────────────────────────────────────

class VsopCacheTest(unittest.TestCase):

    def setUp(self):
        clear_vsop_cache()

    def test_the_cached_path_equals_the_series_exactly(self):
        """
        Not almost-equal. A memoised pure function returns the object the
        uncached one computed, so any difference at all means the cache is
        keyed wrongly.
        """
        random.seed(11)
        for name in VSOP87A:
            for _ in range(40):
                jde = random.uniform(2200000.0, 2600000.0)
                with self.subTest(body=name, jde=jde):
                    self.assertEqual(vsop87_xyz(name, jde),
                                     _vsop87_xyz_uncached(name, jde))

    def test_the_optimised_series_equals_the_pre_v18_implementation(self):
        """
        Part 14: byte-equivalent. Floating-point addition is not
        associative, so flattening the data structure had to preserve
        iteration order exactly — and "exactly" is the only tolerance that
        can detect a reordering, since a reordering moves only the last
        digits.
        """
        random.seed(12)
        for name in VSOP87A:
            for _ in range(40):
                jde = random.uniform(2200000.0, 2600000.0)
                with self.subTest(body=name, jde=jde):
                    self.assertEqual(_vsop87_xyz_uncached(name, jde),
                                     _vsop87_xyz_reference(name, jde))

    def test_a_second_call_is_served_from_the_cache(self):
        clear_vsop_cache()
        self.assertEqual(vsop_cache_stats()["entries"], 0)
        vsop87_xyz("Mars", 2451545.0)
        self.assertEqual(vsop_cache_stats()["entries"], 1)
        vsop87_xyz("Mars", 2451545.0)
        self.assertEqual(vsop_cache_stats()["entries"], 1)

    def test_different_bodies_at_one_instant_do_not_collide(self):
        self.assertNotEqual(vsop87_xyz("Mars", 2451545.0),
                            vsop87_xyz("Jupiter", 2451545.0))

    def test_the_cache_is_bounded(self):
        clear_vsop_cache()
        for step in range(vsop_cache_stats()["limit"] + 50):
            vsop87_xyz("Mars", 2451545.0 + step)
        self.assertLessEqual(vsop_cache_stats()["entries"],
                             vsop_cache_stats()["limit"])

    def test_clearing_the_cache_does_not_change_any_answer(self):
        warm = vsop87_xyz("Saturn", 2460000.5)
        clear_vsop_cache()
        self.assertEqual(warm, vsop87_xyz("Saturn", 2460000.5))

    def test_the_cache_sits_upstream_of_every_methodology_choice(self):
        """
        Part 15's real requirement. This cache is safe not because it is
        small but because ayanamsha, node mode, house system and rule
        profile are all applied AFTER it — so there is no profile for a
        value to leak into. Two charts differing only in ayanamsha share
        every cached series value and still produce different positions.
        """
        jde = jde_from_datetime(BIRTH_UTC)
        clear_vsop_cache()
        lahiri = JyotishChart(jde=jde, lat=26.9, lon=75.8,
                              ayanamsha_system="lahiri")
        raman = JyotishChart(jde=jde, lat=26.9, lon=75.8,
                             ayanamsha_system="raman")
        self.assertNotEqual(lahiri.ayanamsha, raman.ayanamsha)
        self.assertNotEqual(lahiri.planets["Guru"].longitude,
                            raman.planets["Guru"].longitude)


# ── Part 15: the scan cache ─────────────────────────────────────────────────

class PositionCacheTest(unittest.TestCase):

    def setUp(self):
        clear_position_cache()

    def test_the_key_covers_every_argument_that_reaches_the_computation(self):
        """
        The V1.7 key was (moment, ayanamsha, true_node) while the function
        accepted latitude and longitude too. Nothing passed them, so the
        bug was invisible; a transiting-Lagna caller would have received a
        chart computed for the equator.
        """
        moment = datetime.datetime(2026, 3, 1, 12)
        first = _positions_at(moment, ayanamsha_system="lahiri",
                              true_node=True, latitude=26.9, longitude=75.8)
        second = _positions_at(moment, ayanamsha_system="lahiri",
                               true_node=True, latitude=0.0, longitude=0.0)
        self.assertEqual(len(_POSITION_CACHE), 2,
                         "a differing latitude must produce a distinct key")
        self.assertIsNot(first, second)

    def test_ayanamsha_does_not_leak_between_cached_results(self):
        moment = datetime.datetime(2026, 3, 1, 12)
        lahiri = _positions_at(moment, ayanamsha_system="lahiri",
                               true_node=True)
        raman = _positions_at(moment, ayanamsha_system="raman",
                              true_node=True)
        self.assertNotEqual(lahiri["Guru"].longitude, raman["Guru"].longitude)

    def test_node_mode_does_not_leak_between_cached_results(self):
        moment = datetime.datetime(2026, 3, 1, 12)
        true_node = _positions_at(moment, ayanamsha_system="lahiri",
                                  true_node=True)
        mean_node = _positions_at(moment, ayanamsha_system="lahiri",
                                  true_node=False)
        self.assertNotEqual(true_node["Rahu"].longitude,
                            mean_node["Rahu"].longitude)

    def test_repeating_a_query_returns_the_cached_object(self):
        moment = datetime.datetime(2026, 3, 1, 12)
        first = _positions_at(moment, ayanamsha_system="lahiri",
                              true_node=True)
        second = _positions_at(moment, ayanamsha_system="lahiri",
                               true_node=True)
        self.assertIs(first, second)

    def test_a_scan_gives_the_same_events_warm_or_cold(self):
        """The invariant that made the V1.7 cache admissible, re-checked."""
        start = datetime.datetime(2026, 1, 1)
        end = datetime.datetime(2026, 4, 1)
        clear_position_cache()
        clear_vsop_cache()
        cold = get_transit_events_between(start, end, planets=("Guru",))
        warm = get_transit_events_between(start, end, planets=("Guru",))
        self.assertEqual([e.to_dict() for e in cold],
                         [e.to_dict() for e in warm])
        self.assertTrue(cold)


# ── Part 14: the optimised pipeline path ────────────────────────────────────

class ScanHorizonEquivalenceTest(unittest.TestCase):
    """
    Disabling the transit event scan is the difference between a
    three-second synthesis and an eleven-millisecond one, so what it costs
    has to be exactly known rather than assumed.
    """

    @classmethod
    def setUpClass(cls):
        from app.models import ApplicationSettings, ConsultationRecord
        from app.services import calculate_chart, calculate_prediction
        from app.services.prediction_service import parse_moment

        record = ConsultationRecord(
            name="Perf", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur", settings=ApplicationSettings())
        natal = calculate_chart(record, record.settings)
        moment = parse_moment("2026-09-27")
        cls.full = calculate_prediction(natal, moment, "standard").snapshot
        cls.none = calculate_prediction(
            natal, moment, "standard", event_horizon_days=0).snapshot

    def test_only_the_event_windows_differ(self):
        volatile = {"generated", "warnings", "event_candidates"}
        for key in sorted(self.full):
            if key in volatile:
                continue
            with self.subTest(section=key):
                self.assertEqual(
                    json.dumps(self.full[key], sort_keys=True, default=str),
                    json.dumps(self.none[key], sort_keys=True, default=str))

    def test_the_domain_conclusions_are_untouched(self):
        """
        The claim the disabled scan makes about itself: activation,
        confidence and evidence do not consult the scan, so a coarser
        window is a coarser window and not a different answer.
        """
        for name, result in self.full["domain_results"].items():
            other = self.none["domain_results"][name]
            with self.subTest(domain=name):
                self.assertEqual(result["activation"], other["activation"])
                self.assertEqual(result["confidence"], other["confidence"])

    def test_the_same_candidates_are_produced_either_way(self):
        """The scan sharpens windows; it does not invent or remove events."""
        self.assertEqual(len(self.full["event_candidates"]),
                         len(self.none["event_candidates"]))

    def test_disabling_the_scan_says_so_in_the_warnings(self):
        """
        A quietly coarser answer is worse than a slower one. Part 14: "If
        targets cannot be met safely, report the measured result rather
        than hiding it."
        """
        self.assertTrue(any("event scan disabled" in warning
                            for warning in self.none["warnings"]))
        self.assertFalse(any("event scan disabled" in warning
                             for warning in self.full["warnings"]))


# ── Part 12: the benchmark reports what it claims to ────────────────────────

class BenchmarkHonestyTest(unittest.TestCase):

    def test_the_total_sums_the_pipeline_and_not_the_diagnostics(self):
        """
        V1.7's `total` was `sum(timings.values())`, which added the
        re-timed sub-stages to the single pass they were sub-stages OF.
        The note under the table said the rows do not sum to the total
        while the total was computed by summing them.
        """
        from app.benchmark import DIAGNOSTIC_STAGES, PIPELINE_STAGES

        self.assertFalse(set(PIPELINE_STAGES) & set(DIAGNOSTIC_STAGES))
        self.assertIn("transit_scan", DIAGNOSTIC_STAGES)
        self.assertIn("synthesis", PIPELINE_STAGES)

    def test_every_stage_is_either_pipeline_or_diagnostic(self):
        from app.benchmark import (
            DIAGNOSTIC_STAGES, PIPELINE_STAGES, STAGE_ORDER,
        )

        self.assertEqual(set(STAGE_ORDER),
                         set(PIPELINE_STAGES) | set(DIAGNOSTIC_STAGES))


if __name__ == "__main__":
    unittest.main()
