import '../constants/app_constants.dart';
import 'concept_subjects.dart';
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

/// A single real learning gap -- one weak concept, its real subject (derived
/// from the assessments it was actually evaluated against, never guessed),
/// and a deterministic, constructive suggestion. Deliberately not an LLM
/// call: the "deterministic core" principle this codebase already follows
/// for grading (see docs/architecture.md) applies just as much to a document
/// a parent reads -- the wording must be reproducible and explainable, not a
/// fresh generation every time the same real mastery numbers are re-read.
class LearningGap {
  final String conceptId;
  final String subject;
  final double mastery;
  final int evidenceCount;
  final String suggestion;

  const LearningGap({
    required this.conceptId,
    required this.subject,
    required this.mastery,
    required this.evidenceCount,
    required this.suggestion,
  });
}

/// A concept the student has real, evidenced strength in -- included
/// alongside the gaps so the report isn't purely deficit-focused. Per the
/// user's own framing: "its not about blaming the student, its about
/// finding the solution to improve" -- a report that only lists weaknesses
/// reads as blame even when every number in it is real.
class Strength {
  final String conceptId;
  final String subject;
  final double mastery;

  const Strength({required this.conceptId, required this.subject, required this.mastery});
}

class ReportCardData {
  final String studentId;
  final String studentName;
  final String schoolName;
  final int grade;
  final List<ReportCardSubject> subjects;
  final double overallMastery;
  final List<String> weakConcepts;
  final List<LearningGap> learningGaps;
  final List<Strength> strengths;
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
    required this.learningGaps,
    required this.strengths,
    required this.generatedAt,
  });
}

/// Deterministic, constructive suggestion text keyed off real mastery/
/// evidence numbers -- three severity bands (not just the binary weak/not
/// weak split every weak concept otherwise shares) plus an honest caveat
/// when the mastery estimate rests on very little real evidence, so the
/// report never states more confidence than the data actually supports.
String _suggestionFor({required double mastery, required int evidenceCount, required String subject}) {
  final String core;
  if (mastery < 0.2) {
    core = 'This appears to be an early-stage gap -- a short one-on-one walkthrough of the '
        'basics of this topic, before assigning further practice, is likely to help most.';
  } else if (mastery < 0.35) {
    core = 'This is a real foundational gap in $subject -- targeted one-on-one review of this '
        'specific topic is recommended before moving on to related material.';
  } else {
    core = 'Some understanding is present but not yet secure -- a few more focused practice '
        'questions on this topic specifically should help close the gap.';
  }
  if (evidenceCount <= 2) {
    return '$core (Based on only $evidenceCount recorded attempt${evidenceCount == 1 ? '' : 's'} so far '
        '-- worth confirming with a bit more practice before treating this as settled.)';
  }
  return core;
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
    final concepts = List<Map<String, dynamic>>.from(masteryRaw?['concepts'] as List? ?? const []);
    final conceptSubjects = conceptSubjectsFor(studentId);

    final learningGaps = concepts.where((c) => c['isWeak'] == true).map((c) {
      final conceptId = c['conceptId'] as String? ?? c['conceptName'] as String? ?? '';
      final mastery = (c['mastery'] as num? ?? 0).toDouble();
      final evidenceCount = (c['evidenceCount'] as num? ?? 0).toInt();
      final subject = conceptSubjects[conceptId]?.$1 ?? '';
      return LearningGap(
        conceptId: conceptId,
        subject: subject,
        mastery: mastery,
        evidenceCount: evidenceCount,
        suggestion: _suggestionFor(
          mastery: mastery,
          evidenceCount: evidenceCount,
          subject: subject.isNotEmpty ? subject : 'this subject',
        ),
      );
    }).toList()
      ..sort((a, b) => a.mastery.compareTo(b.mastery));

    final strengths = concepts.where((c) => c['status'] == 'proficient').map((c) {
      final conceptId = c['conceptId'] as String? ?? c['conceptName'] as String? ?? '';
      return Strength(
        conceptId: conceptId,
        subject: conceptSubjects[conceptId]?.$1 ?? '',
        mastery: (c['mastery'] as num? ?? 0).toDouble(),
      );
    }).toList()
      ..sort((a, b) => b.mastery.compareTo(a.mastery));

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
      learningGaps: learningGaps,
      strengths: strengths,
      generatedAt: DateTime.now(),
    );
  }
}
