import 'package:dartz/dartz.dart';

import '../entities/entities.dart';
import '../failures/failures.dart';
import 'requests.dart';

abstract class AssessmentRepository {
  Future<Either<Failure, Assessment>> createAssessment(Assessment assessment);
  Future<Either<Failure, Assessment>> getAssessment(String id);
  Future<Either<Failure, List<Assessment>>> getAssessmentsByTeacher(String teacherId);
  Future<Either<Failure, List<Assessment>>> getAssessmentsBySchool(String schoolId);
  Future<Either<Failure, Assessment>> updateAssessment(Assessment assessment);
  Future<Either<Failure, Unit>> deleteAssessment(String id);
  Future<Either<Failure, Assessment>> updateStatus(String id, AssessmentStatus status);
}

// 2026-09-17: getBlueprint/updateBlueprint/saveTemplate removed -- their
// backend routes never existed and had no live caller in either build
// (see api_client.dart's note and docs/system-review.html).
abstract class BlueprintRepository {
  Future<Either<Failure, Blueprint>> generateBlueprint(BlueprintRequest request);
  Future<Either<Failure, List<SectionBlueprint>>> getSchoolTemplates(String schoolId);
}

// 2026-09-17: getQuestion/getQuestionsByIds/createQuestion/updateQuestion/
// deleteQuestion removed -- same reason as above. getQuestionsForBlueprint
// is unrelated (implemented via searchQuestions, not a dead route) and kept.
abstract class QuestionRepository {
  Future<Either<Failure, List<Question>>> searchQuestions(QuestionSearchParams params);
  Future<Either<Failure, List<Question>>> getQuestionsForBlueprint(Blueprint blueprint);
  Future<Either<Failure, QuestionOptimizationResult>> optimizeQuestions(
    List<Question> candidates,
    Blueprint blueprint,
  );
}

abstract class PaperGenerationRepository {
  Future<Either<Failure, GeneratedPaper>> generatePaper(PaperGenerationRequest request);
  Future<Either<Failure, GeneratedPaper>> quickGeneratePaper(QuickPaperRequest request);
  Future<Either<Failure, GeneratedPaper>> generateFromIds(GenerateFromIdsRequest request);
  Future<Either<Failure, List<SchoolTemplate>>> getSchoolTemplates(String schoolId);
  Future<Either<Failure, String>> exportPaper(GeneratedPaper paper, ExportFormat format);
}

// 2026-09-17: PracticeRepository trimmed to just submitPractice -- the only
// one of its four methods backed by a real route (POST /practice/submit).
// createPracticeSession/getPracticeSession/getStudentSessions removed.
// AnswerSheetRepository, EvaluationRepository, MasteryRepository,
// AnalyticsRepository, ReportRepository, and NotificationRepository were
// removed entirely -- every method on each mapped to a backend route that
// never existed, confirmed to have zero live callers through any path
// (screen, bloc, use case, or DI resolution) in either build variant. See
// docs/system-review.html's "Two systems, one interface, neither complete"
// finding and the (now-empty) KNOWN_GAPS in
// tests/test_frontend_backend_contract.py.
abstract class PracticeRepository {
  Future<Either<Failure, PracticeResult>> submitPractice(PracticeSubmission submission);
}
