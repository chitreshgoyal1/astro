"""
Release plumbing (V1.8 Parts 23-35, 39, 46, 47, 48)
-----------------------------------------------------
The parts of a release candidate that are not astrology: versions,
storage, settings separation, diagnostics, the frozen service surface,
accessibility and the architecture boundary.

WHY THESE ARE TESTED AT ALL

    Every one of them is a promise the application makes about itself.
    "Nothing leaves this machine", "presentation cannot change a
    calculation", "a saved file from the last release still opens",
    "there is one version source" — each is checkable, and a promise
    that is not checked is a promise that drifts.

    The version one is the clearest case. V1.8 found the PDF writer
    stamping "V1.7" into every document it produced, months after the
    application version had moved on, because the string was a literal
    in a file nobody had reason to open.
"""

import ast
import datetime
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.diagnostics import (
    Diagnostics, PERSONAL_FIELDS, REDACTED, crash_report,
    format_crash_notice, redact, write_crash_report,
)
from app.models import (
    ApplicationSettings, ConsultationRecord, ReportPreferences,
)
from app.services import (
    RELEASE_DEFAULTS, describe_storage, release_audit, release_settings,
    release_warnings, versions,
)
from app.services.selfcheck import CHECKS, run_selfcheck
from app.services.version_service import engine_versions
from app.storage import DEFAULTS_BY_SCHEMA, from_dict, save
from app.version import APPLICATION_VERSION, CONSULTATION_SCHEMA_VERSION


# ── Part 31: one version source ─────────────────────────────────────────────

class VersionTest(unittest.TestCase):

    def test_the_application_version_has_one_definition(self):
        """
        `app.models` re-exports it; nothing else may define it. A second
        definition is how the PDF writer came to say V1.7 in a V1.8
        build.
        """
        definitions = []
        for base, directories, files in os.walk(ROOT):
            directories[:] = [d for d in directories
                              if d not in ("__pycache__", ".venv", "dist",
                                           ".git", "tests")]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(base, name)
                with open(path, encoding="utf-8") as handle:
                    tree = ast.parse(handle.read(), filename=path)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Assign):
                        continue
                    for target in node.targets:
                        if (isinstance(target, ast.Name)
                                and target.id == "APPLICATION_VERSION"
                                and isinstance(node.value, ast.Constant)):
                            definitions.append(
                                os.path.relpath(path, ROOT))
        self.assertEqual(definitions, ["app/version.py"])

    def test_no_release_name_is_hard_coded_in_a_producer_string(self):
        """
        The specific defect: a version literal inside a string that ends
        up in a document.
        """
        for module in ("app/report/pdf.py", "app/report/html_report.py",
                       "app/report/builder.py"):
            path = os.path.join(ROOT, module)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as handle:
                body = handle.read()
            with self.subTest(module=module):
                for stale in ("V1.5", "V1.6", "V1.7", "V1.8"):
                    self.assertNotIn(f"Engine {stale}", body)

    def test_every_version_is_reported_together(self):
        data = versions()
        for key in ("application", "release", "consultation_schema",
                    "chart_schema", "prediction_schema",
                    "interpretation_schema", "source_registry"):
            with self.subTest(key=key):
                self.assertTrue(data.get(key))

    def test_the_application_module_reaches_no_engine_module(self):
        """
        `app.version` is imported by the PDF writer, which may not reach
        the engine. The engine versions therefore live in a service.
        """
        path = os.path.join(ROOT, "app", "version.py")
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                self.assertFalse(name == "engine"
                                 or name.startswith("engine."))

    def test_the_pdf_stamps_the_current_release(self):
        from app.report.pdf import render_pdf
        from app.version import RELEASE_NAME

        data = render_pdf({"title": "t", "generated": "", "sections": [
            {"id": "s", "title": "S",
             "blocks": [{"block": "paragraph", "text": "x"}]}]})
        self.assertIn(RELEASE_NAME.encode("latin-1"), data)


# ── Part 32: reproducibility ────────────────────────────────────────────────

