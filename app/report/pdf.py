"""
PDF writer (V1.7 Parts 7, 21, 22, 23)
=======================================
A professional report: A4, real typography, tables that fit, vector kundlis,
running headers, page numbers, and a page break that falls where it should.

NO THIRD-PARTY LIBRARY, AND NO NETWORK

    The whole pipeline has to run offline (Part 34), and this repository has
    one dependency, which is an ephemeris used for validation. So the file
    is assembled here: object table, content streams, cross-reference table.
    V1's report writer already did this for monospaced text; this one adds
    proportional faces, measured text, vector graphics and pagination.

    The base-14 faces are NOT embedded. A conforming viewer supplies them,
    which keeps a report around 30 KB instead of 400 KB and means it opens
    on a machine with no fonts installed beyond its own. Measuring is done
    from the committed metrics table in app/report/metrics.py.

WHAT IT REFUSES TO DO

    It draws a ReportDocument and nothing else. It cannot read a chart, a
    snapshot or an engine object, and it has no access to one: every value
    it prints is a string another layer already decided on. If a number
    looks wrong in a PDF, the defect is upstream of this file.

TWO PASSES, FOR ONE REASON

    "Page 3 of 11" cannot be written until the document has been laid out,
    and laying out is what determines 11. So layout runs first into page
    buffers, then the furniture is drawn onto each finished page. Nothing
    else is deferred, because anything else deferred would be a place where
    two passes could disagree.
"""

from __future__ import annotations

import datetime
import zlib
from typing import Optional, Sequence

from ..version import user_agent
from .devanagari import script_runs
from .embed import devanagari_font, needs_shaping, reset_embedded_fonts
from .metrics import text_width as _latin_width

# ── page geometry ────────────────────────────────────────────────────────────

PAGE_SIZES = {
    "a4": (595.28, 841.89),
    "letter": (612.0, 792.0),
}

MARGIN_LEFT = 56.0
MARGIN_RIGHT = 56.0
MARGIN_TOP = 64.0
MARGIN_BOTTOM = 62.0

#: Space reserved below the text block for the footer rule and page number.
FOOTER_HEIGHT = 26.0
HEADER_HEIGHT = 22.0

# ── typography ───────────────────────────────────────────────────────────────
#
# One serif family for reading and one sans for structure. Mixing more than
# two families in a report of this length makes it look assembled rather
# than designed, and there is no third distinction to carry.

FACE_BODY = "Times-Roman"
FACE_BODY_BOLD = "Times-Bold"
FACE_BODY_ITALIC = "Times-Italic"
FACE_HEAD = "Helvetica-Bold"
FACE_LABEL = "Helvetica"

#: style name -> (face, size, leading, space_before, space_after)
STYLES = {
    "title":   (FACE_BODY_BOLD, 26.0, 30.0, 0.0, 14.0),
    "lead":    (FACE_BODY, 11.5, 15.5, 2.0, 7.0),
    "body":    (FACE_BODY, 9.8, 13.2, 0.0, 6.5),
    "note":    (FACE_BODY_ITALIC, 9.0, 12.2, 2.0, 6.0),
    "small":   (FACE_BODY_ITALIC, 8.2, 11.0, 2.0, 5.0),
    "h1":      (FACE_HEAD, 17.0, 21.0, 0.0, 9.0),
    "h2":      (FACE_HEAD, 12.0, 15.0, 11.0, 5.0),
    "h3":      (FACE_HEAD, 10.0, 13.0, 8.0, 4.0),
    "caption": (FACE_HEAD, 8.6, 11.0, 7.0, 3.0),
    "cell":    (FACE_BODY, 8.6, 10.8, 0.0, 0.0),
    "cellhead": (FACE_HEAD, 8.2, 10.4, 0.0, 0.0),
    "footer":  (FACE_LABEL, 7.6, 9.0, 0.0, 0.0),
}

INK = (0.10, 0.10, 0.11)
MUTED = (0.42, 0.44, 0.47)
RULE = (0.78, 0.79, 0.81)
CALLOUT_BG = (0.965, 0.962, 0.952)
WARNING_BAR = (0.62, 0.30, 0.05)
LIMIT_BAR = (0.30, 0.33, 0.38)

#: IAST to plain Latin. The Sanskrit citations carry full diacritics —
#: `Bṛhat Pārāśara Horā Śāstra` — and WinAnsi has glyphs for almost none of
#: them, so without this every witness in the source appendix prints as
#: `B?hat P?r???ara Hor? ??stra`.
#:
#: Losing the diacritics loses information: `śa` and `ṣa` are different
#: sounds and this spelling cannot tell them apart. That is a real cost,
#: and it is smaller than the alternative, which is a page of question
#: marks that reads as a broken program. The SVG and HTML output keep the
#: diacritics, because their encoding can carry them.
IAST_TO_ASCII = {
    "ā": "a", "Ā": "A",        # ā
    "ī": "i", "Ī": "I",        # ī
    "ū": "u", "Ū": "U",        # ū
    "ṛ": "r", "Ṛ": "R",        # ṛ
    "ṝ": "r", "Ṝ": "R",        # ṝ
    "ḷ": "l", "Ḷ": "L",        # ḷ
    "ṃ": "m", "Ṃ": "M",        # ṃ
    "ṁ": "m", "Ṁ": "M",        # ṁ
    "ḥ": "h", "Ḥ": "H",        # ḥ
    "ś": "s", "Ś": "S",        # ś
    "ṣ": "s", "Ṣ": "S",        # ṣ
    "ṭ": "t", "Ṭ": "T",        # ṭ
    "ḍ": "d", "Ḍ": "D",        # ḍ
    "ṇ": "n", "Ṇ": "N",        # ṇ
    "ń": "n", "Ń": "N",        # ń
    "ñ": "ñ",                  # ñ — WinAnsi has this one
    "ṟ": "r", "ṅ": "n", "Ṅ": "N",
}

