// Task 801: signing in, and registering with an invite, in a phone browser,
// on a tablet and on a laptop. The sign-in button must be on the first
// screen without scrolling; the longer register form may scroll (the
// on-screen keyboard covers half a phone anyway), but its button must then be
// reachable, uncovered and big enough to hit.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/presentation/auth/pages/login_page.dart';

import 'responsive_harness.dart';

void main() {
  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('sign in fits and the Sign in button is on the first screen at $name', (tester) async {
      useScreen(tester, size);
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));
      await tester.pumpAndSettle();

      expectNoOverflow(tester);
      expectActionReady(tester, find.widgetWithText(FilledButton, 'Sign in'), size, label: 'Sign in');
      expectActionReady(tester, find.byType(SegmentedButton<bool>), size, label: 'the Sign in / Create account switch');
    });

    testWidgets('register with an invite fits and Create account is reachable at $name', (tester) async {
      useScreen(tester, size);
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Create account'));
      await tester.pumpAndSettle();

      expectNoOverflow(tester);
      expect(find.byKey(const Key('register-invite-code')), findsOneWidget);
      await scrollToAndExpectReady(tester, find.widgetWithText(FilledButton, 'Create account'), size,
          label: 'Create account');

      // A validation pass (every field empty) adds an error line under each
      // field; the form must still fit and the button still be reachable.
      await tester.tap(find.widgetWithText(FilledButton, 'Create account'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' after validation');
      expect(find.text('Required'), findsWidgets);
      await scrollToAndExpectReady(tester, find.widgetWithText(FilledButton, 'Create account'), size,
          label: 'Create account after validation');
    });
  }
}
