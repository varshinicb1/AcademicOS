// ATT-1: a teacher takes a class's register (everyone starts present; one
// tap marks a student absent) and a student or parent reads the record.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/attendance_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart' show useAppFonts;

class _Server implements HttpClientAdapter {
  final List<Map<String, dynamic>> saved = [];
  List<String> withoutConsent = const [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  Map<String, dynamic> _register(Map<String, String> statuses) => {
        'sectionId': 'sec-b', 'sectionName': '10-B', 'date': '2026-06-01', 'taken': statuses.isNotEmpty,
        'rows': [
          {'studentId': 's1', 'name': 'Asha', 'status': statuses['s1'], 'note': ''},
          {'studentId': 's2', 'name': 'Bina', 'status': statuses['s2'], 'note': ''},
        ],
        'counts': {'present': 0, 'late': 0, 'absent': 0, 'excused': 0},
        'withoutConsent': withoutConsent,
      };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'PUT') {
      final sent = Map<String, dynamic>.from(o.data as Map);
      saved.add(sent);
      final statuses = {
        for (final e in (sent['entries'] as List).cast<Map>())
          if (!withoutConsent.contains(e['studentId'] == 's1' ? 'Asha' : 'Bina')) e['studentId'] as String: e['status'] as String,
      };
      return ResponseBody.fromString(jsonEncode(_register(statuses)), 200, headers: _json);
    }
    final Object answer = switch (o.path) {
      '/curriculum/academic-years' => [
          {'id': 'y1', 'startDate': '2026-04-01'},
        ],
      '/curriculum/academic-years/y1/sections' => [
          {'id': 'sec-b', 'gradeNumber': 10, 'name': 'B', 'classTeacherId': 't1'},
          {'id': 'sec-a', 'gradeNumber': 10, 'name': 'A', 'classTeacherId': 't9'},
        ],
      '/curriculum/academic-years/y1/allocations' => <Object>[],
      '/sections/sec-b/attendance' => _register(const {}),
      '/my-attendance-record' => {
          'studentId': 's1', 'start': '2025-05-01', 'end': '2026-06-01', 'daysTaken': 5,
          'counts': {'present': 2, 'late': 1, 'absent': 1, 'excused': 1}, 'percent': 75.0,
          'recent': [
            {'date': '2026-05-28', 'status': 'absent', 'note': ''},
            {'date': '2026-05-27', 'status': 'late', 'note': 'bus'},
          ],
        },
      _ => <Object>[],
    };
    return ResponseBody.fromString(jsonEncode(answer), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Server server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('attendance_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 't1', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Ana'};
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

  Future<void> settle(WidgetTester tester) async {
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    for (var i = 0; i < 4; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
  }

  Future<void> pump(WidgetTester tester, Widget page, {double width = 375}) async {
    tester.view.physicalSize = Size(width, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.darkTheme, home: page));
    await settle(tester);
  }

  testWidgets('the class teacher opens their class; everyone starts present; one tap marks an absence',
      (tester) async {
    await pump(tester, const AttendanceRegisterPage());
    expect(tester.takeException(), isNull);
    expect(find.text('Not taken yet. Everyone starts as present.'), findsOneWidget);
    expect(find.text('10-A'), findsNothing, reason: 'a class Ana neither teaches nor leads');
    expect(find.text('Save: everyone present'), findsOneWidget);

    await tester.tap(find.descendant(of: find.byKey(const ValueKey('register-s2')), matching: find.text('Absent')));
    await tester.pump();
    expect(find.text('Save: 1 absent'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('save-register')));
    await settle(tester);
    expect(server.saved.single['entries'], [
      {'studentId': 's1', 'status': 'present'},
      {'studentId': 's2', 'status': 'absent'},
    ]);
    expect(find.text('Register saved. Parents of absent students have been told.'), findsOneWidget);
    expect(find.text('Taken. Change any row and save again.'), findsOneWidget);
  });

  testWidgets('a student left out for want of consent is named, with what to do', (tester) async {
    server.withoutConsent = const ['Bina'];
    await pump(tester, const AttendanceRegisterPage(), width: 1280);
    await tester.tap(find.byKey(const ValueKey('save-register')));
    await settle(tester);
    expect(find.textContaining('no parental consent on file: Bina. Record their consent under Classes'),
        findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets("a student's record: the share attended and the days away or late", (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    await pump(tester, const Scaffold(body: AttendanceRecordView(path: '/my-attendance-record')));
    expect(find.text('75% of school days attended'), findsOneWidget);
    expect(find.text('5 days taken · 2 present · 1 late · 1 absent · 1 on leave'), findsOneWidget);
    expect(find.text('Late · bus'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
