"""
Extended Yoga catalog (V1.2 Part 10)
-------------------------------------
Additional classical combinations, written in the same declarative form as the
V1.1 catalog. The rule engine is unchanged; this only adds rules.

Discipline applied throughout, per the brief:

  * A rule appears here only when its formation condition is understood well
    enough to state exactly. Nothing is invented to fill a gap.
  * Where sources genuinely differ, the readings are SEPARATE rules with
    distinct ids and profiles, carrying `variant_of`. They are never blended
    into one definition that neither authority would recognise.
  * Where a source could not be traced to a specific chapter, the `source`
    field says so instead of naming a text that may not contain it.

Sources cited:
  BPHS  Brihat Parashara Hora Shastra (Santhanam translation chapter numbers)
  PD    Phaladeepika, Mantreswara
  SY    Saravali, Kalyana Varma
  JP    Jataka Parijata, Vaidyanatha Dikshita
"""

from __future__ import annotations

from typing import Optional, Sequence

from ..features.lordships import (
    DUSTHANA_HOUSES, KENDRA_HOUSES, TRIKONA_HOUSES,
)
from ..features.models import ChartFeatures
from . import conditions as C
from .conditions import ConditionResult, _ordinal
from .engine import YogaRule
from .modifiers import lords_modifiers, standard_modifiers

# Grahas that count as "company" in the Moon- and Sun-relative yogas. The
# luminaries and the shadow grahas are excluded by the classical statements,
# and the exclusions differ between the two families, so each is named where
# it is used rather than shared.
TARA_GRAHAS = ("Mangal", "Budha", "Guru", "Shukra", "Shani")
NATURAL_BENEFICS = ("Guru", "Shukra", "Budha")


# ── shared condition helpers ─────────────────────────────────────────────────

def _houses_from(features: ChartFeatures, reference: str,
                 offsets: Sequence[int]) -> Optional[list[int]]:
    """Absolute house numbers at the given inclusive distances from a graha."""
    anchor = features.planet(reference)
    if anchor is None:
        return None
    return [((anchor.house + offset - 2) % 12) + 1 for offset in offsets]


def occupants_at_distance(reference: str, offsets: Sequence[int],
                          eligible: Sequence[str], label: str,
                          require_all: bool = False) -> C.Condition:
    """
    Grahas from `eligible` occupying the houses at `offsets` from `reference`.

    `require_all` distinguishes "at least one of these houses is occupied"
    (Sunapha, Vesi) from "every one of them is occupied" (Adhi, Durudhara).
    """
    def test(features: ChartFeatures) -> ConditionResult:
        houses = _houses_from(features, reference, offsets)
        if houses is None:
            return ConditionResult(False, f"{reference} is not in the chart")
        found: dict[int, list[str]] = {}
        for name in eligible:
            graha = features.planet(name)
            if graha is not None and graha.house in houses:
                found.setdefault(graha.house, []).append(name)

        distances = ", ".join(_ordinal(o) for o in offsets)
        if require_all:
            missing = [h for h in houses if h not in found]
            if missing:
                return ConditionResult(
                    False,
                    f"not every house at the {distances} from {reference} is "
                    f"occupied by {label} — the "
                    f"{', '.join(_ordinal(h) for h in missing)} "
                    f"{'is' if len(missing) == 1 else 'are'} empty",
                    houses=houses)
            planets = sorted({p for ps in found.values() for p in ps})
            return ConditionResult(
                True,
                f"every house at the {distances} from {reference} is occupied "
                f"by {label}: " + ", ".join(planets),
                planets=planets, houses=houses)

        if not found:
            return ConditionResult(
                False,
                f"no {label} occupies the {distances} from {reference}",
                houses=houses)
        planets = sorted({p for ps in found.values() for p in ps})
        return ConditionResult(
            True,
            f"{', '.join(planets)} "
            f"{'occupies' if len(planets) == 1 else 'occupy'} the "
            f"{distances} from {reference}",
            planets=planets, houses=houses)

    return C.Condition(label + f" at the "
                       + ", ".join(_ordinal(o) for o in offsets)
                       + f" from {reference}", test)


