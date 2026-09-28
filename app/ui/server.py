"""
Local application server (V1.7 Parts 1, 5, 33, 34, 36)
========================================================
A small HTTP server on loopback, serving the screens in a browser.

WHY A BROWSER AND NOT A DESKTOP TOOLKIT

    The application must run offline with no third-party dependency. Tk is
    not present in every Python build — it is absent from the interpreter
    this repository is developed against — and adding a GUI framework would
    add the first heavyweight dependency to a project that has one, an
    ephemeris used for validation.

    A browser is already installed, renders SVG natively, scales text
    properly, and brings a mature accessibility stack with it. The server
    binds to 127.0.0.1 and opens no outbound connection; nothing is
    published by running it.

STATE

    One consultation at a time, held in memory by `Application`. A chart is
    calculated once and reused across screens, so paging from Yogas to
    Vargas does not recompute an ephemeris. A prediction is recomputed when
    the moment or the profile changes, because those are what it depends
    on — and never mutated in place, so a settings change cannot alter a
    snapshot already shown (Part 30).

ERRORS

    Every handler funnels through `_safe`, which turns an ApplicationError
    into a rendered page and anything else into a generic one. A traceback
    reaches a user only in debug mode, which is off unless asked for
    (Part 33).
"""

from __future__ import annotations

import datetime
import http.server
import socketserver
import traceback
import urllib.parse
from typing import Optional

from ..errors import ApplicationError
from ..models import (
    ApplicationSettings, BirthTimePrecision, ConsultationRecord,
    ReportPreferences,
)
from . import pages

HOST = "127.0.0.1"
DEFAULT_PORT = 8713

#: Vargas offered in the explorer, in the engine's own order.
VARGA_ORDER = ("D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
               "D20", "D24", "D27", "D30", "D40", "D45", "D60")


