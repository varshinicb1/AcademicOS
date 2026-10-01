// The principal enters a half day, an exam window or a compensatory working
// day from the web (v3 audit N-3-19). The calendar knew only weekly offs,
// alternate Saturdays and closures, and the web's holiday form offered only
// those kinds, so none of the three could be entered.
//
// The fake backend answers the way the holiday route does, refusals included,
// so the card is tested against answers of the real shape.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/widgets/calendar_days_card.dart';

class _Backend extends Interceptor {
  final List<Map<String, dynamic>> posted = [];
  String? refuse;

  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    if (o.method == 'POST' && o.path == '/curriculum/academic-years/ay_1/holidays') {
      final body = Map<String, dynamic>.from(o.data as Map);
      if (refuse != null) {
        final r = Response(requestOptions: o, statusCode: 422, data: {'detail': refuse});
        return h.reject(DioException.badResponse(statusCode: 422, requestOptions: o, response: r));
      }
      posted.add(body);
      return h.resolve(Response(requestOptions: o, statusCode: 200, data: {
        'id': 'holiday_${posted.length}', 'calendarId': 'cal_1', 'lessonsMoved': 3, 'notMoved': [], ...body,
      }));
    }
    final r = Response(requestOptions: o, statusCode: 404, data: {'detail': 'no route'});
    h.reject(DioException.badResponse(statusCode: 404, requestOptions: o, response: r));
  }
}

void main() {
  Future<(List<String>, List<int>)> pump(WidgetTester tester, _Backend backend) async {
    tester.view.physicalSize = const Size(375, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final messages = <String>[];
    final changed = <int>[];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: CalendarDaysCard(
            api: CurriculumApi(Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(backend)),
            academicYearId: 'ay_1',
            grades: const [9, 10],
            onMessage: messages.add,
            onChanged: () => changed.add(1),
          ),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    return (messages, changed);
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  testWidgets('a half day keeps periods up to the one chosen', (tester) async {
    final backend = _Backend();
    final (messages, changed) = await pump(tester, backend);
    expect(tester.takeException(), isNull, reason: 'the card fits a phone');
    await tester.enterText(find.byKey(const ValueKey('day-label')), 'PTM');
    await tester.enterText(find.byKey(const ValueKey('day-date')), '2026-10-12');
    await tapKey(tester, 'day-last-period');
    await tester.tap(find.text('Period 3').last);
    await tester.pumpAndSettle();
    await tapKey(tester, 'day-add');
    expect(backend.posted.single, {'date': '2026-10-12', 'label': 'PTM', 'kind': 'half_day', 'lastPeriod': 3});
    expect(messages.single, '"PTM" added (half day, periods 1-3). 3 lessons moved to fit it.');
    expect(changed, [1]);
  });

  testWidgets('an exam window stops the classes chosen', (tester) async {
    final backend = _Backend();
    await pump(tester, backend);
    await tapKey(tester, 'day-kind-exam_window');
    await tester.enterText(find.byKey(const ValueKey('day-label')), 'Half-yearly');
    await tester.enterText(find.byKey(const ValueKey('day-date')), '2026-09-21');
    await tester.enterText(find.byKey(const ValueKey('day-end')), '2026-09-30');
    expect(find.text('None chosen: every class.'), findsOneWidget);
    await tapKey(tester, 'day-grade-10');
    await tapKey(tester, 'day-add');
    expect(backend.posted.single, {'date': '2026-09-21', 'label': 'Half-yearly', 'kind': 'exam_window',
      'endDate': '2026-09-30', 'grades': [10]});
  });

  testWidgets('a working day runs the weekday chosen, and the server\'s refusal is shown', (tester) async {
    final backend = _Backend()
      ..refuse = '2026-10-10 is already a working day: a compensatory working day is a weekly off or an '
          'alternate Saturday off made a working day';
    final (messages, _) = await pump(tester, backend);
    await tapKey(tester, 'day-kind-working_day');
    expect(find.byKey(const ValueKey('day-end')), findsNothing, reason: 'one day at a time');
    await tester.enterText(find.byKey(const ValueKey('day-label')), 'Makes up the rain day');
    await tester.enterText(find.byKey(const ValueKey('day-date')), '2026-10-10');
    await tapKey(tester, 'day-add');
    expect(find.textContaining('already a working day'), findsOneWidget);
    expect(messages, isEmpty);

    backend.refuse = null;
    await tapKey(tester, 'day-weekday');
    await tester.tap(find.text('Wednesday').last);
    await tester.pumpAndSettle();
    await tapKey(tester, 'day-add');
    expect(backend.posted.single, {'date': '2026-10-10', 'label': 'Makes up the rain day', 'kind': 'working_day',
      'timetableWeekday': 2});
  });

  testWidgets('a date that is not one is caught before anything is sent', (tester) async {
    final backend = _Backend();
    await pump(tester, backend);
    await tester.enterText(find.byKey(const ValueKey('day-label')), 'PTM');
    await tester.enterText(find.byKey(const ValueKey('day-date')), '12/10/2026');
    await tapKey(tester, 'day-add');
    expect(find.text('Enter the date as YYYY-MM-DD.'), findsOneWidget);
    expect(backend.posted, isEmpty);
  });

  test('each day says what it does', () {
    HolidayInfo h(Map<String, dynamic> j) =>
        HolidayInfo.fromJson({'id': 'h', 'calendarId': 'c', 'date': '2026-10-12', 'label': 'x', ...j});
    expect(h({'kind': 'half_day', 'lastPeriod': 4}).describe, 'half day, periods 1-4');
    expect(h({'kind': 'exam_window', 'grades': [9, 10]}).describe, 'exam window, class 9, 10');
    expect(h({'kind': 'exam_window'}).describe, 'exam window, every class');
    expect(h({'kind': 'working_day', 'timetableWeekday': 0}).describe, "working day, Monday's timetable");
    expect(h({'kind': 'public'}).describe, 'public');
  });
}
