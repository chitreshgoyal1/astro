"""
Vimshottari timing engine (V1.2 Parts 4-9)
-------------------------------------------
The properties that matter for a timing engine are structural, and they are
easy to violate silently: a period that starts a few seconds after its
predecessor ends, or children that sum to slightly less than their parent,
will pass any casual eyeballing and then drift by days at the fourth level.

These tests assert the structure exactly rather than approximately. The engine
holds every duration as an exact Fraction and computes every boundary as an
offset from its parent's start, so "exactly" is achievable and is what is
demanded here — gaps and overlaps are checked to the microsecond.
"""

# V1.2.

import datetime
import os
import sys
import unittest
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.timing import (
    DASHA_LEVELS, DASHA_SEQUENCE, JULIAN_YEAR, NAKSHATRA_DASHA_LORD,
    SAVANA_YEAR, TOTAL_YEARS, VIMSHOTTARI_YEARS, VimshottariDasha,
    YEAR_LENGTHS, birth_dasha_lord, compute_vimshottari, elapsed_fraction,
    nakshatra_index, next_level, subdivide, year_length,
)
from engine.timing.models import NAKSHATRA_SPAN

BIRTH = datetime.datetime(1988, 8, 30, 20, 18)
MOON = 358.1197          # Jaipur 1988: Revati, pada 4


def build(moon=MOON, birth=BIRTH, depth=3, **kwargs) -> VimshottariDasha:
    return compute_vimshottari(moon, birth, depth=depth, **kwargs)


# ── Part 4: canonical constants ──────────────────────────────────────────────

class CanonicalConstantsTest(unittest.TestCase):
    """One source for the cycle; no second copy to drift out of step."""

    def test_sequence_and_years_match_the_classical_cycle(self):
        expected = {
            "Ketu": 7, "Shukra": 20, "Surya": 6, "Chandra": 10, "Mangal": 7,
            "Rahu": 18, "Guru": 16, "Shani": 19, "Budha": 17,
        }
        self.assertEqual(VIMSHOTTARI_YEARS, expected)
        self.assertEqual(
            DASHA_SEQUENCE,
            ("Ketu", "Shukra", "Surya", "Chandra", "Mangal",
             "Rahu", "Guru", "Shani", "Budha"))

    def test_cycle_totals_120_years(self):
        self.assertEqual(TOTAL_YEARS, 120)
        self.assertEqual(sum(VIMSHOTTARI_YEARS.values()), 120)

    def test_nakshatra_lords_are_derived_from_the_sequence(self):
        """27 nakshatras, nine lords, repeating three times."""
        self.assertEqual(len(NAKSHATRA_DASHA_LORD), 27)
        for index in range(27):
            self.assertEqual(NAKSHATRA_DASHA_LORD[index],
                             DASHA_SEQUENCE[index % 9])

    def test_no_duplicate_definition_of_the_cycle_elsewhere(self):
        """
        engine/fal.py holds the V1 copy. It is legacy and must agree with the
        canonical one; a divergence would mean two answers in one codebase.
        """
        from engine.fal import DASHA_ORDER, DASHA_YEARS
        self.assertEqual(tuple(DASHA_ORDER), DASHA_SEQUENCE)
        self.assertEqual(DASHA_YEARS, VIMSHOTTARI_YEARS)


