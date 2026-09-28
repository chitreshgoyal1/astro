"""
Classical Yoga rule set (Part 11)
---------------------------------
Each rule states one combination, cites where it comes from, and keeps its
cancellation clauses separate from its formation clauses.

Two deliberate absences from the previous engine:

  * There is no generic "Raja Yoga". Raja Yoga is a *class* of combinations
    formed by a relationship between a kendra lord and a trikona lord, and the
    class has as many members as there are such pairs. Each pair, and each mode
    of relationship (conjunction, mutual aspect, exchange), is its own rule with
    its own id, so a result names the actual combination that formed.

  * There is no generic "Dhana Yoga" either, for the same reason: BPHS states
    it as relationships among the lords of the 1st, 2nd, 5th, 9th and 11th.

Where authorities disagree, the variants are separate rules carrying
`variant_of`, and they live in different named profiles. Nothing is merged.

Sources cited:
  BPHS     Brihat Parashara Hora Shastra (ch. 34 Yogas, 36 Raja Yoga,
           40 Dhana Yoga, 75 Neechabhanga; chapter numbering follows the
           Santhanam translation)
  PD       Phaladeepika, Mantreswara
  JP       Jataka Parijata, Vaidyanatha Dikshita
  SY       Saravali, Kalyana Varma
"""

from __future__ import annotations

from typing import Optional

from ..features.lordships import KENDRA_HOUSES, TRIKONA_HOUSES
from ..features.models import ChartFeatures
from . import conditions as C
from .conditions import ConditionResult
from .engine import Modifier, YogaRule
from .modifiers import lords_modifiers, standard_modifiers

# ── Pancha Mahapurusha ───────────────────────────────────────────────────────
# BPHS ch.75 / Phaladeepika ch.6: a tara graha in its OWN rashi or in
# EXALTATION, occupying a kendra FROM THE LAGNA.
#
# Two points where sources differ, both handled explicitly rather than merged:
#   * some authorities count kendras from the Moon as well as from the Lagna;
#     that is the `from_moon` variant, in a separate profile.
#   * moolatrikona is accepted here alongside own rashi, because for all five
#     of these grahas the moolatrikona arc lies inside a rashi they own.

MAHAPURUSHA = [
    ("ruchaka", "Ruchaka", "Mangal"),
    ("bhadra", "Bhadra", "Budha"),
    ("hamsa", "Hamsa", "Guru"),
    ("malavya", "Malavya", "Shukra"),
    ("shasha", "Shasha", "Shani"),
]


def _mahapurusha_rules(from_moon: bool = False) -> list[YogaRule]:
    rules = []
    for key, name, planet in MAHAPURUSHA:
        if from_moon:
            placement = C.planet_in_kendra_from_planet(planet, "Chandra")
            suffix, tradition = "_from_moon", "Parashari (kendra from Chandra)"
            note = ("Counted from the Moon. Authorities that reckon the "
                    "Mahapurusha kendra from the Lagna will not recognise this "
                    "as the same yoga.")
        else:
            placement = C.planet_in_houses(
                planet, KENDRA_HOUSES,
                label=f"{planet} occupies a kendra from the Lagna")
            suffix, tradition = "", "Parashari"
            note = ""

        rules.append(YogaRule(
            id=f"mahapurusha_{key}{suffix}",
            name=f"{name} Yoga (Pancha Mahapurusha)",
            category="mahapurusha",
            tradition=tradition,
            source="BPHS ch.75; Phaladeepika ch.6.1",
            explanation=(
                f"{planet} stands in its own rashi or in exaltation while "
                f"occupying a kendra"
                + (" from the Moon." if from_moon else " from the Lagna.")),
            conditions_all=[
                C.planet_dignity(
                    planet, ("own_sign", "exalted", "moolatrikona"),
                    label=f"{planet} in own rashi, moolatrikona or exaltation"),
                placement,
            ],
            cancellation_conditions=[
                C.custom(
                    f"{planet} is combust, which burns the Mahapurusha",
                    _combust_cancellation(planet)),
            ],
            strength_modifiers=standard_modifiers([planet]),
            planets_involved=[planet],
            variant_of=f"mahapurusha_{key}" if from_moon else None,
            notes=note,
        ))
    return rules