def no_occupants_at_distance(reference: str, offsets: Sequence[int],
                             eligible: Sequence[str], label: str) -> C.Condition:
    """The mirror of the above: those houses must be empty."""
    inner = occupants_at_distance(reference, offsets, eligible, label)

    def test(features: ChartFeatures) -> ConditionResult:
        result = inner.evaluate(features)
        if result.met:
            return ConditionResult(False, "fails because " + result.description,
                                   planets=result.planets, houses=result.houses)
        return ConditionResult(True, result.description, houses=result.houses)

    return C.Condition(
        f"no {label} at the " + ", ".join(_ordinal(o) for o in offsets)
        + f" from {reference}", test)


# ── Vipareeta Raja Yoga ──────────────────────────────────────────────────────
# A dusthana lord placed in a dusthana. The reasoning is that the lord of a
# house of difficulty, itself fallen into difficulty, damages what it would
# otherwise have damaged.
#
# Sources differ on ONE point, and it is material: whether the lord may sit in
# its OWN dusthana or must fall into a DIFFERENT one. Both readings are
# implemented, as separate rules in separate profiles.

_VIPAREETA = [
    ("harsha", "Harsha", 6, "the 6th — enemies, disease, debt"),
    ("sarala", "Sarala", 8, "the 8th — longevity, obstruction"),
    ("vimala", "Vimala", 12, "the 12th — loss, expenditure"),
]


def _vipareeta_rules(different_house_only: bool) -> list[YogaRule]:
    rules = []
    for key, name, house, gloss in _VIPAREETA:
        targets = tuple(h for h in DUSTHANA_HOUSES
                        if not (different_house_only and h == house))
        suffix = "_strict" if different_house_only else ""
        rules.append(YogaRule(
            id=f"vipareeta_{key}{suffix}",
            name=(f"{name} Yoga (Vipareeta Raja Yoga)"
                  + (" — strict reading" if different_house_only else "")),
            category="vipareeta_raja",
            tradition=("Parashari, strict reading" if different_house_only
                       else "Parashari"),
            source="BPHS ch.36; Phaladeepika ch.6.38",
            explanation=(
                f"The lord of {gloss} occupies "
                + (f"a dusthana other than its own ({_ordinal(targets[0])}, "
                   f"{_ordinal(targets[1])})" if different_house_only
                   else "the 6th, 8th or 12th")
                + "."),
            conditions_all=[
                C.lord_of_house_in_houses(
                    house, targets,
                    label=f"lord of the {_ordinal(house)} in "
                          + " / ".join(_ordinal(t) for t in targets)),
            ],
            strength_modifiers=lords_modifiers([house]),
            houses_involved=[house],
            variant_of=f"vipareeta_{key}" if different_house_only else None,
            notes=(
                "The strict reading requires the dusthana lord to fall into a "
                "DIFFERENT dusthana; the common reading allows its own. The "
                "two are kept apart because a chart can satisfy one and not "
                "the other."
                if different_house_only else
                "Some authorities require the lord to occupy a dusthana other "
                "than its own; that is the `_strict` variant, in the "
                "parashari_strict profile."),
        ))
    return rules


# ── Parivartana Yogas ────────────────────────────────────────────────────────
# Mutual reception between two house lords. BPHS classifies the exchange by
# the houses involved, and the feature layer already computes that category,
# so these rules read it rather than re-deriving it.

_PARIVARTANA_KINDS = [
    ("maha", "Maha", "between two houses that are neither dusthanas nor the 3rd"),
    ("dainya", "Dainya", "involving a dusthana (6th, 8th or 12th)"),
    ("khala", "Khala", "involving the 3rd house"),
]


def _parivartana_present(category: str):
    def test(features: ChartFeatures) -> ConditionResult:
        matches = [p for p in features.parivartanas if p.category == category]
        if not matches:
            return ConditionResult(
                False, f"no {category} exchange is present in this chart")
        planets = sorted({p.planet1 for p in matches}
                         | {p.planet2 for p in matches})
        houses = sorted({p.house1 for p in matches} | {p.house2 for p in matches})
        return ConditionResult(
            True, "; ".join(p.describe() for p in matches),
            planets=planets, houses=houses)
    return test


