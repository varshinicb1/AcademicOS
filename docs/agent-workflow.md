# Working in this repo alongside other agents

Read this before you change anything. `CLAUDE.md` and `AGENTS.md` describe the
system; this file describes **how work gets done here**: several people and Claude
sessions at once, each on its own branch, every change a pull request into `master`,
and a live product. **The pull-request process itself is [`CONTRIBUTING.md`](../CONTRIBUTING.md).**
Every rule below exists because breaking it cost real work once. The reason is
given with each so you can apply it to a case the rule does not name.

Last reconciled: 2026-09-28 (pull requests replace the `release/v1` integration merges). Counts in prose
rot; re-measure before you rely on one.

---

## 1. What is being built right now

- **Requirements v3 (2026-09-27): [`docs/REQUIREMENTS.md`](REQUIREMENTS.md).** Grades 1-10, four
  products on one backend: the web console (exam automation + the principal's full admin), a
  **teacher app**, a **student app** with parent mode, and the question bank with its API. It supersedes
  the earlier "web-first, classes 6-10, phone app out" scope.
- **What is live** is the v2 web console for classes 6-10 (vidyuthlabs.web.app, Cloud Run
  `academicos-backend`, Cloud SQL `academicos-pg`, GCS). **[`HANDOVER.md`](../HANDOVER.md)** has the gap
  analysis against v3 and the milestone order.
- **Progress is measured by an audited scorecard** against the *live* commit. The v2 instrument
  (`docs/product-scorecard.md`) measured 60.5 at `09649eb`; adopt the v3 instrument (`REQUIREMENTS.md` section 12)
  and take a baseline audit before new work is scored. Nothing moves a score until it is deployed and
  audited. The 5-phase research number in `docs/roadmap.md` (~35%) is separate: report both.

## 2. Branches and worktrees

`master` is what is live. **Every change reaches it as a pull request** that the maintainer reviews,
gates and merges (`CONTRIBUTING.md`); nobody else pushes to `master`. Until the 2026-09-27 handover the
work ran in several git worktrees on one laptop, with `release/v1` as the integration branch. Since
2026-09-28 `release/v1` only follows `master` (the maintainer moves it after each merge), and nobody
branches from it or merges into it. Open branches and their state are in `HANDOVER.md` section 8.

`wip/*` and `draft/*` branches on `origin` are snapshots of unfinished work. Read one before redoing that
work; do not merge one blind. Every such branch on `origin` was finished or merged on 2026-09-28
(PRs #1-#3); unfinished work now lives as a draft PR instead.

Rules, if you run more than one stream or session at a time:

- **One task per branch, one branch per PR**, branched from `origin/master`:
  `git switch -c <type>/<topic> origin/master`. With several sessions on one machine, give each its own
  worktree (`git worktree add ../AcademicOS-<name> -b feat/<name> origin/master`). Never edit, check out,
  reset or clean files in another stream's worktree. Read them freely.
- **Never use a bare `git stash`.** The stash stack is shared by every worktree, so `git stash pop` can
  apply another session's changes into yours. Set work aside with a WIP commit instead.
- **Stage by path** (`git add <files>`), never `git add -A` or `git commit -a`. Every checkout shows the
  Flutter `generated_plugin_registrant.*` / `generated_plugins.cmake` files as modified. They are build
  noise: do not commit them.
- **If `master` moves, merge it into your branch**, and say in the merge message how any conflict was
  resolved. Do not rebase a branch you have pushed: review comments are anchored to its commits.

## 3. Working alongside other sessions

These are the rules that were learned the hard way.

1. **Never sweep, revert or "clean up" another session's uncommitted work.**
   `git checkout -- <file>` on a file another session is editing destroys its
   live edits. It happened once. If a file you need is dirty and not yours, ask
   its owner, or the user.
2. **If you offer to wait, wait.** If you tell another session "I'll hold X until
   you answer", do not do X until they answer, even if it looks safe.
3. **Respect file ownership while sessions run in parallel.** Until the handover, the session *"Make the
   chapter view read the taxonomy chapter tag"* owned the files below. That session is gone, and the
   new team owns everything. Keep the rule for any parallel work you set up: name an owner per file set.
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
5. **Machine load: one heavy job at a time on a laptop.** The development laptop overloaded and shut
   down twice, the second time with four agent workflows running. A full pytest run, a Flutter test run,
   `flutter build web` and a Cloud Build upload are each heavy. Never edit files in a checkout while its
   full suite runs: source-scan tests read files at run time and fail falsely. Never rebuild
   `frontend/build/web` while pytest runs: `api/main.py` mounts it at import.
6. **A test failure is a filter, not a finding.** When a gate fails, report
   everything it measured, including what improved, not just the pairs that
   fell. A partial report once read as a regression that was a net gain.
7. **Read the whole output.** A merge that refused (missing chapter tags) looked
   like success because the output was piped through `grep`. Use `tail`, never a
   filter, on a command whose failure you have to see.

## 4. Before you commit: the gates

    PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 python -m pytest tests -q -p no:cacheprovider
    cd frontend && flutter analyze --no-fatal-infos && flutter test --exclude-tags live-backend -j 1

`python` is your venv's, with the project's PyMuPDF; on the original laptop that is
`D:/AcademicOS-venv/Scripts/python.exe`. Paste the counts into the PR (passed / skipped / xfailed, 0
failed; the analyzer's infos, 7 on 2026-09-28). A clone without the gitignored `academicos-data/`
extras (`answer_keys.db`, `parse/`) skips the tests that need them. That is expected, but say so.

The checks most likely to catch a new contributor out:

- **Every route needs a policy row.** `src/academicos/api/route_policy.py` holds
  one table of who may call each (method, path). `tests/test_role_gates.py` fails
  on any served route missing from it, and on any row whose level does not match
  the route's real dependency chain. `tests/test_route_inventory.py` pins the
  route count (168 at the time of writing): a new route bumps it in the same
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
    tag_question_bank.py --topics <cbse-cbe, cbse-sqp and ncert-exemplar questions.json>
                                          # taxonomy tags, INTO THE SOURCES (see below)
    merge_question_banks.py               # composes the served bank + the APK copy + the exclusions
    enrich_question_bank.py               # relinks board schemes, fills asset fields, stamps the verifier
    bank_health.py                        # regenerates docs/bank-health.md + bank_health.json

- **Tag the sources, never the served bank.** The merge rebuilds every non-board record
  from the source banks, so a tag written into the served bank is lost at the next merge.
  Until 2026-09-28 the list above said `--topics <served bank>`, and the served bank held
  tags its sources did not: the fidelity rebuild's merge dropped 36 SQP records' tags
  until the sources were tagged. The tagger keeps the Exemplar book-map tags pinned.
- **`enrich_question_bank.py` needs `answer_keys.db` and the parse trees**
  (`academicos-data/answer_keys.db`, `academicos-data/parse/`, 683 MB). Both are gitignored
  and exist only in the main checkout (`../AcademicOS/academicos-data/`). For the 2026-09-28
  rebuild the db was copied into this worktree and `parse` linked to the main checkout's
  (a Windows junction), read-only; a worktree without them cannot run the relink.
- **Every fidelity rule** lives in `corpus/fidelity.py` (repairs where certain, refusals
  where not) and is counted by `merge_question_banks.py --check`. Read what a new rule
  refuses before you keep it: the first draft of the 2026-09-28 rules refused five
  answerable questions, and a cosmetic repair changed what the value-point splitter reads.

- The 2026-09 rebuilds of Tasks 121-126 did **not** re-run `enrich_question_bank.py` (the
  2026-09-28 fidelity rebuild did, after the merge):
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

1. Open a pull request into `master` (`CONTRIBUTING.md` §4) with the gate counts and the evidence.
2. The maintainer reviews it with `/review-pr <n>` (`.claude/commands/review-pr.md`). That runs both
   gates on the merge result, re-runs a claim from the description, and merges with a merge commit, or
   requests changes.
3. The maintainer moves `release/v1` to `master` (`git push origin origin/master:release/v1`).
4. CI deploys from `master`. **Until 2026-10-01 CI cannot run** (Actions minutes
   exhausted), so the maintainer follows **`docs/deploy-by-hand.md`** and does all four of its
   verification checks. The owner has authorised hand deploys when both suites
   are green. Once CI runs again, every merge to `master` deploys.
5. Record the deploy in that file's live-history table.

## 7. Evidence

The scorecard's rule is the PRD's: *verified* means run with real data through
the running system, with the output inspected. In practice:

- Quote the command and its output. A count you did not measure is not a count.
- Verify the **live** commit (`/health`), not your branch. A stale `build/web` has
  shipped before: rebuild the web bundle, and compare the `main.dart.<hash>.js`
  byte counts (`docs/deploy-by-hand.md` §6).
- A hand-check sample (answer keys, chapter maps, marking splits) is committed as
  a fixture with its verdicts, so the next change is measured against it.
- An audit is re-run by a fresh reader against the live system and recorded in
  the scorecard's audit log. It is never edited to fit a result.

## 8. Open items

`HANDOVER.md` section 8 lists the open branches and the planned streams.
`docs/audits/2026-09-27-8db6636.md` lists 35 numbered defects with reproductions. The v3 gaps are in
`HANDOVER.md` section 6. Two standing decisions from the product owner:

- **Bank rebuild authorised (2026-09-27)** for the content-fidelity work, and used on 2026-09-28
  (5,429 -> 5,319 served; floors lowered with the per-record diff in `tests/test_catalog_chapters.py`).
  The rule stands: lower a chapter floor only when the bank serves fewer questions that are all
  answerable, with the reason in the commit.
- **Social Science, English, Hindi and grades 1-5** need source material that is not in the repo yet
  (NCERT textbooks and other sources, `REQUIREMENTS.md` QB-4). This is the largest content gap.

## 9. Commits

Match the history: `fix(area): a sentence that says what is now true`, then a
body that says why, what was measured before and after, and anything left
undone. End with the co-author line your session's instructions give. Commit and
push only what you were asked to, and never skip hooks.
