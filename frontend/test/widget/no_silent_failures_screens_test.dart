// Task 802 fixes that no_swallowed_errors_test.dart only scans for: the scan
// passes as soon as serverErrorMessage appears in the handler, not when the
// message reaches the screen. These drive the real screens through a real
// Dio answered by FakeServer (test/support/fake_server.dart).
//
//  * Principal admin, Roster -> Assign a teacher: picking a grade loads its
//    subjects. A failed load used to leave an empty Subject dropdown, which
//    reads as "this class has no subjects". It must say it failed, and why.
//  * Student "My Class": every failure said "check your connection". A 403
//    or a 500 must show the server's reason; Retry only where a second try
//    can succeed (no answer, 5xx), never on a 403 the server will repeat.
//    A 404 is "Not enrolled yet" only when it is the server's not-enrolled
//    sentence, not FastAPI's bare "Not Found" for a missing route.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';
import 'package:academicos/presentation/shared/widgets/common_widgets.dart';
import 'package:academicos/presentation/student/pages/student_schedule_page.dart';

import '../support/fake_server.dart';
import '../support/real_di.dart';

const _yearsPath = 'GET /curriculum/academic-years';
const _years = [
  {'id': 'ay-2026', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'},
];

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('no_silent_failures_screens_test_');
  });

  tearDownAll(() async {
    await env.dispose();
  });

  // Setup writes happen here, outside testWidgets' fake-async zone (see the
  // Hive lock note in no_silent_failures_stored_test.dart). Neither screen
  // writes to the box itself.
  Future<void> signIn(String role) async {
    await env.cacheBox.clear();
    await GetIt.instance.reset();
    env.registerGetIt();
    LocalStore.instance.authUser = {
      'id': 'u_$role',
      'name': 'Test $role',
      'email': '$role@school.invalid',
      'role': role,
      'schoolId': 'sunrise',
    };
  }

  void tallView(WidgetTester tester) {
    tester.view.physicalSize = const Size(1600, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
  }

  group('principal admin: subjects for the chosen grade', () {
    setUp(() => signIn('principal'));

    Future<FakeServer> pickGrade(WidgetTester tester, Object subjectsRoute) async {
      tallView(tester);
      final server = FakeServer({
        _yearsPath: (200, _years),
        'GET /curriculum/academic-years/ay-2026/grades': (200, [
          {'id': 'grade_10', 'number': 10, 'section': null},
        ]),
        'GET /auth/users': (200, <Object>[]),
        'GET /auth/invites': (200, <Object>[]),
        'GET /curriculum/grades/grade_10/subjects': subjectsRoute,
      });
      final dio = fakeDio(server);
      GetIt.instance
        ..registerSingleton<CurriculumApi>(CurriculumApi(dio))
        ..registerSingleton<AuthApi>(AuthApi(dio));

      await tester.pumpWidget(wrapForTest(const PrincipalAdminPage()));
      await tester.pumpAndSettle();

      // "Assign a teacher" card: its Grade dropdown is the first on the tab
      // (the enroll card below has the second).
      await tester.tap(find.widgetWithText(DropdownButtonFormField<GradeSummary>, 'Grade').first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Grade 10').last);
      await tester.pumpAndSettle();
      return server;
    }

    testWidgets('a 500 says the subjects did not load, and why', (tester) async {
      final server = await pickGrade(tester, (500, null));

      expect(server.requests, contains('GET /curriculum/grades/grade_10/subjects'),
          reason: 'picking a grade must actually ask for its subjects');
      expect(find.byType(SnackBar), findsOneWidget);
      expect(find.textContaining('Could not load subjects'), findsOneWidget);
      expect(find.textContaining('HTTP 500'), findsOneWidget);
    });

    testWidgets('a dropped connection blames the connection', (tester) async {
      await pickGrade(tester, DioExceptionType.connectionError);

      expect(find.text("Could not load subjects: Couldn't reach the server — check your connection"),
          findsOneWidget);
    });

    testWidgets('a subject list that did load shows no error', (tester) async {
      // The control case: the snackbar above comes from the failure, not
      // from picking a grade.
      await pickGrade(tester, (200, [
        {'id': 'sub_sci', 'name': 'Science'},
      ]));

      expect(find.byType(SnackBar), findsNothing);
      await tester.tap(find.widgetWithText(DropdownButtonFormField<SubjectSummary>, 'Subject'));
      await tester.pumpAndSettle();
      expect(find.text('Science'), findsWidgets);
    });
  });

  group('student My Class', () {
    setUp(() => signIn('student'));

    Future<FakeServer> pumpSchedule(WidgetTester tester, Object failure) async {
      tallView(tester);
      final server = FakeServer({
        _yearsPath: (200, _years),
        'GET /curriculum/my-progress': failure,
        'GET /curriculum/my-class-schedule': failure,
      });
      GetIt.instance.registerSingleton<CurriculumApi>(CurriculumApi(fakeDio(server)));

      await tester.pumpWidget(const MaterialApp(home: StudentSchedulePage()));
      await tester.pumpAndSettle();
      return server;
    }

    testWidgets("a 403 shows the server's reason and no Retry", (tester) async {
      const detail = 'this endpoint is for students only';
      await pumpSchedule(tester, (403, {'detail': detail}));

      expect(find.byType(ErrorDisplay), findsOneWidget);
      expect(find.text('Could not load your class: $detail'), findsOneWidget);
      expect(find.text('Retry'), findsNothing, reason: 'the server will refuse the same request again');
      expect(find.textContaining('check your connection'), findsNothing);
      expect(find.text('Not enrolled yet'), findsNothing);
    });

    testWidgets('a 500 names the server fault and offers Retry', (tester) async {
      await pumpSchedule(tester, (500, null));

      expect(find.textContaining('HTTP 500'), findsOneWidget);
      expect(find.textContaining('check your connection'), findsNothing);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('a connection error blames the connection and offers Retry that re-sends', (tester) async {
      final server = await pumpSchedule(tester, DioExceptionType.connectionError);

      expect(find.textContaining("Couldn't reach the server — check your connection"), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);

      // The connection comes back. (Answered with a success on purpose: a
      // retry that fails again completes before FutureBuilder's next frame
      // subscribes to it, which the test zone reports as unhandled.)
      server.routes
        ..['GET /curriculum/my-progress'] = (200, {'academicYearId': 'ay-2026', 'asOfDate': '2026-09-22'})
        ..['GET /curriculum/my-class-schedule'] = (200, <Object>[]);
      final before = server.requests.where((r) => r == _yearsPath).length;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(server.requests.where((r) => r == _yearsPath).length, before + 1,
          reason: 'Retry must send the request again');
      expect(find.byType(ErrorDisplay), findsNothing, reason: 'a retry that succeeded shows the class');
    });

    testWidgets("the server's not-enrolled 404 is the Not enrolled yet state", (tester) async {
      await pumpSchedule(tester, (404, {
        'detail': 'you are not enrolled in a class yet -- ask your principal to enroll you',
      }));

      expect(find.text('Not enrolled yet'), findsOneWidget);
      expect(find.byType(ErrorDisplay), findsNothing);
    });

    testWidgets('a bare "Not Found" 404 is an error, not "Not enrolled yet"', (tester) async {
      await pumpSchedule(tester, (404, {'detail': 'Not Found'}));

      expect(find.text('Not enrolled yet'), findsNothing);
      expect(find.text('Could not load your class: Not Found'), findsOneWidget);
    });
  });
}
