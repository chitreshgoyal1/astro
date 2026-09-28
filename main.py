"""
Jyotish Calculator — Main Entry Point
--------------------------------------
Input: Name, Date of Birth, exact Time, Place, and (optionally) the planetary
       degrees for Lagna + 9 grahas. Entered degrees are authoritative.
Output: Chart, entered-vs-calculated comparison, 16 Vargas, Fal report

Usage:
    python main.py
    python main.py --name "Ram Sharma" --dob 1990-06-15 --time 06:30 --place Delhi
    python main.py --consultation sample_consultation.json
    python main.py --consultation sample_consultation.json --varga-config varga_config.json
    python main.py --list-conventions
"""

import sys
import io
import contextlib
import datetime
import argparse
import os

from typing import Optional

# Add engine to path
sys.path.insert(0, ".")

from engine.planets import (
    JyotishChart, jde_from_datetime, available_ayanamshas, PLANET_NAMES, RASHI_NAMES
)
from engine.vargas import (
    VargaConfig, VargaConfigError, VARGA_ORDER, VARGA_SPECS, available_conventions
)
from engine.input_model import (
    LAGNA_KEY, ConsultationInput, InputError,
    load_consultation_file, prompt_positions
)
from engine.compare import DEFAULT_TOLERANCE_DEG, compare, format_comparison
from engine.ephemeris import selftest
from engine.report import Tee, text_to_pdf
from engine.fal import generate_fal_report, detect_yogas
from engine.snapshot import build_snapshot
from engine.timing import (
    YEAR_LENGTHS, DEFAULT_YEAR_LENGTH, format_dasha_report,
    from_chart as dasha_from_chart,
)
from engine.strength import compute_shadbala, format_shadbala_report
from engine.ashtakavarga import compute_ashtakavarga, format_ashtakavarga_report
from engine.houses import HOUSE_PROFILES, build_bhava_chart, format_bhava_report
from engine.sensitivity import analyse_birth_time, format_sensitivity_report
from engine.location import LocationError, known_cities, resolve_location
from engine.features import build_chart_features, parashari_profile
from engine.features.report import format_feature_report
from engine.rules import DEFAULT_PROFILE, RULE_PROFILES, evaluate_rules
from engine.rules.report import format_yoga_report
from engine.synthesis import (
    SynthesisProfile, build_prediction_snapshot, build_reliability,
    event_candidates, format_synthesis_report, synthesise,
)
from engine.transits.calculator import get_transit_snapshot
from engine.transits.query import get_transit_events_between
from engine.interpretation import (
    ReportMode, available_languages, build_interpretation,
    format_interpretation,
)


