"""
The engine boundary (V1.7 Parts 1, 2, 37)
===========================================
The tests that stop the UI and the report writer becoming a second
astrology engine.

WHY THIS IS AN IMPORT-GRAPH TEST AND NOT A CODE REVIEW

    "Do not calculate astrology in the UI" is a rule nobody breaks on
    purpose. It gets broken by one reasonable-looking line — a template
    that needs a house number and works it out with `(sign - lagna) % 12`,
    a report that needs a dignity and asks the chart for one — and the
    second implementation then drifts from the first, silently, because
    nothing compares them.

    An import is the thing that has to happen first. `app/visual`,
    `app/report` and `app/ui` cannot reach the engine at all, so the
    shortest path to a second implementation is closed before anyone takes
    it. The services may import the engine: that is their job.

THE SECOND TEST HERE

    Parsing imports catches `from engine...`. It does not catch a renderer
    that is handed a live engine object by a caller and reaches through it.
    So the renderers are also exercised against plain dictionaries read
    back from JSON, which cannot answer a question that was not written
    down.
"""

from __future__ import annotations

import ast
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

APP_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")

#: Packages that may import the engine, and the reason each may.
MAY_IMPORT_ENGINE = {
    "app/services": "the adapter layer; this is what it is for",
    "app/benchmark.py": "times engine entry points directly",
}

#: Packages that may not, on any path.
MUST_NOT_IMPORT_ENGINE = ("app/visual", "app/report", "app/ui")


def _python_files(root: str):
    for directory, _dirs, files in os.walk(root):
        if "__pycache__" in directory:
            continue
        for name in sorted(files):
            if name.endswith(".py"):
                yield os.path.join(directory, name)


def _imports(path: str) -> set[str]:
    """Every module name imported by a file, including inside functions."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:                 # relative import, never the engine
                continue
            if node.module:
                found.add(node.module)
    return found


def _relative(path: str) -> str:
    return os.path.relpath(path, os.path.dirname(APP_ROOT)).replace("\\", "/")


class ImportBoundaryTest(unittest.TestCase):

    def test_presentation_layers_cannot_import_the_engine(self):
        offenders = []
        for package in MUST_NOT_IMPORT_ENGINE:
            root = os.path.join(os.path.dirname(APP_ROOT), package)
            self.assertTrue(os.path.isdir(root), f"{package} is missing")
            for path in _python_files(root):
                for module in _imports(path):
                    if module == "engine" or module.startswith("engine."):
                        offenders.append(f"{_relative(path)} imports {module}")
        self.assertEqual(
            offenders, [],
            "A presentation layer reached the engine. The fix is to put the "
            "value it needs on the snapshot or the visual model, never to "
            "compute it where it is drawn.")

    def test_the_service_layer_is_the_only_adapter(self):
        """Something must import the engine, or the boundary is a wall."""
        importers = set()
        for path in _python_files(APP_ROOT):
            for module in _imports(path):
                if module == "engine" or module.startswith("engine."):
                    importers.add(_relative(path))
        self.assertTrue(importers, "no part of app/ reaches the engine")
        for path in sorted(importers):
            with self.subTest(path=path):
                self.assertTrue(
                    any(path.startswith(allowed)
                        for allowed in MAY_IMPORT_ENGINE),
                    f"{path} imports the engine but is not an adapter. "
                    f"Allowed: {', '.join(sorted(MAY_IMPORT_ENGINE))}.")

    def test_the_ui_reaches_the_engine_only_through_services(self):
        """
        A UI module may import `app.services`; it may not import
        `app.services.chart_service`'s engine helpers or anything else that
        would let it assemble a calculation of its own.
        """
        root = os.path.join(os.path.dirname(APP_ROOT), "app/ui")
        for path in _python_files(root):
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                names = [a.name for a in node.names]
                if node.module and "engine" in (node.module or ""):
                    self.fail(f"{_relative(path)} imports {node.module}")
                with self.subTest(path=_relative(path), names=names):
                    self.assertNotIn(
                        "JyotishChart", names,
                        "the UI must never hold a chart object")


class NoCalculationLeakageTest(unittest.TestCase):
    """
    The renderers work from data, and a dict cannot be asked a question.

    Each of these passes a snapshot through `json.dumps`/`json.loads`
    first. A renderer that had quietly come to depend on an engine object
    — a method call, an attribute that is a property, a lazily computed
    field — fails on the round trip rather than in production.
    """

    @classmethod
    def setUpClass(cls):
        from app.models import ConsultationRecord
        from app.services import calculate_chart

        cls.record = ConsultationRecord(
            name="Boundary", date_of_birth="1988-08-30",
            time_of_birth="20:18", place="Jaipur")
        cls.natal = calculate_chart(cls.record)
        cls.plain = json.loads(json.dumps(cls.natal.snapshot))

    def test_the_visual_model_builds_from_a_serialised_snapshot(self):
        from app.services.visual_builder import build_visual_model
        model = build_visual_model(self.plain, varga="D9")
        self.assertEqual(model.chart_name, "D9")
        self.assertEqual(len(model.houses), 12)
        self.assertTrue(model.bodies())

    def test_the_chart_renderer_never_sees_an_engine_object(self):
        from app.services.visual_builder import build_visual_model
        from app.visual import render_north_indian, scene_to_svg

        scene = render_north_indian(build_visual_model(self.plain))
        svg = scene_to_svg(scene)
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)

    def test_the_report_builds_from_serialised_snapshots(self):
        from app.report import build_report_document
        document = build_report_document(natal=self.plain, mode="detailed")
        self.assertTrue(document.sections)
        # And the document itself survives the same round trip.
        json.loads(document.to_json())

    def test_the_visual_model_is_frozen(self):
        """
        A settings change must never edit a computed model in place
        (Part 30). Freezing is what makes that structural.
        """
        from app.services.visual_builder import build_visual_model
        model = build_visual_model(self.plain)
        with self.assertRaises(Exception):
            model.chart_name = "D9"          # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
