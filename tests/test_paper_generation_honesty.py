"""A generated paper's tiers, sets and CBQ share mean what they say (Task 17, items 3-5).

The audit (2026-09-21) found three controls that did nothing a teacher could
see: a tier change could not change the paper where the bank carries no
difficulty signal, set B/C were reorderings of set A's questions, and the
quick path dropped the optimizer's CBQ warning. Items 1-2 (gaps and totals)
live in the paper-builder stream.

The real served bank is read, never written.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app  # noqa: E402
from academicos.assessment import selection  # noqa: E402
from academicos.assessment.mapping import to_question_schema  # noqa: E402
from academicos.assessment.paper import generate_paper_sets  # noqa: E402
from academicos.assessment.pool import PoolQuestion, QuestionPool, build_pool  # noqa: E402
from academicos.assessment.schemas import (  # noqa: E402
    AnswerSchemeSchema,
    Blueprint,
    ChapterWeights,
    CompetencyWeights,
    QuestionSchema,
    SectionBlueprint,
)
from academicos.assessment.templates import TIER_BLOOM, TIER_DIFFICULTY, default_sections  # noqa: E402
from academicos.config import Config  # noqa: E402
from academicos.models.academic import Question  # noqa: E402

TIERS_UNAVAILABLE = "Tiers unavailable for this subject"


# ---- fixtures ---------------------------------------------------------------

# Every fixture stem must read as its own question. "Question stem for
# {qid}, explain your answer." differs in one token, which `pool.near_duplicate`
# (Task 903's guard, on the optimizer since the paper-builder stream) correctly
# calls the same question -- so a fixture bank of those stems fills one slot per
# section and every tier prints the same short paper. Neutral nouns, as
# tests/test_paper_templates.py does for the same reason.
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


def _q(qid: str, marks: int, *, difficulty: str = "easy", bloom: str = "understand",
       qtype: str = "short_answer", source: str = "cbse_question_bank",
       chapters: list[str] | None = None, metadata: dict | None = None,
       quality: float = 0.7) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    return QuestionSchema(
        id=qid, question_bank_id="bank", subject="Science", grade=10,
        chapter_ids=chapters or ["ch1"], bloom_level=bloom, difficulty=difficulty,
        type=qtype, stem=f"Question stem for {qid}: explain {_distinct(qid)}.",
        answer_scheme=AnswerSchemeSchema(total_marks=marks, model_answer=f"Answer {qid}"),
        estimated_time_minutes=2, marks=marks, source=source, quality_score=quality,
        created_at=now, updated_at=now, metadata=metadata or {},
    )


def _section(label: str, marks: int, count: int, *, choice: bool = False) -> SectionBlueprint:
    return SectionBlueprint(
        id=f"sec_{label.lower()}", label=label, name=f"Section {label}",
        marks_per_question=marks, question_count=count, total_marks=marks * count,
        has_internal_choice=choice, internal_choice_count=1 if choice else 0,
    )


def _bp(sections: list[SectionBlueprint], tier: str) -> Blueprint:
    return Blueprint(
        total_marks=sum(s.total_marks for s in sections), duration_minutes=60,
        difficulty=TIER_DIFFICULTY[tier], bloom=TIER_BLOOM[tier],
        chapter_weights=ChapterWeights(), competency_weights=CompetencyWeights(),
        sections=sections, tier=tier, competency_percentage=0.5,
    )


def _ids(candidates: list[QuestionSchema], sections: list[SectionBlueprint], tier: str):
    res = selection.optimize([q.model_copy(deep=True) for q in candidates], _bp(sections, tier))
    return {q.id for q in res.selected_questions}, res


@pytest.fixture(scope="module")
def served(tmp_path_factory):
    """The real served bank's class 10 pools, as the web path loads them."""
    cfg = Config(data_root=tmp_path_factory.mktemp("served"))
    cfg._load_baked_questions = True
    return {s: build_pool(cfg, subject=s, grade="X") for s in ("Science", "Mathematics")}


def _client_for(tmp_path, monkeypatch, pool: QuestionPool):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr("academicos.assessment.routes.get_pool",
                        lambda cfg, subject, grade, llm=None: pool)
    return TestClient(app)


