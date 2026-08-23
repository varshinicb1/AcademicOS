import 'package:dio/dio.dart';

import '../../data/datasources/api/pillar_api.dart';
import '../../domain/entities/entities.dart' show Question;
import '../../domain/repositories/requests.dart';
import 'answer_evaluation.dart' as eval_engine;
import 'corpus_repository.dart';
import 'local_scan_engine.dart' as local_scan;
import 'local_store.dart';

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
    return results.map((q) => q.toJson()).toList();
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
      'subjects': [],
      'interventions': [
        if (avg < 0.6) 'Average mastery is ${(avg * 100).toStringAsFixed(0)}% — below the 60% action line.',
      ],
    });
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
    _updateMasteryFromSheet(studentId, evaluations);
    return SheetEvaluation.fromJson(sheetJson);
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
      final existingConcept = concepts[conceptId];
      final priorEvidence = (existingConcept?['evidenceCount'] as num?)?.toInt() ?? 0;
      final priorMastery = (existingConcept?['mastery'] as num?)?.toDouble() ?? 0.3;
      final observed = max > 0 ? awarded / max : 0.0;
      // Simple recency-weighted running average -- real FSRS retention math
      // is a further step, not attempted for this first on-device pass.
      final newMastery = priorEvidence == 0 ? observed : (priorMastery * 0.7 + observed * 0.3);
      concepts[conceptId] = {
        'conceptId': conceptId,
        'conceptName': conceptId,
        'mastery': newMastery,
        'retention': 0.9,
        'evidenceCount': priorEvidence + 1,
        'status': newMastery < 0.5 ? 'needsReview' : (newMastery < 0.8 ? 'developing' : 'proficient'),
        'isWeak': newMastery < 0.5,
      };
    }
    final all = concepts.values.toList();
    final overall = all.isNotEmpty
        ? all.map((c) => (c['mastery'] as num).toDouble()).reduce((a, b) => a + b) / all.length
        : 0.0;
    LocalStore.instance.saveMastery(studentId, {
      'studentId': studentId,
      'overallMastery': overall,
      'concepts': all,
      'weakConcepts': all.where((c) => c['isWeak'] == true).map((c) => c['conceptName']).toList(),
    });
  }

  @override
  Future<Map<String, dynamic>> mailStatus() async => {'configured': false, 'reason': 'offline build'};

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
      ScanReviewItem.fromJson(local_scan.LocalScanEngine.submitReviewDecision(
        sessionId, questionId, action: action, marks: marks, comment: comment,
      ));

  @override
  Future<ScanFinalizeResult> finalizeScanSession(String sessionId) async =>
      ScanFinalizeResult.fromJson(local_scan.LocalScanEngine.finalizeSession(sessionId));

  @override
  Future<String> downloadScanPdf(String url, String savePath) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');
}
