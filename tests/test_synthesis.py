"""
Synthesis engine tests (V1.5 Part 27)
---------------------------------------
Covers the items Part 27 lists: eligibility gates, reference spaces,
birth-time reliability gating, varga reliability, domain mappings, natal
promise, dasha activation, transit activation, conflicting evidence,
activation categories, event candidates, timing windows, source lineage,
profile differences and snapshot serialisation.

The tests that matter most here are the negative ones. It is easy to write a
synthesis engine that produces plausible output for every chart; the
difficulty is making it decline, and most of what follows checks that it
declines in the right places.
"""

import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.features import build_chart_features, parashari_profile
from engine.houses.profiles import ReferenceSpace
from engine.planets import JyotishChart, jde_from_datetime
from engine.rules import evaluate_rules
from engine.sensitivity.models import (
    SensitivityReport, SensitivityWindow, UnstableItem,
)
from engine.strength import compute_shadbala
from engine.ashtakavarga import compute_ashtakavarga
from engine.timing.vimshottari import from_chart as dasha_from_chart
from engine.transits.calculator import get_transit_snapshot
from engine.synthesis import (
    DOMAINS, HIGH_STAKES_DOMAINS, NO_EVENT_DOMAINS, ActivationLevel,
    Domain, EventType, EvidenceConfidence, EvidenceDirection, EvidenceLayer,
    PredictionEligibility, PredictionSnapshot, SynthesisProfile,
    admits_chart, build_lineage, build_prediction_snapshot, build_reliability,
    chart_reliability, describe, domain_mapping_summary, event_candidates,
    evaluate_natal_promise, natal_snapshot_id, prediction_eligibility,
    spec_for, synthesise, synthesis_appendix,
)
from engine.synthesis.natal_promise import strict_admissible_domains
from engine.synthesis.scoring import activation_level, explain_activation
from tests.synthetic import synthetic_features

BIRTH_UTC = datetime.datetime(1988, 8, 30, 14, 48)
MOMENT = datetime.datetime(2026, 9, 27, 12, 0)


def regression_chart():
    return JyotishChart(jde=jde_from_datetime(BIRTH_UTC),
                        lat=26.9124, lon=75.7873)


class _Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chart = regression_chart()
        cls.features = build_chart_features(
            cls.chart, aspect_profile=parashari_profile("none"))
        cls.features.shadbala = compute_shadbala(
            cls.chart, cls.features, birth=BIRTH_UTC)
        cls.yogas = evaluate_rules(cls.features, "parashari")
        cls.dasha = dasha_from_chart(cls.chart, BIRTH_UTC, depth=3)
        cls.av = compute_ashtakavarga(cls.chart)
        cls.transits = get_transit_snapshot(MOMENT, natal_chart=cls.chart)

    def synth(self, profile=SynthesisProfile.STANDARD, **kwargs):
        return synthesise(
            self.features, moment=MOMENT, yoga_results=self.yogas,
            dasha=self.dasha, transit_snapshot=self.transits,
            ashtakavarga=self.av, profile=profile, **kwargs)


# ── Part 3 and 23: eligibility ───────────────────────────────────────────────

class EligibilityGateTest(unittest.TestCase):

    def test_eligibility_is_derived_from_the_registry(self):
        self.assertIs(prediction_eligibility("adhi_yoga"),
                      PredictionEligibility.VERIFIED_STRICT)
        self.assertIs(prediction_eligibility("dhana_yoga_h1_h2_conjunction"),
                      PredictionEligibility.EXPERIMENTAL)

    def test_a_diverging_rule_is_disabled_everywhere(self):
        """
        Part 23's hardest case: a rule KNOWN to contradict its witness.

        Not merely unverified — established as wrong. It must not influence
        any profile, including experimental, because "experimental" means
        unverified and this rule is worse than that.
        """
        for rule_id in ("sunapha", "gajakesari", "mahapurusha_hamsa",
                        "raja_yoga_k1_t5_conjunction"):
            with self.subTest(rule=rule_id):
                self.assertIs(prediction_eligibility(rule_id),
                              PredictionEligibility.DISABLED)
                for profile in SynthesisProfile:
                    self.assertFalse(
                        profile.accepts(PredictionEligibility.DISABLED),
                        f"{profile.value} must not admit a diverging rule")

    def test_corrected_rules_are_admitted_where_the_originals_are_not(self):
        self.assertIs(prediction_eligibility("sunapha"),
                      PredictionEligibility.DISABLED)
        self.assertIs(prediction_eligibility("sunapha_textual"),
                      PredictionEligibility.VERIFIED_STRICT)

    def test_describe_matches_the_brief_shape(self):
        record = describe("adhi_yoga")
        self.assertEqual(record["rule_id"], "adhi_yoga")
        self.assertIn("prediction_eligibility", record)
        self.assertIn("validation_status", record)

    def test_rejections_explain_themselves(self):
        record = describe("dhana_yoga_h1_h2_conjunction")
        self.assertTrue(record["not_strict_because"])


# ── Part 4: birth-time reliability gating ────────────────────────────────────

