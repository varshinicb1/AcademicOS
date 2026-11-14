"""FEE-1 fees: the principal (or a teacher with the fees grant) sets the
year's fees per class, records payments with the school's next receipt
number and grants concessions; a parent sees their child's statement and
hears of each receipt; nobody else reads it. Cover fixture: Asha is in 10-B;
the school's today is 2026-06-01."""
from __future__ import annotations

from test_cover_routes import w  # noqa: F401 - `w` is a fixture
from test_parent_notices import _h, _items, _parent


def _head(w, name, amount, due, grade=10, by=None):
    r = w.c.post("/api/v1/fees/heads", json={"academicYearId": w.year, "grade": grade, "name": name,
                                            "amountPaise": amount, "dueDate": due}, headers=by or w.p)
    assert r.status_code == 200, r.text
    return r.json()


def _pay(w, sid, head, amount, by=None, **kw):
    return w.c.post("/api/v1/fees/payments", json={"studentId": sid, "feeHeadId": head["id"], "amountPaise": amount,
                                                  "method": "upi", **kw}, headers=by or w.p)


def test_a_parent_sees_dues_receipts_and_what_is_overdue(w):
    sid, mum = _parent(w)
    tuition = _head(w, "Tuition, term 1", 15_000_00, "2026-05-15")
    lab = _head(w, "Science lab", 2_000_00, "2026-07-01")
    _head(w, "Class 9 trip", 1_000_00, "2026-07-01", grade=9)
    annual = _head(w, "Annual charges", 5_000_00, "2026-06-30", grade=None)

    r = _pay(w, sid, tuition, 10_000_00, reference="UPI 123")
    assert r.status_code == 200, r.text
    assert r.json()["receiptNo"] == 1 and r.json()["paidOn"] == "2026-06-01"
    assert _pay(w, sid, lab, 2_000_00).json()["receiptNo"] == 2
    [notice] = [n for n in _items(w, _h(mum), "fee_receipt") if "Science lab" in n["body"]]
    assert notice["title"] == "Fee received: Asha" and notice["body"] == "Rs 2,000 for Science lab, receipt 2."

    st = w.c.get(f"/api/v1/children/{sid}/fees", headers=_h(mum))
    assert st.status_code == 200, st.text
    s = st.json()
    rows = {r["head"]["name"]: r for r in s["rows"]}
    assert set(rows) == {"Tuition, term 1", "Science lab", "Annual charges"}, "not another class's fee"
    assert rows["Tuition, term 1"]["status"] == "overdue" and rows["Tuition, term 1"]["balancePaise"] == 5_000_00
    assert rows["Science lab"]["status"] == "paid"
    assert rows["Annual charges"]["status"] == "due"
    assert s["balancePaise"] == 10_000_00 and s["overduePaise"] == 5_000_00 and s["paidPaise"] == 12_000_00
    assert [r["receiptNo"] for r in s["receipts"]] == [1, 2]
    assert w.c.get("/api/v1/my-fees", headers=w.stu).json() == s
    [row] = w.c.get(f"/api/v1/fees/sections/{w.b10}", headers=w.p).json()
    assert row["name"] == "Asha" and row["overduePaise"] == 5_000_00
    assert w.c.get(f"/api/v1/fees/sections/{w.b10}", headers=w.p2).status_code == 403

    # a concession lowers what is owed
    r = w.c.put("/api/v1/fees/concessions", json={"studentId": sid, "feeHeadId": annual["id"], "amountPaise": 5_000_00,
                                                 "reason": "Staff child"}, headers=w.p)
    assert r.status_code == 200 and r.json()["balancePaise"] == 5_000_00
    assert {x["head"]["name"]: x["status"] for x in r.json()["rows"]}["Annual charges"] == "paid"


def test_only_the_school_and_the_childs_family_reach_the_fees(w):
    sid, mum = _parent(w)
    head = _head(w, "Tuition", 1_000_00, "2026-07-01")
    for who in (w.t["ana"], w.stu, _h(mum)):
        assert w.c.post("/api/v1/fees/heads", json={"academicYearId": w.year, "name": "x", "amountPaise": 1,
                                                    "dueDate": "2026-07-01"}, headers=who).status_code == 403
        assert _pay(w, sid, head, 100, by=who).status_code == 403
    assert w.c.get(f"/api/v1/fees/students/{sid}", headers=w.p2).status_code in (403, 404)
    assert _pay(w, sid, head, 100, by=w.p2).status_code in (403, 404), "another school"
    assert w.c.get(f"/api/v1/children/{sid}/fees", headers=w.stu).status_code == 403
    assert w.c.get("/api/v1/my-fees", headers=_h(mum)).status_code == 403

    # the fees grant lets a teacher do the school's side
    assert w.c.post("/api/v1/admin/grants", json={"userId": w.uid["bala"], "capability": "fees"},
                    headers=w.p).status_code == 200
    assert _pay(w, sid, head, 100, by=w.t["bala"]).status_code == 200


def test_bad_payments_are_refused_and_a_paid_fee_cannot_be_removed(w):
    sid, _ = _parent(w)
    nine = _head(w, "Class 9 trip", 1_000_00, "2026-07-01", grade=9)
    r = _pay(w, sid, nine, 100)
    assert r.status_code == 422 and "not charged to Asha's class" in r.json()["detail"]
    ten = _head(w, "Tuition", 1_000_00, "2026-07-01")
    assert _pay(w, sid, ten, 100, paidOn="2026-06-05").status_code == 422, "a future date"
    assert _pay(w, sid, ten, 0).status_code == 422
    assert _pay(w, sid, ten, 100, method="crypto").status_code == 422
    assert _pay(w, sid, ten, 100).status_code == 200
    r = w.c.delete(f"/api/v1/fees/heads/{ten['id']}", headers=w.p)
    assert r.status_code == 409
    assert w.c.delete(f"/api/v1/fees/heads/{nine['id']}", headers=w.p).status_code == 200
    r = w.c.put("/api/v1/fees/concessions", json={"studentId": sid, "feeHeadId": ten["id"], "amountPaise": 2_000_00,
                                                 "reason": "x"}, headers=w.p)
    assert r.status_code == 422


def test_erasing_a_student_removes_their_payments(w):
    from academicos.operations.routes import store
    sid, _ = _parent(w)
    head = _head(w, "Tuition", 1_000_00, "2026-07-01")
    _pay(w, sid, head, 500_00)
    counts = store().forget_student(sid, school_id="school_1", email="s1@example.com", name="Asha")
    assert counts["fee_payments"] == 1
    assert store().payments_of("school_1", sid) == []
