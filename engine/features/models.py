"""
Feature models
--------------
Structured, purely factual descriptions of a chart. Everything in this module
is a CALCULATED ASTROLOGY FEATURE: it follows mechanically from the positions
and from a named, explicit convention. Nothing here decides whether a placement
is good, bad, strong or weak for the native — that is interpretation, and it
lives in the rule engine (engine/rules/) which consumes these objects.

The separation matters: the rule engine must never recompute a fact for itself,
because two implementations of "is Mars aspecting the 7th" will eventually
disagree. There is exactly one place each fact is derived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Relationships between bodies ─────────────────────────────────────────────

@dataclass(frozen=True)
class Aspect:
    """One graha drishti, from a graha onto a house (and whatever sits there)."""

    source: str                 # aspecting graha
    to_house: int               # 1-12, counted from the Lagna
    to_sign: int                # 0-11 sidereal sign index
    aspect_type: str            # "seventh" | "special_4th" | "special_5th" | ...
    distance: int               # houses counted inclusively, so 7 = opposition
    full: bool                  # full-strength drishti in the active profile
    strength: float             # 0.0-1.0 as declared by the profile
    targets: tuple[str, ...] = ()   # grahas occupying the aspected sign

    def describe(self) -> str:
        label = self.aspect_type.replace("_", " ")
        return f"{self.source} → house {self.to_house} ({label})"


@dataclass(frozen=True)
class Conjunction:
    """
    Two grahas in relation. Same-sign and orb proximity are stored separately
    and deliberately never merged: classical Yoga rules speak of grahas sharing
    a rashi, which is true at 0°01' and at 29°59' apart within that rashi, while
    orb-based closeness is a different claim entirely.
    """

    planet1: str
    planet2: str
    same_sign: bool
    sign: Optional[int]              # shared sign index, when same_sign
    house: Optional[int]             # shared house, when same_sign
    angular_separation: float        # 0-180 degrees, always meaningful
    within_orb: bool                 # separation <= orb_used
    orb_used: float

    def describe(self) -> str:
        where = f" in house {self.house}" if self.same_sign else ""
        return (f"{self.planet1}+{self.planet2}{where} "
                f"({self.angular_separation:.2f}° apart)")


@dataclass(frozen=True)
class Parivartana:
    """Mutual reception: two grahas each occupying the other's sign."""

    planet1: str
    planet2: str
    house1: int
    house2: int
    category: str       # "maha" | "dainya" | "khala" — BPHS classification

    def describe(self) -> str:
        return (f"{self.planet1} (house {self.house1}) ⇄ "
                f"{self.planet2} (house {self.house2}) [{self.category}]")


# ── Per-graha features ───────────────────────────────────────────────────────

@dataclass
class VargaPlacement:
    """Where a body falls in one divisional chart, and its standing there."""

    varga: str                  # "D9"
    sign: int                   # 0-11
    sign_name: str
    lord: str
    convention: str             # the named rule that produced it
    exalted: bool = False
    debilitated: bool = False
    own_sign: bool = False
    moolatrikona: bool = False

    def dignity_label(self) -> str:
        if self.exalted:
            return "exalted"
        if self.debilitated:
            return "debilitated"
        if self.moolatrikona:
            return "moolatrikona"
        if self.own_sign:
            return "own"
        return "-"


@dataclass
class PlanetFeatures:
    """Every calculated fact about one graha in one chart."""

    planet: str
    longitude: float
    sign: int
    sign_name: str
    degree_in_sign: float
    house: int
    sign_lord: str
    houses_owned: list[int]

    # Dignity — classical sign-based standing.
    dignity: str
    exalted: bool = False
    debilitated: bool = False
    moolatrikona: bool = False
    own_sign: bool = False
    friendly_sign: bool = False
    enemy_sign: bool = False
    neutral_sign: bool = False

    # Motion.
    speed: float = 0.0
    retrograde: bool = False
    stationary: bool = False
    speed_is_measured: bool = True

    # Relation to the Sun.
    combust: bool = False
    sun_separation: Optional[float] = None
    combustion_orb: Optional[float] = None

    # Divisional standing.
    vargottama: bool = False
    vargas: dict[str, VargaPlacement] = field(default_factory=dict)

    # Relationships.
    dispositor: Optional[str] = None
    conjunctions: list[Conjunction] = field(default_factory=list)
    aspects_given: list[Aspect] = field(default_factory=list)
    aspects_received: list[Aspect] = field(default_factory=list)

    # Nature.
    natural_benefic: bool = False
    natural_malefic: bool = False
    functional_nature: str = "neutral"
    functional_roles: list[str] = field(default_factory=list)

    # Nakshatra.
    nakshatra: str = ""
    nakshatra_lord: str = ""
    pada: int = 0

    # Numerical uncertainty. `uncertainty` is a PositionUncertainty; it is
    # typed loosely to keep engine.features free of a circular import.
    uncertainty: object = None
    theory: str = ""

    @property
    def boundary_warning(self) -> bool:
        """True when this placement is not resolved by the calculation."""
        return bool(self.uncertainty) and self.uncertainty.boundary_warning

    @property
    def boundary_types(self) -> list[str]:
        return list(self.uncertainty.boundary_types) if self.uncertainty else []

    @property
    def conjunct_planets(self) -> list[str]:
        return [c.planet2 if c.planet1 == self.planet else c.planet1
                for c in self.conjunctions if c.same_sign]

    @property
    def aspecting_planets(self) -> list[str]:
        return sorted({a.source for a in self.aspects_received})

    def varga_sign(self, varga: str) -> Optional[int]:
        placement = self.vargas.get(varga)
        return None if placement is None else placement.sign


