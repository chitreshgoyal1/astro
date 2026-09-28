"""
Chart style dispatch (V1.8 Parts 20, 21)
------------------------------------------
One entry point that picks a layout, and refuses the ones that do not exist.

WHY A DISPATCHER RATHER THAN A CALLER-SIDE `if`

    Before V1.8 there was one layout, so every caller named it directly:
    `render_north_indian(model)` appears in the report service, the
    benchmark, the UI and the tests. Adding a second style that way would
    have put the same two-branch conditional in four places, and the
    fourth copy is the one that never learns about the third style.

    So the branch lives here once, the caller passes the model's own
    `style`, and adding a layout is one entry in `_RENDERERS`.

WHY EAST INDIAN IS STILL REFUSED

    Part 20: "Keep EAST_INDIAN refused unless correctly implemented." The
    East Indian (Bengali/Odia) chart is not a relabelling of either
    implemented style — it is a square divided differently again, and
    approximating it with the North Indian geometry would produce a chart
    that is confidently wrong to the readers who use it, which is the
    failure mode this whole module exists to prevent.

    It stays in `CHART_STYLES` so that asking for it produces a named
    refusal rather than a KeyError, and so that this file records what is
    missing rather than the absence being invisible.
"""

from __future__ import annotations

from typing import Optional

from .model import CHART_STYLES, ChartVisualModel
from .north_indian import render_north_indian
from .scene import Scene
from .south_indian import render_south_indian


class UnsupportedChartStyle(ValueError):
    """A named style this build cannot draw correctly."""


_RENDERERS = {
    "north_indian": render_north_indian,
    "south_indian": render_south_indian,
}

#: Styles that can actually be drawn.
IMPLEMENTED_STYLES = tuple(sorted(_RENDERERS))

STYLE_LABELS = {
    "north_indian": "North Indian",
    "south_indian": "South Indian",
    "east_indian": "East Indian",
}

#: What each implemented style prints in each region, because the two
#: layouts hold different things fixed. Surfaced so the UI and the report
#: can explain the chart the reader is looking at rather than assuming
#: they already know which convention they were given.
STYLE_NOTES = {
    "north_indian": (
        "The houses are fixed on the page — house 1 is always the top "
        "diamond — and the signs move through them, so each region prints "
        "its rashi number."),
    "south_indian": (
        "The signs are fixed on the page — Mesha is always the same cell — "
        "and the houses move through them, so each cell prints its bhava "
        "number and the Lagna cell is marked."),
}


def style_label(style: str) -> str:
    return STYLE_LABELS.get(style, style)


def render_chart(model: ChartVisualModel, **kwargs) -> Scene:
    """
    Draw `model` in whichever style it asks for.

    Refuses a style this build cannot draw, naming it. A chart drawn in
    the wrong style is misread rather than disbelieved, so an
    approximation is never the fallback.
    """
    renderer = _RENDERERS.get(model.style)
    if renderer is None:
        if model.style in CHART_STYLES:
            raise UnsupportedChartStyle(
                f"The {style_label(model.style)} chart is a named style "
                f"this build does not draw. It is not a relabelling of an "
                f"implemented layout, so it is refused rather than "
                f"approximated. Available: "
                f"{', '.join(style_label(s) for s in IMPLEMENTED_STYLES)}.")
        raise UnsupportedChartStyle(
            f"'{model.style}' is not a chart style. Available: "
            f"{', '.join(style_label(s) for s in IMPLEMENTED_STYLES)}.")
    return renderer(model, **kwargs)


def style_note(style: str) -> str:
    return STYLE_NOTES.get(style, "")


def describe_styles() -> list[dict]:
    """Every named style and whether it can be drawn. For the UI."""
    return [
        {
            "id": style,
            "label": style_label(style),
            "implemented": style in _RENDERERS,
            "note": STYLE_NOTES.get(style, ""),
        }
        for style in CHART_STYLES
    ]
