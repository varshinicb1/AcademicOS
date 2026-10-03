// What a person has done in the Guide is saved for them, on the server, so a new browser or
// phone shows the same ticks; and it still works with no connection. Before this, nothing
// the Guide knew was saved at all.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/guide/guide_content.dart';
import 'package:academicos/presentation/guide/guide_page.dart';
import 'package:academicos/presentation/shared/user_progress.dart';
import 'package:academicos/presentation/workspace/ops_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// The server's /me/progress: it keeps what it is sent, like the real one.
class _Server implements HttpClientAdapter {
  final Map<String, Map<String, Object?>> stored = {};
  final List<String> puts = [];
  bool offline = false;
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (offline) {
      throw DioException(requestOptions: o, type: DioExceptionType.connectionError, message: 'no connection');
    }
    if (o.method == 'GET' && o.path == '/me/progress') {
      return ResponseBody.fromString(jsonEncode({'items': stored}), 200, headers: _json);
    }
    if (o.method == 'PUT' && o.path.startsWith('/me/progress/')) {
      final key = o.path.substring('/me/progress/'.length);
      final value = (o.data as Map)['value'];
      puts.add(key);
      stored[key] = {'value': value, 'updatedAt': DateTime.now().toUtc().toIso8601String()};
      return ResponseBody.fromString(jsonEncode(stored[key]), 200, headers: _json);
    }
    return ResponseBody.fromString(jsonEncode({'detail': 'not found'}), 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Server server;
  final jobs = guideJobsFor('principal');

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('guide_progress_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Farida'};
    UserProgress.reset();
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
      tmp.deleteSync(recursive: true);
    } on TimeoutException {
      // ignore: avoid_print
      print('guide_progress_test: Hive.close() did not return within 10s -- proceeding.');
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pumpGuide(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1280, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(MaterialApp(theme: AppTheme.lightTheme, home: const GuidePage(role: 'principal')));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
  }

  Future<void> tick(WidgetTester tester, GuideJob job) async {
    await tester.tap(find.text(job.title));
    await tester.pumpAndSettle();
    final box = find.byKey(ValueKey('guide-done-${job.id}'));
    await tester.ensureVisible(box);
    await tester.pumpAndSettle();
    await tester.tap(box);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pumpAndSettle();
  }

  String progressText(WidgetTester tester) =>
      tester.widget<Text>(find.byKey(const ValueKey('guide-progress-text'))).data!;

  testWidgets('a new person has done none, and ticking a job saves it and moves the count', (tester) async {
    await pumpGuide(tester);
    expect(progressText(tester), '0 of ${jobs.length} jobs done');
    await tick(tester, jobs.first);
    expect(progressText(tester), '1 of ${jobs.length} jobs done');
    expect(server.stored[guideDoneKey(jobs.first.id)]!['value'], true);
    expect(server.puts, contains(guideOpenedKey(jobs.first.id)), reason: 'opening a job is recorded too');
  });

  testWidgets('another browser opens the Guide with the same jobs ticked', (tester) async {
    server.stored[guideDoneKey(jobs[0].id)] = {'value': true, 'updatedAt': '2026-10-03T08:00:00+00:00'};
    server.stored[guideDoneKey(jobs[2].id)] = {'value': true, 'updatedAt': '2026-10-03T08:05:00+00:00'};
    await pumpGuide(tester);
    expect(progressText(tester), '2 of ${jobs.length} jobs done');
    expect(find.byIcon(Icons.check_circle), findsNWidgets(2));
  });

  testWidgets('with no connection a tick still shows, is kept on the device and is not lost', (tester) async {
    server.offline = true;
    await pumpGuide(tester);
    await tick(tester, jobs.first);
    expect(progressText(tester), '1 of ${jobs.length} jobs done');
    expect(server.stored, isEmpty, reason: 'nothing reached the server yet');
    // The same person comes back, still offline: the device remembers.
    UserProgress.reset();
    await pumpGuide(tester);
    expect(progressText(tester), '1 of ${jobs.length} jobs done');
  });

  testWidgets("a different person on the same device does not inherit the last one's ticks", (tester) async {
    server.stored[guideDoneKey(jobs.first.id)] = {'value': true, 'updatedAt': '2026-10-03T08:00:00+00:00'};
    await pumpGuide(tester);
    expect(progressText(tester), '1 of ${jobs.length} jobs done');
    server.stored.clear();
    LocalStore.instance.authUser = {'id': 'p_2', 'schoolId': 'school_2', 'role': 'principal', 'name': 'Someone else'};
    await pumpGuide(tester);
    expect(progressText(tester), '0 of ${jobs.length} jobs done');
  });

  test('where the device and the server disagree, the newer write wins', () async {
    server.offline = true;
    await UserProgress.save('guide.done.x', true); // device only, now
    server.offline = false;
    server.stored['guide.done.x'] = {'value': false, 'updatedAt': '2020-01-01T00:00:00+00:00'};
    await UserProgress.load();
    expect(UserProgress.isDone('guide.done.x'), isTrue, reason: "the server's copy is years older");
    // The write that waited for the connection is sent once it is back; let it land first.
    // load() started the send without waiting for it; wait until it has landed.
    for (var i = 0; i < 100 && server.stored['guide.done.x']!['value'] != true; i++) {
      await Ops.flush();
      await Future<void>.delayed(const Duration(milliseconds: 20));
    }
    expect(server.stored['guide.done.x']!['value'], true, reason: 'the queued write was delivered');
    server.stored['guide.done.x'] = {'value': false, 'updatedAt': '2099-01-01T00:00:00+00:00'};
    await UserProgress.load();
    expect(UserProgress.isDone('guide.done.x'), isFalse, reason: "now the server's is newer");
  });
}
