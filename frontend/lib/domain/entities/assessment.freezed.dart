// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'assessment.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

Assessment _$AssessmentFromJson(Map<String, dynamic> json) {
  return _Assessment.fromJson(json);
}

/// @nodoc
mixin _$Assessment {
  String get id => throw _privateConstructorUsedError;
  String get schoolId => throw _privateConstructorUsedError;
  String get teacherId => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  List<String> get chapterIds => throw _privateConstructorUsedError;
  Blueprint get blueprint => throw _privateConstructorUsedError;
  AssessmentStatus get status => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  DateTime get updatedAt => throw _privateConstructorUsedError;
  DateTime? get scheduledAt => throw _privateConstructorUsedError;
  DateTime? get completedAt => throw _privateConstructorUsedError;
  String? get templateId => throw _privateConstructorUsedError;
  Map<String, dynamic> get metadata => throw _privateConstructorUsedError;
  List<String> get selectedQuestionIds => throw _privateConstructorUsedError;
  String? get generatedPaperId => throw _privateConstructorUsedError;
  int? get totalStudents => throw _privateConstructorUsedError;
  int? get evaluatedCount => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AssessmentCopyWith<Assessment> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AssessmentCopyWith<$Res> {
  factory $AssessmentCopyWith(
          Assessment value, $Res Function(Assessment) then) =
      _$AssessmentCopyWithImpl<$Res, Assessment>;
  @useResult
  $Res call(
      {String id,
      String schoolId,
      String teacherId,
      String title,
      String subject,
      int grade,
      List<String> chapterIds,
      Blueprint blueprint,
      AssessmentStatus status,
      DateTime createdAt,
      DateTime updatedAt,
      DateTime? scheduledAt,
      DateTime? completedAt,
      String? templateId,
      Map<String, dynamic> metadata,
      List<String> selectedQuestionIds,
      String? generatedPaperId,
      int? totalStudents,
      int? evaluatedCount});

  $BlueprintCopyWith<$Res> get blueprint;
}

/// @nodoc
class _$AssessmentCopyWithImpl<$Res, $Val extends Assessment>
    implements $AssessmentCopyWith<$Res> {
  _$AssessmentCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? schoolId = null,
    Object? teacherId = null,
    Object? title = null,
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? blueprint = null,
    Object? status = null,
    Object? createdAt = null,
    Object? updatedAt = null,
    Object? scheduledAt = freezed,
    Object? completedAt = freezed,
    Object? templateId = freezed,
    Object? metadata = null,
    Object? selectedQuestionIds = null,
    Object? generatedPaperId = freezed,
    Object? totalStudents = freezed,
    Object? evaluatedCount = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      teacherId: null == teacherId
          ? _value.teacherId
          : teacherId // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      chapterIds: null == chapterIds
          ? _value.chapterIds
          : chapterIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blueprint: null == blueprint
          ? _value.blueprint
          : blueprint // ignore: cast_nullable_to_non_nullable
              as Blueprint,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as AssessmentStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      scheduledAt: freezed == scheduledAt
          ? _value.scheduledAt
          : scheduledAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      completedAt: freezed == completedAt
          ? _value.completedAt
          : completedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      templateId: freezed == templateId
          ? _value.templateId
          : templateId // ignore: cast_nullable_to_non_nullable
              as String?,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      selectedQuestionIds: null == selectedQuestionIds
          ? _value.selectedQuestionIds
          : selectedQuestionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      generatedPaperId: freezed == generatedPaperId
          ? _value.generatedPaperId
          : generatedPaperId // ignore: cast_nullable_to_non_nullable
              as String?,
      totalStudents: freezed == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int?,
      evaluatedCount: freezed == evaluatedCount
          ? _value.evaluatedCount
          : evaluatedCount // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $BlueprintCopyWith<$Res> get blueprint {
    return $BlueprintCopyWith<$Res>(_value.blueprint, (value) {
      return _then(_value.copyWith(blueprint: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AssessmentImplCopyWith<$Res>
    implements $AssessmentCopyWith<$Res> {
  factory _$$AssessmentImplCopyWith(
          _$AssessmentImpl value, $Res Function(_$AssessmentImpl) then) =
      __$$AssessmentImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String schoolId,
      String teacherId,
      String title,
      String subject,
      int grade,
      List<String> chapterIds,
      Blueprint blueprint,
      AssessmentStatus status,
      DateTime createdAt,
      DateTime updatedAt,
      DateTime? scheduledAt,
      DateTime? completedAt,
      String? templateId,
      Map<String, dynamic> metadata,
      List<String> selectedQuestionIds,
      String? generatedPaperId,
      int? totalStudents,
      int? evaluatedCount});

  @override
  $BlueprintCopyWith<$Res> get blueprint;
}

/// @nodoc
class __$$AssessmentImplCopyWithImpl<$Res>
    extends _$AssessmentCopyWithImpl<$Res, _$AssessmentImpl>
    implements _$$AssessmentImplCopyWith<$Res> {
  __$$AssessmentImplCopyWithImpl(
      _$AssessmentImpl _value, $Res Function(_$AssessmentImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? schoolId = null,
    Object? teacherId = null,
    Object? title = null,
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? blueprint = null,
    Object? status = null,
    Object? createdAt = null,
    Object? updatedAt = null,
    Object? scheduledAt = freezed,
    Object? completedAt = freezed,
    Object? templateId = freezed,
    Object? metadata = null,
    Object? selectedQuestionIds = null,
    Object? generatedPaperId = freezed,
    Object? totalStudents = freezed,
    Object? evaluatedCount = freezed,
  }) {
    return _then(_$AssessmentImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      teacherId: null == teacherId
          ? _value.teacherId
          : teacherId // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      chapterIds: null == chapterIds
          ? _value._chapterIds
          : chapterIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blueprint: null == blueprint
          ? _value.blueprint
          : blueprint // ignore: cast_nullable_to_non_nullable
              as Blueprint,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as AssessmentStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      scheduledAt: freezed == scheduledAt
          ? _value.scheduledAt
          : scheduledAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      completedAt: freezed == completedAt
          ? _value.completedAt
          : completedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      templateId: freezed == templateId
          ? _value.templateId
          : templateId // ignore: cast_nullable_to_non_nullable
              as String?,
      metadata: null == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      selectedQuestionIds: null == selectedQuestionIds
          ? _value._selectedQuestionIds
          : selectedQuestionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      generatedPaperId: freezed == generatedPaperId
          ? _value.generatedPaperId
          : generatedPaperId // ignore: cast_nullable_to_non_nullable
              as String?,
      totalStudents: freezed == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int?,
      evaluatedCount: freezed == evaluatedCount
          ? _value.evaluatedCount
          : evaluatedCount // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AssessmentImpl implements _Assessment {
  const _$AssessmentImpl(
      {required this.id,
      required this.schoolId,
      required this.teacherId,
      required this.title,
      required this.subject,
      required this.grade,
      required final List<String> chapterIds,
      required this.blueprint,
      required this.status,
      required this.createdAt,
      required this.updatedAt,
      this.scheduledAt,
      this.completedAt,
      this.templateId,
      final Map<String, dynamic> metadata = const {},
      final List<String> selectedQuestionIds = const [],
      this.generatedPaperId,
      this.totalStudents,
      this.evaluatedCount})
      : _chapterIds = chapterIds,
        _metadata = metadata,
        _selectedQuestionIds = selectedQuestionIds;

  factory _$AssessmentImpl.fromJson(Map<String, dynamic> json) =>
      _$$AssessmentImplFromJson(json);

  @override
  final String id;
  @override
  final String schoolId;
  @override
  final String teacherId;
  @override
  final String title;
  @override
  final String subject;
  @override
  final int grade;
  final List<String> _chapterIds;
  @override
  List<String> get chapterIds {
    if (_chapterIds is EqualUnmodifiableListView) return _chapterIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_chapterIds);
  }

  @override
  final Blueprint blueprint;
  @override
  final AssessmentStatus status;
  @override
  final DateTime createdAt;
  @override
  final DateTime updatedAt;
  @override
  final DateTime? scheduledAt;
  @override
  final DateTime? completedAt;
  @override
  final String? templateId;
  final Map<String, dynamic> _metadata;
  @override
  @JsonKey()
  Map<String, dynamic> get metadata {
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_metadata);
  }

  final List<String> _selectedQuestionIds;
  @override
  @JsonKey()
  List<String> get selectedQuestionIds {
    if (_selectedQuestionIds is EqualUnmodifiableListView)
      return _selectedQuestionIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_selectedQuestionIds);
  }

  @override
  final String? generatedPaperId;
  @override
  final int? totalStudents;
  @override
  final int? evaluatedCount;

  @override
  String toString() {
    return 'Assessment(id: $id, schoolId: $schoolId, teacherId: $teacherId, title: $title, subject: $subject, grade: $grade, chapterIds: $chapterIds, blueprint: $blueprint, status: $status, createdAt: $createdAt, updatedAt: $updatedAt, scheduledAt: $scheduledAt, completedAt: $completedAt, templateId: $templateId, metadata: $metadata, selectedQuestionIds: $selectedQuestionIds, generatedPaperId: $generatedPaperId, totalStudents: $totalStudents, evaluatedCount: $evaluatedCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AssessmentImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.schoolId, schoolId) ||
                other.schoolId == schoolId) &&
            (identical(other.teacherId, teacherId) ||
                other.teacherId == teacherId) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality()
                .equals(other._chapterIds, _chapterIds) &&
            (identical(other.blueprint, blueprint) ||
                other.blueprint == blueprint) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.updatedAt, updatedAt) ||
                other.updatedAt == updatedAt) &&
            (identical(other.scheduledAt, scheduledAt) ||
                other.scheduledAt == scheduledAt) &&
            (identical(other.completedAt, completedAt) ||
                other.completedAt == completedAt) &&
            (identical(other.templateId, templateId) ||
                other.templateId == templateId) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata) &&
            const DeepCollectionEquality()
                .equals(other._selectedQuestionIds, _selectedQuestionIds) &&
            (identical(other.generatedPaperId, generatedPaperId) ||
                other.generatedPaperId == generatedPaperId) &&
            (identical(other.totalStudents, totalStudents) ||
                other.totalStudents == totalStudents) &&
            (identical(other.evaluatedCount, evaluatedCount) ||
                other.evaluatedCount == evaluatedCount));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        id,
        schoolId,
        teacherId,
        title,
        subject,
        grade,
        const DeepCollectionEquality().hash(_chapterIds),
        blueprint,
        status,
        createdAt,
        updatedAt,
        scheduledAt,
        completedAt,
        templateId,
        const DeepCollectionEquality().hash(_metadata),
        const DeepCollectionEquality().hash(_selectedQuestionIds),
        generatedPaperId,
        totalStudents,
        evaluatedCount
      ]);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AssessmentImplCopyWith<_$AssessmentImpl> get copyWith =>
      __$$AssessmentImplCopyWithImpl<_$AssessmentImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AssessmentImplToJson(
      this,
    );
  }
}

