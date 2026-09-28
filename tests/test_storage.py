"""
Saved consultations and migration (V1.7 Parts 31, 32, 37)
===========================================================
What a saved file holds, what it refuses to guess, and what it says when
the world has moved under it.

THE RULE THESE TESTS EXIST FOR

    A changed default must never move a saved chart without saying so.

    That is the whole of Part 32 in one sentence, and it is easy to break:
    the natural way to read an old file is to fill its gaps from today's
    defaults, and the chart then silently becomes a different chart. So
    gaps are filled from the defaults IN FORCE WHEN THE FILE WAS WRITTEN,
    and `DEFAULTS_BY_SCHEMA` is frozen history that later releases append
    to and never edit.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import storage
from app.errors import StorageError
from app.models import (
    APPLICATION_VERSION, CONSULTATION_SCHEMA_VERSION, ApplicationSettings,
    BirthTimePrecision, ConsultationRecord, ReportPreferences,
)
from app.services import calculate_chart

JAIPUR = dict(name="Jaipur 1988", date_of_birth="1988-08-30",
              time_of_birth="20:18", place="Jaipur")


class _Temp(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def path(self, name: str = "consultation.json") -> str:
        return os.path.join(self.directory.name, name)


# ── Part 31: save and load ───────────────────────────────────────────────────

class RoundTripTest(_Temp):

    def test_a_saved_consultation_reloads_unchanged(self):
        record = ConsultationRecord(
            **JAIPUR, precision=BirthTimePrecision.APPROX_5_MIN,
            settings=ApplicationSettings(ayanamsha="raman", node="mean"),
            report=ReportPreferences(mode="technical", language="hi"),
            notes="a note")
        storage.save(record, self.path())
        loaded, report = storage.load(self.path())

        self.assertEqual(loaded.name, record.name)
        self.assertEqual(loaded.date_of_birth, record.date_of_birth)
        self.assertEqual(loaded.time_of_birth, record.time_of_birth)
        self.assertEqual(loaded.place, record.place)
        self.assertIs(loaded.precision, BirthTimePrecision.APPROX_5_MIN)
        self.assertEqual(loaded.settings.ayanamsha, "raman")
        self.assertEqual(loaded.settings.node, "mean")
        self.assertEqual(loaded.report.mode, "technical")
        self.assertEqual(loaded.report.language, "hi")
        self.assertEqual(loaded.notes, "a note")
        self.assertEqual(report["migration_notes"], [])

    def test_the_input_alone_is_sufficient_to_recompute(self):
        """
        Part 31. A file that needed its cache to produce a chart would be
        a file that preserves a stale answer rather than a consultation.
        """
        storage.save(ConsultationRecord(**JAIPUR), self.path())
        with open(self.path(), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertNotIn("cached", payload)

        loaded, _ = storage.load(self.path())
        natal = calculate_chart(loaded)
        self.assertTrue(natal.snapshot["lagna"])

    def test_a_cached_calculation_is_optional_and_marked_as_such(self):
        record = ConsultationRecord(**JAIPUR)
        natal = calculate_chart(record)
        storage.save(record, self.path(), snapshot=natal.snapshot)
        with open(self.path(), encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["cached"]["chart_schema"], "1.2.0")
        self.assertIn("authoritative", payload["cached"]["note"])
        _, report = storage.load(self.path())
        self.assertTrue(report["cached"])

    def test_the_file_records_both_versions(self):
        storage.save(ConsultationRecord(**JAIPUR), self.path())
        with open(self.path(), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["schema_version"],
                         CONSULTATION_SCHEMA_VERSION)
        self.assertEqual(payload["application_version"], APPLICATION_VERSION)

    def test_storage_is_local_and_needs_no_network(self):
        import socket
        real = socket.socket
        socket.socket = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("storage must not open a socket"))
        try:
            storage.save(ConsultationRecord(**JAIPUR), self.path())
            storage.load(self.path())
        finally:
            socket.socket = real

    def test_an_unwritable_path_reports_a_storage_error(self):
        with self.assertRaises(StorageError):
            storage.save(ConsultationRecord(**JAIPUR),
                         os.path.join(self.directory.name, "x\0y.json"))

    def test_a_missing_file_reports_a_storage_error(self):
        with self.assertRaises(StorageError) as caught:
            storage.load(self.path("absent.json"))
        self.assertIn("could not be read", caught.exception.message)

    def test_a_file_that_is_not_json_reports_a_storage_error(self):
        with open(self.path(), "w", encoding="utf-8") as handle:
            handle.write("this is not json")
        with self.assertRaises(StorageError) as caught:
            storage.load(self.path())
        self.assertIn("not a valid consultation file",
                      caught.exception.message)


# ── Part 32: migration ───────────────────────────────────────────────────────

class MigrationTest(_Temp):

    def test_a_v1_consultation_file_still_opens(self):
        """
        The shape `sample_consultation.json` uses, which predates the
        application layer. Migrating it is better than refusing a file
        that ships in this repository.
        """
        legacy = {"name": "Legacy", "dob": "1988-08-30", "tob": "20:18",
                  "place": "Jaipur", "ayanamsha": "Lahiri"}
        with open(self.path(), "w", encoding="utf-8") as handle:
            json.dump(legacy, handle)

        record, report = storage.load(self.path())
        self.assertEqual(record.date_of_birth, "1988-08-30")
        self.assertEqual(record.time_of_birth, "20:18")
        self.assertEqual(record.settings.ayanamsha, "lahiri")
        self.assertIn("pre-schema -> 1.0.0", report["migrations"])

    def test_the_repository_s_own_sample_file_migrates(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample = os.path.join(root, "sample_consultation.json")
        if not os.path.exists(sample):
            self.skipTest("sample_consultation.json is not present")
        record, report = storage.load(sample)
        self.assertTrue(record.date_of_birth)
        self.assertTrue(record.place)
        self.assertEqual(report["read_schema"], "pre-1.7")

    def test_a_legacy_file_claims_only_the_precision_its_field_supports(self):
        """
        A V1 file recorded HH:MM and nothing about how good it was. That
        is exactly the case Part 4 exists for, and assuming the minute is
        what the field supports — not more.
        """
        with open(self.path(), "w", encoding="utf-8") as handle:
            json.dump({"name": "L", "dob": "1988-08-30", "tob": "20:18",
                       "place": "Jaipur"}, handle)
        record, report = storage.load(self.path())
        self.assertIs(record.precision, BirthTimePrecision.EXACT_TO_MINUTE)
        self.assertTrue(any("precision" in note
                            for note in report["migration_notes"]))

    def test_gaps_are_filled_from_the_defaults_of_the_file_s_own_release(self):
        """
        Part 32's core rule. A consultation saved when the default
        ayanamsha was Lahiri must not become a Raman chart because a later
        release changed the default. The chart would move by degrees and
        nothing would say so.
        """
        payload = {"schema_version": "1.0.0", "application_version": "1.7.0",
                   "input": {"name": "Gapped", "date_of_birth": "1988-08-30",
                             "time_of_birth": "20:18", "place": "Jaipur"},
                   "settings": {}, "report": {}}
        record, report = storage.from_dict(payload)
        historical = storage.DEFAULTS_BY_SCHEMA["1.0.0"]
        self.assertEqual(record.settings.ayanamsha, historical["ayanamsha"])
        self.assertEqual(record.settings.rule_profile,
                         historical["rule_profile"])
        self.assertTrue(any("defaults in force when it was written" in note
                            for note in report["migration_notes"]))

    def test_an_explicit_setting_is_never_overwritten_by_a_default(self):
        payload = {"schema_version": "1.0.0",
                   "input": {"name": "x", "date_of_birth": "1988-08-30",
                             "time_of_birth": "20:18", "place": "Jaipur"},
                   "settings": {"ayanamsha": "krishnamurti"}}
        record, _ = storage.from_dict(payload)
        self.assertEqual(record.settings.ayanamsha, "krishnamurti")

    def test_a_future_schema_is_refused_rather_than_guessed_at(self):
        """
        A reader that ignores fields it does not understand silently drops
        a methodology setting, and the chart changes without saying so.
        """
        payload = {"schema_version": "9.9.9",
                   "input": {"name": "x", "date_of_birth": "1988-08-30",
                             "time_of_birth": "20:18", "place": "Jaipur"}}
        with self.assertRaises(StorageError) as caught:
            storage.from_dict(payload)
        self.assertIn("cannot read", caught.exception.message)
        self.assertIn("silently change", caught.exception.hint)

    def test_the_frozen_defaults_table_covers_every_shipped_schema(self):
        self.assertIn(CONSULTATION_SCHEMA_VERSION, storage.DEFAULTS_BY_SCHEMA)
        for version, defaults in storage.DEFAULTS_BY_SCHEMA.items():
            with self.subTest(version=version):
                for key in ("ayanamsha", "node", "house_system",
                            "rule_profile", "synthesis_profile", "language"):
                    self.assertIn(key, defaults)

    def test_a_changed_default_is_reported_and_the_saved_value_kept(self):
        """
        Simulates the release after a default changes: the note has to
        appear, and the saved value has to win.
        """
        original = dict(storage.DEFAULTS_BY_SCHEMA["1.0.0"])
        storage.DEFAULTS_BY_SCHEMA["1.0.0"] = dict(original,
                                                   ayanamsha="raman")
        try:
            payload = {"schema_version": "1.0.0",
                       "input": {"name": "x", "date_of_birth": "1988-08-30",
                                 "time_of_birth": "20:18",
                                 "place": "Jaipur"},
                       "settings": {}}
            record, report = storage.from_dict(payload)
            self.assertEqual(record.settings.ayanamsha, "raman")
            self.assertTrue(any("have changed since" in note
                                for note in report["migration_notes"]))
        finally:
            storage.DEFAULTS_BY_SCHEMA["1.0.0"] = original

    def test_an_unknown_precision_widens_rather_than_narrows(self):
        payload = {"schema_version": "1.0.0",
                   "input": {"name": "x", "date_of_birth": "1988-08-30",
                             "time_of_birth": "20:18", "place": "Jaipur",
                             "birth_time_precision": "EXACT_TO_NANOSECOND"}}
        record, report = storage.from_dict(payload)
        self.assertIs(record.precision, BirthTimePrecision.UNKNOWN)
        self.assertTrue(any("widest band" in note
                            for note in report["migration_notes"]))

    def test_an_incomplete_file_is_refused_with_a_reason(self):
        payload = {"schema_version": "1.0.0",
                   "input": {"name": "x", "place": "Jaipur"}}
        with self.assertRaises(StorageError) as caught:
            storage.from_dict(payload)
        self.assertIn("date_of_birth", caught.exception.message)
        self.assertIn("cannot be recomputed", caught.exception.message)


if __name__ == "__main__":
    unittest.main()


class CommandLineOverrideTest(_Temp):
    """
    A flag the user typed beats the saved file; one they did not does not.

    The defect this pins: `--language hi` on a consultation saved in
    English silently produced an English report, because the loaded record
    carried its own preferences and nothing reconciled them. That is the
    same class of error as a migration applying today's defaults to
    yesterday's chart, in the opposite direction.
    """

    def test_an_explicit_flag_overrides_the_saved_value(self):
        import main

        record = ConsultationRecord(
            **JAIPUR, report=ReportPreferences(mode="summary",
                                               language="en"))
        storage.save(record, self.path())

        args = main.parse_args_from(
            ["--open-consultation", self.path(), "--language", "hi",
             "--report-mode", "technical"])
        reopened = main.consultation_from_args(args)
        self.assertEqual(reopened.report.language, "hi")
        self.assertEqual(reopened.settings.language, "hi")
        self.assertEqual(reopened.report.mode, "technical")

    def test_an_untyped_flag_leaves_the_saved_value_alone(self):
        import main

        record = ConsultationRecord(
            **JAIPUR, report=ReportPreferences(mode="summary",
                                               language="hi"))
        storage.save(record, self.path())

        args = main.parse_args_from(["--open-consultation", self.path()])
        reopened = main.consultation_from_args(args)
        self.assertEqual(reopened.report.language, "hi")
        self.assertEqual(reopened.report.mode, "summary")

    def test_methodology_is_not_overridable_from_the_command_line(self):
        """
        Methodology is what a saved consultation exists to preserve.
        Silently changing an ayanamsha on reopen would make the file
        useless for the thing it is for, so the override table is short
        and deliberate.
        """
        import main

        self.assertNotIn("ayanamsha", main._OVERRIDES)
        self.assertNotIn("rule_profile", main._OVERRIDES)
        self.assertNotIn("house_system", main._OVERRIDES)

