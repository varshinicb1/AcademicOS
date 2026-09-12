import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';

import '../../data/datasources/api/pillar_api.dart';
import '../../domain/entities/entities.dart' show Question;
import '../../domain/entities/enums.dart' show Difficulty;
import '../../domain/repositories/requests.dart';
import 'answer_evaluation.dart' as eval_engine;
import 'concept_subjects.dart';
import 'corpus_repository.dart';
import 'local_scan_engine.dart' as local_scan;
import 'local_scan_pdf_export.dart';
import 'local_store.dart';
import 'mastery_engine.dart';

/// Thrown by local-engine methods that inherently need a network call this
/// build won't make on its own (OCR, email delivery). Distinct from a
/// generic Exception so callers/UI can tell "not implemented offline" apart
/// from "implemented but failed".
class OfflineUnsupportedException implements Exception {
  final String feature;
  OfflineUnsupportedException(this.feature);
  @override
  String toString() => '$feature needs an internet connection and isn\'t available in '
      'this offline build. Configure your own API key in Settings to enable it.';
}

/// On-device replacement for PillarApi -- same method signatures, same
/// response shapes (built as the exact JSON PillarApi's fromJson()
/// constructors already expect), backed by CorpusRepository + LocalStore
/// instead of Dio/HTTP. Used only on the standalone Android build; the
/// hosted web app keeps using the real PillarApi unchanged.
class LocalPillarApi extends PillarApi {
  LocalPillarApi() : super(Dio());

  @override
  String get serverOrigin => '';

  @override
  Future<Catalog> catalog() async {
    await CorpusRepository.instance.ensureLoaded();
    final entries = CorpusRepository.instance.catalog();
    return Catalog.fromJson({
      'entries': entries
          .map((e) => {
                'subject': e.subject,
                'grade': e.grade,
                'questionCount': e.questionCount,
                'chapters': e.chapters,
                'marksAvailable': e.marksAvailable,
              })
          .toList(),
      'totalQuestions': entries.fold<int>(0, (s, e) => s + e.questionCount),
    });
  }

  @override
  Future<List<ChapterEntry>> chapters(String subject, int grade) async {
    await CorpusRepository.instance.ensureLoaded();
    final entries = CorpusRepository.instance.chapters(subject, grade);
    return entries
        .map((e) => ChapterEntry.fromJson({
              'chapterId': e.chapterId,
              'chapterName': e.chapterName,
              'questionCount': e.questionCount,
              'marksAvailable': e.marksAvailable,
            }))
        .toList();
  }

  // Real gap found (not built until now): syllabus()/timetable() only ever
  // existed on the base PillarApi as real HTTP calls -- tapping the
  // Planner's "AI-suggested weekly timetable" sheet in the offline build
  // made a network request with no server, confirmed via the same
  // base-vs-override method audit that found generatePractice/
  // submitPractice broken the same way.
  //
  // Real, honest limitation: the server's real official CBSE unit-name and
  // marks-weightage structure (cbse_syllabus.py) was never bundled into
  // this offline build's corpus -- CorpusRepository only has extracted
  // chapter-level question counts and marks, not official syllabus units.
  // Rather than fabricate weightage numbers to match the online shape,
  // this builds a real, differently-sourced signal instead: real
  // question-bank coverage per chapter (marksAvailable summed from actual
  // extracted questions), clearly labeled as such rather than passed off
  // as official CBSE weightage.
  @override
  Future<Syllabus> syllabus(String subject, int grade) async {
    final entries = await chapters(subject, grade);
    if (entries.isEmpty) {
      throw OfflineUnsupportedException(
          'Syllabus pacing for $subject Class $grade (no corpus chapters found)');
    }
    final units = entries
        .map((e) => {
              'unitNo': e.chapterId,
              'name': e.chapterName,
              'marks': e.marksAvailable.fold<int>(0, (s, m) => s + m),
              'chapterNames': [e.chapterName],
            })
        .toList();
    return Syllabus.fromJson({
      'subject': subject,
      'grade': grade,
      'totalMarks': units.fold<int>(0, (s, u) => s + (u['marks'] as int)),
      'source': 'on-device corpus (real question-bank coverage per chapter, '
          'not official CBSE unit weightage -- that data isn\'t bundled offline)',
      'units': units,
    });
  }

