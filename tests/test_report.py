"""
Reports and PDF (V1.7 Parts 20, 21, 22, 23, 37)
=================================================
The report model, the three modes, the PDF writer, pagination, and the
source appendix.

WHAT THE PDF TESTS CAN AND CANNOT CHECK

    They cannot check that a page looks right. They can check the things
    that go wrong invisibly: a table row split across a page boundary so a
    number is read against the wrong label, text measured with the wrong
    metrics so a column overruns, a cross-reference table whose offsets
    are wrong so the file will not open, and a character silently replaced
    because the encoding could not carry it.

    So the file is parsed back — object count, page count, xref offsets —
    and the layout is exercised at sizes that force breaks.

THE MODE RULE (Part 22)

    Modes select sections. They never rephrase. The test for that is that
    a sentence appearing in two modes is byte-identical in both, which it
    cannot be if there are two phrasing paths.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.models import ConsultationRecord, ReportPreferences
from app.report.strings import load_strings
from app.report import (
    MODE_SECTIONS, SECTION_ORDER, Callout, PdfUnsupportedText, ReportDocument,
    Section, Table, build_report_document, layout_document, render_html,
    render_pdf, scan_unsupported,
)
from app.report.metrics import WIDTHS, text_width
from app.report.pdf import to_winansi, wrap
from app.services import calculate_chart, calculate_prediction
from app.services.report_service import generate_pdf, generate_report

JAIPUR = dict(name="Jaipur 1988", date_of_birth="1988-08-30",
              time_of_birth="20:18", place="Jaipur")
MOMENT = datetime.datetime(2026, 9, 27, 12)


class _Reports(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.record = ConsultationRecord(**JAIPUR)
        cls.natal = calculate_chart(cls.record)
        cls.prediction = calculate_prediction(cls.natal, MOMENT)
        cls.documents = {}
        for mode in ("summary", "detailed", "technical"):
            cls.documents[mode] = generate_report(
                cls.record, natal=cls.natal, prediction=cls.prediction,
                preferences=ReportPreferences(mode=mode),
                generated="2026-09-27T12:00:00")


# ── Part 20: the model ───────────────────────────────────────────────────────

class ReportDocumentTest(_Reports):

    def test_sections_come_out_in_the_canonical_order(self):
        for mode, document in self.documents.items():
            with self.subTest(mode=mode):
                ids = [s.id for s in document.ordered_sections()]
                index = {name: i for i, name in enumerate(SECTION_ORDER)}
                self.assertEqual(ids, sorted(ids, key=lambda i: index[i]))

    def test_an_unknown_section_is_refused(self):
        document = ReportDocument()
        with self.assertRaises(ValueError):
            document.add(Section(id="horoscope", title="Horoscope"))

    def test_the_document_is_json_native(self):
        for mode, document in self.documents.items():
            with self.subTest(mode=mode):
                json.loads(document.to_json())

    def test_the_content_hash_ignores_the_generation_time(self):
        """
        Part 39 compares reports from identical inputs. A hash that
        covered the clock would never match.
        """
        early = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary"),
            generated="2020-01-01T00:00:00")
        late = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary"),
            generated="2030-01-01T00:00:00")
        self.assertEqual(early.content_hash(), late.content_hash())

    def test_no_block_carries_an_engine_object(self):
        """Every value in a block is a string another layer decided on."""
        for mode, document in self.documents.items():
            for section in document.sections:
                for block in section.blocks:
                    with self.subTest(mode=mode, block=block.to_dict()["block"]):
                        json.dumps(block.to_dict())


# ── Part 22: modes ───────────────────────────────────────────────────────────

class ReportModeTest(_Reports):

    def test_each_mode_carries_the_sections_it_declares(self):
        for mode, document in self.documents.items():
            with self.subTest(mode=mode):
                present = {s.id for s in document.sections}
                self.assertTrue(present <= set(MODE_SECTIONS[mode]))

    def test_summary_is_shorter_than_detailed_which_is_shorter_than_technical(self):
        pages = {mode: len(layout_document(doc.to_dict()).pages)
                 for mode, doc in self.documents.items()}
        self.assertLess(pages["summary"], pages["detailed"])
        self.assertLessEqual(pages["detailed"], pages["technical"])

    def test_the_source_appendix_is_technical_only(self):
        self.assertIsNone(self.documents["summary"].section("source_appendix"))
        self.assertIsNone(self.documents["detailed"].section("source_appendix"))
        self.assertIsNotNone(
            self.documents["technical"].section("source_appendix"))

    def test_a_sentence_present_in_two_modes_is_identical_in_both(self):
        """
        Part 22's real content: modes must not duplicate interpretation
        logic. Two phrasing paths would show up here as two phrasings.
        """
        def paragraphs(document):
            return {block.to_dict()["text"]
                    for section in document.sections
                    for block in section.blocks
                    if block.to_dict()["block"] == "paragraph"}

        detailed = paragraphs(self.documents["detailed"])
        technical = paragraphs(self.documents["technical"])
        shared = detailed & technical
        self.assertTrue(shared, "the two modes should share sentences")
        for text in shared:
            with self.subTest(text=text[:50]):
                self.assertIn(text, detailed)
                self.assertIn(text, technical)


# ── Part 23: the source appendix ─────────────────────────────────────────────

class SourceAppendixTest(_Reports):

    def test_the_appendix_cites_and_never_reproduces(self):
        """
        Locators and concise summaries only. The corpus is not
        redistributed, here or anywhere the engine writes.
        """
        section = self.documents["technical"].section("source_appendix")
        self.assertIsNotNone(section)
        blob = json.dumps(section.to_dict())
        # A reproduced verse would be long, Sanskrit, and not a citation.
        for marker in ("||", "\\section", ".itx"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, blob)
        self.assertIn("never reproduced", blob)

    def test_the_appendix_carries_the_validation_columns(self):
        section = self.documents["technical"].section("source_appendix")
        tables = [b.to_dict() for b in section.blocks
                  if b.to_dict()["block"] == "table"]
        columns = {c for table in tables for c in table["columns"]}
        for wanted in ("Citation", "Edition", "Validation status",
                       "Prediction eligibility"):
            with self.subTest(column=wanted):
                self.assertIn(wanted, columns)

    def test_an_unresolved_reference_is_printed_as_unresolved(self):
        """Dropping it would make the appendix look complete when it is not."""
        from app.report.builder import _source_appendix
        section = _source_appendix(
            load_strings("en"), {},
            {"technical_appendix": {
                "sources": [{"id": "MISSING_1", "resolved": False,
                             "note": "no witness registered"}],
                "rules": []}})
        blob = json.dumps(section.to_dict())
        self.assertIn("MISSING_1", blob)
        self.assertIn("could not resolve", blob)

    def test_the_located_is_not_validated_limit_is_stated(self):
        section = self.documents["technical"].section("source_appendix")
        callouts = [b.to_dict() for b in section.blocks
                    if b.to_dict()["block"] == "callout"]
        self.assertTrue(any("scholar" in c["text"] for c in callouts))


# ── Part 21: the PDF ─────────────────────────────────────────────────────────

class PdfWriterTest(_Reports):

    def test_the_file_is_a_pdf_and_parses(self):
        data = render_pdf(self.documents["detailed"].to_dict())
        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertTrue(data.rstrip().endswith(b"%%EOF"))

    def test_the_cross_reference_table_points_at_real_objects(self):
        """
        A wrong xref offset produces a file that looks fine to a byte
        count and will not open. Every offset is checked against the
        object header it claims to point at.
        """
        data = render_pdf(self.documents["summary"].to_dict())
        start = int(re.search(rb"startxref\s+(\d+)", data).group(1))
        self.assertTrue(data[start:start + 4] == b"xref")
        entries = re.findall(rb"^(\d{10}) 00000 n ", data[start:],
                             re.MULTILINE)
        self.assertTrue(entries)
        for number, offset in enumerate(entries, start=1):
            with self.subTest(obj=number):
                at = int(offset)
                self.assertEqual(
                    data[at:at + len(f"{number} 0 obj")],
                    f"{number} 0 obj".encode("latin-1"))

    def test_the_page_count_matches_the_page_tree(self):
        data = render_pdf(self.documents["technical"].to_dict())
        declared = int(re.search(rb"/Type /Pages /Count (\d+)",
                                 data).group(1))
        self.assertEqual(data.count(b"/Type /Page "), declared)
        self.assertEqual(
            declared,
            len(layout_document(self.documents["technical"].to_dict()).pages))

    def test_page_numbers_run_to_the_real_total(self):
        """
        "Page 3 of 11" cannot be written until the layout is finished,
        which is why the writer makes two passes. This checks the second
        one used the number the first produced.
        """
        layout = layout_document(self.documents["detailed"].to_dict())
        total = len(layout.pages)
        last = "\n".join(layout.pages[-1].ops)
        self.assertIn(f"Page {total} of {total}", last)
        first = "\n".join(layout.pages[0].ops)
        self.assertNotIn("Page 1 of", first,
                         "the cover carries no page furniture")

    def test_a_table_row_is_never_split_across_a_page(self):
        """
        A row split across a boundary puts a number under the wrong
        label, and the reader cannot tell. Rows are atomic; tables are not.
        """
        from app.report.pdf import Layout

        layout = Layout()
        rows = tuple((f"Graha {i}", f"{i}", f"{i * 2}") for i in range(90))
        before = len(layout.pages)
        layout.draw_table(("A", "B", "C"), rows)
        self.assertGreater(len(layout.pages), before,
                           "90 rows must break at least one page")
        for page in layout.pages:
            text = "\n".join(page.ops)
            for index in range(90):
                if f"(Graha {index})" in text:
                    with self.subTest(row=index):
                        self.assertIn(f"({index * 2})", text,
                                      "a row landed on two pages")

    def test_a_broken_table_repeats_its_header(self):
        from app.report.pdf import Layout

        layout = Layout()
        layout.draw_table(("Graha", "Sign"),
                          tuple((f"P{i}", f"S{i}") for i in range(90)))
        self.assertGreater(len(layout.pages), 1)
        for index, page in enumerate(layout.pages):
            with self.subTest(page=index):
                self.assertIn("(Graha)", "\n".join(page.ops))

    def test_a_callout_is_never_split(self):
        """Half a warning box reads as the whole warning."""
        from app.report.pdf import Layout

        layout = Layout()
        layout.y = layout.bottom - 30.0      # almost no room left
        before = len(layout.pages)
        layout.draw_callout("A warning long enough to need several lines "
                            "of a page. " * 6, kind="warning")
        self.assertGreater(len(layout.pages), before)

    def test_text_is_measured_with_real_metrics(self):
        """
        Wrapping and centring both depend on measurement. A stand-in that
        counted characters would make these equal.
        """
        self.assertLess(text_width("iii", "Times-Roman", 10),
                        text_width("WWW", "Times-Roman", 10))
        # 62.004pt, from the URW Nimbus Sans widths. Adobe's own
        # Helvetica gives 62.0 for this string; the third decimal is the
        # metric-compatible clone's rounding and is far below anything
        # that affects a line break.
        self.assertAlmostEqual(
            text_width("Hello World", "Helvetica", 12), 62.0, places=1)

    def test_every_face_the_writer_names_has_metrics(self):
        from app.report.pdf import _FACE_IDS
        for face in _FACE_IDS:
            with self.subTest(face=face):
                self.assertIn(face, WIDTHS)
                self.assertEqual(len(WIDTHS[face]), 256)

    def test_wrapping_respects_the_measured_width(self):
        lines = wrap("word " * 60, "Times-Roman", 10.0, 120.0)
        self.assertGreater(len(lines), 1)
        for line in lines:
            with self.subTest(line=line):
                self.assertLessEqual(text_width(line, "Times-Roman", 10.0),
                                     120.0)

    def test_the_bytes_are_a_pure_function_of_the_document(self):
        """
        Part 39 for the file itself: no creation date, no identifier
        derived from the clock.
        """
        payload = self.documents["summary"].to_dict()
        self.assertEqual(render_pdf(payload), render_pdf(payload))
        self.assertNotIn(b"/CreationDate", render_pdf(payload))


# ── encoding ─────────────────────────────────────────────────────────────────

class EncodingTest(unittest.TestCase):

    def test_winansi_mapping_is_idempotent(self):
        """
        Several call paths convert, wrap, then measure again. A conversion
        that was not idempotent mangled every em-dash on the second pass —
        which is exactly what happened before this was fixed.
        """
        for text in ("a — b", "‘q’", "…", "23°"):
            with self.subTest(text=text):
                once = to_winansi(text)
                self.assertEqual(once, to_winansi(once))
                self.assertTrue(all(ord(c) < 256 for c in once))

    def test_the_em_dash_survives_as_the_winansi_byte(self):
        self.assertEqual(to_winansi("—"), chr(0x97))

    def test_sanskrit_diacritics_become_readable_latin(self):
        """
        Without this the source appendix prints `B?hat P?r???ara Hor?
        ??stra`, which reads as a broken program rather than an encoding
        limit. The diacritics are kept in HTML, where they can be.
        """
        self.assertEqual(
            to_winansi("Bṛhat Pārāśara Horā "
                       "Śāstra"),
            "Brhat Parasara Hora Sastra")

    def test_an_english_report_needs_no_transliteration_beyond_that(self):
        document = build_report_document(
            natal={"birth": {"name": "Test"}}, mode="summary")
        self.assertEqual(scan_unsupported(document.to_dict())["total"], 0)


# ── HTML ─────────────────────────────────────────────────────────────────────

class HtmlReportTest(_Reports):

    def test_the_html_is_one_self_contained_file(self):
        """
        Part 34: no font request, no script, no image reference. It opens
        from a USB stick on a machine that has never been online.
        """
        markup = render_html(self.documents["detailed"].to_dict())
        self.assertIn("<!DOCTYPE html>", markup)
        # Anything that would make the browser fetch something. The SVG
        # namespace is a URI that identifies a vocabulary and is never
        # requested, so it is not on this list.
        for forbidden in ("<script", "@import", "<img ", "<link ",
                          "url(http", "src=", "<iframe"):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden, markup)
        self.assertEqual(markup.count("http"),
                         markup.count('xmlns="http://www.w3.org/2000/svg"'),
                         "the only URL in the file is the SVG namespace")

    def test_the_charts_are_inline_svg(self):
        markup = render_html(self.documents["detailed"].to_dict())
        self.assertIn("<svg", markup)
        self.assertIn("<figcaption>", markup)

    def test_tables_use_real_header_cells(self):
        """A `div` grid is invisible to a screen reader (Part 36)."""
        markup = render_html(self.documents["technical"].to_dict())
        self.assertIn('<th scope="col"', markup)

    def test_the_html_is_deterministic(self):
        payload = self.documents["summary"].to_dict()
        self.assertEqual(render_html(payload), render_html(payload))

    def test_user_text_is_escaped(self):
        document = build_report_document(
            natal={"birth": {"name": "<script>alert(1)</script>"}},
            mode="summary")
        markup = render_html(document.to_dict())
        self.assertNotIn("<script>alert", markup)
        self.assertIn("&lt;script&gt;", markup)


# ── the Devanagari limit ─────────────────────────────────────────────────────

class ScriptLimitTest(_Reports):
    """
    REPLACES V1.7's refusal tests.

    V1.7 asserted that a Hindi PDF is refused. That was a correct pin on a
    correct decision — the base-14 faces are Latin and a Hindi report
    rendered into them is a page of question marks — and the decision has
    now been superseded rather than overturned. V1.8 built the two things
    the refusal named as missing: an embedded Devanagari font and a
    shaper.

    So the assertions move from "Hindi is refused" to "Hindi is
    RENDERED, and a script we still cannot shape is refused in the same
    way Hindi used to be". The second half matters: a release that
    removed the refusal without keeping it for the next unsupported
    script would have traded a documented limit for a silent one.
    """

    def test_a_hindi_report_now_renders_as_pdf(self):
        document = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary", language="hi"))
        data = render_pdf(document.to_dict())
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"/Subtype /Type0", data)
        self.assertIn(b"/Encoding /Identity-H", data)
        self.assertIn(b"/FontFile2", data)

    def test_the_hindi_pdf_embeds_a_subset_not_the_whole_face(self):
        document = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary", language="hi"))
        data = render_pdf(document.to_dict())
        full = os.path.getsize(os.path.join(
            ROOT, "app", "report", "fonts",
            "NotoSansDevanagari-Regular.ttf"))
        self.assertLess(len(data), full,
                        "the whole font would be larger than the report")

    def test_an_english_report_embeds_no_font_at_all(self):
        """
        Adding Hindi support must not make every PDF bigger. An English
        document never touches the Devanagari face, so it carries none.
        """
        document = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary", language="en"))
        data = render_pdf(document.to_dict())
        self.assertNotIn(b"/FontFile2", data)
        self.assertNotIn(b"/Identity-H", data)

    def test_the_same_report_renders_completely_as_html(self):
        markup = render_html(generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary",
                                          language="hi")).to_dict())
        self.assertIn('lang="hi"', markup)
        self.assertIn("कुण्डली", markup)

    def test_an_unshapeable_script_is_still_refused_by_name(self):
        """
        The refusal did not go away; its scope narrowed. Tamil has no
        bundled font and no shaper, so it is named rather than drawn as
        boxes — which is what V1.7 was protecting against.
        """
        document = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary",
                                          language="en")).to_dict()
        document["sections"][0]["blocks"].append(
            {"block": "paragraph",
             "text": "வணக்கம் உலகம் தமிழ் எழுத்து முறை சோதனை"})
        with self.assertRaises(PdfUnsupportedText) as caught:
            render_pdf(document)
        self.assertIn("refused", str(caught.exception))

    def test_the_service_still_turns_a_refusal_into_a_message(self):
        from app.errors import ReportGenerationError

        document = generate_report(
            self.record, natal=self.natal, prediction=self.prediction,
            preferences=ReportPreferences(mode="summary",
                                          language="en")).to_dict()
        document["sections"][0]["blocks"].append(
            {"block": "paragraph", "text": "வணக்கம் உலகம் தமிழ் எழுத்து சோதனை"})
        with self.assertRaises(PdfUnsupportedText):
            render_pdf(document)


if __name__ == "__main__":
    unittest.main()
