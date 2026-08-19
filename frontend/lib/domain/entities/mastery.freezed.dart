// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'mastery.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

StudentMastery _$StudentMasteryFromJson(Map<String, dynamic> json) {
  return _StudentMastery.fromJson(json);
}

/// @nodoc
mixin _$StudentMastery {
  String get studentId => throw _privateConstructorUsedError;
  String get schoolId => throw _privateConstructorUsedError;
  String get grade => throw _privateConstructorUsedError;
  List<ConceptMastery> get concepts => throw _privateConstructorUsedError;
  List<ChapterMastery> get chapters => throw _privateConstructorUsedError;
  List<SubjectMastery> get subjects => throw _privateConstructorUsedError;
  MasterySummary get summary => throw _privateConstructorUsedError;
  DateTime get lastUpdated => throw _privateConstructorUsedError;
  int get version => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $StudentMasteryCopyWith<StudentMastery> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StudentMasteryCopyWith<$Res> {
  factory $StudentMasteryCopyWith(
          StudentMastery value, $Res Function(StudentMastery) then) =
      _$StudentMasteryCopyWithImpl<$Res, StudentMastery>;
  @useResult
  $Res call(
      {String studentId,
      String schoolId,
      String grade,
      List<ConceptMastery> concepts,
      List<ChapterMastery> chapters,
      List<SubjectMastery> subjects,
      MasterySummary summary,
      DateTime lastUpdated,
      int version});

  $MasterySummaryCopyWith<$Res> get summary;
}

/// @nodoc
class _$StudentMasteryCopyWithImpl<$Res, $Val extends StudentMastery>
    implements $StudentMasteryCopyWith<$Res> {
  _$StudentMasteryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? schoolId = null,
    Object? grade = null,
    Object? concepts = null,
    Object? chapters = null,
    Object? subjects = null,
    Object? summary = null,
    Object? lastUpdated = null,
    Object? version = null,
  }) {
    return _then(_value.copyWith(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      concepts: null == concepts
          ? _value.concepts
          : concepts // ignore: cast_nullable_to_non_nullable
              as List<ConceptMastery>,
      chapters: null == chapters
          ? _value.chapters
          : chapters // ignore: cast_nullable_to_non_nullable
              as List<ChapterMastery>,
      subjects: null == subjects
          ? _value.subjects
          : subjects // ignore: cast_nullable_to_non_nullable
              as List<SubjectMastery>,
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as MasterySummary,
      lastUpdated: null == lastUpdated
          ? _value.lastUpdated
          : lastUpdated // ignore: cast_nullable_to_non_nullable
              as DateTime,
      version: null == version
          ? _value.version
          : version // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $MasterySummaryCopyWith<$Res> get summary {
    return $MasterySummaryCopyWith<$Res>(_value.summary, (value) {
      return _then(_value.copyWith(summary: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$StudentMasteryImplCopyWith<$Res>
    implements $StudentMasteryCopyWith<$Res> {
  factory _$$StudentMasteryImplCopyWith(_$StudentMasteryImpl value,
          $Res Function(_$StudentMasteryImpl) then) =
      __$$StudentMasteryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String studentId,
      String schoolId,
      String grade,
      List<ConceptMastery> concepts,
      List<ChapterMastery> chapters,
      List<SubjectMastery> subjects,
      MasterySummary summary,
      DateTime lastUpdated,
      int version});

  @override
  $MasterySummaryCopyWith<$Res> get summary;
}

/// @nodoc
class __$$StudentMasteryImplCopyWithImpl<$Res>
    extends _$StudentMasteryCopyWithImpl<$Res, _$StudentMasteryImpl>
    implements _$$StudentMasteryImplCopyWith<$Res> {
  __$$StudentMasteryImplCopyWithImpl(
      _$StudentMasteryImpl _value, $Res Function(_$StudentMasteryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? schoolId = null,
    Object? grade = null,
    Object? concepts = null,
    Object? chapters = null,
    Object? subjects = null,
    Object? summary = null,
    Object? lastUpdated = null,
    Object? version = null,
  }) {
    return _then(_$StudentMasteryImpl(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      concepts: null == concepts
          ? _value._concepts
          : concepts // ignore: cast_nullable_to_non_nullable
              as List<ConceptMastery>,
      chapters: null == chapters
          ? _value._chapters
          : chapters // ignore: cast_nullable_to_non_nullable
              as List<ChapterMastery>,
      subjects: null == subjects
          ? _value._subjects
          : subjects // ignore: cast_nullable_to_non_nullable
              as List<SubjectMastery>,
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as MasterySummary,
      lastUpdated: null == lastUpdated
          ? _value.lastUpdated
          : lastUpdated // ignore: cast_nullable_to_non_nullable
              as DateTime,
      version: null == version
          ? _value.version
          : version // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StudentMasteryImpl implements _StudentMastery {
  const _$StudentMasteryImpl(
      {required this.studentId,
      required this.schoolId,
      required this.grade,
      required final List<ConceptMastery> concepts,
      required final List<ChapterMastery> chapters,
      required final List<SubjectMastery> subjects,
      required this.summary,
      required this.lastUpdated,
      required this.version})
      : _concepts = concepts,
        _chapters = chapters,
        _subjects = subjects;

  factory _$StudentMasteryImpl.fromJson(Map<String, dynamic> json) =>
      _$$StudentMasteryImplFromJson(json);

  @override
  final String studentId;
  @override
  final String schoolId;
  @override
  final String grade;
  final List<ConceptMastery> _concepts;
  @override
  List<ConceptMastery> get concepts {
    if (_concepts is EqualUnmodifiableListView) return _concepts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_concepts);
  }

  final List<ChapterMastery> _chapters;
  @override
  List<ChapterMastery> get chapters {
    if (_chapters is EqualUnmodifiableListView) return _chapters;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_chapters);
  }

  final List<SubjectMastery> _subjects;
  @override
  List<SubjectMastery> get subjects {
    if (_subjects is EqualUnmodifiableListView) return _subjects;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_subjects);
  }

  @override
  final MasterySummary summary;
  @override
  final DateTime lastUpdated;
  @override
  final int version;

  @override
  String toString() {
    return 'StudentMastery(studentId: $studentId, schoolId: $schoolId, grade: $grade, concepts: $concepts, chapters: $chapters, subjects: $subjects, summary: $summary, lastUpdated: $lastUpdated, version: $version)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StudentMasteryImpl &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.schoolId, schoolId) ||
                other.schoolId == schoolId) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality().equals(other._concepts, _concepts) &&
            const DeepCollectionEquality().equals(other._chapters, _chapters) &&
            const DeepCollectionEquality().equals(other._subjects, _subjects) &&
            (identical(other.summary, summary) || other.summary == summary) &&
            (identical(other.lastUpdated, lastUpdated) ||
                other.lastUpdated == lastUpdated) &&
            (identical(other.version, version) || other.version == version));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      studentId,
      schoolId,
      grade,
      const DeepCollectionEquality().hash(_concepts),
      const DeepCollectionEquality().hash(_chapters),
      const DeepCollectionEquality().hash(_subjects),
      summary,
      lastUpdated,
      version);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$StudentMasteryImplCopyWith<_$StudentMasteryImpl> get copyWith =>
      __$$StudentMasteryImplCopyWithImpl<_$StudentMasteryImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StudentMasteryImplToJson(
      this,
    );
  }
}

abstract class _StudentMastery implements StudentMastery {
  const factory _StudentMastery(
      {required final String studentId,
      required final String schoolId,
      required final String grade,
      required final List<ConceptMastery> concepts,
      required final List<ChapterMastery> chapters,
      required final List<SubjectMastery> subjects,
      required final MasterySummary summary,
      required final DateTime lastUpdated,
      required final int version}) = _$StudentMasteryImpl;

  factory _StudentMastery.fromJson(Map<String, dynamic> json) =
      _$StudentMasteryImpl.fromJson;

  @override
  String get studentId;
  @override
  String get schoolId;
  @override
  String get grade;
  @override
  List<ConceptMastery> get concepts;
  @override
  List<ChapterMastery> get chapters;
  @override
  List<SubjectMastery> get subjects;
  @override
  MasterySummary get summary;
  @override
  DateTime get lastUpdated;
  @override
  int get version;
  @override
  @JsonKey(ignore: true)
  _$$StudentMasteryImplCopyWith<_$StudentMasteryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ConceptMastery _$ConceptMasteryFromJson(Map<String, dynamic> json) {
  return _ConceptMastery.fromJson(json);
}

/// @nodoc
mixin _$ConceptMastery {
  String get conceptId => throw _privateConstructorUsedError;
  String get conceptName => throw _privateConstructorUsedError;
  String get chapterId => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  double get masteryScore => throw _privateConstructorUsedError;
  double get confidenceScore => throw _privateConstructorUsedError;
  double get retentionScore => throw _privateConstructorUsedError;
  int get totalAttempts => throw _privateConstructorUsedError;
  int get correctAttempts => throw _privateConstructorUsedError;
  int get consecutiveCorrect => throw _privateConstructorUsedError;
  int get consecutiveIncorrect => throw _privateConstructorUsedError;
  DateTime get lastAttemptedAt => throw _privateConstructorUsedError;
  DateTime? get masteredAt => throw _privateConstructorUsedError;
  MasteryStatus get status => throw _privateConstructorUsedError;
  List<MisconceptionFlag> get misconceptions =>
      throw _privateConstructorUsedError;
  List<String> get prerequisiteConceptIds => throw _privateConstructorUsedError;
  double get difficulty => throw _privateConstructorUsedError;
  double get timeSpentMinutes => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ConceptMasteryCopyWith<ConceptMastery> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ConceptMasteryCopyWith<$Res> {
  factory $ConceptMasteryCopyWith(
          ConceptMastery value, $Res Function(ConceptMastery) then) =
      _$ConceptMasteryCopyWithImpl<$Res, ConceptMastery>;
  @useResult
  $Res call(
      {String conceptId,
      String conceptName,
      String chapterId,
      String subject,
      double masteryScore,
      double confidenceScore,
      double retentionScore,
      int totalAttempts,
      int correctAttempts,
      int consecutiveCorrect,
      int consecutiveIncorrect,
      DateTime lastAttemptedAt,
      DateTime? masteredAt,
      MasteryStatus status,
      List<MisconceptionFlag> misconceptions,
      List<String> prerequisiteConceptIds,
      double difficulty,
      double timeSpentMinutes});
}

/// @nodoc
class _$ConceptMasteryCopyWithImpl<$Res, $Val extends ConceptMastery>
    implements $ConceptMasteryCopyWith<$Res> {
  _$ConceptMasteryCopyWithImpl(this._value, this._then);

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
    Object? subject = null,
    Object? masteryScore = null,
    Object? confidenceScore = null,
    Object? retentionScore = null,
    Object? totalAttempts = null,
    Object? correctAttempts = null,
    Object? consecutiveCorrect = null,
    Object? consecutiveIncorrect = null,
    Object? lastAttemptedAt = null,
    Object? masteredAt = freezed,
    Object? status = null,
    Object? misconceptions = null,
    Object? prerequisiteConceptIds = null,
    Object? difficulty = null,
    Object? timeSpentMinutes = null,
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
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      masteryScore: null == masteryScore
          ? _value.masteryScore
          : masteryScore // ignore: cast_nullable_to_non_nullable
              as double,
      confidenceScore: null == confidenceScore
          ? _value.confidenceScore
          : confidenceScore // ignore: cast_nullable_to_non_nullable
              as double,
      retentionScore: null == retentionScore
          ? _value.retentionScore
          : retentionScore // ignore: cast_nullable_to_non_nullable
              as double,
      totalAttempts: null == totalAttempts
          ? _value.totalAttempts
          : totalAttempts // ignore: cast_nullable_to_non_nullable
              as int,
      correctAttempts: null == correctAttempts
          ? _value.correctAttempts
          : correctAttempts // ignore: cast_nullable_to_non_nullable
              as int,
      consecutiveCorrect: null == consecutiveCorrect
          ? _value.consecutiveCorrect
          : consecutiveCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      consecutiveIncorrect: null == consecutiveIncorrect
          ? _value.consecutiveIncorrect
          : consecutiveIncorrect // ignore: cast_nullable_to_non_nullable
              as int,
      lastAttemptedAt: null == lastAttemptedAt
          ? _value.lastAttemptedAt
          : lastAttemptedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      masteredAt: freezed == masteredAt
          ? _value.masteredAt
          : masteredAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as MasteryStatus,
      misconceptions: null == misconceptions
          ? _value.misconceptions
          : misconceptions // ignore: cast_nullable_to_non_nullable
              as List<MisconceptionFlag>,
      prerequisiteConceptIds: null == prerequisiteConceptIds
          ? _value.prerequisiteConceptIds
          : prerequisiteConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as double,
      timeSpentMinutes: null == timeSpentMinutes
          ? _value.timeSpentMinutes
          : timeSpentMinutes // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ConceptMasteryImplCopyWith<$Res>
    implements $ConceptMasteryCopyWith<$Res> {
  factory _$$ConceptMasteryImplCopyWith(_$ConceptMasteryImpl value,
          $Res Function(_$ConceptMasteryImpl) then) =
      __$$ConceptMasteryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String conceptId,
      String conceptName,
      String chapterId,
      String subject,
      double masteryScore,
      double confidenceScore,
      double retentionScore,
      int totalAttempts,
      int correctAttempts,
      int consecutiveCorrect,
      int consecutiveIncorrect,
      DateTime lastAttemptedAt,
      DateTime? masteredAt,
      MasteryStatus status,
      List<MisconceptionFlag> misconceptions,
      List<String> prerequisiteConceptIds,
      double difficulty,
      double timeSpentMinutes});
}

/// @nodoc
class __$$ConceptMasteryImplCopyWithImpl<$Res>
    extends _$ConceptMasteryCopyWithImpl<$Res, _$ConceptMasteryImpl>
    implements _$$ConceptMasteryImplCopyWith<$Res> {
  __$$ConceptMasteryImplCopyWithImpl(
      _$ConceptMasteryImpl _value, $Res Function(_$ConceptMasteryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? conceptId = null,
    Object? conceptName = null,
    Object? chapterId = null,
    Object? subject = null,
    Object? masteryScore = null,
    Object? confidenceScore = null,
    Object? retentionScore = null,
    Object? totalAttempts = null,
    Object? correctAttempts = null,
    Object? consecutiveCorrect = null,
    Object? consecutiveIncorrect = null,
    Object? lastAttemptedAt = null,
    Object? masteredAt = freezed,
    Object? status = null,
    Object? misconceptions = null,
    Object? prerequisiteConceptIds = null,
    Object? difficulty = null,
    Object? timeSpentMinutes = null,
  }) {
    return _then(_$ConceptMasteryImpl(
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
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      masteryScore: null == masteryScore
          ? _value.masteryScore
          : masteryScore // ignore: cast_nullable_to_non_nullable
              as double,
      confidenceScore: null == confidenceScore
          ? _value.confidenceScore
          : confidenceScore // ignore: cast_nullable_to_non_nullable
              as double,
      retentionScore: null == retentionScore
          ? _value.retentionScore
          : retentionScore // ignore: cast_nullable_to_non_nullable
              as double,
      totalAttempts: null == totalAttempts
          ? _value.totalAttempts
          : totalAttempts // ignore: cast_nullable_to_non_nullable
              as int,
      correctAttempts: null == correctAttempts
          ? _value.correctAttempts
          : correctAttempts // ignore: cast_nullable_to_non_nullable
              as int,
      consecutiveCorrect: null == consecutiveCorrect
          ? _value.consecutiveCorrect
          : consecutiveCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      consecutiveIncorrect: null == consecutiveIncorrect
          ? _value.consecutiveIncorrect
          : consecutiveIncorrect // ignore: cast_nullable_to_non_nullable
              as int,
      lastAttemptedAt: null == lastAttemptedAt
          ? _value.lastAttemptedAt
          : lastAttemptedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      masteredAt: freezed == masteredAt
          ? _value.masteredAt
          : masteredAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as MasteryStatus,
      misconceptions: null == misconceptions
          ? _value._misconceptions
          : misconceptions // ignore: cast_nullable_to_non_nullable
              as List<MisconceptionFlag>,
      prerequisiteConceptIds: null == prerequisiteConceptIds
          ? _value._prerequisiteConceptIds
          : prerequisiteConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as double,
      timeSpentMinutes: null == timeSpentMinutes
          ? _value.timeSpentMinutes
          : timeSpentMinutes // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ConceptMasteryImpl implements _ConceptMastery {
  const _$ConceptMasteryImpl(
      {required this.conceptId,
      required this.conceptName,
      required this.chapterId,
      required this.subject,
      required this.masteryScore,
      required this.confidenceScore,
      required this.retentionScore,
      required this.totalAttempts,
      required this.correctAttempts,
      required this.consecutiveCorrect,
      required this.consecutiveIncorrect,
      required this.lastAttemptedAt,
      this.masteredAt,
      required this.status,
      required final List<MisconceptionFlag> misconceptions,
      required final List<String> prerequisiteConceptIds,
      required this.difficulty,
      required this.timeSpentMinutes})
      : _misconceptions = misconceptions,
        _prerequisiteConceptIds = prerequisiteConceptIds;

  factory _$ConceptMasteryImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConceptMasteryImplFromJson(json);

  @override
  final String conceptId;
  @override
  final String conceptName;
  @override
  final String chapterId;
  @override
  final String subject;
  @override
  final double masteryScore;
  @override
  final double confidenceScore;
  @override
  final double retentionScore;
  @override
  final int totalAttempts;
  @override
  final int correctAttempts;
  @override
  final int consecutiveCorrect;
  @override
  final int consecutiveIncorrect;
  @override
  final DateTime lastAttemptedAt;
  @override
  final DateTime? masteredAt;
  @override
  final MasteryStatus status;
  final List<MisconceptionFlag> _misconceptions;
  @override
  List<MisconceptionFlag> get misconceptions {
    if (_misconceptions is EqualUnmodifiableListView) return _misconceptions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_misconceptions);
  }

  final List<String> _prerequisiteConceptIds;
  @override
  List<String> get prerequisiteConceptIds {
    if (_prerequisiteConceptIds is EqualUnmodifiableListView)
      return _prerequisiteConceptIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_prerequisiteConceptIds);
  }

  @override
  final double difficulty;
  @override
  final double timeSpentMinutes;

  @override
  String toString() {
    return 'ConceptMastery(conceptId: $conceptId, conceptName: $conceptName, chapterId: $chapterId, subject: $subject, masteryScore: $masteryScore, confidenceScore: $confidenceScore, retentionScore: $retentionScore, totalAttempts: $totalAttempts, correctAttempts: $correctAttempts, consecutiveCorrect: $consecutiveCorrect, consecutiveIncorrect: $consecutiveIncorrect, lastAttemptedAt: $lastAttemptedAt, masteredAt: $masteredAt, status: $status, misconceptions: $misconceptions, prerequisiteConceptIds: $prerequisiteConceptIds, difficulty: $difficulty, timeSpentMinutes: $timeSpentMinutes)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConceptMasteryImpl &&
            (identical(other.conceptId, conceptId) ||
                other.conceptId == conceptId) &&
            (identical(other.conceptName, conceptName) ||
                other.conceptName == conceptName) &&
            (identical(other.chapterId, chapterId) ||
                other.chapterId == chapterId) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.masteryScore, masteryScore) ||
                other.masteryScore == masteryScore) &&
            (identical(other.confidenceScore, confidenceScore) ||
                other.confidenceScore == confidenceScore) &&
            (identical(other.retentionScore, retentionScore) ||
                other.retentionScore == retentionScore) &&
            (identical(other.totalAttempts, totalAttempts) ||
                other.totalAttempts == totalAttempts) &&
            (identical(other.correctAttempts, correctAttempts) ||
                other.correctAttempts == correctAttempts) &&
            (identical(other.consecutiveCorrect, consecutiveCorrect) ||
                other.consecutiveCorrect == consecutiveCorrect) &&
            (identical(other.consecutiveIncorrect, consecutiveIncorrect) ||
                other.consecutiveIncorrect == consecutiveIncorrect) &&
            (identical(other.lastAttemptedAt, lastAttemptedAt) ||
                other.lastAttemptedAt == lastAttemptedAt) &&
            (identical(other.masteredAt, masteredAt) ||
                other.masteredAt == masteredAt) &&
            (identical(other.status, status) || other.status == status) &&
            const DeepCollectionEquality()
                .equals(other._misconceptions, _misconceptions) &&
            const DeepCollectionEquality().equals(
                other._prerequisiteConceptIds, _prerequisiteConceptIds) &&
            (identical(other.difficulty, difficulty) ||
                other.difficulty == difficulty) &&
            (identical(other.timeSpentMinutes, timeSpentMinutes) ||
                other.timeSpentMinutes == timeSpentMinutes));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      conceptId,
      conceptName,
      chapterId,
      subject,
      masteryScore,
      confidenceScore,
      retentionScore,
      totalAttempts,
      correctAttempts,
      consecutiveCorrect,
      consecutiveIncorrect,
      lastAttemptedAt,
      masteredAt,
      status,
      const DeepCollectionEquality().hash(_misconceptions),
      const DeepCollectionEquality().hash(_prerequisiteConceptIds),
      difficulty,
      timeSpentMinutes);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ConceptMasteryImplCopyWith<_$ConceptMasteryImpl> get copyWith =>
      __$$ConceptMasteryImplCopyWithImpl<_$ConceptMasteryImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ConceptMasteryImplToJson(
      this,
    );
  }
}

