"""Seeds one small, complete school into a throwaway data root so the web app
can be walked end to end in a 375 px phone browser (Task 801, step 4).

Why this exists: the phone audit's widget tests drive real pages against
captured server responses, which proves the layout but not that a teacher can
actually get from sign-in to a printed paper in a browser. Doing that by hand
needs a school that has everything a teacher touches -- a principal, a teacher
who joined by invite, a curriculum, a calendar, subtopics with teaching-time
estimates and a dated schedule with a lesson on today -- and setting that up
from the UI takes twenty minutes of clicking that nobody will repeat. This
script does it over the public API in a few seconds, so the browser evidence
behind the task report can be reproduced from the repo.

It only ever talks to a backend you point it at, and it writes nothing itself:
every row lands in whatever ACOS_DATA_ROOT that backend was started with. Never
run it against a deployed service -- it registers accounts with known
passwords. It refuses any --api that is not a loopback address.

    # terminal 1 -- a backend on a temp data root
    ACOS_DATA_ROOT=%TEMP%/task801/data ACOS_PRINCIPAL_BOOTSTRAP_KEY=task801-local-demo-key \
        python -m academicos.cli serve --host 127.0.0.1 --port 8010
    # terminal 2
    python scripts/seed_phone_demo_school.py --principal-key task801-local-demo-key

It is idempotent in the sense that the backend's own seeding is: re-running it
against a data root that already has the school logs in instead of registering
and reuses the curriculum, so a half-finished run can just be run again.

Then build and serve the web app and walk it at 375 px:

    cd frontend && flutter build web --release      # default ACADEMICOS_API is
                                                    # http://localhost:8010/api/v1
    cd build/web && python -m http.server 8000      # an origin the backend's
                                                    # default CORS list allows

    As teacher@demo.school: Today -> My Schedule -> today's lesson -> "Yes" to
    mark it taught; Today -> New Assessment -> Class 10 -> Mathematics -> Use
    the "Unit Test" CBSE pattern -> Generate paper -> Pick on a question ->
    search the bank -> pick -> "Done: download".
    As principal@demo.school: the drawer -> Principal, and #/admin for the six
    console tabs.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

PRINCIPAL_EMAIL = "principal@demo.school"
TEACHER_EMAIL = "teacher@demo.school"
DEMO_PASSWORD = "demo-pass-801"
SCHOOL_ID = "school_demo_801"
SUBJECT = "Mathematics"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "[::1]", "::1"}

# One chapter's worth of real teaching, enough for a week of dated lessons.
SUBTOPICS = [
    ("Real Numbers in practice", ["Euclid's division lemma", "Fundamental theorem of arithmetic",
                                  "Irrationality of root 2", "Decimal expansions"]),
]


class Api:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.token: str | None = None

    def __call__(self, method: str, path: str, body: dict | None = None,
                 params: dict | None = None, allow: tuple[int, ...] = ()) -> dict | list | None:
        url = f"{self.base}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code in allow:
                return {"_status": e.code, "_detail": detail}
            raise SystemExit(f"{method} {path} -> {e.code}: {detail}") from e


def _sign_in_principal(api: Api, principal_key: str) -> dict:
    """Registers the school's first principal, or logs in if it already exists."""
    res = api("POST", "/auth/register", {
        "name": "Priya Principal", "email": PRINCIPAL_EMAIL, "password": DEMO_PASSWORD,
        "principalKey": principal_key, "schoolId": SCHOOL_ID,
    }, allow=(403, 409))
    if "_status" in res:
        res = api("POST", "/auth/login", {"email": PRINCIPAL_EMAIL, "password": DEMO_PASSWORD})
    api.token = res["token"]
    return res["user"]


