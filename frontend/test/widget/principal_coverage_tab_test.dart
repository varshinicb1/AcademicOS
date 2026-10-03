// Widget test for the principal admin's Coverage & Pace tab, fed the payload
// GET /curriculum/reporting/coverage really returns
// (test/fixtures/coverage_report.json, captured and drift-checked by
// tests/test_curriculum_coverage_fixture.py).
//
// The 2026-09-21 product audit found this screen showing '0.0% covered' and
// '0/0 lessons' for every subject, no grade on any row, and a headline
// 'Overall Pace %' of 100.0% for a school 89 lessons behind (the client
// recomputed pace from counts it never parsed, falling back to 100 at 0).
// Its 'Reschedule' button on a delayed lesson called animateTo(2) -- the
// Coverage tab itself -- because Reschedule sits at index 4.
//
// Same technique as principal_calendar_setup_load_test.dart: a real Dio whose
// interceptor answers each path with the backend's response shape, no
// network; LocalStore is the real Hive-backed store (RealTestEnv).
import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import '../support/real_di.dart';

final _coverage = jsonDecode(File('test/fixtures/coverage_report.json').readAsStringSync());

/// DelayedTopicsReportResponse (src/academicos/curriculum/schemas.py) for the
/// fixture's school: its two overdue Mathematics lessons.
final _delayed = {
  'schoolId': 'school_1',
  'academicYearId': 'academicYear_1',
  'asOfDate': '2026-09-14',
  'delayedCount': 2,
  'delayedLessons': [
    {
      'lessonId': 'lesson_overdue_integers',
      'scheduledDate': '2026-09-03',
      'daysOverdue': 11,
      'gradeNumber': 7,
      'subjectName': 'Mathematics',
      'chapterName': 'Integers',
      'topicName': 'Integers basics',
      'subtopicName': 'Integers part 3',
      'teacherId': 'teacher_1',
      'teacherName': 'Tara Teacher',
    },
    {
      'lessonId': 'lesson_overdue_fractions',
      'scheduledDate': '2026-09-10',
      'daysOverdue': 4,
      'gradeNumber': 7,
      'subjectName': 'Mathematics',
      'chapterName': 'Fractions',
      'topicName': 'Fractions basics',
      'subtopicName': 'Fractions part 2',
      'teacherId': 'teacher_1',
      'teacherName': 'Tara Teacher',
    },
  ],
};

class _Backend extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final path = options.path;
    Object? body;
    var status = 200;
    if (path == '/curriculum/academic-years') {
      body = [
        {'id': 'academicYear_1', 'label': '2026-27', 'startDate': '2026-06-01', 'endDate': '2027-03-31'},
      ];
    } else if (path.endsWith('/grades')) {
      body = [
        {'id': 'grade_7', 'number': 7, 'section': null},
        {'id': 'grade_10', 'number': 10, 'section': null},
      ];
    } else if (path == '/auth/users') {
      body = <Object>[];
    } else if (path == '/curriculum/reporting/coverage') {
      body = _coverage;
    } else if (path == '/curriculum/reporting/delayed-topics') {
      body = _delayed;
    } else {
      status = 404;
      body = {'detail': 'not found'};
    }
    final response = Response(requestOptions: options, statusCode: status, data: body);
    if (status < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(statusCode: status, requestOptions: options, response: response));
    }
  }
}

Future<void> _openCoverageTab(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1600, 2400);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(wrapForTest(const PrincipalAdminPage()));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Coverage & Pace'));
  await tester.pumpAndSettle();
}

