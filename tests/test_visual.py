"""
Chart visuals (V1.7 Parts 6, 7, 8, 10, 36, 37, 38)
====================================================
The visual model, the North Indian layout, the SVG backend, and the
deterministic fixtures that pin them.

THE ONE THING THESE TESTS ARE REALLY CHECKING

    That changing how a chart LOOKS cannot change what it SAYS.

    Style, detail level, font size and the backend are all presentation.
    A test that only checked the SVG parsed would pass while a renderer
    quietly dropped a graha out of a crowded house, so the checks are on
    the contents: every body placed, every house accounted for, the same
    twelve houses in the text equivalent as in the picture.

VISUAL REGRESSION (Part 38)

    Structural rather than pixel-based. A scene is a tuple of frozen
    elements with rounded coordinates and no timestamp, so its hash is a
    usable fixture and a changed hash means the geometry changed — not
    that the machine did.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import ConsultationRecord
from app.services import calculate_chart, chart_visual_model
from app.services.visual_builder import build_visual_model
from app.visual import (
    CHART_STYLES, DETAIL_LEVELS, IMPLEMENTED_STYLES, ChartVisualModel,
    HouseCell, PlacedBody, Scene, UnsupportedChartStyle, describe,
    house_cell_map, render_chart, render_north_indian, render_south_indian,
    scene_to_svg, scene_to_svg_document,
)
from app.visual.north_indian import MARKER_LEGEND, _polygons
from app.visual.south_indian import CENTRE_CELLS, SIGN_CELLS

JAIPUR = dict(name="Jaipur 1988", date_of_birth="1988-08-30",
              time_of_birth="20:18", place="Jaipur")


def _synthetic(bodies_in_house: dict, lagna_sign: int = 0
               ) -> ChartVisualModel:
    """
    A model built by hand, for the cases a real chart does not supply.

    Seven grahas in one house happens; it did not happen in the regression
    chart, and waiting for a birth that produces one is not a test
    strategy.
    """
    signs = ("Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
             "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena")
    cells = []
    for number in range(1, 13):
        sign = (lagna_sign + number - 1) % 12
        cells.append(HouseCell(
            number=number, sign_index=sign, sign_name=signs[sign],
            bodies=tuple(bodies_in_house.get(number, ()))))
    return ChartVisualModel(
        chart_name="D1", title="Rashi (D1)", lagna_sign=lagna_sign,
        lagna_sign_name=signs[lagna_sign], houses=tuple(cells),
        subject="Synthetic")


class _Chart(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.natal = calculate_chart(ConsultationRecord(**JAIPUR))
        cls.snapshot = json.loads(json.dumps(cls.natal.snapshot))


# ── Part 7: the model ────────────────────────────────────────────────────────

class VisualModelTest(_Chart):

    def test_every_graha_is_placed_exactly_once(self):
        """
        The failure this catches is a chart that is wrong in a way the
        reader cannot see: a graha dropped, or drawn in two houses.
        """
        model = chart_visual_model(self.natal)
        placed = [b.name for b in model.bodies() if not b.is_lagna]
        self.assertEqual(sorted(placed), sorted(set(placed)))
        self.assertEqual(set(placed), set(self.snapshot["planets"]))

    def test_the_lagna_is_always_in_the_first_house(self):
        for varga in ("D1", "D9", "D10", "D60"):
            with self.subTest(varga=varga):
                model = chart_visual_model(self.natal, varga=varga)
                lagna = [b for b in model.bodies() if b.is_lagna]
                self.assertEqual(len(lagna), 1)
                self.assertEqual(lagna[0].house, 1)

    def test_d1_houses_agree_with_the_snapshot(self):
        """The model reads the engine's house assignment; it does not
        recompute one."""
        model = chart_visual_model(self.natal)
        for name, entry in self.snapshot["planets"].items():
            with self.subTest(planet=name):
                body = next(b for b in model.bodies() if b.name == name)
                self.assertEqual(body.house, entry["house"])
                self.assertEqual(body.sign_index, entry["sign_index"])

    def test_varga_houses_use_the_engine_s_own_counting(self):
        from engine.features.varga_features import varga_house_of
        model = chart_visual_model(self.natal, varga="D9")
        placements = self.snapshot["vargas"]["bodies"]
        for body in model.bodies():
            if body.is_lagna:
                continue
            with self.subTest(planet=body.name):
                sign = placements[body.name]["D9"]["sign_index"]
                self.assertEqual(
                    body.house, varga_house_of(sign, model.lagna_sign))

    def test_a_varga_placement_carries_no_degree(self):
        """
        A division maps a RANGE of degrees onto a whole sign. Printing a
        degree in a D9 would invent a precision the calculation does not
        have.
        """
        model = chart_visual_model(self.natal, varga="D9")
        for body in model.bodies():
            with self.subTest(planet=body.name):
                self.assertIsNone(body.degree)

    def test_d1_placements_do_carry_a_degree(self):
        model = chart_visual_model(self.natal, varga="D1")
        degrees = [b.degree for b in model.bodies() if not b.is_lagna]
        self.assertTrue(all(d is not None for d in degrees))

    def test_an_unknown_varga_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            chart_visual_model(self.natal, varga="D11")
        self.assertIn("D11", str(caught.exception))

    def test_an_unknown_detail_level_is_refused(self):
        with self.assertRaises(ValueError):
            chart_visual_model(self.natal, detail="ENORMOUS")

    def test_the_model_records_which_convention_produced_it(self):
        model = chart_visual_model(self.natal, varga="D30")
        self.assertTrue(model.convention)

    def test_an_unstable_varga_carries_its_warning_on_the_chart(self):
        """
        Part 10. A D60 that moves inside the recorded precision is not a
        precise value; the note travels on the model so the warning is
        drawn beside the chart rather than left in a panel.
        """
        record = ConsultationRecord(**JAIPUR)
        natal = calculate_chart(record)
        model = chart_visual_model(natal, varga="D60")
        self.assertTrue(model.notes)
        self.assertTrue(any("D60" in note for note in model.notes))

    def test_the_model_serialises(self):
        model = chart_visual_model(self.natal, varga="D10")
        json.loads(json.dumps(model.to_dict()))


# ── Part 6, 8: the layout ────────────────────────────────────────────────────

class NorthIndianLayoutTest(_Chart):

    def test_the_twelve_regions_tile_the_square(self):
        """
        Areas summing to the square is the check that the diagram is the
        diagram: no overlap, no gap, no region left out.
        """
        def area(points):
            total = 0.0
            for index in range(len(points)):
                x1, y1 = points[index]
                x2, y2 = points[(index + 1) % len(points)]
                total += x1 * y2 - x2 * y1
            return abs(total) / 2

        size = 400.0
        regions = _polygons(size, size)
        self.assertEqual(sorted(regions), list(range(1, 13)))
        self.assertAlmostEqual(sum(area(p) for p in regions.values()),
                               size * size, places=6)

    def test_every_body_gets_a_label(self):
        model = chart_visual_model(self.natal)
        scene = render_north_indian(model)
        labels = [t for t in scene.texts() if t.role == "body"]
        self.assertEqual(len(labels), len(model.bodies()))

    def test_every_label_lands_inside_the_square(self):
        """
        The bug this exists for: the first version pushed corner-region
        text AWAY from the centre, and half the labels came out on or past
        the border. A centroid near the edge has room in one direction
        only.
        """
        size = 420.0
        model = chart_visual_model(self.natal, detail="DETAILED")
        scene = render_north_indian(model, size=size)
        for text in scene.texts():
            with self.subTest(text=text.text):
                self.assertGreater(text.x, 4.0)
                self.assertLess(text.x, size - 4.0)
                self.assertGreater(text.y, 4.0)
                self.assertLess(text.y, size - 4.0)

    def test_a_crowded_house_shrinks_rather_than_overflowing(self):
        """Part 8: seven bodies in one house must still fit."""
        crowded = _synthetic({1: [
            PlacedBody(name=n, display=n[:2], house=1, sign_index=0)
            for n in ("Surya", "Chandra", "Mangal", "Budha", "Guru",
                      "Shukra", "Shani")]})
        self.assertTrue(crowded.is_crowded)
        roomy = _synthetic({1: [PlacedBody(name="Surya", display="Su",
                                           house=1, sign_index=0)]})
        tight = render_north_indian(crowded)
        loose = render_north_indian(roomy)
        crowded_size = min(t.size for t in tight.texts() if t.role == "body")
        roomy_size = min(t.size for t in loose.texts() if t.role == "body")
        self.assertLess(crowded_size, roomy_size)
        self.assertEqual(
            len([t for t in tight.texts() if t.role == "body"]), 7,
            "no graha may be dropped to make room")

    def test_retrograde_is_printed_and_not_only_coloured(self):
        """Part 36: colour is never the only encoding."""
        model = _synthetic({1: [PlacedBody(
            name="Shani", display="Sa", house=1, sign_index=0,
            retrograde=True)]})
        scene = render_north_indian(model)
        label = next(t for t in scene.texts() if t.role == "body")
        self.assertIn("R", label.text)

    def test_dignity_markers_are_printable_text(self):
        for dignity, marker in (("exalted", "^"), ("debilitated", "v"),
                                ("moolatrikona", "mt"), ("own", "sv")):
            with self.subTest(dignity=dignity):
                model = _synthetic({1: [PlacedBody(
                    name="Guru", display="Gu", house=1, sign_index=0,
                    dignity_marker=dignity)]})
                scene = render_north_indian(model)
                label = next(t for t in scene.texts() if t.role == "body")
                self.assertIn(marker, label.text)
                self.assertTrue(label.text.isascii(),
                                "must survive the PDF's Latin encoding")

    def test_the_marker_legend_explains_every_marker_used(self):
        for marker in ("R", "c", "^", "v", "mt", "sv"):
            with self.subTest(marker=marker):
                self.assertIn(marker, MARKER_LEGEND)

    def test_the_rashi_number_identifies_the_sign(self):
        """
        A North Indian chart's houses are fixed on the page and the signs
        move through them, so the number is not decoration.
        """
        model = chart_visual_model(self.natal)
        scene = render_north_indian(model)
        numbers = sorted(int(t.text) for t in scene.texts()
                         if t.role == "sign_number")
        self.assertEqual(numbers, list(range(1, 13)))

    def test_another_style_is_refused_rather_than_approximated(self):
        """
        Part 6: chart style is presentation and must never change a
        calculation. A chart drawn in the wrong style is misread rather
        than disbelieved, so the layout refuses.
        """
        model = chart_visual_model(self.natal)
        south = ChartVisualModel(
            chart_name=model.chart_name, title=model.title,
            lagna_sign=model.lagna_sign,
            lagna_sign_name=model.lagna_sign_name, houses=model.houses,
            style="south_indian")
        with self.assertRaises(ValueError) as caught:
            render_north_indian(south)
        self.assertIn("presentation only", str(caught.exception))
        self.assertIn("south_indian", CHART_STYLES)

    def test_a_layout_refuses_the_other_layouts_model(self):
        """
        The refusal is mutual. Each layout is told which style it draws
        and declines anything else, so a caller who mixes them up gets a
        named error rather than a chart in the wrong convention.
        """
        model = chart_visual_model(self.natal, style="south_indian")
        with self.assertRaises(ValueError):
            render_north_indian(model)
        north = chart_visual_model(self.natal, style="north_indian")
        with self.assertRaises(ValueError):
            render_south_indian(north)

    def test_detail_changes_labels_and_never_placements(self):
        placements = {}
        for detail in DETAIL_LEVELS:
            model = chart_visual_model(self.natal, detail=detail)
            placements[detail] = sorted(
                (b.name, b.house) for b in model.bodies())
        self.assertEqual(placements["COMPACT"], placements["DETAILED"])
        self.assertEqual(placements["COMPACT"], placements["STANDARD"])


# ── Part 36: the text equivalent ─────────────────────────────────────────────

class AccessibilityTest(_Chart):

    def test_the_description_lists_the_same_houses_as_the_picture(self):
        model = chart_visual_model(self.natal)
        text = describe(model)
        for cell in model.houses:
            if not cell.bodies:
                continue
            with self.subTest(house=cell.number):
                self.assertIn(f"House {cell.number}", text)
                for body in cell.bodies:
                    self.assertIn(body.name, text)

    def test_the_description_spells_out_what_the_markers_abbreviate(self):
        model = _synthetic({1: [PlacedBody(
            name="Shani", display="Sa", house=1, sign_index=0,
            retrograde=True, dignity_marker="exalted")]})
        text = describe(model)
        self.assertIn("retrograde", text)
        self.assertIn("exalted", text)

    def test_the_svg_is_labelled_for_a_screen_reader(self):
        scene = render_north_indian(chart_visual_model(self.natal))
        svg = scene_to_svg(scene, element_id="k")
        self.assertIn('role="img"', svg)
        self.assertIn('aria-labelledby="k-title k-desc"', svg)
        self.assertIn("<title id=\"k-title\">", svg)
        self.assertIn("<desc id=\"k-desc\">", svg)

    def test_the_svg_scales_with_its_container(self):
        """
        Part 36 asks for scalable text. Width and height live only in the
        viewBox, so the same markup serves a thumbnail and a full page.
        """
        svg = scene_to_svg(render_north_indian(chart_visual_model(self.natal)))
        self.assertIn("viewBox=", svg)
        self.assertNotIn("<svg width=", svg)


# ── Part 38: deterministic fixtures ──────────────────────────────────────────

class VisualRegressionTest(_Chart):

    def test_a_scene_hash_is_stable_across_runs(self):
        model = chart_visual_model(self.natal, varga="D9")
        first = render_north_indian(model).content_hash()
        second = render_north_indian(
            chart_visual_model(self.natal, varga="D9")).content_hash()
        self.assertEqual(first, second)

    def test_the_hash_covers_no_timestamp_or_identity(self):
        """
        Part 38: insignificant metadata must not make a snapshot
        non-deterministic. The scene carries none, so this checks that
        nothing crept in.
        """
        scene = render_north_indian(chart_visual_model(self.natal))
        payload = json.dumps(scene.to_dict())
        for forbidden in ("generated", "timestamp", "0x", "object at"):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_the_hash_changes_when_the_picture_changes(self):
        one = render_north_indian(chart_visual_model(self.natal, varga="D1"))
        nine = render_north_indian(chart_visual_model(self.natal, varga="D9"))
        self.assertNotEqual(one.content_hash(), nine.content_hash())

    def test_svg_output_is_byte_identical_for_one_scene(self):
        scene = render_north_indian(chart_visual_model(self.natal))
        self.assertEqual(scene_to_svg(scene), scene_to_svg(scene))

    def test_the_svg_document_is_well_formed(self):
        import xml.etree.ElementTree as ET
        for varga in ("D1", "D9", "D10"):
            with self.subTest(varga=varga):
                scene = render_north_indian(
                    chart_visual_model(self.natal, varga=varga))
                ET.fromstring(scene_to_svg_document(scene))

    def test_a_crowded_chart_renders_and_pins(self):
        crowded = _synthetic({1: [
            PlacedBody(name=n, display=n[:2], house=1, sign_index=0,
                       retrograde=(n == "Shani"))
            for n in ("Surya", "Chandra", "Mangal", "Budha", "Guru",
                      "Shukra", "Shani")]})
        scene = render_north_indian(crowded)
        self.assertEqual(scene.content_hash(),
                         render_north_indian(crowded).content_hash())
        import xml.etree.ElementTree as ET
        ET.fromstring(scene_to_svg_document(scene))


if __name__ == "__main__":
    unittest.main()


# ── Part 20: the two styles describe one chart ─────────────────────────────

class StyleEquivalenceTest(unittest.TestCase):
    """
    Part 19: "This is PRESENTATION ONLY. Do not recalculate houses or
    signs." That is a claim, and a claim about drawing code is worth
    exactly as much as the test that checks it.

    So every graha's sign, house and marker is compared across both
    styles, for several divisional charts. If the South Indian renderer
    ever grew arithmetic of its own — a rotation, an offset, a "house
    from Lagna" — these would diverge.
    """

    @classmethod
    def setUpClass(cls):
        record = ConsultationRecord(**JAIPUR)
        cls.natal = calculate_chart(record, record.settings)

    def _model(self, style, varga="D1"):
        return chart_visual_model(self.natal, varga=varga, style=style)

    def test_every_placement_is_identical_across_styles(self):
        for varga in ("D1", "D9", "D10", "D60"):
            north = self._model("north_indian", varga)
            south = self._model("south_indian", varga)
            with self.subTest(varga=varga):
                self.assertEqual(
                    [(b.name, b.house, b.sign_index, b.sign_name,
                      b.dignity_marker, b.retrograde, b.combust)
                     for b in north.bodies()],
                    [(b.name, b.house, b.sign_index, b.sign_name,
                      b.dignity_marker, b.retrograde, b.combust)
                     for b in south.bodies()])

    def test_every_house_holds_the_same_sign_in_both_styles(self):
        north = self._model("north_indian")
        south = self._model("south_indian")
        self.assertEqual(
            [(c.number, c.sign_index, c.sign_name, c.lord)
             for c in north.houses],
            [(c.number, c.sign_index, c.sign_name, c.lord)
             for c in south.houses])

    def test_the_lagna_sign_is_the_same_in_both_styles(self):
        self.assertEqual(self._model("north_indian").lagna_sign,
                         self._model("south_indian").lagna_sign)

    def test_the_two_styles_produce_different_pictures(self):
        """
        The other half of the claim. Identical placements drawn
        identically would mean the style setting does nothing.
        """
        north = render_chart(self._model("north_indian"))
        south = render_chart(self._model("south_indian"))
        self.assertNotEqual(north.content_hash(), south.content_hash())

    def test_both_styles_describe_the_chart_in_the_same_words(self):
        """
        `Scene.description` is the text equivalent a reader who cannot see
        the picture receives. It describes the CHART, not the drawing, so
        it must not depend on the style at all.
        """
        self.assertEqual(
            render_chart(self._model("north_indian")).description,
            render_chart(self._model("south_indian")).description)


class SouthIndianLayoutTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        record = ConsultationRecord(**JAIPUR)
        cls.natal = calculate_chart(record, record.settings)
        cls.model = chart_visual_model(cls.natal, style="south_indian")

    def test_the_twelve_signs_occupy_twelve_distinct_cells(self):
        self.assertEqual(len(SIGN_CELLS), 12)
        self.assertEqual(len(set(SIGN_CELLS.values())), 12)

    def test_no_sign_is_placed_in_the_open_centre(self):
        self.assertFalse(set(SIGN_CELLS.values()) & CENTRE_CELLS)

    def test_the_grid_is_exactly_four_by_four(self):
        cells = set(SIGN_CELLS.values()) | set(CENTRE_CELLS)
        self.assertEqual(
            cells, {(r, c) for r in range(4) for c in range(4)})

    def test_the_signs_run_clockwise_from_mesha(self):
        """
        Mesha at the top row, second cell, and each following sign one
        step clockwise around the ring. Checked as adjacency rather than
        by restating the table, so this test would still catch a table
        that was internally consistent and rotated.
        """
        self.assertEqual(SIGN_CELLS[0], (0, 1))
        for index in range(12):
            here = SIGN_CELLS[index]
            nxt = SIGN_CELLS[(index + 1) % 12]
            step = (abs(here[0] - nxt[0]), abs(here[1] - nxt[1]))
            with self.subTest(sign=index):
                self.assertIn(step, ((0, 1), (1, 0)),
                              "consecutive signs must be adjacent cells")

    def test_the_houses_run_clockwise_from_the_lagna_cell(self):
        mapping = house_cell_map(self.model)
        lagna_cell = SIGN_CELLS[self.model.lagna_sign]
        self.assertEqual(mapping[1], lagna_cell)
        for house in range(1, 13):
            expected = SIGN_CELLS[(self.model.lagna_sign + house - 1) % 12]
            with self.subTest(house=house):
                self.assertEqual(mapping[house], expected)

    def test_the_lagna_cell_is_marked_by_more_than_one_channel(self):
        """
        Part 36: status is never encoded by one channel alone. The Lagna
        cell carries a stroke AND a bold, differently coloured label.
        """
        scene = render_chart(self.model)
        strokes = [e for e in scene.elements
                   if type(e).__name__ == "Line"]
        self.assertTrue(strokes, "expected the Lagna corner stroke")
        bold = [e for e in scene.elements
                if type(e).__name__ == "Text"
                and getattr(e, "weight", "") == "bold"]
        self.assertTrue(bold, "expected a bold Lagna label")

    def test_house_numbers_are_printed_because_the_signs_are_fixed(self):
        scene = render_chart(self.model)
        numbers = sorted(
            e.text for e in scene.elements
            if type(e).__name__ == "Text"
            and getattr(e, "role", "") == "house_number")
        self.assertEqual(numbers, sorted(str(n) for n in range(1, 13)))

    def test_the_scene_is_deterministic(self):
        self.assertEqual(render_chart(self.model).content_hash(),
                         render_chart(self.model).content_hash())

    def test_a_crowded_cell_shrinks_rather_than_overflowing(self):
        crowded = _synthetic({1: [
            PlacedBody(name=n, display=n[:2], house=1, sign_index=0)
            for n in ("Surya", "Chandra", "Mangal", "Budha", "Guru",
                      "Shukra", "Shani")]})
        crowded = ChartVisualModel(
            chart_name=crowded.chart_name, title=crowded.title,
            lagna_sign=crowded.lagna_sign,
            lagna_sign_name=crowded.lagna_sign_name,
            houses=crowded.houses, style="south_indian")
        scene = render_south_indian(crowded)
        sizes = [e.size for e in scene.elements
                 if type(e).__name__ == "Text"
                 and getattr(e, "role", "") == "body"]
        self.assertTrue(sizes)
        self.assertLess(max(sizes), 11.0)


class StyleDispatchTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        record = ConsultationRecord(**JAIPUR)
        cls.natal = calculate_chart(record, record.settings)

    def test_both_implemented_styles_dispatch(self):
        self.assertEqual(IMPLEMENTED_STYLES,
                         ("north_indian", "south_indian"))
        for style in IMPLEMENTED_STYLES:
            with self.subTest(style=style):
                model = chart_visual_model(self.natal, style=style)
                self.assertTrue(render_chart(model).elements)

    def test_east_indian_is_named_and_refused(self):
        """
        Part 20: "Keep EAST_INDIAN refused unless correctly implemented."
        Named, so the refusal can be specific; refused, so it is never
        approximated with a layout that is not it.
        """
        self.assertIn("east_indian", CHART_STYLES)
        self.assertNotIn("east_indian", IMPLEMENTED_STYLES)
        model = chart_visual_model(self.natal, style="east_indian")
        with self.assertRaises(UnsupportedChartStyle) as caught:
            render_chart(model)
        self.assertIn("East Indian", str(caught.exception))

    def test_an_unknown_style_is_refused_differently(self):
        model = chart_visual_model(self.natal)
        made_up = ChartVisualModel(
            chart_name=model.chart_name, title=model.title,
            lagna_sign=model.lagna_sign,
            lagna_sign_name=model.lagna_sign_name, houses=model.houses,
            style="spiral")
        with self.assertRaises(UnsupportedChartStyle) as caught:
            render_chart(made_up)
        self.assertIn("not a chart style", str(caught.exception))