abstract class _ConceptMastery implements ConceptMastery {
  const factory _ConceptMastery(
      {required final String conceptId,
      required final String conceptName,
      required final String chapterId,
      required final String subject,
      required final double masteryScore,
      required final double confidenceScore,
      required final double retentionScore,
      required final int totalAttempts,
      required final int correctAttempts,
      required final int consecutiveCorrect,
      required final int consecutiveIncorrect,
      required final DateTime lastAttemptedAt,
      final DateTime? masteredAt,
      required final MasteryStatus status,
      required final List<MisconceptionFlag> misconceptions,
      required final List<String> prerequisiteConceptIds,
      required final double difficulty,
      required final double timeSpentMinutes}) = _$ConceptMasteryImpl;

  factory _ConceptMastery.fromJson(Map<String, dynamic> json) =
      _$ConceptMasteryImpl.fromJson;

  @override
  String get conceptId;
  @override
  String get conceptName;
  @override
  String get chapterId;
  @override
  String get subject;
  @override
  double get masteryScore;
  @override
  double get confidenceScore;
  @override
  double get retentionScore;
  @override
  int get totalAttempts;
  @override
  int get correctAttempts;
  @override
  int get consecutiveCorrect;
  @override
  int get consecutiveIncorrect;
  @override
  DateTime get lastAttemptedAt;
  @override
  DateTime? get masteredAt;
  @override
  MasteryStatus get status;
  @override
  List<MisconceptionFlag> get misconceptions;
  @override
  List<String> get prerequisiteConceptIds;
  @override
  double get difficulty;
  @override
  double get timeSpentMinutes;
  @override
  @JsonKey(ignore: true)
  _$$ConceptMasteryImplCopyWith<_$ConceptMasteryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChapterMastery _$ChapterMasteryFromJson(Map<String, dynamic> json) {
  return _ChapterMastery.fromJson(json);
}

/// @nodoc
mixin _$ChapterMastery {
  String get chapterId => throw _privateConstructorUsedError;
  String get chapterName => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  double get overallMastery => throw _privateConstructorUsedError;
  double get overallConfidence => throw _privateConstructorUsedError;
  double get overallRetention => throw _privateConstructorUsedError;
  List<String> get masteredConceptIds => throw _privateConstructorUsedError;
  List<String> get weakConceptIds => throw _privateConstructorUsedError;
  List<String> get notAttemptedConceptIds => throw _privateConstructorUsedError;
  int get questionsAttempted => throw _privateConstructorUsedError;
  int get questionsCorrect => throw _privateConstructorUsedError;
  DateTime get lastActivityAt => throw _privateConstructorUsedError;
  ChapterStatus get status => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChapterMasteryCopyWith<ChapterMastery> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChapterMasteryCopyWith<$Res> {
  factory $ChapterMasteryCopyWith(
          ChapterMastery value, $Res Function(ChapterMastery) then) =
      _$ChapterMasteryCopyWithImpl<$Res, ChapterMastery>;
  @useResult
  $Res call(
      {String chapterId,
      String chapterName,
      String subject,
      int grade,
      double overallMastery,
      double overallConfidence,
      double overallRetention,
      List<String> masteredConceptIds,
      List<String> weakConceptIds,
      List<String> notAttemptedConceptIds,
      int questionsAttempted,
      int questionsCorrect,
      DateTime lastActivityAt,
      ChapterStatus status});
}

/// @nodoc
class _$ChapterMasteryCopyWithImpl<$Res, $Val extends ChapterMastery>
    implements $ChapterMasteryCopyWith<$Res> {
  _$ChapterMasteryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? chapterId = null,
    Object? chapterName = null,
    Object? subject = null,
    Object? grade = null,
    Object? overallMastery = null,
    Object? overallConfidence = null,
    Object? overallRetention = null,
    Object? masteredConceptIds = null,
    Object? weakConceptIds = null,
    Object? notAttemptedConceptIds = null,
    Object? questionsAttempted = null,
    Object? questionsCorrect = null,
    Object? lastActivityAt = null,
    Object? status = null,
  }) {
    return _then(_value.copyWith(
      chapterId: null == chapterId
          ? _value.chapterId
          : chapterId // ignore: cast_nullable_to_non_nullable
              as String,
      chapterName: null == chapterName
          ? _value.chapterName
          : chapterName // ignore: cast_nullable_to_non_nullable
              as String,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      overallMastery: null == overallMastery
          ? _value.overallMastery
          : overallMastery // ignore: cast_nullable_to_non_nullable
              as double,
      overallConfidence: null == overallConfidence
          ? _value.overallConfidence
          : overallConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      overallRetention: null == overallRetention
          ? _value.overallRetention
          : overallRetention // ignore: cast_nullable_to_non_nullable
              as double,
      masteredConceptIds: null == masteredConceptIds
          ? _value.masteredConceptIds
          : masteredConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      weakConceptIds: null == weakConceptIds
          ? _value.weakConceptIds
          : weakConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      notAttemptedConceptIds: null == notAttemptedConceptIds
          ? _value.notAttemptedConceptIds
          : notAttemptedConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      questionsCorrect: null == questionsCorrect
          ? _value.questionsCorrect
          : questionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      lastActivityAt: null == lastActivityAt
          ? _value.lastActivityAt
          : lastActivityAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as ChapterStatus,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChapterMasteryImplCopyWith<$Res>
    implements $ChapterMasteryCopyWith<$Res> {
  factory _$$ChapterMasteryImplCopyWith(_$ChapterMasteryImpl value,
          $Res Function(_$ChapterMasteryImpl) then) =
      __$$ChapterMasteryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String chapterId,
      String chapterName,
      String subject,
      int grade,
      double overallMastery,
      double overallConfidence,
      double overallRetention,
      List<String> masteredConceptIds,
      List<String> weakConceptIds,
      List<String> notAttemptedConceptIds,
      int questionsAttempted,
      int questionsCorrect,
      DateTime lastActivityAt,
      ChapterStatus status});
}

/// @nodoc
class __$$ChapterMasteryImplCopyWithImpl<$Res>
    extends _$ChapterMasteryCopyWithImpl<$Res, _$ChapterMasteryImpl>
    implements _$$ChapterMasteryImplCopyWith<$Res> {
  __$$ChapterMasteryImplCopyWithImpl(
      _$ChapterMasteryImpl _value, $Res Function(_$ChapterMasteryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? chapterId = null,
    Object? chapterName = null,
    Object? subject = null,
    Object? grade = null,
    Object? overallMastery = null,
    Object? overallConfidence = null,
    Object? overallRetention = null,
    Object? masteredConceptIds = null,
    Object? weakConceptIds = null,
    Object? notAttemptedConceptIds = null,
    Object? questionsAttempted = null,
    Object? questionsCorrect = null,
    Object? lastActivityAt = null,
    Object? status = null,
  }) {
    return _then(_$ChapterMasteryImpl(
      chapterId: null == chapterId
          ? _value.chapterId
          : chapterId // ignore: cast_nullable_to_non_nullable
              as String,
      chapterName: null == chapterName
          ? _value.chapterName
          : chapterName // ignore: cast_nullable_to_non_nullable
              as String,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      overallMastery: null == overallMastery
          ? _value.overallMastery
          : overallMastery // ignore: cast_nullable_to_non_nullable
              as double,
      overallConfidence: null == overallConfidence
          ? _value.overallConfidence
          : overallConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      overallRetention: null == overallRetention
          ? _value.overallRetention
          : overallRetention // ignore: cast_nullable_to_non_nullable
              as double,
      masteredConceptIds: null == masteredConceptIds
          ? _value._masteredConceptIds
          : masteredConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      weakConceptIds: null == weakConceptIds
          ? _value._weakConceptIds
          : weakConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      notAttemptedConceptIds: null == notAttemptedConceptIds
          ? _value._notAttemptedConceptIds
          : notAttemptedConceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      questionsCorrect: null == questionsCorrect
          ? _value.questionsCorrect
          : questionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      lastActivityAt: null == lastActivityAt
          ? _value.lastActivityAt
          : lastActivityAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as ChapterStatus,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChapterMasteryImpl implements _ChapterMastery {
  const _$ChapterMasteryImpl(
      {required this.chapterId,
      required this.chapterName,
      required this.subject,
      required this.grade,
      required this.overallMastery,
      required this.overallConfidence,
      required this.overallRetention,
      required final List<String> masteredConceptIds,
      required final List<String> weakConceptIds,
      required final List<String> notAttemptedConceptIds,
      required this.questionsAttempted,
      required this.questionsCorrect,
      required this.lastActivityAt,
      required this.status})
      : _masteredConceptIds = masteredConceptIds,
        _weakConceptIds = weakConceptIds,
        _notAttemptedConceptIds = notAttemptedConceptIds;

  factory _$ChapterMasteryImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChapterMasteryImplFromJson(json);

  @override
  final String chapterId;
  @override
  final String chapterName;
  @override
  final String subject;
  @override
  final int grade;
  @override
  final double overallMastery;
  @override
  final double overallConfidence;
  @override
  final double overallRetention;
  final List<String> _masteredConceptIds;
  @override
  List<String> get masteredConceptIds {
    if (_masteredConceptIds is EqualUnmodifiableListView)
      return _masteredConceptIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_masteredConceptIds);
  }

  final List<String> _weakConceptIds;
  @override
  List<String> get weakConceptIds {
    if (_weakConceptIds is EqualUnmodifiableListView) return _weakConceptIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_weakConceptIds);
  }

  final List<String> _notAttemptedConceptIds;
  @override
  List<String> get notAttemptedConceptIds {
    if (_notAttemptedConceptIds is EqualUnmodifiableListView)
      return _notAttemptedConceptIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_notAttemptedConceptIds);
  }

  @override
  final int questionsAttempted;
  @override
  final int questionsCorrect;
  @override
  final DateTime lastActivityAt;
  @override
  final ChapterStatus status;

  @override
  String toString() {
    return 'ChapterMastery(chapterId: $chapterId, chapterName: $chapterName, subject: $subject, grade: $grade, overallMastery: $overallMastery, overallConfidence: $overallConfidence, overallRetention: $overallRetention, masteredConceptIds: $masteredConceptIds, weakConceptIds: $weakConceptIds, notAttemptedConceptIds: $notAttemptedConceptIds, questionsAttempted: $questionsAttempted, questionsCorrect: $questionsCorrect, lastActivityAt: $lastActivityAt, status: $status)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChapterMasteryImpl &&
            (identical(other.chapterId, chapterId) ||
                other.chapterId == chapterId) &&
            (identical(other.chapterName, chapterName) ||
                other.chapterName == chapterName) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.overallMastery, overallMastery) ||
                other.overallMastery == overallMastery) &&
            (identical(other.overallConfidence, overallConfidence) ||
                other.overallConfidence == overallConfidence) &&
            (identical(other.overallRetention, overallRetention) ||
                other.overallRetention == overallRetention) &&
            const DeepCollectionEquality()
                .equals(other._masteredConceptIds, _masteredConceptIds) &&
            const DeepCollectionEquality()
                .equals(other._weakConceptIds, _weakConceptIds) &&
            const DeepCollectionEquality().equals(
                other._notAttemptedConceptIds, _notAttemptedConceptIds) &&
            (identical(other.questionsAttempted, questionsAttempted) ||
                other.questionsAttempted == questionsAttempted) &&
            (identical(other.questionsCorrect, questionsCorrect) ||
                other.questionsCorrect == questionsCorrect) &&
            (identical(other.lastActivityAt, lastActivityAt) ||
                other.lastActivityAt == lastActivityAt) &&
            (identical(other.status, status) || other.status == status));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      chapterId,
      chapterName,
      subject,
      grade,
      overallMastery,
      overallConfidence,
      overallRetention,
      const DeepCollectionEquality().hash(_masteredConceptIds),
      const DeepCollectionEquality().hash(_weakConceptIds),
      const DeepCollectionEquality().hash(_notAttemptedConceptIds),
      questionsAttempted,
      questionsCorrect,
      lastActivityAt,
      status);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChapterMasteryImplCopyWith<_$ChapterMasteryImpl> get copyWith =>
      __$$ChapterMasteryImplCopyWithImpl<_$ChapterMasteryImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChapterMasteryImplToJson(
      this,
    );
  }
}

