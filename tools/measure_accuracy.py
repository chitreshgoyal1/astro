"""
Accuracy measurement  —  DEVELOPMENT TOOL, NOT PART OF THE APPLICATION
----------------------------------------------------------------------
Measures the application's error against the Swiss Ephemeris over a dense grid
of dates, and reports the distribution per body. This is what the accuracy
claims in DOCUMENTATION.md and AUDIT.md are based on: nothing is asserted that
is not measured here.

The application itself never imports swisseph.

Run with the dev virtualenv:
    .venv/bin/python tools/measure_accuracy.py
"""

# Phase 2 (V1.1) audit tooling.

from __future__ import annotations

import json
import os
import statistics
import sys

import swisseph as swe

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from engine import ephemeris as eph  # noqa: E402

OUT = os.path.join(ROOT, "tests", "fixtures", "accuracy_profile.json")

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

BODIES = [
    ("Surya", swe.SUN), ("Chandra", swe.MOON), ("Mangal", swe.MARS),
    ("Budha", swe.MERCURY), ("Guru", swe.JUPITER), ("Shukra", swe.VENUS),
    ("Shani", swe.SATURN),
]

NODES = [("Rahu_true", swe.TRUE_NODE), ("Rahu_mean", swe.MEAN_NODE)]

AYANAMSHAS = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "fagan_bradley": swe.SIDM_FAGAN_BRADLEY,
}

# Sample sites for the Ascendant sweep.
SITES = [
    ("Jaipur", 26.9124, 75.7873),
    ("Sydney", -33.8688, 151.2093),
    ("Reykjavik", 64.1466, -21.9426),
    ("Singapore", 1.3521, 103.8198),
    ("New York", 40.7128, -74.0060),
]

START_JD = swe.julday(1800, 1, 1, 0.0)
END_JD = swe.julday(2050, 1, 1, 0.0)
STEP_DAYS = 91.3125          # ~2740 samples across 250 years


def arcsec(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0) * 3600.0


def summarise(errors: list[float]) -> dict:
    ordered = sorted(errors)
    def pct(p: float) -> float:
        return ordered[min(int(p / 100 * len(ordered)), len(ordered) - 1)]
    return {
        "samples": len(ordered),
        "median_arcsec": round(statistics.median(ordered), 2),
        "p95_arcsec": round(pct(95), 2),
        "p99_arcsec": round(pct(99), 2),
        "max_arcsec": round(ordered[-1], 2),
        "max_arcmin": round(ordered[-1] / 60.0, 2),
    }


def sweep_longitudes() -> dict:
    """Tropical longitude error per body across 1800-2050."""
    errors: dict[str, list[float]] = {name: [] for name, _ in BODIES}
    errors["Rahu_true"] = []
    errors["Rahu_mean"] = []

    jd = START_JD
    while jd < END_JD:
        jd_tt_app = eph.jd_ut_to_tt(jd)
        for name, planet in BODIES:
            values, _ = swe.calc_ut(jd, planet, FLAGS)
            errors[name].append(arcsec(eph.tropical_longitude(name, jd_tt_app), values[0]))
        values, _ = swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)
        errors["Rahu_true"].append(
            arcsec(eph.lunar_node(jd_tt_app, True), values[0]))
        values, _ = swe.calc_ut(jd, swe.MEAN_NODE, FLAGS)
        errors["Rahu_mean"].append(
            arcsec(eph.lunar_node(jd_tt_app, False), values[0]))
        jd += STEP_DAYS

    return {name: summarise(vals) for name, vals in errors.items()}


def sweep_ayanamsha() -> dict:
    """Ayanamsha error per system across 1800-2050."""
    errors: dict[str, list[float]] = {name: [] for name in AYANAMSHAS}
    jd = START_JD
    while jd < END_JD:
        jd_tt_app = eph.jd_ut_to_tt(jd)
        for name, mode in AYANAMSHAS.items():
            swe.set_sid_mode(mode)
            errors[name].append(
                abs(eph.ayanamsha(jd_tt_app, name) - swe.get_ayanamsa_ut(jd)) * 3600.0)
        jd += STEP_DAYS
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return {name: summarise(vals) for name, vals in errors.items()}


def sweep_ascendant() -> dict:
    """Ascendant and MC error across sites and times of day."""
    asc_errors: list[float] = []
    mc_errors: list[float] = []
    per_site: dict[str, list[float]] = {name: [] for name, _, _ in SITES}

    jd = START_JD
    while jd < END_JD:
        for hour_offset in (0.0, 0.31, 0.57, 0.83):
            jd_sample = jd + hour_offset
            jd_tt_app = eph.jd_ut_to_tt(jd_sample)
            for name, lat, lon in SITES:
                _, ascmc = swe.houses_ex(jd_sample, lat, lon, b"W")
                err = arcsec(eph.ascendant(jd_sample, jd_tt_app, lat, lon), ascmc[0])
                asc_errors.append(err)
                per_site[name].append(err)
                mc_errors.append(
                    arcsec(eph.midheaven(jd_sample, jd_tt_app, lon), ascmc[1]))
        jd += STEP_DAYS

    return {
        "ascendant_all_sites": summarise(asc_errors),
        "midheaven_all_sites": summarise(mc_errors),
        "ascendant_per_site": {n: summarise(v) for n, v in per_site.items()},
    }