def _combust_cancellation(planet: str):
    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None or not found.combust:
            return ConditionResult(False, f"{planet} is not combust")
        return ConditionResult(
            True,
            f"{planet} is combust at {found.sun_separation:.2f}° from the Sun "
            f"(arc {found.combustion_orb:g}°), so the Mahapurusha cannot "
            f"deliver its results",
            planets=[planet])
    return test


# ── Budha-Aditya ─────────────────────────────────────────────────────────────
# Surya and Budha in one rashi. Because Budha never exceeds 28° elongation it
# shares the Sun's rashi very often, so the combination alone is unremarkable —
# what distinguishes a working Budha-Aditya from a routine one is whether Budha
# has escaped combustion. That is modelled as a cancellation, not hidden inside
# the formation condition, so the report shows both facts.

def _budha_aditya() -> YogaRule:
    return YogaRule(
        id="budha_aditya",
        name="Budha-Aditya Yoga",
        category="intellect",
        tradition="Parashari",
        source="BPHS ch.34; Phaladeepika ch.6.15",
        explanation="Budha and Surya occupy the same rashi.",
        conditions_all=[C.planets_conjunct("Surya", "Budha")],
        cancellation_conditions=[
            C.custom("Budha is combust", _combust_cancellation("Budha")),
        ],
        strength_modifiers=standard_modifiers(["Budha", "Surya"]),
        planets_involved=["Surya", "Budha"],
        notes=("Budha stays within 28° of the Sun, so this combination is "
               "common; combustion is what usually decides whether it operates."),
    )


# ── Chandra-Mangala ──────────────────────────────────────────────────────────

def _chandra_mangala() -> YogaRule:
    return YogaRule(
        id="chandra_mangala",
        name="Chandra-Mangala Yoga",
        category="dhana",
        tradition="Parashari",
        source="BPHS ch.40.9; Phaladeepika ch.6.17",
        explanation="Chandra and Mangal occupy the same rashi.",
        conditions_all=[C.planets_conjunct("Chandra", "Mangal")],
        strength_modifiers=standard_modifiers(["Chandra", "Mangal"]),
        planets_involved=["Chandra", "Mangal"],
        notes=("Some authorities extend this to mutual aspect; that is the "
               "`chandra_mangala_aspect` variant, not merged into this rule."),
    )


def _chandra_mangala_aspect() -> YogaRule:
    return YogaRule(
        id="chandra_mangala_aspect",
        name="Chandra-Mangala Yoga (mutual aspect variant)",
        category="dhana",
        tradition="Later commentators",
        source="Variant reading of BPHS ch.40.9",
        explanation="Chandra and Mangal aspect one another.",
        conditions_all=[
            C.custom("Chandra and Mangal in mutual aspect",
                     _mutual_aspect("Chandra", "Mangal")),
        ],
        strength_modifiers=standard_modifiers(["Chandra", "Mangal"]),
        planets_involved=["Chandra", "Mangal"],
        variant_of="chandra_mangala",
        notes="Recognised only by authorities that extend the rule past conjunction.",
    )


def _mutual_aspect(a: str, b: str):
    def test(features: ChartFeatures) -> ConditionResult:
        a_to_b = features.aspects_between(a, b)
        b_to_a = features.aspects_between(b, a)
        if a_to_b and b_to_a:
            return ConditionResult(
                True,
                f"{a} aspects {b} ({a_to_b[0].aspect_type}) and {b} aspects "
                f"{a} ({b_to_a[0].aspect_type})", planets=[a, b])
        return ConditionResult(False, f"{a} and {b} are not in mutual aspect",
                               planets=[a, b])
    return test


# ── Gajakesari ───────────────────────────────────────────────────────────────

def _gajakesari() -> YogaRule:
    return YogaRule(
        id="gajakesari",
        name="Gajakesari Yoga",
        category="raja",
        tradition="Parashari",
        source="BPHS ch.34; Phaladeepika ch.6.11",
        explanation="Guru occupies a kendra (1, 4, 7 or 10) from Chandra.",
        conditions_all=[C.planet_in_kendra_from_planet("Guru", "Chandra")],
        cancellation_conditions=[
            C.custom(
                "Guru is debilitated or combust",
                _any_cancellation(
                    "Guru",
                    lambda p: p.debilitated or p.combust,
                    "Guru is {state}, so the Gajakesari does not deliver")),
        ],
        strength_modifiers=standard_modifiers(["Guru", "Chandra"]),
        planets_involved=["Guru", "Chandra"],
        notes=("Phaladeepika additionally requires Guru to be free of "
               "debilitation and combustion; that requirement is applied here "
               "as a cancellation so both facts stay visible."),
    )


