"""
Report builder (V1.7 Parts 20, 22, 23)
========================================
Snapshots in, ReportDocument out.

MODES SELECT, THEY DO NOT REPHRASE (Part 22)

    SUMMARY, DETAILED and TECHNICAL differ in which sections are present and
    how much of each is shown. The sentences are identical wherever they
    appear, because they are not produced here at all — they arrive already
    rendered in the InterpretationDocument, which V1.6 built at the
    requested mode from the one template set.

    There is deliberately no `if mode == "summary": shorter_wording` branch
    anywhere in this file. That branch is how two reports of the same chart
    start disagreeing.

THIS MODULE READS DICTIONARIES

    It takes serialised snapshots, not engine objects, and imports nothing
    from `engine`. Every value it prints was computed and written down
    elsewhere; where it looks like a calculation is happening — a ratio
    formatted to two places, a count of yogas by status — it is formatting
    and counting, never astrology.
"""

from __future__ import annotations

import datetime
from typing import Optional, Sequence

from .strings import ENGLISH, ReportStrings, load_strings
from .document import (
    Bullets, Callout, ChartBlock, Heading, KeyValues, Paragraph,
    ReportDocument, Section, Table,
)

#: Which sections each mode carries. Part 22's three depths, as data.
MODE_SECTIONS = {
    "summary": ("cover", "birth_details", "executive_summary", "charts",
                "life_domains", "reliability"),
    "detailed": ("cover", "birth_details", "executive_summary", "charts",
                 "planets", "strengths", "yogas", "life_domains", "dasha",
                 "transit_summary", "timing_windows", "reliability",
                 "methodology"),
    "technical": ("cover", "birth_details", "executive_summary", "charts",
                  "planets", "strengths", "yogas", "life_domains", "dasha",
                  "transit_summary", "timing_windows", "reliability",
                  "methodology", "source_appendix"),
}

#: Yoga statuses, in the order the Yoga section groups them (Part 11).
YOGA_STATUS_ORDER = ("PRESENT_AND_STRONG", "PRESENT", "PRESENT_BUT_WEAK",
                     "CANCELLED", "ABSENT")

#: The birth-time precision enum, as an English reader would say it.
#:
#: V1.8 moved the real table into `strings.ENGLISH` so it can be
#: translated; this stays as a read-only English view because it is part
#: of this module's published surface and removing it would be a breaking
#: change for no benefit. Derived rather than duplicated, so the two can
#: never disagree.
PRECISION_LABELS = {
    key.split(".", 1)[1]: value
    for key, value in ENGLISH.items() if key.startswith("precision.")
}

_SHORT_STATUS = {
    key.rsplit(".", 1)[1]: value
    for key, value in ENGLISH.items() if key.startswith("yogas.status.")
}


def _status_label(S: ReportStrings, status: str) -> str:
    key = f"yogas.status.{status}"
    return S(key) if S.has(key) else status


def _precision_label(S: ReportStrings, code) -> str:
    """The birth-time precision, in the reader's language."""
    key = f"precision.{code}"
    if code and S.has(key):
        return S(key)
    return _text(code, S("birth.not_recorded"))


def _text(value, default: str = "—") -> str:
    """A cell value. Never None, never 'None'."""
    if value is None or value == "":
        return default
    return str(value)


def _degree(value) -> str:
    if value is None:
        return "—"
    degrees = int(value)
    minutes = int(round((float(value) - degrees) * 60))
    if minutes == 60:
        degrees, minutes = degrees + 1, 0
    return f"{degrees:02d}°{minutes:02d}'"


def _date(value, with_time: bool = False) -> str:
    if not value:
        return "—"
    try:
        moment = datetime.datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return moment.strftime("%d %b %Y %H:%M" if with_time else "%d %b %Y")


# ── sections ─────────────────────────────────────────────────────────────────

