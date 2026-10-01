"""Swapping and picking one question on a generated paper (Task 903).

The builder (Task 902) lets a teacher replace any question on a generated
paper in one tap ("swap": the next best question for that slot) or put a
question of their own choosing there ("pick"). These tests pin what the
server promises for both:

  * swap returns a different question with the slot's marks, kind and scope,
    never one already on the paper, never one it swapped out before, and
    says "no alternative in this scope" with the counts when there is none;
  * pick refuses a question with no verified answer key (PRD rule Q1), a
    question already on the paper, and a question whose marks do not fit;
  * two near-identical stems never share a paper (a real pair from the
    served bank, ids cited below);
  * the answer key follows every edit, every set follows it, and a PDF
    rendered before the edit is never served after it;
  * on the real class 10 Science bank: generate, swap and pick timings
    (p50/p95 over 20 runs) are recorded, and the pool is not reloaded per
    request.

Hermetic except the timing test: the question pool is a fixture seeded into
`pool._CACHE`, as in tests/test_paper_templates.py.
"""
from __future__ import annotations

import statistics
import time
from pathlib import Path

import pytest

from academicos.assessment import pool as pool_mod
from academicos.models.academic import Question
from test_paper_templates import _boot_client, _register

BASE = "/api/v1/schools/school_1/teacher-templates"
GEN = "/api/v1/papers/generate-from-template"

# Distinct stems, so the near-duplicate guard never mistakes two fixture
# questions for one another (it compares the text, not the ids).
_TOPICS = [
    "why the colour of copper sulphate solution fades when an iron nail is dipped in it",
    "how the ciliary muscles change the focal length of the human eye lens",
    "the role of the placenta in the development of the human embryo",
    "why a current carrying conductor experiences a force in a magnetic field",
    "how ozone is formed in the upper atmosphere and why it is being depleted",
    "the difference between the arteries and the veins of the circulatory system",
    "why baking soda is used as an antacid for acidity in the stomach",
    "how a plano convex lens forms a real image of a distant tree",
    "the function of the nephron in filtering blood inside the kidney",
    "why decomposers are essential for recycling nutrients in an ecosystem",
    "how the resistance of a wire depends on its length and its thickness",
    "the reason soap forms scum with hard water but lather with rain water",
    "how auxins cause the shoot of a plant to bend towards the light",
    "why the sky appears blue on a clear day to an observer on the earth",
    "how the electrolytic refining of impure copper is carried out in practice",
    "the steps by which Mendel showed that traits are inherited independently",
]


def _rec(qid: str, marks: int, chapter: str, n: int, *, keyed: bool = True,
         quality: float = 0.8, difficulty: str = "medium",
         qtype: str = "short_answer", stem: str | None = None,
         subject: str = "Science") -> dict:
    return {
        "id": qid, "questionBankId": "fixture", "subject": subject, "grade": 10,
        "chapterIds": [chapter], "competencyIds": [], "bloomLevel": "understand",
        "difficulty": difficulty, "type": qtype,
        "stem": stem or f"Explain {_TOPICS[n % len(_TOPICS)]}.",
        "parts": [],
        "answerScheme": {
            "totalMarks": marks,
            "markingPoints": ([{"id": "mp1", "description": f"point for {qid}",
                                "marks": marks}] if keyed else []),
            "modelAnswer": f"model answer for {qid}" if keyed else "",
            # Rule Q1 is a published provenance AND real content
            # (qbank_routes.KEY_PROVENANCE): a keyed fixture record stands in
            # for a real board record and carries the board's label. The
            # unkeyed one holds nothing and stays unprintable either way.
            "provenance": "cbse_marking_scheme" if keyed else "teacher_authored",
        },
        "estimatedTimeMinutes": marks * 2, "marks": marks, "source": "cbse_board_paper",
        "qualityScore": quality, "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
    }


def _pool(records: list[dict]) -> pool_mod.QuestionPool:
    out = pool_mod.QuestionPool()
    for rec in records:
        q = Question(canonical_id=rec["id"], title=rec["stem"][:100],
                     source_text=rec["stem"], marks=float(rec["marks"]))
        out.questions.append(pool_mod.PoolQuestion(
            question=q, subject=rec["subject"], grade="X", academic_year="2024",
            chapter_id=rec["chapterIds"][0], chapter_name=None, chapter_confidence=0.9,
            text_hash=rec["id"], record=rec))
    return out


# 1-mark: o0..o5 in ch1 (quality falling with the index, so "next best" is
# deterministic), o6 in ch2 (out of scope), o7 in ch1 with no answer key.
# 3-mark: t0..t4 in ch1. 16 distinct stems between them.
FIXTURE = (
    [_rec(f"o{i}", 1, "ch1", i, quality=0.9 - i * 0.05) for i in range(6)]
    + [_rec("o6", 1, "ch2", 6), _rec("o7", 1, "ch1", 7, keyed=False, quality=0.99)]
    + [_rec(f"t{i}", 3, "ch1", 8 + i, quality=0.9 - i * 0.05) for i in range(5)]
)


def _template(**overrides) -> dict:
    body = {
        "name": "Unit test", "grade": 10, "subject": "Science", "examType": "unit_test",
        "totalMarks": 8, "durationMinutes": 40,
        "sections": [
            {"title": "Section A", "questionCount": 2, "marksEach": 1},
            {"title": "Section B", "questionCount": 2, "marksEach": 3, "choiceCount": 1},
        ],
        "scope": {"chapterIds": ["ch1"]},
    }
    body.update(overrides)
    return body


@pytest.fixture
def seeded(monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(FIXTURE))


