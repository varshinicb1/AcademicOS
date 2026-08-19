import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'enums.dart';

part 'answer_sheet.freezed.dart';
part 'answer_sheet.g.dart';

@freezed
class AnswerSheet with _$AnswerSheet {
  const factory AnswerSheet({
    required String id,
    required String assessmentId,
    required String studentId,
    required String studentName,
    required String rollNumber,
    required List<ScannedPage> pages,
    required ScanMetadata scanMetadata,
    required List<QuestionResponse> responses,
    required AnswerSheetStatus status,
    required DateTime submittedAt,
    required DateTime scannedAt,
    DateTime? evaluatedAt,
    @Default({}) Map<String, dynamic> metadata,
  }) = _AnswerSheet;

  factory AnswerSheet.fromJson(Map<String, dynamic> json) => _$AnswerSheetFromJson(json);
}

@freezed
class ScannedPage with _$ScannedPage {
  const factory ScannedPage({
    required int pageNumber,
    required String imagePath,
    required String imageUrl,
    required int width,
    required int height,
    required double qualityScore,
    required PageOrientation orientation,
    required List<QuestionSegment> segments,
    @Default({}) Map<String, dynamic> preprocessing,
  }) = _ScannedPage;

  factory ScannedPage.fromJson(Map<String, dynamic> json) => _$ScannedPageFromJson(json);
}

@freezed
class QuestionSegment with _$QuestionSegment {
  const factory QuestionSegment({
    required String id,
    required String questionId,
    required int questionNumber,
    required SegmentType type,
    required List<Point> boundingBox,
    required String imagePath,
    required String imageUrl,
    required String ocrText,
    required String ocrTextLatex,
    required double ocrConfidence,
    required double visionConfidence,
    required SegmentationStatus status,
    @Default([]) List<String> studentAnswerImages,
  }) = _QuestionSegment;

  factory QuestionSegment.fromJson(Map<String, dynamic> json) => _$QuestionSegmentFromJson(json);
}

@freezed
class ScanMetadata with _$ScanMetadata {
  const factory ScanMetadata({
    required String deviceId,
    required String appVersion,
    required int totalPages,
    required double avgQualityScore,
    required int scanDurationMs,
    required LightingCondition lighting,
    @Default([]) List<String> warnings,
  }) = _ScanMetadata;

  factory ScanMetadata.fromJson(Map<String, dynamic> json) => _$ScanMetadataFromJson(json);
}

@freezed
class QuestionResponse with _$QuestionResponse {
  const factory QuestionResponse({
    required String questionId,
    required int questionNumber,
    required String studentAnswer,
    required String studentAnswerLatex,
    required List<String> studentAnswerImages,
    EvaluationResult? evaluation,
    required EvaluationStatus evaluationStatus,
    DateTime? evaluatedAt,
    String? teacherComment,
    int? teacherAdjustedMarks,
  }) = _QuestionResponse;

  factory QuestionResponse.fromJson(Map<String, dynamic> json) => _$QuestionResponseFromJson(json);
}

@freezed
class EvaluationResult with _$EvaluationResult {
  const factory EvaluationResult({
    required String id,
    required int awardedMarks,
    required int maxMarks,
    required double percentage,
    required EvaluationVerdict verdict,
    required List<MarkingPointResult> markingPoints,
    required RubricLevelResult rubricLevel,
    required double confidenceScore,
    required String reasoning,
    required List<String> strengths,
    required List<String> gaps,
    required List<String> carelessErrors,
    required int estimatedTimeSpentSeconds,
    @Default({}) Map<String, dynamic> metadata,
  }) = _EvaluationResult;

  factory EvaluationResult.fromJson(Map<String, dynamic> json) => _$EvaluationResultFromJson(json);
}

@freezed
class MarkingPointResult with _$MarkingPointResult {
  const factory MarkingPointResult({
    required String markingPointId,
    required bool awarded,
    required String reason,
    required double similarityScore,
  }) = _MarkingPointResult;

  factory MarkingPointResult.fromJson(Map<String, dynamic> json) => _$MarkingPointResultFromJson(json);
}

@freezed
class RubricLevelResult with _$RubricLevelResult {
  const factory RubricLevelResult({
    required int level,
    required String label,
    required String justification,
  }) = _RubricLevelResult;

  factory RubricLevelResult.fromJson(Map<String, dynamic> json) => _$RubricLevelResultFromJson(json);
}

extension QuestionSegmentX on QuestionSegment {
  String get displayText {
    if (ocrText.isNotEmpty) return ocrText;
    if (studentAnswerImages.isNotEmpty) return '[Image: ${studentAnswerImages.length} image(s)]';
    return '[No response detected]';
  }
}
