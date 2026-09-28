"""
Source registry and provenance integrity (V1.3 Parts 2-11, 15, 16)
-------------------------------------------------------------------
These tests cannot prove that a text is historically authentic, that an
edition is sound, or that a rule is astrologically correct. Nothing in a test
suite can.

What they CAN prove is provenance integrity: that every claim the engine makes
about its own evidence is backed by the evidence it says it has, that no claim
is stronger than what was actually examined, and that the categories cannot
quietly leak into one another.

The single most important test here is
`test_nothing_claims_tradition_validated`. The moment that starts failing,
someone has asserted the strongest claim in the system and the assertion needs
a human to confirm it was earned.
"""

# V1.3.

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.rules import RULE_PROFILES, all_rules, rules_for_profile
from engine.rules.catalog import (
    EVIDENCE_GATED_PROFILE, strict_profile_admits, strict_profile_rejections,
)
from engine.sources import (
    ALL_WITNESSES, CONFLICTS, REGISTRY_VERSION, RESOLVED_UNAVAILABLE_WORKS,
    REVIEW_QUEUE,
    STRICT_PROFILE_MINIMUM, UNAVAILABLE_WORKS, RuleClassification,
    SourceAuthority, ValidationStatus, all_recorded_evidence, conflict_by_id,
    evidence_for, highest_supportable_status, overclaimed, registry_summary,
    strict_profile_eligible, unmet_requirements, witness_by_id, witnesses_for,
)
from engine.varga_metadata import all_metadata, metadata_for
from engine.vargas import VARGA_ORDER, VARGA_SPECS


def varga_subjects() -> list[str]:
    return [f"{chart}/{convention}"
            for chart in VARGA_ORDER
            for convention in VARGA_SPECS[chart].conventions]


# ── Part 2: witness integrity ────────────────────────────────────────────────

