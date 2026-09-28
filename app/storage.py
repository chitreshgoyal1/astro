"""
Saved consultations (V1.7 Parts 31, 32)
=========================================
Local JSON files holding what a consultation WAS, never what it computed.

WHY THE INPUT AND NOT THE ANSWER

    A saved chart is a snapshot of an engine version. Reopen it in two
    years and you are reading 2026's arithmetic with 2028's name on it.
    A saved consultation is a birth time and a set of methodology choices,
    and reopening it recomputes — so a fixed ephemeris bug reaches the
    saved chart, and so does a changed default, visibly.

    A computed snapshot may be cached beside the record for speed. It is
    never authoritative: `load` returns the record, and the cache is
    offered separately with the versions it was produced under, so a caller
    can decide whether to trust it.

MIGRATION (Part 32)

    Every file carries `schema_version`. A file from an older version is
    migrated by an explicit function per step, and every migration says in
    `migration_notes` what it assumed.

    The rule that matters: a methodology setting absent from an old file is
    filled with the DEFAULT THAT FILE WAS WRITTEN UNDER, not today's. A
    consultation saved when the default ayanamsha was Lahiri must not
    silently become a Raman chart because a later release changed the
    default — the chart would move by degrees and nothing would say so.

NO CLOUD

    `save` writes a file. There is no account, no sync and no telemetry,
    and the application never opens a socket to store anything.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Callable, Optional

from .errors import StorageError
from .models import (
    APPLICATION_VERSION, CONSULTATION_SCHEMA_VERSION, ApplicationSettings,
    BirthTimePrecision, ConsultationRecord, ReportPreferences,
)

#: The defaults in force at each schema version, for filling gaps in an old
#: file. Frozen history: these entries describe releases that have shipped
#: and must never be edited to match a new default.
DEFAULTS_BY_SCHEMA = {
    # V1.8 shipped no changed defaults, so 2.0.0 repeats 1.0.0's values.
    # Written out rather than aliased: the moment one of them changes,
    # the two entries must differ, and an alias would make that change
    # invisible.
    "2.0.0": {
        "ayanamsha": "lahiri",
        "node": "true",
        "house_system": "whole_sign",
        "rule_profile": "parashari",
        "node_aspects": "parashari_like",
        "synthesis_profile": "standard",
        "language": "en",
    },
    "1.0.0": {
        "ayanamsha": "lahiri",
        "node": "true",
        "house_system": "whole_sign",
        "rule_profile": "parashari",
        "node_aspects": "parashari_like",
        "synthesis_profile": "standard",
        "language": "en",
    },
}


def save(record: ConsultationRecord, path: str,
         snapshot: Optional[dict] = None,
         prediction: Optional[dict] = None) -> str:
    """
    Write a consultation, optionally with a cached calculation.

    The cache is stored under `cached`, with the schema versions it was
    produced under, so a reader can tell whether it still corresponds to
    the engine in front of it.
    """
    payload = record.to_dict()
    if snapshot is not None or prediction is not None:
        payload["cached"] = {
            "note": ("A previous calculation, kept for speed. The input "
                     "above is authoritative: this may be recomputed and "
                     "discarded at any time."),
            "computed": datetime.datetime.now().isoformat(timespec="seconds"),
            "chart_schema": (snapshot or {}).get("schema_version"),
            "prediction_schema": (prediction or {}).get("schema_version"),
            "chart": snapshot,
            "prediction": prediction,
        }
    try:
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except (OSError, ValueError) as exc:
        # ValueError covers a path the OS will not even accept — an
        # embedded null byte, most often, which arrives from a filename
        # field and is a user mistake rather than a defect.
        raise StorageError(
            f"The consultation could not be saved to {path}.",
            detail=str(exc)) from exc
    return path


def load(path: str) -> tuple[ConsultationRecord, dict]:
    """
    Read a consultation, migrating it if it was written by an older build.

    Returns the record and a report describing what happened: the version
    read, the migrations applied and what each of them assumed. The caller
    is expected to show that to the user rather than swallow it.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        # Before the OSError clause: JSONDecodeError IS a ValueError, and
        # a broadly-caught ValueError would swallow it and report a
        # readable file as unreadable.
        raise StorageError(
            f"{path} is not a valid consultation file: it is not readable "
            f"as JSON.", detail=str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise StorageError(
            f"The consultation file {path} could not be read.",
            detail=str(exc)) from exc

    if not isinstance(payload, dict):
        raise StorageError(
            f"{path} is not a consultation file: the top level is not an "
            f"object.")
    return from_dict(payload, source=path)


def _mapping(payload: dict, key: str, source: str) -> dict:
    """
    One block of a consultation file, checked to be an object.

    Part 25. A file whose `input` is a string is corrupt, and before V1.8
    it produced `AttributeError: 'str' object has no attribute 'get'` from
    somewhere three frames down. A hand-edited file is the normal way this
    happens, and a traceback tells the person who edited it nothing about
    which key they broke.
    """
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise StorageError(
            f"The '{key}' section of this consultation is a "
            f"{type(value).__name__}, and it has to be an object.",
            detail=f"{source or 'file'}: {key} = {value!r}"[:200],
            hint="The file has been edited or truncated. Re-save it from "
                 "the application, or re-enter the birth details.",
            field=key)
    return value


def from_dict(payload: dict, source: str = "") -> tuple[ConsultationRecord,
                                                        dict]:
    """Build a record from a loaded file. Exposed for tests and for import."""
    payload, report = migrate(payload, source=source)
    data = _mapping(payload, "input", source)

    missing = [field for field in ("date_of_birth", "time_of_birth")
               if not data.get(field)]
    if missing:
        raise StorageError(
            f"This consultation is missing {' and '.join(missing)}, so the "
            f"chart cannot be recomputed from it.",
            hint="The file records the input rather than the answer, so an "
                 "incomplete input cannot be recovered from the cache.")

    try:
        precision = BirthTimePrecision(
            data.get("birth_time_precision")
            or BirthTimePrecision.from_time_text(
                data.get("time_of_birth", "")).value)
    except ValueError:
        precision = BirthTimePrecision.UNKNOWN
        report["migration_notes"].append(
            f"Birth-time precision '{data.get('birth_time_precision')}' is "
            f"not a value this build knows. Treated as not known, which is "
            f"the widest band; nothing birth-time sensitive will be "
            f"reported as resolved.")

    record = ConsultationRecord(
        name=data.get("name") or "Unknown",
        date_of_birth=str(data["date_of_birth"]),
        time_of_birth=str(data["time_of_birth"]),
        place=data.get("place") or "",
        precision=precision,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        timezone_name=data.get("timezone"),
        utc_offset=data.get("utc_offset"),
        settings=ApplicationSettings.from_dict({
            **(payload.get("calculation") or {}),
            **{key: value
               for key, value in (payload.get("presentation") or {}).items()
               if key in ApplicationSettings.PRESENTATION_FIELDS}}),
        report=ReportPreferences.from_dict(payload.get("presentation")),
        notes=data.get("notes") or "",
        entered_positions=dict(data.get("entered_positions") or {}),
        created=payload.get("created") or "",
        application_version=payload.get("application_version") or "",
        schema_version=CONSULTATION_SCHEMA_VERSION,
    )
    report["cached"] = payload.get("cached") or {}
    return record, report


# ── migration ────────────────────────────────────────────────────────────────

def _migrate_pre_schema(payload: dict, report: dict) -> dict:
    """
    A file with no `schema_version` at all.

    This covers the V1 `sample_consultation.json` shape, which used `dob`,
    `tob` and a flat layout and predates the application layer entirely.
    It is migrated rather than rejected because those files exist in this
    repository and a user may well still have one.
    """
    if "input" in payload:
        return payload

    migrated = {
        "schema_version": "1.0.0",
        "application_version": "",
        "created": "",
        "input": {
            "name": payload.get("name") or "Unknown",
            "date_of_birth": payload.get("dob") or payload.get("date") or "",
            "time_of_birth": (payload.get("tob") or payload.get("time")
                              or ""),
            "place": payload.get("place") or "",
            "latitude": payload.get("latitude") or payload.get("lat"),
            "longitude": (payload.get("longitude") or payload.get("lon")
                          or payload.get("lng")),
            "timezone": payload.get("timezone") or payload.get("tz"),
            "utc_offset": payload.get("utc_offset"),
            "notes": payload.get("notes") or "",
            "entered_positions": payload.get("positions") or {},
        },
        "settings": {},
        "report": {},
    }
    if payload.get("ayanamsha"):
        migrated["settings"]["ayanamsha"] = str(payload["ayanamsha"]).lower()

    # A V1 file recorded HH:MM and nothing about how good it was. That is
    # exactly the case Part 4 exists for, and assuming the minute is what
    # the field can support — not more.
    time_text = migrated["input"]["time_of_birth"]
    migrated["input"]["birth_time_precision"] = (
        BirthTimePrecision.from_time_text(time_text).value)
    report["migration_notes"].append(
        "Read as a pre-V1.7 consultation file. The birth-time precision was "
        f"not recorded in that format; it has been taken as "
        f"'{migrated['input']['birth_time_precision']}', which is what the "
        f"time field itself supports and no more.")
    report["migrations"].append("pre-schema -> 1.0.0")
    return migrated


#: Ordered migration steps. Each takes a payload at the version keyed and
#: returns one at the next.
def _migrate_1_to_2(payload: dict, report: dict) -> dict:
    """
    Schema 1.0.0 → 2.0.0 (V1.8, Parts 24, 27).

    The flat `settings` block splits into `calculation` and
    `presentation`, and `report` folds into the second. Nothing is
    dropped and nothing is reinterpreted: each key moves to the block it
    always belonged to.

    DETERMINISTIC AND IDEMPOTENT. Running it twice is prevented by the
    version loop, but the function itself does not depend on anything
    outside `payload` — no clock, no defaults, no current settings — so
    the same file always migrates to the same bytes. A migration that
    consulted today's defaults would silently re-methodologise old
    charts, which is the failure Part 24's last sentence names.
    """
    settings = dict(payload.get("settings") or {})
    if not isinstance(settings, dict):                     # pragma: no cover
        settings = {}
    presentation = dict(payload.get("report") or {})

    calculation = {key: value for key, value in settings.items()
                   if key in ApplicationSettings.CALCULATION_FIELDS}
    for key in ApplicationSettings.PRESENTATION_FIELDS:
        if key in settings:
            presentation.setdefault(key, settings[key])

    # A v1 file may hold keys this build has never heard of — written by a
    # fork, or by a field that was removed. They are KEPT, in a block of
    # their own, rather than dropped: a reader who silently discards what
    # it does not understand turns an unknown setting into a default
    # without saying so.
    unknown = {key: value for key, value in settings.items()
               if key not in ApplicationSettings.CALCULATION_FIELDS
               and key not in ApplicationSettings.PRESENTATION_FIELDS}

    migrated = {key: value for key, value in payload.items()
                if key not in ("settings", "report")}
    migrated["schema_version"] = "2.0.0"
    migrated["calculation"] = calculation
    migrated["presentation"] = presentation
    if unknown:
        migrated["unrecognised_settings"] = unknown
        report["migration_notes"].append(
            "These saved settings are not fields this build knows and were "
            "kept rather than discarded: "
            + ", ".join(sorted(unknown)) + ". They do not affect the "
            "calculation, and a build that understands them can still "
            "read them.")

    report["migrations"].append({
        "from": "1.0.0", "to": "2.0.0",
        "what": ("Split the single `settings` block into `calculation` and "
                 "`presentation`, and folded `report` into the second."),
        "assumed": ("Nothing. Every key moved to the block it belonged to; "
                    "no value was changed and no default was applied."),
    })
    return migrated


MIGRATIONS: dict[str, Callable[[dict, dict], dict]] = {
    "": _migrate_pre_schema,
    "1.0.0": _migrate_1_to_2,
}


def migrate(payload: dict, source: str = "") -> tuple[dict, dict]:
    """
    Bring a payload up to the current schema.

    Refuses a file from a FUTURE schema rather than guessing at it: a
    reader that ignores fields it does not understand will silently drop a
    methodology setting, and the chart will change without saying so.
    """
    report = {
        "source": source,
        "read_schema": payload.get("schema_version") or "pre-1.7",
        "current_schema": CONSULTATION_SCHEMA_VERSION,
        "application_version": APPLICATION_VERSION,
        "migrations": [],
        "migration_notes": [],
        "cached": {},
    }

    version = payload.get("schema_version") or ""
    while version != CONSULTATION_SCHEMA_VERSION:
        step = MIGRATIONS.get(version)
        if step is None:
            raise StorageError(
                f"This consultation was written under schema "
                f"'{version or 'an unversioned format'}', which this build "
                f"cannot read.",
                hint="Open it with the version that wrote it, or re-enter "
                     "the birth details. Guessing at an unknown format would "
                     "silently change the methodology the chart was computed "
                     "under.")
        payload = step(payload, report)
        version = payload.get("schema_version") or ""

    settings = dict(_mapping(payload, "calculation", source))
    presentation = dict(_mapping(payload, "presentation", source))
    historical = DEFAULTS_BY_SCHEMA.get(report["read_schema"]) \
        or DEFAULTS_BY_SCHEMA[CONSULTATION_SCHEMA_VERSION]
    filled = []
    for key, value in historical.items():
        target = (presentation
                  if key in ApplicationSettings.PRESENTATION_FIELDS
                  else settings)
        if key not in target:
            target[key] = value
            filled.append(f"{key}={value}")
    if filled:
        report["migration_notes"].append(
            "Settings absent from the saved file were filled from the "
            "defaults in force when it was written, not from today's: "
            + ", ".join(sorted(filled)) + ". A changed default must not "
            "move a saved chart without saying so.")
    payload["calculation"] = settings
    payload["presentation"] = presentation

    current = ApplicationSettings().to_dict()
    differing = sorted(
        key for key, value in historical.items()
        if key in current and current[key] != value)
    if differing:
        report["migration_notes"].append(
            "These defaults have changed since that file's schema: "
            + ", ".join(differing) + ". The saved values were kept.")
    return payload, report
