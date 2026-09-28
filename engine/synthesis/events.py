"""
Event candidates and timing windows (V1.5 Parts 18, 19, 24)
-------------------------------------------------------------
Structured candidates only. No prose, no prediction, no date invented.

WHERE A WINDOW COMES FROM

    Part 19 asks for real boundaries, and every boundary here is one of four
    computed things:

        a dasha period edge      exact Fraction arithmetic, V1.2
        a sign ingress           bisected to the second, V1.4
        a station                bisected, V1.4
        an exact aspect or       bisected, V1.4
        conjunction

    Nothing is rounded to a month, nothing is nudged to a nicer date, and
    nothing is emitted when no boundary is available. A candidate with no
    computable window is not produced at all rather than given a plausible
    one — an invented date is the most quotable thing this engine could
    possibly print, and it would be fiction.

WHY CANDIDATES AND NOT EVENTS

    An EventCandidate says: within this window, this engine's rules place an
    activation of this domain, at this level, on this evidence. It does not
    say the event happens. The distinction is carried in the type name, in
    the `is_candidate_not_prediction` field on every serialised record, and
    in the absence of any verb anywhere in this module.

PART 24

    No event type in this module concerns death, diagnosis, disease or
    pregnancy. HEALTH_ACTIVITY exists and is capped at domain-level
    activation; `_EVENT_TYPES` has no entry for LONGEVITY at all, because a
    longevity "event candidate" with a window is a death prediction however
    it is labelled. The longevity DOMAIN is still computed and reported — a
    reader can see the factors — and it never becomes an event.
"""

from __future__ import annotations

import datetime
from typing import Optional, Sequence

from .domains import Domain, spec_for
from .models import (
    ActivationLevel, EventCandidate, EventType, EvidenceConfidence,
    EvidenceLayer, SynthesisProfile, TimingWindow,
)

EVENTS_METHODOLOGY_ID = "event_candidates_v15"

# Which event type a domain's activation is recorded as.
#
# LONGEVITY is deliberately absent — see the module docstring. HEALTH maps to
# HEALTH_ACTIVITY, which is an activation label and not a medical statement.
_EVENT_TYPES: dict[Domain, tuple[EventType, ...]] = {
    Domain.CAREER: (EventType.CAREER_ADVANCEMENT, EventType.CAREER_CHANGE),
    Domain.FINANCE: (EventType.FINANCIAL_GAIN, EventType.FINANCIAL_PRESSURE),
    Domain.WEALTH: (EventType.FINANCIAL_GAIN,),
    Domain.MARRIAGE: (EventType.RELATIONSHIP_ACTIVATION,),
    Domain.RELATIONSHIPS: (EventType.RELATIONSHIP_ACTIVATION,),
    Domain.CHILDREN: (EventType.CHILDREN_ACTIVATION,),
    Domain.EDUCATION: (EventType.EDUCATION_ACTIVITY,),
    Domain.PROPERTY: (EventType.PROPERTY_ACTIVITY,),
    Domain.HEALTH: (EventType.HEALTH_ACTIVITY,),
    Domain.FAMILY: (EventType.FAMILY_ACTIVITY,),
    Domain.SIBLINGS: (EventType.SIBLING_ACTIVITY,),
    Domain.TRAVEL: (EventType.TRAVEL_ACTIVITY,),
    Domain.FOREIGN_RESIDENCE: (EventType.FOREIGN_RESIDENCE_ACTIVITY,),
    Domain.SPIRITUALITY: (EventType.SPIRITUAL_ACTIVITY,),
    Domain.BUSINESS: (EventType.BUSINESS_ACTIVITY,),
    Domain.LITIGATION: (EventType.LITIGATION_ACTIVITY,),
}

# Domains that never produce an event candidate, whatever their activation.
NO_EVENT_DOMAINS = (Domain.LONGEVITY,)

# The minimum activation that produces a candidate. BACKGROUND means the
# chart indicates something and nothing currently activates it, which is not
# an event in any window.
MINIMUM_ACTIVATION = (ActivationLevel.ACTIVE, ActivationLevel.STRONGLY_ACTIVE,
                      ActivationLevel.MIXED)


def _event_types_for(domain: Domain, result) -> tuple[EventType, ...]:
    """
    Which candidate types this domain's evidence supports.

    Part 18: "do not expand into extreme specific claims without explicit
    rule support". So a domain with a supportive-only balance does not
    produce its pressure/change variant, and one with challenging evidence
    does not produce its gain variant. Where the evidence is mixed, both are
    produced, because that is what mixed evidence means.
    """
    types = _EVENT_TYPES.get(domain, ())
    if len(types) < 2:
        return types
    if result.mixed:
        return types
    if result.challenging and not result.supportive:
        return types[1:]
    return types[:1]


# ── Part 19: windows from real boundaries ────────────────────────────────────

