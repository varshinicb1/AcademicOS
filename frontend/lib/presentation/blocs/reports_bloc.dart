import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:dartz/dartz.dart';

import '../../domain/entities/report.dart';
import '../../domain/entities/enums.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';
import '../../domain/usecases/assessment_usecases.dart';

part 'reports_bloc.freezed.dart';

@freezed
class ReportsState with _$ReportsState {
  const factory ReportsState.initial() = _Initial;
  const factory ReportsState.loading() = _Loading;
  const factory ReportsState.reportGenerated(StudentReport report) = _ReportGenerated;
  const factory ReportsState.bulkReportsGenerated(List<StudentReport> reports) = _BulkReportsGenerated;
  const factory ReportsState.reportExported(String filePath) = _ReportExported;
  const factory ReportsState.bulkReportsExported(List<String> filePaths) = _BulkReportsExported;
  const factory ReportsState.parentReportGenerated(ParentReport report) = _ParentReportGenerated;
  const factory ReportsState.error(String message) = _Error;
}

@freezed
class ReportsEvent with _$ReportsEvent {
  const factory ReportsEvent.generateStudentReport({
    required String assessmentId,
    required String studentId,
  }) = _GenerateStudentReport;
  const factory ReportsEvent.generateBulkReports({
    required String assessmentId,
    required List<String> studentIds,
    @Default(ReportType.studentDetailed) ReportType type,
  }) = _GenerateBulkReports;
  const factory ReportsEvent.exportReport({
    required StudentReport report,
    required ExportFormat format,
  }) = _ExportReport;
  const factory ReportsEvent.exportBulkReports({
    required List<StudentReport> reports,
    required ExportFormat format,
  }) = _ExportBulkReports;
  const factory ReportsEvent.generateParentReport({
    required String assessmentId,
    required String studentId,
  }) = _GenerateParentReport;
  const factory ReportsEvent.clearError() = _ClearError;
}

class ReportsBloc extends Bloc<ReportsEvent, ReportsState> {
  final GenerateStudentReportUseCase _generateStudentReport;
  final ReportRepository _reportRepository;

  ReportsBloc({
    required GenerateStudentReportUseCase generateStudentReport,
    required ReportRepository reportRepository,
  })  : _generateStudentReport = generateStudentReport,
        _reportRepository = reportRepository,
        super(const ReportsState.initial()) {
    on<_GenerateStudentReport>(_onGenerateStudentReport);
    on<_GenerateBulkReports>(_onGenerateBulkReports);
    on<_ExportReport>(_onExportReport);
    on<_ExportBulkReports>(_onExportBulkReports);
    on<_GenerateParentReport>(_onGenerateParentReport);
    on<_ClearError>(_onClearError);
  }

  Future<void> _onGenerateStudentReport(_GenerateStudentReport event, Emitter<ReportsState> emit) async {
    emit(const ReportsState.loading());
    final result = await _generateStudentReport(
      assessmentId: event.assessmentId,
      studentId: event.studentId,
    );
    result.fold(
      (failure) => emit(ReportsState.error(failure.message)),
      (report) => emit(ReportsState.reportGenerated(report)),
    );
  }

  Future<void> _onGenerateBulkReports(_GenerateBulkReports event, Emitter<ReportsState> emit) async {
    emit(const ReportsState.loading());
    final request = BulkReportRequest(
      assessmentId: event.assessmentId,
      studentIds: event.studentIds,
      type: event.type,
    );

    final result = await _reportRepository.generateBulkReports(request);
    result.fold(
      (failure) => emit(ReportsState.error(failure.message)),
      (reports) => emit(ReportsState.bulkReportsGenerated(reports)),
    );
  }

  Future<void> _onExportReport(_ExportReport event, Emitter<ReportsState> emit) async {
    emit(const ReportsState.loading());
    final result = await _reportRepository.exportReport(event.report.id, event.format);
    final filePath = result.fold((l) => '', (r) => r);
    if (filePath.isNotEmpty) {
      emit(ReportsState.reportExported(filePath));
    } else {
      emit(const ReportsState.error('Export failed'));
    }
  }

  Future<void> _onExportBulkReports(_ExportBulkReports event, Emitter<ReportsState> emit) async {
    emit(const ReportsState.loading());
    final filePaths = <String>[];
    for (final report in event.reports) {
      final result = await _reportRepository.exportReport(report.id, event.format);
      final filePath = result.fold((l) => '', (r) => r);
      if (filePath.isNotEmpty) {
        filePaths.add(filePath);
      }
    }
    if (filePaths.isNotEmpty) {
      emit(ReportsState.bulkReportsExported(filePaths));
    } else {
      emit(const ReportsState.error('Bulk export failed'));
    }
  }

  Future<void> _onGenerateParentReport(_GenerateParentReport event, Emitter<ReportsState> emit) async {
    emit(const ReportsState.loading());
    final result = await _reportRepository.generateParentReport(ReportRequest(
      assessmentId: event.assessmentId,
      studentId: event.studentId,
      type: ReportType.parentSummary,
    ));
    result.fold(
      (failure) => emit(ReportsState.error(failure.message)),
      (report) => emit(ReportsState.parentReportGenerated(report)),
    );
  }

  Future<void> _onClearError(_ClearError event, Emitter<ReportsState> emit) async {
    emit(const ReportsState.initial());
  }
}