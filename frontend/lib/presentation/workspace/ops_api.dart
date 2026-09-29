import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';

/// Thin calls to the school-operations API (homework, progress, parents,
/// cover, exams, notifications, admin tools). The shared Dio already carries
/// the base URL (`.../api/v1`) and the session token, so paths here are
/// relative to it. Every failure becomes an [OpsError] whose message is the
/// server's own `detail`, which is written for the person using the app.
class Ops {
  Ops._();

  static Dio get _dio => GetIt.I<Dio>();

  static Future<dynamic> get(String path, {Map<String, dynamic>? query}) =>
      _call(() => _dio.get(path, queryParameters: query));

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
