# AcademicOS Design System

**v2.0 · 2026-09-17 · white-first · emoji-free**

The machine-readable source of truth is [`../design/tokens.json`](../design/tokens.json).
This document explains it; it does not restate every value. If the two ever
disagree, the JSON wins and this file is wrong.

```
design/tokens.json ──build_tokens_css.py──> design/tokens.css ──> implementation
                     check_design_tokens.py  enforces both directions
```

| Command | What it does |
|---|---|
`python scripts/build_tokens_css.py` | Regenerates `design/tokens.css` from the JSON |
`python scripts/check_design_tokens.py` | Fails on emoji, raw colours, off-scale sizes, stale CSS |

---

## 1. Principles

1. **White surfaces on a cool off-white canvas.** Cards, tables and inputs are
   `#FFFFFF`; the page behind them is `#F8FAFC`. Structure comes from 1px borders
   and spacing, not from grey fills or drop shadows. **Pure white as a full-page
   background is a documented anti-pattern for dense dashboards** — maximum
   emitted light, visual fatigue over a session, and card edges that dissolve into
   the page. That is why canvas and card are separate tokens
   (`--color-surface-canvas` / `--color-surface-card`); do not collapse them, and
   do not go darker than `#F8FAFC`, which reads grey and looks washed out.
   Reasoning and sources: [`research/ui-ux-principles.md`](research/ui-ux-principles.md) §2.
2. **Density is a feature.** A principal comparing 22 chapters and a teacher
   scanning a week of lessons both want information, not air. Every default
   serves the compact case; `comfortable` is the opt-in.
3. **Numbers must be comparable.** Tabular figures, right-aligned numerics, fixed
   decimals, and colour only where it encodes meaning. Without tabular figures
   columns jitter as values change, which defeats the entire purpose of the screen.
4. **Status is never colour alone.** Colour-blind users and greyscale printouts
   exist. Every state carries a label; the glyph is reinforcement, not decoration.
5. **No emoji, ever.** Not in labels, buttons, empty states, errors, toasts,
   table cells, or UI strings in test fixtures. Use a Lucide icon or a word. There
   is no exception and the checker enforces it.
6. **Every interactive element is addressable.** A stable `data-testid` is part
   of the component contract (§7), not an afterthought. It is what makes
   automated visual verification of a deployed app possible.
7. **One brand colour, spent carefully.** Semantic colour carries meaning; the
   brand carries identity. They never compete and never substitute for each other.

---

## 2. The token workflow

**The rule: no literal value appears anywhere in application code.**

```tsx
// wrong -- invisible drift. Renders fine, survives review, diverges forever.
<div style={{ color: '#4F46E5', padding: '13px', borderRadius: '5px' }} />

// right -- the token, so a change here changes every screen at once.
<div className="text-brand-600 p-3 rounded-md" />
```

If a value you need is not in `tokens.json`, **add it there first**, rebuild, and
commit. That is not bureaucracy: it is the only thing preventing twenty screens
from acquiring twenty slightly different greys.

---

## 3. Colour

White-first, on the standard Tailwind palette so every value is recognisable,
greppable and reviewable.

| Role | Token | Value |
|---|---|---|
Page canvas — the only off-white | `--color-surface-canvas` | `#F8FAFC` |
Card, table, input surface | `--color-surface-card` | `#FFFFFF` |
Inset (table header, code, wells) | `--color-surface-inset` | `#F1F5F9` |
Border | `--color-neutral-200` | `#E2E8F0` |
Border, strong / disabled text | `--color-neutral-300` | `#CBD5E1` |
Text, primary | `--color-neutral-900` | `#0F172A` |
Text, secondary | `--color-neutral-600` | `#475569` |
Text, muted | `--color-neutral-400` | `#94A3B8` |
Brand, interactive | `--color-brand-600` | `#4F46E5` |
Brand, hover | `--color-brand-700` | `#4338CA` |
Brand, tint fill | `--color-brand-50` | `#EEF2FF` |

**Contrast:** `#0F172A` on white is 17.9:1, `#475569` is 7.5:1, `#94A3B8` is
2.6:1 and is therefore **never used for text that must be read** — placeholders
and disabled labels only.

### Status

Each status is a triple (`fg` / `bg` / `border`). Never a bare fill behind text.

| Status | fg | bg | Meaning |
|---|---|---|---|
`success` | `#047857` | `#ECFDF5` | Completed, on pace, approved |
`warning` | `#B45309` | `#FFFBEB` | At risk, delayed, needs review |
`danger` | `#B91C1C` | `#FEF2F2` | Overdue, failed, destructive |
`info` | `#1D4ED8` | `#EFF6FF` | Scheduled, neutral information |
`neutral` | `#475569` | `#F8FAFC` | Not started, skipped |

### Charts

Five series maximum (`--color-series-1..5`). A sixth colour makes the chart
illegible; aggregate the remainder into "Other" instead.

---

## 4. Typography

Two families, both standard and both loaded with a full fallback stack.

