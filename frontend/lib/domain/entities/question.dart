import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'enums.dart';

part 'question.freezed.dart';
part 'question.g.dart';

@freezed
class Question with _$Question {
  const factory Question({
    required String id,
    required String questionBankId,
    required String subject,
    required int grade,
    required List<String> chapterIds,
    required List<String> competencyIds,
    @BloomLevelConverter() required BloomLevel bloomLevel,
    @DifficultyConverter() required Difficulty difficulty,
    @QuestionTypeConverter() required QuestionType type,
    required String stem,
    required String stemLatex,
    required List<QuestionPart> parts,
    required AnswerScheme answerScheme,
    required int estimatedTimeMinutes,
    required int marks,
    required String language,
    @QuestionSourceConverter() required QuestionSource source,
    required double qualityScore,
    required List<String> tags,
    required DateTime createdAt,
    required DateTime updatedAt,
    @Default({}) Map<String, dynamic> metadata,
    String? diagramAssetId,
    String? mapAssetId,
    String? graphAssetId,
    String? tableAssetId,
  }) = _Question;

  factory Question.fromJson(Map<String, dynamic> json) => _$QuestionFromJson(json);
}

@freezed
class QuestionPart with _$QuestionPart {
  const factory QuestionPart({
    required String id,
    required int partNumber,
    required String text,
    required String textLatex,
    required int marks,
    required AnswerType answerType,
    List<String>? options,
    String? correctOption,
    String? expectedAnswer,
    String? expectedAnswerLatex,
    List<String>? keywords,
    @Default([]) List<String> alternativeAnswers,
  }) = _QuestionPart;

  factory QuestionPart.fromJson(Map<String, dynamic> json) => _$QuestionPartFromJson(json);
}

@freezed
class AnswerScheme with _$AnswerScheme {
  const factory AnswerScheme({
    required int totalMarks,
    required List<MarkingPoint> markingPoints,
    required List<RubricLevel> rubricLevels,
    required List<String> commonErrors,
    required List<String> alternativeAnswers,
    required String modelAnswer,
    required String modelAnswerLatex,
    @Default(false) bool hasPartialCredit,
    @Default({}) Map<String, dynamic> metadata,
  }) = _AnswerScheme;

  factory AnswerScheme.fromJson(Map<String, dynamic> json) => _$AnswerSchemeFromJson(json);
}

@freezed
class MarkingPoint with _$MarkingPoint {
  const factory MarkingPoint({
    required String id,
    required String description,
    required int marks,
    required String keyword,
    required bool isRequired,
    @Default([]) List<String> synonyms,
  }) = _MarkingPoint;

  factory MarkingPoint.fromJson(Map<String, dynamic> json) => _$MarkingPointFromJson(json);
}

@freezed
class RubricLevel with _$RubricLevel {
  const factory RubricLevel({
    required int level,
    required String label,
    required int minMarks,
    required int maxMarks,
    required String description,
  }) = _RubricLevel;

  factory RubricLevel.fromJson(Map<String, dynamic> json) => _$RubricLevelFromJson(json);
}

enum AnswerType {
  singleChoice,
  multipleChoice,
  textShort,
  textLong,
  numeric,
  diagram,
  map,
  graph,
  table,
}

@freezed
class QuestionOptimizationRequest with _$QuestionOptimizationRequest {
  const factory QuestionOptimizationRequest({
    required List<Question> candidates,
    required Blueprint blueprint,
  }) = _QuestionOptimizationRequest;

  factory QuestionOptimizationRequest.fromJson(Map<String, dynamic> json) => _$QuestionOptimizationRequestFromJson(json);
}