def dasha_window(dasha, moment: datetime.datetime,
                 level: str = "antardasha") -> Optional[TimingWindow]:
    """
    The running dasha period at `level`, as a window.

    The boundaries are exact: V1.2 computes them with Fraction arithmetic
    from the Moon's longitude, so they are as precise as the Moon's longitude
    and carry no rounding of their own.
    """
    if dasha is None:
        return None
    period = dasha.get_period_at(moment, level=level)
    if period is None:
        return None
    return TimingWindow(
        start=period.start, end=period.end,
        why=(f"{level} of {period.lord}"
             f" ({period.start.date()} to {period.end.date()})",),
        boundary_sources=("vimshottari_period_boundary",))


def _narrow_to_transits(window: TimingWindow, events: Sequence,
                        planets: Sequence[str],
                        moment: datetime.datetime) -> TimingWindow:
    """
    Tighten a dasha window around `moment`, using transit events inside it.

    A dasha antardasha can run for years; the transit events of the
    participating grahas are what give a window edges anyone could act on.

    THE WINDOW MUST STILL CONTAIN THE QUERIED MOMENT. That is the invariant
    that makes narrowing meaningful: the question asked was "what is
    activated now", so the answer is the current sub-period, bounded by the
    last boundary at or before now and the first one after it. Narrowing to
    the first event pair in the period instead — which an earlier version of
    this function did — produces a window that closed months before the date
    the user asked about, and reads as a confident claim about the wrong
    time. A test pins the invariant.
    """
    relevant = [e for e in events
                if window.contains(e.moment) and e.planet in planets]
    if not relevant:
        return window

    boundary_kinds = ("sign_ingress", "station_retrograde", "station_direct")
    ingresses = [e for e in relevant if e.kind in boundary_kinds]
    exacts = [e for e in relevant
              if e.kind in ("exact_conjunction", "exact_aspect")]

    start, end = window.start, window.end
    why = list(window.why)
    sources = list(window.boundary_sources)

    before = [e for e in ingresses if e.moment <= moment]
    after = [e for e in ingresses if e.moment > moment]
    if before:
        latest = max(before, key=lambda e: e.moment)
        start = max(start, latest.moment)
        why.append(f"opens at {latest.detail}")
        sources.append("transit_ingress")
    if after:
        earliest = min(after, key=lambda e: e.moment)
        end = min(end, earliest.moment)
        why.append(f"closes at {earliest.detail}")
        sources.append("transit_ingress")

    if start >= end:
        return window

    # The peak is the exact hit nearest the queried moment that falls inside
    # the narrowed window. An exact conjunction is bisected to the second, so
    # it is a computed instant rather than an estimate — but one outside the
    # window is not this window's peak.
    inside = [e for e in exacts if start <= e.moment <= end]
    peak = None
    if inside:
        nearest = min(inside, key=lambda e: abs(e.moment - moment))
        peak = nearest.moment
        why.append(f"peak at {nearest.detail}")
        sources.append("exact_transit_aspect")

    return TimingWindow(start=start, end=end, peak=peak,
                        why=tuple(why), boundary_sources=tuple(sources))


# ── Part 18: the candidates ──────────────────────────────────────────────────

def event_candidates(context, dasha=None, transit_events: Sequence = (),
                     level: str = "antardasha") -> list[EventCandidate]:
    """
    Structured candidates for every sufficiently activated domain.

    Produces nothing when no window can be computed. A candidate whose
    window this engine cannot derive from a dasha boundary or a transit event
    is not a candidate with a vague window — it is not a candidate.
    """
    out: list[EventCandidate] = []
    base_window = dasha_window(dasha, context.moment, level=level)
    if base_window is None:
        return out

    for name, result in sorted(context.results.items()):
        domain = Domain(name)
        if domain in NO_EVENT_DOMAINS:
            continue
        if result.activation not in MINIMUM_ACTIVATION:
            continue

        spec = spec_for(domain)
        planets = sorted({p for e in result.all_evidence for p in e.planets})
        window = _narrow_to_transits(base_window, transit_events, planets,
                                     context.moment)

        warnings = list(result.reliability_warnings)
        if result.confidence in (EvidenceConfidence.LOW,
                                 EvidenceConfidence.UNRESOLVED):
            warnings.append(
                f"Confidence is {result.confidence.value}. The window is "
                f"computed exactly; what it is a window FOR rests on "
                f"evidence this engine does not consider firm.")
        if spec.is_high_stakes:
            warnings.append(spec.to_dict()["output_constraint"])

        for event_type in _event_types_for(domain, result):
            out.append(EventCandidate(
                domain=name, event_type=event_type, window=window,
                activation=result.activation, confidence=result.confidence,
                profile=context.profile,
                evidence=list(result.all_evidence),
                reliability_warnings=sorted(set(warnings)),
                source_ref_ids=result.source_ref_ids,
                rule_ids=result.rule_ids,
                methodology_ids=(EVENTS_METHODOLOGY_ID,
                                 "vimshottari_activation_v15"),
                notes=(
                    "A window in which this engine's rules place an "
                    "activation of this domain. Not a statement that "
                    "anything happens.")))
    return out


def candidates_for_domain(candidates: Sequence[EventCandidate],
                          domain) -> list[EventCandidate]:
    name = spec_for(domain).domain.value
    return [c for c in candidates if c.domain == name]
