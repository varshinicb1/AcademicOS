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
from academicos.assessment.template_presets import MAIN_SUBJECTS, PRESET_EXAM_TYPES, PRIMARY_SUBJECTS, presets
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
    for grade in range(1, 11):
        subjects = MAIN_SUBJECTS if grade >= 6 else PRIMARY_SUBJECTS[grade]
        for subject in subjects:
            for exam_type in PRESET_EXAM_TYPES:
                assert (grade, subject, exam_type) in keys, (grade, subject, exam_type)
    # EVS is a class 3-5 subject: no class 1-2 preset offers it.
    assert not any(p.subject == "EVS" and p.grade < 3 for p in all_presets)
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
    # Registration is by invite since security Task 301; the principal key
    # only creates a school's first principal.
    from _auth_helpers import invite_code

    body = {"name": email.split("@")[0], "email": email,
            "password": "correct horse battery"}
    if principal_key:
        body.update(schoolId=school_id, principalKey=principal_key)
    else:
        body["inviteCode"] = invite_code(school_id, role)
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

# Words that make each fixture question's stem its own. Two stems that
# differ only in an index ("One-mark item 3?" / "One-mark item 4?") are one
# question to the near-duplicate guard (pool.near_duplicate, Task 903), which
# keeps the second off the paper -- so a fixture bank of such stems could
# never fill a section. Neutral nouns: none is a map, case or source word the
# kind checks read.
_VOCAB = ("magnet", "copper", "enzyme", "glacier", "harvest", "lantern", "orbit",
          "pigment", "quartz", "ribbon", "saddle", "turbine", "valley", "walnut",
          "yeast", "anchor", "bridge", "candle", "desert", "engine", "falcon",
          "garnet", "hammer", "island", "jacket", "kettle", "ladder", "meadow",
          "needle", "oyster", "pepper", "quiver", "rocket", "silver", "tunnel",
          "velvet", "window", "zipper", "barley", "cotton", "dragon", "feather",
          "ginger", "helmet", "indigo", "jasmine", "kidney", "lemon")


def _distinct(qid: str) -> str:
    import random
    return " ".join(random.Random(qid).sample(_VOCAB, 6))


def _record(qid: str, marks: int, chapter: str, *, keyed: bool = True,
            difficulty: str = "medium", subject: str = "Science", grade: int = 10,
            qtype: str = "short_answer") -> dict:
    return {
        "id": qid, "questionBankId": "fixture", "subject": subject, "grade": grade,
        "chapterIds": [chapter], "competencyIds": [], "bloomLevel": "understand",
        "difficulty": difficulty, "type": qtype,
        "stem": f"Fixture question {qid}: explain {_distinct(qid)}.",
        "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": ([{"id": "mp1", "description": "correct reasoning",
                                "marks": marks}] if keyed else []),
            "modelAnswer": "the model answer" if keyed else "",
            # Rule Q1 takes a published provenance AND real content
            # (qbank_routes.KEY_PROVENANCE). A keyed fixture record stands in
            # for a real board record, so it carries the board's label; the
            # unkeyed one still holds nothing and stays ineligible either way.
            "provenance": "cbse_marking_scheme" if keyed else "teacher_authored",
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
# Classes 1-5: shorter papers (a suggested school pattern -- CBSE sets none).
PRIMARY_INTENDED_TOTAL = {"unit_test": 20, "periodic": 25, "half_yearly": 50, "annual": 50}


def test_every_preset_carries_its_exam_types_intended_total():
    for p in presets():
        intended = (PRIMARY_INTENDED_TOTAL if p.grade <= 5 else INTENDED_TOTAL)[p.exam_type]
        assert p.total_marks == intended, (p.id, p.total_marks)
        assert sum(s.marks for s in p.sections) == intended, p.id


def test_primary_presets_are_suggested_and_have_no_long_answers():
    for p in presets():
        if p.grade <= 5:
            assert p.pattern_status == "suggested", p.id
            assert max(s.marks_each for s in p.sections) <= 5, p.id


# Read (Task 904, PyMuPDF) from the CBSE Class X 2024-25 SQPs in
# academicos-data/corpus/cbse-sqp/ClassX_2024_25/ (the PDFs are git-ignored;
# the 2025-26 SQPs beside them say the 2024-25 scheme continues). Per
# section: (questions, marks each, questions carrying a whole-question OR).
# Section E's choice in Science and Mathematics is inside a case unit's
# sub-part ("Attempt either subpart B or C"), part of the question itself,
# so it is not a whole-question OR here.
SQP_2024_25 = {
    # Science-SQP.pdf p. 1 General Instructions; ORs: B Q23, Q25 (pp. 5-6),
    # C Q28 (p. 8), D Q34-36 (pp. 10-13).
    "Science": [(20, 1, 0), (6, 2, 2), (7, 3, 1), (3, 5, 3), (3, 4, 0)],
    # SocialScience-SQP.pdf p. 1; ORs: B Q22 (p. 7), C Q26 (p. 8), D Q30-33
    # (pp. 8-9); none in E (case based) or F (map).
    "Social Science": [(20, 1, 0), (4, 2, 1), (5, 3, 1), (4, 5, 4), (3, 4, 0), (1, 5, 0)],
    # MathsStandard-SQP.pdf p. 1, instruction 8: "an internal choice in 2
    # Question of Section B, 2 Questions of Section C and 2 Questions of
    # Section D".
    "Mathematics": [(20, 1, 0), (5, 2, 2), (6, 3, 2), (4, 5, 2), (3, 4, 0)],
}


def test_board_presets_match_the_2024_25_sqps_including_internal_choice():
    by_key = {(p.grade, p.subject, p.exam_type): p for p in presets()}
    for subject, rows in SQP_2024_25.items():
        p = by_key[(10, subject, "annual")]
        assert [(s.question_count, s.marks_each, s.choice_count) for s in p.sections] == rows, \
            subject
        assert p.pattern_status == "cbse_board"
        # The board design applied to class 9 and the half-yearly keeps the
        # same choices.
        for key in ((9, subject, "annual"), (10, subject, "half_yearly")):
            assert [s.choice_count for s in by_key[key].sections] == [r[2] for r in rows], key
    sci = by_key[(10, "Science", "annual")].source
    assert "16 MCQ + 4 assertion-reason" in sci, sci
    sst = by_key[(10, "Social Science", "annual")]
    # The SQP's own heading (p. 9): "CASE-BASED QUESTIONS (3X4=12)".
    assert [s.title for s in sst.sections][4] == "Section E - Case based"
    for p in presets():
        assert "not on this machine" not in p.source, p.id
    # The printed instructions say which questions carry the choice.
    assert "OR" in by_key[(10, "Science", "annual")].instructions


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
            # The date line travels on the paper (Task 904), not folded into
            # the branding's tagline, where it printed twice.
            assert "Date: ________" not in (stored.tagline or "")
            assert type(stored).__name__ == "SchoolTemplate"
        for p in [paper] + paper["sets"]:
            assert p["metadata"]["dateLine"] == "Date: ________"

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


def test_builder_sets_print_questions_of_their_own_and_count_every_repeat(
        tmp_path, monkeypatch):
    """v3 audit N-2-5: sets B and C were set A rotated (100% of A's questions
    on 110/110 builder papers) though the bank allowed distinct sets. Each
    set is now planned by the sections' own rules from what earlier sets left
    -- verified keys and the paper's chapters only -- and made set A's shape;
    a slot repeats an earlier set's question only when nothing else fits,
    and the paper counts and names every repeat."""
    from test_paper_swap_pick import FIXTURE, _template
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool_records(FIXTURE))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_template(), headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid, "setCount": 3}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]

    def printed(p):
        return [(q["questionId"], q.get("internalChoiceQuestionId"))
                for s in p["sections"] for q in s["questions"]]

    a, b, c = paper["sets"]
    assert printed(a) == [("o0", None), ("o1", None), ("t0", None), ("t1", "t2")]
    # Set B: its own 1-mark and 3-mark questions; the bank has no 3-mark
    # question left for its OR, so it offers set A's OR alternative there.
    assert printed(b) == [("o2", None), ("o3", None), ("t3", None), ("t4", "t2")]
    # Set C: its own 1-mark questions; no 3-mark question is left at all, so
    # it prints set A's, not in set A's order.
    assert printed(c) == [("o4", None), ("o5", None), ("t1", None), ("t0", "t2")]
    assert paper["setOverlap"] == {"A": 0, "B": 1, "C": 3}
    assert [w for w in paper["warnings"] if " repeats " in w] == [
        "Set B repeats 1 question from an earlier set (Q4 (OR)): no other question in the "
        "bank fits that slot under the section's rules and the paper's chapters.",
        "Set C repeats 3 questions from an earlier set (Q3, Q4, Q4 (OR)): no other question "
        "in the bank fits those slots under the section's rules and the paper's chapters."]
    for s in (a, b, c):
        # The same paper in shape: sections, marks and choices.
        assert [(len(x["questions"]), x["totalMarks"]) for x in s["sections"]] == [(2, 2), (2, 6)]
        assert s["metadata"]["totalMarks"] == 8
        ids = {i for pair in printed(s) for i in pair if i}
        assert not ids & {"o6", "o7"}, "outside the chapters, or no verified key"
        for n, (qid, alt) in enumerate(printed(s), start=1):
            assert s["answerKey"][str(n)].startswith(f"model answer for {qid}")
            if alt:
                assert s["answerKey"][f"{n}_OR"] == f"model answer for {alt}"


