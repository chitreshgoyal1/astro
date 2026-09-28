"""
PredictionSnapshot (V1.5 Parts 22, 25)
----------------------------------------
The date-specific counterpart to the natal ChartSnapshot.

WHY A SEPARATE OBJECT

    Part 25 requires the natal snapshot to stay immutable and free of
    date-specific synthesis, and the reason is not tidiness. A natal chart is
    true for a lifetime; a synthesis is true for an afternoon. Embedding the
    second in the first would produce a file that looks canonical, gets
    stored, and is wrong by the following week — with nothing in it to say
    which parts went stale.

    So the natal snapshot is REFERENCED, by schema version and by a content
    hash, and never copied. A consumer can tell whether a prediction was run
    against the chart it is holding.

WHAT IS IN HERE THAT IS NOT IN THE NATAL SNAPSHOT

    reliability, dasha, transits, domain_results, event_candidates, and the
    evidence appendix. All of them depend on a date.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Sequence

from .engine import SynthesisContext, synthesis_appendix
from .models import SynthesisProfile

# 1.1.0 (V1.8): ADDED the top-level `gochara` section. Additive only — every
# 1.0.0 key keeps its meaning, so a 1.0.0 reader still reads a 1.1.0
# prediction correctly and simply does not see the textual transit layer.
SCHEMA_VERSION = "1.1.0"

# The natal schema this prediction schema was written against. A consumer
# seeing a different natal schema should re-run rather than assume the
# sections line up.
EXPECTED_NATAL_SCHEMA = "1.2.0"


def natal_snapshot_id(natal_snapshot: Optional[dict]) -> Optional[str]:
    """
    A stable content hash of the natal snapshot.

    Computed over the canonicalised JSON minus its `generated` timestamp, so
    that re-serialising the same chart yields the same id. Without that
    exclusion every rebuild would produce a new id and the field would be
    useless for telling two charts apart.
    """
    if not natal_snapshot:
        return None
    payload = {k: v for k, v in natal_snapshot.items() if k != "generated"}
    encoded = json.dumps(payload, sort_keys=True, default=str,
                         ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()[:32]


@dataclass
class PredictionSnapshot:
    """One synthesis run, serialisable and fully traceable."""

    schema_version: str = SCHEMA_VERSION
    generated: str = ""
    natal_snapshot_id: Optional[str] = None
    natal_schema_version: Optional[str] = None
    datetime_utc: str = ""
    methodology_profile: str = SynthesisProfile.STANDARD.value
    reliability: dict = field(default_factory=dict)
    dasha: dict = field(default_factory=dict)
    transits: dict = field(default_factory=dict)
    # V1.8. Kept OUT of `transits` on purpose. `transits` holds positions and
    # geometric relationships, which are astronomical fact; this holds what
    # located verses say about them, which is a textual rule. Nesting the
    # second inside the first would let a reader take the first's external
    # benchmark as covering both.
    gochara: dict = field(default_factory=dict)
    domain_results: dict = field(default_factory=dict)
    event_candidates: list = field(default_factory=list)
    evidence_appendix: dict = field(default_factory=dict)
    rule_eligibility: dict = field(default_factory=dict)
    excluded_by_profile: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "generated": self.generated,
            "natal_snapshot_id": self.natal_snapshot_id,
            "natal_schema_version": self.natal_schema_version,
            "datetime": self.datetime_utc,
            "methodology_profile": self.methodology_profile,
            "reliability": self.reliability,
            "dasha": self.dasha,
            "transits": self.transits,
            "gochara": self.gochara,
            "domain_results": self.domain_results,
            "event_candidates": self.event_candidates,
            "evidence_appendix": self.evidence_appendix,
            "rule_eligibility": self.rule_eligibility,
            "excluded_by_profile": self.excluded_by_profile,
            "warnings": self.warnings,
            "claims": {
                "computationally_tested": (
                    "The synthesis logic is exercised by the V1.5 test "
                    "suite, including golden charts constructed to test "
                    "engine behaviour."),
                "externally_benchmarked": (
                    "Astronomical positions only. No synthesis output has "
                    "been benchmarked against anything."),
                "textual_source_located": (
                    "Per rule and per module; see evidence_appendix. Most "
                    "domain mappings have no located witness."),
                "tradition_source_validated": (
                    "Nothing. No rule, mapping, weight or band in this file "
                    "is TRADITION_VALIDATED."),
                "note": (
                    "These four claims are separate and none is evidence for "
                    "another."),
            },
            "not_included": [
                "natural-language interpretation",
                "event probabilities",
                "remedies, gemstones or mantras",
                "medical, death or pregnancy claims",
                "birth-time rectification",
                "machine-learned or fitted weights",
            ],
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False,
                          default=str)

    def write(self, path: str, indent: Optional[int] = 2) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.to_json(indent=indent))
            handle.write("\n")


def build_prediction_snapshot(context: SynthesisContext, *,
                              natal_snapshot: Optional[dict] = None,
                              transit_snapshot=None,
                              candidates: Sequence = (),
                              generated: Optional[datetime.datetime] = None
                              ) -> PredictionSnapshot:
    """Assemble the snapshot from a completed synthesis run."""
    data = context.to_dict()
    warnings = list(context.warnings)

    natal_schema = (natal_snapshot or {}).get("schema_version")
    if natal_schema and natal_schema != EXPECTED_NATAL_SCHEMA:
        warnings.append(
            f"Natal snapshot schema is {natal_schema}; this prediction "
            f"schema was written against {EXPECTED_NATAL_SCHEMA}. Sections "
            f"may not correspond.")

    return PredictionSnapshot(
        generated=(generated or datetime.datetime.now()).isoformat(),
        natal_snapshot_id=natal_snapshot_id(natal_snapshot),
        natal_schema_version=natal_schema,
        datetime_utc=context.moment.isoformat(),
        methodology_profile=context.profile.value,
        reliability=data["reliability"],
        dasha={
            "stack": data["dasha_stack"],
            "activation": data["dasha_activation"],
        },
        transits={
            "snapshot": (transit_snapshot.to_dict()
                         if transit_snapshot is not None else None),
            "activation": data["transit_activation"],
        },
        gochara=data["gochara"] or {},
        domain_results=data["domain_results"],
        event_candidates=[c.to_dict() for c in candidates],
        evidence_appendix=synthesis_appendix(context),
        rule_eligibility=data["rule_eligibility"],
        excluded_by_profile=data["excluded_by_profile"],
        warnings=warnings,
    )
