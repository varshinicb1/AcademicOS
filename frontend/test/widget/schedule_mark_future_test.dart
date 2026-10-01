// A lesson whose day has not come is not offered Yes / No (audit D67).
//
// The live audit marked lessons dated 2026-09-28 and 09-29 taught on
// 2026-09-27, and the principal's coverage counted them. The server now
// refuses that with a 409; the sheet says when the lesson can be marked
// instead of offering buttons that can only fail.
//
// A real Dio whose interceptor answers instead of the network (no mocking
// library, see pubspec.yaml).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/schedule/pages/my_schedule_page.dart';

String _iso(DateTime d) => '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

class _Server extends Interceptor {
  final String lessonDate;
  int marks = 0;
  _Server(this.lessonDate);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.method == 'GET' && options.path == '/curriculum/my-schedule') {
      handler.resolve(Response(requestOptions: options, statusCode: 200, data: [
        {
          'lessonId': 'lesson_1', 'date': lessonDate, 'status': 'scheduled', 'note': null,
          'bookId': 'book_1', 'bookTitle': 'Science X', 'subjectName': 'Science',
          'chapterName': 'Light', 'topicName': 'Reflection', 'subtopicId': 'st_1',
          'subtopicName': 'Laws of reflection',
        },
      ]));
      return;
    }
    marks++;
    handler.resolve(Response(requestOptions: options, statusCode: 200, data: null));
  }
}

Future<_Server> _openSheet(WidgetTester tester, String lessonDate) async {
  final server = _Server(lessonDate);
  final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(server);
  GetIt.instance.registerSingleton<CurriculumApi>(CurriculumApi(dio));
  await tester.pumpWidget(const MaterialApp(home: MySchedulePage()));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Laws of reflection'));
  await tester.pumpAndSettle();
  return server;
}

void main() {
  tearDown(() => GetIt.instance.reset());

  testWidgets("tomorrow's lesson cannot be marked yet", (tester) async {
    final tomorrow = _iso(DateTime.now().add(const Duration(days: 1)));
    final server = await _openSheet(tester, tomorrow);
    expect(find.byKey(const ValueKey('mark-not-yet')), findsOneWidget);
    expect(find.textContaining(tomorrow), findsWidgets);
    expect(find.text('Yes'), findsNothing);
    expect(find.text('No'), findsNothing);
    expect(server.marks, 0);
  });

  testWidgets("today's lesson is still offered Yes and No", (tester) async {
    await _openSheet(tester, _iso(DateTime.now()));
    expect(find.byKey(const ValueKey('mark-not-yet')), findsNothing);
    expect(find.text('Yes'), findsOneWidget);
    expect(find.text('No'), findsOneWidget);
  });
}
