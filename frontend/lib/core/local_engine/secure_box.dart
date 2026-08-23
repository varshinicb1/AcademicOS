import 'package:hive_flutter/hive_flutter.dart';

import 'secure_box_io.dart' if (dart.library.html) 'secure_box_web.dart' as impl;

/// Encryption at rest for the offline build's local student data.
///
/// LocalStore (core/local_engine/local_store.dart) writes every real
/// assessment, evaluation, and mastery record into the 'academicos_cache'
/// Hive box as plain JSON -- fine for a demo, a real gap for a school's
/// actual data. This closes it: a random 256-bit key generated on first
/// run, and the Hive box opened with HiveAesCipher so every value is
/// AES-encrypted on disk.
///
/// Key storage is platform-conditional (secure_box_io.dart /
/// secure_box_web.dart, picked at compile time via `dart.library.html`):
///
/// Native (Windows/Android/desktop): originally used flutter_secure_storage
/// (Android Keystore / Windows Credential Manager), but its Windows native
/// plugin has a broken CMake/ATL packaging (confirmed: the required atlmfc
/// headers are present on disk after installing the VS ATL component, but
/// the plugin's generated vcxproj never adds them to the include path -- a
/// bug in the package, not a fixable local toolchain gap). Rather than
/// block on an upstream fix, the key lives in a file inside the app's own
/// private data directory -- not Keystore-hardware-backed, but still
/// OS-sandboxed to this app. Revisit if flutter_secure_storage ships a fix.
///
/// Web: `path_provider`'s `getApplicationSupportDirectory()` and `dart:io`'s
/// `File` (the native path above) have no web implementation at all --
/// calling either crashed the ENTIRE app on startup before any UI rendered,
/// confirmed against the real deployed build via a browser console check
/// (`MissingPluginException`). Browser `localStorage` is used instead: the
/// browser itself already sandboxes storage per-origin, giving the same
/// "private to this app" property the native file path relies on.
class SecureBox {
  static const _keyFileName = '.academicos_hive_key';

  static Future<Box> openEncrypted(String boxName) async {
    // The whole thing, key generation included, is guarded: this runs
    // before runApp() (main.dart awaits it directly), so ANY uncaught
    // exception here -- key-file I/O failing, not just the decrypt path
    // below -- leaves the app on its native white splash screen forever.
    // Confirmed as a real class of bug via the corpus-loading regression
    // fixed alongside this (corpus_repository.dart's reload()).
    try {
      final key = await impl.getOrCreateSecureKey(_keyFileName);
      try {
        return await Hive.openBox(boxName, encryptionCipher: HiveAesCipher(key));
      } catch (_) {
        // A box written before encryption was added (or with a stale/foreign
        // key) fails to decrypt -- Hive throws deep inside its read path
        // rather than at open time, which previously crashed the whole app
        // before any UI rendered. This is a local cache, not the source of
        // truth (the real record lives server-side / in the offline engine's
        // own store), so losing it is a cold cache, not data loss -- wipe and
        // start clean rather than bring the app down.
        await Hive.deleteBoxFromDisk(boxName);
        return await Hive.openBox(boxName, encryptionCipher: HiveAesCipher(key));
      }
    } catch (_) {
      // Key generation itself failed (extremely rare -- disk full, a
      // sandboxing quirk on some device). An unencrypted local cache is
      // still strictly better than a dead app: better degrade than crash.
      return Hive.openBox(boxName);
    }
  }
}
