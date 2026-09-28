"""
TrueType subsetting and PDF embedding (V1.8 Parts 16, 17)
-----------------------------------------------------------
Puts a real Unicode font inside the PDF.

WHY THE FONT IS SUBSET RATHER THAN EMBEDDED WHOLE

    The bundled Devanagari face is 238 KB. A summary report is 13 KB. A
    reader downloading a nine-page PDF should not receive a font twenty
    times the size of the document, and a reader generating a hundred of
    them should not receive it a hundred times.

    The subsetter keeps GLYPH IDS STABLE and empties the outlines of
    glyphs the document does not use. That is deliberately the simple
    form of subsetting: renumbering glyphs would mean rewriting every
    shaped run and re-deriving the width array, and a renumbering bug
    produces a document full of the wrong letters rather than a crash.
    Keeping ids stable costs a few kilobytes of `loca` and removes the
    entire class of error.

WHY IDENTITY-H

    Shaping has already happened by the time anything here runs. What
    reaches the content stream is glyph ids, not characters — that is the
    whole point of a shaper — so the encoding has to be one that names
    glyphs directly. Identity-H does, and CIDToGIDMap /Identity then means
    CID equals glyph id equals what the shaper produced.

    The cost is that the PDF's text is no longer extractable as Unicode
    by default, which matters: a reader who cannot copy a word out of a
    report has lost something real. So a ToUnicode CMap is emitted from
    the shaper's own cluster mapping, and `test_hindi_pdf.py` asserts that
    the golden words survive a round trip through it.
"""

from __future__ import annotations

import os
import struct
from typing import Iterable, Optional

from .devanagari import DevanagariShaper, is_devanagari
from .opentype import OpenTypeFont, load_font

FONT_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "fonts")

#: Part 17. Recorded here rather than in a README so that the application's
#: own "about" screen and its tests read the same record.
BUNDLED_FONTS = (
    {
        "id": "NotoSansDevanagari-Regular",
        "file": "NotoSansDevanagari-Regular.ttf",
        "family": "Noto Sans Devanagari",
        "style": "Regular",
        "version": "Noto Project release, 2022 copyright line",
        "licence": "SIL Open Font License 1.1",
        "licence_file": "OFL.txt",
        "source": ("https://github.com/notofonts/notofonts.github.io/"
                   "tree/main/fonts/NotoSansDevanagari/hinted/ttf"),
        "retrieved_on": "2026-09-28",
        "sha256": ("4e3c66638958c3e2ab5d37f47a8deb89"
                   "fffeb7be9985c665a519bbc7ba762313"),
        "redistributable": True,
        "notes": (
            "OFL 1.1 permits bundling and redistribution, including inside "
            "a PDF, provided the licence travels with the font and the "
            "Reserved Font Name is not used for a modified version. Both "
            "hold: OFL.txt ships beside the file, and the subsetter "
            "produces an embedded subset rather than a redistributed "
            "font under the same name. "
            "The file is NOT served by the application. Part 17 forbids "
            "exposing raw font files as downloadable content, and the "
            "local server has no route that reaches this directory."),
    },
)


class FontLicenceError(RuntimeError):
    """A font without clear redistribution rights. Never approximated."""


# ── subsetting ──────────────────────────────────────────────────────────────

def _glyph_range(font: OpenTypeFont, glyph: int) -> tuple[int, int]:
    data = font.data
    loca = font.table("loca")
    if font.index_to_loc_format == 0:
        start = struct.unpack_from(">H", data, loca + glyph * 2)[0] * 2
        end = struct.unpack_from(">H", data, loca + glyph * 2 + 2)[0] * 2
    else:
        start = struct.unpack_from(">I", data, loca + glyph * 4)[0]
        end = struct.unpack_from(">I", data, loca + glyph * 4 + 4)[0]
    return start, end


def _components(font: OpenTypeFont, glyph: int) -> list[int]:
    """Glyphs a composite glyph references. Empty for a simple glyph."""
    start, end = _glyph_range(font, glyph)
    if end <= start:
        return []
    base = font.table("glyf") + start
    data = font.data
    if struct.unpack_from(">h", data, base)[0] >= 0:
        return []

    out = []
    cursor = base + 10
    while True:
        flags, index = struct.unpack_from(">HH", data, cursor)
        out.append(index)
        cursor += 4
        cursor += 4 if flags & 0x0001 else 2          # ARG_1_AND_2_ARE_WORDS
        if flags & 0x0008:                             # WE_HAVE_A_SCALE
            cursor += 2
        elif flags & 0x0040:                           # X_AND_Y_SCALE
            cursor += 4
        elif flags & 0x0080:                           # TWO_BY_TWO
            cursor += 8
        if not flags & 0x0020:                         # MORE_COMPONENTS
            break
    return out


