"""
Visual model builder (V1.7 Parts 6, 7, 8, 10)
===============================================
Snapshot in, ChartVisualModel out.

WHY THIS IS A SERVICE AND NOT PART OF THE RENDERER

    Building the model means answering one astrological question: which
    house does a body fall in, in a divisional chart. The D1 snapshot
    already says. For D2 to D60 it records the sign, and the house follows
    from the varga Lagna by whole-sign counting.

    That counting is `engine.features.varga_features.varga_house_of`, and it
    is called here rather than reimplemented three lines into a template.
    Two implementations of the same rule eventually disagree, and the one in
    the renderer would be the one nobody tests.

BIRTH-TIME NOTES (Part 10)

    A D60 Lagna that moves 39 seconds after the recorded time is not a
    precise value — it is not a value. When the sensitivity scan says a
    chart is unstable, the note travels ON the visual model, so the warning
    is drawn beside the chart rather than left in a panel the user may never
    open.
"""

from __future__ import annotations

from typing import Optional, Sequence

from engine.features.varga_features import varga_house_of

from ..visual.model import DETAIL_LEVELS, ChartVisualModel, HouseCell, PlacedBody

#: Two-letter labels for compact drawing. Sanskrit names are long and a
#: house holding five of them is unreadable at chart size.
SHORT_NAMES = {
    "Surya": "Su", "Chandra": "Ch", "Mangal": "Ma", "Budha": "Bu",
    "Guru": "Gu", "Shukra": "Sk", "Shani": "Sa", "Rahu": "Ra", "Ketu": "Ke",
    "Lagna": "La",
}

VARGA_TITLES = {
    "D1": "Rashi", "D2": "Hora", "D3": "Drekkana", "D4": "Chaturthamsha",
    "D7": "Saptamsha", "D9": "Navamsha", "D10": "Dashamsha",
    "D12": "Dwadashamsha", "D16": "Shodashamsha", "D20": "Vimshamsha",
    "D24": "Chaturvimshamsha", "D27": "Bhamsha", "D30": "Trimshamsha",
    "D40": "Khavedamsha", "D45": "Akshavedamsha", "D60": "Shashtiamsha",
}

RASHI_NAMES = ("Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
               "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena")


def _sign_name(index: int) -> str:
    return RASHI_NAMES[index % 12]


def _display(name: str, detail: str) -> str:
    if detail == "DETAILED":
        return name
    return SHORT_NAMES.get(name, name[:2])


def _sensitivity_notes(snapshot: dict, varga: str) -> list[str]:
    """
    Whether this particular chart survives the birth-time uncertainty.

    Reads the V1.4 scan as it was serialised. A chart not in
    `watched_vargas` gets the honest answer — unmeasured — rather than
    silence, because silence reads as stability.
    """
    section = snapshot.get("birth_time_sensitivity") or {}
    if not section:
        return ["Birth-time sensitivity was not calculated for this chart."]

    watched = section.get("watched_vargas") or []
    key = f"{varga.lower()}_lagna"
    notes: list[str] = []
    for window in section.get("windows", []) or []:
        for item in window.get("detail", []) or []:
            if (item.get("key") or "").lower() == key:
                notes.append(
                    f"The {varga} Lagna changes from {item.get('baseline')} "
                    f"to {item.get('changes_to')} {item.get('offset')} from "
                    f"the recorded birth time, which is inside the precision "
                    f"supplied.")
                break
        if notes:
            break

    if not notes and varga not in watched and varga != "D1":
        notes.append(
            f"{varga} was not covered by the birth-time sensitivity scan, so "
            f"its stability against the recorded time is unmeasured.")
    return notes


def _d1_bodies(snapshot: dict, detail: str) -> list[PlacedBody]:
    bodies = []
    for name, entry in sorted((snapshot.get("planets") or {}).items()):
        house = entry.get("house")
        if house is None:
            continue
        bodies.append(PlacedBody(
            name=name,
            display=_display(name, detail),
            house=int(house),
            sign_index=int(entry.get("sign_index", 0)),
            sign_name=entry.get("sign", ""),
            degree=entry.get("degree_in_sign"),
            retrograde=bool(entry.get("retrograde")),
            combust=bool(entry.get("combust")),
            dignity_marker=entry.get("dignity", "") or "",
            nakshatra=entry.get("nakshatra", "") or "",
            pada=entry.get("pada"),
        ))
    return bodies


