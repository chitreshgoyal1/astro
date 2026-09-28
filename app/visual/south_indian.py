r"""
South Indian kundli layout (V1.8 Parts 19, 20, 21)
====================================================
The square chart: a 4x4 grid with the middle four cells removed, and the
twelve rashis in FIXED positions around the edge.

    +--------+--------+--------+--------+
    | Meena  | Mesha  | Vrisha | Mithun |     Mesha at the top-left-but-one,
    |  12    |   1    |   2    |   3    |     and the signs run CLOCKWISE
    +--------+--------+--------+--------+
    | Kumbha |                 | Karka  |
    |  11    |                 |   4    |
    +--------+     (centre)    +--------+
    | Makara |                 | Simha  |
    |  10    |                 |   5    |
    +--------+--------+--------+--------+
    | Dhanu  | Vrisch | Tula   | Kanya  |
    |   9    |   8    |   7    |   6    |
    +--------+--------+--------+--------+

THE DIFFERENCE THAT MATTERS, AND THE ONE THAT DOES NOT

    In the North Indian chart the HOUSES are fixed on the page and the
    signs move through them; house 1 is always the top diamond. In the
    South Indian chart the SIGNS are fixed and the houses move; Mesha is
    always the same cell, and which cell is the first house depends on the
    Lagna. That is why the North Indian chart prints a rashi number in
    each region and this one prints a house number instead. Each chart
    prints the thing its layout does not already say.

    What does NOT differ is a single placement. Both renderers consume the
    same `ChartVisualModel`, whose houses and bodies were decided upstream
    by the engine. Part 19: "This is PRESENTATION ONLY. Do not recalculate
    houses or signs." There is no arithmetic in this module that could:
    the grid position of a sign is a lookup table, and which sign is in
    which house is a field on the model.

    `tests/test_visual.py` asserts the equivalence directly — every graha,
    in every sign, in every house, identical across both styles — because
    "presentation only" is a claim that has to be checkable.

MARKING THE LAGNA

    A South Indian chart conventionally marks the ascendant cell with a
    diagonal stroke across one corner. That stroke is drawn here, AND the
    cell carries a printed label, because Part 36 forbids encoding status
    by one visual channel alone: a stroke can be lost to a low-quality
    print or an unusual viewer, and a reader who cannot see the chart at
    all gets `Scene.description` instead.
"""

from __future__ import annotations

from typing import Optional

from .model import ChartVisualModel
from .north_indian import (
    COMBUST_MARKER, DIGNITY_MARKERS, FAINT, INK, LAGNA_INK, MARKER_LEGEND,
    RETROGRADE_MARKER, RULE, _body_label, _fit, describe,
)
from .scene import Line, Polygon, Scene, Text

#: Grid cell (row, column) for each rashi index 0-11, Mesha first.
#:
#: This table IS the South Indian chart. It is written out rather than
#: computed from a rotation because a formula that produced eleven correct
#: cells and one wrong one would be very hard to see, and this can be
#: checked against any printed chart in under a minute.
SIGN_CELLS: dict[int, tuple[int, int]] = {
    0: (0, 1),    # Mesha
    1: (0, 2),    # Vrishabha
    2: (0, 3),    # Mithuna
    3: (1, 3),    # Karka
    4: (2, 3),    # Simha
    5: (3, 3),    # Kanya
    6: (3, 2),    # Tula
    7: (3, 1),    # Vrishchika
    8: (3, 0),    # Dhanu
    9: (2, 0),    # Makara
    10: (1, 0),   # Kumbha
    11: (0, 0),   # Meena
}

#: The four cells the chart leaves empty.
CENTRE_CELLS = frozenset({(1, 1), (1, 2), (2, 1), (2, 2)})

#: Fraction of a cell the Lagna's corner stroke spans.
LAGNA_MARK = 0.28


def cell_bounds(row: int, column: int, size: float) -> tuple:
    """Pixel bounds of one grid cell as (x, y, width, height)."""
    step = size / 4.0
    return column * step, row * step, step, step


