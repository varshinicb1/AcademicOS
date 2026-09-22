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
            difficulty: str = "medium", subject: str = "Science", grade: int = 10,
            qtype: str = "short_answer") -> dict:
    return {
        "id": qid, "questionBankId": "fixture", "subject": subject, "grade": grade,
        "chapterIds": [chapter], "competencyIds": [], "bloomLevel": "understand",
        "difficulty": difficulty, "type": qtype,
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


# ------------------------------------------------------------------ review fixes

def test_old_school_template_routes_cannot_reach_teacher_paper_templates(tmp_path, monkeypatch):
    """Paper templates live in the `school_templates` table. The older
    `/school-templates` routes only check the school, so without a guard a
    student could read a teacher's private sections or delete the template,
    and a colleague could overwrite it as a branding row."""
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        t2 = _register(client, "school_1", "bob@example.com")
        student = _register(client, "school_1", "stu@example.com", role="student")
        tid = client.post(BASE, json=_draft(), headers=t1).json()["id"]
        old = "/api/v1/schools/school_1/school-templates"

        assert client.get(f"{old}/{tid}/sections", headers=student).status_code == 403
        assert client.get(f"{old}/{tid}/sections", headers=t2).status_code == 403
        overwrite = client.post(old, json={"template": {"id": tid, "schoolId": "school_1",
                                                        "name": "hijack"}}, headers=t2)
        assert overwrite.status_code == 403
        assert client.delete(f"{old}/{tid}", headers=student).status_code == 403
        assert client.delete(f"{old}/{tid}", headers=t1).status_code == 403

        still = client.get(f"{BASE}/{tid}", headers=t1)
        assert still.status_code == 200 and still.json()["name"] == _draft()["name"]

        # Branding rows are school-scoped by id too, not just by URL.
        outsider = _register(client, "school_2", "zed@example.com")
        bid = client.post(old, json={"template": {"id": "new", "schoolId": "school_1",
                                                  "name": "Green Valley"}},
                          headers=t1).json()["id"]
        other = "/api/v1/schools/school_2/school-templates"
        assert client.post(other, json={"template": {"id": bid, "schoolId": "school_2",
                                                     "name": "x"}},
                           headers=outsider).status_code == 403
        assert client.get(f"{other}/{bid}/sections", headers=outsider).status_code == 403
        assert client.delete(f"{other}/{bid}", headers=outsider).status_code == 403
        assert any(t["id"] == bid for t in client.get(old, headers=t1).json())


def test_store_branding_lookups_never_return_a_paper_template(tmp_path):
    """quick/custom generation resolve `templateId` through the store with no
    owner check, so the store itself must not hand out a private paper."""
    from academicos.assessment.school_templates import TemplateStore
    from academicos.assessment.schemas import SchoolTemplate

    store = TemplateStore(tmp_path / "templates.sqlite")
    body = PaperTemplateDraft.model_validate(_draft()).model_dump()
    saved = store.save_paper_template(PaperTemplate(
        **body, id="new", school_id="school_1", owner_id="u_ana"))
    assert store.get_branding(saved.id, "school_1") is None
    got = store.sections_for("school_1", saved.id, 80)
    assert [s.total_marks for s in got] == [s.total_marks for s in default_sections(80)]
    # And another school's branding row is not reachable by id either.
    brand = store.save(SchoolTemplate(id="new", school_id="school_1", name="GV",
                                      is_default=False), default_sections(40))
    assert store.get_branding(brand.id, "school_1") is not None
    assert store.get_branding(brand.id, "school_2") is None
    assert [s.total_marks for s in store.sections_for("school_2", brand.id, 80)] == \
        [s.total_marks for s in default_sections(80)]


def _taxonomy(tmp_path, monkeypatch):
    import json as _json
    from academicos.assessment import paper_templates

    tax = tmp_path / "taxonomy"
    tax.mkdir()
    (tax / "science_10.json").write_text(_json.dumps({
        "subject": "Science", "grade": 10,
        "chapters": [{"id": "ch1", "topics": [
            {"id": "sci10.ch1.t1", "name": "Balancing equations",
             "subtopics": [{"id": "sci10.ch1.t1.s1", "name": "Hit and trial"}]}]}],
    }), encoding="utf-8")
    monkeypatch.setattr(paper_templates, "TAXONOMY_DIR", tax)
    return tax


def test_topic_ids_are_checked_against_the_taxonomy_when_present(tmp_path, monkeypatch):
    _taxonomy(tmp_path, monkeypatch)
    with _boot_client(tmp_path / "data", monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        good = client.post(BASE, json=_draft(scope={
            "chapterIds": ["ch1"], "topicIds": ["sci10.ch1.t1"],
            "subtopicIds": ["sci10.ch1.t1.s1"]}), headers=t1)
        assert good.status_code == 200, good.text
        assert good.json()["scopeNotes"] == []

        bad = client.post(BASE, json=_draft(scope={
            "chapterIds": ["ch1"], "topicIds": ["sci10.ch1.t9"],
            "subtopicIds": ["nope"]}), headers=t1)
        assert bad.status_code == 422
        assert "sci10.ch1.t9" in bad.text and "nope" in bad.text

        tid = good.json()["id"]
        edit = client.put(f"{BASE}/{tid}", json=_draft(scope={"topicIds": ["zz"]}), headers=t1)
        assert edit.status_code == 422 and "zz" in edit.text
        avail = client.post(f"{BASE}/{tid}/availability",
                            json={"scope": {"subtopicIds": ["zz"]}}, headers=t1)
        assert avail.status_code == 422 and "zz" in avail.text


def test_topic_ids_accepted_unchecked_without_taxonomy_and_saying_so(tmp_path, monkeypatch):
    from academicos.assessment import paper_templates

    monkeypatch.setattr(paper_templates, "TAXONOMY_DIR", tmp_path / "absent")
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        r = client.post(BASE, json=_draft(scope={"chapterIds": ["ch1"],
                                                 "topicIds": ["anything"]}), headers=t1)
        assert r.status_code == 200, r.text
        assert any("without checking" in n for n in r.json()["scopeNotes"])
        plain = client.post(BASE, json=_draft(), headers=t1).json()
        assert plain["scopeNotes"] == []


# The mark total each exam type is meant to carry. Written out here, not read
# from template_presets, so a preset whose rows drift from its intended total
# fails -- `sum(s.marks) == total_marks` alone is true by construction.
INTENDED_TOTAL = {"unit_test": 20, "periodic": 40, "half_yearly": 80, "annual": 80}


def test_every_preset_carries_its_exam_types_intended_total():
    for p in presets():
        assert p.total_marks == INTENDED_TOTAL[p.exam_type], (p.id, p.total_marks)
        assert sum(s.marks for s in p.sections) == INTENDED_TOTAL[p.exam_type], p.id


def test_board_science_and_social_science_follow_the_2024_25_sqp():
    """Read from the General Instructions of the CBSE Class X 2024-25 SQP PDFs
    (cbse-sqp/ClassX_2024_25/Science-SQP.pdf and SocialScience-SQP.pdf in the
    academicos-data corpus)."""
    by_key = {(p.grade, p.subject, p.exam_type): p for p in presets()}
    sci = by_key[(10, "Science", "annual")]
    assert [(s.question_count, s.marks_each) for s in sci.sections] == [
        (20, 1), (6, 2), (7, 3), (3, 5), (3, 4)]
    sst = by_key[(10, "Social Science", "annual")]
    assert [(s.question_count, s.marks_each) for s in sst.sections] == [
        (20, 1), (4, 2), (5, 3), (4, 5), (3, 4), (1, 5)]
    for p in (sci, sst):
        assert p.pattern_status == "cbse_board"
        assert "2024-25" in p.source and "General Instructions" in p.source


def test_a_copy_of_a_preset_is_the_teachers_not_a_board_pattern(tmp_path, monkeypatch):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        pid = "preset:cbse:10:mathematics:annual"
        assert client.get(f"{BASE}/{pid}", headers=t1).json()["patternStatus"] == "cbse_board"
        copy = client.post(f"{BASE}/{pid}/duplicate", json={}, headers=t1).json()
        assert copy["patternStatus"] == "teacher"
        assert copy["source"].startswith("Copied from")
        assert copy["basedOn"] == pid


# ------------------------------------------------------------------ review fixes (2)

GEN = "/api/v1/papers/generate-from-template"


def test_generated_paper_prints_the_schools_branding_not_the_template_name(
        tmp_path, monkeypatch, seeded):
    """The PDF exporter reads the branding stored with the paper. Storing the
    PaperTemplate there printed the template's name ("Unit test - Chemical
    reactions") as the school's, and lost the logo and brand colour."""
    from academicos.assessment import paper_template_routes

    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        brand = client.post("/api/v1/schools/school_1/school-templates", json={"template": {
            "id": "new", "schoolId": "school_1", "name": "Green Valley Public School",
            "logoUrl": "logos/gv.png", "brandColor": "#1a5c2e", "isDefault": True}},
            headers=t1)
        assert brand.status_code == 200, brand.text
        exact = _draft(totalMarks=6, sections=[_section("Objective", 3, 1),
                                               _section("Short", 1, 3)])
        tid = client.post(BASE, json=exact, headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid, "setCount": 2}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        for pid in [paper["id"]] + [s["id"] for s in paper["sets"]]:
            stored = paper_template_routes._papers.get_template(pid)
            # The teacher's header names the school; the logo and colour are
            # the school's own.
            assert stored.name == "Green Valley School"
            assert stored.logo_url == "logos/gv.png" and stored.brand_color == "#1a5c2e"
            assert "Date: ________" in stored.tagline
            assert type(stored).__name__ == "SchoolTemplate"

        # Without a header school name, the school's branding name prints.
        plain = client.post(BASE, json={**exact, "name": "Plain", "header": {}},
                            headers=t1).json()["id"]
        pid = client.post(GEN, json={"templateId": plain}, headers=t1).json()["paper"]["id"]
        assert paper_template_routes._papers.get_template(pid).name ==             "Green Valley Public School"


TYPED = ([_record(f"a{i}", 1, "ch1", qtype="mcq") for i in range(3)]
         + [_record(f"b{i}", 1, "ch1", qtype="assertion_reason") for i in range(3)])


def test_every_set_keeps_each_sections_questions_in_that_section(tmp_path, monkeypatch):
    """Sets used to rotate each mark value across the whole paper, so set B
    moved an assertion-reason question under the MCQ heading."""
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(TYPED))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(totalMarks=6, sections=[
            _section("MCQ", 3, 1, questionTypes=["mcq"]),
            _section("Assertion-Reason", 3, 1, questionTypes=["assertion_reason"])]),
            headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid, "setCount": 3}, headers=t1)
        assert r.status_code == 200, r.text
        sets = r.json()["paper"]["sets"]
        assert [s["setLabel"] for s in sets] == ["A", "B", "C"]
        orders = []
        for s in sets:
            mcq, ar = s["sections"]
            assert sorted(q["questionId"] for q in mcq["questions"]) == ["a0", "a1", "a2"]
            assert sorted(q["questionId"] for q in ar["questions"]) == ["b0", "b1", "b2"]
            orders.append([q["questionId"] for q in mcq["questions"]])
        assert orders[0] != orders[1], "a later set is a reordering, not a copy"


