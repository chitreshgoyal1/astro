"""
Ashtakavarga (V1.4 Parts 10, 11, 24)
--------------------------------------
The strongest tests available here are INVARIANTS. A bindu table is 96 small
integers, and a single mistyped entry is invisible on inspection but shows up
immediately as a total that misses its classical figure.

Those totals — 48, 49, 39, 54, 56, 52, 39, summing to 337 — are fixed by the
tables and independent of any chart, so they catch a typo without needing a
reference ephemeris.

The Sun's table is additionally checked against the witness (BPHS ch.66
verses 43-45), transposed from the house-by-house form the text gives.
"""

# V1.4.

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.ashtakavarga import (
    AV_GRAHAS, BINDU_TABLES, CLASSICAL_TOTALS, CONTRIBUTORS, SARVA_TOTAL,
    VERIFIED_AGAINST_WITNESS, compute_all_bhinna, compute_ashtakavarga,
    compute_bhinna, compute_sarva, ekadhipatya_sodhana, house_totals,
    reference_signs_from_chart, sign_totals, trikona_sodhana,
)
from engine.planets import JyotishChart, jde_from_datetime

BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)


def natal():
    return JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                        lat=26.9124, lon=75.7873)


class TableIntegrityTest(unittest.TestCase):
    """Invariants that catch a mistyped table without any chart."""

    def test_every_graha_has_a_table(self):
        self.assertEqual(set(BINDU_TABLES), set(AV_GRAHAS))

    def test_every_table_has_all_eight_contributors(self):
        for planet, table in BINDU_TABLES.items():
            with self.subTest(planet=planet):
                self.assertEqual(set(table), set(CONTRIBUTORS))

    def test_house_numbers_are_in_range(self):
        for planet, table in BINDU_TABLES.items():
            for contributor, houses in table.items():
                with self.subTest(planet=planet, contributor=contributor):
                    for house in houses:
                        self.assertIn(house, range(1, 13))

    def test_no_duplicate_house_in_any_row(self):
        for planet, table in BINDU_TABLES.items():
            for contributor, houses in table.items():
                with self.subTest(planet=planet, contributor=contributor):
                    self.assertEqual(len(houses), len(set(houses)))

    def test_each_table_sums_to_its_classical_total(self):
        """The load-bearing invariant. A single typo fails here."""
        for planet, table in BINDU_TABLES.items():
            total = sum(len(houses) for houses in table.values())
            with self.subTest(planet=planet):
                self.assertEqual(total, CLASSICAL_TOTALS[planet])

    def test_classical_totals_sum_to_337(self):
        self.assertEqual(sum(CLASSICAL_TOTALS.values()), SARVA_TOTAL)

    def test_sun_table_matches_the_witness(self):
        """
        BPHS ch.66.43-45 gives the Sun's rekhaprada houses contributor by
        contributor. This is that list, transposed from the house-by-house
        form the text uses.
        """
        expected = {
            "Surya":   (1, 2, 4, 7, 8, 9, 10, 11),
            "Chandra": (3, 6, 10, 11),
            "Mangal":  (1, 2, 4, 7, 8, 9, 10, 11),
            "Budha":   (3, 5, 6, 9, 10, 11, 12),
            "Guru":    (5, 6, 9, 11),
            "Shukra":  (6, 7, 12),
            "Shani":   (1, 2, 4, 7, 8, 9, 10, 11),
            "Lagna":   (3, 4, 6, 10, 11, 12),
        }
        self.assertEqual(BINDU_TABLES["Surya"], expected)

    def test_only_the_sun_claims_witness_verification(self):
        """
        Part 23: no new rule ships with a fabricated citation. The other six
        tables are located in the same chapter but their OCR is damaged, so
        they are NOT claimed as verified.
        """
        self.assertEqual(VERIFIED_AGAINST_WITNESS, ("Surya",))


class BhinnaTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chart = natal()
        cls.references = reference_signs_from_chart(cls.chart)
        cls.bhinna = compute_all_bhinna(cls.references)

    def test_eight_reference_points_including_the_lagna(self):
        self.assertEqual(set(self.references), set(CONTRIBUTORS))
        self.assertIn("Lagna", self.references)

    def test_nodes_are_not_contributors(self):
        self.assertNotIn("Rahu", self.references)
        self.assertNotIn("Ketu", self.references)

    def test_one_chart_per_graha(self):
        self.assertEqual(set(self.bhinna), set(AV_GRAHAS))

    def test_totals_match_the_classical_figures(self):
        for planet, chart in self.bhinna.items():
            with self.subTest(planet=planet):
                self.assertEqual(chart.total, CLASSICAL_TOTALS[planet])

    def test_every_sign_has_between_zero_and_eight_bindus(self):
        for planet, chart in self.bhinna.items():
            for sign in range(12):
                with self.subTest(planet=planet, sign=sign):
                    count = chart.bindus_in_sign(sign)
                    self.assertGreaterEqual(count, 0)
                    self.assertLessEqual(count, 8)

    def test_all_twelve_signs_are_present(self):
        for planet, chart in self.bhinna.items():
            with self.subTest(planet=planet):
                self.assertEqual(sorted(chart.bindus_by_sign), list(range(12)))

    def test_house_lookup_agrees_with_sign_lookup(self):
        lagna_sign = self.chart.lagna.rashi_index
        for planet, chart in self.bhinna.items():
            for house in range(1, 13):
                sign = (lagna_sign + house - 1) % 12
                with self.subTest(planet=planet, house=house):
                    self.assertEqual(chart.bindus_in_house(house, lagna_sign),
                                     chart.bindus_in_sign(sign))

    def test_contributions_are_recorded_per_contributor(self):
        for planet, chart in self.bhinna.items():
            with self.subTest(planet=planet):
                self.assertEqual(set(chart.contributions), set(CONTRIBUTORS))

    def test_rotating_every_reference_rotates_the_result(self):
        """
        A structural property: shifting every reference point by one sign
        shifts the whole chart by one sign. Catches an off-by-one in the
        house-to-sign arithmetic.
        """
        shifted = {name: (sign + 1) % 12
                   for name, sign in self.references.items()}
        rotated = compute_bhinna("Guru", shifted)
        original = self.bhinna["Guru"]
        for sign in range(12):
            with self.subTest(sign=sign):
                self.assertEqual(rotated.bindus_in_sign((sign + 1) % 12),
                                 original.bindus_in_sign(sign))

    def test_unknown_graha_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_bhinna("Rahu", self.references)


class SarvaTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chart = natal()
        cls.bhinna = compute_all_bhinna(reference_signs_from_chart(cls.chart))
        cls.sarva = compute_sarva(cls.bhinna)

    def test_total_is_337(self):
        self.assertEqual(self.sarva.total, SARVA_TOTAL)

    def test_each_sign_is_the_sum_of_the_seven_charts(self):
        for sign in range(12):
            expected = sum(chart.bindus_in_sign(sign)
                           for chart in self.bhinna.values())
            with self.subTest(sign=sign):
                self.assertEqual(self.sarva.bindus_in_sign(sign), expected)

    def test_each_sign_is_between_zero_and_fifty_six(self):
        for sign in range(12):
            with self.subTest(sign=sign):
                count = self.sarva.bindus_in_sign(sign)
                self.assertGreaterEqual(count, 0)
                self.assertLessEqual(count, 56)

    def test_house_totals_sum_to_337(self):
        totals = house_totals(self.sarva, self.chart.lagna.rashi_index)
        self.assertEqual(sum(totals.values()), SARVA_TOTAL)
        self.assertEqual(sorted(totals), list(range(1, 13)))

    def test_sign_totals_cover_all_twelve(self):
        self.assertEqual(sorted(sign_totals(self.sarva)), list(range(12)))


