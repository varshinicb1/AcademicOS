// The principal's side navigation listed eighteen destinations and the first
// school to use it found it confusing (2026-10-01). It now shows eight core
// pages, with the rest folded under More and Setup; this pins that the folds
// work on a laptop, in the icon rail and in the phone drawer, that the device
// remembers them, and that no page became unreachable.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/shared/device_memory.dart';
import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

const _principalCore = ['Overview', 'Papers', 'Exams', 'Timetable', 'Lesson plans', 'Attendance and cover',
  'Term report', 'Inbox'];
const _principalMore = ['Paper reviews', 'School insights', 'Periods owed', 'Homework', 'Class progress',
  'Question bank'];
const _principalSetup = ['Invite people', 'Staff and access', 'School profile', 'Import and export', 'API keys',
  'Calendar and terms'];

void _signIn(String role) => LocalStore.instance.authUser = {
      'id': 'user_$role', 'schoolId': 'school_a', 'name': 'Test $role', 'email': '$role@example.com', 'role': role,
    };

/// The shell around stand-in pages for every principal and teacher
/// destination.
Widget _app(String initial) {
  Widget page(String path) => Builder(
        builder: (context) => Scaffold(
          appBar: destinationAppBar(context, title: Text('Page $path')),
          body: Text('Body of $path'),
        ),
      );
  const paths = ['/school', '/assessment', '/school/exams', '/school/timetable', '/school/lesson-plans',
    '/school/cover', '/school/term-report', '/school/inbox', '/school/reviews', '/analytics/school',
    '/school/periods-owed', '/school/homework', '/school/class-progress', '/school/question-bank', '/admin',
    '/school/grants', '/school/school-profile', '/school/import', '/school/api-keys', '/settings', '/home',
    '/school/my-day', '/school/week', '/evaluation', '/questions', '/school/my-exams', '/school/today',
    '/school/my-homework', '/school/my-learning'];
  final router = GoRouter(initialLocation: initial, routes: [
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        for (final p in paths)
          GoRoute(path: p, builder: (context, state) => page(state.uri.toString())),
      ],
    ),
  ]);
  return MaterialApp.router(theme: AppTheme.lightTheme, routerConfig: router);
}

/// A laptop tall enough for the whole side navigation, groups open: the
/// list is lazy, so a row below the fold would not be built at all.
const _tallLaptop = (size: Size(1280, 1300), textScale: 1.0);

Finder _inNav(String label) => find.descendant(of: find.byType(SideNav), matching: find.text(label));

bool _selected(WidgetTester tester, String label) =>
    tester.widget<ListTile>(find.ancestor(of: _inNav(label), matching: find.byType(ListTile)).first).selected;

