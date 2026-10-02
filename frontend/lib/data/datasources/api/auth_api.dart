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

/// POST /students/{id}/guardian-invites: a single-use parent invite linked
/// to one child (operations/guardian_routes.py). Whoever registers with the
/// code gets a parent account linked to that student.
class GuardianInvite {
  final String code;
  final String studentId;
  final String relation;
  final String? email;
  final String expiresAt;

  GuardianInvite.fromJson(Map<String, dynamic> j)
      : code = j['code'] as String,
        studentId = j['studentId'] as String,
        relation = j['relation'] as String,
        email = j['email'] as String?,
        expiresAt = j['expiresAt'] as String;
}

/// POST /auth/users/{id}/password-reset: the one-time password the principal
/// reads out. It is shown once and kept nowhere else.
class PasswordReset {
  final String userId;
  final String name;
  final String temporaryPassword;

  PasswordReset.fromJson(Map<String, dynamic> j)
      : userId = j['userId'] as String,
        name = j['name'] as String,
        temporaryPassword = j['temporaryPassword'] as String;
}

/// One store's share of an erasure: what it holds of the person (`count`).
class ErasurePart {
  final String part;
  final String label;
  final int count;
  final String? error;

  ErasurePart.fromJson(Map<String, dynamic> j)
      : part = j['part'] as String,
        label = j['label'] as String,
        count = (j['count'] as num).toInt(),
        error = j['error'] as String?;
}

/// GET /auth/users/{id}/erasure: what an erasure would delete, and what
/// stays and why (the audit log, a parent's consent for a child, backups).
class ErasurePreview {
  final String userId;
  final String name;
  final String role; // "student" | "parent"
  final bool closed;
  final List<ErasurePart> parts;
  final List<(String what, String why)> kept;

  ErasurePreview.fromJson(Map<String, dynamic> j)
      : userId = j['userId'] as String,
        name = j['name'] as String,
        role = j['role'] as String,
        closed = j['closed'] as bool,
        parts = (j['parts'] as List).map((e) => ErasurePart.fromJson(Map<String, dynamic>.from(e))).toList(),
        kept = (j['kept'] as List).map((e) => ((e as Map)['what'] as String, e['why'] as String)).toList();
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

/// The relations a guardian invite takes (operations/guardians.py RELATIONS).
const guardianRelations = ['mother', 'father', 'guardian', 'grandparent', 'other'];

/// "incorrect email or password" -> "Incorrect email or password."
String asSentence(String text) {
  final t = text.trim();
  if (t.isEmpty) return t;
  final first = t[0].toUpperCase() + t.substring(1);
  return RegExp(r'[.!?]$').hasMatch(first) ? first : '$first.';
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

  Future<AuthResult> _register(Map<String, dynamic> body) async {
    try {
      final r = await _dio.post('/auth/register', data: body);
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

  /// A single-use invite for one of [studentId]'s parents or guardians.
  /// `relation` is one of [guardianRelations]. Principal, or a teacher with
  /// the people admin area.
  Future<GuardianInvite> createGuardianInvite(
      {required String studentId, required String relation, String? email, int? expiresInDays}) async {
    try {
      final r = await _dio.post('/students/${Uri.encodeComponent(studentId)}/guardian-invites', data: {
        'relation': relation,
        if (email != null && email.isNotEmpty) 'email': email,
        if (expiresInDays != null) 'expiresInDays': expiresInDays,
      });
      return GuardianInvite.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      throw _asAuthException(e);
    }
  }

  /// Sets a one-time password for a teacher, student or parent of the
  /// caller's school and signs them out everywhere (QA S-05). The server
  /// refuses the principal's own account and another principal's (403).
  Future<PasswordReset> resetPassword(String userId) async {
    try {
      final r = await _dio.post('/auth/users/${Uri.encodeComponent(userId)}/password-reset');
      return PasswordReset.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      throw _asAuthException(e);
    }
  }

  /// Changes the signed-in person's own password. The server ends every
  /// session, this one included, and answers with a new token for this
  /// device, which is returned for the caller to keep.
  Future<String> changePassword({required String currentPassword, required String newPassword}) async {
    try {
      final r = await _dio.post('/auth/password',
          data: {'currentPassword': currentPassword, 'newPassword': newPassword});
      return (r.data as Map)['token'] as String;
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

  /// What erasing this student or parent would delete, part by part, and
  /// what would stay (GET /auth/users/{id}/erasure; principal only). Changes
  /// nothing.
  Future<ErasurePreview> erasurePreview(String userId) async {
    final r = await _dio.get('/auth/users/${Uri.encodeComponent(userId)}/erasure');
    return ErasurePreview.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Erase a student's or parent's data on the school's written request
  /// (DPDP). Cannot be undone. `requestedBy` is "parent" | "student" |
  /// "school"; `requestReceivedOn` is the day the request reached the school;
  /// `confirmName` must be the person's name. A 503 means some part could not
  /// be erased yet: the account stays closed and running it again finishes it.
  Future<List<ErasurePart>> erase(String userId,
      {required String requestedBy, required DateTime requestReceivedOn, required String confirmName}) async {
    final day = '${requestReceivedOn.year.toString().padLeft(4, '0')}-'
        '${requestReceivedOn.month.toString().padLeft(2, '0')}-${requestReceivedOn.day.toString().padLeft(2, '0')}';
    final r = await _dio.post('/auth/users/${Uri.encodeComponent(userId)}/erasure', data: {
      'requestedBy': requestedBy, 'requestReceivedOn': day, 'confirmName': confirmName,
    });
    return ((r.data as Map)['parts'] as List).map((e) => ErasurePart.fromJson(Map<String, dynamic>.from(e))).toList();
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
    final raw = data is Map && data['detail'] is String ? data['detail'] as String : null;
    // The server writes its reasons in lower case with no full stop
    // ("incorrect email or password"); the form shows them as sentences.
    final detail = raw == null || raw.trim().isEmpty ? null : asSentence(raw);
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
