"""
Conjunction engine (Part 6)
---------------------------
Two distinct ideas, stored side by side and never collapsed into one flag:

  1. SAME-SIGN (ek rashi) — the grahas share a rashi. This is what classical
     Yoga rules mean by "conjunct": Budha-Aditya, Chandra-Mangala and the rest
     are stated in terms of rashi occupancy, not degrees. Two grahas at 0°10'
     and 29°50' of the same rashi are conjunct by this rule even though they
     are nearly 30° apart.

  2. ORB PROXIMITY — the angular separation is within some number of degrees.
     This is a modern refinement, useful for judging intensity and for graha
     yuddha (planetary war), and it is a different claim from (1).

Forcing an orb onto a classical same-rashi rule would silently change what the
rule says, so `same_sign` and `within_orb` are separate fields. A rule states
which one it relies on.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Optional

from .models import Conjunction

# Orb used for the proximity flag. It is reported alongside every conjunction
# so the number is never anonymous, and it plays no part in `same_sign`.
DEFAULT_ORB_DEG = 8.0

# Graha yuddha (planetary war) is traditionally reckoned within about one
# degree, and only between the five tara grahas — never involving the
# luminaries or the shadow grahas.
GRAHA_YUDDHA_ORB_DEG = 1.0
YUDDHA_ELIGIBLE = ("Mangal", "Budha", "Guru", "Shukra", "Shani")


def angular_separation(lon_a: float, lon_b: float) -> float:
    """Shortest angular separation between two longitudes, 0-180 degrees."""
    return abs((lon_a - lon_b + 180.0) % 360.0 - 180.0)


@dataclass(frozen=True)
class GrahaYuddha:
    """Planetary war: two tara grahas within a degree of one another."""

    planet1: str
    planet2: str
    separation: float
    winner: Optional[str]           # None when the engine will not call it
    basis: str

    def describe(self) -> str:
        outcome = f"{self.winner} prevails" if self.winner else "outcome not called"
        return (f"{self.planet1} vs {self.planet2} at {self.separation:.2f}° — "
                f"{outcome} ({self.basis})")


def compute_conjunctions(planet_longitudes: dict[str, float],
                         planet_signs: dict[str, int],
                         planet_houses: dict[str, int],
                         orb_deg: float = DEFAULT_ORB_DEG) -> list[Conjunction]:
    """
    Every graha pair that is either in the same rashi or within orb.

    A pair that is within orb but straddles a rashi boundary is still returned,
    with `same_sign=False`, because the orb fact is real and a rule may want it.
    """
    results: list[Conjunction] = []
    for a, b in combinations(sorted(planet_longitudes), 2):
        separation = angular_separation(planet_longitudes[a], planet_longitudes[b])
        same_sign = planet_signs.get(a) == planet_signs.get(b)
        within_orb = separation <= orb_deg
        if not (same_sign or within_orb):
            continue
        results.append(Conjunction(
            planet1=a,
            planet2=b,
            same_sign=same_sign,
            sign=planet_signs.get(a) if same_sign else None,
            house=planet_houses.get(a) if same_sign else None,
            angular_separation=separation,
            within_orb=within_orb,
            orb_used=orb_deg,
        ))
    return results


def compute_graha_yuddha(planet_longitudes: dict[str, float],
                         planet_latitudes: dict[str, float],
                         orb_deg: float = GRAHA_YUDDHA_ORB_DEG) -> list[GrahaYuddha]:
    """
    Planetary wars among the five tara grahas.

    Authorities differ on who wins: by northern ecliptic latitude, by brightness,
    or by the smaller longitude. Latitude is used here and named in `basis`.
    Where the engine's own accuracy cannot separate the two bodies, no winner is
    declared rather than a coin-flip being recorded as a fact.
    """
    results: list[GrahaYuddha] = []
    for a, b in combinations(YUDDHA_ELIGIBLE, 2):
        if a not in planet_longitudes or b not in planet_longitudes:
            continue
        separation = angular_separation(planet_longitudes[a], planet_longitudes[b])
        if separation > orb_deg:
            continue
        lat_a = planet_latitudes.get(a)
        lat_b = planet_latitudes.get(b)
        if lat_a is None or lat_b is None or abs(lat_a - lat_b) < 0.01:
            winner, basis = None, "latitudes too close to separate"
        else:
            winner = a if lat_a > lat_b else b
            basis = "more northerly ecliptic latitude"
        results.append(GrahaYuddha(planet1=a, planet2=b, separation=separation,
                                   winner=winner, basis=basis))
    return results


def conjunctions_to_dicts(conjunctions: list[Conjunction]) -> list[dict]:
    """JSON-shaped view, as specified in the Part 6 interface."""
    return [
        {
            "planet1": c.planet1,
            "planet2": c.planet2,
            "same_sign": c.same_sign,
            "angular_separation": round(c.angular_separation, 2),
            "within_orb": c.within_orb,
            "orb_used": c.orb_used,
        }
        for c in conjunctions
    ]
