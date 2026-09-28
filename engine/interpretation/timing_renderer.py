"""
Timing language (V1.6 Parts 17, 21)
-------------------------------------
Renders the windows the synthesis engine computed, and nothing else.

TWO RULES, BOTH NEGATIVE

    Do not invent a date. Every boundary rendered here came from a dasha
    period edge, a transit ingress, a station or a bisected exact aspect.
    Where the engine produced no window, `timing.no_window` says so rather
    than offering a season.

    Do not invent a peak. `timing.window_with_peak` is used ONLY when
    `window.peak` is present, because "the strongest trigger is around X" is
    a claim the engine either made or did not. A renderer that filled in the
    midpoint would be manufacturing the most quotable sentence in the
    document.

PART 21: NO FALSE SPECIFICITY

    A CAREER_CHANGE candidate renders as a career-change CANDIDATE in a
    window. It does not become "you will change jobs", and the event-type
    vocabulary is passed through rather than paraphrased, so a reader sees
    the engine's own category.

    Dates are rendered to month and year. The engine computes boundaries to
    the second by bisection; printing that would imply a precision about the
    EVENT that the arithmetic only has about the sky.
"""

from __future__ import annotations

from typing import Optional

from . import grammar as G
from .models import RenderedPhrase


def render_window(window: dict, templates, domain: Optional[str] = None
                  ) -> RenderedPhrase:
    """One timing window as a sentence."""
    months = templates.month_names()
    start = G.format_date(window.get("window_start"), months)
    end = G.format_date(window.get("window_end"), months)
    peak = window.get("window_peak")

    if peak:
        key = "timing.window_with_peak"
        args = {"start": start, "end": end,
                "peak": G.format_date(peak, months)}
    else:
        key = "timing.window_without_peak"
        args = {"start": start, "end": end}

    return RenderedPhrase(
        key=key,
        text=G.sentence(templates.render(key, domain=domain, **args),
                        templates.grammar),
        args=args)


def render_no_window(templates, domain: Optional[str] = None
                     ) -> RenderedPhrase:
    key = "timing.no_window"
    return RenderedPhrase(
        key=key, text=G.sentence(templates.render(key, domain=domain),
                                 templates.grammar),
        args={})


def render_event_candidate(candidate: dict, templates,
                           domain: Optional[str] = None) -> RenderedPhrase:
    """
    One EventCandidate, at the specificity the candidate itself carries.

    The event type is passed through in the engine's own words — a
    CAREER_CHANGE stays a career change and does not become a promotion.
    """
    key = "timing.event_candidate"
    args = {
        "event_type": candidate["event_type"].replace("_", " ").lower(),
        "activation": candidate["activation"].replace("_", " ").lower(),
    }
    return RenderedPhrase(
        key=key,
        text=G.sentence(templates.render(key, domain=domain, **args),
                        templates.grammar),
        args=args)


def render_dasha_stack(stack: dict, templates) -> Optional[RenderedPhrase]:
    """The running periods. Returns None when no dasha was computed."""
    if not stack:
        return None
    maha = stack.get("mahadasha")
    antara = stack.get("antardasha")
    pratya = stack.get("pratyantardasha")
    if not (maha and antara and pratya):
        return None
    key = "timing.dasha_stack"
    args = {"mahadasha": templates.planet(maha),
            "antardasha": templates.planet(antara),
            "pratyantardasha": templates.planet(pratya)}
    return RenderedPhrase(
        key=key,
        text=G.sentence(templates.render(key, **args), templates.grammar),
        args=args)


def render_domain_timing(domain: str, candidates: list, templates
                         ) -> list[RenderedPhrase]:
    """
    Timing phrases for one domain.

    Candidates are already filtered and ordered by the synthesis layer; this
    preserves that order rather than sorting, so the document reflects the
    engine's own ranking.
    """
    mine = [c for c in candidates if c.get("domain") == domain]
    if not mine:
        return []

    phrases: list[RenderedPhrase] = []
    seen_windows = set()
    for candidate in mine:
        window = candidate.get("window") or {}
        signature = (window.get("window_start"), window.get("window_end"),
                     window.get("window_peak"))
        if signature not in seen_windows:
            seen_windows.add(signature)
            phrases.append(render_window(window, templates, domain))
        phrases.append(render_event_candidate(candidate, templates, domain))
    return phrases
