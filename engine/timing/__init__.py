"""
Timing engine
-------------
Vimshottari dasha as a standalone, deterministic calculation. It depends on
the Moon's longitude and the birth moment and on nothing else — in particular
it does not import the interpretation or rule layers, so timing can be tested,
reused and later driven by a transit engine without dragging anything with it.

    dasha = compute_vimshottari(moon_longitude, birth, depth=3)
    dasha.get_dasha_stack_at(datetime(2030, 6, 10))

The hierarchy is built by one generic subdivision routine, so Sukshma and
Prana need no new calculation — only a deeper `depth`.
"""

from .models import (
    DASHA_LEVELS, DASHA_SEQUENCE, DEFAULT_YEAR_LENGTH, ENGLISH_NAME,
    GREGORIAN_YEAR, JULIAN_YEAR, LEVEL_INDEX, NAKSHATRA_DASHA_LORD,
    SAVANA_YEAR, SIDEREAL_YEAR, TOTAL_YEARS, VIMSHOTTARI_YEARS, YEAR_LENGTHS,
    DashaPeriod, YearLength, next_level, year_length,
)
from .report import format_dasha_report
from .vimshottari import (
    VimshottariDasha, birth_dasha_lord, compute_vimshottari, elapsed_fraction,
    from_chart, nakshatra_index, subdivide,
)

__all__ = [
    "DASHA_LEVELS", "DASHA_SEQUENCE", "DEFAULT_YEAR_LENGTH", "ENGLISH_NAME",
    "GREGORIAN_YEAR", "JULIAN_YEAR", "LEVEL_INDEX", "NAKSHATRA_DASHA_LORD",
    "SAVANA_YEAR", "SIDEREAL_YEAR", "TOTAL_YEARS", "VIMSHOTTARI_YEARS",
    "YEAR_LENGTHS", "DashaPeriod", "VimshottariDasha", "YearLength",
    "birth_dasha_lord", "compute_vimshottari", "elapsed_fraction",
    "format_dasha_report", "from_chart", "nakshatra_index", "next_level",
    "subdivide", "year_length",
]