def test_attempt_any_sections_print_attempted_marks_that_add_up(tmp_path, monkeypatch, seeded):
    """"Attempt any 3 of 4" 1-mark questions is a 3-mark section: printing 4
    made the sections add up to more than the paper's Maximum Marks."""
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(
            totalMarks=6, scope={"chapterIds": ["ch1", "ch2"]},
            sections=[_section("Grammar", 4, 1, attempt=3), _section("Short", 1, 3)]),
            headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid, "setCount": 2}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        for p in [paper] + paper["sets"]:
            assert [s["totalMarks"] for s in p["sections"]] == [3, 3]
            assert sum(s["totalMarks"] for s in p["sections"]) == p["metadata"]["totalMarks"] == 6
            assert "(3 marks)" in p["formattedContent"]


def test_set_count_is_bounded_to_the_labelled_sets(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(totalMarks=6, sections=[
            _section("Objective", 3, 1), _section("Short", 1, 3)]), headers=t1).json()["id"]
        for bad in (0, 6, 10000):
            assert client.post(GEN, json={"templateId": tid, "setCount": bad},
                               headers=t1).status_code == 422, bad


def test_one_unreadable_template_row_does_not_break_the_list(tmp_path, monkeypatch):
    """A row saved before a validator tightened (or written through the remote
    path) must not 500 the teacher's first screen for the whole school."""
    import json as _json
    import sqlite3

    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        good = client.post(BASE, json=_draft(name="Good"), headers=t1).json()["id"]
        bad = client.post(BASE, json=_draft(name="Legacy"), headers=t1).json()["id"]
        db = sqlite3.connect(str(tmp_path / "templates" / "templates.sqlite"))
        payload = _json.loads(db.execute("SELECT payload FROM school_templates WHERE id=?",
                                         (bad,)).fetchone()[0])
        payload["total_marks"] = 999          # no longer matches its sections
        db.execute("UPDATE school_templates SET payload=? WHERE id=?",
                   (_json.dumps(payload), bad))
        db.commit()
        db.close()

        r = client.get(BASE, headers=t1)
        assert r.status_code == 200, r.text
        assert [t["id"] for t in r.json()["mine"]] == [good]