def _generate(client, headers, **req) -> dict:
    tid = client.post(BASE, json=_template(), headers=headers).json()["id"]
    r = client.post(GEN, json={"templateId": tid, **req}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["paper"]


def _on_paper(paper: dict) -> set[str]:
    ids = set()
    for s in paper["sections"]:
        for q in s["questions"]:
            ids.add(q["questionId"])
            if q.get("internalChoiceQuestionId"):
                ids.add(q["internalChoiceQuestionId"])
    return ids


def _at(paper: dict, number: int) -> dict:
    return next(q for s in paper["sections"] for q in s["questions"]
                if q["displayNumber"] == number)


def _swap(client, headers, paper_id: str, slot: str):
    return client.post(f"/api/v1/papers/{paper_id}/questions/{slot}/swap", json={},
                       headers=headers)


def _pick(client, headers, paper_id: str, slot: str, qid: str):
    return client.post(f"/api/v1/papers/{paper_id}/questions/{slot}",
                       json={"questionId": qid}, headers=headers)


# ------------------------------------------------------------------ swap

def test_swap_returns_a_different_question_of_the_same_marks_type_and_scope(
        tmp_path, monkeypatch, seeded):
    by_id = {r["id"]: r for r in FIXTURE}
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        before = _at(paper, 1)["questionId"]

        r = _swap(client, t1, paper["id"], "1")
        assert r.status_code == 200, r.text
        body = r.json()
        new = body["questionId"]
        assert body["replacedQuestionId"] == before and new != before
        rec = by_id[new]
        assert rec["marks"] == 1 and rec["type"] == by_id[before]["type"]
        assert rec["chapterIds"] == ["ch1"]                 # in the paper's scope
        assert new != "o7"                                  # never an unkeyed one (Q1)
        # The paper itself changed, and is what GET returns from now on.
        assert _at(body["paper"], 1)["questionId"] == new
        stored = client.get(f"/api/v1/papers/{paper['id']}", headers=t1).json()
        assert _at(stored, 1)["questionId"] == new

        # Another school cannot touch it; a bad slot is a 404.
        outsider = _register(client, "school_2", "zed@example.com")
        assert _swap(client, outsider, paper["id"], "1").status_code == 403
        assert _swap(client, t1, paper["id"], "99").status_code == 404
        assert _swap(client, t1, "paper_missing", "1").status_code == 404


def test_swap_keeps_the_replaced_questions_type_when_the_section_names_none(
        tmp_path, monkeypatch, seeded):
    """A section may list no question types (the class 10 Science annual
    preset's Sections A-C do): any type of the right marks may fill it at
    generation. A swap still replaces like with like -- the served bank has
    164 keyed 1-mark very short answers but also 3 long_answer and 1 mcq at
    1 mark, and a 1-mark short answer must not turn into one of those
    because it scores higher."""
    by_id = {r["id"]: r for r in FIXTURE}
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        before = _at(paper, 1)["questionId"]
        assert by_id[before]["type"] == "short_answer"
        # Two better-scoring, in-scope, keyed 1-mark questions of other types
        # arrive after generation (a new pool object, so the bank is rebuilt).
        odd = [_rec("m0", 1, "ch1", 0, qtype="mcq", quality=0.99,
                    stem="Which gas turns lime water milky when passed through it?"),
               _rec("l0", 1, "ch1", 0, qtype="long_answer", quality=0.98,
                    stem="Name the organ that produces bile in the human body.")]
        monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(FIXTURE + odd))

        seen = []
        while True:
            r = _swap(client, t1, paper["id"], "1")
            if r.status_code != 200:
                break
            seen.append(r.json()["questionId"])
        assert seen and all(by_id.get(q, {}).get("type") == "short_answer" for q in seen), seen
        assert r.status_code == 409, r.text
        assert "short answer" in r.json()["detail"]["message"]


