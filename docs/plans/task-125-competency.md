# Task 125 — the competency share is real, and a paper that cannot reach CBSE's 50% says so before it prints

**Status at handover (2026-09-27): in progress on branch `feat/task-125` (pushed), NOT merged, NOT deployed.**

| Group | Plan steps | State |
|---|---|---|
| 1 rule | 1-2: one competency rule in `assessment/competency.py` (CBE item-bank provenance, printed type, printed Assertion/Reason labels; never Bloom, never marks); registry-built types flagged `typeInferred` | done, spec + quality reviews approved (commits 2024d62, 3bc8d7b) |
| 2 engine | 3-4: template engine and swap/pick use the one rule; odd-set OR swap prints the alternative as its own record | done, approved (a34155d, 11276dd) |
| 3 selection | 5-6: tier signals ignore CBE-supplied values; `selection.tiers_note`; "cannot reach CBSE's 50%" warning before selection | done, approved after one fix round (27b915d, a597e9e, 7287dc3) |
| 4 availability | 7: `CompetencyCheck` / `TierCheck` on the builder's availability report; template papers carry the share | committed (5e90119); **one open MAJOR review finding, below** |
| 5 health | 8-9: difficulty-mix note only for judged difficulties; competency section in the bank health report | not started |
| 6 web | 10-11: builder step 3 shows the competency line and tier sentence; `/assessment/create` redirects to the builder on the web | not started |

**Open MAJOR finding on group 4 (fix it first):** after a swap, pick or remove, `paper_edit._restamped`
(paper_edit.py:367-376) recounts `competencyShare` / `competencyTargetMet` but leaves the generation-time
competency sentences in `paper.warnings`, which the web paper step renders -- so after an edit the only share a
teacher sees can contradict the paper (e.g. "Below CBSE's 50%" while the share is 50%). Fix: when `_restamped`
recounts, drop the generation-time "Competency-based: ..." sentence and "Set X has ...%" lines, re-add the per-set
lines from the recount in `report_competency`'s wording, and add the below-target sentence only if still below
(without the whole-syllabus clause, which needs a plan). Tests: route tests for remove and swap asserting that
`paper.warnings` agrees with the recounted share. Three minor findings (below_bank vs `competency_ceiling`, a
topic-only scope test, duplicate share formats) are optional.

