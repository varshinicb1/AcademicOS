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
  useAppFonts();

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('sign in fits and the Sign in button is on the first screen at $name', (tester) async {
      await pumpPage(tester, const LoginPage(), size);

      expectNoOverflow(tester);
      expectActionReady(tester, find.widgetWithText(FilledButton, 'Sign in'), size, label: 'Sign in');
      expectActionReady(tester, find.byType(SegmentedButton<bool>), size, label: 'the Sign in / Create account switch');
    });

    testWidgets('register with an invite fits and Create account is reachable at $name', (tester) async {
      await pumpPage(tester, const LoginPage(), size);
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

  testWidgets('in a desktop-UA browser at phone width Sign in and the switch are still 48 px', (tester) async {
    // A FilledButton and a SegmentedButton's segments both take their
    // visual density from the theme (filled_button.dart:652,
    // segmented_button.dart resolves it the same way), and a desktop browser
    // narrowed to 375 px -- how this task's screenshots were taken -- gets
    // `compact`, which takes 8 px off every minimumSize. Without the density
    // pinned on those two styles the sign-in button renders 40 px tall
    // there. flutter_test pins the platform to android, so none of the tests
    // above can see it (review of 2026-09-23).
    await withDesktopDensity(() async {
      await pumpPage(tester, const LoginPage(), phoneScreen);
      expectNoOverflow(tester, where: ' at a desktop density');
      expectActionReady(tester, find.widgetWithText(FilledButton, 'Sign in'), phoneScreen,
          label: 'Sign in on a desktop density');
      expectActionReady(tester, find.byType(SegmentedButton<bool>), phoneScreen,
          label: 'the Sign in / Create account switch on a desktop density');
    });
  });

  testWidgets('on a laptop Sign in keeps the compact height the desktop app ships', (tester) async {
    // The other side of the rule above. `phoneTapTarget` used to be a const
    // style applied at every width, so the 48 px minimum and the pinned
    // standard density followed these buttons onto a 1280 px screen, where
    // ThemeData's compact density draws them 32 px tall: Sign in and about
    // fourteen console and form actions silently grew and gained padding on
    // a laptop, against Task 801's "keep the desktop look", and nothing in
    // this suite could see it because every desktop-density test above runs
    // at phone width (review of 2026-09-23). The comparison is against a
    // bare FilledButton pumped in the same theme at the same density, so it
    // stays true if the theme's button metrics ever change.
    await withDesktopDensity(() async {
      final shipped = await themeButtonHeight(tester, laptopScreen);
      await pumpPage(tester, const LoginPage(), laptopScreen);
      expectNoOverflow(tester, where: ' on a laptop at a desktop density');
      final signIn = tester.getRect(paintedTarget(tester, find.widgetWithText(FilledButton, 'Sign in'))).height;
      expect(signIn, shipped,
          reason: 'Sign in draws ${signIn.toStringAsFixed(0)} px tall on a 1280 px screen; an unstyled '
              'button in the same theme draws ${shipped.toStringAsFixed(0)} px. A phone tap target must '
              'not follow the app onto a laptop.');
    });
  });
}
