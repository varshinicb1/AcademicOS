// API-6 on the web: a principal adds a partner's webhook to an API key, sees
// the signing secret once (never in the list again), and reads the delivery
// log -- what was sent, whether it arrived, and what is being retried.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/webhooks_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

const _secret = 'whsec_shown_once_abcdefghijklmnopqrstuvwxyz0123456789';

class _FakeServer implements HttpClientAdapter {
  final List<String> sent = [];
  final List<Map<String, dynamic>> hooks = [];

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    sent.add('${o.method} ${o.path}${o.data == null ? '' : ' ${jsonEncode(o.data)}'}');
    Object? data;
    if (o.method == 'GET' && o.path == '/api-keys/k1/webhooks') {
      data = hooks;
    } else if (o.method == 'POST' && o.path == '/api-keys/k1/webhooks') {
      final hook = {
        'id': 'wh_1', 'keyId': 'k1', 'url': (o.data as Map)['url'], 'events': ['questions.added'],
        'secretHint': 'whsec_shown', 'createdAt': '2026-10-01T10:00:00+00:00', 'createdBy': 'user_p',
        'revokedAt': null, 'active': true,
      };
      hooks.add(hook);
      data = {...hook, 'secret': _secret};
    } else if (o.path == '/api-keys/k1/webhooks/wh_1/deliveries') {
      data = [
        {'id': 'whd_2', 'eventId': 'evt_2', 'eventType': 'questions.added', 'status': 'pending', 'attempts': 1,
          'lastStatusCode': 502, 'lastError': 'the receiver answered HTTP 502',
          'nextAttemptAt': '2026-10-01T10:06:00+00:00', 'createdAt': '2026-10-01T10:05:00+00:00',
          'updatedAt': '2026-10-01T10:05:00+00:00', 'deliveredAt': null, 'subject': 'Science', 'grade': 10,
          'chapterId': 'life-processes', 'questionCount': 2},
        {'id': 'whd_1', 'eventId': 'evt_1', 'eventType': 'questions.added', 'status': 'delivered', 'attempts': 1,
          'lastStatusCode': 200, 'lastError': '', 'nextAttemptAt': null, 'createdAt': '2026-10-01T10:01:00+00:00',
          'updatedAt': '2026-10-01T10:01:00+00:00', 'deliveredAt': '2026-10-01T10:01:00+00:00',
          'subject': 'Science', 'grade': 10, 'chapterId': 'life-processes', 'questionCount': 1},
      ];
    }
    return ResponseBody.fromString(jsonEncode(data), 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _FakeServer server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('webhooks_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _FakeServer();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'user_p', 'schoolId': 'school_1', 'role': 'principal'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    // A widget test's Hive writes can be left inside its fake clock, and
    // Hive.close() then waits on them forever (marks_page_test does the same).
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('webhooks_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> open(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: WebhooksPage(keyId: 'k1', keyLabel: 'Partner LMS')));
    await tester.pumpAndSettle();
  }

  testWidgets('the secret is shown once when a webhook is added, and never in the list', (tester) async {
    await open(tester);
    expect(find.text('No webhooks'), findsOneWidget);

    await tester.tap(find.text('Add webhook'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('webhook-url')), 'https://partner.example/acos');
    await tester.tap(find.widgetWithText(FilledButton, 'Add'));
    await tester.pumpAndSettle();

    expect(server.sent, contains('POST /api-keys/k1/webhooks {"url":"https://partner.example/acos","events":["questions.added"]}'));
    expect(find.text('Copy the signing secret now'), findsOneWidget);
    expect(find.text(_secret), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Done'));
    await tester.pumpAndSettle();

    expect(find.text('https://partner.example/acos'), findsOneWidget);
    expect(find.text(_secret), findsNothing);
    expect(find.textContaining('whsec_shown…'), findsOneWidget);
  });

  testWidgets('the delivery log says what was sent and what is being retried', (tester) async {
    server.hooks.add({
      'id': 'wh_1', 'keyId': 'k1', 'url': 'https://partner.example/acos', 'events': ['questions.added'],
      'secretHint': 'whsec_shown', 'createdAt': '2026-10-01T10:00:00+00:00', 'createdBy': 'user_p',
      'revokedAt': null, 'active': true,
    });
    await open(tester);
    await tester.tap(find.text('Deliveries'));
    await tester.pumpAndSettle();
    expect(server.sent, contains('GET /api-keys/k1/webhooks/wh_1/deliveries'));
    expect(find.text('Science 10 · life-processes · 2 questions'), findsOneWidget);
    expect(find.textContaining('Retrying at 2026-10-01 10:06 · 1 attempt · the receiver answered HTTP 502'), findsOneWidget);
    expect(find.textContaining('Delivered (200) · 1 attempt'), findsOneWidget);
  });
}
