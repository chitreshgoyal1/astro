"""
Domain source validation (V1.6 Parts 1-8, 34)
-----------------------------------------------
Pins the V1.6 bhāva audit: which mappings were located, which were
corrected, and — more importantly — which are still not sourced.

The tests that matter most are the ones asserting a mapping is NOT
qualified. A release that sourced everything would have nothing left to
protect; what needs protecting is the boundary between what was read and
what was assumed, because that boundary is invisible in the output.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.sources import ValidationStatus, conflict_by_id, witness_by_id
from engine.sources.editions import (
    BPHS_SANSKRIT_SD_CHAPTER_FILES, BPHS_SANSKRIT_SD_EDITION_IDENTITY,
    BPHS_SANSKRIT_SD_FILES, bphs_file_for_chapter,
)
from engine.synthesis.domain_evidence import FactorType, coverage
from engine.synthesis.domains import (
    DOMAINS, Domain, all_mappings, domain_mapping_summary, spec_for,
    strict_domains,
)

BHAVAVIVEKA = "BPHS_SA_11.2-13_BHAVAVIVEKA"


# ── Parts 1, 2: the house significations ─────────────────────────────────────

class HouseSignificationTest(unittest.TestCase):
    """
    BPHS 11.2-13 gives twelve verses, one per bhāva. These are the domains
    whose primary house the chapter names in a single word.
    """

    # (domain, house, the Sanskrit term the verse uses)
    ATTESTED = (
        (Domain.CAREER, 10, "vṛtti"),
        (Domain.MARRIAGE, 7, "jāyā"),
        (Domain.CHILDREN, 5, "putra"),
        (Domain.EDUCATION, 5, "vidyā"),
        (Domain.FINANCE, 11, "āya"),
        (Domain.WEALTH, 2, "dhana-dhānya"),
        (Domain.FAMILY, 2, "kuṭumba"),
        (Domain.SIBLINGS, 3, "bhrātṛ"),
        (Domain.PROPERTY, 4, "kṣetra, gṛha, vāhana"),
        (Domain.LONGEVITY, 8, "āyus"),
        (Domain.SPIRITUALITY, 9, "dharma"),
        (Domain.BUSINESS, 7, "vāṇijya"),
        (Domain.LITIGATION, 6, "śatru"),
        (Domain.HEALTH, 1, "deha, balābala"),
        (Domain.TRAVEL, 3, "prayāṇa"),
    )

    def test_primary_houses_match_the_verse(self):
        for domain, house, term in self.ATTESTED:
            with self.subTest(domain=domain.value):
                spec = spec_for(domain)
                self.assertEqual(spec.primary_house, house)
                mapping = next(
                    m for m in spec.factors(FactorType.HOUSE, primary=True))
                self.assertEqual(mapping.textual_term, term)
                self.assertTrue(mapping.is_source_qualified)

    def test_every_attested_house_cites_the_bhavaviveka_chapter(self):
        for domain, _house, _term in self.ATTESTED:
            spec = spec_for(domain)
            mapping = next(
                m for m in spec.factors(FactorType.HOUSE, primary=True))
            with self.subTest(domain=domain.value):
                self.assertTrue(
                    set(mapping.source_ref_ids)
                    & {BHAVAVIVEKA, "BPHS_SA_23.9-11_VYAYABHAVA"})

    def test_foreign_residence_rests_on_the_twelfth_house_chapter(self):
        """
        The one primary house not in ch.11: BPHS 23.11 gives `deśād
        deśāntaraṃ gataḥ` for an afflicted twelfth and its lord.
        """
        spec = spec_for(Domain.FOREIGN_RESIDENCE)
        self.assertEqual(spec.primary_house, 12)
        mapping = next(m for m in spec.factors(FactorType.HOUSE, primary=True))
        self.assertIn("BPHS_SA_23.9-11_VYAYABHAVA", mapping.source_ref_ids)
        self.assertEqual(mapping.textual_term, "deśāntara")


# ── the corrections ──────────────────────────────────────────────────────────

class CorrectionTest(unittest.TestCase):

    def test_education_moved_from_the_fourth_to_the_fifth(self):
        """
        CHANGED IN V1.6. BPHS 11.6 puts `vidyā` in the fifth; 11.5 gives the
        fourth vehicles, relatives, the mother's comfort, treasure, land and
        house, and no learning.
        """
        spec = spec_for(Domain.EDUCATION)
        self.assertEqual(spec.primary_house, 5)
        fourth = next(m for m in spec.factors(FactorType.HOUSE)
                      if m.factor == 4)
        self.assertFalse(fourth.is_source_qualified)
        self.assertFalse(fourth.is_primary)
        self.assertIn("V1.5", fourth.notes)

    def test_travel_dropped_the_twelfth_and_gained_the_seventh(self):
        spec = spec_for(Domain.TRAVEL)
        houses = set(spec.all_houses)
        self.assertEqual(houses, {3, 7, 9})
        self.assertNotIn(12, houses)

    def test_relationships_has_no_located_house_witness(self):
        """
        BPHS 11.8 gives the seventh `jāyā`, the wife. A general
        relationships domain is a modern convenience, and the engine says so
        rather than borrowing marriage's witness for it.
        """
        spec = spec_for(Domain.RELATIONSHIPS)
        for mapping in spec.factors(FactorType.HOUSE):
            with self.subTest(house=mapping.factor):
                self.assertFalse(mapping.is_located)
                self.assertFalse(mapping.is_source_qualified)
        self.assertFalse(spec.strict_eligible)
        self.assertNotIn("RELATIONSHIPS", strict_domains())


# ── Parts 3, 7: factor types stay independent ────────────────────────────────

class FactorIndependenceTest(unittest.TestCase):

    def test_career_has_three_factor_types_with_different_standing(self):
        """
        Part 3: house, house lord and varga are separate claims. Career has
        all three and they are not equally sourced, which is the point.
        """
        spec = spec_for(Domain.CAREER)
        self.assertTrue(spec.qualifies_for_strict(FactorType.HOUSE, 10))
        self.assertTrue(spec.qualifies_for_strict(FactorType.HOUSE_LORD, 10))
        self.assertFalse(spec.qualifies_for_strict(FactorType.VARGA, "D10"))

    def test_house_lord_evidence_rests_on_its_own_chapter(self):
        """
        BPHS 11.14-16 states the doctrine and ch.24 works it out lord by
        lord. Without those, treating a lord's condition as evidence about
        its house would be an inference the engine had made up.
        """
        spec = spec_for(Domain.CAREER)
        mapping = next(m for m in spec.factors(FactorType.HOUSE_LORD))
        self.assertIn("BPHS_SA_21.1-8_KARMABHAVA", mapping.source_ref_ids)
        self.assertTrue(
            {"BPHS_SA_11.14-16_BHAVA_STRENGTH", "BPHS_SA_24_BHAVESHAPHALA"}
            & set(mapping.source_ref_ids))

    def test_varga_coverage_is_partial_and_says_which_part(self):
        """
        REPLACES `test_no_varga_mapping_anywhere_is_qualified` (V1.6).

        That test pinned V1.6's finding that no varga mapping is located.
        The V1.7 audit found BPHS 7.1-6, which assigns a subject to each
        of the sixteen divisions, so the finding no longer holds and the
        assertion is replaced rather than weakened.

        What it now pins is that coverage is PARTIAL. A later release that
        marked the remaining six as located, or that quietly dropped the
        two located-but-unqualified ones to make the numbers tidier, would
        fail here.
        """
        stats = coverage(all_mappings())["VARGA"]
        # V1.8: 11 → 12 and 5 → 6, because WEALTH→D2 was ADDED to match a
        # verse the V1.7 audit had already read and recorded as an
        # unimplemented mapping. The reading did not move; the engine did.
        self.assertEqual(stats["total"], 12)
        self.assertEqual(
            stats["located"], 8,
            "six state the verse's subject, two name a nearby one")
        self.assertEqual(
            stats["source_qualified"], 6,
            "only the six whose subject IS the engine's domain qualify")

    def test_unsourced_secondary_houses_are_marked(self):
        """
        Several secondary houses are modern readings and stay in, marked.
        CAREER's sixth is the clearest: BPHS 11.7 gives the sixth enemies
        and wounds, and its association with employment is not in the verse.
        """
        career = spec_for(Domain.CAREER)
        sixth = next(m for m in career.factors(FactorType.HOUSE)
                     if m.factor == 6)
        self.assertFalse(sixth.is_source_qualified)
        self.assertTrue(sixth.needs_human_review)


# ── Part 4: the karaka audit ─────────────────────────────────────────────────

class KarakaAuditTest(unittest.TestCase):

    def test_bhava_karaka_scheme_is_registered(self):
        witness = witness_by_id("BPHS_SA_32.22-24_BHAVA_KARAKA")
        self.assertEqual(witness.chapter, "32")
        self.assertEqual(witness.verse_start, "22")
        self.assertIn("kheṭabhāvavaśād", witness.incipit)

    def test_putrakaraka_conflict_resolved_without_discarding_either(self):
        """
        Part 4: do not choose a reading automatically, and register both.

        BPHS 32.20 gives the son from Saturn; 32.23 gives the son from
        Jupiter. Both are in the same chapter, both ship, and the engine
        qualifies only the one whose scheme matches the use it is put to.
        """
        spec = spec_for(Domain.CHILDREN)
        karakas = {m.factor: m for m in spec.factors(FactorType.KARAKA)}
        self.assertIn("Guru", karakas)
        self.assertIn("Shani", karakas)
        self.assertTrue(karakas["Guru"].is_located)
        self.assertTrue(karakas["Shani"].is_located)
        self.assertTrue(karakas["Guru"].is_source_qualified)
        self.assertFalse(karakas["Shani"].is_source_qualified)
        self.assertIn("PUTRAKARAKA_ATTRIBUTION", karakas["Shani"].conflicts)
        self.assertTrue(karakas["Shani"].needs_human_review)

    def test_saturn_is_qualified_for_longevity_instead(self):
        """BPHS 32.24: `mandād aṣṭamato mṛtyuḥ`."""
        spec = spec_for(Domain.LONGEVITY)
        self.assertTrue(spec.qualifies_for_strict(FactorType.KARAKA, "Shani"))

    def test_venus_is_attested_twice_for_marriage(self):
        """
        The best-sourced kāraka in the engine: BPHS 32.20 `śukrāt patiḥ` and
        32.23 `dārāḥ śukrāc ca saptame`, two schemes agreeing.
        """
        spec = spec_for(Domain.MARRIAGE)
        mapping = next(m for m in spec.factors(FactorType.KARAKA)
                       if m.factor == "Shukra")
        self.assertEqual(len(mapping.source_ref_ids), 2)
        self.assertTrue(mapping.is_source_qualified)

    def test_most_karakas_remain_unsourced(self):
        """
        The honest counterweight. Sun-for-authority, Jupiter-for-wealth and
        Mercury-for-intellect are universal in practice and are in no kāraka
        scheme this engine has read.
        """
        stats = coverage(all_mappings())["KARAKA"]
        self.assertLess(stats["source_qualified"], stats["total"] / 2)


# ── Part 5: edition identity ─────────────────────────────────────────────────

class EditionIdentityTest(unittest.TestCase):

    def test_edition_identity_is_explicitly_unresolved(self):
        """
        The brief says to mark it explicitly if it stays unresolved. It did.
        """
        identity = BPHS_SANSKRIT_SD_EDITION_IDENTITY
        self.assertEqual(identity["status"], "UNRESOLVED")
        for field in ("what_is_known", "what_is_not_known", "why_it_matters",
                      "what_was_tried_in_v16", "what_would_resolve_it",
                      "consequence_for_validation"):
            with self.subTest(field=field):
                self.assertTrue(identity[field])

    def test_every_retrieved_file_has_a_checksum(self):
        for _first, _last, name in BPHS_SANSKRIT_SD_CHAPTER_FILES:
            with self.subTest(file=name):
                self.assertIn(name, BPHS_SANSKRIT_SD_FILES)
                self.assertEqual(len(BPHS_SANSKRIT_SD_FILES[name]), 64)

    def test_chapter_to_file_mapping_covers_the_whole_work(self):
        for chapter in range(1, 98):
            with self.subTest(chapter=chapter):
                self.assertIn(bphs_file_for_chapter(chapter),
                              BPHS_SANSKRIT_SD_FILES)
        with self.assertRaises(KeyError):
            bphs_file_for_chapter(98)

    def test_every_bphs_witness_checksums_the_file_its_chapter_is_in(self):
        """
        The check that caught a real V1.5 defect.

        The kāraka witness recorded par2130's checksum for a chapter that
        lives in par3140, which would have sent anyone verifying the locator
        to the wrong file. A citation whose checksum points elsewhere is
        worse than one with no checksum, because it looks verified.
        """
        from engine.sources import ALL_WITNESSES
        for witness in ALL_WITNESSES:
            if not witness.id.startswith("BPHS_SA_"):
                continue
            with self.subTest(witness=witness.id):
                expected = BPHS_SANSKRIT_SD_FILES[
                    bphs_file_for_chapter(int(witness.chapter))]
                self.assertEqual(
                    witness.checksum_if_local, expected,
                    f"{witness.id} cites chapter {witness.chapter}, which is "
                    f"in {bphs_file_for_chapter(int(witness.chapter))}")


# ── Part 8: coverage ─────────────────────────────────────────────────────────

class CoverageTest(unittest.TestCase):

    def test_sixteen_of_seventeen_domains_are_strict_eligible(self):
        eligible = strict_domains()
        self.assertEqual(len(eligible), 16)
        self.assertNotIn("RELATIONSHIPS", eligible)

    def test_summary_does_not_overstate(self):
        summary = domain_mapping_summary()
        self.assertLessEqual(summary["mappings_source_qualified"],
                             summary["mappings_located"])
        self.assertLessEqual(summary["mappings_located"],
                             summary["mappings_total"])

    def test_report_generator_runs(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/generate_domain_report.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for heading in ("# DOMAIN_VALIDATION.md", "## The five factor types",
                        "## Mappings V1.6 corrected", "## Domain by domain",
                        "## What remains unsourced",
                        "## The edition question (Part 5)"):
            with self.subTest(heading=heading):
                self.assertIn(heading, result.stdout)

    def test_report_states_the_before_and_after(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/generate_domain_report.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True)
        self.assertIn("| House mappings with a witness | 0 |", result.stdout)
        self.assertIn("| Varga mappings with a witness | 0 | 0 |",
                      result.stdout)


if __name__ == "__main__":
    unittest.main()
