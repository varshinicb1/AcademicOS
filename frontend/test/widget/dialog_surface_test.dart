// QA P-34 (2026-10-01): dialogs and the bank picker were translucent glass,
// so the paper behind them read through their fields. Every surface a
// dialog, a bottom sheet or a menu draws on is opaque, in both themes.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/theme/app_theme.dart';

void main() {
  for (final (name, theme) in [('light', AppTheme.lightTheme), ('dark', AppTheme.darkTheme)]) {
    test('dialogs, sheets and menus are opaque in the $name theme', () {
      expect(theme.dialogTheme.backgroundColor?.a, 1.0, reason: 'dialog');
      expect(theme.bottomSheetTheme.backgroundColor?.a, 1.0, reason: 'bottom sheet (the bank picker)');
      expect(theme.popupMenuTheme.color?.a, 1.0, reason: 'popup menu');
    });
  }
}
