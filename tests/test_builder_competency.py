"""The builder's availability report carries the real competency share and the
tier answer, and a template paper carries the share (Task 125, step 7).

CBSE asks that at least half of a paper be competency-based. The builder's
step 3 ("Chapters") is where the teacher can still change the scope, so the
availability report -- the generator's own selection, run dry -- says what
share the paper would print, whether the whole syllabus would reach 50% when
the chosen chapters do not (`below_scope`), or whether the class and subject
bank cannot reach it with this template at all (`below_bank`). It also says
whether a Foundation or Advanced version could differ from this paper.

Counted by the one rule (competency.competency_signal): only what a source
printed, never a Bloom level, marks or wording.

Hermetic except the @needs_real_bank tests, which read the served bank and
never write it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from academicos.assessment import pool as pool_mod
from academicos.assessment.competency import COMPETENCY_RULE_TEXT
from academicos.assessment.paper_templates import (
    AvailabilityReport,
    build_scope_filter,
    competency_check,
    plan,
    tier_check,
)
from academicos.assessment.schemas import PaperTemplate, PaperTemplateDraft, QuestionSchema, \
    TemplateScope
from academicos.assessment.selection import tiers_note
from test_paper_templates import _boot_client, _distinct, _fixture_pool, _record, _register

BASE = "/api/v1/schools/school_1/teacher-templates"
GEN = "/api/v1/papers/generate-from-template"
CBE = "cbe:Item-Bank---Science-Class-10.pdf"


def _rec(qid: str, chapter: str, *, cbe: bool = False, quality: float = 0.8,
         difficulty: str = "medium", marks: int = 1) -> dict:
    rec = _record(qid, marks, chapter, difficulty=difficulty)
    rec["stem"] = f"Fixture question {qid}: explain {_distinct(qid)}."
    rec["qualityScore"] = quality
    if cbe:
        rec["questionBankId"] = CBE
    return rec


def _schemas(records: list[dict]) -> list[QuestionSchema]:
    return [QuestionSchema.model_validate(r) for r in records]


def _template(count: int = 4, chapters: tuple[str, ...] = (),
              share: float | None = None) -> PaperTemplateDraft:
    """`share` is the section's competency share. None, as the presets leave
    every section but the case studies, takes competency-based questions
    first (QA R-03); a test of what the builder says about a paper below 50%
    names 0, a template that asks for no competency-based questions."""
    section = {"title": "Section A", "questionCount": count, "marksEach": 1}
    if share is not None:
        section["competencyShare"] = share
    return PaperTemplateDraft.model_validate({
        "name": "Unit test", "grade": 10, "subject": "Science", "examType": "unit_test",
        "totalMarks": count, "durationMinutes": 40,
        "sections": [section],
        "scope": {"chapterIds": list(chapters)},
    })


def _check(template: PaperTemplateDraft, bank: list[QuestionSchema]):
    """What the availability route attaches: the plan in the template's scope,
    and the whole-syllabus plan beside it when the scope names chapters."""
    _, plans = plan(template, "t", bank, build_scope_filter(template.scope, bank))
    whole = None
    if template.scope.chapter_ids:
        _, whole = plan(template, "t", bank, build_scope_filter(TemplateScope(), bank))
    return competency_check(template, plans, bank, whole)


# Four plain questions in ch1; four CBE item-bank questions in ch2, ranked
# first by quality, so the whole syllabus prints them.
SPLIT = ([_rec(f"p{i}", "ch1") for i in range(4)]
         + [_rec(f"c{i}", "ch2", cbe=True, quality=0.9) for i in range(4)])


# ---- competency_check, pure ---------------------------------------------------

def test_chosen_chapters_below_50_percent_that_the_whole_syllabus_reaches():
    check = _check(_template(chapters=("ch1",)), _schemas(SPLIT))
    assert check.status == "below_scope"
    assert check.summary == "Competency-based: 0 of 4 questions (0%)"
    assert check.detail == "Below CBSE's 50%. The whole syllabus would give 4 of 4 (100%)."
    assert check.counted == COMPETENCY_RULE_TEXT
    assert (check.printed, check.competency_based, check.share) == (4, 0, 0.0)
    assert (check.whole_syllabus_printed, check.whole_syllabus_competency_based) == (4, 4)
    assert (check.bank_usable, check.bank_competency_based, check.bank_share) == (8, 4, 0.5)
    assert check.target == 0.5


def test_the_whole_syllabus_meets_50_percent():
    check = _check(_template(), _schemas(SPLIT))
    assert check.status == "meets"
    assert check.summary == "Competency-based: 4 of 4 questions (100%)"
    assert check.detail == "CBSE asks for at least 50%."
    assert check.by_signal == {"cbeItemBank": 4}
    # No second plan without chosen chapters: nothing to compare with.
    assert check.whole_syllabus_printed is None
    assert check.whole_syllabus_competency_based is None


def test_a_bank_with_too_few_competency_questions_is_named_as_the_limit():
    bank = _schemas([_rec(f"p{i}", "ch1") for i in range(5)] + [_rec("c0", "ch1", cbe=True)])
    for chapters in ((), ("ch1",)):
        check = _check(_template(chapters=chapters), bank)
        assert check.status == "below_bank", chapters
        assert check.summary == "Competency-based: 1 of 4 questions (25%)"
        assert check.detail == (
            "Below CBSE's 50%. The Class 10 Science bank cannot reach it with this "
            "template: 1 of the 6 questions it can use (17%) are competency-based.")
        assert check.bank_share == 0.167


def test_chosen_chapters_whose_whole_syllabus_also_falls_short_are_below_bank():
    bank = _schemas([_rec(f"p{i}", "ch1") for i in range(4)]
                    + [_rec(f"q{i}", "ch2", quality=0.9) for i in range(3)]
                    + [_rec("c0", "ch2", cbe=True, quality=0.95)])
    check = _check(_template(chapters=("ch1",)), bank)
    assert check.status == "below_bank"
    assert (check.whole_syllabus_printed, check.whole_syllabus_competency_based) == (4, 1)


def test_nothing_printed_is_no_share():
    bank = _schemas([_rec("t0", "ch1", marks=3)])
    assert _check(_template(), bank) is None


def test_the_bloom_level_marks_and_a_guessed_type_are_not_counted():
    recs = [_rec(f"p{i}", "ch1") for i in range(4)]
    recs[0]["bloomLevel"] = "analyze"
    recs[1]["type"], recs[1]["metadata"] = "case_study", {"typeInferred": True}
    check = _check(_template(), _schemas(recs))
    assert (check.competency_based, check.status) == (0, "below_bank")


def test_percentages_round_half_up_to_whole_numbers():
    # 1 of 8 is 12.5%: half-up gives 13, banker's rounding would give 12.
    bank = _schemas([_rec(f"p{i}", "ch1") for i in range(7)] + [_rec("c0", "ch1", cbe=True)])
    check = _check(_template(count=8), bank)
    assert check.summary == "Competency-based: 1 of 8 questions (13%)"


# ---- tier_check, pure ---------------------------------------------------------

def test_tiers_are_unavailable_on_difficulties_the_bank_supplied():
    """CBE item-bank difficulties come from marks (cbse_cbe._difficulty_for):
    three 'easy' and three 'hard' of the same marks are no tier signal."""
    recs = [_rec(f"c{i}", "ch1", cbe=True, difficulty="easy" if i < 3 else "hard")
            for i in range(6)]
    check = tier_check(_template(), _schemas(recs))
    assert check.available is False
    assert check.sentence == tiers_note(10, "Science") == (
        "Foundation and Advanced versions are not offered: in the Class 10 Science bank, "
        "questions of the same marks do not differ in a difficulty or Bloom level anyone "
        "judged, so every version would print this same paper.")


def test_tiers_are_available_on_judged_difficulties_and_say_nothing():
    recs = [_rec(f"p{i}", "ch1", difficulty="easy" if i < 3 else "hard") for i in range(6)]
    check = tier_check(_template(), _schemas(recs))
    assert (check.available, check.sentence) == (True, "")


# ---- the routes ---------------------------------------------------------------

@pytest.fixture
def split_bank(monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(SPLIT))


def _create(client, headers, *, count: int = 4, chapters: tuple[str, ...] = ("ch1",),
            share: float | None = None) -> str:
    body = _template(count, chapters, share).model_dump(by_alias=True, mode="json")
    r = client.post(BASE, json=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_the_availability_json_carries_the_competency_check_and_the_tiers(
        tmp_path, monkeypatch, split_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = _create(client, t1)
        body = client.post(f"{BASE}/{tid}/availability", json={}, headers=t1).json()
        comp = body["competency"]
        assert comp["status"] == "below_scope"
        assert comp["summary"] == "Competency-based: 0 of 4 questions (0%)"
        assert comp["detail"] == "Below CBSE's 50%. The whole syllabus would give 4 of 4 (100%)."
        assert comp["counted"] == COMPETENCY_RULE_TEXT
        assert (comp["wholeSyllabusPrinted"], comp["wholeSyllabusCompetencyBased"]) == (4, 4)
        assert body["tiers"] == {"available": False, "sentence": tiers_note(10, "Science")}

        whole = client.post(f"{BASE}/{tid}/availability",
                            json={"scope": {"chapterIds": []}}, headers=t1).json()
        assert whole["competency"]["status"] == "meets"
        assert whole["competency"]["detail"] == "CBSE asks for at least 50%."

        # The check is beside the report, never in it: `complete` and every
        # section are what plan() alone reports.
        bank = _schemas(SPLIT)
        saved = PaperTemplate.model_validate(client.get(f"{BASE}/{tid}", headers=t1).json())
        report, _ = plan(saved, tid, bank, build_scope_filter(saved.scope, bank))
        assert body["complete"] == report.complete
        assert body["sections"] == report.model_dump(by_alias=True, mode="json")["sections"]


def test_a_report_without_the_check_still_parses():
    """Clients and captures from before the check read as `competency` null."""
    report = AvailabilityReport.model_validate({
        "templateId": "t", "grade": 10, "subject": "Science", "bankQuestions": 0,
        "keyedQuestions": 0, "complete": True, "sections": []})
    assert report.competency is None and report.tiers is None


def test_a_template_paper_carries_the_share_the_tiers_and_the_sentence(
        tmp_path, monkeypatch, split_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        # Five asked for, four in ch1: a gap, so allowGaps.
        tid = _create(client, t1, count=5)
        r = client.post(GEN, json={"templateId": tid, "allowGaps": True, "setCount": 2},
                        headers=t1)
        assert r.status_code == 200, r.text
        body = r.json()
        paper, comp = body["paper"], body["availability"]["competency"]
        assert comp["status"] == "below_scope"
        assert paper["tiersAvailable"] is False
        assert paper["competencyShare"] == comp["share"] == 0.0
        assert paper["competencyTargetMet"] is False
        sentence = (f"{comp['summary']}. {comp['detail']}")
        assert sentence == ("Competency-based: 0 of 4 questions (0%). Below CBSE's 50%. "
                            "The whole syllabus would give 4 of 5 (80%).")
        assert paper["warnings"][0] == sentence
        # Notes are the availability report's own, as before: the sentence is
        # a warning about the paper, not a section note.
        assert sentence not in body["notes"]
        assert all(s["competencyShare"] == 0.0 for s in paper["sets"])


def test_a_template_paper_that_meets_50_percent_carries_no_sentence(
        tmp_path, monkeypatch, split_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = _create(client, t1, chapters=())
        body = client.post(GEN, json={"templateId": tid}, headers=t1).json()
        assert body["availability"]["competency"]["status"] == "meets"
        assert body["paper"]["competencyShare"] == 1.0
        assert not any(w.startswith("Competency-based:") for w in body["paper"]["warnings"])


def test_swapping_a_competency_question_for_a_plain_one_lowers_the_share(
        tmp_path, monkeypatch):
    # Two CBE questions print; a swap has only plain ones left.
    recs = [_rec(f"c{i}", "ch1", cbe=True, quality=0.9) for i in range(2)] + \
           [_rec(f"p{i}", "ch1") for i in range(3)]
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(recs))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = _create(client, t1, count=2, chapters=())
        gen = client.post(GEN, json={"templateId": tid, "setCount": 2}, headers=t1).json()
        paper = gen["paper"]
        assert paper["competencyShare"] == 1.0

        swap = client.post(f"/api/v1/papers/{paper['id']}/questions/1/swap", json={},
                           headers=t1)
        assert swap.status_code == 200, swap.text
        edited = swap.json()["paper"]
        assert swap.json()["questionId"].startswith("p")
        assert edited["competencyShare"] == 0.5 < paper["competencyShare"]
        assert edited["competencyTargetMet"] is True        # 50% meets CBSE's 50%

        # The stored paper says the same. Set B prints its own questions (the
        # two plain ones the swap did not take), so the swap leaves it as it
        # was, with its own share.
        stored = client.get(f"/api/v1/papers/{paper['id']}", headers=t1)
        assert stored.status_code == 200, stored.text
        assert stored.json()["competencyShare"] == 0.5
        set_b = client.get(f"/api/v1/papers/{paper['id']}_set_B", headers=t1).json()
        assert set_b["competencyShare"] == 0.0
        assert swap.json()["questionId"] not in {q["questionId"] for s in set_b["sections"]
                                                 for q in s["questions"]}


def test_removing_a_competency_question_recounts_the_share(tmp_path, monkeypatch):
    recs = [_rec(f"c{i}", "ch1", cbe=True, quality=0.9) for i in range(2)] + [_rec("p0", "ch1")]
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(recs))
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        tid = _create(client, t1, count=3, chapters=())
        paper = client.post(GEN, json={"templateId": tid}, headers=t1).json()["paper"]
        assert paper["competencyShare"] == 0.667
        r = client.delete(f"/api/v1/papers/{paper['id']}/questions/1", headers=t1)
        assert r.status_code == 200, r.text
        assert r.json()["removedQuestionIds"][0].startswith("c")
        assert r.json()["paper"]["competencyShare"] == 0.5


def test_report_competency_lives_with_the_paper():
    """One function stamps the share on every generation path, template path
    included (routes.py no longer keeps its own)."""
    from academicos.assessment import paper, routes

    assert callable(paper.report_competency)
    assert not hasattr(routes, "_report_competency")


# ---- the served bank ----------------------------------------------------------

_REAL_BANK = Path(__file__).resolve().parents[1] / "academicos-data" / "syllabus" / "questions.json"
needs_real_bank = pytest.mark.skipif(not _REAL_BANK.exists(),
                                     reason="the served question bank is not in this checkout")

# The six chapters the builder fixtures capture for 10 Science half-yearly
# (frontend/test/paper_builder/fixtures/manifest.json).
HALF = ["chemical-reactions-equations", "acids-bases-salts", "metals-non-metals",
        "carbon-compounds", "life-processes", "control-coordination"]


@pytest.fixture(scope="module")
def served_pools(tmp_path_factory):
    from academicos.config import Config

    cfg = Config(data_root=tmp_path_factory.mktemp("served"))
    cfg._load_baked_questions = True
    return {(s, g): pool_mod.build_pool(cfg, subject=s, grade=g)
            for s, g in (("Science", "X"), ("Science", "VI"), ("Mathematics", "X"))}


@needs_real_bank
def test_the_served_bank_reads_as_the_builder_will_show_it(tmp_path, monkeypatch, served_pools):
    for key, pool in served_pools.items():
        monkeypatch.setitem(pool_mod._CACHE, key, pool)
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")

        def availability(preset: str, chapters: list[str]) -> dict:
            r = client.post(f"{BASE}/{preset}/availability",
                            json={"scope": {"chapterIds": chapters}}, headers=t1)
            assert r.status_code == 200, r.text
            return r.json()

        half = availability("preset:cbse:10:science:half_yearly", HALF)
        # Measured on the rebuilt bank (2026-09-28), which no longer serves the
        # CBE items that point at a figure they do not carry: 10 of 30, because the bank had no
        # 2-mark or 4-mark Science 10 question and the paper printed 30 of its 39. With the
        # model-written ones (2026-10-04) it printed all 39, 13 of them competency-based (33%,
        # "below_scope"); with the second batch of them (2026-10-14: assertion-reason and case-based
        # Science 10 questions) the chosen chapters alone reach CBSE's 50%.
        assert half["competency"]["status"] == "meets"
        assert half["competency"]["summary"] == "Competency-based: 23 of 39 questions (59%)"
        # 22 of 31 (71%) until 2026-10-01. A section that names no share now
        # takes competency-based questions first (QA R-03), but one filed under
        # no current chapter (QA P-04) only as far as CBSE's 50%.
        assert half["competency"]["detail"] == "CBSE asks for at least 50%."
        # False until 2026-10-04: the paper had nothing to vary. With the model-written 2-mark and
        # 4-mark questions a Foundation or Advanced version can print other questions.
        assert half["tiers"]["available"] is True

        six = availability("preset:cbse:6:science:annual", [])
        assert six["competency"]["status"] == "below_bank"
        # 7 of 36 (19%) for a while on 2026-10-01 (QA P-04), back to 10 now
        # that a section with no share takes competency-based questions first.
        assert six["competency"]["summary"] == "Competency-based: 10 of 36 questions (28%)"
        assert six["competency"]["detail"] == (
            "Below CBSE's 50%. The Class 6 Science bank cannot reach it with this template: "
            "12 of the 243 questions it can use (5%) are competency-based.")

        maths = availability("preset:cbse:10:mathematics:annual", [])
        assert maths["competency"]["status"] == "meets"
        assert maths["competency"]["summary"] == "Competency-based: 36 of 38 questions (95%)"
        e = next(s for s in maths["sections"] if s["title"].startswith("Section E"))
        assert (e["filled"], e["needed"]) == (3, 3), e


# ---- edits recount the sentences, not just the numbers -------------------------
#
# Review of 5e90119: swap, pick and remove recounted competencyShare but left
# the generation-time sentences in paper.warnings, which the web paper step
# renders after every edit -- so the only share a teacher saw could contradict
# the paper ("Below CBSE's 50%" on a paper at 50%, "1 of 4" on a paper of 3).

# Plain questions ranked above the CBE ones, all in ch1: the paper prints the
# plain four (0%), and the CBE four are there to pick.
RANKED = ([_rec(f"p{i}", "ch1", quality=0.9) for i in range(4)]
          + [_rec(f"c{i}", "ch1", cbe=True, quality=0.5) for i in range(4)])


@pytest.fixture
def ranked_bank(monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(RANKED))


def _generate(client, headers) -> dict:
    # A template that asks for no competency-based questions, so the paper is
    # below 50% while the bank holds enough: what the sentences below are about.
    tid = _create(client, headers, share=0.0)
    r = client.post(GEN, json={"templateId": tid, "allowGaps": True}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["paper"]


def _competency_lines(paper: dict) -> list[str]:
    return [w for w in paper["warnings"] if "ompetency-based" in w]


def test_removing_a_question_recounts_the_competency_sentence(tmp_path, monkeypatch, ranked_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        assert paper["warnings"][0].startswith("Competency-based: 0 of 4 questions (0%). Below CBSE's 50%.")
        r = client.delete(f"/api/v1/papers/{paper['id']}/questions/1", headers=t1)
        assert r.status_code == 200, r.text
        edited = r.json()["paper"]
        assert edited["competencyShare"] == 0.0
        # Recounted, and the check's reason kept: it is about the bank and the
        # template, which a removal does not change (audit D78).
        assert _competency_lines(edited) == [
            "Competency-based: 0 of 3 questions (0%). Below CBSE's 50%. The bank has enough "
            "competency-based questions for this template (4 of the 8 it can use): swap or pick "
            "them in on the paper step."]


def test_picking_up_to_50_percent_drops_every_below_target_sentence(tmp_path, monkeypatch, ranked_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate(client, t1)
        for slot, qid in (("1", "c0"), ("2", "c1")):
            r = client.post(f"/api/v1/papers/{paper['id']}/questions/{slot}",
                            json={"questionId": qid}, headers=t1)
            assert r.status_code == 200, r.text
        edited = r.json()["paper"]
        assert (edited["competencyShare"], edited["competencyTargetMet"]) == (0.5, True)
        assert not any("Below CBSE" in w for w in edited["warnings"]), edited["warnings"]
        # What the builder re-reads after an edit says the same.
        stored = client.get(f"/api/v1/papers/{paper['id']}", headers=t1).json()
        assert not any("Below CBSE" in w for w in stored["warnings"]), stored["warnings"]



# ---- D78/D79: what generation said is what a reopened paper says -------------
#
# Audit 2026-09-28 (caf5e3d): set A carries the paper's id, and generation saved
# the paper and then each set, so set A's copy -- no warnings, no sets -- was
# written over the paper. A reopened paper showed no share, and the first edit
# lost the "Set B" lines (D78). A below-target paper stated set A's share twice,
# rounded two ways: "11 of 37 questions (30%)" and "Set A has 29.7%" (D79).

def _generate_sets(client, headers, sets: int) -> dict:
    tid = _create(client, headers, share=0.0)     # as `_generate`
    r = client.post(GEN, json={"templateId": tid, "allowGaps": True, "setCount": sets},
                    headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["paper"]


# Sets B and C print questions of their own (N-2-5), so each needs its own
# four plain questions to fall below 50% as set A does: twelve plain ones
# ranked above the four CBE ones.
RANKED_SETS = ([_rec(f"p{i}", "ch1", quality=0.9) for i in range(12)]
               + [_rec(f"c{i}", "ch1", cbe=True, quality=0.5) for i in range(4)])


@pytest.fixture
def ranked_sets_bank(monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _fixture_pool(RANKED_SETS))


def test_a_reopened_paper_says_what_generation_said(tmp_path, monkeypatch, ranked_sets_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate_sets(client, t1, 2)
        stored = client.get(f"/api/v1/papers/{paper['id']}", headers=t1).json()
        assert stored["warnings"] == paper["warnings"]
        assert _competency_lines(stored) == [
            "Competency-based: 0 of 4 questions (0%). Below CBSE's 50%. The bank has enough "
            "competency-based questions for this template (4 of the 16 it can use): swap or pick "
            "them in on the paper step.",
            "Set B competency-based: 0 of 4 questions (0%). Below CBSE's 50%."]
        assert [s["setLabel"] for s in stored["sets"]] == ["A", "B"]


def test_set_a_is_stated_once(tmp_path, monkeypatch, ranked_sets_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate_sets(client, t1, 3)
        lines = _competency_lines(paper)
        assert not any(w.startswith("Set A") for w in lines), lines
        assert [w.split(" competency-based")[0] for w in lines[1:]] == ["Set B", "Set C"]


def test_a_set_with_questions_of_its_own_states_its_own_share(tmp_path, monkeypatch, ranked_bank):
    """Set B prints the four CBE questions set A left (N-2-5): it meets 50%
    and says nothing, while set A's line stands."""
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate_sets(client, t1, 2)
        assert [s["competencyShare"] for s in paper["sets"]] == [0.0, 1.0]
        lines = _competency_lines(paper)
        assert len(lines) == 1 and lines[0].startswith("Competency-based: 0 of 4"), lines


