"""
Chart service (V1.7 Parts 1, 2, 3, 4, 33)
===========================================
`calculate_chart(consultation, settings)` — the whole natal pipeline behind
one call, returning data rather than printing it.

WHAT MOVED HERE, AND WHAT DID NOT

    main.py's `build_report` computed and printed in one pass, so the only
    way to obtain a chart was to produce a console report. This function is
    the computation with the printing removed; `build_report` now calls it
    and prints the result. There is one pipeline, not two.

    Nothing was reimplemented. Every call below is the same engine entry
    point the CLI already used, in the same order, with the same arguments.
    The 53 CLI back-compatibility tests are the check on that claim.

ERRORS (Part 33)

    The engine raises precise, technical exceptions. They are translated
    here into the application's error family, which carries a sentence for
    the user and keeps the technical text in `detail` for debug mode. The
    original is chained, never discarded.
"""

from __future__ import annotations

import datetime
from typing import Optional

from engine.features import build_chart_features, parashari_profile
from engine.input_model import (
    LAGNA_KEY, ConsultationInput, InputError, positions_from_mapping,
)
from engine.location import LocationError as EngineLocationError
from engine.location import resolve_location
from engine.planets import PLANET_NAMES, JyotishChart, jde_from_datetime
from engine.rules import evaluate_rules
from engine.snapshot import build_snapshot
from engine.vargas import VargaConfig, VargaConfigError

from ..errors import (
    ApplicationError, InvalidBirthDataError, LocationError, MethodologyError,
)
from ..models import ApplicationSettings, BirthTimePrecision, ConsultationRecord

#: Seconds are optional in the form; both forms are accepted and the
#: precision the user stated is kept separately (Part 4).
_TIME_FORMATS = ("%H:%M:%S", "%H:%M")


def _parse_birth_moment(record: ConsultationRecord) -> datetime.datetime:
    """Date and time, with an error a person can act on."""
    date_text = (record.date_of_birth or "").strip()
    time_text = (record.time_of_birth or "").strip()

    try:
        date = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise InvalidBirthDataError(
            "The date of birth must be written as YYYY-MM-DD, "
            f"for example 1988-03-14. '{date_text}' could not be read.",
            detail=str(exc), field="date_of_birth") from exc

    if not time_text:
        raise InvalidBirthDataError(
            "A birth time is required. The rising sign changes roughly every "
            "two hours, so a chart without one is a different chart.",
            hint="If the time is not known, enter the best estimate and set "
                 "the precision to 'Not known'.",
            field="time_of_birth")

    for fmt in _TIME_FORMATS:
        try:
            time = datetime.datetime.strptime(time_text, fmt).time()
            break
        except ValueError:
            continue
    else:
        raise InvalidBirthDataError(
            "The birth time must be written as HH:MM or HH:MM:SS on a "
            f"24-hour clock, for example 10:35. '{time_text}' could not be "
            "read.", field="time_of_birth")

    return datetime.datetime.combine(date, time)


def _resolve_place(record: ConsultationRecord,
                   moment: datetime.datetime):
    """
    Coordinates and UTC offset, or a refusal.

    There is deliberately no fallback. A chart computed from the wrong
    coordinates is not a degraded chart, it is someone else's chart, and it
    carries no sign of the substitution.
    """
    if not (record.place or "").strip() and not (
            record.latitude and record.longitude):
        raise LocationError(
            "A birth place is required. The rising sign depends entirely on "
            "where the birth happened.",
            hint="Enter a city, or give latitude, longitude and timezone "
                 "directly.",
            field="place")
    try:
        return resolve_location(
            place=record.place,
            latitude=record.latitude,
            longitude=record.longitude,
            timezone=record.timezone_name,
            utc_offset=record.utc_offset,
            local_datetime=moment,
        )
    except EngineLocationError as exc:
        raise LocationError(
            f"The birth place could not be resolved: {exc}",
            detail=str(exc),
            hint="Enter latitude, longitude and timezone directly if the "
                 "place is not in the built-in list. No other place is "
                 "substituted.",
            field="place") from exc


