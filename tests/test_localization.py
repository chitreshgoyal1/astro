"""
Hindi localisation (V1.7 Parts 24, 25, 26, 37)
================================================
The second locale, and the design flaws it exposed.

WHY HINDI AND NOT A SECOND EUROPEAN LANGUAGE

    Part 26 asks for a language whose grammar and order differ from
    English, because a locale that differs only in vocabulary proves
    nothing: every substitution point English happens not to need stays
    invisible.

    Hindi found four in the first rendered document.

      1. `{ordinal} house` is not a pattern Hindi has. `सातवें भाव` puts
         a distinct ordinal WORD before the noun, in the oblique form the
         following postposition needs. The ordinals and the pattern both
         had to move into the locale.

      2. The sentence terminator is the danda `।`, not the full stop, and
         Devanagari has no letter case, so `sentence()` was doing two
         English-specific things unconditionally.

      3. A dozen short words reached the templates as ARGUMENTS rather
         than templates — "debilitated", "combust", "mahadasha",
         "standard" — so a fully translated template set still produced
         Hindi sentences with English nouns inside them.

      4. The document headings were English literals in Python, while
         `section.*` keys for them existed and were never used.

    Each is fixed in the engine, not worked around in the templates. The
    tests below are what stops a third locale inheriting any of them.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.interpretation import (
    ALL_KEYS, available_languages, format_interpretation, interpretation_hash,
)
from engine.interpretation.grammar import sentence
from engine.interpretation.renderer import (
    DEFAULT_LANGUAGE, completeness_report, load_templates, template_arguments,
)
from app.models import ConsultationRecord
from app.services import (
    calculate_chart, calculate_prediction, render_interpretation,
)

MOMENT = datetime.datetime(2026, 9, 27, 12)
JAIPUR = dict(name="Jaipur 1988", date_of_birth="1988-08-30",
              time_of_birth="20:18", place="Jaipur")

#: Devanagari, for asserting that output is actually in the script.
DEVANAGARI = range(0x0900, 0x0980)


def _is_devanagari(text: str) -> bool:
    return any(ord(c) in DEVANAGARI for c in text)


class _Rendered(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.natal = calculate_chart(ConsultationRecord(**JAIPUR))
        cls.prediction = calculate_prediction(cls.natal, MOMENT)
        cls.en = render_interpretation(cls.prediction, language="en",
                                       mode="detailed")
        cls.hi = render_interpretation(cls.prediction, language="hi",
                                       mode="detailed")


# ── Part 24: the locale exists and is complete ───────────────────────────────

class LocaleCompletenessTest(unittest.TestCase):

    def test_hindi_is_installed(self):
        self.assertIn("hi", available_languages())

    def test_every_installed_locale_defines_every_key(self):
        """
        Part 29 of V1.6, now with something to test it against. The
        renderer raises on a missing key rather than substituting generic
        text, so an incomplete locale fails at whichever key a particular
        chart happened to need — which is not when you want to find out.
        """
        for language in available_languages():
            with self.subTest(language=language):
                report = completeness_report(language)
                self.assertTrue(report["complete"],
                                f"missing: {report['missing']}")
                self.assertEqual(report["missing"], [])

    def test_both_locales_define_the_same_domain_overrides(self):
        """
        A locale that translated common.json and skipped the seventeen
        domain files would pass the completeness check by falling back to
        the common sentence — correct, but not the domain's own.
        """
        english = set(load_templates("en").by_domain)
        hindi = set(load_templates("hi").by_domain)
        self.assertEqual(hindi, english)
        self.assertEqual(len(hindi), 17)

    def test_no_key_is_left_in_english_in_the_hindi_set(self):
        hindi = load_templates("hi")
        untranslated = []
        for key in ALL_KEYS:
            text = hindi.template(key)
            if not _is_devanagari(text):
                untranslated.append(key)
        self.assertEqual(
            untranslated, [],
            "these Hindi templates contain no Devanagari at all")

    def test_the_two_locales_take_the_same_arguments(self):
        """
        A translator who renamed a slot, or dropped one, would produce a
        template that raises at render time on a chart that happens to
        reach it. The argument sets must match key for key.
        """
        english, hindi = load_templates("en"), load_templates("hi")
        for key in ALL_KEYS:
            with self.subTest(key=key):
                self.assertEqual(
                    template_arguments(hindi.template(key))
                    - set(hindi.grammar),
                    template_arguments(english.template(key))
                    - set(english.grammar))


# ── Part 24: complete messages, not concatenated fragments ───────────────────

class ParameterisedMessageTest(unittest.TestCase):

    def test_no_template_is_a_bare_fragment(self):
        """
        Part 24: do not translate by concatenating word fragments. A
        template that is a single slot with no words of its own is a
        fragment waiting to be glued to another one.
        """
        hindi = load_templates("hi")
        for key in ALL_KEYS:
            if key.startswith(("section.", "heading.")):
                continue          # headings are legitimately single words
            text = hindi.template(key)
            with self.subTest(key=key):
                stripped = text
                for argument in template_arguments(text):
                    stripped = stripped.replace("{" + argument + "}", "")
                self.assertGreater(
                    len(stripped.strip()), 12,
                    "a template that is mostly slots is a fragment")

    def test_technical_identifiers_are_never_translated(self):
        """
        Part 25: keep technical identifiers untranslated internally. The
        document's `profile` field is the engine's value; only the word
        printed inside a sentence is localised.
        """
        natal = calculate_chart(ConsultationRecord(**JAIPUR))
        prediction = calculate_prediction(natal, MOMENT, profile="strict")
        document = render_interpretation(prediction, language="hi",
                                         mode="detailed")
        self.assertEqual(document.profile, "strict")
        self.assertEqual(document.language, "hi")
        for section in document.domain_sections:
            with self.subTest(domain=section.domain):
                self.assertTrue(section.domain.isascii())
                self.assertIn(section.activation,
                              ("INACTIVE", "BACKGROUND", "ACTIVE",
                               "STRONGLY_ACTIVE", "MIXED"))


# ── Part 26: the grammar the locale owns ─────────────────────────────────────

class LocaleGrammarTest(unittest.TestCase):

    def setUp(self):
        self.en = load_templates("en")
        self.hi = load_templates("hi")

    def test_house_names_are_built_by_the_locale_s_own_pattern(self):
        self.assertEqual(self.en.house_name(7), "7th house")
        self.assertEqual(self.hi.house_name(7), "सातव"
                                                "ें भा"
                                                "व")
        for number in range(1, 13):
            with self.subTest(house=number):
                self.assertTrue(_is_devanagari(self.hi.house_name(number)))

    def test_ordinals_are_words_and_not_a_suffix_rule(self):
        """
        English builds an ordinal from a numeral and a suffix. Hindi does
        not, and a locale that could only supply a suffix could not write
        `सातवें` at all.
        """
        hindi = [self.hi.ordinal(n) for n in range(1, 13)]
        self.assertEqual(len(set(hindi)), 12)
        for word in hindi:
            with self.subTest(word=word):
                self.assertTrue(_is_devanagari(word))
                self.assertFalse(any(c.isdigit() for c in word))

    def test_list_conjunction_comes_from_the_locale(self):
        items = ["सूर्य",
                 "चन्द्र",
                 "मंगल"]
        joined = self.hi.join(items)
        self.assertIn("तथा", joined)   # तथा
        self.assertNotIn(" and ", joined)

    def test_two_item_and_three_item_lists_conjoin_differently(self):
        two = self.hi.join(["अ", "ब"])
        three = self.hi.join(["अ", "ब", "स"])
        self.assertIn("और", two)            # और, for two
        self.assertIn("तथा", three)    # तथा, for the last

    def test_the_sentence_terminator_is_the_danda(self):
        """Appending a full stop to a Hindi sentence is wrong punctuation."""
        hindi = sentence("यह एक वाक"
                         "्य", self.hi.grammar)
        self.assertTrue(hindi.endswith("।"))
        self.assertFalse(hindi.endswith("."))
        self.assertTrue(sentence("this is a sentence").endswith("."))

    def test_capitalisation_is_skipped_where_the_script_has_no_case(self):
        text = "विवाह"
        self.assertEqual(sentence(text, self.hi.grammar).rstrip("।"),
                         text)

    def test_months_come_from_the_locale(self):
        self.assertEqual(len(self.hi.month_names()), 12)
        for month in self.hi.month_names():
            with self.subTest(month=month):
                self.assertTrue(_is_devanagari(month))

    def test_planet_and_sign_names_come_from_the_locale(self):
        self.assertEqual(self.hi.planet("Guru"), "गुरु")
        self.assertEqual(self.hi.sign("Kanya"), "कन्या")
        self.assertEqual(self.en.planet("Guru"), "Guru")

    def test_the_lagna_is_in_the_planet_table(self):
        """
        It is a natal POINT rather than a graha, and the transit evidence
        names it alongside the nine. Leaving it out produced one English
        word in the middle of a Hindi sentence.
        """
        self.assertTrue(_is_devanagari(self.hi.planet("Lagna")))

    def test_shared_vocabulary_is_centralised(self):
        """
        Part 25: do not scatter translation dictionaries. Every one of
        these is looked up in one place, `TemplateSet.term`.
        """
        for category, value in (("dignity", "Uchcha"),
                                ("state", "combust"),
                                ("dasha_level", "antardasha"),
                                ("profile", "standard"),
                                ("yoga_status", "PRESENT_AND_STRONG")):
            with self.subTest(category=category, value=value):
                self.assertTrue(_is_devanagari(self.hi.term(category, value)))

    def test_an_unknown_term_falls_back_without_raising(self):
        """
        A vocabulary gap must degrade to the engine's own word, not to a
        crash: the term tables are open-ended by nature and a new dignity
        should not take the renderer down.
        """
        self.assertEqual(self.hi.term("dignity", "Something_New"),
                         "something new")

    def test_domain_titles_come_from_the_locale(self):
        self.assertEqual(self.hi.domain_title("CAREER"),
                         "आजीविका")
        self.assertEqual(self.en.domain_title("FOREIGN_RESIDENCE"),
                         "Foreign Residence")


# ── Part 26: the rendered document ───────────────────────────────────────────

class HindiRenderingTest(_Rendered):

    def test_the_whole_document_is_in_hindi(self):
        text = format_interpretation(self.hi)
        self.assertTrue(_is_devanagari(text))
        # Every heading too — these were English literals until V1.7.
        for english in ("Supporting factors", "Challenging factors",
                        "Reliability", "Interpretation", "Note"):
            with self.subTest(heading=english):
                self.assertNotIn(english, text)

    def test_house_references_are_in_hindi_inside_sentences(self):
        for section in self.hi.domain_sections:
            for phrase in section.supporting + section.challenging:
                if "house" in phrase.args:
                    with self.subTest(domain=section.domain):
                        self.assertTrue(_is_devanagari(phrase.args["house"]))
                        self.assertIn(phrase.args["house"], phrase.text)

    def test_dates_are_in_hindi(self):
        joined = " ".join(p.text for p in self.hi.methodology_summary)
        self.assertTrue(_is_devanagari(joined))
        for english_month in ("September", "August"):
            with self.subTest(month=english_month):
                self.assertNotIn(english_month, joined)

    def test_timing_sentences_are_in_hindi(self):
        if not (self.hi.timing_sections
                and self.hi.timing_sections.dasha_stack):
            self.skipTest("this chart produced no dasha stack sentence")
        text = self.hi.timing_sections.dasha_stack.text
        self.assertTrue(_is_devanagari(text))
        self.assertTrue(text.endswith("।"))

    def test_confidence_sentences_are_in_hindi(self):
        for section in self.hi.domain_sections:
            if section.confidence_phrase is None:
                continue
            with self.subTest(domain=section.domain):
                self.assertTrue(
                    _is_devanagari(section.confidence_phrase.text))

    def test_warnings_are_in_hindi(self):
        for phrase in self.hi.reliability_warnings:
            with self.subTest(key=phrase.key):
                self.assertTrue(_is_devanagari(phrase.text))

    def test_mixed_evidence_renders_in_hindi(self):
        mixed = [s for s in self.hi.domain_sections
                 if s.supporting and s.challenging]
        self.assertTrue(mixed, "this chart should produce a mixed domain")
        for section in mixed:
            with self.subTest(domain=section.domain):
                self.assertIsNotNone(section.contradiction)
                self.assertTrue(_is_devanagari(section.contradiction.text))

    def test_silence_renders_in_hindi(self):
        prediction = calculate_prediction(self.natal, MOMENT,
                                          profile="strict")
        document = render_interpretation(prediction, language="hi",
                                         mode="detailed")
        silent = [s for s in document.domain_sections if s.is_silent]
        self.assertTrue(silent, "strict should decline at least one domain")
        for section in silent:
            with self.subTest(domain=section.domain):
                self.assertTrue(_is_devanagari(section.silence.text))


# ── Part 26: the findings must be identical in both languages ────────────────

class LanguageNeutralityTest(_Rendered):

    def test_the_two_languages_report_the_same_findings(self):
        """
        A translation must change the words and nothing else. If Hindi
        reported a different activation for any domain, the locale would
        be deciding something.
        """
        english = {s.domain: (s.activation, s.confidence)
                   for s in self.en.domain_sections}
        hindi = {s.domain: (s.activation, s.confidence)
                 for s in self.hi.domain_sections}
        self.assertEqual(hindi, english)

    def test_the_same_keys_are_used_in_both(self):
        for section in self.en.domain_sections:
            other = self.hi.section_for(section.domain)
            self.assertIsNotNone(other)
            with self.subTest(domain=section.domain):
                self.assertEqual(
                    [p.key for p in section.supporting],
                    [p.key for p in other.supporting])

    def test_neither_language_is_the_other_s_fallback(self):
        """
        If Hindi silently fell back to English for a key, the two
        documents would share a sentence. They must share none.
        """
        english = {p.text for s in self.en.domain_sections
                   for p in s.supporting + s.challenging}
        hindi = {p.text for s in self.hi.domain_sections
                 for p in s.supporting + s.challenging}
        self.assertTrue(english)
        self.assertEqual(english & hindi, set())


# ── Part 26: determinism ─────────────────────────────────────────────────────

class HindiDeterminismTest(_Rendered):

    def test_hindi_rendering_is_byte_identical_across_runs(self):
        again = render_interpretation(self.prediction, language="hi",
                                      mode="detailed")
        self.assertEqual(interpretation_hash(self.hi),
                         interpretation_hash(again))
        self.assertEqual(format_interpretation(self.hi),
                         format_interpretation(again))

    def test_the_hindi_document_serialises_and_round_trips(self):
        payload = json.dumps(self.hi.to_dict(), ensure_ascii=False)
        self.assertTrue(_is_devanagari(payload))
        json.loads(payload)

    def test_no_machine_translation_is_reachable_at_runtime(self):
        """
        Part 26: no machine-translation dependency at runtime. The
        templates are files; nothing in the interpretation package opens a
        socket, and this proves it by making the socket constructor fail.
        """
        import socket

        real = socket.socket
        socket.socket = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("the renderer must not open a socket"))
        try:
            document = render_interpretation(self.prediction, language="hi",
                                             mode="technical")
            self.assertTrue(document.domain_sections)
        finally:
            socket.socket = real


# ── English must not have regressed ──────────────────────────────────────────

class EnglishUnchangedTest(_Rendered):

    def test_english_is_still_the_default(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")

    def test_english_sentences_still_end_in_a_full_stop(self):
        for section in self.en.domain_sections:
            if section.overall is None:
                continue
            with self.subTest(domain=section.domain):
                self.assertTrue(section.overall.text.endswith("."))

    def test_english_house_names_are_unchanged(self):
        english = load_templates("en")
        self.assertEqual(english.house_name(1), "1st house")
        self.assertEqual(english.house_name(11), "11th house")
        self.assertEqual(english.house_name(12), "12th house")


if __name__ == "__main__":
    unittest.main()