class ReproducibilityTest(unittest.TestCase):

    def test_the_block_carries_calculation_settings_and_not_presentation(self):
        from app.services import reproducibility_block

        block = reproducibility_block(
            ApplicationSettings(language="hi"), moment="2026-09-27")
        self.assertIn("calculation_settings", block)
        self.assertIn("ayanamsha", block["calculation_settings"])
        self.assertNotIn("language", block["calculation_settings"])
        self.assertEqual(block["target_datetime"], "2026-09-27")

    def test_the_block_names_every_version_needed_to_reproduce(self):
        from app.services import reproducibility_block

        block = reproducibility_block(ApplicationSettings())
        for key in ("application", "chart_schema", "prediction_schema",
                    "source_registry", "varga_algorithm"):
            with self.subTest(key=key):
                self.assertIn(key, block)


# ── Part 27: calculation and presentation ───────────────────────────────────

class SettingsSeparationTest(unittest.TestCase):

    def test_every_field_is_classified_as_one_or_the_other(self):
        fields = set(ApplicationSettings.__dataclass_fields__)
        classified = (set(ApplicationSettings.CALCULATION_FIELDS)
                      | set(ApplicationSettings.PRESENTATION_FIELDS))
        self.assertEqual(fields, classified,
                         "a new setting must be classified deliberately")

    def test_the_two_sets_do_not_overlap(self):
        self.assertFalse(
            set(ApplicationSettings.CALCULATION_FIELDS)
            & set(ApplicationSettings.PRESENTATION_FIELDS))

    def test_a_presentation_change_cannot_move_a_calculation(self):
        """
        The claim, tested rather than asserted: two settings differing
        only in a presentation field produce the same calculation block,
        and therefore the same cache key and the same reproducibility
        record.
        """
        english = ApplicationSettings(language="en")
        hindi = ApplicationSettings(language="hi")
        self.assertNotEqual(english.language, hindi.language)
        self.assertEqual(english.calculation_settings(),
                         hindi.calculation_settings())

    def test_a_chart_is_identical_across_presentation_settings(self):
        from app.services import calculate_chart

        snapshots = []
        for language in ("en", "hi"):
            for style in ("north_indian", "south_indian"):
                record = ConsultationRecord(
                    name="P", date_of_birth="1988-08-30",
                    time_of_birth="20:18", place="Jaipur",
                    settings=ApplicationSettings(language=language),
                    report=ReportPreferences(chart_style=style))
                natal = calculate_chart(record, record.settings)
                payload = dict(natal.snapshot)
                payload.pop("generated", None)
                snapshots.append(json.dumps(payload, sort_keys=True,
                                            default=str))
        self.assertEqual(len(set(snapshots)), 1)


# ── Parts 23, 24: the saved format ──────────────────────────────────────────

class SavedFormatTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def test_a_saved_file_preserves_everything_part_23_lists(self):
        record = ConsultationRecord(
            name="Saved", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur",
            settings=ApplicationSettings(ayanamsha="raman",
                                         house_system="sripati",
                                         rule_profile="parashari_strict",
                                         language="hi"),
            report=ReportPreferences(chart_style="south_indian",
                                     mode="technical", language="hi"))
        path = save(record, os.path.join(self.directory, "c.json"))
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["schema_version"],
                         CONSULTATION_SCHEMA_VERSION)
        self.assertEqual(payload["application_version"], APPLICATION_VERSION)
        self.assertTrue(payload["created"])
        self.assertEqual(payload["input"]["birth_time_precision"],
                         "EXACT_TO_MINUTE")
        self.assertEqual(payload["calculation"]["ayanamsha"], "raman")
        self.assertEqual(payload["calculation"]["house_system"], "sripati")
        self.assertEqual(payload["calculation"]["rule_profile"],
                         "parashari_strict")
        self.assertEqual(payload["presentation"]["language"], "hi")
        self.assertEqual(payload["presentation"]["chart_style"],
                         "south_indian")

    def test_the_report_language_is_the_one_recorded(self):
        """
        `language` lives on two objects. Which one a saved file records
        is a decision, and an unstated decision is a dict-merge
        accident waiting to change when somebody reorders the merge.
        """
        record = ConsultationRecord(
            name="L", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur",
            settings=ApplicationSettings(language="en"),
            report=ReportPreferences(language="hi"))
        self.assertEqual(record.language_in_effect, "hi")
        self.assertEqual(record.to_dict()["presentation"]["language"], "hi")

    def test_the_two_blocks_hold_what_they_say_they_hold(self):
        record = ConsultationRecord(
            name="S", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur")
        path = save(record, os.path.join(self.directory, "s.json"))
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(set(payload["calculation"]),
                         set(ApplicationSettings.CALCULATION_FIELDS))
        for field in ApplicationSettings.CALCULATION_FIELDS:
            self.assertNotIn(field, payload["presentation"])

    def test_a_cache_is_absent_unless_asked_for(self):
        record = ConsultationRecord(
            name="S", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur")
        path = save(record, os.path.join(self.directory, "n.json"))
        with open(path, encoding="utf-8") as handle:
            self.assertNotIn("cached", json.load(handle))
        self.assertLess(os.path.getsize(path), 4096,
                        "input and methodology should be small")

    def test_no_mutable_global_default_is_written_as_state(self):
        """
        Part 23: "Do not save mutable global defaults as implicit state."
        Every value in the saved blocks comes from the record, so two
        saves of the same record are identical apart from the timestamp.
        """
        record = ConsultationRecord(
            name="S", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur", created="2026-01-01T00:00:00")
        first = save(record, os.path.join(self.directory, "a.json"))
        second = save(record, os.path.join(self.directory, "b.json"))
        with open(first, encoding="utf-8") as handle:
            one = handle.read()
        with open(second, encoding="utf-8") as handle:
            two = handle.read()
        self.assertEqual(one, two)


class MigrationTest(unittest.TestCase):

    LEGACY = {
        "schema_version": "1.0.0",
        "application_version": "1.7.0",
        "created": "2026-01-01T00:00:00",
        "input": {"name": "Legacy", "date_of_birth": "1988-08-30",
                  "time_of_birth": "20:18", "place": "Jaipur",
                  "birth_time_precision": "EXACT_TO_MINUTE"},
        "settings": {"ayanamsha": "raman", "language": "hi",
                     "unknown_future_flag": 7},
        "report": {"mode": "summary"},
    }

    def test_a_v1_file_migrates_to_v2(self):
        record, report = from_dict(json.loads(json.dumps(self.LEGACY)))
        self.assertEqual(report["read_schema"], "1.0.0")
        self.assertEqual(report["current_schema"], "2.0.0")
        self.assertEqual([(s["from"], s["to"]) for s in report["migrations"]],
                         [("1.0.0", "2.0.0")])

    def test_the_migration_changes_no_saved_value(self):
        record, _report = from_dict(json.loads(json.dumps(self.LEGACY)))
        self.assertEqual(record.settings.ayanamsha, "raman")
        self.assertEqual(record.settings.language, "hi")
        self.assertEqual(record.report.mode, "summary")

    def test_an_unknown_setting_is_kept_and_reported(self):
        """
        Part 24. Dropping a key this build does not understand silently
        converts it to a default; keeping it means a build that does
        understand it can still read the file.
        """
        _record, report = from_dict(json.loads(json.dumps(self.LEGACY)))
        self.assertTrue(any("unknown_future_flag" in note
                            for note in report["migration_notes"]))

    def test_the_migration_is_deterministic(self):
        from app.storage import _migrate_1_to_2

        first_report = {"migrations": [], "migration_notes": []}
        second_report = {"migrations": [], "migration_notes": []}
        first = _migrate_1_to_2(json.loads(json.dumps(self.LEGACY)),
                                first_report)
        second = _migrate_1_to_2(json.loads(json.dumps(self.LEGACY)),
                                 second_report)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_the_migration_consults_no_current_default(self):
        """
        A migration that read today's defaults would re-methodologise
        yesterday's chart. Checked structurally: the function's source
        names no settings object.
        """
        import inspect

        from app.storage import _migrate_1_to_2

        source = inspect.getsource(_migrate_1_to_2)
        self.assertNotIn("ApplicationSettings()", source)
        self.assertNotIn("RELEASE_DEFAULTS", source)

    def test_gaps_are_filled_from_the_file_s_own_era(self):
        payload = json.loads(json.dumps(self.LEGACY))
        record, report = from_dict(payload)
        self.assertIn("1.0.0", DEFAULTS_BY_SCHEMA)
        self.assertTrue(any("defaults in force when it was written" in note
                            for note in report["migration_notes"]))

    def test_every_shipped_schema_has_a_recorded_default_set(self):
        self.assertIn(CONSULTATION_SCHEMA_VERSION, DEFAULTS_BY_SCHEMA)


# ── Parts 28, 29, 30: privacy and diagnostics ───────────────────────────────

class DiagnosticsTest(unittest.TestCase):

    def test_personal_fields_are_redacted_by_default(self):
        stream = io.StringIO()
        log = Diagnostics(stream=stream)
        log.info("chart", name="Someone", place="Jaipur", ayanamsha="lahiri")
        record = json.loads(stream.getvalue())
        self.assertEqual(record["name"], REDACTED)
        self.assertEqual(record["place"], REDACTED)
        self.assertEqual(record["ayanamsha"], "lahiri")
        self.assertTrue(record["redacted"])

    def test_redaction_replaces_rather_than_deletes(self):
        """
        A reader debugging a missing field must be able to tell "absent"
        from "hidden".
        """
        out = redact({"name": "X", "place": "Y"})
        self.assertEqual(set(out), {"name", "place"})

    def test_redaction_reaches_nested_structures(self):
        out = redact({"birth": {"name": "X", "nested": [{"place": "Y"}]}})
        self.assertEqual(out["birth"]["name"], REDACTED)
        self.assertEqual(out["birth"]["nested"][0]["place"], REDACTED)

    def test_debug_mode_says_that_it_is_debug_mode(self):
        stream = io.StringIO()
        Diagnostics(stream=stream, debug=True).info("chart", name="Someone")
        record = json.loads(stream.getvalue())
        self.assertEqual(record["name"], "Someone")
        self.assertFalse(record["redacted"])

    def test_the_default_logger_writes_nowhere(self):
        from app.diagnostics import NULL

        NULL.info("event", name="X")
        self.assertIsNone(NULL.stream)

    def test_a_migration_with_assumptions_logs_at_warning(self):
        log = Diagnostics()
        quiet = log.migration({"read_schema": "2.0.0", "migrations": [],
                               "migration_notes": []})
        loud = log.migration({"read_schema": "1.0.0", "migrations": [],
                              "migration_notes": ["filled a gap"]})
        self.assertEqual(quiet["level"], "info")
        self.assertEqual(loud["level"], "warning")

    def test_every_personal_field_name_is_covered(self):
        record = ConsultationRecord(
            name="N", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="P").to_dict()
        for key in record["input"]:
            if key in ("birth_time_precision", "entered_positions",
                       "timezone", "utc_offset"):
                continue
            with self.subTest(field=key):
                self.assertIn(key, PERSONAL_FIELDS)


class CrashReportTest(unittest.TestCase):

    def _report(self, debug: bool = False) -> dict:
        try:
            raise ValueError("something failed")
        except ValueError as exc:
            return crash_report(
                exc, operation="test", settings=ApplicationSettings(),
                versions=versions(), debug=debug,
                context={"name": "Someone", "domain": "CAREER"})

    def test_a_crash_report_carries_the_stack_and_the_build(self):
        report = self._report()
        self.assertTrue(report["traceback"])
        self.assertEqual(report["error_type"], "ValueError")
        self.assertEqual(report["versions"]["application"],
                         APPLICATION_VERSION)
        self.assertIn("ayanamsha", report["methodology"])

    def test_a_crash_report_excludes_personal_data_by_default(self):
        report = self._report()
        self.assertFalse(report["personal_data_included"])
        self.assertEqual(report["context"]["name"], REDACTED)
        self.assertEqual(report["context"]["domain"], "CAREER")

    def test_debug_mode_includes_it_and_marks_the_report(self):
        report = self._report(debug=True)
        self.assertTrue(report["personal_data_included"])
        self.assertEqual(report["context"]["name"], "Someone")

    def test_the_notice_shown_to_a_user_contains_no_traceback(self):
        report = self._report()
        notice = format_crash_notice(report, "/tmp/x.json")
        self.assertNotIn("Traceback", notice)
        self.assertNotIn("File \"", notice)
        self.assertIn(report["report_id"], notice)

    def test_a_crash_report_can_be_written_and_read_back(self):
        report = self._report()
        directory = tempfile.mkdtemp()
        path = write_crash_report(report, directory)
        self.assertTrue(path)
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["report_id"],
                             report["report_id"])


class PrivacyTest(unittest.TestCase):

    def test_the_privacy_statement_answers_part_28s_three_questions(self):
        record = describe_storage()
        for key in ("what_is_stored", "where", "what_leaves_the_machine"):
            with self.subTest(key=key):
                self.assertTrue(record[key])

    def test_nothing_leaves_the_machine_is_stated_plainly(self):
        blob = json.dumps(describe_storage())
        self.assertIn("Nothing", blob)
        self.assertIn("127.0.0.1", blob)


# ── Part 48: release mode ───────────────────────────────────────────────────

class ReleaseModeTest(unittest.TestCase):

    def test_the_release_defaults_match_the_shipped_defaults(self):
        """
        They should agree. The assertion exists so that a divergence is
        argued about in a diff rather than shipped.
        """
        shipped = ApplicationSettings()
        for name, value in RELEASE_DEFAULTS.items():
            with self.subTest(setting=name):
                self.assertEqual(getattr(shipped, name), value)

    def test_the_defaults_produce_no_warning(self):
        audit = release_audit(release_settings())
        self.assertTrue(audit["is_release_default"])
        self.assertEqual(audit["warnings"], [])

    def test_an_experimental_profile_is_named_as_experimental(self):
        audit = release_audit(
            ApplicationSettings(synthesis_profile="experimental"))
        self.assertEqual(audit["experimental_count"], 1)
        self.assertIn("no located witness", audit["warnings"][0])

    def test_unverified_reductions_stay_off_and_announce_themselves(self):
        self.assertFalse(ApplicationSettings().ashtakavarga_reductions)
        audit = release_audit(
            ApplicationSettings(ashtakavarga_reductions=True))
        self.assertEqual(audit["departures"][0]["classification"],
                         "unverified")

    def test_the_strict_profile_is_not_called_experimental(self):
        audit = release_audit(ApplicationSettings(
            synthesis_profile="strict"))
        self.assertEqual(audit["experimental_count"], 0)

    def test_a_document_built_under_an_experiment_says_so(self):
        from app.services import calculate_chart, generate_report

        settings = ApplicationSettings(synthesis_profile="experimental")
        record = ConsultationRecord(
            name="E", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur", settings=settings)
        natal = calculate_chart(record, settings)
        document = generate_report(
            record, settings, ReportPreferences(mode="summary"),
            natal=natal).to_dict()
        self.assertIn("no located witness", json.dumps(document))

    def test_release_mode_removes_no_option(self):
        """
        The design decision, pinned. Unverified rules stay available and
        stay labelled; hiding them would push a practitioner to a fork
        and lose the labelling with them.
        """
        from app.services import available_options

        profiles = available_options()["synthesis_profile"]["values"]
        self.assertIn("experimental", profiles)


# ── Part 35: the self-check ─────────────────────────────────────────────────

class SelfCheckTest(unittest.TestCase):

    def test_this_installation_passes(self):
        report = run_selfcheck()
        failures = [r for r in report["checks"] if r["status"] != "ok"]
        self.assertEqual(failures, [], f"self-check failed: {failures}")

    def test_a_failing_check_does_not_raise(self):
        def explodes():
            raise RuntimeError("boom")

        report = run_selfcheck([explodes])
        self.assertFalse(report["ok"])
        self.assertIn("boom", report["checks"][0]["detail"])

    def test_the_report_says_what_a_pass_does_not_mean(self):
        report = run_selfcheck()
        self.assertIn("does not mean a calculation is wrong", report["note"])
        self.assertIn("a pass does not mean one is right", report["note"])

    def test_it_is_not_the_test_suite(self):
        """
        Part 35: "Do not run the entire test suite at application
        startup." Checked by cost: the whole self-check must be far
        cheaper than the suite it must not become.
        """
        import time

        start = time.perf_counter()
        run_selfcheck()
        self.assertLess(time.perf_counter() - start, 5.0)

    def test_every_check_is_registered(self):
        self.assertGreaterEqual(len(CHECKS), 8)
        report = run_selfcheck()
        self.assertEqual(len(report["checks"]), len(CHECKS))


# ── Part 39: the frozen service surface ─────────────────────────────────────

class ServiceSurfaceTest(unittest.TestCase):
    """
    Part 39: "Identify which application service interfaces become stable
    for V1."

    The list below IS that decision. A name added to `app.services`
    without being added here is a name that was published by accident;
    a name removed from `app.services` that is still here is a breaking
    change somebody has to justify.
    """

    FROZEN = {
        # calculation
        "calculate_chart", "calculate_prediction", "chart_visual_model",
        "render_interpretation", "timeline_candidates",
        # reports
        "generate_report", "generate_pdf", "generate_html",
        # persistence
        "load_consultation", "save_consultation",
        "export_consultations", "import_consultations",
        # settings and methodology
        "available_options", "validate_settings", "describe_methodology",
        # identity and policy
        "versions", "engine_versions", "reproducibility_block",
        "describe_storage", "release_settings", "release_audit",
        "release_warnings", "describe_options", "RELEASE_DEFAULTS",
    }

    def test_the_public_surface_is_exactly_the_frozen_list(self):
        import app.services as services

        self.assertEqual(set(services.__all__), self.FROZEN)

    def test_every_frozen_name_exists_and_is_callable_or_data(self):
        import app.services as services

        for name in sorted(self.FROZEN):
            with self.subTest(name=name):
                self.assertTrue(hasattr(services, name))

    def test_no_engine_class_is_re_exported(self):
        """
        Part 39: "Avoid exposing internal engine classes unnecessarily."
        A caller who receives an engine object is a caller coupled to the
        engine's internals, and the boundary stops meaning anything.
        """
        import app.services as services

        for name in sorted(self.FROZEN):
            value = getattr(services, name)
            module = getattr(value, "__module__", "") or ""
            with self.subTest(name=name):
                self.assertFalse(module.startswith("engine."),
                                 f"{name} is an engine object")


# ── Part 47: the boundary, re-audited ───────────────────────────────────────

class BoundaryReAuditTest(unittest.TestCase):

    FORBIDDEN = ("app/ui", "app/report", "app/visual")

    #: Words that would mean astrology logic had moved below the boundary.
    ASTROLOGY_MARKERS = (
        "shadbala_ratio", "houses_owned_by", "varga_house_of",
        "vimshottari", "dispositor", "graha_drishti", "exaltation",
        "moolatrikona",
    )

    def test_no_presentation_module_imports_the_engine(self):
        for package in self.FORBIDDEN:
            directory = os.path.join(ROOT, package)
            for name in sorted(os.listdir(directory)):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(directory, name)
                with open(path, encoding="utf-8") as handle:
                    tree = ast.parse(handle.read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [a.name for a in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    for module in names:
                        with self.subTest(file=f"{package}/{name}"):
                            self.assertFalse(
                                module == "engine"
                                or module.startswith("engine."))

    def test_no_presentation_module_computes_an_astrological_fact(self):
        """
        The stronger form of the boundary. An import test catches the
        obvious violation; this catches the one where somebody copied a
        rule rather than importing it.
        """
        for package in self.FORBIDDEN:
            directory = os.path.join(ROOT, package)
            for name in sorted(os.listdir(directory)):
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(directory, name),
                          encoding="utf-8") as handle:
                    body = handle.read()
                # Comments and docstrings legitimately discuss astrology;
                # only executable lines are searched.
                code = "\n".join(
                    line for line in body.splitlines()
                    if not line.lstrip().startswith("#"))
                for marker in self.ASTROLOGY_MARKERS:
                    with self.subTest(file=f"{package}/{name}",
                                      marker=marker):
                        self.assertNotIn(f"{marker}(", code)

    def test_the_new_v18_modules_are_covered_by_the_audit(self):
        """
        V1.8 added six modules under the boundary. A boundary test that
        enumerates files it was written against would not have seen them.
        """
        for module in ("app/visual/south_indian.py", "app/visual/styles.py",
                       "app/report/opentype.py", "app/report/otlayout.py",
                       "app/report/devanagari.py", "app/report/embed.py",
                       "app/report/strings.py"):
            with self.subTest(module=module):
                self.assertTrue(os.path.exists(os.path.join(ROOT, module)))


# ── Part 46: accessibility ──────────────────────────────────────────────────

class AccessibilityTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from app.services import calculate_chart, chart_visual_model
        from app.visual import render_chart, scene_to_svg_document

        record = ConsultationRecord(
            name="A11y", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur")
        cls.natal = calculate_chart(record, record.settings)
        cls.svgs = {
            style: scene_to_svg_document(render_chart(
                chart_visual_model(cls.natal, style=style)))
            for style in ("north_indian", "south_indian")}

    def test_every_chart_carries_a_text_equivalent(self):
        for style, svg in self.svgs.items():
            with self.subTest(style=style):
                self.assertIn("<title", svg)
                self.assertIn("<desc", svg)
                self.assertIn('role="img"', svg)
                self.assertIn("aria-labelledby", svg)

    def test_the_text_equivalent_names_every_graha(self):
        from app.services import chart_visual_model
        from app.visual import describe

        model = chart_visual_model(self.natal)
        description = describe(model)
        for body in model.bodies():
            if body.is_lagna:
                continue
            with self.subTest(body=body.name):
                self.assertIn(body.name, description)

    def test_no_status_is_carried_by_colour_alone(self):
        """
        Part 46 and V1.7 Part 36. Retrograde, combustion and dignity are
        printed markers; the Lagna is a label AND a weight AND a colour.
        Removing every colour must lose nothing.
        """
        from app.services import chart_visual_model
        from app.visual import render_chart

        for style in ("north_indian", "south_indian"):
            model = chart_visual_model(self.natal, style=style,
                                       detail="DETAILED")
            scene = render_chart(model)
            labels = " ".join(
                element.text for element in scene.elements
                if type(element).__name__ == "Text")
            with self.subTest(style=style):
                self.assertIn("R", labels)
                self.assertTrue(any(
                    marker in labels
                    for marker in ("^", "v", "mt", "sv")))

    def test_the_svg_scales_without_a_fixed_pixel_size(self):
        for style, svg in self.svgs.items():
            with self.subTest(style=style):
                self.assertIn("viewBox", svg)
                self.assertNotIn('width="420px"', svg)

    def test_every_form_control_has_a_label(self):
        from app.services import available_options
        from app.ui import pages

        markup = pages.consultation_form(available_options(), {})
        ids = set()
        for chunk in markup.split('id="')[1:]:
            ids.add(chunk.split('"')[0])
        for chunk in markup.split('for="')[1:]:
            with self.subTest(control=chunk.split('"')[0]):
                self.assertIn(chunk.split('"')[0], ids)

    def test_the_interface_declares_a_language(self):
        from app.ui import pages

        markup = pages.page("T", "body", subject="")
        self.assertIn("<html", markup)
        self.assertIn("lang=", markup)

    def test_focus_is_visible(self):
        from app.ui.assets import STYLESHEET

        self.assertIn(":focus", STYLESHEET)
        self.assertIn("outline", STYLESHEET)


if __name__ == "__main__":
    unittest.main()
