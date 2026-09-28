"""
Version adapter (V1.8 Parts 31, 32)
-------------------------------------
Joins the application's version identity to the engine's schema versions.

`app.version` holds what the application defines and must not reach the
engine: the PDF writer imports it for the document's Creator string, and
`app/report` may not import `engine`. This module is the adapter, in the
one package whose job that is.
"""

from __future__ import annotations

from typing import Optional

from ..version import (
    APPLICATION_VERSION, CONSULTATION_SCHEMA_VERSION, RELEASE_NAME,
    REPORT_SCHEMA_VERSION, reproducibility_block as _block, versions as _app,
)


def engine_versions() -> dict:
    """Every version the engine defines, read from where it is defined."""
    from engine.interpretation.models import SCHEMA_VERSION as interpretation
    from engine.rules import RULE_PROFILES
    from engine.snapshot import SCHEMA_VERSION as chart
    from engine.sources.registry import REGISTRY_VERSION
    from engine.synthesis.snapshot import SCHEMA_VERSION as prediction
    from engine.varga_metadata import VARGA_ALGORITHM_VERSION

    return {
        "chart_schema": chart,
        "prediction_schema": prediction,
        "interpretation_schema": interpretation,
        "source_registry": REGISTRY_VERSION,
        "varga_algorithm": VARGA_ALGORITHM_VERSION,
        "rule_profiles": len(RULE_PROFILES),
    }


def versions() -> dict:
    """Everything that identifies this build, application and engine."""
    data = _app()
    data.update(engine_versions())
    return data


def reproducibility_block(settings=None, prediction=None,
                          moment: Optional[str] = None) -> dict:
    """Part 32's record, with the engine versions filled in."""
    return _block(settings=settings, prediction=prediction, moment=moment,
                  engine_versions=engine_versions())
