"""
Astrology feature engine (Parts 3-9, 12)
----------------------------------------
Tests the calculated feature layer. Wherever a feature has a closed-form
classical answer, the expected value is written out longhand from the rule
rather than taken from the engine, so these are checks and not echoes.

Synthetic charts are used throughout: placing grahas at chosen degrees is the
only way to exercise a specific configuration (an exchange, a debilitation, a
war) deliberately rather than waiting for one to occur.
"""

# Phase 2 (V1.1).

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.planets import (
    CLASSICAL_COMBUSTION, CombustionProfile, JyotishChart, PLANET_NAMES,
    RASHI_LORDS, RASHI_NAMES,
)
from engine.vargas import VARGA_ORDER, VargaConfig
from engine.features import (
    DEFAULT_ORB_DEG, KENDRA_HOUSES, NODE_ASPECT_CONVENTIONS, TRIKONA_HOUSES,
    build_chart_features, compute_aspects, compute_conjunctions,
    compute_graha_yuddha, dispositor_chain, final_dispositors,
    find_parivartanas, functional_roles, house_lords, house_lords_as_strings,
    houses_owned, lord_of_sign, natural_relationship, parashari_profile,
    relationship_table, sign_relationship, temporary_relationship, yogakarakas,
)

MESHA, VRISHABHA, MITHUNA, KARKA = 0, 1, 2, 3
SIMHA, KANYA, TULA, VRISHCHIKA = 4, 5, 6, 7
DHANU, MAKARA, KUMBHA, MEENA = 8, 9, 10, 11


def synthetic_chart(lagna_sign: int, placements: dict,
                    retrograde=None, speeds=None) -> JyotishChart:
    """
    A chart built from chosen sidereal degrees.

    `placements` maps a graha to either a sign index (placed at 15° of it) or
    an absolute longitude, so a test can be as coarse or as exact as it needs.
    """
    longitudes = {}
    for planet, value in placements.items():
        longitudes[planet] = (value * 30.0 + 15.0
                              if isinstance(value, int) and 0 <= value <= 11
                              else float(value))
    return JyotishChart.from_sidereal_longitudes(
        lagna_lon=lagna_sign * 30.0 + 15.0,
        planet_lons=longitudes,
        retrograde=retrograde or set(),
        speeds=speeds,
    )


# ── Part 4: lordships ────────────────────────────────────────────────────────

class LordshipTest(unittest.TestCase):

    def test_house_lords_for_mesha_lagna(self):
        """Written out longhand from the rashi lords, for a Mesha Lagna."""
        expected = {
            1: "Mangal",    # Mesha
            2: "Shukra",    # Vrishabha
            3: "Budha",     # Mithuna
            4: "Chandra",   # Karka
            5: "Surya",     # Simha
            6: "Budha",     # Kanya
            7: "Shukra",    # Tula
            8: "Mangal",    # Vrishchika
            9: "Guru",      # Dhanu
            10: "Shani",    # Makara
            11: "Shani",    # Kumbha
            12: "Guru",     # Meena
        }
        self.assertEqual(house_lords(MESHA), expected)

    def test_house_lords_for_meena_lagna(self):
        """The regression chart's Lagna."""
        expected = {
            1: "Guru", 2: "Mangal", 3: "Shukra", 4: "Budha", 5: "Chandra",
            6: "Surya", 7: "Budha", 8: "Shukra", 9: "Mangal", 10: "Guru",
            11: "Shani", 12: "Shani",
        }
        self.assertEqual(house_lords(MEENA), expected)

    def test_house_lords_consistent_for_every_lagna(self):
        for lagna in range(12):
            lords = house_lords(lagna)
            with self.subTest(lagna=RASHI_NAMES[lagna]):
                self.assertEqual(len(lords), 12)
                for house in range(1, 13):
                    sign = (lagna + house - 1) % 12
                    self.assertEqual(lords[house], RASHI_LORDS[RASHI_NAMES[sign]])

    def test_string_keyed_form_matches_the_specified_shape(self):
        lords = house_lords_as_strings(MEENA)
        self.assertEqual(lords["1"], "Guru")
        self.assertEqual(lords["2"], "Mangal")
        self.assertTrue(all(isinstance(key, str) for key in lords))

    def test_houses_owned_is_the_inverse_of_house_lords(self):
        for lagna in range(12):
            lords = house_lords(lagna)
            owned = houses_owned(lagna)
            with self.subTest(lagna=lagna):
                for house, lord in lords.items():
                    self.assertIn(house, owned[lord])
                for planet, houses in owned.items():
                    for house in houses:
                        self.assertEqual(lords[house], planet)

    def test_luminaries_own_one_house_and_others_two(self):
        for lagna in range(12):
            owned = houses_owned(lagna)
            with self.subTest(lagna=lagna):
                self.assertEqual(len(owned["Surya"]), 1)
                self.assertEqual(len(owned["Chandra"]), 1)
                for planet in ("Mangal", "Budha", "Guru", "Shukra", "Shani"):
                    self.assertEqual(len(owned[planet]), 2)

    def test_nodes_own_nothing_but_are_still_reported(self):
        for lagna in range(12):
            owned = houses_owned(lagna)
            with self.subTest(lagna=lagna):
                self.assertEqual(owned["Rahu"], [])
                self.assertEqual(owned["Ketu"], [])


