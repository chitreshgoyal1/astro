"""
The application interface (V1.7 Parts 5, 9-19, 33, 34, 36, 37)
================================================================
Every screen, rendered; the routes that serve them; and the things a
screen must never do.

HOW THESE TESTS WORK

    A real server is started on loopback and the pages are fetched over
    HTTP. Calling the page functions directly would test the markup and
    skip the routing, the error handling and the state management, which
    is where the interesting failures are — a screen that recomputes a
    five-second synthesis on every request looks identical in its markup.

WHAT THEY CHECK FOR

    That each screen shows what Part 5's list says it shows; that warnings
    are in the flow rather than in a footnote (Part 19); that silence is
    rendered rather than skipped (Part 16); that no ordinal band is turned
    into a number (Part 17); and that the page is usable without colour
    and without sight (Part 36).
"""

from __future__ import annotations

import datetime
import os
import re
import sys
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import ConsultationRecord
from app.ui import pages
from app.ui.server import HOST, Application, Handler, _Server

PORT = 8791
BASE = f"http://{HOST}:{PORT}"

FORM = {
    "name": "Jaipur 1988", "date_of_birth": "1988-08-30",
    "time_of_birth": "20:18", "place": "Jaipur",
    "birth_time_precision": "EXACT_TO_MINUTE", "ayanamsha": "lahiri",
    "node": "true", "house_system": "whole_sign",
    "rule_profile": "parashari", "node_aspects": "parashari_like",
    "synthesis_profile": "standard", "language": "en",
    "report_mode": "detailed",
}


def _get(path: str) -> tuple[int, str]:
    with urllib.request.urlopen(BASE + path) as response:
        return response.status, response.read().decode("utf-8")


def _get_bytes(path: str) -> tuple[int, bytes]:
    with urllib.request.urlopen(BASE + path) as response:
        return response.status, response.read()


#: One server, one chart, for the whole module.
#
# Per-class setup would bind the same port fourteen times and recompute
# the chart fourteen times. `setUpModule` is the right scope: the screens
# are read-only views of one consultation, which is also how the
# application itself works.
_STATE: dict = {}


