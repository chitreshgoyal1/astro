"""
Deterministic interpretation (V1.6 Parts 10, 11, 13-19, 21-29, 34)
---------------------------------------------------------------------
Tests for the layer that produces prose.

THE TWO THAT MATTER MOST

    `DeterminismTest` — Part 28 asks for byte-identical output from
    identical input. It is the property that makes every other claim in this
    package checkable, and it is the one an LLM could not satisfy.

    `NoAstrologyInRendererTest` — Part 10 forbids the renderer from deciding
    anything. Tested by construction: the renderer's only input is a
    serialised dict, so it is never shown anything it could decide from, and
    the test asserts the package imports nothing that would let it.
"""

import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.interpretation import (
    ALL_KEYS, DomainSection, InterpretationDocument, MissingTemplateArgument,
    MissingTemplateKey, ReportMode, TemplateSet, UnsupportedLocale,
    available_languages, build_interpretation, completeness_report,
    evidence_key, format_interpretation, interpretation_hash, join,
    load_templates, ordinal, sentence, template_arguments, titlecase_domain,
)
from engine.interpretation import keys as K
from engine.interpretation.renderer import TEMPLATE_ROOT

FIXED_TIME = datetime.datetime(2026, 1, 1, 0, 0, 0)

BIRTH = {"name": "Test Native", "date": "1988-08-30", "time": "20:18",
         "place": "Jaipur"}


def build_prediction(profile="standard", moment=None):
    """A real PredictionSnapshot for the regression chart."""
    from engine.ashtakavarga import compute_ashtakavarga
    from engine.features import build_chart_features, parashari_profile
    from engine.planets import JyotishChart, jde_from_datetime
    from engine.rules import evaluate_rules
    from engine.strength import compute_shadbala
    from engine.synthesis import (
        SynthesisProfile, build_prediction_snapshot, event_candidates,
        synthesise,
    )
    from engine.timing.vimshottari import from_chart as dasha_from_chart
    from engine.transits.calculator import get_transit_snapshot

    birth = datetime.datetime(1988, 8, 30, 14, 48)
    moment = moment or datetime.datetime(2026, 9, 27, 12, 0)
    chart = JyotishChart(jde=jde_from_datetime(birth),
                         lat=26.9124, lon=75.7873)
    features = build_chart_features(
        chart, aspect_profile=parashari_profile("none"))
    features.shadbala = compute_shadbala(chart, features, birth=birth)
    yogas = evaluate_rules(features, "parashari")
    dasha = dasha_from_chart(chart, birth, depth=3)
    av = compute_ashtakavarga(chart)
    transits = get_transit_snapshot(moment, natal_chart=chart)
    context = synthesise(
        features, moment=moment, yoga_results=yogas, dasha=dasha,
        transit_snapshot=transits, ashtakavarga=av,
        profile=SynthesisProfile(profile))
    candidates = event_candidates(context, dasha=dasha)
    snapshot = build_prediction_snapshot(
        context, transit_snapshot=transits, candidates=candidates)
    return snapshot.to_dict(), features


class _Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.prediction, cls.features = build_prediction()

    def render(self, mode=ReportMode.DETAILED, **kwargs):
        return build_interpretation(
            self.prediction, mode=mode, features=self.features, birth=BIRTH,
            generated=FIXED_TIME, **kwargs)


# ── Part 29: template completeness ───────────────────────────────────────────

