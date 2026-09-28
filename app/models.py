"""
Application state (V1.7 Parts 3, 4, 30, 32)
=============================================
The objects a consultation is made of, kept strictly apart from the objects a
calculation produces.

THE SEPARATION PART 30 ASKS FOR

    ConsultationInput      what a person typed.            Mutable.
    ApplicationSettings    how they want it computed.      Mutable.
    NatalResult            what the engine computed.       Frozen.
    PredictionResult       what it computed for a moment.  Frozen.
    ReportPreferences      how they want it presented.     Mutable.

    Changing a display preference must never alter a snapshot. So the
    results are frozen dataclasses holding already-serialised dictionaries,
    and a settings change produces a NEW result by recomputation rather than
    by mutation. A UI that could edit a snapshot in place would be able to
    publish a chart that no calculation ever produced.

BIRTH-TIME PRECISION (Part 4)

    A form field reading `10:35` has told us the minute. It has not told us
    that the seconds were zero. V1.5's reliability layer already acts on
    this; what was missing was any way for a user to say how good the time
    actually is, so every chart was implicitly treated as minute-exact.

    `BirthTimePrecision` is that input. It is stored beside the time, never
    folded into it, and it only ever widens the uncertainty — there is no
    setting that makes the engine treat a time as better than entered.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Optional

#: Re-exported from `app.version`, which is the single source Part 31
#: requires. Kept importable from here because every existing caller
#: reaches for `app.models.APPLICATION_VERSION`, and moving a constant
#: is a breaking change for no benefit once it has one definition.
from .version import APPLICATION_VERSION, CONSULTATION_SCHEMA_VERSION


class BirthTimePrecision(str, Enum):
    """
    How well the birth time is actually known (Part 4).

    The seconds each band corresponds to are an uncertainty half-width fed
    to the V1.5 reliability gate, which decides what evidence may be leaned
    on. They are not a claim about the person's memory; they are what the
    engine is told it may assume.
    """

    EXACT_TO_SECOND = "EXACT_TO_SECOND"
    EXACT_TO_MINUTE = "EXACT_TO_MINUTE"
    APPROX_5_MIN = "APPROX_5_MIN"
    APPROX_15_MIN = "APPROX_15_MIN"
    UNKNOWN = "UNKNOWN"

    @property
    def seconds(self) -> int:
        """
        The uncertainty to compute with.

        UNKNOWN does not mean "no uncertainty" and does not mean "skip the
        check". It means the time is not evidence, and it maps to the
        widest band so that everything birth-time sensitive — the D60
        Lagna, and on a bad day the Lagna itself — is reported as
        unresolved rather than as a number.
        """
        return _PRECISION_SECONDS[self]

    @property
    def is_stated(self) -> bool:
        """Whether the user actually told us, as opposed to a default."""
        return self is not BirthTimePrecision.UNKNOWN

    @property
    def label(self) -> str:
        return _PRECISION_LABELS[self]

    @property
    def basis(self) -> str:
        """The sentence the reliability layer records as `precision_basis`."""
        return _PRECISION_BASIS[self]

    @classmethod
    def from_time_text(cls, text: str) -> "BirthTimePrecision":
        """
        Infer the precision a typed time can support, and no more.

        `10:35`    → EXACT_TO_MINUTE
        `10:35:20` → EXACT_TO_SECOND
        anything unparseable → UNKNOWN

        This is the floor, not the answer: a user who knows the time came
        off a hospital clock to the minute and a user who is repeating a
        family story both type `10:35`. The form asks; this is what it
        falls back to.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return cls.UNKNOWN
        parts = cleaned.split(":")
        if len(parts) >= 3 and parts[2].strip():
            return cls.EXACT_TO_SECOND
        if len(parts) == 2:
            return cls.EXACT_TO_MINUTE
        return cls.UNKNOWN


_PRECISION_SECONDS = {
    BirthTimePrecision.EXACT_TO_SECOND: 1,
    BirthTimePrecision.EXACT_TO_MINUTE: 60,
    BirthTimePrecision.APPROX_5_MIN: 300,
    BirthTimePrecision.APPROX_15_MIN: 900,
    # An hour. Wide enough that on most days the Lagna itself is unresolved,
    # which is the honest answer when the time is not known.
    BirthTimePrecision.UNKNOWN: 3600,
}

_PRECISION_LABELS = {
    BirthTimePrecision.EXACT_TO_SECOND: "Exact to the second",
    BirthTimePrecision.EXACT_TO_MINUTE: "Exact to the minute",
    BirthTimePrecision.APPROX_5_MIN: "Approximate, within 5 minutes",
    BirthTimePrecision.APPROX_15_MIN: "Approximate, within 15 minutes",
    BirthTimePrecision.UNKNOWN: "Not known",
}

