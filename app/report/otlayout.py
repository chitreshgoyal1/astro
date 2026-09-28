"""
GSUB and GPOS application (V1.8 Part 16)
------------------------------------------
Applies OpenType lookups to a glyph run.

WHAT A LOOKUP ACTUALLY DOES

    A GSUB lookup rewrites glyphs: one for one (type 1), one for many
    (type 2), many for one (type 4, ligatures), or conditionally on
    surrounding glyphs (types 5 and 6). A GPOS lookup moves them: by a
    fixed amount (type 1), relative to a neighbour (type 2), or by
    attaching a mark to an anchor on a base (types 4 and 6).

    Devanagari needs all of these at once. `क्ष` is a type 4 ligature;
    the rakar in `ग्र` is a type 1 substitution selected by the `blwf`
    feature; and the vowel sign in `कि` is positioned by a type 4 mark
    attachment whose anchor differs per base glyph.

THE PART THAT IS EASY TO GET SUBTLY WRONG

    Lookup flags. A lookup may be told to ignore marks, or ligatures, or
    to consider only marks of one attachment class. Ligature lookups in
    particular MUST skip marks while matching, or `क` + `्` + `ष` with an
    intervening nukta stops ligating and the conjunct silently falls
    apart into three shapes. So matching runs through `_next` rather than
    over raw indices, and the component indices a ligature consumed are
    recorded so its marks can be reattached.

    This is also why `ligature_component` is tracked: after `क्ष` becomes
    one glyph, a mark that belonged to the second component has to attach
    to the second component's anchor, not the first's.
"""

from __future__ import annotations

from typing import Optional

from .opentype import OpenTypeFont, ShapedGlyph, _s16, _u16


# ── iteration honouring lookup flags ────────────────────────────────────────

def _next(font: OpenTypeFont, lookup: dict, glyphs: list, index: int
          ) -> Optional[int]:
    index += 1
    while index < len(glyphs):
        if not font._skips(lookup, glyphs[index].glyph):
            return index
        index += 1
    return None


def _previous(font: OpenTypeFont, lookup: dict, glyphs: list, index: int
              ) -> Optional[int]:
    index -= 1
    while index >= 0:
        if not font._skips(lookup, glyphs[index].glyph):
            return index
        index -= 1
    return None


def _match_forward(font, lookup, glyphs, start, sequence, compare) -> Optional[list]:
    """Indices matching `sequence` after `start`, or None."""
    out = []
    index = start
    for wanted in sequence:
        index = _next(font, lookup, glyphs, index)
        if index is None or not compare(glyphs[index].glyph, wanted):
            return None
        out.append(index)
    return out


def _match_backward(font, lookup, glyphs, start, sequence, compare
                    ) -> Optional[list]:
    out = []
    index = start
    for wanted in sequence:
        index = _previous(font, lookup, glyphs, index)
        if index is None or not compare(glyphs[index].glyph, wanted):
            return None
        out.append(index)
    return out


# ── GSUB ────────────────────────────────────────────────────────────────────

def first_glyphs(font: OpenTypeFont, lookup: dict) -> Optional[set]:
    """
    Every glyph that could begin a match in this lookup, or None if that
    cannot be determined cheaply.

    A lookup may hold dozens of subtables, and a run may hold dozens of
    glyphs, so the naive loop descends into every subtable for every
    glyph — twelve thousand descents to shape one sentence, almost all of
    which fail on the first coverage test. Hoisting that test to the
    lookup means one set membership decides whether the lookup can
    possibly apply.

    This is a pure filter: a glyph the union rejects could not have
    matched any subtable, so skipping it cannot change the result. A test
    shapes every golden word with the filter disabled and asserts the
    glyph stream is identical.
    """
    cached = lookup.get("_first")
    if cached is not None:
        return cached if cached != "unknown" else None

    data = font.data
    union: set = set()
    for subtable in lookup["subtables"]:
        fmt = _u16(data, subtable)
        kind = lookup["type"]
        try:
            if kind in (1, 2, 4) or (kind in (5, 6) and fmt in (1, 2)):
                union |= set(font.coverage(
                    subtable + _u16(data, subtable + 2)))
            elif kind == 6 and fmt == 3:
                backtrack_count = _u16(data, subtable + 2)
                cursor = subtable + 4 + backtrack_count * 2
                if _u16(data, cursor) == 0:
                    lookup["_first"] = "unknown"
                    return None
                union |= set(font.coverage(
                    subtable + _u16(data, cursor + 2)))
            elif kind == 5 and fmt == 3:
                union |= set(font.coverage(
                    subtable + _u16(data, subtable + 6)))
            else:
                lookup["_first"] = "unknown"
                return None
        except Exception:                          # pragma: no cover
            # An unreadable subtable must not silently narrow the filter,
            # because a narrowed filter drops substitutions rather than
            # raising. Fall back to trying every glyph.
            lookup["_first"] = "unknown"
            return None
    lookup["_first"] = union
    return union


