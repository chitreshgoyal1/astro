"""
Rule conditions
---------------
Small, declarative predicates evaluated against a ChartFeatures. Each one
answers a single question and explains itself in words, so a Yoga result can
say exactly which clause matched and which did not.

Conditions never compute astrology. They read features that engine/features
already derived. If a condition needs a fact that does not exist yet, the fact
belongs in the feature engine, not here — that rule is what keeps the two
layers from drifting apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from ..features.lordships import KENDRA_HOUSES, TRIKONA_HOUSES
from ..features.models import ChartFeatures


@dataclass
class ConditionResult:
    """Outcome of one clause: met or not, and why."""

    met: bool
    description: str
    planets: list[str] = field(default_factory=list)
    houses: list[int] = field(default_factory=list)
    detail: str = ""

    def __bool__(self) -> bool:
        return self.met


@dataclass
class Condition:
    """
    A named clause. `test` receives the chart features and returns a
    ConditionResult. `label` is what appears in the report when the clause is
    listed as met or failed.
    """

    label: str
    test: Callable[[ChartFeatures], ConditionResult]

    def evaluate(self, features: ChartFeatures) -> ConditionResult:
        result = self.test(features)
        if not result.description:
            result.description = self.label
        return result


# ── helpers ──────────────────────────────────────────────────────────────────

def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _house_list(houses: Sequence[int]) -> str:
    return ", ".join(_ordinal(h) for h in houses)


def _relationship_between(features: ChartFeatures, a: str, b: str,
                          modes: Sequence[str]) -> Optional[tuple[str, str]]:
    """
    Sambandha between two grahas, restricted to the requested modes.
    Returns (mode, explanation) for the first mode that holds, else None.
    """
    if a == b or a not in features.planets or b not in features.planets:
        return None

    if "conjunction" in modes:
        for conj in features.conjunctions:
            if conj.same_sign and {conj.planet1, conj.planet2} == {a, b}:
                return ("conjunction",
                        f"{a} and {b} share {features.planets[a].sign_name} "
                        f"(house {conj.house}), {conj.angular_separation:.2f}° apart")

    if "mutual_aspect" in modes:
        a_to_b = features.aspects_between(a, b)
        b_to_a = features.aspects_between(b, a)
        if a_to_b and b_to_a:
            return ("mutual_aspect",
                    f"{a} aspects {b} ({a_to_b[0].aspect_type}) and {b} "
                    f"aspects {a} ({b_to_a[0].aspect_type})")

    if "aspect" in modes:
        a_to_b = features.aspects_between(a, b)
        if a_to_b:
            return ("aspect", f"{a} aspects {b} ({a_to_b[0].aspect_type})")
        b_to_a = features.aspects_between(b, a)
        if b_to_a:
            return ("aspect", f"{b} aspects {a} ({b_to_a[0].aspect_type})")

    if "exchange" in modes:
        for swap in features.parivartanas:
            if {swap.planet1, swap.planet2} == {a, b}:
                return ("exchange",
                        f"{a} and {b} exchange rashis ({swap.category} yoga)")

    return None


# ── placement ────────────────────────────────────────────────────────────────

def planet_in_houses(planet: str, houses: Sequence[int],
                     label: Optional[str] = None) -> Condition:
    houses = tuple(houses)

    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None:
            return ConditionResult(False, f"{planet} is not in the chart")
        met = found.house in houses
        return ConditionResult(
            met,
            f"{planet} is in the {_ordinal(found.house)} "
            f"({'a' if met else 'not a'} required house: {_house_list(houses)})",
            planets=[planet], houses=[found.house])

    return Condition(label or f"{planet} in the {_house_list(houses)}", test)


def planet_in_kendra_from_planet(planet: str, reference: str) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        a, b = features.planet(planet), features.planet(reference)
        if a is None or b is None:
            return ConditionResult(False, f"{planet} or {reference} is absent")
        distance = features.house_distance(b.house, a.house)
        met = distance in KENDRA_HOUSES
        return ConditionResult(
            met,
            f"{planet} is the {_ordinal(distance)} from {reference} "
            f"({'a kendra' if met else 'not a kendra'})",
            planets=[planet, reference], houses=[a.house, b.house])

    return Condition(f"{planet} in a kendra from {reference}", test)


def planet_dignity(planet: str, kinds: Sequence[str],
                   label: Optional[str] = None) -> Condition:
    """`kinds` drawn from exalted, own_sign, moolatrikona, debilitated."""
    kinds = tuple(kinds)

    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None:
            return ConditionResult(False, f"{planet} is not in the chart")
        held = [k for k in kinds if getattr(found, k, False)]
        return ConditionResult(
            bool(held),
            f"{planet} in {found.sign_name} is "
            + (", ".join(held).replace("_", " ") if held
               else f"none of: {', '.join(k.replace('_', ' ') for k in kinds)}"),
            planets=[planet], houses=[found.house])

    return Condition(
        label or f"{planet} is {' or '.join(k.replace('_', ' ') for k in kinds)}",
        test)


def planet_not_combust(planet: str) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None:
            return ConditionResult(False, f"{planet} is not in the chart")
        if found.sun_separation is None:
            return ConditionResult(True, f"{planet} has no separation recorded")
        return ConditionResult(
            not found.combust,
            f"{planet} is {found.sun_separation:.2f}° from the Sun "
            f"({'combust' if found.combust else 'not combust'}"
            + (f", arc {found.combustion_orb:g}°" if found.combustion_orb else "")
            + ")",
            planets=[planet])

    return Condition(f"{planet} is not combust", test)


def planet_retrograde(planet: str, want: bool = True) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None:
            return ConditionResult(False, f"{planet} is not in the chart")
        return ConditionResult(
            found.retrograde == want,
            f"{planet} is {'retrograde' if found.retrograde else 'direct'}",
            planets=[planet])

    return Condition(f"{planet} is {'retrograde' if want else 'direct'}", test)


# ── lordship ─────────────────────────────────────────────────────────────────

def lord_of_house_in_houses(house: int, target_houses: Sequence[int],
                            label: Optional[str] = None) -> Condition:
    targets = tuple(target_houses)

    def test(features: ChartFeatures) -> ConditionResult:
        lord = features.lord_of(house)
        found = features.planet(lord) if lord else None
        if found is None:
            return ConditionResult(
                False, f"the {_ordinal(house)} lord is not in the chart")
        met = found.house in targets
        return ConditionResult(
            met,
            f"the {_ordinal(house)} lord {lord} is in the {_ordinal(found.house)} "
            f"({'a' if met else 'not a'} required house: {_house_list(targets)})",
            planets=[lord], houses=[house, found.house])

    return Condition(
        label or f"lord of the {_ordinal(house)} in the {_house_list(targets)}",
        test)


def lords_related(house_a: int, house_b: int,
                  modes: Sequence[str] = ("conjunction", "mutual_aspect", "exchange"),
                  label: Optional[str] = None) -> Condition:
    """Sambandha between the lords of two bhavas, by the named modes only."""
    modes = tuple(modes)

    def test(features: ChartFeatures) -> ConditionResult:
        lord_a = features.lord_of(house_a)
        lord_b = features.lord_of(house_b)
        if not lord_a or not lord_b:
            return ConditionResult(False, "a required house lord is absent")
        if lord_a == lord_b:
            return ConditionResult(
                False,
                f"the {_ordinal(house_a)} and {_ordinal(house_b)} share one lord "
                f"({lord_a}), so there are not two grahas to relate",
                planets=[lord_a], houses=[house_a, house_b])
        relation = _relationship_between(features, lord_a, lord_b, modes)
        if relation is None:
            return ConditionResult(
                False,
                f"no {' / '.join(modes)} between the {_ordinal(house_a)} lord "
                f"{lord_a} and the {_ordinal(house_b)} lord {lord_b}",
                planets=[lord_a, lord_b], houses=[house_a, house_b])
        mode, why = relation
        return ConditionResult(
            True, why, planets=[lord_a, lord_b],
            houses=[house_a, house_b], detail=mode)

    return Condition(
        label or (f"lords of the {_ordinal(house_a)} and {_ordinal(house_b)} "
                  f"related by {' / '.join(modes)}"),
        test)


def planets_conjunct(a: str, b: str) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        for conj in features.conjunctions:
            if conj.same_sign and {conj.planet1, conj.planet2} == {a, b}:
                return ConditionResult(
                    True,
                    f"{a} and {b} share one rashi in house {conj.house} "
                    f"({conj.angular_separation:.2f}° apart)",
                    planets=[a, b], houses=[conj.house or 0])
        return ConditionResult(
            False, f"{a} and {b} do not share a rashi", planets=[a, b])

    return Condition(f"{a} and {b} conjunct in one rashi", test)


def parivartana_between(house_a: int, house_b: int) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        for swap in features.parivartanas:
            if {swap.house1, swap.house2} == {house_a, house_b}:
                return ConditionResult(
                    True, swap.describe(),
                    planets=[swap.planet1, swap.planet2],
                    houses=[house_a, house_b])
        return ConditionResult(
            False,
            f"no exchange between the {_ordinal(house_a)} and "
            f"{_ordinal(house_b)} lords",
            houses=[house_a, house_b])

    return Condition(
        f"exchange between the {_ordinal(house_a)} and {_ordinal(house_b)} lords",
        test)


# ── composite / bespoke ──────────────────────────────────────────────────────

def custom(label: str,
           test: Callable[[ChartFeatures], ConditionResult]) -> Condition:
    """Escape hatch for a clause with no reusable shape."""
    return Condition(label, test)


def none_of(conditions: Sequence[Condition], label: str) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        for condition in conditions:
            result = condition.evaluate(features)
            if result.met:
                return ConditionResult(
                    False, f"fails because {result.description}",
                    planets=result.planets, houses=result.houses)
        return ConditionResult(True, label)

    return Condition(label, test)


def any_of(conditions: Sequence[Condition], label: str) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        reasons = []
        for condition in conditions:
            result = condition.evaluate(features)
            if result.met:
                return ConditionResult(True, result.description,
                                       planets=result.planets,
                                       houses=result.houses,
                                       detail=result.detail)
            reasons.append(result.description)
        return ConditionResult(False, "none held: " + "; ".join(reasons))

    return Condition(label, test)
