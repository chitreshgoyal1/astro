"""
LEGACY V1 INTERPRETATION — NOT USED BY THE CURRENT RULE ENGINE
==============================================================
This module is the V1 interpretation code, retained unchanged so that anyone
depending on its exact output still has a way to obtain it. It is NOT part of
the normal report and nothing in the current engine consumes it.

    Yogas      superseded by engine/rules/ — see below
    Dasha      superseded by engine/timing/
    Graha fal  no replacement yet; it is house-wise boilerplate text

WHY IT WAS SUPERSEDED
    The V1 audit found that several rules here do not implement the
    combination they are named after:

      * "Raja Yoga" fires on any dignified graha in a kendra. A Raja Yoga is
        a relationship between a KENDRA LORD and a TRIKONA LORD; this code has
        no notion of house lordship at all.
      * "Dhana Yoga" fires on any exalted graha in the 2nd or 11th, which is
        not a classical Dhana Yoga either.
      * "Neecha Bhanga Raja Yoga" fires on any debilitated graha in a kendra,
        inverting its own meaning — it reports a bare debility as a raja yoga
        without checking for any cancellation clause.
      * "Kemadruma" reports presence with no bhanga analysis, which inverts
        the reading for most charts that have it.

    These are kept as they were rather than quietly corrected, because the
    point of retaining this module is byte-identical V1 output for comparison.
    Do not fix them here; fix them in engine/rules/.

NEVER MERGE THESE RESULTS WITH THE RULE ENGINE'S. Two yoga systems disagreeing
inside one report is worse than either alone. The CLI exposes this only behind
--legacy-fal, under an explicit label.

Reference: BPHS, Phaladeepika, Jataka Parijata
"""

from dataclasses import dataclass
from typing import Optional
from .planets import (
    JyotishChart, PLANET_NAMES, RASHI_NAMES, STRONG_DIGNITIES, WEAK_DIGNITIES
)


# ── Yoga Detection ────────────────────────────────────────────────────────────

@dataclass
class Yoga:
    name: str
    planets_involved: list[str]
    description: str
    result: str
    strength: str  # Strong / Moderate / Weak


def _house_of(planet_name: str, chart: JyotishChart) -> int:
    """Returns 1-indexed house number of a planet from Lagna."""
    if planet_name not in chart.planets:
        return 0
    lagna_rashi = chart.lagna.rashi_index
    planet_rashi = chart.planets[planet_name].rashi_index
    return ((planet_rashi - lagna_rashi) % 12) + 1


def _planets_in_house(house: int, chart: JyotishChart) -> list[str]:
    return [p for p in PLANET_NAMES if _house_of(p, chart) == house]


def _planets_in_rashi(rashi_idx: int, chart: JyotishChart) -> list[str]:
    return [p for p in PLANET_NAMES
            if p in chart.planets and chart.planets[p].rashi_index == rashi_idx]


