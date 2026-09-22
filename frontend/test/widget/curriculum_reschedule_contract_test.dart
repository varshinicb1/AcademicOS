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
  RequestOptions? last;
  _Recorder(this.responseBody);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    last = options;
    handler.resolve(Response(requestOptions: options, statusCode: 200, data: responseBody));
  }
}

(CurriculumApi, _Recorder) _api(Object? responseBody) {
  final rec = _Recorder(responseBody);
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
