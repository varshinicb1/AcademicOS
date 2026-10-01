import 'package:get_it/get_it.dart';

import '../../data/datasources/api/api_client.dart';
import '../local_engine/local_api_client.dart';
import '../local_engine/local_store.dart';
import '../local_engine/offline_identity.dart';

/// Who is using the app, and for which school -- the one place a screen gets
/// a school id or user id from.
///
/// Signed in (the web, or any server-backed build), it is the user the
/// login/register response named (auth_api.dart's AuthUser, kept in
/// LocalStore.authUser by login_page.dart). The live release (a153003)
/// instead read `AppConstants.currentSchoolId = 'demo_school'` and a literal
/// 'teacher_1': for a real school the assessment list, planner and scan list
/// came back empty, the principal dashboard answered 403, and custom paper
/// creation failed with 403 (re-audit, 2026-09-22).
///
/// While the on-device engine is the ApiClient (the offline Android build) it
/// is that device's own identity (OfflineIdentity), because every local record
/// is stored under it -- signing in there for sync does not re-key them.
///
/// Signed out on the web there is no identity, and the getters return '':
/// the router sends a signed-out user to Sign in, and a request that slips
/// through gets the server's 401/403 rather than another school's data.
class CurrentSession {
  CurrentSession._();

  static bool get _onDevice {
    final sl = GetIt.instance;
    if (sl.isRegistered<ApiClient>()) return sl<ApiClient>() is LocalApiClient;
    return const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
  }

  static String _field(String key) => LocalStore.instance.authUser?[key] as String? ?? '';

  /// The school every school-scoped request is made for.
  static String get schoolId => _onDevice ? OfflineIdentity.schoolId : _field('schoolId');

  /// The signed-in user's id (the teacher who creates an assessment).
  static String get userId => _onDevice ? OfflineIdentity.teacherId : _field('id');

  /// "teacher" | "principal" | "student" online; the device profile's role offline.
  static String get role => _onDevice ? LocalStore.instance.teacherRole : _field('role');

  /// The signed-in person's name as the school knows it (empty offline).
  static String get name => _onDevice ? '' : _field('name');

  /// An owner account over several schools (ROLE-4): role "owner" until it
  /// chooses one of them, then that school's "principal". Never offline.
  static bool get isOwner =>
      !_onDevice && (LocalStore.instance.authUser?['isOwner'] == true || _field('role') == 'owner');
}