class YearLengthTest(unittest.TestCase):
    """The convention is explicit, named and recorded — never assumed."""

    def test_default_is_the_julian_year(self):
        self.assertEqual(JULIAN_YEAR.days, Fraction(36525, 100))
        self.assertAlmostEqual(JULIAN_YEAR.days_float, 365.25)

    def test_120_julian_years_is_a_whole_number_of_days(self):
        self.assertEqual(JULIAN_YEAR.days * 120, Fraction(43830))

    def test_every_convention_is_documented(self):
        for name, convention in YEAR_LENGTHS.items():
            with self.subTest(convention=name):
                self.assertTrue(convention.description)
                self.assertGreater(convention.days, 300)

    def test_unknown_convention_is_rejected(self):
        with self.assertRaises(ValueError):
            year_length("babylonian")

    def test_convention_changes_the_dates(self):
        """A different year length must actually move the boundaries."""
        julian = build()
        savana = build(years=None) if False else compute_vimshottari(
            MOON, BIRTH, depth=1, year_length_name="savana")
        self.assertNotEqual(julian.mahadashas[-1].end,
                            savana.mahadashas[-1].end)
        # 120 savana years is 43,200 days against the Julian 43,830.
        self.assertEqual(SAVANA_YEAR.days * 120, Fraction(43200))

    def test_convention_is_recorded_in_the_output(self):
        data = build().to_dict()
        self.assertEqual(data["convention"]["year_length"], "julian")
        self.assertEqual(data["convention"]["year_length_days"], 365.25)
        self.assertIn("year_length_note", data["convention"])


# ── Part 5: mahadasha with calendar dates ────────────────────────────────────

class BirthBalanceTest(unittest.TestCase):
    """The birth mahadasha begins BEFORE birth, by the elapsed portion."""

    def setUp(self):
        self.dasha = build()

    def test_birth_lord_comes_from_the_moons_nakshatra(self):
        self.assertEqual(nakshatra_index(MOON), 26)          # Revati
        self.assertEqual(birth_dasha_lord(MOON), "Budha")
        self.assertEqual(self.dasha.birth_lord, "Budha")

    def test_first_mahadasha_starts_before_birth(self):
        first = self.dasha.mahadashas[0]
        self.assertLess(first.start, BIRTH)
        self.assertGreater(first.end, BIRTH)
        self.assertTrue(first.contains(BIRTH))

    def test_elapsed_plus_balance_equals_the_full_period(self):
        balance = self.dasha.balance_summary()
        total = VIMSHOTTARI_YEARS["Budha"] * 365.25
        self.assertAlmostEqual(
            balance["elapsed_days"] + balance["balance_days"], total, places=6)
        self.assertAlmostEqual(balance["full_period_days"], total, places=6)

    def test_elapsed_fraction_matches_the_moons_place_in_the_nakshatra(self):
        within = MOON % float(NAKSHATRA_SPAN)
        self.assertAlmostEqual(float(elapsed_fraction(MOON)),
                               within / float(NAKSHATRA_SPAN), places=10)

    def test_balance_is_the_classical_figure(self):
        """Revati at 28°07' gives roughly 2.4 years of Budha left."""
        balance = self.dasha.balance_summary()
        self.assertAlmostEqual(balance["balance_years"], 2.397, places=2)

    def test_moon_at_nakshatra_start_gives_a_full_balance(self):
        dasha = build(moon=0.0)
        balance = dasha.balance_summary()
        self.assertAlmostEqual(balance["elapsed_fraction"], 0.0, places=12)
        self.assertAlmostEqual(balance["balance_years"],
                               VIMSHOTTARI_YEARS[dasha.birth_lord], places=9)
        self.assertEqual(dasha.mahadashas[0].start, BIRTH)

    def test_moon_at_nakshatra_end_gives_almost_no_balance(self):
        dasha = build(moon=float(NAKSHATRA_SPAN) - 1e-9)
        self.assertLess(dasha.balance_summary()["balance_days"], 0.001)

    def test_period_fields_are_populated(self):
        """Part 5 names the fields the model must expose."""
        period = self.dasha.mahadashas[0]
        for attribute in ("level", "lord", "parent_lord", "start", "end",
                          "duration_days", "sequence_index"):
            with self.subTest(field=attribute):
                self.assertTrue(hasattr(period, attribute))
        self.assertEqual(period.level, "mahadasha")
        self.assertIsNone(period.parent_lord)
        self.assertEqual(period.sequence_index, 0)