def render_south_indian(model: ChartVisualModel,
                        size: float = 420.0,
                        font_size: float = 11.0,
                        show_house_numbers: bool = True,
                        title: Optional[str] = None) -> Scene:
    """
    Draw one chart in the South Indian style.

    `show_house_numbers` prints the bhava number in each cell, which is how
    a South Indian chart says which house a sign holds — the signs are
    fixed on the page and the houses move through them. It is the exact
    counterpart of the North Indian renderer's `show_sign_numbers`.
    """
    if model.style != "south_indian":
        raise ValueError(
            f"This layout draws south_indian charts; the model asks for "
            f"'{model.style}'. Chart style is presentation only, so the fix "
            f"is a layout module, never a different calculation.")

    scene = Scene(width=size, height=size, title=title or model.title)
    step = size / 4.0

    scene.add(Polygon(points=((0, 0), (size, 0), (size, size), (0, size)),
                      fill="#ffffff", stroke=RULE, width=1.6))

    # The twelve outer cells, drawn as boxes. The centre is left open: a
    # South Indian chart's middle is where a practitioner writes, and
    # ruling it into four empty boxes would invent a division the chart
    # does not have.
    for row in range(4):
        for column in range(4):
            if (row, column) in CENTRE_CELLS:
                continue
            x, y, width, height = cell_bounds(row, column, size)
            scene.add(Polygon(
                points=((x, y), (x + width, y), (x + width, y + height),
                        (x, y + height)),
                fill=None, stroke=RULE, width=0.9))

    # Sign index → the cell we place it in, and the house it currently is.
    by_sign = {cell.sign_index: cell for cell in model.houses}

    for sign_index, (row, column) in sorted(SIGN_CELLS.items()):
        cell = by_sign.get(sign_index)
        x, y, width, height = cell_bounds(row, column, size)
        centre_x = x + width / 2
        centre_y = y + height / 2

        if cell is None:
            # A model missing a sign is a defect upstream; the chart says
            # so in place rather than drawing a blank that reads as "no
            # grahas here".
            scene.add(Text(x=centre_x, y=centre_y, text="?",
                           size=font_size, colour=FAINT, role="missing"))
            continue

        is_lagna_cell = cell.number == 1
        if is_lagna_cell:
            # The conventional diagonal across the top-left corner, plus a
            # label below. Two channels, per Part 36.
            span = width * LAGNA_MARK
            scene.add(Line(x, y + span, x + span, y,
                           width=1.4, colour=LAGNA_INK))

        if show_house_numbers:
            scene.add(Text(
                x=x + width - font_size * 0.45,
                y=y + font_size * 0.95,
                text=str(cell.number), size=font_size * 0.78,
                colour=FAINT, role="house_number"))

        bodies = cell.bodies
        if not bodies:
            continue
        text_size, line_height = _fit(len(bodies), model.detail, font_size)
        # Bodies are stacked below the house number so the two never
        # collide in a crowded cell.
        top = y + font_size * 1.5
        available = height - (top - y) - font_size * 0.4
        block = (len(bodies) - 1) * line_height
        start = top + max(0.0, (available - block) / 2)
        for index, body in enumerate(bodies):
            scene.add(Text(
                x=centre_x, y=start + index * line_height,
                text=_body_label(body, model.detail),
                size=text_size,
                weight="bold" if body.is_lagna else "normal",
                colour=LAGNA_INK if body.is_lagna else INK,
                role="body"))

    scene.description = describe(model)
    return scene


def house_cell_map(model: ChartVisualModel) -> dict:
    """
    Which grid cell each HOUSE lands in, for tests and for the UI.

    Derived from the model's own sign-to-house assignment, never from a
    rotation computed here — that would be the recalculation Part 19
    forbids, and it would silently disagree with the engine the moment a
    non-whole-sign house system was selected.
    """
    return {cell.number: SIGN_CELLS[cell.sign_index]
            for cell in model.houses if cell.sign_index in SIGN_CELLS}
