"""
Screens (V1.7 Parts 3, 5, 9-19, 36)
=====================================
One function per screen. Each is given finished data and returns markup.

WHAT A PAGE FUNCTION IS ALLOWED TO DO

    Read a dictionary and format it. Nothing here computes a house, judges
    a dignity, decides whether a yoga holds, or ranks anything. Where a
    page looks like it is deciding — grouping yogas by status, colouring a
    badge — it is grouping by a value the engine wrote and tinting a word
    the engine chose.

    `tests/test_app_boundary.py` checks that this module imports nothing
    from `engine`. That is the structural version of the same rule.

WHY SEPARATE SCREENS AND NOT ONE LONG PAGE (Part 5)

    The detailed report is thirty-two pages. A single scrolling page of
    that is not a user interface, it is a PDF with worse typography. Each
    screen answers one question and says which methodology answered it.

SILENCE IS RENDERED, NOT SKIPPED (Part 16)

    A domain the strict profile cannot speak about gets a section saying
    so, with the reason. Omitting it would make an absence of evidence look
    like an absence of the question.
"""

from __future__ import annotations

import datetime
from typing import Optional, Sequence

from ..visual import IMPLEMENTED_STYLES, STYLE_LABELS
from .assets import STYLESHEET
from .html import (
    Raw, badge, callout, definition_list, field, input_field, join, select,
    table, tag, text,
)

#: The navigation, in the order Part 5 suggests.
SCREENS = (
    ("overview", "Overview"),
    ("chart", "Birth Chart"),
    ("vargas", "Vargas"),
    ("strength", "Planetary Strength"),
    ("yogas", "Yogas"),
    ("dasha", "Dasha"),
    ("transits", "Transits"),
    ("domains", "Life Areas"),
    ("timeline", "Timeline"),
    ("reliability", "Reliability"),
    ("methodology", "Sources and Methodology"),
)

_ACTIVATION_KIND = {
    "STRONGLY_ACTIVE": "strong", "ACTIVE": "active", "MIXED": "mixed",
    "BACKGROUND": "", "INACTIVE": "silent",
}

_YOGA_GROUPS = (
    ("PRESENT_AND_STRONG", "Strong"),
    ("PRESENT", "Formed"),
    ("PRESENT_BUT_WEAK", "Weakened"),
    ("CANCELLED", "Cancelled"),
)

PRECISION_LABELS = {
    "EXACT_TO_SECOND": "Exact to the second",
    "EXACT_TO_MINUTE": "Exact to the minute",
    "APPROX_5_MIN": "Approximate, within 5 minutes",
    "APPROX_15_MIN": "Approximate, within 15 minutes",
    "UNKNOWN": "Not known",
}


def _s(value, default="—") -> str:
    return default if value in (None, "") else str(value)


def _degree(value) -> str:
    if value is None:
        return "—"
    degrees = int(value)
    minutes = int(round((float(value) - degrees) * 60))
    if minutes == 60:
        degrees, minutes = degrees + 1, 0
    return f"{degrees:02d}°{minutes:02d}'"


def _date(value, with_time=False) -> str:
    if not value:
        return "—"
    try:
        moment = datetime.datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return moment.strftime("%d %b %Y %H:%M" if with_time else "%d %b %Y")


# ── shell ────────────────────────────────────────────────────────────────────

def pdf_actions(language: str = "en") -> list:
    """Download PDF links shown in the masthead on every chart screen."""
    lang_param = f"&language={language}" if language != "en" else ""
    return [
        tag("a", "Summary",  href=f"/report.pdf?mode=summary{lang_param}",
            class_="pdf-link", title="~9 pages"),
        tag("a", "Detailed", href=f"/report.pdf?mode=detailed{lang_param}",
            class_="pdf-link", title="~32 pages"),
        tag("a", "Technical", href=f"/report.pdf?mode=technical{lang_param}",
            class_="pdf-link", title="~33 pages, with sources"),
    ]


def page(title: str, body, screen: str = "", subject: str = "",
         wide: bool = False, actions: Optional[Sequence] = None) -> str:
    """The document shell: masthead, navigation, content, standing notice."""
    nav = join(
        tag("a", label, href=f"/screen/{name}",
            aria_current="page" if name == screen else None)
        for name, label in SCREENS) if screen else Raw("")

    return (
        "<!DOCTYPE html>\n"
        + text(tag(
            "html",
            tag("head", join([
                Raw('<meta charset="utf-8">'),
                Raw('<meta name="viewport" content="width=device-width, '
                    'initial-scale=1">'),
                tag("title", f"{title} — Jyotish Engine"),
                tag("style", Raw(STYLESHEET)),
            ])),
            tag("body", join([
                tag("a", "Skip to content", href="#content", class_="skip"),
                tag("header", join([
                    tag("h1", "Jyotish Engine"),
                    tag("span", subject, class_="subject") if subject
                    else None,
                    tag("span", join(actions or []), class_="actions")
                    if actions else None,
                ]), class_="masthead"),
                tag("nav", nav, class_="screens",
                    aria_label="Screens") if screen else None,
                tag("main", body, id="content",
                    class_="wide" if wide else None),
                tag("footer", tag(
                    "p",
                    "Deterministic calculation and template substitution. "
                    "No language model, no network, no prediction of "
                    "events. Nothing in this build is tradition-validated."),
                    class_="notice"),
            ])),
            lang="en")))


