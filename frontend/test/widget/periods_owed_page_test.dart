// Periods owed (SCH-7, audit N-3-11): the web could create lost-period debt
// ("Lose the period") but had no call to lost-periods, compensation-options,
// compensate, waive, closures or cover-summary, so debt only grew. This page
// lists what each section and subject is owed, makes a period up in a slot
// the engine proposes or waives it with a reason, closes a day for the whole
// school or some classes, and shows the year's cover figures.
//
// The fake backend answers in the server's shapes (curriculum/cover_routes.py)
// and records what the page sends. Every tab is checked at 390 and 1280 px.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/periods_owed_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

const _narrow = (size: Size(390, 844), textScale: 1.0);
const _narrowLarge = (size: Size(390, 844), textScale: 1.3);
const _wide = (size: Size(1280, 800), textScale: 1.0);

Map<String, dynamic> _lost(String id, String section, String subject, String date, int period,
        {String status = 'owed', String reason = 'lost: no one free'}) =>
    {'id': id, 'sectionId': section, 'subjectId': subject, 'date': date, 'period': period, 'reason': reason,
      'status': status, 'compensationDate': status == 'compensated' ? '2026-10-08' : null,
      'compensationPeriod': status == 'compensated' ? 1 : null};

class _Backend implements HttpClientAdapter {
  final List<(String, String, dynamic)> sent = [];
  final rejected = <String>[];
  List<Map<String, dynamic>> lost = [
    _lost('lp_1', 'sec_a', 'sci', '2026-10-05', 3),
    _lost('lp_2', 'sec_a', 'sci', '2026-10-06', 2, reason: 'closure: heavy rain'),
    _lost('lp_3', 'sec_b', 'mat', '2026-10-05', 1),
    _lost('lp_4', 'sec_b', 'mat', '2026-09-28', 4, status: 'compensated'),
  ];
  int? summaryStatus;
  int? closureStatus;

  static const _json = {Headers.contentTypeHeader: ['application/json']};
  ResponseBody _ok(Object body) => ResponseBody.fromString(jsonEncode(body), 200, headers: _json);
  ResponseBody _err(int status, String detail) =>
      ResponseBody.fromString(jsonEncode({'detail': detail}), status, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    final path = o.path;
    if (o.method != 'GET') sent.add((o.method, path, o.data));
    switch ((o.method, path)) {
      case ('GET', '/curriculum/academic-years'):
        return _ok([{'id': 'ay_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'}]);
      case ('GET', '/curriculum/academic-years/ay_1/sections'):
        return _ok([
          {'id': 'sec_a', 'gradeId': 'g10', 'gradeNumber': 10, 'name': 'A', 'academicYearId': 'ay_1', 'studentCount': 30},
          {'id': 'sec_b', 'gradeId': 'g10', 'gradeNumber': 10, 'name': 'B', 'academicYearId': 'ay_1', 'studentCount': 28},
        ]);
      case ('GET', '/curriculum/grades/g10/subjects'):
        return _ok([
          {'id': 'sci', 'gradeId': 'g10', 'name': 'Science'},
          {'id': 'mat', 'gradeId': 'g10', 'name': 'Maths'},
        ]);
      case ('GET', '/curriculum/academic-years/ay_1/lost-periods'):
        final status = o.queryParameters['status'];
        return _ok([for (final l in lost) if (status == null || l['status'] == status) l]);
      case ('GET', '/curriculum/lost-periods/lp_1/compensation-options'):
        return _ok([{'date': '2026-10-08', 'period': 1}, {'date': '2026-10-09', 'period': 4}]);
      case ('POST', '/curriculum/lost-periods/lp_1/compensate'):
        final b = o.data as Map;
        lost = [for (final l in lost) l['id'] == 'lp_1'
            ? {...l, 'status': 'compensated', 'compensationDate': b['date'], 'compensationPeriod': b['period']} : l];
        return _ok(lost.firstWhere((l) => l['id'] == 'lp_1'));
      case ('POST', '/curriculum/lost-periods/lp_2/waive'):
        lost = [for (final l in lost) l['id'] == 'lp_2' ? {...l, 'status': 'waived'} : l];
        return _ok(lost.firstWhere((l) => l['id'] == 'lp_2'));
      case ('POST', '/curriculum/academic-years/ay_1/closures'):
        if (closureStatus != null) {
          return _err(closureStatus!, 'this action needs the principal, or a teacher the principal has made an admin for it');
        }
        final whole = (o.data as Map)['sectionIds'] == null;
        return _ok({'lostPeriods': whole ? 16 : 8, 'holidayAdded': whole, 'plansReflowed': whole ? 10 : 5});
      case ('GET', '/curriculum/academic-years/ay_1/cover-summary'):
        if (summaryStatus != null) {
          return _err(summaryStatus!, 'this action needs the principal, or a teacher the principal has made an admin for it');
        }
        return _ok({
          'substitutionsRequested': 19, 'filled': 16, 'supervised': 1, 'unfilled': 2, 'lost': 4,
          'compensated': 1, 'owed': 3,
          'debt': [
            {'sectionId': 'sec_a', 'subjectId': 'sci', 'owed': 2, 'compensated': 0, 'waived': 0},
            {'sectionId': 'sec_b', 'subjectId': 'mat', 'owed': 1, 'compensated': 1, 'waived': 0},
          ],
        });
    }
    rejected.add('${o.method} $path');
    return _err(404, 'no route ${o.method} $path');
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('periods_owed_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
  });

