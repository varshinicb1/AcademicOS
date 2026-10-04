// The week page's timetable (redesign 2026-10-04): a full-width grid coloured by subject where there is
// room, one day at a time from a row of day chips on a phone, empty first and last periods left out.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/week_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _Server implements HttpClientAdapter {
  final Map<String, Object> answers = {};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async =>
      ResponseBody.fromString(jsonEncode(answers[o.path] ?? <Object>[]), 200,
          headers: {Headers.contentTypeHeader: ['application/json']});

  @override
  void close({bool force = false}) {}
}

Map<String, Object> _entry(int day, int period, String subject, String teacher) =>
    {'dayOfWeek': day, 'period': period, 'subjectName': subject, 'teacherName': teacher, 'sectionName': '10-A'};

void main() {
  late Directory tmp;
  late _Server server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('week_page_layout_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server()
      ..answers['/my-calendar'] = <Object>[]
      ..answers['/curriculum/my-timetable'] = {
        'role': 'student',
        'entries': [
          _entry(0, 2, 'English', 'Esha Thomas'),
          _entry(0, 4, 'Mathematics', 'Meera Iyer'),
          _entry(1, 2, 'Science', 'Suresh Rao'),
          _entry(1, 4, 'Mathematics', 'Meera Iyer'),
        ],
        // P1 and P5 are on the bell and taught on no day: leading and trailing rows to leave out.
        'bellSchedule': {
          'slots': [
            for (var p = 1; p <= 5; p++) {'period': p, 'start': '0${7 + p}:00', 'end': '0${7 + p}:45'},
          ],
          'days': [0, 1, 2, 3, 4, 5],
        },
      };
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
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
      // a leaked temp dir is harmless
    }
  });

  Future<void> pump(WidgetTester tester, Size size) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.lightTheme, home: const WeekPage()));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    for (var i = 0; i < 3; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  testWidgets('wide: every day is a column and the grid fills the page, not a scrolling table', (tester) async {
    await pump(tester, const Size(1200, 1800));
    expect(tester.takeException(), isNull);
    for (final day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']) {
      expect(find.text(day), findsWidgets, reason: day);
    }
    expect(find.byType(DataTable), findsNothing);
    expect(find.text('Esha Thomas'), findsOneWidget);
    expect(find.text('Suresh Rao'), findsOneWidget);
    expect(find.text('Meera Iyer'), findsNWidgets(2));
  });

  testWidgets('wide: periods nothing is taught in at the start and end of the day are left out', (tester) async {
    await pump(tester, const Size(1200, 1800));
    expect(find.text('P1'), findsNothing);
    expect(find.text('P5'), findsNothing);
    expect(find.text('P2'), findsOneWidget);
    expect(find.text('P3'), findsOneWidget, reason: 'an empty period in the middle stays, as a gap in the day');
    expect(find.text('Free'), findsOneWidget);
    expect(find.text('P4'), findsOneWidget);
  });

  test('a subject is the same colour wherever it appears, and the common ones keep their own', () {
    expect(subjectColor('Mathematics'), subjectColor('maths'));
    expect(subjectColor('Science'), isNot(subjectColor('English')));
    expect(subjectColor('Quantum Basket Weaving'), subjectColor('quantum basket weaving'));
    final core = {for (final s in ['English', 'Mathematics', 'Science', 'Hindi', 'Social Science']) subjectColor(s)};
    expect(core, hasLength(5), reason: 'the five core subjects are told apart');
  });

  testWidgets('phone: a row of day chips, one day at a time, and the chosen day is shown', (tester) async {
    await pump(tester, const Size(390, 1800));
    expect(tester.takeException(), isNull);
    for (var d = 0; d < 6; d++) {
      expect(find.byKey(ValueKey('week-day-$d')), findsOneWidget, reason: 'day $d');
    }
    expect(find.byType(DataTable), findsNothing);
    await tester.tap(find.byKey(const ValueKey('week-day-0')));
    await tester.pump();
    expect(find.text('Esha Thomas'), findsOneWidget);
    expect(find.text('Suresh Rao'), findsNothing, reason: 'Tuesday is not on the Monday list');
    await tester.tap(find.byKey(const ValueKey('week-day-1')));
    await tester.pump();
    expect(find.text('Suresh Rao'), findsOneWidget);
    expect(find.text('Esha Thomas'), findsNothing);
  });

  testWidgets('phone: a day with nothing taught says so', (tester) async {
    await pump(tester, const Size(390, 1800));
    await tester.tap(find.byKey(const ValueKey('week-day-4')));
    await tester.pump();
    expect(find.text('No lessons'), findsOneWidget);
  });

  testWidgets('more than five things coming up fold away behind Show all', (tester) async {
    server.answers['/my-calendar'] = [
      for (var i = 1; i <= 7; i++) {'kind': 'holiday', 'title': 'Event $i', 'date': '2026-10-0$i'},
    ];
    await pump(tester, const Size(1200, 1800));
    expect(find.text('Event 5'), findsOneWidget);
    expect(find.text('Event 6'), findsNothing);
    await tester.tap(find.byKey(const ValueKey('week-coming-toggle')));
    await tester.pump();
    expect(find.text('Event 7'), findsOneWidget);
    expect(find.text('Show fewer'), findsOneWidget);
  });

  test('the week shown starts on a Monday, and on a Sunday is next week', () {
    expect(weekDates(DateTime(2026, 10, 7)).first, DateTime(2026, 10, 5), reason: 'a Wednesday');
    expect(weekDates(DateTime(2026, 10, 5)).first, DateTime(2026, 10, 5), reason: 'a Monday');
    expect(weekDates(DateTime(2026, 10, 11)).first, DateTime(2026, 10, 12), reason: 'a Sunday');
    expect(clockMinutes('08:45'), 525);
    expect(clockMinutes(null), isNull);
    expect(clockMinutes('soon'), isNull);
  });
}