def _invite_teacher(api: Api) -> None:
    """A teacher can only join through an invite -- the flow the phone audit
    screenshots, so it is worth creating a real one rather than a second
    bootstrap-key account."""
    invite = api("POST", "/auth/invites", {"role": "teacher", "email": TEACHER_EMAIL})
    teacher_api = Api(api.base)
    res = teacher_api("POST", "/auth/register", {
        "name": "Tara Teacher", "email": TEACHER_EMAIL, "password": DEMO_PASSWORD,
        "inviteCode": invite["code"],
    }, allow=(403, 409))
    if "_status" in res:
        res = teacher_api("POST", "/auth/login", {"email": TEACHER_EMAIL, "password": DEMO_PASSWORD})
    return res["user"]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api", default="http://127.0.0.1:8010/api/v1")
    p.add_argument("--principal-key", required=True,
                   help="the ACOS_PRINCIPAL_BOOTSTRAP_KEY the local backend was started with")
    p.add_argument("--periods-per-week", type=int, default=6)
    args = p.parse_args(argv)

    host = urllib.parse.urlparse(args.api).hostname or ""
    if host.lower() not in LOOPBACK_HOSTS:
        p.error(f"--api host {host!r} is not loopback; this script seeds known passwords and "
                "must never be pointed at a deployed service")

    api = Api(args.api)
    principal = _sign_in_principal(api, args.principal_key)
    print(f"principal {principal['email']} in school {principal['schoolId']}")

    teacher = _invite_teacher(api)
    print(f"teacher   {teacher['email']} joined by invite")

    today = date.today()
    year_start = date(today.year if today.month >= 6 else today.year - 1, 6, 1)
    year_end = date(year_start.year + 1, 3, 31)
    seeded = api("POST", "/curriculum/seed/cbse10", {
        "academicYearLabel": f"{year_start.year}-{str(year_end.year)[2:]}",
        "startDate": year_start.isoformat(), "endDate": year_end.isoformat(),
    })
    year_id, grade_id = seeded["academicYearId"], seeded["gradeId"]
    print(f"curriculum {seeded['subjectsSeeded']} subjects, {seeded['chaptersSeeded']} chapters")

    # A calendar, so working days -- and therefore lesson dates -- exist at all.
    api("POST", f"/curriculum/academic-years/{year_id}/calendar",
        {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "second_fourth"}, allow=(409,))
    api("POST", f"/curriculum/academic-years/{year_id}/period-configuration", {"periodMinutes": 45})

    subjects = api("GET", f"/curriculum/grades/{grade_id}/subjects")
    subject = next(s for s in subjects if s["name"] == SUBJECT)
    book = api("GET", f"/curriculum/subjects/{subject['id']}/books")[0]
    teacher_id = teacher["id"]
    api("POST", "/curriculum/teacher-assignments", {"teacherId": teacher_id, "bookId": book["id"]},
        allow=(409,))
    print(f"assigned  {teacher['name']} to {book['title'][:48]}...")

    # Subtopics are what a lesson is: seeding stops at chapters, so the first
    # chapter gets a real topic and its subtopics here.
    chapters = api("GET", f"/curriculum/books/{book['id']}/chapters")
    chapter = chapters[0]
    existing = api("GET", f"/curriculum/chapters/{chapter['id']}/topics")
    if not existing:
        for topic_name, subtopic_names in SUBTOPICS:
            topic = api("POST", f"/curriculum/chapters/{chapter['id']}/topics", {"name": topic_name})
            for seq, name in enumerate(subtopic_names):
                api("POST", f"/curriculum/topics/{topic['id']}/subtopics", {"name": name, "seq": seq})
    print(f"subtopics under {chapter['name']}")

    est = api("POST", f"/curriculum/books/{book['id']}/teaching-time-estimates",
              {"periodsPerWeek": args.periods_per_week, "recompute": True},
              params={"academic_year_id": year_id})
    print(f"estimates {est['estimatesCreated']} subtopics, {est['periodsAllocated']} periods")

    sched = api("POST", f"/curriculum/books/{book['id']}/schedule",
                {"periodsPerWeek": args.periods_per_week, "force": True},
                params={"academic_year_id": year_id})
    print(f"schedule  {sched['lessonsCreated']} lessons, "
          f"{sched['firstScheduledDate']} .. {sched['lastScheduledDate']}")

    # An overdue lesson, so the principal's Delayed Topics card and its
    # Reschedule button have something real to show on the phone.
    lessons = api("GET", f"/curriculum/books/{book['id']}/schedule",
                  params={"academic_year_id": year_id})
    if lessons:
        api("POST", f"/curriculum/scheduled-lessons/{lessons[0]['id']}/reschedule",
            {"newDate": (today - timedelta(days=9)).isoformat(), "reason": "Demo: left overdue"},
            allow=(400, 409, 422))

    print("\nsign in at the served build as:")
    print(f"  principal  {PRINCIPAL_EMAIL} / {DEMO_PASSWORD}")
    print(f"  teacher    {TEACHER_EMAIL} / {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