class MahadashaSequenceTest(unittest.TestCase):

    def setUp(self):
        self.dasha = build(depth=1)

    def test_nine_mahadashas_in_the_canonical_order(self):
        lords = [p.lord for p in self.dasha.mahadashas]
        self.assertEqual(len(lords), 9)
        start = DASHA_SEQUENCE.index("Budha")
        self.assertEqual(
            lords, [DASHA_SEQUENCE[(start + i) % 9] for i in range(9)])

    def test_durations_match_the_cycle(self):
        for period in self.dasha.mahadashas:
            with self.subTest(lord=period.lord):
                self.assertAlmostEqual(
                    period.duration_days,
                    VIMSHOTTARI_YEARS[period.lord] * 365.25, places=6)

    def test_periods_are_contiguous_with_no_gap_or_overlap(self):
        periods = self.dasha.mahadashas
        for earlier, later in zip(periods, periods[1:]):
            with self.subTest(lord=earlier.lord):
                self.assertEqual(earlier.end, later.start)

    def test_total_span_is_120_julian_years(self):
        span = self.dasha.end - self.dasha.start
        self.assertAlmostEqual(span.total_seconds() / 86400.0, 43830.0,
                               places=3)


# ── Part 6: antardasha ───────────────────────────────────────────────────────

class AntardashaTest(unittest.TestCase):

    def setUp(self):
        self.dasha = build(depth=2)

    def test_every_mahadasha_has_nine_antardashas(self):
        self.assertEqual(len(self.dasha.mahadashas), 9)
        for maha in self.dasha.mahadashas:
            with self.subTest(maha=maha.lord):
                self.assertEqual(len(maha.children), 9)
        self.assertEqual(len(self.dasha.antardashas), 81)

    def test_all_81_combinations_are_present_and_unique(self):
        """Part 6: all 9 mahadashas x 9 antardashas."""
        pairs = {(a.mahadasha, a.lord) for a in self.dasha.antardashas}
        self.assertEqual(len(pairs), 81)
        for maha in DASHA_SEQUENCE:
            for antar in DASHA_SEQUENCE:
                with self.subTest(maha=maha, antar=antar):
                    self.assertIn((maha, antar), pairs)

    def test_ordering_starts_with_the_mahadasha_lord(self):
        for maha in self.dasha.mahadashas:
            with self.subTest(maha=maha.lord):
                self.assertEqual(maha.children[0].lord, maha.lord)

    def test_ordering_continues_cyclically(self):
        for maha in self.dasha.mahadashas:
            lords = [c.lord for c in maha.children]
            start = DASHA_SEQUENCE.index(maha.lord)
            with self.subTest(maha=maha.lord):
                self.assertEqual(
                    lords, [DASHA_SEQUENCE[(start + i) % 9] for i in range(9)])

    def test_duration_is_derived_from_the_proportions(self):
        """
        Duration must come from the cycle arithmetic, not a table of dates:
            antar_days = maha_days * antar_years / 120
        """
        for maha in self.dasha.mahadashas:
            for antar in maha.children:
                expected = (maha.duration_days
                            * VIMSHOTTARI_YEARS[antar.lord] / TOTAL_YEARS)
                with self.subTest(maha=maha.lord, antar=antar.lord):
                    self.assertAlmostEqual(antar.duration_days, expected,
                                           places=9)

    def test_first_antardasha_starts_exactly_at_the_mahadasha_start(self):
        for maha in self.dasha.mahadashas:
            with self.subTest(maha=maha.lord):
                self.assertEqual(maha.children[0].start, maha.start)

    def test_last_antardasha_ends_exactly_at_the_mahadasha_end(self):
        for maha in self.dasha.mahadashas:
            with self.subTest(maha=maha.lord):
                self.assertEqual(maha.children[-1].end, maha.end)

    def test_no_gaps_or_overlaps_within_a_mahadasha(self):
        for maha in self.dasha.mahadashas:
            for earlier, later in zip(maha.children, maha.children[1:]):
                with self.subTest(maha=maha.lord, antar=earlier.lord):
                    self.assertEqual(earlier.end, later.start)

    def test_children_sum_exactly_to_the_parent(self):
        """Exact Fraction arithmetic makes this an equality, not an estimate."""
        for maha in self.dasha.mahadashas:
            total = sum((c.duration_days_exact for c in maha.children),
                        Fraction(0))
            with self.subTest(maha=maha.lord):
                self.assertEqual(total, maha.duration_days_exact)

    def test_parent_references(self):
        for antar in self.dasha.antardashas:
            with self.subTest(antar=antar.label()):
                self.assertEqual(antar.level, "antardasha")
                self.assertEqual(antar.parent_lord, antar.mahadasha)
                self.assertEqual(len(antar.ancestors), 1)