abstract class _ChapterMastery implements ChapterMastery {
  const factory _ChapterMastery(
      {required final String chapterId,
      required final String chapterName,
      required final String subject,
      required final int grade,
      required final double overallMastery,
      required final double overallConfidence,
      required final double overallRetention,
      required final List<String> masteredConceptIds,
      required final List<String> weakConceptIds,
      required final List<String> notAttemptedConceptIds,
      required final int questionsAttempted,
      required final int questionsCorrect,
      required final DateTime lastActivityAt,
      required final ChapterStatus status}) = _$ChapterMasteryImpl;

  factory _ChapterMastery.fromJson(Map<String, dynamic> json) =
      _$ChapterMasteryImpl.fromJson;

  @override
  String get chapterId;
  @override
  String get chapterName;
  @override
  String get subject;
  @override
  int get grade;
  @override
  double get overallMastery;
  @override
  double get overallConfidence;
  @override
  double get overallRetention;
  @override
  List<String> get masteredConceptIds;
  @override
  List<String> get weakConceptIds;
  @override
  List<String> get notAttemptedConceptIds;
  @override
  int get questionsAttempted;
  @override
  int get questionsCorrect;
  @override
  DateTime get lastActivityAt;
  @override
  ChapterStatus get status;
  @override
  @JsonKey(ignore: true)
  _$$ChapterMasteryImplCopyWith<_$ChapterMasteryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SubjectMastery _$SubjectMasteryFromJson(Map<String, dynamic> json) {
  return _SubjectMastery.fromJson(json);
}

/// @nodoc
mixin _$SubjectMastery {
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  double get overallMastery => throw _privateConstructorUsedError;
  double get overallConfidence => throw _privateConstructorUsedError;
  double get overallRetention => throw _privateConstructorUsedError;
  List<ChapterMastery> get chapters => throw _privateConstructorUsedError;
  int get totalQuestionsAttempted => throw _privateConstructorUsedError;
  int get totalQuestionsCorrect => throw _privateConstructorUsedError;
  double get avgTimePerQuestion => throw _privateConstructorUsedError;
  SubjectStatus get status => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SubjectMasteryCopyWith<SubjectMastery> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SubjectMasteryCopyWith<$Res> {
  factory $SubjectMasteryCopyWith(
          SubjectMastery value, $Res Function(SubjectMastery) then) =
      _$SubjectMasteryCopyWithImpl<$Res, SubjectMastery>;
  @useResult
  $Res call(
      {String subject,
      int grade,
      double overallMastery,
      double overallConfidence,
      double overallRetention,
      List<ChapterMastery> chapters,
      int totalQuestionsAttempted,
      int totalQuestionsCorrect,
      double avgTimePerQuestion,
      SubjectStatus status});
}

/// @nodoc
class _$SubjectMasteryCopyWithImpl<$Res, $Val extends SubjectMastery>
    implements $SubjectMasteryCopyWith<$Res> {
  _$SubjectMasteryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? subject = null,
    Object? grade = null,
    Object? overallMastery = null,
    Object? overallConfidence = null,
    Object? overallRetention = null,
    Object? chapters = null,
    Object? totalQuestionsAttempted = null,
    Object? totalQuestionsCorrect = null,
    Object? avgTimePerQuestion = null,
    Object? status = null,
  }) {
    return _then(_value.copyWith(
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      overallMastery: null == overallMastery
          ? _value.overallMastery
          : overallMastery // ignore: cast_nullable_to_non_nullable
              as double,
      overallConfidence: null == overallConfidence
          ? _value.overallConfidence
          : overallConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      overallRetention: null == overallRetention
          ? _value.overallRetention
          : overallRetention // ignore: cast_nullable_to_non_nullable
              as double,
      chapters: null == chapters
          ? _value.chapters
          : chapters // ignore: cast_nullable_to_non_nullable
              as List<ChapterMastery>,
      totalQuestionsAttempted: null == totalQuestionsAttempted
          ? _value.totalQuestionsAttempted
          : totalQuestionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestionsCorrect: null == totalQuestionsCorrect
          ? _value.totalQuestionsCorrect
          : totalQuestionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      avgTimePerQuestion: null == avgTimePerQuestion
          ? _value.avgTimePerQuestion
          : avgTimePerQuestion // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as SubjectStatus,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SubjectMasteryImplCopyWith<$Res>
    implements $SubjectMasteryCopyWith<$Res> {
  factory _$$SubjectMasteryImplCopyWith(_$SubjectMasteryImpl value,
          $Res Function(_$SubjectMasteryImpl) then) =
      __$$SubjectMasteryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String subject,
      int grade,
      double overallMastery,
      double overallConfidence,
      double overallRetention,
      List<ChapterMastery> chapters,
      int totalQuestionsAttempted,
      int totalQuestionsCorrect,
      double avgTimePerQuestion,
      SubjectStatus status});
}

/// @nodoc
class __$$SubjectMasteryImplCopyWithImpl<$Res>
    extends _$SubjectMasteryCopyWithImpl<$Res, _$SubjectMasteryImpl>
    implements _$$SubjectMasteryImplCopyWith<$Res> {
  __$$SubjectMasteryImplCopyWithImpl(
      _$SubjectMasteryImpl _value, $Res Function(_$SubjectMasteryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? subject = null,
    Object? grade = null,
    Object? overallMastery = null,
    Object? overallConfidence = null,
    Object? overallRetention = null,
    Object? chapters = null,
    Object? totalQuestionsAttempted = null,
    Object? totalQuestionsCorrect = null,
    Object? avgTimePerQuestion = null,
    Object? status = null,
  }) {
    return _then(_$SubjectMasteryImpl(
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      overallMastery: null == overallMastery
          ? _value.overallMastery
          : overallMastery // ignore: cast_nullable_to_non_nullable
              as double,
      overallConfidence: null == overallConfidence
          ? _value.overallConfidence
          : overallConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      overallRetention: null == overallRetention
          ? _value.overallRetention
          : overallRetention // ignore: cast_nullable_to_non_nullable
              as double,
      chapters: null == chapters
          ? _value._chapters
          : chapters // ignore: cast_nullable_to_non_nullable
              as List<ChapterMastery>,
      totalQuestionsAttempted: null == totalQuestionsAttempted
          ? _value.totalQuestionsAttempted
          : totalQuestionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestionsCorrect: null == totalQuestionsCorrect
          ? _value.totalQuestionsCorrect
          : totalQuestionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      avgTimePerQuestion: null == avgTimePerQuestion
          ? _value.avgTimePerQuestion
          : avgTimePerQuestion // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as SubjectStatus,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SubjectMasteryImpl implements _SubjectMastery {
  const _$SubjectMasteryImpl(
      {required this.subject,
      required this.grade,
      required this.overallMastery,
      required this.overallConfidence,
      required this.overallRetention,
      required final List<ChapterMastery> chapters,
      required this.totalQuestionsAttempted,
      required this.totalQuestionsCorrect,
      required this.avgTimePerQuestion,
      required this.status})
      : _chapters = chapters;

  factory _$SubjectMasteryImpl.fromJson(Map<String, dynamic> json) =>
      _$$SubjectMasteryImplFromJson(json);

  @override
  final String subject;
  @override
  final int grade;
  @override
  final double overallMastery;
  @override
  final double overallConfidence;
  @override
  final double overallRetention;
  final List<ChapterMastery> _chapters;
  @override
  List<ChapterMastery> get chapters {
    if (_chapters is EqualUnmodifiableListView) return _chapters;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_chapters);
  }

  @override
  final int totalQuestionsAttempted;
  @override
  final int totalQuestionsCorrect;
  @override
  final double avgTimePerQuestion;
  @override
  final SubjectStatus status;

  @override
  String toString() {
    return 'SubjectMastery(subject: $subject, grade: $grade, overallMastery: $overallMastery, overallConfidence: $overallConfidence, overallRetention: $overallRetention, chapters: $chapters, totalQuestionsAttempted: $totalQuestionsAttempted, totalQuestionsCorrect: $totalQuestionsCorrect, avgTimePerQuestion: $avgTimePerQuestion, status: $status)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SubjectMasteryImpl &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.overallMastery, overallMastery) ||
                other.overallMastery == overallMastery) &&
            (identical(other.overallConfidence, overallConfidence) ||
                other.overallConfidence == overallConfidence) &&
            (identical(other.overallRetention, overallRetention) ||
                other.overallRetention == overallRetention) &&
            const DeepCollectionEquality().equals(other._chapters, _chapters) &&
            (identical(
                    other.totalQuestionsAttempted, totalQuestionsAttempted) ||
                other.totalQuestionsAttempted == totalQuestionsAttempted) &&
            (identical(other.totalQuestionsCorrect, totalQuestionsCorrect) ||
                other.totalQuestionsCorrect == totalQuestionsCorrect) &&
            (identical(other.avgTimePerQuestion, avgTimePerQuestion) ||
                other.avgTimePerQuestion == avgTimePerQuestion) &&
            (identical(other.status, status) || other.status == status));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      subject,
      grade,
      overallMastery,
      overallConfidence,
      overallRetention,
      const DeepCollectionEquality().hash(_chapters),
      totalQuestionsAttempted,
      totalQuestionsCorrect,
      avgTimePerQuestion,
      status);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SubjectMasteryImplCopyWith<_$SubjectMasteryImpl> get copyWith =>
      __$$SubjectMasteryImplCopyWithImpl<_$SubjectMasteryImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SubjectMasteryImplToJson(
      this,
    );
  }
}

abstract class _SubjectMastery implements SubjectMastery {
  const factory _SubjectMastery(
      {required final String subject,
      required final int grade,
      required final double overallMastery,
      required final double overallConfidence,
      required final double overallRetention,
      required final List<ChapterMastery> chapters,
      required final int totalQuestionsAttempted,
      required final int totalQuestionsCorrect,
      required final double avgTimePerQuestion,
      required final SubjectStatus status}) = _$SubjectMasteryImpl;

