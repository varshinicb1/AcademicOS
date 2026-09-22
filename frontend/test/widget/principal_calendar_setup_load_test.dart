// Widget test for the principal admin's Calendar & Setup tab when the saved
// calendar loads but its working-days summary cannot be computed.
//
// calendar.py now rejects stored values it used to accept (a legacy 'Sun'
// weekly off day, an unparseable Saturday rule), and GET /working-days turns
// that ValueError into a 404 whose `detail` names the bad value. The tab's
// loader used to end in `catch (_) {}`, so the card showed "Saved: ..." and
// "Update Calendar" with no working-days count and no reason -- the principal
// could not tell a broken calendar from a slow one. This pins that the
// backend's reason reaches the screen and that no summary is shown.
//
// Same technique as curriculum_calendar_contract_test.dart: a real Dio whose
// interceptor answers each path with the backend's real response shape, no
// network. LocalStore is the real Hive-backed store (RealTestEnv).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import '../support/real_di.dart';

const _legacyDetail = "unknown weekly off day 'Sun' -- use full weekday names: "
    'monday, tuesday, wednesday, thursday, friday, saturday, sunday';

/// Answers each GET by path, as the backend would for a school whose one
/// academic year has a calendar saved with a legacy 'Sun' weekly off day.
class _Backend extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final path = options.path;
    Object? body;
    var status = 200;
    if (path == '/curriculum/academic-years') {
      body = [
        {'id': 'year_1', 'label': '2026-27', 'startDate': '2026-06-01', 'endDate': '2027-03-31'},
      ];
    } else if (path.endsWith('/grades')) {
      // One grade: with none, the page shows its 'No curriculum yet' state
      // instead of the tabs.
      body = [
        {'id': 'grade_10', 'number': 10, 'section': null},
      ];
    } else if (path == '/auth/users') {
      body = <Object>[];
    } else if (path.endsWith('/calendar')) {
      body = {
        'id': 'cal_1',
        'academicYearId': 'year_1',
        'weeklyOffDays': ['Sun'],
        'alternateSaturdayRule': 'none',
      };
    } else if (path.endsWith('/holidays')) {
      body = [
        {'id': 'hol_1', 'calendarId': 'cal_1', 'date': '2026-08-15', 'label': 'Independence Day', 'kind': 'public'},
      ];
    } else if (path.endsWith('/working-days')) {
      status = 404;
      body = {'detail': _legacyDetail};
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

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('principal_calendar_setup_load_test_');
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

  testWidgets('a working-days failure shows the server reason, not a silent missing summary', (tester) async {
    tester.view.physicalSize = const Size(1600, 1400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(wrapForTest(const PrincipalAdminPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Calendar & Setup'));
    await tester.pumpAndSettle();

    expect(find.text('Could not load calendar: $_legacyDetail'), findsOneWidget,
        reason: "the backend's detail names the stored value to fix; dropping it leaves the principal guessing");
    // The working-days card sits below the fold of the tab's lazy ListView;
    // scroll it into view so the absence checks below look at a built card.
    final inlineError = find.text('Working days could not be computed: $_legacyDetail');
    await tester.scrollUntilVisible(inlineError, 300,
        scrollable: find.descendant(of: find.byType(ListView), matching: find.byType(Scrollable)).first);
    await tester.pumpAndSettle();
    expect(inlineError, findsOneWidget,
        reason: 'the snackbar is gone in seconds; the card must keep saying why its count is missing');
    expect(find.textContaining('Total Days:'), findsNothing,
        reason: 'no working-days count exists for this calendar, so none may be shown');
    expect(find.textContaining('Configured Holidays'), findsNothing,
        reason: 'a half-loaded tab (holidays without the count they feed) must not look complete');
    expect(find.textContaining('Initialize the academic calendar above'), findsNothing,
        reason: 'the calendar IS saved -- telling the principal to initialize it would be wrong');
  });
}
