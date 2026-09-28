"""
Strength modifiers
------------------
Adjustments applied to a Yoga AFTER its existence has been established. They
never contribute to whether a Yoga forms.

The numbers are engine conventions for ranking results on one chart against
each other. No classical text scores a Yoga numerically, so these weights are
presentation, not doctrine — which is why each one carries its reason into the
report and why the report prints the band ("strong"/"moderate"/"weakened")
next to the participating factors rather than on its own.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

from ..features.models import ChartFeatures
from .conditions import _ordinal
from .engine import Modifier


def _planets(features: ChartFeatures, names: Sequence[str]):
    return [features.planet(n) for n in names if features.planet(n) is not None]


def combustion_penalty(planets: Sequence[str]) -> Callable:
    """A combust participant cannot deliver its results freely."""
    def test(features: ChartFeatures) -> Optional[Modifier]:
        burnt = [p.planet for p in _planets(features, planets) if p.combust]
        if not burnt:
            return None
        return Modifier(
            "combustion", -0.20 * len(burnt),
            ", ".join(burnt) + " combust — results obstructed")
    return test


def debilitation_penalty(planets: Sequence[str]) -> Callable:
    def test(features: ChartFeatures) -> Optional[Modifier]:
        weak = [p.planet for p in _planets(features, planets) if p.debilitated]
        if not weak:
            return None
        return Modifier("debilitation", -0.25 * len(weak),
                        ", ".join(weak) + " debilitated")
    return test


def exaltation_bonus(planets: Sequence[str]) -> Callable:
    def test(features: ChartFeatures) -> Optional[Modifier]:
        strong = [p.planet for p in _planets(features, planets)
                  if p.exalted or p.moolatrikona]
        if not strong:
            return None
        return Modifier("dignity", 0.20 * len(strong),
                        ", ".join(strong) + " exalted or in moolatrikona")
    return test


def own_sign_bonus(planets: Sequence[str]) -> Callable:
    def test(features: ChartFeatures) -> Optional[Modifier]:
        strong = [p.planet for p in _planets(features, planets)
                  if p.own_sign and not p.moolatrikona]
        if not strong:
            return None
        return Modifier("own rashi", 0.12 * len(strong),
                        ", ".join(strong) + " in own rashi")
    return test


def vargottama_bonus(planets: Sequence[str]) -> Callable:
    def test(features: ChartFeatures) -> Optional[Modifier]:
        strong = [p.planet for p in _planets(features, planets) if p.vargottama]
        if not strong:
            return None
        return Modifier("vargottama", 0.15 * len(strong),
                        ", ".join(strong) + " vargottama (same rashi in D1 and D9)")
    return test


def navamsha_dignity(planets: Sequence[str]) -> Callable:
    """D9 standing, the usual second opinion on a graha's real strength."""
    def test(features: ChartFeatures) -> Optional[Modifier]:
        good, bad = [], []
        for planet in _planets(features, planets):
            d9 = planet.vargas.get("D9")
            if d9 is None:
                continue
            if d9.exalted or d9.own_sign:
                good.append(f"{planet.planet} {d9.dignity_label()} in D9")
            elif d9.debilitated:
                bad.append(f"{planet.planet} debilitated in D9")
        if not good and not bad:
            return None
        delta = 0.12 * len(good) - 0.18 * len(bad)
        return Modifier("navamsha", delta, "; ".join(good + bad))
    return test


def dusthana_penalty(planets: Sequence[str]) -> Callable:
    def test(features: ChartFeatures) -> Optional[Modifier]:
        placed = [f"{p.planet} in the {_ordinal(p.house)}"
                  for p in _planets(features, planets) if p.house in (6, 8, 12)]
        if not placed:
            return None
        return Modifier("dusthana", -0.15 * len(placed),
                        ", ".join(placed) + " (dusthana placement)")
    return test


def malefic_association_penalty(planets: Sequence[str]) -> Callable:
    """Natural malefics joining the participants dilute the result."""
    def test(features: ChartFeatures) -> Optional[Modifier]:
        found: list[str] = []
        for planet in _planets(features, planets):
            for companion in planet.conjunct_planets:
                other = features.planet(companion)
                if other is not None and other.natural_malefic \
                        and companion not in planets:
                    found.append(f"{planet.planet} with {companion}")
        if not found:
            return None
        return Modifier("malefic company", -0.10 * len(found), ", ".join(found))
    return test


def benefic_aspect_bonus(planets: Sequence[str]) -> Callable:
    def test(features: ChartFeatures) -> Optional[Modifier]:
        found: list[str] = []
        for planet in _planets(features, planets):
            for source in planet.aspecting_planets:
                other = features.planet(source)
                if other is not None and other.natural_benefic \
                        and source not in planets:
                    found.append(f"{source} aspects {planet.planet}")
        if not found:
            return None
        return Modifier("benefic drishti", 0.08 * len(found), ", ".join(found))
    return test


def retrograde_note(planets: Sequence[str]) -> Callable:
    """
    Retrogression is recorded as a factor but carries no weight, because
    authorities split on whether a retrograde graha is strengthened (cheshta
    bala) or frustrated. Taking a side silently would be the wrong call.
    """
    def test(features: ChartFeatures) -> Optional[Modifier]:
        retro = [p.planet for p in _planets(features, planets) if p.retrograde]
        if not retro:
            return None
        return Modifier(
            "retrograde", 0.0,
            ", ".join(retro) + " retrograde — authorities differ on the effect, "
            "so no weight is applied")
    return test


def standard_modifiers(planets: Sequence[str]) -> list[Callable]:
    """The usual battery, applied to the grahas forming a Yoga."""
    return [
        exaltation_bonus(planets),
        own_sign_bonus(planets),
        vargottama_bonus(planets),
        navamsha_dignity(planets),
        debilitation_penalty(planets),
        combustion_penalty(planets),
        dusthana_penalty(planets),
        malefic_association_penalty(planets),
        benefic_aspect_bonus(planets),
        retrograde_note(planets),
    ]


def lords_modifiers(houses: Sequence[int]) -> list[Callable]:
    """
    The same battery, but resolved against whichever grahas own the named
    bhavas in this chart. Used by the Raja and Dhana rules, whose participants
    are not known until the Lagna is.
    """
    def resolve(features: ChartFeatures) -> list[str]:
        return [lord for lord in (features.lord_of(h) for h in houses) if lord]

    def make(builder: Callable) -> Callable:
        def test(features: ChartFeatures) -> Optional[Modifier]:
            return builder(resolve(features))(features)
        return test

    return [make(b) for b in (
        exaltation_bonus, own_sign_bonus, vargottama_bonus, navamsha_dignity,
        debilitation_penalty, combustion_penalty, dusthana_penalty,
        malefic_association_penalty, benefic_aspect_bonus, retrograde_note,
    )]
