# Instructions for GitHub Copilot (chat, code review and the coding agent)

**The full rules are in [`AGENTS.md`](../AGENTS.md) at the repository root. Read it before changing
anything; where this file and `AGENTS.md` differ, `AGENTS.md` wins.** These are the rules that matter most:

1. **Every change is a pull request into `master`.**
   - Never push to `master`: CI deploys every push to production.
   - Never merge or approve your own PR, and never deploy.
2. **Work from a branch** (`<type>/<topic>` off current `origin/master`) and **open the PR as a draft**.
   - Fill in `.github/pull_request_template.md`, with the evidence (commands and their output).
   - Stage files by path. Never commit `generated_plugin*` files.
3. **No secret anywhere:** repository, PR, issue, log or test fixture. Refer to secrets by their Secret
   Manager names.
4. **The live system is read-only for you.** Run unauthenticated checks only, and never create accounts or
   enter credentials.
5. **Scope every query by the signed-in user's `school_id`.** Student data never leaves the school's
   scope. Read `docs/compliance.md` before touching it.
6. **Every route** needs a row in `src/academicos/api/route_policy.py` and an entry in
   `tests/test_route_inventory.py`. Regenerate `contract/` when a schema changes.
7. **Write the failing test first for a bug.** Never skip or weaken a test to get green. Both gates must
   pass:
   - backend: `pytest tests -q -p no:cacheprovider` (Python 3.12);
   - frontend: `flutter analyze` and `flutter test --exclude-tags live-backend`.
8. **Frontend:**
   - no swallowed errors (show `serverErrorMessage(e)`);
   - no emoji or raw hex in `frontend/lib`;
   - strings go through `tr()`;
   - check every screen at 375-390 px and at desktop width.
9. **Never invent content** (chapter names, marks, difficulty). The served question bank changes only
   through the pipeline in `docs/agent-workflow.md` §5.
10. **Numbers are measured, with the command quoted, or labelled "estimated".**
11. **The company is VidyuthLabs, one word.** Contracts, signatures, pay terms and school agreements never
    go in this repository.
12. **`backend/` is an abandoned rewrite.** Work in `src/academicos/` and `frontend/`.

Requirements and their IDs: `docs/REQUIREMENTS.md`. Current state and plan:
`docs/handover/2026-10-07-developer-handover.md`.
