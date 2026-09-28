"""
Prediction service (V1.7 Parts 1, 2, 16, 17)
==============================================
`calculate_prediction` and `render_interpretation` — the V1.5 synthesis and
the V1.6 interpretation behind two calls.

WHAT THIS SERVICE IS NOT ALLOWED TO DO

    It does not decide whether a domain is active, how confident an
    assessment is, which evidence counts, or what any of it means. Those are
    engine answers and they arrive already made.

    It also does not re-render. The Life Area screen, the timeline, the PDF
    and the CLI all read the SAME InterpretationDocument; there is no
    "shorter version for the UI" anywhere in this layer, because a second
    phrasing path is a second interpretation engine with extra steps.

THE ONE JUDGEMENT CALL MADE HERE

    How far to scan for transit events when bounding a timing window. The
    scan bisects every graha, so scanning an 18-year Rahu antardasha in full
    would take minutes to no purpose. The horizon is capped at a year either
    side, and only the slow grahas and the boundary-relevant event kinds are
    scanned. This affects how TIGHT a window is, never whether the domain is
    activated or what is said about it — the same policy the CLI has used
    since V1.5, kept in one place instead of two.
"""

from __future__ import annotations

import datetime
from typing import Optional, Sequence

from engine.interpretation import ReportMode, build_interpretation
from engine.interpretation.renderer import (
    MissingTemplateKey, TemplateError, UnsupportedLocale,
)
from engine.synthesis import (
    SynthesisProfile, build_prediction_snapshot, build_reliability,
    event_candidates, synthesise,
)
from engine.transits.calculator import get_transit_snapshot
from engine.transits.query import get_transit_events_between

from ..errors import (
    ApplicationError, InvalidBirthDataError, MethodologyError,
    TemplateUnavailableError, UnsupportedLanguageError,
)
from ..models import PredictionResult

#: How far either side of the queried moment to look for transit events.
EVENT_SCAN_HORIZON = datetime.timedelta(days=365)

#: Only grahas slow enough to bound a window measured in months. Chandra
#: changes rashi every 2.3 days, so scanning for its ingresses costs more
#: than everything else combined and narrows nothing.
EVENT_SCAN_PLANETS = ("Guru", "Shani", "Rahu", "Ketu", "Mangal")

EVENT_SCAN_KINDS = ("sign_ingress", "station_retrograde", "station_direct",
                    "exact_conjunction")


def parse_moment(value) -> datetime.datetime:
    """
    Read a date or date-time from the UI or the command line.

    A bare date means midday, not midnight. The dasha stack and the transit
    positions are both continuous, and midnight sits on a day boundary where
    a reader is most likely to be surprised by which side of an ingress the
    answer fell.
    """
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day, 12)
    text = str(value or "").strip()
    for fmt, midday in (("%Y-%m-%dT%H:%M", False), ("%Y-%m-%d %H:%M", False),
                        ("%Y-%m-%d", True)):
        try:
            parsed = datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.replace(hour=12) if midday else parsed
    raise InvalidBirthDataError(
        f"'{text}' is not a date this application can read. Use YYYY-MM-DD "
        f"or YYYY-MM-DDTHH:MM.", field="moment")


