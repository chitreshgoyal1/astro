
"""
Ashtakavarga models and bindu tables (V1.4 Parts 10, 11)
----------------------------------------------------------
The bindu (rekha) tables: for each graha's own varga, which houses counted
from each of eight reference points receive a benefic point.

SOURCE AND HOW FAR IT WAS CHECKED

    BPHS ch. 66, R. Santhanam translation (witness BPHS_66_ASHTAKAVARGA).

    The SUN's table at verses 43-45 was read directly from the witness and
    transposed into the form below. It matches exactly. As a check on the
    transposition, the witness lists contributions house by house —

        1st: Saturn, Mars, Sun          7th: Sun, Mars, Saturn, Venus
        2nd: Saturn, Mars, Sun          8th: Saturn, Mars, Sun
        3rd: Mercury, Moon, Lagna       9th: Sun, Mars, Saturn, Mercury, Jupiter
        4th: Lagna, Sun, Saturn, Mars  10th: Lagna, Sun, Saturn, Mars, Mercury, Moon
        5th: Jupiter, Mercury          11th: all seven and the Lagna
        6th: Lagna, Venus, Mercury,    12th: Lagna, Venus, Mercury
             Jupiter, Moon

    — and inverting that gives precisely SUN_BINDUS below.

    The remaining seven tables are present in the same chapter but the OCR of
    those verses is damaged in places. They are implemented from the standard
    tables and their per-verse verification is INCOMPLETE. That is recorded in
    the review queue rather than glossed: the Sun is verified, the rest are
    located but unchecked.

NO INTERPRETATION

    Part 10 is explicit. A bindu count is a count. This package attaches no
    claim that many bindus are fortunate or few are not, and the report says
    the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# The eight reference points ("ashta-varga") from which houses are counted.
CONTRIBUTORS = ("Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra",
                "Shani", "Lagna")

# The seven grahas that have an Ashtakavarga of their own. The Lagna
# contributes to every table but does not have one.
AV_GRAHAS = ("Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani")

WITNESS = ("BPHS_66_ASHTAKAVARGA",)

# ── The tables ───────────────────────────────────────────────────────────────
# Read as: in <graha>'s ashtakavarga, counting from <contributor>, these
# house numbers receive a bindu.

SUN_BINDUS = {
    "Surya":   (1, 2, 4, 7, 8, 9, 10, 11),
    "Chandra": (3, 6, 10, 11),
    "Mangal":  (1, 2, 4, 7, 8, 9, 10, 11),
    "Budha":   (3, 5, 6, 9, 10, 11, 12),
    "Guru":    (5, 6, 9, 11),
    "Shukra":  (6, 7, 12),
    "Shani":   (1, 2, 4, 7, 8, 9, 10, 11),
    "Lagna":   (3, 4, 6, 10, 11, 12),
}

MOON_BINDUS = {
    "Surya":   (3, 6, 7, 8, 10, 11),
    "Chandra": (1, 3, 6, 7, 10, 11),
    "Mangal":  (2, 3, 5, 6, 9, 10, 11),
    "Budha":   (1, 3, 4, 5, 7, 8, 10, 11),
    "Guru":    (1, 4, 7, 8, 10, 11, 12),
    "Shukra":  (3, 4, 5, 7, 9, 10, 11),
    "Shani":   (3, 5, 6, 11),
    "Lagna":   (3, 6, 10, 11),
}

MARS_BINDUS = {
    "Surya":   (3, 5, 6, 10, 11),
    "Chandra": (3, 6, 11),
    "Mangal":  (1, 2, 4, 7, 8, 10, 11),
    "Budha":   (3, 5, 6, 11),
    "Guru":    (6, 10, 11, 12),
    "Shukra":  (6, 8, 11, 12),
    "Shani":   (1, 4, 7, 8, 9, 10, 11),
    "Lagna":   (1, 3, 6, 10, 11),
}

MERCURY_BINDUS = {
    "Surya":   (5, 6, 9, 11, 12),
    "Chandra": (2, 4, 6, 8, 10, 11),
    "Mangal":  (1, 2, 4, 7, 8, 9, 10, 11),
    "Budha":   (1, 3, 5, 6, 9, 10, 11, 12),
    "Guru":    (6, 8, 11, 12),
    "Shukra":  (1, 2, 3, 4, 5, 8, 9, 11),
    "Shani":   (1, 2, 4, 7, 8, 9, 10, 11),
    "Lagna":   (1, 2, 4, 6, 8, 10, 11),
}

JUPITER_BINDUS = {
    "Surya":   (1, 2, 3, 4, 7, 8, 9, 10, 11),
    "Chandra": (2, 5, 7, 9, 11),
    "Mangal":  (1, 2, 4, 7, 8, 10, 11),
    "Budha":   (1, 2, 4, 5, 6, 9, 10, 11),
    "Guru":    (1, 2, 3, 4, 7, 8, 10, 11),
    "Shukra":  (2, 5, 6, 9, 10, 11),
    "Shani":   (3, 5, 6, 12),
    "Lagna":   (1, 2, 4, 5, 6, 7, 9, 10, 11),
}

VENUS_BINDUS = {
    "Surya":   (8, 11, 12),
    "Chandra": (1, 2, 3, 4, 5, 8, 9, 11, 12),
    "Mangal":  (3, 5, 6, 9, 11, 12),
    "Budha":   (3, 5, 6, 9, 11),
    "Guru":    (5, 8, 9, 10, 11),
    "Shukra":  (1, 2, 3, 4, 5, 8, 9, 10, 11),
    "Shani":   (3, 4, 5, 8, 9, 10, 11),
    "Lagna":   (1, 2, 3, 4, 5, 8, 9, 11),
}

SATURN_BINDUS = {
    "Surya":   (1, 2, 4, 7, 8, 10, 11),
    "Chandra": (3, 6, 11),
    "Mangal":  (3, 5, 6, 10, 11, 12),
    "Budha":   (6, 8, 9, 10, 11, 12),
    "Guru":    (5, 6, 11, 12),
    "Shukra":  (6, 11, 12),
    "Shani":   (3, 5, 6, 11),
    "Lagna":   (1, 3, 4, 6, 10, 11),
}

BINDU_TABLES: dict[str, dict[str, tuple[int, ...]]] = {
    "Surya": SUN_BINDUS,
    "Chandra": MOON_BINDUS,
    "Mangal": MARS_BINDUS,
    "Budha": MERCURY_BINDUS,
    "Guru": JUPITER_BINDUS,
    "Shukra": VENUS_BINDUS,
    "Shani": SATURN_BINDUS,
}

# Classical totals per graha's own varga. These are a genuine invariant: the
# table above must sum to exactly these, and a test asserts it. A mistyped
# table is caught here rather than silently producing wrong bindus.
CLASSICAL_TOTALS = {
    "Surya": 48, "Chandra": 49, "Mangal": 39, "Budha": 54,
    "Guru": 56, "Shukra": 52, "Shani": 39,
}

# Sum of all seven, the Sarvashtakavarga grand total.
SARVA_TOTAL = 337

# Which tables have been checked verse by verse against the witness.
VERIFIED_AGAINST_WITNESS = ("Surya",)


@dataclass
class BhinnaAshtakavarga:
    """One graha's own ashtakavarga: bindus per sign."""

    planet: str
    bindus_by_sign: dict[int, int] = field(default_factory=dict)
    contributions: dict[str, tuple[int, ...]] = field(default_factory=dict)
    source_ref_ids: tuple[str, ...] = WITNESS
    validation_status: str = "TEXT_LOCATED"

    @property
    def total(self) -> int:
        return sum(self.bindus_by_sign.values())

    def bindus_in_sign(self, sign: int) -> int:
        return self.bindus_by_sign.get(sign % 12, 0)

    def bindus_in_house(self, house: int, lagna_sign: int) -> int:
        return self.bindus_in_sign((lagna_sign + house - 1) % 12)

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "bindus_by_sign": {str(s): b
                               for s, b in sorted(self.bindus_by_sign.items())},
            "total": self.total,
            "classical_total": CLASSICAL_TOTALS.get(self.planet),
            "contributing_signs": {k: list(v)
                                   for k, v in self.contributions.items()},
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status,
            "verified_against_witness": (
                self.planet in VERIFIED_AGAINST_WITNESS),
        }


