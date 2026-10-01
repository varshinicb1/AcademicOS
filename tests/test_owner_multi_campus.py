"""ROLE-4 multi-campus: one owner over several schools, each school's data
kept separate.

What is held here, against a booted app with three schools (A and B linked
to the owner, C not):

1. the owner sees exactly its linked schools;
2. with no school chosen it reaches only its own routes and /auth/me;
3. choosing a school makes the session that school's principal, and
   switching changes the scope;
4. an unlinked school's data is unreachable, by switching or by id;
5. a principal's revoke removes the owner's access on its next request;
6. no route returns records of two schools in one response -- every
   parameterless GET is swept while acting in A for B's markers and the
   other way round -- except the owner overview, which carries per-school
   aggregates and nothing that names a record;
7. owner links are issued and withdrawn only by the school's own principal,
   are single use, and every step is in the audit log.
"""
from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

from academicos.api.main import app
from academicos.api.route_policy import API_KEY, OWNER, PUBLIC, ROUTE_POLICY
from academicos.assessment import auth_routes

from _auth_helpers import PASSWORD, register_invited

BOOTSTRAP_KEY = "owner-multi-campus-bootstrap-key"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _blueprint() -> dict:
    return {
        "totalMarks": 80, "durationMinutes": 180,
        "difficulty": {"easy": 0.3, "medium": 0.4, "hard": 0.3},
        "bloom": {"remember": 0.2, "understand": 0.2, "apply": 0.2, "analyze": 0.2,
                  "evaluate": 0.1, "create": 0.1},
        "chapterWeights": {"weights": {}}, "competencyWeights": {"weights": {}},
    }


class World:
    def __init__(self, client: TestClient, tag: str):
        self.c = client
        self.tag = tag
        self.schools: dict[str, dict] = {}
        self.owner_token = ""

    def school(self, key: str) -> dict:
        return self.schools[key]


def _set_up_school(c: TestClient, tag: str, key: str) -> dict:
    """A school with a principal, a named teacher, a named assessment, an API
    key and a profile name: each a marker that must never be seen from
    another school."""
    school_id = f"school_{key}_{tag}"
    p = c.post("/api/v1/auth/register", json={
        "schoolId": school_id, "name": f"Principal {key}", "email": f"p{key}-{tag}@example.com",
        "password": PASSWORD, "principalKey": BOOTSTRAP_KEY})
    assert p.status_code == 200, p.text
    ph = _auth(p.json()["token"])
    teacher_name = f"Teacher{key}-{tag}"
    teacher = register_invited(c, school_id, f"t{key}-{tag}@example.com", name=teacher_name)
    assert c.put("/api/v1/curriculum/school-profile", json={"name": f"Campus {key} {tag}"},
                 headers=ph).status_code == 200
    title = f"Assessment{key}-{tag}"
    a = c.post("/api/v1/assessments", json={
        "teacherId": teacher["user"]["id"], "schoolId": school_id, "title": title,
        "subject": "Mathematics", "grade": 10, "chapterIds": ["ch1"], "blueprint": _blueprint(),
    }, headers=_auth(teacher["token"]))
    assert a.status_code == 200, a.text
    key_label = f"Key{key}-{tag}"
    k = c.post("/api/v1/api-keys", json={"label": key_label, "scopes": ["questions:read"]}, headers=ph)
    assert k.status_code == 200, k.text
    return {
        "id": school_id, "principal": ph, "teacher": teacher, "assessment_id": a.json()["id"],
        "markers": [teacher_name, title, a.json()["id"], key_label, f"Campus {key} {tag}",
                    teacher["user"]["id"], f"t{key}-{tag}@example.com"],
    }


