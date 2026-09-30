import 'package:academicos/core/routing/app_router.dart';
import 'package:academicos/presentation/workspace/app_mode.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('a parent lands on their children, a student on their workspace', () {
    expect(roleLanding('/home', role: 'parent', offlineBuild: false), '/school/family');
    expect(roleLanding('/home', role: 'student', offlineBuild: false), '/school');
  });

  test('a teacher keeps their day; the principal opens on the school', () {
    expect(roleLanding('/home', role: 'teacher', offlineBuild: false), isNull);
    expect(roleLanding('/home', role: 'principal', offlineBuild: false), '/school');
    expect(roleLanding('/school/inbox', role: 'parent', offlineBuild: false), isNull);
    expect(roleLanding('/assessment', role: 'student', offlineBuild: false), isNull);
  });

  test('offline builds have no roles to route by', () {
    expect(roleLanding('/home', role: 'parent', offlineBuild: true), isNull);
  });

  test('the teacher and student apps land on their own first page', () {
    expect(roleLanding('/home', role: 'teacher', offlineBuild: false, mode: AppMode.teacher), '/school/my-day');
    expect(roleLanding('/home', role: 'student', offlineBuild: false, mode: AppMode.student), '/school/today');
    expect(roleLanding('/home', role: 'parent', offlineBuild: false, mode: AppMode.student), '/school/family');
    expect(roleLanding('/home', role: '', offlineBuild: false, mode: AppMode.teacher), isNull);
  });
}
