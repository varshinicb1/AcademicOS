/// The one school and teacher the offline Android build works as.
///
/// That build has no server and no login: every record the on-device engine
/// writes to LocalStore is keyed to this device identity, and the demo seeder
/// (demo_seeder.dart) seeds under it. It is never an identity on the web:
/// CurrentSession (core/session/current_session.dart) returns it only while
/// the on-device engine is the ApiClient, and the web always talks to a
/// server that knows who signed in. Until Task 604 these values lived in
/// AppConstants as the whole app's "current school", and the live web app
/// asked every real school's server for 'demo_school'.
class OfflineIdentity {
  OfflineIdentity._();

  /// The value the offline build has always stored its data under; kept so
  /// an installed device's existing assessments still list.
  static const String schoolId = 'demo_school';

  /// The teacher id the offline engine stamps on the papers it generates.
  static const String teacherId = 'teacher_1';
}
