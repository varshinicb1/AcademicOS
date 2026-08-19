import 'package:freezed_annotation/freezed_annotation.dart';
import 'enums.dart';
import 'mastery.dart';
import 'analytics.dart';

part 'report.freezed.dart';
part 'report.g.dart';

@freezed
class StudentReport with _$StudentReport {
  const factory StudentReport({
    required String id,
    required String assessmentId,
    required String assessmentTitle,
    required String studentId,
    required String studentName,
    required String rollNumber,
    required int grade,
    required String section,
    required ReportHeader header,
    required PerformanceOverview overview,
    required List<SectionReport> sectionReports,
    required List<ConceptReport> conceptReports,
    required BloomReport bloomReport,
    required CompetencyReport competencyReport,
    required List<String> strengths,
    required List<String> weaknesses,
    required List<String> carelessErrors,
    required List<ActionableRecommendation> recommendations,
    required TeacherRemarks teacherRemarks,
    required ParentSummary parentSummary,
    required DateTime generatedAt,
    required String generatedBy,
  }) = _StudentReport;

  factory StudentReport.fromJson(Map<String, dynamic> json) =>
      _$StudentReportFromJson(json);
}

@freezed
class ReportHeader with _$ReportHeader {
  const factory ReportHeader({
    required String schoolName,
    required String schoolLogoUrl,
    required String academicYear,
    required String term,
    required DateTime assessmentDate,
    required DateTime reportDate,
    required String principalName,
    required String teacherName,
    required String className,
    required String section,
  }) = _ReportHeader;

  factory ReportHeader.fromJson(Map<String, dynamic> json) =>
      _$ReportHeaderFromJson(json);
}

@freezed
class PerformanceOverview with _$PerformanceOverview {
  const factory PerformanceOverview({
    required int totalScore,
    required int maxScore,
    required double percentage,
    required String grade,
    required int classRank,
    required int totalStudents,
    required double percentile,
    required String performanceLevel,
    required Map<String, SectionScore> sectionScores,
    required double classAverage,
    required double classMedian,
  }) = _PerformanceOverview;

  factory PerformanceOverview.fromJson(Map<String, dynamic> json) =>
      _$PerformanceOverviewFromJson(json);
}

@freezed
class SectionReport with _$SectionReport {
  const factory SectionReport({
    required String sectionId,
    required String sectionLabel,
    required String sectionName,
    required int score,
    required int maxScore,
    required double percentage,
    required int questionsAttempted,
    required int questionsCorrect,
    required int questionsPartial,
    required List<QuestionReport> questions,
  }) = _SectionReport;

  factory SectionReport.fromJson(Map<String, dynamic> json) =>
      _$SectionReportFromJson(json);
}

@freezed
class QuestionReport with _$QuestionReport {
  const factory QuestionReport({
    required String questionId,
    required int questionNumber,
    required String questionText,
    required int maxMarks,
    required int awardedMarks,
    required String studentAnswer,
    required String modelAnswer,
    required String verdict,
    required String feedback,
    required String conceptTag,
    required String bloomLevel,
    required String difficulty,
  }) = _QuestionReport;

  factory QuestionReport.fromJson(Map<String, dynamic> json) =>
      _$QuestionReportFromJson(json);
}

@freezed
class ConceptReport with _$ConceptReport {
  const factory ConceptReport({
    required String conceptId,
    required String conceptName,
    required String chapterName,
    required double masteryScore,
    required MasteryStatus status,
    required int questionsAttempted,
    required int questionsCorrect,
    required String statusLabel,
    required String recommendation,
  }) = _ConceptReport;

  factory ConceptReport.fromJson(Map<String, dynamic> json) =>
      _$ConceptReportFromJson(json);
}

@freezed
class BloomReport with _$BloomReport {
  const factory BloomReport({
    required Map<String, BloomLevelReport> byLevel,
    required String strongestLevel,
    required String weakestLevel,
    required List<String> insights,
  }) = _BloomReport;

  factory BloomReport.fromJson(Map<String, dynamic> json) =>
      _$BloomReportFromJson(json);
}

@freezed
class BloomLevelReport with _$BloomLevelReport {
  const factory BloomLevelReport({
    required String level,
    required int questionsAttempted,
    required int maxMarks,
    required int scoredMarks,
    required double percentage,
    required String status,
  }) = _BloomLevelReport;

  factory BloomLevelReport.fromJson(Map<String, dynamic> json) =>
      _$BloomLevelReportFromJson(json);
}

@freezed
class CompetencyReport with _$CompetencyReport {
  const factory CompetencyReport({
    required Map<String, CompetencyReportItem> byCompetency,
    required List<String> insights,
  }) = _CompetencyReport;

  factory CompetencyReport.fromJson(Map<String, dynamic> json) =>
      _$CompetencyReportFromJson(json);
}

@freezed
class CompetencyReportItem with _$CompetencyReportItem {
  const factory CompetencyReportItem({
    required String competencyId,
    required String competencyName,
    required int questionsAttempted,
    required int maxMarks,
    required int scoredMarks,
    required double percentage,
    required String status,
  }) = _CompetencyReportItem;

  factory CompetencyReportItem.fromJson(Map<String, dynamic> json) =>
      _$CompetencyReportItemFromJson(json);
}

@freezed
class TeacherRemarks with _$TeacherRemarks {
  const factory TeacherRemarks({
    required String overallComment,
    required List<String> specificComments,
    required String encouragement,
    required String nextSteps,
    required DateTime writtenAt,
    required String writtenBy,
  }) = _TeacherRemarks;

  factory TeacherRemarks.fromJson(Map<String, dynamic> json) =>
      _$TeacherRemarksFromJson(json);
}

@freezed
class ParentSummary with _$ParentSummary {
  const factory ParentSummary({
    required String simpleSummary,
    required List<String> keyStrengths,
    required List<String> keyAreasForImprovement,
    required String homeSupportSuggestion,
    required String teacherMessage,
  }) = _ParentSummary;

  factory ParentSummary.fromJson(Map<String, dynamic> json) =>
      _$ParentSummaryFromJson(json);
}

@freezed
class ParentReport with _$ParentReport {
  const factory ParentReport({
    required String id,
    required String studentId,
    required String studentName,
    required String assessmentId,
    required String assessmentTitle,
    required String className,
    required ReportHeader header,
    required ParentPerformanceSummary summary,
    required List<String> keyStrengths,
    required List<String> areasForImprovement,
    required List<String> atHomeSuggestions,
    required String teacherMessage,
    required List<ActionableRecommendation> nextSteps,
    required DateTime generatedAt,
    required String generatedBy,
  }) = _ParentReport;

  factory ParentReport.fromJson(Map<String, dynamic> json) =>
      _$ParentReportFromJson(json);
}

@freezed
class ParentPerformanceSummary with _$ParentPerformanceSummary {
  const factory ParentPerformanceSummary({
    required int totalScore,
    required int maxScore,
    required double percentage,
    required String grade,
    required int classRank,
    required int totalStudents,
    required String simpleSummary,
    required String performanceLevel,
  }) = _ParentPerformanceSummary;

  factory ParentPerformanceSummary.fromJson(Map<String, dynamic> json) =>
      _$ParentPerformanceSummaryFromJson(json);
}
