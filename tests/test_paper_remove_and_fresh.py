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
from test_paper_templates import _boot_client, _register, needs_real_bank

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
        # Set B prints its own questions (N-2-5): its Q1 is another question.
        b_before = _printed(client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json())
        b_gone = b_before[0][1]
        assert b_gone != gone

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

        # Every set loses the question in the same place -- its own Q1 -- so
        # the sets stay the same paper in shape, each renumbered.
        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json()
        embedded_b = next(s for s in edited["sets"] if s["setLabel"] == "B")
        for s in (set_b, embedded_b):
            assert b_gone not in _on_paper(s)
            assert [(q, alt) for _, q, alt in _printed(s)] == [(q, alt) for _, q, alt in b_before[1:]]
        for s in (set_b, *edited["sets"]):
            assert gone not in _on_paper(s)
            assert [n for n, _, _ in _printed(s)] == [1, 2, 3]
            assert [x["totalMarks"] for x in s["sections"]] == [1, 6]
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


def _pdf_and_word_text(client, headers, pid: str) -> tuple[str, str]:
    import io
    import re
    import zipfile

    import fitz
    assert client.post(f"/api/v1/papers/{pid}/export/pdf", headers=headers).status_code == 200
    pdf = client.get(f"/api/v1/papers/{pid}/file", headers=headers).content
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        pdf_text = " ".join("".join(p.get_text() for p in doc).split())
    assert client.post(f"/api/v1/papers/{pid}/export/docx", headers=headers).status_code == 200
    docx = client.get(f"/api/v1/papers/{pid}/file", params={"format": "docx"}, headers=headers).content
    xml = zipfile.ZipFile(io.BytesIO(docx)).read("word/document.xml").decode()
    word = " ".join(re.sub(r"<[^>]+>", " ", xml.replace("<w:tab/>", " ")).split())
    return pdf_text, word


