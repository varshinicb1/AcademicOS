"""Document ingestion tests: checksums, SourceRegistry ledger, discovery,
quality gates, document classification and the end-to-end IngestionPipeline.

SQLite-backed pieces use tmp_path; corpus fixtures are tiny born-digital PDFs
built with PyMuPDF (no real corpus, no network). Verified against
src/academicos/ingest/ + src/academicos/storage/registry.py.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.ingest.checksum import file_checksum, verify_digest
from academicos.ingest.classify import classify_from_name, classify_from_text
from academicos.ingest.discovery import (
    Discovery,
    SourceFile,
    infer_metadata,
)
from academicos.ingest.pipeline import IngestionPipeline, safe_name
from academicos.ingest.quality import validate_file
from academicos.models.enums import DocType
from academicos.storage.base import LocalStore
from academicos.storage.registry import SourceRegistry


# ------------------------------------------------------------- fixtures -----

def _pdf(tmp_path: Path, name: str, lines: list[str]) -> Path:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    for i, line in enumerate(lines):
        page.insert_text((72, 72 + 20 * i), line, fontsize=10)
    p = tmp_path / name
    doc.save(p)
    doc.close()
    return p


@pytest.fixture
def corpus_root(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    return root


@pytest.fixture
def qp_pdf(corpus_root):
    return _pdf(corpus_root, "XII_Physics_QP_2025.pdf", [
        "Sample Question Paper 2025",
        "Time allowed: 3 hours  Maximum marks: 80",
        "General Instructions: This question paper comprises sections A and B.",
        "Section A  1. What is photosynthesis? (2 marks)",
        "2. State Newton's second law of motion. (2 marks)",
    ])


@pytest.fixture
def ms_pdf(corpus_root):
    return _pdf(corpus_root, "XII_Physics_MS_2025.pdf", [
        "Marking Scheme 2025",
        "Time allowed: 3 hours  Maximum marks: 80",
        "1. Photosynthesis (2 marks) Conversion of light to chemical energy.",
    ])


# ------------------------------------------------------------- checksum -----

def test_file_checksum_matches_stdlib(tmp_path):
    p = tmp_path / "blob.bin"
    p.write_bytes(b"academicos checksum test" * 1000)
    sha256, sha512 = file_checksum(p)
    assert sha256 == hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha512 == hashlib.sha512(p.read_bytes()).hexdigest()
    assert len(sha256) == 64 and len(sha512) == 128


def test_file_checksum_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        file_checksum(tmp_path / "nope.pdf")


def test_verify_digest_true_on_match(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(b"content")
    sha, _ = file_checksum(p)
    assert verify_digest(p, sha) is True


def test_verify_digest_false_on_mismatch(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(b"content")
    assert verify_digest(p, "0" * 64) is False


def test_verify_digest_false_on_missing_file(tmp_path):
    assert verify_digest(tmp_path / "missing.pdf", "0" * 64) is False


# ------------------------------------------------------------- registry -----

def test_register_and_get_roundtrip(tmp_path):
    reg = SourceRegistry(tmp_path / "reg" / "registry.sqlite")
    reg.register("src:abc", file_key="question_paper/src_abc.pdf",
                 sha256="s256", sha512="s512", size_bytes=123,
                 doc_type="question_paper", title="QP 2025", status="registered")
    row = reg.get("src:abc")
    assert row is not None
    assert row["source_id"] == "src:abc"
    assert row["file_key"] == "question_paper/src_abc.pdf"
    assert row["sha256"] == "s256"
    assert row["sha512"] == "s512"
    assert row["size_bytes"] == 123
    assert row["doc_type"] == "question_paper"
    assert row["title"] == "QP 2025"
    assert row["status"] == "registered"
    assert row["registered_at"]
    reg.close()


def test_register_same_id_is_idempotent_no_duplicate(tmp_path):
    reg = SourceRegistry(tmp_path / "reg.sqlite")
    reg.register("src:x", file_key="k1", size_bytes=10)
    reg.register("src:x", file_key="k2", size_bytes=99)
    assert reg.count() == 1
    row = reg.get("src:x")
    assert row["file_key"] == "k2"
    # on-conflict only rewrites file_key + status; other columns keep first value
    assert row["size_bytes"] == 10
    assert row["status"] == "registered"
    reg.close()


def test_register_resets_status_to_registered_on_reegister(tmp_path):
    reg = SourceRegistry(tmp_path / "reg2.sqlite")
    reg.register("src:y", file_key="k1", status="parsed")
    assert reg.get("src:y")["status"] == "parsed"
    reg.register("src:y", file_key="k1", status="registered")
    assert reg.get("src:y")["status"] == "registered"
    reg.close()


def test_changed_content_maps_to_new_content_addressed_id(tmp_path):
    reg = SourceRegistry(tmp_path / "reg3.sqlite")
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"version one")
    b.write_bytes(b"version two")
    sha_a, sha512_a = file_checksum(a)
    sha_b, sha512_b = file_checksum(b)
    reg.register(f"src:{sha512_a[:24]}", file_key="a.pdf")
    reg.register(f"src:{sha512_b[:24]}", file_key="b.pdf")
    assert reg.count() == 2
    assert reg.get(f"src:{sha512_a[:24]}")["file_key"] == "a.pdf"
    assert reg.get(f"src:{sha512_b[:24]}")["file_key"] == "b.pdf"
    reg.close()


def test_meta_dict_serialized_to_json(tmp_path):
    reg = SourceRegistry(tmp_path / "reg4.sqlite")
    reg.register("src:m", file_key="k", meta={"probe": [1, 2]})
    row = reg.get("src:m")
    assert '"probe"' in row["meta"] and "1" in row["meta"]
    reg.close()


def test_update_and_listing(tmp_path):
    reg = SourceRegistry(tmp_path / "reg5.sqlite")
    reg.register("src:1", file_key="a")
    reg.register("src:2", file_key="b")
    reg.update("src:1", status="parsed", quality_score=0.9)
    row = reg.get("src:1")
    assert row["status"] == "parsed" and row["quality_score"] == 0.9
    assert {r["source_id"] for r in reg.all()} == {"src:1", "src:2"}
    assert len(reg.by_status("parsed")) == 1
    assert reg.count() == 2
    reg.close()


# ------------------------------------------------------------- discovery ----

def test_discovery_walk_finds_and_annotates(corpus_root, qp_pdf):
    d = Discovery(corpus_root)
    files = d.walk()
    assert len(files) == 1
    sf = files[0]
    assert sf.path == qp_pdf
    assert sf.rel_key == qp_pdf.name
    assert sf.size_bytes == qp_pdf.stat().st_size
    assert len(sf.sha256) == 64 and len(sf.sha512) == 128
    assert sf.source_id.startswith("src:")
    assert len(sf.source_id) == len("src:") + 24


def test_discovery_ignores_unsupported_and_hidden(tmp_path):
    (tmp_path / "note.txt").write_text("ok")
    (tmp_path / "image.jpg").write_bytes(b"jpg")
    (tmp_path / "script.py").write_text("x")
    (tmp_path / ".hidden.pdf").write_bytes(b"%PDF hidden")
    (tmp_path / "~$lock.docx").write_bytes(b"lock")
    (tmp_path / "abc").write_bytes(b"short name")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "nested.pdf").write_bytes(b"%PDF nested")
    files = Discovery(tmp_path).walk()
    names = {f.path.name for f in files}
    assert names == {"note.txt", "image.jpg", "nested.pdf"}


def test_discovery_hints_from_filename():
    assert Discovery._hints(Path("marking scheme 2025.pdf")) == ["marking_scheme", "marking_scheme"]
    assert Discovery._hints(Path("model answer.pdf")) == ["model_answer"]
    assert Discovery._hints(Path("circular no 12.pdf")) == ["circular"]
    assert Discovery._hints(Path("random.pdf")) == []


def test_classify_hints():
    assert Discovery.classify_hints(["marking_scheme"]) is DocType.MARKING_SCHEME
    assert Discovery.classify_hints(["question_paper"]) is DocType.QUESTION_PAPER
    assert Discovery.classify_hints(["bogus_tag", "sample_paper"]) is DocType.SAMPLE_PAPER
    assert Discovery.classify_hints(["bogus_tag"]) is DocType.UNKNOWN


def test_dedupe_marks_second_copy(tmp_path):
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"%PDF same content")
    b.write_bytes(b"%PDF same content")
    files = Discovery(tmp_path).walk()
    assert len(files) == 2
    deduped = Discovery(tmp_path).dedupe(files)
    canonical = deduped[0]
    dup = deduped[1]
    assert dup.dedupe_of == canonical.source_id
    assert deduped[0].dedupe_of is None or deduped[0].dedupe_of == ""


def test_infer_metadata_sets_year_and_doc_type(tmp_path):
    sf = SourceFile(path=tmp_path / "physics2026.pdf", rel_key="physics2026.pdf",
                    size_bytes=1, hints=["question_paper"])
    infer_metadata(sf)
    assert sf.academic_year == "2026"
    assert sf.doc_type is DocType.QUESTION_PAPER


# ------------------------------------------------------------- quality ------

def test_validate_rejects_trivially_small(tmp_path):
    p = tmp_path / "tiny.pdf"
    p.write_bytes(b"%PDF")
    sf = SourceFile(path=p, rel_key="tiny.pdf", size_bytes=4)
    ok, problems = validate_file(sf)
    assert ok is False
    assert any("trivially small" in x for x in problems)


def test_validate_rejects_pdf_under_min_bytes(tmp_path):
    p = tmp_path / "small.pdf"
    p.write_bytes(b"%PDF-1.7" + b"0" * 100)
    sf = SourceFile(path=p, rel_key="small.pdf", size_bytes=p.stat().st_size)
    ok, problems = validate_file(sf, min_pdf_bytes=4096)
    assert ok is False
    assert any("pdf under" in x for x in problems)


def test_validate_rejects_html_error_page_masquerading_as_pdf(tmp_path):
    p = tmp_path / "error.pdf"
    p.write_bytes(b"<html><title>500 Internal Server Error</title></html>")
    sf = SourceFile(path=p, rel_key="error.pdf", size_bytes=p.stat().st_size)
    ok, problems = validate_file(sf, min_pdf_bytes=16)
    assert ok is False
    assert any("HTML error page" in x for x in problems)


def test_validate_rejects_missing_pdf_magic(tmp_path):
    p = tmp_path / "fake.pdf"
    p.write_bytes(b"NOT A PDF AT ALL BUT LONG ENOUGH TO PASS SIZE GATES" * 10)
    sf = SourceFile(path=p, rel_key="fake.pdf", size_bytes=p.stat().st_size)
    ok, problems = validate_file(sf, min_pdf_bytes=16)
    assert ok is False
    assert any("magic" in x for x in problems)


def test_validate_rejects_corrupt_zip(tmp_path):
    p = tmp_path / "bad.zip"
    p.write_bytes(b"PK\x03\x04" + b"garbage" * 50)
    sf = SourceFile(path=p, rel_key="bad.zip", size_bytes=p.stat().st_size)
    ok, problems = validate_file(sf)
    assert ok is False
    assert any("zip" in x.lower() for x in problems)


def test_validate_accepts_tiny_born_digital_pdf(tmp_path, qp_pdf):
    sf = SourceFile(path=qp_pdf, rel_key=qp_pdf.name, size_bytes=qp_pdf.stat().st_size)
    ok, problems = validate_file(sf, min_pdf_bytes=256)
    assert ok is True, problems


# ------------------------------------------------------------- classify -----

@pytest.mark.parametrize("name,expected", [
    ("Physics marking scheme 2025.pdf", DocType.MARKING_SCHEME),
    ("Physics answer key.pdf", DocType.MARKING_SCHEME),
    ("XII_Physics_QP_2025.pdf", DocType.QUESTION_PAPER),
    ("questionpaper 2025.pdf", DocType.QUESTION_PAPER),
    ("model answer biology.pdf", DocType.MODEL_ANSWER),
    ("sample paper maths.pdf", DocType.SAMPLE_PAPER),
    ("curriculum science.pdf", DocType.CURRICULUM),
    ("syllabus 2026.pdf", DocType.SYLLABUS),
    ("question bank physics.pdf", DocType.QUESTION_BANK),
    ("circular no 4.pdf", DocType.CIRCULAR),
    ("bye law 2023.pdf", DocType.BYE_LAW),
    ("datesheet term1.pdf", DocType.DATESHEET),
    ("notification of exam.pdf", DocType.NOTIFICATION),
    ("guidelines for practicals.pdf", DocType.GUIDELINE),
    ("reference material maths.pdf", DocType.REFERENCE_MATERIAL),
    ("screenshot_2025.pdf", DocType.UNKNOWN),
])
def test_classify_from_name_rules(tmp_path, name, expected):
    sf = SourceFile(path=tmp_path / name, rel_key=name, size_bytes=1)
    assert classify_from_name(sf) is expected


def test_classify_from_text_name_wins(tmp_path):
    sf = SourceFile(path=tmp_path / "marking scheme physics.pdf", rel_key="x", size_bytes=1)
    assert classify_from_text(sf, "garbage text") is DocType.MARKING_SCHEME


def test_classify_from_text_question_paper_by_keywords(tmp_path):
    sf = SourceFile(path=tmp_path / "mystery.pdf", rel_key="x", size_bytes=1)
    text = ("Time allowed: 3 hours. Maximum marks: 80. General instructions. "
            "This question paper comprises five sections.")
    assert classify_from_text(sf, text) is DocType.QUESTION_PAPER


def test_classify_from_text_marking_scheme_needs_both(tmp_path):
    sf = SourceFile(path=tmp_path / "mystery.pdf", rel_key="x", size_bytes=1)
    text = ("Marking scheme for the paper. Time allowed: 3 hours. Maximum marks: 80. "
            "Section A Section B")
    assert classify_from_text(sf, text) is DocType.MARKING_SCHEME


def test_classify_from_text_model_answer(tmp_path):
    sf = SourceFile(path=tmp_path / "mystery.pdf", rel_key="x", size_bytes=1)
    assert classify_from_text(sf, "model answers for biology") is DocType.MODEL_ANSWER


def test_classify_from_text_curriculum_requires_learning_outcomes(tmp_path):
    sf = SourceFile(path=tmp_path / "mystery.pdf", rel_key="x", size_bytes=1)
    assert classify_from_text(sf, "curriculum with course content listed") is DocType.CURRICULUM
    assert classify_from_text(sf, "curriculum but nothing else") is DocType.UNKNOWN


# ------------------------------------------------------------- pipeline -----

def test_pipeline_registers_and_stores(tmp_path, qp_pdf, ms_pdf):
    reg = SourceRegistry(tmp_path / "reg" / "r.sqlite")
    store = LocalStore(tmp_path / "docs")
    pipe = IngestionPipeline(qp_pdf.parent, reg, store)
    res = pipe.run(min_pdf_bytes=256)
    assert len(res.accepted) == 2
    assert res.rejected == []
    for sf in res.accepted:
        row = reg.get(sf.source_id)
        assert row is not None
        assert row["sha512"] == sf.sha512
        assert store.exists(row["file_key"])
    assert reg.count() == 2
    # registry's doc_type was persisted as the enum value string
    types = {reg.get(sf.source_id)["doc_type"] for sf in res.accepted}
    assert types == {"question_paper", "marking_scheme"}
    reg.close()


def test_pipeline_rerun_detects_duplicates(tmp_path, qp_pdf):
    reg = SourceRegistry(tmp_path / "reg" / "r.sqlite")
    store = LocalStore(tmp_path / "docs")
    pipe = IngestionPipeline(qp_pdf.parent, reg, store)
    first = pipe.run(min_pdf_bytes=256)
    assert len(first.accepted) == 1
    second = pipe.run(min_pdf_bytes=256)
    assert second.accepted == []
    assert len(second.duplicates) == 1
    assert reg.count() == 1
    reg.close()


def test_pipeline_registers_modified_file_as_new_source(tmp_path, qp_pdf):
    reg = SourceRegistry(tmp_path / "reg" / "r.sqlite")
    store = LocalStore(tmp_path / "docs")
    pipe = IngestionPipeline(qp_pdf.parent, reg, store)
    pipe.run(min_pdf_bytes=256)
    before = {sf.source_id for sf in pipe.run(min_pdf_bytes=256).accepted}
    assert len(before) == 0
    # mutate content in place -> checksum changes -> content-addressed id changes
    import fitz

    doc = fitz.open(qp_pdf)
    page = doc[0]
    page.insert_text((72, 400), "ADDED LINE CHANGES CHECKSUM", fontsize=10)
    doc.saveIncr()
    doc.close()
    after = pipe.run(min_pdf_bytes=256)
    assert len(after.accepted) == 1
    new_id = after.accepted[0].source_id
    assert new_id not in before
    # old row is still present (content-addressing never overwrites history)
    assert reg.count() == 2
    reg.close()


def test_pipeline_rejects_bad_file(tmp_path, corpus_root):
    bad = corpus_root / "broken.pdf"
    bad.write_bytes(b"<html><title>404 Not Found</title></html>")
    reg = SourceRegistry(tmp_path / "reg" / "r.sqlite")
    store = LocalStore(tmp_path / "docs")
    res = IngestionPipeline(corpus_root, reg, store).run(min_pdf_bytes=16)
    assert res.accepted == []
    assert len(res.rejected) == 1
    assert reg.count() == 0
    assert res.rejected[0][0].path == bad
    reg.close()


def test_pipeline_doc_type_filter(tmp_path, qp_pdf, ms_pdf):
    reg = SourceRegistry(tmp_path / "reg" / "r.sqlite")
    store = LocalStore(tmp_path / "docs")
    res = IngestionPipeline(qp_pdf.parent, reg, store).run(
        doc_type_filter=DocType.QUESTION_PAPER, min_pdf_bytes=256)
    assert len(res.accepted) == 1
    assert res.accepted[0].doc_type is DocType.QUESTION_PAPER
    reg.close()


def test_safe_name_removes_colons(tmp_path):
    assert safe_name("src:abcd:ef01") == "src_abcd_ef01"
    assert ":" not in safe_name("src:x:y")


def test_store_key_layout(tmp_path, qp_pdf):
    reg = SourceRegistry(tmp_path / "reg" / "r.sqlite")
    store = LocalStore(tmp_path / "docs")
    pipe = IngestionPipeline(qp_pdf.parent, reg, store)
    sf = pipe.discovery.walk()[0]
    sf.doc_type = DocType.QUESTION_PAPER
    key = pipe._store_key(sf)
    assert key.startswith("question_paper/")
    assert key.endswith(".pdf")
    assert "/" in key and ":" not in key
    reg.close()