# ── Part 5: aspects ──────────────────────────────────────────────────────────

class AspectTest(unittest.TestCase):

    def houses_aspected(self, planet: str, house: int,
                        node_convention: str = "none") -> set:
        aspects = compute_aspects({planet: house}, {planet: 0}, 0,
                                  parashari_profile(node_convention))
        return {a.to_house for a in aspects}

    def test_every_graha_aspects_the_seventh(self):
        for planet in ("Surya", "Chandra", "Budha", "Shukra", "Mangal",
                       "Guru", "Shani"):
            with self.subTest(planet=planet):
                self.assertIn(7, self.houses_aspected(planet, 1))

    def test_benefics_and_luminaries_aspect_only_the_seventh(self):
        for planet in ("Surya", "Chandra", "Budha", "Shukra"):
            with self.subTest(planet=planet):
                self.assertEqual(self.houses_aspected(planet, 1), {7})

    def test_mangal_aspects_fourth_seventh_eighth(self):
        self.assertEqual(self.houses_aspected("Mangal", 1), {4, 7, 8})

    def test_guru_aspects_fifth_seventh_ninth(self):
        self.assertEqual(self.houses_aspected("Guru", 1), {5, 7, 9})

    def test_shani_aspects_third_seventh_tenth(self):
        self.assertEqual(self.houses_aspected("Shani", 1), {3, 7, 10})

    def test_special_aspects_wrap_correctly_from_every_house(self):
        """Shani in the 11th aspects the 1st, 5th and 8th."""
        self.assertEqual(self.houses_aspected("Shani", 11), {1, 5, 8})
        self.assertEqual(self.houses_aspected("Guru", 10), {2, 4, 6})
        self.assertEqual(self.houses_aspected("Mangal", 12), {3, 6, 7})

    def test_nodes_have_no_aspect_by_default(self):
        """The default asserts nothing about node drishti."""
        for planet in ("Rahu", "Ketu"):
            with self.subTest(planet=planet):
                self.assertEqual(self.houses_aspected(planet, 1), set())

    def test_node_aspect_conventions_are_selectable(self):
        self.assertEqual(
            self.houses_aspected("Rahu", 1, "parashari_like"), {5, 7, 9})
        self.assertEqual(
            self.houses_aspected("Rahu", 1, "kendra"), {4, 7, 10})

    def test_unknown_node_convention_is_rejected(self):
        with self.assertRaises(ValueError):
            parashari_profile("whatever_school")

    def test_profile_names_record_the_node_choice(self):
        for name in NODE_ASPECT_CONVENTIONS:
            with self.subTest(convention=name):
                self.assertIn(name, parashari_profile(name).name)

    def test_planet_to_planet_aspects_come_from_occupancy(self):
        """A graha aspecting a house aspects whatever stands in it."""
        aspects = compute_aspects(
            {"Shani": 1, "Chandra": 7, "Guru": 10},
            {"Shani": 0, "Chandra": 6, "Guru": 9}, 0)
        shani_to_seventh = [a for a in aspects
                            if a.source == "Shani" and a.to_house == 7]
        self.assertEqual(len(shani_to_seventh), 1)
        self.assertIn("Chandra", shani_to_seventh[0].targets)
        self.assertIn("Shani", [a.source for a in aspects if a.to_house == 10])

    def test_a_graha_does_not_aspect_itself(self):
        aspects = compute_aspects({"Mangal": 1}, {"Mangal": 0}, 0)
        for aspect in aspects:
            self.assertNotIn("Mangal", aspect.targets)


