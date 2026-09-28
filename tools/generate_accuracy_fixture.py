"""
Planetary accuracy fixture generator  —  DEVELOPMENT TOOL
-----------------------------------------------------------
Builds tests/fixtures/planetary_accuracy.json: reference positions from the
Swiss Ephemeris at the dates the V1.2 brief requires, plus the summary
statistics for Jupiter and Saturn.

Case coverage, as specified:
    anchor years           1800, 1850, 1900, 1950, 2000, 2026, 2050
    direct motion          Jupiter and Saturn moving forward
    retrograde motion      both retrograde
    stations               within a day of a station
    opposition periods     planet opposite the Sun
    conjunction periods    planet conjunct the Sun
    sign boundaries        planet crossing a sidereal sign boundary
    deterministic random   seeded, so the fixture is reproducible

The stations, oppositions, conjunctions and sign crossings are FOUND by
searching the reference ephemeris, not hand-picked, so they are genuinely the
configurations they claim to be.

The application never imports swisseph. Run with the dev virtualenv:
    .venv/bin/python tools/generate_accuracy_fixture.py
"""

from __future__ import annotations

import datetime
import json
import os
import random
import statistics
import sys

import swisseph as swe

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from engine import ephemeris as eph                      # noqa: E402

OUT = os.path.join(ROOT, "tests", "fixtures", "planetary_accuracy.json")

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

BODIES = [
    ("Surya", swe.SUN), ("Chandra", swe.MOON), ("Mangal", swe.MARS),
    ("Budha", swe.MERCURY), ("Guru", swe.JUPITER), ("Shukra", swe.VENUS),
    ("Shani", swe.SATURN),
]
BY_NAME = dict(BODIES)

RASHI = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
         "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]

NAKSHATRA = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

START = swe.julday(1800, 1, 1, 0.0)
END = swe.julday(2050, 6, 1, 0.0)


