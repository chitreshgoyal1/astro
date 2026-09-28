"""
Feature assembly
----------------
Turns a JyotishChart into a ChartFeatures: one pass that derives every fact the
rule engine is allowed to use, from the positions and the active conventions.

This is the only place these facts are computed. The rule engine reads the
result and never recalculates — that constraint is what stops two
implementations of "is Mangal aspecting the 7th" from drifting apart.
"""

from __future__ import annotations

from typing import Optional

from ..ephemeris import theory_used
from ..planets import (
    JyotishChart, PLANET_NAMES, RASHI_NAMES,
)
from ..uncertainty import (
    assess_position, envelope_for, summarise as summarise_uncertainty,
    varga_division_spans,
)
from ..vargas import VARGA_ORDER, VARGA_SPECS, VargaConfig
from .aspects import AspectProfile, DEFAULT_ASPECT_PROFILE, compute_aspects
from .conjunctions import DEFAULT_ORB_DEG, compute_conjunctions, compute_graha_yuddha
from .dignity import dignity_flags, natural_nature
from .dispositors import (
    all_dispositor_chains, dispositor_of, final_dispositors, find_parivartanas,
)
from .functional_nature import functional_roles
from .lordships import (
    classify_house, house_lords, house_of_sign, houses_owned, lord_of_sign,
    sign_of_house,
)
from .models import ChartFeatures, HouseFeatures, PlanetFeatures
from .varga_features import (
    compute_varga_features, is_vargottama, varga_lagna,
)


def _moon_phase_fraction(chart: JyotishChart) -> Optional[float]:
    """
    Illuminated fraction of the Moon, 0 at new and 1 at full. Used only to
    resolve Chandra's conditional natural benefic/malefic character.
    """
    sun = chart.planets.get("Surya")
    moon = chart.planets.get("Chandra")
    if sun is None or moon is None:
        return None
    elongation = (moon.longitude - sun.longitude) % 360.0
    # Distance from new moon, normalised so full moon scores 1.0.
    return 1.0 - abs(180.0 - elongation) / 180.0