# ── Part 6: conjunctions ─────────────────────────────────────────────────────

class ConjunctionTest(unittest.TestCase):

    def test_same_sign_is_independent_of_orb(self):
        """
        The case that matters: two grahas at opposite ends of one rashi are
        conjunct by the classical rule and far apart by orb.
        """
        conjunctions = compute_conjunctions(
            {"Surya": 0.1, "Budha": 29.9},
            {"Surya": MESHA, "Budha": MESHA},
            {"Surya": 1, "Budha": 1})
        self.assertEqual(len(conjunctions), 1)
        conjunction = conjunctions[0]
        self.assertTrue(conjunction.same_sign)
        self.assertFalse(conjunction.within_orb)
        self.assertAlmostEqual(conjunction.angular_separation, 29.8, places=4)

    def test_close_across_a_sign_boundary_is_not_same_sign(self):
        """The mirror case: within orb, but in different rashis."""
        conjunctions = compute_conjunctions(
            {"Surya": 29.9, "Budha": 30.1},
            {"Surya": MESHA, "Budha": VRISHABHA},
            {"Surya": 1, "Budha": 2})
        self.assertEqual(len(conjunctions), 1)
        conjunction = conjunctions[0]
        self.assertFalse(conjunction.same_sign)
        self.assertTrue(conjunction.within_orb)
        self.assertAlmostEqual(conjunction.angular_separation, 0.2, places=4)

    def test_distant_pairs_are_not_reported(self):
        self.assertEqual(
            compute_conjunctions({"Surya": 0.0, "Shani": 180.0},
                                 {"Surya": MESHA, "Shani": TULA},
                                 {"Surya": 1, "Shani": 7}), [])

    def test_separation_takes_the_short_way_round(self):
        conjunctions = compute_conjunctions(
            {"Surya": 359.0, "Budha": 1.0},
            {"Surya": MEENA, "Budha": MESHA},
            {"Surya": 12, "Budha": 1})
        self.assertAlmostEqual(conjunctions[0].angular_separation, 2.0, places=6)

    def test_orb_is_reported_with_every_conjunction(self):
        conjunctions = compute_conjunctions(
            {"Surya": 10.0, "Budha": 12.0},
            {"Surya": MESHA, "Budha": MESHA},
            {"Surya": 1, "Budha": 1}, orb_deg=5.0)
        self.assertEqual(conjunctions[0].orb_used, 5.0)

    def test_graha_yuddha_excludes_luminaries_and_nodes(self):
        wars = compute_graha_yuddha(
            {"Surya": 10.0, "Chandra": 10.2, "Rahu": 10.1, "Ketu": 10.3},
            {"Surya": 0.0, "Chandra": 0.0, "Rahu": 0.0, "Ketu": 0.0})
        self.assertEqual(wars, [])

    def test_graha_yuddha_between_tara_grahas(self):
        wars = compute_graha_yuddha({"Mangal": 10.0, "Shani": 10.4},
                                    {"Mangal": 1.5, "Shani": -0.5})
        self.assertEqual(len(wars), 1)
        self.assertEqual(wars[0].winner, "Mangal")

    def test_graha_yuddha_declines_to_call_a_tie(self):
        wars = compute_graha_yuddha({"Mangal": 10.0, "Shani": 10.4},
                                    {"Mangal": 1.0, "Shani": 1.0})
        self.assertIsNone(wars[0].winner)


# ── Part 7: dispositors ──────────────────────────────────────────────────────

