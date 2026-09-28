"""
Version identity (V1.8 Parts 31, 32)
--------------------------------------
One place that knows what this build is.

THE RULE PART 31 SETS

    "Create one application version source. Do not duplicate version
    strings throughout files."

    Before V1.8 the application version was a literal in `app/models.py`,
    the PDF writer said "Jyotish Engine V1.7" in its own literal, and the
    report's provenance block read three schema versions from three
    modules. They agreed by hand. The PDF literal was the one that had
    already drifted — it still said V1.7 in a V1.8 build — which is
    exactly the failure a single source prevents.

WHAT IS NOT CENTRALISED, AND WHY

    The SCHEMA versions stay where their schemas are. `engine.snapshot`
    owns `SCHEMA_VERSION` because that number describes the shape of the
    thing that module emits, and a reader changing that shape must think
    about the number in front of them rather than in a distant file.

    This module READS them and presents them together. It does not define
    them. Centralising the definitions would mean a schema could change
    without its version being in the same diff, which is worse than the
    duplication it would remove.

REPRODUCIBILITY (Part 32)

    `reproducibility_block()` is what a technical report needs to print so
    that somebody else can obtain the same output: the application
    version, every schema, the registry version, the rule catalog version
    and the varga algorithm version. A result that cannot be reproduced
    cannot be checked, and a result nobody can check is an opinion.
"""

from __future__ import annotations

from typing import Optional

#: The application version. THE single source; everything else derives.
APPLICATION_VERSION = "1.8.0"

#: The release name, for documents and the about screen.
RELEASE_NAME = "V1.8"

#: What this release is for, in one line, for the about screen.
RELEASE_DESCRIPTION = (
    "Release candidate: source-qualified gochara, Devanagari PDF, "
    "South Indian charts, and production hardening.")

#: Saved consultation files. Owned here because the format is the
#: application's, not any engine module's.
CONSULTATION_SCHEMA_VERSION = "2.0.0"

#: The report document structure `app.report.document` emits.
REPORT_SCHEMA_VERSION = "1.1.0"


def versions() -> dict:
    """
    Everything the APPLICATION defines about this build.

    Engine schema versions are deliberately absent. This module is
    imported by the presentation layers — the PDF writer stamps
    `user_agent()` into every document — and those layers may not reach
    the engine, not even for a version string. `app.services.versions`
    is the adapter that joins the two, exactly as it is for everything
    else.
    """
    return {
        "application": APPLICATION_VERSION,
        "release": RELEASE_NAME,
        "consultation_schema": CONSULTATION_SCHEMA_VERSION,
        "report_schema": REPORT_SCHEMA_VERSION,
    }


def reproducibility_block(settings=None, prediction=None,
                          moment: Optional[str] = None,
                          engine_versions: Optional[dict] = None) -> dict:
    """
    Part 32: enough to reproduce a result.

    The versions alone are not enough — two runs of the same build differ
    if the ayanamsha differs — so the CALCULATION settings travel with
    them. Presentation settings deliberately do not: they cannot change a
    result, and listing them here would suggest they might.

    `engine_versions` is supplied by the caller rather than read here; see
    `versions()` for why this module does not reach the engine.
    """
    block = dict(versions())
    block.update(engine_versions or {})
    if settings is not None:
        block["calculation_settings"] = {
            name: getattr(settings, name)
            for name in ("ayanamsha", "node", "house_system", "rule_profile",
                         "node_aspects", "synthesis_profile",
                         "compute_strength", "compute_ashtakavarga",
                         "compute_sensitivity", "ashtakavarga_reductions")
            if hasattr(settings, name)
        }
        varga = getattr(settings, "varga_profile", None)
        if varga:
            block["calculation_settings"]["varga_profile"] = varga
    if prediction is not None:
        block["synthesis_profile"] = getattr(prediction, "profile", None)
    if moment:
        block["target_datetime"] = moment
    block["note"] = (
        "These values are sufficient to reproduce the calculation. "
        "Presentation settings — language, chart style, report depth — are "
        "deliberately absent: they cannot change a result, and listing "
        "them here would imply they might.")
    return block


def user_agent() -> str:
    """What this build calls itself in a document's metadata."""
    return f"Jyotish Engine {RELEASE_NAME}"
