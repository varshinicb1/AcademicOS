import 'package:freezed_annotation/freezed_annotation.dart';

import 'enums.dart';
import '../repositories/requests.dart';

part 'assessment.freezed.dart';
part 'assessment.g.dart';

@freezed
class Assessment with _$Assessment {
  const factory Assessment({
    required String id,
    required String schoolId,
    required String teacherId,
    required String title,
    required String subject,
    required int grade,
    required List<String> chapterIds,
    required Blueprint blueprint,
    required AssessmentStatus status,
    required DateTime createdAt,
    required DateTime updatedAt,
    DateTime? scheduledAt,
    DateTime? completedAt,
    String? templateId,
    @Default({}) Map<String, dynamic> metadata,
    @Default([]) List<String> selectedQuestionIds,
    String? generatedPaperId,
    int? totalStudents,
    int? evaluatedCount,
  }) = _Assessment;

  factory Assessment.fromJson(Map<String, dynamic> json) => _$AssessmentFromJson(json);
}

extension BlueprintRequestExt on Blueprint {
  BlueprintRequest toRequest() => BlueprintRequest(
    totalMarks: totalMarks,
    durationMinutes: durationMinutes,
    difficulty: difficulty,
    bloom: bloom,
    chapterWeights: chapterWeights,
    competencyWeights: competencyWeights,
    sections: sections,
    schoolTemplate: metadata,
  );
}