def _any_cancellation(planet: str, predicate, template: str):
    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None or not predicate(found):
            return ConditionResult(False, f"{planet} is neither debilitated nor combust")
        state = []
        if found.debilitated:
            state.append(f"debilitated in {found.sign_name}")
        if found.combust:
            state.append(f"combust at {found.sun_separation:.2f}° from the Sun")
        return ConditionResult(True, template.format(state=" and ".join(state)),
                               planets=[planet])
    return test


# ── Kemadruma and its bhanga ─────────────────────────────────────────────────
# Kemadruma forms when the Moon is isolated: no graha in the 2nd or 12th from
# it. The classical cancellations (Kemadruma Bhanga) are numerous, and the
# previous engine reported none of them. They are modelled here as explicit
# cancellation clauses so the report can show which bhanga applied.
#
# Surya is excluded from the 2nd/12th test, and the nodes with it. Authorities
# differ on the nodes; excluding them is the majority reading and is recorded
# in the rule's notes.

def _kemadruma_isolation():
    def test(features: ChartFeatures) -> ConditionResult:
        moon = features.planet("Chandra")
        if moon is None:
            return ConditionResult(False, "Chandra is not in the chart")
        neighbours = [(moon.sign + 1) % 12, (moon.sign - 1) % 12]
        companions = [
            name for name, planet in features.planets.items()
            if name not in ("Chandra", "Surya", "Rahu", "Ketu")
            and planet.sign in neighbours
        ]
        if companions:
            return ConditionResult(
                False,
                "the 2nd and 12th from Chandra are occupied by "
                + ", ".join(sorted(companions)),
                planets=sorted(companions))
        return ConditionResult(
            True,
            "no graha (other than Surya and the nodes) stands in the 2nd or "
            "12th from Chandra",
            planets=["Chandra"], houses=[moon.house])
    return test


def _bhanga_planet_in_kendra_from_lagna():
    def test(features: ChartFeatures) -> ConditionResult:
        found = [name for name, planet in features.planets.items()
                 if name not in ("Rahu", "Ketu") and planet.house in KENDRA_HOUSES]
        if not found:
            return ConditionResult(False, "no graha occupies a kendra from the Lagna")
        return ConditionResult(
            True,
            "Kemadruma Bhanga: " + ", ".join(sorted(found))
            + " occupy a kendra from the Lagna",
            planets=sorted(found))
    return test


def _bhanga_planet_in_kendra_from_moon():
    def test(features: ChartFeatures) -> ConditionResult:
        moon = features.planet("Chandra")
        if moon is None:
            return ConditionResult(False, "Chandra is not in the chart")
        found = []
        for name, planet in features.planets.items():
            if name in ("Chandra", "Rahu", "Ketu"):
                continue
            if features.house_distance(moon.house, planet.house) in KENDRA_HOUSES:
                found.append(name)
        if not found:
            return ConditionResult(False, "no graha occupies a kendra from Chandra")
        return ConditionResult(
            True,
            "Kemadruma Bhanga: " + ", ".join(sorted(found))
            + " occupy a kendra from Chandra",
            planets=sorted(found))
    return test


def _bhanga_moon_in_kendra_from_lagna():
    def test(features: ChartFeatures) -> ConditionResult:
        moon = features.planet("Chandra")
        if moon is None:
            return ConditionResult(False, "Chandra is not in the chart")
        if moon.house in KENDRA_HOUSES:
            return ConditionResult(
                True,
                f"Kemadruma Bhanga: Chandra itself occupies the "
                f"{_ordinal(moon.house)}, a kendra from the Lagna",
                planets=["Chandra"], houses=[moon.house])
        return ConditionResult(False, "Chandra does not occupy a kendra from the Lagna")
    return test


