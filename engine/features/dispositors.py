"""
Dispositor engine (Part 7)
--------------------------
The dispositor of a graha is the lord of the rashi it occupies. Following that
link repeatedly gives a chain, which must end in one of exactly two ways:

  * a graha in its own rashi, which disposits itself — the chain's terminus,
    the "final dispositor";
  * a closed loop of two or more grahas, of which the two-graha case is the
    classical Parivartana (mutual reception).

Every chain in every chart ends one of those two ways, so cycle detection is
not an edge case to guard against but the normal second outcome. It is handled
explicitly rather than by a recursion limit.

Rahu and Ketu own no rashi, so they have a dispositor but can never be one.
A chain therefore never passes through a node, and a node is never a terminus.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..planets import OWN_SIGN
from .lordships import lord_of_sign
from .models import Parivartana

# BPHS classifies an exchange by the nature of the two houses involved.
_DUSTHANA = (6, 8, 12)


@dataclass(frozen=True)
class DispositorChain:
    """The chain from one graha to its terminus, and how it terminated."""

    planet: str
    chain: list[str]                 # excludes the starting graha
    final: Optional[str]             # self-dispositing terminus, if any
    cycle: list[str]                 # the loop, if the chain closed instead
    terminated_by: str               # "self_dispositor" | "cycle" | "no_lord"

    @property
    def in_cycle(self) -> bool:
        return bool(self.cycle)

    def describe(self) -> str:
        path = " -> ".join([self.planet] + self.chain)
        if self.in_cycle:
            return f"{path}  (closes into a loop: {' ⇄ '.join(self.cycle)})"
        if self.final:
            return f"{path}  (final dispositor: {self.final})"
        return path


def dispositor_of(planet: str, planet_signs: dict[str, int]) -> Optional[str]:
    """Lord of the rashi a graha occupies, or None if the graha is absent."""
    sign = planet_signs.get(planet)
    return None if sign is None else lord_of_sign(sign)


def is_self_dispositing(planet: str, planet_signs: dict[str, int]) -> bool:
    """True when a graha sits in a rashi it owns."""
    sign = planet_signs.get(planet)
    return sign is not None and sign % 12 in OWN_SIGN.get(planet, [])


def dispositor_chain(planet: str, planet_signs: dict[str, int]) -> DispositorChain:
    """
    Walk the dispositor links from one graha until the chain terminates.

    Termination is guaranteed: the graha set is finite, so following links
    either reaches a self-dispositing graha or revisits one already seen.
    """
    chain: list[str] = []
    seen = [planet]
    current = planet

    while True:
        if is_self_dispositing(current, planet_signs):
            return DispositorChain(planet=planet, chain=chain, final=current,
                                   cycle=[], terminated_by="self_dispositor")
        nxt = dispositor_of(current, planet_signs)
        if nxt is None or nxt not in planet_signs:
            return DispositorChain(planet=planet, chain=chain, final=None,
                                   cycle=[], terminated_by="no_lord")
        if nxt in seen:
            # The chain has closed. The loop is the tail from the first
            # occurrence of the repeated graha onwards.
            start = seen.index(nxt)
            return DispositorChain(planet=planet, chain=chain + [nxt], final=None,
                                   cycle=seen[start:], terminated_by="cycle")
        chain.append(nxt)
        seen.append(nxt)
        current = nxt


def all_dispositor_chains(planet_signs: dict[str, int]) -> dict[str, DispositorChain]:
    return {planet: dispositor_chain(planet, planet_signs)
            for planet in planet_signs}


def _exchange_category(house1: int, house2: int) -> str:
    """
    BPHS names three kinds of exchange:
      dainya — one of the houses is a dusthana (6, 8 or 12)
      khala  — the 3rd house is involved
      maha   — any other exchange, between the remaining houses
    """
    if house1 in _DUSTHANA or house2 in _DUSTHANA:
        return "dainya"
    if 3 in (house1, house2):
        return "khala"
    return "maha"


def find_parivartanas(planet_signs: dict[str, int],
                      planet_houses: dict[str, int]) -> list[Parivartana]:
    """
    Mutual reception: two grahas each occupying a rashi the other owns.

    Only genuine exchanges count. A graha in its own rashi is not in exchange
    with itself, and a node is never a party because it owns no rashi.
    """
    found: list[Parivartana] = []
    planets = sorted(planet_signs)
    for i, a in enumerate(planets):
        if not OWN_SIGN.get(a):
            continue
        for b in planets[i + 1:]:
            if not OWN_SIGN.get(b):
                continue
            a_in_b = planet_signs[a] % 12 in OWN_SIGN[b]
            b_in_a = planet_signs[b] % 12 in OWN_SIGN[a]
            if a_in_b and b_in_a:
                house_a = planet_houses.get(a, 0)
                house_b = planet_houses.get(b, 0)
                found.append(Parivartana(
                    planet1=a, planet2=b,
                    house1=house_a, house2=house_b,
                    category=_exchange_category(house_a, house_b),
                ))
    return found


def final_dispositors(planet_signs: dict[str, int]) -> dict[str, Optional[str]]:
    """Terminus of each chain, or None where the chain closed into a loop."""
    return {planet: chain.final
            for planet, chain in all_dispositor_chains(planet_signs).items()}
