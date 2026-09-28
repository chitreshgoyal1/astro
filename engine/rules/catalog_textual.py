"""
The located readings (V1.5 Parts 1, 2, 5)
------------------------------------------
Rules written to match the Sanskrit witnesses obtained in V1.5, for the cases
where the audit found that the shipped rule does not.

WHY THESE ARE NEW RULES AND NOT EDITS

    Part 2 says never to edit yoga logic silently, and Part 1 says that where
    witnesses disagree the answer is separate profiles rather than one blended
    definition. Both point the same way: the V1.1 rule stays exactly as it is,
    the located reading arrives beside it with its own id, and a chart can be
    run under either and compared.

    The practical consequence is that no V1.4 result changes in this release.
    Every difference the audit found is visible as a difference between two
    profiles rather than as a diff in a file nobody re-runs.

WHAT "TEXTUAL" MEANS HERE, AND WHAT IT DOES NOT

    It means: this rule was written by reading a specific verse in a specific
    checksummed witness, and its evidence record says which.

    It does NOT mean the rule is right, and it does not mean the text has been
    correctly understood. Several of these rules rest on a reading of a
    compound that a Sanskritist might overturn — `balibhiḥ` is the obvious
    one, where the engine has decided that "strong" means "Shadbala at or
    above the BPHS 27.32 requirement" and no text says that. Those decisions
    are in the review queue, not hidden in the code.

    Nor is this profile a superset of correctness. `parashari_textual`
    contains fewer rules than `parashari`, because a located reading that
    narrows a rule is still a narrowing: Gajakesari fires less often here, and
    the Raja Yogas fire a great deal less often.
"""

from __future__ import annotations

from typing import Optional, Sequence

from ..features.models import ChartFeatures
from . import conditions as C
from .conditions import Condition, ConditionResult
from .engine import YogaRule
from .modifiers import lords_modifiers, standard_modifiers

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)
DUSTHANA_HOUSES = (6, 8, 12)

TEXTUAL_PROFILE = "parashari_textual"

# The five tara grahas plus the nodes. The Moon yogas' witnesses exclude the
# Sun and nothing else, so the nodes belong in the list of grahas that can
# keep the Moon company — which is the whole point of these three rules.
_ALL_BUT_LUMINARIES = ("Mangal", "Budha", "Guru", "Shukra", "Shani",
                       "Rahu", "Ketu")


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


# ── Moon yogas: BPHS 37.7 and Bṛhajjātaka 13.3 ───────────────────────────────
# Both witnesses exclude the Sun and only the Sun. The engine's default rules
# also exclude Rahu and Ketu, which no witness supports.

def _occupants_at_distance(features: ChartFeatures, distance: int
                           ) -> list[str]:
    moon = features.planet("Chandra")
    if moon is None:
        return []
    house = ((moon.house - 1 + distance - 1) % 12) + 1
    return [name for name in features.occupants_of(house)
            if name in _ALL_BUT_LUMINARIES]


def _company_condition(distances: Sequence[int], label: str) -> Condition:
    distances = tuple(distances)

    def test(features: ChartFeatures) -> ConditionResult:
        if features.planet("Chandra") is None:
            return ConditionResult(False, "Chandra is not in the chart")
        found = {d: _occupants_at_distance(features, d) for d in distances}
        if all(found[d] for d in distances):
            parts = [f"{', '.join(found[d])} in the {_ordinal(d)} from Chandra"
                     for d in distances]
            planets = [p for d in distances for p in found[d]]
            return ConditionResult(True, "; ".join(parts), planets=planets)
        empty = [d for d in distances if not found[d]]
        return ConditionResult(
            False,
            "nothing but the Sun in the "
            + " and the ".join(_ordinal(d) for d in empty)
            + " from Chandra")

    return Condition(label, test)


