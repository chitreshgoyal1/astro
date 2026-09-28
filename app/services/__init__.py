"""
Application services (V1.7 Part 2)
====================================
The only place where the application layer is allowed to touch the engine.

    calculate_chart(consultation, settings)      → NatalResult
    calculate_prediction(natal, moment, profile) → PredictionResult
    render_interpretation(prediction, locale, mode) → InterpretationDocument
    generate_report(...)                         → ReportDocument / PDF bytes

Four operations, each taking plain application state and returning plain
serialisable data. The UI calls these and nothing else; `test_app_boundary`
checks that it cannot call anything else even by accident.

These are adapters, not logic. Where a service looks like it is deciding
something astrological, it is translating a user-facing option into an
engine argument — `BirthTimePrecision.APPROX_5_MIN` into the 300 seconds
the V1.5 reliability gate expects, for instance. The gate still decides.
"""

from .chart_service import calculate_chart, chart_visual_model
from .prediction_service import (
    calculate_prediction, render_interpretation, timeline_candidates,
)
from .report_service import generate_html, generate_pdf, generate_report
from .release import (
    RELEASE_DEFAULTS, audit as release_audit, describe_options,
    release_settings, release_warnings,
)
from .settings_service import (
    available_options, describe_methodology, validate_settings,
)
from .storage_service import (
    describe_storage, export_consultations, import_consultations,
    load_consultation, save_consultation,
)
from .version_service import engine_versions, reproducibility_block, versions

__all__ = [
    "RELEASE_DEFAULTS",
    "available_options",
    "describe_options",
    "release_audit",
    "release_settings",
    "release_warnings",
    "describe_storage",
    "engine_versions",
    "export_consultations",
    "import_consultations",
    "load_consultation",
    "reproducibility_block",
    "save_consultation",
    "versions",
    "calculate_chart",
    "calculate_prediction",
    "chart_visual_model",
    "describe_methodology",
    "generate_html",
    "generate_pdf",
    "generate_report",
    "render_interpretation",
    "timeline_candidates",
    "validate_settings",
]
