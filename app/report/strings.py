"""
Report chrome strings (V1.8 Parts 22, 25)
-------------------------------------------
The words the report itself contributes, in every supported language.

THE GAP THIS CLOSES

    V1.7 reported Hindi localisation as complete, and for what it
    measured it was: the engine's 78 interpretation keys were translated
    and a test asserted no English sentence survived into a Hindi
    document. What nobody measured was the REPORT'S OWN chrome — the
    section headings, the table column labels, the cover text, the
    callout titles. Those are written by `app/report/builder.py`, which
    is below the boundary and therefore outside the engine's template
    system entirely.

    The result was a Hindi PDF whose findings were in Hindi and whose
    headings said "Birth details", "Planetary positions", "Reliability
    and limits". Half a translation reads worse than none, because the
    reader cannot tell which half they are getting.

    This module is the other half. It was found by building the Hindi
    PDF and looking at it — 1,232 English strings in a document that
    claimed to be Hindi — which is a reminder that a completeness test
    measures the thing it was pointed at.

WHERE THE TRANSLATIONS LIVE

    `templates/<language>/report.json`, beside the engine's own locale
    files, because V1.7 Part 25 forbids scattering translation
    dictionaries and one directory per language is the whole point.

    Reading a JSON file is not importing the engine, so the boundary
    holds: `app/report` still has no `engine` import and the AST test
    still passes.

NO SILENT FALLBACK

    A missing key raises. This is the same rule the engine's
    `TemplateSet` follows and for the same reason: an English heading
    appearing in a Hindi report is a defect that looks like a design
    decision, and the only way to keep finding those is to make them
    loud.
"""

from __future__ import annotations

import json
import os
from typing import Optional

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "templates")


class MissingReportString(KeyError):
    """A chrome string with no entry in the active language."""


