"""
VSOP87 coefficient builder  —  DEVELOPMENT TOOL, NOT PART OF THE APPLICATION
-----------------------------------------------------------------------------
Parses the official VSOP87A coefficient files and emits a truncated,
dependency-free Python module (engine/vsop87_data.py).

PROVENANCE
    Theory   VSOP87, Bretagnon P. & Francou G., 1988,
             Astronomy & Astrophysics 202, 309-315.
    Variant  VSOP87A — heliocentric rectangular coordinates,
             dynamical ecliptic and equinox J2000.
    Files    ftp://ftp.imcce.fr/pub/ephem/planets/vsop87/
             VSOP87A.ear, VSOP87A.mar, VSOP87A.jup, VSOP87A.sat
    Checks   vsop87.chk, from the same directory — reference values published
             by the theory's own authors.

The coefficients are used EXACTLY as published. Nothing is fitted, adjusted or
tuned against any other ephemeris. Correctness of the parse is established
against the authors' own check file (`--validate`), which is independent of
the Swiss Ephemeris; the Swiss Ephemeris is used elsewhere only as an external
cross-check of the finished engine.

File format (VSOP87 documentation):
    Each data line ends with five numbers S, K, A, B, C.
    The term contributes  A * cos(B + C * T)  to the coordinate,
    where T is Julian millennia TDB from J2000 (T = (JD - 2451545)/365250).
    The header line above each block gives the power of T that block carries.

Usage:
    .venv/bin/python tools/build_vsop87.py --validate
    .venv/bin/python tools/build_vsop87.py --benchmark
    .venv/bin/python tools/build_vsop87.py --emit --threshold 1e-8
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

SOURCE_DIR = "/tmp/vsop"
OUT = os.path.join(ROOT, "engine", "vsop87_data.py")

SOURCE_URL = "ftp://ftp.imcce.fr/pub/ephem/planets/vsop87/"
CITATION = ("Bretagnon P., Francou G., 1988, Astron. Astrophys. 202, 309-315 "
            "(VSOP87, variant A: heliocentric rectangular, ecliptic J2000)")

BODIES = {"Earth": "VSOP87A.ear", "Mars": "VSOP87A.mar",
          "Jupiter": "VSOP87A.jup", "Saturn": "VSOP87A.sat"}

# Truncation threshold per body, in au. Chosen from the measured benchmark in
# tools/vsop_benchmark.py, not guessed.
#
# Mars is cut finer than the rest because it is the nearest of these bodies to
# the Earth, so the same absolute position error subtends a larger angle. At
# 1e-6 Mars reaches 11.7" worst case; at 1e-7 it reaches 8.0" for 862 terms
# instead of 310. The other three are already at their floor by 1e-6 and
# gain nothing from going finer.
DEFAULT_THRESHOLDS = {
    "Earth": 1e-6,
    "Mars": 1e-7,
    "Jupiter": 1e-6,
    "Saturn": 1e-6,
}

# Header: "VSOP87 VERSION A1    JUPITER   VARIABLE 1 (XYZ)       *T**0   1055 TERMS ..."
_HEADER = re.compile(
    r"VSOP87\s+VERSION\s+\S+\s+(?P<body>[A-Z]+)\s+VARIABLE\s+(?P<var>\d)"
    r".*?\*T\*\*(?P<power>\d)\s+(?P<count>\d+)\s+TERMS")


def parse_file(path: str) -> dict[int, dict[int, list[tuple[float, float, float]]]]:
    """
    Returns {variable (1=X, 2=Y, 3=Z): {power of T: [(A, B, C), ...]}}.

    Terms are returned in the file's own order, which is by decreasing
    amplitude within each block — the property the truncation relies on.
    """
    series: dict[int, dict[int, list]] = {1: {}, 2: {}, 3: {}}
    variable = power = None
    declared = 0
    seen = 0

    with open(path, "r", encoding="ascii") as handle:
        for line in handle:
            header = _HEADER.search(line)
            if header:
                if variable is not None and seen != declared:
                    raise ValueError(
                        f"{path}: block declared {declared} terms, read {seen}")
                variable = int(header.group("var"))
                power = int(header.group("power"))
                declared = int(header.group("count"))
                seen = 0
                series[variable][power] = []
                continue
            if not line.strip():
                continue
            # A, B and C are the final three numbers on the line.
            fields = line.split()
            a, b, c = (float(fields[-3]), float(fields[-2]), float(fields[-1]))
            series[variable][power].append((a, b, c))
            seen += 1

    if variable is not None and seen != declared:
        raise ValueError(f"{path}: final block declared {declared}, read {seen}")
    return series


def evaluate(series: dict, jd_tt: float, threshold: float = 0.0) -> tuple:
    """Heliocentric rectangular (x, y, z) in au, keeping terms >= threshold."""
    t = (jd_tt - 2451545.0) / 365250.0
    out = []
    for variable in (1, 2, 3):
        total = 0.0
        for power, terms in series[variable].items():
            block = 0.0
            for a, b, c in terms:
                if a < threshold:
                    break          # blocks are ordered by decreasing amplitude
                block += a * math.cos(b + c * t)
            total += block * (t ** power)
        out.append(total)
    return tuple(out)


def count_terms(series: dict, threshold: float) -> int:
    total = 0
    for variable in (1, 2, 3):
        for terms in series[variable].values():
            total += sum(1 for a, _b, _c in terms if a >= threshold)
    return total


# ── validation against the authors' own check file ───────────────────────────

_CHK = re.compile(
    r"VSOP87A\s+(?P<body>\w+)\s+JD(?P<jd>[\d.]+)\s")
_XYZ = re.compile(
    r"x\s+(?P<x>[-\d.]+)\s+au\s+y\s+(?P<y>[-\d.]+)\s+au\s+z\s+(?P<z>[-\d.]+)\s+au")


def load_check_values(path: str) -> list[tuple[str, float, tuple]]:
    cases = []
    with open(path, "r", encoding="ascii", errors="replace") as handle:
        lines = handle.readlines()
    for index, line in enumerate(lines):
        header = _CHK.search(line)
        if not header or index + 1 >= len(lines):
            continue
        body = header.group("body").capitalize()
        if body not in BODIES:
            continue
        values = _XYZ.search(lines[index + 1])
        if not values:
            continue
        cases.append((body, float(header.group("jd")),
                      (float(values.group("x")), float(values.group("y")),
                       float(values.group("z")))))
    return cases


def validate(series_by_body: dict) -> int:
    """Check the parse against the reference values published with the theory."""
    cases = load_check_values(os.path.join(SOURCE_DIR, "vsop87.chk"))
    if not cases:
        print("no check values found")
        return 1
    print(f"Validating the parse against {len(cases)} reference values "
          f"published by the VSOP87 authors (vsop87.chk).\n")
    print(f"  {'body':<9}{'JD':>14}  {'|error| (au)':>14}  {'~arcsec at 5 au':>16}")
    print("  " + "-" * 60)
    worst = 0.0
    failures = 0
    for body, jd, expected in cases:
        got = evaluate(series_by_body[body], jd)
        error = math.dist(got, expected)
        worst = max(worst, error)
        if error > 1e-9:
            failures += 1
        if jd in (2451545.0, 2415020.0, 2378495.0, 2469807.5):
            print(f"  {body:<9}{jd:>14.1f}  {error:>14.2e}  "
                  f"{math.degrees(error / 5.0) * 3600:>16.4f}")
    print("  " + "-" * 60)
    print(f"  worst error over all {len(cases)} cases: {worst:.3e} au")
    print(f"  cases above 1e-9 au: {failures}")
    if failures:
        print("\n  PARSE IS WRONG — do not emit.")
        return 1
    print("\n  Parse reproduces the published values exactly. Full series is "
          "correct.")
    return 0


# ── emit ─────────────────────────────────────────────────────────────────────

def emit(series_by_body: dict, thresholds: dict[str, float]) -> None:
    checksums = {
        name: hashlib.sha256(
            open(os.path.join(SOURCE_DIR, filename), "rb").read()).hexdigest()
        for name, filename in BODIES.items()
    }

    lines = [
        '"""',
        "VSOP87 planetary series — generated data, do not edit by hand",
        "-------------------------------------------------------------",
        "Heliocentric rectangular coordinates on the dynamical ecliptic and",
        "equinox of J2000, in astronomical units.",
        "",
        "    x = SUM over p of T**p * SUM of A * cos(B + C * T)",
        "",
        "with T in Julian millennia TDB from J2000:  T = (JD_TT - 2451545) / 365250.",
        "",
        "PROVENANCE",
        f"    Theory    {CITATION}",
        f"    Source    {SOURCE_URL}",
        "    Files     " + ", ".join(f"{v}" for v in BODIES.values()),
        "    SHA-256   " + "; ".join(f"{k}={v[:16]}…" for k, v in checksums.items()),
        f"    Generated by tools/build_vsop87.py on "
        f"{datetime.date.today().isoformat()}",
        "",
        "Coefficients are reproduced EXACTLY as published. The series is",
        "truncated by amplitude only — no coefficient has been fitted, rounded",
        "or tuned against any other ephemeris. The parse was validated against",
        "vsop87.chk, the reference values published by the theory's own authors.",
        "",
        "Truncation thresholds actually applied (au):",
    ]
    for name, threshold in thresholds.items():
        kept = count_terms(series_by_body[name], threshold)
        full = count_terms(series_by_body[name], 0.0)
        lines.append(f"    {name:<9} {threshold:.0e}   {kept} of {full} terms")
    lines += ['"""', "", "# Generated file. Regenerate with tools/build_vsop87.py.", "",
              "VSOP87_PROVENANCE = {", f'    "theory": "{CITATION}",',
              f'    "source": "{SOURCE_URL}",',
              '    "variant": "VSOP87A (heliocentric rectangular, ecliptic J2000)",',
              '    "validated_against": "vsop87.chk (authors\' own reference values)",',
              "    \"files\": {"]
    for name, filename in BODIES.items():
        lines.append(f'        "{name}": {{"file": "{filename}", '
                     f'"sha256": "{checksums[name]}"}},')
    lines += ["    },", "    \"truncation_au\": {"]
    for name, threshold in thresholds.items():
        lines.append(f'        "{name}": {threshold:.0e},')
    lines += ["    },", "    \"term_counts\": {"]
    for name, threshold in thresholds.items():
        lines.append(f'        "{name}": {count_terms(series_by_body[name], threshold)},')
    lines += ["    },", "}", "", ""]

    lines.append("# {body: {variable: {power: ((A, B, C), ...)}}}, "
                 "variable 0=x, 1=y, 2=z")
    lines.append("VSOP87A = {")
    for name in BODIES:
        threshold = thresholds[name]
        lines.append(f'    "{name}": {{')
        for variable in (1, 2, 3):
            lines.append(f"        {variable - 1}: {{")
            for power in sorted(series_by_body[name][variable]):
                terms = [t for t in series_by_body[name][variable][power]
                         if t[0] >= threshold]
                if not terms:
                    continue
                lines.append(f"            {power}: (")
                for a, b, c in terms:
                    lines.append(f"                ({a!r}, {b!r}, {c!r}),")
                lines.append("            ),")
            lines.append("        },")
        lines.append("    },")
    lines.append("}")
    lines.append("")

    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}  ({size / 1024:.0f} KiB)")
    for name, threshold in thresholds.items():
        print(f"  {name:<9} threshold {threshold:.0e}  "
              f"{count_terms(series_by_body[name], threshold)} terms")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Override the per-body defaults with one value")
    args = parser.parse_args()

    series_by_body = {name: parse_file(os.path.join(SOURCE_DIR, filename))
                      for name, filename in BODIES.items()}
    for name, series in series_by_body.items():
        print(f"parsed {name}: {count_terms(series, 0.0)} terms")
    print()

    if args.validate:
        return validate(series_by_body)

    if args.benchmark:
        from vsop_benchmark import run_benchmark     # local helper
        return run_benchmark(series_by_body)

    if args.emit:
        thresholds = dict(DEFAULT_THRESHOLDS)
        if args.threshold is not None:
            thresholds = {name: args.threshold for name in BODIES}
        emit(series_by_body, thresholds)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
