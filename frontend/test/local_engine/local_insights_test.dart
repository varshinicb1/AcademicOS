// Proves classInsights()/schoolInsights() -- the aggregation feeding the
// Gap Analysis and Principal dashboards -- against real evaluated data with
// hand-computed expected numbers, not just "doesn't throw". A codebase
// audit found these had zero test coverage despite being the most complex
// reduce logic in the offline engine: wrong denominator, wrong sort
// direction, or an off-by-one here would misreport which concept is
// "hardest" to a teacher, or the wrong mastery/coverage number to a
// Principal, with nothing catching it.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/core/local_engine/local_pillar_api.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tmpDir;
  late Box cacheBox;
  late LocalApiClient apiClient;
  late LocalPillarApi pillarApi;

  setUpAll(() async {
    tmpDir = Directory.systemTemp.createTempSync('local_insights_test_');
    Hive.init(tmpDir.path);
    cacheBox = await Hive.openBox('academicos_cache');
    await CorpusRepository.instance.ensureLoaded();
  });

  tearDownAll(() async {
    await cacheBox.close();
    tmpDir.deleteSync(recursive: true);
  });

  setUp(() async {
    await cacheBox.clear();
    apiClient = LocalApiClient();
    pillarApi = LocalPillarApi();
  });

  // A real, gradeable MCQ from the corpus -- has a real correctOption, so
  // answering "(X)" for the right letter or a deliberately wrong letter
  // produces a fully deterministic full-marks/zero-marks outcome, unlike a
  // descriptive question's fuzzy keyword matching.
  // Question.toJson() does not deep-serialize nested freezed objects
  // (answerScheme/parts) -- routing through a real JSON string round-trip
  // forces dart:convert to resolve them, same fix demo_seeder.dart needed
  // for the identical reason.
  Map<String, dynamic> realQuestionJson(Question q) =>
      jsonDecode(jsonEncode(q.toJson())) as Map<String, dynamic>;

  Question findRealMcq() {
    final candidates = CorpusRepository.instance.search(
      QuestionSearchParams(subject: 'Mathematics', grade: 10, limit: 500),
    );
    final mcq = candidates.firstWhere(
      (q) => (q.answerScheme.metadata['correctOption']?.toString() ?? '').isNotEmpty,
      orElse: () => throw StateError('no real gradeable MCQ found in the Mathematics/Class 10 corpus'),
    );
    return mcq;
  }

  test('classInsights: real average and per-concept accuracy match hand-computed expected values', () async {
    final assessment = await apiClient.createAssessment(CreateAssessmentRequest(
      teacherId: 'test_teacher',
      schoolId: 'test_school',
      title: 'Insights Test Assessment',
      subject: 'Mathematics',
      grade: 10,
      chapterIds: const [],
      blueprint: const BlueprintRequest(
        totalMarks: 1,
        durationMinutes: 10,
        difficulty: DifficultyDistribution(easy: 1, medium: 0, hard: 0),
        bloom: BloomDistribution(remember: 1, understand: 0, apply: 0, analyze: 0, evaluate: 0, create: 0),
        chapterWeights: ChapterWeights(weights: {}),
        competencyWeights: CompetencyWeights(weights: {}),
        sections: [],
      ),
    ));

    final mcq = findRealMcq();
    final correctOption = mcq.answerScheme.metadata['correctOption']!.toString();
    final wrongOption = ['A', 'B', 'C', 'D'].firstWhere((o) => o != correctOption);
    final questionJson = [realQuestionJson(mcq)];

    // Student A answers correctly, Student B answers wrong -- real
    // evaluateAnswer() decides the outcome, nothing hand-computed here.
    await pillarApi.evaluateSheet(
      assessmentId: assessment.id,
      studentId: 'stu_a',
      questions: questionJson,
      answers: {mcq.id: '($correctOption)'},
    );
    await pillarApi.evaluateSheet(
      assessmentId: assessment.id,
      studentId: 'stu_b',
      questions: questionJson,
      answers: {mcq.id: '($wrongOption)'},
    );

    final insights = await pillarApi.classInsights(assessment.id);
    expect(insights.students, 2);
    // One full-marks sheet (100%) and one zero-marks sheet (0%) -> exactly 50%.
    expect(insights.averagePercentage, closeTo(50.0, 0.01),
        reason: 'one correct + one wrong on a single-question sheet must average to exactly 50%');
    expect(insights.concepts, isNotEmpty);
    final concept = insights.concepts.first;
    // Real corpus questions in this subject carry no chapterIds (a known,
    // documented corpus-extraction gap), so both answers bucket under the
    // 'general' concept -- accuracy there must be exactly 0.5 (1 of 2 marks).
    expect(concept.classAccuracy, closeTo(0.5, 0.01));
  });

  test('classInsights: an assessment with no evaluated sheets yet reports honestly, not zeros dressed up as data', () async {
    final insights = await pillarApi.classInsights('nonexistent_assessment');
    expect(insights.students, 0);
    expect(insights.headline, contains('No evaluated sheets yet'));
  });

  test('schoolInsights: real per-subject rollup matches hand-computed awarded/max ratio', () async {
    final assessment = await apiClient.createAssessment(CreateAssessmentRequest(
      teacherId: 'test_teacher',
      schoolId: 'insights_school',
      title: 'Rollup Test Assessment',
      subject: 'Mathematics',
      grade: 10,
      chapterIds: const [],
      blueprint: const BlueprintRequest(
        totalMarks: 1,
        durationMinutes: 10,
        difficulty: DifficultyDistribution(easy: 1, medium: 0, hard: 0),
        bloom: BloomDistribution(remember: 1, understand: 0, apply: 0, analyze: 0, evaluate: 0, create: 0),
        chapterWeights: ChapterWeights(weights: {}),
        competencyWeights: CompetencyWeights(weights: {}),
        sections: [],
      ),
    ));

    final mcq = findRealMcq();
    final correctOption = mcq.answerScheme.metadata['correctOption']!.toString();
    final questionJson = [realQuestionJson(mcq)];

    // Both students answer correctly this time -> averageMastery for this
    // subject must be exactly 1.0 (awarded == max across every evaluation).
    await pillarApi.evaluateSheet(
      assessmentId: assessment.id,
      studentId: 'stu_x',
      questions: questionJson,
      answers: {mcq.id: '($correctOption)'},
    );
    await pillarApi.evaluateSheet(
      assessmentId: assessment.id,
      studentId: 'stu_y',
      questions: questionJson,
      answers: {mcq.id: '($correctOption)'},
    );
    // schoolInsights reads from mastery, not the raw evaluations -- and
    // evaluateSheet() deliberately no longer updates mastery on its own
    // (see the comment on it in local_pillar_api.dart). A teacher must
    // review and finalize before it counts, so this test does the same.
    await pillarApi.finalizeSheetReview(assessmentId: assessment.id, studentId: 'stu_x');
    await pillarApi.finalizeSheetReview(assessmentId: assessment.id, studentId: 'stu_y');

    final school = await pillarApi.schoolInsights('insights_school');
    expect(school.subjects, isNotEmpty, reason: '_subjectRollups must surface the Mathematics rollup for this school');
    final mathsRollup = school.subjects.firstWhere((s) => s.subject == 'Mathematics');
    expect(mathsRollup.students, 2);
    expect(mathsRollup.averageMastery, closeTo(1.0, 0.01),
        reason: 'two full-marks evaluations must roll up to exactly 100% mastery for this subject');
  });

  test('schoolInsights: a school with no evaluated students reports honestly, not a fabricated average', () async {
    final school = await pillarApi.schoolInsights('school_with_no_data');
    expect(school.students, 0);
    expect(school.averageMastery, 0.0);
    expect(school.subjects, isEmpty);
    expect(school.interventions, contains('No students evaluated yet on this device.'));
  });
}
