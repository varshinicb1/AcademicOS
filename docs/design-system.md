# AcademicOS Design System

**Version** 1.0 · 2026-09-16 · framework-agnostic

The tokens and rules below are the contract between design and implementation.
They are deliberately framework-neutral: they survive a change of renderer, which
matters because [`frontend-platform-decision.md`](frontend-platform-decision.md)
recommends one.

---

## 1. Principles

1. **Density is a feature.** This is an operations tool used by a principal
   comparing coverage across 22 chapters and a teacher scanning a week of
   lessons. Whitespace that would flatter a marketing page wastes their time.
   Every default serves the compact case; comfortable is the opt-in.
2. **Numbers must be scannable and comparable.** Tabular figures, right-aligned
   numerics, consistent decimal places, colour only where it encodes meaning.
3. **Status is never colour alone.** Colour-blind users and monochrome printouts
   exist. Every state carries a label or a glyph as well as a hue.
4. **Every interactive element is addressable.** A stable `data-testid` is not an
   afterthought — it is part of the component contract (§7). This is what makes
   automated visual verification possible, and it is a requirement, not advice.
5. **One accent, spent carefully.** Semantic colour (success/warning/danger)
   carries meaning; the brand colour carries brand. They never compete.

---

## 2. Colour

Primary is a deep **chalkboard green** — derived from the object at the front of
every classroom this product serves, not from a corporate template.

| Token | Hex | Use |
|---|---|---|
`--color-primary` | `#155E52` | Primary actions, active nav, focus |
`--color-primary-hover` | `#0F4A41` | Hover/pressed |
`--color-primary-subtle` | `#E6F0EE` | Selected rows, active tab background |
`--color-ink` | `#0E1B19` | Headings, primary text |
`--color-text` | `#2B3735` | Body text |
`--color-text-muted` | `#61706D` | Secondary text, labels |
`--color-text-faint` | `#94A29F` | Placeholders, disabled |
`--color-surface` | `#FFFFFF` | Cards, tables, modals |
`--color-canvas` | `#F4F6F5` | Page background (cool, green-tinted — *not* cream) |
`--color-border` | `#DCE2E0` | Dividers, input borders |
`--color-border-strong` | `#B8C2BF` | Table header rule, focus-adjacent |

### Semantic status

| Token | Hex | Background | Meaning |
|---|---|---|---|
`--color-success` | `#0F7B4F` | `#E7F4EE` | Completed, on-pace, approved |
`--color-warning` | `#B26A00` | `#FBF1E0` | At-risk, delayed, needs review |
`--color-danger` | `#B42318` | `#FBEAE8` | Overdue, failed, destructive |
`--color-info` | `#1D6FB8` | `#E8F1FA` | Neutral information, links |

**Rules:** status colour fills backgrounds only at ≤12% tint; never as a solid
block behind text. Never use `--color-danger` for anything reversible. Never
rely on hue alone — pair with a label (§6).

### Data visualisation
Use primary for the primary series, `--color-info` for comparison, and the
status ramp for categorical breakdowns. Maximum 5 series before the chart is
lying about its own legibility; aggregate the tail into "Other".

---

## 3. Typography

Two families. This is deliberate: real product design systems (Stripe, Linear,
GitHub) use one well-tuned UI family rather than typographic novelty, because
character in a dashboard comes from density, alignment and colour discipline —
not from an unusual typeface. Novelty here would cost legibility.

| Role | Family | Weight | Size / line-height |
|---|---|---|---|
Display | **Inter Tight** | 600 | 28/34 |
Page title | Inter Tight | 600 | 22/28 |
Section heading | **Inter** | 600 | 16/22 |
Body | Inter | 400 | 14/20 |
Small / meta | Inter | 400 | 12/16 |
Label / table header | Inter | 500 | 11/14 · `letter-spacing: .04em` · uppercase |
Data, IDs, codes | **IBM Plex Mono** | 400 | 13/18 |

**Numerals:** every table, KPI and metric uses `font-variant-numeric:
tabular-nums`. Without it, columns jitter as values change and comparison breaks.

**Rules:** never below 11px. Never more than 3 sizes in one card. Sentence case
for labels and buttons; uppercase only for table headers and eyebrow labels.

---

## 4. Space, shape, elevation

- **Base unit 4px.** Scale: `4 8 12 16 24 32 48 64`.
- **Density:** `compact` (row height 32, padding 8/12) and `comfortable`
  (row height 44, padding 12/16). Tables default compact.
- **Radius:** `--radius-sm 4px` · `--radius 6px` · `--radius-lg 10px` · pills `999px`.
- **Elevation:** three levels only — `0` (flush, tables), `1`
  `0 1px 2px rgba(14,27,25,.06)` (cards), `2` `0 8px 24px rgba(14,27,25,.12)`
  (modals, popovers). Nothing else casts a shadow.
