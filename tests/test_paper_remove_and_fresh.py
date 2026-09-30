"""Remove a question from a generated paper, and "make another like this"
with fresh questions (Task 902, step 4 and step 5).

The builder's paper step offers Swap, Pick and **Remove** on every question;
its finish step offers "Make another like this" -- the same template, fresh
questions. Generation is deterministic (`paper_templates._order`: quality,
then id), so generating again with the same template and chapters printed
the same paper; these tests pin what the server now promises:

  * generate-from-template with `avoidQuestionIds` prints questions not in
    that list while the bank has them, and reuses one only when it has
    nothing else -- saying so in the notes, never leaving the paper short
    for freshness' sake;
  * removing "N" takes question N (and its OR alternative) off the paper and
    every set, renumbers what follows, rebuilds the answer key under the new
    numbers, and lowers the section's and the paper's marks;
  * removing "N_OR" keeps question N and drops only its alternative -- in a
    set that printed the pair the other way round, the paper's question is
    put back as the compulsory one;
  * a removed question is never brought back by a swap, the assessment
    records the paper as it now is, and a PDF rendered before the removal is
    not served after it.

Hermetic: the fixture pool from tests/test_paper_swap_pick.py.
"""
from __future__ import annotations

from test_paper_swap_pick import FIXTURE, GEN, _at, _generate, _on_paper, _swap, seeded  # noqa: F401
from test_paper_templates import _boot_client, _register

BASE = "/api/v1/schools/school_1/teacher-templates"


def _remove(client, headers, paper_id: str, slot: str):
    return client.delete(f"/api/v1/papers/{paper_id}/questions/{slot}", headers=headers)


def _printed(paper: dict) -> list[tuple[int, str, str | None]]:
    return [(q["displayNumber"], q["questionId"], q.get("internalChoiceQuestionId"))
            for s in paper["sections"] for q in s["questions"]]


def _key_matches_print(paper: dict) -> None:
    """Every answer-key entry is its own printed question's, and nothing else."""
    want = set()
    for n, qid, alt in _printed(paper):
        want.add(str(n))
        assert paper["answerKey"][str(n)].startswith(f"model answer for {qid}"), paper["id"]
        if alt:
            want.add(f"{n}_OR")
            assert paper["answerKey"][f"{n}_OR"] == f"model answer for {alt}", paper["id"]
    assert set(paper["answerKey"]) == want, paper["id"]


# ------------------------------------------------------------------ fresh questions

def test_generate_with_avoid_ids_prints_fresh_questions_and_reuses_only_when_it_must(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json={
            "name": "Unit test", "grade": 10, "subject": "Science", "examType": "unit_test",
            "totalMarks": 8, "durationMinutes": 40,
            "sections": [{"title": "Section A", "questionCount": 2, "marksEach": 1},
                         {"title": "Section B", "questionCount": 2, "marksEach": 3,
                          "choiceCount": 1}],
            "scope": {"chapterIds": ["ch1"]}}, headers=t1).json()["id"]
        first = client.post(GEN, json={"templateId": tid}, headers=t1).json()
        again = client.post(GEN, json={"templateId": tid}, headers=t1).json()
        # Without the list the generator is deterministic: the same paper.
        assert _on_paper(again["paper"]) == _on_paper(first["paper"])

        used = sorted(_on_paper(first["paper"]))
        r = client.post(GEN, json={"templateId": tid, "avoidQuestionIds": used}, headers=t1)
        assert r.status_code == 200, r.text
        fresh = r.json()
        a_first = {q for _, q, _ in _printed(first["paper"]) if q.startswith("o")}
        a_fresh = {q for _, q, _ in _printed(fresh["paper"]) if q.startswith("o")}
        # Section A: ch1 has six keyed 1-mark questions, so two new ones.
        assert len(a_fresh) == 2 and not a_fresh & a_first, (a_first, a_fresh)
        # Section B: five 3-mark questions for 2 + 1 OR, three used last time.
        # The two compulsory ones are new; the OR has to be one of the old ones.
        b = [(q, alt) for _, q, alt in _printed(fresh["paper"]) if q.startswith("t")]
        assert {q for q, _ in b} == {"t3", "t4"}, b
        alt = next(a for _, a in b if a)
        assert alt in used
        assert fresh["complete"] is True                  # never short for freshness
        assert any("last paper" in n.lower() and alt in n for n in fresh["notes"]), fresh["notes"]
        # The availability the check shows is unchanged: freshness reorders,
        # it never makes a section short.
        assert [s["filled"] for s in fresh["availability"]["sections"]] == \
            [s["filled"] for s in first["availability"]["sections"]]


# ------------------------------------------------------------------ remove