def closure(font: OpenTypeFont, glyphs: Iterable[int]) -> set:
    """
    Every glyph needed to draw `glyphs`, composites resolved.

    Missing this is how a subset PDF ends up with letters that are blank
    in one viewer and correct in another: a composite glyph whose parts
    were dropped draws nothing, and only a renderer that ignores the
    missing parts appears to work.
    """
    wanted = {0} | {g for g in glyphs if 0 <= g < font.num_glyphs}
    pending = list(wanted)
    while pending:
        glyph = pending.pop()
        for component in _components(font, glyph):
            if component not in wanted and component < font.num_glyphs:
                wanted.add(component)
                pending.append(component)
    return wanted


def _checksum(data: bytes) -> int:
    padded = data + b"\x00" * (-len(data) % 4)
    total = 0
    for offset in range(0, len(padded), 4):
        total = (total + struct.unpack_from(">I", padded, offset)[0]) & 0xFFFFFFFF
    return total


def _build_sfnt(tables: dict) -> bytes:
    """Assemble a TrueType file from tag → bytes."""
    tags = sorted(tables)
    count = len(tags)
    search_range = 1
    entry_selector = 0
    while search_range * 2 <= count:
        search_range *= 2
        entry_selector += 1
    search_range *= 16
    range_shift = count * 16 - search_range

    header = struct.pack(">IHHHH", 0x00010000, count, search_range,
                         entry_selector, range_shift)
    offset = 12 + count * 16
    directory = b""
    body = b""
    for tag in tags:
        payload = tables[tag]
        directory += struct.pack(
            ">4sIII", tag.encode("latin-1").ljust(4),
            _checksum(payload), offset, len(payload))
        padded = payload + b"\x00" * (-len(payload) % 4)
        body += padded
        offset += len(padded)

    font = header + directory + body
    # head.checkSumAdjustment is computed over the finished file with its
    # own field zeroed, which is why it is patched here and not earlier.
    head_index = tags.index("head")
    head_offset = 12 + head_index * 16
    head_start = struct.unpack_from(">I", font, head_offset + 8)[0]
    adjustment = (0xB1B0AFBA - _checksum(font)) & 0xFFFFFFFF
    font = (font[:head_start + 8] + struct.pack(">I", adjustment)
            + font[head_start + 12:])
    return font


def subset_truetype(font: OpenTypeFont, glyphs: Iterable[int]) -> bytes:
    """
    A TrueType file containing only the outlines `glyphs` needs.

    Glyph ids are preserved, so a shaped run needs no remapping and the
    PDF's CIDToGIDMap stays /Identity.
    """
    wanted = closure(font, glyphs)
    data = font.data
    glyf_base = font.table("glyf")

    new_glyf = bytearray()
    offsets = []
    for glyph in range(font.num_glyphs):
        offsets.append(len(new_glyf))
        if glyph not in wanted:
            continue
        start, end = _glyph_range(font, glyph)
        if end > start:
            new_glyf += data[glyf_base + start:glyf_base + end]
            # Every glyph must start on an even boundary for short loca;
            # long loca is used below, but padding keeps the file tidy and
            # matches what every other producer emits.
            new_glyf += b"\x00" * (-len(new_glyf) % 4)
    offsets.append(len(new_glyf))

    new_loca = b"".join(struct.pack(">I", value) for value in offsets)

    head = bytearray(font.table_bytes("head"))
    struct.pack_into(">h", head, 50, 1)          # indexToLocFormat: long
    struct.pack_into(">I", head, 8, 0)           # checkSumAdjustment

    tables = {
        "head": bytes(head),
        "hhea": font.table_bytes("hhea"),
        "maxp": font.table_bytes("maxp"),
        "hmtx": font.table_bytes("hmtx"),
        "loca": new_loca,
        "glyf": bytes(new_glyf),
    }
    for optional in ("cvt ", "fpgm", "prep", "gasp"):
        if optional in font.tables:
            tables[optional] = font.table_bytes(optional)
    return _build_sfnt(tables)


# ── the embedded face ───────────────────────────────────────────────────────

