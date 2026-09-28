"""
Interpretation document model (V1.6 Parts 20, 25, 26)
-------------------------------------------------------
The shape of a rendered reading.

WHAT THIS LAYER IS ALLOWED TO CONTAIN

    Sentences, and the structured facts they were rendered from. Nothing
    else. There is no field here for a judgement the synthesis layer did not
    already make, and no code in this package computes one — Part 10 is
    explicit that the renderer decides nothing about astrology, and the
    model is built so that it could not.

    Every `RenderedPhrase` carries the KEY it came from and the ARGUMENTS it
    was given. That is what makes the output auditable: a reader who doubts
    a sentence can see which template produced it and which structured value
    filled each slot, and a test can assert that the sentence says nothing
    the arguments did not contain.

THREE MODES, ONE SOURCE (Part 25)

    SUMMARY, DETAILED and TECHNICAL are three renderings of the SAME
    PredictionSnapshot. They differ in how much they show, never in what
    they claim. A test asserts that the activation level named in summary
    mode is identical to the one in technical mode for every domain.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

SCHEMA_VERSION = "1.0.0"

# The PredictionSnapshot schema this renderer was written against.
# 1.1.0 (V1.8): the prediction snapshot gained a `gochara` section. The
# renderer reads it, so the expectation moves with it. Raising this is a
# deliberate act each time: leaving it behind would fire the mismatch
# warning on every document, and racing it ahead would suppress the warning
# for a schema nobody had read.
EXPECTED_PREDICTION_SCHEMA = "1.1.0"


class ReportMode(str, Enum):
    """Part 25."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    TECHNICAL = "technical"

    @property
    def shows_evidence(self) -> bool:
        return self is not ReportMode.SUMMARY

    @property
    def shows_sources(self) -> bool:
        return self is ReportMode.TECHNICAL


@dataclass(frozen=True)
class RenderedPhrase:
    """
    One sentence, with the key and arguments that produced it.

    `key` and `args` are retained in the serialised form. They are what makes
    this layer checkable rather than merely readable: the text is a pure
    function of the two, so a reviewer can verify the sentence against the
    structured result without rerunning anything.
    """

    key: str
    text: str
    args: dict = field(default_factory=dict)

    def to_dict(self, include_provenance: bool = True) -> dict:
        data: dict = {"text": self.text}
        if include_provenance:
            data["key"] = self.key
            data["args"] = self.args
        return data


@dataclass
class DomainSection:
    """
    One domain's reading (Part 20).

    Headings are omitted when their evidence is absent, rather than printed
    empty: "Challenging factors: none" reads as a finding, and the absence
    of challenging evidence in a chart the engine barely looked at is not
    one.
    """

    domain: str
    title: str
    activation: str
    confidence: str
    overall: Optional[RenderedPhrase] = None
    confidence_phrase: Optional[RenderedPhrase] = None
    natal_foundation: list = field(default_factory=list)
    supporting: list = field(default_factory=list)
    challenging: list = field(default_factory=list)
    contradiction: Optional[RenderedPhrase] = None
    dasha: list = field(default_factory=list)
    transits: list = field(default_factory=list)
    varga: list = field(default_factory=list)
    timing: list = field(default_factory=list)
    reliability: list = field(default_factory=list)
    safety: Optional[RenderedPhrase] = None
    silence: Optional[RenderedPhrase] = None
    source_ref_ids: tuple = ()
    rule_ids: tuple = ()

    @property
    def is_silent(self) -> bool:
        return self.silence is not None

    def to_dict(self, include_provenance: bool = True) -> dict:
        def phrases(items):
            return [p.to_dict(include_provenance) for p in items]

        data = {
            "domain": self.domain,
            "title": self.title,
            "activation": self.activation,
            "confidence": self.confidence,
        }
        if self.overall:
            data["overall"] = self.overall.to_dict(include_provenance)
        if self.confidence_phrase:
            data["confidence_statement"] = self.confidence_phrase.to_dict(
                include_provenance)
        for name, items in (("natal_foundation", self.natal_foundation),
                            ("supporting_factors", self.supporting),
                            ("challenging_factors", self.challenging),
                            ("dasha_activation", self.dasha),
                            ("transit_triggers", self.transits),
                            ("varga_confirmation", self.varga),
                            ("timing", self.timing),
                            ("reliability", self.reliability)):
            if items:
                data[name] = phrases(items)
        if self.contradiction:
            data["contradiction"] = self.contradiction.to_dict(
                include_provenance)
        if self.safety:
            data["safety"] = self.safety.to_dict(include_provenance)
        if self.silence:
            data["silence"] = self.silence.to_dict(include_provenance)
        if include_provenance:
            data["source_ref_ids"] = list(self.source_ref_ids)
            data["rule_ids"] = list(self.rule_ids)
        return data


