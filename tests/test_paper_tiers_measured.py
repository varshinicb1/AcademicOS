"""Differentiated versions that really differ, on measured difficulty (EX-3).

Audit 2026-09-30: Foundation, Standard and Advanced quick papers printed
identical questions on 14/14 class-subject pairs, because no source in the
bank judges a question's difficulty -- it is inferred from the marks, or an
importer's default. The marks teachers enter now measure it (each question's
facility, `assessment/facility.py`), and where a question has a measured
difficulty the versions rank on it in preference to the inferred one. Each
version says how many of its questions had one.
"""
from __future__ import annotations

from academicos.assessment import facility, selection
from test_paper_generation_honesty import _bp, _q, _section
from test_paper_swap_pick import _pool, _rec
from test_paper_templates import _boot_client, _register

QUICK = "/api/v1/papers/quick-generate"


def _bank():
    """Eight 1-mark questions students found easy and eight they found
    hard, every one's own difficulty an inferred "medium"."""
    return ([_q(f"easy{i}", 1, difficulty="medium", metadata={"difficultyInferred": True}) for i in range(8)]
            + [_q(f"hard{i}", 1, difficulty="medium", metadata={"difficultyInferred": True}) for i in range(8)])


def _measured(monkeypatch):
    values = {**{f"easy{i}": (0.9, 40) for i in range(8)}, **{f"hard{i}": (0.2, 40) for i in range(8)}}
    monkeypatch.setattr(facility, "lookup", lambda ids: {i: values[i] for i in ids if i in values})


def _picked(bank, tier):
    res = selection.optimize([q.model_copy(deep=True) for q in bank], _bp([_section("A", 1, 4)], tier))
    return {q.id for q in res.selected_questions}, res


def test_without_a_measurement_every_version_prints_the_same_paper():
    bank = _bank()
    assert _picked(bank, "foundation")[0] == _picked(bank, "advanced")[0] == _picked(bank, "standard")[0]


def test_a_measured_difficulty_is_preferred_and_the_versions_differ(monkeypatch):
    _measured(monkeypatch)
    bank = _bank()
    assert facility.annotate(bank) == 16
    assert selection.difficulty_signal(bank[0]) == "easy" and selection.difficulty_signal(bank[8]) == "hard"
    foundation, res = _picked(bank, "foundation")
    advanced, _ = _picked(bank, "advanced")
    assert foundation == {f"easy{i}" for i in range(4)}
    assert advanced == {f"hard{i}" for i in range(4)}
    assert res.optimization_metrics["tierSignals"]["available"] is True


def test_a_measurement_under_twenty_answers_is_not_used(monkeypatch):
    from academicos.operations.paper_marks import MarksMixin
    seen = {}

    class Store(MarksMixin):
        def _fetchall(self, sql, params):
            seen["min"] = params[0]
            return []
    monkeypatch.setattr("academicos.operations.routes._cfg", object())
    monkeypatch.setattr("academicos.operations.routes.store", lambda: Store())
    assert facility.lookup(["q1"]) == {} and seen["min"] == facility.MIN_RESPONSES == 20


LEVELS = {"easy": 0.92, "medium": 0.55, "hard": 0.18}


def _quick_pool():
    """24 1-mark questions with distinct stems, eight students found easy,
    eight middling and eight hard; each record's own difficulty "medium"."""
    words = ("copper", "enzyme", "glacier", "harvest", "lantern", "orbit", "pigment", "quartz")
    return _pool([dict(_rec(f"{level}{i}", 1, "ch1", n * 8 + i,
                            stem=f"Describe the {words[i]} in {level} terms, question {n}-{i}."),
                       source="cbse_board_paper")
                  for n, level in enumerate(LEVELS) for i in range(8)])


def test_quick_paper_versions_differ_on_measured_difficulty_and_say_so(tmp_path, monkeypatch):
    from academicos.assessment import pool as pool_mod
    from academicos.operations.routes import store
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _quick_pool())
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")

        def version(tier):
            r = client.post(QUICK, headers=t1, json={"subject": "Science", "grade": 10, "totalMarks": 6,
                                                       "tier": tier, "preview": True})
            assert r.status_code == 200, r.text
            return r.json()

        def printed(p):
            return {q["questionId"] for s in p["sections"] for q in s["questions"]}

        before = {t: version(t) for t in ("foundation", "advanced")}
        assert printed(before["foundation"]) == printed(before["advanced"])
        assert before["foundation"]["difficultyMeasured"] == 0
        assert any(w.startswith("Foundation version: none of its 6 questions") for w in before["foundation"]["warnings"])

        with store()._conn_lock:
            store().conn.executemany(
                "INSERT INTO question_facility (question_id, responses, facility, updated_at) VALUES (?,?,?,?)",
                [(f"{level}{i}", 30, value, "2026-10-01") for level, value in LEVELS.items() for i in range(8)])
            store().conn.commit()
        after = {t: version(t) for t in ("foundation", "standard", "advanced")}
        assert printed(after["foundation"]) <= {f"easy{i}" for i in range(8)}
        assert printed(after["standard"]) <= {f"medium{i}" for i in range(8)}
        assert printed(after["advanced"]) <= {f"hard{i}" for i in range(8)}
        for tier, p in after.items():
            assert p["tiersAvailable"] is True, (tier, p["warnings"])
            assert p["difficultyMeasured"] == 6, tier
            assert f"{tier.capitalize()} version: 6 of its 6 questions have a difficulty measured" \
                in " ".join(p["warnings"]), p["warnings"]
