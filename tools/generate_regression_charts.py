"""
Regression chart fixture generator  —  DEVELOPMENT TOOL
---------------------------------------------------------
Builds tests/fixtures/regression_charts.json: the ASTRONOMICAL reference
values for several unrelated natal charts, taken from the Swiss Ephemeris.

Part 14 of the V1.2 brief requires the astronomical expectations to be stored
SEPARATELY from the astrological-rule expectations, and this is that
separation made physical: this file contains only positions, and the
rule-level expectations live in the test module as code. A change in a yoga
rule cannot silently rewrite an ephemeris expectation, and vice versa.

The charts deliberately span different centuries, hemispheres, latitudes and
planetary configurations, so that no formula can be tuned to suit one of them
without breaking the others.

Run with the dev virtualenv:
    .venv/bin/python tools/generate_regression_charts.py
"""

from __future__ import annotations

import datetime
import json
import os
import sys

import swisseph as swe

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "tests", "fixtures", "regression_charts.json")

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

BODIES = [
    ("Surya", swe.SUN), ("Chandra", swe.MOON), ("Mangal", swe.MARS),
    ("Budha", swe.MERCURY), ("Guru", swe.JUPITER), ("Shukra", swe.VENUS),
    ("Shani", swe.SATURN),
]

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

# id, local datetime, utc datetime, lat, lon, tz offset, why this chart exists
CHARTS = [
    ("jaipur_1988",
     (1988, 8, 30, 20, 18), (1988, 8, 30, 14, 48), 26.9124, 75.7873, 5.5,
     "The documented V1 worked example, kept as the continuing regression case"),
    ("london_1901",
     (1901, 1, 22, 6, 30), (1901, 1, 22, 6, 30), 51.5074, -0.1278, 0.0,
     "Early 20th century, northern latitude, zero meridian"),
    ("sydney_1962",
     (1962, 11, 7, 3, 45), (1962, 11, 6, 16, 45), -33.8688, 151.2093, 11.0,
     "Southern hemisphere, eastern longitude, night birth"),
    ("newyork_1975",
     (1975, 6, 14, 12, 0), (1975, 6, 14, 16, 0), 40.7128, -74.0060, -4.0,
     "Western longitude, noon birth, Mercury retrograde period"),
    ("reykjavik_2001",
     (2001, 12, 21, 11, 15), (2001, 12, 21, 11, 15), 64.1466, -21.9426, 0.0,
     "High latitude near the solstice, where the Ascendant moves unevenly"),
    ("singapore_2019",
     (2019, 4, 3, 9, 5), (2019, 4, 3, 1, 5), 1.3521, 103.8198, 8.0,
     "Equatorial latitude, recent date, Saturn and Jupiter both direct"),
    ("delhi_1947",
     (1947, 8, 15, 0, 0), (1947, 8, 14, 18, 30), 28.6139, 77.2090, 5.5,
     "Midnight birth, historically significant date, Indian Standard Time"),
    ("santiago_2033",
     (2033, 3, 9, 18, 40), (2033, 3, 9, 21, 40), -33.4489, -70.6693, -3.0,
     "Future date, southern and western, beyond the observed delta-T record"),
]


def classify(sidereal: float) -> dict:
    span = 360.0 / 27.0
    nak = int(sidereal / span)
    return {
        "sign": RASHI[int(sidereal // 30) % 12],
        "sign_index": int(sidereal // 30) % 12,
        "degree_in_sign": sidereal % 30,
        "nakshatra": NAKSHATRA[nak],
        "nakshatra_index": nak,
        "pada": int((sidereal % span) / (span / 4)) + 1,
    }


def build(chart_id, local, utc, lat, lon, offset, why) -> dict:
    jd_ut = swe.julday(utc[0], utc[1], utc[2], utc[3] + utc[4] / 60.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd_ut)

    bodies = {}
    for name, code in BODIES:
        values, _ = swe.calc_ut(jd_ut, code, FLAGS)
        sidereal = (values[0] - ayanamsha) % 360.0
        entry = {"tropical": values[0], "sidereal": sidereal,
                 "speed": values[3], "retrograde": values[3] < 0}
        entry.update(classify(sidereal))
        bodies[name] = entry

    values, _ = swe.calc_ut(jd_ut, swe.TRUE_NODE, FLAGS)
    rahu = (values[0] - ayanamsha) % 360.0
    bodies["Rahu"] = {"tropical": values[0], "sidereal": rahu,
                      "speed": values[3], "retrograde": values[3] < 0}
    bodies["Rahu"].update(classify(rahu))
    ketu = (rahu + 180.0) % 360.0
    bodies["Ketu"] = {"tropical": (values[0] + 180.0) % 360.0,
                      "sidereal": ketu, "speed": values[3],
                      "retrograde": values[3] < 0}
    bodies["Ketu"].update(classify(ketu))

    _cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W")
    lagna = {"tropical": ascmc[0], "sidereal": (ascmc[0] - ayanamsha) % 360.0}
    lagna.update(classify(lagna["sidereal"]))

    return {
        "id": chart_id,
        "why": why,
        "birth_local": datetime.datetime(*local).isoformat(),
        "birth_utc": datetime.datetime(*utc).isoformat(),
        "utc_offset_hours": offset,
        "latitude": lat,
        "longitude": lon,
        "jd_ut": jd_ut,
        "ayanamsha_lahiri": ayanamsha,
        "delta_t_seconds": swe.deltat(jd_ut) * 86400.0,
        "lagna": lagna,
        "bodies": bodies,
    }


def main() -> int:
    data = {
        "generator": {
            "tool": "tools/generate_regression_charts.py",
            "reference": "Swiss Ephemeris (pyswisseph) SEFLG_MOSEPH",
            "swisseph_version": swe.version,
            "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "contains": (
                "ASTRONOMICAL reference values only. Astrological rule "
                "expectations are held separately, in "
                "tests/test_regression_charts.py, so that a change to a yoga "
                "rule cannot rewrite an ephemeris expectation."),
        },
        "charts": [build(*chart) for chart in CHARTS],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, sort_keys=True)
    print(f"wrote {OUT}")
    for chart in data["charts"]:
        print(f"  {chart['id']:<18}{chart['birth_local'][:16]}  "
              f"lat {chart['latitude']:>8.3f}  "
              f"Lagna {chart['lagna']['sign']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
