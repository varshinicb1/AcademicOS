import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'dart:convert';

part 'enums.freezed.dart';
part 'enums.g.dart';

enum BloomLevel {
  remember,
  understand,
  apply,
  analyze,
  evaluate,
  create,
}

extension BloomLevelX on BloomLevel {
  String get label => switch (this) {
    BloomLevel.remember => 'Remember',
    BloomLevel.understand => 'Understand',
    BloomLevel.apply => 'Apply',
    BloomLevel.analyze => 'Analyze',
    BloomLevel.evaluate => 'Evaluate',
    BloomLevel.create => 'Create',
  };
}

class BloomLevelConverter implements JsonConverter<BloomLevel, String> {
  const BloomLevelConverter();

  @override
  BloomLevel fromJson(String json) {
    switch (json) {
      case 'remember': return BloomLevel.remember;
      case 'understand': return BloomLevel.understand;
      case 'apply': return BloomLevel.apply;
      case 'analyze': return BloomLevel.analyze;
      case 'evaluate': return BloomLevel.evaluate;
      case 'create': return BloomLevel.create;
      default: return BloomLevel.remember;
    }
  }

  @override
  String toJson(BloomLevel object) => object.name;
}

enum Difficulty {
  easy,
  medium,
  hard,
}

extension DifficultyX on Difficulty {
  String get label => switch (this) {
    Difficulty.easy => 'Easy',
    Difficulty.medium => 'Medium',
    Difficulty.hard => 'Hard',
  };

  Color get color => switch (this) {
    Difficulty.easy => Colors.green,
    Difficulty.medium => Colors.orange,
    Difficulty.hard => Colors.red,
  };
}

class DifficultyConverter implements JsonConverter<Difficulty, String> {
  const DifficultyConverter();

  @override
  Difficulty fromJson(String json) {
    switch (json) {
      case 'easy': return Difficulty.easy;
      case 'medium': return Difficulty.medium;
      case 'hard': return Difficulty.hard;
      default: return Difficulty.medium;
    }
  }

  @override
  String toJson(Difficulty object) => object.name;
}

enum QuestionType {
  mcq,
  veryShortAnswer,
  shortAnswer,
  longAnswer,
  veryLongAnswer,
  caseStudy,
  assertionReason,
  mapBased,
  diagramBased,
  graphBased,
  tableBased,
  competencyBased,
}

extension QuestionTypeX on QuestionType {
  String get label => switch (this) {
    QuestionType.mcq => 'MCQ',
    QuestionType.veryShortAnswer => 'VSA (1M)',
    QuestionType.shortAnswer => 'SA (2M)',
    QuestionType.longAnswer => 'LA (3M)',
    QuestionType.veryLongAnswer => 'VLA (4-5M)',
    QuestionType.caseStudy => 'Case Study',
    QuestionType.assertionReason => 'Assertion & Reason',
    QuestionType.mapBased => 'Map Based',
    QuestionType.diagramBased => 'Diagram',
    QuestionType.graphBased => 'Graph',
    QuestionType.tableBased => 'Table',
    QuestionType.competencyBased => 'Competency',
  };
}

class QuestionTypeConverter implements JsonConverter<QuestionType, String> {
  const QuestionTypeConverter();

  @override
  QuestionType fromJson(String json) {
    switch (json) {
      case 'mcq': return QuestionType.mcq;
      case 'very_short_answer': return QuestionType.veryShortAnswer;
      case 'short_answer': return QuestionType.shortAnswer;
      case 'long_answer': return QuestionType.longAnswer;
      case 'very_long_answer': return QuestionType.veryLongAnswer;
      case 'case_study': return QuestionType.caseStudy;
      case 'assertion_reason': return QuestionType.assertionReason;
      case 'map_based': return QuestionType.mapBased;
      case 'diagram_based': return QuestionType.diagramBased;
      case 'graph_based': return QuestionType.graphBased;
      case 'table_based': return QuestionType.tableBased;
      case 'competency_based': return QuestionType.competencyBased;
      default: return QuestionType.shortAnswer;
    }
  }

  @override
  String toJson(QuestionType object) => switch (object) {
    QuestionType.mcq => 'mcq',
    QuestionType.veryShortAnswer => 'very_short_answer',
    QuestionType.shortAnswer => 'short_answer',
    QuestionType.longAnswer => 'long_answer',
    QuestionType.veryLongAnswer => 'very_long_answer',
    QuestionType.caseStudy => 'case_study',
    QuestionType.assertionReason => 'assertion_reason',
    QuestionType.mapBased => 'map_based',
    QuestionType.diagramBased => 'diagram_based',
    QuestionType.graphBased => 'graph_based',
    QuestionType.tableBased => 'table_based',
    QuestionType.competencyBased => 'competency_based',
  };
}

