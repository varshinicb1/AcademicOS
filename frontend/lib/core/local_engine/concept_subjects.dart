import 'local_store.dart';

/// Maps a student's real weak/mastered concept IDs (keyed by
/// _updateMasteryFromSheet's own convention) back to a real subject/grade
/// by scanning the assessments they were actually evaluated against --
/// every question in one assessment shares that assessment's subject, so
/// this is derived, not guessed. Shared by generatePractice() and the
/// report card's narrative gap analysis -- was duplicated inline in
/// LocalPillarApi until this extraction.
Map<String, (String subject, int grade)> conceptSubjectsFor(String studentId) {
  final map = <String, (String, int)>{};
  for (final a in LocalStore.instance.allAssessments()) {
    final id = a['id'] as String;
    final subject = a['subject'] as String?;
    final grade = (a['grade'] as num?)?.toInt();
    if (subject == null || grade == null) continue;
    for (final sheet in LocalStore.instance.evaluationsFor(id)) {
      if (sheet['studentId'] != studentId) continue;
      for (final ev in (sheet['evaluations'] as List? ?? [])) {
        final concept = (ev as Map)['conceptId'] as String?;
        if (concept != null) map[concept] = (subject, grade);
      }
    }
  }
  return map;
}
