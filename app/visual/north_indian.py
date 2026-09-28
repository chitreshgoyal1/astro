r"""
North Indian kundli layout (V1.7 Parts 6, 8, 36)
==================================================
The diamond chart: a square, both diagonals, and the rhombus joining the
midpoints of the sides. Twelve regions, house 1 at the top, counting
anticlockwise.

    +-----------------+
    | \      12|2     /|      1  top kite          7  bottom kite
    |  \  1    |     / |      4  left kite         10 right kite
    | 11 \_____|____/ 3|
    |    /     |    \  |      2, 12  top corners
    | 10 |  C  |  4 |  |      3, 5   left corners
    |    \_____|____/  |      6, 8   bottom corners
    |  9 /     |    \ 5|      9, 11  right corners
    |   /   7  |     \ |
    | /      8 | 6    \|
    +-----------------+

WHAT THIS MODULE DECIDES

    Where to put ink. Nothing else. It is handed a ChartVisualModel whose
    houses are already filled and whose bodies already carry their markers,
    and it has no way to ask which graha belongs where — the model has no
    method that could answer.

CROWDING (Part 8)

    A house can hold seven bodies. The layout measures what it is about to
    draw and reduces the font and the line spacing to fit, rather than
    overflowing the region or silently dropping a graha. A dropped graha
    would be a chart that is wrong in a way the reader cannot see.

COLOUR IS NEVER THE ONLY SIGNAL (Part 36)

    Retrograde is a printed marker. Exaltation and debilitation are printed
    markers. The Lagna is drawn with a label AND a heavier stroke. Every
    chart here remains complete in black and white, and `Scene.description`
    carries the whole thing as text for a reader who cannot see it at all.
"""

from __future__ import annotations

from typing import Optional

from .model import ChartVisualModel
from .scene import Line, Polygon, Scene, Text

#: Markers drawn next to a body. Short ASCII, never colour alone.
#:
#: Arrows and geometric symbols read better on screen, and the PDF's
#: WinAnsi faces cannot print them — they would have to be spelled out, and
#: "Su (moolatrikona)" does not fit inside a house. Two characters fit
#: everywhere, print everywhere, and survive being pasted into a text
#: field. `MARKER_LEGEND` is drawn beneath the chart so they are never a
#: private code, and `describe()` spells every one of them out in full.
DIGNITY_MARKERS = {
    "exalted": "^",
    "debilitated": "v",
    "moolatrikona": "mt",
    "own": "sv",
}

RETROGRADE_MARKER = "R"
COMBUST_MARKER = "c"

MARKER_LEGEND = ("R retrograde, c combust, ^ exalted, v debilitated, "
                 "mt moolatrikona, sv own sign. The small grey number in "
                 "each house is its rashi.")

#: Ink. Kept to greys and one accent so the chart prints correctly.
INK = "#1a1a1a"
RULE = "#33363d"
FAINT = "#8a8f98"
LAGNA_INK = "#8a2b06"


def _polygons(width: float, height: float) -> dict[int, tuple]:
    """
    The twelve regions, in chart coordinates.

    Derived from the four corners and the four edge midpoints. The diagonals
    of the square meet the rhombus at the midpoints of the rhombus's own
    edges, which is what makes the four inner regions kites rather than
    triangles.
    """
    w, h = width, height
    tl, tr, br, bl = (0, 0), (w, 0), (w, h), (0, h)
    top, right, bottom, left = (w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)
    centre = (w / 2, h / 2)
    # Where each diagonal crosses the rhombus.
    m_lt, m_rt = (w / 4, h / 4), (3 * w / 4, h / 4)
    m_rb, m_lb = (3 * w / 4, 3 * h / 4), (w / 4, 3 * h / 4)

    return {
        1:  (m_lt, top, m_rt, centre),
        2:  (top, tl, m_lt),
        3:  (tl, left, m_lt),
        4:  (m_lt, centre, m_lb, left),
        5:  (left, bl, m_lb),
        6:  (bl, bottom, m_lb),
        7:  (m_lb, bottom, m_rb, centre),
        8:  (bottom, br, m_rb),
        9:  (br, right, m_rb),
        10: (m_rt, right, m_rb, centre),
        11: (right, tr, m_rt),
        12: (tr, top, m_rt),
    }


def _centroid(points) -> tuple[float, float]:
    return (sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points))


#: Which square corner each triangular region touches. Two regions share
#: each corner, which is what makes the corner a usable anchor for the
#: rashi number: it separates the number from the body stack without
#: pushing either outside the shape.
_CORNER_OF = {2: "tl", 3: "tl", 5: "bl", 6: "bl",
              8: "br", 9: "br", 11: "tr", 12: "tr"}

#: How far a corner region's text is pulled IN towards the chart centre,
#: as a fraction of its distance from it.
#:
#: Pulling in, not out. The centroid of a corner triangle sits close to the
#: square's edge — house 2's is one twelfth of the way down the page — so a
#: two-line stack centred there overruns the border. Everything about these
#: regions is tight against the outside, and the room is in the middle.
_CORNER_PULL = 0.14

#: How far the rashi number sits from the region centroid, towards the
#: square corner the region touches.
_NUMBER_PULL = 0.45

#: The same, for the four kites, measured from their outer tip inwards.
_KITE_NUMBER_PULL = 0.22


def _towards(point, target, fraction: float) -> tuple[float, float]:
    """Move a point a fraction of the way towards another."""
    return (point[0] + (target[0] - point[0]) * fraction,
            point[1] + (target[1] - point[1]) * fraction)


