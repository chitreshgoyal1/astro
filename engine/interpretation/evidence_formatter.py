"""
Evidence to phrase (V1.6 Parts 10, 14)
----------------------------------------
Turns one structured DomainEvidence record into one sentence.

THE CONSTRAINT THAT SHAPES THIS MODULE

    Part 14: do NOT add claims absent from the evidence.

    So the arguments handed to a template come only from fields the
    synthesis layer computed. If a record says `{"factor":
    "house_lord_strength", "house": 10, "planet": "Guru", "direction":
    "SUPPORTIVE"}` then the sentence may mention the tenth house, Guru and
    support, and may not mention a career, a promotion, or how likely
    anything is.

    A sentence with a slot the evidence cannot fill is a defect, and
    `renderer` raises on it rather than substituting something plausible.

WHY THE ARGUMENT EXTRACTION IS EXPLICIT

    It would be shorter to hand the whole evidence dict to `format_map` and
    let templates pick what they want. That would also mean a template
    author could reach any field of any record, including the engine's
    internal weights, and quietly promote a SOFTWARE_HEURISTIC magnitude
    into prose. Each key gets exactly the arguments listed for it here, and
    nothing else is in scope.
"""

from __future__ import annotations

from typing import Optional

from . import grammar as G
from . import keys as K


#: The locale used when a caller supplies none. English, and identical to
#: V1.6's hard-coded behaviour, so an existing caller sees no change.
_FALLBACK = None


def _vocabulary(templates):
    """
    The locale's vocabulary, or English.

    `templates` became a parameter of the argument builders in V1.7, when
    Hindi showed that the ARGUMENTS need translating as much as the
    sentences do. It is optional so that every V1.6 caller keeps working
    and gets exactly what it got before.
    """
    global _FALLBACK
    if templates is not None:
        return templates
    if _FALLBACK is None:
        from .renderer import load_templates
        _FALLBACK = load_templates("en")
    return _FALLBACK


def _house(value, templates=None) -> str:
    if value is None:
        return ""
    return _vocabulary(templates).house_name(int(value))


# Evidence arrives as the SERIALISED form from PredictionSnapshot, not as a
# live DomainEvidence. That is deliberate: this package must be able to
# render a snapshot read from a file months later, with no engine objects in
# memory, which is also what makes the determinism test meaningful.

def _get(item, field, default=None):
    return item.get(field, default)


def _houses(item) -> list:
    return list(_get(item, "houses", []) or [])


def _planets(item) -> list:
    return list(_get(item, "planets", []) or [])


def _first_house(item) -> Optional[int]:
    houses = _houses(item)
    return houses[0] if houses else None


def _first_planet(item) -> Optional[str]:
    planets = _planets(item)
    return planets[0] if planets else None


def evidence_arguments(item, features=None, templates=None) -> dict:
    """
    The arguments one evidence record supplies to its template.

    `features` is optional and read-only: it is consulted for the graha's
    sign and dignity, which the natal layer knows and does not put on the
    evidence record. Nothing is computed from it — if it is absent the
    template gets the values the record itself carries.

    `templates` supplies the locale's vocabulary. Every word below that a
    reader will see — the house name, the graha's name, the dignity, the
    dasha level — is looked up rather than written, because Hindi needs
    all of them and English happens not to make that obvious.
    """
    vocab = _vocabulary(templates)
    key = _get(item, "explanation_key", "")
    planet = _first_planet(item)
    house = _first_house(item)
    args: dict = {}

    def dignity_of(name: str) -> str:
        raw = "dignified"
        if features is not None and name is not None:
            found = features.planet(name)
            if found:
                raw = getattr(found, "dignity", "dignified")
        return vocab.term("dignity", raw, default=raw)

    def sign_of(name: str) -> str:
        if features is None or name is None:
            return vocab.term("placeholder", "its_sign", default="its sign")
        found = features.planet(name)
        if not found:
            return vocab.term("placeholder", "its_sign", default="its sign")
        return vocab.sign(getattr(found, "sign_name", "") or "")

    def graha(name) -> str:
        return vocab.planet(name) if name else ""

    def in_house(value) -> str:
        return _house(value, templates)

    if key in ("house_lord_dignified", "house_lord_debilitated"):
        args = {"house": in_house(house),
                "dignity": dignity_of(planet),
                "sign": sign_of(planet)}
    elif key in ("house_lord_in_dusthana", "house_lord_well_placed"):
        # The record carries (owned_house, occupied_house) in that order.
        houses = _houses(item)
        occupied = houses[1] if len(houses) > 1 else house
        args = {"house": in_house(house),
                "occupied_house": in_house(occupied)}
    elif key == "house_lord_combust":
        args = {"house": in_house(house)}
    elif key in ("benefic_occupies_house", "malefic_occupies_house",
                 "benefic_aspects_house", "malefic_aspects_house"):
        args = {"planet": graha(planet), "house": in_house(house)}
    elif key == "karaka_dignified":
        args = {"planet": graha(planet), "dignity": dignity_of(planet)}
    elif key == "karaka_afflicted":
        found = features.planet(planet) if features and planet else None
        state = "afflicted"
        if found is not None:
            state = "debilitated" if found.debilitated else (
                "combust" if found.combust else "afflicted")
        args = {"planet": graha(planet),
                "state": vocab.term("state", state, default=state)}
    elif key == "house_lord_shadbala":
        args = {"house": in_house(house), "ratio": _ratio_from(item)}
    elif key == "sarvashtakavarga_bindus":
        args = {"house": in_house(house), "bindus": _bindus_from(item),
                "reference": "28"}
    elif key == "yoga_present":
        args = {"yoga": _yoga_name_from(item),
                "status": _status_from(item, vocab)}
    elif key == "dasha_lord_activates_house":
        args = {"planet": graha(planet),
                "level": _level_from(item, vocab),
                "houses": _house_list(item, templates)}
    elif key == "dasha_lord_carries_yoga":
        args = {"planet": graha(planet),
                "level": _level_from(item, vocab),
                "yoga": (_get(item, "rule_ids") or ["a yoga"])[0]}
    elif key in ("over_natal_house", "over_house_from_natal_moon"):
        args = {"planet": graha(planet), "house": in_house(house)}
    elif key in ("conjunct_natal_point", "graha_drishti_to_natal_point"):
        args = {"planet": graha(planet),
                "target": _target_from(item, vocab)}
    return args


