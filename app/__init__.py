"""
Application layer (V1.7)
========================
Everything above the engine: services, visuals, report model and the local
user interface.

THE BOUNDARY THIS PACKAGE EXISTS TO DRAW

    The engine computes astrology. This package presents it.

    Nothing in `app/` may decide an astrological question. It may not place
    a graha in a house, judge a dignity, form a yoga, weigh a strength,
    activate a domain or assign a confidence. Every such answer is read out
    of a ChartSnapshot, a PredictionSnapshot or an InterpretationDocument,
    which the engine produced and which carry their own provenance.

    The rule is enforced structurally, not by good intentions:

        app/services/   MAY import engine.*   (this is the adapter layer)
        app/visual/     MAY NOT
        app/report/     MAY NOT
        app/ui/         MAY NOT

    `tests/test_app_boundary.py` reads the import graph and fails if that
    changes. A second engine growing quietly inside a renderer is the
    specific failure this release is meant to prevent, and it is the kind
    that looks like progress while it happens.

WHY A SNAPSHOT AND NOT AN OBJECT

    The three layers that render — visual, report, ui — consume plain
    dictionaries, not engine dataclasses. A renderer given a live object can
    reach through it to a method that recomputes something; a renderer given
    a dict can only read what is written down. It also means a chart saved
    to a file in 2026 still renders in 2030 with no engine in memory, and
    the golden tests exercise exactly that path.
"""

from .errors import (
    ApplicationError, InvalidBirthDataError, LocationError,
    MethodologyError, ReportGenerationError, StorageError,
    TemplateUnavailableError, UnsupportedLanguageError,
)
from .models import (
    APPLICATION_VERSION, ApplicationSettings, BirthTimePrecision,
    ConsultationRecord, NatalResult, PredictionResult, ReportPreferences,
)

__all__ = [
    "APPLICATION_VERSION",
    "ApplicationError",
    "ApplicationSettings",
    "BirthTimePrecision",
    "ConsultationRecord",
    "InvalidBirthDataError",
    "LocationError",
    "MethodologyError",
    "NatalResult",
    "PredictionResult",
    "ReportGenerationError",
    "ReportPreferences",
    "StorageError",
    "TemplateUnavailableError",
    "UnsupportedLanguageError",
]