def _varga_config(settings: ApplicationSettings) -> VargaConfig:
    if not settings.varga_profile:
        return VargaConfig()
    try:
        return VargaConfig.from_file(settings.varga_profile)
    except (VargaConfigError, OSError) as exc:
        raise MethodologyError(
            "The divisional-chart convention file could not be used: "
            f"{exc}", detail=str(exc), field="varga_profile") from exc


def _authoritative_chart(positions: dict, calculated: JyotishChart
                         ) -> JyotishChart:
    """
    Entered degrees win; blanks fall back to the calculated position.

    Same rule as main.authoritative_chart, without the printing. An entered
    degree carries no speed, and leaving it out of `speeds` is what makes
    the feature layer mark the motion unmeasured rather than presenting a
    placeholder as an observation.
    """
    lagna_lon = (positions[LAGNA_KEY].longitude if LAGNA_KEY in positions
                 else calculated.lagna.longitude)
    planet_lons: dict[str, float] = {}
    retrograde: set[str] = set()
    speeds: dict[str, float] = {}
    for body in PLANET_NAMES:
        entered = positions.get(body)
        if entered is not None:
            planet_lons[body] = entered.longitude
            if entered.retrograde:
                retrograde.add(body)
        elif body in calculated.planets:
            planet_lons[body] = calculated.planets[body].longitude
            speeds[body] = calculated.planets[body].speed
            if calculated.planets[body].is_retrograde:
                retrograde.add(body)
    return JyotishChart.from_sidereal_longitudes(
        lagna_lon=lagna_lon, planet_lons=planet_lons, retrograde=retrograde,
        ayanamsha=calculated.ayanamsha, jde=calculated.jde,
        lat=calculated.lat, lon=calculated.lon, speeds=speeds)


def calculate_chart(consultation: ConsultationRecord,
                    settings: Optional[ApplicationSettings] = None,
                    ) -> "NatalResult":
    """
    The natal pipeline: positions, features, yogas, dasha, strength,
    ashtakavarga, bhava and birth-time sensitivity, assembled into one
    ChartSnapshot.

    Returns a NatalResult. Raises an ApplicationError subclass and nothing
    else — engine exceptions are translated, never leaked.
    """
    from ..models import NatalResult   # local: keeps the module import-light

    settings = settings or consultation.settings or ApplicationSettings()
    moment = _parse_birth_moment(consultation)
    location = _resolve_place(consultation, moment)
    varga_config = _varga_config(settings)
    warnings: list[str] = []

    try:
        utc = location.to_utc(moment)
        calculated = JyotishChart(
            jde=jde_from_datetime(utc),
            lat=location.latitude, lon=location.longitude,
            ayanamsha_system=settings.ayanamsha,
            true_node=settings.node == "true")
    except ValueError as exc:
        # available_ayanamshas() is the only ValueError the constructor
        # raises for a user-supplied value.
        raise MethodologyError(
            f"That ayanamsha is not available: {exc}",
            detail=str(exc), field="ayanamsha") from exc

    # Entered degrees, when the consultation carries them, are authoritative.
    chart = calculated
    if consultation.entered_positions:
        try:
            positions = positions_from_mapping(consultation.entered_positions)
        except InputError as exc:
            raise InvalidBirthDataError(
                f"An entered planetary degree could not be read: {exc}",
                detail=str(exc), field="entered_positions") from exc
        missing = [b for b in [LAGNA_KEY] + PLANET_NAMES if b not in positions]
        if missing:
            warnings.append(
                "Calculated positions were used for bodies with no entered "
                "degree: " + ", ".join(missing) + ".")
        chart = _authoritative_chart(positions, calculated)

    features = build_chart_features(
        chart, varga_config=varga_config,
        aspect_profile=parashari_profile(settings.node_aspects))
    yoga_results = evaluate_rules(features, settings.rule_profile)

    dasha = _dasha(chart, moment)
    shadbala = _shadbala(chart, features, moment, varga_config, settings)
    if shadbala is not None:
        # Rules and synthesis must read one strength computation, not each
        # run their own; the engine expects it attached to the features.
        features.shadbala = shadbala
    ashtakavarga = _ashtakavarga(chart, settings)
    bhava = _bhava(chart, location, settings)
    sensitivity = _sensitivity(consultation, location, moment, varga_config,
                               settings, warnings)

    snapshot = build_snapshot(
        chart, features=features, yoga_results=yoga_results, dasha=dasha,
        varga_config=varga_config, birth_datetime=moment,
        birth_utc=location.to_utc(moment), location=location,
        name=consultation.name, rule_profile=settings.rule_profile,
        shadbala=shadbala, ashtakavarga=ashtakavarga, bhava=bhava,
        sensitivity=sensitivity)

    data = snapshot.to_dict()
    # Part 4: the precision the user stated travels with the chart. The
    # snapshot records what was entered; it does not narrow it.
    data["birth"]["time_precision"] = consultation.precision.value
    data["birth"]["time_precision_seconds"] = consultation.precision.seconds
    data["birth"]["time_precision_basis"] = consultation.precision.basis

    warnings.extend(features.warnings)
    return NatalResult(
        snapshot=data,
        warnings=tuple(warnings),
        engine_objects={
            "chart": chart, "calculated": calculated, "features": features,
            "yoga_results": yoga_results, "dasha": dasha,
            "shadbala": shadbala, "ashtakavarga": ashtakavarga,
            "bhava": bhava, "sensitivity": sensitivity,
            "location": location, "birth_datetime": moment,
            "varga_config": varga_config, "settings": settings,
            "precision": consultation.precision,
        })