def parse_args_from(argv=None) -> argparse.Namespace:
    """Command-line interface for the consultation form."""
    parser = argparse.ArgumentParser(description="Jyotish Calculator")
    parser.add_argument("--name",  help="Name of person")
    parser.add_argument("--dob",   help="Date of birth YYYY-MM-DD")
    parser.add_argument("--time",  help="Exact time of birth HH:MM (24hr)")
    parser.add_argument("--place", help="Place of birth")
    parser.add_argument("--lat", help="Birth latitude, e.g. 26.9124 or \"26 54 45 N\"")
    parser.add_argument("--lon", help="Birth longitude, e.g. 75.7873 or \"75 47 14 E\"")
    parser.add_argument("--timezone", metavar="IANA",
                        help="IANA time zone of the birth place, e.g. Asia/Kolkata")
    parser.add_argument("--utc-offset", metavar="OFFSET",
                        help="Fixed UTC offset at birth, e.g. +05:30 "
                             "(use when the zone name is unknown)")
    parser.add_argument("--list-cities", action="store_true",
                        help="List the built-in birth places and exit")
    parser.add_argument("--consultation", metavar="FILE",
                        help="JSON consultation form incl. entered degrees")
    parser.add_argument("--enter-degrees", action="store_true",
                        help="Prompt for Lagna + 9 graha degrees")
    parser.add_argument("--varga-config", metavar="FILE",
                        help="JSON file selecting the convention for each Varga")
    parser.add_argument("--ayanamsha", default=None,
                        help="Ayanamsha: " + ", ".join(available_ayanamshas()))
    parser.add_argument("--node", choices=["true", "mean"], default="true",
                        help="Rahu/Ketu computed from the true or mean lunar node")
    parser.add_argument("--rule-profile", default=DEFAULT_PROFILE,
                        choices=sorted(RULE_PROFILES),
                        help="Named Yoga rule profile (tradition) to evaluate")
    parser.add_argument("--node-aspects", choices=["none", "parashari_like", "kendra"],
                        default="none",
                        help="Aspect convention for Rahu/Ketu; traditions differ, "
                             "so the default asserts nothing")
    parser.add_argument("--no-features", action="store_true",
                        help="Skip the ASTROLOGY FEATURES and YOGA ANALYSIS sections")
    parser.add_argument("--show-absent-yogas", action="store_true",
                        help="List every combination that did not form, with "
                             "the clause that failed")
    parser.add_argument("--legacy-fal", action="store_true",
                        help="Also print the superseded V1 interpretation "
                             "report (old yoga rules and dasha). Off by "
                             "default: it contradicts the rule engine.")
    parser.add_argument("--no-dasha", action="store_true",
                        help="Skip the Vimshottari dasha section")
    parser.add_argument("--dasha-depth", type=int, default=3,
                        choices=[1, 2, 3, 4, 5],
                        help="1 mahadasha, 2 +antardasha, 3 +pratyantardasha, "
                             "4 +sukshma, 5 +prana (default 3)")
    parser.add_argument("--dasha-year", default=DEFAULT_YEAR_LENGTH.name,
                        choices=sorted(YEAR_LENGTHS),
                        help="Year-length convention for dasha dates "
                             f"(default {DEFAULT_YEAR_LENGTH.name})")
    parser.add_argument("--all-antardashas", action="store_true",
                        help="Print antardashas for every mahadasha, not only "
                             "the current one")
    parser.add_argument("--json-output", metavar="FILE",
                        help="Write the canonical ChartSnapshot JSON to FILE")
    parser.add_argument("--json-compact", action="store_true",
                        help="Write the snapshot without indentation")
    parser.add_argument("--house-system", default="whole_sign",
                        choices=sorted(HOUSE_PROFILES),
                        help="House system for the Bhava chart. The Rashi "
                             "chart is always computed and rules always run "
                             "in Rashi space.")
    parser.add_argument("--no-strength", action="store_true",
                        help="Skip the PLANETARY STRENGTH (Shadbala) section")
    parser.add_argument("--no-ashtakavarga", action="store_true",
                        help="Skip the ASHTAKAVARGA section")
    parser.add_argument("--ashtakavarga-reductions", action="store_true",
                        help="Apply Trikona and Ekadhipatya sodhana. These "
                             "are UNVERIFIED against any witness.")
    parser.add_argument("--birth-time-sensitivity", action="store_true",
                        help="Report which classifications change near the "
                             "stated birth time (not rectification)")
    parser.add_argument("--shadbala-detail", action="store_true",
                        help="Show every Shadbala subcomponent")
    # ── V1.5 synthesis (Part 26) ─────────────────────────────────────────────
    # Off unless asked for. Normal natal output must not start producing
    # predictions because a release added the capability.
    parser.add_argument("--synthesis", metavar="DATE", default=None,
                        help="Run deterministic synthesis for a date "
                             "(YYYY-MM-DD or YYYY-MM-DDTHH:MM). Not produced "
                             "unless this flag is given.")
    parser.add_argument("--synthesis-profile",
                        choices=[p.value for p in SynthesisProfile],
                        default=SynthesisProfile.STANDARD.value,
                        help="Which evidence the synthesis may use "
                             "(default: standard)")
    parser.add_argument("--domain", action="append", default=None,
                        metavar="NAME",
                        help="Restrict synthesis output to a domain, e.g. "
                             "--domain career. Repeatable.")
    parser.add_argument("--prediction-json", metavar="FILE", default=None,
                        help="Write the PredictionSnapshot to FILE")
    parser.add_argument("--synthesis-evidence", action="store_true",
                        help="Show every contributing factor in the "
                             "synthesis report")
    parser.add_argument("--birth-time-precision", type=int, default=None,
                        metavar="SECONDS",
                        help="How precisely the birth time is actually known "
                             "(default 60, matching an HH:MM entry). Used to "
                             "gate varga evidence; never used to adjust the "
                             "chart.")
    # ── V1.6 interpretation (Part 27) ────────────────────────────────────────
    # `--interpret` implies `--synthesis` for the same date: an interpretation
    # is a rendering of a synthesis, and asking for one without the other is
    # always a mistake rather than a preference.
    parser.add_argument("--interpret", metavar="DATE", default=None,
                        help="Render a deterministic interpretation for a "
                             "date. Implies --synthesis for that date. No "
                             "model, no network.")
    parser.add_argument("--interpret-profile",
                        choices=[p.value for p in SynthesisProfile],
                        default=None,
                        help="Synthesis profile for the interpretation "
                             "(defaults to --synthesis-profile)")
    parser.add_argument("--report-mode",
                        choices=[m.value for m in ReportMode],
                        default=ReportMode.DETAILED.value,
                        help="summary, detailed or technical (default "
                             "detailed)")
    parser.add_argument("--language", default="en",
                        help="Interpretation language (default en)")
    parser.add_argument("--interpretation-json", metavar="FILE", default=None,
                        help="Write the InterpretationDocument to FILE")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE_DEG,
                        help="Degrees of difference tolerated in the comparison")
    parser.add_argument("--pdf", nargs="?", const="auto", metavar="FILE",
                        help="Save the report as a PDF (filename optional)")
    parser.add_argument("--page-size", choices=["a4", "letter"], default="a4",
                        help="PDF page size")
    parser.add_argument("--landscape", action="store_true",
                        help="Use landscape PDF pages instead of portrait")
    parser.add_argument("--chart-style",
                        choices=["north_indian", "south_indian"],
                        default="north_indian",
                        help="Kundli layout. Presentation only: the same "
                             "placements are drawn in a different "
                             "arrangement")
    parser.add_argument("--list-conventions", action="store_true",
                        help="List the Varga conventions available and exit")
    parser.add_argument("--self-check", action="store_true",
                        help="Verify this installation's resources — "
                             "sources, templates, fonts, data tables — and "
                             "exit")
    parser.add_argument("--selftest", action="store_true",
                        help="Check the ephemeris against reference values and exit")

    # ── V1.7 application layer ───────────────────────────────────────────
    #
    # The console report is unchanged and remains the default. These open
    # the same calculation through the application services, which is the
    # only route the UI and the report writer have.
    parser.add_argument("--app", action="store_true",
                        help="Open the local application in a browser")
    parser.add_argument("--port", type=int, default=8713,
                        help="Port for --app (loopback only)")
    parser.add_argument("--debug", action="store_true",
                        help="Show technical detail with application errors")
    parser.add_argument("--report", metavar="FILE", default=None,
                        help="Write a professional PDF report to FILE "
                             "(typeset, with vector charts; not the console "
                             "transcript --pdf produces)")
    parser.add_argument("--report-html", metavar="FILE", default=None,
                        help="Write a self-contained HTML report to FILE. "
                             "This is the delivery path for languages the "
                             "PDF's Latin fonts cannot print")
    parser.add_argument("--report-json", metavar="FILE", default=None,
                        help="Write the ReportDocument structure to FILE")
    parser.add_argument("--save-consultation", metavar="FILE", default=None,
                        help="Save the consultation input for later recompute")
    parser.add_argument("--open-consultation", metavar="FILE", default=None,
                        help="Load a saved consultation, migrating it if "
                             "it was written by an older build")
    parser.add_argument("--precision", default=None,
                        choices=["EXACT_TO_SECOND", "EXACT_TO_MINUTE",
                                 "APPROX_5_MIN", "APPROX_15_MIN", "UNKNOWN"],
                        help="How well the birth time is actually known")
    parser.add_argument("--save-cache", action="store_true",
                        help="Include the computed chart in a saved "
                             "consultation. Larger, and only a cache: the "
                             "input above remains authoritative")
    parser.add_argument("--export-consultations", metavar="FILE",
                        help="Write the current consultation to a portable "
                             "export file (input and methodology only)")
    parser.add_argument("--import-consultations", metavar="FILE",
                        help="Read an export file and report what it holds")
    parser.add_argument("--privacy", action="store_true",
                        help="Print what is stored, where, and what leaves "
                             "this machine, then exit")
    parser.add_argument("--benchmark", action="store_true",
                        help="Time each stage of the pipeline and exit")
    return parser.parse_args(argv)