def _fixture_pool_records(records: list[dict]):
    from test_paper_swap_pick import _pool
    return _pool(records)


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
#
# Task 125: a label we derived from marks carries metadata.typeInferred, as
# mapping.to_question_schema writes it, so it is never counted as the source
# printing a case study (competency.competency_signal). `inferred=False` is a
# type the source printed.

def _q(qid: str, marks: int, stem: str, qtype: str, quality: float = 0.8, *,
       inferred: bool = False, qbid: str = "fixture"):
    from academicos.assessment.schemas import QuestionSchema
    rec = _record(qid, marks, "ch1", qtype=qtype, subject="Social Science")
    rec["stem"] = f"{stem} [{_distinct(qid)}]"
    rec["qualityScore"] = quality
    rec["questionBankId"] = qbid
    if inferred:
        rec["metadata"] = {"typeInferred": True}
    return QuestionSchema.model_validate(rec)


SOURCE = "Read the given source and answer the questions that follow : {}"
MAP = ("Two places A and B have been marked on the given political outline map of "
       "India. Identify them and write their names. {}")
LONG = "Explain, with examples, how {} changed the economy of the region."


def _filler() -> list:
    """Sections A-C of the class 10 Social Science annual preset, labelled by marks."""
    return ([_q(f"a{i}", 1, f"One-mark item {i}?", "very_short_answer", inferred=True)
             for i in range(20)]
            + [_q(f"b{i}", 2, f"Two-mark item {i}?", "short_answer", inferred=True)
               for i in range(4)]
            + [_q(f"c{i}", 3, f"Three-mark item {i}?", "long_answer", inferred=True)
               for i in range(5)])


def _ss_bank(*, map5: bool = True, case4: bool = True):
    bank = (_filler()
            # 5 marks: source items and real long answers share the label.
            # The wrong-kind items score higher, so a marks-only engine
            # reaches for them first rather than by luck of id order.
            + [_q(f"src{i}", 5, SOURCE.format(i), "case_study", 0.95) for i in range(4)]
            + [_q(f"long{i}", 5, LONG.format(i), "case_study", inferred=True) for i in range(4)]
            # 4 marks: map items labelled long_answer by their marks.
            + [_q(f"map{i}", 4, MAP.format(i), "long_answer", 0.95, inferred=True)
               for i in range(3)])
    if case4:
        # Case studies their source prints as case studies.
        bank += [_q(f"case{i}", 4, SOURCE.format(f"case {i}"), "case_study") for i in range(3)]
    if map5:
        bank += [_q("map5", 5, MAP.format("five"), "case_study", 0.5, inferred=True)]
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
        _q("plain4", 4, "List four features of the region's climate.", "long_answer",
           inferred=True)]
    report, plans = _plan_preset(SS10, bank)
    e = next(p for p in plans if p.section.title == "Section E - Case based")
    assert "plain4" not in {q.id for q in e.picked}
    assert e.availability.shortfall == 3
    assert "competency" in e.availability.reason.lower()
    assert report.complete is False


def test_a_source_stem_alone_is_not_a_competency_signal():
    """Task 125: the template engine counts a question competency-based by the
    one rule (competency.competency_signal), never by its wording. "Read the
    given source" is text a stem can carry -- our merge prepends "Read the
    passage below" to items, and Exemplar prints "Read the following
    statements" -- so three 4-mark source items the bank labels long_answer
    do not make an all-competency section; the same items from a CBSE
    competency-based item bank do."""
    def sources(qbid: str) -> list:
        return [_q(f"srcfour{i}", 4, SOURCE.format(f"four {i}"), "long_answer",
                   inferred=True, qbid=qbid) for i in range(3)]

    report, plans = _plan_preset(SS10, _ss_bank(case4=False) + sources("fixture"))
    e = next(p for p in plans if p.section.title == "Section E - Case based")
    assert e.picked == [] and e.availability.shortfall == 3, e.availability
    assert "competency" in e.availability.reason.lower(), e.availability.reason
    assert report.complete is False

    report, plans = _plan_preset(SS10, _ss_bank(case4=False) + sources("cbe:x.pdf"))
    e = next(p for p in plans if p.section.title == "Section E - Case based")
    assert sorted(q.id for q in e.picked) == ["srcfour0", "srcfour1", "srcfour2"]
    assert (e.availability.filled, e.availability.shortfall) == (3, 0)


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


# ------------------------------------------------------------------ Task 904
#
# What the teacher is told before generating is what the paper will be. The
# availability check used to report counts only: the difficulty and
# competency shortfalls generation found went into the generated paper's
# notes alone, so on the real class 10 bank the Science annual preset's
# "Section E - Source / case based" read 3 of 3 available with no note and
# generating then said "1 competency-based question(s), the template asked
# for 3". And a shortfall reason could leave out the constraint that caused
# it, so the teacher had nothing to act on.

def _src_bank():
    """The shape of the real class 10 Social Science bank that made both
    reasons useless: the source items are stored at 5 marks (the CBSE Section
    E is 4), there are fewer real 5-mark long answers than Section D needs,
    and the only 4-mark question left is a plain one."""
    return (_filler()
            + [_q(f"long{i}", 5, LONG.format(i), "case_study", inferred=True) for i in range(3)]
            + [_q(f"src{i}", 5, SOURCE.format(i), "case_study") for i in range(6)]
            + [_q("plain4", 4, "List four features of the region's climate.", "long_answer",
                  inferred=True)]
            + [_q("map5", 5, MAP.format("five"), "case_study", inferred=True)])


