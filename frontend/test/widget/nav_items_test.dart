import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:flutter_test/flutter_test.dart';

// The web console's side navigation lists what each role uses day to day --
// the same destinations as the School tiles -- instead of the v2 teacher
// tools for everyone (review 2026-10-01).
void main() {
  List<String> labels(String role, {Set<String> grants = const {}}) =>
      [for (final i in navItemsFor(role, grants: grants)) i.label];

  test('a teacher sees their day, papers, homework and marking; no principal tools', () {
    final t = labels('teacher');
    expect(t.take(7), ['Today', 'My week', 'Papers', 'Homework', 'Mark answer sheets', 'Class progress', 'Inbox']);
    expect(t, containsAll(['Question bank', 'Paper reviews', 'Exam duties']));
    expect(t, isNot(contains('School insights')));
    expect(t, isNot(contains('Mastery')), reason: 'the student-id mastery page is not a teacher destination');
  });

  test('a teacher sees exactly the admin tools the principal granted', () {
    expect(labels('teacher', grants: {'exams', 'timetable'}), containsAll(['Exams', 'Timetable', 'Lesson plans']));
    expect(labels('teacher', grants: {'leave'}), containsAll(['Attendance and cover', 'Periods owed']));
    expect(labels('teacher', grants: {'exams'}), isNot(contains('Timetable')));
    final sections = navSectionsFor('teacher', grants: {'leave'});
    expect(sections.last.title, 'Admin');
    expect(navSectionsFor('teacher').any((s) => s.title == 'Admin'), isFalse);
  });

  test('the principal runs and sets up the school from the side navigation', () {
    final p = labels('principal');
    expect(p, containsAll(['Overview', 'Paper reviews', 'Term report', 'Exams', 'Timetable',
        'Attendance and cover', 'Staff and access', 'Import and export', 'School profile',
        'Lesson plans', 'Periods owed']));
    expect([for (final s in navSectionsFor('principal')) s.title], [null, 'Run the school', 'Setup']);
  });

  test('a student and a parent get their own few destinations', () {
    expect(labels('student'), ['Today', 'My week', 'Homework', 'Progress', 'Exams', 'Inbox']);
    expect(labels('parent'), ['My children', 'Inbox']);
  });

  test('no account (offline, tests) keeps the pages that work on the device', () {
    expect(labels(''), ['Today', 'Papers', 'Question bank', 'Evaluate', 'Planner', 'Syllabus',
        'Mastery', 'Class gaps', 'School insights', 'School']);
  });

  test('the longest matching prefix picks the destination, and none is picked off the list', () {
    final principal = navItemsFor('principal');
    String? at(List<NavItem> items, String path) {
      final i = navIndexFor(items, path);
      return i < 0 ? null : items[i].label;
    }
    expect(at(principal, '/school'), 'Overview');
    expect(at(principal, '/school/exams'), 'Exams');
    expect(at(principal, '/school/reviews'), 'Paper reviews');
    expect(at(principal, '/assessment/abc'), 'Papers');
    expect(at(principal, '/somewhere-else'), isNull);
    final student = navItemsFor('student');
    expect(at(student, '/school/my-homework/h1'), 'Homework');
    expect(at(student, '/school/today'), 'Today');
    final offline = navItemsFor('');
    expect(at(offline, '/analytics/gaps'), 'Class gaps');
    expect(at(offline, '/analytics/mastery'), 'Mastery');
    expect(at(offline, '/planner/daily'), 'Planner');
  });
}