#: The English table, and the canonical key list. Kept in code rather than
#: read from `templates/en/report.json` so that `app.report` remains usable
#: with no data directory at all — a packaged build that failed to include
#: the templates should fail loudly on Hindi, not silently on English.
ENGLISH: dict = {
    # cover
    "cover.title": "Jyotish Analysis",
    "cover.document_title": "Jyotish analysis — {name}",
    "cover.unknown_name": "Unknown",
    "cover.generated": "{mode} report, generated {date}.",
    "cover.what_this_is": "What this document is",
    "cover.disclaimer": (
        "This document reports what a deterministic rule engine calculated "
        "from a birth chart. It is not a prediction of events, not advice, "
        "and not a validated statement of any tradition."),

    # birth details
    "birth.section": "Birth details",
    "birth.name": "Name",
    "birth.datetime": "Date and time of birth",
    "birth.precision": "Birth-time precision",
    "birth.utc": "Universal time",
    "birth.place": "Place",
    "birth.coordinates": "Latitude, longitude",
    "birth.timezone": "Timezone",
    "birth.resolved_by": "Place resolved by",
    "birth.lagna": "Lagna",
    "birth.lagna_nakshatra": "Lagna nakshatra",
    "birth.pada": " pada ",
    "birth.not_recorded": "not recorded",
    "birth.place_not_recorded": "place not recorded",
    "birth.precision_prefix": "Precision: ",

    # precision labels
    "precision.EXACT_TO_SECOND": "Exact to the second",
    "precision.EXACT_TO_MINUTE": "Exact to the minute",
    "precision.APPROX_5_MIN": "Approximate, within 5 minutes",
    "precision.APPROX_15_MIN": "Approximate, within 15 minutes",
    "precision.UNKNOWN": "Not known",

    # executive summary
    "summary.section": "Summary",
    "summary.activated": "Areas the engine reports as activated in this period",
    "summary.confidence_join": ", confidence ",
    "summary.none_active": (
        "No life area reaches the activation threshold for this moment "
        "under the profile in use."),
    "summary.silent": (
        " area(s) are reported as silent: the methodology profile in use "
        "does not admit enough evidence to say anything about them."),

    # charts
    "charts.section": "Charts",
    "charts.computed_by": "Computed by the {convention} convention.",
    "charts.style_note": (
        "Charts are drawn in the {style} style. Changing the style changes "
        "nothing about the calculation: the same placements are drawn in a "
        "different arrangement."),

    # planets
    "planets.section": "Planetary positions",
    "planets.graha": "Graha",
    "planets.sign": "Sign",
    "planets.degree": "Degree",
    "planets.house": "House",
    "planets.nakshatra": "Nakshatra",
    "planets.pada": "Pada",
    "planets.state": "State",
    "planets.dignity": "Dignity",
    "planets.shadbala": "Shadbala",

    # strength
    "strength.section": "Planetary strength (Shadbala)",
    "strength.note": (
        "Shadbala is the ratio of computed total strength to the strength "
        "the source text requires for that graha. It is a measured "
        "quantity, not a judgement."),
    "strength.total": "Total (rupa)",
    "strength.required": "Required (rupa)",
    "strength.ratio": "Ratio",
    "strength.meets": "Meets requirement",
    "strength.yes": "yes",
    "strength.components": "The six components, in rupas",
    "strength.sthana": "Sthana",
    "strength.dig": "Dig",
    "strength.kala": "Kala",
    "strength.chesta": "Chesta",
    "strength.naisargika": "Naisargika",
    "strength.drik": "Drik",
    "strength.approximation_title": "Methodology not fully source-validated",
    "strength.approximation": (
        "The strength of {planets} includes at least one component this "
        "engine computes by an approximation the source text does not "
        "state."),

    # yogas
    "yogas.section": "Yogas",
    "yogas.counted": (
        "The rule profile in use evaluated {total} rules and found "
        "{present} bearing on this chart: {names}"),
    "yogas.yoga": "Yoga",
    "yogas.grahas": "Grahas",
    "yogas.houses": "Houses",
    "yogas.validation": "Source validation",
    "yogas.matched": "Matched: ",
    "yogas.cancellation": "Cancellation: ",
    "yogas.stated_at": "Stated at: ",
    "yogas.note": (
        "A yoga's validation status describes how far its rule has been "
        "traced to a text, not how strongly it operates."),
    "yogas.status.PRESENT_AND_STRONG": "Strong",
    "yogas.status.PRESENT": "Formed",
    "yogas.status.PRESENT_BUT_WEAK": "Weakened",
    "yogas.status.CANCELLED": "Cancelled",
    "yogas.status.ABSENT": "Absent",

    # life domains
    "domains.section": "Life areas",
    "domains.natal_foundation": "Natal foundation",
    "domains.supporting": "Supporting factors",
    "domains.challenging": "Challenging factors",
    "domains.dasha": "Dasha activation",
    "domains.transit": "Transit triggers",
    "domains.varga": "Divisional chart confirmation",
    "domains.timing": "Timing",

    # dasha
    "dasha.section": "Vimshottari dasha",
    "dasha.running": "Running periods at the analysed moment",
    "dasha.mahadashas": "Mahadashas, {convention}",
    "dasha.lord": "Lord",
    "dasha.from": "From",
    "dasha.length": "Length",
    "dasha.antardashas": "Antardashas within the {lord} mahadasha",
    "dasha.period": "Period",

    # transits
    "transits.section": "Transits",
    "transits.positions": "Transit positions for {date}",
    "transits.house_from_lagna": "House from Lagna",
    "transits.house_from_moon": "House from Chandra",
    "transits.relationships": "Transit-to-natal relationships",
    "transits.transiting": "Transiting",
    "transits.relationship": "Relationship",
    "transits.natal_point": "Natal point",
    "transits.orb": "Orb",
    "transits.note": (
        "These are positions, not interpretations. What a transit is taken "
        "to activate is decided in the synthesis layer, under the rules "
        "recorded there."),

    # timing windows
    "windows.section": "Timing windows",
    "windows.none": (
        "No timing window could be derived for any area from the dasha "
        "boundaries and transit events available."),
    "windows.area": "Area",
    "windows.candidate": "Candidate",
    "windows.peak": "Peak",
    "windows.to": "To",
    "windows.activation": "Activation",
    "windows.confidence": "Confidence",
    "windows.note": (
        "Activation and confidence are ordinal bands, not probabilities. A "
        "window is the interval in which the engine's conditions hold, not "
        "a forecast that anything happens in it."),

    # reliability
    "reliability.section": "Reliability and limits",
    "reliability.treated_as": "The birth time was treated as {precision}.",
    "reliability.unstated": "unstated",
    "reliability.not_calculated": (
        "Birth-time sensitivity was not calculated for this chart. Nothing "
        "below has been shown to be stable against a small change in the "
        "recorded time."),
    "reliability.stable": (
        "Nothing in this chart changes within {minutes} minutes either side "
        "of the recorded time."),
    "reliability.unstable": (
        "At least one classification in this chart changes within the "
        "smallest window tested."),
    "reliability.changes": "What changes within the birth-time uncertainty",
    "reliability.boundaries": "Unresolved boundaries",
    "reliability.boundary_text": (
        "The calculation does not resolve the sign or nakshatra of: "
        "{bodies}. Their classification is uncertain within the engine's "
        "own error envelope, independently of the birth time."),
    "reliability.four_claims": "Four separate claims",
    "reliability.four_claims_text": (
        "Computationally tested, externally benchmarked, textual source "
        "located and tradition-validated are four different claims. This "
        "engine asserts the fourth for nothing."),

    # methodology
    "methodology.section": "Methodology",
    "methodology.setting": "Setting",
    "methodology.value": "Value",
    "methodology.note": "Note",
    "methodology.registry": "Source registry",

    # sources
    "sources.section": "Sources and rules",
    "sources.intro": (
        "Every rule used above, with where its statement was located. "
        "Passages are cited, never reproduced: this application stores "
        "locators and short summaries, not text."),
    "sources.witnesses": "Witnesses cited",
    "sources.citation": "Citation",
    "sources.work": "Work",
    "sources.authority": "Authority",
    "sources.edition": "Edition",
    "sources.unresolved": "References this build could not resolve",
    "sources.no_witness": "no witness registered",
    "sources.rules": "Rules applied",
    "sources.rule": "Rule",
    "sources.validation_status": "Validation status",
    "sources.eligibility": "Prediction eligibility",
    "sources.note": (
        "A located source means a passage has been found and read. It does "
        "not mean a scholar has confirmed that the passage states this "
        "rule."),

    # generic
    "generic.empty": "—",
    "mode.summary": "Summary",
    "mode.detailed": "Detailed",
    "mode.technical": "Technical",
}

