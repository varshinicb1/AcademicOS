# Handover: school-ready grades 9 and 10 (2026-10-03)

Paste the **Prompt** below into the next session. Everything under it is the evidence behind it.

## Prompt

> You are continuing AcademicOS work for a school that must generate **question papers for classes 9 and 10, all five core subjects (English, Hindi, Mathematics, Science, Social Science)**. Its onboarding must capture every detail and configure everything, with a user guide and a calm UI. Outcomes must work, not just look good.
>
> Read first: `CLAUDE.md`, `HANDOVER.md`, `docs/agent-workflow.md`, `docs/handover-grade9-10.md` (this file). Work in a worktree, one task per branch, both gates before any PR, never deploy unless you are the maintainer's session.
>
> Do these, in order:
> 1. **Question bank for classes 9-10 (the long pole).** Follow "Bank batch" below, one chapter at a time, one opencode process at a time. Priority: Social Science 10 (`jess1`-`jess4`) and 9 (`iest1`), English 10 (`jeff1`, `jefp1`) and 9 (`iebe1`), Hindi 9 (`ihga1`) and 10 (`jhks1`, `jhkr1`; Hindi B: `jhsp1`, `jhsy1`). Check a Hindi chapter's text extraction before scaling it.
> 2. **Serve what was generated.** Generated questions are `source: ai_generated` and are not served until reviewed (REQUIREMENTS QB-5). Decide with the owner: a bulk-approve screen for the reviewer, then make approved items reach `GET /papers/quick-generate`. Measure answerable coverage per class and subject afterwards; do not trust record counts.
> 3. **Wizard gaps.** Add an exam-pattern step (terms' exam names, paper header and general instructions via the school templates), a Maths Standard/Basic choice if the backend supports it, and a Hindi/third-language choice. Teacher-to-subject allocation can only be set after a teacher accepts the invite: add a "give subjects" prompt on the Overview checklist for teachers who have since joined.
> 4. **Design.** Fix the dark theme's primary button (white on the ember gradient is 2.09-4.41:1, needs 4.5:1), update `docs/design-system.md` and `design/tokens.json` so they describe the light-first theme the app now ships, and add a contrast test over the real palette.
> 5. **Land it.** Unpushed branches `feat/setup-wizard` and `feat/guide-nav` hold ~33 commits master lacks (timetable, plans, cover, webhooks, owners, ROLE-4). They are another session's integration work: do not push them; ask the owner.

## What exists now (merged to master by this handover's PR)

| Piece | Where | Evidence |
|---|---|---|
| One-call school setup | `POST /curriculum/school-setup`, `src/academicos/curriculum/school_setup*.py` | `tests/test_school_setup.py`, route inventory 322, contract regenerated |
| Setup wizard | `/school/setup`, `frontend/lib/presentation/onboarding/` | `setup_wizard_test.dart` (5), `setup_wizard_logic_test.dart` (12) |
| Guide | `/school/guide`, `frontend/lib/presentation/guide/` | `guide_test.dart`, `guide_welcome_test.dart` |
| Light default | `LocalStore.themeModeName` | `theme_default_test.dart` |
| Bank bridge + groundedness | `scripts/gen_cbse_chapter.py` (`--bridge`, `ungrounded`) | `tests/test_cbse_generate.py` (77) |

Not verified: the wizard in a real browser (a local build was made but not driven), and the full backend suite (only the setup, contract, route-inventory and generator tests were run; CI is down).

## Bank batch (how it works, and what was learned)

Source PDFs: `ncert-dataset/textbooks/chapters/<code>/<code>NN.pdf`, manifest in `ncert-dataset/textbooks/manifest.json`. Use the venv at `D:\AcademicOS-venv` (PyMuPDF 1.28.2 is pinned; the global Python 3.14 refuses).

Per chapter, three steps:

```bash
# 1. write the prompts (one per call) to a work folder outside the repo
PYTHONIOENCODING=utf-8 python scripts/gen_cbse_chapter.py --book jess2 --chapter 1 --marks 24 \
  --bridge D:/acos-wt/_ocwork --check
# 2. an opencode session answers them (brief: docs/opencode-bank-brief.md, copy it to the work folder)
opencode run --dir "D:\acos-wt\_ocwork" -m opencode-go/space-bunny-free --auto \
  "Read BRIEF.md in this folder and do the job it describes for every prompt file in jess2-01/." > log 2>&1
# 3. validate and write the chapter's own file (never the shared questions.json, it holds class 1)
PYTHONIOENCODING=utf-8 python scripts/gen_cbse_chapter.py --book jess2 --chapter 1 --marks 24 \
  --bridge D:/acos-wt/_ocwork --out academicos-data/corpus/ai-cbse-9-10/jess2-01.json
```

Learned the hard way:
- **`opencode/*-free` (Zen) models return 403** ("free tier can only be used from within OpenCode") from `opencode run`, even in a full session. The free models under the authenticated **OpenCode Go** provider work: `opencode-go/space-bunny-free` finished a 6-prompt chapter in about 6 minutes; `opencode-go/longcat-2.5-preview-free` stalled with an empty log for 22 minutes. Give each session a timeout (about 25 minutes) and kill a stalled one; check `tasklist | grep -i opencode` for orphans after.
- **The driver overwrites its `--out` file** with only that run's records. Always give each chapter its own `--out`, then merge. Nothing merges `ai-cbse-9-10/` yet: `scripts/collect_ai_cbse.py` and `finalize_bank.py` read `ai-cbse/questions.json` only. Write the merge step.
- A free model invents facts the validator cannot see. Hence the `evidence` quotes and the figure check. It cannot catch a wrong *word* (a wrong place name), so a second independent session as verifier, or a human reviewer, is still needed.
- Pilot, `jess2` ch.1, 6 prompts: 10 of 10 kept, figures match the book's Table 1.4. One "map" question was really built on a table: expect Section F (map-based) to need review or to be dropped for Social Science chapters with no map.
- The class 9 books are the new NCERT set (Kaveri, Ganita Manjari, Exploration, Understanding Society Part I). Hindi 10 has four books; CBSE Hindi A uses Kshitij-2 and Kritika-2, Hindi B uses Sparsh-2 and Sanchayan-2.

## Design review (measured)

- Light palette: every measured text/background pair passes WCAG AA (lowest 4.67:1). Calm: neutral surfaces, one ember accent.
- Dark: text passes; the primary button (white label on the ember gradient) measures 2.09:1 at the light end and 4.41:1 at the dark end, so it fails.
- Defaults before this change: dark, with aurora backdrop, glass cards and ember glow. Now: light. Dark remains a Settings choice.
- Three palettes are documented or coded: `docs/design-system.md` (indigo `#4F46E5`, stale), `app_constants.dart` / light theme (ember-deep `#C2410C`), and the Emergera dark brand (ember `#FF5A1F`). The doc is the odd one out.

## Gotchas

- `git cherry-pick --abort` mid-sequence resets to the start of the whole sequence, not the last commit.
- Running `flutter pub get` or a build rewrites the Windows/Linux/macOS plugin registrants. Do not commit them.
- Starting a local server for a browser check: the web build defaults to `http://localhost:8010/api/v1`; build with `--dart-define=ACADEMICOS_API=...` for another port. A bare test school needs `ACOS_PRINCIPAL_BOOTSTRAP_KEY` set to a generated key on the server and `POST /auth/register` with `principalKey`.
- Teachers import creates an invite, not an account; allocations by `teacher_email` need the account.