# ── consultation form (Part 3) ───────────────────────────────────────────────

def consultation_form(options: dict, values: Optional[dict] = None,
                      error=None, saved: Sequence[str] = ()) -> str:
    """
    The birth-details form.

    Advanced settings live in a closed `details` block. A user who does not
    know what an ayanamsha is should not have to choose one, and a user who
    does should be able to see, in one place, exactly what the defaults are
    — which is why the block shows each default rather than hiding it
    behind a word like "automatic".
    """
    values = values or {}

    def option_field(key: str, label_override: str = "") -> Raw:
        spec = options[key]
        return field(
            label_override or spec["label"],
            select(key, spec["values"], values.get(key, spec["default"]),
                   field_id=key, labels=spec.get("labels")),
            help_text=f"{spec['help']} Default: {spec['default']}.",
            field_id=key)

    required = tag("div", join([
        field("Name", input_field("name", values.get("name", ""),
                                  field_id="name", required=True),
              field_id="name"),
        field("Date of birth",
              input_field("date_of_birth", values.get("date_of_birth", ""),
                          type_="date", field_id="date_of_birth",
                          required=True),
              help_text="YYYY-MM-DD.", field_id="date_of_birth"),
        field("Time of birth",
              input_field("time_of_birth", values.get("time_of_birth", ""),
                          field_id="time_of_birth", required=True,
                          placeholder="10:35"),
              help_text="24-hour clock. HH:MM, or HH:MM:SS if you have it.",
              field_id="time_of_birth"),
        option_field("birth_time_precision"),
        field("Place of birth",
              input_field("place", values.get("place", ""), field_id="place",
                          placeholder="Jaipur"),
              help_text="A city from the built-in list, or leave blank and "
                        "give coordinates below. No other place is ever "
                        "substituted.",
              field_id="place"),
    ]), class_="grid two")

    geography = tag("div", join([
        field("Latitude", input_field("latitude", values.get("latitude", ""),
                                      field_id="latitude",
                                      placeholder="26.9124"),
              help_text="Decimal degrees, or 26 54 45 N.",
              field_id="latitude"),
        field("Longitude",
              input_field("longitude", values.get("longitude", ""),
                          field_id="longitude", placeholder="75.7873"),
              help_text="Decimal degrees, or 75 47 14 E.",
              field_id="longitude"),
        field("Timezone",
              input_field("timezone", values.get("timezone", ""),
                          field_id="timezone", placeholder="Asia/Kolkata"),
              help_text="IANA name. Historical offsets are applied.",
              field_id="timezone"),
        field("UTC offset",
              input_field("utc_offset", values.get("utc_offset", ""),
                          field_id="utc_offset", placeholder="+05:30"),
              help_text="Only if the timezone name is not known.",
              field_id="utc_offset"),
    ]), class_="grid two")

    advanced = tag("details", join([
        tag("summary", "Advanced methodology settings"),
        tag("div", join([
            tag("p", "These are the shipped defaults. Every one of them is "
                     "recorded with the chart, and changing any of them "
                     "changes the chart.", class_="help"),
            tag("div", join([
                option_field("ayanamsha"), option_field("node"),
                option_field("house_system"), option_field("rule_profile"),
                option_field("node_aspects"),
                option_field("synthesis_profile"),
                option_field("language"), option_field("report_mode"),
            ]), class_="grid three"),
        ]), class_="body"),
    ]))

    parts = []
    if error is not None:
        parts.append(error_panel(error))
    parts.extend([
        tag("h2", "New consultation"),
        tag("p", "Every value below is stored with the chart. Nothing is "
                 "sent anywhere: the application runs entirely on this "
                 "machine.", class_="lead"),
        tag("form", join([
            tag("h3", "Birth details"), required,
            tag("h3", "Coordinates"),
            tag("p", "Fill these in only if the place is not in the "
                     "built-in list, or to override it.", class_="help"),
            geography,
            tag("h3", "Methodology"), advanced,
            tag("p", tag("button", "Calculate chart", type="submit",
                         class_="primary")),
        ]), method="post", action="/calculate"),
    ])
    if saved:
        parts.append(tag("h3", "Saved consultations"))
        parts.append(tag("ul", join(
            tag("li", tag("a", name, href=f"/open?file={name}"))
            for name in saved)))
    return page("Consultation", join(parts), subject="")


