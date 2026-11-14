// Report cards on the web (EX-8): a student's or parent's view of the term's
// card and its PDF; a principal's or class teacher's page that downloads a
// section's cards; the server's refusals shown as it words them.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:academicos/core/download/pdf_saver.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/report_cards_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _Saver implements PdfSaver {
  final List<(int, String)> saved = [];
  @override
  Future<void> save(Uint8List bytes, String filename) async => saved.add((bytes.length, filename));
}

final _card = {
  'studentId': 'stu_1', 'studentName': 'Asha', 'section': '10-A', 'termId': 'term_1', 'termName': 'Term 1',
  'yearLabel': '2026-27', 'obtained': 56, 'maximum': 70, 'percent': 80.0, 'band': 'B1',
  'note': 'Marks entered in AcademicOS for papers set this term.',
  'subjects': [
    {'subject': 'Mathematics', 'obtained': 18, 'maximum': 20, 'percent': 90.0, 'band': 'A2', 'papers': [
      {'paperId': 'p1', 'title': 'Maths UT', 'examType': 'unit_test', 'examTypeLabel': 'Unit test', 'setOn': '2026-05-12',
        'obtained': null, 'maximum': 20, 'absent': true},
      {'paperId': 'p2', 'title': 'Maths PT', 'examType': 'periodic', 'examTypeLabel': 'Periodic test', 'setOn': '2026-07-01',
        'obtained': 18, 'maximum': 20, 'absent': false},
      // Marks entered for some of its questions only: no total (v3 audit N-2-10).
      {'paperId': 'p3', 'title': 'Maths CT', 'examType': 'class_test', 'examTypeLabel': 'Class test', 'setOn': '2026-07-10',
        'obtained': null, 'maximum': 10, 'absent': false, 'incomplete': true},
    ]},
  ],
};

