"""
User interface (V1.7 Parts 1, 5, 33, 34, 36)
==============================================
    python main.py --app

A local server, screens rendered as HTML, charts as inline SVG. It binds to
loopback, fetches nothing, and stores nothing outside the machine it runs
on.

This package imports the application services and nothing from `engine`;
`tests/test_app_boundary.py` enforces it. The interface is presentation and
input orchestration. Every astrological answer on every screen was decided
by the engine and arrives already made.
"""

from .assets import STYLESHEET
from .pages import SCREENS, consultation_form, page
from .server import DEFAULT_PORT, HOST, Application, serve

__all__ = [
    "Application", "DEFAULT_PORT", "HOST", "SCREENS", "STYLESHEET",
    "consultation_form", "page", "serve",
]
