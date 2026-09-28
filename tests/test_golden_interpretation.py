"""
Golden interpretation text (V1.6 Parts 28, 30)
------------------------------------------------
Exact expected output for the V1.5 synthetic cases A-G, rendered.

WHAT A GOLDEN TEXT TEST IS FOR

    Not to assert that the sentences are true. They are not claims about the
    world, and Part 28 of the V1.5 brief said the same of the synthetic
    charts they rest on: expected results test ENGINE BEHAVIOUR.

    What they pin is that a given structured state renders to a given
    sentence, exactly, every time. That makes two kinds of accident visible
    that nothing else catches: a template edit that quietly changes what the
    engine appears to claim, and a renderer change that makes output depend
    on dict ordering or the clock.

CASE C IS THE ONE TO READ

    A chart with no natal indication for children and two heavy transits
    sitting on the fifth house. A naive engine announces a children
    transit. This one must produce the silence sentence and NO event
    candidate, and the golden text is how that stays true.
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.interpretation import (
    ReportMode, build_interpretation, format_interpretation,
    interpretation_hash,
)
from engine.synthesis import (
    SynthesisProfile, build_prediction_snapshot, event_candidates, synthesise,
)
from engine.synthesis.domains import Domain
from tests.synthetic import synthetic_features
from tests.test_golden_synthesis import (
    MESHA, KUMBHA, MAKARA, SIMHA, TULA, VRISHABHA, _FakeDasha,
    _FakeTransitPosition, _FakeTransitSnapshot,
)

FIXED = datetime.datetime(2026, 1, 1)
MOMENT = datetime.datetime(2026, 6, 15, 12, 0)


def interpret(features, *, dasha=None, transits=None,
              profile=SynthesisProfile.STANDARD,
              domains=None, mode=ReportMode.DETAILED,
              sensitivity=None, precision=None):
    """Synthesise then render, with everything else held fixed."""
    context = synthesise(
        features, moment=MOMENT, dasha=dasha, transit_snapshot=transits,
        profile=profile, domains=domains, sensitivity=sensitivity,
        birth_time_precision_seconds=precision)
    candidates = event_candidates(context, dasha=dasha)
    prediction = build_prediction_snapshot(
        context, candidates=candidates).to_dict()
    return build_interpretation(
        prediction, mode=mode, features=features, generated=FIXED)


def sentences(section) -> list[str]:
    """The claim sentences of one section, in document order."""
    out = []
    for single in (section.overall, section.confidence_phrase,
                   section.contradiction, section.silence):
        if single is not None:
            out.append(single.text)
    return out


# ── A: everything agrees ─────────────────────────────────────────────────────

class CaseAFullStackTest(unittest.TestCase):
    """Natal promise, matching dasha, matching transit → STRONGLY_ACTIVE."""

    def setUp(self):
        self.features = synthetic_features(
            lagna_sign=MESHA,
            placements={"Shani": TULA, "Guru": MAKARA, "Surya": SIMHA},
            shadbala_ratios={"Shani": 1.6, "Guru": 1.2, "Surya": 1.1})
        self.dasha = _FakeDasha({"mahadasha": "Shani",
                                 "antardasha": "Shani"})
        self.transits = _FakeTransitSnapshot(
            {"Shani": _FakeTransitPosition("Shani", 10)})

    def test_exact_activation_sentence(self):
        document = interpret(self.features, dasha=self.dasha,
                             transits=self.transits,
                             domains=[Domain.CAREER])
        section = document.section_for("CAREER")
        self.assertEqual(section.activation, "STRONGLY_ACTIVE")
        self.assertEqual(
            section.overall.text,
            "Professional matters are strongly activated in the period "
            "examined, with indications in the birth chart, the running "
            "dasha and current transits.")

    def test_the_career_override_is_used_not_the_generic(self):
        """
        `career.json` overrides `domain.activation.STRONGLY_ACTIVE`. If the
        override stopped being found, the generic sentence would still read
        plausibly — which is exactly why this needs pinning.
        """
        document = interpret(self.features, dasha=self.dasha,
                             transits=self.transits,
                             domains=[Domain.CAREER])
        self.assertIn("Professional matters",
                      document.section_for("CAREER").overall.text)
        self.assertNotIn("This area is strongly activated",
                         document.section_for("CAREER").overall.text)

    def test_all_three_layers_are_named(self):
        document = interpret(self.features, dasha=self.dasha,
                             transits=self.transits,
                             domains=[Domain.CAREER])
        section = document.section_for("CAREER")
        self.assertTrue(section.dasha)
        self.assertTrue(section.transits)
        self.assertTrue(section.supporting)


# ── B: promise with nothing activating it ────────────────────────────────────

class CaseBBackgroundTest(unittest.TestCase):

    def setUp(self):
        self.features = synthetic_features(
            lagna_sign=MESHA,
            placements={"Shani": TULA, "Budha": VRISHABHA},
            shadbala_ratios={"Shani": 1.6, "Budha": 1.0})

    def test_exact_background_sentence(self):
        document = interpret(self.features, domains=[Domain.CAREER])
        section = document.section_for("CAREER")
        self.assertEqual(section.activation, "BACKGROUND")
        self.assertEqual(
            section.overall.text,
            "The birth chart carries a standing indication about "
            "professional life that nothing in the current period is "
            "activating.")

    def test_no_timing_window_is_offered(self):
        """No dasha, no window. Part 17: no date is invented."""
        document = interpret(self.features, domains=[Domain.CAREER])
        self.assertEqual(document.section_for("CAREER").timing, [])


# ── C: the case that must stay silent ────────────────────────────────────────

class CaseCTransitWithoutPromiseTest(unittest.TestCase):
    """
    THE IMPORTANT ONE. Heavy transits on the fifth, no natal indication.
    """

    def setUp(self):
        self.features = synthetic_features(
            lagna_sign=KUMBHA, placements={"Budha": MESHA})
        self.transits = _FakeTransitSnapshot(
            {"Guru": _FakeTransitPosition("Guru", 5),
             "Shani": _FakeTransitPosition("Shani", 5)})

    def test_exact_silence_sentence(self):
        document = interpret(self.features, transits=self.transits,
                             domains=[Domain.CHILDREN])
        section = document.section_for("CHILDREN")
        self.assertTrue(section.is_silent)
        self.assertEqual(
            section.silence.text,
            "Transits currently touch the houses associated with this area, "
            "but the birth chart shows no standing indication for them to "
            "activate, so nothing is reported.")

    def test_no_event_candidate_is_produced(self):
        """Part 30 names this explicitly."""
        document = interpret(self.features, transits=self.transits,
                             domains=[Domain.CHILDREN])
        section = document.section_for("CHILDREN")
        self.assertEqual(section.timing, [])
        self.assertEqual(section.supporting, [])
        self.assertEqual(section.challenging, [])

    def test_the_rendered_text_makes_no_claim_about_children(self):
        document = interpret(self.features, transits=self.transits,
                             domains=[Domain.CHILDREN])
        text = format_interpretation(document).lower()
        for phrase in ("strongly activated", "is active in the period",
                       "activation is calculated"):
            self.assertNotIn(phrase, text)


# ── D: contradiction ─────────────────────────────────────────────────────────

class CaseDContradictionTest(unittest.TestCase):

    def setUp(self):
        # Mesha lagna. The 2nd lord Shukra is exalted in Meena, and Shani, a
        # malefic, sits in the 2nd and aspects it — supportive and
        # challenging evidence for WEALTH in one chart.
        self.features = synthetic_features(
            lagna_sign=MESHA,
            placements={"Shukra": 11, "Shani": VRISHABHA},
            aspects=(("Shani", VRISHABHA, True),),
            shadbala_ratios={"Shukra": 1.3})

    def test_both_sides_are_rendered(self):
        document = interpret(self.features, domains=[Domain.WEALTH])
        section = document.section_for("WEALTH")
        self.assertTrue(section.supporting)
        self.assertTrue(section.challenging)

    def test_exact_contradiction_sentence(self):
        document = interpret(self.features, domains=[Domain.WEALTH])
        self.assertEqual(
            document.section_for("WEALTH").contradiction.text,
            "Several factors support activity in this area, while other "
            "factors indicate obstacles or delay. Both are listed below and "
            "neither cancels the other.")

    def test_summary_mode_does_not_promise_the_lists(self):
        document = interpret(self.features, domains=[Domain.WEALTH],
                             mode=ReportMode.SUMMARY)
        section = document.section_for("WEALTH")
        self.assertEqual(
            section.contradiction.text,
            "The factors found in this area point in both directions; "
            "neither cancels the other.")


# ── E: unstable D60 ──────────────────────────────────────────────────────────

class CaseEUnstableBirthTimeTest(unittest.TestCase):

    def setUp(self):
        from engine.sensitivity.models import (
            SensitivityReport, SensitivityWindow, UnstableItem,
        )
        item = UnstableItem(
            item="D60 lagna", key="d60_lagna", baseline="Simha",
            changes_to="Kanya", offset_seconds=39, offset_text="+0m39s")
        self.sensitivity = SensitivityReport(
            birth_utc=datetime.datetime(1988, 8, 30, 14, 48),
            latitude=26.9, longitude=75.8, scan_step_seconds=15,
            windows=[SensitivityWindow(window_minutes=1, stable=False,
                                       changes=[item])])
        self.features = synthetic_features(
            lagna_sign=MESHA, placements={"Shani": TULA},
            shadbala_ratios={"Shani": 1.4})

    def test_the_instability_is_stated_in_the_document(self):
        document = interpret(self.features, sensitivity=self.sensitivity,
                             precision=60, domains=[Domain.CAREER])
        keys = {p.key for p in document.reliability_warnings}
        self.assertIn("reliability.varga_unstable", keys)
        texts = [p.text for p in document.reliability_warnings
                 if p.key == "reliability.varga_unstable"]
        self.assertIn(
            "The D60 divisional chart changes within the uncertainty of the "
            "birth time supplied.", texts)

    def test_a_second_exact_birth_time_removes_the_warning(self):
        """
        The instability is a property of chart AND stated precision. Told to
        the second, the same chart's D60 is firm and the warning goes.
        """
        document = interpret(self.features, sensitivity=self.sensitivity,
                             precision=1, domains=[Domain.CAREER])
        keys = {p.key for p in document.reliability_warnings}
        self.assertNotIn("reliability.varga_unstable", keys)


# ── F: an unverified yoga excluded from strict ───────────────────────────────

class CaseFExcludedYogaTest(unittest.TestCase):

    def test_strict_declines_where_standard_speaks(self):
        features = synthetic_features(
            lagna_sign=MESHA, placements={"Shukra": 11},
            shadbala_ratios={"Shukra": 1.2})
        standard = interpret(features, domains=[Domain.RELATIONSHIPS],
                             profile=SynthesisProfile.STANDARD)
        strict = interpret(features, domains=[Domain.RELATIONSHIPS],
                           profile=SynthesisProfile.STRICT)
        self.assertFalse(standard.section_for("RELATIONSHIPS").is_silent)
        self.assertTrue(strict.section_for("RELATIONSHIPS").is_silent)

    def test_exact_strict_silence_sentence(self):
        features = synthetic_features(
            lagna_sign=MESHA, placements={"Shukra": 11},
            shadbala_ratios={"Shukra": 1.2})
        strict = interpret(features, domains=[Domain.RELATIONSHIPS],
                           profile=SynthesisProfile.STRICT)
        self.assertEqual(
            strict.section_for("RELATIONSHIPS").silence.text,
            "Insufficient validated evidence for this area under the strict "
            "profile.")


# ── G: reference space ───────────────────────────────────────────────────────

class CaseGReferenceSpaceTest(unittest.TestCase):

    def test_output_is_identical_whether_or_not_a_bhava_chart_exists(self):
        """
        Part 5 of V1.5, carried into the rendered text: a classical Rashi
        reading must not change because a quadrant house system was built.
        """
        features = synthetic_features(
            lagna_sign=MESHA, placements={"Shani": TULA, "Shukra": 3},
            shadbala_ratios={"Shani": 1.4})
        before = interpret(features, domains=[Domain.CAREER])
        features.bhava_chart = {"Shukra": {"rashi_house": 4,
                                           "bhava_house": 5}}
        after = interpret(features, domains=[Domain.CAREER])
        self.assertEqual(interpretation_hash(before),
                         interpretation_hash(after))


# ── determinism across all the cases ─────────────────────────────────────────

class GoldenDeterminismTest(unittest.TestCase):

    def test_every_case_renders_identically_twice(self):
        cases = {
            "A": (synthetic_features(
                lagna_sign=MESHA, placements={"Shani": TULA},
                shadbala_ratios={"Shani": 1.6}),
                _FakeDasha({"mahadasha": "Shani", "antardasha": "Shani"}),
                _FakeTransitSnapshot(
                    {"Shani": _FakeTransitPosition("Shani", 10)})),
            "B": (synthetic_features(
                lagna_sign=MESHA, placements={"Shani": TULA},
                shadbala_ratios={"Shani": 1.6}), None, None),
            "C": (synthetic_features(
                lagna_sign=KUMBHA, placements={"Budha": MESHA}), None,
                _FakeTransitSnapshot(
                    {"Guru": _FakeTransitPosition("Guru", 5)})),
        }
        for name, (features, dasha, transits) in sorted(cases.items()):
            with self.subTest(case=name):
                first = interpret(features, dasha=dasha, transits=transits)
                second = interpret(features, dasha=dasha, transits=transits)
                self.assertEqual(interpretation_hash(first),
                                 interpretation_hash(second))
                self.assertEqual(format_interpretation(first),
                                 format_interpretation(second))

    def test_the_three_modes_of_one_case_agree_on_findings(self):
        features = synthetic_features(
            lagna_sign=MESHA, placements={"Shani": TULA},
            shadbala_ratios={"Shani": 1.6})
        dasha = _FakeDasha({"mahadasha": "Shani", "antardasha": "Shani"})
        rendered = {
            mode: interpret(features, dasha=dasha, mode=mode)
            for mode in ReportMode}
        detailed = rendered[ReportMode.DETAILED]
        for mode, document in rendered.items():
            for section in document.domain_sections:
                other = detailed.section_for(section.domain)
                with self.subTest(mode=mode.value, domain=section.domain):
                    self.assertEqual(section.activation, other.activation)
                    self.assertEqual(section.confidence, other.confidence)


if __name__ == "__main__":
    unittest.main()