def _parivartana_rules() -> list[YogaRule]:
    return [
        YogaRule(
            id=f"parivartana_{key}",
            name=f"{name} Parivartana Yoga",
            category="parivartana",
            tradition="Parashari",
            source="BPHS ch.36 (exchange of rashis)",
            explanation=(
                f"Two house lords occupy one another's rashis, in an exchange "
                f"{gloss}."),
            conditions_all=[
                C.custom(f"a {key} exchange is present",
                         _parivartana_present(key)),
            ],
            strength_modifiers=[],
            notes=("The three kinds are distinguished by the houses involved, "
                   "not by the grahas. A chart may hold more than one; all "
                   "are listed in the matched clause."),
        )
        for key, name, gloss in _PARIVARTANA_KINDS
    ]


# ── Moon-relative yogas: Sunapha, Anapha, Durudhara ──────────────────────────
# The complement of Kemadruma. Grahas other than the Sun — and, in the
# majority reading, other than the nodes — occupying the 2nd and/or 12th from
# the Moon. The same exclusion Kemadruma uses, for consistency.

def _lunar_company_rules() -> list[YogaRule]:
    return [
        YogaRule(
            id="sunapha",
            name="Sunapha Yoga",
            category="chandra",
            tradition="Parashari",
            source="BPHS ch.34; Phaladeepika ch.6.3",
            explanation=("A graha other than Surya occupies the 2nd from "
                         "Chandra."),
            conditions_all=[
                occupants_at_distance("Chandra", (2,), TARA_GRAHAS,
                                      "a graha other than Surya"),
            ],
            strength_modifiers=standard_modifiers(["Chandra"]),
            planets_involved=["Chandra"],
            notes="Rahu and Ketu are not counted, matching the Kemadruma rule.",
        ),
        YogaRule(
            id="anapha",
            name="Anapha Yoga",
            category="chandra",
            tradition="Parashari",
            source="BPHS ch.34; Phaladeepika ch.6.3",
            explanation=("A graha other than Surya occupies the 12th from "
                         "Chandra."),
            conditions_all=[
                occupants_at_distance("Chandra", (12,), TARA_GRAHAS,
                                      "a graha other than Surya"),
            ],
            strength_modifiers=standard_modifiers(["Chandra"]),
            planets_involved=["Chandra"],
        ),
        YogaRule(
            id="durudhara",
            name="Durudhara Yoga",
            category="chandra",
            tradition="Parashari",
            source="BPHS ch.34; Phaladeepika ch.6.3",
            explanation=("Grahas other than Surya occupy BOTH the 2nd and the "
                         "12th from Chandra."),
            conditions_all=[
                occupants_at_distance("Chandra", (2, 12), TARA_GRAHAS,
                                      "grahas other than Surya",
                                      require_all=True),
            ],
            strength_modifiers=standard_modifiers(["Chandra"]),
            planets_involved=["Chandra"],
            notes=("Implies Sunapha and Anapha both hold; all three are "
                   "reported, since the texts name them separately."),
        ),
    ]


# ── Sun-relative yogas: Vesi, Vasi, Ubhayachari ──────────────────────────────
# The solar counterparts. Here the exclusion is the MOON rather than the Sun,
# and the nodes are again not counted.