enum QuestionSource {
  cbseBoardPaper,
  cbseSamplePaper,
  cbseQuestionBank,
  ncertExemplar,
  ncertTextbook,
  schoolDatabase,
  teacherCreated,
  aiGenerated,
  competencyFramework,
}

extension QuestionSourceX on QuestionSource {
  String get label => switch (this) {
    QuestionSource.cbseBoardPaper => 'CBSE Board Paper',
    QuestionSource.cbseSamplePaper => 'CBSE Sample Paper',
    QuestionSource.cbseQuestionBank => 'CBSE Question Bank',
    QuestionSource.ncertExemplar => 'NCERT Exemplar',
    QuestionSource.ncertTextbook => 'NCERT Textbook',
    QuestionSource.schoolDatabase => 'School Database',
    QuestionSource.teacherCreated => 'Teacher Created',
    QuestionSource.aiGenerated => 'AI Generated',
    QuestionSource.competencyFramework => 'Competency Framework',
  };
}

class QuestionSourceConverter implements JsonConverter<QuestionSource, String> {
  const QuestionSourceConverter();

  @override
  QuestionSource fromJson(String json) {
    switch (json) {
      case 'cbse_board_paper': return QuestionSource.cbseBoardPaper;
      case 'cbse_sample_paper': return QuestionSource.cbseSamplePaper;
      case 'cbse_question_bank': return QuestionSource.cbseQuestionBank;
      case 'ncert_exemplar': return QuestionSource.ncertExemplar;
      case 'ncert_textbook': return QuestionSource.ncertTextbook;
      case 'school_database': return QuestionSource.schoolDatabase;
      case 'teacher_created': return QuestionSource.teacherCreated;
      case 'ai_generated': return QuestionSource.aiGenerated;
      case 'competency_framework': return QuestionSource.competencyFramework;
      default: return QuestionSource.ncertTextbook;
    }
  }

  @override
  String toJson(QuestionSource object) => switch (object) {
    QuestionSource.cbseBoardPaper => 'cbse_board_paper',
    QuestionSource.cbseSamplePaper => 'cbse_sample_paper',
    QuestionSource.cbseQuestionBank => 'cbse_question_bank',
    QuestionSource.ncertExemplar => 'ncert_exemplar',
    QuestionSource.ncertTextbook => 'ncert_textbook',
    QuestionSource.schoolDatabase => 'school_database',
    QuestionSource.teacherCreated => 'teacher_created',
    QuestionSource.aiGenerated => 'ai_generated',
    QuestionSource.competencyFramework => 'competency_framework',
  };
}

enum AssessmentStatus {
  draft,
  blueprintReady,
  questionsSelected,
  questionOptimized,
  paperGenerated,
  underReview,
  principalApproved,
  printed,
  conducted,
  scanning,
  scanned,
  evaluating,
  evaluated,
  teacherReviewed,
  reportsGenerated,
  remediationSent,
  archived,
}

extension AssessmentStatusX on AssessmentStatus {
  String get label => switch (this) {
    AssessmentStatus.draft => 'Draft',
    AssessmentStatus.blueprintReady => 'Blueprint Ready',
    AssessmentStatus.questionsSelected => 'Questions Selected',
    AssessmentStatus.questionOptimized => 'Questions Optimized',
    AssessmentStatus.paperGenerated => 'Paper Generated',
    AssessmentStatus.underReview => 'Under Review',
    AssessmentStatus.principalApproved => 'Approved',
    AssessmentStatus.printed => 'Printed',
    AssessmentStatus.conducted => 'Conducted',
    AssessmentStatus.scanning => 'Scanning',
    AssessmentStatus.scanned => 'Scanned',
    AssessmentStatus.evaluating => 'Evaluating',
    AssessmentStatus.evaluated => 'Evaluated',
    AssessmentStatus.teacherReviewed => 'Teacher Reviewed',
    AssessmentStatus.reportsGenerated => 'Reports Ready',
    AssessmentStatus.remediationSent => 'Remediation Sent',
    AssessmentStatus.archived => 'Archived',
  };

