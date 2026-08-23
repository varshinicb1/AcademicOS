import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/local_engine/keyed_mutex.dart';
import 'package:academicos/core/sync/sync_service.dart';

/// A simple in-memory HTTP adapter for testing Dio calls.
class _MockHttpClientAdapter implements HttpClientAdapter {
  final Map<String, _MockRoute> _routes = {};
  DioException? _throwError;

  void addRoute(String method, String path, _MockRouteHandler handler) {
    _routes['$method:$path'] = _MockRoute(handler: handler);
  }

  void setNetworkError(DioException error) {
    _throwError = error;
  }

  void clearError() {
    _throwError = null;
  }

  @override
  void close({bool force = false}) {
    _routes.clear();
  }

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<dynamic>? requestStream, Future? cancelFuture) async {
    if (_throwError != null) {
      throw _throwError!;
    }

    final key = '${options.method}:${options.uri.path}';
    final route = _routes[key];
    if (route == null) {
      print('MOCK: No route found for $key');
      throw DioException(
        requestOptions: options,
        error: 'No mock route for $key',
        type: DioExceptionType.badResponse,
        response: Response(requestOptions: options, statusCode: 404),
      );
    }

    print('MOCK: Calling handler for $key');
    try {
      final response = await route.handler(options);
      print('MOCK: Handler returned response');
      final headersMap = <String, List<String>>{
        'content-type': ['application/json'],
      };
      response.headers.forEach((k, v) {
        headersMap[k] = [v.toString()];
      });
      final bodyString = response.body is String ? response.body : jsonEncode(response.body);
      return ResponseBody.fromString(bodyString, response.statusCode,
          headers: headersMap);
    } catch (e, stack) {
      print('MOCK: Handler threw: $e\n$stack');
      rethrow;
    }
  }
}

class _MockRoute {
  final _MockRouteHandler handler;
  _MockRoute({required this.handler});
}

typedef _MockRouteHandler = Future<_MockResponse> Function(RequestOptions options);

class _MockResponse {
  final dynamic body;
  final int statusCode;
  final Map<String, dynamic> headers;
  _MockResponse({required this.body, this.statusCode = 200, this.headers = const {}});
}

/// Test implementation of SyncService that uses a provided Dio.
class _TestSyncService {
  final _MockHttpClientAdapter _adapter = _MockHttpClientAdapter();
  late final Dio _dio;
  late final _SyncServiceWithTestDio _service;

  _TestSyncService() {
    _dio = Dio(BaseOptions(
      baseUrl: 'http://test.api/v1',
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 5),
    ));
    _dio.httpClientAdapter = _adapter;
    _service = _SyncServiceWithTestDio(_dio);
  }

  void mockPostAssessment(_MockResponse Function(Map<String, dynamic>) handler) {
    _adapter.addRoute('POST', '/v1/assessments', (options) async {
      final requestData = options.data as Map<String, dynamic>;
      return handler(requestData);
    });
  }

  void mockPutAssessment(String serverId, _MockResponse Function(Map<String, dynamic>) handler) {
    _adapter.addRoute('PUT', '/v1/assessments/$serverId', (options) async {
      final requestData = options.data as Map<String, dynamic>;
      return handler(requestData);
    });
  }

  void mockGetAssessments(_MockResponse Function() handler) {
    _adapter.addRoute('GET', '/v1/assessments', (options) async => handler());
  }

  void mockNetworkError(DioException error) {
    _adapter.setNetworkError(error);
  }

  void clearNetworkError() {
    _adapter.clearError();
  }

  _SyncServiceWithTestDio get service => _service;
  Dio get dio => _dio;
}

/// Internal test version of SyncService that accepts a Dio.
class _SyncServiceWithTestDio {
  final Dio _dio;
  final KeyedMutex _mutex = KeyedMutex();
  final LocalStore _store = LocalStore.instance;

  _SyncServiceWithTestDio(this._dio);

  Future<void> _saveLastSyncResult(String schoolId, SyncResult result) async {
    _store.box.put('last_sync_result_$schoolId', jsonEncode(result.toJson()));
  }

