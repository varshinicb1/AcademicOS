/// Client for the real teacher/principal identity endpoints
/// (src/academicos/assessment/auth_routes.py) -- the online-build
/// counterpart to LocalStore's teacherName/teacherRole for the offline
/// build. Plain maps/classes, same style as pillar_api.dart, for the same
/// reason: no build_runner cycle needed for what's fundamentally simple,
/// read-mostly data.
library;

import 'package:dio/dio.dart';

import 'api_error.dart';

class AuthUser {
  final String id;
  final String schoolId;
  final String name;
  final String email;
  final String role; // "teacher" | "principal" | "student" | "parent" | "owner"

  /// ROLE-4: an owner account over several schools. Its role is "owner"
  /// until it chooses a school, then "principal" of that school; this stays
  /// true either way. Optional on the wire (`isOwner` defaults to false).
  final bool isOwner;

  AuthUser.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        schoolId = j['schoolId'] as String,
        name = j['name'] as String,
        email = j['email'] as String,
        role = j['role'] as String,
        isOwner = j['isOwner'] as bool? ?? false;

  Map<String, dynamic> toJson() =>
      {'id': id, 'schoolId': schoolId, 'name': name, 'email': email, 'role': role, 'isOwner': isOwner};

  bool get isPrincipal => role == 'principal';
  bool get isStudent => role == 'student';
}

/// One row of GET /auth/invites. `status` is "open" | "used" | "revoked" |
/// "expired"; `usedBy`/`usedAt` say which account used it and when.
class Invite {
  final String code;
  final String role;
  final String? email;
  final String expiresAt;
  final String createdAt;
  final String createdBy;
  final String status;
  final String? usedBy;
  final String? usedAt;
  final String? revokedAt;

  Invite.fromJson(Map<String, dynamic> j)
      : code = j['code'] as String,
        role = j['role'] as String,
        email = j['email'] as String?,
        expiresAt = j['expiresAt'] as String,
        createdAt = j['createdAt'] as String,
        createdBy = j['createdBy'] as String,
        status = j['status'] as String,
        usedBy = j['usedBy'] as String?,
        usedAt = j['usedAt'] as String?,
        revokedAt = j['revokedAt'] as String?;

  bool get isOpen => status == 'open';
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

  /// Join a school with an invite code a principal issued. The server takes
  /// the account's school and role from the invite, so there is nothing
  /// else to choose here (users.py: until 2026-09-21 the client named its
  /// own school and role, and an outsider could join any school by id).
  Future<AuthResult> register({
    required String inviteCode,
    required String name,
    required String email,
    required String password,
  }) =>
      _register({
        'inviteCode': inviteCode, 'name': name, 'email': email, 'password': password,
      });

  /// The operator's path for a NEW school's first principal: the school id
  /// plus the principal key the operator handed over. The server refuses it
  /// (403) once that school has a principal; everyone after that joins by
  /// invite.
  Future<AuthResult> registerFirstPrincipal({
    required String schoolId,
    required String principalKey,
    required String name,
    required String email,
    required String password,
  }) =>
      _register({
        'schoolId': schoolId, 'principalKey': principalKey,
        'name': name, 'email': email, 'password': password,
      });

  /// An owner account over several schools (ROLE-4), created with the first
  /// school's owner link code (`own_...`) that school's principal issued.
  Future<AuthResult> registerOwner({
    required String code,
    required String name,
    required String email,
    required String password,
  }) =>
      _register({'code': code, 'name': name, 'email': email, 'password': password}, path: '/owner/register');

  Future<AuthResult> _register(Map<String, dynamic> body, {String path = '/auth/register'}) async {
    try {
      final r = await _dio.post(path, data: body);
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

  // ---- invites (principal only; always the caller's own school) ----

  /// A single-use invite to the caller's school. `role` is "teacher" or
  /// "student"; `email` binds it to one person; `expiresInDays` is 1..90
  /// (server default 14). There is no school field: the server uses the
  /// principal's own.
  Future<Invite> createInvite({required String role, String? email, int? expiresInDays}) async {
    try {
      final r = await _dio.post('/auth/invites', data: {
        'role': role,
        if (email != null && email.isNotEmpty) 'email': email,
        if (expiresInDays != null) 'expiresInDays': expiresInDays,
      });
      return Invite.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      throw _asAuthException(e);
    }
  }

  /// Every invite the school has issued, used and unused, newest first.
  Future<List<Invite>> invites() async {
    final r = await _dio.get('/auth/invites');
    return (r.data as List).map((e) => Invite.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// Withdraw an unused invite. A used one cannot be withdrawn (409).
  Future<Invite> revokeInvite(String code) async {
    try {
      final r = await _dio.delete('/auth/invites/${Uri.encodeComponent(code)}');
      return Invite.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      throw _asAuthException(e);
    }
  }

  /// The sign-in and invite forms' own wording for the statuses they expect;
  /// everything else goes through the shared serverErrorMessage. Until Task
  /// 802 the fallback was "Could not reach the server" for any status, so a
  /// principal whose invite hit a 500 was told to check a working connection,
  /// and a 422 (detail is a list) crashed the `as String?` cast here with a
  /// TypeError the form then reported as a network fault.
  AuthException _asAuthException(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;
    final detail = data is Map && data['detail'] is String ? data['detail'] as String : null;
    if (status == 401) {
      // Wrong credentials only on sign-in/register; on the invite calls a
      // 401 is a session that ended, not a password the principal mistyped.
      final path = e.requestOptions.path;
      final signingIn = path == '/auth/login' || path == '/auth/register';
      return AuthException(signingIn ? detail ?? 'Incorrect email or password.' : serverErrorMessage(e));
    }
    if (status == 409) return AuthException(detail ?? 'An account with this email already exists.');
    if (status == 400) return AuthException(detail ?? 'Password must be at least 8 characters.');
    // Registration without a usable invite, or a principal key for a school
    // that already has a principal. The server's message says which.
    if (status == 403) {
      return AuthException(detail ?? "You need an invite code from your school's principal.");
    }
    return AuthException(serverErrorMessage(e));
  }
}