def test_a_shortfall_reason_names_the_constraint_that_left_questions_out():
    report, _ = _plan_preset(SS10, _src_bank())
    by_title = {s.title: s for s in report.sections}

    d = by_title["Section D - Long answer"]
    assert (d.needed, d.available, d.shortfall) == (4, 3, 1)
    # Not just "Only 3 ... available": the 6 source items at 5 marks were
    # left out because they read as source based, and the reason says so.
    assert "6" in d.reason and "source / case based" in d.reason, d.reason
    relax = next(f for f in d.fixes if f.kind == "relax_type")   # largest kind first
    assert relax.available == 6 and "source / case based" in relax.label
    assert next(f for f in d.fixes if f.kind == "reduce_count").question_count == 3

    e = by_title["Section E - Case based"]
    assert e.shortfall == 3
    # The real cause: the source items carry 5 marks, the section asks for 4.
    assert "5 marks" in e.reason and "6" in e.reason, e.reason
    change = next(f for f in e.fixes if f.kind == "change_marks")
    assert (change.marks_each, change.available) == (5, 6)
    assert any(f.kind == "relax_competency" for f in e.fixes)


def test_availability_reports_the_mix_shortfall_generation_reports():
    """A section that fills by count but not by kind: 3 of 3 available, only
    1 competency-based. The check before generating must say so."""
    bank = _ss_bank(case4=False) + [
        _q("case0", 4, SOURCE.format("case 0"), "case_study"),
        _q("plain4", 4, "List four features of the region's climate.", "long_answer",
           inferred=True),
        _q("plain5", 4, "Describe four features of the region's soils.", "long_answer",
           inferred=True)]
    report, plans = _plan_preset(SS10, bank)
    for s, p in zip(report.sections, plans):
        assert s.notes == p.notes, s.title
        assert s.filled == len(p.picked) + len(p.borrowed)
    e = next(s for s in report.sections if s.title == "Section E - Case based")
    assert e.shortfall == 0 and e.filled == 3
    assert any("competency" in n for n in e.notes), e.notes


def test_borrowing_from_outside_the_scope_is_counted_before_generating():
    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope
    from academicos.assessment.template_presets import get_preset

    t = get_preset("preset:cbse:10:science:unit_test")
    bank = [_q(f"x{m}_{i}", m, f"Item {i} worth {m}?", "short_answer")
            for m, n in ((1, 8), (2, 6), (3, 4)) for i in range(n)]
    for i, q in enumerate(bank):
        q.chapter_ids = ["ch1" if i % 2 else "ch2"]
    scope = build_scope_filter(TemplateScope(chapter_ids=["ch1"]), bank)
    report, plans = plan(t, t.id, bank, scope, fill_from_outside_scope=True)
    assert any(p.borrowed for p in plans)
    for s, p in zip(report.sections, plans):
        assert s.filled == len(p.picked) + len(p.borrowed) == s.needed
        assert s.borrowed == len(p.borrowed) and s.shortfall == 0
        assert s.notes == p.notes
    assert report.complete is True


# ---- the real class 10 bank

from pathlib import Path as _Path  # noqa: E402

_REAL_BANK = _Path(__file__).resolve().parents[1] / "academicos-data" / "syllabus" / "questions.json"
needs_real_bank = pytest.mark.skipif(not _REAL_BANK.exists(),
                                     reason="the served question bank is not in this checkout")


@pytest.fixture(scope="module")
def real_class10_pools(tmp_path_factory):
    from academicos.config import Config
    cfg = Config(data_root=tmp_path_factory.mktemp("bank"))
    cfg._load_baked_questions = True
    return {s: pool_mod.build_pool(cfg, subject=s, grade="X") for s in MAIN_SUBJECTS}


def _real_plan(pools, preset_id):
    from academicos.assessment.mapping import to_question_schema
    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope

    t = next(p for p in presets(grade=10) if p.id == preset_id)
    bank = [to_question_schema(c) for c in pools[t.subject].filter(subject=t.subject, grade="X")]
    return plan(t, t.id, bank, build_scope_filter(TemplateScope(), bank))


@needs_real_bank
def test_availability_equals_generation_for_every_class_10_preset_on_the_real_bank(
        tmp_path, monkeypatch, real_class10_pools):
    for subject, pool in real_class10_pools.items():
        monkeypatch.setitem(pool_mod._CACHE, (subject, "X"), pool)
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        for p in presets(grade=10):
            avail = client.post(f"{BASE}/{p.id}/availability", json={}, headers=t1)
            assert avail.status_code == 200, (p.id, avail.text)
            report = avail.json()
            gen = client.post(GEN, json={"templateId": p.id, "allowGaps": True}, headers=t1)
            if gen.status_code == 400:            # nothing printable at all (Hindi: no keys)
                assert all(s["filled"] == 0 for s in report["sections"]), p.id
                continue
            assert gen.status_code == 200, (p.id, gen.text)
            body = gen.json()
            # Every note generation reports was shown before generating.
            shown = [n for s in report["sections"] for n in s["notes"]] + report["scopeNotes"]
            assert body["notes"] == shown, p.id
            # "Available" before is "filled" after, section by section.
            printed = [len(s["questions"]) for s in body["paper"]["sections"]]
            assert [s["filled"] for s in report["sections"] if s["filled"]] == printed, p.id
            assert [g["sectionId"] for g in body["gaps"]] == \
                [s["sectionId"] for s in report["sections"] if s["shortfall"]], p.id
            assert body["complete"] == report["complete"], p.id


def test_bank_shaped_presets_are_suggested_keep_their_totals_and_say_why():
    """D85/D18: presets asking for shapes a class's bank does not hold, where
    CBSE requires none, are written for what the bank holds -- labelled a
    suggestion, with the reason in the source line. The class 9-10 term
    papers keep the board design whatever the bank holds."""
    by_key = {(p.grade, p.subject, p.exam_type): p for p in presets()}
    shaped = [(g, "Mathematics", e) for g in (6, 7, 8) for e in PRESET_EXAM_TYPES] + \
             [(g, "Science", e) for g in (9, 10) for e in ("unit_test", "periodic")] + \
             [(6, "Science", e) for e in ("half_yearly", "annual")]
    for key in shaped:
        p = by_key[key]
        assert p.pattern_status == "suggested", key
        assert "not a CBSE rule" in p.source and f"Class {key[0]} {key[1]}" in p.source, key
        assert p.total_marks == INTENDED_TOTAL[p.exam_type], key
    for g in (6, 7, 8):
        marks = {s.marks_each for e in PRESET_EXAM_TYPES
                 for s in by_key[(g, "Mathematics", e)].sections}
        assert not marks & {2, 5}, (g, marks)
    for g in (9, 10):
        for e in ("unit_test", "periodic"):
            assert 2 not in {s.marks_each for s in by_key[(g, "Science", e)].sections}, (g, e)
        for e in ("half_yearly", "annual"):
            assert [(s.question_count, s.marks_each) for s in by_key[(g, "Science", e)].sections] \
                == [(r[0], r[1]) for r in SQP_2024_25["Science"]], (g, e)
    case = by_key[(6, "Science", "annual")].sections[-1]
    assert (case.marks_each, case.competency_share, case.question_types) == (6, 1.0, ["case_study"])
    # Classes and subjects the change does not concern keep their patterns.
    assert [(s.question_count, s.marks_each) for s in by_key[(7, "Science", "annual")].sections] \
        == [(16, 1), (8, 2), (8, 3), (4, 5), (1, 4)]
    assert [(s.question_count, s.marks_each) for s in by_key[(9, "Mathematics", "unit_test")].sections] \
        == [(6, 1), (4, 2), (2, 3)]


