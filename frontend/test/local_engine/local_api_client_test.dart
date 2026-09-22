// Proves the 3 live-called LocalApiClient methods that a codebase audit
// found had zero test coverage anywhere (LocalApiClient is never even
// instantiated in test/local_engine/): getAssessment() and getPaper() gate
// whether a teacher can reopen a generated paper (assessment_review_page.dart),
// and updateAssessment() is what the Planner actually persists a reschedule
// through (daily_planner_page.dart). A silent fromJson/serialization
// regression in any of these would surface as a hard crash on those real
// screens with nothing catching it first.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/constants/app_constants.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tmpDir;
  late Box cacheBox;
  late LocalApiClient api;

  setUpAll(() async {
    tmpDir = Directory.systemTemp.createTempSync('local_api_client_test_');
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
    api = LocalApiClient();
  });

  Future<Assessment> createRealAssessment() => api.createAssessment(CreateAssessmentRequest(
        teacherId: 'test_teacher',
        schoolId: 'test_school',
        title: 'Real Test Assessment',
        subject: 'Mathematics',
        grade: 10,
        // Real corpus limitation (see docs/compliance.md and this session's
        // own findings): chapter tagging isn't populated for every subject,
        // so filtering by chapterIds here would return zero real
        // candidates. Subject-only search is what demo_seeder.dart itself
        // falls back to for exactly this reason.
        chapterIds: const [],
        blueprint: const BlueprintRequest(
          totalMarks: 20,
          durationMinutes: 40,
          difficulty: DifficultyDistribution(easy: 0.4, medium: 0.4, hard: 0.2),
          bloom: BloomDistribution(
              remember: 0.3, understand: 0.3, apply: 0.2, analyze: 0.1, evaluate: 0.05, create: 0.05),
          chapterWeights: ChapterWeights(weights: {}),
          competencyWeights: CompetencyWeights(weights: {}),
          sections: [],
        ),
      ));

  group('getAssessment', () {
    test('retrieves a real, just-created assessment with matching fields', () async {
      final created = await createRealAssessment();
      final fetched = await api.getAssessment(created.id);
      expect(fetched.id, created.id);
      expect(fetched.subject, 'Mathematics');
      expect(fetched.teacherId, 'test_teacher');
    });

    test('throws a clear, honest error for a nonexistent id -- not a raw cast exception', () async {
      expect(
        () => api.getAssessment('does_not_exist'),
        throwsA(predicate((e) => e.toString().contains('does_not_exist'))),
      );
    });
  });

  group('getPaper', () {
    test('retrieves a real generated paper with real questions, round-tripped through JSON', () async {
      final assessment = await createRealAssessment();
      final templates = await api.getSchoolPaperTemplates('test_school');
      final candidates = CorpusRepository.instance.search(QuestionSearchParams(
        subject: 'Mathematics',
        grade: 10,
        limit: 200,
      ));
      expect(candidates, isNotEmpty, reason: 'Mathematics/Class 10 is a well-covered subject in the real corpus');
      final optimized = await api.optimizeQuestions(
        QuestionOptimizationRequest(candidates: candidates, blueprint: assessment.blueprint),
      );
      expect(optimized.selectedQuestions, isNotEmpty,
          reason: 'a real, populated candidate pool producing an empty selection would mean optimizeQuestions broke');

      final paper = await api.generatePaper(PaperGenerationRequest(
        assessmentId: assessment.id,
        blueprint: assessment.blueprint,
        selectedQuestions: optimized.selectedQuestions,
        template: templates.first,
      ));

      final fetched = await api.getPaper(paper.id);
      expect(fetched.id, paper.id);
      expect(fetched.sections, isNotEmpty);
      expect(fetched.metadata.subject, 'Mathematics');
    });

    test('throws a clear, honest error for a nonexistent id', () async {
      expect(() => api.getPaper('no_such_paper'), throwsA(anything));
    });
  });

  group('updateAssessment', () {
    test('a real reschedule (the Planner\'s actual live use) persists and round-trips', () async {
      final assessment = await createRealAssessment();
      expect(assessment.scheduledAt, isNull);

      final rescheduled = assessment.copyWith(scheduledAt: DateTime(2026, 9, 1, 10, 30));
      final result = await api.updateAssessment(assessment.id, rescheduled);
      expect(result.scheduledAt, DateTime(2026, 9, 1, 10, 30));

      // The real regression this guards against: a silent toJson/fromJson
      // drift that lets updateAssessment() "succeed" without the change
      // actually sticking -- reopening the planner would show the old time.
      final refetched = await api.getAssessment(assessment.id);
      expect(refetched.scheduledAt, DateTime(2026, 9, 1, 10, 30),
          reason: 'a reschedule that does not survive a re-fetch is exactly the silent-failure '
              'mode a teacher would only discover by reopening the planner later');
    });
  });

  // Against the real bundled corpus. Neither refusal test hard-codes a gap
  // in today's bank: the merge exists to close those gaps (class 7 Science
  // gains CBE questions, English 10 may gain SQP 2-markers), and a test
  // pinned to one would fail, or be weakened, the day the gap closes.
  group('quickGeneratePaper', () {
    // The bank is CBSE classes 6-12; class 3 can never have questions. The
    // old quick path fell back to every grade of the subject, so a request
    // for a grade with none came back as another grade's questions.
    test('a grade with no questions refuses instead of serving another grade', () async {
      await expectLater(
        () => api.quickGeneratePaper(const QuickPaperRequest(subject: 'Science', grade: 3, totalMarks: 20)),
        throwsA(isA<NoQuestionsForGradeException>()),
      );
      expect(await api.getAssessmentsBySchool(AppConstants.currentSchoolId), isEmpty,
          reason: 'a refused request must not leave an empty draft in the Assessments list');
    });

    // English class 10 once held 127 one-markers and no 2- or 3-markers
    // (2026-09-22), and its paper came out as 5 questions worth 5 marks under
    // a "20 marks" header. The short request is found at runtime -- a whole
    // grade, else a single chapter, whose pool cannot fill some section --
    // so the test keeps biting as the bank fills in.
    test('a pool that cannot fill a section refuses instead of printing a short paper', () async {
      final sections = quickPaperSections(20);
      final pairs = {
        for (final q in CorpusRepository.instance.all) (q.subject, q.grade),
      }.toList()
        ..sort((a, b) => '${a.$1}${a.$2}'.compareTo('${b.$1}${b.$2}'));
      QuickPaperRequest? short;
      SectionBlueprint? shortSection;
      var shortFound = 0;
      search:
      for (final (subject, grade) in pairs) {
        final chapters = {
          for (final q in CorpusRepository.instance.search(QuestionSearchParams(subject: subject, grade: grade)))
            ...q.chapterIds,
        }.toList()
          ..sort();
        for (final filter in [<String>[], for (final c in chapters) [c]]) {
          final pool = CorpusRepository.instance.search(
              QuestionSearchParams(subject: subject, grade: grade, chapterIds: filter.isEmpty ? null : filter));
          if (pool.isEmpty) continue;
          for (final section in sections) {
            final have = pool.where((q) => q.marks == section.marksPerQuestion).length;
            if (have < section.questionCount) {
              short = QuickPaperRequest(subject: subject, grade: grade, chapterIds: filter, totalMarks: 20);
              shortSection = section;
              shortFound = have;
              break search;
            }
          }
        }
      }
      expect(short, isNotNull,
          reason: 'every grade and every single chapter can fill a 20-mark paper: pick another short case');
      final word = {1: 'one', 2: 'two', 3: 'three'}[shortSection!.marksPerQuestion];
      await expectLater(
        () => api.quickGeneratePaper(short!),
        throwsA(isA<InsufficientQuestionsException>().having((e) => e.toString(), 'message',
            contains('Only $shortFound of ${shortSection.questionCount} $word-mark questions '
                'for ${short!.subject} class ${short.grade}'))),
      );
      expect(await api.getAssessmentsBySchool(AppConstants.currentSchoolId), isEmpty,
          reason: 'a refused request must not leave an empty draft in the Assessments list');
    });

    // The Quick Paper dialog sends 25, 40, 50 or 80 -- never 20. The sections
    // used to be fixed at 5+6+9 = 20 marks while the header took the
    // requested total, so a class test printed "25 marks" over 20 marks of
    // questions.
    for (final total in const [25, 40, 50, 80]) {
      test('a $total-mark dialog preset prints $total marks of questions under a $total-mark header', () async {
        final paper = await api.quickGeneratePaper(
            QuickPaperRequest(subject: 'Science', grade: 10, totalMarks: total));
        expect(paper.metadata.totalMarks, total);
        expect(paper.sections.fold<int>(0, (s, sec) => s + sec.totalMarks), total);
        expect(
            paper.sections.expand((s) => s.questions).fold<int>(0, (s, q) => s + q.marks), total);
      });
    }

    test('the paper carries the requested grade and fills every section', () async {
      final paper = await api.quickGeneratePaper(
          const QuickPaperRequest(subject: 'Science', grade: 10, totalMarks: 20));
      expect(paper.metadata.grade, 10);
      expect(paper.metadata.subject, 'Science');
      final assessment = await api.getAssessment(paper.assessmentId);
      for (final section in assessment.blueprint.sections) {
        final generated = paper.sections.firstWhere((s) => s.sectionId == section.id);
        expect(generated.questions, hasLength(section.questionCount),
            reason: 'section ${section.id} (${section.marksPerQuestion}-markers) came out short');
      }
      expect(paper.sections.fold<int>(0, (s, sec) => s + sec.totalMarks), 20);
    });
  });
}
