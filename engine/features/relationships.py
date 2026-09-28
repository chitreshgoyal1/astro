"""
Graha relationships (Naisargika Maitri)
---------------------------------------
Permanent natural friendship between the grahas, used to decide whether a
placement sits in a friendly, neutral or inimical rashi.

The table below is the standard BPHS naisargika (natural) scheme. It is
deliberately NOT combined with tatkalika (temporary, position-derived)
friendship into a single "compound" relationship: the two answer different
questions, schools weigh them differently, and merging them silently would
hide which one produced a result. Temporary friendship is computed separately
and both are reported.

Rahu and Ketu are not part of the classical naisargika table. Rather than
invent entries for them, they are reported as `unclassified`.
"""

from __future__ import annotations

from ..planets import OWN_SIGN

FRIEND = "friend"
NEUTRAL = "neutral"
ENEMY = "enemy"
UNCLASSIFIED = "unclassified"

CLASSICAL_GRAHAS = ("Surya", "Chandra", "Mangal", "Budha",
                    "Guru", "Shukra", "Shani")

# BPHS Ch.3: naisargika maitri. Any classical graha not listed as friend or
# enemy for a given graha is its neutral (sama).
_FRIENDS: dict[str, tuple[str, ...]] = {
    "Surya":   ("Chandra", "Mangal", "Guru"),
    "Chandra": ("Surya", "Budha"),
    "Mangal":  ("Surya", "Chandra", "Guru"),
    "Budha":   ("Surya", "Shukra"),
    "Guru":    ("Surya", "Chandra", "Mangal"),
    "Shukra":  ("Budha", "Shani"),
    "Shani":   ("Budha", "Shukra"),
}

_ENEMIES: dict[str, tuple[str, ...]] = {
    "Surya":   ("Shukra", "Shani"),
    "Chandra": (),                       # the Moon has no natural enemy
    "Mangal":  ("Budha",),
    "Budha":   ("Chandra",),
    "Guru":    ("Budha", "Shukra"),
    "Shukra":  ("Surya", "Chandra"),
    "Shani":   ("Surya", "Chandra", "Mangal"),
}


def natural_relationship(of_planet: str, towards: str) -> str:
    """Permanent relationship of one graha towards another."""
    if of_planet not in _FRIENDS or towards not in CLASSICAL_GRAHAS:
        return UNCLASSIFIED
    if of_planet == towards:
        return FRIEND
    if towards in _FRIENDS[of_planet]:
        return FRIEND
    if towards in _ENEMIES[of_planet]:
        return ENEMY
    return NEUTRAL


def sign_relationship(planet: str, sign: int) -> str:
    """
    Relationship between a graha and the rashi it occupies, via that rashi's
    lord. A graha in its own rashi is reported as `friend`; callers that need
    to distinguish own-sign from friendly-sign should read the dignity instead.
    """
    from .lordships import lord_of_sign
    if planet not in CLASSICAL_GRAHAS:
        return UNCLASSIFIED
    if sign % 12 in OWN_SIGN.get(planet, []):
        return FRIEND
    return natural_relationship(planet, lord_of_sign(sign))


def temporary_relationship(house_a: int, house_b: int) -> str:
    """
    Tatkalika maitri: grahas in the 2nd, 3rd, 4th, 10th, 11th or 12th from one
    another are temporary friends; the rest are temporary enemies. There is no
    temporary-neutral category in the classical scheme.
    """
    distance = ((house_b - house_a) % 12) + 1
    return FRIEND if distance in (2, 3, 4, 10, 11, 12) else ENEMY


def compound_relationship(natural: str, temporary: str) -> str:
    """
    Panchadha maitri, the five-fold compound, reported separately from its two
    inputs so that a caller can always see which component drove the result.
    """
    if natural == UNCLASSIFIED:
        return UNCLASSIFIED
    pair = (natural, temporary)
    return {
        (FRIEND, FRIEND):   "great_friend",
        (FRIEND, ENEMY):    NEUTRAL,
        (NEUTRAL, FRIEND):  FRIEND,
        (NEUTRAL, ENEMY):   ENEMY,
        (ENEMY, FRIEND):    NEUTRAL,
        (ENEMY, ENEMY):     "great_enemy",
    }.get(pair, NEUTRAL)


def relationship_table() -> dict[str, dict[str, str]]:
    """Full natural relationship matrix, for reporting and tests."""
    return {a: {b: natural_relationship(a, b) for b in CLASSICAL_GRAHAS}
            for a in CLASSICAL_GRAHAS}
