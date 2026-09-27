# Working in this repo alongside other agents

Read this before you change anything. `CLAUDE.md` and `AGENTS.md` describe the
system; this file describes **how work gets done here**: several Claude sessions
at once, each in its own worktree, one integration branch, and a live product.
Every rule below exists because breaking it cost real work once. The reason is
given with each so you can apply it to a case the rule does not name.

Last reconciled: 2026-09-26. Counts in prose rot; re-measure before you rely on
one.

---

## 1. What is being built right now

- **The product is the web app**, classes **6-10**. The Flutter web build is
  served from Firebase Hosting at **vidyuthlabs.web.app** and talks to the
  FastAPI backend on Cloud Run (`academicos-backend`, `asia-south1`, Cloud SQL
  `academicos-pg`, GCS for blobs). The offline Android app is **out of the first
  release** (user decision, 2026-09-22), and so are classes 11 and 12 (2026-09-23).
  Do not offer a class the product cannot serve.
- **Progress is measured by `docs/product-scorecard.md`** (target 80, then 90)
  and re-audited against the *live* commit. Nothing moves the score until it is
  deployed and an audit has scored it. The 5-phase research number in
  `docs/roadmap.md` (~35%) is separate: report both, never swap one for the other.
- `docs/PRD.md` says what the product is for and what is out of scope.
  `docs/PRODUCTS_AND_RELEASES.md` predates the GCP go-live; where it calls GCP
  "not yet provisioned", GCP is now the live web release.

## 2. Worktrees and branches

