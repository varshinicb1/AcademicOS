"""AGENTS.md §3.1, NFR-2: a principal of one school gets nothing that belongs to another, on any route.

The per-feature tests each hold one route to its school (test_curriculum_read_scoping,
test_cover_routes, test_homework, ...). Nothing walked them all, so a new GET route that forgot its
school check would ship unnoticed until a second school went live. This sweep does:

school_1 is set up the way a real school is on day one (school-setup, a teacher, a student), and the
principal of school_2 -- a full principal, every admin capability -- calls every
signed-in GET route with school_1's real ids in the path (and `school_id=school_1` in the query). Each
answer must be a refusal or a 404, or else hold none of school_1's ids or names.

A route whose path needs an id this world does not make is listed in UNFILLED_PARAMS, so the sweep's
reach is visible rather than assumed. Writes (POST/PUT/DELETE) are not swept here.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import pytest

from academicos.api.route_policy import API_KEY, OWNER, PUBLIC, ROUTE_POLICY
from test_assessment_routes_auth import _boot_client, _register
from _auth_helpers import register_invited

KEY = "test-bootstrap-key"
TODAY = date(2026, 10, 1)
MARK = "Zephyrine"          # in every school_1 name we make, so a leak of any name is found


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    from academicos.curriculum import routes as curriculum_routes

    mp = pytest.MonkeyPatch()
    mp.setattr(curriculum_routes, "_school_today", lambda: TODAY)
    try:
        with _boot_client(tmp_path_factory.mktemp("sweep"), mp) as client:
            p1 = _register(client, "school_1", "head@one.test", f"{MARK} Head", principal_key=KEY)
            p2 = _register(client, "school_2", "head@two.test", "Other Head", principal_key=KEY)
            a1 = {"Authorization": f"Bearer {p1['token']}"}
            setup = client.post("/api/v1/curriculum/school-setup", json={}, headers=a1)
            assert setup.status_code == 200, setup.text
            teacher = register_invited(client, "school_1", "t@one.test", name=f"{MARK} Teacher")
            student = register_invited(client, "school_1", "s@one.test", name=f"{MARK} Student", role="student")
            ids = _school_ids(client, a1, setup.json())
            ids.update(teacher_id=teacher["user"]["id"], student_id=student["user"]["id"],
                       user_id=teacher["user"]["id"], school_id="school_1")
            yield client, {"Authorization": f"Bearer {p2['token']}"}, ids, a1
    finally:
        mp.undo()


def _school_ids(client, auth, setup: dict) -> dict[str, str]:
    base = "/api/v1/curriculum"
    year = setup["academicYear"]["id"]
    sections = client.get(f"{base}/academic-years/{year}/sections", headers=auth).json()
    out = {"academic_year_id": year, "year_id": year, "section_id": sections[0]["id"]}
    grades = client.get(f"{base}/academic-years/{year}/grades", headers=auth)
    if grades.status_code == 200 and grades.json():
        out["grade_id"] = grades.json()[0]["id"]
    terms = client.get(f"{base}/academic-years/{year}/terms", headers=auth)
    if terms.status_code == 200 and terms.json():
        out["term_id"] = terms.json()[0]["id"]
    subjects = client.get(f"{base}/grades/{sections[0]['gradeId']}/subjects", headers=auth).json()
    out["subject_id"] = subjects[0]["id"]
    return out


# The path ids this world makes for school_1. A route whose path needs another id (a paper, a
# homework: this boot has no question bank to make one) is outside the sweep, and listed below.
FILLED = {"academic_year_id", "year_id", "section_id", "grade_id", "term_id", "subject_id",
          "teacher_id", "student_id", "user_id", "school_id"}
UNFILLED_PARAMS = {
    "assessment_id", "book_id", "chapter_id", "exam_id", "grade", "homework_id", "key_id", "kind",
    "leave_id", "lesson_id", "lost_id", "page_no", "paper_id", "photo_id", "practice_id", "question_id",
    "run_id", "session_id", "slug", "sub_id", "subject", "subtopic_id", "template_id",
    "webhook_id",
}
SIGNED_IN_GETS = sorted(p for (m, p), pol in ROUTE_POLICY.items()
                        if m == "GET" and pol.level not in (PUBLIC, API_KEY, OWNER))
GETS = [p for p in SIGNED_IN_GETS if set(re.findall(r"\{(\w+)\}", p)) <= FILLED]


def _fill(path: str, ids: dict[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: ids[m.group(1)], path)


def _school_1_marks(ids: dict[str, str]) -> set[str]:
    return {v for k, v in ids.items() if k != "school_id"} | {MARK}


def _get(client, path, ids, headers):
    return client.get(_fill(path, ids), params={"school_id": "school_1", "schoolId": "school_1"},
                      headers=headers)


@pytest.mark.parametrize("path", GETS)
def test_another_schools_principal_gets_nothing_of_school_1(world, path):
    client, other, ids, _ = world
    r = _get(client, path, ids, other)
    if r.status_code >= 400:
        # 503: a service this boot has not loaded (the question bank) holds nothing to leak.
        assert r.status_code in (400, 403, 404, 409, 422, 503), f"{path} -> {r.status_code} {r.text[:200]}"
        return
    leaked = sorted(v for v in _school_1_marks(ids) if v in r.text)
    assert not leaked, f"{path} -> {r.status_code} showed school_1's {leaked}: {r.text[:300]}"


def test_the_sweep_would_see_a_leak(world):
    """The control: school_1's own principal, on the same calls, is shown school_1's ids and names
    on many of them, so the check above is not passing because nothing is ever shown."""
    client, _, ids, own = world
    shown = [p for p in GETS
             if (r := _get(client, p, ids, own)).status_code == 200
             and any(v in r.text for v in _school_1_marks(ids))]
    assert len(shown) >= 20, shown


def test_the_sweeps_reach_is_what_this_file_says():
    """A route with a new kind of path id must be added to FILLED (with a school_1 id to put
    there) or to UNFILLED_PARAMS, so what the sweep does not reach stays written down."""
    params = {n for p in SIGNED_IN_GETS for n in re.findall(r"\{(\w+)\}", p)}
    assert params - FILLED == UNFILLED_PARAMS, (params - FILLED) ^ UNFILLED_PARAMS
    assert len(GETS) >= 90, len(GETS)