abstract class _Assessment implements Assessment {
  const factory _Assessment(
      {required final String id,
      required final String schoolId,
      required final String teacherId,
      required final String title,
      required final String subject,
      required final int grade,
      required final List<String> chapterIds,
      required final Blueprint blueprint,
      required final AssessmentStatus status,
      required final DateTime createdAt,
      required final DateTime updatedAt,
      final DateTime? scheduledAt,
      final DateTime? completedAt,
      final String? templateId,
      final Map<String, dynamic> metadata,
      final List<String> selectedQuestionIds,
      final String? generatedPaperId,
      final int? totalStudents,
      final int? evaluatedCount}) = _$AssessmentImpl;

  factory _Assessment.fromJson(Map<String, dynamic> json) =
      _$AssessmentImpl.fromJson;

  @override
  String get id;
  @override
  String get schoolId;
  @override
  String get teacherId;
  @override
  String get title;
  @override
  String get subject;
  @override
  int get grade;
  @override
  List<String> get chapterIds;
  @override
  Blueprint get blueprint;
  @override
  AssessmentStatus get status;
  @override
  DateTime get createdAt;
  @override
  DateTime get updatedAt;
  @override
  DateTime? get scheduledAt;
  @override
  DateTime? get completedAt;
  @override
  String? get templateId;
  @override
  Map<String, dynamic> get metadata;
  @override
  List<String> get selectedQuestionIds;
  @override
  String? get generatedPaperId;
  @override
  int? get totalStudents;
  @override
  int? get evaluatedCount;
  @override
  @JsonKey(ignore: true)
  _$$AssessmentImplCopyWith<_$AssessmentImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