def test_the_printed_instructions_describe_the_paper_after_a_remove(tmp_path, monkeypatch, seeded):
    """v3 audit N-2-6: the General Instructions were stamped once at
    generation, so removing Q38 and one of Section B's two ORs on a class 10
    Maths half-yearly paper left the PDF and the Word file saying "Section E
    ... 3 question(s)" and "Section B ... 2 of them offer an internal choice
    (OR)". They now describe the paper as it stands, as does Maximum Marks."""
    from academicos.assessment.schemas import TemplateSection
    from academicos.assessment.template_presets import instructions_for

    sections = [{"title": "Section A - Objective", "questionCount": 2, "marksEach": 1},
                {"title": "Section B - Short answer", "questionCount": 2, "marksEach": 3,
                 "choiceCount": 1}]
    generated = instructions_for([TemplateSection.model_validate(s) for s in sections])
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json={
            "name": "Preset-like", "grade": 10, "subject": "Science", "examType": "unit_test",
            "totalMarks": 8, "durationMinutes": 40, "instructions": generated,
            "sections": sections, "scope": {"chapterIds": ["ch1"]}}, headers=t1).json()["id"]
        r = client.post(GEN, json={"templateId": tid}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        pid = paper["id"]
        assert paper["metadata"]["instructionsGenerated"] is True
        assert paper["metadata"]["instructions"] == generated
        pdf, word = _pdf_and_word_text(client, t1, pid)
        for text in (pdf, word):
            assert "Section B - Short answer: 2 question(s) of 3 mark(s) each. 1 of them offer" in text

        # Remove Q4's OR alternative, then Q1 -- the web's two Remove calls.
        assert _remove(client, t1, pid, "4_OR").status_code == 200
        r = _remove(client, t1, pid, "1")
        assert r.status_code == 200, r.text
        edited = r.json()["paper"]
        want = ("This question paper has 2 sections.\n"
                "Section A - Objective: 1 question(s) of 1 mark(s) each.\n"
                "Section B - Short answer: 2 question(s) of 3 mark(s) each.\n"
                "All questions are compulsory unless a choice is stated.")
        assert edited["metadata"]["instructions"] == want
        assert edited["metadata"]["totalMarks"] == 7
        pdf, word = _pdf_and_word_text(client, t1, pid)
        for text in (pdf, word):
            assert "Section A - Objective: 1 question(s) of 1 mark(s) each." in text
            assert "Section B - Short answer: 2 question(s) of 3 mark(s) each." in text
            assert "offer an internal choice" not in text and "2 question(s) of 1 mark" not in text
            assert "Maximum Marks: 7" in text
        asm = client.get(f"/api/v1/assessments/{paper['assessmentId']}", headers=t1).json()
        assert asm["metadata"]["paperTemplate"]["instructions"] == want

        # A swap keeps them true too (same shape, so the same lines).
        assert _swap(client, t1, pid, "1").status_code == 200
        assert client.get(f"/api/v1/papers/{pid}", headers=t1).json()["metadata"]["instructions"] == want


@needs_real_bank
def test_the_audits_repro_maths_10_half_yearly_on_the_real_bank(tmp_path, monkeypatch):
    """N-2-6 as the audit found it: Maths 10 half-yearly, remove Q38 and one
    of Section B's two ORs, then read the PDF and the Word file."""
    from academicos.assessment import pool as pool_mod
    from academicos.config import Config

    cfg = Config(data_root=tmp_path / "bank")
    cfg._load_baked_questions = True
    monkeypatch.setitem(pool_mod._CACHE, ("Mathematics", "X"),
                        pool_mod.build_pool(cfg, subject="Mathematics", grade="X"))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        r = client.post(GEN, json={"templateId": "preset:cbse:10:mathematics:half_yearly",
                                   "setCount": 3}, headers=t1)
        assert r.status_code == 200, r.text
        paper = r.json()["paper"]
        pid = paper["id"]
        assert paper["metadata"]["totalMarks"] == 80
        b = next(s for s in paper["sections"] if s["label"] == "B")
        ors = [q["displayNumber"] for q in b["questions"] if q.get("internalChoiceQuestionId")]
        assert len(ors) == 2
        assert _remove(client, t1, pid, "38").status_code == 200
        r = _remove(client, t1, pid, f"{ors[0]}_OR")
        assert r.status_code == 200, r.text
        pdf, word = _pdf_and_word_text(client, t1, pid)
        for text in (pdf, word):
            assert "Section E - Case-study based: 2 question(s) of 4 mark(s) each." in text
            assert ("Section B - Very short answer: 5 question(s) of 2 mark(s) each. "
                    "1 of them offer an internal choice (OR)") in text
            assert "3 question(s) of 4 mark(s)" not in text and "2 of them offer" not in text.split(
                "Section C")[0]
            assert "Maximum Marks: 76" in text
        for s in r.json()["paper"]["sets"]:           # every set, in its own words
            assert "Section E - Case-study based: 2 question(s)" in s["metadata"]["instructions"]
            assert s["metadata"]["totalMarks"] == 76


def test_the_teachers_own_instructions_are_never_rewritten_by_an_edit(tmp_path, monkeypatch, seeded):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json={**_template_body(), "instructions": "Write neatly."},
                          headers=t1).json()["id"]
        paper = client.post(GEN, json={"templateId": tid}, headers=t1).json()["paper"]
        assert paper["metadata"]["instructionsGenerated"] is False
        edited = _remove(client, t1, paper["id"], "1").json()["paper"]
        assert edited["metadata"]["instructions"] == "Write neatly."
        pdf, word = _pdf_and_word_text(client, t1, paper["id"])
        assert "Write neatly." in pdf and "Write neatly." in word
        assert "This question paper has" not in pdf


def test_a_paper_stored_before_the_flag_prints_its_generated_instructions_rebuilt():
    """A paper saved before `instructionsGenerated` existed carries stamped
    generated text and no flag: its stale lines are rebuilt from the paper,
    and text that does not read as generated is printed as written."""
    from academicos.assessment.pdf import instruction_lines
    from test_assessment_pdf import _make_paper

    paper = _make_paper()
    stale = ("This question paper has 1 sections.\nMCQ: 3 question(s) of 1 mark(s) each. "
             "2 of them offer an internal choice (OR): attempt only one of the two.\n"
             "All questions are compulsory unless a choice is stated.")
    paper.metadata = paper.metadata.model_copy(update={"instructions": stale})
    assert paper.metadata.instructions_generated is None
    assert instruction_lines(paper) == [
        "This question paper has 1 section.", "MCQ: 1 question(s) of 1 mark(s) each.",
        "All questions are compulsory unless a choice is stated."]
    paper.metadata = paper.metadata.model_copy(update={"instructions": "Answer any five.\nUse ink."})
    assert instruction_lines(paper) == ["Answer any five.", "Use ink."]


