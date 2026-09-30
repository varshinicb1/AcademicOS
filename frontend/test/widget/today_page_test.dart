// The teacher's Today on the web reads the school's server: today's periods
// and planned lessons, what waits on them, and their recent papers, with one
// main action (review 2026-10-01).
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/home/pages/today_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _Server implements HttpClientAdapter {
  final Map<String, Object> answers = {
    '/curriculum/my-day': '[{"sectionId":"s10a","period":2,"subjectId":"sci","kind":"regular",'
        '"sectionName":"10-A","subjectName":"Science"},{"sectionId":"s9a","period":4,"subjectId":"mat",'
        '"kind":"substitute","sectionName":"9-A","subjectName":"Mathematics"}]',
    '/curriculum/my-schedule': '[{"lessonId":"l1","date":"2026-10-01","status":"scheduled","bookId":"b",'
        '"bookTitle":"Science","subjectName":"Science","chapterName":"Life Processes","topicName":"Respiration",'
        '"subtopicId":"st","subtopicName":"Aerobic and anaerobic respiration","sectionName":"10-A"}]',
    '/paper-reviews': '[{"id":"r1","assessmentId":"a9","title":"Class 10 Maths unit test","authorId":"u2",'
        '"reviewerId":"u1","state":"pending","requestNote":"Please check Section C","requestedAt":"2026-09-30"}]',
    '/homework': '[{"id":"h1","title":"Chemical reactions","subjectId":"sci","subjectName":"Science","grade":10,'
        '"sectionIds":["s10b"],"sectionNames":["10-B"],"teacherId":"u1","dueDate":"2026-10-02","status":"open",'
        '"questionCount":6,"totalMarks":12,"submitted":5,"graded":3,"students":30}]',
    '/assessments': '[{"id":"a1","title":"Half-yearly","subject":"Science","grade":10,"status":"underReview",'
        '"updatedAt":"2026-09-30T10:00:00Z"}]',
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    final a = answers[o.path];
    if (a is int) {
      return ResponseBody.fromString('{"detail":"the server said no"}', a,
          headers: {Headers.contentTypeHeader: ['application/json']});
    }
    return ResponseBody.fromString((a ?? '[]') as String, 200,
        headers: {Headers.contentTypeHeader: ['application/json']});
  }

  @override
  void close({bool force = false}) {}
}

Widget _app() => MaterialApp.router(
      theme: AppTheme.lightTheme,
      routerConfig: GoRouter(initialLocation: '/home', routes: [
        GoRoute(path: '/home', builder: (_, __) => TodayPage(now: DateTime(2026, 10, 1, 9))),
        GoRoute(path: '/assessment/:id', builder: (_, s) => Text('paper ${s.pathParameters['id']}')),
        GoRoute(path: '/assessment', builder: (_, __) => const Text('papers')),
        GoRoute(path: '/school/week', builder: (_, __) => const Text('week')),
        GoRoute(path: '/school/homework/:id', builder: (_, s) => Text('homework ${s.pathParameters['id']}')),
      ]),
    );

void main() {
  late Directory tmp;
  late _Server server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('today_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'u1', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Tara Teacher'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    // Hive.close() can hang on Windows; do not let it hold the run.
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // not-a-failure: the box file is released when the test process exits
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pump(WidgetTester tester, Size size) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(_app());
    // Dio's replies are real futures: step outside the fake-async zone so
    // they land, then build the frames. (pumpAndSettle would wait on the
    // loading spinners for ten minutes if a reply never came.)
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    for (var i = 0; i < 3; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  testWidgets('the day, what waits, and the recent papers, with one main action', (tester) async {
    await pump(tester, const Size(1280, 900));
    expect(tester.takeException(), isNull);
    expect(find.text('Good morning, Tara'), findsOneWidget);
    expect(find.text('Thursday, 1 October'), findsOneWidget);
    expect(find.text('10-A'), findsOneWidget);
    expect(find.text('Cover'), findsOneWidget, reason: 'a substitution period says so');
    expect(find.text('Aerobic and anaerobic respiration'), findsOneWidget);
    expect(find.text('Review: Class 10 Maths unit test'), findsOneWidget);
    expect(find.text('Mark 2 submissions'), findsOneWidget, reason: '5 handed in, 3 marked');
    expect(find.text('In review'), findsOneWidget);
    expect(find.byType(FilledButton), findsOneWidget, reason: 'one main action: New paper');

    await tester.tap(find.widgetWithText(OutlinedButton, 'Mark'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('homework h1'), findsOneWidget);
  });

  testWidgets('a card whose call fails says so and offers a retry; the others still show', (tester) async {
    server.answers['/paper-reviews'] = 500;
    await pump(tester, const Size(1280, 900));
    expect(find.text('Try again'), findsOneWidget);
    expect(find.text('10-A'), findsOneWidget);
    expect(find.text('Mark 2 submissions'), findsOneWidget);
  });

  testWidgets('a quiet day and no papers read as such, with no overflow on a phone', (tester) async {
    for (final path in ['/curriculum/my-day', '/curriculum/my-schedule', '/paper-reviews', '/homework', '/assessments']) {
      server.answers[path] = '[]';
    }
    await pump(tester, const Size(390, 844));
    expect(tester.takeException(), isNull);
    expect(find.text('No periods or lessons today.'), findsOneWidget);
    expect(find.text('Nothing is waiting for you.'), findsOneWidget);
    await tester.scrollUntilVisible(find.textContaining('Your papers will appear here'), 200);
    expect(find.textContaining('Your papers will appear here'), findsOneWidget);
  });
}
