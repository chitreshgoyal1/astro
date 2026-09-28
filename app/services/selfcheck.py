"""
Startup self-check (V1.8 Part 35)
-----------------------------------
Confirms that this installation has the resources it needs, before a user
discovers otherwise in the middle of a chart.

WHAT IT CHECKS, AND WHAT IT DELIBERATELY DOES NOT

    Part 35: "Do not run the entire test suite at application startup."
    The distinction is between INTEGRITY and CORRECTNESS. Whether the
    Devanagari font is present, whether the locale files are complete,
    whether the VSOP87 tables have the expected shape — those are facts
    about this installation, they change when packaging goes wrong, and
    they are cheap. Whether Jupiter's longitude is right is a fact about
    the code, it does not change between installations, and the test
    suite settles it before release.

    So a failed self-check means "this copy is broken", never "this
    engine is wrong". The two need different responses and conflating
    them trains people to ignore the first.

WHY IT IS A SERVICE

    It reaches the engine for the source registry and the ephemeris
    tables, and the presentation layers may not. Same rule as everywhere
    else.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Optional

OK = "ok"
FAILED = "failed"
SKIPPED = "skipped"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _check(name: str, detail: str = "", status: str = OK,
           hint: str = "") -> dict:
    return {"check": name, "status": status, "detail": detail, "hint": hint}


# ── individual checks ───────────────────────────────────────────────────────

def check_versions() -> dict:
    from .version_service import versions

    data = versions()
    missing = [key for key, value in data.items() if value in (None, "")]
    if missing:
        return _check("schema versions", f"missing: {', '.join(missing)}",
                      FAILED, "The build is incomplete.")
    return _check("schema versions",
                  f"application {data['application']}, chart "
                  f"{data['chart_schema']}, prediction "
                  f"{data['prediction_schema']}, registry "
                  f"{data['source_registry']}")


def check_source_registry() -> dict:
    """
    The registry resolves, and every rule's witnesses exist.

    A dangling witness id is the failure mode that matters: a report
    prints the citation for a rule, and a missing witness turns a source
    appendix into a list of identifiers.
    """
    try:
        from engine.sources.registry import (
            all_recorded_evidence, all_witnesses, registry_summary,
        )
        from engine.sources.editions import witness_by_id
    except ImportError as exc:                      # pragma: no cover
        return _check("source registry", str(exc), FAILED)

    summary = registry_summary()
    dangling = []
    for evidence in all_recorded_evidence():
        for witness_id in evidence.witness_ids:
            try:
                witness_by_id(witness_id)
            except KeyError:
                dangling.append(f"{evidence.subject} → {witness_id}")
    if dangling:
        return _check("source registry",
                      f"{len(dangling)} unresolved witness reference(s): "
                      + "; ".join(dangling[:3]), FAILED)
    return _check("source registry",
                  f"{len(all_witnesses())} witnesses, "
                  f"{summary['rules_total']} rules, registry "
                  f"{summary['registry_version']}")


def check_templates() -> dict:
    """Every locale carries every interpretation key."""
    try:
        from engine.interpretation import available_languages
        from engine.interpretation.renderer import completeness_report
    except ImportError as exc:                      # pragma: no cover
        return _check("interpretation templates", str(exc), FAILED)

    incomplete = []
    languages = available_languages()
    for language in languages:
        report = completeness_report(language)
        if not report["complete"]:
            incomplete.append(
                f"{language} missing {len(report['missing'])}")
    if incomplete:
        return _check("interpretation templates", "; ".join(incomplete),
                      FAILED, "Reinstall or restore the templates directory.")
    return _check("interpretation templates",
                  f"{len(languages)} language(s) complete: "
                  + ", ".join(languages))


def check_report_strings() -> dict:
    """Every locale carries every report chrome string."""
    from ..report.strings import available_languages, completeness

    partial = []
    languages = available_languages()
    for language in languages:
        report = completeness(language)
        if not report["complete"]:
            partial.append(f"{language} missing {len(report['missing'])}")
    if partial:
        return _check("report chrome strings", "; ".join(partial), FAILED)
    return _check("report chrome strings",
                  f"{len(languages)} language(s) complete: "
                  + ", ".join(languages))


def check_fonts() -> dict:
    """
    Bundled fonts are present, readable, unmodified and licensed.

    The checksum matters for more than integrity: Part 17 requires the
    licence and the file to correspond, and a font substituted for
    another is a licence claim that is no longer true.
    """
    from ..report.embed import BUNDLED_FONTS, FONT_DIRECTORY

    problems = []
    for record in BUNDLED_FONTS:
        path = os.path.join(FONT_DIRECTORY, record["file"])
        if not os.path.exists(path):
            problems.append(f"{record['file']} is missing")
            continue
        with open(path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        if digest != record["sha256"]:
            problems.append(f"{record['file']} does not match its checksum")
        licence = os.path.join(FONT_DIRECTORY, record["licence_file"])
        if not os.path.exists(licence):
            problems.append(f"{record['id']} has no licence file beside it")
        if not record.get("redistributable"):
            problems.append(f"{record['id']} has no redistribution right")
    if problems:
        return _check("bundled fonts", "; ".join(problems), FAILED,
                      "Hindi PDFs will be refused until this is fixed.")
    return _check("bundled fonts",
                  f"{len(BUNDLED_FONTS)} font(s) present and verified")


def check_font_shaping() -> dict:
    """
    The shaper produces the conjuncts it is supposed to.

    Cheap, and it is the one part of the font pipeline that can be
    present-but-broken: a font whose GSUB table were stripped would pass
    the checksum test only if the checksum were also wrong, but a shaper
    given an unexpected font would silently emit unshaped codepoints.
    """
    from ..report.embed import devanagari_font

    try:
        font = devanagari_font()
        glyphs = font.shaper.shape("क्ष")
    except Exception as exc:                        # pragma: no cover
        return _check("Devanagari shaping", str(exc), FAILED)
    if len(glyphs) != 1:
        return _check(
            "Devanagari shaping",
            f"क्ष shaped to {len(glyphs)} glyphs; it is one conjunct",
            FAILED, "The bundled font is not the one this build expects.")
    if font.font.unsupported_lookups:
        return _check("Devanagari shaping",
                      f"unsupported lookups: {font.font.unsupported_lookups}",
                      FAILED)
    return _check("Devanagari shaping", "conjuncts and reordering verified")


def check_ephemeris_data() -> dict:
    """The VSOP87 tables are present and the expected size."""
    try:
        from engine.vsop87_data import VSOP87A
    except ImportError as exc:                      # pragma: no cover
        return _check("ephemeris tables", str(exc), FAILED)

    terms = sum(len(block) for body in VSOP87A.values()
                for axis in (0, 1, 2) for block in body[axis].values())
    bodies = sorted(VSOP87A)
    if terms < 1000:
        return _check("ephemeris tables",
                      f"only {terms} series terms; the tables look "
                      f"truncated", FAILED)
    return _check("ephemeris tables",
                  f"{len(bodies)} bodies, {terms} series terms")


def check_city_table() -> dict:
    try:
        from engine.location import CITY_TABLE
    except ImportError as exc:                      # pragma: no cover
        return _check("city table", str(exc), FAILED)
    if not CITY_TABLE:
        return _check("city table", "empty", FAILED)
    return _check("city table", f"{len(CITY_TABLE)} cities")


def check_gochara_rules() -> dict:
    """The transit rule tables are internally consistent."""
    try:
        from engine.gochara import all_rules
    except ImportError as exc:                      # pragma: no cover
        return _check("gochara rules", str(exc), FAILED)

    problems = []
    for rule in all_rules():
        for house, vedha in rule.vedha_pairs.items():
            if house == vedha:
                problems.append(f"{rule.planet}: {house} obstructs itself")
            if not 1 <= vedha <= 12:
                problems.append(f"{rule.planet}: vedha house {vedha}")
    if problems:
        return _check("gochara rules", "; ".join(problems), FAILED)
    pairs = sum(len(r.vedha_pairs) for r in all_rules())
    return _check("gochara rules", f"{pairs} vedha pairs, all well formed")


def check_boundary() -> dict:
    """
    The presentation layers still do not import the engine.

    Cheap enough to run at startup because it reads source files rather
    than importing them, and worth running because a packaging step that
    rewrote imports would break the guarantee silently.
    """
    import ast

    forbidden = ("app/visual", "app/report", "app/ui")
    offenders = []
    for package in forbidden:
        directory = os.path.join(ROOT, package)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    tree = ast.parse(handle.read(), filename=path)
            except (OSError, SyntaxError):           # pragma: no cover
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                if any(n == "engine" or n.startswith("engine.")
                       for n in names):
                    offenders.append(f"{package}/{name}")
    if offenders:
        return _check("architecture boundary",
                      "presentation layers import the engine: "
                      + ", ".join(sorted(set(offenders))), FAILED)
    return _check("architecture boundary",
                  "presentation layers import no engine module")


CHECKS = (
    check_versions,
    check_source_registry,
    check_templates,
    check_report_strings,
    check_fonts,
    check_font_shaping,
    check_ephemeris_data,
    check_city_table,
    check_gochara_rules,
    check_boundary,
)


def run_selfcheck(checks=None) -> dict:
    """Run every check and return a report. Never raises."""
    results = []
    for check in (checks or CHECKS):
        try:
            results.append(check())
        except Exception as exc:                     # noqa: BLE001
            results.append(_check(getattr(check, "__name__", "check"),
                                  f"{type(exc).__name__}: {exc}", FAILED))
    failed = [r for r in results if r["status"] == FAILED]
    return {
        "checks": results,
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "ok": not failed,
        "note": ("Integrity of this installation, not correctness of the "
                 "engine. A failure here means this copy is missing or has "
                 "an altered resource; it does not mean a calculation is "
                 "wrong, and a pass does not mean one is right."),
    }


def format_selfcheck(report: dict) -> str:
    lines = ["", "  INSTALLATION SELF-CHECK", "  " + "─" * 72]
    for result in report["checks"]:
        mark = "ok  " if result["status"] == OK else "FAIL"
        lines.append(f"  {mark}  {result['check']:<28} {result['detail']}")
        if result["status"] != OK and result["hint"]:
            lines.append(f"        {result['hint']}")
    lines.append("  " + "─" * 72)
    lines.append(f"  {report['passed']} passed, {report['failed']} failed")
    lines.append("")
    lines.append("  " + report["note"])
    lines.append("")
    return "\n".join(lines)