def test_removing_from_an_attempt_any_section_keeps_its_marks_and_says_so(
        tmp_path, monkeypatch, seeded):
    """"Attempt any 2 of 3" is worth 2 questions' marks: removing one of its
    three leaves 2 of 2, still worth the same, and the name and instructions
    say what is printed."""
    from academicos.assessment.schemas import TemplateSection
    from academicos.assessment.template_presets import instructions_for

    sections = [{"title": "Section A - Objective (attempt any 2)", "questionCount": 3,
                 "marksEach": 1, "attemptCount": 2},
                {"title": "Section B - Short answer", "questionCount": 1, "marksEach": 3}]
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = client.post(BASE, json={
            "name": "Any", "grade": 10, "subject": "Science", "examType": "custom",
            "totalMarks": 5, "durationMinutes": 40,
            "instructions": instructions_for([TemplateSection.model_validate(s) for s in sections]),
            "sections": sections, "scope": {"chapterIds": ["ch1"]}}, headers=t1).json()["id"]
        paper = client.post(GEN, json={"templateId": tid}, headers=t1).json()["paper"]
        a = paper["sections"][0]
        assert (a["name"], a["totalMarks"]) == ("Section A - Objective (attempt any 2) (attempt any 2 of 3)", 2)
        edited = _remove(client, t1, paper["id"], "1").json()["paper"]
        a = edited["sections"][0]
        assert (a["name"], a["totalMarks"], len(a["questions"])) == (
            "Section A - Objective (attempt any 2)", 2, 2)
        assert edited["metadata"]["totalMarks"] == 5
        assert "Section A - Objective (attempt any 2): 2 question(s) of 1 mark(s) each.\n" \
            in edited["metadata"]["instructions"]


def _template_body() -> dict:
    from test_paper_swap_pick import _template
    return _template()


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
        b_before = _printed(set_b)
        # Set B prints its own questions, with an OR in the same place.
        assert b_before[3][2] is not None and b_before[3][1] != primary, b_before

        r = _remove(client, t1, pid, "4_OR")
        assert r.status_code == 200, r.text
        assert r.json()["removedQuestionIds"] == [alt]
        edited = r.json()["paper"]
        assert _at(edited, 4)["questionId"] == primary
        assert _at(edited, 4)["internalChoiceQuestionId"] is None
        assert edited["metadata"]["totalMarks"] == paper["metadata"]["totalMarks"]
        _key_matches_print(edited)

        # Every set offers the same choices: set B's OR there is gone too, and
        # its questions stay.
        set_b = client.get(f"/api/v1/papers/{pid}_set_B", headers=t1).json()
        assert [(n, q) for n, q, _ in _printed(set_b)] == [(n, q) for n, q, _ in b_before]
        assert all(a is None for _, _, a in _printed(set_b))
        _key_matches_print(set_b)


def test_a_rotated_set_stored_before_distinct_sets_still_loses_the_or_pair_turned_round():
    """Builder papers stored before sets had questions of their own are set A
    rotated, with OR pairs turned round on set B: removing an OR from set A
    must put set A's question back as the compulsory one there."""
    from academicos.assessment import paper_edit
    from academicos.assessment.paper import generate_paper_sets
    from academicos.assessment.schemas import (BloomDistribution, Blueprint, ChapterWeights,
                                               CompetencyWeights, DifficultyDistribution,
                                               GeneratedPaper, SectionBlueprint)
    from test_paper_swap_pick import _schemas

    t0, t1, t2 = _schemas([r for r in FIXTURE if r["id"] in ("t0", "t1", "t2")])
    t1.metadata.update({"internal_choice_id": t2.id, "internal_choice_stem": t2.stem,
                        "internal_choice_scheme": t2.answer_scheme.model_answer,
                        "internal_choice_question": t2.model_dump(by_alias=False)})
    bp = Blueprint(total_marks=6, duration_minutes=30,
                   difficulty=DifficultyDistribution(easy=0.3, medium=0.4, hard=0.3),
                   bloom=BloomDistribution(remember=0.2, understand=0.2, apply=0.2,
                                           analyze=0.2, evaluate=0.1, create=0.1),
                   chapter_weights=ChapterWeights(), competency_weights=CompetencyWeights(),
                   sections=[SectionBlueprint(id="s1", label="A", name="Short", marks_per_question=3,
                                              question_count=2, total_marks=6)])
    paper = generate_paper_sets(paper_id="paper_old", assessment_id="a", assessment_title="T",
                                subject="Science", grade=10, blueprint=bp,
                                selected_questions=[t0, t1], set_count=2,
                                rotation_groups=[[t0, t1]])
    set_b = paper.sets[1]
    assert [(q.question_id, q.internal_choice_question_id) for q in set_b.sections[0].questions] \
        == [("t2", "t1"), ("t0", None)]
    slot = paper_edit.find_slot(paper, "2_OR")
    for member in (paper, set_b):
        edited = paper_edit.drop_alternative(member, slot.question, paper.answer_key["2"],
                                             position=paper_edit.slot_position(slot))
        printed = [(q.question_id, q.internal_choice_question_id) for q in edited.sections[0].questions]
        assert sorted(printed) == [("t0", None), ("t1", None)], printed
        _key_matches_print(GeneratedPaper.model_validate(edited.model_dump()).model_dump(by_alias=True))
