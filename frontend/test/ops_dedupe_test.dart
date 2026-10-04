// Two reads of the same page in the same moment share one request (audit 2026-10-04), and a write
// ends the sharing so a read after a change never joins a read from before it.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/ops_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

class _Slow implements HttpClientAdapter {
  final List<String> gets = [];
  final Map<String, Completer<void>> gate = {};
  int version = 1;
  bool failNext = false;

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'GET') {
      gets.add(o.uri.toString());
      final seen = version;
      final g = gate[o.path];
      if (g != null) await g.future;
      if (failNext) {
        failNext = false;
        return ResponseBody.fromString('{"detail":"nope"}', 500,
            headers: {Headers.contentTypeHeader: ['application/json']});
      }
      return ResponseBody.fromString('{"v":$seen}', 200, headers: {Headers.contentTypeHeader: ['application/json']});
    }
    version++;
    return ResponseBody.fromString('{}', 200, headers: {Headers.contentTypeHeader: ['application/json']});
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Slow server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('ops_dedupe_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Slow();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'u1', 'schoolId': 's1', 'role': 'principal'};
    Ops.loadSyncState();
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // known hive lock-queue flake
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // a leaked temp dir is harmless
    }
  });

  test('the same read asked twice at once is sent once, and both callers get the answer', () async {
    server.gate['/setup-status'] = Completer<void>();
    final a = Ops.map('/setup-status');
    final b = Ops.map('/setup-status');
    server.gate['/setup-status']!.complete();
    expect(await a, {'v': 1});
    expect(await b, {'v': 1});
    expect(server.gets, hasLength(1));
  });

  test('a different page, or different query, is a different request', () async {
    final r = await Future.wait([
      Ops.map('/a'), Ops.map('/b'), Ops.map('/a', query: {'x': 1}),
    ]);
    expect(r, hasLength(3));
    expect(server.gets, hasLength(3));
  });

  test('a read after a write never joins a read that began before it', () async {
    server.gate['/page'] = Completer<void>();
    final before = Ops.map('/page');            // begins with version 1, held open
    await Ops.post('/change');                   // the write: version 2
    server.gate['/page']!.complete();
    final after = await Ops.map('/page');        // must be a new request, not the held one
    expect((await before)['v'], 1);
    expect(after['v'], 2, reason: 'the second read began after the change');
    expect(server.gets, hasLength(2));
  });

  test('a finished read is not remembered: asking again asks the server again', () async {
    await Ops.map('/page');
    server.version = 5;
    expect((await Ops.map('/page'))['v'], 5);
    expect(server.gets, hasLength(2));
  });

  test('a failed read is shared once, then the next read tries again', () async {
    server.gate['/page'] = Completer<void>();
    server.failNext = true;
    final a = Ops.map('/page').then<Object?>((v) => v, onError: (Object e) => e);
    final b = Ops.map('/page').then<Object?>((v) => v, onError: (Object e) => e);
    server.gate['/page']!.complete();
    expect(await a, isA<OpsError>());
    expect(await b, isA<OpsError>());
    expect(server.gets, hasLength(1));
    expect((await Ops.map('/page'))['v'], 1, reason: 'the failure did not stick');
  });
}
