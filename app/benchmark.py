"""
Pipeline benchmark (V1.7 Part 35)
===================================
Times each stage once and reports where the seconds go.

WHY A BENCHMARK AND NOT A PROFILER

    A profiler answers "which function is hot". This answers "which stage
    is slow", which is the question a user asks when a screen takes five
    seconds, and it is the question that decides whether the fix belongs in
    the engine or in how often the application calls it.

    The measurement is one run, not an average. These stages take tenths of
    a second to seconds; the noise is small relative to the differences
    that matter, and repeating a cold-cache ephemeris scan ten times would
    measure the cache rather than the scan.

WHAT THIS FOUND IN V1.7

    The transit event scan dominated everything else at 58 seconds, because
    the scanner asked for one graha at a time from a function that computes
    all nine, and four of the five scanned grahas sample the same instants.
    Caching those samples took it to 3.6 seconds with byte-identical
    events. See `engine/transits/query._positions_at`.
"""

from __future__ import annotations

import datetime
import time
from typing import Optional

from .models import ApplicationSettings, ConsultationRecord, ReportPreferences

#: Stages, in the order a report needs them.
STAGE_ORDER = ("startup", "chart", "vargas", "strength", "ashtakavarga",
               "sensitivity", "synthesis", "synthesis_no_scan",
               "transit_scan", "transit_range_query", "interpretation",
               "visuals", "report", "pdf", "report_en", "report_hi")

#: The stages a single pass through the pipeline actually performs. These and
#: only these sum to "end to end".
#:
#: V1.8 fixed a defect here. `total` was `sum(timings.values())`, which
#: added the diagnostic re-runs — vargas, strength, ashtakavarga and
#: sensitivity are re-timed individually to show how the chart stage divides
#: — so "end to end" was the sum of one pass plus several repeats of part of
#: it. The note under the table said the rows do not sum to the total while
#: the total was computed by summing them. V1.8 adding two more diagnostic
#: rows made the overcount large enough to notice.
PIPELINE_STAGES = ("chart", "synthesis", "interpretation", "visuals",
                   "report", "pdf")

#: Re-runs and derived figures. Shown, never summed.
DIAGNOSTIC_STAGES = ("startup", "vargas", "strength", "ashtakavarga",
                     "sensitivity", "synthesis_no_scan", "transit_scan",
                     "transit_range_query", "report_en", "report_hi")


def _timed(label: str, function, results: dict):
    start = time.perf_counter()
    value = function()
    results[label] = time.perf_counter() - start
    return value


