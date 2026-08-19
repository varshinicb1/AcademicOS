import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:dartz/dartz.dart';

import '../../domain/entities/analytics.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/usecases/assessment_usecases.dart';

part 'analytics_bloc.freezed.dart';

@freezed
class AnalyticsState with _$AnalyticsState {
  const factory AnalyticsState.initial() = _Initial;
  const factory AnalyticsState.loading() = _Loading;
  const factory AnalyticsState.assessmentAnalyticsLoaded(AssessmentAnalytics analytics) = _AssessmentAnalyticsLoaded;
  const factory AnalyticsState.classAnalyticsLoaded(ClassAnalytics analytics) = _ClassAnalyticsLoaded;
  const factory AnalyticsState.studentAnalyticsLoaded(StudentAnalytics analytics) = _StudentAnalyticsLoaded;
  const factory AnalyticsState.schoolAnalyticsLoaded(SchoolAnalytics analytics) = _SchoolAnalyticsLoaded;
  const factory AnalyticsState.error(String message) = _Error;
}

@freezed
class AnalyticsEvent with _$AnalyticsEvent {
  const factory AnalyticsEvent.loadAssessmentAnalytics(String assessmentId) = _LoadAssessmentAnalytics;
  const factory AnalyticsEvent.loadClassAnalytics(String classId) = _LoadClassAnalytics;
  const factory AnalyticsEvent.loadStudentAnalytics(String studentId) = _LoadStudentAnalytics;
  const factory AnalyticsEvent.loadSchoolAnalytics(String schoolId) = _LoadSchoolAnalytics;
  const factory AnalyticsEvent.clearError() = _ClearError;
}

class AnalyticsBloc extends Bloc<AnalyticsEvent, AnalyticsState> {
  final GetAssessmentAnalyticsUseCase _getAssessmentAnalytics;
  final AnalyticsRepository _analyticsRepository;

  AnalyticsBloc({
    required GetAssessmentAnalyticsUseCase getAssessmentAnalytics,
    required AnalyticsRepository analyticsRepository,
  })  : _getAssessmentAnalytics = getAssessmentAnalytics,
        _analyticsRepository = analyticsRepository,
        super(const AnalyticsState.initial()) {
    on<_LoadAssessmentAnalytics>(_onLoadAssessmentAnalytics);
    on<_LoadClassAnalytics>(_onLoadClassAnalytics);
    on<_LoadStudentAnalytics>(_onLoadStudentAnalytics);
    on<_LoadSchoolAnalytics>(_onLoadSchoolAnalytics);
    on<_ClearError>(_onClearError);
  }

  Future<void> _onLoadAssessmentAnalytics(_LoadAssessmentAnalytics event, Emitter<AnalyticsState> emit) async {
    emit(const AnalyticsState.loading());
    final result = await _getAssessmentAnalytics(event.assessmentId);
    result.fold(
      (failure) => emit(AnalyticsState.error(failure.message)),
      (analytics) => emit(AnalyticsState.assessmentAnalyticsLoaded(analytics)),
    );
  }

  Future<void> _onLoadClassAnalytics(_LoadClassAnalytics event, Emitter<AnalyticsState> emit) async {
    emit(const AnalyticsState.loading());
    final result = await _analyticsRepository.getClassAnalytics(event.classId);
    result.fold(
      (failure) => emit(AnalyticsState.error(failure.message)),
      (analytics) => emit(AnalyticsState.classAnalyticsLoaded(analytics)),
    );
  }

  Future<void> _onLoadStudentAnalytics(_LoadStudentAnalytics event, Emitter<AnalyticsState> emit) async {
    emit(const AnalyticsState.loading());
    final result = await _analyticsRepository.getStudentAnalytics(event.studentId);
    result.fold(
      (failure) => emit(AnalyticsState.error(failure.message)),
      (analytics) => emit(AnalyticsState.studentAnalyticsLoaded(analytics)),
    );
  }

  Future<void> _onLoadSchoolAnalytics(_LoadSchoolAnalytics event, Emitter<AnalyticsState> emit) async {
    emit(const AnalyticsState.loading());
    final result = await _analyticsRepository.getSchoolAnalytics(event.schoolId);
    result.fold(
      (failure) => emit(AnalyticsState.error(failure.message)),
      (analytics) => emit(AnalyticsState.schoolAnalyticsLoaded(analytics)),
    );
  }

  Future<void> _onClearError(_ClearError event, Emitter<AnalyticsState> emit) async {
    emit(const AnalyticsState.initial());
  }
}
