/// Counts in words a teacher reads: "1 mark", "2 marks", "1 chapter". The
/// paper screens printed "1 marks", "1 chapters" and "question(s)" (QA P-33).
String counted(int n, String one, [String? many]) => '$n ${n == 1 ? one : many ?? '${one}s'}';

/// "1 mark" / "5 marks".
String marksText(int n) => counted(n, 'mark');

/// "1 question" / "38 questions".
String questionsText(int n) => counted(n, 'question');

/// A section's heading without its letter twice: a preset's section is
/// already named "Section A - Objective", which printed as "Section A ·
/// Section A - Objective" (QA P-33).
String sectionHeading(String label, String name, {String separator = ' · '}) {
  final lettered = name.trimLeft().toLowerCase().startsWith('section ${label.toLowerCase()}');
  return lettered ? name : 'Section $label$separator$name';
}
