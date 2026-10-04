// The role guard as wired into the real router: a signed-in person who opens a page that is not
// theirs lands on their own home, and no route redirects in a loop (audit 2026-10-04).
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/routing/app_router.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Refuses every request, so the pages the router opens show their own error and no more.
class _Refuses implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async =>
      ResponseBody.fromString(jsonEncode({'detail': 'not in this test'}), 403,
          headers: {Headers.contentTypeHeader: ['application/json']});

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('router_guard_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() => GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = _Refuses()));

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 5));
    } catch (_) {
      // the known hive lock-queue flake on Windows
    }
  });

  Future<String> landing(WidgetTester tester, String role, String from) async {
    LocalStore.instance.authToken = 'token';
    LocalStore.instance.authUser = {'id': 'u1', 'schoolId': 's1', 'role': role, 'name': 'T'};
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final router = container.read(appRouterProvider);
    router.go(from);
    await tester.pumpWidget(UncontrolledProviderScope(
        container: container, child: MaterialApp.router(routerConfig: router)));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 400)));
    await tester.pump();
    final where = router.routerDelegate.currentConfiguration.uri.toString();
    // Let the page's own timers run out, so the test ends with none pending.
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(minutes: 2));
    return where;
  }

  testWidgets('a student who opens the admin console, or a v2 page, lands on their own pages', (tester) async {
    expect(await landing(tester, 'student', '/admin'), '/school');
    expect(await landing(tester, 'student', '/school/timetable'), '/school');
    expect(await landing(tester, 'student', '/syllabus'), '/school');
    expect(await landing(tester, 'student', '/student/schedule'), '/school/week');
    expect(await landing(tester, 'student', '/school/today'), '/school/today');
  });

  testWidgets('a parent lands on their children, and keeps the inbox', (tester) async {
    expect(await landing(tester, 'parent', '/admin'), '/school/family');
    expect(await landing(tester, 'parent', '/parent'), '/school/family');
    expect(await landing(tester, 'parent', '/school/inbox'), '/school/inbox');
  });

  testWidgets('a teacher is kept out of the principal\'s pages, a principal out of the owner overview',
      (tester) async {
    expect(await landing(tester, 'teacher', '/admin'), '/home');
    expect(await landing(tester, 'teacher', '/school/grants'), '/home');
    expect(await landing(tester, 'teacher', '/school/my-day'), '/school/my-day');
    // '/home' is each role's own first page: a principal's is the school at a glance.
    expect(await landing(tester, 'principal', '/owner'), '/school');
    expect(await landing(tester, 'principal', '/admin'), '/admin');
    expect(await landing(tester, 'principal', '/syllabus'), '/school');
  });
}