def test_removing_a_question_renumbers_the_paper_and_every_set_and_lowers_the_marks(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1, setCount=2)
        pid = paper["id"]
        assert client.post(f"/api/v1/papers/{pid}/export/pdf", headers=t1).status_code == 200
        before = _printed(paper)
        gone = _at(paper, 1)["questionId"]

        r = _remove(client, t1, pid, "1")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["slot"] == "1" and body["removedQuestionIds"] == [gone]
        edited = body["paper"]
        after = _printed(edited)
        # Everything after Q1 moves up one number, in the same order.
        assert [n for n, _, _ in after] == [1, 2, 3]
        assert [(q, alt) for _, q, alt in after] == [(q, alt) for _, q, alt in before[1:]]
        a, b = edited["sections"]
        assert a["totalMarks"] == 1 and b["totalMarks"] == 6
        assert edited["metadata"]["totalMarks"] == 7
        _key_matches_print(edited)
        assert gone not in edited["formattedContent"]

        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json()
        for s in (set_b, *edited["sets"]):
            assert gone not in _on_paper(s)
            assert _on_paper(s) == _on_paper(edited)
            assert [n for n, _, _ in _printed(s)] == [1, 2, 3]
            assert s["metadata"]["totalMarks"] == 7
            _key_matches_print(s)

        # The old PDF is not served; the assessment holds the paper as it is.
        assert client.get(f"/api/v1/papers/{pid}/file", headers=t1).status_code == 404
        asm = client.get(f"/api/v1/assessments/{paper['assessmentId']}", headers=t1).json()
        assert gone not in asm["selectedQuestionIds"]
        # A swap never brings a removed question back.
        for _ in range(3):
            s = _swap(client, t1, pid, "1")
            if s.status_code != 200:
                break
            assert s.json()["questionId"] != gone


def test_removing_a_question_with_an_or_takes_both_and_the_last_one_is_refused(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        pid = paper["id"]
        q4 = _at(paper, 4)
        r = _remove(client, t1, pid, "4")
        assert r.status_code == 200, r.text
        assert r.json()["removedQuestionIds"] == [q4["questionId"], q4["internalChoiceQuestionId"]]
        edited = r.json()["paper"]
        assert not {q4["questionId"], q4["internalChoiceQuestionId"]} & _on_paper(edited)
        _key_matches_print(edited)

        assert _remove(client, t1, pid, "9").status_code == 404
        for slot in ("3", "2"):
            assert _remove(client, t1, pid, slot).status_code == 200
        last = _remove(client, t1, pid, "1")
        assert last.status_code == 409 and "last question" in last.text
        # A section left with no question is not printed as an empty heading.
        left = client.get(f"/api/v1/papers/{pid}", headers=t1).json()
        assert [len(s["questions"]) for s in left["sections"]] == [1]


def _headings(paper: dict) -> list[tuple[str, str]]:
    return [(s["label"], s["name"]) for s in paper["sections"]]


def test_a_section_name_says_the_letter_its_heading_prints(tmp_path, monkeypatch, seeded):
    """Audit D44: on a paper with an empty template section the heading
    letter and the section's own name disagreed -- "SECTION B" over
    "(Section C - Short answer ...)" -- because the paper letters the
    sections it prints in order and the name kept the template's letter.
    The same happens when removing a section's last question."""
    import fitz
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json={
            "name": "Gap", "grade": 10, "subject": "Science", "examType": "custom",
            "totalMarks": 10, "durationMinutes": 40,
            "sections": [{"title": "Section A - Objective", "questionCount": 2, "marksEach": 1},
                         {"title": "Section B - Very short answer", "questionCount": 1, "marksEach": 2},
                         {"title": "Section C - Short answer", "questionCount": 2, "marksEach": 3}],
            "scope": {"chapterIds": ["ch1"]}}, headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid, "allowGaps": True}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]                      # the bank has no 2-mark question
        assert _headings(paper) == [("A", "Section A - Objective"), ("B", "Section B - Short answer")]
        pid = paper["id"]
        assert client.post(f"/api/v1/papers/{pid}/export/pdf", headers=t1).status_code == 200
        pdf = client.get(f"/api/v1/papers/{pid}/file", headers=t1).content
        with fitz.open(stream=pdf, filetype="pdf") as doc:
            text = " ".join("".join(p.get_text() for p in doc).split())
        assert "SECTION B (Section B - Short answer" in text and "Section C" not in text

        # Removing Section A's two questions leaves Section B, printed as A.
        for _ in range(2):
            assert _remove(client, t1, pid, "1").status_code == 200
        left = client.get(f"/api/v1/papers/{pid}", headers=t1).json()
        assert _headings(left) == [("A", "Section A - Short answer")]


def test_removing_an_or_alternative_keeps_the_question_in_the_paper_and_every_set(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1, setCount=2)
        pid = paper["id"]
        q4 = _at(paper, 4)
        primary, alt = q4["questionId"], q4["internalChoiceQuestionId"]
        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json()
        # Set B prints OR pairs the other way round: the case this must handle.
        assert any(q == alt and a == primary for _, q, a in _printed(set_b)), _printed(set_b)

        r = _remove(client, t1, pid, "4_OR")
        assert r.status_code == 200, r.text
        assert r.json()["removedQuestionIds"] == [alt]
        edited = r.json()["paper"]
        assert _at(edited, 4)["questionId"] == primary
        assert _at(edited, 4)["internalChoiceQuestionId"] is None
        assert edited["metadata"]["totalMarks"] == paper["metadata"]["totalMarks"]
        _key_matches_print(edited)

        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json()
        assert _on_paper(set_b) == _on_paper(edited)
        assert all(a is None for _, _, a in _printed(set_b))
        _key_matches_print(set_b)
