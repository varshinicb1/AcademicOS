// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'requests.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

CreateAssessmentRequest _$CreateAssessmentRequestFromJson(
    Map<String, dynamic> json) {
  return _CreateAssessmentRequest.fromJson(json);
}

/// @nodoc
mixin _$CreateAssessmentRequest {
  String get teacherId => throw _privateConstructorUsedError;
  String get schoolId => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  List<String> get chapterIds => throw _privateConstructorUsedError;
  BlueprintRequest get blueprint => throw _privateConstructorUsedError;
  String? get templateId => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CreateAssessmentRequestCopyWith<CreateAssessmentRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CreateAssessmentRequestCopyWith<$Res> {
  factory $CreateAssessmentRequestCopyWith(CreateAssessmentRequest value,
          $Res Function(CreateAssessmentRequest) then) =
      _$CreateAssessmentRequestCopyWithImpl<$Res, CreateAssessmentRequest>;
  @useResult
  $Res call(
      {String teacherId,
      String schoolId,
      String title,
      String subject,
      int grade,
      List<String> chapterIds,
      BlueprintRequest blueprint,
      String? templateId});

  $BlueprintRequestCopyWith<$Res> get blueprint;
}

/// @nodoc
class _$CreateAssessmentRequestCopyWithImpl<$Res,
        $Val extends CreateAssessmentRequest>
    implements $CreateAssessmentRequestCopyWith<$Res> {
  _$CreateAssessmentRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? teacherId = null,
    Object? schoolId = null,
    Object? title = null,
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? blueprint = null,
    Object? templateId = freezed,
  }) {
    return _then(_value.copyWith(
      teacherId: null == teacherId
          ? _value.teacherId
          : teacherId // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
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
              as BlueprintRequest,
      templateId: freezed == templateId
          ? _value.templateId
          : templateId // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $BlueprintRequestCopyWith<$Res> get blueprint {
    return $BlueprintRequestCopyWith<$Res>(_value.blueprint, (value) {
      return _then(_value.copyWith(blueprint: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$CreateAssessmentRequestImplCopyWith<$Res>
    implements $CreateAssessmentRequestCopyWith<$Res> {
  factory _$$CreateAssessmentRequestImplCopyWith(
          _$CreateAssessmentRequestImpl value,
          $Res Function(_$CreateAssessmentRequestImpl) then) =
      __$$CreateAssessmentRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String teacherId,
      String schoolId,
      String title,
      String subject,
      int grade,
      List<String> chapterIds,
      BlueprintRequest blueprint,
      String? templateId});

  @override
  $BlueprintRequestCopyWith<$Res> get blueprint;
}

/// @nodoc
class __$$CreateAssessmentRequestImplCopyWithImpl<$Res>
    extends _$CreateAssessmentRequestCopyWithImpl<$Res,
        _$CreateAssessmentRequestImpl>
    implements _$$CreateAssessmentRequestImplCopyWith<$Res> {
  __$$CreateAssessmentRequestImplCopyWithImpl(
      _$CreateAssessmentRequestImpl _value,
      $Res Function(_$CreateAssessmentRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? teacherId = null,
    Object? schoolId = null,
    Object? title = null,
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? blueprint = null,
    Object? templateId = freezed,
  }) {
    return _then(_$CreateAssessmentRequestImpl(
      teacherId: null == teacherId
          ? _value.teacherId
          : teacherId // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
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
              as BlueprintRequest,
      templateId: freezed == templateId
          ? _value.templateId
          : templateId // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CreateAssessmentRequestImpl implements _CreateAssessmentRequest {
  const _$CreateAssessmentRequestImpl(
      {required this.teacherId,
      required this.schoolId,
      required this.title,
      required this.subject,
      required this.grade,
      required final List<String> chapterIds,
      required this.blueprint,
      this.templateId})
      : _chapterIds = chapterIds;

  factory _$CreateAssessmentRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$CreateAssessmentRequestImplFromJson(json);

  @override
  final String teacherId;
  @override
  final String schoolId;
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
  final BlueprintRequest blueprint;
  @override
  final String? templateId;

  @override
  String toString() {
    return 'CreateAssessmentRequest(teacherId: $teacherId, schoolId: $schoolId, title: $title, subject: $subject, grade: $grade, chapterIds: $chapterIds, blueprint: $blueprint, templateId: $templateId)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CreateAssessmentRequestImpl &&
            (identical(other.teacherId, teacherId) ||
                other.teacherId == teacherId) &&
            (identical(other.schoolId, schoolId) ||
                other.schoolId == schoolId) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality()
                .equals(other._chapterIds, _chapterIds) &&
            (identical(other.blueprint, blueprint) ||
                other.blueprint == blueprint) &&
            (identical(other.templateId, templateId) ||
                other.templateId == templateId));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      teacherId,
      schoolId,
      title,
      subject,
      grade,
      const DeepCollectionEquality().hash(_chapterIds),
      blueprint,
      templateId);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CreateAssessmentRequestImplCopyWith<_$CreateAssessmentRequestImpl>
      get copyWith => __$$CreateAssessmentRequestImplCopyWithImpl<
          _$CreateAssessmentRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CreateAssessmentRequestImplToJson(
      this,
    );
  }
}

abstract class _CreateAssessmentRequest implements CreateAssessmentRequest {
  const factory _CreateAssessmentRequest(
      {required final String teacherId,
      required final String schoolId,
      required final String title,
      required final String subject,
      required final int grade,
      required final List<String> chapterIds,
      required final BlueprintRequest blueprint,
      final String? templateId}) = _$CreateAssessmentRequestImpl;

  factory _CreateAssessmentRequest.fromJson(Map<String, dynamic> json) =
      _$CreateAssessmentRequestImpl.fromJson;

  @override
  String get teacherId;
  @override
  String get schoolId;
  @override
  String get title;
  @override
  String get subject;
  @override
  int get grade;
  @override
  List<String> get chapterIds;
  @override
  BlueprintRequest get blueprint;
  @override
  String? get templateId;
  @override
  @JsonKey(ignore: true)
  _$$CreateAssessmentRequestImplCopyWith<_$CreateAssessmentRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

BlueprintRequest _$BlueprintRequestFromJson(Map<String, dynamic> json) {
  return _BlueprintRequest.fromJson(json);
}

/// @nodoc
mixin _$BlueprintRequest {
  int get totalMarks => throw _privateConstructorUsedError;
  int get durationMinutes => throw _privateConstructorUsedError;
  DifficultyDistribution get difficulty => throw _privateConstructorUsedError;
  BloomDistribution get bloom => throw _privateConstructorUsedError;
  ChapterWeights get chapterWeights => throw _privateConstructorUsedError;
  CompetencyWeights get competencyWeights => throw _privateConstructorUsedError;
  List<SectionBlueprint> get sections => throw _privateConstructorUsedError;
  Map<String, dynamic>? get schoolTemplate =>
      throw _privateConstructorUsedError;
  String? get tier => throw _privateConstructorUsedError;
  int? get competencyPercentage => throw _privateConstructorUsedError;
  String? get examType => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BlueprintRequestCopyWith<BlueprintRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BlueprintRequestCopyWith<$Res> {
  factory $BlueprintRequestCopyWith(
          BlueprintRequest value, $Res Function(BlueprintRequest) then) =
      _$BlueprintRequestCopyWithImpl<$Res, BlueprintRequest>;
  @useResult
  $Res call(
      {int totalMarks,
      int durationMinutes,
      DifficultyDistribution difficulty,
      BloomDistribution bloom,
      ChapterWeights chapterWeights,
      CompetencyWeights competencyWeights,
      List<SectionBlueprint> sections,
      Map<String, dynamic>? schoolTemplate,
      String? tier,
      int? competencyPercentage,
      String? examType});

  $DifficultyDistributionCopyWith<$Res> get difficulty;
  $BloomDistributionCopyWith<$Res> get bloom;
  $ChapterWeightsCopyWith<$Res> get chapterWeights;
  $CompetencyWeightsCopyWith<$Res> get competencyWeights;
}

/// @nodoc
class _$BlueprintRequestCopyWithImpl<$Res, $Val extends BlueprintRequest>
    implements $BlueprintRequestCopyWith<$Res> {
  _$BlueprintRequestCopyWithImpl(this._value, this._then);

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
    Object? schoolTemplate = freezed,
    Object? tier = freezed,
    Object? competencyPercentage = freezed,
    Object? examType = freezed,
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
      schoolTemplate: freezed == schoolTemplate
          ? _value.schoolTemplate
          : schoolTemplate // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
      competencyPercentage: freezed == competencyPercentage
          ? _value.competencyPercentage
          : competencyPercentage // ignore: cast_nullable_to_non_nullable
              as int?,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
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
abstract class _$$BlueprintRequestImplCopyWith<$Res>
    implements $BlueprintRequestCopyWith<$Res> {
  factory _$$BlueprintRequestImplCopyWith(_$BlueprintRequestImpl value,
          $Res Function(_$BlueprintRequestImpl) then) =
      __$$BlueprintRequestImplCopyWithImpl<$Res>;
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
      Map<String, dynamic>? schoolTemplate,
      String? tier,
      int? competencyPercentage,
      String? examType});

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
class __$$BlueprintRequestImplCopyWithImpl<$Res>
    extends _$BlueprintRequestCopyWithImpl<$Res, _$BlueprintRequestImpl>
    implements _$$BlueprintRequestImplCopyWith<$Res> {
  __$$BlueprintRequestImplCopyWithImpl(_$BlueprintRequestImpl _value,
      $Res Function(_$BlueprintRequestImpl) _then)
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
    Object? schoolTemplate = freezed,
    Object? tier = freezed,
    Object? competencyPercentage = freezed,
    Object? examType = freezed,
  }) {
    return _then(_$BlueprintRequestImpl(
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
      schoolTemplate: freezed == schoolTemplate
          ? _value._schoolTemplate
          : schoolTemplate // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
      competencyPercentage: freezed == competencyPercentage
          ? _value.competencyPercentage
          : competencyPercentage // ignore: cast_nullable_to_non_nullable
              as int?,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BlueprintRequestImpl implements _BlueprintRequest {
  const _$BlueprintRequestImpl(
      {required this.totalMarks,
      required this.durationMinutes,
      required this.difficulty,
      required this.bloom,
      required this.chapterWeights,
      required this.competencyWeights,
      required final List<SectionBlueprint> sections,
      final Map<String, dynamic>? schoolTemplate,
      this.tier,
      this.competencyPercentage,
      this.examType})
      : _sections = sections,
        _schoolTemplate = schoolTemplate;

  factory _$BlueprintRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$BlueprintRequestImplFromJson(json);

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

  final Map<String, dynamic>? _schoolTemplate;
  @override
  Map<String, dynamic>? get schoolTemplate {
    final value = _schoolTemplate;
    if (value == null) return null;
    if (_schoolTemplate is EqualUnmodifiableMapView) return _schoolTemplate;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  final String? tier;
  @override
  final int? competencyPercentage;
  @override
  final String? examType;

  @override
  String toString() {
    return 'BlueprintRequest(totalMarks: $totalMarks, durationMinutes: $durationMinutes, difficulty: $difficulty, bloom: $bloom, chapterWeights: $chapterWeights, competencyWeights: $competencyWeights, sections: $sections, schoolTemplate: $schoolTemplate, tier: $tier, competencyPercentage: $competencyPercentage, examType: $examType)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BlueprintRequestImpl &&
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
            const DeepCollectionEquality()
                .equals(other._schoolTemplate, _schoolTemplate) &&
            (identical(other.tier, tier) || other.tier == tier) &&
            (identical(other.competencyPercentage, competencyPercentage) ||
                other.competencyPercentage == competencyPercentage) &&
            (identical(other.examType, examType) ||
                other.examType == examType));
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
      const DeepCollectionEquality().hash(_schoolTemplate),
      tier,
      competencyPercentage,
      examType);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BlueprintRequestImplCopyWith<_$BlueprintRequestImpl> get copyWith =>
      __$$BlueprintRequestImplCopyWithImpl<_$BlueprintRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BlueprintRequestImplToJson(
      this,
    );
  }
}

abstract class _BlueprintRequest implements BlueprintRequest {
  const factory _BlueprintRequest(
      {required final int totalMarks,
      required final int durationMinutes,
      required final DifficultyDistribution difficulty,
      required final BloomDistribution bloom,
      required final ChapterWeights chapterWeights,
      required final CompetencyWeights competencyWeights,
      required final List<SectionBlueprint> sections,
      final Map<String, dynamic>? schoolTemplate,
      final String? tier,
      final int? competencyPercentage,
      final String? examType}) = _$BlueprintRequestImpl;

  factory _BlueprintRequest.fromJson(Map<String, dynamic> json) =
      _$BlueprintRequestImpl.fromJson;

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
  Map<String, dynamic>? get schoolTemplate;
  @override
  String? get tier;
  @override
  int? get competencyPercentage;
  @override
  String? get examType;
  @override
  @JsonKey(ignore: true)
  _$$BlueprintRequestImplCopyWith<_$BlueprintRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionSearchParams _$QuestionSearchParamsFromJson(Map<String, dynamic> json) {
  return _QuestionSearchParams.fromJson(json);
}

/// @nodoc
mixin _$QuestionSearchParams {
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  List<String>? get chapterIds => throw _privateConstructorUsedError;
  List<String>? get subtopicIds => throw _privateConstructorUsedError;
  List<String>? get competencyIds => throw _privateConstructorUsedError;
  List<BloomLevel>? get bloomLevels => throw _privateConstructorUsedError;
  List<Difficulty>? get difficulties => throw _privateConstructorUsedError;
  List<QuestionType>? get types => throw _privateConstructorUsedError;
  int? get minMarks => throw _privateConstructorUsedError;
  int? get maxMarks => throw _privateConstructorUsedError;
  int? get limit => throw _privateConstructorUsedError;
  int? get offset => throw _privateConstructorUsedError;
  String? get keyword => throw _privateConstructorUsedError;
  double? get minQualityScore => throw _privateConstructorUsedError;
  List<QuestionSource>? get sources => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionSearchParamsCopyWith<QuestionSearchParams> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionSearchParamsCopyWith<$Res> {
  factory $QuestionSearchParamsCopyWith(QuestionSearchParams value,
          $Res Function(QuestionSearchParams) then) =
      _$QuestionSearchParamsCopyWithImpl<$Res, QuestionSearchParams>;
  @useResult
  $Res call(
      {String subject,
      int grade,
      List<String>? chapterIds,
      List<String>? subtopicIds,
      List<String>? competencyIds,
      List<BloomLevel>? bloomLevels,
      List<Difficulty>? difficulties,
      List<QuestionType>? types,
      int? minMarks,
      int? maxMarks,
      int? limit,
      int? offset,
      String? keyword,
      double? minQualityScore,
      List<QuestionSource>? sources});
}

/// @nodoc
class _$QuestionSearchParamsCopyWithImpl<$Res,
        $Val extends QuestionSearchParams>
    implements $QuestionSearchParamsCopyWith<$Res> {
  _$QuestionSearchParamsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = freezed,
    Object? subtopicIds = freezed,
    Object? competencyIds = freezed,
    Object? bloomLevels = freezed,
    Object? difficulties = freezed,
    Object? types = freezed,
    Object? minMarks = freezed,
    Object? maxMarks = freezed,
    Object? limit = freezed,
    Object? offset = freezed,
    Object? keyword = freezed,
    Object? minQualityScore = freezed,
    Object? sources = freezed,
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
      chapterIds: freezed == chapterIds
          ? _value.chapterIds
          : chapterIds // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      subtopicIds: freezed == subtopicIds
          ? _value.subtopicIds
          : subtopicIds // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      competencyIds: freezed == competencyIds
          ? _value.competencyIds
          : competencyIds // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      bloomLevels: freezed == bloomLevels
          ? _value.bloomLevels
          : bloomLevels // ignore: cast_nullable_to_non_nullable
              as List<BloomLevel>?,
      difficulties: freezed == difficulties
          ? _value.difficulties
          : difficulties // ignore: cast_nullable_to_non_nullable
              as List<Difficulty>?,
      types: freezed == types
          ? _value.types
          : types // ignore: cast_nullable_to_non_nullable
              as List<QuestionType>?,
      minMarks: freezed == minMarks
          ? _value.minMarks
          : minMarks // ignore: cast_nullable_to_non_nullable
              as int?,
      maxMarks: freezed == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int?,
      limit: freezed == limit
          ? _value.limit
          : limit // ignore: cast_nullable_to_non_nullable
              as int?,
      offset: freezed == offset
          ? _value.offset
          : offset // ignore: cast_nullable_to_non_nullable
              as int?,
      keyword: freezed == keyword
          ? _value.keyword
          : keyword // ignore: cast_nullable_to_non_nullable
              as String?,
      minQualityScore: freezed == minQualityScore
          ? _value.minQualityScore
          : minQualityScore // ignore: cast_nullable_to_non_nullable
              as double?,
      sources: freezed == sources
          ? _value.sources
          : sources // ignore: cast_nullable_to_non_nullable
              as List<QuestionSource>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuestionSearchParamsImplCopyWith<$Res>
    implements $QuestionSearchParamsCopyWith<$Res> {
  factory _$$QuestionSearchParamsImplCopyWith(_$QuestionSearchParamsImpl value,
          $Res Function(_$QuestionSearchParamsImpl) then) =
      __$$QuestionSearchParamsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String subject,
      int grade,
      List<String>? chapterIds,
      List<String>? subtopicIds,
      List<String>? competencyIds,
      List<BloomLevel>? bloomLevels,
      List<Difficulty>? difficulties,
      List<QuestionType>? types,
      int? minMarks,
      int? maxMarks,
      int? limit,
      int? offset,
      String? keyword,
      double? minQualityScore,
      List<QuestionSource>? sources});
}

/// @nodoc
class __$$QuestionSearchParamsImplCopyWithImpl<$Res>
    extends _$QuestionSearchParamsCopyWithImpl<$Res, _$QuestionSearchParamsImpl>
    implements _$$QuestionSearchParamsImplCopyWith<$Res> {
  __$$QuestionSearchParamsImplCopyWithImpl(_$QuestionSearchParamsImpl _value,
      $Res Function(_$QuestionSearchParamsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = freezed,
    Object? subtopicIds = freezed,
    Object? competencyIds = freezed,
    Object? bloomLevels = freezed,
    Object? difficulties = freezed,
    Object? types = freezed,
    Object? minMarks = freezed,
    Object? maxMarks = freezed,
    Object? limit = freezed,
    Object? offset = freezed,
    Object? keyword = freezed,
    Object? minQualityScore = freezed,
    Object? sources = freezed,
  }) {
    return _then(_$QuestionSearchParamsImpl(
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      chapterIds: freezed == chapterIds
          ? _value._chapterIds
          : chapterIds // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      subtopicIds: freezed == subtopicIds
          ? _value._subtopicIds
          : subtopicIds // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      competencyIds: freezed == competencyIds
          ? _value._competencyIds
          : competencyIds // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      bloomLevels: freezed == bloomLevels
          ? _value._bloomLevels
          : bloomLevels // ignore: cast_nullable_to_non_nullable
              as List<BloomLevel>?,
      difficulties: freezed == difficulties
          ? _value._difficulties
          : difficulties // ignore: cast_nullable_to_non_nullable
              as List<Difficulty>?,
      types: freezed == types
          ? _value._types
          : types // ignore: cast_nullable_to_non_nullable
              as List<QuestionType>?,
      minMarks: freezed == minMarks
          ? _value.minMarks
          : minMarks // ignore: cast_nullable_to_non_nullable
              as int?,
      maxMarks: freezed == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int?,
      limit: freezed == limit
          ? _value.limit
          : limit // ignore: cast_nullable_to_non_nullable
              as int?,
      offset: freezed == offset
          ? _value.offset
          : offset // ignore: cast_nullable_to_non_nullable
              as int?,
      keyword: freezed == keyword
          ? _value.keyword
          : keyword // ignore: cast_nullable_to_non_nullable
              as String?,
      minQualityScore: freezed == minQualityScore
          ? _value.minQualityScore
          : minQualityScore // ignore: cast_nullable_to_non_nullable
              as double?,
      sources: freezed == sources
          ? _value._sources
          : sources // ignore: cast_nullable_to_non_nullable
              as List<QuestionSource>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionSearchParamsImpl implements _QuestionSearchParams {
  const _$QuestionSearchParamsImpl(
      {required this.subject,
      required this.grade,
      final List<String>? chapterIds,
      final List<String>? subtopicIds,
      final List<String>? competencyIds,
      final List<BloomLevel>? bloomLevels,
      final List<Difficulty>? difficulties,
      final List<QuestionType>? types,
      this.minMarks,
      this.maxMarks,
      this.limit,
      this.offset,
      this.keyword,
      this.minQualityScore,
      final List<QuestionSource>? sources})
      : _chapterIds = chapterIds,
        _subtopicIds = subtopicIds,
        _competencyIds = competencyIds,
        _bloomLevels = bloomLevels,
        _difficulties = difficulties,
        _types = types,
        _sources = sources;

  factory _$QuestionSearchParamsImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionSearchParamsImplFromJson(json);

  @override
  final String subject;
  @override
  final int grade;
  final List<String>? _chapterIds;
  @override
  List<String>? get chapterIds {
    final value = _chapterIds;
    if (value == null) return null;
    if (_chapterIds is EqualUnmodifiableListView) return _chapterIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<String>? _subtopicIds;
  @override
  List<String>? get subtopicIds {
    final value = _subtopicIds;
    if (value == null) return null;
    if (_subtopicIds is EqualUnmodifiableListView) return _subtopicIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<String>? _competencyIds;
  @override
  List<String>? get competencyIds {
    final value = _competencyIds;
    if (value == null) return null;
    if (_competencyIds is EqualUnmodifiableListView) return _competencyIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<BloomLevel>? _bloomLevels;
  @override
  List<BloomLevel>? get bloomLevels {
    final value = _bloomLevels;
    if (value == null) return null;
    if (_bloomLevels is EqualUnmodifiableListView) return _bloomLevels;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<Difficulty>? _difficulties;
  @override
  List<Difficulty>? get difficulties {
    final value = _difficulties;
    if (value == null) return null;
    if (_difficulties is EqualUnmodifiableListView) return _difficulties;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<QuestionType>? _types;
  @override
  List<QuestionType>? get types {
    final value = _types;
    if (value == null) return null;
    if (_types is EqualUnmodifiableListView) return _types;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  final int? minMarks;
  @override
  final int? maxMarks;
  @override
  final int? limit;
  @override
  final int? offset;
  @override
  final String? keyword;
  @override
  final double? minQualityScore;
  final List<QuestionSource>? _sources;
  @override
  List<QuestionSource>? get sources {
    final value = _sources;
    if (value == null) return null;
    if (_sources is EqualUnmodifiableListView) return _sources;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'QuestionSearchParams(subject: $subject, grade: $grade, chapterIds: $chapterIds, subtopicIds: $subtopicIds, competencyIds: $competencyIds, bloomLevels: $bloomLevels, difficulties: $difficulties, types: $types, minMarks: $minMarks, maxMarks: $maxMarks, limit: $limit, offset: $offset, keyword: $keyword, minQualityScore: $minQualityScore, sources: $sources)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionSearchParamsImpl &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality()
                .equals(other._chapterIds, _chapterIds) &&
            const DeepCollectionEquality()
                .equals(other._subtopicIds, _subtopicIds) &&
            const DeepCollectionEquality()
                .equals(other._competencyIds, _competencyIds) &&
            const DeepCollectionEquality()
                .equals(other._bloomLevels, _bloomLevels) &&
            const DeepCollectionEquality()
                .equals(other._difficulties, _difficulties) &&
            const DeepCollectionEquality().equals(other._types, _types) &&
            (identical(other.minMarks, minMarks) ||
                other.minMarks == minMarks) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.limit, limit) || other.limit == limit) &&
            (identical(other.offset, offset) || other.offset == offset) &&
            (identical(other.keyword, keyword) || other.keyword == keyword) &&
            (identical(other.minQualityScore, minQualityScore) ||
                other.minQualityScore == minQualityScore) &&
            const DeepCollectionEquality().equals(other._sources, _sources));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      subject,
      grade,
      const DeepCollectionEquality().hash(_chapterIds),
      const DeepCollectionEquality().hash(_subtopicIds),
      const DeepCollectionEquality().hash(_competencyIds),
      const DeepCollectionEquality().hash(_bloomLevels),
      const DeepCollectionEquality().hash(_difficulties),
      const DeepCollectionEquality().hash(_types),
      minMarks,
      maxMarks,
      limit,
      offset,
      keyword,
      minQualityScore,
      const DeepCollectionEquality().hash(_sources));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionSearchParamsImplCopyWith<_$QuestionSearchParamsImpl>
      get copyWith =>
          __$$QuestionSearchParamsImplCopyWithImpl<_$QuestionSearchParamsImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionSearchParamsImplToJson(
      this,
    );
  }
}

abstract class _QuestionSearchParams implements QuestionSearchParams {
  const factory _QuestionSearchParams(
      {required final String subject,
      required final int grade,
      final List<String>? chapterIds,
      final List<String>? subtopicIds,
      final List<String>? competencyIds,
      final List<BloomLevel>? bloomLevels,
      final List<Difficulty>? difficulties,
      final List<QuestionType>? types,
      final int? minMarks,
      final int? maxMarks,
      final int? limit,
      final int? offset,
      final String? keyword,
      final double? minQualityScore,
      final List<QuestionSource>? sources}) = _$QuestionSearchParamsImpl;

  factory _QuestionSearchParams.fromJson(Map<String, dynamic> json) =
      _$QuestionSearchParamsImpl.fromJson;

  @override
  String get subject;
  @override
  int get grade;
  @override
  List<String>? get chapterIds;
  @override
  List<String>? get subtopicIds;
  @override
  List<String>? get competencyIds;
  @override
  List<BloomLevel>? get bloomLevels;
  @override
  List<Difficulty>? get difficulties;
  @override
  List<QuestionType>? get types;
  @override
  int? get minMarks;
  @override
  int? get maxMarks;
  @override
  int? get limit;
  @override
  int? get offset;
  @override
  String? get keyword;
  @override
  double? get minQualityScore;
  @override
  List<QuestionSource>? get sources;
  @override
  @JsonKey(ignore: true)
  _$$QuestionSearchParamsImplCopyWith<_$QuestionSearchParamsImpl>
      get copyWith => throw _privateConstructorUsedError;
}

QuestionOptimizationResult _$QuestionOptimizationResultFromJson(
    Map<String, dynamic> json) {
  return _QuestionOptimizationResult.fromJson(json);
}

/// @nodoc
mixin _$QuestionOptimizationResult {
  List<Question> get selectedQuestions => throw _privateConstructorUsedError;
  List<Question> get rejectedQuestions => throw _privateConstructorUsedError;
  Map<String, dynamic> get optimizationMetrics =>
      throw _privateConstructorUsedError;
  List<String> get warnings => throw _privateConstructorUsedError;
  List<String> get gaps => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionOptimizationResultCopyWith<QuestionOptimizationResult>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionOptimizationResultCopyWith<$Res> {
  factory $QuestionOptimizationResultCopyWith(QuestionOptimizationResult value,
          $Res Function(QuestionOptimizationResult) then) =
      _$QuestionOptimizationResultCopyWithImpl<$Res,
          QuestionOptimizationResult>;
  @useResult
  $Res call(
      {List<Question> selectedQuestions,
      List<Question> rejectedQuestions,
      Map<String, dynamic> optimizationMetrics,
      List<String> warnings,
      List<String> gaps});
}

/// @nodoc
class _$QuestionOptimizationResultCopyWithImpl<$Res,
        $Val extends QuestionOptimizationResult>
    implements $QuestionOptimizationResultCopyWith<$Res> {
  _$QuestionOptimizationResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? selectedQuestions = null,
    Object? rejectedQuestions = null,
    Object? optimizationMetrics = null,
    Object? warnings = null,
    Object? gaps = null,
  }) {
    return _then(_value.copyWith(
      selectedQuestions: null == selectedQuestions
          ? _value.selectedQuestions
          : selectedQuestions // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      rejectedQuestions: null == rejectedQuestions
          ? _value.rejectedQuestions
          : rejectedQuestions // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      optimizationMetrics: null == optimizationMetrics
          ? _value.optimizationMetrics
          : optimizationMetrics // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      warnings: null == warnings
          ? _value.warnings
          : warnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
      gaps: null == gaps
          ? _value.gaps
          : gaps // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuestionOptimizationResultImplCopyWith<$Res>
    implements $QuestionOptimizationResultCopyWith<$Res> {
  factory _$$QuestionOptimizationResultImplCopyWith(
          _$QuestionOptimizationResultImpl value,
          $Res Function(_$QuestionOptimizationResultImpl) then) =
      __$$QuestionOptimizationResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<Question> selectedQuestions,
      List<Question> rejectedQuestions,
      Map<String, dynamic> optimizationMetrics,
      List<String> warnings,
      List<String> gaps});
}

/// @nodoc
class __$$QuestionOptimizationResultImplCopyWithImpl<$Res>
    extends _$QuestionOptimizationResultCopyWithImpl<$Res,
        _$QuestionOptimizationResultImpl>
    implements _$$QuestionOptimizationResultImplCopyWith<$Res> {
  __$$QuestionOptimizationResultImplCopyWithImpl(
      _$QuestionOptimizationResultImpl _value,
      $Res Function(_$QuestionOptimizationResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? selectedQuestions = null,
    Object? rejectedQuestions = null,
    Object? optimizationMetrics = null,
    Object? warnings = null,
    Object? gaps = null,
  }) {
    return _then(_$QuestionOptimizationResultImpl(
      selectedQuestions: null == selectedQuestions
          ? _value._selectedQuestions
          : selectedQuestions // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      rejectedQuestions: null == rejectedQuestions
          ? _value._rejectedQuestions
          : rejectedQuestions // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      optimizationMetrics: null == optimizationMetrics
          ? _value._optimizationMetrics
          : optimizationMetrics // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      warnings: null == warnings
          ? _value._warnings
          : warnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
      gaps: null == gaps
          ? _value._gaps
          : gaps // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionOptimizationResultImpl implements _QuestionOptimizationResult {
  const _$QuestionOptimizationResultImpl(
      {required final List<Question> selectedQuestions,
      required final List<Question> rejectedQuestions,
      required final Map<String, dynamic> optimizationMetrics,
      required final List<String> warnings,
      required final List<String> gaps})
      : _selectedQuestions = selectedQuestions,
        _rejectedQuestions = rejectedQuestions,
        _optimizationMetrics = optimizationMetrics,
        _warnings = warnings,
        _gaps = gaps;

  factory _$QuestionOptimizationResultImpl.fromJson(
          Map<String, dynamic> json) =>
      _$$QuestionOptimizationResultImplFromJson(json);

  final List<Question> _selectedQuestions;
  @override
  List<Question> get selectedQuestions {
    if (_selectedQuestions is EqualUnmodifiableListView)
      return _selectedQuestions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_selectedQuestions);
  }

  final List<Question> _rejectedQuestions;
  @override
  List<Question> get rejectedQuestions {
    if (_rejectedQuestions is EqualUnmodifiableListView)
      return _rejectedQuestions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_rejectedQuestions);
  }

  final Map<String, dynamic> _optimizationMetrics;
  @override
  Map<String, dynamic> get optimizationMetrics {
    if (_optimizationMetrics is EqualUnmodifiableMapView)
      return _optimizationMetrics;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_optimizationMetrics);
  }

  final List<String> _warnings;
  @override
  List<String> get warnings {
    if (_warnings is EqualUnmodifiableListView) return _warnings;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_warnings);
  }

  final List<String> _gaps;
  @override
  List<String> get gaps {
    if (_gaps is EqualUnmodifiableListView) return _gaps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_gaps);
  }

  @override
  String toString() {
    return 'QuestionOptimizationResult(selectedQuestions: $selectedQuestions, rejectedQuestions: $rejectedQuestions, optimizationMetrics: $optimizationMetrics, warnings: $warnings, gaps: $gaps)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionOptimizationResultImpl &&
            const DeepCollectionEquality()
                .equals(other._selectedQuestions, _selectedQuestions) &&
            const DeepCollectionEquality()
                .equals(other._rejectedQuestions, _rejectedQuestions) &&
            const DeepCollectionEquality()
                .equals(other._optimizationMetrics, _optimizationMetrics) &&
            const DeepCollectionEquality().equals(other._warnings, _warnings) &&
            const DeepCollectionEquality().equals(other._gaps, _gaps));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_selectedQuestions),
      const DeepCollectionEquality().hash(_rejectedQuestions),
      const DeepCollectionEquality().hash(_optimizationMetrics),
      const DeepCollectionEquality().hash(_warnings),
      const DeepCollectionEquality().hash(_gaps));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionOptimizationResultImplCopyWith<_$QuestionOptimizationResultImpl>
      get copyWith => __$$QuestionOptimizationResultImplCopyWithImpl<
          _$QuestionOptimizationResultImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionOptimizationResultImplToJson(
      this,
    );
  }
}

abstract class _QuestionOptimizationResult
    implements QuestionOptimizationResult {
  const factory _QuestionOptimizationResult(
      {required final List<Question> selectedQuestions,
      required final List<Question> rejectedQuestions,
      required final Map<String, dynamic> optimizationMetrics,
      required final List<String> warnings,
      required final List<String> gaps}) = _$QuestionOptimizationResultImpl;

  factory _QuestionOptimizationResult.fromJson(Map<String, dynamic> json) =
      _$QuestionOptimizationResultImpl.fromJson;

  @override
  List<Question> get selectedQuestions;
  @override
  List<Question> get rejectedQuestions;
  @override
  Map<String, dynamic> get optimizationMetrics;
  @override
  List<String> get warnings;
  @override
  List<String> get gaps;
  @override
  @JsonKey(ignore: true)
  _$$QuestionOptimizationResultImplCopyWith<_$QuestionOptimizationResultImpl>
      get copyWith => throw _privateConstructorUsedError;
}

PaperGenerationRequest _$PaperGenerationRequestFromJson(
    Map<String, dynamic> json) {
  return _PaperGenerationRequest.fromJson(json);
}

/// @nodoc
mixin _$PaperGenerationRequest {
  String get assessmentId => throw _privateConstructorUsedError;
  Blueprint get blueprint => throw _privateConstructorUsedError;
  List<Question> get selectedQuestions => throw _privateConstructorUsedError;
  SchoolTemplate get template => throw _privateConstructorUsedError;
  Map<String, dynamic>? get formattingOptions =>
      throw _privateConstructorUsedError;
  int get setCount => throw _privateConstructorUsedError;
  String? get tier => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PaperGenerationRequestCopyWith<PaperGenerationRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PaperGenerationRequestCopyWith<$Res> {
  factory $PaperGenerationRequestCopyWith(PaperGenerationRequest value,
          $Res Function(PaperGenerationRequest) then) =
      _$PaperGenerationRequestCopyWithImpl<$Res, PaperGenerationRequest>;
  @useResult
  $Res call(
      {String assessmentId,
      Blueprint blueprint,
      List<Question> selectedQuestions,
      SchoolTemplate template,
      Map<String, dynamic>? formattingOptions,
      int setCount,
      String? tier});

  $BlueprintCopyWith<$Res> get blueprint;
  $SchoolTemplateCopyWith<$Res> get template;
}

/// @nodoc
class _$PaperGenerationRequestCopyWithImpl<$Res,
        $Val extends PaperGenerationRequest>
    implements $PaperGenerationRequestCopyWith<$Res> {
  _$PaperGenerationRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? blueprint = null,
    Object? selectedQuestions = null,
    Object? template = null,
    Object? formattingOptions = freezed,
    Object? setCount = null,
    Object? tier = freezed,
  }) {
    return _then(_value.copyWith(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      blueprint: null == blueprint
          ? _value.blueprint
          : blueprint // ignore: cast_nullable_to_non_nullable
              as Blueprint,
      selectedQuestions: null == selectedQuestions
          ? _value.selectedQuestions
          : selectedQuestions // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      template: null == template
          ? _value.template
          : template // ignore: cast_nullable_to_non_nullable
              as SchoolTemplate,
      formattingOptions: freezed == formattingOptions
          ? _value.formattingOptions
          : formattingOptions // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      setCount: null == setCount
          ? _value.setCount
          : setCount // ignore: cast_nullable_to_non_nullable
              as int,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $BlueprintCopyWith<$Res> get blueprint {
    return $BlueprintCopyWith<$Res>(_value.blueprint, (value) {
      return _then(_value.copyWith(blueprint: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $SchoolTemplateCopyWith<$Res> get template {
    return $SchoolTemplateCopyWith<$Res>(_value.template, (value) {
      return _then(_value.copyWith(template: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PaperGenerationRequestImplCopyWith<$Res>
    implements $PaperGenerationRequestCopyWith<$Res> {
  factory _$$PaperGenerationRequestImplCopyWith(
          _$PaperGenerationRequestImpl value,
          $Res Function(_$PaperGenerationRequestImpl) then) =
      __$$PaperGenerationRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String assessmentId,
      Blueprint blueprint,
      List<Question> selectedQuestions,
      SchoolTemplate template,
      Map<String, dynamic>? formattingOptions,
      int setCount,
      String? tier});

  @override
  $BlueprintCopyWith<$Res> get blueprint;
  @override
  $SchoolTemplateCopyWith<$Res> get template;
}

/// @nodoc
class __$$PaperGenerationRequestImplCopyWithImpl<$Res>
    extends _$PaperGenerationRequestCopyWithImpl<$Res,
        _$PaperGenerationRequestImpl>
    implements _$$PaperGenerationRequestImplCopyWith<$Res> {
  __$$PaperGenerationRequestImplCopyWithImpl(
      _$PaperGenerationRequestImpl _value,
      $Res Function(_$PaperGenerationRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? blueprint = null,
    Object? selectedQuestions = null,
    Object? template = null,
    Object? formattingOptions = freezed,
    Object? setCount = null,
    Object? tier = freezed,
  }) {
    return _then(_$PaperGenerationRequestImpl(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      blueprint: null == blueprint
          ? _value.blueprint
          : blueprint // ignore: cast_nullable_to_non_nullable
              as Blueprint,
      selectedQuestions: null == selectedQuestions
          ? _value._selectedQuestions
          : selectedQuestions // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      template: null == template
          ? _value.template
          : template // ignore: cast_nullable_to_non_nullable
              as SchoolTemplate,
      formattingOptions: freezed == formattingOptions
          ? _value._formattingOptions
          : formattingOptions // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      setCount: null == setCount
          ? _value.setCount
          : setCount // ignore: cast_nullable_to_non_nullable
              as int,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PaperGenerationRequestImpl implements _PaperGenerationRequest {
  const _$PaperGenerationRequestImpl(
      {required this.assessmentId,
      required this.blueprint,
      required final List<Question> selectedQuestions,
      required this.template,
      final Map<String, dynamic>? formattingOptions,
      this.setCount = 1,
      this.tier})
      : _selectedQuestions = selectedQuestions,
        _formattingOptions = formattingOptions;

  factory _$PaperGenerationRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$PaperGenerationRequestImplFromJson(json);

  @override
  final String assessmentId;
  @override
  final Blueprint blueprint;
  final List<Question> _selectedQuestions;
  @override
  List<Question> get selectedQuestions {
    if (_selectedQuestions is EqualUnmodifiableListView)
      return _selectedQuestions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_selectedQuestions);
  }

  @override
  final SchoolTemplate template;
  final Map<String, dynamic>? _formattingOptions;
  @override
  Map<String, dynamic>? get formattingOptions {
    final value = _formattingOptions;
    if (value == null) return null;
    if (_formattingOptions is EqualUnmodifiableMapView)
      return _formattingOptions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  @JsonKey()
  final int setCount;
  @override
  final String? tier;

  @override
  String toString() {
    return 'PaperGenerationRequest(assessmentId: $assessmentId, blueprint: $blueprint, selectedQuestions: $selectedQuestions, template: $template, formattingOptions: $formattingOptions, setCount: $setCount, tier: $tier)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PaperGenerationRequestImpl &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.blueprint, blueprint) ||
                other.blueprint == blueprint) &&
            const DeepCollectionEquality()
                .equals(other._selectedQuestions, _selectedQuestions) &&
            (identical(other.template, template) ||
                other.template == template) &&
            const DeepCollectionEquality()
                .equals(other._formattingOptions, _formattingOptions) &&
            (identical(other.setCount, setCount) ||
                other.setCount == setCount) &&
            (identical(other.tier, tier) || other.tier == tier));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      assessmentId,
      blueprint,
      const DeepCollectionEquality().hash(_selectedQuestions),
      template,
      const DeepCollectionEquality().hash(_formattingOptions),
      setCount,
      tier);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PaperGenerationRequestImplCopyWith<_$PaperGenerationRequestImpl>
      get copyWith => __$$PaperGenerationRequestImplCopyWithImpl<
          _$PaperGenerationRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PaperGenerationRequestImplToJson(
      this,
    );
  }
}

abstract class _PaperGenerationRequest implements PaperGenerationRequest {
  const factory _PaperGenerationRequest(
      {required final String assessmentId,
      required final Blueprint blueprint,
      required final List<Question> selectedQuestions,
      required final SchoolTemplate template,
      final Map<String, dynamic>? formattingOptions,
      final int setCount,
      final String? tier}) = _$PaperGenerationRequestImpl;

  factory _PaperGenerationRequest.fromJson(Map<String, dynamic> json) =
      _$PaperGenerationRequestImpl.fromJson;

  @override
  String get assessmentId;
  @override
  Blueprint get blueprint;
  @override
  List<Question> get selectedQuestions;
  @override
  SchoolTemplate get template;
  @override
  Map<String, dynamic>? get formattingOptions;
  @override
  int get setCount;
  @override
  String? get tier;
  @override
  @JsonKey(ignore: true)
  _$$PaperGenerationRequestImplCopyWith<_$PaperGenerationRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

GeneratedPaper _$GeneratedPaperFromJson(Map<String, dynamic> json) {
  return _GeneratedPaper.fromJson(json);
}

/// @nodoc
mixin _$GeneratedPaper {
  String get id => throw _privateConstructorUsedError;
  String get assessmentId => throw _privateConstructorUsedError;
  List<GeneratedSection> get sections => throw _privateConstructorUsedError;
  String get formattedContent => throw _privateConstructorUsedError;
  String get formattedContentLatex => throw _privateConstructorUsedError;
  Map<String, dynamic> get answerKey => throw _privateConstructorUsedError;
  PaperMetadata get metadata => throw _privateConstructorUsedError;
  String? get setLabel => throw _privateConstructorUsedError;
  List<GeneratedPaper> get sets => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $GeneratedPaperCopyWith<GeneratedPaper> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $GeneratedPaperCopyWith<$Res> {
  factory $GeneratedPaperCopyWith(
          GeneratedPaper value, $Res Function(GeneratedPaper) then) =
      _$GeneratedPaperCopyWithImpl<$Res, GeneratedPaper>;
  @useResult
  $Res call(
      {String id,
      String assessmentId,
      List<GeneratedSection> sections,
      String formattedContent,
      String formattedContentLatex,
      Map<String, dynamic> answerKey,
      PaperMetadata metadata,
      String? setLabel,
      List<GeneratedPaper> sets});

  $PaperMetadataCopyWith<$Res> get metadata;
}

/// @nodoc
class _$GeneratedPaperCopyWithImpl<$Res, $Val extends GeneratedPaper>
    implements $GeneratedPaperCopyWith<$Res> {
  _$GeneratedPaperCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? assessmentId = null,
    Object? sections = null,
    Object? formattedContent = null,
    Object? formattedContentLatex = null,
    Object? answerKey = null,
    Object? metadata = null,
    Object? setLabel = freezed,
    Object? sets = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      sections: null == sections
          ? _value.sections
          : sections // ignore: cast_nullable_to_non_nullable
              as List<GeneratedSection>,
      formattedContent: null == formattedContent
          ? _value.formattedContent
          : formattedContent // ignore: cast_nullable_to_non_nullable
              as String,
      formattedContentLatex: null == formattedContentLatex
          ? _value.formattedContentLatex
          : formattedContentLatex // ignore: cast_nullable_to_non_nullable
              as String,
      answerKey: null == answerKey
          ? _value.answerKey
          : answerKey // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as PaperMetadata,
      setLabel: freezed == setLabel
          ? _value.setLabel
          : setLabel // ignore: cast_nullable_to_non_nullable
              as String?,
      sets: null == sets
          ? _value.sets
          : sets // ignore: cast_nullable_to_non_nullable
              as List<GeneratedPaper>,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $PaperMetadataCopyWith<$Res> get metadata {
    return $PaperMetadataCopyWith<$Res>(_value.metadata, (value) {
      return _then(_value.copyWith(metadata: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$GeneratedPaperImplCopyWith<$Res>
    implements $GeneratedPaperCopyWith<$Res> {
  factory _$$GeneratedPaperImplCopyWith(_$GeneratedPaperImpl value,
          $Res Function(_$GeneratedPaperImpl) then) =
      __$$GeneratedPaperImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String assessmentId,
      List<GeneratedSection> sections,
      String formattedContent,
      String formattedContentLatex,
      Map<String, dynamic> answerKey,
      PaperMetadata metadata,
      String? setLabel,
      List<GeneratedPaper> sets});

  @override
  $PaperMetadataCopyWith<$Res> get metadata;
}

/// @nodoc
class __$$GeneratedPaperImplCopyWithImpl<$Res>
    extends _$GeneratedPaperCopyWithImpl<$Res, _$GeneratedPaperImpl>
    implements _$$GeneratedPaperImplCopyWith<$Res> {
  __$$GeneratedPaperImplCopyWithImpl(
      _$GeneratedPaperImpl _value, $Res Function(_$GeneratedPaperImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? assessmentId = null,
    Object? sections = null,
    Object? formattedContent = null,
    Object? formattedContentLatex = null,
    Object? answerKey = null,
    Object? metadata = null,
    Object? setLabel = freezed,
    Object? sets = null,
  }) {
    return _then(_$GeneratedPaperImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      sections: null == sections
          ? _value._sections
          : sections // ignore: cast_nullable_to_non_nullable
              as List<GeneratedSection>,
      formattedContent: null == formattedContent
          ? _value.formattedContent
          : formattedContent // ignore: cast_nullable_to_non_nullable
              as String,
      formattedContentLatex: null == formattedContentLatex
          ? _value.formattedContentLatex
          : formattedContentLatex // ignore: cast_nullable_to_non_nullable
              as String,
      answerKey: null == answerKey
          ? _value._answerKey
          : answerKey // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as PaperMetadata,
      setLabel: freezed == setLabel
          ? _value.setLabel
          : setLabel // ignore: cast_nullable_to_non_nullable
              as String?,
      sets: null == sets
          ? _value._sets
          : sets // ignore: cast_nullable_to_non_nullable
              as List<GeneratedPaper>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$GeneratedPaperImpl implements _GeneratedPaper {
  const _$GeneratedPaperImpl(
      {required this.id,
      required this.assessmentId,
      required final List<GeneratedSection> sections,
      required this.formattedContent,
      required this.formattedContentLatex,
      required final Map<String, dynamic> answerKey,
      required this.metadata,
      this.setLabel,
      final List<GeneratedPaper> sets = const []})
      : _sections = sections,
        _answerKey = answerKey,
        _sets = sets;

  factory _$GeneratedPaperImpl.fromJson(Map<String, dynamic> json) =>
      _$$GeneratedPaperImplFromJson(json);

  @override
  final String id;
  @override
  final String assessmentId;
  final List<GeneratedSection> _sections;
  @override
  List<GeneratedSection> get sections {
    if (_sections is EqualUnmodifiableListView) return _sections;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_sections);
  }

  @override
  final String formattedContent;
  @override
  final String formattedContentLatex;
  final Map<String, dynamic> _answerKey;
  @override
  Map<String, dynamic> get answerKey {
    if (_answerKey is EqualUnmodifiableMapView) return _answerKey;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_answerKey);
  }

  @override
  final PaperMetadata metadata;
  @override
  final String? setLabel;
  final List<GeneratedPaper> _sets;
  @override
  @JsonKey()
  List<GeneratedPaper> get sets {
    if (_sets is EqualUnmodifiableListView) return _sets;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_sets);
  }

  @override
  String toString() {
    return 'GeneratedPaper(id: $id, assessmentId: $assessmentId, sections: $sections, formattedContent: $formattedContent, formattedContentLatex: $formattedContentLatex, answerKey: $answerKey, metadata: $metadata, setLabel: $setLabel, sets: $sets)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$GeneratedPaperImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            const DeepCollectionEquality().equals(other._sections, _sections) &&
            (identical(other.formattedContent, formattedContent) ||
                other.formattedContent == formattedContent) &&
            (identical(other.formattedContentLatex, formattedContentLatex) ||
                other.formattedContentLatex == formattedContentLatex) &&
            const DeepCollectionEquality()
                .equals(other._answerKey, _answerKey) &&
            (identical(other.metadata, metadata) ||
                other.metadata == metadata) &&
            (identical(other.setLabel, setLabel) ||
                other.setLabel == setLabel) &&
            const DeepCollectionEquality().equals(other._sets, _sets));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      assessmentId,
      const DeepCollectionEquality().hash(_sections),
      formattedContent,
      formattedContentLatex,
      const DeepCollectionEquality().hash(_answerKey),
      metadata,
      setLabel,
      const DeepCollectionEquality().hash(_sets));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$GeneratedPaperImplCopyWith<_$GeneratedPaperImpl> get copyWith =>
      __$$GeneratedPaperImplCopyWithImpl<_$GeneratedPaperImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$GeneratedPaperImplToJson(
      this,
    );
  }
}

abstract class _GeneratedPaper implements GeneratedPaper {
  const factory _GeneratedPaper(
      {required final String id,
      required final String assessmentId,
      required final List<GeneratedSection> sections,
      required final String formattedContent,
      required final String formattedContentLatex,
      required final Map<String, dynamic> answerKey,
      required final PaperMetadata metadata,
      final String? setLabel,
      final List<GeneratedPaper> sets}) = _$GeneratedPaperImpl;

  factory _GeneratedPaper.fromJson(Map<String, dynamic> json) =
      _$GeneratedPaperImpl.fromJson;

  @override
  String get id;
  @override
  String get assessmentId;
  @override
  List<GeneratedSection> get sections;
  @override
  String get formattedContent;
  @override
  String get formattedContentLatex;
  @override
  Map<String, dynamic> get answerKey;
  @override
  PaperMetadata get metadata;
  @override
  String? get setLabel;
  @override
  List<GeneratedPaper> get sets;
  @override
  @JsonKey(ignore: true)
  _$$GeneratedPaperImplCopyWith<_$GeneratedPaperImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

GeneratedSection _$GeneratedSectionFromJson(Map<String, dynamic> json) {
  return _GeneratedSection.fromJson(json);
}

/// @nodoc
mixin _$GeneratedSection {
  String get sectionId => throw _privateConstructorUsedError;
  String get label => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  List<GeneratedQuestion> get questions => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $GeneratedSectionCopyWith<GeneratedSection> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $GeneratedSectionCopyWith<$Res> {
  factory $GeneratedSectionCopyWith(
          GeneratedSection value, $Res Function(GeneratedSection) then) =
      _$GeneratedSectionCopyWithImpl<$Res, GeneratedSection>;
  @useResult
  $Res call(
      {String sectionId,
      String label,
      String name,
      List<GeneratedQuestion> questions,
      int totalMarks});
}

/// @nodoc
class _$GeneratedSectionCopyWithImpl<$Res, $Val extends GeneratedSection>
    implements $GeneratedSectionCopyWith<$Res> {
  _$GeneratedSectionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sectionId = null,
    Object? label = null,
    Object? name = null,
    Object? questions = null,
    Object? totalMarks = null,
  }) {
    return _then(_value.copyWith(
      sectionId: null == sectionId
          ? _value.sectionId
          : sectionId // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      questions: null == questions
          ? _value.questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<GeneratedQuestion>,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$GeneratedSectionImplCopyWith<$Res>
    implements $GeneratedSectionCopyWith<$Res> {
  factory _$$GeneratedSectionImplCopyWith(_$GeneratedSectionImpl value,
          $Res Function(_$GeneratedSectionImpl) then) =
      __$$GeneratedSectionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String sectionId,
      String label,
      String name,
      List<GeneratedQuestion> questions,
      int totalMarks});
}

/// @nodoc
class __$$GeneratedSectionImplCopyWithImpl<$Res>
    extends _$GeneratedSectionCopyWithImpl<$Res, _$GeneratedSectionImpl>
    implements _$$GeneratedSectionImplCopyWith<$Res> {
  __$$GeneratedSectionImplCopyWithImpl(_$GeneratedSectionImpl _value,
      $Res Function(_$GeneratedSectionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sectionId = null,
    Object? label = null,
    Object? name = null,
    Object? questions = null,
    Object? totalMarks = null,
  }) {
    return _then(_$GeneratedSectionImpl(
      sectionId: null == sectionId
          ? _value.sectionId
          : sectionId // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      questions: null == questions
          ? _value._questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<GeneratedQuestion>,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$GeneratedSectionImpl implements _GeneratedSection {
  const _$GeneratedSectionImpl(
      {required this.sectionId,
      required this.label,
      required this.name,
      required final List<GeneratedQuestion> questions,
      required this.totalMarks})
      : _questions = questions;

  factory _$GeneratedSectionImpl.fromJson(Map<String, dynamic> json) =>
      _$$GeneratedSectionImplFromJson(json);

  @override
  final String sectionId;
  @override
  final String label;
  @override
  final String name;
  final List<GeneratedQuestion> _questions;
  @override
  List<GeneratedQuestion> get questions {
    if (_questions is EqualUnmodifiableListView) return _questions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questions);
  }

  @override
  final int totalMarks;

  @override
  String toString() {
    return 'GeneratedSection(sectionId: $sectionId, label: $label, name: $name, questions: $questions, totalMarks: $totalMarks)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$GeneratedSectionImpl &&
            (identical(other.sectionId, sectionId) ||
                other.sectionId == sectionId) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.name, name) || other.name == name) &&
            const DeepCollectionEquality()
                .equals(other._questions, _questions) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, sectionId, label, name,
      const DeepCollectionEquality().hash(_questions), totalMarks);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$GeneratedSectionImplCopyWith<_$GeneratedSectionImpl> get copyWith =>
      __$$GeneratedSectionImplCopyWithImpl<_$GeneratedSectionImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$GeneratedSectionImplToJson(
      this,
    );
  }
}

abstract class _GeneratedSection implements GeneratedSection {
  const factory _GeneratedSection(
      {required final String sectionId,
      required final String label,
      required final String name,
      required final List<GeneratedQuestion> questions,
      required final int totalMarks}) = _$GeneratedSectionImpl;

  factory _GeneratedSection.fromJson(Map<String, dynamic> json) =
      _$GeneratedSectionImpl.fromJson;

  @override
  String get sectionId;
  @override
  String get label;
  @override
  String get name;
  @override
  List<GeneratedQuestion> get questions;
  @override
  int get totalMarks;
  @override
  @JsonKey(ignore: true)
  _$$GeneratedSectionImplCopyWith<_$GeneratedSectionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

GeneratedQuestion _$GeneratedQuestionFromJson(Map<String, dynamic> json) {
  return _GeneratedQuestion.fromJson(json);
}

/// @nodoc
mixin _$GeneratedQuestion {
  String get questionId => throw _privateConstructorUsedError;
  int get displayNumber => throw _privateConstructorUsedError;
  String get stem => throw _privateConstructorUsedError;
  String get stemLatex => throw _privateConstructorUsedError;
  List<QuestionPart> get parts => throw _privateConstructorUsedError;
  int get marks => throw _privateConstructorUsedError;
  String get bloomLevel => throw _privateConstructorUsedError;
  String get difficulty => throw _privateConstructorUsedError;
  String get type => throw _privateConstructorUsedError;
  String? get internalChoiceText => throw _privateConstructorUsedError;
  String? get internalChoiceQuestionId => throw _privateConstructorUsedError;
  bool get isCompetency => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $GeneratedQuestionCopyWith<GeneratedQuestion> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $GeneratedQuestionCopyWith<$Res> {
  factory $GeneratedQuestionCopyWith(
          GeneratedQuestion value, $Res Function(GeneratedQuestion) then) =
      _$GeneratedQuestionCopyWithImpl<$Res, GeneratedQuestion>;
  @useResult
  $Res call(
      {String questionId,
      int displayNumber,
      String stem,
      String stemLatex,
      List<QuestionPart> parts,
      int marks,
      String bloomLevel,
      String difficulty,
      String type,
      String? internalChoiceText,
      String? internalChoiceQuestionId,
      bool isCompetency});
}

/// @nodoc
class _$GeneratedQuestionCopyWithImpl<$Res, $Val extends GeneratedQuestion>
    implements $GeneratedQuestionCopyWith<$Res> {
  _$GeneratedQuestionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? displayNumber = null,
    Object? stem = null,
    Object? stemLatex = null,
    Object? parts = null,
    Object? marks = null,
    Object? bloomLevel = null,
    Object? difficulty = null,
    Object? type = null,
    Object? internalChoiceText = freezed,
    Object? internalChoiceQuestionId = freezed,
    Object? isCompetency = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      displayNumber: null == displayNumber
          ? _value.displayNumber
          : displayNumber // ignore: cast_nullable_to_non_nullable
              as int,
      stem: null == stem
          ? _value.stem
          : stem // ignore: cast_nullable_to_non_nullable
              as String,
      stemLatex: null == stemLatex
          ? _value.stemLatex
          : stemLatex // ignore: cast_nullable_to_non_nullable
              as String,
      parts: null == parts
          ? _value.parts
          : parts // ignore: cast_nullable_to_non_nullable
              as List<QuestionPart>,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      bloomLevel: null == bloomLevel
          ? _value.bloomLevel
          : bloomLevel // ignore: cast_nullable_to_non_nullable
              as String,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      internalChoiceText: freezed == internalChoiceText
          ? _value.internalChoiceText
          : internalChoiceText // ignore: cast_nullable_to_non_nullable
              as String?,
      internalChoiceQuestionId: freezed == internalChoiceQuestionId
          ? _value.internalChoiceQuestionId
          : internalChoiceQuestionId // ignore: cast_nullable_to_non_nullable
              as String?,
      isCompetency: null == isCompetency
          ? _value.isCompetency
          : isCompetency // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$GeneratedQuestionImplCopyWith<$Res>
    implements $GeneratedQuestionCopyWith<$Res> {
  factory _$$GeneratedQuestionImplCopyWith(_$GeneratedQuestionImpl value,
          $Res Function(_$GeneratedQuestionImpl) then) =
      __$$GeneratedQuestionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      int displayNumber,
      String stem,
      String stemLatex,
      List<QuestionPart> parts,
      int marks,
      String bloomLevel,
      String difficulty,
      String type,
      String? internalChoiceText,
      String? internalChoiceQuestionId,
      bool isCompetency});
}

/// @nodoc
class __$$GeneratedQuestionImplCopyWithImpl<$Res>
    extends _$GeneratedQuestionCopyWithImpl<$Res, _$GeneratedQuestionImpl>
    implements _$$GeneratedQuestionImplCopyWith<$Res> {
  __$$GeneratedQuestionImplCopyWithImpl(_$GeneratedQuestionImpl _value,
      $Res Function(_$GeneratedQuestionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? displayNumber = null,
    Object? stem = null,
    Object? stemLatex = null,
    Object? parts = null,
    Object? marks = null,
    Object? bloomLevel = null,
    Object? difficulty = null,
    Object? type = null,
    Object? internalChoiceText = freezed,
    Object? internalChoiceQuestionId = freezed,
    Object? isCompetency = null,
  }) {
    return _then(_$GeneratedQuestionImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      displayNumber: null == displayNumber
          ? _value.displayNumber
          : displayNumber // ignore: cast_nullable_to_non_nullable
              as int,
      stem: null == stem
          ? _value.stem
          : stem // ignore: cast_nullable_to_non_nullable
              as String,
      stemLatex: null == stemLatex
          ? _value.stemLatex
          : stemLatex // ignore: cast_nullable_to_non_nullable
              as String,
      parts: null == parts
          ? _value._parts
          : parts // ignore: cast_nullable_to_non_nullable
              as List<QuestionPart>,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      bloomLevel: null == bloomLevel
          ? _value.bloomLevel
          : bloomLevel // ignore: cast_nullable_to_non_nullable
              as String,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      internalChoiceText: freezed == internalChoiceText
          ? _value.internalChoiceText
          : internalChoiceText // ignore: cast_nullable_to_non_nullable
              as String?,
      internalChoiceQuestionId: freezed == internalChoiceQuestionId
          ? _value.internalChoiceQuestionId
          : internalChoiceQuestionId // ignore: cast_nullable_to_non_nullable
              as String?,
      isCompetency: null == isCompetency
          ? _value.isCompetency
          : isCompetency // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$GeneratedQuestionImpl implements _GeneratedQuestion {
  const _$GeneratedQuestionImpl(
      {required this.questionId,
      required this.displayNumber,
      required this.stem,
      required this.stemLatex,
      required final List<QuestionPart> parts,
      required this.marks,
      required this.bloomLevel,
      required this.difficulty,
      required this.type,
      this.internalChoiceText,
      this.internalChoiceQuestionId,
      this.isCompetency = false})
      : _parts = parts;

  factory _$GeneratedQuestionImpl.fromJson(Map<String, dynamic> json) =>
      _$$GeneratedQuestionImplFromJson(json);

  @override
  final String questionId;
  @override
  final int displayNumber;
  @override
  final String stem;
  @override
  final String stemLatex;
  final List<QuestionPart> _parts;
  @override
  List<QuestionPart> get parts {
    if (_parts is EqualUnmodifiableListView) return _parts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_parts);
  }

  @override
  final int marks;
  @override
  final String bloomLevel;
  @override
  final String difficulty;
  @override
  final String type;
  @override
  final String? internalChoiceText;
  @override
  final String? internalChoiceQuestionId;
  @override
  @JsonKey()
  final bool isCompetency;

  @override
  String toString() {
    return 'GeneratedQuestion(questionId: $questionId, displayNumber: $displayNumber, stem: $stem, stemLatex: $stemLatex, parts: $parts, marks: $marks, bloomLevel: $bloomLevel, difficulty: $difficulty, type: $type, internalChoiceText: $internalChoiceText, internalChoiceQuestionId: $internalChoiceQuestionId, isCompetency: $isCompetency)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$GeneratedQuestionImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.displayNumber, displayNumber) ||
                other.displayNumber == displayNumber) &&
            (identical(other.stem, stem) || other.stem == stem) &&
            (identical(other.stemLatex, stemLatex) ||
                other.stemLatex == stemLatex) &&
            const DeepCollectionEquality().equals(other._parts, _parts) &&
            (identical(other.marks, marks) || other.marks == marks) &&
            (identical(other.bloomLevel, bloomLevel) ||
                other.bloomLevel == bloomLevel) &&
            (identical(other.difficulty, difficulty) ||
                other.difficulty == difficulty) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.internalChoiceText, internalChoiceText) ||
                other.internalChoiceText == internalChoiceText) &&
            (identical(
                    other.internalChoiceQuestionId, internalChoiceQuestionId) ||
                other.internalChoiceQuestionId == internalChoiceQuestionId) &&
            (identical(other.isCompetency, isCompetency) ||
                other.isCompetency == isCompetency));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      displayNumber,
      stem,
      stemLatex,
      const DeepCollectionEquality().hash(_parts),
      marks,
      bloomLevel,
      difficulty,
      type,
      internalChoiceText,
      internalChoiceQuestionId,
      isCompetency);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$GeneratedQuestionImplCopyWith<_$GeneratedQuestionImpl> get copyWith =>
      __$$GeneratedQuestionImplCopyWithImpl<_$GeneratedQuestionImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$GeneratedQuestionImplToJson(
      this,
    );
  }
}

abstract class _GeneratedQuestion implements GeneratedQuestion {
  const factory _GeneratedQuestion(
      {required final String questionId,
      required final int displayNumber,
      required final String stem,
      required final String stemLatex,
      required final List<QuestionPart> parts,
      required final int marks,
      required final String bloomLevel,
      required final String difficulty,
      required final String type,
      final String? internalChoiceText,
      final String? internalChoiceQuestionId,
      final bool isCompetency}) = _$GeneratedQuestionImpl;

  factory _GeneratedQuestion.fromJson(Map<String, dynamic> json) =
      _$GeneratedQuestionImpl.fromJson;

  @override
  String get questionId;
  @override
  int get displayNumber;
  @override
  String get stem;
  @override
  String get stemLatex;
  @override
  List<QuestionPart> get parts;
  @override
  int get marks;
  @override
  String get bloomLevel;
  @override
  String get difficulty;
  @override
  String get type;
  @override
  String? get internalChoiceText;
  @override
  String? get internalChoiceQuestionId;
  @override
  bool get isCompetency;
  @override
  @JsonKey(ignore: true)
  _$$GeneratedQuestionImplCopyWith<_$GeneratedQuestionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PaperMetadata _$PaperMetadataFromJson(Map<String, dynamic> json) {
  return _PaperMetadata.fromJson(json);
}

/// @nodoc
mixin _$PaperMetadata {
  String get assessmentTitle => throw _privateConstructorUsedError;
  String get schoolName => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;
  int get durationMinutes => throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;
  String get generatedBy => throw _privateConstructorUsedError;
  String get version => throw _privateConstructorUsedError;
  String? get setLabel => throw _privateConstructorUsedError;
  String? get tier => throw _privateConstructorUsedError;
  String? get examType => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PaperMetadataCopyWith<PaperMetadata> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PaperMetadataCopyWith<$Res> {
  factory $PaperMetadataCopyWith(
          PaperMetadata value, $Res Function(PaperMetadata) then) =
      _$PaperMetadataCopyWithImpl<$Res, PaperMetadata>;
  @useResult
  $Res call(
      {String assessmentTitle,
      String schoolName,
      String subject,
      int grade,
      int totalMarks,
      int durationMinutes,
      DateTime generatedAt,
      String generatedBy,
      String version,
      String? setLabel,
      String? tier,
      String? examType});
}

/// @nodoc
class _$PaperMetadataCopyWithImpl<$Res, $Val extends PaperMetadata>
    implements $PaperMetadataCopyWith<$Res> {
  _$PaperMetadataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentTitle = null,
    Object? schoolName = null,
    Object? subject = null,
    Object? grade = null,
    Object? totalMarks = null,
    Object? durationMinutes = null,
    Object? generatedAt = null,
    Object? generatedBy = null,
    Object? version = null,
    Object? setLabel = freezed,
    Object? tier = freezed,
    Object? examType = freezed,
  }) {
    return _then(_value.copyWith(
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      schoolName: null == schoolName
          ? _value.schoolName
          : schoolName // ignore: cast_nullable_to_non_nullable
              as String,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      generatedBy: null == generatedBy
          ? _value.generatedBy
          : generatedBy // ignore: cast_nullable_to_non_nullable
              as String,
      version: null == version
          ? _value.version
          : version // ignore: cast_nullable_to_non_nullable
              as String,
      setLabel: freezed == setLabel
          ? _value.setLabel
          : setLabel // ignore: cast_nullable_to_non_nullable
              as String?,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PaperMetadataImplCopyWith<$Res>
    implements $PaperMetadataCopyWith<$Res> {
  factory _$$PaperMetadataImplCopyWith(
          _$PaperMetadataImpl value, $Res Function(_$PaperMetadataImpl) then) =
      __$$PaperMetadataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String assessmentTitle,
      String schoolName,
      String subject,
      int grade,
      int totalMarks,
      int durationMinutes,
      DateTime generatedAt,
      String generatedBy,
      String version,
      String? setLabel,
      String? tier,
      String? examType});
}

/// @nodoc
class __$$PaperMetadataImplCopyWithImpl<$Res>
    extends _$PaperMetadataCopyWithImpl<$Res, _$PaperMetadataImpl>
    implements _$$PaperMetadataImplCopyWith<$Res> {
  __$$PaperMetadataImplCopyWithImpl(
      _$PaperMetadataImpl _value, $Res Function(_$PaperMetadataImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentTitle = null,
    Object? schoolName = null,
    Object? subject = null,
    Object? grade = null,
    Object? totalMarks = null,
    Object? durationMinutes = null,
    Object? generatedAt = null,
    Object? generatedBy = null,
    Object? version = null,
    Object? setLabel = freezed,
    Object? tier = freezed,
    Object? examType = freezed,
  }) {
    return _then(_$PaperMetadataImpl(
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      schoolName: null == schoolName
          ? _value.schoolName
          : schoolName // ignore: cast_nullable_to_non_nullable
              as String,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      generatedBy: null == generatedBy
          ? _value.generatedBy
          : generatedBy // ignore: cast_nullable_to_non_nullable
              as String,
      version: null == version
          ? _value.version
          : version // ignore: cast_nullable_to_non_nullable
              as String,
      setLabel: freezed == setLabel
          ? _value.setLabel
          : setLabel // ignore: cast_nullable_to_non_nullable
              as String?,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PaperMetadataImpl implements _PaperMetadata {
  const _$PaperMetadataImpl(
      {required this.assessmentTitle,
      required this.schoolName,
      required this.subject,
      required this.grade,
      required this.totalMarks,
      required this.durationMinutes,
      required this.generatedAt,
      required this.generatedBy,
      required this.version,
      this.setLabel,
      this.tier,
      this.examType});

  factory _$PaperMetadataImpl.fromJson(Map<String, dynamic> json) =>
      _$$PaperMetadataImplFromJson(json);

  @override
  final String assessmentTitle;
  @override
  final String schoolName;
  @override
  final String subject;
  @override
  final int grade;
  @override
  final int totalMarks;
  @override
  final int durationMinutes;
  @override
  final DateTime generatedAt;
  @override
  final String generatedBy;
  @override
  final String version;
  @override
  final String? setLabel;
  @override
  final String? tier;
  @override
  final String? examType;

  @override
  String toString() {
    return 'PaperMetadata(assessmentTitle: $assessmentTitle, schoolName: $schoolName, subject: $subject, grade: $grade, totalMarks: $totalMarks, durationMinutes: $durationMinutes, generatedAt: $generatedAt, generatedBy: $generatedBy, version: $version, setLabel: $setLabel, tier: $tier, examType: $examType)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PaperMetadataImpl &&
            (identical(other.assessmentTitle, assessmentTitle) ||
                other.assessmentTitle == assessmentTitle) &&
            (identical(other.schoolName, schoolName) ||
                other.schoolName == schoolName) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            (identical(other.durationMinutes, durationMinutes) ||
                other.durationMinutes == durationMinutes) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt) &&
            (identical(other.generatedBy, generatedBy) ||
                other.generatedBy == generatedBy) &&
            (identical(other.version, version) || other.version == version) &&
            (identical(other.setLabel, setLabel) ||
                other.setLabel == setLabel) &&
            (identical(other.tier, tier) || other.tier == tier) &&
            (identical(other.examType, examType) ||
                other.examType == examType));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      assessmentTitle,
      schoolName,
      subject,
      grade,
      totalMarks,
      durationMinutes,
      generatedAt,
      generatedBy,
      version,
      setLabel,
      tier,
      examType);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PaperMetadataImplCopyWith<_$PaperMetadataImpl> get copyWith =>
      __$$PaperMetadataImplCopyWithImpl<_$PaperMetadataImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PaperMetadataImplToJson(
      this,
    );
  }
}

abstract class _PaperMetadata implements PaperMetadata {
  const factory _PaperMetadata(
      {required final String assessmentTitle,
      required final String schoolName,
      required final String subject,
      required final int grade,
      required final int totalMarks,
      required final int durationMinutes,
      required final DateTime generatedAt,
      required final String generatedBy,
      required final String version,
      final String? setLabel,
      final String? tier,
      final String? examType}) = _$PaperMetadataImpl;

  factory _PaperMetadata.fromJson(Map<String, dynamic> json) =
      _$PaperMetadataImpl.fromJson;

  @override
  String get assessmentTitle;
  @override
  String get schoolName;
  @override
  String get subject;
  @override
  int get grade;
  @override
  int get totalMarks;
  @override
  int get durationMinutes;
  @override
  DateTime get generatedAt;
  @override
  String get generatedBy;
  @override
  String get version;
  @override
  String? get setLabel;
  @override
  String? get tier;
  @override
  String? get examType;
  @override
  @JsonKey(ignore: true)
  _$$PaperMetadataImplCopyWith<_$PaperMetadataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuickPaperRequest _$QuickPaperRequestFromJson(Map<String, dynamic> json) {
  return _QuickPaperRequest.fromJson(json);
}

/// @nodoc
mixin _$QuickPaperRequest {
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  List<String> get chapterIds => throw _privateConstructorUsedError;
  String? get title => throw _privateConstructorUsedError;
  int get totalMarks => throw _privateConstructorUsedError;
  int? get durationMinutes => throw _privateConstructorUsedError;
  String get tier => throw _privateConstructorUsedError;
  String? get examType => throw _privateConstructorUsedError;
  int get setCount => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuickPaperRequestCopyWith<QuickPaperRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuickPaperRequestCopyWith<$Res> {
  factory $QuickPaperRequestCopyWith(
          QuickPaperRequest value, $Res Function(QuickPaperRequest) then) =
      _$QuickPaperRequestCopyWithImpl<$Res, QuickPaperRequest>;
  @useResult
  $Res call(
      {String subject,
      int grade,
      List<String> chapterIds,
      String? title,
      int totalMarks,
      int? durationMinutes,
      String tier,
      String? examType,
      int setCount});
}

/// @nodoc
class _$QuickPaperRequestCopyWithImpl<$Res, $Val extends QuickPaperRequest>
    implements $QuickPaperRequestCopyWith<$Res> {
  _$QuickPaperRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? title = freezed,
    Object? totalMarks = null,
    Object? durationMinutes = freezed,
    Object? tier = null,
    Object? examType = freezed,
    Object? setCount = null,
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
      chapterIds: null == chapterIds
          ? _value.chapterIds
          : chapterIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: freezed == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int?,
      tier: null == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
      setCount: null == setCount
          ? _value.setCount
          : setCount // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuickPaperRequestImplCopyWith<$Res>
    implements $QuickPaperRequestCopyWith<$Res> {
  factory _$$QuickPaperRequestImplCopyWith(_$QuickPaperRequestImpl value,
          $Res Function(_$QuickPaperRequestImpl) then) =
      __$$QuickPaperRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String subject,
      int grade,
      List<String> chapterIds,
      String? title,
      int totalMarks,
      int? durationMinutes,
      String tier,
      String? examType,
      int setCount});
}

/// @nodoc
class __$$QuickPaperRequestImplCopyWithImpl<$Res>
    extends _$QuickPaperRequestCopyWithImpl<$Res, _$QuickPaperRequestImpl>
    implements _$$QuickPaperRequestImplCopyWith<$Res> {
  __$$QuickPaperRequestImplCopyWithImpl(_$QuickPaperRequestImpl _value,
      $Res Function(_$QuickPaperRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? title = freezed,
    Object? totalMarks = null,
    Object? durationMinutes = freezed,
    Object? tier = null,
    Object? examType = freezed,
    Object? setCount = null,
  }) {
    return _then(_$QuickPaperRequestImpl(
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
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: freezed == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int?,
      tier: null == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
      setCount: null == setCount
          ? _value.setCount
          : setCount // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuickPaperRequestImpl implements _QuickPaperRequest {
  const _$QuickPaperRequestImpl(
      {required this.subject,
      this.grade = 10,
      final List<String> chapterIds = const [],
      this.title,
      this.totalMarks = 80,
      this.durationMinutes,
      this.tier = 'standard',
      this.examType,
      this.setCount = 1})
      : _chapterIds = chapterIds;

  factory _$QuickPaperRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuickPaperRequestImplFromJson(json);

  @override
  final String subject;
  @override
  @JsonKey()
  final int grade;
  final List<String> _chapterIds;
  @override
  @JsonKey()
  List<String> get chapterIds {
    if (_chapterIds is EqualUnmodifiableListView) return _chapterIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_chapterIds);
  }

  @override
  final String? title;
  @override
  @JsonKey()
  final int totalMarks;
  @override
  final int? durationMinutes;
  @override
  @JsonKey()
  final String tier;
  @override
  final String? examType;
  @override
  @JsonKey()
  final int setCount;

  @override
  String toString() {
    return 'QuickPaperRequest(subject: $subject, grade: $grade, chapterIds: $chapterIds, title: $title, totalMarks: $totalMarks, durationMinutes: $durationMinutes, tier: $tier, examType: $examType, setCount: $setCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuickPaperRequestImpl &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality()
                .equals(other._chapterIds, _chapterIds) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            (identical(other.durationMinutes, durationMinutes) ||
                other.durationMinutes == durationMinutes) &&
            (identical(other.tier, tier) || other.tier == tier) &&
            (identical(other.examType, examType) ||
                other.examType == examType) &&
            (identical(other.setCount, setCount) ||
                other.setCount == setCount));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      subject,
      grade,
      const DeepCollectionEquality().hash(_chapterIds),
      title,
      totalMarks,
      durationMinutes,
      tier,
      examType,
      setCount);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuickPaperRequestImplCopyWith<_$QuickPaperRequestImpl> get copyWith =>
      __$$QuickPaperRequestImplCopyWithImpl<_$QuickPaperRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuickPaperRequestImplToJson(
      this,
    );
  }
}

abstract class _QuickPaperRequest implements QuickPaperRequest {
  const factory _QuickPaperRequest(
      {required final String subject,
      final int grade,
      final List<String> chapterIds,
      final String? title,
      final int totalMarks,
      final int? durationMinutes,
      final String tier,
      final String? examType,
      final int setCount}) = _$QuickPaperRequestImpl;

  factory _QuickPaperRequest.fromJson(Map<String, dynamic> json) =
      _$QuickPaperRequestImpl.fromJson;

  @override
  String get subject;
  @override
  int get grade;
  @override
  List<String> get chapterIds;
  @override
  String? get title;
  @override
  int get totalMarks;
  @override
  int? get durationMinutes;
  @override
  String get tier;
  @override
  String? get examType;
  @override
  int get setCount;
  @override
  @JsonKey(ignore: true)
  _$$QuickPaperRequestImplCopyWith<_$QuickPaperRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

GenerateFromIdsRequest _$GenerateFromIdsRequestFromJson(
    Map<String, dynamic> json) {
  return _GenerateFromIdsRequest.fromJson(json);
}

/// @nodoc
mixin _$GenerateFromIdsRequest {
  List<String> get questionIds => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  String? get title => throw _privateConstructorUsedError;
  SchoolTemplate? get template => throw _privateConstructorUsedError;
  int get setCount => throw _privateConstructorUsedError;
  String? get tier => throw _privateConstructorUsedError;
  String? get examType => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $GenerateFromIdsRequestCopyWith<GenerateFromIdsRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $GenerateFromIdsRequestCopyWith<$Res> {
  factory $GenerateFromIdsRequestCopyWith(GenerateFromIdsRequest value,
          $Res Function(GenerateFromIdsRequest) then) =
      _$GenerateFromIdsRequestCopyWithImpl<$Res, GenerateFromIdsRequest>;
  @useResult
  $Res call(
      {List<String> questionIds,
      String subject,
      int grade,
      String? title,
      SchoolTemplate? template,
      int setCount,
      String? tier,
      String? examType});

  $SchoolTemplateCopyWith<$Res>? get template;
}

/// @nodoc
class _$GenerateFromIdsRequestCopyWithImpl<$Res,
        $Val extends GenerateFromIdsRequest>
    implements $GenerateFromIdsRequestCopyWith<$Res> {
  _$GenerateFromIdsRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionIds = null,
    Object? subject = null,
    Object? grade = null,
    Object? title = freezed,
    Object? template = freezed,
    Object? setCount = null,
    Object? tier = freezed,
    Object? examType = freezed,
  }) {
    return _then(_value.copyWith(
      questionIds: null == questionIds
          ? _value.questionIds
          : questionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      template: freezed == template
          ? _value.template
          : template // ignore: cast_nullable_to_non_nullable
              as SchoolTemplate?,
      setCount: null == setCount
          ? _value.setCount
          : setCount // ignore: cast_nullable_to_non_nullable
              as int,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $SchoolTemplateCopyWith<$Res>? get template {
    if (_value.template == null) {
      return null;
    }

    return $SchoolTemplateCopyWith<$Res>(_value.template!, (value) {
      return _then(_value.copyWith(template: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$GenerateFromIdsRequestImplCopyWith<$Res>
    implements $GenerateFromIdsRequestCopyWith<$Res> {
  factory _$$GenerateFromIdsRequestImplCopyWith(
          _$GenerateFromIdsRequestImpl value,
          $Res Function(_$GenerateFromIdsRequestImpl) then) =
      __$$GenerateFromIdsRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<String> questionIds,
      String subject,
      int grade,
      String? title,
      SchoolTemplate? template,
      int setCount,
      String? tier,
      String? examType});

  @override
  $SchoolTemplateCopyWith<$Res>? get template;
}

/// @nodoc
class __$$GenerateFromIdsRequestImplCopyWithImpl<$Res>
    extends _$GenerateFromIdsRequestCopyWithImpl<$Res,
        _$GenerateFromIdsRequestImpl>
    implements _$$GenerateFromIdsRequestImplCopyWith<$Res> {
  __$$GenerateFromIdsRequestImplCopyWithImpl(
      _$GenerateFromIdsRequestImpl _value,
      $Res Function(_$GenerateFromIdsRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionIds = null,
    Object? subject = null,
    Object? grade = null,
    Object? title = freezed,
    Object? template = freezed,
    Object? setCount = null,
    Object? tier = freezed,
    Object? examType = freezed,
  }) {
    return _then(_$GenerateFromIdsRequestImpl(
      questionIds: null == questionIds
          ? _value._questionIds
          : questionIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      subject: null == subject
          ? _value.subject
          : subject // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      template: freezed == template
          ? _value.template
          : template // ignore: cast_nullable_to_non_nullable
              as SchoolTemplate?,
      setCount: null == setCount
          ? _value.setCount
          : setCount // ignore: cast_nullable_to_non_nullable
              as int,
      tier: freezed == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String?,
      examType: freezed == examType
          ? _value.examType
          : examType // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$GenerateFromIdsRequestImpl implements _GenerateFromIdsRequest {
  const _$GenerateFromIdsRequestImpl(
      {required final List<String> questionIds,
      required this.subject,
      this.grade = 10,
      this.title,
      this.template,
      this.setCount = 1,
      this.tier,
      this.examType})
      : _questionIds = questionIds;

  factory _$GenerateFromIdsRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$GenerateFromIdsRequestImplFromJson(json);

  final List<String> _questionIds;
  @override
  List<String> get questionIds {
    if (_questionIds is EqualUnmodifiableListView) return _questionIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questionIds);
  }

  @override
  final String subject;
  @override
  @JsonKey()
  final int grade;
  @override
  final String? title;
  @override
  final SchoolTemplate? template;
  @override
  @JsonKey()
  final int setCount;
  @override
  final String? tier;
  @override
  final String? examType;

  @override
  String toString() {
    return 'GenerateFromIdsRequest(questionIds: $questionIds, subject: $subject, grade: $grade, title: $title, template: $template, setCount: $setCount, tier: $tier, examType: $examType)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$GenerateFromIdsRequestImpl &&
            const DeepCollectionEquality()
                .equals(other._questionIds, _questionIds) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.template, template) ||
                other.template == template) &&
            (identical(other.setCount, setCount) ||
                other.setCount == setCount) &&
            (identical(other.tier, tier) || other.tier == tier) &&
            (identical(other.examType, examType) ||
                other.examType == examType));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_questionIds),
      subject,
      grade,
      title,
      template,
      setCount,
      tier,
      examType);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$GenerateFromIdsRequestImplCopyWith<_$GenerateFromIdsRequestImpl>
      get copyWith => __$$GenerateFromIdsRequestImplCopyWithImpl<
          _$GenerateFromIdsRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$GenerateFromIdsRequestImplToJson(
      this,
    );
  }
}

abstract class _GenerateFromIdsRequest implements GenerateFromIdsRequest {
  const factory _GenerateFromIdsRequest(
      {required final List<String> questionIds,
      required final String subject,
      final int grade,
      final String? title,
      final SchoolTemplate? template,
      final int setCount,
      final String? tier,
      final String? examType}) = _$GenerateFromIdsRequestImpl;

  factory _GenerateFromIdsRequest.fromJson(Map<String, dynamic> json) =
      _$GenerateFromIdsRequestImpl.fromJson;

  @override
  List<String> get questionIds;
  @override
  String get subject;
  @override
  int get grade;
  @override
  String? get title;
  @override
  SchoolTemplate? get template;
  @override
  int get setCount;
  @override
  String? get tier;
  @override
  String? get examType;
  @override
  @JsonKey(ignore: true)
  _$$GenerateFromIdsRequestImplCopyWith<_$GenerateFromIdsRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

SchoolTemplate _$SchoolTemplateFromJson(Map<String, dynamic> json) {
  return _SchoolTemplate.fromJson(json);
}

/// @nodoc
mixin _$SchoolTemplate {
  String get id => throw _privateConstructorUsedError;
  String get schoolId => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get tagline => throw _privateConstructorUsedError;
  String get brandColor => throw _privateConstructorUsedError;
  String get headerHtml => throw _privateConstructorUsedError;
  String get footerHtml => throw _privateConstructorUsedError;
  String get logoUrl => throw _privateConstructorUsedError;
  double get marginTop => throw _privateConstructorUsedError;
  double get marginBottom => throw _privateConstructorUsedError;
  double get marginLeft => throw _privateConstructorUsedError;
  double get marginRight => throw _privateConstructorUsedError;
  String get fontFamily => throw _privateConstructorUsedError;
  int get fontSize => throw _privateConstructorUsedError;
  double get lineHeight => throw _privateConstructorUsedError;
  Map<String, dynamic> get sectionFormatting =>
      throw _privateConstructorUsedError;
  bool get isDefault => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SchoolTemplateCopyWith<SchoolTemplate> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SchoolTemplateCopyWith<$Res> {
  factory $SchoolTemplateCopyWith(
          SchoolTemplate value, $Res Function(SchoolTemplate) then) =
      _$SchoolTemplateCopyWithImpl<$Res, SchoolTemplate>;
  @useResult
  $Res call(
      {String id,
      String schoolId,
      String name,
      String tagline,
      String brandColor,
      String headerHtml,
      String footerHtml,
      String logoUrl,
      double marginTop,
      double marginBottom,
      double marginLeft,
      double marginRight,
      String fontFamily,
      int fontSize,
      double lineHeight,
      Map<String, dynamic> sectionFormatting,
      bool isDefault});
}

/// @nodoc
class _$SchoolTemplateCopyWithImpl<$Res, $Val extends SchoolTemplate>
    implements $SchoolTemplateCopyWith<$Res> {
  _$SchoolTemplateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? schoolId = null,
    Object? name = null,
    Object? tagline = null,
    Object? brandColor = null,
    Object? headerHtml = null,
    Object? footerHtml = null,
    Object? logoUrl = null,
    Object? marginTop = null,
    Object? marginBottom = null,
    Object? marginLeft = null,
    Object? marginRight = null,
    Object? fontFamily = null,
    Object? fontSize = null,
    Object? lineHeight = null,
    Object? sectionFormatting = null,
    Object? isDefault = null,
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
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      tagline: null == tagline
          ? _value.tagline
          : tagline // ignore: cast_nullable_to_non_nullable
              as String,
      brandColor: null == brandColor
          ? _value.brandColor
          : brandColor // ignore: cast_nullable_to_non_nullable
              as String,
      headerHtml: null == headerHtml
          ? _value.headerHtml
          : headerHtml // ignore: cast_nullable_to_non_nullable
              as String,
      footerHtml: null == footerHtml
          ? _value.footerHtml
          : footerHtml // ignore: cast_nullable_to_non_nullable
              as String,
      logoUrl: null == logoUrl
          ? _value.logoUrl
          : logoUrl // ignore: cast_nullable_to_non_nullable
              as String,
      marginTop: null == marginTop
          ? _value.marginTop
          : marginTop // ignore: cast_nullable_to_non_nullable
              as double,
      marginBottom: null == marginBottom
          ? _value.marginBottom
          : marginBottom // ignore: cast_nullable_to_non_nullable
              as double,
      marginLeft: null == marginLeft
          ? _value.marginLeft
          : marginLeft // ignore: cast_nullable_to_non_nullable
              as double,
      marginRight: null == marginRight
          ? _value.marginRight
          : marginRight // ignore: cast_nullable_to_non_nullable
              as double,
      fontFamily: null == fontFamily
          ? _value.fontFamily
          : fontFamily // ignore: cast_nullable_to_non_nullable
              as String,
      fontSize: null == fontSize
          ? _value.fontSize
          : fontSize // ignore: cast_nullable_to_non_nullable
              as int,
      lineHeight: null == lineHeight
          ? _value.lineHeight
          : lineHeight // ignore: cast_nullable_to_non_nullable
              as double,
      sectionFormatting: null == sectionFormatting
          ? _value.sectionFormatting
          : sectionFormatting // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      isDefault: null == isDefault
          ? _value.isDefault
          : isDefault // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SchoolTemplateImplCopyWith<$Res>
    implements $SchoolTemplateCopyWith<$Res> {
  factory _$$SchoolTemplateImplCopyWith(_$SchoolTemplateImpl value,
          $Res Function(_$SchoolTemplateImpl) then) =
      __$$SchoolTemplateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String schoolId,
      String name,
      String tagline,
      String brandColor,
      String headerHtml,
      String footerHtml,
      String logoUrl,
      double marginTop,
      double marginBottom,
      double marginLeft,
      double marginRight,
      String fontFamily,
      int fontSize,
      double lineHeight,
      Map<String, dynamic> sectionFormatting,
      bool isDefault});
}

/// @nodoc
class __$$SchoolTemplateImplCopyWithImpl<$Res>
    extends _$SchoolTemplateCopyWithImpl<$Res, _$SchoolTemplateImpl>
    implements _$$SchoolTemplateImplCopyWith<$Res> {
  __$$SchoolTemplateImplCopyWithImpl(
      _$SchoolTemplateImpl _value, $Res Function(_$SchoolTemplateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? schoolId = null,
    Object? name = null,
    Object? tagline = null,
    Object? brandColor = null,
    Object? headerHtml = null,
    Object? footerHtml = null,
    Object? logoUrl = null,
    Object? marginTop = null,
    Object? marginBottom = null,
    Object? marginLeft = null,
    Object? marginRight = null,
    Object? fontFamily = null,
    Object? fontSize = null,
    Object? lineHeight = null,
    Object? sectionFormatting = null,
    Object? isDefault = null,
  }) {
    return _then(_$SchoolTemplateImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      schoolId: null == schoolId
          ? _value.schoolId
          : schoolId // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      tagline: null == tagline
          ? _value.tagline
          : tagline // ignore: cast_nullable_to_non_nullable
              as String,
      brandColor: null == brandColor
          ? _value.brandColor
          : brandColor // ignore: cast_nullable_to_non_nullable
              as String,
      headerHtml: null == headerHtml
          ? _value.headerHtml
          : headerHtml // ignore: cast_nullable_to_non_nullable
              as String,
      footerHtml: null == footerHtml
          ? _value.footerHtml
          : footerHtml // ignore: cast_nullable_to_non_nullable
              as String,
      logoUrl: null == logoUrl
          ? _value.logoUrl
          : logoUrl // ignore: cast_nullable_to_non_nullable
              as String,
      marginTop: null == marginTop
          ? _value.marginTop
          : marginTop // ignore: cast_nullable_to_non_nullable
              as double,
      marginBottom: null == marginBottom
          ? _value.marginBottom
          : marginBottom // ignore: cast_nullable_to_non_nullable
              as double,
      marginLeft: null == marginLeft
          ? _value.marginLeft
          : marginLeft // ignore: cast_nullable_to_non_nullable
              as double,
      marginRight: null == marginRight
          ? _value.marginRight
          : marginRight // ignore: cast_nullable_to_non_nullable
              as double,
      fontFamily: null == fontFamily
          ? _value.fontFamily
          : fontFamily // ignore: cast_nullable_to_non_nullable
              as String,
      fontSize: null == fontSize
          ? _value.fontSize
          : fontSize // ignore: cast_nullable_to_non_nullable
              as int,
      lineHeight: null == lineHeight
          ? _value.lineHeight
          : lineHeight // ignore: cast_nullable_to_non_nullable
              as double,
      sectionFormatting: null == sectionFormatting
          ? _value._sectionFormatting
          : sectionFormatting // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      isDefault: null == isDefault
          ? _value.isDefault
          : isDefault // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SchoolTemplateImpl implements _SchoolTemplate {
  const _$SchoolTemplateImpl(
      {required this.id,
      required this.schoolId,
      required this.name,
      this.tagline = '',
      this.brandColor = '#000000',
      required this.headerHtml,
      required this.footerHtml,
      required this.logoUrl,
      required this.marginTop,
      required this.marginBottom,
      required this.marginLeft,
      required this.marginRight,
      required this.fontFamily,
      required this.fontSize,
      required this.lineHeight,
      required final Map<String, dynamic> sectionFormatting,
      required this.isDefault})
      : _sectionFormatting = sectionFormatting;

  factory _$SchoolTemplateImpl.fromJson(Map<String, dynamic> json) =>
      _$$SchoolTemplateImplFromJson(json);

  @override
  final String id;
  @override
  final String schoolId;
  @override
  final String name;
  @override
  @JsonKey()
  final String tagline;
  @override
  @JsonKey()
  final String brandColor;
  @override
  final String headerHtml;
  @override
  final String footerHtml;
  @override
  final String logoUrl;
  @override
  final double marginTop;
  @override
  final double marginBottom;
  @override
  final double marginLeft;
  @override
  final double marginRight;
  @override
  final String fontFamily;
  @override
  final int fontSize;
  @override
  final double lineHeight;
  final Map<String, dynamic> _sectionFormatting;
  @override
  Map<String, dynamic> get sectionFormatting {
    if (_sectionFormatting is EqualUnmodifiableMapView)
      return _sectionFormatting;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_sectionFormatting);
  }

  @override
  final bool isDefault;

  @override
  String toString() {
    return 'SchoolTemplate(id: $id, schoolId: $schoolId, name: $name, tagline: $tagline, brandColor: $brandColor, headerHtml: $headerHtml, footerHtml: $footerHtml, logoUrl: $logoUrl, marginTop: $marginTop, marginBottom: $marginBottom, marginLeft: $marginLeft, marginRight: $marginRight, fontFamily: $fontFamily, fontSize: $fontSize, lineHeight: $lineHeight, sectionFormatting: $sectionFormatting, isDefault: $isDefault)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SchoolTemplateImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.schoolId, schoolId) ||
                other.schoolId == schoolId) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.tagline, tagline) || other.tagline == tagline) &&
            (identical(other.brandColor, brandColor) ||
                other.brandColor == brandColor) &&
            (identical(other.headerHtml, headerHtml) ||
                other.headerHtml == headerHtml) &&
            (identical(other.footerHtml, footerHtml) ||
                other.footerHtml == footerHtml) &&
            (identical(other.logoUrl, logoUrl) || other.logoUrl == logoUrl) &&
            (identical(other.marginTop, marginTop) ||
                other.marginTop == marginTop) &&
            (identical(other.marginBottom, marginBottom) ||
                other.marginBottom == marginBottom) &&
            (identical(other.marginLeft, marginLeft) ||
                other.marginLeft == marginLeft) &&
            (identical(other.marginRight, marginRight) ||
                other.marginRight == marginRight) &&
            (identical(other.fontFamily, fontFamily) ||
                other.fontFamily == fontFamily) &&
            (identical(other.fontSize, fontSize) ||
                other.fontSize == fontSize) &&
            (identical(other.lineHeight, lineHeight) ||
                other.lineHeight == lineHeight) &&
            const DeepCollectionEquality()
                .equals(other._sectionFormatting, _sectionFormatting) &&
            (identical(other.isDefault, isDefault) ||
                other.isDefault == isDefault));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      schoolId,
      name,
      tagline,
      brandColor,
      headerHtml,
      footerHtml,
      logoUrl,
      marginTop,
      marginBottom,
      marginLeft,
      marginRight,
      fontFamily,
      fontSize,
      lineHeight,
      const DeepCollectionEquality().hash(_sectionFormatting),
      isDefault);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SchoolTemplateImplCopyWith<_$SchoolTemplateImpl> get copyWith =>
      __$$SchoolTemplateImplCopyWithImpl<_$SchoolTemplateImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SchoolTemplateImplToJson(
      this,
    );
  }
}

abstract class _SchoolTemplate implements SchoolTemplate {
  const factory _SchoolTemplate(
      {required final String id,
      required final String schoolId,
      required final String name,
      final String tagline,
      final String brandColor,
      required final String headerHtml,
      required final String footerHtml,
      required final String logoUrl,
      required final double marginTop,
      required final double marginBottom,
      required final double marginLeft,
      required final double marginRight,
      required final String fontFamily,
      required final int fontSize,
      required final double lineHeight,
      required final Map<String, dynamic> sectionFormatting,
      required final bool isDefault}) = _$SchoolTemplateImpl;

  factory _SchoolTemplate.fromJson(Map<String, dynamic> json) =
      _$SchoolTemplateImpl.fromJson;

  @override
  String get id;
  @override
  String get schoolId;
  @override
  String get name;
  @override
  String get tagline;
  @override
  String get brandColor;
  @override
  String get headerHtml;
  @override
  String get footerHtml;
  @override
  String get logoUrl;
  @override
  double get marginTop;
  @override
  double get marginBottom;
  @override
  double get marginLeft;
  @override
  double get marginRight;
  @override
  String get fontFamily;
  @override
  int get fontSize;
  @override
  double get lineHeight;
  @override
  Map<String, dynamic> get sectionFormatting;
  @override
  bool get isDefault;
  @override
  @JsonKey(ignore: true)
  _$$SchoolTemplateImplCopyWith<_$SchoolTemplateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AnswerSheetUpload _$AnswerSheetUploadFromJson(Map<String, dynamic> json) {
  return _AnswerSheetUpload.fromJson(json);
}

/// @nodoc
mixin _$AnswerSheetUpload {
  String get assessmentId => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  String get studentName => throw _privateConstructorUsedError;
  String get rollNumber => throw _privateConstructorUsedError;
  List<String> get imagePaths => throw _privateConstructorUsedError;
  ScanMetadata get scanMetadata => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AnswerSheetUploadCopyWith<AnswerSheetUpload> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AnswerSheetUploadCopyWith<$Res> {
  factory $AnswerSheetUploadCopyWith(
          AnswerSheetUpload value, $Res Function(AnswerSheetUpload) then) =
      _$AnswerSheetUploadCopyWithImpl<$Res, AnswerSheetUpload>;
  @useResult
  $Res call(
      {String assessmentId,
      String studentId,
      String studentName,
      String rollNumber,
      List<String> imagePaths,
      ScanMetadata scanMetadata});

  $ScanMetadataCopyWith<$Res> get scanMetadata;
}

/// @nodoc
class _$AnswerSheetUploadCopyWithImpl<$Res, $Val extends AnswerSheetUpload>
    implements $AnswerSheetUploadCopyWith<$Res> {
  _$AnswerSheetUploadCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? imagePaths = null,
    Object? scanMetadata = null,
  }) {
    return _then(_value.copyWith(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
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
      imagePaths: null == imagePaths
          ? _value.imagePaths
          : imagePaths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      scanMetadata: null == scanMetadata
          ? _value.scanMetadata
          : scanMetadata // ignore: cast_nullable_to_non_nullable
              as ScanMetadata,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ScanMetadataCopyWith<$Res> get scanMetadata {
    return $ScanMetadataCopyWith<$Res>(_value.scanMetadata, (value) {
      return _then(_value.copyWith(scanMetadata: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AnswerSheetUploadImplCopyWith<$Res>
    implements $AnswerSheetUploadCopyWith<$Res> {
  factory _$$AnswerSheetUploadImplCopyWith(_$AnswerSheetUploadImpl value,
          $Res Function(_$AnswerSheetUploadImpl) then) =
      __$$AnswerSheetUploadImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String assessmentId,
      String studentId,
      String studentName,
      String rollNumber,
      List<String> imagePaths,
      ScanMetadata scanMetadata});

  @override
  $ScanMetadataCopyWith<$Res> get scanMetadata;
}

/// @nodoc
class __$$AnswerSheetUploadImplCopyWithImpl<$Res>
    extends _$AnswerSheetUploadCopyWithImpl<$Res, _$AnswerSheetUploadImpl>
    implements _$$AnswerSheetUploadImplCopyWith<$Res> {
  __$$AnswerSheetUploadImplCopyWithImpl(_$AnswerSheetUploadImpl _value,
      $Res Function(_$AnswerSheetUploadImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? imagePaths = null,
    Object? scanMetadata = null,
  }) {
    return _then(_$AnswerSheetUploadImpl(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
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
      imagePaths: null == imagePaths
          ? _value._imagePaths
          : imagePaths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      scanMetadata: null == scanMetadata
          ? _value.scanMetadata
          : scanMetadata // ignore: cast_nullable_to_non_nullable
              as ScanMetadata,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AnswerSheetUploadImpl implements _AnswerSheetUpload {
  const _$AnswerSheetUploadImpl(
      {required this.assessmentId,
      required this.studentId,
      required this.studentName,
      required this.rollNumber,
      required final List<String> imagePaths,
      required this.scanMetadata})
      : _imagePaths = imagePaths;

  factory _$AnswerSheetUploadImpl.fromJson(Map<String, dynamic> json) =>
      _$$AnswerSheetUploadImplFromJson(json);

  @override
  final String assessmentId;
  @override
  final String studentId;
  @override
  final String studentName;
  @override
  final String rollNumber;
  final List<String> _imagePaths;
  @override
  List<String> get imagePaths {
    if (_imagePaths is EqualUnmodifiableListView) return _imagePaths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_imagePaths);
  }

  @override
  final ScanMetadata scanMetadata;

  @override
  String toString() {
    return 'AnswerSheetUpload(assessmentId: $assessmentId, studentId: $studentId, studentName: $studentName, rollNumber: $rollNumber, imagePaths: $imagePaths, scanMetadata: $scanMetadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AnswerSheetUploadImpl &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.studentName, studentName) ||
                other.studentName == studentName) &&
            (identical(other.rollNumber, rollNumber) ||
                other.rollNumber == rollNumber) &&
            const DeepCollectionEquality()
                .equals(other._imagePaths, _imagePaths) &&
            (identical(other.scanMetadata, scanMetadata) ||
                other.scanMetadata == scanMetadata));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      assessmentId,
      studentId,
      studentName,
      rollNumber,
      const DeepCollectionEquality().hash(_imagePaths),
      scanMetadata);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AnswerSheetUploadImplCopyWith<_$AnswerSheetUploadImpl> get copyWith =>
      __$$AnswerSheetUploadImplCopyWithImpl<_$AnswerSheetUploadImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AnswerSheetUploadImplToJson(
      this,
    );
  }
}

abstract class _AnswerSheetUpload implements AnswerSheetUpload {
  const factory _AnswerSheetUpload(
      {required final String assessmentId,
      required final String studentId,
      required final String studentName,
      required final String rollNumber,
      required final List<String> imagePaths,
      required final ScanMetadata scanMetadata}) = _$AnswerSheetUploadImpl;

  factory _AnswerSheetUpload.fromJson(Map<String, dynamic> json) =
      _$AnswerSheetUploadImpl.fromJson;

  @override
  String get assessmentId;
  @override
  String get studentId;
  @override
  String get studentName;
  @override
  String get rollNumber;
  @override
  List<String> get imagePaths;
  @override
  ScanMetadata get scanMetadata;
  @override
  @JsonKey(ignore: true)
  _$$AnswerSheetUploadImplCopyWith<_$AnswerSheetUploadImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ScanRequest _$ScanRequestFromJson(Map<String, dynamic> json) {
  return _ScanRequest.fromJson(json);
}

/// @nodoc
mixin _$ScanRequest {
  String get answerSheetId => throw _privateConstructorUsedError;
  List<String> get imagePaths => throw _privateConstructorUsedError;
  ScanOptions get options => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ScanRequestCopyWith<ScanRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ScanRequestCopyWith<$Res> {
  factory $ScanRequestCopyWith(
          ScanRequest value, $Res Function(ScanRequest) then) =
      _$ScanRequestCopyWithImpl<$Res, ScanRequest>;
  @useResult
  $Res call(
      {String answerSheetId, List<String> imagePaths, ScanOptions options});

  $ScanOptionsCopyWith<$Res> get options;
}

/// @nodoc
class _$ScanRequestCopyWithImpl<$Res, $Val extends ScanRequest>
    implements $ScanRequestCopyWith<$Res> {
  _$ScanRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? answerSheetId = null,
    Object? imagePaths = null,
    Object? options = null,
  }) {
    return _then(_value.copyWith(
      answerSheetId: null == answerSheetId
          ? _value.answerSheetId
          : answerSheetId // ignore: cast_nullable_to_non_nullable
              as String,
      imagePaths: null == imagePaths
          ? _value.imagePaths
          : imagePaths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      options: null == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as ScanOptions,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ScanOptionsCopyWith<$Res> get options {
    return $ScanOptionsCopyWith<$Res>(_value.options, (value) {
      return _then(_value.copyWith(options: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ScanRequestImplCopyWith<$Res>
    implements $ScanRequestCopyWith<$Res> {
  factory _$$ScanRequestImplCopyWith(
          _$ScanRequestImpl value, $Res Function(_$ScanRequestImpl) then) =
      __$$ScanRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String answerSheetId, List<String> imagePaths, ScanOptions options});

  @override
  $ScanOptionsCopyWith<$Res> get options;
}

/// @nodoc
class __$$ScanRequestImplCopyWithImpl<$Res>
    extends _$ScanRequestCopyWithImpl<$Res, _$ScanRequestImpl>
    implements _$$ScanRequestImplCopyWith<$Res> {
  __$$ScanRequestImplCopyWithImpl(
      _$ScanRequestImpl _value, $Res Function(_$ScanRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? answerSheetId = null,
    Object? imagePaths = null,
    Object? options = null,
  }) {
    return _then(_$ScanRequestImpl(
      answerSheetId: null == answerSheetId
          ? _value.answerSheetId
          : answerSheetId // ignore: cast_nullable_to_non_nullable
              as String,
      imagePaths: null == imagePaths
          ? _value._imagePaths
          : imagePaths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      options: null == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as ScanOptions,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ScanRequestImpl implements _ScanRequest {
  const _$ScanRequestImpl(
      {required this.answerSheetId,
      required final List<String> imagePaths,
      required this.options})
      : _imagePaths = imagePaths;

  factory _$ScanRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$ScanRequestImplFromJson(json);

  @override
  final String answerSheetId;
  final List<String> _imagePaths;
  @override
  List<String> get imagePaths {
    if (_imagePaths is EqualUnmodifiableListView) return _imagePaths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_imagePaths);
  }

  @override
  final ScanOptions options;

  @override
  String toString() {
    return 'ScanRequest(answerSheetId: $answerSheetId, imagePaths: $imagePaths, options: $options)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ScanRequestImpl &&
            (identical(other.answerSheetId, answerSheetId) ||
                other.answerSheetId == answerSheetId) &&
            const DeepCollectionEquality()
                .equals(other._imagePaths, _imagePaths) &&
            (identical(other.options, options) || other.options == options));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, answerSheetId,
      const DeepCollectionEquality().hash(_imagePaths), options);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ScanRequestImplCopyWith<_$ScanRequestImpl> get copyWith =>
      __$$ScanRequestImplCopyWithImpl<_$ScanRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ScanRequestImplToJson(
      this,
    );
  }
}

abstract class _ScanRequest implements ScanRequest {
  const factory _ScanRequest(
      {required final String answerSheetId,
      required final List<String> imagePaths,
      required final ScanOptions options}) = _$ScanRequestImpl;

  factory _ScanRequest.fromJson(Map<String, dynamic> json) =
      _$ScanRequestImpl.fromJson;

  @override
  String get answerSheetId;
  @override
  List<String> get imagePaths;
  @override
  ScanOptions get options;
  @override
  @JsonKey(ignore: true)
  _$$ScanRequestImplCopyWith<_$ScanRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ScanOptions _$ScanOptionsFromJson(Map<String, dynamic> json) {
  return _ScanOptions.fromJson(json);
}

/// @nodoc
mixin _$ScanOptions {
  bool get autoRotate => throw _privateConstructorUsedError;
  bool get perspectiveCorrection => throw _privateConstructorUsedError;
  bool get shadowRemoval => throw _privateConstructorUsedError;
  bool get noiseReduction => throw _privateConstructorUsedError;
  bool get contrastEnhancement => throw _privateConstructorUsedError;
  bool get whiteBalance => throw _privateConstructorUsedError;
  bool get dewarp => throw _privateConstructorUsedError;
  bool get pageOrdering => throw _privateConstructorUsedError;
  int get targetDpi => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ScanOptionsCopyWith<ScanOptions> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ScanOptionsCopyWith<$Res> {
  factory $ScanOptionsCopyWith(
          ScanOptions value, $Res Function(ScanOptions) then) =
      _$ScanOptionsCopyWithImpl<$Res, ScanOptions>;
  @useResult
  $Res call(
      {bool autoRotate,
      bool perspectiveCorrection,
      bool shadowRemoval,
      bool noiseReduction,
      bool contrastEnhancement,
      bool whiteBalance,
      bool dewarp,
      bool pageOrdering,
      int targetDpi});
}

/// @nodoc
class _$ScanOptionsCopyWithImpl<$Res, $Val extends ScanOptions>
    implements $ScanOptionsCopyWith<$Res> {
  _$ScanOptionsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? autoRotate = null,
    Object? perspectiveCorrection = null,
    Object? shadowRemoval = null,
    Object? noiseReduction = null,
    Object? contrastEnhancement = null,
    Object? whiteBalance = null,
    Object? dewarp = null,
    Object? pageOrdering = null,
    Object? targetDpi = null,
  }) {
    return _then(_value.copyWith(
      autoRotate: null == autoRotate
          ? _value.autoRotate
          : autoRotate // ignore: cast_nullable_to_non_nullable
              as bool,
      perspectiveCorrection: null == perspectiveCorrection
          ? _value.perspectiveCorrection
          : perspectiveCorrection // ignore: cast_nullable_to_non_nullable
              as bool,
      shadowRemoval: null == shadowRemoval
          ? _value.shadowRemoval
          : shadowRemoval // ignore: cast_nullable_to_non_nullable
              as bool,
      noiseReduction: null == noiseReduction
          ? _value.noiseReduction
          : noiseReduction // ignore: cast_nullable_to_non_nullable
              as bool,
      contrastEnhancement: null == contrastEnhancement
          ? _value.contrastEnhancement
          : contrastEnhancement // ignore: cast_nullable_to_non_nullable
              as bool,
      whiteBalance: null == whiteBalance
          ? _value.whiteBalance
          : whiteBalance // ignore: cast_nullable_to_non_nullable
              as bool,
      dewarp: null == dewarp
          ? _value.dewarp
          : dewarp // ignore: cast_nullable_to_non_nullable
              as bool,
      pageOrdering: null == pageOrdering
          ? _value.pageOrdering
          : pageOrdering // ignore: cast_nullable_to_non_nullable
              as bool,
      targetDpi: null == targetDpi
          ? _value.targetDpi
          : targetDpi // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ScanOptionsImplCopyWith<$Res>
    implements $ScanOptionsCopyWith<$Res> {
  factory _$$ScanOptionsImplCopyWith(
          _$ScanOptionsImpl value, $Res Function(_$ScanOptionsImpl) then) =
      __$$ScanOptionsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool autoRotate,
      bool perspectiveCorrection,
      bool shadowRemoval,
      bool noiseReduction,
      bool contrastEnhancement,
      bool whiteBalance,
      bool dewarp,
      bool pageOrdering,
      int targetDpi});
}

/// @nodoc
class __$$ScanOptionsImplCopyWithImpl<$Res>
    extends _$ScanOptionsCopyWithImpl<$Res, _$ScanOptionsImpl>
    implements _$$ScanOptionsImplCopyWith<$Res> {
  __$$ScanOptionsImplCopyWithImpl(
      _$ScanOptionsImpl _value, $Res Function(_$ScanOptionsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? autoRotate = null,
    Object? perspectiveCorrection = null,
    Object? shadowRemoval = null,
    Object? noiseReduction = null,
    Object? contrastEnhancement = null,
    Object? whiteBalance = null,
    Object? dewarp = null,
    Object? pageOrdering = null,
    Object? targetDpi = null,
  }) {
    return _then(_$ScanOptionsImpl(
      autoRotate: null == autoRotate
          ? _value.autoRotate
          : autoRotate // ignore: cast_nullable_to_non_nullable
              as bool,
      perspectiveCorrection: null == perspectiveCorrection
          ? _value.perspectiveCorrection
          : perspectiveCorrection // ignore: cast_nullable_to_non_nullable
              as bool,
      shadowRemoval: null == shadowRemoval
          ? _value.shadowRemoval
          : shadowRemoval // ignore: cast_nullable_to_non_nullable
              as bool,
      noiseReduction: null == noiseReduction
          ? _value.noiseReduction
          : noiseReduction // ignore: cast_nullable_to_non_nullable
              as bool,
      contrastEnhancement: null == contrastEnhancement
          ? _value.contrastEnhancement
          : contrastEnhancement // ignore: cast_nullable_to_non_nullable
              as bool,
      whiteBalance: null == whiteBalance
          ? _value.whiteBalance
          : whiteBalance // ignore: cast_nullable_to_non_nullable
              as bool,
      dewarp: null == dewarp
          ? _value.dewarp
          : dewarp // ignore: cast_nullable_to_non_nullable
              as bool,
      pageOrdering: null == pageOrdering
          ? _value.pageOrdering
          : pageOrdering // ignore: cast_nullable_to_non_nullable
              as bool,
      targetDpi: null == targetDpi
          ? _value.targetDpi
          : targetDpi // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ScanOptionsImpl implements _ScanOptions {
  const _$ScanOptionsImpl(
      {this.autoRotate = true,
      this.perspectiveCorrection = true,
      this.shadowRemoval = true,
      this.noiseReduction = true,
      this.contrastEnhancement = true,
      this.whiteBalance = true,
      this.dewarp = true,
      this.pageOrdering = true,
      this.targetDpi = 300});

  factory _$ScanOptionsImpl.fromJson(Map<String, dynamic> json) =>
      _$$ScanOptionsImplFromJson(json);

  @override
  @JsonKey()
  final bool autoRotate;
  @override
  @JsonKey()
  final bool perspectiveCorrection;
  @override
  @JsonKey()
  final bool shadowRemoval;
  @override
  @JsonKey()
  final bool noiseReduction;
  @override
  @JsonKey()
  final bool contrastEnhancement;
  @override
  @JsonKey()
  final bool whiteBalance;
  @override
  @JsonKey()
  final bool dewarp;
  @override
  @JsonKey()
  final bool pageOrdering;
  @override
  @JsonKey()
  final int targetDpi;

  @override
  String toString() {
    return 'ScanOptions(autoRotate: $autoRotate, perspectiveCorrection: $perspectiveCorrection, shadowRemoval: $shadowRemoval, noiseReduction: $noiseReduction, contrastEnhancement: $contrastEnhancement, whiteBalance: $whiteBalance, dewarp: $dewarp, pageOrdering: $pageOrdering, targetDpi: $targetDpi)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ScanOptionsImpl &&
            (identical(other.autoRotate, autoRotate) ||
                other.autoRotate == autoRotate) &&
            (identical(other.perspectiveCorrection, perspectiveCorrection) ||
                other.perspectiveCorrection == perspectiveCorrection) &&
            (identical(other.shadowRemoval, shadowRemoval) ||
                other.shadowRemoval == shadowRemoval) &&
            (identical(other.noiseReduction, noiseReduction) ||
                other.noiseReduction == noiseReduction) &&
            (identical(other.contrastEnhancement, contrastEnhancement) ||
                other.contrastEnhancement == contrastEnhancement) &&
            (identical(other.whiteBalance, whiteBalance) ||
                other.whiteBalance == whiteBalance) &&
            (identical(other.dewarp, dewarp) || other.dewarp == dewarp) &&
            (identical(other.pageOrdering, pageOrdering) ||
                other.pageOrdering == pageOrdering) &&
            (identical(other.targetDpi, targetDpi) ||
                other.targetDpi == targetDpi));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      autoRotate,
      perspectiveCorrection,
      shadowRemoval,
      noiseReduction,
      contrastEnhancement,
      whiteBalance,
      dewarp,
      pageOrdering,
      targetDpi);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ScanOptionsImplCopyWith<_$ScanOptionsImpl> get copyWith =>
      __$$ScanOptionsImplCopyWithImpl<_$ScanOptionsImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ScanOptionsImplToJson(
      this,
    );
  }
}

abstract class _ScanOptions implements ScanOptions {
  const factory _ScanOptions(
      {final bool autoRotate,
      final bool perspectiveCorrection,
      final bool shadowRemoval,
      final bool noiseReduction,
      final bool contrastEnhancement,
      final bool whiteBalance,
      final bool dewarp,
      final bool pageOrdering,
      final int targetDpi}) = _$ScanOptionsImpl;

  factory _ScanOptions.fromJson(Map<String, dynamic> json) =
      _$ScanOptionsImpl.fromJson;

  @override
  bool get autoRotate;
  @override
  bool get perspectiveCorrection;
  @override
  bool get shadowRemoval;
  @override
  bool get noiseReduction;
  @override
  bool get contrastEnhancement;
  @override
  bool get whiteBalance;
  @override
  bool get dewarp;
  @override
  bool get pageOrdering;
  @override
  int get targetDpi;
  @override
  @JsonKey(ignore: true)
  _$$ScanOptionsImplCopyWith<_$ScanOptionsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

EvaluationRequest _$EvaluationRequestFromJson(Map<String, dynamic> json) {
  return _EvaluationRequest.fromJson(json);
}

/// @nodoc
mixin _$EvaluationRequest {
  String get questionId => throw _privateConstructorUsedError;
  Question get question => throw _privateConstructorUsedError;
  String get studentAnswer => throw _privateConstructorUsedError;
  String get studentAnswerLatex => throw _privateConstructorUsedError;
  List<String> get studentAnswerImages => throw _privateConstructorUsedError;
  AnswerScheme get answerScheme => throw _privateConstructorUsedError;
  EvaluationContext get context => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $EvaluationRequestCopyWith<EvaluationRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $EvaluationRequestCopyWith<$Res> {
  factory $EvaluationRequestCopyWith(
          EvaluationRequest value, $Res Function(EvaluationRequest) then) =
      _$EvaluationRequestCopyWithImpl<$Res, EvaluationRequest>;
  @useResult
  $Res call(
      {String questionId,
      Question question,
      String studentAnswer,
      String studentAnswerLatex,
      List<String> studentAnswerImages,
      AnswerScheme answerScheme,
      EvaluationContext context});

  $QuestionCopyWith<$Res> get question;
  $AnswerSchemeCopyWith<$Res> get answerScheme;
  $EvaluationContextCopyWith<$Res> get context;
}

/// @nodoc
class _$EvaluationRequestCopyWithImpl<$Res, $Val extends EvaluationRequest>
    implements $EvaluationRequestCopyWith<$Res> {
  _$EvaluationRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? question = null,
    Object? studentAnswer = null,
    Object? studentAnswerLatex = null,
    Object? studentAnswerImages = null,
    Object? answerScheme = null,
    Object? context = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      question: null == question
          ? _value.question
          : question // ignore: cast_nullable_to_non_nullable
              as Question,
      studentAnswer: null == studentAnswer
          ? _value.studentAnswer
          : studentAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerLatex: null == studentAnswerLatex
          ? _value.studentAnswerLatex
          : studentAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerImages: null == studentAnswerImages
          ? _value.studentAnswerImages
          : studentAnswerImages // ignore: cast_nullable_to_non_nullable
              as List<String>,
      answerScheme: null == answerScheme
          ? _value.answerScheme
          : answerScheme // ignore: cast_nullable_to_non_nullable
              as AnswerScheme,
      context: null == context
          ? _value.context
          : context // ignore: cast_nullable_to_non_nullable
              as EvaluationContext,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $QuestionCopyWith<$Res> get question {
    return $QuestionCopyWith<$Res>(_value.question, (value) {
      return _then(_value.copyWith(question: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $AnswerSchemeCopyWith<$Res> get answerScheme {
    return $AnswerSchemeCopyWith<$Res>(_value.answerScheme, (value) {
      return _then(_value.copyWith(answerScheme: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $EvaluationContextCopyWith<$Res> get context {
    return $EvaluationContextCopyWith<$Res>(_value.context, (value) {
      return _then(_value.copyWith(context: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$EvaluationRequestImplCopyWith<$Res>
    implements $EvaluationRequestCopyWith<$Res> {
  factory _$$EvaluationRequestImplCopyWith(_$EvaluationRequestImpl value,
          $Res Function(_$EvaluationRequestImpl) then) =
      __$$EvaluationRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      Question question,
      String studentAnswer,
      String studentAnswerLatex,
      List<String> studentAnswerImages,
      AnswerScheme answerScheme,
      EvaluationContext context});

  @override
  $QuestionCopyWith<$Res> get question;
  @override
  $AnswerSchemeCopyWith<$Res> get answerScheme;
  @override
  $EvaluationContextCopyWith<$Res> get context;
}

/// @nodoc
class __$$EvaluationRequestImplCopyWithImpl<$Res>
    extends _$EvaluationRequestCopyWithImpl<$Res, _$EvaluationRequestImpl>
    implements _$$EvaluationRequestImplCopyWith<$Res> {
  __$$EvaluationRequestImplCopyWithImpl(_$EvaluationRequestImpl _value,
      $Res Function(_$EvaluationRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? question = null,
    Object? studentAnswer = null,
    Object? studentAnswerLatex = null,
    Object? studentAnswerImages = null,
    Object? answerScheme = null,
    Object? context = null,
  }) {
    return _then(_$EvaluationRequestImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      question: null == question
          ? _value.question
          : question // ignore: cast_nullable_to_non_nullable
              as Question,
      studentAnswer: null == studentAnswer
          ? _value.studentAnswer
          : studentAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerLatex: null == studentAnswerLatex
          ? _value.studentAnswerLatex
          : studentAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerImages: null == studentAnswerImages
          ? _value._studentAnswerImages
          : studentAnswerImages // ignore: cast_nullable_to_non_nullable
              as List<String>,
      answerScheme: null == answerScheme
          ? _value.answerScheme
          : answerScheme // ignore: cast_nullable_to_non_nullable
              as AnswerScheme,
      context: null == context
          ? _value.context
          : context // ignore: cast_nullable_to_non_nullable
              as EvaluationContext,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$EvaluationRequestImpl implements _EvaluationRequest {
  const _$EvaluationRequestImpl(
      {required this.questionId,
      required this.question,
      required this.studentAnswer,
      required this.studentAnswerLatex,
      required final List<String> studentAnswerImages,
      required this.answerScheme,
      required this.context})
      : _studentAnswerImages = studentAnswerImages;

  factory _$EvaluationRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$EvaluationRequestImplFromJson(json);

  @override
  final String questionId;
  @override
  final Question question;
  @override
  final String studentAnswer;
  @override
  final String studentAnswerLatex;
  final List<String> _studentAnswerImages;
  @override
  List<String> get studentAnswerImages {
    if (_studentAnswerImages is EqualUnmodifiableListView)
      return _studentAnswerImages;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_studentAnswerImages);
  }

  @override
  final AnswerScheme answerScheme;
  @override
  final EvaluationContext context;

  @override
  String toString() {
    return 'EvaluationRequest(questionId: $questionId, question: $question, studentAnswer: $studentAnswer, studentAnswerLatex: $studentAnswerLatex, studentAnswerImages: $studentAnswerImages, answerScheme: $answerScheme, context: $context)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$EvaluationRequestImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.question, question) ||
                other.question == question) &&
            (identical(other.studentAnswer, studentAnswer) ||
                other.studentAnswer == studentAnswer) &&
            (identical(other.studentAnswerLatex, studentAnswerLatex) ||
                other.studentAnswerLatex == studentAnswerLatex) &&
            const DeepCollectionEquality()
                .equals(other._studentAnswerImages, _studentAnswerImages) &&
            (identical(other.answerScheme, answerScheme) ||
                other.answerScheme == answerScheme) &&
            (identical(other.context, context) || other.context == context));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      question,
      studentAnswer,
      studentAnswerLatex,
      const DeepCollectionEquality().hash(_studentAnswerImages),
      answerScheme,
      context);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$EvaluationRequestImplCopyWith<_$EvaluationRequestImpl> get copyWith =>
      __$$EvaluationRequestImplCopyWithImpl<_$EvaluationRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$EvaluationRequestImplToJson(
      this,
    );
  }
}

abstract class _EvaluationRequest implements EvaluationRequest {
  const factory _EvaluationRequest(
      {required final String questionId,
      required final Question question,
      required final String studentAnswer,
      required final String studentAnswerLatex,
      required final List<String> studentAnswerImages,
      required final AnswerScheme answerScheme,
      required final EvaluationContext context}) = _$EvaluationRequestImpl;

  factory _EvaluationRequest.fromJson(Map<String, dynamic> json) =
      _$EvaluationRequestImpl.fromJson;

  @override
  String get questionId;
  @override
  Question get question;
  @override
  String get studentAnswer;
  @override
  String get studentAnswerLatex;
  @override
  List<String> get studentAnswerImages;
  @override
  AnswerScheme get answerScheme;
  @override
  EvaluationContext get context;
  @override
  @JsonKey(ignore: true)
  _$$EvaluationRequestImplCopyWith<_$EvaluationRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

EvaluationContext _$EvaluationContextFromJson(Map<String, dynamic> json) {
  return _EvaluationContext.fromJson(json);
}

/// @nodoc
mixin _$EvaluationContext {
  String get studentId => throw _privateConstructorUsedError;
  String get assessmentId => throw _privateConstructorUsedError;
  Map<String, double> get studentMastery => throw _privateConstructorUsedError;
  List<String> get previousMisconceptions => throw _privateConstructorUsedError;
  bool get isPractice => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $EvaluationContextCopyWith<EvaluationContext> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $EvaluationContextCopyWith<$Res> {
  factory $EvaluationContextCopyWith(
          EvaluationContext value, $Res Function(EvaluationContext) then) =
      _$EvaluationContextCopyWithImpl<$Res, EvaluationContext>;
  @useResult
  $Res call(
      {String studentId,
      String assessmentId,
      Map<String, double> studentMastery,
      List<String> previousMisconceptions,
      bool isPractice});
}

/// @nodoc
class _$EvaluationContextCopyWithImpl<$Res, $Val extends EvaluationContext>
    implements $EvaluationContextCopyWith<$Res> {
  _$EvaluationContextCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? assessmentId = null,
    Object? studentMastery = null,
    Object? previousMisconceptions = null,
    Object? isPractice = null,
  }) {
    return _then(_value.copyWith(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentMastery: null == studentMastery
          ? _value.studentMastery
          : studentMastery // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      previousMisconceptions: null == previousMisconceptions
          ? _value.previousMisconceptions
          : previousMisconceptions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      isPractice: null == isPractice
          ? _value.isPractice
          : isPractice // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$EvaluationContextImplCopyWith<$Res>
    implements $EvaluationContextCopyWith<$Res> {
  factory _$$EvaluationContextImplCopyWith(_$EvaluationContextImpl value,
          $Res Function(_$EvaluationContextImpl) then) =
      __$$EvaluationContextImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String studentId,
      String assessmentId,
      Map<String, double> studentMastery,
      List<String> previousMisconceptions,
      bool isPractice});
}

/// @nodoc
class __$$EvaluationContextImplCopyWithImpl<$Res>
    extends _$EvaluationContextCopyWithImpl<$Res, _$EvaluationContextImpl>
    implements _$$EvaluationContextImplCopyWith<$Res> {
  __$$EvaluationContextImplCopyWithImpl(_$EvaluationContextImpl _value,
      $Res Function(_$EvaluationContextImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? assessmentId = null,
    Object? studentMastery = null,
    Object? previousMisconceptions = null,
    Object? isPractice = null,
  }) {
    return _then(_$EvaluationContextImpl(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentMastery: null == studentMastery
          ? _value._studentMastery
          : studentMastery // ignore: cast_nullable_to_non_nullable
              as Map<String, double>,
      previousMisconceptions: null == previousMisconceptions
          ? _value._previousMisconceptions
          : previousMisconceptions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      isPractice: null == isPractice
          ? _value.isPractice
          : isPractice // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$EvaluationContextImpl implements _EvaluationContext {
  const _$EvaluationContextImpl(
      {required this.studentId,
      required this.assessmentId,
      required final Map<String, double> studentMastery,
      required final List<String> previousMisconceptions,
      this.isPractice = false})
      : _studentMastery = studentMastery,
        _previousMisconceptions = previousMisconceptions;

  factory _$EvaluationContextImpl.fromJson(Map<String, dynamic> json) =>
      _$$EvaluationContextImplFromJson(json);

  @override
  final String studentId;
  @override
  final String assessmentId;
  final Map<String, double> _studentMastery;
  @override
  Map<String, double> get studentMastery {
    if (_studentMastery is EqualUnmodifiableMapView) return _studentMastery;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_studentMastery);
  }

  final List<String> _previousMisconceptions;
  @override
  List<String> get previousMisconceptions {
    if (_previousMisconceptions is EqualUnmodifiableListView)
      return _previousMisconceptions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_previousMisconceptions);
  }

  @override
  @JsonKey()
  final bool isPractice;

  @override
  String toString() {
    return 'EvaluationContext(studentId: $studentId, assessmentId: $assessmentId, studentMastery: $studentMastery, previousMisconceptions: $previousMisconceptions, isPractice: $isPractice)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$EvaluationContextImpl &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            const DeepCollectionEquality()
                .equals(other._studentMastery, _studentMastery) &&
            const DeepCollectionEquality().equals(
                other._previousMisconceptions, _previousMisconceptions) &&
            (identical(other.isPractice, isPractice) ||
                other.isPractice == isPractice));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      studentId,
      assessmentId,
      const DeepCollectionEquality().hash(_studentMastery),
      const DeepCollectionEquality().hash(_previousMisconceptions),
      isPractice);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$EvaluationContextImplCopyWith<_$EvaluationContextImpl> get copyWith =>
      __$$EvaluationContextImplCopyWithImpl<_$EvaluationContextImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$EvaluationContextImplToJson(
      this,
    );
  }
}

abstract class _EvaluationContext implements EvaluationContext {
  const factory _EvaluationContext(
      {required final String studentId,
      required final String assessmentId,
      required final Map<String, double> studentMastery,
      required final List<String> previousMisconceptions,
      final bool isPractice}) = _$EvaluationContextImpl;

  factory _EvaluationContext.fromJson(Map<String, dynamic> json) =
      _$EvaluationContextImpl.fromJson;

  @override
  String get studentId;
  @override
  String get assessmentId;
  @override
  Map<String, double> get studentMastery;
  @override
  List<String> get previousMisconceptions;
  @override
  bool get isPractice;
  @override
  @JsonKey(ignore: true)
  _$$EvaluationContextImplCopyWith<_$EvaluationContextImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

TeacherReviewRequest _$TeacherReviewRequestFromJson(Map<String, dynamic> json) {
  return _TeacherReviewRequest.fromJson(json);
}

/// @nodoc
mixin _$TeacherReviewRequest {
  String get evaluationId => throw _privateConstructorUsedError;
  String get teacherId => throw _privateConstructorUsedError;
  int? get adjustedMarks => throw _privateConstructorUsedError;
  EvaluationVerdict? get adjustedVerdict => throw _privateConstructorUsedError;
  String? get comment => throw _privateConstructorUsedError;
  bool get approved => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $TeacherReviewRequestCopyWith<TeacherReviewRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TeacherReviewRequestCopyWith<$Res> {
  factory $TeacherReviewRequestCopyWith(TeacherReviewRequest value,
          $Res Function(TeacherReviewRequest) then) =
      _$TeacherReviewRequestCopyWithImpl<$Res, TeacherReviewRequest>;
  @useResult
  $Res call(
      {String evaluationId,
      String teacherId,
      int? adjustedMarks,
      EvaluationVerdict? adjustedVerdict,
      String? comment,
      bool approved});
}

/// @nodoc
class _$TeacherReviewRequestCopyWithImpl<$Res,
        $Val extends TeacherReviewRequest>
    implements $TeacherReviewRequestCopyWith<$Res> {
  _$TeacherReviewRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? evaluationId = null,
    Object? teacherId = null,
    Object? adjustedMarks = freezed,
    Object? adjustedVerdict = freezed,
    Object? comment = freezed,
    Object? approved = null,
  }) {
    return _then(_value.copyWith(
      evaluationId: null == evaluationId
          ? _value.evaluationId
          : evaluationId // ignore: cast_nullable_to_non_nullable
              as String,
      teacherId: null == teacherId
          ? _value.teacherId
          : teacherId // ignore: cast_nullable_to_non_nullable
              as String,
      adjustedMarks: freezed == adjustedMarks
          ? _value.adjustedMarks
          : adjustedMarks // ignore: cast_nullable_to_non_nullable
              as int?,
      adjustedVerdict: freezed == adjustedVerdict
          ? _value.adjustedVerdict
          : adjustedVerdict // ignore: cast_nullable_to_non_nullable
              as EvaluationVerdict?,
      comment: freezed == comment
          ? _value.comment
          : comment // ignore: cast_nullable_to_non_nullable
              as String?,
      approved: null == approved
          ? _value.approved
          : approved // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TeacherReviewRequestImplCopyWith<$Res>
    implements $TeacherReviewRequestCopyWith<$Res> {
  factory _$$TeacherReviewRequestImplCopyWith(_$TeacherReviewRequestImpl value,
          $Res Function(_$TeacherReviewRequestImpl) then) =
      __$$TeacherReviewRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String evaluationId,
      String teacherId,
      int? adjustedMarks,
      EvaluationVerdict? adjustedVerdict,
      String? comment,
      bool approved});
}

/// @nodoc
class __$$TeacherReviewRequestImplCopyWithImpl<$Res>
    extends _$TeacherReviewRequestCopyWithImpl<$Res, _$TeacherReviewRequestImpl>
    implements _$$TeacherReviewRequestImplCopyWith<$Res> {
  __$$TeacherReviewRequestImplCopyWithImpl(_$TeacherReviewRequestImpl _value,
      $Res Function(_$TeacherReviewRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? evaluationId = null,
    Object? teacherId = null,
    Object? adjustedMarks = freezed,
    Object? adjustedVerdict = freezed,
    Object? comment = freezed,
    Object? approved = null,
  }) {
    return _then(_$TeacherReviewRequestImpl(
      evaluationId: null == evaluationId
          ? _value.evaluationId
          : evaluationId // ignore: cast_nullable_to_non_nullable
              as String,
      teacherId: null == teacherId
          ? _value.teacherId
          : teacherId // ignore: cast_nullable_to_non_nullable
              as String,
      adjustedMarks: freezed == adjustedMarks
          ? _value.adjustedMarks
          : adjustedMarks // ignore: cast_nullable_to_non_nullable
              as int?,
      adjustedVerdict: freezed == adjustedVerdict
          ? _value.adjustedVerdict
          : adjustedVerdict // ignore: cast_nullable_to_non_nullable
              as EvaluationVerdict?,
      comment: freezed == comment
          ? _value.comment
          : comment // ignore: cast_nullable_to_non_nullable
              as String?,
      approved: null == approved
          ? _value.approved
          : approved // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TeacherReviewRequestImpl implements _TeacherReviewRequest {
  const _$TeacherReviewRequestImpl(
      {required this.evaluationId,
      required this.teacherId,
      this.adjustedMarks,
      this.adjustedVerdict,
      this.comment,
      required this.approved});

  factory _$TeacherReviewRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$TeacherReviewRequestImplFromJson(json);

  @override
  final String evaluationId;
  @override
  final String teacherId;
  @override
  final int? adjustedMarks;
  @override
  final EvaluationVerdict? adjustedVerdict;
  @override
  final String? comment;
  @override
  final bool approved;

  @override
  String toString() {
    return 'TeacherReviewRequest(evaluationId: $evaluationId, teacherId: $teacherId, adjustedMarks: $adjustedMarks, adjustedVerdict: $adjustedVerdict, comment: $comment, approved: $approved)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TeacherReviewRequestImpl &&
            (identical(other.evaluationId, evaluationId) ||
                other.evaluationId == evaluationId) &&
            (identical(other.teacherId, teacherId) ||
                other.teacherId == teacherId) &&
            (identical(other.adjustedMarks, adjustedMarks) ||
                other.adjustedMarks == adjustedMarks) &&
            (identical(other.adjustedVerdict, adjustedVerdict) ||
                other.adjustedVerdict == adjustedVerdict) &&
            (identical(other.comment, comment) || other.comment == comment) &&
            (identical(other.approved, approved) ||
                other.approved == approved));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, evaluationId, teacherId,
      adjustedMarks, adjustedVerdict, comment, approved);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$TeacherReviewRequestImplCopyWith<_$TeacherReviewRequestImpl>
      get copyWith =>
          __$$TeacherReviewRequestImplCopyWithImpl<_$TeacherReviewRequestImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TeacherReviewRequestImplToJson(
      this,
    );
  }
}

abstract class _TeacherReviewRequest implements TeacherReviewRequest {
  const factory _TeacherReviewRequest(
      {required final String evaluationId,
      required final String teacherId,
      final int? adjustedMarks,
      final EvaluationVerdict? adjustedVerdict,
      final String? comment,
      required final bool approved}) = _$TeacherReviewRequestImpl;

  factory _TeacherReviewRequest.fromJson(Map<String, dynamic> json) =
      _$TeacherReviewRequestImpl.fromJson;

  @override
  String get evaluationId;
  @override
  String get teacherId;
  @override
  int? get adjustedMarks;
  @override
  EvaluationVerdict? get adjustedVerdict;
  @override
  String? get comment;
  @override
  bool get approved;
  @override
  @JsonKey(ignore: true)
  _$$TeacherReviewRequestImplCopyWith<_$TeacherReviewRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

MasteryAttempt _$MasteryAttemptFromJson(Map<String, dynamic> json) {
  return _MasteryAttempt.fromJson(json);
}

/// @nodoc
mixin _$MasteryAttempt {
  String get studentId => throw _privateConstructorUsedError;
  String get conceptId => throw _privateConstructorUsedError;
  bool get correct => throw _privateConstructorUsedError;
  double get confidence => throw _privateConstructorUsedError;
  int get timeSpentSeconds => throw _privateConstructorUsedError;
  DateTime get attemptedAt => throw _privateConstructorUsedError;
  String get source => throw _privateConstructorUsedError;
  String? get assessmentId => throw _privateConstructorUsedError;
  String? get questionId => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MasteryAttemptCopyWith<MasteryAttempt> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MasteryAttemptCopyWith<$Res> {
  factory $MasteryAttemptCopyWith(
          MasteryAttempt value, $Res Function(MasteryAttempt) then) =
      _$MasteryAttemptCopyWithImpl<$Res, MasteryAttempt>;
  @useResult
  $Res call(
      {String studentId,
      String conceptId,
      bool correct,
      double confidence,
      int timeSpentSeconds,
      DateTime attemptedAt,
      String source,
      String? assessmentId,
      String? questionId});
}

/// @nodoc
class _$MasteryAttemptCopyWithImpl<$Res, $Val extends MasteryAttempt>
    implements $MasteryAttemptCopyWith<$Res> {
  _$MasteryAttemptCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? conceptId = null,
    Object? correct = null,
    Object? confidence = null,
    Object? timeSpentSeconds = null,
    Object? attemptedAt = null,
    Object? source = null,
    Object? assessmentId = freezed,
    Object? questionId = freezed,
  }) {
    return _then(_value.copyWith(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptId: null == conceptId
          ? _value.conceptId
          : conceptId // ignore: cast_nullable_to_non_nullable
              as String,
      correct: null == correct
          ? _value.correct
          : correct // ignore: cast_nullable_to_non_nullable
              as bool,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      timeSpentSeconds: null == timeSpentSeconds
          ? _value.timeSpentSeconds
          : timeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      attemptedAt: null == attemptedAt
          ? _value.attemptedAt
          : attemptedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: freezed == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String?,
      questionId: freezed == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MasteryAttemptImplCopyWith<$Res>
    implements $MasteryAttemptCopyWith<$Res> {
  factory _$$MasteryAttemptImplCopyWith(_$MasteryAttemptImpl value,
          $Res Function(_$MasteryAttemptImpl) then) =
      __$$MasteryAttemptImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String studentId,
      String conceptId,
      bool correct,
      double confidence,
      int timeSpentSeconds,
      DateTime attemptedAt,
      String source,
      String? assessmentId,
      String? questionId});
}

/// @nodoc
class __$$MasteryAttemptImplCopyWithImpl<$Res>
    extends _$MasteryAttemptCopyWithImpl<$Res, _$MasteryAttemptImpl>
    implements _$$MasteryAttemptImplCopyWith<$Res> {
  __$$MasteryAttemptImplCopyWithImpl(
      _$MasteryAttemptImpl _value, $Res Function(_$MasteryAttemptImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? conceptId = null,
    Object? correct = null,
    Object? confidence = null,
    Object? timeSpentSeconds = null,
    Object? attemptedAt = null,
    Object? source = null,
    Object? assessmentId = freezed,
    Object? questionId = freezed,
  }) {
    return _then(_$MasteryAttemptImpl(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptId: null == conceptId
          ? _value.conceptId
          : conceptId // ignore: cast_nullable_to_non_nullable
              as String,
      correct: null == correct
          ? _value.correct
          : correct // ignore: cast_nullable_to_non_nullable
              as bool,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      timeSpentSeconds: null == timeSpentSeconds
          ? _value.timeSpentSeconds
          : timeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      attemptedAt: null == attemptedAt
          ? _value.attemptedAt
          : attemptedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: freezed == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String?,
      questionId: freezed == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MasteryAttemptImpl implements _MasteryAttempt {
  const _$MasteryAttemptImpl(
      {required this.studentId,
      required this.conceptId,
      required this.correct,
      required this.confidence,
      required this.timeSpentSeconds,
      required this.attemptedAt,
      required this.source,
      this.assessmentId,
      this.questionId});

  factory _$MasteryAttemptImpl.fromJson(Map<String, dynamic> json) =>
      _$$MasteryAttemptImplFromJson(json);

  @override
  final String studentId;
  @override
  final String conceptId;
  @override
  final bool correct;
  @override
  final double confidence;
  @override
  final int timeSpentSeconds;
  @override
  final DateTime attemptedAt;
  @override
  final String source;
  @override
  final String? assessmentId;
  @override
  final String? questionId;

  @override
  String toString() {
    return 'MasteryAttempt(studentId: $studentId, conceptId: $conceptId, correct: $correct, confidence: $confidence, timeSpentSeconds: $timeSpentSeconds, attemptedAt: $attemptedAt, source: $source, assessmentId: $assessmentId, questionId: $questionId)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MasteryAttemptImpl &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.conceptId, conceptId) ||
                other.conceptId == conceptId) &&
            (identical(other.correct, correct) || other.correct == correct) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.timeSpentSeconds, timeSpentSeconds) ||
                other.timeSpentSeconds == timeSpentSeconds) &&
            (identical(other.attemptedAt, attemptedAt) ||
                other.attemptedAt == attemptedAt) &&
            (identical(other.source, source) || other.source == source) &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      studentId,
      conceptId,
      correct,
      confidence,
      timeSpentSeconds,
      attemptedAt,
      source,
      assessmentId,
      questionId);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MasteryAttemptImplCopyWith<_$MasteryAttemptImpl> get copyWith =>
      __$$MasteryAttemptImplCopyWithImpl<_$MasteryAttemptImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MasteryAttemptImplToJson(
      this,
    );
  }
}

abstract class _MasteryAttempt implements MasteryAttempt {
  const factory _MasteryAttempt(
      {required final String studentId,
      required final String conceptId,
      required final bool correct,
      required final double confidence,
      required final int timeSpentSeconds,
      required final DateTime attemptedAt,
      required final String source,
      final String? assessmentId,
      final String? questionId}) = _$MasteryAttemptImpl;

  factory _MasteryAttempt.fromJson(Map<String, dynamic> json) =
      _$MasteryAttemptImpl.fromJson;

  @override
  String get studentId;
  @override
  String get conceptId;
  @override
  bool get correct;
  @override
  double get confidence;
  @override
  int get timeSpentSeconds;
  @override
  DateTime get attemptedAt;
  @override
  String get source;
  @override
  String? get assessmentId;
  @override
  String? get questionId;
  @override
  @JsonKey(ignore: true)
  _$$MasteryAttemptImplCopyWith<_$MasteryAttemptImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PracticeRequest _$PracticeRequestFromJson(Map<String, dynamic> json) {
  return _PracticeRequest.fromJson(json);
}

/// @nodoc
mixin _$PracticeRequest {
  String get studentId => throw _privateConstructorUsedError;
  List<String> get conceptIds => throw _privateConstructorUsedError;
  PracticeType get type => throw _privateConstructorUsedError;
  int get questionCount => throw _privateConstructorUsedError;
  int get durationMinutes => throw _privateConstructorUsedError;
  Map<String, dynamic>? get options => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeRequestCopyWith<PracticeRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeRequestCopyWith<$Res> {
  factory $PracticeRequestCopyWith(
          PracticeRequest value, $Res Function(PracticeRequest) then) =
      _$PracticeRequestCopyWithImpl<$Res, PracticeRequest>;
  @useResult
  $Res call(
      {String studentId,
      List<String> conceptIds,
      PracticeType type,
      int questionCount,
      int durationMinutes,
      Map<String, dynamic>? options});
}

/// @nodoc
class _$PracticeRequestCopyWithImpl<$Res, $Val extends PracticeRequest>
    implements $PracticeRequestCopyWith<$Res> {
  _$PracticeRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? conceptIds = null,
    Object? type = null,
    Object? questionCount = null,
    Object? durationMinutes = null,
    Object? options = freezed,
  }) {
    return _then(_value.copyWith(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptIds: null == conceptIds
          ? _value.conceptIds
          : conceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as PracticeType,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      options: freezed == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PracticeRequestImplCopyWith<$Res>
    implements $PracticeRequestCopyWith<$Res> {
  factory _$$PracticeRequestImplCopyWith(_$PracticeRequestImpl value,
          $Res Function(_$PracticeRequestImpl) then) =
      __$$PracticeRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String studentId,
      List<String> conceptIds,
      PracticeType type,
      int questionCount,
      int durationMinutes,
      Map<String, dynamic>? options});
}

/// @nodoc
class __$$PracticeRequestImplCopyWithImpl<$Res>
    extends _$PracticeRequestCopyWithImpl<$Res, _$PracticeRequestImpl>
    implements _$$PracticeRequestImplCopyWith<$Res> {
  __$$PracticeRequestImplCopyWithImpl(
      _$PracticeRequestImpl _value, $Res Function(_$PracticeRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? studentId = null,
    Object? conceptIds = null,
    Object? type = null,
    Object? questionCount = null,
    Object? durationMinutes = null,
    Object? options = freezed,
  }) {
    return _then(_$PracticeRequestImpl(
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptIds: null == conceptIds
          ? _value._conceptIds
          : conceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as PracticeType,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      options: freezed == options
          ? _value._options
          : options // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeRequestImpl implements _PracticeRequest {
  const _$PracticeRequestImpl(
      {required this.studentId,
      required final List<String> conceptIds,
      required this.type,
      required this.questionCount,
      required this.durationMinutes,
      final Map<String, dynamic>? options})
      : _conceptIds = conceptIds,
        _options = options;

  factory _$PracticeRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeRequestImplFromJson(json);

  @override
  final String studentId;
  final List<String> _conceptIds;
  @override
  List<String> get conceptIds {
    if (_conceptIds is EqualUnmodifiableListView) return _conceptIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_conceptIds);
  }

  @override
  final PracticeType type;
  @override
  final int questionCount;
  @override
  final int durationMinutes;
  final Map<String, dynamic>? _options;
  @override
  Map<String, dynamic>? get options {
    final value = _options;
    if (value == null) return null;
    if (_options is EqualUnmodifiableMapView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'PracticeRequest(studentId: $studentId, conceptIds: $conceptIds, type: $type, questionCount: $questionCount, durationMinutes: $durationMinutes, options: $options)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeRequestImpl &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            const DeepCollectionEquality()
                .equals(other._conceptIds, _conceptIds) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.questionCount, questionCount) ||
                other.questionCount == questionCount) &&
            (identical(other.durationMinutes, durationMinutes) ||
                other.durationMinutes == durationMinutes) &&
            const DeepCollectionEquality().equals(other._options, _options));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      studentId,
      const DeepCollectionEquality().hash(_conceptIds),
      type,
      questionCount,
      durationMinutes,
      const DeepCollectionEquality().hash(_options));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeRequestImplCopyWith<_$PracticeRequestImpl> get copyWith =>
      __$$PracticeRequestImplCopyWithImpl<_$PracticeRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeRequestImplToJson(
      this,
    );
  }
}

abstract class _PracticeRequest implements PracticeRequest {
  const factory _PracticeRequest(
      {required final String studentId,
      required final List<String> conceptIds,
      required final PracticeType type,
      required final int questionCount,
      required final int durationMinutes,
      final Map<String, dynamic>? options}) = _$PracticeRequestImpl;

  factory _PracticeRequest.fromJson(Map<String, dynamic> json) =
      _$PracticeRequestImpl.fromJson;

  @override
  String get studentId;
  @override
  List<String> get conceptIds;
  @override
  PracticeType get type;
  @override
  int get questionCount;
  @override
  int get durationMinutes;
  @override
  Map<String, dynamic>? get options;
  @override
  @JsonKey(ignore: true)
  _$$PracticeRequestImplCopyWith<_$PracticeRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PracticeSession _$PracticeSessionFromJson(Map<String, dynamic> json) {
  return _PracticeSession.fromJson(json);
}

/// @nodoc
mixin _$PracticeSession {
  String get id => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  List<String> get conceptIds => throw _privateConstructorUsedError;
  PracticeType get type => throw _privateConstructorUsedError;
  int get questionCount => throw _privateConstructorUsedError;
  int get durationMinutes => throw _privateConstructorUsedError;
  List<PracticeQuestion> get questions => throw _privateConstructorUsedError;
  PracticeStatus get status => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  DateTime? get startedAt => throw _privateConstructorUsedError;
  DateTime? get completedAt => throw _privateConstructorUsedError;
  PracticeResult? get result => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeSessionCopyWith<PracticeSession> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeSessionCopyWith<$Res> {
  factory $PracticeSessionCopyWith(
          PracticeSession value, $Res Function(PracticeSession) then) =
      _$PracticeSessionCopyWithImpl<$Res, PracticeSession>;
  @useResult
  $Res call(
      {String id,
      String studentId,
      List<String> conceptIds,
      PracticeType type,
      int questionCount,
      int durationMinutes,
      List<PracticeQuestion> questions,
      PracticeStatus status,
      DateTime createdAt,
      DateTime? startedAt,
      DateTime? completedAt,
      PracticeResult? result});

  $PracticeResultCopyWith<$Res>? get result;
}

/// @nodoc
class _$PracticeSessionCopyWithImpl<$Res, $Val extends PracticeSession>
    implements $PracticeSessionCopyWith<$Res> {
  _$PracticeSessionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? studentId = null,
    Object? conceptIds = null,
    Object? type = null,
    Object? questionCount = null,
    Object? durationMinutes = null,
    Object? questions = null,
    Object? status = null,
    Object? createdAt = null,
    Object? startedAt = freezed,
    Object? completedAt = freezed,
    Object? result = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptIds: null == conceptIds
          ? _value.conceptIds
          : conceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as PracticeType,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      questions: null == questions
          ? _value.questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<PracticeQuestion>,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as PracticeStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      startedAt: freezed == startedAt
          ? _value.startedAt
          : startedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      completedAt: freezed == completedAt
          ? _value.completedAt
          : completedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as PracticeResult?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $PracticeResultCopyWith<$Res>? get result {
    if (_value.result == null) {
      return null;
    }

    return $PracticeResultCopyWith<$Res>(_value.result!, (value) {
      return _then(_value.copyWith(result: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PracticeSessionImplCopyWith<$Res>
    implements $PracticeSessionCopyWith<$Res> {
  factory _$$PracticeSessionImplCopyWith(_$PracticeSessionImpl value,
          $Res Function(_$PracticeSessionImpl) then) =
      __$$PracticeSessionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String studentId,
      List<String> conceptIds,
      PracticeType type,
      int questionCount,
      int durationMinutes,
      List<PracticeQuestion> questions,
      PracticeStatus status,
      DateTime createdAt,
      DateTime? startedAt,
      DateTime? completedAt,
      PracticeResult? result});

  @override
  $PracticeResultCopyWith<$Res>? get result;
}

/// @nodoc
class __$$PracticeSessionImplCopyWithImpl<$Res>
    extends _$PracticeSessionCopyWithImpl<$Res, _$PracticeSessionImpl>
    implements _$$PracticeSessionImplCopyWith<$Res> {
  __$$PracticeSessionImplCopyWithImpl(
      _$PracticeSessionImpl _value, $Res Function(_$PracticeSessionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? studentId = null,
    Object? conceptIds = null,
    Object? type = null,
    Object? questionCount = null,
    Object? durationMinutes = null,
    Object? questions = null,
    Object? status = null,
    Object? createdAt = null,
    Object? startedAt = freezed,
    Object? completedAt = freezed,
    Object? result = freezed,
  }) {
    return _then(_$PracticeSessionImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptIds: null == conceptIds
          ? _value._conceptIds
          : conceptIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as PracticeType,
      questionCount: null == questionCount
          ? _value.questionCount
          : questionCount // ignore: cast_nullable_to_non_nullable
              as int,
      durationMinutes: null == durationMinutes
          ? _value.durationMinutes
          : durationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      questions: null == questions
          ? _value._questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<PracticeQuestion>,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as PracticeStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      startedAt: freezed == startedAt
          ? _value.startedAt
          : startedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      completedAt: freezed == completedAt
          ? _value.completedAt
          : completedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as PracticeResult?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeSessionImpl implements _PracticeSession {
  const _$PracticeSessionImpl(
      {required this.id,
      required this.studentId,
      required final List<String> conceptIds,
      required this.type,
      required this.questionCount,
      required this.durationMinutes,
      required final List<PracticeQuestion> questions,
      required this.status,
      required this.createdAt,
      this.startedAt,
      this.completedAt,
      this.result})
      : _conceptIds = conceptIds,
        _questions = questions;

  factory _$PracticeSessionImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeSessionImplFromJson(json);

  @override
  final String id;
  @override
  final String studentId;
  final List<String> _conceptIds;
  @override
  List<String> get conceptIds {
    if (_conceptIds is EqualUnmodifiableListView) return _conceptIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_conceptIds);
  }

  @override
  final PracticeType type;
  @override
  final int questionCount;
  @override
  final int durationMinutes;
  final List<PracticeQuestion> _questions;
  @override
  List<PracticeQuestion> get questions {
    if (_questions is EqualUnmodifiableListView) return _questions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questions);
  }

  @override
  final PracticeStatus status;
  @override
  final DateTime createdAt;
  @override
  final DateTime? startedAt;
  @override
  final DateTime? completedAt;
  @override
  final PracticeResult? result;

  @override
  String toString() {
    return 'PracticeSession(id: $id, studentId: $studentId, conceptIds: $conceptIds, type: $type, questionCount: $questionCount, durationMinutes: $durationMinutes, questions: $questions, status: $status, createdAt: $createdAt, startedAt: $startedAt, completedAt: $completedAt, result: $result)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeSessionImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            const DeepCollectionEquality()
                .equals(other._conceptIds, _conceptIds) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.questionCount, questionCount) ||
                other.questionCount == questionCount) &&
            (identical(other.durationMinutes, durationMinutes) ||
                other.durationMinutes == durationMinutes) &&
            const DeepCollectionEquality()
                .equals(other._questions, _questions) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.startedAt, startedAt) ||
                other.startedAt == startedAt) &&
            (identical(other.completedAt, completedAt) ||
                other.completedAt == completedAt) &&
            (identical(other.result, result) || other.result == result));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      studentId,
      const DeepCollectionEquality().hash(_conceptIds),
      type,
      questionCount,
      durationMinutes,
      const DeepCollectionEquality().hash(_questions),
      status,
      createdAt,
      startedAt,
      completedAt,
      result);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeSessionImplCopyWith<_$PracticeSessionImpl> get copyWith =>
      __$$PracticeSessionImplCopyWithImpl<_$PracticeSessionImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeSessionImplToJson(
      this,
    );
  }
}

abstract class _PracticeSession implements PracticeSession {
  const factory _PracticeSession(
      {required final String id,
      required final String studentId,
      required final List<String> conceptIds,
      required final PracticeType type,
      required final int questionCount,
      required final int durationMinutes,
      required final List<PracticeQuestion> questions,
      required final PracticeStatus status,
      required final DateTime createdAt,
      final DateTime? startedAt,
      final DateTime? completedAt,
      final PracticeResult? result}) = _$PracticeSessionImpl;

  factory _PracticeSession.fromJson(Map<String, dynamic> json) =
      _$PracticeSessionImpl.fromJson;

  @override
  String get id;
  @override
  String get studentId;
  @override
  List<String> get conceptIds;
  @override
  PracticeType get type;
  @override
  int get questionCount;
  @override
  int get durationMinutes;
  @override
  List<PracticeQuestion> get questions;
  @override
  PracticeStatus get status;
  @override
  DateTime get createdAt;
  @override
  DateTime? get startedAt;
  @override
  DateTime? get completedAt;
  @override
  PracticeResult? get result;
  @override
  @JsonKey(ignore: true)
  _$$PracticeSessionImplCopyWith<_$PracticeSessionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PracticeQuestion _$PracticeQuestionFromJson(Map<String, dynamic> json) {
  return _PracticeQuestion.fromJson(json);
}

/// @nodoc
mixin _$PracticeQuestion {
  String get questionId => throw _privateConstructorUsedError;
  int get displayNumber => throw _privateConstructorUsedError;
  String get stem => throw _privateConstructorUsedError;
  String get stemLatex => throw _privateConstructorUsedError;
  List<QuestionPart> get parts => throw _privateConstructorUsedError;
  int get marks => throw _privateConstructorUsedError;
  String? get hint => throw _privateConstructorUsedError;
  String? get explanation => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeQuestionCopyWith<PracticeQuestion> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeQuestionCopyWith<$Res> {
  factory $PracticeQuestionCopyWith(
          PracticeQuestion value, $Res Function(PracticeQuestion) then) =
      _$PracticeQuestionCopyWithImpl<$Res, PracticeQuestion>;
  @useResult
  $Res call(
      {String questionId,
      int displayNumber,
      String stem,
      String stemLatex,
      List<QuestionPart> parts,
      int marks,
      String? hint,
      String? explanation});
}

/// @nodoc
class _$PracticeQuestionCopyWithImpl<$Res, $Val extends PracticeQuestion>
    implements $PracticeQuestionCopyWith<$Res> {
  _$PracticeQuestionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? displayNumber = null,
    Object? stem = null,
    Object? stemLatex = null,
    Object? parts = null,
    Object? marks = null,
    Object? hint = freezed,
    Object? explanation = freezed,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      displayNumber: null == displayNumber
          ? _value.displayNumber
          : displayNumber // ignore: cast_nullable_to_non_nullable
              as int,
      stem: null == stem
          ? _value.stem
          : stem // ignore: cast_nullable_to_non_nullable
              as String,
      stemLatex: null == stemLatex
          ? _value.stemLatex
          : stemLatex // ignore: cast_nullable_to_non_nullable
              as String,
      parts: null == parts
          ? _value.parts
          : parts // ignore: cast_nullable_to_non_nullable
              as List<QuestionPart>,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      hint: freezed == hint
          ? _value.hint
          : hint // ignore: cast_nullable_to_non_nullable
              as String?,
      explanation: freezed == explanation
          ? _value.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PracticeQuestionImplCopyWith<$Res>
    implements $PracticeQuestionCopyWith<$Res> {
  factory _$$PracticeQuestionImplCopyWith(_$PracticeQuestionImpl value,
          $Res Function(_$PracticeQuestionImpl) then) =
      __$$PracticeQuestionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      int displayNumber,
      String stem,
      String stemLatex,
      List<QuestionPart> parts,
      int marks,
      String? hint,
      String? explanation});
}

/// @nodoc
class __$$PracticeQuestionImplCopyWithImpl<$Res>
    extends _$PracticeQuestionCopyWithImpl<$Res, _$PracticeQuestionImpl>
    implements _$$PracticeQuestionImplCopyWith<$Res> {
  __$$PracticeQuestionImplCopyWithImpl(_$PracticeQuestionImpl _value,
      $Res Function(_$PracticeQuestionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? displayNumber = null,
    Object? stem = null,
    Object? stemLatex = null,
    Object? parts = null,
    Object? marks = null,
    Object? hint = freezed,
    Object? explanation = freezed,
  }) {
    return _then(_$PracticeQuestionImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      displayNumber: null == displayNumber
          ? _value.displayNumber
          : displayNumber // ignore: cast_nullable_to_non_nullable
              as int,
      stem: null == stem
          ? _value.stem
          : stem // ignore: cast_nullable_to_non_nullable
              as String,
      stemLatex: null == stemLatex
          ? _value.stemLatex
          : stemLatex // ignore: cast_nullable_to_non_nullable
              as String,
      parts: null == parts
          ? _value._parts
          : parts // ignore: cast_nullable_to_non_nullable
              as List<QuestionPart>,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      hint: freezed == hint
          ? _value.hint
          : hint // ignore: cast_nullable_to_non_nullable
              as String?,
      explanation: freezed == explanation
          ? _value.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeQuestionImpl implements _PracticeQuestion {
  const _$PracticeQuestionImpl(
      {required this.questionId,
      required this.displayNumber,
      required this.stem,
      required this.stemLatex,
      required final List<QuestionPart> parts,
      required this.marks,
      this.hint,
      this.explanation})
      : _parts = parts;

  factory _$PracticeQuestionImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeQuestionImplFromJson(json);

  @override
  final String questionId;
  @override
  final int displayNumber;
  @override
  final String stem;
  @override
  final String stemLatex;
  final List<QuestionPart> _parts;
  @override
  List<QuestionPart> get parts {
    if (_parts is EqualUnmodifiableListView) return _parts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_parts);
  }

  @override
  final int marks;
  @override
  final String? hint;
  @override
  final String? explanation;

  @override
  String toString() {
    return 'PracticeQuestion(questionId: $questionId, displayNumber: $displayNumber, stem: $stem, stemLatex: $stemLatex, parts: $parts, marks: $marks, hint: $hint, explanation: $explanation)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeQuestionImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.displayNumber, displayNumber) ||
                other.displayNumber == displayNumber) &&
            (identical(other.stem, stem) || other.stem == stem) &&
            (identical(other.stemLatex, stemLatex) ||
                other.stemLatex == stemLatex) &&
            const DeepCollectionEquality().equals(other._parts, _parts) &&
            (identical(other.marks, marks) || other.marks == marks) &&
            (identical(other.hint, hint) || other.hint == hint) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      displayNumber,
      stem,
      stemLatex,
      const DeepCollectionEquality().hash(_parts),
      marks,
      hint,
      explanation);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeQuestionImplCopyWith<_$PracticeQuestionImpl> get copyWith =>
      __$$PracticeQuestionImplCopyWithImpl<_$PracticeQuestionImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeQuestionImplToJson(
      this,
    );
  }
}

abstract class _PracticeQuestion implements PracticeQuestion {
  const factory _PracticeQuestion(
      {required final String questionId,
      required final int displayNumber,
      required final String stem,
      required final String stemLatex,
      required final List<QuestionPart> parts,
      required final int marks,
      final String? hint,
      final String? explanation}) = _$PracticeQuestionImpl;

  factory _PracticeQuestion.fromJson(Map<String, dynamic> json) =
      _$PracticeQuestionImpl.fromJson;

  @override
  String get questionId;
  @override
  int get displayNumber;
  @override
  String get stem;
  @override
  String get stemLatex;
  @override
  List<QuestionPart> get parts;
  @override
  int get marks;
  @override
  String? get hint;
  @override
  String? get explanation;
  @override
  @JsonKey(ignore: true)
  _$$PracticeQuestionImplCopyWith<_$PracticeQuestionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PracticeSubmission _$PracticeSubmissionFromJson(Map<String, dynamic> json) {
  return _PracticeSubmission.fromJson(json);
}

/// @nodoc
mixin _$PracticeSubmission {
  String get sessionId => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  List<PracticeAnswer> get answers => throw _privateConstructorUsedError;
  Duration get timeSpent => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeSubmissionCopyWith<PracticeSubmission> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeSubmissionCopyWith<$Res> {
  factory $PracticeSubmissionCopyWith(
          PracticeSubmission value, $Res Function(PracticeSubmission) then) =
      _$PracticeSubmissionCopyWithImpl<$Res, PracticeSubmission>;
  @useResult
  $Res call(
      {String sessionId,
      String studentId,
      List<PracticeAnswer> answers,
      Duration timeSpent});
}

/// @nodoc
class _$PracticeSubmissionCopyWithImpl<$Res, $Val extends PracticeSubmission>
    implements $PracticeSubmissionCopyWith<$Res> {
  _$PracticeSubmissionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? studentId = null,
    Object? answers = null,
    Object? timeSpent = null,
  }) {
    return _then(_value.copyWith(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      answers: null == answers
          ? _value.answers
          : answers // ignore: cast_nullable_to_non_nullable
              as List<PracticeAnswer>,
      timeSpent: null == timeSpent
          ? _value.timeSpent
          : timeSpent // ignore: cast_nullable_to_non_nullable
              as Duration,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PracticeSubmissionImplCopyWith<$Res>
    implements $PracticeSubmissionCopyWith<$Res> {
  factory _$$PracticeSubmissionImplCopyWith(_$PracticeSubmissionImpl value,
          $Res Function(_$PracticeSubmissionImpl) then) =
      __$$PracticeSubmissionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String sessionId,
      String studentId,
      List<PracticeAnswer> answers,
      Duration timeSpent});
}

/// @nodoc
class __$$PracticeSubmissionImplCopyWithImpl<$Res>
    extends _$PracticeSubmissionCopyWithImpl<$Res, _$PracticeSubmissionImpl>
    implements _$$PracticeSubmissionImplCopyWith<$Res> {
  __$$PracticeSubmissionImplCopyWithImpl(_$PracticeSubmissionImpl _value,
      $Res Function(_$PracticeSubmissionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? studentId = null,
    Object? answers = null,
    Object? timeSpent = null,
  }) {
    return _then(_$PracticeSubmissionImpl(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      answers: null == answers
          ? _value._answers
          : answers // ignore: cast_nullable_to_non_nullable
              as List<PracticeAnswer>,
      timeSpent: null == timeSpent
          ? _value.timeSpent
          : timeSpent // ignore: cast_nullable_to_non_nullable
              as Duration,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeSubmissionImpl implements _PracticeSubmission {
  const _$PracticeSubmissionImpl(
      {required this.sessionId,
      required this.studentId,
      required final List<PracticeAnswer> answers,
      required this.timeSpent})
      : _answers = answers;

  factory _$PracticeSubmissionImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeSubmissionImplFromJson(json);

  @override
  final String sessionId;
  @override
  final String studentId;
  final List<PracticeAnswer> _answers;
  @override
  List<PracticeAnswer> get answers {
    if (_answers is EqualUnmodifiableListView) return _answers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_answers);
  }

  @override
  final Duration timeSpent;

  @override
  String toString() {
    return 'PracticeSubmission(sessionId: $sessionId, studentId: $studentId, answers: $answers, timeSpent: $timeSpent)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeSubmissionImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            const DeepCollectionEquality().equals(other._answers, _answers) &&
            (identical(other.timeSpent, timeSpent) ||
                other.timeSpent == timeSpent));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, sessionId, studentId,
      const DeepCollectionEquality().hash(_answers), timeSpent);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeSubmissionImplCopyWith<_$PracticeSubmissionImpl> get copyWith =>
      __$$PracticeSubmissionImplCopyWithImpl<_$PracticeSubmissionImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeSubmissionImplToJson(
      this,
    );
  }
}

abstract class _PracticeSubmission implements PracticeSubmission {
  const factory _PracticeSubmission(
      {required final String sessionId,
      required final String studentId,
      required final List<PracticeAnswer> answers,
      required final Duration timeSpent}) = _$PracticeSubmissionImpl;

  factory _PracticeSubmission.fromJson(Map<String, dynamic> json) =
      _$PracticeSubmissionImpl.fromJson;

  @override
  String get sessionId;
  @override
  String get studentId;
  @override
  List<PracticeAnswer> get answers;
  @override
  Duration get timeSpent;
  @override
  @JsonKey(ignore: true)
  _$$PracticeSubmissionImplCopyWith<_$PracticeSubmissionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PracticeAnswer _$PracticeAnswerFromJson(Map<String, dynamic> json) {
  return _PracticeAnswer.fromJson(json);
}

/// @nodoc
mixin _$PracticeAnswer {
  String get questionId => throw _privateConstructorUsedError;
  String get answer => throw _privateConstructorUsedError;
  String get answerLatex => throw _privateConstructorUsedError;
  int get timeSpentSeconds => throw _privateConstructorUsedError;
  bool get usedHint => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeAnswerCopyWith<PracticeAnswer> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeAnswerCopyWith<$Res> {
  factory $PracticeAnswerCopyWith(
          PracticeAnswer value, $Res Function(PracticeAnswer) then) =
      _$PracticeAnswerCopyWithImpl<$Res, PracticeAnswer>;
  @useResult
  $Res call(
      {String questionId,
      String answer,
      String answerLatex,
      int timeSpentSeconds,
      bool usedHint});
}

/// @nodoc
class _$PracticeAnswerCopyWithImpl<$Res, $Val extends PracticeAnswer>
    implements $PracticeAnswerCopyWith<$Res> {
  _$PracticeAnswerCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? answer = null,
    Object? answerLatex = null,
    Object? timeSpentSeconds = null,
    Object? usedHint = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      answer: null == answer
          ? _value.answer
          : answer // ignore: cast_nullable_to_non_nullable
              as String,
      answerLatex: null == answerLatex
          ? _value.answerLatex
          : answerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      timeSpentSeconds: null == timeSpentSeconds
          ? _value.timeSpentSeconds
          : timeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      usedHint: null == usedHint
          ? _value.usedHint
          : usedHint // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PracticeAnswerImplCopyWith<$Res>
    implements $PracticeAnswerCopyWith<$Res> {
  factory _$$PracticeAnswerImplCopyWith(_$PracticeAnswerImpl value,
          $Res Function(_$PracticeAnswerImpl) then) =
      __$$PracticeAnswerImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      String answer,
      String answerLatex,
      int timeSpentSeconds,
      bool usedHint});
}

/// @nodoc
class __$$PracticeAnswerImplCopyWithImpl<$Res>
    extends _$PracticeAnswerCopyWithImpl<$Res, _$PracticeAnswerImpl>
    implements _$$PracticeAnswerImplCopyWith<$Res> {
  __$$PracticeAnswerImplCopyWithImpl(
      _$PracticeAnswerImpl _value, $Res Function(_$PracticeAnswerImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? answer = null,
    Object? answerLatex = null,
    Object? timeSpentSeconds = null,
    Object? usedHint = null,
  }) {
    return _then(_$PracticeAnswerImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      answer: null == answer
          ? _value.answer
          : answer // ignore: cast_nullable_to_non_nullable
              as String,
      answerLatex: null == answerLatex
          ? _value.answerLatex
          : answerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      timeSpentSeconds: null == timeSpentSeconds
          ? _value.timeSpentSeconds
          : timeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      usedHint: null == usedHint
          ? _value.usedHint
          : usedHint // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeAnswerImpl implements _PracticeAnswer {
  const _$PracticeAnswerImpl(
      {required this.questionId,
      required this.answer,
      required this.answerLatex,
      required this.timeSpentSeconds,
      required this.usedHint});

  factory _$PracticeAnswerImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeAnswerImplFromJson(json);

  @override
  final String questionId;
  @override
  final String answer;
  @override
  final String answerLatex;
  @override
  final int timeSpentSeconds;
  @override
  final bool usedHint;

  @override
  String toString() {
    return 'PracticeAnswer(questionId: $questionId, answer: $answer, answerLatex: $answerLatex, timeSpentSeconds: $timeSpentSeconds, usedHint: $usedHint)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeAnswerImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.answer, answer) || other.answer == answer) &&
            (identical(other.answerLatex, answerLatex) ||
                other.answerLatex == answerLatex) &&
            (identical(other.timeSpentSeconds, timeSpentSeconds) ||
                other.timeSpentSeconds == timeSpentSeconds) &&
            (identical(other.usedHint, usedHint) ||
                other.usedHint == usedHint));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, questionId, answer, answerLatex, timeSpentSeconds, usedHint);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeAnswerImplCopyWith<_$PracticeAnswerImpl> get copyWith =>
      __$$PracticeAnswerImplCopyWithImpl<_$PracticeAnswerImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeAnswerImplToJson(
      this,
    );
  }
}

abstract class _PracticeAnswer implements PracticeAnswer {
  const factory _PracticeAnswer(
      {required final String questionId,
      required final String answer,
      required final String answerLatex,
      required final int timeSpentSeconds,
      required final bool usedHint}) = _$PracticeAnswerImpl;

  factory _PracticeAnswer.fromJson(Map<String, dynamic> json) =
      _$PracticeAnswerImpl.fromJson;

  @override
  String get questionId;
  @override
  String get answer;
  @override
  String get answerLatex;
  @override
  int get timeSpentSeconds;
  @override
  bool get usedHint;
  @override
  @JsonKey(ignore: true)
  _$$PracticeAnswerImplCopyWith<_$PracticeAnswerImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PracticeAnswerResult _$PracticeAnswerResultFromJson(Map<String, dynamic> json) {
  return _PracticeAnswerResult.fromJson(json);
}

/// @nodoc
mixin _$PracticeAnswerResult {
  String get questionId => throw _privateConstructorUsedError;
  bool get isCorrect => throw _privateConstructorUsedError;
  int get awardedMarks => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  String get feedback => throw _privateConstructorUsedError;
  String get explanation => throw _privateConstructorUsedError;
  List<String> get relatedConcepts => throw _privateConstructorUsedError;
  double get masteryGain => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeAnswerResultCopyWith<PracticeAnswerResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeAnswerResultCopyWith<$Res> {
  factory $PracticeAnswerResultCopyWith(PracticeAnswerResult value,
          $Res Function(PracticeAnswerResult) then) =
      _$PracticeAnswerResultCopyWithImpl<$Res, PracticeAnswerResult>;
  @useResult
  $Res call(
      {String questionId,
      bool isCorrect,
      int awardedMarks,
      int maxMarks,
      String feedback,
      String explanation,
      List<String> relatedConcepts,
      double masteryGain});
}

/// @nodoc
class _$PracticeAnswerResultCopyWithImpl<$Res,
        $Val extends PracticeAnswerResult>
    implements $PracticeAnswerResultCopyWith<$Res> {
  _$PracticeAnswerResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? isCorrect = null,
    Object? awardedMarks = null,
    Object? maxMarks = null,
    Object? feedback = null,
    Object? explanation = null,
    Object? relatedConcepts = null,
    Object? masteryGain = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      isCorrect: null == isCorrect
          ? _value.isCorrect
          : isCorrect // ignore: cast_nullable_to_non_nullable
              as bool,
      awardedMarks: null == awardedMarks
          ? _value.awardedMarks
          : awardedMarks // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      feedback: null == feedback
          ? _value.feedback
          : feedback // ignore: cast_nullable_to_non_nullable
              as String,
      explanation: null == explanation
          ? _value.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String,
      relatedConcepts: null == relatedConcepts
          ? _value.relatedConcepts
          : relatedConcepts // ignore: cast_nullable_to_non_nullable
              as List<String>,
      masteryGain: null == masteryGain
          ? _value.masteryGain
          : masteryGain // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PracticeAnswerResultImplCopyWith<$Res>
    implements $PracticeAnswerResultCopyWith<$Res> {
  factory _$$PracticeAnswerResultImplCopyWith(_$PracticeAnswerResultImpl value,
          $Res Function(_$PracticeAnswerResultImpl) then) =
      __$$PracticeAnswerResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      bool isCorrect,
      int awardedMarks,
      int maxMarks,
      String feedback,
      String explanation,
      List<String> relatedConcepts,
      double masteryGain});
}

/// @nodoc
class __$$PracticeAnswerResultImplCopyWithImpl<$Res>
    extends _$PracticeAnswerResultCopyWithImpl<$Res, _$PracticeAnswerResultImpl>
    implements _$$PracticeAnswerResultImplCopyWith<$Res> {
  __$$PracticeAnswerResultImplCopyWithImpl(_$PracticeAnswerResultImpl _value,
      $Res Function(_$PracticeAnswerResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? isCorrect = null,
    Object? awardedMarks = null,
    Object? maxMarks = null,
    Object? feedback = null,
    Object? explanation = null,
    Object? relatedConcepts = null,
    Object? masteryGain = null,
  }) {
    return _then(_$PracticeAnswerResultImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      isCorrect: null == isCorrect
          ? _value.isCorrect
          : isCorrect // ignore: cast_nullable_to_non_nullable
              as bool,
      awardedMarks: null == awardedMarks
          ? _value.awardedMarks
          : awardedMarks // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      feedback: null == feedback
          ? _value.feedback
          : feedback // ignore: cast_nullable_to_non_nullable
              as String,
      explanation: null == explanation
          ? _value.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String,
      relatedConcepts: null == relatedConcepts
          ? _value._relatedConcepts
          : relatedConcepts // ignore: cast_nullable_to_non_nullable
              as List<String>,
      masteryGain: null == masteryGain
          ? _value.masteryGain
          : masteryGain // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeAnswerResultImpl implements _PracticeAnswerResult {
  const _$PracticeAnswerResultImpl(
      {required this.questionId,
      required this.isCorrect,
      required this.awardedMarks,
      required this.maxMarks,
      required this.feedback,
      required this.explanation,
      required final List<String> relatedConcepts,
      required this.masteryGain})
      : _relatedConcepts = relatedConcepts;

  factory _$PracticeAnswerResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeAnswerResultImplFromJson(json);

  @override
  final String questionId;
  @override
  final bool isCorrect;
  @override
  final int awardedMarks;
  @override
  final int maxMarks;
  @override
  final String feedback;
  @override
  final String explanation;
  final List<String> _relatedConcepts;
  @override
  List<String> get relatedConcepts {
    if (_relatedConcepts is EqualUnmodifiableListView) return _relatedConcepts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_relatedConcepts);
  }

  @override
  final double masteryGain;

  @override
  String toString() {
    return 'PracticeAnswerResult(questionId: $questionId, isCorrect: $isCorrect, awardedMarks: $awardedMarks, maxMarks: $maxMarks, feedback: $feedback, explanation: $explanation, relatedConcepts: $relatedConcepts, masteryGain: $masteryGain)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeAnswerResultImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.isCorrect, isCorrect) ||
                other.isCorrect == isCorrect) &&
            (identical(other.awardedMarks, awardedMarks) ||
                other.awardedMarks == awardedMarks) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.feedback, feedback) ||
                other.feedback == feedback) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation) &&
            const DeepCollectionEquality()
                .equals(other._relatedConcepts, _relatedConcepts) &&
            (identical(other.masteryGain, masteryGain) ||
                other.masteryGain == masteryGain));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      isCorrect,
      awardedMarks,
      maxMarks,
      feedback,
      explanation,
      const DeepCollectionEquality().hash(_relatedConcepts),
      masteryGain);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeAnswerResultImplCopyWith<_$PracticeAnswerResultImpl>
      get copyWith =>
          __$$PracticeAnswerResultImplCopyWithImpl<_$PracticeAnswerResultImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeAnswerResultImplToJson(
      this,
    );
  }
}

abstract class _PracticeAnswerResult implements PracticeAnswerResult {
  const factory _PracticeAnswerResult(
      {required final String questionId,
      required final bool isCorrect,
      required final int awardedMarks,
      required final int maxMarks,
      required final String feedback,
      required final String explanation,
      required final List<String> relatedConcepts,
      required final double masteryGain}) = _$PracticeAnswerResultImpl;

  factory _PracticeAnswerResult.fromJson(Map<String, dynamic> json) =
      _$PracticeAnswerResultImpl.fromJson;

  @override
  String get questionId;
  @override
  bool get isCorrect;
  @override
  int get awardedMarks;
  @override
  int get maxMarks;
  @override
  String get feedback;
  @override
  String get explanation;
  @override
  List<String> get relatedConcepts;
  @override
  double get masteryGain;
  @override
  @JsonKey(ignore: true)
  _$$PracticeAnswerResultImplCopyWith<_$PracticeAnswerResultImpl>
      get copyWith => throw _privateConstructorUsedError;
}

PracticeResult _$PracticeResultFromJson(Map<String, dynamic> json) {
  return _PracticeResult.fromJson(json);
}

/// @nodoc
mixin _$PracticeResult {
  int get score => throw _privateConstructorUsedError;
  int get maxScore => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  Map<String, double> get conceptScores => throw _privateConstructorUsedError;
  List<String> get strengths => throw _privateConstructorUsedError;
  List<String> get weaknesses => throw _privateConstructorUsedError;
  List<ActionableRecommendation> get recommendations =>
      throw _privateConstructorUsedError;
  Duration get timeSpent => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PracticeResultCopyWith<PracticeResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PracticeResultCopyWith<$Res> {
  factory $PracticeResultCopyWith(
          PracticeResult value, $Res Function(PracticeResult) then) =
      _$PracticeResultCopyWithImpl<$Res, PracticeResult>;
  @useResult
  $Res call(
      {int score,
      int maxScore,
      double percentage,
      Map<String, double> conceptScores,
      List<String> strengths,
      List<String> weaknesses,
      List<ActionableRecommendation> recommendations,
      Duration timeSpent});
}

/// @nodoc
class _$PracticeResultCopyWithImpl<$Res, $Val extends PracticeResult>
    implements $PracticeResultCopyWith<$Res> {
  _$PracticeResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? score = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? conceptScores = null,
    Object? strengths = null,
    Object? weaknesses = null,
    Object? recommendations = null,
    Object? timeSpent = null,
  }) {
    return _then(_value.copyWith(
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
      recommendations: null == recommendations
          ? _value.recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      timeSpent: null == timeSpent
          ? _value.timeSpent
          : timeSpent // ignore: cast_nullable_to_non_nullable
              as Duration,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PracticeResultImplCopyWith<$Res>
    implements $PracticeResultCopyWith<$Res> {
  factory _$$PracticeResultImplCopyWith(_$PracticeResultImpl value,
          $Res Function(_$PracticeResultImpl) then) =
      __$$PracticeResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int score,
      int maxScore,
      double percentage,
      Map<String, double> conceptScores,
      List<String> strengths,
      List<String> weaknesses,
      List<ActionableRecommendation> recommendations,
      Duration timeSpent});
}

/// @nodoc
class __$$PracticeResultImplCopyWithImpl<$Res>
    extends _$PracticeResultCopyWithImpl<$Res, _$PracticeResultImpl>
    implements _$$PracticeResultImplCopyWith<$Res> {
  __$$PracticeResultImplCopyWithImpl(
      _$PracticeResultImpl _value, $Res Function(_$PracticeResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? score = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? conceptScores = null,
    Object? strengths = null,
    Object? weaknesses = null,
    Object? recommendations = null,
    Object? timeSpent = null,
  }) {
    return _then(_$PracticeResultImpl(
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
      recommendations: null == recommendations
          ? _value._recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      timeSpent: null == timeSpent
          ? _value.timeSpent
          : timeSpent // ignore: cast_nullable_to_non_nullable
              as Duration,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PracticeResultImpl implements _PracticeResult {
  const _$PracticeResultImpl(
      {required this.score,
      required this.maxScore,
      required this.percentage,
      required final Map<String, double> conceptScores,
      required final List<String> strengths,
      required final List<String> weaknesses,
      required final List<ActionableRecommendation> recommendations,
      required this.timeSpent})
      : _conceptScores = conceptScores,
        _strengths = strengths,
        _weaknesses = weaknesses,
        _recommendations = recommendations;

  factory _$PracticeResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$PracticeResultImplFromJson(json);

  @override
  final int score;
  @override
  final int maxScore;
  @override
  final double percentage;
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

  final List<ActionableRecommendation> _recommendations;
  @override
  List<ActionableRecommendation> get recommendations {
    if (_recommendations is EqualUnmodifiableListView) return _recommendations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendations);
  }

  @override
  final Duration timeSpent;

  @override
  String toString() {
    return 'PracticeResult(score: $score, maxScore: $maxScore, percentage: $percentage, conceptScores: $conceptScores, strengths: $strengths, weaknesses: $weaknesses, recommendations: $recommendations, timeSpent: $timeSpent)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PracticeResultImpl &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.maxScore, maxScore) ||
                other.maxScore == maxScore) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            const DeepCollectionEquality()
                .equals(other._conceptScores, _conceptScores) &&
            const DeepCollectionEquality()
                .equals(other._strengths, _strengths) &&
            const DeepCollectionEquality()
                .equals(other._weaknesses, _weaknesses) &&
            const DeepCollectionEquality()
                .equals(other._recommendations, _recommendations) &&
            (identical(other.timeSpent, timeSpent) ||
                other.timeSpent == timeSpent));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      score,
      maxScore,
      percentage,
      const DeepCollectionEquality().hash(_conceptScores),
      const DeepCollectionEquality().hash(_strengths),
      const DeepCollectionEquality().hash(_weaknesses),
      const DeepCollectionEquality().hash(_recommendations),
      timeSpent);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PracticeResultImplCopyWith<_$PracticeResultImpl> get copyWith =>
      __$$PracticeResultImplCopyWithImpl<_$PracticeResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PracticeResultImplToJson(
      this,
    );
  }
}

abstract class _PracticeResult implements PracticeResult {
  const factory _PracticeResult(
      {required final int score,
      required final int maxScore,
      required final double percentage,
      required final Map<String, double> conceptScores,
      required final List<String> strengths,
      required final List<String> weaknesses,
      required final List<ActionableRecommendation> recommendations,
      required final Duration timeSpent}) = _$PracticeResultImpl;

  factory _PracticeResult.fromJson(Map<String, dynamic> json) =
      _$PracticeResultImpl.fromJson;

  @override
  int get score;
  @override
  int get maxScore;
  @override
  double get percentage;
  @override
  Map<String, double> get conceptScores;
  @override
  List<String> get strengths;
  @override
  List<String> get weaknesses;
  @override
  List<ActionableRecommendation> get recommendations;
  @override
  Duration get timeSpent;
  @override
  @JsonKey(ignore: true)
  _$$PracticeResultImplCopyWith<_$PracticeResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ReportRequest _$ReportRequestFromJson(Map<String, dynamic> json) {
  return _ReportRequest.fromJson(json);
}

/// @nodoc
mixin _$ReportRequest {
  String get assessmentId => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  ReportType get type => throw _privateConstructorUsedError;
  Map<String, dynamic>? get options => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ReportRequestCopyWith<ReportRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ReportRequestCopyWith<$Res> {
  factory $ReportRequestCopyWith(
          ReportRequest value, $Res Function(ReportRequest) then) =
      _$ReportRequestCopyWithImpl<$Res, ReportRequest>;
  @useResult
  $Res call(
      {String assessmentId,
      String studentId,
      ReportType type,
      Map<String, dynamic>? options});
}

/// @nodoc
class _$ReportRequestCopyWithImpl<$Res, $Val extends ReportRequest>
    implements $ReportRequestCopyWith<$Res> {
  _$ReportRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? studentId = null,
    Object? type = null,
    Object? options = freezed,
  }) {
    return _then(_value.copyWith(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as ReportType,
      options: freezed == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ReportRequestImplCopyWith<$Res>
    implements $ReportRequestCopyWith<$Res> {
  factory _$$ReportRequestImplCopyWith(
          _$ReportRequestImpl value, $Res Function(_$ReportRequestImpl) then) =
      __$$ReportRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String assessmentId,
      String studentId,
      ReportType type,
      Map<String, dynamic>? options});
}

/// @nodoc
class __$$ReportRequestImplCopyWithImpl<$Res>
    extends _$ReportRequestCopyWithImpl<$Res, _$ReportRequestImpl>
    implements _$$ReportRequestImplCopyWith<$Res> {
  __$$ReportRequestImplCopyWithImpl(
      _$ReportRequestImpl _value, $Res Function(_$ReportRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? studentId = null,
    Object? type = null,
    Object? options = freezed,
  }) {
    return _then(_$ReportRequestImpl(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as ReportType,
      options: freezed == options
          ? _value._options
          : options // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ReportRequestImpl implements _ReportRequest {
  const _$ReportRequestImpl(
      {required this.assessmentId,
      required this.studentId,
      required this.type,
      final Map<String, dynamic>? options})
      : _options = options;

  factory _$ReportRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$ReportRequestImplFromJson(json);

  @override
  final String assessmentId;
  @override
  final String studentId;
  @override
  final ReportType type;
  final Map<String, dynamic>? _options;
  @override
  Map<String, dynamic>? get options {
    final value = _options;
    if (value == null) return null;
    if (_options is EqualUnmodifiableMapView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'ReportRequest(assessmentId: $assessmentId, studentId: $studentId, type: $type, options: $options)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ReportRequestImpl &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.type, type) || other.type == type) &&
            const DeepCollectionEquality().equals(other._options, _options));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, assessmentId, studentId, type,
      const DeepCollectionEquality().hash(_options));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ReportRequestImplCopyWith<_$ReportRequestImpl> get copyWith =>
      __$$ReportRequestImplCopyWithImpl<_$ReportRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ReportRequestImplToJson(
      this,
    );
  }
}

abstract class _ReportRequest implements ReportRequest {
  const factory _ReportRequest(
      {required final String assessmentId,
      required final String studentId,
      required final ReportType type,
      final Map<String, dynamic>? options}) = _$ReportRequestImpl;

  factory _ReportRequest.fromJson(Map<String, dynamic> json) =
      _$ReportRequestImpl.fromJson;

  @override
  String get assessmentId;
  @override
  String get studentId;
  @override
  ReportType get type;
  @override
  Map<String, dynamic>? get options;
  @override
  @JsonKey(ignore: true)
  _$$ReportRequestImplCopyWith<_$ReportRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BulkReportRequest _$BulkReportRequestFromJson(Map<String, dynamic> json) {
  return _BulkReportRequest.fromJson(json);
}

/// @nodoc
mixin _$BulkReportRequest {
  String get assessmentId => throw _privateConstructorUsedError;
  List<String> get studentIds => throw _privateConstructorUsedError;
  ReportType get type => throw _privateConstructorUsedError;
  Map<String, dynamic>? get options => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BulkReportRequestCopyWith<BulkReportRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BulkReportRequestCopyWith<$Res> {
  factory $BulkReportRequestCopyWith(
          BulkReportRequest value, $Res Function(BulkReportRequest) then) =
      _$BulkReportRequestCopyWithImpl<$Res, BulkReportRequest>;
  @useResult
  $Res call(
      {String assessmentId,
      List<String> studentIds,
      ReportType type,
      Map<String, dynamic>? options});
}

/// @nodoc
class _$BulkReportRequestCopyWithImpl<$Res, $Val extends BulkReportRequest>
    implements $BulkReportRequestCopyWith<$Res> {
  _$BulkReportRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? studentIds = null,
    Object? type = null,
    Object? options = freezed,
  }) {
    return _then(_value.copyWith(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentIds: null == studentIds
          ? _value.studentIds
          : studentIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as ReportType,
      options: freezed == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BulkReportRequestImplCopyWith<$Res>
    implements $BulkReportRequestCopyWith<$Res> {
  factory _$$BulkReportRequestImplCopyWith(_$BulkReportRequestImpl value,
          $Res Function(_$BulkReportRequestImpl) then) =
      __$$BulkReportRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String assessmentId,
      List<String> studentIds,
      ReportType type,
      Map<String, dynamic>? options});
}

/// @nodoc
class __$$BulkReportRequestImplCopyWithImpl<$Res>
    extends _$BulkReportRequestCopyWithImpl<$Res, _$BulkReportRequestImpl>
    implements _$$BulkReportRequestImplCopyWith<$Res> {
  __$$BulkReportRequestImplCopyWithImpl(_$BulkReportRequestImpl _value,
      $Res Function(_$BulkReportRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? assessmentId = null,
    Object? studentIds = null,
    Object? type = null,
    Object? options = freezed,
  }) {
    return _then(_$BulkReportRequestImpl(
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentIds: null == studentIds
          ? _value._studentIds
          : studentIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as ReportType,
      options: freezed == options
          ? _value._options
          : options // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BulkReportRequestImpl implements _BulkReportRequest {
  const _$BulkReportRequestImpl(
      {required this.assessmentId,
      required final List<String> studentIds,
      required this.type,
      final Map<String, dynamic>? options})
      : _studentIds = studentIds,
        _options = options;

  factory _$BulkReportRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$BulkReportRequestImplFromJson(json);

  @override
  final String assessmentId;
  final List<String> _studentIds;
  @override
  List<String> get studentIds {
    if (_studentIds is EqualUnmodifiableListView) return _studentIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_studentIds);
  }

  @override
  final ReportType type;
  final Map<String, dynamic>? _options;
  @override
  Map<String, dynamic>? get options {
    final value = _options;
    if (value == null) return null;
    if (_options is EqualUnmodifiableMapView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'BulkReportRequest(assessmentId: $assessmentId, studentIds: $studentIds, type: $type, options: $options)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BulkReportRequestImpl &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            const DeepCollectionEquality()
                .equals(other._studentIds, _studentIds) &&
            (identical(other.type, type) || other.type == type) &&
            const DeepCollectionEquality().equals(other._options, _options));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      assessmentId,
      const DeepCollectionEquality().hash(_studentIds),
      type,
      const DeepCollectionEquality().hash(_options));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BulkReportRequestImplCopyWith<_$BulkReportRequestImpl> get copyWith =>
      __$$BulkReportRequestImplCopyWithImpl<_$BulkReportRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BulkReportRequestImplToJson(
      this,
    );
  }
}

abstract class _BulkReportRequest implements BulkReportRequest {
  const factory _BulkReportRequest(
      {required final String assessmentId,
      required final List<String> studentIds,
      required final ReportType type,
      final Map<String, dynamic>? options}) = _$BulkReportRequestImpl;

  factory _BulkReportRequest.fromJson(Map<String, dynamic> json) =
      _$BulkReportRequestImpl.fromJson;

  @override
  String get assessmentId;
  @override
  List<String> get studentIds;
  @override
  ReportType get type;
  @override
  Map<String, dynamic>? get options;
  @override
  @JsonKey(ignore: true)
  _$$BulkReportRequestImplCopyWith<_$BulkReportRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

Notification _$NotificationFromJson(Map<String, dynamic> json) {
  return _Notification.fromJson(json);
}

/// @nodoc
mixin _$Notification {
  String get id => throw _privateConstructorUsedError;
  String get userId => throw _privateConstructorUsedError;
  NotificationType get type => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get body => throw _privateConstructorUsedError;
  Map<String, dynamic> get data => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  bool get isRead => throw _privateConstructorUsedError;
  DateTime? get readAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $NotificationCopyWith<Notification> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $NotificationCopyWith<$Res> {
  factory $NotificationCopyWith(
          Notification value, $Res Function(Notification) then) =
      _$NotificationCopyWithImpl<$Res, Notification>;
  @useResult
  $Res call(
      {String id,
      String userId,
      NotificationType type,
      String title,
      String body,
      Map<String, dynamic> data,
      DateTime createdAt,
      bool isRead,
      DateTime? readAt});
}

/// @nodoc
class _$NotificationCopyWithImpl<$Res, $Val extends Notification>
    implements $NotificationCopyWith<$Res> {
  _$NotificationCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? userId = null,
    Object? type = null,
    Object? title = null,
    Object? body = null,
    Object? data = null,
    Object? createdAt = null,
    Object? isRead = null,
    Object? readAt = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      userId: null == userId
          ? _value.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as NotificationType,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      body: null == body
          ? _value.body
          : body // ignore: cast_nullable_to_non_nullable
              as String,
      data: null == data
          ? _value.data
          : data // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      isRead: null == isRead
          ? _value.isRead
          : isRead // ignore: cast_nullable_to_non_nullable
              as bool,
      readAt: freezed == readAt
          ? _value.readAt
          : readAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$NotificationImplCopyWith<$Res>
    implements $NotificationCopyWith<$Res> {
  factory _$$NotificationImplCopyWith(
          _$NotificationImpl value, $Res Function(_$NotificationImpl) then) =
      __$$NotificationImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String userId,
      NotificationType type,
      String title,
      String body,
      Map<String, dynamic> data,
      DateTime createdAt,
      bool isRead,
      DateTime? readAt});
}

/// @nodoc
class __$$NotificationImplCopyWithImpl<$Res>
    extends _$NotificationCopyWithImpl<$Res, _$NotificationImpl>
    implements _$$NotificationImplCopyWith<$Res> {
  __$$NotificationImplCopyWithImpl(
      _$NotificationImpl _value, $Res Function(_$NotificationImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? userId = null,
    Object? type = null,
    Object? title = null,
    Object? body = null,
    Object? data = null,
    Object? createdAt = null,
    Object? isRead = null,
    Object? readAt = freezed,
  }) {
    return _then(_$NotificationImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      userId: null == userId
          ? _value.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as NotificationType,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      body: null == body
          ? _value.body
          : body // ignore: cast_nullable_to_non_nullable
              as String,
      data: null == data
          ? _value._data
          : data // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      isRead: null == isRead
          ? _value.isRead
          : isRead // ignore: cast_nullable_to_non_nullable
              as bool,
      readAt: freezed == readAt
          ? _value.readAt
          : readAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$NotificationImpl implements _Notification {
  const _$NotificationImpl(
      {required this.id,
      required this.userId,
      required this.type,
      required this.title,
      required this.body,
      required final Map<String, dynamic> data,
      required this.createdAt,
      required this.isRead,
      this.readAt})
      : _data = data;

  factory _$NotificationImpl.fromJson(Map<String, dynamic> json) =>
      _$$NotificationImplFromJson(json);

  @override
  final String id;
  @override
  final String userId;
  @override
  final NotificationType type;
  @override
  final String title;
  @override
  final String body;
  final Map<String, dynamic> _data;
  @override
  Map<String, dynamic> get data {
    if (_data is EqualUnmodifiableMapView) return _data;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_data);
  }

  @override
  final DateTime createdAt;
  @override
  final bool isRead;
  @override
  final DateTime? readAt;

  @override
  String toString() {
    return 'Notification(id: $id, userId: $userId, type: $type, title: $title, body: $body, data: $data, createdAt: $createdAt, isRead: $isRead, readAt: $readAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$NotificationImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.body, body) || other.body == body) &&
            const DeepCollectionEquality().equals(other._data, _data) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.isRead, isRead) || other.isRead == isRead) &&
            (identical(other.readAt, readAt) || other.readAt == readAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, id, userId, type, title, body,
      const DeepCollectionEquality().hash(_data), createdAt, isRead, readAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$NotificationImplCopyWith<_$NotificationImpl> get copyWith =>
      __$$NotificationImplCopyWithImpl<_$NotificationImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$NotificationImplToJson(
      this,
    );
  }
}

abstract class _Notification implements Notification {
  const factory _Notification(
      {required final String id,
      required final String userId,
      required final NotificationType type,
      required final String title,
      required final String body,
      required final Map<String, dynamic> data,
      required final DateTime createdAt,
      required final bool isRead,
      final DateTime? readAt}) = _$NotificationImpl;

  factory _Notification.fromJson(Map<String, dynamic> json) =
      _$NotificationImpl.fromJson;

  @override
  String get id;
  @override
  String get userId;
  @override
  NotificationType get type;
  @override
  String get title;
  @override
  String get body;
  @override
  Map<String, dynamic> get data;
  @override
  DateTime get createdAt;
  @override
  bool get isRead;
  @override
  DateTime? get readAt;
  @override
  @JsonKey(ignore: true)
  _$$NotificationImplCopyWith<_$NotificationImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

WhatsAppDeepLink _$WhatsAppDeepLinkFromJson(Map<String, dynamic> json) {
  return _WhatsAppDeepLink.fromJson(json);
}

/// @nodoc
mixin _$WhatsAppDeepLink {
  String get phoneNumber => throw _privateConstructorUsedError;
  String get message => throw _privateConstructorUsedError;
  String get deepLinkUrl => throw _privateConstructorUsedError;
  String get fallbackUrl => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $WhatsAppDeepLinkCopyWith<WhatsAppDeepLink> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $WhatsAppDeepLinkCopyWith<$Res> {
  factory $WhatsAppDeepLinkCopyWith(
          WhatsAppDeepLink value, $Res Function(WhatsAppDeepLink) then) =
      _$WhatsAppDeepLinkCopyWithImpl<$Res, WhatsAppDeepLink>;
  @useResult
  $Res call(
      {String phoneNumber,
      String message,
      String deepLinkUrl,
      String fallbackUrl});
}

/// @nodoc
class _$WhatsAppDeepLinkCopyWithImpl<$Res, $Val extends WhatsAppDeepLink>
    implements $WhatsAppDeepLinkCopyWith<$Res> {
  _$WhatsAppDeepLinkCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? phoneNumber = null,
    Object? message = null,
    Object? deepLinkUrl = null,
    Object? fallbackUrl = null,
  }) {
    return _then(_value.copyWith(
      phoneNumber: null == phoneNumber
          ? _value.phoneNumber
          : phoneNumber // ignore: cast_nullable_to_non_nullable
              as String,
      message: null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
      deepLinkUrl: null == deepLinkUrl
          ? _value.deepLinkUrl
          : deepLinkUrl // ignore: cast_nullable_to_non_nullable
              as String,
      fallbackUrl: null == fallbackUrl
          ? _value.fallbackUrl
          : fallbackUrl // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$WhatsAppDeepLinkImplCopyWith<$Res>
    implements $WhatsAppDeepLinkCopyWith<$Res> {
  factory _$$WhatsAppDeepLinkImplCopyWith(_$WhatsAppDeepLinkImpl value,
          $Res Function(_$WhatsAppDeepLinkImpl) then) =
      __$$WhatsAppDeepLinkImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String phoneNumber,
      String message,
      String deepLinkUrl,
      String fallbackUrl});
}

/// @nodoc
class __$$WhatsAppDeepLinkImplCopyWithImpl<$Res>
    extends _$WhatsAppDeepLinkCopyWithImpl<$Res, _$WhatsAppDeepLinkImpl>
    implements _$$WhatsAppDeepLinkImplCopyWith<$Res> {
  __$$WhatsAppDeepLinkImplCopyWithImpl(_$WhatsAppDeepLinkImpl _value,
      $Res Function(_$WhatsAppDeepLinkImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? phoneNumber = null,
    Object? message = null,
    Object? deepLinkUrl = null,
    Object? fallbackUrl = null,
  }) {
    return _then(_$WhatsAppDeepLinkImpl(
      phoneNumber: null == phoneNumber
          ? _value.phoneNumber
          : phoneNumber // ignore: cast_nullable_to_non_nullable
              as String,
      message: null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
      deepLinkUrl: null == deepLinkUrl
          ? _value.deepLinkUrl
          : deepLinkUrl // ignore: cast_nullable_to_non_nullable
              as String,
      fallbackUrl: null == fallbackUrl
          ? _value.fallbackUrl
          : fallbackUrl // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$WhatsAppDeepLinkImpl implements _WhatsAppDeepLink {
  const _$WhatsAppDeepLinkImpl(
      {required this.phoneNumber,
      required this.message,
      required this.deepLinkUrl,
      required this.fallbackUrl});

  factory _$WhatsAppDeepLinkImpl.fromJson(Map<String, dynamic> json) =>
      _$$WhatsAppDeepLinkImplFromJson(json);

  @override
  final String phoneNumber;
  @override
  final String message;
  @override
  final String deepLinkUrl;
  @override
  final String fallbackUrl;

  @override
  String toString() {
    return 'WhatsAppDeepLink(phoneNumber: $phoneNumber, message: $message, deepLinkUrl: $deepLinkUrl, fallbackUrl: $fallbackUrl)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$WhatsAppDeepLinkImpl &&
            (identical(other.phoneNumber, phoneNumber) ||
                other.phoneNumber == phoneNumber) &&
            (identical(other.message, message) || other.message == message) &&
            (identical(other.deepLinkUrl, deepLinkUrl) ||
                other.deepLinkUrl == deepLinkUrl) &&
            (identical(other.fallbackUrl, fallbackUrl) ||
                other.fallbackUrl == fallbackUrl));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, phoneNumber, message, deepLinkUrl, fallbackUrl);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$WhatsAppDeepLinkImplCopyWith<_$WhatsAppDeepLinkImpl> get copyWith =>
      __$$WhatsAppDeepLinkImplCopyWithImpl<_$WhatsAppDeepLinkImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$WhatsAppDeepLinkImplToJson(
      this,
    );
  }
}

abstract class _WhatsAppDeepLink implements WhatsAppDeepLink {
  const factory _WhatsAppDeepLink(
      {required final String phoneNumber,
      required final String message,
      required final String deepLinkUrl,
      required final String fallbackUrl}) = _$WhatsAppDeepLinkImpl;

  factory _WhatsAppDeepLink.fromJson(Map<String, dynamic> json) =
      _$WhatsAppDeepLinkImpl.fromJson;

  @override
  String get phoneNumber;
  @override
  String get message;
  @override
  String get deepLinkUrl;
  @override
  String get fallbackUrl;
  @override
  @JsonKey(ignore: true)
  _$$WhatsAppDeepLinkImplCopyWith<_$WhatsAppDeepLinkImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
