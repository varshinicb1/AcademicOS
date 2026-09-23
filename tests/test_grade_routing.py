"""Grades 6-9 must reach the web paper path, and an unreadable grade must fail loudly.

Production has no registry.sqlite, so every web request takes build_pool's
baked-bank fallback. These tests drive that fallback with a temporary bank.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.assessment import mapping, pool as pool_module, routes  # noqa: E402
from academicos.assessment.pool import _grade_matches  # noqa: E402
# A complete record, so this test keeps passing after Task 6 makes the web path
# validate the whole record as a QuestionSchema. test_bank_merge exists after wave A.
from test_bank_merge import board  # noqa: E402


@pytest.mark.parametrize("grade,roman", [(6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX"),
                                         (10, "X"), (12, "XII")])
def test_route_grade_key_covers_six_to_twelve(grade, roman):
    assert routes._int_grade_to_roman(grade) == roman


@pytest.mark.parametrize("bad", [0, 13, 99])
def test_route_grade_key_refuses_instead_of_defaulting_to_ten(bad):
    with pytest.raises(HTTPException) as exc:
        routes._int_grade_to_roman(bad)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("pool_grade,requested,expected", [
    ("IX", "IX", True), ("VIII", "8", True), ("VI", "6th", True),
    ("X", "IX", False), ("X", "10", True), ("XII", "XII", True),
])
def test_pool_grade_match(pool_grade, requested, expected):
    assert _grade_matches(pool_grade, requested) is expected


@pytest.mark.parametrize("label,expected", [("IX", 9), ("9", 9), ("VI", 6), ("X", 10), ("XII", 12)])
def test_mapping_grade_to_int(label, expected):
    assert mapping.grade_to_int(label) == expected


def test_mapping_grade_to_int_refuses_junk():
    with pytest.raises(ValueError):
        mapping.grade_to_int("junk")


def _bank(tmp_path: Path, grade: int) -> Path:
    rec = board(id=f"cbe:q:T{grade}", subject="Mathematics", grade=grade,
                source="cbse_question_bank",
                stem="Find the value of 2 + 3 and explain each step you take.")
    p = tmp_path / "syllabus" / "questions.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"questions": [rec]}), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("grade,roman", [(6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX")])
def test_baked_fallback_serves_class_six_to_nine(tmp_path, monkeypatch, grade, roman):
    from academicos.config import Config

    data_root = _bank(tmp_path, grade)
    cfg = Config(data_root=data_root)
    cfg._load_baked_questions = True
    # Point every candidate path the fallback tries at the temp bank only.
    monkeypatch.setattr(pool_module, "_baked_bank_paths",
                        lambda cfg: [data_root / "syllabus" / "questions.json"])
    built = pool_module.build_pool(cfg, subject="Mathematics", grade=roman)
    assert [q.grade for q in built.questions] == [roman]
    schema = mapping.to_question_schema(built.questions[0])
    assert schema.grade == grade


def test_catalog_scope_includes_every_grade_in_the_bank(tmp_path, monkeypatch):
    from academicos.assessment import pillar_routes
    from academicos.config import Config

    data_root = _bank(tmp_path, 7)
    monkeypatch.setattr(pool_module, "_baked_bank_paths",
                        lambda cfg: [data_root / "syllabus" / "questions.json"])
    assert pillar_routes._catalog_scope(Config(data_root=data_root)) == [("Mathematics", 7)]


def test_get_pool_normalises_the_grade_before_caching(tmp_path, monkeypatch):
    """'X', '10' and '10th' are one pool, built once -- not three cache entries."""
    from academicos.config import Config

    data_root = _bank(tmp_path, 10)
    cfg = Config(data_root=data_root)
    cfg._load_baked_questions = True
    monkeypatch.setattr(pool_module, "_baked_bank_paths",
                        lambda cfg: [data_root / "syllabus" / "questions.json"])
    monkeypatch.setattr(pool_module, "_CACHE", {})
    built: list[str] = []
    real_build = pool_module.build_pool

    def counting_build(cfg, **kw):
        built.append(kw["grade"])
        return real_build(cfg, **kw)

    monkeypatch.setattr(pool_module, "build_pool", counting_build)
    pools = [pool_module.get_pool(cfg, subject="Mathematics", grade=g) for g in ("X", "10", "10th")]
    assert pools[0] is pools[1] is pools[2]
    assert built == ["X"]
    assert [q.grade for q in pools[0].questions] == ["X"]


@pytest.mark.parametrize("bad", ["", "junk", "XIII", "13"])
def test_get_pool_refuses_an_unreadable_grade_and_caches_nothing(tmp_path, monkeypatch, bad):
    from academicos.config import Config

    monkeypatch.setattr(pool_module, "_CACHE", {})
    with pytest.raises(ValueError):
        pool_module.get_pool(Config(data_root=tmp_path), subject="Mathematics", grade=bad)
    assert pool_module._CACHE == {}


@pytest.mark.parametrize("raw", ["X", "10", "10th", "Class 10", 10])
def test_practice_request_normalises_the_grade(raw):
    from academicos.assessment.pillar_routes import PracticeRequestBody

    assert PracticeRequestBody(student_id="s", grade=raw).grade == "X"


@pytest.mark.parametrize("bad", ["junk", "XIII", "0", ""])
def test_practice_request_refuses_an_unreadable_grade(bad):
    """A bad grade is a 422 at the request boundary, not an empty pool that
    comes back as 'no auto-scorable practice' warnings."""
    from academicos.assessment.pillar_routes import PracticeRequestBody

    with pytest.raises(ValidationError):
        PracticeRequestBody(student_id="s", grade=bad)


def test_practice_request_default_is_deliberately_still_class_ten():
    """Intentional, see 'Defaults kept on purpose' below: the shipped app posts only
    studentId and perConcept (pillar_api.dart generatePractice), and a student
    record holds no grade."""
    from academicos.assessment.pillar_routes import PracticeRequestBody

    assert PracticeRequestBody(student_id="s").grade == "X"


# Each model gets a body that is valid apart from the missing grade. One body
# for both stopped working when QuickPaperRequest began refusing a field it
# does not have (c4aa403): `questionIds` belongs to GenerateFromIdsRequest, and
# the quick request then failed on the stray field as well as the grade, which
# would have hidden a regression in the grade rule behind an unrelated error.
@pytest.mark.parametrize("model,body", [
    ("QuickPaperRequest", {"subject": "Mathematics"}),
    ("GenerateFromIdsRequest", {"subject": "Mathematics", "questionIds": ["q1"]}),
])
def test_paper_requests_require_a_grade(model, body):
    """A request with no grade used to become a class 10 paper (`grade: int = 10`)."""
    from academicos.assessment import schemas

    with pytest.raises(ValidationError) as exc:
        getattr(schemas, model).model_validate(body)
    assert [e["loc"] for e in exc.value.errors()] == [("grade",)]


def test_scan_session_for_an_unknown_assessment_is_refused_not_made_class_ten(monkeypatch):
    """It used to become a Science class 10 session. Every later route on that
    session 404s anyway (require_school_owns_scan_session), so it could never be
    processed -- the default only hid the mistake."""
    from academicos.assessment import mobile_routes
    from academicos.assessment.users import User

    class _NoAssessments:
        def get(self, _id):
            return None

    monkeypatch.setattr(routes, "_store", _NoAssessments())
    user = User(id="t1", school_id="school_1", name="T", email="t@example.com",
                role="teacher", created_at="")
    req = mobile_routes.CreateScanSessionRequest(
        assessment_id="nope", student_id="s1", student_name="S")
    with pytest.raises(HTTPException) as exc:
        mobile_routes.create_scan_session(req, current=user)
    assert exc.value.status_code == 404


def test_registry_query_reads_every_grade_spelling(tmp_path):
    """registry.sqlite's sources.grade holds '6'..'9' for classes 6-9 but 'X' and
    'XII' for 10 and 12 (measured 2026-09-21). A raw `grade=?` against the pool's
    roman key would miss a class 8 paper stored as '8'."""
    from academicos.config import Config

    cfg = Config(data_root=tmp_path)
    cfg.registry_db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(cfg.registry_db)
    con.execute("CREATE TABLE sources (source_id TEXT, doc_type TEXT, subject TEXT, "
                "grade TEXT, academic_year TEXT)")
    con.executemany("INSERT INTO sources VALUES (?,?,?,?,?)", [
        ("qp8", "question_paper", "Mathematics", "8", "2025"),
        ("qp10", "question_paper", "Mathematics", "X", "2025"),
        ("book8", "reference_material", "Mathematics", "8", None),
        ("nograde", "question_paper", "Mathematics", None, "2025"),
    ])
    con.commit()
    con.close()
    rows = pool_module._registry_paper_rows
    assert [r["source_id"] for r in rows(cfg, "Mathematics", "VIII")] == ["qp8"]
    assert [r["source_id"] for r in rows(cfg, "Mathematics", "X")] == ["qp10"]
    assert rows(cfg, "Science", "X") == []


def test_registry_question_is_labelled_with_the_pool_key_not_the_registry_spelling(
        tmp_path, monkeypatch):
    """A class 8 paper stored as '8' must come out labelled 'VIII', the same label
    the baked path gives it. The label is passed to AnswerKeyStore.lookup as the
    grade, so a raw '8' could miss the official answer and leave the question
    unscorable with no error."""
    from types import SimpleNamespace

    from academicos.config import Config
    from academicos.models.academic import Question
    from academicos.models.enums import DocType

    cfg = Config(data_root=tmp_path)
    cfg.registry_db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(cfg.registry_db)
    con.execute("CREATE TABLE sources (source_id TEXT, doc_type TEXT, subject TEXT, "
                "grade TEXT, academic_year TEXT)")
    con.execute("INSERT INTO sources VALUES (?,?,?,?,?)",
                ("qp8", "question_paper", "Science", "8", "2025"))
    con.commit()
    con.close()
    cfg.parse_dir.mkdir(parents=True, exist_ok=True)
    (cfg.parse_dir / "qp8.json").write_text("{}", encoding="utf-8")

    stem = "Explain why a candle flame goes out when it is covered with a glass jar."
    monkeypatch.setattr(pool_module, "ParsedDocument", SimpleNamespace(
        model_validate=lambda _d: SimpleNamespace(doc_type=DocType.QUESTION_PAPER)))
    monkeypatch.setattr(pool_module, "_paper_code_of", lambda _doc: "")
    monkeypatch.setattr(pool_module, "_open_answer_keys", lambda _cfg: None)
    monkeypatch.setattr(pool_module, "extract_questions", lambda _doc, _t: [
        Question(canonical_id="q1", title=stem, source_text=stem, marks=2.0)])

    built = pool_module.build_pool(cfg, subject="Science", grade="VIII")
    assert [pq.grade for pq in built.questions] == ["VIII"]
