import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:flutter_test/flutter_test.dart';

// The web console's side navigation lists what each role can use: a student
// or a parent is not shown teacher tools, and a teacher is not shown the
// principal's school-wide insights.
void main() {
  List<String> labels(String role) => [for (final i in navItemsFor(role)) i.label];

  test('staff see the teaching tools; only the principal sees school insights', () {
    expect(labels('principal'), contains('School insights'));
    expect(labels('teacher'), isNot(contains('School insights')));
    expect(labels('teacher'), containsAll(['Today', 'Papers', 'Question bank', 'Evaluate', 'School']));
    expect(labels(''), labels('principal'), reason: 'no account (offline, tests) keeps the full list');
  });

  test('a student and a parent get their own few destinations', () {
    expect(labels('student'), ['My day', 'Homework', 'Exams', 'Learning', 'Inbox']);
    expect(labels('parent'), ['Family', 'Inbox']);
  });

  test('the longest matching prefix picks the destination', () {
    final staff = navItemsFor('principal');
    String at(String path) => staff[navIndexFor(staff, path)].label;
    expect(at('/analytics/gaps'), 'Class gaps');
    expect(at('/analytics/school'), 'School insights');
    expect(at('/analytics/mastery'), 'Mastery');
    expect(at('/planner/daily'), 'Planner');
    expect(at('/school/reviews'), 'School');
    expect(at('/somewhere-else'), 'Today');
    final student = navItemsFor('student');
    expect(student[navIndexFor(student, '/school/my-homework/h1')].label, 'Homework');
    expect(student[navIndexFor(student, '/school')].label, 'My day');
  });
}