#: Characters with no WinAnsi glyph, spelled out instead.
#:
#: The chart markers are the interesting case. `↑` means exalted and the
#: reader of a screen has a legend beside it; a reader of a printed page may
#: not, and a glyph that fails to render is read as a defect in the
#: calculation rather than in the font. So they become words.
TRANSLITERATE = {
    "↑": " (exalted)", "↓": " (debilitated)",
    "△": " (moolatrikona)", "○": " (own sign)",
    "℞": "R", "◆": "*", "⚠": "!", "✗": "x",
    "✓": "v", "→": "->", "Δ": "Delta ", "λ": "lambda",
    "β": "beta", "\U0001f64f": "", "\U0001f4cb": "", "\U0001f52e": "",
    "\U0001f4dd": "", "\U0001f4c4": "",
}

#: Unicode code point to WinAnsi byte, for the 27 characters where WinAnsi
#: differs from Latin-1 — the smart quotes, the dashes, the ellipsis. Built
#: from cp1252 rather than typed out, because cp1252 IS WinAnsi.
_IAST_TABLE = str.maketrans(IAST_TO_ASCII)

_WINANSI_HIGH = {}
for _byte in range(0x80, 0xA0):
    try:
        _WINANSI_HIGH[ord(bytes([_byte]).decode("cp1252"))] = _byte
    except (UnicodeDecodeError, TypeError):    # five undefined positions
        continue


class PdfUnsupportedText(ValueError):
    """
    Text no face available to this writer can represent.

    THE HINDI PDF LIMIT, AND ITS REMOVAL (V1.7 Parts 24, 34; V1.8 Part 16)

        V1.7 refused Hindi PDFs. The base-14 faces are Latin, so a Hindi
        report rendered into them came out as a page of question marks —
        a document that looks like a broken program rather than an
        unsupported feature. Refusing was right, and the refusal named
        what was missing: an embedded Devanagari font AND a shaper,
        because Devanagari is not a matter of swapping glyphs.

        V1.8 built both. `app/report/devanagari.py` implements the
        OpenType Indic v2 model — reordering, conjuncts, reph, mark
        attachment — and `app/report/embed.py` subsets and embeds an OFL
        licensed face. `कार्य` now renders as the four shapes it is, with
        the ra raised into a reph above the ya.

        WHAT STILL RAISES THIS. Any character that is neither
        representable in WinAnsi nor covered by the bundled Devanagari
        font — Tamil, Bengali, CJK. The refusal is narrower than it was
        and it is the same refusal: a script this writer cannot shape is
        named, not approximated.

    Detected by `scan_unsupported`, which counts characters no available
    face can carry.
    """


def to_winansi(text: str) -> str:
    """
    Map a string onto the WinAnsi byte values, as characters.

    IDEMPOTENT, DELIBERATELY. The result contains only code points below
    256, each equal to the byte the PDF will carry, so measuring can index
    the metrics table with `ord()` and a second pass over already-converted
    text changes nothing. Several call paths convert, wrap, then measure
    again, and a conversion that was not idempotent would mangle every
    em-dash on the second pass.
    """
    for src, dst in TRANSLITERATE.items():
        if src in text:
            text = text.replace(src, dst)
    text = text.translate(_IAST_TABLE)
    out = []
    for char in text:
        point = ord(char)
        if point < 256:
            out.append(char)               # Latin-1 and WinAnsi agree here
        elif point in _WINANSI_HIGH:
            out.append(chr(_WINANSI_HIGH[point]))
        else:
            out.append("?")
    return "".join(out)


def _escape(text: str) -> str:
    return (text.replace("\\", r"\\").replace("(", r"\(")
            .replace(")", r"\)"))


def sanitise_metadata(value: str, limit: int = 200) -> str:
    """
    A string fit for a PDF Info dictionary.

    Part 45: "Sanitize metadata." Escaping alone is not enough here.
    A newline inside a string object is LEGAL PDF and survives escaping,
    so a pasted multi-line name produces a document whose title spans
    lines in every reader that shows it; a null byte is not legal and
    some readers stop at it, silently truncating the title.

    Neither is a code-execution risk — this is tidiness and robustness,
    not a vulnerability — and both arrive from an ordinary paste. Control
    characters become spaces rather than being deleted, so the words on
    either side do not run together.
    """
    cleaned = "".join(
        " " if (ord(ch) < 0x20 or ord(ch) == 0x7F) else ch
        for ch in value)
    cleaned = " ".join(cleaned.split())
    return cleaned[:limit]


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


