// Contract test for the principal admin's Calendar & Setup tab: the exact
// requests CurriculumApi sends to create/correct a calendar and manage
// holidays, and how the backend's CalendarResponse is read back.
//
// The 2026-09-21 product audit found the tab could never create a calendar:
// createCalendar sent `weeklyOffDays: [7]` where the backend's
// CreateCalendarRequest (src/academicos/curriculum/schemas.py) is `list[str]`
// of weekday names -- every create was a 422 -- and CalendarInfo.fromJson cast
// the returned names to int, so even a calendar made elsewhere could not be
// read. tests/test_curriculum_calendar_setup.py pins the server side.
//
// Same technique as curriculum_reschedule_contract_test.dart: a real Dio whose
// interceptor records the outgoing RequestOptions and answers with the
// backend's real response shape, no network.
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';

class _Recorder extends Interceptor {
  final Object? responseBody;
  final int statusCode;
  RequestOptions? last;
  _Recorder(this.responseBody, this.statusCode);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    last = options;
    final response = Response(requestOptions: options, statusCode: statusCode, data: responseBody);
    if (statusCode < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(
          statusCode: statusCode, requestOptions: options, response: response));
    }
  }
}

(CurriculumApi, _Recorder) _api(Object? responseBody, {int statusCode = 200}) {
  final rec = _Recorder(responseBody, statusCode);
  final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(rec);
  return (CurriculumApi(dio), rec);
}

/// CalendarResponse exactly as the backend serialises it (camelCase aliases,
/// weekday names lower-cased by the route).
Map<String, dynamic> _calendarResponse({
  List<String> weeklyOffDays = const ['sunday'],
  String rule = 'second_fourth',
}) =>
    {
      'id': 'cal_1',
      'academicYearId': 'year_1',
      'weeklyOffDays': weeklyOffDays,
      'alternateSaturdayRule': rule,
    };

void main() {
  group('create / update request contract (CreateCalendarRequest)', () {
    test('create posts weekday NAMES, not ints, plus the UI rule value', () async {
      final (api, rec) = _api(_calendarResponse());
      await api.createCalendar('year_1', weeklyOffDays: ['sunday'], alternateSaturdayRule: 'second_fourth');
      final req = rec.last!;
      expect(req.method, 'POST');
      expect(req.path, '/curriculum/academic-years/year_1/calendar');
      expect(req.data, {
        'weeklyOffDays': ['sunday'],
        'alternateSaturdayRule': 'second_fourth',
      });
      expect((req.data as Map)['weeklyOffDays'], everyElement(isA<String>()));
    });

    test('the default weekly off is Sunday by name', () async {
      final (api, rec) = _api(_calendarResponse(rule: 'none'));
      await api.createCalendar('year_1');
      expect(rec.last!.data, {
        'weeklyOffDays': ['sunday'],
        'alternateSaturdayRule': 'none',
      });
    });

    test('update PUTs the same body to the same path', () async {
      final (api, rec) = _api(_calendarResponse(weeklyOffDays: ['saturday', 'sunday'], rule: 'none'));
      final cal = await api.updateCalendar('year_1',
          weeklyOffDays: ['saturday', 'sunday'], alternateSaturdayRule: 'none');
      final req = rec.last!;
      expect(req.method, 'PUT');
      expect(req.path, '/curriculum/academic-years/year_1/calendar');
      expect(req.data, {
        'weeklyOffDays': ['saturday', 'sunday'],
        'alternateSaturdayRule': 'none',
      });
      expect(cal.weeklyOffDays, ['saturday', 'sunday']);
    });
  });

  group('CalendarInfo.fromJson on the real response shape', () {
    test('reads weekday names as strings (it cast them to int before)', () {
      final cal = CalendarInfo.fromJson(_calendarResponse(weeklyOffDays: ['saturday', 'sunday']));
      expect(cal.id, 'cal_1');
      expect(cal.academicYearId, 'year_1');
      expect(cal.weeklyOffDays, ['saturday', 'sunday']);
      expect(cal.alternateSaturdayRule, 'second_fourth');
    });

    test('getCalendar parses the server body, and a 404 means "none yet"', () async {
      final (api, rec) = _api(_calendarResponse());
      final cal = await api.getCalendar('year_1');
      expect(rec.last!.method, 'GET');
      expect(cal!.weeklyOffDays, ['sunday']);

      final (missing, _) = _api({'detail': 'no calendar configured for this academic year yet'},
          statusCode: 404);
      expect(await missing.getCalendar('year_1'), isNull);
    });
  });

  group('holidays', () {
    test('addHoliday posts kind and endDate in the backend field names', () async {
      final (api, rec) = _api({
        'id': 'holiday_1',
        'calendarId': 'cal_1',
        'date': '2026-10-05',
        'label': 'Dussehra break',
        'kind': 'school',
        'endDate': '2026-10-10',
      });
      final h = await api.addHoliday('year_1',
          date: '2026-10-05', label: 'Dussehra break', kind: 'school', endDate: '2026-10-10');
      expect(rec.last!.path, '/curriculum/academic-years/year_1/holidays');
      expect(rec.last!.data, {
        'date': '2026-10-05',
        'label': 'Dussehra break',
        'kind': 'school',
        'endDate': '2026-10-10',
      });
      expect(h.endDate, '2026-10-10');
    });

    test('deleteHoliday DELETEs the holiday under its academic year', () async {
      final (api, rec) = _api({'ok': true});
      await api.deleteHoliday('year_1', 'holiday_1');
      expect(rec.last!.method, 'DELETE');
      expect(rec.last!.path, '/curriculum/academic-years/year_1/holidays/holiday_1');
    });

    test("a refused holiday shows the server's reason", () async {
      const detail = 'holiday 2030-01-01 falls outside the academic year (2026-06-01 .. 2027-03-31)';
      final (api, _) = _api({'detail': detail}, statusCode: 422);
      final e = await api
          .addHoliday('year_1', date: '2030-01-01', label: 'x')
          .then<Object?>((_) => null, onError: (Object e) => e);
      expect(serverErrorMessage(e!), detail);
    });
  });
}
