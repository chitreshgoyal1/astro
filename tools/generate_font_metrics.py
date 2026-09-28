"""
Generate app/report/metrics.py from Adobe font metrics (V1.7 Part 21)
======================================================================
Reads AFM files for the base-14 faces and writes a Python module holding
one width per WinAnsi byte, per face.

WHY THE TABLE IS GENERATED AND THEN COMMITTED

    The PDF writer has to measure text to wrap a paragraph, centre a
    heading and fit a table column. Measuring needs the advance width of
    every glyph, and the base-14 faces are NOT embedded in the file — the
    viewer supplies them — so the widths must be known to the writer.

    Reading an AFM at run time would make the report depend on a font file
    being installed, which Part 34 forbids for the generation pipeline. So
    the table is produced once, here, and committed as data. Re-running this
    script and finding no diff is the check that it is still right.

USAGE

    python tools/generate_font_metrics.py \
        --afm Times-Roman=/path/Times-Roman.afm ... \
        --glyphlist /path/glyphlist.txt \
        --out app/report/metrics.py

SOURCE OF THE NUMBERS

    The URW++ Nimbus faces shipped with Ghostscript, which are metrically
    compatible with the Adobe base-14 by construction — that compatibility
    is the reason they exist. Glyph names come from Adobe's glyph list.
    Both are redistributable; neither font file is copied into this
    repository, only the integer advance widths, which are facts about
    spacing rather than a font program.
"""

from __future__ import annotations

import argparse
import datetime
import sys


def read_glyphlist(path: str) -> dict[str, str]:
    """Unicode character to Adobe glyph name."""
    mapping: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            name, _, codes = line.strip().partition(";")
            if not codes:
                continue
            points = codes.split()
            if len(points) != 1:
                continue            # ligature entries; not needed here
            char = chr(int(points[0], 16))
            mapping.setdefault(char, name)
    return mapping


def read_afm(path: str) -> dict[str, int]:
    """Glyph name to advance width, in 1/1000 em."""
    widths: dict[str, int] = {}
    with open(path, encoding="latin-1") as handle:
        in_chars = False
        for line in handle:
            if line.startswith("StartCharMetrics"):
                in_chars = True
                continue
            if line.startswith("EndCharMetrics"):
                break
            if not in_chars:
                continue
            width = None
            name = None
            for field in line.strip().split(";"):
                field = field.strip()
                if field.startswith("WX "):
                    width = int(float(field[3:]))
                elif field.startswith("N "):
                    name = field[2:].strip()
            if name is not None and width is not None:
                widths[name] = width
    return widths


def winansi_names(glyphs: dict[str, str]) -> list[str]:
    """
    The 256 glyph names of WinAnsiEncoding.

    Built from cp1252 rather than typed out: cp1252 IS WinAnsi for every
    code that has a character, and the undefined codes get the name PDF
    expects for them.
    """
    names = ["" for _ in range(256)]
    for code in range(32, 256):
        try:
            char = bytes([code]).decode("cp1252")
        except UnicodeDecodeError:
            continue
        name = glyphs.get(char)
        if name:
            names[code] = name
    # PDF's WinAnsiEncoding defines these three where cp1252 does not.
    names[160] = "space"
    names[173] = "hyphen"
    return names


HEADER = '''"""
Base-14 font metrics (V1.7 Part 21)
=====================================
Advance widths for the PDF base-14 faces, one entry per WinAnsi byte, in
units of 1/1000 em.

GENERATED FILE. Produced by tools/generate_font_metrics.py from the URW++
Nimbus AFM files, which are metrically compatible with the Adobe base-14 by
construction, and from Adobe's glyph list. Do not edit by hand: re-run the
generator.

These faces are NOT embedded in the PDF. A conforming viewer supplies them,
which is what keeps a report small and independent of any font being
installed. The writer still has to measure text to wrap a paragraph and fit
a table column, and that is what this table is for.

Generated {stamp} from:
{sources}
"""

from __future__ import annotations

#: Width used for a byte the face has no glyph for. The space width, so an
#: unexpected character costs the layout a space rather than nothing.
FALLBACK_WIDTH = {fallback}

'''


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--afm", action="append", required=True,
                        metavar="FACE=PATH",
                        help="PDF face name and the AFM file to read")
    parser.add_argument("--glyphlist", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    glyphs = read_glyphlist(args.glyphlist)
    names = winansi_names(glyphs)

    faces: dict[str, list[int]] = {}
    sources = []
    for item in args.afm:
        face, _, path = item.partition("=")
        widths = read_afm(path)
        sources.append(f"    {face:<20} {path}")
        faces[face] = [widths.get(name, 0) if name else 0 for name in names]

    fallback = faces[sorted(faces)[0]][32] or 250
    lines = [HEADER.format(
        stamp=datetime.date.today().isoformat(),
        sources="\n".join(sources),
        fallback=fallback)]

    lines.append("#: face name -> 256 advance widths, indexed by WinAnsi byte.")
    lines.append("WIDTHS: dict[str, tuple[int, ...]] = {")
    for face in sorted(faces):
        lines.append(f'    "{face}": (')
        row = faces[face]
        for start in range(0, 256, 16):
            chunk = ", ".join(str(w) for w in row[start:start + 16])
            lines.append(f"        {chunk},")
        lines.append("    ),")
    lines.append("}")
    lines.append("")
    lines.append('''

def text_width(text: str, face: str, size: float) -> float:
    """
    The width of `text` in points, set in `face` at `size`.

    Characters outside WinAnsi are measured at the fallback width. They are
    also unprintable in these faces, and `app/report/pdf.py` transliterates
    them before they reach here, so this is a guard rather than a path.
    """
    widths = WIDTHS.get(face) or WIDTHS["Times-Roman"]
    total = 0
    for char in text:
        code = ord(char)
        width = widths[code] if code < 256 else 0
        total += width or FALLBACK_WIDTH
    return total * size / 1000.0
''')

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    print(f"wrote {args.out}: {len(faces)} faces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