@pytest.fixture(scope="module")
def real_6_to_10_pools(tmp_path_factory):
    from academicos.assessment import grades
    from academicos.config import Config
    cfg = Config(data_root=tmp_path_factory.mktemp("bank610"))
    cfg._load_baked_questions = True
    return {(s, grades.to_roman(g)): pool_mod.build_pool(cfg, subject=s, grade=grades.to_roman(g))
            for s in ("Mathematics", "Science") for g in range(6, 11)}


@needs_real_bank
def test_mathematics_and_science_presets_reach_their_marks_on_the_real_bank(
        tmp_path, monkeypatch, real_6_to_10_pools):
    """D85/D18, through the builder's own calls (whole syllabus, three sets):
    18 of these 40 presets reached their marks before; 36 do now. The four
    that do not are class 9-10 Science half-yearly and annual, which keep the
    board design: the bank has 2 and 1 keyed 2-mark questions for Section B's
    six, and no 4-mark case-based question for Section E -- a bank gap, which
    the paper names, never filled with anything else."""
    for key, pool in real_6_to_10_pools.items():
        monkeypatch.setitem(pool_mod._CACHE, key, pool)
    short = {}
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        for subject in ("Mathematics", "Science"):
            for grade in range(6, 11):
                for p in presets(grade=grade, subject=subject):
                    avail = client.post(f"{BASE}/{p.id}/availability", json={}, headers=t1).json()
                    r = client.post(GEN, json={"templateId": p.id, "setCount": 3,
                                               "allowGaps": not avail["complete"]}, headers=t1)
                    assert r.status_code == 200, (p.id, r.text)
                    body = r.json()
                    got = body["paper"]["metadata"]["totalMarks"]
                    assert body["complete"] == (got == p.total_marks), p.id
                    assert {s["metadata"]["totalMarks"] for s in body["paper"]["sets"]} == {got}
                    if got != p.total_marks:
                        short[p.id] = sorted(g["title"] for g in body["gaps"])
    assert short == {
        f"preset:cbse:{g}:science:{e}": ["Section B - Very short answer",
                                         "Section E - Source / case based"]
        for g in (9, 10) for e in ("half_yearly", "annual")}


@needs_real_bank
def test_the_real_banks_competency_sections_warn_before_generating(real_class10_pools):
    """A section that asks for competency-based questions is never quietly
    filled with something else -- the report says so before generating.

    Re-measured after the question-bank merge (2026-09-23). Class 10 Science
    now holds 504 questions but none at 4 marks at all (308 1-mark MCQ, 127
    3-mark short answers, 51 5-mark long answers, 4+4+3 else), so Section E
    reports a whole-section shortfall naming the kind it needs instead of the
    competency-share note it carried when the pre-merge bank filled it from
    5-mark source items. The share note only ever describes a section that
    printed something, so the general guard below is the one that has to
    hold whatever the bank looks like: short, or noted, never silent.
    """
    from academicos.assessment.competency import is_competency_question

    report, _ = _real_plan(real_class10_pools, "preset:cbse:10:science:annual")
    e = next(s for s in report.sections if s.title.startswith("Section E"))
    assert (e.available, e.shortfall, e.needed) == (0, 3, 3), e
    assert "4-mark case study" in e.reason and "Class 10 Science" in e.reason, e.reason

    english, _ = _real_plan(real_class10_pools, "preset:cbse:10:english:annual")
    reading = next(s for s in english.sections if "Reading" in s.title)
    assert reading.shortfall and reading.reason, reading

    for preset in presets(grade=10):
        rep, plans = _real_plan(real_class10_pools, preset.id)
        for section, avail, plan_ in zip(preset.sections, rep.sections, plans):
            if not section.competency_share:
                continue
            printed = plan_.picked + plan_.borrowed
            got = sum(1 for q in printed if is_competency_question(q))
            if got >= round(section.competency_share * len(printed)):
                continue
            assert avail.shortfall or avail.notes, (preset.id, avail.title)


@needs_real_bank
def test_the_real_banks_social_science_gaps_name_their_binding_constraint(real_class10_pools):
    """Re-measured after the question-bank merge (2026-09-23): Class 10 Social
    Science is down to 14 served questions -- 12 one-mark MCQs and 2 three-mark
    short answers -- from 375 before, so the 5-mark and 4-mark sections have
    nothing of any kind rather than the wrong kind. What is checked is
    unchanged: the reason names the binding constraint (the marks AND the
    type the section needs), and a fix is only offered where the bank really
    has something to switch to."""
    report, _ = _real_plan(real_class10_pools, SS10)
    by_title = {s.title: s for s in report.sections}
    d = by_title["Section D - Long answer"]
    assert d.shortfall == d.needed
    assert "5-mark long answer/very long answer" in d.reason, d.reason
    assert "Class 10 Social Science" in d.reason, d.reason
    e = by_title["Section E - Case based"]
    assert e.shortfall == e.needed
    assert "4-mark case study" in e.reason, e.reason
    # Nothing of that kind at any mark value, so no "change the marks" fix is
    # invented; the honest fix left is to shorten or drop the section.
    assert not any(f.kind == "change_marks" for f in e.fixes), e.fixes
    assert any(f.kind == "reduce_count" for f in e.fixes), e.fixes
    # A section the bank can partly fill still says how far it gets.
    c = by_title["Section C - Short answer"]
    assert (c.available, c.shortfall) == (2, 3), c
    assert "Only 2 3-mark questions are available; 3 short." in c.reason, c.reason


# ---- presets checked against the real papers

def test_board_presets_cite_the_paper_file_and_page_they_were_read_from():
    by_key = {(p.grade, p.subject, p.exam_type): p for p in presets()}
    for subject, name in (("Mathematics", "MathsStandard"), ("Science", "Science"),
                          ("Social Science", "SocialScience")):
        p = by_key[(10, subject, "annual")]
        assert p.pattern_status == "cbse_board", subject
        for year in ("ClassX_2024_25", "ClassX_2025_26"):
            assert f"{year}/{name}-SQP.pdf" in p.source, (subject, p.source)
        # The marking scheme was read too: its section headings agree.
        assert f"ClassX_2024_25/{name}-MS.pdf" in p.source, p.source
        assert "General Instructions" in p.source and "p. 1" in p.source, p.source
    # CBSE sets no class IX paper: the class X design applied there is a
    # suggestion, and says so.
    for subject in ("Mathematics", "Science", "Social Science"):
        assert by_key[(9, subject, "annual")].pattern_status == "suggested", subject
    # The 2025 English board paper's literature Q9 is "any two of three" at
    # 3 marks each (2-1-1_English Language and Literature.pdf, p. 17).
    lit = [(s.question_count, s.marks_each, s.attempts)
           for s in by_key[(10, "English", "annual")].sections if "Literature" in s.title]
    assert (3, 3, 2) in lit and not any(m == 2 for _, m, _ in lit), lit