def parse_args() -> argparse.Namespace:
    """
    Parse the process's own arguments.

    Kept as the entry point `main()` calls, with `parse_args_from` beneath it
    so a test can ask what the CLI accepts without going through the shell.
    """
    return parse_args_from(None)


def run_selftest() -> int:
    """Print the ephemeris accuracy check; returns a process exit code."""
    print("\n  EPHEMERIS SELF-TEST")
    print(f"  {'Check':<36} {'Computed':>13} {'Reference':>13} {'Error':>10}")
    print("  " + "─" * 80)
    failures = 0
    for label, value, expected, tol, ok in selftest():
        error_arcsec = abs(value - expected) * 3600
        mark = "ok" if ok else "FAIL"
        failures += 0 if ok else 1
        print(f"  {label:<36} {value:>13.6f} {expected:>13.6f} "
              f"{error_arcsec:>8.2f}\"  {mark}")
    print("  " + "─" * 80)
    print(f"  {'All checks passed.' if not failures else str(failures) + ' check(s) failed.'}\n")
    return 1 if failures else 0


def list_conventions():
    """Print every Varga and the conventions it can be computed with."""
    print("\n  AVAILABLE VARGA CONVENTIONS")
    print(f"  {'Chart':<6} {'Name':<18} {'Default':<15} Available")
    print("  " + "─" * 78)
    for key, names in available_conventions().items():
        spec = VARGA_SPECS[key]
        print(f"  {key:<6} {spec.name:<18} {spec.default:<15} {', '.join(names)}")
    print("\n  Select them in a JSON file, e.g.:")
    print('    {"conventions": {"D2": "parivritti", "D30": "movable_lords"}}')
    print("  and pass it with --varga-config.\n")


def collect_input(args: argparse.Namespace) -> ConsultationInput:
    """Build the consultation input from a file, CLI flags, or prompts."""
    if args.consultation:
        data = load_consultation_file(args.consultation)
        if args.enter_degrees:
            data.positions = prompt_positions(data.positions)
        return data

    if args.name and args.dob and args.time and args.place:
        data = ConsultationInput(name=args.name, dob=args.dob,
                                 tob=args.time, place=args.place)
        if args.enter_degrees:
            data.positions = prompt_positions()
        return data

    print("\n" + "═" * 50)
    print("  JYOTISH CALCULATOR")
    print("  Vedic Astrology — Shodasha Varga System")
    print("═" * 50 + "\n")

    name  = args.name  or input("  Naam (Name)        : ").strip() or "Unknown"
    dob   = args.dob   or input("  Janma Tithi (DOB)  : [YYYY-MM-DD] ").strip()
    time_ = args.time  or input("  Janma Samay (Time) : [HH:MM 24hr] ").strip() or "12:00"
    place = args.place or input("  Janma Sthan (Place): ").strip()
    if not place:
        raise InputError(
            "Place of birth is required — the Lagna cannot be computed without "
            "it. Run --list-cities to see the built-in places, or pass "
            "--lat/--lon with --timezone.")

    data = ConsultationInput(name=name, dob=dob, tob=time_, place=place)

    if args.enter_degrees:
        data.positions = prompt_positions()
    else:
        answer = input("\n  Enter planetary degrees manually? [y/N] ").strip().lower()
        if answer.startswith("y"):
            data.positions = prompt_positions()
    return data


def calculate_chart(data: ConsultationInput,
                    ayanamsha_system: str = "lahiri",
                    true_node: bool = True,
                    args: argparse.Namespace | None = None
                    ) -> tuple[JyotishChart, datetime.datetime, "BirthLocation"]:
    """
    Compute a chart from DOB / time / place.

    The place must resolve to real coordinates and a real UTC offset. There is
    no fallback city: a chart computed with someone else's coordinates is
    confidently wrong, which is worse than refusing to compute one.
    """
    dt_local = data.birth_datetime()

    location = resolve_location(
        place=data.place,
        latitude=_first(getattr(args, "lat", None), data.latitude),
        longitude=_first(getattr(args, "lon", None), data.longitude),
        timezone=_first(getattr(args, "timezone", None), data.timezone_name),
        utc_offset=_first(getattr(args, "utc_offset", None), data.utc_offset),
        local_datetime=dt_local,
    )
    dt_utc = location.to_utc(dt_local)

    print(f"\n  Name    : {data.name}")
    print(f"  DOB     : {dt_local.strftime('%d %B %Y, %H:%M')} "
          f"(Local, {location.offset_text()})")
    print(f"  Place   : {location.describe()}")
    print(f"  Source  : {location.source}")
    print(f"  UTC     : {dt_utc.strftime('%Y-%m-%d %H:%M')}")

    jde = jde_from_datetime(dt_utc)
    chart = JyotishChart(jde=jde, lat=location.latitude, lon=location.longitude,
                         ayanamsha_system=ayanamsha_system,
                         true_node=true_node)
    return chart, dt_local, location


def _first(*values):
    """First value that was actually supplied."""
    for value in values:
        if value is not None and value != "":
            return value
    return None


