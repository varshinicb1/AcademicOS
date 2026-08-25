import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/assessment.dart';
import '../../domain/entities/question.dart';
import '../../domain/entities/enums.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';
import '../../domain/usecases/assessment_usecases.dart';

part 'assessment_bloc.freezed.dart';

@freezed
class AssessmentState with _$AssessmentState {
  const factory AssessmentState.initial() = _Initial;
  const factory AssessmentState.loading() = _Loading;
  const factory AssessmentState.questionsSelected(QuestionOptimizationResult result) = _QuestionsSelected;
  const factory AssessmentState.paperGenerated(GeneratedPaper paper) = _PaperGenerated;
  const factory AssessmentState.paperExported(String filePath) = _PaperExported;
  const factory AssessmentState.assessmentCreated(Assessment assessment) = _AssessmentCreated;
  const factory AssessmentState.assessmentsLoaded(List<Assessment> assessments) = _AssessmentsLoaded;
  const factory AssessmentState.error(String message) = _Error;
  const factory AssessmentState.success(String message) = _Success;
}

@freezed
class AssessmentEvent with _$AssessmentEvent {
  const factory AssessmentEvent.createAssessment(CreateAssessmentRequest request) = _CreateAssessment;
  const factory AssessmentEvent.selectQuestions({
    required Blueprint blueprint,
    required QuestionSearchParams params,
  }) = _SelectQuestions;
  const factory AssessmentEvent.generatePaper({
    required String assessmentId,
    required Blueprint blueprint,
    required List<Question> questions,
    required String schoolId,
  }) = _GeneratePaper;
  const factory AssessmentEvent.exportPaper({
    required GeneratedPaper paper,
    required String templateId,
    required ExportFormat format,
  }) = _ExportPaper;
  const factory AssessmentEvent.loadAssessments(String teacherId) = _LoadAssessments;
  const factory AssessmentEvent.loadAssessmentsBySchool(String schoolId) = _LoadAssessmentsBySchool;
  const factory AssessmentEvent.updateStatus({
    required String assessmentId,
    required AssessmentStatus status,
  }) = _UpdateStatus;
  const factory AssessmentEvent.clearError() = _ClearError;
}

class AssessmentBloc extends Bloc<AssessmentEvent, AssessmentState> {
  final CreateAssessmentUseCase _createAssessment;
  final SelectQuestionsUseCase _selectQuestions;
  final GeneratePaperUseCase _generatePaper;
  final AssessmentRepository _assessmentRepository;
  final PaperGenerationRepository _paperRepository;

  AssessmentBloc({
    required CreateAssessmentUseCase createAssessment,
    required SelectQuestionsUseCase selectQuestions,
    required GeneratePaperUseCase generatePaper,
    required AssessmentRepository assessmentRepository,
    required PaperGenerationRepository paperRepository,
  })  : _createAssessment = createAssessment,
        _selectQuestions = selectQuestions,
        _generatePaper = generatePaper,
        _assessmentRepository = assessmentRepository,
        _paperRepository = paperRepository,
        super(const AssessmentState.initial()) {
    on<_CreateAssessment>(_onCreateAssessment);
    on<_SelectQuestions>(_onSelectQuestions);
    on<_GeneratePaper>(_onGeneratePaper);
    on<_ExportPaper>(_onExportPaper);
    on<_LoadAssessments>(_onLoadAssessments);
    on<_LoadAssessmentsBySchool>(_onLoadAssessmentsBySchool);
    on<_UpdateStatus>(_onUpdateStatus);
    on<_ClearError>(_onClearError);
  }

  Future<void> _onCreateAssessment(_CreateAssessment event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.loading());
    final result = await _createAssessment(event.request);
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (assessment) => emit(AssessmentState.assessmentCreated(assessment)),
    );
  }

  Future<void> _onSelectQuestions(_SelectQuestions event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.loading());
    final result = await _selectQuestions(
      blueprint: event.blueprint,
      searchParams: event.params,
    );
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (result) => emit(AssessmentState.questionsSelected(result)),
    );
  }

  Future<void> _onGeneratePaper(_GeneratePaper event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.loading());
    final result = await _generatePaper(
      assessmentId: event.assessmentId,
      blueprint: event.blueprint,
      selectedQuestions: event.questions,
      schoolId: event.schoolId,
    );
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (paper) => emit(AssessmentState.paperGenerated(paper)),
    );
  }

  Future<void> _onExportPaper(_ExportPaper event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.loading());
    final result = await _paperRepository.exportPaper(event.paper, event.format);
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (filePath) => emit(AssessmentState.paperExported(filePath)),
    );
  }

  Future<void> _onLoadAssessments(_LoadAssessments event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.loading());
    final result = await _assessmentRepository.getAssessmentsByTeacher(event.teacherId);
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (assessments) => emit(AssessmentState.assessmentsLoaded(assessments)),
    );
  }

  Future<void> _onLoadAssessmentsBySchool(
      _LoadAssessmentsBySchool event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.loading());
    final result = await _assessmentRepository.getAssessmentsBySchool(event.schoolId);
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (assessments) => emit(AssessmentState.assessmentsLoaded(assessments)),
    );
  }

  Future<void> _onUpdateStatus(_UpdateStatus event, Emitter<AssessmentState> emit) async {
    final result = await _assessmentRepository.updateStatus(event.assessmentId, event.status);
    result.fold(
      (failure) => emit(AssessmentState.error(failure.message)),
      (_) => emit(const AssessmentState.success('Status updated')),
    );
  }

  Future<void> _onClearError(_ClearError event, Emitter<AssessmentState> emit) async {
    emit(const AssessmentState.initial());
  }
}
