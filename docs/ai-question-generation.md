# Generating the question bank, and why it is built this way

**Status:** working, measured on the real corpus on 2026-09-30. Supersedes nothing;
sits alongside the official-only builders, which remain the default for anything
lifted from a board paper or a book.

## The decision

The bank is generated from the NCERT chapter PDFs, one chapter at a time, into the
section shape CBSE actually prints. Not generated freely, and not generated into a
format of our own choosing.

The alternative considered first was to keep the bank official-only and spend the
effort on retrieving more board papers. Rejected: the official corpus is bounded at
roughly what CBSE has ever published, it is already harvested, and the gap is in
*practice* questions -- the ones a teacher sets from a chapter, in the board's own
sections -- not in past papers.

## Why the format lives in code and not in a prompt

A prompt cannot be checked. A language model asked to follow a format will report
having followed it whether or not it did, and the failure is invisible downstream
because each question still looks individually well formed.

So the format is `src/academicos/corpus/cbse_blueprint.py`, as data, per grade band
and per subject, and it is tested against the board's own arithmetic
(`tests/test_cbse_blueprint.py`, 31 tests):

- 80 marks of theory, 20 of internal assessment, every main subject.
- The sections are **per subject**, not one template. Social Science ends in a map
  section; Science spends four of Section A's twenty marks on assertion-reason; the
  language papers have no objective run over the syllabus at all, and are Reading 20,
  Grammar 10, Writing 10, Literature 40.
- The board's 50 / 20 / 30 split of competency, MCQ and subjective is *computed*
  from the sections rather than asserted, so editing a section count cannot silently
  break the ratio.
- An unregistered subject raises. A silent default is how a school prints a paper in
  a shape no marker has seen.

Two of those tests caught real errors in the first draft of the module: the language
papers summed to 66 marks, and the Class 1-5 paper was half one-mark questions. Both
were wrong and both were fixed in the data, not by relaxing the test.

## Why the model is Cloudflare Workers AI

Measured on the account, three runs each, same prompt, same schema:

| Model | Result | Neurons |
|---|---|---|
| `@cf/meta/llama-3.1-8b-instruct` | **3 of 3 failed** | 22 |
| `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 3 of 3 clean | 47-53 |
| `@cf/openai/gpt-oss-120b` | clean | 89 |

The 8B model never emitted a stop token, ran to `max_tokens` every time, and
produced output with no parseable JSON in it. It also routes to
`llama-3.1-8b-fast-v2` -- the *non-JSON* variant -- so the schema never reaches it. It
is 3x cheaper and it does not work. **The bulk/strong split this design started with
was removed**: there is one model, used everywhere, because the cheap one cannot be made
to follow the format.

What makes the 70B usable rather than merely cheap is **JSON Mode with `json_schema`**:
it routes to the `-json` variant, the blueprint's marks value goes into the schema as a
`const` and the type as an `enum`, and a question with the wrong marks cannot be produced
at all rather than being produced and caught.

That is the whole reason the format is data. A `const: 1` in a schema is a constraint
the model cannot talk its way around; a sentence in a prompt asking for one mark is not.

**Groq** is the fallback: free tier, 30 RPM, OpenAI-compatible, ~14,400 requests/day.

**No vector store.** A single NCERT chapter is 5-15 pages, roughly 2-10k tokens, and
these models take 128k. The chapter *is* the retrieval corpus, so "RAG" here is "put the
chapter in the prompt". A vector database would add a failure mode and cost for no
recall gain at this size. Revisit only if chapters are ever chunked.

## Cost, measured on a real chapter

One live run: `jemh1` chapter 1 (Real Numbers, 556 lines, 3 topics), planned at 12 marks.

- **12 calls, 913 neurons**, 7 questions kept, 7 refused.
- That is **~76 neurons per call** and **~913 per chapter** at a 12-mark budget.
- All 643 chapter PDFs at that budget is **~590,000 neurons, or about 59 days** at
  10,000 neurons/day.

Free is genuinely free, but it is slow. The 8B model would have made this 3x faster and
could not do the job, so the levers are elsewhere: a smaller per-chapter mark budget,
narrower topic windows (already 90 lines, centred on the topic), and a cron-driven
worker to grind through it unattended.

**That arithmetic is the honest answer to "absolutely free for grades 1-10":** reachable,
but it is a two-month unattended grind, not an afternoon.

## What the first real run got wrong

The first full run is the reason the validator exists, and it is worth reading. Of 12
calls on Real Numbers, the model produced good questions -- *"Show that 7 - sqrt(5) is
irrational"* with a correct contradiction proof, *"Find the LCM and HCF of 140 and 156"*,
correct sections and correct marking-point counts -- alongside these, every one of which
now has a check:

| What came back | Now |
|---|---|
| `"Find the LCM and HCF of 140 and 156 ... and verify that LCM x HCF = product"` | `premise-not-supported` |
| `"1. Find the HCF of 6, 72 and 120"` | number stripped from the stem |
| `"I. Is 5 - sqrt(3) rational? II. What property is used here?"` as one 2-mark item | `stem-is-several-questions` |
| `"7x13, 7x14, 7x15, 7x16"` as distractors | `distractor-ladder` |
| The whole of Section E, 4 of 4 refused | still broken, see below |

**The first row is the one that matters.** LCM x HCF = product only holds for coprime
pairs, so the question asked the student to prove something false about 140 and 156. The
model *computed it correctly* and answered by saying so -- and the question is still
unaskable, because the mark scheme would have to mark the right answer wrong. No schema
catches this, and neither does a shape check. A language model will cheerfully construct
a question with a false premise and then quietly contradict it in the answer.

The narrow check added for it (`_contradicts_its_stem`) reads the stem for
"show/verify/prove that" and the answer for a denial. It is deliberately word-based, not
arithmetic. It caught 1 of the 7 kept items on replay, and correctly kept the *same*
wording on 12 and 15, where the identity does hold.

**Section E is still broken: 4 of 4 refused.** The model does not understand that a
case-based section needs a passage *first* -- it returns another short question, so
`case-passage-too-short` fires every time. Case-based and source-based work is the
board's competency centrepiece and it is currently producing nothing.

**Bloom level is not controlled at all.** Every one of the 7 kept items came back
labelled `apply`, including a one-mark recall. The level is a hint in the prompt, not a
constraint, and the schema's `enum` cannot tie a level to the difficulty of the stem.

**Topic assignment is by rotation, not by content.** The plan walks the chapter's topics
in order, so the LCM/HCF questions land on `"Introduction"` because that was the next
topic to be filled, not because the material is there. The questions are sound; the tag
is wrong. The chapter id is right, because it now comes from the tree that named the
chapter -- an earlier version took it from `topics[0]` and filed everything under
`mathematics-10/introduction` when the chapter is Real Numbers.

## Why the validator is not the model

Schema compliance is not question quality, and the first live run proved it. Asked for
two one-mark MCQs on the Fundamental Theorem of Arithmetic, `llama-3.3-70b` returned:

- both keys on **A**, against an explicit instruction not to;
- distractors **7x13, 7x14, 7x15, 7x16** for the factorisation of 91 -- four distinct
  options, so the existing shape gate passed them, and a student who cannot factorise
  anything can still pick one;
- stems that trailed off: *"The prime factorisation of the number 12 is"*;
- both labelled `apply` when they are pure recall.

So `cbse_generate.validate` checks what a schema cannot see:

| Refusal | Catches |
|---|---|
| `stem-is-not-a-question` | trailing statements, and stems that ask for a form ("State the factors of 12") rather than testing anything |
| `distractor-ladder` | wrong options that are the answer walked by 1-3 |
| `stem-names-the-text` | "According to the text...", "In the chapter...", "As an AI..." |
| `options-not-answerable` | reuses the repo's existing `mcq_shape.answerable`, which was written for this and never wired in |
| `marking-points-do-not-match-marks` | a 3-mark question scored with 2 points |

And `audit_key_distribution` reports key position across a run. A single A is not a
fault; above 40% across a run it is a paper a student can score in without reading the
questions, so it is reported for retry or drop.

The three live-run failures are pinned in `tests/test_cbse_generate.py` so a regression
in any of them is caught by one test.

## What the topics come from

The **taxonomy trees**, for every grade. The classes 6-10 trees were read off the
books' own typography and point straight at the chapter PDFs; the classes 1-5 trees
were read off the transcriptions. Taking topics from the trees rather than the
transcriptions is what makes one code path cover grades 1-10 -- the transcriptions are
sparse above Class 5, with single chapters transcribed per book. Where no tree covers
a chapter, `textbook_headings.chapter_headings` reads the topics off the PDF's own
typography, which works for numbered (senior) and unnumbered (primary) schemes alike.

Chapter text is read through `textbook_headings.read_lines`, not `get_text()`. This is
not a detail: an NCERT heading wraps ("Chemical Reactions" / "and Equations") and drop
capitals arrive as a bare `C` followed by `onsider`. Raw `get_text` returns those as
separate lines, so **no heading matches itself** and every topic silently falls back to
the whole chapter -- which is exactly what happened on the first run, with 2-line
windows. `printed_page_numbers` also gives the page the book prints rather than the
page's position in the file, which is the difference between citing page 7 and citing
something no marker can find.

## Who may call the Workers, and what they may spend

Both Workers sit on public `workers.dev` hostnames, so every route that calls a model
or hands out generated questions needs `Authorization: Bearer <token>`:

- `qbank`: `/api/topics`, `/api/generate` and `/api/papers` need `QBANK_TOKEN`.
- `academicos-qgen`: `/run` and `/probe` need `RUN_TOKEN`. The 02:17 cron needs none.

With no token secret set those routes answer 503, so a fresh deploy is closed, not open.
Set the tokens once per Worker, then pass the same value to `scripts/finalize_bank.py`
as `QBANK_TOKEN` in the environment:

```bash
openssl rand -hex 24 | npx wrangler secret put QBANK_TOKEN --name qbank
openssl rand -hex 24 | npx wrangler secret put RUN_TOKEN --name academicos-qgen
```

Spend stops hard on both paths:

- Without a Gemini key, at the 9,000-neuron daily allowance.
- With `GEMINI_API_KEY`, at `DAILY_USD_CAP` dollars a day (default $2), reset at 00:00 UTC.

One request asks for at most 20 questions.

## What is still needed, in priority order

1. **Independent answer verification.** Generate with one model, verify with another,
   blind -- the ensemble pattern from QUEST-AI, and the answer to both the false-premise
   problem and Bloom mislabelling. `solve2.py` already does blind second solves for the
   official corpus and is the obvious thing to reuse. This is the single highest-value
   remaining piece.
2. **Fix Section E.** The prompt asks for a passage and gets a question. Either a
   two-call shape (passage first, then questions on it) or a schema that makes the
   passage a required leading field.
3. **Derive Bloom from the stem** rather than asking for it, and check the two agree.
4. **Tag by content.** Ask which topic the question came from, or match the evidence
   span against the topic's pages, instead of rotating.
5. **Human review.** Competitors run an SME loop over generated items -- Physics Wallah's
   is the clearest example. Without one these are drafts, and the doc should say so.

## What is not done

- No generated question reaches the served bank. Output goes to
  `academicos-data/corpus/ai-cbse/questions.json`, which the merge reads like any other
  corpus, so a generated chapter is reviewable before it is served.
- Every record carries `source: ai_generated` and a `provenance` block naming the
  model, the section and the pages. A generated question can never be mistaken for one
  lifted from a board paper.
- NCERT content rights are unresolved and are not a technical problem. This decides
  whether the bank can be sold at all, and nothing here changes that.
- No human review step is built. Competitors run an SME loop over generated items
  (Physics Wallah's is the clearest example); without one, generated questions should
  be treated as draft until a teacher has seen them.
