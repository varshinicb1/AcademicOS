import 'package:dartz/dartz.dart';

import '../../domain/entities/entities.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';
import '../datasources/api/api_client.dart';
import '../datasources/api/api_error.dart';
import '../datasources/local/app_database.dart';

// 2026-09-17: AnswerSheetRepositoryImpl, EvaluationRepositoryImpl,
// MasteryRepositoryImpl, AnalyticsRepositoryImpl, ReportRepositoryImpl, and
// NotificationRepositoryImpl removed entirely -- every method on each called
// a backend route that never existed, with zero live callers through any
// path in either build. BlueprintRepositoryImpl/QuestionRepositoryImpl/
// PracticeRepositoryImpl trimmed to their real methods only. See
// domain/repositories/repositories.dart's matching note.

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
      return left(ServerFailure(serverErrorMessage(e)));
    }
  }

  @override
  Future<Either<Failure, List<SectionBlueprint>>> getSchoolTemplates(String schoolId) async {
    try {
      final result = await _apiClient.getSchoolTemplates(schoolId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(serverErrorMessage(e)));
    }
  }
}

class QuestionRepositoryImpl implements QuestionRepository {
  final ApiClient _apiClient;
  final AppDatabase _localDb;

  QuestionRepositoryImpl({
    required ApiClient apiClient,
    required AppDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  @override
  Future<Either<Failure, List<Question>>> searchQuestions(QuestionSearchParams params) async {
    try {
      final result = await _apiClient.searchQuestions(params);
      return right(result);
    } catch (e) {
      return left(ServerFailure(serverErrorMessage(e)));
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
      return left(ServerFailure(serverErrorMessage(e)));
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
      return left(ServerFailure(serverErrorMessage(e)));
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
      return left(ServerFailure(serverErrorMessage(e)));
    }
  }

  @override
  Future<Either<Failure, GeneratedPaper>> quickGeneratePaper(QuickPaperRequest request) async {
    try {
      final result = await _apiClient.quickGeneratePaper(request);
      return right(result);
    } catch (e) {
      return left(ServerFailure(serverErrorMessage(e)));
    }
  }

  @override
  Future<Either<Failure, GeneratedPaper>> generateFromIds(GenerateFromIdsRequest request) async {
    try {
      final result = await _apiClient.generateFromIds(request);
      return right(result);
    } catch (e) {
      return left(ServerFailure(serverErrorMessage(e)));
    }
  }

  @override
  Future<Either<Failure, List<SchoolTemplate>>> getSchoolTemplates(String schoolId) async {
    try {
      final result = await _apiClient.getSchoolPaperTemplates(schoolId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(serverErrorMessage(e)));
    }
  }

  @override
  Future<Either<Failure, String>> exportPaper(GeneratedPaper paper, ExportFormat format) async {
    try {
      final result = await _apiClient.exportPaper(paper.id, format);
      return right(result);
    } catch (e) {
      return left(ServerFailure(serverErrorMessage(e)));
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
  Future<Either<Failure, PracticeResult>> submitPractice(PracticeSubmission submission) async {
    try {
      final result = await _apiClient.submitPractice(submission);
      return right(result);
    } catch (e) {
      return left(EvaluationFailure(serverErrorMessage(e)));
    }
  }
}
