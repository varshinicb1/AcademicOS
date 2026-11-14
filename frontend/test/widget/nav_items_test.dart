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
    expect(t.take(9), ['Today', 'My day', 'My week', 'Papers', 'Homework', 'Mark answer sheets', 'Class progress',
        'Messages', 'Inbox'], reason: 'MSG-1: parents write to teachers');
    expect(t, containsAll(['Question bank', 'Paper reviews', 'Exam duties']));
    expect([for (final s in navSectionsFor('teacher')) s.title], [null, 'More']);
    expect(navSectionsFor('teacher').last.collapsible, isTrue);
    expect(t, isNot(contains('School insights')));
    expect(t, isNot(contains('Mastery')), reason: 'the student-id mastery page is not a teacher destination');
  });

  test('a teacher sees exactly the admin tools the principal granted', () {
    expect(labels('teacher', grants: {'exams', 'timetable'}), containsAll(['Exams', 'Timetable', 'Lesson plans']));
    expect(labels('teacher', grants: {'leave'}), containsAll(['Attendance and cover', 'Periods owed']));
    expect(labels('teacher', grants: {'exams'}), isNot(contains('Timetable')));
    final sections = navSectionsFor('teacher', grants: {'leave'});
    expect(sections.last.title, 'Admin');
    expect(sections.last.openByDefault, isTrue, reason: 'the tools a principal handed over start open');
    expect(navSectionsFor('teacher').any((s) => s.title == 'Admin'), isFalse);
  });

  test('the principal sees eight core pages; the rest fold under More and Setup', () {
    final sections = navSectionsFor('principal');
    expect([for (final s in sections) s.title], [null, 'More', 'Setup']);
    expect([for (final i in sections.first.items) i.label], ['Overview', 'Papers', 'Exams', 'Timetable',
        'Lesson plans', 'Attendance and cover', 'Term report', 'Inbox']);
    expect(sections.first.collapsible, isFalse);
    expect([for (final i in sections[1].items) i.label], ['Paper reviews', 'School insights', 'Periods owed',
        'Homework', 'Class progress', 'Messages', 'Question bank']);
    expect([for (final i in sections[2].items) i.label], ['Set up your school', 'Invite people', 'Staff and access',
        'School profile', 'Import and export', 'Calendar and terms']);
    for (final s in sections.skip(1)) {
      expect(s.collapsible, isTrue, reason: '${s.title} folds away');
      expect(s.openByDefault, isFalse, reason: '${s.title} starts folded');
    }
  });

  test('folding the menu dropped no principal page', () {
    // Every destination the principal had before 2026-10-01, by path.
    const before = ['/school', '/assessment', '/school/reviews', '/school/term-report', '/analytics/school',
      '/school/inbox', '/school/exams', '/school/timetable', '/school/lesson-plans', '/school/cover',
      '/school/periods-owed', '/school/homework', '/school/class-progress', '/school/question-bank', '/admin',
      '/school/grants', '/school/import', '/school/school-profile'];
    final paths = [for (final i in navItemsFor('principal')) i.path];
    expect(paths, containsAll(before));
    expect(paths, contains('/admin?tab=calendar-setup'));
  });

  test('a student and a parent get their own few destinations', () {
    expect(labels('student'), ['Today', 'My week', 'Homework', 'Progress', 'Exams', 'Inbox']);
    expect(labels('parent'), ['My children', 'Messages', 'Inbox']);
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
    expect(at(principal, '/admin'), 'Invite people');
    expect(at(principal, '/admin?tab=calendar-setup'), 'Calendar and terms');
    expect(at(principal, '/admin?tab=roster'), 'Invite people', reason: 'another tab is read by its path');
    expect(at(principal, '/school/question-bank?review=1'), 'Question bank');
    final student = navItemsFor('student');
    expect(at(student, '/school/my-homework/h1'), 'Homework');
    expect(at(student, '/school/today'), 'Today');
    final offline = navItemsFor('');
    expect(at(offline, '/analytics/gaps'), 'Class gaps');
    expect(at(offline, '/analytics/mastery'), 'Mastery');
    expect(at(offline, '/planner/daily'), 'Planner');
  });
}
