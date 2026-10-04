/// What the setup wizard sends, and the checks it makes before it sends.
///
/// Kept apart from the page so the parts that can be wrong without anyone
/// noticing (a term that ends before it starts, a CSV with a comma in a name, a
/// section called "a") are tested without a widget tree.
library;

/// The classes the setup can make. 9 and 10 are what the question bank is for;
/// 1-8 are offered because a school usually has them too and the server seeds
/// their books' chapters (classes 1-5 from 2026-10-04).
const wizardGrades = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const wizardDefaultGrades = [9, 10];
const maxSectionsPerClass = 8;

/// `A`, `B`, ... for the first [count] sections.
List<String> sectionNames(int count) =>
    [for (var i = 0; i < count.clamp(1, maxSectionsPerClass); i++) String.fromCharCode(65 + i)];

final _email = RegExp(r'^[^@\s,"]+@[^@\s,"]+\.[^@\s,"]+$');
bool validEmail(String s) => _email.hasMatch(s.trim());

/// `YYYY-MM-DD` that is a real calendar day.
DateTime? parseIsoDate(String s) {
  final m = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(s.trim());
  if (m == null) return null;
  final y = int.parse(m[1]!), mo = int.parse(m[2]!), d = int.parse(m[3]!);
  final date = DateTime.utc(y, mo, d);
  return date.year == y && date.month == mo && date.day == d ? date : null;
}

String isoDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// The Indian school year containing [today]: 1 April to 31 March.
({String label, String start, String end}) schoolYearFor(DateTime today) {
  final first = today.month >= 4 ? today.year : today.year - 1;
  return (
    label: '$first-${((first + 1) % 100).toString().padLeft(2, '0')}',
    start: '$first-04-01',
    end: '${first + 1}-03-31',
  );
}

class TermDraft {
  String name;
  String start;
  String end;
  TermDraft(this.name, this.start, this.end);
}

/// Two terms: the year's first six months, then the rest.
List<TermDraft> defaultTerms(String yearStart) {
  final s = parseIsoDate(yearStart);
  if (s == null) return [];
  final firstYear = s.year;
  return [
    TermDraft('Term 1', yearStart, '$firstYear-09-30'),
    TermDraft('Term 2', '$firstYear-10-01', '${firstYear + 1}-03-31'),
  ];
}

class BellDraft {
  int periods;
  int periodMinutes;
  String startsAt;
  int breakAfterPeriod;
  int breakMinutes;
  BellDraft({
    this.periods = 8,
    this.periodMinutes = 40,
    this.startsAt = '08:00',
    this.breakAfterPeriod = 4,
    this.breakMinutes = 20,
  });
}

class CalendarDraft {
  String start;
  String end;
  Set<String> weeklyOff;
  bool secondFourthSaturdays;
  List<TermDraft> terms;
  BellDraft bell;
  CalendarDraft({
    required this.start,
    required this.end,
    Set<String>? weeklyOff,
    this.secondFourthSaturdays = false,
    List<TermDraft>? terms,
    BellDraft? bell,
  })  : weeklyOff = weeklyOff ?? {'sunday'},
        terms = terms ?? defaultTerms(start),
        bell = bell ?? BellDraft();
}

/// What is wrong with the calendar, one sentence each; empty when it can be sent.
List<String> calendarProblems(CalendarDraft c) {
  final out = <String>[];
  final start = parseIsoDate(c.start), end = parseIsoDate(c.end);
  if (start == null || end == null) {
    out.add('The year needs a first and a last day, written YYYY-MM-DD.');
  } else if (!end.isAfter(start)) {
    out.add('The year must end after it starts.');
  }
  for (final t in c.terms) {
    final a = parseIsoDate(t.start), b = parseIsoDate(t.end);
    if (a == null || b == null) {
      out.add('${t.name}: both dates are needed, written YYYY-MM-DD.');
      continue;
    }
    if (b.isBefore(a)) out.add('${t.name} ends before it starts.');
    if (start != null && end != null && (a.isBefore(start) || b.isAfter(end))) {
      out.add('${t.name} falls outside the school year.');
    }
  }
  final sorted = [...c.terms]..sort((x, y) => x.start.compareTo(y.start));
  for (var i = 1; i < sorted.length; i++) {
    if (sorted[i].start.compareTo(sorted[i - 1].end) <= 0) {
      out.add('${sorted[i - 1].name} and ${sorted[i].name} overlap.');
    }
  }
  if (c.weeklyOff.length >= 7) out.add('Every day of the week is off.');
  if (RegExp(r'^\d{2}:\d{2}$').firstMatch(c.bell.startsAt) == null) {
    out.add('The first bell is a time like 08:00.');
  }
  if (c.bell.breakAfterPeriod > c.bell.periods) {
    out.add('The break comes after a period the day does not have.');
  }
  return out;
}