class Application:
    """
    The consultation currently open, and the calculations for it.

    Deliberately not a web session: there is one user, on one machine, and
    inventing a session store would add a concept the application does not
    have.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.record: Optional[ConsultationRecord] = None
        self.settings = ApplicationSettings()
        self.preferences = ReportPreferences()
        self.natal = None
        self.prediction = None
        self.interpretation = None
        self.moment: Optional[datetime.datetime] = None
        self.notes: list[str] = []

    # ── calculation ────────────────────────────────────────────────────────
    def calculate(self, record: ConsultationRecord) -> None:
        from ..services import calculate_chart
        self.record = record
        self.settings = record.settings
        self.preferences = record.report
        self.natal = calculate_chart(record, self.settings)
        self.prediction = None
        self.interpretation = None
        self.moment = None

    def predict(self, moment=None, profile: Optional[str] = None,
                force: bool = False):
        """
        Synthesis for a moment, recomputed only when the inputs change.

        An omitted moment means "whatever is already loaded", not "now".
        Reading `now` on every request would give a different instant each
        time, so every screen would recompute a five-second synthesis and
        two screens could disagree about which moment they described.
        """
        from ..services import calculate_prediction
        from ..services.prediction_service import parse_moment

        wanted = profile or self.settings.synthesis_profile
        if moment is None and self.prediction is not None and not force:
            if self.prediction.profile == wanted:
                return self.prediction
            when = self.moment
        else:
            when = parse_moment(moment or datetime.datetime.now())

        unchanged = (self.prediction is not None and not force
                     and self.moment == when
                     and self.prediction.profile == wanted)
        if unchanged:
            return self.prediction
        self.prediction = calculate_prediction(self.natal, moment=when,
                                               profile=wanted)
        self.moment = when
        self.interpretation = None
        return self.prediction

    def interpret(self, mode: Optional[str] = None,
                  language: Optional[str] = None):
        from ..services import render_interpretation
        mode = mode or self.preferences.mode
        language = language or self.preferences.language
        key = (mode, language)
        if self.interpretation is not None \
                and getattr(self, "_interpretation_key", None) == key:
            return self.interpretation
        self.interpretation = render_interpretation(
            self.prediction, language=language, mode=mode)
        self._interpretation_key = key
        return self.interpretation

    # ── presentation helpers ───────────────────────────────────────────────
    def charts(self, names, detail: Optional[str] = None,
               style: Optional[str] = None) -> list:
        """Rendered SVG for each named varga, with what produced it."""
        from ..services import chart_visual_model
        from ..visual import render_chart, scene_to_svg

        detail = detail or self.preferences.chart_detail
        style = style or self.preferences.chart_style
        out = []
        for index, name in enumerate(names):
            model = chart_visual_model(self.natal, varga=name, detail=detail,
                                       style=style)
            scene = render_chart(model)
            out.append({
                "name": name,
                "svg": scene_to_svg(scene, element_id=f"kundli-{index}"),
                "caption": f"{model.title} — Lagna in "
                           f"{model.lagna_sign_name}",
                "convention": model.convention,
                "notes": list(model.notes),
            })
        return out

    @property
    def subject(self) -> str:
        return self.record.name if self.record else ""

    @property
    def ready(self) -> bool:
        return self.natal is not None


# ── request handling ─────────────────────────────────────────────────────────

#: Characters allowed in a download filename. Deliberately a whitelist.
#:
#: The value reaching Content-Disposition is built from a query parameter,
#: so a blacklist would be a list of the injection characters somebody had
#: already thought of. A quote closes the filename attribute and a CR/LF
#: pair ends the header and starts another one; both arrive from a URL the
#: user was given rather than one they typed.
_FILENAME_SAFE = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")


def safe_filename(value: str, fallback: str = "download.pdf") -> str:
    """A filename safe to put in a response header."""
    cleaned = "".join(ch if ch in _FILENAME_SAFE else "_" for ch in value)
    cleaned = cleaned.strip("._") or ""
    # A name that is only dots would still read as a path component.
    if not cleaned or set(cleaned) <= {"."}:
        return fallback
    return cleaned[:96]


class Handler(http.server.BaseHTTPRequestHandler):
    """Routes. One method per route, each returning markup or bytes."""

    server_version = "JyotishEngine/1.7"
    app: Application = None            # set by `serve`

    # Silence the default stderr logging: a request log interleaved with the
    # engine's own output makes both unreadable, and nothing here needs it.
    def log_message(self, fmt, *args):      # pragma: no cover - noise only
        pass

    # ── plumbing ───────────────────────────────────────────────────────────
    def _send(self, body, status: int = 200,
              content_type: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        # The application serves only itself and loads nothing remote.
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; "
                         "img-src data:; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _form(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}

    def _safe(self, handler) -> None:
        """Run a handler, rendering any error as a page rather than a trace."""
        try:
            handler()
        except ApplicationError as exc:
            self._send(pages.page(
                exc.category,
                pages.error_panel(exc.to_dict(debug=self.app.debug)),
                subject=self.app.subject), status=400)
        except Exception as exc:                # pragma: no cover - guard
            detail = traceback.format_exc() if self.app.debug else ""
            self._send(pages.page("Error", pages.error_panel({
                "category": "Unexpected error",
                "message": "Something went wrong that this application does "
                           "not have a specific message for. The calculation "
                           "was not completed.",
                "hint": "Run with --debug to see the technical detail.",
                "detail": detail,
            }), subject=self.app.subject), status=500)

    # ── routes ─────────────────────────────────────────────────────────────
    def do_GET(self):                   # noqa: N802 - stdlib naming
        self._safe(self._route_get)

    def do_POST(self):                  # noqa: N802 - stdlib naming
        self._safe(self._route_post)

    def _route_get(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = {k: v[0] for k, v in
                 urllib.parse.parse_qs(parsed.query).items()}

        if path == "/":
            return self._send(self._form_page())
        if path == "/report.pdf":
            return self._report_pdf(query)
        if path.startswith("/screen/"):
            return self._screen(path[len("/screen/"):], query)
        if path == "/chart.svg":
            return self._chart_svg(query)
        self._send(pages.page("Not found", pages.error_panel({
            "category": "Not found",
            "message": f"There is no screen at {parsed.path}.",
            "hint": "Use the navigation above.",
        }), subject=self.app.subject), status=404)

    def _route_post(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.rstrip("/") == "/calculate":
            return self._calculate(self._form())
        self._send("", status=404)

    # ── route bodies ───────────────────────────────────────────────────────
    def _form_page(self, error=None, values=None) -> str:
        from ..services import available_options
        return pages.consultation_form(available_options(), values or {},
                                       error=error)

    def _calculate(self, form: dict) -> None:
        from ..services import validate_settings

        settings = ApplicationSettings(
            ayanamsha=form.get("ayanamsha") or "lahiri",
            node=form.get("node") or "true",
            house_system=form.get("house_system") or "whole_sign",
            rule_profile=form.get("rule_profile") or "parashari",
            node_aspects=form.get("node_aspects") or "parashari_like",
            synthesis_profile=form.get("synthesis_profile") or "standard",
            language=form.get("language") or "en")
        validate_settings(settings)

        try:
            precision = BirthTimePrecision(
                form.get("birth_time_precision")
                or BirthTimePrecision.EXACT_TO_MINUTE.value)
        except ValueError:
            precision = BirthTimePrecision.UNKNOWN

        record = ConsultationRecord(
            name=form.get("name") or "Unknown",
            date_of_birth=form.get("date_of_birth") or "",
            time_of_birth=form.get("time_of_birth") or "",
            place=form.get("place") or "",
            precision=precision,
            latitude=form.get("latitude") or None,
            longitude=form.get("longitude") or None,
            timezone_name=form.get("timezone") or None,
            utc_offset=form.get("utc_offset") or None,
            settings=settings,
            report=ReportPreferences(
                mode=form.get("report_mode") or "detailed",
                language=settings.language))
        self.app.calculate(record)
        self._redirect("/screen/overview")

    def _pdf_actions(self) -> list:
        return pages.pdf_actions(self.app.preferences.language)

    def _screen(self, name: str, query: dict) -> None:
        app = self.app
        if not app.ready:
            return self._redirect("/")

        natal = app.natal.snapshot
        pdf = self._pdf_actions()
        if name == "overview":
            app.predict(query.get("moment"))
            return self._send(pages.overview(
                natal, app.prediction.snapshot, app.charts(["D1"]),
                app.subject, actions=pdf))

        if name == "chart":
            from ..visual import MARKER_LEGEND, IMPLEMENTED_STYLES
            from ..visual.styles import style_note
            detail = query.get("detail", app.preferences.chart_detail)
            style = query.get("style", app.preferences.chart_style)
            if style not in IMPLEMENTED_STYLES:
                style = app.preferences.chart_style
            return self._send(pages.chart_screen(
                natal, app.charts(["D1", "D9", "D10"], detail, style),
                app.subject, detail=detail, legend=MARKER_LEGEND,
                style=style, style_note=style_note(style), actions=pdf))

        if name == "vargas":
            varga = query.get("varga", "D9").upper()
            if varga not in VARGA_ORDER:
                varga = "D9"
            return self._send(pages.vargas_screen(
                natal, app.charts([varga]), app.subject, selected=varga,
                available=VARGA_ORDER, actions=pdf))

        if name == "strength":
            return self._send(pages.strength_screen(natal, app.subject,
                                                     actions=pdf))

        if name == "yogas":
            return self._send(pages.yogas_screen(natal, app.subject,
                                                  actions=pdf))

        if name == "dasha":
            app.predict(query.get("moment"))
            return self._send(pages.dasha_screen(
                natal, app.prediction.snapshot, app.subject, actions=pdf))

        if name == "transits":
            prediction = app.predict(query.get("moment"))
            events = (prediction.engine_objects or {}).get("events", [])
            return self._send(pages.transits_screen(
                natal, prediction.snapshot, app.subject,
                moment=prediction.moment, events=events, actions=pdf))

        if name == "domains":
            return self._domains(query, pdf=pdf)

        if name == "timeline":
            return self._timeline(query, pdf=pdf)

        if name == "reliability":
            prediction = app.predict(query.get("moment"))
            return self._send(pages.reliability_screen(
                natal, prediction.snapshot, app.natal.warnings, app.subject,
                actions=pdf))

        if name == "methodology":
            from ..services import describe_methodology
            return self._send(pages.methodology_screen(
                describe_methodology(app.natal, app.settings), app.subject,
                actions=pdf))

        self._send(pages.page("Not found", pages.error_panel({
            "category": "Not found",
            "message": f"There is no screen called '{name}'.",
        }), subject=app.subject), status=404)

    def _domains(self, query: dict, pdf=None) -> None:
        from ..services import available_options
        app = self.app
        profile = query.get("profile", app.settings.synthesis_profile)
        prediction = app.predict(query.get("moment"), profile=profile)
        interpretation = app.interpret(mode="detailed")
        profiles = available_options()["synthesis_profile"]["values"]
        self._send(pages.domains_screen(
            interpretation.to_dict(), prediction.snapshot, app.subject,
            profile=profile, profiles=profiles, actions=pdf))

    def _timeline(self, query: dict, pdf=None) -> None:
        from ..services import timeline_candidates
        app = self.app
        prediction = app.predict(query.get("moment"))
        wanted = query.get("domain")
        selected = [] if not wanted or wanted == "(all)" else [wanted]
        rows = timeline_candidates(prediction, domains=selected or None)
        every = sorted({r["domain"] for r
                        in timeline_candidates(prediction)})
        self._send(pages.timeline_screen(rows, app.subject, domains=every,
                                         selected=selected, actions=pdf))

    def _chart_svg(self, query: dict) -> None:
        app = self.app
        if not app.ready:
            return self._send("", status=404)
        from ..services import chart_visual_model
        from ..visual import render_chart
        from ..visual.svg import scene_to_svg_document

        from ..visual import IMPLEMENTED_STYLES

        varga = query.get("varga", "D1").upper()
        detail = query.get("detail", "STANDARD")
        style = query.get("style", app.preferences.chart_style)
        if style not in IMPLEMENTED_STYLES:
            style = app.preferences.chart_style
        model = chart_visual_model(app.natal, varga=varga, detail=detail,
                                   style=style)
        self._send(scene_to_svg_document(render_chart(model)),
                   content_type="image/svg+xml; charset=utf-8")

    def _report_pdf(self, query: dict) -> None:
        from ..services import generate_pdf
        app = self.app
        if not app.ready:
            return self._redirect("/")
        mode = query.get("mode", app.preferences.mode)
        preferences = ReportPreferences(
            mode=mode, language=query.get("language",
                                          app.preferences.language),
            page_size=app.preferences.page_size,
            chart_detail=app.preferences.chart_detail,
            chart_style=app.preferences.chart_style)
        prediction = app.predict(query.get("moment"))
        data = generate_pdf(app.record, app.settings, preferences,
                            natal=app.natal, prediction=prediction)
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(len(data)))
        self.send_header(
            "Content-Disposition",
            f'inline; filename="{safe_filename(f"jyotish_{mode}.pdf")}"')
        self.end_headers()
        self.wfile.write(data)


class _Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(port: int = DEFAULT_PORT, host: str = HOST, debug: bool = False,
          record: Optional[ConsultationRecord] = None) -> None:
    """
    Run the application until interrupted.

    Binds to loopback only. A chart contains a person's birth time and
    place; serving it on 0.0.0.0 would publish that to the local network,
    which is not something a user asked for by typing a birth date.
    """
    application = Application(debug=debug)
    if record is not None:
        application.calculate(record)
    Handler.app = application

    with _Server((host, port), Handler) as httpd:
        print(f"  Jyotish Engine — http://{host}:{port}/")
        print("  Loopback only. Nothing is sent anywhere. Ctrl-C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Stopped.")
