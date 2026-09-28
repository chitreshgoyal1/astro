"""
Property and invariant tests (V1.8 Part 41)
---------------------------------------------
Facts that must hold for EVERY chart, checked against many.

WHAT A PROPERTY TEST IS FOR HERE

    The rest of this suite asserts particular values: Jupiter is in
    Vrishabha in the 1988 chart, this yoga forms, that window opens. Those
    catch regressions in what the engine computes.

    These catch a different thing: a rule the engine must never break,
    anywhere. A house number outside 1-12 is wrong for every chart ever
    cast, and a dasha sequence with a gap in it is wrong whether or not
    any fixture happens to notice.

    The distinction matters because the two fail differently. A fixture
    breaks when behaviour changes, which is often intended. An invariant
    breaks when behaviour becomes impossible, which never is.

DETERMINISTIC SEEDS (Part 41)

    `random.Random(SEED)` with a fixed seed, not the global generator.
    A property test that draws different inputs each run is a test that
    fails for somebody else and passes for you, and the first response to
    that is to disable it.

    So the inputs are pseudo-random and REPRODUCIBLE: the same hundred
    charts every time, on every machine, in every order. Widening the
    search is a deliberate act — change the seed, or the count, in a
    commit somebody can review.

WHAT THIS DOES NOT ESTABLISH

    Part 40's closing line applies here too. These are statements about
    software consistency. That Rahu is exactly opposite Ketu is a fact
    about the engine's arithmetic, not evidence that either signifies
    anything.
"""

import datetime
import json
import math
import os
import random
import sys
import unittest
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import (
    PLANET_NAMES, RASHI_NAMES, JyotishChart, jde_from_datetime,
)
from engine.timing.vimshottari import from_chart as vimshottari_from_chart
from engine.vargas import VARGA_ORDER, compute_all_vargas

#: Fixed. See the module docstring.
SEED = 20260928

#: How many charts the invariants are checked against. Chosen so the whole
#: file runs in a few seconds: an invariant suite that is slow gets run
#: less often, and one that is never run is worth nothing.
CHART_COUNT = 60


def _charts(count: int = CHART_COUNT) -> list:
    """
    A reproducible spread of charts.

    Deliberately extreme in places: latitudes past the polar circles,
    dates from the 17th century to the 22nd, and times that fall near
    midnight in every zone. Those are where the arithmetic goes wrong, and
    a corpus of comfortable charts proves the comfortable case.
    """
    rng = random.Random(SEED)
    out = []
    for _ in range(count):
        year = rng.randint(1650, 2150)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        hour = rng.randint(0, 23)
        minute = rng.randint(0, 59)
        latitude = rng.uniform(-72.0, 72.0)
        longitude = rng.uniform(-180.0, 180.0)
        moment = datetime.datetime(year, month, day, hour, minute)
        out.append((moment, latitude, longitude))
    return out


_CACHE: dict = {}


def _chart_for(moment, latitude, longitude) -> JyotishChart:
    key = (moment, round(latitude, 6), round(longitude, 6))
    if key not in _CACHE:
        _CACHE[key] = JyotishChart(
            jde=jde_from_datetime(moment), lat=latitude, lon=longitude,
            ayanamsha_system="lahiri", true_node=True)
    return _CACHE[key]


class _Corpus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.samples = _charts()
        cls.charts = [_chart_for(*sample) for sample in cls.samples]


# ── longitudes ──────────────────────────────────────────────────────────────