def error_panel(error) -> Raw:
    """
    An application error, shown as a sentence.

    `detail` is present only in debug mode — the dictionary simply does not
    carry it otherwise, so there is no path by which a stack trace reaches
    a normal user (Part 33).
    """
    data = error if isinstance(error, dict) else error.to_dict()
    parts = [tag("strong", data.get("category", "Error")),
             tag("p", data.get("message", ""))]
    if data.get("hint"):
        parts.append(tag("p", data["hint"], class_="note"))
    if data.get("detail"):
        parts.append(tag("details", join([
            tag("summary", "Technical detail"),
            tag("div", tag("pre", data["detail"]), class_="body"),
        ])))
    return tag("aside", join(parts), class_="callout warning", role="alert")


# ── screens ──────────────────────────────────────────────────────────────────

def overview(natal: dict, prediction: Optional[dict], charts: Sequence,
             subject: str, actions=None) -> str:
    birth = natal.get("birth") or {}
    location = birth.get("location") or {}
    lagna = natal.get("lagna") or {}
    planets = natal.get("planets") or {}
    chandra = planets.get("Chandra") or {}

    facts = definition_list([
        ("Born", _date(birth.get("datetime_local"), True),
         _s(location.get("name"), "")),
        ("Birth-time precision",
         PRECISION_LABELS.get(birth.get("time_precision"),
                              _s(birth.get("time_precision"), "not recorded")),
         _s(birth.get("time_precision_basis"), "")),
        ("Lagna", f"{_s(lagna.get('sign'))} {_degree(lagna.get('degree_in_sign'))}",
         f"{_s(lagna.get('nakshatra'))} pada {_s(lagna.get('pada'))}"),
        ("Chandra", f"{_s(chandra.get('sign'))} "
                    f"{_degree(chandra.get('degree_in_sign'))}",
         f"{_s(chandra.get('nakshatra'))} pada {_s(chandra.get('pada'))}"),
    ])

    stack = ((prediction or {}).get("dasha") or {}).get("stack") or {}
    running = definition_list([
        (level.capitalize(), _s(stack.get(level)), "")
        for level in ("mahadasha", "antardasha", "pratyantardasha")
    ]) if stack else tag("p", "No dasha has been computed for this chart.",
                         class_="note")

    # `domain_results` is keyed by domain name, not a list.
    results = (prediction or {}).get("domain_results") or {}
    active = [(name, entry) for name, entry in sorted(results.items())
              if entry.get("activation") in ("ACTIVE", "STRONGLY_ACTIVE",
                                             "MIXED")]
    domains = tag("ul", join(
        tag("li", join([
            tag("a", name.replace("_", " ").title(),
                href="/screen/domains#" + name),
            Raw(" "), badge(entry.get("activation", ""),
                            _ACTIVATION_KIND.get(entry.get("activation"), "")),
            Raw(" "), badge(entry.get("confidence", "")),
        ])) for name, entry in active)) if active else tag(
        "p", "No life area reaches the activation threshold at this moment "
             "under the profile in use.", class_="note")

    return page("Overview", join([
        tag("h2", "Overview"),
        tag("div", join([
            tag("section", join([tag("h3", "Birth"), facts]),
                class_="panel"),
            tag("section", join([tag("h3", "Running periods"), running]),
                class_="panel"),
        ]), class_="grid two"),
        tag("h3", "Rashi chart"),
        _chart_figures(charts[:1]),
        tag("h3", "Activated life areas"),
        domains,
        callout("Activation and confidence are ordinal bands produced by "
                "this engine's own weighting. They are not probabilities, "
                "and no likelihood can be derived from them.", "limit"),
    ]), screen="overview", subject=subject, actions=actions)


def _chart_figures(charts: Sequence) -> Raw:
    figures = []
    for item in charts:
        caption = [item.get("caption") or item["name"]]
        if item.get("convention"):
            caption.append(f" · {item['convention']} convention")
        figures.append(tag("figure", join([
            Raw(item["svg"]),
            tag("figcaption", "".join(caption)),
            join(callout(note, "warning") for note in item.get("notes") or []),
        ]), class_="chart"))
    return tag("div", join(figures), class_="grid two")


