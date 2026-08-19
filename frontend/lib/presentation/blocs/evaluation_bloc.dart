import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:dartz/dartz.dart';

import '../../domain/entities/answer_sheet.dart';
import '../../domain/entities/enums.dart';
import '../../domain/entities/report.dart';
import '../../domain/failures/failures.dart';
import '../../domain/repositories/requests.dart';
import '../../domain/usecases/assessment_usecases.dart';

part 'evaluation_bloc.freezed.dart';

@freezed
class EvaluationState with _$EvaluationState {
  const factory EvaluationState.initial() = _Initial;
  const factory EvaluationState.loading() = _Loading;
  const factory EvaluationState.aiEvaluated(List<EvaluationResult> results) = _AIEvaluated;
  const factory EvaluationState.teacherReviewing(int currentIndex, List<EvaluationResult> results) = _TeacherReviewing;
  const factory EvaluationState.teacherReviewed(List<EvaluationResult> results) = _TeacherReviewed;
  const factory EvaluationState.finalized(List<StudentReport> reports) = _Finalized;
  const factory EvaluationState.error(String message) = _Error;
  const factory EvaluationState.partialError(int completed, int total, String message) = _PartialError;
}

@freezed
class EvaluationEvent with _$EvaluationEvent {
  const factory EvaluationEvent.startEvaluation(String answerSheetId) = _StartEvaluation;
  const factory EvaluationEvent.nextQuestion() = _NextQuestion;
  const factory EvaluationEvent.previousQuestion() = _PreviousQuestion;
  const factory EvaluationEvent.approveEvaluation(int index) = _ApproveEvaluation;
  const factory EvaluationEvent.adjustMarks(int index, int newMarks, String? comment) = _AdjustMarks;
  const factory EvaluationEvent.changeVerdict(int index, EvaluationVerdict verdict, String? comment) = _ChangeVerdict;
  const factory EvaluationEvent.skipQuestion(int index) = _SkipQuestion;
  const factory EvaluationEvent.finalizeEvaluation(List<String> studentIds) = _FinalizeEvaluation;
  const factory EvaluationEvent.clearError() = _ClearError;
}

class EvaluationBloc extends Bloc<EvaluationEvent, EvaluationState> {
  final EvaluateAnswerSheetUseCase _evaluateUseCase;
  final TeacherReviewUseCase _reviewUseCase;
  final FinalizeEvaluationUseCase _finalizeUseCase;

  List<EvaluationResult> _results = [];
  int _currentIndex = 0;

  EvaluationBloc({
    required EvaluateAnswerSheetUseCase evaluateUseCase,
    required TeacherReviewUseCase reviewUseCase,
    required FinalizeEvaluationUseCase finalizeUseCase,
  })  : _evaluateUseCase = evaluateUseCase,
        _reviewUseCase = reviewUseCase,
        _finalizeUseCase = finalizeUseCase,
        super(const EvaluationState.initial()) {
    on<_StartEvaluation>(_onStartEvaluation);
    on<_NextQuestion>(_onNextQuestion);
    on<_PreviousQuestion>(_onPreviousQuestion);
    on<_ApproveEvaluation>(_onApproveEvaluation);
    on<_AdjustMarks>(_onAdjustMarks);
    on<_ChangeVerdict>(_onChangeVerdict);
    on<_SkipQuestion>(_onSkipQuestion);
    on<_FinalizeEvaluation>(_onFinalizeEvaluation);
    on<_ClearError>(_onClearError);
  }

  Future<void> _onStartEvaluation(_StartEvaluation event, Emitter<EvaluationState> emit) async {
    emit(const EvaluationState.loading());
    final result = await _evaluateUseCase(event.answerSheetId);
    result.fold(
      (failure) => emit(EvaluationState.error(failure.message)),
      (results) {
        _results = results;
        _currentIndex = 0;
        emit(EvaluationState.aiEvaluated(results));
      },
    );
  }

  Future<void> _onNextQuestion(_NextQuestion event, Emitter<EvaluationState> emit) async {
    if (state is _TeacherReviewing) {
      if (_currentIndex < _results.length - 1) {
        _currentIndex++;
        emit(EvaluationState.teacherReviewing(_currentIndex, _results));
      }
    }
  }

  Future<void> _onPreviousQuestion(_PreviousQuestion event, Emitter<EvaluationState> emit) async {
    if (state is _TeacherReviewing) {
      if (_currentIndex > 0) {
        _currentIndex--;
        emit(EvaluationState.teacherReviewing(_currentIndex, _results));
      }
    }
  }

  Future<void> _onApproveEvaluation(_ApproveEvaluation event, Emitter<EvaluationState> emit) async {
    final request = TeacherReviewRequest(
      evaluationId: _results[event.index].id,
      teacherId: '',
      approved: true,
    );

    final result = await _reviewUseCase(request);
    result.fold(
      (failure) => emit(EvaluationState.error(failure.message)),
      (updated) {
        _results[event.index] = updated;
        if (event.index < _results.length - 1) {
          _currentIndex++;
          emit(EvaluationState.teacherReviewing(_currentIndex, _results));
        } else {
          emit(EvaluationState.teacherReviewed(_results));
        }
      },
    );
  }

  Future<void> _onAdjustMarks(_AdjustMarks event, Emitter<EvaluationState> emit) async {
    final request = TeacherReviewRequest(
      evaluationId: _results[event.index].id,
      teacherId: '',
      adjustedMarks: event.newMarks,
      comment: event.comment,
      approved: true,
    );

    final result = await _reviewUseCase(request);
    result.fold(
      (failure) => emit(EvaluationState.error(failure.message)),
      (updated) {
        _results[event.index] = updated;
        emit(EvaluationState.teacherReviewing(_currentIndex, _results));
      },
    );
  }

  Future<void> _onChangeVerdict(_ChangeVerdict event, Emitter<EvaluationState> emit) async {
    final request = TeacherReviewRequest(
      evaluationId: _results[event.index].id,
      teacherId: '',
      adjustedVerdict: event.verdict,
      comment: event.comment,
      approved: true,
    );

    final result = await _reviewUseCase(request);
    result.fold(
      (failure) => emit(EvaluationState.error(failure.message)),
      (updated) {
        _results[event.index] = updated;
        emit(EvaluationState.teacherReviewing(_currentIndex, _results));
      },
    );
  }

  Future<void> _onSkipQuestion(_SkipQuestion event, Emitter<EvaluationState> emit) async {
    if (event.index < _results.length - 1) {
      _currentIndex++;
      emit(EvaluationState.teacherReviewing(_currentIndex, _results));
    } else {
      emit(EvaluationState.teacherReviewed(_results));
    }
  }

  Future<void> _onFinalizeEvaluation(_FinalizeEvaluation event, Emitter<EvaluationState> emit) async {
    emit(const EvaluationState.loading());
    final result = await _finalizeUseCase(
      assessmentId: '',
      studentIds: event.studentIds,
      teacherId: '',
    );
    result.fold(
      (failure) => emit(EvaluationState.error(failure.message)),
      (reports) => emit(EvaluationState.finalized(reports)),
    );
  }

  Future<void> _onClearError(_ClearError event, Emitter<EvaluationState> emit) async {
    emit(const EvaluationState.initial());
  }
}
