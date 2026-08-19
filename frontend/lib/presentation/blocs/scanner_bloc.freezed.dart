// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'scanner_bloc.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$ScannerState {
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ScannerStateCopyWith<$Res> {
  factory $ScannerStateCopyWith(
          ScannerState value, $Res Function(ScannerState) then) =
      _$ScannerStateCopyWithImpl<$Res, ScannerState>;
}

/// @nodoc
class _$ScannerStateCopyWithImpl<$Res, $Val extends ScannerState>
    implements $ScannerStateCopyWith<$Res> {
  _$ScannerStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;
}

/// @nodoc
abstract class _$$InitialImplCopyWith<$Res> {
  factory _$$InitialImplCopyWith(
          _$InitialImpl value, $Res Function(_$InitialImpl) then) =
      __$$InitialImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$InitialImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$InitialImpl>
    implements _$$InitialImplCopyWith<$Res> {
  __$$InitialImplCopyWithImpl(
      _$InitialImpl _value, $Res Function(_$InitialImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$InitialImpl implements _Initial {
  const _$InitialImpl();

  @override
  String toString() {
    return 'ScannerState.initial()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$InitialImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return initial();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return initial?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (initial != null) {
      return initial();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return initial(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return initial?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (initial != null) {
      return initial(this);
    }
    return orElse();
  }
}

abstract class _Initial implements ScannerState {
  const factory _Initial() = _$InitialImpl;
}

/// @nodoc
abstract class _$$CameraReadyImplCopyWith<$Res> {
  factory _$$CameraReadyImplCopyWith(
          _$CameraReadyImpl value, $Res Function(_$CameraReadyImpl) then) =
      __$$CameraReadyImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$CameraReadyImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$CameraReadyImpl>
    implements _$$CameraReadyImplCopyWith<$Res> {
  __$$CameraReadyImplCopyWithImpl(
      _$CameraReadyImpl _value, $Res Function(_$CameraReadyImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$CameraReadyImpl implements _CameraReady {
  const _$CameraReadyImpl();

  @override
  String toString() {
    return 'ScannerState.cameraReady()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$CameraReadyImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return cameraReady();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return cameraReady?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (cameraReady != null) {
      return cameraReady();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return cameraReady(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return cameraReady?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (cameraReady != null) {
      return cameraReady(this);
    }
    return orElse();
  }
}

abstract class _CameraReady implements ScannerState {
  const factory _CameraReady() = _$CameraReadyImpl;
}

/// @nodoc
abstract class _$$CapturingImplCopyWith<$Res> {
  factory _$$CapturingImplCopyWith(
          _$CapturingImpl value, $Res Function(_$CapturingImpl) then) =
      __$$CapturingImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$CapturingImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$CapturingImpl>
    implements _$$CapturingImplCopyWith<$Res> {
  __$$CapturingImplCopyWithImpl(
      _$CapturingImpl _value, $Res Function(_$CapturingImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$CapturingImpl implements _Capturing {
  const _$CapturingImpl();

  @override
  String toString() {
    return 'ScannerState.capturing()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$CapturingImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return capturing();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return capturing?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (capturing != null) {
      return capturing();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return capturing(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return capturing?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (capturing != null) {
      return capturing(this);
    }
    return orElse();
  }
}

abstract class _Capturing implements ScannerState {
  const factory _Capturing() = _$CapturingImpl;
}

/// @nodoc
abstract class _$$PagesCapturedImplCopyWith<$Res> {
  factory _$$PagesCapturedImplCopyWith(
          _$PagesCapturedImpl value, $Res Function(_$PagesCapturedImpl) then) =
      __$$PagesCapturedImplCopyWithImpl<$Res>;
  @useResult
  $Res call({List<ScannedPage> pages});
}

/// @nodoc
class __$$PagesCapturedImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$PagesCapturedImpl>
    implements _$$PagesCapturedImplCopyWith<$Res> {
  __$$PagesCapturedImplCopyWithImpl(
      _$PagesCapturedImpl _value, $Res Function(_$PagesCapturedImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pages = null,
  }) {
    return _then(_$PagesCapturedImpl(
      null == pages
          ? _value._pages
          : pages // ignore: cast_nullable_to_non_nullable
              as List<ScannedPage>,
    ));
  }
}

/// @nodoc

class _$PagesCapturedImpl implements _PagesCaptured {
  const _$PagesCapturedImpl(final List<ScannedPage> pages) : _pages = pages;

  final List<ScannedPage> _pages;
  @override
  List<ScannedPage> get pages {
    if (_pages is EqualUnmodifiableListView) return _pages;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_pages);
  }

  @override
  String toString() {
    return 'ScannerState.pagesCaptured(pages: $pages)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PagesCapturedImpl &&
            const DeepCollectionEquality().equals(other._pages, _pages));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_pages));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PagesCapturedImplCopyWith<_$PagesCapturedImpl> get copyWith =>
      __$$PagesCapturedImplCopyWithImpl<_$PagesCapturedImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return pagesCaptured(pages);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return pagesCaptured?.call(pages);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (pagesCaptured != null) {
      return pagesCaptured(pages);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return pagesCaptured(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return pagesCaptured?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (pagesCaptured != null) {
      return pagesCaptured(this);
    }
    return orElse();
  }
}

abstract class _PagesCaptured implements ScannerState {
  const factory _PagesCaptured(final List<ScannedPage> pages) =
      _$PagesCapturedImpl;

  List<ScannedPage> get pages;
  @JsonKey(ignore: true)
  _$$PagesCapturedImplCopyWith<_$PagesCapturedImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ProcessingImplCopyWith<$Res> {
  factory _$$ProcessingImplCopyWith(
          _$ProcessingImpl value, $Res Function(_$ProcessingImpl) then) =
      __$$ProcessingImplCopyWithImpl<$Res>;
  @useResult
  $Res call({ProcessingStage stage, double progress});
}

/// @nodoc
class __$$ProcessingImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$ProcessingImpl>
    implements _$$ProcessingImplCopyWith<$Res> {
  __$$ProcessingImplCopyWithImpl(
      _$ProcessingImpl _value, $Res Function(_$ProcessingImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? stage = null,
    Object? progress = null,
  }) {
    return _then(_$ProcessingImpl(
      null == stage
          ? _value.stage
          : stage // ignore: cast_nullable_to_non_nullable
              as ProcessingStage,
      null == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc

class _$ProcessingImpl implements _Processing {
  const _$ProcessingImpl(this.stage, this.progress);

  @override
  final ProcessingStage stage;
  @override
  final double progress;

  @override
  String toString() {
    return 'ScannerState.processing(stage: $stage, progress: $progress)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProcessingImpl &&
            (identical(other.stage, stage) || other.stage == stage) &&
            (identical(other.progress, progress) ||
                other.progress == progress));
  }

  @override
  int get hashCode => Object.hash(runtimeType, stage, progress);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ProcessingImplCopyWith<_$ProcessingImpl> get copyWith =>
      __$$ProcessingImplCopyWithImpl<_$ProcessingImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return processing(stage, progress);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return processing?.call(stage, progress);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (processing != null) {
      return processing(stage, progress);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return processing(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return processing?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (processing != null) {
      return processing(this);
    }
    return orElse();
  }
}

abstract class _Processing implements ScannerState {
  const factory _Processing(
      final ProcessingStage stage, final double progress) = _$ProcessingImpl;

  ProcessingStage get stage;
  double get progress;
  @JsonKey(ignore: true)
  _$$ProcessingImplCopyWith<_$ProcessingImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ProcessedImplCopyWith<$Res> {
  factory _$$ProcessedImplCopyWith(
          _$ProcessedImpl value, $Res Function(_$ProcessedImpl) then) =
      __$$ProcessedImplCopyWithImpl<$Res>;
  @useResult
  $Res call({AnswerSheet answerSheet});

  $AnswerSheetCopyWith<$Res> get answerSheet;
}

/// @nodoc
class __$$ProcessedImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$ProcessedImpl>
    implements _$$ProcessedImplCopyWith<$Res> {
  __$$ProcessedImplCopyWithImpl(
      _$ProcessedImpl _value, $Res Function(_$ProcessedImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? answerSheet = null,
  }) {
    return _then(_$ProcessedImpl(
      null == answerSheet
          ? _value.answerSheet
          : answerSheet // ignore: cast_nullable_to_non_nullable
              as AnswerSheet,
    ));
  }

  @override
  @pragma('vm:prefer-inline')
  $AnswerSheetCopyWith<$Res> get answerSheet {
    return $AnswerSheetCopyWith<$Res>(_value.answerSheet, (value) {
      return _then(_value.copyWith(answerSheet: value));
    });
  }
}

/// @nodoc

class _$ProcessedImpl implements _Processed {
  const _$ProcessedImpl(this.answerSheet);

  @override
  final AnswerSheet answerSheet;

  @override
  String toString() {
    return 'ScannerState.processed(answerSheet: $answerSheet)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProcessedImpl &&
            (identical(other.answerSheet, answerSheet) ||
                other.answerSheet == answerSheet));
  }

  @override
  int get hashCode => Object.hash(runtimeType, answerSheet);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ProcessedImplCopyWith<_$ProcessedImpl> get copyWith =>
      __$$ProcessedImplCopyWithImpl<_$ProcessedImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return processed(answerSheet);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return processed?.call(answerSheet);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (processed != null) {
      return processed(answerSheet);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return processed(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return processed?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (processed != null) {
      return processed(this);
    }
    return orElse();
  }
}

abstract class _Processed implements ScannerState {
  const factory _Processed(final AnswerSheet answerSheet) = _$ProcessedImpl;

  AnswerSheet get answerSheet;
  @JsonKey(ignore: true)
  _$$ProcessedImplCopyWith<_$ProcessedImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ErrorImplCopyWith<$Res> {
  factory _$$ErrorImplCopyWith(
          _$ErrorImpl value, $Res Function(_$ErrorImpl) then) =
      __$$ErrorImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String message});
}

/// @nodoc
class __$$ErrorImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$ErrorImpl>
    implements _$$ErrorImplCopyWith<$Res> {
  __$$ErrorImplCopyWithImpl(
      _$ErrorImpl _value, $Res Function(_$ErrorImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? message = null,
  }) {
    return _then(_$ErrorImpl(
      null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc

class _$ErrorImpl implements _Error {
  const _$ErrorImpl(this.message);

  @override
  final String message;

  @override
  String toString() {
    return 'ScannerState.error(message: $message)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ErrorImpl &&
            (identical(other.message, message) || other.message == message));
  }

  @override
  int get hashCode => Object.hash(runtimeType, message);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ErrorImplCopyWith<_$ErrorImpl> get copyWith =>
      __$$ErrorImplCopyWithImpl<_$ErrorImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return error(message);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return error?.call(message);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (error != null) {
      return error(message);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return error(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return error?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (error != null) {
      return error(this);
    }
    return orElse();
  }
}

abstract class _Error implements ScannerState {
  const factory _Error(final String message) = _$ErrorImpl;

  String get message;
  @JsonKey(ignore: true)
  _$$ErrorImplCopyWith<_$ErrorImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$RetryableErrorImplCopyWith<$Res> {
  factory _$$RetryableErrorImplCopyWith(_$RetryableErrorImpl value,
          $Res Function(_$RetryableErrorImpl) then) =
      __$$RetryableErrorImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String message, int retryCount});
}

/// @nodoc
class __$$RetryableErrorImplCopyWithImpl<$Res>
    extends _$ScannerStateCopyWithImpl<$Res, _$RetryableErrorImpl>
    implements _$$RetryableErrorImplCopyWith<$Res> {
  __$$RetryableErrorImplCopyWithImpl(
      _$RetryableErrorImpl _value, $Res Function(_$RetryableErrorImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? message = null,
    Object? retryCount = null,
  }) {
    return _then(_$RetryableErrorImpl(
      null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
      null == retryCount
          ? _value.retryCount
          : retryCount // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$RetryableErrorImpl implements _RetryableError {
  const _$RetryableErrorImpl(this.message, this.retryCount);

  @override
  final String message;
  @override
  final int retryCount;

  @override
  String toString() {
    return 'ScannerState.retryableError(message: $message, retryCount: $retryCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RetryableErrorImpl &&
            (identical(other.message, message) || other.message == message) &&
            (identical(other.retryCount, retryCount) ||
                other.retryCount == retryCount));
  }

  @override
  int get hashCode => Object.hash(runtimeType, message, retryCount);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RetryableErrorImplCopyWith<_$RetryableErrorImpl> get copyWith =>
      __$$RetryableErrorImplCopyWithImpl<_$RetryableErrorImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() cameraReady,
    required TResult Function() capturing,
    required TResult Function(List<ScannedPage> pages) pagesCaptured,
    required TResult Function(ProcessingStage stage, double progress)
        processing,
    required TResult Function(AnswerSheet answerSheet) processed,
    required TResult Function(String message) error,
    required TResult Function(String message, int retryCount) retryableError,
  }) {
    return retryableError(message, retryCount);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? cameraReady,
    TResult? Function()? capturing,
    TResult? Function(List<ScannedPage> pages)? pagesCaptured,
    TResult? Function(ProcessingStage stage, double progress)? processing,
    TResult? Function(AnswerSheet answerSheet)? processed,
    TResult? Function(String message)? error,
    TResult? Function(String message, int retryCount)? retryableError,
  }) {
    return retryableError?.call(message, retryCount);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? cameraReady,
    TResult Function()? capturing,
    TResult Function(List<ScannedPage> pages)? pagesCaptured,
    TResult Function(ProcessingStage stage, double progress)? processing,
    TResult Function(AnswerSheet answerSheet)? processed,
    TResult Function(String message)? error,
    TResult Function(String message, int retryCount)? retryableError,
    required TResult orElse(),
  }) {
    if (retryableError != null) {
      return retryableError(message, retryCount);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_CameraReady value) cameraReady,
    required TResult Function(_Capturing value) capturing,
    required TResult Function(_PagesCaptured value) pagesCaptured,
    required TResult Function(_Processing value) processing,
    required TResult Function(_Processed value) processed,
    required TResult Function(_Error value) error,
    required TResult Function(_RetryableError value) retryableError,
  }) {
    return retryableError(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_CameraReady value)? cameraReady,
    TResult? Function(_Capturing value)? capturing,
    TResult? Function(_PagesCaptured value)? pagesCaptured,
    TResult? Function(_Processing value)? processing,
    TResult? Function(_Processed value)? processed,
    TResult? Function(_Error value)? error,
    TResult? Function(_RetryableError value)? retryableError,
  }) {
    return retryableError?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_CameraReady value)? cameraReady,
    TResult Function(_Capturing value)? capturing,
    TResult Function(_PagesCaptured value)? pagesCaptured,
    TResult Function(_Processing value)? processing,
    TResult Function(_Processed value)? processed,
    TResult Function(_Error value)? error,
    TResult Function(_RetryableError value)? retryableError,
    required TResult orElse(),
  }) {
    if (retryableError != null) {
      return retryableError(this);
    }
    return orElse();
  }
}

abstract class _RetryableError implements ScannerState {
  const factory _RetryableError(final String message, final int retryCount) =
      _$RetryableErrorImpl;

  String get message;
  int get retryCount;
  @JsonKey(ignore: true)
  _$$RetryableErrorImplCopyWith<_$RetryableErrorImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ScannerEvent {
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ScannerEventCopyWith<$Res> {
  factory $ScannerEventCopyWith(
          ScannerEvent value, $Res Function(ScannerEvent) then) =
      _$ScannerEventCopyWithImpl<$Res, ScannerEvent>;
}

/// @nodoc
class _$ScannerEventCopyWithImpl<$Res, $Val extends ScannerEvent>
    implements $ScannerEventCopyWith<$Res> {
  _$ScannerEventCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;
}

/// @nodoc
abstract class _$$InitializeCameraImplCopyWith<$Res> {
  factory _$$InitializeCameraImplCopyWith(_$InitializeCameraImpl value,
          $Res Function(_$InitializeCameraImpl) then) =
      __$$InitializeCameraImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$InitializeCameraImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$InitializeCameraImpl>
    implements _$$InitializeCameraImplCopyWith<$Res> {
  __$$InitializeCameraImplCopyWithImpl(_$InitializeCameraImpl _value,
      $Res Function(_$InitializeCameraImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$InitializeCameraImpl implements _InitializeCamera {
  const _$InitializeCameraImpl();

  @override
  String toString() {
    return 'ScannerEvent.initializeCamera()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$InitializeCameraImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return initializeCamera();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return initializeCamera?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (initializeCamera != null) {
      return initializeCamera();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return initializeCamera(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return initializeCamera?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (initializeCamera != null) {
      return initializeCamera(this);
    }
    return orElse();
  }
}

abstract class _InitializeCamera implements ScannerEvent {
  const factory _InitializeCamera() = _$InitializeCameraImpl;
}

/// @nodoc
abstract class _$$CapturePageImplCopyWith<$Res> {
  factory _$$CapturePageImplCopyWith(
          _$CapturePageImpl value, $Res Function(_$CapturePageImpl) then) =
      __$$CapturePageImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$CapturePageImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$CapturePageImpl>
    implements _$$CapturePageImplCopyWith<$Res> {
  __$$CapturePageImplCopyWithImpl(
      _$CapturePageImpl _value, $Res Function(_$CapturePageImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$CapturePageImpl implements _CapturePage {
  const _$CapturePageImpl();

  @override
  String toString() {
    return 'ScannerEvent.capturePage()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$CapturePageImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return capturePage();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return capturePage?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (capturePage != null) {
      return capturePage();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return capturePage(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return capturePage?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (capturePage != null) {
      return capturePage(this);
    }
    return orElse();
  }
}

abstract class _CapturePage implements ScannerEvent {
  const factory _CapturePage() = _$CapturePageImpl;
}

/// @nodoc
abstract class _$$RetakePageImplCopyWith<$Res> {
  factory _$$RetakePageImplCopyWith(
          _$RetakePageImpl value, $Res Function(_$RetakePageImpl) then) =
      __$$RetakePageImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int pageIndex});
}

/// @nodoc
class __$$RetakePageImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$RetakePageImpl>
    implements _$$RetakePageImplCopyWith<$Res> {
  __$$RetakePageImplCopyWithImpl(
      _$RetakePageImpl _value, $Res Function(_$RetakePageImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pageIndex = null,
  }) {
    return _then(_$RetakePageImpl(
      null == pageIndex
          ? _value.pageIndex
          : pageIndex // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$RetakePageImpl implements _RetakePage {
  const _$RetakePageImpl(this.pageIndex);

  @override
  final int pageIndex;

  @override
  String toString() {
    return 'ScannerEvent.retakePage(pageIndex: $pageIndex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RetakePageImpl &&
            (identical(other.pageIndex, pageIndex) ||
                other.pageIndex == pageIndex));
  }

  @override
  int get hashCode => Object.hash(runtimeType, pageIndex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RetakePageImplCopyWith<_$RetakePageImpl> get copyWith =>
      __$$RetakePageImplCopyWithImpl<_$RetakePageImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return retakePage(pageIndex);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return retakePage?.call(pageIndex);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (retakePage != null) {
      return retakePage(pageIndex);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return retakePage(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return retakePage?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (retakePage != null) {
      return retakePage(this);
    }
    return orElse();
  }
}

abstract class _RetakePage implements ScannerEvent {
  const factory _RetakePage(final int pageIndex) = _$RetakePageImpl;

  int get pageIndex;
  @JsonKey(ignore: true)
  _$$RetakePageImplCopyWith<_$RetakePageImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$RemovePageImplCopyWith<$Res> {
  factory _$$RemovePageImplCopyWith(
          _$RemovePageImpl value, $Res Function(_$RemovePageImpl) then) =
      __$$RemovePageImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int pageIndex});
}

/// @nodoc
class __$$RemovePageImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$RemovePageImpl>
    implements _$$RemovePageImplCopyWith<$Res> {
  __$$RemovePageImplCopyWithImpl(
      _$RemovePageImpl _value, $Res Function(_$RemovePageImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pageIndex = null,
  }) {
    return _then(_$RemovePageImpl(
      null == pageIndex
          ? _value.pageIndex
          : pageIndex // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$RemovePageImpl implements _RemovePage {
  const _$RemovePageImpl(this.pageIndex);

  @override
  final int pageIndex;

  @override
  String toString() {
    return 'ScannerEvent.removePage(pageIndex: $pageIndex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RemovePageImpl &&
            (identical(other.pageIndex, pageIndex) ||
                other.pageIndex == pageIndex));
  }

  @override
  int get hashCode => Object.hash(runtimeType, pageIndex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RemovePageImplCopyWith<_$RemovePageImpl> get copyWith =>
      __$$RemovePageImplCopyWithImpl<_$RemovePageImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return removePage(pageIndex);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return removePage?.call(pageIndex);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (removePage != null) {
      return removePage(pageIndex);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return removePage(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return removePage?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (removePage != null) {
      return removePage(this);
    }
    return orElse();
  }
}

abstract class _RemovePage implements ScannerEvent {
  const factory _RemovePage(final int pageIndex) = _$RemovePageImpl;

  int get pageIndex;
  @JsonKey(ignore: true)
  _$$RemovePageImplCopyWith<_$RemovePageImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ReorderPagesImplCopyWith<$Res> {
  factory _$$ReorderPagesImplCopyWith(
          _$ReorderPagesImpl value, $Res Function(_$ReorderPagesImpl) then) =
      __$$ReorderPagesImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int oldIndex, int newIndex});
}

/// @nodoc
class __$$ReorderPagesImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$ReorderPagesImpl>
    implements _$$ReorderPagesImplCopyWith<$Res> {
  __$$ReorderPagesImplCopyWithImpl(
      _$ReorderPagesImpl _value, $Res Function(_$ReorderPagesImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? oldIndex = null,
    Object? newIndex = null,
  }) {
    return _then(_$ReorderPagesImpl(
      null == oldIndex
          ? _value.oldIndex
          : oldIndex // ignore: cast_nullable_to_non_nullable
              as int,
      null == newIndex
          ? _value.newIndex
          : newIndex // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$ReorderPagesImpl implements _ReorderPages {
  const _$ReorderPagesImpl(this.oldIndex, this.newIndex);

  @override
  final int oldIndex;
  @override
  final int newIndex;

  @override
  String toString() {
    return 'ScannerEvent.reorderPages(oldIndex: $oldIndex, newIndex: $newIndex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ReorderPagesImpl &&
            (identical(other.oldIndex, oldIndex) ||
                other.oldIndex == oldIndex) &&
            (identical(other.newIndex, newIndex) ||
                other.newIndex == newIndex));
  }

  @override
  int get hashCode => Object.hash(runtimeType, oldIndex, newIndex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ReorderPagesImplCopyWith<_$ReorderPagesImpl> get copyWith =>
      __$$ReorderPagesImplCopyWithImpl<_$ReorderPagesImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return reorderPages(oldIndex, newIndex);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return reorderPages?.call(oldIndex, newIndex);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (reorderPages != null) {
      return reorderPages(oldIndex, newIndex);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return reorderPages(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return reorderPages?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (reorderPages != null) {
      return reorderPages(this);
    }
    return orElse();
  }
}

abstract class _ReorderPages implements ScannerEvent {
  const factory _ReorderPages(final int oldIndex, final int newIndex) =
      _$ReorderPagesImpl;

  int get oldIndex;
  int get newIndex;
  @JsonKey(ignore: true)
  _$$ReorderPagesImplCopyWith<_$ReorderPagesImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$StartProcessingImplCopyWith<$Res> {
  factory _$$StartProcessingImplCopyWith(_$StartProcessingImpl value,
          $Res Function(_$StartProcessingImpl) then) =
      __$$StartProcessingImplCopyWithImpl<$Res>;
  @useResult
  $Res call({ScanOptions options});

  $ScanOptionsCopyWith<$Res> get options;
}

/// @nodoc
class __$$StartProcessingImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$StartProcessingImpl>
    implements _$$StartProcessingImplCopyWith<$Res> {
  __$$StartProcessingImplCopyWithImpl(
      _$StartProcessingImpl _value, $Res Function(_$StartProcessingImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? options = null,
  }) {
    return _then(_$StartProcessingImpl(
      null == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as ScanOptions,
    ));
  }

  @override
  @pragma('vm:prefer-inline')
  $ScanOptionsCopyWith<$Res> get options {
    return $ScanOptionsCopyWith<$Res>(_value.options, (value) {
      return _then(_value.copyWith(options: value));
    });
  }
}

/// @nodoc

class _$StartProcessingImpl implements _StartProcessing {
  const _$StartProcessingImpl(this.options);

  @override
  final ScanOptions options;

  @override
  String toString() {
    return 'ScannerEvent.startProcessing(options: $options)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StartProcessingImpl &&
            (identical(other.options, options) || other.options == options));
  }

  @override
  int get hashCode => Object.hash(runtimeType, options);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$StartProcessingImplCopyWith<_$StartProcessingImpl> get copyWith =>
      __$$StartProcessingImplCopyWithImpl<_$StartProcessingImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return startProcessing(options);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return startProcessing?.call(options);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (startProcessing != null) {
      return startProcessing(options);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return startProcessing(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return startProcessing?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (startProcessing != null) {
      return startProcessing(this);
    }
    return orElse();
  }
}

abstract class _StartProcessing implements ScannerEvent {
  const factory _StartProcessing(final ScanOptions options) =
      _$StartProcessingImpl;

  ScanOptions get options;
  @JsonKey(ignore: true)
  _$$StartProcessingImplCopyWith<_$StartProcessingImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$CancelProcessingImplCopyWith<$Res> {
  factory _$$CancelProcessingImplCopyWith(_$CancelProcessingImpl value,
          $Res Function(_$CancelProcessingImpl) then) =
      __$$CancelProcessingImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$CancelProcessingImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$CancelProcessingImpl>
    implements _$$CancelProcessingImplCopyWith<$Res> {
  __$$CancelProcessingImplCopyWithImpl(_$CancelProcessingImpl _value,
      $Res Function(_$CancelProcessingImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$CancelProcessingImpl implements _CancelProcessing {
  const _$CancelProcessingImpl();

  @override
  String toString() {
    return 'ScannerEvent.cancelProcessing()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$CancelProcessingImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return cancelProcessing();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return cancelProcessing?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (cancelProcessing != null) {
      return cancelProcessing();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return cancelProcessing(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return cancelProcessing?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (cancelProcessing != null) {
      return cancelProcessing(this);
    }
    return orElse();
  }
}

abstract class _CancelProcessing implements ScannerEvent {
  const factory _CancelProcessing() = _$CancelProcessingImpl;
}

/// @nodoc
abstract class _$$RetryImplCopyWith<$Res> {
  factory _$$RetryImplCopyWith(
          _$RetryImpl value, $Res Function(_$RetryImpl) then) =
      __$$RetryImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int pageIndex});
}

/// @nodoc
class __$$RetryImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$RetryImpl>
    implements _$$RetryImplCopyWith<$Res> {
  __$$RetryImplCopyWithImpl(
      _$RetryImpl _value, $Res Function(_$RetryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pageIndex = null,
  }) {
    return _then(_$RetryImpl(
      null == pageIndex
          ? _value.pageIndex
          : pageIndex // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$RetryImpl implements _Retry {
  const _$RetryImpl(this.pageIndex);

  @override
  final int pageIndex;

  @override
  String toString() {
    return 'ScannerEvent.retry(pageIndex: $pageIndex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RetryImpl &&
            (identical(other.pageIndex, pageIndex) ||
                other.pageIndex == pageIndex));
  }

  @override
  int get hashCode => Object.hash(runtimeType, pageIndex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RetryImplCopyWith<_$RetryImpl> get copyWith =>
      __$$RetryImplCopyWithImpl<_$RetryImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return retry(pageIndex);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return retry?.call(pageIndex);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (retry != null) {
      return retry(pageIndex);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return retry(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return retry?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (retry != null) {
      return retry(this);
    }
    return orElse();
  }
}

abstract class _Retry implements ScannerEvent {
  const factory _Retry(final int pageIndex) = _$RetryImpl;

  int get pageIndex;
  @JsonKey(ignore: true)
  _$$RetryImplCopyWith<_$RetryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ClearImplCopyWith<$Res> {
  factory _$$ClearImplCopyWith(
          _$ClearImpl value, $Res Function(_$ClearImpl) then) =
      __$$ClearImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$ClearImplCopyWithImpl<$Res>
    extends _$ScannerEventCopyWithImpl<$Res, _$ClearImpl>
    implements _$$ClearImplCopyWith<$Res> {
  __$$ClearImplCopyWithImpl(
      _$ClearImpl _value, $Res Function(_$ClearImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$ClearImpl implements _Clear {
  const _$ClearImpl();

  @override
  String toString() {
    return 'ScannerEvent.clear()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$ClearImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initializeCamera,
    required TResult Function() capturePage,
    required TResult Function(int pageIndex) retakePage,
    required TResult Function(int pageIndex) removePage,
    required TResult Function(int oldIndex, int newIndex) reorderPages,
    required TResult Function(ScanOptions options) startProcessing,
    required TResult Function() cancelProcessing,
    required TResult Function(int pageIndex) retry,
    required TResult Function() clear,
  }) {
    return clear();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initializeCamera,
    TResult? Function()? capturePage,
    TResult? Function(int pageIndex)? retakePage,
    TResult? Function(int pageIndex)? removePage,
    TResult? Function(int oldIndex, int newIndex)? reorderPages,
    TResult? Function(ScanOptions options)? startProcessing,
    TResult? Function()? cancelProcessing,
    TResult? Function(int pageIndex)? retry,
    TResult? Function()? clear,
  }) {
    return clear?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initializeCamera,
    TResult Function()? capturePage,
    TResult Function(int pageIndex)? retakePage,
    TResult Function(int pageIndex)? removePage,
    TResult Function(int oldIndex, int newIndex)? reorderPages,
    TResult Function(ScanOptions options)? startProcessing,
    TResult Function()? cancelProcessing,
    TResult Function(int pageIndex)? retry,
    TResult Function()? clear,
    required TResult orElse(),
  }) {
    if (clear != null) {
      return clear();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_InitializeCamera value) initializeCamera,
    required TResult Function(_CapturePage value) capturePage,
    required TResult Function(_RetakePage value) retakePage,
    required TResult Function(_RemovePage value) removePage,
    required TResult Function(_ReorderPages value) reorderPages,
    required TResult Function(_StartProcessing value) startProcessing,
    required TResult Function(_CancelProcessing value) cancelProcessing,
    required TResult Function(_Retry value) retry,
    required TResult Function(_Clear value) clear,
  }) {
    return clear(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_InitializeCamera value)? initializeCamera,
    TResult? Function(_CapturePage value)? capturePage,
    TResult? Function(_RetakePage value)? retakePage,
    TResult? Function(_RemovePage value)? removePage,
    TResult? Function(_ReorderPages value)? reorderPages,
    TResult? Function(_StartProcessing value)? startProcessing,
    TResult? Function(_CancelProcessing value)? cancelProcessing,
    TResult? Function(_Retry value)? retry,
    TResult? Function(_Clear value)? clear,
  }) {
    return clear?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_InitializeCamera value)? initializeCamera,
    TResult Function(_CapturePage value)? capturePage,
    TResult Function(_RetakePage value)? retakePage,
    TResult Function(_RemovePage value)? removePage,
    TResult Function(_ReorderPages value)? reorderPages,
    TResult Function(_StartProcessing value)? startProcessing,
    TResult Function(_CancelProcessing value)? cancelProcessing,
    TResult Function(_Retry value)? retry,
    TResult Function(_Clear value)? clear,
    required TResult orElse(),
  }) {
    if (clear != null) {
      return clear(this);
    }
    return orElse();
  }
}

abstract class _Clear implements ScannerEvent {
  const factory _Clear() = _$ClearImpl;
}
