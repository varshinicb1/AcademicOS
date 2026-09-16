import 'dart:math';

import 'package:dio/dio.dart';

import '../../data/datasources/api/api_client.dart';
import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import '../constants/app_constants.dart';
import 'corpus_repository.dart';
import 'local_pdf_export.dart';
import 'local_pillar_api.dart' show OfflineUnsupportedException;
import 'local_store.dart';
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
///
/// 2026-09-17: removed the 41 overrides of methods no longer on ApiClient
/// (their backend routes never existed and had no live caller in either
/// build -- see api_client.dart's own note and docs/system-review.html).
/// `getQuestionsByIds` is kept as a plain (no-longer-@override) method:
/// unlike the others it's a real internal dependency of `generateFromIds`
/// below, just no longer part of the public ApiClient contract.
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
  Future<List<SectionBlueprint>> getSchoolTemplates(String schoolId) async {
    return selection_engine.defaultSections(100);
  }

  // ---------------- Questions ----------------

  @override
  Future<List<Question>> searchQuestions(QuestionSearchParams params) async {
    await CorpusRepository.instance.ensureLoaded();
    return CorpusRepository.instance.search(params);
  }

  /// No longer an @override (the base ApiClient method it used to mirror
  /// called a backend route -- /questions/batch -- that never existed and
  /// had no live caller; see api_client.dart's 2026-09-17 note). Kept as a
  /// plain method because generateFromIds below genuinely needs it.
  Future<List<Question>> getQuestionsByIds(List<String> ids) async {
    await CorpusRepository.instance.ensureLoaded();
    final wanted = ids.toSet();
    return CorpusRepository.instance.all.where((q) => wanted.contains(q.id)).toList();
  }

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
                  internalChoiceText: q.metadata['internal_choice_stem'] as String?,
                  internalChoiceQuestionId: q.metadata['internal_choice_id'] as String?,
                  isCompetency: q.type == QuestionType.caseStudy ||
                      q.type == QuestionType.competencyBased ||
                      q.type == QuestionType.assertionReason ||
                      (q.metadata['competency'] == true),
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
      setLabel: request.setCount > 1 ? 'A' : null,
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
        setLabel: request.setCount > 1 ? 'A' : null,
        tier: request.tier,
      ),
    );

    final paperSets = <GeneratedPaper>[];
    if (request.setCount > 1) {
      final setLabels = ['A', 'B', 'C'];
      for (var sIdx = 0; sIdx < request.setCount && sIdx < setLabels.length; sIdx++) {
        final label = setLabels[sIdx];
        if (sIdx == 0) {
          paperSets.add(paper);
          continue;
        }
        final rotatedSections = <GeneratedSection>[];
        var dNum = 1;
        for (final sec in sections) {
          final isObjective = sec.questions.every((q) => q.type == 'mcq' || q.type == 'assertionReason');
          var qList = List<GeneratedQuestion>.from(sec.questions);
          if (isObjective && qList.length > 1) {
            var shift = (sIdx * 3) % qList.length;
            if (shift == 0) shift = 1;
            qList = [...qList.sublist(shift), ...qList.sublist(0, shift)];
          }
          final swapped = qList.map((q) {
            final hasChoice = q.internalChoiceText != null && q.internalChoiceText!.isNotEmpty;
            if (hasChoice && sIdx % 2 == 1) {
              return q.copyWith(
                displayNumber: dNum++,
                stem: q.internalChoiceText!,
                internalChoiceText: q.stem,
                internalChoiceQuestionId: q.questionId,
              );
            }
            return q.copyWith(displayNumber: dNum++);
          }).toList();
          rotatedSections.add(sec.copyWith(questions: swapped));
        }
        final setPaper = paper.copyWith(
          id: '${paper.id}_set_$label',
          setLabel: label,
          sections: rotatedSections,
          metadata: paper.metadata.copyWith(setLabel: label),
        );
        paperSets.add(setPaper);
        LocalStore.instance.savePaper(setPaper.id, setPaper.toJson());
      }
    }
    final primaryPaper = paper.copyWith(sets: paperSets);
    LocalStore.instance.savePaper(primaryPaper.id, primaryPaper.toJson());
    LocalStore.instance.upsertAssessment(
      assessment
          .copyWith(status: AssessmentStatus.paperGenerated, generatedPaperId: primaryPaper.id, updatedAt: DateTime.now())
          .toJson(),
    );
    return primaryPaper;
  }

  @override
  Future<GeneratedPaper> quickGeneratePaper(QuickPaperRequest request) async {
    await CorpusRepository.instance.ensureLoaded();
    const schoolId = AppConstants.currentSchoolId;
    final assessment = Assessment(
      id: _newId('asm_quick'),
      schoolId: schoolId,
      teacherId: 'teacher_1',
      title: request.title ?? '${request.subject} Grade ${request.grade} Quick Paper',
      subject: request.subject,
      grade: request.grade,
      chapterIds: request.chapterIds,
      blueprint: Blueprint(
        totalMarks: request.totalMarks,
        durationMinutes: request.durationMinutes ?? (request.totalMarks <= 25 ? 45 : request.totalMarks <= 50 ? 90 : 180),
        difficulty: const DifficultyDistribution(easy: 0.3, medium: 0.5, hard: 0.2),
        bloom: const BloomDistribution(remember: 0.2, understand: 0.25, apply: 0.3, analyze: 0.15, evaluate: 0.05, create: 0.05),
        chapterWeights: const ChapterWeights(weights: {}),
        competencyWeights: const CompetencyWeights(weights: {}),
        sections: [
          const SectionBlueprint(id: 'A', label: 'A', name: 'MCQs', marksPerQuestion: 1, questionCount: 5, totalMarks: 5, allowedBloomLevels: [BloomLevel.remember, BloomLevel.understand], allowedDifficulties: [Difficulty.easy, Difficulty.medium]),
          const SectionBlueprint(id: 'B', label: 'B', name: 'Short Answer', marksPerQuestion: 2, questionCount: 3, totalMarks: 6, allowedBloomLevels: [BloomLevel.understand, BloomLevel.apply], allowedDifficulties: [Difficulty.easy, Difficulty.medium]),
          const SectionBlueprint(id: 'C', label: 'C', name: 'Long Answer', marksPerQuestion: 3, questionCount: 3, totalMarks: 9, allowedBloomLevels: [BloomLevel.apply, BloomLevel.analyze], allowedDifficulties: [Difficulty.medium, Difficulty.hard], hasInternalChoice: true, internalChoiceCount: 1),
        ],
        tier: request.tier,
        examType: request.examType,
      ),
      status: AssessmentStatus.draft,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
    LocalStore.instance.upsertAssessment(assessment.toJson());

    final searchParams = QuestionSearchParams(
      subject: request.subject,
      grade: request.grade,
      chapterIds: request.chapterIds.isEmpty ? null : request.chapterIds,
      limit: 100,
    );
    final candidates = CorpusRepository.instance.search(searchParams);
    final selected = (candidates.isNotEmpty ? candidates : CorpusRepository.instance.all.where((q) => q.subject == request.subject).toList()).take(11).toList();

    final templates = await getSchoolPaperTemplates(schoolId);
    final template = templates.firstWhere((t) => t.isDefault, orElse: () => templates.first);

    return generatePaper(PaperGenerationRequest(
      assessmentId: assessment.id,
      blueprint: assessment.blueprint,
      selectedQuestions: selected,
      template: template,
      setCount: request.setCount,
      tier: request.tier,
    ));
  }

  @override
  Future<GeneratedPaper> generateFromIds(GenerateFromIdsRequest request) async {
    await CorpusRepository.instance.ensureLoaded();
    const schoolId = AppConstants.currentSchoolId;
    final questions = await getQuestionsByIds(request.questionIds);
    if (questions.isEmpty) throw Exception('No valid questions found for the given IDs.');

    final totalMarks = questions.fold(0, (sum, q) => sum + q.marks);
    final assessment = Assessment(
      id: _newId('asm_curated'),
      schoolId: schoolId,
      teacherId: 'teacher_1',
      title: request.title ?? '${request.subject} Curated Paper',
      subject: request.subject,
      grade: request.grade,
      chapterIds: questions.expand((q) => q.chapterIds).toSet().toList(),
      blueprint: Blueprint(
        totalMarks: totalMarks,
        durationMinutes: (totalMarks * 2).clamp(30, 180),
        difficulty: const DifficultyDistribution(easy: 0.3, medium: 0.5, hard: 0.2),
        bloom: const BloomDistribution(remember: 0.2, understand: 0.25, apply: 0.3, analyze: 0.15, evaluate: 0.05, create: 0.05),
        chapterWeights: const ChapterWeights(weights: {}),
        competencyWeights: const CompetencyWeights(weights: {}),
        sections: [
          for (final m in (questions.map((q) => q.marks).toSet().toList()..sort()))
            SectionBlueprint(
              id: 'sec_$m',
              label: 'Section ${m}M',
              name: '$m-Mark Questions',
              marksPerQuestion: m,
              questionCount: questions.where((q) => q.marks == m).length,
              totalMarks: questions.where((q) => q.marks == m).fold(0, (s, q) => s + q.marks),
              allowedBloomLevels: BloomLevel.values,
              allowedDifficulties: Difficulty.values,
            ),
        ],
        tier: request.tier,
        examType: request.examType,
      ),
      status: AssessmentStatus.draft,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
    LocalStore.instance.upsertAssessment(assessment.toJson());

    final templates = await getSchoolPaperTemplates(schoolId);
    final template = request.template ?? (templates.isNotEmpty ? templates.first : templates.first);

    return generatePaper(PaperGenerationRequest(
      assessmentId: assessment.id,
      blueprint: assessment.blueprint,
      selectedQuestions: questions,
      template: template,
      setCount: request.setCount,
      tier: request.tier,
    ));
  }

  @override
  Future<GeneratedPaper> getPaper(String paperId) async {
    final j = LocalStore.instance.getPaper(paperId);
    if (j == null) throw Exception('Paper $paperId not found on this device.');
    return GeneratedPaper.fromJson(j);
  }

  @override
  Future<String> exportPaper(String paperId, ExportFormat format) async {
    final paper = await getPaper(paperId);
    if (format == ExportFormat.answerKey) {
      return LocalPdfExporter.exportAnswerKey(paper);
    }
    if (format != ExportFormat.pdf) {
      throw OfflineUnsupportedException('DOCX export');
    }
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

  // ---------------- Practice ----------------
  // Not ported for this first on-device pass -- practice sessions need
  // richer aggregation than a first pass warrants. submitPractice is a real,
  // matched route on the online path; offline just declares it unsupported
  // rather than silently no-op'ing.

  @override
  Future<PracticeResult> submitPractice(PracticeSubmission submission) async =>
      throw OfflineUnsupportedException('Practice sessions');
}

extension _FirstOrNull<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