def authoritative_chart(data: ConsultationInput,
                        calculated: JyotishChart) -> JyotishChart:
    """
    Build the chart the interpretation engine runs on. Entered degrees are used
    verbatim; only bodies left blank fall back to the calculated position.
    """
    missing = data.missing_bodies()
    if missing:
        print(f"\n  ⚠ No degrees entered for: {', '.join(missing)}")
        print("    Calculated values are used for those bodies only.")

    lagna_lon = (data.positions[LAGNA_KEY].longitude if LAGNA_KEY in data.positions
                 else calculated.lagna.longitude)
    planet_lons: dict[str, float] = {}
    retrograde: set[str] = set()
    speeds: dict[str, float] = {}
    for body in PLANET_NAMES:
        entered = data.positions.get(body)
        if entered is not None:
            planet_lons[body] = entered.longitude
            if entered.retrograde:
                retrograde.add(body)
            # An entered degree carries no speed. Leaving it out of `speeds`
            # is what makes the feature report mark the motion as unmeasured,
            # rather than presenting a placeholder as an observation.
        elif body in calculated.planets:
            planet_lons[body] = calculated.planets[body].longitude
            speeds[body] = calculated.planets[body].speed
            if calculated.planets[body].is_retrograde:
                retrograde.add(body)

    return JyotishChart.from_sidereal_longitudes(
        lagna_lon=lagna_lon,
        planet_lons=planet_lons,
        retrograde=retrograde,
        ayanamsha=calculated.ayanamsha,
        jde=calculated.jde,
        lat=calculated.lat,
        lon=calculated.lon,
        speeds=speeds,
    )


def print_varga_chart(chart: JyotishChart, config: VargaConfig):
    """Print all 16 varga positions for Lagna and every graha."""
    print(f"\n{'═'*62}")
    print(f"  SHODASHA VARGA — 16 DIVISIONAL CHARTS")
    print(f"{'═'*62}")
    print(config.describe())
    print()

    header = f"  {'Body':<10}"
    for k in VARGA_ORDER:
        header += f" {k:<6}"
    print(header)
    print("  " + "─" * (10 + 7 * len(VARGA_ORDER)))

    rows = [(LAGNA_KEY, chart.lagna.longitude)]
    rows += [(p, chart.planets[p].longitude)
             for p in PLANET_NAMES if p in chart.planets]

    for label, lon in rows:
        vargas = config.compute_all(lon)
        row = f"  {label:<10}"
        for k in VARGA_ORDER:
            row += f" {vargas[k].rashi[:3]:<6}"
        print(row)

    print(f"\n  Rashi abbreviations: Mes=Mesha Vri=Vrishabha Mit=Mithuna Kar=Karka")
    print(f"  Sim=Simha Kan=Kanya Tul=Tula Vri=Vrishchika Dha=Dhanu")
    print(f"  Mak=Makara Kum=Kumbha Mee=Meena")



def print_north_indian_chart(chart: JyotishChart):
    """ASCII representation of North Indian style chart."""
    # 12-house grid positions (North Indian style)
    # House positions in the grid (row, col, span)
    house_positions = {
        12: (0, 1), 1: (0, 2), 2: (0, 3),
        11: (1, 0),             3: (1, 3),
        10: (2, 0),             4: (2, 3),
        9: (3, 0), 8: (3, 1), 7: (3, 2), 6: (3, 3),
    }
    # 5th house is center-left, 6th center etc — simplified display
    house_content = {h: [] for h in range(1, 13)}

    # Lagna
    lagna_house = 1
    house_content[1].append("ASC")

    # Fill planets into houses
    for pname in PLANET_NAMES:
        if pname in chart.planets:
            h = ((chart.planets[pname].rashi_index - chart.lagna.rashi_index) % 12) + 1
            abbrev = pname[:3]
            if chart.planets[pname].is_retrograde:
                abbrev += "℞"
            house_content[h].append(abbrev)

    W = 12  # cell width

    def cell(house_num: int) -> str:
        items = house_content.get(house_num, [])
        rashi = RASHI_NAMES[(chart.lagna.rashi_index + house_num - 1) % 12][:3]
        top = f"{house_num}({rashi})"
        content = " ".join(items)
        # Pad to width
        top = top[:W-1].ljust(W)
        content = content[:W-1].ljust(W)
        return top, content

    print(f"\n  NORTH INDIAN CHART  (Lagna: {chart.lagna.rashi})")
    print(f"  ┌{'─'*W}┬{'─'*W}┬{'─'*W}┬{'─'*W}┐")

    rows_data = [
        [12, 1, 2, 3],
        [11, None, None, 4],
        [10, None, None, 5],
        [9, 8, 7, 6],
    ]

    for ri, row in enumerate(rows_data):
        top_line = "  │"
        bot_line = "  │"
        for ci, h in enumerate(row):
            if h is None:
                if ri == 1 and ci == 1:
                    top_line += f"{'':^{W*2+1}}│"
                    bot_line += f"{'':^{W*2+1}}│"
                    # skip next cell
                elif ri == 1 and ci == 2:
                    continue
                elif ri == 2 and ci in [1, 2]:
                    if ci == 1:
                        top_line += f"{'':^{W*2+1}}│"
                        bot_line += f"{'':^{W*2+1}}│"
                    continue
                else:
                    top_line += " " * W + "│"
                    bot_line += " " * W + "│"
            else:
                t, c = cell(h)
                top_line += t + "│"
                bot_line += c + "│"

        print(top_line)
        print(bot_line)
        if ri < 3:
            if ri == 0:
                print(f"  ├{'─'*W}┼{'─'*W*2+'─'}┼{'─'*W}┤")
            elif ri == 1:
                print(f"  ├{'─'*W}┼{'─'*W*2+'─'}┼{'─'*W}┤")
            elif ri == 2:
                print(f"  ├{'─'*W}┴{'─'*W*2+'─'}┴{'─'*W}┤")

    print(f"  └{'─'*W}─{'─'*W*2+'─'}─{'─'*W}┘")


