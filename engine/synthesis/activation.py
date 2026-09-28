"""
Dasha and transit activation (V1.5 Parts 12, 13)
--------------------------------------------------
The two timing layers. Both answer the same shape of question — what does
this moving thing TOUCH in the natal chart — and neither answers what that
means.

THE ASYMMETRY THAT MATTERS

    A dasha lord activates what it OWNS and OCCUPIES: its lordships are
    natal facts, fixed at birth, and the dasha merely selects which of them
    is currently in view.

    A transit touches where it IS. It owns nothing in the natal chart by
    virtue of transiting, and it brings no promise with it.

    That is why `transit_activation` returns facts tagged with the houses and
    domains they touch, and nothing else: no weight, no direction, no
    confidence. Direction and weight are assigned in `engine.py`, and only
    for domains that already have natal evidence. A transit over an empty
    10th house produces a fact here and produces no career evidence there.
"""

from __future__ import annotations

import datetime
from typing import Optional

from .domains import Domain, domains_for_house, spec_for
from .eligibility import prediction_eligibility
from .models import (
    DashaActivation, EvidenceConfidence, PredictionEligibility,
    SynthesisProfile, TransitActivation,
)

DASHA_METHODOLOGY_ID = "vimshottari_activation_v15"
TRANSIT_METHODOLOGY_ID = "transit_activation_v15"


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


# ── Part 12: dasha activation ────────────────────────────────────────────────

def dasha_activation(planet: str, level: str, features, *,
                     yoga_results=None,
                     profile: SynthesisProfile = SynthesisProfile.STANDARD,
                     period_start: Optional[datetime.datetime] = None,
                     period_end: Optional[datetime.datetime] = None
                     ) -> DashaActivation:
    """
    Which natal factors one dasha lord activates.

    Facts only. Which houses the lord owns, which it occupies, what it is
    conjoined with and aspected by, its dispositor chain, its functional
    nature, and which eligible Yogas it participates in. What a Jupiter
    mahadasha "brings" is not computed here or anywhere in V1.5.
    """
    found = features.planet(planet)
    if found is None:
        return DashaActivation(
            planet=planet, level=level,
            confidence=EvidenceConfidence.UNRESOLVED)

    owned = tuple(sorted(features.houses_owned_by(planet)))
    occupied = found.house
    activated_houses = tuple(sorted(set(owned) | {occupied}))

    domains: set[str] = set()
    for house in activated_houses:
        for domain in domains_for_house(house):
            domains.add(domain.value)

    yogas: list[str] = []
    if yoga_results:
        for result in yoga_results:
            if not result.present or planet not in result.planets:
                continue
            if not profile.accepts(prediction_eligibility(result.id)):
                continue
            yogas.append(result.id)

    strength: dict = {}
    ratio = features.shadbala_ratio(planet)
    if ratio is not None:
        result = getattr(features.shadbala, "results", {}).get(planet)
        strength = {
            "shadbala_ratio": round(ratio, 3),
            "total_virupa": round(getattr(result, "total_virupa", 0.0), 2),
            "required_virupa": getattr(result, "required_virupa", None),
            "meets_requirement": ratio >= 1.0,
            "source_ref_ids": ["BPHS_27_SHADBALA"],
            "note": (
                "A measured quantity from a located witness. Whether a "
                "strong dasha lord gives good results is an interpretation "
                "and is not made here."),
        }

    # The dispositor chain is a natal fact and is included because a dasha
    # lord's results are traditionally read through where its dispositor
    # sits. Reported, not weighted.
    chain = tuple(features.dispositor_chains.get(planet, ()))

    # Confidence here is about the ACTIVATION, not about any outcome: a
    # Vimshottari stack computed with exact Fraction arithmetic from a Moon
    # longitude is a firm fact, so MEDIUM is the floor and the Moon's own
    # boundary state is what can lower it.
    moon = features.planet("Chandra")
    confidence = EvidenceConfidence.HIGH
    if moon is not None and moon.boundary_warning:
        confidence = EvidenceConfidence.LOW

    return DashaActivation(
        planet=planet, level=level,
        activated_houses=activated_houses,
        activated_domains=tuple(sorted(domains)),
        yogas_activated=tuple(yogas),
        occupied_house=occupied,
        dispositor_chain=chain,
        functional_nature=found.functional_nature,
        strength_evidence=strength,
        confidence=confidence,
        period_start=period_start, period_end=period_end,
    )