def _solar_company_rules() -> list[YogaRule]:
    return [
        YogaRule(
            id="vesi",
            name="Vesi Yoga",
            category="surya",
            tradition="Parashari",
            source="BPHS ch.34; Phaladeepika ch.6.2",
            explanation=("A graha other than Chandra occupies the 2nd from "
                         "Surya."),
            conditions_all=[
                occupants_at_distance("Surya", (2,), TARA_GRAHAS,
                                      "a graha other than Chandra"),
            ],
            strength_modifiers=standard_modifiers(["Surya"]),
            planets_involved=["Surya"],
        ),
        YogaRule(
            id="vasi",
            name="Vasi Yoga",
            category="surya",
            tradition="Parashari",
            source="BPHS ch.34; Phaladeepika ch.6.2",
            explanation=("A graha other than Chandra occupies the 12th from "
                         "Surya."),
            conditions_all=[
                occupants_at_distance("Surya", (12,), TARA_GRAHAS,
                                      "a graha other than Chandra"),
            ],
            strength_modifiers=standard_modifiers(["Surya"]),
            planets_involved=["Surya"],
        ),
        YogaRule(
            id="ubhayachari",
            name="Ubhayachari Yoga",
            category="surya",
            tradition="Parashari",
            source="BPHS ch.34; Phaladeepika ch.6.2",
            explanation=("Grahas other than Chandra occupy BOTH the 2nd and "
                         "the 12th from Surya."),
            conditions_all=[
                occupants_at_distance("Surya", (2, 12), TARA_GRAHAS,
                                      "grahas other than Chandra",
                                      require_all=True),
            ],
            strength_modifiers=standard_modifiers(["Surya"]),
            planets_involved=["Surya"],
        ),
    ]


# ── Adhi Yoga ────────────────────────────────────────────────────────────────
# Natural benefics occupying the 6th, 7th and 8th from a reference point.
# Sources split on whether that point is the Moon or the Lagna, so both exist
# as separate rules. They also split on whether ALL THREE houses must be
# occupied or merely that the benefics are confined to them; the stricter
# all-three reading is implemented and the looser one is not invented.

def _adhi_rules() -> list[YogaRule]:
    rules = []
    for reference, suffix, tradition, source in (
        ("Chandra", "", "Parashari",
         "BPHS ch.36; Phaladeepika ch.6.13"),
        ("Lagna_proxy", "_from_lagna", "Variant reading",
         "Authorities that reckon Adhi Yoga from the Lagna"),
    ):
        if reference == "Lagna_proxy":
            # Counted from the Lagna, i.e. the absolute 6th, 7th and 8th.
            condition = C.custom(
                "natural benefics occupy the 6th, 7th and 8th from the Lagna",
                _benefics_in_houses((6, 7, 8)))
        else:
            condition = occupants_at_distance(
                "Chandra", (6, 7, 8), NATURAL_BENEFICS,
                "natural benefics", require_all=True)

        rules.append(YogaRule(
            id=f"adhi_yoga{suffix}",
            name="Adhi Yoga" + (" (from the Lagna)" if suffix else ""),
            category="raja",
            tradition=tradition,
            source=source,
            explanation=(
                "Guru, Shukra and Budha occupy the 6th, 7th and 8th from "
                + ("the Lagna." if suffix else "Chandra.")),
            conditions_all=[condition],
            strength_modifiers=standard_modifiers(list(NATURAL_BENEFICS)),
            planets_involved=list(NATURAL_BENEFICS),
            variant_of="adhi_yoga" if suffix else None,
            notes=("Reckoned from the Lagna rather than the Moon. Charts "
                   "satisfying one rarely satisfy the other."
                   if suffix else
                   "Requires all three houses to be occupied by benefics. A "
                   "looser reading merely requires the benefics to be confined "
                   "to those houses; it is not implemented, because the "
                   "sources consulted do not state it unambiguously."),
        ))
    return rules


def _benefics_in_houses(houses: Sequence[int]):
    def test(features: ChartFeatures) -> ConditionResult:
        found: dict[int, list[str]] = {}
        for name in NATURAL_BENEFICS:
            graha = features.planet(name)
            if graha is not None and graha.house in houses:
                found.setdefault(graha.house, []).append(name)
        missing = [h for h in houses if h not in found]
        if missing:
            return ConditionResult(
                False,
                "the " + ", ".join(_ordinal(h) for h in missing)
                + " from the Lagna "
                + ("is" if len(missing) == 1 else "are")
                + " not occupied by a natural benefic",
                houses=list(houses))
        planets = sorted({p for ps in found.values() for p in ps})
        return ConditionResult(
            True,
            "natural benefics occupy the "
            + ", ".join(_ordinal(h) for h in houses) + ": "
            + ", ".join(planets),
            planets=planets, houses=list(houses))
    return test


