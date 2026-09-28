"""
Mars migration regression report  —  DEVELOPMENT TOOL (V1.3 Part 19)
----------------------------------------------------------------------
Answers one question: did moving Mars from the JPL Keplerian elements to
VSOP87A change any ASTROLOGICAL classification, and if so, why?

An astronomy upgrade must not quietly alter astrology. A longitude shift of a
few arcminutes matters only where it crosses a boundary — a rashi, nakshatra,
pada or varga edge. This tool finds every such crossing across the regression
charts and the accuracy fixture, so that any fixture change can be justified
by a stated astronomical reason rather than edited until the tests go green.

Run:
    .venv/bin/python tools/mars_migration_report.py
"""

from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from engine import ephemeris as eph                              # noqa: E402
from engine.planets import RASHI_NAMES, get_nakshatra            # noqa: E402
from engine.vargas import VARGA_ORDER, VargaConfig               # noqa: E402

_LIGHT_TIME_PER_AU = 0.005775518331
_ABERRATION = 20.49552 / 3600.0


def keplerian_apparent_longitude(body: str, jd_tt: float) -> float:
    """
    The pre-V1.3 Mars pipeline: Keplerian elements for Mars, VSOP for Earth.

    Reconstructed here rather than quoted from an old run, so the comparison
    is made by the same code on the same dates.
    """
    ex, ey, ez = eph.heliocentric_xyz("Earth", jd_tt)
    px, py, pz = eph.keplerian_xyz(body, jd_tt)
    for _ in range(3):
        dx, dy, dz = px - ex, py - ey, pz - ez
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        px, py, pz = eph.keplerian_xyz(body, jd_tt - distance * _LIGHT_TIME_PER_AU)
    dx, dy, dz = px - ex, py - ey, pz - ez
    lon = math.degrees(math.atan2(dy, dx)) % 360.0
    lat = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
    lon = (lon + eph.precession_in_longitude(jd_tt)) % 360.0
    sun_lon = eph.sun_true_longitude(jd_tt)
    lon += (-_ABERRATION * math.cos(math.radians(sun_lon - lon))
            / math.cos(math.radians(lat)))
    d_psi, _ = eph.nutation(jd_tt)
    return (lon + d_psi) % 360.0


def classify(sidereal: float, config: VargaConfig) -> dict:
    nak_index, nak_name, _lord, pada = get_nakshatra(sidereal)
    result = {
        "rashi": RASHI_NAMES[int(sidereal // 30) % 12],
        "nakshatra": nak_name,
        "pada": pada,
    }
    for key in VARGA_ORDER:
        result[key] = config.compute(key, sidereal).rashi
    return result


def compare_case(label: str, jd_ut: float, config: VargaConfig) -> dict:
    jd_tt = eph.jd_ut_to_tt(jd_ut)
    ayanamsha = eph.ayanamsha(jd_tt, "lahiri")
    before = (keplerian_apparent_longitude("Mars", jd_tt) - ayanamsha) % 360.0
    after = (eph.tropical_longitude("Mangal", jd_tt) - ayanamsha) % 360.0

    old = classify(before, config)
    new = classify(after, config)
    changed = {k: (old[k], new[k]) for k in old if old[k] != new[k]}
    shift = abs((after - before + 180.0) % 360.0 - 180.0)
    return {
        "label": label,
        "jd_ut": jd_ut,
        "before": before,
        "after": after,
        "shift_arcmin": shift * 60.0,
        "changed": changed,
    }


def load_cases() -> list[tuple[str, float]]:
    cases: list[tuple[str, float]] = []
    fixtures = os.path.join(ROOT, "tests", "fixtures")

    path = os.path.join(fixtures, "regression_charts.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            for chart in json.load(handle)["charts"]:
                cases.append((f"chart:{chart['id']}", chart["jd_ut"]))

    path = os.path.join(fixtures, "planetary_accuracy.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            for case in json.load(handle)["cases"]:
                cases.append((f"accuracy:{case['label']}", case["jd_ut"]))

    path = os.path.join(fixtures, "reference_positions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
            for case in data.get("cases", []):
                cases.append((f"reference:{case['label']}", case["jd_ut"]))
    return cases


def main() -> int:
    config = VargaConfig()
    cases = load_cases()
    results = [compare_case(label, jd, config) for label, jd in cases]

    shifts = sorted(r["shift_arcmin"] for r in results)
    changed = [r for r in results if r["changed"]]

    print("MARS MIGRATION REGRESSION  (Keplerian elements -> VSOP87A)")
    print("=" * 74)
    print(f"  fixture cases examined : {len(results)}")
    print(f"  longitude shift        : median {shifts[len(shifts) // 2]:.3f}' "
          f"max {shifts[-1]:.3f}'")
    print(f"  classifications changed: {len(changed)}")
    print()

    if not changed:
        print("  No rashi, nakshatra, pada or varga classification changed in")
        print("  any fixture case. The longitude moved, but never across a")
        print("  boundary, so no expected astrological value needs revising.")
    else:
        print("  CHANGED CLASSIFICATIONS — each needs a documented reason")
        print("  " + "-" * 70)
        for entry in changed:
            print(f"\n  {entry['label']}")
            print(f"    Mars {entry['before']:.6f}° -> {entry['after']:.6f}°  "
                  f"(shift {entry['shift_arcmin']:.3f}')")
            for field, (old, new) in entry["changed"].items():
                print(f"      {field:<6} {old} -> {new}")

    # A broader sweep, to say how often this can happen at all.
    print()
    print("  How often could this bite? Sweeping 1800-2050 at 7-day steps:")
    jd = 2378496.5
    total = crossings = 0
    worst = 0.0
    while jd < 2469807.5:
        jd_tt = eph.jd_ut_to_tt(jd)
        ayanamsha = eph.ayanamsha(jd_tt, "lahiri")
        before = (keplerian_apparent_longitude("Mars", jd_tt) - ayanamsha) % 360.0
        after = (eph.tropical_longitude("Mangal", jd_tt) - ayanamsha) % 360.0
        total += 1
        worst = max(worst, abs((after - before + 180.0) % 360.0 - 180.0) * 60.0)
        if int(before // 30) != int(after // 30):
            crossings += 1
        jd += 7.0
    print(f"    {crossings} of {total} samples changed RASHI "
          f"({100.0 * crossings / total:.3f}%)")
    print(f"    worst longitude shift over the span: {worst:.2f}'")
    print()
    print("  Interpretation: a shift only matters within its own size of a")
    print("  boundary, so the rate above is roughly (shift / 30 degrees).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
