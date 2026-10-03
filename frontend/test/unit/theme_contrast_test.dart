// WCAG AA (4.5:1) on the pairs a person has to read, in both themes, measured on the
// real theme and brand constants. The primary button's ember gradient had stops that put
// its white label at 2.1:1 and 4.4:1; that is what this holds.
import 'dart:math' as math;

import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/core/theme/emergera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

double _luminance(Color c) {
  double channel(double v) => v <= 0.03928 ? v / 12.92 : math.pow((v + 0.055) / 1.055, 2.4).toDouble();
  return 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
}

double contrast(Color a, Color b) {
  final la = _luminance(a), lb = _luminance(b);
  final hi = math.max(la, lb), lo = math.min(la, lb);
  return (hi + 0.05) / (lo + 0.05);
}

void main() {
  test('white on every stop of the primary button fill is at least 4.5:1', () {
    for (final stop in Em.primaryFill.colors) {
      expect(contrast(Colors.white, stop), greaterThanOrEqualTo(4.5), reason: '$stop');
    }
  });

  for (final (name, theme) in [('light', AppTheme.lightTheme), ('dark', AppTheme.darkTheme)]) {
    test('$name: body text, secondary text and errors are readable on their surfaces', () {
      final c = theme.colorScheme;
      expect(contrast(c.onSurface, c.surface), greaterThanOrEqualTo(7), reason: 'body text');
      expect(contrast(c.onSurfaceVariant, c.surface), greaterThanOrEqualTo(4.5), reason: 'secondary text');
      expect(contrast(c.error, c.surface), greaterThanOrEqualTo(4.5), reason: 'error text');
    });
  }

  test('light: the accent is readable as text and carries a white label', () {
    final c = AppTheme.lightTheme.colorScheme;
    expect(contrast(c.primary, c.surface), greaterThanOrEqualTo(4.5));
    expect(contrast(c.onPrimary, c.primary), greaterThanOrEqualTo(4.5));
  });
}