@pytest.fixture(scope="module")
def w(tmp_path_factory):
    from academicos.assessment import audit_log, consent as consent_mod
    from academicos.assessment import consent_routes as consent_routes_mod
    from academicos.assessment import users as users_mod
    from academicos.curriculum import store as curriculum_store_mod

    mp = pytest.MonkeyPatch()
    mp.setenv("ACOS_DATA_ROOT", str(tmp_path_factory.mktemp("owner_multi_campus")))
    mp.setenv("ACOS_PRINCIPAL_BOOTSTRAP_KEY", BOOTSTRAP_KEY)
    mp.setattr(audit_log, "_INSTANCE", None)
    mp.setattr(users_mod, "_INSTANCE", None)
    mp.setattr(curriculum_store_mod, "_INSTANCE", None)
    mp.setattr(consent_mod, "_INSTANCE", None)
    mp.setattr(consent_routes_mod, "_store", None)
    mp.setattr(consent_routes_mod, "_audit", None)
    try:
        with TestClient(app) as client:
            world = World(client, uuid.uuid4().hex[:8])
            for key in ("A", "B", "C"):
                world.schools[key] = _set_up_school(client, world.tag, key)
            code_a = client.post("/api/v1/owner-links", json={"label": "Trust chair"},
                                 headers=world.school("A")["principal"])
            assert code_a.status_code == 200, code_a.text
            reg = client.post("/api/v1/owner/register", json={
                "name": "Owner", "email": f"owner-{world.tag}@example.com", "password": PASSWORD,
                "code": code_a.json()["code"]})
            assert reg.status_code == 200, reg.text
            world.owner_token = reg.json()["token"]
            world.owner_id = reg.json()["user"]["id"]
            code_b = client.post("/api/v1/owner-links", json={}, headers=world.school("B")["principal"])
            assert code_b.status_code == 200, code_b.text
            redeemed = client.post("/api/v1/owner/links/redeem", json={"code": code_b.json()["code"]},
                                   headers=world.oh)
            assert redeemed.status_code == 200, redeemed.text
            world.link_b = code_b.json()["id"]
            yield world
    finally:
        mp.undo()


World.oh = property(lambda self: _auth(self.owner_token))


def _choose(w: World, key: str) -> None:
    r = w.c.post("/api/v1/owner/active-school", json={"schoolId": w.school(key)["id"]}, headers=w.oh)
    assert r.status_code == 200, r.text


def _leave(w: World) -> None:
    assert w.c.delete("/api/v1/owner/active-school", headers=w.oh).status_code == 200


# ---------------------------------------------------------------- 1, 2

def test_owner_sees_exactly_its_linked_schools(w):
    _leave(w)
    r = w.c.get("/api/v1/owner/schools", headers=w.oh)
    assert r.status_code == 200, r.text
    got = {s["schoolId"]: s for s in r.json()}
    assert set(got) == {w.school("A")["id"], w.school("B")["id"]}
    assert got[w.school("A")["id"]]["name"] == f"Campus A {w.tag}"
    assert not any(s["active"] for s in r.json())


def test_with_no_school_chosen_the_owner_reaches_only_its_own_routes(w):
    _leave(w)
    me = w.c.get("/api/v1/auth/me", headers=w.oh).json()
    assert (me["role"], me["schoolId"], me["isOwner"]) == ("owner", "", True)
    r = w.c.get("/api/v1/assessments", headers=w.oh)
    assert r.status_code == 403 and r.json()["detail"] == auth_routes.OWNER_CHOOSE_DETAIL
    assert w.c.get("/api/v1/auth/users", headers=w.oh).status_code == 403


# ---------------------------------------------------------------- 3

def _assessment_ids(w: World) -> set[str]:
    r = w.c.get("/api/v1/assessments", headers=w.oh)
    assert r.status_code == 200, r.text
    return {a["id"] for a in r.json()}


def test_choosing_a_school_scopes_the_session_and_switching_changes_it(w):
    a, b = w.school("A"), w.school("B")
    _choose(w, "A")
    me = w.c.get("/api/v1/auth/me", headers=w.oh).json()
    assert (me["role"], me["schoolId"], me["isOwner"]) == ("principal", a["id"], True)
    assert _assessment_ids(w) == {a["assessment_id"]}
    schools = {s["schoolId"]: s["active"] for s in w.c.get("/api/v1/owner/schools", headers=w.oh).json()}
    assert schools == {a["id"]: True, b["id"]: False}

    _choose(w, "B")
    assert w.c.get("/api/v1/auth/me", headers=w.oh).json()["schoolId"] == b["id"]
    assert _assessment_ids(w) == {b["assessment_id"]}
    # principal-level rights in the chosen school: the roster is a principal read
    roster = w.c.get("/api/v1/auth/users", params={"role": "teacher"}, headers=w.oh)
    assert roster.status_code == 200
    assert [u["id"] for u in roster.json()] == [b["teacher"]["user"]["id"]]


