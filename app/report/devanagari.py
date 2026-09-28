"""
Devanagari shaping (V1.8 Part 16)
-----------------------------------
Turns a Hindi string into positioned glyphs.

WHY A CODEPOINT-TO-GLYPH MAP IS NOT ENOUGH

    Three things happen in Devanagari that no Latin renderer has to do.

    REORDERING. `कि` is written क then ि, and drawn ि then क. The vowel
    sign precedes the consonant it belongs to on the page and follows it
    in the string. A renderer that emits glyphs in string order draws
    `कि` as two shapes in the wrong order, which a reader of Hindi reads
    as a different word or as nonsense.

    CONJUNCTS. `क्ष` is three codepoints — क, ्, ष — and one shape. Not a
    kerned pair: a distinct glyph that looks like neither letter. So does
    `स्प` in `बृहस्पति`, and so does the small `्र` hanging under the ग of
    `ग्रह`.

    MARK POSITIONING. `बृ` puts a mark under ब at a position that depends
    on ब's outline. The font carries an anchor per base glyph; using a
    fixed offset puts the mark through the letter.

    All three are why V1.7 refused to emit a Hindi PDF rather than emit
    one that looked plausible to somebody who could not read it.

WHAT THIS IMPLEMENTS

    The OpenType Indic v2 (`dev2`) model, for Devanagari, in the order the
    specification sets: categorise, segment into syllables, find the base
    consonant, apply the basic features to the glyph ranges each one
    governs, reorder, then apply the presentation features and GPOS.

    The one place this deliberately simplifies is reph placement, which is
    documented at `_reorder`.
"""

from __future__ import annotations

from typing import Optional

from .opentype import OpenTypeFont, ShapedGlyph
from .otlayout import apply_gpos_lookup, apply_gsub_lookup

# ── categories ──────────────────────────────────────────────────────────────

CAT_OTHER = 0
CAT_CONSONANT = 1
CAT_VOWEL = 2          # independent vowel
CAT_NUKTA = 3
CAT_HALANT = 4
CAT_MATRA = 5          # dependent vowel sign
CAT_MODIFIER = 6       # anusvara, candrabindu, visarga
CAT_ZWJ = 7
CAT_ZWNJ = 8
CAT_PLACEHOLDER = 9    # digits, danda, avagraha, spaces — syllable breakers

VIRAMA = 0x094D
RA = 0x0930
NUKTA = 0x093C
ZWJ = 0x200D
ZWNJ = 0x200C

#: Matra positions. `PRE` is the one that reorders.
POS_PRE = 1
POS_ABOVE = 2
POS_BELOW = 3
POS_POST = 4

#: U+093F DEVANAGARI VOWEL SIGN I is the only pre-base matra in the block.
#: Listed as a set rather than a comparison so that adding a script later
#: does not silently inherit Devanagari's answer.
PRE_BASE_MATRAS = frozenset({0x093F})

_ABOVE_MATRAS = frozenset(
    {0x093A, 0x0945, 0x0946, 0x0947, 0x0948, 0x0951, 0x0953, 0x0954,
     0x0955})
_BELOW_MATRAS = frozenset(
    {0x0941, 0x0942, 0x0943, 0x0944, 0x0956, 0x0957, 0x0962, 0x0963,
     0x0952})
_POST_MATRAS = frozenset(
    {0x093B, 0x093E, 0x0949, 0x094A, 0x094B, 0x094C, 0x094E, 0x094F})


def category(code: int) -> int:
    """The Indic syllabic category of one codepoint."""
    if code == ZWJ:
        return CAT_ZWJ
    if code == ZWNJ:
        return CAT_ZWNJ
    if code == VIRAMA:
        return CAT_HALANT
    if code == NUKTA:
        return CAT_NUKTA
    if 0x0900 <= code <= 0x0902 or code == 0x0903:
        return CAT_MODIFIER
    if 0x0904 <= code <= 0x0914 or code in (0x0960, 0x0961):
        return CAT_VOWEL
    if 0x0972 <= code <= 0x0977:
        return CAT_VOWEL
    if 0x0915 <= code <= 0x0939 or 0x0958 <= code <= 0x095F:
        return CAT_CONSONANT
    if 0x0978 <= code <= 0x097F:
        return CAT_CONSONANT
    if (code in PRE_BASE_MATRAS or code in _ABOVE_MATRAS
            or code in _BELOW_MATRAS or code in _POST_MATRAS):
        return CAT_MATRA
    if 0x0900 <= code <= 0x097F:
        return CAT_PLACEHOLDER
    return CAT_OTHER


