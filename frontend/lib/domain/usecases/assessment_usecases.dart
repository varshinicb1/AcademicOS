import 'package:dartz/dartz.dart';

import '../../domain/entities/assessment.dart';
import '../../domain/entities/question.dart';
import '../../domain/entities/enums.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';

// 2026-09-17: removed 11 use cases (ScanAnswerSheetUseCase,
// EvaluateAnswerSheetUseCase, TeacherReviewUseCase, FinalizeEvaluationUseCase,
// GetStudentMasteryUseCase, GetRecommendationsUseCase,
// CreatePracticeSessionUseCase, SubmitPracticeUseCase,
// GetAssessmentAnalyticsUseCase, GenerateStudentReportUseCase,
// SendWhatsAppNotificationUseCase) that depended on the repositories removed
// in repositories_impl.dart -- confirmed never constructed by
// service_locator.dart (see its own comment there) and unreferenced by any
// screen. Only the 3 use cases the app actually registers/uses remain.

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
    int setCount = 1,
    String? tier,
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
      setCount: setCount,
      tier: tier,
    );

    return _paperRepository.generatePaper(request);
  }
}
