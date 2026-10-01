// The teacher's My day and the student's Today as the apps show them (v3
// audit areas 4 and 5): each period's time and room, what changed, the
// handover note for whoever covers, "Partly" for a lesson, the next period,
// and an inbox link for every kind the server sends. Neither page had a
// widget test.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/cover_pages.dart';
import 'package:academicos/presentation/workspace/inbox_page.dart';
import 'package:academicos/presentation/workspace/period_line.dart';
import 'package:academicos/presentation/workspace/student_today_page.dart';
import 'package:academicos/presentation/workspace/week_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

const _day = '[{"sectionId":"s10a","period":1,"subjectId":"sci","teacherId":"u1","kind":"regular",'
    '"sectionName":"10-A","subjectName":"Science","startTime":"08:00","endTime":"08:45","changed":false},'
    '{"sectionId":"s9a","period":3,"subjectId":"mat","teacherId":"u1","kind":"substitute","roomId":"r1",'
    '"roomName":"Physics Lab","sectionName":"9-A","subjectName":"Mathematics","startTime":"10:00",'
    '"endTime":"10:45","changed":true,"note":"Worksheet 3 is on my desk"}]';

class _Server implements HttpClientAdapter {
  final List<RequestOptions> posted = [];
  final Map<String, String> answers = {
    '/curriculum/my-day': _day,
    '/curriculum/substitutions': '[{"id":"sub1","date":"2026-10-02","sectionId":"s9a","period":3,"subjectId":"mat",'
        '"absentTeacherId":"u2","substituteId":"u1","status":"proposed","mode":"substitute",'
        '"handoverNote":"Worksheet 3 is on my desk"}]',
    '/curriculum/leave-requests': '[]',
    '/curriculum/my-schedule': '[{"lessonId":"l1","date":"2026-10-01","status":"scheduled","sectionName":"10-A",'
        '"subjectName":"Science","chapterName":"Light","topicName":"Mirrors","subtopicName":"Concave mirrors"}]',
    '/curriculum/academic-years': '[]',
    '/my-homework': '[]',
    '/my-exams': '{"exams":[]}',
    '/my-calendar': '[{"kind":"holiday","title":"Sports day","date":"2026-10-05"},'
        '{"kind":"invigilation","title":"Invigilation: 10-A Science","date":"2026-10-08",'
        '"startTime":"09:30","endTime":"11:00"}]',
    '/my-load': '{"periodsPerWeek":24,"maxInOneDay":6,"daysTaught":{"0":6,"1":4},'
        '"classes":[{"sectionName":"10-A","subjectName":"Science","periodsPerWeek":6}],'
        '"coversThisWeek":2,"invigilationsAhead":1}',
    '/curriculum/my-timetable': '{"role":"teacher","entries":[{"dayOfWeek":0,"period":1,'
        '"subjectName":"Science","sectionName":"10-A"}],"bellSchedule":{"slots":'
        '[{"period":1,"start":"08:00","end":"08:45"}],"days":[0,1,2,3,4,5]}}',
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'POST') posted.add(o);
    final post = o.path == '/curriculum/my-attendance'
        ? '{"teacherId":"u1","name":"Tara Teacher","status":"present"}'
        : '{}';
    return ResponseBody.fromString(o.method == 'POST' ? post : (answers[o.path] ?? '[]'), 200,
        headers: {Headers.contentTypeHeader: ['application/json']});
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('app_day_pages_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  late _Server server;

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

  Future<void> pump(WidgetTester tester, Widget page) async {
    tester.view.physicalSize = const Size(390, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.lightTheme, home: page));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    for (var i = 0; i < 3; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  testWidgets('My day: each period with its time and room, what changed, the note and Partly', (tester) async {
    await pump(tester, const MyDayPage());
    expect(tester.takeException(), isNull);
    expect(find.textContaining('08:00–08:45'), findsOneWidget);
    expect(find.textContaining('10:00–10:45 · Physics Lab'), findsOneWidget);
    expect(find.textContaining('Worksheet 3 is on my desk'), findsWidgets, reason: 'the handover reaches the cover');
    expect(find.textContaining('1 changed'), findsOneWidget);
    expect(find.text('Partly'), findsOneWidget);
    expect(find.text('Covering'), findsOneWidget);
    // The lesson's buttons sit under it: on a 390 px phone the title keeps the
    // row's width instead of wrapping one word a line beside three buttons.
    final title = tester.getSize(find.textContaining('Concave mirrors').first);
    expect(title.width, greaterThan(250));
  });

  testWidgets('Leave for today in three taps (TA-3)', (tester) async {
    await pump(tester, const MyDayPage());
    final apply = find.text('Apply for leave');
    await tester.scrollUntilVisible(apply, 200);
    await tester.tap(apply); // 1
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.byKey(const Key('leave-today')), findsOneWidget, reason: 'today is chosen as the dialog opens');
    await tester.tap(find.byKey(const Key('leave-apply'))); // 2: leave for today
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 50));
    final sent = server.posted.where((o) => o.path == '/curriculum/leave-requests').toList();
    expect(sent, hasLength(1));
    final now = DateTime.now();
    final today = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    expect((sent.single.data as Map)['startDate'], today);
    expect((sent.single.data as Map)['endDate'], today);
  });

  // "I'm here" went back to "I'm here" every time My day opened, inviting a
  // second check-in and saying nothing of the first (QA S-12, 2026-10-01).
  testWidgets("I'm here stays marked when My day opens again", (tester) async {
    await pump(tester, const MyDayPage());
    await tester.tap(find.byKey(const Key('check-in')));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 50));
    expect(find.text('Marked present'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await pump(tester, const MyDayPage());
    expect(find.text('Marked present'), findsOneWidget, reason: 'today\'s check-in is remembered');
    expect(find.text("I'm here"), findsNothing);
    expect(server.posted.where((o) => o.path == '/curriculum/my-attendance'), hasLength(1));
  });

  testWidgets("another day's check-in does not mark today", (tester) async {
    LocalStore.instance.setCheckIn('u1', '2000-01-01', 'present');
    await pump(tester, const MyDayPage());
    expect(find.text("I'm here"), findsOneWidget);
  });

  testWidgets('Today: the student sees times, the room and a changed period', (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    await pump(tester, const StudentTodayPage());
    expect(tester.takeException(), isNull);
    expect(find.textContaining('08:00–08:45'), findsOneWidget);
    expect(find.textContaining('Physics Lab'), findsOneWidget);
    expect(find.text('Changed'), findsOneWidget);
  });

  testWidgets('Week: what is coming up, my load, then the timetable (TA-2)', (tester) async {
    await pump(tester, const WeekPage());
    expect(tester.takeException(), isNull);
    expect(find.text('Coming up'), findsOneWidget);
    expect(find.text('Sports day'), findsOneWidget);
    expect(find.text('Invigilation: 10-A Science'), findsOneWidget);
    expect(find.textContaining('09:30–11:00'), findsOneWidget);
    expect(find.text('24 periods a week'), findsOneWidget);
    expect(find.text('Busiest day: Mon (6)'), findsOneWidget);
    expect(find.textContaining('Covers this week: 2'), findsOneWidget);
    expect(find.text('10-A Science · 6'), findsOneWidget);
    expect(find.text('P1'), findsOneWidget, reason: 'the grid is still there');
  });

  testWidgets('Week: a student gets no load section', (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    await pump(tester, const WeekPage());
    expect(tester.takeException(), isNull);
    expect(find.text('My load'), findsNothing);
    expect(find.text('Sports day'), findsOneWidget);
  });

  test('when a calendar item happens', () {
    final today = DateTime(2026, 10, 1);
    expect(calendarWhen({'date': '2026-10-01'}, today), 'Today');
    expect(calendarWhen({'date': '2026-10-02', 'startTime': '09:30', 'endTime': '11:00'}, today),
        'Tomorrow · 09:30–11:00');
    expect(calendarWhen({'date': '2026-10-05', 'endDate': '2026-10-09'}, today), 'Mon 5 Oct – Fri 9 Oct');
  });

  test('the next period and its countdown', () {
    final rows = [
      {'period': 1, 'startTime': '08:00', 'kind': 'regular'},
      {'period': 3, 'startTime': '10:00', 'kind': 'substitute', 'sectionName': '9-A'},
      {'period': 4, 'startTime': '11:00', 'kind': 'lost'},
    ];
    expect(nextPeriodLine(rows, DateTime(2026, 10, 1, 9, 35), what: (r) => r['sectionName'] as String? ?? ''),
        'Next: period 3 at 10:00 · 9-A (in 25 min)');
    expect(nextPeriodLine(rows, DateTime(2026, 10, 1, 10, 30)), isNull, reason: 'a lost period is nobody\'s next');
    expect(periodWhenWhere({'startTime': '08:00', 'endTime': '08:45', 'roomName': 'Lab'}), '08:00–08:45 · Lab');
    expect(periodWhenWhere({}), '');
  });

  test('every link the server sends opens a page', () {
    const links = ['/my-exams', '/my-homework/h1', '/assessments/a1', '/my-day?date=2026-10-01', '/week',
      '/dashboard', '/homework/h1', '/cover?date=2026-10-01', '/school/term-report', '/my-timetable',
      '/my-children', '/leave', '/homework', '/my-learning'];
    for (final l in links) {
      expect(inboxRoute(l, 'teacher'), isNotNull, reason: l);
    }
    expect(inboxRoute('/cover?date=2026-10-01', 'principal'), '/school/cover');
    expect(inboxRoute('/cover?date=2026-10-01', 'teacher'), '/school/my-day');
    expect(inboxRoute('/assessments/a1', 'teacher'), '/assessment/a1');
    expect(inboxRoute('/my-timetable', 'student'), '/school/week');
    expect(inboxRoute('/leave', 'teacher'), '/school/my-day');
  });
}
