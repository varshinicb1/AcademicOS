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
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async =>
      ResponseBody.fromString(answers[o.path] ?? '[]', 200,
          headers: {Headers.contentTypeHeader: ['application/json']});

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

  setUp(() {
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = _Server());
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
  });

  testWidgets('Today: the student sees times, the room and a changed period', (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    await pump(tester, const StudentTodayPage());
    expect(tester.takeException(), isNull);
    expect(find.textContaining('08:00–08:45'), findsOneWidget);
    expect(find.textContaining('Physics Lab'), findsOneWidget);
    expect(find.text('Changed'), findsOneWidget);
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
