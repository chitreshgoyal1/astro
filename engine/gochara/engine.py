"""
Gochara evaluation (V1.8 Parts 1-7)
-------------------------------------
Runs the located rules against a transit snapshot, in the order Part 1 sets:
frame, placement, favourability, vedha, daśā condition, natal strength, and
only then eligibility.

THE RESULT THIS PRODUCES, STATED HONESTLY

    Two rules are implemented and both are source-qualified. They do NOT do
    the same amount of work, and the difference decides everything about
    what strict synthesis may use.

    Phaladīpikā 26 judges a transit favourable or obstructed IN THE MOON'S
    FRAME. It does not say which affairs the transit bears on. The bhāva
    significations this engine holds are stated from the Lagna, in BPHS 11,
    so there is no sourced path from "Jupiter is favourable in the 9th from
    the Moon" to any life area. Chapter 26 therefore yields a verdict with
    NO HOUSES ATTACHED, and a verdict with no houses cannot reach a domain.

    Phaladīpikā 20.34-35 names the bhāva explicitly — `yadbhāvago gocarato
    vilagnāt … tadbhāvapuṣṭiṃ kurute` — and conditions the result on the
    transiting graha being the running daśā lord and on its natal strength.
    That is a complete chain: located frame, located condition, located
    effect, and a bhāva whose significations are separately sourced.

    So strict synthesis admits transit evidence from ONE of the two rules,
    and the other one narrows what the engine claims rather than widening
    it. That is the correct direction for a source to push a result.

WHY THE VERDICT IS NOT A SCORE

    `GocharaVerdict` has four values and no number. The verses say a
    placement is auspicious, or that an obstruction cancels the auspicious
    result. They do not rank placements, and any ranking here would be this
    engine's invention wearing a citation.
"""

from __future__ import annotations

from typing import Mapping, Optional

from ..features.dignity import is_exalted, is_own_sign
from ..features.relationships import FRIEND, sign_relationship
from .models import (
    GocharaActivation, GocharaJudgement, GocharaPlacement, GocharaResult,
    GocharaVerdict, NatalStrengthCondition, TransitReference,
)
from .rules import (
    DASHA_LORD_RULE, METHODOLOGY_ID, RULE_DASHA_LORD, RULE_MOON_FRAME,
    moon_frame_rule,
)
from .vedha import NODES_CAUSE_VEDHA_DEFAULT, NODE_VEDHA_NOTE, evaluate_vedha

# Part 6. BPHS 27 gives each graha a required virūpa total, and the Shadbala
# engine already computes the ratio of achieved to required. That ratio is
# the engine's reading of Phaladīpikā's `balānvita`, and the two are kept
# separate in `NatalStrengthCondition` because they are separate claims:
# Mantreśvara says "endowed with strength" and names no number.
STRENGTH_THRESHOLD = 1.0
STRENGTH_MEASURE = "shadbala_ratio"
STRENGTH_MEASURE_SOURCES = ("BPHS_27_SHADBALA",)

_ORDINALS = {1: "st", 2: "nd", 3: "rd"}


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{_ORDINALS.get(n % 10, 'th')}"


# ── frames ───────────────────────────────────────────────────────────────────

def _frame_houses(snapshot, frame: TransitReference) -> dict:
    """
    Every transiting graha's house, in one declared frame.

    Part 2 exists because this function has two correct answers and picking
    the wrong one is undetectable downstream: both frames produce integers
    from 1 to 12.
    """
    attribute = {TransitReference.MOON: "house_from_natal_moon",
                 TransitReference.LAGNA: "house_from_natal_lagna"}.get(frame)
    if attribute is None:
        return {}
    # `getattr` with a default rather than attribute access, because a
    # caller may legitimately supply a narrower position object than
    # TransitPosition — the golden fixtures do. A missing house means the
    # rule is not evaluated for that graha, which is a result; an
    # AttributeError in the middle of synthesis is not.
    return {name: getattr(position, attribute, None)
            for name, position in snapshot.positions.items()}


# ── Part 3 + 4: the chapter-26 rule ─────────────────────────────────────────

