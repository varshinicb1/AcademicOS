# GEMINI.md

Context for Gemini CLI and other Gemini-based agents in this repository.

**Read [`AGENTS.md`](AGENTS.md) in full before changing anything. It is the rulebook for every contributor,
and where this file differs, `AGENTS.md` wins.** Then read `docs/REQUIREMENTS.md` (what to build) and
`docs/handover/2026-10-07-developer-handover.md` (what exists, and the current plan).

The rules that matter most:

1. **Every change is a pull request into `master`.**
   - Never push to `master`: CI deploys every push to production.
   - Never merge or approve your own PR, and never deploy.
2. **Branch from current `origin/master`** as `<type>/<topic>`, open a draft PR, and fill in the template
   with evidence. Stage files by path.
3. **No secret anywhere:** repository, PR, issue, log or test fixture.
4. **Live checks are unauthenticated and read-only.** Never create accounts or enter credentials on the
   live site.
5. **Every query is scoped by the signed-in user's `school_id`.** Student data never leaves the school's
   scope (`docs/compliance.md`).
6. **New routes** need `api/route_policy.py`, `tests/test_route_inventory.py` and a regenerated
   `contract/`.
7. **A bug fix starts with a failing test.** Never skip or weaken a test. Both gates must pass (backend
   `pytest`, frontend `flutter analyze` and `flutter test`).
8. **Never invent content.** The question bank changes only through its pipeline
   (`docs/agent-workflow.md` §5).
9. **Numbers are measured, with the command quoted, or labelled "estimated".**
10. **The company is VidyuthLabs, one word.** No contracts, signatures, pay terms or school agreements in
    this repository.

Run one heavy job at a time (a full test run, a web build, an image build). Work only in
`src/academicos/` and `frontend/`; `backend/` is an abandoned rewrite.
