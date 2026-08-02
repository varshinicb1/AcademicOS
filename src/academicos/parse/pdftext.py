"""PDF-native parser: PyMuPDF text extraction with block layout and reading order.

Fast path for born-digital CBSE PDFs. Classifies pages as text/scan/mixed and
attaches bbox for every block so downstream layout/table modules can work in
relative page coordinates.
"""
from __future__ import annotations

import logging
from pathlib import Path

from ..models.document import Page, ParseResult, Block
from ..models.enums import BlockKind, PageKind
from .base import ParserProvider

log = logging.getLogger(__name__)

_NON_TEXT_THRESHOLD = 0.85
_BLANK_THRESHOLD = 20


class PdfTextParser(ParserProvider):
    name = "pdf_native"

    def parse(self, document_path: Path, document_id: str, max_pages: int = 500) -> ParseResult:
        import fitz  # pymupdf

        res = ParseResult(document_id=document_id, method=self.name)
        with fitz.open(document_path) as doc:
            for i in range(min(doc.page_count, max_pages)):
                page = doc[i]
                text = page.get_text("text").strip()
                blocks: list[Block] = []
                kind = PageKind.TEXT

                if len(text) < _BLANK_THRESHOLD:
                    kind = PageKind.BLANK
                else:
                    char_count = sum(len(b[4]) for b in page.get_text("blocks"))
                    drawn_area = page.rect.width * page.rect.height
                    raster = page.get_text("dict")

                    # rough scan heuristic: if most spans come from rawdict as image blocks
                    images = page.get_images(full=True)
                    text_chars = char_count
                    if images and text_chars == 0:
                        kind = PageKind.SCAN
                    elif images and text_chars < 40:
                        kind = PageKind.MIXED

                    order = 0
                    for b in page.get_text("blocks"):
                        x0, y0, x1, y1, btext, bno, btype = b[:7]
                        if not btext.strip():
                            continue
                        blocks.append(Block(
                            kind=self._kind(btype, btext, order, blocks),
                            text=btext.strip(),
                            bbox={"x0": x0 / page.rect.width, "y0": y0 / page.rect.height,
                                  "x1": x1 / page.rect.width, "y1": y1 / page.rect.height},
                            order=order,
                            metadata={"fontsize_estimate": self._fontsize(page, bno)},
                        ))
                        order += 1

                page_model = Page(
                    page_no=i + 1,
                    kind=kind,
                    text=text,
                    blocks=blocks,
                    quality=1.0 if kind != PageKind.SCAN else 0.3,
                )
                res.pages.append(page_model)

        res.confidence = min(1.0, 0.9 if any(p.kind != PageKind.SCAN for p in res.pages) else 0.4)
        if not res.pages:
            res.warnings.append("no pages parsed")
        return res

    @staticmethod
    def _kind(btype: int, text: str, order: int, prev: list[Block]) -> BlockKind:
        if btype == 1:
            return BlockKind.IMAGE_ONLY
        low = text.strip().lower()
        if order == 0 and (len(low) < 120 and (low.endswith((")", "]", "»")) or " " not in low.strip())):
            return BlockKind.HEADING
        return BlockKind.PARAGRAPH

    @staticmethod
    def _fontsize(page, bno: int) -> float:
        try:
            d = page.get_text("dict")
            for b in d.get("blocks", []):
                if b.get("number") == bno or b.get("bbox", [0])[0] == bno:
                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            return round(s.get("size", 0), 1)
        except Exception:
            pass
        return 0.0
