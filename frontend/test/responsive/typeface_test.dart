// The guard on [useAppFonts]: that the responsive suite really does lay text
// out in Inter, and that the app really does name it.
//
// Every width assertion in this directory is only worth what the font behind
// it is worth. flutter_test's fallback is a fixed-width box glyph -- "iiii"
// and "WWWW" measure the same -- so a suite running on it can pass a 375 px
// phone flow that overflows in the shipped app, and fail one that does not.
// The two are indistinguishable from the test output, which is how the
// typeface being absent survived a whole task before (review of 2026-09-23).
//
// These fail if the fonts stop being bundled, stop being loaded, or the theme
// stops asking for them.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/constants/app_constants.dart';
import 'package:academicos/core/theme/app_theme.dart';

import 'responsive_harness.dart';

double _widthOf(String text, TextStyle style) {
  final painter = TextPainter(
    text: TextSpan(text: text, style: style),
    textDirection: TextDirection.ltr,
  )..layout();
  return painter.width;
}

void main() {
  useAppFonts();

  test('the shipped theme names Inter on its body text', () {
    expect(AppConstants.fontFamily, 'Inter');
    expect(AppTheme.lightTheme.textTheme.bodyMedium?.fontFamily, 'Inter');
    expect(AppTheme.darkTheme.textTheme.titleLarge?.fontFamily, 'Inter');
  });

  testWidgets('the face the suite measures in is proportional, not the fallback box', (tester) async {
    final style = AppTheme.lightTheme.textTheme.bodyMedium!;

    // Inter is proportional: four `i`s are far narrower than four `W`s. In
    // flutter_test's fallback the two are exactly equal, so this is the one
    // assertion that can tell a loaded font from no font at all.
    expect(_widthOf('WWWW', style), greaterThan(_widthOf('iiii', style) * 2),
        reason: 'text is being laid out in flutter_test\'s fixed-width fallback, not Inter -- '
            'every width assertion in this suite is measuring the wrong glyph');
  });

  testWidgets('each declared weight is its own face, not a synthesised one', (tester) async {
    final regular = AppTheme.font(fontSize: 14, fontWeight: FontWeight.w400);
    final semiBold = AppTheme.font(fontSize: 14, fontWeight: FontWeight.w600);
    final bold = AppTheme.font(fontSize: 14, fontWeight: FontWeight.w700);

    // Inter's weights differ in advance width, so a real face swap moves the
    // measurement. A family carrying one face would return the same number for
    // all three and lean on a synthesised emboldening instead -- which is what
    // google_fonts' per-weight families did to every `copyWith(fontWeight:)`
    // in lib/.
    final widths = <double>{
      _widthOf('Create account', regular),
      _widthOf('Create account', semiBold),
      _widthOf('Create account', bold),
    };
    expect(widths.length, 3,
        reason: 'w400/w600/w700 all measured the same, so at most one Inter face is registered');
  });
}