# ------------------------------------------------------------------ section content (review of 248e832)
#
# The engine used to match a question to a section by marks alone, so the
# class 10 Social Science annual preset reported complete=True while putting
# "Read the given source" items under "Section D - Long answer" and "Section
# F - Map skill", and outline-map items under "Section E - Case based". The
# fixture below reproduces the shape of the real bank: its type labels come
# from marks (mapping._resolve_type: 3-4 -> long_answer, 5+ -> case_study), so
# a source item stored as 5 marks is labelled case_study exactly like a real
# 5-mark long answer, and a map item stored as 4 marks is labelled long_answer.

def _q(qid: str, marks: int, stem: str, qtype: str, quality: float = 0.8):
    from academicos.assessment.schemas import QuestionSchema
    rec = _record(qid, marks, "ch1", qtype=qtype, subject="Social Science")
    rec["stem"] = stem
    rec["qualityScore"] = quality
    return QuestionSchema.model_validate(rec)


SOURCE = "Read the given source and answer the questions that follow : {}"
MAP = ("Two places A and B have been marked on the given political outline map of "
       "India. Identify them and write their names. {}")
LONG = "Explain, with examples, how {} changed the economy of the region."


def _ss_bank(*, map5: bool = True, case4: bool = True):
    bank = ([_q(f"a{i}", 1, f"One-mark item {i}?", "very_short_answer") for i in range(20)]
            + [_q(f"b{i}", 2, f"Two-mark item {i}?", "short_answer") for i in range(4)]
            + [_q(f"c{i}", 3, f"Three-mark item {i}?", "long_answer") for i in range(5)]
            # 5 marks: source items and real long answers share the label.
            # The wrong-kind items score higher, so a marks-only engine
            # reaches for them first rather than by luck of id order.
            + [_q(f"src{i}", 5, SOURCE.format(i), "case_study", 0.95) for i in range(4)]
            + [_q(f"long{i}", 5, LONG.format(i), "case_study") for i in range(4)]
            # 4 marks: map items labelled long_answer by their marks.
            + [_q(f"map{i}", 4, MAP.format(i), "long_answer", 0.95) for i in range(3)])
    if case4:
        bank += [_q(f"case{i}", 4, SOURCE.format(f"case {i}"), "long_answer") for i in range(3)]
    if map5:
        bank += [_q("map5", 5, MAP.format("five"), "case_study", 0.5)]
    return bank


