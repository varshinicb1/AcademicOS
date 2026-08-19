import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'enums.dart';
import 'mastery.dart';

part 'analytics.freezed.dart';
part 'analytics.g.dart';

@freezed
class AssessmentAnalytics with _$AssessmentAnalytics {
  const factory AssessmentAnalytics({
    required String assessmentId,
    required String assessmentTitle,
    required int totalStudents,
    required int submittedStudents,
    required int evaluatedStudents,
    required ClassPerformance classPerformance,
    required List<StudentPerformance> studentPerformances,
    required List<QuestionAnalytics> questionAnalytics,
    required List<ConceptGap> conceptGaps,
    required BloomAnalytics bloomAnalytics,
    required CompetencyAnalytics competencyAnalytics,
    required DifficultyAnalytics difficultyAnalytics,
    required TimeAnalytics timeAnalytics,
    required List<CommonError> commonErrors,
    required DateTime generatedAt,
  }) = _AssessmentAnalytics;

  factory AssessmentAnalytics.fromJson(Map<String, dynamic> json) => _$AssessmentAnalyticsFromJson(json);
}

@freezed
class ClassPerformance with _$ClassPerformance {
  const factory ClassPerformance({
    required double averageScore,
    required double medianScore,
    required double standardDeviation,
    required double passRate,
    required double distinctionRate,
    required Map<String, int> gradeDistribution,
    required int highestScore,
    required int lowestScore,
    required double reliabilityCoefficient,
    required double standardError,
  }) = _ClassPerformance;

  factory ClassPerformance.fromJson(Map<String, dynamic> json) => _$ClassPerformanceFromJson(json);
}

@freezed
class StudentPerformance with _$StudentPerformance {
  const factory StudentPerformance({
    required String studentId,
    required String studentName,
    required String rollNumber,
    required int totalScore,
    required int maxScore,
    required double percentage,
    required String grade,
    required int rank,
    required double percentile,
    required List<SectionScore> sectionScores,
    required Map<String, double> conceptScores,
    required List<String> strengths,
    required List<String> weaknesses,
    required List<String> carelessErrors,
    required String recommendation,
  }) = _StudentPerformance;

  factory StudentPerformance.fromJson(Map<String, dynamic> json) => _$StudentPerformanceFromJson(json);
}

@freezed
class SectionScore with _$SectionScore {
  const factory SectionScore({
    required String sectionId,
    required String sectionLabel,
    required int score,
    required int maxScore,
    required double percentage,
  }) = _SectionScore;

  factory SectionScore.fromJson(Map<String, dynamic> json) => _$SectionScoreFromJson(json);
}

@freezed
class QuestionAnalytics with _$QuestionAnalytics {
  const factory QuestionAnalytics({
    required String questionId,
    required int questionNumber,
    required String sectionLabel,
    required int maxMarks,
    required double averageMarks,
    required double difficultyIndex,
    required double discriminationIndex,
    required int attemptedCount,
    required int correctCount,
    required int partialCount,
    required int blankCount,
    required double avgTimeSeconds,
    required List<String> commonWrongAnswers,
    required Map<String, int> optionDistribution,
    required QuestionQualityFlags flags,
  }) = _QuestionAnalytics;

  factory QuestionAnalytics.fromJson(Map<String, dynamic> json) => _$QuestionAnalyticsFromJson(json);
}

@freezed
class QuestionQualityFlags with _$QuestionQualityFlags {
  const factory QuestionQualityFlags({
    @Default(false) bool tooEasy,
    @Default(false) bool tooHard,
    @Default(false) bool poorDiscrimination,
    @Default(false) bool ambiguous,
    @Default(false) bool guessingPossible,
    @Default(false) bool timeConsuming,
    @Default([]) List<String> warnings,
  }) = _QuestionQualityFlags;

  factory QuestionQualityFlags.fromJson(Map<String, dynamic> json) => _$QuestionQualityFlagsFromJson(json);
}

@freezed
class ConceptGap with _$ConceptGap {
  const factory ConceptGap({
    required String conceptId,
    required String conceptName,
    required String chapterId,
    required String chapterName,
    required int studentsAffected,
    required double avgMastery,
    required List<String> relatedQuestionIds,
    required List<String> misconceptionIds,
    required GapSeverity severity,
    required String recommendedAction,
  }) = _ConceptGap;

  factory ConceptGap.fromJson(Map<String, dynamic> json) => _$ConceptGapFromJson(json);
}

@freezed
class BloomAnalytics with _$BloomAnalytics {
  const factory BloomAnalytics({
    required Map<String, BloomLevelStats> byLevel,
    required List<String> insights,
  }) = _BloomAnalytics;

  factory BloomAnalytics.fromJson(Map<String, dynamic> json) => _$BloomAnalyticsFromJson(json);
}

