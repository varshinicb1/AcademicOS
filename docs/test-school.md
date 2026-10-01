# A test school on the live site

`scripts/seed_test_school.py` builds a complete school you can sign in to and click through, on the live
site or on a local server. It uses only the public API, the same calls the web makes, so it tests the
product the way a school would meet it.

## What it makes

| Who | How many | Where |
|---|---|---|
| Principal | 1 | registers with the principal key |
| Teachers | 3 (Mathematics, Science, English) | allocated 6 periods a week in 10-A and 10-B |
| Students | 4 | two in 10-A, two in 10-B, with parental consent recorded |
| Parent | 1 | linked to the first student |

It also sets up:
- the school profile;
- classes 6 and 10 from the CBSE syllabus;
- a calendar, two terms and a bell schedule;
- a solved, published timetable.

Every account gets its own random password. The sign-in details go to a file in your home folder,
`academicos-<school-id>-logins.txt`, and are never printed to the screen.

## Run it

You need the principal key. Read it yourself; nobody else should:

```bash
gcloud secrets versions access latest --secret=principal-bootstrap-key --project vidyuthlabs
```

Then:

```bash
python scripts/seed_test_school.py
```

The script asks for the key without echoing it, or reads `ACOS_PRINCIPAL_KEY`. By default it makes
`test-school-<today>` on the live API.

- **Another school:** `--school-id test-school-2`. A school that already has a principal refuses the key,
  so each run needs a new id.
- **A local server:** `--api http://127.0.0.1:8010/api/v1`.

Sign in at https://vidyuthlabs.web.app with any line of the logins file.

## Next steps after it runs

- **As the principal:**
  - Lesson plans → **Plan every section** (approve the proposed topics) gives every section a dated plan.
  - Exams → a datesheet, published, then appears on the students' Exams and their Coming up.
- **As a teacher:**
  - My day shows the timetabled periods.
  - Papers → Generate makes a paper from the bank.
  - Set homework reaches the class.
- **As a student:** Today, the week, homework, Exams → **Prepare**, and Progress.
- **As the parent:** My children shows the child's week, homework and report card.

## Remove it

A test school is a real school in the live database. Its data is scoped to its own school id, and no
other school can see it. To stop its staff signing in, the principal closes their accounts under
**Setup → Staff and access** (each person's menu → **Close account**).
