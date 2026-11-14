"""SA-6, INT-2, NTF-2: a parent hears, the evening before, that their child's homework is due and
not handed in, and that their child has an exam tomorrow -- and those are the notices that may go by
SMS or WhatsApp.

The two scheduled reminders went to the student alone. A student is never sent an SMS or WhatsApp
(messaging.MESSAGE_ROLES: a minor's messages go to their parent), so "homework due" and "exam
tomorrow" sat in MESSAGE_KINDS with nobody who could ever receive them: the parent who gave their
number and said yes to SMS heard nothing. Now each linked parent gets their own notice, naming the
child, under their own settings, once.

Uses the cover fixture (Asha in 10-B; 2026-06-01 is a Monday) and test_parent_notices' parent.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from test_automations import _homework, _run
from test_cover_routes import MON, w  # noqa: F401 - `w` is a fixture
from test_homework import _q
from test_exams import _exam, _sheet
from test_parent_notices import _h, _items, _parent

IST = timezone(timedelta(hours=5, minutes=30))


def _at(day, hh, mm=0):
    y, m, d = map(int, day.split("-"))
    return datetime(y, m, d, hh, mm, tzinfo=IST).astimezone(timezone.utc)


def _wants_sms(parent_id):
    from academicos.operations.routes import store
    store().set_contact(parent_id, phone="+919876543210", sms_ok=True, whatsapp_ok=False)


def _sms_rows(parent_id):
    from academicos.operations.routes import store
    return store()._fetchall("SELECT d.channel, n.kind FROM message_deliveries d JOIN notifications n "
                             "ON n.id = d.notification_id WHERE d.user_id=?", (parent_id,))


def test_a_parent_hears_their_childs_homework_is_due_and_may_get_it_by_sms(w):
    _sid, parent = _parent(w)
    _wants_sms(parent["user"]["id"])
    _homework(w, MON)

    out = _run(_at("2026-05-31", 18))
    assert out["homework_due_tomorrow"] == 2, out          # Asha, and her mother

    [notice] = _items(w, _h(parent), "child_homework_due")
    assert notice["title"] == "Asha: homework due 2026-06-01", notice
    assert "Light worksheet" in notice["body"] and "Science" in notice["body"]
    assert notice["link"] == "/my-children"
    assert _sms_rows(parent["user"]["id"]) == [{"channel": "sms", "kind": "child_homework_due"}]
    # The student's own notice is unchanged, and still never an SMS.
    assert len(_items(w, w.stu, "homework_due")) == 1

    _run(_at("2026-05-31", 19))
    assert len(_items(w, _h(parent), "child_homework_due")) == 1, "once"


def test_a_parent_is_not_told_of_homework_already_handed_in(w):
    sid, parent = _parent(w)
    from academicos.operations.routes import store
    hw = store().create_homework(school_id="school_1", academic_year_id=w.year, teacher_id=w.uid["ana"],
                                 subject_id=w.sci10, subject_name="Science", grade=10, section_ids=[w.b10],
                                 title="Leaves", instructions="", chapter_ids=[],
                                 questions=[_q("q1", "short_answer", "Why are leaves green?", 1,
                                               points=[("chlorophyll", "chlorophyll")])],
                                 due_date=MON, created_by=w.uid["ana"], publish=True)
    store().submit_homework(hw, student_id=sid, section_id=w.b10, answers={"q1": "chlorophyll"}, late=False)
    _run(_at("2026-05-31", 18))
    assert _items(w, _h(parent), "child_homework_due") == []


def test_a_parent_hears_their_child_has_an_exam_tomorrow(w):
    _sid, parent = _parent(w)
    _wants_sms(parent["user"]["id"])
    eid = _exam(w)
    _sheet(w, eid, [(10, "Science", "2026-06-02")])
    w.c.post(f"/api/v1/exams/{eid}/publish", headers=w.p)
    from academicos.operations.routes import store
    with store()._conn_lock:          # publishing ran the jobs for the fixture's own day; start over
        store().conn.execute("DELETE FROM automation_runs")
        store()._commit()

    assert _run(_at("2026-06-01", 17, 30))["exam_reminders"] > 0
    [notice] = _items(w, _h(parent), "child_exam_tomorrow")
    assert notice["title"] == "Asha: exam tomorrow, Science", notice
    assert "Unit test 1" in notice["body"]
    assert {"channel": "sms", "kind": "child_exam_tomorrow"} in _sms_rows(parent["user"]["id"])


def test_a_parent_whose_link_ended_hears_nothing(w):
    sid, parent = _parent(w)
    r = w.c.delete(f"/api/v1/guardianships/{parent['user']['id']}/{sid}", headers=w.p)
    assert r.status_code == 200, r.text
    _homework(w, MON)
    _run(_at("2026-05-31", 18))
    assert _items(w, _h(parent), "child_homework_due") == []


def test_both_parent_kinds_may_go_by_message():
    from academicos.operations.messaging import MESSAGE_KINDS
    assert {"child_homework_due", "child_exam_tomorrow"} <= MESSAGE_KINDS