def calculate_prediction(natal,
                         moment=None,
                         profile: Optional[str] = None,
                         domains: Optional[Sequence[str]] = None,
                         include_natal: bool = False,
                         event_horizon_days: Optional[int] = None
                         ) -> PredictionResult:
    """
    Synthesis for one moment, returned as a PredictionSnapshot dictionary.

    `natal` is a NatalResult. Its engine objects are read — features, dasha,
    ashtakavarga, sensitivity — rather than recomputed, so the prediction is
    guaranteed to describe the chart the user is looking at.
    """
    objects = getattr(natal, "engine_objects", {}) or {}
    features = objects.get("features")
    if features is None:
        raise MethodologyError(
            "This chart was calculated without the feature engine, so no "
            "synthesis can be run for it.",
            hint="Recalculate with the feature engine enabled.")

    when = parse_moment(moment or datetime.datetime.now())
    settings = objects.get("settings")
    profile_name = profile or (settings.synthesis_profile if settings
                               else "standard")
    try:
        synthesis_profile = SynthesisProfile(profile_name)
    except ValueError as exc:
        raise MethodologyError(
            f"'{profile_name}' is not a synthesis profile. Available: "
            f"{', '.join(p.value for p in SynthesisProfile)}.",
            detail=str(exc), field="synthesis_profile") from exc

    chart = objects.get("chart")
    dasha = objects.get("dasha")
    precision = objects.get("precision")
    warnings: list[str] = []

    transit_snapshot = get_transit_snapshot(when, natal_chart=chart)
    reliability = build_reliability(
        objects.get("sensitivity"),
        **({"birth_time_precision_seconds": precision.seconds,
            "precision_basis": precision.basis} if precision else {}))

    context = synthesise(
        features, moment=when, yoga_results=objects.get("yoga_results"),
        dasha=dasha, transit_snapshot=transit_snapshot,
        ashtakavarga=objects.get("ashtakavarga"), reliability=reliability,
        profile=synthesis_profile, domains=list(domains) if domains else None)

    events = _transit_events(
        dasha, when, chart, warnings,
        horizon=(None if event_horizon_days is None
                 else datetime.timedelta(days=event_horizon_days)))
    candidates = (event_candidates(context, dasha=dasha, transit_events=events)
                  if dasha is not None else [])

    # V1.8. These warnings used to reach PredictionResult only, so a
    # saved or exported prediction JSON — which is where a reader actually
    # looks — did not carry them. A disabled event scan or a failed one is
    # exactly the kind of fact that must travel WITH the answer rather than
    # beside it in an object the caller may not keep.
    for warning in warnings:
        if warning not in context.warnings:
            context.warnings.append(warning)

    snapshot = build_prediction_snapshot(
        context,
        natal_snapshot=natal.snapshot if include_natal else None,
        transit_snapshot=transit_snapshot, candidates=candidates)

    return PredictionResult(
        snapshot=snapshot.to_dict(),
        moment=when.isoformat(),
        profile=synthesis_profile.value,
        warnings=tuple(context.warnings),
        engine_objects={
            "context": context, "candidates": candidates,
            "transit_snapshot": transit_snapshot, "events": events,
            "features": features, "natal": natal,
        })


def _transit_events(dasha, moment, chart, warnings,
                    horizon: Optional[datetime.timedelta] = None) -> list:
    """
    Ingresses and stations that can give a window a real edge.

    V1.8 Part 14 asks for a date-specific synthesis under a second, and
    measurement says this scan IS the second: everything else in the
    pipeline together costs about 60ms and a year-wide scan of five grahas
    costs three seconds. So the horizon is a parameter, and a zero horizon
    skips the scan entirely.

    What that costs is stated rather than buried. Without the scan the
    domain results, the evidence and the confidence are unchanged — they
    do not consult it — and the event candidates lose their sharp edges:
    a window that would have been bounded by "Guru enters Karka" is
    bounded by the antardasha boundary instead. That is a coarser answer,
    not a different one.
    """
    if dasha is None:
        return []
    span = EVENT_SCAN_HORIZON if horizon is None else horizon
    if not span:
        warnings.append(
            "Transit event scan disabled, so event windows are bounded by "
            "dasha period edges rather than by ingresses and stations. "
            "Domain activation, evidence and confidence are unaffected.")
        return []
    window = dasha.get_period_at(moment, level="antardasha")
    start = max(window.start, moment - span) if window else moment - span
    end = min(window.end, moment + span) if window else moment + span
    try:
        return get_transit_events_between(
            start, end, planets=EVENT_SCAN_PLANETS, kinds=EVENT_SCAN_KINDS,
            natal_chart=chart)
    except Exception as exc:                       # pragma: no cover - guard
        # A failed scan costs precision in the window edges and nothing else,
        # so it is reported rather than fatal.
        warnings.append(f"Transit event scan skipped: {exc}")
        return []


