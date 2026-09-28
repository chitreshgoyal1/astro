"""
End-to-end golden reports (V1.7 Parts 38, 39)
===============================================
Five reports from one chart, and the guarantee that identical inputs
produce identical output.

THE FIVE PART 39 ASKS FOR

    English summary, English detailed, English technical,
    Hindi summary, Hindi detailed.

    The English three go to PDF and HTML. The Hindi two go to HTML only:
    the PDF's Latin base-14 faces cannot print Devanagari and refuse to
    try, which is itself pinned below.

WHAT "IDENTICAL" MEANS HERE

    Byte-identical, with nothing ignored. The PDF writer emits no creation
    date and no identifier derived from the clock, and the report's content
    hash excludes the generation timestamp, so there is no unavoidable
    metadata to make an exception for. If that ever changes, this test is
    where it should become visible.

THE CASES

    The Jaipur 1988 regression chart, which every release since V1.4 has
    used, plus a synthetic chart built to be crowded — seven bodies in one
    house — because the regression chart is not, and a renderer that drops
    a graha under pressure would otherwise never be tested end to end.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import ConsultationRecord, ReportPreferences
from app.report import PdfUnsupportedText, render_html, render_pdf
from app.services import calculate_chart, calculate_prediction
from app.services.report_service import generate_report

MOMENT = datetime.datetime(2026, 9, 27, 12)
FIXED_TIME = "2026-09-27T12:00:00"

JAIPUR = dict(name="Jaipur 1988", date_of_birth="1988-08-30",
              time_of_birth="20:18", place="Jaipur")

#: (language, mode). The five Part 39 names.
CASES = (("en", "summary"), ("en", "detailed"), ("en", "technical"),
         ("hi", "summary"), ("hi", "detailed"))


def _claim_text(document) -> list[str]:
    """
    The sentences a report ASSERTS, as opposed to the ones that limit it.

    Body and lead paragraphs, bullets and table cells are claims. Callouts
    and small-print notes are limits, and a limit has to be able to name
    the thing it rules out. See `test_no_report_states_a_probability`.
    """
    out: list[str] = []
    for section in document.sections:
        for block in section.blocks:
            data = block.to_dict()
            kind = data["block"]
            if kind == "paragraph" and data.get("style") in ("body", "lead"):
                out.append(data["text"])
            elif kind == "heading":
                out.append(data["text"])
            elif kind == "bullets":
                out.extend(data["items"])
            elif kind == "table":
                out.extend(str(cell) for row in data["rows"] for cell in row)
            elif kind == "keyvalues":
                out.extend(str(value) for _key, value in data["pairs"])
    return out


class GoldenReportTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.record = ConsultationRecord(**JAIPUR)
        cls.natal = calculate_chart(cls.record)
        cls.prediction = calculate_prediction(cls.natal, MOMENT)
        cls.reports = {}
        for language, mode in CASES:
            cls.reports[(language, mode)] = cls._build(cls, language, mode)

    def _build(self, language: str, mode: str):
        return generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode=mode, language=language),
            generated=FIXED_TIME)

    def _rebuild(self, language: str, mode: str):
        """A second, independent build of the same report."""
        return generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode=mode, language=language),
            generated=FIXED_TIME)

    # ── all five exist and are non-trivial ──────────────────────────────
    def test_all_five_reports_build(self):
        for key, document in self.reports.items():
            with self.subTest(case=key):
                self.assertTrue(document.sections)
                self.assertEqual(document.mode, key[1])
                self.assertEqual(document.language, key[0])

    def test_each_report_records_what_produced_it(self):
        for key, document in self.reports.items():
            with self.subTest(case=key):
                provenance = document.provenance
                # Deliberately literal, not read from the constants they
                # pin. Reading them would make this test agree with any
                # value the engine happened to hold, which is the opposite
                # of what a pin is for: a schema bump must show up here as
                # a diff somebody had to justify.
                self.assertEqual(provenance["chart_schema"], "1.2.0")
                # 1.0.0 → 1.1.0 in V1.8: the prediction snapshot gained the
                # `gochara` section. Additive; no 1.0.0 key changed meaning.
                self.assertEqual(provenance["prediction_schema"], "1.1.0")
                self.assertEqual(provenance["interpretation_schema"], "1.0.0")
                self.assertEqual(provenance["language"], key[0])

    # ── Part 39: identical inputs, identical output ─────────────────────
    def test_the_document_is_byte_identical_on_a_second_build(self):
        for language, mode in CASES:
            with self.subTest(language=language, mode=mode):
                first = self.reports[(language, mode)]
                second = self._rebuild(language, mode)
                self.assertEqual(first.content_hash(), second.content_hash())
                self.assertEqual(first.to_json(), second.to_json())

    def test_the_html_is_byte_identical_on_a_second_build(self):
        for language, mode in CASES:
            with self.subTest(language=language, mode=mode):
                first = render_html(
                    self.reports[(language, mode)].to_dict())
                second = render_html(self._rebuild(language, mode).to_dict())
                self.assertEqual(first, second)

    def test_the_pdf_is_byte_identical_on_a_second_build(self):
        for mode in ("summary", "detailed", "technical"):
            with self.subTest(mode=mode):
                first = render_pdf(self.reports[("en", mode)].to_dict())
                second = render_pdf(self._rebuild("en", mode).to_dict())
                self.assertEqual(first, second)

    def test_no_unavoidable_metadata_had_to_be_ignored(self):
        """
        Part 39 allows PDF metadata to be excluded if necessary. It was
        not necessary, and this records that: the comparison above is on
        the whole file, and the writer emits no clock-derived field.
        """
        data = render_pdf(self.reports[("en", "summary")].to_dict())
        for forbidden in (b"/CreationDate", b"/ModDate", b"/ID"):
            with self.subTest(field=forbidden):
                self.assertNotIn(forbidden, data)

    # ── the two languages report the same findings ──────────────────────
    def test_hindi_and_english_summaries_report_the_same_activation(self):
        """
        A translation changes the words. If it changed a finding, the
        locale would be deciding something about the chart.
        """
        from app.services import render_interpretation
        english = render_interpretation(self.prediction, language="en",
                                        mode="summary")
        hindi = render_interpretation(self.prediction, language="hi",
                                      mode="summary")
        self.assertEqual(
            {s.domain: s.activation for s in english.domain_sections},
            {s.domain: s.activation for s in hindi.domain_sections})

    def test_the_two_languages_produce_the_same_section_structure(self):
        english = self.reports[("en", "detailed")]
        hindi = self.reports[("hi", "detailed")]
        self.assertEqual([s.id for s in english.ordered_sections()],
                         [s.id for s in hindi.ordered_sections()])

    # ── the script limit, pinned ────────────────────────────────────────
    def test_hindi_renders_as_both_pdf_and_html(self):
        """
        REPLACES `test_hindi_pdf_is_refused_and_html_is_complete` (V1.7).

        The refusal was correct while the engine had no Devanagari font
        and no shaper. V1.8 has both, so the assertion is replaced rather
        than relaxed: the same document now has to come out as a real PDF
        with an embedded Type0 font AND as complete HTML, because HTML
        remains the better answer for a reader who wants to copy text or
        resize it.
        """
        for mode in ("summary", "detailed"):
            with self.subTest(mode=mode):
                document = self.reports[("hi", mode)].to_dict()
                data = render_pdf(document)
                self.assertTrue(data.startswith(b"%PDF"))
                self.assertIn(b"/Subtype /Type0", data)
                markup = render_html(document)
                self.assertIn('lang="hi"', markup)
                self.assertGreater(len(markup), 10_000)

    def test_the_hindi_pdf_is_byte_identical_on_a_second_render(self):
        """
        Font subsetting is the step most likely to break determinism: the
        subset depends on which glyphs were used, and glyph usage
        accumulates on a module-level object. If it is not reset per
        document, the second render of the same report embeds a larger
        subset than the first.
        """
        document = self.reports[("hi", "detailed")].to_dict()
        self.assertEqual(render_pdf(document), render_pdf(document))

    # ── the reports say what they are ───────────────────────────────────
    def test_every_report_carries_the_standing_disclaimer(self):
        for key, document in self.reports.items():
            with self.subTest(case=key):
                blob = json.dumps(document.to_dict(), ensure_ascii=False)
                self.assertTrue(
                    "not a prediction of events" in blob
                    or "भविष्यवा"
                       "णी नहीं" in blob,
                    "the report must say what it is not")

    def test_no_report_claims_tradition_validation(self):
        for key, document in self.reports.items():
            with self.subTest(case=key):
                blob = json.dumps(document.to_dict(), ensure_ascii=False)
                self.assertNotIn("tradition-validated methodology", blob)
                self.assertNotIn("validated by tradition", blob)

    def test_no_report_states_a_probability(self):
        """
        Activation and confidence are ordinal bands. A percentage or a
        "chance" anywhere in a report would be an invention.

        THE DISCLAIMER TRAP, FOR THE FOURTH RELEASE RUNNING

            V1.4 failed a test like this on the word "score" inside its
            own note about scores. V1.5 failed on a FIELD NAME,
            `confidence_is_not_probability`. V1.6 failed on the health
            scope limit, which contains the word "diagnosis" in order to
            disclaim one. And this one fails on three sentences that exist
            to say the engine emits no probability.

            The tempting fix, every time, is to soften the disclaimer. The
            correct fix is to scan CLAIMS rather than documents. A claim
            is a body paragraph, a bullet or a table cell; a limit is a
            callout or a small-print note, and a limit is allowed — is
            obliged — to name the thing it is ruling out.
        """
        import re

        forbidden = ("probability", "likelihood", "odds of", "per cent",
                     "% chance")
        for key, document in self.reports.items():
            for text in _claim_text(document):
                with self.subTest(case=key, text=text[:48]):
                    lowered = text.lower()
                    self.assertIsNone(
                        re.search(r"\d+\s?%", lowered),
                        "a percentage in a claim is an invention")
                    for word in forbidden:
                        self.assertNotIn(word, lowered)

    def test_the_limits_do_name_what_they_rule_out(self):
        """
        The other half of the rule above. A disclaimer that could not use
        the word "probability" would not be a disclaimer, so this asserts
        that the callouts still say it — a future release that weakened
        them to pass the test above fails here instead.
        """
        document = self.reports[("en", "detailed")]
        limits = " ".join(
            block.to_dict().get("text", "")
            for section in document.sections for block in section.blocks
            if block.to_dict()["block"] == "callout")
        self.assertIn("not probabilities", limits)
        self.assertIn("ordinal", limits)


class CrowdedChartReportTest(unittest.TestCase):
    """
    A chart with many bodies in one house, carried end to end.

    Built by hand rather than hunted for: the point is the renderer under
    pressure, not the astrology of any particular birth.
    """

    @classmethod
    def setUpClass(cls):
        cls.record = ConsultationRecord(
            name="Crowded", date_of_birth="1988-08-30",
            time_of_birth="20:18", place="Jaipur",
            entered_positions={
                "Lagna": "Mesha 10 00", "Surya": "Mesha 1 00",
                "Chandra": "Mesha 3 00", "Mangal": "Mesha 5 00",
                "Budha": "Mesha 7 00", "Guru": "Mesha 9 00",
                "Shukra": "Mesha 11 00", "Shani": "Mesha 13 00",
                "Rahu": "Tula 4 00", "Ketu": "Mesha 4 00"})
        cls.natal = calculate_chart(cls.record)

    def test_all_seven_reach_the_first_house(self):
        from app.services import chart_visual_model
        model = chart_visual_model(self.natal)
        first = model.house(1)
        self.assertGreaterEqual(len(first.bodies), 8)   # seven plus Lagna
        self.assertTrue(model.is_crowded)

    def test_the_crowded_chart_renders_to_pdf_and_html(self):
        document = generate_report(
            self.record, natal=self.natal,
            prediction=calculate_prediction(self.natal, MOMENT),
            preferences=ReportPreferences(mode="summary"),
            generated=FIXED_TIME)
        data = render_pdf(document.to_dict())
        self.assertTrue(data.startswith(b"%PDF"))
        markup = render_html(document.to_dict())
        self.assertIn("<svg", markup)

    def test_the_crowded_chart_is_deterministic(self):
        from app.services import chart_visual_model
        from app.visual import render_north_indian
        model = chart_visual_model(self.natal)
        self.assertEqual(render_north_indian(model).content_hash(),
                         render_north_indian(model).content_hash())


if __name__ == "__main__":
    unittest.main()