# ---- header and instructions on the paper

def test_the_generated_paper_carries_the_templates_header_and_instructions(
        tmp_path, monkeypatch, seeded):
    import fitz

    from academicos.assessment import paper_template_routes
    from academicos.assessment.pdf import export_pdf
    from academicos.assessment.schemas import GeneratedPaper

    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(
            totalMarks=6, instructions="Write neatly.\nNo calculators.",
            header={"schoolName": "Green Valley School", "examName": "Unit Test 1",
                    "dateLine": "Date: 3 October"},
            sections=[_section("Objective", 3, 1), _section("Short", 1, 3)]),
            headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid, "setCount": 2}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        for p in [paper] + paper["sets"]:
            m = p["metadata"]
            assert (m["schoolName"], m["examName"], m["dateLine"]) == (
                "Green Valley School", "Unit Test 1", "Date: 3 October")
            assert m["instructions"] == "Write neatly.\nNo calculators."
            assert m["durationMinutes"] == 40

        out = export_pdf(GeneratedPaper.model_validate(paper), tmp_path / "pdf",
                         template=paper_template_routes._papers.get_template(paper["id"]))
        doc = fitz.open(str(out))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        for expected in ("Green Valley School", "Unit Test 1", "Date: 3 October",
                         "Write neatly.", "No calculators."):
            assert expected in text, expected
        assert text.count("Date: 3 October") == 1


# ---- routes.py: a branding templateId on quick / custom generation

def test_quick_and_custom_generation_accept_a_branding_template_id(tmp_path, monkeypatch, seeded):
    """`TemplateStore.get_branding` returns (template, sections); both routes
    handed that tuple to PaperStore.save, which raised on the first templateId."""
    from academicos.assessment import routes as routes_mod

    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        brand = client.post("/api/v1/schools/school_1/school-templates", json={"template": {
            "id": "new", "schoolId": "school_1", "name": "Green Valley Public School"}},
            headers=t1).json()["id"]
        ids = client.post("/api/v1/papers/generate-from-ids", json={
            "subject": "Science", "grade": 10, "questionIds": ["q1", "q7"],
            "templateId": brand}, headers=t1)
        assert ids.status_code == 200, ids.text
        stored = routes_mod._require_papers().get_template(ids.json()["id"])
        assert stored.name == "Green Valley Public School"

        quick = client.post("/api/v1/papers/quick-generate", json={
            "subject": "Science", "grade": 10, "totalMarks": 6, "templateId": brand},
            headers=t1)
        assert quick.status_code == 200, quick.text
        stored = routes_mod._require_papers().get_template(quick.json()["id"])
        assert stored.name == "Green Valley Public School"


# ---- internal choice (OR), as the CBSE papers print it

def test_choice_count_above_question_count_is_rejected():
    body = _draft(sections=[_section("Section A", 4, 1),
                            _section("Section B", 2, 3, choiceCount=3)])
    with pytest.raises(ValidationError) as err:
        PaperTemplateDraft.model_validate(body)
    assert "Section B" in str(err.value) and "OR" in str(err.value)


def _choice_template(choices: int):
    return PaperTemplateDraft.model_validate(_draft(
        totalMarks=9, scope={},
        sections=[_section("Section A", 3, 1),
                  _section("Section B", 2, 3, choiceCount=choices)]))


def _choice_bank(threes: int):
    bank = ([_q(f"one{i}", 1, f"One-mark item {i}?", "very_short_answer") for i in range(3)]
            + [_q(f"three{i}", 3, f"Three-mark item {i}?", "short_answer") for i in range(threes)])
    for q in bank:
        q.subject = "Science"
    return bank


def _plan_draft(t, bank):
    import dataclasses

    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope
    # These fixtures carry no chapter, so the whole-syllabus rule would rank
    # every one of them last and say so; it has tests of its own below.
    scope = dataclasses.replace(build_scope_filter(TemplateScope(), bank), last_resort=frozenset())
    return plan(t, "tpl", bank, scope)


def test_a_section_with_internal_choice_pairs_an_or_alternative_per_choice():
    report, plans = _plan_draft(_choice_template(2), _choice_bank(4))
    b = plans[1]
    assert len(b.picked) == 2 and len(b.alternatives) == 2
    primaries = {q.id for q in b.picked}
    alts = {q.id for q in b.alternatives.values()}
    assert set(b.alternatives) <= primaries and not alts & primaries
    s = report.sections[1]
    assert (s.choices_needed, s.choices_filled, s.shortfall) == (2, 2, 0)
    assert report.complete is True and s.notes == []


def test_an_or_the_bank_cannot_pair_is_reported_before_generating():
    report, plans = _plan_draft(_choice_template(2), _choice_bank(3))
    s = report.sections[1]
    assert (s.filled, s.choices_needed, s.choices_filled) == (2, 2, 1)
    assert any("OR" in n and "1 of 2" in n for n in s.notes), s.notes
    assert s.notes == plans[1].notes
    assert any(f.kind == "reduce_choices" for f in s.fixes), s.fixes


def test_an_or_never_takes_a_question_a_later_section_needs_as_compulsory():
    # Section A offers ORs, Section B asks for the same marks and kind, and
    # the bank holds exactly the four questions both sections print. Pairing
    # A's ORs before B picked left B empty: "incomplete", and with gaps
    # allowed, 6 compulsory marks lost to print two optional ORs.
    t = PaperTemplateDraft.model_validate(_draft(totalMarks=12, scope={}, sections=[
        _section("Section A", 2, 3, choiceCount=2), _section("Section B", 2, 3)]))
    report, plans = _plan_draft(t, _choice_bank(4)[3:])
    a, b = report.sections
    assert report.complete is True
    assert (b.filled, b.shortfall) == (2, 0), b.reason
    assert (a.filled, a.choices_needed, a.choices_filled) == (2, 2, 0)
    # The ORs are what gives way, and the section that offers them says why.
    assert any("later section" in n for n in a.notes), a.notes
    assert any(f.kind == "reduce_choices" and f.choice_count == 0 for f in a.fixes), a.fixes
    printed = [q.id for p in plans for q in p.picked]
    assert len(printed) == len(set(printed)) == 4


def test_ors_pair_from_what_every_section_left_over():
    # One spare question: it becomes Section A's OR only after B has its two.
    t = PaperTemplateDraft.model_validate(_draft(totalMarks=12, scope={}, sections=[
        _section("Section A", 2, 3, choiceCount=2), _section("Section B", 2, 3)]))
    report, plans = _plan_draft(t, _choice_bank(5)[3:])
    a, b = report.sections
    assert report.complete is True and (b.filled, a.choices_filled) == (2, 1)
    used = [q.id for p in plans for q in p.picked] + \
           [q.id for p in plans for q in p.alternatives.values()]
    assert len(used) == len(set(used)) == 5


