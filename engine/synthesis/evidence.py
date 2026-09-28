"""
Evidence lineage (V1.5 Parts 17, 22)
--------------------------------------
Every synthesis conclusion, traced back to the things that produced it.

WHAT PART 17 ACTUALLY DEMANDS

    Not "an explanation" — a LIST. Which natal factor contributed, which
    yoga, which Shadbala component, which Ashtakavarga value, which dasha
    activated it, which transit triggered it, which varga confirmed it, and
    under which methodology profile. A sentence saying "Jupiter's influence
    is favourable" answers none of those.

WHY IDENTIFIERS AND NOT TEXT

    Part 22 forbids copying source passages into results, and the reason is
    the same one that governs the whole source layer: a chart JSON is not a
    place to redistribute a copyrighted translation, and a paraphrase pasted
    into a prediction stops being visibly a paraphrase.

    So a lineage carries stable ids — `source_ref_ids` into the witness
    registry, `rule_ids` into the catalog, `methodology_ids` and
    `calculation_ids` into the modules that computed things. A later report
    engine resolves them into an evidence appendix; this module guarantees
    they are all present and all resolvable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

from ..sources import evidence_for, witness_by_id
from .models import (
    DomainEvidence, EvidenceLayer, SynthesisResult, VargaEvidence,
)


@dataclass
class EvidenceLineage:
    """The complete provenance of one synthesis conclusion."""

    domain: str
    profile: str
    natal_factors: list = field(default_factory=list)
    yogas: list = field(default_factory=list)
    shadbala_components: list = field(default_factory=list)
    ashtakavarga_values: list = field(default_factory=list)
    dasha_lords: list = field(default_factory=list)
    transit_triggers: list = field(default_factory=list)
    varga_confirmations: list = field(default_factory=list)
    source_ref_ids: list = field(default_factory=list)
    rule_ids: list = field(default_factory=list)
    methodology_ids: list = field(default_factory=list)
    calculation_ids: list = field(default_factory=list)

    @property
    def is_traceable(self) -> bool:
        """
        Whether the conclusion rests on anything identifiable at all.

        A conclusion with no factors, no rules and no calculations behind it
        would be exactly the black box Part 17 forbids. The synthesis tests
        assert this holds for every result the engine emits.
        """
        return bool(self.natal_factors or self.yogas
                    or self.shadbala_components
                    or self.ashtakavarga_values)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "synthesis_profile": self.profile,
            "which_natal_factors": list(self.natal_factors),
            "which_yogas": list(self.yogas),
            "which_shadbala_components": list(self.shadbala_components),
            "which_ashtakavarga_values": list(self.ashtakavarga_values),
            "which_dasha_activated": list(self.dasha_lords),
            "which_transits_triggered": list(self.transit_triggers),
            "which_vargas_confirmed": list(self.varga_confirmations),
            "source_ref_ids": sorted(set(self.source_ref_ids)),
            "rule_ids": sorted(set(self.rule_ids)),
            "methodology_ids": sorted(set(self.methodology_ids)),
            "calculation_ids": sorted(set(self.calculation_ids)),
        }


def build_lineage(result: SynthesisResult) -> EvidenceLineage:
    """Extract the full lineage of one domain result."""
    lineage = EvidenceLineage(domain=result.domain,
                              profile=result.profile.value)

    for item in result.all_evidence:
        record = {
            "factor_id": item.factor_id,
            "source_type": item.source_type,
            "layer": item.layer.value,
            "direction": item.direction.value,
            "explanation_key": item.explanation_key,
        }
        if item.layer is EvidenceLayer.NATAL:
            if item.source_type == "yoga":
                lineage.yogas.append(
                    {**record, "rule_ids": list(item.rule_ids)})
            elif item.source_type == "shadbala":
                lineage.shadbala_components.append(record)
            elif item.source_type == "ashtakavarga":
                lineage.ashtakavarga_values.append(record)
            else:
                lineage.natal_factors.append(record)
        elif item.layer is EvidenceLayer.DASHA:
            lineage.dasha_lords.append(record)
        elif item.layer is EvidenceLayer.TRANSIT:
            lineage.transit_triggers.append(record)

        lineage.source_ref_ids.extend(item.source_ref_ids)
        lineage.rule_ids.extend(item.rule_ids)
        lineage.calculation_ids.extend(item.calculation_ids)
        if item.methodology_id:
            lineage.methodology_ids.append(item.methodology_id)

    for varga in result.varga_evidence:
        lineage.varga_confirmations.append({
            "chart": varga.chart,
            "factor": varga.factor,
            "direction": varga.direction.value,
            "reliability": varga.reliability.value,
            "confirms_natal_theme": varga.confirms,
        })
        lineage.source_ref_ids.extend(varga.source_ref_ids)
        if varga.methodology_id:
            lineage.methodology_ids.append(varga.methodology_id)

    return lineage


def resolve_sources(source_ref_ids: Iterable[str]) -> list[dict]:
    """
    Turn witness ids into citations for an evidence appendix.

    Metadata and a citation string only — never the passage. An id that does
    not resolve is reported as unresolved rather than dropped: a dangling
    reference in a provenance chain is a defect and should be visible.
    """
    out = []
    for ref in sorted(set(source_ref_ids)):
        try:
            witness = witness_by_id(ref)
        except KeyError:
            out.append({"id": ref, "resolved": False,
                        "note": "no registered witness with this id"})
            continue
        out.append({
            "id": witness.id,
            "resolved": True,
            "work": witness.work,
            "authority": witness.authority.value,
            "language": witness.language,
            "citation": witness.citation(),
            "edition": witness.edition,
        })
    return out


def resolve_rules(rule_ids: Iterable[str]) -> list[dict]:
    """Turn rule ids into their validation standing, for the appendix."""
    from .eligibility import prediction_eligibility

    out = []
    for rule_id in sorted(set(rule_ids)):
        record = evidence_for(rule_id)
        out.append({
            "rule_id": rule_id,
            "validation_status": record.validation_status.value,
            "classification": record.classification.value,
            "prediction_eligibility": prediction_eligibility(rule_id).value,
            "source_ref_ids": list(record.witness_ids),
            "conflicts": list(record.conflicts),
        })
    return out


def evidence_appendix(results: Sequence[SynthesisResult]) -> dict:
    """
    Everything a report engine needs to show its working.

    Deliberately assembled from the results rather than from the registry at
    large: an appendix should list what this prediction actually used, not
    everything the engine knows.
    """
    lineages = [build_lineage(r) for r in results]
    sources: list[str] = []
    rules: list[str] = []
    methodologies: list[str] = []
    for lineage in lineages:
        sources.extend(lineage.source_ref_ids)
        rules.extend(lineage.rule_ids)
        methodologies.extend(lineage.methodology_ids)

    return {
        "lineages": [lineage.to_dict() for lineage in lineages],
        "sources": resolve_sources(sources),
        "rules": resolve_rules(rules),
        "methodologies": sorted(set(methodologies)),
        "note": (
            "Stable identifiers only. No source passage is reproduced here "
            "or anywhere in the engine's output; the citations are sufficient "
            "to find the text and the texts are not redistributed."),
    }