# ── canvas ───────────────────────────────────────────────────────────────────

class Page:
    """One page's content stream, built as a list of operator strings."""

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        self.ops: list[str] = []
        #: Filled in by the furniture pass.
        self.section_title = ""

    # All drawing takes y measured DOWN from the top of the page; the flip
    # happens here, once, so no layout code has to think about it.
    def _y(self, y: float) -> float:
        return self.height - y

    def text(self, x: float, y: float, value: str, face: str, size: float,
             colour=INK, anchor: str = "start") -> None:
        if needs_shaping(value):
            # Mixed lines are drawn run by run, each in the face that can
            # draw it. The anchor is resolved against the WHOLE line first,
            # so a centred mixed heading centres on its real width rather
            # than on its Devanagari part.
            runs = script_runs(value)
            total = sum(text_width(part, face, size) for _deva, part in runs)
            if anchor == "end":
                x -= total
            elif anchor != "start":
                x -= total / 2
            for is_devanagari, part in runs:
                if is_devanagari:
                    self._devanagari(x, y, part, size, colour, "start")
                else:
                    self.text(x, y, part, face, size, colour, "start")
                x += text_width(part, face, size)
            return
        printable = to_winansi(value)
        if not printable.strip():
            return
        if anchor != "start":
            width = text_width(printable, face, size)
            x -= width if anchor == "end" else width / 2
        r, g, b = colour
        self.ops.append(
            f"BT /{_FACE_IDS[face]} {_fmt(size)} Tf "
            f"{_fmt(r)} {_fmt(g)} {_fmt(b)} rg "
            f"{_fmt(x)} {_fmt(self._y(y) - size * 0.32)} Td "
            f"({_escape(printable)}) Tj ET")

    def _devanagari(self, x: float, y: float, value: str, size: float,
                    colour, anchor: str) -> None:
        """
        Draw a shaped Devanagari run.

        The content stream carries GLYPH IDS, not characters, because
        shaping has already decided which shapes appear and in what
        order. Runs of glyphs whose vertical offset is zero go into one
        TJ array with horizontal adjustments between them; a glyph that
        needs a vertical offset gets its own positioned block, since TJ
        can only move the pen along the baseline.
        """
        if not value.strip():
            return
        font = devanagari_font()
        glyphs = font.shape(value)
        if not glyphs:
            return

        scale = size / font.units_per_em
        width = sum(glyph.x_advance for glyph in glyphs) * scale
        if anchor != "start":
            x -= width if anchor == "end" else width / 2

        red, green, blue = colour
        baseline = self._y(y) - size * 0.32
        prefix = (f"BT /{DEVANAGARI_FACE_ID} {_fmt(size)} Tf "
                  f"{_fmt(red)} {_fmt(green)} {_fmt(blue)} rg ")

        pen = x
        parts: list[str] = []

        def flush() -> None:
            if parts:
                self.ops.append(
                    prefix + f"{_fmt(pen_start[0])} {_fmt(baseline)} Td "
                    + "[" + "".join(parts) + "] TJ ET")
                parts.clear()

        pen_start = [x]
        for glyph in glyphs:
            if glyph.y_offset:
                flush()
                pen_start[0] = pen
                self.ops.append(
                    prefix
                    + f"{_fmt(pen + glyph.x_offset * scale)} "
                    f"{_fmt(baseline + glyph.y_offset * scale)} Td "
                    f"<{glyph.glyph:04X}> Tj ET")
                pen += glyph.x_advance * scale
                pen_start[0] = pen
                continue
            if glyph.x_offset:
                # A TJ number moves the pen LEFT by value/1000 of the font
                # size, so shifting a glyph right takes a negative number
                # and the shift is undone after it — the advance the
                # shaper reported already accounts for the offset.
                parts.append(f"{-_thousandths(glyph.x_offset, font)}")
                parts.append(f"<{glyph.glyph:04X}>")
                parts.append(f"{_thousandths(glyph.x_offset, font)}")
            else:
                parts.append(f"<{glyph.glyph:04X}>")
            pen += glyph.x_advance * scale
        flush()

    def line(self, x1, y1, x2, y2, width=0.6, colour=RULE) -> None:
        r, g, b = colour
        self.ops.append(
            f"{_fmt(r)} {_fmt(g)} {_fmt(b)} RG {_fmt(width)} w "
            f"{_fmt(x1)} {_fmt(self._y(y1))} m "
            f"{_fmt(x2)} {_fmt(self._y(y2))} l S")

    def rect(self, x, y, w, h, fill=None, stroke=None, width=0.6) -> None:
        ops = []
        if fill:
            ops.append(f"{_fmt(fill[0])} {_fmt(fill[1])} {_fmt(fill[2])} rg")
        if stroke:
            ops.append(f"{_fmt(stroke[0])} {_fmt(stroke[1])} "
                       f"{_fmt(stroke[2])} RG {_fmt(width)} w")
        ops.append(f"{_fmt(x)} {_fmt(self._y(y + h))} {_fmt(w)} {_fmt(h)} re")
        ops.append("B" if (fill and stroke) else ("f" if fill else "S"))
        self.ops.append(" ".join(ops))

    def polygon(self, points, fill=None, stroke=None, width=0.6) -> None:
        if len(points) < 2:
            return
        ops = []
        if fill:
            ops.append(f"{_fmt(fill[0])} {_fmt(fill[1])} {_fmt(fill[2])} rg")
        if stroke:
            ops.append(f"{_fmt(stroke[0])} {_fmt(stroke[1])} "
                       f"{_fmt(stroke[2])} RG {_fmt(width)} w")
        first = points[0]
        ops.append(f"{_fmt(first[0])} {_fmt(self._y(first[1]))} m")
        for x, y in points[1:]:
            ops.append(f"{_fmt(x)} {_fmt(self._y(y))} l")
        ops.append("h")
        ops.append("B" if (fill and stroke) else ("f" if fill else "S"))
        self.ops.append(" ".join(ops))

    def stream(self) -> bytes:
        return "\n".join(self.ops).encode("latin-1", "replace")