def _cover(S: ReportStrings, natal: dict, interpretation: Optional[dict],
           mode: str, language: str) -> Section:
    birth = natal.get("birth", {}) or {}
    location = birth.get("location") or {}
    name = birth.get("name") or S("cover.unknown_name")
    section = Section(id="cover", title="", starts_page=True)
    section.add(Heading(text=S("cover.title"), level=1))
    section.add(Paragraph(text=name, style="lead"))
    section.add(Paragraph(
        text=f"{_date(birth.get('datetime_local'), with_time=True)} "
             f"— {location.get('name') or S('birth.place_not_recorded')}",
        style="body"))
    section.add(Paragraph(
        text=S("cover.generated", mode=S(f"mode.{mode}"),
               date=datetime.date.today().isoformat()),
        style="small"))
    if interpretation:
        disclaimer = (interpretation.get("disclaimer") or {}).get("text")
        if disclaimer:
            section.add(Callout(text=disclaimer, kind="limit",
                                title=S("cover.what_this_is")))
    else:
        section.add(Callout(text=S("cover.disclaimer"), kind="limit",
                            title=S("cover.what_this_is")))
    return section


def _birth_details(S: ReportStrings, natal: dict) -> Section:
    birth = natal.get("birth", {}) or {}
    location = birth.get("location") or {}
    lagna = natal.get("lagna", {}) or {}
    pairs = [
        (S("birth.name"), _text(birth.get("name"))),
        (S("birth.datetime"),
         _date(birth.get("datetime_local"), with_time=True)),
        (S("birth.precision"), _precision_label(
            S, birth.get("time_precision"))),
        (S("birth.utc"), _date(birth.get("datetime_utc"), with_time=True)),
        (S("birth.place"), _text(location.get("name"))),
        (S("birth.coordinates"),
         f"{_text(location.get('latitude'))}, "
         f"{_text(location.get('longitude'))}"),
        (S("birth.timezone"), f"{_text(location.get('timezone_name'))} "
                     f"(UTC{location.get('utc_offset_hours', ''):+g})"
         if location.get("utc_offset_hours") is not None
         else _text(location.get("timezone_name"))),
        (S("birth.resolved_by"), _text(location.get("resolved_by"))),
        (S("birth.lagna"), f"{_text(lagna.get('sign'))} "
                           f"{_degree(lagna.get('degree_in_sign'))}"),
        (S("birth.lagna_nakshatra"), f"{_text(lagna.get('nakshatra'))}"
                                     f"{S('birth.pada')}"
                                     f"{_text(lagna.get('pada'))}"),
    ]
    section = Section(id="birth_details", title=S("birth.section"),
                      starts_page=True)
    notes = []
    if birth.get("time_precision_basis"):
        notes.append(S("birth.precision_prefix")
                     + birth["time_precision_basis"] + ".")
    section.add(KeyValues(pairs=tuple(pairs), notes=tuple(notes)))
    return section


def _executive_summary(S: ReportStrings, interpretation: Optional[dict],
                       prediction: Optional[dict]) -> Optional[Section]:
    if not interpretation:
        return None
    section = Section(id="executive_summary", title=S("summary.section"),
                      starts_page=False)

    summary = interpretation.get("birth_summary") or {}
    if summary.get("text"):
        section.add(Paragraph(text=summary["text"], style="lead"))
    for phrase in interpretation.get("methodology_summary") or []:
        if phrase.get("text"):
            section.add(Paragraph(text=phrase["text"], style="body"))

    # Which areas the engine found active, as a list rather than a ranking:
    # the activation levels are ordinal and ordering them by an invented
    # score would turn a band into a number (Part 17).
    active = [s for s in interpretation.get("domain_sections") or []
              if s.get("activation") in ("ACTIVE", "STRONGLY_ACTIVE", "MIXED")]
    if active:
        section.add(Bullets(
            caption=S("summary.activated"),
            items=tuple(
                f"{d.get('title', d.get('domain', ''))} — "
                f"{d.get('activation', '').replace('_', ' ').lower()}"
                f"{S('summary.confidence_join')}"
                f"{d.get('confidence', '').lower()}"
                for d in active)))
    else:
        section.add(Paragraph(text=S("summary.none_active"), style="body"))

    silent = [s for s in interpretation.get("domain_sections") or []
              if s.get("silence")]
    if silent:
        section.add(Paragraph(
            text=f"{len(silent)}{S('summary.silent')}", style="note"))
    return section


