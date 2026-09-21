# Question-bank merge: SQP + CBE into the served bank — design

**Date:** 2026-09-21
**Status:** approved (scope "all"), in implementation
**Research:** 43-agent review, 34 blocker/high findings each re-checked by an
independent skeptic, 2 refuted, plus a completeness critic. 87 items in total.

---

## 1. Why this is not a data operation

The request was "merge the banks into the served bank". Doing that literally —
concatenating the three files — breaks the product in two verified ways:

1. **It stops the offline Android app from starting.** The phone decodes every
   record with `Question.fromJson`, whose generated casts are strict. All 1,834
   SQP rows lack `competencyIds` and `bloomLevel`; 259 CBE rows have parts with
   no `textLatex`. One bad row throws, the bundled-asset parse is not guarded,
   and it runs before `runApp()`. Reproduced on a real Dart build:
   `reload() threw: type 'Null' is not a subtype of type 'List<dynamic>'`.
2. **It breaks web PDF export for papers that work today.** SQP items with
   bled-in answers raise `LayoutError`; stems yielding more than four option
   labels raise `IndexError`. Default 80-mark History XII, Social Science X,
   Home Science X and Geography XII papers export before the merge and return
   HTTP 500 after it.

And a merge alone would not reach class 6–9 on the web at all, because the
grade is mishandled three separate ways (§4).

## 2. What each source contributes

| | Board (served today) | CBE | SQP |
|---|---|---|---|
| Records | 3,286 | 720 | 1,834 |
| Grades | 10, 12 | **6, 7, 8, 9**, 10 | 10, 12 |
| New grade coverage | — | **the only source of 6–9** | none |
| Decodes on the phone | 3,286 | 461 | 0 |

## 3. Honest projection

A record is served only if it can be answered and rendered. Measured against the
CBE bank before implementation:

```
CBE classes 6-9: 533
  served                  369
  figure-unavailable       96   no `cbe-figure:` resolver exists on any surface
  passage-unavailable      48   English comprehension with no extracted passage
  mcq-answer-unresolved    20   correct option not recoverable (to be retried)

class 6: 75   class 7: 71   class 8: 75   class 9: 148
English 7 and 8: 0 until their passages are extracted
```

The final numbers are measured in Task 11 and reported with their shortfall.
They are not to be rounded up to 533 (rule Q4).

## 4. The web grade path is broken three ways

Production has no `registry.sqlite` (the image is built from a checkout that
does not track it), so every web request takes `build_pool`'s baked-bank
fallback. On that path:

1. `routes._int_grade_to_roman` knows only 8–12, so 6 and 7 fall to `"X"`. A
   class 7 teacher silently gets a class 10 board paper headed "Class: 7".
   **This is live in production today, independent of the merge.**
2. The fallback labels items 6–9 as `"6"`..`"9"`, while `_grade_matches` knows
   only `"10"`; requests for 8/9 arrive as `"VIII"`/`"IX"` and never match.
3. `mapping.grade_to_int` does `_ROMAN_GRADE.get(g, 10)`, so `"9"` reports
   itself as grade 10.

Fixing any one leaves wrong output. The design is one grade module used
everywhere, and an invalid grade becomes a 422 rather than a silent `"X"`.

## 5. The record contract

The phone's `Question.fromJson` is stricter than the Python `QuestionSchema`
(all 720 CBE records pass Python validation; 259 fail Dart). The two contracts
have already drifted, which CLAUDE.md warns nothing detects. So the merge
enforces the **Dart** contract, mirrored in Python, and a Dart test decoding the
real bundled asset is the authoritative gate.

Hard-required: `id, questionBankId, subject, grade(num), chapterIds[str],
competencyIds[str], bloomLevel, difficulty, type, stem, stemLatex, parts[],
answerScheme{}, estimatedTimeMinutes(num), marks(num), language, source,
qualityScore(num), tags[str], createdAt, updatedAt`. Each part needs `id,
partNumber, text, textLatex, marks, answerType`. The answer scheme needs
`totalMarks, markingPoints[], rubricLevels[], commonErrors[],
alternativeAnswers[], modelAnswer, modelAnswerLatex`; each marking point `id,
description, marks, keyword, isRequired`.