def matra_position(code: int) -> int:
    if code in PRE_BASE_MATRAS:
        return POS_PRE
    if code in _ABOVE_MATRAS:
        return POS_ABOVE
    if code in _BELOW_MATRAS:
        return POS_BELOW
    return POS_POST


def is_devanagari(text: str) -> bool:
    return any(0x0900 <= ord(ch) <= 0x097F for ch in text)


def _is_devanagari_char(code: int) -> bool:
    return 0x0900 <= code <= 0x097F or code in (ZWJ, ZWNJ)


def script_runs(text: str) -> list[tuple[bool, str]]:
    """
    Split a string into alternating Devanagari and non-Devanagari runs.

    MIXED TEXT IS THE NORMAL CASE, NOT AN EDGE CASE. V1.7's Hindi
    templates keep technical identifiers untranslated on purpose — a
    Hindi report says `BPHS 11.3` and `D9` and `Shadbala` — so a Hindi
    page is mostly Devanagari with Latin embedded in it.

    That matters because the bundled Devanagari face has no Latin
    letters. Sending a whole mixed line through it draws every English
    word as a row of empty boxes, which is exactly the kind of
    confidently-wrong output V1.7 refused to produce. Each run therefore
    goes to the face that can draw it.

    Digits, spaces and punctuation are NEUTRAL: they join whichever run
    is in progress, so `भाव 5` keeps its space and its digit in one
    measurement rather than splitting into three runs whose widths are
    summed with rounding between them.
    """
    if not text:
        return []
    runs: list[tuple[bool, str]] = []
    current: list[str] = []
    current_is_deva: Optional[bool] = None

    for char in text:
        code = ord(char)
        if _is_devanagari_char(code):
            kind: Optional[bool] = True
        elif char.isspace() or (code < 128 and not char.isalnum()):
            kind = None                    # neutral: stays in the run
        elif code < 128:
            kind = False
        else:
            # Non-ASCII that is not Devanagari — IAST diacritics, dashes.
            # The Latin face handles them through WinAnsi or the
            # transliteration table.
            kind = False

        if kind is None:
            if current_is_deva is None:
                current_is_deva = False
            current.append(char)
            continue
        if current_is_deva is None or kind == current_is_deva:
            current_is_deva = kind
            current.append(char)
            continue
        runs.append((current_is_deva, "".join(current)))
        current = [char]
        current_is_deva = kind

    if current:
        runs.append((bool(current_is_deva), "".join(current)))
    return runs


# ── shaping masks ───────────────────────────────────────────────────────────
#
# A feature such as `half` must reach the consonants BEFORE the base and
# nothing else, while `blwf` must reach those after it. Rather than slicing
# the run per feature — which would break ligature lookups that need to see
# their neighbours — each glyph carries a bitmask of the features it
# participates in, and a lookup is applied only where its bit is set.

M_GENERAL = 1 << 0     # locl, nukt, akhn, cjct, and the presentation set
M_RPHF = 1 << 1
M_BLWF = 1 << 2
M_HALF = 1 << 3
M_RKRF = 1 << 4

#: Order matters and is the specification's, not a preference. `rphf`
#: before `blwf` because a reph is not a below-base ra; `half` after both
#: because a consonant that already took a below-base form must not also
#: take a half form.
BASIC_FEATURES = (
    ("locl", M_GENERAL),
    ("nukt", M_GENERAL),
    ("akhn", M_GENERAL),
    ("rphf", M_RPHF),
    ("rkrf", M_RKRF),
    ("blwf", M_BLWF),
    ("half", M_HALF),
    ("cjct", M_GENERAL),
)

#: Applied to the whole reordered run.
PRESENTATION_FEATURES = ("pres", "abvs", "blws", "psts", "haln", "calt",
                         "clig", "liga")

POSITIONING_FEATURES = ("abvm", "blwm", "dist", "kern", "mark", "mkmk")

#: `dev2` first. A font carrying both encodes two different shaping
#: models under them, and the older `deva` tables assume the client does
#: reordering the new ones expect the font to handle.
SCRIPT_TAGS = ("dev2", "deva")


# ── syllable segmentation ───────────────────────────────────────────────────