def detect_yogas(chart: JyotishChart) -> list[Yoga]:
    yogas = []
    planets = chart.planets
    lagna = chart.lagna

    # ── Raja Yogas ────────────────────────────────────────────────────────────
    # Kendra lords (1,4,7,10) conjunct or exchange with Trikona lords (1,5,9)
    kendra_houses = [1, 4, 7, 10]
    trikona_houses = [1, 5, 9]

    lagna_rashi = lagna.rashi_index
    kendra_rashis = [(lagna_rashi + h - 1) % 12 for h in kendra_houses]
    trikona_rashis = [(lagna_rashi + h - 1) % 12 for h in trikona_houses]

    for pname, pos in planets.items():
        if pname in ["Rahu", "Ketu"]:
            continue
        h = _house_of(pname, chart)
        if h in kendra_houses and pos.dignity in STRONG_DIGNITIES:
            yogas.append(Yoga(
                name=f"Raja Yoga ({pname})",
                planets_involved=[pname],
                description=f"{pname} is exalted/own sign in Kendra (house {h})",
                result="Success, authority, recognition, leadership qualities",
                strength="Strong" if pos.dignity == "Parama Uchcha" else "Moderate"
            ))

    # ── Dhana Yogas ───────────────────────────────────────────────────────────
    # Lords of 2nd and 11th conjunct or in each other's houses
    lord_2 = RASHI_NAMES[(lagna_rashi + 1) % 12]
    lord_11 = RASHI_NAMES[(lagna_rashi + 10) % 12]

    for pname, pos in planets.items():
        if pname in ["Rahu", "Ketu"]:
            continue
        if pos.dignity in ["Uchcha", "Parama Uchcha"] and _house_of(pname, chart) in [2, 11]:
            yogas.append(Yoga(
                name=f"Dhana Yoga ({pname})",
                planets_involved=[pname],
                description=f"{pname} strong in house of wealth ({_house_of(pname, chart)})",
                result="Financial prosperity, accumulation of wealth",
                strength="Strong"
            ))

    # ── Gajakesari Yoga ───────────────────────────────────────────────────────
    if "Guru" in planets and "Chandra" in planets:
        guru_house = _house_of("Guru", chart)
        chandra_house = _house_of("Chandra", chart)
        diff = abs(guru_house - chandra_house)
        if diff in [0, 3, 6, 9]:  # Kendra from each other
            yogas.append(Yoga(
                name="Gajakesari Yoga",
                planets_involved=["Guru", "Chandra"],
                description="Guru is in Kendra from Chandra",
                result="Fame, intelligence, leadership, respected in society",
                strength="Strong" if planets["Guru"].dignity != "Neecha" else "Weak"
            ))

    # ── Budha-Aditya Yoga ─────────────────────────────────────────────────────
    if "Budha" in planets and "Surya" in planets:
        if planets["Budha"].rashi_index == planets["Surya"].rashi_index:
            yogas.append(Yoga(
                name="Budha-Aditya Yoga",
                planets_involved=["Surya", "Budha"],
                description="Surya and Budha conjunct in same rashi",
                result="Intelligence, sharp mind, good communication, administrative skills",
                strength="Moderate"
            ))

    # ── Chandra-Mangal Yoga ───────────────────────────────────────────────────
    if "Chandra" in planets and "Mangal" in planets:
        if planets["Chandra"].rashi_index == planets["Mangal"].rashi_index:
            yogas.append(Yoga(
                name="Chandra-Mangal Yoga",
                planets_involved=["Chandra", "Mangal"],
                description="Chandra and Mangal conjunct",
                result="Wealth through mother, real estate, determined mind",
                strength="Moderate"
            ))

    # ── Pancha Mahapurusha Yogas ──────────────────────────────────────────────
    mahapurusha = {
        "Mangal":  ("Ruchaka",  "Courage, leadership, military success, athletic"),
        "Budha":   ("Bhadra",   "Intelligence, wit, business acumen, communication"),
        "Guru":    ("Hamsa",    "Wisdom, teaching, spirituality, noble character"),
        "Shukra":  ("Malavya",  "Beauty, arts, luxury, marital happiness"),
        "Shani":   ("Shasha",   "Service, discipline, longevity, mass following"),
    }
    for planet, (yoga_name, result) in mahapurusha.items():
        if planet in planets:
            pos = planets[planet]
            h = _house_of(planet, chart)
            if pos.dignity in STRONG_DIGNITIES and h in kendra_houses:
                yogas.append(Yoga(
                    name=f"{yoga_name} Yoga (Mahapurusha)",
                    planets_involved=[planet],
                    description=f"{planet} in own/exaltation in Kendra",
                    result=result,
                    strength="Strong"
                ))

    # ── Kemadruma Yoga (negative) ─────────────────────────────────────────────
    if "Chandra" in planets:
        chandra_rashi = planets["Chandra"].rashi_index
        # No planet in 2nd or 12th from Moon (excluding Sun/nodes)
        neighbors = [(chandra_rashi + 1) % 12, (chandra_rashi - 1) % 12]
        has_neighbor = any(
            p in planets and planets[p].rashi_index in neighbors
            for p in ["Mangal", "Budha", "Guru", "Shukra", "Shani"]
        )
        if not has_neighbor:
            yogas.append(Yoga(
                name="Kemadruma Yoga",
                planets_involved=["Chandra"],
                description="No planet in 2nd or 12th from Moon",
                result="Struggles, instability, emotional disturbances (can be cancelled by other yogas)",
                strength="Weak"
            ))

    # ── Neecha Bhanga Raja Yoga ───────────────────────────────────────────────
    for pname, pos in planets.items():
        if pos.dignity in WEAK_DIGNITIES:
            # Check if lord of debilitation sign is in kendra, or if debilitated planet's exaltation lord is strong
            h = _house_of(pname, chart)
            if h in kendra_houses:
                yogas.append(Yoga(
                    name=f"Neecha Bhanga Raja Yoga ({pname})",
                    planets_involved=[pname],
                    description=f"Debilitated {pname} in Kendra — cancellation of debility",
                    result="Challenges overcome, rise after initial setbacks, strong character",
                    strength="Moderate"
                ))

    return yogas


