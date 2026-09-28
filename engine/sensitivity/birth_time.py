"""
Birth-time sensitivity (V1.4 Part 16)
---------------------------------------
Given a birth time, recompute the chart at nearby times and report which
classifications change and when.

WHY THIS EXISTS

    The engine already reports NUMERICAL uncertainty — how far a graha sits
    from a boundary relative to the ephemeris's own error. That is a
    statement about the arithmetic.

    This module reports a different and usually larger uncertainty: how far
    the CLASSIFICATIONS sit from a boundary relative to the error in the
    stated birth time. The Lagna moves about a degree every four minutes, so
    a birth time recorded to the nearest five minutes leaves the D60 Lagna
    essentially undetermined and can move the Lagna's pada.

    A reading that depends on something this module reports as unstable is
    resting on the clock, not on the sky.

WHAT THIS IS NOT

    Not rectification. The module never suggests a "better" birth time and
    never scores candidates. It reports what changes within a window and
    stops. Part 16 is explicit, and rectification is a different activity
    with different evidential standards.
"""

from __future__ import annotations

import datetime
from typing import Callable, Optional

from ..planets import JyotishChart, jde_from_datetime
from ..vargas import VargaConfig
from .models import SensitivityReport, SensitivityWindow, UnstableItem

# Windows tested by default, in minutes either side of the stated time.
DEFAULT_WINDOWS = (1, 2, 5, 10)

# Resolution of the scan. One second is finer than any birth time is ever
# recorded to, so a boundary found here is a real crossing rather than an
# artefact of sampling.
SCAN_STEP_SECONDS = 15
REFINE_STEP_SECONDS = 1

# The divisional Lagnas worth watching. D60 changes every 30 seconds of
# clock time and is the usual reason a chart is unstable.
WATCHED_VARGAS = ("D1", "D9", "D10", "D30", "D60")


def _signature(chart: JyotishChart, config: VargaConfig,
               bhava_system: Optional[str]) -> dict:
    """
    The classifications worth watching, as a comparable snapshot.

    Deliberately narrow: things that change with the CLOCK. Planetary signs
    barely move in ten minutes and are not included, except through their
    bhava, which can.
    """
    lagna = chart.lagna
    values = {
        "lagna_sign": lagna.rashi,
        "lagna_nakshatra": lagna.nakshatra,
        "lagna_pada": lagna.pada,
    }
    for varga in WATCHED_VARGAS:
        values[f"{varga}_lagna"] = config.compute(
            varga, lagna.longitude).rashi

    if bhava_system and bhava_system != "whole_sign":
        from ..houses import build_bhava_chart
        bhava = build_bhava_chart(chart, bhava_system)
        for name, placement in bhava.placements.items():
            values[f"bhava_{name}"] = placement.bhava_house
    else:
        lagna_sign = lagna.rashi_index
        for name, position in chart.planets.items():
            values[f"house_{name}"] = (
                ((position.rashi_index - lagna_sign) % 12) + 1)

    return values


_LABELS = {
    "lagna_sign": "Lagna sign",
    "lagna_nakshatra": "Lagna nakshatra",
    "lagna_pada": "Lagna pada",
}


def _label(key: str) -> str:
    if key in _LABELS:
        return _LABELS[key]
    if key.endswith("_lagna"):
        return f"{key[:-6]} Lagna"
    if key.startswith("bhava_"):
        return f"{key[6:]} bhava"
    if key.startswith("house_"):
        return f"{key[6:]} house"
    return key


def _offset_text(seconds: int) -> str:
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    return f"{sign}{seconds // 60}m {seconds % 60:02d}s"


