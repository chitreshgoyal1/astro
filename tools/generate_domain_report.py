#!/usr/bin/env python3
"""
Generate DOMAIN_VALIDATION.md (V1.6 Part 8)
---------------------------------------------
    python3 tools/generate_domain_report.py > DOMAIN_VALIDATION.md

Generated from `engine.synthesis.domains`, for the same reason
RULE_AUDIT_V15.md is generated from the registry: a coverage document
maintained by hand goes stale, and a stale provenance document is worse than
none because it reads as current.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.sources import witness_by_id
from engine.sources.editions import BPHS_SANSKRIT_SD_EDITION_IDENTITY
from engine.synthesis.domain_evidence import FACTOR_TYPE_MEANING, FactorType
from engine.synthesis.domains import (
    DOMAINS, Domain, domain_mapping_summary, strict_domains,
)

# What V1.5 shipped, for the before/after the brief asks for. Hard-coded
# because it is history: the V1.5 module had no per-factor evidence at all,
# so it cannot be recomputed from anything still in the tree.
V15_BASELINE = {
    "house_mappings_located": 0,
    "house_mappings_total": 17,
    "karakas_located": 5,
    "karakas_total": 30,
    "strict_domains": ["CHILDREN", "FAMILY", "MARRIAGE", "SIBLINGS"],
}

# Mappings V1.6 changed outright, as against merely sourcing.
CORRECTIONS = [
    ("EDUCATION", "primary house 4 → 5",
     "BPHS 11.6 places `vidyā` (learning) and `buddhi` (the intellect) in "
     "the FIFTH bhāva. The fourth, at 11.5, gets vehicles, relatives, the "
     "mother's comfort, treasure, land and house — and no learning. V1.5 "
     "had followed a modern convention the text does not support."),
    ("TRAVEL", "houses 3, 9, 12 → 3, 7, 9",
     "BPHS 11.4 gives `prayāṇa` from the third, 11.8 `adhva-prayāṇa` (road "
     "travel) from the seventh and 11.10 `tīrthayātrā` (pilgrimage) from "
     "the ninth. The twelfth, at 11.13, gets expenditure and news of "
     "enemies; V1.5's twelfth is dropped."),
    ("SPIRITUALITY", "added houses 5 and 12",
     "BPHS 11.6 gives `yantra-mantra` from the fifth and BPHS 23.10 gives "
     "`mokṣa` from a well-disposed twelfth."),
    ("RELATIONSHIPS", "marked unsourced",
     "BPHS 11.8 gives the seventh `jāyā` — the wife — specifically. No "
     "witness supports a general relationships domain distinct from "
     "marriage. The domain is retained and excluded from strict synthesis."),
    ("CHILDREN", "putrakāraka Saturn → Jupiter, both retained",
     "V1.5 read BPHS 32.20 (`putraḥ śanaiścarāt`) and registered a conflict "
     "with modern practice. BPHS 32.23, four verses later, gives a second "
     "kāraka scheme and says `devejyāt pañcamāt putro` — the son from "
     "Jupiter. The disagreement is between two schemes inside one chapter, "
     "not between BPHS and modernity."),
]


def _citation(ref: str) -> str:
    try:
        return witness_by_id(ref).citation()
    except KeyError:
        return f"{ref} (unresolved)"


def header() -> list[str]:
    summary = domain_mapping_summary()
    return [
        "# DOMAIN_VALIDATION.md",
        "",
        "Source coverage for the 17 life domains of the synthesis engine.",
        "",
        "Generated from `engine/synthesis/domains.py`. Do not edit by hand — "
        "regenerate with `python3 tools/generate_domain_report.py`.",
        "",
        "## What this closes",
        "",
        "V1.5 shipped 17 domains and recorded that **not one** house mapping "
        "had a located witness. That was the release's largest remaining "
        "gap, and it had a visible consequence: strict synthesis could "
        "speak about four domains, because the only source-qualified "
        "factor→domain links in the whole engine were kāraka attributions.",
        "",
        "V1.6 read BPHS chapter 11 — `bhāvaviveka` — which is the "
        "house-signification chapter, and chapters 21 to 24, which give the "
        "phala of the tenth, eleventh and twelfth houses and the doctrine "
        "of the house lords. Most of the mappings turn out to be attested, "
        "several of them in a single word.",
        "",
        "| | V1.5 | V1.6 |",
        "| --- | --- | --- |",
        f"| House mappings with a witness | "
        f"{V15_BASELINE['house_mappings_located']} | "
        f"{summary['house_mappings_located']} of "
        f"{summary['house_mappings_total']} |",
        f"| Kārakas with a witness | {V15_BASELINE['karakas_located']} | "
        f"{summary['karakas_with_located_witness']} of "
        f"{summary['karakas_total']} |",
        f"| Domains strict synthesis admits | "
        f"{len(V15_BASELINE['strict_domains'])} | "
        f"{len(strict_domains())} of 17 |",
        f"| Varga mappings with a witness | 0 | 0 |",
        "",
        "The varga row is unchanged and is the gap V1.6 did **not** close. "
        "BPHS chapters 6 and 7 give the ṣoḍaśavarga and how to compute them; "
        "no passage in any witness this engine holds assigns a divisional "
        "chart to a life area. D10-for-career and D9-for-marriage remain "
        "modern convention, however universal.",
        "",
    ]


def factor_type_section() -> list[str]:
    lines = [
        "## The five factor types",
        "",
        "A domain is not a house plus some kārakas. It is a list of "
        "factor→domain links, each making one of five kinds of claim with "
        "its own evidence. Collapsing them would hide which is sourced: "
        "CAREER has an attested HOUSE link, an attested HOUSE_LORD link and "
        "an unsourced VARGA link, and a reader should be able to see that.",
        "",
        "| type | meaning | located | source-qualified |",
        "| --- | --- | --- | --- |",
    ]
    coverage = domain_mapping_summary()["coverage_by_factor_type"]
    for factor_type in FactorType:
        stats = coverage[factor_type.value]
        meaning = FACTOR_TYPE_MEANING[factor_type].split(".")[0] + "."
        lines.append(
            f"| `{factor_type.value}` | {meaning} | "
            f"{stats['located']}/{stats['total']} | "
            f"{stats['source_qualified']}/{stats['total']} |")
    lines.append("")
    return lines


def corrections_section() -> list[str]:
    lines = [
        "## Mappings V1.6 corrected",
        "",
        "Sourcing a mapping and changing one are different outcomes. These "
        "are the changes, as against the much larger set of mappings that "
        "were already right and simply had no citation.",
        "",
    ]
    for domain, change, why in CORRECTIONS:
        lines.extend([f"### {domain} — {change}", "", why, ""])
    return lines


def domain_sections() -> list[str]:
    lines = ["## Domain by domain", ""]
    for domain in Domain:
        spec = DOMAINS[domain]
        lines.extend([
            f"### {domain.value}",
            "",
            f"*{spec.label}* — reference space `{spec.reference_space.value}`, "
            f"profile `{spec.methodology_profile}`, "
            f"strict eligible: **{'yes' if spec.strict_eligible else 'no'}**",
            "",
            "| factor | type | primary | status | witness |",
            "| --- | --- | --- | --- | --- |",
        ])
        for mapping in spec.mappings:
            refs = ("<br>".join(f"`{r}`" for r in mapping.source_ref_ids)
                    or "*none*")
            mark = "✓" if mapping.is_source_qualified else "—"
            lines.append(
                f"| {mapping.factor} | `{mapping.factor_type.value}` | "
                f"{'primary' if mapping.is_primary else 'secondary'} | "
                f"{mark} {mapping.validation_status.value} | {refs} |")
        lines.append("")

        terms = [f"`{m.textual_term}`" for m in spec.mappings
                 if m.textual_term]
        if terms:
            lines.append(f"Textual terms located: {', '.join(terms)}.")
            lines.append("")
        conflicts = sorted({c for m in spec.mappings for c in m.conflicts})
        if conflicts:
            lines.append(
                "Conflicts: " + ", ".join(f"`{c}`" for c in conflicts) + ".")
            lines.append("")
        if spec.notes:
            lines.append(f"{spec.notes}")
            lines.append("")
    return lines


def unsourced_section() -> list[str]:
    lines = [
        "## What remains unsourced",
        "",
        "| domain | factor | type | why |",
        "| --- | --- | --- | --- |",
    ]
    for domain in Domain:
        for mapping in DOMAINS[domain].mappings:
            if mapping.is_source_qualified:
                continue
            why = (mapping.notes or "no witness located").replace("\n", " ")
            if len(why) > 180:
                why = why[:177] + "…"
            lines.append(
                f"| {domain.value} | {mapping.factor} | "
                f"`{mapping.factor_type.value}` | {why} |")
    lines.append("")
    return lines


def edition_section() -> list[str]:
    identity = BPHS_SANSKRIT_SD_EDITION_IDENTITY
    lines = [
        "## The edition question (Part 5)",
        "",
        f"**Status: {identity['status']}.**",
        "",
        "Every locator in this document is a chapter-and-verse reference "
        "into one witness, and BPHS chapter numbering is precisely what "
        "varies between editions. V1.6 went looking for the printed "
        "exemplar behind the transliteration and did not find it.",
        "",
        "| | |",
        "| --- | --- |",
    ]
    for key, value in sorted(identity["what_is_known"].items()):
        lines.append(f"| {key.replace('_', ' ')} | {value} |")
    lines.extend([
        "",
        f"**Not known:** {identity['what_is_not_known']}",
        "",
        f"**Why it matters:** {identity['why_it_matters']}",
        "",
        f"**Tried in V1.6:** {identity['what_was_tried_in_v16']}",
        "",
        f"**Consequence:** {identity['consequence_for_validation']}",
        "",
    ])
    return lines


def claims_section() -> list[str]:
    return [
        "## The four claims, kept separate",
        "",
        "| claim | status for the domain layer |",
        "| --- | --- |",
        "| COMPUTATIONALLY TESTED | The mappings are exercised by the suite, "
        "including a test that the strict gate refuses an unsourced factor "
        "inside a sourced domain. |",
        "| EXTERNALLY BENCHMARKED | Nothing. No domain mapping has been "
        "tested against any outcome, and none could be by this engine. |",
        "| TEXTUAL SOURCE LOCATED | Substantially improved — this document. |",
        "| TRADITION/SOURCE VALIDATED | **Nothing.** A located passage is "
        "not a confirmed reading, and the exemplar behind the witness is "
        "still unidentified. |",
        "",
        "Finding that BPHS 11.11 gives the tenth house `vṛtti` establishes "
        "that the mapping has a textual basis. It does not establish that "
        "the engine's use of it is what the tradition intends, and no "
        "amount of further reading by this engine could.",
        "",
    ]


def main() -> int:
    lines = (header() + factor_type_section() + corrections_section()
             + domain_sections() + unsourced_section() + edition_section()
             + claims_section())
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