| Role | Family | Size / line-height | Weight |
|---|---|---|---|
KPI number | Inter | 30 / 36 · tabular | 600 |
Page title | Inter | 24 / 32 | 600 |
Card / section heading | Inter | 16 / 24 | 600 |
Body, buttons, inputs | Inter | **14 / 20** | 400–500 |
Dense table cell | Inter | 13 / 18 | 400 |
Meta, badge | Inter | 12 / 16 | 400–500 |
Table header, eyebrow | Inter | 11 / 16 · `0.04em` · uppercase | 500 |
IDs, codes, timestamps, numerics | JetBrains Mono | 13 / 18 | 400 |

**Never below 11px. Never more than three sizes in one card.** Sentence case
everywhere except table headers and eyebrows. No italics, no text-shadow, no
letter-spacing beyond the two defined.

---

## 5. Space, density, shape

- **Space scale (4px base, identical to Tailwind):** 0 4 8 12 16 20 24 32 40 48 64.
  An off-scale value is a bug, not a preference.
- **Density:** `compact` — row 32px, cell padding 12/6 (the default for tables and
  lists). `comfortable` — row 44px, padding 16/10 (touch viewports and forms).
- **Radius:** 4 / 6 (default) / 8 / 12 / 999.
- **Elevation:** **two** levels. Cards use a 1px border and no shadow. Only
  overlays (modal, drawer, popover) cast `--shadow-md`.
- **Stacking:** a fixed ladder — sticky 10, drawer 30, modal 40, popover 50,
  toast 60. Never invent a z-index, never `9999`.

---

## 6. Icons and the emoji ban