# ── interpretation ───────────────────────────────────────────────────────────

def render_interpretation(prediction,
                          language: str = "en",
                          mode: str = "detailed",
                          domains: Optional[Sequence[str]] = None,
                          birth: Optional[dict] = None):
    """
    The V1.6 renderer, with its exceptions translated.

    A missing template key stays fatal. V1.6 made that choice deliberately —
    a document with a bland sentence where a specific finding should have
    been still looks like a reading, and the reader has no way to know
    something was lost. Wrapping it in an ApplicationError changes who sees
    the message, not whether the report is produced.
    """
    snapshot = (prediction.snapshot if hasattr(prediction, "snapshot")
                else prediction)
    objects = getattr(prediction, "engine_objects", {}) or {}
    natal = objects.get("natal")

    try:
        report_mode = ReportMode(mode)
    except ValueError as exc:
        raise MethodologyError(
            f"'{mode}' is not a report mode. Available: "
            f"{', '.join(m.value for m in ReportMode)}.",
            detail=str(exc), field="report_mode") from exc

    if birth is None and natal is not None:
        birth = _birth_block(natal)

    try:
        return build_interpretation(
            snapshot, language=language, mode=report_mode,
            features=objects.get("features"), birth=birth,
            domains=list(domains) if domains else None)
    except UnsupportedLocale as exc:
        raise UnsupportedLanguageError(
            f"No interpretation templates are installed for '{language}'.",
            detail=str(exc),
            hint="Choose an installed language.", field="language") from exc
    except MissingTemplateKey as exc:
        raise TemplateUnavailableError(
            f"The '{language}' template set is incomplete, so this report "
            f"cannot be produced without leaving a gap in it.",
            detail=str(exc), field="language") from exc
    except TemplateError as exc:
        raise TemplateUnavailableError(
            f"The '{language}' template set could not render this report.",
            detail=str(exc), field="language") from exc


def _birth_block(natal) -> dict:
    """The four birth facts the document header needs, read from a snapshot."""
    birth = natal.snapshot.get("birth", {}) or {}
    local = (birth.get("datetime_local") or "")
    date, _, time = local.partition("T")
    location = birth.get("location") or {}
    return {
        "name": birth.get("name") or "Unknown",
        "date": date or "an unrecorded date",
        "time": (time[:5] if time else "an unrecorded time"),
        "place": location.get("name") or "an unrecorded place",
    }


def timeline_candidates(prediction, domains: Optional[Sequence[str]] = None
                        ) -> list[dict]:
    """
    Event candidates as plain rows, for the timeline screen (Part 17).

    ORDINAL STAYS ORDINAL. Each row carries the activation level and the
    confidence band as the engine named them, and the caller is given no
    numeric field it could plot on a probability axis. A timeline that drew
    STRONGLY_ACTIVE at 0.9 would have invented the 0.9.
    """
    snapshot = (prediction.snapshot if hasattr(prediction, "snapshot")
                else prediction)
    wanted = {d.upper() for d in domains} if domains else None
    rows = []
    for item in snapshot.get("event_candidates", []) or []:
        if wanted and item.get("domain", "").upper() not in wanted:
            continue
        window = item.get("window", {}) or {}
        rows.append({
            "domain": item.get("domain", ""),
            "event_type": item.get("event_type", ""),
            "window_start": window.get("window_start"),
            "window_end": window.get("window_end"),
            "peak": window.get("peak"),
            "activation": item.get("activation", ""),
            "confidence": item.get("confidence", ""),
            "synthesis_profile": item.get("synthesis_profile", ""),
            "basis": window.get("basis", ""),
        })
    rows.sort(key=lambda r: (r["window_start"] or "", r["domain"]))
    return rows
