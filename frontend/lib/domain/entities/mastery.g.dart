// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mastery.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$StudentMasteryImpl _$$StudentMasteryImplFromJson(Map<String, dynamic> json) =>
    _$StudentMasteryImpl(
      studentId: json['studentId'] as String,
      schoolId: json['schoolId'] as String,
      grade: json['grade'] as String,
      concepts: (json['concepts'] as List<dynamic>)
          .map((e) => ConceptMastery.fromJson(e as Map<String, dynamic>))
          .toList(),
      chapters: (json['chapters'] as List<dynamic>)
          .map((e) => ChapterMastery.fromJson(e as Map<String, dynamic>))
          .toList(),
      subjects: (json['subjects'] as List<dynamic>)
          .map((e) => SubjectMastery.fromJson(e as Map<String, dynamic>))
          .toList(),
      summary: MasterySummary.fromJson(json['summary'] as Map<String, dynamic>),
      lastUpdated: DateTime.parse(json['lastUpdated'] as String),
      version: (json['version'] as num).toInt(),
    );

Map<String, dynamic> _$$StudentMasteryImplToJson(
        _$StudentMasteryImpl instance) =>
    <String, dynamic>{
      'studentId': instance.studentId,
      'schoolId': instance.schoolId,
      'grade': instance.grade,
      'concepts': instance.concepts,
      'chapters': instance.chapters,
      'subjects': instance.subjects,
      'summary': instance.summary,
      'lastUpdated': instance.lastUpdated.toIso8601String(),
      'version': instance.version,
    };