def _moon_yoga_rules() -> list[YogaRule]:
    shared_source = ("BPHS(Sanskrit/SD) 37.7; Bṛhajjātaka 13.3 "
                     "[witnesses BPHS_SA_37.7_CANDRA_YOGAS, "
                     "BJ_13.3_CANDRA_YOGAS]")
    shared_note = (
        "Differs from the default rule of the same name in one respect: Rahu "
        "and Ketu count as company. Neither witness excludes them — BJ 13.3 "
        "says hitvārkaṃ and BPHS 37.7 says sūryaṃ binā, and both mean the Sun "
        "alone. The node exclusion in the default rule has no located source.")
    specs = (
        ("sunapha", "Sunapha", (2,), "the 2nd from Chandra"),
        ("anapha", "Anapha", (12,), "the 12th from Chandra"),
        ("durudhara", "Durudhara", (2, 12),
         "both the 2nd and the 12th from Chandra"),
    )
    rules = []
    for key, name, distances, gloss in specs:
        rules.append(YogaRule(
            id=f"{key}_textual",
            name=f"{name} Yoga (located reading)",
            category="chandra",
            tradition="Parashari (BPHS 37.7 / BJ 13.3 as located)",
            source=shared_source,
            explanation=(
                f"A graha other than the Sun occupies {gloss}."),
            conditions_all=[_company_condition(
                distances, f"a graha other than Surya in {gloss}")],
            strength_modifiers=standard_modifiers(["Chandra"]),
            planets_involved=["Chandra"],
            variant_of=key,
            notes=shared_note,
        ))
    return rules


# ── Kemadruma: BPHS 37.11-12 ─────────────────────────────────────────────────

def _kemadruma_textual_isolation() -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        moon = features.planet("Chandra")
        if moon is None:
            return ConditionResult(False, "Chandra is not in the chart")
        # BPHS 37.11 counts the 1st from the Moon as well as the 2nd and the
        # 12th, so a graha merely conjunct the Moon prevents Kemadruma.
        occupied = {d: _occupants_at_distance(features, d) for d in (1, 2, 12)}
        keeping_company = [p for names in occupied.values() for p in names]
        if keeping_company:
            return ConditionResult(
                False,
                f"Chandra has company: {', '.join(sorted(set(keeping_company)))}",
                planets=sorted(set(keeping_company)))
        return ConditionResult(
            True,
            "no graha other than Surya occupies the 1st, 2nd or 12th from "
            "Chandra",
            planets=["Chandra"], houses=[moon.house])

    return Condition(
        "no graha but Surya in the 1st, 2nd or 12th from Chandra", test)


def _kemadruma_textual_bhanga() -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        # "vinā candraṃ" — the Moon itself is expressly NOT one of the grahas
        # whose kendra placement cancels. The default rule's
        # `kemadruma_bhanga_moon_kendra` clause asserts the opposite.
        found = []
        for house in KENDRA_HOUSES:
            for name in features.occupants_of(house):
                if name != "Chandra":
                    found.append(f"{name} in the {_ordinal(house)}")
        if found:
            return ConditionResult(
                True,
                "a graha other than Chandra occupies a kendra from the Lagna: "
                + ", ".join(found))
        return ConditionResult(
            False, "no graha other than Chandra occupies a kendra from the Lagna")

    return Condition(
        "a graha other than Chandra occupies a kendra from the Lagna", test)