# ── Part 7: pratyantardasha and generic subdivision ──────────────────────────

class PratyantardashaTest(unittest.TestCase):

    def setUp(self):
        self.dasha = build(depth=3)

    def test_counts(self):
        self.assertEqual(len(self.dasha.pratyantardashas), 729)

    def test_proportions_and_containment(self):
        for antar in self.dasha.antardashas:
            self.assertEqual(len(antar.children), 9)
            self.assertEqual(antar.children[0].start, antar.start)
            self.assertEqual(antar.children[-1].end, antar.end)
            total = sum((c.duration_days_exact for c in antar.children),
                        Fraction(0))
            with self.subTest(antar=antar.label()):
                self.assertEqual(total, antar.duration_days_exact)

    def test_parent_references_name_the_whole_chain(self):
        praty = self.dasha.pratyantardashas[0]
        self.assertEqual(praty.level, "pratyantardasha")
        self.assertEqual(len(praty.ancestors), 2)
        self.assertIsNotNone(praty.mahadasha)
        self.assertIsNotNone(praty.antardasha)
        data = praty.to_dict()
        for key in ("level", "lord", "mahadasha", "antardasha", "start", "end"):
            with self.subTest(key=key):
                self.assertIn(key, data)

    def test_subdivision_is_generic_not_special_cased(self):
        """
        Part 7: the same routine must produce any level. Subdividing a
        pratyantardasha yields sukshma with no new code.
        """
        praty = self.dasha.pratyantardashas[0]
        sukshma = subdivide(praty)
        self.assertEqual(len(sukshma), 9)
        self.assertEqual(sukshma[0].level, "sukshma")
        self.assertEqual(sukshma[0].start, praty.start)
        self.assertEqual(sukshma[-1].end, praty.end)
        self.assertEqual(
            sum((s.duration_days_exact for s in sukshma), Fraction(0)),
            praty.duration_days_exact)

    def test_deeper_levels_build_through_the_same_path(self):
        deep = build(depth=4)
        sukshma = deep.periods_at_level("sukshma")
        self.assertEqual(len(sukshma), 9 ** 4)

    def test_level_hierarchy_is_declared_in_order(self):
        self.assertEqual(DASHA_LEVELS[:3],
                         ("mahadasha", "antardasha", "pratyantardasha"))
        self.assertEqual(next_level("mahadasha"), "antardasha")
        self.assertEqual(next_level("antardasha"), "pratyantardasha")
        self.assertIsNone(next_level(DASHA_LEVELS[-1]))


# ── Part 8: query API ────────────────────────────────────────────────────────