  IconData get icon => switch (this) {
    AssessmentStatus.draft => Icons.drafts,
    AssessmentStatus.blueprintReady => Icons.architecture,
    AssessmentStatus.questionsSelected => Icons.playlist_add_check,
    AssessmentStatus.questionOptimized => Icons.tune,
    AssessmentStatus.paperGenerated => Icons.description,
    AssessmentStatus.underReview => Icons.rate_review,
    AssessmentStatus.principalApproved => Icons.verified,
    AssessmentStatus.printed => Icons.local_printshop,
    AssessmentStatus.conducted => Icons.check_circle,
    AssessmentStatus.scanning => Icons.document_scanner,
    AssessmentStatus.scanned => Icons.scanner,
    AssessmentStatus.evaluating => Icons.auto_awesome,
    AssessmentStatus.evaluated => Icons.grade,
    AssessmentStatus.teacherReviewed => Icons.rate_review,
    AssessmentStatus.reportsGenerated => Icons.analytics,
    AssessmentStatus.remediationSent => Icons.personal_injury,
    AssessmentStatus.archived => Icons.archive,
  };

  Color get color => switch (this) {
    AssessmentStatus.draft => Colors.grey,
    AssessmentStatus.blueprintReady => Colors.blue,
    AssessmentStatus.questionsSelected => Colors.purple,
    AssessmentStatus.questionOptimized => Colors.indigo,
    AssessmentStatus.paperGenerated => Colors.teal,
    AssessmentStatus.underReview => Colors.orange,
    AssessmentStatus.principalApproved => Colors.green,
    AssessmentStatus.printed => Colors.cyan,
    AssessmentStatus.conducted => Colors.blueGrey,
    AssessmentStatus.scanning => Colors.amber,
    AssessmentStatus.scanned => Colors.yellow,
    AssessmentStatus.evaluating => Colors.deepPurple,
    AssessmentStatus.evaluated => Colors.lightGreen,
    AssessmentStatus.teacherReviewed => Colors.teal,
    AssessmentStatus.reportsGenerated => Colors.greenAccent,
    AssessmentStatus.remediationSent => Colors.pinkAccent,
    AssessmentStatus.archived => Colors.blueGrey,
  };
}

enum AnswerSheetStatus {
  scanned,
  segmented,
  ocrCompleted,
  underEvaluation,
  evaluated,
  teacherReviewed,
  finalized,
  disputed,
}

enum SegmentType {
  textAnswer,
  diagram,
  map,
  graph,
  table,
  mixed,
}

enum SegmentationStatus {
  detected,
  ocrPending,
  ocrCompleted,
  visionPending,
  visionCompleted,
  readyForEvaluation,
  evaluated,
}

enum EvaluationStatus {
  pending,
  aiEvaluated,
  teacherApproved,
  teacherAdjusted,
  disputed,
}

enum EvaluationVerdict {
  fullCredit,
  partialCredit,
  noCredit,
  carelessError,
  conceptualError,
  blank,
}

extension EvaluationVerdictX on EvaluationVerdict {
  String get label => switch (this) {
    EvaluationVerdict.fullCredit => 'Full Credit',
    EvaluationVerdict.partialCredit => 'Partial Credit',
    EvaluationVerdict.noCredit => 'No Credit',
    EvaluationVerdict.carelessError => 'Careless Error',
    EvaluationVerdict.conceptualError => 'Conceptual Error',
    EvaluationVerdict.blank => 'Blank',
  };

  Color get color => switch (this) {
    EvaluationVerdict.fullCredit => Colors.green,
    EvaluationVerdict.partialCredit => Colors.orange,
    EvaluationVerdict.noCredit => Colors.red,
    EvaluationVerdict.carelessError => Colors.amber,
    EvaluationVerdict.conceptualError => Colors.deepOrange,
    EvaluationVerdict.blank => Colors.grey,
  };
}

enum PageOrientation {
  portrait,
  landscape,
  auto,
}

enum LightingCondition {
  good,
  fair,
  poor,
  unknown,
}

enum MasteryStatus {
  notAttempted,
  learning,
  developing,
  proficient,
  mastered,
  decaying,
  needsReview,
}

extension MasteryStatusX on MasteryStatus {
  String get label => switch (this) {
    MasteryStatus.notAttempted => 'Not Attempted',
    MasteryStatus.learning => 'Learning',
    MasteryStatus.developing => 'Developing',
    MasteryStatus.proficient => 'Proficient',
    MasteryStatus.mastered => 'Mastered',
    MasteryStatus.decaying => 'Decaying',
    MasteryStatus.needsReview => 'Needs Review',
  };

  Color get color => switch (this) {
    MasteryStatus.notAttempted => Colors.grey,
    MasteryStatus.learning => Colors.blue,
    MasteryStatus.developing => Colors.orange,
    MasteryStatus.proficient => Colors.lightGreen,
    MasteryStatus.mastered => Colors.green,
    MasteryStatus.decaying => Colors.redAccent,
    MasteryStatus.needsReview => Colors.amber,
  };
}

enum ChapterStatus {
  notStarted,
  inProgress,
  needsReview,
  completed,
  mastered,
}

enum SubjectStatus {
  onTrack,
  needsAttention,
  critical,
}

