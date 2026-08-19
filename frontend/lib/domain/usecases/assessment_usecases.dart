import 'package:dartz/dartz.dart';

import '../../domain/entities/assessment.dart';
import '../../domain/entities/question.dart';
import '../../domain/entities/answer_sheet.dart';
import '../../domain/entities/mastery.dart';
import '../../domain/entities/analytics.dart';
import '../../domain/entities/report.dart';
import '../../domain/entities/enums.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';

/// Use case for creating an assessment with AI-generated blueprint
class CreateAssessmentUseCase {
  final AssessmentRepository _assessmentRepository;
  final BlueprintRepository _blueprintRepository;

  CreateAssessmentUseCase(this._assessmentRepository, this._blueprintRepository);

  Future<Either<Failure, Assessment>> call(CreateAssessmentRequest request) async {
    final blueprintResult = await _blueprintRepository.generateBlueprint(request.blueprint);
    if (blueprintResult.isLeft()) return left(blueprintResult.fold((l) => l, (r) => throw UnimplementedError()));

    final blueprint = blueprintResult.fold((l) => throw UnimplementedError(), (r) => r);

    final assessment = Assessment(
      id: '',
      schoolId: request.schoolId,
      teacherId: request.teacherId,
      title: request.title,
      subject: request.subject,
      grade: request.grade,
      chapterIds: request.chapterIds,
      blueprint: blueprint,
      status: AssessmentStatus.draft,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    return _assessmentRepository.createAssessment(assessment);
  }
}

/// Use case for AI-powered question selection and optimization
class SelectQuestionsUseCase {
  final QuestionRepository _questionRepository;

  SelectQuestionsUseCase(this._questionRepository);

  Future<Either<Failure, QuestionOptimizationResult>> call({
    required Blueprint blueprint,
    required QuestionSearchParams searchParams,
    Map<String, double>? studentMastery,
  }) async {
    final candidatesResult = await _questionRepository.searchQuestions(searchParams);
    if (candidatesResult.isLeft()) return left(candidatesResult.fold((l) => l, (r) => throw UnimplementedError()));

    final candidates = candidatesResult.fold((l) => throw UnimplementedError(), (r) => r);

    return _questionRepository.optimizeQuestions(candidates, blueprint);
  }
}

/// Use case for generating a formatted question paper
class GeneratePaperUseCase {
  final PaperGenerationRepository _paperRepository;

  GeneratePaperUseCase(this._paperRepository);

  Future<Either<Failure, GeneratedPaper>> call({
    required String assessmentId,
    required Blueprint blueprint,
    required List<Question> selectedQuestions,
    required String schoolId,
  }) async {
    final templatesResult = await _paperRepository.getSchoolTemplates(schoolId);
    if (templatesResult.isLeft()) return left(templatesResult.fold((l) => l, (r) => throw UnimplementedError()));

    final templates = templatesResult.fold((l) => throw UnimplementedError(), (r) => r);
    if (templates.isEmpty) {
      return left(NotFoundFailure('No paper template configured for school $schoolId'));
    }
    final template = templates.firstWhere((t) => t.isDefault, orElse: () => templates.first);

    final request = PaperGenerationRequest(
      assessmentId: assessmentId,
      blueprint: blueprint,
      selectedQuestions: selectedQuestions,
      template: template,
    );

    return _paperRepository.generatePaper(request);
  }
}

/// Use case for scanning and processing answer sheets
class ScanAnswerSheetUseCase {
  final AnswerSheetRepository _answerSheetRepository;

  ScanAnswerSheetUseCase(this._answerSheetRepository);

