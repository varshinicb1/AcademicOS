"""Make a complete test school on a running AcademicOS, ready to sign in to.

What it makes, through the public API only, exactly as a principal would:

  * a principal, who registers with the operator's principal key;
  * the school profile, classes 6 and 10 seeded from the CBSE syllabus,
    sections 10-A and 10-B, a calendar, two terms and a bell schedule;
  * three teachers (Mathematics, Science, English) allocated to 10-A and 10-B,
    and a solved, published timetable;
  * four students, two in each section, with parental consent recorded;
  * one parent, linked to the first student.

Every account gets its own random password. The sign-in details are written
to a file in your home folder (not the repository) and are never printed.

    # the key is asked for and not echoed; or set ACOS_PRINCIPAL_KEY
    python scripts/seed_test_school.py
    python scripts/seed_test_school.py --school-id test-school-2 --api http://127.0.0.1:8010/api/v1

To fetch the live key (run it yourself; nobody else should read it):

    gcloud secrets versions access latest --secret=principal-bootstrap-key --project vidyuthlabs

The school id must be new: a school that already has a principal refuses the
key. Re-running with a new --school-id makes a second, separate school.
"""
from __future__ import annotations

import argparse
import contextlib
import getpass
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

LIVE_API = "https://academicos-backend-2eskom55ta-el.a.run.app/api/v1"

TEACHERS = [("maths", "Meera Iyer", "Mathematics"), ("science", "Suresh Rao", "Science"),
            ("english", "Esha Thomas", "English")]
STUDENTS = [("asha", "Asha Kumar", "10-A"), ("ravi", "Ravi Shah", "10-A"),
            ("diya", "Diya Nair", "10-B"), ("kabir", "Kabir Singh", "10-B")]
PARENT = ("meena", "Meena Kumar", "asha")


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/")

    def call(self, method: str, path: str, body=None, token: str | None = None, ok=(200,)):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "academicos-seed-test-school/1",
                                              **({"Authorization": f"Bearer {token}"} if token else {})})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                status, payload = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, payload = e.code, e.read()
        try:
            parsed = json.loads(payload or b"null")
        except ValueError:
            parsed = payload.decode("utf-8", "replace")
        if status not in ok:
            detail = parsed.get("detail") if isinstance(parsed, dict) else parsed
            raise SystemExit(f"{method} {path} -> {status}: {detail}")
        return parsed