class TemplateCompletenessTest(unittest.TestCase):

    def test_english_defines_every_key_the_engine_can_emit(self):
        report = completeness_report("en")
        self.assertTrue(
            report["complete"],
            f"missing template keys: {report['missing']}")

    def test_every_shipped_locale_is_complete(self):
        languages = available_languages()
        self.assertIn("en", languages)
        for language in languages:
            with self.subTest(language=language):
                self.assertTrue(completeness_report(language)["complete"])

    def test_missing_key_raises_rather_than_falling_back(self):
        """
        Part 29: no silent fallback. A bland sentence where a specific
        finding should have been is worse than a crash, because the reader
        cannot tell anything was lost.
        """
        templates = load_templates("en")
        with self.assertRaises(MissingTemplateKey):
            templates.render("domain.activation.NOT_A_LEVEL")

    def test_missing_argument_raises(self):
        templates = load_templates("en")
        with self.assertRaises(MissingTemplateArgument):
            templates.render("evidence.benefic_occupies_house")

    def test_unknown_locale_raises(self):
        with self.assertRaises(UnsupportedLocale):
            TemplateSet("kl", root=TEMPLATE_ROOT)

    def test_unknown_activation_level_raises(self):
        with self.assertRaises(KeyError):
            K.activation_key("VERY_ACTIVE")

    def test_unknown_evidence_type_raises(self):
        with self.assertRaises(KeyError):
            evidence_key("something_the_engine_never_emits")

    def test_every_template_argument_is_supplied_somewhere(self):
        """
        A template asking for an argument no renderer provides is a latent
        crash that only fires on the chart that happens to reach it.
        """
        templates = load_templates("en")
        known = {
            "date", "name", "birth_date", "birth_time", "place", "profile",
            "house", "dignity", "sign", "occupied_house", "planet", "state",
            "ratio", "bindus", "reference", "yoga", "status", "level",
            "houses", "target", "start", "end", "peak", "event_type",
            "activation", "mahadasha", "antardasha", "pratyantardasha",
            "seconds", "chart", "count", "qualified", "total", "citation",
            "authority", "rule_id", "validation_status", "eligibility",
            "list_two", "list_last", "list_separator", "months",
            # V1.8: the schema-mismatch warning. It existed since V1.6 as a
            # hard-coded English sentence, so it had no arguments for this
            # test to check; making it a key gave it two.
            "found", "expected",
        }
        for key in ALL_KEYS:
            template = templates.template(key)
            for argument in template_arguments(template):
                with self.subTest(key=key, argument=argument):
                    self.assertIn(argument, known)


# ── Part 28: determinism ─────────────────────────────────────────────────────

