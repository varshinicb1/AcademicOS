// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analytics.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$AssessmentAnalyticsImpl _$$AssessmentAnalyticsImplFromJson(
        Map<String, dynamic> json) =>
    _$AssessmentAnalyticsImpl(
      assessmentId: json['assessmentId'] as String,
      assessmentTitle: json['assessmentTitle'] as String,
      totalStudents: (json['totalStudents'] as num).toInt(),
      submittedStudents: (json['submittedStudents'] as num).toInt(),
      evaluatedStudents: (json['evaluatedStudents'] as num).toInt(),
      classPerformance: ClassPerformance.fromJson(
          json['classPerformance'] as Map<String, dynamic>),
      studentPerformances: (json['studentPerformances'] as List<dynamic>)
          .map((e) => StudentPerformance.fromJson(e as Map<String, dynamic>))
          .toList(),
      questionAnalytics: (json['questionAnalytics'] as List<dynamic>)
          .map((e) => QuestionAnalytics.fromJson(e as Map<String, dynamic>))
          .toList(),
      conceptGaps: (json['conceptGaps'] as List<dynamic>)
          .map((e) => ConceptGap.fromJson(e as Map<String, dynamic>))
          .toList(),
      bloomAnalytics: BloomAnalytics.fromJson(
          json['bloomAnalytics'] as Map<String, dynamic>),
      competencyAnalytics: CompetencyAnalytics.fromJson(
          json['competencyAnalytics'] as Map<String, dynamic>),
      difficultyAnalytics: DifficultyAnalytics.fromJson(
          json['difficultyAnalytics'] as Map<String, dynamic>),
      timeAnalytics:
          TimeAnalytics.fromJson(json['timeAnalytics'] as Map<String, dynamic>),
      commonErrors: (json['commonErrors'] as List<dynamic>)
          .map((e) => CommonError.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
    );

Map<String, dynamic> _$$AssessmentAnalyticsImplToJson(
        _$AssessmentAnalyticsImpl instance) =>
    <String, dynamic>{
      'assessmentId': instance.assessmentId,
      'assessmentTitle': instance.assessmentTitle,
      'totalStudents': instance.totalStudents,
      'submittedStudents': instance.submittedStudents,
      'evaluatedStudents': instance.evaluatedStudents,
      'classPerformance': instance.classPerformance,
      'studentPerformances': instance.studentPerformances,
      'questionAnalytics': instance.questionAnalytics,
      'conceptGaps': instance.conceptGaps,
      'bloomAnalytics': instance.bloomAnalytics,
      'competencyAnalytics': instance.competencyAnalytics,
      'difficultyAnalytics': instance.difficultyAnalytics,
      'timeAnalytics': instance.timeAnalytics,
      'commonErrors': instance.commonErrors,
      'generatedAt': instance.generatedAt.toIso8601String(),
    };

_$ClassPerformanceImpl _$$ClassPerformanceImplFromJson(
        Map<String, dynamic> json) =>
    _$ClassPerformanceImpl(
      averageScore: (json['averageScore'] as num).toDouble(),
      medianScore: (json['medianScore'] as num).toDouble(),
      standardDeviation: (json['standardDeviation'] as num).toDouble(),
      passRate: (json['passRate'] as num).toDouble(),
      distinctionRate: (json['distinctionRate'] as num).toDouble(),
      gradeDistribution:
          Map<String, int>.from(json['gradeDistribution'] as Map),
      highestScore: (json['highestScore'] as num).toInt(),
      lowestScore: (json['lowestScore'] as num).toInt(),
      reliabilityCoefficient:
          (json['reliabilityCoefficient'] as num).toDouble(),
      standardError: (json['standardError'] as num).toDouble(),
    );

Map<String, dynamic> _$$ClassPerformanceImplToJson(
        _$ClassPerformanceImpl instance) =>
    <String, dynamic>{
      'averageScore': instance.averageScore,
      'medianScore': instance.medianScore,
      'standardDeviation': instance.standardDeviation,
      'passRate': instance.passRate,
      'distinctionRate': instance.distinctionRate,
      'gradeDistribution': instance.gradeDistribution,
      'highestScore': instance.highestScore,
      'lowestScore': instance.lowestScore,
      'reliabilityCoefficient': instance.reliabilityCoefficient,
      'standardError': instance.standardError,
    };

_$StudentPerformanceImpl _$$StudentPerformanceImplFromJson(
        Map<String, dynamic> json) =>
    _$StudentPerformanceImpl(
      studentId: json['studentId'] as String,
      studentName: json['studentName'] as String,
      rollNumber: json['rollNumber'] as String,
      totalScore: (json['totalScore'] as num).toInt(),
      maxScore: (json['maxScore'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      grade: json['grade'] as String,
      rank: (json['rank'] as num).toInt(),
      percentile: (json['percentile'] as num).toDouble(),
      sectionScores: (json['sectionScores'] as List<dynamic>)
          .map((e) => SectionScore.fromJson(e as Map<String, dynamic>))
          .toList(),
      conceptScores: (json['conceptScores'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      strengths:
          (json['strengths'] as List<dynamic>).map((e) => e as String).toList(),
      weaknesses: (json['weaknesses'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      carelessErrors: (json['carelessErrors'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      recommendation: json['recommendation'] as String,
    );

Map<String, dynamic> _$$StudentPerformanceImplToJson(
        _$StudentPerformanceImpl instance) =>
    <String, dynamic>{
      'studentId': instance.studentId,
      'studentName': instance.studentName,
      'rollNumber': instance.rollNumber,
      'totalScore': instance.totalScore,
      'maxScore': instance.maxScore,
      'percentage': instance.percentage,
      'grade': instance.grade,
      'rank': instance.rank,
      'percentile': instance.percentile,
      'sectionScores': instance.sectionScores,
      'conceptScores': instance.conceptScores,
      'strengths': instance.strengths,
      'weaknesses': instance.weaknesses,
      'carelessErrors': instance.carelessErrors,
      'recommendation': instance.recommendation,
    };

_$SectionScoreImpl _$$SectionScoreImplFromJson(Map<String, dynamic> json) =>
    _$SectionScoreImpl(
      sectionId: json['sectionId'] as String,
      sectionLabel: json['sectionLabel'] as String,
      score: (json['score'] as num).toInt(),
      maxScore: (json['maxScore'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
    );

Map<String, dynamic> _$$SectionScoreImplToJson(_$SectionScoreImpl instance) =>
    <String, dynamic>{
      'sectionId': instance.sectionId,
      'sectionLabel': instance.sectionLabel,
      'score': instance.score,
      'maxScore': instance.maxScore,
      'percentage': instance.percentage,
    };

_$QuestionAnalyticsImpl _$$QuestionAnalyticsImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionAnalyticsImpl(
      questionId: json['questionId'] as String,
      questionNumber: (json['questionNumber'] as num).toInt(),
      sectionLabel: json['sectionLabel'] as String,
      maxMarks: (json['maxMarks'] as num).toInt(),
      averageMarks: (json['averageMarks'] as num).toDouble(),
      difficultyIndex: (json['difficultyIndex'] as num).toDouble(),
      discriminationIndex: (json['discriminationIndex'] as num).toDouble(),
      attemptedCount: (json['attemptedCount'] as num).toInt(),
      correctCount: (json['correctCount'] as num).toInt(),
      partialCount: (json['partialCount'] as num).toInt(),
      blankCount: (json['blankCount'] as num).toInt(),
      avgTimeSeconds: (json['avgTimeSeconds'] as num).toDouble(),
      commonWrongAnswers: (json['commonWrongAnswers'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      optionDistribution:
          Map<String, int>.from(json['optionDistribution'] as Map),
      flags:
          QuestionQualityFlags.fromJson(json['flags'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$QuestionAnalyticsImplToJson(
        _$QuestionAnalyticsImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'questionNumber': instance.questionNumber,
      'sectionLabel': instance.sectionLabel,
      'maxMarks': instance.maxMarks,
      'averageMarks': instance.averageMarks,
      'difficultyIndex': instance.difficultyIndex,
      'discriminationIndex': instance.discriminationIndex,
      'attemptedCount': instance.attemptedCount,
      'correctCount': instance.correctCount,
      'partialCount': instance.partialCount,
      'blankCount': instance.blankCount,
      'avgTimeSeconds': instance.avgTimeSeconds,
      'commonWrongAnswers': instance.commonWrongAnswers,
      'optionDistribution': instance.optionDistribution,
      'flags': instance.flags,
    };

_$QuestionQualityFlagsImpl _$$QuestionQualityFlagsImplFromJson(
        Map<String, dynamic> json) =>
    _$QuestionQualityFlagsImpl(
      tooEasy: json['tooEasy'] as bool? ?? false,
      tooHard: json['tooHard'] as bool? ?? false,
      poorDiscrimination: json['poorDiscrimination'] as bool? ?? false,
      ambiguous: json['ambiguous'] as bool? ?? false,
      guessingPossible: json['guessingPossible'] as bool? ?? false,
      timeConsuming: json['timeConsuming'] as bool? ?? false,
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$QuestionQualityFlagsImplToJson(
        _$QuestionQualityFlagsImpl instance) =>
    <String, dynamic>{
      'tooEasy': instance.tooEasy,
      'tooHard': instance.tooHard,
      'poorDiscrimination': instance.poorDiscrimination,
      'ambiguous': instance.ambiguous,
      'guessingPossible': instance.guessingPossible,
      'timeConsuming': instance.timeConsuming,
      'warnings': instance.warnings,
    };

_$ConceptGapImpl _$$ConceptGapImplFromJson(Map<String, dynamic> json) =>
    _$ConceptGapImpl(
      conceptId: json['conceptId'] as String,
      conceptName: json['conceptName'] as String,
      chapterId: json['chapterId'] as String,
      chapterName: json['chapterName'] as String,
      studentsAffected: (json['studentsAffected'] as num).toInt(),
      avgMastery: (json['avgMastery'] as num).toDouble(),
      relatedQuestionIds: (json['relatedQuestionIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      misconceptionIds: (json['misconceptionIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      severity: $enumDecode(_$GapSeverityEnumMap, json['severity']),
      recommendedAction: json['recommendedAction'] as String,
    );

Map<String, dynamic> _$$ConceptGapImplToJson(_$ConceptGapImpl instance) =>
    <String, dynamic>{
      'conceptId': instance.conceptId,
      'conceptName': instance.conceptName,
      'chapterId': instance.chapterId,
      'chapterName': instance.chapterName,
      'studentsAffected': instance.studentsAffected,
      'avgMastery': instance.avgMastery,
      'relatedQuestionIds': instance.relatedQuestionIds,
      'misconceptionIds': instance.misconceptionIds,
      'severity': _$GapSeverityEnumMap[instance.severity]!,
      'recommendedAction': instance.recommendedAction,
    };

const _$GapSeverityEnumMap = {
  GapSeverity.critical: 'critical',
  GapSeverity.high: 'high',
  GapSeverity.medium: 'medium',
  GapSeverity.low: 'low',
};

_$BloomAnalyticsImpl _$$BloomAnalyticsImplFromJson(Map<String, dynamic> json) =>
    _$BloomAnalyticsImpl(
      byLevel: (json['byLevel'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, BloomLevelStats.fromJson(e as Map<String, dynamic>)),
      ),
      insights:
          (json['insights'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$BloomAnalyticsImplToJson(
        _$BloomAnalyticsImpl instance) =>
    <String, dynamic>{
      'byLevel': instance.byLevel,
      'insights': instance.insights,
    };

_$BloomLevelStatsImpl _$$BloomLevelStatsImplFromJson(
        Map<String, dynamic> json) =>
    _$BloomLevelStatsImpl(
      level: json['level'] as String,
      questionCount: (json['questionCount'] as num).toInt(),
      totalMarks: (json['totalMarks'] as num).toInt(),
      avgScore: (json['avgScore'] as num).toDouble(),
      avgPercentage: (json['avgPercentage'] as num).toDouble(),
      studentsAttempted: (json['studentsAttempted'] as num).toInt(),
      studentsProficient: (json['studentsProficient'] as num).toInt(),
    );

Map<String, dynamic> _$$BloomLevelStatsImplToJson(
        _$BloomLevelStatsImpl instance) =>
    <String, dynamic>{
      'level': instance.level,
      'questionCount': instance.questionCount,
      'totalMarks': instance.totalMarks,
      'avgScore': instance.avgScore,
      'avgPercentage': instance.avgPercentage,
      'studentsAttempted': instance.studentsAttempted,
      'studentsProficient': instance.studentsProficient,
    };

_$CompetencyAnalyticsImpl _$$CompetencyAnalyticsImplFromJson(
        Map<String, dynamic> json) =>
    _$CompetencyAnalyticsImpl(
      byCompetency: (json['byCompetency'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, CompetencyStats.fromJson(e as Map<String, dynamic>)),
      ),
      insights:
          (json['insights'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$CompetencyAnalyticsImplToJson(
        _$CompetencyAnalyticsImpl instance) =>
    <String, dynamic>{
      'byCompetency': instance.byCompetency,
      'insights': instance.insights,
    };

_$CompetencyStatsImpl _$$CompetencyStatsImplFromJson(
        Map<String, dynamic> json) =>
    _$CompetencyStatsImpl(
      competencyId: json['competencyId'] as String,
      competencyName: json['competencyName'] as String,
      questionCount: (json['questionCount'] as num).toInt(),
      totalMarks: (json['totalMarks'] as num).toInt(),
      avgScore: (json['avgScore'] as num).toDouble(),
      avgPercentage: (json['avgPercentage'] as num).toDouble(),
      studentsProficient: (json['studentsProficient'] as num).toInt(),
    );

Map<String, dynamic> _$$CompetencyStatsImplToJson(
        _$CompetencyStatsImpl instance) =>
    <String, dynamic>{
      'competencyId': instance.competencyId,
      'competencyName': instance.competencyName,
      'questionCount': instance.questionCount,
      'totalMarks': instance.totalMarks,
      'avgScore': instance.avgScore,
      'avgPercentage': instance.avgPercentage,
      'studentsProficient': instance.studentsProficient,
    };

_$DifficultyAnalyticsImpl _$$DifficultyAnalyticsImplFromJson(
        Map<String, dynamic> json) =>
    _$DifficultyAnalyticsImpl(
      easy: DifficultyLevelStats.fromJson(json['easy'] as Map<String, dynamic>),
      medium:
          DifficultyLevelStats.fromJson(json['medium'] as Map<String, dynamic>),
      hard: DifficultyLevelStats.fromJson(json['hard'] as Map<String, dynamic>),
      insights:
          (json['insights'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$DifficultyAnalyticsImplToJson(
        _$DifficultyAnalyticsImpl instance) =>
    <String, dynamic>{
      'easy': instance.easy,
      'medium': instance.medium,
      'hard': instance.hard,
      'insights': instance.insights,
    };

_$DifficultyLevelStatsImpl _$$DifficultyLevelStatsImplFromJson(
        Map<String, dynamic> json) =>
    _$DifficultyLevelStatsImpl(
      level: json['level'] as String,
      questionCount: (json['questionCount'] as num).toInt(),
      totalMarks: (json['totalMarks'] as num).toInt(),
      avgScore: (json['avgScore'] as num).toDouble(),
      avgPercentage: (json['avgPercentage'] as num).toDouble(),
      discriminationIndex: (json['discriminationIndex'] as num).toDouble(),
    );

Map<String, dynamic> _$$DifficultyLevelStatsImplToJson(
        _$DifficultyLevelStatsImpl instance) =>
    <String, dynamic>{
      'level': instance.level,
      'questionCount': instance.questionCount,
      'totalMarks': instance.totalMarks,
      'avgScore': instance.avgScore,
      'avgPercentage': instance.avgPercentage,
      'discriminationIndex': instance.discriminationIndex,
    };

_$TimeAnalyticsImpl _$$TimeAnalyticsImplFromJson(Map<String, dynamic> json) =>
    _$TimeAnalyticsImpl(
      avgTimePerQuestion: (json['avgTimePerQuestion'] as num).toDouble(),
      avgTotalTime: (json['avgTotalTime'] as num).toDouble(),
      timeBySection: (json['timeBySection'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      timeByQuestion: (json['timeByQuestion'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      studentsFinishedEarly: (json['studentsFinishedEarly'] as num).toInt(),
      studentsRanOutOfTime: (json['studentsRanOutOfTime'] as num).toInt(),
      insights:
          (json['insights'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$TimeAnalyticsImplToJson(_$TimeAnalyticsImpl instance) =>
    <String, dynamic>{
      'avgTimePerQuestion': instance.avgTimePerQuestion,
      'avgTotalTime': instance.avgTotalTime,
      'timeBySection': instance.timeBySection,
      'timeByQuestion': instance.timeByQuestion,
      'studentsFinishedEarly': instance.studentsFinishedEarly,
      'studentsRanOutOfTime': instance.studentsRanOutOfTime,
      'insights': instance.insights,
    };

_$CommonErrorImpl _$$CommonErrorImplFromJson(Map<String, dynamic> json) =>
    _$CommonErrorImpl(
      id: json['id'] as String,
      questionId: json['questionId'] as String,
      questionNumber: (json['questionNumber'] as num).toInt(),
      errorType: json['errorType'] as String,
      description: json['description'] as String,
      frequency: (json['frequency'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      exampleAnswers: (json['exampleAnswers'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      remediationHint: json['remediationHint'] as String,
    );

Map<String, dynamic> _$$CommonErrorImplToJson(_$CommonErrorImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'questionId': instance.questionId,
      'questionNumber': instance.questionNumber,
      'errorType': instance.errorType,
      'description': instance.description,
      'frequency': instance.frequency,
      'percentage': instance.percentage,
      'exampleAnswers': instance.exampleAnswers,
      'remediationHint': instance.remediationHint,
    };

_$ClassAnalyticsImpl _$$ClassAnalyticsImplFromJson(Map<String, dynamic> json) =>
    _$ClassAnalyticsImpl(
      classId: json['classId'] as String,
      className: json['className'] as String,
      totalStudents: (json['totalStudents'] as num).toInt(),
      assessments: (json['assessments'] as List<dynamic>)
          .map((e) => AssessmentAnalytics.fromJson(e as Map<String, dynamic>))
          .toList(),
      subjectMastery: (json['subjectMastery'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, SubjectMastery.fromJson(e as Map<String, dynamic>)),
      ),
      classWideGaps: (json['classWideGaps'] as List<dynamic>)
          .map((e) => ConceptGap.fromJson(e as Map<String, dynamic>))
          .toList(),
      topPerformers: (json['topPerformers'] as List<dynamic>)
          .map((e) => StudentPerformance.fromJson(e as Map<String, dynamic>))
          .toList(),
      atRiskStudents: (json['atRiskStudents'] as List<dynamic>)
          .map((e) => StudentPerformance.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
    );

Map<String, dynamic> _$$ClassAnalyticsImplToJson(
        _$ClassAnalyticsImpl instance) =>
    <String, dynamic>{
      'classId': instance.classId,
      'className': instance.className,
      'totalStudents': instance.totalStudents,
      'assessments': instance.assessments,
      'subjectMastery': instance.subjectMastery,
      'classWideGaps': instance.classWideGaps,
      'topPerformers': instance.topPerformers,
      'atRiskStudents': instance.atRiskStudents,
      'generatedAt': instance.generatedAt.toIso8601String(),
    };

_$StudentAnalyticsImpl _$$StudentAnalyticsImplFromJson(
        Map<String, dynamic> json) =>
    _$StudentAnalyticsImpl(
      studentId: json['studentId'] as String,
      studentName: json['studentName'] as String,
      grade: json['grade'] as String,
      subjectMastery: (json['subjectMastery'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, SubjectMastery.fromJson(e as Map<String, dynamic>)),
      ),
      assessmentHistory: (json['assessmentHistory'] as List<dynamic>)
          .map((e) => AssessmentAnalytics.fromJson(e as Map<String, dynamic>))
          .toList(),
      activeMisconceptions: (json['activeMisconceptions'] as List<dynamic>)
          .map((e) => MisconceptionFlag.fromJson(e as Map<String, dynamic>))
          .toList(),
      conceptGaps: (json['conceptGaps'] as List<dynamic>)
          .map((e) => ConceptGap.fromJson(e as Map<String, dynamic>))
          .toList(),
      recommendations: (json['recommendations'] as List<dynamic>)
          .map((e) =>
              ActionableRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
    );

Map<String, dynamic> _$$StudentAnalyticsImplToJson(
        _$StudentAnalyticsImpl instance) =>
    <String, dynamic>{
      'studentId': instance.studentId,
      'studentName': instance.studentName,
      'grade': instance.grade,
      'subjectMastery': instance.subjectMastery,
      'assessmentHistory': instance.assessmentHistory,
      'activeMisconceptions': instance.activeMisconceptions,
      'conceptGaps': instance.conceptGaps,
      'recommendations': instance.recommendations,
      'generatedAt': instance.generatedAt.toIso8601String(),
    };

_$SchoolAnalyticsImpl _$$SchoolAnalyticsImplFromJson(
        Map<String, dynamic> json) =>
    _$SchoolAnalyticsImpl(
      schoolId: json['schoolId'] as String,
      schoolName: json['schoolName'] as String,
      totalClasses: (json['totalClasses'] as num).toInt(),
      totalStudents: (json['totalStudents'] as num).toInt(),
      totalTeachers: (json['totalTeachers'] as num).toInt(),
      subjectPerformance:
          (json['subjectPerformance'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      gradeDistribution:
          Map<String, int>.from(json['gradeDistribution'] as Map),
      topClasses: (json['topClasses'] as List<dynamic>)
          .map((e) => ClassAnalytics.fromJson(e as Map<String, dynamic>))
          .toList(),
      atRiskClasses: (json['atRiskClasses'] as List<dynamic>)
          .map((e) => ClassAnalytics.fromJson(e as Map<String, dynamic>))
          .toList(),
      schoolWideGaps: (json['schoolWideGaps'] as List<dynamic>)
          .map((e) => ConceptGap.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
    );

Map<String, dynamic> _$$SchoolAnalyticsImplToJson(
        _$SchoolAnalyticsImpl instance) =>
    <String, dynamic>{
      'schoolId': instance.schoolId,
      'schoolName': instance.schoolName,
      'totalClasses': instance.totalClasses,
      'totalStudents': instance.totalStudents,
      'totalTeachers': instance.totalTeachers,
      'subjectPerformance': instance.subjectPerformance,
      'gradeDistribution': instance.gradeDistribution,
      'topClasses': instance.topClasses,
      'atRiskClasses': instance.atRiskClasses,
      'schoolWideGaps': instance.schoolWideGaps,
      'generatedAt': instance.generatedAt.toIso8601String(),
    };
