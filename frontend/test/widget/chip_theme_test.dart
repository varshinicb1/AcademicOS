// A selected chip's label stays readable in both themes (QA S-10, 2026-10-01).
//
// The theme filled a selected chip with --em-chip-on (fog in the dark theme,
// graphite in the light one) and left its label the page's text colour (fog
// in the dark theme, graphite in the light one): white on white, or graphite
// on graphite. The bell's weekday chips, a homework's sections and its
// chapters showed only a tick, so nobody could tell what was chosen.
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/core/theme/emergera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

double _contrast(Color a, Color b) {
  final la = a.computeLuminance(), lb = b.computeLuminance();
  final hi = la > lb ? la : lb, lo = la > lb ? lb : la;
  return (hi + 0.05) / (lo + 0.05);
}

void main() {
  for (final (name, theme, brightness) in [
    ('dark', AppTheme.darkTheme, Brightness.dark),
    ('light', AppTheme.lightTheme, Brightness.light),
  ]) {
    testWidgets('$name theme: a selected chip\'s label contrasts with its fill, an unselected one with the page',
        (tester) async {
      await tester.pumpWidget(MaterialApp(
        theme: theme,
        home: Scaffold(
          body: Wrap(children: [
            FilterChip(label: const Text('Mon'), selected: true, onSelected: (_) {}),
            FilterChip(label: const Text('Tue'), selected: false, onSelected: (_) {}),
            ChoiceChip(label: const Text('10-A'), selected: true, onSelected: (_) {}),
          ]),
        ),
      ));
      final surfaces = EmSurfaces.of(brightness);
      Color labelColour(String text) => tester.renderObject<RenderParagraph>(find.text(text)).text.style!.color!;
      for (final selected in ['Mon', '10-A']) {
        expect(_contrast(labelColour(selected), surfaces.chipOnBg), greaterThanOrEqualTo(4.5), reason: selected);
      }
      expect(labelColour('Tue'), theme.colorScheme.onSurface);
    });
  }
}