def analyse_birth_time(birth_utc: datetime.datetime,
                       latitude: float, longitude: float,
                       windows=DEFAULT_WINDOWS,
                       ayanamsha_system: str = "lahiri",
                       true_node: bool = True,
                       varga_config: Optional[VargaConfig] = None,
                       bhava_system: Optional[str] = None,
                       rule_check: Optional[Callable] = None
                       ) -> SensitivityReport:
    """
    Which classifications change within each window, and at what offset.

    The scan walks outward from the stated time in 15-second steps, and
    bisects to the second once a change is detected — so the reported offset
    is where the crossing actually is, not where the sampling happened to
    notice it.
    """
    config = varga_config or VargaConfig()

    def chart_at(offset_seconds: int) -> JyotishChart:
        moment = birth_utc + datetime.timedelta(seconds=offset_seconds)
        return JyotishChart(jde=jde_from_datetime(moment),
                            lat=latitude, lon=longitude,
                            ayanamsha_system=ayanamsha_system,
                            true_node=true_node)

    def signature_at(offset_seconds: int) -> dict:
        return _signature(chart_at(offset_seconds), config, bhava_system)

    baseline = signature_at(0)
    baseline_rules = rule_check(chart_at(0)) if rule_check else None

    largest = max(windows)
    limit = largest * 60

    # Walk outward in both directions, recording the first offset at which
    # each key departs from its baseline value.
    first_change: dict[str, tuple[int, object]] = {}
    for direction in (1, -1):
        previous = baseline
        previous_offset = 0
        offset = direction * SCAN_STEP_SECONDS
        while abs(offset) <= limit:
            current = signature_at(offset)
            for key, value in current.items():
                if value == baseline[key] or key in first_change:
                    continue
                crossing = _bisect(signature_at, key, baseline[key],
                                   previous_offset, offset)
                first_change[key] = (crossing, value)
            previous, previous_offset = current, offset
            offset += direction * SCAN_STEP_SECONDS

    rule_changes: list[UnstableItem] = []
    if rule_check is not None and baseline_rules is not None:
        rule_changes = _scan_rules(chart_at, rule_check, baseline_rules, limit)

    result_windows: list[SensitivityWindow] = []
    for minutes in sorted(windows):
        bound = minutes * 60
        items = [
            UnstableItem(
                item=_label(key),
                key=key,
                baseline=baseline[key],
                changes_to=new_value,
                offset_seconds=offset,
                offset_text=_offset_text(offset),
            )
            for key, (offset, new_value) in sorted(
                first_change.items(), key=lambda kv: abs(kv[1][0]))
            if abs(offset) <= bound
        ]
        items.extend(item for item in rule_changes
                     if abs(item.offset_seconds) <= bound)
        result_windows.append(SensitivityWindow(
            window_minutes=minutes,
            stable=not items,
            changes=items,
        ))

    return SensitivityReport(
        birth_utc=birth_utc,
        latitude=latitude,
        longitude=longitude,
        scan_step_seconds=SCAN_STEP_SECONDS,
        watched_vargas=list(WATCHED_VARGAS),
        bhava_system=bhava_system,
        windows=result_windows,
        baseline=baseline,
    )


def _bisect(signature_at: Callable, key: str, baseline_value,
            stable_offset: int, changed_offset: int) -> int:
    """Narrow a detected change to the nearest second."""
    low, high = stable_offset, changed_offset
    while abs(high - low) > REFINE_STEP_SECONDS:
        middle = (low + high) // 2
        if signature_at(middle)[key] == baseline_value:
            low = middle
        else:
            high = middle
    return high


def _scan_rules(chart_at: Callable, rule_check: Callable,
                baseline: object, limit: int) -> list[UnstableItem]:
    """
    Whether a supplied rule summary changes within the window.

    `rule_check` is any callable taking a chart and returning something
    comparable — typically the set of yoga ids present. Kept generic so the
    caller decides what counts as an "important rule outcome" rather than
    this module deciding for them.
    """
    changes: list[UnstableItem] = []
    for direction in (1, -1):
        offset = direction * 60
        while abs(offset) <= limit:
            current = rule_check(chart_at(offset))
            if current != baseline:
                added = set(current) - set(baseline)
                removed = set(baseline) - set(current)
                detail = ", ".join(
                    [f"+{name}" for name in sorted(added)]
                    + [f"-{name}" for name in sorted(removed)])
                changes.append(UnstableItem(
                    item="rule outcome",
                    key="rules",
                    baseline=f"{len(baseline)} present",
                    changes_to=detail or f"{len(current)} present",
                    offset_seconds=offset,
                    offset_text=_offset_text(offset),
                ))
                break
            offset += direction * 60
    return changes
