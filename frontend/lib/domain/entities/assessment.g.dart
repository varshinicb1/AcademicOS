// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'assessment.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$AssessmentImpl _$$AssessmentImplFromJson(Map<String, dynamic> json) =>
    _$AssessmentImpl(
      id: json['id'] as String,
      schoolId: json['schoolId'] as String,
      teacherId: json['teacherId'] as String,
      title: json['title'] as String,
      subject: json['subject'] as String,
      grade: (json['grade'] as num).toInt(),
      chapterIds: (json['chapterIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      blueprint: Blueprint.fromJson(json['blueprint'] as Map<String, dynamic>),
      status: $enumDecode(_$AssessmentStatusEnumMap, json['status']),
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      scheduledAt: json['scheduledAt'] == null
          ? null
          : DateTime.parse(json['scheduledAt'] as String),
      completedAt: json['completedAt'] == null
          ? null
          : DateTime.parse(json['completedAt'] as String),
      templateId: json['templateId'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>? ?? const {},
      selectedQuestionIds: (json['selectedQuestionIds'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      generatedPaperId: json['generatedPaperId'] as String?,
      totalStudents: (json['totalStudents'] as num?)?.toInt(),
      evaluatedCount: (json['evaluatedCount'] as num?)?.toInt(),
    );

Map<String, dynamic> _$$AssessmentImplToJson(_$AssessmentImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'schoolId': instance.schoolId,
      'teacherId': instance.teacherId,
      'title': instance.title,
      'subject': instance.subject,
      'grade': instance.grade,
      'chapterIds': instance.chapterIds,
      'blueprint': instance.blueprint,
      'status': _$AssessmentStatusEnumMap[instance.status]!,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
      'scheduledAt': instance.scheduledAt?.toIso8601String(),
      'completedAt': instance.completedAt?.toIso8601String(),
      'templateId': instance.templateId,
      'metadata': instance.metadata,
      'selectedQuestionIds': instance.selectedQuestionIds,
      'generatedPaperId': instance.generatedPaperId,
      'totalStudents': instance.totalStudents,
      'evaluatedCount': instance.evaluatedCount,
    };

const _$AssessmentStatusEnumMap = {
  AssessmentStatus.draft: 'draft',
  AssessmentStatus.blueprintReady: 'blueprintReady',
  AssessmentStatus.questionsSelected: 'questionsSelected',
  AssessmentStatus.questionOptimized: 'questionOptimized',
  AssessmentStatus.paperGenerated: 'paperGenerated',
  AssessmentStatus.underReview: 'underReview',
  AssessmentStatus.principalApproved: 'principalApproved',
  AssessmentStatus.printed: 'printed',
  AssessmentStatus.conducted: 'conducted',
  AssessmentStatus.scanning: 'scanning',
  AssessmentStatus.scanned: 'scanned',
  AssessmentStatus.evaluating: 'evaluating',
  AssessmentStatus.evaluated: 'evaluated',
  AssessmentStatus.teacherReviewed: 'teacherReviewed',
  AssessmentStatus.reportsGenerated: 'reportsGenerated',
  AssessmentStatus.remediationSent: 'remediationSent',
  AssessmentStatus.archived: 'archived',
};
