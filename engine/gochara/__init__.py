"""
Gochara: textual transit rules (V1.8 Parts 1-7)
------------------------------------------------
Transit JUDGEMENT, kept apart from the transit FACTS in `engine.transits`.

    engine.transits    where a graha is, and what it touches.
                       ASTRONOMICAL FACT, externally benchmarked.

    engine.gochara     whether a located verse calls that placement
                       favourable, and whether an obstruction cancels it.
                       TEXTUAL RULE, source-located, implementation-matched.

The separation is load-bearing. The positions being correct to the
arcsecond is not evidence about what Phaladīpikā says, and a single module
holding both would let the second silently inherit the first's benchmark.
"""

from .engine import (
    STRENGTH_MEASURE, STRENGTH_THRESHOLD, STRICT_REQUIREMENTS,
    evaluate_dasha_lord, evaluate_gochara, evaluate_moon_frame,
    strict_eligible_judgements,
)
from .models import (
    GocharaActivation, GocharaJudgement, GocharaPlacement, GocharaResult,
    GocharaRule, GocharaVerdict, NatalStrengthCondition, TransitReference,
    VedhaResult, WitnessAgreement,
)
from .rules import (
    DASHA_LORD_RULE, GOCHARA_PROFILE, METHODOLOGY_ID, MOON_FRAME_RULES,
    NODE_RULES, RULE_DASHA_LORD, RULE_MOON_FRAME, UNIMPLEMENTED_LAYERS,
    all_rules, moon_frame_rule, rule_summary,
)
from .vedha import (
    NODES_CAUSE_VEDHA_DEFAULT, NODE_VEDHA_NOTE, evaluate_vedha, vedha_table,
)

__all__ = [
    "DASHA_LORD_RULE", "GOCHARA_PROFILE", "GocharaActivation",
    "GocharaJudgement", "GocharaPlacement", "GocharaResult", "GocharaRule",
    "GocharaVerdict", "METHODOLOGY_ID", "MOON_FRAME_RULES",
    "NODES_CAUSE_VEDHA_DEFAULT", "NODE_RULES", "NODE_VEDHA_NOTE",
    "NatalStrengthCondition", "RULE_DASHA_LORD", "RULE_MOON_FRAME",
    "STRENGTH_MEASURE", "STRENGTH_THRESHOLD", "STRICT_REQUIREMENTS",
    "TransitReference", "UNIMPLEMENTED_LAYERS", "VedhaResult",
    "WitnessAgreement", "all_rules", "evaluate_dasha_lord",
    "evaluate_gochara", "evaluate_moon_frame", "evaluate_vedha",
    "moon_frame_rule", "rule_summary", "strict_eligible_judgements",
    "vedha_table",
]
