/// Client for the real teacher/principal identity endpoints
/// (src/academicos/assessment/auth_routes.py) -- the online-build
/// counterpart to LocalStore's teacherName/teacherRole for the offline
/// build. Plain maps/classes, same style as pillar_api.dart, for the same
/// reason: no build_runner cycle needed for what's fundamentally simple,
/// read-mostly data.
library;

import 'package:dio/dio.dart';

class AuthUser {
  final String id;
  final String schoolId;
  final String name;
  final String email;
  final String role; // "teacher" | "principal" | "student"

  AuthUser.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        schoolId = j['schoolId'] as String,
        name = j['name'] as String,
        email = j['email'] as String,
        role = j['role'] as String;

  Map<String, dynamic> toJson() =>
      {'id': id, 'schoolId': schoolId, 'name': name, 'email': email, 'role': role};

  bool get isPrincipal => role == 'principal';
  bool get isStudent => role == 'student';
}

class AuthResult {
  final AuthUser user;
  final String token;
  AuthResult.fromJson(Map<String, dynamic> j)
      : user = AuthUser.fromJson(Map<String, dynamic>.from(j['user'] as Map)),
        token = j['token'] as String;
}

/// Thrown for a real, user-facing auth failure (wrong password, duplicate
/// email, weak password) so callers can show `message` directly rather than
/// a raw DioException — every other failure (network, 5xx) is left as a
/// DioException, same as every other API client in this app.
class AuthException implements Exception {
  final String message;
  AuthException(this.message);
  @override
  String toString() => message;
}

class AuthApi {
  final Dio _dio;
  AuthApi(Dio dio) : _dio = dio;

  Future<AuthResult> register({
    required String schoolId,
    required String name,
    required String email,
    required String password,
    // Self-selected: "teacher" (default, unchanged) or "student". Never
    // "principal" -- the server only grants that via a matching
    // principal_key, this field can't escalate to it (see
    // users.py::UserStore.register's docstring).
    String? role,
  }) async {
    try {
      final r = await _dio.post('/auth/register', data: {
        'schoolId': schoolId, 'name': name, 'email': email, 'password': password,
        if (role != null) 'role': role,
      });
      return AuthResult.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      throw _asAuthException(e);
    }
  }

  Future<AuthResult> login({required String email, required String password}) async {
    try {
      final r = await _dio.post('/auth/login', data: {'email': email, 'password': password});
      return AuthResult.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      throw _asAuthException(e);
    }
  }

  /// Best-effort: a stale/already-expired token logging out is not a real
  /// error the caller needs to react to differently than success.
  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } on DioException {
      // ignore
    }
  }

  Future<AuthUser> me() async {
    final r = await _dio.get('/auth/me');
    return AuthUser.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// The real roster an admin picks a teacher/student from -- principal-
  /// gated and school-scoped server-side by the caller's own token.
  /// `role` filters to "teacher" | "principal" | "student"; omit for
  /// everyone at the school.
  Future<List<AuthUser>> usersForSchool({String? role}) async {
    final r = await _dio.get('/auth/users', queryParameters: {if (role != null) 'role': role});
    return (r.data as List).map((e) => AuthUser.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  AuthException _asAuthException(DioException e) {
    final status = e.response?.statusCode;
    final detail = e.response?.data is Map ? (e.response?.data['detail'] as String?) : null;
    if (status == 401) return AuthException(detail ?? 'Incorrect email or password.');
    if (status == 409) return AuthException(detail ?? 'An account with this email already exists.');
    if (status == 400) return AuthException(detail ?? 'Password must be at least 8 characters.');
    return AuthException(detail ?? 'Could not reach the server. Check your connection and try again.');
  }
}