#: Languages this module can produce chrome for. English is built in; the
#: rest must supply a complete `report.json`.
BUILTIN_LANGUAGE = "en"


class ReportStrings:
    """One language's chrome strings."""

    def __init__(self, language: str, table: dict):
        self.language = language
        self.table = table

    def __call__(self, key: str, **kwargs) -> str:
        try:
            value = self.table[key]
        except KeyError:
            raise MissingReportString(
                f"report string '{key}' has no entry for language "
                f"'{self.language}'") from None
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as exc:
                raise MissingReportString(
                    f"report string '{key}' wants argument {exc} in "
                    f"language '{self.language}'") from None
        return value

    def has(self, key: str) -> bool:
        return key in self.table

    def missing(self) -> list[str]:
        return sorted(key for key in ENGLISH if key not in self.table)


_CACHE: dict = {}


def load_strings(language: str = "en",
                 root: Optional[str] = None) -> ReportStrings:
    """
    Chrome strings for one language.

    An unknown language falls back to English AND SAYS SO through
    `ReportStrings.language`, rather than pretending to be the requested
    one — a caller rendering a report can then state the substitution in
    the document instead of a reader discovering it.
    """
    key = (language, root or TEMPLATE_ROOT)
    if key in _CACHE:
        return _CACHE[key]

    if language == BUILTIN_LANGUAGE:
        strings = ReportStrings(language, dict(ENGLISH))
    else:
        path = os.path.join(root or TEMPLATE_ROOT, language, "report.json")
        if not os.path.exists(path):
            strings = ReportStrings(BUILTIN_LANGUAGE, dict(ENGLISH))
        else:
            with open(path, encoding="utf-8") as handle:
                table = json.load(handle)
            strings = ReportStrings(language, table)
    _CACHE[key] = strings
    return strings


def available_languages(root: Optional[str] = None) -> list[str]:
    """Languages with a complete chrome table."""
    base = root or TEMPLATE_ROOT
    out = [BUILTIN_LANGUAGE]
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            if name == BUILTIN_LANGUAGE:
                continue
            if os.path.exists(os.path.join(base, name, "report.json")):
                out.append(name)
    return out


def completeness(language: str, root: Optional[str] = None) -> dict:
    """How complete one language's chrome is. For the methodology screen."""
    strings = load_strings(language, root)
    missing = strings.missing()
    return {
        "language": language,
        "resolved_language": strings.language,
        "total_keys": len(ENGLISH),
        "translated": len(ENGLISH) - len(missing),
        "missing": missing,
        "complete": not missing and strings.language == language,
    }
