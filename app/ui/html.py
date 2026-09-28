"""
HTML building (V1.7 Parts 5, 36)
==================================
Small, explicit helpers. No template language, no dependency.

ESCAPING IS NOT OPTIONAL HERE

    Every value that reaches a page comes from a snapshot, and a snapshot
    carries a name a user typed. `text()` escapes; the element helpers
    escape their children unless handed a `Raw`, which exists so that
    already-built markup can be nested and is the only way to bypass
    escaping. That makes the unsafe path visible at every call site.

ACCESSIBILITY (Part 36)

    The helpers produce semantic elements — `table`, `th` with scope,
    `figure`/`figcaption`, `label` bound to its control — because a `div`
    grid is invisible to a screen reader and no amount of styling fixes
    that afterwards. Status is never carried by colour alone: every badge
    prints its word.
"""

from __future__ import annotations

import html
from typing import Iterable, Optional


class Raw(str):
    """Markup that is already escaped. The only way past `text()`."""


def text(value) -> str:
    """Escape a value for HTML. `Raw` passes through untouched."""
    if isinstance(value, Raw):
        return str(value)
    return html.escape("" if value is None else str(value), quote=True)


def attrs(mapping: dict) -> str:
    out = []
    for key, value in mapping.items():
        if value is None or value is False:
            continue
        name = key.rstrip("_").replace("_", "-")
        if value is True:
            out.append(name)
        else:
            out.append(f'{name}="{html.escape(str(value), quote=True)}"')
    return (" " + " ".join(out)) if out else ""


# The element name is positional-only. `name` and `id` are both HTML
# attributes a caller will want to pass by keyword, and without the `/`
# they collide with the parameter holding the element name — which is a
# TypeError at the first `<input name="...">`.
def tag(element, /, *children, **attributes) -> Raw:
    inner = "".join(text(c) for c in children if c is not None)
    return Raw(f"<{element}{attrs(attributes)}>{inner}</{element}>")


def void(element, /, **attributes) -> Raw:
    return Raw(f"<{element}{attrs(attributes)} />")


def join(children: Iterable) -> Raw:
    return Raw("".join(text(c) for c in children if c is not None))


# ── common structures ────────────────────────────────────────────────────────

def table(columns, rows, caption: str = "", class_name: str = "data",
          align: Optional[Iterable[str]] = None) -> Raw:
    """
    A data table with real `th` cells and a caption.

    A screen reader announces the column header with each cell only when
    the header is a `th` with a scope. Styling a `td` to look bold does not
    do it, and a planetary table read out as forty loose numbers is not
    usable.
    """
    alignment = list(align or [])
    head = join(
        tag("th", column, scope="col",
            class_=alignment[i] if i < len(alignment) else None)
        for i, column in enumerate(columns))
    body = join(
        tag("tr", join(
            tag("td", cell,
                class_=alignment[i] if i < len(alignment) else None)
            for i, cell in enumerate(row)))
        for row in rows)
    parts = [tag("caption", caption)] if caption else []
    parts.append(tag("thead", tag("tr", head)))
    parts.append(tag("tbody", body))
    return tag("table", join(parts), class_=class_name)


def badge(value: str, kind: str = "") -> Raw:
    """
    A status chip that always prints its word.

    Part 36: colour is never the only encoding. The class tints the chip;
    the text inside says what it is, so the chip works in greyscale, in
    high contrast, and when read aloud.
    """
    label = str(value or "").replace("_", " ").lower()
    return tag("span", label, class_=f"badge {kind}".strip())


def callout(body, kind: str = "note", title: str = "") -> Raw:
    parts = []
    if title:
        parts.append(tag("strong", title))
    parts.append(tag("p", body))
    return tag("aside", join(parts), class_=f"callout {kind}",
               role="note" if kind != "warning" else "alert")


def definition_list(pairs, class_name: str = "kv") -> Raw:
    rows = []
    for key, value, *rest in pairs:
        note = rest[0] if rest else ""
        rows.append(tag("dt", key))
        rows.append(tag("dd", join(
            [tag("span", value, class_="value")]
            + ([tag("span", note, class_="note")] if note else []))))
    return tag("dl", join(rows), class_=class_name)


def field(label: str, control: Raw, help_text: str = "",
          field_id: str = "") -> Raw:
    parts = [tag("label", label, for_=field_id)] if field_id else \
        [tag("label", label)]
    parts.append(control)
    if help_text:
        parts.append(tag("p", help_text, class_="help",
                         id=f"{field_id}-help" if field_id else None))
    return tag("div", join(parts), class_="field")


def select(name: str, options, selected=None, field_id: str = "",
           labels: Optional[dict] = None) -> Raw:
    labels = labels or {}
    items = []
    for option in options:
        items.append(tag("option", labels.get(option, option), value=option,
                         selected=(str(option) == str(selected))))
    return tag("select", join(items), name=name, id=field_id or name)


def input_field(name: str, value="", type_: str = "text", field_id: str = "",
                required: bool = False, placeholder: str = "",
                pattern: str = "") -> Raw:
    return void("input", type=type_, name=name, id=field_id or name,
                value=value if value is not None else "",
                required=required or None,
                placeholder=placeholder or None, pattern=pattern or None)