# ── optional sections ────────────────────────────────────────────────────────
#
# Each is separately skippable because each costs real time and a user
# paging through a birth chart does not always need all of them. None of
# them changes any other: they read the chart and the features and add a
# section. A skipped section is absent from the snapshot, never defaulted.

def _dasha(chart, moment):
    from engine.timing import DEFAULT_YEAR_LENGTH, from_chart
    return from_chart(chart, moment, depth=3,
                      year_length_name=DEFAULT_YEAR_LENGTH.name)


def _shadbala(chart, features, moment, varga_config, settings):
    if not settings.compute_strength:
        return None
    from engine.strength import compute_shadbala
    return compute_shadbala(chart, features, birth=moment,
                            varga_config=varga_config)


def _ashtakavarga(chart, settings):
    if not settings.compute_ashtakavarga:
        return None
    from engine.ashtakavarga import compute_ashtakavarga
    return compute_ashtakavarga(
        chart, include_reductions=settings.ashtakavarga_reductions)


def _bhava(chart, location, settings):
    if settings.house_system == "whole_sign":
        return None
    from engine.houses import HOUSE_PROFILES, build_bhava_chart
    if settings.house_system not in HOUSE_PROFILES:
        raise MethodologyError(
            f"'{settings.house_system}' is not one of the house systems this "
            f"build offers: {', '.join(sorted(HOUSE_PROFILES))}.",
            field="house_system")
    return build_bhava_chart(chart, settings.house_system,
                             latitude=location.latitude if location else None)


def _sensitivity(consultation, location, moment, varga_config, settings,
                 warnings):
    """
    The birth-time scan, run at the precision the user actually stated.

    This is the connection Part 4 asks for. V1.6 ran the scan at a fixed
    default; here the half-width comes from the form, so a chart entered as
    "within 15 minutes" is tested against fifteen minutes and reports the
    vargas that do not survive it.
    """
    if not settings.compute_sensitivity or location is None:
        warnings.append(
            "Birth-time sensitivity was not calculated, so nothing in this "
            "chart has been shown to be stable against a small change in the "
            "recorded time.")
        return None
    from engine.sensitivity import analyse_birth_time
    return analyse_birth_time(
        location.to_utc(moment), location.latitude, location.longitude,
        ayanamsha_system=settings.ayanamsha,
        true_node=settings.node == "true",
        varga_config=varga_config,
        bhava_system=(settings.house_system
                      if settings.house_system != "whole_sign" else None))


# ── presentation model ───────────────────────────────────────────────────────

def chart_visual_model(natal, varga: str = "D1", **options):
    """
    A ChartVisualModel for one divisional chart.

    Lives here rather than in `app/visual` because building it means reading
    a snapshot, and `app/visual` is downstream of that: the renderer is
    handed a finished model and has nothing to reason about. See
    app/visual/model.py for what the model may and may not contain.
    """
    from .visual_builder import build_visual_model
    snapshot = natal.snapshot if hasattr(natal, "snapshot") else natal
    return build_visual_model(snapshot, varga=varga, **options)