  @override
  Future<Timetable> timetable(String subject, int grade,
      {int periodsPerWeek = 6, int weeks = 20}) async {
    final s = await syllabus(subject, grade);
    final totalMarks = s.totalMarks;
    final totalPeriods = periodsPerWeek * weeks;
    if (totalMarks == 0) {
      throw OfflineUnsupportedException(
          'Weekly pacing for $subject Class $grade (no real question-bank coverage to weight by)');
    }

    final allocations = <Map<String, dynamic>>[];
    final schedule = <Map<String, dynamic>>[];
    var week = 1;
    for (final unit in s.units) {
      // Real, proportional allocation from real chapter coverage -- same
      // marks-weightage-proportional method the server's real timetable
      // uses, just sourced from real extracted question marks instead of
      // an official syllabus table this build doesn't have.
      final suggested = totalMarks > 0
          ? (unit.marks / totalMarks * totalPeriods).round().clamp(1, totalPeriods)
          : 0;
      allocations.add({'unitName': unit.name, 'marks': unit.marks, 'suggestedPeriods': suggested});

      var remaining = suggested;
      while (remaining > 0 && week <= weeks) {
        final thisWeek = remaining.clamp(0, periodsPerWeek);
        schedule.add({'week': week, 'unitName': unit.name, 'periods': thisWeek});
        remaining -= thisWeek;
        week++;
      }
    }

    return Timetable.fromJson({
      'subject': subject,
      'grade': grade,
      'periodsPerWeek': periodsPerWeek,
      'weeks': weeks,
      'allocations': allocations,
      'schedule': schedule,
    });
  }

  @override
  Future<List<Map<String, dynamic>>> searchQuestionsRaw({
    required String subject,
    required int grade,
    int limit = 50,
  }) async {
    await CorpusRepository.instance.ensureLoaded();
    final results = CorpusRepository.instance.search(
      QuestionSearchParams(subject: subject, grade: grade, limit: limit),
    );
    // Question.toJson() does not deep-serialize nested freezed fields
    // (answerScheme, parts) -- see the NOTE on Question in
    // domain/entities/question.dart. Round-tripping through jsonEncode/
    // jsonDecode forces a real JSON-safe Map the same way a Dio HTTP call
    // already does; without it, callers that cast q['answerScheme'] as Map
    // (e.g. evaluation_page.dart's demo flow) crash with "type
    // '_$AnswerSchemeImpl' is not a subtype of type 'Map<dynamic, dynamic>'"
    // the moment this runs through the offline/local engine instead of Dio.
    return results
        .map((q) => jsonDecode(jsonEncode(q.toJson())) as Map<String, dynamic>)
        .toList();
  }

  @override
  Future<List<BankQuestion>> searchQuestions({
    required String subject,
    required int grade,
    String? keyword,
    int? minMarks,
    int? maxMarks,
    List<String>? chapterIds,
    int limit = 200,
  }) async {
    await CorpusRepository.instance.ensureLoaded();
    final results = CorpusRepository.instance.search(QuestionSearchParams(
      subject: subject,
      grade: grade,
      keyword: keyword,
      minMarks: minMarks,
      maxMarks: maxMarks,
      chapterIds: chapterIds,
      limit: limit,
    ));
    return results
        .map((q) => BankQuestion.fromJson({
              'id': q.id,
              'stem': q.stem,
              'marks': q.marks,
              'difficulty': q.difficulty.name,
              'bloomLevel': q.bloomLevel.name,
              'type': q.type.name,
              'chapterIds': q.chapterIds,
              'chapterNames': q.tags,
            }))
        .toList();
  }

  @override
  Future<StudentMastery> knowledge(String studentId) async {
    final stored = LocalStore.instance.getMastery(studentId);
    if (stored != null) return StudentMastery.fromJson(stored);
    return StudentMastery.fromJson({
      'studentId': studentId,
      'overallMastery': 0.0,
      'concepts': [],
      'weakConcepts': [],
    });
  }