def sweep_delta_t() -> dict:
    """Delta T error in seconds against Swiss Ephemeris."""
    errors = []
    jd = START_JD
    while jd < END_JD:
        errors.append(abs(eph.delta_t_seconds(jd) - swe.deltat(jd) * 86400.0))
        jd += STEP_DAYS
    ordered = sorted(errors)
    return {
        "samples": len(ordered),
        "median_seconds": round(statistics.median(ordered), 3),
        "max_seconds": round(ordered[-1], 3),
    }


def sweep_speed_and_retrograde() -> dict:
    """How often the retrograde flag and the speed disagree with the reference."""
    wrong_flag: dict[str, int] = {name: 0 for name, _ in BODIES}
    total: dict[str, int] = {name: 0 for name, _ in BODIES}
    speed_error: dict[str, list[float]] = {name: [] for name, _ in BODIES}
    # Daily sampling over 30 years catches every station.
    jd = swe.julday(1990, 1, 1, 0.0)
    end = swe.julday(2020, 1, 1, 0.0)
    while jd < end:
        jd_tt_app = eph.jd_ut_to_tt(jd)
        for name, planet in BODIES:
            values, _ = swe.calc_ut(jd, planet, FLAGS)
            got = eph.daily_motion(name, jd_tt_app)
            total[name] += 1
            if (got < 0) != (values[3] < 0):
                wrong_flag[name] += 1
            speed_error[name].append(abs(got - values[3]))
        jd += 1.0
    return {
        name: {
            "samples": total[name],
            "retrograde_flag_mismatches": wrong_flag[name],
            "mismatch_rate_pct": round(100.0 * wrong_flag[name] / total[name], 4),
            "max_speed_error_deg_per_day": round(max(speed_error[name]), 5),
            "median_speed_error_deg_per_day": round(
                statistics.median(speed_error[name]), 6),
        }
        for name, _ in BODIES
    }


def main() -> int:
    print("measuring longitudes 1800-2050 ...")
    longitudes = sweep_longitudes()
    print("measuring ayanamsha ...")
    ayan = sweep_ayanamsha()
    print("measuring ascendant ...")
    asc = sweep_ascendant()
    print("measuring delta T ...")
    dt = sweep_delta_t()
    print("measuring speed / retrogression (daily, 1990-2020) ...")
    speed = sweep_speed_and_retrograde()

    data = {
        "generator": {
            "tool": "tools/measure_accuracy.py",
            "reference": "Swiss Ephemeris (pyswisseph) SEFLG_MOSEPH",
            "swisseph_version": swe.version,
            "span": "1800-01-01 to 2050-01-01",
            "step_days": STEP_DAYS,
        },
        "tropical_longitude": longitudes,
        "ayanamsha": ayan,
        "angles": asc,
        "delta_t": dt,
        "speed_and_retrogression": speed,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)

    print(f"\nwrote {OUT}\n")
    print(f"  {'body':<12} {'median':>10} {'p95':>10} {'p99':>10} {'max':>10} {'max arcmin':>12}")
    print("  " + "-" * 68)
    for name, s in longitudes.items():
        print(f"  {name:<12} {s['median_arcsec']:>9.1f}\" {s['p95_arcsec']:>9.1f}\" "
              f"{s['p99_arcsec']:>9.1f}\" {s['max_arcsec']:>9.1f}\" {s['max_arcmin']:>11.2f}'")
    print("\n  ayanamsha (arcsec):")
    for name, s in ayan.items():
        print(f"    {name:<16} median {s['median_arcsec']:>7.2f}\"  max {s['max_arcsec']:>7.2f}\"")
    print(f"\n  ascendant  max {asc['ascendant_all_sites']['max_arcsec']:.1f}\"")
    print(f"  midheaven  max {asc['midheaven_all_sites']['max_arcsec']:.1f}\"")
    print(f"  delta T    max {dt['max_seconds']:.2f}s")
    print("\n  retrograde flag:")
    for name, s in speed.items():
        print(f"    {name:<10} {s['retrograde_flag_mismatches']:>5} / {s['samples']} "
              f"({s['mismatch_rate_pct']}%)  max speed err "
              f"{s['max_speed_error_deg_per_day']}°/day")
    return 0


if __name__ == "__main__":
    sys.exit(main())
