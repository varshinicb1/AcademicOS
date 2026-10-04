// Proves the actual on-device engine works, using the real bundled corpus,
// the real ported selection algorithm, and the real ported evaluation
// engine -- no device, no emulator, no mocked data. Run with:
//   flutter test test/local_engine/real_pipeline_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/core/local_engine/paper_selection.dart' as selection;
import 'package:academicos/core/local_engine/answer_evaluation.dart' as eval_engine;
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('real corpus loads with real question counts', () async {
    await CorpusRepository.instance.ensureLoaded();
    final catalog = CorpusRepository.instance.catalog();
    final science10 = catalog.firstWhere((c) => c.subject == 'Science' && c.grade == 10);

    // ignore: avoid_print
    print('\n=== CATALOG (real bundled corpus) ===');
    for (final c in catalog) {
      // ignore: avoid_print
      print('${c.subject} grade ${c.grade}: ${c.questionCount} questions, ${c.chapters} chapters');
    }

    // The served bank as merge_question_banks.py composed it (Task 11): 60
    // board records with a verified key, CBE, SQP and NCERT Exemplar. Science
    // 10 was 408 board questions in 13 chapters; it is now 1 board, 36 CBE
    // and 468 Exemplar. Task 121 dropped the 37th CBE record (its key holds a
    // symbol-font character nothing can name) and put every raw content code
    // back on the chapter it belongs to, so the 24 "chapters" -- 13 real ones
    // and 11 codes such as "10.6.9" -- are the syllabus's 13 again.
    //
    // 504, not 505: cbse:q:src:de9d7a7a1c777974c1dd9138:30 is refused as
    // scheme-marks-unallocated -- its key lists value points and gives every
    // one 0 marks, so the printed answer key reads "[0m]" against each and
    // tells a teacher nothing (re-audit of 2026-09-22 found 38% of the
    // then-live bank like that).
    expect(CorpusRepository.instance.all.length, greaterThan(5000));
    // 504 until the fidelity rebuild of 2026-09-28, which refused the Science
    // 10 items that point at a figure or graph they do not carry.
    // 589 with the 95 model-written, book-quoted Science 10 questions (corpus/ai-cbse-9-10): 2- and 4-mark
    // case studies and short answers for all 13 chapters.
    expect(science10.questionCount, 589);
    expect(science10.chapters, 13);
  });

  test('real paper generation produces a non-empty, correctly-sectioned paper', () async {
    await CorpusRepository.instance.ensureLoaded();

    final blueprint = Blueprint(
      totalMarks: 30,
      durationMinutes: 60,
      difficulty: const DifficultyDistribution(easy: 0.35, medium: 0.45, hard: 0.2),
      bloom: const BloomDistribution(
        remember: 0.25, understand: 0.25, apply: 0.2, analyze: 0.15, evaluate: 0.1, create: 0.05,
      ),
      chapterWeights: const ChapterWeights(weights: {}),
      competencyWeights: const CompetencyWeights(weights: {}),
      sections: selection.defaultSections(30),
    );

    // Mathematics 10, not Science 10: since Task 11 no Science 10 question
    // is worth 4 marks (the board case studies have no verified key), so its
    // section E cannot be filled from anywhere -- the honest gap the next
    // test covers, not a recovery.
    //
    // Deliberately narrow: a single real chapter, to exercise the
    // fallback/backfill rescue -- this is the exact bug class found and
    // fixed earlier this session (a narrow pick returning a blank paper).
    final candidates = CorpusRepository.instance.search(const QuestionSearchParams(
      subject: 'Mathematics', grade: 10, chapterIds: ['trigonometry'], limit: 500,
    ));
    final fallback = CorpusRepository.instance.search(
      const QuestionSearchParams(subject: 'Mathematics', grade: 10, limit: 2000),
    );

    final result = selection.optimize(candidates, blueprint, fallbackCandidates: fallback);

    // ignore: avoid_print
    print('\n=== REAL GENERATED PAPER (narrow chapter + fallback) ===');
    // ignore: avoid_print
    print('Selected: ${result.selectedQuestions.length} questions, '
        '${result.optimizationMetrics["totalMarksSelected"]} marks');
    // ignore: avoid_print
    print('Gaps (fallback rescue in action): ${result.gaps}');
    for (final q in result.selectedQuestions.take(5)) {
      // ignore: avoid_print
      print('  [${q.marks}m, ${q.difficulty.name}] ${q.stem.substring(0, q.stem.length.clamp(0, 70))}...');
    }

    expect(result.selectedQuestions, isNotEmpty,
        reason: 'THE core bug this whole build exists to fix: an empty generated paper');
    expect(result.optimizationMetrics['totalMarksSelected'], greaterThan(0));

    // Real user complaint this fixed: a narrow chapter pick that gets fully
    // recovered by the wider-subject fallback used to still narrate the
    // recovery as a scary "gap" ("needs X, only 0 available... filled N of
    // the shortfall") even though the teacher's real paper came back
    // completely full. A fully-recovered shortfall must produce zero
    // user-facing gaps -- the backfill is still real and still recorded,
    // just not as an alarming message for something that isn't a problem.
    expect(result.gaps, isEmpty,
        reason: 'a real, fully-backfilled paper (every section actually filled) must show no gaps');
    expect(result.optimizationMetrics['backfilledFromOutsideChapters'], greaterThan(0),
        reason: 'the real recovery must still be recorded internally, just not surfaced as a gap');
  });

  test('a genuinely unfillable section (no candidates anywhere) still reports a real, honest gap', () async {
    await CorpusRepository.instance.ensureLoaded();

    final blueprint = Blueprint(
      totalMarks: 30,
      durationMinutes: 60,
      difficulty: const DifficultyDistribution(easy: 0.35, medium: 0.45, hard: 0.2),
      bloom: const BloomDistribution(
        remember: 0.25, understand: 0.25, apply: 0.2, analyze: 0.15, evaluate: 0.1, create: 0.05,
      ),
      chapterWeights: const ChapterWeights(weights: {}),
      competencyWeights: const CompetencyWeights(weights: {}),
      sections: selection.defaultSections(30),
    );

    // No candidates, no fallback -- a real, unrecoverable shortfall (the
    // exact case that must NOT be silently hidden, unlike the recovered
    // case above -- this is a real incomplete paper the teacher must know about).
    final result = selection.optimize(const [], blueprint);

    expect(result.selectedQuestions, isEmpty);
    expect(result.gaps, isNotEmpty,
        reason: 'a real, still-incomplete paper must never be silently reported as gap-free');
    expect(result.gaps.every((g) => g.contains('could be found')), isTrue);
  });

  test('real evaluation engine scores real questions with real reasoning', () async {
    await CorpusRepository.instance.ensureLoaded();
    final questions = CorpusRepository.instance
        .search(const QuestionSearchParams(subject: 'Science', grade: 10, limit: 5));

    // ignore: avoid_print
    print('\n=== REAL EVALUATION (deterministic marking-point engine) ===');
    for (final q in questions) {
      final scheme = q.answerScheme;
      final correctAnswer = scheme.metadata['correctOption']?.toString() ??
          (scheme.markingPoints.isNotEmpty ? scheme.markingPoints.first.keyword : '');
      final result = eval_engine.evaluateAnswer(q, scheme, '($correctAnswer)');
      // ignore: avoid_print
      print('Q: ${q.stem.substring(0, q.stem.length.clamp(0, 60))}...');
      // ignore: avoid_print
      print('  answer="($correctAnswer)" -> ${result.awardedMarks}/${result.maxMarks} '
          '(${result.verdict}, confidence ${result.confidence}) -- ${result.reasoning}');

      final blankResult = eval_engine.evaluateAnswer(q, scheme, '');
      expect(blankResult.verdict, 'blank');
      expect(blankResult.awardedMarks, 0);
    }
  });

  test('ambiguous MCQ transcription (multiple option letters) forces review, not a confident wrong mark', () async {
    // The real, highest-severity bug found earlier this session: OCR text
    // naming an earlier-considered option before the real answer ("(A) but
    // eliminated it, chose (D)") used to get scored at 93% confidence with
    // no human review. This is the Dart engine's copy of that fix, ported
    // from evaluate.py's _evaluate_objective -- was stale here until now.
    await CorpusRepository.instance.ensureLoaded();
    // The first Science 10 MCQ: the bank's first question is no longer one.
    final q = CorpusRepository.instance
        .search(const QuestionSearchParams(subject: 'Science', grade: 10, limit: 2000))
        .firstWhere((q) => q.answerScheme.metadata['correctOption'] != null);
    final scheme = q.answerScheme;
    final key = scheme.metadata['correctOption']!.toString();

    final unambiguous = eval_engine.evaluateAnswer(q, scheme, '($key)');
    expect(unambiguous.confidence, greaterThan(0.75));
    expect(unambiguous.needsReview, isFalse);

    final otherLetter = (String.fromCharCode(key.codeUnitAt(0)) == 'A') ? 'B' : 'A';
    final ambiguous = eval_engine.evaluateAnswer(
        q, scheme, 'I first thought ($otherLetter) but the answer is ($key)');
    expect(ambiguous.confidence, lessThanOrEqualTo(0.5),
        reason: 'multiple distinct option letters must cap confidence low enough to force review');
    expect(ambiguous.needsReview, isTrue);
    // Still takes the first-mentioned letter as the best guess (verified
    // against real CBSE data as the right default) -- ambiguity changes the
    // confidence, not which letter is picked.
    expect(ambiguous.verdict, otherLetter == key ? 'fullCredit' : 'noCredit');
  });
}
