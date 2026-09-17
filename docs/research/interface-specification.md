# The interface specification: minimal, complete, and defensible

**Status:** specification, ready to build against. Supersedes nothing; extends
[`ui-ux-principles.md`](ui-ux-principles.md) (which owns the adoption and
habit-formation research) and [`../design-system.md`](../design-system.md) (which
owns the tokens).
**Date:** 2026-09-17
**Covers:** every one of the 24 requirement rows in
[`../TRANSCRIPT_REQUIREMENTS_MATRIX.md`](../TRANSCRIPT_REQUIREMENTS_MATRIX.md),
plus the capability set in §8 that the matrix does not ask for and a school
genuinely needs.

---

## 1. What "award-winning minimal" has to mean here

There are two ways to read "minimal". One of them is a trap for this product.

**Minimal as fewer features** is wrong here, and the reason is in the matrix
itself: a principal has to see 22 chapters of coverage variance, reschedule a
disrupted week, and approve 404 extracted subtopics. A product that hides those
to look calm has not simplified the work, it has moved the work to paper.

**Minimal as fewer visible decisions** is the real target, and it is what
Linear, Stripe and Vercel actually do. The industry write-up on those three puts
it precisely:

> Generic SaaS UIs often confuse "information density" with "premium." Linear,
> Vercel, and Stripe are relatively sparse visually, but **interaction-dense** —
> every element you see is responsive to hover, focus, keyboard, and context.
> **The density is in the behavior, not the pixels.**
> — [Mantlr, May 2026](https://mantlr.com/blog/stripe-linear-vercel-premium-ui)

So the operating definition for this project:

> **Minimal means every visible element earns its place and every interaction
> is complete. It does not mean fewer capabilities.**

The corollary is the one that governs build order, and it is uncomfortable:

> Before adding a new element to a screen, audit the existing elements'
> interaction completeness. Hover states. Focus rings. Keyboard shortcuts.
> Loading skeletons. Transition timing. **If the existing elements don't have
> those, adding more elements will make the UI feel less premium, not more.**
> — same source

Concretely: **the app already has 26 screens.** Ship zero new screens until the
existing ones have complete microstates. A partially-built new screen on top of
incomplete ones makes the product worse, not bigger.

### The four craft decisions, measured

| Product | What it gets right | The number |
|---|---|---|
| Linear | Density without clutter, keyboard-first movement | **36px** row height, almost no chrome |
| Stripe | Metric discipline, nothing competes | **4** KPI cards above the fold, full stop |
| Grafana | Stays legible when crowded | 20+ panels, still readable |
| Vercel | Progressive disclosure done honestly | Summary up top, logs one click deep |
| — | from [ArtofStyleframe, Mar 2026](https://artofstyleframe.com/blog/dashboard-design-patterns-web-apps/) | |

We adopt the research's *ranges*, but the **values come from
`design/tokens.json`** and are not restated here, because a number written in
prose drifts from the number the code uses — which is exactly what happened
when this section was first drafted with 256px/36px/48px against the tokens'
`--layout-sidebarWidth: 240px`, `--compact-rowHeight: 32px` and
`--comfortable-rowHeight: 44px`. Tokens win; they already sit inside every
published range (240 is within 240–280, and 44 is the WCAG-recommended touch
target the tokens also carry as `--target-touch`).

| Decision | Token, not a number |
|---|---|
| Sidebar width | `--layout-sidebarWidth` / `--layout-sidebarCollapsedWidth` |
| Row height, dense vs comfortable | `--compact-rowHeight` / `--comfortable-rowHeight` |
| Cell padding | `--compact-cellPadding*` / `--comfortable-cellPadding*` |
| Content max width | `--layout-contentMaxWidth` |
| Touch and pointer targets | `--target-touch` / `--target-pointer` |
| Z-order | `--z-*` ladder — never an invented value |

And a **hard cap of 4 KPI tiles** on any single view. Stripe's discipline is
not conservatism, it is the finding that "a screen with twenty equal widgets is
a screen with none."

### The counter-position, stated fairly

Graphite, Grafana and Datadog are dense and beloved by professionals. The
research quoted above explicitly says *"Prioritize information density over
whitespace, dashboard users are power users who want data, not breathing room."*
Both are true, which is why **density is a user setting, not a philosophy** —
already in `design/tokens.json` as a toggle, and specified in §5.1.

---

## 2. The craft contract

Non-negotiable, applies to every control in the app. This is the checklist that
makes a screen "done" rather than "built".

### 2.1 Interaction completeness

Every interactive element ships all six states, designed:

| State | Requirement |
|---|---|
| Default | Token-driven, per `design/tokens.json` |
| Hover | Distinct and immediate (`--duration-fast`) |
| Focus | Visible, non-obscured, ≥3:1 against both states — see §7 |
| Active | Depressed; a 1px inset shadow, never a colour shift alone |
| Disabled | `--btn-disabledBg/Fg/Border`; **never** a disabled-looking-but-clickable control |
| Loading | Spinner **plus the label held in flow** so nothing shifts |

The last row is not decoration. The current `Button` reserves label width during
loading for exactly this reason, and it is why a paper-generate button does not
jump when it is clicked.

### 2.2 The four states of every data surface

Every list, table, chart and panel ships **loading, empty, error and partial** —
not just the happy path. The research is unanimous that empty states are where
users conclude the product is broken:

| Context | Wrong | Right (this product's copy) |
|---|---|---|
| No lessons today | "No data" | "No lessons scheduled today. Next: tomorrow, Science P2." |
| No coverage yet | "No data" | "Coverage appears once lessons are marked. [Mark today's lesson]" |
| Load failed | "An error occurred" | "Couldn't load the coverage report. [Retry] — nothing was lost." |
| First use | blank | "No book selected yet. [Choose this year's Science book]" |

**Errors must state whether data was lost.** `docs/notifications.md` and the
matrix both record a history of real incidents where a silent failure was read
as "nothing to show". Every error surface carries one of: *nothing was lost*,
*this is saved locally and will sync*, or *this did not save, here is the retry*.

### 2.3 Typography and numerals

- One family (already tokenised). 4–6 sizes maximum.
- **Tabular numerals are mandatory on every metric** — already enforced by
  `@utility tabular` and `scripts/check_design_tokens.py`.
- Units set lighter than values: `78.4` at `--text-3xl`, `%` at `--text-sm`.
- Consistent decimal precision per column: never `78.4` next to `78`.
- Dates and IDs in mono where they are scanned, not read.

### 2.4 Motion

Defined curves and durations, not browser defaults. Two rules specific to this
product:

- Motion must be **seek-safe and interruptible** — no animation whose absence
  changes what the user understands.
- Everything respects `prefers-reduced-motion` (already in `globals.css`).

---

## 3. Information architecture: three shells, not one app with permissions

**The matrix's own requirement — "Admin primarily web, Teacher/Student
primarily mobile, one shared backend" — is an information-architecture
instruction.** A principal's console and a student's phone do not become the
same product by hiding navigation items.

The earlier research reached the same conclusion from the dashboard-family
analysis: *"the principal's console and the parent portal are not the same
design problem, and should not be the same screen."*

| Shell | Device | Shape | Density | Tone |
|---|---|---|---|---|
| **Principal / Admin** | Web, ≥1280px | Sidebar + work surface + inspector | Dense (36px rows) | Analytical: show the data, let them find their own answer |
| **Teacher** | Mobile + web | Bottom nav + one primary action per screen | Comfortable (48px) | Operational: make the next tap obvious |
| **Student** | Mobile | Bottom nav, read-only | Comfortable | Interpreted: state a conclusion, no management vocabulary |
| **Parent** | Mobile, scenario-driven | Card stack keyed to questions | Comfortable | Interpreted, and **scenario-led, not vocabulary-led** |

### 3.1 Navigation, per shell

**Principal (web).** The sidebar exists and is 256px, but it is **not the
primary navigation** — §4's command palette is. Sidebar groups, derived from the
modules that actually exist in `contract/openapi.json`:

```
OVERVIEW      Dashboard
ACADEMICS     Curriculum · Question bank · Book selection
PLANNING      Calendar · Timetable · Schedule
DELIVERY      Coverage & pace · Delayed topics · Teacher assignments
ASSESSMENT    Papers · Assessments · Scan & grade · Evaluations
PEOPLE        Students · Teachers · Parents · Consent
SETTINGS      School · Templates · Users · Audit trail · Export
```

The sidebar **recedes** when the user reaches a destination. Linear's 2025
refresh did exactly this, and their stated reasoning is the principle: *"not
every element of the interface should carry equal visual weight... the parts
central to the user's task should stay in focus, ones that support orientation
and navigation should recede."*

**Teacher (mobile).** Three items, no more:
1. **Today** — the default landing surface, and the answer to the only question that matters at 8am
2. **Timetable** — day/week/month
3. **Papers** — generate, review, share

**Student (mobile).** Today · Progress · Practice.
**Parent (mobile).** Three scenario cards, phrased as questions:
*"What is my child learning this week?"* · *"Is my child on track?"* · *"What can I do at home?"*
The last one maps to the growth-mindset scaffolding already specified in AGENTS.md §A8.

---

## 4. The command palette — the single highest-leverage addition

**This is not in the matrix. It is the change that most reduces clicks per task,
and it is the pattern that separates a modern professional tool from a form
wizard.**

A palette fuses three things the research insists must be one surface:

| Function | Example query | Result |
|---|---|---|
| **Navigate** | `cov` | Coverage & Pace → |
| **Lookup** | `Aarav` | Student · Aarav Menon, 10-B |
| **Act** | `resched` | Reschedule lesson… · PUSH schedule… |

### 4.1 The contract (do not deviate)

```
⌘K / Ctrl+K   open          ↑ ↓   move
Esc           close         ↵     run
                              ⌘↵   open in new tab
```

Deviating from this is "a UX tax you collect on every keypress" — this is the
one shortcut set users have already learned from Raycast, Linear, Notion and
GitHub.

### 4.2 The things most palettes get wrong, and ours must not

| Failure | Requirement here |
|---|---|
| Input not focused on open | Focus the input before the open animation begins |
| Focus not returned on close | Return focus to the exact invoking element, not `<body>` |
| Real focus moved to the highlighted row | Keep focus in the input; use `aria-activedescendant` |
| `Tab` escapes to the page | Trap focus; `Tab` cycles within the palette |
| Async results reorder under the cursor mid-keystroke | `AbortController` on every keystroke; never reorder after paint |
| Mouse and keyboard select differently | One code path for both |
| 400 admin actions flood the list | **Curate.** Cap 5 results per group; exhaustive search is a second mode |
| Blank on no results | Offer recents, then common actions, then an explanation |

### 4.3 Accessibility (ARIA 1.2 combobox, not a div with a keydown)

```
role="combobox" aria-expanded aria-haspopup="listbox" aria-controls
aria-activedescendant  → the highlighted option's id
role="listbox" › role="option" aria-selected
role="dialog" aria-modal="true"   focus trapped, restored on close
```

> "Get this wrong and a screen reader user hears nothing useful, which is worse
> than not having a palette at all." — [137Foundry, Aug 2026](https://137foundry.com/articles/command-palette-interface-users-actually-reach-for)

### 4.4 Ranking

Local registry, ranked client-side, **sub-100ms or it has failed**:

```
score = fuzzyMatch(label, query) + frecencyBoost(id) + contextBoost(route)
```

- **Frecency** (recency × frequency, decayed over weeks) persisted locally. A palette without recents "doesn't learn".
- **Context boost**: on `/curriculum/ch_42`, put "Extract topics from this chapter" above generic actions.
- **Fuzzy**: reward prefix and camel-boundary matches, penalise gaps, rank exact above partial.
- Remote content search debounced 150–250ms, merged into **one** ranked list with a quiet badge — never two sections.

---

## 5. The primitives

Existing (Phase 2, verified): `Button`, `StatusPill`, `KpiTile`, `DataTable`,
`Card`, `EmptyState`, `Skeleton`, `Tabs`, `Icon`.

Required to reach "complete", in build order:

| # | Primitive | Why it is not optional here |
|---|---|---|
| 1 | **CommandPalette** | §4. Primary navigation for the principal shell |
| 2 | **Inspector / side panel** | Master-detail beats modals for records. A modal loses context on a 22-row table; an inspector keeps the table visible. Also the only shape that survives keyboard navigation well. |
| 3 | **Toast + UndoStack** | Undo replaces confirmation. §5.2 |
| 4 | **BulkActionBar** | Marking 6 lessons, enrolling 30 students. Appearance-on-selection, count, and a clear cancel. |
| 5 | **SavedViews / FilterBar** | "Delayed topics, Science, this month" must be a URL and a saved view, not a memory. |
| 6 | **DiffReview** | The ITS trust finding: every generated artefact inspectable and editable before use. Side-by-side, per-item accept/reject. |
| 7 | **Timeline / AuditTrail** | `audit_log` exists and has **no UI**. CERT-In requires the trail; a principal needs to read it. |
| 8 | **ProgressBar / Meter** | Coverage and pace need a shape, not just a number |
| 9 | **DateRangePicker** | Calendar, holiday and reporting screens all need it; one implementation |
| 10 | **Wizard / Stepper** | Multi-step flows. Recognition cues do not scaffold multi-step tasks — see §5.3 |
| 11 | **SyncStatus** | Per-record offline state — §9 |
| 12 | **ProvenancePopover** | Every AI-derived value needs "where did this come from" |

### 5.1 Density toggle

One control, ≥1280px only, persisted per user: **Comfortable (48px rows) /
Dense (36px rows)**. Default dense for the principal shell, comfortable for
teacher and parent. This is the honest way to resolve the density disagreement
in the literature rather than picking a side.

### 5.2 Undo, not confirmation

| Action | Treatment |
|---|---|
| Mark lesson complete | **Immediate + undo toast** (5s). The highest-frequency action in the product must be one tap. |
| Reschedule / PUSH | Preview of exactly which lessons move, then apply + undo |
| Delete a topic with linked questions | **Blocked**, with the linked count and what to do about it (matches the existing `DELETE` protection) |
| Delete a book/school-year | Typed confirmation of the exact name |
| Approve 404 extracted subtopics | Review surface, not a dialog. Never a bulk approve without inspection. |

The rule: **reversible actions get undo; irreversible ones get friction; nothing
gets a dialog nobody reads.**

### 5.3 Progressive disclosure, capped at three levels

Levels: (1) the default path, (2) a named reveal (*"Advanced retention
settings"*, never *"More"*), (3) a dedicated secondary route.

Hard requirements from the pattern literature:

- The default path must be **genuinely complete**, not a decoy.
- A reveal label **names what is hidden** and whether hidden values differ from defaults.
- When a hidden section has been changed, **summarise the change near the primary action** and offer reset.
- Keep the reveal trigger **in keyboard order before** the controls it reveals.
- If validation fails inside a hidden section, **open it or link to it** — never fail silently behind a collapse.

Cap at 3: *"too many layers can have the opposite effect."*

---

## 6. Screen inventory — every matrix row, mapped

Legend: **E** = exists in Flutter today · **N** = new · **U** = needs upgrading to this spec.

### 6.1 Curriculum hierarchy

| Matrix row | Screen | Notes |
|---|---|---|
| Board → Subtopic hierarchy, LLM-proposed, admin-approved | **Curriculum explorer** (E/U) | Tree left, inspector right, DiffReview for proposals. Chain: Board → Year → Grade → Subject → Unit → Chapter → Topic → Subtopic, **3 levels visible, deeper on demand** |
| Official CBSE data as source | same | Show the `source` field per node — provenance is the product's differentiator |
| **School selects the actual book** ⚠ *matrix: Missing* | **Book selection** (N) | Highest-value new screen. Pick edition per subject/grade, then **"Process this book"** → the real TOC/extraction pipeline. Today a school cannot do this at all |
| Teaching-time estimate, configurable period duration | **Teaching-time panel** (U) | Inside the book/chapter inspector. Show the estimate **and its inputs** (working days, period minutes, weightage) — a number with no visible derivation is the black box the ITS study says loses teachers |
| Chapter-level breakdown, displayed | same | |

### 6.2 Academic calendar

| Matrix row | Screen | Notes |
|---|---|---|
| Academic year start/end | **School calendar** (N) | *The matrix explicitly notes there is no school-wide calendar UI.* Month grid + year ribbon |
| Calendar vs working days, holidays, 2nd/4th Saturdays | **Calendar setup** (U) | Per-weekday toggles, alternate-Saturday rule, **multi-day block holidays as a drag range** — plus a **non-drag alternative** for WCAG 2.5.7 (§7) |
| Configurable period duration | **Calendar setup** (U) | Already exists as controls; bring to spec |
| Teaching-time estimate grounded in the calendar | **Coverage projection** (N) | "At 6 periods/week you finish Science on 14 Mar; the year ends 30 Apr." A date the principal can act on beats a period count |

### 6.3 Micro-scheduling

| Matrix row | Screen | Notes |
|---|---|---|
| Dated `ScheduledLesson[]` | **Schedule** (E/U) | |
| Yearly / Monthly / Weekly / Daily, consistent | **Schedule** (E) | Four modes, **one data source**. Already built correctly for teachers — the year view as a 12-tile per-month count is exactly right |
| Reorder delivery sequence | **Curriculum editor** (N) | Drag-and-drop **plus** a "Move to position…" menu for WCAG 2.5.7 |
| Reschedule PUSH/ADJUST + audit trail | **Reschedule panel** (U) | Show the *preview delta* before applying, and the audit entry after |

### 6.4 Teacher execution

| Matrix row | Screen | Notes |
|---|---|---|
| "What do I teach today" | **Today** (E/U) | **This is the product.** Time-to-first-value target: **< 3 seconds from login to today's lesson visible.** One card, one primary action |
| Mark Completed Yes/No + optional note | **Lesson sheet** (E/U) | Yes/No + note. Marking is **optimistic** (§9). Voice note as an input alternative — the research flags it as a cheap, real differentiator for a teacher typing 40 notes on a phone |

### 6.5 Management tracking

| Matrix row | Screen | Notes |
|---|---|---|
| Coverage %, variance, delayed topics by every axis | **Coverage & pace** (E/U) | **The analytical screen, so every number needs a baseline.** A bare "78%" is decoration. Require comparison: last month, target, or sister subject |
| | | Cap at 4 KPI tiles. Tables lead; one chart maximum, and only where a trend is the insight |
| | | Delayed topics must **drill through to reschedule in one click** and show *days overdue* + assigned teacher |

### 6.6 Student & parent

| Matrix row | Screen | Notes |
|---|---|---|
| Student portal, read-only | **Student home** (E/U) | Interpreted, not raw. "You're on track in Science; two chapters behind in Maths." |
| Parent view | **Parent home** (N) | Scenario cards (§3.1). **No vocabulary the parent does not have.** No management controls, no teacher names |

### 6.7 Users / roles

| Matrix row | Screen | Notes |
|---|---|---|
| 3 roles | **Users** (E/U) | Principal-only |
| Admin web / teacher+student mobile | shells (§3) | |
| **Create a TeacherAssignment** ⚠ *matrix: API-only* | **Roster** (N) | Assign teacher → book. Currently requires a raw API call |

### 6.8 Assessment & papers

| Matrix row | Screen | Notes |
|---|---|---|
| Assessment designer, question bank, blueprint, PDF | **Assessment designer** (E/U) | Strongest existing area; bring to craft spec |
| Subtopic-level selection | **Question picker** (E/U) | Faceted: subtopic, Bloom, difficulty, type, CBQ |
| PARAKH/CBSE: tiers, parallel sets, CBQ ≥50%, internal choice, marking scheme, quick-generate | **Paper builder** (E/U) | CBQ quota as a **visible live meter**, not a post-hoc error. Parallel sets as a compare view |

### 6.9 Preserve

All of §25–26 functionality: Evaluation, Scan & Grade, OCR, Mastery, Practice,
Gap Analysis, Planner, offline mode, encrypted storage, biometric lock.

---

## 7. Accessibility: WCAG 2.2 AA, and the six criteria that are new

The existing research set the bar (designed focus rings, keyboard-navigable,
raised text contrast). WCAG 2.2 adds obligations that **directly contradict
patterns in this app**, so they are called out rather than assumed.

| SC | Level | What it requires | Where we must act |
|---|---|---|---|
| **2.4.11 Focus Not Obscured (Minimum)** | AA | Focus must not be **entirely** hidden by author content | Sticky topbar + sticky table headers. `scroll-margin-top` on every focusable; the existing `sticky top-0 z-10` topbar is the exact risk |
| **2.5.7 Dragging Movements** | AA | Anything drag-operated needs a **single-pointer, non-drag** alternative | Timetable builder, curriculum resequencing, calendar range selection, timetable slots. Each needs "Move to…" / date inputs |
| **2.5.8 Target Size (Minimum)** | AA | ≥ **24×24 CSS px** | The 36px dense row height is fine; **row action icons are not.** Icon buttons in tables need 24px hit area minimum, ideally 44 |
| **3.2.6 Consistent Help** | A | Help mechanism in a consistent place | One help affordance, same position, every shell |
| **3.3.7 Redundant Entry** | A | Do not ask for the same information twice | Multi-step paper generation and onboarding must carry data forward |
| **3.3.8 Accessible Authentication** | AA | No cognitive test without an alternative; **allow paste and password managers** | Biometric app-lock is fine (it is an alternative, not the only path). Never block paste into password fields |

Plus the AAA target we will meet anyway because it is cheap: **2.4.13 Focus
Appearance** — a 2px perimeter with ≥3:1 contrast between focused and unfocused
states. Our focus ring is `2px solid var(--color-brand-600)` with a 2px offset;
this is already met and `scripts/check_design_tokens.py` fails the build on
`outline: none`.

### 7.1 Verification, not assertion

Accessibility is only claimed when measured. Required before any screen is
called done:

- Keyboard-only traversal of the full task, no mouse
- One screen-reader pass with real content, not lorem ipsum
- 200% zoom without loss of function
- Contrast checked in default *and* stressed (hover/focus/disabled) states
- Automated axe pass in CI on every route

---

## 8. Beyond the matrix — what a world-class school OS also needs

Ordered by value per unit of effort. Each is justified, not merely listed.

| # | Capability | Why it belongs |
|---|---|---|
| **1** | **Command palette** (§4) | Highest click-reduction of anything available |
| **2** | **Audit trail viewer** | `audit_log` is written and never read. CERT-In requires retention; a principal needs to answer "who changed this". A control with no interface is not a control |
| **3** | **Consent management** | `GET/POST/DELETE /api/v1/consent` exist with **no UI**. DPDP requires verifiable parental consent for minors — an API-only compliance feature is a compliance gap with a green test |
| **4** | **Data export / portability** | `GET /curriculum/export` exists; DPDP and basic trust require it be self-serve. Also the real answer to "what if we leave" |
| **5** | **Global search** | One box for students, papers, topics, chapters. Shares the palette's plumbing |
| **6** | **Saved views** | "Science, behind pace, this term" should be a link a principal sends |
| **7** | **Bulk operations** | Enrolling 30 students one at a time is why pilots die |
| **8** | **School-wide calendar** | The matrix asks for it and notes it does not exist |
| **9** | **Book selection + processing** | The matrix's one **Missing** row |
| **10** | **Teacher assignment admin UI** | Matrix calls it "a real, smaller follow-up" |
| **11** | **Notification centre + one morning digest** | Per `docs/notifications.md`. Engagement-driven pushes are explicitly rejected in the research |
| **12** | **Print stylesheet** | **The paper is the product.** A printed CBSE paper, answer key and coverage report are real outputs. A print stylesheet is not a nice-to-have; today the browser will print the sidebar |
| **13** | **Devanagari + Indian numerals + Indian-English microcopy** | The research is specific: script-appropriate typography and the right microcopy register |
| **14** | **Answer-key side-by-side review** | Scan & grade review is the highest-volume keyboard task in the product. It deserves a dedicated keyboard contract (j/k/1-5/↵) |
| **15** | **Onboarding: a first-run checklist, not a tour** | 65% of teachers never get a clear explanation. A dismissible checklist that reflects real state ("1 of 4: choose Science book") beats a modal tour |
| **16** | **Performance budgets in CI** | See §11 |
| **17** | **Conflict resolution UI** | §9. The honest half of offline-first |

### 8.1 Explicitly NOT built

Minimalism is also refusal, and the research settled these:

| Rejected | Reason |
|---|---|
| Streaks, badges, points, leaderboards | Already refused in `design-system.md` §12. A principal ranking teachers by app usage is a labour dispute |
| Engagement push notifications | "Most school software's notification strategy destroys trust" |
| Dark mode as a headline feature | Genuinely contested (one eye-tracking study found dark mode lowered *perceived* workload but light gave better acuity at small sizes). Token-ready, but not a priority, and the brief is white-first |
| Text-free / picture-based UI | Our users are graduates. Do not design for illiteracy |
| A separate "parent app" | Piggyback until there is evidence it is needed |
| Gamified progress for students | The parent view carries growth-mindset framing instead |

---

## 9. Offline and sync: telling the truth

Mobile is offline-first; the Web sub-product is a thin client. The failure the
literature is unanimous about is **silently lying about save state**:

> What breaks trust is not conflict itself. **What breaks trust is silence.**
> — [DEV, Apr 2026](https://dev.to/crisiscoresystems/sync-conflict-handling-in-offline-first-pwas-how-to-merge-without-lying-to-the-user-59i3)

### 9.1 Per-record state, always visible

| State | UI | Copy |
|---|---|---|
| `pending` | Small dot | "Saved on this device" |
| `syncing` | Subtle activity | "Syncing…" |
| `synced` | Nothing (clean is the reward) | — |
| `needs-attention` | Amber, tappable | "Couldn't upload — tap to review" |
| `blocked` | Amber | "Waiting on an earlier change" |

**Never show a permanent success tick at local-commit time** if the workflow
requires server acceptance. The teacher marking a lesson is the case that
matters: mark is local-committed instantly, and the state must say so honestly
until acknowledged.

### 9.2 Optimistic writes, honestly resolved

Two writes per action, which the research articulates well:

- An **immutable event** ("at 14:32 this user marked lesson X complete") — the
  only thing the server trusts, and the thing that gets uploaded.
- A **disposable local projection** that paints the screen instantly.

The projection is safe to throw away precisely because the event is permanent.
The UI consequence: the screen never shows a spinner for a tap, and never shows
the old state for a frame first.

### 9.3 Conflict, by data type

| Data | Policy | Guardrail |
|---|---|---|
| Lesson completion | Last-write-wins with server stamp | `completed_by`/`completed_at` already exist |
| Lesson note (free text) | **Soft conflict** — keep both, show a review toast | "Edited on two devices. [Keep both] [Use this one]" |
| Reschedule / PUSH | **Hard conflict** — never auto-merge | A silently moved schedule is a labour dispute |
| Consent, permissions | **Hard conflict** — server-authoritative, explicit rejection | Legal weight |

Clock skew warning: never decide with client wall-clock alone. `EventStore`
already stamps server-side with a `seq`; keep that.

---

## 10. Artificial intelligence: making it inspectable

The single most important finding in the existing research for this product:

> A two-year study of an intelligent tutoring system found teachers abandoned it
> because they could not predict what it would show students... "You assign them
> tasks that are hidden. I have no idea what kind of tasks they get. I experience
> a lack of control. I prefer control." The system was a black box, so teachers
> stopped using it before assessments.
> — [HICSS 2021](https://doi.org/10.24251/hicss.2021.186)

Blueprint-driven paper generation is exactly this shape. Therefore, as a product
rule rather than a UX preference:

1. **Every generated artefact is inspectable and editable before it is used.** The review step is a first-class screen, never an "advanced" option.
2. **Every generated claim shows its evidence.** The system already returns `citations` and `document_id`/`page` — surface them. A citation is the product's differentiator, not debug output.
3. **Every AI value carries provenance** on hover/tap: which document, which page, which method, what confidence.
4. **Confidence is shown honestly** where it drives a decision (extraction, OCR, auto-scoring), and low confidence routes to a human — already true in `evaluate.py`; keep it.
5. **AI never takes an irreversible action.** Read-only is the architectural property that makes prompt injection survivable here (`llm/coerce.py`, `agents/`). Do not give the agent a tool without revisiting this.

---

## 11. Performance budgets

A dashboard that takes 3 seconds loses half its sessions. Budgets, enforced in
CI rather than aspirational:

| Metric | Budget |
|---|---|
| Time to first value (login → today's lesson visible) | **< 3s** |
| Route transition (already-loaded shell) | **< 150ms** |
| Command palette keystroke→result | **< 100ms** |
| Table with 500 rows, scroll | 60fps (virtualise past ~100 rows) |
| LCP, principal shell on 4G | **< 2.0s** |
| Marketing/static route on Cloudflare Pages | **< 1.0s** |

The existing bundle work (gzip, 19.4MB → 5.0MB) is the baseline; a Lighthouse
or `web-perf` check belongs in the pipeline so this cannot silently regress.

---

## 12. Measurement

**Measure**

| Metric | Why |
|---|---|
| Time to first value | The most predictive adoption number |
| Completion rate of the three core loops | See today's lessons · mark a lesson · generate a paper |
| Weekly active teachers **as a share of the school roster** | A raw count is meaningless |
| Palette open rate, query→selection time, **zero-result rate** | Zero-result rate is the tuning signal |
| Empty/error state hit rate | High = onboarding failure, not a data problem |
| Coverage-report views per principal per month | Evidence reporting drives decisions |

**Anti-metrics** (make usage look good while nothing improves): raw DAU,
notifications sent, assessments generated without evidence they were taught,
time-in-app, and **any per-teacher ranking**.

Instrument the palette from day one, because the failure mode is silent: teams
"assume the palette is working because nobody complained, and never notice that
half their users tried it once, hit a bad result, and quietly went back to
clicking through menus."

---

## 13. Build order

Ordered so each phase is independently valuable and measurable.

| Phase | Contents | Gate |
|---|---|---|
| **0 — Craft pass** | Complete the six states on the 12 existing primitives; the four data-surface states on existing screens. No new screens | Every primitive passes the §2.1 matrix; axe in CI |
| **1 — Shells** | Role shells per §3; palette per §4 | ⌘K navigates, looks up and acts; keyboard-only pass; <100ms |
| **2 — Missing matrix rows** | Book selection, roster/assignments, school calendar, curriculum resequencer | The matrix's 4 open rows close |
| **3 — Trust surfaces** | DiffReview, ProvenancePopover, AuditTrail, Consent UI, Export | Every generated artefact inspectable and editable |
| **4 — Offline truth** | SyncStatus, optimistic marking, soft-conflict review | Kill the network mid-mark; state is never wrong |
| **5 — Interpretation** | Student and parent shells | A parent completes their three questions without a single piece of our vocabulary |
| **6 — Scale & polish** | Saved views, bulk ops, search, print stylesheet, i18n | Print output is genuinely good |

Phase 0 first is the whole argument of §1. A new screen built on incomplete
primitives makes the product measurably worse.

---

## 14. Evidence quality

What I would **not** put in front of a board:

- **The 36px/48px and 256px numbers** are practitioner conventions with strong
  convergence, not controlled findings. They are defaults to start from and test.
- **Frecency decay curves** are borrowed from browser address bars. Reasonable,
  unmeasured *for this product*; instrument and tune.
- **"<100ms feels instant"** is a long-standing interaction heuristic, not a
  measured threshold for our users on our devices.
- **The dark-mode conclusion** is genuinely contested and not settled by the
  studies cited.
- **Everything in §11 is a budget, not a measurement.** None of it has been
  measured on this product yet. Phase 0 is where it becomes real.
- **The award-winning claim is unfalsifiable as written.** What is falsifiable,
  and what this document actually commits to: every interactive element has six
  designed states, every data surface has four, WCAG 2.2 AA is verified rather
  than asserted, and time-to-first-value is under three seconds. Those can be
  checked. "Award-winning" cannot.
