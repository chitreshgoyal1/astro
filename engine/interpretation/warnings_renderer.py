"""
Reliability and birth-time language (V1.6 Parts 18, 19)
---------------------------------------------------------
Renders what the engine knows about how far its own inputs can be trusted.

CONFIDENCE IS NOT PROBABILITY (Part 18)

    The four bands map to four sentences about the CALCULATION, not about
    the likelihood of anything. "The underlying calculations are stable for
    the birth data supplied" is a statement about arithmetic and inputs. "An
    80% chance" would be a statement about the world, and this engine has
    never been tested against the world.

WHY THE WARNINGS ARE NOT OPTIONAL (Part 19)

    V1.4 measured that the regression chart's D60 lagna changes 39 seconds
    after the stated birth time, and the stated time came from a field
    reading HH:MM. A reader shown a D60-derived conclusion without that fact
    is being shown a precise-looking statement about something the input
    does not determine.

    So a conclusion resting on an unstable varga carries the warning in the
    domain section, beside the conclusion, not only in a preamble the reader
    may have skipped.
"""

from __future__ import annotations

from typing import Optional

from . import grammar as G
from . import keys as K
from .models import RenderedPhrase

# Which reliability flags correspond to which divisional chart, so a warning
# can name the chart a conclusion actually rests on.
_CHART_FLAGS = (
    ("D60", "d60_lagna_stable"),
    ("D10", "d10_lagna_stable"),
    ("D9", "d9_lagna_stable"),
)


def render_confidence(level: str, templates, domain: Optional[str] = None
                      ) -> RenderedPhrase:
    """One of four bands, as a statement about the calculation."""
    key = K.confidence_key(level)
    return RenderedPhrase(
        key=key,
        text=G.sentence(templates.render(key, domain=domain),
                        templates.grammar),
        args={})


def render_document_warnings(reliability: dict, templates
                             ) -> list[RenderedPhrase]:
    """Reliability facts that apply to the whole document."""
    phrases: list[RenderedPhrase] = []

    seconds = reliability.get("birth_time_precision_seconds")
    if seconds is not None:
        key = "reliability.birth_time_precision"
        args = {"seconds": seconds}
        phrases.append(RenderedPhrase(
            key=key,
            text=G.sentence(templates.render(key, **args), templates.grammar),
            args=args))

    if not reliability.get("sensitivity_available", False):
        key = "reliability.sensitivity_not_computed"
        phrases.append(RenderedPhrase(
            key=key, text=G.sentence(templates.render(key), templates.grammar),
            args={}))
        return phrases

    # The Lagna first: if the rising sign itself is unresolved then every
    # house in the document moves, and that outranks any varga warning.
    if not reliability.get("lagna_stable", True):
        key = "reliability.lagna_unstable"
        phrases.append(RenderedPhrase(
            key=key, text=G.sentence(templates.render(key), templates.grammar),
            args={}))

    for chart, flag in _CHART_FLAGS:
        if reliability.get(flag, True):
            continue
        key = "reliability.varga_unstable"
        args = {"chart": chart}
        phrases.append(RenderedPhrase(
            key=key,
            text=G.sentence(templates.render(key, **args), templates.grammar),
            args=args))

    return phrases


def unstable_charts(reliability: dict) -> list[str]:
    """Divisional charts the birth time does not resolve."""
    if not reliability.get("sensitivity_available", False):
        return []
    return [chart for chart, flag in _CHART_FLAGS
            if not reliability.get(flag, True)]


def render_domain_warnings(result: dict, reliability: dict, templates,
                           domain: Optional[str] = None
                           ) -> list[RenderedPhrase]:
    """
    Warnings that belong beside one domain's conclusion.

    Only charts this domain actually used are named. A D60 instability is
    not a reason to caveat a conclusion that never consulted D60, and
    attaching every warning everywhere would train a reader to skip them.
    """
    phrases: list[RenderedPhrase] = []
    unstable = set(unstable_charts(reliability))
    if not unstable:
        return phrases

    used = {v.get("chart") for v in result.get("varga_evidence", [])}
    for chart in sorted(unstable & used):
        key = "reliability.depends_on_unstable_varga"
        args = {"chart": chart}
        phrases.append(RenderedPhrase(
            key=key,
            text=G.sentence(templates.render(key, domain=domain, **args),
                        templates.grammar),
            args=args))
    return phrases


def render_boundary_warnings(result: dict, templates,
                             domain: Optional[str] = None
                             ) -> list[RenderedPhrase]:
    """
    Astronomical boundary warnings carried on the synthesis result.

    Distinct from birth-time instability: a graha at a sign boundary is
    uncertain because the EPHEMERIS does not resolve it, not because the
    clock time is vague. Two different uncertainties, two different
    sentences.
    """
    phrases: list[RenderedPhrase] = []
    for warning in result.get("reliability_warnings", []):
        if "unresolved astronomical boundary" not in warning:
            continue
        planet = warning.split(" is ", 1)[0].strip()
        key = "reliability.boundary_unresolved"
        args = {"planet": templates.planet(planet)}
        phrases.append(RenderedPhrase(
            key=key,
            text=G.sentence(templates.render(key, domain=domain, **args),
                        templates.grammar),
            args=args))
    return phrases