def _charts(S: ReportStrings, charts: Sequence, detail: str,
            legend: str = "", style_label: str = "") -> Optional[Section]:
    """
    One block per divisional chart, each with what produced it.

    The convention and the birth-time notes are printed WITH the chart, not
    collected into an appendix. A D60 whose Lagna moves inside the recorded
    precision is not a chart with a caveat somewhere else in the document;
    Part 10 asks for the warning to be visible where the chart is.
    """
    if not charts:
        return None
    section = Section(id="charts", title=S("charts.section"))
    for item in charts:
        scene = item["scene"]
        section.add(ChartBlock(
            scene=scene,
            caption=item.get("caption") or scene.title or item["name"],
            description=scene.description))
        if item.get("convention"):
            section.add(Paragraph(
                text=S("charts.computed_by",
                       convention=item["convention"]), style="small"))
        for note in item.get("notes") or []:
            section.add(Callout(text=note, kind="warning"))
    if legend:
        section.add(Paragraph(text=legend, style="small"))
    section.add(Paragraph(
        text=S("charts.style_note", style=style_label or "North Indian"),
        style="small"))
    return section


def _planets(S: ReportStrings, natal: dict) -> Optional[Section]:
    planets = natal.get("planets") or {}
    if not planets:
        return None
    vargas = ((natal.get("vargas") or {}).get("bodies") or {})
    strengths = ((natal.get("strengths") or {}).get("planets") or {})

    rows = []
    for name, entry in planets.items():
        varga = vargas.get(name, {})
        strength = strengths.get(name, {})
        ratio = strength.get("ratio")
        markers = []
        if entry.get("retrograde"):
            markers.append("R")
        if entry.get("combust"):
            markers.append("combust")
        rows.append((
            name,
            _text(entry.get("sign")),
            _degree(entry.get("degree_in_sign")),
            _text(entry.get("house")),
            _text(entry.get("nakshatra")),
            _text(entry.get("pada")),
            ", ".join(markers) or "—",
            _text(entry.get("dignity")),
            f"{ratio:.2f}" if isinstance(ratio, (int, float)) else "—",
            _text((varga.get("D9") or {}).get("sign")),
            _text((varga.get("D10") or {}).get("sign")),
        ))

    section = Section(id="planets", title=S("planets.section"))
    section.add(Table(
        columns=(S("planets.graha"), S("planets.sign"), S("planets.degree"),
                 S("planets.house"), S("planets.nakshatra"),
                 S("planets.pada"), S("planets.state"),
                 S("planets.dignity"), S("planets.shadbala"), "D9", "D10"),
        rows=tuple(rows),
        widths=(1.1, 1.2, 0.9, 0.7, 1.3, 0.55, 1.0, 1.35, 0.9, 1.1, 1.1),
        align=("left", "left", "right", "right", "left", "right", "left",
               "left", "right", "left", "left")))
    section.add(Paragraph(text=S("strength.note"), style="small"))
    return section


