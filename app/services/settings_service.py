"""
Settings service (V1.7 Parts 3, 18, 19, 33)
=============================================
Which methodology options exist, whether a chosen set is usable, and what
actually produced the chart on screen.

WHY THE OPTIONS ARE READ FROM THE ENGINE, NOT LISTED HERE

    A hard-coded list of ayanamshas in the UI is a list that goes stale the
    first time the engine gains one, and goes wrong the first time it loses
    one. Every option below is enumerated from the engine's own registry, so
    the form can only ever offer what the calculator can actually do.

THE METHODOLOGY PANEL (Part 18)

    `describe_methodology` reads the snapshot, not the settings. Those are
    different questions: settings are what was asked for, the snapshot
    records what was used. They normally agree, and when they do not — a
    varga convention file that named a convention for a chart that was not
    computed, say — the panel should show the second.
"""

from __future__ import annotations

from typing import Optional

from ..errors import MethodologyError, UnsupportedLanguageError
from ..models import ApplicationSettings, BirthTimePrecision, ReportPreferences


def available_options() -> dict:
    """Every choice the form may offer, with the shipped default marked."""
    from engine.houses import HOUSE_PROFILES
    from engine.interpretation import available_languages
    from engine.interpretation.models import ReportMode
    from engine.planets import available_ayanamshas
    from engine.rules import DEFAULT_PROFILE, RULE_PROFILES
    from engine.synthesis import PROFILE_MEANING, SynthesisProfile
    from engine.vargas import VARGA_ORDER, VARGA_SPECS, available_conventions

    from ..visual import IMPLEMENTED_STYLES, STYLE_LABELS

    defaults = ApplicationSettings()
    return {
        "ayanamsha": {
            "values": sorted(available_ayanamshas()),
            "default": defaults.ayanamsha,
            "label": "Ayanamsha",
            "help": "The sidereal/tropical offset. Changing it moves every "
                    "position and can move a graha into a different sign.",
        },
        "node": {
            "values": ["true", "mean"],
            "default": defaults.node,
            "label": "Rahu/Ketu node",
            "help": "Whether the lunar nodes are the true oscillating node "
                    "or the mean node.",
        },
        "house_system": {
            "values": sorted(HOUSE_PROFILES),
            "default": defaults.house_system,
            "label": "Bhava (house) system",
            "help": "The Rashi chart is always computed and every yoga rule "
                    "is evaluated in Rashi space. This chooses the Bhava "
                    "representation shown alongside it.",
        },
        "rule_profile": {
            "values": sorted(RULE_PROFILES),
            "default": DEFAULT_PROFILE,
            "labels": dict(RULE_PROFILES),
            "label": "Yoga rule profile",
            "help": "Which tradition's rule set is evaluated.",
        },
        "node_aspects": {
            "values": ["none", "parashari_like", "kendra"],
            "default": defaults.node_aspects,
            "label": "Node aspects",
            "help": "Whether Rahu and Ketu cast drishti, and on which "
                    "houses. Traditions disagree; the choice is recorded "
                    "with the chart.",
        },
        "synthesis_profile": {
            "values": [p.value for p in SynthesisProfile],
            "default": defaults.synthesis_profile,
            "labels": {k.value if hasattr(k, "value") else str(k): v
                       for k, v in PROFILE_MEANING.items()},
            "label": "Synthesis profile",
            "help": "How much evidence a conclusion is allowed to rest on.",
        },
        "language": {
            "values": available_languages(),
            "default": defaults.language,
            "label": "Language",
            "help": "The language of the interpretation. Calculations are "
                    "identical in every language.",
        },
        "report_mode": {
            "values": [m.value for m in ReportMode],
            "default": ReportPreferences().mode,
            "label": "Report depth",
            "help": "Summary, detailed or technical. The same findings; "
                    "more or less of the working shown.",
        },
        "birth_time_precision": {
            "values": [p.value for p in BirthTimePrecision],
            "default": BirthTimePrecision.EXACT_TO_MINUTE.value,
            "labels": {p.value: p.label for p in BirthTimePrecision},
            "label": "Birth-time precision",
            "help": "How well the time is actually known. This only ever "
                    "widens what the engine treats as uncertain.",
        },
        "varga_conventions": {
            "charts": list(VARGA_ORDER),
            "values": {key: list(conventions)
                       for key, conventions
                       in available_conventions().items()},
            "defaults": {key: VARGA_SPECS[key].default for key in VARGA_ORDER},
            "label": "Divisional chart conventions",
            "help": "Several vargas are computed differently by different "
                    "authorities. The convention used is recorded with every "
                    "placement.",
        },
        "chart_detail": {
            "values": ["COMPACT", "STANDARD", "DETAILED"],
            "default": ReportPreferences().chart_detail,
            "label": "Chart detail",
            "help": "How much is drawn inside each house of a kundli. "
                    "Presentation only; no calculation changes.",
        },
        "chart_style": {
            # Only the styles that can actually be drawn are offered. The
            # East Indian chart is a named, refused style; listing it in a
            # form would be offering something the application cannot do.
            "values": list(IMPLEMENTED_STYLES),
            "default": ReportPreferences().chart_style,
            "labels": {style: STYLE_LABELS[style]
                       for style in IMPLEMENTED_STYLES},
            "label": "Chart style",
            "help": "North Indian fixes the houses on the page and moves "
                    "the signs; South Indian fixes the signs and moves the "
                    "houses. The same placements either way.",
        },
    }