_PRECISION_BASIS = {
    BirthTimePrecision.EXACT_TO_SECOND:
        "stated as exact to the second on the consultation form",
    BirthTimePrecision.EXACT_TO_MINUTE:
        "stated as exact to the minute on the consultation form",
    BirthTimePrecision.APPROX_5_MIN:
        "stated as approximate within 5 minutes on the consultation form",
    BirthTimePrecision.APPROX_15_MIN:
        "stated as approximate within 15 minutes on the consultation form",
    BirthTimePrecision.UNKNOWN:
        "not stated; the widest band is assumed and nothing birth-time "
        "sensitive is treated as resolved",
}


# ── settings ─────────────────────────────────────────────────────────────────

@dataclass
class ApplicationSettings:
    """
    Every methodology choice, with its default visible (Part 3).

    Defaults are shown, never hidden. A user who does not understand
    ayanamsha should not have to, and a user who does should be able to see
    in one place which one produced the chart in front of them — which is
    also what the methodology panel renders.
    """

    # Astronomy.
    ayanamsha: str = "lahiri"
    node: str = "true"                       # true | mean

    # Astrological convention.
    house_system: str = "whole_sign"
    varga_profile: Optional[str] = None      # path to a varga config, or None
    # Mirrors engine.rules.DEFAULT_PROFILE. Written out rather than imported
    # so this module stays free of the engine; a test asserts they agree, so
    # the two cannot drift apart silently.
    rule_profile: str = "parashari"
    node_aspects: str = "parashari_like"

    # Synthesis.
    synthesis_profile: str = "standard"

    # PRESENTATION, and the odd one out (Part 27).
    #
    # Language belongs with the presentation settings and is kept here for
    # one reason: every existing caller reads `settings.language`, and the
    # engine's interpretation layer is handed it from here. Moving the
    # field would be a breaking change across the whole application.
    #
    # So it stays, and `calculation_settings()` EXCLUDES it — the saved
    # file, the reproducibility block and the methodology panel all take
    # their calculation list from that method rather than from `to_dict`,
    # which is what actually enforces the separation.
    language: str = "en"

    # What to compute. All default on; the UI exposes them for speed.
    compute_strength: bool = True
    compute_ashtakavarga: bool = True
    compute_sensitivity: bool = True
    ashtakavarga_reductions: bool = False    # unverified; off unless asked

    def to_dict(self) -> dict:
        return {
            "ayanamsha": self.ayanamsha,
            "node": self.node,
            "house_system": self.house_system,
            "varga_profile": self.varga_profile,
            "rule_profile": self.rule_profile,
            "node_aspects": self.node_aspects,
            "synthesis_profile": self.synthesis_profile,
            "language": self.language,
            "compute_strength": self.compute_strength,
            "compute_ashtakavarga": self.compute_ashtakavarga,
            "compute_sensitivity": self.compute_sensitivity,
            "ashtakavarga_reductions": self.ashtakavarga_reductions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApplicationSettings":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (data or {}).items() if k in known})

    #: Settings that can change a calculation. Part 27's list, written out
    #: so that a new field has to be classified deliberately rather than
    #: inheriting a category from where it happened to be declared.
    CALCULATION_FIELDS = (
        "ayanamsha", "node", "house_system", "varga_profile", "rule_profile",
        "node_aspects", "synthesis_profile", "compute_strength",
        "compute_ashtakavarga", "compute_sensitivity",
        "ashtakavarga_reductions",
    )

    #: Settings that cannot. Language lives on this object for historical
    #: reasons; it is classified correctly here.
    PRESENTATION_FIELDS = ("language",)

    def calculation_settings(self) -> dict:
        """
        Only the settings that can change a result.

        Part 27: "Presentation changes must never modify astrology
        output." The way to keep that true is to make the calculation set
        explicit and derive everything that depends on it — the saved
        file, the reproducibility block, the cache key — from this one
        method.
        """
        return {name: getattr(self, name) for name in self.CALCULATION_FIELDS}

    def presentation_settings(self) -> dict:
        return {name: getattr(self, name)
                for name in self.PRESENTATION_FIELDS}

    def replace(self, **changes) -> "ApplicationSettings":
        """A copy with changes. Never mutates, so a snapshot cannot drift."""
        return replace(self, **changes)

    def non_default(self) -> dict:
        """Which settings differ from the shipped defaults."""
        defaults = ApplicationSettings().to_dict()
        return {k: v for k, v in self.to_dict().items() if defaults[k] != v}


@dataclass
class ReportPreferences:
    """How a report should be presented. Never affects a calculation."""

    mode: str = "detailed"                   # summary | detailed | technical
    language: str = "en"
    page_size: str = "a4"
    include_charts: tuple[str, ...] = ("D1", "D9", "D10")
    chart_style: str = "north_indian"
    chart_detail: str = "STANDARD"           # COMPACT | STANDARD | DETAILED
    include_source_appendix: bool = True

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "language": self.language,
            "page_size": self.page_size,
            "include_charts": list(self.include_charts),
            "chart_style": self.chart_style,
            "chart_detail": self.chart_detail,
            "include_source_appendix": self.include_source_appendix,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReportPreferences":
        data = dict(data or {})
        if "include_charts" in data:
            data["include_charts"] = tuple(data["include_charts"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


# ── consultation ─────────────────────────────────────────────────────────────

@dataclass
class ConsultationRecord:
    """
    One saved consultation: the input, the precision, and the methodology.

    This is the unit of persistence (Part 31). It holds everything needed to
    RECOMPUTE, and nothing that was computed. A cached snapshot may be
    stored alongside it, but the record alone is sufficient — which is what
    makes a saved consultation survive an engine change instead of
    preserving a stale answer.
    """

    name: str
    date_of_birth: str                       # YYYY-MM-DD
    time_of_birth: str                       # HH:MM or HH:MM:SS
    place: str
    precision: BirthTimePrecision = BirthTimePrecision.EXACT_TO_MINUTE
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    timezone_name: Optional[str] = None
    utc_offset: Optional[str] = None
    settings: ApplicationSettings = field(default_factory=ApplicationSettings)
    report: ReportPreferences = field(default_factory=ReportPreferences)
    notes: str = ""
    entered_positions: dict = field(default_factory=dict)
    created: str = ""
    # Versions, recorded at save time. See app/storage.py for what they do.
    application_version: str = APPLICATION_VERSION
    schema_version: str = CONSULTATION_SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "application_version": self.application_version,
            "created": self.created or datetime.datetime.now().isoformat(
                timespec="seconds"),
            "input": {
                "name": self.name,
                "date_of_birth": self.date_of_birth,
                "time_of_birth": self.time_of_birth,
                "birth_time_precision": self.precision.value,
                "place": self.place,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "timezone": self.timezone_name,
                "utc_offset": self.utc_offset,
                "notes": self.notes,
                "entered_positions": dict(self.entered_positions),
            },
            # SCHEMA 2.0.0 (V1.8, Parts 23, 24, 27). The flat `settings`
            # block became two, because one of them can change a chart and
            # the other cannot. A reader of a v1 file could not tell which
            # of its keys were which, and `language` sitting in `settings`
            # beside `ayanamsha` actively suggested they were the same kind
            # of thing.
            "calculation": self.settings.calculation_settings(),
            # `language` is the one field that exists on BOTH objects —
            # `ApplicationSettings.language` drives the interpretation and
            # `ReportPreferences.language` drives the document. They are
            # kept in step by every caller, and the saved file records ONE
            # value, so the precedence has to be a decision rather than a
            # dict-merge accident.
            #
            # The REPORT's value wins, because that is the object whose
            # entire purpose is presentation. `language_in_effect` states
            # the same rule for readers, and a test pins it.
            "presentation": {
                **self.settings.presentation_settings(),
                **self.report.to_dict(),
            },
        }

    @property
    def language_in_effect(self) -> str:
        """The presentation language a saved file will record."""
        return self.report.language


# ── results ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NatalResult:
    """
    A computed natal chart, as data.

    Frozen, and `snapshot` is the serialised ChartSnapshot rather than the
    dataclass, so that everything downstream reads the same representation a
    saved file would give it. `engine_objects` carries the live objects for
    the services that legitimately need them (synthesis needs `features`);
    no renderer is given it.
    """

    snapshot: dict
    warnings: tuple[str, ...] = ()
    engine_objects: dict = field(default_factory=dict, repr=False,
                                 compare=False)

    @property
    def schema_version(self) -> str:
        return self.snapshot.get("schema_version", "")

    @property
    def name(self) -> str:
        return (self.snapshot.get("birth", {}) or {}).get("name") or "Unknown"

    def section(self, key: str) -> Any:
        return self.snapshot.get(key, {})


@dataclass(frozen=True)
class PredictionResult:
    """A synthesis for one moment, as data."""

    snapshot: dict
    moment: str = ""
    profile: str = "standard"
    warnings: tuple[str, ...] = ()
    engine_objects: dict = field(default_factory=dict, repr=False,
                                 compare=False)

    @property
    def schema_version(self) -> str:
        return self.snapshot.get("schema_version", "")

    @property
    def domains(self) -> list:
        return self.snapshot.get("domains", []) or []