class ReliabilityGateTest(unittest.TestCase):

    def _sensitivity(self, offset_seconds: int, key: str):
        item = UnstableItem(
            item=f"{key} lagna", key=key, baseline="A", changes_to="B",
            offset_seconds=offset_seconds,
            offset_text=f"+{offset_seconds}s")
        return SensitivityReport(
            birth_utc=BIRTH_UTC, latitude=26.9, longitude=75.8,
            scan_step_seconds=15,
            windows=[SensitivityWindow(window_minutes=1, stable=False,
                                       changes=[item])])

    def test_unmeasured_is_not_stable(self):
        """
        None must never read as True. "We did not check" is not "it is fine".
        """
        reliability = build_reliability(None)
        self.assertFalse(reliability.sensitivity_available)
        self.assertIsNone(reliability.chart_is_stable("D60"))
        self.assertTrue(reliability.warnings)

    def test_the_v14_d60_finding_gates_d60_evidence(self):
        """
        The worked example from the brief, and V1.4's actual measurement.

        D60 lagna changes at +39s; the birth time was entered as HH:MM and so
        resolves to 60s. The instability is inside the precision, therefore
        D60 is not determined by the input.
        """
        reliability = build_reliability(
            self._sensitivity(39, "d60_lagna"),
            birth_time_precision_seconds=60)
        self.assertFalse(reliability.d60_lagna_stable)
        self.assertIs(chart_reliability("D60", reliability),
                      EvidenceConfidence.LOW)
        self.assertFalse(admits_chart("D60", reliability, strict=True))
        self.assertTrue(admits_chart("D60", reliability, strict=False))

    def test_a_second_exact_birth_time_resolves_the_same_instability(self):
        """
        The same chart, told to the second, makes the same D60 firm.

        The instability is a property of the pairing of chart and stated
        precision, not of the chart alone — which is the whole reason this
        gate takes precision as an input rather than assuming one.
        """
        reliability = build_reliability(
            self._sensitivity(39, "d60_lagna"),
            birth_time_precision_seconds=1)
        self.assertTrue(reliability.d60_lagna_stable)
        self.assertIs(chart_reliability("D60", reliability),
                      EvidenceConfidence.HIGH)

    def test_an_unresolved_lagna_drags_every_varga_down(self):
        reliability = build_reliability(
            self._sensitivity(20, "lagna"), birth_time_precision_seconds=60)
        self.assertFalse(reliability.lagna_stable)
        self.assertIs(chart_reliability("D9", reliability),
                      EvidenceConfidence.LOW)

    def test_finer_varga_is_not_more_reliable_when_unmeasured(self):
        """Part 9: D60 must not outrank D1 merely for being finer."""
        reliability = build_reliability(None)
        self.assertIs(chart_reliability("D1", reliability),
                      EvidenceConfidence.MEDIUM)
        self.assertIs(chart_reliability("D60", reliability),
                      EvidenceConfidence.LOW)

    def test_no_rectification_is_offered(self):
        """
        The report must describe instability and never propose a time.

        Checked against the DATA rather than the prose: the note deliberately
        contains the word "rectification" in order to disclaim it, so
        scanning the whole blob would fail on the disclaimer — the same trap
        as the probability-field test.
        """
        reliability = build_reliability(self._sensitivity(39, "d60_lagna"))
        data = reliability.to_dict()
        self.assertIn("not rectification", data["note"].lower())

        payload = {k: v for k, v in data.items() if k != "note"}
        blob = json.dumps(payload).lower()
        for word in ("rectif", "suggested", "recommended", "corrected time",
                     "better time", "preferred"):
            self.assertNotIn(word, blob)

        # No field anywhere proposes a datetime other than the one entered.
        for item in data["unstable_items"]:
            with self.subTest(item=item["key"]):
                self.assertIn("offset_seconds", item)
                self.assertNotIn("suggested_time", item)
                self.assertNotIn("corrected_birth_time", item)


# ── Parts 5, 6, 8: the domain model ──────────────────────────────────────────