def _plan_preset(preset_id: str, bank):
    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope
    from academicos.assessment.template_presets import get_preset

    t = get_preset(preset_id)
    return plan(t, t.id, bank, build_scope_filter(TemplateScope(), bank))


SS10 = "preset:cbse:10:social-science:annual"


def test_board_presets_name_the_question_kind_of_their_long_case_and_map_sections():
    for subject in ("Mathematics", "Science", "Social Science"):
        for grade in (9, 10):
            p = next(p for p in presets(grade=grade, subject=subject) if p.exam_type == "annual")
            by_title = {s.title: s for s in p.sections}
            d = next(s for t, s in by_title.items() if "Long answer" in t)
            e = next(s for t, s in by_title.items() if "ase" in t and "Section E" in t)
            assert "long_answer" in d.question_types and "case_study" not in d.question_types
            assert e.question_types == ["case_study"]
            if subject == "Social Science":
                assert by_title["Section F - Map skill"].question_types == ["map_based"]


def test_a_case_or_map_question_is_never_placed_under_the_wrong_heading():
    report, plans = _plan_preset(SS10, _ss_bank())
    by_title = {p.section.title: p for p in plans}

    def ids(title):
        p = by_title[title]
        return {q.id for q in p.picked + p.borrowed}

    long_ids = ids("Section D - Long answer")
    case_ids = ids("Section E - Case based")
    map_ids = ids("Section F - Map skill")
    assert long_ids and all(i.startswith("long") for i in long_ids), long_ids
    assert case_ids and all(i.startswith("case") for i in case_ids), case_ids
    assert map_ids == {"map5"}
    assert report.complete is True


