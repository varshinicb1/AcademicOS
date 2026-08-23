import 'dart:convert';

import 'package:dio/dio.dart';

import '../local_engine/keyed_mutex.dart';
import '../local_engine/local_store.dart';

/// Result of a single sync operation.
class SyncResult {
  const SyncResult({
    required this.pushedCount,
    required this.pulledCount,
    required this.error,
    required this.timestamp,
  });

  final int pushedCount;
  final int pulledCount;
  final String? error;
  final DateTime timestamp;

  bool get success => error == null;

  Map<String, dynamic> toJson() => {
        'pushedCount': pushedCount,
        'pulledCount': pulledCount,
        'error': error,
        'timestamp': timestamp.toIso8601String(),
      };

  factory SyncResult.fromJson(Map<String, dynamic> json) => SyncResult(
        pushedCount: json['pushedCount'] as int,
        pulledCount: json['pulledCount'] as int,
        error: json['error'] as String?,
        timestamp: DateTime.parse(json['timestamp'] as String),
      );
}

/// Background reconciliation service for assessments.
/// Local-first: all writes succeed instantly offline; sync runs when online.
class SyncService {
  SyncService._();

  static final SyncService instance = SyncService._();

  final KeyedMutex _mutex = KeyedMutex();
  final LocalStore _store = LocalStore.instance;

  /// Builds a Dio instance pointing at the same API base used by the rest of the app.
  Dio _buildDio() {
    const apiBase = String.fromEnvironment(
      'ACADEMICOS_API',
      defaultValue: 'http://localhost:8010/api/v1',
    );
    return Dio(BaseOptions(
      baseUrl: apiBase,
      connectTimeout: const Duration(seconds: 90),
      receiveTimeout: const Duration(seconds: 90),
      headers: {'Content-Type': 'application/json'},
    ));
  }

  /// Persists the last sync result for the given school.
  Future<void> _saveLastSyncResult(String schoolId, SyncResult result) async {
    _store.box.put('last_sync_result_$schoolId', jsonEncode(result.toJson()));
  }

  /// Retrieves the last sync result for the given school.
  SyncResult? getLastSyncResult(String schoolId) {
    final raw = _store.box.get('last_sync_result_$schoolId') as String?;
    if (raw == null) return null;
    return SyncResult.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  /// Checks if an assessment has been modified locally since its last server sync.
  bool _isLocallyModified(Map<String, dynamic> local) {
    final metadata = local['metadata'] as Map<String, dynamic>?;
    if (metadata == null) return true; // no metadata means never synced
    final serverSyncedAt = metadata['serverSyncedAt'] as String?;
    if (serverSyncedAt == null) return true; // never synced
    final localUpdatedAt = local['updatedAt'] as String?;
    if (localUpdatedAt == null) return false;
    return DateTime.parse(localUpdatedAt).isAfter(DateTime.parse(serverSyncedAt));
  }

  /// Checks if an assessment has never been synced to the server.
  bool _neverSynced(Map<String, dynamic> local) {
    final metadata = local['metadata'] as Map<String, dynamic>?;
    return metadata == null || metadata['serverId'] == null;
  }

  /// Performs a full sync (push + pull) for the given school.
  /// Returns a SyncResult with counts and any error.
  Future<SyncResult> sync(String schoolId) async {
    return _mutex.synchronized('sync_$schoolId', () async {
      final dio = _buildDio();
      int pushedCount = 0;
      int pulledCount = 0;
      String? error;

      try {
        // PUSH: local -> server
        pushedCount = await _pushLocalAssessments(dio, schoolId);

        // PULL: server -> local
        pulledCount = await _pullServerAssessments(dio, schoolId);
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

  /// Pushes local assessments that are new or locally modified.
  Future<int> _pushLocalAssessments(Dio dio, String schoolId) async {
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
          // POST for new assessments
          final request = _toServerCreateRequest(local);
          final response = await dio.post('/assessments', data: request);
          responseData = response.data as Map<String, dynamic>;
        } else {
          // PUT for existing assessments
          final metadata = local['metadata'] as Map<String, dynamic>;
          final serverId = metadata['serverId'] as String;
          final request = _toServerUpdateRequest(local);
          final response = await dio.put('/assessments/$serverId', data: request);
          responseData = response.data as Map<String, dynamic>;
        }

        // Update local record with serverId and serverSyncedAt
        final serverId = responseData['id'] as String;
        final serverUpdatedAt = responseData['updatedAt'] as String;

        final metadata = Map<String, dynamic>.from(local['metadata'] as Map? ?? {});
        metadata['serverId'] = serverId;
        metadata['serverSyncedAt'] = serverUpdatedAt;

        final updated = Map<String, dynamic>.from(local);
        updated['metadata'] = metadata;
        // Keep local updatedAt as-is (it's the source of truth for local modifications)
        // Server's updatedAt is tracked separately in metadata.serverSyncedAt

        _store.upsertAssessment(updated);
        pushed++;
      } catch (e) {
        // Stop pushing on first failure to avoid partial state
        rethrow;
      }
    }

    return pushed;
  }

  /// Pulls assessments from server and merges with local store.
  Future<int> _pullServerAssessments(Dio dio, String schoolId) async {
    final response = await dio.get('/assessments', queryParameters: {'school_id': schoolId});
    final serverAssessments = (response.data as List).cast<Map<String, dynamic>>();

    int pulled = 0;

    for (final server in serverAssessments) {
      final serverId = server['id'] as String;
      final serverUpdatedAt = server['updatedAt'] as String;

      // Check if we have this locally by serverId
      final localIndex = _store.allAssessments().indexWhere((a) {
        final meta = a['metadata'] as Map<String, dynamic>?;
        return meta?['serverId'] == serverId;
      });

      if (localIndex < 0) {
        // New from server - insert
        final local = _serverToLocal(server);
        _store.upsertAssessment(local);
        pulled++;
      } else {
        // Exists locally - check if server is newer
        final local = _store.allAssessments()[localIndex];
        final localUpdatedAt = local['updatedAt'] as String?;

        if (localUpdatedAt != null &&
            DateTime.parse(serverUpdatedAt).isAfter(DateTime.parse(localUpdatedAt))) {
          // Server wins - update local
          final localMeta = Map<String, dynamic>.from(local['metadata'] as Map? ?? {});
          localMeta['serverSyncedAt'] = serverUpdatedAt;

          final merged = _serverToLocal(server);
          merged['metadata'] = localMeta;
          // Keep local updatedAt if it's newer (shouldn't happen here since we checked)
          // but preserve the local updatedAt to track local modifications
          merged['updatedAt'] = localUpdatedAt;

          _store.upsertAssessment(merged);
          pulled++;
        } else {
          // Debug: local is newer or equal
          // print('PULL SKIP: serverUpdatedAt=$serverUpdatedAt, localUpdatedAt=$localUpdatedAt');
        }
        // else: local is newer or equal, leave it alone
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
      'id': server['id'], // Keep server ID as local ID for now
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