# ── Per-house features ───────────────────────────────────────────────────────

@dataclass
class HouseFeatures:
    """Every calculated fact about one bhava."""

    house: int
    sign: int
    sign_name: str
    lord: str
    lord_house: int
    lord_sign: int
    occupants: list[str] = field(default_factory=list)
    aspects_received: list[Aspect] = field(default_factory=list)
    benefic_influences: list[str] = field(default_factory=list)
    malefic_influences: list[str] = field(default_factory=list)
    is_kendra: bool = False
    is_trikona: bool = False
    is_dusthana: bool = False
    is_upachaya: bool = False
    is_maraka: bool = False

    @property
    def aspecting_planets(self) -> list[str]:
        return sorted({a.source for a in self.aspects_received})

    @property
    def is_occupied(self) -> bool:
        return bool(self.occupants)


# ── Whole-chart features ─────────────────────────────────────────────────────

@dataclass
class ChartFeatures:
    """
    The complete factual description a rule engine runs against.

    `provenance` records which named conventions produced these facts, so a
    Yoga result can always be traced back to the tradition it assumed.
    """

    lagna_sign: int
    lagna_sign_name: str
    lagna_lord: str
    lagna_degree: float
    planets: dict[str, PlanetFeatures] = field(default_factory=dict)
    houses: dict[int, HouseFeatures] = field(default_factory=dict)
    house_lords: dict[int, str] = field(default_factory=dict)
    conjunctions: list[Conjunction] = field(default_factory=list)
    aspects: list[Aspect] = field(default_factory=list)
    parivartanas: list[Parivartana] = field(default_factory=list)
    dispositor_chains: dict[str, list[str]] = field(default_factory=dict)
    final_dispositors: dict[str, Optional[str]] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    uncertainty: dict = field(default_factory=dict)
    lagna_uncertainty: object = None

    # Detail objects kept off the per-graha record because they describe the
    # chart as a whole. Typed as Any to avoid a circular import back into the
    # modules that produce them.
    graha_yuddha: list = field(default_factory=list)
    functional_roles: dict = field(default_factory=dict)
    dispositor_details: dict = field(default_factory=dict)
    varga_lagnas: dict = field(default_factory=dict)
    varga_config: object = None

    # A ShadbalaSet, when one has been computed and attached (V1.5).
    #
    # Rules do not normally need strength: a yoga forms from placement, and
    # letting strength decide existence is the confusion the rule engine was
    # built to end. Two witnesses put a strength condition in the FORMATION
    # clause of the Pañca Mahāpuruṣa yogas, though — balibhiḥ at BPHS 75.1 and
    # baliṣṭhāḥ at Jātaka Pārijāta 59 — so the textual variants of those rules
    # need it, and it has to come from somewhere other than the rule engine
    # recomputing it. Typed loosely to keep engine.features independent of
    # engine.strength.
    shadbala: object = None

    def shadbala_ratio(self, planet: str) -> Optional[float]:
        """
        Shadbala total over the requirement, or None if not computed.

        None means NOT KNOWN, never zero. A caller that treats a missing
        Shadbala as weakness would silently turn "we did not measure" into
        "we measured and it failed".
        """
        if self.shadbala is None:
            return None
        result = getattr(self.shadbala, "results", {}).get(planet)
        return None if result is None else getattr(result, "ratio", None)

    # ── lookups the rule engine leans on ────────────────────────────────────

    def planet(self, name: str) -> Optional[PlanetFeatures]:
        return self.planets.get(name)

    def house_of(self, planet: str) -> Optional[int]:
        features = self.planets.get(planet)
        return None if features is None else features.house

    def lord_of(self, house: int) -> Optional[str]:
        return self.house_lords.get(((house - 1) % 12) + 1)

    def occupants_of(self, house: int) -> list[str]:
        bhava = self.houses.get(((house - 1) % 12) + 1)
        return [] if bhava is None else list(bhava.occupants)

    def houses_owned_by(self, planet: str) -> list[int]:
        features = self.planets.get(planet)
        return [] if features is None else list(features.houses_owned)

    def house_distance(self, from_house: int, to_house: int) -> int:
        """Inclusive count from one house to another, 1-12 (1 = same house)."""
        return ((to_house - from_house) % 12) + 1

    def planets_aspecting_house(self, house: int) -> list[str]:
        bhava = self.houses.get(((house - 1) % 12) + 1)
        return [] if bhava is None else bhava.aspecting_planets

    def aspects_between(self, source: str, target: str) -> list[Aspect]:
        """Aspects cast by `source` onto the sign `target` occupies."""
        target_features = self.planets.get(target)
        if target_features is None:
            return []
        return [a for a in self.aspects
                if a.source == source and a.to_sign == target_features.sign]
