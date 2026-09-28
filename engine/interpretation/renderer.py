"""
Template resolution (V1.6 Parts 10, 12, 13, 23, 29)
-----------------------------------------------------
Loads a locale's templates and resolves a key plus arguments into a sentence.

THE ONE RULE THIS MODULE ENFORCES

    A key that is not defined raises. An argument a template needs and did
    not get raises. An unknown locale raises.

    It never falls back to generic text, and Part 29 asks for exactly that.
    Silent fallback is worse than a crash here, because the output still
    looks like a reading: the reader gets a bland sentence where a specific
    finding should have been and has no way to know something was lost.

WHAT IT REFUSES TO DO (Part 10)

    Nothing in this module inspects a chart, a graha, a house or a yoga. It
    is given a key and a dictionary of already-computed values and it
    performs substitution. It cannot decide whether a yoga exists or whether
    a domain is activated, because it is never shown anything it could
    decide that from.

DETERMINISM (Part 28)

    `str.format_map` over a dict, with sorted iteration wherever order could
    matter. No random choice among phrasings, no time-dependent behaviour,
    no dict-ordering dependence. Identical inputs give byte-identical output.

FILE LAYOUT (Part 12)

    templates/<lang>/common.json     shared keys
    templates/<lang>/<domain>.json   per-domain overrides

    Resolution looks in the domain file first, then common. That fallback is
    between template files and is not a fallback to generic text: the key
    must exist in one of them.
"""

from __future__ import annotations

import json
import os
import string
from typing import Optional

from . import keys as K

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "templates")

DEFAULT_LANGUAGE = "en"


class TemplateError(KeyError):
    """A key or argument a template set cannot satisfy."""


class MissingTemplateKey(TemplateError):
    pass


class MissingTemplateArgument(TemplateError):
    pass


class UnsupportedLocale(TemplateError):
    pass


def available_languages(root: Optional[str] = None) -> list[str]:
    root = root or TEMPLATE_ROOT
    if not os.path.isdir(root):
        return []
    return sorted(
        name for name in os.listdir(root)
        if os.path.isdir(os.path.join(root, name)) and not name.startswith("."))


def _flatten(node, prefix: str = "") -> dict:
    """
    Turn nested JSON into dotted keys.

    Templates are written nested, because that is how a translator wants to
    read them, and looked up flat, because that is how the code refers to
    them.
    """
    out: dict = {}
    for key in sorted(node):
        value = node[key]
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, path))
        else:
            out[path] = value
    return out


#: Locale files this loader must not read as domain overrides.
RESERVED_FILES = frozenset({"report"})