def dasha_stack_activations(dasha, moment: datetime.datetime, features, *,
                            yoga_results=None,
                            profile: SynthesisProfile
                            = SynthesisProfile.STANDARD
                            ) -> list[DashaActivation]:
    """Activation for every level of the running dasha stack."""
    if dasha is None:
        return []
    out = []
    for level in ("mahadasha", "antardasha", "pratyantardasha"):
        period = dasha.get_period_at(moment, level=level)
        if period is None:
            continue
        out.append(dasha_activation(
            period.lord, level, features,
            yoga_results=yoga_results, profile=profile,
            period_start=period.start, period_end=period.end))
    return out


# ── Part 13: transit activation ──────────────────────────────────────────────

def transit_activation(transit_snapshot, features, *,
                       dasha_lords: tuple = (),
                       natal_chart=None) -> list[TransitActivation]:
    """
    Factual transit-to-natal relationships, tagged with what they touch.

    Part 13 asks for the classical sign/house relationship and the exact
    degree proximity to be kept apart, and they are: `same_sign` and
    `angular_separation` come straight from the V1.4 relationship objects and
    neither is derived from the other.
    """
    if transit_snapshot is None:
        return []

    out: list[TransitActivation] = []
    lords = set(dasha_lords)

    for name, position in transit_snapshot.positions.items():
        house = position.house_from_natal_lagna
        if house:
            domains = tuple(sorted(d.value for d in domains_for_house(house)))
            out.append(TransitActivation(
                transit_planet=name, relation="over_natal_house",
                natal_target=f"house_{house}", target_kind="house",
                house_touched=house, domains_touched=domains,
                is_dasha_lord=name in lords,
                retrograde=position.retrograde,
                explanation=(
                    f"Transiting {name} occupies the {_ordinal(house)} from "
                    f"the natal Lagna"
                    + (" (retrograde)" if position.retrograde else "") + ".")))

        from_moon = position.house_from_natal_moon
        if from_moon:
            out.append(TransitActivation(
                transit_planet=name, relation="over_house_from_natal_moon",
                natal_target=f"house_{from_moon}_from_moon",
                target_kind="house_from_moon",
                house_touched=None, domains_touched=(),
                is_dasha_lord=name in lords,
                retrograde=position.retrograde,
                explanation=(
                    f"Transiting {name} is in the {_ordinal(from_moon)} from "
                    f"the natal Chandra.")))

    for relationship in transit_snapshot.relationships:
        natal = features.planet(relationship.natal_target)
        house = natal.house if natal is not None else None
        if relationship.target_kind == "lagna":
            house = 1

        domains = tuple(sorted(d.value for d in domains_for_house(house))) \
            if house else ()

        if relationship.same_sign:
            relation = "conjunct_natal_point"
        elif relationship.graha_drishti:
            relation = "graha_drishti_to_natal_point"
        else:
            continue

        # A transiting graha that also rules a natal house carries that
        # lordship with it. This is the one place a transit legitimately
        # reaches houses it is not standing in.
        ruled = tuple(sorted(features.houses_owned_by(
            relationship.transit_planet)))
        for owned in ruled:
            for domain in domains_for_house(owned):
                domains = tuple(sorted(set(domains) | {domain.value}))

        out.append(TransitActivation(
            transit_planet=relationship.transit_planet,
            relation=relation,
            natal_target=relationship.natal_target,
            target_kind=relationship.target_kind,
            house_touched=house, domains_touched=domains,
            same_sign=relationship.same_sign,
            angular_separation=relationship.angular_separation,
            within_orb=relationship.within_orb,
            graha_drishti=relationship.graha_drishti,
            drishti_type=relationship.drishti_type,
            is_dasha_lord=relationship.transit_planet in lords,
            explanation=(
                f"Transiting {relationship.transit_planet} "
                + ("shares a rashi with" if relationship.same_sign
                   else f"casts {relationship.drishti_type} drishti on")
                + f" natal {relationship.natal_target} "
                  f"({relationship.angular_separation:.2f}° apart).")))

    return out


def activations_for_domain(activations, domain) -> list[TransitActivation]:
    """Transit activations touching one domain."""
    name = spec_for(domain).domain.value
    return [a for a in activations if name in a.domains_touched]


def dasha_activations_for_domain(activations, domain) -> list[DashaActivation]:
    name = spec_for(domain).domain.value
    return [a for a in activations if name in a.activated_domains]
