"""Class 10 Hindi chapters, read by OCR because their PDF text layer is a legacy font.

The generator sets questions from the cached OCR text only when the text layer is not Hindi,
the cleaner keeps the book's own lines and drops what the OCR said about pictures, and nothing
here sends a page anywhere (scripts/ocr_hindi_chapter.py does, and it is not run by a test).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import cbse_generate as cg  # noqa: E402
from academicos.corpus import hindi_ocr as ho  # noqa: E402

MARKDOWN = """## काव्य खंड

![Image](data:image/jpeg;base64,/9j/4AAQSkZJRg==)

*हृदय सिंधु मति सीप समाना।
स्वाति सारदा कहहिं सुजाना।*

Reprint 2026-27

---

*यह छवि एक ग्रेस्केल चित्रण है जिसमें कई आकृतियाँ दिखाई दे रही हैं।
यह एक युद्धकालीन चित्रण प्रतीत होता है।*

This image contains a QR code, not readable text.

सूरदास का जन्म सन् 1478 में माना जाता है।
"""


def test_the_cleaner_keeps_the_books_lines_and_drops_the_ocrs_notes_about_pictures():
    lines = ho.clean(MARKDOWN)
    assert lines == ["काव्य खंड", "हृदय सिंधु मति सीप समाना।", "स्वाति सारदा कहहिं सुजाना।",
                     "सूरदास का जन्म सन् 1478 में माना जाता है।"]


def test_the_cleaner_survives_an_empty_page():
    assert ho.clean("") == []
    assert ho.clean("![Image](data:image/png;base64,AAAA)\n") == []


def test_devanagari_share_tells_hindi_from_a_legacy_font():
    assert ho.devanagari_share("तुम हौ अति बड़भागी") > 0.9
    assert ho.devanagari_share("rqe gkS vfr cM+HkkxhA") == 0.0
    assert ho.devanagari_share("") == 0.0


def test_a_cached_chapter_loads_with_its_page_numbers(tmp_path):
    path = ho.cache_path("jhks1", 1, tmp_path)
    path.write_text(json.dumps({"pages": [{"page": 2, "lines": ["दूसरी"]}, {"page": 1, "lines": ["पहली", "दो"]}]},
                               ensure_ascii=False), encoding="utf-8")
    assert ho.load("jhks1", 1, tmp_path) == [(2, "दूसरी"), (1, "पहली"), (1, "दो")]
    assert ho.load("jhks1", 2, tmp_path) is None, "a chapter not read is not an empty one"


def _script():
    spec = importlib.util.spec_from_file_location("gen_chapter_ocr", ROOT / "scripts" / "gen_cbse_chapter.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_chapter_ocr"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("gen_chapter_ocr", None)
    return mod


def _chapter(language, lines, book="jhks1", number=1):
    return cg.Chapter(book_code=book, subject="Hindi", grade=10, language=language, number=number,
                      title="t", pages=tuple((1, l) for l in lines))


def test_a_legacy_text_layer_is_replaced_by_the_cache(tmp_path, monkeypatch):
    mod = _script()
    monkeypatch.setattr(ho, "DEFAULT_CACHE", tmp_path)
    ho.cache_path("jhks1", 1, tmp_path).write_text(
        json.dumps({"pages": [{"page": 3, "lines": ["ऊधौ, तुम हौ अति बड़भागी।"]}]}, ensure_ascii=False),
        encoding="utf-8")
    legacy = _chapter("hi", ["rqe gkS vfr cM+HkkxhA"] * 30)
    out = mod.prefer_ocr(legacy)
    assert out.pages == ((3, "ऊधौ, तुम हौ अति बड़भागी।"),)
    assert ho.devanagari_share(out.text) > 0.9


def test_a_chapter_not_yet_read_stays_as_it_was(tmp_path, monkeypatch):
    mod = _script()
    monkeypatch.setattr(ho, "DEFAULT_CACHE", tmp_path)
    legacy = _chapter("hi", ["rqe gkS vfr cM+HkkxhA"] * 30)
    assert mod.prefer_ocr(legacy) is legacy, "the batch skips it, naming the text as not Hindi"


def test_unicode_hindi_without_a_cache_is_mended_and_with_one_is_read_from_it(tmp_path, monkeypatch):
    mod = _script()
    monkeypatch.setattr(ho, "DEFAULT_CACHE", tmp_path)
    broken = _chapter("hi", ["आज सबका मन नहीीं लिखन ा होगा।"] * 30, book="ihga1")
    assert mod.prefer_ocr(broken).pages[0][1] == "आज सबका मन नहीं लिखना होगा।"
    correct = _chapter("hi", ["आज सबका मन चुआ होगा।"] * 30, book="ihga1")
    assert mod.prefer_ocr(correct).pages == correct.pages
    ho.cache_path("ihga1", 1, tmp_path).write_text(json.dumps({"pages": [{"page": 1, "lines": ["x"]}]}),
                                                   encoding="utf-8")
    assert mod.prefer_ocr(correct).pages == ((1, "x"),)


def test_other_languages_never_use_the_cache(tmp_path, monkeypatch):
    mod = _script()
    monkeypatch.setattr(ho, "DEFAULT_CACHE", tmp_path)
    ho.cache_path("jess1", 1, tmp_path).write_text(json.dumps({"pages": [{"page": 1, "lines": ["x"]}]}),
                                                   encoding="utf-8")
    english = _chapter("en", ["Resources and Development"] * 30, book="jess1")
    assert mod.prefer_ocr(english) is english


def test_repair_devanagari_mends_what_extraction_broke_and_leaves_correct_text_alone():
    from academicos.corpus.hindi_ocr import repair_devanagari as fix
    assert fix("लिखन ा") == "लिखना"
    assert fix("नहीीं") == "नहीं"
    assert fix("उन्हो ोंने") == "उन्होंने"
    assert fix("मिट् ट ी") == "मिट्टी"
    for correct in ("में हम जाते हैं", "तुम हौ अति बड़भागी", "English words only", ""):
        assert fix(correct) == correct
