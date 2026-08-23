// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'requests.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$CreateAssessmentRequestImpl _$$CreateAssessmentRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$CreateAssessmentRequestImpl(
      teacherId: json['teacherId'] as String,
      schoolId: json['schoolId'] as String,
      title: json['title'] as String,
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      chapterIds: (json['chapterIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      blueprint:
          BlueprintRequest.fromJson(json['blueprint'] as Map<String, dynamic>),
      templateId: json['templateId'] as String?,
    );

Map<String, dynamic> _$$CreateAssessmentRequestImplToJson(
        _$CreateAssessmentRequestImpl instance) =>
    <String, dynamic>{
      'teacherId': instance.teacherId,
      'schoolId': instance.schoolId,
      'title': instance.title,
      'subject': instance.subject,
      'grade': instance.grade,
      'chapterIds': instance.chapterIds,
      'blueprint': instance.blueprint,
      'templateId': instance.templateId,
    };

_$BlueprintRequestImpl _$$BlueprintRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$BlueprintRequestImpl(
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
      schoolTemplate: json['schoolTemplate'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$BlueprintRequestImplToJson(
        _$BlueprintRequestImpl instance) =>
    <String, dynamic>{
      'totalMarks': instance.totalMarks,
      'durationMinutes': instance.durationMinutes,
      'difficulty': instance.difficulty,
      'bloom': instance.bloom,
      'chapterWeights': instance.chapterWeights,
      'competencyWeights': instance.competencyWeights,
      'sections': instance.sections,
      'schoolTemplate': instance.schoolTemplate,
    };

_$QuestionSearchParamsImpl _$$QuestionSearchParamsImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionSearchParamsImpl(
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      chapterIds: (json['chapterIds'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      competencyIds: (json['competencyIds'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      bloomLevels: (json['bloomLevels'] as List<dynamic>?)
          ?.map((e) => $enumDecode(_$BloomLevelEnumMap, e))
          .toList(),
      difficulties: (json['difficulties'] as List<dynamic>?)
          ?.map((e) => $enumDecode(_$DifficultyEnumMap, e))
          .toList(),
      types: (json['types'] as List<dynamic>?)
          ?.map((e) => $enumDecode(_$QuestionTypeEnumMap, e))
          .toList(),
      minMarks: (json['minMarks'] as num?)?.toInt(),
      maxMarks: (json['maxMarks'] as num?)?.toInt(),
      limit: (json['limit'] as num?)?.toInt(),
      offset: (json['offset'] as num?)?.toInt(),
      keyword: json['keyword'] as String?,
      minQualityScore: (json['minQualityScore'] as num?)?.toDouble(),
      sources: (json['sources'] as List<dynamic>?)
          ?.map((e) => $enumDecode(_$QuestionSourceEnumMap, e))
          .toList(),
    );

Map<String, dynamic> _$$QuestionSearchParamsImplToJson(
        _$QuestionSearchParamsImpl instance) =>
    <String, dynamic>{
      'subject': instance.subject,
      'grade': instance.grade,
      'chapterIds': instance.chapterIds,
      'competencyIds': instance.competencyIds,
      'bloomLevels':
          instance.bloomLevels?.map((e) => _$BloomLevelEnumMap[e]!).toList(),
      'difficulties':
          instance.difficulties?.map((e) => _$DifficultyEnumMap[e]!).toList(),
      'types': instance.types?.map((e) => _$QuestionTypeEnumMap[e]!).toList(),
      'minMarks': instance.minMarks,
      'maxMarks': instance.maxMarks,
      'limit': instance.limit,
      'offset': instance.offset,
      'keyword': instance.keyword,
      'minQualityScore': instance.minQualityScore,
      'sources':
          instance.sources?.map((e) => _$QuestionSourceEnumMap[e]!).toList(),
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

const _$QuestionTypeEnumMap = {
  QuestionType.mcq: 'mcq',
  QuestionType.veryShortAnswer: 'veryShortAnswer',
  QuestionType.shortAnswer: 'shortAnswer',
  QuestionType.longAnswer: 'longAnswer',
  QuestionType.veryLongAnswer: 'veryLongAnswer',
  QuestionType.caseStudy: 'caseStudy',
  QuestionType.assertionReason: 'assertionReason',
  QuestionType.mapBased: 'mapBased',
  QuestionType.diagramBased: 'diagramBased',
  QuestionType.graphBased: 'graphBased',
  QuestionType.tableBased: 'tableBased',
  QuestionType.competencyBased: 'competencyBased',
};

const _$QuestionSourceEnumMap = {
  QuestionSource.cbseBoardPaper: 'cbseBoardPaper',
  QuestionSource.cbseSamplePaper: 'cbseSamplePaper',
  QuestionSource.cbseQuestionBank: 'cbseQuestionBank',
  QuestionSource.ncertExemplar: 'ncertExemplar',
  QuestionSource.ncertTextbook: 'ncertTextbook',
  QuestionSource.schoolDatabase: 'schoolDatabase',
  QuestionSource.teacherCreated: 'teacherCreated',
  QuestionSource.aiGenerated: 'aiGenerated',
  QuestionSource.competencyFramework: 'competencyFramework',
};

_$QuestionOptimizationResultImpl _$$QuestionOptimizationResultImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionOptimizationResultImpl(
      selectedQuestions: (json['selectedQuestions'] as List<dynamic>)
          .map((e) => Question.fromJson(e as Map<String, dynamic>))
          .toList(),
      rejectedQuestions: (json['rejectedQuestions'] as List<dynamic>)
          .map((e) => Question.fromJson(e as Map<String, dynamic>))
          .toList(),
      optimizationMetrics: json['optimizationMetrics'] as Map<String, dynamic>,
      warnings:
          (json['warnings'] as List<dynamic>).map((e) => e as String).toList(),
      gaps: (json['gaps'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$QuestionOptimizationResultImplToJson(
        _$QuestionOptimizationResultImpl instance) =>
    <String, dynamic>{
      'selectedQuestions': instance.selectedQuestions,
      'rejectedQuestions': instance.rejectedQuestions,
      'optimizationMetrics': instance.optimizationMetrics,
      'warnings': instance.warnings,
      'gaps': instance.gaps,
    };

_$PaperGenerationRequestImpl _$$PaperGenerationRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$PaperGenerationRequestImpl(
      assessmentId: json['assessmentId'] as String,
      blueprint: Blueprint.fromJson(json['blueprint'] as Map<String, dynamic>),
      selectedQuestions: (json['selectedQuestions'] as List<dynamic>)
          .map((e) => Question.fromJson(e as Map<String, dynamic>))
          .toList(),
      template:
          SchoolTemplate.fromJson(json['template'] as Map<String, dynamic>),
      formattingOptions: json['formattingOptions'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$PaperGenerationRequestImplToJson(
        _$PaperGenerationRequestImpl instance) =>
    <String, dynamic>{
      'assessmentId': instance.assessmentId,
      'blueprint': instance.blueprint,
      'selectedQuestions': instance.selectedQuestions,
      'template': instance.template,
      'formattingOptions': instance.formattingOptions,
    };

_$GeneratedPaperImpl _$$GeneratedPaperImplFromJson(Map<String, dynamic> json) =>
    _$GeneratedPaperImpl(
      id: json['id'] as String,
      assessmentId: json['assessmentId'] as String,
      sections: (json['sections'] as List<dynamic>)
          .map((e) => GeneratedSection.fromJson(e as Map<String, dynamic>))
          .toList(),
      formattedContent: json['formattedContent'] as String,
      formattedContentLatex: json['formattedContentLatex'] as String,
      answerKey: json['answerKey'] as Map<String, dynamic>,
      metadata:
          PaperMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$GeneratedPaperImplToJson(
        _$GeneratedPaperImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'assessmentId': instance.assessmentId,
      'sections': instance.sections,
      'formattedContent': instance.formattedContent,
      'formattedContentLatex': instance.formattedContentLatex,
      'answerKey': instance.answerKey,
      'metadata': instance.metadata,
    };

_$GeneratedSectionImpl _$$GeneratedSectionImplFromJson(
        Map<String, dynamic> json) =>
    _$GeneratedSectionImpl(
      sectionId: json['sectionId'] as String,
      label: json['label'] as String,
      name: json['name'] as String,
      questions: (json['questions'] as List<dynamic>)
          .map((e) => GeneratedQuestion.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalMarks: (json['totalMarks'] as num).toInt(),
    );

Map<String, dynamic> _$$GeneratedSectionImplToJson(
        _$GeneratedSectionImpl instance) =>
    <String, dynamic>{
      'sectionId': instance.sectionId,
      'label': instance.label,
      'name': instance.name,
      'questions': instance.questions,
      'totalMarks': instance.totalMarks,
    };

_$GeneratedQuestionImpl _$$GeneratedQuestionImplFromJson(
        Map<String, dynamic> json) =>
    _$GeneratedQuestionImpl(
      questionId: json['questionId'] as String,
      displayNumber: (json['displayNumber'] as num).toInt(),
      stem: json['stem'] as String,
      stemLatex: json['stemLatex'] as String,
      parts: (json['parts'] as List<dynamic>)
          .map((e) => QuestionPart.fromJson(e as Map<String, dynamic>))
          .toList(),
      marks: (json['marks'] as num).toInt(),
      bloomLevel: json['bloomLevel'] as String,
      difficulty: json['difficulty'] as String,
      type: json['type'] as String,
      internalChoiceText: json['internalChoiceText'] as String?,
    );

Map<String, dynamic> _$$GeneratedQuestionImplToJson(
        _$GeneratedQuestionImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'displayNumber': instance.displayNumber,
      'stem': instance.stem,
      'stemLatex': instance.stemLatex,
      'parts': instance.parts,
      'marks': instance.marks,
      'bloomLevel': instance.bloomLevel,
      'difficulty': instance.difficulty,
      'type': instance.type,
      'internalChoiceText': instance.internalChoiceText,
    };

_$PaperMetadataImpl _$$PaperMetadataImplFromJson(Map<String, dynamic> json) =>
    _$PaperMetadataImpl(
      assessmentTitle: json['assessmentTitle'] as String,
      schoolName: json['schoolName'] as String,
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      totalMarks: (json['totalMarks'] as num).toInt(),
      durationMinutes: (json['durationMinutes'] as num).toInt(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
      generatedBy: json['generatedBy'] as String,
      version: json['version'] as String,
    );

Map<String, dynamic> _$$PaperMetadataImplToJson(_$PaperMetadataImpl instance) =>
    <String, dynamic>{
      'assessmentTitle': instance.assessmentTitle,
      'schoolName': instance.schoolName,
      'subject': instance.subject,
      'grade': instance.grade,
      'totalMarks': instance.totalMarks,
      'durationMinutes': instance.durationMinutes,
      'generatedAt': instance.generatedAt.toIso8601String(),
      'generatedBy': instance.generatedBy,
      'version': instance.version,
    };

_$SchoolTemplateImpl _$$SchoolTemplateImplFromJson(Map<String, dynamic> json) =>
    _$SchoolTemplateImpl(
      id: json['id'] as String,
      schoolId: json['schoolId'] as String,
      name: json['name'] as String,
      tagline: json['tagline'] as String? ?? '',
      brandColor: json['brandColor'] as String? ?? '#000000',
      headerHtml: json['headerHtml'] as String,
      footerHtml: json['footerHtml'] as String,
      logoUrl: json['logoUrl'] as String,
      marginTop: (json['marginTop'] as num).toDouble(),
      marginBottom: (json['marginBottom'] as num).toDouble(),
      marginLeft: (json['marginLeft'] as num).toDouble(),
      marginRight: (json['marginRight'] as num).toDouble(),
      fontFamily: json['fontFamily'] as String,
      fontSize: (json['fontSize'] as num).toInt(),
      lineHeight: (json['lineHeight'] as num).toDouble(),
      sectionFormatting: json['sectionFormatting'] as Map<String, dynamic>,
      isDefault: json['isDefault'] as bool,
    );

Map<String, dynamic> _$$SchoolTemplateImplToJson(
        _$SchoolTemplateImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'schoolId': instance.schoolId,
      'name': instance.name,
      'tagline': instance.tagline,
      'brandColor': instance.brandColor,
      'headerHtml': instance.headerHtml,
      'footerHtml': instance.footerHtml,
      'logoUrl': instance.logoUrl,
      'marginTop': instance.marginTop,
      'marginBottom': instance.marginBottom,
      'marginLeft': instance.marginLeft,
      'marginRight': instance.marginRight,
      'fontFamily': instance.fontFamily,
      'fontSize': instance.fontSize,
      'lineHeight': instance.lineHeight,
      'sectionFormatting': instance.sectionFormatting,
      'isDefault': instance.isDefault,
    };

_$AnswerSheetUploadImpl _$$AnswerSheetUploadImplFromJson(
        Map<String, dynamic> json) =>
    _$AnswerSheetUploadImpl(
      assessmentId: json['assessmentId'] as String,
      studentId: json['studentId'] as String,
      studentName: json['studentName'] as String,
      rollNumber: json['rollNumber'] as String,
      imagePaths: (json['imagePaths'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      scanMetadata:
          ScanMetadata.fromJson(json['scanMetadata'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$AnswerSheetUploadImplToJson(
        _$AnswerSheetUploadImpl instance) =>
    <String, dynamic>{
      'assessmentId': instance.assessmentId,
      'studentId': instance.studentId,
      'studentName': instance.studentName,
      'rollNumber': instance.rollNumber,
      'imagePaths': instance.imagePaths,
      'scanMetadata': instance.scanMetadata,
    };

_$ScanRequestImpl _$$ScanRequestImplFromJson(Map<String, dynamic> json) =>
    _$ScanRequestImpl(
      answerSheetId: json['answerSheetId'] as String,
      imagePaths: (json['imagePaths'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      options: ScanOptions.fromJson(json['options'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$ScanRequestImplToJson(_$ScanRequestImpl instance) =>
    <String, dynamic>{
      'answerSheetId': instance.answerSheetId,
      'imagePaths': instance.imagePaths,
      'options': instance.options,
    };

_$ScanOptionsImpl _$$ScanOptionsImplFromJson(Map<String, dynamic> json) =>
    _$ScanOptionsImpl(
      autoRotate: json['autoRotate'] as bool? ?? true,
      perspectiveCorrection: json['perspectiveCorrection'] as bool? ?? true,
      shadowRemoval: json['shadowRemoval'] as bool? ?? true,
      noiseReduction: json['noiseReduction'] as bool? ?? true,
      contrastEnhancement: json['contrastEnhancement'] as bool? ?? true,
      whiteBalance: json['whiteBalance'] as bool? ?? true,
      dewarp: json['dewarp'] as bool? ?? true,
      pageOrdering: json['pageOrdering'] as bool? ?? true,
      targetDpi: (json['targetDpi'] as num?)?.toInt() ?? 300,
    );

Map<String, dynamic> _$$ScanOptionsImplToJson(_$ScanOptionsImpl instance) =>
    <String, dynamic>{
      'autoRotate': instance.autoRotate,
      'perspectiveCorrection': instance.perspectiveCorrection,
      'shadowRemoval': instance.shadowRemoval,
      'noiseReduction': instance.noiseReduction,
      'contrastEnhancement': instance.contrastEnhancement,
      'whiteBalance': instance.whiteBalance,
      'dewarp': instance.dewarp,
      'pageOrdering': instance.pageOrdering,
      'targetDpi': instance.targetDpi,
    };

_$EvaluationRequestImpl _$$EvaluationRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$EvaluationRequestImpl(
      questionId: json['questionId'] as String,
      question: Question.fromJson(json['question'] as Map<String, dynamic>),
      studentAnswer: json['studentAnswer'] as String,
      studentAnswerLatex: json['studentAnswerLatex'] as String,
      studentAnswerImages: (json['studentAnswerImages'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      answerScheme:
          AnswerScheme.fromJson(json['answerScheme'] as Map<String, dynamic>),
      context:
          EvaluationContext.fromJson(json['context'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$EvaluationRequestImplToJson(
        _$EvaluationRequestImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'question': instance.question,
      'studentAnswer': instance.studentAnswer,
      'studentAnswerLatex': instance.studentAnswerLatex,
      'studentAnswerImages': instance.studentAnswerImages,
      'answerScheme': instance.answerScheme,
      'context': instance.context,
    };

_$EvaluationContextImpl _$$EvaluationContextImplFromJson(
        Map<String, dynamic> json) =>
    _$EvaluationContextImpl(
      studentId: json['studentId'] as String,
      assessmentId: json['assessmentId'] as String,
      studentMastery: (json['studentMastery'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      previousMisconceptions: (json['previousMisconceptions'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      isPractice: json['isPractice'] as bool? ?? false,
    );

Map<String, dynamic> _$$EvaluationContextImplToJson(
        _$EvaluationContextImpl instance) =>
    <String, dynamic>{
      'studentId': instance.studentId,
      'assessmentId': instance.assessmentId,
      'studentMastery': instance.studentMastery,
      'previousMisconceptions': instance.previousMisconceptions,
      'isPractice': instance.isPractice,
    };

_$TeacherReviewRequestImpl _$$TeacherReviewRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$TeacherReviewRequestImpl(
      evaluationId: json['evaluationId'] as String,
      teacherId: json['teacherId'] as String,
      adjustedMarks: (json['adjustedMarks'] as num?)?.toInt(),
      adjustedVerdict: $enumDecodeNullable(
          _$EvaluationVerdictEnumMap, json['adjustedVerdict']),
      comment: json['comment'] as String?,
      approved: json['approved'] as bool,
    );

Map<String, dynamic> _$$TeacherReviewRequestImplToJson(
        _$TeacherReviewRequestImpl instance) =>
    <String, dynamic>{
      'evaluationId': instance.evaluationId,
      'teacherId': instance.teacherId,
      'adjustedMarks': instance.adjustedMarks,
      'adjustedVerdict': _$EvaluationVerdictEnumMap[instance.adjustedVerdict],
      'comment': instance.comment,
      'approved': instance.approved,
    };

const _$EvaluationVerdictEnumMap = {
  EvaluationVerdict.fullCredit: 'fullCredit',
  EvaluationVerdict.partialCredit: 'partialCredit',
  EvaluationVerdict.noCredit: 'noCredit',
  EvaluationVerdict.carelessError: 'carelessError',
  EvaluationVerdict.conceptualError: 'conceptualError',
  EvaluationVerdict.blank: 'blank',
};

_$MasteryAttemptImpl _$$MasteryAttemptImplFromJson(Map<String, dynamic> json) =>
    _$MasteryAttemptImpl(
      studentId: json['studentId'] as String,
      conceptId: json['conceptId'] as String,
      correct: json['correct'] as bool,
      confidence: (json['confidence'] as num).toDouble(),
      timeSpentSeconds: (json['timeSpentSeconds'] as num).toInt(),
      attemptedAt: DateTime.parse(json['attemptedAt'] as String),
      source: json['source'] as String,
      assessmentId: json['assessmentId'] as String?,
      questionId: json['questionId'] as String?,
    );

Map<String, dynamic> _$$MasteryAttemptImplToJson(
        _$MasteryAttemptImpl instance) =>
    <String, dynamic>{
      'studentId': instance.studentId,
      'conceptId': instance.conceptId,
      'correct': instance.correct,
      'confidence': instance.confidence,
      'timeSpentSeconds': instance.timeSpentSeconds,
      'attemptedAt': instance.attemptedAt.toIso8601String(),
      'source': instance.source,
      'assessmentId': instance.assessmentId,
      'questionId': instance.questionId,
    };

_$PracticeRequestImpl _$$PracticeRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$PracticeRequestImpl(
      studentId: json['studentId'] as String,
      conceptIds: (json['conceptIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      type: $enumDecode(_$PracticeTypeEnumMap, json['type']),
      questionCount: (json['questionCount'] as num).toInt(),
      durationMinutes: (json['durationMinutes'] as num).toInt(),
      options: json['options'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$PracticeRequestImplToJson(
        _$PracticeRequestImpl instance) =>
    <String, dynamic>{
      'studentId': instance.studentId,
      'conceptIds': instance.conceptIds,
      'type': _$PracticeTypeEnumMap[instance.type]!,
      'questionCount': instance.questionCount,
      'durationMinutes': instance.durationMinutes,
      'options': instance.options,
    };

const _$PracticeTypeEnumMap = {
  PracticeType.remedial: 'remedial',
  PracticeType.reinforcement: 'reinforcement',
  PracticeType.challenge: 'challenge',
  PracticeType.mockTest: 'mockTest',
  PracticeType.dailyReview: 'dailyReview',
};

_$PracticeSessionImpl _$$PracticeSessionImplFromJson(
        Map<String, dynamic> json) =>
    _$PracticeSessionImpl(
      id: json['id'] as String,
      studentId: json['studentId'] as String,
      conceptIds: (json['conceptIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      type: $enumDecode(_$PracticeTypeEnumMap, json['type']),
      questionCount: (json['questionCount'] as num).toInt(),
      durationMinutes: (json['durationMinutes'] as num).toInt(),
      questions: (json['questions'] as List<dynamic>)
          .map((e) => PracticeQuestion.fromJson(e as Map<String, dynamic>))
          .toList(),
      status: $enumDecode(_$PracticeStatusEnumMap, json['status']),
      createdAt: DateTime.parse(json['createdAt'] as String),
      startedAt: json['startedAt'] == null
          ? null
          : DateTime.parse(json['startedAt'] as String),
      completedAt: json['completedAt'] == null
          ? null
          : DateTime.parse(json['completedAt'] as String),
      result: json['result'] == null
          ? null
          : PracticeResult.fromJson(json['result'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$PracticeSessionImplToJson(
        _$PracticeSessionImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'studentId': instance.studentId,
      'conceptIds': instance.conceptIds,
      'type': _$PracticeTypeEnumMap[instance.type]!,
      'questionCount': instance.questionCount,
      'durationMinutes': instance.durationMinutes,
      'questions': instance.questions,
      'status': _$PracticeStatusEnumMap[instance.status]!,
      'createdAt': instance.createdAt.toIso8601String(),
      'startedAt': instance.startedAt?.toIso8601String(),
      'completedAt': instance.completedAt?.toIso8601String(),
      'result': instance.result,
    };

const _$PracticeStatusEnumMap = {
  PracticeStatus.created: 'created',
  PracticeStatus.inProgress: 'inProgress',
  PracticeStatus.completed: 'completed',
  PracticeStatus.abandoned: 'abandoned',
  PracticeStatus.expired: 'expired',
};

_$PracticeQuestionImpl _$$PracticeQuestionImplFromJson(
        Map<String, dynamic> json) =>
    _$PracticeQuestionImpl(
      questionId: json['questionId'] as String,
      displayNumber: (json['displayNumber'] as num).toInt(),
      stem: json['stem'] as String,
      stemLatex: json['stemLatex'] as String,
      parts: (json['parts'] as List<dynamic>)
          .map((e) => QuestionPart.fromJson(e as Map<String, dynamic>))
          .toList(),
      marks: (json['marks'] as num).toInt(),
      hint: json['hint'] as String?,
      explanation: json['explanation'] as String?,
    );

Map<String, dynamic> _$$PracticeQuestionImplToJson(
        _$PracticeQuestionImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'displayNumber': instance.displayNumber,
      'stem': instance.stem,
      'stemLatex': instance.stemLatex,
      'parts': instance.parts,
      'marks': instance.marks,
      'hint': instance.hint,
      'explanation': instance.explanation,
    };

_$PracticeSubmissionImpl _$$PracticeSubmissionImplFromJson(
        Map<String, dynamic> json) =>
    _$PracticeSubmissionImpl(
      sessionId: json['sessionId'] as String,
      studentId: json['studentId'] as String,
      answers: (json['answers'] as List<dynamic>)
          .map((e) => PracticeAnswer.fromJson(e as Map<String, dynamic>))
          .toList(),
      timeSpent: Duration(microseconds: (json['timeSpent'] as num).toInt()),
    );

Map<String, dynamic> _$$PracticeSubmissionImplToJson(
        _$PracticeSubmissionImpl instance) =>
    <String, dynamic>{
      'sessionId': instance.sessionId,
      'studentId': instance.studentId,
      'answers': instance.answers,
      'timeSpent': instance.timeSpent.inMicroseconds,
    };

_$PracticeAnswerImpl _$$PracticeAnswerImplFromJson(Map<String, dynamic> json) =>
    _$PracticeAnswerImpl(
      questionId: json['questionId'] as String,
      answer: json['answer'] as String,
      answerLatex: json['answerLatex'] as String,
      timeSpentSeconds: (json['timeSpentSeconds'] as num).toInt(),
      usedHint: json['usedHint'] as bool,
    );

Map<String, dynamic> _$$PracticeAnswerImplToJson(
        _$PracticeAnswerImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'answer': instance.answer,
      'answerLatex': instance.answerLatex,
      'timeSpentSeconds': instance.timeSpentSeconds,
      'usedHint': instance.usedHint,
    };

_$PracticeAnswerResultImpl _$$PracticeAnswerResultImplFromJson(
        Map<String, dynamic> json) =>
    _$PracticeAnswerResultImpl(
      questionId: json['questionId'] as String,
      isCorrect: json['isCorrect'] as bool,
      awardedMarks: (json['awardedMarks'] as num).toInt(),
      maxMarks: (json['maxMarks'] as num).toInt(),
      feedback: json['feedback'] as String,
      explanation: json['explanation'] as String,
      relatedConcepts: (json['relatedConcepts'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      masteryGain: (json['masteryGain'] as num).toDouble(),
    );

Map<String, dynamic> _$$PracticeAnswerResultImplToJson(
        _$PracticeAnswerResultImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'isCorrect': instance.isCorrect,
      'awardedMarks': instance.awardedMarks,
      'maxMarks': instance.maxMarks,
      'feedback': instance.feedback,
      'explanation': instance.explanation,
      'relatedConcepts': instance.relatedConcepts,
      'masteryGain': instance.masteryGain,
    };

_$PracticeResultImpl _$$PracticeResultImplFromJson(Map<String, dynamic> json) =>
    _$PracticeResultImpl(
      score: (json['score'] as num).toInt(),
      maxScore: (json['maxScore'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      conceptScores: (json['conceptScores'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      strengths:
          (json['strengths'] as List<dynamic>).map((e) => e as String).toList(),
      weaknesses: (json['weaknesses'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      recommendations: (json['recommendations'] as List<dynamic>)
          .map((e) =>
              ActionableRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
      timeSpent: Duration(microseconds: (json['timeSpent'] as num).toInt()),
    );

Map<String, dynamic> _$$PracticeResultImplToJson(
        _$PracticeResultImpl instance) =>
    <String, dynamic>{
      'score': instance.score,
      'maxScore': instance.maxScore,
      'percentage': instance.percentage,
      'conceptScores': instance.conceptScores,
      'strengths': instance.strengths,
      'weaknesses': instance.weaknesses,
      'recommendations': instance.recommendations,
      'timeSpent': instance.timeSpent.inMicroseconds,
    };

_$ReportRequestImpl _$$ReportRequestImplFromJson(Map<String, dynamic> json) =>
    _$ReportRequestImpl(
      assessmentId: json['assessmentId'] as String,
      studentId: json['studentId'] as String,
      type: $enumDecode(_$ReportTypeEnumMap, json['type']),
      options: json['options'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$ReportRequestImplToJson(_$ReportRequestImpl instance) =>
    <String, dynamic>{
      'assessmentId': instance.assessmentId,
      'studentId': instance.studentId,
      'type': _$ReportTypeEnumMap[instance.type]!,
      'options': instance.options,
    };

const _$ReportTypeEnumMap = {
  ReportType.studentDetailed: 'studentDetailed',
  ReportType.studentSummary: 'studentSummary',
  ReportType.parentSummary: 'parentSummary',
  ReportType.teacherAnalytics: 'teacherAnalytics',
  ReportType.classSummary: 'classSummary',
  ReportType.schoolDashboard: 'schoolDashboard',
};

_$BulkReportRequestImpl _$$BulkReportRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$BulkReportRequestImpl(
      assessmentId: json['assessmentId'] as String,
      studentIds: (json['studentIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      type: $enumDecode(_$ReportTypeEnumMap, json['type']),
      options: json['options'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$BulkReportRequestImplToJson(
        _$BulkReportRequestImpl instance) =>
    <String, dynamic>{
      'assessmentId': instance.assessmentId,
      'studentIds': instance.studentIds,
      'type': _$ReportTypeEnumMap[instance.type]!,
      'options': instance.options,
    };

_$NotificationImpl _$$NotificationImplFromJson(Map<String, dynamic> json) =>
    _$NotificationImpl(
      id: json['id'] as String,
      userId: json['userId'] as String,
      type: $enumDecode(_$NotificationTypeEnumMap, json['type']),
      title: json['title'] as String,
      body: json['body'] as String,
      data: json['data'] as Map<String, dynamic>,
      createdAt: DateTime.parse(json['createdAt'] as String),
      isRead: json['isRead'] as bool,
      readAt: json['readAt'] == null
          ? null
          : DateTime.parse(json['readAt'] as String),
    );

Map<String, dynamic> _$$NotificationImplToJson(_$NotificationImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'userId': instance.userId,
      'type': _$NotificationTypeEnumMap[instance.type]!,
      'title': instance.title,
      'body': instance.body,
      'data': instance.data,
      'createdAt': instance.createdAt.toIso8601String(),
      'isRead': instance.isRead,
      'readAt': instance.readAt?.toIso8601String(),
    };

const _$NotificationTypeEnumMap = {
  NotificationType.assessmentCreated: 'assessmentCreated',
  NotificationType.assessmentAssigned: 'assessmentAssigned',
  NotificationType.assessmentDue: 'assessmentDue',
  NotificationType.assessmentCompleted: 'assessmentCompleted',
  NotificationType.evaluationReady: 'evaluationReady',
  NotificationType.reportReady: 'reportReady',
  NotificationType.practiceAssigned: 'practiceAssigned',
  NotificationType.practiceCompleted: 'practiceCompleted',
  NotificationType.masteryUpdate: 'masteryUpdate',
  NotificationType.interventionNeeded: 'interventionNeeded',
  NotificationType.general: 'general',
};

_$WhatsAppDeepLinkImpl _$$WhatsAppDeepLinkImplFromJson(
        Map<String, dynamic> json) =>
    _$WhatsAppDeepLinkImpl(
      phoneNumber: json['phoneNumber'] as String,
      message: json['message'] as String,
      deepLinkUrl: json['deepLinkUrl'] as String,
      fallbackUrl: json['fallbackUrl'] as String,
    );

Map<String, dynamic> _$$WhatsAppDeepLinkImplToJson(
        _$WhatsAppDeepLinkImpl instance) =>
    <String, dynamic>{
      'phoneNumber': instance.phoneNumber,
      'message': instance.message,
      'deepLinkUrl': instance.deepLinkUrl,
      'fallbackUrl': instance.fallbackUrl,
    };