  Future<Either<Failure, AnswerSheet>> call(AnswerSheetUpload upload) async {
    final uploadResult = await _answerSheetRepository.uploadAnswerSheet(upload);
    if (uploadResult.isLeft()) return left(uploadResult.fold((l) => l, (r) => throw UnimplementedError()));

    final answerSheet = uploadResult.fold((l) => throw UnimplementedError(), (r) => r);

    final scanRequest = ScanRequest(
      answerSheetId: answerSheet.id,
      imagePaths: upload.imagePaths,
      options: const ScanOptions(),
    );

    final scanResult = await _answerSheetRepository.processScan(scanRequest);
    if (scanResult.isLeft()) return left(scanResult.fold((l) => l, (r) => throw UnimplementedError()));

    final scannedSheet = scanResult.fold((l) => throw UnimplementedError(), (r) => r);

    final segmentResult = await _answerSheetRepository.segmentAnswerSheet(scannedSheet.id);
    if (segmentResult.isLeft()) return left(segmentResult.fold((l) => l, (r) => throw UnimplementedError()));

    final segmentedSheet = segmentResult.fold((l) => throw UnimplementedError(), (r) => r);

    final ocrResult = await _answerSheetRepository.runOcr(segmentedSheet.id);
    if (ocrResult.isLeft()) return left(ocrResult.fold((l) => l, (r) => throw UnimplementedError()));

    final ocrSheet = ocrResult.fold((l) => throw UnimplementedError(), (r) => r);

    final visionResult = await _answerSheetRepository.runVision(ocrSheet.id);
    return visionResult;
  }
}

/// Use case for AI evaluation of answer sheets
class EvaluateAnswerSheetUseCase {
  final EvaluationRepository _evaluationRepository;

  EvaluateAnswerSheetUseCase(this._evaluationRepository);

  Future<Either<Failure, List<EvaluationResult>>> call(String answerSheetId) async {
    return _evaluationRepository.evaluateAnswerSheet(answerSheetId);
  }
}

/// Use case for teacher review of AI evaluations
class TeacherReviewUseCase {
  final EvaluationRepository _evaluationRepository;

  TeacherReviewUseCase(this._evaluationRepository);

  Future<Either<Failure, EvaluationResult>> call(TeacherReviewRequest request) async {
    return _evaluationRepository.teacherReview(request);
  }
}

/// Use case for finalizing evaluations and generating reports
class FinalizeEvaluationUseCase {
  final EvaluationRepository _evaluationRepository;
  final ReportRepository _reportRepository;
  final MasteryRepository _masteryRepository;
  final NotificationRepository _notificationRepository;

  FinalizeEvaluationUseCase(
    this._evaluationRepository,
    this._reportRepository,
    this._masteryRepository,
    this._notificationRepository,
  );

  Future<Either<Failure, List<StudentReport>>> call({
    required String assessmentId,
    required List<String> studentIds,
    required String teacherId,
  }) async {
    final finalizeResult = await _evaluationRepository.finalizeEvaluation(assessmentId);
    if (finalizeResult.isLeft()) return left(finalizeResult.fold((l) => l, (r) => throw UnimplementedError()));

    final bulkRequest = BulkReportRequest(
      assessmentId: assessmentId,
      studentIds: studentIds,
      type: ReportType.studentDetailed,
    );

    final reportsResult = await _reportRepository.generateBulkReports(bulkRequest);
    if (reportsResult.isLeft()) return left(reportsResult.fold((l) => l, (r) => throw UnimplementedError()));

    final reports = reportsResult.fold((l) => throw UnimplementedError(), (r) => r);

    for (final report in reports) {
      await _notificationRepository.sendNotification(Notification(
        id: '',
        userId: report.studentId,
        type: NotificationType.reportReady,
        title: 'Report Ready',
        body: 'Your assessment report for ${report.assessmentTitle} is ready.',
        data: {'assessmentId': assessmentId, 'reportId': report.id},
        createdAt: DateTime.now(),
        isRead: false,
      ));
    }

    return right(reports);
  }
}

/// Use case for getting student mastery and recommendations
class GetStudentMasteryUseCase {
  final MasteryRepository _masteryRepository;

  GetStudentMasteryUseCase(this._masteryRepository);

