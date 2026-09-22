// Task 801: the principal's console at phone, tablet and laptop widths --
// the Roster tab (inviting teachers is how anyone joins a school) and the
// Coverage & Pace dashboard, fed the payload GET /curriculum/reporting/coverage
// really returns (test/fixtures/coverage_report.json, drift-checked by
// tests/test_curriculum_coverage_fixture.py). On a phone the dashboard is for
// reading and the one action on it, Reschedule on an overdue lesson, must
// still be reachable and hit.
//
// Same technique as principal_coverage_tab_test.dart: a real Dio whose
// interceptor answers each path with the backend's response shape.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import 'responsive_harness.dart';

final _coverage = jsonDecode(File('test/fixtures/coverage_report.json').readAsStringSync());

Map<String, Object?> _delayedLesson(String id, String date, int days, String chapter, String subtopic) => {
      'lessonId': id,
      'scheduledDate': date,
      'daysOverdue': days,
      'gradeNumber': 7,
      'subjectName': 'Mathematics',
      'chapterName': chapter,
      'topicName': '$chapter basics',
      'subtopicName': subtopic,
      'teacherId': 'teacher_1',
      'teacherName': 'Tara Teacher',
    };

/// DelayedTopicsReportResponse (curriculum/schemas.py) for the fixture's
/// school: its two overdue Mathematics lessons.
final _delayed = {
  'schoolId': 'school_1',
  'academicYearId': 'academicYear_1',
  'asOfDate': '2026-09-14',
  'delayedCount': 2,
  'delayedLessons': [
    _delayedLesson('lesson_overdue_integers', '2026-09-03', 11, 'Integers', 'Integers part 3'),
    _delayedLesson('lesson_overdue_fractions', '2026-09-10', 4, 'Fractions', 'Fractions part 2'),
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
    } else if (path == '/auth/invites') {
      body = [
        {
          'code': 'open-code-1234567890ab', 'role': 'teacher', 'email': 'new.science.teacher@school.example',
          'expiresAt': '2026-10-06T00:00:00+00:00', 'createdAt': '2026-09-22T00:00:00+00:00',
          'createdBy': 'u_principal', 'status': 'open', 'usedBy': null, 'usedAt': null, 'revokedAt': null,
        },
      ];
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

Finder _button(String label) =>
    find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('responsive_principal_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });
  tearDownAll(() async => Hive.close());

  setUp(() async {
    // Awaited: an unawaited clear() lands after the writes below and wipes them.
    await LocalStore.instance.box.clear();
    LocalStore.instance.authUser = {
      'id': 'u_principal',
      'schoolId': 'school_1',
      'name': 'Principal',
      'email': 'principal@school.invalid',
      'role': 'principal',
    };
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(_Backend());
    GetIt.I
      ..registerSingleton<CurriculumApi>(CurriculumApi(dio))
      ..registerSingleton<AuthApi>(AuthApi(dio));
  });
  tearDown(() => GetIt.I.reset());

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('the Roster tab fits and Create invite is ready at $name', (tester) async {
      useScreen(tester, size);
      await tester.pumpWidget(const MaterialApp(home: PrincipalAdminPage()));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' on the Roster tab');
      expect(find.textContaining('open-code-1234567890ab'), findsOneWidget);
      await scrollToAndExpectReady(tester, _button('Create invite'), size, label: 'Create invite');
      await scrollToAndExpectReady(tester, _button('Withdraw'), size, label: 'Withdraw');
      expectNoOverflow(tester, where: ' after scrolling the Roster tab');
    });

    testWidgets('the Coverage & Pace dashboard fits and Reschedule is reachable at $name', (tester) async {
      useScreen(tester, size);
      await tester.pumpWidget(const MaterialApp(home: PrincipalAdminPage()));
      await tester.pumpAndSettle();
      // The tab row scrolls sideways on a phone; the tab must still be hit.
      final tab = find.text('Coverage & Pace');
      await tester.ensureVisible(tab);
      await tester.pumpAndSettle();
      expectActionReady(tester, find.ancestor(of: tab, matching: find.byType(Tab)), size,
          label: 'the Coverage & Pace tab');
      await tester.tap(tab);
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' on the Coverage & Pace tab');
      expect(find.text('33.3%'), findsOneWidget);
      expect(find.text('22.2%'), findsOneWidget);
      expect(find.textContaining('Grade 7 · Mathematics'), findsOneWidget);

      // A subject opened to its chapters.
      await tester.tap(find.textContaining('Grade 7 · Mathematics'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' with a subject opened');

      // The delayed lessons are below the subject cards; the list builds them
      // lazily, so scroll the dashboard itself rather than the tab strip.
      final dashboard = find.descendant(of: find.byType(RefreshIndicator), matching: find.byType(Scrollable)).first;
      await scrollUntilPresent(tester, find.widgetWithText(TextButton, 'Reschedule'), dashboard);
      await scrollToAndExpectReady(tester, find.widgetWithText(TextButton, 'Reschedule').first, size,
          label: 'Reschedule on an overdue lesson');
      expectNoOverflow(tester, where: ' at the delayed lessons');
    });
  }
}
