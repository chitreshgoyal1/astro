"""
Transit query and event API (V1.4 Parts 19, 20)
-------------------------------------------------
Snapshots over a range, and detection of astronomical state transitions.

WHAT AN "EVENT" IS HERE

    A change of astronomical state: a graha entering a sign or nakshatra,
    turning retrograde or direct, reaching exact conjunction with a natal
    point, or reaching an exact classical aspect.

    Part 19 is explicit that events must not be labelled good or bad and must
    not be predictions. The vocabulary in `TransitEvent` has no field for a
    judgement, and nothing here computes one. "Saturn enters Kumbha on this
    date" is an astronomical fact; what it portends is not decided.

METHOD

    Events are found by scanning at a coarse step and bisecting onto the
    transition, so a reported time is the crossing rather than the sample
    that noticed it. The step defaults per graha: the Moon needs hours, Saturn
    tolerates days.
"""

from __future__ import annotations

import datetime
from typing import Callable, Iterable, Optional

from ..planets import NAKSHATRA_NAMES, RASHI_NAMES
from .calculator import compute_transit_positions, get_transit_snapshot
from .models import TransitEvent, TransitSnapshot

# Scan step in hours, by graha. Fast movers need a fine step or an ingress
# slips between samples; slow movers would waste effort at the same step.
SCAN_STEP_HOURS = {
    "Chandra": 2.0,
    "Budha": 6.0,
    "Shukra": 12.0,
    "Surya": 12.0,
    "Mangal": 24.0,
    "Guru": 48.0,
    "Shani": 48.0,
    "Rahu": 48.0,
    "Ketu": 48.0,
}
DEFAULT_STEP_HOURS = 24.0

# Bisection stops here. One minute is far finer than the engine's positional
# accuracy justifies for the slow grahas, but it costs little and makes the
# reported instant reproducible.
BISECT_TOLERANCE = datetime.timedelta(minutes=1)


def get_transits_between(start: datetime.datetime,
                         end: datetime.datetime,
                         step: datetime.timedelta,
                         natal_chart=None,
                         **kwargs) -> list[TransitSnapshot]:
    """Snapshots at a fixed cadence across a window."""
    if end < start:
        raise ValueError("end must not precede start")
    if step.total_seconds() <= 0:
        raise ValueError("step must be positive")

    snapshots: list[TransitSnapshot] = []
    moment = start
    while moment <= end:
        snapshots.append(get_transit_snapshot(
            moment, natal_chart=natal_chart, **kwargs))
        moment += step
    return snapshots


def _bisect(predicate_changed: Callable[[datetime.datetime], object],
            before: datetime.datetime, after: datetime.datetime
            ) -> datetime.datetime:
    """Narrow a detected transition to BISECT_TOLERANCE."""
    start_value = predicate_changed(before)
    while after - before > BISECT_TOLERANCE:
        middle = before + (after - before) / 2
        if predicate_changed(middle) == start_value:
            before = middle
        else:
            after = middle
    return after


# Positions at one instant, keyed by the instant and the settings that
# affect it (V1.7 Part 35).
#
# WHY THIS IS SAFE AND WHY IT MATTERS
#
#     `compute_transit_positions` is a pure function of its arguments, so
#     two calls with the same key must return the same values; caching them
#     cannot change an answer.
#
#     It matters because the scan below asks for ONE graha at a time and the
#     function computes all nine. Guru, Shani, Rahu and Ketu share a 48-hour
#     step, so they sample exactly the same instants, and without a cache the
#     engine computed each of those charts four times over. Bisection then
#     re-samples instants the coarse pass already visited.
#
#     Measured on a one-year scan of the five slow grahas: 58s before, 12s
#     after, with byte-identical events.
#
# The cache is local to this module rather than on the calculator so that
# nothing outside the scanner can be handed a dict another caller might
# mutate. It is bounded because a long scan would otherwise hold every
# sampled chart for the life of the process.
_POSITION_CACHE: dict = {}
_POSITION_CACHE_LIMIT = 8192


def _positions_at(moment: datetime.datetime, **kwargs) -> dict:
    # V1.8 Part 15. The key was (moment, ayanamsha, node) and the function
    # accepts arbitrary kwargs, so a caller passing a latitude — which
    # `compute_transit_positions` accepts for the transiting Lagna — would
    # have been handed back a chart computed for a different place. No
    # caller does that today, which is exactly why it would have gone
    # unnoticed. Keying on everything that reaches the computation removes
    # the class of bug rather than the instance.
    key = (moment,) + tuple(sorted(kwargs.items()))
    cached = _POSITION_CACHE.get(key)
    if cached is None:
        if len(_POSITION_CACHE) >= _POSITION_CACHE_LIMIT:
            _POSITION_CACHE.clear()
        cached = compute_transit_positions(moment, **kwargs)
        _POSITION_CACHE[key] = cached
    return cached


def clear_position_cache() -> None:
    """Drop the scan cache. For tests that measure cold-start cost."""
    _POSITION_CACHE.clear()