def _kemadruma_textual() -> YogaRule:
    return YogaRule(
        id="kemadruma_textual",
        name="Kemadruma Yoga (located reading)",
        category="arishta",
        tradition="Parashari (BPHS 37.11 as located)",
        source=("BPHS(Sanskrit/SD) 37.11-12 "
                "[witness BPHS_SA_37.11_KEMADRUMA]"),
        explanation=(
            "No graha other than Surya occupies the 1st, 2nd or 12th from "
            "Chandra, and no graha other than Chandra occupies a kendra from "
            "the Lagna."),
        conditions_all=[_kemadruma_textual_isolation()],
        cancellation_conditions=[_kemadruma_textual_bhanga()],
        strength_modifiers=standard_modifiers(["Chandra"]),
        planets_involved=["Chandra"],
        variant_of="kemadruma",
        notes=(
            "Two cancellation clauses in the default rule are dropped here "
            "and one is reversed. Dropped: a graha in a kendra from the MOON, "
            "and a benefic aspect on the Moon — neither is in any located "
            "witness. Reversed: the default cancels when the Moon itself "
            "occupies a kendra from the Lagna, and BPHS 37.11 explicitly "
            "excludes the Moon from the grahas that count, vinā candraṃ. "
            "Bṛhajjātaka 13.3, quoted at Jātaka Pārijāta 83, reports the "
            "wider kendra/navāṃśa opinion and dismisses it as "
            "ukti-prasiddhā na te."),
    )


# ── Pañca Mahāpuruṣa: BPHS 75.1 and Jātaka Pārijāta 59 ───────────────────────

MAHAPURUSHA = (
    ("ruchaka", "Ruchaka", "Mangal"),
    ("bhadra", "Bhadra", "Budha"),
    ("hamsa", "Hamsa", "Guru"),
    ("malavya", "Malavya", "Shukra"),
    ("shasha", "Shasha", "Shani"),
)

# SOFTWARE INTERPRETATION, flagged as one.
#
# Both witnesses require the graha to be strong — balibhiḥ at BPHS 75.1,
# baliṣṭhāḥ at JP 59 — and neither says by what measure. The engine reads it
# as Shadbala reaching the requirement BPHS 27.32-33 states for that graha,
# which is at least a measure from the same tradition and is computable. It
# is still a choice the texts did not make, and it is in the review queue.
MAHAPURUSHA_STRENGTH_RATIO = 1.0


def _is_strong(planet: str) -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        ratio = features.shadbala_ratio(planet)
        if ratio is None:
            # FAIL CLOSED. The witnesses make strength part of the formation
            # condition, so a chart where strength was never computed is a
            # chart where the yoga has not been shown to form. Reporting it
            # as present would drop the very clause this rule exists to add.
            return ConditionResult(
                False,
                f"{planet}'s Shadbala was not computed, so the strength "
                f"required by BPHS 75.1 (balibhiḥ) cannot be established",
                planets=[planet])
        met = ratio >= MAHAPURUSHA_STRENGTH_RATIO
        return ConditionResult(
            met,
            f"{planet}'s Shadbala is {ratio:.2f}x its BPHS 27.32 requirement "
            f"({'at or above' if met else 'below'} the "
            f"{MAHAPURUSHA_STRENGTH_RATIO:g}x the engine reads as balibhiḥ)",
            planets=[planet])

    return Condition(f"{planet} is strong (balibhiḥ)", test)


def _mahapurusha_textual_rules() -> list[YogaRule]:
    rules = []
    for key, name, planet in MAHAPURUSHA:
        rules.append(YogaRule(
            id=f"mahapurusha_{key}_textual",
            name=f"{name} Yoga (located reading)",
            category="mahapurusha",
            tradition="Parashari (BPHS 75.1 / JP 59 as located)",
            source=("BPHS(Sanskrit/SD) 75.1-2; Jātaka Pārijāta(SD) v.59 "
                    "[witnesses BPHS_SA_75.1_MAHAPURUSHA, JP_59_MAHAPURUSHA]"),
            explanation=(
                f"{planet} stands in own rashi, moolatrikona or exaltation, "
                f"occupies a kendra from the Lagna, and is strong."),
            conditions_all=[
                C.planet_dignity(
                    planet, ("own_sign", "exalted", "moolatrikona"),
                    label=f"{planet} in own rashi, moolatrikona or exaltation"),
                C.planet_in_houses(
                    planet, KENDRA_HOUSES,
                    label=f"{planet} occupies a kendra from the Lagna"),
                _is_strong(planet),
            ],
            strength_modifiers=standard_modifiers([planet]),
            planets_involved=[planet],
            variant_of=f"mahapurusha_{key}",
            notes=(
                "Adds the strength clause both witnesses state and the "
                "default rule omits. Drops the default's combustion "
                "cancellation, which neither witness gives here — though a "
                "combust graha will usually fail the strength clause anyway, "
                "since combustion costs Chesta and Ayana Bala. The dignity "
                "set follows Jātaka Pārijāta, which includes moolatrikona; "
                "BPHS 75.1 gives only own sign and exaltation."),
        ))
    return rules


