"""
Synthetic chart construction for tests (V1.5 Part 28)
-------------------------------------------------------
Charts built to exercise ENGINE BEHAVIOUR, never to claim anything about the
sky or about a person.

WHY SYNTHETIC AND NOT REAL

    A real nativity tests whatever it happens to contain. Asking "does the
    BPHS 34.15 exception fire" of the regression chart got the answer "not on
    this chart", which is true and tests nothing: on Meena lagna neither
    participating lord owns a dusthana, so the clause never runs.

    These builders place grahas where a rule needs them. Part 28 is explicit
    that the expected results test engine behaviour and make no empirical
    claim, and nothing here is presented as a horoscope.

WHAT THEY ARE NOT

    Not ephemeris output. Longitudes are chosen, not computed, and a chart
    built here would not match the sky at any moment. Anything that needs
    real positions — accuracy, vargas, dasha boundaries — must use the
    regression charts instead.
"""

from __future__ import annotations

from engine.features.models import (
    Aspect, ChartFeatures, Conjunction, HouseFeatures, Parivartana,
    PlanetFeatures,
)
from engine.planets import RASHI_LORDS, RASHI_NAMES

BENEFICS = ("Guru", "Shukra", "Budha", "Chandra")
MALEFICS = ("Surya", "Mangal", "Shani", "Rahu", "Ketu")

EXALTATION = {
    "Surya": 0, "Chandra": 1, "Mangal": 9, "Budha": 5,
    "Guru": 3, "Shukra": 11, "Shani": 6,
}
OWN_SIGNS = {
    "Surya": (4,), "Chandra": (3,), "Mangal": (0, 7), "Budha": (2, 5),
    "Guru": (8, 11), "Shukra": (1, 6), "Shani": (9, 10),
}


def _dignity(planet: str, sign: int) -> dict:
    exalted = EXALTATION.get(planet) == sign
    debilitated = (EXALTATION.get(planet) is not None
                   and (EXALTATION[planet] + 6) % 12 == sign)
    own = sign in OWN_SIGNS.get(planet, ())
    label = ("exalted" if exalted else "debilitated" if debilitated
             else "own" if own else "neutral")
    return {
        "dignity": label, "exalted": exalted, "debilitated": debilitated,
        "own_sign": own, "moolatrikona": False,
        "friendly_sign": False, "enemy_sign": False,
        "neutral_sign": not (exalted or debilitated or own),
    }


