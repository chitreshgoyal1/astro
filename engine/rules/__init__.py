"""
Yoga rule engine
----------------
Declarative, sourced classical combinations evaluated against a ChartFeatures.

    features = build_chart_features(chart)       # engine.features
    results  = evaluate_rules(features)

The engine consumes facts and never derives them. Every result carries the
rule's source, the clauses that matched, the clauses that failed, any
cancellation that applied, and the modifiers that set its strength band.
"""

from .catalog import (
    DEFAULT_PROFILE, DHANA_HOUSES, MAHAPURUSHA, RULE_PROFILES, all_rules,
    rule_by_id, rules_for_profile,
)
from .conditions import Condition, ConditionResult
from .engine import (
    Modifier, YogaResult, YogaRule, YogaStatus, evaluate_rule, evaluate_ruleset,
)
from ..features.models import ChartFeatures


def evaluate_rules(features: ChartFeatures,
                   profile: str = DEFAULT_PROFILE) -> list[YogaResult]:
    """Evaluate a named rule profile against a chart's features."""
    return evaluate_ruleset(rules_for_profile(profile), features,
                            rule_profile=profile)


def present_yogas(features: ChartFeatures,
                  profile: str = DEFAULT_PROFILE) -> list[YogaResult]:
    """Only the combinations that actually formed, cancelled or not."""
    return [r for r in evaluate_rules(features, profile) if r.present]


__all__ = [
    "Condition", "ConditionResult", "DEFAULT_PROFILE", "DHANA_HOUSES",
    "MAHAPURUSHA", "Modifier", "RULE_PROFILES", "YogaResult", "YogaRule",
    "YogaStatus", "all_rules", "evaluate_rule", "evaluate_rules",
    "evaluate_ruleset", "present_yogas", "rule_by_id", "rules_for_profile",
]
