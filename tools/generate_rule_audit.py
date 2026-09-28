#!/usr/bin/env python3
"""
Generate RULE_AUDIT_V15.md (V1.5 Part 2)
------------------------------------------
    python3 tools/generate_rule_audit.py > RULE_AUDIT_V15.md

Generated rather than written by hand, for one reason: a change log that is
maintained separately from the thing it logs goes stale, and a stale
provenance document is worse than none — it reads as current.

Everything here is read from `engine.sources.registry` and
`engine.rules.catalog_textual` at run time, so the document cannot claim a
divergence the registry does not record, or miss one it does.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.rules import rules_for_profile
from engine.rules.catalog import TEXTUAL_PROFILE
from engine.rules.catalog_textual import SUPERSEDED_BY_TEXTUAL, textual_rules
from engine.sources import (
    AUDIT_RELEASE, CONFLICTS, REGISTRY_VERSION, RESOLVED_UNAVAILABLE_WORKS,
    ValidationStatus, evidence_for, witness_by_id, witnesses_for,
)
from engine.sources.registry import all_recorded_evidence
from engine.synthesis import prediction_eligibility

# Regression charts a behavioural change could show up in. Named explicitly
# because Part 2 asks which charts are affected, and "all of them" is not an
# answer anyone can check.
REGRESSION_CHARTS = {
    "jaipur_1988": "tests/test_regression_jaipur_1988.py (Meena lagna)",
    "regression_set": "tests/test_regression_charts.py (24 charts)",
    "golden": "tests/test_golden_synthesis.py (constructed cases)",
}


def _citation(witness_id: str) -> str:
    try:
        return witness_by_id(witness_id).citation()
    except KeyError:
        return witness_id


def _affected_charts(rule_id: str) -> str:
    """
    Which regression charts a change could alter.

    V1.5 changed NO default-profile behaviour, so the honest answer for every
    diverging rule is that the default output is unchanged and the corrected
    reading is reachable only by selecting the textual profile.
    """
    if rule_id.startswith("raja_yoga"):
        return (f"{REGRESSION_CHARTS['jaipur_1988']} — forms 4 Raja Yogas; "
                f"BPHS 34.15 does not fire there (no participating lord owns "
                f"a dusthana). Demonstrated instead on a constructed Mesha "
                f"chart in tests/test_rule_audit.py.")
    return ("Default profile output unchanged on every regression chart; "
            "the corrected reading is in `parashari_textual` only.")


def header() -> list[str]:
    # Two different counts, and conflating them would misreport the audit.
    # A combinatorially generated family — the 36 Raja Yogas, say — shares
    # ONE evidence record because it shares one source and one condition
    # shape. So there are few records and many affected rules, and the
    # document states both.
    diverging = [e for e in all_recorded_evidence()
                 if e.validation_status is
                 ValidationStatus.IMPLEMENTATION_DIVERGES]
    diverging_rules = [
        rule for rule in rules_for_profile("parashari")
        if evidence_for(rule.id).validation_status is
        ValidationStatus.IMPLEMENTATION_DIVERGES]
    return [
        "# RULE_AUDIT_V15.md",
        "",
        "Rule-by-rule change log for the V1.5 corpus audit.",
        "",
        f"Generated from `engine/sources/registry.py` "
        f"(version {REGISTRY_VERSION}). Do not edit by hand — regenerate "
        f"with `python3 tools/generate_rule_audit.py`.",
        "",
        "## What this document is",
        "",
        "V1.1 shipped ~110 yoga rules carrying citations like "
        "`BPHS ch.36`. Every one of those strings was written from memory by "
        "the implementing model. None had been checked against an edition, "
        "and V1.3 recorded that as the engine's largest outstanding trust "
        "gap.",
        "",
        "V1.5 obtained Sanskrit witnesses for Bṛhat Parāśara Horā Śāstra, "
        "Phaladīpikā and Jātaka Pārijāta, and checked the corpus against "
        "them chapter by chapter. This is what that found.",
        "",
        "## The headline",
        "",
        "**The doctrine was mostly real. The citations were mostly wrong.**",
        "",
        "Of the legacy citations checked, exactly one named the correct "
        "chapter: `BPHS ch.75` for the Pañca Mahāpuruṣa yogas. The Raja "
        "Yogas cited ch.36 and are at 34.11-15 and 41.28. The Dhana Yogas "
        "cited ch.40, which is the rāja-sambandha chapter; the wealth "
        "chapter is 41 and does not contain the rule the engine implements. "
        "The Moon yogas cited ch.34 and are at 37.7.",
        "",
        f"**{len(diverging_rules)} of the {len(rules_for_profile('parashari'))} "
        f"shipped rules were found to diverge from the text that was "
        f"located**, described by {len(diverging)} evidence records — "
        f"combinatorially generated families such as the 36 Raja Yogas share "
        f"one record because they share one source and one condition shape.",
        "",
        "None was edited. Each keeps its V1.4 behaviour, is marked "
        f"`IMPLEMENTATION_DIVERGES`, and has a corrected counterpart in the "
        f"`{TEXTUAL_PROFILE}` profile.",
        "",
        "## Why nothing was silently corrected",
        "",
        "Part 2 forbids editing yoga logic silently and Part 1 says that "
        "where witnesses disagree the answer is separate profiles. Both "
        "point the same way, and there is a practical reason beyond "
        "obedience: a diff nobody re-runs is not a record. Shipping the "
        "located reading beside the original means the difference is "
        "observable on any chart, by switching one flag.",
        "",
        "```",
        "  python3 main.py ... --rule-profile parashari          # V1.1 reading",
        "  python3 main.py ... --rule-profile parashari_textual  # V1.5 reading",
        "```",
        "",
    ]


def divergence_section() -> list[str]:
    lines = [
        "## Changed rules",
        "",
        "Each entry gives the fields Part 2 requires: the old software "
        "condition, the textual condition it was checked against, the "
        "difference, the new software condition, the source references, the "
        "affected regression charts, and the reason.",
        "",
    ]
    diverging = sorted(
        (e for e in all_recorded_evidence()
         if e.validation_status is ValidationStatus.IMPLEMENTATION_DIVERGES),
        key=lambda e: e.subject)

    for evidence in diverging:
        corrected = evidence.corrected_by or "—"
        lines.extend([
            f"### `{evidence.subject}`",
            "",
            f"| field | value |",
            f"| --- | --- |",
            f"| **rule_id** | `{evidence.subject}` |",
            f"| **old software condition** | {evidence.software_condition} |",
            f"| **textual / source condition** | {evidence.textual_condition} |",
            f"| **difference found** | {evidence.divergence} |",
            f"| **new software condition** | implemented as "
            f"`{corrected}` in `{TEXTUAL_PROFILE}`; the rule above is "
            f"unchanged |",
            f"| **source refs** | "
            + "<br>".join(f"`{w}` — {_citation(w)}"
                          for w in evidence.witness_ids) + " |",
            f"| **affected regression charts** | "
            f"{_affected_charts(evidence.subject)} |",
            f"| **reason for change** | "
            f"{evidence.interpretive_notes or evidence.textual_summary} |",
            f"| **prediction eligibility** | "
            f"`{prediction_eligibility(evidence.subject).value}` |",
            "",
        ])
    return lines


def negative_section() -> list[str]:
    lines = [
        "## Read and absent",
        "",
        "A category that did not exist before V1.5. `UNVERIFIED` covers both "
        "\"we never looked\" and \"we looked and it is not there\", and "
        "those leave a reader in very different positions. These rules had "
        "their cited chapter read in full in a Sanskrit witness, and the "
        "rule was not in it.",
        "",
        "| rule | cited | what the chapter actually contains |",
        "| --- | --- | --- |",
    ]
    for evidence in sorted(all_recorded_evidence(), key=lambda e: e.subject):
        if "NEGATIVE RESULT" not in evidence.textual_summary:
            continue
        summary = evidence.textual_summary.replace("NEGATIVE RESULT. ", "")
        lines.append(f"| `{evidence.subject}` | see rule `source` | {summary} |")
    lines.append("")
    return lines


def conflict_section() -> list[str]:
    lines = [
        "## Conflicts",
        "",
        "Where two reputable witnesses disagree, V1.5 models the "
        "disagreement rather than choosing. A rule carrying an unresolved "
        "conflict is barred from the evidence-gated strict profile and from "
        "strict synthesis, however well sourced it otherwise is.",
        "",
        "| id | topic | status |",
        "| --- | --- | --- |",
    ]
    for conflict in sorted(CONFLICTS, key=lambda c: c.id):
        lines.append(
            f"| `{conflict.id}` | {conflict.topic} | "
            f"{conflict.resolution_status} |")
    lines.append("")

    lines.extend([
        "### Resolved against the implementation",
        "",
        "Two V1.3 conflicts were recorded as source disagreements and turned "
        "out to be defects in the code. The distinction matters: a source "
        "conflict is a fact about the tradition and nobody's fault, and a "
        "divergence is something to fix.",
        "",
    ])
    for conflict in CONFLICTS:
        if conflict.resolution_status != "RESOLVED_AGAINST_IMPLEMENTATION":
            continue
        lines.extend([
            f"**`{conflict.id}`** — {conflict.topic}",
            "",
            f"{conflict.resolution_note}",
            "",
        ])
    return lines


def profile_section() -> list[str]:
    default = rules_for_profile("parashari")
    textual = rules_for_profile(TEXTUAL_PROFILE)
    strict = rules_for_profile("parashari_strict")
    return [
        "## Profile sizes",
        "",
        "| profile | rules | note |",
        "| --- | --- | --- |",
        f"| `parashari` | {len(default)} | unchanged from V1.4 |",
        f"| `parashari_textual` | {len(textual)} | "
        f"{len(SUPERSEDED_BY_TEXTUAL)} rules substituted, not added |",
        f"| `parashari_strict` | {len(strict)} | evidence-gated; was 1 in "
        f"V1.4 |",
        "",
        "The textual profile is **smaller** than the default, which is the "
        "opposite of the intuitive expectation. More sourcing produced "
        "fewer and stricter rules: the located Gajakesari requires Jupiter "
        "unafflicted, the located Mahāpuruṣa yogas require strength, and "
        "the located Raja Yogas carry an exception that the default has "
        "never applied.",
        "",
        "The strict profile grew from 1 rule to "
        f"{len(strict)} **without a single change to the gate**. "
        "`strict_profile_eligible` is untouched since V1.3; the growth is "
        "entirely the arrival of evidence.",
        "",
    ]


def sourcing_section() -> list[str]:
    lines = [
        "## Source acquisition",
        "",
        "V1.4 recorded a Sanskrit BPHS, Phaladīpikā and Jātaka Pārijāta as "
        "unavailable. All three were retrieved on the first attempt in V1.5, "
        "from a repository neither earlier release had tried.",
        "",
        "| work | V1.4 claim | what was actually true |",
        "| --- | --- | --- |",
    ]
    for key, entry in sorted(RESOLVED_UNAVAILABLE_WORKS.items()):
        lines.append(
            f"| {entry['work']} | {entry['v14_claim']} | "
            f"{entry['what_was_actually_true']} |")
    lines.extend([
        "",
        "This is the third release running in which a previous release's "
        "conclusion about a TEXT turned out to be a conclusion about its own "
        "SEARCH. V1.3 said BPHS was unavailable; V1.4 found a translation in "
        "minutes and then said the Sanskrit was unavailable; V1.5 found the "
        "Sanskrit in minutes. The pattern is recorded in "
        "`RESOLVED_UNAVAILABLE_WORKS` rather than tidied away.",
        "",
        "**Still not read: Sārāvalī.** A 1928 Sanskrit edition was located "
        "and downloaded in full. It is an image scan with no text layer and "
        "no OCR tool is available here, so not one verse has been read. It "
        "stays in `UNAVAILABLE_WORKS`, because having the file is not having "
        "the text — which is the distinction that table exists to make.",
        "",
        "### Licensing",
        "",
        "None of these texts is vendored. The sanskritdocuments.org files "
        "restrict themselves to personal study and research and forbid "
        "reposting; the Santhanam translation is in copyright. Under both, "
        "the engine stores the same thing: metadata, edition, locator, "
        "SHA-256, a short incipit for finding the verse, and paraphrase in "
        "the engine's own words. No running text appears anywhere in this "
        "repository or in any output it produces.",
        "",
    ])
    return lines


def status_section() -> list[str]:
    counts = Counter(
        evidence_for(rule.id).validation_status.value
        for rule in rules_for_profile("parashari"))
    lines = [
        "## Corpus status after the audit",
        "",
        "| status | rules |",
        "| --- | --- |",
    ]
    for status, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{status}` | {count} |")
    lines.extend([
        "",
        "`IMPLEMENTATION_DIVERGES` is not a worse state than `UNVERIFIED`. "
        "It is a better-understood one: an unverified rule might be right, "
        "and a diverging rule is known not to match the text it cites. The "
        "count going up is what a successful audit looks like.",
        "",
        "**Nothing is `TRADITION_VALIDATED`,** and nothing can be until a "
        "human with the texts closes the review queue. "
        + (f"{counts.get('VALIDATED_FOR_PROFILE', 0)} rule(s) reach "
           f"`VALIDATED_FOR_PROFILE`, the highest status this engine can "
           f"assert on its own."),
        "",
    ])
    return lines


def claims_section() -> list[str]:
    return [
        "## The four claims, kept separate",
        "",
        "| claim | status after V1.5 |",
        "| --- | --- |",
        "| COMPUTATIONALLY TESTED | The suite passes, including tests that "
        "pin each finding below. This says the code does what it was told "
        "to, and nothing more. |",
        "| EXTERNALLY BENCHMARKED | Astronomical positions only. No rule, "
        "mapping or synthesis output has been benchmarked against anything. |",
        "| TEXTUAL SOURCE LOCATED | Substantially improved: Sanskrit "
        "witnesses now exist for four works and the corpus has been checked "
        "against them. |",
        "| TRADITION/SOURCE VALIDATED | **Nothing.** Unchanged since V1.3. |",
        "",
        "No one of these is evidence for another. A passing test says "
        "nothing about a text; a located passage says nothing about whether "
        "the code implements it; and the audit above exists precisely "
        "because those two were being confused.",
        "",
    ]


def main() -> int:
    lines = (header() + sourcing_section() + status_section()
             + divergence_section() + negative_section()
             + conflict_section() + profile_section() + claims_section())
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