class TemplateSet:
    """One locale's templates, loaded once."""

    def __init__(self, language: str = DEFAULT_LANGUAGE,
                 root: Optional[str] = None):
        self.language = language
        self.root = root or TEMPLATE_ROOT
        directory = os.path.join(self.root, language)
        if not os.path.isdir(directory):
            raise UnsupportedLocale(
                f"no templates for language '{language}' in {self.root}. "
                f"Available: {', '.join(available_languages(self.root)) or 'none'}")

        self.common: dict = {}
        self.by_domain: dict[str, dict] = {}
        # Files in a locale directory that are NOT engine domains. V1.8
        # added `report.json`, the application's own chrome strings, which
        # live beside the engine's locale files because Part 25 forbids
        # scattering translation dictionaries. Without this the loader
        # read it as an eighteenth life area called REPORT.
        self.grammar: dict = {}

        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            if name[:-5] in RESERVED_FILES:
                continue
            with open(os.path.join(directory, name), encoding="utf-8") as fh:
                payload = json.load(fh)
            stem = name[:-5]
            if stem == "common":
                self.grammar = payload.pop("grammar", {})
                self.common = _flatten(payload)
            else:
                self.by_domain[stem.upper()] = _flatten(payload)

        if not self.common:
            raise UnsupportedLocale(
                f"language '{language}' has no common.json")

    # ── lookup ──────────────────────────────────────────────────────────────

    def defined_keys(self, domain: Optional[str] = None) -> set[str]:
        have = set(self.common)
        if domain:
            have |= set(self.by_domain.get(domain.upper(), {}))
        return have

    def all_defined_keys(self) -> set[str]:
        have = set(self.common)
        for overrides in self.by_domain.values():
            have |= set(overrides)
        return have

    def has(self, key: str, domain: Optional[str] = None) -> bool:
        return key in self.defined_keys(domain)

    def template(self, key: str, domain: Optional[str] = None) -> str:
        if domain:
            override = self.by_domain.get(domain.upper(), {}).get(key)
            if override is not None:
                return override
        value = self.common.get(key)
        if value is None:
            raise MissingTemplateKey(
                f"no template for key '{key}'"
                + (f" (domain {domain})" if domain else "")
                + f" in language '{self.language}'. Part 29: add it rather "
                  f"than letting the renderer substitute generic text.")
        return value

    # ── rendering ───────────────────────────────────────────────────────────

    def render(self, key: str, domain: Optional[str] = None, **args) -> str:
        """
        Resolve one key. Raises on a missing key or a missing argument.
        """
        template = self.template(key, domain)
        merged = dict(self.grammar)
        merged.update(args)
        try:
            return template.format_map(_StrictArgs(merged, key, self.language))
        except MissingTemplateArgument:
            raise
        except (IndexError, ValueError) as exc:
            raise TemplateError(
                f"template '{key}' in '{self.language}' is malformed: "
                f"{exc}") from exc

    def join(self, items, domain: Optional[str] = None) -> str:
        """List joining with this locale's conjunctions."""
        from .grammar import join
        return join(
            items,
            two=self.grammar.get("list_two", "and"),
            last=self.grammar.get("list_last", "and"),
            separator=self.grammar.get("list_separator", ", "))

    def month_names(self):
        return self.grammar.get("months")

    # ── vocabulary (V1.7 Parts 24, 25) ──────────────────────────────────────
    #
    # V1.6 put the JOIN WORDS in the locale and left the rest in Python:
    # "7th house" was built by `grammar.house_name`, the ordinal suffix was
    # a Python table, and a dozen short words — "debilitated", "combust",
    # "mahadasha" — were English string literals passed in as template
    # arguments.
    #
    # Hindi is what made that visible. `सातवें भाव` is not `{ordinal} house`
    # with the words swapped: the ordinal is a distinct word, it inflects
    # for the oblique case the postposition needs, and the noun follows the
    # numeral rather than preceding it. A locale that cannot supply its own
    # ordinals cannot write that phrase at all.
    #
    # So every word that reaches a reader now comes from the locale, and
    # Python supplies only the English fallback. Part 25 asks for the
    # mapping to be centralised rather than scattered; these five methods
    # are that one place.

    def ordinal(self, number: int) -> str:
        """The ordinal word or numeral form this locale uses."""
        ordinals = self.grammar.get("ordinals")
        if ordinals and 1 <= number <= len(ordinals):
            return ordinals[number - 1]
        from .grammar import ordinal
        return ordinal(number)

    def house_name(self, number: int) -> str:
        """`7th house`, `सातवें भाव`. Assembled by the LOCALE's pattern."""
        pattern = self.grammar.get("house_name")
        if pattern:
            return pattern.format(ordinal=self.ordinal(number),
                                  number=number)
        from .grammar import house_name
        return house_name(number)

    def planet(self, name: str) -> str:
        return (self.grammar.get("planets") or {}).get(name) or name

    def sign(self, name: str) -> str:
        return (self.grammar.get("signs") or {}).get(name) or name

    def domain_title(self, domain: str) -> str:
        titles = self.grammar.get("domains") or {}
        if domain in titles:
            return titles[domain]
        from .grammar import titlecase_domain
        return titlecase_domain(domain)

    def term(self, category: str, value: str, default: Optional[str] = None
             ) -> str:
        """
        One word of shared vocabulary: a dignity, a dasha level, a state.

        These are template ARGUMENTS rather than templates, which is why
        they were missed in V1.6 — they are substituted into a sentence and
        so never appear in a template file. A locale that translates the
        sentence and not the words inside it produces Hindi with English
        nouns in the middle of it.
        """
        terms = (self.grammar.get("terms") or {}).get(category) or {}
        if value in terms:
            return terms[value]
        if default is not None:
            return default
        return str(value).replace("_", " ").lower()

    def duration(self, days: float) -> str:
        bands = self.grammar.get("duration")
        if bands:
            for limit, phrase in bands:
                if days < limit:
                    return phrase
            return bands[-1][1]
        from .grammar import duration_phrase
        return duration_phrase(days)


class _StrictArgs(dict):
    """A mapping that reports which argument a template wanted."""

    def __init__(self, data, key, language):
        super().__init__(data)
        self._key = key
        self._language = language

    def __missing__(self, name):
        raise MissingTemplateArgument(
            f"template '{self._key}' in '{self._language}' needs argument "
            f"'{name}', which the renderer did not supply. Part 29: this is "
            f"a defect in the caller or the template, not something to "
            f"paper over.")


_CACHE: dict[tuple[str, str], TemplateSet] = {}


def load_templates(language: str = DEFAULT_LANGUAGE,
                   root: Optional[str] = None) -> TemplateSet:
    """Load and cache a locale. Caching is safe: template sets are read-only."""
    cache_key = (language, root or TEMPLATE_ROOT)
    if cache_key not in _CACHE:
        _CACHE[cache_key] = TemplateSet(language, root)
    return _CACHE[cache_key]


def template_arguments(template: str) -> set[str]:
    """Which named arguments a template string requires."""
    return {
        name for _literal, name, _spec, _conv
        in string.Formatter().parse(template) if name}


def completeness_report(language: str = DEFAULT_LANGUAGE,
                        root: Optional[str] = None) -> dict:
    """
    What a locale defines, and what it is missing (Part 29).

    Used by the template-completeness test and by the CLI, so that adding a
    locale tells you exactly what remains to translate rather than failing
    at render time on whichever key a particular chart happened to need.
    """
    templates = load_templates(language, root)
    defined = templates.all_defined_keys()
    missing = K.missing_keys(defined)
    extra = sorted(key for key in defined if key not in set(K.ALL_KEYS))
    return {
        "language": language,
        "defined": len(defined),
        "required": len(K.ALL_KEYS),
        "missing": missing,
        "complete": not missing,
        "not_in_key_registry": extra,
        "domains_with_overrides": sorted(templates.by_domain),
    }
