# Job: answer question-writing prompts, one file at a time

This folder is `D:\acos-wt\_ocwork`. Work ONLY inside it. Do not read, edit or create anything outside it.
Never start a server or a long-running process. You do not need python or any other program: read files, write files.

Each folder `<book>-<chapter>/` holds prompt files `p001.json`, `p002.json`, ...
Each prompt file is a JSON object with:
- `system`: the question-paper-maker rules. Follow every one of them exactly.
- `user`: the chapter text and what to write (how many questions, for which section).
- `schema`: a JSON Schema. Your answer must be a JSON object that satisfies it.

For every `pNNN.json` that has no matching `rNNN.json` next to it:
1. Read the prompt file.
2. Write the questions the `user` text asks for, following `system` and using ONLY facts the chapter text states.
3. Write `rNNN.json` next to it, containing ONLY the JSON object of the answer (shape: `{"questions": [ ... ]}`, each item with every field the schema requires). No markdown fences, no commentary, no extra keys.

Rules that matter more than speed:
- Write EXACTLY the number of questions the `user` text asks for ("Write N question(s)"), no more, no fewer.
- Every question carries `"evidence"`: an array of 1 to 3 quotes copied CHARACTER FOR CHARACTER from the chapter text in the `user` field (each at least 12 characters, from one line or a few joined lines), which together prove the correct answer. If you cannot quote proof for a question, do not write that question.
- Every number, year, name of a place/person/law and every figure in a question, option, model answer or marking point must be one that appears in the chapter text. Never add a statistic or fact from memory, even a true one. Distractor options may be names or numbers from elsewhere in the text, never invented figures.
- A question must make sense on its own: do not say "the table", "the data given", "the map", "the figure", "the above" unless the full table or map is reproduced in the question itself.
- Every question must be answerable from the chapter text alone; never refer to "the text", "the chapter", "the passage" or yourself.
- For mcq / assertion-reason: exactly four options A-D, exactly one correct, and spread the correct letter (do not default to A or B).
- For short/long answer: `markingPoints` is an array of separate points, one per mark, and the model answer covers each of them.
- `qtype` and `marks` must equal the schema's enum value exactly (marks is a STRING such as "1").
- `option` is the 1-based position of the question within this call.
- If the chapter text genuinely cannot support a question of that kind, write `{"questions": []}` rather than inventing facts.
- The text has page-layout noise (stray single words, table fragments). Ignore the noise; do not build a question on a fragment you cannot make sense of.

When every prompt has an answer, reply with one line: how many `r` files you wrote.
