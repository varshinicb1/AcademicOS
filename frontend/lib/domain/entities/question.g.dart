// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'question.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$QuestionImpl _$$QuestionImplFromJson(Map<String, dynamic> json) =>
    _$QuestionImpl(
      id: json['id'] as String,
      questionBankId: json['questionBankId'] as String,
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      chapterIds: (json['chapterIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      competencyIds: (json['competencyIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      bloomLevel:
          const BloomLevelConverter().fromJson(json['bloomLevel'] as String),
      difficulty:
          const DifficultyConverter().fromJson(json['difficulty'] as String),
      type: const QuestionTypeConverter().fromJson(json['type'] as String),
      stem: json['stem'] as String,
      stemLatex: json['stemLatex'] as String,
      parts: (json['parts'] as List<dynamic>)
          .map((e) => QuestionPart.fromJson(e as Map<String, dynamic>))
          .toList(),
      answerScheme:
          AnswerScheme.fromJson(json['answerScheme'] as Map<String, dynamic>),
      estimatedTimeMinutes: (json['estimatedTimeMinutes'] as num).toInt(),
      marks: (json['marks'] as num).toInt(),
      language: json['language'] as String,
      source:
          const QuestionSourceConverter().fromJson(json['source'] as String),
      qualityScore: (json['qualityScore'] as num).toDouble(),
      tags: (json['tags'] as List<dynamic>).map((e) => e as String).toList(),
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      metadata: json['metadata'] as Map<String, dynamic>? ?? const {},
      diagramAssetId: json['diagramAssetId'] as String?,
      mapAssetId: json['mapAssetId'] as String?,
      graphAssetId: json['graphAssetId'] as String?,
      tableAssetId: json['tableAssetId'] as String?,
    );

Map<String, dynamic> _$$QuestionImplToJson(_$QuestionImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'questionBankId': instance.questionBankId,
      'subject': instance.subject,
      'grade': instance.grade,
      'chapterIds': instance.chapterIds,
      'competencyIds': instance.competencyIds,
      'bloomLevel': const BloomLevelConverter().toJson(instance.bloomLevel),
      'difficulty': const DifficultyConverter().toJson(instance.difficulty),
      'type': const QuestionTypeConverter().toJson(instance.type),
      'stem': instance.stem,
      'stemLatex': instance.stemLatex,
      'parts': instance.parts,
      'answerScheme': instance.answerScheme,
      'estimatedTimeMinutes': instance.estimatedTimeMinutes,
      'marks': instance.marks,
      'language': instance.language,
      'source': const QuestionSourceConverter().toJson(instance.source),
      'qualityScore': instance.qualityScore,
      'tags': instance.tags,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
      'metadata': instance.metadata,
      'diagramAssetId': instance.diagramAssetId,
      'mapAssetId': instance.mapAssetId,
      'graphAssetId': instance.graphAssetId,
      'tableAssetId': instance.tableAssetId,
    };

_$QuestionPartImpl _$$QuestionPartImplFromJson(Map<String, dynamic> json) =>
    _$QuestionPartImpl(
      id: json['id'] as String,
      partNumber: (json['partNumber'] as num).toInt(),
      text: json['text'] as String,
      textLatex: json['textLatex'] as String,
      marks: (json['marks'] as num).toInt(),
      answerType: $enumDecode(_$AnswerTypeEnumMap, json['answerType']),
      options:
          (json['options'] as List<dynamic>?)?.map((e) => e as String).toList(),
      correctOption: json['correctOption'] as String?,
      expectedAnswer: json['expectedAnswer'] as String?,
      expectedAnswerLatex: json['expectedAnswerLatex'] as String?,
      keywords: (json['keywords'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      alternativeAnswers: (json['alternativeAnswers'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$QuestionPartImplToJson(_$QuestionPartImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'partNumber': instance.partNumber,
      'text': instance.text,
      'textLatex': instance.textLatex,
      'marks': instance.marks,
      'answerType': _$AnswerTypeEnumMap[instance.answerType]!,
      'options': instance.options,
      'correctOption': instance.correctOption,
      'expectedAnswer': instance.expectedAnswer,
      'expectedAnswerLatex': instance.expectedAnswerLatex,
      'keywords': instance.keywords,
      'alternativeAnswers': instance.alternativeAnswers,
    };

const _$AnswerTypeEnumMap = {
  AnswerType.singleChoice: 'singleChoice',
  AnswerType.multipleChoice: 'multipleChoice',
  AnswerType.textShort: 'textShort',
  AnswerType.textLong: 'textLong',
  AnswerType.numeric: 'numeric',
  AnswerType.diagram: 'diagram',
  AnswerType.map: 'map',
  AnswerType.graph: 'graph',
  AnswerType.table: 'table',
};

_$AnswerSchemeImpl _$$AnswerSchemeImplFromJson(Map<String, dynamic> json) =>
    _$AnswerSchemeImpl(
      totalMarks: (json['totalMarks'] as num).toInt(),
      markingPoints: (json['markingPoints'] as List<dynamic>)
          .map((e) => MarkingPoint.fromJson(e as Map<String, dynamic>))
          .toList(),
      rubricLevels: (json['rubricLevels'] as List<dynamic>)
          .map((e) => RubricLevel.fromJson(e as Map<String, dynamic>))
          .toList(),
      commonErrors: (json['commonErrors'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      alternativeAnswers: (json['alternativeAnswers'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      modelAnswer: json['modelAnswer'] as String,
      modelAnswerLatex: json['modelAnswerLatex'] as String,
      hasPartialCredit: json['hasPartialCredit'] as bool? ?? false,
      metadata: json['metadata'] as Map<String, dynamic>? ?? const {},
    );

Map<String, dynamic> _$$AnswerSchemeImplToJson(_$AnswerSchemeImpl instance) =>
    <String, dynamic>{
      'totalMarks': instance.totalMarks,
      'markingPoints': instance.markingPoints,
      'rubricLevels': instance.rubricLevels,
      'commonErrors': instance.commonErrors,
      'alternativeAnswers': instance.alternativeAnswers,
      'modelAnswer': instance.modelAnswer,
      'modelAnswerLatex': instance.modelAnswerLatex,
      'hasPartialCredit': instance.hasPartialCredit,
      'metadata': instance.metadata,
    };

_$MarkingPointImpl _$$MarkingPointImplFromJson(Map<String, dynamic> json) =>
    _$MarkingPointImpl(
      id: json['id'] as String,
      description: json['description'] as String,
      marks: (json['marks'] as num).toInt(),
      keyword: json['keyword'] as String,
      isRequired: json['isRequired'] as bool,
      synonyms: (json['synonyms'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$MarkingPointImplToJson(_$MarkingPointImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'description': instance.description,
      'marks': instance.marks,
      'keyword': instance.keyword,
      'isRequired': instance.isRequired,
      'synonyms': instance.synonyms,
    };

_$RubricLevelImpl _$$RubricLevelImplFromJson(Map<String, dynamic> json) =>
    _$RubricLevelImpl(
      level: (json['level'] as num).toInt(),
      label: json['label'] as String,
      minMarks: (json['minMarks'] as num).toInt(),
      maxMarks: (json['maxMarks'] as num).toInt(),
      description: json['description'] as String,
    );

Map<String, dynamic> _$$RubricLevelImplToJson(_$RubricLevelImpl instance) =>
    <String, dynamic>{
      'level': instance.level,
      'label': instance.label,
      'minMarks': instance.minMarks,
      'maxMarks': instance.maxMarks,
      'description': instance.description,
    };

_$QuestionOptimizationRequestImpl _$$QuestionOptimizationRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionOptimizationRequestImpl(
      candidates: (json['candidates'] as List<dynamic>)
          .map((e) => Question.fromJson(e as Map<String, dynamic>))
          .toList(),
      blueprint: Blueprint.fromJson(json['blueprint'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$QuestionOptimizationRequestImplToJson(
        _$QuestionOptimizationRequestImpl instance) =>
    <String, dynamic>{
      'candidates': instance.candidates,
      'blueprint': instance.blueprint,
    };