class DispositorTest(unittest.TestCase):

    def test_chain_terminates_at_a_self_dispositing_graha(self):
        # Mangal in Meena (Guru's), Guru in Vrishabha (Shukra's),
        # Shukra in Mithuna (Budha's), Budha in Kanya (its own).
        signs = {"Mangal": MEENA, "Guru": VRISHABHA, "Shukra": MITHUNA,
                 "Budha": KANYA}
        chain = dispositor_chain("Mangal", signs)
        self.assertEqual(chain.chain, ["Guru", "Shukra", "Budha"])
        self.assertEqual(chain.final, "Budha")
        self.assertEqual(chain.terminated_by, "self_dispositor")
        self.assertFalse(chain.in_cycle)

    def test_self_dispositing_graha_has_an_empty_chain(self):
        chain = dispositor_chain("Budha", {"Budha": KANYA})
        self.assertEqual(chain.chain, [])
        self.assertEqual(chain.final, "Budha")

    def test_two_graha_cycle_is_detected_and_does_not_hang(self):
        # Surya in Karka (Chandra's), Chandra in Simha (Surya's).
        signs = {"Surya": KARKA, "Chandra": SIMHA}
        chain = dispositor_chain("Surya", signs)
        self.assertTrue(chain.in_cycle)
        self.assertIsNone(chain.final)
        self.assertEqual(chain.terminated_by, "cycle")
        self.assertEqual(set(chain.cycle), {"Surya", "Chandra"})

    def test_long_cycle_is_detected(self):
        # Surya->Karka(Chandra), Chandra->Mesha(Mangal), Mangal->Simha(Surya)
        signs = {"Surya": KARKA, "Chandra": MESHA, "Mangal": SIMHA}
        chain = dispositor_chain("Surya", signs)
        self.assertTrue(chain.in_cycle)
        self.assertEqual(set(chain.cycle), {"Surya", "Chandra", "Mangal"})

    def test_every_chain_terminates_for_a_full_chart(self):
        """Exhaustive: every graha in every rashi still terminates."""
        for sign in range(12):
            signs = {planet: (sign + index) % 12
                     for index, planet in enumerate(PLANET_NAMES)}
            for planet in signs:
                with self.subTest(sign=sign, planet=planet):
                    chain = dispositor_chain(planet, signs)
                    self.assertIn(chain.terminated_by,
                                  ("self_dispositor", "cycle", "no_lord"))
                    self.assertLessEqual(len(chain.chain), len(signs) + 1)

    def test_node_has_a_dispositor_but_is_never_one(self):
        signs = {"Rahu": KUMBHA, "Shani": MAKARA}
        chain = dispositor_chain("Rahu", signs)
        self.assertEqual(chain.chain[0], "Shani")
        for planet, final in final_dispositors(signs).items():
            self.assertNotIn(final, ("Rahu", "Ketu"))

    def test_parivartana_detected_both_ways(self):
        # Mangal in Vrishabha (Shukra's), Shukra in Mesha (Mangal's).
        swaps = find_parivartanas({"Mangal": VRISHABHA, "Shukra": MESHA},
                                  {"Mangal": 2, "Shukra": 1})
        self.assertEqual(len(swaps), 1)
        self.assertEqual({swaps[0].planet1, swaps[0].planet2},
                         {"Mangal", "Shukra"})

    def test_no_parivartana_when_only_one_side_holds(self):
        swaps = find_parivartanas({"Mangal": VRISHABHA, "Shukra": MITHUNA},
                                  {"Mangal": 2, "Shukra": 3})
        self.assertEqual(swaps, [])

    def test_own_sign_is_not_an_exchange_with_itself(self):
        swaps = find_parivartanas({"Mangal": MESHA}, {"Mangal": 1})
        self.assertEqual(swaps, [])

    def test_exchange_categories(self):
        # An exchange involving the 6th is dainya.
        swaps = find_parivartanas({"Mangal": VRISHABHA, "Shukra": MESHA},
                                  {"Mangal": 6, "Shukra": 1})
        self.assertEqual(swaps[0].category, "dainya")
        # Involving the 3rd is khala.
        swaps = find_parivartanas({"Mangal": VRISHABHA, "Shukra": MESHA},
                                  {"Mangal": 3, "Shukra": 1})
        self.assertEqual(swaps[0].category, "khala")
        # Otherwise maha.
        swaps = find_parivartanas({"Mangal": VRISHABHA, "Shukra": MESHA},
                                  {"Mangal": 5, "Shukra": 1})
        self.assertEqual(swaps[0].category, "maha")


