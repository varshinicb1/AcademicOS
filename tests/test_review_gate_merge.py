"""QB-5 / R-C3 at the serving gate (corpus/bank_merge): a model- or
teacher-written question new to the bank leaves the merge `in_review`, and the
offline bundle leaves it out; the ones served before the gate stay served."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.corpus import bank_merge as bm  # noqa: E402
from test_ai_bank_source import _record  # noqa: E402
from test_bank_merge import board  # noqa: E402
from test_merge_question_banks import _write, layout  # noqa: E402,F401 - `layout` is a fixture

import merge_question_banks as mqb  # noqa: E402

SERVED = ROOT / "academicos-data" / "syllabus" / "questions.json"
BEFORE = ROOT / "academicos-data" / "syllabus" / bm.SERVED_BEFORE_REVIEW_NAME


def test_only_a_new_written_record_goes_to_review_and_nothing_is_changed_in_place():
    old, new, teacher, official = _record(), _record(), _record(), board()
    old["id"], new["id"], teacher["id"] = "ai:old", "ai:new", "t:new"
    teacher["source"] = "teacher_created"
    records = [old, new, teacher, official]
    out, marked = bm.mark_review_state(records, frozenset({"ai:old"}))
    assert marked == 2
    assert [r.get("reviewState") for r in out] == [old.get("reviewState"), "in_review", "in_review",
                                                  official.get("reviewState")]
    assert new.get("reviewState") != "in_review", "the input record is not changed"


def _ai_layout(layout, listed):
    rec = _record()
    _write(layout.ai, [rec])
    if listed is not None:
        layout.before_review.write_text(json.dumps({"ids": listed}), encoding="utf-8")
    return rec["id"]


def _with_ai(layout, tmp_path):
    layout.ai = tmp_path / "ai.json"
    layout.before_review = tmp_path / "before.json"
    return layout


def test_the_merge_refuses_without_the_list_of_questions_served_before_review(layout, tmp_path):
    _ai_layout(_with_ai(layout, tmp_path), None)
    before = layout.served.read_bytes()
    assert mqb.run(layout, check=False) == 2
    assert layout.served.read_bytes() == before and not layout.apk.exists()


def test_a_new_written_question_is_served_in_review_and_kept_out_of_the_offline_bundle(layout, tmp_path):
    qid = _ai_layout(_with_ai(layout, tmp_path), [])
    assert mqb.run(layout, check=False) == 0
    served = {q["id"]: q for q in json.loads(layout.served.read_text(encoding="utf-8"))["questions"]}
    offline = json.loads(layout.apk.read_text(encoding="utf-8"))
    assert served[qid]["reviewState"] == "in_review"
    assert qid not in {q["id"] for q in offline["questions"]}
    assert offline["exportedCount"] == len(offline["questions"]) == len(served) - 1


def test_a_written_question_served_before_the_gate_stays_served(layout, tmp_path):
    qid = _ai_layout(_with_ai(layout, tmp_path), [])
    mqb.run(layout, check=False)
    layout.before_review.write_text(json.dumps({"ids": [qid]}), encoding="utf-8")
    assert mqb.run(layout, check=False) == 0
    served = {q["id"]: q for q in json.loads(layout.served.read_text(encoding="utf-8"))["questions"]}
    assert served[qid].get("reviewState") != "in_review"
    assert layout.served.read_bytes() == layout.apk.read_bytes()


def test_every_written_question_served_today_is_on_the_list_and_none_waits():
    """The owner kept the written questions served before the gate (R-C3): the
    list holds each of them, so the gate changes nothing served on the day it
    lands. A new one off the list is what waits."""
    listed = bm.load_served_before_review(BEFORE)
    records = json.loads(SERVED.read_text(encoding="utf-8"))["questions"]
    written = {str(r["id"]) for r in records if bm.needs_review(r)}
    assert written and written <= listed
    assert not [r["id"] for r in records if r.get("reviewState") == "in_review"]
