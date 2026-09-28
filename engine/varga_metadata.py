"""
Varga convention metadata (V1.2 Part 12)
-----------------------------------------
Records, for every divisional convention, WHERE the rule comes from and HOW
FAR it has actually been verified — and keeps those two things apart.

The distinction this module exists to enforce:

    IMPLEMENTATION CONSISTENCY
        Two independent implementations of the same stated rule agree.
        This is what tests/test_vargas_golden.py establishes: the engine's
        table-driven combinators against a longhand transcription of the rule.
        It proves the code does what we believe the rule says. It proves
        NOTHING about whether we read the rule correctly.

    TRADITION / SOURCE VALIDATION
        The rule as implemented has been checked against the primary text, or
        against worked examples from an authority. None of the conventions
        here have had that done. Saying so is the point.

Calling a Varga "classically validated" because two implementations of one
formula agree would be a category error, and a tempting one — the test suite
is large and green. The `validation` field on every convention therefore
states the weaker claim that is actually true.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Bumped when a convention's ALGORITHM changes. A consumer that cached a
# divisional chart can compare this to know whether to recompute. It is not
# the schema version and not the application version.
VARGA_ALGORITHM_VERSION = "1.0.0"

IMPLEMENTATION_CONSISTENT = "implementation_consistency"
SOURCE_VALIDATED = "tradition_source_validated"
UNVERIFIED = "unverified"

_VALIDATION_MEANING = {
    IMPLEMENTATION_CONSISTENT: (
        "Two independent implementations of the stated rule agree across a "
        "full sweep and every division boundary. This confirms the code, not "
        "the reading of the source."),
    SOURCE_VALIDATED: (
        "Checked against the primary text or an authority's worked examples."),
    UNVERIFIED: "Not yet verified.",
}


@dataclass(frozen=True)
class ConventionMetadata:
    """Provenance and verification status of one named Varga convention."""

    chart: str                    # "D9"
    convention_id: str            # "standard", "parashari", "parivritti"
    tradition: str
    source: str
    validation: str
    algorithm_version: str = VARGA_ALGORITHM_VERSION
    notes: str = ""
    identical_to: Optional[str] = None   # another convention it duplicates
    # V1.3 Part 9: an alias is a name kept for compatibility that executes
    # identical mathematics to another name. Declaring it as such is the
    # difference between a documented synonym and a misleading choice.
    is_deprecated_alias: bool = False

    @property
    def source_evidence(self):
        """Registered RuleEvidence for this convention, if any."""
        from .sources import evidence_for
        return evidence_for(f"{self.chart}/{self.convention_id}", kind="varga")

    @property
    def source_witnesses(self):
        from .sources import witnesses_for
        return witnesses_for(f"{self.chart}/{self.convention_id}")

    def to_dict(self) -> dict:
        evidence = self.source_evidence
        data = {
            "chart": self.chart,
            "convention_id": self.convention_id,
            "tradition": self.tradition,
            "source": self.source,
            "validation": self.validation,
            "validation_meaning": _VALIDATION_MEANING[self.validation],
            "algorithm_version": self.algorithm_version,
            # V1.3: textual provenance, held separately from the
            # implementation-consistency claim above.
            "source_validation_status": evidence.validation_status.value,
            "source_classification": evidence.classification.value,
            "source_ref_ids": list(evidence.witness_ids),
            "textual_condition": evidence.textual_condition,
            "algorithm_summary": evidence.software_condition,
            "known_ambiguities": list(evidence.ambiguities),
            "needs_human_review": evidence.needs_human_review,
        }
        if self.is_deprecated_alias:
            data["is_deprecated_alias"] = True
        if self.notes:
            data["notes"] = self.notes
        if self.identical_to:
            data["identical_to"] = self.identical_to
            data["identical_note"] = (
                "Mathematically indistinguishable from the named convention "
                "at every longitude. Selecting it changes nothing.")
        return data


_BPHS = "Brihat Parashara Hora Shastra, Vargas Adhyaya"
_PARASHARI = "Parashari"
_CYCLIC = "Parivritti (cyclic counting)"

# One entry per (chart, convention). Every Varga listed in the V1.2 brief as
# needing explicit metadata is present, and so are the rest.
CONVENTION_METADATA: dict[tuple[str, str], ConventionMetadata] = {}


def _register(chart, convention_id, tradition, source, notes="",
              identical_to=None, is_deprecated_alias=False,
              validation=IMPLEMENTATION_CONSISTENT):
    CONVENTION_METADATA[(chart, convention_id)] = ConventionMetadata(
        chart=chart, convention_id=convention_id, tradition=tradition,
        source=source, validation=validation, notes=notes,
        identical_to=identical_to, is_deprecated_alias=is_deprecated_alias)


_register("D1", "standard", _PARASHARI, _BPHS,
          "The rashi itself; no division applied.")

_register("D2", "parashari", _PARASHARI, _BPHS,
          "Odd rashi: first half Simha (Surya's hora), second half Karka "
          "(Chandra's). Even rashi: reversed. Schools differ on whether the "
          "hora lord or the hora rashi is the result; this engine returns the "
          "rashi.")
_register("D2", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "24 horas counted continuously from Mesha.")

_register("D3", "parashari", _PARASHARI, _BPHS,
          "The three parts go to the rashi itself, the 5th and the 9th — the "
          "trines from it.")
_register("D3", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "36 drekkanas counted continuously from Mesha. Distinct from the "
          "Parashari rule at most longitudes.")

_register("D4", "parashari", _PARASHARI, _BPHS,
          "The four parts go to the kendras from the occupied rashi.")
_register("D4", "parivritti", _CYCLIC, "Parivritti-traya usage")

_register("D7", "parashari", _PARASHARI, _BPHS,
          "Odd rashi: count from itself. Even rashi: count from the 7th.")
_register("D7", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "Arithmetically identical to the Parashari rule here: 7 is congruent "
          "to 7 mod 12, and the cyclic offset 6s is 0 for odd rashis and 6 "
          "for even ones — exactly the parity offset the rule applies.",
          identical_to="parashari",
          is_deprecated_alias=True)

_register("D9", "standard", "Varahamihira / Parashari",
          "Bṛhajjātaka 1.6 (witness BJ_1.6_NAVAMSHA); also in the BPHS "
          "tradition, for which no witness has been obtained",
          "Fire rashis count from Mesha, earth from Makara, air from Tula, "
          "water from Karka. The one Varga rule in this engine with a located "
          "Sanskrit witness: BJ 1.6 names the four starting rashis directly. "
          "V1.2 attributed this to BPHS alone; that attribution was never "
          "checked and the actual located witness is Bṛhajjātaka.")

_register("D10", "parashari", _PARASHARI, _BPHS,
          "Odd rashi: count from itself. Even rashi: count from the 9th. "
          "A minority of sources count from the 8th for even rashis; that "
          "variant is NOT implemented and would be a separate convention id.")
_register("D10", "parivritti", _CYCLIC, "Parivritti-traya usage")

_register("D12", "parashari", _PARASHARI, _BPHS,
          "Twelve parts counted from the occupied rashi.")
_register("D12", "parivritti", _CYCLIC, "Parivritti-traya usage")

_register("D16", "parashari", _PARASHARI, _BPHS,
          "Movable rashis count from Mesha, fixed from Simha, dual from Dhanu.")
_register("D16", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "Arithmetically identical to the Parashari rule: 16 is congruent to "
          "4 mod 12, movability has period 3, and 4 x 3 is congruent to 0.",
          identical_to="parashari",
          is_deprecated_alias=True)

_register("D20", "parashari", _PARASHARI, _BPHS,
          "Movable rashis count from Mesha, fixed from Dhanu, dual from Simha.")
_register("D20", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "Arithmetically identical to the Parashari rule: 20 is congruent to "
          "8 mod 12, movability has period 3, and 8 x 3 is congruent to 0.",
          identical_to="parashari",
          is_deprecated_alias=True)

_register("D24", "parashari", _PARASHARI, _BPHS,
          "Odd rashis count from Simha, even rashis from Karka.")
_register("D24", "parivritti", _CYCLIC, "Parivritti-traya usage")

_register("D27", "parashari", _PARASHARI, _BPHS,
          "Fire rashis count from Mesha, earth from Karka, air from Tula, "
          "water from Makara.")
_register("D27", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "Arithmetically identical to the Parashari rule: 27 is congruent to "
          "3 mod 12, element has period 4, and 3 x 4 is congruent to 0.",
          identical_to="parashari",
          is_deprecated_alias=True)

_register("D30", "parashari", "Varahamihira / Parashari",
          "Bṛhajjātaka 1.7 (witness BJ_1.7_TRIMSHAMSHA) for the lord order "
          "and the odd/even reversal; the DEGREE spans are not confirmed from "
          "that witness",
          "The only Varga with UNEQUAL parts: 5/5/8/7/5 degrees, assigned to "
          "the five non-luminaries. Odd rashis take Mangal, Shani, Guru, "
          "Budha, Shukra; even rashis reverse the order and use each lord's "
          "other rashi. Because the parts are unequal, a single division span "
          "does not describe this chart and boundary tolerances must be "
          "computed per part.")
_register("D30", "movable_lords", "Variant attribution",
          "Later commentators; exact attribution not established",
          "As Parashari but Shani maps to Makara and Mangal to Mesha for both "
          "parities. Retained because V1 offered it; the source has NOT been "
          "traced, which is why its tradition field says so rather than "
          "naming a text.",
          validation=IMPLEMENTATION_CONSISTENT)
_register("D30", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "Equal 1-degree parts. This discards the unequal-part structure that "
          "defines Trimshamsha, so it is a genuinely different chart.")

_register("D40", "parashari", _PARASHARI, _BPHS,
          "Odd rashis count from Mesha, even rashis from Tula.")
_register("D40", "parivritti", _CYCLIC, "Parivritti-traya usage")

_register("D45", "parashari", _PARASHARI, _BPHS,
          "Movable rashis count from Mesha, fixed from Simha, dual from Dhanu.")
_register("D45", "parivritti", _CYCLIC, "Parivritti-traya usage")

_register("D60", "parashari", _PARASHARI, _BPHS,
          "Sixty half-degree parts counted from the occupied rashi. Equivalent "
          "to doubling the degree and counting the integer part forward.")
_register("D60", "reverse_even", "Variant attribution",
          "Later commentators; exact attribution not established",
          "Forward for odd rashis, reverse for even ones. Source not traced.",
          validation=IMPLEMENTATION_CONSISTENT)
_register("D60", "parivritti", _CYCLIC, "Parivritti-traya usage",
          "720 parts counted continuously from Mesha.")


# Charts the V1.2 brief calls out as requiring explicit metadata.
REQUIRED_METADATA_CHARTS = ("D2", "D3", "D7", "D10", "D16", "D20", "D24",
                            "D30", "D40", "D45", "D60")


def metadata_for(chart: str, convention_id: str) -> ConventionMetadata:
    key = (chart, convention_id)
    if key not in CONVENTION_METADATA:
        raise KeyError(
            f"No metadata registered for {chart}/{convention_id}. Every "
            f"convention must declare its source and verification status.")
    return CONVENTION_METADATA[key]


def convention_metadata(varga_config=None) -> dict:
    """
    Metadata for the conventions actually in force, for the snapshot.

    With no config, returns metadata for every registered convention.
    """
    from .vargas import VARGA_ORDER, VargaConfig

    config = varga_config or VargaConfig()
    active = {
        key: metadata_for(key, config.convention_for(key)).to_dict()
        for key in VARGA_ORDER
    }
    return {
        "algorithm_version": VARGA_ALGORITHM_VERSION,
        "config_source": config.source,
        "validation_levels": _VALIDATION_MEANING,
        "caveat": (
            "No Varga convention in this engine has been source-validated. "
            "Agreement between two implementations of the same stated rule "
            "confirms the code, not the reading of the text."),
        "active": active,
    }


def all_metadata() -> list[dict]:
    return [meta.to_dict() for meta in CONVENTION_METADATA.values()]


# ── expressive range (V1.8 Part 8) ──────────────────────────────────────────
#
# Not every divisional chart can say every thing. The Parāśarī horā maps the
# whole zodiac onto TWO rashis, Karka and Simha, so a D2 lagna lord is always
# Chandra or Surya and neither can be exalted or debilitated there — the only
# dignity D2 can express about its own lagna lord is "in its own sign".
#
# This matters the moment a D2 mapping becomes source-qualified, because the
# engine's varga confirmation asks about the lagna lord's dignity. In D2 that
# question has one positive answer and no negative one, so D2 can produce
# SUPPORTIVE evidence and can never produce CHALLENGING evidence.
#
# That is a property of the division, not a defect, and it is measured here
# rather than asserted: the reachable set is computed from the conventions
# themselves, so it stays correct if a convention changes. D30 is the other
# restricted chart — the Parāśarī triṃśāṃśa uses only the five non-luminary
# lords, so it reaches ten rashis and never Karka or Simha.

_REACHABLE: dict[str, frozenset] = {}


def _compute_reachable() -> dict[str, frozenset]:
    """
    Which rashis each varga can actually produce, measured.

    Sampled every 0.1°, which is finer than the smallest cell any registered
    convention uses (D60's is 0.5°), so every cell is visited.
    """
    from .vargas import compute_all_vargas

    found: dict[str, set] = {}
    for step in range(3600):
        for key, position in compute_all_vargas(step * 0.1).items():
            found.setdefault(key, set()).add(position.rashi_index)
    return {key: frozenset(value) for key, value in found.items()}


def reachable_rashis(chart: str) -> frozenset:
    """The rashis `chart` can produce. Computed once, then cached."""
    global _REACHABLE
    if not _REACHABLE:
        _REACHABLE = _compute_reachable()
    return _REACHABLE.get(chart, frozenset(range(12)))


def range_limitation(chart: str) -> str:
    """
    A caveat for a varga that cannot express the full dignity range, or "".

    Returned as a sentence for a reader, because the place it has to end up
    is beside a conclusion that rests on the chart — not in a footnote.
    """
    reachable = reachable_rashis(chart)
    if len(reachable) >= 12:
        return ""
    from .planets import RASHI_NAMES

    names = ", ".join(RASHI_NAMES[i] for i in sorted(reachable))
    return (
        f"{chart} maps the whole zodiac onto {len(reachable)} rashis "
        f"({names}), so it cannot express every dignity. Evidence drawn "
        f"from it is narrower than the same test applied to a chart that "
        f"reaches all twelve.")


def restricted_charts() -> dict[str, int]:
    """Every chart that reaches fewer than twelve rashis, and how many."""
    if not _REACHABLE:
        reachable_rashis("D1")
    return {key: len(value) for key, value in sorted(_REACHABLE.items())
            if len(value) < 12}