def chart_screen(natal: dict, charts: Sequence, subject: str,
                 detail: str = "STANDARD", legend: str = "",
                 style: str = "north_indian", style_note: str = "",
                 actions=None) -> str:
    """Part 9: the planetary table, with the technical columns collapsed."""
    planets = natal.get("planets") or {}
    vargas = (natal.get("vargas") or {}).get("bodies") or {}
    strengths = (natal.get("strengths") or {}).get("planets") or {}

    rows = []
    for name, entry in planets.items():
        varga = vargas.get(name, {})
        ratio = (strengths.get(name) or {}).get("ratio")
        state = []
        if entry.get("retrograde"):
            state.append(badge("retrograde", "warn"))
        if entry.get("combust"):
            state.append(badge("combust", "warn"))
        rows.append((
            name, _s(entry.get("sign")), _degree(entry.get("degree_in_sign")),
            _s(entry.get("house")), _s(entry.get("nakshatra")),
            _s(entry.get("pada")), join(state) if state else "—",
            _s(entry.get("dignity")),
            f"{ratio:.2f}" if isinstance(ratio, (int, float)) else "—",
            _s((varga.get("D9") or {}).get("sign")),
            _s((varga.get("D10") or {}).get("sign")),
        ))

    # Both controls are presentation. They are placed together, and the
    # note under the style select says what the chosen layout holds fixed —
    # a reader given a South Indian chart without being told the signs are
    # fixed will read the house numbers as sign numbers.
    detail_options = tag("form", join([
        field("Chart style",
              select("style", IMPLEMENTED_STYLES, style, field_id="style",
                     labels=STYLE_LABELS),
              help_text=style_note or "Presentation only; no calculation "
                                      "changes.",
              field_id="style"),
        field("Chart detail",
              select("detail", ("COMPACT", "STANDARD", "DETAILED"), detail,
                     field_id="detail"),
              help_text="How much is drawn inside each house. Presentation "
                        "only.", field_id="detail"),
        tag("button", "Redraw", type="submit", class_="primary"),
    ]), method="get", action="/screen/chart")

    return page("Birth Chart", join([
        tag("h2", "Birth chart"),
        _chart_figures(charts),
        tag("p", legend, class_="note") if legend else None,
        detail_options,
        tag("h3", "Planetary positions"),
        table(("Graha", "Sign", "Degree", "House", "Nakshatra", "Pada",
               "State", "Dignity", "Shadbala", "D9", "D10"), rows,
              align=("", "", "right", "right", "", "right", "", "", "right",
                     "", "")),
        tag("p", "Shadbala is the ratio of computed strength to the strength "
                 "the source text requires for that graha. A ratio, not a "
                 "score and not a probability.", class_="note"),
    ]), screen="chart", subject=subject, wide=True, actions=actions)


def vargas_screen(natal: dict, charts: Sequence, subject: str,
                  selected: str = "D9", available: Sequence[str] = (),
                  actions=None) -> str:
    """
    Part 10: one varga at a time, with the convention that produced it and
    whether the birth time actually determines it.
    """
    conventions = (natal.get("vargas") or {}).get("conventions") or {}
    convention = conventions.get(selected) or {}
    lagnas = (natal.get("vargas") or {}).get("lagna") or {}
    bodies = (natal.get("vargas") or {}).get("bodies") or {}

    rows = [(name, _s((charts_by := entry.get(selected) or {}).get("sign")),
             _s(charts_by.get("lord")), _s(charts_by.get("dignity")),
             _s(charts_by.get("convention")))
            for name, entry in sorted(bodies.items())]

    chooser = tag("form", join([
        field("Divisional chart",
              select("varga", available or [selected], selected,
                     field_id="varga"),
              help_text="All sixteen are computed for every chart.",
              field_id="varga"),
        tag("button", "Show", type="submit", class_="primary"),
    ]), method="get", action="/screen/vargas")

    details = definition_list([
        ("Lagna", _s((lagnas.get(selected) or {}).get("sign")), ""),
        ("Convention", _s((lagnas.get(selected) or {}).get("convention")),
         _s(convention.get("description") if isinstance(convention, dict)
            else "", "")),
        ("Validation", _s(convention.get("validation_status")
                          if isinstance(convention, dict) else ""),
         "How far this division rule has been traced to a text."),
    ])

    return page("Vargas", join([
        tag("h2", "Divisional charts"),
        chooser,
        tag("div", join([
            tag("section", _chart_figures(charts), class_=""),
            tag("section", join([tag("h3", "Methodology"), details]),
                class_="panel"),
        ]), class_="grid two"),
        tag("h3", f"{selected} placements"),
        table(("Graha", "Sign", "Sign lord", "Dignity", "Convention"), rows),
    ]), screen="vargas", subject=subject, wide=True, actions=actions)


def strength_screen(natal: dict, subject: str, actions=None) -> str:
    """Part 12: Shadbala, with the components expandable and flagged."""
    strengths = natal.get("strengths") or {}
    planets = strengths.get("planets") or {}
    if not planets:
        return page("Planetary Strength", join([
            tag("h2", "Planetary strength"),
            callout("Shadbala was not computed for this chart.", "note"),
        ]), screen="strength", subject=subject, actions=actions)

    rows = [(
        name, f"{entry.get('total_rupa', 0):.2f}",
        f"{entry.get('required_rupa', 0):.2f}",
        f"{entry.get('ratio', 0):.2f}",
        badge("meets requirement" if entry.get("meets_requirement")
              else "below requirement",
              "" if entry.get("meets_requirement") else "warn"),
    ) for name, entry in planets.items()]

    components = ("sthana_bala", "dig_bala", "kala_bala", "chesta_bala",
                  "naisargika_bala", "drik_bala")
    expanders = []
    for name, entry in planets.items():
        detail_rows = [(
            component.replace("_", " ").title(),
            f"{(entry.get(component) or {}).get('value_rupa', 0):.2f}",
            f"{(entry.get(component) or {}).get('value_virupa', 0):.1f}",
            _s((entry.get(component) or {}).get("validation_status")),
            _s((entry.get(component) or {}).get("detail"), ""),
        ) for component in components]
        expanders.append(tag("details", join([
            tag("summary", f"{name} — six components"),
            tag("div", table(
                ("Component", "Rupa", "Virupa", "Validation", "Basis"),
                detail_rows, align=("", "right", "right", "", "")),
                class_="body"),
        ])))

    approximate = sorted(name for name, entry in planets.items()
                         if entry.get("contains_approximation"))
    notes = []
    if approximate:
        notes.append(callout(
            "The strength of " + ", ".join(approximate) + " includes at "
            "least one component computed by an approximation the source "
            "text does not state. The number is reproducible; it is not the "
            "text's number.", "warning",
            title="Methodology not fully source-validated"))
    notes.extend(callout(w, "warning") for w in strengths.get("warnings") or [])

    return page("Planetary Strength", join([
        tag("h2", "Planetary strength (Shadbala)"),
        definition_list([
            ("System", _s(strengths.get("system")), ""),
            ("Profile", _s(strengths.get("methodology_profile")), ""),
            ("Source", _s(strengths.get("source")), ""),
            ("Validation", _s(strengths.get("validation_status")), ""),
        ]),
        table(("Graha", "Total (rupa)", "Required (rupa)", "Ratio", "Verdict"),
              rows, align=("", "right", "right", "right", "")),
        join(notes),
        tag("h3", "Components"),
        join(expanders),
    ]), screen="strength", subject=subject, wide=True, actions=actions)


