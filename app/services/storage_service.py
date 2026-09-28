"""
Consultation storage adapter (V1.8 Parts 25, 26, 28)
------------------------------------------------------
Loading, validating, exporting and importing consultations.

WHY VALIDATION LIVES HERE AND NOT IN `app/storage.py`

    `app.storage` reads and writes a file format. It knows nothing about
    ayanamshas, and it should not: the list of valid ayanamshas is the
    engine's, and putting an engine import in the file reader would make
    the storage layer un-loadable in a build whose engine failed to
    import — the exact situation in which you most want to read a saved
    file and see what it says.

    So the reader guarantees the SHAPE and this adapter guarantees the
    MEANING. Part 25 lists "invalid methodology profile" among the cases
    that must produce a recoverable error, and before V1.8 a file naming
    an ayanamsha that does not exist loaded cleanly and failed three
    minutes later inside the ephemeris.

WHAT AN EXPORT CONTAINS (Part 26)

    The input and the methodology. Not the answer.

    "Do not embed unnecessary calculated data when input + methodology is
    sufficient to reproduce the chart." A cached chart in an export is a
    stale chart the moment the engine changes, and an export is precisely
    the artefact most likely to be opened by a future version. So the
    cache is dropped on export and recomputed on import.

PRIVACY (Part 28)

    An export is a local file the user asked for, containing birth data
    they entered. Nothing here transmits it. `describe_storage()` states
    what is written and where, so the application can show it rather than
    the user having to take it on trust.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Optional, Sequence

from ..errors import StorageError
from ..models import ConsultationRecord
from ..storage import from_dict, load as _load, save as _save
from ..version import APPLICATION_VERSION, CONSULTATION_SCHEMA_VERSION
from .settings_service import validate_settings

#: The export envelope's own version, separate from a consultation's.
EXPORT_SCHEMA_VERSION = "1.0.0"


def load_consultation(path: str) -> tuple[ConsultationRecord, dict]:
    """
    Load a consultation and check that its methodology still exists.

    Returns the record and the migration report. A methodology this build
    does not have is raised as a `MethodologyError` naming the field,
    because the alternative — substituting a default — would silently
    recompute somebody's chart under a different convention.
    """
    record, report = _load(path)
    validate_settings(record.settings)
    return record, report


def save_consultation(record: ConsultationRecord, path: str,
                      snapshot: Optional[dict] = None,
                      prediction: Optional[dict] = None) -> str:
    return _save(record, path, snapshot=snapshot, prediction=prediction)


# ── Part 26: export and import ──────────────────────────────────────────────

def export_consultations(records: Sequence[ConsultationRecord], path: str,
                         note: str = "") -> str:
    """
    Write several consultations to one portable file.

    No cached calculation travels: input plus methodology reproduces the
    chart, and a cache would be the one part of the file guaranteed to go
    stale.
    """
    payload = {
        "export_schema": EXPORT_SCHEMA_VERSION,
        "application_version": APPLICATION_VERSION,
        "consultation_schema": CONSULTATION_SCHEMA_VERSION,
        "exported": datetime.datetime.now().isoformat(timespec="seconds"),
        "count": len(records),
        "note": note or (
            "Input and methodology only. Charts are recomputed on import, "
            "so this file stays correct across engine versions. Nothing "
            "here has left this machine."),
        "consultations": [
            {key: value for key, value in record.to_dict().items()
             if key != "cached"}
            for record in records],
    }
    try:
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except (OSError, ValueError) as exc:
        raise StorageError(
            f"The export could not be written to {path}.",
            detail=str(exc)) from exc
    return path


def import_consultations(path: str) -> tuple[list, list[dict]]:
    """
    Read an export, migrating each consultation it holds.

    Returns (records, reports). A consultation that cannot be read does
    NOT abort the import: it is reported with its index and its reason,
    and the rest are returned. An import that refuses everything because
    one entry is damaged is the behaviour that makes people edit JSON by
    hand.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"{path} is not a valid export file: it is not readable as "
            f"JSON.", detail=str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise StorageError(f"The export file {path} could not be read.",
                           detail=str(exc)) from exc

    if not isinstance(payload, dict):
        raise StorageError(
            f"{path} is not an export file: the top level is not an object.")

    entries = payload.get("consultations")
    if not isinstance(entries, list):
        raise StorageError(
            f"{path} is not an export file: it has no `consultations` list.",
            hint="A single consultation is opened with the normal open "
                 "command; an export holds a list of them.")

    records, reports = [], []
    for index, entry in enumerate(entries):
        try:
            if not isinstance(entry, dict):
                raise StorageError(
                    f"Entry {index + 1} is a {type(entry).__name__}, not a "
                    f"consultation.")
            record, report = from_dict(entry, source=f"{path}[{index}]")
            validate_settings(record.settings)
            records.append(record)
            report["index"] = index
            reports.append(report)
        except StorageError as exc:
            reports.append({
                "index": index, "source": f"{path}[{index}]",
                "failed": True, "reason": exc.message,
                "migrations": [], "migration_notes": [],
            })
        except Exception as exc:                    # pragma: no cover
            reports.append({
                "index": index, "source": f"{path}[{index}]",
                "failed": True, "reason": str(exc),
                "migrations": [], "migration_notes": [],
            })
    return records, reports


# ── Part 28: what is stored, and where ──────────────────────────────────────

def describe_storage(paths: Sequence[str] = ()) -> dict:
    """
    What this application writes, where, and what leaves the machine.

    Shown in the application rather than only documented, because a claim
    about privacy that a user has to find in a README is a claim they
    cannot check at the moment it matters.
    """
    return {
        "what_is_stored": [
            "The birth details you enter: name, date, time, place, and "
            "coordinates if you gave them.",
            "The methodology settings in force when you saved.",
            "Optionally, a cached copy of the last calculation — for "
            "speed only. The input above is authoritative and the cache "
            "is recomputed whenever it does not match.",
        ],
        "what_is_not_stored": [
            "Nothing is written unless you ask for it. Calculating a "
            "chart writes no file.",
            "Exports never carry a cached calculation.",
        ],
        "where": list(paths) or [
            "Only the paths you name. This application has no library "
            "directory, no database and no default save location."],
        "what_leaves_the_machine": [
            "Nothing. Chart calculation, interpretation, chart drawing "
            "and both report formats run entirely offline.",
            "The local web interface binds to 127.0.0.1 and serves only "
            "this machine.",
            "There is no telemetry, no crash upload, no update check and "
            "no font or map fetched at runtime.",
        ],
        "network_use": (
            "The application makes no network request at any point in "
            "normal operation. Source texts were retrieved during "
            "development and are cited by locator, not bundled."),
    }
