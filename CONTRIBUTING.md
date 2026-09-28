# Contributing

AcademicOS takes every change as a **pull request into `master`**, from people and from Claude Code agents
alike. `master` is what is live. The maintainer reviews each PR, runs the gates on it, merges it and
deploys it. This page is the whole process. The engineering rules it relies on (the gates, the question-bank
pipeline, evidence) are in [`docs/agent-workflow.md`](docs/agent-workflow.md): read both before your first PR.

## Who does what

| Who | Does | Never |
|---|---|---|
| **Maintainer**: @varshinicb1, reviewing with Claude Code (`/review-pr <n>`) | reviews and merges PRs, deploys, runs the audits, owns the live release and its secrets | merges a PR whose gates it has not seen pass |
| **Collaborators** (@bahumanyarg11, and the agents they run) | pick a task, branch, build, test, open a PR, answer review | push to `master` or `release/v1`; merge or approve their own PR; deploy |

**This is a rule, not a lock.** Branch protection needs GitHub Pro on a private repository, so GitHub will
not stop a push to `master`. Once CI minutes return (2026-10-01) a push to `master` **deploys to
production**, so a stray push is a release. If you push to `master` by mistake, say so in the PR or an issue
at once. Do not force-push to fix it.

## 1. Before you start

1. **Set up a machine**: [`HANDOVER.md`](HANDOVER.md) §3. Read `HANDOVER.md`, then
   [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md), then [`docs/agent-workflow.md`](docs/agent-workflow.md).
2. **Pick one task**: an open issue, a defect from the latest audit in [`docs/audits/`](docs/audits/), or
   the next step of the current milestone ([`HANDOVER.md`](HANDOVER.md) §7, [`docs/plans/`](docs/plans/)).
3. **Claim it before you build it**, so two agents never build the same thing:
   - check `gh pr list` and `gh issue list` first;
   - then assign yourself the issue, or open a **draft PR** with the task in its title as soon as your
     branch has a first commit.
4. **Ask before a product decision.** If the requirement leaves a choice open (a plan's "open questions",
   `docs/PRD.md` §12), ask in the issue or the draft PR. Do not decide it in code.

## 2. Branch

```bash
git fetch origin
git switch -c <type>/<topic> origin/master      # type: feat, fix, docs, test, data, chore
```

- **One task per branch and per PR.** A question-bank rebuild is always its own PR.
- **Stage by path** (`git add <files>`), never `git add -A` or `commit -a`. Every checkout shows the Flutter
  `generated_plugin_registrant.*`, `generated_plugins.cmake` and `GeneratedPluginRegistrant.swift` as
  modified. They are build noise: never commit them.
- **Never commit a secret.** Keys go in `config/secrets.env` (gitignored) or Secret Manager. Never put one
  in `config/config.toml`. No test or fixture holds a real key, token or password.
- **Never use a bare `git stash`**; set work aside with a WIP commit.
- **If `master` moves**, merge it into your branch (`git merge origin/master`). Do not rebase a branch you
  have pushed: review comments are anchored to its commits.

## 3. Build and test

- **Tests first.** A behaviour change comes with the test that shows it.
- **Run both gates before you mark the PR ready.** The commands and the checks new contributors trip on
  are in [`docs/agent-workflow.md`](docs/agent-workflow.md) §4:

  ```bash
  PYTHONPATH=$PWD/src PYTHONIOENCODING=utf-8 python -m pytest tests -q -p no:cacheprovider
  cd frontend && flutter analyze --no-fatal-infos && flutter test --exclude-tags live-backend -j 1
  ```

  Run them one at a time. Each is heavy, and the development laptops have shut down under load.
- **Areas that need the maintainer's explicit agreement in the PR**:
  - the served question bank or a chapter floor (`agent-workflow.md` §5);
  - a route, a role gate (`api/route_policy.py`), auth, invites or school scoping;
  - student data, consent or the audit log (tick the boxes in [`docs/compliance.md`](docs/compliance.md));
  - deploy files (`deploy/`, `Dockerfile`, `firebase.json`, `.github/workflows/`);
  - a request or response shape the web client uses (`tests/test_frontend_backend_contract.py`).

  Say which of these your PR touches. The PR template asks.

## 4. Open the pull request

```bash
git push -u origin <type>/<topic>
gh pr create --draft --base master --title "<type>(<area>): what is now true"   # the template opens
gh pr ready          # once both gates pass and the template is filled in
```

- **Fill in the template.** The reviewer reads the PR, not your session. Paste the gate counts and the
  commands behind every number you claim.
- **Title like a commit**: `fix(area): a sentence that says what is now true` (`agent-workflow.md` §9).
- **Keep it reviewable.** Aim for a few hundred changed lines, excluding generated data. Split larger work
  into PRs that each leave `master` green.
- **Say what you left undone.** A PR that says "the Settings half is not done" is mergeable. One that hides
  it is not.

## 5. Review and merge (maintainer)

The maintainer's Claude runs `/review-pr <n>` ([`.claude/commands/review-pr.md`](.claude/commands/review-pr.md)).
It:
1. reads the PR, its template and the whole diff;
2. checks the result of merging it into current `master` out in a separate worktree;
3. runs both gates there, one at a time;
4. re-runs at least one of the PR's own evidence claims;
5. then either **approves and merges** (a merge commit, never squash, so history keeps the author's
   commits) or **requests changes** with the specific reason.

A PR is merged only when:
- both gates pass on the merge result, with 0 failures and the known 7 analyzer infos;
- nothing in the diff breaks a rule in `docs/agent-workflow.md` or this page;
- every area in §3's list that it touches has the maintainer's explicit agreement;
- its claims hold when re-run.

After a merge, the maintainer keeps `release/v1` equal to `master` and deploys by hand
([`docs/deploy-by-hand.md`](docs/deploy-by-hand.md)) until CI can run. Only a deployed, audited change moves
the scorecard.

## 6. Notes for Claude Code agents

- `CLAUDE.md` loads automatically and points here. It also points to `docs/agent-workflow.md`, whose rules
  exist because breaking them cost real work once.
- Work in your own clone or worktree. Never edit, reset or clean another session's checkout, and never
  sweep another session's uncommitted work.
- End commits with the co-author line your session's instructions give. Never skip hooks.
- Do not merge or approve PRs, and do not deploy, unless you are the maintainer's session.
- Put your evidence in the PR description, not only in your chat.
