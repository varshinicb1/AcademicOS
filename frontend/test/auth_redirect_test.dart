// Unit tests for the router's sign-in-first gate (authRedirect in
// app_router.dart): the rule that keeps signed-out visitors off
// authenticated pages so they meet the sign-in screen instead of a raw
// 401 error. Pure function -- no widgets, no router, no Hive.
import 'package:academicos/core/routing/app_router.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('authRedirect', () {
    test('signed-out online user is sent to /login from every gated page', () {
      const gated = [
        '/home', '/assessment', '/assessment/create', '/syllabus',
        '/planner', '/questions', '/evaluation', '/scan', '/parent',
        '/admin', '/settings', '/settings/profile', '/student/schedule',
        '/my-schedule',
      ];
      for (final loc in gated) {
        expect(authRedirect(loc, signedIn: false, offlineBuild: false), '/login',
            reason: loc);
      }
    });

    test('signed-out online user stays on the sign-in screen and legal docs', () {
      const public = [
        '/login', '/settings/login', '/settings/legal/privacy', '/settings/legal/terms',
      ];
      for (final loc in public) {
        expect(authRedirect(loc, signedIn: false, offlineBuild: false), isNull,
            reason: loc);
      }
    });

    test('signed-in user is never bounced anywhere', () {
      const anywhere = ['/home', '/assessment', '/login', '/settings/login', '/settings'];
      for (final loc in anywhere) {
        expect(authRedirect(loc, signedIn: true, offlineBuild: false), isNull,
            reason: loc);
      }
    });

    test('offline build never redirects -- there are no accounts there', () {
      const anywhere = ['/home', '/assessment', '/login'];
      for (final loc in anywhere) {
        expect(authRedirect(loc, signedIn: false, offlineBuild: true), isNull,
            reason: loc);
        expect(authRedirect(loc, signedIn: true, offlineBuild: true), isNull,
            reason: loc);
      }
    });
  });
}