def evaluate_moon_frame(snapshot, *,
                        nodes_cause_vedha: bool = NODES_CAUSE_VEDHA_DEFAULT
                        ) -> list[GocharaJudgement]:
    """Phaladīpikā 26.2-8 for every transiting graha the table covers."""
    houses = _frame_houses(snapshot, TransitReference.MOON)
    out: list[GocharaJudgement] = []

    for planet in sorted(snapshot.positions):
        rule = moon_frame_rule(planet)
        if rule is None:
            continue
        house = houses.get(planet)
        if not house:
            continue

        favourable = rule.is_favourable_house(house)
        placement = GocharaPlacement(
            planet=planet, reference_frame=TransitReference.MOON,
            house=house,
            # False here means "the verse does not list this house as
            # favourable", which is NOT the same as "the verse calls it
            # unfavourable". The verdict below keeps the two apart.
            favourable=favourable,
            rule_id=RULE_MOON_FRAME,
            source_ref_ids=rule.source_ref_ids,
            explanation=(
                f"Transiting {planet} is in the {_ordinal(house)} from the "
                f"natal Chandra, which the verse "
                f"{'lists as favourable' if favourable else 'does not list'}."))

        vedha = None
        if favourable:
            vedha = evaluate_vedha(rule, house, houses,
                                   nodes_cause_vedha=nodes_cause_vedha)

        if not favourable:
            verdict = GocharaVerdict.NOT_STATED
            explanation = (
                f"Phaladīpikā 26 does not list the {_ordinal(house)} from "
                f"the Chandra among {planet}'s favourable houses. The "
                f"chapter states which placements are auspicious and does "
                f"not declare the rest inauspicious, so no verdict follows.")
        elif vedha is not None and vedha.obstructs:
            verdict = GocharaVerdict.OBSTRUCTED
            explanation = (
                f"{planet} in the {_ordinal(house)} from the Chandra is a "
                f"favourable transit, cancelled by vedha: "
                f"{vedha.explanation}")
        else:
            verdict = GocharaVerdict.FAVOURABLE
            explanation = (
                f"{planet} in the {_ordinal(house)} from the Chandra is "
                f"favourable. {vedha.explanation if vedha else ''}".strip())

        not_strict: tuple[str, ...] = ()
        if not rule.vedha_pairs:
            not_strict = (
                "no vedha houses are stated for this graha in either "
                "witness, so the rule's obstruction layer cannot be "
                "evaluated",)

        out.append(GocharaJudgement(
            rule_id=RULE_MOON_FRAME, transit_planet=planet,
            reference_frame=TransitReference.MOON,
            verdict=verdict, placement=placement, vedha=vedha,
            # Deliberately empty. See the module docstring: chapter 26
            # judges the transit, not the affairs it touches.
            houses_affected=(),
            house_frame=TransitReference.MOON,
            source_ref_ids=rule.source_ref_ids,
            validation_status=rule.validation_status,
            witness_agreement=rule.witness_agreement,
            strict_eligible=False,
            not_strict_because=not_strict or (
                "the rule judges the transit in the Chandra's frame and "
                "names no bhāva; the engine's bhāva significations are "
                "stated from the Lagna, so no sourced path reaches a "
                "life area",),
            explanation=explanation,
            explanation_key=f"gochara_{verdict.value.lower()}",
            explanation_args={"planet": planet, "house": house},
            limitations=(
                "Phaladīpikā 26.9-24 gives the effect of each graha in each "
                "house and is not implemented; this verdict is the "
                "favourable/obstructed judgement of 26.2-8 only.",)))
    return out


# ── Parts 5 + 6: the chapter-20 rule ────────────────────────────────────────

def _natal_strength(planet: str, features) -> NatalStrengthCondition:
    """
    Phaladīpikā 20.34's `balānvita`, and 20.35's list of natal afflictions.

    Two independent tests, because the verses give two: 20.34 requires
    strength, 20.35 names weakness OR combustion OR debilitation OR an
    enemy's sign. A graha can be Shadbala-strong and combust at once, and
    collapsing the two would lose that.
    """
    natal = features.planet(planet)
    afflictions: list[str] = []
    if natal is not None:
        if natal.combust:
            afflictions.append("combust at birth")
        if natal.debilitated:
            afflictions.append("debilitated at birth")
        if natal.enemy_sign:
            afflictions.append("in an enemy's sign at birth")

    ratio = features.shadbala_ratio(planet)
    if ratio is None:
        return NatalStrengthCondition(
            planet=planet,
            textual_qualification=(
                "20.34 `balānvitaś cej janane 'pi tasya` — provided it was "
                "endowed with strength at birth as well."),
            software_interpretation=(
                "Shadbala was not computed for this chart, so the condition "
                "could not be tested."),
            satisfied=None,
            measure=STRENGTH_MEASURE,
            rule_source_ref_ids=DASHA_LORD_RULE.source_ref_ids,
            afflictions=tuple(afflictions),
            note=("Untested, not failed. A rule whose condition could not "
                  "be evaluated does not thereby pass it."))

    return NatalStrengthCondition(
        planet=planet,
        textual_qualification=(
            "20.34 `balānvitaś cej janane 'pi tasya` — provided it was "
            "endowed with strength at birth as well. The verse names no "
            "number."),
        software_interpretation=(
            f"Shadbala total reaches its BPHS 27 requirement, i.e. "
            f"{STRENGTH_MEASURE} >= {STRENGTH_THRESHOLD}. The threshold is "
            f"BPHS's own requirement table and is NOT Phaladīpikā's; the "
            f"verse is being operationalised, not quoted."),
        satisfied=ratio >= STRENGTH_THRESHOLD,
        measure=STRENGTH_MEASURE,
        measured_value=round(ratio, 3),
        threshold=STRENGTH_THRESHOLD,
        measure_source_ref_ids=STRENGTH_MEASURE_SOURCES,
        rule_source_ref_ids=DASHA_LORD_RULE.source_ref_ids,
        afflictions=tuple(afflictions),
        note=("The measure comes from a different work than the rule. That "
              "is recorded rather than smoothed over: BPHS supplies the "
              "number, Mantreśvara supplies the condition."))