  @override
  Future<ClassInsights> classInsights(String assessmentId, {String classId = '10A'}) async {
    final evaluations = LocalStore.instance.evaluationsFor(assessmentId);
    if (evaluations.isEmpty) {
      return ClassInsights.fromJson({
        'headline': 'No evaluated sheets yet for this assessment.',
        'students': 0,
        'averagePercentage': 0.0,
        'concepts': [],
        'sharedMistakes': [],
      });
    }
    final percentages = evaluations.map((e) => (e['percentage'] as num).toDouble()).toList();
    final avg = percentages.reduce((a, b) => a + b) / percentages.length;

    // Per-concept accuracy across every student's answers, same shape the
    // real /insights/class endpoint reports.
    final conceptTotals = <String, List<int>>{}; // [awarded, max]
    final conceptAtRisk = <String, Set<String>>{};
    for (final sheet in evaluations) {
      final studentId = sheet['studentId'] as String? ?? '';
      for (final ev in (sheet['evaluations'] as List? ?? [])) {
        final e = Map<String, dynamic>.from(ev as Map);
        final concept = (e['conceptId'] as String?) ?? 'general';
        final totals = conceptTotals.putIfAbsent(concept, () => [0, 0]);
        totals[0] += (e['awardedMarks'] as num? ?? 0).toInt();
        totals[1] += (e['maxMarks'] as num? ?? 0).toInt();
        if ((e['awardedMarks'] as num? ?? 0) < (e['maxMarks'] as num? ?? 1)) {
          conceptAtRisk.putIfAbsent(concept, () => {}).add(studentId);
        }
      }
    }
    final concepts = conceptTotals.entries.map((e) {
      final accuracy = e.value[1] > 0 ? e.value[0] / e.value[1] : 0.0;
      return {
        'conceptName': e.key,
        'classAccuracy': accuracy,
        'studentsRated': evaluations.length,
        'atRiskStudents': (conceptAtRisk[e.key] ?? {}).toList(),
        'recommendation': accuracy < 0.5
            ? 'Re-teach ${e.key} to the whole class — most students are below target.'
            : 'On track.',
        'estimatedMinutes': accuracy < 0.5 ? 45 : 0,
      };
    }).toList()
      ..sort((a, b) => (a['classAccuracy'] as double).compareTo(b['classAccuracy'] as double));

    return ClassInsights.fromJson({
      'headline':
          'Class average ${avg.toStringAsFixed(1)}%. ${concepts.isNotEmpty ? "Hardest concept: ${concepts.first['conceptName']}." : ""}',
      'students': evaluations.length,
      'averagePercentage': avg,
      'hardestConcept': concepts.isNotEmpty ? concepts.first['conceptName'] : null,
      'concepts': concepts,
      'sharedMistakes': [],
    });
  }

  @override
  Future<SchoolInsights> schoolInsights(String schoolId) async {
    final studentIds = LocalStore.instance.allStudentIdsWithMastery();
    final assessmentIds = LocalStore.instance.allAssessmentIdsWithEvaluations();
    if (studentIds.isEmpty) {
      return SchoolInsights.fromJson({
        'students': 0,
        'assessments': assessmentIds.length,
        'averageMastery': 0.0,
        'subjects': [],
        'interventions': ['No students evaluated yet on this device.'],
      });
    }
    final masteries = studentIds
        .map((id) => LocalStore.instance.getMastery(id))
        .whereType<Map<String, dynamic>>()
        .map((m) => (m['overallMastery'] as num? ?? 0).toDouble())
        .toList();
    final avg = masteries.isNotEmpty ? masteries.reduce((a, b) => a + b) / masteries.length : 0.0;
    return SchoolInsights.fromJson({
      'students': studentIds.length,
      'assessments': assessmentIds.length,
      'averageMastery': avg,
      'subjects': await _subjectRollups(schoolId),
      'interventions': [
        if (avg < 0.6) 'Average mastery is ${(avg * 100).toStringAsFixed(0)}% — below the 60% action line.',
      ],
    });
  }