def _strengths(S: ReportStrings, natal: dict, mode: str) -> Optional[Section]:
    strengths = natal.get("strengths") or {}
    planets = strengths.get("planets") or {}
    if not planets:
        return None

    section = Section(id="strengths", title=S("strength.section"))
    rows = []
    for name, entry in planets.items():
        rows.append((
            name,
            f"{entry.get('total_rupa', 0):.2f}",
            f"{entry.get('required_rupa', 0):.2f}",
            f"{entry.get('ratio', 0):.2f}",
            S("strength.yes") if entry.get("meets_requirement") else "—",
        ))
    section.add(Table(
        columns=(S("planets.graha"), S("strength.total"),
                 S("strength.required"), S("strength.ratio"),
                 S("strength.meets")),
        rows=tuple(rows),
        widths=(1.2, 1.1, 1.1, 0.8, 1.1),
        align=("left", "right", "right", "right", "centre")))

    if mode == "technical":
        components = ("sthana_bala", "dig_bala", "kala_bala", "chesta_bala",
                      "naisargika_bala", "drik_bala")
        detail_rows = []
        for name, entry in planets.items():
            detail_rows.append((name,) + tuple(
                f"{(entry.get(c) or {}).get('value_rupa', 0):.2f}"
                for c in components))
        section.add(Table(
            caption=S("strength.components"),
            columns=(S("planets.graha"), S("strength.sthana"),
                     S("strength.dig"), S("strength.kala"),
                     S("strength.chesta"), S("strength.naisargika"),
                     S("strength.drik")),
            rows=tuple(detail_rows),
            widths=(1.2, 1, 1, 1, 1, 1.2, 1),
            align=("left",) + ("right",) * 6,
            compact=True))

    approximations = sorted(
        name for name, entry in planets.items()
        if entry.get("contains_approximation"))
    if approximations:
        section.add(Callout(
            kind="warning",
            title=S("strength.approximation_title"),
            text=S("strength.approximation",
                   planets=", ".join(approximations))))
    for warning in strengths.get("warnings") or []:
        section.add(Callout(text=warning, kind="warning"))
    return section


def _yogas(S: ReportStrings, natal: dict, mode: str) -> Optional[Section]:
    yogas = natal.get("yogas") or []
    present = [y for y in yogas if y.get("status") != "ABSENT"]
    if not present:
        return None

    section = Section(id="yogas", title=S("yogas.section"))
    by_status: dict[str, list] = {}
    for yoga in present:
        by_status.setdefault(yoga.get("status", "PRESENT"), []).append(yoga)

    counts = ", ".join(
        f"{len(by_status[status])} {_status_label(S, status).lower()}"
        for status in YOGA_STATUS_ORDER if status in by_status)
    section.add(Paragraph(
        text=S("yogas.counted", total=len(yogas), present=len(present),
               names=counts) + ".",
        style="body"))

    for status in YOGA_STATUS_ORDER:
        group = by_status.get(status)
        if not group:
            continue
        rows = []
        for yoga in group:
            rows.append((
                _text(yoga.get("name")),
                ", ".join(yoga.get("planets") or []) or "—",
                ", ".join(str(h) for h in yoga.get("houses") or [])
                or "—",
                _text(yoga.get("validation_status")),
            ))
        section.add(Table(
            caption=_status_label(S, status),
            columns=(S("yogas.yoga"), S("yogas.grahas"), S("yogas.houses"),
                     S("yogas.validation")),
            rows=tuple(rows),
            widths=(2.2, 1.4, 0.8, 1.6),
            align=("left", "left", "left", "left")))

    if mode in ("detailed", "technical"):
        for yoga in sorted(present, key=lambda y: y.get("name", "")):
            lines = []
            if yoga.get("explanation"):
                lines.append(yoga["explanation"])
            for condition in yoga.get("conditions_met") or []:
                lines.append(S("yogas.matched") + condition)
            for condition in yoga.get("cancellations_found") or []:
                lines.append(S("yogas.cancellation") + condition)
            if yoga.get("source"):
                lines.append(S("yogas.stated_at") + yoga["source"])
            if lines:
                section.add(Bullets(caption=_text(yoga.get("name")),
                                    items=tuple(lines)))

    section.add(Paragraph(text=S("yogas.note"), style="small"))
    return section


