"""
Deterministic text normalisation (V1.6 Parts 23, 24)
------------------------------------------------------
List joining, punctuation, dates, and the names of things.

NO NLP, NO DEPENDENCY, NO RANDOMNESS

    Every function here is a pure function of its arguments. There is no
    phrase selection, no synonym table, no "vary the wording so it reads
    naturally". Part 28 requires byte-identical output for identical input,
    and the cheapest way to guarantee that is to have nothing here that could
    ever produce two answers.

LOCALISATION (Part 23)

    The hard part of translating generated text is not the words, it is the
    grammar that assembles them. `A, B and C` is an English fact; Hindi
    conjoins differently, and a language with case marking would need the
    list items inflected by their role in the sentence.

    So the join words live in the template set, not in this module. A locale
    supplies its own `grammar.list_two`, `grammar.list_last` and separator,
    and these functions read them. Nothing here concatenates a translatable
    fragment onto another translatable fragment.
"""

from __future__ import annotations

import datetime
from typing import Optional, Sequence

# Display names. Kept here rather than in a template because they are proper
# nouns in the engine's own vocabulary — the same strings the chart output
# and the JSON use — and a report that called Guru "Jupiter" while the chart
# beside it said "Guru" would be worse, not friendlier.
PLANET_DISPLAY = {
    "Surya": "Surya", "Chandra": "Chandra", "Mangal": "Mangal",
    "Budha": "Budha", "Guru": "Guru", "Shukra": "Shukra", "Shani": "Shani",
    "Rahu": "Rahu", "Ketu": "Ketu",
}

# Optional English glosses, for a locale or report mode that wants them.
PLANET_GLOSS = {
    "Surya": "the Sun", "Chandra": "the Moon", "Mangal": "Mars",
    "Budha": "Mercury", "Guru": "Jupiter", "Shukra": "Venus",
    "Shani": "Saturn", "Rahu": "the north node", "Ketu": "the south node",
}

_ORDINAL_SUFFIX = {1: "st", 2: "nd", 3: "rd"}

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def ordinal(n: int) -> str:
    """1 → '1st'. Teens take 'th' regardless of final digit."""
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{_ORDINAL_SUFFIX.get(n % 10, 'th')}"


def house_name(house: int) -> str:
    return f"{ordinal(house)} house"


def planet_name(planet: str, gloss: bool = False) -> str:
    if gloss:
        return PLANET_GLOSS.get(planet, planet)
    return PLANET_DISPLAY.get(planet, planet)


def yoga_name(name: str) -> str:
    """A yoga's display name, with any parenthetical qualifier kept."""
    return name.strip()


def join(items: Sequence[str], two: str = "and", last: str = "and",
         separator: str = ", ") -> str:
    """
    Deterministic list joining.

    `two` and `last` are supplied by the locale's grammar block, so that a
    translation can change "and" without touching Python, and can use a
    different word for the two-item case where its grammar needs one.
    """
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} {two} {items[1]}"
    return f"{separator.join(items[:-1])} {last} {items[-1]}"


def sentence(text: str, grammar: Optional[dict] = None) -> str:
    """
    Capitalise and terminate, without disturbing text already terminated.

    Templates are written as complete sentences, so this is a guard against
    a template author forgetting the full stop rather than a construction
    step. It never joins two fragments.

    BOTH OPERATIONS ARE LANGUAGE-SPECIFIC, WHICH V1.6 DID NOT NOTICE
    (V1.7 Part 26)

        Devanagari has no letter case, so capitalising its first character
        is a no-op — harmless. Its sentence terminator is the danda `।`,
        not the full stop, and appending `.` to a Hindi sentence is simply
        wrong punctuation.

        So a locale may declare `sentence_end` and `capitalise`. English
        keeps exactly the behaviour it had.
    """
    grammar = grammar or {}
    terminators = grammar.get("sentence_terminators") or ".!?:"
    ending = grammar.get("sentence_end", ".")
    capitalise = grammar.get("capitalise", True)

    text = text.strip()
    if not text:
        return ""
    if capitalise and text[0].islower():
        text = text[0].upper() + text[1:]
    if text[-1] not in terminators:
        text += ending
    return text


def paragraph(sentences: Sequence[str],
              grammar: Optional[dict] = None) -> str:
    """Join complete sentences with single spaces. No fragment assembly."""
    return " ".join(sentence(s, grammar) for s in sentences
                    if s and s.strip())


def format_date(value, month_names: Optional[Sequence[str]] = None) -> str:
    """
    'September 2028'. Month and year only.

    Deliberately coarse. The engine computes window boundaries to the second
    by bisection, and printing that precision next to an interpretation
    would imply a confidence about the EVENT that the arithmetic only has
    about the astronomy.
    """
    if value is None:
        return ""
    names = month_names or MONTHS
    if isinstance(value, str):
        value = datetime.datetime.fromisoformat(value)
    return f"{names[value.month - 1]} {value.year}"


def format_exact_date(value, month_names: Optional[Sequence[str]] = None
                      ) -> str:
    """'27 September 2026'. For technical mode, where precision is the point."""
    if value is None:
        return ""
    names = month_names or MONTHS
    if isinstance(value, str):
        value = datetime.datetime.fromisoformat(value)
    return f"{value.day} {names[value.month - 1]} {value.year}"


def duration_phrase(days: float) -> str:
    """A coarse, deterministic duration band. Never a precise interval."""
    if days < 45:
        return "about a month"
    if days < 120:
        return "a few months"
    if days < 400:
        return "under a year"
    if days < 900:
        return "a little over a year"
    return "several years"


def titlecase_domain(domain: str) -> str:
    """'FOREIGN_RESIDENCE' → 'Foreign Residence'."""
    return " ".join(word.capitalize() for word in domain.split("_"))