**Icon set: [Lucide](https://lucide.dev). One set. No custom SVGs, no second
library, no emoji as an icon.**

| Size | Use | Stroke |
|---|---|---|
16 | inline with 13–14px text, table cells | 2 |
20 | buttons, nav, form fields | 1.5 |
24 | page headers, empty states | 1.5 |

- Icons inherit `currentColor` and never carry their own colour.
- Decorative icons get `aria-hidden="true"`. A meaningful icon gets an
  `aria-label` **or** adjacent visible text — never neither.
- **Emoji are forbidden.** `scripts/check_design_tokens.py` scans the source and
  fails on any pictograph, dingbat or variation selector. This includes `✓` and
  `✗` in UI strings: those are a Lucide `check` / `x` icon, not a text glyph. A
  check mark rendered as a character has no accessible name, scales badly, and
  renders differently on every device.

---

## 7. Components

Every component exposes the `data-testid` below. This is the mechanism that makes
the deployed app automatically verifiable — a test must never have to find a
control by its visible text.

| Component | Variants | Test hook |
|---|---|---|
Button | primary · secondary · ghost · danger · icon-only | `<action>-btn` |
Input / Textarea | default · error · disabled · prefix/suffix | `<field>-input` |
Select / Combobox | single · multi · async | `<field>-select` |
Table | compact · comfortable · sortable · selectable · sticky header | `<entity>-table`, `row-<id>` |
KPI tile | default · trend · status | `kpi-<metric>` |
Status pill | the five states in §3 | `status-<id>` |
Tabs | underline · segmented | `tab-<name>` |
Card | default · interactive · flush | `card-<name>` |
Drawer | right (detail) · bottom (mobile) | `drawer-<name>` |
Modal | confirm · form | `modal-<name>` |
Toast | success · error · info | `toast-<kind>` |
Empty state | no-data · no-results · error · no-permission | `<scope>-empty` |
Skeleton | text · table · card | `<scope>-loading` |
Calendar grid | month · week · agenda | `calendar-<mode>` |

### Button state matrix

Every state maps to a token. Nothing is derived at implementation time.

| State | Primary | Secondary | Ghost | Danger |
|---|---|---|---|---|
Default | `--btn-primaryBg` | `--btn-secondaryBg` + border `neutral-300` | transparent, text `neutral-600` | `--btn-dangerBg` |
Hover | `--btn-primaryBgHover` | `--btn-secondaryBgHover`, border `neutral-400` | bg `neutral-100` | `--btn-dangerBgHover` |
Active | `--btn-primaryBgActive` + `inset 0 1px 2px rgb(0 0 0 / .18)` | `--btn-secondaryBgActive` | bg `neutral-200` | `--btn-dangerBgActive` |
Focus | `--focus-ring` (2px white + 2px brand) — on every variant | same | same | same |
Disabled | bg `--btn-disabledBg`, text `--btn-disabledFg`, `cursor: not-allowed` | same | text `neutral-300` | same |
Loading | disabled visuals + 16px spinner replacing the label, `aria-busy="true"`, width locked | same | same | same |

Button geometry: height 32 (compact) / 36 (default) / 44 (touch), padding-x 12/16,
radius 6, gap 8 between icon and label. Loading **never** changes the button's
width — a control that resizes on click moves the thing the user is about to
click next.

### Mandatory states for every data surface

`loading` (skeleton, not a spinner) · `empty` (says why, and what to do next) ·
`error` (what failed, whether retrying helps) · `no-permission` (**distinct from
empty** — a teacher must never be shown "no data" when the truth is "not for you").

---

## 8. Layout

```
┌────────────┬───────────────────────────────────────────────┐
│            │  Page header:  breadcrumb · title · actions    │
│  Sidebar   ├───────────────────────────────────────────────┤
│  240px     │  Filter bar (optional, sticky, z-10)           │
│  → 64px    ├───────────────────────────────────────────────┤
│  < 1280px  │  Content                                       │
│            │   ├ KPI row (max 4 tiles)                      │
│            │   ├ Primary table / calendar / chart           │
│            │   └ Detail drawer 480px (right) or modal        │
└────────────┴───────────────────────────────────────────────┘
```

Content max 1440px; prose max 720px (≈72 characters). Breakpoints 640 / 768 /
1024 / 1280 / 1600. **A KPI row of five tiles means the page has no priority** —
four is the maximum.

---

## 9. Motion

Functional only. Durations 100 / 150 / 200ms; one easing
`cubic-bezier(0.2, 0.8, 0.2, 1)`. Animate opacity and transform only — never
width, height, top or left. No entrance animations on page load, no parallax, no
bounce. A dashboard that animates is a dashboard somebody is waiting on. Under
`prefers-reduced-motion: reduce` the durations collapse to zero (§tokens).

---

## 10. Accessibility floor

- AA contrast minimum (4.5:1 text, 3:1 large text and UI borders).
- Visible focus on **every** interactive element via `--focus-ring`. Never
  `outline: none` without a replacement; the checker flags it.
- Full keyboard operation: tab order follows visual order, arrow keys within
  tables and menus, `Esc` closes overlays, focus trapped in modals and restored on close.
- Hit areas: 32px pointer, 44px touch — the *target*, not the visual size.
- `aria-live="polite"` for toasts and async table updates.
- The app must be usable in English by someone reading it as a second language:
  short labels, no idioms, no abbreviations that are not universal.

---

## 11. Writing

Interface copy is design material.

- Name things by what the user controls: "Assign teacher", not "Create mapping".
- Active voice, sentence case, no exclamation marks.
- Errors state what happened and whether retrying helps. No apologies, no
  vagueness, never a bare "Something went wrong".
- Empty states invite an action: "No lessons scheduled yet — generate the
  schedule from Calendar & setup."
- **One term per concept across all 24 screens.** A "lesson" is never also a
  "session" or a "period slot". Pick one and hold it.

---

## 12. For AI agents working on this UI

This section exists because agents are a primary contributor, and the failure
mode is specific and predictable: an agent asked to "add a card" invents a
shadow, a colour and a radius, and the UI drifts one component at a time.

**Do**
- Read `design/tokens.json`. Use a token for every colour, size, radius and
  duration. If the token does not exist, add it to the JSON, run
  `build_tokens_css.py`, and commit — do not inline a literal.
- Compose the components in §7 rather than writing new markup.
- Add the `data-testid` from the table.
- Put the value in `tokens.json` when you need a new one — that is a two-line
  change and it is reviewed like any other.

**Do not**
- Do not emit an emoji. Not for a status, a bullet, a celebration, or a comment.
- Do not hardcode a hex colour, an off-scale spacing value, or a z-index.
- Do not add a third elevation, a second icon set, or a fourth font size.
- Do not restyle an existing component to fit a new screen — change the
  component if it is genuinely wrong, so every screen moves together.
- Do not write `outline: none`.
- **Do not add a streak, badge, points, level or leaderboard mechanic.** This is
  a settled decision, not an oversight. Eyal's own critique applies: variable
  rewards are a liability for a utility, and a broken streak punishes a teacher
  for the product's failure. The reward for using AcademicOS is that it worked,
  again, in twenty seconds. Reasoning:
  [`research/ui-ux-principles.md`](research/ui-ux-principles.md) §4.
- **Do not add an engagement-driven notification.** One morning digest keyed to
  "what am I teaching today" is the policy. A push whose purpose is to make
  somebody open the app is how a school tool loses trust.

**Why this is enforced rather than documented:** rules in prose get ignored by
the next agent and forgotten by the next human. `check_design_tokens.py` turns
each of these into a failing build, which is the only instruction that reliably
survives a context reset. Run it before you push.

---

## 13. Enforcement summary

| Check | Catches |
|---|---|
Emoji scan | Any pictograph, dingbat or variation selector in source |
Raw colour scan | A hex value not present in `tokens.json` |
Off-scale size scan | A `px` value off the 4px scale |
`outline: none` | Removed focus without a replacement ring |
Generated-CSS staleness | `tokens.css` edited by hand or not rebuilt after a token change |

All five run in the ordinary test gate (`tests/test_design_tokens.py`), so they
run before any deploy rather than being a script somebody has to remember. That
test also pins the emoji detector in **both** directions — it asserts real
pictographs are caught *and* that ordinary typography (`→`, `⇒`, `★`, `—`) is
not, so the check cannot decay into noise people learn to skip.