class WitnessIntegrityTest(unittest.TestCase):

    def test_witness_ids_are_unique(self):
        ids = [w.id for w in ALL_WITNESSES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_witness_names_its_work(self):
        for witness in ALL_WITNESSES:
            with self.subTest(witness=witness.id):
                self.assertTrue(witness.work)
                self.assertTrue(witness.language)

    def test_passage_witnesses_carry_a_locator(self):
        """A witness to a rule must identify a passage, not merely a work."""
        passage_witnesses = [w for w in ALL_WITNESSES if w.chapter]
        self.assertTrue(passage_witnesses)
        for witness in passage_witnesses:
            with self.subTest(witness=witness.id):
                self.assertTrue(witness.has_locator)

    def test_every_witness_identifies_its_edition(self):
        """Part 7: a work name without an edition does not identify a text."""
        for witness in ALL_WITNESSES:
            with self.subTest(witness=witness.id):
                self.assertTrue(
                    witness.identifies_edition,
                    f"{witness.id} names no edition, publisher or retrieval "
                    f"source, so it cannot identify which text was read")

    def test_digital_witnesses_carry_a_checksum(self):
        for witness in ALL_WITNESSES:
            if not witness.retrieved_from:
                continue
            with self.subTest(witness=witness.id):
                self.assertTrue(witness.checksum_if_local)
                self.assertEqual(len(witness.checksum_if_local), 64)

    def test_no_dangling_witness_references(self):
        """Part 16: every source ID resolves."""
        for evidence in all_recorded_evidence():
            for witness_id in evidence.witness_ids:
                with self.subTest(subject=evidence.subject, ref=witness_id):
                    self.assertIsNotNone(witness_by_id(witness_id))

    def test_unknown_witness_id_raises(self):
        with self.assertRaises(KeyError):
            witness_by_id("NO_SUCH_WITNESS")

    def test_unavailable_works_are_recorded_explicitly(self):
        """
        The absence of a witness is data.

        CHANGED IN V1.4 AND AGAIN IN V1.5, deliberately, and the sequence is
        worth reading as a whole.

        V1.3 recorded plain "BPHS" as unavailable after one retrieval method
        failed. Wrong: V1.4 obtained the Santhanam translation on a second
        attempt, and renamed the key to "BPHS_SANSKRIT" because what was
        genuinely missing was a Sanskrit witness.

        V1.4's narrowed claim was also wrong. V1.5 obtained a Sanskrit BPHS,
        plus Phaladīpikā and Jātaka Pārijāta, from sanskritdocuments.org —
        a repository neither earlier release had tried. All three keys are
        gone from this table and are recorded in RESOLVED_UNAVAILABLE_WORKS
        instead, with the claim they overturned.

        What is left is Sārāvalī, and it is left for a different reason than
        any of the others: the scan was retrieved in full and has no text
        layer, so the work is in hand and has not been read. This test now
        pins that distinction, because it is the one the table exists to
        make.
        """
        self.assertNotIn("BPHS", UNAVAILABLE_WORKS)
        self.assertNotIn(
            "BPHS_SANSKRIT", UNAVAILABLE_WORKS,
            "a Sanskrit BPHS was obtained in V1.5; V1.4's claim that none "
            "existed was a claim about its own searching")
        for key in ("BPHS_SANSKRIT", "PHALADEEPIKA", "JATAKA_PARIJATA"):
            with self.subTest(resolved=key):
                self.assertIn(key, RESOLVED_UNAVAILABLE_WORKS)
                entry = RESOLVED_UNAVAILABLE_WORKS[key]
                self.assertTrue(entry["now_registered_as"])
                self.assertTrue(entry["v14_claim"])
                self.assertTrue(entry["what_was_actually_true"])

        self.assertIn(
            "SARAVALI", UNAVAILABLE_WORKS,
            "retrieved but unreadable is still unavailable: possession of a "
            "file is not possession of a text")
        for key, entry in UNAVAILABLE_WORKS.items():
            with self.subTest(work=key):
                for field in ("work", "why_unavailable", "consequence",
                              "what_would_resolve_it"):
                    self.assertTrue(entry.get(field))

    def test_every_unavailable_work_records_what_was_tried(self):
        """
        V1.4 lesson: "we could not find it" is a claim about the search, not
        about the text. V1.3 stated it as though it were about the text and
        was wrong. Every gap now carries its retrieval history.
        """
        for key, entry in UNAVAILABLE_WORKS.items():
            with self.subTest(work=key):
                self.assertTrue(entry.get("retrieval_attempts"))

    def test_bphs_translation_was_acquired(self):
        """The V1.3 correction, pinned so it cannot silently regress."""
        from engine.sources import witness_by_id
        witness = witness_by_id("BPHS_27_SHADBALA")
        self.assertEqual(witness.authority, SourceAuthority.TRANSLATION)
        self.assertEqual(witness.chapter, "27")
        self.assertIn("Santhanam", witness.editor_or_translator)

    def test_bphs_translation_cannot_reach_sanskrit_tier(self):
        """A translation is a witness to the translator, not to the text."""
        from engine.sources import witness_by_id
        for witness_id in ("BPHS_27_SHADBALA", "BPHS_66_ASHTAKAVARGA"):
            with self.subTest(witness=witness_id):
                self.assertFalse(
                    witness_by_id(witness_id).authority.is_sanskrit_tier)

    def test_citation_renders(self):
        for witness in ALL_WITNESSES:
            with self.subTest(witness=witness.id):
                self.assertTrue(witness.citation())


# ── Part 3: authority levels ─────────────────────────────────────────────────

class AuthorityTest(unittest.TestCase):

    def test_all_levels_exist(self):
        for name in ("PRIMARY_SANSKRIT_WITNESS", "PRINTED_SANSKRIT_EDITION",
                     "CLASSICAL_COMMENTARY", "TRANSLATION",
                     "MODERN_COMMENTARY", "SECONDARY_REFERENCE",
                     "WEB_SUMMARY"):
            with self.subTest(level=name):
                self.assertTrue(hasattr(SourceAuthority, name))

    def test_web_summary_can_never_support_validation(self):
        """Part 3, stated as an absolute. This is the rule that must not bend."""
        self.assertFalse(SourceAuthority.WEB_SUMMARY.can_support_validation)
        for authority in SourceAuthority:
            if authority is SourceAuthority.WEB_SUMMARY:
                continue
            with self.subTest(authority=authority.value):
                self.assertTrue(authority.can_support_validation)

    def test_only_sanskrit_tiers_are_sanskrit_tier(self):
        sanskrit = {a for a in SourceAuthority if a.is_sanskrit_tier}
        self.assertEqual(sanskrit, {SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
                                    SourceAuthority.PRINTED_SANSKRIT_EDITION})

    def test_a_translation_is_not_the_original(self):
        """A translation is a separate, weaker witness — never the text."""
        self.assertFalse(SourceAuthority.TRANSLATION.is_sanskrit_tier)
        self.assertGreater(SourceAuthority.TRANSLATION.rank,
                           SourceAuthority.PRIMARY_SANSKRIT_WITNESS.rank)

    def test_ranking_is_strict(self):
        ranks = [a.rank for a in SourceAuthority]
        self.assertEqual(len(ranks), len(set(ranks)))


# ── Part 4: the validation lifecycle ─────────────────────────────────────────

class ValidationLifecycleTest(unittest.TestCase):

    def test_all_states_exist(self):
        for name in ("UNVERIFIED", "TEXT_LOCATED", "WITNESS_RECORDED",
                     "TRANSLATION_CHECKED", "RULE_INTERPRETATION_MAPPED",
                     "IMPLEMENTATION_MATCHED", "SECOND_WITNESS_CHECKED",
                     "TRADITION_VALIDATED", "CONFLICTING_SOURCES"):
            with self.subTest(state=name):
                self.assertTrue(hasattr(ValidationStatus, name))

    def test_no_evidence_overclaims_its_status(self):
        """
        Every declared status must be supported by the evidence recorded for
        it. This is what makes the status field a checked claim rather than a
        label somebody typed.
        """
        for evidence in all_recorded_evidence():
            witnesses = witnesses_for(evidence.subject)
            with self.subTest(subject=evidence.subject):
                self.assertFalse(
                    overclaimed(evidence, witnesses),
                    f"{evidence.subject} claims "
                    f"{evidence.validation_status.value} but is missing: "
                    f"{unmet_requirements(evidence, witnesses)}")

    def test_unverified_needs_no_evidence(self):
        evidence = evidence_for("no_such_rule_at_all")
        self.assertEqual(evidence.validation_status, ValidationStatus.UNVERIFIED)
        self.assertEqual(unmet_requirements(evidence, []), [])

    def test_cannot_claim_text_located_without_a_witness(self):
        from engine.sources.models import RuleEvidence
        bare = RuleEvidence(subject="x",
                            validation_status=ValidationStatus.TEXT_LOCATED)
        self.assertTrue(unmet_requirements(bare, []))

    def test_cannot_claim_validated_on_a_web_summary_alone(self):
        """Part 16, stated directly."""
        from engine.sources.models import (
            RuleEvidence, SourceType, SourceWitness,
        )
        web = SourceWitness(
            id="WEB", work="Some astrology site",
            authority=SourceAuthority.WEB_SUMMARY,
            source_type=SourceType.WEBSITE, chapter="6", verse_start="1",
            edition="website", retrieved_from="https://example.invalid")
        evidence = RuleEvidence(
            subject="x",
            validation_status=ValidationStatus.TRADITION_VALIDATED,
            witness_ids=("WEB",), textual_condition="something",
            software_condition="something", implementation_test="somewhere")
        missing = unmet_requirements(evidence, [web])
        self.assertTrue(missing)
        self.assertTrue(any("web-summary" in m or "Sanskrit-tier" in m
                            for m in missing))

    def test_conflicting_sources_never_satisfies_a_floor(self):
        self.assertFalse(
            ValidationStatus.CONFLICTING_SOURCES.at_least(
                ValidationStatus.TEXT_LOCATED))

    def test_highest_supportable_status_is_honest(self):
        for evidence in all_recorded_evidence():
            if evidence.validation_status is ValidationStatus.CONFLICTING_SOURCES:
                continue
            witnesses = witnesses_for(evidence.subject)
            with self.subTest(subject=evidence.subject):
                self.assertTrue(
                    highest_supportable_status(evidence, witnesses)
                    .at_least(evidence.validation_status))


class NothingIsOverclaimedTest(unittest.TestCase):
    """The claims this build is careful NOT to make."""

    def test_nothing_claims_tradition_validated(self):
        """
        THE LOAD-BEARING TEST.

        TRADITION_VALIDATED means a Sanskrit-tier witness, a second
        independent witness, an implementation mapping and completed human
        review all agree. Nothing in this engine has all four.

        If this test starts failing, someone has asserted the strongest claim
        in the system. That is not necessarily wrong — but it must be a
        deliberate act confirmed by a human who has seen the texts, not a
        side effect of editing a registry entry.
        """
        claimed = [e.subject for e in all_recorded_evidence()
                   if e.validation_status is ValidationStatus.TRADITION_VALIDATED]
        self.assertEqual(
            claimed, [],
            "something now claims TRADITION_VALIDATED; confirm a human with "
            "the texts actually established it")
        self.assertEqual(registry_summary()["tradition_validated"], 0)

    def test_no_rule_claims_second_witness_without_two_works(self):
        for evidence in all_recorded_evidence():
            if not evidence.validation_status.at_least(
                    ValidationStatus.SECOND_WITNESS_CHECKED):
                continue
            works = {w.work for w in witnesses_for(evidence.subject)}
            with self.subTest(subject=evidence.subject):
                self.assertGreaterEqual(len(works), 2)

    def test_most_rules_are_honestly_unverified(self):
        """
        The audit's actual finding. Pinned so that a future change which
        quietly marks rules verified has to justify itself here.

        CHANGED IN V1.5. The V1.4 threshold was ">90 UNVERIFIED out of 110",
        which was right when nothing had been checked. V1.5 read Sanskrit
        witnesses for the whole corpus, and the count fell to 54 because 56
        rules moved to a status that reflects what was found — including 43
        that moved to IMPLEMENTATION_DIVERGES, which is emphatically not an
        improvement in the rules, only in what is known about them.

        The test now pins the thing worth protecting: the great majority of
        the corpus is still not in a state anyone should call validated. The
        bound is expressed against the statuses that assert real provenance
        rather than against UNVERIFIED alone, so that a future release cannot
        satisfy it by relabelling UNVERIFIED rules as diverging.
        """
        summary = registry_summary()
        by_status = summary["rules_by_status"]
        self.assertEqual(summary["rules_total"], len(all_rules()))

        attested = sum(
            count for status, count in by_status.items()
            if ValidationStatus(status).at_least(
                ValidationStatus.IMPLEMENTATION_MATCHED))
        self.assertLess(
            attested, 0.2 * summary["rules_total"],
            "fewer than a fifth of shipped rules reach IMPLEMENTATION_MATCHED "
            "or better; if that changes, it must change with evidence")
        self.assertEqual(
            by_status.get("TRADITION_VALIDATED", 0), 0,
            "nothing is tradition-validated, and nothing may become so "
            "without a human closing the review queue")

    def test_unverified_rules_say_why(self):
        """
        BROADENED IN V1.5. The V1.4 test required `interpretive_notes`, which
        was the only place a reason could live when the only reason available
        was "nobody has looked".

        V1.5 introduced a second kind of unverified rule: one where somebody
        DID look, read the cited chapter in a Sanskrit witness, and found the
        rule was not in it. That reason belongs in `textual_summary`, because
        it is a statement about the text. Both are accepted; a blank is still
        not.
        """
        for rule in all_rules():
            evidence = evidence_for(rule.id)
            if evidence.validation_status is not ValidationStatus.UNVERIFIED:
                continue
            with self.subTest(rule=rule.id):
                self.assertTrue(
                    evidence.interpretive_notes or evidence.textual_summary,
                    "an unverified rule must record why, so a blank is never "
                    "mistaken for a clean bill of health")
                self.assertTrue(evidence.needs_human_review)

    def test_negative_results_are_recorded_as_findings(self):
        """
        V1.5: "we read the cited chapter and the rule is not there" is
        evidence, and it must not be stored the same way as "we never
        looked". Each of these rules named a BPHS chapter that was read in
        full in V1.5 and does not contain it.
        """
        for rule_id in ("chandra_mangala", "budha_aditya",
                        "dhana_yoga_2_11_placement", "dhana_yoga_h1_h2_exchange",
                        "neecha_bhanga_surya"):
            with self.subTest(rule=rule_id):
                evidence = evidence_for(rule_id)
                self.assertIs(evidence.validation_status,
                              ValidationStatus.UNVERIFIED)
                self.assertIn("NEGATIVE RESULT", evidence.textual_summary)
                self.assertEqual(evidence.audited_in, "V1.5")
                self.assertFalse(
                    evidence.witness_ids,
                    "a negative result records no witness FOR the rule; the "
                    "chapter that was read is named in the summary")


# ── Part 5: rule provenance ──────────────────────────────────────────────────

class RuleProvenanceTest(unittest.TestCase):

    def test_every_rule_resolves_to_evidence(self):
        for rule in all_rules():
            with self.subTest(rule=rule.id):
                self.assertIsNotNone(rule.evidence())
                self.assertEqual(rule.evidence().subject, rule.id)

    def test_rule_exposes_text_and_software_separately(self):
        """
        Part 5: TEXT SAYS and SOFTWARE IMPLEMENTS must not be the same field.
        An English paraphrase must never quietly become the source.
        """
        for rule in all_rules():
            evidence = evidence_for(rule.id)
            if not evidence.textual_condition:
                continue
            with self.subTest(rule=rule.id):
                self.assertTrue(evidence.software_condition)
                self.assertNotEqual(evidence.textual_condition,
                                    evidence.software_condition)

    def test_located_rules_record_their_reference_frame(self):
        """Part 10: the frame a rule is judged from is part of the rule."""
        for evidence in all_recorded_evidence():
            if evidence.kind != "yoga":
                continue
            if evidence.validation_status is ValidationStatus.UNVERIFIED:
                continue
            with self.subTest(subject=evidence.subject):
                self.assertTrue(evidence.reference_frame)

    def test_results_carry_provenance(self):
        import datetime
        from engine.features import build_chart_features
        from engine.planets import JyotishChart, jde_from_datetime
        from engine.rules import evaluate_rules
        chart = JyotishChart(
            jde=jde_from_datetime(datetime.datetime(1988, 8, 30, 14, 48)),
            lat=26.9124, lon=75.7873)
        results = evaluate_rules(build_chart_features(chart))
        self.assertTrue(results)
        for result in results:
            with self.subTest(rule=result.id):
                self.assertEqual(result.rule_profile, "parashari")
                self.assertIn(result.validation_status,
                              {s.value for s in ValidationStatus})
                self.assertIsInstance(result.source_ref_ids, list)

    def test_result_dict_exposes_source_ref_ids(self):
        import datetime
        from engine.features import build_chart_features
        from engine.planets import JyotishChart, jde_from_datetime
        from engine.rules import evaluate_rules
        chart = JyotishChart(
            jde=jde_from_datetime(datetime.datetime(1988, 8, 30, 14, 48)),
            lat=26.9124, lon=75.7873)
        for result in evaluate_rules(build_chart_features(chart)):
            data = result.to_dict()
            with self.subTest(rule=result.id):
                for key in ("rule_id" if False else "id", "rule_profile",
                            "validation_status", "source_ref_ids"):
                    self.assertIn(key, data)

    def test_no_runtime_dump_of_long_translations(self):
        """
        Part 13: brief normalised summaries and precise locations, never
        running text. Guards against a copyrighted translation being pasted
        into the registry and then into every chart JSON.
        """
        for evidence in all_recorded_evidence():
            with self.subTest(subject=evidence.subject):
                self.assertLess(len(evidence.textual_condition), 400)
                self.assertLess(len(evidence.textual_summary), 600)
        for witness in ALL_WITNESSES:
            with self.subTest(witness=witness.id):
                self.assertLess(len(witness.incipit or ""), 200)


# ── Part 6: classification ───────────────────────────────────────────────────

class ClassificationTest(unittest.TestCase):

    def test_every_rule_is_classified(self):
        valid = {c for c in RuleClassification}
        for rule in all_rules():
            with self.subTest(rule=rule.id):
                self.assertIn(evidence_for(rule.id).classification, valid)

    def test_nothing_is_classified_source_validated_without_a_witness(self):
        for evidence in all_recorded_evidence():
            if evidence.classification is not \
                    RuleClassification.CLASSICAL_SOURCE_VALIDATED:
                continue
            with self.subTest(subject=evidence.subject):
                self.assertTrue(witnesses_for(evidence.subject))

    def test_unverified_rules_are_retained_not_deleted(self):
        """
        Part 6: classify, do not automatically delete. An untraced rule is not
        a wrong rule, and removing it would trade a known unknown for a
        silent gap.
        """
        unverified = [r.id for r in all_rules()
                      if evidence_for(r.id).validation_status
                      is ValidationStatus.UNVERIFIED]
        self.assertTrue(unverified)
        available = {r.id for r in rules_for_profile("parashari")}
        for rule_id in unverified:
            with self.subTest(rule=rule_id):
                self.assertIn(rule_id, available)


# ── Parts 7 and 11: conflicts ────────────────────────────────────────────────

class ConflictTest(unittest.TestCase):

    def test_conflict_ids_unique_and_resolvable(self):
        ids = [c.id for c in CONFLICTS]
        self.assertEqual(len(ids), len(set(ids)))
        for conflict_id in ids:
            with self.subTest(conflict=conflict_id):
                self.assertIsNotNone(conflict_by_id(conflict_id))

    def test_every_conflict_describes_the_difference(self):
        for conflict in CONFLICTS:
            with self.subTest(conflict=conflict.id):
                self.assertTrue(conflict.topic)
                self.assertTrue(conflict.difference)
                self.assertTrue(conflict.resolution_status)

    def test_conflicts_referenced_by_evidence_resolve(self):
        for evidence in all_recorded_evidence():
            for conflict_id in evidence.conflicts:
                with self.subTest(subject=evidence.subject):
                    self.assertIsNotNone(conflict_by_id(conflict_id))

    def test_bphs_edition_problem_is_registered(self):
        """Part 7: the engine must record that its BPHS citations name no edition."""
        self.assertIsNotNone(conflict_by_id("BPHS_EDITION_UNIDENTIFIED"))

    def test_conflicted_rules_cannot_enter_the_strict_profile(self):
        """Part 16, stated directly."""
        strict_ids = {r.id for r in rules_for_profile(EVIDENCE_GATED_PROFILE)}
        for evidence in all_recorded_evidence():
            if not evidence.conflicts:
                continue
            with self.subTest(subject=evidence.subject):
                self.assertNotIn(evidence.subject, strict_ids)


# ── Part 15: the evidence-gated profile ──────────────────────────────────────

class StrictProfileTest(unittest.TestCase):

    def test_strict_profile_exists_and_is_evidence_gated(self):
        self.assertIn(EVIDENCE_GATED_PROFILE, RULE_PROFILES)
        self.assertIn("EVIDENCE-GATED", RULE_PROFILES[EVIDENCE_GATED_PROFILE])

    def test_no_unqualified_rule_enters_strict_mode(self):
        """
        THE PART 15 TEST. Every member must independently satisfy the
        threshold; membership cannot be granted by editing the catalog.
        """
        for rule in rules_for_profile(EVIDENCE_GATED_PROFILE):
            evidence = evidence_for(rule.id)
            eligible, reasons = strict_profile_eligible(
                evidence, witnesses_for(rule.id))
            with self.subTest(rule=rule.id):
                self.assertTrue(
                    eligible,
                    f"{rule.id} is in the strict profile but fails: {reasons}")

    def test_strict_members_have_a_sanskrit_tier_witness(self):
        for rule in rules_for_profile(EVIDENCE_GATED_PROFILE):
            witnesses = witnesses_for(rule.id)
            with self.subTest(rule=rule.id):
                self.assertTrue(any(w.authority.is_sanskrit_tier
                                    for w in witnesses))

    def test_strict_members_meet_the_minimum_status(self):
        for rule in rules_for_profile(EVIDENCE_GATED_PROFILE):
            with self.subTest(rule=rule.id):
                self.assertTrue(
                    evidence_for(rule.id).validation_status
                    .at_least(STRICT_PROFILE_MINIMUM))

    def test_strict_members_have_text_software_and_a_test(self):
        for rule in rules_for_profile(EVIDENCE_GATED_PROFILE):
            evidence = evidence_for(rule.id)
            with self.subTest(rule=rule.id):
                self.assertTrue(evidence.textual_condition)
                self.assertTrue(evidence.software_condition)
                self.assertTrue(evidence.implementation_test)

    def test_strict_profile_is_a_subset_of_the_full_catalog(self):
        """
        CHANGED IN V1.5. The strict profile used to draw only from the
        mainstream and variant catalogs. It now also draws from the V1.5
        textual catalog, which is where the best-evidenced rules live — they
        were written FROM located witnesses rather than checked against them.
        The invariant that matters is unchanged: strict invents nothing, and
        every rule in it exists in a catalog a user can also run directly.
        """
        full = ({r.id for r in rules_for_profile("parashari_extended")}
                | {r.id for r in rules_for_profile("parashari_textual")})
        for rule in rules_for_profile(EVIDENCE_GATED_PROFILE):
            with self.subTest(rule=rule.id):
                self.assertIn(rule.id, full)

    def test_strict_profile_grew_only_by_evidence(self):
        """
        CHANGED IN V1.5, and this is the release's clearest single number.

        V1.4 asserted `len(strict) < 10`, and the profile held exactly one
        rule. That was the correct finding at the time and it was a finding
        about the SEARCH, not about the tradition: one Sanskrit witness had
        been obtained, so one rule could clear the gate.

        V1.5 obtained three more Sanskrit works and the profile holds 41. Not
        one line of the gate changed to allow this — `strict_profile_eligible`
        is untouched — so the growth is entirely the arrival of evidence.

        The bound is kept, raised, and kept tight: strict must remain a small
        minority of the catalog, because most of the catalog still has no
        witness.
        """
        strict = rules_for_profile(EVIDENCE_GATED_PROFILE)
        self.assertGreater(
            len(strict), 1,
            "V1.4 shipped one strict rule; V1.5's witnesses should admit more")
        self.assertLess(
            len(strict), 0.5 * len(rules_for_profile("parashari_textual")),
            "strict must stay a minority of the catalog")
        self.assertGreater(len(all_rules()), 100)

    def test_strict_profile_excludes_rules_whose_witnesses_disagree(self):
        """
        Good sourcing is not settled sourcing.

        Several V1.5 textual rules rest on a witness read carefully and are
        still kept out, because a SECOND witness states the formation
        condition differently. Admitting them would mean picking a reading
        and calling the result strict, which hides exactly what the profile
        exists to expose.
        """
        members = {r.id for r in rules_for_profile(EVIDENCE_GATED_PROFILE)}
        for rule_id in ("lakshmi_yoga_bphs", "lakshmi_yoga_phaladeepika",
                        "gajakesari_textual_bphs", "mahapurusha_hamsa_textual",
                        "kemadruma_textual"):
            with self.subTest(rule=rule_id):
                evidence = evidence_for(rule_id)
                self.assertTrue(
                    evidence.witness_ids,
                    "this rule was written from a located witness")
                self.assertTrue(
                    evidence.conflicts,
                    "and a second witness disagrees about it")
                self.assertNotIn(rule_id, members)

    def test_rejections_are_explained(self):
        rejections = strict_profile_rejections()
        self.assertTrue(rejections)
        for rule_id, reasons in rejections.items():
            with self.subTest(rule=rule_id):
                self.assertTrue(reasons)

    def test_admission_helper_agrees_with_membership(self):
        members = {r.id for r in rules_for_profile(EVIDENCE_GATED_PROFILE)}
        for rule in all_rules():
            with self.subTest(rule=rule.id):
                self.assertEqual(strict_profile_admits(rule.id),
                                 rule.id in members)

    def test_old_vipareeta_profile_was_renamed_not_deleted(self):
        """The V1.2 meaning of 'strict' survives under a name that fits it."""
        self.assertIn("parashari_vipareeta_strict", RULE_PROFILES)
        ids = {r.id for r in rules_for_profile("parashari_vipareeta_strict")}
        self.assertIn("vipareeta_harsha_strict", ids)


# ── Part 8: Varga source evidence ────────────────────────────────────────────

class VargaSourceTest(unittest.TestCase):

    def test_every_convention_has_evidence(self):
        for subject in varga_subjects():
            with self.subTest(subject=subject):
                self.assertIsNotNone(evidence_for(subject, kind="varga"))

    def test_every_convention_is_audited_in_metadata(self):
        for chart in VARGA_ORDER:
            for convention in VARGA_SPECS[chart].conventions:
                with self.subTest(chart=chart, convention=convention):
                    data = metadata_for(chart, convention).to_dict()
                    for key in ("source_validation_status",
                                "source_classification", "source_ref_ids",
                                "algorithm_version"):
                        self.assertIn(key, data)

    def test_charts_named_in_the_brief_are_all_audited(self):
        for chart in ("D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
                      "D20", "D24", "D27", "D30", "D40", "D45", "D60"):
            with self.subTest(chart=chart):
                self.assertIn(chart, VARGA_ORDER)
                subjects = [s for s in varga_subjects()
                            if s.startswith(chart + "/")]
                self.assertTrue(subjects)

    def test_validated_conventions_carry_a_witness(self):
        """Part 16: every validated Varga convention has source evidence."""
        for subject in varga_subjects():
            evidence = evidence_for(subject, kind="varga")
            if evidence.validation_status is ValidationStatus.UNVERIFIED:
                continue
            with self.subTest(subject=subject):
                self.assertTrue(witnesses_for(subject))
                self.assertTrue(evidence.textual_condition)

    def test_d9_is_the_one_with_a_located_witness(self):
        """
        The only Varga rule in this engine with a Sanskrit witness: BJ 1.6
        names the four starting rashis directly.
        """
        evidence = evidence_for("D9/standard", kind="varga")
        self.assertTrue(evidence.validation_status.at_least(
            ValidationStatus.IMPLEMENTATION_MATCHED))
        self.assertTrue(witnesses_for("D9/standard"))

    def test_d30_stops_short_because_the_degrees_are_unconfirmed(self):
        """
        The lord order is attested; the 5/5/8/7/5 division is not readable
        from the witness. The status stops accordingly instead of rounding up.
        """
        evidence = evidence_for("D30/parashari", kind="varga")
        self.assertEqual(evidence.validation_status,
                         ValidationStatus.RULE_INTERPRETATION_MAPPED)
        self.assertTrue(evidence.ambiguities)
        self.assertTrue(evidence.needs_human_review)

    def test_no_convention_claims_source_validation_without_one(self):
        for meta in all_metadata():
            if meta["source_classification"] != \
                    RuleClassification.CLASSICAL_SOURCE_VALIDATED.value:
                continue
            with self.subTest(chart=meta["chart"],
                              convention=meta["convention_id"]):
                self.assertTrue(meta["source_ref_ids"])


# ── Part 9: aliases ──────────────────────────────────────────────────────────

class AliasTest(unittest.TestCase):

    EXPECTED_ALIASES = {("D7", "parivritti"), ("D16", "parivritti"),
                        ("D20", "parivritti"), ("D27", "parivritti")}

    def test_identical_conventions_are_declared_as_aliases(self):
        flagged = {(m["chart"], m["convention_id"]) for m in all_metadata()
                   if m.get("is_deprecated_alias")}
        self.assertEqual(flagged, self.EXPECTED_ALIASES)

    def test_declared_aliases_really_are_identical(self):
        """Part 16: assert alias equivalence where it is intentional."""
        from engine.vargas import VargaConfig
        default = VargaConfig()
        for chart, convention in self.EXPECTED_ALIASES:
            other = VargaConfig(conventions={chart: convention})
            with self.subTest(chart=chart, convention=convention):
                for index in range(0, 36000, 7):
                    longitude = index * 0.01
                    self.assertEqual(
                        default.compute(chart, longitude).rashi_index,
                        other.compute(chart, longitude).rashi_index)

    def test_no_undeclared_alias_exists(self):
        """A new mathematical duplicate must be declared, not discovered."""
        from engine.vargas import VargaConfig
        default = VargaConfig()
        found = set()
        for chart in VARGA_ORDER:
            for convention in VARGA_SPECS[chart].conventions:
                if convention == default.conventions[chart]:
                    continue
                other = VargaConfig(conventions={chart: convention})
                identical = all(
                    default.compute(chart, i * 0.01).rashi_index
                    == other.compute(chart, i * 0.01).rashi_index
                    for i in range(0, 36000, 7))
                if identical:
                    found.add((chart, convention))
        self.assertEqual(found, self.EXPECTED_ALIASES)

    def test_aliases_explain_why_they_are_identical(self):
        for meta in all_metadata():
            if not meta.get("is_deprecated_alias"):
                continue
            with self.subTest(chart=meta["chart"]):
                self.assertTrue(meta.get("identical_to"))
                self.assertIn("congruent", meta.get("notes", ""))


# ── Part 17: human review queue ──────────────────────────────────────────────

class ReviewQueueTest(unittest.TestCase):

    def test_queue_is_populated(self):
        self.assertTrue(REVIEW_QUEUE)

    def test_every_item_is_actionable(self):
        for item in REVIEW_QUEUE:
            with self.subTest(subject=item.subject):
                self.assertTrue(item.subject)
                self.assertTrue(item.question)
                self.assertTrue(item.current_behaviour)
                self.assertTrue(item.question.strip().endswith("?"))

    def test_reasons_are_from_the_declared_vocabulary(self):
        from engine.sources import ReviewReason
        for item in REVIEW_QUEUE:
            with self.subTest(subject=item.subject):
                self.assertIsInstance(item.reason, ReviewReason)

    def test_ambiguous_rules_are_flagged_for_review(self):
        for evidence in all_recorded_evidence():
            if not evidence.ambiguities:
                continue
            with self.subTest(subject=evidence.subject):
                self.assertTrue(evidence.needs_human_review)

    def test_the_bphs_gap_is_queued(self):
        subjects = " ".join(item.subject for item in REVIEW_QUEUE)
        self.assertIn("BPHS", subjects)


# ── Part 14: snapshot provenance ─────────────────────────────────────────────

class SnapshotProvenanceTest(unittest.TestCase):

    def snapshot(self, rule_profile="parashari"):
        import datetime
        from engine.features import build_chart_features
        from engine.planets import JyotishChart, jde_from_datetime
        from engine.rules import evaluate_rules
        from engine.snapshot import build_snapshot
        chart = JyotishChart(
            jde=jde_from_datetime(datetime.datetime(1988, 8, 30, 14, 48)),
            lat=26.9124, lon=75.7873)
        features = build_chart_features(chart)
        return build_snapshot(
            chart, features=features,
            yoga_results=evaluate_rules(features, rule_profile),
            rule_profile=rule_profile).to_dict()

    def test_methodology_section_exists(self):
        methodology = self.snapshot()["methodology"]
        for key in ("varga_profile", "rule_profile",
                    "source_registry_version"):
            with self.subTest(key=key):
                self.assertIn(key, methodology)

    def test_methodology_reports_the_active_profile(self):
        for profile in ("parashari", "parashari_extended"):
            with self.subTest(profile=profile):
                data = self.snapshot(profile)
                self.assertEqual(data["methodology"]["rule_profile"], profile)

    def test_snapshot_carries_the_four_claim_separation(self):
        claims = self.snapshot()["methodology"]["claim_separation"]
        for key in ("computationally_tested", "externally_benchmarked",
                    "textual_source_located", "tradition_source_validated"):
            with self.subTest(claim=key):
                self.assertIn(key, claims)

    def test_snapshot_reports_zero_tradition_validated(self):
        summary = self.snapshot()["methodology"]["provenance_summary"]
        self.assertEqual(summary["tradition_validated"], 0)

    def test_yoga_results_carry_source_ref_ids(self):
        for yoga in self.snapshot()["yogas"]:
            with self.subTest(rule=yoga["id"]):
                self.assertIn("validation_status", yoga)
                self.assertIn("source_ref_ids", yoga)
                self.assertIn("rule_profile", yoga)

    def test_snapshot_does_not_embed_the_source_corpus(self):
        """
        Part 14: source IDs, not the corpus. A chart snapshot must not carry
        editions, locators and incipits for every rule.
        """
        import json
        blob = json.dumps(self.snapshot())
        self.assertNotIn("Oriental Books Reprint", blob)
        self.assertNotIn("gretil", blob.lower())

    def test_schema_version_was_raised_for_the_addition(self):
        from engine.snapshot import SCHEMA_VERSION
        major, minor, _patch = SCHEMA_VERSION.split(".")
        self.assertEqual(major, "1")
        self.assertGreaterEqual(int(minor), 1,
                                "adding methodology is a minor bump")

    def test_addition_is_backward_compatible(self):
        """Nothing a 1.0.0 reader depended on was removed or redefined."""
        data = self.snapshot()
        for section in ("schema_version", "birth", "calculation_settings",
                        "accuracy", "lagna", "planets", "houses", "vargas",
                        "features", "yogas", "timing"):
            with self.subTest(section=section):
                self.assertIn(section, data)


# ── Part 12: strength stays separate from existence ──────────────────────────

class StrengthSeparationTest(unittest.TestCase):
    """Source validation must not have leaked into the scoring order."""

    def results(self):
        import datetime
        from engine.features import build_chart_features
        from engine.planets import JyotishChart, jde_from_datetime
        from engine.rules import evaluate_rules
        chart = JyotishChart(
            jde=jde_from_datetime(datetime.datetime(1988, 8, 30, 14, 48)),
            lat=26.9124, lon=75.7873)
        return evaluate_rules(build_chart_features(chart))

    def test_validation_status_does_not_affect_presence(self):
        """
        A rule's provenance says nothing about whether the combination is in
        the chart. An UNVERIFIED rule still forms or does not form on the
        chart's own terms.
        """
        present = [r for r in self.results() if r.present]
        self.assertTrue(present)
        statuses = {r.validation_status for r in present}
        self.assertIn(ValidationStatus.UNVERIFIED.value, statuses,
                      "unverified rules must still be evaluated normally")

    def test_score_remains_a_software_heuristic(self):
        for result in self.results():
            if result.engine_strength_score is None:
                continue
            with self.subTest(rule=result.id):
                self.assertEqual(result.score_type, "software_heuristic")
                self.assertFalse(result.classical_measure)

    def test_presence_is_never_a_percentage(self):
        """Part 12: no '78% yoga present'. Presence is categorical."""
        for result in self.results():
            with self.subTest(rule=result.id):
                self.assertIsInstance(result.present, bool)


class CalculationProvenanceTest(unittest.TestCase):
    """
    V1.4 Part 23: provenance work continues alongside the calculations, and
    every newly implemented formula has better source discipline than the
    original V1 yoga catalog.
    """

    def calculations(self):
        return [e for e in all_recorded_evidence() if e.kind == "calculation"]

    def test_new_modules_are_registered(self):
        subjects = {e.subject for e in self.calculations()}
        for expected in ("shadbala/sthana_bala", "shadbala/dig_bala",
                         "shadbala/kala_bala", "shadbala/naisargika_bala",
                         "shadbala/drik_bala", "ashtakavarga/bhinna",
                         "houses/sripati"):
            with self.subTest(module=expected):
                self.assertIn(expected, subjects)

    def test_no_module_ships_a_fabricated_citation(self):
        """
        Part 23: if a source is absent, the module must say UNVERIFIED rather
        than name a text it has not seen.
        """
        for evidence in self.calculations():
            with self.subTest(module=evidence.subject):
                if evidence.witness_ids:
                    for witness_id in evidence.witness_ids:
                        self.assertIsNotNone(witness_by_id(witness_id))
                else:
                    self.assertEqual(evidence.validation_status,
                                     ValidationStatus.UNVERIFIED)

    def test_source_discipline_beats_the_v1_yoga_catalog(self):
        """
        The measurable claim: modules implemented after obtaining a witness
        have a far better located ratio than rules written from memory.
        """
        calculations = self.calculations()
        located = [e for e in calculations
                   if e.validation_status is not ValidationStatus.UNVERIFIED]
        calculation_ratio = len(located) / len(calculations)

        rules = all_rules()
        rules_matched = [
            r for r in rules
            if evidence_for(r.id).validation_status.at_least(
                ValidationStatus.IMPLEMENTATION_MATCHED)]
        rule_ratio = len(rules_matched) / len(rules)

        # CHANGED IN V1.5. The V1.4 comparison counted any status above
        # UNVERIFIED as "located", which stopped discriminating once the audit
        # ran: 43 rules acquired a located witness and a documented MISMATCH
        # with it, and counting those as a win for the memory-first approach
        # would invert the finding. The comparison is now against rules whose
        # implementation actually matches their witness, which is what the
        # calculation modules achieved by reading the source first.
        self.assertGreater(calculation_ratio, rule_ratio * 5)

    def test_modules_separate_text_from_implementation(self):
        for evidence in self.calculations():
            if not evidence.textual_condition:
                continue
            with self.subTest(module=evidence.subject):
                self.assertTrue(evidence.software_condition)
                self.assertNotEqual(evidence.textual_condition,
                                    evidence.software_condition)

    def test_every_module_names_a_test(self):
        for evidence in self.calculations():
            with self.subTest(module=evidence.subject):
                self.assertTrue(evidence.implementation_test)

    def test_unverified_modules_explain_themselves(self):
        for evidence in self.calculations():
            if evidence.validation_status is not ValidationStatus.UNVERIFIED:
                continue
            with self.subTest(module=evidence.subject):
                self.assertTrue(evidence.interpretive_notes)
                self.assertTrue(evidence.needs_human_review)

    def test_no_calculation_claims_tradition_validated(self):
        """The BPHS witness is a TRANSLATION; Sanskrit tier is unreachable."""
        for evidence in self.calculations():
            with self.subTest(module=evidence.subject):
                self.assertNotEqual(evidence.validation_status,
                                    ValidationStatus.TRADITION_VALIDATED)

    def test_summary_reports_calculation_counts(self):
        summary = registry_summary()
        self.assertIn("calculation_modules_total", summary)
        self.assertIn("calculations_by_status", summary)
        self.assertEqual(summary["calculation_modules_total"],
                         len(self.calculations()))


class RegistrySummaryTest(unittest.TestCase):

    def test_summary_fields(self):
        summary = registry_summary()
        for key in ("registry_version", "witnesses_registered", "rules_total",
                    "rules_by_status", "varga_conventions_total",
                    "vargas_by_status", "conflicts", "open_review_items",
                    "tradition_validated"):
            with self.subTest(key=key):
                self.assertIn(key, summary)
        self.assertEqual(summary["registry_version"], REGISTRY_VERSION)

    def test_counts_are_consistent_with_the_catalog(self):
        summary = registry_summary()
        self.assertEqual(summary["rules_total"], len(all_rules()))
        self.assertEqual(sum(summary["rules_by_status"].values()),
                         len(all_rules()))
        self.assertEqual(sum(summary["vargas_by_status"].values()),
                         len(varga_subjects()))

    def test_report_generates(self):
        from engine.sources.report import build_report
        report = build_report()
        self.assertIn("TRADITION/SOURCE VALIDATED", report)
        self.assertIn("UNVERIFIED", report)
        self.assertIn("Bṛhajjātaka", report)
        self.assertGreater(len(report), 5000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