class QueryApiTest(unittest.TestCase):

    def setUp(self):
        self.dasha = build(depth=3)

    def test_get_mahadasha_at(self):
        maha = self.dasha.mahadashas[3]
        middle = maha.start + (maha.end - maha.start) / 2
        self.assertIs(self.dasha.get_mahadasha_at(middle), maha)

    def test_get_antardasha_at(self):
        antar = self.dasha.antardashas[20]
        middle = antar.start + (antar.end - antar.start) / 2
        self.assertIs(self.dasha.get_antardasha_at(middle), antar)

    def test_get_pratyantardasha_at(self):
        praty = self.dasha.pratyantardashas[100]
        middle = praty.start + (praty.end - praty.start) / 2
        self.assertIs(self.dasha.get_pratyantardasha_at(middle), praty)

    def test_get_dasha_stack_at_returns_the_specified_shape(self):
        stack = self.dasha.get_dasha_stack_at(datetime.datetime(2030, 6, 10))
        for key in ("date", "mahadasha", "antardasha", "pratyantardasha"):
            with self.subTest(key=key):
                self.assertIn(key, stack)
        self.assertTrue(stack["in_range"])
        self.assertIn(stack["mahadasha"], DASHA_SEQUENCE)
        self.assertIn(stack["antardasha"], DASHA_SEQUENCE)
        self.assertIn(stack["pratyantardasha"], DASHA_SEQUENCE)

    def test_stack_levels_agree_with_the_individual_queries(self):
        for moment in (datetime.datetime(1990, 1, 1),
                       datetime.datetime(2005, 7, 4),
                       datetime.datetime(2030, 6, 10),
                       datetime.datetime(2077, 12, 31)):
            stack = self.dasha.get_dasha_stack_at(moment)
            with self.subTest(moment=moment):
                self.assertEqual(stack["mahadasha"],
                                 self.dasha.get_mahadasha_at(moment).lord)
                self.assertEqual(stack["antardasha"],
                                 self.dasha.get_antardasha_at(moment).lord)
                self.assertEqual(stack["pratyantardasha"],
                                 self.dasha.get_pratyantardasha_at(moment).lord)

    def test_queries_outside_the_span_return_none(self):
        before = self.dasha.start - datetime.timedelta(days=1)
        after = self.dasha.end + datetime.timedelta(days=1)
        for moment in (before, after):
            with self.subTest(moment=moment):
                self.assertIsNone(self.dasha.get_mahadasha_at(moment))
                self.assertIsNone(self.dasha.get_antardasha_at(moment))
                self.assertFalse(
                    self.dasha.get_dasha_stack_at(moment)["in_range"])

    def test_get_periods_between(self):
        start = datetime.datetime(2000, 1, 1)
        end = datetime.datetime(2010, 1, 1)
        found = self.dasha.get_periods_between(start, end)
        self.assertTrue(found)
        for period in found:
            with self.subTest(lord=period.lord):
                self.assertTrue(period.overlaps(start, end))
        # Every mahadasha overlapping the window is included, none missed.
        expected = [p for p in self.dasha.mahadashas if p.overlaps(start, end)]
        self.assertEqual(found, expected)

    def test_get_periods_between_at_deeper_levels(self):
        start = datetime.datetime(2030, 1, 1)
        end = datetime.datetime(2030, 12, 31)
        for level in ("mahadasha", "antardasha", "pratyantardasha"):
            with self.subTest(level=level):
                found = self.dasha.get_periods_between(start, end, level=level)
                self.assertTrue(found)
                self.assertTrue(all(p.level == level for p in found))

    def test_reversed_window_is_rejected(self):
        with self.assertRaises(ValueError):
            self.dasha.get_periods_between(datetime.datetime(2010, 1, 1),
                                           datetime.datetime(2000, 1, 1))

    def test_get_period_at_any_level(self):
        moment = datetime.datetime(2030, 6, 10)
        for level in ("mahadasha", "antardasha", "pratyantardasha"):
            with self.subTest(level=level):
                period = self.dasha.get_period_at(moment, level)
                self.assertIsNotNone(period)
                self.assertEqual(period.level, level)
                self.assertTrue(period.contains(moment))


# ── Part 9: boundary behaviour ───────────────────────────────────────────────

