// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'evaluation_bloc.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$EvaluationState {
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $EvaluationStateCopyWith<$Res> {
  factory $EvaluationStateCopyWith(
          EvaluationState value, $Res Function(EvaluationState) then) =
      _$EvaluationStateCopyWithImpl<$Res, EvaluationState>;
}

/// @nodoc
class _$EvaluationStateCopyWithImpl<$Res, $Val extends EvaluationState>
    implements $EvaluationStateCopyWith<$Res> {
  _$EvaluationStateCopyWithImpl(this._value, this._then);

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
    extends _$EvaluationStateCopyWithImpl<$Res, _$InitialImpl>
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
    return 'EvaluationState.initial()';
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
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return initial();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return initial?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
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
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return initial(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return initial?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (initial != null) {
      return initial(this);
    }
    return orElse();
  }
}

abstract class _Initial implements EvaluationState {
  const factory _Initial() = _$InitialImpl;
}

/// @nodoc
abstract class _$$LoadingImplCopyWith<$Res> {
  factory _$$LoadingImplCopyWith(
          _$LoadingImpl value, $Res Function(_$LoadingImpl) then) =
      __$$LoadingImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$LoadingImplCopyWithImpl<$Res>
    extends _$EvaluationStateCopyWithImpl<$Res, _$LoadingImpl>
    implements _$$LoadingImplCopyWith<$Res> {
  __$$LoadingImplCopyWithImpl(
      _$LoadingImpl _value, $Res Function(_$LoadingImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$LoadingImpl implements _Loading {
  const _$LoadingImpl();

  @override
  String toString() {
    return 'EvaluationState.loading()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$LoadingImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return loading();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return loading?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) {
    if (loading != null) {
      return loading();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return loading(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return loading?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (loading != null) {
      return loading(this);
    }
    return orElse();
  }
}

abstract class _Loading implements EvaluationState {
  const factory _Loading() = _$LoadingImpl;
}

/// @nodoc
abstract class _$$AIEvaluatedImplCopyWith<$Res> {
  factory _$$AIEvaluatedImplCopyWith(
          _$AIEvaluatedImpl value, $Res Function(_$AIEvaluatedImpl) then) =
      __$$AIEvaluatedImplCopyWithImpl<$Res>;
  @useResult
  $Res call({List<EvaluationResult> results});
}

/// @nodoc
class __$$AIEvaluatedImplCopyWithImpl<$Res>
    extends _$EvaluationStateCopyWithImpl<$Res, _$AIEvaluatedImpl>
    implements _$$AIEvaluatedImplCopyWith<$Res> {
  __$$AIEvaluatedImplCopyWithImpl(
      _$AIEvaluatedImpl _value, $Res Function(_$AIEvaluatedImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? results = null,
  }) {
    return _then(_$AIEvaluatedImpl(
      null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<EvaluationResult>,
    ));
  }
}

/// @nodoc

class _$AIEvaluatedImpl implements _AIEvaluated {
  const _$AIEvaluatedImpl(final List<EvaluationResult> results)
      : _results = results;

  final List<EvaluationResult> _results;
  @override
  List<EvaluationResult> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'EvaluationState.aiEvaluated(results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AIEvaluatedImpl &&
            const DeepCollectionEquality().equals(other._results, _results));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_results));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AIEvaluatedImplCopyWith<_$AIEvaluatedImpl> get copyWith =>
      __$$AIEvaluatedImplCopyWithImpl<_$AIEvaluatedImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return aiEvaluated(results);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return aiEvaluated?.call(results);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) {
    if (aiEvaluated != null) {
      return aiEvaluated(results);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return aiEvaluated(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return aiEvaluated?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (aiEvaluated != null) {
      return aiEvaluated(this);
    }
    return orElse();
  }
}

abstract class _AIEvaluated implements EvaluationState {
  const factory _AIEvaluated(final List<EvaluationResult> results) =
      _$AIEvaluatedImpl;

  List<EvaluationResult> get results;
  @JsonKey(ignore: true)
  _$$AIEvaluatedImplCopyWith<_$AIEvaluatedImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$TeacherReviewingImplCopyWith<$Res> {
  factory _$$TeacherReviewingImplCopyWith(_$TeacherReviewingImpl value,
          $Res Function(_$TeacherReviewingImpl) then) =
      __$$TeacherReviewingImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int currentIndex, List<EvaluationResult> results});
}

/// @nodoc
class __$$TeacherReviewingImplCopyWithImpl<$Res>
    extends _$EvaluationStateCopyWithImpl<$Res, _$TeacherReviewingImpl>
    implements _$$TeacherReviewingImplCopyWith<$Res> {
  __$$TeacherReviewingImplCopyWithImpl(_$TeacherReviewingImpl _value,
      $Res Function(_$TeacherReviewingImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentIndex = null,
    Object? results = null,
  }) {
    return _then(_$TeacherReviewingImpl(
      null == currentIndex
          ? _value.currentIndex
          : currentIndex // ignore: cast_nullable_to_non_nullable
              as int,
      null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<EvaluationResult>,
    ));
  }
}

/// @nodoc

class _$TeacherReviewingImpl implements _TeacherReviewing {
  const _$TeacherReviewingImpl(
      this.currentIndex, final List<EvaluationResult> results)
      : _results = results;

  @override
  final int currentIndex;
  final List<EvaluationResult> _results;
  @override
  List<EvaluationResult> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'EvaluationState.teacherReviewing(currentIndex: $currentIndex, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TeacherReviewingImpl &&
            (identical(other.currentIndex, currentIndex) ||
                other.currentIndex == currentIndex) &&
            const DeepCollectionEquality().equals(other._results, _results));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType, currentIndex, const DeepCollectionEquality().hash(_results));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$TeacherReviewingImplCopyWith<_$TeacherReviewingImpl> get copyWith =>
      __$$TeacherReviewingImplCopyWithImpl<_$TeacherReviewingImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return teacherReviewing(currentIndex, results);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return teacherReviewing?.call(currentIndex, results);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) {
    if (teacherReviewing != null) {
      return teacherReviewing(currentIndex, results);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return teacherReviewing(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return teacherReviewing?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (teacherReviewing != null) {
      return teacherReviewing(this);
    }
    return orElse();
  }
}

abstract class _TeacherReviewing implements EvaluationState {
  const factory _TeacherReviewing(
          final int currentIndex, final List<EvaluationResult> results) =
      _$TeacherReviewingImpl;

  int get currentIndex;
  List<EvaluationResult> get results;
  @JsonKey(ignore: true)
  _$$TeacherReviewingImplCopyWith<_$TeacherReviewingImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$TeacherReviewedImplCopyWith<$Res> {
  factory _$$TeacherReviewedImplCopyWith(_$TeacherReviewedImpl value,
          $Res Function(_$TeacherReviewedImpl) then) =
      __$$TeacherReviewedImplCopyWithImpl<$Res>;
  @useResult
  $Res call({List<EvaluationResult> results});
}

/// @nodoc
class __$$TeacherReviewedImplCopyWithImpl<$Res>
    extends _$EvaluationStateCopyWithImpl<$Res, _$TeacherReviewedImpl>
    implements _$$TeacherReviewedImplCopyWith<$Res> {
  __$$TeacherReviewedImplCopyWithImpl(
      _$TeacherReviewedImpl _value, $Res Function(_$TeacherReviewedImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? results = null,
  }) {
    return _then(_$TeacherReviewedImpl(
      null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<EvaluationResult>,
    ));
  }
}

/// @nodoc

class _$TeacherReviewedImpl implements _TeacherReviewed {
  const _$TeacherReviewedImpl(final List<EvaluationResult> results)
      : _results = results;

  final List<EvaluationResult> _results;
  @override
  List<EvaluationResult> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'EvaluationState.teacherReviewed(results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TeacherReviewedImpl &&
            const DeepCollectionEquality().equals(other._results, _results));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_results));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$TeacherReviewedImplCopyWith<_$TeacherReviewedImpl> get copyWith =>
      __$$TeacherReviewedImplCopyWithImpl<_$TeacherReviewedImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return teacherReviewed(results);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return teacherReviewed?.call(results);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) {
    if (teacherReviewed != null) {
      return teacherReviewed(results);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return teacherReviewed(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return teacherReviewed?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (teacherReviewed != null) {
      return teacherReviewed(this);
    }
    return orElse();
  }
}

abstract class _TeacherReviewed implements EvaluationState {
  const factory _TeacherReviewed(final List<EvaluationResult> results) =
      _$TeacherReviewedImpl;

  List<EvaluationResult> get results;
  @JsonKey(ignore: true)
  _$$TeacherReviewedImplCopyWith<_$TeacherReviewedImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$FinalizedImplCopyWith<$Res> {
  factory _$$FinalizedImplCopyWith(
          _$FinalizedImpl value, $Res Function(_$FinalizedImpl) then) =
      __$$FinalizedImplCopyWithImpl<$Res>;
  @useResult
  $Res call({List<StudentReport> reports});
}

/// @nodoc
class __$$FinalizedImplCopyWithImpl<$Res>
    extends _$EvaluationStateCopyWithImpl<$Res, _$FinalizedImpl>
    implements _$$FinalizedImplCopyWith<$Res> {
  __$$FinalizedImplCopyWithImpl(
      _$FinalizedImpl _value, $Res Function(_$FinalizedImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? reports = null,
  }) {
    return _then(_$FinalizedImpl(
      null == reports
          ? _value._reports
          : reports // ignore: cast_nullable_to_non_nullable
              as List<StudentReport>,
    ));
  }
}

/// @nodoc

class _$FinalizedImpl implements _Finalized {
  const _$FinalizedImpl(final List<StudentReport> reports) : _reports = reports;

  final List<StudentReport> _reports;
  @override
  List<StudentReport> get reports {
    if (_reports is EqualUnmodifiableListView) return _reports;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_reports);
  }

  @override
  String toString() {
    return 'EvaluationState.finalized(reports: $reports)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$FinalizedImpl &&
            const DeepCollectionEquality().equals(other._reports, _reports));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_reports));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$FinalizedImplCopyWith<_$FinalizedImpl> get copyWith =>
      __$$FinalizedImplCopyWithImpl<_$FinalizedImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return finalized(reports);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return finalized?.call(reports);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) {
    if (finalized != null) {
      return finalized(reports);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return finalized(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return finalized?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (finalized != null) {
      return finalized(this);
    }
    return orElse();
  }
}

abstract class _Finalized implements EvaluationState {
  const factory _Finalized(final List<StudentReport> reports) = _$FinalizedImpl;

  List<StudentReport> get reports;
  @JsonKey(ignore: true)
  _$$FinalizedImplCopyWith<_$FinalizedImpl> get copyWith =>
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
    extends _$EvaluationStateCopyWithImpl<$Res, _$ErrorImpl>
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
    return 'EvaluationState.error(message: $message)';
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
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return error(message);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return error?.call(message);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
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
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return error(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return error?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (error != null) {
      return error(this);
    }
    return orElse();
  }
}

abstract class _Error implements EvaluationState {
  const factory _Error(final String message) = _$ErrorImpl;

  String get message;
  @JsonKey(ignore: true)
  _$$ErrorImplCopyWith<_$ErrorImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$PartialErrorImplCopyWith<$Res> {
  factory _$$PartialErrorImplCopyWith(
          _$PartialErrorImpl value, $Res Function(_$PartialErrorImpl) then) =
      __$$PartialErrorImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int completed, int total, String message});
}

