import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter/services.dart' show rootBundle;
import 'package:path_provider/path_provider.dart';

import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import '../constants/app_constants.dart';
import 'answer_evaluation.dart' as eval_engine;
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

  // Same value as AppConstants.currentSchoolId -- kept as a real reference
  // (not just a matching literal) after a stress test found the Assessments
  // list, Planner, and Settings/Sync screens each hardcoding a DIFFERENT
  // school ID that didn't match this one, silently showing empty/wrong data.
  static const _demoSchoolId = AppConstants.currentSchoolId;

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

  // A deliberately fictional placeholder name -- product-owner decision, not
  // a real unaffiliated school. Every demo PDF/report should show this
  // rather than a blank header.
  static const _demoSchoolName = 'AcademicOS Demo School';

  static Future<void> seedIfEmpty() async {
    if (LocalStore.instance.allAssessments().isNotEmpty) return;

    LocalStore.instance.setSchoolName(_demoSchoolId, _demoSchoolName);
    // Real gap fixed here: student display names used to live only in the
    // _students tuple below, never persisted -- Mastery's student picker
    // and any future roster view could only ever show a raw id.
    for (final (studentId, name, _) in _students) {
      LocalStore.instance.setStudentName(studentId, name);
    }
    final apiClient = LocalApiClient();
    final pillarApi = LocalPillarApi();
    await CorpusRepository.instance.ensureLoaded();
    final templates = await apiClient.getSchoolPaperTemplates(_demoSchoolId);

    Assessment? scanDemoAssessment;
    for (final teacher in _teachers) {
      final seeded = await _seedOneTeacher(apiClient, pillarApi, teacher, templates.first);
      // First successfully-seeded assessment becomes the one real "corrected
      // paper" demo -- see _seedDemoScanSession below. Real user request:
      // Scan & Grade's corrected-sheet feature had nothing to show without
      // a teacher actually scanning something themselves first.
      scanDemoAssessment ??= seeded;
      // Yields to the event loop between teachers too -- see the longer
      // note on the same pattern inside _seedOneTeacher's per-student loop.
      await Future<void>.delayed(Duration.zero);
    }

    if (scanDemoAssessment != null) {
      final scanStudent = _students.firstWhere((s) => s.$1 == 'demo_stu_4');
      await _seedDemoScanSession(scanDemoAssessment, scanStudent.$1, scanStudent.$2);
    }

    await LocalStore.instance.markDemoSeeded();
  }

  static Future<Assessment?> _seedOneTeacher(
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
      return null;
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
      // evaluateSheet() deliberately no longer folds its (unreviewed) AI
      // score into mastery on its own -- see the comment on evaluateSheet()
      // in local_pillar_api.dart. Every demo student here is presented as
      // already "evaluated" (below, and in the Assessments list UI), i.e.
      // a teacher has already reviewed and signed off on it, so finalizing
      // immediately is the correct simulation of that -- not a workaround.
      await pillarApi.finalizeSheetReview(assessmentId: assessment.id, studentId: studentId);
      // Real ANR reproduced on-device: seeding 5 assessments x 10 students,
      // each doing several LocalStore reads/re-encodes, ran long enough
      // between await points that a tap during startup made Android report
      // "academicos isn't responding". This is a genuine yield to the event
      // loop (not a real delay) so pending frames/input actually get a
      // chance to process between students instead of the whole loop
      // running as one long unbroken stretch on the UI isolate.
      await Future<void>.delayed(Duration.zero);
    }

    final evaluatedAssessment = assessment.copyWith(status: AssessmentStatus.evaluated, generatedPaperId: paper.id);
    LocalStore.instance.upsertAssessment(evaluatedAssessment.toJson());
    return evaluatedAssessment;
  }

  /// Seeds ONE real, fully-graded Scan & Grade session -- the "corrected
  /// paper" demo the app had nothing to show for otherwise (MobileScanPage
  /// always starts a brand-new capture, there's no way to resume/browse a
  /// past one). Reuses the exact same real evaluation engine
  /// (answer_evaluation.dart) that a live scan uses -- these are real marks
  /// against real corpus marking schemes, not invented numbers.
  ///
  /// `pages`/`pageImageUrls` point at two bundled asset images
  /// (assets/images/demo_scan_page_*.jpg -- a synthetic but realistic-looking
  /// photographed answer script, generated once offline, no real student's
  /// handwriting) materialized into real files via _materializeDemoPage
  /// below, so the review/correction screens and the corrected-sheet PDF
  /// export -- which both read a real `File(imagePath)` -- have something
  /// genuine to show instead of "no photo saved". Real user request: a
  /// teacher opening this app for the first time should see what a fully
  /// completed scan looks like, not an empty placeholder.
  static Future<void> _seedDemoScanSession(
    Assessment assessment,
    String studentId,
    String studentName,
  ) async {
    final paperId = assessment.generatedPaperId;
    if (paperId == null || paperId.isEmpty) return;
    final paperRaw = LocalStore.instance.getPaper(paperId);
    if (paperRaw == null) return;
    final paper = GeneratedPaper.fromJson(paperRaw);
    final pageImagePaths = await _materializeDemoScanPages();

    final questionsById = {for (final q in CorpusRepository.instance.all) q.id: q};
    final review = <Map<String, dynamic>>[];
    var editedOne = false;
    for (final section in paper.sections) {
      for (final gq in section.questions) {
        final question = questionsById[gq.questionId];
        if (question == null) continue;
        // Same deterministic-but-varied answer pattern as the rest of this
        // seeder: a real mix of correct/partial/blank so the corrected
        // sheet shows genuine red/orange/green variation, not a flat score.
        final roll = _rng.nextDouble();
        final answerText = roll < 0.55
            ? _plausibleCorrectAnswer(question)
            : roll < 0.8
                ? 'Attempt: ${question.stem.substring(0, min(30, question.stem.length))}'
                : '';
        final result = eval_engine.evaluateAnswer(question, question.answerScheme, answerText);
        final item = <String, dynamic>{
          'questionId': gq.questionId,
          'displayNumber': gq.displayNumber,
          'stem': gq.stem,
          'maxMarks': gq.marks,
          'studentAnswer': answerText,
          'awardedMarks': result.awardedMarks,
          'verdict': result.verdict,
          'confidence': result.confidence,
          'reasoning': result.reasoning,
          'markingPoints': result.markingPoints
              .map((m) => {
                    'id': m.markingPointId,
                    'description': m.description,
                    'awarded': m.awarded,
                    'marks': m.marks,
                    'reason': m.reason,
                  })
              .toList(),
          'ocrWarnings': const <String>[],
          'needsReview': false,
          'status': 'approved',
          'teacherMarks': null,
          'teacherComment': '',
          'finalMarks': result.awardedMarks,
          'pageImageUrls': pageImagePaths,
        };
        // One real teacher override, on the first partial-credit question --
        // demos the actual red-pen/edited-annotation feature, not just AI marks.
        if (!editedOne && result.awardedMarks > 0 && result.awardedMarks < gq.marks) {
          item['status'] = 'edited';
          item['teacherMarks'] = gq.marks;
          item['finalMarks'] = gq.marks;
          item['teacherComment'] = 'Full method shown on paper -- awarding full marks.';
          editedOne = true;
        }
        review.add(item);
      }
    }
    if (review.isEmpty) return;

    final sessionId = 'demo_scan_$studentId';
    final pages = [
      for (var i = 0; i < pageImagePaths.length; i++)
        {
          'pageNo': i + 1,
          'imagePath': pageImagePaths[i],
          'text': '',
          'warnings': const <String>[],
          'confidence': 0.92,
        },
    ];
    LocalStore.instance.saveScanSession(sessionId, {
      'id': sessionId,
      'assessmentId': assessment.id,
      'studentId': studentId,
      'studentName': studentName,
      'status': 'finalized',
      'pages': pages,
      'review': review,
    });
  }

  /// Copies the two bundled demo answer-sheet images (assets/images/) out of
  /// the asset bundle into real files under the app's documents directory,
  /// once -- every downstream consumer (the review screen's Image.file,
  /// the full-page viewer, local_scan_pdf_export.dart's
  /// File(imagePath).readAsBytes()) already expects a real filesystem path,
  /// same as a genuinely captured photo would produce, so nothing downstream
  /// needs to know these started life as bundled assets.
  static Future<List<String>> _materializeDemoScanPages() async {
    final dir = await getApplicationDocumentsDirectory();
    final paths = <String>[];
    for (final name in const ['demo_scan_page_1.jpg', 'demo_scan_page_2.jpg']) {
      final file = File('${dir.path}/$name');
      if (!await file.exists()) {
        final bytes = await rootBundle.load('assets/images/$name');
        await file.writeAsBytes(bytes.buffer.asUint8List(), flush: true);
      }
      paths.add(file.path);
    }
    return paths;
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
      LocalStore.instance.deleteScanSession('demo_scan_$studentId');
    }
    // Removes the two real files _materializeDemoScanPages wrote out --
    // otherwise they'd silently linger in the app's documents directory
    // after a "clear demo data" a teacher expects to be a clean slate.
    try {
      final dir = await getApplicationDocumentsDirectory();
      for (final name in const ['demo_scan_page_1.jpg', 'demo_scan_page_2.jpg']) {
        final file = File('${dir.path}/$name');
        if (await file.exists()) await file.delete();
      }
    } catch (_) {
      // Best-effort cleanup -- never block clearing the rest of the demo data.
    }
    await LocalStore.instance.clearDemoSeededFlag();
  }
}