def _syllables(codes: list[int]) -> list[tuple[int, int]]:
    """
    Split into (start, end) syllable spans.

    A consonant syllable is `[C [N] H]* C [N] [H] [M]* [SM]*`; a vowel
    syllable is `V [N] [M]* [SM]*`. Anything else is its own span, which
    is what keeps digits, dandas and Latin text out of the reordering
    machinery entirely.
    """
    spans: list[tuple[int, int]] = []
    index = 0
    length = len(codes)

    while index < length:
        start = index
        cat = category(codes[index])

        if cat in (CAT_CONSONANT, CAT_VOWEL):
            index += 1
            if cat == CAT_CONSONANT:
                # Consonant + halant runs, each optionally with a nukta.
                while index < length:
                    if (index < length
                            and category(codes[index]) == CAT_NUKTA):
                        index += 1
                    if (index < length
                            and category(codes[index]) == CAT_HALANT):
                        index += 1
                        # A halant may be followed by ZWJ/ZWNJ requesting
                        # an explicit form. Consumed here so it stays in
                        # the syllable and reaches the lookups.
                        while (index < length
                               and category(codes[index]) in (CAT_ZWJ,
                                                              CAT_ZWNJ)):
                            index += 1
                        if (index < length
                                and category(codes[index]) == CAT_CONSONANT):
                            index += 1
                            continue
                        break
                    break
            else:
                if index < length and category(codes[index]) == CAT_NUKTA:
                    index += 1

            while index < length and category(codes[index]) == CAT_MATRA:
                index += 1
            while index < length and category(codes[index]) == CAT_MODIFIER:
                index += 1
        else:
            index += 1

        spans.append((start, index))
    return spans


# ── base consonant ──────────────────────────────────────────────────────────

def _find_base(codes: list[int], start: int, end: int,
               has_reph: bool) -> Optional[int]:
    """
    The index of the syllable's base consonant.

    Devanagari uses BASE_POS_LAST: the base is the last consonant of the
    cluster, EXCEPT that a ra which follows a halant is a below-base form
    (the `्र` rakar) and cannot be the base. So the search walks backwards
    past any such ra.

    The reph — an initial `र्` before another consonant — is excluded by
    `has_reph`, because it is a mark above the base and not the base.
    """
    first = start + 2 if has_reph else start
    index = end - 1
    while index >= first:
        if category(codes[index]) != CAT_CONSONANT:
            index -= 1
            continue
        if (codes[index] == RA and index > first
                and category(codes[index - 1]) == CAT_HALANT):
            index -= 1
            continue
        return index
    # Every consonant was a below-base ra, so the first one is the base
    # after all: `र्` alone is a ra, not a floating rakar.
    for index in range(first, end):
        if category(codes[index]) == CAT_CONSONANT:
            return index
    return None


def _has_reph(codes: list[int], start: int, end: int) -> bool:
    """
    Whether the syllable opens with a reph.

    `र` + halant + another consonant. The trailing consonant matters: `र्`
    at the end of a word is a dead ra with a visible virama, not a reph
    looking for something to sit on.
    """
    if end - start < 3:
        return False
    if codes[start] != RA or category(codes[start + 1]) != CAT_HALANT:
        return False
    # An explicit ZWJ after the halant requests the full form and
    # suppresses the reph.
    if start + 2 < end and codes[start + 2] == ZWJ:
        return False
    return any(category(codes[i]) == CAT_CONSONANT
               for i in range(start + 2, end))


# ── the shaper ──────────────────────────────────────────────────────────────