#: PDF resource names for the faces this writer uses.
_FACE_IDS = {
    "Times-Roman": "F1", "Times-Bold": "F2", "Times-Italic": "F3",
    "Helvetica": "F4", "Helvetica-Bold": "F5", "Helvetica-Oblique": "F6",
}

#: The embedded Devanagari face. One resource name for every weight,
#: because the bundled family ships a single Regular instance — a bold
#: heading in Hindi is set in the regular face rather than in a synthesised
#: bold, which would be a fake the reader could not distinguish from a real
#: one.
DEVANAGARI_FACE_ID = "F7"


def _thousandths(font_units: int, font) -> int:
    return round(font_units * 1000.0 / font.units_per_em)


# ── text measurement and wrapping ────────────────────────────────────────────

def text_width(text: str, face: str, size: float) -> float:
    """
    Measured width of a string in one face.

    Devanagari is routed through the shaper, because its width is not the
    sum of its characters' widths: `क्ष` is three codepoints and one
    glyph, and measuring it as three would wrap the line early and leave
    a ragged column that looks like a layout bug.
    """
    if needs_shaping(text):
        return sum(
            devanagari_font().width(part, size) if is_devanagari
            else _latin_width(to_winansi(part), face, size)
            for is_devanagari, part in script_runs(text))
    # MEASURED ON WHAT IS DRAWN. `Page.text` converts to WinAnsi before
    # emitting, and the metrics table is indexed by byte value, so
    # measuring the unconverted string gives an em-dash — and every other
    # character above U+00FF — a width of zero. The symptom is a line that
    # looks a word too long and a run that starts in the wrong place.
    return _latin_width(to_winansi(text), face, size)


def wrap(text: str, face: str, size: float, width: float) -> list[str]:
    """
    Greedy word wrap to a measured width.

    Greedy rather than Knuth-Plass: the difference shows in justified text
    and nothing here is justified, so the extra machinery would buy a
    rag-right column that looks the same.
    """
    # Devanagari is left alone: `to_winansi` would turn every character
    # into a question mark, and the shaper needs the original codepoints.
    if not needs_shaping(text):
        text = to_winansi(text)
    if not text:
        return []
    lines: list[str] = []
    for hard_line in text.split("\n"):
        words = hard_line.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if text_width(trial, face, size) <= width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _shrink_to_fit(text: str, face: str, size: float, width: float) -> str:
    """
    Truncate a single-line cell that cannot fit, with an ellipsis.

    Used only in table cells, where wrapping is already done and a value
    still overruns — a long place name, usually. Truncation is visible;
    overlap is not, and overlapping text in a table reads as two values.
    """
    if not needs_shaping(text):
        text = to_winansi(text)
    if text_width(text, face, size) <= width:
        return text
    ellipsis = "…"
    while text and text_width(text + ellipsis, face, size) > width:
        text = text[:-1]
    return text + ellipsis


# ── layout ───────────────────────────────────────────────────────────────────