def apply_gsub_lookup(font: OpenTypeFont, lookup: dict, glyphs: list,
                      mask: int = 0, use_filter: bool = True) -> bool:
    """
    Apply one GSUB lookup across the run. Returns whether anything changed.

    `mask` restricts the lookup to glyphs whose shaping mask has that bit
    set. That is how a feature such as `half` is applied to the
    consonants before the base and to nothing else: the shaper sets the
    bit on exactly those glyphs, and the same lookup list is then safe to
    run over the whole syllable.
    """
    changed = False
    starters = first_glyphs(font, lookup) if use_filter else None
    index = 0
    while index < len(glyphs):
        if mask and not (glyphs[index].mask & mask):
            index += 1
            continue
        if starters is not None and glyphs[index].glyph not in starters:
            index += 1
            continue
        if font._skips(lookup, glyphs[index].glyph):
            index += 1
            continue
        consumed = _apply_gsub_at(font, lookup, glyphs, index, mask)
        if consumed:
            changed = True
            index += max(1, consumed)
        else:
            index += 1
    return changed


def _apply_gsub_at(font, lookup, glyphs, index, mask) -> int:
    kind = lookup["type"]
    for subtable in lookup["subtables"]:
        if kind == 1:
            if _single_substitution(font, subtable, glyphs, index):
                return 1
        elif kind == 2:
            consumed = _multiple_substitution(font, subtable, glyphs, index)
            if consumed:
                return consumed
        elif kind == 4:
            consumed = _ligature_substitution(
                font, lookup, subtable, glyphs, index)
            if consumed:
                return consumed
        elif kind == 5:
            if _context_substitution(font, lookup, subtable, glyphs, index,
                                     mask):
                return 1
        elif kind == 6:
            if _chaining_substitution(font, lookup, subtable, glyphs, index,
                                      mask):
                return 1
        else:
            font.unsupported_lookups[("GSUB", kind)] = (
                font.unsupported_lookups.get(("GSUB", kind), 0) + 1)
            return 0
    return 0


def _single_substitution(font, offset, glyphs, index) -> bool:
    data = font.data
    fmt = _u16(data, offset)
    coverage = font.coverage(offset + _u16(data, offset + 2))
    position = coverage.get(glyphs[index].glyph)
    if position is None:
        return False
    if fmt == 1:
        delta = _s16(data, offset + 4)
        glyphs[index].glyph = (glyphs[index].glyph + delta) & 0xFFFF
        return True
    if fmt == 2:
        count = _u16(data, offset + 4)
        if position >= count:
            return False
        glyphs[index].glyph = _u16(data, offset + 6 + position * 2)
        return True
    return False


def _multiple_substitution(font, offset, glyphs, index) -> int:
    data = font.data
    if _u16(data, offset) != 1:
        return 0
    coverage = font.coverage(offset + _u16(data, offset + 2))
    position = coverage.get(glyphs[index].glyph)
    if position is None or position >= _u16(data, offset + 4):
        return 0
    sequence = offset + _u16(data, offset + 6 + position * 2)
    count = _u16(data, sequence)
    replacements = [_u16(data, sequence + 2 + i * 2) for i in range(count)]
    if not replacements:
        # A zero-length sequence deletes the glyph. Legal, and rare enough
        # that treating it as "no match" would be a silent corruption.
        del glyphs[index]
        return 1

    original = glyphs[index]
    glyphs[index].glyph = replacements[0]
    glyphs[index].multiplied = True
    for step, replacement in enumerate(replacements[1:], start=1):
        glyphs.insert(index + step, ShapedGlyph(
            glyph=replacement, cluster=original.cluster,
            category=original.category, position=original.position,
            mask=original.mask, multiplied=True))
    return len(replacements)