def _transit_dignity(planet: str, sign: int) -> tuple[bool, str]:
    """20.34's `svoccasuhṛdgṛhasthaḥ` — own sign, exaltation, or a friend's."""
    if is_exalted(planet, sign):
        return True, "exalted"
    if is_own_sign(planet, sign):
        return True, "in its own sign"
    if sign_relationship(planet, sign) == FRIEND:
        return True, "in a friend's sign"
    return False, "neither exalted, in its own sign, nor in a friend's"


def evaluate_dasha_lord(snapshot, features, dasha_stack: Mapping
                        ) -> list[GocharaJudgement]:
    """
    Phaladīpikā 20.34-35 for whichever grahas are running the daśā.

    `dasha_stack` is the mapping `Vimshottari.get_dasha_stack_at` already
    returns. Part 5 forbids duplicating the daśā computation and this does
    not: it reads three lord names and computes no period.
    """
    if not dasha_stack or not dasha_stack.get("in_range", True):
        return []

    lords = {level: dasha_stack.get(level)
             for level in ("mahadasha", "antardasha", "pratyantardasha")}
    out: list[GocharaJudgement] = []

    for planet in sorted(snapshot.positions):
        levels = tuple(level for level, lord in lords.items()
                       if lord == planet)
        if not levels:
            continue

        position = snapshot.positions[planet]
        house = getattr(position, "house_from_natal_lagna", None)
        sign = getattr(position, "sign", None)
        if not house or sign is None:
            # 20.34 needs both the transited bhāva and the transited rashi.
            # A position object supplying neither is not a failed condition,
            # it is an unevaluable one, and it is skipped rather than
            # silently treated as unfavourable.
            continue

        strength = _natal_strength(planet, features)
        dignified, dignity_words = _transit_dignity(planet, sign)

        activation = GocharaActivation(
            transit_planet=planet,
            is_mahadasha_lord="mahadasha" in levels,
            is_antardasha_lord="antardasha" in levels,
            is_pratyantardasha_lord="pratyantardasha" in levels,
            natal_strength=strength,
            transit_rule_result=GocharaPlacement(
                planet=planet, reference_frame=TransitReference.LAGNA,
                house=house, favourable=dignified,
                rule_id=RULE_DASHA_LORD,
                source_ref_ids=DASHA_LORD_RULE.source_ref_ids,
                explanation=(
                    f"Transiting {planet} is in the {_ordinal(house)} from "
                    f"the natal Lagna, {dignity_words}.")),
            vedha_result=None)

        # 20.35 first, because its condition is the natal one and it carries
        # no requirement on the transited sign. A daśā lord afflicted at
        # birth damages whichever bhāva it reaches, dignified or not.
        afflicted = bool(strength.afflictions) or strength.satisfied is False

        if afflicted:
            verdict = GocharaVerdict.UNFAVOURABLE
            reasons = list(strength.afflictions)
            if strength.satisfied is False:
                reasons.append(
                    f"below its BPHS 27 Shadbala requirement "
                    f"({strength.measured_value})")
            explanation = (
                f"{planet} rules the running "
                f"{' and '.join(levels)} and was {', '.join(reasons)}. "
                f"Phaladīpikā 20.35: such a lord damages whichever bhāva it "
                f"transits — here the {_ordinal(house)} from the Lagna.")
            key = "gochara_dasha_lord_afflicted"
        elif dignified and strength.satisfied:
            verdict = GocharaVerdict.FAVOURABLE
            explanation = (
                f"{planet} rules the running {' and '.join(levels)}, "
                f"transits the {_ordinal(house)} from the Lagna "
                f"{dignity_words}, and met its Shadbala requirement at "
                f"birth. Phaladīpikā 20.34: it nourishes that bhāva.")
            key = "gochara_dasha_lord_nourishes"
        else:
            verdict = GocharaVerdict.NOT_STATED
            missing = []
            if not dignified:
                missing.append(
                    "its transited rashi is not its own, its exaltation or "
                    "a friend's")
            if strength.satisfied is None:
                missing.append("its natal strength could not be measured")
            explanation = (
                f"{planet} rules the running {' and '.join(levels)} but "
                f"{'; '.join(missing)}. Neither 20.34 nor 20.35 states a "
                f"result for this combination.")
            key = "gochara_dasha_lord_not_stated"

        not_strict: tuple[str, ...] = ()
        if verdict is GocharaVerdict.NOT_STATED:
            not_strict = ("the verses state no result for this combination",)
        elif strength.satisfied is None:
            not_strict = ("the natal-strength condition could not be "
                          "evaluated",)

        out.append(GocharaJudgement(
            rule_id=RULE_DASHA_LORD, transit_planet=planet,
            reference_frame=TransitReference.LAGNA,
            verdict=verdict,
            placement=activation.transit_rule_result,
            vedha=None, activation=activation, natal_strength=strength,
            houses_affected=(house,),
            house_frame=TransitReference.LAGNA,
            source_ref_ids=DASHA_LORD_RULE.source_ref_ids,
            validation_status=DASHA_LORD_RULE.validation_status,
            witness_agreement=DASHA_LORD_RULE.witness_agreement,
            strict_eligible=not not_strict,
            not_strict_because=not_strict,
            explanation=explanation, explanation_key=key,
            explanation_args={"planet": planet, "house": house,
                              "levels": list(levels)},
            limitations=(
                "20.34-35 govern the running daśā lord only. They say "
                "nothing about the other grahas transiting at the same "
                "moment, and this engine claims nothing about them.",)))
    return out


