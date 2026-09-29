"""The principal's dashboard (ADM-2), the private calendar feed (INT-2),
/v1 homework sets (API-2) and photos of written homework (SA-2)."""
from __future__ import annotations

from test_homework import BANK, _create, w  # noqa: F401 - `w` is a fixture

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")


def test_the_dashboard_counts_today_and_the_week(w):
    _create(w, "ana", questionIds=["q1", "q2"])
    d = w.c.get("/api/v1/dashboard/summary", headers=w.p)
    assert d.status_code == 200, d.text
    body = d.json()
    assert body["cover"]["staff"] == 3 and body["cover"]["unmarked"] == 3
    assert body["homework"]["set"] == 1 and body["homework"]["submissionsExpected"] == 2
    assert w.c.get("/api/v1/dashboard/summary", headers=w.ana).status_code == 403
    w.c.post("/api/v1/admin/grants", json={"userId": w.c.get("/api/v1/auth/me", headers=w.ana).json()["id"],
                                          "capability": "reports"}, headers=w.p)
    assert w.c.get("/api/v1/dashboard/summary", headers=w.ana).status_code == 200


def test_the_calendar_feed_is_private_and_resettable(w):
    hw = _create(w, "ana", questionIds=["q1"]).json()
    url = w.c.get("/api/v1/calendar-feed", headers=w.s1).json()["url"]
    path = "/api/v1/ics/" + url.rsplit("/ics/", 1)[1]
    r = w.c.get(path)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/calendar")
    text = r.text
    assert text.startswith("BEGIN:VCALENDAR") and "Homework due: Light practice" in text and f"hw-{hw['id']}" in text
    assert all(len(line.encode()) <= 75 for line in text.split("\r\n")), "folded per RFC 5545"
    again = w.c.get("/api/v1/calendar-feed", headers=w.s1).json()["url"]
    assert again == url, "one feed per person"
    new = w.c.post("/api/v1/calendar-feed/reset", headers=w.s1).json()["url"]
    assert new != url and w.c.get(path).status_code == 404
    assert w.c.get("/api/v1/ics/not-a-token.ics").status_code == 404


def test_v1_homework_sets(w, monkeypatch):
    from academicos.assessment import qbank_routes
    from academicos.assessment.qbank_engine import QuestionBank
    keyed = [dict(q, answerScheme={**q["answerScheme"], "provenance": "cbse_marking_scheme"}) for q in BANK]
    monkeypatch.setattr(qbank_routes, "_bank", QuestionBank(keyed))
    key = w.c.post("/api/v1/api-keys", json={"label": "LMS", "scopes": ["questions:read"]}, headers=w.p).json()["key"]
    h = {"X-API-Key": key}
    r = w.c.post("/v1/homework-sets", json={"subject": "Science", "grade": 10, "count": 3}, headers=h)
    assert r.status_code == 200, r.text
    first = r.json()
    assert first["count"] == 3 and "answerScheme" not in first["items"][0]
    same = w.c.post("/v1/homework-sets", json={"subject": "Science", "grade": 10, "count": 3}, headers=h).json()
    assert [i["id"] for i in same["items"]] == [i["id"] for i in first["items"]], "stable for the same request"
    mix = w.c.post("/v1/homework-sets", json={"subject": "Science", "grade": 10, "types": {"mcq": 5},
                                              "excludeIds": ["q1"]}, headers=h).json()
    assert {i["id"] for i in mix["items"]} == {"q2", "q4"} and mix["shortfall"] == {"mcq": 3}
    assert w.c.post("/v1/homework-sets", json={"subject": "Science", "grade": 10}).status_code == 401


def test_written_work_as_photos_waits_for_the_teacher(w):
    hw = _create(w, "ana", questionIds=["q1"]).json()
    up = w.c.post(f"/api/v1/my-homework/{hw['id']}/photos", files={"file": ("page1.png", PNG, "image/png")},
                  headers=w.s1)
    assert up.status_code == 200, up.text
    pid = up.json()["id"]
    assert w.c.post(f"/api/v1/my-homework/{hw['id']}/photos", files={"file": ("x.gif", b"GIF89a", "image/gif")},
                    headers=w.s1).status_code == 415
    assert w.c.get(f"/api/v1/my-homework/{hw['id']}/photos/{pid}", headers=w.s1).content == PNG
    assert w.c.get(f"/api/v1/my-homework/{hw['id']}/photos/{pid}", headers=w.s2).status_code == 404
    # an MCQ answered right would be final at once; with a photo, the teacher marks it
    out = w.c.post(f"/api/v1/my-homework/{hw['id']}/submit", json={"answers": {"q1": "A"}}, headers=w.s1).json()
    assert out["myStatus"] == "submitted"
    rows = {r["studentId"]: r for r in w.c.get(f"/api/v1/homework/{hw['id']}/submissions", headers=w.ana).json()}
    assert rows[w.ids["s1"]]["photoIds"] == [pid]
    got = w.c.get(f"/api/v1/homework/{hw['id']}/submissions/{w.ids['s1']}/photos/{pid}", headers=w.ana)
    assert got.status_code == 200 and got.content == PNG
    assert w.c.get(f"/api/v1/homework/{hw['id']}/submissions/{w.ids['s1']}/photos/{pid}",
                   headers=w.bala).status_code == 403