def validate_settings(settings: ApplicationSettings) -> ApplicationSettings:
    """
    Check every option against the engine's registries before anything runs.

    Failing here is much better than failing three minutes into a chart
    calculation, and it lets the form mark the offending field.
    """
    options = available_options()
    for field_name in ("ayanamsha", "node", "house_system", "rule_profile",
                       "node_aspects", "synthesis_profile"):
        value = getattr(settings, field_name)
        allowed = options[field_name]["values"]
        if value not in allowed:
            raise MethodologyError(
                f"'{value}' is not one of the available values for "
                f"{options[field_name]['label'].lower()}. "
                f"Available: {', '.join(map(str, allowed))}.",
                field=field_name)

    if settings.language not in options["language"]["values"]:
        raise UnsupportedLanguageError(
            f"No templates are installed for '{settings.language}'. "
            f"Installed: {', '.join(options['language']['values']) or 'none'}.",
            field="language")
    return settings


def describe_methodology(natal, settings: Optional[ApplicationSettings] = None
                         ) -> dict:
    """
    What produced this chart (Part 18), read out of the snapshot.

    Returns display rows rather than a nested structure, because the panel
    is a table and the caller should not have to know which engine section
    each value came from.
    """
    snapshot = natal.snapshot if hasattr(natal, "snapshot") else natal
    calc = snapshot.get("calculation_settings", {}) or {}
    method = snapshot.get("methodology", {}) or {}
    birth = snapshot.get("birth", {}) or {}
    provenance = method.get("provenance_summary", {}) or {}

    rows = [
        ("Zodiac", calc.get("zodiac", "sidereal"),
         "Sidereal throughout. This engine has no tropical mode."),
        ("Ayanamsha", calc.get("ayanamsha", ""),
         f"Value at birth: {calc.get('ayanamsha_value_deg')}°"),
        ("Lunar node", calc.get("node", ""),
         "Rahu and Ketu are computed from this node."),
        ("Rashi house system", calc.get("house_system", "whole_sign"),
         "The space every yoga rule is evaluated in."),
        ("Bhava system", method.get("house_system", "whole_sign"),
         method.get("reference_space_note", "")),
        ("Varga profile", method.get("varga_profile", ""),
         f"Algorithm version {method.get('varga_algorithm_version', '')}"),
        ("Rule profile", method.get("rule_profile", ""),
         method.get("rule_profile_description", "")),
        ("Aspect profile", calc.get("aspect_profile", ""),
         f"Node aspects: {calc.get('node_aspects', '')}"),
        ("Positions source", calc.get("positions_source", ""),
         "Whether the positions were calculated or entered by hand."),
        ("Birth-time precision", birth.get("time_precision", "not recorded"),
         birth.get("time_precision_basis", "")),
        ("Source registry", method.get("source_registry_version", ""),
         f"Reviewed {method.get('source_registry_reviewed_on', '')}"),
        ("Chart schema", snapshot.get("schema_version", ""),
         "The version of the snapshot format this chart was written in."),
        ("ΔT", f"{calc.get('delta_t_seconds', '')} s",
         "Terrestrial minus universal time at the moment of birth."),
        ("Julian day (UT)", calc.get("julian_day_ut", ""),
         "The instant every position was computed for."),
    ]
    if settings is not None:
        changed = settings.non_default()
        if changed:
            rows.append(
                ("Non-default settings",
                 ", ".join(f"{k}={v}" for k, v in sorted(changed.items())),
                 "Options changed from the shipped defaults."))

    return {
        "rows": [{"label": label, "value": value, "note": note}
                 for label, value, note in rows],
        "provenance": provenance,
        "claim_separation": method.get("claim_separation", {}),
    }