# ── Vimshottari Dasha ─────────────────────────────────────────────────────────

DASHA_ORDER = ["Ketu", "Shukra", "Surya", "Chandra", "Mangal",
               "Rahu", "Guru", "Shani", "Budha"]
DASHA_YEARS = {"Ketu": 7, "Shukra": 20, "Surya": 6, "Chandra": 10, "Mangal": 7,
               "Rahu": 18, "Guru": 16, "Shani": 19, "Budha": 17}
TOTAL_YEARS = 120

NAKSHATRA_DASHA_LORD = [
    "Ketu", "Shukra", "Surya", "Chandra", "Mangal",
    "Rahu", "Guru", "Shani", "Budha",
    "Ketu", "Shukra", "Surya", "Chandra", "Mangal",
    "Rahu", "Guru", "Shani", "Budha",
    "Ketu", "Shukra", "Surya", "Chandra", "Mangal",
    "Rahu", "Guru", "Shani", "Budha"
]


@dataclass
class DashaPeriod:
    planet: str
    start_age: float
    end_age: float
    years: int

    def format_age(self, age: float) -> str:
        y = int(age)
        m = int((age - y) * 12)
        return f"{y}y {m}m"

    def __str__(self):
        return (f"{self.planet:<10} {self.format_age(self.start_age):>8} → "
                f"{self.format_age(self.end_age):>8}  ({self.years} years)")


def compute_vimshottari_dasha(chart: JyotishChart, birth_date) -> list[DashaPeriod]:
    """
    Compute Vimshottari Dasha sequence from birth.
    birth_date: datetime object
    Returns list of DashaPeriod (mahadasha only, 120 years)
    """
    # Moon's nakshatra determines starting dasha
    moon_nak_idx = chart.planets["Chandra"].nakshatra_index
    moon_lon = chart.planets["Chandra"].longitude

    dasha_lord = NAKSHATRA_DASHA_LORD[moon_nak_idx]
    dasha_idx = DASHA_ORDER.index(dasha_lord)

    # How much of current dasha has elapsed
    # Moon's position within nakshatra (each = 13°20' = 800')
    nak_span = 360 / 27  # 13.333...°
    moon_in_nak = moon_lon % nak_span
    fraction_elapsed = moon_in_nak / nak_span
    current_dasha_years = DASHA_YEARS[dasha_lord]
    years_elapsed = fraction_elapsed * current_dasha_years
    years_remaining = current_dasha_years - years_elapsed

    periods = []
    current_age = 0.0

    # First dasha (partial)
    periods.append(DashaPeriod(
        planet=dasha_lord,
        start_age=0.0,
        end_age=years_remaining,
        years=current_dasha_years
    ))
    current_age = years_remaining

    # Subsequent dashas
    idx = (dasha_idx + 1) % 9
    while current_age < 120:
        planet = DASHA_ORDER[idx]
        yrs = DASHA_YEARS[planet]
        end_age = min(current_age + yrs, 120)
        periods.append(DashaPeriod(
            planet=planet,
            start_age=current_age,
            end_age=end_age,
            years=yrs
        ))
        current_age = end_age
        idx = (idx + 1) % 9

    return periods


# ── Planet Results (Graha Fal) ────────────────────────────────────────────────

