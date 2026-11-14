"""The class teacher's remark on each report card (EX-8), drafted from the
term's marks so a class is reviewed and saved rather than written from
nothing. Built on test_report_cards.rc: in 10-A, Asha has Science 76% and
Mathematics 90% (absent for one paper), 80% overall (B1); Bhavna has Science
60%, English 70% and Mathematics 75%, 67% overall (B2)."""
from __future__ import annotations

from test_guardians import _h, _parent
from test_homework import w  # noqa: F401 - `w` is a fixture
from test_report_cards import _card, rc  # noqa: F401 - `rc` is a fixture


def _url(rc):
    return f"/api/v1/report-cards/sections/{rc.a10}/remarks"


def _make_ana_class_teacher(rc):
    rc.store.update_section(rc.a10, class_teacher_id=rc.store.allocation_for(rc.a10, rc.sci10).teacher_id)


def test_each_student_gets_a_draft_from_their_marks_and_none_is_on_the_card_yet(rc):
    r = rc.c.get(_url(rc), headers=rc.p)
    assert r.status_code == 200, r.text
    d = r.json()
    assert (d["section"], d["termName"]) == ("10-A", "Term 1")
    rows = {x["studentName"]: x for x in d["rows"]}
    assert list(rows) == ["Asha", "Bhavna"], "name order"
    assert rows["Asha"]["remark"] is None
    assert rows["Asha"]["draft"] == ("Asha scored 80% overall this term (grade B1). Strongest in Mathematics (90%); "
                                     "Science (76%) is the one to focus on next. Absent for 1 paper this term.")
    assert rows["Bhavna"]["draft"].startswith("Bhavna scored 67% overall this term (grade B2). "
                                              "Strongest in Mathematics (75%); Science (60%)")
    assert "rank" not in r.text.lower() and "position" not in r.text.lower()
    assert _card(rc, rc.p).json()["remark"] is None, "a draft never reaches the card"


def test_a_saved_remark_is_on_the_card_and_its_pdf_and_is_audited(rc, tmp_path):
    import fitz
    from academicos.assessment.audit_log import get_audit_log
    from academicos.curriculum import routes as cr
    _make_ana_class_teacher(rc)
    s1, s2 = rc.ids["s1"], rc.ids["s2"]
    r = rc.c.put(_url(rc), headers=rc.ana, json={"remarks": [
        {"studentId": s1, "remark": "  Asha works  steadily; well done.  "},
        {"studentId": s2, "remark": ""}]})
    assert r.status_code == 200, r.text
    rows = {x["studentName"]: x for x in r.json()["rows"]}
    assert rows["Asha"]["remark"] == "Asha works steadily; well done." and rows["Asha"]["writtenBy"] == "Ana"
    assert rows["Bhavna"]["remark"] is None
    assert _card(rc, rc.p).json()["remark"] == "Asha works steadily; well done."
    mum = _h(_parent(rc))
    assert _card(rc, mum).json()["remark"] == "Asha works steadily; well done.", "the parent reads it too"
    pdf = rc.c.get(f"/api/v1/report-cards/students/{s1}/pdf", headers=rc.p)
    (tmp_path / "r.pdf").write_bytes(pdf.content)
    with fitz.open(str(tmp_path / "r.pdf")) as doc:
        text = doc[0].get_text()
    assert "Class teacher's remark" in text and "Asha works steadily; well done." in text
    [entry] = get_audit_log(cr._cfg.data_root).for_action("report_card_remarks_saved")
    assert entry["details"]["written"] == [s1] and entry["details"]["termId"] == rc.term

    # Changing it is audited as a change (the log reads newest first); an empty
    # remark removes it.
    rc.c.put(_url(rc), headers=rc.ana, json={"remarks": [{"studentId": s1, "remark": "Better in Science."}]})
    assert get_audit_log(cr._cfg.data_root).for_action("report_card_remarks_saved")[0]["details"]["changed"] == [s1]
    rc.c.put(_url(rc), headers=rc.ana, json={"remarks": [{"studentId": s1, "remark": ""}]})
    assert _card(rc, rc.p).json()["remark"] is None


def test_who_may_read_and_write_remarks(rc):
    s1 = rc.ids["s1"]
    body = {"remarks": [{"studentId": s1, "remark": "Good term."}]}
    assert rc.c.get(_url(rc), headers=rc.ana).status_code == 403, "a subject teacher, not the class teacher"
    assert rc.c.put(_url(rc), headers=rc.ana, json=body).status_code == 403
    assert rc.c.put(_url(rc), headers=rc.s1, json=body).status_code == 403, "the student"
    assert rc.c.put(_url(rc), headers=rc.p2, json=body).status_code in (403, 404), "another school's principal"
    _make_ana_class_teacher(rc)
    assert rc.c.put(_url(rc), headers=rc.ana, json=body).status_code == 200


def test_a_student_of_another_section_refuses_the_whole_batch(rc):
    body = {"remarks": [{"studentId": rc.ids["s1"], "remark": "Fine."},
                        {"studentId": rc.ids["s3"], "remark": "Charu is in 10-B."}]}
    r = rc.c.put(_url(rc), headers=rc.p, json=body)
    assert r.status_code == 422
    assert _card(rc, rc.p).json()["remark"] is None, "nothing of the batch landed"
    assert rc.c.put(_url(rc), headers=rc.p, json={"remarks": [{"studentId": rc.ids["s1"], "remark": "x" * 601}]}
                    ).status_code == 422, "a remark is at most 600 characters"


def test_no_remark_is_written_for_a_student_without_parental_consent(rc):
    from academicos.assessment.consent import get_consent_store
    from academicos.curriculum import routes as cr
    get_consent_store(cr._cfg.data_root).revoke_consent("school_1", rc.ids["s2"], revoked_by="parent")
    r = rc.c.put(_url(rc), headers=rc.p, json={"remarks": [{"studentId": rc.ids["s1"], "remark": "Fine."},
                                                           {"studentId": rc.ids["s2"], "remark": "Fine."}]})
    assert r.status_code == 409, r.text


def test_erasing_a_student_erases_their_remark(rc):
    from academicos.operations.routes import store
    rc.c.put(_url(rc), headers=rc.p, json={"remarks": [{"studentId": rc.ids["s1"], "remark": "Fine."}]})
    out = store().forget_student(rc.ids["s1"], school_id="school_1", email="s1@example.com", name="Asha")
    assert out["report_card_remarks"] == 1
    assert store().remark_for(rc.term, rc.ids["s1"]) is None
