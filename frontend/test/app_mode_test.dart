import 'package:academicos/presentation/workspace/app_mode.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('each app build opens on its own first page', () {
    expect(appHome(AppMode.teacher), '/school/my-day');
    expect(appHome(AppMode.student), '/school/today');
    expect(appHome(AppMode.student, role: 'parent'), '/school/family');
    expect(appHome(AppMode.console), '/home');
  });

  test('the phone apps keep to five tabs or fewer', () {
    for (final mode in AppMode.values) {
      for (final role in ['teacher', 'principal', 'student', 'parent']) {
        expect(appTabs(mode, role: role).length, lessThanOrEqualTo(5));
      }
    }
    expect(appTabs(AppMode.console), isEmpty);
  });

  test('a deep page selects its own tab, not the catch-all', () {
    final tabs = appTabs(AppMode.teacher);
    expect(tabs[tabIndexFor(tabs, '/school/homework/hw_1')].label, 'Homework');
    expect(tabs[tabIndexFor(tabs, '/school/reviews')].label, 'More');
    expect(tabs[tabIndexFor(tabs, '/assessment/abc')].label, 'Papers');
    final student = appTabs(AppMode.student);
    expect(student[tabIndexFor(student, '/school/my-homework/hw_1')].label, 'Homework');
  });

  test('the web console is the default build', () {
    expect(appMode, AppMode.console);
  });
}
