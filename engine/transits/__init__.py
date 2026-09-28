"""
Transit engine (V1.4 Parts 17-20)
-----------------------------------
    snapshot = get_transit_snapshot(moment, natal_chart=chart)
    events   = get_transit_events_between(start, end)
    context  = build_timing_context(moment, natal_snapshot, dasha, chart)

Deterministic positions and factual relationships, reusing the natal
ephemeris rather than a second implementation. No Gochara rules, no
benefic/malefic judgement, no prediction — those need sources first.
"""

from .calculator import compute_transit_positions, get_transit_snapshot
from .models import (
    EVENT_KINDS, TransitEvent, TransitNatalRelationship, TransitPosition,
    TransitSnapshot,
)
from .query import (
    SCAN_STEP_HOURS, get_transit_events_between, get_transits_between,
)
from .relationships import compute_relationships, significant_relationships
from .report import format_events, format_transit_report
from .timing_context import TimingContext, build_timing_context

__all__ = [
    "EVENT_KINDS", "SCAN_STEP_HOURS", "TimingContext", "TransitEvent",
    "TransitNatalRelationship", "TransitPosition", "TransitSnapshot",
    "build_timing_context", "compute_relationships",
    "compute_transit_positions", "format_events", "format_transit_report",
    "get_transit_events_between", "get_transit_snapshot",
    "get_transits_between", "significant_relationships",
]