  factory _SubjectMastery.fromJson(Map<String, dynamic> json) =
      _$SubjectMasteryImpl.fromJson;

  @override
  String get subject;
  @override
  int get grade;
  @override
  double get overallMastery;
  @override
  double get overallConfidence;
  @override
  double get overallRetention;
  @override
  List<ChapterMastery> get chapters;
  @override
  int get totalQuestionsAttempted;
  @override
  int get totalQuestionsCorrect;
  @override
  double get avgTimePerQuestion;
  @override
  SubjectStatus get status;
  @override
  @JsonKey(ignore: true)
  _$$SubjectMasteryImplCopyWith<_$SubjectMasteryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MasterySummary _$MasterySummaryFromJson(Map<String, dynamic> json) {
  return _MasterySummary.fromJson(json);
}

/// @nodoc
mixin _$MasterySummary {
  double get overallMastery => throw _privateConstructorUsedError;
  double get overallConfidence => throw _privateConstructorUsedError;
  double get overallRetention => throw _privateConstructorUsedError;
  int get totalConcepts => throw _privateConstructorUsedError;
  int get masteredConcepts => throw _privateConstructorUsedError;
  int get weakConcepts => throw _privateConstructorUsedError;
  int get notAttemptedConcepts => throw _privateConstructorUsedError;
  int get totalQuestionsAttempted => throw _privateConstructorUsedError;
  int get totalQuestionsCorrect => throw _privateConstructorUsedError;
  double get accuracyRate => throw _privateConstructorUsedError;
  Map<String, int> get bloomDistribution => throw _privateConstructorUsedError;
  Map<String, int> get difficultyDistribution =>
      throw _privateConstructorUsedError;
  List<String> get topStrengths => throw _privateConstructorUsedError;
  List<String> get topWeaknesses => throw _privateConstructorUsedError;
  List<ActionableRecommendation> get recommendations =>
      throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MasterySummaryCopyWith<MasterySummary> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MasterySummaryCopyWith<$Res> {
  factory $MasterySummaryCopyWith(
          MasterySummary value, $Res Function(MasterySummary) then) =
      _$MasterySummaryCopyWithImpl<$Res, MasterySummary>;
  @useResult
  $Res call(
      {double overallMastery,
      double overallConfidence,
      double overallRetention,
      int totalConcepts,
      int masteredConcepts,
      int weakConcepts,
      int notAttemptedConcepts,
      int totalQuestionsAttempted,
      int totalQuestionsCorrect,
      double accuracyRate,
      Map<String, int> bloomDistribution,
      Map<String, int> difficultyDistribution,
      List<String> topStrengths,
      List<String> topWeaknesses,
      List<ActionableRecommendation> recommendations});
}

/// @nodoc
class _$MasterySummaryCopyWithImpl<$Res, $Val extends MasterySummary>
    implements $MasterySummaryCopyWith<$Res> {
  _$MasterySummaryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? overallMastery = null,
    Object? overallConfidence = null,
    Object? overallRetention = null,
    Object? totalConcepts = null,
    Object? masteredConcepts = null,
    Object? weakConcepts = null,
    Object? notAttemptedConcepts = null,
    Object? totalQuestionsAttempted = null,
    Object? totalQuestionsCorrect = null,
    Object? accuracyRate = null,
    Object? bloomDistribution = null,
    Object? difficultyDistribution = null,
    Object? topStrengths = null,
    Object? topWeaknesses = null,
    Object? recommendations = null,
  }) {
    return _then(_value.copyWith(
      overallMastery: null == overallMastery
          ? _value.overallMastery
          : overallMastery // ignore: cast_nullable_to_non_nullable
              as double,
      overallConfidence: null == overallConfidence
          ? _value.overallConfidence
          : overallConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      overallRetention: null == overallRetention
          ? _value.overallRetention
          : overallRetention // ignore: cast_nullable_to_non_nullable
              as double,
      totalConcepts: null == totalConcepts
          ? _value.totalConcepts
          : totalConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      masteredConcepts: null == masteredConcepts
          ? _value.masteredConcepts
          : masteredConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      weakConcepts: null == weakConcepts
          ? _value.weakConcepts
          : weakConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      notAttemptedConcepts: null == notAttemptedConcepts
          ? _value.notAttemptedConcepts
          : notAttemptedConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestionsAttempted: null == totalQuestionsAttempted
          ? _value.totalQuestionsAttempted
          : totalQuestionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestionsCorrect: null == totalQuestionsCorrect
          ? _value.totalQuestionsCorrect
          : totalQuestionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      accuracyRate: null == accuracyRate
          ? _value.accuracyRate
          : accuracyRate // ignore: cast_nullable_to_non_nullable
              as double,
      bloomDistribution: null == bloomDistribution
          ? _value.bloomDistribution
          : bloomDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      difficultyDistribution: null == difficultyDistribution
          ? _value.difficultyDistribution
          : difficultyDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      topStrengths: null == topStrengths
          ? _value.topStrengths
          : topStrengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      topWeaknesses: null == topWeaknesses
          ? _value.topWeaknesses
          : topWeaknesses // ignore: cast_nullable_to_non_nullable
              as List<String>,
      recommendations: null == recommendations
          ? _value.recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MasterySummaryImplCopyWith<$Res>
    implements $MasterySummaryCopyWith<$Res> {
  factory _$$MasterySummaryImplCopyWith(_$MasterySummaryImpl value,
          $Res Function(_$MasterySummaryImpl) then) =
      __$$MasterySummaryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double overallMastery,
      double overallConfidence,
      double overallRetention,
      int totalConcepts,
      int masteredConcepts,
      int weakConcepts,
      int notAttemptedConcepts,
      int totalQuestionsAttempted,
      int totalQuestionsCorrect,
      double accuracyRate,
      Map<String, int> bloomDistribution,
      Map<String, int> difficultyDistribution,
      List<String> topStrengths,
      List<String> topWeaknesses,
      List<ActionableRecommendation> recommendations});
}

/// @nodoc
class __$$MasterySummaryImplCopyWithImpl<$Res>
    extends _$MasterySummaryCopyWithImpl<$Res, _$MasterySummaryImpl>
    implements _$$MasterySummaryImplCopyWith<$Res> {
  __$$MasterySummaryImplCopyWithImpl(
      _$MasterySummaryImpl _value, $Res Function(_$MasterySummaryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? overallMastery = null,
    Object? overallConfidence = null,
    Object? overallRetention = null,
    Object? totalConcepts = null,
    Object? masteredConcepts = null,
    Object? weakConcepts = null,
    Object? notAttemptedConcepts = null,
    Object? totalQuestionsAttempted = null,
    Object? totalQuestionsCorrect = null,
    Object? accuracyRate = null,
    Object? bloomDistribution = null,
    Object? difficultyDistribution = null,
    Object? topStrengths = null,
    Object? topWeaknesses = null,
    Object? recommendations = null,
  }) {
    return _then(_$MasterySummaryImpl(
      overallMastery: null == overallMastery
          ? _value.overallMastery
          : overallMastery // ignore: cast_nullable_to_non_nullable
              as double,
      overallConfidence: null == overallConfidence
          ? _value.overallConfidence
          : overallConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      overallRetention: null == overallRetention
          ? _value.overallRetention
          : overallRetention // ignore: cast_nullable_to_non_nullable
              as double,
      totalConcepts: null == totalConcepts
          ? _value.totalConcepts
          : totalConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      masteredConcepts: null == masteredConcepts
          ? _value.masteredConcepts
          : masteredConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      weakConcepts: null == weakConcepts
          ? _value.weakConcepts
          : weakConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      notAttemptedConcepts: null == notAttemptedConcepts
          ? _value.notAttemptedConcepts
          : notAttemptedConcepts // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestionsAttempted: null == totalQuestionsAttempted
          ? _value.totalQuestionsAttempted
          : totalQuestionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestionsCorrect: null == totalQuestionsCorrect
          ? _value.totalQuestionsCorrect
          : totalQuestionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      accuracyRate: null == accuracyRate
          ? _value.accuracyRate
          : accuracyRate // ignore: cast_nullable_to_non_nullable
              as double,
      bloomDistribution: null == bloomDistribution
          ? _value._bloomDistribution
          : bloomDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      difficultyDistribution: null == difficultyDistribution
          ? _value._difficultyDistribution
          : difficultyDistribution // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      topStrengths: null == topStrengths
          ? _value._topStrengths
          : topStrengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      topWeaknesses: null == topWeaknesses
          ? _value._topWeaknesses
          : topWeaknesses // ignore: cast_nullable_to_non_nullable
              as List<String>,
      recommendations: null == recommendations
          ? _value._recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MasterySummaryImpl implements _MasterySummary {
  const _$MasterySummaryImpl(
      {required this.overallMastery,
      required this.overallConfidence,
      required this.overallRetention,
      required this.totalConcepts,
      required this.masteredConcepts,
      required this.weakConcepts,
      required this.notAttemptedConcepts,
      required this.totalQuestionsAttempted,
      required this.totalQuestionsCorrect,
      required this.accuracyRate,
      required final Map<String, int> bloomDistribution,
      required final Map<String, int> difficultyDistribution,
      required final List<String> topStrengths,
      required final List<String> topWeaknesses,
      required final List<ActionableRecommendation> recommendations})
      : _bloomDistribution = bloomDistribution,
        _difficultyDistribution = difficultyDistribution,
        _topStrengths = topStrengths,
        _topWeaknesses = topWeaknesses,
        _recommendations = recommendations;

  factory _$MasterySummaryImpl.fromJson(Map<String, dynamic> json) =>
      _$$MasterySummaryImplFromJson(json);

  @override
  final double overallMastery;
  @override
  final double overallConfidence;
  @override
  final double overallRetention;
  @override
  final int totalConcepts;
  @override
  final int masteredConcepts;
  @override
  final int weakConcepts;
  @override
  final int notAttemptedConcepts;
  @override
  final int totalQuestionsAttempted;
  @override
  final int totalQuestionsCorrect;
  @override
  final double accuracyRate;
  final Map<String, int> _bloomDistribution;
  @override
  Map<String, int> get bloomDistribution {
    if (_bloomDistribution is EqualUnmodifiableMapView)
      return _bloomDistribution;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_bloomDistribution);
  }

  final Map<String, int> _difficultyDistribution;
  @override
  Map<String, int> get difficultyDistribution {
    if (_difficultyDistribution is EqualUnmodifiableMapView)
      return _difficultyDistribution;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_difficultyDistribution);
  }

  final List<String> _topStrengths;
  @override
  List<String> get topStrengths {
    if (_topStrengths is EqualUnmodifiableListView) return _topStrengths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_topStrengths);
  }

  final List<String> _topWeaknesses;
  @override
  List<String> get topWeaknesses {
    if (_topWeaknesses is EqualUnmodifiableListView) return _topWeaknesses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_topWeaknesses);
  }

  final List<ActionableRecommendation> _recommendations;
  @override
  List<ActionableRecommendation> get recommendations {
    if (_recommendations is EqualUnmodifiableListView) return _recommendations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendations);
  }

  @override
  String toString() {
    return 'MasterySummary(overallMastery: $overallMastery, overallConfidence: $overallConfidence, overallRetention: $overallRetention, totalConcepts: $totalConcepts, masteredConcepts: $masteredConcepts, weakConcepts: $weakConcepts, notAttemptedConcepts: $notAttemptedConcepts, totalQuestionsAttempted: $totalQuestionsAttempted, totalQuestionsCorrect: $totalQuestionsCorrect, accuracyRate: $accuracyRate, bloomDistribution: $bloomDistribution, difficultyDistribution: $difficultyDistribution, topStrengths: $topStrengths, topWeaknesses: $topWeaknesses, recommendations: $recommendations)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MasterySummaryImpl &&
            (identical(other.overallMastery, overallMastery) ||
                other.overallMastery == overallMastery) &&
            (identical(other.overallConfidence, overallConfidence) ||
                other.overallConfidence == overallConfidence) &&
            (identical(other.overallRetention, overallRetention) ||
                other.overallRetention == overallRetention) &&
            (identical(other.totalConcepts, totalConcepts) ||
                other.totalConcepts == totalConcepts) &&
            (identical(other.masteredConcepts, masteredConcepts) ||
                other.masteredConcepts == masteredConcepts) &&
            (identical(other.weakConcepts, weakConcepts) ||
                other.weakConcepts == weakConcepts) &&
            (identical(other.notAttemptedConcepts, notAttemptedConcepts) ||
                other.notAttemptedConcepts == notAttemptedConcepts) &&
            (identical(
                    other.totalQuestionsAttempted, totalQuestionsAttempted) ||
                other.totalQuestionsAttempted == totalQuestionsAttempted) &&
            (identical(other.totalQuestionsCorrect, totalQuestionsCorrect) ||
                other.totalQuestionsCorrect == totalQuestionsCorrect) &&
            (identical(other.accuracyRate, accuracyRate) ||
                other.accuracyRate == accuracyRate) &&
            const DeepCollectionEquality()
                .equals(other._bloomDistribution, _bloomDistribution) &&
            const DeepCollectionEquality().equals(
                other._difficultyDistribution, _difficultyDistribution) &&
            const DeepCollectionEquality()
                .equals(other._topStrengths, _topStrengths) &&
            const DeepCollectionEquality()
                .equals(other._topWeaknesses, _topWeaknesses) &&
            const DeepCollectionEquality()
                .equals(other._recommendations, _recommendations));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      overallMastery,
      overallConfidence,
      overallRetention,
      totalConcepts,
      masteredConcepts,
      weakConcepts,
      notAttemptedConcepts,
      totalQuestionsAttempted,
      totalQuestionsCorrect,
      accuracyRate,
      const DeepCollectionEquality().hash(_bloomDistribution),
      const DeepCollectionEquality().hash(_difficultyDistribution),
      const DeepCollectionEquality().hash(_topStrengths),
      const DeepCollectionEquality().hash(_topWeaknesses),
      const DeepCollectionEquality().hash(_recommendations));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MasterySummaryImplCopyWith<_$MasterySummaryImpl> get copyWith =>
      __$$MasterySummaryImplCopyWithImpl<_$MasterySummaryImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MasterySummaryImplToJson(
      this,
    );
  }
}

