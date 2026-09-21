# Answer-key recovery: variant paper codes — design

**Date:** 2026-09-21
**Status:** approved, in implementation
**Supersedes the "Remaining Work" section of `HANDOVER.md`**, which measures the
wrong denominator (see §1).

---

## 1. The finding

`HANDOVER.md` reports the Q1 answer-key milestone as 96% complete with 21 cells
remaining (7 objective + 14 VAL). Those numbers reproduce, but they count only
one of two failure modes, and it is the smaller one by a factor of thirty.

Measured against the bank the product actually serves
(`academicos-data/syllabus/questions.json`):

| | Questions |
|---|---|
| Served | 3,286 |
| With an official CBSE marking scheme | 2,833 (86.2%) |
| Without | 453 |
| — of which ship a **completely blank** scheme (zero `markingPoints`, empty `modelAnswer`) | **442** |

Splitting the 442 by why the link failed:

| Failure mode | Questions | Tracked in `HANDOVER.md`? |
|---|---|---|
| Paper code read, no answer row for that `q_no` | 14 | yes — this is its "7 + 14 cells" |
| **Paper code could not be read from the document** | **428** | no |

The milestone is nearer 86% than 96%, and the residual work is ~20x larger than
the handover implies.

## 2. Root cause

The 428 questions come from **63 source documents** whose running header carries
a paper code in a variant CBSE format:

```
465          Applied Mathematics XII
37           Home Science X
14-30(B)     Mathematics X
14-53        Computer Applications X
65(B)-11     Mathematics XII
```

`_CODE_HINT` (`src/academicos/assessment/question_bank.py:61`) matches only
three-part codes:

```python
r"(?<!\d)\d{2,3}\s*[/\-._]\s*\d\s*[/\-._]\s*\d(?!\d)"   # 31/1/1
```

It matches none of the above. Independently, every one of the 305 distinct
`paper_code` values in `answer_keys.db` is three-part — so even a correctly read
variant code would have nothing to link against.

**The marking schemes for these papers do exist, parsed, on disk.** Of the parse
artifacts, only 42 are classified `doc_type == "marking_scheme"` while **1,288
marking schemes are misclassified as `unknown`**, and they cover the same papers:

```
MS-Home Science/064/37                   -> the "37" paper
MS_XII_Applied Mathematics_241_465_...   -> the "465" paper
MS_X_Mathematics_041_30(B)_2025-26       -> the "14-30(B)" paper
MS_XII_Mathematics_041_65(B)_2025-26     -> the "65(B)-11" paper
```

The Home Science pair is the load-bearing evidence: the question paper's header
is the bare token `37`, which is precisely why a code-shaped regex skipped it,
and a separately-parsed marking scheme independently names `37` as the Q.P. code.
Two documents agreeing is the provenance standard PRD rule Q1 asks for, which is
what makes this a recovery rather than a guess.

## 3. Suspected correctness hole — unverified

`src/academicos/assessment/pool.py` reads only `answerScheme.totalMarks` and
`answerScheme.modelAnswer` and applies no filter on scheme presence. Paper
generation therefore *appears* able to select one of the 442 blank-scheme
questions, producing an exam paper whose exported answer key has empty entries —
a direct violation of PRD rule Q1 ("no answer key, no question").

This is recorded as **suspected, not proven**. Under the repo's evidence standard
(PRD §8.2) it may not be claimed until a paper has been generated against a live
backend and the exported PDF inspected. Doing so is step 1 below.

## 4. Approach

Chosen: **guard first, then recover.**

The recovery in §5 rewrites linkage logic that 2,833 currently-correct questions
depend on. Landing the guard first means that if the recovery is incomplete or
goes wrong, the product still cannot emit a paper with a blank answer key. The
guard holds independently of whether the recovery succeeds.

## 5. Plan

### Step 1 — Verify the hole (evidence standard)
Generate a real paper against a running `academicos.cli serve`, for a
subject/grade whose pool contains blank-scheme questions, and inspect the
exported PDF's answer key. Record the result either way. If the hole does not
reproduce, find and document what already filters it, and step 2 becomes a
regression test only.

### Step 2 — Characterization tests
Before touching `_CODE_HINT` or `normalize_paper_code`, pin current behavior:
the set of (question id -> paper code -> official answer) links that resolve
today, so any change to the normalizer that breaks an existing link fails a test
rather than silently reducing coverage. These tests are purely additive.

### Step 3 — The Q1 guard
Make paper generation refuse questions whose scheme has no marking points and no
model answer. Surface the refusal as a visible shortfall (PRD rule Q4: the gap is
reported, not hidden) rather than a silent drop.

### Step 4 — Variant-code extraction
Extend paper-code recognition to the variant formats, on both sides:
- question-paper headers (`465`, `37`, `30(B)`, `65(B)`, `14-53`)
- marking-scheme headers (`MS_XII_Applied Mathematics_241_465_2025-26`,
  `MS-Home Science/064/37`)

Both sides must produce the same canonical key or the link still fails.

### Step 5 — Reclassify and ingest
Reclassify the 1,288 `unknown` marking schemes and ingest them into
`answer_keys.db` under their canonical codes.

### Step 6 — Relink and measure
Re-run the relink and report how many of the 428 came back, as a measured number
against the 86.2% baseline. Report the shortfall too.

## 6. Gates

- `pytest tests -q` green after every step. Baseline at design time:
  **1850 passed, 15 skipped, 1 xfailed**.
- No question enters the bank without a real CBSE answer (rule Q1). The recovery
  must not relax this to raise the coverage number.
- Coverage is reported as a measured figure with its shortfall named, never as a
  rounded claim (rule Q4).

## 7. Explicitly out of scope

- Merging the SQP (1,834) and CBE (720) banks into the served bank. This is a
  separate, larger gap — the product serves only grades 10 and 12 while those
  banks hold grades 6-9 — and is tracked independently of this spec.
- Any change to `backend/` (the scaffolded rewrite).