def run_benchmark(record: Optional[ConsultationRecord] = None,
                  moment=None) -> dict:
    """
    Run the whole pipeline once, recording the cost of each stage.

    Returns a dict of stage name to seconds, plus the sizes that explain
    them — a 32-page report is slower than an 8-page one for a reason that
    is not a defect.
    """
    from engine.ephemeris import clear_vsop_cache, vsop_cache_stats
    from engine.transits.query import clear_position_cache
    from .report import render_pdf
    from .services import (
        calculate_chart, calculate_prediction, chart_visual_model,
        render_interpretation,
    )
    from .services.report_service import generate_report
    from .visual import render_chart, scene_to_svg

    record = record or ConsultationRecord(
        name="Benchmark", date_of_birth="1988-08-30", time_of_birth="20:18",
        place="Jaipur", settings=ApplicationSettings(),
        report=ReportPreferences(mode="technical"))
    moment = moment or datetime.datetime(2026, 9, 27, 12)

    # A cold cache is the honest starting point: a user opening the
    # application has one. Both caches, not just the scanner's — measuring
    # with a warm series cache would report a number no first run sees.
    clear_position_cache()
    clear_vsop_cache()

    timings: dict[str, float] = {}
    sizes: dict[str, int] = {}

    # Startup: importing the engine and the application, which is what a
    # user waits for before anything else happens. Measured by importing
    # a module chain that is NOT already loaded would be ideal and is not
    # possible in-process, so this measures re-resolution rather than
    # cold import and is labelled as a floor rather than a figure.
    def _startup():
        import importlib

        for name in ("engine.planets", "engine.features", "engine.synthesis",
                     "engine.interpretation", "app.report", "app.visual"):
            importlib.import_module(name)

    _timed("startup", _startup, timings)

    # The chart service computes vargas, strength, ashtakavarga and
    # sensitivity inside one call, so they are timed by re-running the
    # individual engine entry points rather than by splitting the service.
    natal = _timed("chart", lambda: calculate_chart(record, record.settings),
                   timings)
    objects = natal.engine_objects
    chart, features = objects["chart"], objects["features"]

    from engine.ashtakavarga import compute_ashtakavarga
    from engine.features import build_chart_features, parashari_profile
    from engine.sensitivity import analyse_birth_time
    from engine.strength import compute_shadbala

    varga_config = objects["varga_config"]
    _timed("vargas", lambda: build_chart_features(
        chart, varga_config=varga_config,
        aspect_profile=parashari_profile("parashari_like")), timings)
    _timed("strength", lambda: compute_shadbala(
        chart, features, birth=objects["birth_datetime"],
        varga_config=varga_config), timings)
    _timed("ashtakavarga", lambda: compute_ashtakavarga(chart), timings)

    # Part 49 asks for a transit RANGE query as its own figure. Three
    # months of the five slow grahas: the shape of query the timeline
    # screen makes, rather than the full year the synthesis scan runs.
    from engine.transits import get_transit_events_between

    clear_position_cache()
    clear_vsop_cache()
    _timed("transit_range_query", lambda: get_transit_events_between(
        moment, moment + datetime.timedelta(days=90),
        planets=("Guru", "Shani", "Rahu", "Ketu", "Mangal")), timings)

    location = objects["location"]
    _timed("sensitivity", lambda: analyse_birth_time(
        location.to_utc(objects["birth_datetime"]), location.latitude,
        location.longitude, varga_config=varga_config), timings)

    prediction = _timed(
        "synthesis",
        lambda: calculate_prediction(natal, moment=moment,
                                     profile="standard"), timings)

    # V1.8 Part 14 names two different targets, and one pipeline cannot
    # report both. The same synthesis is re-run with the transit event scan
    # disabled, because measurement showed the scan is essentially the
    # entire cost: everything else together is tens of milliseconds.
    #
    # The two runs differ ONLY in `event_candidates`, whose windows lose
    # their ingress-sharp edges. Domain results, evidence, gochara,
    # reliability and confidence are byte-identical, and a test asserts it.
    clear_position_cache()
    clear_vsop_cache()
    _timed("synthesis_no_scan",
           lambda: calculate_prediction(natal, moment=moment,
                                        profile="standard",
                                        event_horizon_days=0), timings)
    timings["transit_scan"] = max(
        0.0, timings["synthesis"] - timings["synthesis_no_scan"])
    document = _timed(
        "interpretation",
        lambda: render_interpretation(prediction, mode="technical"), timings)

    def draw():
        out = []
        for name in ("D1", "D9", "D10"):
            model = chart_visual_model(natal, varga=name)
            out.append(scene_to_svg(render_chart(model)))
        return out

    svgs = _timed("visuals", draw, timings)
    sizes["svg_bytes"] = sum(len(s) for s in svgs)

    report = _timed("report", lambda: generate_report(
        record, record.settings, record.report, natal=natal,
        prediction=prediction), timings)
    data = _timed("pdf", lambda: render_pdf(report.to_dict()), timings)

    # Part 49 wants the English and the Hindi report timed separately.
    # They differ by more than a factor of twenty, because one of them
    # shapes every glyph, and reporting a single "report" figure would
    # hide that entirely.
    def _language_report(language: str):
        document = generate_report(
            record, record.settings,
            ReportPreferences(mode=record.report.mode, language=language),
            natal=natal, prediction=prediction)
        return render_pdf(document.to_dict())

    english = _timed("report_en", lambda: _language_report("en"), timings)
    hindi = _timed("report_hi", lambda: _language_report("hi"), timings)
    sizes["pdf_bytes_en"] = len(english)
    sizes["pdf_bytes_hi"] = len(hindi)

    sizes["pdf_bytes"] = len(data)
    sizes["report_sections"] = len(report.sections)
    sizes["domains"] = len(document.domain_sections)
    sizes["event_candidates"] = len(
        prediction.snapshot.get("event_candidates") or [])
    sizes["vsop_cache_entries"] = vsop_cache_stats()["entries"]

    return {
        "timings": timings,
        "total": sum(seconds for stage, seconds in timings.items()
                     if stage in PIPELINE_STAGES),
        "pipeline_stages": list(PIPELINE_STAGES),
        "diagnostic_stages": list(DIAGNOSTIC_STAGES),
        "sizes": sizes,
        "moment": moment.isoformat(),
        "note": ("One cold run, both caches cleared first. The chart stage "
                 "includes the vargas, the strength and the sensitivity "
                 "scan; the three rows below it re-run those engine entry "
                 "points on their own to show how the chart stage divides, "
                 "so the indented rows are NOT counted in the total. "
                 "`synthesis_no_scan` "
                 "is the same synthesis with the transit event scan "
                 "disabled and `transit_scan` is the difference between "
                 "them — the two runs agree on every field except the "
                 "event-window edges."),
    }


def format_benchmark(result: dict) -> str:
    """The benchmark as a console table."""
    lines = ["", "  PIPELINE BENCHMARK", "  " + "─" * 52,
             f"  {'Stage':<18}{'Seconds':>10}{'Share':>10}"]
    total = sum(seconds for stage, seconds in result["timings"].items()
                if stage in PIPELINE_STAGES)
    for stage in STAGE_ORDER:
        if stage not in result["timings"]:
            continue
        seconds = result["timings"][stage]
        share = (f"{seconds / total * 100:5.1f}%"
                 if total and stage in PIPELINE_STAGES else "     —")
        indent = "  " if stage in DIAGNOSTIC_STAGES else ""
        lines.append(f"  {indent + stage:<18}{seconds:>10.3f}{share:>10}")
    lines.append("  " + "─" * 52)
    lines.append(f"  {'end to end':<18}{total:>10.3f}")
    lines.append("")
    for key, value in sorted(result["sizes"].items()):
        lines.append(f"  {key:<20}{value:>12,}")
    lines.append("")
    lines.append("  " + result["note"])
    lines.append("")
    return "\n".join(lines)
