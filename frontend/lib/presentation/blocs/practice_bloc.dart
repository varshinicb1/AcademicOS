import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/question.dart';
import '../../domain/entities/enums.dart';
import '../../domain/entities/mastery.dart';
import '../../domain/repositories/requests.dart';

part 'practice_bloc.freezed.dart';

@freezed
class PracticeState with _$PracticeState {
  const factory PracticeState.initial() = _Initial;
  const factory PracticeState.loading() = _Loading;
  const factory PracticeState.sessionLoaded(PracticeSession session) = _SessionLoaded;
  const factory PracticeState.questionLoaded(PracticeQuestion question, int index, int total) = _QuestionLoaded;
  const factory PracticeState.answerSubmitted(PracticeAnswerResult result) = _AnswerSubmitted;
  const factory PracticeState.sessionCompleted(PracticeResult result) = _SessionCompleted;
  const factory PracticeState.error(String message) = _Error;
}

@freezed
class PracticeEvent with _$PracticeEvent {
  const factory PracticeEvent.loadSession(String sessionId) = _LoadSession;
  const factory PracticeEvent.startSession(String sessionId) = _StartSession;
  const factory PracticeEvent.loadQuestion(int index) = _LoadQuestion;
  const factory PracticeEvent.submitAnswer(PracticeAnswer answer) = _SubmitAnswer;
  const factory PracticeEvent.nextQuestion() = _NextQuestion;
  const factory PracticeEvent.previousQuestion() = _PreviousQuestion;
  const factory PracticeEvent.useHint(String questionId) = _UseHint;
  const factory PracticeEvent.skipQuestion() = _SkipQuestion;
  const factory PracticeEvent.finishSession() = _FinishSession;
  const factory PracticeEvent.clearError() = _ClearError;
}

class PracticeBloc extends Bloc<PracticeEvent, PracticeState> {
  PracticeSession? _session;
  int _currentIndex = 0;

  PracticeBloc() : super(const PracticeState.initial()) {
    on<_LoadSession>(_onLoadSession);
    on<_StartSession>(_onStartSession);
    on<_LoadQuestion>(_onLoadQuestion);
    on<_SubmitAnswer>(_onSubmitAnswer);
    on<_NextQuestion>(_onNextQuestion);
    on<_PreviousQuestion>(_onPreviousQuestion);
    on<_UseHint>(_onUseHint);
    on<_SkipQuestion>(_onSkipQuestion);
    on<_FinishSession>(_onFinishSession);
    on<_ClearError>(_onClearError);
  }

  Future<void> _onLoadSession(_LoadSession event, Emitter<PracticeState> emit) async {
    emit(const PracticeState.loading());
    // TODO: Load session from repository
    emit(const PracticeState.error('Session loading not implemented'));
  }

  Future<void> _onStartSession(_StartSession event, Emitter<PracticeState> emit) async {
    // Transition session to in_progress
    if (_session != null && _session!.questions.isNotEmpty) {
      _currentIndex = 0;
      emit(PracticeState.questionLoaded(
        _session!.questions.first,
        0,
        _session!.questions.length,
      ));
    }
  }

  Future<void> _onLoadQuestion(_LoadQuestion event, Emitter<PracticeState> emit) async {
    if (_session != null && event.index >= 0 && event.index < _session!.questions.length) {
      _currentIndex = event.index;
      emit(PracticeState.questionLoaded(
        _session!.questions[event.index],
        event.index,
        _session!.questions.length,
      ));
    }
  }

  Future<void> _onSubmitAnswer(_SubmitAnswer event, Emitter<PracticeState> emit) async {
    // TODO: Submit answer and evaluate
  }

  Future<void> _onNextQuestion(_NextQuestion event, Emitter<PracticeState> emit) async {
    if (_session != null && _currentIndex < _session!.questions.length - 1) {
      _currentIndex++;
      emit(PracticeState.questionLoaded(
        _session!.questions[_currentIndex],
        _currentIndex,
        _session!.questions.length,
      ));
    } else {
      add(const PracticeEvent.finishSession());
    }
  }

  Future<void> _onPreviousQuestion(_PreviousQuestion event, Emitter<PracticeState> emit) async {
    if (_session != null && _currentIndex > 0) {
      _currentIndex--;
      emit(PracticeState.questionLoaded(
        _session!.questions[_currentIndex],
        _currentIndex,
        _session!.questions.length,
      ));
    }
  }

  Future<void> _onUseHint(_UseHint event, Emitter<PracticeState> emit) async {
    // Hint usage tracking
  }

  Future<void> _onSkipQuestion(_SkipQuestion event, Emitter<PracticeState> emit) async {
    add(const PracticeEvent.nextQuestion());
  }

  Future<void> _onFinishSession(_FinishSession event, Emitter<PracticeState> emit) async {
    emit(const PracticeState.loading());
    // TODO: Compute and publish practice result
  }

  Future<void> _onClearError(_ClearError event, Emitter<PracticeState> emit) async {
    emit(const PracticeState.initial());
  }
}