# ── Gajakesari: BPHS 36.3 and Jātaka Pārijāta 116 ────────────────────────────

def _guru_unafflicted(include_enemy_sign: bool) -> Condition:
    wanted = "debilitation, combustion or an enemy sign" if include_enemy_sign \
        else "debilitation or combustion"

    def test(features: ChartFeatures) -> ConditionResult:
        guru = features.planet("Guru")
        if guru is None:
            return ConditionResult(False, "Guru is not in the chart")
        faults = []
        if guru.debilitated:
            faults.append(f"debilitated in {guru.sign_name}")
        if guru.combust:
            faults.append("combust")
        if include_enemy_sign and guru.enemy_sign:
            faults.append(f"in the enemy sign {guru.sign_name}")
        if faults:
            return ConditionResult(
                False, "Guru is " + " and ".join(faults), planets=["Guru"])
        return ConditionResult(
            True, f"Guru is free of {wanted}", planets=["Guru"])

    return Condition(f"Guru free of {wanted}", test)


def _guru_with_benefics() -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        guru = features.planet("Guru")
        if guru is None:
            return ConditionResult(False, "Guru is not in the chart")
        companions = [p for p in guru.conjunct_planets
                      if (features.planet(p) or guru).natural_benefic]
        aspecting = [p for p in guru.aspecting_planets
                     if (features.planet(p) or guru).natural_benefic]
        if companions or aspecting:
            parts = []
            if companions:
                parts.append("conjoined with " + ", ".join(sorted(companions)))
            if aspecting:
                parts.append("aspected by " + ", ".join(sorted(aspecting)))
            return ConditionResult(
                True, "Guru is " + " and ".join(parts),
                planets=["Guru"] + sorted(set(companions + aspecting)))
        return ConditionResult(
            False, "no benefic is conjoined with or aspects Guru",
            planets=["Guru"])

    return Condition("Guru conjoined with or aspected by a benefic", test)


def _guru_in_kendra_from_lagna_or_moon() -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        guru = features.planet("Guru")
        moon = features.planet("Chandra")
        if guru is None:
            return ConditionResult(False, "Guru is not in the chart")
        from_lagna = guru.house in KENDRA_HOUSES
        distance = (None if moon is None
                    else features.house_distance(moon.house, guru.house))
        from_moon = distance in (1, 4, 7, 10)
        if from_lagna or from_moon:
            where = []
            if from_lagna:
                where.append(f"the {_ordinal(guru.house)} from the Lagna")
            if from_moon:
                where.append(f"the {_ordinal(distance)} from Chandra")
            return ConditionResult(
                True, "Guru occupies a kendra — " + " and ".join(where),
                planets=["Guru"], houses=[guru.house])
        return ConditionResult(
            False,
            f"Guru is in the {_ordinal(guru.house)} from the Lagna and the "
            f"{_ordinal(distance)} from Chandra, neither a kendra",
            planets=["Guru"], houses=[guru.house])

    return Condition("Guru in a kendra from the Lagna or from Chandra", test)


