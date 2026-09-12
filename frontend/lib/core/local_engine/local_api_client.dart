import 'dart:math';

import 'package:dio/dio.dart';

import '../../data/datasources/api/api_client.dart';
import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import 'answer_evaluation.dart' as eval_engine;
import 'corpus_repository.dart';
import 'local_pdf_export.dart';
import 'local_pillar_api.dart' show OfflineUnsupportedException;
import 'local_store.dart';
import 'mastery_engine.dart';
import 'paper_selection.dart' as selection_engine;

/// Mirrors the real backend's `_require_editable` guard
/// (`src/academicos/assessment/routes.py`) so the offline build enforces the
/// exact same paper-approval lock instead of silently allowing a question
/// swap or content edit after a principal has approved a paper -- the hard
/// edit-lock docs/compliance.md calls for, previously only real on the
/// network build.
class AssessmentLockedException implements Exception {
  final String assessmentId;
  final String status;
  AssessmentLockedException(this.assessmentId, this.status);
  @override
  String toString() => 'assessment $assessmentId is $status — the paper is locked; '
      'question selection and paper content cannot be changed after principal approval';
}

/// Mirrors the real backend's auth_routes.require_principal (403) -- the
/// offline half of the same principal-approval workflow, gated on the
/// device's self-declared role (LocalStore.teacherRole, set in Settings ->
/// Profile) rather than a server-issued one. See local_store.dart's comment
/// on why that's the honest limit of what's enforceable without a server.
class NotPrincipalException implements Exception {
  @override
  String toString() => 'only the principal role can approve a paper -- set your role in '
      'Settings > Profile if you are the principal';
}

const editableAssessmentStatuses = {
  AssessmentStatus.draft,
  AssessmentStatus.blueprintReady,
  AssessmentStatus.questionsSelected,
  AssessmentStatus.questionOptimized,
  AssessmentStatus.paperGenerated,
  AssessmentStatus.underReview,
};

/// On-device replacement for ApiClient -- the paper-generation +
/// evaluation + mastery core, real algorithms (paper_selection.dart /
/// answer_evaluation.dart are faithful ports of the actual Python engine),
/// backed by LocalStore instead of a server. Same method signatures as
/// ApiClient so every repository/bloc built against it works unmodified.
class LocalApiClient extends ApiClient {
  LocalApiClient() : super(Dio());

  final _rng = Random();
  String _newId(String prefix) =>
      '${prefix}_${DateTime.now().millisecondsSinceEpoch.toRadixString(16)}${_rng.nextInt(0xFFFF).toRadixString(16)}';

  // ---------------- Assessment ----------------

  @override
  Future<Assessment> createAssessment(CreateAssessmentRequest request) async {
    final blueprint = await generateBlueprint(request.blueprint);
    final assessment = Assessment(
      id: _newId('assess'),
      schoolId: request.schoolId,
      teacherId: request.teacherId,
      title: request.title,
      subject: request.subject,
      grade: request.grade,
      chapterIds: request.chapterIds,
      blueprint: blueprint,
      status: AssessmentStatus.blueprintReady,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      templateId: request.templateId,
    );
    LocalStore.instance.upsertAssessment(assessment.toJson());
    return assessment;
  }

  @override
  Future<Assessment> getAssessment(String id) async {
    final j = LocalStore.instance.getAssessment(id);
    if (j == null) throw Exception('Assessment $id not found on this device.');
    return Assessment.fromJson(j);
  }

  @override
  Future<List<Assessment>> getAssessmentsByTeacher(String teacherId) async {
    return LocalStore.instance
        .allAssessments()
        .where((a) => a['teacherId'] == teacherId)
        .map(Assessment.fromJson)
        .toList();
  }

  @override
  Future<List<Assessment>> getAssessmentsBySchool(String schoolId) async {
    return LocalStore.instance
        .allAssessments()
        .where((a) => a['schoolId'] == schoolId)
        .map(Assessment.fromJson)
        .toList();
  }

  @override
  Future<Assessment> updateAssessment(String id, Assessment assessment) async {
    final existingJson = LocalStore.instance.getAssessment(id);
    if (existingJson != null) {
      final existing = Assessment.fromJson(existingJson);
      if (!editableAssessmentStatuses.contains(existing.status)) {
        throw AssessmentLockedException(id, existing.status.name);
      }
    }
    LocalStore.instance.upsertAssessment(assessment.toJson());
    return assessment;
  }

