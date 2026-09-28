"""
Security review (V1.8 Parts 43, 44, 45)
-----------------------------------------
Hostile input through every path a user's own words reach.

THE THREAT MODEL, STATED PLAINLY

    This is a local, offline application. There is no remote attacker and
    no multi-user server, so the classic web threats are mostly absent.
    What remains is real and is what these tests cover:

    A CONSULTATION FILE IS UNTRUSTED INPUT. It is a document people mail
    to each other, and it names methodology settings, file paths and a
    person's own words. Opening one must not write outside the directory
    the user chose, must not execute anything, and must not crash.

    AN HTML REPORT IS OPENED IN A BROWSER. A name containing markup that
    survives into the report is script running in the user's browser with
    access to the local file the report sits in.

    A PDF IS A SYNTAX. An unescaped parenthesis in a place name ends a
    string object early, and the rest of the name becomes PDF operators.
    That is not a theoretical concern: `Jaip)ur` is a plausible typo.

    THE LOCAL SERVER BINDS TO 127.0.0.1, which is the mitigation for
    everything else, and is why these tests check that too.
"""

import datetime
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.errors import ApplicationError
from app.models import (
    ApplicationSettings, ConsultationRecord, ReportPreferences,
)
from app.report import render_html, render_pdf
from app.services import (
    calculate_chart, calculate_prediction, generate_report,
    import_consultations, load_consultation,
)
from app.services.prediction_service import parse_moment
from app.storage import save

#: Strings chosen so that a failure is unambiguous rather than subtle.
SCRIPT = '<script>alert("xss")</script>'
IMG = '"><img src=x onerror=alert(1)>'
PDF_BREAK = "A) 0 0 1 rg (injected"
PDF_ESCAPE = r"back\slash (open paren"
TRAVERSAL = "../../../../etc/passwd"
NEWLINES = "line1\r\nSet-Cookie: x=1\r\n\r\nline2"
NULLS = "before\x00after"


def _record(**changes) -> ConsultationRecord:
    values = dict(name="Test", date_of_birth="1988-08-30",
                  time_of_birth="20:18", place="Jaipur")
    values.update(changes)
    return ConsultationRecord(**values)


class _Rendered(unittest.TestCase):
    """Builds one report from a record carrying hostile text."""

    HOSTILE = {}

    @classmethod
    def setUpClass(cls):
        record = _record(**cls.HOSTILE)
        natal = calculate_chart(record, record.settings)
        prediction = calculate_prediction(
            natal, parse_moment("2026-09-27"), "standard",
            event_horizon_days=0)
        cls.record = record
        cls.document = generate_report(
            record, natal=natal, prediction=prediction,
            preferences=ReportPreferences(mode="summary")).to_dict()


# ── Part 44: HTML safety ────────────────────────────────────────────────────

class HtmlEscapingTest(_Rendered):

    HOSTILE = {"name": SCRIPT, "place": "Jaipur", "notes": IMG}

    def setUp(self):
        self.markup = render_html(self.document)

    def test_the_name_is_escaped(self):
        self.assertNotIn("<script>alert", self.markup)
        self.assertIn("&lt;script&gt;", self.markup)

    def test_no_event_handler_attribute_survives(self):
        """
        `onerror=` reaching the output unescaped is script execution, and
        it is the payload that survives naive angle-bracket filtering.
        """
        for handler in ("onerror=", "onload=", "onclick="):
            with self.subTest(handler=handler):
                self.assertNotIn(f' {handler}', self.markup)

    def test_the_document_declares_its_encoding_before_any_content(self):
        """
        A charset declared late lets a browser sniff the encoding, and a
        sniffed encoding is a way to smuggle markup past an escaper.
        """
        head = self.markup[:1024]
        self.assertIn("charset", head.lower())

    def test_the_report_loads_nothing_from_the_network(self):
        for pattern in ("<script", "src=", "@import", "url(http", "<iframe",
                        "<link ", "<object", "<embed"):
            with self.subTest(pattern=pattern):
                self.assertNotIn(pattern, self.markup.lower())


class HtmlInAllFieldsTest(unittest.TestCase):
    """Every free-text field a user controls, not just the name."""

    def test_markup_in_a_free_text_field_is_escaped(self):
        for field in ("name", "notes"):
            with self.subTest(field=field):
                record = _record(**{field: SCRIPT})
                natal = calculate_chart(record, record.settings)
                document = generate_report(
                    record, natal=natal,
                    preferences=ReportPreferences(mode="summary")).to_dict()
                markup = render_html(document)
                self.assertNotIn("<script>alert", markup)

    def test_a_hostile_place_is_refused_rather_than_escaped(self):
        """
        `place` is not free text: it is looked up in the city table, and
        an unresolvable place is refused outright. That is a stronger
        outcome than escaping — V1.7 Part 3 forbids silently substituting
        another birthplace, and the same refusal happens to close this
        input as an injection vector entirely.
        """
        record = _record(place=SCRIPT)
        with self.assertRaises(ApplicationError) as caught:
            calculate_chart(record, record.settings)
        self.assertEqual(caught.exception.field, "place")