def _ligature_substitution(font, lookup, offset, glyphs, index) -> int:
    data = font.data
    if _u16(data, offset) != 1:
        return 0
    coverage = font.coverage(offset + _u16(data, offset + 2))
    position = coverage.get(glyphs[index].glyph)
    if position is None or position >= _u16(data, offset + 4):
        return 0

    set_offset = offset + _u16(data, offset + 6 + position * 2)
    for i in range(_u16(data, set_offset)):
        ligature = set_offset + _u16(data, set_offset + 2 + i * 2)
        glyph = _u16(data, ligature)
        component_count = _u16(data, ligature + 2)
        components = [_u16(data, ligature + 4 + c * 2)
                      for c in range(component_count - 1)]
        matched = _match_forward(font, lookup, glyphs, index, components,
                                 lambda have, want: have == want)
        if matched is None:
            continue

        # The ligature replaces the first glyph and the matched components
        # are removed. Anything SKIPPED between them — marks, typically —
        # stays where it is, which is what lets a nukta survive a conjunct.
        glyphs[index].glyph = glyph
        glyphs[index].ligated = True
        for removed in sorted(matched, reverse=True):
            del glyphs[removed]
        return 1
    return 0


def _apply_nested(font, glyphs, index, records, table, mask) -> None:
    """Run the nested lookups a context rule names, at its given offsets."""
    for sequence_index, lookup_index in records:
        target = index + sequence_index
        if target >= len(glyphs):
            continue
        lookups = table["lookups"]
        if lookup_index >= len(lookups):
            continue
        nested = font.lookup(lookups[lookup_index], "GSUB")
        _apply_gsub_at(font, nested, glyphs, target, mask)


def _records(data, offset, count) -> list:
    return [(_u16(data, offset + i * 4), _u16(data, offset + i * 4 + 2))
            for i in range(count)]


def _context_substitution(font, lookup, offset, glyphs, index, mask) -> bool:
    data = font.data
    fmt = _u16(data, offset)
    table = font.gsub

    if fmt == 1:
        coverage = font.coverage(offset + _u16(data, offset + 2))
        position = coverage.get(glyphs[index].glyph)
        if position is None or position >= _u16(data, offset + 4):
            return False
        rule_set = offset + _u16(data, offset + 6 + position * 2)
        for i in range(_u16(data, rule_set)):
            rule = rule_set + _u16(data, rule_set + 2 + i * 2)
            glyph_count = _u16(data, rule)
            lookup_count = _u16(data, rule + 2)
            inputs = [_u16(data, rule + 4 + g * 2)
                      for g in range(glyph_count - 1)]
            if _match_forward(font, lookup, glyphs, index, inputs,
                              lambda have, want: have == want) is None:
                continue
            _apply_nested(font, glyphs, index,
                          _records(data, rule + 4 + (glyph_count - 1) * 2,
                                   lookup_count), table, mask)
            return True
        return False

    if fmt == 2:
        coverage = font.coverage(offset + _u16(data, offset + 2))
        if glyphs[index].glyph not in coverage:
            return False
        classes = font.class_def(offset + _u16(data, offset + 4))
        this_class = classes.get(glyphs[index].glyph, 0)
        count = _u16(data, offset + 6)
        if this_class >= count:
            return False
        set_offset = _u16(data, offset + 8 + this_class * 2)
        if not set_offset:
            return False
        rule_set = offset + set_offset
        for i in range(_u16(data, rule_set)):
            rule = rule_set + _u16(data, rule_set + 2 + i * 2)
            glyph_count = _u16(data, rule)
            lookup_count = _u16(data, rule + 2)
            inputs = [_u16(data, rule + 4 + g * 2)
                      for g in range(glyph_count - 1)]
            if _match_forward(
                    font, lookup, glyphs, index, inputs,
                    lambda have, want: classes.get(have, 0) == want) is None:
                continue
            _apply_nested(font, glyphs, index,
                          _records(data, rule + 4 + (glyph_count - 1) * 2,
                                   lookup_count), table, mask)
            return True
        return False

    if fmt == 3:
        glyph_count = _u16(data, offset + 2)
        lookup_count = _u16(data, offset + 4)
        coverages = [font.coverage(offset + _u16(data, offset + 6 + g * 2))
                     for g in range(glyph_count)]
        if glyphs[index].glyph not in coverages[0]:
            return False
        if _match_forward(
                font, lookup, glyphs, index, coverages[1:],
                lambda have, want: have in want) is None:
            return False
        _apply_nested(font, glyphs, index,
                      _records(data, offset + 6 + glyph_count * 2,
                               lookup_count), table, mask)
        return True
    return False


