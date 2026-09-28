"""
Golden synthesis cases (V1.5 Part 28)
---------------------------------------
Seven charts, each constructed to isolate one behaviour of the synthesis
engine. Part 28 is explicit about what these assert:

    Expected results test ENGINE BEHAVIOUR, not empirical truth.

So nothing here claims that a 10th lord exalted in a kendra produces a
career, or that any of these nativities would be read this way by anyone.
Each asserts that GIVEN this input the engine reaches that output, which is
the only thing a test of deterministic logic can honestly assert.

The cases are the brief's own list:

    A  strong natal career promise + matching dasha + matching transit
    B  strong natal promise + no current activation
    C  weak natal promise + strong transit
    D  contradictory natal evidence
    E  D60 confirmation but unreliable birth time
    F  Yoga present but excluded from the strict profile
    G  Rashi condition true but Bhava condition false

C and G are the two that would be easiest to get wrong, and are the reason
the list is worth working through: C is where a prediction engine invents a
promise out of a transit, and G is where it lets a house-system setting
silently move a classical rule.
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.synthesis import (
    ActivationLevel, Domain, EvidenceConfidence, EvidenceDirection,
    EvidenceLayer, PredictionEligibility, SynthesisProfile, build_reliability,
    chart_reliability, evaluate_natal_promise, event_candidates,
    prediction_eligibility, spec_for, synthesise,
)
from engine.synthesis.models import DomainEvidence, TransitActivation
from engine.sensitivity.models import (
    SensitivityReport, SensitivityWindow, UnstableItem,
)
from tests.synthetic import synthetic_features

MOMENT = datetime.datetime(2026, 6, 15, 12, 0)

# Sign indices, for readability in the placements below.
MESHA, VRISHABHA, MITHUNA, KARKA, SIMHA, KANYA = 0, 1, 2, 3, 4, 5
TULA, VRISHCHIKA, DHANU, MAKARA, KUMBHA, MEENA = 6, 7, 8, 9, 10, 11


def _evidence(domain, layer, direction, magnitude=0.7,
              confidence=EvidenceConfidence.HIGH, factor="f"):
    return DomainEvidence(
        domain=domain, factor_id=factor, layer=layer,
        source_type="house_lord", direction=direction, magnitude=magnitude,
        confidence=confidence, explanation_key="test",
        explanation="constructed for a golden case")


class _FakeDashaPeriod:
    def __init__(self, lord, level, start, end):
        self.lord, self.level = lord, level
        self.start, self.end = start, end


class _FakeDasha:
    """
    A dasha stack with chosen lords.

    Real Vimshottari is exercised by test_timing.py; what these cases need is
    control over WHICH graha is running, which the real engine derives from
    the Moon and cannot be told.
    """

    def __init__(self, lords: dict):
        self.lords = lords

    def get_dasha_stack_at(self, moment):
        return dict(self.lords)

    def get_period_at(self, moment, level="antardasha"):
        lord = self.lords.get(level)
        if lord is None:
            return None
        return _FakeDashaPeriod(
            lord, level, moment - datetime.timedelta(days=200),
            moment + datetime.timedelta(days=200))


class _FakeTransitSnapshot:
    def __init__(self, positions, relationships=()):
        self.positions = positions
        self.relationships = list(relationships)


class _FakeTransitPosition:
    def __init__(self, planet, house_from_lagna, retrograde=False):
        self.planet = planet
        self.house_from_natal_lagna = house_from_lagna
        self.house_from_natal_moon = None
        self.retrograde = retrograde


# ── A: everything agrees ─────────────────────────────────────────────────────

class CaseAFullStackTest(unittest.TestCase):
    """
    Mesha lagna. 10th lord Shani exalted in Tula, the 7th, a kendra.
    Shani runs the mahadasha and transits the natal 10th.

    Expected: STRONGLY_ACTIVE, because all three layers are present.
    """

    def setUp(self):
        self.features = synthetic_features(
            lagna_sign=MESHA,
            placements={"Shani": TULA, "Guru": MAKARA, "Surya": SIMHA},
            shadbala_ratios={"Shani": 1.6, "Guru": 1.2, "Surya": 1.1})
        self.dasha = _FakeDasha({"mahadasha": "Shani",
                                 "antardasha": "Shani"})
        self.transits = _FakeTransitSnapshot(
            {"Shani": _FakeTransitPosition("Shani", 10)})

    def test_all_three_layers_present(self):
        context = synthesise(
            self.features, moment=MOMENT, dasha=self.dasha,
            transit_snapshot=self.transits, domains=[Domain.CAREER])
        result = context.result_for(Domain.CAREER)
        layers = {e.layer for e in result.all_evidence}
        self.assertEqual(
            layers, {EvidenceLayer.NATAL, EvidenceLayer.DASHA,
                     EvidenceLayer.TRANSIT})

    def test_activation_is_strongly_active(self):
        context = synthesise(
            self.features, moment=MOMENT, dasha=self.dasha,
            transit_snapshot=self.transits, domains=[Domain.CAREER])
        self.assertIs(context.result_for(Domain.CAREER).activation,
                      ActivationLevel.STRONGLY_ACTIVE)

    def test_the_exalted_lord_is_recorded_as_the_reason(self):
        evidence, _v, _e = evaluate_natal_promise(
            Domain.CAREER, self.features)
        dignity = [e for e in evidence
                   if e.explanation_key == "house_lord_dignified"]
        self.assertTrue(dignity)
        self.assertIn("Shani", dignity[0].planets)


# ── B: promise with nothing activating it ────────────────────────────────────

class CaseBPromiseWithoutActivationTest(unittest.TestCase):
    """
    The same natal chart as A, and Budha — which touches nothing in the
    career houses — is running.

    Expected: BACKGROUND. The promise is real and nothing is activating it,
    and the engine must be able to say that rather than either forgetting
    the promise or inventing an activation.
    """

    def setUp(self):
        self.features = synthetic_features(
            lagna_sign=MESHA,
            placements={"Shani": TULA, "Budha": VRISHABHA},
            shadbala_ratios={"Shani": 1.6, "Budha": 1.0})

    def test_no_dasha_means_background_not_inactive(self):
        context = synthesise(self.features, moment=MOMENT,
                             domains=[Domain.CAREER])
        result = context.result_for(Domain.CAREER)
        self.assertIs(result.activation, ActivationLevel.BACKGROUND)
        self.assertTrue(result.has_natal_promise)

    def test_the_engine_says_why_it_cannot_go_higher(self):
        context = synthesise(self.features, moment=MOMENT,
                             domains=[Domain.CAREER])
        self.assertTrue(
            any("dasha" in w.lower() for w in context.warnings))


# ── C: the case a prediction engine gets wrong ───────────────────────────────

class CaseCTransitWithoutPromiseTest(unittest.TestCase):
    """
    THE IMPORTANT ONE.

    Kumbha lagna with the CHILDREN houses empty and their lords undignified,
    and a heavy transit sitting on the 5th. A naive engine announces a
    children transit. This one must not.
    """

    def setUp(self):
        # Kumbha lagna, so the 5th is Mithuna and its lord is Budha.
        #
        # Budha goes to Mesha, which is the 3rd house: no dignity there, and
        # the 3rd is neither one of the well-placed houses the engine counts
        # as supportive nor a dusthana it counts as challenging. The 5th is
        # empty, nothing aspects it, no karaka is placed, and neither
        # Shadbala nor Ashtakavarga is supplied.
        #
        # The result is a domain with genuinely NO natal factor — which took
        # some arranging, and is the point: an engine that finds evidence
        # everywhere cannot demonstrate that it declines anywhere.
        self.features = synthetic_features(
            lagna_sign=KUMBHA, placements={"Budha": MESHA})
        self.transits = _FakeTransitSnapshot(
            {"Guru": _FakeTransitPosition("Guru", 5),
             "Shani": _FakeTransitPosition("Shani", 5)})

    def test_the_chart_really_has_no_natal_evidence(self):
        """Guard: if this fails the case has stopped testing what it says."""
        evidence, _v, _e = evaluate_natal_promise(
            Domain.CHILDREN, self.features)
        self.assertEqual(evidence, [])

    def test_transit_alone_yields_inactive(self):
        context = synthesise(
            self.features, moment=MOMENT, transit_snapshot=self.transits,
            domains=[Domain.CHILDREN])
        result = context.result_for(Domain.CHILDREN)
        self.assertIs(result.activation, ActivationLevel.INACTIVE)

    def test_the_transit_is_still_recorded_as_a_fact(self):
        """
        Refused as evidence, retained as an observation.

        Dropping it silently would leave a reader unable to tell the engine
        considered and declined it from the engine never having looked.
        """
        context = synthesise(
            self.features, moment=MOMENT, transit_snapshot=self.transits,
            domains=[Domain.CHILDREN])
        touching = [a for a in context.transit_activations
                    if "CHILDREN" in a.domains_touched]
        self.assertTrue(touching)
        self.assertEqual(context.result_for(Domain.CHILDREN).transit_evidence,
                         [])

    def test_the_refusal_is_explained(self):
        context = synthesise(
            self.features, moment=MOMENT, transit_snapshot=self.transits,
            domains=[Domain.CHILDREN])
        warnings = " ".join(
            context.result_for(Domain.CHILDREN).reliability_warnings)
        self.assertIn("no natal indication", warnings)
        self.assertIn("cannot create", warnings)


# ── D: contradiction ─────────────────────────────────────────────────────────

class CaseDContradictionTest(unittest.TestCase):
    """
    Evidence pointing both ways, in near-balance.

    Expected: MIXED, with both lists populated. Part 16 forbids resolving
    this into a direction.
    """

    def test_balanced_evidence_is_mixed(self):
        from engine.synthesis.scoring import activation_level
        evidence = [
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.SUPPORTIVE, 0.7, factor="a"),
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.CHALLENGING, 0.7, factor="b"),
            _evidence("WEALTH", EvidenceLayer.DASHA,
                      EvidenceDirection.SUPPORTIVE, 0.6, factor="c"),
        ]
        self.assertIs(activation_level(evidence), ActivationLevel.MIXED)

    def test_lopsided_evidence_keeps_a_direction(self):
        from engine.synthesis.scoring import activation_level
        evidence = [
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.SUPPORTIVE, 0.9, factor="a"),
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.SUPPORTIVE, 0.9, factor="b"),
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.SUPPORTIVE, 0.9, factor="c"),
            _evidence("WEALTH", EvidenceLayer.DASHA,
                      EvidenceDirection.SUPPORTIVE, 0.9, factor="d"),
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.CHALLENGING, 0.3, factor="e"),
        ]
        self.assertIs(activation_level(evidence), ActivationLevel.ACTIVE)

    def test_contradiction_lowers_confidence(self):
        from engine.synthesis.scoring import synthesis_confidence
        agreeing = [
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.SUPPORTIVE, factor="a"),
            _evidence("WEALTH", EvidenceLayer.DASHA,
                      EvidenceDirection.SUPPORTIVE, factor="b"),
        ]
        conflicting = agreeing + [
            _evidence("WEALTH", EvidenceLayer.NATAL,
                      EvidenceDirection.CHALLENGING, factor="c")]
        self.assertGreater(
            synthesis_confidence(agreeing).rank,
            synthesis_confidence(conflicting).rank)


# ── E: D60 on an unreliable birth time ───────────────────────────────────────

class CaseEUnreliableD60Test(unittest.TestCase):
    """
    The brief's own worked example, and V1.4's real measurement.

    D60 lagna changes at +39s; the birth time was entered as HH:MM. The
    engine must mark D60 evidence LOW and drop it from strict — without
    lowering the activation level, which is a separate axis.
    """

    def setUp(self):
        item = UnstableItem(
            item="D60 lagna", key="d60_lagna", baseline="Simha",
            changes_to="Kanya", offset_seconds=39, offset_text="+0m39s")
        self.sensitivity = SensitivityReport(
            birth_utc=datetime.datetime(1988, 8, 30, 14, 48),
            latitude=26.9, longitude=75.8, scan_step_seconds=15,
            windows=[SensitivityWindow(window_minutes=1, stable=False,
                                       changes=[item])])

    def test_d60_is_low_confidence_and_strict_drops_it(self):
        from engine.synthesis import admits_chart
        reliability = build_reliability(self.sensitivity,
                                        birth_time_precision_seconds=60)
        self.assertIs(chart_reliability("D60", reliability),
                      EvidenceConfidence.LOW)
        self.assertFalse(admits_chart("D60", reliability, strict=True))
        self.assertTrue(admits_chart("D60", reliability, strict=False))

    def test_activation_and_confidence_move_independently(self):
        """
        STRONGLY_ACTIVE with LOW confidence is valid and must be reachable.
        """
        from engine.synthesis.scoring import (
            activation_level, synthesis_confidence,
        )
        evidence = [
            _evidence("CAREER", EvidenceLayer.NATAL,
                      EvidenceDirection.SUPPORTIVE, 0.9,
                      EvidenceConfidence.LOW, factor="a"),
            _evidence("CAREER", EvidenceLayer.DASHA,
                      EvidenceDirection.SUPPORTIVE, 0.9,
                      EvidenceConfidence.LOW, factor="b"),
            _evidence("CAREER", EvidenceLayer.TRANSIT,
                      EvidenceDirection.SUPPORTIVE, 0.9,
                      EvidenceConfidence.LOW, factor="c"),
        ]
        self.assertIs(activation_level(evidence),
                      ActivationLevel.STRONGLY_ACTIVE)
        self.assertIs(synthesis_confidence(evidence), EvidenceConfidence.LOW)

    def test_the_warning_names_the_offset_and_the_precision(self):
        reliability = build_reliability(self.sensitivity,
                                        birth_time_precision_seconds=60)
        warnings = " ".join(reliability.warnings)
        self.assertIn("+0m39s", warnings)
        self.assertIn("60s", warnings)


# ── F: present but excluded ──────────────────────────────────────────────────

class CaseFYogaExcludedFromStrictTest(unittest.TestCase):
    """
    A yoga the engine reports as PRESENT and strict synthesis will not use.

    The exclusion must be visible: an unverified yoga may appear in
    diagnostic output (Part 23) and must not quietly influence a prediction.
    """

    def test_a_present_yoga_can_be_disabled_for_synthesis(self):
        self.assertIs(prediction_eligibility("gajakesari"),
                      PredictionEligibility.DISABLED)

    def test_experimental_admits_what_strict_refuses(self):
        self.assertIs(prediction_eligibility("vipareeta_harsha"),
                      PredictionEligibility.SOURCE_LOCATED)
        self.assertTrue(
            SynthesisProfile.STANDARD.accepts(
                PredictionEligibility.SOURCE_LOCATED))
        self.assertFalse(
            SynthesisProfile.STRICT.accepts(
                PredictionEligibility.SOURCE_LOCATED))

    def test_exclusions_are_itemised_with_reasons(self):
        from engine.synthesis import filter_results

        class _Result:
            def __init__(self, rule_id):
                self.id = rule_id
                self.name = rule_id
                self.status = type("S", (), {"value": "PRESENT"})()

        admitted, excluded = filter_results(
            [_Result("adhi_yoga"), _Result("gajakesari"),
             _Result("vipareeta_harsha")],
            SynthesisProfile.STRICT)
        self.assertEqual([r.id for r in admitted], ["adhi_yoga"])
        self.assertEqual(len(excluded), 2)
        for record in excluded:
            with self.subTest(rule=record["rule_id"]):
                self.assertTrue(record["reasons"])


# ── G: rashi true, bhava false ───────────────────────────────────────────────

class CaseGReferenceSpaceTest(unittest.TestCase):
    """
    A graha whose RASHI house and BHAVA house differ.

    Part 5: a classical Rashi Yoga must never silently change because the
    user selected a quadrant house system. The V1.4 regression finding —
    Shukra at rashi house 4 and Sripati bhava house 5 — is the real instance
    of this, and it is pinned in test_houses.py. What this case pins is that
    the SYNTHESIS layer declares RASHI and does not consult the bhava chart.
    """

    def test_every_domain_declares_rashi(self):
        for domain in Domain:
            with self.subTest(domain=domain.value):
                self.assertEqual(
                    spec_for(domain).reference_space.value, "RASHI")

    def test_synthesis_reads_rashi_houses_only(self):
        """
        The engine must reach the same result whether or not a bhava chart
        was built, because it never looks at one.
        """
        features = synthetic_features(
            lagna_sign=MESHA,
            placements={"Shani": TULA, "Shukra": KARKA},
            shadbala_ratios={"Shani": 1.4})

        before = synthesise(features, moment=MOMENT,
                            domains=[Domain.CAREER]).to_dict()

        # Attaching a bhava chart that moves Shukra must change nothing.
        features.bhava_chart = {"Shukra": {"rashi_house": 4,
                                           "bhava_house": 5}}
        after = synthesise(features, moment=MOMENT,
                           domains=[Domain.CAREER]).to_dict()
        self.assertEqual(before["domain_results"], after["domain_results"])

    def test_house_system_compatibility_is_declared(self):
        for domain in Domain:
            with self.subTest(domain=domain.value):
                self.assertIn("whole_sign",
                              spec_for(domain).house_system_compatibility)


# ── the golden charts are not horoscopes ─────────────────────────────────────

class GoldenChartDisclaimerTest(unittest.TestCase):

    def test_synthetic_features_are_marked_synthetic(self):
        features = synthetic_features(lagna_sign=MESHA,
                                      placements={"Surya": SIMHA})
        self.assertIn("synthetic", features.provenance)
        self.assertIn("not ephemeris output",
                      features.provenance["synthetic"])

    def test_fake_shadbala_is_marked(self):
        features = synthetic_features(
            lagna_sign=MESHA, placements={"Surya": SIMHA},
            shadbala_ratios={"Surya": 1.0})
        self.assertTrue(getattr(features.shadbala, "is_synthetic", False))


if __name__ == "__main__":
    unittest.main()
