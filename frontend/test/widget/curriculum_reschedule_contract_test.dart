// Contract test for the principal admin's Reschedule tab: the exact request
// CurriculumApi sends for ADJUST and PUSH, and how the PUSH response is read.
//
// The 2026-09-21 product audit found the tab could never succeed and nothing
// caught it: ADJUST sent `targetDate` where the backend's AdjustLessonRequest
// (src/academicos/curriculum/schemas.py) wants `newDate`; PUSH put
// `academicYearId` in the body (the route takes `academic_year_id` as a query
// parameter), sent `afterDate` instead of `fromDate`, and omitted the then-
// required `periodsPerWeek` -- both calls 422'd. The page then read
// `res['pushedCount']`, a field PushScheduleResponse doesn't have
// (`lessonsPushed`), so even a success would have reported 0.
//
// No Dio mocking library is available (mocktail was removed for a freezed
// conflict -- see pubspec.yaml), so this drives a real Dio whose interceptor
// records the outgoing RequestOptions and answers with the backend's real
// response shape instead of touching the network.
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

/// PushScheduleResponse as the backend serialises it (camelCase aliases).
Map<String, dynamic> _pushResponse({int pushed = 3, List<String> dropped = const []}) => {
      'academicYearId': 'year_1',
      'bookId': 'book_1',
      'fromDate': '2026-09-21',
      'periodsPerWeek': 6,
      'lessonsPushed': pushed,
      'lessonsDropped': dropped,
      'reschedules': const [],
    };

void main() {
  group('ADJUST request contract (AdjustLessonRequest)', () {
    test('posts newDate + reason to /scheduled-lessons/{id}/reschedule', () async {
      final (api, rec) = _api({'id': 'lesson_1'});
      await api.rescheduleLesson('lesson_1', newDate: '2026-09-24', reason: 'Assembly');
      final req = rec.last!;
      expect(req.method, 'POST');
      expect(req.path, '/curriculum/scheduled-lessons/lesson_1/reschedule');
      expect(req.data, {'newDate': '2026-09-24', 'reason': 'Assembly'});
      expect(req.queryParameters, isEmpty);
    });
  });

  group('PUSH request contract (push_schedule route + PushScheduleRequest)', () {
    test('academic_year_id rides in the query; fromDate + reason in the body; '
        'no periodsPerWeek when the admin left it unset', () async {
      final (api, rec) = _api(_pushResponse());
      await api.pushSchedule(
          bookId: 'book_1', academicYearId: 'year_1', fromDate: '2026-09-21', reason: 'Closure');
      final req = rec.last!;
      expect(req.method, 'POST');
      expect(req.path, '/curriculum/books/book_1/schedule/push');
      expect(req.queryParameters, {'academic_year_id': 'year_1'});
      expect(req.data, {'fromDate': '2026-09-21', 'reason': 'Closure'});
    });

    test('sends periodsPerWeek only when the admin set one', () async {
      final (api, rec) = _api(_pushResponse());
      await api.pushSchedule(
          bookId: 'book_1',
          academicYearId: 'year_1',
          fromDate: '2026-09-21',
          reason: 'Closure',
          periodsPerWeek: 5);
      expect(rec.last!.data, {'fromDate': '2026-09-21', 'reason': 'Closure', 'periodsPerWeek': 5});
    });

    // Audit N-3-1: the web's PUSH sent no sectionId, so it could never move a
    // section's plan -- the only kind the Lesson plans page makes.
    test("sends sectionId to move one section's plan", () async {
      final (api, rec) = _api(_pushResponse());
      await api.pushSchedule(
          bookId: 'book_1', academicYearId: 'year_1', fromDate: '2026-09-21', reason: 'Closure', sectionId: 'sec_a');
      expect(rec.last!.queryParameters, {'academic_year_id': 'year_1'});
      expect(rec.last!.data, {'fromDate': '2026-09-21', 'reason': 'Closure', 'sectionId': 'sec_a'});
    });
  });

  group("refusals show the server's detail, not Dio's generic text", () {
    test('an ADJUST 409 surfaces the clash date and occupying lesson IDs', () async {
      const detail = '2026-09-24 already has 1 lesson(s) for this book (lesson_7) and this '
          'subject has 1 period(s) that day -- move or push that lesson first';
      final (api, _) = _api({'detail': detail}, statusCode: 409);
      Object? caught;
      try {
        await api.rescheduleLesson('lesson_1', newDate: '2026-09-24', reason: 'swap');
      } catch (e) {
        caught = e;
      }
      expect(caught, isA<DioException>());
      expect('$caught', isNot(contains('lesson_7')), reason: 'why the page needs the helper');
      expect(serverErrorMessage(caught!), detail);
    });

    test('a PUSH 422 surfaces the missing-allocation message', () async {
      const detail = "no periods_per_week supplied and no stored subject period allocation for "
          "'Mathematics' in this academic year -- set one, or pass periodsPerWeek";
      final (api, _) = _api({'detail': detail}, statusCode: 422);
      final e = await api
          .pushSchedule(bookId: 'book_1', academicYearId: 'year_1', fromDate: '2026-09-21', reason: 'x')
          .then<Object?>((_) => null, onError: (Object e) => e);
      expect(serverErrorMessage(e!), detail);
    });

    test('a validation 422 (detail is a list) names the field and the reason (Task 802)', () async {
      final (api, _) = _api({
        'detail': [
          {'loc': ['body', 'newDate'], 'msg': 'Field required'}
        ]
      }, statusCode: 422);
      final e = await api
          .rescheduleLesson('lesson_1', newDate: '', reason: '')
          .then<Object?>((_) => null, onError: (Object e) => e);
      expect(serverErrorMessage(e!), 'newDate: Field required');
    });
  });

  group('PUSH response parsing (what the Reschedule tab shows)', () {
    test('reads lessonsPushed and lessonsDropped', () async {
      final (api, _) = _api(_pushResponse(pushed: 7, dropped: ['lesson_9', 'lesson_10']));
      final res = await api.pushSchedule(
          bookId: 'book_1', academicYearId: 'year_1', fromDate: '2026-09-21', reason: 'Closure');
      expect(res.lessonsPushed, 7);
      expect(res.lessonsDropped, ['lesson_9', 'lesson_10']);
      expect(res.periodsPerWeek, 6);
    });

    test('summary names the pushed count, and the dropped count only when non-zero', () {
      expect(PushScheduleResult.fromJson(_pushResponse(pushed: 4)).summary,
          'Schedule pushed: 4 lessons shifted.');
      expect(PushScheduleResult.fromJson(_pushResponse(pushed: 1, dropped: ['a', 'b'])).summary,
          'Schedule pushed: 1 lesson shifted. 2 lessons no longer fit before the year ends.');
    });
  });
}
