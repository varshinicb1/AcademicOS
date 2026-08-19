// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'report.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$StudentReportImpl _$$StudentReportImplFromJson(Map<String, dynamic> json) =>
    _$StudentReportImpl(
      id: json['id'] as String,
      assessmentId: json['assessmentId'] as String,
      assessmentTitle: json['assessmentTitle'] as String,
      studentId: json['studentId'] as String,
      studentName: json['studentName'] as String,
      rollNumber: json['rollNumber'] as String,
      grade: (json['grade'] as num).toInt(),
      section: json['section'] as String,
      header: ReportHeader.fromJson(json['header'] as Map<String, dynamic>),
      overview: PerformanceOverview.fromJson(
          json['overview'] as Map<String, dynamic>),
      sectionReports: (json['sectionReports'] as List<dynamic>)
          .map((e) => SectionReport.fromJson(e as Map<String, dynamic>))
          .toList(),
      conceptReports: (json['conceptReports'] as List<dynamic>)
          .map((e) => ConceptReport.fromJson(e as Map<String, dynamic>))
          .toList(),
      bloomReport:
          BloomReport.fromJson(json['bloomReport'] as Map<String, dynamic>),
      competencyReport: CompetencyReport.fromJson(
          json['competencyReport'] as Map<String, dynamic>),
      strengths:
          (json['strengths'] as List<dynamic>).map((e) => e as String).toList(),
      weaknesses: (json['weaknesses'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      carelessErrors: (json['carelessErrors'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      recommendations: (json['recommendations'] as List<dynamic>)
          .map((e) =>
              ActionableRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
      teacherRemarks: TeacherRemarks.fromJson(
          json['teacherRemarks'] as Map<String, dynamic>),
      parentSummary:
          ParentSummary.fromJson(json['parentSummary'] as Map<String, dynamic>),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
      generatedBy: json['generatedBy'] as String,
    );

Map<String, dynamic> _$$StudentReportImplToJson(_$StudentReportImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'assessmentId': instance.assessmentId,
      'assessmentTitle': instance.assessmentTitle,
      'studentId': instance.studentId,
      'studentName': instance.studentName,
      'rollNumber': instance.rollNumber,
      'grade': instance.grade,
      'section': instance.section,
      'header': instance.header,
      'overview': instance.overview,
      'sectionReports': instance.sectionReports,
      'conceptReports': instance.conceptReports,
      'bloomReport': instance.bloomReport,
      'competencyReport': instance.competencyReport,
      'strengths': instance.strengths,
      'weaknesses': instance.weaknesses,
      'carelessErrors': instance.carelessErrors,
      'recommendations': instance.recommendations,
      'teacherRemarks': instance.teacherRemarks,
      'parentSummary': instance.parentSummary,
      'generatedAt': instance.generatedAt.toIso8601String(),
      'generatedBy': instance.generatedBy,
    };

_$ReportHeaderImpl _$$ReportHeaderImplFromJson(Map<String, dynamic> json) =>
    _$ReportHeaderImpl(
      schoolName: json['schoolName'] as String,
      schoolLogoUrl: json['schoolLogoUrl'] as String,
      academicYear: json['academicYear'] as String,
      term: json['term'] as String,
      assessmentDate: DateTime.parse(json['assessmentDate'] as String),
      reportDate: DateTime.parse(json['reportDate'] as String),
      principalName: json['principalName'] as String,
      teacherName: json['teacherName'] as String,
      className: json['className'] as String,
      section: json['section'] as String,
    );

Map<String, dynamic> _$$ReportHeaderImplToJson(_$ReportHeaderImpl instance) =>
    <String, dynamic>{
      'schoolName': instance.schoolName,
      'schoolLogoUrl': instance.schoolLogoUrl,
      'academicYear': instance.academicYear,
      'term': instance.term,
      'assessmentDate': instance.assessmentDate.toIso8601String(),
      'reportDate': instance.reportDate.toIso8601String(),
      'principalName': instance.principalName,
      'teacherName': instance.teacherName,
      'className': instance.className,
      'section': instance.section,
    };

_$PerformanceOverviewImpl _$$PerformanceOverviewImplFromJson(
        Map<String, dynamic> json) =>
    _$PerformanceOverviewImpl(
      totalScore: (json['totalScore'] as num).toInt(),
      maxScore: (json['maxScore'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      grade: json['grade'] as String,
      classRank: (json['classRank'] as num).toInt(),
      totalStudents: (json['totalStudents'] as num).toInt(),
      percentile: (json['percentile'] as num).toDouble(),
      performanceLevel: json['performanceLevel'] as String,
      sectionScores: (json['sectionScores'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, SectionScore.fromJson(e as Map<String, dynamic>)),
      ),
      classAverage: (json['classAverage'] as num).toDouble(),
      classMedian: (json['classMedian'] as num).toDouble(),
    );

Map<String, dynamic> _$$PerformanceOverviewImplToJson(
        _$PerformanceOverviewImpl instance) =>
    <String, dynamic>{
      'totalScore': instance.totalScore,
      'maxScore': instance.maxScore,
      'percentage': instance.percentage,
      'grade': instance.grade,
      'classRank': instance.classRank,
      'totalStudents': instance.totalStudents,
      'percentile': instance.percentile,
      'performanceLevel': instance.performanceLevel,
      'sectionScores': instance.sectionScores,
      'classAverage': instance.classAverage,
      'classMedian': instance.classMedian,
    };

_$SectionReportImpl _$$SectionReportImplFromJson(Map<String, dynamic> json) =>
    _$SectionReportImpl(
      sectionId: json['sectionId'] as String,
      sectionLabel: json['sectionLabel'] as String,
      sectionName: json['sectionName'] as String,
      score: (json['score'] as num).toInt(),
      maxScore: (json['maxScore'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      questionsAttempted: (json['questionsAttempted'] as num).toInt(),
      questionsCorrect: (json['questionsCorrect'] as num).toInt(),
      questionsPartial: (json['questionsPartial'] as num).toInt(),
      questions: (json['questions'] as List<dynamic>)
          .map((e) => QuestionReport.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$SectionReportImplToJson(_$SectionReportImpl instance) =>
    <String, dynamic>{
      'sectionId': instance.sectionId,
      'sectionLabel': instance.sectionLabel,
      'sectionName': instance.sectionName,
      'score': instance.score,
      'maxScore': instance.maxScore,
      'percentage': instance.percentage,
      'questionsAttempted': instance.questionsAttempted,
      'questionsCorrect': instance.questionsCorrect,
      'questionsPartial': instance.questionsPartial,
      'questions': instance.questions,
    };

_$QuestionReportImpl _$$QuestionReportImplFromJson(Map<String, dynamic> json) =>
    _$QuestionReportImpl(
      questionId: json['questionId'] as String,
      questionNumber: (json['questionNumber'] as num).toInt(),
      questionText: json['questionText'] as String,
      maxMarks: (json['maxMarks'] as num).toInt(),
      awardedMarks: (json['awardedMarks'] as num).toInt(),
      studentAnswer: json['studentAnswer'] as String,
      modelAnswer: json['modelAnswer'] as String,
      verdict: json['verdict'] as String,
      feedback: json['feedback'] as String,
      conceptTag: json['conceptTag'] as String,
      bloomLevel: json['bloomLevel'] as String,
      difficulty: json['difficulty'] as String,
    );

Map<String, dynamic> _$$QuestionReportImplToJson(
        _$QuestionReportImpl instance) =>
    <String, dynamic>{
      'questionId': instance.questionId,
      'questionNumber': instance.questionNumber,
      'questionText': instance.questionText,
      'maxMarks': instance.maxMarks,
      'awardedMarks': instance.awardedMarks,
      'studentAnswer': instance.studentAnswer,
      'modelAnswer': instance.modelAnswer,
      'verdict': instance.verdict,
      'feedback': instance.feedback,
      'conceptTag': instance.conceptTag,
      'bloomLevel': instance.bloomLevel,
      'difficulty': instance.difficulty,
    };

_$ConceptReportImpl _$$ConceptReportImplFromJson(Map<String, dynamic> json) =>
    _$ConceptReportImpl(
      conceptId: json['conceptId'] as String,
      conceptName: json['conceptName'] as String,
      chapterName: json['chapterName'] as String,
      masteryScore: (json['masteryScore'] as num).toDouble(),
      status: $enumDecode(_$MasteryStatusEnumMap, json['status']),
      questionsAttempted: (json['questionsAttempted'] as num).toInt(),
      questionsCorrect: (json['questionsCorrect'] as num).toInt(),
      statusLabel: json['statusLabel'] as String,
      recommendation: json['recommendation'] as String,
    );

Map<String, dynamic> _$$ConceptReportImplToJson(_$ConceptReportImpl instance) =>
    <String, dynamic>{
      'conceptId': instance.conceptId,
      'conceptName': instance.conceptName,
      'chapterName': instance.chapterName,
      'masteryScore': instance.masteryScore,
      'status': _$MasteryStatusEnumMap[instance.status]!,
      'questionsAttempted': instance.questionsAttempted,
      'questionsCorrect': instance.questionsCorrect,
      'statusLabel': instance.statusLabel,
      'recommendation': instance.recommendation,
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

_$BloomReportImpl _$$BloomReportImplFromJson(Map<String, dynamic> json) =>
    _$BloomReportImpl(
      byLevel: (json['byLevel'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, BloomLevelReport.fromJson(e as Map<String, dynamic>)),
      ),
      strongestLevel: json['strongestLevel'] as String,
      weakestLevel: json['weakestLevel'] as String,
      insights:
          (json['insights'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$BloomReportImplToJson(_$BloomReportImpl instance) =>
    <String, dynamic>{
      'byLevel': instance.byLevel,
      'strongestLevel': instance.strongestLevel,
      'weakestLevel': instance.weakestLevel,
      'insights': instance.insights,
    };

_$BloomLevelReportImpl _$$BloomLevelReportImplFromJson(
        Map<String, dynamic> json) =>
    _$BloomLevelReportImpl(
      level: json['level'] as String,
      questionsAttempted: (json['questionsAttempted'] as num).toInt(),
      maxMarks: (json['maxMarks'] as num).toInt(),
      scoredMarks: (json['scoredMarks'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      status: json['status'] as String,
    );

Map<String, dynamic> _$$BloomLevelReportImplToJson(
        _$BloomLevelReportImpl instance) =>
    <String, dynamic>{
      'level': instance.level,
      'questionsAttempted': instance.questionsAttempted,
      'maxMarks': instance.maxMarks,
      'scoredMarks': instance.scoredMarks,
      'percentage': instance.percentage,
      'status': instance.status,
    };

_$CompetencyReportImpl _$$CompetencyReportImplFromJson(
        Map<String, dynamic> json) =>
    _$CompetencyReportImpl(
      byCompetency: (json['byCompetency'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(
            k, CompetencyReportItem.fromJson(e as Map<String, dynamic>)),
      ),
      insights:
          (json['insights'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$CompetencyReportImplToJson(
        _$CompetencyReportImpl instance) =>
    <String, dynamic>{
      'byCompetency': instance.byCompetency,
      'insights': instance.insights,
    };

_$CompetencyReportItemImpl _$$CompetencyReportItemImplFromJson(
        Map<String, dynamic> json) =>
    _$CompetencyReportItemImpl(
      competencyId: json['competencyId'] as String,
      competencyName: json['competencyName'] as String,
      questionsAttempted: (json['questionsAttempted'] as num).toInt(),
      maxMarks: (json['maxMarks'] as num).toInt(),
      scoredMarks: (json['scoredMarks'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      status: json['status'] as String,
    );

Map<String, dynamic> _$$CompetencyReportItemImplToJson(
        _$CompetencyReportItemImpl instance) =>
    <String, dynamic>{
      'competencyId': instance.competencyId,
      'competencyName': instance.competencyName,
      'questionsAttempted': instance.questionsAttempted,
      'maxMarks': instance.maxMarks,
      'scoredMarks': instance.scoredMarks,
      'percentage': instance.percentage,
      'status': instance.status,
    };

_$TeacherRemarksImpl _$$TeacherRemarksImplFromJson(Map<String, dynamic> json) =>
    _$TeacherRemarksImpl(
      overallComment: json['overallComment'] as String,
      specificComments: (json['specificComments'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      encouragement: json['encouragement'] as String,
      nextSteps: json['nextSteps'] as String,
      writtenAt: DateTime.parse(json['writtenAt'] as String),
      writtenBy: json['writtenBy'] as String,
    );

Map<String, dynamic> _$$TeacherRemarksImplToJson(
        _$TeacherRemarksImpl instance) =>
    <String, dynamic>{
      'overallComment': instance.overallComment,
      'specificComments': instance.specificComments,
      'encouragement': instance.encouragement,
      'nextSteps': instance.nextSteps,
      'writtenAt': instance.writtenAt.toIso8601String(),
      'writtenBy': instance.writtenBy,
    };

_$ParentSummaryImpl _$$ParentSummaryImplFromJson(Map<String, dynamic> json) =>
    _$ParentSummaryImpl(
      simpleSummary: json['simpleSummary'] as String,
      keyStrengths: (json['keyStrengths'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      keyAreasForImprovement: (json['keyAreasForImprovement'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      homeSupportSuggestion: json['homeSupportSuggestion'] as String,
      teacherMessage: json['teacherMessage'] as String,
    );

Map<String, dynamic> _$$ParentSummaryImplToJson(_$ParentSummaryImpl instance) =>
    <String, dynamic>{
      'simpleSummary': instance.simpleSummary,
      'keyStrengths': instance.keyStrengths,
      'keyAreasForImprovement': instance.keyAreasForImprovement,
      'homeSupportSuggestion': instance.homeSupportSuggestion,
      'teacherMessage': instance.teacherMessage,
    };

_$ParentReportImpl _$$ParentReportImplFromJson(Map<String, dynamic> json) =>
    _$ParentReportImpl(
      id: json['id'] as String,
      studentId: json['studentId'] as String,
      studentName: json['studentName'] as String,
      assessmentId: json['assessmentId'] as String,
      assessmentTitle: json['assessmentTitle'] as String,
      className: json['className'] as String,
      header: ReportHeader.fromJson(json['header'] as Map<String, dynamic>),
      summary: ParentPerformanceSummary.fromJson(
          json['summary'] as Map<String, dynamic>),
      keyStrengths: (json['keyStrengths'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      areasForImprovement: (json['areasForImprovement'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      atHomeSuggestions: (json['atHomeSuggestions'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      teacherMessage: json['teacherMessage'] as String,
      nextSteps: (json['nextSteps'] as List<dynamic>)
          .map((e) =>
              ActionableRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
      generatedBy: json['generatedBy'] as String,
    );

Map<String, dynamic> _$$ParentReportImplToJson(_$ParentReportImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'studentId': instance.studentId,
      'studentName': instance.studentName,
      'assessmentId': instance.assessmentId,
      'assessmentTitle': instance.assessmentTitle,
      'className': instance.className,
      'header': instance.header,
      'summary': instance.summary,
      'keyStrengths': instance.keyStrengths,
      'areasForImprovement': instance.areasForImprovement,
      'atHomeSuggestions': instance.atHomeSuggestions,
      'teacherMessage': instance.teacherMessage,
      'nextSteps': instance.nextSteps,
      'generatedAt': instance.generatedAt.toIso8601String(),
      'generatedBy': instance.generatedBy,
    };

_$ParentPerformanceSummaryImpl _$$ParentPerformanceSummaryImplFromJson(
        Map<String, dynamic> json) =>
    _$ParentPerformanceSummaryImpl(
      totalScore: (json['totalScore'] as num).toInt(),
      maxScore: (json['maxScore'] as num).toInt(),
      percentage: (json['percentage'] as num).toDouble(),
      grade: json['grade'] as String,
      classRank: (json['classRank'] as num).toInt(),
      totalStudents: (json['totalStudents'] as num).toInt(),
      simpleSummary: json['simpleSummary'] as String,
      performanceLevel: json['performanceLevel'] as String,
    );

Map<String, dynamic> _$$ParentPerformanceSummaryImplToJson(
        _$ParentPerformanceSummaryImpl instance) =>
    <String, dynamic>{
      'totalScore': instance.totalScore,
      'maxScore': instance.maxScore,
      'percentage': instance.percentage,
      'grade': instance.grade,
      'classRank': instance.classRank,
      'totalStudents': instance.totalStudents,
      'simpleSummary': instance.simpleSummary,
      'performanceLevel': instance.performanceLevel,
    };