class BoundaryTest(unittest.TestCase):
    """
    Timing boundaries are where an off-by-one lives. Intervals are half-open:
    the instant a period ends belongs to the next period, never to both and
    never to neither.
    """

    def setUp(self):
        self.dasha = build(depth=3)
        self.second = datetime.timedelta(seconds=1)

    def test_exact_start_belongs_to_the_period(self):
        for maha in self.dasha.mahadashas:
            with self.subTest(lord=maha.lord):
                self.assertTrue(maha.contains(maha.start))
                self.assertIs(self.dasha.get_mahadasha_at(maha.start), maha)

    def test_exact_end_belongs_to_the_next_period(self):
        for earlier, later in zip(self.dasha.mahadashas,
                                  self.dasha.mahadashas[1:]):
            with self.subTest(lord=earlier.lord):
                self.assertFalse(earlier.contains(earlier.end))
                self.assertTrue(later.contains(earlier.end))
                self.assertIs(self.dasha.get_mahadasha_at(earlier.end), later)

    def test_one_second_before_and_after_a_boundary(self):
        for earlier, later in zip(self.dasha.mahadashas,
                                  self.dasha.mahadashas[1:]):
            boundary = earlier.end
            with self.subTest(lord=earlier.lord):
                self.assertIs(
                    self.dasha.get_mahadasha_at(boundary - self.second), earlier)
                self.assertIs(
                    self.dasha.get_mahadasha_at(boundary + self.second), later)

    def test_no_moment_falls_between_two_periods(self):
        """Sweep every antardasha boundary: something always answers."""
        for antar in self.dasha.antardashas:
            for offset in (-self.second, datetime.timedelta(0), self.second):
                moment = antar.start + offset
                if not (self.dasha.start <= moment < self.dasha.end):
                    continue
                with self.subTest(antar=antar.label(), offset=offset):
                    self.assertIsNotNone(self.dasha.get_mahadasha_at(moment))
                    self.assertIsNotNone(self.dasha.get_antardasha_at(moment))

    def test_birth_exactly_on_a_nakshatra_boundary(self):
        """Zero elapsed: the mahadasha starts exactly at birth."""
        for index in range(27):
            longitude = index * float(NAKSHATRA_SPAN)
            dasha = build(moon=longitude, depth=1)
            with self.subTest(nakshatra=index):
                self.assertEqual(dasha.mahadashas[0].start, BIRTH)
                self.assertEqual(dasha.birth_lord, NAKSHATRA_DASHA_LORD[index])

    def test_moon_just_before_a_nakshatra_boundary(self):
        """The lord must be the earlier nakshatra's, with almost no balance."""
        for index in range(1, 27):
            longitude = index * float(NAKSHATRA_SPAN) - 1e-9
            dasha = build(moon=longitude, depth=1)
            with self.subTest(nakshatra=index):
                self.assertEqual(dasha.birth_lord,
                                 NAKSHATRA_DASHA_LORD[index - 1])
                self.assertLess(dasha.balance_summary()["balance_days"], 0.01)

    def test_moon_just_after_a_nakshatra_boundary(self):
        for index in range(27):
            longitude = index * float(NAKSHATRA_SPAN) + 1e-9
            dasha = build(moon=longitude, depth=1)
            with self.subTest(nakshatra=index):
                self.assertEqual(dasha.birth_lord, NAKSHATRA_DASHA_LORD[index])
                balance = dasha.balance_summary()
                self.assertAlmostEqual(
                    balance["balance_years"],
                    VIMSHOTTARI_YEARS[dasha.birth_lord], places=6)

    def test_leap_year_birth(self):
        birth = datetime.datetime(2000, 2, 29, 12, 0)
        dasha = compute_vimshottari(MOON, birth, depth=2)
        self.assertTrue(dasha.mahadashas[0].contains(birth))
        for earlier, later in zip(dasha.mahadashas, dasha.mahadashas[1:]):
            self.assertEqual(earlier.end, later.start)

    def test_leap_day_queries_resolve(self):
        dasha = build(depth=3)
        for year in (1992, 1996, 2000, 2004, 2020, 2024):
            moment = datetime.datetime(year, 2, 29, 6, 0)
            if not (dasha.start <= moment < dasha.end):
                continue
            with self.subTest(year=year):
                self.assertIsNotNone(dasha.get_pratyantardasha_at(moment))

    def test_span_crossing_centuries(self):
        """
        A 19th-century birth runs past 1900 without losing contiguity. The
        span starts before birth (by the elapsed portion of the first
        mahadasha) and runs 120 years from there, so this one covers
        1875 to 1995.
        """
        dasha = compute_vimshottari(
            MOON, datetime.datetime(1890, 3, 15, 4, 30), depth=2)
        self.assertLess(dasha.start.year, 1900)
        self.assertGreater(dasha.end.year, 1900)
        self.assertLess(dasha.start.year, dasha.end.year - 100)
        for earlier, later in zip(dasha.mahadashas, dasha.mahadashas[1:]):
            with self.subTest(lord=earlier.lord):
                self.assertEqual(earlier.end, later.start)
        for antar in dasha.antardashas:
            self.assertTrue(dasha.start <= antar.start < dasha.end)

    def test_no_drift_accumulates_across_the_whole_tree(self):
        """
        The end of the last pratyantardasha must equal the end of the whole
        span exactly. Repeated rounded arithmetic would miss by hours here.
        """
        dasha = build(depth=3)
        self.assertEqual(dasha.pratyantardashas[-1].end, dasha.end)
        self.assertEqual(dasha.pratyantardashas[0].start, dasha.start)

    def test_dates_are_not_derived_from_age_strings(self):
        """
        Part 9: calendar timestamps must come from the timing calculation.
        Reconstructing a period start by adding its age in years to the birth
        date must agree with the computed start to the second.
        """
        dasha = build(depth=1)
        for period in dasha.mahadashas:
            offset_days = float(period.start_offset_days)
            reconstructed = dasha.cycle_start + datetime.timedelta(
                days=offset_days)
            with self.subTest(lord=period.lord):
                self.assertLess(abs((reconstructed - period.start)
                                    .total_seconds()), 1e-3)