class Layout:
    """
    A cursor walking down pages, placing blocks.

    Every `draw_*` method leaves the cursor below what it drew and starts a
    new page when what it is about to draw will not fit. The one place that
    is subtle is a table: a row is atomic, a table is not, and the header is
    repeated when one breaks. A row split across a page boundary is how a
    number ends up read against the wrong label.
    """

    def __init__(self, page_size: str = "a4", title: str = "",
                 subject: str = ""):
        self.width, self.height = PAGE_SIZES.get(page_size, PAGE_SIZES["a4"])
        self.pages: list[Page] = []
        self.title = title
        self.subject = subject
        self.section_title = ""
        self.page: Optional[Page] = None
        self.y = 0.0
        self.new_page()

    # ── page management ────────────────────────────────────────────────────
    @property
    def left(self) -> float:
        return MARGIN_LEFT

    @property
    def right(self) -> float:
        return self.width - MARGIN_RIGHT

    @property
    def column_width(self) -> float:
        return self.right - self.left

    @property
    def bottom(self) -> float:
        return self.height - MARGIN_BOTTOM - FOOTER_HEIGHT

    def new_page(self) -> Page:
        self.page = Page(self.width, self.height)
        self.page.section_title = self.section_title
        self.pages.append(self.page)
        self.y = MARGIN_TOP + HEADER_HEIGHT
        return self.page

    def space_left(self) -> float:
        return self.bottom - self.y

    def need(self, height: float) -> None:
        """Start a new page if `height` will not fit on this one."""
        if self.y + height > self.bottom:
            self.new_page()

    def gap(self, height: float) -> None:
        self.y += height

    # ── blocks ─────────────────────────────────────────────────────────────
    def draw_text(self, text: str, style: str = "body",
                  colour=INK, indent: float = 0.0,
                  width: Optional[float] = None) -> None:
        face, size, leading, before, after = STYLES[style]
        available = (width if width is not None
                     else self.column_width - indent)
        lines = wrap(text, face, size, available)
        if not lines:
            return
        self.y += before
        for line in lines:
            # An orphaned final line is worth a page break; an orphaned
            # first line is worse, so the whole paragraph moves when only
            # one line would be left behind.
            self.need(leading)
            self.page.text(self.left + indent, self.y, line, face, size,
                           colour)
            self.y += leading
        self.y += after

    def draw_heading(self, text: str, level: int = 2) -> None:
        style = {1: "h1", 2: "h2", 3: "h3"}.get(level, "h3")
        face, size, leading, before, after = STYLES[style]
        # A heading with nothing under it is worse than a short page.
        self.need(leading + before + 34.0)
        self.y += before
        self.page.text(self.left, self.y, text, face, size, INK)
        self.y += leading
        if level <= 2:
            self.page.line(self.left, self.y - 3, self.right, self.y - 3,
                           width=0.5)
        self.y += after

    def draw_bullets(self, items: Sequence[str], caption: str = "") -> None:
        if caption:
            self.draw_caption(caption)
        face, size, leading, _, after = STYLES["body"]
        for item in items:
            lines = wrap(item, face, size, self.column_width - 14.0)
            for index, line in enumerate(lines):
                self.need(leading)
                if index == 0:
                    self.page.text(self.left + 3, self.y, "•", face,
                                   size, MUTED)
                self.page.text(self.left + 14, self.y, line, face, size, INK)
                self.y += leading
            self.y += 1.4
        self.y += after

    def draw_caption(self, text: str) -> None:
        face, size, leading, before, after = STYLES["caption"]
        self.need(leading + before + 20.0)
        self.y += before
        self.page.text(self.left, self.y, text, face, size, MUTED)
        self.y += leading + after

    def draw_keyvalues(self, pairs, caption: str = "",
                       notes: Sequence[str] = ()) -> None:
        if caption:
            self.draw_caption(caption)
        label_face, label_size, leading, _, _ = STYLES["cell"]
        label_width = max(
            [text_width(k, FACE_LABEL, label_size)
             for k, _ in pairs] or [80.0]) + 14.0
        label_width = min(label_width, self.column_width * 0.42)
        for key, value in pairs:
            lines = wrap(str(value), label_face, label_size,
                         self.column_width - label_width)
            self.need(leading * max(1, len(lines)))
            self.page.text(self.left, self.y, key, FACE_LABEL, label_size,
                           MUTED)
            for index, line in enumerate(lines or [""]):
                self.page.text(self.left + label_width, self.y, line,
                               label_face, label_size, INK)
                self.y += leading
        self.y += 4.0
        for note in notes:
            self.draw_text(note, "small", MUTED)

    def draw_callout(self, text: str, kind: str = "note",
                     title: str = "") -> None:
        face, size, leading, _, _ = STYLES["body"]
        pad = 8.0
        inner = self.column_width - pad * 2 - 4.0
        lines = wrap(text, face, size, inner)
        title_lines = wrap(title, FACE_HEAD, size, inner) if title else []
        height = pad * 2 + leading * (len(lines) + len(title_lines))
        # A callout is a unit: half a warning box at the foot of a page
        # reads as the whole warning.
        self.need(height + 6.0)
        top = self.y
        self.page.rect(self.left, top, self.column_width, height,
                       fill=CALLOUT_BG, stroke=None)
        bar = {"warning": WARNING_BAR, "limit": LIMIT_BAR}.get(kind, MUTED)
        self.page.rect(self.left, top, 2.6, height, fill=bar, stroke=None)
        y = top + pad
        for line in title_lines:
            self.page.text(self.left + pad + 4, y, line, FACE_HEAD, size, INK)
            y += leading
        for line in lines:
            self.page.text(self.left + pad + 4, y, line, face, size, INK)
            y += leading
        self.y = top + height + 8.0

    def draw_table(self, columns, rows, widths=(), align=(), caption="",
                   compact: bool = False) -> None:
        if caption:
            self.draw_caption(caption)
        head_face, head_size, head_leading, _, _ = STYLES["cellhead"]
        cell_face, cell_size, cell_leading, _, _ = STYLES["cell"]
        if compact:
            cell_size *= 0.94
            cell_leading *= 0.94

        weights = list(widths) or [1.0] * len(columns)
        if len(weights) != len(columns):
            weights = [1.0] * len(columns)
        total = sum(weights) or 1.0
        pad = 4.0
        col_widths = [self.column_width * w / total for w in weights]
        aligns = list(align) + ["left"] * (len(columns) - len(align))

        def draw_header() -> None:
            self.need(head_leading + 8.0)
            top = self.y
            self.page.rect(self.left, top - 2, self.column_width,
                           head_leading + 4, fill=(0.945, 0.945, 0.94),
                           stroke=None)
            x = self.left
            for index, name in enumerate(columns):
                self._cell(x, self.y, col_widths[index], name, head_face,
                           head_size, aligns[index], pad, INK)
                x += col_widths[index]
            self.y += head_leading + 3.0
            self.page.line(self.left, self.y - 1.5, self.right, self.y - 1.5,
                           width=0.7, colour=(0.55, 0.56, 0.58))
            # Clear of the rule. Text is drawn slightly above its y, so
            # without this the first row of every table sits on the line
            # under the header and reads as struck through.
            self.y += 4.0

        draw_header()
        for row in rows:
            wrapped = []
            for index, value in enumerate(row):
                inner = col_widths[index] - pad * 2
                lines = wrap(str(value), cell_face, cell_size, inner)
                wrapped.append(lines or [""])
            height = cell_leading * max(len(c) for c in wrapped) + 2.0
            if self.y + height > self.bottom:
                self.new_page()
                draw_header()
            top = self.y
            x = self.left
            for index, lines in enumerate(wrapped):
                inner = col_widths[index] - pad * 2
                for offset, line in enumerate(lines):
                    self._cell(x, top + offset * cell_leading,
                               col_widths[index],
                               _shrink_to_fit(line, cell_face, cell_size,
                                              inner),
                               cell_face, cell_size, aligns[index], pad, INK)
                x += col_widths[index]
            self.y = top + height
            self.page.line(self.left, self.y - 1.0, self.right, self.y - 1.0,
                           width=0.25, colour=(0.88, 0.885, 0.89))
        self.y += 7.0

    def _cell(self, x, y, width, text, face, size, alignment, pad,
              colour) -> None:
        if alignment == "right":
            self.page.text(x + width - pad, y, text, face, size, colour,
                           anchor="end")
        elif alignment == "centre":
            self.page.text(x + width / 2, y, text, face, size, colour,
                           anchor="middle")
        else:
            self.page.text(x + pad, y, text, face, size, colour)

    def draw_scene(self, scene: dict, caption: str = "",
                   max_width: float = 0.0) -> None:
        """
        Place a vector scene, scaled to fit the column.

        The same Scene the screen draws. Part 7's point: one description of
        the picture, two backends, so the kundli in the report cannot differ
        from the kundli on the screen.
        """
        source_w = float(scene.get("width") or 1.0)
        source_h = float(scene.get("height") or 1.0)
        target_w = max_width or min(self.column_width * 0.55, 250.0)
        scale = target_w / source_w
        target_h = source_h * scale

        self.need(target_h + 26.0)
        origin_x = self.left + (self.column_width - target_w) / 2
        origin_y = self.y

        def px(x):
            return origin_x + float(x) * scale

        def py(y):
            return origin_y + float(y) * scale

        for element in scene.get("elements", []):
            kind = element.get("kind")
            if kind == "line":
                self.page.line(px(element["x1"]), py(element["y1"]),
                               px(element["x2"]), py(element["y2"]),
                               width=max(0.3, element.get("width", 1) * scale),
                               colour=_hex(element.get("colour")))
            elif kind == "polygon":
                self.page.polygon(
                    [(px(x), py(y)) for x, y in element["points"]],
                    fill=_hex(element.get("fill")),
                    stroke=_hex(element.get("stroke")),
                    width=max(0.3, element.get("width", 1) * scale))
            elif kind == "rect":
                self.page.rect(px(element["x"]), py(element["y"]),
                               element["width"] * scale,
                               element["height"] * scale,
                               fill=_hex(element.get("fill")),
                               stroke=_hex(element.get("stroke")))
            elif kind == "text":
                size = element.get("size", 10) * scale
                face = (FACE_BODY_BOLD if element.get("weight") == "bold"
                        else FACE_BODY)
                self.page.text(
                    px(element["x"]), py(element["y"]) + size * 0.34,
                    element.get("text", ""), face, size,
                    _hex(element.get("colour")) or INK,
                    anchor=element.get("anchor", "middle"))

        self.y = origin_y + target_h + 6.0
        if caption:
            self.page.text(self.left + self.column_width / 2, self.y, caption,
                           FACE_HEAD, 8.6, MUTED, anchor="middle")
            self.y += 14.0


