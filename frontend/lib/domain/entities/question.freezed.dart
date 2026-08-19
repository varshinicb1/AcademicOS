// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'question.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

Question _$QuestionFromJson(Map<String, dynamic> json) {
  return _Question.fromJson(json);
}

/// @nodoc
mixin _$Question {
  String get id => throw _privateConstructorUsedError;
  String get questionBankId => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  List<String> get chapterIds => throw _privateConstructorUsedError;
  List<String> get competencyIds => throw _privateConstructorUsedError;
  @BloomLevelConverter()
  BloomLevel get bloomLevel => throw _privateConstructorUsedError;
  @DifficultyConverter()
  Difficulty get difficulty => throw _privateConstructorUsedError;
  @QuestionTypeConverter()
  QuestionType get type => throw _privateConstructorUsedError;
  String get stem => throw _privateConstructorUsedError;
  String get stemLatex => throw _privateConstructorUsedError;
  List<QuestionPart> get parts => throw _privateConstructorUsedError;
  AnswerScheme get answerScheme => throw _privateConstructorUsedError;
  int get estimatedTimeMinutes => throw _privateConstructorUsedError;
  int get marks => throw _privateConstructorUsedError;
  String get language => throw _privateConstructorUsedError;
  @QuestionSourceConverter()
  QuestionSource get source => throw _privateConstructorUsedError;
  double get qualityScore => throw _privateConstructorUsedError;
  List<String> get tags => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  DateTime get updatedAt => throw _privateConstructorUsedError;
  Map<String, dynamic> get metadata => throw _privateConstructorUsedError;
  String? get diagramAssetId => throw _privateConstructorUsedError;
  String? get mapAssetId => throw _privateConstructorUsedError;
  String? get graphAssetId => throw _privateConstructorUsedError;
  String? get tableAssetId => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionCopyWith<Question> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionCopyWith<$Res> {
  factory $QuestionCopyWith(Question value, $Res Function(Question) then) =
      _$QuestionCopyWithImpl<$Res, Question>;
  @useResult
  $Res call(
      {String id,
      String questionBankId,
      String subject,
      int grade,
      List<String> chapterIds,
      List<String> competencyIds,
      @BloomLevelConverter() BloomLevel bloomLevel,
      @DifficultyConverter() Difficulty difficulty,
      @QuestionTypeConverter() QuestionType type,
      String stem,
      String stemLatex,
      List<QuestionPart> parts,
      AnswerScheme answerScheme,
      int estimatedTimeMinutes,
      int marks,
      String language,
      @QuestionSourceConverter() QuestionSource source,
      double qualityScore,
      List<String> tags,
      DateTime createdAt,
      DateTime updatedAt,
      Map<String, dynamic> metadata,
      String? diagramAssetId,
      String? mapAssetId,
      String? graphAssetId,
      String? tableAssetId});

  $AnswerSchemeCopyWith<$Res> get answerScheme;
}

/// @nodoc
class _$QuestionCopyWithImpl<$Res, $Val extends Question>
    implements $QuestionCopyWith<$Res> {
  _$QuestionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? questionBankId = null,
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? competencyIds = null,
    Object? bloomLevel = null,
    Object? difficulty = null,
    Object? type = null,
    Object? stem = null,
    Object? stemLatex = null,
    Object? parts = null,
    Object? answerScheme = null,
    Object? estimatedTimeMinutes = null,
    Object? marks = null,
    Object? language = null,
    Object? source = null,
    Object? qualityScore = null,
    Object? tags = null,
    Object? createdAt = null,
    Object? updatedAt = null,
    Object? metadata = null,
    Object? diagramAssetId = freezed,
    Object? mapAssetId = freezed,
    Object? graphAssetId = freezed,
    Object? tableAssetId = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      questionBankId: null == questionBankId
          ? _value.questionBankId
          : questionBankId // ignore: cast_nullable_to_non_nullable
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
      competencyIds: null == competencyIds
          ? _value.competencyIds
          : competencyIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      bloomLevel: null == bloomLevel
          ? _value.bloomLevel
          : bloomLevel // ignore: cast_nullable_to_non_nullable
              as BloomLevel,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as Difficulty,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as QuestionType,
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
      answerScheme: null == answerScheme
          ? _value.answerScheme
          : answerScheme // ignore: cast_nullable_to_non_nullable
              as AnswerScheme,
      estimatedTimeMinutes: null == estimatedTimeMinutes
          ? _value.estimatedTimeMinutes
          : estimatedTimeMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      language: null == language
          ? _value.language
          : language // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as QuestionSource,
      qualityScore: null == qualityScore
          ? _value.qualityScore
          : qualityScore // ignore: cast_nullable_to_non_nullable
              as double,
      tags: null == tags
          ? _value.tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      diagramAssetId: freezed == diagramAssetId
          ? _value.diagramAssetId
          : diagramAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
      mapAssetId: freezed == mapAssetId
          ? _value.mapAssetId
          : mapAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
      graphAssetId: freezed == graphAssetId
          ? _value.graphAssetId
          : graphAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
      tableAssetId: freezed == tableAssetId
          ? _value.tableAssetId
          : tableAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $AnswerSchemeCopyWith<$Res> get answerScheme {
    return $AnswerSchemeCopyWith<$Res>(_value.answerScheme, (value) {
      return _then(_value.copyWith(answerScheme: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$QuestionImplCopyWith<$Res>
    implements $QuestionCopyWith<$Res> {
  factory _$$QuestionImplCopyWith(
          _$QuestionImpl value, $Res Function(_$QuestionImpl) then) =
      __$$QuestionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String questionBankId,
      String subject,
      int grade,
      List<String> chapterIds,
      List<String> competencyIds,
      @BloomLevelConverter() BloomLevel bloomLevel,
      @DifficultyConverter() Difficulty difficulty,
      @QuestionTypeConverter() QuestionType type,
      String stem,
      String stemLatex,
      List<QuestionPart> parts,
      AnswerScheme answerScheme,
      int estimatedTimeMinutes,
      int marks,
      String language,
      @QuestionSourceConverter() QuestionSource source,
      double qualityScore,
      List<String> tags,
      DateTime createdAt,
      DateTime updatedAt,
      Map<String, dynamic> metadata,
      String? diagramAssetId,
      String? mapAssetId,
      String? graphAssetId,
      String? tableAssetId});

  @override
  $AnswerSchemeCopyWith<$Res> get answerScheme;
}

/// @nodoc
class __$$QuestionImplCopyWithImpl<$Res>
    extends _$QuestionCopyWithImpl<$Res, _$QuestionImpl>
    implements _$$QuestionImplCopyWith<$Res> {
  __$$QuestionImplCopyWithImpl(
      _$QuestionImpl _value, $Res Function(_$QuestionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? questionBankId = null,
    Object? subject = null,
    Object? grade = null,
    Object? chapterIds = null,
    Object? competencyIds = null,
    Object? bloomLevel = null,
    Object? difficulty = null,
    Object? type = null,
    Object? stem = null,
    Object? stemLatex = null,
    Object? parts = null,
    Object? answerScheme = null,
    Object? estimatedTimeMinutes = null,
    Object? marks = null,
    Object? language = null,
    Object? source = null,
    Object? qualityScore = null,
    Object? tags = null,
    Object? createdAt = null,
    Object? updatedAt = null,
    Object? metadata = null,
    Object? diagramAssetId = freezed,
    Object? mapAssetId = freezed,
    Object? graphAssetId = freezed,
    Object? tableAssetId = freezed,
  }) {
    return _then(_$QuestionImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      questionBankId: null == questionBankId
          ? _value.questionBankId
          : questionBankId // ignore: cast_nullable_to_non_nullable
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
      competencyIds: null == competencyIds
          ? _value._competencyIds
          : competencyIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      bloomLevel: null == bloomLevel
          ? _value.bloomLevel
          : bloomLevel // ignore: cast_nullable_to_non_nullable
              as BloomLevel,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as Difficulty,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as QuestionType,
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
      answerScheme: null == answerScheme
          ? _value.answerScheme
          : answerScheme // ignore: cast_nullable_to_non_nullable
              as AnswerScheme,
      estimatedTimeMinutes: null == estimatedTimeMinutes
          ? _value.estimatedTimeMinutes
          : estimatedTimeMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      language: null == language
          ? _value.language
          : language // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as QuestionSource,
      qualityScore: null == qualityScore
          ? _value.qualityScore
          : qualityScore // ignore: cast_nullable_to_non_nullable
              as double,
      tags: null == tags
          ? _value._tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      metadata: null == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
      diagramAssetId: freezed == diagramAssetId
          ? _value.diagramAssetId
          : diagramAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
      mapAssetId: freezed == mapAssetId
          ? _value.mapAssetId
          : mapAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
      graphAssetId: freezed == graphAssetId
          ? _value.graphAssetId
          : graphAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
      tableAssetId: freezed == tableAssetId
          ? _value.tableAssetId
          : tableAssetId // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionImpl implements _Question {
  const _$QuestionImpl(
      {required this.id,
      required this.questionBankId,
      required this.subject,
      required this.grade,
      required final List<String> chapterIds,
      required final List<String> competencyIds,
      @BloomLevelConverter() required this.bloomLevel,
      @DifficultyConverter() required this.difficulty,
      @QuestionTypeConverter() required this.type,
      required this.stem,
      required this.stemLatex,
      required final List<QuestionPart> parts,
      required this.answerScheme,
      required this.estimatedTimeMinutes,
      required this.marks,
      required this.language,
      @QuestionSourceConverter() required this.source,
      required this.qualityScore,
      required final List<String> tags,
      required this.createdAt,
      required this.updatedAt,
      final Map<String, dynamic> metadata = const {},
      this.diagramAssetId,
      this.mapAssetId,
      this.graphAssetId,
      this.tableAssetId})
      : _chapterIds = chapterIds,
        _competencyIds = competencyIds,
        _parts = parts,
        _tags = tags,
        _metadata = metadata;

  factory _$QuestionImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionImplFromJson(json);

  @override
  final String id;
  @override
  final String questionBankId;
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

  final List<String> _competencyIds;
  @override
  List<String> get competencyIds {
    if (_competencyIds is EqualUnmodifiableListView) return _competencyIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_competencyIds);
  }

  @override
  @BloomLevelConverter()
  final BloomLevel bloomLevel;
  @override
  @DifficultyConverter()
  final Difficulty difficulty;
  @override
  @QuestionTypeConverter()
  final QuestionType type;
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
  final AnswerScheme answerScheme;
  @override
  final int estimatedTimeMinutes;
  @override
  final int marks;
  @override
  final String language;
  @override
  @QuestionSourceConverter()
  final QuestionSource source;
  @override
  final double qualityScore;
  final List<String> _tags;
  @override
  List<String> get tags {
    if (_tags is EqualUnmodifiableListView) return _tags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_tags);
  }

  @override
  final DateTime createdAt;
  @override
  final DateTime updatedAt;
  final Map<String, dynamic> _metadata;
  @override
  @JsonKey()
  Map<String, dynamic> get metadata {
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_metadata);
  }

  @override
  final String? diagramAssetId;
  @override
  final String? mapAssetId;
  @override
  final String? graphAssetId;
  @override
  final String? tableAssetId;

  @override
  String toString() {
    return 'Question(id: $id, questionBankId: $questionBankId, subject: $subject, grade: $grade, chapterIds: $chapterIds, competencyIds: $competencyIds, bloomLevel: $bloomLevel, difficulty: $difficulty, type: $type, stem: $stem, stemLatex: $stemLatex, parts: $parts, answerScheme: $answerScheme, estimatedTimeMinutes: $estimatedTimeMinutes, marks: $marks, language: $language, source: $source, qualityScore: $qualityScore, tags: $tags, createdAt: $createdAt, updatedAt: $updatedAt, metadata: $metadata, diagramAssetId: $diagramAssetId, mapAssetId: $mapAssetId, graphAssetId: $graphAssetId, tableAssetId: $tableAssetId)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.questionBankId, questionBankId) ||
                other.questionBankId == questionBankId) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            const DeepCollectionEquality()
                .equals(other._chapterIds, _chapterIds) &&
            const DeepCollectionEquality()
                .equals(other._competencyIds, _competencyIds) &&
            (identical(other.bloomLevel, bloomLevel) ||
                other.bloomLevel == bloomLevel) &&
            (identical(other.difficulty, difficulty) ||
                other.difficulty == difficulty) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.stem, stem) || other.stem == stem) &&
            (identical(other.stemLatex, stemLatex) ||
                other.stemLatex == stemLatex) &&
            const DeepCollectionEquality().equals(other._parts, _parts) &&
            (identical(other.answerScheme, answerScheme) ||
                other.answerScheme == answerScheme) &&
            (identical(other.estimatedTimeMinutes, estimatedTimeMinutes) ||
                other.estimatedTimeMinutes == estimatedTimeMinutes) &&
            (identical(other.marks, marks) || other.marks == marks) &&
            (identical(other.language, language) ||
                other.language == language) &&
            (identical(other.source, source) || other.source == source) &&
            (identical(other.qualityScore, qualityScore) ||
                other.qualityScore == qualityScore) &&
            const DeepCollectionEquality().equals(other._tags, _tags) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.updatedAt, updatedAt) ||
                other.updatedAt == updatedAt) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata) &&
            (identical(other.diagramAssetId, diagramAssetId) ||
                other.diagramAssetId == diagramAssetId) &&
            (identical(other.mapAssetId, mapAssetId) ||
                other.mapAssetId == mapAssetId) &&
            (identical(other.graphAssetId, graphAssetId) ||
                other.graphAssetId == graphAssetId) &&
            (identical(other.tableAssetId, tableAssetId) ||
                other.tableAssetId == tableAssetId));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        id,
        questionBankId,
        subject,
        grade,
        const DeepCollectionEquality().hash(_chapterIds),
        const DeepCollectionEquality().hash(_competencyIds),
        bloomLevel,
        difficulty,
        type,
        stem,
        stemLatex,
        const DeepCollectionEquality().hash(_parts),
        answerScheme,
        estimatedTimeMinutes,
        marks,
        language,
        source,
        qualityScore,
        const DeepCollectionEquality().hash(_tags),
        createdAt,
        updatedAt,
        const DeepCollectionEquality().hash(_metadata),
        diagramAssetId,
        mapAssetId,
        graphAssetId,
        tableAssetId
      ]);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionImplCopyWith<_$QuestionImpl> get copyWith =>
      __$$QuestionImplCopyWithImpl<_$QuestionImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionImplToJson(
      this,
    );
  }
}