def _chain_format_3(font, offset) -> tuple:
    """Parse a format-3 chaining subtable once. See `_subtable_cache`."""
    cached = font._subtable_cache.get(offset)
    if cached is not None:
        return cached
    data = font.data
    cursor = offset + 2
    backtrack_count = _u16(data, cursor)
    backtrack = [font.coverage(offset + _u16(data, cursor + 2 + i * 2))
                 for i in range(backtrack_count)]
    cursor += 2 + backtrack_count * 2
    input_count = _u16(data, cursor)
    inputs = [font.coverage(offset + _u16(data, cursor + 2 + i * 2))
              for i in range(input_count)]
    cursor += 2 + input_count * 2
    lookahead_count = _u16(data, cursor)
    lookahead = [font.coverage(offset + _u16(data, cursor + 2 + i * 2))
                 for i in range(lookahead_count)]
    cursor += 2 + lookahead_count * 2
    records = _records(data, cursor + 2, _u16(data, cursor))
    cached = (backtrack, inputs, lookahead, records)
    font._subtable_cache[offset] = cached
    return cached


def _chaining_substitution(font, lookup, offset, glyphs, index, mask) -> bool:
    data = font.data
    fmt = _u16(data, offset)
    table = font.gsub

    if fmt == 3:
        backtrack, inputs, lookahead, records = _chain_format_3(font, offset)

        if not inputs or glyphs[index].glyph not in inputs[0]:
            return False
        matched = _match_forward(font, lookup, glyphs, index, inputs[1:],
                                 lambda have, want: have in want)
        if matched is None:
            return False
        last = matched[-1] if matched else index
        if _match_backward(font, lookup, glyphs, index, backtrack,
                           lambda have, want: have in want) is None:
            return False
        if _match_forward(font, lookup, glyphs, last, lookahead,
                          lambda have, want: have in want) is None:
            return False
        _apply_nested(font, glyphs, index, records, table, mask)
        return True

    if fmt in (1, 2):
        coverage = font.coverage(offset + _u16(data, offset + 2))
        if glyphs[index].glyph not in coverage:
            return False
        if fmt == 1:
            position = coverage[glyphs[index].glyph]
            count = _u16(data, offset + 4)
            if position >= count:
                return False
            set_offset = _u16(data, offset + 6 + position * 2)
            classes = None
            back_classes = ahead_classes = None
        else:
            back_classes = font.class_def(offset + _u16(data, offset + 4))
            classes = font.class_def(offset + _u16(data, offset + 6))
            ahead_classes = font.class_def(offset + _u16(data, offset + 8))
            this_class = classes.get(glyphs[index].glyph, 0)
            count = _u16(data, offset + 10)
            if this_class >= count:
                return False
            set_offset = _u16(data, offset + 12 + this_class * 2)
        if not set_offset:
            return False

        rule_set = offset + set_offset
        for i in range(_u16(data, rule_set)):
            rule = rule_set + _u16(data, rule_set + 2 + i * 2)
            cursor = rule
            backtrack_count = _u16(data, cursor)
            backtrack = [_u16(data, cursor + 2 + g * 2)
                         for g in range(backtrack_count)]
            cursor += 2 + backtrack_count * 2
            input_count = _u16(data, cursor)
            inputs = [_u16(data, cursor + 2 + g * 2)
                      for g in range(input_count - 1)]
            cursor += 2 + (input_count - 1) * 2
            lookahead_count = _u16(data, cursor)
            lookahead = [_u16(data, cursor + 2 + g * 2)
                         for g in range(lookahead_count)]
            cursor += 2 + lookahead_count * 2
            lookup_count = _u16(data, cursor)
            records = _records(data, cursor + 2, lookup_count)

            if fmt == 1:
                same = (lambda have, want: have == want)
                back_same = ahead_same = same
            else:
                same = (lambda have, want: classes.get(have, 0) == want)
                back_same = (
                    lambda have, want: back_classes.get(have, 0) == want)
                ahead_same = (
                    lambda have, want: ahead_classes.get(have, 0) == want)

            matched = _match_forward(font, lookup, glyphs, index, inputs, same)
            if matched is None:
                continue
            last = matched[-1] if matched else index
            if _match_backward(font, lookup, glyphs, index, backtrack,
                               back_same) is None:
                continue
            if _match_forward(font, lookup, glyphs, last, lookahead,
                              ahead_same) is None:
                continue
            _apply_nested(font, glyphs, index, records, table, mask)
            return True
    return False


