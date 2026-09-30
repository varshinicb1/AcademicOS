# Transcribing a question paper with its official answers

The format every paper transcription follows: CBSE board papers, CBSE sample
papers, CBSE competency (CFPQ) question sets. A transcriber (a person, or a
vision model run through the Antigravity CLI) reads the question paper and its
official marking scheme / answer key and writes one JSON file. The code that
reads it is `src/academicos/corpus/transcribed.py`; it serves nothing on the
transcription's word (see "What happens next").

## Rules
1. **Transcribe; never invent.** Every question comes from the question paper,
   every answer from the official scheme. If something is unreadable, write what
   you can read and set `"unreadable": true` on that item.
2. English-medium text only (a bilingual paper: skip the Hindi).
3. Every question in the paper appears once, in order, including the "For
   Visually Impaired Candidates" variants (flagged). Their marks add up to the
   paper's total (visually-impaired variants excluded).
4. Value points are copied from the scheme **word for word** (join lines the page
   broke; nothing else). Their marks add up to the question's marks, or, when the
   scheme says "any N", set `anyN`.
5. A question that needs a map, picture, graph or table that is not fully written
   out in words gets `"needsFigure": true`.
6. Output valid JSON only (no comments).

## Format
```json
{
  "paper": {"board": "CBSE", "kind": "board", "year": 2024, "class": 10,
            "subject": "Social Science", "code": "32/1/1", "totalMarks": 80,
            "durationMinutes": 180, "generalInstructions": ["..."]},
  "questions": [
    {
      "number": "1",
      "section": "A",
      "marks": 1,
      "type": "mcq",
      "stem": "the question text as printed, without the option lines",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "passage": null,
      "parts": [{"label": "(i)", "text": "...", "marks": 1}],
      "alternative": null,
      "needsFigure": false,
      "visuallyImpairedVariant": false,
      "unreadable": false,
      "scheme": {
        "correctOption": "B",
        "points": [{"text": "...", "marks": 1, "part": null}],
        "anyN": null,
        "notes": null,
        "msPage": 3
      }
    }
  ]
}
```
- `kind`: `board` | `sqp` | `cfpq`.
- `type`: `mcq` | `assertion_reason` | `very_short_answer` | `short_answer` |
  `long_answer` | `source_based` | `case_based` | `map` | `diagram`.
- `options`: MCQ and assertion-reason only, else `null`.
- `passage`: the source or case text of a source-/case-based question.
- `parts`: sub-questions `(i)`, `(ii)` ... with their marks, else `[]`.
- `alternative`: an internal choice ("OR"): the same shape (stem, options,
  parts, scheme), without `number`.
- `scheme.correctOption`: the letter the scheme gives for an MCQ / A-R, else
  `null` (also `null` when the scheme withdraws the question, e.g. "marks to be
  given if attempted").
- `scheme.points[].part`: `"(i)"` when the point answers a part.
- `scheme.msPage`: the scheme page where this answer is.

## What happens next
`transcribed.build` turns each question (and each internal choice) into a source
record and refuses, with the reason, any that is:
- `unreadable`, `figure-unavailable`;
- an MCQ without four options (`options-missing`) or without a key
  (`mcq-answer-unresolved`);
- without value points (`no-answer`);
- `scheme-unverified`: a value point not found in the scheme's own text layer;
- `scheme-out-of-place`: value points found in the scheme, but not where this
  question's answer is (another question's answer copied in).

Half-mark points are joined into whole-mark points (the scheme format holds whole
marks). The records then go through every merge gate (`bank_merge.compose`), like
every other source.