  @override
  Future<void> deleteAssessment(String id) async {
    LocalStore.instance.deleteAssessment(id);
  }

  @override
  Future<Assessment> updateStatus(String id, Map<String, dynamic> status) async {
    final current = await getAssessment(id);
    final statusName = status['status'] as String?;
    final newStatus = statusName != null
        ? AssessmentStatus.values.firstWhere((s) => s.name == statusName, orElse: () => current.status)
        : current.status;
    if (!editableAssessmentStatuses.contains(current.status) && editableAssessmentStatuses.contains(newStatus)) {
      // Mirrors PATCH /assessments/{id}/status's own guard: forward
      // progression (principalApproved -> printed -> conducted -> ...) is
      // always fine; moving BACK into an editable state after approval is
      // exactly the silent-tamper path the lock exists to close.
      throw AssessmentLockedException(id, current.status.name);
    }
    final updated = current.copyWith(status: newStatus, updatedAt: DateTime.now());
    LocalStore.instance.upsertAssessment(updated.toJson());
    return updated;
  }

  /// Offline counterpart to the real backend's PATCH .../approve
  /// (auth_routes.require_principal-gated there; LocalStore.teacherRole-
  /// gated here -- see NotPrincipalException's comment on why that's a
  /// different, honestly weaker trust model, not a bypass of the same one).
  @override
  Future<Assessment> approveAssessment(String id) async {
    if (LocalStore.instance.teacherRole != 'principal') {
      throw NotPrincipalException();
    }
    final current = await getAssessment(id);
    final updated = current.copyWith(
      status: AssessmentStatus.principalApproved, updatedAt: DateTime.now(),
    );
    LocalStore.instance.upsertAssessment(updated.toJson());
    LocalStore.instance.appendAuditLog(
      action: 'assessment_approved',
      assessmentId: id,
      studentId: '-',
      details: {'principalName': LocalStore.instance.teacherName},
    );
    return updated;
  }

  // ---------------- Blueprint ----------------

  @override
  Future<Blueprint> generateBlueprint(BlueprintRequest request) async {
    // Deterministic, same as the server side: the wizard never actually
    // lets a teacher hand-author sections, so the standard CBSE A-E layout
    // (scaled to totalMarks) fills that gap here exactly like it does live.
    final sections = request.sections.isNotEmpty
        ? request.sections
        : selection_engine.defaultSections(request.totalMarks);
    return Blueprint(
      totalMarks: request.totalMarks,
      durationMinutes: request.durationMinutes,
      difficulty: request.difficulty,
      bloom: request.bloom,
      chapterWeights: request.chapterWeights,
      competencyWeights: request.competencyWeights,
      sections: sections,
    );
  }

  @override
  Future<Blueprint> getBlueprint(String assessmentId) async {
    final a = await getAssessment(assessmentId);
    return a.blueprint;
  }

  @override
  Future<Blueprint> updateBlueprint(String assessmentId, Blueprint blueprint) async {
    final a = await getAssessment(assessmentId);
    final updated = a.copyWith(blueprint: blueprint, updatedAt: DateTime.now());
    LocalStore.instance.upsertAssessment(updated.toJson());
    return blueprint;
  }

  @override
  Future<List<SectionBlueprint>> getSchoolTemplates(String schoolId) async {
    return selection_engine.defaultSections(100);
  }

  @override
  Future<void> saveTemplate(String schoolId, SectionBlueprint template) async {
    // Section-shape templates aren't used by the wizard (school branding
    // templates are handled by LocalPillarApi.saveTemplate instead); no-op
    // kept intentionally rather than silently pretending to persist.
  }

  // ---------------- Questions ----------------

  @override
  Future<List<Question>> searchQuestions(QuestionSearchParams params) async {
    await CorpusRepository.instance.ensureLoaded();
    return CorpusRepository.instance.search(params);
  }

  @override
  Future<Question> getQuestion(String id) async {
    await CorpusRepository.instance.ensureLoaded();
    return CorpusRepository.instance.all.firstWhere(
      (q) => q.id == id,
      orElse: () => throw Exception('Question $id not found in bundled corpus.'),
    );
  }

  @override
  Future<List<Question>> getQuestionsByIds(List<String> ids) async {
    await CorpusRepository.instance.ensureLoaded();
    final wanted = ids.toSet();
    return CorpusRepository.instance.all.where((q) => wanted.contains(q.id)).toList();
  }

