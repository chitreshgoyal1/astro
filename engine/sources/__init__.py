"""
Source and provenance layer (V1.3)
-----------------------------------
Answers, for any shipped rule: what evidence stands behind this, and how far
has it actually been traced?

    from engine.sources import evidence_for, strict_profile_eligible

    evidence = evidence_for("sunapha")
    evidence.validation_status        # ValidationStatus.IMPLEMENTATION_MATCHED
    witnesses_for("sunapha")          # [SourceWitness(Bṛhajjātaka 13.3)]

Four claims are kept permanently separate, and nothing here lets one stand in
for another:

    COMPUTATIONALLY TESTED      the code does what we told it to
    EXTERNALLY BENCHMARKED      the numbers match an independent reference
    TEXTUAL SOURCE LOCATED      a specific passage in a specific witness exists
    TRADITION/SOURCE VALIDATED  that passage actually states this rule

As of V1.3 the engine asserts the fourth for NOTHING. One Sanskrit witness has
been obtained (Bṛhajjātaka) covering five passages; every other rule is
UNVERIFIED and says so.
"""

from .editions import (
    ALL_WITNESSES, BPHS_SANSKRIT_SD, BRIHAJJATAKA_GRETIL, JATAKA_PARIJATA_SD,
    PHALADEEPIKA_SD, QUOTATION_WITNESSES, RESOLVED_UNAVAILABLE_WORKS,
    UNAVAILABLE_WORKS, sanskrit_tier_witnesses, witness_by_id,
)
from .models import (
    CLASSIFICATION_MEANING, STATUS_MEANING, ReviewItem, ReviewReason,
    RuleClassification, RuleEvidence, SourceAuthority, SourceConflict,
    SourceType, SourceWitness, ValidationStatus,
)
from .review import (
    REVIEW_TASKS, ReviewStage, ReviewTask, SourceAvailability,
    can_register_witness, review_summary, task_for, tasks_needing_a_reader,
)
from .registry import (
    AUDIT_RELEASE, CONFLICTS, REGISTRY_VERSION, REVIEW_QUEUE, REVIEWED_ON,
    all_recorded_evidence, all_witnesses, conflict_by_id, evidence_for,
    family_of, has_recorded_evidence, registry_summary, witnesses_for,
)
from .validation import (
    STRICT_PROFILE_MINIMUM, STRICT_PROFILE_REQUIREMENTS, check_status,
    highest_supportable_status, overclaimed, strict_profile_eligible,
    unmet_requirements,
)

__all__ = [
    "REVIEW_TASKS",
    "ReviewStage",
    "ReviewTask",
    "SourceAvailability",
    "can_register_witness",
    "review_summary",
    "task_for",
    "tasks_needing_a_reader",
    "ALL_WITNESSES", "AUDIT_RELEASE", "BPHS_SANSKRIT_SD",
    "BRIHAJJATAKA_GRETIL", "CLASSIFICATION_MEANING", "JATAKA_PARIJATA_SD",
    "PHALADEEPIKA_SD", "QUOTATION_WITNESSES", "RESOLVED_UNAVAILABLE_WORKS",
    "family_of",
    "CONFLICTS", "REGISTRY_VERSION", "REVIEWED_ON", "REVIEW_QUEUE",
    "STATUS_MEANING", "STRICT_PROFILE_MINIMUM", "STRICT_PROFILE_REQUIREMENTS",
    "UNAVAILABLE_WORKS", "ReviewItem", "ReviewReason", "RuleClassification",
    "RuleEvidence", "SourceAuthority", "SourceConflict", "SourceType",
    "SourceWitness", "ValidationStatus", "all_recorded_evidence",
    "all_witnesses", "check_status", "conflict_by_id", "evidence_for",
    "has_recorded_evidence", "highest_supportable_status", "overclaimed",
    "registry_summary", "sanskrit_tier_witnesses", "strict_profile_eligible",
    "unmet_requirements", "witness_by_id", "witnesses_for",
]