def _label_anchor(house: int, points, size: float) -> tuple[float, float]:
    """
    Where the stack of bodies is centred inside a region.

    The geometric centroid is right for the four kites and too close to the
    page edge for the eight corner triangles, where a three-line stack runs
    off the chart. Corner regions are pulled in towards the middle, which
    is the only direction with room in them.
    """
    centroid = _centroid(points)
    if house in (1, 4, 7, 10):
        return centroid
    return _towards(centroid, (size / 2, size / 2), _CORNER_PULL)


def _body_label(body, detail: str) -> str:
    """One line of text for one body, with every marker it carries."""
    parts = [body.display]
    if body.retrograde:
        parts.append(RETROGRADE_MARKER)
    marker = DIGNITY_MARKERS.get((body.dignity_marker or "").lower())
    if marker:
        parts.append(marker)
    if body.combust and detail != "COMPACT":
        parts.append(COMBUST_MARKER)
    label = " ".join(parts)
    if detail == "DETAILED" and body.degree is not None:
        label = f"{label} {body.degree:.0f}°"
    return label


def _fit(count: int, detail: str, size: float) -> tuple[float, float]:
    """
    Font size and line height for a house holding `count` bodies.

    Shrinks rather than overflows. Below five bodies nothing changes, so the
    ordinary chart is never penalised for the crowded one.
    """
    base = {"COMPACT": size * 0.78, "STANDARD": size,
            "DETAILED": size * 1.0}[detail]
    if count >= 6:
        base *= 0.62
    elif count == 5:
        base *= 0.74
    elif count == 4:
        base *= 0.86
    return base, base * 1.22


def render_north_indian(model: ChartVisualModel,
                        size: float = 420.0,
                        font_size: float = 11.0,
                        show_sign_numbers: bool = True,
                        title: Optional[str] = None) -> Scene:
    """
    Draw one chart. Returns a Scene; a backend turns it into SVG or PDF.

    `show_sign_numbers` prints the rashi number in each house, which is how
    a North Indian chart says which sign a house holds — the houses are
    fixed on the page and the signs move.
    """
    if model.style != "north_indian":
        raise ValueError(
            f"This layout draws north_indian charts; the model asks for "
            f"'{model.style}'. Chart style is presentation only, so the fix "
            f"is a layout module, never a different calculation.")

    scene = Scene(width=size, height=size, title=title or model.title)
    regions = _polygons(size, size)
    corners = {"tl": (0.0, 0.0), "tr": (size, 0.0),
               "br": (size, size), "bl": (0.0, size)}

    # Frame and dividers.
    scene.add(Polygon(points=((0, 0), (size, 0), (size, size), (0, size)),
                      fill="#ffffff", stroke=RULE, width=1.6))
    scene.add(Line(0, 0, size, size, width=1.0, colour=RULE))
    scene.add(Line(size, 0, 0, size, width=1.0, colour=RULE))
    half = size / 2
    scene.add(Polygon(
        points=((half, 0), (size, half), (half, size), (0, half)),
        fill=None, stroke=RULE, width=1.0))

    for number in range(1, 13):
        cell = model.house(number)
        points = regions[number]
        cx, cy = _label_anchor(number, points, size)

        if show_sign_numbers and cell is not None:
            # The rashi number, small and set apart from the bodies. A North
            # Indian chart's houses are fixed on the page and the signs move
            # through them, so this number is what identifies the sign.
            #
            # A kite takes it just inside its outer tip; a corner triangle
            # takes it towards the square corner it touches. Both are the
            # part of the region the body stack was pulled away from.
            if number in (1, 4, 7, 10):
                nx, ny = _towards(points[1], (size / 2, size / 2),
                                  _KITE_NUMBER_PULL)
            else:
                nx, ny = _towards(_centroid(points),
                                  corners[_CORNER_OF[number]], _NUMBER_PULL)
            scene.add(Text(
                x=nx, y=ny, text=str(cell.sign_index + 1),
                size=font_size * 0.78, colour=FAINT, role="sign_number"))

        bodies = cell.bodies if cell else ()
        if not bodies:
            continue
        text_size, line_height = _fit(len(bodies), model.detail, font_size)
        start = cy - (len(bodies) - 1) * line_height / 2
        for index, body in enumerate(bodies):
            scene.add(Text(
                x=cx, y=start + index * line_height,
                text=_body_label(body, model.detail),
                size=text_size,
                weight="bold" if body.is_lagna else "normal",
                colour=LAGNA_INK if body.is_lagna else INK,
                role="body"))

    scene.description = describe(model)
    return scene


def describe(model: ChartVisualModel) -> str:
    """
    The chart as a sentence, for a reader who cannot see the picture.

    Part 36 asks for a textual equivalent, and this is it: the same twelve
    houses in the same order with the same contents. It is generated from
    the model, so it cannot drift from what was drawn.
    """
    parts = [f"{model.title} for {model.subject or 'this chart'}. "
             f"Lagna in {model.lagna_sign_name}."]
    for cell in model.houses:
        if not cell.bodies:
            continue
        names = ", ".join(
            b.name + (" retrograde" if b.retrograde else "")
            + (f" {b.dignity_marker}" if b.dignity_marker
               and b.dignity_marker != "-" else "")
            for b in cell.bodies)
        parts.append(f"House {cell.number} ({cell.sign_name}): {names}.")
    empty = [str(c.number) for c in model.houses if not c.bodies]
    if empty:
        parts.append("Houses with no graha: " + ", ".join(empty) + ".")
    return " ".join(parts)