def _pdf_path(requested: str, name: str) -> str:
    """Resolve the PDF filename, defaulting to a dated name from the person's name."""
    if requested and requested != "auto":
        return requested if requested.lower().endswith(".pdf") else requested + ".pdf"
    slug = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower()
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    return f"kundli_{slug or 'chart'}_{stamp}.pdf"


def _parse_synthesis_date(value: str) -> Optional[datetime.datetime]:
    """
    Read a --synthesis date.

    A bare date means midday, not midnight: the dasha stack and the transit
    positions are both continuous, and midnight sits on a day boundary where
    a reader is most likely to be surprised by which side of an ingress the
    answer fell.
    """
    for fmt, midday in (("%Y-%m-%dT%H:%M", False), ("%Y-%m-%d %H:%M", False),
                        ("%Y-%m-%d", True)):
        try:
            parsed = datetime.datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
        return parsed.replace(hour=12) if midday else parsed
    return None


def build_report(args: argparse.Namespace, varga_config: VargaConfig) -> str:
    """Produce the full report, returning the name used on the consultation."""
    data = collect_input(args)
    ayanamsha_system = args.ayanamsha or data.ayanamsha
    calculated, birth_dt, location = calculate_chart(
        data, ayanamsha_system=ayanamsha_system, true_node=args.node == "true",
        args=args)

    if data.has_entered_degrees:
        data.print_entered()
        print(format_comparison(
            compare(data.positions, calculated, args.tolerance), args.tolerance))
        chart = authoritative_chart(data, calculated)
        print("  Interpretation uses the ENTERED degrees.")
    else:
        chart = calculated
        print("\n  No degrees entered — interpretation uses calculated positions.")

    chart.print_chart()
    print_north_indian_chart(chart)
    print_varga_chart(chart, varga_config)

    features = None
    yoga_results = None
    if not args.no_features:
        features = build_chart_features(
            chart,
            varga_config=varga_config,
            aspect_profile=parashari_profile(args.node_aspects))
        yoga_results = evaluate_rules(features, args.rule_profile)
        print(format_feature_report(features))
        print(format_yoga_report(
            yoga_results,
            profile=args.rule_profile,
            show_absent=args.show_absent_yogas))

    # ── timing ───────────────────────────────────────────────────────────────
    dasha = None
    if not args.no_dasha:
        dasha = dasha_from_chart(chart, birth_dt, depth=args.dasha_depth,
                                 year_length_name=args.dasha_year)
        if dasha is not None:
            print(format_dasha_report(
                dasha, today=datetime.datetime.now(),
                show_all_antardashas=args.all_antardashas))

    # ── V1.4 calculated sections ─────────────────────────────────────────────
    shadbala = None
    ashtakavarga = None
    bhava = None
    sensitivity = None

    if features is not None and not args.no_strength:
        shadbala = compute_shadbala(chart, features, birth=birth_dt,
                                    varga_config=varga_config)
        print(format_shadbala_report(shadbala,
                                     show_subcomponents=args.shadbala_detail))

    if not args.no_ashtakavarga:
        ashtakavarga = compute_ashtakavarga(
            chart, include_reductions=args.ashtakavarga_reductions)
        print(format_ashtakavarga_report(ashtakavarga))

    if args.house_system != "whole_sign":
        bhava = build_bhava_chart(chart, args.house_system,
                                  latitude=location.latitude if location else None)
        print(format_bhava_report(bhava))

    if args.birth_time_sensitivity and location is not None:
        sensitivity = analyse_birth_time(
            location.to_utc(birth_dt), location.latitude, location.longitude,
            ayanamsha_system=ayanamsha_system,
            true_node=args.node == "true",
            varga_config=varga_config,
            bhava_system=(args.house_system
                          if args.house_system != "whole_sign" else None))
        print(format_sensitivity_report(sensitivity))

    # ── V1.5 synthesis, only when explicitly asked for (Part 26) ─────────────
    synthesis_context = None
    candidates: list = []
    transit_snapshot = None
    # An interpretation is a rendering of a synthesis, so asking for the
    # first without the second is always an oversight. Filling it in is
    # better than an error message that just tells the user to type more.
    if args.interpret and not args.synthesis:
        args.synthesis = args.interpret
    if args.interpret and args.interpret_profile:
        args.synthesis_profile = args.interpret_profile

    if args.synthesis and features is not None:
        moment = _parse_synthesis_date(args.synthesis)
        if moment is None:
            print(f"  ✗ Could not read --synthesis date '{args.synthesis}'. "
                  f"Use YYYY-MM-DD or YYYY-MM-DDTHH:MM.")
        else:
            # Shadbala is attached to the features so that rules and
            # synthesis read one computation rather than each doing its own.
            if shadbala is not None:
                features.shadbala = shadbala

            transit_snapshot = get_transit_snapshot(moment, natal_chart=chart)
            reliability = build_reliability(
                sensitivity,
                **({"birth_time_precision_seconds":
                    args.birth_time_precision,
                    "precision_basis": "stated on the command line"}
                   if args.birth_time_precision else {}))

            synthesis_context = synthesise(
                features, moment=moment, yoga_results=yoga_results,
                dasha=dasha, transit_snapshot=transit_snapshot,
                ashtakavarga=ashtakavarga, reliability=reliability,
                profile=SynthesisProfile(args.synthesis_profile),
                domains=args.domain)

            events = []
            if dasha is not None:
                # Transit events give the windows real edges. The scan is
                # bounded by the running antardasha rather than by a fixed
                # span: events outside the period cannot narrow a window
                # inside it, so scanning further is only cost. Capped at a
                # year either way because the scan bisects every graha and an
                # 18-year Rahu antardasha would take minutes to no purpose.
                window = dasha.get_period_at(moment, level="antardasha")
                horizon = datetime.timedelta(days=365)
                start = max(window.start, moment - horizon) if window \
                    else moment - horizon
                end = min(window.end, moment + horizon) if window \
                    else moment + horizon
                # Only the slow grahas, and only the event kinds that can
                # bound a window. Chandra changes rashi every 2.3 days, so
                # its ingresses cannot narrow a period measured in months and
                # scanning for them costs more than everything else combined.
                # Nakshatra ingresses are excluded for the same reason.
                try:
                    events = get_transit_events_between(
                        start, end,
                        planets=("Guru", "Shani", "Rahu", "Ketu", "Mangal"),
                        kinds=("sign_ingress", "station_retrograde",
                               "station_direct", "exact_conjunction"),
                        natal_chart=chart)
                except Exception as exc:
                    print(f"  ! Transit event scan skipped: {exc}")
                candidates = event_candidates(
                    synthesis_context, dasha=dasha, transit_events=events)

            print(format_synthesis_report(
                synthesis_context, candidates,
                show_evidence=args.synthesis_evidence,
                domain_filter=args.domain))

            if args.prediction_json:
                natal = None
                if args.json_output:
                    natal = build_snapshot(
                        chart, features=features, yoga_results=yoga_results,
                        dasha=dasha, varga_config=varga_config,
                        birth_datetime=birth_dt, location=location,
                        name=data.name, rule_profile=args.rule_profile,
                        shadbala=shadbala, ashtakavarga=ashtakavarga,
                        bhava=bhava, sensitivity=sensitivity).to_dict()
                snapshot = build_prediction_snapshot(
                    synthesis_context, natal_snapshot=natal,
                    transit_snapshot=transit_snapshot, candidates=candidates)
                try:
                    snapshot.write(args.prediction_json,
                                   indent=None if args.json_compact else 2)
                except OSError as exc:
                    print(f"  ✗ Could not write prediction JSON: {exc}")
                else:
                    print(f"  🔮 Prediction snapshot (schema "
                          f"{snapshot.schema_version}) saved: "
                          f"{args.prediction_json}")

            # ── V1.6 interpretation (Part 27) ────────────────────────────
            if args.interpret:
                prediction = build_prediction_snapshot(
                    synthesis_context,
                    transit_snapshot=transit_snapshot,
                    candidates=candidates).to_dict()
                try:
                    document = build_interpretation(
                        prediction,
                        language=args.language,
                        mode=ReportMode(args.report_mode),
                        features=features,
                        birth={
                            "name": data.name,
                            "date": birth_dt.strftime("%Y-%m-%d"),
                            "time": birth_dt.strftime("%H:%M"),
                            "place": (location.name if location
                                      else "an unrecorded place"),
                        },
                        domains=args.domain)
                except Exception as exc:
                    # A missing template key is a defect, not a degraded
                    # mode. Part 29: fail visibly rather than printing a
                    # document with a hole in it.
                    print(f"  ✗ Interpretation failed: {exc}")
                else:
                    print(format_interpretation(document))
                    if args.interpretation_json:
                        try:
                            document.write(
                                args.interpretation_json,
                                indent=None if args.json_compact else 2)
                        except OSError as exc:
                            print(f"  ✗ Could not write interpretation "
                                  f"JSON: {exc}")
                        else:
                            print(f"  📝 Interpretation (schema "
                                  f"{document.schema_version}, "
                                  f"{document.report_mode.value}) saved: "
                                  f"{args.interpretation_json}")
    elif args.synthesis and features is None:
        print("  ✗ --synthesis needs the feature engine; drop --no-features.")

    # ── legacy V1 output, only when explicitly asked for ─────────────────────
    # The old fal report contains a second, superseded yoga system. Printing it
    # beside the rule engine's would put two contradictory answers in one
    # document, so it is opt-in and carries its own banner.
    if args.legacy_fal:
        print(generate_fal_report(chart, birth_date=birth_dt))

    # ── canonical snapshot ───────────────────────────────────────────────────
    if args.json_output:
        snapshot = build_snapshot(
            chart, features=features, yoga_results=yoga_results, dasha=dasha,
            varga_config=varga_config, birth_datetime=birth_dt,
            birth_utc=location.to_utc(birth_dt) if location else None,
            location=location, name=data.name,
            rule_profile=args.rule_profile,
            shadbala=shadbala, ashtakavarga=ashtakavarga, bhava=bhava,
            sensitivity=sensitivity)
        try:
            snapshot.write(args.json_output,
                           indent=None if args.json_compact else 2)
        except OSError as exc:
            print(f"  ✗ Could not write JSON: {exc}")
        else:
            print(f"  📋 Chart snapshot (schema {snapshot.schema_version}) "
                  f"saved: {args.json_output}")

    print("  Calculations complete. Jai Shri Ganeshaya Namah 🙏")
    return data.name