def _gajakesari_textual_rules() -> list[YogaRule]:
    return [
        YogaRule(
            id="gajakesari_textual_bphs",
            name="Gajakesari Yoga (BPHS 36.3 reading)",
            category="raja",
            tradition="Parashari (BPHS 36.3 as located)",
            source=("BPHS(Sanskrit/SD) 36.3 "
                    "[witness BPHS_SA_36.3_GAJAKESARI]"),
            explanation=(
                "Guru occupies a kendra from the Lagna or from Chandra, is "
                "conjoined with or aspected by benefics, and is free of "
                "debilitation, combustion and enemy signs."),
            conditions_all=[
                _guru_in_kendra_from_lagna_or_moon(),
                _guru_with_benefics(),
                _guru_unafflicted(include_enemy_sign=True),
            ],
            strength_modifiers=standard_modifiers(["Guru", "Chandra"]),
            planets_involved=["Guru", "Chandra"],
            variant_of="gajakesari",
            notes=(
                "The verse allows the Lagna as a reference point, which "
                "Jātaka Pārijāta 116 does not; see "
                "`gajakesari_textual_jataka_parijata` for that reading. Both "
                "add the affliction conditions the default rule lacks."),
        ),
        YogaRule(
            id="gajakesari_textual_jataka_parijata",
            name="Gajakesari Yoga (Jataka Parijata 116 reading)",
            category="raja",
            tradition="Vaidyanātha Dīkṣita (JP 116 as located)",
            source="Jātaka Pārijāta(SD) v.116 [witness JP_116_GAJAKESARI]",
            explanation=(
                "Guru occupies a kendra from Chandra and is free of "
                "debilitation and combustion."),
            conditions_all=[
                C.planet_in_kendra_from_planet("Guru", "Chandra"),
                _guru_unafflicted(include_enemy_sign=False),
            ],
            strength_modifiers=standard_modifiers(["Guru", "Chandra"]),
            planets_involved=["Guru", "Chandra"],
            variant_of="gajakesari",
            notes=(
                "Counted from the Moon only, and without the benefic "
                "association BPHS requires. The two witnesses disagree on "
                "both points, so both rules ship and neither is blended into "
                "the other."),
        ),
    ]


# ── Raja Yoga: BPHS 34.11-15 and 41.28 ───────────────────────────────────────

def _lords_related_full(house_a: int, house_b: int, mode: str) -> Condition:
    """
    Sambandha restricted to what BPHS 34.11-12 actually enumerates.

    The difference from `conditions.lords_related` is the aspect mode: the
    verse says pūrṇa-dṛṣṭyā, full aspect, and the engine's default accepts any
    graha drishti including the partial special aspects. A Saturn third-house
    aspect at quarter strength is a drishti and is not a pūrṇa-dṛṣṭi.
    """
    def test(features: ChartFeatures) -> ConditionResult:
        lord_a = features.lord_of(house_a)
        lord_b = features.lord_of(house_b)
        if not lord_a or not lord_b:
            return ConditionResult(False, "a required house lord is absent")
        if lord_a == lord_b:
            return ConditionResult(
                False,
                f"the {_ordinal(house_a)} and {_ordinal(house_b)} share one "
                f"lord ({lord_a}); BPHS 34.13 treats that as a yogakaraka in "
                f"its own right, not as a relationship between two grahas",
                planets=[lord_a], houses=[house_a, house_b])

        if mode == "conjunction":
            for conj in features.conjunctions:
                if conj.same_sign and {conj.planet1, conj.planet2} == {lord_a,
                                                                       lord_b}:
                    return ConditionResult(
                        True,
                        f"{lord_a} and {lord_b} share one rashi in house "
                        f"{conj.house}",
                        planets=[lord_a, lord_b], houses=[house_a, house_b],
                        detail="conjunction")
        elif mode == "full_mutual_aspect":
            a_to_b = [a for a in features.aspects_between(lord_a, lord_b)
                      if a.full]
            b_to_a = [a for a in features.aspects_between(lord_b, lord_a)
                      if a.full]
            if a_to_b and b_to_a:
                return ConditionResult(
                    True,
                    f"{lord_a} and {lord_b} aspect one another with full "
                    f"drishti ({a_to_b[0].aspect_type} / "
                    f"{b_to_a[0].aspect_type})",
                    planets=[lord_a, lord_b], houses=[house_a, house_b],
                    detail="full_mutual_aspect")
        elif mode == "exchange":
            for swap in features.parivartanas:
                if {swap.planet1, swap.planet2} == {lord_a, lord_b}:
                    return ConditionResult(
                        True,
                        f"{lord_a} and {lord_b} exchange rashis "
                        f"({swap.category})",
                        planets=[lord_a, lord_b], houses=[house_a, house_b],
                        detail="exchange")

        return ConditionResult(
            False,
            f"no {mode.replace('_', ' ')} between the {_ordinal(house_a)} lord "
            f"{lord_a} and the {_ordinal(house_b)} lord {lord_b}",
            planets=[lord_a, lord_b], houses=[house_a, house_b])

    return Condition(
        f"lords of the {_ordinal(house_a)} and {_ordinal(house_b)} related by "
        f"{mode.replace('_', ' ')}",
        test)