# ── Part 8: combustion ───────────────────────────────────────────────────────

class CombustionTest(unittest.TestCase):

    def chart_with_separation(self, planet: str, separation: float,
                              retrograde: bool = False) -> JyotishChart:
        return synthetic_chart(
            MESHA,
            {"Surya": 100.0, planet: 100.0 + separation},
            retrograde={planet} if retrograde else set())

    def test_default_arcs_match_the_specified_profile(self):
        self.assertEqual(CLASSICAL_COMBUSTION.direct["Chandra"], 12.0)
        self.assertEqual(CLASSICAL_COMBUSTION.direct["Mangal"], 17.0)
        self.assertEqual(CLASSICAL_COMBUSTION.direct["Budha"], 14.0)
        self.assertEqual(CLASSICAL_COMBUSTION.direct["Guru"], 11.0)
        self.assertEqual(CLASSICAL_COMBUSTION.direct["Shukra"], 10.0)
        self.assertEqual(CLASSICAL_COMBUSTION.direct["Shani"], 15.0)
        self.assertEqual(CLASSICAL_COMBUSTION.retrograde["Budha"], 12.0)
        self.assertEqual(CLASSICAL_COMBUSTION.retrograde["Shukra"], 8.0)

    def test_each_arc_is_applied_at_its_boundary(self):
        for planet, arc in CLASSICAL_COMBUSTION.direct.items():
            with self.subTest(planet=planet):
                inside = self.chart_with_separation(planet, arc - 0.5)
                outside = self.chart_with_separation(planet, arc + 0.5)
                self.assertTrue(inside.planets[planet].is_combust)
                self.assertFalse(outside.planets[planet].is_combust)

    def test_retrograde_arcs_are_narrower_for_budha_and_shukra(self):
        for planet, direct, retro in (("Budha", 14.0, 12.0),
                                      ("Shukra", 10.0, 8.0)):
            with self.subTest(planet=planet):
                between = (direct + retro) / 2
                self.assertTrue(
                    self.chart_with_separation(planet, between).planets[planet].is_combust)
                self.assertFalse(
                    self.chart_with_separation(planet, between, retrograde=True)
                    .planets[planet].is_combust)

    def test_nodes_are_never_combust(self):
        for node in ("Rahu", "Ketu"):
            for separation in (0.0, 0.5, 5.0, 17.0):
                chart = self.chart_with_separation(node, separation)
                with self.subTest(node=node, separation=separation):
                    self.assertFalse(chart.planets[node].is_combust)
                    self.assertIsNone(chart.planets[node].combustion_orb)

    def test_separation_is_stored_whether_or_not_combust(self):
        chart = self.chart_with_separation("Shani", 40.0)
        self.assertAlmostEqual(chart.planets["Shani"].sun_separation, 40.0, places=4)
        self.assertFalse(chart.planets["Shani"].is_combust)
        self.assertEqual(chart.planets["Shani"].combustion_orb, 15.0)

    def test_separation_is_the_short_arc(self):
        chart = synthetic_chart(MESHA, {"Surya": 10.0, "Shani": 350.0})
        self.assertAlmostEqual(chart.planets["Shani"].sun_separation, 20.0, places=4)

    def test_sun_itself_has_no_separation(self):
        chart = self.chart_with_separation("Shani", 40.0)
        self.assertIsNone(chart.planets["Surya"].sun_separation)
        self.assertFalse(chart.planets["Surya"].is_combust)

    def test_profile_is_replaceable(self):
        strict = CombustionProfile(name="strict", direct={"Shani": 3.0})
        chart = JyotishChart.from_sidereal_longitudes(
            lagna_lon=0.0,
            planet_lons={"Surya": 100.0, "Shani": 105.0, "Guru": 102.0},
            combustion_profile=strict)
        self.assertFalse(chart.planets["Shani"].is_combust)   # 5° > 3° arc
        self.assertFalse(chart.planets["Guru"].is_combust)    # not in profile
        self.assertIsNone(chart.planets["Guru"].combustion_orb)


# ── Part 9: varga features ───────────────────────────────────────────────────

