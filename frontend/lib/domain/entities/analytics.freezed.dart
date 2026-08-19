// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'analytics.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

AssessmentAnalytics _$AssessmentAnalyticsFromJson(Map<String, dynamic> json) {
  return _AssessmentAnalytics.fromJson(json);
}

/// @nodoc
mixin _$AssessmentAnalytics {
  String get assessmentId => throw _privateConstructorUsedError;
  String get assessmentTitle => throw _privateConstructorUsedError;
  int get totalStudents => throw _privateConstructorUsedError;
  int get submittedStudents => throw _privateConstructorUsedError;
  int get evaluatedStudents => throw _privateConstructorUsedError;
  ClassPerformance get classPerformance => throw _privateConstructorUsedError;
  List<StudentPerformance> get studentPerformances =>
      throw _privateConstructorUsedError;
  List<QuestionAnalytics> get questionAnalytics =>
      throw _privateConstructorUsedError;
  List<ConceptGap> get conceptGaps => throw _privateConstructorUsedError;
  BloomAnalytics get bloomAnalytics => throw _privateConstructorUsedError;
  CompetencyAnalytics get competencyAnalytics =>
      throw _privateConstructorUsedError;
  DifficultyAnalytics get difficultyAnalytics =>
      throw _privateConstructorUsedError;
  TimeAnalytics get timeAnalytics => throw _privateConstructorUsedError;
  List<CommonError> get commonErrors => throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AssessmentAnalyticsCopyWith<AssessmentAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AssessmentAnalyticsCopyWith<$Res> {
  factory $AssessmentAnalyticsCopyWith(
          AssessmentAnalytics value, $Res Function(AssessmentAnalytics) then) =
      _$AssessmentAnalyticsCopyWithImpl<$Res, AssessmentAnalytics>;
  @useResult
  $Res call(
      {String assessmentId,
      String assessmentTitle,
      int totalStudents,
      int submittedStudents,
      int evaluatedStudents,
      ClassPerformance classPerformance,
      List<StudentPerformance> studentPerformances,
      List<QuestionAnalytics> questionAnalytics,
      List<ConceptGap> conceptGaps,
      BloomAnalytics bloomAnalytics,
      CompetencyAnalytics competencyAnalytics,
      DifficultyAnalytics difficultyAnalytics,
      TimeAnalytics timeAnalytics,
      List<CommonError> commonErrors,
      DateTime generatedAt});

  $ClassPerformanceCopyWith<$Res> get classPerformance;
  $BloomAnalyticsCopyWith<$Res> get bloomAnalytics;
  $CompetencyAnalyticsCopyWith<$Res> get competencyAnalytics;
  $DifficultyAnalyticsCopyWith<$Res> get difficultyAnalytics;
  $TimeAnalyticsCopyWith<$Res> get timeAnalytics;
}

/// @nodoc
class _$AssessmentAnalyticsCopyWithImpl<$Res, $Val extends AssessmentAnalytics>
    implements $AssessmentAnalyticsCopyWith<$Res> {
  _$AssessmentAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? assessmentTitle = null,
    Object? totalStudents = null,
    Object? submittedStudents = null,
    Object? evaluatedStudents = null,
    Object? classPerformance = null,
    Object? studentPerformances = null,
    Object? questionAnalytics = null,
    Object? conceptGaps = null,
    Object? bloomAnalytics = null,
    Object? competencyAnalytics = null,
    Object? difficultyAnalytics = null,
    Object? timeAnalytics = null,
    Object? commonErrors = null,
    Object? generatedAt = null,
  }) {
    return _then(_value.copyWith(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      submittedStudents: null == submittedStudents
          ? _value.submittedStudents
          : submittedStudents // ignore: cast_nullable_to_non_nullable
              as int,
      evaluatedStudents: null == evaluatedStudents
          ? _value.evaluatedStudents
          : evaluatedStudents // ignore: cast_nullable_to_non_nullable
              as int,
      classPerformance: null == classPerformance
          ? _value.classPerformance
          : classPerformance // ignore: cast_nullable_to_non_nullable
              as ClassPerformance,
      studentPerformances: null == studentPerformances
          ? _value.studentPerformances
          : studentPerformances // ignore: cast_nullable_to_non_nullable
              as List<StudentPerformance>,
      questionAnalytics: null == questionAnalytics
          ? _value.questionAnalytics
          : questionAnalytics // ignore: cast_nullable_to_non_nullable
              as List<QuestionAnalytics>,
      conceptGaps: null == conceptGaps
          ? _value.conceptGaps
          : conceptGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      bloomAnalytics: null == bloomAnalytics
          ? _value.bloomAnalytics
          : bloomAnalytics // ignore: cast_nullable_to_non_nullable
              as BloomAnalytics,
      competencyAnalytics: null == competencyAnalytics
          ? _value.competencyAnalytics
          : competencyAnalytics // ignore: cast_nullable_to_non_nullable
              as CompetencyAnalytics,
      difficultyAnalytics: null == difficultyAnalytics
          ? _value.difficultyAnalytics
          : difficultyAnalytics // ignore: cast_nullable_to_non_nullable
              as DifficultyAnalytics,
      timeAnalytics: null == timeAnalytics
          ? _value.timeAnalytics
          : timeAnalytics // ignore: cast_nullable_to_non_nullable
              as TimeAnalytics,
      commonErrors: null == commonErrors
          ? _value.commonErrors
          : commonErrors // ignore: cast_nullable_to_non_nullable
              as List<CommonError>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ClassPerformanceCopyWith<$Res> get classPerformance {
    return $ClassPerformanceCopyWith<$Res>(_value.classPerformance, (value) {
      return _then(_value.copyWith(classPerformance: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $BloomAnalyticsCopyWith<$Res> get bloomAnalytics {
    return $BloomAnalyticsCopyWith<$Res>(_value.bloomAnalytics, (value) {
      return _then(_value.copyWith(bloomAnalytics: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $CompetencyAnalyticsCopyWith<$Res> get competencyAnalytics {
    return $CompetencyAnalyticsCopyWith<$Res>(_value.competencyAnalytics,
        (value) {
      return _then(_value.copyWith(competencyAnalytics: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $DifficultyAnalyticsCopyWith<$Res> get difficultyAnalytics {
    return $DifficultyAnalyticsCopyWith<$Res>(_value.difficultyAnalytics,
        (value) {
      return _then(_value.copyWith(difficultyAnalytics: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $TimeAnalyticsCopyWith<$Res> get timeAnalytics {
    return $TimeAnalyticsCopyWith<$Res>(_value.timeAnalytics, (value) {
      return _then(_value.copyWith(timeAnalytics: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AssessmentAnalyticsImplCopyWith<$Res>
    implements $AssessmentAnalyticsCopyWith<$Res> {
  factory _$$AssessmentAnalyticsImplCopyWith(_$AssessmentAnalyticsImpl value,
          $Res Function(_$AssessmentAnalyticsImpl) then) =
      __$$AssessmentAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String assessmentId,
      String assessmentTitle,
      int totalStudents,
      int submittedStudents,
      int evaluatedStudents,
      ClassPerformance classPerformance,
      List<StudentPerformance> studentPerformances,
      List<QuestionAnalytics> questionAnalytics,
      List<ConceptGap> conceptGaps,
      BloomAnalytics bloomAnalytics,
      CompetencyAnalytics competencyAnalytics,
      DifficultyAnalytics difficultyAnalytics,
      TimeAnalytics timeAnalytics,
      List<CommonError> commonErrors,
      DateTime generatedAt});

  @override
  $ClassPerformanceCopyWith<$Res> get classPerformance;
  @override
  $BloomAnalyticsCopyWith<$Res> get bloomAnalytics;
  @override
  $CompetencyAnalyticsCopyWith<$Res> get competencyAnalytics;
  @override
  $DifficultyAnalyticsCopyWith<$Res> get difficultyAnalytics;
  @override
  $TimeAnalyticsCopyWith<$Res> get timeAnalytics;
}

/// @nodoc
class __$$AssessmentAnalyticsImplCopyWithImpl<$Res>
    extends _$AssessmentAnalyticsCopyWithImpl<$Res, _$AssessmentAnalyticsImpl>
    implements _$$AssessmentAnalyticsImplCopyWith<$Res> {
  __$$AssessmentAnalyticsImplCopyWithImpl(_$AssessmentAnalyticsImpl _value,
      $Res Function(_$AssessmentAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? assessmentTitle = null,
    Object? totalStudents = null,
    Object? submittedStudents = null,
    Object? evaluatedStudents = null,
    Object? classPerformance = null,
    Object? studentPerformances = null,
    Object? questionAnalytics = null,
    Object? conceptGaps = null,
    Object? bloomAnalytics = null,
    Object? competencyAnalytics = null,
    Object? difficultyAnalytics = null,
    Object? timeAnalytics = null,
    Object? commonErrors = null,
    Object? generatedAt = null,
  }) {
    return _then(_$AssessmentAnalyticsImpl(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      submittedStudents: null == submittedStudents
          ? _value.submittedStudents
          : submittedStudents // ignore: cast_nullable_to_non_nullable
              as int,
      evaluatedStudents: null == evaluatedStudents
          ? _value.evaluatedStudents
          : evaluatedStudents // ignore: cast_nullable_to_non_nullable
              as int,
      classPerformance: null == classPerformance
          ? _value.classPerformance
          : classPerformance // ignore: cast_nullable_to_non_nullable
              as ClassPerformance,
      studentPerformances: null == studentPerformances
          ? _value._studentPerformances
          : studentPerformances // ignore: cast_nullable_to_non_nullable
              as List<StudentPerformance>,
      questionAnalytics: null == questionAnalytics
          ? _value._questionAnalytics
          : questionAnalytics // ignore: cast_nullable_to_non_nullable
              as List<QuestionAnalytics>,
      conceptGaps: null == conceptGaps
          ? _value._conceptGaps
          : conceptGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      bloomAnalytics: null == bloomAnalytics
          ? _value.bloomAnalytics
          : bloomAnalytics // ignore: cast_nullable_to_non_nullable
              as BloomAnalytics,
      competencyAnalytics: null == competencyAnalytics
          ? _value.competencyAnalytics
          : competencyAnalytics // ignore: cast_nullable_to_non_nullable
              as CompetencyAnalytics,
      difficultyAnalytics: null == difficultyAnalytics
          ? _value.difficultyAnalytics
          : difficultyAnalytics // ignore: cast_nullable_to_non_nullable
              as DifficultyAnalytics,
      timeAnalytics: null == timeAnalytics
          ? _value.timeAnalytics
          : timeAnalytics // ignore: cast_nullable_to_non_nullable
              as TimeAnalytics,
      commonErrors: null == commonErrors
          ? _value._commonErrors
          : commonErrors // ignore: cast_nullable_to_non_nullable
              as List<CommonError>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AssessmentAnalyticsImpl implements _AssessmentAnalytics {
  const _$AssessmentAnalyticsImpl(
      {required this.assessmentId,
      required this.assessmentTitle,
      required this.totalStudents,
      required this.submittedStudents,
      required this.evaluatedStudents,
      required this.classPerformance,
      required final List<StudentPerformance> studentPerformances,
      required final List<QuestionAnalytics> questionAnalytics,
      required final List<ConceptGap> conceptGaps,
      required this.bloomAnalytics,
      required this.competencyAnalytics,
      required this.difficultyAnalytics,
      required this.timeAnalytics,
      required final List<CommonError> commonErrors,
      required this.generatedAt})
      : _studentPerformances = studentPerformances,
        _questionAnalytics = questionAnalytics,
        _conceptGaps = conceptGaps,
        _commonErrors = commonErrors;

  factory _$AssessmentAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$AssessmentAnalyticsImplFromJson(json);

  @override
  final String assessmentId;
  @override
  final String assessmentTitle;
  @override
  final int totalStudents;
  @override
  final int submittedStudents;
  @override
  final int evaluatedStudents;
  @override
  final ClassPerformance classPerformance;
  final List<StudentPerformance> _studentPerformances;
  @override
  List<StudentPerformance> get studentPerformances {
    if (_studentPerformances is EqualUnmodifiableListView)
      return _studentPerformances;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_studentPerformances);
  }

  final List<QuestionAnalytics> _questionAnalytics;
  @override
  List<QuestionAnalytics> get questionAnalytics {
    if (_questionAnalytics is EqualUnmodifiableListView)
      return _questionAnalytics;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questionAnalytics);
  }

  final List<ConceptGap> _conceptGaps;
  @override
  List<ConceptGap> get conceptGaps {
    if (_conceptGaps is EqualUnmodifiableListView) return _conceptGaps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_conceptGaps);
  }

  @override
  final BloomAnalytics bloomAnalytics;
  @override
  final CompetencyAnalytics competencyAnalytics;
  @override
  final DifficultyAnalytics difficultyAnalytics;
  @override
  final TimeAnalytics timeAnalytics;
  final List<CommonError> _commonErrors;
  @override
  List<CommonError> get commonErrors {
    if (_commonErrors is EqualUnmodifiableListView) return _commonErrors;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_commonErrors);
  }

  @override
  final DateTime generatedAt;

  @override
  String toString() {
    return 'AssessmentAnalytics(assessmentId: $assessmentId, assessmentTitle: $assessmentTitle, totalStudents: $totalStudents, submittedStudents: $submittedStudents, evaluatedStudents: $evaluatedStudents, classPerformance: $classPerformance, studentPerformances: $studentPerformances, questionAnalytics: $questionAnalytics, conceptGaps: $conceptGaps, bloomAnalytics: $bloomAnalytics, competencyAnalytics: $competencyAnalytics, difficultyAnalytics: $difficultyAnalytics, timeAnalytics: $timeAnalytics, commonErrors: $commonErrors, generatedAt: $generatedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AssessmentAnalyticsImpl &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.assessmentTitle, assessmentTitle) ||
                other.assessmentTitle == assessmentTitle) &&
            (identical(other.totalStudents, totalStudents) ||
                other.totalStudents == totalStudents) &&
            (identical(other.submittedStudents, submittedStudents) ||
                other.submittedStudents == submittedStudents) &&
            (identical(other.evaluatedStudents, evaluatedStudents) ||
                other.evaluatedStudents == evaluatedStudents) &&
            (identical(other.classPerformance, classPerformance) ||
                other.classPerformance == classPerformance) &&
            const DeepCollectionEquality()
                .equals(other._studentPerformances, _studentPerformances) &&
            const DeepCollectionEquality()
                .equals(other._questionAnalytics, _questionAnalytics) &&
            const DeepCollectionEquality()
                .equals(other._conceptGaps, _conceptGaps) &&
            (identical(other.bloomAnalytics, bloomAnalytics) ||
                other.bloomAnalytics == bloomAnalytics) &&
            (identical(other.competencyAnalytics, competencyAnalytics) ||
                other.competencyAnalytics == competencyAnalytics) &&
            (identical(other.difficultyAnalytics, difficultyAnalytics) ||
                other.difficultyAnalytics == difficultyAnalytics) &&
            (identical(other.timeAnalytics, timeAnalytics) ||
                other.timeAnalytics == timeAnalytics) &&
            const DeepCollectionEquality()
                .equals(other._commonErrors, _commonErrors) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      assessmentId,
      assessmentTitle,
      totalStudents,
      submittedStudents,
      evaluatedStudents,
      classPerformance,
      const DeepCollectionEquality().hash(_studentPerformances),
      const DeepCollectionEquality().hash(_questionAnalytics),
      const DeepCollectionEquality().hash(_conceptGaps),
      bloomAnalytics,
      competencyAnalytics,
      difficultyAnalytics,
      timeAnalytics,
      const DeepCollectionEquality().hash(_commonErrors),
      generatedAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AssessmentAnalyticsImplCopyWith<_$AssessmentAnalyticsImpl> get copyWith =>
      __$$AssessmentAnalyticsImplCopyWithImpl<_$AssessmentAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AssessmentAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _AssessmentAnalytics implements AssessmentAnalytics {
  const factory _AssessmentAnalytics(
      {required final String assessmentId,
      required final String assessmentTitle,
      required final int totalStudents,
      required final int submittedStudents,
      required final int evaluatedStudents,
      required final ClassPerformance classPerformance,
      required final List<StudentPerformance> studentPerformances,
      required final List<QuestionAnalytics> questionAnalytics,
      required final List<ConceptGap> conceptGaps,
      required final BloomAnalytics bloomAnalytics,
      required final CompetencyAnalytics competencyAnalytics,
      required final DifficultyAnalytics difficultyAnalytics,
      required final TimeAnalytics timeAnalytics,
      required final List<CommonError> commonErrors,
      required final DateTime generatedAt}) = _$AssessmentAnalyticsImpl;

  factory _AssessmentAnalytics.fromJson(Map<String, dynamic> json) =
      _$AssessmentAnalyticsImpl.fromJson;

  @override
  String get assessmentId;
  @override
  String get assessmentTitle;
  @override
  int get totalStudents;
  @override
  int get submittedStudents;
  @override
  int get evaluatedStudents;
  @override
  ClassPerformance get classPerformance;
  @override
  List<StudentPerformance> get studentPerformances;
  @override
  List<QuestionAnalytics> get questionAnalytics;
  @override
  List<ConceptGap> get conceptGaps;
  @override
  BloomAnalytics get bloomAnalytics;
  @override
  CompetencyAnalytics get competencyAnalytics;
  @override
  DifficultyAnalytics get difficultyAnalytics;
  @override
  TimeAnalytics get timeAnalytics;
  @override
  List<CommonError> get commonErrors;
  @override
  DateTime get generatedAt;
  @override
  @JsonKey(ignore: true)
  _$$AssessmentAnalyticsImplCopyWith<_$AssessmentAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ClassPerformance _$ClassPerformanceFromJson(Map<String, dynamic> json) {
  return _ClassPerformance.fromJson(json);
}

/// @nodoc
mixin _$ClassPerformance {
  double get averageScore => throw _privateConstructorUsedError;
  double get medianScore => throw _privateConstructorUsedError;
  double get standardDeviation => throw _privateConstructorUsedError;
  double get passRate => throw _privateConstructorUsedError;
  double get distinctionRate => throw _privateConstructorUsedError;
  Map<String, int> get gradeDistribution => throw _privateConstructorUsedError;
  int get highestScore => throw _privateConstructorUsedError;
  int get lowestScore => throw _privateConstructorUsedError;
  double get reliabilityCoefficient => throw _privateConstructorUsedError;
  double get standardError => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ClassPerformanceCopyWith<ClassPerformance> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ClassPerformanceCopyWith<$Res> {
  factory $ClassPerformanceCopyWith(
          ClassPerformance value, $Res Function(ClassPerformance) then) =
      _$ClassPerformanceCopyWithImpl<$Res, ClassPerformance>;
  @useResult
  $Res call(
      {double averageScore,
      double medianScore,
      double standardDeviation,
      double passRate,
      double distinctionRate,
      Map<String, int> gradeDistribution,
      int highestScore,
      int lowestScore,
      double reliabilityCoefficient,
      double standardError});
}

/// @nodoc
class _$ClassPerformanceCopyWithImpl<$Res, $Val extends ClassPerformance>
    implements $ClassPerformanceCopyWith<$Res> {
  _$ClassPerformanceCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? averageScore = null,
    Object? medianScore = null,
    Object? standardDeviation = null,
    Object? passRate = null,
    Object? distinctionRate = null,
    Object? gradeDistribution = null,
    Object? highestScore = null,
    Object? lowestScore = null,
    Object? reliabilityCoefficient = null,
    Object? standardError = null,
  }) {
    return _then(_value.copyWith(
      averageScore: null == averageScore
          ? _value.averageScore
          : averageScore // ignore: cast_nullable_to_non_nullable
              as double,
      medianScore: null == medianScore
          ? _value.medianScore
          : medianScore // ignore: cast_nullable_to_non_nullable
              as double,
      standardDeviation: null == standardDeviation
          ? _value.standardDeviation
          : standardDeviation // ignore: cast_nullable_to_non_nullable
              as double,
      passRate: null == passRate
          ? _value.passRate
          : passRate // ignore: cast_nullable_to_non_nullable
              as double,
      distinctionRate: null == distinctionRate
          ? _value.distinctionRate
          : distinctionRate // ignore: cast_nullable_to_non_nullable
              as double,
      gradeDistribution: null == gradeDistribution
          ? _value.gradeDistribution
          : gradeDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      highestScore: null == highestScore
          ? _value.highestScore
          : highestScore // ignore: cast_nullable_to_non_nullable
              as int,
      lowestScore: null == lowestScore
          ? _value.lowestScore
          : lowestScore // ignore: cast_nullable_to_non_nullable
              as int,
      reliabilityCoefficient: null == reliabilityCoefficient
          ? _value.reliabilityCoefficient
          : reliabilityCoefficient // ignore: cast_nullable_to_non_nullable
              as double,
      standardError: null == standardError
          ? _value.standardError
          : standardError // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ClassPerformanceImplCopyWith<$Res>
    implements $ClassPerformanceCopyWith<$Res> {
  factory _$$ClassPerformanceImplCopyWith(_$ClassPerformanceImpl value,
          $Res Function(_$ClassPerformanceImpl) then) =
      __$$ClassPerformanceImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double averageScore,
      double medianScore,
      double standardDeviation,
      double passRate,
      double distinctionRate,
      Map<String, int> gradeDistribution,
      int highestScore,
      int lowestScore,
      double reliabilityCoefficient,
      double standardError});
}

/// @nodoc
class __$$ClassPerformanceImplCopyWithImpl<$Res>
    extends _$ClassPerformanceCopyWithImpl<$Res, _$ClassPerformanceImpl>
    implements _$$ClassPerformanceImplCopyWith<$Res> {
  __$$ClassPerformanceImplCopyWithImpl(_$ClassPerformanceImpl _value,
      $Res Function(_$ClassPerformanceImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? averageScore = null,
    Object? medianScore = null,
    Object? standardDeviation = null,
    Object? passRate = null,
    Object? distinctionRate = null,
    Object? gradeDistribution = null,
    Object? highestScore = null,
    Object? lowestScore = null,
    Object? reliabilityCoefficient = null,
    Object? standardError = null,
  }) {
    return _then(_$ClassPerformanceImpl(
      averageScore: null == averageScore
          ? _value.averageScore
          : averageScore // ignore: cast_nullable_to_non_nullable
              as double,
      medianScore: null == medianScore
          ? _value.medianScore
          : medianScore // ignore: cast_nullable_to_non_nullable
              as double,
      standardDeviation: null == standardDeviation
          ? _value.standardDeviation
          : standardDeviation // ignore: cast_nullable_to_non_nullable
              as double,
      passRate: null == passRate
          ? _value.passRate
          : passRate // ignore: cast_nullable_to_non_nullable
              as double,
      distinctionRate: null == distinctionRate
          ? _value.distinctionRate
          : distinctionRate // ignore: cast_nullable_to_non_nullable
              as double,
      gradeDistribution: null == gradeDistribution
          ? _value._gradeDistribution
          : gradeDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      highestScore: null == highestScore
          ? _value.highestScore
          : highestScore // ignore: cast_nullable_to_non_nullable
              as int,
      lowestScore: null == lowestScore
          ? _value.lowestScore
          : lowestScore // ignore: cast_nullable_to_non_nullable
              as int,
      reliabilityCoefficient: null == reliabilityCoefficient
          ? _value.reliabilityCoefficient
          : reliabilityCoefficient // ignore: cast_nullable_to_non_nullable
              as double,
      standardError: null == standardError
          ? _value.standardError
          : standardError // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ClassPerformanceImpl implements _ClassPerformance {
  const _$ClassPerformanceImpl(
      {required this.averageScore,
      required this.medianScore,
      required this.standardDeviation,
      required this.passRate,
      required this.distinctionRate,
      required final Map<String, int> gradeDistribution,
      required this.highestScore,
      required this.lowestScore,
      required this.reliabilityCoefficient,
      required this.standardError})
      : _gradeDistribution = gradeDistribution;

  factory _$ClassPerformanceImpl.fromJson(Map<String, dynamic> json) =>
      _$$ClassPerformanceImplFromJson(json);

  @override
  final double averageScore;
  @override
  final double medianScore;
  @override
  final double standardDeviation;
  @override
  final double passRate;
  @override
  final double distinctionRate;
  final Map<String, int> _gradeDistribution;
  @override
  Map<String, int> get gradeDistribution {
    if (_gradeDistribution is EqualUnmodifiableMapView)
      return _gradeDistribution;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_gradeDistribution);
  }

  @override
  final int highestScore;
  @override
  final int lowestScore;
  @override
  final double reliabilityCoefficient;
  @override
  final double standardError;

  @override
  String toString() {
    return 'ClassPerformance(averageScore: $averageScore, medianScore: $medianScore, standardDeviation: $standardDeviation, passRate: $passRate, distinctionRate: $distinctionRate, gradeDistribution: $gradeDistribution, highestScore: $highestScore, lowestScore: $lowestScore, reliabilityCoefficient: $reliabilityCoefficient, standardError: $standardError)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ClassPerformanceImpl &&
            (identical(other.averageScore, averageScore) ||
                other.averageScore == averageScore) &&
            (identical(other.medianScore, medianScore) ||
                other.medianScore == medianScore) &&
            (identical(other.standardDeviation, standardDeviation) ||
                other.standardDeviation == standardDeviation) &&
            (identical(other.passRate, passRate) ||
                other.passRate == passRate) &&
            (identical(other.distinctionRate, distinctionRate) ||
                other.distinctionRate == distinctionRate) &&
            const DeepCollectionEquality()
                .equals(other._gradeDistribution, _gradeDistribution) &&
            (identical(other.highestScore, highestScore) ||
                other.highestScore == highestScore) &&
            (identical(other.lowestScore, lowestScore) ||
                other.lowestScore == lowestScore) &&
            (identical(other.reliabilityCoefficient, reliabilityCoefficient) ||
                other.reliabilityCoefficient == reliabilityCoefficient) &&
            (identical(other.standardError, standardError) ||
                other.standardError == standardError));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      averageScore,
      medianScore,
      standardDeviation,
      passRate,
      distinctionRate,
      const DeepCollectionEquality().hash(_gradeDistribution),
      highestScore,
      lowestScore,
      reliabilityCoefficient,
      standardError);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ClassPerformanceImplCopyWith<_$ClassPerformanceImpl> get copyWith =>
      __$$ClassPerformanceImplCopyWithImpl<_$ClassPerformanceImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ClassPerformanceImplToJson(
      this,
    );
  }
}

abstract class _ClassPerformance implements ClassPerformance {
  const factory _ClassPerformance(
      {required final double averageScore,
      required final double medianScore,
      required final double standardDeviation,
      required final double passRate,
      required final double distinctionRate,
      required final Map<String, int> gradeDistribution,
      required final int highestScore,
      required final int lowestScore,
      required final double reliabilityCoefficient,
      required final double standardError}) = _$ClassPerformanceImpl;

  factory _ClassPerformance.fromJson(Map<String, dynamic> json) =
      _$ClassPerformanceImpl.fromJson;

  @override
  double get averageScore;
  @override
  double get medianScore;
  @override
  double get standardDeviation;
  @override
  double get passRate;
  @override
  double get distinctionRate;
  @override
  Map<String, int> get gradeDistribution;
  @override
  int get highestScore;
  @override
  int get lowestScore;
  @override
  double get reliabilityCoefficient;
  @override
  double get standardError;
  @override
  @JsonKey(ignore: true)
  _$$ClassPerformanceImplCopyWith<_$ClassPerformanceImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

StudentPerformance _$StudentPerformanceFromJson(Map<String, dynamic> json) {
  return _StudentPerformance.fromJson(json);
}

/// @nodoc
mixin _$StudentPerformance {
  String get studentId => throw _privateConstructorUsedError;
  String get studentName => throw _privateConstructorUsedError;
  String get rollNumber => throw _privateConstructorUsedError;
  int get totalScore => throw _privateConstructorUsedError;
  int get maxScore => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  String get grade => throw _privateConstructorUsedError;
  int get rank => throw _privateConstructorUsedError;
  double get percentile => throw _privateConstructorUsedError;
  List<SectionScore> get sectionScores => throw _privateConstructorUsedError;
  Map<String, double> get conceptScores => throw _privateConstructorUsedError;
  List<String> get strengths => throw _privateConstructorUsedError;
  List<String> get weaknesses => throw _privateConstructorUsedError;
  List<String> get carelessErrors => throw _privateConstructorUsedError;
  String get recommendation => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $StudentPerformanceCopyWith<StudentPerformance> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StudentPerformanceCopyWith<$Res> {
  factory $StudentPerformanceCopyWith(
          StudentPerformance value, $Res Function(StudentPerformance) then) =
      _$StudentPerformanceCopyWithImpl<$Res, StudentPerformance>;
  @useResult
  $Res call(
      {String studentId,
      String studentName,
      String rollNumber,
      int totalScore,
      int maxScore,
      double percentage,
      String grade,
      int rank,
      double percentile,
      List<SectionScore> sectionScores,
      Map<String, double> conceptScores,
      List<String> strengths,
      List<String> weaknesses,
      List<String> carelessErrors,
      String recommendation});
}

/// @nodoc
class _$StudentPerformanceCopyWithImpl<$Res, $Val extends StudentPerformance>
    implements $StudentPerformanceCopyWith<$Res> {
  _$StudentPerformanceCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? totalScore = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? grade = null,
    Object? rank = null,
    Object? percentile = null,
    Object? sectionScores = null,
    Object? conceptScores = null,
    Object? strengths = null,
    Object? weaknesses = null,
    Object? carelessErrors = null,
    Object? recommendation = null,
  }) {
    return _then(_value.copyWith(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      rollNumber: null == rollNumber
          ? _value.rollNumber
          : rollNumber // ignore: cast_nullable_to_non_nullable
              as String,
      totalScore: null == totalScore
          ? _value.totalScore
          : totalScore // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      rank: null == rank
          ? _value.rank
          : rank // ignore: cast_nullable_to_non_nullable
              as int,
      percentile: null == percentile
          ? _value.percentile
          : percentile // ignore: cast_nullable_to_non_nullable
              as double,
      sectionScores: null == sectionScores
          ? _value.sectionScores
          : sectionScores // ignore: cast_nullable_to_non_nullable
              as List<SectionScore>,
      conceptScores: null == conceptScores
          ? _value.conceptScores
          : conceptScores // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      strengths: null == strengths
          ? _value.strengths
          : strengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      weaknesses: null == weaknesses
          ? _value.weaknesses
          : weaknesses // ignore: cast_nullable_to_non_nullable
              as List<String>,
      carelessErrors: null == carelessErrors
          ? _value.carelessErrors
          : carelessErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      recommendation: null == recommendation
          ? _value.recommendation
          : recommendation // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$StudentPerformanceImplCopyWith<$Res>
    implements $StudentPerformanceCopyWith<$Res> {
  factory _$$StudentPerformanceImplCopyWith(_$StudentPerformanceImpl value,
          $Res Function(_$StudentPerformanceImpl) then) =
      __$$StudentPerformanceImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String studentId,
      String studentName,
      String rollNumber,
      int totalScore,
      int maxScore,
      double percentage,
      String grade,
      int rank,
      double percentile,
      List<SectionScore> sectionScores,
      Map<String, double> conceptScores,
      List<String> strengths,
      List<String> weaknesses,
      List<String> carelessErrors,
      String recommendation});
}

/// @nodoc
class __$$StudentPerformanceImplCopyWithImpl<$Res>
    extends _$StudentPerformanceCopyWithImpl<$Res, _$StudentPerformanceImpl>
    implements _$$StudentPerformanceImplCopyWith<$Res> {
  __$$StudentPerformanceImplCopyWithImpl(_$StudentPerformanceImpl _value,
      $Res Function(_$StudentPerformanceImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? totalScore = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? grade = null,
    Object? rank = null,
    Object? percentile = null,
    Object? sectionScores = null,
    Object? conceptScores = null,
    Object? strengths = null,
    Object? weaknesses = null,
    Object? carelessErrors = null,
    Object? recommendation = null,
  }) {
    return _then(_$StudentPerformanceImpl(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      rollNumber: null == rollNumber
          ? _value.rollNumber
          : rollNumber // ignore: cast_nullable_to_non_nullable
              as String,
      totalScore: null == totalScore
          ? _value.totalScore
          : totalScore // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      rank: null == rank
          ? _value.rank
          : rank // ignore: cast_nullable_to_non_nullable
              as int,
      percentile: null == percentile
          ? _value.percentile
          : percentile // ignore: cast_nullable_to_non_nullable
              as double,
      sectionScores: null == sectionScores
          ? _value._sectionScores
          : sectionScores // ignore: cast_nullable_to_non_nullable
              as List<SectionScore>,
      conceptScores: null == conceptScores
          ? _value._conceptScores
          : conceptScores // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      strengths: null == strengths
          ? _value._strengths
          : strengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      weaknesses: null == weaknesses
          ? _value._weaknesses
          : weaknesses // ignore: cast_nullable_to_non_nullable
              as List<String>,
      carelessErrors: null == carelessErrors
          ? _value._carelessErrors
          : carelessErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      recommendation: null == recommendation
          ? _value.recommendation
          : recommendation // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StudentPerformanceImpl implements _StudentPerformance {
  const _$StudentPerformanceImpl(
      {required this.studentId,
      required this.studentName,
      required this.rollNumber,
      required this.totalScore,
      required this.maxScore,
      required this.percentage,
      required this.grade,
      required this.rank,
      required this.percentile,
      required final List<SectionScore> sectionScores,
      required final Map<String, double> conceptScores,
      required final List<String> strengths,
      required final List<String> weaknesses,
      required final List<String> carelessErrors,
      required this.recommendation})
      : _sectionScores = sectionScores,
        _conceptScores = conceptScores,
        _strengths = strengths,
        _weaknesses = weaknesses,
        _carelessErrors = carelessErrors;

  factory _$StudentPerformanceImpl.fromJson(Map<String, dynamic> json) =>
      _$$StudentPerformanceImplFromJson(json);

  @override
  final String studentId;
  @override
  final String studentName;
  @override
  final String rollNumber;
  @override
  final int totalScore;
  @override
  final int maxScore;
  @override
  final double percentage;
  @override
  final String grade;
  @override
  final int rank;
  @override
  final double percentile;
  final List<SectionScore> _sectionScores;
  @override
  List<SectionScore> get sectionScores {
    if (_sectionScores is EqualUnmodifiableListView) return _sectionScores;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_sectionScores);
  }

  final Map<String, double> _conceptScores;
  @override
  Map<String, double> get conceptScores {
    if (_conceptScores is EqualUnmodifiableMapView) return _conceptScores;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_conceptScores);
  }

  final List<String> _strengths;
  @override
  List<String> get strengths {
    if (_strengths is EqualUnmodifiableListView) return _strengths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_strengths);
  }

  final List<String> _weaknesses;
  @override
  List<String> get weaknesses {
    if (_weaknesses is EqualUnmodifiableListView) return _weaknesses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_weaknesses);
  }

  final List<String> _carelessErrors;
  @override
  List<String> get carelessErrors {
    if (_carelessErrors is EqualUnmodifiableListView) return _carelessErrors;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_carelessErrors);
  }

  @override
  final String recommendation;

  @override
  String toString() {
    return 'StudentPerformance(studentId: $studentId, studentName: $studentName, rollNumber: $rollNumber, totalScore: $totalScore, maxScore: $maxScore, percentage: $percentage, grade: $grade, rank: $rank, percentile: $percentile, sectionScores: $sectionScores, conceptScores: $conceptScores, strengths: $strengths, weaknesses: $weaknesses, carelessErrors: $carelessErrors, recommendation: $recommendation)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StudentPerformanceImpl &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.studentName, studentName) ||
                other.studentName == studentName) &&
            (identical(other.rollNumber, rollNumber) ||
                other.rollNumber == rollNumber) &&
            (identical(other.totalScore, totalScore) ||
                other.totalScore == totalScore) &&
            (identical(other.maxScore, maxScore) ||
                other.maxScore == maxScore) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.rank, rank) || other.rank == rank) &&
            (identical(other.percentile, percentile) ||
                other.percentile == percentile) &&
            const DeepCollectionEquality()
                .equals(other._sectionScores, _sectionScores) &&
            const DeepCollectionEquality()
                .equals(other._conceptScores, _conceptScores) &&
            const DeepCollectionEquality()
                .equals(other._strengths, _strengths) &&
            const DeepCollectionEquality()
                .equals(other._weaknesses, _weaknesses) &&
            const DeepCollectionEquality()
                .equals(other._carelessErrors, _carelessErrors) &&
            (identical(other.recommendation, recommendation) ||
                other.recommendation == recommendation));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      studentId,
      studentName,
      rollNumber,
      totalScore,
      maxScore,
      percentage,
      grade,
      rank,
      percentile,
      const DeepCollectionEquality().hash(_sectionScores),
      const DeepCollectionEquality().hash(_conceptScores),
      const DeepCollectionEquality().hash(_strengths),
      const DeepCollectionEquality().hash(_weaknesses),
      const DeepCollectionEquality().hash(_carelessErrors),
      recommendation);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$StudentPerformanceImplCopyWith<_$StudentPerformanceImpl> get copyWith =>
      __$$StudentPerformanceImplCopyWithImpl<_$StudentPerformanceImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StudentPerformanceImplToJson(
      this,
    );
  }
}

abstract class _StudentPerformance implements StudentPerformance {
  const factory _StudentPerformance(
      {required final String studentId,
      required final String studentName,
      required final String rollNumber,
      required final int totalScore,
      required final int maxScore,
      required final double percentage,
      required final String grade,
      required final int rank,
      required final double percentile,
      required final List<SectionScore> sectionScores,
      required final Map<String, double> conceptScores,
      required final List<String> strengths,
      required final List<String> weaknesses,
      required final List<String> carelessErrors,
      required final String recommendation}) = _$StudentPerformanceImpl;

  factory _StudentPerformance.fromJson(Map<String, dynamic> json) =
      _$StudentPerformanceImpl.fromJson;

  @override
  String get studentId;
  @override
  String get studentName;
  @override
  String get rollNumber;
  @override
  int get totalScore;
  @override
  int get maxScore;
  @override
  double get percentage;
  @override
  String get grade;
  @override
  int get rank;
  @override
  double get percentile;
  @override
  List<SectionScore> get sectionScores;
  @override
  Map<String, double> get conceptScores;
  @override
  List<String> get strengths;
  @override
  List<String> get weaknesses;
  @override
  List<String> get carelessErrors;
  @override
  String get recommendation;
  @override
  @JsonKey(ignore: true)
  _$$StudentPerformanceImplCopyWith<_$StudentPerformanceImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SectionScore _$SectionScoreFromJson(Map<String, dynamic> json) {
  return _SectionScore.fromJson(json);
}

/// @nodoc
mixin _$SectionScore {
  String get sectionId => throw _privateConstructorUsedError;
  String get sectionLabel => throw _privateConstructorUsedError;
  int get score => throw _privateConstructorUsedError;
  int get maxScore => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SectionScoreCopyWith<SectionScore> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SectionScoreCopyWith<$Res> {
  factory $SectionScoreCopyWith(
          SectionScore value, $Res Function(SectionScore) then) =
      _$SectionScoreCopyWithImpl<$Res, SectionScore>;
  @useResult
  $Res call(
      {String sectionId,
      String sectionLabel,
      int score,
      int maxScore,
      double percentage});
}

/// @nodoc
class _$SectionScoreCopyWithImpl<$Res, $Val extends SectionScore>
    implements $SectionScoreCopyWith<$Res> {
  _$SectionScoreCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sectionId = null,
    Object? sectionLabel = null,
    Object? score = null,
    Object? maxScore = null,
    Object? percentage = null,
  }) {
    return _then(_value.copyWith(
      sectionId: null == sectionId
          ? _value.sectionId
          : sectionId // ignore: cast_nullable_to_non_nullable
              as String,
      sectionLabel: null == sectionLabel
          ? _value.sectionLabel
          : sectionLabel // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SectionScoreImplCopyWith<$Res>
    implements $SectionScoreCopyWith<$Res> {
  factory _$$SectionScoreImplCopyWith(
          _$SectionScoreImpl value, $Res Function(_$SectionScoreImpl) then) =
      __$$SectionScoreImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String sectionId,
      String sectionLabel,
      int score,
      int maxScore,
      double percentage});
}

/// @nodoc
class __$$SectionScoreImplCopyWithImpl<$Res>
    extends _$SectionScoreCopyWithImpl<$Res, _$SectionScoreImpl>
    implements _$$SectionScoreImplCopyWith<$Res> {
  __$$SectionScoreImplCopyWithImpl(
      _$SectionScoreImpl _value, $Res Function(_$SectionScoreImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sectionId = null,
    Object? sectionLabel = null,
    Object? score = null,
    Object? maxScore = null,
    Object? percentage = null,
  }) {
    return _then(_$SectionScoreImpl(
      sectionId: null == sectionId
          ? _value.sectionId
          : sectionId // ignore: cast_nullable_to_non_nullable
              as String,
      sectionLabel: null == sectionLabel
          ? _value.sectionLabel
          : sectionLabel // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SectionScoreImpl implements _SectionScore {
  const _$SectionScoreImpl(
      {required this.sectionId,
      required this.sectionLabel,
      required this.score,
      required this.maxScore,
      required this.percentage});

  factory _$SectionScoreImpl.fromJson(Map<String, dynamic> json) =>
      _$$SectionScoreImplFromJson(json);

  @override
  final String sectionId;
  @override
  final String sectionLabel;
  @override
  final int score;
  @override
  final int maxScore;
  @override
  final double percentage;

  @override
  String toString() {
    return 'SectionScore(sectionId: $sectionId, sectionLabel: $sectionLabel, score: $score, maxScore: $maxScore, percentage: $percentage)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SectionScoreImpl &&
            (identical(other.sectionId, sectionId) ||
                other.sectionId == sectionId) &&
            (identical(other.sectionLabel, sectionLabel) ||
                other.sectionLabel == sectionLabel) &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.maxScore, maxScore) ||
                other.maxScore == maxScore) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, sectionId, sectionLabel, score, maxScore, percentage);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SectionScoreImplCopyWith<_$SectionScoreImpl> get copyWith =>
      __$$SectionScoreImplCopyWithImpl<_$SectionScoreImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SectionScoreImplToJson(
      this,
    );
  }
}

abstract class _SectionScore implements SectionScore {
  const factory _SectionScore(
      {required final String sectionId,
      required final String sectionLabel,
      required final int score,
      required final int maxScore,
      required final double percentage}) = _$SectionScoreImpl;

  factory _SectionScore.fromJson(Map<String, dynamic> json) =
      _$SectionScoreImpl.fromJson;

  @override
  String get sectionId;
  @override
  String get sectionLabel;
  @override
  int get score;
  @override
  int get maxScore;
  @override
  double get percentage;
  @override
  @JsonKey(ignore: true)
  _$$SectionScoreImplCopyWith<_$SectionScoreImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionAnalytics _$QuestionAnalyticsFromJson(Map<String, dynamic> json) {
  return _QuestionAnalytics.fromJson(json);
}

/// @nodoc
mixin _$QuestionAnalytics {
  String get questionId => throw _privateConstructorUsedError;
  int get questionNumber => throw _privateConstructorUsedError;
  String get sectionLabel => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  double get averageMarks => throw _privateConstructorUsedError;
  double get difficultyIndex => throw _privateConstructorUsedError;
  double get discriminationIndex => throw _privateConstructorUsedError;
  int get attemptedCount => throw _privateConstructorUsedError;
  int get correctCount => throw _privateConstructorUsedError;
  int get partialCount => throw _privateConstructorUsedError;
  int get blankCount => throw _privateConstructorUsedError;
  double get avgTimeSeconds => throw _privateConstructorUsedError;
  List<String> get commonWrongAnswers => throw _privateConstructorUsedError;
  Map<String, int> get optionDistribution => throw _privateConstructorUsedError;
  QuestionQualityFlags get flags => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionAnalyticsCopyWith<QuestionAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionAnalyticsCopyWith<$Res> {
  factory $QuestionAnalyticsCopyWith(
          QuestionAnalytics value, $Res Function(QuestionAnalytics) then) =
      _$QuestionAnalyticsCopyWithImpl<$Res, QuestionAnalytics>;
  @useResult
  $Res call(
      {String questionId,
      int questionNumber,
      String sectionLabel,
      int maxMarks,
      double averageMarks,
      double difficultyIndex,
      double discriminationIndex,
      int attemptedCount,
      int correctCount,
      int partialCount,
      int blankCount,
      double avgTimeSeconds,
      List<String> commonWrongAnswers,
      Map<String, int> optionDistribution,
      QuestionQualityFlags flags});

  $QuestionQualityFlagsCopyWith<$Res> get flags;
}

/// @nodoc
class _$QuestionAnalyticsCopyWithImpl<$Res, $Val extends QuestionAnalytics>
    implements $QuestionAnalyticsCopyWith<$Res> {
  _$QuestionAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? questionNumber = null,
    Object? sectionLabel = null,
    Object? maxMarks = null,
    Object? averageMarks = null,
    Object? difficultyIndex = null,
    Object? discriminationIndex = null,
    Object? attemptedCount = null,
    Object? correctCount = null,
    Object? partialCount = null,
    Object? blankCount = null,
    Object? avgTimeSeconds = null,
    Object? commonWrongAnswers = null,
    Object? optionDistribution = null,
    Object? flags = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      sectionLabel: null == sectionLabel
          ? _value.sectionLabel
          : sectionLabel // ignore: cast_nullable_to_non_nullable
              as String,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      averageMarks: null == averageMarks
          ? _value.averageMarks
          : averageMarks // ignore: cast_nullable_to_non_nullable
              as double,
      difficultyIndex: null == difficultyIndex
          ? _value.difficultyIndex
          : difficultyIndex // ignore: cast_nullable_to_non_nullable
              as double,
      discriminationIndex: null == discriminationIndex
          ? _value.discriminationIndex
          : discriminationIndex // ignore: cast_nullable_to_non_nullable
              as double,
      attemptedCount: null == attemptedCount
          ? _value.attemptedCount
          : attemptedCount // ignore: cast_nullable_to_non_nullable
              as int,
      correctCount: null == correctCount
          ? _value.correctCount
          : correctCount // ignore: cast_nullable_to_non_nullable
              as int,
      partialCount: null == partialCount
          ? _value.partialCount
          : partialCount // ignore: cast_nullable_to_non_nullable
              as int,
      blankCount: null == blankCount
          ? _value.blankCount
          : blankCount // ignore: cast_nullable_to_non_nullable
              as int,
      avgTimeSeconds: null == avgTimeSeconds
          ? _value.avgTimeSeconds
          : avgTimeSeconds // ignore: cast_nullable_to_non_nullable
              as double,
      commonWrongAnswers: null == commonWrongAnswers
          ? _value.commonWrongAnswers
          : commonWrongAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
      optionDistribution: null == optionDistribution
          ? _value.optionDistribution
          : optionDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      flags: null == flags
          ? _value.flags
          : flags // ignore: cast_nullable_to_non_nullable
              as QuestionQualityFlags,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $QuestionQualityFlagsCopyWith<$Res> get flags {
    return $QuestionQualityFlagsCopyWith<$Res>(_value.flags, (value) {
      return _then(_value.copyWith(flags: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$QuestionAnalyticsImplCopyWith<$Res>
    implements $QuestionAnalyticsCopyWith<$Res> {
  factory _$$QuestionAnalyticsImplCopyWith(_$QuestionAnalyticsImpl value,
          $Res Function(_$QuestionAnalyticsImpl) then) =
      __$$QuestionAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      int questionNumber,
      String sectionLabel,
      int maxMarks,
      double averageMarks,
      double difficultyIndex,
      double discriminationIndex,
      int attemptedCount,
      int correctCount,
      int partialCount,
      int blankCount,
      double avgTimeSeconds,
      List<String> commonWrongAnswers,
      Map<String, int> optionDistribution,
      QuestionQualityFlags flags});

  @override
  $QuestionQualityFlagsCopyWith<$Res> get flags;
}

/// @nodoc
class __$$QuestionAnalyticsImplCopyWithImpl<$Res>
    extends _$QuestionAnalyticsCopyWithImpl<$Res, _$QuestionAnalyticsImpl>
    implements _$$QuestionAnalyticsImplCopyWith<$Res> {
  __$$QuestionAnalyticsImplCopyWithImpl(_$QuestionAnalyticsImpl _value,
      $Res Function(_$QuestionAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? questionNumber = null,
    Object? sectionLabel = null,
    Object? maxMarks = null,
    Object? averageMarks = null,
    Object? difficultyIndex = null,
    Object? discriminationIndex = null,
    Object? attemptedCount = null,
    Object? correctCount = null,
    Object? partialCount = null,
    Object? blankCount = null,
    Object? avgTimeSeconds = null,
    Object? commonWrongAnswers = null,
    Object? optionDistribution = null,
    Object? flags = null,
  }) {
    return _then(_$QuestionAnalyticsImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      sectionLabel: null == sectionLabel
          ? _value.sectionLabel
          : sectionLabel // ignore: cast_nullable_to_non_nullable
              as String,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      averageMarks: null == averageMarks
          ? _value.averageMarks
          : averageMarks // ignore: cast_nullable_to_non_nullable
              as double,
      difficultyIndex: null == difficultyIndex
          ? _value.difficultyIndex
          : difficultyIndex // ignore: cast_nullable_to_non_nullable
              as double,
      discriminationIndex: null == discriminationIndex
          ? _value.discriminationIndex
          : discriminationIndex // ignore: cast_nullable_to_non_nullable
              as double,
      attemptedCount: null == attemptedCount
          ? _value.attemptedCount
          : attemptedCount // ignore: cast_nullable_to_non_nullable
              as int,
      correctCount: null == correctCount
          ? _value.correctCount
          : correctCount // ignore: cast_nullable_to_non_nullable
              as int,
      partialCount: null == partialCount
          ? _value.partialCount
          : partialCount // ignore: cast_nullable_to_non_nullable
              as int,
      blankCount: null == blankCount
          ? _value.blankCount
          : blankCount // ignore: cast_nullable_to_non_nullable
              as int,
      avgTimeSeconds: null == avgTimeSeconds
          ? _value.avgTimeSeconds
          : avgTimeSeconds // ignore: cast_nullable_to_non_nullable
              as double,
      commonWrongAnswers: null == commonWrongAnswers
          ? _value._commonWrongAnswers
          : commonWrongAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
      optionDistribution: null == optionDistribution
          ? _value._optionDistribution
          : optionDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      flags: null == flags
          ? _value.flags
          : flags // ignore: cast_nullable_to_non_nullable
              as QuestionQualityFlags,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionAnalyticsImpl implements _QuestionAnalytics {
  const _$QuestionAnalyticsImpl(
      {required this.questionId,
      required this.questionNumber,
      required this.sectionLabel,
      required this.maxMarks,
      required this.averageMarks,
      required this.difficultyIndex,
      required this.discriminationIndex,
      required this.attemptedCount,
      required this.correctCount,
      required this.partialCount,
      required this.blankCount,
      required this.avgTimeSeconds,
      required final List<String> commonWrongAnswers,
      required final Map<String, int> optionDistribution,
      required this.flags})
      : _commonWrongAnswers = commonWrongAnswers,
        _optionDistribution = optionDistribution;

  factory _$QuestionAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionAnalyticsImplFromJson(json);

  @override
  final String questionId;
  @override
  final int questionNumber;
  @override
  final String sectionLabel;
  @override
  final int maxMarks;
  @override
  final double averageMarks;
  @override
  final double difficultyIndex;
  @override
  final double discriminationIndex;
  @override
  final int attemptedCount;
  @override
  final int correctCount;
  @override
  final int partialCount;
  @override
  final int blankCount;
  @override
  final double avgTimeSeconds;
  final List<String> _commonWrongAnswers;
  @override
  List<String> get commonWrongAnswers {
    if (_commonWrongAnswers is EqualUnmodifiableListView)
      return _commonWrongAnswers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_commonWrongAnswers);
  }

  final Map<String, int> _optionDistribution;
  @override
  Map<String, int> get optionDistribution {
    if (_optionDistribution is EqualUnmodifiableMapView)
      return _optionDistribution;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_optionDistribution);
  }

  @override
  final QuestionQualityFlags flags;

  @override
  String toString() {
    return 'QuestionAnalytics(questionId: $questionId, questionNumber: $questionNumber, sectionLabel: $sectionLabel, maxMarks: $maxMarks, averageMarks: $averageMarks, difficultyIndex: $difficultyIndex, discriminationIndex: $discriminationIndex, attemptedCount: $attemptedCount, correctCount: $correctCount, partialCount: $partialCount, blankCount: $blankCount, avgTimeSeconds: $avgTimeSeconds, commonWrongAnswers: $commonWrongAnswers, optionDistribution: $optionDistribution, flags: $flags)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionAnalyticsImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.questionNumber, questionNumber) ||
                other.questionNumber == questionNumber) &&
            (identical(other.sectionLabel, sectionLabel) ||
                other.sectionLabel == sectionLabel) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.averageMarks, averageMarks) ||
                other.averageMarks == averageMarks) &&
            (identical(other.difficultyIndex, difficultyIndex) ||
                other.difficultyIndex == difficultyIndex) &&
            (identical(other.discriminationIndex, discriminationIndex) ||
                other.discriminationIndex == discriminationIndex) &&
            (identical(other.attemptedCount, attemptedCount) ||
                other.attemptedCount == attemptedCount) &&
            (identical(other.correctCount, correctCount) ||
                other.correctCount == correctCount) &&
            (identical(other.partialCount, partialCount) ||
                other.partialCount == partialCount) &&
            (identical(other.blankCount, blankCount) ||
                other.blankCount == blankCount) &&
            (identical(other.avgTimeSeconds, avgTimeSeconds) ||
                other.avgTimeSeconds == avgTimeSeconds) &&
            const DeepCollectionEquality()
                .equals(other._commonWrongAnswers, _commonWrongAnswers) &&
            const DeepCollectionEquality()
                .equals(other._optionDistribution, _optionDistribution) &&
            (identical(other.flags, flags) || other.flags == flags));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      questionNumber,
      sectionLabel,
      maxMarks,
      averageMarks,
      difficultyIndex,
      discriminationIndex,
      attemptedCount,
      correctCount,
      partialCount,
      blankCount,
      avgTimeSeconds,
      const DeepCollectionEquality().hash(_commonWrongAnswers),
      const DeepCollectionEquality().hash(_optionDistribution),
      flags);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionAnalyticsImplCopyWith<_$QuestionAnalyticsImpl> get copyWith =>
      __$$QuestionAnalyticsImplCopyWithImpl<_$QuestionAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _QuestionAnalytics implements QuestionAnalytics {
  const factory _QuestionAnalytics(
      {required final String questionId,
      required final int questionNumber,
      required final String sectionLabel,
      required final int maxMarks,
      required final double averageMarks,
      required final double difficultyIndex,
      required final double discriminationIndex,
      required final int attemptedCount,
      required final int correctCount,
      required final int partialCount,
      required final int blankCount,
      required final double avgTimeSeconds,
      required final List<String> commonWrongAnswers,
      required final Map<String, int> optionDistribution,
      required final QuestionQualityFlags flags}) = _$QuestionAnalyticsImpl;

  factory _QuestionAnalytics.fromJson(Map<String, dynamic> json) =
      _$QuestionAnalyticsImpl.fromJson;

  @override
  String get questionId;
  @override
  int get questionNumber;
  @override
  String get sectionLabel;
  @override
  int get maxMarks;
  @override
  double get averageMarks;
  @override
  double get difficultyIndex;
  @override
  double get discriminationIndex;
  @override
  int get attemptedCount;
  @override
  int get correctCount;
  @override
  int get partialCount;
  @override
  int get blankCount;
  @override
  double get avgTimeSeconds;
  @override
  List<String> get commonWrongAnswers;
  @override
  Map<String, int> get optionDistribution;
  @override
  QuestionQualityFlags get flags;
  @override
  @JsonKey(ignore: true)
  _$$QuestionAnalyticsImplCopyWith<_$QuestionAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionQualityFlags _$QuestionQualityFlagsFromJson(Map<String, dynamic> json) {
  return _QuestionQualityFlags.fromJson(json);
}

/// @nodoc
mixin _$QuestionQualityFlags {
  bool get tooEasy => throw _privateConstructorUsedError;
  bool get tooHard => throw _privateConstructorUsedError;
  bool get poorDiscrimination => throw _privateConstructorUsedError;
  bool get ambiguous => throw _privateConstructorUsedError;
  bool get guessingPossible => throw _privateConstructorUsedError;
  bool get timeConsuming => throw _privateConstructorUsedError;
  List<String> get warnings => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionQualityFlagsCopyWith<QuestionQualityFlags> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionQualityFlagsCopyWith<$Res> {
  factory $QuestionQualityFlagsCopyWith(QuestionQualityFlags value,
          $Res Function(QuestionQualityFlags) then) =
      _$QuestionQualityFlagsCopyWithImpl<$Res, QuestionQualityFlags>;
  @useResult
  $Res call(
      {bool tooEasy,
      bool tooHard,
      bool poorDiscrimination,
      bool ambiguous,
      bool guessingPossible,
      bool timeConsuming,
      List<String> warnings});
}

/// @nodoc
class _$QuestionQualityFlagsCopyWithImpl<$Res,
        $Val extends QuestionQualityFlags>
    implements $QuestionQualityFlagsCopyWith<$Res> {
  _$QuestionQualityFlagsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? tooEasy = null,
    Object? tooHard = null,
    Object? poorDiscrimination = null,
    Object? ambiguous = null,
    Object? guessingPossible = null,
    Object? timeConsuming = null,
    Object? warnings = null,
  }) {
    return _then(_value.copyWith(
      tooEasy: null == tooEasy
          ? _value.tooEasy
          : tooEasy // ignore: cast_nullable_to_non_nullable
              as bool,
      tooHard: null == tooHard
          ? _value.tooHard
          : tooHard // ignore: cast_nullable_to_non_nullable
              as bool,
      poorDiscrimination: null == poorDiscrimination
          ? _value.poorDiscrimination
          : poorDiscrimination // ignore: cast_nullable_to_non_nullable
              as bool,
      ambiguous: null == ambiguous
          ? _value.ambiguous
          : ambiguous // ignore: cast_nullable_to_non_nullable
              as bool,
      guessingPossible: null == guessingPossible
          ? _value.guessingPossible
          : guessingPossible // ignore: cast_nullable_to_non_nullable
              as bool,
      timeConsuming: null == timeConsuming
          ? _value.timeConsuming
          : timeConsuming // ignore: cast_nullable_to_non_nullable
              as bool,
      warnings: null == warnings
          ? _value.warnings
          : warnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuestionQualityFlagsImplCopyWith<$Res>
    implements $QuestionQualityFlagsCopyWith<$Res> {
  factory _$$QuestionQualityFlagsImplCopyWith(_$QuestionQualityFlagsImpl value,
          $Res Function(_$QuestionQualityFlagsImpl) then) =
      __$$QuestionQualityFlagsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool tooEasy,
      bool tooHard,
      bool poorDiscrimination,
      bool ambiguous,
      bool guessingPossible,
      bool timeConsuming,
      List<String> warnings});
}

/// @nodoc
class __$$QuestionQualityFlagsImplCopyWithImpl<$Res>
    extends _$QuestionQualityFlagsCopyWithImpl<$Res, _$QuestionQualityFlagsImpl>
    implements _$$QuestionQualityFlagsImplCopyWith<$Res> {
  __$$QuestionQualityFlagsImplCopyWithImpl(_$QuestionQualityFlagsImpl _value,
      $Res Function(_$QuestionQualityFlagsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? tooEasy = null,
    Object? tooHard = null,
    Object? poorDiscrimination = null,
    Object? ambiguous = null,
    Object? guessingPossible = null,
    Object? timeConsuming = null,
    Object? warnings = null,
  }) {
    return _then(_$QuestionQualityFlagsImpl(
      tooEasy: null == tooEasy
          ? _value.tooEasy
          : tooEasy // ignore: cast_nullable_to_non_nullable
              as bool,
      tooHard: null == tooHard
          ? _value.tooHard
          : tooHard // ignore: cast_nullable_to_non_nullable
              as bool,
      poorDiscrimination: null == poorDiscrimination
          ? _value.poorDiscrimination
          : poorDiscrimination // ignore: cast_nullable_to_non_nullable
              as bool,
      ambiguous: null == ambiguous
          ? _value.ambiguous
          : ambiguous // ignore: cast_nullable_to_non_nullable
              as bool,
      guessingPossible: null == guessingPossible
          ? _value.guessingPossible
          : guessingPossible // ignore: cast_nullable_to_non_nullable
              as bool,
      timeConsuming: null == timeConsuming
          ? _value.timeConsuming
          : timeConsuming // ignore: cast_nullable_to_non_nullable
              as bool,
      warnings: null == warnings
          ? _value._warnings
          : warnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionQualityFlagsImpl implements _QuestionQualityFlags {
  const _$QuestionQualityFlagsImpl(
      {this.tooEasy = false,
      this.tooHard = false,
      this.poorDiscrimination = false,
      this.ambiguous = false,
      this.guessingPossible = false,
      this.timeConsuming = false,
      final List<String> warnings = const []})
      : _warnings = warnings;

  factory _$QuestionQualityFlagsImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionQualityFlagsImplFromJson(json);

  @override
  @JsonKey()
  final bool tooEasy;
  @override
  @JsonKey()
  final bool tooHard;
  @override
  @JsonKey()
  final bool poorDiscrimination;
  @override
  @JsonKey()
  final bool ambiguous;
  @override
  @JsonKey()
  final bool guessingPossible;
  @override
  @JsonKey()
  final bool timeConsuming;
  final List<String> _warnings;
  @override
  @JsonKey()
  List<String> get warnings {
    if (_warnings is EqualUnmodifiableListView) return _warnings;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_warnings);
  }

  @override
  String toString() {
    return 'QuestionQualityFlags(tooEasy: $tooEasy, tooHard: $tooHard, poorDiscrimination: $poorDiscrimination, ambiguous: $ambiguous, guessingPossible: $guessingPossible, timeConsuming: $timeConsuming, warnings: $warnings)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionQualityFlagsImpl &&
            (identical(other.tooEasy, tooEasy) || other.tooEasy == tooEasy) &&
            (identical(other.tooHard, tooHard) || other.tooHard == tooHard) &&
            (identical(other.poorDiscrimination, poorDiscrimination) ||
                other.poorDiscrimination == poorDiscrimination) &&
            (identical(other.ambiguous, ambiguous) ||
                other.ambiguous == ambiguous) &&
            (identical(other.guessingPossible, guessingPossible) ||
                other.guessingPossible == guessingPossible) &&
            (identical(other.timeConsuming, timeConsuming) ||
                other.timeConsuming == timeConsuming) &&
            const DeepCollectionEquality().equals(other._warnings, _warnings));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      tooEasy,
      tooHard,
      poorDiscrimination,
      ambiguous,
      guessingPossible,
      timeConsuming,
      const DeepCollectionEquality().hash(_warnings));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionQualityFlagsImplCopyWith<_$QuestionQualityFlagsImpl>
      get copyWith =>
          __$$QuestionQualityFlagsImplCopyWithImpl<_$QuestionQualityFlagsImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionQualityFlagsImplToJson(
      this,
    );
  }
}

abstract class _QuestionQualityFlags implements QuestionQualityFlags {
  const factory _QuestionQualityFlags(
      {final bool tooEasy,
      final bool tooHard,
      final bool poorDiscrimination,
      final bool ambiguous,
      final bool guessingPossible,
      final bool timeConsuming,
      final List<String> warnings}) = _$QuestionQualityFlagsImpl;

  factory _QuestionQualityFlags.fromJson(Map<String, dynamic> json) =
      _$QuestionQualityFlagsImpl.fromJson;

  @override
  bool get tooEasy;
  @override
  bool get tooHard;
  @override
  bool get poorDiscrimination;
  @override
  bool get ambiguous;
  @override
  bool get guessingPossible;
  @override
  bool get timeConsuming;
  @override
  List<String> get warnings;
  @override
  @JsonKey(ignore: true)
  _$$QuestionQualityFlagsImplCopyWith<_$QuestionQualityFlagsImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ConceptGap _$ConceptGapFromJson(Map<String, dynamic> json) {
  return _ConceptGap.fromJson(json);
}

/// @nodoc
mixin _$ConceptGap {
  String get conceptId => throw _privateConstructorUsedError;
  String get conceptName => throw _privateConstructorUsedError;
  String get chapterId => throw _privateConstructorUsedError;
  String get chapterName => throw _privateConstructorUsedError;
  int get studentsAffected => throw _privateConstructorUsedError;
  double get avgMastery => throw _privateConstructorUsedError;
  List<String> get relatedQuestionIds => throw _privateConstructorUsedError;
  List<String> get misconceptionIds => throw _privateConstructorUsedError;
  GapSeverity get severity => throw _privateConstructorUsedError;
  String get recommendedAction => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ConceptGapCopyWith<ConceptGap> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ConceptGapCopyWith<$Res> {
  factory $ConceptGapCopyWith(
          ConceptGap value, $Res Function(ConceptGap) then) =
      _$ConceptGapCopyWithImpl<$Res, ConceptGap>;
  @useResult
  $Res call(
      {String conceptId,
      String conceptName,
      String chapterId,
      String chapterName,
      int studentsAffected,
      double avgMastery,
      List<String> relatedQuestionIds,
      List<String> misconceptionIds,
      GapSeverity severity,
      String recommendedAction});
}

/// @nodoc
class _$ConceptGapCopyWithImpl<$Res, $Val extends ConceptGap>
    implements $ConceptGapCopyWith<$Res> {
  _$ConceptGapCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? conceptId = null,
    Object? conceptName = null,
    Object? chapterId = null,
    Object? chapterName = null,
    Object? studentsAffected = null,
    Object? avgMastery = null,
    Object? relatedQuestionIds = null,
    Object? misconceptionIds = null,
    Object? severity = null,
    Object? recommendedAction = null,
  }) {
    return _then(_value.copyWith(
      conceptId: null == conceptId
          ? _value.conceptId
          : conceptId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptName: null == conceptName
          ? _value.conceptName
          : conceptName // ignore: cast_nullable_to_non_nullable
              as String,
      chapterId: null == chapterId
          ? _value.chapterId
          : chapterId // ignore: cast_nullable_to_non_nullable
              as String,
      chapterName: null == chapterName
          ? _value.chapterName
          : chapterName // ignore: cast_nullable_to_non_nullable
              as String,
      studentsAffected: null == studentsAffected
          ? _value.studentsAffected
          : studentsAffected // ignore: cast_nullable_to_non_nullable
              as int,
      avgMastery: null == avgMastery
          ? _value.avgMastery
          : avgMastery // ignore: cast_nullable_to_non_nullable
              as double,
      relatedQuestionIds: null == relatedQuestionIds
          ? _value.relatedQuestionIds
          : relatedQuestionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      misconceptionIds: null == misconceptionIds
          ? _value.misconceptionIds
          : misconceptionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      severity: null == severity
          ? _value.severity
          : severity // ignore: cast_nullable_to_non_nullable
              as GapSeverity,
      recommendedAction: null == recommendedAction
          ? _value.recommendedAction
          : recommendedAction // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ConceptGapImplCopyWith<$Res>
    implements $ConceptGapCopyWith<$Res> {
  factory _$$ConceptGapImplCopyWith(
          _$ConceptGapImpl value, $Res Function(_$ConceptGapImpl) then) =
      __$$ConceptGapImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String conceptId,
      String conceptName,
      String chapterId,
      String chapterName,
      int studentsAffected,
      double avgMastery,
      List<String> relatedQuestionIds,
      List<String> misconceptionIds,
      GapSeverity severity,
      String recommendedAction});
}

/// @nodoc
class __$$ConceptGapImplCopyWithImpl<$Res>
    extends _$ConceptGapCopyWithImpl<$Res, _$ConceptGapImpl>
    implements _$$ConceptGapImplCopyWith<$Res> {
  __$$ConceptGapImplCopyWithImpl(
      _$ConceptGapImpl _value, $Res Function(_$ConceptGapImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? conceptId = null,
    Object? conceptName = null,
    Object? chapterId = null,
    Object? chapterName = null,
    Object? studentsAffected = null,
    Object? avgMastery = null,
    Object? relatedQuestionIds = null,
    Object? misconceptionIds = null,
    Object? severity = null,
    Object? recommendedAction = null,
  }) {
    return _then(_$ConceptGapImpl(
      conceptId: null == conceptId
          ? _value.conceptId
          : conceptId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptName: null == conceptName
          ? _value.conceptName
          : conceptName // ignore: cast_nullable_to_non_nullable
              as String,
      chapterId: null == chapterId
          ? _value.chapterId
          : chapterId // ignore: cast_nullable_to_non_nullable
              as String,
      chapterName: null == chapterName
          ? _value.chapterName
          : chapterName // ignore: cast_nullable_to_non_nullable
              as String,
      studentsAffected: null == studentsAffected
          ? _value.studentsAffected
          : studentsAffected // ignore: cast_nullable_to_non_nullable
              as int,
      avgMastery: null == avgMastery
          ? _value.avgMastery
          : avgMastery // ignore: cast_nullable_to_non_nullable
              as double,
      relatedQuestionIds: null == relatedQuestionIds
          ? _value._relatedQuestionIds
          : relatedQuestionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      misconceptionIds: null == misconceptionIds
          ? _value._misconceptionIds
          : misconceptionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      severity: null == severity
          ? _value.severity
          : severity // ignore: cast_nullable_to_non_nullable
              as GapSeverity,
      recommendedAction: null == recommendedAction
          ? _value.recommendedAction
          : recommendedAction // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ConceptGapImpl implements _ConceptGap {
  const _$ConceptGapImpl(
      {required this.conceptId,
      required this.conceptName,
      required this.chapterId,
      required this.chapterName,
      required this.studentsAffected,
      required this.avgMastery,
      required final List<String> relatedQuestionIds,
      required final List<String> misconceptionIds,
      required this.severity,
      required this.recommendedAction})
      : _relatedQuestionIds = relatedQuestionIds,
        _misconceptionIds = misconceptionIds;

  factory _$ConceptGapImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConceptGapImplFromJson(json);

  @override
  final String conceptId;
  @override
  final String conceptName;
  @override
  final String chapterId;
  @override
  final String chapterName;
  @override
  final int studentsAffected;
  @override
  final double avgMastery;
  final List<String> _relatedQuestionIds;
  @override
  List<String> get relatedQuestionIds {
    if (_relatedQuestionIds is EqualUnmodifiableListView)
      return _relatedQuestionIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_relatedQuestionIds);
  }

  final List<String> _misconceptionIds;
  @override
  List<String> get misconceptionIds {
    if (_misconceptionIds is EqualUnmodifiableListView)
      return _misconceptionIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_misconceptionIds);
  }

  @override
  final GapSeverity severity;
  @override
  final String recommendedAction;

  @override
  String toString() {
    return 'ConceptGap(conceptId: $conceptId, conceptName: $conceptName, chapterId: $chapterId, chapterName: $chapterName, studentsAffected: $studentsAffected, avgMastery: $avgMastery, relatedQuestionIds: $relatedQuestionIds, misconceptionIds: $misconceptionIds, severity: $severity, recommendedAction: $recommendedAction)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConceptGapImpl &&
            (identical(other.conceptId, conceptId) ||
                other.conceptId == conceptId) &&
            (identical(other.conceptName, conceptName) ||
                other.conceptName == conceptName) &&
            (identical(other.chapterId, chapterId) ||
                other.chapterId == chapterId) &&
            (identical(other.chapterName, chapterName) ||
                other.chapterName == chapterName) &&
            (identical(other.studentsAffected, studentsAffected) ||
                other.studentsAffected == studentsAffected) &&
            (identical(other.avgMastery, avgMastery) ||
                other.avgMastery == avgMastery) &&
            const DeepCollectionEquality()
                .equals(other._relatedQuestionIds, _relatedQuestionIds) &&
            const DeepCollectionEquality()
                .equals(other._misconceptionIds, _misconceptionIds) &&
            (identical(other.severity, severity) ||
                other.severity == severity) &&
            (identical(other.recommendedAction, recommendedAction) ||
                other.recommendedAction == recommendedAction));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      conceptId,
      conceptName,
      chapterId,
      chapterName,
      studentsAffected,
      avgMastery,
      const DeepCollectionEquality().hash(_relatedQuestionIds),
      const DeepCollectionEquality().hash(_misconceptionIds),
      severity,
      recommendedAction);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ConceptGapImplCopyWith<_$ConceptGapImpl> get copyWith =>
      __$$ConceptGapImplCopyWithImpl<_$ConceptGapImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ConceptGapImplToJson(
      this,
    );
  }
}

abstract class _ConceptGap implements ConceptGap {
  const factory _ConceptGap(
      {required final String conceptId,
      required final String conceptName,
      required final String chapterId,
      required final String chapterName,
      required final int studentsAffected,
      required final double avgMastery,
      required final List<String> relatedQuestionIds,
      required final List<String> misconceptionIds,
      required final GapSeverity severity,
      required final String recommendedAction}) = _$ConceptGapImpl;

  factory _ConceptGap.fromJson(Map<String, dynamic> json) =
      _$ConceptGapImpl.fromJson;

  @override
  String get conceptId;
  @override
  String get conceptName;
  @override
  String get chapterId;
  @override
  String get chapterName;
  @override
  int get studentsAffected;
  @override
  double get avgMastery;
  @override
  List<String> get relatedQuestionIds;
  @override
  List<String> get misconceptionIds;
  @override
  GapSeverity get severity;
  @override
  String get recommendedAction;
  @override
  @JsonKey(ignore: true)
  _$$ConceptGapImplCopyWith<_$ConceptGapImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BloomAnalytics _$BloomAnalyticsFromJson(Map<String, dynamic> json) {
  return _BloomAnalytics.fromJson(json);
}

/// @nodoc
mixin _$BloomAnalytics {
  Map<String, BloomLevelStats> get byLevel =>
      throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BloomAnalyticsCopyWith<BloomAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BloomAnalyticsCopyWith<$Res> {
  factory $BloomAnalyticsCopyWith(
          BloomAnalytics value, $Res Function(BloomAnalytics) then) =
      _$BloomAnalyticsCopyWithImpl<$Res, BloomAnalytics>;
  @useResult
  $Res call({Map<String, BloomLevelStats> byLevel, List<String> insights});
}

/// @nodoc
class _$BloomAnalyticsCopyWithImpl<$Res, $Val extends BloomAnalytics>
    implements $BloomAnalyticsCopyWith<$Res> {
  _$BloomAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byLevel = null,
    Object? insights = null,
  }) {
    return _then(_value.copyWith(
      byLevel: null == byLevel
          ? _value.byLevel
          : byLevel // ignore: cast_nullable_to_non_nullable
              as Map<String, BloomLevelStats>,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BloomAnalyticsImplCopyWith<$Res>
    implements $BloomAnalyticsCopyWith<$Res> {
  factory _$$BloomAnalyticsImplCopyWith(_$BloomAnalyticsImpl value,
          $Res Function(_$BloomAnalyticsImpl) then) =
      __$$BloomAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({Map<String, BloomLevelStats> byLevel, List<String> insights});
}

/// @nodoc
class __$$BloomAnalyticsImplCopyWithImpl<$Res>
    extends _$BloomAnalyticsCopyWithImpl<$Res, _$BloomAnalyticsImpl>
    implements _$$BloomAnalyticsImplCopyWith<$Res> {
  __$$BloomAnalyticsImplCopyWithImpl(
      _$BloomAnalyticsImpl _value, $Res Function(_$BloomAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byLevel = null,
    Object? insights = null,
  }) {
    return _then(_$BloomAnalyticsImpl(
      byLevel: null == byLevel
          ? _value._byLevel
          : byLevel // ignore: cast_nullable_to_non_nullable
              as Map<String, BloomLevelStats>,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BloomAnalyticsImpl implements _BloomAnalytics {
  const _$BloomAnalyticsImpl(
      {required final Map<String, BloomLevelStats> byLevel,
      required final List<String> insights})
      : _byLevel = byLevel,
        _insights = insights;

  factory _$BloomAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$BloomAnalyticsImplFromJson(json);

  final Map<String, BloomLevelStats> _byLevel;
  @override
  Map<String, BloomLevelStats> get byLevel {
    if (_byLevel is EqualUnmodifiableMapView) return _byLevel;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_byLevel);
  }

  final List<String> _insights;
  @override
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  @override
  String toString() {
    return 'BloomAnalytics(byLevel: $byLevel, insights: $insights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BloomAnalyticsImpl &&
            const DeepCollectionEquality().equals(other._byLevel, _byLevel) &&
            const DeepCollectionEquality().equals(other._insights, _insights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_byLevel),
      const DeepCollectionEquality().hash(_insights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BloomAnalyticsImplCopyWith<_$BloomAnalyticsImpl> get copyWith =>
      __$$BloomAnalyticsImplCopyWithImpl<_$BloomAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BloomAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _BloomAnalytics implements BloomAnalytics {
  const factory _BloomAnalytics(
      {required final Map<String, BloomLevelStats> byLevel,
      required final List<String> insights}) = _$BloomAnalyticsImpl;

  factory _BloomAnalytics.fromJson(Map<String, dynamic> json) =
      _$BloomAnalyticsImpl.fromJson;

  @override
  Map<String, BloomLevelStats> get byLevel;
  @override
  List<String> get insights;
  @override
  @JsonKey(ignore: true)
  _$$BloomAnalyticsImplCopyWith<_$BloomAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BloomLevelStats _$BloomLevelStatsFromJson(Map<String, dynamic> json) {
  return _BloomLevelStats.fromJson(json);
}

/// @nodoc
mixin _$BloomLevelStats {
  String get level => throw _privateConstructorUsedError;
  int get questionCount => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;
  double get avgScore => throw _privateConstructorUsedError;
  double get avgPercentage => throw _privateConstructorUsedError;
  int get studentsAttempted => throw _privateConstructorUsedError;
  int get studentsProficient => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BloomLevelStatsCopyWith<BloomLevelStats> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BloomLevelStatsCopyWith<$Res> {
  factory $BloomLevelStatsCopyWith(
          BloomLevelStats value, $Res Function(BloomLevelStats) then) =
      _$BloomLevelStatsCopyWithImpl<$Res, BloomLevelStats>;
  @useResult
  $Res call(
      {String level,
      int questionCount,
      int totalMarks,
      double avgScore,
      double avgPercentage,
      int studentsAttempted,
      int studentsProficient});
}

/// @nodoc
class _$BloomLevelStatsCopyWithImpl<$Res, $Val extends BloomLevelStats>
    implements $BloomLevelStatsCopyWith<$Res> {
  _$BloomLevelStatsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? avgScore = null,
    Object? avgPercentage = null,
    Object? studentsAttempted = null,
    Object? studentsProficient = null,
  }) {
    return _then(_value.copyWith(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      avgScore: null == avgScore
          ? _value.avgScore
          : avgScore // ignore: cast_nullable_to_non_nullable
              as double,
      avgPercentage: null == avgPercentage
          ? _value.avgPercentage
          : avgPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      studentsAttempted: null == studentsAttempted
          ? _value.studentsAttempted
          : studentsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      studentsProficient: null == studentsProficient
          ? _value.studentsProficient
          : studentsProficient // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BloomLevelStatsImplCopyWith<$Res>
    implements $BloomLevelStatsCopyWith<$Res> {
  factory _$$BloomLevelStatsImplCopyWith(_$BloomLevelStatsImpl value,
          $Res Function(_$BloomLevelStatsImpl) then) =
      __$$BloomLevelStatsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String level,
      int questionCount,
      int totalMarks,
      double avgScore,
      double avgPercentage,
      int studentsAttempted,
      int studentsProficient});
}

/// @nodoc
class __$$BloomLevelStatsImplCopyWithImpl<$Res>
    extends _$BloomLevelStatsCopyWithImpl<$Res, _$BloomLevelStatsImpl>
    implements _$$BloomLevelStatsImplCopyWith<$Res> {
  __$$BloomLevelStatsImplCopyWithImpl(
      _$BloomLevelStatsImpl _value, $Res Function(_$BloomLevelStatsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? avgScore = null,
    Object? avgPercentage = null,
    Object? studentsAttempted = null,
    Object? studentsProficient = null,
  }) {
    return _then(_$BloomLevelStatsImpl(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      avgScore: null == avgScore
          ? _value.avgScore
          : avgScore // ignore: cast_nullable_to_non_nullable
              as double,
      avgPercentage: null == avgPercentage
          ? _value.avgPercentage
          : avgPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      studentsAttempted: null == studentsAttempted
          ? _value.studentsAttempted
          : studentsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      studentsProficient: null == studentsProficient
          ? _value.studentsProficient
          : studentsProficient // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BloomLevelStatsImpl implements _BloomLevelStats {
  const _$BloomLevelStatsImpl(
      {required this.level,
      required this.questionCount,
      required this.totalMarks,
      required this.avgScore,
      required this.avgPercentage,
      required this.studentsAttempted,
      required this.studentsProficient});

  factory _$BloomLevelStatsImpl.fromJson(Map<String, dynamic> json) =>
      _$$BloomLevelStatsImplFromJson(json);

  @override
  final String level;
  @override
  final int questionCount;
  @override
  final int totalMarks;
  @override
  final double avgScore;
  @override
  final double avgPercentage;
  @override
  final int studentsAttempted;
  @override
  final int studentsProficient;

  @override
  String toString() {
    return 'BloomLevelStats(level: $level, questionCount: $questionCount, totalMarks: $totalMarks, avgScore: $avgScore, avgPercentage: $avgPercentage, studentsAttempted: $studentsAttempted, studentsProficient: $studentsProficient)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BloomLevelStatsImpl &&
            (identical(other.level, level) || other.level == level) &&
            (identical(other.questionCount, questionCount) ||
                other.questionCount == questionCount) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            (identical(other.avgScore, avgScore) ||
                other.avgScore == avgScore) &&
            (identical(other.avgPercentage, avgPercentage) ||
                other.avgPercentage == avgPercentage) &&
            (identical(other.studentsAttempted, studentsAttempted) ||
                other.studentsAttempted == studentsAttempted) &&
            (identical(other.studentsProficient, studentsProficient) ||
                other.studentsProficient == studentsProficient));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, level, questionCount, totalMarks,
      avgScore, avgPercentage, studentsAttempted, studentsProficient);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BloomLevelStatsImplCopyWith<_$BloomLevelStatsImpl> get copyWith =>
      __$$BloomLevelStatsImplCopyWithImpl<_$BloomLevelStatsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BloomLevelStatsImplToJson(
      this,
    );
  }
}

abstract class _BloomLevelStats implements BloomLevelStats {
  const factory _BloomLevelStats(
      {required final String level,
      required final int questionCount,
      required final int totalMarks,
      required final double avgScore,
      required final double avgPercentage,
      required final int studentsAttempted,
      required final int studentsProficient}) = _$BloomLevelStatsImpl;

  factory _BloomLevelStats.fromJson(Map<String, dynamic> json) =
      _$BloomLevelStatsImpl.fromJson;

  @override
  String get level;
  @override
  int get questionCount;
  @override
  int get totalMarks;
  @override
  double get avgScore;
  @override
  double get avgPercentage;
  @override
  int get studentsAttempted;
  @override
  int get studentsProficient;
  @override
  @JsonKey(ignore: true)
  _$$BloomLevelStatsImplCopyWith<_$BloomLevelStatsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CompetencyAnalytics _$CompetencyAnalyticsFromJson(Map<String, dynamic> json) {
  return _CompetencyAnalytics.fromJson(json);
}

/// @nodoc
mixin _$CompetencyAnalytics {
  Map<String, CompetencyStats> get byCompetency =>
      throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CompetencyAnalyticsCopyWith<CompetencyAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CompetencyAnalyticsCopyWith<$Res> {
  factory $CompetencyAnalyticsCopyWith(
          CompetencyAnalytics value, $Res Function(CompetencyAnalytics) then) =
      _$CompetencyAnalyticsCopyWithImpl<$Res, CompetencyAnalytics>;
  @useResult
  $Res call({Map<String, CompetencyStats> byCompetency, List<String> insights});
}

/// @nodoc
class _$CompetencyAnalyticsCopyWithImpl<$Res, $Val extends CompetencyAnalytics>
    implements $CompetencyAnalyticsCopyWith<$Res> {
  _$CompetencyAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byCompetency = null,
    Object? insights = null,
  }) {
    return _then(_value.copyWith(
      byCompetency: null == byCompetency
          ? _value.byCompetency
          : byCompetency // ignore: cast_nullable_to_non_nullable
              as Map<String, CompetencyStats>,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CompetencyAnalyticsImplCopyWith<$Res>
    implements $CompetencyAnalyticsCopyWith<$Res> {
  factory _$$CompetencyAnalyticsImplCopyWith(_$CompetencyAnalyticsImpl value,
          $Res Function(_$CompetencyAnalyticsImpl) then) =
      __$$CompetencyAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({Map<String, CompetencyStats> byCompetency, List<String> insights});
}

/// @nodoc
class __$$CompetencyAnalyticsImplCopyWithImpl<$Res>
    extends _$CompetencyAnalyticsCopyWithImpl<$Res, _$CompetencyAnalyticsImpl>
    implements _$$CompetencyAnalyticsImplCopyWith<$Res> {
  __$$CompetencyAnalyticsImplCopyWithImpl(_$CompetencyAnalyticsImpl _value,
      $Res Function(_$CompetencyAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byCompetency = null,
    Object? insights = null,
  }) {
    return _then(_$CompetencyAnalyticsImpl(
      byCompetency: null == byCompetency
          ? _value._byCompetency
          : byCompetency // ignore: cast_nullable_to_non_nullable
              as Map<String, CompetencyStats>,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CompetencyAnalyticsImpl implements _CompetencyAnalytics {
  const _$CompetencyAnalyticsImpl(
      {required final Map<String, CompetencyStats> byCompetency,
      required final List<String> insights})
      : _byCompetency = byCompetency,
        _insights = insights;

  factory _$CompetencyAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$CompetencyAnalyticsImplFromJson(json);

  final Map<String, CompetencyStats> _byCompetency;
  @override
  Map<String, CompetencyStats> get byCompetency {
    if (_byCompetency is EqualUnmodifiableMapView) return _byCompetency;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_byCompetency);
  }

  final List<String> _insights;
  @override
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  @override
  String toString() {
    return 'CompetencyAnalytics(byCompetency: $byCompetency, insights: $insights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CompetencyAnalyticsImpl &&
            const DeepCollectionEquality()
                .equals(other._byCompetency, _byCompetency) &&
            const DeepCollectionEquality().equals(other._insights, _insights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_byCompetency),
      const DeepCollectionEquality().hash(_insights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CompetencyAnalyticsImplCopyWith<_$CompetencyAnalyticsImpl> get copyWith =>
      __$$CompetencyAnalyticsImplCopyWithImpl<_$CompetencyAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CompetencyAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _CompetencyAnalytics implements CompetencyAnalytics {
  const factory _CompetencyAnalytics(
      {required final Map<String, CompetencyStats> byCompetency,
      required final List<String> insights}) = _$CompetencyAnalyticsImpl;

  factory _CompetencyAnalytics.fromJson(Map<String, dynamic> json) =
      _$CompetencyAnalyticsImpl.fromJson;

  @override
  Map<String, CompetencyStats> get byCompetency;
  @override
  List<String> get insights;
  @override
  @JsonKey(ignore: true)
  _$$CompetencyAnalyticsImplCopyWith<_$CompetencyAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CompetencyStats _$CompetencyStatsFromJson(Map<String, dynamic> json) {
  return _CompetencyStats.fromJson(json);
}

/// @nodoc
mixin _$CompetencyStats {
  String get competencyId => throw _privateConstructorUsedError;
  String get competencyName => throw _privateConstructorUsedError;
  int get questionCount => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;
  double get avgScore => throw _privateConstructorUsedError;
  double get avgPercentage => throw _privateConstructorUsedError;
  int get studentsProficient => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CompetencyStatsCopyWith<CompetencyStats> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CompetencyStatsCopyWith<$Res> {
  factory $CompetencyStatsCopyWith(
          CompetencyStats value, $Res Function(CompetencyStats) then) =
      _$CompetencyStatsCopyWithImpl<$Res, CompetencyStats>;
  @useResult
  $Res call(
      {String competencyId,
      String competencyName,
      int questionCount,
      int totalMarks,
      double avgScore,
      double avgPercentage,
      int studentsProficient});
}

/// @nodoc
class _$CompetencyStatsCopyWithImpl<$Res, $Val extends CompetencyStats>
    implements $CompetencyStatsCopyWith<$Res> {
  _$CompetencyStatsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? competencyId = null,
    Object? competencyName = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? avgScore = null,
    Object? avgPercentage = null,
    Object? studentsProficient = null,
  }) {
    return _then(_value.copyWith(
      competencyId: null == competencyId
          ? _value.competencyId
          : competencyId // ignore: cast_nullable_to_non_nullable
              as String,
      competencyName: null == competencyName
          ? _value.competencyName
          : competencyName // ignore: cast_nullable_to_non_nullable
              as String,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      avgScore: null == avgScore
          ? _value.avgScore
          : avgScore // ignore: cast_nullable_to_non_nullable
              as double,
      avgPercentage: null == avgPercentage
          ? _value.avgPercentage
          : avgPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      studentsProficient: null == studentsProficient
          ? _value.studentsProficient
          : studentsProficient // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CompetencyStatsImplCopyWith<$Res>
    implements $CompetencyStatsCopyWith<$Res> {
  factory _$$CompetencyStatsImplCopyWith(_$CompetencyStatsImpl value,
          $Res Function(_$CompetencyStatsImpl) then) =
      __$$CompetencyStatsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String competencyId,
      String competencyName,
      int questionCount,
      int totalMarks,
      double avgScore,
      double avgPercentage,
      int studentsProficient});
}

/// @nodoc
class __$$CompetencyStatsImplCopyWithImpl<$Res>
    extends _$CompetencyStatsCopyWithImpl<$Res, _$CompetencyStatsImpl>
    implements _$$CompetencyStatsImplCopyWith<$Res> {
  __$$CompetencyStatsImplCopyWithImpl(
      _$CompetencyStatsImpl _value, $Res Function(_$CompetencyStatsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? competencyId = null,
    Object? competencyName = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? avgScore = null,
    Object? avgPercentage = null,
    Object? studentsProficient = null,
  }) {
    return _then(_$CompetencyStatsImpl(
      competencyId: null == competencyId
          ? _value.competencyId
          : competencyId // ignore: cast_nullable_to_non_nullable
              as String,
      competencyName: null == competencyName
          ? _value.competencyName
          : competencyName // ignore: cast_nullable_to_non_nullable
              as String,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      avgScore: null == avgScore
          ? _value.avgScore
          : avgScore // ignore: cast_nullable_to_non_nullable
              as double,
      avgPercentage: null == avgPercentage
          ? _value.avgPercentage
          : avgPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      studentsProficient: null == studentsProficient
          ? _value.studentsProficient
          : studentsProficient // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CompetencyStatsImpl implements _CompetencyStats {
  const _$CompetencyStatsImpl(
      {required this.competencyId,
      required this.competencyName,
      required this.questionCount,
      required this.totalMarks,
      required this.avgScore,
      required this.avgPercentage,
      required this.studentsProficient});

  factory _$CompetencyStatsImpl.fromJson(Map<String, dynamic> json) =>
      _$$CompetencyStatsImplFromJson(json);

  @override
  final String competencyId;
  @override
  final String competencyName;
  @override
  final int questionCount;
  @override
  final int totalMarks;
  @override
  final double avgScore;
  @override
  final double avgPercentage;
  @override
  final int studentsProficient;

  @override
  String toString() {
    return 'CompetencyStats(competencyId: $competencyId, competencyName: $competencyName, questionCount: $questionCount, totalMarks: $totalMarks, avgScore: $avgScore, avgPercentage: $avgPercentage, studentsProficient: $studentsProficient)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CompetencyStatsImpl &&
            (identical(other.competencyId, competencyId) ||
                other.competencyId == competencyId) &&
            (identical(other.competencyName, competencyName) ||
                other.competencyName == competencyName) &&
            (identical(other.questionCount, questionCount) ||
                other.questionCount == questionCount) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            (identical(other.avgScore, avgScore) ||
                other.avgScore == avgScore) &&
            (identical(other.avgPercentage, avgPercentage) ||
                other.avgPercentage == avgPercentage) &&
            (identical(other.studentsProficient, studentsProficient) ||
                other.studentsProficient == studentsProficient));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, competencyId, competencyName,
      questionCount, totalMarks, avgScore, avgPercentage, studentsProficient);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CompetencyStatsImplCopyWith<_$CompetencyStatsImpl> get copyWith =>
      __$$CompetencyStatsImplCopyWithImpl<_$CompetencyStatsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CompetencyStatsImplToJson(
      this,
    );
  }
}

abstract class _CompetencyStats implements CompetencyStats {
  const factory _CompetencyStats(
      {required final String competencyId,
      required final String competencyName,
      required final int questionCount,
      required final int totalMarks,
      required final double avgScore,
      required final double avgPercentage,
      required final int studentsProficient}) = _$CompetencyStatsImpl;

  factory _CompetencyStats.fromJson(Map<String, dynamic> json) =
      _$CompetencyStatsImpl.fromJson;

  @override
  String get competencyId;
  @override
  String get competencyName;
  @override
  int get questionCount;
  @override
  int get totalMarks;
  @override
  double get avgScore;
  @override
  double get avgPercentage;
  @override
  int get studentsProficient;
  @override
  @JsonKey(ignore: true)
  _$$CompetencyStatsImplCopyWith<_$CompetencyStatsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DifficultyAnalytics _$DifficultyAnalyticsFromJson(Map<String, dynamic> json) {
  return _DifficultyAnalytics.fromJson(json);
}

/// @nodoc
mixin _$DifficultyAnalytics {
  DifficultyLevelStats get easy => throw _privateConstructorUsedError;
  DifficultyLevelStats get medium => throw _privateConstructorUsedError;
  DifficultyLevelStats get hard => throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $DifficultyAnalyticsCopyWith<DifficultyAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DifficultyAnalyticsCopyWith<$Res> {
  factory $DifficultyAnalyticsCopyWith(
          DifficultyAnalytics value, $Res Function(DifficultyAnalytics) then) =
      _$DifficultyAnalyticsCopyWithImpl<$Res, DifficultyAnalytics>;
  @useResult
  $Res call(
      {DifficultyLevelStats easy,
      DifficultyLevelStats medium,
      DifficultyLevelStats hard,
      List<String> insights});

  $DifficultyLevelStatsCopyWith<$Res> get easy;
  $DifficultyLevelStatsCopyWith<$Res> get medium;
  $DifficultyLevelStatsCopyWith<$Res> get hard;
}

/// @nodoc
class _$DifficultyAnalyticsCopyWithImpl<$Res, $Val extends DifficultyAnalytics>
    implements $DifficultyAnalyticsCopyWith<$Res> {
  _$DifficultyAnalyticsCopyWithImpl(this._value, this._then);

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
    Object? insights = null,
  }) {
    return _then(_value.copyWith(
      easy: null == easy
          ? _value.easy
          : easy // ignore: cast_nullable_to_non_nullable
              as DifficultyLevelStats,
      medium: null == medium
          ? _value.medium
          : medium // ignore: cast_nullable_to_non_nullable
              as DifficultyLevelStats,
      hard: null == hard
          ? _value.hard
          : hard // ignore: cast_nullable_to_non_nullable
              as DifficultyLevelStats,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $DifficultyLevelStatsCopyWith<$Res> get easy {
    return $DifficultyLevelStatsCopyWith<$Res>(_value.easy, (value) {
      return _then(_value.copyWith(easy: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $DifficultyLevelStatsCopyWith<$Res> get medium {
    return $DifficultyLevelStatsCopyWith<$Res>(_value.medium, (value) {
      return _then(_value.copyWith(medium: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $DifficultyLevelStatsCopyWith<$Res> get hard {
    return $DifficultyLevelStatsCopyWith<$Res>(_value.hard, (value) {
      return _then(_value.copyWith(hard: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$DifficultyAnalyticsImplCopyWith<$Res>
    implements $DifficultyAnalyticsCopyWith<$Res> {
  factory _$$DifficultyAnalyticsImplCopyWith(_$DifficultyAnalyticsImpl value,
          $Res Function(_$DifficultyAnalyticsImpl) then) =
      __$$DifficultyAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {DifficultyLevelStats easy,
      DifficultyLevelStats medium,
      DifficultyLevelStats hard,
      List<String> insights});

  @override
  $DifficultyLevelStatsCopyWith<$Res> get easy;
  @override
  $DifficultyLevelStatsCopyWith<$Res> get medium;
  @override
  $DifficultyLevelStatsCopyWith<$Res> get hard;
}

/// @nodoc
class __$$DifficultyAnalyticsImplCopyWithImpl<$Res>
    extends _$DifficultyAnalyticsCopyWithImpl<$Res, _$DifficultyAnalyticsImpl>
    implements _$$DifficultyAnalyticsImplCopyWith<$Res> {
  __$$DifficultyAnalyticsImplCopyWithImpl(_$DifficultyAnalyticsImpl _value,
      $Res Function(_$DifficultyAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? easy = null,
    Object? medium = null,
    Object? hard = null,
    Object? insights = null,
  }) {
    return _then(_$DifficultyAnalyticsImpl(
      easy: null == easy
          ? _value.easy
          : easy // ignore: cast_nullable_to_non_nullable
              as DifficultyLevelStats,
      medium: null == medium
          ? _value.medium
          : medium // ignore: cast_nullable_to_non_nullable
              as DifficultyLevelStats,
      hard: null == hard
          ? _value.hard
          : hard // ignore: cast_nullable_to_non_nullable
              as DifficultyLevelStats,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DifficultyAnalyticsImpl implements _DifficultyAnalytics {
  const _$DifficultyAnalyticsImpl(
      {required this.easy,
      required this.medium,
      required this.hard,
      required final List<String> insights})
      : _insights = insights;

  factory _$DifficultyAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$DifficultyAnalyticsImplFromJson(json);

  @override
  final DifficultyLevelStats easy;
  @override
  final DifficultyLevelStats medium;
  @override
  final DifficultyLevelStats hard;
  final List<String> _insights;
  @override
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  @override
  String toString() {
    return 'DifficultyAnalytics(easy: $easy, medium: $medium, hard: $hard, insights: $insights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DifficultyAnalyticsImpl &&
            (identical(other.easy, easy) || other.easy == easy) &&
            (identical(other.medium, medium) || other.medium == medium) &&
            (identical(other.hard, hard) || other.hard == hard) &&
            const DeepCollectionEquality().equals(other._insights, _insights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, easy, medium, hard,
      const DeepCollectionEquality().hash(_insights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$DifficultyAnalyticsImplCopyWith<_$DifficultyAnalyticsImpl> get copyWith =>
      __$$DifficultyAnalyticsImplCopyWithImpl<_$DifficultyAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DifficultyAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _DifficultyAnalytics implements DifficultyAnalytics {
  const factory _DifficultyAnalytics(
      {required final DifficultyLevelStats easy,
      required final DifficultyLevelStats medium,
      required final DifficultyLevelStats hard,
      required final List<String> insights}) = _$DifficultyAnalyticsImpl;

  factory _DifficultyAnalytics.fromJson(Map<String, dynamic> json) =
      _$DifficultyAnalyticsImpl.fromJson;

  @override
  DifficultyLevelStats get easy;
  @override
  DifficultyLevelStats get medium;
  @override
  DifficultyLevelStats get hard;
  @override
  List<String> get insights;
  @override
  @JsonKey(ignore: true)
  _$$DifficultyAnalyticsImplCopyWith<_$DifficultyAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DifficultyLevelStats _$DifficultyLevelStatsFromJson(Map<String, dynamic> json) {
  return _DifficultyLevelStats.fromJson(json);
}

/// @nodoc
mixin _$DifficultyLevelStats {
  String get level => throw _privateConstructorUsedError;
  int get questionCount => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;
  double get avgScore => throw _privateConstructorUsedError;
  double get avgPercentage => throw _privateConstructorUsedError;
  double get discriminationIndex => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $DifficultyLevelStatsCopyWith<DifficultyLevelStats> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DifficultyLevelStatsCopyWith<$Res> {
  factory $DifficultyLevelStatsCopyWith(DifficultyLevelStats value,
          $Res Function(DifficultyLevelStats) then) =
      _$DifficultyLevelStatsCopyWithImpl<$Res, DifficultyLevelStats>;
  @useResult
  $Res call(
      {String level,
      int questionCount,
      int totalMarks,
      double avgScore,
      double avgPercentage,
      double discriminationIndex});
}

/// @nodoc
class _$DifficultyLevelStatsCopyWithImpl<$Res,
        $Val extends DifficultyLevelStats>
    implements $DifficultyLevelStatsCopyWith<$Res> {
  _$DifficultyLevelStatsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? avgScore = null,
    Object? avgPercentage = null,
    Object? discriminationIndex = null,
  }) {
    return _then(_value.copyWith(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      avgScore: null == avgScore
          ? _value.avgScore
          : avgScore // ignore: cast_nullable_to_non_nullable
              as double,
      avgPercentage: null == avgPercentage
          ? _value.avgPercentage
          : avgPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      discriminationIndex: null == discriminationIndex
          ? _value.discriminationIndex
          : discriminationIndex // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DifficultyLevelStatsImplCopyWith<$Res>
    implements $DifficultyLevelStatsCopyWith<$Res> {
  factory _$$DifficultyLevelStatsImplCopyWith(_$DifficultyLevelStatsImpl value,
          $Res Function(_$DifficultyLevelStatsImpl) then) =
      __$$DifficultyLevelStatsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String level,
      int questionCount,
      int totalMarks,
      double avgScore,
      double avgPercentage,
      double discriminationIndex});
}

/// @nodoc
class __$$DifficultyLevelStatsImplCopyWithImpl<$Res>
    extends _$DifficultyLevelStatsCopyWithImpl<$Res, _$DifficultyLevelStatsImpl>
    implements _$$DifficultyLevelStatsImplCopyWith<$Res> {
  __$$DifficultyLevelStatsImplCopyWithImpl(_$DifficultyLevelStatsImpl _value,
      $Res Function(_$DifficultyLevelStatsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? questionCount = null,
    Object? totalMarks = null,
    Object? avgScore = null,
    Object? avgPercentage = null,
    Object? discriminationIndex = null,
  }) {
    return _then(_$DifficultyLevelStatsImpl(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      avgScore: null == avgScore
          ? _value.avgScore
          : avgScore // ignore: cast_nullable_to_non_nullable
              as double,
      avgPercentage: null == avgPercentage
          ? _value.avgPercentage
          : avgPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      discriminationIndex: null == discriminationIndex
          ? _value.discriminationIndex
          : discriminationIndex // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DifficultyLevelStatsImpl implements _DifficultyLevelStats {
  const _$DifficultyLevelStatsImpl(
      {required this.level,
      required this.questionCount,
      required this.totalMarks,
      required this.avgScore,
      required this.avgPercentage,
      required this.discriminationIndex});

  factory _$DifficultyLevelStatsImpl.fromJson(Map<String, dynamic> json) =>
      _$$DifficultyLevelStatsImplFromJson(json);

  @override
  final String level;
  @override
  final int questionCount;
  @override
  final int totalMarks;
  @override
  final double avgScore;
  @override
  final double avgPercentage;
  @override
  final double discriminationIndex;

  @override
  String toString() {
    return 'DifficultyLevelStats(level: $level, questionCount: $questionCount, totalMarks: $totalMarks, avgScore: $avgScore, avgPercentage: $avgPercentage, discriminationIndex: $discriminationIndex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DifficultyLevelStatsImpl &&
            (identical(other.level, level) || other.level == level) &&
            (identical(other.questionCount, questionCount) ||
                other.questionCount == questionCount) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            (identical(other.avgScore, avgScore) ||
                other.avgScore == avgScore) &&
            (identical(other.avgPercentage, avgPercentage) ||
                other.avgPercentage == avgPercentage) &&
            (identical(other.discriminationIndex, discriminationIndex) ||
                other.discriminationIndex == discriminationIndex));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, level, questionCount, totalMarks,
      avgScore, avgPercentage, discriminationIndex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$DifficultyLevelStatsImplCopyWith<_$DifficultyLevelStatsImpl>
      get copyWith =>
          __$$DifficultyLevelStatsImplCopyWithImpl<_$DifficultyLevelStatsImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DifficultyLevelStatsImplToJson(
      this,
    );
  }
}

abstract class _DifficultyLevelStats implements DifficultyLevelStats {
  const factory _DifficultyLevelStats(
      {required final String level,
      required final int questionCount,
      required final int totalMarks,
      required final double avgScore,
      required final double avgPercentage,
      required final double discriminationIndex}) = _$DifficultyLevelStatsImpl;

  factory _DifficultyLevelStats.fromJson(Map<String, dynamic> json) =
      _$DifficultyLevelStatsImpl.fromJson;

  @override
  String get level;
  @override
  int get questionCount;
  @override
  int get totalMarks;
  @override
  double get avgScore;
  @override
  double get avgPercentage;
  @override
  double get discriminationIndex;
  @override
  @JsonKey(ignore: true)
  _$$DifficultyLevelStatsImplCopyWith<_$DifficultyLevelStatsImpl>
      get copyWith => throw _privateConstructorUsedError;
}

TimeAnalytics _$TimeAnalyticsFromJson(Map<String, dynamic> json) {
  return _TimeAnalytics.fromJson(json);
}

/// @nodoc
mixin _$TimeAnalytics {
  double get avgTimePerQuestion => throw _privateConstructorUsedError;
  double get avgTotalTime => throw _privateConstructorUsedError;
  Map<String, double> get timeBySection => throw _privateConstructorUsedError;
  Map<String, double> get timeByQuestion => throw _privateConstructorUsedError;
  int get studentsFinishedEarly => throw _privateConstructorUsedError;
  int get studentsRanOutOfTime => throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $TimeAnalyticsCopyWith<TimeAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TimeAnalyticsCopyWith<$Res> {
  factory $TimeAnalyticsCopyWith(
          TimeAnalytics value, $Res Function(TimeAnalytics) then) =
      _$TimeAnalyticsCopyWithImpl<$Res, TimeAnalytics>;
  @useResult
  $Res call(
      {double avgTimePerQuestion,
      double avgTotalTime,
      Map<String, double> timeBySection,
      Map<String, double> timeByQuestion,
      int studentsFinishedEarly,
      int studentsRanOutOfTime,
      List<String> insights});
}

/// @nodoc
class _$TimeAnalyticsCopyWithImpl<$Res, $Val extends TimeAnalytics>
    implements $TimeAnalyticsCopyWith<$Res> {
  _$TimeAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? avgTimePerQuestion = null,
    Object? avgTotalTime = null,
    Object? timeBySection = null,
    Object? timeByQuestion = null,
    Object? studentsFinishedEarly = null,
    Object? studentsRanOutOfTime = null,
    Object? insights = null,
  }) {
    return _then(_value.copyWith(
      avgTimePerQuestion: null == avgTimePerQuestion
          ? _value.avgTimePerQuestion
          : avgTimePerQuestion // ignore: cast_nullable_to_non_nullable
              as double,
      avgTotalTime: null == avgTotalTime
          ? _value.avgTotalTime
          : avgTotalTime // ignore: cast_nullable_to_non_nullable
              as double,
      timeBySection: null == timeBySection
          ? _value.timeBySection
          : timeBySection // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      timeByQuestion: null == timeByQuestion
          ? _value.timeByQuestion
          : timeByQuestion // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      studentsFinishedEarly: null == studentsFinishedEarly
          ? _value.studentsFinishedEarly
          : studentsFinishedEarly // ignore: cast_nullable_to_non_nullable
              as int,
      studentsRanOutOfTime: null == studentsRanOutOfTime
          ? _value.studentsRanOutOfTime
          : studentsRanOutOfTime // ignore: cast_nullable_to_non_nullable
              as int,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TimeAnalyticsImplCopyWith<$Res>
    implements $TimeAnalyticsCopyWith<$Res> {
  factory _$$TimeAnalyticsImplCopyWith(
          _$TimeAnalyticsImpl value, $Res Function(_$TimeAnalyticsImpl) then) =
      __$$TimeAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double avgTimePerQuestion,
      double avgTotalTime,
      Map<String, double> timeBySection,
      Map<String, double> timeByQuestion,
      int studentsFinishedEarly,
      int studentsRanOutOfTime,
      List<String> insights});
}

/// @nodoc
class __$$TimeAnalyticsImplCopyWithImpl<$Res>
    extends _$TimeAnalyticsCopyWithImpl<$Res, _$TimeAnalyticsImpl>
    implements _$$TimeAnalyticsImplCopyWith<$Res> {
  __$$TimeAnalyticsImplCopyWithImpl(
      _$TimeAnalyticsImpl _value, $Res Function(_$TimeAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? avgTimePerQuestion = null,
    Object? avgTotalTime = null,
    Object? timeBySection = null,
    Object? timeByQuestion = null,
    Object? studentsFinishedEarly = null,
    Object? studentsRanOutOfTime = null,
    Object? insights = null,
  }) {
    return _then(_$TimeAnalyticsImpl(
      avgTimePerQuestion: null == avgTimePerQuestion
          ? _value.avgTimePerQuestion
          : avgTimePerQuestion // ignore: cast_nullable_to_non_nullable
              as double,
      avgTotalTime: null == avgTotalTime
          ? _value.avgTotalTime
          : avgTotalTime // ignore: cast_nullable_to_non_nullable
              as double,
      timeBySection: null == timeBySection
          ? _value._timeBySection
          : timeBySection // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      timeByQuestion: null == timeByQuestion
          ? _value._timeByQuestion
          : timeByQuestion // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      studentsFinishedEarly: null == studentsFinishedEarly
          ? _value.studentsFinishedEarly
          : studentsFinishedEarly // ignore: cast_nullable_to_non_nullable
              as int,
      studentsRanOutOfTime: null == studentsRanOutOfTime
          ? _value.studentsRanOutOfTime
          : studentsRanOutOfTime // ignore: cast_nullable_to_non_nullable
              as int,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TimeAnalyticsImpl implements _TimeAnalytics {
  const _$TimeAnalyticsImpl(
      {required this.avgTimePerQuestion,
      required this.avgTotalTime,
      required final Map<String, double> timeBySection,
      required final Map<String, double> timeByQuestion,
      required this.studentsFinishedEarly,
      required this.studentsRanOutOfTime,
      required final List<String> insights})
      : _timeBySection = timeBySection,
        _timeByQuestion = timeByQuestion,
        _insights = insights;

  factory _$TimeAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$TimeAnalyticsImplFromJson(json);

  @override
  final double avgTimePerQuestion;
  @override
  final double avgTotalTime;
  final Map<String, double> _timeBySection;
  @override
  Map<String, double> get timeBySection {
    if (_timeBySection is EqualUnmodifiableMapView) return _timeBySection;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_timeBySection);
  }

  final Map<String, double> _timeByQuestion;
  @override
  Map<String, double> get timeByQuestion {
    if (_timeByQuestion is EqualUnmodifiableMapView) return _timeByQuestion;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_timeByQuestion);
  }

  @override
  final int studentsFinishedEarly;
  @override
  final int studentsRanOutOfTime;
  final List<String> _insights;
  @override
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  @override
  String toString() {
    return 'TimeAnalytics(avgTimePerQuestion: $avgTimePerQuestion, avgTotalTime: $avgTotalTime, timeBySection: $timeBySection, timeByQuestion: $timeByQuestion, studentsFinishedEarly: $studentsFinishedEarly, studentsRanOutOfTime: $studentsRanOutOfTime, insights: $insights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TimeAnalyticsImpl &&
            (identical(other.avgTimePerQuestion, avgTimePerQuestion) ||
                other.avgTimePerQuestion == avgTimePerQuestion) &&
            (identical(other.avgTotalTime, avgTotalTime) ||
                other.avgTotalTime == avgTotalTime) &&
            const DeepCollectionEquality()
                .equals(other._timeBySection, _timeBySection) &&
            const DeepCollectionEquality()
                .equals(other._timeByQuestion, _timeByQuestion) &&
            (identical(other.studentsFinishedEarly, studentsFinishedEarly) ||
                other.studentsFinishedEarly == studentsFinishedEarly) &&
            (identical(other.studentsRanOutOfTime, studentsRanOutOfTime) ||
                other.studentsRanOutOfTime == studentsRanOutOfTime) &&
            const DeepCollectionEquality().equals(other._insights, _insights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      avgTimePerQuestion,
      avgTotalTime,
      const DeepCollectionEquality().hash(_timeBySection),
      const DeepCollectionEquality().hash(_timeByQuestion),
      studentsFinishedEarly,
      studentsRanOutOfTime,
      const DeepCollectionEquality().hash(_insights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$TimeAnalyticsImplCopyWith<_$TimeAnalyticsImpl> get copyWith =>
      __$$TimeAnalyticsImplCopyWithImpl<_$TimeAnalyticsImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TimeAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _TimeAnalytics implements TimeAnalytics {
  const factory _TimeAnalytics(
      {required final double avgTimePerQuestion,
      required final double avgTotalTime,
      required final Map<String, double> timeBySection,
      required final Map<String, double> timeByQuestion,
      required final int studentsFinishedEarly,
      required final int studentsRanOutOfTime,
      required final List<String> insights}) = _$TimeAnalyticsImpl;

  factory _TimeAnalytics.fromJson(Map<String, dynamic> json) =
      _$TimeAnalyticsImpl.fromJson;

  @override
  double get avgTimePerQuestion;
  @override
  double get avgTotalTime;
  @override
  Map<String, double> get timeBySection;
  @override
  Map<String, double> get timeByQuestion;
  @override
  int get studentsFinishedEarly;
  @override
  int get studentsRanOutOfTime;
  @override
  List<String> get insights;
  @override
  @JsonKey(ignore: true)
  _$$TimeAnalyticsImplCopyWith<_$TimeAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CommonError _$CommonErrorFromJson(Map<String, dynamic> json) {
  return _CommonError.fromJson(json);
}

/// @nodoc
mixin _$CommonError {
  String get id => throw _privateConstructorUsedError;
  String get questionId => throw _privateConstructorUsedError;
  int get questionNumber => throw _privateConstructorUsedError;
  String get errorType => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  int get frequency => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  List<String> get exampleAnswers => throw _privateConstructorUsedError;
  String get remediationHint => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CommonErrorCopyWith<CommonError> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CommonErrorCopyWith<$Res> {
  factory $CommonErrorCopyWith(
          CommonError value, $Res Function(CommonError) then) =
      _$CommonErrorCopyWithImpl<$Res, CommonError>;
  @useResult
  $Res call(
      {String id,
      String questionId,
      int questionNumber,
      String errorType,
      String description,
      int frequency,
      double percentage,
      List<String> exampleAnswers,
      String remediationHint});
}

/// @nodoc
class _$CommonErrorCopyWithImpl<$Res, $Val extends CommonError>
    implements $CommonErrorCopyWith<$Res> {
  _$CommonErrorCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? questionId = null,
    Object? questionNumber = null,
    Object? errorType = null,
    Object? description = null,
    Object? frequency = null,
    Object? percentage = null,
    Object? exampleAnswers = null,
    Object? remediationHint = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      errorType: null == errorType
          ? _value.errorType
          : errorType // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      frequency: null == frequency
          ? _value.frequency
          : frequency // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      exampleAnswers: null == exampleAnswers
          ? _value.exampleAnswers
          : exampleAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
      remediationHint: null == remediationHint
          ? _value.remediationHint
          : remediationHint // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CommonErrorImplCopyWith<$Res>
    implements $CommonErrorCopyWith<$Res> {
  factory _$$CommonErrorImplCopyWith(
          _$CommonErrorImpl value, $Res Function(_$CommonErrorImpl) then) =
      __$$CommonErrorImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String questionId,
      int questionNumber,
      String errorType,
      String description,
      int frequency,
      double percentage,
      List<String> exampleAnswers,
      String remediationHint});
}

/// @nodoc
class __$$CommonErrorImplCopyWithImpl<$Res>
    extends _$CommonErrorCopyWithImpl<$Res, _$CommonErrorImpl>
    implements _$$CommonErrorImplCopyWith<$Res> {
  __$$CommonErrorImplCopyWithImpl(
      _$CommonErrorImpl _value, $Res Function(_$CommonErrorImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? questionId = null,
    Object? questionNumber = null,
    Object? errorType = null,
    Object? description = null,
    Object? frequency = null,
    Object? percentage = null,
    Object? exampleAnswers = null,
    Object? remediationHint = null,
  }) {
    return _then(_$CommonErrorImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      errorType: null == errorType
          ? _value.errorType
          : errorType // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      frequency: null == frequency
          ? _value.frequency
          : frequency // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      exampleAnswers: null == exampleAnswers
          ? _value._exampleAnswers
          : exampleAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
      remediationHint: null == remediationHint
          ? _value.remediationHint
          : remediationHint // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CommonErrorImpl implements _CommonError {
  const _$CommonErrorImpl(
      {required this.id,
      required this.questionId,
      required this.questionNumber,
      required this.errorType,
      required this.description,
      required this.frequency,
      required this.percentage,
      required final List<String> exampleAnswers,
      required this.remediationHint})
      : _exampleAnswers = exampleAnswers;

  factory _$CommonErrorImpl.fromJson(Map<String, dynamic> json) =>
      _$$CommonErrorImplFromJson(json);

  @override
  final String id;
  @override
  final String questionId;
  @override
  final int questionNumber;
  @override
  final String errorType;
  @override
  final String description;
  @override
  final int frequency;
  @override
  final double percentage;
  final List<String> _exampleAnswers;
  @override
  List<String> get exampleAnswers {
    if (_exampleAnswers is EqualUnmodifiableListView) return _exampleAnswers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_exampleAnswers);
  }

  @override
  final String remediationHint;

  @override
  String toString() {
    return 'CommonError(id: $id, questionId: $questionId, questionNumber: $questionNumber, errorType: $errorType, description: $description, frequency: $frequency, percentage: $percentage, exampleAnswers: $exampleAnswers, remediationHint: $remediationHint)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CommonErrorImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.questionNumber, questionNumber) ||
                other.questionNumber == questionNumber) &&
            (identical(other.errorType, errorType) ||
                other.errorType == errorType) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.frequency, frequency) ||
                other.frequency == frequency) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            const DeepCollectionEquality()
                .equals(other._exampleAnswers, _exampleAnswers) &&
            (identical(other.remediationHint, remediationHint) ||
                other.remediationHint == remediationHint));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      questionId,
      questionNumber,
      errorType,
      description,
      frequency,
      percentage,
      const DeepCollectionEquality().hash(_exampleAnswers),
      remediationHint);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CommonErrorImplCopyWith<_$CommonErrorImpl> get copyWith =>
      __$$CommonErrorImplCopyWithImpl<_$CommonErrorImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CommonErrorImplToJson(
      this,
    );
  }
}

abstract class _CommonError implements CommonError {
  const factory _CommonError(
      {required final String id,
      required final String questionId,
      required final int questionNumber,
      required final String errorType,
      required final String description,
      required final int frequency,
      required final double percentage,
      required final List<String> exampleAnswers,
      required final String remediationHint}) = _$CommonErrorImpl;

  factory _CommonError.fromJson(Map<String, dynamic> json) =
      _$CommonErrorImpl.fromJson;

  @override
  String get id;
  @override
  String get questionId;
  @override
  int get questionNumber;
  @override
  String get errorType;
  @override
  String get description;
  @override
  int get frequency;
  @override
  double get percentage;
  @override
  List<String> get exampleAnswers;
  @override
  String get remediationHint;
  @override
  @JsonKey(ignore: true)
  _$$CommonErrorImplCopyWith<_$CommonErrorImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ClassAnalytics _$ClassAnalyticsFromJson(Map<String, dynamic> json) {
  return _ClassAnalytics.fromJson(json);
}

/// @nodoc
mixin _$ClassAnalytics {
  String get classId => throw _privateConstructorUsedError;
  String get className => throw _privateConstructorUsedError;
  int get totalStudents => throw _privateConstructorUsedError;
  List<AssessmentAnalytics> get assessments =>
      throw _privateConstructorUsedError;
  Map<String, SubjectMastery> get subjectMastery =>
      throw _privateConstructorUsedError;
  List<ConceptGap> get classWideGaps => throw _privateConstructorUsedError;
  List<StudentPerformance> get topPerformers =>
      throw _privateConstructorUsedError;
  List<StudentPerformance> get atRiskStudents =>
      throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ClassAnalyticsCopyWith<ClassAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ClassAnalyticsCopyWith<$Res> {
  factory $ClassAnalyticsCopyWith(
          ClassAnalytics value, $Res Function(ClassAnalytics) then) =
      _$ClassAnalyticsCopyWithImpl<$Res, ClassAnalytics>;
  @useResult
  $Res call(
      {String classId,
      String className,
      int totalStudents,
      List<AssessmentAnalytics> assessments,
      Map<String, SubjectMastery> subjectMastery,
      List<ConceptGap> classWideGaps,
      List<StudentPerformance> topPerformers,
      List<StudentPerformance> atRiskStudents,
      DateTime generatedAt});
}

/// @nodoc
class _$ClassAnalyticsCopyWithImpl<$Res, $Val extends ClassAnalytics>
    implements $ClassAnalyticsCopyWith<$Res> {
  _$ClassAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? classId = null,
    Object? className = null,
    Object? totalStudents = null,
    Object? assessments = null,
    Object? subjectMastery = null,
    Object? classWideGaps = null,
    Object? topPerformers = null,
    Object? atRiskStudents = null,
    Object? generatedAt = null,
  }) {
    return _then(_value.copyWith(
      classId: null == classId
          ? _value.classId
          : classId // ignore: cast_nullable_to_non_nullable
              as String,
      className: null == className
          ? _value.className
          : className // ignore: cast_nullable_to_non_nullable
              as String,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      assessments: null == assessments
          ? _value.assessments
          : assessments // ignore: cast_nullable_to_non_nullable
              as List<AssessmentAnalytics>,
      subjectMastery: null == subjectMastery
          ? _value.subjectMastery
          : subjectMastery // ignore: cast_nullable_to_non_nullable
              as Map<String, SubjectMastery>,
      classWideGaps: null == classWideGaps
          ? _value.classWideGaps
          : classWideGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      topPerformers: null == topPerformers
          ? _value.topPerformers
          : topPerformers // ignore: cast_nullable_to_non_nullable
              as List<StudentPerformance>,
      atRiskStudents: null == atRiskStudents
          ? _value.atRiskStudents
          : atRiskStudents // ignore: cast_nullable_to_non_nullable
              as List<StudentPerformance>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ClassAnalyticsImplCopyWith<$Res>
    implements $ClassAnalyticsCopyWith<$Res> {
  factory _$$ClassAnalyticsImplCopyWith(_$ClassAnalyticsImpl value,
          $Res Function(_$ClassAnalyticsImpl) then) =
      __$$ClassAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String classId,
      String className,
      int totalStudents,
      List<AssessmentAnalytics> assessments,
      Map<String, SubjectMastery> subjectMastery,
      List<ConceptGap> classWideGaps,
      List<StudentPerformance> topPerformers,
      List<StudentPerformance> atRiskStudents,
      DateTime generatedAt});
}

/// @nodoc
class __$$ClassAnalyticsImplCopyWithImpl<$Res>
    extends _$ClassAnalyticsCopyWithImpl<$Res, _$ClassAnalyticsImpl>
    implements _$$ClassAnalyticsImplCopyWith<$Res> {
  __$$ClassAnalyticsImplCopyWithImpl(
      _$ClassAnalyticsImpl _value, $Res Function(_$ClassAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? classId = null,
    Object? className = null,
    Object? totalStudents = null,
    Object? assessments = null,
    Object? subjectMastery = null,
    Object? classWideGaps = null,
    Object? topPerformers = null,
    Object? atRiskStudents = null,
    Object? generatedAt = null,
  }) {
    return _then(_$ClassAnalyticsImpl(
      classId: null == classId
          ? _value.classId
          : classId // ignore: cast_nullable_to_non_nullable
              as String,
      className: null == className
          ? _value.className
          : className // ignore: cast_nullable_to_non_nullable
              as String,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      assessments: null == assessments
          ? _value._assessments
          : assessments // ignore: cast_nullable_to_non_nullable
              as List<AssessmentAnalytics>,
      subjectMastery: null == subjectMastery
          ? _value._subjectMastery
          : subjectMastery // ignore: cast_nullable_to_non_nullable
              as Map<String, SubjectMastery>,
      classWideGaps: null == classWideGaps
          ? _value._classWideGaps
          : classWideGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      topPerformers: null == topPerformers
          ? _value._topPerformers
          : topPerformers // ignore: cast_nullable_to_non_nullable
              as List<StudentPerformance>,
      atRiskStudents: null == atRiskStudents
          ? _value._atRiskStudents
          : atRiskStudents // ignore: cast_nullable_to_non_nullable
              as List<StudentPerformance>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ClassAnalyticsImpl implements _ClassAnalytics {
  const _$ClassAnalyticsImpl(
      {required this.classId,
      required this.className,
      required this.totalStudents,
      required final List<AssessmentAnalytics> assessments,
      required final Map<String, SubjectMastery> subjectMastery,
      required final List<ConceptGap> classWideGaps,
      required final List<StudentPerformance> topPerformers,
      required final List<StudentPerformance> atRiskStudents,
      required this.generatedAt})
      : _assessments = assessments,
        _subjectMastery = subjectMastery,
        _classWideGaps = classWideGaps,
        _topPerformers = topPerformers,
        _atRiskStudents = atRiskStudents;

  factory _$ClassAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$ClassAnalyticsImplFromJson(json);

  @override
  final String classId;
  @override
  final String className;
  @override
  final int totalStudents;
  final List<AssessmentAnalytics> _assessments;
  @override
  List<AssessmentAnalytics> get assessments {
    if (_assessments is EqualUnmodifiableListView) return _assessments;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_assessments);
  }

  final Map<String, SubjectMastery> _subjectMastery;
  @override
  Map<String, SubjectMastery> get subjectMastery {
    if (_subjectMastery is EqualUnmodifiableMapView) return _subjectMastery;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_subjectMastery);
  }

  final List<ConceptGap> _classWideGaps;
  @override
  List<ConceptGap> get classWideGaps {
    if (_classWideGaps is EqualUnmodifiableListView) return _classWideGaps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_classWideGaps);
  }

  final List<StudentPerformance> _topPerformers;
  @override
  List<StudentPerformance> get topPerformers {
    if (_topPerformers is EqualUnmodifiableListView) return _topPerformers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_topPerformers);
  }

  final List<StudentPerformance> _atRiskStudents;
  @override
  List<StudentPerformance> get atRiskStudents {
    if (_atRiskStudents is EqualUnmodifiableListView) return _atRiskStudents;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_atRiskStudents);
  }

  @override
  final DateTime generatedAt;

  @override
  String toString() {
    return 'ClassAnalytics(classId: $classId, className: $className, totalStudents: $totalStudents, assessments: $assessments, subjectMastery: $subjectMastery, classWideGaps: $classWideGaps, topPerformers: $topPerformers, atRiskStudents: $atRiskStudents, generatedAt: $generatedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ClassAnalyticsImpl &&
            (identical(other.classId, classId) || other.classId == classId) &&
            (identical(other.className, className) ||
                other.className == className) &&
            (identical(other.totalStudents, totalStudents) ||
                other.totalStudents == totalStudents) &&
            const DeepCollectionEquality()
                .equals(other._assessments, _assessments) &&
            const DeepCollectionEquality()
                .equals(other._subjectMastery, _subjectMastery) &&
            const DeepCollectionEquality()
                .equals(other._classWideGaps, _classWideGaps) &&
            const DeepCollectionEquality()
                .equals(other._topPerformers, _topPerformers) &&
            const DeepCollectionEquality()
                .equals(other._atRiskStudents, _atRiskStudents) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      classId,
      className,
      totalStudents,
      const DeepCollectionEquality().hash(_assessments),
      const DeepCollectionEquality().hash(_subjectMastery),
      const DeepCollectionEquality().hash(_classWideGaps),
      const DeepCollectionEquality().hash(_topPerformers),
      const DeepCollectionEquality().hash(_atRiskStudents),
      generatedAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ClassAnalyticsImplCopyWith<_$ClassAnalyticsImpl> get copyWith =>
      __$$ClassAnalyticsImplCopyWithImpl<_$ClassAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ClassAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _ClassAnalytics implements ClassAnalytics {
  const factory _ClassAnalytics(
      {required final String classId,
      required final String className,
      required final int totalStudents,
      required final List<AssessmentAnalytics> assessments,
      required final Map<String, SubjectMastery> subjectMastery,
      required final List<ConceptGap> classWideGaps,
      required final List<StudentPerformance> topPerformers,
      required final List<StudentPerformance> atRiskStudents,
      required final DateTime generatedAt}) = _$ClassAnalyticsImpl;

  factory _ClassAnalytics.fromJson(Map<String, dynamic> json) =
      _$ClassAnalyticsImpl.fromJson;

  @override
  String get classId;
  @override
  String get className;
  @override
  int get totalStudents;
  @override
  List<AssessmentAnalytics> get assessments;
  @override
  Map<String, SubjectMastery> get subjectMastery;
  @override
  List<ConceptGap> get classWideGaps;
  @override
  List<StudentPerformance> get topPerformers;
  @override
  List<StudentPerformance> get atRiskStudents;
  @override
  DateTime get generatedAt;
  @override
  @JsonKey(ignore: true)
  _$$ClassAnalyticsImplCopyWith<_$ClassAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

StudentAnalytics _$StudentAnalyticsFromJson(Map<String, dynamic> json) {
  return _StudentAnalytics.fromJson(json);
}

/// @nodoc
mixin _$StudentAnalytics {
  String get studentId => throw _privateConstructorUsedError;
  String get studentName => throw _privateConstructorUsedError;
  String get grade => throw _privateConstructorUsedError;
  Map<String, SubjectMastery> get subjectMastery =>
      throw _privateConstructorUsedError;
  List<AssessmentAnalytics> get assessmentHistory =>
      throw _privateConstructorUsedError;
  List<MisconceptionFlag> get activeMisconceptions =>
      throw _privateConstructorUsedError;
  List<ConceptGap> get conceptGaps => throw _privateConstructorUsedError;
  List<ActionableRecommendation> get recommendations =>
      throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $StudentAnalyticsCopyWith<StudentAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StudentAnalyticsCopyWith<$Res> {
  factory $StudentAnalyticsCopyWith(
          StudentAnalytics value, $Res Function(StudentAnalytics) then) =
      _$StudentAnalyticsCopyWithImpl<$Res, StudentAnalytics>;
  @useResult
  $Res call(
      {String studentId,
      String studentName,
      String grade,
      Map<String, SubjectMastery> subjectMastery,
      List<AssessmentAnalytics> assessmentHistory,
      List<MisconceptionFlag> activeMisconceptions,
      List<ConceptGap> conceptGaps,
      List<ActionableRecommendation> recommendations,
      DateTime generatedAt});
}

/// @nodoc
class _$StudentAnalyticsCopyWithImpl<$Res, $Val extends StudentAnalytics>
    implements $StudentAnalyticsCopyWith<$Res> {
  _$StudentAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? studentName = null,
    Object? grade = null,
    Object? subjectMastery = null,
    Object? assessmentHistory = null,
    Object? activeMisconceptions = null,
    Object? conceptGaps = null,
    Object? recommendations = null,
    Object? generatedAt = null,
  }) {
    return _then(_value.copyWith(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      subjectMastery: null == subjectMastery
          ? _value.subjectMastery
          : subjectMastery // ignore: cast_nullable_to_non_nullable
              as Map<String, SubjectMastery>,
      assessmentHistory: null == assessmentHistory
          ? _value.assessmentHistory
          : assessmentHistory // ignore: cast_nullable_to_non_nullable
              as List<AssessmentAnalytics>,
      activeMisconceptions: null == activeMisconceptions
          ? _value.activeMisconceptions
          : activeMisconceptions // ignore: cast_nullable_to_non_nullable
              as List<MisconceptionFlag>,
      conceptGaps: null == conceptGaps
          ? _value.conceptGaps
          : conceptGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      recommendations: null == recommendations
          ? _value.recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$StudentAnalyticsImplCopyWith<$Res>
    implements $StudentAnalyticsCopyWith<$Res> {
  factory _$$StudentAnalyticsImplCopyWith(_$StudentAnalyticsImpl value,
          $Res Function(_$StudentAnalyticsImpl) then) =
      __$$StudentAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String studentId,
      String studentName,
      String grade,
      Map<String, SubjectMastery> subjectMastery,
      List<AssessmentAnalytics> assessmentHistory,
      List<MisconceptionFlag> activeMisconceptions,
      List<ConceptGap> conceptGaps,
      List<ActionableRecommendation> recommendations,
      DateTime generatedAt});
}

/// @nodoc
class __$$StudentAnalyticsImplCopyWithImpl<$Res>
    extends _$StudentAnalyticsCopyWithImpl<$Res, _$StudentAnalyticsImpl>
    implements _$$StudentAnalyticsImplCopyWith<$Res> {
  __$$StudentAnalyticsImplCopyWithImpl(_$StudentAnalyticsImpl _value,
      $Res Function(_$StudentAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? studentName = null,
    Object? grade = null,
    Object? subjectMastery = null,
    Object? assessmentHistory = null,
    Object? activeMisconceptions = null,
    Object? conceptGaps = null,
    Object? recommendations = null,
    Object? generatedAt = null,
  }) {
    return _then(_$StudentAnalyticsImpl(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      subjectMastery: null == subjectMastery
          ? _value._subjectMastery
          : subjectMastery // ignore: cast_nullable_to_non_nullable
              as Map<String, SubjectMastery>,
      assessmentHistory: null == assessmentHistory
          ? _value._assessmentHistory
          : assessmentHistory // ignore: cast_nullable_to_non_nullable
              as List<AssessmentAnalytics>,
      activeMisconceptions: null == activeMisconceptions
          ? _value._activeMisconceptions
          : activeMisconceptions // ignore: cast_nullable_to_non_nullable
              as List<MisconceptionFlag>,
      conceptGaps: null == conceptGaps
          ? _value._conceptGaps
          : conceptGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      recommendations: null == recommendations
          ? _value._recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StudentAnalyticsImpl implements _StudentAnalytics {
  const _$StudentAnalyticsImpl(
      {required this.studentId,
      required this.studentName,
      required this.grade,
      required final Map<String, SubjectMastery> subjectMastery,
      required final List<AssessmentAnalytics> assessmentHistory,
      required final List<MisconceptionFlag> activeMisconceptions,
      required final List<ConceptGap> conceptGaps,
      required final List<ActionableRecommendation> recommendations,
      required this.generatedAt})
      : _subjectMastery = subjectMastery,
        _assessmentHistory = assessmentHistory,
        _activeMisconceptions = activeMisconceptions,
        _conceptGaps = conceptGaps,
        _recommendations = recommendations;

  factory _$StudentAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$StudentAnalyticsImplFromJson(json);

  @override
  final String studentId;
  @override
  final String studentName;
  @override
  final String grade;
  final Map<String, SubjectMastery> _subjectMastery;
  @override
  Map<String, SubjectMastery> get subjectMastery {
    if (_subjectMastery is EqualUnmodifiableMapView) return _subjectMastery;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_subjectMastery);
  }

  final List<AssessmentAnalytics> _assessmentHistory;
  @override
  List<AssessmentAnalytics> get assessmentHistory {
    if (_assessmentHistory is EqualUnmodifiableListView)
      return _assessmentHistory;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_assessmentHistory);
  }

  final List<MisconceptionFlag> _activeMisconceptions;
  @override
  List<MisconceptionFlag> get activeMisconceptions {
    if (_activeMisconceptions is EqualUnmodifiableListView)
      return _activeMisconceptions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_activeMisconceptions);
  }

  final List<ConceptGap> _conceptGaps;
  @override
  List<ConceptGap> get conceptGaps {
    if (_conceptGaps is EqualUnmodifiableListView) return _conceptGaps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_conceptGaps);
  }

  final List<ActionableRecommendation> _recommendations;
  @override
  List<ActionableRecommendation> get recommendations {
    if (_recommendations is EqualUnmodifiableListView) return _recommendations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendations);
  }

  @override
  final DateTime generatedAt;

  @override
  String toString() {
    return 'StudentAnalytics(studentId: $studentId, studentName: $studentName, grade: $grade, subjectMastery: $subjectMastery, assessmentHistory: $assessmentHistory, activeMisconceptions: $activeMisconceptions, conceptGaps: $conceptGaps, recommendations: $recommendations, generatedAt: $generatedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StudentAnalyticsImpl &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.studentName, studentName) ||
                other.studentName == studentName) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality()
                .equals(other._subjectMastery, _subjectMastery) &&
            const DeepCollectionEquality()
                .equals(other._assessmentHistory, _assessmentHistory) &&
            const DeepCollectionEquality()
                .equals(other._activeMisconceptions, _activeMisconceptions) &&
            const DeepCollectionEquality()
                .equals(other._conceptGaps, _conceptGaps) &&
            const DeepCollectionEquality()
                .equals(other._recommendations, _recommendations) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      studentId,
      studentName,
      grade,
      const DeepCollectionEquality().hash(_subjectMastery),
      const DeepCollectionEquality().hash(_assessmentHistory),
      const DeepCollectionEquality().hash(_activeMisconceptions),
      const DeepCollectionEquality().hash(_conceptGaps),
      const DeepCollectionEquality().hash(_recommendations),
      generatedAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$StudentAnalyticsImplCopyWith<_$StudentAnalyticsImpl> get copyWith =>
      __$$StudentAnalyticsImplCopyWithImpl<_$StudentAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StudentAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _StudentAnalytics implements StudentAnalytics {
  const factory _StudentAnalytics(
      {required final String studentId,
      required final String studentName,
      required final String grade,
      required final Map<String, SubjectMastery> subjectMastery,
      required final List<AssessmentAnalytics> assessmentHistory,
      required final List<MisconceptionFlag> activeMisconceptions,
      required final List<ConceptGap> conceptGaps,
      required final List<ActionableRecommendation> recommendations,
      required final DateTime generatedAt}) = _$StudentAnalyticsImpl;

  factory _StudentAnalytics.fromJson(Map<String, dynamic> json) =
      _$StudentAnalyticsImpl.fromJson;

  @override
  String get studentId;
  @override
  String get studentName;
  @override
  String get grade;
  @override
  Map<String, SubjectMastery> get subjectMastery;
  @override
  List<AssessmentAnalytics> get assessmentHistory;
  @override
  List<MisconceptionFlag> get activeMisconceptions;
  @override
  List<ConceptGap> get conceptGaps;
  @override
  List<ActionableRecommendation> get recommendations;
  @override
  DateTime get generatedAt;
  @override
  @JsonKey(ignore: true)
  _$$StudentAnalyticsImplCopyWith<_$StudentAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SchoolAnalytics _$SchoolAnalyticsFromJson(Map<String, dynamic> json) {
  return _SchoolAnalytics.fromJson(json);
}

/// @nodoc
mixin _$SchoolAnalytics {
  String get schoolId => throw _privateConstructorUsedError;
  String get schoolName => throw _privateConstructorUsedError;
  int get totalClasses => throw _privateConstructorUsedError;
  int get totalStudents => throw _privateConstructorUsedError;
  int get totalTeachers => throw _privateConstructorUsedError;
  Map<String, double> get subjectPerformance =>
      throw _privateConstructorUsedError;
  Map<String, int> get gradeDistribution => throw _privateConstructorUsedError;
  List<ClassAnalytics> get topClasses => throw _privateConstructorUsedError;
  List<ClassAnalytics> get atRiskClasses => throw _privateConstructorUsedError;
  List<ConceptGap> get schoolWideGaps => throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SchoolAnalyticsCopyWith<SchoolAnalytics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SchoolAnalyticsCopyWith<$Res> {
  factory $SchoolAnalyticsCopyWith(
          SchoolAnalytics value, $Res Function(SchoolAnalytics) then) =
      _$SchoolAnalyticsCopyWithImpl<$Res, SchoolAnalytics>;
  @useResult
  $Res call(
      {String schoolId,
      String schoolName,
      int totalClasses,
      int totalStudents,
      int totalTeachers,
      Map<String, double> subjectPerformance,
      Map<String, int> gradeDistribution,
      List<ClassAnalytics> topClasses,
      List<ClassAnalytics> atRiskClasses,
      List<ConceptGap> schoolWideGaps,
      DateTime generatedAt});
}

/// @nodoc
class _$SchoolAnalyticsCopyWithImpl<$Res, $Val extends SchoolAnalytics>
    implements $SchoolAnalyticsCopyWith<$Res> {
  _$SchoolAnalyticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? schoolId = null,
    Object? schoolName = null,
    Object? totalClasses = null,
    Object? totalStudents = null,
    Object? totalTeachers = null,
    Object? subjectPerformance = null,
    Object? gradeDistribution = null,
    Object? topClasses = null,
    Object? atRiskClasses = null,
    Object? schoolWideGaps = null,
    Object? generatedAt = null,
  }) {
    return _then(_value.copyWith(
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      schoolName: null == schoolName
          ? _value.schoolName
          : schoolName // ignore: cast_nullable_to_non_nullable
              as String,
      totalClasses: null == totalClasses
          ? _value.totalClasses
          : totalClasses // ignore: cast_nullable_to_non_nullable
              as int,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      totalTeachers: null == totalTeachers
          ? _value.totalTeachers
          : totalTeachers // ignore: cast_nullable_to_non_nullable
              as int,
      subjectPerformance: null == subjectPerformance
          ? _value.subjectPerformance
          : subjectPerformance // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      gradeDistribution: null == gradeDistribution
          ? _value.gradeDistribution
          : gradeDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      topClasses: null == topClasses
          ? _value.topClasses
          : topClasses // ignore: cast_nullable_to_non_nullable
              as List<ClassAnalytics>,
      atRiskClasses: null == atRiskClasses
          ? _value.atRiskClasses
          : atRiskClasses // ignore: cast_nullable_to_non_nullable
              as List<ClassAnalytics>,
      schoolWideGaps: null == schoolWideGaps
          ? _value.schoolWideGaps
          : schoolWideGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SchoolAnalyticsImplCopyWith<$Res>
    implements $SchoolAnalyticsCopyWith<$Res> {
  factory _$$SchoolAnalyticsImplCopyWith(_$SchoolAnalyticsImpl value,
          $Res Function(_$SchoolAnalyticsImpl) then) =
      __$$SchoolAnalyticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String schoolId,
      String schoolName,
      int totalClasses,
      int totalStudents,
      int totalTeachers,
      Map<String, double> subjectPerformance,
      Map<String, int> gradeDistribution,
      List<ClassAnalytics> topClasses,
      List<ClassAnalytics> atRiskClasses,
      List<ConceptGap> schoolWideGaps,
      DateTime generatedAt});
}

/// @nodoc
class __$$SchoolAnalyticsImplCopyWithImpl<$Res>
    extends _$SchoolAnalyticsCopyWithImpl<$Res, _$SchoolAnalyticsImpl>
    implements _$$SchoolAnalyticsImplCopyWith<$Res> {
  __$$SchoolAnalyticsImplCopyWithImpl(
      _$SchoolAnalyticsImpl _value, $Res Function(_$SchoolAnalyticsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? schoolId = null,
    Object? schoolName = null,
    Object? totalClasses = null,
    Object? totalStudents = null,
    Object? totalTeachers = null,
    Object? subjectPerformance = null,
    Object? gradeDistribution = null,
    Object? topClasses = null,
    Object? atRiskClasses = null,
    Object? schoolWideGaps = null,
    Object? generatedAt = null,
  }) {
    return _then(_$SchoolAnalyticsImpl(
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      schoolName: null == schoolName
          ? _value.schoolName
          : schoolName // ignore: cast_nullable_to_non_nullable
              as String,
      totalClasses: null == totalClasses
          ? _value.totalClasses
          : totalClasses // ignore: cast_nullable_to_non_nullable
              as int,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      totalTeachers: null == totalTeachers
          ? _value.totalTeachers
          : totalTeachers // ignore: cast_nullable_to_non_nullable
              as int,
      subjectPerformance: null == subjectPerformance
          ? _value._subjectPerformance
          : subjectPerformance // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      gradeDistribution: null == gradeDistribution
          ? _value._gradeDistribution
          : gradeDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      topClasses: null == topClasses
          ? _value._topClasses
          : topClasses // ignore: cast_nullable_to_non_nullable
              as List<ClassAnalytics>,
      atRiskClasses: null == atRiskClasses
          ? _value._atRiskClasses
          : atRiskClasses // ignore: cast_nullable_to_non_nullable
              as List<ClassAnalytics>,
      schoolWideGaps: null == schoolWideGaps
          ? _value._schoolWideGaps
          : schoolWideGaps // ignore: cast_nullable_to_non_nullable
              as List<ConceptGap>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SchoolAnalyticsImpl implements _SchoolAnalytics {
  const _$SchoolAnalyticsImpl(
      {required this.schoolId,
      required this.schoolName,
      required this.totalClasses,
      required this.totalStudents,
      required this.totalTeachers,
      required final Map<String, double> subjectPerformance,
      required final Map<String, int> gradeDistribution,
      required final List<ClassAnalytics> topClasses,
      required final List<ClassAnalytics> atRiskClasses,
      required final List<ConceptGap> schoolWideGaps,
      required this.generatedAt})
      : _subjectPerformance = subjectPerformance,
        _gradeDistribution = gradeDistribution,
        _topClasses = topClasses,
        _atRiskClasses = atRiskClasses,
        _schoolWideGaps = schoolWideGaps;

  factory _$SchoolAnalyticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$SchoolAnalyticsImplFromJson(json);

  @override
  final String schoolId;
  @override
  final String schoolName;
  @override
  final int totalClasses;
  @override
  final int totalStudents;
  @override
  final int totalTeachers;
  final Map<String, double> _subjectPerformance;
  @override
  Map<String, double> get subjectPerformance {
    if (_subjectPerformance is EqualUnmodifiableMapView)
      return _subjectPerformance;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_subjectPerformance);
  }

  final Map<String, int> _gradeDistribution;
  @override
  Map<String, int> get gradeDistribution {
    if (_gradeDistribution is EqualUnmodifiableMapView)
      return _gradeDistribution;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_gradeDistribution);
  }

  final List<ClassAnalytics> _topClasses;
  @override
  List<ClassAnalytics> get topClasses {
    if (_topClasses is EqualUnmodifiableListView) return _topClasses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_topClasses);
  }

  final List<ClassAnalytics> _atRiskClasses;
  @override
  List<ClassAnalytics> get atRiskClasses {
    if (_atRiskClasses is EqualUnmodifiableListView) return _atRiskClasses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_atRiskClasses);
  }

  final List<ConceptGap> _schoolWideGaps;
  @override
  List<ConceptGap> get schoolWideGaps {
    if (_schoolWideGaps is EqualUnmodifiableListView) return _schoolWideGaps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_schoolWideGaps);
  }

  @override
  final DateTime generatedAt;

  @override
  String toString() {
    return 'SchoolAnalytics(schoolId: $schoolId, schoolName: $schoolName, totalClasses: $totalClasses, totalStudents: $totalStudents, totalTeachers: $totalTeachers, subjectPerformance: $subjectPerformance, gradeDistribution: $gradeDistribution, topClasses: $topClasses, atRiskClasses: $atRiskClasses, schoolWideGaps: $schoolWideGaps, generatedAt: $generatedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SchoolAnalyticsImpl &&
            (identical(other.schoolId, schoolId) ||
                other.schoolId == schoolId) &&
            (identical(other.schoolName, schoolName) ||
                other.schoolName == schoolName) &&
            (identical(other.totalClasses, totalClasses) ||
                other.totalClasses == totalClasses) &&
            (identical(other.totalStudents, totalStudents) ||
                other.totalStudents == totalStudents) &&
            (identical(other.totalTeachers, totalTeachers) ||
                other.totalTeachers == totalTeachers) &&
            const DeepCollectionEquality()
                .equals(other._subjectPerformance, _subjectPerformance) &&
            const DeepCollectionEquality()
                .equals(other._gradeDistribution, _gradeDistribution) &&
            const DeepCollectionEquality()
                .equals(other._topClasses, _topClasses) &&
            const DeepCollectionEquality()
                .equals(other._atRiskClasses, _atRiskClasses) &&
            const DeepCollectionEquality()
                .equals(other._schoolWideGaps, _schoolWideGaps) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      schoolId,
      schoolName,
      totalClasses,
      totalStudents,
      totalTeachers,
      const DeepCollectionEquality().hash(_subjectPerformance),
      const DeepCollectionEquality().hash(_gradeDistribution),
      const DeepCollectionEquality().hash(_topClasses),
      const DeepCollectionEquality().hash(_atRiskClasses),
      const DeepCollectionEquality().hash(_schoolWideGaps),
      generatedAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SchoolAnalyticsImplCopyWith<_$SchoolAnalyticsImpl> get copyWith =>
      __$$SchoolAnalyticsImplCopyWithImpl<_$SchoolAnalyticsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SchoolAnalyticsImplToJson(
      this,
    );
  }
}

abstract class _SchoolAnalytics implements SchoolAnalytics {
  const factory _SchoolAnalytics(
      {required final String schoolId,
      required final String schoolName,
      required final int totalClasses,
      required final int totalStudents,
      required final int totalTeachers,
      required final Map<String, double> subjectPerformance,
      required final Map<String, int> gradeDistribution,
      required final List<ClassAnalytics> topClasses,
      required final List<ClassAnalytics> atRiskClasses,
      required final List<ConceptGap> schoolWideGaps,
      required final DateTime generatedAt}) = _$SchoolAnalyticsImpl;

  factory _SchoolAnalytics.fromJson(Map<String, dynamic> json) =
      _$SchoolAnalyticsImpl.fromJson;

  @override
  String get schoolId;
  @override
  String get schoolName;
  @override
  int get totalClasses;
  @override
  int get totalStudents;
  @override
  int get totalTeachers;
  @override
  Map<String, double> get subjectPerformance;
  @override
  Map<String, int> get gradeDistribution;
  @override
  List<ClassAnalytics> get topClasses;
  @override
  List<ClassAnalytics> get atRiskClasses;
  @override
  List<ConceptGap> get schoolWideGaps;
  @override
  DateTime get generatedAt;
  @override
  @JsonKey(ignore: true)
  _$$SchoolAnalyticsImplCopyWith<_$SchoolAnalyticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