def _auth(client) -> dict:
    # Registration is by invite since security Task 301 (assessment/users.py):
    # a body carrying its own schoolId/role is a 403 now, so the invite is
    # minted through the store the running app is using.
    from _auth_helpers import register_invited

    body = register_invited(client, "school_1", "t1@school.org")
    return {"Authorization": f"Bearer {body['token']}"}


def _printed_ids(paper: dict) -> list[str]:
    """Every question a set prints, OR alternatives included."""
    out = []
    for s in paper["sections"]:
        for q in s["questions"]:
            out.append(q["questionId"])
            if q.get("internalChoiceQuestionId"):
                out.append(q["internalChoiceQuestionId"])
    return out


# ---- 3. tiers use real signals ----------------------------------------------

def test_a_tier_change_changes_the_selection_where_difficulty_varies():
    """Same marks, different authored difficulty: foundation and advanced must differ."""
    sec = [_section("A", 1, 3)]
    pool = ([_q(f"easy{i}", 1, difficulty="easy") for i in range(4)]
            + [_q(f"hard{i}", 1, difficulty="hard") for i in range(4)])
    foundation, res = _ids(pool, sec, "foundation")
    advanced, _ = _ids(pool, sec, "advanced")
    assert foundation != advanced
    assert all(i.startswith("easy") for i in foundation)
    assert all(i.startswith("hard") for i in advanced)
    assert res.optimization_metrics["tierSignals"]["available"] is True
    assert not any(TIERS_UNAVAILABLE in w for w in res.warnings)


def test_difficulty_that_only_restates_marks_is_no_tier_signal():
    """Every 1-mark question easy, every 3-mark one medium, Bloom the default: a
    tier cannot change anything, and the paper says so instead of doing nothing."""
    secs = [_section("A", 1, 2), _section("C", 3, 1)]
    pool = ([_q(f"one{i}", 1, difficulty="easy") for i in range(4)]
            + [_q(f"three{i}", 3, difficulty="medium") for i in range(3)])
    foundation, res = _ids(pool, secs, "foundation")
    advanced, res_adv = _ids(pool, secs, "advanced")
    assert foundation == advanced
    assert res_adv.optimization_metrics["tierSignals"]["available"] is False
    assert any(TIERS_UNAVAILABLE in w for w in res_adv.warnings)


def test_placeholder_and_inferred_values_are_not_signals():
    """The SQP builder writes difficulty "medium" on every item; bank_merge marks a
    value it supplied `difficultyInferred`. Neither may steer a tier."""
    sec = [_section("A", 1, 2)]
    pool = ([_q(f"cbe{i}", 1, difficulty="easy") for i in range(3)]
            + [_q(f"sqp{i}", 1, difficulty="medium", source="cbse_sample_paper") for i in range(3)]
            + [_q(f"inf{i}", 1, difficulty="hard", metadata={"difficultyInferred": True})
               for i in range(3)])
    foundation, _ = _ids(pool, sec, "foundation")
    advanced, res = _ids(pool, sec, "advanced")
    assert foundation == advanced
    assert res.optimization_metrics["tierSignals"]["available"] is False
    assert any(TIERS_UNAVAILABLE in w for w in res.warnings)


def test_the_registry_path_marks_what_it_made_up():
    """mapping.py supplies a Bloom level and a marks-derived difficulty when
    extraction found none; the record must say they were supplied."""
    pq = PoolQuestion(
        question=Question(canonical_id="reg1", title="t", marks=3.0,
                          source_text="Explain the process of photosynthesis in plants."),
        subject="Science", grade="X", academic_year="2024", chapter_id="ch1",
        chapter_name="Life Processes", chapter_confidence=0.9, text_hash="h")
    schema = to_question_schema(pq)
    assert schema.metadata.get("bloomInferred") is True
    assert schema.metadata.get("difficultyInferred") is True


def test_a_signal_with_no_choice_left_is_still_unavailable():
    """Difficulty varies, but the section takes every question: no tier can
    change the paper, so it must not be reported as one that did."""
    sec = [_section("A", 1, 2)]
    pool = [_q("easy0", 1, difficulty="easy"), _q("hard0", 1, difficulty="hard")]
    _, res = _ids(pool, sec, "advanced")
    assert res.optimization_metrics["tierSignals"]["available"] is True
    assert selection.tier_changed_selection(pool, _bp(sec, "advanced"), None,
                                            res.selected_questions) is False
    varied = pool + [_q("easy1", 1, difficulty="easy"), _q("hard1", 1, difficulty="hard")]
    _, res = _ids(varied, sec, "advanced")
    assert selection.tier_changed_selection(varied, _bp(sec, "advanced"), None,
                                            res.selected_questions) is True


