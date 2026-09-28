"""
Astrology feature engine
------------------------
Calculated, factual descriptions of a chart, built once and consumed by the
rule engine. The package boundary is the important part: everything in here
derives facts, and nothing in here decides what a fact means for the native.

    chart      = JyotishChart(...)
    features   = build_chart_features(chart)
    results    = evaluate_rules(features)        # engine.rules

Layers, in the vocabulary used throughout the documentation:

  ASTRONOMICAL FACT            engine/ephemeris.py — positions
  CALCULATED ASTROLOGY FEATURE engine/features/   — this package
  TRADITION-SPECIFIC RULE      engine/rules/      — named, sourced Yoga rules
  INTERPRETATION               not yet built      — the narrative layer
"""

from .aspects import (
    AspectProfile, DEFAULT_ASPECT_PROFILE, NODE_ASPECT_CONVENTIONS,
    aspects_to_dicts, compute_aspects, parashari_profile,
)
from .builder import build_chart_features
from .conjunctions import (
    DEFAULT_ORB_DEG, GrahaYuddha, angular_separation, compute_conjunctions,
    compute_graha_yuddha, conjunctions_to_dicts,
)
from .dignity import (
    dignity_flags, is_debilitated, is_exalted, is_moolatrikona, is_own_sign,
    natural_nature,
)
from .dispositors import (
    DispositorChain, all_dispositor_chains, dispositor_chain, dispositor_of,
    final_dispositors, find_parivartanas,
)
from .functional_nature import (
    FunctionalRole, functional_roles, lords_of_category, yogakarakas,
)
from .lordships import (
    DUSTHANA_HOUSES, KENDRA_HOUSES, MARAKA_HOUSES, TRIKONA_HOUSES,
    UPACHAYA_HOUSES, house_lords, house_lords_as_strings, house_of_sign,
    houses_owned, lord_of_sign, sign_of_house,
)
from .models import (
    Aspect, ChartFeatures, Conjunction, HouseFeatures, Parivartana,
    PlanetFeatures, VargaPlacement,
)
from .relationships import (
    compound_relationship, natural_relationship, relationship_table,
    sign_relationship, temporary_relationship,
)
from .varga_features import (
    KEY_VARGAS, compute_varga_features, is_vargottama, varga_house_of,
    varga_lagna, varga_lord, vargottama_in, vargottama_vargas,
)

__all__ = [
    "Aspect", "AspectProfile", "ChartFeatures", "Conjunction",
    "DEFAULT_ASPECT_PROFILE", "DEFAULT_ORB_DEG", "DUSTHANA_HOUSES",
    "DispositorChain", "FunctionalRole", "GrahaYuddha", "HouseFeatures",
    "KENDRA_HOUSES", "KEY_VARGAS", "MARAKA_HOUSES", "NODE_ASPECT_CONVENTIONS",
    "Parivartana", "PlanetFeatures", "TRIKONA_HOUSES", "UPACHAYA_HOUSES",
    "VargaPlacement", "all_dispositor_chains", "angular_separation",
    "aspects_to_dicts", "build_chart_features", "compound_relationship",
    "compute_aspects", "compute_conjunctions", "compute_graha_yuddha",
    "compute_varga_features", "conjunctions_to_dicts", "dignity_flags",
    "dispositor_chain", "dispositor_of", "final_dispositors",
    "find_parivartanas", "functional_roles", "house_lords",
    "house_lords_as_strings", "house_of_sign", "houses_owned", "is_debilitated",
    "is_exalted", "is_moolatrikona", "is_own_sign", "is_vargottama",
    "lord_of_sign", "lords_of_category", "natural_nature",
    "natural_relationship", "parashari_profile", "relationship_table",
    "sign_of_house", "sign_relationship", "temporary_relationship",
    "varga_house_of", "varga_lagna", "varga_lord", "vargottama_in",
    "vargottama_vargas", "yogakarakas",
]