def yogas_screen(natal: dict, subject: str, actions=None) -> str:
    """Part 11: grouped by status, each expandable to its conditions."""
    yogas = natal.get("yogas") or []
    present = [y for y in yogas if y.get("status") != "ABSENT"]
    groups = []
    for status, label in _YOGA_GROUPS:
        group = [y for y in present if y.get("status") == status]
        if not group:
            continue
        items = []
        for yoga in group:
            body = [tag("p", _s(yoga.get("explanation"), ""))]
            if yoga.get("conditions_met"):
                body.append(tag("h4", "Conditions matched"))
                body.append(tag("ul", join(
                    tag("li", c) for c in yoga["conditions_met"])))
            if yoga.get("conditions_failed"):
                body.append(tag("h4", "Conditions not matched"))
                body.append(tag("ul", join(
                    tag("li", c) for c in yoga["conditions_failed"])))
            if yoga.get("cancellations_found"):
                body.append(tag("h4", "Cancellation conditions"))
                body.append(tag("ul", join(
                    tag("li", c) for c in yoga["cancellations_found"])))
            body.append(definition_list([
                ("Grahas", ", ".join(yoga.get("planets") or []) or "—",
                 ""),
                ("Houses", ", ".join(str(h) for h in yoga.get("houses") or [])
                 or "—", ""),
                ("Rule profile", _s(yoga.get("rule_profile")), ""),
                ("Source validation", _s(yoga.get("validation_status")),
                 "How far the RULE has been traced to a text. Not a "
                 "likelihood."),
                ("Stated at", _s(yoga.get("source"), ""), ""),
            ]))
            items.append(tag("details", join([
                tag("summary", join([
                    Raw(text(yoga.get("name", ""))), Raw(" "),
                    badge(status, "strong" if status == "PRESENT_AND_STRONG"
                          else ("warn" if status in ("PRESENT_BUT_WEAK",
                                                     "CANCELLED") else "")),
                ])),
                tag("div", join(body), class_="body"),
            ])))
        groups.append(tag("section", join(
            [tag("h3", f"{label} ({len(group)})")] + items)))

    return page("Yogas", join([
        tag("h2", "Yogas"),
        tag("p", f"The rule profile evaluated {len(yogas)} rules and found "
                 f"{len(present)} bearing on this chart.", class_="lead"),
        join(groups) if groups else callout(
            "No yoga in this profile is formed in this chart.", "note"),
        callout("A yoga's engine strength, where shown, is a software "
                "heuristic. It is not a probability and no classical text "
                "states it.", "limit"),
    ]), screen="yogas", subject=subject, actions=actions)


