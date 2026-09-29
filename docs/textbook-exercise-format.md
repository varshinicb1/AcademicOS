# Transcribing NCERT textbook exercises, with answers that can be checked

Classes 1-10 textbooks print their exercises inside each chapter, and (apart
from some Mathematics answer pages) no answers. This format takes one chapter's
exercises with an answer for each, and says where each answer comes from, so
the builder (`src/academicos/corpus/textbook.py`) can check it before anything
is served. One JSON file per chapter.

## Rules
1. **The questions are the book's.** Transcribe every exercise question in the
   chapter (end-of-chapter exercises, "Let us do", "Figure it out", "Think and
   answer", comprehension questions after a story or poem) exactly as printed.
   Never write a question of your own.
2. **Every answer says its source** (`answer.source`):
   - `book` -- the book prints the answer (an answers page, a worked example).
   - `grounded` -- the answer is stated in the chapter's own text. Every value
     point carries `evidence`: a sentence copied **word for word** from the chapter
     that states it, and the page. A point with no such sentence is not written.
   - `solved` -- a Mathematics, grammar or vocabulary answer worked out, not
     stated in the text (sums, fill in the blanks, word meanings). Give the working
     and the `finalAnswer`. These are checked by a second, independent solve.
   - `open` -- the question has no single answer (opinion, "discuss with your
     friends", "find out from your elders", draw, act out, project, activity).
     Transcribe it, give no answer. It is kept for teachers, never keyed.
3. `needsFigure: true` when the question depends on a picture, diagram, map,
   table or graph that is not fully written out in words.
4. English-medium books in English; Hindi books in Hindi (Devanagari), as printed.
5. Output valid JSON only.

## Topics, and new questions for every topic
The same file also carries the chapter's **topics** and **new questions written for
each topic**, so every chapter and every topic has questions, not only the few the
book prints.
- `topics`: the chapter's sections in order, from its own headings (a chapter with
  no headings: its natural parts). Each has an `id` ("t1", "t2", ...), the heading as
  printed (`title`), and `startsWith`: the first sentence of that section, copied word
  for word.
- Every question names its `topic` (a topic id) and its `origin`: `"book"` for the
  book's own exercises, `"generated"` for a question you write.
- **Generated questions** test what that topic's text teaches -- facts, concepts,
  reasoning, application -- at the class's level and in the book's language (Hindi
  books: Hindi). Per topic, write:
  - classes 1-2: 4 questions (MCQ, fill in the blank, true/false, very short);
  - classes 3-5: 5 questions (2 MCQ, 1 fill in the blank or true/false, 2 very short/short);
  - classes 6-10: 6 questions (2 MCQ, 1 very short, 2 short, 1 long or case-based).
  Each carries `difficulty` (`easy` | `medium` | `hard`) and `bloom` (`remember` |
  `understand` | `apply` | `analyze` | `evaluate` | `create`).
- A generated question's answer is `grounded` (every point with an `evidence`
  sentence copied word for word from the chapter) or, for a sum or a grammar item,
  `solved` (working and `finalAnswer`). Never `open`. An MCQ's distractors are wrong
  by the chapter's own text, and exactly one option is right.
- Do not copy a book exercise as a generated question.

## Format
```json
{
  "book": {"code": "fegp1", "class": 6, "subject": "Mathematics", "title": "Ganita Prakash",
           "language": "en"},
  "chapter": {"number": 1, "title": "Patterns in Mathematics", "file": "<chapter PDF path>"},
  "topics": [{"id": "t1", "title": "What is Mathematics?", "startsWith": "exact first sentence"}],
  "questions": [
    {
      "ref": "Figure it Out 1.2 Q3",
      "origin": "book",
      "topic": "t1",
      "difficulty": "medium",
      "bloom": "apply",
      "page": 12,
      "type": "short_answer",
      "stem": "...",
      "options": null,
      "passage": null,
      "parts": [{"label": "(a)", "text": "..."}],
      "needsFigure": false,
      "answer": {
        "source": "grounded",
        "correctOption": null,
        "points": [{"text": "...", "evidence": "exact sentence from the chapter", "page": 11,
                    "part": null}],
        "working": null,
        "finalAnswer": null
      }
    }
  ]
}
```
- `type`: `mcq` | `true_false` | `fill_blank` | `match` | `very_short_answer` |
  `short_answer` | `long_answer` | `case_based`.
- `options`: an MCQ's `{"A": ..., "D": ...}` (relabel a book's (a)-(d) as A-D), else `null`.
- `passage`: the text a comprehension question is about, when it is not the whole chapter.

## What the builder checks
- a book question's stem is in the chapter's text layer (`stem-not-in-book`); a
  generated one's is not required to be, but its answer must be grounded or solved;
- every `grounded` point's evidence is in the chapter's text (`evidence-not-found`);
- a `solved` answer agrees with an independent second solve (`solve-disagrees`);
- `open` and `needsFigure` questions are kept out of the served bank.

Marks are not printed in textbooks. The builder gives a question the marks its
type usually carries in a CBSE paper (MCQ, true/false, fill-in-the-blank 1;
very short 1; short 2; long 5; case-based 4) and flags them `marksInferred`, like
every other value the source did not print.

Answers from `grounded` and `solved` carry that provenance to the teacher
(`answerScheme.provenance`), next to the official schemes.