def _quick(client, auth, subject: str, tier: str) -> dict:
    resp = client.post("/api/v1/papers/quick-generate", headers=auth, json={
        "subject": subject, "grade": 10, "totalMarks": 80, "tier": tier})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.parametrize("subject", ["Science", "Mathematics"])
def test_on_the_served_bank_a_tier_acts_or_says_it_cannot(served, subject, tmp_path,
                                                          monkeypatch):
    """Measured on the real bank through the tier control: a foundation or
    advanced paper differs from the standard one, or says tiers are unavailable."""
    with _client_for(tmp_path, monkeypatch, served[subject]) as client:
        auth = _auth(client)
        standard = _quick(client, auth, subject, "standard")
        assert standard["tiersAvailable"] is not None
        for tier in ("foundation", "advanced"):
            paper = _quick(client, auth, subject, tier)
            if paper["tiersAvailable"]:
                assert set(_printed_ids(paper)) != set(_printed_ids(standard)), tier
            else:
                assert any(TIERS_UNAVAILABLE in w for w in paper["warnings"]), tier


# ---- 4. parallel sets are alternative questions -----------------------------

def test_the_sets_of_a_science_10_paper_are_mostly_different_and_honest_about_the_rest(
        served, tmp_path, monkeypatch):
    """Sets B and C draw fresh questions of the same marks and type; where the
    bank has none left they repeat one of set A's, and both setOverlap and a
    warning say how many. The original form of this test demanded no repeat at
    all, which the real bank cannot give at 80 marks."""
    with _client_for(tmp_path, monkeypatch, served["Science"]) as client:
        resp = client.post("/api/v1/papers/quick-generate", headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 80, "setCount": 3})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    sets = data["sets"]
    assert [s["setLabel"] for s in sets] == ["A", "B", "C"]
    printed = [_printed_ids(s) for s in sets]
    assert all(printed)
    # Same shape: each position holds a question of the same marks and type.
    shape = [[(q["marks"], q["type"]) for s in p["sections"] for q in s["questions"]]
             for p in sets]
    assert shape[0] == shape[1] == shape[2]
    # Most of each later set is new. An 80-mark Science 10 paper prints 37
    # questions a set, and the bank holds few long-answer questions, so some
    # repeats are unavoidable -- but every one is counted and said out loud
    # (measured 2026-09-23: 7 of 37 shared, setOverlap {A:0, B:7, C:7}).
    for label, ids in zip(("A", "B", "C"), printed):
        repeats = len(set(ids) & set(printed[0])) if label != "A" else 0
        assert data["setOverlap"][label] == repeats, (label, repeats)
        assert repeats < len(ids) / 2, (label, repeats, len(ids))
        if repeats:
            assert any(f"Set {label} repeats" in w for w in data["warnings"]), data["warnings"]
    assert data["setOverlap"]["A"] == 0


def test_when_the_pool_runs_out_the_overlap_is_reported():
    sec = [_section("A", 1, 2)]
    bp = _bp(sec, "standard")
    primary = [_q("p1", 1), _q("p2", 1)]
    pool = primary + [_q("x1", 1), _q("other_type", 1, qtype="mcq"), _q("two_mark", 2)]
    paper = generate_paper_sets(
        paper_id="p", assessment_id="a", assessment_title="T", subject="Science", grade=10,
        blueprint=bp, selected_questions=primary, set_count=3, alternatives_pool=pool)
    b = [q.question_id for q in paper.sets[1].sections[0].questions]
    c = [q.question_id for q in paper.sets[2].sections[0].questions]
    # Only x1 is an alternative of the same marks and type: B takes it and
    # repeats one of A's; C has nothing new left and repeats both.
    assert "x1" in b and "other_type" not in b + c and "two_mark" not in b + c
    assert paper.set_overlap == {"A": 0, "B": 1, "C": 2}


# ---- 5. the CBQ share is reported -------------------------------------------