class DevanagariShaper:
    """
    Shapes Devanagari with one font. Stateless between calls; the font's
    parsed lookups are cached on the font object.
    """

    def __init__(self, font: OpenTypeFont):
        self.font = font
        self._basic = {
            tag: font.feature_lookups(font.gsub, SCRIPT_TAGS, tag)
            for tag, _mask in BASIC_FEATURES}
        self._presentation = {
            tag: font.feature_lookups(font.gsub, SCRIPT_TAGS, tag)
            for tag in PRESENTATION_FEATURES}
        self._positioning = {
            tag: font.feature_lookups(font.gpos, SCRIPT_TAGS, tag)
            for tag in POSITIONING_FEATURES}

    # ── public ──────────────────────────────────────────────────────────

    def shape(self, text: str) -> list[ShapedGlyph]:
        """Positioned glyphs for one string, in visual order."""
        codes = [ord(ch) for ch in text]
        out: list[ShapedGlyph] = []
        for start, end in _syllables(codes):
            out.extend(self._shape_syllable(codes, start, end))

        for tag in PRESENTATION_FEATURES:
            for offset in self._presentation.get(tag, ()):
                apply_gsub_lookup(
                    self.font, self.font.lookup(offset, "GSUB"), out,
                    mask=M_GENERAL)

        for glyph in out:
            glyph.x_advance = self.font.advance(glyph.glyph)

        for tag in POSITIONING_FEATURES:
            for offset in self._positioning.get(tag, ()):
                apply_gpos_lookup(
                    self.font, self.font.lookup(offset, "GPOS"), out)
        return out

    # ── one syllable ────────────────────────────────────────────────────

    def _shape_syllable(self, codes, start, end) -> list[ShapedGlyph]:
        glyphs = [
            ShapedGlyph(glyph=self.font.glyph_for(codes[i]), cluster=i,
                        category=category(codes[i]), mask=M_GENERAL)
            for i in range(start, end)]
        if not glyphs:
            return []

        # ZWJ and ZWNJ are requests to the shaper, not glyphs. They are
        # kept through substitution — the font's lookups match on them —
        # and dropped before output.
        has_reph = _has_reph(codes, start, end)
        base = _find_base(codes, start, end, has_reph)

        for offset, glyph in enumerate(glyphs):
            index = start + offset
            code = codes[index]
            if glyph.category == CAT_MATRA:
                glyph.position = matra_position(code)

        if has_reph:
            glyphs[0].mask |= M_RPHF
            glyphs[1].mask |= M_RPHF

        if base is not None:
            base_offset = base - start
            first = 2 if has_reph else 0
            for offset in range(first, len(glyphs)):
                index = start + offset
                if category(codes[index]) != CAT_CONSONANT:
                    continue
                if offset == base_offset:
                    continue
                preceded_by_halant = (
                    index > start
                    and category(codes[index - 1]) == CAT_HALANT)
                if codes[index] == RA and preceded_by_halant:
                    # The rakar. `rkrf` in fonts that have it, `blwf`
                    # otherwise; both bits are set and only the feature
                    # the font actually carries will match.
                    glyphs[offset].mask |= M_BLWF | M_RKRF
                    glyphs[offset - 1].mask |= M_BLWF | M_RKRF
                elif offset < base_offset:
                    glyphs[offset].mask |= M_HALF
                    if offset + 1 < len(glyphs) and \
                            glyphs[offset + 1].category == CAT_HALANT:
                        glyphs[offset + 1].mask |= M_HALF
                else:
                    glyphs[offset].mask |= M_BLWF
                    if offset > 0 and glyphs[offset - 1].category == CAT_HALANT:
                        glyphs[offset - 1].mask |= M_BLWF

        for tag, mask in BASIC_FEATURES:
            for offset in self._basic.get(tag, ()):
                apply_gsub_lookup(
                    self.font, self.font.lookup(offset, "GSUB"), glyphs,
                    mask=mask)

        glyphs = self._reorder(glyphs, codes, start, base, has_reph)
        return [g for g in glyphs if g.category not in (CAT_ZWJ, CAT_ZWNJ)]

    # ── reordering ──────────────────────────────────────────────────────

    def _reorder(self, glyphs, codes, start, base, has_reph) -> list:
        """
        Move the pre-base matra and the reph into visual order.

        PRE-BASE MATRA. `ि` is drawn to the left of the entire cluster it
        belongs to, so it moves to the front of the syllable. This is the
        step that makes `कि` and `क्रि` come out right, and its absence is
        the single most visible shaping error in Devanagari.

        REPH. Devanagari's reph is drawn above the syllable and is placed,
        in glyph order, after the base and before any post-base matra —
        `REPH_POS_BEFORE_POST` in the Indic model. The simplification here
        is that the reph is moved to the end of the syllable's consonant
        run rather than negotiated against below-base forms; for the
        Devanagari block, where no post-base consonant forms exist, the
        two agree.
        """
        pre_matras = [g for g in glyphs
                      if g.category == CAT_MATRA and g.position == POS_PRE]
        rest = [g for g in glyphs
                if not (g.category == CAT_MATRA and g.position == POS_PRE)]

        if has_reph and rest:
            # The reph glyph is whatever the `rphf` lookups left at the
            # front. If they substituted nothing — a font without the
            # feature — there is no reph to move and the ra stays put.
            reph = rest[0]
            if reph.mask & M_RPHF and reph.glyph != self.font.glyph_for(RA):
                rest = rest[1:]
                insert_at = len(rest)
                for index, glyph in enumerate(rest):
                    if (glyph.category == CAT_MATRA
                            and glyph.position == POS_POST):
                        insert_at = index
                        break
                    if glyph.category == CAT_MODIFIER:
                        insert_at = index
                        break
                rest.insert(insert_at, reph)

        return pre_matras + rest


# ── measurement ─────────────────────────────────────────────────────────────

def shaped_width(glyphs, font: OpenTypeFont, size: float) -> float:
    """Advance width of a shaped run, in points."""
    total = sum(glyph.x_advance for glyph in glyphs)
    return total * size / font.units_per_em
