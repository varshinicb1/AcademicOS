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
  Future<void> save(Uint8List bytes, String filename) async => saved.add('$filename ${bytes.length}');
}

class _Server implements HttpClientAdapter {
  final List<String> writes = [];
  final List<String> reads = [];
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
        'paidOn': '2026-06-01', 'method': 'upi', 'reference': 'UPI 123', 'reversed': false, 'reversalReason': null},
      {'id': 'p0', 'receiptNo': 2, 'feeHeadId': 'h1', 'feeHeadName': 'Tuition, term 1', 'amountPaise': 500000,
        'paidOn': '2026-06-01', 'method': 'cheque', 'reference': 'CHQ 9', 'reversed': true,
        'reversalReason': 'Cheque bounced'},
    ],
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'POST' || o.method == 'PUT') {
      writes.add('${o.method} ${o.path} ${jsonEncode(o.data)}');
      return ResponseBody.fromString(o.method == 'PUT' || o.path.endsWith('/reverse') ? jsonEncode(_statement)
          : '{"id":"p2","receiptNo":2}', 200, headers: _json);
    }
    reads.add(o.path);
    if (o.path.contains('receipt')) {
      return ResponseBody.fromBytes(utf8.encode('%PDF-1.4 x'), 200,
          headers: {Headers.contentTypeHeader: ['application/pdf']});
    }
    return ResponseBody.fromString(jsonEncode(_statement), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Server server;
  late _Saver saver;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('fees_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    saver = _Saver();
    GetIt.instance.registerSingleton<PdfSaver>(saver);
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
        'POST /fees/payments {"studentId":"s1","feeHeadId":"h1","amountPaise":500000,"method":"cash","reference":""}');
  });

  testWidgets('a cancelled receipt shows as cancelled, with its reason', (tester) async {
    await pump(tester, const FeeStatementView(path: '/children/s1/fees'));
    expect(find.textContaining('Cancelled: Cheque bounced'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('a parent downloads a receipt from their own route', (tester) async {
    await pump(tester, const FeeStatementView(path: '/children/s1/fees'));
    await tester.tap(find.byKey(const ValueKey('receipt-menu-1')));
    await tester.pumpAndSettle();
    expect(find.text('Cancel this receipt'), findsNothing, reason: 'a parent cancels nothing');
    await tester.tap(find.text('Download receipt'));
    await settle(tester);
    expect(server.reads.last, '/children/s1/fees/receipts/p1');
    expect(saver.saved, ['receipt-1.pdf 10']);
  });

  testWidgets('the school cancels a receipt with a reason', (tester) async {
    await pump(tester, const FeeStatementView(path: '/fees/students/s1', canRecord: true));
    await tester.tap(find.byKey(const ValueKey('receipt-menu-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancel this receipt'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('save-reverse')));
    await tester.pump();
    expect(find.text('Say why, for example: the cheque bounced.'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('reverse-reason')), 'Wrong student');
    await tester.tap(find.byKey(const ValueKey('save-reverse')));
    await settle(tester);
    expect(server.writes.single, 'POST /fees/payments/p1/reverse {"reason":"Wrong student"}');
  });

  testWidgets('the school gives a concession on one fee', (tester) async {
    await pump(tester, const FeeStatementView(path: '/fees/students/s1', canRecord: true));
    await tester.tap(find.byKey(const ValueKey('fee-h2')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('concession-amount')), '6000');
    await tester.enterText(find.byKey(const ValueKey('concession-reason')), 'Sibling');
    await tester.tap(find.byKey(const ValueKey('save-concession')));
    await tester.pump();
    expect(find.textContaining('Enter rupees from 0 up to the fee'), findsOneWidget, reason: 'above the fee');
    await tester.enterText(find.byKey(const ValueKey('concession-amount')), '1000');
    await tester.tap(find.byKey(const ValueKey('save-concession')));
    await settle(tester);
    expect(server.writes.single,
        'PUT /fees/concessions {"studentId":"s1","feeHeadId":"h2","amountPaise":100000,"reason":"Sibling"}');
  });
}