void main() {
  late Directory tmp;
  useAppFonts();

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('grouped_menu_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    // Not awaited: a write made inside the previous test's fake clock can sit
    // in the box's queue forever, and awaiting behind it hangs the run. The
    // box's in-memory view changes at once, which is all a test reads.
    final box = Hive.box('academicos_cache');
    box.deleteAll(box.keys.where((k) => '$k'.startsWith('nav_group_open:')).toList());
    DeviceMemory.resetMemory();
  });

  tearDown(() => LocalStore.instance.clearAuth());

  tearDownAll(() async {
    // A widget test's Hive writes can be left inside its fake clock, and
    // Hive.close() then waits on them forever (owner_switcher_test does the same).
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('grouped_menu_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  testWidgets('a principal on a laptop sees the eight core pages and two folded groups', (tester) async {
    useScreen(tester, _tallLaptop);
    _signIn('principal');
    await tester.pumpWidget(_app('/school'));
    await tester.pumpAndSettle();
    expectNoOverflow(tester);

    for (final label in _principalCore) {
      expect(_inNav(label), findsOneWidget, reason: '$label is always on show');
    }
    for (final label in [..._principalMore, ..._principalSetup]) {
      expect(_inNav(label), findsNothing, reason: '$label is folded away');
    }
    expect(find.byKey(const ValueKey('nav-group-More')), findsOneWidget);
    expect(find.byKey(const ValueKey('nav-group-Setup')), findsOneWidget);
    expect(_inNav('Settings'), findsOneWidget);
  });

  testWidgets('opening a group lists its pages, and the device remembers it open', (tester) async {
    useScreen(tester, _tallLaptop);
    _signIn('principal');
    await tester.pumpWidget(_app('/school'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('nav-group-More')));
    await tester.pumpAndSettle();
    for (final label in _principalMore) {
      expect(_inNav(label), findsOneWidget, reason: '$label shows once More is open');
    }
    expect(_inNav('Invite people'), findsNothing, reason: 'Setup stays folded');
    expect(Hive.box('academicos_cache').get('nav_group_open:More'), isTrue, reason: 'kept in the local store');

    // A fresh start (a reload) keeps More open and Setup folded.
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(_app('/school'));
    await tester.pumpAndSettle();
    expect(_inNav('Paper reviews'), findsOneWidget);
    expect(_inNav('Invite people'), findsNothing);

    // Folding it again is remembered too.
    await tester.tap(find.byKey(const ValueKey('nav-group-More')));
    await tester.pumpAndSettle();
    expect(_inNav('Paper reviews'), findsNothing);
    expect(Hive.box('academicos_cache').get('nav_group_open:More'), isFalse);
  });

  testWidgets('a page inside a folded group opens it, selected', (tester) async {
    useScreen(tester, _tallLaptop);
    _signIn('principal');
    await tester.pumpWidget(_app('/school/periods-owed'));
    await tester.pumpAndSettle();
    expect(_inNav('Periods owed'), findsOneWidget, reason: 'the page on screen is never hidden in a fold');
    expect(_selected(tester, 'Periods owed'), isTrue);
    expect(_inNav('Invite people'), findsNothing, reason: 'other groups stay as they were');

    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(_app('/admin?tab=calendar-setup'));
    await tester.pumpAndSettle();
    expect(_selected(tester, 'Calendar and terms'), isTrue);
    expect(_selected(tester, 'Invite people'), isFalse);
  });

  testWidgets('every principal page is reachable from the phone drawer', (tester) async {
    useScreen(tester, phoneScreen);
    _signIn('principal');
    await tester.pumpWidget(_app('/school'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Menu'));
    await tester.pumpAndSettle();
    expectNoOverflow(tester, where: ' in the drawer');

    final list = find.descendant(of: find.byType(Drawer), matching: find.byType(Scrollable)).first;
    for (final group in ['More', 'Setup']) {
      final header = find.byKey(ValueKey('nav-group-$group'));
      await tester.scrollUntilVisible(header, 100, scrollable: list);
      await tester.pumpAndSettle(); // scrollUntilVisible's last jump is laid out on the next frame
      expect(tester.getRect(header).height, greaterThanOrEqualTo(minTapTarget), reason: '$group is thumb-sized');
      await tester.tap(header);
      await tester.pumpAndSettle();
    }
    // Back to the top, then down through every destination in order.
    await tester.drag(list, const Offset(0, 3000));
    await tester.pumpAndSettle();
    for (final label in [..._principalCore, ..._principalMore, ..._principalSetup]) {
      final tile = find.widgetWithText(ListTile, label);
      await tester.scrollUntilVisible(tile, 100, scrollable: list);
      await tester.pumpAndSettle();
      expect(tile, findsOneWidget, reason: '$label must be reachable on a phone');
    }
    await tester.ensureVisible(find.widgetWithText(ListTile, 'Calendar and terms'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ListTile, 'Calendar and terms'));
    await tester.pumpAndSettle();
    expect(find.text('Body of /admin?tab=calendar-setup'), findsOneWidget);
  });

  testWidgets('in the icon rail a group is a named chevron', (tester) async {
    useScreen(tester, (size: const Size(900, 800), textScale: 1.0));
    _signIn('principal');
    await tester.pumpWidget(_app('/school'));
    await tester.pumpAndSettle();
    expectNoOverflow(tester);
    expect(find.byTooltip('Paper reviews'), findsNothing);
    await tester.tap(find.byTooltip('Show More'));
    await tester.pumpAndSettle();
    expect(find.byTooltip('Paper reviews'), findsOneWidget);
    expect(find.byTooltip('Hide More'), findsOneWidget);
  });

  testWidgets('a teacher has eight core pages and a folded More; a student has no folds', (tester) async {
    useScreen(tester, _tallLaptop);
    _signIn('teacher');
    await tester.pumpWidget(_app('/home'));
    await tester.pumpAndSettle();
    for (final label in ['Today', 'My day', 'My week', 'Papers', 'Homework', 'Mark answer sheets', 'Class progress',
      'Inbox']) {
      expect(_inNav(label), findsOneWidget, reason: '$label is a teacher core page');
    }
    expect(_inNav('Question bank'), findsNothing);
    await tester.tap(find.byKey(const ValueKey('nav-group-More')));
    await tester.pumpAndSettle();
    for (final label in ['Question bank', 'Paper reviews', 'Exam duties']) {
      expect(_inNav(label), findsOneWidget);
    }

    await tester.pumpWidget(const SizedBox());
    LocalStore.instance.clearAuth();
    _signIn('student');
    await tester.pumpWidget(_app('/school/today'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('nav-group-More')), findsNothing);
    for (final label in ['Today', 'My week', 'Homework', 'Progress', 'Exams', 'Inbox']) {
      expect(_inNav(label), findsOneWidget);
    }
  });
}
