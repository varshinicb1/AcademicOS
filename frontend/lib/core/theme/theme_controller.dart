import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../local_engine/local_store.dart';

/// Real app-wide theme control, backed by LocalStore so it survives a
/// restart. Was a UI gap before this: Settings' Theme toggle updated only
/// its own widget's local state and MaterialApp.router's themeMode was
/// hardcoded to ThemeMode.system regardless -- switching the toggle to
/// Dark visibly changed nothing.
///
/// Before the local store is open (a widget test that mounts a page alone)
/// the mode starts dark, as the widget tests were written, and a change is not
/// stored. A signed-in person's default is light (LocalStore.themeModeName).
class ThemeController {
  ThemeController._();

  static final ValueNotifier<ThemeMode> mode = ValueNotifier(_load());

  static bool get _stored => Hive.isBoxOpen('academicos_cache');

  static ThemeMode _load() => !_stored
      ? ThemeMode.dark
      : switch (LocalStore.instance.themeModeName) {
          'dark' => ThemeMode.dark,
          'system' => ThemeMode.system,
          _ => ThemeMode.light,
        };

  static void set(ThemeMode m) {
    mode.value = m;
    if (!_stored) return;
    LocalStore.instance.themeModeName = switch (m) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
    };
  }
}