abstract class _MasterySummary implements MasterySummary {
  const factory _MasterySummary(
          {required final double overallMastery,
          required final double overallConfidence,
          required final double overallRetention,
          required final int totalConcepts,
          required final int masteredConcepts,
          required final int weakConcepts,
          required final int notAttemptedConcepts,
          required final int totalQuestionsAttempted,
          required final int totalQuestionsCorrect,
          required final double accuracyRate,
          required final Map<String, int> bloomDistribution,
          required final Map<String, int> difficultyDistribution,
          required final List<String> topStrengths,
          required final List<String> topWeaknesses,
          required final List<ActionableRecommendation> recommendations}) =
      _$MasterySummaryImpl;

  factory _MasterySummary.fromJson(Map<String, dynamic> json) =
      _$MasterySummaryImpl.fromJson;

  @override
  double get overallMastery;
  @override
  double get overallConfidence;
  @override
  double get overallRetention;
  @override
  int get totalConcepts;
  @override
  int get masteredConcepts;
  @override
  int get weakConcepts;
  @override
  int get notAttemptedConcepts;
  @override
  int get totalQuestionsAttempted;
  @override
  int get totalQuestionsCorrect;
  @override
  double get accuracyRate;
  @override
  Map<String, int> get bloomDistribution;
  @override
  Map<String, int> get difficultyDistribution;
  @override
  List<String> get topStrengths;
  @override
  List<String> get topWeaknesses;
  @override
  List<ActionableRecommendation> get recommendations;
  @override
  @JsonKey(ignore: true)
  _$$MasterySummaryImplCopyWith<_$MasterySummaryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MisconceptionFlag _$MisconceptionFlagFromJson(Map<String, dynamic> json) {
  return _MisconceptionFlag.fromJson(json);
}

/// @nodoc
mixin _$MisconceptionFlag {
  String get misconceptionId => throw _privateConstructorUsedError;
  String get misconceptionName => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  double get confidence => throw _privateConstructorUsedError;
  int get occurrenceCount => throw _privateConstructorUsedError;
  DateTime get firstDetectedAt => throw _privateConstructorUsedError;
  DateTime get lastDetectedAt => throw _privateConstructorUsedError;
  MisconceptionSeverity get severity => throw _privateConstructorUsedError;
  List<String> get evidenceQuestionIds => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MisconceptionFlagCopyWith<MisconceptionFlag> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MisconceptionFlagCopyWith<$Res> {
  factory $MisconceptionFlagCopyWith(
          MisconceptionFlag value, $Res Function(MisconceptionFlag) then) =
      _$MisconceptionFlagCopyWithImpl<$Res, MisconceptionFlag>;
  @useResult
  $Res call(
      {String misconceptionId,
      String misconceptionName,
      String description,
      double confidence,
      int occurrenceCount,
      DateTime firstDetectedAt,
      DateTime lastDetectedAt,
      MisconceptionSeverity severity,
      List<String> evidenceQuestionIds});
}

/// @nodoc
class _$MisconceptionFlagCopyWithImpl<$Res, $Val extends MisconceptionFlag>
    implements $MisconceptionFlagCopyWith<$Res> {
  _$MisconceptionFlagCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? misconceptionId = null,
    Object? misconceptionName = null,
    Object? description = null,
    Object? confidence = null,
    Object? occurrenceCount = null,
    Object? firstDetectedAt = null,
    Object? lastDetectedAt = null,
    Object? severity = null,
    Object? evidenceQuestionIds = null,
  }) {
    return _then(_value.copyWith(
      misconceptionId: null == misconceptionId
          ? _value.misconceptionId
          : misconceptionId // ignore: cast_nullable_to_non_nullable
              as String,
      misconceptionName: null == misconceptionName
          ? _value.misconceptionName
          : misconceptionName // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      occurrenceCount: null == occurrenceCount
          ? _value.occurrenceCount
          : occurrenceCount // ignore: cast_nullable_to_non_nullable
              as int,
      firstDetectedAt: null == firstDetectedAt
          ? _value.firstDetectedAt
          : firstDetectedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastDetectedAt: null == lastDetectedAt
          ? _value.lastDetectedAt
          : lastDetectedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      severity: null == severity
          ? _value.severity
          : severity // ignore: cast_nullable_to_non_nullable
              as MisconceptionSeverity,
      evidenceQuestionIds: null == evidenceQuestionIds
          ? _value.evidenceQuestionIds
          : evidenceQuestionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MisconceptionFlagImplCopyWith<$Res>
    implements $MisconceptionFlagCopyWith<$Res> {
  factory _$$MisconceptionFlagImplCopyWith(_$MisconceptionFlagImpl value,
          $Res Function(_$MisconceptionFlagImpl) then) =
      __$$MisconceptionFlagImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String misconceptionId,
      String misconceptionName,
      String description,
      double confidence,
      int occurrenceCount,
      DateTime firstDetectedAt,
      DateTime lastDetectedAt,
      MisconceptionSeverity severity,
      List<String> evidenceQuestionIds});
}

/// @nodoc
class __$$MisconceptionFlagImplCopyWithImpl<$Res>
    extends _$MisconceptionFlagCopyWithImpl<$Res, _$MisconceptionFlagImpl>
    implements _$$MisconceptionFlagImplCopyWith<$Res> {
  __$$MisconceptionFlagImplCopyWithImpl(_$MisconceptionFlagImpl _value,
      $Res Function(_$MisconceptionFlagImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? misconceptionId = null,
    Object? misconceptionName = null,
    Object? description = null,
    Object? confidence = null,
    Object? occurrenceCount = null,
    Object? firstDetectedAt = null,
    Object? lastDetectedAt = null,
    Object? severity = null,
    Object? evidenceQuestionIds = null,
  }) {
    return _then(_$MisconceptionFlagImpl(
      misconceptionId: null == misconceptionId
          ? _value.misconceptionId
          : misconceptionId // ignore: cast_nullable_to_non_nullable
              as String,
      misconceptionName: null == misconceptionName
          ? _value.misconceptionName
          : misconceptionName // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      occurrenceCount: null == occurrenceCount
          ? _value.occurrenceCount
          : occurrenceCount // ignore: cast_nullable_to_non_nullable
              as int,
      firstDetectedAt: null == firstDetectedAt
          ? _value.firstDetectedAt
          : firstDetectedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastDetectedAt: null == lastDetectedAt
          ? _value.lastDetectedAt
          : lastDetectedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      severity: null == severity
          ? _value.severity
          : severity // ignore: cast_nullable_to_non_nullable
              as MisconceptionSeverity,
      evidenceQuestionIds: null == evidenceQuestionIds
          ? _value._evidenceQuestionIds
          : evidenceQuestionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MisconceptionFlagImpl implements _MisconceptionFlag {
  const _$MisconceptionFlagImpl(
      {required this.misconceptionId,
      required this.misconceptionName,
      required this.description,
      required this.confidence,
      required this.occurrenceCount,
      required this.firstDetectedAt,
      required this.lastDetectedAt,
      required this.severity,
      required final List<String> evidenceQuestionIds})
      : _evidenceQuestionIds = evidenceQuestionIds;

  factory _$MisconceptionFlagImpl.fromJson(Map<String, dynamic> json) =>
      _$$MisconceptionFlagImplFromJson(json);

  @override
  final String misconceptionId;
  @override
  final String misconceptionName;
  @override
  final String description;
  @override
  final double confidence;
  @override
  final int occurrenceCount;
  @override
  final DateTime firstDetectedAt;
  @override
  final DateTime lastDetectedAt;
  @override
  final MisconceptionSeverity severity;
  final List<String> _evidenceQuestionIds;
  @override
  List<String> get evidenceQuestionIds {
    if (_evidenceQuestionIds is EqualUnmodifiableListView)
      return _evidenceQuestionIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_evidenceQuestionIds);
  }

  @override
  String toString() {
    return 'MisconceptionFlag(misconceptionId: $misconceptionId, misconceptionName: $misconceptionName, description: $description, confidence: $confidence, occurrenceCount: $occurrenceCount, firstDetectedAt: $firstDetectedAt, lastDetectedAt: $lastDetectedAt, severity: $severity, evidenceQuestionIds: $evidenceQuestionIds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MisconceptionFlagImpl &&
            (identical(other.misconceptionId, misconceptionId) ||
                other.misconceptionId == misconceptionId) &&
            (identical(other.misconceptionName, misconceptionName) ||
                other.misconceptionName == misconceptionName) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.occurrenceCount, occurrenceCount) ||
                other.occurrenceCount == occurrenceCount) &&
            (identical(other.firstDetectedAt, firstDetectedAt) ||
                other.firstDetectedAt == firstDetectedAt) &&
            (identical(other.lastDetectedAt, lastDetectedAt) ||
                other.lastDetectedAt == lastDetectedAt) &&
            (identical(other.severity, severity) ||
                other.severity == severity) &&
            const DeepCollectionEquality()
                .equals(other._evidenceQuestionIds, _evidenceQuestionIds));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      misconceptionId,
      misconceptionName,
      description,
      confidence,
      occurrenceCount,
      firstDetectedAt,
      lastDetectedAt,
      severity,
      const DeepCollectionEquality().hash(_evidenceQuestionIds));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MisconceptionFlagImplCopyWith<_$MisconceptionFlagImpl> get copyWith =>
      __$$MisconceptionFlagImplCopyWithImpl<_$MisconceptionFlagImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MisconceptionFlagImplToJson(
      this,
    );
  }
}

abstract class _MisconceptionFlag implements MisconceptionFlag {
  const factory _MisconceptionFlag(
          {required final String misconceptionId,
          required final String misconceptionName,
          required final String description,
          required final double confidence,
          required final int occurrenceCount,
          required final DateTime firstDetectedAt,
          required final DateTime lastDetectedAt,
          required final MisconceptionSeverity severity,
          required final List<String> evidenceQuestionIds}) =
      _$MisconceptionFlagImpl;