class EmbeddedFont:
    """
    One bundled font, its shaper, and the glyphs a document has used.

    `used` accumulates across a render so the subset is built once, at
    assembly, from exactly what was drawn.
    """

    def __init__(self, record: dict):
        path = os.path.join(FONT_DIRECTORY, record["file"])
        if not record.get("redistributable"):
            raise FontLicenceError(
                f"{record['id']} has no recorded redistribution right; "
                f"a font is not bundled on the assumption that it is free")
        self.record = record
        self.path = path
        self.font = load_font(path)
        self.shaper = DevanagariShaper(self.font)
        self.used: set = set()
        #: glyph id → the text it came from, for the ToUnicode map.
        self.to_unicode: dict = {}
        # Greedy word wrap measures the same growing prefix once per word,
        # so laying out one paragraph asks for the same shaping dozens of
        # times. Widths are cached; shaped runs are not, because callers
        # receive mutable glyph objects and a shared cached list would let
        # one drawing pass corrupt the next.
        self._width_cache: dict = {}

    @property
    def id(self) -> str:
        return self.record["id"]

    @property
    def units_per_em(self) -> int:
        return self.font.units_per_em

    def shape(self, text: str) -> list:
        glyphs = self.shaper.shape(text)
        for glyph in glyphs:
            self.used.add(glyph.glyph)
            if glyph.glyph not in self.to_unicode:
                index = glyph.cluster
                if 0 <= index < len(text):
                    self.to_unicode[glyph.glyph] = text[index]
        return glyphs

    def width(self, text: str, size: float) -> float:
        units = self._width_cache.get(text)
        if units is None:
            glyphs = self.shaper.shape(text)
            units = sum(glyph.x_advance for glyph in glyphs)
            if len(self._width_cache) >= 20000:
                self._width_cache.clear()
            self._width_cache[text] = units
        return units * size / self.font.units_per_em

    def subset(self) -> bytes:
        return subset_truetype(self.font, self.used)

    # ── PDF objects ─────────────────────────────────────────────────────

    def widths_array(self) -> str:
        """
        The /W array: glyph widths in 1/1000 em.

        Only used glyphs are listed. A viewer falls back to /DW for the
        rest, and the rest are never drawn.
        """
        scale = 1000.0 / self.font.units_per_em
        entries = []
        for glyph in sorted(self.used):
            width = round(self.font.advance(glyph) * scale)
            entries.append(f"{glyph} [{width}]")
        return "[" + " ".join(entries) + "]"

    def to_unicode_cmap(self) -> bytes:
        """
        A ToUnicode CMap so the text can still be copied out.

        Built from the shaper's cluster mapping, which means a ligature
        maps to the FIRST character of the cluster it came from. That is
        lossy — `क्ष` copies as `क` — and it is recorded as a limitation
        rather than papered over, because the alternative is emitting a
        mapping that claims more than the shaper knows.
        """
        pairs = sorted(self.to_unicode.items())
        lines = [
            "/CIDInit /ProcSet findresource begin",
            "12 dict begin", "begincmap",
            "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) "
            "/Supplement 0 >> def",
            "/CMapName /Adobe-Identity-UCS def", "/CMapType 2 def",
            "1 begincodespacerange", "<0000> <FFFF>", "endcodespacerange",
        ]
        for start in range(0, len(pairs), 100):
            chunk = pairs[start:start + 100]
            lines.append(f"{len(chunk)} beginbfchar")
            for glyph, character in chunk:
                code = "".join(f"{ord(part):04X}" for part in character)
                lines.append(f"<{glyph:04X}> <{code}>")
            lines.append("endbfchar")
        lines += ["endcmap",
                  "CMapName currentdict /CMap defineresource pop",
                  "end", "end"]
        return "\n".join(lines).encode("latin-1", "replace")

    def descriptor_flags(self) -> int:
        # 4 = symbolic. Devanagari is outside the standard Latin set, so a
        # nonsymbolic flag would invite a viewer to apply a Latin encoding.
        return 4

    def bbox(self) -> str:
        font = self.font
        scale = 1000.0 / font.units_per_em
        return (f"[{round(font.x_min * scale)} {round(font.y_min * scale)} "
                f"{round(font.x_max * scale)} {round(font.y_max * scale)}]")


_CACHE: dict = {}


def devanagari_font() -> EmbeddedFont:
    """The bundled Devanagari face, loaded once per process."""
    if "devanagari" not in _CACHE:
        _CACHE["devanagari"] = EmbeddedFont(BUNDLED_FONTS[0])
    return _CACHE["devanagari"]


def reset_embedded_fonts() -> None:
    """Drop accumulated glyph usage between documents."""
    for font in _CACHE.values():
        font.used = set()
        font.to_unicode = {}


def font_licences() -> list[dict]:
    """Part 17's record, for the methodology screen and the report."""
    return [dict(record) for record in BUNDLED_FONTS]


def licence_text(record: Optional[dict] = None) -> str:
    entry = record or BUNDLED_FONTS[0]
    path = os.path.join(FONT_DIRECTORY, entry["licence_file"])
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def needs_shaping(text: str) -> bool:
    return is_devanagari(text)