def test_swap_never_returns_a_question_already_on_the_paper_or_swapped_out_before(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        seen: list[str] = [_at(paper, 1)["questionId"]]
        while True:
            on_paper = _on_paper(paper)
            r = _swap(client, t1, paper["id"], "1")
            if r.status_code != 200:
                break
            new = r.json()["questionId"]
            assert new not in on_paper, (new, on_paper)
            assert new not in seen, (new, seen)          # never bounces back
            seen.append(new)
            paper = r.json()["paper"]
        # o0..o5 in scope and keyed; one sits in slot 2, so slot 1 cycles
        # through the other five and then runs out -- with the counts.
        assert len(seen) == 5, seen
        assert r.status_code == 409, r.text
        detail = r.json()["detail"]
        assert "no alternative in this scope" in detail["message"]
        counts = detail["counts"]
        assert counts["onPaper"] >= 1 and counts["swappedOutEarlier"] == 4
        assert counts["withoutKey"] == 1 and counts["outsideScope"] == 1


def test_swapping_a_question_keeps_its_or_pair_and_the_or_can_be_swapped_alone(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        q4 = _at(paper, 4)                           # Section B's last carries the OR
        assert q4["internalChoiceQuestionId"]

        r = _swap(client, t1, paper["id"], "4")
        assert r.status_code == 200, r.text
        after = _at(r.json()["paper"], 4)
        assert after["questionId"] != q4["questionId"]
        assert after["internalChoiceQuestionId"] == q4["internalChoiceQuestionId"]

        r = _swap(client, t1, paper["id"], "4_OR")
        assert r.status_code == 200, r.text
        after_or = _at(r.json()["paper"], 4)
        assert after_or["questionId"] == after["questionId"]
        assert after_or["internalChoiceQuestionId"] not in (
            q4["internalChoiceQuestionId"], after["questionId"])
        assert after_or["internalChoiceText"].startswith("Explain")
        # An OR slot on a question that has none does not exist.
        assert _swap(client, t1, paper["id"], "1_OR").status_code == 404


# ------------------------------------------------------------------ pick

def test_pick_rejects_unkeyed_duplicate_and_wrong_marks_and_takes_a_valid_one(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        pid = paper["id"]
        second = _at(paper, 2)["questionId"]

        unkeyed = _pick(client, t1, pid, "1", "o7")
        assert unkeyed.status_code == 422 and "answer key" in unkeyed.text.lower()
        dup = _pick(client, t1, pid, "1", second)
        assert dup.status_code == 409 and "already on the paper" in dup.text
        wrong = _pick(client, t1, pid, "1", "t4")
        assert wrong.status_code == 422
        assert "1-mark" in wrong.text and "3 marks" in wrong.text
        assert _pick(client, t1, pid, "1", "nope").status_code == 404

        ok = _pick(client, t1, pid, "1", "o5")
        assert ok.status_code == 200, ok.text
        assert _at(ok.json()["paper"], 1)["questionId"] == "o5"
        # Outside the paper's chapters: allowed (the teacher chose it), and said.
        out = _pick(client, t1, pid, "1", "o6")
        assert out.status_code == 200, out.text
        assert any("outside" in n.lower() for n in out.json()["notes"])


# ------------------------------------------------------------------ answer key + PDFs

def test_the_answer_key_and_every_set_follow_a_swap_and_old_pdfs_are_not_served(
        tmp_path, monkeypatch, seeded):
    import fitz

    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1, setCount=2)
        pid = paper["id"]
        assert client.post(f"/api/v1/papers/{pid}/export/pdf", headers=t1).status_code == 200
        assert client.post(f"/api/v1/papers/{pid}/export/answer-key",
                           headers=t1).status_code == 200

        old = _at(paper, 1)["questionId"]
        b_before = _on_paper(client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json())
        assert old not in b_before                     # set B prints its own (N-2-5)
        r = _swap(client, t1, pid, "1")
        assert r.status_code == 200, r.text
        new = r.json()["questionId"]
        edited = r.json()["paper"]
        assert edited["answerKey"]["1"].startswith(f"model answer for {new}")
        assert f"model answer for {old}" not in "\n".join(edited["answerKey"].values())
        # The bank still has 1-mark questions no set prints: the swap takes
        # one of them, not one of set B's.
        assert new not in b_before

        # Every set (each is its own row, set B as `<id>_set_B`): the old
        # question is on none, set A prints the new one and set B its own,
        # and each answer-key entry is its own printed question's.
        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1)
        assert set_b.status_code == 200, set_b.text
        assert _on_paper(set_b.json()) == b_before
        for s in [edited, set_b.json(), *edited["sets"]]:
            printed = {q["questionId"]: q["displayNumber"]
                       for sec in s["sections"] for q in sec["questions"]}
            ors = {q["internalChoiceQuestionId"]: q["displayNumber"]
                   for sec in s["sections"] for q in sec["questions"]
                   if q["internalChoiceQuestionId"]}
            assert old not in printed and old not in ors
            assert (new in printed or new in ors) == (s["setLabel"] == "A"), s["setLabel"]
            for qid, n in printed.items():
                assert s["answerKey"][str(n)].startswith(f"model answer for {qid}"), s["id"]
            for qid, n in ors.items():
                assert s["answerKey"][f"{n}_OR"] == f"model answer for {qid}", s["id"]
            assert old not in s["formattedContent"]

        # The PDFs rendered before the swap are not served after it...
        assert client.get(f"/api/v1/papers/{pid}/file", headers=t1).status_code == 404
        assert client.get(f"/api/v1/papers/{pid}/file?format=answer-key",
                          headers=t1).status_code == 404
        # ...and rendering again prints the updated answer key.
        assert client.post(f"/api/v1/papers/{pid}/export/answer-key",
                           headers=t1).status_code == 200
        pdf = client.get(f"/api/v1/papers/{pid}/file?format=answer-key", headers=t1)
        doc = fitz.open(stream=pdf.content, filetype="pdf")
        text = " ".join(" ".join(page.get_text() for page in doc).split())
        doc.close()
        assert f"model answer for {new}" in text and f"model answer for {old}" not in text

        # The assessment records the paper's questions as they now are.
        asm = client.get(f"/api/v1/assessments/{paper['assessmentId']}", headers=t1).json()
        assert new in asm["selectedQuestionIds"] and old not in asm["selectedQuestionIds"]


def test_a_quick_generated_paper_swaps_by_the_slots_marks_type_and_chapters(
        tmp_path, monkeypatch, seeded):
    """No template recorded the section's rules: the slot's own marks, the
    replaced question's type and the assessment's chapters stand in.

    Written after rule_for's fallback, so each clause was checked against a
    broken copy of it: fallback marks + 2 fails (3 == 1); fallback chapters
    emptied fails (['ch2'] == ['ch1']); no fallback at all is a 500
    (AttributeError on None). The type is pinned twice -- here and in
    choose_swap for any section that names no types -- so it fails only with
    both pins removed ('mcq' == 'short_answer')."""
    by_id = {r["id"]: r for r in FIXTURE}
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        r = client.post("/api/v1/papers/quick-generate", headers=t1, json={
            "subject": "Science", "grade": 10, "chapterIds": ["ch1"], "totalMarks": 20})
        assert r.status_code == 200, r.text
        paper = r.json()
        first = next(q for s in paper["sections"] for q in s["questions"] if q["marks"] == 1)
        # Better-scoring in-scope keyed 1-mark questions of other types: only
        # the type rule keeps them out of this short-answer slot.
        odd = [_rec("m0", 1, "ch1", 0, qtype="mcq", quality=0.99,
                    stem="Which gas turns lime water milky when passed through it?"),
               _rec("l0", 1, "ch1", 0, qtype="long_answer", quality=0.98,
                    stem="Name the organ that produces bile in the human body.")]
        monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(FIXTURE + odd))
        by_id.update({r["id"]: r for r in odd})
        swap = _swap(client, t1, paper["id"], str(first["displayNumber"]))
        assert swap.status_code == 200, swap.text
        new = by_id[swap.json()["questionId"]]
        assert new["marks"] == 1 and new["chapterIds"] == ["ch1"]
        assert new["type"] == by_id[first["questionId"]]["type"]
        assert swap.json()["questionId"] not in _on_paper(paper)


