// A parent gives or withdraws consent from My children (QA S-01, 2026-10-01).
//
// The consent dialog's buttons popped the chip's context. In the app that
// context sits under the shell's own navigator while the dialog is on the
// root one, so Withdraw, I agree and Cancel each closed the page behind the
// dialog, left the dialog open, and sent no request: a parent could not
// change their DPDP consent at all. The page here sits under a nested
// navigator, as it does in the shell, so the old code fails these tests.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/family_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart' show useAppFonts;

class _Server implements HttpClientAdapter {
  String consent = 'granted';
  final List<String> writes = [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method != 'GET') {
      writes.add('${o.method} ${o.path}');
      if (o.path == '/children/s1/consent') consent = o.method == 'DELETE' ? 'withdrawn' : 'granted';
      return ResponseBody.fromString('{"ok":true}', 200, headers: _json);
    }
    final Object answer = switch (o.path) {
      '/my-children' => [
          {'studentId': 's1', 'name': 'Asha', 'sectionName': '10-A', 'grade': 10, 'consent': consent},
        ],
      '/children/s1/timetable' => {'entries': <Object>[], 'subjectNames': <String, Object>{}},
      '/children/s1/calendar' => [
          {'kind': 'holiday', 'title': 'Gandhi Jayanti', 'date': '2026-10-02'},
          {'kind': 'exam', 'title': 'Science, Half-yearly', 'date': '2026-10-08', 'startTime': '09:30',
            'endTime': '12:30'},
        ],
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
    tmp = Directory.systemTemp.createTempSync('family_consent_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'p1', 'schoolId': 'school_1', 'role': 'parent', 'name': 'Meena'};
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

  /// My children under a nested navigator, with a page beneath it -- as the
  /// shell's ShellRoute leaves the School overview beneath /school/family.
  Future<void> pumpFamily(WidgetTester tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: Navigator(
        onGenerateInitialRoutes: (_, __) => [
          MaterialPageRoute<void>(builder: (_) => const Scaffold(body: Text('School overview'))),
          MaterialPageRoute<void>(builder: (_) => const FamilyPage()),
        ],
      ),
    ));
    await settle(tester);
  }

  testWidgets('Withdraw closes the dialog, sends the withdrawal and keeps the page', (tester) async {
    await pumpFamily(tester);
    await tester.tap(find.text('Consent given'));
    await tester.pumpAndSettle();
    expect(find.text('Withdraw consent?'), findsOneWidget);
    await tester.tap(find.text('Withdraw'));
    await settle(tester);
    expect(find.text('Withdraw consent?'), findsNothing, reason: 'the dialog closes');
    expect(server.writes, ['DELETE /children/s1/consent']);
    expect(find.text('Consent needed'), findsOneWidget, reason: 'the chip shows the new state');
    expect(find.text('School overview'), findsNothing, reason: 'the page behind is not popped');
  });

  testWidgets('Cancel closes only the dialog and sends nothing', (tester) async {
    await pumpFamily(tester);
    await tester.tap(find.text('Consent given'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancel'));
    await settle(tester);
    expect(find.text('Withdraw consent?'), findsNothing);
    expect(server.writes, isEmpty);
    expect(find.text('Consent given'), findsOneWidget);
  });

  testWidgets('I agree gives consent', (tester) async {
    server.consent = 'withdrawn';
    await pumpFamily(tester);
    await tester.tap(find.text('Consent needed'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('I agree'));
    await settle(tester);
    expect(server.writes, ['POST /children/s1/consent']);
    expect(find.text('Consent given'), findsOneWidget);
  });

  testWidgets('at 375 px every tab label is whole', (tester) async {
    await pumpFamily(tester);
    expect(tester.takeException(), isNull);
    for (final label in ['Week', 'Today', 'Calendar', 'Homework', 'Progress', 'Attendance']) {
      final text = tester.renderObject<RenderParagraph>(
          find.descendant(of: find.byKey(const ValueKey('child-tabs')), matching: find.text(label)));
      expect(text.didExceedMaxLines, isFalse, reason: label);
      expect(text.size.width, greaterThanOrEqualTo(text.getMaxIntrinsicWidth(double.infinity) - 0.5), reason: label);
    }
  });

  testWidgets("the Calendar tab shows the child's holidays and exams (SA-6)", (tester) async {
    await pumpFamily(tester);
    await tester.tap(find.descendant(of: find.byKey(const ValueKey('child-tabs')), matching: find.text('Calendar')));
    await settle(tester);
    expect(find.text('Gandhi Jayanti'), findsOneWidget);
    expect(find.text('Friday 2 October'), findsOneWidget);
    expect(find.text('Science, Half-yearly'), findsOneWidget);
    expect(find.text('Thursday 8 October · 09:30-12:30'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