class VargaFeatureTest(unittest.TestCase):

    def setUp(self):
        self.chart = synthetic_chart(
            MESHA, {"Surya": 10.0, "Chandra": 100.0, "Mangal": 200.0,
                    "Budha": 160.0, "Guru": 40.0, "Shukra": 70.0,
                    "Shani": 280.0, "Rahu": 310.0, "Ketu": 130.0})
        self.features = build_chart_features(self.chart)

    def test_every_graha_has_every_varga(self):
        for name, planet in self.features.planets.items():
            with self.subTest(planet=name):
                self.assertEqual(set(planet.vargas), set(VARGA_ORDER))

    def test_each_placement_records_its_convention(self):
        for planet in self.features.planets.values():
            for key, placement in planet.vargas.items():
                with self.subTest(planet=planet.planet, varga=key):
                    self.assertTrue(placement.convention)

    def test_d1_placement_matches_the_rashi(self):
        for planet in self.features.planets.values():
            with self.subTest(planet=planet.planet):
                self.assertEqual(planet.vargas["D1"].sign, planet.sign)

    def test_vargottama_is_d1_equals_d9(self):
        for planet in self.features.planets.values():
            with self.subTest(planet=planet.planet):
                self.assertEqual(
                    planet.vargottama,
                    planet.vargas["D1"].sign == planet.vargas["D9"].sign)

    def test_known_vargottama_case(self):
        """0° of Mesha is Mesha in both D1 and D9 by construction."""
        chart = synthetic_chart(MESHA, {"Surya": 0.5})
        features = build_chart_features(chart)
        self.assertTrue(features.planets["Surya"].vargottama)

    def test_dignity_is_evaluated_within_each_varga(self):
        """
        Surya in the first navamsha of Mesha is exalted in D1 and in D9 alike,
        because that navamsha is Mesha again. Move it to 10° of Mesha and the
        navamsha becomes Karka (the fourth, since each spans 3°20'), where
        Surya has no special dignity — which is the point of checking dignity
        per varga rather than carrying the D1 verdict across.
        """
        first_navamsha = build_chart_features(
            synthetic_chart(MESHA, {"Surya": 1.0})).planets["Surya"]
        self.assertTrue(first_navamsha.vargas["D1"].exalted)
        self.assertEqual(first_navamsha.vargas["D9"].sign, MESHA)
        self.assertTrue(first_navamsha.vargas["D9"].exalted)
        self.assertTrue(first_navamsha.vargottama)

        fourth_navamsha = build_chart_features(
            synthetic_chart(MESHA, {"Surya": 10.0})).planets["Surya"]
        self.assertTrue(fourth_navamsha.vargas["D1"].exalted)
        self.assertEqual(fourth_navamsha.vargas["D9"].sign, KARKA)
        self.assertFalse(fourth_navamsha.vargas["D9"].exalted)
        self.assertFalse(fourth_navamsha.vargottama)

    def test_varga_lagna_is_computed_for_every_chart(self):
        self.assertEqual(set(self.features.varga_lagnas), set(VARGA_ORDER))
        for key, placement in self.features.varga_lagnas.items():
            with self.subTest(varga=key):
                self.assertTrue(0 <= placement.sign <= 11)
                self.assertTrue(placement.lord)

    def test_varga_lord_matches_the_rashi_lord(self):
        for planet in self.features.planets.values():
            for key, placement in planet.vargas.items():
                with self.subTest(planet=planet.planet, varga=key):
                    self.assertEqual(placement.lord, lord_of_sign(placement.sign))

    def test_varga_config_choice_flows_into_features(self):
        config = VargaConfig(conventions={"D10": "parivritti"})
        features = build_chart_features(self.chart, varga_config=config)
        for planet in features.planets.values():
            with self.subTest(planet=planet.planet):
                self.assertEqual(planet.vargas["D10"].convention, "parivritti")


# ── Part 12: functional nature ───────────────────────────────────────────────