class ReductionTest(unittest.TestCase):
    """Part 11: differing traditions are separate profiles, not averaged."""

    @classmethod
    def setUpClass(cls):
        cls.chart = natal()
        cls.bhinna = compute_all_bhinna(reference_signs_from_chart(cls.chart))

    def test_reductions_are_off_by_default(self):
        """An UNVERIFIED transform must not be applied silently."""
        result = compute_ashtakavarga(self.chart)
        self.assertEqual(result.reductions, {})

    def test_reductions_are_available_on_request(self):
        result = compute_ashtakavarga(self.chart, include_reductions=True)
        self.assertEqual(set(result.reductions), set(AV_GRAHAS))

    def test_requesting_reductions_warns_that_they_are_unverified(self):
        result = compute_ashtakavarga(self.chart, include_reductions=True)
        self.assertTrue(any("UNVERIFIED" in w for w in result.warnings))

    def test_reductions_declare_their_status(self):
        result = compute_ashtakavarga(self.chart, include_reductions=True)
        for planet, data in result.reductions.items():
            with self.subTest(planet=planet):
                self.assertEqual(data["validation_status"], "UNVERIFIED")
                self.assertIn("profile", data)

    def test_trikona_never_increases_a_count(self):
        for planet, chart in self.bhinna.items():
            reduced = trikona_sodhana(chart)
            for sign in range(12):
                with self.subTest(planet=planet, sign=sign):
                    self.assertLessEqual(reduced[sign],
                                         chart.bindus_in_sign(sign))

    def test_ekadhipatya_never_increases_a_count(self):
        occupied = {p.rashi_index for n, p in self.chart.planets.items()
                    if n in BINDU_TABLES}
        for planet, chart in self.bhinna.items():
            after = ekadhipatya_sodhana(dict(chart.bindus_by_sign), occupied)
            for sign in range(12):
                with self.subTest(planet=planet, sign=sign):
                    self.assertLessEqual(after[sign],
                                         chart.bindus_in_sign(sign))

    def test_reduction_keeps_the_intermediate_steps(self):
        result = compute_ashtakavarga(self.chart, include_reductions=True)
        for data in result.reductions.values():
            for key in ("original", "after_trikona", "after_ekadhipatya"):
                self.assertIn(key, data)


class IntegrationTest(unittest.TestCase):

    def test_full_set_builds_and_serialises(self):
        import json
        result = compute_ashtakavarga(natal())
        self.assertEqual(len(result.bhinna), 7)
        self.assertIsNotNone(result.sarva)
        json.dumps(result.to_dict())

    def test_set_records_its_provenance(self):
        data = compute_ashtakavarga(natal()).to_dict()
        self.assertEqual(data["validation_status"], "TEXT_LOCATED")
        self.assertIn("BPHS ch.66", data["source"])
        self.assertIn("incomplete", data["verification_note"])

    def test_no_interpretation_anywhere_in_the_output(self):
        """Part 10 forbids attaching predictions to bindu counts."""
        import json
        blob = json.dumps(compute_ashtakavarga(natal()).to_dict()).lower()
        for phrase in ("success", "fortunate", "auspicious result",
                       "guaranteed", "good period", "favourable"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, blob)

    def test_report_states_that_no_claim_is_made(self):
        from engine.ashtakavarga import format_ashtakavarga_report
        report = format_ashtakavarga_report(compute_ashtakavarga(natal()))
        self.assertIn("NO CLAIM", report)

    def test_different_charts_give_different_bindus(self):
        """Guards against a bug that would make every chart identical."""
        other = JyotishChart(jde=jde_from_datetime(
            datetime.datetime(1975, 6, 14, 16, 0)), lat=40.7128, lon=-74.006)
        first = compute_ashtakavarga(natal()).sarva.bindus_by_sign
        second = compute_ashtakavarga(other).sarva.bindus_by_sign
        self.assertNotEqual(first, second)

    def test_totals_hold_across_many_charts(self):
        """The invariant must hold for any chart, not just the fixture."""
        for day in (1, 90, 180, 270):
            moment = datetime.datetime(2000, 1, 1) + datetime.timedelta(days=day)
            chart = JyotishChart(jde=jde_from_datetime(moment),
                                 lat=0.0, lon=0.0)
            result = compute_ashtakavarga(chart)
            with self.subTest(day=day):
                self.assertEqual(result.sarva.total, SARVA_TOTAL)
                for planet, bav in result.bhinna.items():
                    self.assertEqual(bav.total, CLASSICAL_TOTALS[planet])


if __name__ == "__main__":
    unittest.main(verbosity=2)
