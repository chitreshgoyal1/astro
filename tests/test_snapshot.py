"""
Canonical chart snapshot (V1.2 Parts 11-13)
--------------------------------------------
The snapshot is a CONTRACT. A transit engine, a prediction layer, an API, a UI
and a PDF generator will all read it, and they will be written against a shape
they cannot see changing. So the shape is pinned here: required sections,
required keys, JSON-native types, and a version that has to move when any of
that moves.

Also covers the strength-terminology rules (Part 11) and the Varga validation
metadata (Part 12), both of which surface through the snapshot.
"""

# V1.2.

import datetime
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.features import build_chart_features
from engine.planets import JyotishChart, jde_from_datetime
from engine.rules import YogaStatus, evaluate_rules, rules_for_profile
from engine.snapshot import SCHEMA_VERSION, ChartSnapshot, build_snapshot
from engine.timing import from_chart as dasha_from_chart
from engine.varga_metadata import (
    CONVENTION_METADATA, IMPLEMENTATION_CONSISTENT, REQUIRED_METADATA_CHARTS,
    SOURCE_VALIDATED, VARGA_ALGORITHM_VERSION, all_metadata,
    convention_metadata, metadata_for,
)
from engine.vargas import VARGA_ORDER, VARGA_SPECS, VargaConfig

BIRTH_LOCAL = datetime.datetime(1988, 8, 30, 20, 18)
BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)


def full_snapshot() -> ChartSnapshot:
    from engine.ashtakavarga import compute_ashtakavarga
    from engine.houses import build_bhava_chart
    from engine.location import resolve_location
    from engine.strength import compute_shadbala
    chart = JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                         lat=26.9124, lon=75.7873)
    config = VargaConfig()
    features = build_chart_features(chart, varga_config=config)
    return build_snapshot(
        chart,
        features=features,
        yoga_results=evaluate_rules(features),
        dasha=dasha_from_chart(chart, BIRTH_LOCAL, depth=2),
        varga_config=config,
        birth_datetime=BIRTH_LOCAL,
        birth_utc=BIRTH_UTC,
        location=resolve_location(place="Jaipur", local_datetime=BIRTH_LOCAL),
        name="Chitresh Goyal",
        shadbala=compute_shadbala(chart, features, birth=BIRTH_LOCAL),
        ashtakavarga=compute_ashtakavarga(chart),
        bhava=build_bhava_chart(chart, "sripati"))


class SchemaShapeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.snapshot = full_snapshot()
        cls.data = cls.snapshot.to_dict()

    def test_schema_version_is_semantic(self):
        parts = SCHEMA_VERSION.split(".")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())

    def test_required_top_level_sections(self):
        """Every section any brief has named, across V1.2, V1.3 and V1.4."""
        for section in ("schema_version", "birth", "calculation_settings",
                        "accuracy", "planets", "houses", "vargas", "features",
                        "yogas", "timing", "lagna", "methodology",
                        "strengths", "ashtakavarga", "bhava",
                        "birth_time_sensitivity"):
            with self.subTest(section=section):
                self.assertIn(section, self.data)

    def test_v14_sections_are_populated(self):
        self.assertIn("planets", self.data["strengths"])
        self.assertIn("bhinna", self.data["ashtakavarga"])
        self.assertIn("placements", self.data["bhava"])

    def test_transits_are_not_embedded_in_the_natal_snapshot(self):
        """
        Part 21, explicitly. A natal chart is immutable; a transit snapshot is
        a function of an arbitrary moment. Embedding one in the other would
        make the natal snapshot silently time-dependent.
        """
        self.assertNotIn("transits", self.data)
        self.assertNotIn("transit_snapshot", self.data)
        import json
        blob = json.dumps(self.data).lower()
        self.assertNotIn("transit_to_natal", blob)

    def test_schema_version_is_1_2_for_the_v14_additions(self):
        major, minor, _patch = SCHEMA_VERSION.split(".")
        self.assertEqual(major, "1")
        self.assertGreaterEqual(int(minor), 2,
                                "V1.4 added four sections: a minor bump")

    def test_v14_additions_are_backward_compatible(self):
        """
        Nothing a 1.0.0 or 1.1.0 reader depended on was removed or
        redefined. A reader of either keeps working and simply does not see
        the new sections.
        """
        for section in ("schema_version", "birth", "calculation_settings",
                        "accuracy", "lagna", "planets", "houses", "vargas",
                        "features", "yogas", "timing", "methodology"):
            with self.subTest(section=section):
                self.assertIn(section, self.data)
        # The house section still means WHOLE SIGN, even with a bhava chart
        # present. A consumer reading `houses` must never find bhavas there.
        self.assertEqual(len(self.data["houses"]), 12)
        self.assertEqual(self.data["bhava"]["system"], "sripati")

    def test_methodology_records_the_house_system(self):
        self.assertEqual(self.data["methodology"]["house_system"], "sripati")
        self.assertEqual(self.data["methodology"]["rule_reference_space"],
                         "RASHI")

    def test_optional_sections_are_empty_when_not_computed(self):
        chart = JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                             lat=26.9124, lon=75.7873)
        data = build_snapshot(chart).to_dict()
        for section in ("strengths", "ashtakavarga", "bhava",
                        "birth_time_sensitivity"):
            with self.subTest(section=section):
                self.assertEqual(data[section], {})

    def test_serialises_with_the_standard_encoder(self):
        """
        Part 13: JSON-serialisable with no custom post-processing. A dataclass
        or a datetime leaking in would raise here.
        """
        json.dumps(self.data)

    def test_round_trips_through_json_unchanged(self):
        self.assertEqual(json.loads(json.dumps(self.data)), self.data)

    def test_no_python_objects_survive(self):
        """Every leaf must be a JSON primitive."""
        allowed = (str, int, float, bool, type(None))

        def walk(node, path="root"):
            if isinstance(node, dict):
                for key, value in node.items():
                    self.assertIsInstance(key, str, f"{path}: non-string key")
                    walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")
            else:
                self.assertIsInstance(node, allowed, f"{path} is {type(node)}")

        walk(self.data)

    def test_calculation_settings_record_every_choice(self):
        settings = self.data["calculation_settings"]
        for key in ("zodiac", "ayanamsha", "node", "house_system",
                    "positions_source", "aspect_profile", "node_aspects",
                    "combustion_profile"):
            with self.subTest(key=key):
                self.assertIn(key, settings)
        self.assertEqual(settings["zodiac"], "sidereal")
        self.assertEqual(settings["house_system"], "whole_sign")

    def test_birth_section(self):
        birth = self.data["birth"]
        self.assertEqual(birth["name"], "Chitresh Goyal")
        self.assertTrue(birth["datetime_local"].startswith("1988-08-30"))
        self.assertIn("location", birth)
        self.assertAlmostEqual(birth["location"]["latitude"], 26.9124, places=4)
        self.assertIn("resolved_by", birth["location"])

    def test_every_graha_is_present_with_facts(self):
        planets = self.data["planets"]
        self.assertEqual(len(planets), 9)
        for name, entry in planets.items():
            with self.subTest(graha=name):
                for key in ("longitude", "sign", "degree_in_sign", "house",
                            "nakshatra", "pada", "dignity", "retrograde",
                            "houses_owned", "theory"):
                    self.assertIn(key, entry)

    def test_accuracy_section_carries_provenance_and_warnings(self):
        accuracy = self.data["accuracy"]
        for key in ("basis", "envelopes_arcmin", "theories", "vsop87",
                    "boundary_warnings"):
            with self.subTest(key=key):
                self.assertIn(key, accuracy)
        self.assertIn("Bretagnon", accuracy["vsop87"]["theory"])

    def test_timing_section_holds_the_vimshottari_tree(self):
        vimshottari = self.data["timing"]["vimshottari"]
        self.assertEqual(vimshottari["system"], "vimshottari")
        self.assertEqual(len(vimshottari["mahadashas"]), 9)
        self.assertIn("convention", vimshottari)
        self.assertIn("balance_at_birth", vimshottari)

    def test_houses_are_string_keyed_for_json(self):
        houses = self.data["houses"]
        self.assertEqual(sorted(houses), sorted(str(n) for n in range(1, 13)))

    def test_contains_no_prose_predictions(self):
        """
        Part 13: facts, not prose. The V1 graha-fal sentences are the thing
        being kept out.
        """
        blob = json.dumps(self.data).lower()
        for phrase in ("you will", "the native will", "brings wealth",
                       "financial prosperity", "marital happiness"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, blob)

    def test_write_and_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "snapshot.json")
            self.snapshot.write(path)
            with open(path, encoding="utf-8") as handle:
                reloaded = json.load(handle)
        self.assertEqual(reloaded["schema_version"], SCHEMA_VERSION)

    def test_snapshot_works_without_optional_sections(self):
        """A chart alone must still produce a valid snapshot."""
        chart = JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                             lat=26.9124, lon=75.7873)
        snapshot = build_snapshot(chart)
        json.dumps(snapshot.to_dict())
        self.assertEqual(snapshot.yogas, [])
        self.assertEqual(snapshot.timing, {})
        self.assertTrue(snapshot.planets)