/// @nodoc
class __$$PartialErrorImplCopyWithImpl<$Res>
    extends _$EvaluationStateCopyWithImpl<$Res, _$PartialErrorImpl>
    implements _$$PartialErrorImplCopyWith<$Res> {
  __$$PartialErrorImplCopyWithImpl(
      _$PartialErrorImpl _value, $Res Function(_$PartialErrorImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? completed = null,
    Object? total = null,
    Object? message = null,
  }) {
    return _then(_$PartialErrorImpl(
      null == completed
          ? _value.completed
          : completed // ignore: cast_nullable_to_non_nullable
              as int,
      null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc

class _$PartialErrorImpl implements _PartialError {
  const _$PartialErrorImpl(this.completed, this.total, this.message);

  @override
  final int completed;
  @override
  final int total;
  @override
  final String message;

  @override
  String toString() {
    return 'EvaluationState.partialError(completed: $completed, total: $total, message: $message)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PartialErrorImpl &&
            (identical(other.completed, completed) ||
                other.completed == completed) &&
            (identical(other.total, total) || other.total == total) &&
            (identical(other.message, message) || other.message == message));
  }

  @override
  int get hashCode => Object.hash(runtimeType, completed, total, message);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PartialErrorImplCopyWith<_$PartialErrorImpl> get copyWith =>
      __$$PartialErrorImplCopyWithImpl<_$PartialErrorImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function() initial,
    required TResult Function() loading,
    required TResult Function(List<EvaluationResult> results) aiEvaluated,
    required TResult Function(int currentIndex, List<EvaluationResult> results)
        teacherReviewing,
    required TResult Function(List<EvaluationResult> results) teacherReviewed,
    required TResult Function(List<StudentReport> reports) finalized,
    required TResult Function(String message) error,
    required TResult Function(int completed, int total, String message)
        partialError,
  }) {
    return partialError(completed, total, message);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function()? initial,
    TResult? Function()? loading,
    TResult? Function(List<EvaluationResult> results)? aiEvaluated,
    TResult? Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult? Function(List<EvaluationResult> results)? teacherReviewed,
    TResult? Function(List<StudentReport> reports)? finalized,
    TResult? Function(String message)? error,
    TResult? Function(int completed, int total, String message)? partialError,
  }) {
    return partialError?.call(completed, total, message);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function()? initial,
    TResult Function()? loading,
    TResult Function(List<EvaluationResult> results)? aiEvaluated,
    TResult Function(int currentIndex, List<EvaluationResult> results)?
        teacherReviewing,
    TResult Function(List<EvaluationResult> results)? teacherReviewed,
    TResult Function(List<StudentReport> reports)? finalized,
    TResult Function(String message)? error,
    TResult Function(int completed, int total, String message)? partialError,
    required TResult orElse(),
  }) {
    if (partialError != null) {
      return partialError(completed, total, message);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_Initial value) initial,
    required TResult Function(_Loading value) loading,
    required TResult Function(_AIEvaluated value) aiEvaluated,
    required TResult Function(_TeacherReviewing value) teacherReviewing,
    required TResult Function(_TeacherReviewed value) teacherReviewed,
    required TResult Function(_Finalized value) finalized,
    required TResult Function(_Error value) error,
    required TResult Function(_PartialError value) partialError,
  }) {
    return partialError(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_Initial value)? initial,
    TResult? Function(_Loading value)? loading,
    TResult? Function(_AIEvaluated value)? aiEvaluated,
    TResult? Function(_TeacherReviewing value)? teacherReviewing,
    TResult? Function(_TeacherReviewed value)? teacherReviewed,
    TResult? Function(_Finalized value)? finalized,
    TResult? Function(_Error value)? error,
    TResult? Function(_PartialError value)? partialError,
  }) {
    return partialError?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_Initial value)? initial,
    TResult Function(_Loading value)? loading,
    TResult Function(_AIEvaluated value)? aiEvaluated,
    TResult Function(_TeacherReviewing value)? teacherReviewing,
    TResult Function(_TeacherReviewed value)? teacherReviewed,
    TResult Function(_Finalized value)? finalized,
    TResult Function(_Error value)? error,
    TResult Function(_PartialError value)? partialError,
    required TResult orElse(),
  }) {
    if (partialError != null) {
      return partialError(this);
    }
    return orElse();
  }
}