#: Flags that may override a loaded consultation, and how each applies.
#: Deliberately short: methodology is what a saved consultation exists to
#: preserve, and silently changing an ayanamsha on reopen would make the
#: file useless for the thing it is for.
_OVERRIDES = {
    "language": lambda record, value: (
        setattr(record.report, "language", value),
        setattr(record.settings, "language", value)),
    "report_mode": lambda record, value: setattr(record.report, "mode",
                                                 value),
    "page_size": lambda record, value: setattr(record.report, "page_size",
                                               value),
    # Presentation, so it overrides a saved file freely — Part 27 keeps
    # presentation and calculation apart, and changing how a chart is
    # drawn cannot change what it says.
    "chart_style": lambda record, value: setattr(record.report,
                                                 "chart_style", value),
    "synthesis_profile": lambda record, value: setattr(
        record.settings, "synthesis_profile", value),
}


def _was_supplied(args: argparse.Namespace, flag: str) -> bool:
    """
    Whether a flag was typed, as opposed to left at its default.

    argparse does not record this, so the namespace is compared against one
    parsed from no arguments at all.
    """
    global _DEFAULT_ARGS
    if _DEFAULT_ARGS is None:
        _DEFAULT_ARGS = parse_args_from([])
    return getattr(args, flag) != getattr(_DEFAULT_ARGS, flag)


_DEFAULT_ARGS: Optional[argparse.Namespace] = None


