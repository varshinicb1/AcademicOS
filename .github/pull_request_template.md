<!--
Read AGENTS.md and CONTRIBUTING.md first. One task per PR. Open it as a draft, and mark it ready only when both gates pass.
The reviewer reads this description, not your session: put the evidence here.
-->

## What is now true

<!-- One or two sentences: what the product or the code does after this PR that it did not before. -->

## Why

<!--
The requirement ID (docs/REQUIREMENTS.md, e.g. SCH-4), the plan step (R-A1 in the developer handover),
the audit defect (Dxx in docs/audits/) or the issue (#n). A PR with none of these needs a sentence on why it exists.
-->

## Evidence

<!--
The commands you ran and what came back: counts, ids, before and after. A count you did not measure is not a count;
label anything modelled or extrapolated "estimated".
For a UI change, add a screenshot at 375-390 px and at desktop width.
-->

## Gates

- [ ] `pytest tests -q -p no:cacheprovider -p no:warnings` (Python 3.12): ___ passed / ___ skipped / ___ xfailed, 0 failed
- [ ] `flutter analyze`: No issues found
- [ ] `flutter test --exclude-tags live-backend`: ___ passed, 0 failed
- [ ] Not run, because: <!-- e.g. docs only -->

## Touches an area that needs the maintainer's agreement

- [ ] The served question bank (`academicos-data/syllabus/questions.json`) or a chapter floor
- [ ] A route, a role gate (`api/route_policy.py`), auth, invites or school scoping
- [ ] Student data, consent or the audit log (the `docs/compliance.md` boxes are checked)
- [ ] A storage backend, a schema or a migration
- [ ] Deploy files (`deploy/`, `Dockerfile`, `firebase.json`, `.github/workflows/`)
- [ ] A request or response shape the web client uses (`tests/test_frontend_backend_contract.py` run)
- [ ] The pilot agreement text (`VERSION` bumped in `operations/pilot_agreement.py`)
- [ ] None of these

## Checklist

- [ ] Branched from current `master`; if `master` moved, I merged it in (no rebase after pushing)
- [ ] Staged by path: no `generated_plugin*` or `GeneratedPluginRegistrant.swift`, no secrets
- [ ] A new route has its `route_policy.py` row and its `test_route_inventory.py` entry; `contract/` regenerated if a schema changed
- [ ] Tests added or changed for the behaviour; a bug fix has a test that fails without it; no test skipped or weakened
- [ ] User-facing strings go through `tr()`; no emoji or raw hex in `frontend/lib`; errors say what to do next
- [ ] Docs updated where a count, a route or a rule changed
- [ ] No contracts, signatures, pay terms, school agreements or other confidential material in the diff

## Left undone

<!-- Anything this PR does not do that a reader might assume it does. "Nothing" is an answer. -->