def _dusthana_ownership_cancellation(house_a: int, house_b: int) -> Condition:
    """
    BPHS 34.15, the exception the default rules do not implement.

    `kendrakoṇādhipāv eva pāpasthānādhipau yadā | tayoḥ sambandhamātreṇa na
    yogaṃ labhate naraḥ` — when the kendra and trikoṇa lords are ALSO lords of
    the evil houses, the native does not obtain the yoga by their mere
    relationship.

    The engine implements the wide reading: any dusthana ownership by either
    lord cancels. Whether the verse means that, or only that a lord whose
    dusthana ownership DOMINATES cannot give the yoga, is a question for a
    human and is in the review queue. The wide reading suppresses a great many
    Raja Yogas — which is the point of running this profile beside the
    default rather than instead of it.
    """
    def test(features: ChartFeatures) -> ConditionResult:
        lord_a = features.lord_of(house_a)
        lord_b = features.lord_of(house_b)
        offending = []
        for lord, owned_house in ((lord_a, house_a), (lord_b, house_b)):
            if not lord:
                continue
            dusthanas = [h for h in features.houses_owned_by(lord)
                         if h in DUSTHANA_HOUSES]
            if dusthanas:
                offending.append(
                    f"{lord} (lord of the {_ordinal(owned_house)}) also owns "
                    f"the {', '.join(_ordinal(h) for h in sorted(dusthanas))}")
        if offending:
            return ConditionResult(
                True,
                "BPHS 34.15: " + "; ".join(offending)
                + " — the relationship alone does not give the yoga",
                planets=[p for p in (lord_a, lord_b) if p],
                houses=[house_a, house_b])
        return ConditionResult(
            False, "neither lord also owns a dusthana")

    return Condition(
        "BPHS 34.15 exception: a participating lord also owns a dusthana",
        test)


_TEXTUAL_MODES = {
    "conjunction": "conjunction",
    "full_mutual_aspect": "full mutual aspect",
    "exchange": "exchange of rashis",
}