  /// Real per-subject rollup for the Principal's "By subject" section --
  /// was a hardcoded `subjects: []` before this, so the section always
  /// rendered empty regardless of real evaluated data. Mastery is tracked
  /// per-concept without a subject tag in the current schema, so this uses
  /// real awarded/max marks across every evaluated assessment per subject
  /// as the mastery proxy (a genuine measured value, not invented), and
  /// real chapter coverage (chapters actually assessed vs. the subject's
  /// full corpus chapter count from the same chapters() call the Syllabus
  /// page uses).
  Future<List<Map<String, dynamic>>> _subjectRollups(String schoolId) async {
    final assessments = LocalStore.instance
        .allAssessments()
        .where((a) => a['schoolId'] == schoolId)
        .toList();
    final bySubjectGrade = <String, List<Map<String, dynamic>>>{};
    for (final a in assessments) {
      final key = '${a['subject']}|${a['grade']}';
      bySubjectGrade.putIfAbsent(key, () => []).add(a);
    }
    final rollups = <Map<String, dynamic>>[];
    for (final entry in bySubjectGrade.entries) {
      final subject = entry.value.first['subject'] as String? ?? '';
      final grade = (entry.value.first['grade'] as num?)?.toInt() ?? 0;
      if (subject.isEmpty) continue;

      var awarded = 0, max = 0;
      final students = <String>{};
      final assessedChapters = <String>{};
      for (final a in entry.value) {
        final id = a['id'] as String;
        for (final ev in LocalStore.instance.evaluationsFor(id)) {
          awarded += (ev['totalAwarded'] as num? ?? 0).toInt();
          max += (ev['totalMax'] as num? ?? 0).toInt();
          final sid = ev['studentId'] as String?;
          if (sid != null) students.add(sid);
        }
        for (final c in (a['chapterIds'] as List? ?? const [])) {
          assessedChapters.add(c.toString());
        }
      }
      if (students.isEmpty) continue; // no real evaluated data for this subject yet

      double coverage = 0;
      try {
        final allChapters = await chapters(subject, grade);
        coverage = allChapters.isEmpty
            ? 0
            : assessedChapters.length / allChapters.length;
      } catch (_) {
        // Real corpus lookup failed (e.g. subject not in catalog) -- leave
        // coverage at 0 rather than guessing.
      }

      rollups.add({
        'subject': subject,
        'grade': grade,
        'averageMastery': max > 0 ? awarded / max : 0.0,
        'students': students.length,
        'weakestConcept': null,
        'curriculumCoverage': coverage.clamp(0, 1),
      });
    }
    return rollups;
  }

  @override
  Future<SheetEvaluation> evaluateSheet({
    required String assessmentId,
    required String studentId,
    required List<Map<String, dynamic>> questions,
    required Map<String, String> answers,
    Map<String, String> correctOptions = const {},
  }) async {
    final evaluations = <Map<String, dynamic>>[];
    var totalAwarded = 0, totalMax = 0, needsReview = 0;
    for (final qJson in questions) {
      final question = Question.fromJson(qJson);
      final scheme = question.answerScheme;
      final answer = answers[question.id] ?? '';
      final result = eval_engine.evaluateAnswer(question, scheme, answer);
      totalAwarded += result.awardedMarks;
      totalMax += result.maxMarks;
      if (result.needsReview) needsReview++;
      evaluations.add({
        'questionId': result.questionId,
        'stem': question.stem,
        'studentAnswer': answer,
        'awardedMarks': result.awardedMarks,
        'maxMarks': result.maxMarks,
        'percentage': result.percentage,
        'verdict': result.verdict,
        'confidence': result.confidence,
        'reasoning': result.reasoning,
        'strengths': result.strengths,
        'gaps': result.gaps,
        'misconceptions': const [],
        'ocrWarnings': result.ocrWarnings,
        'needsReview': result.needsReview,
        'markingPoints': result.markingPoints
            .map((m) => {
                  'description': m.description,
                  'awarded': m.awarded,
                  'marks': m.marks,
                  'reason': m.reason,
                })
            .toList(),
        // conceptId isn't part of AnswerEvaluation.fromJson but classInsights
        // reads it straight off the stored map above.
        'conceptId': question.chapterIds.isNotEmpty ? question.chapterIds.first : 'general',
      });
    }
    final sheetJson = {
      'studentId': studentId,
      'totalAwarded': totalAwarded,
      'totalMax': totalMax,
      'percentage': totalMax > 0 ? 100.0 * totalAwarded / totalMax : 0.0,
      'needsReviewCount': needsReview,
      'evaluations': evaluations,
    };
    LocalStore.instance.addEvaluations(assessmentId, [sheetJson]);
    LocalStore.instance.appendAuditLog(
      action: 'sheet_evaluated',
      assessmentId: assessmentId,
      studentId: studentId,
      details: {'totalAwarded': totalAwarded, 'totalMax': totalMax, 'questionCount': questions.length},
    );
    // Deliberately NOT _updateMasteryFromSheet() here -- this is the raw AI
    // pass, before any teacher has looked at it. finalizeSheetReview() below
    // is the single point that folds it into mastery, once, using whatever
    // marks the teacher actually approved -- mirrors the same fix and the
    // same reasoning applied to the real backend's evaluate_sheet() in
    // src/academicos/assessment/pillar_routes.py.
    return SheetEvaluation.fromJson(sheetJson);
  }

