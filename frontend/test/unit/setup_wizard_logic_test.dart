import 'package:academicos/presentation/onboarding/setup_wizard_logic.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('the Indian school year is the one that contains today', () {
    expect(schoolYearFor(DateTime(2026, 10, 3)), (label: '2026-27', start: '2026-04-01', end: '2027-03-31'));
    expect(schoolYearFor(DateTime(2027, 2, 1)), (label: '2026-27', start: '2026-04-01', end: '2027-03-31'));
    expect(schoolYearFor(DateTime(2027, 4, 1)).label, '2027-28');
    expect(schoolYearFor(DateTime(2099, 5, 1)).label, '2099-00');
  });

  test('dates must be real calendar days', () {
    expect(parseIsoDate('2026-02-30'), isNull);
    expect(parseIsoDate('2026-2-3'), isNull);
    expect(parseIsoDate('2028-02-29'), isNotNull);
    expect(isoDate(DateTime.utc(2026, 4, 1)), '2026-04-01');
  });

  test('section names run A, B, C and stay within the limit', () {
    expect(sectionNames(3), ['A', 'B', 'C']);
    expect(sectionNames(0), ['A']);
    expect(sectionNames(99).length, maxSectionsPerClass);
  });

  group('calendar checks', () {
    CalendarDraft ok() => CalendarDraft(start: '2026-04-01', end: '2027-03-31');

    test('the default calendar can be sent', () => expect(calendarProblems(ok()), isEmpty));

    test('a term that ends before it starts, or leaves the year, is named', () {
      final c = ok()..terms[0].end = '2026-03-01';
      expect(calendarProblems(c), contains('Term 1 ends before it starts.'));
      final d = ok()..terms[1].end = '2027-06-30';
      expect(calendarProblems(d), contains('Term 2 falls outside the school year.'));
    });

    test('overlapping terms, an unreal date, and a week with no working day are named', () {
      final overlap = ok()..terms[1].start = '2026-09-01';
      expect(calendarProblems(overlap).any((p) => p.contains('overlap')), isTrue);
      final bad = ok()..terms[0].start = '2026-13-01';
      expect(calendarProblems(bad).any((p) => p.startsWith('Term 1: both dates')), isTrue);
      final week = ok()..weeklyOff = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'};
      expect(calendarProblems(week), contains('Every day of the week is off.'));
    });

    test('a break after a period the day does not have is named', () {
      final c = ok()..bell.breakAfterPeriod = 9;
      expect(calendarProblems(c), contains('The break comes after a period the day does not have.'));
    });
  });

  test('the setup body is what the server reads', () {
    final c = CalendarDraft(start: '2026-04-01', end: '2027-03-31', secondFourthSaturdays: true);
    final body = schoolSetupBody(sectionsByGrade: {10: 2, 9: 1}, calendar: c);
    expect(body['classes'], [
      {'grade': 9, 'sections': ['A']},
      {'grade': 10, 'sections': ['A', 'B']},
    ]);
    expect(body['weeklyOffDays'], ['sunday']);
    expect(body['secondAndFourthSaturdaysOff'], true);
    expect((body['terms'] as List).first, {'name': 'Term 1', 'startDate': '2026-04-01', 'endDate': '2026-09-30'});
    expect((body['bell'] as Map)['startsAt'], '08:00');
    expect(body.containsKey('yearLabel'), isFalse);
  });

  group('teachers', () {
    test('the CSV quotes what needs quoting and drops rows with no valid email', () {
      final csv = teachersCsv([
        (name: 'Rao, Anita', email: ' Anita@School.in '),
        (name: 'No Email', email: ''),
        (name: 'Bad', email: 'not-an-email'),
        (name: 'Say "Hi"', email: 'hi@school.in'),
      ]);
      expect(csv.split('\n'), ['name,email', '"Rao, Anita",anita@school.in', '"Say ""Hi""",hi@school.in']);
    });

    test('problems are by row, skip empty rows, and catch duplicates', () {
      final problems = teacherRowProblems([
        (name: '', email: ''),
        (name: 'A', email: 'a@s.in'),
        (name: 'B', email: 'A@S.in'),
        (name: 'C', email: 'oops'),
      ]);
      expect(problems.keys, [3, 4]);
      expect(problems[3], contains('same email'));
      expect(problems[4], contains('needs an email'));
    });
  });

  test('allocations repeat each subject for every section of the class', () {
    final csv = allocationsCsv([
      (grade: 10, subject: 'Science', teacherEmail: 'anita@school.in', periods: 6),
      (grade: 9, subject: 'Social Science', teacherEmail: null, periods: 5),
    ], {10: ['A', 'B'], 9: ['A']});
    expect(csv.split('\n'), [
      'grade,section,subject,teacher_email,periods_per_week',
      '10,A,Science,anita@school.in,6',
      '10,B,Science,anita@school.in,6',
      '9,A,Social Science,,5',
    ]);
  });

  test('core subjects get a heavier week than the rest', () {
    expect(defaultPeriodsPerWeek('Mathematics'), 6);
    expect(defaultPeriodsPerWeek('Social Science'), 5);
    expect(defaultPeriodsPerWeek('Art Education'), 2);
  });
}