# ── Amala Yoga ───────────────────────────────────────────────────────────────

def _amala_rules() -> list[YogaRule]:
    rules = []
    for reference, suffix, tradition in (
            ("Lagna", "", "Parashari"),
            ("Chandra", "_from_moon", "Variant reading")):
        if reference == "Lagna":
            condition = C.custom(
                "a natural benefic occupies the 10th from the Lagna",
                _benefic_in_tenth_from_lagna())
        else:
            condition = occupants_at_distance(
                "Chandra", (10,), NATURAL_BENEFICS, "a natural benefic")

        rules.append(YogaRule(
            id=f"amala_yoga{suffix}",
            name="Amala Yoga" + (" (from Chandra)" if suffix else ""),
            category="raja",
            tradition=tradition,
            source=("BPHS ch.36; Phaladeepika ch.6.35" if not suffix
                    else "Authorities that reckon Amala Yoga from the Moon"),
            explanation=(
                "A natural benefic occupies the 10th from "
                + ("Chandra." if suffix else "the Lagna.")),
            conditions_all=[condition],
            strength_modifiers=standard_modifiers(list(NATURAL_BENEFICS)),
            houses_involved=[10],
            variant_of="amala_yoga" if suffix else None,
        ))
    return rules


def _benefic_in_tenth_from_lagna():
    def test(features: ChartFeatures) -> ConditionResult:
        found = [name for name in NATURAL_BENEFICS
                 if (features.planet(name) or None)
                 and features.planet(name).house == 10]
        if not found:
            return ConditionResult(
                False, "no natural benefic occupies the 10th from the Lagna",
                houses=[10])
        return ConditionResult(
            True,
            ", ".join(found) + " occupies the 10th from the Lagna",
            planets=found, houses=[10])
    return test


# ── Lakshmi Yoga ─────────────────────────────────────────────────────────────
# The 9th lord dignified and well placed, with a strong Lagna lord. Sources
# vary in how they word "strong"; the condition implemented is the concrete
# one they agree on — own rashi or exaltation — rather than a vaguer notion
# invented to cover the difference.

def _lakshmi_yoga() -> YogaRule:
    def ninth_lord_dignified_and_placed(features: ChartFeatures) -> ConditionResult:
        lord = features.lord_of(9)
        graha = features.planet(lord) if lord else None
        if graha is None:
            return ConditionResult(False, "the 9th lord is not in the chart")
        dignified = graha.own_sign or graha.exalted or graha.moolatrikona
        well_placed = graha.house in tuple(KENDRA_HOUSES) + tuple(TRIKONA_HOUSES)
        if dignified and well_placed:
            return ConditionResult(
                True,
                f"the 9th lord {lord} is in "
                f"{'exaltation' if graha.exalted else 'its own rashi'} and "
                f"occupies the {_ordinal(graha.house)}, a kendra or trikona",
                planets=[lord], houses=[9, graha.house])
        missing = []
        if not dignified:
            missing.append(f"{lord} is neither exalted nor in its own rashi")
        if not well_placed:
            missing.append(f"{lord} is in the {_ordinal(graha.house)}, "
                           f"neither a kendra nor a trikona")
        return ConditionResult(False, "; ".join(missing), planets=[lord])

    def lagna_lord_strong(features: ChartFeatures) -> ConditionResult:
        lord = features.lagna_lord
        graha = features.planet(lord)
        if graha is None:
            return ConditionResult(False, "the Lagna lord is not in the chart")
        if graha.own_sign or graha.exalted or graha.moolatrikona:
            return ConditionResult(
                True,
                f"the Lagna lord {lord} is in "
                f"{'exaltation' if graha.exalted else 'its own rashi'}",
                planets=[lord])
        return ConditionResult(
            False,
            f"the Lagna lord {lord} is in {graha.sign_name}, neither its own "
            f"rashi nor exaltation", planets=[lord])

    return YogaRule(
        id="lakshmi_yoga",
        name="Lakshmi Yoga",
        category="dhana",
        tradition="Parashari",
        source="Phaladeepika ch.6.34; BPHS ch.36",
        explanation=("The lord of the 9th stands in its own rashi or in "
                     "exaltation while occupying a kendra or trikona, and the "
                     "Lagna lord is likewise dignified."),
        conditions_all=[
            C.custom("the 9th lord is dignified and in a kendra or trikona",
                     ninth_lord_dignified_and_placed),
            C.custom("the Lagna lord is in its own rashi or exaltation",
                     lagna_lord_strong),
        ],
        strength_modifiers=lords_modifiers([1, 9]),
        houses_involved=[1, 9],
        notes=("Sources word the Lagna-lord requirement as 'strong', which is "
               "not a testable condition. The concrete reading they share — "
               "own rashi or exaltation — is what is implemented; no broader "
               "notion of strength has been invented to widen it."),
    )