# ── Part 7: the gate ─────────────────────────────────────────────────────────

STRICT_REQUIREMENTS = (
    "source-qualified reference frame",
    "source-qualified transit house rule",
    "vedha implemented where the source states it",
    "dasha condition implemented where the source states it",
    "natal-strength condition implemented where the source states it",
    "implementation matched to the located reading",
    "the rule names a bhava, so a domain can be reached without inference",
)


def strict_eligible_judgements(result: GocharaResult) -> list:
    """
    The judgements strict synthesis may use.

    A located source is not permission. Every clause of `STRICT_REQUIREMENTS`
    has to hold of the RULE, and the judgement has to name a bhāva, before
    anything here reaches a domain.
    """
    return [j for j in result.judgements
            if j.strict_eligible and j.attributes_to_houses
            and j.verdict is not GocharaVerdict.NOT_STATED]


# ── entry point ──────────────────────────────────────────────────────────────

def evaluate_gochara(snapshot, features, *,
                     dasha_stack: Optional[Mapping] = None,
                     nodes_cause_vedha: bool = NODES_CAUSE_VEDHA_DEFAULT
                     ) -> GocharaResult:
    """
    Both located rules, against one transit snapshot.

    Returns every judgement, including the ones that reach no verdict and
    the ones barred from strict. A shorter list would hide the gate's work,
    which is the same reason `filter_results` returns its exclusions.
    """
    if snapshot is None:
        return GocharaResult(methodology_id=METHODOLOGY_ID,
                             notes=["No transit snapshot was supplied."])

    result = GocharaResult(
        methodology_id=METHODOLOGY_ID,
        reference_frames=(TransitReference.MOON, TransitReference.LAGNA))

    if getattr(snapshot, "natal_moon_sign", None) is None:
        result.notes.append(
            "The natal Chandra rashi is unknown, so Phaladīpikā 26 — which "
            "26.1 states must be read from the Chandra — was not evaluated.")
    else:
        result.judgements.extend(evaluate_moon_frame(
            snapshot, nodes_cause_vedha=nodes_cause_vedha))

    if dasha_stack:
        result.judgements.extend(
            evaluate_dasha_lord(snapshot, features, dasha_stack))
    else:
        result.notes.append(
            "No dasha stack was supplied, so Phaladīpikā 20.34-35 — whose "
            "subject is the running dasha lord — was not evaluated. This is "
            "the only implemented rule that can reach a life area, so "
            "without a dasha there is no strict transit evidence at all.")

    result.notes.append(
        NODE_VEDHA_NOTE if nodes_cause_vedha else
        "Rahu and Ketu were excluded from causing vedha by caller request.")

    covered = {j.transit_planet for j in result.judgements}
    result.unevaluated = sorted(
        set(snapshot.positions) - covered)
    return result
