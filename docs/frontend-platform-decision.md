# Frontend platform decision — stay on Flutter, or move the web client

**Status:** recommendation, not a decision. Prepared 2026-09-16.
**Decision owner:** whoever owns the frontend roadmap.

---

## 1. What is actually being asked

Three requirements, in the requester's own priority order:

1. Professional dashboards, comparable to what global product companies ship.
2. Lower risk than the status quo.
3. **Most importantly**: automated testing of the **GCP-deployed** app, with
   **visual verification**.

Requirement 3 is not a preference about frameworks. It is a hard technical
constraint, and it decides this question on its own.

---

## 2. The constraint, with evidence

Flutter web renders the entire application into a single `<canvas>` via
CanvasKit. There is no DOM.

This was measured, not assumed, during the only interactive verification pass
this project has ever run (2026-09-14, recorded in
[`TRANSCRIPT_REQUIREMENTS_MATRIX.md`](TRANSCRIPT_REQUIREMENTS_MATRIX.md)):

> "this Flutter build renders everything — including text fields and buttons — to
> a single `<canvas>` via CanvasKit with no real DOM elements
> (`flt-glass-pane`/`flt-text-editing-host` are the only real non-canvas hooks).
> The browser automation's ordinary click action didn't reliably trigger
> Flutter's own pointer/focus handling […] became unreliable for
> smaller/edge-positioned targets […] consistent across retries, not a one-off flake."

Consequences, all of which follow directly:

| What | Status under CanvasKit |
|---|---|
Ordinary Playwright/Selenium clicks | Unreliable — a hand-dispatched `PointerEvent` workaround is required, and it still fails on small targets |
`data-testid` selectors | **Impossible.** There is no element to attach one to |
Accessibility tree | Effectively absent — screen readers cannot read the app |
Visual regression (screenshot diffing) | Possible, but every diff is a whole-canvas diff: a moved button reports as a full-page failure, because nothing knows what a "button" is |
Text selection, browser find, copy | Do not work |
First load | `main.dart.js` 5.17 MB + `canvaskit.wasm` 7.23 MB; 50.7 MB total SPA, 5.0 MB gzipped critical path |

Since requirement 3 is *automated visual verification of the deployed app*, and
**`data-testid` is the mechanism that makes it possible**, CanvasKit is not a
suboptimal choice for this requirement — it is a disqualifying one. The design
system therefore mandates `data-testid` on every component (§7 of
[`design-system.md`](design-system.md)), which means the current renderer cannot
satisfy its own design system.

---

## 3. The fact that makes this cheap

**The Web sub-product is a thin client.**

From [`PRODUCTS_AND_RELEASES.md`](PRODUCTS_AND_RELEASES.md): Web talks to a
backend over HTTP for every action. The offline engine — the actual intellectual
property, with the ported paper-selection and evaluation algorithms — is used by
the **Mobile** sub-product only.

So a web rewrite duplicates **no business logic**. It rebuilds presentation and
API calls. That is the single most important input to the cost estimate, and it
is unusually favourable.

---

## 4. Options

| Option | Automated visual verification | Dashboard ecosystem | Cost | Risk |
|---|---|---|---|---|
**A. Stay on Flutter web** | ✗ cannot satisfy the requirement | Weak. No React-equivalent of TanStack Table / AG Grid / Recharts / Visx | 0 | Status quo. Requirement 3 permanently unmet. |
**B. Flutter web + DOM-injection hacks** | ~ partial, brittle | Weak | Low | Carrying a bespoke hack forever; breaks on Flutter upgrades. Not viable. |
**C. React/Next.js for Web; keep Flutter for Mobile** | ✓ Playwright + `data-testid` + screenshot diffing, all standard | Best in class | **High but bounded** — ~20 thin screens, no logic | Medium — two codebases, two skill sets |
**D. Rewrite everything (incl. Mobile) off Flutter** | ✓ | ✓ | Very high | **High — discards a working offline engine for no gain** |
**E. Server-rendered admin (Django/Rails)** | ✓ | Moderate | High — different language | Rewrites the backend team's world for a frontend problem |

### Why not A
It fails the stated priority, permanently, and no amount of engineering effort
inside Flutter changes that — the canvas is the design, not a bug.

### Why not B
Every Flutter release reshuffles the canvas internals. A bespoke DOM-injection
harness is a permanent maintenance tax with a known expiry date.

### Why not D
The offline engine is the differentiator for low-connectivity schools. Flutter is
genuinely good at it. Rewriting it to satisfy a *web* testing requirement would
be paying twice to lose the best asset.

### Why not E
The backend is Python/FastAPI and is the best-verified layer here. Introducing a
second server language to fix a client-rendering problem is disproportionate.

---

## 5. Recommendation: option C

**Move the Web sub-product to React + TypeScript. Keep Flutter for Mobile.**

The stack:

| Concern | Choice | Why |
|---|---|---|
Framework | **Next.js** (App Router) | Routing, code-splitting, and a path to SSR for the login/legal pages |
Language | **TypeScript**, strict | — |
Styling | **Tailwind** + the tokens in `design-system.md` | Tokens map 1:1 to `@theme` variables |
Primitives | **shadcn/ui** (Radix), restyled to our tokens | Accessible by default; we own the source rather than depending on a themed black box |
Data | **TanStack Query** | Cache, retry, and background refetch that the 401-recovery path needs |
Tables | **TanStack Table** | The admin console is 6 tabs of dense, sortable tables |
Charts | **Recharts** | Coverage/pace/variance reporting |
Forms | **React Hook Form + Zod** | Zod also validates API responses at the boundary |
API types | **generated from the backend OpenAPI schema** | see below |
E2E + visual | **Playwright** with `toHaveScreenshot()` | The whole point |

### The unplanned but significant bonus

Generating the API client from the backend's OpenAPI spec (`openapi-typescript`)
turns the biggest defect found this session into a **compile error**. Today, 46
of 126 frontend calls target routes that do not exist, and nothing detects it —
they surface as runtime 404s the moment someone wires a screen up. With a
generated client, that class of bug cannot be written.

That is a structural fix for a problem the ratchet test only *pins*.

### Cost, honestly

~20 thin screens × (layout + API call + local state). With a component library
and generated types, this is **4–8 engineer-weeks for feature parity**, not a
quarter. It is real work. It is also the cheapest version of this rewrite the
architecture allows, because there is no logic to port.

### Risk, honestly

Two codebases and two skill sets. Mitigated by: the design tokens are shared;
the API contract is one artifact; and Mobile changes rarely, since its feature
set is already frozen behind `OfflineUnsupportedException` for anything needing
a network.

---

## 6. Migration plan

> **Status 2026-09-17 — steps 1 and 2 are done.** `contract/openapi.json` and the
> generated `contract/api-types.ts` are committed, with
> `tests/test_openapi_contract.py` failing CI if the schema changes without
> re-exporting. See [`../contract/README.md`](../contract/README.md).
>
> Step 2 landed the app shell and the primitive set under `web/` — Next 16,
> React 19, Tailwind 4, and no UI framework dependency. Every value resolves
> from `design/tokens.json` via a generated copy at `web/src/styles/tokens.css`
> (Turbopack refuses to import CSS from outside its project root), mapped into
> Tailwind with `@theme inline`. **Verified, not assumed:** `npm run build`
> emits `var()` references rather than literals, checked in the built bundle;
> `/gallery` renders every primitive in every state and is captured by headless
> Chrome. Steps 3-5 are not started.
>
> Two latent holes in `scripts/check_design_tokens.py` were found and fixed
> while doing this, both of which had been reporting OK:
> the glob `web/src/**/*.{ts,tsx,css}` matched **zero** files — pathlib has no
> brace expansion, so no line of the React client was ever read — and the skip
> list matched by substring, so adding `"out"` silently hid `layout.tsx` and
> `app_router.dart`. Each now has a ratchet test in
> `tests/test_design_tokens.py` (`test_every_scan_glob_matches_files`,
> `test_checker_fails_on_a_react_violation`).

1. **Freeze the contract first.** Generate the TypeScript client from the
   OpenAPI schema and commit it. Every subsequent step builds on types that
   cannot drift. — **done**
2. **Build the shell + design system** — side nav, page header, KPI tile, table,
   status pill, empty/loading/error states. No feature work. — **done**
   (`web/src/components/shell/`, `web/src/components/ui/`, `/gallery`; error
   states are the one item still outstanding, since they need the typed client
   from step 3 to be meaningful rather than decorative)
3. **Port by role, not by file**, in this order: Principal admin console
   (highest dashboard value, exercises the whole component set) → Teacher
   schedule → Student portal → Assessment review. Each port ships behind the
   same backend, so the two clients can coexist while a school is mid-migration.
4. **Stand up Playwright against the GCP release from day one** — not at the
   end. Add `toHaveScreenshot()` on the first screen that lands and let the
   baseline grow with the port.
5. **Retire the Flutter web target** only once parity is verified. Keep Mobile
   untouched throughout.

Nothing here requires a big bang, and no step blocks another team.

---

## 7. What I am not recommending

- Rewriting the **Mobile** sub-product. Flutter is the right tool there.
- Rewriting the **backend**. It is the most verified layer in the project.
- Any decision made before the **GCP release has actually run once**. Prove the
  deployment first; it is the prerequisite for "testing of the GCP-deployed app"
  meaning anything.

---

## 8. If the answer is "stay on Flutter"

That is a legitimate call — one codebase, one skill set, and Mobile is the
strategically important sub-product. But it must be made with the trade stated
plainly: **automated visual verification of the deployed web app will not be
achievable**, and the accessibility and payload problems stay. If that trade is
acceptable, the honest move is to drop requirement 3 for web rather than fund an
approach that cannot deliver it.
