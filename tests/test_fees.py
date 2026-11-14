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


def test_a_payment_recorded_in_error_is_reversed_and_its_receipt_stays_marked(w):
    sid, mum = _parent(w)
    tuition = _head(w, "Tuition", 10_000_00, "2026-07-01")
    p = _pay(w, sid, tuition, 10_000_00).json()
    assert _pay(w, sid, tuition, 1_000_00).json()["receiptNo"] == 2

    for who in (w.t["ana"], _h(mum), w.stu, w.p2):
        r = w.c.post(f"/api/v1/fees/payments/{p['id']}/reverse", json={"reason": "x"}, headers=who)
        assert r.status_code in (403, 404), r.text
    r = w.c.post(f"/api/v1/fees/payments/{p['id']}/reverse", json={"reason": "Cheque bounced"}, headers=w.p)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["paidPaise"] == 1_000_00 and s["balancePaise"] == 9_000_00, "the reversed money no longer counts"
    first = s["receipts"][0]
    assert first["receiptNo"] == 1 and first["reversed"] is True and first["reversalReason"] == "Cheque bounced"
    assert s["receipts"][1]["reversed"] is False
    [notice] = _items(w, _h(mum), "fee_payment_reversed")
    assert notice["title"] == "Receipt cancelled: Asha"
    assert notice["body"] == "Receipt 1 for Rs 10,000 (Tuition) was cancelled: Cheque bounced"
    again = w.c.post(f"/api/v1/fees/payments/{p['id']}/reverse", json={"reason": "again"}, headers=w.p)
    assert again.status_code == 409
    assert w.c.post(f"/api/v1/fees/payments/{p['id']}/reverse", json={"reason": ""}, headers=w.p).status_code == 422
    # the next payment still takes the next number: a reversal frees none
    assert _pay(w, sid, tuition, 500_00).json()["receiptNo"] == 3


def test_the_receipt_prints_for_the_school_the_parent_and_the_student_only(w):
    sid, mum = _parent(w)
    tuition = _head(w, "Tuition", 10_000_00, "2026-07-01")
    p = _pay(w, sid, tuition, 4_500_50, reference="CHQ 7").json()
    for path, who in ((f"/api/v1/fees/payments/{p['id']}/receipt", w.p),
                      (f"/api/v1/children/{sid}/fees/receipts/{p['id']}", _h(mum)),
                      (f"/api/v1/my-fees/receipts/{p['id']}", w.stu)):
        r = w.c.get(path, headers=who)
        assert r.status_code == 200, (path, r.text)
        assert r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
        assert 'filename="receipt-1.pdf"' in r.headers["content-disposition"]
    assert w.c.get(f"/api/v1/fees/payments/{p['id']}/receipt", headers=w.t["ana"]).status_code == 403
    assert w.c.get(f"/api/v1/fees/payments/{p['id']}/receipt", headers=w.p2).status_code in (403, 404)
    assert w.c.get(f"/api/v1/children/{sid}/fees/receipts/{p['id']}", headers=w.stu).status_code == 403
    assert w.c.get(f"/api/v1/my-fees/receipts/{p['id']}", headers=_h(mum)).status_code == 403
    assert w.c.get("/api/v1/my-fees/receipts/nope", headers=w.stu).status_code == 404


def test_the_receipt_says_what_it_records_and_when_it_was_cancelled():
    import fitz
    from academicos.operations.fee_receipt_pdf import receipt_pdf

    def text_of(data: bytes) -> str:
        with fitz.open(stream=data, filetype="pdf") as doc:
            return " ".join(doc[0].get_text().split())

    row = {"receipt_no": 12, "paid_on": "2026-06-01", "method": "cheque", "reference": "CHQ 7",
           "recorded_at": "2026-06-01T05:00:00+00:00", "reversed_at": None, "reversal_reason": None}
    text = text_of(receipt_pdf(receipt=row, student_name="Asha", class_name="10-B", fee_name="Tuition",
                                            recorded_by="Priya", amount="Rs 4,500.50"))
    for words in ("Fee receipt", "12", "01 Jun 2026", "Asha, class 10-B", "Tuition", "Cheque (CHQ 7)", "Rs 4,500.50",
                  "Recorded by Priya"):
        assert words in text, words
    assert "CANCELLED" not in text
    row.update(reversed_at="2026-06-02T05:00:00+00:00", reversal_reason="Cheque bounced")
    text = text_of(receipt_pdf(receipt=row, student_name="Asha", class_name="10-B", fee_name="Tuition",
                                            recorded_by="Priya", amount="Rs 4,500.50"))
    assert "CANCELLED on 02 Jun 2026: Cheque bounced" in text
