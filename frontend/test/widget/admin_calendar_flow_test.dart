// The admin console's Calendar & Setup, as a new school's principal meets it
// (QA of 2026-10-01):
//
// - S-15: a year the setup card has just made has no calendar, and asking for
//   one was a 404 the screen hid. The console now knows and does not ask.
// - S-19: after "Update Calendar" the saved line still said "Saturday rule
//   none" until a reload, then the stored value "second_fourth". The line is
//   the server's answer to the save, in words.
// - S-09: the dashboard's setup checklist links to Calendar & Setup, so the
//   console can open on that tab.
//
// The fake backend keeps a school's year, classes and calendar as the server
// does. Its GET of the calendar answers what was first saved, never an
// update: a line that followed a re-read instead of the save shows stale.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import '../support/real_di.dart';

class _Backend extends Interceptor {
  final List<String> calls = [];
  bool hasYear = false;
  final Set<int> grades = {};
  Map<String, dynamic>? firstCalendar;
  Map<String, dynamic>? calendar;

  void _answer(RequestInterceptorHandler h, RequestOptions o, int status, Object? body) {
    final r = Response(requestOptions: o, statusCode: status, data: body);
    if (status < 400) {
      h.resolve(r);
    } else {
      h.reject(DioException.badResponse(statusCode: status, requestOptions: o, response: r));
    }
  }

  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    final path = o.path;
    calls.add('${o.method} $path');
    final body = o.data is Map ? Map<String, dynamic>.from(o.data as Map) : <String, dynamic>{};
    const year = {'id': 'year_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'};
    switch ((o.method, path)) {
      case ('GET', '/curriculum/academic-years'):
        return _answer(h, o, 200, hasYear ? [year] : <Object>[]);
      case ('GET', '/curriculum/academic-years/year_1/grades'):
        return _answer(h, o, 200, [for (final g in grades) {'id': 'g_$g', 'number': g, 'section': null}]);
      case ('GET', '/curriculum/school-profile'):
        return _answer(h, o, 200, {'name': 'Green Valley School', 'address': null, 'affiliation': null,
          'hasLogo': false});
      case ('POST', '/curriculum/seed/cbse'):
        hasYear = true;
        grades.add(body['grade'] as int);
        return _answer(h, o, 200, {'boardId': 'b', 'academicYearId': 'year_1', 'gradeId': 'g_${body['grade']}',
          'grade': body['grade'], 'subjectsSeeded': 5, 'unitsSeeded': 10, 'chaptersSeeded': 14,
          'subjectsSkipped': <String>[]});
      case ('GET', '/curriculum/academic-years/year_1/calendar'):
        if (firstCalendar == null) return _answer(h, o, 404, {'detail': 'no calendar configured for this academic year yet'});
        return _answer(h, o, 200, firstCalendar);
      case ('POST', '/curriculum/academic-years/year_1/calendar'):
        calendar = {'id': 'cal_1', 'academicYearId': 'year_1', ...body};
        firstCalendar = calendar;
        return _answer(h, o, 200, calendar);
      case ('PUT', '/curriculum/academic-years/year_1/calendar'):
        calendar = {'id': 'cal_1', 'academicYearId': 'year_1', ...body};
        return _answer(h, o, 200, calendar);
      case ('GET', '/curriculum/academic-years/year_1/working-days'):
        return _answer(h, o, 200, {'academicYearId': 'year_1', 'totalDays': 365, 'workingDays': 290,
          'weeklyOffCount': 52, 'alternateSaturdayOffCount': 0, 'holidayCount': 0, 'dates': <String>[]});
      case ('GET', '/curriculum/academic-years/year_1/holidays'):
      case ('GET', '/curriculum/academic-years/year_1/terms'):
      case ('GET', '/auth/users'):
        return _answer(h, o, 200, <Object>[]);
    }
    _answer(h, o, 404, {'detail': 'not served here'});
  }

  int get calendarReads => calls.where((c) => c == 'GET /curriculum/academic-years/year_1/calendar').length;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;
  late _Backend backend;

  setUpAll(() async {
    env = await RealTestEnv.init('admin_calendar_flow_test_');
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
    await GetIt.instance.reset();
    backend = _Backend();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(backend);
    GetIt.instance
      ..registerSingleton<CurriculumApi>(CurriculumApi(dio))
      ..registerSingleton<AuthApi>(AuthApi(dio));
    LocalStore.instance.authUser = {
      'id': 'u_principal', 'schoolId': 'school_1', 'name': 'Farida Khan',
      'email': 'farida@school.invalid', 'role': 'principal',
    };
  });

  Future<void> pump(WidgetTester tester, Widget page) async {
    tester.view.physicalSize = const Size(1600, 1400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(wrapForTest(page));
    await tester.pumpAndSettle();
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  testWidgets("a year the setup just made is not asked for a calendar it cannot have (S-15)", (tester) async {
    await pump(tester, const PrincipalAdminPage());
    expect(find.byKey(const ValueKey('school-setup-card')), findsOneWidget);
    await tapKey(tester, 'setup-run');
    await tapKey(tester, 'setup-continue');
    await tester.tap(find.text('Calendar & Setup'));
    await tester.pumpAndSettle();
    expect(find.text('Initialize Calendar'), findsOneWidget);
    expect(backend.calendarReads, 0, reason: 'the 404 is not fetched');

    await tester.tap(find.text('Initialize Calendar'));
    await tester.pumpAndSettle();
    expect(find.text('Saved: Sundays off; every Saturday a working day.'), findsOneWidget);
    expect(find.text('Update Calendar'), findsOneWidget);
    expect(backend.calendarReads, 0);
  });

  testWidgets('the saved line follows the update at once, in words (S-19)', (tester) async {
    backend
      ..hasYear = true
      ..grades.add(10)
      ..firstCalendar = {'id': 'cal_1', 'academicYearId': 'year_1', 'weeklyOffDays': ['sunday'],
        'alternateSaturdayRule': 'none'};
    await pump(tester, const PrincipalAdminPage(initialTab: 'calendar'));
    expect(find.text('Saved: Sundays off; every Saturday a working day.'), findsOneWidget,
        reason: 'opened on Calendar & Setup, it loads that tab');

    await tester.tap(find.text('None (All working)'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('2nd & 4th Saturdays Off').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Update Calendar'));
    await tester.pumpAndSettle();
    expect(backend.calendar?['alternateSaturdayRule'], 'second_fourth');
    expect(find.text('Saved: Sundays off; 2nd and 4th Saturdays off.'), findsOneWidget);
    expect(find.textContaining('second_fourth'), findsNothing);
    expect(find.textContaining('§'), findsNothing, reason: 'no requirement numbers on screen (S-23)');
  });
}