def consultation_from_args(args: argparse.Namespace):
    """
    A V1.7 ConsultationRecord from the command line or a saved file.

    The CLI's own flags stay exactly as they were; this reads the same
    values into the application layer's shape, so `--app`, `--report` and
    the console report all describe one consultation rather than three
    parallel notions of one.
    """
    from app.models import (
        ApplicationSettings, BirthTimePrecision, ConsultationRecord,
        ReportPreferences,
    )
    from app import storage

    if args.open_consultation:
        # Through the service, which also checks that the methodology the
        # file names still exists in this build. Part 25: an invalid
        # profile is a recoverable error at open time, not a failure three
        # minutes into a calculation.
        from app.services import load_consultation
        record, report = load_consultation(args.open_consultation)
        print(f"\n  Loaded {args.open_consultation} "
              f"(schema {report['read_schema']})")
        # The migration STEPS, not only their side effects. A reader who
        # sees only the notes cannot tell whether the file was rewritten
        # at all, and Part 24 requires the change to be recorded.
        for step in report.get("migrations") or []:
            print(f"    \u2192 migrated {step['from']} to {step['to']}: "
                  f"{step['what']}")
            if step.get("assumed"):
                print(f"      assumed: {step['assumed']}")
        for note in report["migration_notes"]:
            print(f"    ! {note}")
        print(f"    methodology: {record.settings.ayanamsha} ayanamsha, "
              f"{record.settings.rule_profile} rules, "
              f"{record.settings.synthesis_profile} synthesis")

        # A flag the user actually typed overrides the saved file; one they
        # did not is left as saved. Without this, `--language hi` on a
        # consultation saved in English silently produced an English
        # report, which is the same class of defect as a migration
        # applying today's defaults to yesterday's chart.
        for flag, apply in _OVERRIDES.items():
            if _was_supplied(args, flag):
                apply(record, getattr(args, flag))
                print(f"    \u2022 {flag.replace('_', '-')} overridden on "
                      f"the command line: {getattr(args, flag)}")
        return record

    data = collect_input(args)
    precision = (BirthTimePrecision(args.precision) if args.precision
                 else BirthTimePrecision.from_time_text(data.tob))
    settings = ApplicationSettings(
        ayanamsha=(args.ayanamsha or data.ayanamsha or "lahiri").lower(),
        node=args.node,
        house_system=args.house_system,
        rule_profile=args.rule_profile,
        node_aspects=args.node_aspects,
        synthesis_profile=args.synthesis_profile,
        language=args.language,
        varga_profile=args.varga_config,
        compute_strength=not args.no_strength,
        compute_ashtakavarga=not args.no_ashtakavarga,
        compute_sensitivity=args.birth_time_sensitivity,
        ashtakavarga_reductions=args.ashtakavarga_reductions)
    return ConsultationRecord(
        name=data.name, date_of_birth=data.dob, time_of_birth=data.tob,
        place=data.place, precision=precision,
        latitude=_first(args.lat, data.latitude),
        longitude=_first(args.lon, data.longitude),
        timezone_name=_first(args.timezone, data.timezone_name),
        utc_offset=_first(args.utc_offset, data.utc_offset),
        settings=settings,
        report=ReportPreferences(mode=args.report_mode,
                                 language=args.language,
                                 page_size=args.page_size,
                                 chart_style=args.chart_style),
        entered_positions={b: p.raw for b, p in data.positions.items()})



def _has_birth_details(args: argparse.Namespace) -> bool:
    """Whether a chart can be built without asking the console for anything."""
    if args.open_consultation or args.consultation:
        return True
    return bool(args.dob and args.time and args.place)