  @override
  Future<Question> createQuestion(Question question) async =>
      throw OfflineUnsupportedException('Adding custom questions to the bank');

  @override
  Future<Question> updateQuestion(String id, Question question) async =>
      throw OfflineUnsupportedException('Editing bank questions');

  @override
  Future<void> deleteQuestion(String id) async =>
      throw OfflineUnsupportedException('Deleting bank questions');

  @override
  Future<QuestionOptimizationResult> optimizeQuestions(QuestionOptimizationRequest request) async {
    await CorpusRepository.instance.ensureLoaded();
    // Same rescue the live fix applies: if the chapter-scoped candidates
    // can't fill a section, backfill from the full subject+grade pool
    // instead of returning a paper with a blank section.
    final fallback = CorpusRepository.instance.all
        .where((q) =>
            q.subject == request.candidates.firstOrNull?.subject &&
            q.grade == request.candidates.firstOrNull?.grade)
        .toList();
    return selection_engine.optimize(request.candidates, request.blueprint,
        fallbackCandidates: fallback);
  }

  // ---------------- Paper Generation ----------------

  @override
  Future<GeneratedPaper> generatePaper(PaperGenerationRequest request) async {
    final assessment = await getAssessment(request.assessmentId);
    if (!editableAssessmentStatuses.contains(assessment.status)) {
      throw AssessmentLockedException(request.assessmentId, assessment.status.name);
    }
    final sections = <GeneratedSection>[];
    var displayNumber = 1;
    // Group selected questions by which section they fit (same
    // marksPerQuestion / difficulty rule paper_selection.dart already used
    // to pick them), so the generated paper is laid out section-by-section
    // like a real CBSE paper.
    final remaining = List<Question>.from(request.selectedQuestions);
    for (final section in request.blueprint.sections) {
      final matching = remaining.where((q) => q.marks == section.marksPerQuestion).take(section.questionCount).toList();
      for (final q in matching) {
        remaining.remove(q);
      }
      sections.add(GeneratedSection(
        sectionId: section.id,
        label: section.label,
        name: section.name,
        totalMarks: matching.fold(0, (s, q) => s + q.marks),
        questions: matching
            .map((q) => GeneratedQuestion(
                  questionId: q.id,
                  displayNumber: displayNumber++,
                  stem: q.stem,
                  stemLatex: q.stemLatex,
                  parts: q.parts,
                  marks: q.marks,
                  bloomLevel: q.bloomLevel.name,
                  difficulty: q.difficulty.name,
                  type: q.type.name,
                ))
            .toList(),
      ));
    }

    final answerKey = <String, dynamic>{
      for (final q in request.selectedQuestions)
        q.id: q.answerScheme.metadata['correctOption'] ?? q.answerScheme.modelAnswer,
    };

    final paper = GeneratedPaper(
      id: _newId('paper'),
      assessmentId: request.assessmentId,
      sections: sections,
      formattedContent: '',
      formattedContentLatex: '',
      answerKey: answerKey,
      metadata: PaperMetadata(
        assessmentTitle: request.template.name,
        schoolName: LocalStore.instance.schoolName(assessment.schoolId),
        subject: request.selectedQuestions.firstOrNull?.subject ?? '',
        grade: request.selectedQuestions.firstOrNull?.grade ?? 0,
        totalMarks: request.blueprint.totalMarks,
        durationMinutes: request.blueprint.durationMinutes,
        generatedAt: DateTime.now(),
        generatedBy: 'AcademicOS on-device engine',
        version: '1.0-local',
      ),
    );
    LocalStore.instance.savePaper(paper.id, paper.toJson());
    LocalStore.instance.upsertAssessment(
      assessment
          .copyWith(status: AssessmentStatus.paperGenerated, generatedPaperId: paper.id, updatedAt: DateTime.now())
          .toJson(),
    );
    return paper;
  }

  @override
  Future<GeneratedPaper> getPaper(String paperId) async {
    final j = LocalStore.instance.getPaper(paperId);
    if (j == null) throw Exception('Paper $paperId not found on this device.');
    return GeneratedPaper.fromJson(j);
  }

  @override
  Future<GeneratedPaper> formatPaper(String paperId, SchoolTemplate template) async => getPaper(paperId);