  tearDown(() async {
    expect(backend.rejected, isEmpty, reason: 'the page called a route the fake does not serve');
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('periods_owed_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  Future<void> openTab(WidgetTester tester, String name) async {
    final tab = find.widgetWithText(Tab, name);
    await tester.ensureVisible(tab);
    await tester.pumpAndSettle();
    await tester.tap(tab);
    await tester.pumpAndSettle();
  }

  testWidgets('owed periods are grouped by section and subject', (tester) async {
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    expect(find.text('10-A · Science: 2 owed'), findsOneWidget);
    expect(find.text('10-B · Maths: 1 owed'), findsOneWidget);
    expect(find.text('2026-10-05 (Mon) · period 3'), findsOneWidget);
    expect(find.text('closure: heavy rain'), findsOneWidget);

    await tester.tap(find.text('Made up'));
    await tester.pumpAndSettle();
    expect(find.text('10-B · Maths: 1 made up'), findsOneWidget);
    expect(find.text('Made up on 2026-10-08 (Thu) · period 1'), findsOneWidget);
    expect(find.byKey(const ValueKey('owed-makeup-lp_4')), findsNothing, reason: 'nothing to make up');

    await tester.tap(find.text('Waived'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('owed-empty')), findsOneWidget);
  });

  testWidgets('a period is made up in a slot the engine proposes', (tester) async {
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    await tapKey(tester, 'owed-makeup-lp_1');
    expect(find.text('2026-10-08 (Thu) · P1'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('makeup-save'))).onPressed, isNull,
        reason: 'nothing is sent before a slot is chosen');
    await tester.tap(find.byKey(const ValueKey('makeup-2026-10-09-4')));
    await tester.pumpAndSettle();
    await tapKey(tester, 'makeup-save');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('POST', '/curriculum/lost-periods/lp_1/compensate'));
    expect(body, {'date': '2026-10-09', 'period': 4});
    expect(find.text('10-A · Science: 1 owed'), findsOneWidget, reason: 'the list is read again');
  });