def setUpModule():
    application = Application(debug=False)
    Handler.app = application
    server = _Server((HOST, PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    data = urllib.parse.urlencode(FORM).encode()
    with urllib.request.urlopen(
            urllib.request.Request(BASE + "/calculate", data=data)) as r:
        calculated_url = r.url
    # Pin the analysed moment so screens do not drift with the clock.
    application.predict(datetime.datetime(2026, 9, 27, 12))
    _STATE.update(application=application, server=server,
                  calculated_url=calculated_url)


def tearDownModule():
    server = _STATE.get("server")
    if server is not None:
        server.shutdown()
        server.server_close()


class _Served(unittest.TestCase):
    """A view onto the module's single server."""

    @property
    def application(self) -> Application:
        return _STATE["application"]

    @property
    def server(self):
        return _STATE["server"]

    @property
    def calculated_url(self) -> str:
        return _STATE["calculated_url"]


# ── Part 3: the form ─────────────────────────────────────────────────────────

class ConsultationFormTest(_Served):

    def test_the_form_asks_for_everything_part_3_lists(self):
        status, html = _get("/")
        self.assertEqual(status, 200)
        for field in ("name", "date_of_birth", "time_of_birth", "place",
                      "latitude", "longitude", "timezone",
                      "birth_time_precision"):
            with self.subTest(field=field):
                self.assertIn(f'id="{field}"', html)

    def test_advanced_settings_are_present_and_show_their_defaults(self):
        """
        Part 3: normal users should not need to understand these, and a
        user who does should see in one place what produced their chart.
        Hiding a default behind the word "automatic" fails both.
        """
        _status, html = _get("/")
        self.assertIn("Advanced methodology settings", html)
        for field in ("ayanamsha", "node", "house_system", "rule_profile",
                      "synthesis_profile", "language"):
            with self.subTest(field=field):
                self.assertIn(f'id="{field}"', html)
        self.assertIn("Default: lahiri", html)

    def test_every_control_has_a_bound_label(self):
        """Part 36: an unlabelled control is unusable with a screen reader."""
        _status, html = _get("/")
        for field_id in re.findall(r'<(?:input|select)[^>]*id="([^"]+)"',
                                   html):
            with self.subTest(field=field_id):
                self.assertIn(f'for="{field_id}"', html)

    def test_the_form_posts_to_a_calculation(self):
        self.assertTrue(self.calculated_url.endswith("/screen/overview"))


# ── Part 5: the screens ──────────────────────────────────────────────────────

class ScreenTest(_Served):

    def test_every_screen_in_the_navigation_renders(self):
        for name, label in pages.SCREENS:
            with self.subTest(screen=name):
                status, html = _get(f"/screen/{name}")
                self.assertEqual(status, 200)
                self.assertIn("<main", html)
                self.assertIn(label, html)

    def test_the_current_screen_is_marked_for_assistive_technology(self):
        for name, _label in pages.SCREENS:
            with self.subTest(screen=name):
                _status, html = _get(f"/screen/{name}")
                self.assertIn(f'href="/screen/{name}" aria-current="page"',
                              html)

    def test_every_page_offers_a_skip_link(self):
        _status, html = _get("/screen/overview")
        self.assertIn('href="#content" class="skip"', html)
        self.assertIn('id="content"', html)

    def test_an_unknown_screen_is_a_404_with_a_message(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            _get("/screen/horoscope")
        self.assertEqual(caught.exception.code, 404)
        body = caught.exception.read().decode("utf-8")
        self.assertIn("no screen called", body)

    def test_a_normal_error_shows_no_traceback(self):
        """Part 33: technical detail is debug-mode only."""
        with self.assertRaises(urllib.error.HTTPError) as caught:
            _get("/screen/nonsense")
        body = caught.exception.read().decode("utf-8")
        self.assertNotIn("Traceback", body)
        self.assertNotIn("File \"", body)


class PlanetTableTest(_Served):

    def test_the_table_carries_every_column_part_9_lists(self):
        _status, html = _get("/screen/chart")
        for column in ("Graha", "Sign", "Degree", "House", "Nakshatra",
                       "Pada", "Retrograde".replace("Retrograde", "State"),
                       "Dignity", "Shadbala", "D9", "D10"):
            with self.subTest(column=column):
                self.assertIn(f">{column}</th>", html)

    def test_the_shadbala_column_says_it_is_a_ratio(self):
        _status, html = _get("/screen/chart")
        self.assertIn("ratio, not a score and not a probability", html)

    def test_the_chart_is_inline_svg_with_a_description(self):
        _status, html = _get("/screen/chart")
        self.assertIn("<svg", html)
        self.assertIn('role="img"', html)
        self.assertIn("<desc", html)


class VargaExplorerTest(_Served):

    def test_every_varga_can_be_selected(self):
        from app.ui.server import VARGA_ORDER
        for varga in VARGA_ORDER:
            with self.subTest(varga=varga):
                status, html = _get(f"/screen/vargas?varga={varga}")
                self.assertEqual(status, 200)
                self.assertIn(f"{varga} placements", html)

    def test_the_active_convention_is_shown(self):
        _status, html = _get("/screen/vargas?varga=D30")
        self.assertIn("Convention", html)
        self.assertIn("Methodology", html)

    def test_birth_time_sensitivity_is_visible_on_the_chart(self):
        """
        Part 10: if the chart is birth-time sensitive, show it. The D60
        Lagna of this chart moves inside the recorded precision.
        """
        _status, html = _get("/screen/vargas?varga=D60")
        self.assertIn("D60 Lagna changes", html)
        self.assertIn("callout warning", html)

    def test_an_unknown_varga_falls_back_without_pretending(self):
        _status, html = _get("/screen/vargas?varga=D11")
        self.assertIn("D9 placements", html)


class StrengthScreenTest(_Served):

    def test_total_required_and_ratio_are_shown(self):
        _status, html = _get("/screen/strength")
        for column in ("Total (rupa)", "Required (rupa)", "Ratio"):
            with self.subTest(column=column):
                self.assertIn(column, html)

    def test_the_six_components_expand(self):
        _status, html = _get("/screen/strength")
        for component in ("Sthana Bala", "Dig Bala", "Kala Bala",
                          "Chesta Bala", "Naisargika Bala", "Drik Bala"):
            with self.subTest(component=component):
                self.assertIn(component, html)

    def test_approximated_components_are_flagged(self):
        """
        Part 12: clearly flag components whose methodology is not fully
        source-validated. The engine marks them; the screen must not
        swallow the mark.
        """
        _status, html = _get("/screen/strength")
        self.assertIn("not fully source-validated", html)
        # The apostrophe is escaped in the markup, which is the point of
        # escaping it; asserting on the raw form would pass only if the
        # value had reached the page unescaped.
        self.assertIn("not the text&#x27;s number", html)


class YogaScreenTest(_Served):

    def test_yogas_are_grouped_by_status(self):
        _status, html = _get("/screen/yogas")
        self.assertTrue(any(label in html for label in
                            ("Strong", "Formed", "Weakened", "Cancelled")))

    def test_conditions_and_validation_status_expand(self):
        _status, html = _get("/screen/yogas")
        self.assertIn("Conditions matched", html)
        self.assertIn("Source validation", html)
        self.assertIn("Rule profile", html)

    def test_the_engine_score_is_not_presented_as_a_probability(self):
        """Part 11: do not show software score as probability."""
        _status, html = _get("/screen/yogas")
        self.assertIn("not a probability", html)
        self.assertIn("How far the RULE has been traced", html)


class DashaScreenTest(_Served):

    def test_all_three_levels_are_reachable(self):
        _status, html = _get("/screen/dasha")
        self.assertIn("mahadasha", html.lower())
        self.assertIn("Antardasha", html)
        self.assertIn("Pratyantardasha", html)

    def test_the_running_period_is_marked(self):
        _status, html = _get("/screen/dasha")
        self.assertIn("running", html)

    def test_the_timeline_generates_no_interpretation(self):
        """
        Part 14: do not generate new interpretations inside the timeline
        component. It shows periods and boundaries and says where the
        meaning is decided.
        """
        _status, html = _get("/screen/dasha")
        self.assertIn("decided on the Life Areas screen", html)


class TransitScreenTest(_Served):

    def test_both_reference_frames_are_shown(self):
        _status, html = _get("/screen/transits")
        self.assertIn("House from Lagna", html)
        self.assertIn("House from Chandra", html)

    def test_a_date_can_be_chosen(self):
        status, html = _get("/screen/transits?moment=2027-01-15")
        self.assertEqual(status, 200)
        self.assertIn("2027", html)

    def test_facts_are_kept_apart_from_synthesis(self):
        """Part 15: keep FACTS separate from synthesis interpretation."""
        _status, html = _get("/screen/transits")
        self.assertIn("astronomical fact", html)
        self.assertIn("Nothing here says what a transit means", html)


class LifeAreaScreenTest(_Served):

    def test_all_seventeen_domains_are_rendered(self):
        _status, html = _get("/screen/domains")
        from engine.synthesis.domains import DOMAINS
        for domain in DOMAINS:
            with self.subTest(domain=domain.value):
                self.assertIn(f'id="{domain.value}"', html)

    def test_silence_is_rendered_with_its_reason(self):
        """
        Part 16: if strict mode has insufficient evidence, do not
        fabricate an interpretation. Omitting the section instead would
        make an absence of evidence look like an absence of the question.
        """
        _status, html = _get("/screen/domains?profile=strict")
        self.assertIn("Nothing reported", html)
        self.assertIn("RELATIONSHIPS", html)

    def test_the_profile_can_be_changed_and_changes_what_is_admitted(self):
        _status, strict = _get("/screen/domains?profile=strict")
        _status, standard = _get("/screen/domains?profile=standard")
        self.assertNotEqual(strict, standard)
        self.assertIn("Excluded by this profile", strict)

    def test_every_evidence_layer_has_a_heading(self):
        _status, html = _get("/screen/domains")
        for heading in ("Natal foundation", "Supporting factors",
                        "Challenging factors", "Transit triggers"):
            with self.subTest(heading=heading):
                self.assertIn(heading, html)


class TimelineScreenTest(_Served):

    def test_windows_are_drawn_with_a_text_equivalent(self):
        """Part 36: a chart must be accompanied by a textual equivalent."""
        _status, html = _get("/screen/timeline")
        if "class=\"timeline\"" not in html:
            self.skipTest("this chart produced no candidates")
        self.assertIn('role="img"', html)
        self.assertIn("aria-label", html)

    def test_activation_is_never_converted_to_a_number(self):
        """
        Part 17. The bar's length is the window and its mark is the peak.
        Nothing about it is scaled by activation, because a longer bar
        for STRONGLY_ACTIVE would be a probability drawn as a picture.
        """
        _status, html = _get("/screen/timeline")
        self.assertIn("not a forecast", html)
        self.assertIn("ordinal bands", html)
        for badge in re.findall(r'<span class="badge[^"]*">([^<]+)</span>',
                                html):
            with self.subTest(badge=badge):
                self.assertFalse(re.fullmatch(r"[\d.]+%?", badge.strip()))

    def test_filtering_is_offered_per_area(self):
        _status, html = _get("/screen/timeline")
        self.assertIn('name="domain"', html)
        self.assertIn("never what was calculated", html)


class ReliabilityScreenTest(_Served):

    def test_warnings_are_in_the_flow_and_not_in_a_footnote(self):
        """Part 19: do not hide warnings in footnotes only."""
        _status, html = _get("/screen/reliability")
        self.assertIn("callout", html)
        self.assertIn("Unstable within the birth-time uncertainty", html)

    def test_the_four_claims_are_restated(self):
        _status, html = _get("/screen/reliability")
        self.assertIn("Four separate claims", html)
        self.assertIn("none is evidence for another", html)

    def test_birth_time_precision_is_shown_in_words(self):
        _status, html = _get("/screen/reliability")
        self.assertIn("Exact to the minute", html)


class MethodologyScreenTest(_Served):

    def test_every_setting_part_18_lists_is_shown(self):
        _status, html = _get("/screen/methodology")
        for label in ("Ayanamsha", "Lunar node", "Rashi house system",
                      "Bhava system", "Varga profile", "Rule profile",
                      "Source registry", "Chart schema"):
            with self.subTest(label=label):
                self.assertIn(label, html)

    def test_the_claim_separation_is_shown_to_the_user(self):
        _status, html = _get("/screen/methodology")
        self.assertIn("Computationally tested", html)
        self.assertIn("Tradition source validated", html)


# ── routes that are not screens ──────────────────────────────────────────────

class AssetRouteTest(_Served):

    def test_a_chart_can_be_fetched_as_a_standalone_svg(self):
        status, body = _get_bytes("/chart.svg?varga=D9")
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b"<?xml"))
        import xml.etree.ElementTree as ET
        ET.fromstring(body.decode("utf-8"))

    def test_a_pdf_can_be_fetched(self):
        status, body = _get_bytes("/report.pdf?mode=summary")
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b"%PDF"))

    def test_the_stylesheet_is_inlined_and_not_fetched(self):
        """Part 34: a page that waits on a network request is a page that
        does not load offline."""
        _status, html = _get("/screen/overview")
        self.assertIn("<style>", html)
        self.assertNotIn("<link rel=\"stylesheet\"", html)