abstract class _Question implements Question {
  const factory _Question(
      {required final String id,
      required final String questionBankId,
      required final String subject,
      required final int grade,
      required final List<String> chapterIds,
      required final List<String> competencyIds,
      @BloomLevelConverter() required final BloomLevel bloomLevel,
      @DifficultyConverter() required final Difficulty difficulty,
      @QuestionTypeConverter() required final QuestionType type,
      required final String stem,
      required final String stemLatex,
      required final List<QuestionPart> parts,
      required final AnswerScheme answerScheme,
      required final int estimatedTimeMinutes,
      required final int marks,
      required final String language,
      @QuestionSourceConverter() required final QuestionSource source,
      required final double qualityScore,
      required final List<String> tags,
      required final DateTime createdAt,
      required final DateTime updatedAt,
      final Map<String, dynamic> metadata,
      final String? diagramAssetId,
      final String? mapAssetId,
      final String? graphAssetId,
      final String? tableAssetId}) = _$QuestionImpl;

  factory _Question.fromJson(Map<String, dynamic> json) =
      _$QuestionImpl.fromJson;

  @override
  String get id;
  @override
  String get questionBankId;
  @override
  String get subject;
  @override
  int get grade;
  @override
  List<String> get chapterIds;
  @override
  List<String> get competencyIds;
  @override
  @BloomLevelConverter()
  BloomLevel get bloomLevel;
  @override
  @DifficultyConverter()
  Difficulty get difficulty;
  @override
  @QuestionTypeConverter()
  QuestionType get type;
  @override
  String get stem;
  @override
  String get stemLatex;
  @override
  List<QuestionPart> get parts;
  @override
  AnswerScheme get answerScheme;
  @override
  int get estimatedTimeMinutes;
  @override
  int get marks;
  @override
  String get language;
  @override
  @QuestionSourceConverter()
  QuestionSource get source;
  @override
  double get qualityScore;
  @override
  List<String> get tags;
  @override
  DateTime get createdAt;
  @override
  DateTime get updatedAt;
  @override
  Map<String, dynamic> get metadata;
  @override
  String? get diagramAssetId;
  @override
  String? get mapAssetId;
  @override
  String? get graphAssetId;
  @override
  String? get tableAssetId;
  @override
  @JsonKey(ignore: true)
  _$$QuestionImplCopyWith<_$QuestionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionPart _$QuestionPartFromJson(Map<String, dynamic> json) {
  return _QuestionPart.fromJson(json);
}

/// @nodoc
mixin _$QuestionPart {
  String get id => throw _privateConstructorUsedError;
  int get partNumber => throw _privateConstructorUsedError;
  String get text => throw _privateConstructorUsedError;
  String get textLatex => throw _privateConstructorUsedError;
  int get marks => throw _privateConstructorUsedError;
  AnswerType get answerType => throw _privateConstructorUsedError;
  List<String>? get options => throw _privateConstructorUsedError;
  String? get correctOption => throw _privateConstructorUsedError;
  String? get expectedAnswer => throw _privateConstructorUsedError;
  String? get expectedAnswerLatex => throw _privateConstructorUsedError;
  List<String>? get keywords => throw _privateConstructorUsedError;
  List<String> get alternativeAnswers => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionPartCopyWith<QuestionPart> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionPartCopyWith<$Res> {
  factory $QuestionPartCopyWith(
          QuestionPart value, $Res Function(QuestionPart) then) =
      _$QuestionPartCopyWithImpl<$Res, QuestionPart>;
  @useResult
  $Res call(
      {String id,
      int partNumber,
      String text,
      String textLatex,
      int marks,
      AnswerType answerType,
      List<String>? options,
      String? correctOption,
      String? expectedAnswer,
      String? expectedAnswerLatex,
      List<String>? keywords,
      List<String> alternativeAnswers});
}

/// @nodoc
class _$QuestionPartCopyWithImpl<$Res, $Val extends QuestionPart>
    implements $QuestionPartCopyWith<$Res> {
  _$QuestionPartCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? partNumber = null,
    Object? text = null,
    Object? textLatex = null,
    Object? marks = null,
    Object? answerType = null,
    Object? options = freezed,
    Object? correctOption = freezed,
    Object? expectedAnswer = freezed,
    Object? expectedAnswerLatex = freezed,
    Object? keywords = freezed,
    Object? alternativeAnswers = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      partNumber: null == partNumber
          ? _value.partNumber
          : partNumber // ignore: cast_nullable_to_non_nullable
              as int,
      text: null == text
          ? _value.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      textLatex: null == textLatex
          ? _value.textLatex
          : textLatex // ignore: cast_nullable_to_non_nullable
              as String,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      answerType: null == answerType
          ? _value.answerType
          : answerType // ignore: cast_nullable_to_non_nullable
              as AnswerType,
      options: freezed == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      correctOption: freezed == correctOption
          ? _value.correctOption
          : correctOption // ignore: cast_nullable_to_non_nullable
              as String?,
      expectedAnswer: freezed == expectedAnswer
          ? _value.expectedAnswer
          : expectedAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      expectedAnswerLatex: freezed == expectedAnswerLatex
          ? _value.expectedAnswerLatex
          : expectedAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String?,
      keywords: freezed == keywords
          ? _value.keywords
          : keywords // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      alternativeAnswers: null == alternativeAnswers
          ? _value.alternativeAnswers
          : alternativeAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuestionPartImplCopyWith<$Res>
    implements $QuestionPartCopyWith<$Res> {
  factory _$$QuestionPartImplCopyWith(
          _$QuestionPartImpl value, $Res Function(_$QuestionPartImpl) then) =
      __$$QuestionPartImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      int partNumber,
      String text,
      String textLatex,
      int marks,
      AnswerType answerType,
      List<String>? options,
      String? correctOption,
      String? expectedAnswer,
      String? expectedAnswerLatex,
      List<String>? keywords,
      List<String> alternativeAnswers});
}

/// @nodoc
class __$$QuestionPartImplCopyWithImpl<$Res>
    extends _$QuestionPartCopyWithImpl<$Res, _$QuestionPartImpl>
    implements _$$QuestionPartImplCopyWith<$Res> {
  __$$QuestionPartImplCopyWithImpl(
      _$QuestionPartImpl _value, $Res Function(_$QuestionPartImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? partNumber = null,
    Object? text = null,
    Object? textLatex = null,
    Object? marks = null,
    Object? answerType = null,
    Object? options = freezed,
    Object? correctOption = freezed,
    Object? expectedAnswer = freezed,
    Object? expectedAnswerLatex = freezed,
    Object? keywords = freezed,
    Object? alternativeAnswers = null,
  }) {
    return _then(_$QuestionPartImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      partNumber: null == partNumber
          ? _value.partNumber
          : partNumber // ignore: cast_nullable_to_non_nullable
              as int,
      text: null == text
          ? _value.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      textLatex: null == textLatex
          ? _value.textLatex
          : textLatex // ignore: cast_nullable_to_non_nullable
              as String,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      answerType: null == answerType
          ? _value.answerType
          : answerType // ignore: cast_nullable_to_non_nullable
              as AnswerType,
      options: freezed == options
          ? _value._options
          : options // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      correctOption: freezed == correctOption
          ? _value.correctOption
          : correctOption // ignore: cast_nullable_to_non_nullable
              as String?,
      expectedAnswer: freezed == expectedAnswer
          ? _value.expectedAnswer
          : expectedAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      expectedAnswerLatex: freezed == expectedAnswerLatex
          ? _value.expectedAnswerLatex
          : expectedAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String?,
      keywords: freezed == keywords
          ? _value._keywords
          : keywords // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      alternativeAnswers: null == alternativeAnswers
          ? _value._alternativeAnswers
          : alternativeAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionPartImpl implements _QuestionPart {
  const _$QuestionPartImpl(
      {required this.id,
      required this.partNumber,
      required this.text,
      required this.textLatex,
      required this.marks,
      required this.answerType,
      final List<String>? options,
      this.correctOption,
      this.expectedAnswer,
      this.expectedAnswerLatex,
      final List<String>? keywords,
      final List<String> alternativeAnswers = const []})
      : _options = options,
        _keywords = keywords,
        _alternativeAnswers = alternativeAnswers;

  factory _$QuestionPartImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionPartImplFromJson(json);

  @override
  final String id;
  @override
  final int partNumber;
  @override
  final String text;
  @override
  final String textLatex;
  @override
  final int marks;
  @override
  final AnswerType answerType;
  final List<String>? _options;
  @override
  List<String>? get options {
    final value = _options;
    if (value == null) return null;
    if (_options is EqualUnmodifiableListView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  final String? correctOption;
  @override
  final String? expectedAnswer;
  @override
  final String? expectedAnswerLatex;
  final List<String>? _keywords;
  @override
  List<String>? get keywords {
    final value = _keywords;
    if (value == null) return null;
    if (_keywords is EqualUnmodifiableListView) return _keywords;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<String> _alternativeAnswers;
  @override
  @JsonKey()
  List<String> get alternativeAnswers {
    if (_alternativeAnswers is EqualUnmodifiableListView)
      return _alternativeAnswers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_alternativeAnswers);
  }

  @override
  String toString() {
    return 'QuestionPart(id: $id, partNumber: $partNumber, text: $text, textLatex: $textLatex, marks: $marks, answerType: $answerType, options: $options, correctOption: $correctOption, expectedAnswer: $expectedAnswer, expectedAnswerLatex: $expectedAnswerLatex, keywords: $keywords, alternativeAnswers: $alternativeAnswers)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionPartImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.partNumber, partNumber) ||
                other.partNumber == partNumber) &&
            (identical(other.text, text) || other.text == text) &&
            (identical(other.textLatex, textLatex) ||
                other.textLatex == textLatex) &&
            (identical(other.marks, marks) || other.marks == marks) &&
            (identical(other.answerType, answerType) ||
                other.answerType == answerType) &&
            const DeepCollectionEquality().equals(other._options, _options) &&
            (identical(other.correctOption, correctOption) ||
                other.correctOption == correctOption) &&
            (identical(other.expectedAnswer, expectedAnswer) ||
                other.expectedAnswer == expectedAnswer) &&
            (identical(other.expectedAnswerLatex, expectedAnswerLatex) ||
                other.expectedAnswerLatex == expectedAnswerLatex) &&
            const DeepCollectionEquality().equals(other._keywords, _keywords) &&
            const DeepCollectionEquality()
                .equals(other._alternativeAnswers, _alternativeAnswers));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      partNumber,
      text,
      textLatex,
      marks,
      answerType,
      const DeepCollectionEquality().hash(_options),
      correctOption,
      expectedAnswer,
      expectedAnswerLatex,
      const DeepCollectionEquality().hash(_keywords),
      const DeepCollectionEquality().hash(_alternativeAnswers));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionPartImplCopyWith<_$QuestionPartImpl> get copyWith =>
      __$$QuestionPartImplCopyWithImpl<_$QuestionPartImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionPartImplToJson(
      this,
    );
  }
}

abstract class _QuestionPart implements QuestionPart {
  const factory _QuestionPart(
      {required final String id,
      required final int partNumber,
      required final String text,
      required final String textLatex,
      required final int marks,
      required final AnswerType answerType,
      final List<String>? options,
      final String? correctOption,
      final String? expectedAnswer,
      final String? expectedAnswerLatex,
      final List<String>? keywords,
      final List<String> alternativeAnswers}) = _$QuestionPartImpl;

  factory _QuestionPart.fromJson(Map<String, dynamic> json) =
      _$QuestionPartImpl.fromJson;

  @override
  String get id;
  @override
  int get partNumber;
  @override
  String get text;
  @override
  String get textLatex;
  @override
  int get marks;
  @override
  AnswerType get answerType;
  @override
  List<String>? get options;
  @override
  String? get correctOption;
  @override
  String? get expectedAnswer;
  @override
  String? get expectedAnswerLatex;
  @override
  List<String>? get keywords;
  @override
  List<String> get alternativeAnswers;
  @override
  @JsonKey(ignore: true)
  _$$QuestionPartImplCopyWith<_$QuestionPartImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AnswerScheme _$AnswerSchemeFromJson(Map<String, dynamic> json) {
  return _AnswerScheme.fromJson(json);
}

/// @nodoc
mixin _$AnswerScheme {
  int get totalMarks => throw _privateConstructorUsedError;
  List<MarkingPoint> get markingPoints => throw _privateConstructorUsedError;
  List<RubricLevel> get rubricLevels => throw _privateConstructorUsedError;
  List<String> get commonErrors => throw _privateConstructorUsedError;
  List<String> get alternativeAnswers => throw _privateConstructorUsedError;
  String get modelAnswer => throw _privateConstructorUsedError;
  String get modelAnswerLatex => throw _privateConstructorUsedError;
  bool get hasPartialCredit => throw _privateConstructorUsedError;
  Map<String, dynamic> get metadata => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AnswerSchemeCopyWith<AnswerScheme> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AnswerSchemeCopyWith<$Res> {
  factory $AnswerSchemeCopyWith(
          AnswerScheme value, $Res Function(AnswerScheme) then) =
      _$AnswerSchemeCopyWithImpl<$Res, AnswerScheme>;
  @useResult
  $Res call(
      {int totalMarks,
      List<MarkingPoint> markingPoints,
      List<RubricLevel> rubricLevels,
      List<String> commonErrors,
      List<String> alternativeAnswers,
      String modelAnswer,
      String modelAnswerLatex,
      bool hasPartialCredit,
      Map<String, dynamic> metadata});
}

/// @nodoc
class _$AnswerSchemeCopyWithImpl<$Res, $Val extends AnswerScheme>
    implements $AnswerSchemeCopyWith<$Res> {
  _$AnswerSchemeCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalMarks = null,
    Object? markingPoints = null,
    Object? rubricLevels = null,
    Object? commonErrors = null,
    Object? alternativeAnswers = null,
    Object? modelAnswer = null,
    Object? modelAnswerLatex = null,
    Object? hasPartialCredit = null,
    Object? metadata = null,
  }) {
    return _then(_value.copyWith(
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      markingPoints: null == markingPoints
          ? _value.markingPoints
          : markingPoints // ignore: cast_nullable_to_non_nullable
              as List<MarkingPoint>,
      rubricLevels: null == rubricLevels
          ? _value.rubricLevels
          : rubricLevels // ignore: cast_nullable_to_non_nullable
              as List<RubricLevel>,
      commonErrors: null == commonErrors
          ? _value.commonErrors
          : commonErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      alternativeAnswers: null == alternativeAnswers
          ? _value.alternativeAnswers
          : alternativeAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
      modelAnswer: null == modelAnswer
          ? _value.modelAnswer
          : modelAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      modelAnswerLatex: null == modelAnswerLatex
          ? _value.modelAnswerLatex
          : modelAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      hasPartialCredit: null == hasPartialCredit
          ? _value.hasPartialCredit
          : hasPartialCredit // ignore: cast_nullable_to_non_nullable
              as bool,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AnswerSchemeImplCopyWith<$Res>
    implements $AnswerSchemeCopyWith<$Res> {
  factory _$$AnswerSchemeImplCopyWith(
          _$AnswerSchemeImpl value, $Res Function(_$AnswerSchemeImpl) then) =
      __$$AnswerSchemeImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int totalMarks,
      List<MarkingPoint> markingPoints,
      List<RubricLevel> rubricLevels,
      List<String> commonErrors,
      List<String> alternativeAnswers,
      String modelAnswer,
      String modelAnswerLatex,
      bool hasPartialCredit,
      Map<String, dynamic> metadata});
}

/// @nodoc
class __$$AnswerSchemeImplCopyWithImpl<$Res>
    extends _$AnswerSchemeCopyWithImpl<$Res, _$AnswerSchemeImpl>
    implements _$$AnswerSchemeImplCopyWith<$Res> {
  __$$AnswerSchemeImplCopyWithImpl(
      _$AnswerSchemeImpl _value, $Res Function(_$AnswerSchemeImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalMarks = null,
    Object? markingPoints = null,
    Object? rubricLevels = null,
    Object? commonErrors = null,
    Object? alternativeAnswers = null,
    Object? modelAnswer = null,
    Object? modelAnswerLatex = null,
    Object? hasPartialCredit = null,
    Object? metadata = null,
  }) {
    return _then(_$AnswerSchemeImpl(
      totalMarks: null == totalMarks
          ? _value.totalMarks
          : totalMarks // ignore: cast_nullable_to_non_nullable
              as int,
      markingPoints: null == markingPoints
          ? _value._markingPoints
          : markingPoints // ignore: cast_nullable_to_non_nullable
              as List<MarkingPoint>,
      rubricLevels: null == rubricLevels
          ? _value._rubricLevels
          : rubricLevels // ignore: cast_nullable_to_non_nullable
              as List<RubricLevel>,
      commonErrors: null == commonErrors
          ? _value._commonErrors
          : commonErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      alternativeAnswers: null == alternativeAnswers
          ? _value._alternativeAnswers
          : alternativeAnswers // ignore: cast_nullable_to_non_nullable
              as List<String>,
      modelAnswer: null == modelAnswer
          ? _value.modelAnswer
          : modelAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      modelAnswerLatex: null == modelAnswerLatex
          ? _value.modelAnswerLatex
          : modelAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      hasPartialCredit: null == hasPartialCredit
          ? _value.hasPartialCredit
          : hasPartialCredit // ignore: cast_nullable_to_non_nullable
              as bool,
      metadata: null == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AnswerSchemeImpl implements _AnswerScheme {
  const _$AnswerSchemeImpl(
      {required this.totalMarks,
      required final List<MarkingPoint> markingPoints,
      required final List<RubricLevel> rubricLevels,
      required final List<String> commonErrors,
      required final List<String> alternativeAnswers,
      required this.modelAnswer,
      required this.modelAnswerLatex,
      this.hasPartialCredit = false,
      final Map<String, dynamic> metadata = const {}})
      : _markingPoints = markingPoints,
        _rubricLevels = rubricLevels,
        _commonErrors = commonErrors,
        _alternativeAnswers = alternativeAnswers,
        _metadata = metadata;

  factory _$AnswerSchemeImpl.fromJson(Map<String, dynamic> json) =>
      _$$AnswerSchemeImplFromJson(json);

  @override
  final int totalMarks;
  final List<MarkingPoint> _markingPoints;
  @override
  List<MarkingPoint> get markingPoints {
    if (_markingPoints is EqualUnmodifiableListView) return _markingPoints;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_markingPoints);
  }

  final List<RubricLevel> _rubricLevels;
  @override
  List<RubricLevel> get rubricLevels {
    if (_rubricLevels is EqualUnmodifiableListView) return _rubricLevels;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_rubricLevels);
  }

  final List<String> _commonErrors;
  @override
  List<String> get commonErrors {
    if (_commonErrors is EqualUnmodifiableListView) return _commonErrors;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_commonErrors);
  }

  final List<String> _alternativeAnswers;
  @override
  List<String> get alternativeAnswers {
    if (_alternativeAnswers is EqualUnmodifiableListView)
      return _alternativeAnswers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_alternativeAnswers);
  }

  @override
  final String modelAnswer;
  @override
  final String modelAnswerLatex;
  @override
  @JsonKey()
  final bool hasPartialCredit;
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
    return 'AnswerScheme(totalMarks: $totalMarks, markingPoints: $markingPoints, rubricLevels: $rubricLevels, commonErrors: $commonErrors, alternativeAnswers: $alternativeAnswers, modelAnswer: $modelAnswer, modelAnswerLatex: $modelAnswerLatex, hasPartialCredit: $hasPartialCredit, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AnswerSchemeImpl &&
            (identical(other.totalMarks, totalMarks) ||
                other.totalMarks == totalMarks) &&
            const DeepCollectionEquality()
                .equals(other._markingPoints, _markingPoints) &&
            const DeepCollectionEquality()
                .equals(other._rubricLevels, _rubricLevels) &&
            const DeepCollectionEquality()
                .equals(other._commonErrors, _commonErrors) &&
            const DeepCollectionEquality()
                .equals(other._alternativeAnswers, _alternativeAnswers) &&
            (identical(other.modelAnswer, modelAnswer) ||
                other.modelAnswer == modelAnswer) &&
            (identical(other.modelAnswerLatex, modelAnswerLatex) ||
                other.modelAnswerLatex == modelAnswerLatex) &&
            (identical(other.hasPartialCredit, hasPartialCredit) ||
                other.hasPartialCredit == hasPartialCredit) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalMarks,
      const DeepCollectionEquality().hash(_markingPoints),
      const DeepCollectionEquality().hash(_rubricLevels),
      const DeepCollectionEquality().hash(_commonErrors),
      const DeepCollectionEquality().hash(_alternativeAnswers),
      modelAnswer,
      modelAnswerLatex,
      hasPartialCredit,
      const DeepCollectionEquality().hash(_metadata));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AnswerSchemeImplCopyWith<_$AnswerSchemeImpl> get copyWith =>
      __$$AnswerSchemeImplCopyWithImpl<_$AnswerSchemeImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AnswerSchemeImplToJson(
      this,
    );
  }
}

abstract class _AnswerScheme implements AnswerScheme {
  const factory _AnswerScheme(
      {required final int totalMarks,
      required final List<MarkingPoint> markingPoints,
      required final List<RubricLevel> rubricLevels,
      required final List<String> commonErrors,
      required final List<String> alternativeAnswers,
      required final String modelAnswer,
      required final String modelAnswerLatex,
      final bool hasPartialCredit,
      final Map<String, dynamic> metadata}) = _$AnswerSchemeImpl;

  factory _AnswerScheme.fromJson(Map<String, dynamic> json) =
      _$AnswerSchemeImpl.fromJson;

  @override
  int get totalMarks;
  @override
  List<MarkingPoint> get markingPoints;
  @override
  List<RubricLevel> get rubricLevels;
  @override
  List<String> get commonErrors;
  @override
  List<String> get alternativeAnswers;
  @override
  String get modelAnswer;
  @override
  String get modelAnswerLatex;
  @override
  bool get hasPartialCredit;
  @override
  Map<String, dynamic> get metadata;
  @override
  @JsonKey(ignore: true)
  _$$AnswerSchemeImplCopyWith<_$AnswerSchemeImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MarkingPoint _$MarkingPointFromJson(Map<String, dynamic> json) {
  return _MarkingPoint.fromJson(json);
}

/// @nodoc
mixin _$MarkingPoint {
  String get id => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  int get marks => throw _privateConstructorUsedError;
  String get keyword => throw _privateConstructorUsedError;
  bool get isRequired => throw _privateConstructorUsedError;
  List<String> get synonyms => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MarkingPointCopyWith<MarkingPoint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MarkingPointCopyWith<$Res> {
  factory $MarkingPointCopyWith(
          MarkingPoint value, $Res Function(MarkingPoint) then) =
      _$MarkingPointCopyWithImpl<$Res, MarkingPoint>;
  @useResult
  $Res call(
      {String id,
      String description,
      int marks,
      String keyword,
      bool isRequired,
      List<String> synonyms});
}

/// @nodoc
class _$MarkingPointCopyWithImpl<$Res, $Val extends MarkingPoint>
    implements $MarkingPointCopyWith<$Res> {
  _$MarkingPointCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? description = null,
    Object? marks = null,
    Object? keyword = null,
    Object? isRequired = null,
    Object? synonyms = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      keyword: null == keyword
          ? _value.keyword
          : keyword // ignore: cast_nullable_to_non_nullable
              as String,
      isRequired: null == isRequired
          ? _value.isRequired
          : isRequired // ignore: cast_nullable_to_non_nullable
              as bool,
      synonyms: null == synonyms
          ? _value.synonyms
          : synonyms // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MarkingPointImplCopyWith<$Res>
    implements $MarkingPointCopyWith<$Res> {
  factory _$$MarkingPointImplCopyWith(
          _$MarkingPointImpl value, $Res Function(_$MarkingPointImpl) then) =
      __$$MarkingPointImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String description,
      int marks,
      String keyword,
      bool isRequired,
      List<String> synonyms});
}

/// @nodoc
class __$$MarkingPointImplCopyWithImpl<$Res>
    extends _$MarkingPointCopyWithImpl<$Res, _$MarkingPointImpl>
    implements _$$MarkingPointImplCopyWith<$Res> {
  __$$MarkingPointImplCopyWithImpl(
      _$MarkingPointImpl _value, $Res Function(_$MarkingPointImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? description = null,
    Object? marks = null,
    Object? keyword = null,
    Object? isRequired = null,
    Object? synonyms = null,
  }) {
    return _then(_$MarkingPointImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      marks: null == marks
          ? _value.marks
          : marks // ignore: cast_nullable_to_non_nullable
              as int,
      keyword: null == keyword
          ? _value.keyword
          : keyword // ignore: cast_nullable_to_non_nullable
              as String,
      isRequired: null == isRequired
          ? _value.isRequired
          : isRequired // ignore: cast_nullable_to_non_nullable
              as bool,
      synonyms: null == synonyms
          ? _value._synonyms
          : synonyms // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MarkingPointImpl implements _MarkingPoint {
  const _$MarkingPointImpl(
      {required this.id,
      required this.description,
      required this.marks,
      required this.keyword,
      required this.isRequired,
      final List<String> synonyms = const []})
      : _synonyms = synonyms;

  factory _$MarkingPointImpl.fromJson(Map<String, dynamic> json) =>
      _$$MarkingPointImplFromJson(json);

  @override
  final String id;
  @override
  final String description;
  @override
  final int marks;
  @override
  final String keyword;
  @override
  final bool isRequired;
  final List<String> _synonyms;
  @override
  @JsonKey()
  List<String> get synonyms {
    if (_synonyms is EqualUnmodifiableListView) return _synonyms;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_synonyms);
  }

  @override
  String toString() {
    return 'MarkingPoint(id: $id, description: $description, marks: $marks, keyword: $keyword, isRequired: $isRequired, synonyms: $synonyms)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MarkingPointImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.marks, marks) || other.marks == marks) &&
            (identical(other.keyword, keyword) || other.keyword == keyword) &&
            (identical(other.isRequired, isRequired) ||
                other.isRequired == isRequired) &&
            const DeepCollectionEquality().equals(other._synonyms, _synonyms));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, id, description, marks, keyword,
      isRequired, const DeepCollectionEquality().hash(_synonyms));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MarkingPointImplCopyWith<_$MarkingPointImpl> get copyWith =>
      __$$MarkingPointImplCopyWithImpl<_$MarkingPointImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MarkingPointImplToJson(
      this,
    );
  }
}

abstract class _MarkingPoint implements MarkingPoint {
  const factory _MarkingPoint(
      {required final String id,
      required final String description,
      required final int marks,
      required final String keyword,
      required final bool isRequired,
      final List<String> synonyms}) = _$MarkingPointImpl;

  factory _MarkingPoint.fromJson(Map<String, dynamic> json) =
      _$MarkingPointImpl.fromJson;

  @override
  String get id;
  @override
  String get description;
  @override
  int get marks;
  @override
  String get keyword;
  @override
  bool get isRequired;
  @override
  List<String> get synonyms;
  @override
  @JsonKey(ignore: true)
  _$$MarkingPointImplCopyWith<_$MarkingPointImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RubricLevel _$RubricLevelFromJson(Map<String, dynamic> json) {
  return _RubricLevel.fromJson(json);
}

/// @nodoc
mixin _$RubricLevel {
  int get level => throw _privateConstructorUsedError;
  String get label => throw _privateConstructorUsedError;
  int get minMarks => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $RubricLevelCopyWith<RubricLevel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RubricLevelCopyWith<$Res> {
  factory $RubricLevelCopyWith(
          RubricLevel value, $Res Function(RubricLevel) then) =
      _$RubricLevelCopyWithImpl<$Res, RubricLevel>;
  @useResult
  $Res call(
      {int level,
      String label,
      int minMarks,
      int maxMarks,
      String description});
}

/// @nodoc
class _$RubricLevelCopyWithImpl<$Res, $Val extends RubricLevel>
    implements $RubricLevelCopyWith<$Res> {
  _$RubricLevelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? label = null,
    Object? minMarks = null,
    Object? maxMarks = null,
    Object? description = null,
  }) {
    return _then(_value.copyWith(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as int,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      minMarks: null == minMarks
          ? _value.minMarks
          : minMarks // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RubricLevelImplCopyWith<$Res>
    implements $RubricLevelCopyWith<$Res> {
  factory _$$RubricLevelImplCopyWith(
          _$RubricLevelImpl value, $Res Function(_$RubricLevelImpl) then) =
      __$$RubricLevelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int level,
      String label,
      int minMarks,
      int maxMarks,
      String description});
}

/// @nodoc
class __$$RubricLevelImplCopyWithImpl<$Res>
    extends _$RubricLevelCopyWithImpl<$Res, _$RubricLevelImpl>
    implements _$$RubricLevelImplCopyWith<$Res> {
  __$$RubricLevelImplCopyWithImpl(
      _$RubricLevelImpl _value, $Res Function(_$RubricLevelImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? label = null,
    Object? minMarks = null,
    Object? maxMarks = null,
    Object? description = null,
  }) {
    return _then(_$RubricLevelImpl(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as int,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      minMarks: null == minMarks
          ? _value.minMarks
          : minMarks // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RubricLevelImpl implements _RubricLevel {
  const _$RubricLevelImpl(
      {required this.level,
      required this.label,
      required this.minMarks,
      required this.maxMarks,
      required this.description});

  factory _$RubricLevelImpl.fromJson(Map<String, dynamic> json) =>
      _$$RubricLevelImplFromJson(json);

  @override
  final int level;
  @override
  final String label;
  @override
  final int minMarks;
  @override
  final int maxMarks;
  @override
  final String description;

  @override
  String toString() {
    return 'RubricLevel(level: $level, label: $label, minMarks: $minMarks, maxMarks: $maxMarks, description: $description)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RubricLevelImpl &&
            (identical(other.level, level) || other.level == level) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.minMarks, minMarks) ||
                other.minMarks == minMarks) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.description, description) ||
                other.description == description));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, level, label, minMarks, maxMarks, description);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RubricLevelImplCopyWith<_$RubricLevelImpl> get copyWith =>
      __$$RubricLevelImplCopyWithImpl<_$RubricLevelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RubricLevelImplToJson(
      this,
    );
  }
}

abstract class _RubricLevel implements RubricLevel {
  const factory _RubricLevel(
      {required final int level,
      required final String label,
      required final int minMarks,
      required final int maxMarks,
      required final String description}) = _$RubricLevelImpl;

  factory _RubricLevel.fromJson(Map<String, dynamic> json) =
      _$RubricLevelImpl.fromJson;

  @override
  int get level;
  @override
  String get label;
  @override
  int get minMarks;
  @override
  int get maxMarks;
  @override
  String get description;
  @override
  @JsonKey(ignore: true)
  _$$RubricLevelImplCopyWith<_$RubricLevelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionOptimizationRequest _$QuestionOptimizationRequestFromJson(
    Map<String, dynamic> json) {
  return _QuestionOptimizationRequest.fromJson(json);
}

/// @nodoc
mixin _$QuestionOptimizationRequest {
  List<Question> get candidates => throw _privateConstructorUsedError;
  Blueprint get blueprint => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionOptimizationRequestCopyWith<QuestionOptimizationRequest>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionOptimizationRequestCopyWith<$Res> {
  factory $QuestionOptimizationRequestCopyWith(
          QuestionOptimizationRequest value,
          $Res Function(QuestionOptimizationRequest) then) =
      _$QuestionOptimizationRequestCopyWithImpl<$Res,
          QuestionOptimizationRequest>;
  @useResult
  $Res call({List<Question> candidates, Blueprint blueprint});

  $BlueprintCopyWith<$Res> get blueprint;
}

/// @nodoc
class _$QuestionOptimizationRequestCopyWithImpl<$Res,
        $Val extends QuestionOptimizationRequest>
    implements $QuestionOptimizationRequestCopyWith<$Res> {
  _$QuestionOptimizationRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? candidates = null,
    Object? blueprint = null,
  }) {
    return _then(_value.copyWith(
      candidates: null == candidates
          ? _value.candidates
          : candidates // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      blueprint: null == blueprint
          ? _value.blueprint
          : blueprint // ignore: cast_nullable_to_non_nullable
              as Blueprint,
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
abstract class _$$QuestionOptimizationRequestImplCopyWith<$Res>
    implements $QuestionOptimizationRequestCopyWith<$Res> {
  factory _$$QuestionOptimizationRequestImplCopyWith(
          _$QuestionOptimizationRequestImpl value,
          $Res Function(_$QuestionOptimizationRequestImpl) then) =
      __$$QuestionOptimizationRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({List<Question> candidates, Blueprint blueprint});

  @override
  $BlueprintCopyWith<$Res> get blueprint;
}

/// @nodoc
class __$$QuestionOptimizationRequestImplCopyWithImpl<$Res>
    extends _$QuestionOptimizationRequestCopyWithImpl<$Res,
        _$QuestionOptimizationRequestImpl>
    implements _$$QuestionOptimizationRequestImplCopyWith<$Res> {
  __$$QuestionOptimizationRequestImplCopyWithImpl(
      _$QuestionOptimizationRequestImpl _value,
      $Res Function(_$QuestionOptimizationRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? candidates = null,
    Object? blueprint = null,
  }) {
    return _then(_$QuestionOptimizationRequestImpl(
      candidates: null == candidates
          ? _value._candidates
          : candidates // ignore: cast_nullable_to_non_nullable
              as List<Question>,
      blueprint: null == blueprint
          ? _value.blueprint
          : blueprint // ignore: cast_nullable_to_non_nullable
              as Blueprint,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionOptimizationRequestImpl
    implements _QuestionOptimizationRequest {
  const _$QuestionOptimizationRequestImpl(
      {required final List<Question> candidates, required this.blueprint})
      : _candidates = candidates;

  factory _$QuestionOptimizationRequestImpl.fromJson(
          Map<String, dynamic> json) =>
      _$$QuestionOptimizationRequestImplFromJson(json);

  final List<Question> _candidates;
  @override
  List<Question> get candidates {
    if (_candidates is EqualUnmodifiableListView) return _candidates;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_candidates);
  }

  @override
  final Blueprint blueprint;

  @override
  String toString() {
    return 'QuestionOptimizationRequest(candidates: $candidates, blueprint: $blueprint)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionOptimizationRequestImpl &&
            const DeepCollectionEquality()
                .equals(other._candidates, _candidates) &&
            (identical(other.blueprint, blueprint) ||
                other.blueprint == blueprint));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, const DeepCollectionEquality().hash(_candidates), blueprint);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionOptimizationRequestImplCopyWith<_$QuestionOptimizationRequestImpl>
      get copyWith => __$$QuestionOptimizationRequestImplCopyWithImpl<
          _$QuestionOptimizationRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionOptimizationRequestImplToJson(
      this,
    );
  }
}

abstract class _QuestionOptimizationRequest
    implements QuestionOptimizationRequest {
  const factory _QuestionOptimizationRequest(
      {required final List<Question> candidates,
      required final Blueprint blueprint}) = _$QuestionOptimizationRequestImpl;

  factory _QuestionOptimizationRequest.fromJson(Map<String, dynamic> json) =
      _$QuestionOptimizationRequestImpl.fromJson;

  @override
  List<Question> get candidates;
  @override
  Blueprint get blueprint;
  @override
  @JsonKey(ignore: true)
  _$$QuestionOptimizationRequestImplCopyWith<_$QuestionOptimizationRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}
