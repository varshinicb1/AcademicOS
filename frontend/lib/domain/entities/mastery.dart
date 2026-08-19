import 'package:freezed_annotation/freezed_annotation.dart';
import 'enums.dart';

part 'mastery.freezed.dart';
part 'mastery.g.dart';

@freezed
class StudentMastery with _$StudentMastery {
  const factory StudentMastery({
    required String studentId,
    required String schoolId,
    required String grade,
    required List<ConceptMastery> concepts,
    required List<ChapterMastery> chapters,
    required List<SubjectMastery> subjects,
    required MasterySummary summary,
    required DateTime lastUpdated,
    required int version,
  }) = _StudentMastery;

  factory StudentMastery.fromJson(Map<String, dynamic> json) => _$StudentMasteryFromJson(json);
}

@freezed
class ConceptMastery with _$ConceptMastery {
  const factory ConceptMastery({
    required String conceptId,
    required String conceptName,
    required String chapterId,
    required String subject,
    required double masteryScore,
    required double confidenceScore,
    required double retentionScore,
    required int totalAttempts,
    required int correctAttempts,
    required int consecutiveCorrect,
    required int consecutiveIncorrect,
    required DateTime lastAttemptedAt,
    DateTime? masteredAt,
    required MasteryStatus status,
    required List<MisconceptionFlag> misconceptions,
    required List<String> prerequisiteConceptIds,
    required double difficulty,
    required double timeSpentMinutes,
  }) = _ConceptMastery;

  factory ConceptMastery.fromJson(Map<String, dynamic> json) => _$ConceptMasteryFromJson(json);
}

@freezed
class ChapterMastery with _$ChapterMastery {
  const factory ChapterMastery({
    required String chapterId,
    required String chapterName,
    required String subject,
    required int grade,
    required double overallMastery,
    required double overallConfidence,
    required double overallRetention,
    required List<String> masteredConceptIds,
    required List<String> weakConceptIds,
    required List<String> notAttemptedConceptIds,
    required int questionsAttempted,
    required int questionsCorrect,
    required DateTime lastActivityAt,
    required ChapterStatus status,
  }) = _ChapterMastery;

  factory ChapterMastery.fromJson(Map<String, dynamic> json) => _$ChapterMasteryFromJson(json);
}

@freezed
class SubjectMastery with _$SubjectMastery {
  const factory SubjectMastery({
    required String subject,
    required int grade,
    required double overallMastery,
    required double overallConfidence,
    required double overallRetention,
    required List<ChapterMastery> chapters,
    required int totalQuestionsAttempted,
    required int totalQuestionsCorrect,
    required double avgTimePerQuestion,
    required SubjectStatus status,
  }) = _SubjectMastery;

  factory SubjectMastery.fromJson(Map<String, dynamic> json) => _$SubjectMasteryFromJson(json);
}

@freezed
class MasterySummary with _$MasterySummary {
  const factory MasterySummary({
    required double overallMastery,
    required double overallConfidence,
    required double overallRetention,
    required int totalConcepts,
    required int masteredConcepts,
    required int weakConcepts,
    required int notAttemptedConcepts,
    required int totalQuestionsAttempted,
    required int totalQuestionsCorrect,
    required double accuracyRate,
    required Map<String, int> bloomDistribution,
    required Map<String, int> difficultyDistribution,
    required List<String> topStrengths,
    required List<String> topWeaknesses,
    required List<ActionableRecommendation> recommendations,
  }) = _MasterySummary;

  factory MasterySummary.fromJson(Map<String, dynamic> json) => _$MasterySummaryFromJson(json);
}

@freezed
class MisconceptionFlag with _$MisconceptionFlag {
  const factory MisconceptionFlag({
    required String misconceptionId,
    required String misconceptionName,
    required String description,
    required double confidence,
    required int occurrenceCount,
    required DateTime firstDetectedAt,
    required DateTime lastDetectedAt,
    required MisconceptionSeverity severity,
    required List<String> evidenceQuestionIds,
  }) = _MisconceptionFlag;

  factory MisconceptionFlag.fromJson(Map<String, dynamic> json) => _$MisconceptionFlagFromJson(json);
}

@freezed
class ActionableRecommendation with _$ActionableRecommendation {
  const factory ActionableRecommendation({
    required String id,
    required RecommendationType type,
    required String title,
    required String description,
    required String targetConceptId,
    required String targetConceptName,
    required int estimatedMinutes,
    required double successProbability,
    required Priority priority,
    required List<String> resourceIds,
  }) = _ActionableRecommendation;

  factory ActionableRecommendation.fromJson(Map<String, dynamic> json) => _$ActionableRecommendationFromJson(json);
}
