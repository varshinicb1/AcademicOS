// Offline reads for the School pages and phone apps (TA-8, SA-8): a read is
// saved per signed-in user and served when the server cannot be reached; a
// real refusal from the server is never covered up; another user on the
// same phone never sees the first user's copy.
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/ops_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Answers from a map; `offline` makes every request fail as if there were
/// no network, and a path mapped to a status code answers with that code.
class _FakeAdapter implements HttpClientAdapter {
  bool offline = false;
  final Map<String, Object> answers = {};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (offline) {
      throw DioException.connectionError(requestOptions: o, reason: 'no network');
    }
    final a = answers[o.path];
    if (a is int) {
      return ResponseBody.fromString('{"detail":"not yours"}', a, headers: {
        Headers.contentTypeHeader: ['application/json'],
      });
    }
    return ResponseBody.fromString(a as String, 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _FakeAdapter adapter;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('ops_offline_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    adapter = _FakeAdapter();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = adapter);
    LocalStore.instance.authUser = {'id': 'stu_1', 'schoolId': 'school_1', 'role': 'student'};
    Ops.offlineSince.value = null;
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    await Hive.close();
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  test('a saved read is served offline, and the banner knows', () async {
    adapter.answers['/my-homework'] = '[{"id":"hw_1","title":"Light"}]';
    expect((await Ops.list('/my-homework')).single['title'], 'Light');
    expect(Ops.offlineSince.value, isNull);
    adapter.offline = true;
    expect((await Ops.list('/my-homework')).single['id'], 'hw_1');
    expect(Ops.offlineSince.value, isNotNull);
  });

  test('never saved: offline is an error, not an empty page', () async {
    adapter.offline = true;
    expect(() => Ops.list('/my-exams'), throwsA(isA<OpsError>()));
  });

  test('a refusal from the server is not replaced by a saved copy', () async {
    adapter.answers['/children/c1/homework'] = '[]';
    await Ops.list('/children/c1/homework');
    adapter.answers['/children/c1/homework'] = 404;
    expect(() => Ops.list('/children/c1/homework'), throwsA(isA<OpsError>()));
  });

  test('another user on the same phone does not see the first one\'s copy', () async {
    adapter.answers['/my-learning'] = '{"subjects":[]}';
    await Ops.map('/my-learning');
    LocalStore.instance.authUser = {'id': 'stu_2', 'schoolId': 'school_1', 'role': 'student'};
    adapter.offline = true;
    expect(() => Ops.map('/my-learning'), throwsA(isA<OpsError>()));
  });
}
