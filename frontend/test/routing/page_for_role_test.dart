// The router's role guard: a person is not left on a page the server will refuse them, and the
// v2 pages with a v3 replacement send a signed-in person to it (audit 2026-10-04).
import 'package:academicos/core/routing/app_router.dart';
import 'package:flutter_test/flutter_test.dart';

String? go(String loc, String role, {bool offline = false}) =>
    pageForRole(loc, role: role, offlineBuild: offline);

void main() {
  test('a student reaches their own pages and is sent home from anyone else\'s', () {
    for (final ok in ['/home', '/school', '/school/today', '/school/week', '/school/my-homework/hw_1',
      '/school/my-learning', '/school/my-exams', '/school/my-report-card', '/school/inbox', '/school/guide',
      '/school/practice/p1', '/practice/p1', '/settings', '/settings/legal/privacy']) {
      expect(go(ok, 'student'), isNull, reason: ok);
    }
    for (final no in ['/admin', '/owner', '/school/timetable', '/school/question-bank', '/school/homework',
      '/school/grants', '/assessment', '/scan', '/school/family']) {
      expect(go(no, 'student'), '/home', reason: no);
    }
  });

  test('a parent reaches their children and the inbox, and nothing the school keeps to itself', () {
    for (final ok in ['/home', '/school', '/school/family', '/school/inbox', '/school/my-exams',
      '/school/my-homework/hw_1', '/school/guide', '/settings']) {
      expect(go(ok, 'parent'), isNull, reason: ok);
    }
    for (final no in ['/admin', '/school/week', '/school/today', '/school/term-report', '/assessment']) {
      expect(go(no, 'parent'), '/home', reason: no);
    }
  });

  test('a teacher is kept out of the principal\'s pages and the owner overview only', () {
    for (final no in ['/admin', '/admin?tab=calendar-setup', '/owner', '/school/grants']) {
      expect(go(no, 'teacher'), '/home', reason: no);
    }
    for (final ok in ['/home', '/school/my-day', '/assessment', '/school/timetable', '/school/import',
      '/analytics/school']) {
      expect(go(ok, 'teacher'), isNull, reason: ok);
    }
  });

  test('a principal is kept out of the owner overview; an owner is left alone', () {
    expect(go('/owner', 'principal'), '/home');
    expect(go('/admin', 'principal'), isNull);
    expect(go('/school/grants', 'principal'), isNull);
    expect(go('/owner', 'owner'), isNull);
    expect(go('/admin', 'owner'), isNull);
  });

  test('the v2 pages with a v3 replacement send everyone signed in to it', () {
    for (final role in ['teacher', 'principal', 'owner', 'student', 'parent']) {
      expect(go('/syllabus', role), '/home', reason: role);
      expect(go('/planner/daily', role), '/home', reason: role);
      expect(go('/analytics', role), '/home', reason: role);
      expect(go('/analytics/gaps?assessment=a', role), '/home', reason: role);
    }
    expect(go('/student/schedule', 'student'), '/school/week');
    expect(go('/parent', 'parent'), '/school/family');
  });

  test('pages other roles still use are not replaced', () {
    for (final p in ['/analytics/mastery', '/analytics/school', '/my-schedule', '/scan', '/scan-history',
      '/evaluation', '/questions', '/assessment/build']) {
      expect(go(p, 'teacher'), isNull, reason: p);
    }
  });

  test('the offline build and an unknown role are never redirected', () {
    expect(go('/syllabus', 'student', offline: true), isNull);
    expect(go('/admin', '', offline: false), isNull);
    expect(go('/admin', 'unknown'), isNull);
  });

  test('every place the guard sends a person is itself allowed for them', () {
    for (final role in ['student', 'parent', 'teacher', 'principal']) {
      expect(go('/home', role), isNull, reason: '$role /home must not loop');
    }
    expect(go('/school/week', 'student'), isNull);
    expect(go('/school/family', 'parent'), isNull);
  });
}
