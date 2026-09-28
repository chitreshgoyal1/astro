"""
Shadbala assembly (V1.4 Parts 3, 9)
-------------------------------------
Brings the six strengths together for every graha, applies the planetary-war
adjustment that needs both totals, and reports the whole with provenance.

WHAT THIS MODULE DOES NOT DO

    It does not compute anything itself. Positions come from the chart,
    aspects from the feature layer, speed and stationary state from the
    ephemeris. Each of the six components lives in its own module. This file
    is assembly and bookkeeping, which is why it is short.

SOURCE
    BPHS ch. 27, R. Santhanam translation (witness BPHS_27_SHADBALA), a
    TRANSLATION-tier witness. Nothing here can reach TRADITION_VALIDATED
    without a Sanskrit witness — see engine/sources/.
"""

from __future__ import annotations

import datetime
from typing import Optional

from ..ephemeris import mean_obliquity
from ..vargas import VargaConfig
from .chesta_bala import chesta_bala
from .dig_bala import dig_bala
from .drik_bala import drik_bala
from .kala_bala import kala_bala
from .models import SHADBALA_GRAHAS, ShadbalaResult, ShadbalaSet
from .naisargika_bala import naisargika_bala
from .sthana_bala import sthana_bala

METHODOLOGY = "bphs_santhanam_ch27"


def _component(parent, name: str):
    """Pull a named subcomponent out of a composite, or None."""
    for part in parent.subcomponents:
        if part.name == name:
            return part
    return None


def compute_shadbala(chart, features,
                     birth: Optional[datetime.datetime] = None,
                     varga_config: Optional[VargaConfig] = None,
                     bhava_madhyas: Optional[dict[int, float]] = None
                     ) -> ShadbalaSet:
    """
    Shadbala for the seven grahas.

    `birth` is needed for the temporal components. Without it Kala Bala cannot
    be computed at all, so the set is returned with a warning rather than with
    a fabricated time.
    """
    config = varga_config or VargaConfig()
    results: dict[str, ShadbalaResult] = {}
    warnings: list[str] = []

    sun = chart.planets.get("Surya")
    moon = chart.planets.get("Chandra")
    if sun is None or moon is None:
        warnings.append(
            "Surya or Chandra is absent, so paksha and ayana bala cannot be "
            "computed; Shadbala is not produced.")
        return ShadbalaSet(results={}, methodology_profile=METHODOLOGY,
                           warnings=warnings)

    if birth is None:
        warnings.append(
            "No birth datetime supplied. Kala Bala depends on the time of "
            "birth and cannot be computed; Shadbala is not produced.")
        return ShadbalaSet(results={}, methodology_profile=METHODOLOGY,
                           warnings=warnings)

    obliquity = mean_obliquity(getattr(chart, "jd_tt", 2451545.0))
    wars = list(getattr(features, "graha_yuddha", []))

    planet_houses = {name: graha.house for name, graha in features.planets.items()}
    planet_signs = {name: graha.sign for name, graha in features.planets.items()}

    measured = getattr(chart, "speeds_are_measured", set())
    unmeasured = [p for p in SHADBALA_GRAHAS
                  if p in chart.planets and p not in measured]
    if unmeasured:
        warnings.append(
            "Daily motion was not measured for " + ", ".join(unmeasured)
            + "; their Chesta Bala rests on a placeholder speed and is not a "
              "statement about the sky.")

    for planet in SHADBALA_GRAHAS:
        position = chart.planets.get(planet)
        graha = features.planet(planet)
        if position is None or graha is None:
            continue

        sthana = sthana_bala(planet, position.longitude, graha.house,
                             planet_houses, planet_signs, config)
        direction = dig_bala(planet, position.longitude,
                             chart.lagna.longitude,
                             getattr(chart, "midheaven", None),
                             bhava_madhyas)

        conjunct_malefic = any(
            (features.planet(other) or graha).natural_malefic
            for other in graha.conjunct_planets)

        temporal = kala_bala(
            planet, birth, sun.longitude, moon.longitude,
            position.longitude, position.latitude, obliquity,
            conjunct_malefic=conjunct_malefic, wars=wars)

        motion = chesta_bala(
            planet, position.speed, position.is_stationary,
            ayana_bala=_component(temporal, "ayana_bala"),
            paksha_bala=_component(temporal, "paksha_bala"))

        results[planet] = ShadbalaResult(
            planet=planet,
            sthana_bala=sthana,
            dig_bala=direction,
            kala_bala=temporal,
            chesta_bala=motion,
            naisargika_bala=naisargika_bala(planet),
            drik_bala=drik_bala(planet, features),
            methodology_profile=METHODOLOGY,
        )

    _apply_planetary_war(results, wars)

    return ShadbalaSet(results=results, methodology_profile=METHODOLOGY,
                       warnings=warnings)


def _apply_planetary_war(results: dict[str, ShadbalaResult], wars) -> None:
    """
    BPHS 27.20: the difference between the two Shadbalas goes to the victor
    and comes off the loser.

    Applied after every total exists, because it needs both. The adjustment is
    recorded in each result's notes rather than folded invisibly into a
    component, so the reported six still sum to the pre-war figure and the
    war is visible as what it is.
    """
    for war in wars:
        first = results.get(war.planet1)
        second = results.get(war.planet2)
        if first is None or second is None or war.winner is None:
            if first is not None or second is not None:
                note = (f"planetary war between {war.planet1} and "
                        f"{war.planet2} at {war.separation:.3f}°, but no "
                        f"winner was called ({war.basis}), so no adjustment "
                        f"was applied")
                for result in (first, second):
                    if result is not None:
                        result.notes = result.notes + (note,)
            continue

        difference = abs(first.total_virupa - second.total_virupa)
        loser = war.planet2 if war.winner == war.planet1 else war.planet1
        results[war.winner].notes = results[war.winner].notes + (
            f"planetary war with {loser}: victor, "
            f"+{difference:.3f} virupas (BPHS 27.20)",)
        results[loser].notes = results[loser].notes + (
            f"planetary war with {war.winner}: vanquished, "
            f"-{difference:.3f} virupas (BPHS 27.20)",)


def shadbala_from_chart(chart, features, birth=None, varga_config=None,
                        bhava_madhyas=None) -> ShadbalaSet:
    """Convenience wrapper matching the naming used elsewhere in the engine."""
    return compute_shadbala(chart, features, birth, varga_config,
                            bhava_madhyas)