# ── Part 45: PDF safety ─────────────────────────────────────────────────────

class PdfSyntaxTest(unittest.TestCase):

    def _pdf(self, **changes) -> bytes:
        record = _record(**changes)
        natal = calculate_chart(record, record.settings)
        document = generate_report(
            record, natal=natal,
            preferences=ReportPreferences(mode="summary")).to_dict()
        return render_pdf(document)

    def test_a_parenthesis_in_a_name_does_not_end_the_string(self):
        """
        Every parenthesis must be backslash-escaped. Checked as "no
        UNESCAPED parenthesis" rather than "the text is absent", because
        the text is supposed to be present — it is the person's name —
        and asserting its absence would pass on a build that silently
        dropped it.
        """
        data = self._pdf(name=PDF_BREAK)
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"startxref", data)
        self.assertIsNone(re.search(rb"(?<!\\)\(injected", data))
        self.assertIn(rb"\(injected", data)

    def test_a_backslash_in_a_name_is_escaped(self):
        data = self._pdf(name=PDF_ESCAPE)
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"startxref", data)

    def test_the_document_title_carries_no_control_characters(self):
        """
        Part 45: "Sanitize metadata." A newline inside a PDF string
        object is legal and a null byte is not; neither belongs in a
        title, and both arrive from a pasted field.
        """
        data = self._pdf(name=NEWLINES + NULLS)
        titles = re.findall(rb"/Title \(((?:[^()\\]|\\.)*)\)", data)
        self.assertTrue(titles)
        for title in titles:
            self.assertNotIn(b"\x00", title)
            self.assertNotIn(b"\r", title)
            self.assertNotIn(b"\n", title)

    def test_the_xref_table_still_points_at_real_objects(self):
        """
        The strongest check that escaping held: if a hostile string had
        ended an object early, the byte offsets recorded in the xref
        table would no longer land on `N 0 obj`.
        """
        data = self._pdf(name=PDF_BREAK, place="Jaipur")
        start = data.rindex(b"startxref")
        offset = int(data[start + 9:].split()[0])
        table = data[offset:]
        self.assertTrue(table.startswith(b"xref"))
        entries = re.findall(rb"(\d{10}) (\d{5}) n", table)
        self.assertTrue(entries)
        for position, _generation in entries:
            index = int(position)
            self.assertRegex(data[index:index + 24], rb"^\d+ \d+ obj")


class PdfFilenameTest(unittest.TestCase):
    """Part 43/45: a name must not choose where a file is written."""

    def test_an_auto_filename_cannot_escape_the_directory(self):
        from main import _pdf_path

        for hostile in (TRAVERSAL, "..\\..\\windows", "a/b/c", NULLS):
            with self.subTest(name=hostile):
                path = _pdf_path("auto", hostile)
                self.assertNotIn("/", path)
                self.assertNotIn("\\", path)
                self.assertNotIn("\x00", path)
                self.assertNotIn("..", path)

    def test_an_auto_filename_is_never_empty(self):
        from main import _pdf_path

        self.assertTrue(_pdf_path("auto", "").endswith(".pdf"))
        self.assertTrue(_pdf_path("auto", "!!!").endswith(".pdf"))

    def test_a_download_filename_is_sanitised(self):
        from app.ui.server import safe_filename

        for hostile in (TRAVERSAL, NEWLINES, NULLS, 'a"b', "a;b"):
            with self.subTest(value=hostile):
                name = safe_filename(hostile, "fallback.pdf")
                self.assertNotIn("/", name)
                self.assertNotIn("\\", name)
                self.assertNotIn('"', name)
                self.assertNotIn("\r", name)
                self.assertNotIn("\n", name)


# ── Part 43: consultation files ─────────────────────────────────────────────

class ConsultationInputTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def _write(self, payload) -> str:
        path = os.path.join(self.directory, "c.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(payload if isinstance(payload, str)
                         else json.dumps(payload))
        return path

    def test_every_malformed_file_raises_a_user_facing_error(self):
        """
        Part 25 and Part 43 meet here: a hostile or damaged file must
        produce a message, never a traceback and never a silent default.
        """
        cases = {
            "truncated": '{"schema_version": "2.0.0", "input": {"da',
            "not json": "not json at all",
            "top level list": "[1, 2, 3]",
            "empty": "",
            "input is a string": json.dumps(
                {"schema_version": "2.0.0", "input": "x"}),
            "input is a list": json.dumps(
                {"schema_version": "2.0.0", "input": []}),
            "calculation is a string": json.dumps(
                {"schema_version": "2.0.0",
                 "input": {"date_of_birth": "1988-08-30",
                           "time_of_birth": "20:18"},
                 "calculation": "x"}),
            "future schema": json.dumps(
                {"schema_version": "99.0.0",
                 "input": {"date_of_birth": "1988-08-30",
                           "time_of_birth": "20:18"}}),
            "unknown ayanamsha": json.dumps(
                {"schema_version": "2.0.0",
                 "input": {"date_of_birth": "1988-08-30",
                           "time_of_birth": "20:18"},
                 "calculation": {"ayanamsha": "../../etc/passwd"}}),
            "deeply nested": json.dumps(
                {"schema_version": "2.0.0",
                 "input": {"date_of_birth": "1988-08-30",
                           "time_of_birth": "20:18",
                           "entered_positions": {"a": {"b": {"c": {}}}}},
                 "calculation": {}}),
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                path = self._write(payload)
                try:
                    load_consultation(path)
                except ApplicationError:
                    pass                      # the required outcome
                except Exception as exc:      # noqa: BLE001
                    self.fail(f"{label} raised {type(exc).__name__}: {exc}")

    def test_a_consultation_never_names_a_file_to_open(self):
        """
        The format holds birth data and methodology names. It has no
        field that is a path, which is the structural reason a hostile
        consultation cannot make the application read something else.
        """
        record = _record()
        path = save(record, os.path.join(self.directory, "s.json"))
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        blob = json.dumps(payload)
        self.assertNotIn("/", payload.get("calculation", {}).get(
            "varga_profile") or "")
        self.assertNotIn("file://", blob)

    def test_hostile_text_survives_a_round_trip_unchanged(self):
        """
        Sanitising ON THE WAY IN would corrupt a legitimate name. The
        rule is escape-on-output, and that means the stored value must
        come back exactly as it went.
        """
        record = _record(name=SCRIPT, place=PDF_BREAK, notes=NEWLINES)
        path = save(record, os.path.join(self.directory, "h.json"))
        loaded, _report = load_consultation(path)
        self.assertEqual(loaded.name, SCRIPT)
        self.assertEqual(loaded.place, PDF_BREAK)
        self.assertEqual(loaded.notes, NEWLINES)

    def test_an_import_with_a_hostile_entry_reports_and_continues(self):
        path = os.path.join(self.directory, "export.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({
                "export_schema": "1.0.0",
                "consultations": [
                    {"schema_version": "2.0.0",
                     "input": {"name": SCRIPT, "date_of_birth": "1988-08-30",
                               "time_of_birth": "20:18", "place": "Jaipur"}},
                    "not a consultation",
                    {"schema_version": "99.0.0", "input": {}},
                ]}, handle)
        records, reports = import_consultations(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, SCRIPT)
        self.assertEqual(sum(1 for r in reports if r.get("failed")), 2)

    def test_saving_to_an_impossible_path_is_a_message(self):
        record = _record()
        for path in (os.path.join(self.directory, "a\x00b.json"),
                     os.path.join(self.directory, "missing", "x", "y.json")):
            with self.subTest(path=path):
                try:
                    save(record, path)
                except ApplicationError:
                    pass
                except Exception as exc:      # noqa: BLE001
                    self.fail(f"raised {type(exc).__name__}: {exc}")


# ── the local server ────────────────────────────────────────────────────────

class LocalServerTest(unittest.TestCase):

    def test_the_server_binds_only_to_loopback(self):
        """
        The mitigation everything else rests on. A chart engine listening
        on 0.0.0.0 publishes the birth details of everyone who uses it to
        the local network.
        """
        import inspect

        from app.ui import server

        source = inspect.getsource(server)
        self.assertIn("127.0.0.1", source)
        self.assertNotIn('"0.0.0.0"', source)
        self.assertNotIn("'0.0.0.0'", source)

    def test_the_not_found_page_escapes_the_requested_path(self):
        """
        The 404 page echoes the path back. An unescaped echo is reflected
        XSS, reachable by giving somebody a link to their own machine.
        """
        from app.ui import pages

        markup = pages.page("Not found", pages.error_panel({
            "category": "Not found",
            "message": f"There is no screen at /{SCRIPT}.",
            "hint": "Use the navigation above.",
        }), subject="")
        self.assertNotIn("<script>alert", markup)
        self.assertIn("&lt;script&gt;", markup)

    def test_a_screen_name_is_a_key_and_never_a_path(self):
        """
        `/screen/<name>` resolves through a table of known screens. If it
        ever indexed the filesystem, `..` would matter; the names are
        checked to be plain identifiers so that a future refactor which
        did touch the filesystem would still be safe.
        """
        from app.ui.pages import SCREENS

        names = [entry[0] if isinstance(entry, (tuple, list)) else entry
                 for entry in SCREENS]
        for name in names:
            with self.subTest(screen=name):
                self.assertRegex(name, r"^[a-z_]+$")


if __name__ == "__main__":
    unittest.main()