def _life_domains(S: ReportStrings, interpretation: Optional[dict],
                  mode: str) -> Optional[Section]:
    if not interpretation:
        return None
    sections = interpretation.get("domain_sections") or []
    if not sections:
        return None

    out = Section(id="life_domains", title=S("domains.section"))
    for domain in sections:
        out.add(Heading(text=_text(domain.get("title"), domain.get("domain")),
                        level=2))
        if domain.get("silence"):
            out.add(Paragraph(text=domain["silence"]["text"], style="note"))
            continue
        for field_name in ("overall", "confidence_statement",
                           "contradiction"):
            phrase = domain.get(field_name)
            if phrase and phrase.get("text"):
                out.add(Paragraph(
                    text=phrase["text"],
                    style="lead" if field_name == "overall" else "body"))
        if domain.get("safety"):
            out.add(Callout(text=domain["safety"]["text"], kind="limit"))
        # The interpretation layer lists the natal factors once as the
        # foundation and again, split by direction, as supporting and
        # challenging. Both are wanted when they differ. When the split
        # accounts for every natal sentence — which it usually does — the
        # foundation list repeats them verbatim a few centimetres higher,
        # and a reader takes the repetition for two separate findings.
        #
        # So the foundation is dropped when it is exactly the union of the
        # other two. That is deduplication of identical sentences, not a
        # judgement about evidence: nothing is removed that is not printed
        # in full elsewhere on the same page.
        split = {p.get("text") for key in ("supporting_factors",
                                           "challenging_factors")
                 for p in domain.get(key) or []}
        foundation = [p for p in domain.get("natal_foundation") or []
                      if p.get("text")]
        skip_foundation = bool(foundation) and all(
            p["text"] in split for p in foundation)

        for key, title in (
                ("natal_foundation", S("domains.natal_foundation")),
                ("supporting_factors", S("domains.supporting")),
                ("challenging_factors", S("domains.challenging")),
                ("dasha_activation", S("domains.dasha")),
                ("transit_triggers", S("domains.transit")),
                ("varga_confirmation", S("domains.varga")),
                ("timing", S("domains.timing"))):
            if key == "natal_foundation" and skip_foundation:
                continue
            items = domain.get(key) or []
            if not items:
                continue
            out.add(Bullets(caption=title,
                            items=tuple(p["text"] for p in items
                                        if p.get("text"))))
        for phrase in domain.get("reliability") or []:
            if phrase.get("text"):
                out.add(Callout(text=phrase["text"], kind="warning"))
    return out


def _dasha(S: ReportStrings, natal: dict, prediction: Optional[dict],
           mode: str) -> Optional[Section]:
    vimshottari = (natal.get("timing") or {}).get("vimshottari") or {}
    mahadashas = vimshottari.get("mahadashas") or []
    if not mahadashas:
        return None

    section = Section(id="dasha", title=S("dasha.section"))
    if prediction:
        stack = (prediction.get("dasha") or {}).get("stack") or {}
        pairs = tuple(
            (level.capitalize(), _text(stack.get(level)))
            for level in ("mahadasha", "antardasha", "pratyantardasha")
            if stack.get(level))
        if pairs:
            section.add(KeyValues(
                caption=S("dasha.running"), pairs=pairs))

    rows = [(
        _text(period.get("lord")),
        _date(period.get("start")),
        _date(period.get("end")),
        f"{(period.get('duration_days') or 0) / 365.25:.1f} y",
    ) for period in mahadashas]
    section.add(Table(
        caption=S("dasha.mahadashas",
                  convention=vimshottari.get("convention", "")),
        columns=(S("dasha.lord"), S("dasha.from"), S("windows.to"),
                 S("dasha.length")),
        rows=tuple(rows), widths=(1, 1.2, 1.2, 0.9),
        align=("left", "left", "left", "right")))

    if mode in ("detailed", "technical"):
        # Antardashas of the period covering the analysed moment only.
        # Printing all 81 sub-periods of nine mahadashas fills nine pages
        # and is not what a reader of a consultation report is looking for.
        current = _current_period(mahadashas, prediction)
        if current:
            rows = [(
                f"{current.get('lord')}–{child.get('lord')}",
                _date(child.get("start")), _date(child.get("end")),
                f"{(child.get('duration_days') or 0) / 30.44:.1f} m",
            ) for child in current.get("children") or []]
            if rows:
                section.add(Table(
                    caption=S("dasha.antardashas",
                              lord=current.get("lord")),
                    columns=(S("dasha.period"), S("dasha.from"),
                             S("windows.to"), S("dasha.length")),
                    rows=tuple(rows), widths=(1.4, 1.2, 1.2, 0.9),
                    align=("left", "left", "left", "right"), compact=True))
    return section