@dataclass
class TimingSection:
    """Timing that belongs to the document rather than to one domain."""

    dasha_stack: Optional[RenderedPhrase] = None
    event_candidates: list = field(default_factory=list)

    def to_dict(self, include_provenance: bool = True) -> dict:
        data: dict = {}
        if self.dasha_stack:
            data["dasha_stack"] = self.dasha_stack.to_dict(include_provenance)
        if self.event_candidates:
            data["event_candidates"] = [
                p.to_dict(include_provenance) for p in self.event_candidates]
        return data


@dataclass
class InterpretationDocument:
    """Part 26. JSON-serialisable, and never written back into a chart."""

    schema_version: str = SCHEMA_VERSION
    generated: str = ""
    language: str = "en"
    report_mode: ReportMode = ReportMode.DETAILED
    profile: str = "standard"
    generated_from_prediction_schema: Optional[str] = None
    natal_snapshot_id: Optional[str] = None
    moment: str = ""
    birth_summary: dict = field(default_factory=dict)
    methodology_summary: list = field(default_factory=list)
    domain_sections: list = field(default_factory=list)
    timing_sections: Optional[TimingSection] = None
    reliability_warnings: list = field(default_factory=list)
    technical_appendix: dict = field(default_factory=dict)
    disclaimer: Optional[RenderedPhrase] = None

    @property
    def include_provenance(self) -> bool:
        return self.report_mode is ReportMode.TECHNICAL

    def section_for(self, domain: str) -> Optional[DomainSection]:
        for section in self.domain_sections:
            if section.domain == domain:
                return section
        return None

    def to_dict(self) -> dict:
        provenance = self.include_provenance
        data = {
            "schema_version": self.schema_version,
            "generated": self.generated,
            "language": self.language,
            "report_mode": self.report_mode.value,
            "methodology_profile": self.profile,
            "generated_from_prediction_schema":
                self.generated_from_prediction_schema,
            "natal_snapshot_id": self.natal_snapshot_id,
            "datetime": self.moment,
            "birth_summary": self.birth_summary,
            "methodology_summary": [
                p.to_dict(provenance) for p in self.methodology_summary],
            "domain_sections": [
                s.to_dict(provenance) for s in self.domain_sections],
            "reliability_warnings": [
                p.to_dict(provenance) for p in self.reliability_warnings],
        }
        if self.timing_sections:
            data["timing_sections"] = self.timing_sections.to_dict(provenance)
        if self.disclaimer:
            data["disclaimer"] = self.disclaimer.to_dict(provenance)
        if self.technical_appendix:
            data["technical_appendix"] = self.technical_appendix
        data["claims"] = {
            "deterministic": (
                "Rendered by template substitution from a structured "
                "PredictionSnapshot. No language model, no generative "
                "component, no random selection."),
            "interpretation_is_not_validation": (
                "The wording here is this engine's. Nothing in it is "
                "TRADITION_VALIDATED, and readable prose is not evidence."),
        }
        data["not_included"] = [
            "medical diagnosis or prognosis",
            "death or lifespan prediction",
            "pregnancy or conception claims",
            "event probabilities",
            "remedies, gemstones or mantras",
            "financial amounts or specific outcomes",
        ]
        return data

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False,
                          default=str)

    def write(self, path: str, indent: Optional[int] = 2) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.to_json(indent=indent))
            handle.write("\n")
