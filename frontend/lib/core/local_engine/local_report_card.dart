import '../constants/app_constants.dart';
import 'local_store.dart';

/// One subject's real performance for a student's report card -- built
/// from actual evaluations recorded against real assessments, never
/// invented.
class ReportCardSubject {
  final String subject;
  final int assessmentCount;
  final int totalAwarded;
  final int totalMax;
  double get percentage => totalMax > 0 ? 100.0 * totalAwarded / totalMax : 0.0;

  const ReportCardSubject({
    required this.subject,
    required this.assessmentCount,
    required this.totalAwarded,
    required this.totalMax,
  });
}

class ReportCardData {
  final String studentId;
  final String studentName;
  final String schoolName;
  final int grade;
  final List<ReportCardSubject> subjects;
  final double overallMastery;
  final List<String> weakConcepts;
  final DateTime generatedAt;

  double get overallPercentage {
    final totalAwarded = subjects.fold<int>(0, (s, r) => s + r.totalAwarded);
    final totalMax = subjects.fold<int>(0, (s, r) => s + r.totalMax);
    return totalMax > 0 ? 100.0 * totalAwarded / totalMax : 0.0;
  }

  const ReportCardData({
    required this.studentId,
    required this.studentName,
    required this.schoolName,
    required this.grade,
    required this.subjects,
    required this.overallMastery,
    required this.weakConcepts,
    required this.generatedAt,
  });
}

/// Aggregates a student's real evaluation and mastery history into a
/// report card -- the "report card generation" feature requested but
/// never built. Every number here comes from a real stored evaluation or
/// a real stored mastery record; a subject with no evaluated assessments
/// simply doesn't appear rather than showing a fabricated zero.
class LocalReportCardService {
  static ReportCardData generate(String studentId, {String schoolId = AppConstants.currentSchoolId}) {
    final assessments = LocalStore.instance
        .allAssessments()
        .where((a) => a['schoolId'] == schoolId)
        .toList();

    final bySubject = <String, ReportCardSubject>{};
    int grade = 10;
    for (final a in assessments) {
      final id = a['id'] as String;
      final subject = a['subject'] as String? ?? '';
      if (subject.isEmpty) continue;
      grade = (a['grade'] as num?)?.toInt() ?? grade;

      final evals = LocalStore.instance
          .evaluationsFor(id)
          .where((e) => e['studentId'] == studentId)
          .toList();
      if (evals.isEmpty) continue;

      final awarded = evals.fold<int>(0, (s, e) => s + (e['totalAwarded'] as num? ?? 0).toInt());
      final max = evals.fold<int>(0, (s, e) => s + (e['totalMax'] as num? ?? 0).toInt());

      final existing = bySubject[subject];
      bySubject[subject] = ReportCardSubject(
        subject: subject,
        assessmentCount: (existing?.assessmentCount ?? 0) + evals.length,
        totalAwarded: (existing?.totalAwarded ?? 0) + awarded,
        totalMax: (existing?.totalMax ?? 0) + max,
      );
    }

    final masteryRaw = LocalStore.instance.getMastery(studentId);
    final overallMastery = (masteryRaw?['overallMastery'] as num? ?? 0).toDouble();
    final weakConcepts = List<String>.from(masteryRaw?['weakConcepts'] as List? ?? const []);

    final subjectsList = bySubject.values.toList()
      ..sort((a, b) => a.subject.compareTo(b.subject));

    return ReportCardData(
      studentId: studentId,
      studentName: LocalStore.instance.studentName(studentId),
      schoolName: LocalStore.instance.schoolName(schoolId),
      grade: grade,
      subjects: subjectsList,
      overallMastery: overallMastery,
      weakConcepts: weakConcepts,
      generatedAt: DateTime.now(),
    );
  }
}
