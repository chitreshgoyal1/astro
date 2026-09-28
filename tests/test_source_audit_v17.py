"""
Source closure (V1.7 Parts 27, 28, 29, 37)
============================================
What the varga and gochara audits found, pinned so the findings cannot be
quietly widened.

THE PATTERN THIS RELEASE FOUND AGAIN

    V1.4 declared four works unavailable. V1.5 retrieved three of them.
    V1.6 declared that no passage assigns a divisional chart to a life
    area. V1.7 found it, one chapter after the chapter V1.6 read, in a
    file the engine had held and checksummed since V1.5.

    The pattern is not "the sources are hard to find". It is that a search
    stops at the first place the answer should have been. `RESOLVED_
    UNAVAILABLE_WORKS` records it at the scale of a work; these tests
    record it at the scale of a chapter.

WHAT A LOCATED PASSAGE DOES AND DOES NOT DO

    It does not validate an implementation. BPHS 7 assigns D4 to bhāgya,
    fortune — so locating the passage CONVICTS the engine's D4-for-property
    mapping rather than supporting it. Phaladīpikā 26 makes every transit
    result conditional on vedha, which the engine does not compute, so
    locating it leaves strict synthesis refusing transits for a narrower
    and better-documented reason than before.

    Both are recorded here, because a release that found a source and
    treated it as permission would be the failure this ladder exists to
    prevent.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.sources import ALL_WITNESSES, registry_summary
from engine.sources.editions import (
    BPHS_EN_7_VARGAVIVEKA, BPHS_SA_7_VARGAVIVEKA, BPHS_SANSKRIT_SD_FILES,
    PD_20_GOCHARA_FROM_LAGNA, PD_26_GOCHARA, bphs_checksum_for_chapter,
)
from engine.sources.models import SourceAuthority, ValidationStatus
from engine.synthesis.domain_evidence import FactorType
from engine.synthesis.domains import DOMAINS, Domain, spec_for

VARGAVIVEKA = "BPHS_SA_7.1-8_VARGAVIVEKA"


def _vargas():
    return [m for spec in DOMAINS.values() for m in spec.mappings
            if m.factor_type is FactorType.VARGA]


# ── Part 29: the varga-domain passage ────────────────────────────────────────

class VargaPassageTest(unittest.TestCase):

    def test_the_passage_is_registered_as_a_witness(self):
        ids = {w.id for w in ALL_WITNESSES}
        self.assertIn(VARGAVIVEKA, ids)
        self.assertIn("BPHS_EN_7.1-8_VARGAVIVEKA", ids)

    def test_it_points_at_the_file_that_actually_contains_chapter_7(self):
        """
        The V1.6 defect this guards against: three witnesses recorded the
        checksum of files that did not contain their chapters. Chapter 7
        is in par0110.itx, and the checksum is derived from the chapter
        rather than copied.
        """
        self.assertEqual(BPHS_SA_7_VARGAVIVEKA.chapter, "7")
        self.assertEqual(BPHS_SA_7_VARGAVIVEKA.checksum_if_local,
                         bphs_checksum_for_chapter(7))
        self.assertEqual(BPHS_SA_7_VARGAVIVEKA.checksum_if_local,
                         BPHS_SANSKRIT_SD_FILES["par0110.itx"])

    def test_the_sanskrit_and_the_translation_are_separate_witnesses(self):
        """
        A translator's reading of an ambiguous compound is an
        interpretation, not the text. Recording a translation under the
        original's name is the commonest provenance error in astrology
        software, and it matters most here: `mahat-phala` is glossed
        "i.e. livelihood etc." in a footnote and that gloss is the
        translator's.
        """
        self.assertIs(BPHS_SA_7_VARGAVIVEKA.authority,
                      SourceAuthority.PRINTED_SANSKRIT_EDITION)
        self.assertIs(BPHS_EN_7_VARGAVIVEKA.authority,
                      SourceAuthority.TRANSLATION)
        self.assertNotEqual(BPHS_SA_7_VARGAVIVEKA.id,
                            BPHS_EN_7_VARGAVIVEKA.id)
        self.assertIn("gloss is the translator's",
                      BPHS_EN_7_VARGAVIVEKA.notes)

    def test_the_witness_records_the_incipit_and_not_the_passage(self):
        """
        A short normalised incipit locates the verse. A full text would
        redistribute a corpus this application is not licensed to copy.
        """
        self.assertTrue(BPHS_SA_7_VARGAVIVEKA.incipit)
        self.assertLess(len(BPHS_SA_7_VARGAVIVEKA.incipit), 120)


class VargaMappingTest(unittest.TestCase):

    def test_exactly_six_mappings_state_the_verse_s_own_subject(self):
        """
        V1.7 asserted five. The sixth is WEALTH→D2, and it is a different
        kind of change from the other five.

        The other five were mappings the engine ALREADY SHIPPED, which the
        V1.7 audit then found the verse stating. D2→WEALTH went the other
        way: the audit found `horāyāṃ sampadādikam` in the passage and
        recorded that the engine had no such mapping at all. V1.8 added the
        mapping to match the verse, which is the only direction this
        project permits — the source is not adjusted to fit the code.

        So the count moved because the ENGINE changed, not because the
        reading did. Nothing about the original five was revised.
        """
        qualified = {(m.domain, m.factor) for m in _vargas()
                     if m.is_source_qualified}
        self.assertEqual(
            qualified,
            {("MARRIAGE", "D9"), ("CHILDREN", "D7"), ("EDUCATION", "D24"),
             ("SIBLINGS", "D3"), ("SPIRITUALITY", "D20"), ("WEALTH", "D2")})

    def test_the_wealth_mapping_was_added_to_match_the_verse(self):
        """
        Part 8 asked for integration, not for a switch to be flipped. The
        mapping has to carry the same evidence every other qualified varga
        carries, and go through the same gates.
        """
        mapping = next(m for m in _vargas()
                       if (m.domain, m.factor) == ("WEALTH", "D2"))
        self.assertTrue(mapping.is_source_qualified)
        self.assertIn(VARGAVIVEKA, mapping.source_ref_ids)
        self.assertEqual(mapping.textual_term, "sampad")
        self.assertIn("BPHS 7.1", mapping.textual_condition)

    def test_d2_can_confirm_and_can_never_challenge(self):
        """
        The horā reaches two rashis, so its lagna lord is always Chandra or
        Surya and neither can be exalted or debilitated there. The engine's
        varga confirmation asks about the lagna lord's dignity, so D2 can
        return SUPPORTIVE and can never return CHALLENGING.

        That is a property of the division rather than a defect, and it is
        pinned here so that a future release which starts reporting a
        challenging D2 has to explain what changed in the mechanism.
        """
        from engine.varga_metadata import range_limitation, restricted_charts

        self.assertEqual(restricted_charts(), {"D2": 2, "D30": 10})
        self.assertIn("2 rashis", range_limitation("D2"))
        self.assertEqual(range_limitation("D9"), "")

    def test_every_qualified_mapping_cites_the_passage_and_its_term(self):
        for mapping in _vargas():
            if not mapping.is_source_qualified:
                continue
            with self.subTest(domain=mapping.domain, chart=mapping.factor):
                self.assertIn(VARGAVIVEKA, mapping.source_ref_ids)
                self.assertTrue(mapping.textual_term.strip())
                self.assertIn("BPHS 7.", mapping.textual_condition)

    def test_a_nearby_subject_is_located_without_being_qualified(self):
        """
        D10 is given mahat-phala, "great fruit", and D12 is given parents
        specifically. Neither is the engine's domain, and widening a verse
        to fit a mapping is the error this audit exists to catch.
        """
        for domain, chart in (("CAREER", "D10"), ("FAMILY", "D12")):
            mapping = next(m for m in _vargas()
                           if (m.domain, m.factor) == (domain, chart))
            with self.subTest(domain=domain, chart=chart):
                self.assertTrue(mapping.is_located)
                self.assertFalse(mapping.is_source_qualified)
                self.assertIs(mapping.validation_status,
                              ValidationStatus.RULE_INTERPRETATION_MAPPED)

    def test_the_career_mapping_records_that_the_verse_does_not_say_vrtti(self):
        mapping = next(m for m in _vargas()
                       if (m.domain, m.factor) == ("CAREER", "D10"))
        self.assertIn("mahat-phala", mapping.textual_term)
        self.assertIn("vṛtti", mapping.textual_condition)

    def test_d4_for_property_is_recorded_as_contradicted_not_merely_absent(self):
        """
        Part 27 asks for an honest classification. "Unsourced" would not
        be one: BPHS 7.2 assigns the caturthāṃśa to bhāgya, so the located
        verse points somewhere else.
        """
        mapping = next(m for m in _vargas()
                       if (m.domain, m.factor) == ("PROPERTY", "D4"))
        self.assertFalse(mapping.is_source_qualified)
        self.assertIn("bhāgya", mapping.notes)

    def test_d6_is_not_one_of_the_sixteen_divisions(self):
        mapping = next(m for m in _vargas()
                       if (m.domain, m.factor) == ("HEALTH", "D6"))
        self.assertIn("sixteen", mapping.notes)
        from engine.vargas import VARGA_ORDER
        self.assertNotIn("D6", VARGA_ORDER)

    def test_no_unsourced_mapping_pretends_to_a_textual_condition(self):
        """
        A mapping with no witness must put its explanation in `notes`.
        Putting it in `textual_condition` would dress an editorial
        decision as a quotation and make it indistinguishable at a glance
        from a located one.
        """
        for mapping in _vargas():
            with self.subTest(domain=mapping.domain, chart=mapping.factor):
                if mapping.source_ref_ids:
                    self.assertTrue(mapping.textual_condition.strip())
                else:
                    self.assertFalse(mapping.textual_condition.strip())
                    self.assertTrue(mapping.notes.strip())

    def test_the_strict_gate_now_asks_the_source_question_of_vargas(self):
        """
        The Part 7 laundering gate, applied to vargas. Until V1.7 nothing
        asked it — a perfectly stable D10 could carry a CAREER conclusion
        into strict synthesis on a mapping resting on nothing. V1.6 could
        not see this, because no varga was qualified then and the missing
        gate would have changed no result.
        """
        self.assertTrue(
            spec_for(Domain.MARRIAGE).qualifies_for_strict(
                FactorType.VARGA, "D9"))
        self.assertFalse(
            spec_for(Domain.CAREER).qualifies_for_strict(
                FactorType.VARGA, "D10"))
        self.assertFalse(
            spec_for(Domain.PROPERTY).qualifies_for_strict(
                FactorType.VARGA, "D4"))


class VargaGateBehaviourTest(unittest.TestCase):
    """The gate, exercised through a real synthesis rather than asserted."""

    @classmethod
    def setUpClass(cls):
        import datetime

        from app.models import ConsultationRecord
        from app.services import calculate_chart, calculate_prediction

        natal = calculate_chart(ConsultationRecord(
            name="Audit", date_of_birth="1988-08-30", time_of_birth="20:18",
            place="Jaipur"))
        moment = datetime.datetime(2026, 9, 27, 12)
        cls.strict = calculate_prediction(natal, moment, profile="strict")
        cls.standard = calculate_prediction(natal, moment, profile="standard")

    def _charts(self, prediction) -> set:
        return {(domain, item["chart"])
                for domain, result in prediction.snapshot[
                    "domain_results"].items()
                for item in result.get("varga_evidence") or []}

    def test_strict_admits_only_source_qualified_varga_evidence(self):
        for domain, chart in self._charts(self.strict):
            with self.subTest(domain=domain, chart=chart):
                self.assertTrue(
                    spec_for(Domain(domain)).qualifies_for_strict(
                        FactorType.VARGA, chart))

    def test_standard_admits_conventional_mappings_that_strict_refuses(self):
        """
        Both profiles must be exercised, or the gate could be passing by
        admitting nothing at all.
        """
        standard_only = self._charts(self.standard) - self._charts(self.strict)
        self.assertTrue(
            standard_only,
            "standard should use at least one mapping strict refuses")
        for domain, chart in standard_only:
            with self.subTest(domain=domain, chart=chart):
                self.assertFalse(
                    spec_for(Domain(domain)).qualifies_for_strict(
                        FactorType.VARGA, chart))


# ── Part 28: gochara ─────────────────────────────────────────────────────────

class GocharaAuditTest(unittest.TestCase):

    def test_the_gochara_chapter_is_registered(self):
        ids = {w.id for w in ALL_WITNESSES}
        self.assertIn(PD_26_GOCHARA.id, ids)
        self.assertIn(PD_20_GOCHARA_FROM_LAGNA.id, ids)

    def test_the_moon_is_recorded_as_the_primary_reference_frame(self):
        """
        Phaladīpikā 26.1 settles it outright: though all the lagnas exist,
        in transits the candra-lagna is primary. V1.6 had no witness for
        either frame and refused both.
        """
        self.assertIn("candralagnaṃ pradhānaṃ", PD_26_GOCHARA.incipit)
        self.assertIn("CANDRA-LAGNA is primary", PD_26_GOCHARA.notes)

    def test_the_witness_records_that_the_engine_does_not_implement_it(self):
        """
        The distinction the ladder exists for. A located source is not a
        validated implementation, and this witness says so in its own
        notes rather than leaving a reader to assume otherwise.
        """
        self.assertIn("engine implements none of this", PD_26_GOCHARA.notes)
        self.assertIn("without validating the IMPLEMENTATION",
                      PD_26_GOCHARA.notes)

    def test_the_dasha_lord_condition_is_recorded(self):
        """
        Phaladīpikā 20.34-35 is the closest thing in any located text to
        the hierarchy V1.5 built: the transiting graha is the running
        daśā lord, and its effect is conditioned on its natal strength.
        The engine applies neither condition.
        """
        notes = PD_20_GOCHARA_FROM_LAGNA.notes
        self.assertIn("daśā lord", notes)
        self.assertIn("NATAL strength", notes)
        self.assertIn("Natal → Daśā → Transit", notes)

    def test_strict_synthesis_still_refuses_transit_evidence(self):
        """
        Locating a source is not permission. The passage describes a rule
        with a favourable-house list and a vedha check; the engine records
        that a graha occupies a house. Strict must keep refusing until the
        implementation is the rule the text states.
        """
        import datetime

        from app.models import ConsultationRecord
        from app.services import calculate_chart, calculate_prediction

        natal = calculate_chart(ConsultationRecord(
            name="Gochara", date_of_birth="1988-08-30",
            time_of_birth="20:18", place="Jaipur"))
        strict = calculate_prediction(
            natal, datetime.datetime(2026, 9, 27, 12), profile="strict")
        transits = [item for result in strict.snapshot[
            "domain_results"].values()
            for item in result.get("transit_evidence") or []]
        self.assertEqual(
            transits, [],
            "strict must not use a transit rule the engine does not "
            "implement as the text states it")


# ── the registry as a whole ──────────────────────────────────────────────────

class RegistryTest(unittest.TestCase):

    def test_the_new_witnesses_are_counted(self):
        summary = registry_summary()
        self.assertGreaterEqual(summary["witnesses_registered"], 43)
        self.assertGreaterEqual(summary["sanskrit_tier_witnesses"], 38)

    def test_nothing_is_tradition_validated(self):
        """
        The claim no release has made and this one does not either.
        Finding a passage is not a scholar confirming that the passage
        states the rule.
        """
        self.assertEqual(registry_summary()["tradition_validated"], 0)

    def test_saravali_is_still_recorded_as_without_a_witness(self):
        """
        Possession of a file is not possession of a text. V1.6 kept
        Sārāvalī in the unavailable list with a reason beginning
        "RETRIEVED BUT NOT READ", and V1.7 did not read it either.
        """
        self.assertIn("SARAVALI",
                      registry_summary()["works_without_any_witness"])


if __name__ == "__main__":
    unittest.main()