class LongitudeTest(_Corpus):

    def test_every_longitude_is_normalised(self):
        for chart, sample in zip(self.charts, self.samples):
            for name, body in chart.planets.items():
                with self.subTest(chart=sample[0], body=name):
                    self.assertGreaterEqual(body.longitude, 0.0)
                    self.assertLess(body.longitude, 360.0)
                    self.assertFalse(math.isnan(body.longitude))

    def test_the_lagna_is_normalised(self):
        for chart, sample in zip(self.charts, self.samples):
            with self.subTest(chart=sample[0]):
                self.assertGreaterEqual(chart.lagna.longitude, 0.0)
                self.assertLess(chart.lagna.longitude, 360.0)

    def test_sign_index_agrees_with_longitude(self):
        """
        `rashi_index` is not stored independently of the longitude; if it
        ever were, this is where the two would part company.
        """
        for chart, sample in zip(self.charts, self.samples):
            for name, body in chart.planets.items():
                with self.subTest(chart=sample[0], body=name):
                    self.assertEqual(body.rashi_index,
                                     int(body.longitude // 30) % 12)
                    self.assertEqual(body.rashi,
                                     RASHI_NAMES[body.rashi_index])

    def test_degree_in_sign_is_within_one_sign(self):
        for chart in self.charts:
            for name, body in chart.planets.items():
                with self.subTest(body=name):
                    self.assertGreaterEqual(body.degree_in_rashi, 0.0)
                    self.assertLess(body.degree_in_rashi, 30.0)


class NodeTest(_Corpus):

    def test_rahu_and_ketu_are_exactly_opposite(self):
        """
        Ketu is not computed; it is Rahu plus 180 degrees. The invariant
        is therefore exact rather than approximate, and a tolerance here
        would hide a second computation appearing.
        """
        for chart, sample in zip(self.charts, self.samples):
            rahu = chart.planets["Rahu"].longitude
            ketu = chart.planets["Ketu"].longitude
            with self.subTest(chart=sample[0]):
                separation = (ketu - rahu) % 360.0
                self.assertAlmostEqual(separation, 180.0, places=9)

    def test_the_nodes_are_always_six_signs_apart(self):
        for chart in self.charts:
            rahu = chart.planets["Rahu"].rashi_index
            ketu = chart.planets["Ketu"].rashi_index
            self.assertEqual((ketu - rahu) % 12, 6)

    def test_the_nodes_retrograde_together(self):
        for chart in self.charts:
            self.assertEqual(chart.planets["Rahu"].is_retrograde,
                             chart.planets["Ketu"].is_retrograde)


# ── houses ──────────────────────────────────────────────────────────────────

class HouseTest(_Corpus):

    def test_every_house_number_is_in_range(self):
        for chart, sample in zip(self.charts, self.samples):
            features = build_chart_features(chart)
            for name in PLANET_NAMES:
                planet = features.planet(name)
                if planet is None:
                    continue
                with self.subTest(chart=sample[0], body=name):
                    self.assertIn(planet.house, range(1, 13))

    def test_house_follows_from_the_lagna_in_whole_sign(self):
        for chart in self.charts:
            features = build_chart_features(chart)
            lagna = chart.lagna.rashi_index
            for name in PLANET_NAMES:
                planet = features.planet(name)
                if planet is None:
                    continue
                with self.subTest(body=name):
                    self.assertEqual(planet.house,
                                     ((planet.sign - lagna) % 12) + 1)

    def test_the_twelve_houses_hold_the_twelve_signs_once_each(self):
        for chart in self.charts:
            features = build_chart_features(chart)
            signs = [h.sign for h in features.houses.values()]
            self.assertEqual(sorted(signs), list(range(12)))


# ── vargas ──────────────────────────────────────────────────────────────────

class VargaTest(_Corpus):

    def test_every_varga_sign_is_valid(self):
        for chart, sample in zip(self.charts, self.samples):
            for name, body in chart.planets.items():
                vargas = compute_all_vargas(body.longitude)
                for key, placement in vargas.items():
                    with self.subTest(chart=sample[0], body=name, varga=key):
                        self.assertIn(placement.rashi_index, range(12))
                        self.assertEqual(placement.rashi,
                                         RASHI_NAMES[placement.rashi_index])

    def test_every_registered_varga_is_produced(self):
        for chart in self.charts[:10]:
            for body in chart.planets.values():
                self.assertEqual(sorted(compute_all_vargas(body.longitude)),
                                 sorted(VARGA_ORDER))

    def test_d1_is_the_rashi_itself(self):
        """The identity case. A D1 that drifted would be invisible."""
        for chart in self.charts:
            for body in chart.planets.values():
                self.assertEqual(
                    compute_all_vargas(body.longitude)["D1"].rashi_index,
                    body.rashi_index)

    def test_a_varga_is_a_pure_function_of_longitude(self):
        rng = random.Random(SEED + 1)
        for _ in range(200):
            longitude = rng.uniform(0.0, 360.0)
            self.assertEqual(
                {k: v.rashi_index
                 for k, v in compute_all_vargas(longitude).items()},
                {k: v.rashi_index
                 for k, v in compute_all_vargas(longitude).items()})


# ── dasha ───────────────────────────────────────────────────────────────────

class DashaTest(_Corpus):

    def test_the_sequence_is_continuous_and_never_overlaps(self):
        """
        Part 41 names both, and they are different failures: a gap loses
        time and an overlap invents it. Checked as exact equality of one
        period's end and the next one's start, because the Vimshottari
        stack is computed in `Fraction` arithmetic and a tolerance would
        conceal a float creeping in.
        """
        for chart, sample in zip(self.charts[:20], self.samples[:20]):
            dasha = vimshottari_from_chart(chart, sample[0])
            periods = dasha.mahadashas
            with self.subTest(chart=sample[0]):
                self.assertTrue(periods)
                for earlier, later in zip(periods, periods[1:]):
                    self.assertEqual(earlier.end, later.start)

    def test_sub_periods_exactly_fill_their_parent(self):
        for chart, sample in zip(self.charts[:20], self.samples[:20]):
            dasha = vimshottari_from_chart(chart, sample[0])
            for period in dasha.mahadashas:
                children = period.children
                if not children:
                    continue
                with self.subTest(lord=period.lord):
                    self.assertEqual(children[0].start, period.start)
                    self.assertEqual(children[-1].end, period.end)
                    for earlier, later in zip(children, children[1:]):
                        self.assertEqual(earlier.end, later.start)

    def test_the_nine_lords_appear_in_the_traditional_order(self):
        order = ("Ketu", "Shukra", "Surya", "Chandra", "Mangal", "Rahu",
                 "Guru", "Shani", "Budha")
        for chart, sample in zip(self.charts[:20], self.samples[:20]):
            dasha = vimshottari_from_chart(chart, sample[0])
            lords = [p.lord for p in dasha.mahadashas]
            start = order.index(lords[0])
            expected = [order[(start + i) % 9] for i in range(len(lords))]
            with self.subTest(chart=sample[0]):
                self.assertEqual(lords, expected)

    def test_a_lookup_inside_a_period_returns_that_period(self):
        for chart, sample in zip(self.charts[:15], self.samples[:15]):
            dasha = vimshottari_from_chart(chart, sample[0])
            for period in dasha.mahadashas[:3]:
                middle = period.start + (period.end - period.start) / 2
                with self.subTest(lord=period.lord):
                    found = dasha.get_period_at(middle, level="mahadasha")
                    self.assertIsNotNone(found)
                    self.assertEqual(found.lord, period.lord)


# ── serialisation ───────────────────────────────────────────────────────────

class SerialisationTest(_Corpus):

    def test_every_snapshot_round_trips_through_json(self):
        from engine.snapshot import build_snapshot

        for chart, sample in zip(self.charts[:12], self.samples[:12]):
            features = build_chart_features(chart)
            snapshot = build_snapshot(chart, features,
                                      birth_datetime=sample[0])
            payload = snapshot.to_dict()
            with self.subTest(chart=sample[0]):
                restored = json.loads(json.dumps(payload, default=str))
                self.assertEqual(
                    json.dumps(restored, sort_keys=True, default=str),
                    json.dumps(payload, sort_keys=True, default=str))

    def test_a_snapshot_contains_no_engine_objects(self):
        """
        The boundary, checked from the other side: anything a snapshot
        carries must survive `json.dumps` without `default=`.
        """
        from engine.snapshot import build_snapshot

        for chart, sample in zip(self.charts[:8], self.samples[:8]):
            features = build_chart_features(chart)
            snapshot = build_snapshot(chart, features,
                                      birth_datetime=sample[0])
            with self.subTest(chart=sample[0]):
                json.dumps(snapshot.to_dict())


# ── determinism ─────────────────────────────────────────────────────────────

class DeterminismTest(_Corpus):

    def test_the_same_inputs_give_the_same_chart(self):
        for moment, latitude, longitude in self.samples[:15]:
            first = JyotishChart(jde=jde_from_datetime(moment), lat=latitude,
                                 lon=longitude, ayanamsha_system="lahiri")
            second = JyotishChart(jde=jde_from_datetime(moment), lat=latitude,
                                  lon=longitude, ayanamsha_system="lahiri")
            with self.subTest(moment=moment):
                self.assertEqual(
                    {n: p.longitude for n, p in first.planets.items()},
                    {n: p.longitude for n, p in second.planets.items()})

    def test_synthesis_is_deterministic_across_the_corpus(self):
        from engine.synthesis import SynthesisProfile, synthesise
        from engine.transits import get_transit_snapshot

        moment = datetime.datetime(2026, 6, 1, 12)
        for chart, sample in zip(self.charts[:6], self.samples[:6]):
            features = build_chart_features(chart)
            dasha = vimshottari_from_chart(chart, sample[0])
            transits = get_transit_snapshot(moment, natal_chart=chart)
            runs = [
                synthesise(features, moment=moment, dasha=dasha,
                           transit_snapshot=transits,
                           profile=SynthesisProfile.STANDARD).to_dict()
                for _ in range(2)]
            with self.subTest(chart=sample[0]):
                self.assertEqual(json.dumps(runs[0], sort_keys=True,
                                            default=str),
                                 json.dumps(runs[1], sort_keys=True,
                                            default=str))


# ── source identifiers ──────────────────────────────────────────────────────

class SourceResolutionTest(unittest.TestCase):

    def test_every_witness_id_a_rule_cites_resolves(self):
        from engine.sources.editions import witness_by_id
        from engine.sources.registry import all_recorded_evidence

        for evidence in all_recorded_evidence():
            for witness_id in evidence.witness_ids:
                with self.subTest(rule=evidence.subject, witness=witness_id):
                    self.assertIsNotNone(witness_by_id(witness_id))

    def test_every_conflict_a_rule_cites_resolves(self):
        from engine.sources.registry import (
            all_recorded_evidence, conflict_by_id,
        )

        for evidence in all_recorded_evidence():
            for conflict_id in evidence.conflicts:
                with self.subTest(rule=evidence.subject,
                                  conflict=conflict_id):
                    self.assertIsNotNone(conflict_by_id(conflict_id))

    def test_every_domain_mapping_citation_resolves(self):
        from engine.sources.editions import witness_by_id
        from engine.synthesis.domains import all_mappings

        for mapping in all_mappings():
            for witness_id in mapping.source_ref_ids:
                with self.subTest(domain=mapping.domain,
                                  witness=witness_id):
                    self.assertIsNotNone(witness_by_id(witness_id))

    def test_every_gochara_rule_citation_resolves(self):
        from engine.gochara import all_rules
        from engine.sources.editions import witness_by_id

        for rule in all_rules():
            for witness_id in rule.source_ref_ids:
                with self.subTest(planet=rule.planet, witness=witness_id):
                    self.assertIsNotNone(witness_by_id(witness_id))


if __name__ == "__main__":
    unittest.main()
