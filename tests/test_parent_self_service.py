"""A parent's own account routes. A parent may call only route_policy.PARENT_PATHS; the audit
(2026-10-04) found their own password change and their Guide progress refused with "a parent account
can see only their children's pages", although the school hands a parent a temporary password,
Settings offers the change, and the Guide saves progress."""
from __future__ import annotations

from test_guardians import _h, _parent
from test_homework import w as homework_world


def test_a_parent_can_change_their_own_password_and_keep_their_guide_progress(tmp_path, monkeypatch):
    gen = homework_world.__wrapped__(tmp_path, monkeypatch)
    hw = next(gen)
    try:
        mum = _h(_parent(hw))
        put = hw.c.put("/api/v1/me/progress/guide_seen", json={"value": True}, headers=mum)
        assert put.status_code == 200, put.text
        assert hw.c.get("/api/v1/me/progress", headers=mum).status_code == 200
        wrong = hw.c.post("/api/v1/auth/password",
                          json={"currentPassword": "not-it", "newPassword": "a-new-password-1"}, headers=mum)
        assert wrong.status_code == 400, "the route is reached; the wrong current password is what is refused"
    finally:
        gen.close()


def test_a_parent_still_cannot_reach_the_schools_other_routes(tmp_path, monkeypatch):
    gen = homework_world.__wrapped__(tmp_path, monkeypatch)
    hw = next(gen)
    try:
        mum = _h(_parent(hw))
        for path in ("/api/v1/setup-status", "/api/v1/calendar-feed", "/api/v1/auth/users", "/api/v1/homework"):
            assert hw.c.get(path, headers=mum).status_code == 403, path
    finally:
        gen.close()
