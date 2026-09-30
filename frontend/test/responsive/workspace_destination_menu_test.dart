// The school workspace's pages (/school/exams, /school/my-homework, ...) are
// nested under /school, so go_router leaves the overview beneath each one.
// Their app bars printed Flutter's back arrow to it, and on a phone none of
// them had the menu: a student or parent could not get from Today to their
// homework or exams except through the overview (E2E run on production's
// commit, 2026-10-01). A destination's bar is destinationAppBar: the menu on
// a phone, no back arrow anywhere; a page pushed over one keeps its back arrow.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/shared/widgets/shell.dart';

import 'responsive_harness.dart';

Widget _app(String initial) {
  final router = GoRouter(
    initialLocation: initial,
    routes: [
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/school',
            builder: (context, _) => Scaffold(appBar: destinationAppBar(context, title: const Text('School'))),
            routes: [
              GoRoute(
                path: 'exams',
                builder: (context, _) => Scaffold(appBar: destinationAppBar(context, title: const Text('Exams'))),
              ),
              GoRoute(
                path: 'homework/:id',
                builder: (context, _) => Scaffold(appBar: AppBar(title: const Text('One homework'))),
              ),
            ],
          ),
        ],
      ),
    ],
  );
  return MaterialApp.router(theme: AppTheme.lightTheme, routerConfig: router);
}

void main() {
  useAppFonts();

  testWidgets('on a phone a nested destination has the menu, not a back arrow', (tester) async {
    useScreen(tester, phoneScreen);
    await tester.pumpWidget(_app('/school/exams'));
    await tester.pumpAndSettle();
    expectNoOverflow(tester);
    expectActionReady(tester, find.byTooltip('Menu'), phoneScreen, label: 'the Menu button');
    expect(find.byType(BackButton), findsNothing);

    await tester.tap(find.byTooltip('Menu'));
    await tester.pumpAndSettle();
    expect(find.byType(Drawer), findsOneWidget, reason: 'the menu opens the navigation');
  });

  testWidgets('on a laptop a nested destination has neither: the side navigation is on screen', (tester) async {
    useScreen(tester, laptopScreen);
    await tester.pumpWidget(_app('/school/exams'));
    await tester.pumpAndSettle();
    expect(find.byType(SideNav), findsOneWidget);
    expect(find.byTooltip('Menu'), findsNothing);
    expect(find.byType(BackButton), findsNothing, reason: 'a back arrow to the overview reads as a sub-page');
  });

  testWidgets('a page pushed over a destination keeps its back arrow', (tester) async {
    useScreen(tester, phoneScreen);
    await tester.pumpWidget(_app('/school/homework/h1'));
    await tester.pumpAndSettle();
    expect(find.byType(BackButton), findsOneWidget);
    expect(find.byTooltip('Menu'), findsNothing);
  });
}