# ── Saraswati Yoga ───────────────────────────────────────────────────────────

def _saraswati_yoga() -> YogaRule:
    ALLOWED = tuple(sorted(set(KENDRA_HOUSES) | set(TRIKONA_HOUSES) | {2}))

    def all_three_well_placed(features: ChartFeatures) -> ConditionResult:
        placements = []
        bad = []
        for name in ("Guru", "Shukra", "Budha"):
            graha = features.planet(name)
            if graha is None:
                return ConditionResult(False, f"{name} is not in the chart")
            if graha.house in ALLOWED:
                placements.append(f"{name} in the {_ordinal(graha.house)}")
            else:
                bad.append(f"{name} in the {_ordinal(graha.house)}")
        if bad:
            return ConditionResult(
                False,
                "not all of Guru, Shukra and Budha are in a kendra, trikona or "
                "the 2nd — " + ", ".join(bad))
        return ConditionResult(
            True,
            "Guru, Shukra and Budha all occupy a kendra, trikona or the 2nd: "
            + ", ".join(placements),
            planets=["Guru", "Shukra", "Budha"])

    def guru_dignified(features: ChartFeatures) -> ConditionResult:
        guru = features.planet("Guru")
        if guru is None:
            return ConditionResult(False, "Guru is not in the chart")
        if guru.exalted or guru.own_sign or guru.moolatrikona or guru.friendly_sign:
            state = ("exalted" if guru.exalted else
                     "in moolatrikona" if guru.moolatrikona else
                     "in its own rashi" if guru.own_sign else
                     "in a friendly rashi")
            return ConditionResult(
                True, f"Guru is {state} ({guru.sign_name})", planets=["Guru"])
        return ConditionResult(
            False,
            f"Guru in {guru.sign_name} is neither exalted, nor in its own, "
            f"moolatrikona or a friendly rashi", planets=["Guru"])

    return YogaRule(
        id="saraswati_yoga",
        name="Saraswati Yoga",
        category="vidya",
        tradition="Parashari",
        source="Phaladeepika ch.6.33; Jataka Parijata",
        explanation=("Guru, Shukra and Budha all occupy a kendra, a trikona "
                     "or the 2nd house, with Guru in its own, moolatrikona, "
                     "exaltation or a friendly rashi."),
        conditions_all=[
            C.custom("Guru, Shukra and Budha are in kendras, trikonas or the 2nd",
                     all_three_well_placed),
            C.custom("Guru is dignified", guru_dignified),
        ],
        strength_modifiers=standard_modifiers(["Guru", "Shukra", "Budha"]),
        planets_involved=["Guru", "Shukra", "Budha"],
    )


# ── Gajakesari, alternate profile ────────────────────────────────────────────
# The V1.1 catalog carries the Parashari reading: Guru in a kendra FROM THE
# MOON. Some authorities additionally require Guru to be dignified and to
# occupy a kendra from the LAGNA. That is a materially narrower rule, so it is
# a separate id rather than extra conditions bolted onto the original.

