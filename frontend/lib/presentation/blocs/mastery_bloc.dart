import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/mastery.dart';
import '../../domain/entities/enums.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/repositories/requests.dart';
import '../../domain/usecases/assessment_usecases.dart';

part 'mastery_bloc.freezed.dart';

@freezed
class MasteryState with _$MasteryState {
  const factory MasteryState.initial() = _Initial;
  const factory MasteryState.loading() = _Loading;
  const factory MasteryState.loaded(StudentMastery mastery) = _Loaded;
  const factory MasteryState.recommendationsLoaded(List<ActionableRecommendation> recommendations) = _RecommendationsLoaded;
  const factory MasteryState.practiceCreated(PracticeSession session) = _PracticeCreated;
  const factory MasteryState.practiceCompleted(PracticeResult result) = _PracticeCompleted;
  const factory MasteryState.error(String message) = _Error;
}

@freezed
class MasteryEvent with _$MasteryEvent {
  const factory MasteryEvent.loadMastery(String studentId) = _LoadMastery;
  const factory MasteryEvent.refreshMastery(String studentId) = _RefreshMastery;
  const factory MasteryEvent.loadRecommendations(String studentId) = _LoadRecommendations;
  const factory MasteryEvent.createPracticeSession({
    required String studentId,
    List<String>? conceptIds,
    PracticeType? type,
    int? questionCount,
    int? durationMinutes,
  }) = _CreatePracticeSession;
  const factory MasteryEvent.startPracticeSession(String sessionId) = _StartPracticeSession;
  const factory MasteryEvent.submitPractice(PracticeSubmission submission) = _SubmitPractice;
  const factory MasteryEvent.recordAttempt(MasteryAttempt attempt) = _RecordAttempt;
  const factory MasteryEvent.clearError() = _ClearError;
}

class MasteryBloc extends Bloc<MasteryEvent, MasteryState> {
  final GetStudentMasteryUseCase _getMastery;
  final GetRecommendationsUseCase _getRecommendations;
  final CreatePracticeSessionUseCase _createPractice;
  final SubmitPracticeUseCase _submitPractice;
  final MasteryRepository _masteryRepository;

  MasteryBloc({
    required GetStudentMasteryUseCase getMastery,
    required GetRecommendationsUseCase getRecommendations,
    required CreatePracticeSessionUseCase createPractice,
    required SubmitPracticeUseCase submitPractice,
    required MasteryRepository masteryRepository,
  })  : _getMastery = getMastery,
        _getRecommendations = getRecommendations,
        _createPractice = createPractice,
        _submitPractice = submitPractice,
        _masteryRepository = masteryRepository,
        super(const MasteryState.initial()) {
    on<_LoadMastery>(_onLoadMastery);
    on<_RefreshMastery>(_onRefreshMastery);
    on<_LoadRecommendations>(_onLoadRecommendations);
    on<_CreatePracticeSession>(_onCreatePracticeSession);
    on<_StartPracticeSession>(_onStartPracticeSession);
    on<_SubmitPractice>(_onSubmitPractice);
    on<_RecordAttempt>(_onRecordAttempt);
    on<_ClearError>(_onClearError);
  }

  Future<void> _onLoadMastery(_LoadMastery event, Emitter<MasteryState> emit) async {
    emit(const MasteryState.loading());
    final result = await _getMastery(event.studentId);
    result.fold(
      (failure) => emit(MasteryState.error(failure.message)),
      (mastery) => emit(MasteryState.loaded(mastery)),
    );
  }

  Future<void> _onRefreshMastery(_RefreshMastery event, Emitter<MasteryState> emit) async {
    if (state is! _Loaded) {
      emit(const MasteryState.loading());
    }
    final result = await _getMastery(event.studentId);
    result.fold(
      (failure) => emit(MasteryState.error(failure.message)),
      (mastery) => emit(MasteryState.loaded(mastery)),
    );
  }

  Future<void> _onLoadRecommendations(_LoadRecommendations event, Emitter<MasteryState> emit) async {
    final result = await _getRecommendations(event.studentId);
    result.fold(
      (failure) => emit(MasteryState.error(failure.message)),
      (recommendations) => emit(MasteryState.recommendationsLoaded(recommendations)),
    );
  }

  Future<void> _onCreatePracticeSession(_CreatePracticeSession event, Emitter<MasteryState> emit) async {
    emit(const MasteryState.loading());
    final result = await _createPractice(
      studentId: event.studentId,
      conceptIds: event.conceptIds,
      type: event.type,
      questionCount: event.questionCount,
      durationMinutes: event.durationMinutes,
    );
    result.fold(
      (failure) => emit(MasteryState.error(failure.message)),
      (session) => emit(MasteryState.practiceCreated(session)),
    );
  }

  Future<void> _onStartPracticeSession(_StartPracticeSession event, Emitter<MasteryState> emit) async {
    // Navigate to practice session screen
  }

  Future<void> _onSubmitPractice(_SubmitPractice event, Emitter<MasteryState> emit) async {
    emit(const MasteryState.loading());
    final result = await _submitPractice(event.submission);
    result.fold(
      (failure) => emit(MasteryState.error(failure.message)),
      (result) => emit(MasteryState.practiceCompleted(result)),
    );
  }

  Future<void> _onRecordAttempt(_RecordAttempt event, Emitter<MasteryState> emit) async {
    await _masteryRepository.recordAttempt(event.attempt);
  }

  Future<void> _onClearError(_ClearError event, Emitter<MasteryState> emit) async {
    emit(const MasteryState.initial());
  }
}