def _hex(value):
    """'#1a1a1a' to a PDF colour triple. None passes through as None."""
    if not value or value == "none":
        return None
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        return None
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ── document rendering ───────────────────────────────────────────────────────

_BLOCK_DRAWERS = {}


def _draw_block(layout: Layout, block: dict) -> None:
    kind = block.get("block")
    if kind == "paragraph":
        style = block.get("style", "body")
        layout.draw_text(block.get("text", ""), style,
                         MUTED if style in ("small", "note") else INK)
    elif kind == "heading":
        layout.draw_heading(block.get("text", ""), block.get("level", 2))
    elif kind == "table":
        layout.draw_table(
            block.get("columns", []), block.get("rows", []),
            widths=block.get("widths", ()), align=block.get("align", ()),
            caption=block.get("caption", ""),
            compact=block.get("compact", False))
    elif kind == "chart":
        scene = block.get("scene")
        if scene:
            layout.draw_scene(scene, caption=block.get("caption", ""))
    elif kind == "keyvalues":
        layout.draw_keyvalues(
            [tuple(p) for p in block.get("pairs", [])],
            caption=block.get("caption", ""), notes=block.get("notes", ()))
    elif kind == "callout":
        layout.draw_callout(block.get("text", ""), block.get("kind", "note"),
                            block.get("title", ""))
    elif kind == "bullets":
        layout.draw_bullets(block.get("items", []),
                            caption=block.get("caption", ""))
    elif kind == "pagebreak":
        layout.new_page()
    else:
        raise ValueError(f"no PDF renderer for block type '{kind}'")


