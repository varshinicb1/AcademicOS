// Marks entry and analysis on the web (EX-8; v3 audit N-2-10): a partly
// entered row reads "Incomplete" rather than a total and grade, and the
// analysis shows the topics the API returns as well as the chapters.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/marks_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

final _grid = {
  'paperId': 'p1', 'sectionId': 'sec_a', 'totalMarks': 4, 'withoutConsent': [],
  'questions': [
    {'questionId': 'q1', 'number': 'A1', 'maxMarks': 1},
    {'questionId': 'q2', 'number': 'A2', 'maxMarks': 1},
    {'questionId': 'q3', 'number': 'A3', 'maxMarks': 2},
  ],
  'rows': [
    {'studentId': 'stu_1', 'name': 'Asha', 'absent': false, 'marks': {'q1': 1, 'q2': 1, 'q3': 2},
      'complete': true, 'total': 4, 'percent': 100.0, 'band': 'A1'},
    {'studentId': 'stu_2', 'name': 'Bhavna', 'absent': false, 'marks': {'q3': 1},
      'complete': false, 'total': null, 'percent': null, 'band': null},
    {'studentId': 'stu_3', 'name': 'Charu', 'absent': true, 'marks': {},
      'complete': false, 'total': null, 'percent': null, 'band': null},
  ],
};

final _analysis = {
  'paperId': 'p1', 'sectionId': 'sec_a', 'weakest': ['A3'],
  'questions': [
    {'questionId': 'q1', 'number': 'A1', 'maxMarks': 1, 'attempted': 1, 'mean': 1.0, 'facility': 1.0,
      'chapter': 'Light', 'topic': 'Mirrors'},
    {'questionId': 'q3', 'number': 'A3', 'maxMarks': 2, 'attempted': 2, 'mean': 1.5, 'facility': 0.75,
      'chapter': 'Light', 'topic': 'Laws of reflection'},
  ],
  'chapters': [{'key': 'Light', 'name': 'Light', 'maxMarks': 4, 'facility': 0.8, 'questions': 3}],
  'topics': [
    {'key': 'Laws of reflection', 'name': 'Laws of reflection', 'maxMarks': 2, 'facility': 0.75, 'questions': 1},
    {'key': 'Mirrors', 'name': 'Mirrors', 'maxMarks': 2, 'facility': 1.0, 'questions': 2},
  ],
  'summary': {'students': 3, 'absent': 1, 'incomplete': 1, 'meanPercent': 100.0, 'medianPercent': 100.0,
    'highestPercent': 100.0, 'lowestPercent': 100.0,
    'bands': {'A1': 1, 'A2': 0, 'B1': 0, 'B2': 0, 'C1': 0, 'C2': 0, 'D': 0, 'E': 0}},
};

class _Backend implements HttpClientAdapter {
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  ResponseBody _ok(Object b) => ResponseBody.fromString(jsonEncode(b), 200, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    switch (o.path) {
      case '/curriculum/academic-years':
        return _ok([{'id': 'ay_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'}]);
      case '/curriculum/academic-years/ay_1/sections':
        return _ok([{'id': 'sec_a', 'gradeNumber': 10, 'name': 'A', 'gradeId': 'g10'}]);
      case '/curriculum/grades/g10/subjects':
        return _ok([{'id': 'sub_sci', 'name': 'Science'}]);
      case '/curriculum/academic-years/ay_1/allocations':
        return _ok([]);
      case '/papers/p1/marks':
        return _ok(_grid);
      case '/papers/p1/analysis':
        return _ok(_analysis);
    }
    return ResponseBody.fromString('{"detail":"no route"}', 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('marks_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = _Backend());
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('marks_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> open(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: MarksPage(paperId: 'p1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(DropdownButton<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('10-A').last);
    await tester.pumpAndSettle();
  }

  testWidgets('a partly entered row reads Incomplete, not a total and grade', (tester) async {
    await open(tester);
    expect(find.byKey(const ValueKey('total-stu_1')), findsOneWidget);
    expect(tester.widget<Text>(find.byKey(const ValueKey('total-stu_1'))).data, '4 (A1)');
    expect(tester.widget<Text>(find.byKey(const ValueKey('total-stu_2'))).data, 'Incomplete');
    expect(tester.widget<Text>(find.byKey(const ValueKey('total-stu_3'))).data, '-', reason: 'absent');
    expect(find.textContaining('null'), findsNothing);
  });

  testWidgets('the analysis shows topics as well as chapters, and says who is left out', (tester) async {
    await open(tester);
    await tester.tap(find.text('Analysis'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Mirrors'), 200, scrollable: find.byType(Scrollable).last);
    expect(find.text('By chapter'), findsOneWidget);
    expect(find.text('By topic'), findsOneWidget);
    expect(find.text('Laws of reflection'), findsOneWidget);
    expect(find.text('Mirrors'), findsOneWidget);
    expect(find.text('75%'), findsOneWidget, reason: 'the weakest topic, first');
    await tester.scrollUntilVisible(find.byKey(const ValueKey('incomplete-note')), -200,
        scrollable: find.byType(Scrollable).last);
    expect(find.textContaining('Incomplete: 1, left out of the average'), findsOneWidget);
  });
}
