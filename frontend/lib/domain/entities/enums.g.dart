// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'enums.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DifficultyDistributionImpl _$$DifficultyDistributionImplFromJson(
        Map<String, dynamic> json) =>
    _$DifficultyDistributionImpl(
      easy: (json['easy'] as num).toDouble(),
      medium: (json['medium'] as num).toDouble(),
      hard: (json['hard'] as num).toDouble(),
    );

Map<String, dynamic> _$$DifficultyDistributionImplToJson(
        _$DifficultyDistributionImpl instance) =>
    <String, dynamic>{
      'easy': instance.easy,
      'medium': instance.medium,
      'hard': instance.hard,
    };

_$BloomDistributionImpl _$$BloomDistributionImplFromJson(
        Map<String, dynamic> json) =>
    _$BloomDistributionImpl(
      remember: (json['remember'] as num).toDouble(),
      understand: (json['understand'] as num).toDouble(),
      apply: (json['apply'] as num).toDouble(),
      analyze: (json['analyze'] as num).toDouble(),
      evaluate: (json['evaluate'] as num).toDouble(),
      create: (json['create'] as num).toDouble(),
    );

Map<String, dynamic> _$$BloomDistributionImplToJson(
        _$BloomDistributionImpl instance) =>
    <String, dynamic>{
      'remember': instance.remember,
      'understand': instance.understand,
      'apply': instance.apply,
      'analyze': instance.analyze,
      'evaluate': instance.evaluate,
      'create': instance.create,
    };

_$ChapterWeightsImpl _$$ChapterWeightsImplFromJson(Map<String, dynamic> json) =>
    _$ChapterWeightsImpl(
      weights: (json['weights'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
    );

Map<String, dynamic> _$$ChapterWeightsImplToJson(
        _$ChapterWeightsImpl instance) =>
    <String, dynamic>{
      'weights': instance.weights,
    };

_$CompetencyWeightsImpl _$$CompetencyWeightsImplFromJson(
        Map<String, dynamic> json) =>
    _$CompetencyWeightsImpl(
      weights: (json['weights'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
    );

Map<String, dynamic> _$$CompetencyWeightsImplToJson(
        _$CompetencyWeightsImpl instance) =>
    <String, dynamic>{
      'weights': instance.weights,
    };

_$SectionBlueprintImpl _$$SectionBlueprintImplFromJson(
        Map<String, dynamic> json) =>
    _$SectionBlueprintImpl(
      id: json['id'] as String,
      label: json['label'] as String,
      name: json['name'] as String,
      marksPerQuestion: (json['marksPerQuestion'] as num).toInt(),
      questionCount: (json['questionCount'] as num).toInt(),
      totalMarks: (json['totalMarks'] as num).toInt(),
      allowedBloomLevels: (json['allowedBloomLevels'] as List<dynamic>)
          .map((e) => $enumDecode(_$BloomLevelEnumMap, e))
          .toList(),
      allowedDifficulties: (json['allowedDifficulties'] as List<dynamic>)
          .map((e) => $enumDecode(_$DifficultyEnumMap, e))
          .toList(),
      hasInternalChoice: json['hasInternalChoice'] as bool? ?? false,
      internalChoiceCount: (json['internalChoiceCount'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$SectionBlueprintImplToJson(
        _$SectionBlueprintImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'label': instance.label,
      'name': instance.name,
      'marksPerQuestion': instance.marksPerQuestion,
      'questionCount': instance.questionCount,
      'totalMarks': instance.totalMarks,
      'allowedBloomLevels': instance.allowedBloomLevels
          .map((e) => _$BloomLevelEnumMap[e]!)
          .toList(),
      'allowedDifficulties': instance.allowedDifficulties
          .map((e) => _$DifficultyEnumMap[e]!)
          .toList(),
      'hasInternalChoice': instance.hasInternalChoice,
      'internalChoiceCount': instance.internalChoiceCount,
    };

const _$BloomLevelEnumMap = {
  BloomLevel.remember: 'remember',
  BloomLevel.understand: 'understand',
  BloomLevel.apply: 'apply',
  BloomLevel.analyze: 'analyze',
  BloomLevel.evaluate: 'evaluate',
  BloomLevel.create: 'create',
};

const _$DifficultyEnumMap = {
  Difficulty.easy: 'easy',
  Difficulty.medium: 'medium',
  Difficulty.hard: 'hard',
};

_$BlueprintImpl _$$BlueprintImplFromJson(Map<String, dynamic> json) =>
    _$BlueprintImpl(
      totalMarks: (json['totalMarks'] as num).toInt(),
      durationMinutes: (json['durationMinutes'] as num).toInt(),
      difficulty: DifficultyDistribution.fromJson(
          json['difficulty'] as Map<String, dynamic>),
      bloom: BloomDistribution.fromJson(json['bloom'] as Map<String, dynamic>),
      chapterWeights: ChapterWeights.fromJson(
          json['chapterWeights'] as Map<String, dynamic>),
      competencyWeights: CompetencyWeights.fromJson(
          json['competencyWeights'] as Map<String, dynamic>),
      sections: (json['sections'] as List<dynamic>)
          .map((e) => SectionBlueprint.fromJson(e as Map<String, dynamic>))
          .toList(),
      metadata: json['metadata'] as Map<String, dynamic>? ?? const {},
    );

Map<String, dynamic> _$$BlueprintImplToJson(_$BlueprintImpl instance) =>
    <String, dynamic>{
      'totalMarks': instance.totalMarks,
      'durationMinutes': instance.durationMinutes,
      'difficulty': instance.difficulty,
      'bloom': instance.bloom,
      'chapterWeights': instance.chapterWeights,
      'competencyWeights': instance.competencyWeights,
      'sections': instance.sections,
      'metadata': instance.metadata,
    };

_$PointImpl _$$PointImplFromJson(Map<String, dynamic> json) => _$PointImpl(
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
    );

Map<String, dynamic> _$$PointImplToJson(_$PointImpl instance) =>
    <String, dynamic>{
      'x': instance.x,
      'y': instance.y,
    };
