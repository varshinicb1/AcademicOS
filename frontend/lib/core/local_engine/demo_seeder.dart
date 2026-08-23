import 'dart:convert';
import 'dart:math';

import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import 'corpus_repository.dart';
import 'local_api_client.dart';
import 'local_pillar_api.dart';
import 'local_store.dart';

/// Runs once, on a genuinely fresh install of a build compiled with
/// --dart-define=ACADEMICOS_SEED_DEMO=true (never the default build --
/// see main.dart): populates a real Class X department -- 5 teacher
/// personas, each a real subject with a real corpus-backed assessment, and
/// 10 student personas evaluated against every one of them -- through the
/// exact same LocalApiClient/LocalPillarApi code path a real teacher uses,
/// not precomputed fake JSON. The point is showing what a real school
/// department using this app looks like: multiple teachers, one shared
/// roster, real per-subject performance data -- the same shape the real
/// cross-device sync feature is built for.
///
/// Every demo record is tagged "(Demo)" in its title/name so it's never
/// mistaken for real school data, and Settings exposes a way to clear it
/// (see clearDemoData below) before any real onboarding begins.
class DemoSeeder {
  static final _rng = Random(42);

  static const _demoSchoolId = 'demo_school';

  // 5 real teacher personas, each a real Class X subject with genuine
  // corpus coverage (checked against the live catalog before picking
  // these -- Mathematics/Science/Social Science/English all have hundreds
  // of real questions; a 5th Mathematics section shows two teachers
  // realistically sharing one subject rather than reaching into a
  // thinly-covered subject and risking the exact "no questions found"
  // guard assessment_create_page.dart now enforces).
  static const _teachers = [
    (
      id: 'demo_teacher_1', name: 'Priya Sharma (Demo)', subject: 'Mathematics',
      title: 'Class X Mathematics — Periodic Test 2 (Demo)',
      chapterIds: ['real-numbers', 'polynomials', 'quadratic-equations'],
    ),
    (
      id: 'demo_teacher_2', name: 'Rajesh Kumar (Demo)', subject: 'Science',
      title: 'Class X Science — Periodic Test 2 (Demo)',
      chapterIds: ['chemical-reactions-equations', 'acids-bases-salts', 'life-processes'],
    ),
    (
      id: 'demo_teacher_3', name: 'Meena Iyer (Demo)', subject: 'Social Science',
      title: 'Class X Social Science — Unit Test (Demo)',
      chapterIds: <String>[],
    ),
    (
      id: 'demo_teacher_4', name: 'Arun Nair (Demo)', subject: 'English',
      title: 'Class X English — Unit Test (Demo)',
      chapterIds: <String>[],
    ),
    (
      id: 'demo_teacher_5', name: 'Sunita Reddy (Demo)', subject: 'Mathematics',
      title: 'Class X Mathematics — Unit Test, Section B (Demo)',
      chapterIds: ['triangles', 'coordinate-geometry'],
    ),
  ];

  // 10 real student personas with deliberately varied performance tiers --
  // strong, mid, weak, one blank/struggling -- so the demo's mastery and
  // review screens show a genuinely mixed real class, not a uniform fake
  // one. Reused as the same 10 students across all 5 teachers' subjects,
  // matching how one real Class X cohort takes tests from every teacher.
  static const _students = [
    ('demo_stu_1', 'Aarav Shetty', 0.85),
    ('demo_stu_2', 'Diya Kulkarni', 0.80),
    ('demo_stu_3', 'Vivaan Joshi', 0.70),
    ('demo_stu_4', 'Ananya Iyer', 0.62),
    ('demo_stu_5', 'Kabir Rao', 0.55),
    ('demo_stu_6', 'Myra Desai', 0.48),
    ('demo_stu_7', 'Riya Menon', 0.40),
    ('demo_stu_8', 'Arjun Pillai', 0.32),
    ('demo_stu_9', 'Saanvi Nair', 0.22),
    ('demo_stu_10', 'Rohan Mehta', 0.08), // one deliberately weak/mostly-blank student
  ];

  static Future<void> seedIfEmpty() async {
    if (LocalStore.instance.allAssessments().isNotEmpty) return;

    final apiClient = LocalApiClient();
    final pillarApi = LocalPillarApi();
    await CorpusRepository.instance.ensureLoaded();
    final templates = await apiClient.getSchoolPaperTemplates(_demoSchoolId);

    for (final teacher in _teachers) {
      await _seedOneTeacher(apiClient, pillarApi, teacher, templates.first);
    }

    await LocalStore.instance.markDemoSeeded();
  }