def test_a_competency_section_swaps_and_picks_by_the_one_competency_rule(
        tmp_path, monkeypatch):
    """Task 125: a case-based section (all competency questions) is refilled
    by the rule generation uses (competency.competency_signal), never by the
    stem's wording. A 4-mark long answer that opens "Read the given source"
    but comes from no competency-based source is not one, however well it
    scores; a CBSE competency-based item-bank question ("cbe:" bank id) is."""
    source = "Read the given source and answer the questions that follow: "
    recs = [
        _rec("src", 4, "ch1", 0, qtype="long_answer", quality=0.99,
             stem=source + "how ozone is formed in the upper atmosphere."),
        _rec("cbe0", 4, "ch1", 1, qtype="long_answer", quality=0.9),
        _rec("cbe1", 4, "ch1", 2, qtype="long_answer", quality=0.8),
    ]
    recs[0]["metadata"] = {"typeInferred": True}          # its label came from marks
    for r in recs[1:]:
        r["questionBankId"] = "cbe:Item-Bank---Science-Class-10.pdf"
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(recs))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json=_template(totalMarks=4, sections=[
            {"title": "Section E - Case based", "questionCount": 1, "marksEach": 4,
             "questionTypes": ["case_study"], "competencyShare": 1.0}]),
            headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        assert _at(paper, 1)["questionId"] == "cbe0"

        swap = _swap(client, t1, paper["id"], "1")
        assert swap.status_code == 200, swap.text
        assert swap.json()["questionId"] == "cbe1"
        again = _swap(client, t1, paper["id"], "1")
        assert again.status_code == 409, again.text
        assert again.json()["detail"]["counts"]["notCompetency"] == 1

        pick = _pick(client, t1, paper["id"], "1", "src")
        assert pick.status_code == 200, pick.text
        assert any("src is not competency-based" in n for n in pick.json()["notes"]), \
            pick.json()["notes"]


# ------------------------------------------------------------------ near-duplicates

# A real pair from the served bank (academicos-data/syllabus/questions.json,
# Class 10 Mathematics, 1 mark each): the same MCQ in two board papers,
# differing only in a trailing page-number fragment. The pool's own
# near-duplicate gate lets both through because the stem has only three
# content words ("equation", "not", "quadratic") and the gate needs four.
QUADRATIC_A = ("cbse:q:src:f319c93abeb1185b0864d200:9",
               "Which of the following is not a quadratic equation ? (A) (x – 2)₂ + 1 = "
               "2x – 3 (B) (2x – 1) (x – 3) = (x + 5) (x – 1) (C) x(x + 1) + 8 = (x + 2) "
               "(x – 2) (D) 2x + x 3 = 5 14-")
QUADRATIC_B = ("cbse:q:src:b23bc2e537566a04afbf4415:15",
               "Which of the following is not a quadratic equation ? (A) (x – 2)₂ + 1 = "
               "2x – 3 (B) (2x – 1) (x – 3) = (x + 5) (x – 1) (C) x(x + 1) + 8 = (x + 2) "
               "(x – 2) (D) 2x + x 3 =")
# Two real pairs that look alike and are different questions (Science,
# cbse:q:src:af50a3f7e666fdea9cee608f:24 / cbse:q:src:6dd3ff9345090c327a5b5409:23;
# Mathematics, cbse:q:src:94cb306f384779a2121f9f55:21 /
# cbse:q:src:0b3c7b807dcc7e88fd1809df:24): below the threshold.
LENS = "An object is placed at a distance of 60 cm from a concave lens of focal length 30 cm."
MIRROR = ("An object is placed at a distance of 30 cm in front of a concave mirror of "
          "focal length 20 cm.")
LCM = "Find LCM of 576 and 512 by prime factorization."
HCF = "Find HCF of 660 and 704 by prime factorization."


def test_the_near_duplicate_measure_on_real_pairs():
    assert pool_mod.near_duplicate(QUADRATIC_A[1], QUADRATIC_B[1])
    # Why a paper needs its own guard: the pool's gate misses this pair.
    gate = pool_mod._NearDuplicateIndex()
    assert not gate.is_duplicate(QUADRATIC_A[1]) and not gate.is_duplicate(QUADRATIC_B[1])
    assert not pool_mod.near_duplicate(LENS, MIRROR)
    assert not pool_mod.near_duplicate(LCM, HCF)


# Real pairs the text measure alone called one question (Task 906, from the
# class 10 Mathematics pool, ids cited). Near-identical words, but different
# numbers, polarity or function: a teacher sets both.
ROOT_K = (  # cbse:q:src:0916a372de696613bddff07e:23 / cbse:q:src:74d29feaacad629411a49c95:21
    "If 3 2 is a root of the quadratic equation kx2 – x – 2 = 0, then find the value of k.",
    "If 2 1 is a root of the quadratic equation x2 + kx – 4 5 = 0, then find the value of k.")
SUNDAYS = (  # cbse:q:src:f516dfe29cfec4ac6d74feec:19 / cbse:q:src:f516dfe29cfec4ac6d74feec:7
    "Assertion (A) : The probability that a leap year has 53 Sundays is",
    "Reason (R) : The probability that a non-leap year has 53 Sundays is")
IRRATIONAL = (  # cbse:q:src:f516dfe29cfec4ac6d74feec:27 / cbse:q:src:9e5b18498717709257f60167:30
    "Prove that 5 is an irrational number.",
    "Prove that 3 is an irrational number.")
IDENTITY = (  # cbse:q:src:abf68dc97d40281d455ffaa2:28 / cbse:q:src:db32b7ab98169b625243c09e:26
    "Prove the following trigonometric identity : = sec A -tan A",
    "Prove the following trigonometric identity : = cot A")
# Task 906's review: the radical is lost in extraction, so "root 3" and "3 +
# 2 root 5" differ only by numbers the shorter never had. A cut copy loses
# its end, not a middle; these differ in the middle.
RADICAL = ("Prove that 3 is an irrational number.",
           "Prove that 3 + 2 5 is an irrational number.")
RADICAL_2 = ("Prove that 2 is an irrational number.",
             "Prove that 2 3 is an irrational number.")
