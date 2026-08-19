import 'dart:convert';
import 'package:dartz/dartz.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../domain/entities/entities.dart';
import '../../domain/entities/enums.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';
import '../datasources/api/api_client.dart';
import '../datasources/local/app_database.dart';

class BlueprintRepositoryImpl implements BlueprintRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  BlueprintRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, Blueprint>> generateBlueprint(BlueprintRequest request) async {
    try {
      final result = await _apiClient.generateBlueprint(request);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Blueprint>> getBlueprint(String assessmentId) async {
    try {
      final result = await _apiClient.getBlueprint(assessmentId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Blueprint>> updateBlueprint(Blueprint blueprint) async {
    try {
      final fakeAssessmentId = blueprint.metadata?['assessmentId'] as String? ?? '';
      final result = await _apiClient.updateBlueprint(fakeAssessmentId, blueprint);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<SectionBlueprint>>> getSchoolTemplates(String schoolId) async {
    try {
      final result = await _apiClient.getSchoolTemplates(schoolId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Unit>> saveTemplate(SectionBlueprint template) async {
    try {
      await _apiClient.saveTemplate('school_1', template);
      return right(unit);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class QuestionRepositoryImpl implements QuestionRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;
  final Box _cache;

  QuestionRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
    required Box cache,
  })  : _apiClient = apiClient,
        _localDb = localDb,
        _cache = cache;

  @override
  Future<Either<Failure, List<Question>>> searchQuestions(QuestionSearchParams params) async {
    try {
      final result = await _apiClient.searchQuestions(params);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Question>> getQuestion(String id) async {
    try {
      final cacheKey = 'question_$id';
      if (_cache.containsKey(cacheKey)) {
        return right(Question.fromJson(Map<String, dynamic>.from(_cache.get(cacheKey))));
      }

      final result = await _apiClient.getQuestion(id);
      _cache.put(cacheKey, result.toJson());
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<Question>>> getQuestionsByIds(List<String> ids) async {
    try {
      final result = await _apiClient.getQuestionsByIds(ids);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Question>> createQuestion(Question question) async {
    try {
      final result = await _apiClient.createQuestion(question);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Question>> updateQuestion(Question question) async {
    try {
      final result = await _apiClient.updateQuestion(question.id, question);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Unit>> deleteQuestion(String id) async {
    try {
      await _apiClient.deleteQuestion(id);
      return right(unit);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<Question>>> getQuestionsForBlueprint(Blueprint blueprint) async {
    try {
      final params = QuestionSearchParams(
        subject: blueprint.metadata?['subject'] as String? ?? 'Mathematics',
        grade: blueprint.metadata?['grade'] as int? ?? 10,
        limit: 200,
      );
      return searchQuestions(params);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, QuestionOptimizationResult>> optimizeQuestions(
    List<Question> candidates,
    Blueprint blueprint,
  ) async {
    try {
      final result = await _apiClient.optimizeQuestions(QuestionOptimizationRequest(
        candidates: candidates,
        blueprint: blueprint,
      ));
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class PaperGenerationRepositoryImpl implements PaperGenerationRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  PaperGenerationRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, GeneratedPaper>> generatePaper(PaperGenerationRequest request) async {
    try {
      final result = await _apiClient.generatePaper(request);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<SchoolTemplate>>> getSchoolTemplates(String schoolId) async {
    try {
      final result = await _apiClient.getSchoolPaperTemplates(schoolId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, String>> exportPaper(GeneratedPaper paper, ExportFormat format) async {
    try {
      final result = await _apiClient.exportPaper(paper.id, format);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class AnswerSheetRepositoryImpl implements AnswerSheetRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  AnswerSheetRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, AnswerSheet>> uploadAnswerSheet(AnswerSheetUpload upload) async {
    try {
      final result = await _apiClient.uploadAnswerSheet(upload);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, AnswerSheet>> processScan(ScanRequest request) async {
    try {
      final result = await _apiClient.processScan(request);
      return right(result);
    } catch (e) {
      return left(ScanningFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, AnswerSheet>> segmentAnswerSheet(String answerSheetId) async {
    try {
      final result = await _apiClient.segmentAnswerSheet(answerSheetId);
      return right(result);
    } catch (e) {
      return left(ScanningFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, AnswerSheet>> runOcr(String answerSheetId) async {
    try {
      final result = await _apiClient.runOcr(answerSheetId);
      return right(result);
    } catch (e) {
      return left(OcrFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, AnswerSheet>> runVision(String answerSheetId) async {
    try {
      final result = await _apiClient.runVision(answerSheetId);
      return right(result);
    } catch (e) {
      return left(VisionFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<AnswerSheet>>> getAnswerSheets(String assessmentId) async {
    try {
      final result = await _apiClient.getAnswerSheets(assessmentId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, AnswerSheet>> getAnswerSheet(String id) async {
    try {
      final result = await _apiClient.getAnswerSheet(id);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class EvaluationRepositoryImpl implements EvaluationRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  EvaluationRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, List<EvaluationResult>>> evaluateAnswerSheet(String answerSheetId) async {
    try {
      final result = await _apiClient.evaluateAnswerSheet(answerSheetId);
      return right(result);
    } catch (e) {
      return left(EvaluationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, EvaluationResult>> evaluateQuestion(EvaluationRequest request) async {
    try {
      final result = await _apiClient.evaluateQuestion(request);
      return right(result);
    } catch (e) {
      return left(EvaluationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, EvaluationResult>> teacherReview(TeacherReviewRequest request) async {
    try {
      final result = await _apiClient.teacherReview(request);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Unit>> finalizeEvaluation(String assessmentId) async {
    try {
      await _apiClient.finalizeEvaluation(assessmentId);
      return right(unit);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class MasteryRepositoryImpl implements MasteryRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  MasteryRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, StudentMastery>> getMastery(String studentId) async {
    try {
      final result = await _apiClient.getStudentMastery(studentId);
      return right(result);
    } catch (e) {
      return left(CacheFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<ActionableRecommendation>>> getRecommendations(String studentId) async {
    try {
      final result = await _apiClient.getRecommendations(studentId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Unit>> recordAttempt(MasteryAttempt attempt) async {
    try {
      await _apiClient.recordMasteryAttempt(attempt);
      return right(unit);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, StudentMastery>> updateMastery(StudentMastery mastery) async {
    try {
      final result = await _apiClient.updateStudentMastery(mastery);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class AnalyticsRepositoryImpl implements AnalyticsRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  AnalyticsRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, AssessmentAnalytics>> getAssessmentAnalytics(String assessmentId) async {
    try {
      final result = await _apiClient.getAssessmentAnalytics(assessmentId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, ClassAnalytics>> getClassAnalytics(String classId) async {
    try {
      final result = await _apiClient.getClassAnalytics(classId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, StudentAnalytics>> getStudentAnalytics(String studentId) async {
    try {
      final result = await _apiClient.getStudentAnalytics(studentId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, SchoolAnalytics>> getSchoolAnalytics(String schoolId) async {
    try {
      final result = await _apiClient.getSchoolAnalytics(schoolId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class ReportRepositoryImpl implements ReportRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  ReportRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, StudentReport>> generateStudentReport(ReportRequest request) async {
    try {
      final result = await _apiClient.generateStudentReport(request);
      return right(result);
    } catch (e) {
      return left(GenerationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<StudentReport>>> generateBulkReports(BulkReportRequest request) async {
    try {
      final result = await _apiClient.generateBulkReports(request);
      return right(result);
    } catch (e) {
      return left(GenerationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, ParentReport>> generateParentReport(ReportRequest request) async {
    try {
      final result = await _apiClient.generateParentReport(request);
      return right(result);
    } catch (e) {
      return left(GenerationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, String>> exportReport(String reportId, ExportFormat format) async {
    try {
      final result = await _apiClient.exportReport(reportId, format);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class PracticeRepositoryImpl implements PracticeRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  PracticeRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, PracticeSession>> createPracticeSession(PracticeRequest request) async {
    try {
      final result = await _apiClient.createPracticeSession(request);
      return right(result);
    } catch (e) {
      return left(GenerationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, PracticeSession>> getPracticeSession(String sessionId) async {
    try {
      final result = await _apiClient.getPracticeSession(sessionId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, PracticeResult>> submitPractice(PracticeSubmission submission) async {
    try {
      final result = await _apiClient.submitPractice(submission);
      return right(result);
    } catch (e) {
      return left(EvaluationFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<PracticeSession>>> getStudentSessions(String studentId) async {
    try {
      final result = await _apiClient.getStudentPracticeSessions(studentId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}

class NotificationRepositoryImpl implements NotificationRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  NotificationRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, Unit>> sendNotification(Notification notification) async {
    try {
      await _apiClient.sendNotification(notification);
      return right(unit);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<Notification>>> getNotifications(String userId) async {
    try {
      final result = await _apiClient.getNotifications(userId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Unit>> sendWhatsAppDeepLink(WhatsAppDeepLink link) async {
    try {
      await _apiClient.sendWhatsAppNotification(link);
      return right(unit);
    } catch (e) {
      return left(NetworkFailure(e.toString()));
    }
  }
}
