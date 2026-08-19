// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'answer_sheet.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$AnswerSheetImpl _$$AnswerSheetImplFromJson(Map<String, dynamic> json) =>
    _$AnswerSheetImpl(
      id: json['id'] as String,
      assessmentId: json['assessmentId'] as String,
      studentId: json['studentId'] as String,
      studentName: json['studentName'] as String,
      rollNumber: json['rollNumber'] as String,
      pages: (json['pages'] as List<dynamic>)
          .map((e) => ScannedPage.fromJson(e as Map<String, dynamic>))
          .toList(),
      scanMetadata:
          ScanMetadata.fromJson(json['scanMetadata'] as Map<String, dynamic>),
      responses: (json['responses'] as List<dynamic>)
          .map((e) => QuestionResponse.fromJson(e as Map<String, dynamic>))
          .toList(),
      status: $enumDecode(_$AnswerSheetStatusEnumMap, json['status']),
      submittedAt: DateTime.parse(json['submittedAt'] as String),
      scannedAt: DateTime.parse(json['scannedAt'] as String),
      evaluatedAt: json['evaluatedAt'] == null
          ? null
          : DateTime.parse(json['evaluatedAt'] as String),
      metadata: json['metadata'] as Map<String, dynamic>? ?? const {},
    );

Map<String, dynamic> _$$AnswerSheetImplToJson(_$AnswerSheetImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'assessmentId': instance.assessmentId,
      'studentId': instance.studentId,
      'studentName': instance.studentName,
      'rollNumber': instance.rollNumber,
      'pages': instance.pages,
      'scanMetadata': instance.scanMetadata,
      'responses': instance.responses,
      'status': _$AnswerSheetStatusEnumMap[instance.status]!,
      'submittedAt': instance.submittedAt.toIso8601String(),
      'scannedAt': instance.scannedAt.toIso8601String(),
      'evaluatedAt': instance.evaluatedAt?.toIso8601String(),
      'metadata': instance.metadata,
    };

const _$AnswerSheetStatusEnumMap = {
  AnswerSheetStatus.scanned: 'scanned',
  AnswerSheetStatus.segmented: 'segmented',
  AnswerSheetStatus.ocrCompleted: 'ocrCompleted',
  AnswerSheetStatus.underEvaluation: 'underEvaluation',
  AnswerSheetStatus.evaluated: 'evaluated',
  AnswerSheetStatus.teacherReviewed: 'teacherReviewed',
  AnswerSheetStatus.finalized: 'finalized',
  AnswerSheetStatus.disputed: 'disputed',
};

_$ScannedPageImpl _$$ScannedPageImplFromJson(Map<String, dynamic> json) =>
    _$ScannedPageImpl(
      pageNumber: (json['pageNumber'] as num).toInt(),
      imagePath: json['imagePath'] as String,
      imageUrl: json['imageUrl'] as String,
      width: (json['width'] as num).toInt(),
      height: (json['height'] as num).toInt(),
      qualityScore: (json['qualityScore'] as num).toDouble(),
      orientation: $enumDecode(_$PageOrientationEnumMap, json['orientation']),
      segments: (json['segments'] as List<dynamic>)
          .map((e) => QuestionSegment.fromJson(e as Map<String, dynamic>))
          .toList(),
      preprocessing: json['preprocessing'] as Map<String, dynamic>? ?? const {},
    );

Map<String, dynamic> _$$ScannedPageImplToJson(_$ScannedPageImpl instance) =>
    <String, dynamic>{
      'pageNumber': instance.pageNumber,
      'imagePath': instance.imagePath,
      'imageUrl': instance.imageUrl,
      'width': instance.width,
      'height': instance.height,
      'qualityScore': instance.qualityScore,
      'orientation': _$PageOrientationEnumMap[instance.orientation]!,
      'segments': instance.segments,
      'preprocessing': instance.preprocessing,
    };

const _$PageOrientationEnumMap = {
  PageOrientation.portrait: 'portrait',
  PageOrientation.landscape: 'landscape',
  PageOrientation.auto: 'auto',
};

