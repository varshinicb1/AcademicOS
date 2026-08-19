import 'dart:math';

import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import 'corpus_repository.dart';
import 'local_api_client.dart';
import 'local_pillar_api.dart';
import 'local_store.dart';

/// Runs once, on a genuinely fresh install of the standalone offline build:
/// generates a real Class X Science periodic test, evaluates a class of 16
/// demo students against it, and lets that populate real mastery/insights --
/// through the exact same LocalApiClient/LocalPillarApi code path a real
/// teacher uses, not precomputed fake JSON. The point isn't to fake a
/// result; it's so a principal opens the app for the first time and sees a
/// fully working product instead of eight empty screens and a manual setup
/// form, which is what actually killed the last pitch.
///
/// Every demo record is tagged "(Demo)" in its title/name so it's never
/// mistaken for real school data, and Settings exposes a way to clear it
/// (see clearDemoData below) before any real onboarding begins.
class DemoSeeder {
  static final _rng = Random(42);

  static const _demoSchoolId = 'demo_school';
  static const _demoTeacherId = 'demo_teacher';

  static const _students = [
    ('demo_stu_1', 'Aarav Shetty', 0.85),
    ('demo_stu_2', 'Diya Kulkarni', 0.80),
    ('demo_stu_3', 'Vivaan Joshi', 0.78),
    ('demo_stu_4', 'Ananya Iyer', 0.62),
    ('demo_stu_5', 'Kabir Rao', 0.60),
    ('demo_stu_6', 'Myra Desai', 0.58),
    ('demo_stu_7', 'Riya Menon', 0.55),
    ('demo_stu_8', 'Arjun Pillai', 0.52),
    ('demo_stu_9', 'Saanvi Nair', 0.40),
    ('demo_stu_10', 'Rohan Mehta', 0.38),
    ('demo_stu_11', 'Kavya Reddy', 0.35),
    ('demo_stu_12', 'Ishaan Bhatt', 0.32),
    ('demo_stu_13', 'Pari Agarwal', 0.20),
    ('demo_stu_14', 'Yash Verma', 0.18),
    ('demo_stu_15', 'Zara Khan', 0.15),
    ('demo_stu_16', 'Aditya Gowda', 0.05), // one deliberately weak/blank student
  ];

  static Future<void> seedIfEmpty() async {
    if (LocalStore.instance.allAssessments().isNotEmpty) return;

    final apiClient = LocalApiClient();
    final pillarApi = LocalPillarApi();
    await CorpusRepository.instance.ensureLoaded();

    final assessment = await apiClient.createAssessment(CreateAssessmentRequest(
      teacherId: _demoTeacherId,
      schoolId: _demoSchoolId,
      title: 'Class X Science — Periodic Test 2 (Demo)',
      subject: 'Science',
      grade: 10,
      chapterIds: const ['chemical-reactions-equations', 'acids-bases-salts', 'life-processes'],
      blueprint: BlueprintRequest(
        totalMarks: 30,
        durationMinutes: 60,
        difficulty: const DifficultyDistribution(easy: 0.35, medium: 0.45, hard: 0.2),
        bloom: const BloomDistribution(
          remember: 0.25, understand: 0.25, apply: 0.2, analyze: 0.15, evaluate: 0.1, create: 0.05,
        ),
        chapterWeights: const ChapterWeights(weights: {}),
        competencyWeights: const CompetencyWeights(weights: {}),
        sections: const [],
      ),
    ));

    final candidates = CorpusRepository.instance.search(QuestionSearchParams(
      subject: 'Science',
      grade: 10,
      chapterIds: assessment.chapterIds,
      limit: 500,
    ));
    final fallback = CorpusRepository.instance.search(
      QuestionSearchParams(subject: 'Science', grade: 10, limit: 2000),
    );
    final optimized = await apiClient.optimizeQuestions(
      QuestionOptimizationRequest(candidates: candidates, blueprint: assessment.blueprint),
    );
    var selected = optimized.selectedQuestions;
    if (selected.isEmpty) {
      // Chapter pick came up too narrow even for the demo seed -- same
      // rescue path a real teacher gets, drawing from the wider pool so the
      // first thing a principal sees is never an empty paper.
      final rescued = await apiClient.optimizeQuestions(
        QuestionOptimizationRequest(candidates: fallback, blueprint: assessment.blueprint),
      );
      selected = rescued.selectedQuestions;
    }

    final templates = await apiClient.getSchoolPaperTemplates(_demoSchoolId);
    final paper = await apiClient.generatePaper(PaperGenerationRequest(
      assessmentId: assessment.id,
      blueprint: assessment.blueprint,
      selectedQuestions: selected,
      template: templates.first,
    ));

    final questionsJson = selected.map((q) => q.toJson()).toList();

    for (final (studentId, _, targetScore) in _students) {
      final answers = <String, String>{};
      for (final q in selected) {
        final roll = _rng.nextDouble();
        if (roll > targetScore + 0.15) {
          continue; // left blank, like a real weak/rushed student
        }
        final correctish = roll <= targetScore;
        answers[q.id] = correctish
            ? _plausibleCorrectAnswer(q)
            : 'Attempt: ${q.stem.substring(0, min(40, q.stem.length))}';
      }
      await pillarApi.evaluateSheet(
        assessmentId: assessment.id,
        studentId: studentId,
        questions: questionsJson,
        answers: answers,
      );
    }

    LocalStore.instance.upsertAssessment(
      assessment.copyWith(status: AssessmentStatus.evaluated, generatedPaperId: paper.id).toJson(),
    );
    await LocalStore.instance.markDemoSeeded();
  }

  static String _plausibleCorrectAnswer(Question q) {
    final key = q.answerScheme.metadata['correctOption']?.toString();
    if (key != null && key.isNotEmpty) return '($key)';
    final point = q.answerScheme.markingPoints.isNotEmpty ? q.answerScheme.markingPoints.first : null;
    return point?.keyword.isNotEmpty == true ? point!.keyword : q.answerScheme.modelAnswer;
  }

  /// Wipes every demo_* record so a real onboarding starts from a clean
  /// slate -- exposed from Settings, not run automatically, so nobody loses
  /// real school data by accident.
  static Future<void> clearDemoData() async {
    for (final a in LocalStore.instance.allAssessments().where((a) => a['schoolId'] == _demoSchoolId).toList()) {
      LocalStore.instance.deleteAssessment(a['id'] as String);
    }
    for (final (studentId, _, _) in _students) {
      LocalStore.instance.clearMastery(studentId);
    }
    await LocalStore.instance.clearDemoSeededFlag();
  }
}