GRAHA_FAL = {
    "Surya": {
        1:  "Confident, leadership, govt favour, strong constitution",
        2:  "Speech issues possible, family wealth, harsh speaker",
        3:  "Courage, younger siblings, short travels, own efforts",
        4:  "Property, mother, vehicles — challenges in domestic life",
        5:  "Intelligence, leadership, political inclination, few children",
        6:  "Victory over enemies, good health, service sector",
        7:  "Marital tensions, strong personality partner, diplomatic",
        8:  "Health concerns, father issues, obstacles, longevity variable",
        9:  "Father-like guru, dharmic, religious travels, fortune",
        10: "Career success, govt favour, authority, social status",
        11: "Gains, elder siblings, fulfilment of desires, income",
        12: "Expenses, foreign lands, eye issues, spiritual inclination",
    },
    "Chandra": {
        1: "Attractive personality, emotional, good memory, public popularity",
        2: "Family wealth, sweet speech, good food, monetary gains",
        3: "Courage, travelling, siblings, writng, communication",
        4: "Mother's love, property, vehicles, domestic happiness",
        5: "Intelligence, education, children, romance, speculation",
        6: "Health fluctuations, enemies, maternal relatives, service",
        7: "Attractive spouse, travel, public life, emotional relationships",
        8: "Ups and downs, occult interest, inheritance, health",
        9: "Fortunate, religious, travels, good relations with father",
        10: "Career in public life, hospitality, agriculture, mother's support",
        11: "Gains, wealthy, desires fulfilled, elder siblings helpful",
        12: "Expenses, foreign stay, spiritual, sleep issues, losses",
    },
    "Mangal": {
        1: "Energetic, bold, quick-tempered, athletic, leadership",
        2: "Financial gains through effort, harsh speech, family conflicts",
        3: "Courageous, adventurous, siblings helpful, self-made",
        4: "Property and vehicles, mother issues, domestic disputes",
        5: "Authority, sports, speculation, children issues possible",
        6: "Victory over enemies, surgery possible, police/military",
        7: "Manglik influence, passionate marriage, partner bold",
        8: "Accidents possible, surgeries, occult, inheritance",
        9: "Religious pilgrimages, charitable, younger siblings support",
        10: "Leadership career, technical, engineering, govt/military",
        11: "Gains through courage, elder brothers, sports earnings",
        12: "Expenses, foreign, hidden enemies, hospitalization possible",
    },
    "Budha": {
        1: "Intelligent, witty, communicative, youthful appearance",
        2: "Wealth through intelligence, good speech, business acumen",
        3: "Writing, media, siblings, short travel, communication",
        4: "Education, property, mother's intelligence, domestic harmony",
        5: "Sharp intellect, mathematics, children intelligent, creativity",
        6: "Service, health profession, analytical, debt management",
        7: "Intelligent spouse, business partnerships, travel",
        8: "Research, occult study, longevity, inheritance",
        9: "Higher education, travel, philosophy, father's wisdom",
        10: "Career in communication, media, business, administration",
        11: "Income through trade, elder siblings helpful, wishes fulfilled",
        12: "Foreign languages, spiritual study, expenses on education",
    },
    "Guru": {
        1: "Wise, benevolent, respected, healthy, fortunate",
        2: "Family prosperity, good speech, financial wisdom",
        3: "Younger siblings support, courage, short travels",
        4: "Domestic happiness, property, mother's wisdom, education",
        5: "Good children, intelligence, spiritual wisdom, luck",
        6: "Victory over enemies, health, judicial profession",
        7: "Wise and noble spouse, beneficial partnerships, travel",
        8: "Longevity, occult wisdom, inheritance, spiritual depth",
        9: "Most auspicious — dharma, guru's grace, fortune, father",
        10: "Career excellence, teaching, law, administration, reputation",
        11: "Gains, elder siblings, desires fulfilled, wealth",
        12: "Spiritual liberation, foreign travel, ashram life, expenses",
    },
    "Shukra": {
        1: "Beautiful, charming, artistic, love for luxury, social",
        2: "Wealth, family happiness, sweet speech, ornaments",
        3: "Arts, music, writing, younger siblings, travel",
        4: "Vehicles, property, domestic luxury, mother's love",
        5: "Romance, creativity, children, arts, speculation",
        6: "Service in arts/beauty, health issues related to kidney",
        7: "Beautiful/artistic spouse, marital happiness, partnerships",
        8: "Occult, inheritance, spouse's wealth, hidden pleasures",
        9: "Fortune, religious arts, father's wealth, pilgrimages",
        10: "Career in arts, beauty, luxury goods, diplomacy, success",
        11: "Gains through arts, wealthy elder siblings, desires fulfilled",
        12: "Expenses on luxury, foreign pleasures, spiritual devotion",
    },
    "Shani": {
        1: "Hardworking, disciplined, delays in life, serious personality",
        2: "Family responsibilities, slow wealth accumulation, speech",
        3: "Hard-working, younger siblings, long travels, persistence",
        4: "Property through hard work, mother issues, late domestic joy",
        5: "Delays in children, disciplined mind, service-oriented",
        6: "Strong against enemies, good in service/labour, health",
        7: "Delayed marriage, older/serious spouse, long-lasting union",
        8: "Longevity, chronic health issues, occult, deep research",
        9: "Karmic dharma, father's discipline, late fortune, service",
        10: "Career through hard work, politics, labour, slow but sure rise",
        11: "Gains through persistence, older friends, delayed fulfilment",
        12: "Foreign lands, isolation, spiritual liberation, expenses",
    },
}