# ... and a sign or an exponent is a different question too, including the
# superscript and subscript digits the served stems carry ("(x – 2)₂").
SIGN = ("Find the zeroes of the quadratic polynomial x2 + 7x + 10 and verify the "
        "relationship between the zeroes and the coefficients.",
        "Find the zeroes of the quadratic polynomial x2 – 7x + 10 and verify the "
        "relationship between the zeroes and the coefficients.")
EXPONENT = ("Find the zeroes of the polynomial x² + 7x + 10 and verify the relationship.",
            "Find the zeroes of the polynomial x³ + 7x + 10 and verify the relationship.")
# ... and real pairs that are one question: the same MCQ in two papers, one
# copy carrying the page footer ("15-", "5| P a g e") or cut before its last
# number (cbse:q:src:0916a372de696613bddff07e:7 / cbse:q:src:7bc43935e9890c40e2e44322:12;
# cbse:q:src:411ab10b9f5e44bccbdb2339:5 / cbse:q:src:281d955eeac178f6b9b7a91b:12).
FACTORISE = (
    "Prime factorisation of 424 is : (A) 2 ´ 53 ´ 4 (B) 2 ´ 53 ´ 2 (C) 23 ´ 53 (D) 24 ´ 53 15-",
    "Prime factorisation of 424 is : (A) 2 ´ 53 ´ 4 (B) 2 ´ 53 ´ 2 (C) 23 ´ 53 (D) 24 ´")
FOOTER = (
    "x = 1 y = 2, 2x -3y + a = 0 2x + 3y -b = 0 , (A) a = 2b (B) 2a = b (C) a + 2b = 0 "
    "(D) 2a + b = 5| P a g e",
    "x = 1 y = 2, 2x -3y + a = 0 2x + 3y -b = 0 , (A) a = 2b (B) 2a = b (C) a + 2b = 0 "
    "(D) 2a + b = 9| P a g e")
# ... and one question whose copies differ by one token in the middle: the
# Hindi-medium frequency-table case study, its words lost in extraction, one
# copy carrying a stray "12" before its last "x y" (Task 906's code review,
# cbse:q:src:0b075a8b722f16f272c0cc4d:34 against
# cbse:q:src:db32b7ab98169b625243c09e:32, and against
# cbse:q:src:c42982ff54131ed0d5b7d9b0:35 with its page footer). The
# cut-at-the-end rule alone let both pairs print on one paper.
_FREQ_TABLE = ("( ) (mm ) 100 -120 8 120 -140 9 140 -160 12 160 -180 5 180 -200 6 mm ( ) "
               "(Record) 0 -4 4 -8 8 -12 12 -16 16 -20 20 -24 1 x y")
FREQ_TABLE = (_FREQ_TABLE + " 12 x y", _FREQ_TABLE + " x y")
FREQ_TABLE_FOOTER = (_FREQ_TABLE + " 12 x y", _FREQ_TABLE + " x y # 17| P a g e")


def test_numbers_polarity_and_functions_tell_different_questions_apart():
    """Task 905's review: over every pair in the real class 10 Mathematics
    pool the text measure flagged 28, and some were different questions."""
    for a, b in (ROOT_K, SUNDAYS, IRRATIONAL, IDENTITY, RADICAL, RADICAL_2, SIGN,
                 EXPONENT):
        assert not pool_mod.near_duplicate(a, b), (a, b)
        assert not pool_mod.near_duplicate(b, a), (a, b)
    # A page footer or a copy cut short is not a different question.
    for a, b in (FACTORISE, FOOTER, (QUADRATIC_A[1], QUADRATIC_B[1]), FREQ_TABLE,
                 FREQ_TABLE_FOOTER):
        assert pool_mod.near_duplicate(a, b), (a, b)
        assert pool_mod.near_duplicate(b, a), (a, b)


def test_near_duplicate_stems_never_share_a_paper(tmp_path, monkeypatch):
    twins = [
        _rec(QUADRATIC_A[0], 1, "ch1", 0, stem=QUADRATIC_A[1], quality=0.99),
        _rec(QUADRATIC_B[0], 1, "ch1", 0, stem=QUADRATIC_B[1], quality=0.98),
    ]
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(twins + FIXTURE))
    twin_ids = {QUADRATIC_A[0], QUADRATIC_B[0]}
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        # Generation: the two best-scoring 1-mark questions are the twins;
        # the paper takes one of them, never both.
        paper = _generate(client, t1)
        assert len(_on_paper(paper) & twin_ids) == 1
        other = (twin_ids - _on_paper(paper)).pop()
        slot_of_twin = next(q["displayNumber"] for s in paper["sections"]
                            for q in s["questions"] if q["questionId"] in twin_ids)
        free_slot = 2 if slot_of_twin == 1 else 1

        # Swap the other 1-mark slot until it runs out: never the twin.
        while True:
            r = _swap(client, t1, paper["id"], str(free_slot))
            if r.status_code != 200:
                break
            assert r.json()["questionId"] != other
            paper = r.json()["paper"]
        assert r.json()["detail"]["counts"]["nearDuplicate"] == 1

        # Picking it is refused, naming the question it repeats.
        pick = _pick(client, t1, paper["id"], str(free_slot), other)
        assert pick.status_code == 409 and "near-duplicate" in pick.text
        assert f"Q{slot_of_twin}" in pick.text
        # Replacing the twin itself with its own near-copy is allowed: the
        # paper still carries only one of them.
        same = _pick(client, t1, paper["id"], str(slot_of_twin), other)
        assert same.status_code == 200, same.text
        assert len(_on_paper(same.json()["paper"]) & twin_ids) == 1


# The same guard on the other two ways a paper is made (Task 905). Both run
# through `selection.optimize`, which had no near-duplicate check: the spec
# review of Task 903 ran the real pair plus 10 filler 1-mark questions
# through it with a 4-question 1-mark section and got both copies.

_TWINS = [
    _rec(QUADRATIC_A[0], 1, "ch1", 0, stem=QUADRATIC_A[1], quality=0.99),
    _rec(QUADRATIC_B[0], 1, "ch1", 0, stem=QUADRATIC_B[1], quality=0.98),
]
_TWIN_IDS = {QUADRATIC_A[0], QUADRATIC_B[0]}


