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

abstract class BlueprintRepository {
  Future<Either<Failure, Blueprint>> generateBlueprint(BlueprintRequest request);
  Future<Either<Failure, Blueprint>> getBlueprint(String assessmentId);
  Future<Either<Failure, Blueprint>> updateBlueprint(Blueprint blueprint);
  Future<Either<Failure, List<SectionBlueprint>>> getSchoolTemplates(String schoolId);
  Future<Either<Failure, Unit>> saveTemplate(SectionBlueprint template);
}

abstract class QuestionRepository {
  Future<Either<Failure, List<Question>>> searchQuestions(QuestionSearchParams params);
  Future<Either<Failure, Question>> getQuestion(String id);
  Future<Either<Failure, List<Question>>> getQuestionsByIds(List<String> ids);
  Future<Either<Failure, Question>> createQuestion(Question question);
  Future<Either<Failure, Question>> updateQuestion(Question question);
  Future<Either<Failure, Unit>> deleteQuestion(String id);
  Future<Either<Failure, List<Question>>> getQuestionsForBlueprint(Blueprint blueprint);
  Future<Either<Failure, QuestionOptimizationResult>> optimizeQuestions(
    List<Question> candidates,
    Blueprint blueprint,
  );
}

abstract class PaperGenerationRepository {
  Future<Either<Failure, GeneratedPaper>> generatePaper(PaperGenerationRequest request);
  Future<Either<Failure, List<SchoolTemplate>>> getSchoolTemplates(String schoolId);
  Future<Either<Failure, String>> exportPaper(GeneratedPaper paper, ExportFormat format);
}

abstract class AnswerSheetRepository {
  Future<Either<Failure, AnswerSheet>> uploadAnswerSheet(AnswerSheetUpload upload);
  Future<Either<Failure, AnswerSheet>> getAnswerSheet(String id);
  Future<Either<Failure, List<AnswerSheet>>> getAnswerSheets(String assessmentId);
  Future<Either<Failure, AnswerSheet>> processScan(ScanRequest request);
  Future<Either<Failure, AnswerSheet>> segmentAnswerSheet(String answerSheetId);
  Future<Either<Failure, AnswerSheet>> runOcr(String answerSheetId);
  Future<Either<Failure, AnswerSheet>> runVision(String answerSheetId);
}

abstract class EvaluationRepository {
  Future<Either<Failure, EvaluationResult>> evaluateQuestion(EvaluationRequest request);
  Future<Either<Failure, List<EvaluationResult>>> evaluateAnswerSheet(String answerSheetId);
  Future<Either<Failure, EvaluationResult>> teacherReview(TeacherReviewRequest request);
  Future<Either<Failure, Unit>> finalizeEvaluation(String answerSheetId);
}

abstract class MasteryRepository {
  Future<Either<Failure, StudentMastery>> getMastery(String studentId);
  Future<Either<Failure, StudentMastery>> updateMastery(StudentMastery mastery);
  Future<Either<Failure, List<ActionableRecommendation>>> getRecommendations(String studentId);
  Future<Either<Failure, Unit>> recordAttempt(MasteryAttempt attempt);
}

abstract class AnalyticsRepository {
  Future<Either<Failure, AssessmentAnalytics>> getAssessmentAnalytics(String assessmentId);
  Future<Either<Failure, ClassAnalytics>> getClassAnalytics(String classId);
  Future<Either<Failure, StudentAnalytics>> getStudentAnalytics(String studentId);
  Future<Either<Failure, SchoolAnalytics>> getSchoolAnalytics(String schoolId);
}

abstract class ReportRepository {
  Future<Either<Failure, StudentReport>> generateStudentReport(ReportRequest request);
  Future<Either<Failure, String>> exportReport(String reportId, ExportFormat format);
  Future<Either<Failure, List<StudentReport>>> generateBulkReports(BulkReportRequest request);
  Future<Either<Failure, ParentReport>> generateParentReport(ReportRequest request);
}

abstract class PracticeRepository {
  Future<Either<Failure, PracticeSession>> createPracticeSession(PracticeRequest request);
  Future<Either<Failure, PracticeSession>> getPracticeSession(String id);
  Future<Either<Failure, PracticeResult>> submitPractice(PracticeSubmission submission);
  Future<Either<Failure, List<PracticeSession>>> getStudentSessions(String studentId);
}

abstract class NotificationRepository {
  Future<Either<Failure, Unit>> sendNotification(Notification notification);
  Future<Either<Failure, Unit>> sendWhatsAppDeepLink(WhatsAppDeepLink link);
  Future<Either<Failure, List<Notification>>> getNotifications(String userId);
}