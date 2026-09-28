"""
Application errors (V1.7 Part 33)
===================================
One exception family, each carrying two separate things: a sentence a person
can act on, and the diagnostic detail an engineer needs.

WHY BOTH, AND WHY SEPARATE

    A traceback shown to someone filling in a birth form tells them nothing
    they can use and leaks the shape of the code. A message reading "could
    not calculate" tells the engineer nothing either.

    So every error carries `message` (shown always) and `detail` plus
    `__cause__` (shown only in debug mode). The UI decides which to print;
    neither is reconstructed from the other, because a message assembled
    from a traceback is how internals reach a user by accident.

WHAT IS NOT AN APPLICATION ERROR

    A missing template key is a defect, and V1.6 made it raise rather than
    substitute generic text. It is wrapped here as
    TemplateUnavailableError so that a report run does not die with a bare
    KeyError, but the wrapping does not make it recoverable: there is no
    fallback text, and the report is not produced.
"""

from __future__ import annotations

from typing import Optional


class ApplicationError(Exception):
    """
    Base for every error the application layer reports to a user.

    `message`  a complete sentence, safe to display, no internals.
    `detail`   the technical cause, shown only when debug mode is on.
    `hint`     what the user could do differently, when there is such a thing.
    """

    #: Shown in the UI as the error category.
    category = "Error"

    def __init__(self, message: str, detail: str = "", hint: str = "",
                 field: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail
        self.hint = hint
        self.field = field

    def to_dict(self, debug: bool = False) -> dict:
        data = {
            "category": self.category,
            "message": self.message,
            "hint": self.hint,
            "field": self.field,
        }
        if debug:
            data["detail"] = self.detail
            data["exception"] = type(self).__name__
            cause = self.__cause__
            data["cause"] = f"{type(cause).__name__}: {cause}" if cause else ""
        return data

    def __str__(self) -> str:      # what a plain `print(exc)` shows
        return self.message


class InvalidBirthDataError(ApplicationError):
    """A date, time or name the consultation form cannot accept."""

    category = "Birth details"


class LocationError(ApplicationError):
    """
    A place that cannot be resolved to coordinates and a UTC offset.

    Deliberately fatal. The engine has never substituted a default city and
    this layer does not introduce one: a chart computed from the wrong
    coordinates is confidently wrong, which is worse than no chart.
    """

    category = "Birth place"


class MethodologyError(ApplicationError):
    """An ayanamsha, profile, house system or convention that is not offered."""

    category = "Methodology"


class UnsupportedLanguageError(ApplicationError):
    """A locale with no template set installed."""

    category = "Language"


class TemplateUnavailableError(ApplicationError):
    """
    A template key the installed locale does not define.

    This is a defect in the build, not a user mistake, and the report is
    refused rather than produced with a hole in it.
    """

    category = "Interpretation"


class ReportGenerationError(ApplicationError):
    """A report that could not be built or written."""

    category = "Report"


class StorageError(ApplicationError):
    """A saved consultation that could not be read, written or migrated."""

    category = "Saved consultation"