def _schemas(records: list[dict]):
    from academicos.assessment.schemas import QuestionSchema
    return [QuestionSchema.model_validate(r) for r in records]


def _one_mark_blueprint(count: int, *, choice: int = 0):
    from academicos.assessment.schemas import (
        BloomDistribution, Blueprint, ChapterWeights, CompetencyWeights,
        DifficultyDistribution, SectionBlueprint)
    return Blueprint(
        total_marks=count, duration_minutes=30,
        difficulty=DifficultyDistribution(easy=0.3, medium=0.4, hard=0.3),
        bloom=BloomDistribution(remember=0.2, understand=0.2, apply=0.2,
                                analyze=0.2, evaluate=0.1, create=0.1),
        chapter_weights=ChapterWeights(), competency_weights=CompetencyWeights(),
        sections=[SectionBlueprint(
            id="section-a", label="A", name="Section A", marks_per_question=1,
            question_count=count, total_marks=count,
            has_internal_choice=choice > 0, internal_choice_count=choice)],
    )


def _ids_selected(result) -> set[str]:
    ids = set()
    for q in result.selected_questions:
        ids.add(q.id)
        if q.metadata.get("internal_choice_id"):
            ids.add(q.metadata["internal_choice_id"])
    return ids


def test_optimize_never_selects_both_near_duplicates():
    """The spec review's repro: the real pair, 10 fillers, four 1-mark slots.
    The twins score highest, so without the guard both are taken."""
    from academicos.assessment.selection import optimize
    fillers = [_rec(f"f{i}", 1, "ch1", i + 1, quality=0.7 - i * 0.01) for i in range(10)]
    result = optimize(_schemas(_TWINS + fillers), _one_mark_blueprint(4))
    assert len(result.selected_questions) == 4
    assert len(_ids_selected(result) & _TWIN_IDS) == 1


def test_a_short_section_is_filled_from_the_fallback_after_the_duplicate_is_left_out():
    """The code-quality review's repro: the twins and one filler in the chosen
    chapter, four 1-mark slots, five unused questions outside it. Borrowing
    exactly the shortfall (one) before the duplicate filter ran printed three
    questions under a gap saying the shortfall had been filled."""
    from academicos.assessment.selection import optimize
    fillers = [_rec("f0", 1, "ch1", 1, quality=0.7)]
    outside = [_rec(f"g{i}", 1, "ch2", i + 2, quality=0.6 - i * 0.01) for i in range(5)]
    result = optimize(_schemas(_TWINS + fillers), _one_mark_blueprint(4),
                      fallback_candidates=_schemas(outside))
    ids = _ids_selected(result)
    assert len(result.selected_questions) == 4, sorted(ids)
    assert len(ids & _TWIN_IDS) == 1
    assert len(ids & {f"g{i}" for i in range(5)}) == 2
    assert any("filled 2 of the shortfall" in g for g in result.gaps), result.gaps
    assert not any("only 3 of 4" in g for g in result.gaps), result.gaps


def test_a_section_the_fallback_cannot_fill_says_how_short_it_prints():
    """Nothing outside the chapters fits either: the gap reports the count
    actually printed, not the count available before duplicates were cut."""
    from academicos.assessment.selection import optimize
    fillers = [_rec("f0", 1, "ch1", 1, quality=0.7)]
    result = optimize(_schemas(_TWINS + fillers), _one_mark_blueprint(4))
    assert len(result.selected_questions) == 2
    assert any("only 2 of 4" in g for g in result.gaps), result.gaps


def test_an_or_alternative_is_never_a_near_duplicate_of_the_paper():
    """The OR partner is printed on the paper too: the twin of a question
    (its best-scoring same-chapter alternative) must not be offered as it."""
    from academicos.assessment.selection import optimize
    fillers = [_rec(f"f{i}", 1, "ch1", i + 1, quality=0.7 - i * 0.01) for i in range(3)]
    result = optimize(_schemas(_TWINS + fillers), _one_mark_blueprint(1, choice=1))
    assert result.selected_questions[0].id == QUADRATIC_A[0]
    alt = result.selected_questions[0].metadata.get("internal_choice_id")
    assert alt and alt != QUADRATIC_B[0]


def test_an_or_choice_left_out_for_repeating_the_paper_is_reported_as_a_gap():
    """One slot, one OR, and the only alternative is the twin of the primary.
    The OR is rightly not offered -- but a section printing fewer internal
    choices than its blueprint asks for has to say so, not drop it silently."""
    from academicos.assessment.selection import optimize
    result = optimize(_schemas(_TWINS), _one_mark_blueprint(1, choice=1))
    assert [q.id for q in result.selected_questions] == [QUADRATIC_A[0]]
    assert not result.selected_questions[0].metadata.get("internal_choice_id")
    assert any("only 0 of 1 internal choices" in g
               and "repeat a question already on the paper" in g
               for g in result.gaps), result.gaps


def test_a_quick_generated_paper_never_carries_both_near_duplicates(tmp_path, monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(_TWINS + FIXTURE))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        r = client.post("/api/v1/papers/quick-generate", headers=t1, json={
            "subject": "Science", "grade": 10, "chapterIds": ["ch1"], "totalMarks": 20})
        assert r.status_code == 200, r.text
        on_paper = _on_paper(r.json())
        assert len(on_paper & _TWIN_IDS) == 1, sorted(on_paper)


def test_optimize_then_generate_never_carries_both_near_duplicates(tmp_path, monkeypatch):
    """The builder's other path: POST /questions/optimize picks, POST
    /papers/generate prints what it picked."""
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(_TWINS + FIXTURE))
    keyed_ones = [r for r in _TWINS + FIXTURE if r["marks"] == 1 and r["id"] != "o7"]
    bp = _one_mark_blueprint(4).model_dump(by_alias=True)
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        opt = client.post("/api/v1/questions/optimize", headers=t1,
                          json={"candidates": keyed_ones, "blueprint": bp})
        assert opt.status_code == 200, opt.text
        picked = opt.json()["selectedQuestions"]
        assert len(picked) == 4
        gen = client.post("/api/v1/papers/generate", headers=t1, json={
            "assessmentId": "asm_none", "blueprint": bp, "selectedQuestions": picked,
            "template": {"id": "tpl", "schoolId": "school_1", "name": "Plain"}})
        assert gen.status_code == 200, gen.text
        on_paper = _on_paper(gen.json())
        assert len(on_paper & _TWIN_IDS) == 1, sorted(on_paper)


