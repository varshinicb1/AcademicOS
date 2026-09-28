---
description: Review a pull request as the maintainer's reviewer, run the gates on the merge result, then merge it or request changes
argument-hint: <PR number>
---

Review pull request #$ARGUMENTS of `varshinicb1/AcademicOS` as the maintainer's reviewer. The process is
`CONTRIBUTING.md` §5. The rules the diff is held to are `CONTRIBUTING.md` §2-§3 and `docs/agent-workflow.md`
§3-§5. Read both files first if they are not already in context.

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
- **Tests.** A behaviour change has a test that fails without it. An `xfail` is `strict=True` and says how to
  un-xfail it. No floor or count was lowered to make a test pass (`agent-workflow.md` §3.3).
- **Routes.** Every new route has a `route_policy.py` row and a `test_route_inventory.py` count bump. Request
  models forbid unknown fields. The web client contract still holds.
- **The question bank.** It was changed only through the pipeline (`agent-workflow.md` §5), in its own PR,
  with the per-record diff.
- **Student data.** `docs/compliance.md` boxes, school scoping, and the audit log on PII reads.
- **Hygiene.** No `generated_plugin*` or `GeneratedPluginRegistrant.swift`. No secret: grep the diff for
  `key`, `token`, `password` and `secret`. No emoji or raw hex in `frontend/lib`. No stray debug output.

## 5. Run the gates in the review worktree, one at a time

Never edit files in this worktree while a suite runs.

```bash
PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 <venv python> -m pytest tests -q -p no:cacheprovider
cd frontend && flutter pub get && flutter analyze --no-fatal-infos && flutter test --exclude-tags live-backend -j 1
```

The venv python on the maintainer's laptop is `D:/AcademicOS-venv/Scripts/python.exe`. Record passed,
skipped, xfailed and failed, and the analyzer's count. The merge bar is **0 failed** and only the known
infos, which were 7 on 2026-09-28. Compare the skip count with `master`'s: a jump means tests stopped
running.

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
  `gh pr review --comment` instead of `--approve`. Always a merge commit, never squash or rebase. Never
  `--admin`.
- **Request changes** otherwise: `gh pr review $ARGUMENTS --request-changes --body-file <review.md>`. For each
  blocking finding, say what would make the PR mergeable. Do not fix the author's branch yourself unless the
  user asks.

## 8. After a merge

```bash
git fetch origin && git push origin origin/master:release/v1     # release/v1 follows master
```

**A merge is a deploy.** Since 2026-09-28 CI runs again, and a merge that touches a shipped path (the
`paths:` list in `.github/workflows/deploy-gcp.yml`) deploys the backend by itself. Merge only what is ready
to ship. Then:
- watch the run (`gh run list --limit 3`) and check that `/health` reports the merge commit;
- for a PR that changes the stored schema, dry-run its migration on a copy of the live snapshot before
  merging;
- deploy the web by hand, steps 4-6 of `docs/deploy-by-hand.md`, while the workflow's Flutter is unpinned.
  Do it when the user has asked for it or authorised it.
- Record the deploy in that file's live history.

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
