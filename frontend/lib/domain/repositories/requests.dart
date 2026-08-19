import 'package:freezed_annotation/freezed_annotation.dart';

import '../entities/entities.dart';

part 'requests.freezed.dart';
part 'requests.g.dart';

@freezed
class CreateAssessmentRequest with _$CreateAssessmentRequest {
  const factory CreateAssessmentRequest({
    required String teacherId,
    required String schoolId,
    required String title,
    required String subject,
    required int grade,
    required List<String> chapterIds,
    required BlueprintRequest blueprint,
    String? templateId,
  }) = _CreateAssessmentRequest;

  factory CreateAssessmentRequest.fromJson(Map<String, dynamic> json) => _$CreateAssessmentRequestFromJson(json);
}

@freezed
class BlueprintRequest with _$BlueprintRequest {
  const factory BlueprintRequest({
    required int totalMarks,
    required int durationMinutes,
    required DifficultyDistribution difficulty,
    required BloomDistribution bloom,
    required ChapterWeights chapterWeights,
    required CompetencyWeights competencyWeights,
    required List<SectionBlueprint> sections,
    Map<String, dynamic>? schoolTemplate,
  }) = _BlueprintRequest;

  factory BlueprintRequest.fromJson(Map<String, dynamic> json) => _$BlueprintRequestFromJson(json);
}

@freezed
class QuestionSearchParams with _$QuestionSearchParams {
  const factory QuestionSearchParams({
    required String subject,
    required int grade,
    List<String>? chapterIds,
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
    List<QuestionSource>? sources,
  }) = _QuestionSearchParams;

  factory QuestionSearchParams.fromJson(Map<String, dynamic> json) => _$QuestionSearchParamsFromJson(json);
}

@freezed
class QuestionOptimizationResult with _$QuestionOptimizationResult {
  const factory QuestionOptimizationResult({
    required List<Question> selectedQuestions,
    required List<Question> rejectedQuestions,
    required Map<String, dynamic> optimizationMetrics,
    required List<String> warnings,
    required List<String> gaps,
  }) = _QuestionOptimizationResult;

  factory QuestionOptimizationResult.fromJson(Map<String, dynamic> json) => _$QuestionOptimizationResultFromJson(json);
}

@freezed
class PaperGenerationRequest with _$PaperGenerationRequest {
  const factory PaperGenerationRequest({
    required String assessmentId,
    required Blueprint blueprint,
    required List<Question> selectedQuestions,
    required SchoolTemplate template,
    Map<String, dynamic>? formattingOptions,
  }) = _PaperGenerationRequest;

  factory PaperGenerationRequest.fromJson(Map<String, dynamic> json) => _$PaperGenerationRequestFromJson(json);
}

@freezed
class GeneratedPaper with _$GeneratedPaper {
  const factory GeneratedPaper({
    required String id,
    required String assessmentId,
    required List<GeneratedSection> sections,
    required String formattedContent,
    required String formattedContentLatex,
    required Map<String, dynamic> answerKey,
    required PaperMetadata metadata,
  }) = _GeneratedPaper;

  factory GeneratedPaper.fromJson(Map<String, dynamic> json) => _$GeneratedPaperFromJson(json);
}

@freezed
class GeneratedSection with _$GeneratedSection {
  const factory GeneratedSection({
    required String sectionId,
    required String label,
    required String name,
    required List<GeneratedQuestion> questions,
    required int totalMarks,
  }) = _GeneratedSection;

  factory GeneratedSection.fromJson(Map<String, dynamic> json) => _$GeneratedSectionFromJson(json);
}

@freezed
class GeneratedQuestion with _$GeneratedQuestion {
  const factory GeneratedQuestion({
    required String questionId,
    required int displayNumber,
    required String stem,
    required String stemLatex,
    required List<QuestionPart> parts,
    required int marks,
    required String bloomLevel,
    required String difficulty,
    String? internalChoiceText,
  }) = _GeneratedQuestion;

  factory GeneratedQuestion.fromJson(Map<String, dynamic> json) => _$GeneratedQuestionFromJson(json);
}

@freezed
class PaperMetadata with _$PaperMetadata {
  const factory PaperMetadata({
    required String assessmentTitle,
    required String subject,
    required int grade,
    required int totalMarks,
    required int durationMinutes,
    required DateTime generatedAt,
    required String generatedBy,
    required String version,
  }) = _PaperMetadata;

