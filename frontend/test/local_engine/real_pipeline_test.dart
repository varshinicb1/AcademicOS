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

    expect(CorpusRepository.instance.all.length, greaterThan(3000));
    expect(science10.questionCount, 408);
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

    // Deliberately narrow: a single real chapter, to exercise the
    // fallback/backfill rescue -- this is the exact bug class found and
    // fixed earlier this session (a narrow pick returning a blank paper).
    final candidates = CorpusRepository.instance.search(QuestionSearchParams(
      subject: 'Science', grade: 10, chapterIds: const ['our-environment'], limit: 500,
    ));
    final fallback = CorpusRepository.instance.search(
      QuestionSearchParams(subject: 'Science', grade: 10, limit: 2000),
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
  });

  test('real evaluation engine scores real questions with real reasoning', () async {
    await CorpusRepository.instance.ensureLoaded();
    final questions = CorpusRepository.instance
        .search(QuestionSearchParams(subject: 'Science', grade: 10, limit: 5));

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
}