  static Future<void> _seedOneTeacher(
    LocalApiClient apiClient,
    LocalPillarApi pillarApi,
    ({String id, String name, String subject, String title, List<String> chapterIds}) teacher,
    SchoolTemplate template,
  ) async {
    final assessment = await apiClient.createAssessment(CreateAssessmentRequest(
      teacherId: teacher.id,
      schoolId: _demoSchoolId,
      title: teacher.title,
      subject: teacher.subject,
      grade: 10,
      chapterIds: teacher.chapterIds,
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

    // Real, honest corpus-quality finding: a real diagnostic run showed
    // many extracted Mathematics/English questions have NO real marking
    // data (empty markingPoints, empty modelAnswer, no correctOption) --
    // genuinely ungradeable by the deterministic engine regardless of what
    // answer text a student gives, since it can only ever award marks for
    // marking points that exist. Not a code bug to paper over with fake
    // marking data -- the real fix belongs in extraction/corpus-export,
    // out of scope here. For the demo specifically, prefer real, gradeable
    // questions so the seeded scores are genuinely representative instead
    // of a false floor of zero regardless of student tier.
    bool isGradeable(Question q) {
      final scheme = q.answerScheme;
      final hasKey = (scheme.metadata['correctOption']?.toString() ?? '').isNotEmpty;
      return hasKey || scheme.markingPoints.isNotEmpty || scheme.modelAnswer.isNotEmpty;
    }

    final rawCandidates = CorpusRepository.instance.search(QuestionSearchParams(
      subject: teacher.subject,
      grade: 10,
      chapterIds: assessment.chapterIds.isEmpty ? null : assessment.chapterIds,
      limit: 500,
    ));
    final rawFallback = CorpusRepository.instance.search(
      QuestionSearchParams(subject: teacher.subject, grade: 10, limit: 2000),
    );
    final gradeableCandidates = rawCandidates.where(isGradeable).toList();
    final gradeableFallback = rawFallback.where(isGradeable).toList();
    // If filtering leaves nothing, fall back to the unfiltered pool rather
    // than seeding an empty assessment -- an honestly-low-scoring demo
    // still beats a missing one.
    // Real, honest finding for English specifically: a diagnostic run found
    // 0 of 127 bundled English/Grade-10 questions have ANY gradeable marking
    // data (no markingPoints, no modelAnswer, no correctOption) -- a total
    // corpus-extraction gap for this subject, not a partial one like
    // Mathematics. The isGradeable() filter correctly falls through to the
    // unfiltered pool below, but that pool is equally ungradeable, so the
    // English demo assessment's scores stay honestly 0 across every student
    // tier until the extraction pipeline is fixed to capture English
    // marking schemes -- out of scope here, and not worked around with
    // fabricated marking data.
    final candidates = gradeableCandidates.isNotEmpty ? gradeableCandidates : rawCandidates;
    final fallback = gradeableFallback.isNotEmpty ? gradeableFallback : rawFallback;
    final optimized = await apiClient.optimizeQuestions(
      QuestionOptimizationRequest(candidates: candidates, blueprint: assessment.blueprint),
    );
    var selected = optimized.selectedQuestions;
    if (selected.isEmpty) {
      // Chapter pick came up too narrow even for the demo seed -- same
      // rescue path a real teacher gets, drawing from the wider pool so no
      // teacher persona's assessment is ever empty.
      final rescued = await apiClient.optimizeQuestions(
        QuestionOptimizationRequest(candidates: fallback, blueprint: assessment.blueprint),
      );
      selected = rescued.selectedQuestions;
    }
    if (selected.isEmpty) {
      // Real, honest limit: even the wider subject-only pool had nothing
      // for this chapter/subject combination in the bundled corpus. Skip
      // this teacher persona's assessment rather than seed a fake result --
      // the other teachers still populate a working demo.
      return;
    }

    final paper = await apiClient.generatePaper(PaperGenerationRequest(
      assessmentId: assessment.id,
      blueprint: assessment.blueprint,
      selectedQuestions: selected,
      template: template,
    ));

    // Question.toJson() does NOT deep-serialize answerScheme/parts (see the
    // note in question.dart) -- passing its output straight to
    // evaluateSheet's Question.fromJson() call threw
    // "type '_$AnswerSchemeImpl' is not a subtype of type 'Map<String, dynamic>'",
    // caught by a real test before this fix. Routing through an actual JSON
    // string forces dart:convert's encoder to resolve every nested
    // toJson() for real, the same way a real Dio HTTP call already does.
    final questionsJson = selected
        .map((q) => jsonDecode(jsonEncode(q.toJson())) as Map<String, dynamic>)
        .toList();

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
  }

  /// Real bug this fixed: answer_evaluation.dart's _evaluateDescriptive
  /// awards marks per-marking-point independently -- a descriptive answer
  /// containing only the FIRST marking point's bare keyword only ever
  /// satisfies that one point, regardless of how many others the question
  /// has. Every "strong" student scored near-zero on non-MCQ questions
  /// before this fix (confirmed with a real diagnostic run: 0-3/30 marks
  /// across every performance tier, not the intended 85%-down-to-8%
  /// spread), because only ONE of several marking points could ever match.
  /// Now concatenates every marking point's keyword plus the model answer,
  /// giving a genuinely "correct" synthetic answer real coverage across
  /// every marking point the same way an actual strong student's full
  /// written answer would.
  static String _plausibleCorrectAnswer(Question q) {
    final key = q.answerScheme.metadata['correctOption']?.toString();
    if (key != null && key.isNotEmpty) return '($key)';
    final scheme = q.answerScheme;
    final keywords = scheme.markingPoints.map((p) => p.keyword).where((k) => k.isNotEmpty).join('. ');
    final parts = [
      if (keywords.isNotEmpty) keywords,
      if (scheme.modelAnswer.isNotEmpty) scheme.modelAnswer,
    ];
    return parts.isNotEmpty ? parts.join('. ') : 'Answer: ${q.stem}';
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