def test_generate_warns_about_selected_questions_that_repeat_each_other(tmp_path, monkeypatch):
    """POST /papers/generate prints what the client posts, and the teacher
    chose it. A hand-built selection holding both twins -- as two questions,
    or as a question and its OR partner -- prints (200) with a warning naming
    the pair, so the builder can offer "keep both" or "swap one". A client
    that wants a refusal sets rejectSimilar; the same question id twice is
    always refused."""
    bp = _one_mark_blueprint(3).model_dump(by_alias=True)
    others = [r for r in FIXTURE if r["marks"] == 1 and r["id"] in ("o0", "o1")]
    partnered = dict(_TWINS[0], metadata={
        "internal_choice_id": QUADRATIC_B[0],
        "internal_choice_stem": QUADRATIC_B[1],
        "internal_choice_question": _TWINS[1]})
    tpl = {"id": "tpl", "schoolId": "school_1", "name": "Plain"}
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")

        def post(picked, **extra):
            return client.post("/api/v1/papers/generate", headers=t1, json={
                "assessmentId": "asm_none", "blueprint": bp,
                "selectedQuestions": picked, "template": tpl, **extra})

        for picked in (_TWINS + others[:1], [partnered] + others):
            gen = post(picked)
            assert gen.status_code == 200, gen.text
            # The competency line is the paper's own share (paper.report_competency).
            warnings = [w for w in gen.json()["warnings"] if not w.startswith("Competency-based: ")]
            assert len(warnings) == 1, warnings
            assert QUADRATIC_A[0] in warnings[0] and QUADRATIC_B[0] in warnings[0], warnings
            # The same pair as ids, so the builder can swap one without
            # reading ids back out of the sentence.
            assert gen.json()["similarPairs"] == [[QUADRATIC_A[0], QUADRATIC_B[0]]]
            assert _TWIN_IDS <= _on_paper(gen.json())
            refused = post(picked, rejectSimilar=True)
            assert refused.status_code == 422, refused.text
            detail = refused.json()["detail"]
            assert QUADRATIC_A[0] in detail and QUADRATIC_B[0] in detail, detail
        ok = post(_TWINS[:1] + others)
        assert ok.status_code == 200, ok.text
        assert [w for w in ok.json()["warnings"] if "look like the same question" in w] == []
        assert ok.json()["similarPairs"] == []
        twice = post(_TWINS[:1] + _TWINS[:1] + others[:1])
        assert twice.status_code == 422, twice.text
        assert QUADRATIC_A[0] in twice.json()["detail"]


def test_generate_from_ids_prints_exactly_the_chosen_questions_or_refuses(tmp_path, monkeypatch, seeded):
    """D57: three class 7 ids plus `cbe:q:Maths8BS2` (class 8), or plus
    `no-such-id-xyz`, returned 200 printing the three with `warnings []` --
    the paper silently left out a question the teacher chose. An id the
    class's bank does not hold is now refused, by name; the pick route
    already refused it with 404."""
    other = [dict(_rec("e8", 1, "ch1", 3), grade=8)]
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "VIII"), _pool(other))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")

        def post(ids):
            return client.post("/api/v1/papers/generate-from-ids", headers=t1,
                               json={"subject": "Science", "grade": 10, "questionIds": ids})

        for stray in ("no-such-id-xyz", "e8"):
            r = post(["o0", "o1", "t0", stray])
            assert r.status_code == 404, r.text
            assert stray in r.json()["detail"] and "Class 10 Science" in r.json()["detail"]
            assert "o0" not in r.json()["detail"]
        assert client.get("/api/v1/assessments", headers=t1).json() == [], "nothing saved"

        ok = post(["o0", "o1", "t0"])
        assert ok.status_code == 200, ok.text
        printed = [q["questionId"] for s in ok.json()["sections"] for q in s["questions"]]
        assert sorted(printed) == ["o0", "o1", "t0"]


def test_generate_from_ids_warns_about_ids_that_repeat_each_other(tmp_path, monkeypatch):
    """POST /papers/generate-from-ids builds the paper straight from the
    teacher's curated ids (the Flutter client's path): both twins curated
    together print with a warning naming the pair, like /papers/generate;
    rejectSimilar refuses them, and one id listed twice is refused."""
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(_TWINS + FIXTURE))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        body = {"subject": "Science", "grade": 10}

        def post(ids, **extra):
            return client.post("/api/v1/papers/generate-from-ids", headers=t1,
                               json={**body, "questionIds": ids, **extra})

        gen = post([QUADRATIC_A[0], "o0", QUADRATIC_B[0]])
        assert gen.status_code == 200, gen.text
        warnings = gen.json()["warnings"]
        assert len(warnings) == 1, warnings
        assert QUADRATIC_A[0] in warnings[0] and QUADRATIC_B[0] in warnings[0], warnings
        assert [sorted(p) for p in gen.json()["similarPairs"]] == [sorted(_TWIN_IDS)]
        assert _TWIN_IDS <= _on_paper(gen.json())
        # The warning belongs to this generation, not to the stored paper.
        stored = client.get(f"/api/v1/papers/{gen.json()['id']}", headers=t1)
        assert stored.status_code == 200, stored.text
        assert stored.json()["warnings"] == []
        assert stored.json()["similarPairs"] == []
        refused = post([QUADRATIC_A[0], "o0", QUADRATIC_B[0]], rejectSimilar=True)
        assert refused.status_code == 422, refused.text
        detail = refused.json()["detail"]
        assert QUADRATIC_A[0] in detail and QUADRATIC_B[0] in detail, detail
        twice = post([QUADRATIC_A[0], "o0", QUADRATIC_A[0]])
        assert twice.status_code == 422, twice.text
        ok = post([QUADRATIC_A[0], "o0"])
        assert ok.status_code == 200, ok.text
        assert ok.json()["warnings"] == []


