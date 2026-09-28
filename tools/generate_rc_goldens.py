#!/usr/bin/env python3
"""
Generate the V1 release-candidate goldens (V1.8 Part 42)
----------------------------------------------------------
    python3 tools/generate_rc_goldens.py [--write]

Freezes a small set of charts at every stage of the pipeline, as CONTENT
HASHES rather than as copies of the output.

WHY HASHES AND NOT SNAPSHOTS

    A 32-page report stored verbatim is 50 KB of fixture that nobody
    reads and everybody regenerates. What a golden needs to do is FAIL
    when the output changes, and a hash does that in one line while
    making it obvious that the fixture is not a specification.

    The hashes exclude timestamps — every stage already has a
    `content_hash` that pops the generated time — so a golden that
    changes means the ANSWER changed, which is exactly when somebody
    should have to write down why.

REGENERATING IS DELIBERATE

    `--write` overwrites the fixture. The test that consumes it does
    not, and the fixture carries a `reasons` field: a release that
    changes a golden is expected to add an entry saying what changed and
    why, in the same commit. That is the whole mechanism Part 42 asks
    for — "require an explicit reason" is a review convention, and this
    is where the reason is written down.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "rc_goldens.json")

#: A frozen clock, so "generated" fields cannot enter a hash by accident.
FIXED_TIME = datetime.datetime(2026, 1, 1, 12, 0, 0)

#: The moment every prediction is computed for.
MOMENT = datetime.datetime(2026, 9, 27, 12, 0, 0)

#: Small on purpose. Part 42 says "a small frozen set", and the value of
#: a golden is that somebody looks at it when it breaks.
#:
#: The four are chosen to differ in what they stress, not in taste:
#:   jaipur_1988     the documented worked example, northern, minute-precise
#:   reykjavik_1975  high latitude, where the ascendant misbehaves
#:   santiago_2003   southern hemisphere, a different dasha era
#:   singapore_1960  equatorial, and an hour-precision birth time
CASES = (
    {
        "id": "jaipur_1988",
        "name": "Jaipur 1988",
        "date_of_birth": "1988-08-30",
        "time_of_birth": "20:18",
        "place": "Jaipur",
        "precision": "EXACT_TO_MINUTE",
        "why": "The documented worked example; every other suite pins it.",
    },
    {
        "id": "reykjavik_1975",
        "name": "Reykjavik 1975",
        "date_of_birth": "1975-03-14",
        "time_of_birth": "04:05",
        "place": "Reykjavik",
        "precision": "EXACT_TO_MINUTE",
        "why": "64 degrees north, where ascendant arithmetic breaks first.",
    },
    {
        "id": "auckland_2003",
        "name": "Auckland 2003",
        "date_of_birth": "2003-11-02",
        "time_of_birth": "17:40",
        "place": "Auckland",
        "precision": "APPROX_5_MIN",
        "why": "Southern hemisphere, and an imprecise birth time.",
    },
    {
        "id": "singapore_1960",
        "name": "Singapore 1960",
        "date_of_birth": "1960-06-21",
        "time_of_birth": "12:00",
        "place": "Singapore",
        "precision": "APPROX_15_MIN",
        "why": "Equatorial, and a birth time known only to the quarter hour.",
    },
)


def _hash(payload) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str,
                      ensure_ascii=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def _without_time(payload: dict) -> dict:
    return {key: value for key, value in payload.items()
            if key not in ("generated", "created")}


def build_case(case: dict) -> dict:
    from app.models import (
        ApplicationSettings, BirthTimePrecision, ConsultationRecord,
        ReportPreferences,
    )
    from app.report import render_pdf
    from app.services import (
        calculate_chart, calculate_prediction, chart_visual_model,
        generate_report, render_interpretation,
    )
    from app.visual import render_chart

    record = ConsultationRecord(
        name=case["name"], date_of_birth=case["date_of_birth"],
        time_of_birth=case["time_of_birth"], place=case["place"],
        precision=BirthTimePrecision(case["precision"]),
        settings=ApplicationSettings(), created=FIXED_TIME.isoformat())

    natal = calculate_chart(record, record.settings)
    # The event scan is disabled: it costs three seconds a chart and
    # moves only the window edges, and a golden set that takes a minute
    # to check is a golden set that gets skipped.
    prediction = calculate_prediction(natal, MOMENT, "standard",
                                      event_horizon_days=0)
    interpretation = render_interpretation(prediction, mode="detailed")

    charts = {}
    for style in ("north_indian", "south_indian"):
        for varga in ("D1", "D9"):
            model = chart_visual_model(natal, varga=varga, style=style)
            charts[f"{style}/{varga}"] = render_chart(model).content_hash()

    reports = {}
    for language in ("en", "hi"):
        for mode in ("summary", "technical"):
            document = generate_report(
                record, record.settings,
                ReportPreferences(mode=mode, language=language),
                natal=natal, prediction=prediction,
                generated=FIXED_TIME.isoformat())
            reports[f"{language}/{mode}"] = {
                "document": document.content_hash(),
                "pdf_bytes": len(render_pdf(document.to_dict())),
                "sections": [section.id for section in document.sections],
            }

    return {
        "id": case["id"],
        "why": case["why"],
        "input": {
            "name": case["name"], "date_of_birth": case["date_of_birth"],
            "time_of_birth": case["time_of_birth"], "place": case["place"],
            "precision": case["precision"],
        },
        "natal_snapshot": _hash(_without_time(natal.snapshot)),
        "prediction_snapshot": _hash(_without_time(prediction.snapshot)),
        "interpretation": _hash(_without_time(interpretation.to_dict())),
        "charts": charts,
        "reports": reports,
        "shape": {
            "planets": len(natal.snapshot.get("planets") or {}),
            "domains": len(prediction.snapshot.get("domain_results") or {}),
            "warnings": len(prediction.snapshot.get("warnings") or []),
        },
    }


def build() -> dict:
    from app.services import versions

    return {
        "note": (
            "V1 release-candidate goldens. Content hashes, excluding "
            "timestamps, for every stage of the pipeline. A change here "
            "means an ANSWER changed; add an entry to `reasons` in the "
            "same commit saying what and why."),
        "generated_under": versions(),
        "moment": MOMENT.isoformat(),
        "fixed_time": FIXED_TIME.isoformat(),
        "reasons": [
            {
                "release": "V1.8",
                "what": "Created.",
                "why": ("First frozen set. Baselines the release "
                        "candidate at gochara-complete, D2-integrated, "
                        "Devanagari-PDF, South-Indian-capable."),
            },
        ],
        "cases": [build_case(case) for case in CASES],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--write", action="store_true",
                        help="Overwrite the fixture")
    arguments = parser.parse_args()

    payload = build()
    if arguments.write:
        existing = {}
        if os.path.exists(FIXTURE):
            with open(FIXTURE, encoding="utf-8") as handle:
                existing = json.load(handle)
        # Reasons accumulate; they are the record of why a golden moved.
        if existing.get("reasons"):
            known = {(r["release"], r["what"]) for r in payload["reasons"]}
            payload["reasons"] = existing["reasons"] + [
                r for r in payload["reasons"]
                if (r["release"], r["what"]) not in
                {(e["release"], e["what"]) for e in existing["reasons"]}]
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        with open(FIXTURE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        print(f"\n  Wrote {FIXTURE}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n  {len(payload['cases'])} golden case(s).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
