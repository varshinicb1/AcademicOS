"""A quick paper holds the marks asked for whenever the bank can (D57).

Audit 2026-10-01: a quick Science 10 paper asked for 40 marks printed 28. The
CBSE layout asked for five 2-mark questions and one 4-mark one; the served
bank holds one 2-mark Science 10 question and no 4-mark one, and hundreds of
1-, 3- and 5-mark ones. A preset asked for other marks than its own printed
its own (a weekly test asked for 40 printed 25; a board pattern asked for 40
printed 60 under a header saying 40).

Now a section the bank cannot fill moves its marks to sections it can --
each section still "N questions of M marks" -- and only when the bank truly
cannot make the total does the paper print short, with the shortfall named
section by section, and a preview shows it before anything is saved.

The served bank is read, never written.
"""
from __future__ import annotations

import pytest

from academicos.assessment import selection
from test_paper_generation_honesty import (  # noqa: F401 - `served` is a fixture
    _auth, _bp, _client_for, _q, _section, served,
)

QUICK = "/api/v1/papers/quick-generate"


def _sections_valid(paper: dict) -> None:
    """Every section is one marks value, its total is its questions' marks,
    none is empty, and they are lettered A, B, C... in order."""
    assert paper["sections"]
    for i, s in enumerate(paper["sections"]):
        marks = {q["marks"] for q in s["questions"]}
        assert len(marks) == 1, (s["label"], marks)
        assert s["totalMarks"] == sum(q["marks"] for q in s["questions"])
        assert s["label"] == chr(ord("A") + i)


@pytest.mark.parametrize("req", [
    {"totalMarks": 40},                                   # the audit's paper: 28 of 40
    {"totalMarks": 20},
    {"totalMarks": 80},
    {"totalMarks": 40, "examType": "weekly_test"},        # the preset printed its own 25
    {"totalMarks": 40, "examType": "board"},              # printed 60 under "40"
    {"totalMarks": 50, "examType": "monthly_test"},
])
def test_a_science_10_quick_paper_holds_the_marks_asked(served, tmp_path, monkeypatch, req):
    with _client_for(tmp_path, monkeypatch, served["Science"]) as client:
        r = client.post(QUICK, headers=_auth(client), json={"subject": "Science", "grade": 10, **req})
    assert r.status_code == 200, r.text
    paper = r.json()
    held = sum(s["totalMarks"] for s in paper["sections"])
    assert held == paper["metadata"]["totalMarks"] == req["totalMarks"], paper["warnings"]
    assert paper["marksAsked"] == req["totalMarks"]
    assert paper["shortfall"] == []
    assert f"Maximum Marks: {req['totalMarks']}" in paper["formattedContent"]
    _sections_valid(paper)


def test_a_rebalanced_paper_says_what_it_changed(served, tmp_path, monkeypatch):
    """The audit's bank held one 2-mark Science 10 question and no 4-mark one. With the model-written
    questions (corpus/ai-cbse-9-10) the served bank fills the 40 marks as asked, so the rebalancing path
    is exercised on the bank as it was, without them."""
    from academicos.assessment.pool import QuestionPool

    as_audited = QuestionPool(questions=[q for q in served["Science"].questions
                                         if not str((q.record or {}).get("id") or "").startswith("ai:")])
    with _client_for(tmp_path, monkeypatch, as_audited) as client:
        paper = client.post(QUICK, headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 40}).json()
    [note] = [w for w in paper["warnings"] if w.startswith("To make the 40 marks asked for")]
    assert "2-mark and 4-mark" in note, note
    assert "(asked: A 10 × 1, B 5 × 2, C 2 × 3, D 2 × 5, E 1 × 4)" in note, note
    printed = ", ".join(f"{s['label']} {len(s['questions'])} × {s['questions'][0]['marks']}"
                        for s in paper["sections"])
    assert f"It prints {printed} " in note, (printed, note)


# ---- the bank truly cannot -------------------------------------------------

def _small_pool():
    """Three 1-mark and two 3-mark questions: 9 marks at most."""
    from test_paper_swap_pick import _pool, _rec
    return _pool([_rec(f"o{i}", 1, "ch1", i) for i in range(3)]
                 + [_rec(f"t{i}", 3, "ch1", 5 + i) for i in range(2)])


