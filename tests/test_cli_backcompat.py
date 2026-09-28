"""
Backward compatibility (Part 15)
--------------------------------
Every command and input format that worked in V1 must still work. These tests
drive the real CLI as a subprocess rather than importing it, because the thing
being protected is the command-line contract itself: flag names, exit codes
and the presence of each report section.

The one deliberate break is documented and tested for: an unknown birth place
used to produce a chart on Delhi's coordinates and now fails. That was the
point of Part 2, and test_location.py covers it.
"""

# Phase 2 (V1.1).

import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def run_cli(*args, timeout=180) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "main.py", *args],
                          cwd=ROOT, capture_output=True, text=True,
                          timeout=timeout)


class ExistingFlagsTest(unittest.TestCase):
    """Part 15 names these explicitly: none may break."""

    def test_help_lists_every_preserved_flag(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        for flag in ("--consultation", "--enter-degrees", "--varga-config",
                     "--ayanamsha", "--node", "--tolerance", "--pdf",
                     "--selftest", "--name", "--dob", "--time", "--place",
                     "--list-conventions", "--page-size", "--landscape"):
            with self.subTest(flag=flag):
                self.assertIn(flag, result.stdout)

    def test_selftest_passes(self):
        result = run_cli("--selftest")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("All checks passed", result.stdout)

    def test_list_conventions(self):
        result = run_cli("--list-conventions")
        self.assertEqual(result.returncode, 0)
        for varga in ("D1", "D9", "D30", "D60"):
            with self.subTest(varga=varga):
                self.assertIn(varga, result.stdout)

    def test_consultation_file(self):
        result = run_cli("--consultation", "chitresh_consultation.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JYOTISH CHART", result.stdout)

    def test_consultation_file_with_entered_degrees(self):
        """sample_consultation.json carries a full set of entered degrees."""
        result = run_cli("--consultation", "sample_consultation.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ENTERED vs CALCULATED", result.stdout)
        self.assertIn("Interpretation uses the ENTERED degrees", result.stdout)

    def test_command_line_flags_form(self):
        result = run_cli("--name", "Test Person", "--dob", "1990-06-15",
                         "--time", "06:30", "--place", "Delhi")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JYOTISH CHART", result.stdout)

    def test_varga_config(self):
        result = run_cli("--consultation", "chitresh_consultation.json",
                         "--varga-config", "varga_config.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SHODASHA VARGA", result.stdout)

    def test_every_ayanamsha_still_works(self):
        for ayanamsha in ("lahiri", "raman", "krishnamurti", "fagan_bradley"):
            with self.subTest(ayanamsha=ayanamsha):
                result = run_cli("--consultation", "chitresh_consultation.json",
                                 "--ayanamsha", ayanamsha, "--no-features")
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_node_choice(self):
        for node in ("true", "mean"):
            with self.subTest(node=node):
                result = run_cli("--consultation", "chitresh_consultation.json",
                                 "--node", node, "--no-features")
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"Node: {node}", result.stdout)

    def test_tolerance(self):
        result = run_cli("--consultation", "sample_consultation.json",
                         "--tolerance", "5.0", "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_pdf_output(self):
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "out.pdf")
            result = run_cli("--consultation", "chitresh_consultation.json",
                             "--pdf", target)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(os.path.exists(target))
            self.assertGreater(os.path.getsize(target), 1000)
            with open(target, "rb") as handle:
                self.assertTrue(handle.read(5).startswith(b"%PDF"))

    def test_pdf_page_size_and_landscape(self):
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "letter.pdf")
            result = run_cli("--consultation", "chitresh_consultation.json",
                             "--pdf", target, "--page-size", "letter",
                             "--landscape")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(os.path.exists(target))

    def test_bad_varga_config_is_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as handle:
            json.dump({"conventions": {"D9": "nonsense"}}, handle)
            path = handle.name
        try:
            result = run_cli("--consultation", "chitresh_consultation.json",
                             "--varga-config", path)
            self.assertNotEqual(result.returncode, 0)
        finally:
            os.unlink(path)


