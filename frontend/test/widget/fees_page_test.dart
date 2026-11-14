// FEE-1: a parent reads a child's fees (what is owed, overdue, the
// receipts); the school records a payment from a student's statement.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'dart:typed_data';

import 'package:academicos/core/download/pdf_saver.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/fees_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart' show useAppFonts;

class _Saver implements PdfSaver {
  final List<String> saved = [];

  @override
  Future<void> save(Uint8List bytes, String filename) async => saved.add(filename);
}

class _Server implements HttpClientAdapter {
  final List<String> writes = [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  static const _statement = {
    'studentId': 's1', 'studentName': 'Asha',
    'rows': [
      {'head': {'id': 'h1', 'academicYearId': 'y1', 'grade': 10, 'name': 'Tuition, term 1', 'amountPaise': 1500000,
          'dueDate': '2026-05-15'},
        'concessionPaise': 0, 'paidPaise': 1000000, 'balancePaise': 500000, 'status': 'overdue'},
      {'head': {'id': 'h2', 'academicYearId': 'y1', 'grade': null, 'name': 'Annual charges', 'amountPaise': 500000,
          'dueDate': '2026-06-30'},
        'concessionPaise': 0, 'paidPaise': 0, 'balancePaise': 500000, 'status': 'due'},
    ],
    'totalPaise': 2000000, 'concessionPaise': 0, 'paidPaise': 1000000, 'balancePaise': 1000000,
    'overduePaise': 500000,
    'receipts': [
      {'id': 'p1', 'receiptNo': 1, 'feeHeadId': 'h1', 'feeHeadName': 'Tuition, term 1', 'amountPaise': 1000000,
        'paidOn': '2026-06-01', 'method': 'upi', 'reference': 'UPI 123'},
    ],
  };

  static const _overview = {
    'date': '2026-06-01', 'totalPaise': 1700000, 'concessionPaise': 0, 'paidPaise': 1000000, 'balancePaise': 700000,
    'overduePaise': 500000, 'collectedPercent': 58.8,
    'classes': [
      {'sectionId': 'sb', 'sectionName': '10-B', 'students': 1, 'totalPaise': 1700000, 'paidPaise': 1000000,
        'balancePaise': 700000, 'overduePaise': 500000, 'studentsOverdue': 1},
    ],
    'defaulters': [
      {'studentId': 's1', 'name': 'Asha', 'sectionName': '10-B', 'overduePaise': 500000, 'balancePaise': 700000,
        'overdueHeads': ['Tuition, term 1']},
    ],
    'defaultersTotal': 1,
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'POST') {
      writes.add('${o.path} ${jsonEncode(o.data)}');
      return ResponseBody.fromString('{"id":"p2","receiptNo":2}', 200, headers: _json);
    }
    if (o.path == '/fees/defaulters/export') {
      writes.add('${o.path} ${o.queryParameters['format']}');
      return ResponseBody.fromBytes(utf8.encode('PK-fake'), 200);
    }
    if (o.path == '/fees/overview') return ResponseBody.fromString(jsonEncode(_overview), 200, headers: _json);
    return ResponseBody.fromString(jsonEncode(_statement), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Server server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('fees_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'p1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
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

  Future<void> pump(WidgetTester tester, Widget page) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.darkTheme, home: Scaffold(body: page)));
    await settle(tester);
  }

  test('rupees are grouped the Indian way', () {
    expect(formatRupees(150000000), 'Rs 15,00,000');
    expect(formatRupees(1500000), 'Rs 15,000');
    expect(formatRupees(99950), 'Rs 999.50');
  });

  testWidgets('a parent sees what is owed, what is overdue and the receipts', (tester) async {
    await pump(tester, const FeeStatementView(path: '/children/s1/fees'));
    expect(find.text('Rs 10,000 to pay'), findsOneWidget);
    expect(find.text('Rs 5,000 overdue'), findsOneWidget);
    expect(find.text('Overdue'), findsOneWidget);
    expect(find.text('Receipt 1 · Rs 10,000'), findsOneWidget);
    expect(find.byKey(const ValueKey('record-payment')), findsNothing, reason: 'a parent records nothing');
    expect(tester.takeException(), isNull);
  });

  testWidgets('the school records a payment against the first unpaid fee', (tester) async {
    await pump(tester, const FeeStatementView(path: '/fees/students/s1', canRecord: true));
    await tester.tap(find.byKey(const ValueKey('record-payment')));
    await settle(tester);
    expect(tester.widget<TextField>(find.byKey(const ValueKey('payment-amount'))).controller!.text, '5000');
    await tester.tap(find.byKey(const ValueKey('save-payment')));
    await settle(tester);
    expect(server.writes.single,
        '/fees/payments {"studentId":"s1","feeHeadId":"h1","amountPaise":500000,"method":"cash","reference":""}');
  });

  // FEE-1 oversight: the principal's view of the whole school's fees.
  testWidgets('the principal sees the year at a glance and downloads who is overdue', (tester) async {
    final saver = _Saver();
    GetIt.instance.registerSingleton<PdfSaver>(saver);
    await pump(tester, const FeesOverviewView());
    expect(tester.takeException(), isNull);
    expect(find.text('Rs 17,000'), findsOneWidget, reason: 'billed');
    expect(find.text('Rs 10,000'), findsOneWidget, reason: 'collected');
    expect(find.text('58.8% collected'), findsOneWidget);
    expect(find.text('Overdue: 1 students'), findsOneWidget);
    expect(find.text('10-B · Tuition, term 1'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('download-defaulters')));
    await settle(tester);
    expect(server.writes, contains('/fees/defaulters/export xlsx'));
    expect(saver.saved, ['fee-defaulters.xlsx']);
  });
}