class DomainModelTest(unittest.TestCase):

    def test_all_seventeen_domains_exist(self):
        self.assertEqual(len(Domain), 17)
        self.assertEqual(len(DOMAINS), 17)

    def test_every_mapping_declares_its_reference_space(self):
        """
        Part 5: a Rashi rule must not silently move because of --house-system.
        """
        for spec in DOMAINS.values():
            with self.subTest(domain=spec.domain.value):
                self.assertIs(spec.reference_space, ReferenceSpace.RASHI)
                self.assertIn("whole_sign", spec.house_system_compatibility)

    def test_every_mapping_states_its_own_standing(self):
        """
        REPLACED IN V1.6. The V1.5 test asserted a single
        `spec.validation_status` of UNVERIFIED for every domain, which was
        the honest summary when no mapping had a witness.

        V1.6 splits a domain into individual factor→domain mappings with
        independent provenance, so a per-domain status would now be a lossy
        average of things that genuinely differ — CAREER's house mapping is
        sourced from BPHS 11.11 and its D10 mapping is sourced from nowhere.
        The invariant that survives is that every mapping declares its own
        standing, and an unlocated one says why.
        """
        for spec in DOMAINS.values():
            for mapping in spec.mappings:
                with self.subTest(domain=spec.domain.value,
                                  factor=f"{mapping.factor_type.value}"
                                         f":{mapping.factor}"):
                    if mapping.is_located:
                        self.assertTrue(mapping.textual_condition.strip())
                    else:
                        self.assertTrue(
                            mapping.notes.strip(),
                            "an unlocated mapping must record why")
                        self.assertFalse(mapping.is_source_qualified)

    def test_varga_mappings_match_the_verse_that_assigns_them(self):
        """
        REPLACES `test_no_varga_mapping_is_source_qualified` (V1.6).

        WHY THE OLD ASSERTION WAS REMOVED, AND WHAT REPLACES IT

            V1.6 asserted that no varga mapping is located anywhere, on
            the finding that "no passage in any witness this engine holds
            assigns a divisional chart to a life area". The V1.7 audit
            found the passage: BPHS 7.1-6, `vargavivekādhyāya`, one
            chapter after the ṣoḍaśavarga chapter V1.6 read. The old
            assertion was a correct pin on an incorrect finding, so it is
            replaced rather than relaxed.

            The replacement is stricter in the way that matters. It does
            not say "vargas are sourced now"; it pins each mapping to
            exactly what the verse does and does not say, so that widening
            one later fails here.

        THE ENGINE'S ELEVEN, AGAINST BPHS 7.1-6

            Six state the engine's own claim and are qualified. Five of
            them were mappings the engine already shipped; the sixth,
            D2 for wealth, was added in V1.8 BECAUSE the verse states it
            and the engine had no such mapping.
            Two name a NEARBY subject — mahat-phala for D10, parents for
            D12 — and are located without being qualified.
            Four are not in the verse. One of those, D4 for property, is
            contradicted by it: 7.2 gives the caturthāṃśa bhāgya.
        """
        from engine.synthesis.domain_evidence import FactorType

        attested = {("MARRIAGE", "D9"), ("CHILDREN", "D7"),
                    ("EDUCATION", "D24"), ("SIBLINGS", "D3"),
                    ("SPIRITUALITY", "D20"), ("WEALTH", "D2")}
        located_not_qualified = {("CAREER", "D10"), ("FAMILY", "D12")}
        not_in_verse = {("CAREER", "D9"), ("PROPERTY", "D4"),
                        ("HEALTH", "D6"), ("BUSINESS", "D10")}

        vargas = [m for spec in DOMAINS.values() for m in spec.mappings
                  if m.factor_type is FactorType.VARGA]
        self.assertEqual(len(vargas), 12)
        seen = set()
        for mapping in vargas:
            key = (mapping.domain, mapping.factor)
            seen.add(key)
            with self.subTest(domain=mapping.domain, chart=mapping.factor):
                if key in attested:
                    self.assertTrue(mapping.is_source_qualified)
                    self.assertIn("BPHS_SA_7.1-8_VARGAVIVEKA",
                                  mapping.source_ref_ids)
                    self.assertTrue(mapping.textual_term.strip())
                elif key in located_not_qualified:
                    self.assertTrue(mapping.is_located)
                    self.assertFalse(
                        mapping.is_source_qualified,
                        "a nearby subject is not the engine's claim")
                else:
                    self.assertIn(key, not_in_verse)
                    self.assertFalse(mapping.is_located)
                    self.assertFalse(mapping.is_source_qualified)
                    self.assertTrue(mapping.notes.strip())
        self.assertEqual(
            seen, attested | located_not_qualified | not_in_verse)

    def test_the_d4_property_mapping_records_that_the_verse_disagrees(self):
        """
        V1.7 Part 29 asks for an honest classification, and "unsourced"
        would not be one here.

        BPHS 7.2 assigns the caturthāṃśa to bhāgya, fortune. The engine
        ships D4 for property because that is universal modern practice.
        Those are not the same claim, and the note has to say so — a
        reader comparing this mapping with, say, D6-for-health should be
        able to see that one is merely absent from the verse and the other
        is pointed elsewhere by it.
        """
        from engine.synthesis.domain_evidence import FactorType
        spec = spec_for(Domain.PROPERTY)
        d4 = [m for m in spec.mappings
              if m.factor_type is FactorType.VARGA and m.factor == "D4"]
        self.assertEqual(len(d4), 1)
        self.assertFalse(d4[0].is_source_qualified)
        self.assertIn("bhāgya", d4[0].notes)

    def test_located_karakas_carry_their_witness(self):
        """
        UPDATED IN V1.6. V1.5 knew only the sthira kāraka list at BPHS
        32.18-21, so every located kāraka cited it. V1.6 found the bhāva
        kāraka scheme four verses later at 32.22-24, and several
        attributions now rest on that instead — or on both.
        """
        allowed = {"BPHS_SA_32.18-21_STHIRA_KARAKA",
                   "BPHS_SA_32.22-24_BHAVA_KARAKA"}
        located = [k for spec in DOMAINS.values() for k in spec.karakas
                   if k.is_located]
        self.assertTrue(located)
        for karaka in located:
            with self.subTest(planet=karaka.planet):
                self.assertTrue(set(karaka.source_ref_ids) & allowed)
                self.assertTrue(karaka.note.strip())

    def test_the_putrakaraka_question_was_resolved_by_a_second_passage(self):
        """
        CORRECTED IN V1.6, and the correction is to V1.5's own reading.

        V1.5 read BPHS 32.18-21, found `putraḥ śanaiścarāt` — the son from
        Saturn — and registered a conflict between BPHS and the modern
        attribution of putrakāraka to Jupiter. That was an accurate report
        of an incomplete reading.

        Four verses later, at 32.23, the same chapter gives a different
        kāraka scheme `kheṭa-bhāva-vaśāt` and says `devejyāt pañcamāt putro`
        — the son from Jupiter, in the fifth. So the conflict was never
        between BPHS and modern practice; it is between two schemes inside
        one chapter, and the second agrees with modern practice.

        Both readings still ship. Jupiter is source-qualified for CHILDREN;
        Saturn is retained, carries the conflict, and cannot enter strict.
        """
        spec = spec_for(Domain.CHILDREN)
        planets = {k.planet: k for k in spec.karakas}
        self.assertIn("Guru", planets)
        self.assertIn("Shani", planets)
        self.assertTrue(planets["Guru"].is_located)
        self.assertTrue(planets["Shani"].is_located)

        from engine.synthesis.domain_evidence import FactorType
        self.assertTrue(
            spec.qualifies_for_strict(FactorType.KARAKA, "Guru"),
            "BPHS 32.23 attests Jupiter as putrakāraka")
        self.assertFalse(
            spec.qualifies_for_strict(FactorType.KARAKA, "Shani"),
            "the Saturn reading carries an unresolved conflict")

    def test_saturn_is_the_longevity_karaka_in_the_bhava_scheme(self):
        """
        The other half of the same verse group: BPHS 32.24 gives
        `mandād aṣṭamato mṛtyuḥ`, death from Saturn in the eighth. So the
        bhāva scheme assigns Saturn to longevity, not to children — which
        is also where modern practice puts it.
        """
        from engine.synthesis.domain_evidence import FactorType
        spec = spec_for(Domain.LONGEVITY)
        self.assertTrue(
            spec.qualifies_for_strict(FactorType.KARAKA, "Shani"))

    def test_summary_reports_the_ratio_honestly(self):
        """
        UPDATED IN V1.7. V1.5 asserted zero validated house mappings and
        V1.6 asserted zero validated varga mappings; each was the finding
        of its release and each was overturned by the next one reading
        further into a file it already had.

        What must stay true is that the summary does not OVERSTATE. So
        this asserts bounds rather than totals: some houses qualify, some
        vargas now qualify, most kārakas still do not, and no count
        exceeds its own total.
        """
        summary = domain_mapping_summary()
        self.assertGreater(
            summary["house_mappings_validated"], 0,
            "the V1.6 bhava audit should have qualified some house mappings")
        self.assertLessEqual(summary["house_mappings_validated"],
                             summary["house_mappings_total"])
        self.assertLess(summary["karakas_with_located_witness"],
                        summary["karakas_total"])
        varga = summary["coverage_by_factor_type"]["VARGA"]
        self.assertGreater(
            varga["source_qualified"], 0,
            "BPHS 7.1-6 assigns subjects to the divisions; the five "
            "mappings that state the verse's own subject should qualify")
        self.assertLess(
            varga["source_qualified"], varga["total"],
            "and the six that do not state it should still not qualify")