def test_the_generated_paper_prints_each_or_alternative(tmp_path, monkeypatch):
    bank = [_record(f"one{i}", 1, "ch1") for i in range(3)] + \
           [_record(f"three{i}", 3, "ch1") for i in range(4)]
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(bank))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_draft(
            totalMarks=9, sections=[_section("Section A", 3, 1),
                                    _section("Section B", 2, 3, choiceCount=2)]),
            headers=t1).json()["id"]
        avail = client.post(f"{BASE}/{tid}/availability", json={}, headers=t1).json()
        assert avail["sections"][1]["choicesFilled"] == 2
        r = client.post(GEN, json={"templateId": tid, "setCount": 2}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        for p in [paper] + paper["sets"]:
            b = p["sections"][1]
            assert len(b["questions"]) == 2 and b["totalMarks"] == 6
            ors = [q["internalChoiceQuestionId"] for q in b["questions"]]
            assert all(ors) and not set(ors) & {q["questionId"] for q in b["questions"]}
        assert paper["metadata"]["totalMarks"] == 9
        assert any(k.endswith("_OR") for k in paper["answerKey"])


# The SQP PDFs are git-ignored; point ACOS_CBSE_SQP_DIR at a checkout that has
# them to re-read the counts above from the papers themselves.
import os as _os  # noqa: E402

_SQP_DIR = _Path(_os.environ.get("ACOS_CBSE_SQP_DIR") or
                 _Path(__file__).resolve().parents[1] / "academicos-data" / "corpus" / "cbse-sqp")


@pytest.mark.skipif(not (_SQP_DIR / "ClassX_2024_25" / "Science-SQP.pdf").exists(),
                    reason="the CBSE SQP PDFs are not in this checkout")
def test_the_sqp_pdfs_say_what_the_presets_say():
    import re

    import fitz

    def text(name):
        doc = fitz.open(str(_SQP_DIR / "ClassX_2024_25" / f"{name}-SQP.pdf"))
        out = "\n".join(page.get_text() for page in doc)
        doc.close()
        return out

    def ors_per_section(body, heading, marker):
        parts = re.split(heading, body)[1:]          # text of each section, in order
        return [len(re.findall(marker, part, re.M)) for part in parts]

    sci = text("Science")
    assert "16 simple/complex MCQs and 04 Assertion-Reasoning" in sci
    # Science marks each whole-question OR "Attempt either option A or B."
    # (a visually-impaired alternative also prints "OR", so count the marker).
    got = ors_per_section(sci, r"\nSection\s*[-–]\s*[A-E]\s*\n", r"Attempt either option A or B")
    assert got == [c for _, _, c in SQP_2024_25["Science"]], got

    sst = text("SocialScience")
    got = ors_per_section(sst, r"\nSECTION [A-F]\s*\n", r"^\s*OR\s*$")
    assert got == [c for _, _, c in SQP_2024_25["Social Science"]], got

    maths = " ".join(text("MathsStandard").split())
    assert ("internal choice in 2 Question of Section B, 2 Questions of Section C and "
            "2 Questions of Section D") in maths


# Class X Hindi Course A (002) SQP 2024-25, HindiCourseA-SQP.pdf, read with
# PyMuPDF: p. 1 General Instructions -- 15 questions in four khands;
# Khand Ka Q1-2, two unseen passages of 7 marks, each three 1-mark and two
# 2-mark sub-questions (pp. 1-4); Khand Kha Q3-6, any 4 of 5 one-mark
# sub-questions each (pp. 4-5); Khand Ga Q7/Q9 five 1-mark extract MCQs each,
# Q8/Q10 any 3 of 4 two-mark answers, Q11 any 2 of 3 four-mark answers
# (pp. 5-9); Khand Gha Q12 a paragraph on one of three topics (6), Q13 letter
# and Q14 CV / e-mail (5 each), Q15 advertisement / message (4), Q13-15 each
# with an OR (pp. 9-10). (questions printed, marks each, attempted, ORs)
HINDI_A_2024_25 = [(6, 1, 6, 0), (4, 2, 4, 0), (20, 1, 16, 0), (10, 1, 10, 0),
                   (8, 2, 6, 0), (3, 4, 2, 0), (3, 6, 1, 0), (2, 5, 2, 2), (1, 4, 1, 1)]


def test_hindi_presets_follow_the_course_a_sqp_and_cite_it():
    by_key = {(p.grade, p.subject, p.exam_type): p for p in presets()}
    for key in ((10, "Hindi", "annual"), (9, "Hindi", "annual"), (10, "Hindi", "half_yearly")):
        p = by_key[key]
        rows = [(s.question_count, s.marks_each, s.attempts, s.choice_count) for s in p.sections]
        assert rows == HINDI_A_2024_25, (key, rows)
        assert p.total_marks == 80
        assert "ClassX_2024_25/HindiCourseA-SQP.pdf" in p.source, p.source
        assert "does not extract" not in p.source
    src = by_key[(10, "Hindi", "annual")].source
    for page in ("p. 1", "pp. 1-4", "pp. 4-5", "pp. 5-9", "pp. 9-10"):
        assert page in src, (page, src)
    assert "HindiCourseB-SQP.pdf" in src           # Course B differs, and says where


@pytest.mark.skipif(not (_SQP_DIR / "ClassX_2024_25" / "HindiCourseA-SQP.pdf").exists(),
                    reason="the CBSE SQP PDFs are not in this checkout")
def test_the_hindi_sqp_pdf_says_what_the_hindi_preset_says():
    """The Devanagari extracts with some conjuncts mis-mapped, so this reads
    the marks lines ("4x1=4") and the OR markers, which extract cleanly."""
    import re

    import fitz

    doc = fitz.open(str(_SQP_DIR / "ClassX_2024_25" / "HindiCourseA-SQP.pdf"))
    pages = [page.get_text() for page in doc]
    doc.close()
    text = "\n".join(pages)
    marks = re.findall(r"(\d)x(\d)=(\d+)", text)
    assert marks == [("4", "1", "4")] * 4 + [("5", "1", "5"), ("3", "2", "6"), ("5", "1", "5"),
                                             ("3", "2", "6"), ("2", "4", "8"), ("1", "6", "6"),
                                             ("1", "5", "5"), ("1", "5", "5"), ("1", "4", "4")]
    assert len(re.findall(r"^\s*अथवा\s*$", pages[-1], re.M)) == 3        # Q13-15, p. 10
    assert "15" in pages[0] and "80" in pages[0]


@needs_real_bank
def test_a_short_sections_fixes_keep_the_mix_fixes_without_repeating_one(real_class10_pools):
    """`_diagnose`'s fixes used to replace the competency (mix) fixes of a
    short section instead of joining them; merged now, one per kind and value."""
    for p in presets(grade=10):
        if p.subject == "Hindi":
            continue
        report, _ = _real_plan(real_class10_pools, p.id)
        for s in report.sections:
            keys = [(f.kind, f.marks_each, f.question_count, f.choice_count) for f in s.fixes]
            assert len(keys) == len(set(keys)), (p.id, s.title, keys)
            if s.shortfall:
                assert any(f.kind == "reduce_count" for f in s.fixes), (p.id, s.title)


# ---- review of 6c86e99: what the paper prints, and fixes a client can apply

def test_preset_instructions_describe_the_paper_that_was_printed():
    """The preset's instructions were written once from `choice_count` and
    stamped unchanged, so a section whose ORs the bank could not pair still
    printed "4 of them offer an internal choice". Rebuilt from what was
    printed, a section says the ORs it carries and the questions it holds,
    and a section with nothing in it is not described at all."""
    from academicos.assessment.template_presets import get_preset, instructions_for

    t = get_preset(SS10)
    assert instructions_for(t.sections) == t.instructions
    printed = [(20, 0), (4, 1), (5, 0), (3, 0), (0, 0), (0, 0)]
    lines = instructions_for(t.sections, printed).splitlines()
    assert lines[0] == "This question paper has 4 sections."
    by_title = {line.split(":")[0]: line for line in lines[1:-1]}
    assert set(by_title) == {s.title for s in t.sections[:4]}
    assert "1 of them offers" in by_title["Section B - Very short answer"]
    assert "OR" not in by_title["Section C - Short answer"]
    d = by_title["Section D - Long answer"]
    assert "3 questions" in d and "OR" not in d, d


def test_a_relax_type_fix_names_the_types_to_apply():
    """`relax_type` carried only an English label; a client could not apply
    it without parsing the sentence. It now carries the section's types
    after relaxing, like `change_marks` carries its mark value."""
    report, _ = _plan_preset(SS10, _src_bank())
    d = next(s for s in report.sections if s.title == "Section D - Long answer")
    relax = next(f for f in d.fixes if f.kind == "relax_type")
    assert relax.question_types == ["long_answer", "very_long_answer", "case_study"]
    assert relax.model_dump(by_alias=True)["questionTypes"] == relax.question_types


@needs_real_bank
def test_the_real_banks_map_and_case_sections_are_never_offered_the_other_kind(
        real_class10_pools):
    """A map question only ever fills a map section, and a source passage
    cannot answer a map-skill section, so neither is a reason or a fix.
    Before: Section F offered "the 45 5-mark question(s) that read as source
    / case based" and Section E "the 3 4-mark question(s) that are map
    questions".

    Re-measured after the question-bank merge (2026-09-23): Class 10 Social
    Science now holds no map question at ANY mark value (14 questions: 12
    1-mark MCQ, 2 3-mark short answers), where before it held three at 4
    marks. So the "change the marks" fix that used to point at them is now
    correctly not offered at all -- which is the same guard from the other
    side: a fix is never invented out of the wrong kind of question."""
    report, _ = _real_plan(real_class10_pools, SS10)
    by_title = {s.title: s for s in report.sections}
    f = by_title["Section F - Map skill"]
    assert f.shortfall and "source" not in f.reason, f.reason
    assert "5-mark map based" in f.reason, f.reason
    assert not any(x.kind == "relax_type" for x in f.fixes), f.fixes
    assert not any(x.kind == "change_marks" for x in f.fixes), f.fixes
    e = by_title["Section E - Case based"]
    assert e.shortfall and "map" not in e.reason, e.reason
    assert not any("map" in x.label for x in e.fixes), e.fixes
    for s in report.sections:
        for x in s.fixes:
            if x.kind == "relax_type":
                assert x.question_types and "map_based" not in x.question_types, (s.title, x)


@needs_real_bank
@needs_real_bank
def test_the_real_banks_class_10_sets_are_distinct_papers(tmp_path, monkeypatch, real_class10_pools):
    """N-2-5 on the served bank: before, B and C held 100% of set A's
    questions. Measured on this bank (2026-09-30): Maths 10 half-yearly
    repeats none of set A's questions in B or C; Science 10 annual repeats
    one in each (2.9% of the set: the only keyed 2-mark question the bank
    has, which Section B needs in every set)."""
    for subject, pool in real_class10_pools.items():
        monkeypatch.setitem(pool_mod._CACHE, (subject, "X"), pool)
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        for preset, most in (("preset:cbse:10:mathematics:half_yearly", 0),
                             ("preset:cbse:10:science:annual", 2)):
            r = client.post(GEN, json={"templateId": preset, "setCount": 3, "allowGaps": True},
                            headers=t1)
            assert r.status_code == 200, r.text
            paper = r.json()["paper"]
            ids = [{i for s in p["sections"] for q in s["questions"]
                    for i in (q["questionId"], q.get("internalChoiceQuestionId")) if i}
                   for p in paper["sets"]]
            shapes = [[(len(s["questions"]), s["totalMarks"]) for s in p["sections"]]
                      for p in paper["sets"]]
            assert shapes[0] == shapes[1] == shapes[2], preset
            earlier: set[str] = set()
            for p, mine in zip(paper["sets"], ids):
                assert paper["setOverlap"][p["setLabel"]] == len(mine & earlier) <= most, preset
                earlier |= mine


def test_the_real_papers_instructions_match_the_ors_it_prints(
        tmp_path, monkeypatch, real_class10_pools):
    """Social Science Section C pairs 0 of its 1 OR on the merged bank -- the
    two 3-mark questions it has are both printed as compulsory, leaving none
    to offer -- and the General Instructions printed on the paper must not
    promise it. Before the question-bank merge the unpaired ORs were Section
    D's 4, which the merged bank cannot fill at all (2026-09-23)."""
    for subject, pool in real_class10_pools.items():
        monkeypatch.setitem(pool_mod._CACHE, (subject, "X"), pool)
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        report = client.post(f"{BASE}/{SS10}/availability", json={}, headers=t1).json()
        r = client.post(GEN, json={"templateId": SS10, "allowGaps": True}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
    c = next(s for s in report["sections"] if s["title"] == "Section C - Short answer")
    assert c["choicesNeeded"] > c["choicesFilled"] == 0
    for p in [paper] + paper["sets"]:
        lines = p["metadata"]["instructions"].splitlines()
        printed = [s for s in report["sections"] if s["filled"]]
        assert lines[0] == f"This question paper has {len(printed)} sections."
        for s in report["sections"]:
            line = next((x for x in lines if x.startswith(_printed_title(s, report) + ":")), None)
            if not s["filled"]:
                assert line is None, line
                continue
            assert _n(s["filled"], "question") in line, line
            if s["choicesFilled"]:
                assert f"{_n(s['choicesFilled'], 'of them offer', 'of them offers')} an internal choice" \
                    in line, line
            else:
                assert "OR" not in line, line


def _n(n: int, many: str, one: str = "") -> str:
    """How the printed instructions count: "1 question", "3 questions"
    (they said "question(s)" until QA P-33)."""
    return f"{n} {(one or many) if n == 1 else (many if one else many + 's')}"


def _printed_title(section: dict, report: dict) -> str:
    """The name a report section prints under: the paper letters the
    sections it prints in order, and the title's own "Section X" says that
    letter (audit D44). A section that prints nothing keeps its title."""
    from academicos.assessment.paper import lettered
    filled = [s["sectionId"] for s in report["sections"] if s["filled"]]
    if section["sectionId"] not in filled:
        return section["title"]
    return lettered(section["title"], chr(ord("A") + filled.index(section["sectionId"])))


# ---- review of 9b2f64c: a copied preset's instructions after the teacher edits it

def _assert_instructions_describe(lines: list[str], sections: list[dict]) -> None:
    printed = [s for s in sections if s["filled"]]
    assert lines[0] == f"This question paper has {len(printed)} sections.", lines
    for s in sections:
        title = _printed_title(s, {"sections": sections})
        line = next((x for x in lines if x.startswith(title + ":")), None)
        if not s["filled"]:
            assert line is None, line
            continue
        assert f"{_n(s['filled'], 'question')} of {_n(s['marksEach'], 'mark')}" in line, line
        if s["choicesFilled"]:
            assert f"{_n(s['choicesFilled'], 'of them offer', 'of them offers')} an internal choice" \
                in line, line
        else:
            assert "OR" not in line, line


def _ss_records() -> list[dict]:
    return ([_record(f"ss1_{i}", 1, "ch1", subject="Social Science",
                     qtype="very_short_answer") for i in range(22)]
            + [_record(f"ss2_{i}", 2, "ch1", subject="Social Science") for i in range(5)]
            + [_record(f"ss3_{i}", 3, "ch1", subject="Social Science") for i in range(6)])


def test_a_copied_preset_edited_by_the_teacher_prints_instructions_for_its_paper(
        tmp_path, monkeypatch):
    """Duplicate, then edit a section (here the product's own change-marks
    fix on Section E): the copy's instructions are still the preset's
    generated text, but no longer equal to what the edited sections would
    generate, so they were taken for the teacher's own words and printed
    "Section E - Case based: 3 question(s) of 4 mark(s) each" and Section
    D's four ORs on a paper that had neither."""
    monkeypatch.setitem(pool_mod._CACHE, ("Social Science", "X"), _fixture_pool(_ss_records()))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        copy = client.post(f"{BASE}/{SS10}/duplicate", json={}, headers=t1).json()
        e = next(s for s in copy["sections"] if s["title"].startswith("Section E"))
        e["marksEach"] = 5
        copy["totalMarks"] += 3
        r = client.put(f"{BASE}/{copy['id']}", json=copy, headers=t1)
        assert r.status_code == 200, r.text
        report = client.post(f"{BASE}/{copy['id']}/availability", json={}, headers=t1).json()
        r = client.post(GEN, json={"templateId": copy["id"], "allowGaps": True}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
    for p in [paper] + paper["sets"]:
        lines = p["metadata"]["instructions"].splitlines()
        _assert_instructions_describe(lines, report["sections"])
        assert not any("4 marks" in x for x in lines), lines


def test_instructions_the_teacher_rewrites_on_a_copy_print_as_written(tmp_path, monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Social Science", "X"), _fixture_pool(_ss_records()))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        copy = client.post(f"{BASE}/{SS10}/duplicate", json={}, headers=t1).json()
        copy["instructions"] = "Answer in your own words.\nMaps are attached."
        saved = client.put(f"{BASE}/{copy['id']}", json=copy, headers=t1).json()
        # Editing sections afterwards keeps the teacher's words theirs.
        saved["sections"][0]["title"] = "Section A - Objective"
        client.put(f"{BASE}/{copy['id']}", json=saved, headers=t1)
        r = client.post(GEN, json={"templateId": copy["id"], "allowGaps": True}, headers=t1)
        assert r.status_code == 200, r.text
        assert r.json()["paper"]["metadata"]["instructions"] == (
            "Answer in your own words.\nMaps are attached.")


# ---- "Whole syllabus" is the class's current syllabus first (QA P-04) --------

def test_a_whole_syllabus_paper_prints_off_syllabus_questions_only_to_fill():
    """A Class 10 Science annual printed three Exemplar questions on Sources
    of Energy, a chapter CBSE dropped, and the bank's unmatched ones ranked
    with the rest. They rank last now, and a section that needs one says so."""
    from academicos.assessment.chapter_filing import ChapterFiling

    known = sorted(ChapterFiling.for_class("Science", 10).known)
    if not known:
        pytest.skip("no Class 10 Science syllabus in this checkout")
    on = [_q(f"on{i}", 3, f"Syllabus item number {i} about {w}?", "short_answer")
          for i, w in enumerate(("acids", "lenses", "nephrons"))]
    off = [_q(f"off{i}", 3, f"Dropped item number {i} about {w}?", "short_answer")
           for i, w in enumerate(("tidal energy", "biogas plants", "solar cookers"))]
    for q in on:
        q.chapter_ids = [known[0]]
    for q in on + off:
        q.subject, q.quality_score = "Science", 0.5
    for q in off:                    # the best-rated questions, as the Exemplar's were
        q.quality_score = 0.99
    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope

    def section_of(n: int):
        t = PaperTemplateDraft.model_validate(_draft(
            totalMarks=3 * n, scope={}, sections=[_section("Section B", n, 3)]))
        bank = on + off
        report, plans = plan(t, "tpl", bank, build_scope_filter(TemplateScope(), bank))
        return {q.id for q in plans[0].picked}, report.sections[0].notes

    picked, notes = section_of(3)
    assert picked == {"on0", "on1", "on2"}
    assert not any("not matched to a chapter" in n for n in notes), notes
    picked, notes = section_of(4)
    assert {"on0", "on1", "on2"} <= picked and len(picked & {"off0", "off1", "off2"}) == 1
    assert any("1 question is not matched to a chapter" in n for n in notes), notes


# ---- a paper spreads over the chapters (QA R-03) -----------------------------

import dataclasses  # noqa: E402

def _chaptered(qid: str, chapter: str, *, cbe: bool = False):
    q = _q(qid, 1, f"Spread item {qid}", "very_short_answer")
    q.chapter_ids, q.subject = [chapter], "Science"
    if cbe:
        q.question_bank_id = "cbe:Item-Bank---Science-Class-10.pdf"
    return q


def _six_of(bank, stale=frozenset()):
    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope
    t = PaperTemplateDraft.model_validate(_draft(
        totalMarks=6, scope={}, sections=[_section("Section A", 6, 1, competencyShare=0.0)]))
    scope = dataclasses.replace(build_scope_filter(TemplateScope(), bank), last_resort=frozenset())
    _, plans = plan(t, "tpl", bank, scope, stale=stale)
    return [q.id for q in plans[0].picked]


def test_a_paper_takes_the_chapters_in_turn_and_so_does_the_next():
    """A whole-syllabus Class 10 Science annual printed 29 of its 31 questions
    from one chapter: the bank's ids run chapter by chapter, most questions
    share one quality score, and once a teacher's recent questions went last
    each new paper took the next block of ids."""
    from collections import Counter
    bank = [_chaptered(f"{c}{i}", f"chap-{c}") for c in "abc" for i in range(4)]
    first = _six_of(bank)
    assert Counter(q[0] for q in first) == {"a": 2, "b": 2, "c": 2}, first
    second = _six_of(bank, stale=frozenset(first))
    assert not set(first) & set(second)
    assert Counter(q[0] for q in second) == {"a": 2, "b": 2, "c": 2}, second


def test_a_recent_competency_question_comes_back_only_to_reach_cbses_half():
    """A section that names no share takes competency-based questions first,
    but one from the teacher's recent papers only up to CBSE's 50%: preferring
    them all reprinted every one of a small bank's on each new paper."""
    from academicos.assessment.competency import is_competency_question
    from academicos.assessment.paper_templates import build_scope_filter, plan
    from academicos.assessment.schemas import TemplateScope
    bank = ([_chaptered(f"c{i}", "chap-a", cbe=True) for i in range(4)]
            + [_chaptered(f"p{i}", "chap-b") for i in range(8)])
    t = PaperTemplateDraft.model_validate(_draft(
        totalMarks=4, scope={}, sections=[_section("Section A", 4, 1)]))
    scope = dataclasses.replace(build_scope_filter(TemplateScope(), bank), last_resort=frozenset())
    _, fresh = plan(t, "tpl", bank, scope)
    assert sum(is_competency_question(q) for q in fresh[0].picked) == 4
    _, again = plan(t, "tpl", bank, scope, stale=frozenset({"c0", "c1", "c2", "c3"}))
    picked = again[0].picked
    assert sum(is_competency_question(q) for q in picked) == 2, [q.id for q in picked]