  /// Local-engine counterpart to the real backend's review_sheet_answer().
  /// Without this override, the base PillarApi's Dio implementation runs
  /// instead -- a real HTTP call to 'localhost' from the emulator/device,
  /// which cannot reach the host machine and just hangs/fails silently.
  /// Same bug class already found and fixed once for generatePractice()/
  /// submitPractice() below -- see the comment there.
  @override
  Future<void> reviewSheetAnswer({
    required String assessmentId,
    required String studentId,
    required String questionId,
    required String action,
    int? marks,
  }) async {
    if (action != 'edit' || marks == null) return; // approve = accept the AI's award as-is
    final sheets = LocalStore.instance.evaluationsFor(assessmentId);
    final sheet = sheets.firstWhere((s) => s['studentId'] == studentId, orElse: () => const {});
    if (sheet.isEmpty) return;
    final evaluations = (sheet['evaluations'] as List).cast<Map<String, dynamic>>();
    final idx = evaluations.indexWhere((e) => e['questionId'] == questionId);
    if (idx < 0) return;
    final maxMarks = (evaluations[idx]['maxMarks'] as num).toInt();
    evaluations[idx] = {...evaluations[idx], 'awardedMarks': marks.clamp(0, maxMarks)};
    final totalAwarded = evaluations.fold<int>(0, (sum, e) => sum + (e['awardedMarks'] as num).toInt());
    final totalMax = evaluations.fold<int>(0, (sum, e) => sum + (e['maxMarks'] as num).toInt());
    LocalStore.instance.replaceEvaluationSheet(assessmentId, {
      ...sheet,
      'evaluations': evaluations,
      'totalAwarded': totalAwarded,
      'totalMax': totalMax,
      'percentage': totalMax > 0 ? 100.0 * totalAwarded / totalMax : 0.0,
    });
  }

  /// Local-engine counterpart to the real backend's finalize_sheet_review().
  /// Folds the teacher-reviewed sheet (whatever mix of approved/edited marks
  /// [reviewSheetAnswer] has left in LocalStore) into the student's mastery
  /// model, exactly once. See the comment on evaluateSheet() above.
  @override
  Future<void> finalizeSheetReview({
    required String assessmentId,
    required String studentId,
    String reviewerId = '',
  }) async {
    final sheets = LocalStore.instance.evaluationsFor(assessmentId);
    final sheet = sheets.firstWhere((s) => s['studentId'] == studentId, orElse: () => const {});
    if (sheet.isEmpty) return;
    final evaluations = (sheet['evaluations'] as List).cast<Map<String, dynamic>>();
    LocalStore.instance.appendAuditLog(
      action: 'sheet_reviewed',
      assessmentId: assessmentId,
      studentId: studentId,
      details: {
        'totalAwarded': sheet['totalAwarded'],
        'totalMax': sheet['totalMax'],
        'questionCount': evaluations.length,
      },
      // Caller-supplied reviewerId wins when given (an older call site might
      // still pass one explicitly); otherwise falls back to the device's
      // current-user profile rather than being permanently blank.
      actor: reviewerId.isNotEmpty ? reviewerId : null,
    );
    _updateMasteryFromSheet(studentId, evaluations);
  }