def test_when_the_bank_cannot_the_shortfall_is_named_by_section(tmp_path, monkeypatch):
    with _client_for(tmp_path, monkeypatch, _small_pool()) as client:
        paper = client.post(QUICK, headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 20}).json()
    assert paper["metadata"]["totalMarks"] == 9          # all the bank holds
    assert paper["marksAsked"] == 20
    by_label = {s["label"]: s for s in paper["shortfall"]}
    # Asked: A 5 x 1, B 2 x 2, C 2 x 3, D 1 x 5 (default_sections(20)).
    assert set(by_label) == {"A", "B", "D"}, paper["shortfall"]
    assert (by_label["A"]["asked"], by_label["A"]["printed"], by_label["A"]["available"]) == (5, 3, 3)
    assert (by_label["B"]["printed"], by_label["B"]["missingMarks"], by_label["B"]["available"]) == (0, 4, 0)
    assert by_label["D"]["marksEach"] == 5 and by_label["D"]["missingMarks"] == 5
    assert "the bank holds 0 question(s) of 2 mark(s)" in by_label["B"]["reason"]
    assert any(w.startswith("This paper holds 9 of the 20 marks asked for") for w in paper["warnings"])
    assert any(w.startswith("Section B (Very Short Answer) as asked prints short") for w in paper["warnings"])


def test_a_preview_says_what_the_paper_would_hold_and_saves_nothing(tmp_path, monkeypatch):
    from academicos.assessment.audit_log import get_audit_log
    with _client_for(tmp_path, monkeypatch, _small_pool()) as client:
        h = _auth(client)
        preview = client.post(QUICK, headers=h, json={
            "subject": "Science", "grade": 10, "totalMarks": 20, "preview": True})
        assert preview.status_code == 200, preview.text
        body = preview.json()
        assert body["preview"] is True and body["marksAsked"] == 20
        assert [s["label"] for s in body["shortfall"]] == ["A", "B", "D"]
        assert client.get(f"/api/v1/papers/{body['id']}", headers=h).status_code == 404
        assert client.get("/api/v1/assessments", headers=h).json() == []
        assert get_audit_log(tmp_path).for_action("quick_paper_generated") == []

        saved = client.post(QUICK, headers=h, json={
            "subject": "Science", "grade": 10, "totalMarks": 20}).json()
        assert saved["preview"] is False
        ids = lambda p: [q["questionId"] for s in p["sections"] for q in s["questions"]]  # noqa: E731
        assert ids(saved) == ids(body), "the preview is the paper Save makes"
        assert client.get(f"/api/v1/papers/{saved['id']}", headers=h).status_code == 200


# ---- the selection rule itself -----------------------------------------------

def test_a_short_section_moves_its_marks_to_sections_the_bank_can_fill():
    bank = ([_q(f"one{i}", 1) for i in range(30)] + [_q("two0", 2)]
            + [_q(f"three{i}", 3) for i in range(10)])
    asked = _bp([_section("A", 1, 10), _section("B", 2, 5), _section("C", 3, 2)], "standard")
    assert asked.total_marks == 26
    bp, res, notes = selection.fill_to_marks(bank, asked)
    assert sum(q.marks for q in res.selected_questions) == 26
    assert all(s.total_marks == s.question_count * s.marks_per_question for s in bp.sections)
    assert sum(s.total_marks for s in bp.sections) == 26
    assert [s.marks_per_question for s in bp.sections] == [1, 2, 3]
    assert next(s for s in bp.sections if s.marks_per_question == 2).question_count == 1
    assert notes and "too few 2-mark questions" in notes[0]
    # The bank's questions are never written: OR pairings go on copies.
    assert all("internal_choice_id" not in q.metadata for q in bank)


def test_a_full_layout_is_left_as_asked():
    bank = [_q(f"one{i}", 1) for i in range(12)] + [_q(f"three{i}", 3) for i in range(4)]
    asked = _bp([_section("A", 1, 10), _section("B", 3, 2)], "standard")
    bp, res, notes = selection.fill_to_marks(bank, asked)
    assert bp is asked and notes == []
    assert sum(q.marks for q in res.selected_questions) == 16


def test_marks_no_section_asked_for_are_used_only_when_the_asked_ones_cannot_make_the_total():
    bank = [_q(f"two{i}", 2) for i in range(10)] + [_q(f"five{i}", 5) for i in range(3)]
    asked = _bp([_section("A", 2, 2), _section("B", 3, 3)], "standard")      # 13 marks
    bp, res, notes = selection.fill_to_marks(bank, asked)
    assert sum(q.marks for q in res.selected_questions) == 13
    assert sorted(s.marks_per_question for s in bp.sections) == [2, 5]      # 4 x 2 + 1 x 5
    assert notes
