// MSG-1: a parent sees their conversations, starts one with a child's
// teacher, and replies in a conversation.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/messages_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart' show useAppFonts;

class _Server implements HttpClientAdapter {
  final List<String> writes = [];
  final List<Map<String, dynamic>> messages = [
    {'id': 'm1', 'senderId': 'p1', 'senderName': 'Meena', 'mine': true, 'body': 'Can Asha hand in on Friday?',
      'createdAt': '2026-06-01T04:00:00Z'},
  ];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  Map<String, dynamic> _conv() => {
        'id': 'c1', 'studentId': 's1', 'studentName': 'Asha', 'withId': 't1', 'withName': 'Ana',
        'withRole': 'teacher', 'lastAt': '2026-06-01T04:00:00Z', 'lastMessage': messages.last['body'], 'unread': 1,
        'messages': messages,
      };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'POST') {
      writes.add('${o.path} ${jsonEncode(o.data)}');
      if (o.path == '/conversations/c1/messages') {
        messages.add({'id': 'm2', 'senderId': 'p1', 'senderName': 'Meena', 'mine': true,
          'body': (o.data as Map)['body'], 'createdAt': '2026-06-01T05:00:00Z'});
      }
      return ResponseBody.fromString(jsonEncode(_conv()), 200, headers: _json);
    }
    final Object answer = switch (o.path) {
      '/conversations' => [_conv()],
      '/conversations/c1' => _conv(),
      '/my-children' => [
          {'studentId': 's1', 'name': 'Asha', 'grade': 10, 'consent': 'granted'},
        ],
      '/children/s1/contacts' => [
          {'userId': 't1', 'name': 'Ana', 'role': 'Science teacher'},
          {'userId': 'pr', 'name': 'Priya', 'role': 'principal'},
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
    tmp = Directory.systemTemp.createTempSync('messages_page_test_');
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

  Future<void> pump(WidgetTester tester, Widget page) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.darkTheme, home: page));
    await settle(tester);
  }

  testWidgets('a parent sees the conversation, unread, with whom and about which child', (tester) async {
    await pump(tester, const MessagesPage());
    expect(find.text('Ana · about Asha'), findsOneWidget);
    expect(find.text('1 new'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets("New message writes to one of the child's teachers", (tester) async {
    await pump(tester, const MessagesPage());
    await tester.tap(find.byKey(const ValueKey('new-message')));
    await settle(tester);
    await tester.tap(find.byKey(const ValueKey('message-to')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ana (Science teacher)').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('message-body')), 'Asha was unwell today.');
    await tester.tap(find.byKey(const ValueKey('send-message')));
    await settle(tester);
    expect(server.writes, ['/conversations {"studentId":"s1","withId":"t1","body":"Asha was unwell today."}']);
  });

  testWidgets('a reply is sent and shown in the conversation', (tester) async {
    await pump(tester, const ConversationPage(conversationId: 'c1'));
    expect(find.text('Can Asha hand in on Friday?'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('reply-body')), 'Thank you');
    await tester.tap(find.byKey(const ValueKey('send-reply')));
    await settle(tester);
    expect(find.text('Thank you'), findsOneWidget);
    expect(server.writes.single, '/conversations/c1/messages {"body":"Thank you"}');
    expect(tester.takeException(), isNull);
  });
}