def test_an_edit_keeps_the_set_lines(tmp_path, monkeypatch, ranked_sets_bank):
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        paper = _generate_sets(client, t1, 2)
        r = client.delete(f"/api/v1/papers/{paper['id']}/questions/1", headers=t1)
        assert r.status_code == 200, r.text
        lines = _competency_lines(r.json()["paper"])
        assert lines[0].startswith("Competency-based: 0 of 3 questions (0%). Below CBSE's 50%. "
                                   "The bank has enough"), lines
        assert lines[1:] == ["Set B competency-based: 0 of 3 questions (0%). Below CBSE's 50%."]


def test_every_share_sentence_is_the_one_shape():
    from academicos.assessment.competency import share_summary
    assert share_summary(11, 37) == "Competency-based: 11 of 37 questions (30%)"
    assert share_summary(1, 8, "B") == "Set B competency-based: 1 of 8 questions (13%)"
    assert share_summary(1, 1) == "Competency-based: 1 of 1 question (100%)"


def test_a_bank_that_could_reach_50_percent_is_not_blamed():
    """Review of 5e90119 (minor): 'below_bank' was the fallback whenever the
    printed share missed, so a template whose sections ranked plain questions
    first read "the bank cannot reach it ... 4 of the 8 questions it can use
    (50%) are competency-based" -- a sentence that refutes itself. The bank's
    ceiling decides: here the four CBE questions alone would fill the paper."""
    check = _check(_template(chapters=("ch1",), share=0.0), _schemas(RANKED))
    assert (check.printed, check.competency_based) == (4, 0)
    assert check.status == "below_choice"
    assert check.detail == ("Below CBSE's 50%. The bank has enough competency-based questions "
                            "for this template (4 of the 8 it can use): swap or pick them in "
                            "on the paper step.")