# ── state ────────────────────────────────────────────────────────────────────

class ApplicationStateTest(_Served):

    def test_a_chart_is_calculated_once_and_reused(self):
        """
        Paging from Yogas to Vargas must not recompute an ephemeris.
        Identity is the check: a recalculation would produce a new object.
        """
        before = self.application.natal
        _get("/screen/yogas")
        _get("/screen/vargas")
        _get("/screen/strength")
        self.assertIs(self.application.natal, before)

    def test_a_prediction_is_reused_until_its_inputs_change(self):
        before = self.application.prediction
        _get("/screen/overview")
        _get("/screen/dasha")
        self.assertIs(self.application.prediction, before)

    def test_changing_the_profile_recomputes_and_does_not_mutate(self):
        """
        Part 30: avoid mutating snapshots when settings change. A new
        profile produces a NEW result; the old snapshot is untouched.
        """
        original = self.application.prediction
        original_snapshot = original.snapshot
        _get("/screen/domains?profile=strict")
        self.assertIsNot(self.application.prediction, original)
        self.assertEqual(original.snapshot, original_snapshot)
        self.assertEqual(original.snapshot["methodology_profile"],
                         "standard")
        # Restore, so later tests in this class see the pinned moment.
        self.application.predict(datetime.datetime(2026, 9, 27, 12),
                                 profile="standard")

    def test_the_server_binds_to_loopback_only(self):
        """
        A chart contains a birth time and place. Serving it on 0.0.0.0
        would publish that to the local network, which is not something a
        user asked for by typing a birth date.
        """
        self.assertEqual(HOST, "127.0.0.1")
        self.assertEqual(self.server.server_address[0], "127.0.0.1")


