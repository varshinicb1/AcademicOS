/// When this app is allowed to touch the network -- one switch, one guard.
///
/// The Mobile build (`--dart-define=ACADEMICOS_OFFLINE=true`) is the
/// primary surface and is promised to never contact a backend unless the
/// teacher opts in (PRD section 0 decision 12; the opt-in itself is Task
/// 405). Until 2026-09-22 that promise was kept only by accident: the
/// release AndroidManifest has no INTERNET permission, while three call
/// sites in the offline build (Settings > Manual Sync, the Classes page's
/// consent POST carrying a student id and a guardian's name, and the
/// subtopic fetch on New Assessment) went straight to a Dio whose base was
/// `http://localhost:8010/api/v1` -- live in every debug/profile APK, whose
/// manifests DO declare INTERNET. This file is the guard that no longer
/// depends on the manifest.
library;

import 'package:dio/dio.dart';

import '../local_engine/local_store.dart';

/// True only in the standalone Android build. The one spelling of the flag
/// new code should use (older pages still declare their own private copy).
const kOfflineBuild = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

/// The release AndroidManifest.xml declares no INTERNET permission, so any
/// feature that needs the network (Settings > Download Data, the opt-in
/// Sarvam Vision OCR upgrade) cannot work in a release APK -- it would fail
/// with a connection error the teacher cannot fix. Such features are hidden
/// in the offline build instead of left silently broken. Adding the
/// permission is a product decision; flip this together with the manifest.
const kOfflineBuildHasInternet = false;

/// The teacher's opt-in to sync. Off by default, off in every test (a fresh
/// Hive box has no key), and until Task 405 builds the Settings switch
/// nothing in the app turns it on.
class SyncSettings {
  SyncSettings._();

  static const _key = 'sync_enabled';

  static bool get enabled => LocalStore.instance.box.get(_key, defaultValue: false) as bool;

  static set enabled(bool value) => LocalStore.instance.box.put(_key, value);
}

/// Whether an HTTP request may leave the device right now. The Web build is
/// a thin client -- every action is a request, so it is always allowed.
/// The offline build allows one only after the teacher turns sync on.
bool networkAllowed({required bool offline}) => !offline || SyncSettings.enabled;

/// Thrown (wrapped in a [DioException]) for every request the guard stops.
class NetworkDisabledException implements Exception {
  const NetworkDisabledException();

  @override
  String toString() => 'Sync is off -- this build keeps everything on the device '
      'and makes no network request until sync is turned on in Settings.';
}

/// Rejects every request while [networkAllowed] is false, before any byte
/// is sent. Must be the FIRST interceptor on a Dio, so nothing that runs
/// earlier (the debug logger prints request bodies with student names in
/// them) sees a request that was never allowed to exist. Re-checked per
/// request, so turning sync on or off takes effect without a restart.
InterceptorsWrapper networkGuardInterceptor({required bool offline}) => InterceptorsWrapper(
      onRequest: (options, handler) {
        if (networkAllowed(offline: offline)) return handler.next(options);
        handler.reject(DioException(
          requestOptions: options,
          type: DioExceptionType.cancel,
          error: const NetworkDisabledException(),
        ));
      },
    );