def build_chart_features(chart: JyotishChart,
                         varga_config: Optional[VargaConfig] = None,
                         aspect_profile: Optional[AspectProfile] = None,
                         conjunction_orb: float = DEFAULT_ORB_DEG
                         ) -> ChartFeatures:
    """Derive the complete factual description of a chart."""
    config = varga_config or VargaConfig()
    profile = aspect_profile or DEFAULT_ASPECT_PROFILE
    lagna = chart.lagna
    lagna_sign = lagna.rashi_index

    present = [p for p in PLANET_NAMES if p in chart.planets]
    planet_signs = {p: chart.planets[p].rashi_index for p in present}
    planet_longitudes = {p: chart.planets[p].longitude for p in present}
    planet_latitudes = {p: chart.planets[p].latitude for p in present}
    planet_houses = {p: house_of_sign(lagna_sign, planet_signs[p]) for p in present}

    lords = house_lords(lagna_sign)
    owned = houses_owned(lagna_sign)
    roles = functional_roles(lagna_sign)

    aspects = compute_aspects(planet_houses, planet_signs, lagna_sign, profile)
    conjunctions = compute_conjunctions(planet_longitudes, planet_signs,
                                        planet_houses, conjunction_orb)
    yuddha = compute_graha_yuddha(planet_longitudes, planet_latitudes)
    parivartanas = find_parivartanas(planet_signs, planet_houses)
    chains = all_dispositor_chains(planet_signs)
    moon_phase = _moon_phase_fraction(chart)

    # Numerical uncertainty: is each classification actually resolved?
    varga_spans = varga_division_spans(
        {key: VARGA_SPECS[key].divisions for key in VARGA_ORDER})
    true_node = getattr(chart, "true_node", True)
    uncertainties = {
        name: assess_position(
            name, chart.planets[name].longitude, true_node=true_node,
            theory=theory_used(name), varga_spans=varga_spans)
        for name in present
    }
    lagna_uncertainty = assess_position(
        "Lagna", lagna.longitude, true_node=true_node,
        theory="apparent sidereal time with nutation", varga_spans=varga_spans)

    warnings: list[str] = []
    unresolved = [f"{name} ({', '.join(u.boundary_types)})"
                  for name, u in uncertainties.items() if u.boundary_warning]
    if unresolved:
        warnings.append(
            "Classification is not resolved by the calculation for "
            + "; ".join(unresolved)
            + ". These placements sit nearer a boundary than the engine's own "
              "measured error for that body, so the sign, nakshatra, pada or "
              "varga shown could be wrong. Verify externally before relying "
              "on them.")

    measured = getattr(chart, "speeds_are_measured", set(present))
    unmeasured = [p for p in present if p not in measured]
    if unmeasured:
        warnings.append(
            "Daily motion was not calculated for " + ", ".join(unmeasured)
            + " (entered positions carry direction but not speed), so their "
              "stationary state is not a measured fact.")

    # ── per-graha features ───────────────────────────────────────────────────
    planets: dict[str, PlanetFeatures] = {}
    for name in present:
        position = chart.planets[name]
        sign = position.rashi_index
        flags = dignity_flags(name, sign, position.degree_in_rashi)
        vargas = compute_varga_features(name, position.longitude, config,
                                        VARGA_ORDER)
        companions = tuple(
            c.planet2 if c.planet1 == name else c.planet1
            for c in conjunctions
            if c.same_sign and name in (c.planet1, c.planet2))
        nature = natural_nature(name, sign, companions, moon_phase)
        role = roles.get(name)

        planets[name] = PlanetFeatures(
            planet=name,
            longitude=position.longitude,
            sign=sign,
            sign_name=RASHI_NAMES[sign],
            degree_in_sign=position.degree_in_rashi,
            house=planet_houses[name],
            sign_lord=lord_of_sign(sign),
            houses_owned=list(owned.get(name, [])),
            dignity=position.dignity,
            speed=position.speed,
            retrograde=position.is_retrograde,
            stationary=position.is_stationary and name in measured,
            speed_is_measured=name in measured,
            combust=position.is_combust,
            sun_separation=position.sun_separation,
            combustion_orb=position.combustion_orb,
            vargottama=is_vargottama(vargas),
            vargas=vargas,
            dispositor=dispositor_of(name, planet_signs),
            conjunctions=[c for c in conjunctions
                          if name in (c.planet1, c.planet2)],
            aspects_given=[a for a in aspects if a.source == name],
            aspects_received=[a for a in aspects
                              if a.to_sign == sign and a.source != name],
            natural_benefic=nature == "benefic",
            natural_malefic=nature == "malefic",
            functional_nature=role.functional_nature if role else "none",
            functional_roles=list(role.roles) if role else [],
            nakshatra=position.nakshatra,
            nakshatra_lord=position.nakshatra_lord,
            pada=position.pada,
            uncertainty=uncertainties[name],
            theory=theory_used(name),
            **flags,
        )

    # ── per-bhava features ───────────────────────────────────────────────────
    houses: dict[int, HouseFeatures] = {}
    for house in range(1, 13):
        sign = sign_of_house(lagna_sign, house)
        lord = lords[house]
        occupants = sorted(p for p in present if planet_houses[p] == house)
        received = [a for a in aspects if a.to_house == house]
        categories = classify_house(house)

        influences_benefic: list[str] = []
        influences_malefic: list[str] = []
        for planet in occupants + [a.source for a in received]:
            features = planets.get(planet)
            if features is None:
                continue
            if features.natural_benefic and planet not in influences_benefic:
                influences_benefic.append(planet)
            elif features.natural_malefic and planet not in influences_malefic:
                influences_malefic.append(planet)

        houses[house] = HouseFeatures(
            house=house,
            sign=sign,
            sign_name=RASHI_NAMES[sign],
            lord=lord,
            lord_house=planet_houses.get(lord, 0),
            lord_sign=planet_signs.get(lord, -1),
            occupants=occupants,
            aspects_received=received,
            benefic_influences=influences_benefic,
            malefic_influences=influences_malefic,
            is_kendra=categories["kendra"],
            is_trikona=categories["trikona"],
            is_dusthana=categories["dusthana"],
            is_upachaya=categories["upachaya"],
            is_maraka=categories["maraka"],
        )

    features = ChartFeatures(
        lagna_sign=lagna_sign,
        lagna_sign_name=RASHI_NAMES[lagna_sign],
        lagna_lord=lord_of_sign(lagna_sign),
        lagna_degree=lagna.degree_in_rashi,
        planets=planets,
        houses=houses,
        house_lords=lords,
        conjunctions=conjunctions,
        aspects=aspects,
        parivartanas=parivartanas,
        dispositor_chains={p: chain.chain for p, chain in chains.items()},
        final_dispositors=final_dispositors(planet_signs),
        provenance={
            "house_system": "whole sign (rashi = bhava)",
            "aspect_profile": profile.name,
            "node_aspects": profile.node_convention,
            "conjunction_orb_deg": f"{conjunction_orb:g}",
            "varga_conventions": config.source,
            "combustion_profile": getattr(
                chart, "combustion_profile", None).name if getattr(
                    chart, "combustion_profile", None) else "unknown",
            "positions": chart.source,
            "ayanamsha": chart.ayanamsha_system,
        },
        warnings=warnings,
        uncertainty=summarise_uncertainty(uncertainties),
        lagna_uncertainty=lagna_uncertainty,
        graha_yuddha=yuddha,
        functional_roles=roles,
        dispositor_details=chains,
        varga_lagnas={key: varga_lagna(lagna.longitude, config, key)
                      for key in VARGA_ORDER},
        varga_config=config,
    )
    return features