# ── Part 7: natal promise ────────────────────────────────────────────────────

class NatalPromiseTest(_Base):

    def test_promise_is_structured_evidence(self):
        evidence, vargas, excluded = evaluate_natal_promise(
            Domain.CAREER, self.features, yoga_results=self.yogas,
            ashtakavarga=self.av)
        self.assertTrue(evidence)
        for item in evidence:
            with self.subTest(factor=item.factor_id):
                self.assertIs(item.layer, EvidenceLayer.NATAL)
                self.assertTrue(item.explanation_key)
                self.assertTrue(item.explanation)
                self.assertEqual(item.weighting_basis, "SOFTWARE_HEURISTIC")

    def test_shadbala_keeps_the_ratio_not_a_verdict(self):
        """Part 10: retain total, required and ratio; do not reduce."""
        evidence, _v, _e = evaluate_natal_promise(
            Domain.CAREER, self.features, ashtakavarga=self.av)
        shadbala = [e for e in evidence if e.source_type == "shadbala"]
        self.assertTrue(shadbala)
        self.assertIn("x its BPHS 27.32 requirement",
                      shadbala[0].explanation)
        self.assertIn("virupas", shadbala[0].explanation)

    def test_ashtakavarga_bindus_are_reported_as_counts(self):
        evidence, _v, _e = evaluate_natal_promise(
            Domain.CAREER, self.features, ashtakavarga=self.av)
        av = [e for e in evidence if e.source_type == "ashtakavarga"]
        self.assertTrue(av)
        self.assertIn("bindus", av[0].explanation)
        self.assertIn("BPHS_66_ASHTAKAVARGA", av[0].source_ref_ids)

    def test_unverified_reductions_stay_out(self):
        """Part 11: UNVERIFIED reductions must not reach strict synthesis."""
        self.assertFalse(self.av.reductions)


# ── Parts 12 and 13: activation ──────────────────────────────────────────────