  factory PaperMetadata.fromJson(Map<String, dynamic> json) => _$PaperMetadataFromJson(json);
}

@freezed
class SchoolTemplate with _$SchoolTemplate {
  const factory SchoolTemplate({
    required String id,
    required String schoolId,
    required String name,
    @Default('') String tagline,
    @Default('#000000') String brandColor,
    required String headerHtml,
    required String footerHtml,
    required String logoUrl,
    required double marginTop,
    required double marginBottom,
    required double marginLeft,
    required double marginRight,
    required String fontFamily,
    required int fontSize,
    required double lineHeight,
    required Map<String, dynamic> sectionFormatting,
    required bool isDefault,
  }) = _SchoolTemplate;

  factory SchoolTemplate.fromJson(Map<String, dynamic> json) => _$SchoolTemplateFromJson(json);
}

@freezed
class AnswerSheetUpload with _$AnswerSheetUpload {
  const factory AnswerSheetUpload({
    required String assessmentId,
    required String studentId,
    required String studentName,
    required String rollNumber,
    required List<String> imagePaths,
    required ScanMetadata scanMetadata,
  }) = _AnswerSheetUpload;

  factory AnswerSheetUpload.fromJson(Map<String, dynamic> json) => _$AnswerSheetUploadFromJson(json);
}

@freezed
class ScanRequest with _$ScanRequest {
  const factory ScanRequest({
    required String answerSheetId,
    required List<String> imagePaths,
    required ScanOptions options,
  }) = _ScanRequest;

  factory ScanRequest.fromJson(Map<String, dynamic> json) => _$ScanRequestFromJson(json);
}

@freezed
class ScanOptions with _$ScanOptions {
  const factory ScanOptions({
    @Default(true) bool autoRotate,
    @Default(true) bool perspectiveCorrection,
    @Default(true) bool shadowRemoval,
    @Default(true) bool noiseReduction,
    @Default(true) bool contrastEnhancement,
    @Default(true) bool whiteBalance,
    @Default(true) bool dewarp,
    @Default(true) bool pageOrdering,
    @Default(300) int targetDpi,
  }) = _ScanOptions;

  factory ScanOptions.fromJson(Map<String, dynamic> json) => _$ScanOptionsFromJson(json);
}

@freezed
class EvaluationRequest with _$EvaluationRequest {
  const factory EvaluationRequest({
    required String questionId,
    required Question question,
    required String studentAnswer,
    required String studentAnswerLatex,
    required List<String> studentAnswerImages,
    required AnswerScheme answerScheme,
    required EvaluationContext context,
  }) = _EvaluationRequest;

  factory EvaluationRequest.fromJson(Map<String, dynamic> json) => _$EvaluationRequestFromJson(json);
}

@freezed
class EvaluationContext with _$EvaluationContext {
  const factory EvaluationContext({
    required String studentId,
    required String assessmentId,
    required Map<String, double> studentMastery,
    required List<String> previousMisconceptions,
    @Default(false) bool isPractice,
  }) = _EvaluationContext;

  factory EvaluationContext.fromJson(Map<String, dynamic> json) => _$EvaluationContextFromJson(json);
}

@freezed
class TeacherReviewRequest with _$TeacherReviewRequest {
  const factory TeacherReviewRequest({
    required String evaluationId,
    required String teacherId,
    int? adjustedMarks,
    EvaluationVerdict? adjustedVerdict,
    String? comment,
    required bool approved,
  }) = _TeacherReviewRequest;

  factory TeacherReviewRequest.fromJson(Map<String, dynamic> json) => _$TeacherReviewRequestFromJson(json);
}

@freezed
class MasteryAttempt with _$MasteryAttempt {
  const factory MasteryAttempt({
    required String studentId,
    required String conceptId,
    required bool correct,
    required double confidence,
    required int timeSpentSeconds,
    required DateTime attemptedAt,
    required String source,
    String? assessmentId,
    String? questionId,
  }) = _MasteryAttempt;

  factory MasteryAttempt.fromJson(Map<String, dynamic> json) => _$MasteryAttemptFromJson(json);
}

@freezed
class PracticeRequest with _$PracticeRequest {
  const factory PracticeRequest({
    required String studentId,
    required List<String> conceptIds,
    required PracticeType type,
    required int questionCount,
    required int durationMinutes,
    Map<String, dynamic>? options,
  }) = _PracticeRequest;