def test_a_bank_that_cannot_reach_50_percent_is_still_named():
    recs = [_rec(f"p{i}", "ch1", quality=0.9) for i in range(7)] + [_rec("c0", "ch1", cbe=True)]
    check = _check(_template(chapters=("ch1",)), _schemas(recs))
    assert check.status == "below_bank"


# ---- step 8: the difficulty-mix note needs a judged difficulty ---------------

def _mixed_section():
    from academicos.assessment.schemas import TemplateSection
    return TemplateSection.model_validate({
        "title": "Section A", "questionCount": 4, "marksEach": 1,
        "difficultyMix": {"easy": 0.25, "medium": 0.5, "hard": 0.25}})


def test_no_difficulty_mix_note_when_no_pick_has_a_judged_difficulty():
    """The note said "the bank has too few at the requested level" of values
    the bank set from marks -- on 168 of 170 class 6-10 preset sections, none
    of them with a judged difficulty among its picks -- while the tier
    sentence on the same screen says no difficulty was judged."""
    from academicos.assessment.paper_templates import _LeftOut, _mix_notes
    inferred = _schemas([_rec(f"p{i}", "ch1") for i in range(4)])
    for q in inferred:
        q.metadata["difficultyInferred"] = True
    cbe = _schemas([_rec(f"c{i}", "ch1", cbe=True) for i in range(4)])
    for picked in (inferred, cbe):
        notes, _ = _mix_notes(_mixed_section(), picked, _LeftOut())
        assert not any("difficulty is" in n for n in notes), notes


def test_a_judged_difficulty_still_gets_the_note():
    from academicos.assessment.paper_templates import _LeftOut, _mix_notes
    picked = _schemas([_rec(f"p{i}", "ch1", difficulty="easy") for i in range(4)])
    notes, _ = _mix_notes(_mixed_section(), picked, _LeftOut())
    assert any("difficulty is easy/medium/hard 4/0/0" in n for n in notes), notes


def test_a_section_that_names_no_share_takes_competency_based_questions_first():
    """QA R-03: only the presets' case-study sections name a share, so the
    rest of a paper's share was whatever the order gave -- 95% on a Class 10
    Mathematics half-yearly while CBE items sorted first by id, 8% once a
    teacher's recent papers held them. A section that names none takes them
    first; one that names a share, 0 included, keeps it."""
    bank = _schemas(RANKED)       # the plain questions rank above the CBE ones
    assert _check(_template(), bank).summary == "Competency-based: 4 of 4 questions (100%)"
    assert _check(_template(share=0.0), bank).summary == "Competency-based: 0 of 4 questions (0%)"
    assert _check(_template(share=0.5), bank).summary == "Competency-based: 2 of 4 questions (50%)"