def get_graha_fal(chart: JyotishChart) -> dict[str, str]:
    """Returns house-based results for each planet."""
    results = {}
    for pname in PLANET_NAMES:
        if pname in ["Rahu", "Ketu"]:
            results[pname] = f"House {_house_of(pname, chart)} — Rahu/Ketu axis effects (karmic)"
            continue
        if pname in chart.planets and pname in GRAHA_FAL:
            h = _house_of(pname, chart)
            base_fal = GRAHA_FAL[pname].get(h, "Results to be calculated")
            dignity = chart.planets[pname].dignity
            # Modify based on dignity
            if dignity in ["Uchcha", "Parama Uchcha"]:
                results[pname] = f"(Exalted — strong positive) {base_fal}"
            elif dignity == "Moolatrikona":
                results[pname] = f"(Moolatrikona — strong) {base_fal}"
            elif dignity == "Swa":
                results[pname] = f"(Own sign — positive) {base_fal}"
            elif dignity in WEAK_DIGNITIES:
                results[pname] = f"(Debilitated — challenges) {base_fal}"
            else:
                results[pname] = base_fal
            if chart.planets[pname].is_combust:
                results[pname] += "  [combust — results weakened]"
    return results


# ── Summary Report ────────────────────────────────────────────────────────────

def generate_fal_report(chart: JyotishChart, birth_date=None) -> str:
    """
    The V1 report, unchanged.

    Reached only via --legacy-fal. The banner is part of the output so that a
    saved or pasted report cannot be mistaken for the current engine's.
    """
    lines = []
    lines.append("\n" + "═"*62)
    lines.append("  LEGACY V1 INTERPRETATION")
    lines.append("  NOT USED BY THE CURRENT RULE ENGINE")
    lines.append("═"*62)
    lines.append("  Retained for regression and comparison only. The yoga")
    lines.append("  rules below are the superseded V1 ones: 'Raja Yoga' here")
    lines.append("  means a dignified graha in a kendra, not a kendra-trikona")
    lines.append("  lord relationship, and Kemadruma is reported without its")
    lines.append("  cancellation analysis. Use the YOGA ANALYSIS section.")
    lines.append("═"*62)
    lines.append("  FAL REPORT (Interpretations)")
    lines.append("═"*62)

    # Yogas
    yogas = detect_yogas(chart)
    lines.append(f"\n  YOGAS PRESENT ({len(yogas)} found):")
    lines.append("  " + "─"*58)
    if yogas:
        for y in yogas:
            lines.append(f"\n  ◆ {y.name}  [{y.strength}]")
            lines.append(f"    {y.description}")
            lines.append(f"    Result: {y.result}")
    else:
        lines.append("  No major yogas detected.")

    # Graha Fal
    lines.append(f"\n\n  GRAHA FAL (Planet Results by House):")
    lines.append("  " + "─"*58)
    fal = get_graha_fal(chart)
    for pname in PLANET_NAMES:
        if pname in fal:
            h = _house_of(pname, chart)
            lines.append(f"\n  {pname:<10} (House {h:>2}): {fal[pname]}")

    # Dasha
    if birth_date and "Chandra" in chart.planets:
        lines.append(f"\n\n  VIMSHOTTARI DASHA SEQUENCE:")
        lines.append("  " + "─"*58)
        lines.append(f"  {'Planet':<12} {'Start Age':>10} {'End Age':>10}  {'Duration'}")
        lines.append("  " + "─"*58)
        dashas = compute_vimshottari_dasha(chart, birth_date)
        for d in dashas:
            lines.append(f"  {d.planet:<12} {d.format_age(d.start_age):>10} → "
                        f"{d.format_age(d.end_age):>10}  ({d.years} years)")

    lines.append("\n" + "═"*62 + "\n")
    return "\n".join(lines)
