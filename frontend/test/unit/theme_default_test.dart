// A person who has never chosen a theme gets the calm light one. The product is
// designed white (design/tokens.json) and the brand's dark theme is a choice in
// Settings: 44a8b3a made it the default and left a comment saying light, so a
// school's first screen was the ember-on-ink theme with its glow and aurora.
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/theme_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('theme_default_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
      tmp.deleteSync(recursive: true);
    } catch (_) {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  test('nothing chosen yet means light', () {
    expect(LocalStore.instance.themeModeName, 'light');
    expect(ThemeController.mode.value, ThemeMode.light);
  });

  test('a person who chose dark keeps dark', () {
    ThemeController.set(ThemeMode.dark);
    expect(LocalStore.instance.themeModeName, 'dark');
    ThemeController.set(ThemeMode.light);
    expect(LocalStore.instance.themeModeName, 'light');
  });
}