def _current_period(mahadashas, prediction) -> Optional[dict]:
    """The mahadasha holding the analysed moment, or the first one."""
    moment = (prediction or {}).get("datetime")
    if moment:
        for period in mahadashas:
            if (period.get("start") or "") <= moment <= (period.get("end")
                                                         or ""):
                return period
    return mahadashas[0] if mahadashas else None


def _transit_summary(S: ReportStrings,
                     prediction: Optional[dict]) -> Optional[Section]:
    if not prediction:
        return None
    transits = (prediction.get("transits") or {}).get("snapshot") or {}
    positions = transits.get("planetary_positions") or {}
    if not positions:
        return None

    section = Section(id="transit_summary", title=S("transits.section"))
    section.add(Paragraph(
        text=S("transits.positions",
               date=_date(prediction.get("datetime"), with_time=True)) + ".",
        style="body"))
    rows = []
    for name, entry in sorted(positions.items()):
        markers = []
        if entry.get("retrograde"):
            markers.append("R")
        if entry.get("stationary"):
            markers.append("stationary")
        rows.append((
            name,
            _text(entry.get("sign")),
            _degree(entry.get("degree_in_sign")),
            _text(entry.get("house_from_natal_lagna")),
            _text(entry.get("house_from_natal_moon")),
            _text(entry.get("nakshatra")),
            ", ".join(markers) or "—",
        ))
    section.add(Table(
        columns=(S("planets.graha"), S("planets.sign"), S("planets.degree"),
                 S("transits.house_from_lagna"),
                 S("transits.house_from_moon"), S("planets.nakshatra"),
                 S("planets.state")),
        rows=tuple(rows), widths=(1.1, 1.2, 0.9, 1.3, 1.4, 1.3, 1.0),
        align=("left", "left", "right", "right", "right", "left", "left")))

    relations = transits.get("transit_to_natal") or []
    if relations:
        section.add(Table(
            caption=S("transits.relationships"),
            columns=(S("transits.transiting"), S("transits.relationship"),
                     S("transits.natal_point"), S("transits.orb")),
            rows=tuple((
                _text(r.get("transiting_planet") or r.get("from")),
                _text(r.get("relationship") or r.get("type")).replace(
                    "_", " "),
                _text(r.get("natal_point") or r.get("to")),
                _text(r.get("orb_deg") or r.get("separation_deg")),
            ) for r in relations),
            widths=(1.2, 1.6, 1.4, 0.9),
            align=("left", "left", "left", "right"), compact=True))

    section.add(Paragraph(text=S("transits.note"), style="small"))
    return section


def _timing_windows(S: ReportStrings,
                    prediction: Optional[dict]) -> Optional[Section]:
    if not prediction:
        return None
    candidates = prediction.get("event_candidates") or []
    section = Section(id="timing_windows", title=S("windows.section"))
    if not candidates:
        section.add(Paragraph(text=S("windows.none"), style="body"))
        return section

    rows = []
    for item in candidates:
        window = item.get("window") or {}
        rows.append((
            _text(item.get("domain")),
            _text(item.get("event_type")).replace("_", " ").lower(),
            _date(window.get("window_start")),
            _date(window.get("peak")),
            _date(window.get("window_end")),
            _text(item.get("activation")).replace("_", " ").lower(),
            _text(item.get("confidence")).lower(),
        ))
    section.add(Table(
        columns=(S("windows.area"), S("windows.candidate"), S("dasha.from"),
                 S("windows.peak"), S("windows.to"), S("windows.activation"),
                 S("windows.confidence")),
        rows=tuple(rows), widths=(1.4, 1.5, 1.1, 1.1, 1.1, 1.3, 1.1),
        align=("left", "left", "left", "left", "left", "left", "left")))
    section.add(Callout(kind="limit", text=S("windows.note")))
    return section


