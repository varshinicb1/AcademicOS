import 'package:flutter/material.dart';

import '../local_engine/local_store.dart';

/// Real app-wide theme control, backed by LocalStore so it survives a
/// restart. Was a UI gap before this: Settings' Theme toggle updated only
/// its own widget's local state and MaterialApp.router's themeMode was
/// hardcoded to ThemeMode.system regardless -- switching the toggle to
/// Dark visibly changed nothing.
class ThemeController {
  ThemeController._();

  static final ValueNotifier<ThemeMode> mode = ValueNotifier(_load());

  static ThemeMode _load() => switch (LocalStore.instance.themeModeName) {
        'light' => ThemeMode.light,
        'dark' => ThemeMode.dark,
        _ => ThemeMode.system,
      };

  static void set(ThemeMode m) {
    mode.value = m;
    LocalStore.instance.themeModeName = switch (m) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
    };
  }
}