  @override
  Future<String> exportPaper(String paperId, ExportFormat format) async {
    if (format != ExportFormat.pdf) {
      throw OfflineUnsupportedException('DOCX export');
    }
    final paper = await getPaper(paperId);
    // Real file, rendered on-device (see local_pdf_export.dart), returned
    // as an absolute local path. assessment_review_page.dart's open-button
    // routes non-http paths through `printing` (native share/view) instead
    // of launchUrl -- a raw file:// URI would hit Android's
    // FileUriExposedException on API 24+.
    return LocalPdfExporter.exportPaper(paper);
  }

  @override
  Future<List<SchoolTemplate>> getSchoolPaperTemplates(String schoolId) async {
    var stored = LocalStore.instance.templatesFor(schoolId);
    if (stored.isEmpty) {
      // A genuinely fresh install has no branding template yet -- the live
      // web app has the same requirement (a school sets one up via Template
      // Maker before its first paper), but there it's an existing school
      // with an existing template, so the gap never showed up in testing.
      // Offline, day one, "generate a paper" is the very first thing a
      // teacher does -- seeding a sensible default here is the difference
      // between that working and a dead-end exception on first use.
      final defaultTemplate = SchoolTemplate(
        id: _newId('template'),
        schoolId: schoolId,
        name: 'Default CBSE Template',
        tagline: '',
        brandColor: '#0A0A0A',
        headerHtml: '',
        footerHtml: '',
        logoUrl: '',
        marginTop: 20,
        marginBottom: 20,
        marginLeft: 20,
        marginRight: 20,
        fontFamily: 'Helvetica',
        fontSize: 11,
        lineHeight: 1.4,
        sectionFormatting: const {},
        isDefault: true,
      );
      LocalStore.instance.saveTemplate(schoolId, defaultTemplate.toJson());
      stored = LocalStore.instance.templatesFor(schoolId);
    }
    return stored.map((t) => SchoolTemplate.fromJson(t)).toList();
  }

  // ---------------- Answer Sheets (needs a scan -- offline unsupported) ----------------

  @override
  Future<AnswerSheet> uploadAnswerSheet(AnswerSheetUpload upload) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');

  @override
  Future<AnswerSheet> getAnswerSheet(String id) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');

  @override
  Future<List<AnswerSheet>> getAnswerSheets(String assessmentId) async => [];

  @override
  Future<AnswerSheet> processScan(ScanRequest request) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');

  @override
  Future<AnswerSheet> segmentAnswerSheet(String answerSheetId) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');

  @override
  Future<AnswerSheet> runOcr(String answerSheetId) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');

  @override
  Future<AnswerSheet> runVision(String answerSheetId) async =>
      throw OfflineUnsupportedException('Scan & Grade (handwriting OCR)');

  // ---------------- Evaluation ----------------

  @override
  Future<EvaluationResult> evaluateQuestion(EvaluationRequest request) async {
    final result =
        eval_engine.evaluateAnswer(request.question, request.answerScheme, request.studentAnswer);
    _recordMasteryFromEvaluation(request.context.studentId, request.question, result);
    LocalStore.instance.appendAuditLog(
      action: 'question_evaluated',
      assessmentId: request.context.assessmentId,
      studentId: request.context.studentId,
      details: {
        'questionId': request.question.id,
        'awardedMarks': result.awardedMarks,
        'maxMarks': result.maxMarks,
        'verdict': result.verdict,
      },
    );
    return EvaluationResult(
      id: _newId('eval'),
      awardedMarks: result.awardedMarks,
      maxMarks: result.maxMarks,
      percentage: result.percentage,
      verdict: _verdictFrom(result.verdict),
      markingPoints: result.markingPoints
          .map((m) => MarkingPointResult(
                markingPointId: m.markingPointId,
                awarded: m.awarded,
                reason: m.reason,
                similarityScore: m.similarity,
              ))
          .toList(),
      rubricLevel: RubricLevelResult(
        level: result.verdict == 'fullCredit' ? 1 : 0,
        label: result.verdict,
        justification: result.reasoning,
      ),
      confidenceScore: result.confidence,
      reasoning: result.reasoning,
      strengths: result.strengths,
      gaps: result.gaps,
      carelessErrors: const [],
      estimatedTimeSpentSeconds: 0,
    );
  }

  EvaluationVerdict _verdictFrom(String v) => switch (v) {
        'fullCredit' => EvaluationVerdict.fullCredit,
        'partialCredit' => EvaluationVerdict.partialCredit,
        'blank' => EvaluationVerdict.blank,
        _ => EvaluationVerdict.noCredit,
      };

