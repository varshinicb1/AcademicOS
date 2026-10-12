---
description: Review a pull request as the maintainer's reviewer, run the gates on the merge result, then merge it or request changes
argument-hint: <PR number>
---

Review pull request #$ARGUMENTS of `varshinicb1/AcademicOS` as the maintainer's reviewer. The process is
`CONTRIBUTING.md` §5. The rules the diff is held to are [`AGENTS.md`](../../AGENTS.md) (all of it, with its
definition of done in §9) and `docs/agent-workflow.md` §3-§5. Read them first if they are not already in
context. Only the maintainer's session runs this command.

**One heavy job at a time.** Before step 5, make sure no other full test run, Flutter run, web build or audit
is running on this machine. If one is, wait for it.

## 1. Read the PR

```bash
gh pr view $ARGUMENTS --json number,title,author,isDraft,baseRefName,headRefName,mergeable,additions,deletions,files,commits,body
gh pr diff $ARGUMENTS
```

Read the description and the **whole** diff, not a sample.

## 2. Stop early when the PR is not ready

Stop and comment (`gh pr comment $ARGUMENTS --body ...`), without running anything, when any of these hold:
- it is a draft;
- its base is not `master`;
- the template's gates or evidence are empty;
- it touches an area in `CONTRIBUTING.md` §3's list without the maintainer's agreement in the thread.

For the last case, ask the user in chat. Do not decide it yourself.

## 3. Check out the merge result

Test what `master` will become, not the branch alone:

```bash
git fetch origin master "pull/$ARGUMENTS/head:review/pr-$ARGUMENTS"
git worktree add "../AcademicOS-review-$ARGUMENTS" "review/pr-$ARGUMENTS"
cd "../AcademicOS-review-$ARGUMENTS"
git merge --no-ff --no-edit origin/master          # local only; never push this
```

If the merge conflicts, abort it. Request changes, asking the author to merge `master` into the branch.

## 4. Review the diff against the rules

Report each finding with `file:line`. Look for:
- **Correctness.** Does the code do what the description says? Trace the changed paths. Check the edge
  cases the tests skip.
- **Scope.** The PR names a requirement ID, plan step, defect or issue, and does one task. It does not
  rebuild something the developer handover lists as existing.
- **Tests.** A behaviour change has a test that fails without it. An `xfail` is `strict=True` and says how to
  un-xfail it. No floor or count was lowered to make a test pass (`agent-workflow.md` §3.3).
- **Routes.** Every new route has a `route_policy.py` row and a `test_route_inventory.py` entry. Request
  models forbid unknown fields. `contract/` is regenerated when a schema changed, and the web client
  contract still holds.
- **Storage.** No SQL that only SQLite accepts (`INSERT OR IGNORE`/`OR REPLACE`, `rowid`, `AUTOINCREMENT`,
  `instr`, `PRAGMA`) in new code. No check-then-act that assumes one instance (`AGENTS.md` §5). A remote
  table only through `postgres_kv.durable_table`.
- **The question bank.** It was changed only through the pipeline (`agent-workflow.md` §5), in its own PR,
  with the per-record diff.
- **Student data.** `docs/compliance.md` boxes, school scoping, and the audit log on PII reads.
- **Hygiene.** No `generated_plugin*` or `GeneratedPluginRegistrant.swift`. No secret: grep the diff for
  `key`, `token`, `password` and `secret`. No emoji or raw hex in `frontend/lib`. No stray debug output. No
  contracts, signatures, pay terms or school agreements. The company is written VidyuthLabs.
- **Evidence.** Every number in the description is measured, with its command, or labelled "estimated".

## 5. Run the gates in the review worktree, one at a time

Never edit files in this worktree while a suite runs.

```bash
PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 <venv python> -m pytest tests -q -p no:cacheprovider -p no:warnings
cd frontend && flutter pub get && flutter analyze && flutter test --exclude-tags live-backend
```

`<venv python>` is a Python 3.12 venv with the project installed; a global 3.14 fails the OpenAPI contract
test even on `master`. A docs-only PR (no file under `src/`, `tests/`, `frontend/`, `contract/`, `deploy/`,
`scripts/` or `academicos-data/`) may skip the suites; say so in the review. Record passed, skipped, xfailed
and failed, and the analyzer's output. The merge bar is **0 failed** and "No issues found". Compare the
skip count with `master`'s: a jump means tests stopped running.

## 6. Re-run the PR's own evidence

Re-run at least one claim from the description (a count, a request, a screen) and compare it. A claim that
does not reproduce blocks the merge.

## 7. Decide and act

Write the review body with:
- what the PR does;
- the gate counts from step 5;
- the claim re-run in step 6 and its result;
- every finding, blocking or not.

- **Merge**, only if every check passed:

  ```bash
  gh pr review $ARGUMENTS --approve --body-file <review.md>
  gh pr merge $ARGUMENTS --merge --delete-branch --match-head-commit <full 40-char head SHA you reviewed> \
    --subject "Merge #$ARGUMENTS <branch>: <what is now true>" --body-file <merge-body.md>
  ```

  GitHub refuses an approval of one's own PR. For a PR opened from the maintainer's account, use
  `gh pr review --comment` instead of `--approve`. A collaborator's PR is merged with `--merge` (or
  `--rebase` for a clean linear series), never `--squash`, so their commits and authorship stay in the
  history. The maintainer's own single-purpose PR may use `--squash`. Never `--admin`.
- **Request changes** otherwise: `gh pr review $ARGUMENTS --request-changes --body-file <review.md>`. For each
  blocking finding, say what would make the PR mergeable. Do not fix the author's branch yourself unless the
  user asks.

## 8. After a merge

`release/v1` is retired (2026-10-01): do not move it.

**A merge is a deploy.** A merge that touches a shipped path (the `paths:` list in
`.github/workflows/deploy-gcp.yml`) deploys the backend and the web by itself. Runs queue rather than
cancel. Merge only what is ready to ship. Then:
- watch the run (`gh run list --limit 3`) and check that `/health` reports the merge commit;
- for a PR that changes the stored schema, dry-run its migration on a copy of the live data before
  merging;
- after the run, do the unauthenticated checks in `docs/deploy-by-hand.md` section 6. Never create an
  account or sign in on the live site.
- **Never deploy by hand while CI works**: it races CI. If a CI job cannot run, deploy by that runbook
  only when the user asks for it, and record the hand deploy there.

## 9. Clean up and report

```bash
cd - && git worktree remove "../AcademicOS-review-$ARGUMENTS" && git branch -D "review/pr-$ARGUMENTS"
```

Tell the user:
- the verdict and the PR link;
- the gate counts;
- what was re-run and whether it held;
- anything left for a later PR;
- whether the change is deployed. It moves the scorecard only once it is deployed and audited.
