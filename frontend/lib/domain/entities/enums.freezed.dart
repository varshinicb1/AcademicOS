// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'enums.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

DifficultyDistribution _$DifficultyDistributionFromJson(
    Map<String, dynamic> json) {
  return _DifficultyDistribution.fromJson(json);
}

/// @nodoc
mixin _$DifficultyDistribution {
  double get easy => throw _privateConstructorUsedError;
  double get medium => throw _privateConstructorUsedError;
  double get hard => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $DifficultyDistributionCopyWith<DifficultyDistribution> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DifficultyDistributionCopyWith<$Res> {
  factory $DifficultyDistributionCopyWith(DifficultyDistribution value,
          $Res Function(DifficultyDistribution) then) =
      _$DifficultyDistributionCopyWithImpl<$Res, DifficultyDistribution>;
  @useResult
  $Res call({double easy, double medium, double hard});
}

/// @nodoc
class _$DifficultyDistributionCopyWithImpl<$Res,
        $Val extends DifficultyDistribution>
    implements $DifficultyDistributionCopyWith<$Res> {
  _$DifficultyDistributionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? easy = null,
    Object? medium = null,
    Object? hard = null,
  }) {
    return _then(_value.copyWith(
      easy: null == easy
          ? _value.easy
          : easy // ignore: cast_nullable_to_non_nullable
              as double,
      medium: null == medium
          ? _value.medium
          : medium // ignore: cast_nullable_to_non_nullable
              as double,
      hard: null == hard
          ? _value.hard
          : hard // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DifficultyDistributionImplCopyWith<$Res>
    implements $DifficultyDistributionCopyWith<$Res> {
  factory _$$DifficultyDistributionImplCopyWith(
          _$DifficultyDistributionImpl value,
          $Res Function(_$DifficultyDistributionImpl) then) =
      __$$DifficultyDistributionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double easy, double medium, double hard});
}

/// @nodoc
class __$$DifficultyDistributionImplCopyWithImpl<$Res>
    extends _$DifficultyDistributionCopyWithImpl<$Res,
        _$DifficultyDistributionImpl>
    implements _$$DifficultyDistributionImplCopyWith<$Res> {
  __$$DifficultyDistributionImplCopyWithImpl(
      _$DifficultyDistributionImpl _value,
      $Res Function(_$DifficultyDistributionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? easy = null,
    Object? medium = null,
    Object? hard = null,
  }) {
    return _then(_$DifficultyDistributionImpl(
      easy: null == easy
          ? _value.easy
          : easy // ignore: cast_nullable_to_non_nullable
              as double,
      medium: null == medium
          ? _value.medium
          : medium // ignore: cast_nullable_to_non_nullable
              as double,
      hard: null == hard
          ? _value.hard
          : hard // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DifficultyDistributionImpl implements _DifficultyDistribution {
  const _$DifficultyDistributionImpl(
      {required this.easy, required this.medium, required this.hard});

  factory _$DifficultyDistributionImpl.fromJson(Map<String, dynamic> json) =>
      _$$DifficultyDistributionImplFromJson(json);

  @override
  final double easy;
  @override
  final double medium;
  @override
  final double hard;

  @override
  String toString() {
    return 'DifficultyDistribution(easy: $easy, medium: $medium, hard: $hard)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DifficultyDistributionImpl &&
            (identical(other.easy, easy) || other.easy == easy) &&
            (identical(other.medium, medium) || other.medium == medium) &&
            (identical(other.hard, hard) || other.hard == hard));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, easy, medium, hard);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$DifficultyDistributionImplCopyWith<_$DifficultyDistributionImpl>
      get copyWith => __$$DifficultyDistributionImplCopyWithImpl<
          _$DifficultyDistributionImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DifficultyDistributionImplToJson(
      this,
    );
  }
}

abstract class _DifficultyDistribution implements DifficultyDistribution {
  const factory _DifficultyDistribution(
      {required final double easy,
      required final double medium,
      required final double hard}) = _$DifficultyDistributionImpl;

  factory _DifficultyDistribution.fromJson(Map<String, dynamic> json) =
      _$DifficultyDistributionImpl.fromJson;

  @override
  double get easy;
  @override
  double get medium;
  @override
  double get hard;
  @override
  @JsonKey(ignore: true)
  _$$DifficultyDistributionImplCopyWith<_$DifficultyDistributionImpl>
      get copyWith => throw _privateConstructorUsedError;
}

BloomDistribution _$BloomDistributionFromJson(Map<String, dynamic> json) {
  return _BloomDistribution.fromJson(json);
}

/// @nodoc
mixin _$BloomDistribution {
  double get remember => throw _privateConstructorUsedError;
  double get understand => throw _privateConstructorUsedError;
  double get apply => throw _privateConstructorUsedError;
  double get analyze => throw _privateConstructorUsedError;
  double get evaluate => throw _privateConstructorUsedError;
  double get create => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BloomDistributionCopyWith<BloomDistribution> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BloomDistributionCopyWith<$Res> {
  factory $BloomDistributionCopyWith(
          BloomDistribution value, $Res Function(BloomDistribution) then) =
      _$BloomDistributionCopyWithImpl<$Res, BloomDistribution>;
  @useResult
  $Res call(
      {double remember,
      double understand,
      double apply,
      double analyze,
      double evaluate,
      double create});
}

/// @nodoc
class _$BloomDistributionCopyWithImpl<$Res, $Val extends BloomDistribution>
    implements $BloomDistributionCopyWith<$Res> {
  _$BloomDistributionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? remember = null,
    Object? understand = null,
    Object? apply = null,
    Object? analyze = null,
    Object? evaluate = null,
    Object? create = null,
  }) {
    return _then(_value.copyWith(
      remember: null == remember
          ? _value.remember
          : remember // ignore: cast_nullable_to_non_nullable
              as double,
      understand: null == understand
          ? _value.understand
          : understand // ignore: cast_nullable_to_non_nullable
              as double,
      apply: null == apply
          ? _value.apply
          : apply // ignore: cast_nullable_to_non_nullable
              as double,
      analyze: null == analyze
          ? _value.analyze
          : analyze // ignore: cast_nullable_to_non_nullable
              as double,
      evaluate: null == evaluate
          ? _value.evaluate
          : evaluate // ignore: cast_nullable_to_non_nullable
              as double,
      create: null == create
          ? _value.create
          : create // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BloomDistributionImplCopyWith<$Res>
    implements $BloomDistributionCopyWith<$Res> {
  factory _$$BloomDistributionImplCopyWith(_$BloomDistributionImpl value,
          $Res Function(_$BloomDistributionImpl) then) =
      __$$BloomDistributionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double remember,
      double understand,
      double apply,
      double analyze,
      double evaluate,
      double create});
}

/// @nodoc
class __$$BloomDistributionImplCopyWithImpl<$Res>
    extends _$BloomDistributionCopyWithImpl<$Res, _$BloomDistributionImpl>
    implements _$$BloomDistributionImplCopyWith<$Res> {
  __$$BloomDistributionImplCopyWithImpl(_$BloomDistributionImpl _value,
      $Res Function(_$BloomDistributionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? remember = null,
    Object? understand = null,
    Object? apply = null,
    Object? analyze = null,
    Object? evaluate = null,
    Object? create = null,
  }) {
    return _then(_$BloomDistributionImpl(
      remember: null == remember
          ? _value.remember
          : remember // ignore: cast_nullable_to_non_nullable
              as double,
      understand: null == understand
          ? _value.understand
          : understand // ignore: cast_nullable_to_non_nullable
              as double,
      apply: null == apply
          ? _value.apply
          : apply // ignore: cast_nullable_to_non_nullable
              as double,
      analyze: null == analyze
          ? _value.analyze
          : analyze // ignore: cast_nullable_to_non_nullable
              as double,
      evaluate: null == evaluate
          ? _value.evaluate
          : evaluate // ignore: cast_nullable_to_non_nullable
              as double,
      create: null == create
          ? _value.create
          : create // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BloomDistributionImpl implements _BloomDistribution {
  const _$BloomDistributionImpl(
      {required this.remember,
      required this.understand,
      required this.apply,
      required this.analyze,
      required this.evaluate,
      required this.create});

  factory _$BloomDistributionImpl.fromJson(Map<String, dynamic> json) =>
      _$$BloomDistributionImplFromJson(json);

  @override
  final double remember;
  @override
  final double understand;
  @override
  final double apply;
  @override
  final double analyze;
  @override
  final double evaluate;
  @override
  final double create;

  @override
  String toString() {
    return 'BloomDistribution(remember: $remember, understand: $understand, apply: $apply, analyze: $analyze, evaluate: $evaluate, create: $create)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BloomDistributionImpl &&
            (identical(other.remember, remember) ||
                other.remember == remember) &&
            (identical(other.understand, understand) ||
                other.understand == understand) &&
            (identical(other.apply, apply) || other.apply == apply) &&
            (identical(other.analyze, analyze) || other.analyze == analyze) &&
            (identical(other.evaluate, evaluate) ||
                other.evaluate == evaluate) &&
            (identical(other.create, create) || other.create == create));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, remember, understand, apply, analyze, evaluate, create);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BloomDistributionImplCopyWith<_$BloomDistributionImpl> get copyWith =>
      __$$BloomDistributionImplCopyWithImpl<_$BloomDistributionImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BloomDistributionImplToJson(
      this,
    );
  }
}

abstract class _BloomDistribution implements BloomDistribution {
  const factory _BloomDistribution(
      {required final double remember,
      required final double understand,
      required final double apply,
      required final double analyze,
      required final double evaluate,
      required final double create}) = _$BloomDistributionImpl;

  factory _BloomDistribution.fromJson(Map<String, dynamic> json) =
      _$BloomDistributionImpl.fromJson;

  @override
  double get remember;
  @override
  double get understand;
  @override
  double get apply;
  @override
  double get analyze;
  @override
  double get evaluate;
  @override
  double get create;
  @override
  @JsonKey(ignore: true)
  _$$BloomDistributionImplCopyWith<_$BloomDistributionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChapterWeights _$ChapterWeightsFromJson(Map<String, dynamic> json) {
  return _ChapterWeights.fromJson(json);
}

/// @nodoc
mixin _$ChapterWeights {
  Map<String, double> get weights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChapterWeightsCopyWith<ChapterWeights> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChapterWeightsCopyWith<$Res> {
  factory $ChapterWeightsCopyWith(
          ChapterWeights value, $Res Function(ChapterWeights) then) =
      _$ChapterWeightsCopyWithImpl<$Res, ChapterWeights>;
  @useResult
  $Res call({Map<String, double> weights});
}

/// @nodoc
class _$ChapterWeightsCopyWithImpl<$Res, $Val extends ChapterWeights>
    implements $ChapterWeightsCopyWith<$Res> {
  _$ChapterWeightsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? weights = null,
  }) {
    return _then(_value.copyWith(
      weights: null == weights
          ? _value.weights
          : weights // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChapterWeightsImplCopyWith<$Res>
    implements $ChapterWeightsCopyWith<$Res> {
  factory _$$ChapterWeightsImplCopyWith(_$ChapterWeightsImpl value,
          $Res Function(_$ChapterWeightsImpl) then) =
      __$$ChapterWeightsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({Map<String, double> weights});
}

/// @nodoc
class __$$ChapterWeightsImplCopyWithImpl<$Res>
    extends _$ChapterWeightsCopyWithImpl<$Res, _$ChapterWeightsImpl>
    implements _$$ChapterWeightsImplCopyWith<$Res> {
  __$$ChapterWeightsImplCopyWithImpl(
      _$ChapterWeightsImpl _value, $Res Function(_$ChapterWeightsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? weights = null,
  }) {
    return _then(_$ChapterWeightsImpl(
      weights: null == weights
          ? _value._weights
          : weights // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChapterWeightsImpl implements _ChapterWeights {
  const _$ChapterWeightsImpl({required final Map<String, double> weights})
      : _weights = weights;

  factory _$ChapterWeightsImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChapterWeightsImplFromJson(json);

  final Map<String, double> _weights;
  @override
  Map<String, double> get weights {
    if (_weights is EqualUnmodifiableMapView) return _weights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_weights);
  }

  @override
  String toString() {
    return 'ChapterWeights(weights: $weights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChapterWeightsImpl &&
            const DeepCollectionEquality().equals(other._weights, _weights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_weights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChapterWeightsImplCopyWith<_$ChapterWeightsImpl> get copyWith =>
      __$$ChapterWeightsImplCopyWithImpl<_$ChapterWeightsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChapterWeightsImplToJson(
      this,
    );
  }
}

abstract class _ChapterWeights implements ChapterWeights {
  const factory _ChapterWeights({required final Map<String, double> weights}) =
      _$ChapterWeightsImpl;

  factory _ChapterWeights.fromJson(Map<String, dynamic> json) =
      _$ChapterWeightsImpl.fromJson;

  @override
  Map<String, double> get weights;
  @override
  @JsonKey(ignore: true)
  _$$ChapterWeightsImplCopyWith<_$ChapterWeightsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CompetencyWeights _$CompetencyWeightsFromJson(Map<String, dynamic> json) {
  return _CompetencyWeights.fromJson(json);
}

/// @nodoc
mixin _$CompetencyWeights {
  Map<String, double> get weights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CompetencyWeightsCopyWith<CompetencyWeights> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CompetencyWeightsCopyWith<$Res> {
  factory $CompetencyWeightsCopyWith(
          CompetencyWeights value, $Res Function(CompetencyWeights) then) =
      _$CompetencyWeightsCopyWithImpl<$Res, CompetencyWeights>;
  @useResult
  $Res call({Map<String, double> weights});
}

/// @nodoc
class _$CompetencyWeightsCopyWithImpl<$Res, $Val extends CompetencyWeights>
    implements $CompetencyWeightsCopyWith<$Res> {
  _$CompetencyWeightsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? weights = null,
  }) {
    return _then(_value.copyWith(
      weights: null == weights
          ? _value.weights
          : weights // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CompetencyWeightsImplCopyWith<$Res>
    implements $CompetencyWeightsCopyWith<$Res> {
  factory _$$CompetencyWeightsImplCopyWith(_$CompetencyWeightsImpl value,
          $Res Function(_$CompetencyWeightsImpl) then) =
      __$$CompetencyWeightsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({Map<String, double> weights});
}

/// @nodoc
class __$$CompetencyWeightsImplCopyWithImpl<$Res>
    extends _$CompetencyWeightsCopyWithImpl<$Res, _$CompetencyWeightsImpl>
    implements _$$CompetencyWeightsImplCopyWith<$Res> {
  __$$CompetencyWeightsImplCopyWithImpl(_$CompetencyWeightsImpl _value,
      $Res Function(_$CompetencyWeightsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? weights = null,
  }) {
    return _then(_$CompetencyWeightsImpl(
      weights: null == weights
          ? _value._weights
          : weights // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CompetencyWeightsImpl implements _CompetencyWeights {
  const _$CompetencyWeightsImpl({required final Map<String, double> weights})
      : _weights = weights;

  factory _$CompetencyWeightsImpl.fromJson(Map<String, dynamic> json) =>
      _$$CompetencyWeightsImplFromJson(json);

  final Map<String, double> _weights;
  @override
  Map<String, double> get weights {
    if (_weights is EqualUnmodifiableMapView) return _weights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_weights);
  }

  @override
  String toString() {
    return 'CompetencyWeights(weights: $weights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CompetencyWeightsImpl &&
            const DeepCollectionEquality().equals(other._weights, _weights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_weights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CompetencyWeightsImplCopyWith<_$CompetencyWeightsImpl> get copyWith =>
      __$$CompetencyWeightsImplCopyWithImpl<_$CompetencyWeightsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CompetencyWeightsImplToJson(
      this,
    );
  }
}

abstract class _CompetencyWeights implements CompetencyWeights {
  const factory _CompetencyWeights(
      {required final Map<String, double> weights}) = _$CompetencyWeightsImpl;

  factory _CompetencyWeights.fromJson(Map<String, dynamic> json) =
      _$CompetencyWeightsImpl.fromJson;

  @override
  Map<String, double> get weights;
  @override
  @JsonKey(ignore: true)
  _$$CompetencyWeightsImplCopyWith<_$CompetencyWeightsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SectionBlueprint _$SectionBlueprintFromJson(Map<String, dynamic> json) {
  return _SectionBlueprint.fromJson(json);
}

/// @nodoc
mixin _$SectionBlueprint {
  String get id => throw _privateConstructorUsedError;
  String get label => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  int get marksPerQuestion => throw _privateConstructorUsedError;
  int get questionCount => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;
  List<BloomLevel> get allowedBloomLevels => throw _privateConstructorUsedError;
  List<Difficulty> get allowedDifficulties =>
      throw _privateConstructorUsedError;
  bool get hasInternalChoice => throw _privateConstructorUsedError;
  int get internalChoiceCount => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SectionBlueprintCopyWith<SectionBlueprint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SectionBlueprintCopyWith<$Res> {
  factory $SectionBlueprintCopyWith(
          SectionBlueprint value, $Res Function(SectionBlueprint) then) =
      _$SectionBlueprintCopyWithImpl<$Res, SectionBlueprint>;
  @useResult
  $Res call(
      {String id,
      String label,
      String name,
      int marksPerQuestion,
      int questionCount,
      int totalMarks,
      List<BloomLevel> allowedBloomLevels,
      List<Difficulty> allowedDifficulties,
      bool hasInternalChoice,
      int internalChoiceCount});
}

/// @nodoc
class _$SectionBlueprintCopyWithImpl<$Res, $Val extends SectionBlueprint>
    implements $SectionBlueprintCopyWith<$Res> {
  _$SectionBlueprintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? label = null,
    Object? name = null,
    Object? marksPerQuestion = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? allowedBloomLevels = null,
    Object? allowedDifficulties = null,
    Object? hasInternalChoice = null,
    Object? internalChoiceCount = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      marksPerQuestion: null == marksPerQuestion
          ? _value.marksPerQuestion
          : marksPerQuestion // ignore: cast_nullable_to_non_nullable
              as int,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      allowedBloomLevels: null == allowedBloomLevels
          ? _value.allowedBloomLevels
          : allowedBloomLevels // ignore: cast_nullable_to_non_nullable
              as List<BloomLevel>,
      allowedDifficulties: null == allowedDifficulties
          ? _value.allowedDifficulties
          : allowedDifficulties // ignore: cast_nullable_to_non_nullable
              as List<Difficulty>,
      hasInternalChoice: null == hasInternalChoice
          ? _value.hasInternalChoice
          : hasInternalChoice // ignore: cast_nullable_to_non_nullable
              as bool,
      internalChoiceCount: null == internalChoiceCount
          ? _value.internalChoiceCount
          : internalChoiceCount // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SectionBlueprintImplCopyWith<$Res>
    implements $SectionBlueprintCopyWith<$Res> {
  factory _$$SectionBlueprintImplCopyWith(_$SectionBlueprintImpl value,
          $Res Function(_$SectionBlueprintImpl) then) =
      __$$SectionBlueprintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String label,
      String name,
      int marksPerQuestion,
      int questionCount,
      int totalMarks,
      List<BloomLevel> allowedBloomLevels,
      List<Difficulty> allowedDifficulties,
      bool hasInternalChoice,
      int internalChoiceCount});
}

/// @nodoc
class __$$SectionBlueprintImplCopyWithImpl<$Res>
    extends _$SectionBlueprintCopyWithImpl<$Res, _$SectionBlueprintImpl>
    implements _$$SectionBlueprintImplCopyWith<$Res> {
  __$$SectionBlueprintImplCopyWithImpl(_$SectionBlueprintImpl _value,
      $Res Function(_$SectionBlueprintImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? label = null,
    Object? name = null,
    Object? marksPerQuestion = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? allowedBloomLevels = null,
    Object? allowedDifficulties = null,
    Object? hasInternalChoice = null,
    Object? internalChoiceCount = null,
  }) {
    return _then(_$SectionBlueprintImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      marksPerQuestion: null == marksPerQuestion
          ? _value.marksPerQuestion
          : marksPerQuestion // ignore: cast_nullable_to_non_nullable
              as int,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      allowedBloomLevels: null == allowedBloomLevels
          ? _value._allowedBloomLevels
          : allowedBloomLevels // ignore: cast_nullable_to_non_nullable
              as List<BloomLevel>,
      allowedDifficulties: null == allowedDifficulties
          ? _value._allowedDifficulties
          : allowedDifficulties // ignore: cast_nullable_to_non_nullable
              as List<Difficulty>,
      hasInternalChoice: null == hasInternalChoice
          ? _value.hasInternalChoice
          : hasInternalChoice // ignore: cast_nullable_to_non_nullable
              as bool,
      internalChoiceCount: null == internalChoiceCount
          ? _value.internalChoiceCount
          : internalChoiceCount // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SectionBlueprintImpl implements _SectionBlueprint {
  const _$SectionBlueprintImpl(
      {required this.id,
      required this.label,
      required this.name,
      required this.marksPerQuestion,
      required this.questionCount,
      required this.totalMarks,
      required final List<BloomLevel> allowedBloomLevels,
      required final List<Difficulty> allowedDifficulties,
      this.hasInternalChoice = false,
      this.internalChoiceCount = 0})
      : _allowedBloomLevels = allowedBloomLevels,
        _allowedDifficulties = allowedDifficulties;

  factory _$SectionBlueprintImpl.fromJson(Map<String, dynamic> json) =>
      _$$SectionBlueprintImplFromJson(json);

  @override
  final String id;
  @override
  final String label;
  @override
  final String name;
  @override
  final int marksPerQuestion;
  @override
  final int questionCount;
  @override
  final int totalMarks;
  final List<BloomLevel> _allowedBloomLevels;
  @override
  List<BloomLevel> get allowedBloomLevels {
    if (_allowedBloomLevels is EqualUnmodifiableListView)
      return _allowedBloomLevels;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_allowedBloomLevels);
  }

  final List<Difficulty> _allowedDifficulties;
  @override
  List<Difficulty> get allowedDifficulties {
    if (_allowedDifficulties is EqualUnmodifiableListView)
      return _allowedDifficulties;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_allowedDifficulties);
  }

  @override
  @JsonKey()
  final bool hasInternalChoice;
  @override
  @JsonKey()
  final int internalChoiceCount;

  @override
  String toString() {
    return 'SectionBlueprint(id: $id, label: $label, name: $name, marksPerQuestion: $marksPerQuestion, questionCount: $questionCount, totalMarks: $totalMarks, allowedBloomLevels: $allowedBloomLevels, allowedDifficulties: $allowedDifficulties, hasInternalChoice: $hasInternalChoice, internalChoiceCount: $internalChoiceCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SectionBlueprintImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.marksPerQuestion, marksPerQuestion) ||
                other.marksPerQuestion == marksPerQuestion) &&
            (identical(other.questionCount, questionCount) ||
                other.questionCount == questionCount) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            const DeepCollectionEquality()
                .equals(other._allowedBloomLevels, _allowedBloomLevels) &&
            const DeepCollectionEquality()
                .equals(other._allowedDifficulties, _allowedDifficulties) &&
            (identical(other.hasInternalChoice, hasInternalChoice) ||
                other.hasInternalChoice == hasInternalChoice) &&
            (identical(other.internalChoiceCount, internalChoiceCount) ||
                other.internalChoiceCount == internalChoiceCount));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      label,
      name,
      marksPerQuestion,
      questionCount,
      totalMarks,
      const DeepCollectionEquality().hash(_allowedBloomLevels),
      const DeepCollectionEquality().hash(_allowedDifficulties),
      hasInternalChoice,
      internalChoiceCount);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SectionBlueprintImplCopyWith<_$SectionBlueprintImpl> get copyWith =>
      __$$SectionBlueprintImplCopyWithImpl<_$SectionBlueprintImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SectionBlueprintImplToJson(
      this,
    );
  }
}

abstract class _SectionBlueprint implements SectionBlueprint {
  const factory _SectionBlueprint(
      {required final String id,
      required final String label,
      required final String name,
      required final int marksPerQuestion,
      required final int questionCount,
      required final int totalMarks,
      required final List<BloomLevel> allowedBloomLevels,
      required final List<Difficulty> allowedDifficulties,
      final bool hasInternalChoice,
      final int internalChoiceCount}) = _$SectionBlueprintImpl;

  factory _SectionBlueprint.fromJson(Map<String, dynamic> json) =
      _$SectionBlueprintImpl.fromJson;

  @override
  String get id;
  @override
  String get label;
  @override
  String get name;
  @override
  int get marksPerQuestion;
  @override
  int get questionCount;
  @override
  int get totalMarks;
  @override
  List<BloomLevel> get allowedBloomLevels;
  @override
  List<Difficulty> get allowedDifficulties;
  @override
  bool get hasInternalChoice;
  @override
  int get internalChoiceCount;
  @override
  @JsonKey(ignore: true)
  _$$SectionBlueprintImplCopyWith<_$SectionBlueprintImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

Blueprint _$BlueprintFromJson(Map<String, dynamic> json) {
  return _Blueprint.fromJson(json);
}

/// @nodoc
mixin _$Blueprint {
  int get totalMarks => throw _privateConstructorUsedError;
  int get durationMinutes => throw _privateConstructorUsedError;
  DifficultyDistribution get difficulty => throw _privateConstructorUsedError;
  BloomDistribution get bloom => throw _privateConstructorUsedError;
  ChapterWeights get chapterWeights => throw _privateConstructorUsedError;
  CompetencyWeights get competencyWeights => throw _privateConstructorUsedError;
  List<SectionBlueprint> get sections => throw _privateConstructorUsedError;
  Map<String, dynamic> get metadata => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BlueprintCopyWith<Blueprint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BlueprintCopyWith<$Res> {
  factory $BlueprintCopyWith(Blueprint value, $Res Function(Blueprint) then) =
      _$BlueprintCopyWithImpl<$Res, Blueprint>;
  @useResult
  $Res call(
      {int totalMarks,
      int durationMinutes,
      DifficultyDistribution difficulty,
      BloomDistribution bloom,
      ChapterWeights chapterWeights,
      CompetencyWeights competencyWeights,
      List<SectionBlueprint> sections,
      Map<String, dynamic> metadata});

  $DifficultyDistributionCopyWith<$Res> get difficulty;
  $BloomDistributionCopyWith<$Res> get bloom;
  $ChapterWeightsCopyWith<$Res> get chapterWeights;
  $CompetencyWeightsCopyWith<$Res> get competencyWeights;
}

/// @nodoc
class _$BlueprintCopyWithImpl<$Res, $Val extends Blueprint>
    implements $BlueprintCopyWith<$Res> {
  _$BlueprintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalMarks = null,
    Object? durationMinutes = null,
    Object? difficulty = null,
    Object? bloom = null,
    Object? chapterWeights = null,
    Object? competencyWeights = null,
    Object? sections = null,
    Object? metadata = null,
  }) {
    return _then(_value.copyWith(
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as DifficultyDistribution,
      bloom: null == bloom
          ? _value.bloom
          : bloom // ignore: cast_nullable_to_non_nullable
              as BloomDistribution,
      chapterWeights: null == chapterWeights
          ? _value.chapterWeights
          : chapterWeights // ignore: cast_nullable_to_non_nullable
              as ChapterWeights,
      competencyWeights: null == competencyWeights
          ? _value.competencyWeights
          : competencyWeights // ignore: cast_nullable_to_non_nullable
              as CompetencyWeights,
      sections: null == sections
          ? _value.sections
          : sections // ignore: cast_nullable_to_non_nullable
              as List<SectionBlueprint>,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $DifficultyDistributionCopyWith<$Res> get difficulty {
    return $DifficultyDistributionCopyWith<$Res>(_value.difficulty, (value) {
      return _then(_value.copyWith(difficulty: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $BloomDistributionCopyWith<$Res> get bloom {
    return $BloomDistributionCopyWith<$Res>(_value.bloom, (value) {
      return _then(_value.copyWith(bloom: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ChapterWeightsCopyWith<$Res> get chapterWeights {
    return $ChapterWeightsCopyWith<$Res>(_value.chapterWeights, (value) {
      return _then(_value.copyWith(chapterWeights: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $CompetencyWeightsCopyWith<$Res> get competencyWeights {
    return $CompetencyWeightsCopyWith<$Res>(_value.competencyWeights, (value) {
      return _then(_value.copyWith(competencyWeights: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$BlueprintImplCopyWith<$Res>
    implements $BlueprintCopyWith<$Res> {
  factory _$$BlueprintImplCopyWith(
          _$BlueprintImpl value, $Res Function(_$BlueprintImpl) then) =
      __$$BlueprintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int totalMarks,
      int durationMinutes,
      DifficultyDistribution difficulty,
      BloomDistribution bloom,
      ChapterWeights chapterWeights,
      CompetencyWeights competencyWeights,
      List<SectionBlueprint> sections,
      Map<String, dynamic> metadata});

  @override
  $DifficultyDistributionCopyWith<$Res> get difficulty;
  @override
  $BloomDistributionCopyWith<$Res> get bloom;
  @override
  $ChapterWeightsCopyWith<$Res> get chapterWeights;
  @override
  $CompetencyWeightsCopyWith<$Res> get competencyWeights;
}

/// @nodoc
class __$$BlueprintImplCopyWithImpl<$Res>
    extends _$BlueprintCopyWithImpl<$Res, _$BlueprintImpl>
    implements _$$BlueprintImplCopyWith<$Res> {
  __$$BlueprintImplCopyWithImpl(
      _$BlueprintImpl _value, $Res Function(_$BlueprintImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalMarks = null,
    Object? durationMinutes = null,
    Object? difficulty = null,
    Object? bloom = null,
    Object? chapterWeights = null,
    Object? competencyWeights = null,
    Object? sections = null,
    Object? metadata = null,
  }) {
    return _then(_$BlueprintImpl(
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as DifficultyDistribution,
      bloom: null == bloom
          ? _value.bloom
          : bloom // ignore: cast_nullable_to_non_nullable
              as BloomDistribution,
      chapterWeights: null == chapterWeights
          ? _value.chapterWeights
          : chapterWeights // ignore: cast_nullable_to_non_nullable
              as ChapterWeights,
      competencyWeights: null == competencyWeights
          ? _value.competencyWeights
          : competencyWeights // ignore: cast_nullable_to_non_nullable
              as CompetencyWeights,
      sections: null == sections
          ? _value._sections
          : sections // ignore: cast_nullable_to_non_nullable
              as List<SectionBlueprint>,
      metadata: null == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BlueprintImpl implements _Blueprint {
  const _$BlueprintImpl(
      {required this.totalMarks,
      required this.durationMinutes,
      required this.difficulty,
      required this.bloom,
      required this.chapterWeights,
      required this.competencyWeights,
      required final List<SectionBlueprint> sections,
      final Map<String, dynamic> metadata = const {}})
      : _sections = sections,
        _metadata = metadata;

  factory _$BlueprintImpl.fromJson(Map<String, dynamic> json) =>
      _$$BlueprintImplFromJson(json);

  @override
  final int totalMarks;
  @override
  final int durationMinutes;
  @override
  final DifficultyDistribution difficulty;
  @override
  final BloomDistribution bloom;
  @override
  final ChapterWeights chapterWeights;
  @override
  final CompetencyWeights competencyWeights;
  final List<SectionBlueprint> _sections;
  @override
  List<SectionBlueprint> get sections {
    if (_sections is EqualUnmodifiableListView) return _sections;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_sections);
  }

  final Map<String, dynamic> _metadata;
  @override
  @JsonKey()
  Map<String, dynamic> get metadata {
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_metadata);
  }

  @override
  String toString() {
    return 'Blueprint(totalMarks: $totalMarks, durationMinutes: $durationMinutes, difficulty: $difficulty, bloom: $bloom, chapterWeights: $chapterWeights, competencyWeights: $competencyWeights, sections: $sections, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BlueprintImpl &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            (identical(other.durationMinutes, durationMinutes) ||
                other.durationMinutes == durationMinutes) &&
            (identical(other.difficulty, difficulty) ||
                other.difficulty == difficulty) &&
            (identical(other.bloom, bloom) || other.bloom == bloom) &&
            (identical(other.chapterWeights, chapterWeights) ||
                other.chapterWeights == chapterWeights) &&
            (identical(other.competencyWeights, competencyWeights) ||
                other.competencyWeights == competencyWeights) &&
            const DeepCollectionEquality().equals(other._sections, _sections) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalMarks,
      durationMinutes,
      difficulty,
      bloom,
      chapterWeights,
      competencyWeights,
      const DeepCollectionEquality().hash(_sections),
      const DeepCollectionEquality().hash(_metadata));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BlueprintImplCopyWith<_$BlueprintImpl> get copyWith =>
      __$$BlueprintImplCopyWithImpl<_$BlueprintImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BlueprintImplToJson(
      this,
    );
  }
}

abstract class _Blueprint implements Blueprint {
  const factory _Blueprint(
      {required final int totalMarks,
      required final int durationMinutes,
      required final DifficultyDistribution difficulty,
      required final BloomDistribution bloom,
      required final ChapterWeights chapterWeights,
      required final CompetencyWeights competencyWeights,
      required final List<SectionBlueprint> sections,
      final Map<String, dynamic> metadata}) = _$BlueprintImpl;

  factory _Blueprint.fromJson(Map<String, dynamic> json) =
      _$BlueprintImpl.fromJson;

  @override
  int get totalMarks;
  @override
  int get durationMinutes;
  @override
  DifficultyDistribution get difficulty;
  @override
  BloomDistribution get bloom;
  @override
  ChapterWeights get chapterWeights;
  @override
  CompetencyWeights get competencyWeights;
  @override
  List<SectionBlueprint> get sections;
  @override
  Map<String, dynamic> get metadata;
  @override
  @JsonKey(ignore: true)
  _$$BlueprintImplCopyWith<_$BlueprintImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

Point _$PointFromJson(Map<String, dynamic> json) {
  return _Point.fromJson(json);
}

/// @nodoc
mixin _$Point {
  double get x => throw _privateConstructorUsedError;
  double get y => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PointCopyWith<Point> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PointCopyWith<$Res> {
  factory $PointCopyWith(Point value, $Res Function(Point) then) =
      _$PointCopyWithImpl<$Res, Point>;
  @useResult
  $Res call({double x, double y});
}

/// @nodoc
class _$PointCopyWithImpl<$Res, $Val extends Point>
    implements $PointCopyWith<$Res> {
  _$PointCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? x = null,
    Object? y = null,
  }) {
    return _then(_value.copyWith(
      x: null == x
          ? _value.x
          : x // ignore: cast_nullable_to_non_nullable
              as double,
      y: null == y
          ? _value.y
          : y // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PointImplCopyWith<$Res> implements $PointCopyWith<$Res> {
  factory _$$PointImplCopyWith(
          _$PointImpl value, $Res Function(_$PointImpl) then) =
      __$$PointImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double x, double y});
}

/// @nodoc
class __$$PointImplCopyWithImpl<$Res>
    extends _$PointCopyWithImpl<$Res, _$PointImpl>
    implements _$$PointImplCopyWith<$Res> {
  __$$PointImplCopyWithImpl(
      _$PointImpl _value, $Res Function(_$PointImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? x = null,
    Object? y = null,
  }) {
    return _then(_$PointImpl(
      x: null == x
          ? _value.x
          : x // ignore: cast_nullable_to_non_nullable
              as double,
      y: null == y
          ? _value.y
          : y // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PointImpl implements _Point {
  const _$PointImpl({required this.x, required this.y});

  factory _$PointImpl.fromJson(Map<String, dynamic> json) =>
      _$$PointImplFromJson(json);

  @override
  final double x;
  @override
  final double y;

  @override
  String toString() {
    return 'Point(x: $x, y: $y)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PointImpl &&
            (identical(other.x, x) || other.x == x) &&
            (identical(other.y, y) || other.y == y));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, x, y);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PointImplCopyWith<_$PointImpl> get copyWith =>
      __$$PointImplCopyWithImpl<_$PointImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PointImplToJson(
      this,
    );
  }
}

abstract class _Point implements Point {
  const factory _Point({required final double x, required final double y}) =
      _$PointImpl;

  factory _Point.fromJson(Map<String, dynamic> json) = _$PointImpl.fromJson;

  @override
  double get x;
  @override
  double get y;
  @override
  @JsonKey(ignore: true)
  _$$PointImplCopyWith<_$PointImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
