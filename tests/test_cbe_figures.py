"""Tests for figure extraction from the CBSE CBE item banks.

The behaviour that matters most here is a REFUSAL. An image that two items can
both claim must be attached to neither, because a wrong diagram teaches wrong
geometry. The regression test for that is
`test_two_items_sharing_one_image_get_none`.
"""
from __future__ import annotations

import dataclasses
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import figures as figmod  # noqa: E402

CBE_DIR = REPO / "academicos-data" / "corpus" / "cbse-cbe"


def _fig(page: int, y: float, *, x: float = 48.0, w: int = 400, h: int = 300):
    return figmod.Figure(page=page, bbox=(x, y, x + 200, y + 150),
                         png=b"\x89PNG-fake", width_px=w, height_px=h)


def _item(item_id: str, question: str, pages):
    @dataclasses.dataclass
    class _I:
        item_id: str
        question: str
        pages: list

    return _I(item_id=item_id, question=question, pages=list(pages))


# --- needs_figure ---------------------------------------------------------

@pytest.mark.parametrize("text", [
    "In the given figure, find the value of y.",
    "Study the map and answer the questions that follow.",
    "The graph shows the number of students in each class.",
    "Observe the diagram and label the parts.",
    "Which of the following is shown in the table below?",
])
def test_figure_language_is_detected(text):
    assert figmod.needs_figure(text)


@pytest.mark.parametrize("text", [
    "Solve for x: 2x + 3 = 11.",
    "Name the largest planet in the solar system.",
    "Write the chemical formula for common salt.",
    "",
])
def test_plain_text_is_not_flagged(text):
    assert not figmod.needs_figure(text)


def test_options_do_not_suppress_the_figure_signal():
    """An option list does not supply the figure an MCQ's stem refers to.

    The CBE parser suppresses the signal when an item has options
    (`needs_figure = any(...) and not options`). For a stem that says "in the
    given figure", that is wrong, and this is the guard.
    """
    assert figmod.needs_figure("In the given figure, AB is a diameter.",
                               has_options=True)


# --- the raster gates -----------------------------------------------------

def test_small_images_are_rejected():
    """A 40x40 running-header logo is not a figure."""
    assert not figmod._plausibly_a_figure(
        {"width": 40, "height": 40, "bbox": (10, 10, 50, 50)})


def test_thin_rules_are_rejected():
    """A ruled answer line is wide and nearly flat."""
    assert not figmod._plausibly_a_figure(
        {"width": 900, "height": 8, "bbox": (40, 700, 540, 702)})


def test_a_real_figure_is_accepted():
    assert figmod._plausibly_a_figure(
        {"width": 400, "height": 300, "bbox": (48, 200, 300, 425)})


# --- attribution ----------------------------------------------------------

def test_a_lone_item_with_a_lone_image_is_attached():
    items = [_item("A1", "In the given figure find x", [7])]
    got = figmod.assign_figures(items, {7: [_fig(7, 200)]})
    assert got["A1"].state == "attached"
    assert got["A1"].figure is not None


def test_an_item_with_no_image_is_missing():
    items = [_item("A1", "In the given figure find x", [7])]
    got = figmod.assign_figures(items, {})
    assert got["A1"].state == "missing"


def test_an_item_not_mentioning_a_figure_is_none():
    items = [_item("A1", "Solve 2x + 3 = 11", [7])]
    got = figmod.assign_figures(items, {7: [_fig(7, 200)]})
    assert got["A1"].state == "none"


def test_two_items_sharing_one_image_get_none():
    """The regression this module exists for.

    Measured on the real banks: `Maths9LK6` ("in the given figure angle ABD is
    an exterior angle") and `Maths9CN3` ("in the given figure triangle ACB is
    congruent to triangle DFE") are distinct items with distinct figures on the
    same page. A per-item rule sees "one image on this page" twice and hands
    both items the same picture. One of them is then wrong, and a student
    answers the wrong question confidently.
    """
    shared = _fig(12, 300)
    items = [
        _item("LK6", "In the given figure angle ABD is an exterior angle", [12]),
        _item("CN3", "In the given figure triangle ACB is congruent to DFE", [12]),
    ]
    got = figmod.assign_figures(items, {12: [shared]})
    assert got["LK6"].state == "ambiguous"
    assert got["CN3"].state == "ambiguous"
    assert got["LK6"].figure is None
    assert got["CN3"].figure is None


def test_an_uncontested_image_is_still_attached_among_several():
    """Mutual exclusion must not collapse to 'any ambiguity wins'.

    A page holds two images. Both items on the page can claim the first, only
    one can claim the second. So the item that has a single uncontested
    candidate keeps it, and the other is flagged. Without this branch the rule
    would throw away every figure on a shared page.

    The images must sit on DIFFERENT pages for this to arise: candidates are
    "every image on the item's pages", so two items sharing a page both claim
    everything on it.
    """
    shared = _fig(20, 100)
    beyond = _fig(21, 100)
    items = [
        _item("BOTH", "In the given figure find x", [20, 21]),
        _item("ONE", "Study the diagram and answer", [20]),
    ]
    got = figmod.assign_figures(items, {20: [shared], 21: [beyond]})
    assert got["BOTH"].state == "attached"
    assert got["BOTH"].figure is beyond
    assert got["ONE"].state == "ambiguous"
    assert got["ONE"].figure is None


