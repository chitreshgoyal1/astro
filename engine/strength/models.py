"""
Shadbala models (V1.4 Parts 3, 9)
----------------------------------
Every component of Shadbala is a separate object carrying its own value, its
own methodology profile and its own provenance. Shadbala is not one number: it
is six strengths, most of which are themselves sums of subcomponents, and
collapsing them loses exactly the information that makes the total meaningful.

UNITS

    Virupa   the working unit. One rupa = 60 virupas.
    Rupa     virupas / 60.

    Both are kept. The classical requirements are stated in virupas, the
    conventional presentation is in rupas, and converting early would force
    every consumer to convert back.

PROVENANCE

    Source: Bṛhat Parāśara Horā Śāstra ch. 27, in the R. Santhanam
    translation (witness BPHS_27_SHADBALA). That is a TRANSLATION-tier
    witness, so nothing here can reach TRADITION_VALIDATED — see
    engine/sources/.

    A total is only as validated as its weakest constituent. `ShadbalaResult`
    computes its own status from its components rather than being told one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

VIRUPAS_PER_RUPA = 60.0

# BPHS 27.32-33: the Shadbala Pinda each graha needs to be reckoned strong,
# in virupas. Read from the Santhanam translation; two digits are OCR-damaged
# in that copy ("3*0", "42C") and were resolved to the values the surrounding
# arithmetic requires. Recorded as an ambiguity in the source registry.
REQUIRED_VIRUPAS: dict[str, float] = {
    "Surya": 390.0,
    "Chandra": 360.0,
    "Mangal": 300.0,
    "Budha": 420.0,
    "Guru": 390.0,
    "Shukra": 330.0,
    "Shani": 300.0,
}

# Shadbala is computed for the seven grahas from the Sun to Saturn.
# BPHS 27: "The nodes are not considered." Rahu and Ketu are therefore absent
# by instruction, not by oversight.
SHADBALA_GRAHAS = ("Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra",
                   "Shani")


@dataclass(frozen=True)
class BalaComponent:
    """
    One named strength contribution.

    `validation_status` is per-component on purpose. Uchcha Bala is stated
    plainly in the witness; Varsha and Masa Bala depend on an Ahargana epoch
    the witness describes but does not fix unambiguously. Reporting one status
    for the whole of Shadbala would hide that difference.
    """

    name: str
    value_virupa: float
    calculation_profile: str
    source_ref_ids: tuple[str, ...] = ()
    validation_status: str = "UNVERIFIED"
    detail: str = ""
    subcomponents: tuple["BalaComponent", ...] = ()
    is_approximation: bool = False
    approximation_note: str = ""

    @property
    def value_rupa(self) -> float:
        return self.value_virupa / VIRUPAS_PER_RUPA

    def to_dict(self) -> dict:
        data = {
            "component": self.name,
            "value_virupa": round(self.value_virupa, 4),
            "value_rupa": round(self.value_rupa, 5),
            "calculation_profile": self.calculation_profile,
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status,
        }
        if self.detail:
            data["detail"] = self.detail
        if self.is_approximation:
            data["is_approximation"] = True
            data["approximation_note"] = self.approximation_note
        if self.subcomponents:
            data["subcomponents"] = [s.to_dict() for s in self.subcomponents]
        return data


# Ranked weakest-first, so a total can report its floor.
_STATUS_ORDER = (
    "UNVERIFIED", "TEXT_LOCATED", "WITNESS_RECORDED", "TRANSLATION_CHECKED",
    "RULE_INTERPRETATION_MAPPED", "IMPLEMENTATION_MATCHED",
    "SECOND_WITNESS_CHECKED", "TRADITION_VALIDATED",
)


def weakest_status(components) -> str:
    """
    The weakest validation status among the components.

    Part 9: a total must not be labelled better-validated than its worst
    constituent. Shadbala is a sum, and a sum inherits the weakest term's
    standing.
    """
    statuses = [c.validation_status for c in components]
    if not statuses:
        return "UNVERIFIED"
    return min(statuses,
               key=lambda s: _STATUS_ORDER.index(s)
               if s in _STATUS_ORDER else 0)


@dataclass
class ShadbalaResult:
    """The six strengths of one graha, with every intermediate value kept."""

    planet: str
    sthana_bala: BalaComponent
    dig_bala: BalaComponent
    kala_bala: BalaComponent
    chesta_bala: BalaComponent
    naisargika_bala: BalaComponent
    drik_bala: BalaComponent
    methodology_profile: str = "bphs_santhanam"
    notes: tuple[str, ...] = ()

    @property
    def components(self) -> tuple[BalaComponent, ...]:
        return (self.sthana_bala, self.dig_bala, self.kala_bala,
                self.chesta_bala, self.naisargika_bala, self.drik_bala)

    @property
    def total_virupa(self) -> float:
        return sum(c.value_virupa for c in self.components)

    @property
    def total_rupa(self) -> float:
        return self.total_virupa / VIRUPAS_PER_RUPA

    @property
    def required_virupa(self) -> float:
        return REQUIRED_VIRUPAS[self.planet]

    @property
    def required_rupa(self) -> float:
        return self.required_virupa / VIRUPAS_PER_RUPA

    @property
    def ratio(self) -> float:
        """Total against requirement. Above 1.0 meets the classical bar."""
        return self.total_virupa / self.required_virupa

    @property
    def meets_requirement(self) -> bool:
        return self.ratio >= 1.0

    @property
    def validation_status(self) -> str:
        """Inherited from the weakest component — never asserted directly."""
        return weakest_status(self.components)

    @property
    def source_ref_ids(self) -> list[str]:
        refs: list[str] = []
        for component in self.components:
            for ref in component.source_ref_ids:
                if ref not in refs:
                    refs.append(ref)
        return refs

    @property
    def has_approximation(self) -> bool:
        def walk(component) -> bool:
            return (component.is_approximation
                    or any(walk(s) for s in component.subcomponents))
        return any(walk(c) for c in self.components)

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "sthana_bala": self.sthana_bala.to_dict(),
            "dig_bala": self.dig_bala.to_dict(),
            "kala_bala": self.kala_bala.to_dict(),
            "chesta_bala": self.chesta_bala.to_dict(),
            "naisargika_bala": self.naisargika_bala.to_dict(),
            "drik_bala": self.drik_bala.to_dict(),
            "total_virupa": round(self.total_virupa, 4),
            "total_rupa": round(self.total_rupa, 5),
            "required_virupa": self.required_virupa,
            "required_rupa": round(self.required_rupa, 5),
            "ratio": round(self.ratio, 5),
            "meets_requirement": self.meets_requirement,
            "methodology_profile": self.methodology_profile,
            "validation_status": self.validation_status,
            "source_ref_ids": self.source_ref_ids,
            "contains_approximation": self.has_approximation,
            "notes": list(self.notes),
        }


@dataclass
class ShadbalaSet:
    """Shadbala for every graha in one chart."""

    results: dict[str, ShadbalaResult] = field(default_factory=dict)
    methodology_profile: str = "bphs_santhanam"
    warnings: list[str] = field(default_factory=list)

    @property
    def validation_status(self) -> str:
        return weakest_status(
            [c for r in self.results.values() for c in r.components])

    def ranked(self) -> list[ShadbalaResult]:
        """Strongest first, by ratio to requirement."""
        return sorted(self.results.values(), key=lambda r: -r.ratio)

    def to_dict(self) -> dict:
        return {
            "system": "shadbala",
            "methodology_profile": self.methodology_profile,
            "validation_status": self.validation_status,
            "units": {"virupa": "1/60 rupa", "rupa": "60 virupas"},
            "source": "BPHS ch.27 (Santhanam translation)",
            "planets": {name: result.to_dict()
                        for name, result in self.results.items()},
            "warnings": list(self.warnings),
        }