# ── serialisation ────────────────────────────────────────────────────────────

class SerialisationTest(unittest.TestCase):

    def test_to_dict_is_json_native(self):
        import json
        data = build(depth=2).to_dict()
        json.dumps(data)                      # must not raise

    def test_period_dict_has_the_specified_fields(self):
        period = build(depth=2).antardashas[0]
        data = period.to_dict()
        for key in ("level", "lord", "parent_lord", "start", "end",
                    "duration_days", "sequence_index"):
            with self.subTest(key=key):
                self.assertIn(key, data)

    def test_depth_limits_serialisation(self):
        dasha = build(depth=3)
        shallow = dasha.to_dict(depth=1)
        self.assertNotIn("children", shallow["mahadashas"][0])
        deep = dasha.to_dict(depth=2)
        self.assertIn("children", deep["mahadashas"][0])


class ChartIntegrationTest(unittest.TestCase):

    def test_from_chart(self):
        from engine.planets import JyotishChart, jde_from_datetime
        from engine.timing import from_chart
        chart = JyotishChart(
            jde=jde_from_datetime(datetime.datetime(1988, 8, 30, 14, 48)),
            lat=26.9124, lon=75.7873)
        dasha = from_chart(chart, BIRTH, depth=2)
        self.assertIsNotNone(dasha)
        self.assertEqual(dasha.birth_lord, "Budha")

    def test_from_chart_without_a_moon_returns_none(self):
        from engine.planets import JyotishChart
        from engine.timing import from_chart
        chart = JyotishChart.from_sidereal_longitudes(
            lagna_lon=0.0, planet_lons={"Surya": 100.0})
        self.assertIsNone(from_chart(chart, BIRTH))

    def test_timing_package_does_not_import_interpretation_layers(self):
        """Part 4: timing must stay independent of rules and features."""
        import os
        folder = os.path.join(ROOT, "engine", "timing")
        for name in os.listdir(folder):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                body = handle.read()
            with self.subTest(module=name):
                self.assertNotIn("from ..rules", body)
                self.assertNotIn("from ..features", body)
                self.assertNotIn("from ..fal", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