# --- stale assets ---------------------------------------------------------

def test_a_lost_figure_removes_its_stale_png(tmp_path, monkeypatch):
    """An item that no longer has a figure must not keep the old image.

    Measured once at 63 files for 59 attachments; the stale file would have
    been served as that item's figure -- the exact wrong-figure failure this
    module prevents.
    """
    stale = tmp_path / "A1.png"
    stale.write_bytes(b"old")

    def fake_page_figures(_pdf, **_kw):
        return {}

    monkeypatch.setattr(figmod, "page_figures", fake_page_figures)
    items = [_item("A1", "In the given figure find x", [1])]
    got = figmod.extract_document(pathlib.Path("nonexistent.pdf"), items, tmp_path)
    assert got["A1"].state == "missing"
    assert not stale.exists()


# --- build integration ----------------------------------------------------

def test_asset_slot_routes_by_the_word_the_item_uses():
    """A map is not a diagram; the record has four slots for a reason."""
    from importlib import import_module
    mod = None
    import types
    for path in (REPO / "scripts",):
        sys.path.insert(0, str(path))
    mod = import_module("build_cbe_bank")
    assert mod._asset_slot("Study the map below") == "mapAssetId"
    assert mod._asset_slot("The graph shows") == "graphAssetId"
    assert mod._asset_slot("shown in the table") == "tableAssetId"
    assert mod._asset_slot("In the given figure") == "diagramAssetId"
    assert mod._asset_slot("something else") == "diagramAssetId"


# --- position-based attribution ------------------------------------------

def test_text_inside_finds_only_words_centred_in_the_rect():
    words = [
        (0, 0, 10, 10, "inside", 0, 0, 0),
        (100, 100, 110, 110, "outside", 0, 0, 0),
    ]
    got = figmod._text_inside(figmod._fitz.Rect(0, 0, 50, 50), words)
    assert "inside" in got
    assert "outside" not in got


def test_the_item_metadata_table_is_rejected_as_furniture():
    """It heads every CBE item and sits beside it, so proximity prefers it.

    Verified by eye as a WRONG figure before this filter existed: the extracted
    asset was the "Subject | Class | Question reference/Filename" table, and it
    slipped through the character gate at ~55 characters against a limit of 60.
    """
    table = "Subject Class Question reference/Filename Maths 9 Maths9NK6"
    assert figmod._is_furniture(table, "Maths9NK6")


def test_a_region_naming_the_item_is_rejected():
    assert figmod._is_furniture("Maths9NK6", "Maths9NK6")


def test_a_figure_label_is_not_furniture():
    """Axis labels are short and name nothing."""
    assert not figmod._is_furniture("y 10 Line 2 Line 1 5 -5 -10 x", "Maths9NK6")
    assert not figmod._is_furniture("P (-3, 2) Q (2, 7) x y", "Maths9NK6")


def test_the_label_character_limit_stays_below_the_metadata_table():
    """The limit must not creep back above the table it was lowered to exclude."""
    assert figmod._MAX_LABEL_CHARS < 55


class _FakePage:
    """A page whose only behaviour is `search_for`, which is all `_find_anchor` uses."""

    def __init__(self, hits):
        self._hits = hits
        self.searched: list[str] = []

    def search_for(self, token):
        self.searched.append(token)
        return self._hits


def test_find_anchor_returns_none_when_nothing_on_the_page_matches():
    """A probe that is absent must yield None, not a wrong anchor.

    This previously asserted `_find_anchor.__doc__ is not None` -- it checked
    that a docstring existed and never exercised the behaviour its own name
    described. A test whose body does not match its name is worse than a missing
    test, because it reports green for a function that could be entirely broken.
    """
    page = _FakePage([])
    assert figmod._find_anchor(page, "in the given figure find the value of x") is None
    assert page.searched, "the probe should have been attempted"


def test_find_anchor_returns_the_first_hit_and_probes_the_longest_token_first():
    """The longest word is the most distinctive, so it is tried first.

    A single token also survives the line-breaks that break a phrase search.
    """
    hit = figmod._fitz.Rect(10, 10, 80, 20)
    page = _FakePage([hit])
    got = figmod._find_anchor(page, "in the given figure find the value of photosynthesis")
    assert got == hit
    assert page.searched[0] == "photosynthesis", (
        f"probed {page.searched[0]!r} first; the longest token should be first"
    )


def test_find_anchor_falls_through_to_shorter_tokens():
    """If the longest token is not on the page, a shorter one is tried."""
    hit = figmod._fitz.Rect(0, 0, 5, 5)

    class _Picky(_FakePage):
        def search_for(self, token):
            self.searched.append(token)
            return [hit] if token == "triangle" else []

    page = _Picky([])
    assert figmod._find_anchor(page, "the photosynthesis triangle") == hit
    assert page.searched[0] == "photosynthesis"
    assert "triangle" in page.searched


