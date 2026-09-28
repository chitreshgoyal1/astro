"""
Chart visuals (V1.7 Parts 6, 7, 8)
====================================
    model = build_visual_model(snapshot, varga="D9")   # app/services
    scene = render_north_indian(model)                 # geometry
    svg   = scene_to_svg(scene)                        # one backend

Three steps, each with one job, and none of them astrological. This package
imports nothing from `engine` and `tests/test_app_boundary.py` enforces it:
a renderer that could reach the engine would eventually be asked to decide
something, and the decision would live where nobody looks for it.

Chart style is presentation. Each layout refuses a model asking for
another style rather than drawing it approximately, because a chart in the
wrong style is misread rather than disbelieved. The fix for a new style is
a new layout module reading the same model — never a change to how the
placements were computed, and V1.8's South Indian layout is exactly that:
a second reader of one model, with `render_chart` dispatching between them.

`east_indian` is still named and still refused. Naming an unimplemented
style is what makes the refusal specific.
"""

from .model import (
    CHART_STYLES, DETAIL_LEVELS, ChartVisualModel, HouseCell, PlacedBody,
)
from .north_indian import MARKER_LEGEND, describe, render_north_indian
from .scene import Line, Polygon, Rect, Scene, Text
from .south_indian import SIGN_CELLS, house_cell_map, render_south_indian
from .styles import (
    IMPLEMENTED_STYLES, STYLE_LABELS, UnsupportedChartStyle, render_chart,
    style_label,
)
from .svg import scene_to_svg, scene_to_svg_document

__all__ = [
    "CHART_STYLES", "ChartVisualModel", "DETAIL_LEVELS", "HouseCell",
    "IMPLEMENTED_STYLES", "Line", "MARKER_LEGEND", "PlacedBody", "Polygon",
    "Rect", "SIGN_CELLS", "STYLE_LABELS", "Scene", "Text",
    "UnsupportedChartStyle", "describe", "house_cell_map", "render_chart",
    "render_north_indian", "render_south_indian", "scene_to_svg",
    "scene_to_svg_document", "style_label",
]