class ReportSectionsTest(unittest.TestCase):
    """Every V1 section survives, and the two new ones appear."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_cli("--consultation", "chitresh_consultation.json")
        assert cls.result.returncode == 0, cls.result.stdout + cls.result.stderr
        cls.output = cls.result.stdout

    def test_v1_chart_sections_still_present(self):
        """The chart output itself is unchanged from V1."""
        for section in ("JYOTISH CHART", "NORTH INDIAN CHART",
                        "SHODASHA VARGA"):
            with self.subTest(section=section):
                self.assertIn(section, self.output)

    def test_new_sections_present(self):
        for section in ("ASTROLOGY FEATURES", "YOGA ANALYSIS",
                        "HOUSE LORDS", "GRAHA FEATURES", "FUNCTIONAL NATURE",
                        "DISPOSITOR CHAINS", "CONJUNCTIONS",
                        "VIMSHOTTARI DASHA"):
            with self.subTest(section=section):
                self.assertIn(section, self.output)

    def test_no_features_flag_suppresses_only_the_new_sections(self):
        result = run_cli("--consultation", "chitresh_consultation.json",
                         "--no-features")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("ASTROLOGY FEATURES", result.stdout)
        self.assertNotIn("YOGA ANALYSIS", result.stdout)
        self.assertIn("JYOTISH CHART", result.stdout)

    def test_no_llm_generated_narrative(self):
        """Facts and rules only — no generated prose, still true in V1.2."""
        analysis = self.output[self.output.index("YOGA ANALYSIS"):]
        for phrase in ("you will", "the native will", "this suggests that you",
                       "indicates that you"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase.lower(), analysis.lower())


class LegacyFalIsolationTest(unittest.TestCase):
    """
    V1.2 Part 3: the superseded V1 interpretation must not appear beside the
    rule engine's, because the two disagree. It stays reachable, but only on
    request and only under a label.
    """

    @classmethod
    def setUpClass(cls):
        cls.default = run_cli("--consultation", "chitresh_consultation.json")
        cls.legacy = run_cli("--consultation", "chitresh_consultation.json",
                             "--legacy-fal")
        assert cls.default.returncode == 0
        assert cls.legacy.returncode == 0

    def test_legacy_report_is_absent_by_default(self):
        for marker in ("FAL REPORT", "YOGAS PRESENT",
                       "VIMSHOTTARI DASHA SEQUENCE", "GRAHA FAL"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.default.stdout)

    def test_only_one_yoga_system_appears_by_default(self):
        """The defect being prevented: two contradictory yoga lists."""
        self.assertIn("YOGA ANALYSIS", self.default.stdout)
        self.assertNotIn("YOGAS PRESENT", self.default.stdout)

    def test_legacy_flag_restores_the_v1_report(self):
        for marker in ("FAL REPORT", "YOGAS PRESENT", "GRAHA FAL",
                       "VIMSHOTTARI DASHA SEQUENCE"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.legacy.stdout)

    def test_legacy_output_is_clearly_labelled(self):
        self.assertIn("LEGACY V1 INTERPRETATION", self.legacy.stdout)
        self.assertIn("NOT USED BY THE CURRENT RULE ENGINE", self.legacy.stdout)

    def test_label_precedes_the_legacy_content(self):
        output = self.legacy.stdout
        self.assertLess(output.index("LEGACY V1 INTERPRETATION"),
                        output.index("YOGAS PRESENT"))

    def test_legacy_and_new_results_are_never_merged(self):
        """
        Both appear when asked for, in separate sections. The new analysis
        must come first and must not contain the legacy verdicts.
        """
        output = self.legacy.stdout
        new_section = output[output.index("YOGA ANALYSIS"):
                             output.index("LEGACY V1 INTERPRETATION")]
        self.assertNotIn("YOGAS PRESENT", new_section)
        self.assertNotIn("Raja Yoga (Budha)", new_section)

    def test_legacy_module_still_importable_with_its_v1_api(self):
        from engine.fal import (
            DASHA_ORDER, DASHA_YEARS, compute_vimshottari_dasha, detect_yogas,
            generate_fal_report, get_graha_fal,
        )
        for symbol in (detect_yogas, generate_fal_report, get_graha_fal,
                       compute_vimshottari_dasha):
            self.assertTrue(callable(symbol))
        self.assertEqual(len(DASHA_ORDER), 9)
        self.assertEqual(sum(DASHA_YEARS.values()), 120)

    def test_legacy_module_docstring_marks_it_as_superseded(self):
        import engine.fal as legacy
        self.assertIn("LEGACY", legacy.__doc__)
        self.assertIn("NOT USED BY THE CURRENT RULE ENGINE", legacy.__doc__)

    def test_legacy_yoga_results_are_not_in_the_snapshot(self):
        """The canonical snapshot carries rule-engine results only."""
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "snap.json")
            result = run_cli("--consultation", "chitresh_consultation.json",
                             "--legacy-fal", "--json-output", target,
                             "--json-compact")
            self.assertEqual(result.returncode, 0, result.stdout)
            with open(target, encoding="utf-8") as handle:
                data = json.load(handle)
        ids = {yoga["id"] for yoga in data["yogas"]}
        # Rule-engine ids are machine ids; the V1 engine had display names.
        self.assertIn("mahapurusha_bhadra", ids)
        for yoga in data["yogas"]:
            with self.subTest(yoga=yoga["id"]):
                self.assertNotEqual(yoga["name"], "Raja Yoga (Budha)")

class NewFlagsTest(unittest.TestCase):

    def test_rule_profile_choice(self):
        for profile in ("parashari", "parashari_extended"):
            with self.subTest(profile=profile):
                result = run_cli("--consultation", "chitresh_consultation.json",
                                 "--rule-profile", profile)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"Rule profile : {profile}", result.stdout)

    def test_node_aspect_conventions(self):
        for convention in ("none", "parashari_like", "kendra"):
            with self.subTest(convention=convention):
                result = run_cli("--consultation", "chitresh_consultation.json",
                                 "--node-aspects", convention)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"node aspects             {convention}",
                              result.stdout)

    def test_show_absent_yogas(self):
        result = run_cli("--consultation", "chitresh_consultation.json",
                         "--show-absent-yogas")
        self.assertEqual(result.returncode, 0)
        self.assertIn("COMBINATIONS NOT FORMED", result.stdout)
        self.assertIn("failed:", result.stdout)

    def test_invalid_rule_profile_is_rejected(self):
        result = run_cli("--consultation", "chitresh_consultation.json",
                         "--rule-profile", "made_up")
        self.assertNotEqual(result.returncode, 0)


class ConsultationJsonTest(unittest.TestCase):
    """The V1 JSON shape must keep loading, and the new keys must be optional."""

    def write_and_run(self, payload, *extra):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as handle:
            json.dump(payload, handle)
            path = handle.name
        try:
            return run_cli("--consultation", path, *extra)
        finally:
            os.unlink(path)

    def test_v1_shape_still_loads(self):
        result = self.write_and_run({
            "name": "Ram Sharma",
            "dob": "1990-06-15",
            "tob": "06:30",
            "place": "Delhi",
            "zodiac": "sidereal",
            "ayanamsha": "Lahiri",
            "positions": {"Lagna": "Mithuna 12 40", "Surya": "Vrishabha 0 55"},
        }, "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ENTERED vs CALCULATED", result.stdout)

    def test_empty_positions_still_loads(self):
        result = self.write_and_run({
            "name": "Test", "dob": "1988-08-30", "tob": "20:18",
            "place": "Jaipur", "positions": {},
        }, "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_time_key_alias_still_works(self):
        result = self.write_and_run({
            "name": "Test", "dob": "1988-08-30", "time": "20:18",
            "place": "Jaipur",
        }, "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_new_geography_keys_are_accepted(self):
        result = self.write_and_run({
            "name": "Test", "dob": "1988-08-30", "tob": "20:18",
            "place": "Sehore", "latitude": "23.2032", "longitude": "77.0856",
            "timezone": "Asia/Kolkata",
        }, "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Sehore", result.stdout)

    def test_missing_place_is_rejected_not_defaulted(self):
        """V1 silently defaulted a missing place to Delhi."""
        result = self.write_and_run({
            "name": "Test", "dob": "1988-08-30", "tob": "20:18",
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("JYOTISH CHART", result.stdout)

    def test_english_planet_names_still_accepted(self):
        result = self.write_and_run({
            "name": "Test", "dob": "1990-06-15", "tob": "06:30",
            "place": "Delhi",
            "positions": {"Ascendant": "Gemini 12 40", "Sun": "Taurus 0 55",
                          "Moon": "Pisces 21 10"},
        }, "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class EngineImportTest(unittest.TestCase):
    """The application must stay dependency-free."""

    def test_no_module_imports_swisseph(self):
        offenders = []
        for folder, _dirs, files in os.walk(os.path.join(ROOT, "engine")):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as handle:
                    body = handle.read()
                if "import swisseph" in body:
                    offenders.append(path)
        with open(os.path.join(ROOT, "main.py"), encoding="utf-8") as handle:
            if "import swisseph" in handle.read():
                offenders.append("main.py")
        self.assertEqual(offenders, [],
                         "the application must not depend on Swiss Ephemeris")

    def test_engine_uses_only_the_standard_library(self):
        """A crude but effective check on third-party imports."""
        allowed_prefixes = ("engine", "tests", ".")
        third_party = []
        for folder, _dirs, files in os.walk(os.path.join(ROOT, "engine")):
            for name in files:
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(folder, name), encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line.startswith(("import ", "from ")):
                            continue
                        module = line.split()[1].split(".")[0]
                        if module in ("numpy", "scipy", "pandas", "swisseph",
                                      "pyswisseph", "requests", "pytz"):
                            third_party.append(f"{name}: {line}")
        self.assertEqual(third_party, [])

    def test_backwards_compatible_helpers_still_exist(self):
        from engine.fal import detect_yogas, generate_fal_report
        from engine.planets import COMBUSTION_ORB
        from engine.vargas import VARGA_FUNCTIONS, compute_all_vargas
        self.assertTrue(callable(detect_yogas))
        self.assertTrue(callable(generate_fal_report))
        self.assertTrue(callable(compute_all_vargas))
        self.assertEqual(len(VARGA_FUNCTIONS), 16)
        self.assertEqual(COMBUSTION_ORB["Budha"], 14.0)


# ── V1.5 Part 26: the synthesis flags ────────────────────────────────────────

class SynthesisCLITest(unittest.TestCase):
    """
    The new flags exist, default to off, and do not disturb natal output.
    """

    @classmethod
    def setUpClass(cls):
        """
        Read the real parser's `--help`, not the source of the function that
        builds it. The profile choices are computed from the enum, so they do
        not appear as literals anywhere in the source — a source-text check
        passes or fails for reasons unrelated to what the CLI accepts.
        """
        cls.help = subprocess.run(
            [sys.executable, "main.py", "--help"],
            cwd=ROOT, capture_output=True, text=True,
            env={**os.environ, "COLUMNS": "200"}).stdout

    def test_every_part_26_flag_is_offered(self):
        for flag in ("--synthesis", "--synthesis-profile", "--domain",
                     "--prediction-json"):
            with self.subTest(flag=flag):
                self.assertIn(flag, self.help)

    def test_synthesis_is_off_by_default(self):
        """
        Part 26: normal natal output must not start producing predictions
        because a release added the capability.
        """
        import main
        args = main.parse_args_from([
            "--name", "T", "--dob", "1988-08-30", "--time", "20:18",
            "--place", "Jaipur"])
        self.assertIsNone(args.synthesis)
        self.assertIsNone(args.prediction_json)
        self.assertIsNone(args.domain)
        self.assertEqual(args.synthesis_profile, "standard")

    def test_profile_choices_match_the_enum(self):
        import main
        from engine.synthesis import SynthesisProfile
        for profile in SynthesisProfile:
            with self.subTest(profile=profile.value):
                args = main.parse_args_from([
                    "--name", "T", "--dob", "1988-08-30", "--time", "20:18",
                    "--place", "Jaipur", "--synthesis", "2026-01-01",
                    "--synthesis-profile", profile.value])
                self.assertEqual(args.synthesis_profile, profile.value)

    def test_an_unknown_profile_is_rejected(self):
        result = subprocess.run(
            [sys.executable, "main.py", "--name", "T", "--dob", "1988-08-30",
             "--time", "20:18", "--place", "Jaipur",
             "--synthesis", "2026-01-01", "--synthesis-profile", "psychic"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_bare_date_is_read_as_midday(self):
        """
        Midnight sits on a day boundary, where a reader is most likely to be
        surprised by which side of an ingress the answer fell.
        """
        import datetime

        import main
        self.assertEqual(main._parse_synthesis_date("2026-09-27"),
                         datetime.datetime(2026, 9, 27, 12, 0))
        self.assertEqual(main._parse_synthesis_date("2026-09-27T08:30"),
                         datetime.datetime(2026, 9, 27, 8, 30))
        self.assertIsNone(main._parse_synthesis_date("not a date"))


class InterpretationCLITest(unittest.TestCase):
    """V1.6 Part 27: the interpretation flags."""

    @classmethod
    def setUpClass(cls):
        cls.help = subprocess.run(
            [sys.executable, "main.py", "--help"],
            cwd=ROOT, capture_output=True, text=True,
            env={**os.environ, "COLUMNS": "200"}).stdout

    def test_every_part_27_flag_is_offered(self):
        for flag in ("--interpret", "--interpret-profile", "--report-mode",
                     "--language", "--interpretation-json"):
            with self.subTest(flag=flag):
                self.assertIn(flag, self.help)

    def test_interpretation_is_off_by_default(self):
        import main
        args = main.parse_args_from([
            "--name", "T", "--dob", "1988-08-30", "--time", "20:18",
            "--place", "Jaipur"])
        self.assertIsNone(args.interpret)
        self.assertIsNone(args.interpretation_json)
        self.assertEqual(args.language, "en")
        self.assertEqual(args.report_mode, "detailed")

    def test_report_mode_choices_match_the_enum(self):
        import main
        from engine.interpretation import ReportMode
        for mode in ReportMode:
            with self.subTest(mode=mode.value):
                args = main.parse_args_from([
                    "--name", "T", "--dob", "1988-08-30", "--time", "20:18",
                    "--place", "Jaipur", "--interpret", "2026-01-01",
                    "--report-mode", mode.value])
                self.assertEqual(args.report_mode, mode.value)

    def test_an_unknown_report_mode_is_rejected(self):
        result = subprocess.run(
            [sys.executable, "main.py", "--name", "T", "--dob", "1988-08-30",
             "--time", "20:18", "--place", "Jaipur",
             "--interpret", "2026-01-01", "--report-mode", "poetic"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_interpret_implies_synthesis(self):
        """
        An interpretation is a rendering of a synthesis, so asking for the
        first without the second is an oversight rather than a preference.
        """
        import main
        args = main.parse_args_from([
            "--name", "T", "--dob", "1988-08-30", "--time", "20:18",
            "--place", "Jaipur", "--interpret", "2026-09-27"])
        self.assertIsNone(args.synthesis)
        # build_report fills it in; the parser deliberately does not, so the
        # two flags stay independently inspectable.
        self.assertEqual(args.interpret, "2026-09-27")

    def test_english_is_available_and_complete(self):
        from engine.interpretation import available_languages, completeness_report
        self.assertIn("en", available_languages())
        self.assertTrue(completeness_report("en")["complete"])


class DomainReportDocumentTest(unittest.TestCase):
    """V1.6 Part 8."""

    def test_generator_runs_and_reports_coverage(self):
        result = subprocess.run(
            [sys.executable, "tools/generate_domain_report.py"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# DOMAIN_VALIDATION.md", result.stdout)
        self.assertIn("## Domain by domain", result.stdout)


class RuleAuditDocumentTest(unittest.TestCase):
    """The Part 2 change log is generated, so it cannot drift."""

    def test_generator_runs_and_reports_the_findings(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/generate_rule_audit.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for heading in ("## Changed rules", "## Read and absent",
                        "## Conflicts", "## Profile sizes",
                        "## The four claims, kept separate"):
            with self.subTest(heading=heading):
                self.assertIn(heading, result.stdout)

    def test_change_log_records_every_part_2_field(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/generate_rule_audit.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True)
        for field in ("**rule_id**", "**old software condition**",
                      "**textual / source condition**",
                      "**difference found**", "**new software condition**",
                      "**source refs**",
                      "**affected regression charts**",
                      "**reason for change**"):
            with self.subTest(field=field):
                self.assertIn(field, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
