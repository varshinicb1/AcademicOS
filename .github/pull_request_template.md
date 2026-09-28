<!--
Read CONTRIBUTING.md first. One task per PR. Open it as a draft, and mark it ready only when both gates pass.
The reviewer reads this description, not your session: put the evidence here.
-->

## What is now true

<!-- One or two sentences: what the product or the code does after this PR that it did not before. -->

## Why

<!-- The requirement ID (docs/REQUIREMENTS.md), audit defect (Dxx in docs/audits/), issue (#n) or milestone step (M1.1, ...). -->

## Evidence

<!--
The commands you ran and what came back: counts, ids, before and after. A count you did not measure is not a count.
For a UI change, add a screenshot at 375 px and at desktop width.
-->

## Gates

- [ ] `pytest tests -q -p no:cacheprovider`: ___ passed / ___ skipped / ___ xfailed, 0 failed
- [ ] `flutter analyze --no-fatal-infos`: ___ infos (7 expected), 0 warnings, 0 errors
- [ ] `flutter test --exclude-tags live-backend -j 1`: ___ passed, 0 failed
- [ ] Not run, because: <!-- e.g. docs only -->

## Touches an area that needs the maintainer's agreement

- [ ] The served question bank (`academicos-data/syllabus/questions.json`) or a chapter floor
- [ ] A route, a role gate (`api/route_policy.py`), auth, invites or school scoping
- [ ] Student data, consent or the audit log (the `docs/compliance.md` boxes are checked)
- [ ] Deploy files (`deploy/`, `Dockerfile`, `firebase.json`, `.github/workflows/`)
- [ ] A request or response shape the web client uses (`tests/test_frontend_backend_contract.py` run)
- [ ] None of these

## Checklist

- [ ] Branched from current `master`; if `master` moved, I merged it in (no rebase after pushing)
- [ ] Staged by path: no `generated_plugin*` or `GeneratedPluginRegistrant.swift`, no secrets
- [ ] Tests added or changed for the behaviour
- [ ] Docs updated where a count, a route or a rule changed

## Left undone

<!-- Anything this PR does not do that a reader might assume it does. "Nothing" is an answer. -->
