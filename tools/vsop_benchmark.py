"""
VSOP87 benchmark  —  DEVELOPMENT TOOL, NOT PART OF THE APPLICATION
-------------------------------------------------------------------
Answers the two questions Part 1 of the V1.2 brief poses:

  1. Does swapping VSOP87 in for Jupiter and Saturn alone reach the accuracy
     target, or does EARTH also need VSOP87? Geocentric longitude depends on
     both the planet's and the Earth's heliocentric position, so an error in
     the Earth's position projects onto the planet's apparent direction.

     Configuration A:  current Keplerian Earth + VSOP Jupiter/Saturn
     Configuration B:  VSOP Earth            + VSOP Jupiter/Saturn

  2. What is the smallest truncation that still meets the target?

The Swiss Ephemeris is used here ONLY to measure the finished result. No
coefficient is fitted, chosen or adjusted to reduce the measured difference;
the truncation threshold is picked on amplitude alone and the error is then
reported, whatever it turns out to be.

Run:
    .venv/bin/python tools/vsop_benchmark.py
"""

from __future__ import annotations

import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import swisseph as swe                                    # noqa: E402

from engine import ephemeris as eph                       # noqa: E402
from build_vsop87 import BODIES, SOURCE_DIR, count_terms, evaluate, parse_file  # noqa: E402

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED
SWE_BODY = {"Jupiter": swe.JUPITER, "Saturn": swe.SATURN}
SANSKRIT = {"Jupiter": "Guru", "Saturn": "Shani"}

_LIGHT_TIME_PER_AU = 0.005775518331
_ABERRATION = 20.49552 / 3600.0


def make_position_function(series_by_body, thresholds, vsop_earth: bool):
    """Heliocentric xyz using VSOP for the giants, optionally also for Earth."""
    def position(body: str, jd_tt: float):
        if body == "Earth" and not vsop_earth:
            return eph.heliocentric_xyz("Earth", jd_tt)
        if body in series_by_body:
            return evaluate(series_by_body[body], jd_tt, thresholds[body])
        return eph.heliocentric_xyz(body, jd_tt)
    return position


def apparent_longitude(body: str, jd_tt: float, position) -> float:
    """
    Geocentric apparent tropical longitude, using the same pipeline the engine
    uses: light-time iteration, annual aberration, precession, nutation.
    """
    ex, ey, ez = position("Earth", jd_tt)
    px, py, pz = position(body, jd_tt)
    for _ in range(3):
        dx, dy, dz = px - ex, py - ey, pz - ez
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        px, py, pz = position(body, jd_tt - distance * _LIGHT_TIME_PER_AU)

    dx, dy, dz = px - ex, py - ey, pz - ez
    lon = math.degrees(math.atan2(dy, dx)) % 360.0
    lat = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
    lon = (lon + eph.precession_in_longitude(jd_tt)) % 360.0
    sun_lon = eph.sun_true_longitude(jd_tt)
    lon += -_ABERRATION * math.cos(math.radians(sun_lon - lon)) \
        / math.cos(math.radians(lat))
    d_psi, _ = eph.nutation(jd_tt)
    return (lon + d_psi) % 360.0


def arcsec(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0) * 3600.0


def sample_dates(step_days: float = 29.3) -> list[float]:
    """Dense sweep across the supported range."""
    start = swe.julday(1800, 1, 1, 0.0)
    end = swe.julday(2050, 1, 1, 0.0)
    dates = []
    jd = start
    while jd < end:
        dates.append(jd)
        jd += step_days
    return dates


def summarise(errors: list[float]) -> dict:
    ordered = sorted(errors)
    return {
        "n": len(ordered),
        "mean": statistics.fmean(ordered),
        "median": statistics.median(ordered),
        "p95": ordered[min(int(0.95 * len(ordered)), len(ordered) - 1)],
        "max": ordered[-1],
    }


