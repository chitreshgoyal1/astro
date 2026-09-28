"""
Application services (V1.7 Parts 2, 3, 4, 30, 33, 34, 37)
===========================================================
The four public operations, the errors they raise, and the state they
refuse to mutate.

WHAT THESE TESTS ARE FOR

    The services are adapters. The risk in an adapter is not that it
    computes the wrong answer — it does not compute — but that it quietly
    changes what was asked for on the way through: narrows a precision,
    substitutes a default, or hands a renderer a live object it can reach
    through.

    So these check the translation, not the astrology. Whether the tenth
    house means career is settled in `test_domain_validation`; whether the
    form's "within 15 minutes" reaches the reliability gate as 900 seconds
    is settled here.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.errors import (
    ApplicationError, InvalidBirthDataError, LocationError, MethodologyError,
    ReportGenerationError, UnsupportedLanguageError,
)
from app.models import (
    APPLICATION_VERSION, ApplicationSettings, BirthTimePrecision,
    ConsultationRecord, ReportPreferences,
)
from app.services import (
    available_options, calculate_chart, calculate_prediction,
    chart_visual_model, describe_methodology, render_interpretation,
    timeline_candidates, validate_settings,
)

JAIPUR = dict(name="Jaipur 1988", date_of_birth="1988-08-30",
              time_of_birth="20:18", place="Jaipur")
MOMENT = datetime.datetime(2026, 9, 27, 12)


class _Calculated(unittest.TestCase):
    """One chart and one prediction, computed once for the whole module."""

    @classmethod
    def setUpClass(cls):
        cls.record = ConsultationRecord(**JAIPUR)
        cls.natal = calculate_chart(cls.record)
        cls.prediction = calculate_prediction(cls.natal, MOMENT)


# ── Part 3, Part 4: input and precision ──────────────────────────────────────

class BirthTimePrecisionTest(unittest.TestCase):

    def test_a_typed_time_never_claims_more_than_it_carries(self):
        """
        Part 4, stated as a rule: `10:35` has told us the minute, and the
        seconds were never supplied. Treating HH:MM as second-exact is how
        a chart acquires confidence nobody ever claimed for it.
        """
        self.assertIs(BirthTimePrecision.from_time_text("10:35"),
                      BirthTimePrecision.EXACT_TO_MINUTE)
        self.assertIs(BirthTimePrecision.from_time_text("10:35:20"),
                      BirthTimePrecision.EXACT_TO_SECOND)
        self.assertIs(BirthTimePrecision.from_time_text(""),
                      BirthTimePrecision.UNKNOWN)

    def test_unknown_is_the_widest_band_and_not_the_narrowest(self):
        """
        UNKNOWN must never mean "no uncertainty". A chart whose time is
        not known is a chart whose D60 Lagna — and often whose Lagna — is
        not known either, and the band has to say so.
        """
        bands = [p.seconds for p in BirthTimePrecision]
        self.assertEqual(max(bands), BirthTimePrecision.UNKNOWN.seconds)
        self.assertEqual(BirthTimePrecision.EXACT_TO_MINUTE.seconds, 60)
        self.assertEqual(BirthTimePrecision.APPROX_15_MIN.seconds, 900)

    def test_the_precision_travels_with_the_chart(self):
        record = ConsultationRecord(
            **JAIPUR, precision=BirthTimePrecision.APPROX_15_MIN)
        natal = calculate_chart(record)
        birth = natal.snapshot["birth"]
        self.assertEqual(birth["time_precision"], "APPROX_15_MIN")
        self.assertEqual(birth["time_precision_seconds"], 900)
        self.assertIn("15 minutes", birth["time_precision_basis"])

    def test_the_precision_reaches_the_reliability_gate(self):
        """
        The connection Part 4 asks for. A user who says the time is
        approximate must get a synthesis that treats it as approximate,
        not one that recorded the answer and computed as before.
        """
        loose = calculate_prediction(
            calculate_chart(ConsultationRecord(
                **JAIPUR, precision=BirthTimePrecision.APPROX_15_MIN)),
            MOMENT)
        tight = calculate_prediction(
            calculate_chart(ConsultationRecord(
                **JAIPUR, precision=BirthTimePrecision.EXACT_TO_SECOND)),
            MOMENT)
        self.assertEqual(
            loose.snapshot["reliability"]["birth_time_precision_seconds"],
            900)
        self.assertEqual(
            tight.snapshot["reliability"]["birth_time_precision_seconds"], 1)


# ── Part 33: errors ──────────────────────────────────────────────────────────

class ErrorTest(unittest.TestCase):

    def test_an_unreadable_date_names_the_field(self):
        with self.assertRaises(InvalidBirthDataError) as caught:
            calculate_chart(ConsultationRecord(
                name="x", date_of_birth="30/08/1988", time_of_birth="20:18",
                place="Jaipur"))
        self.assertEqual(caught.exception.field, "date_of_birth")
        self.assertIn("YYYY-MM-DD", caught.exception.message)

    def test_a_missing_time_is_refused_with_a_reason(self):
        with self.assertRaises(InvalidBirthDataError) as caught:
            calculate_chart(ConsultationRecord(
                name="x", date_of_birth="1988-08-30", time_of_birth="",
                place="Jaipur"))
        self.assertIn("rising sign", caught.exception.message)
        self.assertTrue(caught.exception.hint)

    def test_an_unknown_place_is_never_substituted(self):
        """
        The engine has never had a fallback city and this layer does not
        introduce one. A chart computed from the wrong coordinates is not
        a degraded chart, it is someone else's.
        """
        with self.assertRaises(LocationError) as caught:
            calculate_chart(ConsultationRecord(
                name="x", date_of_birth="1988-08-30", time_of_birth="20:18",
                place="Nowhere-in-Particular"))
        self.assertIn("No other place is substituted",
                      caught.exception.hint)

    def test_an_unavailable_methodology_lists_what_is_available(self):
        with self.assertRaises(MethodologyError) as caught:
            validate_settings(ApplicationSettings(ayanamsha="tropical"))
        self.assertIn("lahiri", caught.exception.message)

    def test_an_uninstalled_language_is_refused(self):
        with self.assertRaises(UnsupportedLanguageError):
            validate_settings(ApplicationSettings(language="fr"))

    def test_a_normal_error_carries_no_technical_detail(self):
        """
        Part 33: no raw stack trace reaches a normal user. The dictionary
        simply does not carry one unless debug mode asks for it, so there
        is no path by which internals leak by accident.
        """
        error = InvalidBirthDataError("A message.", detail="ValueError: ...",
                                      field="dob")
        self.assertNotIn("detail", error.to_dict(debug=False))
        self.assertIn("detail", error.to_dict(debug=True))

    def test_every_service_error_is_an_application_error(self):
        for error in (InvalidBirthDataError, LocationError, MethodologyError,
                      UnsupportedLanguageError, ReportGenerationError):
            with self.subTest(error=error.__name__):
                self.assertTrue(issubclass(error, ApplicationError))
                self.assertTrue(error.category)


# ── Part 2: the operations ───────────────────────────────────────────────────

class ChartServiceTest(_Calculated):

    def test_the_snapshot_is_the_engine_s_own(self):
        self.assertEqual(self.natal.schema_version, "1.2.0")
        for section in ("birth", "lagna", "planets", "houses", "vargas",
                        "yogas", "timing", "methodology"):
            with self.subTest(section=section):
                self.assertTrue(self.natal.snapshot[section])

    def test_the_result_is_json_native(self):
        json.loads(json.dumps(self.natal.snapshot))

    def test_engine_objects_are_excluded_from_equality(self):
        """
        Part 30: a result is its data. Two results holding the same
        snapshot are the same result, whatever live objects came with them.
        """
        from dataclasses import replace
        other = replace(self.natal, engine_objects={})
        self.assertEqual(self.natal, other)

    def test_settings_are_never_mutated(self):
        settings = ApplicationSettings()
        before = settings.to_dict()
        calculate_chart(ConsultationRecord(**JAIPUR), settings)
        self.assertEqual(settings.to_dict(), before)

    def test_replace_returns_a_copy(self):
        settings = ApplicationSettings()
        changed = settings.replace(ayanamsha="raman")
        self.assertEqual(settings.ayanamsha, "lahiri")
        self.assertEqual(changed.ayanamsha, "raman")


class PredictionServiceTest(_Calculated):

    def test_a_bare_date_is_read_as_midday(self):
        """
        Not midnight. The dasha stack and the transit positions are both
        continuous, and midnight sits on a day boundary where a reader is
        most likely to be surprised by which side of an ingress the answer
        fell.
        """
        from app.services.prediction_service import parse_moment
        self.assertEqual(parse_moment("2026-09-27").hour, 12)
        self.assertEqual(parse_moment("2026-09-27T06:30").hour, 6)

    def test_an_unreadable_moment_is_refused(self):
        from app.services.prediction_service import parse_moment
        with self.assertRaises(InvalidBirthDataError):
            parse_moment("next Tuesday")

    def test_the_profile_reaches_the_snapshot(self):
        strict = calculate_prediction(self.natal, MOMENT, profile="strict")
        self.assertEqual(strict.snapshot["methodology_profile"], "strict")

    def test_an_unknown_profile_names_the_available_ones(self):
        with self.assertRaises(MethodologyError) as caught:
            calculate_prediction(self.natal, MOMENT, profile="lenient")
        self.assertIn("strict", caught.exception.message)

    def test_timeline_rows_carry_no_number_to_plot_as_probability(self):
        """
        Part 17. Activation and confidence are ordinal bands. A timeline
        given a numeric field would eventually draw it on an axis, and the
        axis would be an invention.
        """
        rows = timeline_candidates(self.prediction)
        for row in rows:
            with self.subTest(domain=row["domain"]):
                for key, value in row.items():
                    if key in ("window_start", "window_end", "peak"):
                        continue
                    self.assertNotIsInstance(
                        value, (int, float),
                        f"{key} is numeric and could be plotted")

    def test_timeline_filtering_changes_the_list_not_the_calculation(self):
        everything = timeline_candidates(self.prediction)
        if not everything:
            self.skipTest("this chart produced no candidates")
        first = everything[0]["domain"]
        filtered = timeline_candidates(self.prediction, domains=[first])
        self.assertTrue(filtered)
        self.assertTrue(all(r["domain"] == first for r in filtered))
        for row in filtered:
            self.assertIn(row, everything)


class InterpretationServiceTest(_Calculated):

    def test_one_render_per_mode_and_no_second_phrasing_path(self):
        """
        Part 22: the modes must not duplicate interpretation logic. The
        check is that a finding present in two modes is phrased
        identically in both — if there were a second path, it would not be.
        """
        detailed = render_interpretation(self.prediction, mode="detailed")
        technical = render_interpretation(self.prediction, mode="technical")
        for section in detailed.domain_sections:
            other = technical.section_for(section.domain)
            if other is None or section.overall is None:
                continue
            with self.subTest(domain=section.domain):
                self.assertEqual(section.activation, other.activation)
                self.assertEqual(section.overall.text, other.overall.text)

    def test_an_unknown_mode_is_refused(self):
        with self.assertRaises(MethodologyError):
            render_interpretation(self.prediction, mode="brief")

    def test_an_uninstalled_language_is_refused(self):
        with self.assertRaises(UnsupportedLanguageError):
            render_interpretation(self.prediction, language="fr")

    def test_the_birth_block_is_read_from_the_snapshot(self):
        document = render_interpretation(self.prediction, mode="summary")
        self.assertEqual(document.birth_summary["name"], "Jaipur 1988")
        self.assertEqual(document.birth_summary["place"], "Jaipur")


# ── Part 18: the methodology panel ───────────────────────────────────────────

class MethodologyPanelTest(_Calculated):

    def test_the_panel_reads_the_snapshot_not_the_settings(self):
        """
        Different questions. Settings are what was asked for; the snapshot
        records what was used. The panel shows the second.
        """
        described = describe_methodology(self.natal, ApplicationSettings())
        values = {row["label"]: row["value"] for row in described["rows"]}
        self.assertEqual(values["Ayanamsha"],
                         self.natal.snapshot["calculation_settings"]
                         ["ayanamsha"])
        self.assertEqual(values["Chart schema"], "1.2.0")

    def test_non_default_settings_are_listed(self):
        settings = ApplicationSettings(ayanamsha="raman", node="mean")
        described = describe_methodology(self.natal, settings)
        labels = {row["label"] for row in described["rows"]}
        self.assertIn("Non-default settings", labels)

    def test_the_four_claims_stay_separate(self):
        described = describe_methodology(self.natal)
        claims = described["claim_separation"]
        for key in ("computationally_tested", "externally_benchmarked",
                    "textual_source_located", "tradition_source_validated"):
            with self.subTest(claim=key):
                self.assertIn(key, claims)
        self.assertIn("none is evidence", claims["note"].lower())

    def test_no_tradition_validated_claim_is_made(self):
        described = describe_methodology(self.natal)
        self.assertEqual(described["provenance"]["tradition_validated"], 0)


# ── Part 3: the options the form may offer ───────────────────────────────────

class OptionsTest(unittest.TestCase):

    def test_options_are_enumerated_from_the_engine(self):
        """
        A hard-coded list in the UI goes stale the first time the engine
        gains an option and goes wrong the first time it loses one.
        """
        from engine.planets import available_ayanamshas
        from engine.rules import RULE_PROFILES

        options = available_options()
        self.assertEqual(set(options["ayanamsha"]["values"]),
                         set(available_ayanamshas()))
        self.assertEqual(set(options["rule_profile"]["values"]),
                         set(RULE_PROFILES))

    def test_the_default_rule_profile_matches_the_engine(self):
        """
        `ApplicationSettings` writes the default out rather than importing
        it, so the two can drift. This is what stops them.
        """
        from engine.rules import DEFAULT_PROFILE
        self.assertEqual(ApplicationSettings().rule_profile, DEFAULT_PROFILE)

    def test_every_option_shows_its_default(self):
        for name, spec in available_options().items():
            if name == "varga_conventions":
                continue
            with self.subTest(option=name):
                self.assertIn("default", spec)
                self.assertIn(spec["default"], spec["values"])
                self.assertTrue(spec["help"])

    def test_unverified_ashtakavarga_reductions_are_off_by_default(self):
        """Part 13: the UI must not enable them silently."""
        self.assertFalse(ApplicationSettings().ashtakavarga_reductions)


# ── Part 34: offline ─────────────────────────────────────────────────────────

class OfflineTest(_Calculated):

    def test_the_pipeline_opens_no_socket(self):
        """
        Part 34. Checked by making the socket constructor fail: anything
        that reached for the network would raise instead of silently
        succeeding on a machine that happens to be connected.
        """
        import socket

        real = socket.socket

        class Blocked(Exception):
            pass

        def refuse(*args, **kwargs):
            raise Blocked("the pipeline must not open a socket")

        socket.socket = refuse
        try:
            record = ConsultationRecord(**JAIPUR)
            natal = calculate_chart(record)
            prediction = calculate_prediction(natal, MOMENT)
            document = render_interpretation(prediction, mode="technical")
            self.assertTrue(document.domain_sections)
            model = chart_visual_model(natal, varga="D9")
            self.assertEqual(len(model.houses), 12)
        finally:
            socket.socket = real


if __name__ == "__main__":
    unittest.main()


class CommandLineEntryTest(unittest.TestCase):
    """
    `--app` must open the UI, not the console prompt.

    The defect this pins: `--app` alone called `collect_input`, which
    prompts on stdin for details the browser's own form is about to ask
    for. With stdin not a terminal it raised EOFError and the server never
    started at all.
    """

    def test_app_alone_needs_no_birth_details(self):
        import main
        args = main.parse_args_from(["--app"])
        self.assertFalse(main._has_birth_details(args))

    def test_details_on_the_command_line_are_recognised(self):
        import main
        args = main.parse_args_from(
            ["--app", "--name", "X", "--dob", "1988-08-30",
             "--time", "20:18", "--place", "Jaipur"])
        self.assertTrue(main._has_birth_details(args))

    def test_a_consultation_file_counts_as_details(self):
        import main
        self.assertTrue(main._has_birth_details(
            main.parse_args_from(["--app", "--consultation", "x.json"])))
        self.assertTrue(main._has_birth_details(
            main.parse_args_from(["--app", "--open-consultation",
                                  "x.json"])))

    def test_the_application_routes_are_recognised_by_main(self):
        """Every V1.7 flag must reach `run_application` rather than the
        console report."""
        import main
        for flag in ("--app", "--benchmark"):
            with self.subTest(flag=flag):
                args = main.parse_args_from([flag])
                self.assertTrue(
                    args.app or args.report or args.report_html
                    or args.report_json or args.benchmark
                    or args.save_consultation or args.open_consultation)