# ── GPOS ────────────────────────────────────────────────────────────────────

def apply_gpos_lookup(font: OpenTypeFont, lookup: dict, glyphs: list) -> None:
    """Apply one GPOS lookup across the run."""
    index = 0
    while index < len(glyphs):
        if font._skips(lookup, glyphs[index].glyph):
            index += 1
            continue
        _apply_gpos_at(font, lookup, glyphs, index)
        index += 1


def _apply_gpos_at(font, lookup, glyphs, index) -> None:
    kind = lookup["type"]
    for subtable in lookup["subtables"]:
        if kind == 1:
            _single_position(font, subtable, glyphs, index)
        elif kind == 2:
            _pair_position(font, lookup, subtable, glyphs, index)
        elif kind == 4:
            if _mark_to_base(font, lookup, subtable, glyphs, index):
                return
        elif kind == 6:
            if _mark_to_mark(font, lookup, subtable, glyphs, index):
                return
        elif kind == 8:
            _chaining_position(font, lookup, subtable, glyphs, index)
        else:
            font.unsupported_lookups[("GPOS", kind)] = (
                font.unsupported_lookups.get(("GPOS", kind), 0) + 1)


_VALUE_FIELDS = (
    (0x0001, "x_placement"), (0x0002, "y_placement"),
    (0x0004, "x_advance"), (0x0008, "y_advance"),
)


def _value_size(value_format: int) -> int:
    return bin(value_format & 0xFFFF).count("1") * 2


def _read_value(data, offset, value_format) -> dict:
    out = {}
    cursor = offset
    for bit, name in _VALUE_FIELDS:
        if value_format & bit:
            out[name] = _s16(data, cursor)
            cursor += 2
    # Device tables occupy the remaining set bits; skipped deliberately,
    # since they only matter for hinted rasterisation at a fixed ppem and
    # a PDF is resolution-independent.
    return out


def _apply_value(glyph: ShapedGlyph, value: dict) -> None:
    glyph.x_offset += value.get("x_placement", 0)
    glyph.y_offset += value.get("y_placement", 0)
    glyph.x_advance += value.get("x_advance", 0)
    glyph.y_advance += value.get("y_advance", 0)


def _single_position(font, offset, glyphs, index) -> None:
    data = font.data
    fmt = _u16(data, offset)
    coverage = font.coverage(offset + _u16(data, offset + 2))
    position = coverage.get(glyphs[index].glyph)
    if position is None:
        return
    value_format = _u16(data, offset + 4)
    if fmt == 1:
        _apply_value(glyphs[index], _read_value(data, offset + 6, value_format))
    elif fmt == 2:
        size = _value_size(value_format)
        _apply_value(glyphs[index],
                     _read_value(data, offset + 8 + position * size,
                                 value_format))