@dataclass
class Sarvashtakavarga:
    """The seven bhinna charts summed sign by sign."""

    bindus_by_sign: dict[int, int] = field(default_factory=dict)
    source_ref_ids: tuple[str, ...] = WITNESS
    validation_status: str = "TEXT_LOCATED"

    @property
    def total(self) -> int:
        return sum(self.bindus_by_sign.values())

    def bindus_in_sign(self, sign: int) -> int:
        return self.bindus_by_sign.get(sign % 12, 0)

    def bindus_in_house(self, house: int, lagna_sign: int) -> int:
        return self.bindus_in_sign((lagna_sign + house - 1) % 12)

    def to_dict(self) -> dict:
        return {
            "bindus_by_sign": {str(s): b
                               for s, b in sorted(self.bindus_by_sign.items())},
            "total": self.total,
            "classical_total": SARVA_TOTAL,
            "source_ref_ids": list(self.source_ref_ids),
            "validation_status": self.validation_status,
        }


@dataclass
class AshtakavargaSet:
    """Every ashtakavarga for one chart."""

    bhinna: dict[str, BhinnaAshtakavarga] = field(default_factory=dict)
    sarva: Optional[Sarvashtakavarga] = None
    lagna_sign: int = 0
    methodology_profile: str = "bphs_parashari"
    reductions: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "system": "ashtakavarga",
            "methodology_profile": self.methodology_profile,
            "source": "BPHS ch.66 (R. Santhanam translation)",
            "validation_status": "TEXT_LOCATED",
            "verification_note": (
                "The Sun's table was checked verse by verse against the "
                "witness and matches. The other six are located in the same "
                "chapter but their OCR is damaged, so per-graha verification "
                "is incomplete."),
            "lagna_sign": self.lagna_sign,
            "bhinna": {name: chart.to_dict()
                       for name, chart in self.bhinna.items()},
            "sarva": self.sarva.to_dict() if self.sarva else None,
            "reductions": self.reductions,
            "warnings": list(self.warnings),
        }