def _draw_furniture(layout: Layout, footer_note: str) -> None:
    """
    Running header and footer, drawn after the page count is known.

    The cover page carries neither: a report whose first page is numbered
    and headed reads like a chapter of something else.
    """
    total = len(layout.pages)
    for index, page in enumerate(layout.pages, start=1):
        if index == 1:
            continue
        face, size, _, _, _ = STYLES["footer"]
        top = MARGIN_TOP - 12.0
        page.line(MARGIN_LEFT, top + 4, page.width - MARGIN_RIGHT, top + 4,
                  width=0.4)
        page.text(MARGIN_LEFT, top, layout.subject, face, size, MUTED)
        if page.section_title:
            page.text(page.width - MARGIN_RIGHT, top, page.section_title,
                      face, size, MUTED, anchor="end")

        foot = page.height - MARGIN_BOTTOM + 6.0
        page.line(MARGIN_LEFT, foot - 8, page.width - MARGIN_RIGHT, foot - 8,
                  width=0.4)
        page.text(MARGIN_LEFT, foot, footer_note, face, size, MUTED)
        page.text(page.width - MARGIN_RIGHT, foot, f"Page {index} of {total}",
                  face, size, MUTED, anchor="end")


#: How many dropped characters count as "this document is not renderable"
#: rather than "one stray symbol". A Sanskrit citation transliterates to
#: ASCII and loses nothing countable; a page of Devanagari loses everything.
UNSUPPORTED_THRESHOLD = 12