def _pair_position(font, lookup, offset, glyphs, index) -> None:
    data = font.data
    fmt = _u16(data, offset)
    coverage = font.coverage(offset + _u16(data, offset + 2))
    position = coverage.get(glyphs[index].glyph)
    if position is None:
        return
    second = _next(font, lookup, glyphs, index)
    if second is None:
        return

    format_one = _u16(data, offset + 4)
    format_two = _u16(data, offset + 6)
    size_one, size_two = _value_size(format_one), _value_size(format_two)

    if fmt == 1:
        if position >= _u16(data, offset + 8):
            return
        set_offset = offset + _u16(data, offset + 10 + position * 2)
        count = _u16(data, set_offset)
        record = 2 + size_one + size_two
        for i in range(count):
            entry = set_offset + 2 + i * record
            if _u16(data, entry) != glyphs[second].glyph:
                continue
            _apply_value(glyphs[index],
                         _read_value(data, entry + 2, format_one))
            _apply_value(glyphs[second],
                         _read_value(data, entry + 2 + size_one, format_two))
            return
    elif fmt == 2:
        first_classes = font.class_def(offset + _u16(data, offset + 8))
        second_classes = font.class_def(offset + _u16(data, offset + 10))
        count_one = _u16(data, offset + 12)
        count_two = _u16(data, offset + 14)
        a = first_classes.get(glyphs[index].glyph, 0)
        b = second_classes.get(glyphs[second].glyph, 0)
        if a >= count_one or b >= count_two:
            return
        record = size_one + size_two
        entry = offset + 16 + (a * count_two + b) * record
        _apply_value(glyphs[index], _read_value(data, entry, format_one))
        _apply_value(glyphs[second],
                     _read_value(data, entry + size_one, format_two))


def _anchor(data, offset) -> tuple:
    return _s16(data, offset + 2), _s16(data, offset + 4)


def _mark_array(data, offset) -> list:
    count = _u16(data, offset)
    out = []
    for i in range(count):
        entry = offset + 2 + i * 4
        anchor_offset = _u16(data, entry + 2)
        out.append((_u16(data, entry),
                    _anchor(data, offset + anchor_offset)
                    if anchor_offset else None))
    return out


def _mark_to_base(font, lookup, offset, glyphs, index) -> bool:
    data = font.data
    if _u16(data, offset) != 1:
        return False
    mark_coverage = font.coverage(offset + _u16(data, offset + 2))
    mark_index = mark_coverage.get(glyphs[index].glyph)
    if mark_index is None:
        return False

    base_index_of = font.coverage(offset + _u16(data, offset + 4))
    previous = _previous(font, lookup, glyphs, index)
    # A mark attaches to the nearest preceding NON-MARK glyph. Walking
    # back over marks here is what makes a vowel sign attach to its
    # consonant rather than to an anusvara that happens to precede it.
    while previous is not None and font.is_mark(glyphs[previous].glyph):
        previous = _previous(font, lookup, glyphs, previous)
    if previous is None:
        return False
    base_index = base_index_of.get(glyphs[previous].glyph)
    if base_index is None:
        return False

    class_count = _u16(data, offset + 6)
    marks = _mark_array(data, offset + _u16(data, offset + 8))
    if mark_index >= len(marks):
        return False
    mark_class, mark_anchor = marks[mark_index]
    if mark_anchor is None or mark_class >= class_count:
        return False

    base_array = offset + _u16(data, offset + 10)
    if base_index >= _u16(data, base_array):
        return False
    anchor_offset = _u16(
        data, base_array + 2 + (base_index * class_count + mark_class) * 2)
    if not anchor_offset:
        return False
    base_x, base_y = _anchor(data, base_array + anchor_offset)
    mark_x, mark_y = mark_anchor

    # The anchors are expressed against the BASE's origin, but the mark is
    # drawn at the pen, which has already advanced past the base and past
    # anything between them. Without subtracting that, every mark lands one
    # base-width to the right — the reph of `कार्य` sits beside the य
    # instead of above it, and `शु` puts its vowel sign after the श.
    glyphs[index].x_offset = (
        base_x - mark_x - _advance_between(glyphs, previous, index)
        + glyphs[previous].x_offset)
    glyphs[index].y_offset = base_y - mark_y + glyphs[previous].y_offset
    # An attached mark takes no width of its own; the advance belongs to
    # the base it sits on.
    glyphs[index].x_advance = 0
    return True