class YogaSerialisationTest(unittest.TestCase):
    """Part 11: the score must never travel without its disclaimer."""

    @classmethod
    def setUpClass(cls):
        cls.data = full_snapshot().to_dict()
        cls.yogas = cls.data["yogas"]

    def test_every_rule_is_reported(self):
        self.assertEqual(len(self.yogas), len(rules_for_profile("parashari")))

    def test_present_yogas_carry_score_metadata(self):
        present = [y for y in self.yogas if y["present"]]
        self.assertTrue(present)
        for yoga in present:
            with self.subTest(yoga=yoga["id"]):
                self.assertIn("engine_strength_score", yoga)
                self.assertEqual(yoga["score_type"], "software_heuristic")
                self.assertIs(yoga["classical_measure"], False)

    def test_score_is_never_called_classical_strength(self):
        blob = json.dumps(self.data)
        self.assertNotIn("classical_strength", blob)

    def test_score_range(self):
        for yoga in self.yogas:
            if "engine_strength_score" not in yoga:
                continue
            with self.subTest(yoga=yoga["id"]):
                self.assertGreaterEqual(yoga["engine_strength_score"], 0)
                self.assertLessEqual(yoga["engine_strength_score"], 100)

    def test_absent_yogas_carry_no_score(self):
        for yoga in self.yogas:
            if yoga["present"]:
                continue
            with self.subTest(yoga=yoga["id"]):
                self.assertNotIn("engine_strength_score", yoga)

    def test_every_yoga_carries_its_source(self):
        for yoga in self.yogas:
            with self.subTest(yoga=yoga["id"]):
                self.assertTrue(yoga["source"])
                self.assertTrue(yoga["tradition"])
                self.assertTrue(yoga["explanation"])


class ScoreDoesNotDecidePresenceTest(unittest.TestCase):
    """
    Part 11's hard rule: presence must never depend on a numeric threshold.

    This is checked structurally rather than by example — every rule in the
    catalog is evaluated against many charts, and a formed yoga is required to
    stay formed no matter what its score came out as.
    """

    def charts(self):
        for lagna in range(0, 12, 2):
            for shift in (0, 4, 7):
                longitudes = {
                    planet: ((lagna + shift + index) % 12) * 30.0 + 15.0
                    for index, planet in enumerate(
                        ["Surya", "Chandra", "Mangal", "Budha", "Guru",
                         "Shukra", "Shani", "Rahu", "Ketu"])
                }
                yield JyotishChart.from_sidereal_longitudes(
                    lagna_lon=lagna * 30.0 + 15.0, planet_lons=longitudes)

    def test_weakened_and_strong_are_both_present(self):
        seen = set()
        for chart in self.charts():
            for result in evaluate_rules(build_chart_features(chart)):
                seen.add(result.status)
                if result.status is YogaStatus.ABSENT:
                    continue
                with self.subTest(rule=result.id):
                    self.assertTrue(
                        result.present,
                        "a scored status must still count as present")
        self.assertIn(YogaStatus.PRESENT_AND_STRONG, seen)

    def test_absence_is_always_explained_by_a_failed_condition(self):
        """
        If a yoga is ABSENT there must be a clause that failed. An absence
        produced by a low score would have no failed clause to point at.
        """
        for chart in self.charts():
            features = build_chart_features(chart)
            for result in evaluate_rules(features):
                if result.status is not YogaStatus.ABSENT:
                    continue
                with self.subTest(rule=result.id):
                    self.assertTrue(
                        result.conditions_failed,
                        f"{result.id} is absent with no failed condition")

    def test_cancellation_is_the_only_route_to_ineffective(self):
        for chart in self.charts():
            features = build_chart_features(chart)
            for result in evaluate_rules(features):
                if result.present and not result.effective:
                    with self.subTest(rule=result.id):
                        self.assertEqual(result.status,
                                         YogaStatus.PRESENT_BUT_CANCELLED)
                        self.assertTrue(result.cancellations_found)


