import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Small things this device remembers about how someone uses the app: which
/// menu groups they keep open, and whether they have seen the welcome. Kept
/// in the local store (the same box as the UI language), so they survive a
/// reload and stay on this device.
///
/// Before the local store is open -- a widget test that mounts a page alone
/// -- values live in memory for the run instead, so nothing here needs a
/// try/catch.
abstract final class DeviceMemory {
  static const _boxName = 'academicos_cache';
  static final Map<String, Object> _memory = {};

  static bool get _stored => Hive.isBoxOpen(_boxName);

  static Object? read(String key) => _stored ? Hive.box(_boxName).get(key) : _memory[key];

  static void write(String key, Object value) {
    if (_stored) {
      Hive.box(_boxName).put(key, value);
    } else {
      _memory[key] = value;
    }
  }

  /// Forget what was kept in memory (tests).
  @visibleForTesting
  static void resetMemory() => _memory.clear();
}