def measure(position, dates) -> dict[str, dict]:
    out = {}
    for name in ("Jupiter", "Saturn"):
        errors = []
        for jd in dates:
            jd_tt = eph.jd_ut_to_tt(jd)
            values, _ = swe.calc_ut(jd, SWE_BODY[name], FLAGS)
            errors.append(arcsec(apparent_longitude(name, jd_tt, position),
                                 values[0]))
        out[name] = summarise(errors)
    return out


def show(label: str, result: dict) -> None:
    print(f"  {label}")
    for name, stats in result.items():
        print(f"    {name:<9} mean {stats['mean']:8.2f}\"  median "
              f"{stats['median']:8.2f}\"  p95 {stats['p95']:8.2f}\"  "
              f"max {stats['max']:8.2f}\" ({stats['max'] / 60:5.2f}')")


def run_benchmark(series_by_body) -> int:
    dates = sample_dates()
    print(f"Benchmarking against Swiss Ephemeris at {len(dates)} dates, "
          f"1800-2050.\n")

    # ── baseline: the current engine ─────────────────────────────────────────
    baseline = {}
    for name in ("Jupiter", "Saturn"):
        errors = []
        for jd in dates:
            jd_tt = eph.jd_ut_to_tt(jd)
            values, _ = swe.calc_ut(jd, SWE_BODY[name], FLAGS)
            errors.append(arcsec(
                eph.planet_apparent_longitude(SANSKRIT[name], jd_tt), values[0]))
        baseline[name] = summarise(errors)
    print("BASELINE — current Keplerian elements for everything")
    show("", baseline)
    print()

    # ── question 1: does Earth need VSOP too? ────────────────────────────────
    full = {name: 0.0 for name in BODIES}
    print("QUESTION 1 — is VSOP for the giants enough, or does Earth need it too?")
    print("  (full untruncated series, so this isolates the Earth question)\n")
    a = measure(make_position_function(series_by_body, full, vsop_earth=False), dates)
    show("A: Keplerian Earth + VSOP Jupiter/Saturn", a)
    b = measure(make_position_function(series_by_body, full, vsop_earth=True), dates)
    show("B: VSOP Earth      + VSOP Jupiter/Saturn", b)
    print()
    verdict = max(a[n]["max"] for n in a) / max(b[n]["max"] for n in b)
    print(f"  Configuration A is {verdict:.1f}x worse than B at worst case.")
    print("  => Earth's heliocentric position is " +
          ("ALSO a limiting factor; VSOP Earth is required."
           if verdict > 1.5 else "not the limiting factor."))
    print()

    # ── question 2: how far can the series be truncated? ─────────────────────
    print("QUESTION 2 — smallest truncation that still meets the target\n")
    print(f"  {'threshold':>10} {'terms':>7}  {'Jupiter max':>13}  "
          f"{'Saturn max':>13}")
    print("  " + "-" * 50)
    results = {}
    for threshold in (0.0, 1e-10, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5):
        thresholds = {name: threshold for name in BODIES}
        position = make_position_function(series_by_body, thresholds,
                                          vsop_earth=True)
        measured = measure(position, dates)
        terms = sum(count_terms(series_by_body[n], threshold) for n in BODIES)
        results[threshold] = (measured, terms)
        print(f"  {threshold:>10.0e} {terms:>7}  "
              f"{measured['Jupiter']['max']:>11.2f}\"  "
              f"{measured['Saturn']['max']:>11.2f}\"")
    print()

    target = 60.0
    chosen = None
    for threshold in sorted(results, reverse=True):
        measured, terms = results[threshold]
        if max(measured[n]["max"] for n in measured) <= target:
            chosen = threshold
            break
    if chosen is None:
        print("  No truncation met 1 arcmin; use the full series.")
    else:
        measured, terms = results[chosen]
        print(f"  Coarsest truncation meeting 1 arcmin: {chosen:.0e} au "
              f"({terms} terms across Earth, Jupiter and Saturn)")
        show("  at that threshold:", measured)
    return 0


def main() -> int:
    series_by_body = {name: parse_file(os.path.join(SOURCE_DIR, filename))
                      for name, filename in BODIES.items()}
    return run_benchmark(series_by_body)


if __name__ == "__main__":
    sys.exit(main())
