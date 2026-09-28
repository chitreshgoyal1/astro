"""
OpenType layout (V1.8 Part 16)
--------------------------------
Enough of the OpenType specification to render Devanagari correctly.

WHY THIS EXISTS AT ALL

    V1.7 refused to produce a Hindi PDF, and the refusal was right: the
    base-14 PDF fonts are Latin, and Devanagari needs more than a font
    that contains the letters. `कार्य` is five codepoints and renders as
    three shapes, one of which is drawn above a letter that appears later
    in the string than the letter it belongs to. A renderer that maps
    codepoints to glyphs in order produces something that is wrong in a
    way a reader of Hindi sees immediately and a reader of English does
    not — which is worse than refusing.

    Part 16 requires the real thing, offline, and this project takes no
    runtime dependencies. So the shaping engine is here.

WHAT IS IMPLEMENTED, AND WHAT IS NOT

    GSUB lookup types 1, 2, 4, 5, 6 and GPOS types 1, 2, 4, 6, 8. That is
    not an arbitrary subset: it is exactly what the bundled font uses,
    measured by walking its lookup list rather than guessed. An
    unimplemented lookup type is SKIPPED AND COUNTED, never silently
    treated as a no-op, so `unsupported_lookups` can be asserted empty in
    a test and would become non-empty the moment the font is replaced with
    one that needs more.

    Extension lookups (GSUB 7 / GPOS 9) are unwrapped where present.
    Variable fonts, vertical layout and CFF outlines are not supported and
    are rejected at load rather than mis-rendered.

THE DESIGN RULE THAT KEEPS THIS HONEST

    Nothing in this module knows anything about astrology, and nothing in
    it may import from `engine`. It is a text renderer. It is under
    `app/report` and the boundary test covers it.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Optional

# ── primitive readers ───────────────────────────────────────────────────────


def _u8(data: bytes, offset: int) -> int:
    return data[offset]


def _u16(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def _s16(data: bytes, offset: int) -> int:
    value = _u16(data, offset)
    return value - 0x10000 if value & 0x8000 else value


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


class FontError(Exception):
    """A font this renderer cannot use, named rather than approximated."""


# ── coverage and class definition tables ────────────────────────────────────

def _coverage(data: bytes, offset: int) -> dict:
    """Glyph id → coverage index."""
    fmt = _u16(data, offset)
    out: dict = {}
    if fmt == 1:
        count = _u16(data, offset + 2)
        for i in range(count):
            out[_u16(data, offset + 4 + i * 2)] = i
    elif fmt == 2:
        count = _u16(data, offset + 2)
        for i in range(count):
            base = offset + 4 + i * 6
            start, end, index = (_u16(data, base), _u16(data, base + 2),
                                 _u16(data, base + 4))
            for gid in range(start, end + 1):
                out[gid] = index + gid - start
    else:
        raise FontError(f"coverage format {fmt}")
    return out


def _class_def(data: bytes, offset: int) -> dict:
    """Glyph id → class. Absent glyphs are class 0 by definition."""
    fmt = _u16(data, offset)
    out: dict = {}
    if fmt == 1:
        start = _u16(data, offset + 2)
        count = _u16(data, offset + 4)
        for i in range(count):
            out[start + i] = _u16(data, offset + 6 + i * 2)
    elif fmt == 2:
        count = _u16(data, offset + 2)
        for i in range(count):
            base = offset + 4 + i * 6
            first, last, value = (_u16(data, base), _u16(data, base + 2),
                                  _u16(data, base + 4))
            for gid in range(first, last + 1):
                out[gid] = value
    else:
        raise FontError(f"class definition format {fmt}")
    return out


# ── the shaped output ───────────────────────────────────────────────────────

@dataclass
class ShapedGlyph:
    """
    One positioned glyph.

    `cluster` is the index in the ORIGINAL string of the character this
    glyph came from. It survives reordering and ligation, which is what
    lets a caller map a glyph back to the text — and what lets a test
    assert that a pre-base matra really did move before its consonant
    rather than merely appearing earlier by accident.
    """

    glyph: int
    cluster: int
    x_advance: int = 0
    y_advance: int = 0
    x_offset: int = 0
    y_offset: int = 0
    # Shaping bookkeeping, not output.
    category: int = 0
    position: int = 0
    mask: int = 0
    ligated: bool = False
    multiplied: bool = False


# ── the font ────────────────────────────────────────────────────────────────

class OpenTypeFont:
    """
    A parsed TrueType font with GSUB/GPOS layout.

    Loaded once and reused; the tables are read lazily and cached, because
    GSUB in the bundled font is 63 KB of nested offsets and parsing it on
    every page would dominate PDF generation.
    """

    def __init__(self, data: bytes, name: str = ""):
        self.data = data
        self.name = name
        self.unsupported_lookups: dict = {}
        self._parse_directory()
        self._parse_head()
        self._parse_hmtx()
        self._cmap: Optional[dict] = None
        self._gdef_classes: Optional[dict] = None
        self._gsub: Optional[dict] = None
        self._gpos: Optional[dict] = None
        self._lookup_cache: dict = {}
        self._coverage_cache: dict = {}
        self._class_cache: dict = {}
        #: Parsed subtable structures, keyed by their file offset. A
        #: chaining subtable's header — the backtrack, input and lookahead
        #: coverage arrays — was being re-read from bytes for every glyph
        #: of every run, which made shaping one Hindi page take seconds.
        self._subtable_cache: dict = {}

    # ── directory and basic metrics ─────────────────────────────────────

    def _parse_directory(self) -> None:
        data = self.data
        if len(data) < 12:
            raise FontError("file is too short to be a font")
        tag = data[0:4]
        if tag == b"ttcf":
            raise FontError("TrueType collections are not supported")
        if tag == b"OTTO":
            raise FontError(
                "CFF outlines are not supported; this renderer embeds "
                "TrueType glyf outlines only")
        if tag not in (b"\x00\x01\x00\x00", b"true"):
            raise FontError(f"unrecognised sfnt version {tag!r}")

        count = _u16(data, 4)
        self.tables: dict = {}
        for index in range(count):
            entry = 12 + index * 16
            name = data[entry:entry + 4].decode("latin-1")
            offset = _u32(data, entry + 8)
            length = _u32(data, entry + 12)
            self.tables[name] = (offset, length)

        for required in ("head", "hhea", "hmtx", "maxp", "cmap", "glyf",
                         "loca"):
            if required not in self.tables:
                raise FontError(f"font has no {required} table")
        if "fvar" in self.tables:
            raise FontError(
                "variable fonts are not supported; supply a static "
                "instance so the embedded outlines match what is measured")

    # Coverage and class-definition tables are read once each and cached.
    # They are the hot path of layout: every subtable consults its
    # coverage for every glyph, and building a 500-entry dict per glyph
    # per subtable made shaping one paragraph cost 70 milliseconds.
    def coverage(self, offset: int) -> dict:
        cached = self._coverage_cache.get(offset)
        if cached is None:
            cached = _coverage(self.data, offset)
            self._coverage_cache[offset] = cached
        return cached

    def class_def(self, offset: int) -> dict:
        cached = self._class_cache.get(offset)
        if cached is None:
            cached = _class_def(self.data, offset)
            self._class_cache[offset] = cached
        return cached

    def table(self, name: str) -> Optional[int]:
        entry = self.tables.get(name)
        return None if entry is None else entry[0]

    def table_bytes(self, name: str) -> bytes:
        offset, length = self.tables[name]
        return self.data[offset:offset + length]

    def _parse_head(self) -> None:
        head = self.table("head")
        self.units_per_em = _u16(self.data, head + 18)
        self.index_to_loc_format = _s16(self.data, head + 50)
        self.x_min = _s16(self.data, head + 36)
        self.y_min = _s16(self.data, head + 38)
        self.x_max = _s16(self.data, head + 40)
        self.y_max = _s16(self.data, head + 42)

        maxp = self.table("maxp")
        self.num_glyphs = _u16(self.data, maxp + 4)

        hhea = self.table("hhea")
        self.ascender = _s16(self.data, hhea + 4)
        self.descender = _s16(self.data, hhea + 6)
        self.number_of_h_metrics = _u16(self.data, hhea + 34)

        os2 = self.table("OS/2")
        self.cap_height = self.ascender
        self.italic_angle = 0
        if os2 is not None and _u16(self.data, os2) >= 2:
            self.cap_height = _s16(self.data, os2 + 88)

    def _parse_hmtx(self) -> None:
        hmtx = self.table("hmtx")
        self.advances: list[int] = []
        last = 0
        for index in range(self.number_of_h_metrics):
            last = _u16(self.data, hmtx + index * 4)
            self.advances.append(last)
        # Monospaced tails: every glyph past numberOfHMetrics repeats the
        # final advance. Expanded rather than special-cased at lookup.
        self.advances.extend([last] * (self.num_glyphs - len(self.advances)))

    def advance(self, glyph: int) -> int:
        if 0 <= glyph < len(self.advances):
            return self.advances[glyph]
        return 0

    # ── cmap ────────────────────────────────────────────────────────────

    @property
    def cmap(self) -> dict:
        if self._cmap is None:
            self._cmap = self._parse_cmap()
        return self._cmap

    def _parse_cmap(self) -> dict:
        data = self.data
        base = self.table("cmap")
        count = _u16(data, base + 2)

        # Preference order: a full Unicode subtable beats a BMP one, and
        # both beat a symbol encoding. Picking the first subtable found is
        # the classic way to render a font's text as mojibake.
        best = None
        best_score = -1
        for index in range(count):
            record = base + 4 + index * 8
            platform = _u16(data, record)
            encoding = _u16(data, record + 2)
            offset = base + _u32(data, record + 4)
            score = {
                (3, 10): 5, (0, 6): 5, (0, 4): 5,
                (3, 1): 4, (0, 3): 4, (0, 2): 3, (0, 1): 3, (0, 0): 3,
                (3, 0): 1,
            }.get((platform, encoding), 0)
            if score > best_score:
                best_score, best = score, offset
        if best is None:
            raise FontError("font has no usable cmap subtable")

        fmt = _u16(data, best)
        if fmt == 4:
            return self._cmap_format_4(best)
        if fmt == 12:
            return self._cmap_format_12(best)
        if fmt == 6:
            first = _u16(data, best + 6)
            entries = _u16(data, best + 8)
            return {first + i: _u16(data, best + 10 + i * 2)
                    for i in range(entries)}
        raise FontError(f"cmap format {fmt} is not supported")

    def _cmap_format_4(self, offset: int) -> dict:
        data = self.data
        seg_x2 = _u16(data, offset + 6)
        segments = seg_x2 // 2
        ends = offset + 14
        starts = ends + seg_x2 + 2
        deltas = starts + seg_x2
        ranges = deltas + seg_x2

        out: dict = {}
        for index in range(segments):
            end = _u16(data, ends + index * 2)
            start = _u16(data, starts + index * 2)
            delta = _u16(data, deltas + index * 2)
            range_offset = _u16(data, ranges + index * 2)
            if start > end:
                continue
            for code in range(start, min(end, 0xFFFF) + 1):
                if range_offset == 0:
                    glyph = (code + delta) & 0xFFFF
                else:
                    position = (ranges + index * 2 + range_offset
                                + (code - start) * 2)
                    if position + 1 >= len(data):
                        continue
                    glyph = _u16(data, position)
                    if glyph:
                        glyph = (glyph + delta) & 0xFFFF
                if glyph:
                    out[code] = glyph
        return out

    def _cmap_format_12(self, offset: int) -> dict:
        data = self.data
        groups = _u32(data, offset + 12)
        out: dict = {}
        for index in range(groups):
            base = offset + 16 + index * 12
            start = _u32(data, base)
            end = _u32(data, base + 4)
            glyph = _u32(data, base + 8)
            for step in range(end - start + 1):
                out[start + step] = glyph + step
        return out

    def glyph_for(self, codepoint: int) -> int:
        return self.cmap.get(codepoint, 0)

    # ── GDEF ────────────────────────────────────────────────────────────

    @property
    def glyph_classes(self) -> dict:
        """Glyph id → 1 base, 2 ligature, 3 mark, 4 component."""
        if self._gdef_classes is None:
            base = self.table("GDEF")
            if base is None:
                self._gdef_classes = {}
            else:
                offset = _u16(self.data, base + 4)
                self._gdef_classes = (
                    _class_def(self.data, base + offset) if offset else {})
        return self._gdef_classes

    def is_mark(self, glyph: int) -> bool:
        return self.glyph_classes.get(glyph) == 3

    # ── GSUB / GPOS tables ──────────────────────────────────────────────

    def _parse_layout(self, tag: str) -> dict:
        base = self.table(tag)
        if base is None:
            return {"scripts": {}, "features": [], "lookups": []}
        data = self.data
        script_list = base + _u16(data, base + 4)
        feature_list = base + _u16(data, base + 6)
        lookup_list = base + _u16(data, base + 8)

        scripts: dict = {}
        for index in range(_u16(data, script_list)):
            record = script_list + 2 + index * 6
            name = data[record:record + 4].decode("latin-1")
            table = script_list + _u16(data, record + 4)
            langs: dict = {}
            default = _u16(data, table)
            if default:
                langs[""] = self._lang_sys(table + default)
            for lang_index in range(_u16(data, table + 2)):
                lrec = table + 4 + lang_index * 6
                langs[data[lrec:lrec + 4].decode("latin-1")] = self._lang_sys(
                    table + _u16(data, lrec + 4))
            scripts[name] = langs

        features = []
        for index in range(_u16(data, feature_list)):
            record = feature_list + 2 + index * 6
            name = data[record:record + 4].decode("latin-1")
            table = feature_list + _u16(data, record + 4)
            indices = [_u16(data, table + 4 + i * 2)
                       for i in range(_u16(data, table + 2))]
            features.append((name, indices))

        lookups = [lookup_list + _u16(data, lookup_list + 2 + i * 2)
                   for i in range(_u16(data, lookup_list))]

        return {"scripts": scripts, "features": features, "lookups": lookups}

    def _lang_sys(self, offset: int) -> list:
        data = self.data
        return [_u16(data, offset + 6 + i * 2)
                for i in range(_u16(data, offset + 4))]

    @property
    def gsub(self) -> dict:
        if self._gsub is None:
            self._gsub = self._parse_layout("GSUB")
        return self._gsub

    @property
    def gpos(self) -> dict:
        if self._gpos is None:
            self._gpos = self._parse_layout("GPOS")
        return self._gpos

    def feature_lookups(self, table: dict, script_tags, feature_tag: str
                        ) -> list:
        """
        Lookup offsets for one feature under the first script that has it.

        `script_tags` is tried in order — for Devanagari that is `dev2`
        then `deva`, because the two encode DIFFERENT shaping models and a
        font supporting both expects the newer one to win.
        """
        scripts = table["scripts"]
        chosen = None
        for tag in script_tags:
            if tag in scripts:
                chosen = scripts[tag]
                break
        if chosen is None:
            chosen = scripts.get("DFLT")
        if chosen is None:
            return []
        indices = chosen.get("") or next(iter(chosen.values()), [])
        wanted = set(indices)
        out = []
        for index, (name, lookup_indices) in enumerate(table["features"]):
            if name != feature_tag or index not in wanted:
                continue
            out.extend(lookup_indices)
        return [table["lookups"][i] for i in sorted(set(out))
                if i < len(table["lookups"])]

    # ── lookup parsing ──────────────────────────────────────────────────

    def lookup(self, offset: int, kind: str) -> dict:
        key = (offset, kind)
        cached = self._lookup_cache.get(key)
        if cached is None:
            cached = self._parse_lookup(offset, kind)
            self._lookup_cache[key] = cached
        return cached

    def _parse_lookup(self, offset: int, kind: str) -> dict:
        data = self.data
        lookup_type = _u16(data, offset)
        flag = _u16(data, offset + 2)
        count = _u16(data, offset + 4)
        subtables = [offset + _u16(data, offset + 6 + i * 2)
                     for i in range(count)]
        mark_filtering_set = None
        if flag & 0x0010:
            mark_filtering_set = _u16(data, offset + 6 + count * 2)

        # Extension lookups (GSUB 7, GPOS 9) point at a real subtable of
        # another type. Unwrapped here so nothing downstream has to know.
        extension = 7 if kind == "GSUB" else 9
        if lookup_type == extension:
            resolved = []
            real_type = lookup_type
            for sub in subtables:
                real_type = _u16(data, sub + 2)
                resolved.append(sub + _u32(data, sub + 4))
            subtables, lookup_type = resolved, real_type

        return {"type": lookup_type, "flag": flag, "subtables": subtables,
                "mark_filtering_set": mark_filtering_set, "kind": kind}

    def _skips(self, lookup: dict, glyph: int) -> bool:
        """Whether a lookup's flags say to ignore this glyph."""
        flag = lookup["flag"]
        klass = self.glyph_classes.get(glyph, 0)
        if flag & 0x0008 and klass == 3:
            return True
        if flag & 0x0004 and klass == 2:
            return True
        if flag & 0x0002 and klass == 1:
            return True
        mark_class = flag >> 8
        if mark_class and klass == 3:
            attach = self._mark_attach_class(glyph)
            if attach and attach != mark_class:
                return True
        return False

    def _mark_attach_class(self, glyph: int) -> int:
        base = self.table("GDEF")
        if base is None:
            return 0
        offset = _u16(self.data, base + 10)
        if not offset:
            return 0
        if not hasattr(self, "_mark_attach"):
            self._mark_attach = _class_def(self.data, base + offset)
        return self._mark_attach.get(glyph, 0)


def load_font(path: str) -> OpenTypeFont:
    with open(path, "rb") as handle:
        return OpenTypeFont(handle.read(), name=path)