  // Was a hand-duplicated copy of LocalPillarApi's mastery update (found by
  // audit) that had silently diverged: the new-concept branch below only
  // ever assigned 'needsReview'/'developing', never 'proficient', even when
  // a student's very first evaluated answer for a concept scored >=80%. Now
  // shares the single-sourced helper so the two paths can't drift again.
  void _recordMasteryFromEvaluation(String studentId, Question question, eval_engine.LocalEvaluation result) {
    if (studentId.isEmpty) return;
    final conceptId = question.chapterIds.isNotEmpty ? question.chapterIds.first : 'general';
    final existing = LocalStore.instance.getMastery(studentId);
    final concepts = ((existing?['concepts'] as List?) ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    final idx = concepts.indexWhere((c) => c['conceptId'] == conceptId);
    final observed = result.maxMarks > 0 ? result.awardedMarks / result.maxMarks : 0.0;
    final updated = updatedConceptMastery(
      conceptId: conceptId,
      existing: idx >= 0 ? concepts[idx] : null,
      observed: observed,
    );
    if (idx >= 0) {
      concepts[idx] = updated;
    } else {
      concepts.add(updated);
    }
    saveMasteryRollup(studentId, concepts);
  }

  @override
  Future<List<EvaluationResult>> evaluateAnswerSheet(String answerSheetId) async => [];

  @override
  Future<EvaluationResult> teacherReview(TeacherReviewRequest request) async =>
      throw Exception('Stored evaluations for teacher review are not tracked individually offline yet.');

  @override
  Future<void> finalizeEvaluation(String answerSheetId) async {}

  @override
  Future<List<EvaluationResult>> getEvaluations(String answerSheetId) async => [];

  // ---------------- Mastery ----------------
  // LocalStore keeps a simpler mastery shape (see _recordMasteryFromEvaluation
  // above and LocalPillarApi's own updateMasteryFromSheet) shared with the
  // lighter PillarApi.StudentMastery view. ApiClient's StudentMastery is the
  // richer domain entity (chapter/subject rollups, a MasterySummary) --
  // converted here rather than duplicating storage, so both call paths stay
  // backed by the same underlying evidence.

  StudentMastery _toDomainMastery(Map<String, dynamic> simple) {
    final rawConcepts = (simple['concepts'] as List? ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    final now = DateTime.now();
    final concepts = rawConcepts
        .map((c) => ConceptMastery(
              conceptId: c['conceptId'] as String? ?? '',
              conceptName: c['conceptName'] as String? ?? '',
              chapterId: c['conceptId'] as String? ?? '',
              subject: '',
              masteryScore: (c['mastery'] as num? ?? 0).toDouble(),
              confidenceScore: 0.7,
              retentionScore: (c['retention'] as num? ?? 0.9).toDouble(),
              totalAttempts: (c['evidenceCount'] as num? ?? 0).toInt(),
              correctAttempts: ((c['mastery'] as num? ?? 0) * (c['evidenceCount'] as num? ?? 0)).round(),
              consecutiveCorrect: 0,
              consecutiveIncorrect: 0,
              lastAttemptedAt: now,
              status: MasteryStatus.values.firstWhere(
                (s) => s.name == (c['status'] as String? ?? 'learning'),
                orElse: () => MasteryStatus.learning,
              ),
              misconceptions: const [],
              prerequisiteConceptIds: const [],
              difficulty: 0.5,
              timeSpentMinutes: 0,
            ))
        .toList();
    final overall = (simple['overallMastery'] as num? ?? 0).toDouble();
    final weakCount = concepts.where((c) => c.masteryScore < 0.5).length;
    return StudentMastery(
      studentId: simple['studentId'] as String? ?? '',
      schoolId: '',
      grade: '',
      concepts: concepts,
      chapters: const [],
      subjects: const [],
      summary: MasterySummary(
        overallMastery: overall,
        overallConfidence: 0.7,
        overallRetention: 0.9,
        totalConcepts: concepts.length,
        masteredConcepts: concepts.where((c) => c.masteryScore >= 0.8).length,
        weakConcepts: weakCount,
        notAttemptedConcepts: 0,
        totalQuestionsAttempted: concepts.fold(0, (s, c) => s + c.totalAttempts),
        totalQuestionsCorrect: concepts.fold(0, (s, c) => s + c.correctAttempts),
        accuracyRate: overall,
        bloomDistribution: const {},
        difficultyDistribution: const {},
        topStrengths: concepts.where((c) => c.masteryScore >= 0.8).map((c) => c.conceptName).toList(),
        topWeaknesses: concepts.where((c) => c.masteryScore < 0.5).map((c) => c.conceptName).toList(),
        recommendations: const [],
      ),
      lastUpdated: now,
      version: 1,
    );
  }

  @override
  Future<StudentMastery> getStudentMastery(String studentId) async {
    final j = LocalStore.instance.getMastery(studentId) ??
        {'studentId': studentId, 'overallMastery': 0.0, 'concepts': [], 'weakConcepts': []};
    return _toDomainMastery(j);
  }

  @override
  Future<StudentMastery> updateStudentMastery(StudentMastery mastery) async {
    LocalStore.instance.saveMastery(mastery.studentId, {
      'studentId': mastery.studentId,
      'overallMastery': mastery.summary.overallMastery,
      'concepts': mastery.concepts
          .map((c) => {
                'conceptId': c.conceptId,
                'conceptName': c.conceptName,
                'mastery': c.masteryScore,
                'retention': c.retentionScore,
                'evidenceCount': c.totalAttempts,
                'status': c.status.name,
                'isWeak': c.masteryScore < 0.5,
              })
          .toList(),
      'weakConcepts': mastery.concepts.where((c) => c.masteryScore < 0.5).map((c) => c.conceptName).toList(),
    });
    return mastery;
  }

  @override
  Future<List<ActionableRecommendation>> getRecommendations(String studentId) async => [];

  @override
  Future<void> recordMasteryAttempt(MasteryAttempt attempt) async {}

  @override
  Future<List<ConceptMastery>> getWeakConcepts(String studentId, {int limit = 10}) async {
    final m = await getStudentMastery(studentId);
    final weak = m.concepts.where((c) => c.masteryScore < 0.5).toList()
      ..sort((a, b) => a.masteryScore.compareTo(b.masteryScore));
    return weak.take(limit).toList();
  }

  @override
  Future<List<MisconceptionFlag>> getMisconceptions(String studentId) async => [];

  // ---------------- Analytics / Reports / Practice / Notifications ----------------
  // Not ported for this first on-device pass -- all genuinely need either
  // richer aggregation than a first pass warrants, or (reports/notifications)
  // touch things (email, WhatsApp deep links) that are inherently external.

  @override
  Future<AssessmentAnalytics> getAssessmentAnalytics(String assessmentId) async =>
      throw OfflineUnsupportedException('Assessment analytics dashboard');

  @override
  Future<ClassAnalytics> getClassAnalytics(String classId) async =>
      throw OfflineUnsupportedException('Class analytics dashboard');

  @override
  Future<StudentAnalytics> getStudentAnalytics(String studentId) async =>
      throw OfflineUnsupportedException('Student analytics dashboard');

  @override
  Future<SchoolAnalytics> getSchoolAnalytics(String schoolId) async =>
      throw OfflineUnsupportedException('School analytics dashboard');

  @override
  Future<StudentReport> generateStudentReport(ReportRequest request) async =>
      throw OfflineUnsupportedException('PDF report generation');

  @override
  Future<String> exportReport(String reportId, ExportFormat format) async =>
      throw OfflineUnsupportedException('Report export');

  @override
  Future<List<StudentReport>> generateBulkReports(BulkReportRequest request) async =>
      throw OfflineUnsupportedException('Bulk report generation');

  @override
  Future<ParentReport> generateParentReport(ReportRequest request) async =>
      throw OfflineUnsupportedException('Parent report generation');

  @override
  Future<PracticeSession> createPracticeSession(PracticeRequest request) async =>
      throw OfflineUnsupportedException('Practice sessions');

  @override
  Future<PracticeSession> getPracticeSession(String id) async =>
      throw OfflineUnsupportedException('Practice sessions');

  @override
  Future<PracticeResult> submitPractice(PracticeSubmission submission) async =>
      throw OfflineUnsupportedException('Practice sessions');

  @override
  Future<List<PracticeSession>> getStudentPracticeSessions(String studentId) async => [];

  @override
  Future<void> sendNotification(Notification notification) async {}

  @override
  Future<void> sendWhatsAppNotification(WhatsAppDeepLink link) async =>
      throw OfflineUnsupportedException('WhatsApp notifications');

  @override
  Future<List<Notification>> getNotifications(String userId) async => [];

  @override
  Future<void> markAsRead(String notificationId) async {}
}

extension _FirstOrNull<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