def run_application(args: argparse.Namespace) -> int:
    """`--app`, `--report`, `--benchmark` and the consultation store."""
    from app import storage
    from app.errors import ApplicationError, ReportGenerationError
    from app.report.pdf import PdfUnsupportedText

    try:
        if args.privacy:
            from app.services import describe_storage

            record = describe_storage()
            print("\n  WHAT THIS APPLICATION STORES")
            for heading in ("what_is_stored", "what_is_not_stored", "where",
                            "what_leaves_the_machine"):
                print(f"\n  {heading.replace('_', ' ').upper()}")
                for line in record[heading]:
                    print(f"    \u2022 {line}")
            print(f"\n  {record['network_use']}\n")
            return 0

        if args.import_consultations:
            from app.services import import_consultations

            records, reports = import_consultations(args.import_consultations)
            print(f"\n  Read {len(records)} consultation(s) from "
                  f"{args.import_consultations}")
            for entry, report in zip(records, [r for r in reports
                                               if not r.get("failed")]):
                print(f"    \u2022 {entry.name} — {entry.date_of_birth} "
                      f"{entry.time_of_birth}, {entry.place}")
                for note in report.get("migration_notes") or []:
                    print(f"        {note}")
            for report in reports:
                if report.get("failed"):
                    print(f"    \u2717 entry {report['index'] + 1}: "
                          f"{report['reason']}")
            print()
            return 0

        if args.app:
            from app.ui import serve

            # The UI HAS a consultation form. Prompting on the console for
            # details the browser is about to ask for was the first thing
            # `--app` did, and it blocked the server from starting at all
            # when stdin was not a terminal.
            #
            # So birth details are read only when they were actually
            # supplied on the command line or in a file, and `--app` alone
            # opens straight onto the empty form.
            record = None
            if _has_birth_details(args):
                record = consultation_from_args(args)
            print("\n  Starting the local application. Nothing leaves this "
                  "machine.")
            serve(port=args.port, debug=args.debug, record=record)
            return 0

        record = consultation_from_args(args)

        if args.export_consultations:
            from app.services import export_consultations

            path = export_consultations([record], args.export_consultations)
            print(f"\n  \U0001f4e6 Exported to {path} — input and "
                  f"methodology only; charts are recomputed on import.\n")
            return 0

        if args.benchmark:
            from app.benchmark import run_benchmark, format_benchmark
            print(format_benchmark(run_benchmark(record)))
            return 0

        from app.services import calculate_chart, calculate_prediction
        from app.services.report_service import generate_report
        from app.report import render_pdf

        natal = calculate_chart(record, record.settings)
        moment = args.interpret or args.synthesis
        prediction = calculate_prediction(
            natal, moment=moment or datetime.datetime.now(),
            profile=record.settings.synthesis_profile,
            domains=args.domain)
        document = generate_report(record, record.settings, record.report,
                                   natal=natal, prediction=prediction,
                                   domains=args.domain)

        if args.report_json:
            with open(args.report_json, "w", encoding="utf-8") as handle:
                handle.write(document.to_json())
                handle.write("\n")
            print(f"  📑 Report structure saved: {args.report_json}")

        if args.report_html:
            from app.report import write_html
            write_html(document.to_dict(), args.report_html,
                       record.report.language)
            print(f"  🌐 {record.report.mode.capitalize()} report "
                  f"({record.report.language}) saved: {args.report_html}")

        if args.report:
            # The PDF refuses a script its Latin faces cannot print rather
            # than producing a page of question marks. That refusal is a
            # message for the user, not a traceback.
            try:
                data = render_pdf(document.to_dict(),
                                  page_size=record.report.page_size)
            except PdfUnsupportedText as exc:
                raise ReportGenerationError(
                    f"A PDF cannot be produced in "
                    f"'{record.report.language}': it contains a script no "
                    f"face available to this build can draw.",
                    detail=str(exc),
                    hint="Use --report-html instead. That report is "
                         "complete, it prints from a browser, and the "
                         "browser supplies the font and the shaping.",
                    field="language") from exc
            with open(args.report, "wb") as handle:
                handle.write(data)
            print(f"  📄 {record.report.mode.capitalize()} report "
                  f"({len(data):,} bytes) saved: {args.report}")

        if args.save_consultation:
            # The cache is OPT-IN from V1.8. It made a saved consultation
            # two megabytes — a full technical snapshot plus a prediction
            # — where the input and methodology that actually reproduce
            # the chart are under two kilobytes. Part 26: do not embed
            # calculated data when the input is sufficient.
            storage.save(
                record, args.save_consultation,
                snapshot=natal.snapshot if args.save_cache else None,
                prediction=(prediction.snapshot
                            if args.save_cache and prediction else None))
            size = os.path.getsize(args.save_consultation)
            print(f"  💾 Consultation saved: {args.save_consultation} "
                  f"({size:,} bytes"
                  + (", with a cached calculation)" if args.save_cache
                     else ")"))
        return 0

    except ApplicationError as exc:
        # An expected failure. The user gets the message and the hint; the
        # detail is technical and appears only in debug mode.
        print(f"\n  ✗ {exc.category}: {exc.message}")
        if exc.hint:
            print(f"    {exc.hint}")
        if args.debug and exc.detail:
            print(f"    detail: {exc.detail}")
        return 2

    except KeyboardInterrupt:
        print("\n  Interrupted. Nothing was written.")
        return 130

    except Exception as exc:                        # noqa: BLE001
        # Part 30 and Part 36. An UNEXPECTED failure: the user gets a
        # sentence and a reference, never a traceback, and the traceback
        # goes into a local file that carries no birth details.
        #
        # `--debug` re-raises instead, because a developer who asked for
        # debugging wants the real stack in their terminal.
        from app.diagnostics import (
            crash_report, format_crash_notice, write_crash_report,
        )
        from app.services.version_service import versions as _versions

        if args.debug:
            raise
        report = crash_report(
            exc, operation="command line",
            settings=getattr(locals().get("record", None), "settings", None),
            versions=_versions(), debug=False)
        print(format_crash_notice(report, write_crash_report(report)))
        return 3


def main():
    args = parse_args()

    if args.self_check:
        from app.services.selfcheck import format_selfcheck, run_selfcheck

        report = run_selfcheck()
        print(format_selfcheck(report))
        sys.exit(0 if report["ok"] else 1)

    if args.selftest:
        sys.exit(run_selftest())

    if args.list_conventions:
        list_conventions()
        return

    if args.list_cities:
        cities = known_cities()
        print(f"\n  BUILT-IN BIRTH PLACES ({len(cities)})")
        print("  Any place not listed must be given as --lat/--lon with "
              "--timezone or --utc-offset.")
        print("  " + "─" * 70)
        for row in range(0, len(cities), 4):
            print("  " + "".join(f"{city:<22}" for city in cities[row:row + 4]))
        print()
        return

    # The application layer handles these end to end. It is a different
    # entry point into the same services, not a second pipeline.
    if (args.app or args.report or args.report_html or args.report_json
            or args.benchmark or args.save_consultation
            or args.export_consultations or args.import_consultations
            or args.privacy
            or args.open_consultation):
        sys.exit(run_application(args))

    try:
        varga_config = (VargaConfig.from_file(args.varga_config)
                        if args.varga_config else VargaConfig())
    except (OSError, VargaConfigError, ValueError) as exc:
        print(f"  ✗ Varga configuration error: {exc}")
        sys.exit(1)

    captured = io.StringIO()
    try:
        if args.pdf:
            with contextlib.redirect_stdout(Tee(sys.stdout, captured)):
                name = build_report(args, varga_config)
        else:
            name = build_report(args, varga_config)
    except LocationError as exc:
        print(f"\n  ✗ Birth place could not be resolved.\n\n    {exc}\n")
        sys.exit(2)
    except (InputError, OSError, ValueError) as exc:
        print(f"  ✗ {exc}")
        sys.exit(1)

    if args.pdf:
        path = _pdf_path(args.pdf, name)
        try:
            text_to_pdf(captured.getvalue(), path,
                        title=f"Jyotish Chart — {name}", author=name,
                        page_size=args.page_size, landscape=args.landscape)
        except OSError as exc:
            print(f"  ✗ Could not write PDF: {exc}")
            sys.exit(1)
        print(f"  📄 PDF saved: {path}")


if __name__ == "__main__":
    main()