def _plain_pool() -> QuestionPool:
    """1- and 2-mark recall questions: no competency-based question at all."""
    qs = []
    for i in range(30):
        marks = 1 if i < 20 else 2
        qs.append(PoolQuestion(
            question=Question(canonical_id=f"plain{i}", title=f"q{i}", marks=float(marks),
                              source_text=f"State the definition of term number {i} clearly."),
            subject="Science", grade="X", academic_year="2024", chapter_id="ch1",
            chapter_name="Ch", chapter_confidence=0.9, text_hash=f"h{i}"))
    return QuestionPool(questions=qs)


def test_quick_generate_reports_the_cbq_share_and_keeps_the_warning(tmp_path, monkeypatch):
    with _client_for(tmp_path, monkeypatch, _plain_pool()) as client:
        resp = client.post("/api/v1/papers/quick-generate", headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 20, "examType": "class_test"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["competencyShare"] == 0.0
    assert data["competencyTargetMet"] is False
    assert any("competency-based" in w for w in data["warnings"])


def test_the_served_bank_paper_reports_its_cbq_share(served, tmp_path, monkeypatch):
    with _client_for(tmp_path, monkeypatch, served["Science"]) as client:
        resp = client.post("/api/v1/papers/quick-generate", headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 80})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    flags = [q["isCompetency"] for s in data["sections"] for q in s["questions"]]
    assert data["competencyShare"] == round(sum(flags) / len(flags), 3)
    assert data["competencyTargetMet"] is (data["competencyShare"] >= 0.5)


# ---- review fixes: sets stay in the chosen chapters; each set's CBQ share ----

def _largest_chapters(pool: QuestionPool, n: int) -> list[str]:
    from collections import Counter
    counts = Counter(q.chapter_id for q in pool.questions if q.chapter_id)
    return [c for c, _ in counts.most_common(n)]


def test_sets_b_and_c_stay_in_the_chosen_chapters(served, tmp_path, monkeypatch):
    """A unit test on chapters 1-3 must not print, in set B or C, a question
    from a chapter students have not been taught. Where a set cannot stay in
    them it repeats a set A question, and setOverlap says so."""
    pool = served["Science"]
    chosen = _largest_chapters(pool, 3)
    chapter_of = {q.id: set(q.chapter_ids) for q in map(to_question_schema, pool.questions)}
    with _client_for(tmp_path, monkeypatch, pool) as client:
        resp = client.post("/api/v1/papers/quick-generate", headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 40, "setCount": 3,
            "chapterIds": chosen})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    sets = {s["setLabel"]: _printed_ids(s) for s in data["sets"]}
    outside = {label: [i for i in ids if not chapter_of[i] & set(chosen)]
               for label, ids in sets.items()}
    if outside["A"]:
        # Set A may only borrow with the optimizer saying so.
        assert any("shortfall" in w for w in data["warnings"]), outside["A"]
    for label in ("B", "C"):
        # Anything outside the chapters is a set A repeat, counted as overlap.
        assert set(outside[label]) <= set(sets["A"]), (label, outside[label])
        assert data["setOverlap"][label] >= len(outside[label]), label


def test_each_set_reports_its_own_cbq_share(served, tmp_path, monkeypatch):
    with _client_for(tmp_path, monkeypatch, served["Science"]) as client:
        resp = client.post("/api/v1/papers/quick-generate", headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 40, "setCount": 3,
            "chapterIds": _largest_chapters(served["Science"], 3)})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for s in data["sets"]:
        flags = [q["isCompetency"] for sec in s["sections"] for q in sec["questions"]]
        assert s["competencyShare"] == round(sum(flags) / len(flags), 3), s["setLabel"]
        assert s["competencyTargetMet"] is (s["competencyShare"] >= 0.5), s["setLabel"]
        if not s["competencyTargetMet"]:
            assert any(f"Set {s['setLabel']}" in w and "competency-based" in w
                       for w in data["warnings"]), s["setLabel"]
    assert data["competencyShare"] == data["sets"][0]["competencyShare"]


