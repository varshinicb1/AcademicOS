// Task 801: the app shell at phone, tablet and laptop widths. Every flow
// below lives inside MainShell, so if the navigation itself does not fit, no
// flow does. Nine destinations are too many for a bottom bar (see
// shell.dart), so below 800 px the rail collapses into a drawer opened from
// the page's own AppBar; at and above 800 px the rail is on screen.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/shared/widgets/shell.dart';

import 'responsive_harness.dart';

/// The shell around stand-in pages: this test is about the navigation, not
/// about what any one screen shows.
Widget _shellApp() {
  Widget page(String title) => Builder(
        builder: (context) => Scaffold(
          appBar: AppBar(leading: shellLeading(context), title: Text(title)),
          body: Center(child: Text('$title body')),
        ),
      );
  final router = GoRouter(
    initialLocation: '/home',
    routes: [
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          for (final (path, title) in const [
            ('/home', 'Today'),
            ('/syllabus', 'Syllabus'),
            ('/assessment', 'Assessments'),
            ('/planner/daily', 'Planner'),
            ('/questions', 'Questions'),
            ('/evaluation', 'Evaluate'),
            ('/analytics/mastery', 'Mastery'),
            ('/analytics/gaps', 'Teacher'),
            ('/analytics/school', 'Principal'),
            ('/school', 'School'),
            ('/settings', 'Settings'),
          ])
            GoRoute(path: path, builder: (context, state) => page(title)),
        ],
      ),
    ],
  );
  return MaterialApp.router(theme: AppTheme.lightTheme, routerConfig: router);
}

void main() {
  useAppFonts();

  testWidgets('on a phone the rail is a drawer, opened from the page and big enough to tap', (tester) async {
    useScreen(tester, phoneScreen);
    await tester.pumpWidget(_shellApp());
    await tester.pumpAndSettle();
    expectNoOverflow(tester);

    expect(find.byType(SideNav), findsNothing, reason: 'a side navigation would eat a phone screen');
    final menu = find.byTooltip('Menu');
    expectActionReady(tester, menu, phoneScreen, label: 'the Menu button');

    await tester.tap(menu);
    await tester.pumpAndSettle();
    expectNoOverflow(tester, where: ' in the drawer');
    for (final destination in ['Today', 'Syllabus', 'Papers', 'Planner', 'Question bank', 'Evaluate',
      'Mastery', 'Class gaps', 'School insights', 'School', 'Settings']) {
      final tile = find.widgetWithText(ListTile, destination);
      expect(tile, findsOneWidget, reason: '$destination must be reachable on a phone');
      final r = tester.getRect(tile);
      expect(r.height >= minTapTarget, isTrue, reason: '$destination is only ${r.height} px tall');
    }

    await tester.tap(find.widgetWithText(ListTile, 'Papers'));
    await tester.pumpAndSettle();
    expect(find.text('Assessments body'), findsOneWidget);
    expectNoOverflow(tester, where: ' after navigating');
  });

  testWidgets('in a desktop-UA browser at phone width the Menu button is still 48 px', (tester) async {
    // A phone browser reports android/iOS and gets the standard density the
    // test above runs at; a desktop browser narrowed to 375 px -- how this
    // task's screenshots were taken -- reports windows and gets `compact`,
    // which shrinks every button's minimumSize by 8 px. Only shellLeading's
    // own visualDensity keeps the one way into the navigation thumb-sized
    // there (review of 2026-09-23).
    await withDesktopDensity(() async {
      useScreen(tester, phoneScreen);
      await tester.pumpWidget(_shellApp());
      await tester.pumpAndSettle();
      expectNoOverflow(tester);
      expectActionReady(tester, find.byTooltip('Menu'), phoneScreen, label: 'the Menu button on a desktop density');
    });
  });

  testWidgets('a tablet keeps the drawer: 768 px is still narrower than the rail wants', (tester) async {
    useScreen(tester, tabletScreen);
    await tester.pumpWidget(_shellApp());
    await tester.pumpAndSettle();
    expectNoOverflow(tester);
    expectActionReady(tester, find.byTooltip('Menu'), tabletScreen, label: 'the Menu button');
    expect(find.byType(SideNav), findsNothing);
  });

  testWidgets('a laptop shows the side navigation with every destination and Settings', (tester) async {
    useScreen(tester, laptopScreen);
    await tester.pumpWidget(_shellApp());
    await tester.pumpAndSettle();
    expectNoOverflow(tester);

    expect(find.byType(SideNav), findsOneWidget);
    expect(find.byTooltip('Menu'), findsNothing, reason: 'no hamburger next to a visible side navigation');
    for (final destination in ['Today', 'Syllabus', 'Papers', 'Planner', 'Question bank', 'Evaluate',
      'Mastery', 'Class gaps', 'School insights', 'School', 'Settings']) {
      expect(find.descendant(of: find.byType(SideNav), matching: find.text(destination)), findsOneWidget);
    }
    expectActionReady(tester, find.widgetWithText(ListTile, 'Settings'), laptopScreen,
        label: 'Settings in the side navigation');
  });

  testWidgets('a screen reader finds every side navigation item on a laptop (QA P-28, S-22)', (tester) async {
    // Each page route in the shell's navigator lays a modal barrier that
    // blocks the semantics painted before it in its container: the sidebar
    // vanished for a screen reader on every desktop page.
    final semantics = tester.ensureSemantics();
    useScreen(tester, laptopScreen);
    await tester.pumpWidget(_shellApp());
    await tester.pumpAndSettle();
    for (final destination in ['Today', 'Papers', 'Question bank', 'School', 'Settings']) {
      expect(find.bySemanticsLabel(destination), findsWidgets, reason: '$destination is announced');
    }
    final papers = tester.getSemantics(find.descendant(of: find.byType(SideNav), matching: find.text('Papers')));
    expect(papers.getSemanticsData().flagsCollection.isButton, isTrue, reason: 'announced as something to press');
    semantics.dispose();
  });

  testWidgets('between the phone breakpoint and 1000 px the side navigation is icons with names', (tester) async {
    useScreen(tester, (size: const Size(900, 700), textScale: 1.0));
    await tester.pumpWidget(_shellApp());
    await tester.pumpAndSettle();
    expectNoOverflow(tester);
    expect(find.byType(SideNav), findsOneWidget);
    for (final destination in ['Today', 'Papers', 'Question bank', 'Settings']) {
      expect(find.byTooltip(destination), findsOneWidget, reason: '$destination has an accessible name');
    }
  });
}