  factory _MisconceptionFlag.fromJson(Map<String, dynamic> json) =
      _$MisconceptionFlagImpl.fromJson;

  @override
  String get misconceptionId;
  @override
  String get misconceptionName;
  @override
  String get description;
  @override
  double get confidence;
  @override
  int get occurrenceCount;
  @override
  DateTime get firstDetectedAt;
  @override
  DateTime get lastDetectedAt;
  @override
  MisconceptionSeverity get severity;
  @override
  List<String> get evidenceQuestionIds;
  @override
  @JsonKey(ignore: true)
  _$$MisconceptionFlagImplCopyWith<_$MisconceptionFlagImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ActionableRecommendation _$ActionableRecommendationFromJson(
    Map<String, dynamic> json) {
  return _ActionableRecommendation.fromJson(json);
}

/// @nodoc
mixin _$ActionableRecommendation {
  String get id => throw _privateConstructorUsedError;
  RecommendationType get type => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get targetConceptId => throw _privateConstructorUsedError;
  String get targetConceptName => throw _privateConstructorUsedError;
  int get estimatedMinutes => throw _privateConstructorUsedError;
  double get successProbability => throw _privateConstructorUsedError;
  Priority get priority => throw _privateConstructorUsedError;
  List<String> get resourceIds => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ActionableRecommendationCopyWith<ActionableRecommendation> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ActionableRecommendationCopyWith<$Res> {
  factory $ActionableRecommendationCopyWith(ActionableRecommendation value,
          $Res Function(ActionableRecommendation) then) =
      _$ActionableRecommendationCopyWithImpl<$Res, ActionableRecommendation>;
  @useResult
  $Res call(
      {String id,
      RecommendationType type,
      String title,
      String description,
      String targetConceptId,
      String targetConceptName,
      int estimatedMinutes,
      double successProbability,
      Priority priority,
      List<String> resourceIds});
}

/// @nodoc
class _$ActionableRecommendationCopyWithImpl<$Res,
        $Val extends ActionableRecommendation>
    implements $ActionableRecommendationCopyWith<$Res> {
  _$ActionableRecommendationCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? type = null,
    Object? title = null,
    Object? description = null,
    Object? targetConceptId = null,
    Object? targetConceptName = null,
    Object? estimatedMinutes = null,
    Object? successProbability = null,
    Object? priority = null,
    Object? resourceIds = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as RecommendationType,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      targetConceptId: null == targetConceptId
          ? _value.targetConceptId
          : targetConceptId // ignore: cast_nullable_to_non_nullable
              as String,
      targetConceptName: null == targetConceptName
          ? _value.targetConceptName
          : targetConceptName // ignore: cast_nullable_to_non_nullable
              as String,
      estimatedMinutes: null == estimatedMinutes
          ? _value.estimatedMinutes
          : estimatedMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      successProbability: null == successProbability
          ? _value.successProbability
          : successProbability // ignore: cast_nullable_to_non_nullable
              as double,
      priority: null == priority
          ? _value.priority
          : priority // ignore: cast_nullable_to_non_nullable
              as Priority,
      resourceIds: null == resourceIds
          ? _value.resourceIds
          : resourceIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ActionableRecommendationImplCopyWith<$Res>
    implements $ActionableRecommendationCopyWith<$Res> {
  factory _$$ActionableRecommendationImplCopyWith(
          _$ActionableRecommendationImpl value,
          $Res Function(_$ActionableRecommendationImpl) then) =
      __$$ActionableRecommendationImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      RecommendationType type,
      String title,
      String description,
      String targetConceptId,
      String targetConceptName,
      int estimatedMinutes,
      double successProbability,
      Priority priority,
      List<String> resourceIds});
}

/// @nodoc
class __$$ActionableRecommendationImplCopyWithImpl<$Res>
    extends _$ActionableRecommendationCopyWithImpl<$Res,
        _$ActionableRecommendationImpl>
    implements _$$ActionableRecommendationImplCopyWith<$Res> {
  __$$ActionableRecommendationImplCopyWithImpl(
      _$ActionableRecommendationImpl _value,
      $Res Function(_$ActionableRecommendationImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? type = null,
    Object? title = null,
    Object? description = null,
    Object? targetConceptId = null,
    Object? targetConceptName = null,
    Object? estimatedMinutes = null,
    Object? successProbability = null,
    Object? priority = null,
    Object? resourceIds = null,
  }) {
    return _then(_$ActionableRecommendationImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as RecommendationType,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      targetConceptId: null == targetConceptId
          ? _value.targetConceptId
          : targetConceptId // ignore: cast_nullable_to_non_nullable
              as String,
      targetConceptName: null == targetConceptName
          ? _value.targetConceptName
          : targetConceptName // ignore: cast_nullable_to_non_nullable
              as String,
      estimatedMinutes: null == estimatedMinutes
          ? _value.estimatedMinutes
          : estimatedMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      successProbability: null == successProbability
          ? _value.successProbability
          : successProbability // ignore: cast_nullable_to_non_nullable
              as double,
      priority: null == priority
          ? _value.priority
          : priority // ignore: cast_nullable_to_non_nullable
              as Priority,
      resourceIds: null == resourceIds
          ? _value._resourceIds
          : resourceIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ActionableRecommendationImpl implements _ActionableRecommendation {
  const _$ActionableRecommendationImpl(
      {required this.id,
      required this.type,
      required this.title,
      required this.description,
      required this.targetConceptId,
      required this.targetConceptName,
      required this.estimatedMinutes,
      required this.successProbability,
      required this.priority,
      required final List<String> resourceIds})
      : _resourceIds = resourceIds;

  factory _$ActionableRecommendationImpl.fromJson(Map<String, dynamic> json) =>
      _$$ActionableRecommendationImplFromJson(json);

  @override
  final String id;
  @override
  final RecommendationType type;
  @override
  final String title;
  @override
  final String description;
  @override
  final String targetConceptId;
  @override
  final String targetConceptName;
  @override
  final int estimatedMinutes;
  @override
  final double successProbability;
  @override
  final Priority priority;
  final List<String> _resourceIds;
  @override
  List<String> get resourceIds {
    if (_resourceIds is EqualUnmodifiableListView) return _resourceIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_resourceIds);
  }

  @override
  String toString() {
    return 'ActionableRecommendation(id: $id, type: $type, title: $title, description: $description, targetConceptId: $targetConceptId, targetConceptName: $targetConceptName, estimatedMinutes: $estimatedMinutes, successProbability: $successProbability, priority: $priority, resourceIds: $resourceIds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ActionableRecommendationImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.targetConceptId, targetConceptId) ||
                other.targetConceptId == targetConceptId) &&
            (identical(other.targetConceptName, targetConceptName) ||
                other.targetConceptName == targetConceptName) &&
            (identical(other.estimatedMinutes, estimatedMinutes) ||
                other.estimatedMinutes == estimatedMinutes) &&
            (identical(other.successProbability, successProbability) ||
                other.successProbability == successProbability) &&
            (identical(other.priority, priority) ||
                other.priority == priority) &&
            const DeepCollectionEquality()
                .equals(other._resourceIds, _resourceIds));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      type,
      title,
      description,
      targetConceptId,
      targetConceptName,
      estimatedMinutes,
      successProbability,
      priority,
      const DeepCollectionEquality().hash(_resourceIds));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ActionableRecommendationImplCopyWith<_$ActionableRecommendationImpl>
      get copyWith => __$$ActionableRecommendationImplCopyWithImpl<
          _$ActionableRecommendationImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ActionableRecommendationImplToJson(
      this,
    );
  }
}

abstract class _ActionableRecommendation implements ActionableRecommendation {
  const factory _ActionableRecommendation(
          {required final String id,
          required final RecommendationType type,
          required final String title,
          required final String description,
          required final String targetConceptId,
          required final String targetConceptName,
          required final int estimatedMinutes,
          required final double successProbability,
          required final Priority priority,
          required final List<String> resourceIds}) =
      _$ActionableRecommendationImpl;

  factory _ActionableRecommendation.fromJson(Map<String, dynamic> json) =
      _$ActionableRecommendationImpl.fromJson;

  @override
  String get id;
  @override
  RecommendationType get type;
  @override
  String get title;
  @override
  String get description;
  @override
  String get targetConceptId;
  @override
  String get targetConceptName;
  @override
  int get estimatedMinutes;
  @override
  double get successProbability;
  @override
  Priority get priority;
  @override
  List<String> get resourceIds;
  @override
  @JsonKey(ignore: true)
  _$$ActionableRecommendationImplCopyWith<_$ActionableRecommendationImpl>
      get copyWith => throw _privateConstructorUsedError;
}