def synthetic_features(lagna_sign: int,
                       placements: dict,
                       *,
                       aspects: tuple = (),
                       parivartanas: tuple = (),
                       shadbala_ratios: dict | None = None,
                       degrees: dict | None = None) -> ChartFeatures:
    """
    Build a ChartFeatures with grahas in chosen SIGNS.

    `placements` maps graha name to sign index 0-11. `aspects` is a tuple of
    (source, target_sign, full) triples; graha drishti is not derived from
    the placements because a test usually wants to control it exactly.

    `shadbala_ratios` attaches a minimal stand-in for a ShadbalaSet, enough
    for `features.shadbala_ratio` to answer. It is not a Shadbala
    computation and must never be used to test one.
    """
    degrees = degrees or {}
    lagna_lord = RASHI_LORDS[RASHI_NAMES[lagna_sign]]

    house_lords = {}
    for house in range(1, 13):
        sign = (lagna_sign + house - 1) % 12
        house_lords[house] = RASHI_LORDS[RASHI_NAMES[sign]]

    owned: dict[str, list[int]] = {}
    for house, lord in house_lords.items():
        owned.setdefault(lord, []).append(house)

    planets: dict[str, PlanetFeatures] = {}
    for name, sign in placements.items():
        house = ((sign - lagna_sign) % 12) + 1
        degree = degrees.get(name, 15.0)
        planets[name] = PlanetFeatures(
            planet=name, longitude=sign * 30.0 + degree, sign=sign,
            sign_name=RASHI_NAMES[sign], degree_in_sign=degree, house=house,
            sign_lord=RASHI_LORDS[RASHI_NAMES[sign]],
            houses_owned=sorted(owned.get(name, [])),
            natural_benefic=name in BENEFICS,
            natural_malefic=name in MALEFICS,
            functional_nature="neutral",
            **_dignity(name, sign))

    houses: dict[int, HouseFeatures] = {}
    for house in range(1, 13):
        sign = (lagna_sign + house - 1) % 12
        lord = house_lords[house]
        lord_features = planets.get(lord)
        occupants = [n for n, p in planets.items() if p.house == house]
        houses[house] = HouseFeatures(
            house=house, sign=sign, sign_name=RASHI_NAMES[sign], lord=lord,
            lord_house=lord_features.house if lord_features else 0,
            lord_sign=lord_features.sign if lord_features else 0,
            occupants=occupants,
            is_kendra=house in (1, 4, 7, 10),
            is_trikona=house in (1, 5, 9),
            is_dusthana=house in (6, 8, 12),
            is_upachaya=house in (3, 6, 10, 11),
            is_maraka=house in (2, 7))

    aspect_objects: list[Aspect] = []
    for source, to_sign, full in aspects:
        to_house = ((to_sign - lagna_sign) % 12) + 1
        source_house = planets[source].house if source in planets else 1
        aspect = Aspect(
            source=source, to_house=to_house, to_sign=to_sign,
            aspect_type="seventh" if full else "special_3rd",
            distance=((to_house - source_house) % 12) + 1,
            full=full, strength=1.0 if full else 0.25,
            targets=tuple(n for n, p in planets.items() if p.sign == to_sign))
        aspect_objects.append(aspect)
        if source in planets:
            planets[source].aspects_given.append(aspect)
        for name, p in planets.items():
            if p.sign == to_sign:
                p.aspects_received.append(aspect)
        houses[to_house].aspects_received.append(aspect)

    conjunctions: list[Conjunction] = []
    names = sorted(planets)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            a, b = planets[first], planets[second]
            if a.sign != b.sign:
                continue
            separation = abs(a.longitude - b.longitude)
            conjunction = Conjunction(
                planet1=first, planet2=second, same_sign=True, sign=a.sign,
                house=a.house, angular_separation=separation,
                within_orb=separation <= 8.0, orb_used=8.0)
            conjunctions.append(conjunction)
            a.conjunctions.append(conjunction)
            b.conjunctions.append(conjunction)

    swaps = []
    for first, second in parivartanas:
        swaps.append(Parivartana(
            planet1=first, planet2=second,
            house1=planets[first].house, house2=planets[second].house,
            category="maha"))

    features = ChartFeatures(
        lagna_sign=lagna_sign, lagna_sign_name=RASHI_NAMES[lagna_sign],
        lagna_lord=lagna_lord, lagna_degree=lagna_sign * 30.0 + 10.0,
        planets=planets, houses=houses, house_lords=house_lords,
        conjunctions=conjunctions, aspects=aspect_objects,
        parivartanas=swaps,
        dispositor_chains={n: [p.sign_lord] for n, p in planets.items()},
        provenance={"synthetic": "tests/synthetic.py — not ephemeris output"})

    if shadbala_ratios:
        features.shadbala = _FakeShadbala(shadbala_ratios)
    return features


class _FakeShadbalaResult:
    """Only what `shadbala_ratio` and the synthesis layer read."""

    def __init__(self, planet: str, ratio: float):
        self.planet = planet
        self.ratio = ratio
        self.required_virupa = 360.0
        self.total_virupa = 360.0 * ratio
        self.validation_status = "SYNTHETIC"


class _FakeShadbala:
    """
    A stand-in, named so no reader mistakes it for a computation.

    Exists because two textual rules put strength in their formation clause,
    so testing those rules needs a strength value and must not need the whole
    Shadbala pipeline — which has its own tests, and whose correctness is not
    what a yoga test is trying to establish.
    """

    def __init__(self, ratios: dict):
        self.results = {name: _FakeShadbalaResult(name, ratio)
                        for name, ratio in ratios.items()}
        self.is_synthetic = True