class _Backend implements HttpClientAdapter {
  final List<String> gets = [];
  final List<Object?> puts = [];
  Map<String, dynamic> remarks = {
    'termId': 'term_1', 'termName': 'Term 1', 'section': '10-A',
    'rows': [
      {'studentId': 'stu_1', 'studentName': 'Asha', 'percent': 80.0, 'band': 'B1', 'remark': null,
        'draft': 'Asha scored 80% overall this term (grade B1).'},
      {'studentId': 'stu_2', 'studentName': 'Bhavna', 'percent': 67.0, 'band': 'B2', 'remark': 'Works hard.',
        'draft': 'Bhavna scored 67% overall this term (grade B2).'},
      {'studentId': 'stu_3', 'studentName': 'Charu', 'percent': null, 'band': null, 'remark': null, 'draft': null},
    ],
  };
  int? sectionPdfStatus;
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  ResponseBody _ok(Object b) => ResponseBody.fromString(jsonEncode(b), 200, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    gets.add('${o.path}${o.queryParameters.isEmpty ? '' : '?${o.queryParameters.entries.map((e) => '${e.key}=${e.value}').join('&')}'}');
    switch (o.path) {
      case '/report-cards/students/stu_1':
        return _ok(_card);
      case '/report-cards/sections/sec_a/remarks':
        if (o.method == 'PUT') {
          puts.add(o.data);
          final rows = (remarks['rows'] as List).cast<Map<String, dynamic>>();
          for (final e in ((o.data as Map)['remarks'] as List).cast<Map>()) {
            final row = rows.firstWhere((r) => r['studentId'] == e['studentId']);
            row['remark'] = (e['remark'] as String).isEmpty ? null : e['remark'];
          }
        }
        return _ok(remarks);
      case '/report-cards/students/stu_1/pdf':
      case '/report-cards/sections/sec_a/pdf':
        if (o.path.startsWith('/report-cards/sections') && sectionPdfStatus != null) {
          return ResponseBody.fromString(jsonEncode({'detail': 'report cards are for the principal, a teacher given '
              'reports, and the section\'s class teacher'}), sectionPdfStatus!, headers: _json);
        }
        return ResponseBody.fromBytes(Uint8List.fromList(utf8.encode('%PDF-1.4 fake')), 200,
            headers: {Headers.contentTypeHeader: ['application/pdf']});
      case '/curriculum/academic-years':
        return _ok([{'id': 'ay_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'}]);
      case '/curriculum/academic-years/ay_1/terms':
        return _ok([
          {'id': 'term_1', 'name': 'Term 1', 'startDate': '2000-01-01', 'endDate': '2099-12-31'},
          {'id': 'term_2', 'name': 'Term 2', 'startDate': '2100-01-01', 'endDate': '2100-06-30'},
        ]);
      case '/curriculum/academic-years/ay_1/sections':
        return _ok([{'id': 'sec_a', 'gradeNumber': 10, 'name': 'A', 'gradeId': 'g10'}]);
    }
    return ResponseBody.fromString('{"detail":"no route"}', 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Backend backend;
  late _Saver saver;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('report_cards_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    saver = _Saver();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
    GetIt.instance.registerSingleton<PdfSaver>(saver);
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
      print('report_cards_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pump(WidgetTester tester, Widget page) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(home: page));
    await tester.pumpAndSettle();
  }

  testWidgets("a student's card shows each subject, an absence, an incomplete paper, the overall, and downloads",
      (tester) async {
    await pump(tester, const StudentReportCardPage(studentId: 'stu_1', name: 'Asha'));
    expect(find.text('Term 1, 2026-27 · Class 10-A'), findsOneWidget);
    expect(find.text('18/20  90%  A2'), findsOneWidget);
    expect(find.text('Unit test: absent/20'), findsOneWidget);
    expect(find.text('Class test: incomplete/10'), findsOneWidget);
    expect(find.text('Overall: 56/70  80%  B1'), findsOneWidget);
    expect(tester.takeException(), isNull, reason: 'fits a phone');
    await tester.tap(find.byKey(const ValueKey('card-pdf')));
    await tester.pumpAndSettle();
    expect(saver.saved.single.$2, 'report-card.pdf');
  });

  testWidgets("a section's cards download for the term today is in", (tester) async {
    await pump(tester, const ReportCardsPage());
    expect(find.text('Term 1'), findsOneWidget, reason: 'the term containing today is chosen');
    await tester.tap(find.byKey(const ValueKey('rc-section')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('10-A').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('rc-download')));
    await tester.pumpAndSettle();
    expect(backend.gets, contains('/report-cards/sections/sec_a/pdf?termId=term_1'));
    expect(saver.saved.single.$2, 'report-cards.pdf');
    expect(find.text('Downloaded.'), findsOneWidget);
  });

  testWidgets("a student's card shows the class teacher's remark once one is saved", (tester) async {
    _card['remark'] = 'Asha works steadily.';
    addTearDown(() => _card.remove('remark'));
    await pump(tester, const StudentReportCardPage(studentId: 'stu_1', name: 'Asha'));
    expect(find.text("Class teacher's remark"), findsOneWidget);
    expect(find.text('Asha works steadily.'), findsOneWidget);
  });

  testWidgets('remarks open on the saved one or a draft from the marks, and save what changed', (tester) async {
    await pump(tester, const ReportRemarksPage(sectionId: 'sec_a', termId: 'term_1'));
    expect(tester.takeException(), isNull, reason: 'fits a phone');
    expect(backend.gets, contains('/report-cards/sections/sec_a/remarks?termId=term_1'));
    expect(find.text('Asha scored 80% overall this term (grade B1).'), findsOneWidget, reason: 'the draft');
    expect(find.text('Works hard.'), findsOneWidget, reason: 'the saved remark, not the draft');
    expect(find.text('Draft from the marks: not saved yet'), findsOneWidget);
    expect(find.text('No marks this term yet: write one, or leave it empty'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('remark-stu_2')), 'Works hard; more reading.');
    await tester.tap(find.byKey(const ValueKey('remarks-save')));
    await tester.pumpAndSettle();
    expect(backend.puts.single, {'remarks': [
      {'studentId': 'stu_1', 'remark': 'Asha scored 80% overall this term (grade B1).'},
      {'studentId': 'stu_2', 'remark': 'Works hard; more reading.'},
    ]}, reason: 'the kept draft and the edit; the empty box with nothing saved is not sent');
    expect(find.text('Remarks saved'), findsOneWidget);
    expect(find.text('Saved'), findsNWidgets(2));
  });

  testWidgets("a teacher who is not the class teacher is told why", (tester) async {
    backend.sectionPdfStatus = 403;
    await pump(tester, const ReportCardsPage());
    await tester.tap(find.byKey(const ValueKey('rc-section')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('10-A').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('rc-download')));
    await tester.pumpAndSettle();
    expect(find.textContaining("the section's class teacher"), findsOneWidget);
    expect(saver.saved, isEmpty);
  });
}
