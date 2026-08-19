import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/answer_sheet.dart';
import '../../domain/entities/enums.dart';
import '../../domain/repositories/requests.dart';
import '../../domain/usecases/assessment_usecases.dart';

part 'scanner_bloc.freezed.dart';

@freezed
class ScannerState with _$ScannerState {
  const factory ScannerState.initial() = _Initial;
  const factory ScannerState.cameraReady() = _CameraReady;
  const factory ScannerState.capturing() = _Capturing;
  const factory ScannerState.pagesCaptured(List<ScannedPage> pages) = _PagesCaptured;
  const factory ScannerState.processing(ProcessingStage stage, double progress) = _Processing;
  const factory ScannerState.processed(AnswerSheet answerSheet) = _Processed;
  const factory ScannerState.error(String message) = _Error;
  const factory ScannerState.retryableError(String message, int retryCount) = _RetryableError;
}

@freezed
class ScannerEvent with _$ScannerEvent {
  const factory ScannerEvent.initializeCamera() = _InitializeCamera;
  const factory ScannerEvent.capturePage() = _CapturePage;
  const factory ScannerEvent.retakePage(int pageIndex) = _RetakePage;
  const factory ScannerEvent.removePage(int pageIndex) = _RemovePage;
  const factory ScannerEvent.reorderPages(int oldIndex, int newIndex) = _ReorderPages;
  const factory ScannerEvent.startProcessing(ScanOptions options) = _StartProcessing;
  const factory ScannerEvent.cancelProcessing() = _CancelProcessing;
  const factory ScannerEvent.retry(int pageIndex) = _Retry;
  const factory ScannerEvent.clear() = _Clear;
}

enum ProcessingStage {
  uploading,
  perspectiveCorrection,
  shadowRemoval,
  noiseReduction,
  contrastEnhancement,
  segmentation,
  ocr,
  vision,
  completed,
}

extension ProcessingStageX on ProcessingStage {
  String get label => switch (this) {
    ProcessingStage.uploading => 'Uploading pages...',
    ProcessingStage.perspectiveCorrection => 'Correcting perspective...',
    ProcessingStage.shadowRemoval => 'Removing shadows...',
    ProcessingStage.noiseReduction => 'Reducing noise...',
    ProcessingStage.contrastEnhancement => 'Enhancing contrast...',
    ProcessingStage.segmentation => 'Segmenting questions...',
    ProcessingStage.ocr => 'Running OCR...',
    ProcessingStage.vision => 'Analyzing diagrams...',
    ProcessingStage.completed => 'Processing complete!',
  };

  double get progress => switch (this) {
    ProcessingStage.uploading => 0.1,
    ProcessingStage.perspectiveCorrection => 0.2,
    ProcessingStage.shadowRemoval => 0.3,
    ProcessingStage.noiseReduction => 0.4,
    ProcessingStage.contrastEnhancement => 0.5,
    ProcessingStage.segmentation => 0.6,
    ProcessingStage.ocr => 0.8,
    ProcessingStage.vision => 0.9,
    ProcessingStage.completed => 1.0,
  };
}

class ScannerBloc extends Bloc<ScannerEvent, ScannerState> {
  final ScanAnswerSheetUseCase _scanUseCase;

  ScannerBloc({required ScanAnswerSheetUseCase scanAnswerSheetUseCase})
      : _scanUseCase = scanAnswerSheetUseCase,
        super(const ScannerState.initial()) {
    on<_InitializeCamera>(_onInitializeCamera);
    on<_CapturePage>(_onCapturePage);
    on<_RetakePage>(_onRetakePage);
    on<_RemovePage>(_onRemovePage);
    on<_ReorderPages>(_onReorderPages);
    on<_StartProcessing>(_onStartProcessing);
    on<_CancelProcessing>(_onCancelProcessing);
    on<_Retry>(_onRetry);
    on<_Clear>(_onClear);
  }

  final List<ScannedPage> _pages = [];
  bool _isProcessing = false;

  Future<void> _onInitializeCamera(_InitializeCamera event, Emitter<ScannerState> emit) async {
    emit(const ScannerState.cameraReady());
  }

  Future<void> _onCapturePage(_CapturePage event, Emitter<ScannerState> emit) async {
    emit(const ScannerState.capturing());
  }

  void addPage(ScannedPage page) {
    _pages.add(page);
    emit(ScannerState.pagesCaptured(List.from(_pages)));
  }

  Future<void> _onRetakePage(_RetakePage event, Emitter<ScannerState> emit) async {
    if (event.pageIndex >= 0 && event.pageIndex < _pages.length) {
      emit(ScannerState.pagesCaptured(List.from(_pages)));
    }
  }

  Future<void> _onRemovePage(_RemovePage event, Emitter<ScannerState> emit) async {
    if (event.pageIndex >= 0 && event.pageIndex < _pages.length) {
      _pages.removeAt(event.pageIndex);
      emit(ScannerState.pagesCaptured(List.from(_pages)));
    }
  }

  Future<void> _onReorderPages(_ReorderPages event, Emitter<ScannerState> emit) async {
    final page = _pages.removeAt(event.oldIndex);
    _pages.insert(event.newIndex, page);
    emit(ScannerState.pagesCaptured(List.from(_pages)));
  }

  Future<void> _onStartProcessing(_StartProcessing event, Emitter<ScannerState> emit) async {
    if (_pages.isEmpty) {
      emit(const ScannerState.error('No pages captured'));
      return;
    }

    _isProcessing = true;
    const stages = ProcessingStage.values;

    for (int i = 0; i < stages.length; i++) {
      if (!_isProcessing) {
        break;
      }
      emit(ScannerState.processing(stages[i], stages[i].progress));
      await Future.delayed(const Duration(milliseconds: 500));
    }

    if (!_isProcessing) {
      return;
    }

    final upload = AnswerSheetUpload(
      assessmentId: '',
      studentId: '',
      studentName: '',
      rollNumber: '',
      imagePaths: _pages.map((p) => p.imagePath).toList(),
      scanMetadata: ScanMetadata(
        deviceId: '',
        appVersion: '',
        totalPages: _pages.length,
        avgQualityScore: _pages.fold(0.0, (sum, p) => sum + p.qualityScore) / _pages.length,
        scanDurationMs: 0,
        lighting: LightingCondition.good,
      ),
    );

    final result = await _scanUseCase(upload);
    result.fold(
      (failure) => emit(ScannerState.error(failure.message)),
      (answerSheet) => emit(ScannerState.processed(answerSheet)),
    );
  }

  Future<void> _onCancelProcessing(_CancelProcessing event, Emitter<ScannerState> emit) async {
    _isProcessing = false;
    emit(ScannerState.pagesCaptured(List.from(_pages)));
  }

  Future<void> _onRetry(_Retry event, Emitter<ScannerState> emit) async {
    // Retry specific page processing
  }

  Future<void> _onClear(_Clear event, Emitter<ScannerState> emit) async {
    _pages.clear();
    _isProcessing = false;
    emit(const ScannerState.initial());
  }
}