All worktrees sit side by side under `C:\Users\varsh\OneDrive\Documents\Sarvam\`.

| Worktree | Branch | Stream | State (2026-09-26) |
|---|---|---|---|
| `AcademicOS-release` | `release/v1` | **Integration.** The only branch that reaches `master`. | pushed as `master` |
| `AcademicOS` | `feat/question-bank-merge` | Question bank (Tasks 121-126) | merged |
| `AcademicOS-calendar` | `feat/product-calendar` | Curriculum, calendar, class setup | merged; **uncommitted edits** to `scripts/export_decomposition_templates.py` and `decomposition/_manifest.json` belong to this stream |
| `AcademicOS-exemplar` | `feat/product-exemplar` | NCERT Exemplar import, bank health report | merged |
| `AcademicOS-gcp` | `feat/product-gcp` | GCP deploy | merged |
| `AcademicOS-paperux` | `feat/product-paperux` | Paper builder UX | merged |
| `AcademicOS-security` | `feat/product-security` | Role gates, audit log | merged |
| `AcademicOS-phone` | `feat/product-phone` | Offline Android app | **not merged** (out of the release); 8 commits plus uncommitted network-policy work |

`wip/*` branches on `origin` are snapshots of uncommitted work that was left in a
worktree when its stream stopped. They were taken without touching the worktree.
Read one before redoing that work; do not merge one blind.

Rules:

- **Work only in your own worktree.** Never edit, check out, reset or clean files
  in another one, even to "tidy up". Read other worktrees freely.
- **Never use a bare `git stash`.** The stash stack is shared by every worktree,
  so `git stash pop` can apply another session's changes into yours. Set work
  aside with a WIP commit instead.
- **Stage by path** (`git add <files>`), never `git add -A` or `git commit -a`.
  Every worktree shows the Flutter `generated_plugin_registrant.*` /
  `generated_plugins.cmake` files as modified. They are build noise. Do not commit
  them, and do not revert them in someone else's tree.
- Branch off `release/v1` for new work, and merge back into it with `--no-ff`
  and a message that says what the merge brings and how any conflict was resolved.

## 3. Working alongside other sessions

These are the rules that were learned the hard way.

1. **Never sweep, revert or "clean up" another session's uncommitted work.**
   `git checkout -- <file>` on a file another session is editing destroys its
   live edits. It happened once. If a file you need is dirty and not yours, ask
   its owner, or the user.
2. **If you offer to wait, wait.** If you tell another session "I'll hold X until
   you answer", do not do X until they answer, even if it looks safe.
3. **Respect file ownership.** At the time of writing, the session *"Make the
   chapter view read the taxonomy chapter tag"* owns:
   - `src/academicos/assessment/pillar_routes.py`
   - `src/academicos/syllabus/cbse_syllabus.py`
   - `tests/test_catalog_chapters.py`, **including its floors** (`TAG_FLOOR`,
     `FILED_FLOOR`, `MAP_TAG_FLOOR`)
   - `academicos-data/syllabus/{Mathematics_6..10,Science_7,8,9}.json`
   - `scripts/syllabus_chapters_from_taxonomy.py`

   If your change moves a count those floors pin, **tell the owner the new counts
   (every pair, the ones that rose as well as the ones that fell) and let them
   change the floor.** Do not edit a floor to make your test pass.
4. **Tell the bank owner before any rebuild of the served bank**
   (`academicos-data/syllabus/questions.json`). A rebuild changes every count
   other streams test against.
5. **At most 3-4 heavy streams at once on this machine.** The development PC shut
   down from overload once. A full pytest run plus a Flutter test run is already
   two.
6. **A test failure is a filter, not a finding.** When a gate fails, report
   everything it measured, including what improved, not just the pairs that
   fell. A partial report once read as a regression that was a net gain.
7. **Read the whole output.** A merge that refused (missing chapter tags) looked
   like success because the output was piped through `grep`. Use `tail`, never a
   filter, on a command whose failure you have to see.

## 4. Before you commit: the gates

    PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 D:/AcademicOS-venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
    cd frontend && flutter analyze --no-fatal-infos && flutter test --exclude-tags live-backend -j 1

The checks most likely to catch a new contributor out:

- **Every route needs a policy row.** `src/academicos/api/route_policy.py` holds
  one table of who may call each (method, path). `tests/test_role_gates.py` fails
  on any served route missing from it, and on any row whose level does not match
  the route's real dependency chain. `tests/test_route_inventory.py` pins the
  route count (163 at the time of writing): a new route bumps it in the same
  commit, with the reason.
- **Registration is invite-only**, in tests too. Use
  `tests/_auth_helpers.py` (`invite_code`, `register_invited`, `grant_consent`)
  rather than posting to `/register` bare.
- **The design system bans emoji and symbol glyphs** in `frontend/lib`, raw hex
  colours, and off-scale spacing (`tests/test_design_tokens.py`, which runs
  `scripts/check_design_tokens.py`). A `✓` in a label fails the build: use an
  `Icon`.
- **Request models forbid unknown fields** (`extra="forbid"`, camelCase aliases).
  A test that posts one shared body to several routes must build a body per model.
- **Web client ↔ backend contract**: `tests/test_frontend_backend_contract.py`.
  A route change must match what the web screens send.
- **The CI deploy triggers on paths.** `.github/workflows/deploy-gcp.yml` and
  `deploy-backend.yml` list the paths that start a deploy (`tests/**` is one).
  A change outside them merges without deploying.
- An `xfail` must be `strict=True` with a reason that says how to un-xfail it
  (see `tests/test_curriculum_seed_grades.py`).

## 5. The question bank

The served bank is `academicos-data/syllabus/questions.json`. The merge writes a
byte-identical copy to `frontend/assets/corpus/questions.json`, and writes every
record it refused, with the reason, to `academicos-data/syllabus/_merge_excluded.json`.
The rules live in `src/academicos/corpus/bank_merge.py`; the scripts only do I/O.

**The order is written in the scripts' docstrings. Read them before you run
anything**: `scripts/merge_question_banks.py` (the whole pipeline) and
`scripts/apply_chapter_tags.py` (why the order matters). In short:

    build_cbe_bank.py / build_sqp_bank.py / build_exemplar_bank.py
    tag_question_bank.py                  # infers chapter tags
    apply_chapter_tags.py                 # writes them into the sources; a builder rerun discards them
    enrich_question_bank.py               # relinks and verifies board schemes (only when that must change)
    merge_question_banks.py               # composes the served bank + the APK copy + the exclusions
    tag_question_bank.py --topics <served bank>   # taxonomy chapter/topic/subtopic tags
    bank_health.py                        # regenerates docs/bank-health.md + bank_health.json

- The 2026-09 rebuilds (Tasks 121-126) did **not** re-run `enrich_question_bank.py`:
  the board records were already stamped with the current scheme verifier, and
  the merge **refuses** a bank that is not, so skipping it fails loudly rather
  than silently. Re-run it only when the board relink itself has to change.
- **One gate decides what can be served**: `bank_merge.unservable_reason` for a
  merged record, and `bank_merge.raw_extraction_reason` for a stem straight out
  of PDF extraction. `pool.py` calls them and keeps no rule of its own, and a
  source scan test enforces that. Add a rule inside the gate, never beside it.
  A second gate over already-gated data once refused 238 of 476 answerable
  questions.
- **Generated files are regenerated, never hand-merged.** On a merge conflict in
  `bank_health.json` or `docs/bank-health.md`, take either side and re-run
  `python scripts/bank_health.py`.
- `--check` on the merge and the health script prints what would change without
  writing. Use it, and quote its numbers, before a real run.
- Nothing is invented. A difficulty or Bloom level the source did not print is
  flagged (`difficultyInferred`, `bloomInferred`) and ignored by selection. A
  marking split is made only where the source shows one.

## 6. Releasing and deploying

1. Merge your branch into `release/v1` (in the `AcademicOS-release` worktree).
2. Run both gates there.
3. `git push origin release/v1:master` and `git push origin release/v1`.
4. CI deploys from `master`. **Until 2026-10-01 CI cannot run** (Actions minutes
   exhausted), so follow **`docs/deploy-by-hand.md`** and do all four of its
   verification checks. The user has authorised hand deploys when both suites
   are green.
5. Record the deploy in that file's live-history table.

## 7. Evidence

The scorecard's rule is the PRD's: *verified* means run with real data through
the running system, with the output inspected. In practice:

- Quote the command and its output. A count you did not measure is not a count.
- Verify the **live** commit (`/health`), not your branch. A stale `build/web` has
  shipped before: rebuild the web bundle, and compare `main.dart.js` byte counts.
- A hand-check sample (answer keys, chapter maps, marking splits) is committed as
  a fixture with its verdicts, so the next change is measured against it.
- An audit is re-run by a fresh reader against the live system and recorded in
  the scorecard's audit log. It is never edited to fit a result.

## 8. Open items (2026-09-26)

- **Bank rebuild pending (Task 126, requirement 5).** It would remove three class
  12 Informatics Practices records whose chart never arrived
  (`PENDING_REBUILD` in `tests/test_bank_surfaces_agree.py`). Classes 6-10 are
  unchanged by it. It needs the bank owner's go-ahead.
- **Six `xfail`s in `tests/test_curriculum_seed_grades.py`**: a stale
  decomposition `_manifest.json` and a missing `export.textbook_sources`. The fix
  is the calendar stream's uncommitted exporter work (see §2).
- **Task 125 (competency share and tiers)** is not started: CBQ is near 0% against
  CBSE's 50%, and the builder still offers tiers that return the same paper.
- **Classes 11 and 12** still appear on the question-bank and syllabus browse
  screens, though the paper builder offers only 6-10.
- **Social Science, English and Hindi for classes 6-9** need source material
  that is not in the repo. That is the largest coverage gap, and it needs the
  user.
- Web bundle size (scorecard item 2.4) is unmeasured on a throttled profile.

## 9. Commits

Match the history: `fix(area): a sentence that says what is now true`, then a
body that says why, what was measured before and after, and anything left
undone. End with the co-author line your session's instructions give. Commit and
push only what you were asked to, and never skip hooks.
