"""
Birth-time sensitivity (V1.4 Part 16)
---------------------------------------
    report = analyse_birth_time(birth_utc, latitude, longitude)
    report.windows[0].stable
    report.tightest_stable_window

Reports which classifications change within a window of the stated birth
time. Explicitly NOT rectification: no time is suggested or scored.
"""

from .birth_time import (
    DEFAULT_WINDOWS, SCAN_STEP_SECONDS, WATCHED_VARGAS, analyse_birth_time,
)
from .models import SensitivityReport, SensitivityWindow, UnstableItem
from .report import format_sensitivity_report

__all__ = [
    "DEFAULT_WINDOWS", "SCAN_STEP_SECONDS", "SensitivityReport",
    "SensitivityWindow", "UnstableItem", "WATCHED_VARGAS",
    "analyse_birth_time", "format_sensitivity_report",
]
