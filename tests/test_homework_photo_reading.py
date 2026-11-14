"""TA-4: AI reads the photos of written homework and suggests marks per
question (operations/homework_ai.py). The vision provider and the LLM marker
are replaced: these tests prove what is sent, when, for whom, and what the
teacher sees -- not the provider's accuracy."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from test_dashboard_feed_photos import PNG
from test_homework import _create, w  # noqa: F401 - `w` is a fixture

READ = "1. A\n\n3. The angle of incidence equals the angle of reflection. They lie in the same plane."


@pytest.fixture
def ai(monkeypatch):
    """A configured provider that records every photo it is sent."""
    from academicos.assessment import imaging, llm_evaluate, vision
    from academicos.assessment.evaluate import Evaluation

    sent: list[bytes] = []
    marked: list[tuple[str, str]] = []
    monkeypatch.setattr(vision, "api_key", lambda: "test-key")

    def no_preprocess(path, workdir, page_no):
        raise RuntimeError("no OpenCV in this test")

    def ocr(path, page_no, *, workdir, language="en-IN", crop_furniture=True):
        assert crop_furniture is False, "a phone photo has no booklet margins to crop"
        sent.append(path.read_bytes())
        return vision.PageOCR(page_no=page_no, text=READ)

    def mark(question, scheme, answer, *, concept_label=None):
        marked.append((question.id, answer))
        return Evaluation(question_id=question.id, awarded_marks=2, max_marks=question.marks,
                          verdict="fullCredit", confidence=0.8, reasoning="both laws stated",
                          ocr_warnings=["handwriting partly unclear"])

    monkeypatch.setattr(imaging, "preprocess_page", no_preprocess)
    monkeypatch.setattr(vision, "ocr_page", ocr)
    monkeypatch.setattr(llm_evaluate, "evaluate_answer_llm", mark)
    return type("AI", (), {"sent": sent, "marked": marked})


def _handed_in_with_photo(w, who="s1"):
    hw = _create(w, "ana", questionIds=["q1", "q2", "q3"]).json()
    up = w.c.post(f"/api/v1/my-homework/{hw['id']}/photos", files={"file": ("p.png", PNG, "image/png")},
                  headers=getattr(w, who))
    assert up.status_code == 200, up.text
    # q1 typed in the app; q2 and q3 only on paper
    out = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}}, headers=getattr(w, who))
    assert out.status_code == 200, out.text
    return hw


def _url(hw, w, sid="s1", what="read-photos"):
    return f"/api/v1/homework/{hw['id']}/submissions/{w.ids[sid]}/{what}"


def test_the_teacher_gets_suggested_marks_for_what_was_written(w, ai):
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    hw = _handed_in_with_photo(w)
    r = w.c.post(_url(hw, w), headers=w.ana)
    assert r.status_code == 202, r.text
    assert ai.sent == [PNG], "the photo, as uploaded, after straightening failed"
    # the typed question is not read again; q2 has nothing under its number
    assert [q for q, _ in ai.marked] == ["q2", "q3"]
    assert dict(ai.marked)["q3"].startswith("The angle of incidence")

    got = w.c.get(_url(hw, w, what="photo-reading"), headers=w.ana).json()
    assert got["status"] == "done" and got["note"] is None
    by_q = {x["questionId"]: x for x in got["readings"]}
    assert set(by_q) == {"q2", "q3"}
    assert by_q["q3"]["awardedMarks"] == 2 and by_q["q3"]["reasoning"] == "both laws stated"
    assert "handwriting partly unclear" in by_q["q3"]["warnings"]
    assert any("no answer found" in x for x in by_q["q2"]["warnings"])
    assert any("could not be straightened" in x for x in by_q["q3"]["warnings"])

    row = next(x for x in w.c.get(f"/api/v1/homework/{hw['id']}/submissions", headers=w.ana).json()
               if x["studentId"] == w.ids["s1"])
    assert row["photoReading"]["status"] == "done" and len(row["photoReading"]["readings"]) == 2
    assert row["status"] == "submitted", "a suggestion never becomes a mark on its own"

    log = get_audit_log(cr._cfg.data_root)
    assert log.for_action("homework_photo_read_requested")
    [sent] = log.for_action("homework_photos_read")
    assert sent["details"]["processor"] == "sarvam" and sent["details"]["photos"] == 1


def test_only_the_homeworks_teacher_may_ask_and_only_for_a_handed_in_photo(w, ai):
    hw = _handed_in_with_photo(w)
    assert w.c.post(_url(hw, w), headers=w.bala).status_code == 403
    assert w.c.post(_url(hw, w), headers=w.p2).status_code == 403
    assert w.c.post(_url(hw, w), headers=w.s1).status_code == 403
    assert w.c.post(_url(hw, w, sid="s2"), headers=w.ana).status_code == 404   # not handed in
    w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}}, headers=w.s2)
    assert w.c.post(_url(hw, w, sid="s2"), headers=w.ana).status_code == 409   # no photos
    assert ai.sent == []


def test_nothing_is_sent_without_a_key(w, ai, monkeypatch):
    from academicos.assessment import vision
    from academicos.config import LLMNotEnabled
    from academicos.operations import homework_ai
    from academicos.operations.routes import store
    from academicos.curriculum import routes as cr

    def none():
        raise LLMNotEnabled()
    monkeypatch.setattr(vision, "api_key", none)
    hw = _handed_in_with_photo(w)
    assert w.c.post(_url(hw, w), headers=w.ana).status_code == 501
    assert homework_ai.homework_photo_reading(store(), cr._require(), None, None, datetime.now(timezone.utc)) == 0
    assert ai.sent == [] and store().photo_read(hw["id"], w.ids["s1"]) is None


def test_nothing_is_sent_once_the_parent_withdraws_consent(w, ai):
    from academicos.assessment.consent import get_consent_store
    from academicos.curriculum import routes as cr
    from academicos.operations import homework_ai
    from academicos.operations.routes import store

    hw = _handed_in_with_photo(w)
    get_consent_store(cr._cfg.data_root).revoke_consent("school_1", w.ids["s1"], revoked_by="parent")
    assert w.c.post(_url(hw, w), headers=w.ana).status_code == 409
    # the automation records why, and does not send
    assert homework_ai.homework_photo_reading(store(), cr._require(), None, None, datetime.now(timezone.utc)) == 0
    assert ai.sent == []
    got = w.c.get(_url(hw, w, what="photo-reading"), headers=w.ana).json()
    assert got["status"] == "failed" and "consent" in got["note"]


def test_the_automation_reads_waiting_photos_once_and_again_after_a_retake(w, ai):
    from academicos.curriculum import routes as cr
    from academicos.operations import homework_ai
    from academicos.operations.routes import store

    hw = _handed_in_with_photo(w)
    now = datetime.now(timezone.utc)
    assert homework_ai.homework_photo_reading(store(), cr._require(), None, None, now) == 1
    assert homework_ai.homework_photo_reading(store(), cr._require(), None, None, now) == 0
    assert len(ai.sent) == 1
    assert store().photo_read(hw["id"], w.ids["s1"])["requested_by"] == "automation"

    # a re-take: a photo newer than the last reading is read again
    with store()._conn_lock:
        store().conn.execute("UPDATE homework_photo_reads SET started_at='2000-01-01T00:00:00+00:00'")
        store()._commit()
    assert homework_ai.homework_photo_reading(store(), cr._require(), None, None, now) == 1
    assert len(ai.sent) == 2


def test_a_submission_is_claimed_once(w, ai):
    from academicos.operations.routes import store
    hw = _handed_in_with_photo(w)
    s = store()
    assert s.claim_photo_read(hw["id"], w.ids["s1"], by="a") is True
    assert s.claim_photo_read(hw["id"], w.ids["s1"], by="b") is False
    assert s.claim_photo_read(hw["id"], w.ids["s1"], by="b", again=True) is False, "being read now"
    assert w.c.post(_url(hw, w), headers=w.ana).status_code == 409
    s.finish_photo_read(hw["id"], w.ids["s1"], readings=[])
    assert s.claim_photo_read(hw["id"], w.ids["s1"], by="b") is False, "read; only a teacher asks again"
    assert s.claim_photo_read(hw["id"], w.ids["s1"], by="b", again=True) is True
    # a reader that died: its claim is taken over after STALE_CLAIM_MINUTES
    with s._conn_lock:
        s.conn.execute("UPDATE homework_photo_reads SET started_at='2000-01-01T00:00:00+00:00'")
        s._commit()
    assert s.claim_photo_read(hw["id"], w.ids["s1"], by="c") is True


def test_erasure_removes_the_readings(w, ai):
    from academicos.operations.routes import store
    hw = _handed_in_with_photo(w)
    assert w.c.post(_url(hw, w), headers=w.ana).status_code == 202
    assert store().photo_readings(hw["id"], w.ids["s1"])
    counts = store().forget_student(w.ids["s1"], school_id="school_1", email="s1@example.com", name="Asha")
    assert counts["homework_photo_reads"] == 1 and counts["homework_photo_readings"] == 2
    assert store().photo_read(hw["id"], w.ids["s1"]) is None