def _reliability(S: ReportStrings, natal: dict, prediction: Optional[dict],
                 warnings: Sequence[str]) -> Section:
    section = Section(id="reliability", title=S("reliability.section"))
    birth = natal.get("birth", {}) or {}
    basis = birth.get("time_precision_basis")
    section.add(Paragraph(
        text=S("reliability.treated_as",
               precision=_precision_label(S, birth.get("time_precision"))
               if birth.get("time_precision") else S("reliability.unstated"))
             + (f" {basis}." if basis else ""),
        style="body"))

    sensitivity = natal.get("birth_time_sensitivity") or {}
    if not sensitivity:
        section.add(Callout(kind="warning",
                            text=S("reliability.not_calculated")))
    else:
        stable = sensitivity.get("largest_stable_window_minutes")
        section.add(Paragraph(
            text=(S("reliability.stable", minutes=stable) if stable
                  else S("reliability.unstable")),
            style="body"))
        unstable = []
        for window in sensitivity.get("windows") or []:
            for change in window.get("detail") or []:
                text = change.get("description")
                if text and text not in unstable:
                    unstable.append(text)
        if unstable:
            section.add(Bullets(caption=S("reliability.changes"),
                                items=tuple(unstable[:12])))

    accuracy = natal.get("accuracy") or {}
    boundary = accuracy.get("bodies_with_warnings") or []
    if boundary:
        section.add(Callout(
            kind="warning", title=S("reliability.boundaries"),
            text=S("reliability.boundary_text",
                   bodies=", ".join(boundary))))

    if prediction:
        for warning in (prediction.get("reliability") or {}).get(
                "warnings", []) or []:
            section.add(Callout(text=warning, kind="warning"))
    for warning in warnings:
        section.add(Callout(text=warning, kind="warning"))

    section.add(Callout(kind="limit", title=S("reliability.four_claims"),
                        text=S("reliability.four_claims_text")))
    return section


def _methodology(S: ReportStrings,
                 methodology: Optional[dict]) -> Optional[Section]:
    if not methodology:
        return None
    rows = methodology.get("rows") or []
    if not rows:
        return None
    section = Section(id="methodology", title=S("methodology.section"))
    section.add(Table(
        columns=(S("methodology.setting"), S("methodology.value"),
                 S("methodology.note")),
        rows=tuple((r["label"], _text(r["value"]), _text(r.get("note"), ""))
                   for r in rows),
        widths=(1.4, 1.6, 3.0),
        align=("left", "left", "left")))
    provenance = methodology.get("provenance") or {}
    if provenance:
        section.add(KeyValues(
            caption=S("methodology.registry"),
            pairs=tuple(
                (key.replace("_", " ").capitalize(), _text(value))
                for key, value in sorted(provenance.items())
                if not isinstance(value, (dict, list)))))
    return section