- **Borders before shadows.** In dense UI a 1px border reads sharper than a
  shadow and costs no paint.

---

## 5. Layout

```
┌────────────┬──────────────────────────────────────────────┐
│            │  Page header: title · breadcrumb · actions    │
│  Side nav  ├──────────────────────────────────────────────┤
│  240px     │  Filter bar (optional, sticky)                │
│  collapsible├─────────────────────────────────────────────┤
│            │  Content                                      │
│            │   ├ KPI row      (max 4 tiles, equal)         │
│            │   ├ Primary table / calendar / chart          │
│            │   └ Detail drawer (right, 480px) or modal      │
└────────────┴──────────────────────────────────────────────┘
```

- Max content width **1440px**; tables stretch, prose does not (72ch max).
- **Side nav** collapses to 64px icon rail below 1280px; becomes a drawer below 768px.
- **KPI row:** maximum 4 tiles. Five means the page has no priority.
- Responsive breakpoints: `768` `1024` `1280` `1600`.

---

## 6. Status vocabulary (shared by every surface)

| State | Colour | Label | Glyph |
|---|---|---|---|
Completed / approved | success | "Completed" | ✓ |
On pace | success | "On pace" | — |
Scheduled / pending | info | "Scheduled" | ○ |
At risk / needs review | warning | "At risk" | ! |
Delayed / overdue | danger | "Overdue · 3d" | ▲ |
Skipped | muted | "Skipped" | – |

The **label always appears.** The glyph is a redundancy for colour-blind users
and greyscale printing, not decoration.

---

## 7. Component inventory

Each component below must expose the listed `data-testid`. This is the
mechanism that makes the deployed app automatically verifiable — a test should
never have to find a button by its text.

| Component | Variants | Required test hooks |
|---|---|---|
Button | primary · secondary · ghost · danger · icon-only | `data-testid="<action>-btn"` |
Input / Textarea | default · error · disabled · with-prefix | `data-testid="<field>-input"` |
Select / Combobox | single · multi · async | `data-testid="<field>-select"` |
Table | compact · comfortable · sortable · selectable · sticky header | `data-testid="<entity>-table"`, `row-<id>` |
KPI tile | default · trend · status | `data-testid="kpi-<metric>"` |
Status pill | 6 states (§6) | `data-testid="status-<id>"` |
Tabs | underline · segmented | `data-testid="tab-<name>"` |
Card | default · interactive · flush | `data-testid="card-<name>"` |
Drawer | right (detail) · bottom (mobile) | `data-testid="drawer-<name>"` |
Modal | confirm · form | `data-testid="modal-<name>"` |
Toast | success · error · info | `data-testid="toast-<kind>"` |
Empty state | no-data · no-results · error · no-permission | `data-testid="<scope>-empty"` |
Skeleton | text · table · card | `data-testid="<scope>-loading"` |
Pagination | numeric · cursor | `data-testid="pager"` |
Breadcrumb | — | `data-testid="breadcrumb"` |
Date picker | single · range | `data-testid="<field>-date"` |
Calendar grid | month · week · agenda | `data-testid="calendar-<mode>"` |

### Mandatory states for every data surface
`loading` (skeleton, not a spinner) · `empty` (explains why and what to do) ·
`error` (what failed, whether retrying helps) · `no-permission` (distinct from
empty — a teacher must never see "no data" when the truth is "not for you").

---

## 8. Accessibility floor

- Contrast: **AA minimum** (4.5:1 text, 3:1 large text and UI borders).
  `--color-primary #155E52` on white is 8.1:1; on `--color-canvas` 7.4:1.
- Focus: 2px `--color-primary` ring at 2px offset on **every** interactive
  element. Never `outline: none` without a replacement.
- Keyboard: full tab order, arrow keys within tables and menus, `Esc` closes
  overlays, focus is trapped in modals and restored on close.
- Touch targets ≥44×44px on touch viewports, ≥32px on pointer-only.
- Respect `prefers-reduced-motion`: replace transforms with opacity.
- Live regions (`aria-live="polite"`) for toasts and async table updates.

---

## 9. Motion

Functional, never decorative. Three durations: `100ms` (hover, focus),
`180ms` (expand, drawer), `240ms` (page/modal transition). One easing:
`cubic-bezier(.2,.8,.2,1)`. No entrance animations on page load, no parallax,
no bounce. A dashboard that animates is a dashboard somebody is waiting on.

---

## 10. Writing

Interface copy is design material, not decoration.

- Name things by what the user controls: "Assign teacher", not "Create mapping".
- Active voice, sentence case, no exclamation marks.
- Errors state what happened and whether retrying helps. No apologies, no
  vagueness, never a bare "Something went wrong".
- Empty states invite an action: "No lessons scheduled yet — generate the
  schedule from Calendar & Setup."
- One term per concept everywhere: a "lesson" is never also a "session" or a
  "period slot". Pick one and hold it across all 24 screens.
