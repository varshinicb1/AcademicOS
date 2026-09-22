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
        r = _swap(client, t1, pid, "1")
        assert r.status_code == 200, r.text
        new = r.json()["questionId"]
        edited = r.json()["paper"]
        assert edited["answerKey"]["1"].startswith(f"model answer for {new}")
        assert f"model answer for {old}" not in "\n".join(edited["answerKey"].values())

        # Every set (each is its own row, set B as `<id>_set_B`): the old
        # question is gone, the new one printed, and each answer-key entry is
        # its own printed question's.
        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1)
        assert set_b.status_code == 200, set_b.text
        for s in [edited, set_b.json(), *edited["sets"]]:
            printed = {q["questionId"]: q["displayNumber"]
                       for sec in s["sections"] for q in sec["questions"]}
            ors = {q["internalChoiceQuestionId"]: q["displayNumber"]
                   for sec in s["sections"] for q in sec["questions"]
                   if q["internalChoiceQuestionId"]}
            assert old not in printed and old not in ors
            assert new in printed or new in ors
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
    replaced question's type and the assessment's chapters stand in."""
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
        # Sections A-D (36 questions). Section E's case units are all the
        # bank has at 4 marks, so a swap there is the "no alternative" answer,
        # which is not what this measures.
        numbers = [q["displayNumber"] for s in paper["sections"][:4] for q in s["questions"]]
        assert len(numbers) == 36
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