def _varga_bodies(snapshot: dict, varga: str, lagna_sign: int, detail: str
                  ) -> list[PlacedBody]:
    bodies = []
    section = (snapshot.get("vargas") or {}).get("bodies") or {}
    for name, charts in sorted(section.items()):
        placement = charts.get(varga)
        if not placement:
            continue
        sign = int(placement.get("sign_index", 0))
        bodies.append(PlacedBody(
            name=name,
            display=_display(name, detail),
            house=varga_house_of(sign, lagna_sign),
            sign_index=sign,
            sign_name=placement.get("sign", _sign_name(sign)),
            # A varga placement has no degree: the division maps a range of
            # degrees onto a whole sign, so printing one would invent a
            # precision the calculation does not have.
            degree=None,
            retrograde=bool(
                ((snapshot.get("planets") or {}).get(name) or {})
                .get("retrograde")),
            dignity_marker=(placement.get("dignity") or "").replace("-", ""),
        ))
    return bodies


def build_visual_model(snapshot: dict,
                       varga: str = "D1",
                       detail: str = "STANDARD",
                       style: str = "north_indian",
                       include_lagna: bool = True,
                       notes: Optional[Sequence[str]] = None
                       ) -> ChartVisualModel:
    """
    Assemble the model for one divisional chart.

    Raises ValueError for an unknown varga or detail level rather than
    drawing something plausible — a chart labelled D9 that is not a D9 is
    worse than an error message.
    """
    varga = varga.upper()
    if detail not in DETAIL_LEVELS:
        raise ValueError(
            f"'{detail}' is not a chart detail level. "
            f"Available: {', '.join(DETAIL_LEVELS)}.")

    if varga == "D1":
        lagna = snapshot.get("lagna") or {}
        if not lagna:
            raise ValueError("This snapshot carries no Lagna, so no chart "
                             "can be drawn from it.")
        lagna_sign = int(lagna.get("sign_index", 0))
        lagna_name = lagna.get("sign") or _sign_name(lagna_sign)
        convention = "rashi"
        bodies = _d1_bodies(snapshot, detail)
    else:
        lagnas = (snapshot.get("vargas") or {}).get("lagna") or {}
        placement = lagnas.get(varga)
        if not placement:
            raise ValueError(
                f"This snapshot does not carry a {varga} chart. Available: "
                f"{', '.join(sorted(lagnas)) or 'none'}.")
        lagna_sign = int(placement.get("sign_index", 0))
        lagna_name = placement.get("sign") or _sign_name(lagna_sign)
        convention = placement.get("convention", "")
        bodies = _varga_bodies(snapshot, varga, lagna_sign, detail)

    if include_lagna:
        bodies.insert(0, PlacedBody(
            name="Lagna", display=_display("Lagna", detail), house=1,
            sign_index=lagna_sign, sign_name=lagna_name,
            degree=((snapshot.get("lagna") or {}).get("degree_in_sign")
                    if varga == "D1" else None),
            is_lagna=True))

    house_lords = {str(k): (v or {}).get("lord", "")
                   for k, v in (snapshot.get("houses") or {}).items()}
    cells = []
    for number in range(1, 13):
        sign = (lagna_sign + number - 1) % 12
        cells.append(HouseCell(
            number=number,
            sign_index=sign,
            sign_name=_sign_name(sign),
            lord=house_lords.get(str(number), "") if varga == "D1" else "",
            bodies=tuple(b for b in bodies if b.house == number),
        ))

    all_notes = list(notes or []) + _sensitivity_notes(snapshot, varga)
    title = f"{VARGA_TITLES.get(varga, varga)} ({varga})"
    subject = ((snapshot.get("birth") or {}).get("name") or "")

    return ChartVisualModel(
        chart_name=varga, title=title, lagna_sign=lagna_sign,
        lagna_sign_name=lagna_name, houses=tuple(cells), style=style,
        detail=detail, convention=convention, notes=tuple(all_notes),
        subject=subject)
