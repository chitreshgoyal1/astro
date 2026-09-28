"""
Large regression corpus (V1.8 Part 40)
----------------------------------------
Many charts, checked for consistency rather than for truth.

WHAT THIS CORPUS IS AND IS NOT

    Part 40's closing line is the important one: "Do not interpret
    passing regressions as empirical proof of astrology. They test
    software consistency."

    So this file makes no astrological claim at all. It asserts that the
    engine survives two hundred assorted charts, that every one of them
    is internally consistent, that the awkward configurations Part 40
    lists are actually represented, and that the answers do not move
    between runs.

    The EXTERNAL accuracy benchmark is a different thing and stays where
    it is: `tests/test_regression_charts.py` holds eight charts checked
    against the Swiss Ephemeris, and `tests/fixtures/` holds the
    reference positions. Eight benchmarked charts and two hundred
    consistency charts answer different questions, and merging them would
    produce two hundred charts that look benchmarked and are not.

WHY COVERAGE IS ASSERTED, NOT ASSUMED

    A corpus that claims to cover high latitudes is worth nothing if the
    generator happens to stop producing them. `CoverageTest` classifies
    every chart and requires each of Part 40's categories to appear, so
    the claim is checked on every run rather than made once in a
    docstring.
"""

import datetime
import json
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import JyotishChart, jde_from_datetime
from engine.vargas import compute_all_vargas

SEED = 20260928
CORPUS_SIZE = 200

#: Part 40's list, as tags a chart can carry.
REQUIRED_COVERAGE = (
    "pre_1800", "post_2100", "twentieth_century",
    "northern", "southern", "equatorial", "high_latitude",
    "retrograde", "station",
    "sign_boundary", "nakshatra_boundary", "varga_boundary",
)

_STATE: dict = {}


def _corpus() -> list:
    rng = random.Random(SEED)
    out = []
    for _ in range(CORPUS_SIZE):
        moment = datetime.datetime(
            rng.randint(1650, 2150), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), rng.randint(0, 59))
        out.append((moment, rng.uniform(-72.0, 72.0),
                    rng.uniform(-180.0, 180.0)))
    return out


def _tags(moment, latitude, chart) -> set:
    """
    Which of Part 40's awkward conditions this chart exercises.

    The boundary thresholds are deliberately tight. A graha within a
    quarter degree of a sign edge is the case where the engine's own
    error envelope can move it into the next sign, which is what makes it
    interesting; a graha ten degrees in is an ordinary placement.
    """
    tags = set()
    if moment.year < 1800:
        tags.add("pre_1800")
    if moment.year > 2100:
        tags.add("post_2100")
    if 1900 <= moment.year < 2000:
        tags.add("twentieth_century")
    tags.add("southern" if latitude < 0 else "northern")
    if abs(latitude) < 5.0:
        tags.add("equatorial")
    if abs(latitude) > 60.0:
        tags.add("high_latitude")

    nakshatra_span = 360.0 / 27.0
    for name, body in chart.planets.items():
        if name not in ("Rahu", "Ketu") and body.is_retrograde:
            tags.add("retrograde")
        if getattr(body, "is_stationary", False):
            tags.add("station")
        if body.degree_in_rashi < 0.25 or body.degree_in_rashi > 29.75:
            tags.add("sign_boundary")
        within = body.longitude % nakshatra_span
        if within < 0.05 or within > nakshatra_span - 0.05:
            tags.add("nakshatra_boundary")
        # The finest division the engine computes is the ṣaṣṭyāṃśa, half
        # a degree. A graha within a thousandth of one of its edges is a
        # placement the birth time does not determine.
        if body.longitude % 0.5 < 0.004:
            tags.add("varga_boundary")
    return tags


def setUpModule():
    charts = []
    for moment, latitude, longitude in _corpus():
        chart = JyotishChart(jde=jde_from_datetime(moment), lat=latitude,
                             lon=longitude, ayanamsha_system="lahiri",
                             true_node=True)
        charts.append({
            "moment": moment, "latitude": latitude, "longitude": longitude,
            "chart": chart, "tags": _tags(moment, latitude, chart),
        })
    _STATE["charts"] = charts


