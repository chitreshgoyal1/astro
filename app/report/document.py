"""
Report document model (V1.7 Part 20)
======================================
A report as structured blocks, not as text.

WHY NOT GENERATE THE PDF FROM THE CONSOLE OUTPUT

    That is what V1 did, and the result was a monospaced transcript in a PDF
    wrapper: no table could be laid out, no chart could be vector, no page
    could break in a sensible place, and the only way to change the report
    was to change what the program printed.

    Here the report is data. A section holds blocks; a block is a paragraph,
    a table, a chart or a callout; and the PDF writer is a renderer for that
    structure. The same document could be rendered to HTML without another
    pass over the engine, and the golden tests compare documents rather than
    comparing the ink.

WHAT A BLOCK MAY CONTAIN

    Finished values. A table cell is a string the builder already formatted;
    a paragraph is a sentence the interpretation layer already produced. No
    block holds a number the renderer is expected to interpret, and none
    holds an engine object. That is what keeps the report from becoming the
    place where astrology quietly gets decided a second time.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional

#: Section identifiers, in the order Part 20 lists them. A report may omit
#: any of them; it may not invent one, because the PDF writer's page
#: furniture and the table of contents are keyed on these.
SECTION_ORDER = (
    "cover",
    "birth_details",
    "executive_summary",
    "charts",
    "planets",
    "strengths",
    "yogas",
    "life_domains",
    "dasha",
    "transit_summary",
    "timing_windows",
    "reliability",
    "methodology",
    "source_appendix",
)


@dataclass(frozen=True)
class Paragraph:
    text: str
    style: str = "body"             # body | lead | note | small
    role: str = ""

    def to_dict(self) -> dict:
        return {"block": "paragraph", "text": self.text, "style": self.style,
                "role": self.role}


@dataclass(frozen=True)
class Heading:
    text: str
    level: int = 2

    def to_dict(self) -> dict:
        return {"block": "heading", "text": self.text, "level": self.level}


@dataclass(frozen=True)
class Table:
    """
    A table of already-formatted strings.

    `widths` are relative column weights, not points: the renderer owns the
    page geometry and the builder should not have to know how wide A4 is.
    """

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    widths: tuple[float, ...] = ()
    caption: str = ""
    align: tuple[str, ...] = ()     # "left" | "right" | "centre" per column
    compact: bool = False

    def to_dict(self) -> dict:
        return {"block": "table", "columns": list(self.columns),
                "rows": [list(r) for r in self.rows],
                "widths": list(self.widths), "caption": self.caption,
                "align": list(self.align), "compact": self.compact}


@dataclass(frozen=True)
class ChartBlock:
    """
    A vector chart, plus the text equivalent of it.

    `scene` is an app.visual.Scene. `description` duplicates the scene's own
    description so that a renderer that cannot draw — or a reader who cannot
    see — still gets the chart's contents (Part 36).
    """

    scene: Any
    caption: str = ""
    description: str = ""
    width: float = 0.0              # points; 0 means "fit the column"

    def to_dict(self) -> dict:
        return {"block": "chart", "caption": self.caption,
                "description": self.description, "width": self.width,
                "scene": self.scene.to_dict() if self.scene else None}


@dataclass(frozen=True)
class KeyValues:
    """Label/value pairs. Used for birth details and the methodology panel."""

    pairs: tuple[tuple[str, str], ...]
    caption: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {"block": "keyvalues",
                "pairs": [list(p) for p in self.pairs],
                "caption": self.caption, "notes": list(self.notes)}


@dataclass(frozen=True)
class Callout:
    """
    A boxed note. Reliability warnings and scope limits, mostly.

    Part 19: warnings are not footnotes. A callout is drawn in the flow of
    the section it belongs to, where it cannot be skipped by a reader who
    does not go looking.
    """

    text: str
    kind: str = "note"              # note | warning | limit
    title: str = ""

    def to_dict(self) -> dict:
        return {"block": "callout", "text": self.text, "kind": self.kind,
                "title": self.title}


@dataclass(frozen=True)
class Bullets:
    items: tuple[str, ...]
    caption: str = ""

    def to_dict(self) -> dict:
        return {"block": "bullets", "items": list(self.items),
                "caption": self.caption}


@dataclass(frozen=True)
class PageBreak:
    """An explicit break. Used sparingly; the renderer breaks on its own."""

    def to_dict(self) -> dict:
        return {"block": "pagebreak"}


@dataclass
class Section:
    """One part of the report."""

    id: str
    title: str
    blocks: list = field(default_factory=list)
    #: Whether this section starts on a fresh page.
    starts_page: bool = True
    subtitle: str = ""

    def add(self, block) -> "Section":
        self.blocks.append(block)
        return self

    def extend(self, blocks) -> "Section":
        self.blocks.extend(b for b in blocks if b is not None)
        return self

    @property
    def is_empty(self) -> bool:
        return not self.blocks

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "subtitle": self.subtitle,
                "starts_page": self.starts_page,
                "blocks": [b.to_dict() for b in self.blocks]}


@dataclass
class ReportDocument:
    """
    A complete report, ready to render.

    `content_hash` covers the blocks and nothing else — not the generation
    time, not the output path — so two runs from identical inputs produce
    the same hash and Part 39's end-to-end test can say so.
    """

    title: str = ""
    subject: str = ""
    mode: str = "detailed"
    language: str = "en"
    sections: list = field(default_factory=list)
    generated: str = ""
    #: Versions of everything that fed this report, recorded for the reader
    #: and for the migration code that may one day meet an old one.
    provenance: dict = field(default_factory=dict)

    def add(self, section: Section) -> "ReportDocument":
        if section.id not in SECTION_ORDER:
            raise ValueError(
                f"'{section.id}' is not a known report section. Known: "
                f"{', '.join(SECTION_ORDER)}.")
        self.sections.append(section)
        return self

    def section(self, id_: str) -> Optional[Section]:
        for section in self.sections:
            if section.id == id_:
                return section
        return None

    def ordered_sections(self) -> list:
        """Sections in the canonical order, regardless of insertion order."""
        index = {name: i for i, name in enumerate(SECTION_ORDER)}
        return sorted(self.sections, key=lambda s: index[s.id])

    def to_dict(self) -> dict:
        return {
            "title": self.title, "subject": self.subject, "mode": self.mode,
            "language": self.language, "generated": self.generated,
            "provenance": self.provenance,
            "sections": [s.to_dict() for s in self.ordered_sections()],
        }

    def content_hash(self) -> str:
        data = self.to_dict()
        data.pop("generated", None)
        payload = json.dumps(data, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
