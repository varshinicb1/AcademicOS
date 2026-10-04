// A brand-new school opened Term report, Exams > New exam, Timetable or Lesson plans and met a red
// "Error" with the server's sentence ("no academic year covers today; ...", "no academic year contains
// the exam's start date") and a Retry that could never work (school's screenshots, 2026-10-01; still
// so on 5d9022d, 2026-10-04). Those pages now say the school is not set up yet, and give the principal
// the way to the setup wizard; the New exam dialog offers only the year's days and classes.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/shared/widgets/common_widgets.dart';
import 'package:academicos/presentation/workspace/exams_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _School implements HttpClientAdapter {
  bool hasYear = false;
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    final Object? answer = switch (o.path) {
      '/exams' => <Object>[],
      '/curriculum/academic-years' => [
          if (hasYear) {'id': 'ay_1', 'schoolId': 'school_1', 'label': '2026-27', 'startDate': '2026-04-01',
            'endDate': '2027-03-31', 'status': 'draft'},
        ],
      '/curriculum/academic-years/ay_1/sections' => [
          for (final (id, g) in [('s6a', 6), ('s6b', 6), ('s7a', 7)])
            {'id': id, 'gradeId': 'g$g', 'gradeNumber': g, 'name': 'A', 'studentCount': 0},
        ],
      _ => null,
    };
    if (answer == null) return ResponseBody.fromString(jsonEncode({'detail': 'not found'}), 404, headers: _json);
    return ResponseBody.fromString(jsonEncode(answer), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _School school;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('school_not_set_up_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    school = _School();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = school);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Meera Iyer'};
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
      print('school_not_set_up_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pump(WidgetTester tester, Widget page) async {
    final router = GoRouter(initialLocation: '/page', routes: [
      GoRoute(path: '/page', builder: (_, __) => page),
      GoRoute(path: '/school/setup', builder: (_, __) => const Scaffold(body: Text('the setup wizard'))),
    ]);
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pumpAndSettle();
  }

  const termReport = "no academic year covers today; set up this year's classes on the School Admin console (/admin)";

  test('the sentences that mean "not set up" are told apart from real failures', () {
    expect(isSchoolNotSetUp(termReport), isTrue);
    expect(isSchoolNotSetUp("no academic year contains the exam's start date"), isTrue);
    expect(isSchoolNotSetUp('Your school has no academic year set up yet.'), isTrue);
    expect(isSchoolNotSetUp('today is in no term: choose one (termId), or declare the school\'s terms'), isTrue);
    expect(isSchoolNotSetUp('Something went wrong (500).'), isFalse);
    expect(isSchoolNotSetUp('that section is not in this academic year'), isFalse);
  });

  testWidgets('the principal is shown the next step, not an error, and it opens the wizard', (tester) async {
    await pump(tester, const Scaffold(body: ErrorDisplay(message: termReport)));
    expect(find.text('Error'), findsNothing);
    expect(find.text("Your school isn't set up yet"), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('school-not-set-up-action')));
    await tester.pumpAndSettle();
    expect(find.text('the setup wizard'), findsOneWidget);
  });

  testWidgets('anyone else is told to ask the principal, with nothing to press', (tester) async {
    LocalStore.instance.authUser = {'id': 't_1', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Suresh'};
    await pump(tester, const Scaffold(body: ErrorDisplay(message: termReport)));
    expect(find.textContaining('Ask your principal'), findsOneWidget);
    expect(find.byKey(const ValueKey('school-not-set-up-action')), findsNothing);
  });

  testWidgets('a real failure is still an error', (tester) async {
    await pump(tester, const Scaffold(body: ErrorDisplay(message: 'Something went wrong (500).')));
    expect(find.text('Error'), findsOneWidget);
    expect(find.byKey(const ValueKey('school-not-set-up')), findsNothing);
  });

  testWidgets('New exam in a school with no year says so instead of failing on Create', (tester) async {
    await pump(tester, const ExamsPage());
    await tester.tap(find.text('New exam'));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pumpAndSettle();
    expect(find.text("Your school isn't set up yet"), findsOneWidget);
    expect(find.textContaining('An exam goes inside the school year'), findsOneWidget);
    expect(find.byKey(const ValueKey('exam-create')), findsNothing);
    // The way to the wizard closes the dialog first.
    await tester.tap(find.byKey(const ValueKey('school-not-set-up-action')));
    await tester.pumpAndSettle();
    expect(find.text('the setup wizard'), findsOneWidget);
  });

  testWidgets("New exam offers the year's classes and days only", (tester) async {
    school.hasYear = true;
    await pump(tester, ExamsPage(today: DateTime(2026, 10, 4)));
    await tester.tap(find.text('New exam'));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('exam-class-6')), findsOneWidget);
    expect(find.byKey(const ValueKey('exam-class-7')), findsOneWidget);
    expect(find.byKey(const ValueKey('exam-class-12')), findsNothing, reason: 'the school has no class 12');
    expect(find.text('Within 2026-27: 2026-04-01 to 2027-03-31'), findsOneWidget);
  });
}