def scan_unsupported(document: dict) -> dict:
    """
    Which characters this document carries that NO available face can
    print, and how many.

    Returns a report rather than raising, so a caller can decide: the PDF
    writer refuses above the threshold, and a test can assert that an
    English document is at zero.

    V1.8 narrowed what counts. Devanagari used to land here and made every
    Hindi document unprintable; it is now carried by an embedded, shaped
    face, so the question asked of each character is "can any face draw
    it" rather than "is it Latin". A codepoint inside the Devanagari block
    that the bundled font has no glyph for still counts — a font covering
    a script is not the same as a font covering every character in it.
    """
    counts: dict[str, int] = {}
    font = devanagari_font()

    def scan(value) -> None:
        if isinstance(value, str):
            for char in value:
                if ord(char) < 256 or ord(char) in _WINANSI_HIGH:
                    continue
                if char in TRANSLITERATE or char in IAST_TO_ASCII:
                    continue
                if font.font.glyph_for(ord(char)):
                    continue
                counts[char] = counts.get(char, 0) + 1
        elif isinstance(value, dict):
            for item in value.values():
                scan(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                scan(item)

    scan(document)
    total = sum(counts.values())
    return {
        "total": total,
        "characters": dict(sorted(counts.items())),
        "renderable": total <= UNSUPPORTED_THRESHOLD,
    }


def layout_document(document: dict, page_size: str = "a4") -> Layout:
    """Lay a serialised ReportDocument out into pages. No file is written."""
    layout = Layout(page_size=page_size,
                    title=document.get("title", ""),
                    subject=document.get("subject", ""))

    for index, section in enumerate(document.get("sections", [])):
        layout.section_title = section.get("title", "")
        if index > 0 and section.get("starts_page", True):
            layout.new_page()
        layout.page.section_title = layout.section_title
        if section.get("title"):
            layout.draw_heading(section["title"], level=1)
        if section.get("subtitle"):
            layout.draw_text(section["subtitle"], "note")
        for block in section.get("blocks", []):
            _draw_block(layout, block)

    note = (f"{document.get('mode', 'detailed').capitalize()} report — "
            f"deterministic calculation, no predictive claim")
    _draw_furniture(layout, note)
    return layout


def render_pdf(document: dict, page_size: str = "a4",
               compress: bool = True) -> bytes:
    """
    A complete PDF file as bytes.

    `document` is a serialised ReportDocument. The bytes are a pure function
    of it plus the two arguments here — there is no creation date and no
    document identifier derived from the clock, so Part 39's requirement
    that identical inputs produce identical output holds for the file
    itself, not merely for its text.

    Refuses a document it cannot print. See `PdfUnsupportedText`.
    """
    unsupported = scan_unsupported(document)
    if not unsupported["renderable"]:
        sample = "".join(list(unsupported["characters"])[:8])
        raise PdfUnsupportedText(
            f"This report contains {unsupported['total']} characters no "
            f"face available to this writer can print (for example: "
            f"{sample}). It would render as a page of question marks, so "
            f"it is refused rather than produced. The HTML report carries "
            f"any script the reader's browser has a font for.")
    # Glyph usage is per document. Without this, a second report in the
    # same process would embed a subset containing the first report's
    # glyphs — harmless to look at, and enough to break the byte-identical
    # determinism Part 39 requires.
    reset_embedded_fonts()
    layout = layout_document(document, page_size=page_size)
    return _assemble(layout, document, compress=compress)


# ── file assembly ────────────────────────────────────────────────────────────

def _stream_object(payload: bytes, extra: str = "",
                   compress: bool = True) -> bytes:
    """A PDF stream object, compressed unless asked otherwise."""
    if compress:
        packed = zlib.compress(payload, 9)
        header = (f"<< /Length {len(packed)} /Filter /FlateDecode{extra} >>\n"
                  f"stream\n")
        return header.encode("latin-1") + packed + b"\nendstream"
    header = f"<< /Length {len(payload)}{extra} >>\nstream\n"
    return header.encode("latin-1") + payload + b"\nendstream"


def _assemble(layout: Layout, document: dict, compress: bool = True) -> bytes:
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)          # 1-based object number

    font_ids = {}
    for face, name in sorted(_FACE_IDS.items()):
        font_ids[name] = add(
            f"<< /Type /Font /Subtype /Type1 /BaseFont /{face} "
            f"/Encoding /WinAnsiEncoding >>".encode("latin-1"))

    # The embedded Devanagari face, emitted only when the document used
    # it. An English report carries no font file at all, so adding Hindi
    # support did not make every PDF bigger — which it would have, by
    # about 60 KB, had the subset been unconditional.
    embedded = devanagari_font()
    if embedded.used:
        subset = embedded.subset()
        font_file = add(_stream_object(
            subset, extra=f" /Length1 {len(subset)}", compress=compress))
        descriptor = add((
            f"<< /Type /FontDescriptor /FontName /{embedded.id} "
            f"/Flags {embedded.descriptor_flags()} "
            f"/FontBBox {embedded.bbox()} /ItalicAngle 0 "
            f"/Ascent {embedded.font.ascender} "
            f"/Descent {embedded.font.descender} "
            f"/CapHeight {embedded.font.cap_height} /StemV 80 "
            f"/FontFile2 {font_file} 0 R >>").encode("latin-1"))
        to_unicode = add(_stream_object(
            embedded.to_unicode_cmap(), compress=compress))
        descendant = add((
            f"<< /Type /Font /Subtype /CIDFontType2 "
            f"/BaseFont /{embedded.id} "
            f"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) "
            f"/Supplement 0 >> /FontDescriptor {descriptor} 0 R "
            f"/DW 1000 /W {embedded.widths_array()} "
            f"/CIDToGIDMap /Identity >>").encode("latin-1"))
        font_ids[DEVANAGARI_FACE_ID] = add((
            f"<< /Type /Font /Subtype /Type0 /BaseFont /{embedded.id} "
            f"/Encoding /Identity-H /DescendantFonts [{descendant} 0 R] "
            f"/ToUnicode {to_unicode} 0 R >>").encode("latin-1"))

    resources = ("<< /Font << " + " ".join(
        f"/{name} {number} 0 R" for name, number in sorted(font_ids.items()))
        + " >> >>")

    # The page tree has to name its children and each child has to name the
    # tree, so one of the two numbers must be predicted. Each page costs
    # exactly two objects — a content stream and the page itself — which
    # makes the tree's number arithmetic rather than a second pass. The
    # assertion below is what keeps that arithmetic honest.
    pages_number = len(objects) + 2 * len(layout.pages) + 1
    page_numbers = []
    for page in layout.pages:
        stream = page.stream()
        if compress:
            packed = zlib.compress(stream, 9)
            content = (f"<< /Length {len(packed)} /Filter /FlateDecode >>\n"
                       f"stream\n").encode("latin-1") + packed + \
                      b"\nendstream"
        else:
            content = (f"<< /Length {len(stream)} >>\nstream\n"
                       .encode("latin-1") + stream + b"\nendstream")
        content_number = add(content)
        page_numbers.append(add(
            f"<< /Type /Page /Parent {pages_number} 0 R "
            f"/MediaBox [0 0 {_fmt(page.width)} {_fmt(page.height)}] "
            f"/Resources {resources} /Contents {content_number} 0 R >>"
            .encode("latin-1")))

    kids = " ".join(f"{n} 0 R" for n in page_numbers)
    pages_object = add(
        f"<< /Type /Pages /Count {len(page_numbers)} /Kids [{kids}] >>"
        .encode("latin-1"))
    assert pages_object == pages_number, "page tree numbering drifted"

    info = add(
        f"<< /Title "
        f"({_escape(to_winansi(sanitise_metadata(document.get('title', ''))))}) "
        f"/Creator ({_escape(to_winansi(user_agent()))}) "
        f"/Producer (Jyotish Engine deterministic PDF writer) >>"
        .encode("latin-1"))
    catalog = add(
        f"<< /Type /Catalog /Pages {pages_object} 0 R >>".encode("latin-1"))

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R "
            f"/Info {info} 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
            .encode("latin-1"))
    return bytes(out)


def write_pdf(document: dict, path: str, page_size: str = "a4") -> str:
    data = render_pdf(document, page_size=page_size)
    with open(path, "wb") as handle:
        handle.write(data)
    return path
