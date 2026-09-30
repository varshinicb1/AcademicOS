// SMS and WhatsApp consent (INT-2): a teacher or parent gives their own number
// and ticks each channel, then confirms it with the code sent to it; the card
// says when the school has not switched a channel on; a student never sees it
// (nor asks the server); removing the number withdraws both.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/messaging_card.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _Backend implements HttpClientAdapter {
  Map<String, dynamic> contact = {'phone': null, 'smsOk': false, 'whatsappOk': false, 'verified': false,
    'smsAvailable': true, 'whatsappAvailable': false, 'kinds': ['substitution_proposed']};
  final List<dynamic> puts = [];
  final List<String> paths = [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    paths.add('${o.method} ${o.path}');
    if (o.path == '/me/contact/verify') {
      if ((o.data as Map)['code'] != '123456') {
        return ResponseBody.fromString('{"detail":"that code is not right: 4 tries left"}', 422, headers: _json);
      }
      contact = {...contact, 'verified': true, 'codeSentVia': null};
      return ResponseBody.fromString(jsonEncode(contact), 200, headers: _json);
    }
    if (o.path == '/me/contact' && o.method == 'PUT') {
      final b = Map<String, dynamic>.from(o.data as Map);
      puts.add(b);
      if ((b['phone'] as String?) == '12345') {
        return ResponseBody.fromString('{"detail":"give an Indian mobile number: 10 digits starting with 6, 7, 8 or 9"}',
            422, headers: _json);
      }
      final kept = b['phone'] != null && (b['smsOk'] == true || b['whatsappOk'] == true);
      contact = {...contact, 'phone': kept ? '+919876543210' : null,
        'smsOk': kept && b['smsOk'] == true, 'whatsappOk': kept && b['whatsappOk'] == true,
        'verified': kept && contact['verified'] == true,
        'codeSentVia': kept && contact['verified'] != true ? (b['whatsappOk'] == true ? 'whatsapp' : 'sms') : null};
    }
    return ResponseBody.fromString(jsonEncode(contact), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('messaging_card_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
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
      print('messaging_card_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pump(WidgetTester tester, String role) async {
    LocalStore.instance.authUser = {'id': 'u_1', 'schoolId': 'school_1', 'role': role, 'name': 'Ana'};
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: SingleChildScrollView(child: MessagingCard()))));
    await tester.pumpAndSettle();
  }

  testWidgets('a student does not see it, and it does not ask the server', (tester) async {
    await pump(tester, 'student');
    expect(find.byKey(const ValueKey('messaging-card')), findsNothing);
    expect(backend.paths, isEmpty);
  });

  testWidgets('a parent ticks WhatsApp and is told the school has not switched it on yet', (tester) async {
    await pump(tester, 'parent');
    expect(find.byKey(const ValueKey('messaging-off')), findsOneWidget);
    expect(find.textContaining('WhatsApp yet'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('messaging-phone')), '98765 43210');
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-whatsapp')));
    await tester.tap(find.byKey(const ValueKey('messaging-whatsapp')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-save')));
    await tester.tap(find.byKey(const ValueKey('messaging-save')));
    await tester.pumpAndSettle();
    expect(backend.puts.single, {'phone': '98765 43210', 'smsOk': false, 'whatsappOk': true});
    expect(find.text('Saved.'), findsOneWidget);
    expect(find.textContaining('About your children'), findsOneWidget);
    expect(find.textContaining('A code was sent by WhatsApp'), findsOneWidget);
    expect(find.text('Not confirmed yet'), findsOneWidget);
    expect(tester.takeException(), isNull, reason: 'fits a phone');

    await tester.enterText(find.byKey(const ValueKey('messaging-code')), '123456');
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-confirm')));
    await tester.tap(find.byKey(const ValueKey('messaging-confirm')));
    await tester.pumpAndSettle();
    expect(backend.paths, contains('POST /me/contact/verify'));
    expect(find.text('Number confirmed.'), findsOneWidget);
    expect(find.text('Confirmed'), findsOneWidget);
    expect(find.byKey(const ValueKey('messaging-code')), findsNothing);
  });

  testWidgets('a wrong code is refused as the server words it; unticking both drops the number',
      (tester) async {
    await pump(tester, 'teacher');
    expect(find.textContaining('For cover requests'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('messaging-phone')), '9876543210');
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-sms')));
    await tester.tap(find.byKey(const ValueKey('messaging-sms')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-save')));
    await tester.tap(find.byKey(const ValueKey('messaging-save')));
    await tester.pumpAndSettle();
    expect(find.textContaining('A code was sent by SMS'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('messaging-code')), '999999');
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-confirm')));
    await tester.tap(find.byKey(const ValueKey('messaging-confirm')));
    await tester.pumpAndSettle();
    expect(find.text('that code is not right: 4 tries left'), findsOneWidget);

    await tester.ensureVisible(find.byKey(const ValueKey('messaging-sms')));

    await tester.tap(find.byKey(const ValueKey('messaging-sms')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-save')));
    await tester.tap(find.byKey(const ValueKey('messaging-save')));
    await tester.pumpAndSettle();
    expect(find.text('Nothing ticked, so your number is not kept.'), findsOneWidget);
    expect(find.byKey(const ValueKey('messaging-remove')), findsNothing);
  });

  testWidgets("the server's refusal is shown; removing the number withdraws both", (tester) async {
    await pump(tester, 'teacher');
    await tester.enterText(find.byKey(const ValueKey('messaging-phone')), '12345');
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-save')));
    await tester.tap(find.byKey(const ValueKey('messaging-save')));
    await tester.pumpAndSettle();
    expect(find.textContaining('give an Indian mobile number'), findsOneWidget);

    await tester.enterText(find.byKey(const ValueKey('messaging-phone')), '9876543210');
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-sms')));
    await tester.tap(find.byKey(const ValueKey('messaging-sms')));
    await tester.pump();
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-save')));
    await tester.tap(find.byKey(const ValueKey('messaging-save')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('messaging-remove')));
    await tester.tap(find.byKey(const ValueKey('messaging-remove')));
    await tester.pumpAndSettle();
    expect(backend.puts.last, {'phone': null});
    expect(find.text('Number removed. No SMS or WhatsApp will be sent.'), findsOneWidget);
  });
}