def year_dates(today: date) -> tuple[str, str, str]:
    """The Indian school year containing today: April to March."""
    start = today.year if today.month >= 4 else today.year - 1
    return f"{start}-{str(start + 1)[2:]}", f"{start}-04-01", f"{start + 1}-03-31"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api", default=LIVE_API)
    p.add_argument("--school-id", default=f"test-school-{date.today():%Y%m%d}")
    p.add_argument("--school-name", default="AcademicOS Test School")
    p.add_argument("--out", default=None, help="where to write the sign-in details (default: your home folder)")
    args = p.parse_args()

    key = os.environ.get("ACOS_PRINCIPAL_KEY") or getpass.getpass("Principal key (not shown): ")
    if not key.strip():
        raise SystemExit("a principal key is needed")
    api = Api(args.api)
    domain = f"{args.school_id}.test"
    out = Path(args.out) if args.out else Path.home() / f"academicos-{args.school_id}-logins.txt"
    logins: list[tuple[str, str, str, str]] = []

    def password() -> str:
        return secrets.token_urlsafe(12)

    # -- the principal ---------------------------------------------------------
    pw = password()
    email = f"principal@{domain}"
    reg = api.call("POST", "/auth/register", {"name": "Priya Menon", "email": email, "password": pw,
                                              "schoolId": args.school_id, "principalKey": key.strip()})
    tok = reg["token"]
    logins.append(("principal", "Priya Menon", email, pw))
    print(f"principal registered for {args.school_id}")

    # -- the school -------------------------------------------------------------
    label, start, end = year_dates(date.today())
    api.call("PUT", "/curriculum/school-profile", {"name": args.school_name, "address": "1 School Road",
                                                   "affiliation": "CBSE (test)"}, tok)
    for grade in (10, 6):
        api.call("POST", "/curriculum/seed/cbse", {"academicYearLabel": label, "startDate": start,
                                                   "endDate": end, "grade": grade}, tok)
    year = api.call("GET", f"/curriculum/academic-years?school_id={args.school_id}", token=tok)[0]["id"]
    api.call("POST", f"/curriculum/academic-years/{year}/calendar",
             {"weeklyOffDays": ["sunday"], "alternateSaturdayRule": "none"}, tok, ok=(200, 409))
    mid = f"{start[:4]}-09-30"
    api.call("POST", f"/curriculum/academic-years/{year}/terms",
             {"name": "Term 1", "startDate": start, "endDate": mid}, tok, ok=(200, 409))
    api.call("POST", f"/curriculum/academic-years/{year}/terms",
             {"name": "Term 2", "startDate": f"{start[:4]}-10-01", "endDate": end}, tok, ok=(200, 409))
    slots = [{"start": f"{8 + i:02d}:00", "end": f"{8 + i:02d}:45"} for i in range(7)]
    api.call("POST", f"/curriculum/academic-years/{year}/bell-schedules", {"name": "Main", "slots": slots},
             tok, ok=(200, 409))
    grades = {g["number"]: g["id"] for g in api.call("GET", f"/curriculum/academic-years/{year}/grades", token=tok)}
    api.call("POST", f"/curriculum/grades/{grades[10]}/sections", {"name": "B"}, tok, ok=(200, 409, 422))
    sections = {f"{s['gradeNumber']}-{s['name']}": s["id"]
                for s in api.call("GET", f"/curriculum/academic-years/{year}/sections", token=tok)}
    subjects = {s["name"]: s["id"] for s in api.call("GET", f"/curriculum/grades/{grades[10]}/subjects", token=tok)}
    print(f"school set up: {label}, sections {', '.join(sorted(sections))}")

    # -- people, by invite --------------------------------------------------------
    def join(role: str, name: str, email: str) -> dict:
        code = api.call("POST", "/auth/invites", {"role": role, "email": email}, tok)["code"]
        pw = password()
        user = api.call("POST", "/auth/register", {"inviteCode": code, "name": name, "email": email,
                                                   "password": pw})["user"]
        logins.append((role, name, email, pw))
        return user

    teachers = {short: join("teacher", name, f"{short}.teacher@{domain}") for short, name, _ in TEACHERS}
    for short, _, subject in TEACHERS:
        for sec in ("10-A", "10-B"):
            api.call("PUT", f"/curriculum/sections/{sections[sec]}/allocations/{subjects[subject]}",
                     {"teacherId": teachers[short]["id"], "periodsPerWeek": 6}, tok)
    solved = api.call("POST", f"/curriculum/academic-years/{year}/timetable/solve",
                      {"apply": True, "timeLimitSeconds": 30}, tok)
    print(f"timetable: {solved.get('status')}, {solved.get('placed')} periods placed")

    students = {}
    for short, name, sec in STUDENTS:
        students[short] = join("student", name, f"{short}@{domain}")
        api.call("POST", "/curriculum/student-enrollments",
                 {"studentId": students[short]["id"], "sectionId": sections[sec]}, tok, ok=(200, 409))
        api.call("POST", "/consent", {"studentId": students[short]["id"], "guardianName": "Parent (test)",
                                      "method": "Test school: recorded by the seeding script"}, tok)

    short, name, child = PARENT
    email = f"{short}.parent@{domain}"
    code = api.call("POST", f"/students/{students[child]['id']}/guardian-invites",
                    {"relation": "mother", "email": email}, tok)["code"]
    pw = password()
    api.call("POST", "/auth/register", {"inviteCode": code, "name": name, "email": email, "password": pw})
    logins.append(("parent", name, email, pw))

    # -- the sign-in details --------------------------------------------------------
    lines = [f"AcademicOS test school: {args.school_name} ({args.school_id})",
             f"API: {args.api}", "Sign in at https://vidyuthlabs.web.app with these. Keep this file private.", ""]
    lines += [f"{role:<10} {name:<14} {email:<40} {pw}" for role, name, email, pw in logins]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with contextlib.suppress(OSError):  # Windows keeps it under the user's own profile
        out.chmod(0o600)
    print(f"{len(logins)} accounts made; sign-in details written to {out}")
    for role, name, email, _ in logins:
        print(f"  {role:<10} {email}")


if __name__ == "__main__":
    sys.exit(main())