def dasha_screen(natal: dict, prediction: Optional[dict], subject: str,
                 actions=None) -> str:
    """Part 14: the Vimshottari hierarchy, expandable, with the current stack."""
    vimshottari = (natal.get("timing") or {}).get("vimshottari") or {}
    mahadashas = vimshottari.get("mahadashas") or []
    stack = ((prediction or {}).get("dasha") or {}).get("stack") or {}
    moment = (prediction or {}).get("datetime")

    def is_current(period) -> bool:
        return bool(moment and (period.get("start") or "") <= moment
                    <= (period.get("end") or ""))

    levels = []
    for maha in mahadashas:
        children = []
        for antara in maha.get("children") or []:
            praty = tag("ul", join(
                tag("li", f"{p.get('lord')} · {_date(p.get('start'))} "
                          f"– {_date(p.get('end'))}")
                for p in antara.get("children") or []))
            children.append(tag("details", join([
                tag("summary", join([
                    Raw(text(f"{maha.get('lord')}–{antara.get('lord')}"
                             f"  {_date(antara.get('start'))} – "
                             f"{_date(antara.get('end'))}")),
                    Raw(" "), badge("running") if is_current(antara) else None,
                ])),
                tag("div", praty, class_="body"),
            ]), open=is_current(antara)))
        levels.append(tag("details", join([
            tag("summary", join([
                Raw(text(f"{maha.get('lord')} mahadasha  "
                         f"{_date(maha.get('start'))} – "
                         f"{_date(maha.get('end'))}")),
                Raw(" "), badge("running", "active") if is_current(maha)
                else None,
            ])),
            tag("div", join(children), class_="body"),
        ]), open=is_current(maha)))

    return page("Dasha", join([
        tag("h2", "Vimshottari dasha"),
        definition_list([
            ("Convention", _s(vimshottari.get("convention")), ""),
            ("Balance at birth", _s(vimshottari.get("balance_at_birth")), ""),
            ("Analysed moment", _date(moment, True), ""),
        ] + [(level.capitalize(), _s(stack.get(level)), "")
             for level in ("mahadasha", "antardasha", "pratyantardasha")
             if stack.get(level)]),
        join(levels),
        callout("This screen shows periods and their boundaries. What a "
                "period is taken to activate is decided on the Life Areas "
                "screen, under the profile recorded there.", "limit"),
    ]), screen="dasha", subject=subject, actions=actions)


def transits_screen(natal: dict, prediction: Optional[dict], subject: str,
                    moment: str = "", events: Sequence = (),
                    actions=None) -> str:
    """Part 15: facts first, and interpretation nowhere on this screen."""
    snapshot = ((prediction or {}).get("transits") or {}).get("snapshot") or {}
    positions = snapshot.get("planetary_positions") or {}

    chooser = tag("form", join([
        field("Date", input_field("moment", moment[:10], type_="date",
                                  field_id="moment"),
              help_text="A bare date is read as midday, so the answer does "
                        "not sit on a midnight boundary.",
              field_id="moment"),
        tag("button", "Recalculate", type="submit", class_="primary"),
    ]), method="get", action="/screen/transits")

    rows = [(
        name, _s(entry.get("sign")), _degree(entry.get("degree_in_sign")),
        _s(entry.get("house_from_natal_lagna")),
        _s(entry.get("house_from_natal_moon")),
        _s(entry.get("nakshatra")),
        join([badge("retrograde", "warn")] if entry.get("retrograde") else [])
        or ("stationary" if entry.get("stationary") else "—"),
    ) for name, entry in sorted(positions.items())]

    relations = snapshot.get("transit_to_natal") or []
    relation_table = table(
        ("Transiting", "Relationship", "Natal point", "Separation"),
        [(_s(r.get("transiting_planet") or r.get("from")),
          _s(r.get("relationship") or r.get("type")).replace("_", " "),
          _s(r.get("natal_point") or r.get("to")),
          _s(r.get("orb_deg") or r.get("separation_deg")))
         for r in relations]) if relations else tag(
        "p", "No transit-to-natal relationship is within orb at this moment.",
        class_="note")

    event_rows = [(
        _date(getattr(e, "moment", None) or e.get("moment"), True),
        _s(getattr(e, "planet", None) or e.get("planet")),
        _s(getattr(e, "kind", None) or e.get("kind")).replace("_", " "),
        _s(getattr(e, "detail", None) or e.get("detail")),
    ) for e in events]

    return page("Transits", join([
        tag("h2", "Transits"),
        chooser,
        tag("p", f"Positions for {_date(moment, True)}.", class_="lead")
        if moment else None,
        table(("Graha", "Sign", "Degree", "House from Lagna",
               "House from Chandra", "Nakshatra", "State"), rows,
              align=("", "", "right", "right", "right", "", "")),
        tag("h3", "Transit to natal"),
        relation_table,
        tag("h3", "Ingresses and stations"),
        table(("When", "Graha", "Event", "Detail"), event_rows)
        if event_rows else tag(
            "p", "No ingress or station was scanned for this window.",
            class_="note"),
        callout("Everything on this screen is an astronomical fact. Nothing "
                "here says what a transit means; that is decided on the Life "
                "Areas screen and is recorded there with its profile.",
                "limit"),
    ]), screen="transits", subject=subject, wide=True, actions=actions)