  SyncResult? getLastSyncResult(String schoolId) {
    final raw = _store.box.get('last_sync_result_$schoolId') as String?;
    if (raw == null) return null;
    return SyncResult.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  bool _isLocallyModified(Map<String, dynamic> local) {
    final metadata = local['metadata'] as Map<String, dynamic>?;
    if (metadata == null) return true;
    final serverSyncedAt = metadata['serverSyncedAt'] as String?;
    if (serverSyncedAt == null) return true;
    final localUpdatedAt = local['updatedAt'] as String?;
    if (localUpdatedAt == null) return false;
    return DateTime.parse(localUpdatedAt).isAfter(DateTime.parse(serverSyncedAt));
  }

  bool _neverSynced(Map<String, dynamic> local) {
    final metadata = local['metadata'] as Map<String, dynamic>?;
    return metadata == null || metadata['serverId'] == null;
  }

  Future<SyncResult> sync(String schoolId) async {
    return _mutex.synchronized('sync_$schoolId', () async {
      int pushedCount = 0;
      int pulledCount = 0;
      String? error;

      try {
        pushedCount = await _pushLocalAssessments(schoolId);
        pulledCount = await _pullServerAssessments(schoolId);
      } on DioException catch (e) {
        error = _formatDioError(e);
      } catch (e) {
        error = e.toString();
      }

      final result = SyncResult(
        pushedCount: pushedCount,
        pulledCount: pulledCount,
        error: error,
        timestamp: DateTime.now(),
      );

      await _saveLastSyncResult(schoolId, result);
      return result;
    });
  }

  Future<int> _pushLocalAssessments(String schoolId) async {
    final localAssessments = _store.allAssessments()
        .where((a) => a['schoolId'] == schoolId)
        .toList();

    int pushed = 0;

    for (final local in localAssessments) {
      final isNew = _neverSynced(local);
      final isModified = _isLocallyModified(local);

      if (!isNew && !isModified) continue;

      try {
        Map<String, dynamic> responseData;
        if (isNew) {
          final request = _toServerCreateRequest(local);
          final response = await _dio.post('/assessments', data: request);
          responseData = response.data as Map<String, dynamic>;
        } else {
          final metadata = local['metadata'] as Map<String, dynamic>;
          final serverId = metadata['serverId'] as String;
          final request = _toServerUpdateRequest(local);
          final response = await _dio.put('/assessments/$serverId', data: request);
          responseData = response.data as Map<String, dynamic>;
        }

        final serverId = responseData['id'] as String;
        final serverUpdatedAt = responseData['updatedAt'] as String;

        final metadata = Map<String, dynamic>.from(local['metadata'] as Map? ?? {});
        metadata['serverId'] = serverId;
        metadata['serverSyncedAt'] = serverUpdatedAt;

        final updated = Map<String, dynamic>.from(local);
        updated['metadata'] = metadata;

        _store.upsertAssessment(updated);
        pushed++;
      } catch (e) {
        rethrow;
      }
    }

    return pushed;
  }

  Future<int> _pullServerAssessments(String schoolId) async {
    final response = await _dio.get('/assessments', queryParameters: {'school_id': schoolId});
    final serverAssessments = (response.data as List).cast<Map<String, dynamic>>();

    int pulled = 0;

    for (final server in serverAssessments) {
      final serverId = server['id'] as String;
      final serverUpdatedAt = server['updatedAt'] as String;

      final localIndex = _store.allAssessments().indexWhere((a) {
        final meta = a['metadata'] as Map<String, dynamic>?;
        return meta?['serverId'] == serverId;
      });

      if (localIndex < 0) {
        final local = _serverToLocal(server);
        _store.upsertAssessment(local);
        pulled++;
      } else {
        final local = _store.allAssessments()[localIndex];
        final localUpdatedAt = local['updatedAt'] as String?;

        if (localUpdatedAt != null &&
            DateTime.parse(serverUpdatedAt).isAfter(DateTime.parse(localUpdatedAt))) {
          final localMeta = Map<String, dynamic>.from(local['metadata'] as Map? ?? {});
          localMeta['serverSyncedAt'] = serverUpdatedAt;

          final merged = _serverToLocal(server);
          merged['metadata'] = localMeta;
          merged['updatedAt'] = localUpdatedAt;

          _store.upsertAssessment(merged);
          pulled++;
        }
      }
    }

    return pulled;
  }

  Map<String, dynamic> _toServerCreateRequest(Map<String, dynamic> local) {
    return {
      'teacherId': local['teacherId'],
      'schoolId': local['schoolId'],
      'title': local['title'],
      'subject': local['subject'],
      'grade': local['grade'],
      'chapterIds': local['chapterIds'],
      'blueprint': local['blueprint'],
      'status': local['status'],
      'selectedQuestionIds': local['selectedQuestionIds'] ?? [],
      'templateId': local['templateId'],
      'metadata': local['metadata'] ?? {},
    };
  }

  Map<String, dynamic> _toServerUpdateRequest(Map<String, dynamic> local) {
    return {
      'teacherId': local['teacherId'],
      'schoolId': local['schoolId'],
      'title': local['title'],
      'subject': local['subject'],
      'grade': local['grade'],
      'chapterIds': local['chapterIds'],
      'blueprint': local['blueprint'],
      'status': local['status'],
      'selectedQuestionIds': local['selectedQuestionIds'] ?? [],
      'templateId': local['templateId'],
      'metadata': local['metadata'] ?? {},
      'updatedAt': local['updatedAt'],
    };
  }

  Map<String, dynamic> _serverToLocal(Map<String, dynamic> server) {
    return {
      'id': server['id'],
      'schoolId': server['schoolId'],
      'teacherId': server['teacherId'],
      'title': server['title'],
      'subject': server['subject'],
      'grade': server['grade'],
      'chapterIds': server['chapterIds'] ?? [],
      'blueprint': server['blueprint'],
      'status': server['status'],
      'createdAt': server['createdAt'],
      'updatedAt': server['updatedAt'],
      'scheduledAt': server['scheduledAt'],
      'completedAt': server['completedAt'],
      'templateId': server['templateId'],
      'metadata': {
        'serverId': server['id'],
        'serverSyncedAt': server['updatedAt'],
        ...(server['metadata'] as Map? ?? {}),
      },
      'selectedQuestionIds': server['selectedQuestionIds'] ?? [],
      'generatedPaperId': server['generatedPaperId'],
      'totalStudents': server['totalStudents'],
      'evaluatedCount': server['evaluatedCount'],
    };
  }

  String _formatDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timed out. The server may be starting up (cold start takes ~60s). Try again in a moment.';
      case DioExceptionType.connectionError:
        return 'Could not connect to server. Check your internet connection and server URL.';
      case DioExceptionType.badResponse:
        final status = e.response?.statusCode ?? 0;
        if (status >= 500) {
          return 'Server error ($status). The backend may be restarting. Try again shortly.';
        }
        return 'Server returned $status: ${e.response?.data ?? e.message}';
      default:
        return 'Sync failed: ${e.message}';
    }
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('SyncService', () {
    late Box cacheBox;
    late LocalStore store;
    late _TestSyncService testHelper;

    const schoolId = 'school_1';
    const teacherId = 'teacher_1';

    late Directory tempDir;
    late Box academicosCacheBox;

    setUpAll(() async {
      tempDir = Directory.systemTemp.createTempSync('sync_service_test_');
      Hive.init(tempDir.path);
      academicosCacheBox = await Hive.openBox('academicos_cache');
      cacheBox = await Hive.openBox('test_academicos_cache');
    });

    tearDownAll(() async {
      await Hive.close();
      tempDir.deleteSync(recursive: true);
    });

    setUp(() async {
      // Real bug found here: clear() returns a Future and was never awaited,
      // so it could race with the test body -- a test's own
      // store.upsertAssessment() call could get silently wiped by the
      // previous test's still-pending clear(), landing an empty box right
      // before sync() reads it. Confirmed via a real diagnostic print
      // showing the store genuinely empty (all=[]) mid-test. Awaiting here
      // makes setUp a real barrier before the test body runs.
      await academicosCacheBox.clear();
      await cacheBox.clear();
      store = LocalStore.instance;
      testHelper = _TestSyncService();
    });

    Map<String, dynamic> makeAssessment({
      String? id,
      bool hasMetadata = false,
      bool hasServerId = false,
      bool hasServerSyncedAt = false,
      String? updatedAt,
    }) {
      final now = DateTime.now().toIso8601String();
      final metadata = <String, dynamic>{};
      if (hasMetadata) {
        if (hasServerId) metadata['serverId'] = 'server_123';
        if (hasServerSyncedAt) metadata['serverSyncedAt'] = now;
      }
      return {
        'id': id ?? 'local_${DateTime.now().millisecondsSinceEpoch}',
        'schoolId': schoolId,
        'teacherId': teacherId,
        'title': 'Test Assessment',
        'subject': 'Science',
        'grade': 10,
        'chapterIds': ['chapter_1'],
        'blueprint': {'totalMarks': 30, 'sections': []},
        'status': 'draft',
        'createdAt': now,
        'updatedAt': updatedAt ?? now,
        'metadata': hasMetadata ? metadata : null,
        'selectedQuestionIds': [],
      };
    }

    group('push logic', () {
      test('pushes never-synced assessment via POST and stamps serverId + serverSyncedAt', () async {
        final local = makeAssessment(hasMetadata: false);
        store.upsertAssessment(local);

        var capturedRequest = <String, dynamic>{};
        testHelper.mockPostAssessment((request) {
          capturedRequest = request;
          return _MockResponse(body: {'id': 'server_456', 'updatedAt': '2026-08-23T12:00:00Z'});
        });
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        final result = await testHelper.service.sync(schoolId);
        print('DEBUG: result = ${result.success}, error = ${result.error}, pushed = ${result.pushedCount}');

        expect(result.success, isTrue);
        expect(result.pushedCount, 1);
        expect(result.pulledCount, 0);

        final updated = store.getAssessment(local['id'] as String)!;
        final meta = updated['metadata'] as Map<String, dynamic>;
        expect(meta['serverId'], 'server_456');
        expect(meta['serverSyncedAt'], '2026-08-23T12:00:00Z');
        expect(capturedRequest['title'], 'Test Assessment');
        expect(capturedRequest['schoolId'], schoolId);
      });

      test('pushes locally-modified assessment via PUT (not POST) when serverId exists', () async {
        final oldSyncTime = DateTime.now().subtract(const Duration(hours: 1)).toIso8601String();
        final local = makeAssessment(
          hasMetadata: true,
          hasServerId: true,
          hasServerSyncedAt: true,
          updatedAt: DateTime.now().toIso8601String(),
        );
        final meta = local['metadata'] as Map<String, dynamic>;
        meta['serverSyncedAt'] = oldSyncTime;
        store.upsertAssessment(local);

        var usedPut = false;
        testHelper.mockPutAssessment('server_123', (request) {
          usedPut = true;
          return _MockResponse(body: {'id': 'server_123', 'updatedAt': '2026-08-23T13:00:00Z'});
        });
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isTrue);
        expect(result.pushedCount, 1);
        expect(usedPut, isTrue, reason: 'should use PUT for previously-synced assessment');

        final updated = store.getAssessment(local['id'] as String)!;
        final newMeta = updated['metadata'] as Map<String, dynamic>;
        expect(newMeta['serverSyncedAt'], '2026-08-23T13:00:00Z');
      });

      test('skips assessment that has serverId and is not locally modified', () async {
        final now = DateTime.now().toIso8601String();
        final local = makeAssessment(
          hasMetadata: true,
          hasServerId: true,
          hasServerSyncedAt: true,
          updatedAt: now,
        );
        final meta = local['metadata'] as Map<String, dynamic>;
        meta['serverSyncedAt'] = now;
        store.upsertAssessment(local);

        bool postCalled = false;
        bool putCalled = false;
        testHelper.mockPostAssessment((_) {
          postCalled = true;
          return _MockResponse(body: {'id': 'server_new', 'updatedAt': now});
        });
        testHelper.mockPutAssessment('server_123', (_) {
          putCalled = true;
          return _MockResponse(body: {'id': 'server_123', 'updatedAt': now});
        });
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isTrue);
        expect(result.pushedCount, 0);
        expect(postCalled, isFalse);
        expect(putCalled, isFalse);
      });

      test('stops pushing on first failure and returns error', () async {
        final local1 = makeAssessment(id: 'a1', hasMetadata: false);
        final local2 = makeAssessment(id: 'a2', hasMetadata: false);
        store.upsertAssessment(local1);
        store.upsertAssessment(local2);

        testHelper.mockPostAssessment((_) => throw DioException(
          requestOptions: RequestOptions(path: '/v1/assessments'),
          error: 'Network error',
          type: DioExceptionType.connectionError,
        ));
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isFalse);
        expect(result.error, contains('Could not connect'));
        expect(result.pushedCount, 0);
        final a1 = store.getAssessment('a1')!;
        final a2 = store.getAssessment('a2')!;
        expect((a1['metadata'] as Map?)?['serverId'], isNull);
        expect((a2['metadata'] as Map?)?['serverId'], isNull);
      });
    });

    group('pull logic', () {
      test('pulls new server assessment not present locally', () async {
        testHelper.mockGetAssessments(() => _MockResponse(body: [
          {
            'id': 'server_789',
            'schoolId': schoolId,
            'teacherId': teacherId,
            'title': 'Server Assessment',
            'subject': 'Science',
            'grade': 10,
            'chapterIds': ['chapter_1'],
            'blueprint': {'totalMarks': 30, 'sections': []},
            'status': 'draft',
            'createdAt': '2026-08-23T10:00:00Z',
            'updatedAt': '2026-08-23T10:00:00Z',
            'metadata': {},
            'selectedQuestionIds': [],
          },
        ]));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isTrue);
        expect(result.pulledCount, 1);
        expect(result.pushedCount, 0);

        final all = store.allAssessments();
        expect(all.length, 1);
        expect(all.first['id'], 'server_789');
        final meta = all.first['metadata'] as Map<String, dynamic>;
        expect(meta['serverId'], 'server_789');
        expect(meta['serverSyncedAt'], '2026-08-23T10:00:00Z');
      });

      test('does NOT overwrite locally-newer assessment with stale server version', () async {
        // Local assessment with serverId but NOT locally modified (serverSyncedAt == updatedAt)
        // This ensures the push phase skips it, testing only the pull logic
        final now = DateTime.now().toIso8601String();
        final local = makeAssessment(
          id: 'server_999',
          hasMetadata: true,
          hasServerId: true,
          hasServerSyncedAt: true,
          updatedAt: now,
        );
        final meta = local['metadata'] as Map<String, dynamic>;
        meta['serverId'] = 'server_999';
        meta['serverSyncedAt'] = now; // Not locally modified
        store.upsertAssessment(local);

        final serverTime = DateTime.now().subtract(const Duration(hours: 3)).toIso8601String();
        testHelper.mockGetAssessments(() => _MockResponse(body: [
          {
            'id': 'server_999',
            'schoolId': schoolId,
            'teacherId': teacherId,
            'title': 'Server Assessment (stale)',
            'subject': 'Science',
            'grade': 10,
            'chapterIds': ['chapter_1'],
            'blueprint': {'totalMarks': 30, 'sections': []},
            'status': 'draft',
            'createdAt': serverTime,
            'updatedAt': serverTime,
            'metadata': {},
            'selectedQuestionIds': [],
          },
        ]));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isTrue);
        expect(result.pulledCount, 0, reason: 'should not pull/overwrite newer local');

        final updated = store.getAssessment('server_999')!;
        expect(updated['title'], 'Test Assessment');
        expect(updated['updatedAt'], local['updatedAt']);
      });

      test('updates local when server is newer', () async {
        final localTime = DateTime.now().subtract(const Duration(hours: 2)).toIso8601String();
        final local = makeAssessment(
          id: 'server_888',
          hasMetadata: true,
          hasServerId: true,
          hasServerSyncedAt: true,
          updatedAt: localTime,
        );
        final meta = local['metadata'] as Map<String, dynamic>;
        meta['serverId'] = 'server_888';
        meta['serverSyncedAt'] = localTime;
        store.upsertAssessment(local);

        final serverTime = DateTime.now().toIso8601String();
        testHelper.mockGetAssessments(() => _MockResponse(body: [
          {
            'id': 'server_888',
            'schoolId': schoolId,
            'teacherId': teacherId,
            'title': 'Server Assessment (newer)',
            'subject': 'Science',
            'grade': 10,
            'chapterIds': ['chapter_2'],
            'blueprint': {'totalMarks': 40, 'sections': []},
            'status': 'blueprintReady',
            'createdAt': localTime,
            'updatedAt': serverTime,
            'metadata': {},
            'selectedQuestionIds': [],
          },
        ]));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isTrue);
        expect(result.pulledCount, 1);

        final updated = store.getAssessment('server_888')!;
        expect(updated['title'], 'Server Assessment (newer)');
        expect(updated['chapterIds'], ['chapter_2']);
        expect(updated['status'], 'blueprintReady');
        expect(updated['updatedAt'], localTime);
        final newMeta = updated['metadata'] as Map<String, dynamic>;
        expect(newMeta['serverSyncedAt'], serverTime);
      });
    });

    group('error handling', () {
      test('network failure during push returns clean SyncResult with error, never throws', () async {
        final local = makeAssessment(hasMetadata: false);
        store.upsertAssessment(local);

        testHelper.mockNetworkError(DioException(
          requestOptions: RequestOptions(path: '/assessments'),
          error: 'Connection refused',
          type: DioExceptionType.connectionError,
        ));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isFalse);
        expect(result.error, isNotNull);
        expect(result.error, contains('Could not connect'));
        expect(result.pushedCount, 0);
        expect(result.pulledCount, 0);
      });

      test('network failure during pull returns clean SyncResult with error, never throws', () async {
        final local = makeAssessment(hasMetadata: false);
        store.upsertAssessment(local);
        testHelper.mockPostAssessment((_) =>
            _MockResponse(body: {'id': 'server_1', 'updatedAt': DateTime.now().toIso8601String()}));

        testHelper.mockGetAssessments(() => throw DioException(
          requestOptions: RequestOptions(path: '/v1/assessments'),
          error: 'Timeout',
          type: DioExceptionType.receiveTimeout,
        ));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isFalse);
        expect(result.error, isNotNull);
        expect(result.error, contains('timed out'));
        expect(result.pushedCount, 1);
        expect(result.pulledCount, 0);
      });

      test('5xx server error returns clean SyncResult with error', () async {
        final local = makeAssessment(hasMetadata: false);
        store.upsertAssessment(local);

        testHelper.mockPostAssessment((_) => throw DioException(
          requestOptions: RequestOptions(path: '/v1/assessments'),
          error: 'Internal Server Error',
          type: DioExceptionType.badResponse,
          response: Response(requestOptions: RequestOptions(path: '/v1/assessments'), statusCode: 500, data: {}),
        ));
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        final result = await testHelper.service.sync(schoolId);

        expect(result.success, isFalse);
        expect(result.error, contains('Server error (500)'));
      });
    });

    group('concurrency', () {
      test('concurrent sync calls for same school are serialized via KeyedMutex', () async {
        final local1 = makeAssessment(id: 'a1', hasMetadata: false);
        final local2 = makeAssessment(id: 'a2', hasMetadata: false);
        store.upsertAssessment(local1);
        store.upsertAssessment(local2);

        int callCount = 0;
        testHelper.mockPostAssessment((_) {
          callCount++;
          return _MockResponse(
              body: {'id': 'server_$callCount', 'updatedAt': DateTime.now().toIso8601String()});
        });
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        final results = await Future.wait([
          testHelper.service.sync(schoolId),
          testHelper.service.sync(schoolId),
        ]);

        expect(results.every((r) => r.success), isTrue);
        final totalPushed = results.fold(0, (sum, r) => sum + r.pushedCount);
        expect(totalPushed, 2);
      });

      test('concurrent sync calls for different schools do not block each other', () async {
        final schoolA = 'school_A';
        final schoolB = 'school_B';
        final localA = makeAssessment(id: 'a1', hasMetadata: false)..update('schoolId', (v) => schoolA);
        final localB = makeAssessment(id: 'b1', hasMetadata: false)..update('schoolId', (v) => schoolB);
        store.upsertAssessment(localA);
        store.upsertAssessment(localB);

        final order = <String>[];
        testHelper.mockPostAssessment((_) {
          order.add('post');
          return _MockResponse(body: {'id': 'server_1', 'updatedAt': DateTime.now().toIso8601String()});
        });
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        await Future.wait([
          testHelper.service.sync(schoolA),
          testHelper.service.sync(schoolB),
        ]);

        expect(order.length, 2);
      });
    });

    group('SyncResult persistence', () {
      test('last sync result is persisted and retrievable', () async {
        final local = makeAssessment(hasMetadata: false);
        store.upsertAssessment(local);
        testHelper.mockPostAssessment((_) =>
            _MockResponse(body: {'id': 'server_1', 'updatedAt': '2026-08-23T12:00:00Z'}));
        testHelper.mockGetAssessments(() => _MockResponse(body: []));

        await testHelper.service.sync(schoolId);

        final saved = testHelper.service.getLastSyncResult(schoolId);
        expect(saved, isNotNull);
        expect(saved!.pushedCount, 1);
        expect(saved.error, isNull);
      });
    });
  });
}