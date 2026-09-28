"""
Dignity features
----------------
Sign-based standing of a graha, expressed as independent booleans rather than
as one label, because rules ask different questions of it: "is it exalted",
"is it in its own sign", "is it in a friendly sign". A single string forces
every caller to re-parse it, and re-parsing is where engines drift apart.

The underlying exaltation / debilitation / moolatrikona / own-sign tables live
in engine.planets and are shared with the chart assembly, so there is one
source for them.

Exaltation of Rahu and Ketu is tradition-dependent — BPHS does not assign the
nodes exaltation rashis at all, and the later tables disagree with each other
(Vrishabha/Vrishchika against Mithuna/Dhanu). The engine carries the
Vrishabha/Vrishchika pair that engine.planets already used, but marks it so
that a rule can choose to ignore node dignity entirely.
"""

from __future__ import annotations

from ..planets import (
    DEBILITATION, EXALTATION, MOOLATRIKONA, OWN_SIGN, RASHI_NAMES,
)
from .relationships import (
    CLASSICAL_GRAHAS, ENEMY, FRIEND, NEUTRAL, sign_relationship,
)

# Grahas whose exaltation rashi is not agreed across traditions.
TRADITION_DEPENDENT_DIGNITY = ("Rahu", "Ketu")

# Naisargika (natural) benefics and malefics. Budha and Chandra are
# conditional in the classical scheme and are resolved by context, so they are
# listed here with their unmodified natural character and adjusted below.
NATURAL_BENEFICS = ("Guru", "Shukra")
NATURAL_MALEFICS = ("Surya", "Mangal", "Shani", "Rahu", "Ketu")
CONDITIONAL = ("Budha", "Chandra")


def is_exalted(planet: str, sign: int) -> bool:
    entry = EXALTATION.get(planet)
    return entry is not None and sign % 12 == entry[0]


def is_debilitated(planet: str, sign: int) -> bool:
    entry = DEBILITATION.get(planet)
    return entry is not None and sign % 12 == entry[0]


def is_own_sign(planet: str, sign: int) -> bool:
    return sign % 12 in OWN_SIGN.get(planet, [])


def is_moolatrikona(planet: str, sign: int, degree_in_sign: float) -> bool:
    entry = MOOLATRIKONA.get(planet)
    if entry is None:
        return False
    mt_sign, start, end = entry
    return sign % 12 == mt_sign and start <= degree_in_sign < end


def exaltation_sign(planet: str) -> int | None:
    entry = EXALTATION.get(planet)
    return None if entry is None else entry[0]


def debilitation_sign(planet: str) -> int | None:
    entry = DEBILITATION.get(planet)
    return None if entry is None else entry[0]


def degrees_from_deep_exaltation(planet: str, sign: int,
                                 degree_in_sign: float) -> float | None:
    """How far a graha stands from its exact exaltation degree, or None."""
    entry = EXALTATION.get(planet)
    if entry is None:
        return None
    ex_sign, ex_degree = entry
    here = sign % 12 * 30.0 + degree_in_sign
    there = ex_sign * 30.0 + ex_degree
    return abs((here - there + 180.0) % 360.0 - 180.0)


def dignity_flags(planet: str, sign: int, degree_in_sign: float) -> dict[str, bool]:
    """
    Every dignity predicate for one placement.

    The categories are not mutually exclusive by construction — moolatrikona
    always falls inside an own rashi, for instance — so all are reported and
    the caller decides which it cares about.
    """
    exalted = is_exalted(planet, sign)
    debilitated = is_debilitated(planet, sign)
    own = is_own_sign(planet, sign)
    moolatrikona = is_moolatrikona(planet, sign, degree_in_sign)
    relationship = sign_relationship(planet, sign)

    return {
        "exalted": exalted,
        "debilitated": debilitated,
        "own_sign": own,
        "moolatrikona": moolatrikona,
        # A graha in its own or exaltation rashi is not additionally reported
        # as "friendly": those are stronger, distinct statements.
        "friendly_sign": (relationship == FRIEND and not own and not exalted),
        "enemy_sign": relationship == ENEMY and not debilitated,
        "neutral_sign": relationship == NEUTRAL,
    }


def natural_nature(planet: str, sign: int | None = None,
                   conjunct: tuple[str, ...] = (),
                   moon_paksha_bala: float | None = None) -> str:
    """
    Naisargika (natural) benefic or malefic character.

    Budha is benefic alone but takes on the character of whatever it joins;
    Chandra is benefic when waxing and reckoned malefic when deeply waning.
    Both conditions need context, so when that context is not supplied the
    unmodified classical default is returned rather than a guess.
    """
    if planet in NATURAL_BENEFICS:
        return "benefic"
    if planet in NATURAL_MALEFICS:
        return "malefic"
    if planet == "Budha":
        malefic_company = [p for p in conjunct if p in NATURAL_MALEFICS]
        benefic_company = [p for p in conjunct if p in NATURAL_BENEFICS]
        if malefic_company and not benefic_company:
            return "malefic"
        return "benefic"
    if planet == "Chandra":
        if moon_paksha_bala is None:
            return "benefic"
        # Waning past roughly the last quarter is the usual cut.
        return "benefic" if moon_paksha_bala >= 0.5 else "malefic"
    return "neutral"


def sign_name(sign: int) -> str:
    return RASHI_NAMES[sign % 12]