class FunctionalNatureTest(unittest.TestCase):

    def test_yogakaraka_for_the_classical_lagnas(self):
        """
        The textbook cases: Shani is yogakaraka for Vrishabha and Tula,
        Mangal for Karka and Simha, Shukra for Makara and Kumbha.
        """
        self.assertIn("Shani", yogakarakas(VRISHABHA))
        self.assertIn("Shani", yogakarakas(TULA))
        self.assertIn("Mangal", yogakarakas(KARKA))
        self.assertIn("Mangal", yogakarakas(SIMHA))
        self.assertIn("Shukra", yogakarakas(MAKARA))
        self.assertIn("Shukra", yogakarakas(KUMBHA))

    def test_yogakaraka_requires_a_kendra_and_a_trikona_beyond_the_first(self):
        """
        Owning the 1st does not make a graha a yogakaraka on its own, even
        though the 1st is both a kendra and a trikona.
        """
        for lagna in range(12):
            roles = functional_roles(lagna)
            for planet, role in roles.items():
                if not role.is_yogakaraka:
                    continue
                kendras = [h for h in role.houses_owned
                           if h in KENDRA_HOUSES and h != 1]
                trikonas = [h for h in role.houses_owned
                            if h in TRIKONA_HOUSES and h != 1]
                with self.subTest(lagna=lagna, planet=planet):
                    self.assertTrue(kendras and trikonas)

    def test_shani_is_not_yogakaraka_for_mesha(self):
        self.assertNotIn("Shani", yogakarakas(MESHA))

    def test_nodes_have_no_functional_nature(self):
        for lagna in range(12):
            roles = functional_roles(lagna)
            for node in ("Rahu", "Ketu"):
                with self.subTest(lagna=lagna, node=node):
                    self.assertEqual(roles[node].functional_nature, "none")
                    self.assertEqual(roles[node].houses_owned, [])

    def test_natural_and_functional_nature_are_reported_separately(self):
        """
        Guru from a Vrishabha Lagna owns the 8th and 11th: a natural benefic
        whose functional standing is quite different.
        """
        chart = synthetic_chart(VRISHABHA, {"Guru": DHANU, "Surya": SIMHA})
        features = build_chart_features(chart)
        guru = features.planets["Guru"]
        self.assertTrue(guru.natural_benefic)
        self.assertEqual(sorted(guru.houses_owned), [8, 11])
        self.assertNotEqual(guru.functional_nature, "benefic")

    def test_roles_are_recorded_for_every_lagna(self):
        for lagna in range(12):
            roles = functional_roles(lagna)
            with self.subTest(lagna=lagna):
                lagna_lords = [p for p, r in roles.items() if r.is_lagna_lord]
                self.assertEqual(len(lagna_lords), 1)
                self.assertTrue(any("dharma_lord" in r.roles for r in roles.values()))
                self.assertTrue(any("karma_lord" in r.roles for r in roles.values()))


# ── relationships ────────────────────────────────────────────────────────────

class RelationshipTest(unittest.TestCase):

    def test_known_friendships(self):
        self.assertEqual(natural_relationship("Surya", "Guru"), "friend")
        self.assertEqual(natural_relationship("Surya", "Shani"), "enemy")
        self.assertEqual(natural_relationship("Shani", "Shukra"), "friend")
        self.assertEqual(natural_relationship("Guru", "Budha"), "enemy")
        self.assertEqual(natural_relationship("Chandra", "Mangal"), "neutral")

    def test_moon_has_no_natural_enemy(self):
        table = relationship_table()
        self.assertNotIn("enemy", table["Chandra"].values())

    def test_nodes_are_unclassified(self):
        self.assertEqual(natural_relationship("Rahu", "Surya"), "unclassified")
        self.assertEqual(natural_relationship("Surya", "Rahu"), "unclassified")

    def test_sign_relationship_uses_the_rashi_lord(self):
        # Simha is Surya's own rashi.
        self.assertEqual(sign_relationship("Surya", SIMHA), "friend")
        # Makara is Shani's, and Shani is Surya's enemy.
        self.assertEqual(sign_relationship("Surya", MAKARA), "enemy")

    def test_temporary_friendship_follows_the_2_3_4_10_11_12_rule(self):
        for distance in (2, 3, 4, 10, 11, 12):
            with self.subTest(distance=distance):
                other = ((1 + distance - 1 - 1) % 12) + 1
                self.assertEqual(temporary_relationship(1, other), "friend")
        for distance in (1, 5, 6, 7, 8, 9):
            with self.subTest(distance=distance):
                other = ((1 + distance - 1 - 1) % 12) + 1
                self.assertEqual(temporary_relationship(1, other), "enemy")