# ── markup helpers ───────────────────────────────────────────────────────────

class HtmlHelperTest(unittest.TestCase):

    def test_values_are_escaped(self):
        from app.ui.html import tag
        rendered = str(tag("p", "<script>alert(1)</script>"))
        self.assertNotIn("<script>alert", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_raw_is_the_only_way_past_escaping(self):
        from app.ui.html import Raw, tag
        self.assertIn("<b>x</b>", str(tag("p", Raw("<b>x</b>"))))

    def test_the_element_name_cannot_be_shadowed_by_an_attribute(self):
        """
        `name` and `id` are both HTML attributes a caller passes by
        keyword. Before the element name was made positional-only this
        raised a TypeError at the first `<input name="...">`.
        """
        from app.ui.html import void
        rendered = str(void("input", name="dob", id="dob"))
        self.assertIn('name="dob"', rendered)
        self.assertIn('id="dob"', rendered)

    def test_a_badge_always_prints_its_word(self):
        from app.ui.html import badge
        rendered = str(badge("STRONGLY_ACTIVE", "strong"))
        self.assertIn("strongly active", rendered)

    def test_a_table_uses_scoped_header_cells(self):
        from app.ui.html import table
        rendered = str(table(("A", "B"), [("1", "2")]))
        self.assertIn('<th scope="col"', rendered)


if __name__ == "__main__":
    unittest.main()