def _advance_between(glyphs, base: int, mark: int) -> int:
    """Advance the pen accumulates travelling from `base` to `mark`."""
    return sum(glyphs[i].x_advance for i in range(base, mark))


def _mark_to_mark(font, lookup, offset, glyphs, index) -> bool:
    data = font.data
    if _u16(data, offset) != 1:
        return False
    mark_coverage = font.coverage(offset + _u16(data, offset + 2))
    mark_index = mark_coverage.get(glyphs[index].glyph)
    if mark_index is None:
        return False
    base_coverage = font.coverage(offset + _u16(data, offset + 4))

    previous = _previous(font, lookup, glyphs, index)
    if previous is None:
        return False
    base_index = base_coverage.get(glyphs[previous].glyph)
    if base_index is None:
        return False

    class_count = _u16(data, offset + 6)
    marks = _mark_array(data, offset + _u16(data, offset + 8))
    if mark_index >= len(marks):
        return False
    mark_class, mark_anchor = marks[mark_index]
    if mark_anchor is None or mark_class >= class_count:
        return False

    base_array = offset + _u16(data, offset + 10)
    if base_index >= _u16(data, base_array):
        return False
    anchor_offset = _u16(
        data, base_array + 2 + (base_index * class_count + mark_class) * 2)
    if not anchor_offset:
        return False
    base_x, base_y = _anchor(data, base_array + anchor_offset)
    mark_x, mark_y = mark_anchor

    glyphs[index].x_offset = (
        glyphs[previous].x_offset + base_x - mark_x
        - _advance_between(glyphs, previous, index))
    glyphs[index].y_offset = (glyphs[previous].y_offset + base_y - mark_y)
    glyphs[index].x_advance = 0
    return True


def _chaining_position(font, lookup, offset, glyphs, index) -> None:
    """
    Chained contextual positioning.

    Shares the matching logic with GSUB's chaining substitution but runs
    NESTED GPOS lookups, so it cannot simply call it.
    """
    data = font.data
    if _u16(data, offset) != 3:
        return
    cursor = offset + 2
    backtrack_count = _u16(data, cursor)
    backtrack = [font.coverage(offset + _u16(data, cursor + 2 + i * 2))
                 for i in range(backtrack_count)]
    cursor += 2 + backtrack_count * 2
    input_count = _u16(data, cursor)
    inputs = [font.coverage(offset + _u16(data, cursor + 2 + i * 2))
              for i in range(input_count)]
    cursor += 2 + input_count * 2
    lookahead_count = _u16(data, cursor)
    lookahead = [font.coverage(offset + _u16(data, cursor + 2 + i * 2))
                 for i in range(lookahead_count)]
    cursor += 2 + lookahead_count * 2
    records = _records(data, cursor + 2, _u16(data, cursor))

    if not inputs or glyphs[index].glyph not in inputs[0]:
        return
    matched = _match_forward(font, lookup, glyphs, index, inputs[1:],
                             lambda have, want: have in want)
    if matched is None:
        return
    last = matched[-1] if matched else index
    if _match_backward(font, lookup, glyphs, index, backtrack,
                       lambda have, want: have in want) is None:
        return
    if _match_forward(font, lookup, glyphs, last, lookahead,
                      lambda have, want: have in want) is None:
        return

    lookups = font.gpos["lookups"]
    for sequence_index, lookup_index in records:
        target = index + sequence_index
        if target >= len(glyphs) or lookup_index >= len(lookups):
            continue
        _apply_gpos_at(font, font.lookup(lookups[lookup_index], "GPOS"),
                       glyphs, target)