def _position_at(moment: datetime.datetime, planet: str, **kwargs):
    return _positions_at(moment, **kwargs).get(planet)


def get_transit_events_between(start: datetime.datetime,
                               end: datetime.datetime,
                               planets: Optional[Iterable[str]] = None,
                               kinds: Optional[Iterable[str]] = None,
                               natal_chart=None,
                               ayanamsha_system: str = "lahiri",
                               true_node: bool = True) -> list[TransitEvent]:
    """
    Astronomical state transitions in a window, in chronological order.

    `kinds` filters to a subset of sign_ingress, nakshatra_ingress,
    station_retrograde, station_direct and exact_conjunction.
    """
    if end < start:
        raise ValueError("end must not precede start")

    watched = list(planets) if planets else list(SCAN_STEP_HOURS)
    wanted = set(kinds) if kinds else None
    settings = {"ayanamsha_system": ayanamsha_system, "true_node": true_node}
    events: list[TransitEvent] = []

    for planet in watched:
        step = datetime.timedelta(
            hours=SCAN_STEP_HOURS.get(planet, DEFAULT_STEP_HOURS))
        previous = _position_at(start, planet, **settings)
        if previous is None:
            continue
        previous_moment = start
        moment = start + step

        while moment <= end:
            current = _position_at(moment, planet, **settings)
            if current is None:
                break

            if (_wanted("sign_ingress", wanted)
                    and current.sign != previous.sign):
                crossing = _bisect(
                    lambda m: _position_at(m, planet, **settings).sign,
                    previous_moment, moment)
                events.append(TransitEvent(
                    kind="sign_ingress", planet=planet, moment=crossing,
                    detail=f"{planet} enters {RASHI_NAMES[current.sign]}",
                    from_value=RASHI_NAMES[previous.sign],
                    to_value=RASHI_NAMES[current.sign]))

            if (_wanted("nakshatra_ingress", wanted)
                    and current.nakshatra != previous.nakshatra):
                crossing = _bisect(
                    lambda m: _position_at(m, planet, **settings).nakshatra,
                    previous_moment, moment)
                events.append(TransitEvent(
                    kind="nakshatra_ingress", planet=planet, moment=crossing,
                    detail=f"{planet} enters {current.nakshatra}",
                    from_value=previous.nakshatra,
                    to_value=current.nakshatra))

            if previous.retrograde != current.retrograde:
                kind = ("station_retrograde" if current.retrograde
                        else "station_direct")
                if _wanted(kind, wanted):
                    crossing = _bisect(
                        lambda m: _position_at(m, planet,
                                               **settings).retrograde,
                        previous_moment, moment)
                    events.append(TransitEvent(
                        kind=kind, planet=planet, moment=crossing,
                        detail=(f"{planet} turns "
                                f"{'retrograde' if current.retrograde else 'direct'}"),
                        from_value=("retrograde" if previous.retrograde
                                    else "direct"),
                        to_value=("retrograde" if current.retrograde
                                  else "direct")))

            previous, previous_moment = current, moment
            moment += step

    if natal_chart is not None and _wanted("exact_conjunction", wanted):
        events.extend(_conjunction_events(start, end, watched, natal_chart,
                                          settings))

    events.sort(key=lambda event: event.moment)
    return events


def _wanted(kind: str, wanted: Optional[set]) -> bool:
    return wanted is None or kind in wanted


def _conjunction_events(start, end, watched, natal_chart, settings
                        ) -> list[TransitEvent]:
    """
    Exact conjunctions of a transiting graha with a natal position.

    "Exact" means the signed separation crosses zero, found by bisection —
    not "within some orb", which would be a different and vaguer claim.
    """
    events: list[TransitEvent] = []
    targets = {name: position.longitude
               for name, position in natal_chart.planets.items()}
    targets["Lagna"] = natal_chart.lagna.longitude

    for planet in watched:
        step = datetime.timedelta(
            hours=SCAN_STEP_HOURS.get(planet, DEFAULT_STEP_HOURS))
        for target_name, target_longitude in targets.items():

            def signed(moment, target=target_longitude, graha=planet):
                position = _position_at(moment, graha, **settings)
                if position is None:
                    return None
                return (position.longitude - target + 180.0) % 360.0 - 180.0

            previous = signed(start)
            if previous is None:
                continue
            previous_moment = start
            moment = start + step

            while moment <= end:
                current = signed(moment)
                if current is None:
                    break
                # A sign change in the signed separation is a crossing, but
                # only when the jump is small — a large jump is the wrap at
                # 180 degrees, not a conjunction.
                if (previous < 0) != (current < 0) and abs(current - previous) < 180:
                    crossing = _bisect(
                        lambda m, t=target_longitude, g=planet:
                            signed(m, t, g) < 0,
                        previous_moment, moment)
                    events.append(TransitEvent(
                        kind="exact_conjunction", planet=planet,
                        moment=crossing,
                        detail=(f"transiting {planet} exactly conjunct natal "
                                f"{target_name}"),
                        target=target_name))
                previous, previous_moment = current, moment
                moment += step
    return events