@pytest.mark.skipif(not any(CBE_DIR.glob("*.pdf")),
                    reason="CBSE CBE source PDFs not present (not committed)")
def test_position_beats_shape_on_the_real_banks():
    """The measurement that justified switching methods.

    Shape-based clustering attached 59 of 124 figure-referencing items; taking
    the region nearest the item's own text attaches 95. This asserts a floor
    well below the measured figure so it catches a regression without being
    brittle to a page-count change.
    """
    from academicos.corpus import cbse_cbe
    import shutil
    import tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="figpos-"))
    try:
        attached = 0
        need = 0
        # Mathematics, not whichever files sort first: the English banks hold
        # only a handful of figure-dependent items between them, so an
        # alphabetical slice tests almost nothing.
        pdfs = sorted(p for p in CBE_DIR.glob("*.pdf") if "Maths" in p.name)
        for pdf in pdfs:
            items = cbse_cbe.parse_item_bank(pdf)
            got = figmod.attribute_by_position(pdf, items, tmp)
            for item in items:
                if figmod.needs_figure(item.question or ""):
                    need += 1
                    if got[item.item_id].state == "attached":
                        attached += 1
        assert need >= 30, f"expected figure-dependent items, found {need}"
        assert attached / need >= 0.55, (
            f"position-based attribution attached {attached}/{need}; "
            "it measured 77% across all 15 documents -- if this drops, the "
            "proximity rule or the furniture filter has regressed"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.mark.skipif(not any(CBE_DIR.glob("*.pdf")),
                    reason="CBSE CBE source PDFs not present (not committed)")
def test_no_metadata_table_is_served_as_a_figure():
    """The specific visual defect, asserted at the level of the pipeline."""
    from academicos.corpus import cbse_cbe
    import tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="figfurn-"))
    try:
        pdf = next(p for p in CBE_DIR.glob("*.pdf") if "Maths---Class-9" in p.name)
        items = cbse_cbe.parse_item_bank(pdf)
        got = figmod.attribute_by_position(pdf, items, tmp)
        by_id = {i.item_id: i for i in items}

        # One document handle for the whole check. An earlier version called
        # `_fitz.open(pdf)` inside the loop and never closed it, leaking a file
        # handle per attached figure. That starved unrelated tests of handles
        # and made `tests/test_smoke.py::test_end_to_end` fail intermittently --
        # which is how a test bug in one file shows up as a flaky failure in
        # another, and is the reason that flake was investigated rather than
        # re-run until green.
        doc = figmod._fitz.open(pdf)
        try:
            for item_id, verdict in got.items():
                if verdict.state != "attached":
                    continue
                item = by_id.get(item_id)
                if item is None:
                    continue
                text = figmod._text_inside(
                    figmod._fitz.Rect(verdict.figure.bbox),
                    figmod._page_words(doc[verdict.figure.page - 1]))
                assert not figmod._is_furniture(text, item_id), (
                    f"{item_id} was attached to what looks like page furniture: {text!r}"
                )
        finally:
            doc.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

@pytest.mark.skipif(not any(CBE_DIR.glob("*.pdf")),
                    reason="CBSE CBE source PDFs not present (not committed)")
def test_real_figures_are_extracted_and_contested_ones_withheld(tmp_path):
    """The floors that make this work real rather than theoretical."""
    from academicos.corpus import cbse_cbe

    pdf = next(p for p in CBE_DIR.glob("*.pdf") if "Maths-Class-6" in p.name)
    items = cbse_cbe.parse_item_bank(pdf)
    # `tmp_path`, not a hardcoded path. This wrote to `C:/Temp/figcheck`, which
    # on Linux and macOS becomes a RELATIVE directory literally named `C:` in
    # the working tree, and on Windows depends on `C:\Temp` already existing.
    # The only test that verifies real figure extraction was therefore the one
    # test that could not run anywhere but this workstation.
    got = figmod.extract_document(pdf, items, tmp_path)

    assert len(items) > 50, "the Maths 6 bank should parse to ~107 items"
    attached = sum(1 for v in got.values() if v.state == "attached")
    assert attached >= 3, (
        f"expected at least 3 figures in Maths Class 6, got {attached}"
    )
    # Every attached figure must be a real PNG of a usable size.
    for verdict in got.values():
        if verdict.state == "attached":
            assert verdict.figure is not None
            assert verdict.figure.png[:4] == b"\x89PNG"
            assert verdict.figure.width_px >= figmod._MIN_SIDE_PX


@pytest.mark.skipif(not any(CBE_DIR.glob("*.pdf")),
                    reason="CBSE CBE source PDFs not present (not committed)")
def test_vector_extraction_stays_off_because_it_measured_worse():
    """`include_vector` is off by default on evidence, not taste.

    Turning it on produced so many candidate regions that attribution got
    worse: attached fell from 59 to 2. If someone enables it without fixing the
    region detection first, this fails and points at why.
    """
    import inspect
    sig = inspect.signature(figmod.page_figures)
    assert sig.parameters["include_vector"].default is False
