"""
Birth-time sensitivity models (V1.4 Part 16)
----------------------------------------------
Facts about what changes near the stated birth time. No rectification, no
recommendation, no preferred time.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class UnstableItem:
    """One classification that changes within the window, and where."""

    item: str
    key: str
    baseline: Any
    changes_to: Any
    offset_seconds: int
    offset_text: str

    def describe(self) -> str:
        return (f"{self.item} changes at {self.offset_text} "
                f"({self.baseline} -> {self.changes_to})")

    def to_dict(self) -> dict:
        return {
            "item": self.item,
            "key": self.key,
            "baseline": self.baseline,
            "changes_to": self.changes_to,
            "offset_seconds": self.offset_seconds,
            "offset": self.offset_text,
            "description": self.describe(),
        }


@dataclass
class SensitivityWindow:
    """What is stable, and what is not, within one window."""

    window_minutes: int
    stable: bool
    changes: list[UnstableItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "window_minutes": self.window_minutes,
            "stable": self.stable,
            "changes": [c.describe() for c in self.changes],
            "detail": [c.to_dict() for c in self.changes],
        }


@dataclass
class SensitivityReport:
    """Sensitivity across every window tested."""

    birth_utc: datetime.datetime
    latitude: float
    longitude: float
    scan_step_seconds: int
    watched_vargas: list[str] = field(default_factory=list)
    bhava_system: Optional[str] = None
    windows: list[SensitivityWindow] = field(default_factory=list)
    baseline: dict = field(default_factory=dict)

    @property
    def tightest_stable_window(self) -> Optional[int]:
        """The largest window in which nothing changes, or None."""
        stable = [w.window_minutes for w in self.windows if w.stable]
        return max(stable) if stable else None

    @property
    def is_stable_anywhere(self) -> bool:
        return any(w.stable for w in self.windows)

    def to_dict(self) -> dict:
        return {
            "birth_utc": self.birth_utc.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "scan_step_seconds": self.scan_step_seconds,
            "watched_vargas": list(self.watched_vargas),
            "bhava_system": self.bhava_system,
            "largest_stable_window_minutes": self.tightest_stable_window,
            "windows": [w.to_dict() for w in self.windows],
            "note": (
                "Reports what changes near the stated birth time. This is "
                "NOT rectification: no time is suggested, preferred or "
                "scored. A classification listed as unstable depends on the "
                "recorded clock time as much as on the sky."),
        }
