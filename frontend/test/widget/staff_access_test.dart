// Staff and access, API keys and the forgotten-password card (QA 2026-10-01).
//
// S-05: nobody could reset a forgotten password; the principal now resets it
// from a teacher's ⋮ (or anyone's, on the admin console's card) and is shown
// the one-time password plainly, with a Copy that says it copied.
// S-18: revoking an API key and taking an admin area away were one tap with
// no question asked. S-07 / S-23: the new key was not visible, and the list
// read "last used 2026-10-01T21:27:20.432778+00:00" and "(classes 10)".
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/presentation/admin/widgets/password_reset.dart';
import 'package:academicos/presentation/workspace/admin_pages.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _Server implements HttpClientAdapter {
  final List<String> calls = [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    calls.add('${o.method} ${o.path}');
    final role = o.queryParameters['role'];
    final Object? answer = switch ((o.method, o.path)) {
      ('GET', '/auth/users') when role == 'teacher' => [
          {'id': 't_meera', 'schoolId': 's', 'name': 'Meera Iyer', 'email': 'meera@x.in', 'role': 'teacher'},
        ],
      ('GET', '/auth/users') when role == 'left' => <Object>[],
      ('GET', '/auth/users') => [
          {'id': 'p_1', 'schoolId': 's', 'name': 'Priya Menon', 'email': 'priya@x.in', 'role': 'principal'},
          {'id': 't_meera', 'schoolId': 's', 'name': 'Meera Iyer', 'email': 'meera@x.in', 'role': 'teacher'},
          {'id': 's_asha', 'schoolId': 's', 'name': 'Asha Kumar', 'email': 'asha@x.in', 'role': 'student'},
          {'id': 'g_meena', 'schoolId': 's', 'name': 'Meena Kumar', 'email': 'meena@x.in', 'role': 'parent'},
        ],
      ('GET', '/admin/grants') => [
          {'id': 'gr_1', 'userId': 't_meera', 'label': 'Leave, attendance and substitutions', 'scope': {'grades': [10]}},
        ],
      ('GET', '/my-grants') => {'capabilities': <String>[], 'available': <Object>[]},
      ('POST', '/auth/users/t_meera/password-reset') =>
        {'userId': 't_meera', 'name': 'Meera Iyer', 'temporaryPassword': 'k7mq-x2rw-9tpd'},
      ('POST', '/auth/users/s_asha/password-reset') =>
        {'userId': 's_asha', 'name': 'Asha Kumar', 'temporaryPassword': 'ab3d-ef4h-jk5m'},
      ('GET', '/api-keys') => [
          {'id': 'k1', 'label': 'Tuition partner app', 'prefix': 'aos_ab12', 'scopes': ['questions:read'],
            'grades': [10], 'active': true, 'lastUsedAt': '2026-09-28T21:27:20.432778+00:00', 'quotaPerMinute': 60},
        ],
      ('POST', '/api-keys') => {'id': 'k2', 'key': 'aos_secret_key_value_123'},
      ('DELETE', _) => {'ok': true},
      _ => null,
    };
    if (answer == null) {
      return ResponseBody.fromString(jsonEncode({'detail': 'not served here'}), 404, headers: _json);
    }
    return ResponseBody.fromString(jsonEncode(answer), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Server server;
  late List<String> clipboard;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('staff_access_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    final dio = Dio()..httpClientAdapter = server;
    GetIt.instance.registerSingleton<Dio>(dio);
    GetIt.instance.registerSingleton<AuthApi>(AuthApi(dio));
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 's', 'role': 'principal', 'name': 'Priya Menon'};
    clipboard = [];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform, (call) async {
      if (call.method == 'Clipboard.setData') clipboard.add((call.arguments as Map)['text'] as String);
      return null;
    });
  });

  tearDown(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(SystemChannels.platform, null);
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
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 150)));
    await tester.pumpAndSettle();
  }

  Future<void> pump(WidgetTester tester, Widget page) async {
    tester.view.physicalSize = const Size(1000, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.darkTheme, home: page));
    await settle(tester);
  }

  testWidgets("a teacher's ⋮ resets the password and shows it to copy", (tester) async {
    await pump(tester, const GrantsPage());
    expect(find.text('Leave, attendance and substitutions (class 10)'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('staff-more-t_meera')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Reset password'));
    await tester.pumpAndSettle();
    expect(find.text("Reset Meera Iyer's password?"), findsOneWidget);
    expect(server.calls.where((c) => c.contains('password-reset')), isEmpty, reason: 'nothing before yes');
    await tester.tap(find.byKey(const ValueKey('confirm-action')));
    await settle(tester);

    expect(server.calls, contains('POST /auth/users/t_meera/password-reset'));
    expect(find.text('Temporary password for Meera Iyer'), findsOneWidget);
    expect(tester.widget<SelectableText>(find.byKey(const ValueKey('copyable-value'))).data, 'k7mq-x2rw-9tpd');
    await tester.tap(find.byKey(const ValueKey('copyable-copy')));
    await tester.pump();
    expect(clipboard, ['k7mq-x2rw-9tpd']);
    expect(find.text('Temporary password copied.'), findsOneWidget);
  });

  testWidgets('taking an admin area away asks first', (tester) async {
    await pump(tester, const GrantsPage());
    await tester.tap(find.byTooltip('Take this away'));
    await tester.pumpAndSettle();
    expect(find.text('Take this away from Meera Iyer?'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(server.calls.where((c) => c.startsWith('DELETE')), isEmpty);
    await tester.tap(find.byTooltip('Take this away'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('confirm-action')));
    await settle(tester);
    expect(server.calls, contains('DELETE /admin/grants/gr_1'));
  });

  testWidgets('API keys: readable last use, a confirmed revoke, and a new key shown whole', (tester) async {
    await pump(tester, const ApiKeysPage());
    // The page shows the device's local day: 21:27 UTC is the 29th in India, so the
    // expectation is derived the same way instead of hard-coding the UTC day.
    final usedOn = DateTime.parse('2026-09-28T21:27:20.432778+00:00').toLocal().day;
    expect(find.textContaining('last used $usedOn Sep 2026 at'), findsOneWidget);
    expect(find.textContaining('T21:27'), findsNothing);
    expect(find.textContaining('class 10'), findsOneWidget);
    expect(find.textContaining('Search and fetch questions'), findsOneWidget);

    await tester.tap(find.text('Revoke'));
    await tester.pumpAndSettle();
    expect(find.text('Revoke "Tuition partner app"?'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('confirm-action')));
    await settle(tester);
    expect(server.calls, contains('DELETE /api-keys/k1'));

    await tester.tap(find.text('New key'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Create'));
    await settle(tester);
    expect(find.text('Copy the key now'), findsOneWidget);
    expect(tester.widget<SelectableText>(find.byKey(const ValueKey('copyable-value'))).data,
        'aos_secret_key_value_123');
    await tester.tap(find.byKey(const ValueKey('copyable-copy')));
    await tester.pump();
    expect(clipboard, ['aos_secret_key_value_123']);
    expect(find.text('API key copied.'), findsOneWidget);
    await tester.tap(find.text('Done'));
    await settle(tester);
    expect(find.text('Copy the key now'), findsNothing);
    expect(find.text('API keys'), findsOneWidget, reason: 'Done closes the dialog, not the page');
  });

  testWidgets('the forgotten-passwords card finds a student and resets theirs', (tester) async {
    await pump(tester, const Scaffold(body: SingleChildScrollView(child: PasswordResetCard())));
    expect(find.text('Priya Menon'), findsNothing, reason: "the principal's account is the operator's");
    expect(find.text('Meena Kumar'), findsOneWidget, reason: 'parents are listed');
    await tester.enterText(find.byKey(const ValueKey('reset-search')), 'asha');
    await tester.pumpAndSettle();
    expect(find.text('Meera Iyer'), findsNothing);
    await tester.tap(find.byKey(const ValueKey('reset-more-s_asha')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Reset password'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('confirm-action')));
    await settle(tester);
    expect(server.calls, contains('POST /auth/users/s_asha/password-reset'));
    expect(tester.widget<SelectableText>(find.byKey(const ValueKey('copyable-value'))).data, 'ab3d-ef4h-jk5m');
  });
}
