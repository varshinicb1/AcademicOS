import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../core/session/current_session.dart';
import '../workspace/ops_api.dart';
import 'device_memory.dart';

/// What a person has done in the product's own guidance -- Guide jobs opened and done, the
/// welcome, the setup wizard -- kept on the server (GET/PUT /me/progress) so a new browser,
/// a new phone or a cleared cache picks up where they were.
///
/// It reads from this device's copy at once and from the server when [load] answers; a
/// write shows at once, goes to the server, and if there is no connection it waits in the
/// queued writes (Ops.send) and is sent when the connection returns. Where the server and
/// the device disagree about a key, the newer write wins.
abstract final class UserProgress {
  /// The current values by key. Listen to this to redraw when progress changes.
  static final ValueNotifier<Map<String, Object?>> items = ValueNotifier(const {});

  // When each key was last written, here or on the server.
  static final Map<String, DateTime> _at = {};
  static String _owner = '';

  static String get _user => Hive.isBoxOpen('academicos_cache') ? CurrentSession.userId : '';
  static String get _cacheKey => 'user_progress:$_user';

  static Object? read(String key) => items.value[key];
  static bool isDone(String key) => items.value[key] == true;

  /// Switch to whoever is signed in now: a different person starts from their own
  /// device copy, never the previous person's.
  static void _adoptUser() {
    final user = _user;
    if (user == _owner) return;
    _owner = user;
    _at.clear();
    items.value = const {};
    if (user.isEmpty) return;
    final raw = DeviceMemory.read(_cacheKey);
    if (raw is! String) return;
    final saved = jsonDecode(raw) as Map<String, dynamic>;
    final values = <String, Object?>{};
    for (final e in saved.entries) {
      final row = e.value as Map<String, dynamic>;
      values[e.key] = row['v'];
      _at[e.key] = DateTime.parse(row['at'] as String);
    }
    items.value = values;
  }

  static void _remember() {
    if (_user.isEmpty) return;
    DeviceMemory.write(_cacheKey, jsonEncode({
      for (final e in items.value.entries)
        e.key: {'v': e.value, 'at': (_at[e.key] ?? DateTime.fromMillisecondsSinceEpoch(0, isUtc: true)).toIso8601String()},
    }));
  }

  /// Read the server's copy and merge it in. Offline, or if the server is down, the
  /// device's copy stands and nothing is shown: progress is a convenience.
  static Future<void> load() async {
    _adoptUser();
    if (_owner.isEmpty) return;
    try {
      final reply = await Ops.map('/me/progress');
      final merged = {...items.value};
      for (final e in (reply['items'] as Map).entries) {
        final row = e.value as Map;
        final at = DateTime.parse(row['updatedAt'] as String).toUtc();
        final have = _at[e.key as String];
        if (have == null || at.isAfter(have)) {
          merged[e.key as String] = row['value'];
          _at[e.key as String] = at;
        }
      }
      items.value = merged;
      _remember();
    } on OpsError {
      // not-a-failure: offline or a server fault; this device's copy of the progress stands
    }
  }

  /// Save one entry. It shows at once; the server write follows, or waits for the connection.
  static Future<void> save(String key, Object? value) async {
    _adoptUser();
    if (_owner.isEmpty) return;
    _at[key] = DateTime.now().toUtc();
    items.value = {...items.value, key: value};
    _remember();
    try {
      await Ops.send('PUT', '/me/progress/$key', body: {'value': value}, label: 'Save your progress');
    } on OpsError {
      // not-a-failure: saved on this device; no connection queues it, and a refusal is ours to fix, not the person's
    }
  }

  /// Forget the in-memory copy (sign-out, tests). The device copy stays for the next sign-in.
  @visibleForTesting
  static void reset() {
    _owner = '';
    _at.clear();
    items.value = const {};
  }
}
