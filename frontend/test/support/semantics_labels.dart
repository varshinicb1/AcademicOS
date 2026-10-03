// What a screen reader is told about the text fields on screen: the label of
// each field's semantics node. The web build turns that label into the
// input's aria-label, which the QA pass of 2026-10-01 found empty on the
// marks grid and the review comment (P-28).
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

/// The label of every text field built, in tree order. Call with semantics
/// enabled (`tester.ensureSemantics()`).
List<String> textFieldLabels(WidgetTester tester) => [
      for (final e in find.byType(EditableText).evaluate())
        tester.getSemantics(find.byElementPredicate((x) => x == e)).label,
    ];