def _raja_yoga_textual_rules() -> list[YogaRule]:
    rules = []
    for kendra in KENDRA_HOUSES:
        for trikona in TRIKONA_HOUSES:
            if kendra == trikona:
                continue
            for mode, label in _TEXTUAL_MODES.items():
                rules.append(YogaRule(
                    id=f"raja_yoga_k{kendra}_t{trikona}_{mode}_textual",
                    name=(f"Raja Yoga — {_ordinal(kendra)} lord with "
                          f"{_ordinal(trikona)} lord ({label}, located "
                          f"reading)"),
                    category="raja",
                    tradition="Parashari (BPHS 34.11-15 / 41.28 as located)",
                    source=("BPHS(Sanskrit/SD) 34.11-15, 41.28 "
                            "[witnesses BPHS_SA_34.11-15_YOGAKARAKA, "
                            "BPHS_SA_41.28_KENDRA_TRIKONA]"),
                    explanation=(
                        f"The lord of the {_ordinal(kendra)}, a kendra "
                        f"(Viṣṇu's place), forms a {label} with the lord of "
                        f"the {_ordinal(trikona)}, a trikoṇa (Lakṣmī's "
                        f"place)."),
                    conditions_all=[
                        _lords_related_full(kendra, trikona, mode)],
                    cancellation_conditions=[
                        _dusthana_ownership_cancellation(kendra, trikona)],
                    strength_modifiers=lords_modifiers([kendra, trikona]),
                    houses_involved=[kendra, trikona],
                    variant_of=(f"raja_yoga_k{kendra}_t{trikona}_"
                                + ("mutual_aspect"
                                   if mode == "full_mutual_aspect" else mode)),
                    notes=(
                        "Two differences from the default rule: the aspect "
                        "mode requires FULL drishti, as pūrṇa-dṛṣṭyā in BPHS "
                        "34.12 states, and the BPHS 34.15 exception is "
                        "applied as a cancellation."),
                ))
    return rules


# ── Lakshmi: two witnesses, two rules ────────────────────────────────────────

def _lord_dignified_and_placed(house: int, houses: Sequence[int],
                               dignities: Sequence[str]) -> Condition:
    houses = tuple(houses)
    dignities = tuple(dignities)

    def test(features: ChartFeatures) -> ConditionResult:
        lord = features.lord_of(house)
        if not lord:
            return ConditionResult(False, f"the {_ordinal(house)} has no lord")
        found = features.planet(lord)
        if found is None:
            return ConditionResult(False, f"{lord} is not in the chart")
        has_dignity = any(getattr(found, d, False) for d in dignities)
        well_placed = found.house in houses
        if has_dignity and well_placed:
            return ConditionResult(
                True,
                f"the {_ordinal(house)} lord {lord} is {found.dignity} and in "
                f"the {_ordinal(found.house)}",
                planets=[lord], houses=[found.house])
        return ConditionResult(
            False,
            f"the {_ordinal(house)} lord {lord} is {found.dignity} in the "
            f"{_ordinal(found.house)}",
            planets=[lord], houses=[found.house])

    return Condition(
        f"the {_ordinal(house)} lord dignified and angular or trinal", test)


def _planet_dignified_and_placed(planet: str, houses: Sequence[int],
                                 dignities: Sequence[str]) -> Condition:
    houses = tuple(houses)

    def test(features: ChartFeatures) -> ConditionResult:
        found = features.planet(planet)
        if found is None:
            return ConditionResult(False, f"{planet} is not in the chart")
        has_dignity = any(getattr(found, d, False) for d in dignities)
        met = has_dignity and found.house in houses
        return ConditionResult(
            met,
            f"{planet} is {found.dignity} in the {_ordinal(found.house)}",
            planets=[planet], houses=[found.house])

    return Condition(f"{planet} dignified and angular or trinal", test)


def _lagna_lord_strong() -> Condition:
    def test(features: ChartFeatures) -> ConditionResult:
        lord = features.lagna_lord
        ratio = features.shadbala_ratio(lord)
        if ratio is None:
            return ConditionResult(
                False,
                f"the Lagna lord {lord}'s Shadbala was not computed, so the "
                f"strength BPHS 36.27 requires cannot be established",
                planets=[lord])
        met = ratio >= 1.0
        return ConditionResult(
            met,
            f"the Lagna lord {lord}'s Shadbala is {ratio:.2f}x its "
            f"requirement",
            planets=[lord])

    return Condition("the Lagna lord is strong (balāḍhya)", test)