def classify(sidereal: float) -> dict:
    span = 360.0 / 27.0
    nak = int(sidereal / span)
    return {
        "sign_index": int(sidereal // 30) % 12,
        "sign": RASHI[int(sidereal // 30) % 12],
        "degree_in_sign": sidereal % 30,
        "nakshatra": NAKSHATRA[nak],
        "pada": int((sidereal % span) / (span / 4)) + 1,
    }


def longitude(jd: float, body: int) -> float:
    values, _ = swe.calc_ut(jd, body, FLAGS)
    return values[0]


def speed(jd: float, body: int) -> float:
    values, _ = swe.calc_ut(jd, body, FLAGS)
    return values[3]


# ── event finders ────────────────────────────────────────────────────────────

def find_stations(body: int, limit: int) -> list[float]:
    """Dates where the body's speed changes sign."""
    found = []
    jd = START
    previous = speed(jd, body)
    while jd < END and len(found) < limit:
        jd += 3.0
        current = speed(jd, body)
        if (previous < 0) != (current < 0):
            low, high = jd - 3.0, jd
            for _ in range(50):
                mid = (low + high) / 2
                if (speed(low, body) < 0) == (speed(mid, body) < 0):
                    low = mid
                else:
                    high = mid
            found.append(round((low + high) / 2, 6))
        previous = current
    return found


def find_elongations(body: int, target: float, limit: int) -> list[float]:
    """
    Dates where the body's elongation from the Sun equals `target` degrees.
    target 180 is opposition, 0 is conjunction.
    """
    def offset(jd: float) -> float:
        difference = (longitude(jd, body) - longitude(jd, swe.SUN)) % 360.0
        return (difference - target + 180.0) % 360.0 - 180.0

    found = []
    jd = START
    previous = offset(jd)
    while jd < END and len(found) < limit:
        jd += 5.0
        current = offset(jd)
        if abs(current - previous) < 180 and (previous < 0) != (current < 0):
            low, high = jd - 5.0, jd
            for _ in range(50):
                mid = (low + high) / 2
                if (offset(low) < 0) == (offset(mid) < 0):
                    low = mid
                else:
                    high = mid
            found.append(round((low + high) / 2, 6))
        previous = current
    return found


def find_sign_crossings(body: int, limit: int) -> list[float]:
    """Dates where the body crosses a sidereal sign boundary."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    def sidereal(jd: float) -> float:
        return (longitude(jd, body) - swe.get_ayanamsa_ut(jd)) % 360.0

    found = []
    jd = START
    previous = sidereal(jd)
    while jd < END and len(found) < limit:
        jd += 5.0
        current = sidereal(jd)
        if abs(current - previous) < 180 and int(previous / 30) != int(current / 30):
            low, high = jd - 5.0, jd
            boundary = int(max(previous, current) / 30) * 30
            for _ in range(60):
                mid = (low + high) / 2
                if (sidereal(mid) < boundary) == (sidereal(low) < boundary):
                    low = mid
                else:
                    high = mid
            # Sit just off the boundary, not exactly on it.
            found.append(round((low + high) / 2 + 0.05, 6))
        previous = current
    return found


def find_direct_dates(body: int, limit: int) -> list[float]:
    """Dates where the body is clearly moving direct."""
    found = []
    jd = START + 1234.0
    while jd < END and len(found) < limit:
        if speed(jd, body) > 0.02:
            found.append(round(jd, 6))
            jd += 3000.0
        else:
            jd += 200.0
    return found


def find_retrograde_dates(body: int, limit: int) -> list[float]:
    found = []
    jd = START + 500.0
    while jd < END and len(found) < limit:
        if speed(jd, body) < -0.01:
            found.append(round(jd, 6))
            jd += 3000.0
        else:
            jd += 30.0
    return found


# ── case assembly ────────────────────────────────────────────────────────────

def build_case(label: str, kind: str, jd_ut: float, why: str) -> dict:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd_ut)

    bodies = {}
    for name, code in BODIES:
        values, _ = swe.calc_ut(jd_ut, code, FLAGS)
        sidereal = (values[0] - ayanamsha) % 360.0
        entry = {
            "tropical": values[0],
            "sidereal": sidereal,
            "speed": values[3],
            "retrograde": values[3] < 0,
        }
        entry.update(classify(sidereal))
        bodies[name] = entry

    year, month, day, hour = swe.revjul(jd_ut)
    when = (datetime.datetime(year, month, day)
            + datetime.timedelta(hours=hour))

    return {
        "label": label,
        "kind": kind,
        "why": why,
        "jd_ut": jd_ut,
        "utc": when.isoformat(timespec="seconds"),
        "ayanamsha_lahiri": ayanamsha,
        "bodies": bodies,
    }


def collect_cases() -> list[dict]:
    cases: list[dict] = []

    # Anchor years named in the brief.
    for year in (1800, 1850, 1900, 1950, 2000, 2026, 2050):
        cases.append(build_case(
            f"anchor_{year}", "anchor_year",
            swe.julday(year, 3, 15, 12.0),
            "Anchor year required by the V1.2 accuracy brief"))

    # Configuration-driven cases, found by searching the reference.
    for name, code in (("jupiter", swe.JUPITER), ("saturn", swe.SATURN)):
        for jd in find_direct_dates(code, 3):
            cases.append(build_case(f"{name}_direct_{jd:.0f}", "direct", jd,
                                    f"{name} in clear direct motion"))
        for jd in find_retrograde_dates(code, 3):
            cases.append(build_case(f"{name}_retro_{jd:.0f}", "retrograde", jd,
                                    f"{name} retrograde"))
        for jd in find_stations(code, 3):
            cases.append(build_case(f"{name}_station_{jd:.0f}", "station", jd,
                                    f"{name} within hours of a station"))
        for jd in find_elongations(code, 180.0, 2):
            cases.append(build_case(f"{name}_opposition_{jd:.0f}",
                                    "opposition", jd,
                                    f"{name} at opposition to the Sun"))
        for jd in find_elongations(code, 0.0, 2):
            cases.append(build_case(f"{name}_conjunction_{jd:.0f}",
                                    "conjunction", jd,
                                    f"{name} in conjunction with the Sun"))
        for jd in find_sign_crossings(code, 3):
            cases.append(build_case(f"{name}_signchange_{jd:.0f}",
                                    "sign_boundary", jd,
                                    f"{name} just past a sidereal sign boundary"))

    # Deterministic random dates: seeded so the fixture is reproducible.
    generator = random.Random(20260927)
    for index in range(12):
        jd = round(generator.uniform(START, END), 6)
        cases.append(build_case(f"random_{index:02d}", "deterministic_random",
                                jd, "Seeded random date (seed 20260927)"))

    cases.sort(key=lambda case: case["jd_ut"])
    return cases


def measure_statistics(cases: list[dict]) -> dict:
    """
    Error statistics for Jupiter and Saturn, current theory against the old.

    The Keplerian figure is computed by calling the retained
    `keplerian_xyz` path, so the before/after comparison is made by the same
    code on the same dates rather than quoted from an earlier run.
    """
    import math

    def arcsec(a: float, b: float) -> float:
        return abs((a - b + 180.0) % 360.0 - 180.0) * 3600.0

    def keplerian_longitude(body: str, jd_tt: float) -> float:
        """The pre-V1.2 pipeline: Keplerian elements for everything."""
        ex, ey, ez = eph.keplerian_xyz("Earth", jd_tt)
        px, py, pz = eph.keplerian_xyz(body, jd_tt)
        for _ in range(3):
            dx, dy, dz = px - ex, py - ey, pz - ez
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)
            px, py, pz = eph.keplerian_xyz(body, jd_tt - distance * 0.005775518331)
        dx, dy, dz = px - ex, py - ey, pz - ez
        lon = math.degrees(math.atan2(dy, dx)) % 360.0
        lat = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
        lon = (lon + eph.precession_in_longitude(jd_tt)) % 360.0
        sun_lon = eph.sun_true_longitude(jd_tt)
        lon += (-(20.49552 / 3600.0) * math.cos(math.radians(sun_lon - lon))
                / math.cos(math.radians(lat)))
        d_psi, _ = eph.nutation(jd_tt)
        return (lon + d_psi) % 360.0

    stats = {}
    for body, english in (("Guru", "Jupiter"), ("Shani", "Saturn")):
        current, previous = [], []
        for case in cases:
            jd_tt = eph.jd_ut_to_tt(case["jd_ut"])
            expected = case["bodies"][body]["tropical"]
            current.append(arcsec(eph.tropical_longitude(body, jd_tt), expected))
            previous.append(arcsec(keplerian_longitude(english, jd_tt), expected))
        ordered = sorted(current)
        stats[body] = {
            "english": english,
            "theory": eph.theory_used(body),
            "samples": len(ordered),
            "max_arcsec": round(ordered[-1], 3),
            "mean_arcsec": round(statistics.fmean(ordered), 3),
            "median_arcsec": round(statistics.median(ordered), 3),
            "p95_arcsec": round(
                ordered[min(int(0.95 * len(ordered)), len(ordered) - 1)], 3),
            "max_arcmin": round(ordered[-1] / 60.0, 4),
            "keplerian_max_arcsec": round(max(previous), 3),
            "keplerian_mean_arcsec": round(statistics.fmean(previous), 3),
            "keplerian_median_arcsec": round(statistics.median(previous), 3),
            "keplerian_max_arcmin": round(max(previous) / 60.0, 4),
            "improvement_factor": round(max(previous) / ordered[-1], 1),
        }
    return stats


def main() -> int:
    print("building cases ...")
    cases = collect_cases()
    print(f"  {len(cases)} cases")
    print("measuring ...")
    stats = measure_statistics(cases)

    data = {
        "generator": {
            "tool": "tools/generate_accuracy_fixture.py",
            "reference": "Swiss Ephemeris (pyswisseph) SEFLG_MOSEPH",
            "swisseph_version": swe.version,
            "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "note": (
                "Independent of the theories the application implements "
                "(VSOP87A for Earth/Jupiter/Saturn, JPL Keplerian elements for "
                "Mercury/Venus/Mars, Meeus for the luminaries). The "
                "application never imports swisseph. Note that Moshier itself "
                "differs from the JPL DE series by of order an arcsecond for "
                "the outer planets, so residuals at that level are at the "
                "reference's own resolution."),
            "random_seed": 20260927,
        },
        "statistics": stats,
        "cases": cases,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, sort_keys=True)

    print(f"\nwrote {OUT}")
    print(f"\n  {'body':<9}{'theory':<12}{'max':>10}{'mean':>10}"
          f"{'median':>10}{'p95':>10}   was (Keplerian)")
    print("  " + "-" * 76)
    for body, entry in stats.items():
        print(f"  {entry['english']:<9}{'VSOP87A':<12}"
              f"{entry['max_arcsec']:>9.2f}\"{entry['mean_arcsec']:>9.2f}\""
              f"{entry['median_arcsec']:>9.2f}\"{entry['p95_arcsec']:>9.2f}\""
              f"   {entry['keplerian_max_arcsec']:>8.1f}\" "
              f"({entry['improvement_factor']}x better)")
    from collections import Counter
    print("\n  case kinds: " + ", ".join(
        f"{kind} {count}" for kind, count
        in sorted(Counter(c["kind"] for c in cases).items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
