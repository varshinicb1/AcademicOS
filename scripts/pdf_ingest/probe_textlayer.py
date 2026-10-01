"""Probe NCERT chapter PDFs: is there a usable digital text layer, or is OCR required?

Determines the entire ingestion architecture. Emits one JSON row per PDF.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

CHAPTERS = Path(
    r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters"
)
FULLBOOK = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks")


def probe(path: Path) -> dict:
    row: dict = {
        "path": str(path),
        "name": path.name,
        "bytes": path.stat().st_size,
    }
    try:
        doc = fitz.open(path)
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"open: {exc}"
        return row

    row["pages"] = doc.page_count
    page_count = doc.page_count
    total_chars = 0
    pages_with_text = 0
    image_bytes = 0
    fonts = set()
    per_page = []

    for page in doc:
        text = page.get_text("text")
        total_chars += len(text.strip())
        if len(text.strip()) >= 40:
            pages_with_text += 1
        per_page.append(len(text.strip()))
        for img in page.get_images(full=True):
            try:
                image_bytes += doc.extract_image(img[0])["image"].__len__()
            except Exception:  # noqa: BLE001, S110
                pass
        for font in page.get_fonts(full=True):
            fonts.add(str(font[3]))

    doc.close()

    row["chars"] = total_chars
    row["pages_with_text"] = pages_with_text
    row["text_coverage"] = round(pages_with_text / page_count, 4) if page_count else 0.0
    row["chars_per_page"] = round(total_chars / page_count, 2) if page_count else 0.0
    row["image_bytes"] = image_bytes
    row["n_fonts"] = len(fonts)
    row["has_fonts"] = len(fonts) > 0
    # Scanned: images dominate and almost no text. Hybrid: both present.
    if pages_with_text == 0:
        row["kind"] = "scanned_no_text"
    elif image_bytes > total_chars * 12 and row["chars_per_page"] < 120:
        row["kind"] = "image_heavy_thin_text"
    elif row["chars_per_page"] < 120:
        row["kind"] = "thin_text"
    else:
        row["kind"] = "digital"
    row["min_page_chars"] = min(per_page) if per_page else 0
    return row


def main() -> int:
    targets = sorted(CHAPTERS.rglob("*.pdf"))
    targets += sorted(
        p
        for p in FULLBOOK.rglob("*.pdf")
        if CHAPTERS not in p.parents and p not in targets
    )
    if len(sys.argv) > 1:
        targets = targets[: int(sys.argv[1])]

    rows = []
    for i, path in enumerate(targets, 1):
        rows.append(probe(path))
        if i % 50 == 0:
            print(f"  probed {i}/{len(targets)}", flush=True)

    out = Path(__file__).with_name("textlayer_probe.json")
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")

    from collections import Counter

    kinds = Counter(r.get("kind", "error") for r in rows)
    print(f"\ntotal pdfs: {len(rows)}")
    for kind, n in kinds.most_common():
        sel = [r for r in rows if r.get("kind") == kind]
        avg_cpp = sum(r.get("chars_per_page", 0) for r in sel) / max(len(sel), 1)
        avg_cov = sum(r.get("text_coverage", 0) for r in sel) / max(len(sel), 1)
        print(f"  {kind:26s} {n:5d}  chars/page={avg_cpp:8.1f}  coverage={avg_cov:.3f}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