abstract class _PartialError implements EvaluationState {
  const factory _PartialError(
          final int completed, final int total, final String message) =
      _$PartialErrorImpl;

  int get completed;
  int get total;
  String get message;
  @JsonKey(ignore: true)
  _$$PartialErrorImplCopyWith<_$PartialErrorImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$EvaluationEvent {
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $EvaluationEventCopyWith<$Res> {
  factory $EvaluationEventCopyWith(
          EvaluationEvent value, $Res Function(EvaluationEvent) then) =
      _$EvaluationEventCopyWithImpl<$Res, EvaluationEvent>;
}

/// @nodoc
class _$EvaluationEventCopyWithImpl<$Res, $Val extends EvaluationEvent>
    implements $EvaluationEventCopyWith<$Res> {
  _$EvaluationEventCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;
}

/// @nodoc
abstract class _$$StartEvaluationImplCopyWith<$Res> {
  factory _$$StartEvaluationImplCopyWith(_$StartEvaluationImpl value,
          $Res Function(_$StartEvaluationImpl) then) =
      __$$StartEvaluationImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String answerSheetId});
}

/// @nodoc
class __$$StartEvaluationImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$StartEvaluationImpl>
    implements _$$StartEvaluationImplCopyWith<$Res> {
  __$$StartEvaluationImplCopyWithImpl(
      _$StartEvaluationImpl _value, $Res Function(_$StartEvaluationImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? answerSheetId = null,
  }) {
    return _then(_$StartEvaluationImpl(
      null == answerSheetId
          ? _value.answerSheetId
          : answerSheetId // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc

class _$StartEvaluationImpl implements _StartEvaluation {
  const _$StartEvaluationImpl(this.answerSheetId);

  @override
  final String answerSheetId;

  @override
  String toString() {
    return 'EvaluationEvent.startEvaluation(answerSheetId: $answerSheetId)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StartEvaluationImpl &&
            (identical(other.answerSheetId, answerSheetId) ||
                other.answerSheetId == answerSheetId));
  }

  @override
  int get hashCode => Object.hash(runtimeType, answerSheetId);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$StartEvaluationImplCopyWith<_$StartEvaluationImpl> get copyWith =>
      __$$StartEvaluationImplCopyWithImpl<_$StartEvaluationImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return startEvaluation(answerSheetId);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return startEvaluation?.call(answerSheetId);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (startEvaluation != null) {
      return startEvaluation(answerSheetId);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return startEvaluation(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return startEvaluation?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (startEvaluation != null) {
      return startEvaluation(this);
    }
    return orElse();
  }
}

abstract class _StartEvaluation implements EvaluationEvent {
  const factory _StartEvaluation(final String answerSheetId) =
      _$StartEvaluationImpl;

  String get answerSheetId;
  @JsonKey(ignore: true)
  _$$StartEvaluationImplCopyWith<_$StartEvaluationImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$NextQuestionImplCopyWith<$Res> {
  factory _$$NextQuestionImplCopyWith(
          _$NextQuestionImpl value, $Res Function(_$NextQuestionImpl) then) =
      __$$NextQuestionImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$NextQuestionImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$NextQuestionImpl>
    implements _$$NextQuestionImplCopyWith<$Res> {
  __$$NextQuestionImplCopyWithImpl(
      _$NextQuestionImpl _value, $Res Function(_$NextQuestionImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$NextQuestionImpl implements _NextQuestion {
  const _$NextQuestionImpl();

  @override
  String toString() {
    return 'EvaluationEvent.nextQuestion()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$NextQuestionImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return nextQuestion();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return nextQuestion?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (nextQuestion != null) {
      return nextQuestion();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return nextQuestion(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return nextQuestion?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (nextQuestion != null) {
      return nextQuestion(this);
    }
    return orElse();
  }
}

abstract class _NextQuestion implements EvaluationEvent {
  const factory _NextQuestion() = _$NextQuestionImpl;
}

/// @nodoc
abstract class _$$PreviousQuestionImplCopyWith<$Res> {
  factory _$$PreviousQuestionImplCopyWith(_$PreviousQuestionImpl value,
          $Res Function(_$PreviousQuestionImpl) then) =
      __$$PreviousQuestionImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$PreviousQuestionImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$PreviousQuestionImpl>
    implements _$$PreviousQuestionImplCopyWith<$Res> {
  __$$PreviousQuestionImplCopyWithImpl(_$PreviousQuestionImpl _value,
      $Res Function(_$PreviousQuestionImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$PreviousQuestionImpl implements _PreviousQuestion {
  const _$PreviousQuestionImpl();

  @override
  String toString() {
    return 'EvaluationEvent.previousQuestion()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$PreviousQuestionImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return previousQuestion();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return previousQuestion?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (previousQuestion != null) {
      return previousQuestion();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return previousQuestion(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return previousQuestion?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (previousQuestion != null) {
      return previousQuestion(this);
    }
    return orElse();
  }
}

abstract class _PreviousQuestion implements EvaluationEvent {
  const factory _PreviousQuestion() = _$PreviousQuestionImpl;
}

/// @nodoc
abstract class _$$ApproveEvaluationImplCopyWith<$Res> {
  factory _$$ApproveEvaluationImplCopyWith(_$ApproveEvaluationImpl value,
          $Res Function(_$ApproveEvaluationImpl) then) =
      __$$ApproveEvaluationImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int index});
}

/// @nodoc
class __$$ApproveEvaluationImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$ApproveEvaluationImpl>
    implements _$$ApproveEvaluationImplCopyWith<$Res> {
  __$$ApproveEvaluationImplCopyWithImpl(_$ApproveEvaluationImpl _value,
      $Res Function(_$ApproveEvaluationImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? index = null,
  }) {
    return _then(_$ApproveEvaluationImpl(
      null == index
          ? _value.index
          : index // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$ApproveEvaluationImpl implements _ApproveEvaluation {
  const _$ApproveEvaluationImpl(this.index);

  @override
  final int index;

  @override
  String toString() {
    return 'EvaluationEvent.approveEvaluation(index: $index)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApproveEvaluationImpl &&
            (identical(other.index, index) || other.index == index));
  }

  @override
  int get hashCode => Object.hash(runtimeType, index);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ApproveEvaluationImplCopyWith<_$ApproveEvaluationImpl> get copyWith =>
      __$$ApproveEvaluationImplCopyWithImpl<_$ApproveEvaluationImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return approveEvaluation(index);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return approveEvaluation?.call(index);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (approveEvaluation != null) {
      return approveEvaluation(index);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return approveEvaluation(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return approveEvaluation?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (approveEvaluation != null) {
      return approveEvaluation(this);
    }
    return orElse();
  }
}

abstract class _ApproveEvaluation implements EvaluationEvent {
  const factory _ApproveEvaluation(final int index) = _$ApproveEvaluationImpl;

  int get index;
  @JsonKey(ignore: true)
  _$$ApproveEvaluationImplCopyWith<_$ApproveEvaluationImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$AdjustMarksImplCopyWith<$Res> {
  factory _$$AdjustMarksImplCopyWith(
          _$AdjustMarksImpl value, $Res Function(_$AdjustMarksImpl) then) =
      __$$AdjustMarksImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int index, int newMarks, String? comment});
}

/// @nodoc
class __$$AdjustMarksImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$AdjustMarksImpl>
    implements _$$AdjustMarksImplCopyWith<$Res> {
  __$$AdjustMarksImplCopyWithImpl(
      _$AdjustMarksImpl _value, $Res Function(_$AdjustMarksImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? index = null,
    Object? newMarks = null,
    Object? comment = freezed,
  }) {
    return _then(_$AdjustMarksImpl(
      null == index
          ? _value.index
          : index // ignore: cast_nullable_to_non_nullable
              as int,
      null == newMarks
          ? _value.newMarks
          : newMarks // ignore: cast_nullable_to_non_nullable
              as int,
      freezed == comment
          ? _value.comment
          : comment // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$AdjustMarksImpl implements _AdjustMarks {
  const _$AdjustMarksImpl(this.index, this.newMarks, this.comment);

  @override
  final int index;
  @override
  final int newMarks;
  @override
  final String? comment;

  @override
  String toString() {
    return 'EvaluationEvent.adjustMarks(index: $index, newMarks: $newMarks, comment: $comment)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AdjustMarksImpl &&
            (identical(other.index, index) || other.index == index) &&
            (identical(other.newMarks, newMarks) ||
                other.newMarks == newMarks) &&
            (identical(other.comment, comment) || other.comment == comment));
  }

  @override
  int get hashCode => Object.hash(runtimeType, index, newMarks, comment);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AdjustMarksImplCopyWith<_$AdjustMarksImpl> get copyWith =>
      __$$AdjustMarksImplCopyWithImpl<_$AdjustMarksImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return adjustMarks(index, newMarks, comment);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return adjustMarks?.call(index, newMarks, comment);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (adjustMarks != null) {
      return adjustMarks(index, newMarks, comment);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return adjustMarks(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return adjustMarks?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (adjustMarks != null) {
      return adjustMarks(this);
    }
    return orElse();
  }
}

abstract class _AdjustMarks implements EvaluationEvent {
  const factory _AdjustMarks(
          final int index, final int newMarks, final String? comment) =
      _$AdjustMarksImpl;

  int get index;
  int get newMarks;
  String? get comment;
  @JsonKey(ignore: true)
  _$$AdjustMarksImplCopyWith<_$AdjustMarksImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ChangeVerdictImplCopyWith<$Res> {
  factory _$$ChangeVerdictImplCopyWith(
          _$ChangeVerdictImpl value, $Res Function(_$ChangeVerdictImpl) then) =
      __$$ChangeVerdictImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int index, EvaluationVerdict verdict, String? comment});
}

/// @nodoc
class __$$ChangeVerdictImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$ChangeVerdictImpl>
    implements _$$ChangeVerdictImplCopyWith<$Res> {
  __$$ChangeVerdictImplCopyWithImpl(
      _$ChangeVerdictImpl _value, $Res Function(_$ChangeVerdictImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? index = null,
    Object? verdict = null,
    Object? comment = freezed,
  }) {
    return _then(_$ChangeVerdictImpl(
      null == index
          ? _value.index
          : index // ignore: cast_nullable_to_non_nullable
              as int,
      null == verdict
          ? _value.verdict
          : verdict // ignore: cast_nullable_to_non_nullable
              as EvaluationVerdict,
      freezed == comment
          ? _value.comment
          : comment // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$ChangeVerdictImpl implements _ChangeVerdict {
  const _$ChangeVerdictImpl(this.index, this.verdict, this.comment);

  @override
  final int index;
  @override
  final EvaluationVerdict verdict;
  @override
  final String? comment;

  @override
  String toString() {
    return 'EvaluationEvent.changeVerdict(index: $index, verdict: $verdict, comment: $comment)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChangeVerdictImpl &&
            (identical(other.index, index) || other.index == index) &&
            (identical(other.verdict, verdict) || other.verdict == verdict) &&
            (identical(other.comment, comment) || other.comment == comment));
  }

  @override
  int get hashCode => Object.hash(runtimeType, index, verdict, comment);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChangeVerdictImplCopyWith<_$ChangeVerdictImpl> get copyWith =>
      __$$ChangeVerdictImplCopyWithImpl<_$ChangeVerdictImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return changeVerdict(index, verdict, comment);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return changeVerdict?.call(index, verdict, comment);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (changeVerdict != null) {
      return changeVerdict(index, verdict, comment);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return changeVerdict(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return changeVerdict?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (changeVerdict != null) {
      return changeVerdict(this);
    }
    return orElse();
  }
}

abstract class _ChangeVerdict implements EvaluationEvent {
  const factory _ChangeVerdict(final int index, final EvaluationVerdict verdict,
      final String? comment) = _$ChangeVerdictImpl;

  int get index;
  EvaluationVerdict get verdict;
  String? get comment;
  @JsonKey(ignore: true)
  _$$ChangeVerdictImplCopyWith<_$ChangeVerdictImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$SkipQuestionImplCopyWith<$Res> {
  factory _$$SkipQuestionImplCopyWith(
          _$SkipQuestionImpl value, $Res Function(_$SkipQuestionImpl) then) =
      __$$SkipQuestionImplCopyWithImpl<$Res>;
  @useResult
  $Res call({int index});
}

/// @nodoc
class __$$SkipQuestionImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$SkipQuestionImpl>
    implements _$$SkipQuestionImplCopyWith<$Res> {
  __$$SkipQuestionImplCopyWithImpl(
      _$SkipQuestionImpl _value, $Res Function(_$SkipQuestionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? index = null,
  }) {
    return _then(_$SkipQuestionImpl(
      null == index
          ? _value.index
          : index // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$SkipQuestionImpl implements _SkipQuestion {
  const _$SkipQuestionImpl(this.index);

  @override
  final int index;

  @override
  String toString() {
    return 'EvaluationEvent.skipQuestion(index: $index)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SkipQuestionImpl &&
            (identical(other.index, index) || other.index == index));
  }

  @override
  int get hashCode => Object.hash(runtimeType, index);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SkipQuestionImplCopyWith<_$SkipQuestionImpl> get copyWith =>
      __$$SkipQuestionImplCopyWithImpl<_$SkipQuestionImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return skipQuestion(index);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return skipQuestion?.call(index);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (skipQuestion != null) {
      return skipQuestion(index);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return skipQuestion(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return skipQuestion?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (skipQuestion != null) {
      return skipQuestion(this);
    }
    return orElse();
  }
}

abstract class _SkipQuestion implements EvaluationEvent {
  const factory _SkipQuestion(final int index) = _$SkipQuestionImpl;

  int get index;
  @JsonKey(ignore: true)
  _$$SkipQuestionImplCopyWith<_$SkipQuestionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$FinalizeEvaluationImplCopyWith<$Res> {
  factory _$$FinalizeEvaluationImplCopyWith(_$FinalizeEvaluationImpl value,
          $Res Function(_$FinalizeEvaluationImpl) then) =
      __$$FinalizeEvaluationImplCopyWithImpl<$Res>;
  @useResult
  $Res call({List<String> studentIds});
}

/// @nodoc
class __$$FinalizeEvaluationImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$FinalizeEvaluationImpl>
    implements _$$FinalizeEvaluationImplCopyWith<$Res> {
  __$$FinalizeEvaluationImplCopyWithImpl(_$FinalizeEvaluationImpl _value,
      $Res Function(_$FinalizeEvaluationImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentIds = null,
  }) {
    return _then(_$FinalizeEvaluationImpl(
      null == studentIds
          ? _value._studentIds
          : studentIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc

class _$FinalizeEvaluationImpl implements _FinalizeEvaluation {
  const _$FinalizeEvaluationImpl(final List<String> studentIds)
      : _studentIds = studentIds;

  final List<String> _studentIds;
  @override
  List<String> get studentIds {
    if (_studentIds is EqualUnmodifiableListView) return _studentIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_studentIds);
  }

  @override
  String toString() {
    return 'EvaluationEvent.finalizeEvaluation(studentIds: $studentIds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$FinalizeEvaluationImpl &&
            const DeepCollectionEquality()
                .equals(other._studentIds, _studentIds));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType, const DeepCollectionEquality().hash(_studentIds));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$FinalizeEvaluationImplCopyWith<_$FinalizeEvaluationImpl> get copyWith =>
      __$$FinalizeEvaluationImplCopyWithImpl<_$FinalizeEvaluationImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return finalizeEvaluation(studentIds);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return finalizeEvaluation?.call(studentIds);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (finalizeEvaluation != null) {
      return finalizeEvaluation(studentIds);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return finalizeEvaluation(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return finalizeEvaluation?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (finalizeEvaluation != null) {
      return finalizeEvaluation(this);
    }
    return orElse();
  }
}

abstract class _FinalizeEvaluation implements EvaluationEvent {
  const factory _FinalizeEvaluation(final List<String> studentIds) =
      _$FinalizeEvaluationImpl;

  List<String> get studentIds;
  @JsonKey(ignore: true)
  _$$FinalizeEvaluationImplCopyWith<_$FinalizeEvaluationImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ClearErrorImplCopyWith<$Res> {
  factory _$$ClearErrorImplCopyWith(
          _$ClearErrorImpl value, $Res Function(_$ClearErrorImpl) then) =
      __$$ClearErrorImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$ClearErrorImplCopyWithImpl<$Res>
    extends _$EvaluationEventCopyWithImpl<$Res, _$ClearErrorImpl>
    implements _$$ClearErrorImplCopyWith<$Res> {
  __$$ClearErrorImplCopyWithImpl(
      _$ClearErrorImpl _value, $Res Function(_$ClearErrorImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$ClearErrorImpl implements _ClearError {
  const _$ClearErrorImpl();

  @override
  String toString() {
    return 'EvaluationEvent.clearError()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$ClearErrorImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(String answerSheetId) startEvaluation,
    required TResult Function() nextQuestion,
    required TResult Function() previousQuestion,
    required TResult Function(int index) approveEvaluation,
    required TResult Function(int index, int newMarks, String? comment)
        adjustMarks,
    required TResult Function(
            int index, EvaluationVerdict verdict, String? comment)
        changeVerdict,
    required TResult Function(int index) skipQuestion,
    required TResult Function(List<String> studentIds) finalizeEvaluation,
    required TResult Function() clearError,
  }) {
    return clearError();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(String answerSheetId)? startEvaluation,
    TResult? Function()? nextQuestion,
    TResult? Function()? previousQuestion,
    TResult? Function(int index)? approveEvaluation,
    TResult? Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult? Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult? Function(int index)? skipQuestion,
    TResult? Function(List<String> studentIds)? finalizeEvaluation,
    TResult? Function()? clearError,
  }) {
    return clearError?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(String answerSheetId)? startEvaluation,
    TResult Function()? nextQuestion,
    TResult Function()? previousQuestion,
    TResult Function(int index)? approveEvaluation,
    TResult Function(int index, int newMarks, String? comment)? adjustMarks,
    TResult Function(int index, EvaluationVerdict verdict, String? comment)?
        changeVerdict,
    TResult Function(int index)? skipQuestion,
    TResult Function(List<String> studentIds)? finalizeEvaluation,
    TResult Function()? clearError,
    required TResult orElse(),
  }) {
    if (clearError != null) {
      return clearError();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(_StartEvaluation value) startEvaluation,
    required TResult Function(_NextQuestion value) nextQuestion,
    required TResult Function(_PreviousQuestion value) previousQuestion,
    required TResult Function(_ApproveEvaluation value) approveEvaluation,
    required TResult Function(_AdjustMarks value) adjustMarks,
    required TResult Function(_ChangeVerdict value) changeVerdict,
    required TResult Function(_SkipQuestion value) skipQuestion,
    required TResult Function(_FinalizeEvaluation value) finalizeEvaluation,
    required TResult Function(_ClearError value) clearError,
  }) {
    return clearError(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(_StartEvaluation value)? startEvaluation,
    TResult? Function(_NextQuestion value)? nextQuestion,
    TResult? Function(_PreviousQuestion value)? previousQuestion,
    TResult? Function(_ApproveEvaluation value)? approveEvaluation,
    TResult? Function(_AdjustMarks value)? adjustMarks,
    TResult? Function(_ChangeVerdict value)? changeVerdict,
    TResult? Function(_SkipQuestion value)? skipQuestion,
    TResult? Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult? Function(_ClearError value)? clearError,
  }) {
    return clearError?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(_StartEvaluation value)? startEvaluation,
    TResult Function(_NextQuestion value)? nextQuestion,
    TResult Function(_PreviousQuestion value)? previousQuestion,
    TResult Function(_ApproveEvaluation value)? approveEvaluation,
    TResult Function(_AdjustMarks value)? adjustMarks,
    TResult Function(_ChangeVerdict value)? changeVerdict,
    TResult Function(_SkipQuestion value)? skipQuestion,
    TResult Function(_FinalizeEvaluation value)? finalizeEvaluation,
    TResult Function(_ClearError value)? clearError,
    required TResult orElse(),
  }) {
    if (clearError != null) {
      return clearError(this);
    }
    return orElse();
  }
}

abstract class _ClearError implements EvaluationEvent {
  const factory _ClearError() = _$ClearErrorImpl;
}
