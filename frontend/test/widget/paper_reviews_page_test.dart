// Paper reviews (EX-6), the QA pass of 2026-10-01:
//   * P-08: "Ask for changes" -> "Send back" closed the page behind the
//     dialog and left the dialog open; nothing was sent. The dialog now pops
//     itself and the decision reaches the server.
//   * P-12: a paper a colleague approved for the principal was nowhere in
//     the principal's "Waiting". The server marks those rows
//     `awaitingPrincipal`; they show with "Approve & lock", and the list
//     updates once the paper is locked.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/admin_pages.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../support/semantics_labels.dart';

Map<String, dynamic> _review(String id, String state, {bool awaitingPrincipal = false}) => {
      'id': id,
      'assessmentId': 'asm_$id',
      'title': 'Half-Yearly Examination',
      'authorId': 'u_meera',
      'reviewerId': 'u_suresh',
      'reviewerName': 'Suresh Rao',
      'state': state,
      'requestNote': 'Please check section E',
      'comment': null,
      'requestedAt': '2026-10-01T20:50:00Z',
      'decidedAt': null,
      if (awaitingPrincipal) 'awaitingPrincipal': true,
    };

class _Backend implements HttpClientAdapter {
  static const _json = {Headers.contentTypeHeader: ['application/json']};
  final List<(String, String, Object?)> requests = [];
  List<Map<String, dynamic>> waiting;

  _Backend(this.waiting);

  ResponseBody _ok(Object b) => ResponseBody.fromString(jsonEncode(b), 200, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    requests.add((o.method, o.path, o.data));
    if (o.method == 'GET' && o.path == '/paper-reviews') return _ok(waiting);
    if (o.method == 'POST' && o.path.endsWith('/review-decision')) {
      final id = o.path.split('/')[2];
      waiting = [for (final r in waiting) if (r['assessmentId'] != id) r];
      return _ok(_review('r1', 'changes_requested'));
    }
    if (o.method == 'PATCH' && o.path.endsWith('/approve')) {
      final id = o.path.split('/')[2];
      waiting = [for (final r in waiting) if (r['assessmentId'] != id) r];
      return _ok({'id': id, 'status': 'principalApproved'});
    }
    return ResponseBody.fromString('{"detail":"no route"}', 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('paper_reviews_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
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
      print('paper_reviews_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  /// The reviews page pushed over another page, as the app opens it: a pop
  /// with the wrong context closes it and lands on 'School'.
  Future<_Backend> open(WidgetTester tester, {required Map<String, String> user,
      required List<Map<String, dynamic>> waiting}) async {
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final backend = _Backend(waiting);
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
    LocalStore.instance.authUser = user;
    await tester.pumpWidget(MaterialApp(
      home: Builder(
        builder: (context) => Scaffold(
          body: Center(
            child: TextButton(
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ReviewsPage())),
              child: const Text('School'),
            ),
          ),
        ),
      ),
    ));
    await tester.tap(find.text('School'));
    await tester.pumpAndSettle();
    return backend;
  }

  testWidgets('Ask for changes sends the comment and closes only the dialog (P-08)', (tester) async {
    final backend = await open(tester,
        user: {'id': 'u_suresh', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Suresh Rao'},
        waiting: [_review('r1', 'pending')]);
    expect(find.text('Waiting'), findsWidgets);
    await tester.tap(find.text('Ask for changes'));
    await tester.pumpAndSettle();

    final send = find.widgetWithText(FilledButton, 'Send back');
    expect(tester.widget<FilledButton>(send).onPressed, isNull, reason: 'an empty comment is refused anyway');
    await tester.enterText(find.byKey(const ValueKey('review-comment')), 'Q26 needs its table');
    await tester.pumpAndSettle();
    await tester.tap(send);
    await tester.pumpAndSettle();

    expect(find.text('What should change?'), findsNothing, reason: 'the dialog closed');
    expect(find.text('Paper reviews'), findsOneWidget, reason: 'the page behind it did not');
    final decision = backend.requests.where((r) => r.$2 == '/assessments/asm_r1/review-decision').single;
    expect(decision.$3, {'decision': 'changes', 'comment': 'Q26 needs its table'});
    expect(find.text('Sent back to the author with your comments'), findsOneWidget);
    expect(find.text('Nothing to review'), findsOneWidget, reason: 'the list was read again');
  });

  testWidgets('the "What should change?" field is labelled for a screen reader (P-28)', (tester) async {
    final semantics = tester.ensureSemantics();
    await open(tester,
        user: {'id': 'u_suresh', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Suresh Rao'},
        waiting: [_review('r1', 'pending')]);
    await tester.tap(find.text('Ask for changes'));
    await tester.pumpAndSettle();
    expect(textFieldLabels(tester), contains(contains('What should change?')));
    semantics.dispose();
  });

  testWidgets("a paper a colleague approved waits in the principal's list with Approve & lock (P-12)",
      (tester) async {
    final backend = await open(tester,
        user: {'id': 'u_priya', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya Menon'},
        waiting: [_review('r2', 'approved', awaitingPrincipal: true)]);

    expect(find.text('Approved by reviewer'), findsOneWidget, reason: 'the chip says what happened, not "approved"');
    expect(find.text('Suresh Rao approved it for you. Approving locks the paper.'), findsOneWidget);
    expect(find.text('Ask for changes'), findsNothing, reason: 'the review itself is decided');
    await tester.tap(find.byKey(const ValueKey('approve-lock-r2')));
    await tester.pumpAndSettle();

    expect(backend.requests.where((r) => r.$1 == 'PATCH').single.$2, '/assessments/asm_r2/approve');
    expect(find.text('Approved and locked: Half-Yearly Examination'), findsOneWidget);
    expect(find.text('Nothing to review'), findsOneWidget, reason: 'the locked paper left the list at once');
  });

  testWidgets('a row without awaitingPrincipal is treated as already done', (tester) async {
    await open(tester,
        user: {'id': 'u_priya', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya Menon'},
        waiting: [_review('r3', 'approved')]);
    expect(find.text('Approved'), findsOneWidget);
    expect(find.text('Approve & lock'), findsNothing);
  });
}