_$ConceptMasteryImpl _$$ConceptMasteryImplFromJson(Map<String, dynamic> json) =>
    _$ConceptMasteryImpl(
      conceptId: json['conceptId'] as String,
      conceptName: json['conceptName'] as String,
      chapterId: json['chapterId'] as String,
      subject: json['subject'] as String,
      masteryScore: (json['masteryScore'] as num).toDouble(),
      confidenceScore: (json['confidenceScore'] as num).toDouble(),
      retentionScore: (json['retentionScore'] as num).toDouble(),
      totalAttempts: (json['totalAttempts'] as num).toInt(),
      correctAttempts: (json['correctAttempts'] as num).toInt(),
      consecutiveCorrect: (json['consecutiveCorrect'] as num).toInt(),
      consecutiveIncorrect: (json['consecutiveIncorrect'] as num).toInt(),
      lastAttemptedAt: DateTime.parse(json['lastAttemptedAt'] as String),
      masteredAt: json['masteredAt'] == null
          ? null
          : DateTime.parse(json['masteredAt'] as String),
      status: $enumDecode(_$MasteryStatusEnumMap, json['status']),
      misconceptions: (json['misconceptions'] as List<dynamic>)
          .map((e) => MisconceptionFlag.fromJson(e as Map<String, dynamic>))
          .toList(),
      prerequisiteConceptIds: (json['prerequisiteConceptIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      difficulty: (json['difficulty'] as num).toDouble(),
      timeSpentMinutes: (json['timeSpentMinutes'] as num).toDouble(),
    );

Map<String, dynamic> _$$ConceptMasteryImplToJson(
        _$ConceptMasteryImpl instance) =>
    <String, dynamic>{
      'conceptId': instance.conceptId,
      'conceptName': instance.conceptName,
      'chapterId': instance.chapterId,
      'subject': instance.subject,
      'masteryScore': instance.masteryScore,
      'confidenceScore': instance.confidenceScore,
      'retentionScore': instance.retentionScore,
      'totalAttempts': instance.totalAttempts,
      'correctAttempts': instance.correctAttempts,
      'consecutiveCorrect': instance.consecutiveCorrect,
      'consecutiveIncorrect': instance.consecutiveIncorrect,
      'lastAttemptedAt': instance.lastAttemptedAt.toIso8601String(),
      'masteredAt': instance.masteredAt?.toIso8601String(),
      'status': _$MasteryStatusEnumMap[instance.status]!,
      'misconceptions': instance.misconceptions,
      'prerequisiteConceptIds': instance.prerequisiteConceptIds,
      'difficulty': instance.difficulty,
      'timeSpentMinutes': instance.timeSpentMinutes,
    };

const _$MasteryStatusEnumMap = {
  MasteryStatus.notAttempted: 'notAttempted',
  MasteryStatus.learning: 'learning',
  MasteryStatus.developing: 'developing',
  MasteryStatus.proficient: 'proficient',
  MasteryStatus.mastered: 'mastered',
  MasteryStatus.decaying: 'decaying',
  MasteryStatus.needsReview: 'needsReview',
};

_$ChapterMasteryImpl _$$ChapterMasteryImplFromJson(Map<String, dynamic> json) =>
    _$ChapterMasteryImpl(
      chapterId: json['chapterId'] as String,
      chapterName: json['chapterName'] as String,
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      overallMastery: (json['overallMastery'] as num).toDouble(),
      overallConfidence: (json['overallConfidence'] as num).toDouble(),
      overallRetention: (json['overallRetention'] as num).toDouble(),
      masteredConceptIds: (json['masteredConceptIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      weakConceptIds: (json['weakConceptIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      notAttemptedConceptIds: (json['notAttemptedConceptIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      questionsAttempted: (json['questionsAttempted'] as num).toInt(),
      questionsCorrect: (json['questionsCorrect'] as num).toInt(),
      lastActivityAt: DateTime.parse(json['lastActivityAt'] as String),
      status: $enumDecode(_$ChapterStatusEnumMap, json['status']),
    );

Map<String, dynamic> _$$ChapterMasteryImplToJson(
        _$ChapterMasteryImpl instance) =>
    <String, dynamic>{
      'chapterId': instance.chapterId,
      'chapterName': instance.chapterName,
      'subject': instance.subject,
      'grade': instance.grade,
      'overallMastery': instance.overallMastery,
      'overallConfidence': instance.overallConfidence,
      'overallRetention': instance.overallRetention,
      'masteredConceptIds': instance.masteredConceptIds,
      'weakConceptIds': instance.weakConceptIds,
      'notAttemptedConceptIds': instance.notAttemptedConceptIds,
      'questionsAttempted': instance.questionsAttempted,
      'questionsCorrect': instance.questionsCorrect,
      'lastActivityAt': instance.lastActivityAt.toIso8601String(),
      'status': _$ChapterStatusEnumMap[instance.status]!,
    };

const _$ChapterStatusEnumMap = {
  ChapterStatus.notStarted: 'notStarted',
  ChapterStatus.inProgress: 'inProgress',
  ChapterStatus.needsReview: 'needsReview',
  ChapterStatus.completed: 'completed',
  ChapterStatus.mastered: 'mastered',
};

_$SubjectMasteryImpl _$$SubjectMasteryImplFromJson(Map<String, dynamic> json) =>
    _$SubjectMasteryImpl(
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      overallMastery: (json['overallMastery'] as num).toDouble(),
      overallConfidence: (json['overallConfidence'] as num).toDouble(),
      overallRetention: (json['overallRetention'] as num).toDouble(),
      chapters: (json['chapters'] as List<dynamic>)
          .map((e) => ChapterMastery.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalQuestionsAttempted: (json['totalQuestionsAttempted'] as num).toInt(),
      totalQuestionsCorrect: (json['totalQuestionsCorrect'] as num).toInt(),
      avgTimePerQuestion: (json['avgTimePerQuestion'] as num).toDouble(),
      status: $enumDecode(_$SubjectStatusEnumMap, json['status']),
    );

Map<String, dynamic> _$$SubjectMasteryImplToJson(
        _$SubjectMasteryImpl instance) =>
    <String, dynamic>{
      'subject': instance.subject,
      'grade': instance.grade,
      'overallMastery': instance.overallMastery,
      'overallConfidence': instance.overallConfidence,
      'overallRetention': instance.overallRetention,
      'chapters': instance.chapters,
      'totalQuestionsAttempted': instance.totalQuestionsAttempted,
      'totalQuestionsCorrect': instance.totalQuestionsCorrect,
      'avgTimePerQuestion': instance.avgTimePerQuestion,
      'status': _$SubjectStatusEnumMap[instance.status]!,
    };

const _$SubjectStatusEnumMap = {
  SubjectStatus.onTrack: 'onTrack',
  SubjectStatus.needsAttention: 'needsAttention',
  SubjectStatus.critical: 'critical',
};

_$MasterySummaryImpl _$$MasterySummaryImplFromJson(Map<String, dynamic> json) =>
    _$MasterySummaryImpl(
      overallMastery: (json['overallMastery'] as num).toDouble(),
      overallConfidence: (json['overallConfidence'] as num).toDouble(),
      overallRetention: (json['overallRetention'] as num).toDouble(),
      totalConcepts: (json['totalConcepts'] as num).toInt(),
      masteredConcepts: (json['masteredConcepts'] as num).toInt(),
      weakConcepts: (json['weakConcepts'] as num).toInt(),
      notAttemptedConcepts: (json['notAttemptedConcepts'] as num).toInt(),
      totalQuestionsAttempted: (json['totalQuestionsAttempted'] as num).toInt(),
      totalQuestionsCorrect: (json['totalQuestionsCorrect'] as num).toInt(),
      accuracyRate: (json['accuracyRate'] as num).toDouble(),
      bloomDistribution:
          Map<String, int>.from(json['bloomDistribution'] as Map),
      difficultyDistribution:
          Map<String, int>.from(json['difficultyDistribution'] as Map),
      topStrengths: (json['topStrengths'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      topWeaknesses: (json['topWeaknesses'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      recommendations: (json['recommendations'] as List<dynamic>)
          .map((e) =>
              ActionableRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$MasterySummaryImplToJson(
        _$MasterySummaryImpl instance) =>
    <String, dynamic>{
      'overallMastery': instance.overallMastery,
      'overallConfidence': instance.overallConfidence,
      'overallRetention': instance.overallRetention,
      'totalConcepts': instance.totalConcepts,
      'masteredConcepts': instance.masteredConcepts,
      'weakConcepts': instance.weakConcepts,
      'notAttemptedConcepts': instance.notAttemptedConcepts,
      'totalQuestionsAttempted': instance.totalQuestionsAttempted,
      'totalQuestionsCorrect': instance.totalQuestionsCorrect,
      'accuracyRate': instance.accuracyRate,
      'bloomDistribution': instance.bloomDistribution,
      'difficultyDistribution': instance.difficultyDistribution,
      'topStrengths': instance.topStrengths,
      'topWeaknesses': instance.topWeaknesses,
      'recommendations': instance.recommendations,
    };

_$MisconceptionFlagImpl _$$MisconceptionFlagImplFromJson(
        Map<String, dynamic> json) =>
    _$MisconceptionFlagImpl(
      misconceptionId: json['misconceptionId'] as String,
      misconceptionName: json['misconceptionName'] as String,
      description: json['description'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      occurrenceCount: (json['occurrenceCount'] as num).toInt(),
      firstDetectedAt: DateTime.parse(json['firstDetectedAt'] as String),
      lastDetectedAt: DateTime.parse(json['lastDetectedAt'] as String),
      severity: $enumDecode(_$MisconceptionSeverityEnumMap, json['severity']),
      evidenceQuestionIds: (json['evidenceQuestionIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$MisconceptionFlagImplToJson(
        _$MisconceptionFlagImpl instance) =>
    <String, dynamic>{
      'misconceptionId': instance.misconceptionId,
      'misconceptionName': instance.misconceptionName,
      'description': instance.description,
      'confidence': instance.confidence,
      'occurrenceCount': instance.occurrenceCount,
      'firstDetectedAt': instance.firstDetectedAt.toIso8601String(),
      'lastDetectedAt': instance.lastDetectedAt.toIso8601String(),
      'severity': _$MisconceptionSeverityEnumMap[instance.severity]!,
      'evidenceQuestionIds': instance.evidenceQuestionIds,
    };

const _$MisconceptionSeverityEnumMap = {
  MisconceptionSeverity.low: 'low',
  MisconceptionSeverity.medium: 'medium',
  MisconceptionSeverity.high: 'high',
  MisconceptionSeverity.critical: 'critical',
};

_$ActionableRecommendationImpl _$$ActionableRecommendationImplFromJson(
        Map<String, dynamic> json) =>
    _$ActionableRecommendationImpl(
      id: json['id'] as String,
      type: $enumDecode(_$RecommendationTypeEnumMap, json['type']),
      title: json['title'] as String,
      description: json['description'] as String,
      targetConceptId: json['targetConceptId'] as String,
      targetConceptName: json['targetConceptName'] as String,
      estimatedMinutes: (json['estimatedMinutes'] as num).toInt(),
      successProbability: (json['successProbability'] as num).toDouble(),
      priority: $enumDecode(_$PriorityEnumMap, json['priority']),
      resourceIds: (json['resourceIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$ActionableRecommendationImplToJson(
        _$ActionableRecommendationImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'type': _$RecommendationTypeEnumMap[instance.type]!,
      'title': instance.title,
      'description': instance.description,
      'targetConceptId': instance.targetConceptId,
      'targetConceptName': instance.targetConceptName,
      'estimatedMinutes': instance.estimatedMinutes,
      'successProbability': instance.successProbability,
      'priority': _$PriorityEnumMap[instance.priority]!,
      'resourceIds': instance.resourceIds,
    };

const _$RecommendationTypeEnumMap = {
  RecommendationType.practiceWorksheet: 'practiceWorksheet',
  RecommendationType.conceptReview: 'conceptReview',
  RecommendationType.videoLesson: 'videoLesson',
  RecommendationType.peerTutoring: 'peerTutoring',
  RecommendationType.teacherIntervention: 'teacherIntervention',
  RecommendationType.remedialClass: 'remedialClass',
  RecommendationType.formativeAssessment: 'formativeAssessment',
};

const _$PriorityEnumMap = {
  Priority.low: 'low',
  Priority.medium: 'medium',
  Priority.high: 'high',
  Priority.urgent: 'urgent',
};
