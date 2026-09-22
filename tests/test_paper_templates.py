"""A teacher's paper template: model, presets, API, availability, generation.

Task 901 (user priority 2, 2026-09-22): a guided builder with saved teacher
templates. These tests pin the contract the builder UI is written against:

  * the totals are exact, and a mismatch is a 422 that names the numbers;
  * every class 6-10 main-subject preset sums exactly, and the class 9-10
    annual presets say which CBSE SQP they come from;
  * `default_sections` hits every total the UI offers (20..100) -- it used to
    miss 40 (41), 50 (52), 70 (69) and 100 (101);
  * CRUD, sharing and the school/role boundaries;
  * availability on a tiny fixture bank reports the real shortfall and why;
  * generation follows the template and never hands back a silently short
    paper, and never prints a question without a verified answer key (Q1).

Hermetic: the question pool is a fixture seeded into `pool._CACHE`; the
served bank is never loaded under pytest (see pool.build_pool).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from academicos.api.main import app
from academicos.assessment import pool as pool_mod
from academicos.assessment.schemas import PaperTemplate, PaperTemplateDraft
from academicos.assessment.templates import default_sections
from academicos.assessment.template_presets import MAIN_SUBJECTS, PRESET_EXAM_TYPES, presets
from academicos.models.academic import Question


# ------------------------------------------------------------------ helpers

def _section(title="Section A", count=4, marks=1, attempt=None, **extra) -> dict:
    body = {"title": title, "questionCount": count, "marksEach": marks}
    if attempt is not None:
        body["attemptCount"] = attempt
    body.update(extra)
    return body


def _draft(**overrides) -> dict:
    body = {
        "name": "Unit test - Chemical reactions",
        "grade": 10,
        "subject": "Science",
        "examType": "unit_test",
        "totalMarks": 10,
        "durationMinutes": 40,
        "instructions": "All questions are compulsory.",
        "header": {"schoolName": "Green Valley School", "examName": "Unit Test 1",
                   "dateLine": "Date: ________"},
        "sections": [_section("Section A", 4, 1), _section("Section B", 2, 3)],
        "scope": {"chapterIds": ["ch1"]},
    }
    body.update(overrides)
    return body


# ------------------------------------------------------------------ model

def test_valid_template_passes():
    t = PaperTemplateDraft.model_validate(_draft())
    assert t.total_marks == 10
    assert [s.title for s in t.sections] == ["Section A", "Section B"]


def test_sections_not_summing_to_total_is_rejected_naming_the_numbers():
    with pytest.raises(ValidationError) as err:
        PaperTemplateDraft.model_validate(_draft(totalMarks=12))
    msg = str(err.value)
    assert "10" in msg and "12" in msg


def test_attempt_count_above_question_count_is_rejected():
    body = _draft(sections=[_section("Section A", 4, 1, attempt=5), _section("Section B", 2, 3)],
                  totalMarks=11)
    with pytest.raises(ValidationError) as err:
        PaperTemplateDraft.model_validate(body)
    assert "Section A" in str(err.value)


def test_internal_choice_counts_only_attempted_marks():
    # 5 questions printed, attempt any 4 of 3 marks = 12 marks, not 15.
    body = _draft(sections=[_section("Section A", 5, 3, attempt=4)], totalMarks=12)
    assert PaperTemplateDraft.model_validate(body).total_marks == 12


def test_difficulty_mix_must_sum_to_one():
    body = _draft(sections=[
        _section("Section A", 4, 1, difficultyMix={"easy": 0.5, "medium": 0.5, "hard": 0.5}),
        _section("Section B", 2, 3)])
    with pytest.raises(ValidationError) as err:
        PaperTemplateDraft.model_validate(body)
    assert "difficulty" in str(err.value).lower()


# ------------------------------------------------------------------ default_sections

@pytest.mark.parametrize("total", range(20, 101))
def test_default_sections_sum_exactly(total):
    sections = default_sections(total)
    assert sum(s.total_marks for s in sections) == total
    assert all(s.question_count * s.marks_per_question == s.total_marks for s in sections)
    assert all(s.question_count >= 1 for s in sections)


# ------------------------------------------------------------------ presets

def test_every_class_subject_exam_type_has_an_exact_preset():
    all_presets = presets()
    keys = {(p.grade, p.subject, p.exam_type) for p in all_presets}
    for grade in range(6, 11):
        for subject in MAIN_SUBJECTS:
            for exam_type in PRESET_EXAM_TYPES:
                assert (grade, subject, exam_type) in keys, (grade, subject, exam_type)
    for p in all_presets:
        assert p.is_preset
        assert sum(s.marks for s in p.sections) == p.total_marks, p.id
        # The model's own validator also passes (presets are real templates).
        PaperTemplate.model_validate(p.model_dump(by_alias=True))


def test_board_presets_cite_their_sqp_and_junior_presets_say_suggested():
    by_key = {(p.grade, p.subject, p.exam_type): p for p in presets()}
    maths10 = by_key[(10, "Mathematics", "annual")]
    assert maths10.pattern_status == "cbse_board"
    assert "SQP" in maths10.source and "Mathematics" in maths10.source
    assert [(s.question_count, s.marks_each) for s in maths10.sections] == [
        (20, 1), (5, 2), (6, 3), (4, 5), (3, 4)]
    assert maths10.total_marks == 80
    for grade in (6, 7, 8):
        assert by_key[(grade, "Science", "annual")].pattern_status == "suggested"


# ------------------------------------------------------------------ API

def _boot_client(tmp_path, monkeypatch):
    from academicos.assessment import audit_log, users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    monkeypatch.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", "test-bootstrap-key")
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(audit_log, "_INSTANCE", None)
    monkeypatch.setattr(users_mod, "_INSTANCE", None)
    monkeypatch.setattr(curriculum_store_mod, "_INSTANCE", None)
    from fastapi.testclient import TestClient

    return TestClient(app)


def _register(client, school_id, email, role="teacher", principal_key=None):
    body = {"schoolId": school_id, "name": email.split("@")[0], "email": email,
            "password": "correct horse battery", "role": role}
    if principal_key:
        body["principalKey"] = principal_key
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


BASE = "/api/v1/schools/school_1/teacher-templates"


def test_crud_sharing_and_scoping(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        t2 = _register(client, "school_1", "bob@example.com")
        principal = _register(client, "school_1", "priya@example.com",
                              principal_key="test-bootstrap-key")
        student = _register(client, "school_1", "stu@example.com", role="student")
        outsider = _register(client, "school_2", "zed@example.com")

        assert client.get(BASE).status_code == 401
        assert client.get(BASE, headers=student).status_code == 403
        assert client.get(BASE, headers=outsider).status_code == 403

        # Totals are checked on the way in, with the numbers named.
        bad = client.post(BASE, json=_draft(totalMarks=12), headers=t1)
        assert bad.status_code == 422
        assert "12" in bad.text and "10" in bad.text

        created = client.post(BASE, json=_draft(), headers=t1)
        assert created.status_code == 200, created.text
        tpl = created.json()
        tid = tpl["id"]
        assert tpl["shared"] is False and tpl["schoolId"] == "school_1"
        assert tpl["isDefault"] is False  # never displaces the school's branding default

        # Private: another teacher can neither read nor edit it.
        assert client.get(f"{BASE}/{tid}", headers=t2).status_code == 403
        assert client.put(f"{BASE}/{tid}", json=_draft(name="x"), headers=t2).status_code == 403
        assert client.post(f"{BASE}/{tid}/share", json={"shared": True},
                           headers=t2).status_code == 403
        # Another school: refused even with the right id.
        assert client.get(f"/api/v1/schools/school_2/teacher-templates/{tid}",
                          headers=outsider).status_code == 403
        assert client.get(f"{BASE}/{tid}", headers=student).status_code == 403

        listed = client.get(BASE, headers=t1).json()
        assert [t["id"] for t in listed["mine"]] == [tid]
        assert listed["shared"] == []
        assert listed["presets"], "presets are listed alongside the teacher's own"
        assert all(t["id"] != tid for t in client.get(BASE, headers=t2).json()["mine"])

        # The owner edits it.
        edited = client.put(f"{BASE}/{tid}", json=_draft(name="Renamed"), headers=t1)
        assert edited.status_code == 200 and edited.json()["name"] == "Renamed"

        # Shared: visible to the school, still editable only by its owner.
        assert client.post(f"{BASE}/{tid}/share", json={"shared": True},
                           headers=t1).status_code == 200
        t2_list = client.get(BASE, headers=t2).json()
        assert [t["id"] for t in t2_list["shared"]] == [tid]
        assert client.get(f"{BASE}/{tid}", headers=t2).status_code == 200
        assert client.put(f"{BASE}/{tid}", json=_draft(name="x"), headers=t2).status_code == 403
        assert client.delete(f"{BASE}/{tid}", headers=t2).status_code == 403

        # Anyone on staff may take a copy; it is theirs and private.
        copy = client.post(f"{BASE}/{tid}/duplicate", json={}, headers=t2)
        assert copy.status_code == 200, copy.text
        assert copy.json()["id"] != tid and copy.json()["shared"] is False
        assert copy.json()["basedOn"] == tid
        assert copy.json()["ownerId"] != tpl["ownerId"]

        # Principal may unshare and delete.
        assert client.post(f"{BASE}/{tid}/share", json={"shared": False},
                           headers=principal).status_code == 200
        assert client.delete(f"{BASE}/{tid}", headers=principal).status_code == 200
        assert client.get(f"{BASE}/{tid}", headers=t1).status_code == 404

        # The old branding list never shows teacher paper templates.
        branding = client.get("/api/v1/schools/school_1/school-templates", headers=t1).json()
        assert all(t["id"] != copy.json()["id"] for t in branding)


def test_presets_are_read_only_but_copyable(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        listed = client.get(BASE, params={"grade": 10, "subject": "Mathematics"},
                            headers=t1).json()
        preset = next(p for p in listed["presets"] if p["examType"] == "annual")
        assert all(p["grade"] == 10 and p["subject"] == "Mathematics" for p in listed["presets"])
        pid = preset["id"]

        assert client.get(f"{BASE}/{pid}", headers=t1).status_code == 200
        assert client.put(f"{BASE}/{pid}", json=_draft(), headers=t1).status_code == 403
        assert client.delete(f"{BASE}/{pid}", headers=t1).status_code == 403
        assert client.post(f"{BASE}/{pid}/share", json={"shared": True},
                           headers=t1).status_code == 403

        copy = client.post(f"{BASE}/{pid}/duplicate", json={"name": "My annual"}, headers=t1)
        assert copy.status_code == 200, copy.text
        body = copy.json()
        assert body["isPreset"] is False and body["basedOn"] == pid
        assert body["name"] == "My annual" and body["totalMarks"] == 80
        assert [t["id"] for t in client.get(BASE, headers=t1).json()["mine"]] == [body["id"]]


# ------------------------------------------------------------------ availability + generation

def _record(qid: str, marks: int, chapter: str, *, keyed: bool = True,
            difficulty: str = "medium", subject: str = "Science", grade: int = 10) -> dict:
    return {
        "id": qid, "questionBankId": "fixture", "subject": subject, "grade": grade,
        "chapterIds": [chapter], "competencyIds": [], "bloomLevel": "understand",
        "difficulty": difficulty, "type": "short_answer",
        "stem": f"Fixture question {qid}: explain the observed change in detail.",
        "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": ([{"id": "mp1", "description": "correct reasoning",
                                "marks": marks}] if keyed else []),
            "modelAnswer": "the model answer" if keyed else "",
        },
        "estimatedTimeMinutes": marks * 2, "marks": marks, "source": "cbse_board_paper",
        "qualityScore": 0.8, "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    }


def _fixture_pool(records: list[dict]) -> pool_mod.QuestionPool:
    out = pool_mod.QuestionPool()
    for rec in records:
        q = Question(canonical_id=rec["id"], title=rec["stem"][:100],
                     source_text=rec["stem"], marks=float(rec["marks"]))
        out.questions.append(pool_mod.PoolQuestion(
            question=q, subject=rec["subject"], grade="X", academic_year="2024",
            chapter_id=rec["chapterIds"][0], chapter_name=None, chapter_confidence=0.9,
            text_hash=rec["id"], record=rec))
    return out


FIXTURE = [
    _record("q1", 1, "ch1", difficulty="easy"),
    _record("q2", 1, "ch1"),
    _record("q3", 1, "ch1", difficulty="hard"),
    _record("q4", 1, "ch1", keyed=False),      # no key: never eligible (Q1)
    _record("q5", 1, "ch2"),
    _record("q6", 1, "ch2"),
    _record("q7", 3, "ch1"),
]


@pytest.fixture
def seeded(monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(FIXTURE))


def test_availability_reports_shortfall_and_reason(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(), headers=t1).json()["id"]

        r = client.post(f"{BASE}/{tid}/availability", json={}, headers=t1)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["complete"] is False
        a, b = body["sections"]
        assert (a["needed"], a["available"], a["shortfall"]) == (4, 3, 1)
        assert a["outsideScopeAvailable"] == 2
        assert a["withoutKey"] == 1
        assert "chapter" in a["reason"].lower()
        assert (b["needed"], b["available"], b["shortfall"]) == (2, 1, 1)
        assert b["reason"]

        # Widening the scope for this paper closes section A's gap.
        wide = client.post(f"{BASE}/{tid}/availability",
                           json={"scope": {"chapterIds": ["ch1", "ch2"]}}, headers=t1).json()
        assert wide["sections"][0]["shortfall"] == 0

        # An empty class/subject says so rather than a bare zero.
        seven = client.post(BASE, json=_draft(grade=7), headers=t1).json()["id"]
        monkeypatch.setitem(pool_mod._CACHE, ("Science", "VII"), pool_mod.QuestionPool())
        empty = client.post(f"{BASE}/{seven}/availability", json={}, headers=t1).json()
        assert empty["sections"][0]["available"] == 0
        assert "no class 7 science" in empty["sections"][0]["reason"].lower()


def test_generation_follows_template_and_never_silently_short(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(), headers=t1).json()["id"]
        url = "/api/v1/papers/generate-from-template"

        # Short sections and no permission to go short -> 409 with the gaps.
        refused = client.post(url, json={"templateId": tid}, headers=t1)
        assert refused.status_code == 409
        assert refused.json()["detail"]["availability"]["sections"][0]["shortfall"] == 1

        # Allowed short: the paper is built and every gap is returned.
        short = client.post(url, json={"templateId": tid, "allowGaps": True}, headers=t1)
        assert short.status_code == 200, short.text
        body = short.json()
        assert body["complete"] is False
        assert [g["shortfall"] for g in body["gaps"]] == [1, 1]
        sections = body["paper"]["sections"]
        assert [s["name"] for s in sections] == ["Section A", "Section B"]
        a_ids = [q["questionId"] for q in sections[0]["questions"]]
        assert sorted(a_ids) == ["q1", "q2", "q3"]            # in scope, keyed only
        assert "q4" not in a_ids                               # no key -> never printed
        # A short paper prints the marks it actually carries (3x1 + 1x3), not
        # the template's 10: its "Maximum Marks" line must match its questions.
        assert body["paper"]["metadata"]["totalMarks"] == 6

        # Filling from outside the chosen chapters is opt-in and flagged.
        filled = client.post(url, json={"templateId": tid, "allowGaps": True,
                                        "fillFromOutsideScope": True}, headers=t1).json()
        a_ids = [q["questionId"] for q in filled["paper"]["sections"][0]["questions"]]
        assert len(a_ids) == 4 and "q4" not in a_ids
        assert any("outside" in n.lower() for n in filled["notes"])

        # A template the bank can satisfy is generated complete, in order.
        exact = client.post(BASE, json=_draft(
            totalMarks=6, sections=[_section("Objective", 3, 1), _section("Short", 1, 3)],
        ), headers=t1).json()["id"]
        done = client.post(url, json={"templateId": exact}, headers=t1)
        assert done.status_code == 200, done.text
        assert done.json()["complete"] is True and done.json()["gaps"] == []
        assert done.json()["paper"]["metadata"]["totalMarks"] == 6
        secs = done.json()["paper"]["sections"]
        assert [len(s["questions"]) for s in secs] == [3, 1]
        assert secs[1]["questions"][0]["questionId"] == "q7"

        # Another school's template id is refused.
        outsider = _register(client, "school_2", "zed@example.com")
        assert client.post(url, json={"templateId": exact},
                           headers=outsider).status_code == 403