/// The body of `POST /curriculum/school-setup`.
Map<String, dynamic> schoolSetupBody({
  required Map<int, int> sectionsByGrade,
  required CalendarDraft calendar,
  String? yearLabel,
}) {
  final grades = sectionsByGrade.keys.toList()..sort();
  return {
    if (yearLabel != null) 'yearLabel': yearLabel,
    'startDate': calendar.start,
    'endDate': calendar.end,
    'classes': [
      for (final g in grades) {'grade': g, 'sections': sectionNames(sectionsByGrade[g]!)},
    ],
    'weeklyOffDays': calendar.weeklyOff.toList()..sort(),
    'secondAndFourthSaturdaysOff': calendar.secondFourthSaturdays,
    'terms': [
      for (final t in calendar.terms) {'name': t.name, 'startDate': t.start, 'endDate': t.end},
    ],
    'bell': {
      'periods': calendar.bell.periods,
      'periodMinutes': calendar.bell.periodMinutes,
      'startsAt': calendar.bell.startsAt,
      'breakAfterPeriod': calendar.bell.breakAfterPeriod,
      'breakMinutes': calendar.bell.breakMinutes,
    },
  };
}

/// One CSV field, quoted when it holds a comma, a quote or a line break.
String csvField(String v) =>
    RegExp(r'[",\r\n]').hasMatch(v) ? '"${v.replaceAll('"', '""')}"' : v;

typedef TeacherRow = ({String name, String email});

/// `teachers` import: `name,email`. Rows with no valid email are left out;
/// [teacherRowProblems] says why.
String teachersCsv(List<TeacherRow> rows) => [
      'name,email',
      for (final r in rows)
        if (validEmail(r.email)) '${csvField(r.name.trim())},${csvField(r.email.trim().toLowerCase())}',
    ].join('\n');

/// Why a row cannot be imported, by 1-based row number; rows that are fine
/// and rows that are wholly empty are not listed.
Map<int, String> teacherRowProblems(List<TeacherRow> rows) {
  final out = <int, String>{};
  final seen = <String>{};
  for (var i = 0; i < rows.length; i++) {
    final r = rows[i];
    if (r.name.trim().isEmpty && r.email.trim().isEmpty) continue;
    final email = r.email.trim().toLowerCase();
    if (!validEmail(email)) {
      out[i + 1] = 'needs an email like name@school.in';
    } else if (!seen.add(email)) {
      out[i + 1] = 'is the same email as an earlier row';
    }
  }
  return out;
}

/// A subject's weekly periods in one class, to every section of it.
typedef AllocationRow = ({int grade, String subject, String? teacherEmail, int periods});

/// `allocations` import: `grade,section,subject,teacher_email,periods_per_week`,
/// one line per section of the class.
String allocationsCsv(List<AllocationRow> rows, Map<int, List<String>> sectionsByGrade) => [
      'grade,section,subject,teacher_email,periods_per_week',
      for (final r in rows)
        for (final s in sectionsByGrade[r.grade] ?? const <String>[])
          '${r.grade},${csvField(s)},${csvField(r.subject)},${r.teacherEmail ?? ''},${r.periods}',
    ].join('\n');

/// A starting weekly load for a subject: the CBSE-typical spread, which the
/// principal edits. Maths, Science, English and Social Science are taught most.
int defaultPeriodsPerWeek(String subject) {
  final s = subject.toLowerCase();
  // Before 'science': "Social Science". EVS is classes 3-5's science and social studies in one.
  if (s.contains('social') || s.contains('hindi') || s == 'evs') return 5;
  if (s.contains('math') || s.contains('science') || s.contains('english')) return 6;
  return 2;
}

/// The five core subjects a first paper is offered for, with the bank's own
/// subject names.
const coreSubjects = ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science'];