def test_a_set_under_the_cbq_target_is_warned_on_the_custom_path(tmp_path, monkeypatch):
    """/papers/generate: sets B/C are other questions, so their share is their own."""
    pool = _plain_pool()
    primary = [to_question_schema(q) for q in pool.questions[:2]]
    sec = [_section("A", 1, 2)]
    with _client_for(tmp_path, monkeypatch, pool) as client:
        resp = client.post("/api/v1/papers/generate", headers=_auth(client), json={
            "assessmentId": "none", "selectedQuestions": [q.model_dump(mode="json", by_alias=True) for q in primary],
            "blueprint": _bp(sec, "standard").model_dump(mode="json", by_alias=True),
            "template": {"id": "tpl_1", "schoolId": "school_1", "name": "Default"},
            "setCount": 3})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert [s["competencyShare"] for s in data["sets"]] == [0.0, 0.0, 0.0]
    for label in ("A", "B", "C"):
        assert any(f"Set {label}" in w and "competency-based" in w for w in data["warnings"])


def test_sets_b_and_c_obey_the_section_difficulty_and_bloom_limits():
    """Set A obeys a section's allowed difficulties and Bloom levels because
    optimize() enforces them; sets B and C must too. A 'hard' or 'apply'
    1-mark question may not stand in for set A's easy recall question in a
    section limited to easy/medium and remember/understand -- set A's
    question is reused instead, and the overlap counted."""
    sec = _section("A", 1, 1)
    sec.allowed_difficulties = ["easy", "medium"]
    sec.allowed_bloom_levels = ["remember", "understand"]
    bp = _bp([sec], "standard")
    primary = [_q("p1", 1, difficulty="easy", bloom="remember")]
    pool = primary + [
        _q("too_hard", 1, difficulty="hard", bloom="remember", quality=0.99),
        _q("too_high", 1, difficulty="easy", bloom="apply", quality=0.99),
        _q("fits", 1, difficulty="medium", bloom="understand", quality=0.1),
    ]
    paper = generate_paper_sets(
        paper_id="p", assessment_id="a", assessment_title="T", subject="Science", grade=10,
        blueprint=bp, selected_questions=primary, set_count=3, alternatives_pool=pool)
    b = [q.question_id for q in paper.sets[1].sections[0].questions]
    c = [q.question_id for q in paper.sets[2].sections[0].questions]
    assert b == ["fits"]
    assert c == ["p1"]
    assert paper.set_overlap == {"A": 0, "B": 0, "C": 1}


def test_a_paper_that_borrows_outside_the_chosen_chapters_says_so(served, tmp_path, monkeypatch):
    """`optimize` records every borrowing in `gaps` -- "filled N of the
    shortfall from outside the selected chapters" -- and neither generate path
    ever copied `gaps` into the response. A teacher setting a unit test on
    three chapters was handed questions from others with nothing saying so
    (merge of 2026-09-23: 3 of 20 on Science 10, 40 marks)."""
    pool = served["Science"]
    chosen = _largest_chapters(pool, 3)
    chapter_of = {q.id: set(q.chapter_ids) for q in map(to_question_schema, pool.questions)}
    with _client_for(tmp_path, monkeypatch, pool) as client:
        resp = client.post("/api/v1/papers/quick-generate", headers=_auth(client), json={
            "subject": "Science", "grade": 10, "totalMarks": 40, "setCount": 1,
            "chapterIds": chosen})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    printed = _printed_ids(data["sets"][0] if data["sets"] else data)
    outside = [i for i in printed if not chapter_of[i] & set(chosen)]
    if outside:
        assert any("outside the selected chapters" in w for w in data["warnings"]), data["warnings"]


def test_a_field_name_the_request_does_not_have_is_refused(served, tmp_path, monkeypatch):
    """`{"parallelSets": 5}` returned 200 and one set: the field the client
    meant is `setCount`, and an unknown key was dropped in silence, so a
    teacher asking for five papers got one and was told nothing (re-audit,
    2026-09-23). A request the server cannot honour must fail loudly."""
    with _client_for(tmp_path, monkeypatch, served["Science"]) as client:
        headers = _auth(client)
        good = client.post("/api/v1/papers/quick-generate", headers=headers, json={
            "subject": "Science", "grade": 10, "totalMarks": 40, "setCount": 3})
        assert good.status_code == 200, good.text
        assert len(good.json()["sets"]) == 3

        typo = client.post("/api/v1/papers/quick-generate", headers=headers, json={
            "subject": "Science", "grade": 10, "totalMarks": 40, "parallelSets": 5})
    assert typo.status_code == 422, typo.text
    assert "parallelSets" in typo.text