enum MisconceptionSeverity {
  low,
  medium,
  high,
  critical,
}

enum RecommendationType {
  practiceWorksheet,
  conceptReview,
  videoLesson,
  peerTutoring,
  teacherIntervention,
  remedialClass,
  formativeAssessment,
}

enum Priority {
  low,
  medium,
  high,
  urgent,
}

extension PriorityX on Priority {
  String get label => switch (this) {
    Priority.low => 'Low',
    Priority.medium => 'Medium',
    Priority.high => 'High',
    Priority.urgent => 'Urgent',
  };

  Color get color => switch (this) {
    Priority.low => Colors.grey,
    Priority.medium => Colors.blue,
    Priority.high => Colors.orange,
    Priority.urgent => Colors.red,
  };
}

enum GapSeverity {
  critical,
  high,
  medium,
  low,
}

extension GapSeverityX on GapSeverity {
  String get label => switch (this) {
    GapSeverity.critical => 'Critical',
    GapSeverity.high => 'High',
    GapSeverity.medium => 'Medium',
    GapSeverity.low => 'Low',
  };

  Color get color => switch (this) {
    GapSeverity.critical => Colors.red,
    GapSeverity.high => Colors.orange,
    GapSeverity.medium => Colors.amber,
    GapSeverity.low => Colors.blue,
  };
}

enum PracticeType {
  remedial,
  reinforcement,
  challenge,
  mockTest,
  dailyReview,
}

enum PracticeStatus {
  created,
  inProgress,
  completed,
  abandoned,
  expired,
}

enum ReportType {
  studentDetailed,
  studentSummary,
  parentSummary,
  teacherAnalytics,
  classSummary,
  schoolDashboard,
}

enum NotificationType {
  assessmentCreated,
  assessmentAssigned,
  assessmentDue,
  assessmentCompleted,
  evaluationReady,
  reportReady,
  practiceAssigned,
  practiceCompleted,
  masteryUpdate,
  interventionNeeded,
  general,
}

enum ExportFormat { pdf, docx }

@freezed
class DifficultyDistribution with _$DifficultyDistribution {
  const factory DifficultyDistribution({
    required double easy,
    required double medium,
    required double hard,
  }) = _DifficultyDistribution;

  factory DifficultyDistribution.fromJson(Map<String, dynamic> json) => _$DifficultyDistributionFromJson(json);
}

@freezed
class BloomDistribution with _$BloomDistribution {
  const factory BloomDistribution({
    required double remember,
    required double understand,
    required double apply,
    required double analyze,
    required double evaluate,
    required double create,
  }) = _BloomDistribution;

  factory BloomDistribution.fromJson(Map<String, dynamic> json) => _$BloomDistributionFromJson(json);
}

@freezed
class ChapterWeights with _$ChapterWeights {
  const factory ChapterWeights({
    required Map<String, double> weights,
  }) = _ChapterWeights;

  factory ChapterWeights.fromJson(Map<String, dynamic> json) => _$ChapterWeightsFromJson(json);
}

@freezed
class CompetencyWeights with _$CompetencyWeights {
  const factory CompetencyWeights({
    required Map<String, double> weights,
  }) = _CompetencyWeights;

  factory CompetencyWeights.fromJson(Map<String, dynamic> json) => _$CompetencyWeightsFromJson(json);
}

@freezed
class SectionBlueprint with _$SectionBlueprint {
  const factory SectionBlueprint({
    required String id,
    required String label,
    required String name,
    required int marksPerQuestion,
    required int questionCount,
    required int totalMarks,
    required List<BloomLevel> allowedBloomLevels,
    required List<Difficulty> allowedDifficulties,
    @Default(false) bool hasInternalChoice,
    @Default(0) int internalChoiceCount,
  }) = _SectionBlueprint;

  factory SectionBlueprint.fromJson(Map<String, dynamic> json) => _$SectionBlueprintFromJson(json);
}

@freezed
class Blueprint with _$Blueprint {
  const factory Blueprint({
    required int totalMarks,
    required int durationMinutes,
    required DifficultyDistribution difficulty,
    required BloomDistribution bloom,
    required ChapterWeights chapterWeights,
    required CompetencyWeights competencyWeights,
    required List<SectionBlueprint> sections,
    @Default({}) Map<String, dynamic> metadata,
  }) = _Blueprint;

  factory Blueprint.fromJson(Map<String, dynamic> json) => _$BlueprintFromJson(json);
}

@freezed
class Point with _$Point {
  const factory Point({
    required double x,
    required double y,
  }) = _Point;

  factory Point.fromJson(Map<String, dynamic> json) => _$PointFromJson(json);
}
