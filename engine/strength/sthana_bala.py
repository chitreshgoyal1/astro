"""
Sthana Bala — positional strength (V1.4 Part 4)
------------------------------------------------
Five subcomponents, each computed and reported separately:

    Uchcha Bala          proximity to the exaltation point
    Saptavargaja Bala    dignity across seven divisional charts
    Ojhayugma Bala       odd/even rashi and navamsha placement
    Kendradi Bala        angular, succedent or cadent house
    Drekkana Bala        first, second or third decanate

SOURCE
    BPHS ch. 27.1-6, R. Santhanam translation (witness BPHS_27_SHADBALA).
    Each function records the passage it implements and, where the wording is
    ambiguous or the OCR damaged, says so rather than choosing quietly.
"""

from __future__ import annotations

from typing import Optional

from ..features.relationships import (
    ENEMY, FRIEND, NEUTRAL, natural_relationship,
)
from ..planets import DEBILITATION, MOOLATRIKONA, OWN_SIGN, RASHI_LORDS, RASHI_NAMES
from ..vargas import VargaConfig
from .models import BalaComponent

WITNESS = ("BPHS_27_SHADBALA",)
PROFILE = "bphs_santhanam_ch27"

# BPHS 27.2-4. Virupas awarded for a graha's standing in each of the seven
# vargas. The "extreme friend"/"extreme enemy" tiers are the compound
# (panchadha) relationship, which the witness says is judged in the RASI chart
# only and not in the divisional chart being scored.
SAPTAVARGAJA_VIRUPAS = {
    "moolatrikona": 45.0,
    "own": 30.0,
    "great_friend": 20.0,
    "friend": 15.0,
    "neutral": 10.0,
    "enemy": 4.0,
    "great_enemy": 2.0,
}

# BPHS 27.2: Rasi, Hora, Drekkana, Saptamamsa, Navamsa, Dwadasamsa,
# Trimsamsa. Named explicitly in the witness, so the set is not a choice.
SAPTAVARGA_CHARTS = ("D1", "D2", "D3", "D7", "D9", "D12", "D30")

# BPHS 27.5.
KENDRADI_VIRUPAS = {"kendra": 60.0, "panaphara": 30.0, "apoklima": 15.0}

# BPHS 27.6. Male grahas gain in the first decanate, female in the second,
# neutral in the third.
MALE_GRAHAS = ("Surya", "Mangal", "Guru")
FEMALE_GRAHAS = ("Chandra", "Shukra")
NEUTRAL_GRAHAS = ("Budha", "Shani")

# BPHS 27.4.5: Venus and the Moon gain in even rashis, the rest in odd.
EVEN_SIGN_GRAHAS = ("Chandra", "Shukra")


def _fold(degrees: float) -> float:
    """Reduce an arc to 0-180, as the witness directs for Uchcha and Dig."""
    degrees %= 360.0
    return 360.0 - degrees if degrees > 180.0 else degrees


def uchcha_bala(planet: str, longitude: float) -> BalaComponent:
    """
    BPHS 27.1: deduct the deep debilitation point from the graha's longitude;
    fold anything above 180 degrees; divide by 3.

    Maximum 60 virupas at exact exaltation, zero at exact debilitation, and
    linear between. The witness works the example of the Sun at Pisces 12°15'
    against a debilitation point of Libra 10°, giving 50.75 virupas — which
    this function reproduces.
    """
    entry = DEBILITATION.get(planet)
    if entry is None:
        return BalaComponent(
            name="uchcha_bala", value_virupa=0.0,
            calculation_profile=PROFILE, source_ref_ids=WITNESS,
            validation_status="UNVERIFIED",
            detail=f"{planet} has no debilitation point in this engine")

    debilitation_longitude = entry[0] * 30.0 + entry[1]
    arc = _fold(longitude - debilitation_longitude)
    return BalaComponent(
        name="uchcha_bala",
        value_virupa=arc / 3.0,
        calculation_profile=PROFILE,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=(f"{arc:.4f}° from deep debilitation at "
                f"{RASHI_NAMES[entry[0]]} {entry[1]}°, divided by 3"),
    )


def _compound_relationship_tier(planet: str, sign: int,
                                planet_houses: dict[str, int],
                                planet_signs: dict[str, int]) -> str:
    """
    The graha's standing in a rashi, as one of the seven Saptavargaja tiers.

    The witness says the compound relationship is read in the RASI chart, so
    the temporary (tatkalika) component uses the graha's D1 house throughout,
    even when the tier is being applied to a divisional placement.
    """
    if planet in MOOLATRIKONA:
        mt_sign, _start, _end = MOOLATRIKONA[planet]
        if sign == mt_sign:
            return "moolatrikona"
    if sign in OWN_SIGN.get(planet, []):
        return "own"

    lord = RASHI_LORDS[RASHI_NAMES[sign % 12]]
    if lord == planet:
        return "own"

    natural = natural_relationship(planet, lord)
    if natural == "unclassified":
        return "neutral"

    own_house = planet_houses.get(planet)
    lord_house = planet_houses.get(lord)
    if own_house is None or lord_house is None:
        temporary = NEUTRAL
    else:
        distance = ((lord_house - own_house) % 12) + 1
        temporary = FRIEND if distance in (2, 3, 4, 10, 11, 12) else ENEMY

    compound = {
        (FRIEND, FRIEND): "great_friend",
        (FRIEND, ENEMY): "neutral",
        (NEUTRAL, FRIEND): "friend",
        (NEUTRAL, ENEMY): "enemy",
        (ENEMY, FRIEND): "neutral",
        (ENEMY, ENEMY): "great_enemy",
    }.get((natural, temporary))
    return compound or "neutral"