# ── whole-chart assembly ─────────────────────────────────────────────────────

class ChartFeatureAssemblyTest(unittest.TestCase):

    def setUp(self):
        self.chart = synthetic_chart(
            MEENA, {"Surya": SIMHA, "Chandra": MEENA, "Mangal": MEENA,
                    "Budha": KANYA, "Guru": VRISHABHA, "Shukra": MITHUNA,
                    "Shani": DHANU, "Rahu": KUMBHA, "Ketu": SIMHA})
        self.features = build_chart_features(self.chart)

    def test_all_twelve_houses_present(self):
        self.assertEqual(sorted(self.features.houses), list(range(1, 13)))

    def test_house_of_each_graha_is_consistent_with_its_sign(self):
        for name, planet in self.features.planets.items():
            expected = ((planet.sign - self.features.lagna_sign) % 12) + 1
            with self.subTest(planet=name):
                self.assertEqual(planet.house, expected)

    def test_occupants_agree_with_per_graha_houses(self):
        for number, bhava in self.features.houses.items():
            expected = sorted(p for p, f in self.features.planets.items()
                              if f.house == number)
            with self.subTest(house=number):
                self.assertEqual(sorted(bhava.occupants), expected)

    def test_aspects_given_and_received_are_two_views_of_one_list(self):
        given = sum(len(p.aspects_given) for p in self.features.planets.values())
        self.assertEqual(given, len(self.features.aspects))
        for name, planet in self.features.planets.items():
            for aspect in planet.aspects_received:
                with self.subTest(planet=name, source=aspect.source):
                    self.assertEqual(aspect.to_sign, planet.sign)
                    self.assertIn(name, aspect.targets)

    def test_house_categories(self):
        houses = self.features.houses
        self.assertTrue(all(houses[h].is_kendra for h in (1, 4, 7, 10)))
        self.assertTrue(all(houses[h].is_trikona for h in (1, 5, 9)))
        self.assertTrue(all(houses[h].is_dusthana for h in (6, 8, 12)))
        self.assertTrue(all(houses[h].is_maraka for h in (2, 7)))

    def test_provenance_records_every_convention(self):
        provenance = self.features.provenance
        for key in ("house_system", "aspect_profile", "node_aspects",
                    "conjunction_orb_deg", "varga_conventions",
                    "combustion_profile", "positions", "ayanamsha"):
            with self.subTest(key=key):
                self.assertIn(key, provenance)

    def test_entered_positions_are_flagged_as_unmeasured_speed(self):
        """
        An entered chart carries direction but not speed, and the feature set
        must say so rather than presenting the placeholder as an observation.
        """
        self.assertTrue(self.features.warnings)
        for planet in self.features.planets.values():
            with self.subTest(planet=planet.planet):
                self.assertFalse(planet.speed_is_measured)
                self.assertFalse(planet.stationary)

    def test_calculated_chart_has_measured_speeds(self):
        import datetime
        from engine.planets import jde_from_datetime
        chart = JyotishChart(
            jde=jde_from_datetime(datetime.datetime(1988, 8, 30, 14, 48)),
            lat=26.9124, lon=75.7873)
        features = build_chart_features(chart)
        self.assertEqual(features.warnings, [])
        for planet in features.planets.values():
            with self.subTest(planet=planet.planet):
                self.assertTrue(planet.speed_is_measured)

    def test_lookup_helpers(self):
        features = self.features
        self.assertEqual(features.lord_of(1), "Guru")
        self.assertEqual(features.house_of("Budha"), 7)
        self.assertIn("Budha", features.occupants_of(7))
        self.assertEqual(features.houses_owned_by("Budha"), [4, 7])
        self.assertEqual(features.house_distance(1, 7), 7)
        self.assertEqual(features.house_distance(7, 1), 7)
        self.assertEqual(features.house_distance(1, 1), 1)

    def test_default_conjunction_orb(self):
        self.assertEqual(
            self.features.provenance["conjunction_orb_deg"],
            f"{DEFAULT_ORB_DEG:g}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
