"""
Reports (V1.7 Parts 20, 21, 22, 23)
=====================================
    document = build_report_document(natal, prediction, interpretation, ...)
    pdf      = render_pdf(document.to_dict())

A report is built as structure and then rendered, never printed and then
wrapped in a PDF. That was V1's approach and it made every question about
layout a question about what the program printed to the console.

This package imports nothing from `engine`; `tests/test_app_boundary.py`
enforces it. Everything here reads finished dictionaries, so the report can
be regenerated from a saved snapshot years later with no engine in memory,
and the golden tests exercise exactly that path.
"""

from .builder import MODE_SECTIONS, build_report_document
from .document import (
    Bullets, Callout, ChartBlock, Heading, KeyValues, PageBreak, Paragraph,
    ReportDocument, SECTION_ORDER, Section, Table,
)
from .html_report import render_html, write_html
from .pdf import (
    PAGE_SIZES, PdfUnsupportedText, layout_document, render_pdf,
    scan_unsupported, write_pdf,
)

__all__ = [
    "Bullets", "Callout", "ChartBlock", "Heading", "KeyValues",
    "MODE_SECTIONS", "PAGE_SIZES", "PageBreak", "Paragraph",
    "PdfUnsupportedText", "ReportDocument", "SECTION_ORDER", "Section",
    "Table", "build_report_document", "layout_document", "render_html",
    "render_pdf", "scan_unsupported", "write_html", "write_pdf",
]