  void _updateMasteryFromSheet(String studentId, List<Map<String, dynamic>> evaluations) {
    final existing = LocalStore.instance.getMastery(studentId);
    final concepts = <String, Map<String, dynamic>>{};
    if (existing != null) {
      for (final c in (existing['concepts'] as List? ?? [])) {
        final m = Map<String, dynamic>.from(c as Map);
        concepts[m['conceptId'] as String] = m;
      }
    }
    for (final e in evaluations) {
      final conceptId = e['conceptId'] as String? ?? 'general';
      final awarded = (e['awardedMarks'] as num? ?? 0).toDouble();
      final max = (e['maxMarks'] as num? ?? 1).toDouble();
      final observed = max > 0 ? awarded / max : 0.0;
      concepts[conceptId] = updatedConceptMastery(
        conceptId: conceptId,
        existing: concepts[conceptId],
        observed: observed,
      );
    }
    saveMasteryRollup(studentId, concepts.values);
  }

  // ---------------- Personalized practice ----------------
  // Real gap found and fixed: generatePractice()/submitPractice() only
  // ever existed on the base PillarApi (real Dio HTTP calls) -- never
  // overridden here, so tapping Mastery's real "Generate targeted
  // practice" button in the offline build made a network call with no
  // server to answer it. This is the "personalized assessment generation"
  // feature the user explicitly asked for and that never actually worked
  // offline.

  @override
  Future<PracticeSetView> generatePractice(String studentId, {int perConcept = 2}) async {
    final mastery = LocalStore.instance.getMastery(studentId);
    final warnings = <String>[];
    if (mastery == null) {
      return PracticeSetView.fromJson({
        'id': '', 'items': [], 'totalMarks': 0,
        'warnings': ['This student has no evaluated work yet -- nothing to target practice at.'],
      });
    }
    var weak = List<String>.from(mastery['weakConcepts'] as List? ?? const []);
    if (weak.isEmpty) {
      // Real, honest fallback: nothing below the weak threshold -- practice
      // the lowest-mastery concepts anyway rather than returning nothing.
      final concepts = (mastery['concepts'] as List? ?? [])
          .map((c) => Map<String, dynamic>.from(c as Map))
          .toList()
        ..sort((a, b) => (a['mastery'] as num).compareTo(b['mastery'] as num));
      weak = concepts.take(3).map((c) => c['conceptId'] as String).toList();
    }

    final conceptSubjects = conceptSubjectsFor(studentId);
    final items = <Map<String, dynamic>>[];
    final questionsById = <String, Map<String, dynamic>>{};
    var totalMarks = 0;
    for (final concept in weak) {
      final subjectGrade = conceptSubjects[concept];
      if (subjectGrade == null) {
        warnings.add('No subject on record for "$concept" -- skipped.');
        continue;
      }
      final (subject, grade) = subjectGrade;
      final candidates = CorpusRepository.instance
          .search(QuestionSearchParams(
            subject: subject,
            grade: grade,
            chapterIds: [concept],
            difficulties: const [Difficulty.easy],
            limit: perConcept * 4,
          ))
          .where((q) =>
              q.answerScheme.markingPoints.isNotEmpty ||
              q.answerScheme.modelAnswer.isNotEmpty ||
              (q.answerScheme.metadata['correctOption']?.toString() ?? '').isNotEmpty)
          .take(perConcept)
          .toList();
      if (candidates.isEmpty) {
        warnings.add('No real gradeable easy questions found for "$concept" in the corpus.');
        continue;
      }
      for (final q in candidates) {
        questionsById[q.id] = q.toJson();
        items.add({
          'questionId': q.id,
          'conceptId': concept,
          'stem': q.stem,
          'marks': q.marks,
          'difficulty': q.difficulty.name,
        });
        totalMarks += q.marks;
      }
    }

    final setId = 'practice_${DateTime.now().millisecondsSinceEpoch}';
    LocalStore.instance.savePracticeSet(setId, {
      'studentId': studentId,
      'questions': questionsById,
      'conceptByQuestion': {for (final i in items) i['questionId'] as String: i['conceptId']},
    });

    return PracticeSetView.fromJson({
      'id': setId,
      'items': items,
      'totalMarks': totalMarks,
      'warnings': warnings,
    });
  }