Four value sets **silently mis-default** on the phone rather than failing, so
presence is not enough — values are checked too: `bloomLevel` (default
`remember`), `difficulty` (`medium`), `type` (`short_answer`), `source`
(`ncert_textbook` — a provenance mislabel). `answerType` must be one of nine.

## 6. Design decisions

- **Board records pass through unchanged.** They already decode and render; the
  merge must not risk them. They are still validated.
- **MCQ options are written inline in the stem** as `(A) … (B) …`, with
  `parts: []`. Board MCQs already use this shape, the web PDF already splits it,
  and the phone prints it within the stem. Writing options into both the stem
  and `parts[0].options` would print them twice on the phone.
- **MCQ answer schemes reuse `question_bank.build_official_scheme`**, so a merged
  MCQ carries the same objective shape as a board MCQ
  (`metadata.objective/correctOption/options`, a marking point with the option
  as keyword and the letter as synonym). This is what makes on-device Scan &
  Grade and web auto-scoring work. An MCQ whose correct option cannot be
  recovered is excluded — no answer key, no question (rule Q1).
- **Inferred values are marked inferred.** SQP carries no Bloom level; the merge
  supplies one through `mapping._resolve_bloom` and records
  `metadata.bloomInferred = true`, so an inferred value is never readable as an
  authored one.
- **English passages ride with their question.** The CBE parser already extracts
  passages (60 of 151 English 6–9 items); `to_bank_record` was dropping them.
  They are emitted and prepended to the stem so each question is answerable on
  its own. Known cost: two questions from one passage print it twice (§8).
- **Excluded is recorded, never silent.** Every excluded record goes to
  `academicos-data/syllabus/_merge_excluded.json` with its reason.
- **A contract violation after normalisation fails the whole merge** and writes
  nothing. It indicates a normaliser bug, and per-record exclusion would hide it.
- **The served bank and the APK copy are written together and byte-identical.**
- **The merge refuses sources that carry no chapter tags.** Rebuilding a builder
  discards applied tags; merging then would ship class 6–9 with zero
  chapter-matched questions.
- **Web paper selection prefers board questions** at equal fit, so existing
  class 10/12 papers are not silently re-composed from sample-paper items.

## 7. Pipeline order

```
build_cbe_bank.py   build_sqp_bank.py
tag_question_bank.py
apply_chapter_tags.py
merge_question_banks.py        # new — composes the served bank + APK copy
enrich_question_bank.py
```

`export_mobile_corpus.py` wrote a registry-derived board-only corpus straight
over the APK asset, which would silently delete every merged record. It is
retired as a writer.

## 8. Out of scope — reported, not fixed

- A `cbe-figure:` asset resolver (would unlock 96 class 6–9 items).
- CBE items whose chapter is still a raw content code (`9N1e`, `ENG7.8`) rather
  than a syllabus chapter — about 46% of class 6–9. They are served and appear
  in whole-subject papers, but a chapter-scoped paper cannot select them. Task
  14 fixes the chapter *names* for the items that do carry a syllabus chapter.
- Passage grouping in the renderers (a shared passage prints once per question).
- Extracting English 7/8 passages.
- The textbook-edition mix in class 6–8 syllabus files.
- Class 11 — no source exists.
- **Building, signing and distributing a new APK, and republishing the
  `corpus-data` release** phones download from (already stale: 4.8 MB, older
  than the bundled asset, and nothing publishes it). Teachers see none of this
  work until that happens. These are outward actions that need the owner.
- A board-bank MCQ found in passing with an answer from a different question
  (`cbse:q:src:7c78ffa137e914e0b76bd4e2:5`, a hydrogenation stem carrying "(a)
  Tallness depends on the amount of plant hormone"). Pre-existing; tracked
  separately.
