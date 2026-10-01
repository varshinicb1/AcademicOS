// A new school's first steps on the principal's School page (QA S-09,
// 2026-10-01). A new principal landed on a dashboard of zeros, "1 Attendance
// not marked" (herself), and found class setup only by guessing "Invite
// people". The checklist names the five steps, each a link, ticks what the
// school's own data shows done, and goes once all are; the dashboard says no
// teacher has joined instead of counting the principal's attendance.
//
// The fake backend answers in the server's shapes and records every path
// asked for: the checklist must not fetch the calendar, a 404 for a new year.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/dashboard_card.dart';
import 'package:academicos/presentation/workspace/setup_checklist.dart';
import 'package:academicos/presentation/workspace/workspace_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

class _School implements HttpClientAdapter {
  final List<String> asked = [];
  String? name;
  bool hasYear = false;
  bool hasClasses = false;
  bool hasTerms = false;
  bool hasTeacher = false;
  bool hasTimetable = false;
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  Map<String, dynamic> get _summary => {
        'date': '2026-10-02',
        'cover': {'staff': hasTeacher ? 3 : 1, 'absent': 0, 'onLeave': 0, 'unmarked': 1, 'periodsToCover': 0,
          'covered': 0, 'uncovered': 0},
        'homework': {'set': 0, 'submissionsExpected': 0, 'submitted': 0, 'marked': 0, 'waitingToMark': 0,
          'overdueHomework': 0},
        'exams': <Object>[],
        'studentsNeedingHelp': <Object>[],
      };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    asked.add(o.path);
    final Object? answer = switch (o.path) {
      '/curriculum/school-profile' => {'name': name, 'address': null, 'affiliation': null, 'hasLogo': false},
      '/staff' => [
          {'id': 'p_1', 'name': 'Farida Khan', 'role': 'principal'},
          if (hasTeacher) {'id': 't_1', 'name': 'Suresh Rao', 'role': 'teacher'},
        ],
      '/curriculum/academic-years' => [
          if (hasYear) {'id': 'ay_1', 'schoolId': 'school_1', 'label': '2026-27', 'startDate': '2026-04-01',
            'endDate': '2027-03-31', 'status': 'draft'},
        ],
      '/curriculum/academic-years/ay_1/grades' => [if (hasClasses) {'id': 'g_10', 'academicYearId': 'ay_1', 'number': 10}],
      '/curriculum/academic-years/ay_1/terms' => [
          if (hasTerms) {'id': 'term_1', 'name': 'Term 1', 'startDate': '2026-04-01', 'endDate': '2026-09-30'},
        ],
      '/curriculum/academic-years/ay_1/timetable' => [
          if (hasTimetable) {'id': 'tt_1', 'sectionId': 's', 'dayOfWeek': 0, 'period': 1, 'subjectId': 'sci'},
        ],
      '/dashboard/summary' => _summary,
      '/notifications' => {'items': <Object>[], 'unreadCount': 0},
      _ => null,
    };
    if (answer == null) {
      return ResponseBody.fromString(jsonEncode({'detail': 'not found'}), 404, headers: _json);
    }
    return ResponseBody.fromString(jsonEncode(answer), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _School school;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('setup_checklist_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    school = _School();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = school);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Farida Khan'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('setup_checklist_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  /// The checklist on a page of its own, with every step's destination.
  Future<GoRouter> pumpChecklist(WidgetTester tester) async {
    useScreen(tester, phoneScreen);
    final router = GoRouter(initialLocation: '/school', routes: [
      GoRoute(path: '/school', builder: (_, __) => const Scaffold(body: SingleChildScrollView(child: SetupChecklistCard()))),
      for (final path in ['/admin', '/school-profile-page', '/timetable-page'])
        GoRoute(path: path, builder: (_, s) => Scaffold(body: Text('at ${s.uri}'))),
    ], redirect: (_, s) => switch (s.uri.path) {
          '/school/school-profile' => '/school-profile-page',
          '/school/timetable' => '/timetable-page',
          _ => null,
        });
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
    return router;
  }

  bool ticked(WidgetTester tester, String step) {
    final icon = tester.widget<Icon>(
        find.descendant(of: find.byKey(ValueKey('setup-step-$step')), matching: find.byType(Icon)).first);
    return icon.icon == Icons.check_circle;
  }

  testWidgets('a new school sees the five steps, none done, and the first is next', (tester) async {
    await pumpChecklist(tester);
    expect(find.byKey(const ValueKey('setup-checklist')), findsOneWidget);
    expect(find.text('0 of 5 done. Next: School profile.'), findsOneWidget);
    for (final step in ['profile', 'classes', 'calendar', 'people', 'timetable']) {
      expect(find.byKey(ValueKey('setup-step-$step')), findsOneWidget);
      expect(ticked(tester, step), isFalse, reason: step);
    }
    expect(school.asked.where((p) => p.endsWith('/calendar')), isEmpty, reason: 'a new year has none: a 404');
    expectNoOverflow(tester);
  });

  testWidgets('what the school has done is ticked, and the next step is named', (tester) async {
    school
      ..name = 'Green Valley School'
      ..hasYear = true
      ..hasClasses = true
      ..hasTeacher = true;
    await pumpChecklist(tester);
    expect(find.text('3 of 5 done. Next: Calendar and terms.'), findsOneWidget);
    expect(ticked(tester, 'profile'), isTrue);
    expect(ticked(tester, 'classes'), isTrue);
    expect(ticked(tester, 'calendar'), isFalse);
    expect(ticked(tester, 'people'), isTrue);
    expect(ticked(tester, 'timetable'), isFalse);
  });

  testWidgets('each step is a link to where it is done', (tester) async {
    final router = await pumpChecklist(tester);
    final expected = {
      'profile': '/school-profile-page',
      'classes': '/admin',
      'calendar': '/admin?tab=calendar',
      'people': '/admin',
      'timetable': '/timetable-page',
    };
    for (final MapEntry(key: step, value: location) in expected.entries) {
      await tester.tap(find.byKey(ValueKey('setup-step-$step')));
      await tester.pumpAndSettle();
      expect(find.text('at $location'), findsOneWidget, reason: step);
      router.pop();
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
      await tester.pumpAndSettle();
    }
  });

  testWidgets('a school with every step done sees no checklist', (tester) async {
    school
      ..name = 'Green Valley School'
      ..hasYear = true
      ..hasClasses = true
      ..hasTerms = true
      ..hasTeacher = true
      ..hasTimetable = true;
    await pumpChecklist(tester);
    expect(find.byKey(const ValueKey('setup-checklist')), findsNothing);
  });

  testWidgets('with no teacher yet the dashboard does not count the principal as unmarked', (tester) async {
    await pumpPage(tester, const Scaffold(body: SingleChildScrollView(child: DashboardCard())), phoneScreen);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
    expect(find.text('Attendance not marked'), findsNothing);
    expect(find.text('Teachers who have joined'), findsOneWidget);
  });

  testWidgets('once teachers have joined the attendance tiles are back', (tester) async {
    school.hasTeacher = true;
    await pumpPage(tester, const Scaffold(body: SingleChildScrollView(child: DashboardCard())), phoneScreen);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
    expect(find.text('Attendance not marked'), findsOneWidget);
    expect(find.text('Teachers who have joined'), findsNothing);
  });

  testWidgets("a new school's School page fits a phone with the checklist, the dashboard and the tiles",
      (tester) async {
    await pumpPage(tester, const WorkspacePage(), phoneScreen);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pumpAndSettle();
    expectNoOverflow(tester);
    expect(find.byKey(const ValueKey('setup-checklist')), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Question bank'), 300);
    expect(find.text('Question bank'), findsOneWidget, reason: 'the tiles are reached by scrolling');
    expectNoOverflow(tester);
  });
}
