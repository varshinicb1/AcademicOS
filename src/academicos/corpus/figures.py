"""Extract the figures a CBSE CBE item refers to, so the item can be served whole.

The problem this solves
-----------------------
194 of the 722 answerable CBE items (26.9%) say something like "in the given
figure" or "study the map". None of them carried a figure. Serving those as
text alone is worse than not serving them: the question as printed is
unanswerable, and a student sees a question that refers to nothing.

512 images are embedded in the 15 source PDFs. They are recoverable.

Why crop the page rather than extract the embedded object
--------------------------------------------------------
`doc.extract_image(xref)` returns the raw stored object, which may be a mask, a
soft mask, a palette image, or oriented by a page transform. `get_pixmap(clip=)`
renders exactly the rectangle the reader sees, with the page's own rotation and
scaling already applied. For a figure that must look right to a student, the
rendered crop is the correct choice.

Why so much of this module is about refusing to attach an image
---------------------------------------------------------------
A wrong diagram is worse than a missing one. A student shown the wrong figure
will answer the wrong question confidently. So attribution is deliberately
conservative:

  * A logo or a bullet is not a figure. Anything below `_MIN_SIDE_PX` on either
    side, or below `_MIN_AREA_PX`, is dropped before attribution.
  * If a page carries several surviving images and the item spans them all, the
    choice is ambiguous. It is recorded as ambiguous and flagged, not guessed.
  * If an item refers to a figure and nothing is found, that is recorded as
    missing. `figureState` always says which of the three happened.

The three states are `attached`, `ambiguous` and `missing`. There is no state
for "probably this one".
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Iterable, Iterator, Sequence

try:                                       # PyMuPDF renamed the module
    import pymupdf as _fitz
except ImportError:                        # pragma: no cover - older installs
    import fitz as _fitz

# A figure is at least this many pixels on a side, and this many square pixels.
# A CBSE running header logo lands around 40x40; the smallest real figure seen
# in these banks (a number line) is about 200x60.
_MIN_SIDE_PX = 90
_MIN_AREA_PX = 9_000

# Render at this resolution. Figures are line art and small text, so 150 dpi is
# legible without making the asset large; a full-page Science diagram lands
# around 60 KB.
_RENDER_DPI = 150

# Phrasings that make an item depend on a figure it does not contain. This list
# is intentionally the same family the CBE parser uses, extended with the ones
# that only appear alongside an actual image ("the given map", "the graph
# shows").
_FIGURE_PHRASES = (
    "given figure", "given diagram", "given graph", "given map", "given picture",
    "given image", "given table", "figure below", "diagram below", "graph below",
    "map below", "table below", "shown below", "given below", "shown in the",
    "observe the", "study the", "look at the", "refer to the", "from the figure",
    "in the figure", "in the diagram", "as shown", "the figure shows",
    "the diagram shows", "the graph shows", "the map shows", "the table shows",
    "the picture shows",
)

_FIGURE_RE = re.compile("|".join(re.escape(p) for p in _FIGURE_PHRASES), re.I)

# A page footer/header rule, a bullet glyph, or a divider. These are wide but
# very short, or square and tiny; the side and area gates cover most, this
# catches a long thin rule that sneaks past the area gate.
_ASPECT_RULE_MAX = 0.06


@dataclasses.dataclass(frozen=True)
class Figure:
    """One rendered figure, positioned on one page of one PDF."""

    page: int                       # 1-based page number
    bbox: tuple[float, float, float, float]
    png: bytes
    width_px: int
    height_px: int

    @property
    def area_px(self) -> int:
        return self.width_px * self.height_px


@dataclasses.dataclass
class Attribution:
    """What was decided for one item, and on what basis."""

    state: str                      # "attached" | "ambiguous" | "missing" | "none"
    figure: Figure | None = None
    candidates: int = 0
    reason: str = ""


def _plausibly_a_figure(info: dict) -> bool:
    """Reject headers, logos, bullets and rules before they can be attributed."""
    w, h = info.get("width", 0), info.get("height", 0)
    x0, y0, x1, y1 = info.get("bbox", (0, 0, 0, 0))
    # Prefer the rendered size, falling back to the stored pixel size.
    pw, ph = abs(x1 - x0), abs(y1 - y0)
    if w < _MIN_SIDE_PX or h < _MIN_SIDE_PX:
        return False
    if w * h < _MIN_AREA_PX:
        return False
    # A near-flat band is a horizontal rule, not a figure.
    if pw > 0 and ph / pw < _ASPECT_RULE_MAX:
        return False
    return True


# --- vector figures -------------------------------------------------------
#
# Many CBSE figures are not images. A geometry diagram -- a labelled triangle,
# a number line, a ray diagram -- is drawn as vector paths, and
# `page.get_image_info()` cannot see it at all. On the real banks this is why
# 39 items referred to a figure whose page appeared to contain no image.
#
# `page.get_drawings()` returns every path. The work is separating a figure
# from everything else that is also vector: the page frame, table rules, the
# answer-lines a question paper prints, and bullet markers.

# A figure is drawn from many segments. A single rule is one or two paths.
_MIN_PATHS = 5

# A cluster this wide AND this tall is the page frame, a full-page table, or
# the ruled answer area -- not a figure.
_MAX_PAGE_FRACTION = 0.92

# Paths closer than this vertically belong to the same figure (PDF points).
_CLUSTER_GAP = 26.0

# A figure must occupy a real area, matching the raster gate's spirit.
_MIN_AREA_PT = 5_000


def _vector_regions(page) -> list[Figure]:
    """Cluster vector paths into candidate figure regions and render them."""
    try:
        drawings = page.get_drawings()
    except Exception:                              # pragma: no cover
        return []
    rects = []
    for d in drawings:
        rect = d.get("rect")
        if rect is None or rect.is_empty or rect.is_infinite:
            continue
        if rect.width <= 1 and rect.height <= 1:   # degenerate point
            continue
        rects.append(rect)
    if len(rects) < _MIN_PATHS:
        return []

    page_rect = page.rect
    page_area = page_rect.width * page_rect.height

    # Cluster by vertical proximity. Sort by top, grow a cluster while the next
    # rect starts before the current cluster's bottom plus the gap.
    rects.sort(key=lambda r: (round(r.y0, 1), round(r.x0, 1)))
    clusters: list[list] = []
    for rect in rects:
        if clusters and rect.y0 <= max(r.y1 for r in clusters[-1]) + _CLUSTER_GAP:
            clusters[-1].append(rect)
        else:
            clusters.append([rect])

    out: list[Figure] = []
    for cluster in clusters:
        if len(cluster) < _MIN_PATHS:
            continue
        region = cluster[0]
        for rect in cluster[1:]:
            region = region | rect                    # bounding union
        if region.width * region.height < _MIN_AREA_PT:
            continue
        if (region.width * region.height) / max(page_area, 1) > _MAX_PAGE_FRACTION:
            continue
        if (region.width >= page_rect.width * 0.9
                and region.height >= page_rect.height * 0.9):
            continue
        # Leave a small margin so labels sitting just outside the paths are
        # included; the figure is being shown to a student, not measured.
        padded = _fitz.Rect(region.x0 - 6, region.y0 - 6,
                            region.x1 + 6, region.y1 + 6) & page_rect
        if padded.is_empty:
            continue
        try:
            pix = page.get_pixmap(clip=padded, dpi=_RENDER_DPI)
            png = pix.tobytes("png")
        except Exception:                          # pragma: no cover
            continue
        out.append(Figure(page=page.number + 1,
                          bbox=(padded.x0, padded.y0, padded.x1, padded.y1),
                          png=png, width_px=pix.width, height_px=pix.height))
    return out


def page_figures(pdf_path: pathlib.Path,
                 *, include_vector: bool = False) -> dict[int, list[Figure]]:
    """Render every plausible figure, keyed by 1-based page number.

    Deterministic: figures on a page are returned top-to-bottom, left-to-right,
    so an ambiguous choice is reproducible.

    `include_vector` is OFF by default, and that is a measured decision, not a
    preference. See `_vector_regions` for what happens when it is turned on:
    naive clustering is too permissive, every page ends up with many candidate
    regions, nearly every item becomes contested, and attribution gets WORSE
    than raster-only (59 attached fall to 2). It is kept in the module because
    the code is sound and the failure is a tuning failure, but it must not be
    enabled until a region can be identified by the item's own text position
    rather than by shape alone.
    """
    out: dict[int, list[Figure]] = {}
    doc = _fitz.open(pdf_path)
    try:
        for index in range(doc.page_count):
            page = doc[index]
            found: list[Figure] = []
            try:
                infos = page.get_image_info()
            except Exception:                     # pragma: no cover - bad page
                infos = []
            for info in infos:
                if not _plausibly_a_figure(info):
                    continue
                rect = _fitz.Rect(info["bbox"])
                if rect.is_empty or rect.is_infinite:
                    continue
                try:
                    pix = page.get_pixmap(clip=rect, dpi=_RENDER_DPI)
                    png = pix.tobytes("png")
                except Exception:                 # pragma: no cover
                    continue
                found.append(Figure(
                    page=index + 1, bbox=tuple(info["bbox"]), png=png,
                    width_px=pix.width, height_px=pix.height,
                ))
            if include_vector:
                found.extend(_vector_regions(page))
            if found:
                found.sort(key=lambda f: (round(f.bbox[1], 1), round(f.bbox[0], 1)))
                # A region found both ways (a raster inside a drawn frame) would
                # otherwise be offered twice and made to look contested.
                deduped: list[Figure] = []
                for fig in found:
                    dup = any(
                        abs(fig.bbox[0] - k.bbox[0]) < 12 and abs(fig.bbox[1] - k.bbox[1]) < 12
                        and abs(fig.bbox[2] - k.bbox[2]) < 12 and abs(fig.bbox[3] - k.bbox[3]) < 12
                        for k in deduped
                    )
                    if not dup:
                        deduped.append(fig)
                out[index + 1] = deduped
    finally:
        doc.close()
    return out


def needs_figure(text: str, has_options: bool = False) -> bool:
    """Does this item's text depend on a figure it does not itself contain?

    `has_options` is accepted and deliberately NOT used to suppress the signal.
    The CBE parser treats an item with options as self-contained; that is wrong
    for an MCQ whose stem says "in the given figure". An option list does not
    supply the figure.
    """
    return bool(_FIGURE_RE.search(text or ""))


def _candidates(pages: Sequence[int],
                figures_by_page: dict[int, list[Figure]]) -> list[Figure]:
    out: list[Figure] = []
    for page in pages:
        out.extend(figures_by_page.get(page, ()))
    return out


def assign_figures(items: Iterable,
                   figures_by_page: dict[int, list[Figure]],
                   ) -> dict[str, Attribution]:
    """Assign figures to items across a whole document, with mutual exclusion.

    Attribution cannot be decided one item at a time. The earlier per-item
    version treated "exactly one image on this page" as a confident 1-to-1
    match, but two figure-referencing items routinely share a page -- and both
    then claimed the same image. Measured on the real banks, that produced
    pairs like `Maths9LK6` and `Maths9CN3`, distinct items with distinct
    figures, both handed the same one at bbox (48, 442, 353, 616). One of them
    was necessarily wrong.

    So the unit of decision is the document, not the item. An image is attached
    only when exactly one item can claim it. An image claimed by two or more
    items is attached to none of them, because a wrong figure teaches wrong
    geometry, and the honest failure is to flag the item rather than guess.

    Returns `item_id -> Attribution`. `none` means the item never referenced a
    figure; `missing` means it did and no image could be assigned.
    """
    items = list(items)
    wants: dict[str, list[Figure]] = {}
    for item in items:
        text = getattr(item, "question", "") or ""
        if not needs_figure(text):
            wants[item.item_id] = []
            continue
        wants[item.item_id] = _candidates(list(getattr(item, "pages", []) or []),
                                          figures_by_page)

    # How many distinct items can claim each image?
    claimants: dict[tuple[int, tuple], int] = {}
    for figures in wants.values():
        for figure in set(figures):
            key = (figure.page, figure.bbox)
            claimants[key] = claimants.get(key, 0) + 1

    results: dict[str, Attribution] = {}
    for item in items:
        figures = wants[item.item_id]
        if not figures:
            text = getattr(item, "question", "") or ""
            results[item.item_id] = (
                Attribution("missing", reason="no image on the item's pages")
                if needs_figure(text) else
                Attribution("none", reason="no figure reference")
            )
            continue
        unique = sorted({f for f in figures}, key=lambda f: (f.page, round(f.bbox[1], 1)))
        uncontested = [f for f in unique if claimants[(f.page, f.bbox)] == 1]
        if len(unique) == 1 and uncontested:
            results[item.item_id] = Attribution(
                "attached", figure=unique[0], candidates=1,
                reason="the only image on the item's pages, claimed by no other item")
        elif len(uncontested) == 1:
            results[item.item_id] = Attribution(
                "attached", figure=uncontested[0], candidates=len(unique),
                reason="one unclaimed image among "
                       f"{len(unique)} on the item's pages")
        else:
            results[item.item_id] = Attribution(
                "ambiguous", candidates=len(unique),
                reason=f"no image is uniquely assignable "
                       f"({len(uncontested)} uncontested of {len(unique)})")
    return results


def extract_document(pdf_path: pathlib.Path,
                     items: Iterable,
                     out_dir: pathlib.Path) -> dict[str, Attribution]:
    """Assign and write figures for `items` from one PDF.

    `items` must expose `item_id`, `pages` and `question` (the `CbeItem` shape).
    Returns `item_id -> Attribution`. Files are written as
    `<out_dir>/<item_id>.png` only when the state is `attached`.
    """
    figures_by_page = page_figures(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = assign_figures(items, figures_by_page)
    for item_id, verdict in results.items():
        target = out_dir / f"{_safe(item_id)}.png"
        if verdict.state == "attached" and verdict.figure is not None:
            target.write_bytes(verdict.figure.png)
        elif target.exists():
            # An item that no longer has an assignable figure must not keep the
            # previous run's image. Measured once at 63 files for 59
            # attachments: the stale file would have been served as this item's
            # figure, which is exactly the wrong-figure failure this module
            # exists to prevent.
            target.unlink()
    return results


_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe(name: str) -> str:
    """A filesystem-safe asset name. Item ids are alphanumeric but be certain."""
    return _SAFE_RE.sub("_", name)[:120]