def domains_screen(interpretation: Optional[dict], prediction: Optional[dict],
                   subject: str, profile: str = "standard",
                   profiles: Sequence[str] = (), actions=None) -> str:
    """Part 16: every domain, including the silent ones, with their reasons."""
    sections = (interpretation or {}).get("domain_sections") or []

    chooser = tag("form", join([
        field("Synthesis profile",
              select("profile", profiles or [profile], profile,
                     field_id="profile"),
              help_text="How much evidence a conclusion may rest on. Strict "
                        "uses only factors whose link to the area has a "
                        "located textual source.",
              field_id="profile"),
        tag("button", "Apply", type="submit", class_="primary"),
    ]), method="get", action="/screen/domains")

    blocks = []
    for section in sections:
        heading = tag("h3", join([
            Raw(text(section.get("title") or section.get("domain"))),
            Raw(" "),
            badge(section.get("activation", ""),
                  _ACTIVATION_KIND.get(section.get("activation"), "")),
            Raw(" "), badge(section.get("confidence", "")),
        ]), id=section.get("domain"))
        body = [heading]

        if section.get("silence"):
            body.append(callout(section["silence"]["text"], "note",
                                title="Nothing reported"))
            blocks.append(tag("section", join(body)))
            continue

        for key in ("overall", "confidence_statement", "contradiction"):
            phrase = section.get(key)
            if phrase and phrase.get("text"):
                body.append(tag("p", phrase["text"],
                                class_="lead" if key == "overall" else None))
        if section.get("safety"):
            body.append(callout(section["safety"]["text"], "limit"))
        for key, label in (("natal_foundation", "Natal foundation"),
                           ("supporting_factors", "Supporting factors"),
                           ("challenging_factors", "Challenging factors"),
                           ("dasha_activation", "Dasha activation"),
                           ("transit_triggers", "Transit triggers"),
                           ("varga_confirmation",
                            "Divisional chart confirmation"),
                           ("timing", "Timing")):
            items = section.get(key) or []
            if not items:
                continue
            body.append(tag("h4", label))
            body.append(tag("ul", join(
                tag("li", p["text"]) for p in items if p.get("text"))))
        for phrase in section.get("reliability") or []:
            body.append(callout(phrase["text"], "warning"))
        blocks.append(tag("section", join(body)))

    # Rules the profile refused, each with the gate's own reason. Shown,
    # not hidden: a strict run that drops forty rules and says nothing
    # about it looks like a chart with nothing in it rather than a profile
    # that declined to speak.
    excluded = sorted((prediction or {}).get("excluded_by_profile") or [],
                      key=lambda item: item.get("rule_id", ""))
    return page("Life Areas", join([
        tag("h2", "Life areas"),
        chooser,
        join(blocks) if blocks else callout(
            "No interpretation has been rendered for this chart.", "note"),
        tag("h3", f"Excluded by this profile ({len(excluded)})")
        if excluded else None,
        table(("Rule", "Status", "Eligibility", "Reason"),
              [(_s(item.get("name") or item.get("rule_id")),
                _s(item.get("status")), _s(item.get("eligibility")),
                _s(item.get("reason"), ""))
               for item in excluded]) if excluded else None,
    ]), screen="domains", subject=subject, actions=actions)


def timeline_screen(rows: Sequence[dict], subject: str,
                    domains: Sequence[str] = (),
                    selected: Sequence[str] = (), actions=None) -> str:
    """
    Part 17: candidate windows on a time axis.

    The bar shows WHEN, never HOW LIKELY. Its length is the window and its
    mark is the calculated peak; nothing about it is scaled by activation,
    because a longer or thicker bar for STRONGLY_ACTIVE would be a
    probability drawn as a picture.
    """
    if not rows:
        body = callout(
            "No timing window could be derived for any area from the dasha "
            "boundaries and transit events available. A window this engine "
            "cannot derive is not reported as a vague one.", "note")
    else:
        starts = [r["window_start"] for r in rows if r.get("window_start")]
        ends = [r["window_end"] for r in rows if r.get("window_end")]
        span_start, span_end = (min(starts), max(ends)) if starts and ends \
            else (None, None)

        def fraction(value) -> Optional[float]:
            if not (value and span_start and span_end
                    and span_end > span_start):
                return None
            try:
                point = datetime.datetime.fromisoformat(value)
                low = datetime.datetime.fromisoformat(span_start)
                high = datetime.datetime.fromisoformat(span_end)
            except ValueError:
                return None
            return max(0.0, min(1.0, (point - low) / (high - low)))

        events = []
        for row in rows:
            left = fraction(row.get("window_start")) or 0.0
            right = fraction(row.get("window_end"))
            right = 1.0 if right is None else right
            peak = fraction(row.get("peak"))
            bar_children = [tag(
                "span", "", class_="fill",
                style=f"left:{left * 100:.1f}%;"
                      f"width:{max(0.6, (right - left) * 100):.1f}%")]
            if peak is not None:
                bar_children.append(tag("span", "", class_="peak",
                                        style=f"left:{peak * 100:.1f}%"))
            events.append(tag("div", join([
                tag("div", join([
                    Raw(text(row["domain"].replace("_", " ").title())),
                    Raw(" "),
                    badge(row["event_type"]),
                    Raw(" "),
                    badge(row["activation"],
                          _ACTIVATION_KIND.get(row["activation"], "")),
                    Raw(" "), badge(row["confidence"]),
                ])),
                tag("div", join(bar_children), class_="bar",
                    role="img",
                    aria_label=(
                        f"{row['domain']} window from "
                        f"{_date(row.get('window_start'))} to "
                        f"{_date(row.get('window_end'))}"
                        + (f", strongest calculated trigger around "
                           f"{_date(row.get('peak'))}" if row.get("peak")
                           else ", with no single strongest point"))),
                tag("div", f"{_date(row.get('window_start'))} – "
                           f"{_date(row.get('window_end'))}"
                           + (f" · peak {_date(row['peak'])}"
                              if row.get("peak") else ""),
                    class_="when"),
                tag("p", _s(row.get("basis"), ""), class_="note"),
            ]), class_="event"))
        body = tag("div", join(events), class_="timeline")

    filter_form = tag("form", join([
        field("Area", select("domain", ["(all)"] + list(domains),
                             (list(selected) or ["(all)"])[0],
                             field_id="domain"),
              help_text="Filtering changes what is listed, never what was "
                        "calculated.", field_id="domain"),
        tag("button", "Filter", type="submit", class_="primary"),
    ]), method="get", action="/screen/timeline")

    return page("Timeline", join([
        tag("h2", "Event candidates"),
        filter_form,
        body,
        callout("A candidate is a window in which this engine's rules place "
                "an activation. It is not a forecast that anything will "
                "happen. Activation and confidence are ordinal bands and no "
                "probability can be derived from them.", "limit"),
    ]), screen="timeline", subject=subject, actions=actions)


