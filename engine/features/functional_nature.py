"""
Functional nature (Part 12)
---------------------------
Lagna-dependent classification of the grahas by the bhavas they own. This is
kept strictly apart from natural benefic/malefic character:

  NATURAL   — permanent. Guru is a benefic in every chart ever cast.
  FUNCTIONAL— depends entirely on the Lagna. Guru owning the 3rd and 6th from
              a Vrishabha Lagna is functionally difficult, while remaining a
              natural benefic.

Both are reported. Neither is turned into a prediction here: this module
returns roles and categories, and stops. What a Yogakaraka "means" is
interpretation and belongs in the rule engine and, later, in the narrative layer.

Rahu and Ketu own no rashi, so they have no functional nature under this
scheme. They are reported as `none` rather than being forced into a category;
the common practice of treating a node as taking on its dispositor's function
is a tradition-specific reading, not a lordship fact, so it is not applied here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .lordships import (
    DUSTHANA_HOUSES, KENDRA_HOUSES, MARAKA_HOUSES, TRIKONA_HOUSES,
    TRISHADAYA_HOUSES, UPACHAYA_HOUSES, houses_owned,
)

# A graha owning both a kendra and a trikona is a Yogakaraka. Because the 1st
# house is both, ownership of the 1st alone never qualifies: the classical
# requirement is a kendra AND a trikona other than that shared house.
YOGAKARAKA_NOTE = ("owns both a kendra and a trikona, counting the 1st house "
                   "only once")


@dataclass
class FunctionalRole:
    """What one graha owns, and the categories that ownership puts it in."""

    planet: str
    houses_owned: list[int]
    roles: list[str] = field(default_factory=list)
    functional_nature: str = "neutral"
    is_yogakaraka: bool = False
    is_lagna_lord: bool = False
    kendra_houses_owned: list[int] = field(default_factory=list)
    trikona_houses_owned: list[int] = field(default_factory=list)
    dusthana_houses_owned: list[int] = field(default_factory=list)
    maraka_houses_owned: list[int] = field(default_factory=list)
    reason: str = ""

    def describe(self) -> str:
        owned = ", ".join(str(h) for h in self.houses_owned) or "none"
        roles = ", ".join(self.roles) or "no functional role"
        return f"{self.planet}: owns {owned} — {roles}"


def _classify(planet: str, owned: list[int]) -> FunctionalRole:
    kendra = [h for h in owned if h in KENDRA_HOUSES]
    trikona = [h for h in owned if h in TRIKONA_HOUSES]
    dusthana = [h for h in owned if h in DUSTHANA_HOUSES]
    maraka = [h for h in owned if h in MARAKA_HOUSES]
    upachaya = [h for h in owned if h in UPACHAYA_HOUSES]
    trishadaya = [h for h in owned if h in TRISHADAYA_HOUSES]

    roles: list[str] = []
    if 1 in owned:
        roles.append("lagna_lord")
    if kendra:
        roles.append("kendra_lord")
    if trikona:
        roles.append("trikona_lord")
    if dusthana:
        roles.append("dusthana_lord")
    if maraka:
        roles.append("maraka_lord")
    if upachaya:
        roles.append("upachaya_lord")
    if trishadaya:
        roles.append("trishadaya_lord")
    if 9 in owned:
        roles.append("dharma_lord")          # 9th — dharmadhipati
    if 10 in owned:
        roles.append("karma_lord")           # 10th — karmadhipati

    # Yogakaraka: a kendra and a trikona, not counting the 1st twice.
    kendra_beyond_first = [h for h in kendra if h != 1]
    trikona_beyond_first = [h for h in trikona if h != 1]
    is_yogakaraka = bool(kendra_beyond_first and trikona_beyond_first)
    if is_yogakaraka:
        roles.append("yogakaraka")

    if not owned:
        nature, reason = "none", "owns no rashi under the Parashari scheme"
    elif is_yogakaraka:
        nature, reason = "yogakaraka", YOGAKARAKA_NOTE
    elif trikona and not dusthana:
        nature, reason = "benefic", "owns a trikona and no dusthana"
    elif dusthana and not trikona:
        nature, reason = "malefic", "owns a dusthana and no trikona"
    elif trikona and dusthana:
        nature, reason = "mixed", "owns both a trikona and a dusthana"
    elif kendra:
        # Kendradhipatya dosha: a natural benefic owning only kendras loses
        # some of its benefic power. That qualifier is recorded, not applied.
        nature, reason = "neutral", "owns kendras only (kendradhipatya applies)"
    else:
        nature, reason = "neutral", "owns neither a trikona nor a dusthana"

    return FunctionalRole(
        planet=planet,
        houses_owned=sorted(owned),
        roles=roles,
        functional_nature=nature,
        is_yogakaraka=is_yogakaraka,
        is_lagna_lord=1 in owned,
        kendra_houses_owned=sorted(kendra),
        trikona_houses_owned=sorted(trikona),
        dusthana_houses_owned=sorted(dusthana),
        maraka_houses_owned=sorted(maraka),
        reason=reason,
    )


def functional_roles(lagna_sign: int) -> dict[str, FunctionalRole]:
    """Functional classification of every graha for one Lagna."""
    owned = houses_owned(lagna_sign)
    return {planet: _classify(planet, houses) for planet, houses in owned.items()}


def yogakarakas(lagna_sign: int) -> list[str]:
    """Grahas that own both a kendra and a trikona for this Lagna."""
    return sorted(p for p, r in functional_roles(lagna_sign).items()
                  if r.is_yogakaraka)


def lords_of_category(lagna_sign: int, category: str) -> list[str]:
    """
    Grahas holding a named role, e.g. "kendra_lord", "dusthana_lord",
    "maraka_lord", "yogakaraka".
    """
    return sorted(p for p, r in functional_roles(lagna_sign).items()
                  if category in r.roles)