def _source_appendix(S: ReportStrings, natal: dict,
                     interpretation: Optional[dict]) -> Optional[Section]:
    """
    Rule and source references (Part 23).

    LOCATORS AND SUMMARIES ONLY. A citation, an edition, a chapter, a verse
    and a validation status — never the passage. The corpus is not
    redistributed here, and a reader who wants the text is given precisely
    what they need to find it in their own copy.
    """
    appendix = (interpretation or {}).get("technical_appendix") or {}
    sources = appendix.get("sources") or []
    rules = appendix.get("rules") or []
    if not sources and not rules:
        return None

    section = Section(id="source_appendix", title=S("sources.section"))
    section.add(Paragraph(text=S("sources.intro"), style="body"))
    resolved = [s for s in sources if s.get("resolved", True)]
    unresolved = [s for s in sources if not s.get("resolved", True)]
    if resolved:
        section.add(Table(
            caption=S("sources.witnesses"),
            columns=(S("sources.citation"), S("sources.work"),
                     S("sources.authority"), S("sources.edition")),
            rows=tuple((_text(s.get("citation")), _text(s.get("work")),
                        _text(s.get("authority")), _text(s.get("edition")))
                       for s in resolved),
            widths=(2.4, 1.6, 1.5, 2.0),
            align=("left", "left", "left", "left"), compact=True))
    if unresolved:
        # A reference the registry could not resolve is printed as such.
        # Dropping it would make the appendix look complete when it is not.
        section.add(Bullets(
            caption=S("sources.unresolved"),
            items=tuple(f"{_text(item.get('id'))} — "
                        f"{_text(item.get('note'), S('sources.no_witness'))}"
                        for item in unresolved)))
    if rules:
        section.add(Table(
            caption=S("sources.rules"),
            columns=(S("sources.rule"), S("sources.validation_status"),
                     S("sources.eligibility")),
            rows=tuple((_text(r.get("rule_id")),
                        _text(r.get("validation_status")),
                        _text(r.get("prediction_eligibility")))
                       for r in rules),
            widths=(2.4, 1.8, 1.8), align=("left", "left", "left"),
            compact=True))
    section.add(Callout(kind="limit", text=S("sources.note")))
    return section


# ── assembly ─────────────────────────────────────────────────────────────────

def build_report_document(natal: dict,
                          prediction: Optional[dict] = None,
                          interpretation: Optional[dict] = None,
                          charts: Sequence = (),
                          mode: str = "detailed",
                          language: str = "en",
                          methodology: Optional[dict] = None,
                          warnings: Sequence[str] = (),
                          chart_detail: str = "STANDARD",
                          chart_legend: str = "",
                          provenance: Optional[dict] = None,
                          generated: Optional[str] = None,
                          chart_style_label: str = "",
                          strings: Optional[ReportStrings] = None
                          ) -> ReportDocument:
    """
    Assemble the document for one report mode.

    `charts` is a sequence of dicts holding a rendered Scene and what
    produced it. `interpretation` is a serialised InterpretationDocument
    built at this same mode — not a different one, and not rephrased here.
    """
    if mode not in MODE_SECTIONS:
        raise ValueError(
            f"'{mode}' is not a report mode. Available: "
            f"{', '.join(sorted(MODE_SECTIONS))}.")
    wanted = MODE_SECTIONS[mode]
    S = strings or load_strings(language)

    birth = natal.get("birth", {}) or {}
    name = birth.get("name") or S("cover.unknown_name")
    document = ReportDocument(
        title=S("cover.document_title", name=name),
        subject=name,
        mode=mode,
        language=language,
        generated=generated or datetime.datetime.now().isoformat(
            timespec="seconds"),
        provenance=dict(provenance or {}))

    candidates = [
        ("cover", lambda: _cover(S, natal, interpretation, mode, language)),
        ("birth_details", lambda: _birth_details(S, natal)),
        ("executive_summary",
         lambda: _executive_summary(S, interpretation, prediction)),
        ("charts", lambda: _charts(S, charts, chart_detail, chart_legend,
                                   chart_style_label)),
        ("planets", lambda: _planets(S, natal)),
        ("strengths", lambda: _strengths(S, natal, mode)),
        ("yogas", lambda: _yogas(S, natal, mode)),
        ("life_domains", lambda: _life_domains(S, interpretation, mode)),
        ("dasha", lambda: _dasha(S, natal, prediction, mode)),
        ("transit_summary", lambda: _transit_summary(S, prediction)),
        ("timing_windows", lambda: _timing_windows(S, prediction)),
        ("reliability", lambda: _reliability(S, natal, prediction, warnings)),
        ("methodology", lambda: _methodology(S, methodology)),
        ("source_appendix",
         lambda: _source_appendix(S, natal, interpretation)),
    ]
    for name, build in candidates:
        if name not in wanted:
            continue
        section = build()
        if section is not None and not section.is_empty:
            document.add(section)
    return document