def test_a_school_principal_is_not_an_owner_and_a_principal_session_cannot_switch(w):
    r = w.c.post("/api/v1/owner/active-school", json={"schoolId": w.school("B")["id"]},
                 headers=w.school("A")["principal"])
    assert r.status_code == 403 and r.json()["detail"] == auth_routes.OWNER_DETAIL
    me = w.c.get("/api/v1/auth/me", headers=w.school("A")["principal"]).json()
    assert me["isOwner"] is False


# ---------------------------------------------------------------- 4

def test_an_unlinked_schools_data_is_unreachable(w):
    c_school = w.school("C")
    r = w.c.post("/api/v1/owner/active-school", json={"schoolId": c_school["id"]}, headers=w.oh)
    assert r.status_code == 403
    _choose(w, "A")
    # by id: C's assessment, and every {school_id} route named for C
    assert w.c.get(f"/api/v1/assessments/{c_school['assessment_id']}", headers=w.oh).status_code == 403
    assert w.c.get(f"/api/v1/assessments/{w.school('B')['assessment_id']}", headers=w.oh).status_code == 403
    for (method, path), policy in ROUTE_POLICY.items():
        if method != "GET" or "{school_id}" not in path or policy.level in (PUBLIC, API_KEY):
            continue
        url = re.sub(r"\{(\w+)\}", lambda m: c_school["id"] if m.group(1) == "school_id" else "x", path)
        got = w.c.get(url, headers=w.oh)
        assert got.status_code in (403, 404), f"GET {url} -> {got.status_code} {got.text[:200]}"


# ---------------------------------------------------------------- 6

def _parameterless_gets() -> list[str]:
    return sorted(path for (method, path), p in ROUTE_POLICY.items()
                  if method == "GET" and "{" not in path and p.level not in (PUBLIC, API_KEY, OWNER)
                  and not path.startswith("/docs") and not path.endswith(".json"))


@pytest.mark.parametrize("acting,other", [("A", "B"), ("B", "A")])
def test_no_route_returns_another_schools_records(w, acting, other):
    """Every parameterless GET the app serves, called as an owner acting in
    one school: none answers with a marker of the other linked school (or of
    the unlinked one). The owner overview is excluded by its level, and
    checked on its own below."""
    _choose(w, acting)
    foreign = [m for key in (other, "C") for m in w.school(key)["markers"]]
    own = w.school(acting)["markers"]
    leaks, errors, seen = [], [], set()
    for path in _parameterless_gets():
        r = w.c.get(path, headers=w.oh)
        if r.status_code >= 500 and r.status_code != 503:
            errors.append(f"{path} -> {r.status_code}")
        text = r.text
        leaks += [f"{path}: {m}" for m in foreign if m in text]
        seen.update(m for m in own if m in text)
    assert not leaks, leaks
    assert not errors, errors
    # Not vacuous: the same sweep does find the acting school's own records
    # (its teacher in the roster, its assessment, its API key, its name).
    assert set(own[:5]) <= seen, sorted(set(own[:5]) - seen)


def test_the_overview_is_per_school_aggregates_only(w):
    _choose(w, "A")
    r = w.c.get("/api/v1/owner/overview", headers=w.oh)
    assert r.status_code == 200, r.text
    rows = r.json()["schools"]
    assert [s["schoolId"] for s in rows] == [w.school("A")["id"], w.school("B")["id"]]
    allowed = {"schoolId", "name", "period", "periodStart", "periodEnd", "papersThisTerm", "syllabusPlanned",
               "syllabusTaught", "syllabusPacePct", "rowsBehind", "coverRequested", "coverFilled",
               "coverFilledPct", "note"}
    for row in rows:
        assert set(row) <= allowed
        assert all(v is None or isinstance(v, (int, float, str)) for v in row.values())
    everyone = [m for key in "ABC" for m in w.school(key)["markers"] if not m.startswith("Campus")]
    assert not [m for m in everyone if m in r.text]
    assert w.school("C")["id"] not in r.text


# ---------------------------------------------------------------- 7