  testWidgets('a period is waived only with a reason, and the reason is sent', (tester) async {
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    await tapKey(tester, 'owed-waive-lp_2');
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('waive-save'))).onPressed, isNull);
    await tester.enterText(find.byKey(const ValueKey('waive-reason')), 'Covered in the revision week');
    await tester.pump();
    await tapKey(tester, 'waive-save');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('POST', '/curriculum/lost-periods/lp_2/waive'));
    expect(body, {'reason': 'Covered in the revision week'});
    expect(find.text('closure: heavy rain'), findsNothing);
  });

  testWidgets('some classes are closed for a day, after a confirmation', (tester) async {
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    await openTab(tester, 'Close a day');
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('closure-save'))).onPressed, isNull,
        reason: 'a closure needs a reason');
    await tester.tap(find.text('Some classes'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('closure-reason')), 'Class 10 trip');
    await tester.pump();
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('closure-save'))).onPressed, isNull,
        reason: 'some classes means at least one');
    await tapKey(tester, 'closure-section-sec_a');
    await tapKey(tester, 'closure-save');
    expect(find.textContaining('for 10-A?'), findsOneWidget);
    await tapKey(tester, 'closure-confirm');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('POST', '/curriculum/academic-years/ay_1/closures'));
    expect((body as Map)['sectionIds'], ['sec_a']);
    expect(body['reason'], 'Class 10 trip');
    expect(body['date'], matches(RegExp(r'^\d{4}-\d{2}-\d{2}$')));
    expect(find.text('8 periods are now owed.'), findsOneWidget);
    expect(find.text('• 5 lesson plans moved past the day.'), findsOneWidget);
    expect(find.textContaining('on the calendar as a holiday.'), findsNothing);
  });

  testWidgets('the whole school closes; a refusal says why', (tester) async {
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    await openTab(tester, 'Close a day');
    await tester.enterText(find.byKey(const ValueKey('closure-reason')), 'Heavy rain');
    await tester.pump();
    await tapKey(tester, 'closure-save');
    await tapKey(tester, 'closure-confirm');
    expect((backend.sent.single.$3 as Map).containsKey('sectionIds'), isFalse);
    expect(find.text('• The day is on the calendar as a holiday.'), findsOneWidget);

    backend.closureStatus = 403;
    await tapKey(tester, 'closure-save');
    await tapKey(tester, 'closure-confirm');
    expect(find.text('The day was not closed.'), findsOneWidget);
    expect(find.textContaining('made an admin for it'), findsOneWidget);
  });

  testWidgets("the year's figures and the debt per section and subject", (tester) async {
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    await openTab(tester, 'The year');
    expect(find.text('Cover asked for'), findsOneWidget);
    expect(find.text('19'), findsOneWidget);
    expect(find.text('Still owed'), findsOneWidget);
    expect(find.text('10-A · Science'), findsOneWidget);
    expect(find.text('1 owed · 1 made up · 0 waived'), findsOneWidget);
  });

  testWidgets('without the reports permission the year says so, and the rest still works', (tester) async {
    backend.summaryStatus = 403;
    await pumpPage(tester, const PeriodsOwedPage(), _narrow);
    await openTab(tester, 'The year');
    expect(find.textContaining('made an admin for it'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  for (final (name, screen) in [('390 px', _narrow), ('390 px at 1.3x text', _narrowLarge), ('1280 px', _wide)]) {
    testWidgets('nothing overflows at $name on any tab or dialog', (tester) async {
      await pumpPage(tester, const PeriodsOwedPage(), screen);
      expectNoOverflow(tester, where: ' on Owed');
      await tapKey(tester, 'owed-makeup-lp_1');
      expectNoOverflow(tester, where: ' in the make-up dialog');
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      await tapKey(tester, 'owed-waive-lp_2');
      expectNoOverflow(tester, where: ' in the waive dialog');
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      await openTab(tester, 'Close a day');
      await tester.tap(find.text('Some classes'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' on Close a day');
      await tester.enterText(find.byKey(const ValueKey('closure-reason')), 'Heavy rain');
      await tester.pump();
      await tapKey(tester, 'closure-section-sec_b');
      await scrollToAndExpectReady(tester, find.byKey(const ValueKey('closure-save')), screen, label: 'Close the day');
      await openTab(tester, 'The year');
      expectNoOverflow(tester, where: ' on The year');
    });
  }
}