Paths below under `scratchpad/` (t125/*.py measurement scripts) were the author's working files on the old
laptop and are not in the repo; the numbers they produced are quoted in the plan.

Before merging: run BOTH full suites on the branch (Python ~20 min, Flutter ~3 min, one at a time), then follow
docs/deploy-by-hand.md. Expected effect is in "EXPECTED NUMBERS" below; re-measure, don't quote.

---

FINAL PLAN, Task 125: the competency share is real, and a paper that cannot reach CBSE's 50% says so before it prints.

Repo: C:/Users/varsh/OneDrive/Documents/Sarvam/AcademicOS-release, branch feat/term-insights @ f9ead42. All paths below are relative to it.
- Spine: the minimal plan.
- From the teacher plan: the step-3 status design (meets / below_scope / below_bank), the tier sentence placement, the difficulty-mix fix, and stamping the share on template papers.
- From the provenance plan: flag every registry-built type as supplied; report_competency moves into paper.py; the answer-key consequence of the swap fix.
- Constraints: no new route (so no route_policy row); no bank rebuild; no edits to pillar_routes.py, cbse_syllabus.py or tests/test_catalog_chapters.py.
- Start only after the running suite finishes.

Re-verified for this plan (scratch scripts in scratchpad/t125, output quoted):
- v_sel.py: board-80 picks are identical in 10 of 14 cells.
- v_ar.py: 2 served assertion-reason stems.
- v_mix.py: 150, then 168 difficulty-mix notes.
- v_mix2.py: 0 notes carry a judged difficulty.
- min_or_pairs.py: 16 of 40 template OR pairs mixed.

== STEP 1. One rule, in a leaf module ==
Files:
- src/academicos/assessment/competency.py (new)
- selection.py
- schemas.py
- routes.py
- tests/test_competency_rule.py (new)

competency.py imports nothing from the package. That avoids the paper_templates/selection import cycle (paper_templates.py:339 imports lazily today) and keeps bank_health from pulling in pool.py. It holds:
- CBE_ITEM_BANK_PREFIX = "cbe:". The prefix is written at cbse_cbe.py:1023. Source page: https://cbseacademic.nic.in/cbe/assessment.html. Page 1 of every Maths/Science item-bank PDF reads "Competency-based education for CBSE".
- COMPETENCY_TYPES = {case_study, assertion_reason, competency_based}.
- CBSE_COMPETENCY_TARGET = 0.50.
- COMPETENCY_RULE_TEXT.
- competency_signal(q), which takes a QuestionSchema or a camelCase Mapping and returns the first signal that holds:
  - "cbeItemBank" when questionBankId / question_bank_id starts with "cbe:";
  - "competencyType" when the type is in COMPETENCY_TYPES and metadata.typeInferred is not set;
  - "assertionReasonLabels" when the stem carries both CBSE labels. Test re.search(r"\bAssertion\s*\(A\)") and re.search(r"\bReason\s*\(R\)") separately, so order does not matter;
  - otherwise None.
- is_competency_question(q) = competency_signal(q) is not None.

What the rule never reads:
- Bloom level: 'understand' on 5,429 of 5,429 records.
- The metadata flags is_competency / cbq: nothing writes them.
- Stem phrases or _CASE_RE: 56 of today's template-rule hits are text our merge prepends (bank_merge.py:1256-1259), and 13 are Exemplar 'Read the following statements'.
- Marks.

Changes to existing files:
- selection.py:34-47 re-exports is_competency_question and competency_signal from competency.py and loses its own body.
- Delete the dead selection.competency_share (:50-54; grep finds no caller).
- schemas.py:92 and :106 default to CBSE_COMPETENCY_TARGET.
- routes.py:486 and :356, and selection.py:194-196, use the constant instead of the literal.

Failing tests. Each case runs on both the dict and the QuestionSchema form, and the two must agree:
- A record with qbid 'cbe:Item-Bank---Maths-Class-6.pdf', type long_answer, Bloom understand counts, with signal 'cbeItemBank'. Today it does not (0 of 435 CBE records count).
- Bloom apply, analyze, evaluate or create on a plain record does NOT count. Today it does (:38).
- These stems do NOT count:
  - 'Read the following statements about diseases';
  - bank_merge's 'Read the passage below and answer the question that follows.';
  - the SQP Maths (Standard) Q35 run-on '... Section E consists of 3 case study based questions';
  - 'The assertion that ... for this reason'.
- case_study with typeInferred True does NOT count. Without the flag it counts as 'competencyType'.
- metadata {'cbq': True} does NOT count.
- The real SS10 Q23 stem typed mcq, and a Reason-first stem, both give 'assertionReasonLabels'.
- An Exemplar record labelled 'Short Answer Questions with Reasoning' does NOT count.
- Blueprint(...).competency_percentage == CBSE_COMPETENCY_TARGET == 0.5.
- @needs_real_bank: across served class 6-10 records, the signal counts are {'cbeItemBank': 435, 'assertionReasonLabels': 2} and 0 ncert_exemplar records count.
- tests/test_assessment_parakh_cbse.py:150-161 stays green: its 'cbq' fixture is typed competency_based and carries no flag.

== STEP 2. The registry path says its type was supplied ==
File: mapping.py:120-148. to_question_schema sets metadata.typeInferred=True on every record it builds from extraction:
- the type is either the keyword guess (extract/academic.py:89-99: 'passage' becomes case_study),
- or the marks fallback (mapping.py:71-83: 5 marks or more becomes case_study).

Baked records are returned as-is (:109-113).

Failing tests, in tests/test_paper_generation_honesty.py next to :181-193, using the same PoolQuestion pattern:
- marks=5.0 and no question_type gives type 'case_study', typeInferred True, and is_competency_question False.
- Question(question_type='case_study') gives typeInferred True and not competency-based.

== STEP 3. The template engine and swap/pick use the one rule ==
Files:
- paper_templates.py
- paper_edit.py
- tests/test_paper_templates.py

Changes:
- Delete _is_competency (paper_templates.py:338-340). Callers call is_competency_question: :476, :532, :534, :679, :685, :770, :773, :857.
- :477 is kind evidence and becomes `is_map_question(q) or is_case_question(q) or is_competency_question(q)`.
- is_case_question stays, only as the kind check in _content_fits (:343-363) and _admitting_type.
- paper_edit.py: update the import at :63-64 and the calls at :274 and :352.

Fixture updates:
- case{i} (:765) and case0 (:904) become type 'case_study' with no flag.
- The mark-derived labels get typeInferred: long{i}, map{i}, map5, plain4, plain5, and the a/b/c filler.
- :1006 imports is_competency_question.

New failing test, test_a_source_stem_alone_is_not_a_competency_signal:
- On SS10 annual, three 4-mark items with SOURCE stems, typed long_answer, qbid 'fixture', leave Section E with shortfall 3 and a reason that names competency.
- The same three items with qbid 'cbe:x.pdf' fill it 3 of 3.

Re-run :803, :821, :880, :901 and :994.

== STEP 4. The odd-set OR swap prints the alternative as its own record ==
File: paper.py:200-212. This is the template path's rotation_groups (paper_template_routes.py:403).
- When metadata['internal_choice_question'] exists, rebuild the printed question with QuestionSchema.model_validate(dump). selection.py:314 and paper_template_routes.py:463 both write that dump.
- Point the new record's four choice keys back at the old primary.
- Keep the stem/id/scheme swap only as a fallback when the dump is absent.
- This also corrects the set B/D answer keys. Today they print the primary's marking points under the alternative's model answer (answer_key_entry, paper.py:258-270).

Failing test:
- Primary P: qbid 'cbe:x.pdf', long_answer, 3 marks. OR partner Q: Exemplar short_answer, 3 marks, attached with selection._attach_choice.
- generate_paper_sets(set_count=2, rotation_groups=[[P]]).
- Set B's slot has questionId == Q.id, isCompetency False, type short_answer, and internalChoiceQuestionId == P.id.
- Set A shows P with isCompetency True.
- It fails today: set B prints Q's stem under P's qbid and type, flagged True.

== STEP 5. Tier signals ignore values CBE supplied ==
File: selection.py.
- difficulty_signal and bloom_signal (:75-87) return None when question_bank_id starts with 'cbe:'. The importer writes the default Bloom (cbse_cbe.py:950-954) and derives difficulty from marks (:957-963), and flags neither.
- Add selection.tiers_note(grade, subject) -> str: "Foundation and Advanced versions are not offered: in the Class {g} {subject} bank, questions of the same marks do not differ in a difficulty or Bloom level anyone judged (the bank sets them from marks), so every version would print this same paper."
- Keep optimize's existing tier warning (:368-373) unchanged, because TIERS_UNAVAILABLE pins its prefix.

Failing test:
- Six 1-mark _q records with question_bank_id 'cbe:x.pdf', three easy and three hard.
- tierSignals == {'available': False, 'difficultyLevels': 0, 'bloomLevels': 0}.
- test_paper_generation_honesty.py:195-207 stays green, because its qbid is 'bank'.

== STEP 6. Warn before selection on the blueprint path ==
Files:
- competency.py
- selection.py
- tests/test_competency_rule.py
- tests/test_paper_generation_honesty.py

competency.competency_ceiling(sections) is duck-typed. Each section is (count, in_scope_fit_ids, fallback_fit_ids). Walk the sections in order with a shared taken-set. Each section holds:
- min(count, unused competency in-scope fits), plus
- min(max(0, count - in-scope fits), unused competency fallback fits).
The fallback only fills a shortfall (selection.py:250-263).

In optimize(), before the section loop (after :201):
- When usable questions exist and ceiling/asked < target, insert as warnings[0]:
  "This paper cannot reach CBSE's {T}% competency-based share: its sections can hold at most {c} competency-based question(s) of the {asked} it asks for ({p}%). Of the {u} question(s) in the bank these sections can use, {k} ({p2}%) are competency-based."
- Add the metrics competencyCeiling, competencyUsable, competencyInBank and competencyTarget.
- Keep the post-selection sentence (:361-366). It reports a different fact: the printed share.

/questions/optimize (routes.py:250-260) is the dry run. Quick-generate carries the sentence first because it copies warnings (:533).

Failing tests:
- One 1-mark section of 4, with 1 CBE and 5 plain questions. warnings[0] must be exactly: "This paper cannot reach CBSE's 50% competency-based share: its sections can hold at most 1 competency-based question(s) of the 4 it asks for (25.0%). Of the 6 question(s) in the bank these sections can use, 1 (16.7%) are competency-based."
- The same pool with 3 CBE gives no such warning.
- Chapter-scoped with 4 plain in scope plus 3 CBE in the fallback gives ceiling 0; with 2 in scope, ceiling 2.
- An empty pool gives no pre-warning.
- Quick-generate on _plain_pool with class_test: the 'cannot reach' sentence comes before 'Selected paper has'. Derive its numbers from EXAM_PRESETS['class_test'].

== STEP 7. The builder's availability report carries the real share and the tier answer; template papers carry the share ==
Files:
- paper_templates.py
- paper_template_routes.py
- paper.py
- routes.py
- paper_edit.py
- tests/test_builder_competency.py (new)

New Camel models in paper_templates.py:
- CompetencyCheck:
  - status: meets / below_scope / below_bank;
  - target, printed, competency_based, share;
  - whole_syllabus_printed and whole_syllabus_competency_based (Optional);
  - bank_usable, bank_competency_based, bank_share;
  - by_signal;
  - summary, detail, counted.
- TierCheck: available, sentence.
- AvailabilityReport (:186-194) gains competency: Optional[CompetencyCheck] = None and tiers: Optional[TierCheck] = None.
- `complete` is untouched. It drives allowGaps (paper_builder_controller.dart:504) and the 409.

Pure function competency_check(template, plans, keyed, whole_plans, target):
- printed = picked + borrowed; the denominator is printed questions, as in routes.py:359.
- bank_usable = keyed class/subject questions that _fits some section.
- Returns None when nothing prints.
- Status:
  - meets when share >= target;
  - below_scope when share < target, the scope names chapters, and the whole-syllabus plan would reach the target;
  - otherwise below_bank.
- Percentages round half-up to whole numbers.

Sentences:
- summary: "Competency-based: {c} of {n} questions ({p}%)".
- detail, meets: "CBSE asks for at least 50%."
- detail, below_scope: "Below CBSE's 50%. The whole syllabus would give {wc} of {wn} ({wp}%)."
- detail, below_bank: "Below CBSE's 50%. The Class {g} {subject} bank cannot reach it with this template: {bc} of the {bu} questions it can use ({bp}%) are competency-based."
- counted: COMPETENCY_RULE_TEXT.

paper_template_routes._plan (:328-342):
- When the scope names chapters, topics or subtopics, run plan() a second time with TemplateScope() and the same stale set. Cost 8-19 ms (ux_timing.py).
- Attach competency_check, and TierCheck(tier_signals(keyed, section marks)['available'], tiers_note(...)).

Move routes._report_competency (:347-366) to paper.report_competency, and call it from routes.py :431, :535, :669 and from generate_from_template.

generate_from_template (:364-445):
- Sets paper.tiers_available from TierCheck. Today it is null (fixture generate_from_template_10_maths_unit_test.json:239).
- When status != meets, appends f"{summary}. {detail}" to paper.warnings, which paper_step.dart:83-84 already renders.

paper_edit.replace_question (:365-388) recomputes competency_share for the paper and its sets when it was set. Otherwise the swap/pick flow would leave the new field stale.

Failing tests:
- Synthetic chapter scope with no CBE: below_scope, with exact summary and detail.
- Whole syllabus: meets.
- Too few CBE: below_bank, naming the bank's share.
- report.complete is identical with and without the check.
- On supplied difficulties, TierCheck.available is False with the exact sentence.
- TestClient: /availability JSON has competency.status, summary and detail, and tiers.available false.
- generate-from-template (allowGaps) returns paper.tiersAvailable False (not null) and competencyShare == competency.share, with the sentence in warnings.
- A swap of a CBE question for a plain one lowers competencyShare.
- test_availability_equals_generation_for_every_class_10_preset_on_the_real_bank (:964-990) must stay green: the sentence goes to warnings, not notes.
- @needs_real_bank:
  - 10 Science half_yearly on the six manifest chapters: 'Competency-based: 8 of 30 questions (27%)' / 'Below CBSE's 50%. The whole syllabus would give 25 of 33 (76%).'
  - 6 Science annual, whole syllabus: '11 of 37 questions (30%)' / '... 11 of the 242 questions it can use (5%) are competency-based.'
  - 10 Mathematics annual: meets, 37 of 38 (97%), and Section E filled 3 of 3.

== STEP 8. The difficulty-mix note stops blaming the bank for a marks-derived value ==
File: paper_templates._mix_notes (:846-854).
- Emit the 'difficulty is easy/medium/hard ... the bank has too few at the requested level' note only when at least one picked question has a selection.difficulty_signal.
- Otherwise it contradicts the tier sentence on the same screen.
- _pick output is unchanged.

Measured: 168 of 170 class 6-10 Maths/Science preset sections carry the note under the new rule (150 today), and 0 of those 168 have a judged difficulty among their picks (v_mix.py, v_mix2.py).

Failing tests:
- A section whose picks all carry difficultyInferred or a 'cbe:' qbid gets no note.
- Two authored difficulties still produce the note.

== STEP 9. Bank health report ==
Files:
- src/academicos/syllabus/bank_health.py
- scripts/bank_health.py
- tests/test_bank_health.py
- docs/bank-health.md and academicos-data/syllabus/bank_health.json, regenerated only.

Import competency_signal and competency_ceiling; keep no local copy (the has_answer_key pattern, :85-86).

In _cell (:181-247), add cell['competency'] after 'types' (:216):
- {'all': block(keyed), 'served': block(served keyed)}, where block = {n, competency, pct, bySignal, byMarks via _buckets};
- refusedCbe only when exclusions are given.

In _paper_verdicts (:131-149), add per preset {usable = union of fit, competency, pct, need, ceiling, ceilingPct}.

report['competency'] = {rule, target}.

In render_markdown:
- Add '## Competency-based questions' after '## Answer keys' (:489-502). It opens with the rule sentence: no Bloom read, and no Exemplar heading says competency.
- Add a table of served cells.
- Add the lines 'Share below CBSE's 50% (N)' and 'Board paper cannot reach 50% (N)'.
- Add a clause on each preset line (:515-527).
- Empty cells print no share.
- Say that Mathematics 10 counts subject-family records (396) while the pool draws on 340 (pool.py:741).

Add a cbq% column in scripts/bank_health.py:121-128.

Failing tests, on BANK and TINY (:83-89):
- a1 with qbid 'cbe:x' gives Mathematics 7 competency.all {n 6, competency 1, pct 16.7}.
- Bloom 'apply' does not count.
- An A-R-labelled mcq counts as 'assertionReasonLabels'.
- case_study with typeInferred does not count.
- TINY with a1 as CBE: 'ones' gives usable 2, competency 1, pct 50.0, ceiling 1 of 2; 'tiny' gives usable 3, ceiling 1 of 3.
- The served/all split follows the :212-219 pattern.
- An empty cell prints no share.
- The Markdown carries the section and both lines.

Run: `python scripts/bank_health.py --check` (quote its output), then the real run. Expect only builtAt and the new keys to differ.

== STEP 10. The web builder shows it at step 3 ('Chapters'), where scope can still change ==
Files:
- frontend/lib/data/datasources/api/paper_builder_api.dart
- frontend/lib/presentation/paper_builder/widgets/scope_step.dart
- scripts/capture_paper_builder_fixtures.py
- frontend/test/paper_builder/ (new fixtures and tests)

AvailabilityView (:293-312) parses competency into CompetencyCheckView? and tiers into TierCheckView?, null-safe:
- numbers as `(x as num?)?.toDouble()`;
- strings as `as String? ?? ''`.
The contract audit checks paths only.

AvailabilityPanel shows _CompetencyLine right after the summary Row and the fill-from-outside line (scope_step.dart:154-176):
- ValueKey('availability-competency');
- icon: check / info / warning for meets / below_scope / below_bank;
- the summary line, then the detail line, then the counted line in the below states;
- never inside the collapsed ExpansionTile (:187-202).

Under the 'Question sets' SegmentedButton (:44-56), when tiers is present and not available, show Text(tiers.sentence) with ValueKey('availability-tiers').

The step re-checks on every scope change (paper_builder_controller.dart:274-285, :380-396, :447-456), so the line updates without new controller logic.

Capture script:
- Add --only NAME[,NAME]. save() skips other names and merges manifest.json instead of rewriting it.
- Capture:
  - availability_10_science_half_competency: half-yearly, the six chapter ids copied from the committed manifest;
  - availability_10_science_all_competency;
  - templates_6_science, chapters_6_science and availability_6_science_annual_all.
- Leave the stale 2026-09-22 captures alone.

Tests:
- A new testWidgets wraps FixtureAdapter the way _Refusing does (builder_errors_test.dart:63-92), answering only the new captures.
- Class 10 Science, 'Use' half-yearly, tick the six chapters:
  - 'availability-competency' shows 'Competency-based: 8 of 30 questions (27%)' and 'Below CBSE's 50%. The whole syllabus would give 25 of 33 (76%).';
  - 'availability-tiers' shows the sentence;
  - calls(api, 'POST', generate) is empty;
  - expectPhoneReady holds at 375x812.
- Tap 'Whole syllabus': the line shows 'Competency-based: 25 of 33 questions (76%)' and 'CBSE asks for at least 50%.'
- Class 6 Science annual: the below_bank text is visible without expanding the notes.
- Parse test: the committed availability_10_science_all.json, which has no new keys, gives competency == null and no row.

== STEP 11. No silent three tiers on the web ==
Files:
- frontend/lib/core/routing/app_router.dart
- frontend/test/routing/legacy_create_redirect_test.dart (new)

Add a pure `String? legacyCreateRedirect({required bool offlineBuild})`: '/assessment/build' on the web build, null offline. Use it as the 'create' GoRoute's redirect (:151-155). authRedirect stays untouched.

Why: the Foundation/Standard/Advanced control (assessment_create_page.dart:507-519) is the only tier choice on the web. It is reachable only by URL (newPaperLocation, paper_builder_page.dart:19-23), and tiers are unavailable in 14 of 14 served cells.

Tests:
- The function returns '/assessment/build' on web and null offline.
- auth_redirect_test.dart stays green.
- assessment_create_page_test.dart pumps the page directly and is unaffected.

== STEP 12. Verify and ship ==
1. Targeted pytest runs: test_competency_rule, test_assessment_parakh_cbse, test_paper_templates, test_paper_generation_honesty, test_paper_swap_pick, test_pool_record_fidelity, test_builder_competency, test_bank_health, test_route_inventory. Then the full suite.
2. bank_health --check, then the real run.
3. The capture script with --only.
4. flutter test test/paper_builder test/routing test/auth_redirect_test.dart, then flutter build web. Beware the stale build/web trap.
5. Merge, push and deploy (web-first, authorised 2026-09-22).
6. Screenshot step 3 on vidyuthlabs.web.app at 375 px for 10 Science half-yearly with the six chapters, and for 6 Science annual. The on-screen text must match the step-7 sentences.

No bank rebuild: questions.json and frontend/assets/corpus/questions.json stay byte-identical.

== EXPECTED NUMBERS ==
Source: served bank academicos-data/syllabus/questions.json (composedAt 2026-09-23). Measured by min_expect.out and v_sel.py.

A. Served keyed share (pool subject)

| Cell | Today (selection rule) | After |
|---|---|---|
| Maths 6 | 0/555 | 42/555 (7.6%) |
| Maths 7 | 0/573 | 25/573 (4.4%) |
| Maths 8 | 0/857 | 40/857 (4.7%) |
| Maths 9 | 3/289 (1.0%) | 62/289 (21.5%) |
| Maths 10 | 0/340 | 76/340 (22.4%) |
| Science 6 | 3/247 (1.2%) | 15/247 (6.1%) |
| Science 7 | 6/335 (1.8%) | 26/335 (7.8%) |
| Science 8 | 1/418 (0.2%) | 19/418 (4.5%) |
| Science 9 | 0/457 | 38/457 (8.3%) |
| Science 10 | 0/504 | 36/504 (7.1%) |
| English 6 / 9 / 10 | 0% | 7/7, 39/39, 10/10 |
| Social Science 10 | 1/14 | 1/14 (7.1%) |

- Bank health counts subject families, so Maths 10 reads 76/396 (19.2%) and English 10 reads 10/12 (83.3%).
- Share below 50%: 11 of 14 cells.
- Hindi 6-10 and Social Science 6-9 have no served questions.

B. Board-80 usable share, and the most competency questions a paper could hold (of 38)

| Cell | Usable share | Most of 38 |
|---|---|---|
| Maths 6 | 41/554 (7.4%) | 32 (84.2%) |
| Maths 7 | 25/573 (4.4%) | 25 (65.8%) |
| Maths 8 | 40/857 (4.7%) | 35 (92.1%) |
| Maths 9 | 54/281 (19.2%) | 38 (100%) |
| Maths 10 | 67/331 (20.2%) | 37 (97.4%) |
| Science 6 | 12/244 (4.9%) | 12 (31.6%) |
| Science 7 | 18/327 (5.5%) | 18 (47.4%) |
| Science 8 | 17/416 (4.1%) | 14 (36.8%) |
| Science 9 | 28/447 (6.3%) | 28 (73.7%) |
| Science 10 | 25/493 (5.1%) | 25 (65.8%) |
| English 6 | 7/7 | 7 (18.4%) |
| English 9 | 39/39 | 20 (52.6%) |
| English 10 | 10/10 | 10 (26.3%) |
| Social Science 10 | 1/14 | 1 (2.6%) |

The 'cannot reach' warning fires before selection for Science 6, 7 and 8, Social Science 10, English 6 and English 10.

C. Quick-generate board-80, printed share (today, then after)

| Cell | Today | After |
|---|---|---|
| Maths 6 | 0% | 88.9% |
| Maths 7 | 0% | 73.5% |
| Maths 8 | 0% | 97.1% |
| Maths 9 | 7.9% | 81.6% |
| Maths 10 | 0% | 94.7% |
| Science 6 | 8.3% | 33.3% |
| Science 7 | 15.8% | 47.4% |
| Science 8 | 2.6% | 36.8% |
| Science 9 | 0% | 75.8% |
| Science 10 | 0% | 75.8% |
| English 6 / 9 / 10 | 0% | 100% |
| Social Science 10 | 7.1% | 7.1% |

Picks are identical in 10 of 14 cells.

D. Guided builder, whole syllabus: 56 presets with a bank
- Maths/Science papers read 0% today.
- 10 presets are below_bank:
  - Science 6 half-yearly and annual: 11/37 (29.7%);
  - Science 7 half-yearly and annual: 16/37 (43.2%);
  - Science 8 half-yearly and annual: 12/37 (32.4%);
  - Social Science 10 unit test 1/8, periodic 1/12, half-yearly and annual 1/14.
- The other 46 meet 50%. Examples: Maths 10 half-yearly 37/38; Science 10 half-yearly 25/33; Science 6 periodic 10/20 (exactly 50%).
- Section E fills from CBE items:
  - Maths 9 and 10 half-yearly and annual: 0/3 to 3/3;
  - Maths 6, 7, 8 and Science 6, 7, 8 half-yearly and annual: 0/1 to 1/1;
  - Science 9: 0/3 to 1/3;
  - Science 10 and Social Science 10 stay 0/3.
- 10 presets flip from complete=False to True: Science 6, 7, 8 and Maths 9, 10, half-yearly and annual.
- Chapter-scoped: 10 Science half-yearly on the six chapters prints 8/30 and is below_scope.

E. Tiers
- tiersAvailable is false in 14 of 14 cells, before and after.
- difficultyLevels goes from 3/2/1 to 0 everywhere except Maths 10, which keeps 1 (4 board-paper records).
- Difficulty-mix notes: 168 to 0.

F. OR pairs
- 16 of 40 template OR pairs mix a CBE item with a non-CBE one; after step 4, sets B and D flag the question they actually print.

== DELIBERATELY LEFT OUT (and why) ==
- The CBE assessment-objective (AO2) share. aoMarks is {} on all 605 Maths/Science CBE records because cbse_cbe.py:99 and :208-213 strip the AO cells. Fixing it needs a parser change and a rebuild. Many CBE Maths items carry no AO2 marks (27/42 ... 29/67), so the provenance share should be reported with AO2 beside it later.
- Recording SQP section types in build_sqp_bank.py:82. It changes 0 served class 6-10 records today.
- Tagging the 168 chapterless CBE items.
- A paper-level competency quota in _pick.
- Re-baselining the stale builder fixtures. That is its own task, and a full recapture breaks flow_test :169, :185-196 and :212 for unrelated reasons.
- The Dart GeneratedPaper fields (competencyShare, competencyTargetMet, tiersAvailable; requests.dart:100-118). The web reads availability and paper.warnings.
- A quick-generate dry-run route. It would need a route_policy row, the web never calls quick-generate, and /questions/optimize is the dry run.
- The offline phone app: local_api_client.dart:274-277, the tier dropdown at assessment_list_page.dart:238-247, and 'Tier: X'. The release is web-first.
- Classes 11-12.
- Files owned by other sessions.

== RISKS FOR THE LEAD ==
- Is 50% right for classes 6-8? The constant makes a per-class table a one-line change.
- The printed assertion-reason labels are counted as TYPE. Dropping that takes Social Science 10 from 1/14 to 0/14.
- 'Section E - Case based' now fills with CBE 4-mark items that are mostly scenarios but not always cases, e.g. cbe:q:Maths9AG4 'Draw the graph of ...'. The kind check (_content_fits) already admitted any 4-mark long answer; the old competency gate was the only text check.
- A short paper inflates the printed share: English 6 annual reads 1 of 1 (100%, meets) while its sections are empty, which the red summary already says.
- Denominators: 340 vs 396 for Maths 10.
- The deployed bank may differ from this worktree's.