# ------------------------------------------------------------------ recent papers

def test_swap_avoids_the_teachers_recent_papers_while_the_bank_has_alternatives(
        tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        first = _generate(client, t1)                       # o0, o1
        for slot in ("1", "2"):                             # -> o2, o3
            first = _swap(client, t1, first["id"], slot).json()["paper"]
        assert {_at(first, 1)["questionId"], _at(first, 2)["questionId"]} == {"o2", "o3"}

        second = _generate(client, t1)                      # o0, o1 again
        r = _swap(client, t1, second["id"], "1")
        # o2 and o3 rank higher but sit on the teacher's last paper.
        assert r.json()["questionId"] == "o4", r.json()
        r = _swap(client, t1, second["id"], "1")
        assert r.json()["questionId"] == "o5"
        # Only recent ones left: one is used, and the teacher is told.
        r = _swap(client, t1, second["id"], "1")
        assert r.status_code == 200 and r.json()["questionId"] in ("o2", "o3")
        assert any("recent" in n.lower() for n in r.json()["notes"])


# ------------------------------------------------------------------ speed, real bank

_REAL_BANK = Path(__file__).resolve().parents[1] / "academicos-data" / "syllabus" / "questions.json"


def _p(values: list[float], q: float) -> float:
    values = sorted(values)
    return values[min(len(values) - 1, int(round(q * (len(values) - 1))))]


@pytest.mark.skipif(not _REAL_BANK.exists(), reason="the served bank is not in this checkout")
def test_generate_swap_and_pick_timings_on_the_real_class_10_science_bank(
        tmp_path, monkeypatch, record_property):
    from academicos.assessment import paper_edit
    from academicos.config import Config

    cfg = Config(data_root=tmp_path / "bank")
    cfg._load_baked_questions = True
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"),
                        pool_mod.build_pool(cfg, subject="Science", grade="X"))
    builds: list[str] = []
    monkeypatch.setattr(pool_mod, "build_pool",
                        lambda *a, **k: builds.append("reload") or pytest.fail("pool rebuilt"))
    mapped: list[int] = []
    real_bank = paper_edit._build_bank
    monkeypatch.setattr(paper_edit, "_build_bank",
                        lambda *a, **k: mapped.append(1) or real_bank(*a, **k))
    monkeypatch.setattr(paper_edit, "_BANKS", {})

    preset = "preset:cbse:10:science:annual"
    gen_ms, swap_ms, pick_ms = [], [], []
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        papers = []
        for _ in range(20):
            t = time.perf_counter()
            r = client.post(GEN, json={"templateId": preset, "allowGaps": True}, headers=t1)
            gen_ms.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 200, r.text
            papers.append(r.json()["paper"])
        paper = papers[-1]
        # Only the slots the bank can actually answer. What is measured is how
        # long the search for an alternative takes; a slot with nothing to
        # swap to answers 409 in no time and would flatter the numbers.
        # Which slots those are is read from the bank rather than written
        # down, because the bank's shape moves under this test: it used to be
        # "sections A-D, 36 questions", and on the merged bank (2026-09-23)
        # Science 10 holds exactly 3 questions at 2 marks and 4 1-mark very
        # short answers -- every one of which a single paper prints -- and
        # nothing at all at 4 marks.
        from collections import Counter

        from academicos.assessment.mapping import to_question_schema

        spare = Counter((q.marks, q.type) for q in
                        map(to_question_schema, pool_mod._CACHE[("Science", "X")].questions))
        printed = [q for s in paper["sections"] for q in s["questions"]]
        on_paper = Counter((q["marks"], q["type"]) for q in printed)
        numbers = [q["displayNumber"] for q in printed
                   if spare[(q["marks"], q["type"])] > on_paper[(q["marks"], q["type"])]]
        assert len(numbers) >= 20, (len(numbers), on_paper)
        for i in range(20):
            slot = str(numbers[(i * 7) % len(numbers)])      # 20 different slots
            t = time.perf_counter()
            r = _swap(client, t1, paper["id"], slot)
            swap_ms.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 200, r.text
            paper, old = r.json()["paper"], r.json()["replacedQuestionId"]
            # Changed their mind: the question swapped out is picked back.
            t = time.perf_counter()
            r = _pick(client, t1, paper["id"], slot, old)
            pick_ms.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 200, r.text
            paper = r.json()["paper"]

    timings = {name: {"p50": round(statistics.median(v), 1), "p95": round(_p(v, 0.95), 1)}
               for name, v in (("generate", gen_ms), ("swap", swap_ms), ("pick", pick_ms))}
    record_property("timings_ms", timings)
    print(f"\nclass 10 Science annual, real bank, 20 runs each (ms): {timings}")
    assert builds == []                 # the pool is built once, never per request
    assert len(mapped) == 1             # and mapped to the wire shape once


def test_one_inserted_sign_mid_stem_is_a_different_question():
    """Task 906's review: the mid-stem exception took any single extra token,
    so '... 2x - 4y = 24 ...' and '... 2x - 4y = -24 ...' (one inserted '-',
    with >= 10 exact tokens) were near-duplicates. Only a stray NUMBER is
    extraction noise; a sign, relation, function name, polarity word or
    assertion/reason label changes the question."""
    from academicos.assessment import pool

    a = ("Solve the pair of linear equations 2x + 3y = 11 and 2x - 4y = 24 and "
         "hence find the value of m for which y = mx + 3.")
    b = a.replace("= 24", "= -24")
    assert not pool.near_duplicate(a, b)
    assert not pool.near_duplicate(b, a)
    c = a.replace("= 11 and", "= 11 not and")
    assert not pool.near_duplicate(a, c)
