"""
V1 release-candidate goldens (V1.8 Part 42)
---------------------------------------------
Four charts, frozen at every stage.

WHAT A GOLDEN IS FOR HERE

    Not correctness. Nothing in this file says a chart is right; the
    hashes were produced by the same engine they now guard, so a wrong
    answer froze exactly as readily as a right one.

    What they establish is that an answer DID NOT MOVE. That is the
    question a release candidate has to answer about every change after
    it: did this refactor alter a single reported value, anywhere in the
    pipeline, for any of four quite different charts.

    A failure here is therefore never "the code is broken". It is "an
    output changed — say why", and `tests/fixtures/rc_goldens.json`
    carries a `reasons` list for exactly that purpose.

WHY THE HASHES EXCLUDE TIMESTAMPS

    Every document this engine produces carries the time it was
    generated. Hashing that would make every golden fail every second,
    which trains people to regenerate the fixture without reading it —
    the precise failure mode a golden exists to prevent.
"""

import datetime
import hashlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.generate_rc_goldens import (  # noqa: E402
    CASES, FIXED_TIME, FIXTURE, MOMENT, build_case,
)

_STATE: dict = {}


def setUpModule():
    with open(FIXTURE, encoding="utf-8") as handle:
        _STATE["expected"] = json.load(handle)
    _STATE["actual"] = {case["id"]: build_case(case) for case in CASES}


def _expected(case_id: str) -> dict:
    for case in _STATE["expected"]["cases"]:
        if case["id"] == case_id:
            return case
    raise AssertionError(f"no golden recorded for {case_id}")


class GoldenTest(unittest.TestCase):

    def test_the_fixture_covers_every_case(self):
        self.assertEqual(
            sorted(case["id"] for case in _STATE["expected"]["cases"]),
            sorted(case["id"] for case in CASES))

    def test_every_natal_snapshot_is_unchanged(self):
        for case_id, actual in _STATE["actual"].items():
            with self.subTest(case=case_id):
                self.assertEqual(actual["natal_snapshot"],
                                 _expected(case_id)["natal_snapshot"],
                                 self._message(case_id, "natal snapshot"))

    def test_every_prediction_snapshot_is_unchanged(self):
        for case_id, actual in _STATE["actual"].items():
            with self.subTest(case=case_id):
                self.assertEqual(actual["prediction_snapshot"],
                                 _expected(case_id)["prediction_snapshot"],
                                 self._message(case_id, "prediction"))

    def test_every_interpretation_is_unchanged(self):
        for case_id, actual in _STATE["actual"].items():
            with self.subTest(case=case_id):
                self.assertEqual(actual["interpretation"],
                                 _expected(case_id)["interpretation"],
                                 self._message(case_id, "interpretation"))

    def test_every_chart_drawing_is_unchanged(self):
        for case_id, actual in _STATE["actual"].items():
            for key, value in sorted(actual["charts"].items()):
                with self.subTest(case=case_id, chart=key):
                    self.assertEqual(
                        value, _expected(case_id)["charts"][key],
                        self._message(case_id, f"the {key} drawing"))

    def test_every_report_is_unchanged(self):
        for case_id, actual in _STATE["actual"].items():
            for key, value in sorted(actual["reports"].items()):
                with self.subTest(case=case_id, report=key):
                    expected = _expected(case_id)["reports"][key]
                    self.assertEqual(value["document"], expected["document"],
                                     self._message(case_id, f"the {key} "
                                                            f"report"))
                    self.assertEqual(value["sections"], expected["sections"])

    def test_pdf_sizes_have_not_drifted_materially(self):
        """
        Byte-for-byte PDF equality is not asserted: zlib's output can
        vary between Python builds and that would be a failure nobody
        could act on. A size that moves by more than a few per cent
        means the document changed, which is actionable.
        """
        for case_id, actual in _STATE["actual"].items():
            for key, value in sorted(actual["reports"].items()):
                expected = _expected(case_id)["reports"][key]["pdf_bytes"]
                with self.subTest(case=case_id, report=key):
                    self.assertAlmostEqual(
                        value["pdf_bytes"] / expected, 1.0, delta=0.02,
                        msg=self._message(case_id, f"the {key} PDF size"))

    def test_the_shape_of_every_result_is_unchanged(self):
        for case_id, actual in _STATE["actual"].items():
            with self.subTest(case=case_id):
                self.assertEqual(actual["shape"], _expected(case_id)["shape"])

    def _message(self, case_id: str, what: str) -> str:
        return (
            f"{what} changed for {case_id}. This is not necessarily a bug: "
            f"it means an output moved. Regenerate with "
            f"`python3 tools/generate_rc_goldens.py --write` AND add an "
            f"entry to `reasons` in tests/fixtures/rc_goldens.json saying "
            f"what changed and why, in the same commit.")


class FixtureDisciplineTest(unittest.TestCase):

    def test_the_fixture_records_what_produced_it(self):
        expected = _STATE["expected"]
        self.assertIn("generated_under", expected)
        self.assertTrue(expected["generated_under"]["application"])
        self.assertEqual(expected["moment"], MOMENT.isoformat())
        self.assertEqual(expected["fixed_time"], FIXED_TIME.isoformat())

    def test_every_change_to_a_golden_has_a_recorded_reason(self):
        reasons = _STATE["expected"]["reasons"]
        self.assertTrue(reasons)
        for entry in reasons:
            with self.subTest(release=entry.get("release")):
                self.assertTrue(entry.get("release"))
                self.assertTrue(entry.get("what"))
                self.assertTrue(entry.get("why"))

    def test_the_cases_differ_in_what_they_stress(self):
        """
        Four goldens that all look like the documented example would
        freeze one chart four times.
        """
        cases = _STATE["expected"]["cases"]
        self.assertEqual(len(cases), 4)
        self.assertEqual(len({c["input"]["place"] for c in cases}), 4)
        self.assertGreaterEqual(
            len({c["input"]["precision"] for c in cases}), 3)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["why"])

    def test_a_golden_is_deterministic_within_one_run(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                self.assertEqual(build_case(case)["natal_snapshot"],
                                 _STATE["actual"][case["id"]]
                                 ["natal_snapshot"])


if __name__ == "__main__":
    unittest.main()