class VargaMetadataTest(unittest.TestCase):
    """Part 12: implementation consistency is not source validation."""

    def test_every_registered_convention_has_metadata(self):
        for chart in VARGA_ORDER:
            for convention in VARGA_SPECS[chart].conventions:
                with self.subTest(chart=chart, convention=convention):
                    meta = metadata_for(chart, convention)
                    self.assertTrue(meta.tradition)
                    self.assertTrue(meta.source)
                    self.assertTrue(meta.algorithm_version)

    def test_no_orphan_metadata(self):
        """Metadata must not describe a convention that no longer exists."""
        for (chart, convention) in CONVENTION_METADATA:
            with self.subTest(chart=chart, convention=convention):
                self.assertIn(chart, VARGA_SPECS)
                self.assertIn(convention, VARGA_SPECS[chart].conventions)

    def test_charts_named_in_the_brief_all_carry_metadata(self):
        for chart in REQUIRED_METADATA_CHARTS:
            with self.subTest(chart=chart):
                self.assertIn(chart, VARGA_ORDER)
                entries = [m for (c, _v), m in CONVENTION_METADATA.items()
                           if c == chart]
                self.assertTrue(entries)

    def test_nothing_claims_source_validation(self):
        """
        The honest position: two implementations of one formula agreeing says
        nothing about whether we read the source correctly. If a convention
        ever IS validated against a text, this test should be updated
        deliberately — not silently.
        """
        claimed = [m for m in all_metadata()
                   if m["validation"] == SOURCE_VALIDATED]
        self.assertEqual(
            claimed, [],
            "a convention claims source validation; confirm that work was "
            "actually done before allowing this")

    def test_validation_level_is_stated_with_its_meaning(self):
        for meta in all_metadata():
            with self.subTest(chart=meta["chart"], conv=meta["convention_id"]):
                self.assertEqual(meta["validation"], IMPLEMENTATION_CONSISTENT)
                self.assertIn("confirms the code", meta["validation_meaning"])

    def test_identical_conventions_are_flagged(self):
        """The four that cannot change anything must say so."""
        expected = {("D7", "parivritti"), ("D16", "parivritti"),
                    ("D20", "parivritti"), ("D27", "parivritti")}
        flagged = {(m["chart"], m["convention_id"]) for m in all_metadata()
                   if "identical_to" in m}
        self.assertEqual(flagged, expected)

    def test_untraced_sources_say_so_rather_than_naming_a_text(self):
        for chart, convention in (("D30", "movable_lords"),
                                  ("D60", "reverse_even")):
            meta = metadata_for(chart, convention)
            with self.subTest(chart=chart):
                self.assertIn("not established", meta.source)
                self.assertNotIn("BPHS", meta.source)

    def test_snapshot_carries_the_active_conventions(self):
        data = full_snapshot().to_dict()
        conventions = data["vargas"]["conventions"]
        self.assertEqual(conventions["algorithm_version"],
                         VARGA_ALGORITHM_VERSION)
        self.assertIn("caveat", conventions)
        self.assertEqual(sorted(conventions["active"]), sorted(VARGA_ORDER))
        for chart, meta in conventions["active"].items():
            with self.subTest(chart=chart):
                for key in ("convention_id", "tradition", "source",
                            "validation", "algorithm_version"):
                    self.assertIn(key, meta)

    def test_config_choice_flows_into_the_metadata(self):
        config = VargaConfig(conventions={"D30": "parivritti"})
        active = convention_metadata(config)["active"]
        self.assertEqual(active["D30"]["convention_id"], "parivritti")

    def test_unregistered_convention_raises(self):
        with self.assertRaises(KeyError):
            metadata_for("D9", "made_up")


if __name__ == "__main__":
    unittest.main(verbosity=2)