class DeterminismTest(_Base):

    def test_two_renders_are_byte_identical(self):
        first = self.render()
        second = self.render()
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(format_interpretation(first),
                         format_interpretation(second))

    def test_hash_is_stable_across_runs(self):
        self.assertEqual(interpretation_hash(self.render()),
                         interpretation_hash(self.render()))

    def test_hash_ignores_only_the_timestamp(self):
        early = self.render()
        late = build_interpretation(
            self.prediction, mode=ReportMode.DETAILED,
            features=self.features, birth=BIRTH,
            generated=datetime.datetime(2030, 6, 1))
        self.assertEqual(interpretation_hash(early),
                         interpretation_hash(late))
        self.assertNotEqual(early.generated, late.generated)

    def test_different_input_gives_a_different_hash(self):
        summary = self.render(ReportMode.SUMMARY)
        detailed = self.render(ReportMode.DETAILED)
        self.assertNotEqual(interpretation_hash(summary),
                            interpretation_hash(detailed))

    def test_no_randomness_or_model_in_the_package(self):
        """Part 35: fully offline, no generative component."""
        import pathlib
        package = (pathlib.Path(__file__).resolve().parent.parent
                   / "engine" / "interpretation")
        for path in sorted(package.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            with self.subTest(module=path.name):
                for banned in ("import random", "openai", "anthropic",
                               "transformers", "requests", "urllib.request",
                               "socket", "httpx"):
                    self.assertNotIn(banned, source)


# ── Part 10: the renderer decides nothing ────────────────────────────────────

class NoAstrologyInRendererTest(unittest.TestCase):

    def test_package_imports_no_astrology_module(self):
        """
        Tested by construction. The renderer's input is a serialised dict,
        so it is never shown a chart it could draw a conclusion from.
        """
        import pathlib
        package = (pathlib.Path(__file__).resolve().parent.parent
                   / "engine" / "interpretation")
        forbidden = ("engine.ephemeris", "engine.planets", "engine.vargas",
                     "engine.rules", "engine.strength", "engine.ashtakavarga",
                     "engine.transits", "engine.timing")
        for path in sorted(package.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            with self.subTest(module=path.name):
                for module in forbidden:
                    self.assertNotIn(f"import {module}", source)
                    self.assertNotIn(f"from {module}", source)

    def test_renders_from_a_stored_snapshot_with_no_engine_objects(self):
        """
        The strongest form of the guarantee: round-trip the snapshot through
        JSON so nothing but plain data remains, then render.
        """
        prediction, _features = build_prediction()
        round_tripped = json.loads(json.dumps(prediction, default=str))
        document = build_interpretation(
            round_tripped, mode=ReportMode.DETAILED, generated=FIXED_TIME)
        self.assertTrue(document.domain_sections)
        self.assertTrue(format_interpretation(document))


# ── Parts 25: the three modes ────────────────────────────────────────────────

class ReportModeTest(_Base):

    def test_all_three_modes_render(self):
        for mode in ReportMode:
            with self.subTest(mode=mode.value):
                document = self.render(mode)
                self.assertTrue(format_interpretation(document))

    def test_modes_agree_on_every_activation_level(self):
        """
        Part 25: the modes differ in how much they show, never in what they
        claim. A summary that rounded a finding would be a different
        document, not a shorter one.
        """
        detailed = self.render(ReportMode.DETAILED)
        technical = self.render(ReportMode.TECHNICAL)
        for section in detailed.domain_sections:
            other = technical.section_for(section.domain)
            with self.subTest(domain=section.domain):
                self.assertIsNotNone(other)
                self.assertEqual(section.activation, other.activation)
                self.assertEqual(section.confidence, other.confidence)

    def test_summary_hides_evidence_and_drops_silent_domains(self):
        summary = self.render(ReportMode.SUMMARY)
        detailed = self.render(ReportMode.DETAILED)
        for section in summary.domain_sections:
            with self.subTest(domain=section.domain):
                self.assertEqual(section.supporting, [])
                self.assertFalse(section.is_silent)
        self.assertLessEqual(len(summary.domain_sections),
                             len(detailed.domain_sections))

    def test_summary_does_not_promise_lists_it_will_not_print(self):
        """
        A small correctness point with a general shape: the contradiction
        sentence in detailed mode says "both are listed below", and summary
        mode prints no lists, so it uses a different sentence.
        """
        summary = self.render(ReportMode.SUMMARY)
        for section in summary.domain_sections:
            if section.contradiction is None:
                continue
            with self.subTest(domain=section.domain):
                self.assertNotIn("below", section.contradiction.text)

    def test_only_technical_carries_provenance(self):
        """Part 15: sources available, not intrusive."""
        detailed = self.render(ReportMode.DETAILED).to_dict()
        technical = self.render(ReportMode.TECHNICAL).to_dict()
        self.assertNotIn("technical_appendix", detailed)
        self.assertIn("technical_appendix", technical)
        first_detailed = detailed["domain_sections"][0]
        self.assertNotIn("rule_ids", first_detailed)

    def test_no_verse_numbers_in_normal_prose(self):
        """
        Part 15 again. Verse locators belong in the appendix and the JSON,
        not in a sentence a lay reader is trying to follow.
        """
        text = format_interpretation(self.render(ReportMode.SUMMARY))
        for marker in ("BPHS_SA_", "11.2-13", "32.22-24", "witness"):
            self.assertNotIn(marker, text)

    def test_technical_appendix_carries_citations_not_passages(self):
        """Part 33: no long source text is reproduced."""
        document = self.render(ReportMode.TECHNICAL)
        appendix = document.technical_appendix
        self.assertTrue(appendix["sources"])
        for source in appendix["sources"]:
            with self.subTest(source=source["id"]):
                self.assertNotIn("incipit", source)
                self.assertLess(len(json.dumps(source)), 500)


# ── Parts 16, 21, 22: what the prose may and may not say ─────────────────────

class ProseSafetyTest(_Base):

    def test_contradictions_render_both_sides(self):
        """Part 16: never collapse mixed evidence into one direction."""
        document = self.render(ReportMode.DETAILED)
        mixed = [s for s in document.domain_sections
                 if s.supporting and s.challenging]
        self.assertTrue(mixed)
        for section in mixed:
            with self.subTest(domain=section.domain):
                self.assertIsNotNone(section.contradiction)
                self.assertIn("both directions",
                              section.contradiction.text.lower()
                              .replace("obstacles or delay",
                                       "both directions"))

    def test_no_false_specificity(self):
        """
        Part 21: a CAREER_CHANGE candidate does not become a promotion, and
        a RELATIONSHIP_ACTIVATION does not become a wedding.
        """
        text = format_interpretation(self.render(ReportMode.DETAILED)).lower()
        for phrase in ("you will", "promotion", "you'll", "guaranteed",
                       "certainly", "definitely", "is going to"):
            self.assertNotIn(phrase, text)

    def _claim_phrases(self, document):
        """
        Every sentence that ASSERTS something, excluding the disclaimers.

        Scanning the whole document for "diagnosis" fails on the safety
        sentence that promises there is no diagnosis — the same trap that
        caught V1.4 with the word "score" and V1.5 with "probability". The
        disclaimers have to use the forbidden words in order to disclaim
        them, so the scan has to know which sentences are disclaimers.
        """
        disclaimer_keys = {"safety.health_scope", "safety.longevity_scope",
                           "document.disclaimer",
                           "methodology.not_validated"}
        phrases = []
        for section in document.domain_sections:
            for group in (section.natal_foundation, section.supporting,
                          section.challenging, section.dasha,
                          section.transits, section.timing,
                          section.reliability):
                phrases.extend(group)
            for single in (section.overall, section.confidence_phrase,
                           section.contradiction, section.silence):
                if single is not None:
                    phrases.append(single)
        return [p for p in phrases if p.key not in disclaimer_keys]

    def test_no_medical_or_mortality_language(self):
        """
        Part 22, checked against the sentences that make claims.

        The scope disclaimers are excluded because they exist precisely to
        say the document contains no diagnosis, and a scan that failed on
        them would push a future author to weaken the disclaimer rather
        than the claim.
        """
        for phrase in self._claim_phrases(self.render(ReportMode.DETAILED)):
            text = phrase.text.lower()
            with self.subTest(key=phrase.key):
                for banned in ("diagnos", "disease", "illness", "death",
                               "lifespan", "pregnan", "cure", "terminal"):
                    self.assertNotIn(banned, text)

    def test_the_disclaimers_do_mention_what_they_exclude(self):
        """
        The other half: a scope limit that never names what it excludes is
        not a scope limit. HEALTH must say it is not medical, and LONGEVITY
        must say it makes no statement about lifespan.
        """
        document = self.render(ReportMode.DETAILED)
        health = document.section_for("HEALTH")
        self.assertIn("medical", health.safety.text.lower())
        longevity = document.section_for("LONGEVITY")
        self.assertIn("lifespan", longevity.safety.text.lower())

    def test_health_and_longevity_carry_their_scope_limit(self):
        document = self.render(ReportMode.DETAILED)
        for domain in ("HEALTH", "LONGEVITY"):
            section = document.section_for(domain)
            with self.subTest(domain=domain):
                self.assertIsNotNone(section)
                self.assertIsNotNone(section.safety)
                self.assertTrue(section.safety.text)

    def test_no_probability_language(self):
        """Part 18: confidence is not probability."""
        text = format_interpretation(self.render(ReportMode.DETAILED)).lower()
        for phrase in ("% chance", "percent", "probability", "likelihood",
                       "odds of"):
            self.assertNotIn(phrase, text)

    def test_document_declares_what_it_is_not(self):
        data = self.render().to_dict()
        blob = " ".join(data["not_included"]).lower()
        for item in ("medical", "death", "probabilit", "remed"):
            self.assertIn(item, blob)
        self.assertIn("interpretation_is_not_validation", data["claims"])


# ── Parts 17, 19: timing and reliability language ────────────────────────────

class TimingLanguageTest(_Base):

    def test_no_peak_is_invented(self):
        """
        Part 17: never assert a peak the engine did not identify.

        Checked on the ARGUMENTS rather than the words. The no-peak
        template legitimately contains "strongest" — it says no strongest
        point was identified — so a word scan would fail on the sentence
        that does the right thing. What must be true is that the phrase was
        given no peak value to print.
        """
        document = self.render(ReportMode.DETAILED)
        for section in document.domain_sections:
            for phrase in section.timing:
                if phrase.key != "timing.window_without_peak":
                    continue
                with self.subTest(domain=section.domain):
                    self.assertNotIn("peak", phrase.args)

    def test_peak_phrase_only_used_when_a_peak_exists(self):
        document = self.render(ReportMode.DETAILED)
        candidates = {c["domain"]: c for c in
                      self.prediction["event_candidates"]}
        for section in document.domain_sections:
            peaks = [p for p in section.timing
                     if p.key == "timing.window_with_peak"]
            if not peaks:
                continue
            with self.subTest(domain=section.domain):
                self.assertIsNotNone(
                    candidates[section.domain]["window"]["window_peak"])

    def test_dates_are_rendered_month_and_year(self):
        document = self.render(ReportMode.DETAILED)
        for section in document.domain_sections:
            for phrase in section.timing:
                if "start" not in phrase.args:
                    continue
                with self.subTest(domain=section.domain):
                    # "September 2026", never "2026-09-27T12:00:00".
                    self.assertNotIn("T", phrase.args["start"])
                    self.assertNotIn("-", phrase.args["start"])

    def test_birth_time_precision_is_stated(self):
        document = self.render(ReportMode.DETAILED)
        keys = {p.key for p in document.reliability_warnings}
        self.assertIn("reliability.birth_time_precision", keys)


# ── Part 31: silence ─────────────────────────────────────────────────────────

class DomainSilenceTest(unittest.TestCase):

    def test_strict_renders_silence_rather_than_generic_astrology(self):
        prediction, features = build_prediction(profile="strict")
        document = build_interpretation(
            prediction, mode=ReportMode.DETAILED, features=features,
            generated=FIXED_TIME)
        silent = [s for s in document.domain_sections if s.is_silent]
        self.assertTrue(
            silent,
            "strict should decline at least one domain on this chart")
        for section in silent:
            with self.subTest(domain=section.domain):
                self.assertIsNotNone(section.silence)
                self.assertEqual(section.supporting, [])
                self.assertEqual(section.timing, [])

    def test_relationships_is_declined_under_strict(self):
        """
        The domain with no located house witness. Under strict it must say
        so rather than borrowing marriage's evidence.
        """
        prediction, features = build_prediction(profile="strict")
        document = build_interpretation(
            prediction, mode=ReportMode.DETAILED, features=features,
            generated=FIXED_TIME)
        section = document.section_for("RELATIONSHIPS")
        self.assertIsNotNone(section)
        self.assertTrue(section.is_silent)


# ── Part 23: localisation architecture ───────────────────────────────────────

class LocalisationTest(unittest.TestCase):

    def test_grammar_words_come_from_the_template_set(self):
        """
        Part 23: conjunctions live in the locale, not in Python. A language
        that conjoins differently must not need a code change.
        """
        templates = load_templates("en")
        self.assertIn("list_two", templates.grammar)
        self.assertIn("list_last", templates.grammar)
        self.assertIn("months", templates.grammar)

    def test_join_uses_supplied_conjunctions(self):
        self.assertEqual(join(["a", "b"], two="und", last="und"), "a und b")
        self.assertEqual(join(["a", "b", "c"], two="und", last="und"),
                         "a, b und c")

    def test_templates_are_complete_sentences_not_fragments(self):
        """
        Part 23: prefer complete parameterised messages. A fragment cannot
        be reordered by a translator whose grammar needs a different order.
        """
        templates = load_templates("en")
        for key in K.ACTIVATION + K.CONFIDENCE + K.CONTRADICTION_KEYS:
            template = templates.template(key)
            with self.subTest(key=key):
                self.assertTrue(template[0].isupper())
                self.assertIn(template[-1], ".!?")

    def test_a_new_locale_needs_no_code_change(self):
        """
        Architecture check: a locale is a directory of JSON. Building one
        with the same keys renders without touching Python.
        """
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(os.path.join(TEMPLATE_ROOT, "en"),
                            os.path.join(tmp, "xx"))
            templates = TemplateSet("xx", root=tmp)
            self.assertTrue(templates.render("document.disclaimer"))
            self.assertIn("xx", available_languages(tmp))


# ── grammar helpers (Part 24) ────────────────────────────────────────────────

class GrammarTest(unittest.TestCase):

    def test_ordinals(self):
        for value, expected in ((1, "1st"), (2, "2nd"), (3, "3rd"),
                                (4, "4th"), (11, "11th"), (12, "12th"),
                                (13, "13th"), (21, "21st")):
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_join_handles_zero_one_and_many(self):
        self.assertEqual(join([]), "")
        self.assertEqual(join(["a"]), "a")
        self.assertEqual(join(["a", "b"]), "a and b")
        self.assertEqual(join(["a", "b", "c"]), "a, b and c")

    def test_sentence_does_not_double_punctuate(self):
        self.assertEqual(sentence("hello"), "Hello.")
        self.assertEqual(sentence("Hello."), "Hello.")
        self.assertEqual(sentence("Really?"), "Really?")

    def test_domain_titles(self):
        self.assertEqual(titlecase_domain("FOREIGN_RESIDENCE"),
                         "Foreign Residence")


# ── serialisation (Part 26) ──────────────────────────────────────────────────

class SerialisationTest(_Base):

    def test_document_round_trips_through_json(self):
        document = self.render(ReportMode.TECHNICAL)
        data = json.loads(document.to_json())
        for key in ("schema_version", "language", "report_mode",
                    "methodology_profile",
                    "generated_from_prediction_schema", "domain_sections",
                    "claims", "not_included"):
            self.assertIn(key, data)

    def test_it_references_the_prediction_schema_it_rendered(self):
        document = self.render()
        self.assertEqual(document.generated_from_prediction_schema,
                         self.prediction["schema_version"])
        self.assertEqual(document.natal_snapshot_id,
                         self.prediction["natal_snapshot_id"])

    def test_technical_mode_keeps_key_and_args_for_audit(self):
        """
        Every sentence records the template and the values that produced it,
        so a reviewer can check the prose against the structured result
        without rerunning anything.
        """
        data = self.render(ReportMode.TECHNICAL).to_dict()
        section = data["domain_sections"][0]
        if "overall" in section:
            self.assertIn("key", section["overall"])
            self.assertIn("args", section["overall"])


if __name__ == "__main__":
    unittest.main()
