"""
Vedha (V1.8 Part 4)
---------------------
Obstruction, as a layer in its own right.

WHY THIS IS NOT A BOOLEAN

    Part 4: "Do not bury it inside one boolean expression." The reason is
    that three different situations all produce "this transit is not
    obstructed", and a caller that cannot tell them apart will eventually
    report the wrong one:

        the vedha house is empty
        the vedha house holds only a graha the verse exempts
        the graha has no vedha table at all

    The first is a finding, the second is a finding WITH A NAMED EXCEPTION
    that the verse states, and the third is a gap in the source. `VedhaResult`
    distinguishes them; a boolean cannot.

WHAT COUNTS AS AN OBSTRUCTING GRAHA

    The verses say `khecharaiḥ` and `grahaiḥ` — sky-goers, grahas. In
    Jyotiṣa usage that is the nine, and 26.2 itself treats Rāhu and Ketu as
    transiting grahas with results of their own. So the nodes obstruct.

    This is the one place in the chapter-26 implementation where the text is
    read rather than merely transcribed, and it is recorded as such: the
    decision is named, defaulted, and queued for human review. It is not
    hidden in a membership test.
"""

from __future__ import annotations

from typing import Mapping, Optional

from .models import GocharaRule, VedhaResult

# The named methodology decision described above. A caller may turn it off;
# nothing in the engine does so silently, and `GocharaResult.notes` records
# which way it was set on every run.
NODES_CAUSE_VEDHA_DEFAULT = True

NODE_VEDHA_NOTE = (
    "The verses name the obstructing bodies `khecharaiḥ`/`grahaiḥ`. Rāhu "
    "and Ketu are counted among them here, because 26.2 treats the nodes as "
    "transiting grahas with results of their own. Neither witness settles "
    "it explicitly; see the review queue.")


def evaluate_vedha(rule: GocharaRule, house: int,
                   houses_by_planet: Mapping[str, Optional[int]], *,
                   nodes_cause_vedha: bool = NODES_CAUSE_VEDHA_DEFAULT
                   ) -> VedhaResult:
    """
    Whether the graha's favourable transit of `house` is obstructed.

    `houses_by_planet` maps every transiting graha to its house in the SAME
    reference frame the rule declares. Passing houses from the Lagna to a
    Moon-frame rule would produce a confident wrong answer, so the caller
    builds this mapping from `rule.reference_frame` rather than from a
    default — see `engine.gochara.engine._frame_houses`.
    """
    vedha_house = rule.vedha_house_for(house)
    if vedha_house is None:
        return VedhaResult(
            transit_planet=rule.planet, transit_house=house,
            vedha_house=None, blocking_condition_present=False,
            source_ref_ids=rule.source_ref_ids,
            explanation=(
                f"No vedha house is stated for {rule.planet} in the "
                f"{_ordinal(house)}."))

    exempt = set(rule.vedha_exempt_planets)
    blocking: list[str] = []
    exempted: list[str] = []

    for planet, occupied in sorted(houses_by_planet.items()):
        if occupied != vedha_house or planet == rule.planet:
            # A graha cannot obstruct itself: it is standing in the
            # favourable house, so it is not standing in the vedha house.
            # The test is vacuous and kept for the reader rather than the
            # arithmetic.
            continue
        if not nodes_cause_vedha and planet in ("Rahu", "Ketu"):
            exempted.append(planet)
            continue
        if planet in exempt:
            exempted.append(planet)
            continue
        blocking.append(planet)

    exception = None
    if exempted and not blocking:
        exception = rule.exemption_reason or NODE_VEDHA_NOTE

    if blocking:
        explanation = (
            f"{', '.join(blocking)} occupies the {_ordinal(vedha_house)}, "
            f"which obstructs {rule.planet} in the {_ordinal(house)}.")
    elif exempted:
        explanation = (
            f"{', '.join(exempted)} occupies the {_ordinal(vedha_house)} and "
            f"the verse exempts it, so {rule.planet} in the "
            f"{_ordinal(house)} is not obstructed.")
    else:
        explanation = (
            f"The {_ordinal(vedha_house)} is unoccupied, so {rule.planet} in "
            f"the {_ordinal(house)} is not obstructed.")

    return VedhaResult(
        transit_planet=rule.planet, transit_house=house,
        vedha_house=vedha_house,
        blocking_condition_present=bool(blocking),
        blocking_planet=blocking[0] if blocking else None,
        blocking_planets=tuple(blocking),
        exception_applied=exception,
        exempted_planets=tuple(exempted),
        source_ref_ids=rule.source_ref_ids,
        explanation=explanation)


def vedha_table() -> dict:
    """Every stated pair, for the methodology screen and the report."""
    from .rules import MOON_FRAME_RULES, NODE_RULES

    return {
        "reference_frame": "MOON",
        "nodes_cause_vedha_default": NODES_CAUSE_VEDHA_DEFAULT,
        "node_decision_note": NODE_VEDHA_NOTE,
        "pairs": {
            rule.planet: {
                "favourable": list(rule.favourable_houses),
                "vedha": [rule.vedha_pairs[h] for h in rule.favourable_houses]
                if rule.vedha_pairs else [],
                "exempt": list(rule.vedha_exempt_planets),
            }
            for rule in MOON_FRAME_RULES + NODE_RULES},
    }


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"