def _gajakesari_alternate() -> YogaRule:
    return YogaRule(
        id="gajakesari_alternate",
        name="Gajakesari Yoga (alternate, stricter reading)",
        category="raja",
        tradition="Alternate reading",
        source=("Authorities requiring Guru to be dignified and angular from "
                "the Lagna as well as from Chandra"),
        explanation=("Guru occupies a kendra from Chandra AND a kendra from "
                     "the Lagna, and is dignified."),
        conditions_all=[
            C.planet_in_kendra_from_planet("Guru", "Chandra"),
            C.planet_in_houses("Guru", KENDRA_HOUSES,
                               label="Guru occupies a kendra from the Lagna"),
            C.planet_dignity("Guru", ("own_sign", "exalted", "moolatrikona",
                                      "friendly_sign"),
                             label="Guru is dignified or in a friendly rashi"),
        ],
        strength_modifiers=standard_modifiers(["Guru", "Chandra"]),
        planets_involved=["Guru", "Chandra"],
        variant_of="gajakesari",
        notes=("Strictly narrower than the Parashari Gajakesari. A chart "
               "satisfying this one also satisfies that one; the reverse does "
               "not hold. Both are reported so the difference is visible."),
    )


# ── Kemadruma Bhanga as findable results ─────────────────────────────────────
# The V1.1 engine evaluates the bhanga clauses as CANCELLATIONS inside the
# Kemadruma rule, which is where they belong. But a reader often wants to know
# which bhanga applied without reading the cancellation list, so each is also
# exposed as its own rule. These are reported alongside Kemadruma and never
# instead of it.

from .catalog import (                                        # noqa: E402
    _bhanga_moon_aspected_by_benefic, _bhanga_moon_in_kendra_from_lagna,
    _bhanga_planet_in_kendra_from_lagna, _bhanga_planet_in_kendra_from_moon,
    _kemadruma_isolation,
)

_BHANGA_CLAUSES = [
    ("kendra_lagna", "a graha occupies a kendra from the Lagna",
     _bhanga_planet_in_kendra_from_lagna),
    ("kendra_moon", "a graha occupies a kendra from Chandra",
     _bhanga_planet_in_kendra_from_moon),
    ("moon_kendra", "Chandra itself occupies a kendra from the Lagna",
     _bhanga_moon_in_kendra_from_lagna),
    ("benefic_drishti", "Chandra receives a benefic drishti",
     _bhanga_moon_aspected_by_benefic),
]


def _kemadruma_bhanga_rules() -> list[YogaRule]:
    rules = []
    for key, gloss, builder in _BHANGA_CLAUSES:
        rules.append(YogaRule(
            id=f"kemadruma_bhanga_{key}",
            name=f"Kemadruma Bhanga ({gloss})",
            category="cancellation",
            tradition="Parashari",
            source="BPHS ch.34.7; Phaladeepika ch.6.6",
            explanation=(
                f"Kemadruma has formed and is cancelled because {gloss}."),
            conditions_all=[
                C.custom("Chandra is isolated in the 2nd and 12th from itself",
                         _kemadruma_isolation()),
                C.custom(gloss, builder()),
            ],
            strength_modifiers=[],
            planets_involved=["Chandra"],
            notes=("Reported in addition to the Kemadruma result, not instead "
                   "of it. Kemadruma itself already evaluates every bhanga "
                   "clause as a cancellation; this exposes each clause "
                   "individually so the specific one can be cited."),
        ))
    return rules


# ── assembly ─────────────────────────────────────────────────────────────────

def extended_core_rules() -> list[YogaRule]:
    """Rules added in V1.2 that belong to the mainstream Parashari profile."""
    return (
        _vipareeta_rules(different_house_only=False)
        + _parivartana_rules()
        + _lunar_company_rules()
        + _solar_company_rules()
        + [_adhi_rules()[0]]
        + [_amala_rules()[0]]
        + [_lakshmi_yoga(), _saraswati_yoga()]
        + _kemadruma_bhanga_rules()
    )


def extended_variant_rules() -> list[YogaRule]:
    """Readings held by some authorities, kept out of the default profile."""
    return (
        _vipareeta_rules(different_house_only=True)
        + [_adhi_rules()[1]]
        + [_amala_rules()[1]]
        + [_gajakesari_alternate()]
    )
