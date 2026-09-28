"""
Varga features (Part 9)
-----------------------
Derived, reusable facts about divisional placements — not just "which sign in
D9", but the standing of the graha there: its lord, whether it is exalted,
debilitated, in its own rashi or moolatrikona in that varga, and whether it is
vargottama.

Every varga position comes from engine.vargas, which computes it from a NAMED
convention. That convention name is carried through onto each placement, so a
feature can always be traced to the tradition that produced it. No convention
is chosen or changed here.

Vargottama: a graha occupying the same rashi in D1 and D9. The term is
sometimes extended to mean the same rashi in D1 and any varga; the narrow and
standard D1=D9 sense is what `vargottama` reports, and the general case is
available through `vargottama_in`.
"""

from __future__ import annotations

from typing import Iterable, Optional

from ..planets import RASHI_NAMES
from ..vargas import VARGA_ORDER, VargaConfig
from .dignity import is_debilitated, is_exalted, is_moolatrikona, is_own_sign
from .models import VargaPlacement

# Vargas the feature layer surfaces by default. The rest are still computed
# and available; these are the ones the report and the rules lean on.
KEY_VARGAS = ("D1", "D9", "D10", "D30", "D60")


def _placement(planet: str, varga_key: str, sign: int, lord: str,
               convention: str, degree_in_varga_sign: float) -> VargaPlacement:
    """
    Standing of a graha in one divisional sign.

    Moolatrikona depends on a degree, and a varga sign has no meaningful
    degree of its own — the graha simply occupies the whole divisional rashi.
    The degree used is therefore the graha's D1 degree within that rashi only
    for D1; for every other varga moolatrikona is reported False rather than
    computed from a quantity that does not exist.
    """
    return VargaPlacement(
        varga=varga_key,
        sign=sign,
        sign_name=RASHI_NAMES[sign % 12],
        lord=lord,
        convention=convention,
        exalted=is_exalted(planet, sign),
        debilitated=is_debilitated(planet, sign),
        own_sign=is_own_sign(planet, sign),
        moolatrikona=(is_moolatrikona(planet, sign, degree_in_varga_sign)
                      if varga_key == "D1" else False),
    )


def compute_varga_features(planet: str,
                           sidereal_longitude: float,
                           config: VargaConfig,
                           vargas: Iterable[str] = VARGA_ORDER
                           ) -> dict[str, VargaPlacement]:
    """Placement and standing of one graha across the requested vargas."""
    degree_in_sign = sidereal_longitude % 30.0
    placements: dict[str, VargaPlacement] = {}
    for key in vargas:
        position = config.compute(key, sidereal_longitude)
        placements[key] = _placement(
            planet=planet,
            varga_key=key,
            sign=position.rashi_index,
            lord=position.rashi_lord,
            convention=position.convention,
            degree_in_varga_sign=degree_in_sign,
        )
    return placements


def is_vargottama(placements: dict[str, VargaPlacement]) -> bool:
    """Same rashi in D1 and D9 — the standard sense of the term."""
    d1 = placements.get("D1")
    d9 = placements.get("D9")
    return d1 is not None and d9 is not None and d1.sign == d9.sign


def vargottama_in(placements: dict[str, VargaPlacement], varga: str) -> bool:
    """Same rashi in D1 and the named varga."""
    d1 = placements.get("D1")
    other = placements.get(varga)
    return d1 is not None and other is not None and d1.sign == other.sign


def vargottama_vargas(placements: dict[str, VargaPlacement]) -> list[str]:
    """Every varga in which the graha repeats its D1 rashi."""
    d1 = placements.get("D1")
    if d1 is None:
        return []
    return [key for key, placement in placements.items()
            if key != "D1" and placement.sign == d1.sign]


def varga_lord(placements: dict[str, VargaPlacement], varga: str) -> Optional[str]:
    placement = placements.get(varga)
    return None if placement is None else placement.lord


def varga_lagna(lagna_longitude: float, config: VargaConfig,
                varga: str) -> VargaPlacement:
    """
    The Lagna's own position in a divisional chart.

    The divisional Lagna is what every other placement in that chart is counted
    from, so it is computed once here rather than being re-derived per graha.
    """
    position = config.compute(varga, lagna_longitude)
    return VargaPlacement(
        varga=varga,
        sign=position.rashi_index,
        sign_name=position.rashi,
        lord=position.rashi_lord,
        convention=position.convention,
    )


def varga_house_of(planet_varga_sign: int, lagna_varga_sign: int) -> int:
    """Whole-sign house of a graha within a divisional chart, 1-12."""
    return ((planet_varga_sign - lagna_varga_sign) % 12) + 1


def vimshopaka_inputs(placements: dict[str, VargaPlacement]) -> dict[str, str]:
    """
    Per-varga dignity labels, the raw material a Vimshopaka Bala calculation
    would consume. The weighting scheme itself is not implemented — see
    AUDIT.md — so this returns inputs, not a strength score.
    """
    return {key: placement.dignity_label() for key, placement in placements.items()}