def saptavargaja_bala(planet: str, longitude: float,
                      planet_houses: dict[str, int],
                      planet_signs: dict[str, int],
                      varga_config: Optional[VargaConfig] = None
                      ) -> BalaComponent:
    """
    BPHS 27.2-4: the graha's standing in each of seven vargas, summed.

    Ranges from 14 virupas (great enemy everywhere) to 315 (moolatrikona
    everywhere), so this dominates Sthana Bala — which is why the per-varga
    breakdown is kept rather than only the sum.
    """
    config = varga_config or VargaConfig()
    parts: list[BalaComponent] = []
    total = 0.0

    for chart in SAPTAVARGA_CHARTS:
        sign = config.compute(chart, longitude).rashi_index
        tier = _compound_relationship_tier(planet, sign, planet_houses,
                                           planet_signs)
        value = SAPTAVARGAJA_VIRUPAS[tier]
        total += value
        parts.append(BalaComponent(
            name=f"saptavargaja_{chart}",
            value_virupa=value,
            calculation_profile=PROFILE,
            source_ref_ids=WITNESS,
            validation_status="IMPLEMENTATION_MATCHED",
            detail=f"{RASHI_NAMES[sign]} — {tier.replace('_', ' ')}",
        ))

    return BalaComponent(
        name="saptavargaja_bala",
        value_virupa=total,
        calculation_profile=PROFILE,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=f"sum over {', '.join(SAPTAVARGA_CHARTS)}",
        subcomponents=tuple(parts),
    )


def ojhayugma_bala(planet: str, longitude: float,
                   varga_config: Optional[VargaConfig] = None
                   ) -> BalaComponent:
    """
    BPHS 27.4.5: Venus and the Moon gain in even rashis, the rest in odd;
    the same again for the navamsha. 15 virupas each, 30 maximum.

    NOTE ON THE WITNESS. The verse says "a quarter of Rupa (i.e. 15 Virupas)",
    but Santhanam's explanatory note beneath it reads "35 Virupas". Fifteen is
    a quarter of sixty and thirty-five is not, so the note is an OCR or
    typesetting error and the verse is followed. Recorded as an ambiguity in
    the source registry rather than silently resolved.
    """
    config = varga_config or VargaConfig()
    wants_even = planet in EVEN_SIGN_GRAHAS

    rashi = config.compute("D1", longitude).rashi_index
    navamsha = config.compute("D9", longitude).rashi_index

    parts = []
    total = 0.0
    for label, sign in (("rashi", rashi), ("navamsha", navamsha)):
        is_even = sign % 2 == 1          # index 1 = Vrishabha = even rashi
        gains = is_even if wants_even else not is_even
        value = 15.0 if gains else 0.0
        total += value
        parts.append(BalaComponent(
            name=f"ojhayugma_{label}",
            value_virupa=value,
            calculation_profile=PROFILE,
            source_ref_ids=WITNESS,
            validation_status="IMPLEMENTATION_MATCHED",
            detail=(f"{RASHI_NAMES[sign]} is "
                    f"{'even' if is_even else 'odd'}; {planet} gains in "
                    f"{'even' if wants_even else 'odd'}"),
        ))

    return BalaComponent(
        name="ojhayugma_bala",
        value_virupa=total,
        calculation_profile=PROFILE,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail="rashi and navamsha parity",
        subcomponents=tuple(parts),
    )


def kendradi_bala(planet: str, house: int) -> BalaComponent:
    """BPHS 27.5: 60 virupas in a kendra, 30 in a panaphara, 15 in an apoklima."""
    if house in (1, 4, 7, 10):
        kind = "kendra"
    elif house in (2, 5, 8, 11):
        kind = "panaphara"
    else:
        kind = "apoklima"
    return BalaComponent(
        name="kendradi_bala",
        value_virupa=KENDRADI_VIRUPAS[kind],
        calculation_profile=PROFILE,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=f"house {house} is a {kind}",
    )


def drekkana_bala(planet: str, longitude: float) -> BalaComponent:
    """
    BPHS 27.6: male grahas gain in the first decanate of a rashi, female in
    the second, neutral in the third. 15 virupas, or none.

    The decanate here is the third of the OCCUPIED rashi by degree, not the
    D3 divisional sign — the witness says "first, second or third part of a
    sign", which is the positional third.
    """
    degree = longitude % 30.0
    third = min(int(degree / 10.0), 2)

    if planet in MALE_GRAHAS:
        wanted, group = 0, "male"
    elif planet in FEMALE_GRAHAS:
        wanted, group = 1, "female"
    else:
        wanted, group = 2, "neutral"

    gains = third == wanted
    return BalaComponent(
        name="drekkana_bala",
        value_virupa=15.0 if gains else 0.0,
        calculation_profile=PROFILE,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=(f"{degree:.2f}° is decanate {third + 1}; {planet} is "
                f"{group} and gains in decanate {wanted + 1}"),
    )


def sthana_bala(planet: str, longitude: float, house: int,
                planet_houses: dict[str, int],
                planet_signs: dict[str, int],
                varga_config: Optional[VargaConfig] = None) -> BalaComponent:
    """The five subcomponents, summed. BPHS 27.1-6."""
    parts = (
        uchcha_bala(planet, longitude),
        saptavargaja_bala(planet, longitude, planet_houses, planet_signs,
                          varga_config),
        ojhayugma_bala(planet, longitude, varga_config),
        kendradi_bala(planet, house),
        drekkana_bala(planet, longitude),
    )
    return BalaComponent(
        name="sthana_bala",
        value_virupa=sum(p.value_virupa for p in parts),
        calculation_profile=PROFILE,
        source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail="uchcha + saptavargaja + ojhayugma + kendradi + drekkana",
        subcomponents=parts,
    )