def _lakshmi_rules() -> list[YogaRule]:
    kendra_or_trikona = tuple(sorted(set(KENDRA_HOUSES + TRIKONA_HOUSES)))
    return [
        YogaRule(
            id="lakshmi_yoga_bphs",
            name="Lakshmi Yoga (BPHS 36.27 reading)",
            category="dhana",
            tradition="Parashari (BPHS 36.27 as located)",
            source="BPHS(Sanskrit/SD) 36.27 [witness BPHS_SA_36.27_LAKSHMI]",
            explanation=(
                "The 9th lord is in a kendra, in moolatrikona, or in its own "
                "sign or exaltation, and the Lagna lord is strong."),
            conditions_all=[
                _lord_dignified_and_placed(
                    9, kendra_or_trikona,
                    ("own_sign", "exalted", "moolatrikona")),
                _lagna_lord_strong(),
            ],
            strength_modifiers=lords_modifiers([9, 1]),
            houses_involved=[9, 1],
            variant_of="lakshmi_yoga",
            notes=(
                "Phaladīpikā 6.21 gives a different rule under the same name, "
                "requiring Venus as well; see `lakshmi_yoga_phaladeepika`. "
                "The two are registered as the conflict "
                "LAKSHMI_YOGA_DEFINITION and are not merged."),
        ),
        YogaRule(
            id="lakshmi_yoga_phaladeepika",
            name="Lakshmi Yoga (Phaladeepika 6.21 reading)",
            category="dhana",
            tradition="Mantreśvara (PD 6.21 as located)",
            source="Phaladīpikā(SD) 6.21 [witness PD_6.21_LAKSHMI]",
            explanation=(
                "The 9th lord and Shukra are both in own sign or exaltation "
                "and both occupy a kendra or a trikona."),
            conditions_all=[
                _lord_dignified_and_placed(
                    9, kendra_or_trikona, ("own_sign", "exalted")),
                _planet_dignified_and_placed(
                    "Shukra", kendra_or_trikona, ("own_sign", "exalted")),
            ],
            strength_modifiers=lords_modifiers([9]),
            planets_involved=["Shukra"],
            houses_involved=[9],
            variant_of="lakshmi_yoga",
            notes=(
                "Requires two grahas where the BPHS reading requires one, and "
                "does not mention the Lagna lord. Fires on different charts."),
        ),
    ]


# ── The profile ──────────────────────────────────────────────────────────────

def textual_rules() -> list[YogaRule]:
    """Every rule written against a located V1.5 witness."""
    return (
        _moon_yoga_rules()
        + [_kemadruma_textual()]
        + _mahapurusha_textual_rules()
        + _gajakesari_textual_rules()
        + _raja_yoga_textual_rules()
        + _lakshmi_rules()
    )


# Rules in the default catalog that a textual rule supersedes. When the
# textual profile is selected these are dropped, so that one chart does not
# report both readings of one combination as if they were two findings.
SUPERSEDED_BY_TEXTUAL: dict[str, str] = {
    "sunapha": "sunapha_textual",
    "anapha": "anapha_textual",
    "durudhara": "durudhara_textual",
    "kemadruma": "kemadruma_textual",
    "kemadruma_bhanga_kendra_lagna": "kemadruma_textual",
    "kemadruma_bhanga_kendra_moon": "kemadruma_textual",
    "kemadruma_bhanga_moon_kendra": "kemadruma_textual",
    "kemadruma_bhanga_benefic_drishti": "kemadruma_textual",
    "gajakesari": "gajakesari_textual_bphs",
    "lakshmi_yoga": "lakshmi_yoga_bphs",
    **{f"mahapurusha_{key}": f"mahapurusha_{key}_textual"
       for key, _name, _planet in MAHAPURUSHA},
    **{f"raja_yoga_k{k}_t{t}_{mode}":
       f"raja_yoga_k{k}_t{t}_"
       f"{'full_mutual_aspect' if mode == 'mutual_aspect' else mode}_textual"
       for k in KENDRA_HOUSES for t in TRIKONA_HOUSES if k != t
       for mode in ("conjunction", "mutual_aspect", "exchange")},
}