  @override
  Future<PracticeResultView> submitPractice(String setId, Map<String, String> answers) async {
    final set = LocalStore.instance.getPracticeSet(setId);
    if (set == null) {
      return PracticeResultView.fromJson({
        'score': 0, 'maxScore': 0, 'percentage': 0.0, 'outcomes': [],
        'nextAction': 'This practice set has expired -- generate a new one.',
      });
    }
    final studentId = set['studentId'] as String;
    final questions = Map<String, dynamic>.from(set['questions'] as Map);
    final conceptByQuestion = Map<String, dynamic>.from(set['conceptByQuestion'] as Map);

    final masteryBefore = LocalStore.instance.getMastery(studentId);
    final masteryBeforeByConcept = <String, double>{
      for (final c in (masteryBefore?['concepts'] as List? ?? []))
        (c as Map)['conceptId'] as String: (c['mastery'] as num).toDouble(),
    };

    final evaluations = <Map<String, dynamic>>[];
    var score = 0, maxScore = 0;
    for (final entry in questions.entries) {
      final question = Question.fromJson(Map<String, dynamic>.from(entry.value as Map));
      final answer = answers[entry.key] ?? '';
      final result = eval_engine.evaluateAnswer(question, question.answerScheme, answer);
      score += result.awardedMarks;
      maxScore += result.maxMarks;
      evaluations.add({
        'awardedMarks': result.awardedMarks,
        'maxMarks': result.maxMarks,
        'conceptId': conceptByQuestion[entry.key] ?? 'general',
      });
    }
    _updateMasteryFromSheet(studentId, evaluations);
    final masteryAfter = LocalStore.instance.getMastery(studentId);
    final masteryAfterByConcept = <String, double>{
      for (final c in (masteryAfter?['concepts'] as List? ?? []))
        (c as Map)['conceptId'] as String: (c['mastery'] as num).toDouble(),
    };

    final touchedConcepts = conceptByQuestion.values.toSet();
    final outcomes = touchedConcepts.map((concept) {
      final before = masteryBeforeByConcept[concept] ?? 0.3;
      final after = masteryAfterByConcept[concept] ?? before;
      return {
        'conceptName': concept,
        'masteryBefore': before,
        'masteryAfter': after,
        'delta': after - before,
        'mastered': after >= 0.8,
      };
    }).toList();

    final percentage = maxScore > 0 ? 100.0 * score / maxScore : 0.0;
    return PracticeResultView.fromJson({
      'score': score,
      'maxScore': maxScore,
      'percentage': percentage,
      'outcomes': outcomes,
      'nextAction': percentage >= 80
          ? 'Strong result -- ready to move on to a new concept.'
          : (percentage >= 50
              ? 'Getting there -- one more practice round on the same concepts is worth it.'
              : 'Still shaky -- consider re-teaching before another practice round.'),
    });
  }

  @override
  Future<Map<String, dynamic>> mailStatus() async => {
        // Shape must match the server's real /mail/status response --
        // PaperDeliverySheet reads anyConfigured and backends[x].reason
        // directly; the old {'configured': false} shape had neither key,
        // so opening the Email tab threw a null-cast exception instead of
        // showing the intended "not configured" warning.
        'anyConfigured': false,
        'backends': {
          'offline': {
            'configured': false,
            'reason': 'This is an offline on-device build -- there is no mail server to send through.',
          },
        },
      };

  @override
  Future<Map<String, dynamic>> sendPaper({
    required String paperId,
    required List<String> recipients,
    required String subjectName,
    required int grade,
    required String paperTitle,
    String schoolName = 'AcademicOS School',
    String note = '',
    bool includeAnswerKey = true,
  }) async =>
      throw OfflineUnsupportedException('Emailing papers');