# ── small extractors ─────────────────────────────────────────────────────────
#
# These read values the synthesis layer already put into the evidence
# record's own explanation. They parse rather than recompute, because
# recomputing would be a second implementation of a fact and the two would
# eventually disagree — the reason engine/features exists at all.

def _ratio_from(item) -> str:
    text = _get(item, "explanation", "")
    marker = "Shadbala "
    if marker in text:
        rest = text.split(marker, 1)[1]
        value = rest.split("x", 1)[0].strip()
        if value:
            return value
    return "the measured"


def _bindus_from(item) -> str:
    for token in _get(item, "explanation", "").replace(",", " ").split():
        if token.isdigit():
            return token
    return "the counted number"


def _yoga_name_from(item) -> str:
    return _get(item, "explanation", "").split(":", 1)[0].strip() or "a combination"


def _status_from(item, vocab=None) -> str:
    text = _get(item, "explanation", "")
    raw = "PRESENT"
    if ":" in text:
        raw = text.split(":", 1)[1].strip().rstrip(".")
    vocab = _vocabulary(vocab)
    return vocab.term("yoga_status", raw,
                      default=raw.replace("_", " ").lower())


def _level_from(item, vocab=None) -> str:
    vocab = _vocabulary(vocab)
    for level in ("pratyantardasha", "antardasha", "mahadasha"):
        if level in _get(item, "factor_id", ""):
            return vocab.term("dasha_level", level, default=level)
    return vocab.term("dasha_level", "period", default="period")


def _house_list(item, templates=None) -> str:
    vocab = _vocabulary(templates)
    houses = _houses(item)
    if not houses:
        return vocab.term("placeholder", "relevant_houses",
                          default="relevant houses")
    return vocab.join([vocab.house_name(h) for h in sorted(houses)])


def _target_from(item, vocab=None) -> str:
    vocab = _vocabulary(vocab)
    text = _get(item, "explanation", "")
    if "natal " in text:
        rest = text.split("natal ", 1)[1]
        name = rest.split(" ", 1)[0].strip().rstrip(".,")
        return vocab.planet(name)
    return vocab.term("placeholder", "a_natal_point",
                      default="a natal point")


def format_evidence(item, templates, features=None, domain: Optional[str] = None):
    """
    Render one evidence record. Returns a RenderedPhrase.

    Raises when the evidence type has no key, which is Part 29's intent: an
    evidence type the renderer cannot describe is one the reader would never
    learn about, and a release that adds one should fail loudly.
    """
    from .models import RenderedPhrase

    key = K.evidence_key(_get(item, "explanation_key", ""))
    args = evidence_arguments(item, features, templates)
    text = templates.render(key, domain=domain, **args)
    return RenderedPhrase(key=key, text=G.sentence(text, templates.grammar),
                          args=args)
