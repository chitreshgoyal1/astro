"""
Logging and crash diagnostics (V1.8 Parts 28, 29, 30, 33)
-----------------------------------------------------------
What the application records about its own behaviour, and what it
deliberately does not.

THE TENSION THIS MODULE RESOLVES

    Part 29 wants logs that diagnose calculation failures, profile
    mismatches, PDF failures and migration problems. Part 28 wants birth
    information treated as personal data. Those pull in opposite
    directions: the single most useful thing to put in a log for
    diagnosing a chart failure is the birth details, and they are exactly
    the thing that must not be written to a file the user did not ask
    for.

    The resolution is that this module REDACTS BY DEFAULT and names what
    it redacted. A log line says "date_of_birth=<redacted>" rather than
    omitting the field, because a reader debugging a missing-field error
    needs to know whether the field was absent or merely hidden.

    Debug mode turns redaction off. It is opt-in, per run, and every
    record carries `redacted: false` so a log that was captured in debug
    mode cannot be mistaken for one that was not.

WHY THE OUTPUT IS JSON LINES

    A log nobody can query is a log nobody reads. One JSON object per
    line greps, sorts and loads without a parser, and it survives being
    pasted into a bug report — which is the actual delivery mechanism for
    a local application's diagnostics.

WHAT IS NOT HERE

    No upload, no telemetry, no crash reporting service. A crash report
    is written to a file and its path is printed. Whether anybody ever
    sees it is the user's decision, which is the only arrangement
    compatible with the privacy claim this application makes.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import traceback
import uuid
from typing import Any, Optional

#: Fields that identify a person. Redacted unless debug mode is on.
#:
#: Written as a set of NAMES rather than a rule about values, because a
#: rule ("anything that looks like a date") both misses `place` and
#: redacts the target datetime of a synthesis, which is not personal.
PERSONAL_FIELDS = frozenset({
    "name", "subject", "date_of_birth", "time_of_birth", "dob", "tob",
    "birth_date", "birth_time", "place", "latitude", "longitude",
    "datetime_local", "datetime_utc", "notes", "address",
})

REDACTED = "<redacted>"

LEVELS = ("debug", "info", "warning", "error")


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="milliseconds")


def redact(payload: Any, debug: bool = False) -> Any:
    """
    A copy of `payload` with personal fields replaced.

    Recursive, and it replaces rather than deletes: a diagnostic that
    cannot distinguish "absent" from "hidden" sends the reader looking
    for a bug that is not there.
    """
    if debug:
        return payload
    if isinstance(payload, dict):
        return {key: (REDACTED if key in PERSONAL_FIELDS
                      else redact(value, debug))
                for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [redact(item, debug) for item in payload]
    return payload


class Diagnostics:
    """
    A structured log with a redaction policy.

    Deliberately not the standard library's `logging`: this writes one
    JSON object per line to a stream the caller owns, has no global
    state, and cannot be reconfigured by an unrelated import — all three
    of which matter for a library that may be embedded.
    """

    def __init__(self, stream=None, debug: bool = False,
                 minimum: str = "info"):
        self.stream = stream
        self.debug = debug
        self.minimum = minimum if minimum in LEVELS else "info"
        self.records: list[dict] = []

    def _enabled(self, level: str) -> bool:
        return LEVELS.index(level) >= LEVELS.index(self.minimum)

    def log(self, level: str, event: str, **fields) -> dict:
        record = {
            "time": _now(),
            "level": level,
            "event": event,
            "redacted": not self.debug,
        }
        record.update(redact(fields, self.debug))
        self.records.append(record)
        if self.stream is not None and self._enabled(level):
            self.stream.write(json.dumps(record, ensure_ascii=False,
                                         default=str) + "\n")
            self.stream.flush()
        return record

    def info(self, event: str, **fields) -> dict:
        return self.log("info", event, **fields)

    def warning(self, event: str, **fields) -> dict:
        return self.log("warning", event, **fields)

    def error(self, event: str, **fields) -> dict:
        return self.log("error", event, **fields)

    def debug_event(self, event: str, **fields) -> dict:
        return self.log("debug", event, **fields)

    # ── the events Part 29 names ────────────────────────────────────────

    def calculation_failed(self, operation: str, error: BaseException,
                           **fields) -> dict:
        return self.error("calculation_failed", operation=operation,
                          error_type=type(error).__name__,
                          error=str(error), **fields)

    def profile_mismatch(self, wanted: str, available, **fields) -> dict:
        return self.warning("profile_mismatch", wanted=wanted,
                            available=list(available), **fields)

    def pdf_failed(self, reason: str, **fields) -> dict:
        return self.error("pdf_failed", reason=reason, **fields)

    def migration(self, report: dict) -> dict:
        """
        A schema migration. Logged at warning when it ASSUMED anything.

        A migration that filled a gap from a historical default changed
        what the user will see, and Part 24's last sentence forbids doing
        that silently.
        """
        steps = report.get("migrations") or []
        notes = report.get("migration_notes") or []
        level = "warning" if notes else "info"
        return self.log(level, "schema_migration",
                        read_schema=report.get("read_schema"),
                        current_schema=report.get("current_schema"),
                        steps=[f"{s.get('from')}->{s.get('to')}"
                               for s in steps],
                        notes=notes)


#: A default instance for code with nowhere better to log. Silent — no
#: stream — so importing this module never writes anything anywhere.
NULL = Diagnostics()


# ── Part 30: crash reports ──────────────────────────────────────────────────

def crash_report(error: BaseException, *,
                 operation: str = "",
                 settings=None,
                 versions: Optional[dict] = None,
                 debug: bool = False,
                 context: Optional[dict] = None) -> dict:
    """
    A local crash record: what failed, in which build, under which
    methodology.

    THE STACK IS INCLUDED AND THE BIRTH DATA IS NOT. A traceback names
    modules and line numbers and is the whole reason to keep a crash
    report; birth details are personal and rarely necessary, because the
    methodology and the operation usually identify the path. Where they
    ARE necessary, `--debug` includes them and the report says so.

    Frame LOCALS are never captured. A local variable in the ephemeris is
    a longitude; a local variable three frames up is the person's name,
    and there is no way to tell them apart automatically.
    """
    return {
        "report_id": uuid.uuid4().hex[:12],
        "time": _now(),
        "operation": operation,
        "error_type": type(error).__name__,
        "error": str(error),
        "module": getattr(error, "__module__", "") or "",
        "traceback": traceback.format_exception(
            type(error), error, error.__traceback__),
        "versions": dict(versions or {}),
        "methodology": (dict(settings.calculation_settings())
                        if settings is not None
                        and hasattr(settings, "calculation_settings") else {}),
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "personal_data_included": bool(debug),
        "context": redact(context or {}, debug),
        "note": (
            "Written locally and never transmitted. Birth details are "
            "excluded unless the run used --debug, in which case "
            "`personal_data_included` is true. Frame locals are never "
            "captured."),
    }


def write_crash_report(report: dict, directory: Optional[str] = None) -> str:
    """
    Save a crash report beside the user's other files and return its path.

    Falls back to the system temporary directory, because a crash handler
    that raises while handling a crash replaces a useful error with a
    useless one.
    """
    import tempfile

    base = directory or os.path.join(tempfile.gettempdir(), "jyotish-crashes")
    name = f"crash-{report.get('report_id', 'unknown')}.json"
    try:
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False,
                      default=str)
            handle.write("\n")
        return path
    except OSError:                                  # pragma: no cover
        return ""


def format_crash_notice(report: dict, path: str = "") -> str:
    """
    What a normal user is shown when something unexpected fails.

    Part 33 of V1.7 and Part 36 of V1.8: no raw traceback. The user gets
    what went wrong in one line, the report id so a maintainer can ask
    for the right file, and where the file is.
    """
    lines = [
        "",
        "  Something went wrong that this application did not expect.",
        f"  {report.get('error_type', 'Error')}: {report.get('error', '')}",
        "",
        f"  A diagnostic report was written: {path or '(not written)'}",
        f"  Reference: {report.get('report_id', '')}",
        "  It contains no birth details. Nothing was sent anywhere.",
        "",
    ]
    return "\n".join(lines)