class ActivationTest(_Base):

    def test_dasha_activation_lists_what_the_lord_touches(self):
        context = self.synth()
        self.assertTrue(context.dasha_activations)
        for activation in context.dasha_activations:
            with self.subTest(level=activation.level):
                self.assertTrue(activation.activated_houses)
                self.assertIsNotNone(activation.occupied_house)

    def test_dasha_stack_has_three_levels(self):
        context = self.synth()
        self.assertEqual(
            [a.level for a in context.dasha_activations],
            ["mahadasha", "antardasha", "pratyantardasha"])

    def test_transit_keeps_sign_and_degree_separate(self):
        """
        Part 13, continuing the V1.4 discipline: `same_sign` and
        `angular_separation` are independent facts and neither is derived
        from the other.
        """
        context = self.synth()
        conjunct = [a for a in context.transit_activations
                    if a.relation == "conjunct_natal_point"]
        self.assertTrue(conjunct)
        wide = [a for a in conjunct
                if a.same_sign and a.angular_separation > 8.0]
        self.assertTrue(
            wide,
            "a same-sign relationship far outside any orb should exist and "
            "prove the two fields are not the same claim")
        self.assertFalse(any(a.within_orb for a in wide))

    def test_transit_activation_carries_no_judgement(self):
        context = self.synth()
        blob = json.dumps(
            [a.to_dict() for a in context.transit_activations]).lower()
        for word in ("favourable", "favorable", "auspicious", "benefic period",
                     "good", "bad"):
            self.assertNotIn(word, blob)


# ── Part 14: the hierarchy ───────────────────────────────────────────────────

class HierarchyTest(unittest.TestCase):

    def test_a_transit_cannot_create_a_natal_promise(self):
        """
        THE load-bearing guarantee of the whole package.

        A chart with no natal indication for a domain, and a transit sitting
        squarely on that domain's house, must yield INACTIVE — and must say
        why rather than silently omitting the transit.
        """
        from engine.synthesis.engine import _gated_transit_evidence
        from engine.synthesis.models import TransitActivation

        spec = spec_for(Domain.CAREER)
        activation = TransitActivation(
            transit_planet="Shani", relation="over_natal_house",
            natal_target="house_10", target_kind="house", house_touched=10,
            domains_touched=("CAREER",),
            explanation="Transiting Shani occupies the 10th.")

        evidence, notes = _gated_transit_evidence(
            spec, [activation], natal_evidence=[],
            base_conf=EvidenceConfidence.MEDIUM)
        self.assertEqual(evidence, [])
        self.assertTrue(notes)
        self.assertIn("cannot create", notes[0])

    def test_activation_level_requires_the_natal_layer(self):
        from engine.synthesis.models import DomainEvidence
        transit_only = [DomainEvidence(
            domain="CAREER", factor_id="t", layer=EvidenceLayer.TRANSIT,
            source_type="transit", direction=EvidenceDirection.NEUTRAL,
            magnitude=1.0, confidence=EvidenceConfidence.HIGH,
            explanation_key="k")]
        self.assertIs(activation_level(transit_only),
                      ActivationLevel.INACTIVE)

    def test_natal_only_is_background(self):
        from engine.synthesis.models import DomainEvidence
        natal_only = [DomainEvidence(
            domain="CAREER", factor_id="n", layer=EvidenceLayer.NATAL,
            source_type="house_lord", direction=EvidenceDirection.SUPPORTIVE,
            magnitude=0.7, confidence=EvidenceConfidence.HIGH,
            explanation_key="k")]
        self.assertIs(activation_level(natal_only),
                      ActivationLevel.BACKGROUND)


# ── Parts 15 and 16: bands and contradictions ────────────────────────────────

