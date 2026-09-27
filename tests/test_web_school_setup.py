"""A new school set up the way the web now does it reaches the per-term views.

Audit D27 (2026-09-27): the web could not seed a class or declare a term. A
school set up the documented way had no term, so `/paper-timing` read scope
"allTime", a term's baseline could not be set, and the "not yet" list was
empty. The admin console now seeds classes 6-10 one at a time under one year
(`SchoolSetupCard`) and offers the usual two terms (`TermsCard.twoTerms`).
This replays exactly those requests against the real app.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from test_assessment_routes_auth import _boot_client, _register  # noqa: E402

BASE = "/api/v1/curriculum"
PRINCIPAL_KEY = "test-bootstrap-key"


def _session(today: date) -> tuple[str, str, str]:
    """SchoolSetupCard.sessionFor: the 1 April - 31 March year holding today."""
    first = today.year if today.month >= 4 else today.year - 1
    return f"{first}-{(first + 1) % 100:02d}", f"{first}-04-01", f"{first + 1}-03-31"


def test_the_web_setup_reaches_a_term(tmp_path, monkeypatch):
    from academicos.curriculum.routes import _school_today
    label, start, end = _session(_school_today())
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "head@school1.test", "Head",
                              principal_key=PRINCIPAL_KEY)
        auth = {"Authorization": f"Bearer {principal['token']}"}

        # Before: the console's "No curriculum yet", and no term.
        assert client.get(f"{BASE}/terms/current", headers=auth).status_code == 404

        for grade in range(6, 11):
            r = client.post(f"{BASE}/seed/cbse", headers=auth, json={
                "grade": grade, "academicYearLabel": label, "startDate": start, "endDate": end})
            assert r.status_code == 200, r.text

        years = client.get(f"{BASE}/academic-years", params={"school_id": "school_1"},
                           headers=auth).json()
        assert [y["label"] for y in years] == [label], "one year, not one per class"
        year = years[0]["id"]
        grades = client.get(f"{BASE}/academic-years/{year}/grades", headers=auth).json()
        assert sorted(g["number"] for g in grades) == [6, 7, 8, 9, 10]

        # TermsCard.twoTerms for an April-March year.
        first = int(start[:4])
        for name, s, e in (("Term 1", start, f"{first}-09-30"), ("Term 2", f"{first}-10-01", end)):
            r = client.post(f"{BASE}/academic-years/{year}/terms", headers=auth,
                            json={"name": name, "startDate": s, "endDate": e})
            assert r.status_code == 200, r.text
        assert [t["name"] for t in client.get(f"{BASE}/academic-years/{year}/terms",
                                              headers=auth).json()] == ["Term 1", "Term 2"]

        # After: today is in a term, and the report is per term.
        assert client.get(f"{BASE}/terms/current", headers=auth).status_code == 200
        timing = client.get("/api/v1/paper-timing", headers=auth).json()
        assert timing["scope"] == "term", timing


def test_a_term_the_card_sends_wrong_is_refused_with_the_reason(tmp_path, monkeypatch):
    """The card shows the server's sentence as it comes; it must be one."""
    from academicos.curriculum.routes import _school_today
    label, start, end = _session(_school_today())
    with _boot_client(tmp_path, monkeypatch) as client:
        principal = _register(client, "school_1", "head@school1.test", "Head",
                              principal_key=PRINCIPAL_KEY)
        auth = {"Authorization": f"Bearer {principal['token']}"}
        client.post(f"{BASE}/seed/cbse", headers=auth, json={
            "grade": 6, "academicYearLabel": label, "startDate": start, "endDate": end})
        year = client.get(f"{BASE}/academic-years", params={"school_id": "school_1"},
                          headers=auth).json()[0]["id"]
        first = int(start[:4])
        ok = client.post(f"{BASE}/academic-years/{year}/terms", headers=auth,
                         json={"name": "Term 1", "startDate": start, "endDate": f"{first}-09-30"})
        assert ok.status_code == 200, ok.text
        r = client.post(f"{BASE}/academic-years/{year}/terms", headers=auth,
                        json={"name": "Term 2", "startDate": f"{first}-09-30", "endDate": end})
        assert r.status_code == 422
        assert "overlaps 'Term 1'" in r.json()["detail"]