def test_an_owner_acting_as_principal_cannot_issue_or_withdraw_owner_links(w):
    _choose(w, "A")
    r = w.c.post("/api/v1/owner-links", json={}, headers=w.oh)
    assert r.status_code == 403 and "school's own principal" in r.json()["detail"]
    links = w.c.get("/api/v1/owner-links", headers=w.oh)
    assert links.status_code == 200
    mine = next(x for x in links.json() if x["ownerId"] == w.owner_id)
    assert w.c.delete(f"/api/v1/owner-links/{mine['id']}", headers=w.oh).status_code == 403


def test_a_code_is_single_use_and_another_schools_link_is_404(w):
    code = w.c.post("/api/v1/owner-links", json={}, headers=w.school("C")["principal"]).json()
    assert code["code"].startswith("own_") and code["status"] == "open"
    other = w.c.post("/api/v1/owner/register", json={
        "name": "Second owner", "email": f"o2-{w.tag}@example.com", "password": PASSWORD, "code": code["code"]})
    assert other.status_code == 200, other.text
    again = w.c.post("/api/v1/owner/links/redeem", json={"code": code["code"]}, headers=w.oh)
    assert again.status_code == 403 and "already been used" in again.json()["detail"]
    # A's principal cannot see or withdraw C's link
    assert w.c.delete(f"/api/v1/owner-links/{code['id']}", headers=w.school("A")["principal"]).status_code == 404
    assert code["id"] not in w.c.get("/api/v1/owner-links", headers=w.school("A")["principal"]).text
    # only the hash is kept: the list shows the hint, never the code
    listed = w.c.get("/api/v1/owner-links", headers=w.school("C")["principal"]).text
    assert code["code"] not in listed and code["codeHint"] in listed
    # a teacher invite is not an owner code
    bad = w.c.post("/api/v1/owner/register", json={
        "name": "x", "email": f"o3-{w.tag}@example.com", "password": PASSWORD, "code": "not-an-owner-code"})
    assert bad.status_code == 403


def test_the_owners_actions_are_audited(w):
    from academicos.assessment.audit_log import get_audit_log
    _choose(w, "A")
    # a principal-level write the owner makes inside school A
    made = w.c.post("/api/v1/auth/invites", json={"role": "teacher"}, headers=w.oh)
    assert made.status_code == 200, made.text
    log = get_audit_log(auth_routes._cfg.data_root)
    for action in ("owner_link_created", "owner_registered", "owner_link_redeemed", "owner_school_switched"):
        assert log.for_action(action), action
    row = log.for_action("admin_action")[0]
    assert row["actor"] == w.owner_id
    assert row["details"]["viaOwner"] is True and row["details"]["schoolId"] == w.school("A")["id"]


# ---------------------------------------------------------------- 5 (last: it ends B's link)

def test_a_revoked_link_removes_access_at_once(w):
    from academicos.assessment.audit_log import get_audit_log
    b = w.school("B")
    _choose(w, "B")
    assert _assessment_ids(w) == {b["assessment_id"]}
    revoked = w.c.delete(f"/api/v1/owner-links/{w.link_b}", headers=b["principal"])
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    # the very next request: no longer B's principal, and B is gone
    r = w.c.get("/api/v1/assessments", headers=w.oh)
    assert r.status_code == 403 and r.json()["detail"] == auth_routes.OWNER_CHOOSE_DETAIL
    me = w.c.get("/api/v1/auth/me", headers=w.oh).json()
    assert (me["role"], me["schoolId"]) == ("owner", "")
    assert [s["schoolId"] for s in w.c.get("/api/v1/owner/schools", headers=w.oh).json()] == [w.school("A")["id"]]
    assert w.c.post("/api/v1/owner/active-school", json={"schoolId": b["id"]}, headers=w.oh).status_code == 403
    assert b["id"] not in w.c.get("/api/v1/owner/overview", headers=w.oh).text
    assert w.c.delete(f"/api/v1/owner-links/{w.link_b}", headers=b["principal"]).status_code == 409
    entry = get_audit_log(auth_routes._cfg.data_root).for_action("owner_link_revoked")[0]
    assert entry["details"]["ownerId"] == w.owner_id and entry["details"]["wasLinked"] is True