String _selectedTabLabel(WidgetTester tester) {
  final bar = tester.widget<TabBar>(find.byType(TabBar));
  return (bar.tabs[bar.controller!.index] as Tab).text!;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('principal_coverage_tab_test_');
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(_Backend());
    GetIt.instance
      ..registerSingleton<CurriculumApi>(CurriculumApi(dio))
      ..registerSingleton<AuthApi>(AuthApi(dio));
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
    LocalStore.instance.authUser = {
      'id': 'u_principal',
      'schoolId': 'school_1',
      'name': 'Principal',
      'email': 'principal@school.invalid',
      'role': 'principal',
    };
  });

  testWidgets("the headline shows the backend's pace for a school behind, not 100%", (tester) async {
    await _openCoverageTab(tester);

    expect(find.text('33.3%'), findsOneWidget, reason: "overallPacePct 33.33: 2 of 6 due lessons taught");
    expect(find.text('100.0%'), findsNothing, reason: 'a school 4 lessons behind is not on 100% pace');
    expect(find.text('2 of 6 due lessons taught'), findsOneWidget,
        reason: "completedToDate/plannedToDate as the backend counted them, not a sum of unparsed zeros");
    expect(find.text('22.2%'), findsOneWidget, reason: 'overallCoveragePct 22.22');
    expect(find.text('2 of 9 lessons taught'), findsOneWidget);
  });

  testWidgets('each subject row shows its grade and real coverage, lessons and pace', (tester) async {
    await _openCoverageTab(tester);

    expect(find.textContaining('Grade 7 · Mathematics'), findsOneWidget);
    expect(find.textContaining('Grade 10 · Science'), findsOneWidget);
    expect(find.text('28.6% covered'), findsOneWidget);
    expect(find.text('0.0% covered'), findsOneWidget, reason: 'Science really has taught nothing yet');
    expect(find.textContaining('2/7 lessons taught'), findsOneWidget);
    expect(find.textContaining('2 of 6 due to date'), findsOneWidget);
    expect(find.textContaining('pace 33.3%'), findsOneWidget);
    expect(find.textContaining('0/0 lessons'), findsNothing);
  });

  testWidgets('a subject with nothing due yet shows no pace figure, never 100%', (tester) async {
    await _openCoverageTab(tester);

    expect(find.textContaining('no lessons due yet'), findsOneWidget,
        reason: 'Science has plannedToDate 0; the backend sends pacePct 100.0 for it');
    expect(find.textContaining('pace 100'), findsNothing);
  });

  testWidgets('Reschedule on a delayed lesson lands on the Reschedule tab with that lesson', (tester) async {
    await _openCoverageTab(tester);
    expect(_selectedTabLabel(tester), 'Coverage & Pace');

    final button = find.widgetWithText(TextButton, 'Reschedule').first;
    await tester.ensureVisible(button);
    await tester.pumpAndSettle();
    await tester.tap(button);
    await tester.pumpAndSettle();

    expect(_selectedTabLabel(tester), 'Reschedule',
        reason: 'animateTo(2) was the Coverage tab itself; the button did nothing visible');
    final lessonField = find.byWidgetPredicate(
        (w) => w is TextField && w.controller?.text == 'lesson_overdue_integers');
    await tester.scrollUntilVisible(lessonField, 300,
        scrollable: find.descendant(of: find.byType(ListView), matching: find.byType(Scrollable)).last);
    expect(lessonField, findsOneWidget, reason: 'the lesson to move is carried into the adjust form');
  });

  testWidgets("PUSH's date is picked from a calendar, never typed (D116)", (tester) async {
    await _openCoverageTab(tester);
    await tester.tap(find.widgetWithText(Tab, 'Reschedule'));
    await tester.pumpAndSettle();

    final field = find.byKey(const ValueKey('push-from-date'));
    await tester.ensureVisible(field);
    await tester.pumpAndSettle();
    TextField input() => tester.widget<TextField>(find.descendant(of: field, matching: find.byType(TextField)));
    expect(input().readOnly, isTrue, reason: '"2026-10-5" typed by hand was pushed from November');

    await tester.tap(field);
    await tester.pumpAndSettle();
    expect(find.byType(DatePickerDialog), findsOneWidget);
    await tester.tap(find.text('15'));
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    expect(input().controller!.text, matches(RegExp(r'^\d{4}-\d{2}-15$')));
  });
}
