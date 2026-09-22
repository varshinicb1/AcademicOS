// The two Task 802 silent failures whose screens also read the Hive-backed
// LocalStore, fed a failing server through the same interceptor-backed Dio
// as no_silent_failures_test.dart (test/support/fake_server.dart).
//
//  * Parental consent (Classes): the server save was fire-and-forget
//    (`.ignore()` inside an empty catch). A failed save still said "Consent
//    recorded" and turned the shield green from the on-device record, and
//    grading then refused the student with 409 "no recorded parental
//    consent". The on-device record must follow the server's, not lead it.
//  * Parent portal: every error became "No progress recorded", as if the
//    term had not started. Only the server's 403/404 (an account not linked
//    to an enrolled student) is an empty portal; a 500 or a dropped
//    connection is an error with Retry.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/consent_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/parent/pages/parent_portal_page.dart';
import 'package:academicos/presentation/settings/pages/classes_page.dart';
import 'package:academicos/presentation/shared/widgets/common_widgets.dart';

import '../support/fake_server.dart';
import '../support/real_di.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('no_silent_failures_stored_test_');
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
    await GetIt.instance.reset();
    env.registerGetIt();
  });

  // Order matters here. A Hive write the PAGE starts inside testWidgets'
  // fake-async zone (the success case's LocalStore.setConsent) resumes in
  // that zone after its real file I/O, and pumping afterwards does not drain
  // it: the next cacheBox.clear() then waits forever on Hive's lock queue
  // (measured: the parent-portal tests after it hung until the 4-minute
  // timeout; alone they pass in under a second). This is the lock
  // real_di.dart's dispose() already bounds with a timeout. So the one test
  // whose page writes to the box runs last, and the tests' own setup writes
  // go through tester.runAsync, outside the fake zone.

  group('parent portal', () {
    const yearsPath = 'GET /curriculum/academic-years';
    const progressPath = 'GET /curriculum/my-progress';
    const schedulePath = 'GET /curriculum/my-class-schedule';

    Future<void> pumpPortal(WidgetTester tester, Object failure) async {
      // Tall enough that the progress section is built, not culled below the
      // fold of the ListView.
      tester.view.physicalSize = const Size(1200, 3000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.runAsync(() async => LocalStore.instance.authUser = {
            'id': 'p1',
            'name': 'Ravi Kumar',
            'role': 'student',
            'schoolId': 'sunrise',
          });
      GetIt.instance.registerSingleton<CurriculumApi>(CurriculumApi(fakeDio(FakeServer({
        yearsPath: (200, [
          {'id': 'ay-2026', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'},
        ]),
        progressPath: failure,
        schedulePath: failure,
      }))));
      await tester.pumpWidget(const MaterialApp(home: ParentPortalPage()));
      await tester.pumpAndSettle();
    }

    for (final status in [403, 404]) {
      testWidgets('a $status (no enrolled child linked) is the "No class linked yet" empty state', (tester) async {
        await pumpPortal(tester, (status, {'detail': 'You are not enrolled in a class yet'}));

        expect(find.text('No class linked yet'), findsOneWidget);
        expect(find.textContaining('You are not enrolled in a class yet'), findsOneWidget,
            reason: "the server's sentence says why");
        expect(find.text('No progress recorded'), findsNothing);
        expect(find.byType(ErrorDisplay), findsNothing);
      });
    }

    testWidgets('a 500 is an error with Retry, not an empty term', (tester) async {
      await pumpPortal(tester, (500, null));

      expect(find.byType(ErrorDisplay), findsOneWidget);
      expect(find.textContaining('Could not load parent portal data'), findsOneWidget);
      expect(find.textContaining('HTTP 500'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
      expect(find.text('No progress recorded'), findsNothing);
      expect(find.text('No class linked yet'), findsNothing);
    });

    testWidgets('a dropped connection is an error that blames the connection', (tester) async {
      await pumpPortal(tester, DioExceptionType.connectionError);

      expect(find.byType(ErrorDisplay), findsOneWidget);
      expect(find.textContaining("Couldn't reach the server — check your connection"), findsOneWidget);
      expect(find.text('No progress recorded'), findsNothing);
      expect(find.text('No class linked yet'), findsNothing);
    });
  });

  group('parental consent (Classes)', () {
    const studentId = 'stu_asha';
    const studentName = 'Asha Nair';

    Future<FakeServer> recordConsent(WidgetTester tester, Object consentRoute) async {
      await tester.runAsync(() async => LocalStore.instance.setStudentName(studentId, studentName));
      final server = FakeServer({'POST /consent': consentRoute});
      GetIt.instance.registerSingleton<ConsentApi>(ConsentApi(fakeDio(server)));

      await tester.pumpWidget(wrapForTest(const ClassesPage()));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Parental consent required — tap to record'));
      await tester.pumpAndSettle();
      await tester.enterText(find.widgetWithText(TextFormField, 'Parent/guardian name *'), 'Meera Nair');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'How consent was obtained *'), 'Signed admission form, clause 4');
      await tester.tap(find.widgetWithText(FilledButton, 'Record consent'));
      await tester.pumpAndSettle();
      return server;
    }

    testWidgets('a failed save says it was not saved and records nothing on the device', (tester) async {
      final server = await recordConsent(tester, (500, null));

      expect(server.requests, ['POST /consent'], reason: 'the save must actually be attempted');
      expect(find.textContaining('Consent for $studentName was not saved'), findsOneWidget);
      expect(find.textContaining('HTTP 500'), findsOneWidget);
      expect(find.textContaining('Grading stays blocked'), findsOneWidget);
      expect(find.textContaining('Consent recorded'), findsNothing);
      expect(LocalStore.instance.hasConsent(studentId), isFalse,
          reason: 'a green shield the server does not agree with is what made grading refuse a '
              'student who looked consented');
      expect(find.byTooltip('Parental consent required — tap to record'), findsOneWidget);
      expect(find.byTooltip('Parental consent on file'), findsNothing);
    });

    testWidgets('a save that never got an answer blames the connection and records nothing', (tester) async {
      await recordConsent(tester, DioExceptionType.connectionError);

      expect(find.textContaining("was not saved: Couldn't reach the server — check your connection"),
          findsOneWidget);
      expect(find.textContaining('Consent recorded'), findsNothing);
      expect(LocalStore.instance.hasConsent(studentId), isFalse);
    });

    // Keep last: its page writes to the box (see the note above the groups).
    testWidgets('a saved consent says so and turns the shield green', (tester) async {
      // The control case: the success path still records on the device.
      await recordConsent(tester, (201, {
        'id': 'c1',
        'schoolId': 'sunrise',
        'studentId': studentId,
        'guardianName': 'Meera Nair',
        'method': 'Signed admission form, clause 4',
        'recordedBy': 'teacher_1',
        'recordedAt': '2026-09-22T10:00:00Z',
      }));

      expect(find.textContaining('Consent recorded for $studentName'), findsOneWidget);
      expect(find.textContaining('was not saved'), findsNothing);
      expect(LocalStore.instance.hasConsent(studentId), isTrue);
      expect(find.byTooltip('Parental consent on file'), findsOneWidget);
    });
  });
}