@freezed
class BloomLevelStats with _$BloomLevelStats {
  const factory BloomLevelStats({
    required String level,
    required int questionCount,
    required int totalMarks,
    required double avgScore,
    required double avgPercentage,
    required int studentsAttempted,
    required int studentsProficient,
  }) = _BloomLevelStats;

  factory BloomLevelStats.fromJson(Map<String, dynamic> json) => _$BloomLevelStatsFromJson(json);
}

@freezed
class CompetencyAnalytics with _$CompetencyAnalytics {
  const factory CompetencyAnalytics({
    required Map<String, CompetencyStats> byCompetency,
    required List<String> insights,
  }) = _CompetencyAnalytics;

  factory CompetencyAnalytics.fromJson(Map<String, dynamic> json) => _$CompetencyAnalyticsFromJson(json);
}

@freezed
class CompetencyStats with _$CompetencyStats {
  const factory CompetencyStats({
    required String competencyId,
    required String competencyName,
    required int questionCount,
    required int totalMarks,
    required double avgScore,
    required double avgPercentage,
    required int studentsProficient,
  }) = _CompetencyStats;

  factory CompetencyStats.fromJson(Map<String, dynamic> json) => _$CompetencyStatsFromJson(json);
}

@freezed
class DifficultyAnalytics with _$DifficultyAnalytics {
  const factory DifficultyAnalytics({
    required DifficultyLevelStats easy,
    required DifficultyLevelStats medium,
    required DifficultyLevelStats hard,
    required List<String> insights,
  }) = _DifficultyAnalytics;

  factory DifficultyAnalytics.fromJson(Map<String, dynamic> json) => _$DifficultyAnalyticsFromJson(json);
}

@freezed
class DifficultyLevelStats with _$DifficultyLevelStats {
  const factory DifficultyLevelStats({
    required String level,
    required int questionCount,
    required int totalMarks,
    required double avgScore,
    required double avgPercentage,
    required double discriminationIndex,
  }) = _DifficultyLevelStats;

  factory DifficultyLevelStats.fromJson(Map<String, dynamic> json) => _$DifficultyLevelStatsFromJson(json);
}

@freezed
class TimeAnalytics with _$TimeAnalytics {
  const factory TimeAnalytics({
    required double avgTimePerQuestion,
    required double avgTotalTime,
    required Map<String, double> timeBySection,
    required Map<String, double> timeByQuestion,
    required int studentsFinishedEarly,
    required int studentsRanOutOfTime,
    required List<String> insights,
  }) = _TimeAnalytics;

  factory TimeAnalytics.fromJson(Map<String, dynamic> json) => _$TimeAnalyticsFromJson(json);
}

@freezed
class CommonError with _$CommonError {
  const factory CommonError({
    required String id,
    required String questionId,
    required int questionNumber,
    required String errorType,
    required String description,
    required int frequency,
    required double percentage,
    required List<String> exampleAnswers,
    required String remediationHint,
  }) = _CommonError;

  factory CommonError.fromJson(Map<String, dynamic> json) => _$CommonErrorFromJson(json);
}

@freezed
class ClassAnalytics with _$ClassAnalytics {
  const factory ClassAnalytics({
    required String classId,
    required String className,
    required int totalStudents,
    required List<AssessmentAnalytics> assessments,
    required Map<String, SubjectMastery> subjectMastery,
    required List<ConceptGap> classWideGaps,
    required List<StudentPerformance> topPerformers,
    required List<StudentPerformance> atRiskStudents,
    required DateTime generatedAt,
  }) = _ClassAnalytics;

  factory ClassAnalytics.fromJson(Map<String, dynamic> json) => _$ClassAnalyticsFromJson(json);
}

@freezed
class StudentAnalytics with _$StudentAnalytics {
  const factory StudentAnalytics({
    required String studentId,
    required String studentName,
    required String grade,
    required Map<String, SubjectMastery> subjectMastery,
    required List<AssessmentAnalytics> assessmentHistory,
    required List<MisconceptionFlag> activeMisconceptions,
    required List<ConceptGap> conceptGaps,
    required List<ActionableRecommendation> recommendations,
    required DateTime generatedAt,
  }) = _StudentAnalytics;

  factory StudentAnalytics.fromJson(Map<String, dynamic> json) => _$StudentAnalyticsFromJson(json);
}

@freezed
class SchoolAnalytics with _$SchoolAnalytics {
  const factory SchoolAnalytics({
    required String schoolId,
    required String schoolName,
    required int totalClasses,
    required int totalStudents,
    required int totalTeachers,
    required Map<String, double> subjectPerformance,
    required Map<String, int> gradeDistribution,
    required List<ClassAnalytics> topClasses,
    required List<ClassAnalytics> atRiskClasses,
    required List<ConceptGap> schoolWideGaps,
    required DateTime generatedAt,
  }) = _SchoolAnalytics;

  factory SchoolAnalytics.fromJson(Map<String, dynamic> json) => _$SchoolAnalyticsFromJson(json);
}