  factory PracticeRequest.fromJson(Map<String, dynamic> json) => _$PracticeRequestFromJson(json);
}

@freezed
class PracticeSession with _$PracticeSession {
  const factory PracticeSession({
    required String id,
    required String studentId,
    required List<String> conceptIds,
    required PracticeType type,
    required int questionCount,
    required int durationMinutes,
    required List<PracticeQuestion> questions,
    required PracticeStatus status,
    required DateTime createdAt,
    DateTime? startedAt,
    DateTime? completedAt,
    PracticeResult? result,
  }) = _PracticeSession;

  factory PracticeSession.fromJson(Map<String, dynamic> json) => _$PracticeSessionFromJson(json);
}

@freezed
class PracticeQuestion with _$PracticeQuestion {
  const factory PracticeQuestion({
    required String questionId,
    required int displayNumber,
    required String stem,
    required String stemLatex,
    required List<QuestionPart> parts,
    required int marks,
    String? hint,
    String? explanation,
  }) = _PracticeQuestion;

  factory PracticeQuestion.fromJson(Map<String, dynamic> json) => _$PracticeQuestionFromJson(json);
}

@freezed
class PracticeSubmission with _$PracticeSubmission {
  const factory PracticeSubmission({
    required String sessionId,
    required String studentId,
    required List<PracticeAnswer> answers,
    required Duration timeSpent,
  }) = _PracticeSubmission;

  factory PracticeSubmission.fromJson(Map<String, dynamic> json) => _$PracticeSubmissionFromJson(json);
}

@freezed
class PracticeAnswer with _$PracticeAnswer {
  const factory PracticeAnswer({
    required String questionId,
    required String answer,
    required String answerLatex,
    required int timeSpentSeconds,
    required bool usedHint,
  }) = _PracticeAnswer;

  factory PracticeAnswer.fromJson(Map<String, dynamic> json) => _$PracticeAnswerFromJson(json);
}

@freezed
class PracticeAnswerResult with _$PracticeAnswerResult {
  const factory PracticeAnswerResult({
    required String questionId,
    required bool isCorrect,
    required int awardedMarks,
    required int maxMarks,
    required String feedback,
    required String explanation,
    required List<String> relatedConcepts,
    required double masteryGain,
  }) = _PracticeAnswerResult;

  factory PracticeAnswerResult.fromJson(Map<String, dynamic> json) => _$PracticeAnswerResultFromJson(json);
}

@freezed
class PracticeResult with _$PracticeResult {
  const factory PracticeResult({
    required int score,
    required int maxScore,
    required double percentage,
    required Map<String, double> conceptScores,
    required List<String> strengths,
    required List<String> weaknesses,
    required List<ActionableRecommendation> recommendations,
    required Duration timeSpent,
  }) = _PracticeResult;

  factory PracticeResult.fromJson(Map<String, dynamic> json) => _$PracticeResultFromJson(json);
}

@freezed
class ReportRequest with _$ReportRequest {
  const factory ReportRequest({
    required String assessmentId,
    required String studentId,
    required ReportType type,
    Map<String, dynamic>? options,
  }) = _ReportRequest;

  factory ReportRequest.fromJson(Map<String, dynamic> json) => _$ReportRequestFromJson(json);
}

@freezed
class BulkReportRequest with _$BulkReportRequest {
  const factory BulkReportRequest({
    required String assessmentId,
    required List<String> studentIds,
    required ReportType type,
    Map<String, dynamic>? options,
  }) = _BulkReportRequest;

  factory BulkReportRequest.fromJson(Map<String, dynamic> json) => _$BulkReportRequestFromJson(json);
}

@freezed
class Notification with _$Notification {
  const factory Notification({
    required String id,
    required String userId,
    required NotificationType type,
    required String title,
    required String body,
    required Map<String, dynamic> data,
    required DateTime createdAt,
    required bool isRead,
    DateTime? readAt,
  }) = _Notification;

  factory Notification.fromJson(Map<String, dynamic> json) => _$NotificationFromJson(json);
}

@freezed
class WhatsAppDeepLink with _$WhatsAppDeepLink {
  const factory WhatsAppDeepLink({
    required String phoneNumber,
    required String message,
    required String deepLinkUrl,
    required String fallbackUrl,
  }) = _WhatsAppDeepLink;

  factory WhatsAppDeepLink.fromJson(Map<String, dynamic> json) => _$WhatsAppDeepLinkFromJson(json);
}