def reliability_screen(natal: dict, prediction: Optional[dict],
                       warnings: Sequence[str], subject: str,
                       actions=None) -> str:
    """Part 19: everything the engine is unsure about, in one place."""
    birth = natal.get("birth") or {}
    sensitivity = natal.get("birth_time_sensitivity") or {}
    accuracy = natal.get("accuracy") or {}

    blocks = [
        tag("h2", "Reliability and calculation notes"),
        definition_list([
            ("Birth-time precision",
             PRECISION_LABELS.get(birth.get("time_precision"),
                                  _s(birth.get("time_precision"),
                                     "not recorded")),
             _s(birth.get("time_precision_basis"), "")),
            ("Largest stable window",
             (f"{sensitivity.get('largest_stable_window_minutes')} minutes"
              if sensitivity.get("largest_stable_window_minutes")
              else "none of the windows tested is stable"),
             "Nothing in the chart changes within this window either side "
             "of the recorded time."),
        ]),
    ]

    if not sensitivity:
        blocks.append(callout(
            "Birth-time sensitivity was not calculated for this chart. "
            "Nothing here has been shown to be stable against a small change "
            "in the recorded time, and the absence of a warning is not "
            "evidence of stability.", "warning"))
    else:
        unstable = []
        for window in sensitivity.get("windows") or []:
            for change in window.get("detail") or []:
                if change.get("description") not in unstable:
                    unstable.append(change.get("description"))
        if unstable:
            blocks.append(tag("h3", "Unstable within the birth-time "
                                    "uncertainty"))
            blocks.append(tag("ul", join(tag("li", u) for u in unstable)))
        else:
            blocks.append(tag("p", "Nothing the scan watches changes within "
                                   "the windows tested.", class_="note"))

    boundary = accuracy.get("bodies_with_warnings") or []
    if boundary:
        blocks.append(callout(
            "The calculation does not resolve the sign or nakshatra of: "
            + ", ".join(boundary) + ". This is the engine's own error "
            "envelope and is independent of the birth time.", "warning",
            title="Unresolved boundaries"))

    for warning in (prediction or {}).get("warnings") or []:
        blocks.append(callout(warning, "warning"))
    for warning in warnings:
        blocks.append(callout(warning, "warning"))

    blocks.append(callout(
        "Computationally tested, externally benchmarked, textual source "
        "located and tradition-validated are four separate claims about "
        "this engine, and none is evidence for another. Nothing in this "
        "build is tradition-validated.", "limit", title="Four separate claims"))
    return page("Reliability", join(blocks), screen="reliability",
                subject=subject, actions=actions)


def methodology_screen(methodology: dict, subject: str,
                       provenance: Optional[dict] = None,
                       actions=None) -> str:
    """Part 18: exactly how this chart was computed."""
    rows = [(row["label"], _s(row["value"]), _s(row.get("note"), ""))
            for row in methodology.get("rows") or []]
    registry = methodology.get("provenance") or {}
    claims = methodology.get("claim_separation") or {}

    return page("Sources & Methodology", join([
        tag("h2", "Methodology"),
        table(("Setting", "Value", "Note"), rows),
        tag("h3", "Source registry"),
        definition_list([
            (key.replace("_", " ").capitalize(), _s(value), "")
            for key, value in sorted(registry.items())
            if not isinstance(value, (dict, list))
        ]),
        tag("h3", "Rules by validation status"),
        table(("Status", "Rules"),
              [(k, str(v)) for k, v in sorted(
                  (registry.get("rules_by_validation_status") or {}).items())])
        if registry.get("rules_by_validation_status") else tag(
            "p", "Not recorded in this snapshot.", class_="note"),
        tag("h3", "What the claims mean"),
        definition_list([
            (key.replace("_", " ").capitalize(), value, "")
            for key, value in claims.items() if isinstance(value, str)
        ]),
    ]), screen="methodology", subject=subject, wide=True, actions=actions)
