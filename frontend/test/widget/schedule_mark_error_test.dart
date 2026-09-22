// A refused lesson mark says why, not "check your connection" (Task 604).
//
// The re-audit of the live release (2026-09-22) found the web mark sheet
// showing every failure as "Could not save -- check your connection and try
// again": a 403 (a teacher marking a lesson that is not theirs) read as a
// network fault, so the teacher retried a request that could never succeed.
// The connection wording is now kept for a request that never got an answer.
//
// A real Dio whose interceptor answers instead of the network (no mocking
// library, see pubspec.yaml).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/schedule/pages/my_schedule_page.dart';

String _today() {
  final d = DateTime.now();
  return '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}

class _Server extends Interceptor {
  /// What PATCH /curriculum/scheduled-lessons/{id} does: a status to refuse
  /// with, or a DioExceptionType for a request that never got an answer.
  final int? markStatus;
  final DioExceptionType? markFailure;
  _Server({this.markStatus, this.markFailure});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.method == 'GET' && options.path == '/curriculum/my-schedule') {
      handler.resolve(Response(requestOptions: options, statusCode: 200, data: [
        {
          'lessonId': 'lesson_1', 'date': _today(), 'status': 'scheduled', 'note': null,
          'bookId': 'book_1', 'bookTitle': 'Science X', 'subjectName': 'Science',
          'chapterName': 'Light', 'topicName': 'Reflection', 'subtopicId': 'st_1',
          'subtopicName': 'Laws of reflection',
        },
      ]));
      return;
    }
    if (markFailure != null) {
      handler.reject(DioException(requestOptions: options, type: markFailure!));
      return;
    }
    final response = Response(requestOptions: options, statusCode: markStatus, data: null);
    handler.reject(DioException.badResponse(
        statusCode: markStatus!, requestOptions: options, response: response));
  }
}

Future<void> _markYes(WidgetTester tester, _Server server) async {
  final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(server);
  GetIt.instance.registerSingleton<CurriculumApi>(CurriculumApi(dio));
  await tester.pumpWidget(const MaterialApp(home: MySchedulePage()));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Laws of reflection'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Yes'));
  await tester.pumpAndSettle();
}

void main() {
  tearDown(() => GetIt.instance.reset());

  testWidgets('a 403 on marking a lesson says the account lacks access', (tester) async {
    await _markYes(tester, _Server(markStatus: 403));
    expect(find.textContaining("don't have access"), findsOneWidget);
    expect(find.textContaining('connection'), findsNothing);
  });

  testWidgets('a request that never got an answer still says to check the connection',
      (tester) async {
    await _markYes(tester, _Server(markFailure: DioExceptionType.connectionError));
    expect(find.textContaining('connection'), findsOneWidget);
    expect(find.textContaining("don't have access"), findsNothing);
  });
}