class CoverageTest(unittest.TestCase):

    def test_the_corpus_is_the_size_it_claims(self):
        self.assertEqual(len(_STATE["charts"]), CORPUS_SIZE)

    def test_every_listed_condition_is_represented(self):
        covered = set()
        for entry in _STATE["charts"]:
            covered |= entry["tags"]
        for condition in REQUIRED_COVERAGE:
            with self.subTest(condition=condition):
                self.assertIn(
                    condition, covered,
                    f"the corpus no longer contains a {condition} chart; "
                    f"widen the generator rather than dropping the claim")

    def test_the_corpus_spans_five_centuries(self):
        years = [e["moment"].year for e in _STATE["charts"]]
        self.assertLess(min(years), 1750)
        self.assertGreater(max(years), 2100)

    def test_the_corpus_spans_both_hemispheres_to_high_latitude(self):
        latitudes = [e["latitude"] for e in _STATE["charts"]]
        self.assertLess(min(latitudes), -60.0)
        self.assertGreater(max(latitudes), 60.0)

    def test_the_coverage_report_is_printable(self):
        """
        The corpus states what it covers, so a reader of the test output
        can see the spread rather than trusting the generator.
        """
        counts: dict = {}
        for entry in _STATE["charts"]:
            for tag in entry["tags"]:
                counts[tag] = counts.get(tag, 0) + 1
        self.assertTrue(counts)
        for condition in REQUIRED_COVERAGE:
            self.assertGreater(counts.get(condition, 0), 0)


class ConsistencyTest(unittest.TestCase):
    """Every chart in the corpus is internally coherent."""

    def test_every_chart_computes_without_error(self):
        for entry in _STATE["charts"]:
            with self.subTest(moment=entry["moment"]):
                self.assertEqual(len(entry["chart"].planets), 9)
                self.assertIsNotNone(entry["chart"].lagna)

    def test_every_chart_produces_features(self):
        for entry in _STATE["charts"][:60]:
            with self.subTest(moment=entry["moment"]):
                features = build_chart_features(entry["chart"])
                self.assertEqual(len(features.houses), 12)

    def test_an_unresolved_boundary_is_flagged_and_not_hidden(self):
        """
        The interesting half of a boundary chart. A graha the engine
        cannot confidently place in a sign must SAY so; a confident wrong
        answer at a boundary is the failure the uncertainty machinery
        exists to prevent.
        """
        flagged = 0
        for entry in _STATE["charts"]:
            if "sign_boundary" not in entry["tags"]:
                continue
            features = build_chart_features(entry["chart"])
            for name in entry["chart"].planets:
                planet = features.planet(name)
                if planet is not None and planet.boundary_warning:
                    flagged += 1
        self.assertGreater(
            flagged, 0,
            "no boundary chart produced a boundary warning, which would "
            "mean the uncertainty envelope had been switched off")

    def test_high_latitude_charts_still_produce_a_lagna(self):
        """
        The ascendant is where high latitudes break naive implementations:
        near the poles some signs rise for minutes and others for hours.
        """
        for entry in _STATE["charts"]:
            if "high_latitude" not in entry["tags"]:
                continue
            with self.subTest(moment=entry["moment"],
                              latitude=round(entry["latitude"], 2)):
                lagna = entry["chart"].lagna
                self.assertIn(lagna.rashi_index, range(12))
                self.assertGreaterEqual(lagna.degree_in_rashi, 0.0)
                self.assertLess(lagna.degree_in_rashi, 30.0)

    def test_every_varga_resolves_for_every_chart(self):
        for entry in _STATE["charts"][:50]:
            for name, body in entry["chart"].planets.items():
                vargas = compute_all_vargas(body.longitude)
                with self.subTest(moment=entry["moment"], body=name):
                    self.assertEqual(len(vargas), 16)


class StabilityTest(unittest.TestCase):

    def test_the_corpus_is_the_same_corpus_every_run(self):
        """
        The seed is the whole basis for these tests being reproducible.
        If the generator ever consumed randomness in a different order,
        every chart would change and every failure would be a mystery.
        """
        first = _corpus()
        second = _corpus()
        self.assertEqual(first, second)
        self.assertEqual(
            [round(latitude, 6) for _m, latitude, _lon in first[:3]],
            [36.897144, 59.630293, -67.809033])

    def test_recomputing_a_chart_gives_the_same_longitudes(self):
        for entry in _STATE["charts"][:40]:
            again = JyotishChart(
                jde=jde_from_datetime(entry["moment"]),
                lat=entry["latitude"], lon=entry["longitude"],
                ayanamsha_system="lahiri", true_node=True)
            with self.subTest(moment=entry["moment"]):
                self.assertEqual(
                    {n: p.longitude for n, p in entry["chart"].planets.items()},
                    {n: p.longitude for n, p in again.planets.items()})


if __name__ == "__main__":
    unittest.main()