  @override
  Future<List<Map<String, dynamic>>> schoolTemplates(String schoolId) async =>
      LocalStore.instance.templatesFor(schoolId);

  @override
  Future<List<Map<String, dynamic>>> templateSections(String schoolId, String templateId) async {
    final t = LocalStore.instance.templatesFor(schoolId).cast<Map<String, dynamic>?>().firstWhere(
          (t) => t?['id'] == templateId,
          orElse: () => null,
        );
    return List<Map<String, dynamic>>.from(t?['sections'] as List? ?? []);
  }

  @override
  Future<Map<String, dynamic>> saveTemplate(
      String schoolId, Map<String, dynamic> template, List<Map<String, dynamic>> sections) async {
    final withSections = {...template, 'sections': sections};
    LocalStore.instance.saveTemplate(schoolId, withSections);
    return withSections;
  }

  @override
  Future<List<Map<String, dynamic>>> listAssessmentsForSchool(String schoolId) async {
    return LocalStore.instance.allAssessments().where((a) => a['schoolId'] == schoolId).toList();
  }

  // Real on-device handwriting OCR (google_mlkit_text_recognition, see
  // on_device_ocr.dart) + the same evaluation engine the typed-answer path
  // uses (local_scan_engine.dart) -- no network call anywhere in this flow.
  @override
  Future<ScanSession> createScanSession({
    required String assessmentId,
    required String studentId,
    required String studentName,
  }) async =>
      ScanSession.fromJson(local_scan.LocalScanEngine.createSession(
        assessmentId: assessmentId,
        studentId: studentId,
        studentName: studentName,
      ));

  @override
  Future<CapturedPageResult> uploadScanPage(String sessionId, String imagePath) async =>
      CapturedPageResult.fromJson(await local_scan.LocalScanEngine.uploadPage(sessionId, imagePath));

  @override
  Future<ScanReviewQueue> processScanSession(String sessionId) async =>
      ScanReviewQueue.fromJson(await local_scan.LocalScanEngine.processSession(sessionId));

  @override
  Future<ScanReviewQueue> getScanReview(String sessionId) async =>
      ScanReviewQueue.fromJson(local_scan.LocalScanEngine.getReview(sessionId));

  @override
  Future<ScanReviewItem> submitReviewDecision(
    String sessionId,
    String questionId, {
    required String action,
    int? marks,
    String comment = '',
  }) async =>
      ScanReviewItem.fromJson(await local_scan.LocalScanEngine.submitReviewDecision(
        sessionId, questionId, action: action, marks: marks, comment: comment,
      ));

  @override
  Future<ScanFinalizeResult> finalizeScanSession(String sessionId) async =>
      ScanFinalizeResult.fromJson(await local_scan.LocalScanEngine.finalizeSession(sessionId));

  // Real gap closed: this used to throw OfflineUnsupportedException
  // unconditionally for both PDFs. The backend already had real
  // export_corrected_pdf/export_raw_booklet_pdf logic
  // (src/academicos/assessment/mobile_scan.py) that never made it into the
  // offline build -- ported here using the same real session/review data,
  // ../local_scan_pdf_export.dart. `url` is the same relative path the
  // caller already builds (/scan/sessions/{id}/{raw|corrected}-pdf) --
  // parsed rather than given a new offline-only shape, so no caller change
  // was needed.
  static final RegExp _scanPdfUrl = RegExp(r'^/scan/sessions/([^/]+)/(raw|corrected)-pdf$');

  @override
  Future<String> downloadScanPdf(String url, String savePath) async {
    final match = _scanPdfUrl.firstMatch(url);
    if (match == null) {
      throw OfflineUnsupportedException('Scan & Grade PDF export for "$url"');
    }
    final sessionId = match.group(1)!;
    final kind = match.group(2)!;
    final generatedPath = kind == 'corrected'
        ? await LocalScanPdfExporter.exportCorrected(sessionId)
        : await LocalScanPdfExporter.exportRawBooklet(sessionId);
    final bytes = await File(generatedPath).readAsBytes();
    await File(savePath).writeAsBytes(bytes);
    return savePath;
  }
}
