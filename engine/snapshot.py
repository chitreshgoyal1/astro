"""
Canonical chart snapshot (V1.2 Part 13)
----------------------------------------
One serialisable object holding everything the engine knows about a natal
chart. This is the formal contract that the transit engine, timing rules, an
interpretation layer, an API, a UI and the PDF generator will all consume, so
it is versioned and its shape is pinned by tests.

CONTENTS ARE FACTS. Four kinds, and the snapshot keeps them apart:

    ASTRONOMICAL FACT             positions, speeds, ayanamsha, accuracy
    CALCULATED ASTROLOGICAL       houses, lordships, dignity, aspects, vargas
      FEATURE
    TRADITION-SPECIFIC RULE       yoga verdicts, varga conventions, dasha
    SOFTWARE HEURISTIC            engine_strength_score, boundary warnings

No prose and no predictions. A consumer that wants to say what a placement
means must do that itself; nothing here has decided it already.

SCHEMA STABILITY
    `schema_version` follows semantic versioning.
      major  a field was removed or its meaning changed
      minor  a field was added; existing readers keep working
      patch  a value changed, the shape did not
    Everything is JSON-native: `json.dumps(snapshot.to_dict())` works with no
    custom encoder, and a test asserts it.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from typing import Any, Optional

# 1.2.0 (V1.4): ADDED `strengths`, `ashtakavarga`, `bhava` and
# `birth_time_sensitivity`. All additive — nothing removed, nothing
# redefined — so a 1.0.0 or 1.1.0 reader keeps working and simply does not
# see the new sections. A minor bump, per the versioning rule below.
#
# TRANSITS ARE NOT HERE, DELIBERATELY. Part 21 forbids embedding them in the
# natal snapshot, and rightly: a natal chart is immutable and a transit
# snapshot is a function of an arbitrary moment. Putting one inside the other
# would make the "natal" snapshot silently time-dependent. TransitSnapshot
# stays a separate object.
SCHEMA_VERSION = "1.2.0"


def _round(value: Optional[float], places: int = 6) -> Optional[float]:
    return None if value is None else round(value, places)


def _isoformat(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return str(value)


# ── section builders ─────────────────────────────────────────────────────────

def _birth_section(birth_datetime, location, birth_utc=None,
                   name: Optional[str] = None) -> dict:
    data: dict[str, Any] = {
        "name": name,
        "datetime_local": _isoformat(birth_datetime),
        "datetime_utc": _isoformat(birth_utc),
    }
    if location is not None:
        data["location"] = {
            "name": location.name,
            "latitude": _round(location.latitude),
            "longitude": _round(location.longitude),
            "timezone_name": location.timezone_name,
            "utc_offset_hours": location.utc_offset_at_birth,
            "resolved_by": location.source,
        }
    else:
        data["location"] = None
    return data


def _methodology_section(varga_config, rule_profile: Optional[str],
                         house_system: str = "whole_sign") -> dict:
    """
    V1.3 Part 14: which methodology produced this chart, and how far its rules
    have actually been traced to a text.

    Source IDs only — never the corpus. A consumer that wants a witness looks
    it up in the registry by id; embedding editions and locators in every
    chart would bloat the snapshot and duplicate a single source of truth.
    """
    from .rules import DEFAULT_PROFILE, RULE_PROFILES
    from .sources import REGISTRY_VERSION, registry_summary
    from .varga_metadata import VARGA_ALGORITHM_VERSION

    profile = rule_profile or DEFAULT_PROFILE
    summary = registry_summary()
    return {
        "varga_profile": (varga_config.source
                          if varga_config is not None else "built-in defaults"),
        "varga_algorithm_version": VARGA_ALGORITHM_VERSION,
        "rule_profile": profile,
        "house_system": house_system,
        "rule_reference_space": "RASHI",
        "reference_space_note": (
            "Every shipped yoga rule is evaluated in RASHI space. Bhava "
            "Chalit, where computed, is a separate representation and does "
            "not feed the rules."),
        "rule_profile_description": RULE_PROFILES.get(profile, ""),
        "source_registry_version": REGISTRY_VERSION,
        "source_registry_reviewed_on": summary["reviewed_on"],
        "provenance_summary": {
            "witnesses_registered": summary["witnesses_registered"],
            "rules_by_validation_status": summary["rules_by_status"],
            "vargas_by_validation_status": summary["vargas_by_status"],
            "registered_conflicts": summary["conflicts"],
            "open_human_review_items": summary["open_review_items"],
            "tradition_validated": summary["tradition_validated"],
        },
        "claim_separation": {
            "computationally_tested": (
                "The code does what it was told to. Established by the test "
                "suite."),
            "externally_benchmarked": (
                "Positions agree with an independent reference ephemeris. "
                "This is agreement, not absolute accuracy."),
            "textual_source_located": (
                "A specific passage in a specific witness has been found."),
            "tradition_source_validated": (
                "That passage actually states this rule. Asserted for nothing "
                "in this build."),
            "note": (
                "These four are separate claims. None is evidence for any "
                "other."),
        },
    }


def _settings_section(chart, features, varga_config) -> dict:
    provenance = dict(features.provenance) if features is not None else {}
    return {
        "zodiac": "sidereal",
        "ayanamsha": chart.ayanamsha_system,
        "ayanamsha_value_deg": _round(chart.ayanamsha),
        "node": "true" if getattr(chart, "true_node", True) else "mean",
        "house_system": "whole_sign",
        "positions_source": chart.source,
        "aspect_profile": provenance.get("aspect_profile"),
        "node_aspects": provenance.get("node_aspects"),
        "conjunction_orb_deg": provenance.get("conjunction_orb_deg"),
        "combustion_profile": provenance.get("combustion_profile"),
        "varga_conventions_source": (
            varga_config.source if varga_config is not None else None),
        "delta_t_seconds": _round(getattr(chart, "delta_t", None), 3),
        "julian_day_ut": _round(getattr(chart, "jd_ut", None), 9),
    }


def _accuracy_section(features) -> dict:
    """
    ASTRONOMICAL FACT plus SOFTWARE HEURISTIC: the measured error envelopes,
    and which classifications they leave unresolved in this particular chart.
    """
    from .ephemeris import VSOP87_PROVENANCE, theory_used
    from .uncertainty import ACCURACY_ARCMIN, SAFETY_FACTOR

    section: dict[str, Any] = {
        "basis": ("maximum error measured against the Swiss Ephemeris over "
                  "1800-2050; see tests/fixtures/accuracy_profile.json"),
        "safety_factor": SAFETY_FACTOR,
        "envelopes_arcmin": dict(ACCURACY_ARCMIN),
        "theories": {body: theory_used(body) for body in ACCURACY_ARCMIN},
        "vsop87": {
            "theory": VSOP87_PROVENANCE["theory"],
            "variant": VSOP87_PROVENANCE["variant"],
            "source": VSOP87_PROVENANCE["source"],
            "validated_against": VSOP87_PROVENANCE["validated_against"],
            "bodies": sorted(VSOP87_PROVENANCE["term_counts"]),
            "term_counts": VSOP87_PROVENANCE["term_counts"],
        },
    }
    if features is not None:
        section["boundary_warnings"] = features.uncertainty.get("warnings", {})
        section["bodies_with_warnings"] = features.uncertainty.get(
            "bodies_with_warnings", [])
        if features.lagna_uncertainty is not None:
            section["lagna"] = features.lagna_uncertainty.to_dict()
    return section


def _planet_section(chart, features) -> dict:
    planets: dict[str, Any] = {}
    for name, position in chart.planets.items():
        entry: dict[str, Any] = {
            # ASTRONOMICAL FACT
            "longitude": _round(position.longitude),
            "latitude": _round(position.latitude),
            "speed_deg_per_day": _round(position.speed),
            "retrograde": bool(position.is_retrograde),
            "stationary": bool(position.is_stationary),
            # CALCULATED ASTROLOGICAL FEATURE
            "sign": position.rashi,
            "sign_index": position.rashi_index,
            "degree_in_sign": _round(position.degree_in_rashi),
            "sign_lord": position.rashi_lord,
            "nakshatra": position.nakshatra,
            "nakshatra_index": position.nakshatra_index,
            "nakshatra_lord": position.nakshatra_lord,
            "pada": position.pada,
            "dignity": position.dignity,
            "combust": bool(position.is_combust),
            "sun_separation_deg": _round(position.sun_separation, 4),
            "combustion_orb_deg": position.combustion_orb,
        }
        graha = features.planet(name) if features is not None else None
        if graha is not None:
            entry.update({
                "house": graha.house,
                "houses_owned": list(graha.houses_owned),
                "exalted": graha.exalted,
                "debilitated": graha.debilitated,
                "own_sign": graha.own_sign,
                "moolatrikona": graha.moolatrikona,
                "friendly_sign": graha.friendly_sign,
                "enemy_sign": graha.enemy_sign,
                "vargottama": graha.vargottama,
                "dispositor": graha.dispositor,
                "natural_benefic": graha.natural_benefic,
                "natural_malefic": graha.natural_malefic,
                "functional_nature": graha.functional_nature,
                "functional_roles": list(graha.functional_roles),
                "conjunct_same_sign": graha.conjunct_planets,
                "aspects_given": [
                    {"to_house": a.to_house, "type": a.aspect_type,
                     "full": a.full, "targets": list(a.targets)}
                    for a in graha.aspects_given],
                "aspected_by": graha.aspecting_planets,
                "speed_is_measured": graha.speed_is_measured,
                "theory": graha.theory,
            })
            if graha.uncertainty is not None:
                entry["uncertainty"] = graha.uncertainty.to_dict()
        planets[name] = entry
    return planets


def _lagna_section(chart, features) -> dict:
    lagna = chart.lagna
    data = {
        "longitude": _round(lagna.longitude),
        "sign": lagna.rashi,
        "sign_index": lagna.rashi_index,
        "degree_in_sign": _round(lagna.degree_in_rashi),
        "sign_lord": lagna.rashi_lord,
        "nakshatra": lagna.nakshatra,
        "nakshatra_lord": lagna.nakshatra_lord,
        "pada": lagna.pada,
    }
    if getattr(chart, "midheaven", None) is not None:
        data["midheaven_longitude"] = _round(chart.midheaven)
    if features is not None and features.lagna_uncertainty is not None:
        data["uncertainty"] = features.lagna_uncertainty.to_dict()
    return data


def _houses_section(features) -> dict:
    if features is None:
        return {}
    return {
        str(number): {
            "sign": bhava.sign_name,
            "sign_index": bhava.sign,
            "lord": bhava.lord,
            "lord_house": bhava.lord_house,
            "occupants": list(bhava.occupants),
            "aspected_by": bhava.aspecting_planets,
            "benefic_influences": list(bhava.benefic_influences),
            "malefic_influences": list(bhava.malefic_influences),
            "is_kendra": bhava.is_kendra,
            "is_trikona": bhava.is_trikona,
            "is_dusthana": bhava.is_dusthana,
            "is_upachaya": bhava.is_upachaya,
            "is_maraka": bhava.is_maraka,
        }
        for number, bhava in sorted(features.houses.items())
    }


def _vargas_section(features, varga_config) -> dict:
    """
    Divisional placements, each carrying the convention and algorithm version
    that produced it — see engine/varga_metadata.py for why that matters.
    """
    if features is None:
        return {}
    from .varga_metadata import convention_metadata

    bodies: dict[str, Any] = {}
    for name, graha in features.planets.items():
        bodies[name] = {
            key: {"sign": placement.sign_name,
                  "sign_index": placement.sign,
                  "lord": placement.lord,
                  "convention": placement.convention,
                  "dignity": placement.dignity_label()}
            for key, placement in graha.vargas.items()
        }
    lagnas = {
        key: {"sign": placement.sign_name, "sign_index": placement.sign,
              "lord": placement.lord, "convention": placement.convention}
        for key, placement in features.varga_lagnas.items()
    }
    return {
        "conventions": convention_metadata(varga_config),
        "lagna": lagnas,
        "bodies": bodies,
    }


def _features_section(features) -> dict:
    if features is None:
        return {}
    from .features.conjunctions import conjunctions_to_dicts

    return {
        "house_lords": {str(k): v for k, v in features.house_lords.items()},
        "conjunctions": conjunctions_to_dicts(features.conjunctions),
        "aspects": [
            {"from": a.source, "to_house": a.to_house, "to_sign": a.to_sign,
             "aspect_type": a.aspect_type, "full": a.full,
             "targets": list(a.targets)}
            for a in features.aspects],
        "parivartanas": [
            {"planet1": p.planet1, "planet2": p.planet2, "house1": p.house1,
             "house2": p.house2, "category": p.category}
            for p in features.parivartanas],
        "dispositor_chains": {k: list(v)
                              for k, v in features.dispositor_chains.items()},
        "final_dispositors": dict(features.final_dispositors),
        "graha_yuddha": [
            {"planet1": w.planet1, "planet2": w.planet2,
             "separation_deg": _round(w.separation, 4),
             "winner": w.winner, "basis": w.basis}
            for w in features.graha_yuddha],
        "functional_roles": {
            name: {"houses_owned": list(role.houses_owned),
                   "roles": list(role.roles),
                   "functional_nature": role.functional_nature,
                   "is_yogakaraka": role.is_yogakaraka,
                   "reason": role.reason}
            for name, role in features.functional_roles.items()},
        "warnings": list(features.warnings),
    }


def _yogas_section(results) -> list:
    if not results:
        return []
    return [result.to_dict() for result in results]


def _timing_section(dasha) -> dict:
    if dasha is None:
        return {}
    return {"vimshottari": dasha.to_dict()}


# ── the snapshot ─────────────────────────────────────────────────────────────

@dataclass
class ChartSnapshot:
    """Everything known about one natal chart, as plain JSON-native data."""

    schema_version: str = SCHEMA_VERSION
    generated: str = ""
    birth: dict = field(default_factory=dict)
    calculation_settings: dict = field(default_factory=dict)
    methodology: dict = field(default_factory=dict)
    accuracy: dict = field(default_factory=dict)
    lagna: dict = field(default_factory=dict)
    planets: dict = field(default_factory=dict)
    houses: dict = field(default_factory=dict)
    vargas: dict = field(default_factory=dict)
    features: dict = field(default_factory=dict)
    yogas: list = field(default_factory=list)
    timing: dict = field(default_factory=dict)
    # V1.4 additions.
    strengths: dict = field(default_factory=dict)
    ashtakavarga: dict = field(default_factory=dict)
    bhava: dict = field(default_factory=dict)
    birth_time_sensitivity: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "generated": self.generated,
            "birth": self.birth,
            "calculation_settings": self.calculation_settings,
            "methodology": self.methodology,
            "accuracy": self.accuracy,
            "lagna": self.lagna,
            "planets": self.planets,
            "houses": self.houses,
            "vargas": self.vargas,
            "features": self.features,
            "yogas": self.yogas,
            "timing": self.timing,
            "strengths": self.strengths,
            "ashtakavarga": self.ashtakavarga,
            "bhava": self.bhava,
            "birth_time_sensitivity": self.birth_time_sensitivity,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialise with the standard encoder — no custom handling needed."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def write(self, path: str, indent: Optional[int] = 2) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.to_json(indent=indent))
            handle.write("\n")


def build_snapshot(chart,
                   features=None,
                   yoga_results=None,
                   dasha=None,
                   varga_config=None,
                   birth_datetime=None,
                   birth_utc=None,
                   location=None,
                   name: Optional[str] = None,
                   rule_profile: Optional[str] = None,
                   shadbala=None,
                   ashtakavarga=None,
                   bhava=None,
                   sensitivity=None) -> ChartSnapshot:
    """
    Assemble the snapshot.

    Every section is optional: a snapshot built from a chart alone is still
    valid and still serialises, it simply carries empty sections for the parts
    that were not computed.
    """
    return ChartSnapshot(
        schema_version=SCHEMA_VERSION,
        generated=datetime.datetime.now().isoformat(timespec="seconds"),
        birth=_birth_section(birth_datetime, location, birth_utc, name),
        calculation_settings=_settings_section(chart, features, varga_config),
        methodology=_methodology_section(
            varga_config, rule_profile,
            house_system=(bhava.system if bhava is not None
                          else "whole_sign")),
        accuracy=_accuracy_section(features),
        lagna=_lagna_section(chart, features),
        planets=_planet_section(chart, features),
        houses=_houses_section(features),
        vargas=_vargas_section(features, varga_config),
        features=_features_section(features),
        yogas=_yogas_section(yoga_results),
        timing=_timing_section(dasha),
        strengths=shadbala.to_dict() if shadbala is not None else {},
        ashtakavarga=(ashtakavarga.to_dict()
                      if ashtakavarga is not None else {}),
        bhava=bhava.to_dict() if bhava is not None else {},
        birth_time_sensitivity=(sensitivity.to_dict()
                                if sensitivity is not None else {}),
    )
