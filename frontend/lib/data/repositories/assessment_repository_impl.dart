import 'package:dartz/dartz.dart';

import '../../domain/entities/entities.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';
import '../datasources/api/api_client.dart';

class AssessmentRepositoryImpl implements AssessmentRepository {
  final ApiClient _apiClient;

  AssessmentRepositoryImpl({required ApiClient apiClient}) : _apiClient = apiClient;

  @override
  Future<Either<Failure, Assessment>> createAssessment(Assessment assessment) async {
    try {
      final result = await _apiClient.createAssessment(CreateAssessmentRequest(
        teacherId: assessment.teacherId,
        schoolId: assessment.schoolId,
        title: assessment.title,
        subject: assessment.subject,
        grade: assessment.grade,
        chapterIds: assessment.chapterIds,
        blueprint: assessment.blueprint.toRequest(),
      ));
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Assessment>> getAssessment(String id) async {
    try {
      final result = await _apiClient.getAssessment(id);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<Assessment>>> getAssessmentsByTeacher(String teacherId) async {
    try {
      final result = await _apiClient.getAssessmentsByTeacher(teacherId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<Assessment>>> getAssessmentsBySchool(String schoolId) async {
    try {
      final result = await _apiClient.getAssessmentsBySchool(schoolId);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Assessment>> updateAssessment(Assessment assessment) async {
    try {
      final result = await _apiClient.updateAssessment(assessment.id, assessment);
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Unit>> deleteAssessment(String id) async {
    try {
      await _apiClient.deleteAssessment(id);
      return right(unit);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Assessment>> updateStatus(String id, AssessmentStatus status) async {
    try {
      final result = await _apiClient.updateStatus(id, {'status': status.name});
      return right(result);
    } catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}