class ActivationBandTest(_Base):

    def test_no_output_field_implies_a_probability(self):
        """
        Part 15 and Part 20. Walks the serialised KEYS rather than the text,
        so that a disclaimer mentioning the word cannot trip it.
        """
        context = self.synth()
        candidates = event_candidates(context, dasha=self.dasha)
        snapshot = build_prediction_snapshot(
            context, candidates=candidates).to_dict()

        banned = ("probability", "likelihood", "percent", "odds", "chance",
                  "score", "certainty")

        def walk(node, path=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    lowered = key.lower()
                    # A field whose NAME is a denial — `not_included`,
                    # `is_not_probability` — asserts the opposite of what it
                    # contains, so matching the substring in it would fail
                    # the test on its own disclaimer. V1.4 hit the same trap
                    # with the word "score".
                    if "not_" in lowered or lowered.startswith("no_"):
                        walk(value, f"{path}.{key}")
                        continue
                    for word in banned:
                        self.assertNotIn(
                            word, lowered,
                            f"field '{path}.{key}' implies a probability")
                    walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")

        walk(snapshot)

    def test_contradictions_are_reported_not_averaged(self):
        """
        Part 16: five supportive and four challenging is not "positive".

        The demand is that BOTH sides survive into the output. That is a
        different and weaker claim than the activation level being MIXED,
        which requires the two to be near-balanced — so this test checks the
        thing Part 16 actually asks for, on every domain where the evidence
        is not unanimous.
        """
        context = self.synth()
        conflicting = [r for r in context.results.values()
                       if r.has_conflicting_evidence]
        self.assertTrue(conflicting,
                        "the regression chart should produce conflict")
        for result in conflicting:
            with self.subTest(domain=result.domain):
                data = result.to_dict()
                self.assertTrue(data["supportive"])
                self.assertTrue(data["challenging"])
                self.assertTrue(data["mixed"])
                self.assertFalse(data["evidence_is_unanimous"])

    def test_mixed_activation_is_the_stronger_claim(self):
        """
        `mixed` and ActivationLevel.MIXED are not the same statement.

        Every MIXED domain has conflicting evidence; the reverse does not
        hold, because a single dissenting factor among eight should not
        strip the result of a direction.
        """
        context = self.synth()
        for result in context.results.values():
            if result.activation is ActivationLevel.MIXED:
                with self.subTest(domain=result.domain):
                    self.assertTrue(result.has_conflicting_evidence)
        lopsided = [r for r in context.results.values()
                    if r.has_conflicting_evidence
                    and r.activation is not ActivationLevel.MIXED]
        self.assertTrue(
            lopsided,
            "a domain with conflicting but lopsided evidence should keep a "
            "direction; if none does, the two notions have been merged")

    def test_activation_is_reproducible_from_the_evidence(self):
        context = self.synth()
        for result in context.results.values():
            with self.subTest(domain=result.domain):
                self.assertIs(
                    activation_level(result.all_evidence), result.activation)

    def test_activation_explains_its_own_derivation(self):
        context = self.synth()
        result = next(iter(context.results.values()))
        explanation = result.methodology["activation"]
        self.assertEqual(explanation["basis"], "SOFTWARE_HEURISTIC")
        self.assertIn("layers", explanation)
        self.assertIn("rule", explanation)


# ── Part 20: confidence ──────────────────────────────────────────────────────

class ConfidenceTest(_Base):

    def test_confidence_is_independent_of_activation(self):
        """
        The brief's own example: STRONGLY_ACTIVE with LOW confidence is a
        valid combination, so the two must not be derived from one another.
        """
        context = self.synth()
        pairs = {(r.activation, r.confidence) for r in context.results.values()}
        activations = {a for a, _c in pairs}
        for activation in activations:
            confidences = {c for a, c in pairs if a is activation}
            if len(confidences) > 1:
                return
        self.fail("no activation level occurs with two different "
                  "confidences; the two may have become coupled")

    def test_confidence_is_an_ordinal_band_not_a_number(self):
        context = self.synth()
        for result in context.results.values():
            with self.subTest(domain=result.domain):
                data = result.to_dict()
                self.assertTrue(data["confidence_is_ordinal_band"])
                self.assertIn(data["confidence"],
                              {c.value for c in EvidenceConfidence})
                self.assertNotIsInstance(data["confidence"], (int, float))


# ── Part 17: lineage ─────────────────────────────────────────────────────────

class LineageTest(_Base):

    def test_every_result_is_traceable(self):
        context = self.synth()
        for result in context.results.values():
            if result.activation is ActivationLevel.INACTIVE:
                continue
            with self.subTest(domain=result.domain):
                lineage = build_lineage(result)
                self.assertTrue(lineage.is_traceable)
                self.assertTrue(lineage.methodology_ids)

    def test_appendix_resolves_every_source_reference(self):
        context = self.synth()
        appendix = synthesis_appendix(context)
        self.assertTrue(appendix["sources"])
        for source in appendix["sources"]:
            with self.subTest(source=source["id"]):
                self.assertTrue(
                    source["resolved"],
                    "a dangling provenance reference is a defect")

    def test_appendix_carries_no_source_text(self):
        """Part 22: identifiers, never passages."""
        context = self.synth()
        appendix = synthesis_appendix(context)
        for source in appendix["sources"]:
            with self.subTest(source=source["id"]):
                self.assertNotIn("incipit", source)
                self.assertLess(len(json.dumps(source)), 600)


# ── Part 21: profiles ────────────────────────────────────────────────────────

class ProfileTest(_Base):

    def test_strict_is_materially_narrower(self):
        strict = self.synth(SynthesisProfile.STRICT)
        standard = self.synth(SynthesisProfile.STANDARD)
        strict_active = len([r for r in strict.results.values()
                             if r.activation is not ActivationLevel.INACTIVE])
        standard_active = len([r for r in standard.results.values()
                               if r.activation is not ActivationLevel.INACTIVE])
        self.assertLess(strict_active, standard_active)

    def test_strict_speaks_only_where_the_link_to_the_domain_is_sourced(self):
        """
        THE LAUNDERING TEST, which Part 7 says to keep permanently.

        The criterion has not changed since V1.5: a factor may carry a
        strict prediction only if the link FROM that factor TO that domain
        has a witness, not merely if the factor itself is well computed.

        What changed is the answer. V1.5 could name four domains, because
        the only source-qualified links in the engine were kāraka
        attributions. The V1.6 bhāva audit sourced the house and house-lord
        mappings, so strict now reaches sixteen — by producing evidence,
        with the gate untouched.

        RELATIONSHIPS is the one that still fails, and it fails for a real
        reason: BPHS 11.8 gives the seventh house `jāyā`, the wife, and no
        witness supports a general relationships domain distinct from
        marriage.
        """
        admissible = set(strict_admissible_domains())
        self.assertNotIn("RELATIONSHIPS", admissible)
        self.assertEqual(len(admissible), 16)

        strict = self.synth(SynthesisProfile.STRICT)
        for name, result in strict.results.items():
            if name in admissible:
                continue
            with self.subTest(domain=name):
                self.assertIs(result.activation, ActivationLevel.INACTIVE)
                self.assertEqual(result.natal_evidence, [])

    def test_an_unsourced_factor_is_refused_even_in_a_sourced_domain(self):
        """
        The gate is per-factor, not per-domain — which is the part that
        makes it a real gate rather than a label.

        CAREER is strict-eligible on BPHS 11.11. Its SIXTH-house mapping is
        not: that house's relevance to employment is a modern reading and
        BPHS 11.7 gives the sixth enemies and wounds. So career evidence
        arriving via the sixth is refused while evidence via the tenth is
        admitted, in the same domain, in the same run.
        """
        from engine.synthesis.domain_evidence import FactorType
        spec = spec_for(Domain.CAREER)
        self.assertTrue(spec.qualifies_for_strict(FactorType.HOUSE, 10))
        self.assertFalse(spec.qualifies_for_strict(FactorType.HOUSE, 6))
        self.assertTrue(spec.qualifies_for_strict(FactorType.HOUSE_LORD, 10))
        self.assertFalse(spec.qualifies_for_strict(FactorType.VARGA, "D10"))

    def test_shadbala_enters_strict_only_via_a_sourced_house_lord_link(self):
        """
        The exact example Part 7 gives.

        "10th lord has strong Shadbala" is not sufficient for CAREER unless
        "the 10th lord is relevant to CAREER" is also source-qualified. It
        now is — BPHS 21.2 makes a STRONG tenth lord bear on occupation —
        so the factor is admitted, and the admission is traceable to that
        verse rather than to the Shadbala computation being sound.
        """
        from engine.synthesis.domain_evidence import FactorType
        spec = spec_for(Domain.CAREER)
        mapping = next(m for m in spec.mappings
                       if m.factor_type is FactorType.HOUSE_LORD
                       and m.factor == 10)
        self.assertIn("BPHS_SA_21.1-8_KARMABHAVA", mapping.source_ref_ids)
        self.assertTrue(mapping.is_source_qualified)

        strict = self.synth(SynthesisProfile.STRICT)
        career = strict.result_for(Domain.CAREER)
        sources = {e.source_type for e in career.natal_evidence}
        self.assertTrue(
            {"shadbala", "house_lord"} & sources,
            "house-lord evidence should now reach strict CAREER synthesis")

    def test_strict_admits_no_transit_evidence(self):
        strict = self.synth(SynthesisProfile.STRICT)
        for result in strict.results.values():
            with self.subTest(domain=result.domain):
                self.assertEqual(result.transit_evidence, [])

    def test_every_result_states_its_profile(self):
        for profile in SynthesisProfile:
            context = self.synth(profile)
            for result in context.results.values():
                with self.subTest(profile=profile.value,
                                  domain=result.domain):
                    self.assertIs(result.profile, profile)
                    self.assertEqual(
                        result.to_dict()["synthesis_profile"], profile.value)

    def test_exclusions_are_recorded_not_dropped(self):
        context = self.synth(SynthesisProfile.STRICT)
        self.assertTrue(context.excluded_rules)
        for record in context.excluded_rules:
            with self.subTest(rule=record["rule_id"]):
                self.assertTrue(record["reasons"])

    def test_profiles_do_not_share_evidence_silently(self):
        strict = self.synth(SynthesisProfile.STRICT)
        experimental = self.synth(SynthesisProfile.EXPERIMENTAL)
        strict_rules = {r for result in strict.results.values()
                        for r in result.rule_ids}
        experimental_rules = {r for result in experimental.results.values()
                              for r in result.rule_ids}
        self.assertTrue(strict_rules <= experimental_rules)
        self.assertLess(len(strict_rules), len(experimental_rules))


# ── Parts 18, 19, 24: events and windows ─────────────────────────────────────

class EventCandidateTest(_Base):

    def test_candidates_are_produced_with_real_windows(self):
        context = self.synth()
        candidates = event_candidates(context, dasha=self.dasha)
        self.assertTrue(candidates)
        for candidate in candidates:
            with self.subTest(event=candidate.event_type.value):
                self.assertTrue(candidate.window.why)
                self.assertTrue(candidate.window.boundary_sources)
                self.assertLess(candidate.window.start, candidate.window.end)

    def test_a_window_contains_the_moment_it_was_computed_for(self):
        """
        Regression. An earlier narrowing rule clipped the window to the first
        event pair inside the dasha period, producing windows that closed a
        year before the date asked about — a confident statement about the
        wrong time.
        """
        from engine.transits.query import get_transit_events_between
        events = get_transit_events_between(
            MOMENT - datetime.timedelta(days=200),
            MOMENT + datetime.timedelta(days=200),
            planets=("Guru", "Shani"), kinds=("sign_ingress",),
            natal_chart=self.chart)
        context = self.synth()
        for candidate in event_candidates(context, dasha=self.dasha,
                                          transit_events=events):
            with self.subTest(event=candidate.event_type.value):
                self.assertTrue(
                    candidate.window.contains(MOMENT),
                    f"{candidate.window.start} → {candidate.window.end} does "
                    f"not contain {MOMENT}")

    def test_no_candidate_without_a_computable_window(self):
        """No dasha, no window, no candidate. No date is invented."""
        context = synthesise(
            self.features, moment=MOMENT, yoga_results=self.yogas,
            dasha=None, transit_snapshot=self.transits)
        self.assertEqual(event_candidates(context, dasha=None), [])

    def test_longevity_never_becomes_an_event(self):
        """
        Part 24. A longevity candidate with a window is a death prediction
        whatever it is labelled, so the domain is computed and never
        converted.
        """
        self.assertIn(Domain.LONGEVITY, NO_EVENT_DOMAINS)
        context = self.synth()
        candidates = event_candidates(context, dasha=self.dasha)
        self.assertNotIn("LONGEVITY", {c.domain for c in candidates})
        self.assertIn("LONGEVITY", context.results)

    def test_no_event_type_names_a_high_stakes_outcome(self):
        blob = " ".join(e.value for e in EventType).lower()
        for word in ("death", "disease", "diagnos", "pregnan", "illness",
                     "accident", "divorce"):
            self.assertNotIn(word, blob)

    def test_high_stakes_domains_carry_their_constraint(self):
        context = self.synth()
        for domain in HIGH_STAKES_DOMAINS:
            with self.subTest(domain=domain.value):
                result = context.results[domain.value]
                self.assertIn("Part 24", result.notes)

    def test_candidates_declare_they_are_not_predictions(self):
        context = self.synth()
        for candidate in event_candidates(context, dasha=self.dasha):
            with self.subTest(event=candidate.event_type.value):
                self.assertTrue(
                    candidate.to_dict()["is_candidate_not_prediction"])


# ── Part 25: the snapshot ────────────────────────────────────────────────────

class PredictionSnapshotTest(_Base):

    def test_snapshot_serialises_and_round_trips(self):
        context = self.synth()
        candidates = event_candidates(context, dasha=self.dasha)
        snapshot = build_prediction_snapshot(
            context, transit_snapshot=self.transits, candidates=candidates)
        data = json.loads(snapshot.to_json())
        for key in ("schema_version", "natal_snapshot_id",
                    "methodology_profile", "reliability", "dasha", "transits",
                    "domain_results", "event_candidates",
                    "evidence_appendix"):
            self.assertIn(key, data)

    def test_natal_snapshot_stays_out(self):
        """
        Part 25: the natal snapshot is referenced, never embedded.

        A chart is true for a lifetime and a synthesis for an afternoon;
        copying the first into the second produces a file that looks
        canonical and goes stale with nothing to say which half did.
        """
        context = self.synth()
        snapshot = build_prediction_snapshot(context).to_dict()
        self.assertNotIn("planets", snapshot)
        self.assertNotIn("lagna", snapshot)
        self.assertNotIn("vargas", snapshot)

    def test_natal_id_is_stable_across_regeneration(self):
        natal = {"schema_version": "1.2.0", "lagna": {"sign": "Meena"},
                 "generated": "2026-01-01T00:00:00"}
        again = dict(natal, generated="2026-09-27T12:00:00")
        self.assertEqual(natal_snapshot_id(natal), natal_snapshot_id(again))
        different = dict(natal, lagna={"sign": "Mesha"})
        self.assertNotEqual(natal_snapshot_id(natal),
                            natal_snapshot_id(different))

    def test_snapshot_keeps_the_four_claims_separate(self):
        context = self.synth()
        claims = build_prediction_snapshot(context).to_dict()["claims"]
        for key in ("computationally_tested", "externally_benchmarked",
                    "textual_source_located", "tradition_source_validated"):
            self.assertIn(key, claims)
        self.assertIn("Nothing", claims["tradition_source_validated"])

    def test_snapshot_lists_what_it_does_not_contain(self):
        context = self.synth()
        absent = build_prediction_snapshot(context).to_dict()["not_included"]
        blob = " ".join(absent).lower()
        for word in ("interpretation", "probabilit", "remed", "rectification"):
            self.assertIn(word, blob)


# ── Part 29: determinism ─────────────────────────────────────────────────────

class DeterminismTest(_Base):

    def test_two_runs_agree_exactly(self):
        first = self.synth()
        second = self.synth()
        self.assertEqual(
            json.dumps(first.to_dict()["domain_results"], sort_keys=True),
            json.dumps(second.to_dict()["domain_results"], sort_keys=True))

    def test_no_randomness_or_model_call_in_the_package(self):
        """
        Part 29: no LLM decides anything, and nothing here is stochastic.
        """
        import pathlib
        package = pathlib.Path(__file__).resolve().parent.parent / "engine" \
            / "synthesis"
        for path in package.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            with self.subTest(module=path.name):
                for banned in ("import random", "openai", "anthropic",
                               "requests.post", "urllib.request"):
                    self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
