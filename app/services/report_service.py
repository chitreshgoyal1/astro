"""
Report service (V1.7 Parts 2, 20, 21, 22)
===========================================
`generate_report` and `generate_pdf` — one call from a consultation to a
finished document.

WHAT THIS SERVICE ORCHESTRATES

    It calls the chart service, the prediction service and the
    interpretation renderer, draws the requested kundlis, and hands the
    results to the report builder. It computes nothing itself.

    The interpretation is rendered ONCE, at the requested mode, and that
    single document supplies every sentence in the report. Part 22: the
    modes must not duplicate interpretation logic, and the cheapest way to
    guarantee that is to have only one call that could produce a sentence.
"""

from __future__ import annotations

import datetime
from typing import Optional, Sequence

from ..errors import ReportGenerationError
from ..models import ApplicationSettings, ConsultationRecord, ReportPreferences
from ..report.builder import build_report_document
from ..report.pdf import PdfUnsupportedText
from ..report.pdf import render_pdf as _render_pdf
from ..visual import MARKER_LEGEND, render_chart, style_label
from .chart_service import calculate_chart, chart_visual_model
from .prediction_service import calculate_prediction, render_interpretation
from .release import release_warnings
from .settings_service import describe_methodology


def _charts(natal, preferences: ReportPreferences) -> list:
    """Render each requested varga as a Scene. Unknown vargas are refused."""
    charts = []
    for name in preferences.include_charts:
        try:
            model = chart_visual_model(
                natal, varga=name, detail=preferences.chart_detail,
                style=preferences.chart_style)
        except ValueError as exc:
            raise ReportGenerationError(
                f"The report asks for a {name} chart, which this "
                f"calculation does not carry.",
                detail=str(exc), field="include_charts") from exc
        charts.append({
            "name": name,
            "scene": render_chart(model),
            "caption": f"{model.title} — Lagna in {model.lagna_sign_name}",
            "convention": model.convention,
            "notes": list(model.notes),
        })
    return charts


def generate_report(consultation: ConsultationRecord,
                    settings: Optional[ApplicationSettings] = None,
                    preferences: Optional[ReportPreferences] = None,
                    moment=None,
                    natal=None,
                    prediction=None,
                    domains: Optional[Sequence[str]] = None,
                    generated: Optional[str] = None):
    """
    Build a ReportDocument for one consultation.

    `natal` and `prediction` may be supplied to reuse a calculation the UI
    already has on screen. When they are not, they are computed here with
    the same services, so a report and a screen never disagree.
    """
    settings = settings or consultation.settings or ApplicationSettings()
    preferences = preferences or consultation.report or ReportPreferences()

    natal = natal or calculate_chart(consultation, settings)
    if prediction is None:
        prediction = calculate_prediction(
            natal, moment=moment or datetime.datetime.now(),
            profile=settings.synthesis_profile, domains=domains)

    interpretation = render_interpretation(
        prediction, language=preferences.language, mode=preferences.mode,
        domains=domains)

    return build_report_document(
        natal=natal.snapshot,
        prediction=prediction.snapshot,
        interpretation=interpretation.to_dict(),
        charts=_charts(natal, preferences),
        mode=preferences.mode,
        language=preferences.language,
        methodology=describe_methodology(natal, settings),
        # V1.8 Part 48. A document produced under an experimental setting
        # says so, beside the findings, in the same place every other
        # reliability warning appears. The audit is derived from the
        # settings rather than declared, so a new experimental option
        # cannot be added without this picking it up.
        warnings=(tuple(release_warnings(settings))
                  + tuple(natal.warnings) + tuple(prediction.warnings)),
        chart_detail=preferences.chart_detail,
        chart_legend=MARKER_LEGEND,
        chart_style_label=style_label(preferences.chart_style),
        generated=generated,
        provenance={
            "chart_schema": natal.schema_version,
            "prediction_schema": prediction.schema_version,
            "interpretation_schema": interpretation.schema_version,
            "synthesis_profile": prediction.profile,
            "rule_profile": settings.rule_profile,
            "language": preferences.language,
            "analysed_moment": prediction.moment,
        })


def generate_html(consultation: ConsultationRecord,
                  settings: Optional[ApplicationSettings] = None,
                  preferences: Optional[ReportPreferences] = None,
                  path: Optional[str] = None,
                  **kwargs) -> str:
    """
    Build the document and render it as one self-contained HTML file.

    This is the Hindi delivery path. The PDF's Latin faces cannot print
    Devanagari and refuse to try; a browser supplies both the font and the
    shaping, so the HTML report is complete in every installed locale.
    """
    from ..report.html_report import render_html

    preferences = preferences or consultation.report or ReportPreferences()
    document = generate_report(consultation, settings, preferences, **kwargs)
    markup = render_html(document.to_dict(), preferences.language)
    if path:
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(markup)
        except OSError as exc:
            raise ReportGenerationError(
                f"The report could not be written to {path}.",
                detail=str(exc)) from exc
    return markup


def generate_pdf(consultation: ConsultationRecord,
                 settings: Optional[ApplicationSettings] = None,
                 preferences: Optional[ReportPreferences] = None,
                 path: Optional[str] = None,
                 **kwargs) -> bytes:
    """
    Build the document and render it to PDF bytes, optionally to a file.

    Returns the bytes either way, because the tests hash them and the UI
    serves them without touching the disk.
    """
    preferences = preferences or consultation.report or ReportPreferences()
    document = generate_report(consultation, settings, preferences, **kwargs)
    try:
        data = _render_pdf(document.to_dict(),
                           page_size=preferences.page_size)
    except PdfUnsupportedText as exc:
        raise ReportGenerationError(
            f"A PDF report cannot be produced in "
            f"'{preferences.language}': the PDF's Latin fonts cannot print "
            f"this script.",
            detail=str(exc),
            hint="Use the HTML report for this language. It is complete, "
                 "it prints, and the browser supplies the font.",
            field="language") from exc
    except ValueError as exc:
        raise ReportGenerationError(
            "The report could not be rendered to PDF.",
            detail=str(exc)) from exc
    if path:
        try:
            with open(path, "wb") as handle:
                handle.write(data)
        except OSError as exc:
            raise ReportGenerationError(
                f"The PDF could not be written to {path}.",
                detail=str(exc)) from exc
    return data