def test_a_map_section_with_no_map_question_is_a_gap_not_any_5_mark_question():
    report, plans = _plan_preset(SS10, _ss_bank(map5=False))
    f = next(p for p in plans if p.section.title == "Section F - Map skill")
    assert f.picked == [] and f.availability.shortfall == 1
    assert "map" in f.availability.reason.lower()
    assert report.complete is False


def test_a_competency_section_with_no_competency_question_is_a_gap():
    # Only map items at 4 marks, which the case section refuses; and with a
    # plain 4-mark item that is not competency-based, still not complete.
    bank = _ss_bank(case4=False) + [
        _q("plain4", 4, "List four features of the region's climate.", "long_answer")]
    report, plans = _plan_preset(SS10, bank)
    e = next(p for p in plans if p.section.title == "Section E - Case based")
    assert "plain4" not in {q.id for q in e.picked}
    assert e.availability.shortfall == 3
    assert "competency" in e.availability.reason.lower()
    assert report.complete is False


def test_a_heading_no_constraint_checks_says_so():
    """English Grammar/Reading/Literature are filled by marks alone -- the bank
    does not label a question as grammar -- so the report must say the
    section's content was not checked rather than implying it was."""
    from academicos.assessment.template_presets import get_preset
    bank = [_q(f"e{i}", 1, "Answer any four of the following in 40-50 words.",
               "very_short_answer") for i in range(40)]
    for q in bank:
        q.subject = "English"
    report, _ = _plan_preset("preset:cbse:10:english:annual", bank)
    by_title = {s.title: s for s in report.sections}
    grammar = by_title["Section B - Grammar (attempt any 10)"]
    assert any("not checked" in n for n in grammar.notes), grammar.notes

    ss_report, _ = _plan_preset(SS10, _ss_bank())
    for s in ss_report.sections:
        assert not any("not checked" in n for n in s.notes), (s.title, s.notes)
    assert get_preset(SS10) is not None
