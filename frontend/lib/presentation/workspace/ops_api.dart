import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../core/local_engine/local_store.dart';
import '../../core/session/current_session.dart';

/// Thin calls to the school-operations API (homework, progress, parents,
/// cover, exams, notifications, admin tools). The shared Dio already carries
/// the base URL (`.../api/v1`) and the session token, so paths here are
/// relative to it. Every failure becomes an [OpsError] whose message is the
/// server's own `detail`, which is written for the person using the app.
class Ops {
  Ops._();

  static Dio get _dio => GetIt.I<Dio>();

  /// When the last read was answered from this device's saved copy because
  /// the server could not be reached; null when the last read was live.
  static final ValueNotifier<DateTime?> offlineSince = ValueNotifier(null);

  /// A read. Its answer is saved on the device, per signed-in user; when the
  /// server cannot be reached at all, the saved answer is returned instead
  /// (TA-8, SA-8: a phone without signal still shows today's timetable,
  /// homework and progress). Writes are never answered from the cache.
  static Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    final key = _cacheKey(path, query);
    try {
      final data = await _call(() => _dio.get(path, queryParameters: query));
      _save(key, data);
      offlineSince.value = null;
      return data;
    } on OpsError catch (e) {
      if (e.status != null) rethrow;          // the server answered: a real refusal, not "offline"
      final saved = _load(key);
      if (saved == null) rethrow;
      offlineSince.value = DateTime.tryParse(saved['at'] as String? ?? '');
      return saved['data'];
    }
  }

  static String _cacheKey(String path, Map<String, dynamic>? query) {
    final q = (query ?? const {}).entries.map((e) => '${e.key}=${e.value}').toList()..sort();
    return 'ops_cache:${CurrentSession.userId}:$path?${q.join('&')}';
  }

  static void _save(String key, dynamic data) {
    if (data is! Map && data is! List) return;   // text (CSV, calendars) is not worth keeping offline
    try {
      LocalStore.instance.box.put(key, jsonEncode({'at': DateTime.now().toIso8601String(), 'data': data}));
    } catch (_) {
      // not-a-failure: the live answer is already in hand; only its offline copy was not kept
    }
  }

  static Map<String, dynamic>? _load(String key) {
    final raw = LocalStore.instance.box.get(key);
    return raw is String ? Map<String, dynamic>.from(jsonDecode(raw) as Map) : null;
  }

  static Future<dynamic> post(String path, {Object? body, Map<String, dynamic>? query}) =>
      _call(() => _dio.post(path, data: body, queryParameters: query));

  static Future<dynamic> put(String path, {Object? body, Map<String, dynamic>? query}) =>
      _call(() => _dio.put(path, data: body, queryParameters: query));

  static Future<dynamic> patch(String path, {Object? body}) => _call(() => _dio.patch(path, data: body));

  static Future<dynamic> delete(String path) => _call(() => _dio.delete(path));

  static Future<List<Map<String, dynamic>>> list(String path, {Map<String, dynamic>? query}) async {
    final data = await get(path, query: query);
    return (data as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Future<Map<String, dynamic>> map(String path, {Map<String, dynamic>? query}) async =>
      Map<String, dynamic>.from(await get(path, query: query) as Map);

  static Future<dynamic> _call(Future<Response<dynamic>> Function() send) async {
    try {
      return (await send()).data;
    } on DioException catch (e) {
      throw OpsError.from(e);
    }
  }
}

class OpsError implements Exception {
  final int? status;
  final String message;
  OpsError(this.status, this.message);

  factory OpsError.from(DioException e) {
    final data = e.response?.data;
    String msg = 'Something went wrong. Check your connection and try again.';
    if (data is Map && data['detail'] != null) {
      final d = data['detail'];
      if (d is String) {
        msg = d;
      } else if (d is Map && d['message'] != null) {
        msg = d['message'].toString();
      } else if (d is List && d.isNotEmpty && d.first is Map) {
        msg = (d.first as Map)['msg']?.toString() ?? msg;
      }
    }
    return OpsError(e.response?.statusCode, msg);
  }

  @override
  String toString() => message;
}

/// "2026-06-03" from a DateTime, the school's own calendar date.
String isoDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// "Offline: showing what was saved at 09:12", while reads come from the
/// device's saved copies.
class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<DateTime?>(
      valueListenable: Ops.offlineSince,
      builder: (context, at, _) {
        if (at == null) return const SizedBox.shrink();
        final t = at.toLocal();
        final hhmm = '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
        return MaterialBanner(
          leading: const Icon(Icons.cloud_off),
          content: Text('Offline: showing what was saved at $hhmm on ${t.day}/${t.month}. '
              'Changes need a connection.'),
          actions: [TextButton(onPressed: () => Ops.offlineSince.value = null, child: const Text('OK'))],
        );
      },
    );
  }
}
