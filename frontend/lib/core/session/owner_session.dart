import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:get_it/get_it.dart';

import '../local_engine/local_store.dart';

/// An owner over several schools (ROLE-4): its linked schools, and which one
/// its session acts in.
///
/// Choosing a school makes the session that school's principal on the server
/// (auth_routes.get_current_user), so every page works as it does for that
/// school's own principal and sees that school's data only. The answer is
/// the session's new identity; it replaces the signed-in user kept on this
/// device, which is where CurrentSession reads the role and school from.
class OwnerSession {
  OwnerSession._();

  static Dio get _dio => GetIt.I<Dio>();

  /// Bumped on every switch, so the shell rebuilds its page for the new
  /// school even when the location does not change.
  static final ValueNotifier<int> switched = ValueNotifier(0);

  /// The schools linked to this account: `{schoolId, name, linkedAt, active}`.
  static Future<List<Map<String, dynamic>>> schools() async {
    final r = await _dio.get('/owner/schools');
    return (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  /// Act in [schoolId] from now on.
  static Future<void> choose(String schoolId) async {
    final r = await _dio.post('/owner/active-school', data: {'schoolId': schoolId});
    LocalStore.instance.authUser = Map<String, dynamic>.from(r.data as Map);
    switched.value++;
  }

  /// Stop acting in a school: back to the owner's own pages.
  static Future<void> leave() async {
    final r = await _dio.delete('/owner/active-school');
    LocalStore.instance.authUser = Map<String, dynamic>.from(r.data as Map);
    switched.value++;
  }

  /// Link one more school with the code its principal issued.
  static Future<Map<String, dynamic>> redeem(String code) async {
    final r = await _dio.post('/owner/links/redeem', data: {'code': code.trim()});
    return Map<String, dynamic>.from(r.data as Map);
  }
}