def _bhanga_moon_aspected_by_benefic():
    def test(features: ChartFeatures) -> ConditionResult:
        moon = features.planet("Chandra")
        if moon is None:
            return ConditionResult(False, "Chandra is not in the chart")
        benefics = [source for source in moon.aspecting_planets
                    if (features.planet(source) or moon).natural_benefic]
        if not benefics:
            return ConditionResult(False, "no natural benefic aspects Chandra")
        return ConditionResult(
            True,
            "Kemadruma Bhanga: Chandra receives the drishti of "
            + ", ".join(benefics),
            planets=benefics + ["Chandra"])
    return test


def _kemadruma() -> YogaRule:
    return YogaRule(
        id="kemadruma",
        name="Kemadruma Yoga",
        category="arishta",
        tradition="Parashari",
        source="BPHS ch.34.6; Phaladeepika ch.6.6",
        explanation=(
            "Chandra stands isolated: no graha occupies the 2nd or 12th rashi "
            "from it. Surya and the nodes are not counted as company."),
        conditions_all=[
            C.custom("Chandra is isolated in the 2nd and 12th from itself",
                     _kemadruma_isolation()),
        ],
        cancellation_conditions=[
            C.custom("A graha occupies a kendra from the Lagna",
                     _bhanga_planet_in_kendra_from_lagna()),
            C.custom("A graha occupies a kendra from Chandra",
                     _bhanga_planet_in_kendra_from_moon()),
            C.custom("Chandra occupies a kendra from the Lagna",
                     _bhanga_moon_in_kendra_from_lagna()),
            C.custom("Chandra receives a benefic drishti",
                     _bhanga_moon_aspected_by_benefic()),
        ],
        strength_modifiers=standard_modifiers(["Chandra"]),
        planets_involved=["Chandra"],
        notes=(
            "The bhanga clauses are drawn from BPHS ch.34.7 and Phaladeepika "
            "ch.6.6. They cancel Kemadruma rather than merely softening it, so "
            "a chart showing Kemadruma alongside any of them is reported as "
            "PRESENT_BUT_CANCELLED. The cancellations are common — an isolated "
            "Moon with no bhanga at all is rare."),
    )


# ── Neecha Bhanga ────────────────────────────────────────────────────────────
# Cancellation of debility. BPHS ch.75 gives several independent clauses; any
# one suffices. Modelled per debilitated graha, so a chart with two debilitated
# grahas produces two separate results.

