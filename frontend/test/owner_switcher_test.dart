// ROLE-4 multi-campus on the web: an owner account switches between its
// linked schools from the side navigation, and nobody else is offered the
// switcher. Choosing a school replaces the signed-in user kept on the device
// with the server's answer (that school's principal), which is where every
// page reads its role and school from; an owner's offline copies are kept
// per school, so one school's saved page is never shown inside another.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/routing/app_router.dart';
import 'package:academicos/core/session/current_session.dart';
import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:academicos/presentation/workspace/ops_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

Map<String, dynamic> _owner(String schoolId) => {
      'id': 'user_owner', 'schoolId': schoolId, 'name': 'Owner', 'email': 'o@example.com',
      'role': schoolId.isEmpty ? 'owner' : 'principal', 'isOwner': true,
    };

/// The owner routes, from memory; records what was sent.
class _FakeOwnerServer implements HttpClientAdapter {
  final List<String> sent = [];
  bool offline = false;
  String active = 'school_a';

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (offline) throw DioException.connectionError(requestOptions: o, reason: 'no network');
    sent.add('${o.method} ${o.path}${o.data == null ? '' : ' ${jsonEncode(o.data)}'}');
    Object? data;
    if (o.method == 'GET' && o.path == '/owner/schools') {
      data = [
        {'schoolId': 'school_a', 'name': 'Campus A', 'linkedAt': '2026-10-01', 'active': active == 'school_a'},
        {'schoolId': 'school_b', 'name': 'Campus B', 'linkedAt': '2026-10-01', 'active': active == 'school_b'},
      ];
    } else if (o.path == '/owner/active-school') {
      active = o.method == 'POST' ? (o.data as Map)['schoolId'] as String : '';
      data = _owner(active);
    } else if (o.path == '/dashboard/summary') {
      data = {'school': active};
    } else {
      data = const <String, dynamic>{};
    }
    return ResponseBody.fromString(jsonEncode(data), 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

Widget _app() {
  Widget page(String title) => Scaffold(appBar: AppBar(title: Text(title)), body: Text('$title body'));
  return MaterialApp.router(routerConfig: GoRouter(initialLocation: '/school', routes: [
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        GoRoute(path: '/school', builder: (context, state) => page('School')),
        GoRoute(path: '/owner', builder: (context, state) => page('Your schools')),
        GoRoute(path: '/settings', builder: (context, state) => page('Settings')),
      ],
    ),
  ]));
}

void main() {
  late Directory tmp;
  late _FakeOwnerServer server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('owner_switcher_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _FakeOwnerServer();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
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
      print('owner_switcher_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  test('an owner with no school chosen lands on its schools, with only that destination', () {
    expect(roleLanding('/home', role: 'owner', offlineBuild: false), '/owner');
    expect([for (final i in navItemsFor('owner')) i.label], ['All schools']);
  });

  testWidgets('the switcher is shown to an owner and switches the school the session acts in', (tester) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    LocalStore.instance.authUser = _owner('school_a');
    expect(CurrentSession.isOwner, isTrue);

    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();
    final switcher = find.byKey(const Key('school-switcher'));
    expect(switcher, findsOneWidget);
    expect(find.descendant(of: switcher, matching: find.text('Campus A')), findsOneWidget);

    await tester.tap(switcher);
    await tester.pumpAndSettle();
    expect(find.text('Campus B'), findsOneWidget);
    expect(find.text('All schools'), findsWidgets);
    await tester.tap(find.widgetWithText(CheckedPopupMenuItem<String>, 'Campus B'));
    await tester.pumpAndSettle();

    expect(server.sent, contains('POST /owner/active-school {"schoolId":"school_b"}'));
    expect(CurrentSession.schoolId, 'school_b');
    expect(CurrentSession.role, 'principal');
    expect(find.descendant(of: switcher, matching: find.text('Campus B')), findsOneWidget);

    // back to all schools: the owner's own page, role "owner"
    await tester.tap(switcher);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(CheckedPopupMenuItem<String>, 'All schools'));
    await tester.pumpAndSettle();
    expect(server.sent, contains('DELETE /owner/active-school'));
    expect(CurrentSession.role, 'owner');
    expect(CurrentSession.schoolId, '');
    expect(find.text('Your schools body'), findsOneWidget);
  });

  testWidgets("a school's own principal has no switcher", (tester) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    LocalStore.instance.authUser = {'id': 'user_p', 'schoolId': 'school_a', 'name': 'P', 'email': 'p@example.com',
      'role': 'principal'};
    expect(CurrentSession.isOwner, isFalse);
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('school-switcher')), findsNothing);
    expect(server.sent, isNot(contains('GET /owner/schools')));
  });

  test("an owner's saved copy of one school is not served inside another", () async {
    LocalStore.instance.authUser = _owner('school_a');
    server.active = 'school_a';
    expect((await Ops.map('/dashboard/summary'))['school'], 'school_a');
    LocalStore.instance.authUser = _owner('school_b');
    server.offline = true;
    expect(() => Ops.map('/dashboard/summary'), throwsA(isA<OpsError>()),
        reason: "school A's dashboard must not stand in for school B's");
    LocalStore.instance.authUser = _owner('school_a');
    expect((await Ops.map('/dashboard/summary'))['school'], 'school_a');
  });

  test("an owner's change made offline in one school waits for that school", () async {
    LocalStore.instance.authUser = _owner('school_a');
    server.offline = true;
    await expectLater(Ops.send('PUT', '/papers/p1/marks', body: {'v': 1}, label: 'Marks'), throwsA(isA<OpsQueued>()));
    expect(Ops.pending.value, 1);
    LocalStore.instance.authUser = _owner('school_b');
    server.offline = false;
    Ops.loadSyncState();
    expect(Ops.pending.value, 0, reason: "nothing waits for school B");
    await Ops.flush();
    expect(server.sent.where((s) => s.startsWith('PUT')), isEmpty, reason: "school A's change is not sent as B");
    LocalStore.instance.authUser = _owner('school_a');
    await Ops.flush();
    expect(server.sent, contains('PUT /papers/p1/marks {"v":1}'));
    expect(Ops.pending.value, 0);
  });
}
