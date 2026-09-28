"""
Lordship engine (Part 4)
------------------------
Which graha rules which bhava, for a given Lagna, and which bhavas each graha
owns. Pure fact: no judgement about whether an ownership is fortunate is made
here. Functional nature — the Lagna-dependent reading of these ownerships —
is a separate module (functional_nature.py) so that FACT and INTERPRETATION
never share a function.

Rahu and Ketu own no rashi under the Parashari scheme used throughout, so they
never appear as a house lord. Some later traditions co-assign them to Kumbha
and Vrishchika; that is not assumed here, and would be a named profile if added.
"""

from __future__ import annotations

from ..planets import RASHI_LORDS, RASHI_NAMES

HOUSE_COUNT = 12

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)
DUSTHANA_HOUSES = (6, 8, 12)
UPACHAYA_HOUSES = (3, 6, 10, 11)
MARAKA_HOUSES = (2, 7)
TRISHADAYA_HOUSES = (3, 6, 11)


def sign_of_house(lagna_sign: int, house: int) -> int:
    """Sidereal sign index occupying a whole-sign house."""
    return (lagna_sign + house - 1) % 12


def house_of_sign(lagna_sign: int, sign: int) -> int:
    """Whole-sign house number a sidereal sign occupies, 1-12."""
    return ((sign - lagna_sign) % 12) + 1


def lord_of_sign(sign: int) -> str:
    return RASHI_LORDS[RASHI_NAMES[sign % 12]]


def house_lords(lagna_sign: int) -> dict[int, str]:
    """
    Lord of every bhava for a D1 Lagna.

    Returns {1: "Guru", 2: "Mangal", ...} with integer keys. Use
    `house_lords_as_strings` for the string-keyed JSON shape.
    """
    return {house: lord_of_sign(sign_of_house(lagna_sign, house))
            for house in range(1, HOUSE_COUNT + 1)}


def house_lords_as_strings(lagna_sign: int) -> dict[str, str]:
    """The same mapping with string keys, as used in JSON output."""
    return {str(house): lord for house, lord in house_lords(lagna_sign).items()}


def houses_owned(lagna_sign: int) -> dict[str, list[int]]:
    """
    Bhavas owned by each graha for this Lagna.

    Every graha except Surya and Chandra owns two rashis, so most entries have
    two houses. Rahu and Ketu own none and are returned with an empty list
    rather than omitted, so callers need no special case.
    """
    owned: dict[str, list[int]] = {"Rahu": [], "Ketu": []}
    for house, lord in house_lords(lagna_sign).items():
        owned.setdefault(lord, []).append(house)
    for houses in owned.values():
        houses.sort()
    return owned


def houses_owned_by(lagna_sign: int, planet: str) -> list[int]:
    return houses_owned(lagna_sign).get(planet, [])


def classify_house(house: int) -> dict[str, bool]:
    """Structural categories of a bhava. Category membership only, no verdict."""
    house = ((house - 1) % 12) + 1
    return {
        "kendra": house in KENDRA_HOUSES,
        "trikona": house in TRIKONA_HOUSES,
        "dusthana": house in DUSTHANA_HOUSES,
        "upachaya": house in UPACHAYA_HOUSES,
        "maraka": house in MARAKA_HOUSES,
        "trishadaya": house in TRISHADAYA_HOUSES,
    }