def _neecha_bhanga_clauses(planet: str):
    """Returns (is_debilitated_condition, list_of_bhanga_conditions)."""

    def debilitated(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None:
            return ConditionResult(False, f"{planet} is not in the chart")
        if not found.debilitated:
            return ConditionResult(
                False, f"{planet} is not debilitated (it is in {found.sign_name})",
                planets=[planet])
        return ConditionResult(
            True, f"{planet} is debilitated in {found.sign_name}",
            planets=[planet], houses=[found.house])

    def dispositor_in_kendra(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None or not found.debilitated:
            return ConditionResult(False, "not applicable")
        lord = found.sign_lord
        lord_features = features.planet(lord)
        if lord_features is None:
            return ConditionResult(
                False, f"the dispositor {lord} is not in the chart")
        if lord_features.house in KENDRA_HOUSES:
            return ConditionResult(
                True,
                f"the dispositor {lord} occupies the {_ordinal(lord_features.house)}, "
                f"a kendra from the Lagna",
                planets=[lord], houses=[lord_features.house])
        return ConditionResult(
            False,
            f"the dispositor {lord} is in the {_ordinal(lord_features.house)}, not a kendra",
            planets=[lord])

    def exaltation_lord_in_kendra(features: ChartFeatures) -> ConditionResult:
        from ..features.dignity import exaltation_sign
        from ..features.lordships import lord_of_sign
        found = features.planet(planet)
        if found is None or not found.debilitated:
            return ConditionResult(False, "not applicable")
        ex_sign = exaltation_sign(planet)
        if ex_sign is None:
            return ConditionResult(
                False, f"{planet} has no assigned exaltation rashi")
        lord = lord_of_sign(ex_sign)
        lord_features = features.planet(lord)
        if lord_features is None:
            return ConditionResult(False, f"{lord} is not in the chart")
        if lord_features.house in KENDRA_HOUSES:
            return ConditionResult(
                True,
                f"{lord}, lord of {planet}'s exaltation rashi, occupies the "
                f"{_ordinal(lord_features.house)}, a kendra from the Lagna",
                planets=[lord], houses=[lord_features.house])
        return ConditionResult(
            False,
            f"{lord}, lord of the exaltation rashi, is in the "
            f"{_ordinal(lord_features.house)}, not a kendra", planets=[lord])

    def exchange_with_dispositor(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None or not found.debilitated:
            return ConditionResult(False, "not applicable")
        for swap in features.parivartanas:
            if planet in (swap.planet1, swap.planet2):
                return ConditionResult(
                    True,
                    f"{planet} is in an exchange: {swap.describe()}",
                    planets=[swap.planet1, swap.planet2])
        return ConditionResult(False, f"{planet} is in no exchange")

    def aspected_by_dispositor(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None or not found.debilitated:
            return ConditionResult(False, "not applicable")
        lord = found.sign_lord
        if lord in found.aspecting_planets:
            return ConditionResult(
                True, f"the dispositor {lord} aspects the debilitated {planet}",
                planets=[lord, planet])
        return ConditionResult(
            False, f"the dispositor {lord} does not aspect {planet}")

    def exalted_planet_in_same_house(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None or not found.debilitated:
            return ConditionResult(False, "not applicable")
        companions = [name for name in found.conjunct_planets
                      if (features.planet(name) or found).exalted]
        if companions:
            return ConditionResult(
                True,
                f"{', '.join(companions)} stands exalted in the same rashi as "
                f"the debilitated {planet}",
                planets=companions + [planet])
        return ConditionResult(
            False, f"no exalted graha shares {planet}'s rashi")

    bhangas = [
        C.custom("the dispositor of the debilitation rashi is in a kendra",
                 dispositor_in_kendra),
        C.custom("the lord of the exaltation rashi is in a kendra",
                 exaltation_lord_in_kendra),
        C.custom("the debilitated graha is in an exchange", exchange_with_dispositor),
        C.custom("the dispositor aspects the debilitated graha",
                 aspected_by_dispositor),
        C.custom("an exalted graha shares the same rashi",
                 exalted_planet_in_same_house),
    ]
    return C.custom(f"{planet} is debilitated", debilitated), bhangas


TARA_AND_LUMINARIES = ("Surya", "Chandra", "Mangal", "Budha", "Guru",
                       "Shukra", "Shani")


def _neecha_bhanga_rules() -> list[YogaRule]:
    rules = []
    for planet in TARA_AND_LUMINARIES:
        debilitated, bhangas = _neecha_bhanga_clauses(planet)
        rules.append(YogaRule(
            id=f"neecha_bhanga_{planet.lower()}",
            name=f"Neecha Bhanga ({planet})",
            category="cancellation",
            tradition="Parashari",
            source="BPHS ch.75; Phaladeepika ch.6.25",
            explanation=(
                f"{planet} is debilitated and at least one classical clause "
                f"cancels that debility."),
            conditions_all=[debilitated],
            conditions_any=bhangas,
            strength_modifiers=standard_modifiers([planet]),
            planets_involved=[planet],
            notes=("Any one clause suffices; BPHS states them as alternatives, "
                   "not as a set that must all hold."),
        ))
    return rules


def _neecha_bhanga_raja_yoga_rules() -> list[YogaRule]:
    """
    Neecha Bhanga RAJA Yoga is a stronger claim than Neecha Bhanga alone: the
    cancelled debility must also produce a rise in status. The requirement
    modelled here is that the debilitated graha, or the graha cancelling it,
    holds a kendra or trikona — not the previous engine's rule, which called
    any debilitated graha in a kendra a Raja Yoga outright.
    """
    rules = []
    for planet in TARA_AND_LUMINARIES:
        debilitated, bhangas = _neecha_bhanga_clauses(planet)

        def in_kendra_or_trikona(features: ChartFeatures, planet=planet) -> ConditionResult:
            found = features.planet(planet)
            if found is None:
                return ConditionResult(False, f"{planet} is not in the chart")
            good = KENDRA_HOUSES + TRIKONA_HOUSES
            if found.house in good:
                return ConditionResult(
                    True,
                    f"the debilitated {planet} occupies the {_ordinal(found.house)}, "
                    f"a kendra or trikona",
                    planets=[planet], houses=[found.house])
            lord = features.planet(found.sign_lord)
            if lord is not None and lord.house in good:
                return ConditionResult(
                    True,
                    f"the cancelling dispositor {found.sign_lord} occupies the "
                    f"{_ordinal(lord.house)}, a kendra or trikona",
                    planets=[found.sign_lord], houses=[lord.house])
            return ConditionResult(
                False,
                f"neither {planet} nor its dispositor holds a kendra or trikona",
                planets=[planet])

        rules.append(YogaRule(
            id=f"neecha_bhanga_raja_{planet.lower()}",
            name=f"Neecha Bhanga Raja Yoga ({planet})",
            category="raja",
            tradition="Parashari",
            source="BPHS ch.75 read with ch.36; Phaladeepika ch.6.25",
            explanation=(
                f"{planet}'s debility is cancelled AND the combination falls "
                f"on a kendra or trikona, which is what raises it to a Raja "
                f"Yoga rather than a simple cancellation."),
            conditions_all=[
                debilitated,
                C.custom("the debilitated graha or its dispositor holds a "
                         "kendra or trikona", in_kendra_or_trikona),
                C.any_of(bhangas, "at least one neecha bhanga clause holds"),
            ],
            strength_modifiers=standard_modifiers([planet]),
            planets_involved=[planet],
            notes=("Distinct from plain Neecha Bhanga: cancellation alone "
                   "restores the graha, it does not by itself confer rajayoga."),
        ))
    return rules


# ── Raja Yogas: kendra lord with trikona lord ────────────────────────────────

_RELATION_MODES = {
    "conjunction": ("conjunction",),
    "mutual_aspect": ("mutual_aspect",),
    "exchange": ("exchange",),
}

_MODE_LABELS = {
    "conjunction": "conjunction",
    "mutual_aspect": "mutual aspect",
    "exchange": "exchange of rashis",
}


def _raja_yoga_rules() -> list[YogaRule]:
    """
    One rule per (kendra house, trikona house, mode of relationship).

    The 1st house is both a kendra and a trikona, so a pair is skipped when the
    two houses are the same. Pairs where a single graha owns both houses are
    not skipped at the catalog level — the condition reports that case with its
    own explanation, which is more informative than the rule silently vanishing.
    """
    rules = []
    for kendra in KENDRA_HOUSES:
        for trikona in TRIKONA_HOUSES:
            if kendra == trikona:
                continue
            for mode, modes in _RELATION_MODES.items():
                rules.append(YogaRule(
                    id=f"raja_yoga_k{kendra}_t{trikona}_{mode}",
                    name=(f"Raja Yoga — {_ordinal(kendra)} lord with "
                          f"{_ordinal(trikona)} lord ({_MODE_LABELS[mode]})"),
                    category="raja",
                    tradition="Parashari",
                    source="BPHS ch.36 (Raja Yoga Adhyaya)",
                    explanation=(
                        f"The lord of the {_ordinal(kendra)}, a kendra, forms a "
                        f"{_MODE_LABELS[mode]} with the lord of the "
                        f"{_ordinal(trikona)}, a trikona."),
                    conditions_all=[C.lords_related(kendra, trikona, modes)],
                    strength_modifiers=lords_modifiers([kendra, trikona]),
                    houses_involved=[kendra, trikona],
                ))
    return rules


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


# ── Dharma-Karmadhipati ──────────────────────────────────────────────────────
# The 9th (dharma) and 10th (karma) lords in relationship. This is a specific,
# named Raja Yoga and is modelled separately from the generated pairs above,
# because the 10th is a kendra and the 9th a trikona but the combination has
# its own name and its own literature.

def _dharma_karmadhipati_rules() -> list[YogaRule]:
    rules = []
    for mode, modes in _RELATION_MODES.items():
        rules.append(YogaRule(
            id=f"dharma_karmadhipati_{mode}",
            name=f"Dharma-Karmadhipati Yoga ({_MODE_LABELS[mode]})",
            category="raja",
            tradition="Parashari",
            source="BPHS ch.36; Phaladeepika ch.6.36",
            explanation=(
                f"The 9th lord (dharma) and the 10th lord (karma) form a "
                f"{_MODE_LABELS[mode]}."),
            conditions_all=[C.lords_related(9, 10, modes)],
            strength_modifiers=lords_modifiers([9, 10]),
            houses_involved=[9, 10],
            notes=("Held by many authorities to be the strongest of the Raja "
                   "Yogas, because it joins fortune to action."),
        ))
    return rules


# ── Dhana Yogas ──────────────────────────────────────────────────────────────
# BPHS ch.40 states wealth combinations as relationships among the lords of the
# 1st, 2nd, 5th, 9th and 11th. Each pair and each mode is a separate rule.

DHANA_HOUSES = (1, 2, 5, 9, 11)

_DHANA_HOUSE_NAMES = {
    1: "the Lagna (the native's own capacity)",
    2: "the 2nd (accumulated wealth)",
    5: "the 5th (purva punya)",
    9: "the 9th (fortune)",
    11: "the 11th (gains)",
}


def _dhana_yoga_rules() -> list[YogaRule]:
    rules = []
    for i, first in enumerate(DHANA_HOUSES):
        for second in DHANA_HOUSES[i + 1:]:
            for mode, modes in _RELATION_MODES.items():
                rules.append(YogaRule(
                    id=f"dhana_yoga_h{first}_h{second}_{mode}",
                    name=(f"Dhana Yoga — {_ordinal(first)} lord with "
                          f"{_ordinal(second)} lord ({_MODE_LABELS[mode]})"),
                    category="dhana",
                    tradition="Parashari",
                    source="BPHS ch.40 (Dhana Yoga Adhyaya)",
                    explanation=(
                        f"The lord of {_DHANA_HOUSE_NAMES[first]} forms a "
                        f"{_MODE_LABELS[mode]} with the lord of "
                        f"{_DHANA_HOUSE_NAMES[second]}."),
                    conditions_all=[C.lords_related(first, second, modes)],
                    strength_modifiers=lords_modifiers([first, second]),
                    houses_involved=[first, second],
                ))

    # The classical placement form: 2nd lord in the 11th and 11th lord in the
    # 2nd is stated directly in BPHS and is not merely an exchange.
    rules.append(YogaRule(
        id="dhana_yoga_2_11_placement",
        name="Dhana Yoga — 2nd lord in the 11th and 11th lord in the 2nd",
        category="dhana",
        tradition="Parashari",
        source="BPHS ch.40.4",
        explanation=("The lord of the 2nd occupies the 11th while the lord of "
                     "the 11th occupies the 2nd."),
        conditions_all=[
            C.lord_of_house_in_houses(2, [11]),
            C.lord_of_house_in_houses(11, [2]),
        ],
        strength_modifiers=lords_modifiers([2, 11]),
        houses_involved=[2, 11],
    ))
    return rules


# ── Profiles ─────────────────────────────────────────────────────────────────

def _core_rules() -> list[YogaRule]:
    from .catalog_extended import extended_core_rules
    return extended_core_rules() + (
        _mahapurusha_rules(from_moon=False)
        + [_budha_aditya(), _chandra_mangala(), _gajakesari(), _kemadruma()]
        + _neecha_bhanga_rules()
        + _neecha_bhanga_raja_yoga_rules()
        + _raja_yoga_rules()
        + _dharma_karmadhipati_rules()
        + _dhana_yoga_rules()
    )


def _variant_rules() -> list[YogaRule]:
    """Readings held by some authorities but not by the Parashari mainstream."""
    from .catalog_extended import extended_variant_rules
    return (_mahapurusha_rules(from_moon=True) + [_chandra_mangala_aspect()]
            + extended_variant_rules())


RULE_PROFILES: dict[str, str] = {
    "parashari": (
        "The full mainstream catalog. Most rules here are UNVERIFIED against "
        "any text — see engine/sources/ — but are in common traditional use."),
    "parashari_extended": (
        "The mainstream catalog plus variant readings held by later "
        "authorities (Mahapurusha reckoned from the Moon, Chandra-Mangala by "
        "aspect, and others). Variants carry `variant_of` so they are never "
        "confused with the combination they extend."),
    "parashari_vipareeta_strict": (
        "The mainstream catalog with the strict reading of Vipareeta Raja "
        "Yoga, which requires a dusthana lord to fall into a DIFFERENT "
        "dusthana rather than its own. 'Strict' here refers to that ONE "
        "reading, not to evidence — this was what `parashari_strict` meant "
        "in V1.2, renamed in V1.3 so the word could be freed for the "
        "evidence-gated profile."),
    "parashari_textual": (
        "The mainstream catalog with the V1.5 located readings substituted "
        "for the rules the audit found diverging from their witnesses. "
        "Smaller and stricter than `parashari`, not larger: the Raja Yogas "
        "carry the BPHS 34.15 exception and require full aspect, Gajakesari "
        "requires Jupiter unafflicted, the Mahapurusha yogas require the "
        "strength both witnesses state, and the Moon yogas stop excluding the "
        "nodes. Every substitution is recorded in RULE_AUDIT_V15.md."),
    "parashari_strict": (
        "EVIDENCE-GATED. Contains only rules that meet a documented minimum "
        "standard of textual provenance: a Sanskrit-tier witness with an "
        "edition and a passage locator, a written textual condition, a "
        "written software condition mapped to it, a named implementation "
        "test, and no registered conflict saying the implementation diverges "
        "from the witness. "
        "It is deliberately very small. That is the finding, not a defect."),
}

DEFAULT_PROFILE = "parashari"

# The profile whose membership is decided by evidence rather than by content.
EVIDENCE_GATED_PROFILE = "parashari_strict"

# The profile whose CONTENT is decided by the V1.5 audit.
TEXTUAL_PROFILE = "parashari_textual"


def rules_for_profile(profile: str = DEFAULT_PROFILE) -> list[YogaRule]:
    if profile not in RULE_PROFILES:
        raise ValueError(
            f"Unknown rule profile '{profile}'. "
            f"Available: {', '.join(sorted(RULE_PROFILES))}")
    rules = _core_rules()
    if profile == "parashari_extended":
        rules = rules + _variant_rules()
    elif profile == "parashari_vipareeta_strict":
        from .catalog_extended import _VIPAREETA, _vipareeta_rules
        # Swap the permissive Vipareeta rules for the strict ones rather than
        # reporting both, which would double-count the same combination.
        permissive = {f"vipareeta_{key}" for key, _name, _house, _gloss
                      in _VIPAREETA}
        rules = [rule for rule in rules if rule.id not in permissive]
        rules = rules + _vipareeta_rules(different_house_only=True)
    elif profile == TEXTUAL_PROFILE:
        from .catalog_textual import SUPERSEDED_BY_TEXTUAL, textual_rules
        # Drop the superseded rule rather than reporting both readings of one
        # combination, which would present a single fact twice and let a
        # reader count it twice.
        rules = [rule for rule in rules
                 if rule.id not in SUPERSEDED_BY_TEXTUAL]
        rules = rules + textual_rules()
    elif profile == EVIDENCE_GATED_PROFILE:
        rules = [rule for rule in _strict_candidates()
                 if strict_profile_admits(rule.id)]
    return rules


def _strict_candidates() -> list[YogaRule]:
    """
    Everything the evidence gate is allowed to consider.

    The V1.5 textual rules are included, and that is what changes this
    profile from a curiosity into something usable: they were written from
    located witnesses, so they are the rules most likely to clear the gate.
    Their divergent counterparts are considered too and simply fail, which is
    better than excluding them by hand — the gate should be seen rejecting
    them.
    """
    from .catalog_textual import textual_rules
    return _core_rules() + _variant_rules() + textual_rules()


def strict_profile_admits(rule_id: str) -> bool:
    """
    Whether a rule meets the evidence threshold for `parashari_strict`.

    The gate is the source registry, not a hand-maintained list, so a rule
    cannot be admitted by editing the catalog — only by producing evidence.
    """
    from ..sources import evidence_for, strict_profile_eligible, witnesses_for
    eligible, _reasons = strict_profile_eligible(
        evidence_for(rule_id), witnesses_for(rule_id))
    return eligible


def strict_profile_rejections() -> dict[str, list[str]]:
    """Every rule kept out of the strict profile, and why."""
    from ..sources import evidence_for, strict_profile_eligible, witnesses_for
    rejected: dict[str, list[str]] = {}
    for rule in _strict_candidates():
        eligible, reasons = strict_profile_eligible(
            evidence_for(rule.id), witnesses_for(rule.id))
        if not eligible:
            rejected[rule.id] = reasons
    return rejected


def all_rules() -> list[YogaRule]:
    return rules_for_profile(DEFAULT_PROFILE)


def rule_by_id(rule_id: str, profile: str = DEFAULT_PROFILE) -> Optional[YogaRule]:
    for rule in rules_for_profile(profile):
        if rule.id == rule_id:
            return rule
    return None