_$QuestionSegmentImpl _$$QuestionSegmentImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionSegmentImpl(
      id: json['id'] as String,
      questionId: json['questionId'] as String,
      questionNumber: (json['questionNumber'] as num).toInt(),
      type: $enumDecode(_$SegmentTypeEnumMap, json['type']),
      boundingBox: (json['boundingBox'] as List<dynamic>)
          .map((e) => Point.fromJson(e as Map<String, dynamic>))
          .toList(),
      imagePath: json['imagePath'] as String,
      imageUrl: json['imageUrl'] as String,
      ocrText: json['ocrText'] as String,
      ocrTextLatex: json['ocrTextLatex'] as String,
      ocrConfidence: (json['ocrConfidence'] as num).toDouble(),
      visionConfidence: (json['visionConfidence'] as num).toDouble(),
      status: $enumDecode(_$SegmentationStatusEnumMap, json['status']),
      studentAnswerImages: (json['studentAnswerImages'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$QuestionSegmentImplToJson(
        _$QuestionSegmentImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'questionId': instance.questionId,
      'questionNumber': instance.questionNumber,
      'type': _$SegmentTypeEnumMap[instance.type]!,
      'boundingBox': instance.boundingBox,
      'imagePath': instance.imagePath,
      'imageUrl': instance.imageUrl,
      'ocrText': instance.ocrText,
      'ocrTextLatex': instance.ocrTextLatex,
      'ocrConfidence': instance.ocrConfidence,
      'visionConfidence': instance.visionConfidence,
      'status': _$SegmentationStatusEnumMap[instance.status]!,
      'studentAnswerImages': instance.studentAnswerImages,
    };

const _$SegmentTypeEnumMap = {
  SegmentType.textAnswer: 'textAnswer',
  SegmentType.diagram: 'diagram',
  SegmentType.map: 'map',
  SegmentType.graph: 'graph',
  SegmentType.table: 'table',
  SegmentType.mixed: 'mixed',
};

const _$SegmentationStatusEnumMap = {
  SegmentationStatus.detected: 'detected',
  SegmentationStatus.ocrPending: 'ocrPending',
  SegmentationStatus.ocrCompleted: 'ocrCompleted',
  SegmentationStatus.visionPending: 'visionPending',
  SegmentationStatus.visionCompleted: 'visionCompleted',
  SegmentationStatus.readyForEvaluation: 'readyForEvaluation',
  SegmentationStatus.evaluated: 'evaluated',
};

_$ScanMetadataImpl _$$ScanMetadataImplFromJson(Map<String, dynamic> json) =>
    _$ScanMetadataImpl(
      deviceId: json['deviceId'] as String,
      appVersion: json['appVersion'] as String,
      totalPages: (json['totalPages'] as num).toInt(),
      avgQualityScore: (json['avgQualityScore'] as num).toDouble(),
      scanDurationMs: (json['scanDurationMs'] as num).toInt(),
      lighting: $enumDecode(_$LightingConditionEnumMap, json['lighting']),
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$ScanMetadataImplToJson(_$ScanMetadataImpl instance) =>
    <String, dynamic>{
      'deviceId': instance.deviceId,
      'appVersion': instance.appVersion,
      'totalPages': instance.totalPages,
      'avgQualityScore': instance.avgQualityScore,
      'scanDurationMs': instance.scanDurationMs,
      'lighting': _$LightingConditionEnumMap[instance.lighting]!,
      'warnings': instance.warnings,
    };

const _$LightingConditionEnumMap = {
  LightingCondition.good: 'good',
  LightingCondition.fair: 'fair',
  LightingCondition.poor: 'poor',
  LightingCondition.unknown: 'unknown',
};

_$QuestionResponseImpl _$$QuestionResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionResponseImpl(
      questionId: json['questionId'] as String,
      questionNumber: (json['questionNumber'] as num).toInt(),
      studentAnswer: json['studentAnswer'] as String,
      studentAnswerLatex: json['studentAnswerLatex'] as String,
      studentAnswerImages: (json['studentAnswerImages'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      evaluation: json['evaluation'] == null
          ? null
          : EvaluationResult.fromJson(
              json['evaluation'] as Map<String, dynamic>),
      evaluationStatus:
          $enumDecode(_$EvaluationStatusEnumMap, json['evaluationStatus']),
      evaluatedAt: json['evaluatedAt'] == null
          ? null
          : DateTime.parse(json['evaluatedAt'] as String),
      teacherComment: json['teacherComment'] as String?,
      teacherAdjustedMarks: (json['teacherAdjustedMarks'] as num?)?.toInt(),
    );

Map<String, dynamic> _$$QuestionResponseImplToJson(
        _$QuestionResponseImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'questionNumber': instance.questionNumber,
      'studentAnswer': instance.studentAnswer,
      'studentAnswerLatex': instance.studentAnswerLatex,
      'studentAnswerImages': instance.studentAnswerImages,
      'evaluation': instance.evaluation,
      'evaluationStatus': _$EvaluationStatusEnumMap[instance.evaluationStatus]!,
      'evaluatedAt': instance.evaluatedAt?.toIso8601String(),
      'teacherComment': instance.teacherComment,
      'teacherAdjustedMarks': instance.teacherAdjustedMarks,
    };

const _$EvaluationStatusEnumMap = {
  EvaluationStatus.pending: 'pending',
  EvaluationStatus.aiEvaluated: 'aiEvaluated',
  EvaluationStatus.teacherApproved: 'teacherApproved',
  EvaluationStatus.teacherAdjusted: 'teacherAdjusted',
  EvaluationStatus.disputed: 'disputed',
};

_$EvaluationResultImpl _$$EvaluationResultImplFromJson(
        Map<String, dynamic> json) =>
    _$EvaluationResultImpl(
      id: json['id'] as String,
      awardedMarks: (json['awardedMarks'] as num).toInt(),
      maxMarks: (json['maxMarks'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      verdict: $enumDecode(_$EvaluationVerdictEnumMap, json['verdict']),
      markingPoints: (json['markingPoints'] as List<dynamic>)
          .map((e) => MarkingPointResult.fromJson(e as Map<String, dynamic>))
          .toList(),
      rubricLevel: RubricLevelResult.fromJson(
          json['rubricLevel'] as Map<String, dynamic>),
      confidenceScore: (json['confidenceScore'] as num).toDouble(),
      reasoning: json['reasoning'] as String,
      strengths:
          (json['strengths'] as List<dynamic>).map((e) => e as String).toList(),
      gaps: (json['gaps'] as List<dynamic>).map((e) => e as String).toList(),
      carelessErrors: (json['carelessErrors'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      estimatedTimeSpentSeconds:
          (json['estimatedTimeSpentSeconds'] as num).toInt(),
      metadata: json['metadata'] as Map<String, dynamic>? ?? const {},
    );

Map<String, dynamic> _$$EvaluationResultImplToJson(
        _$EvaluationResultImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'awardedMarks': instance.awardedMarks,
      'maxMarks': instance.maxMarks,
      'percentage': instance.percentage,
      'verdict': _$EvaluationVerdictEnumMap[instance.verdict]!,
      'markingPoints': instance.markingPoints,
      'rubricLevel': instance.rubricLevel,
      'confidenceScore': instance.confidenceScore,
      'reasoning': instance.reasoning,
      'strengths': instance.strengths,
      'gaps': instance.gaps,
      'carelessErrors': instance.carelessErrors,
      'estimatedTimeSpentSeconds': instance.estimatedTimeSpentSeconds,
      'metadata': instance.metadata,
    };

const _$EvaluationVerdictEnumMap = {
  EvaluationVerdict.fullCredit: 'fullCredit',
  EvaluationVerdict.partialCredit: 'partialCredit',
  EvaluationVerdict.noCredit: 'noCredit',
  EvaluationVerdict.carelessError: 'carelessError',
  EvaluationVerdict.conceptualError: 'conceptualError',
  EvaluationVerdict.blank: 'blank',
};

_$MarkingPointResultImpl _$$MarkingPointResultImplFromJson(
        Map<String, dynamic> json) =>
    _$MarkingPointResultImpl(
      markingPointId: json['markingPointId'] as String,
      awarded: json['awarded'] as bool,
      reason: json['reason'] as String,
      similarityScore: (json['similarityScore'] as num).toDouble(),
    );

Map<String, dynamic> _$$MarkingPointResultImplToJson(
        _$MarkingPointResultImpl instance) =>
    <String, dynamic>{
      'markingPointId': instance.markingPointId,
      'awarded': instance.awarded,
      'reason': instance.reason,
      'similarityScore': instance.similarityScore,
    };

_$RubricLevelResultImpl _$$RubricLevelResultImplFromJson(
        Map<String, dynamic> json) =>
    _$RubricLevelResultImpl(
      level: (json['level'] as num).toInt(),
      label: json['label'] as String,
      justification: json['justification'] as String,
    );

Map<String, dynamic> _$$RubricLevelResultImplToJson(
        _$RubricLevelResultImpl instance) =>
    <String, dynamic>{
      'level': instance.level,
      'label': instance.label,
      'justification': instance.justification,
    };
