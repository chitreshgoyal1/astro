"""
Release mode (V1.8 Part 48)
-----------------------------
Conservative defaults, and experimental choices that announce themselves.

THE PROBLEM PART 48 NAMES

    "Do not make experimental rules appear equivalent to strict rules."

    Every methodology option in this application is presented in the same
    dropdown, in the same typeface, with the same kind of help text. A
    user choosing `experimental` sees a word; they do not see that it
    admits rules with no located witness, and the report they get back
    looks exactly like the report the strict profile produces — same
    headings, same confidence vocabulary, same tone.

    That is a presentation problem with a methodological consequence, and
    it is the last one a release candidate should ship with.

WHAT RELEASE MODE ACTUALLY DOES

    It does NOT remove options. Removing them would push a practitioner
    who wants the extended catalog to a fork, and the whole point of the
    provenance work is that unverified rules stay visible rather than
    being deleted.

    It does three things instead:

        1. Defaults are the conservative ones, stated here rather than
           scattered across dataclass field defaults.
        2. Any departure from them is CLASSIFIED — conservative,
           experimental, or unverified — and the classification is
           derived from the engine's own registries, not typed out.
        3. A run using an experimental option carries a warning into the
           document, beside the result, not in a footer.

    A user who wants experimental settings gets them. They also get a
    document that says so.
"""

from __future__ import annotations

from typing import Optional

from ..models import ApplicationSettings

CONSERVATIVE = "conservative"
EXPERIMENTAL = "experimental"
UNVERIFIED = "unverified"


#: The settings a release build uses when nobody chooses otherwise.
#:
#: Written out here rather than being read from `ApplicationSettings()`
#: so that a field default can change for a development reason without
#: silently changing what a release ships with. A test asserts the two
#: agree, which is the point: they should, and the assertion is where a
#: divergence gets argued about.
RELEASE_DEFAULTS = {
    "ayanamsha": "lahiri",
    "node": "true",
    "house_system": "whole_sign",
    "rule_profile": "parashari",
    "node_aspects": "parashari_like",
    "synthesis_profile": "standard",
    "ashtakavarga_reductions": False,
}


#: Choices that go beyond the located evidence, and what each one admits.
#:
#: The TEXT here is the engine's own, read from its registries where
#: possible; the CLASSIFICATION is this module's, because "is this
#: experimental" is a product judgement rather than an evidential one.
_CLASSIFIED = {
    ("synthesis_profile", "experimental"): (
        EXPERIMENTAL,
        "The experimental synthesis profile admits rules that have no "
        "located witness. Conclusions drawn under it rest partly on "
        "convention this engine has not traced to any text."),
    ("synthesis_profile", "strict"): (
        CONSERVATIVE,
        "The strict profile admits only evidence-qualified rules. It is "
        "often silent on a domain, and silence there means the evidence "
        "did not reach the bar rather than that nothing is indicated."),
    ("rule_profile", "parashari_extended"): (
        EXPERIMENTAL,
        "The extended rule profile adds variant readings held by later "
        "authorities. The variants are attested; the combination is this "
        "engine's."),
    ("ashtakavarga_reductions", True): (
        UNVERIFIED,
        "Ashtakavarga reductions (trikona and ekadhipatya) are computed "
        "by a procedure this engine has not matched to a located source. "
        "They are off by default and stay off unless asked for."),
}


def classify(name: str, value) -> tuple[str, str]:
    """How far one setting departs from the conservative default."""
    known = _CLASSIFIED.get((name, value))
    if known is not None:
        return known
    if name in RELEASE_DEFAULTS and value != RELEASE_DEFAULTS[name]:
        return (EXPERIMENTAL,
                f"{name} is set to {value!r}, which is not the value this "
                f"release ships with ({RELEASE_DEFAULTS[name]!r}). The "
                f"choice is recorded with every result.")
    return (CONSERVATIVE, "")


def release_settings(**overrides) -> ApplicationSettings:
    """Settings starting from the release defaults."""
    values = dict(RELEASE_DEFAULTS)
    values.update(overrides)
    return ApplicationSettings(**values)


def audit(settings: ApplicationSettings) -> dict:
    """
    Which of these settings depart from the release defaults, and how.

    Returns the departures with their classification, and a list of
    warnings ready to be carried into a document.
    """
    departures = []
    for name in sorted(RELEASE_DEFAULTS):
        value = getattr(settings, name, None)
        kind, note = classify(name, value)
        if kind == CONSERVATIVE and value == RELEASE_DEFAULTS[name]:
            continue
        departures.append({
            "setting": name,
            "value": value,
            "default": RELEASE_DEFAULTS[name],
            "classification": kind,
            "note": note,
        })

    experimental = [d for d in departures
                    if d["classification"] in (EXPERIMENTAL, UNVERIFIED)]
    return {
        "is_release_default": not departures,
        "departures": departures,
        "experimental_count": len(experimental),
        "warnings": [d["note"] for d in experimental if d["note"]],
        "note": (
            "Release mode does not remove options. It states which of them "
            "go beyond what this engine has traced to a source, so that a "
            "document produced under one cannot be mistaken for a document "
            "produced under the defaults."),
    }


def describe_options() -> list[dict]:
    """
    Every classified option, for the settings screen.

    Rendered beside the control rather than in a separate help page: a
    warning a user has to navigate to is a warning they will not see at
    the moment they are making the choice.
    """
    return [
        {
            "setting": name,
            "value": value,
            "classification": kind,
            "note": note,
        }
        for (name, value), (kind, note) in sorted(
            _CLASSIFIED.items(), key=lambda item: (item[0][0], str(item[0][1])))
    ]


def release_warnings(settings: Optional[ApplicationSettings]) -> list[str]:
    """The warnings a document should carry for these settings."""
    if settings is None:
        return []
    return audit(settings)["warnings"]