  Future<Either<Failure, StudentMastery>> call(String studentId) async {
    return _masteryRepository.getMastery(studentId);
  }
}

/// Use case for getting personalized recommendations
class GetRecommendationsUseCase {
  final MasteryRepository _masteryRepository;

  GetRecommendationsUseCase(this._masteryRepository);

  Future<Either<Failure, List<ActionableRecommendation>>> call(String studentId) async {
    return _masteryRepository.getRecommendations(studentId);
  }
}

/// Use case for creating personalized practice sessions
class CreatePracticeSessionUseCase {
  final PracticeRepository _practiceRepository;
  final MasteryRepository _masteryRepository;

  CreatePracticeSessionUseCase(this._practiceRepository, this._masteryRepository);

  Future<Either<Failure, PracticeSession>> call({
    required String studentId,
    List<String>? conceptIds,
    PracticeType? type,
    int? questionCount,
    int? durationMinutes,
  }) async {
    final targetConcepts = conceptIds ?? (await _getWeakConcepts(studentId));

    final request = PracticeRequest(
      studentId: studentId,
      conceptIds: targetConcepts,
      type: type ?? PracticeType.remedial,
      questionCount: questionCount ?? 10,
      durationMinutes: durationMinutes ?? 30,
    );

    return _practiceRepository.createPracticeSession(request);
  }

  Future<List<String>> _getWeakConcepts(String studentId) async {
    final masteryResult = await _masteryRepository.getMastery(studentId);
    if (masteryResult.isLeft()) return [];

    final mastery = masteryResult.fold((l) => throw UnimplementedError(), (r) => r);
    return mastery.concepts
        .where((c) => c.status == MasteryStatus.developing || c.status == MasteryStatus.needsReview || c.status == MasteryStatus.learning)
        .take(5)
        .map((c) => c.conceptId)
        .toList();
  }
}

/// Use case for submitting practice and getting results
class SubmitPracticeUseCase {
  final PracticeRepository _practiceRepository;
  final MasteryRepository _masteryRepository;

  SubmitPracticeUseCase(this._practiceRepository, this._masteryRepository);

  Future<Either<Failure, PracticeResult>> call(PracticeSubmission submission) async {
    final result = await _practiceRepository.submitPractice(submission);
    if (result.isLeft()) return left(result.fold((l) => l, (r) => throw UnimplementedError()));

    final practiceResult = result.fold((l) => throw UnimplementedError(), (r) => r);

    for (final answer in submission.answers) {
      // TODO: map answer -> concept recording
    }

    return right(practiceResult);
  }
}

/// Use case for getting assessment analytics
class GetAssessmentAnalyticsUseCase {
  final AnalyticsRepository _analyticsRepository;

  GetAssessmentAnalyticsUseCase(this._analyticsRepository);

  Future<Either<Failure, AssessmentAnalytics>> call(String assessmentId) async {
    return _analyticsRepository.getAssessmentAnalytics(assessmentId);
  }
}

/// Use case for generating student report
class GenerateStudentReportUseCase {
  final ReportRepository _reportRepository;

  GenerateStudentReportUseCase(this._reportRepository);

  Future<Either<Failure, StudentReport>> call({
    required String assessmentId,
    required String studentId,
  }) async {
    final request = ReportRequest(
      assessmentId: assessmentId,
      studentId: studentId,
      type: ReportType.studentDetailed,
    );

    return _reportRepository.generateStudentReport(request);
  }
}

/// Use case for sending WhatsApp notification with deep link
class SendWhatsAppNotificationUseCase {
  final NotificationRepository _notificationRepository;

  SendWhatsAppNotificationUseCase(this._notificationRepository);

  Future<Either<Failure, Unit>> call({
    required String phoneNumber,
    required String message,
    required String deepLinkUrl,
  }) async {
    final link = WhatsAppDeepLink(
      phoneNumber: phoneNumber,
      message: message,
      deepLinkUrl: deepLinkUrl,
      fallbackUrl: 'https://assessmentos.app',
    );

    return _notificationRepository.sendWhatsAppDeepLink(link);
  }
}
