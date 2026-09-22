// Task 801: a custom paper in the guided builder (/assessment/build) at
// phone, tablet and laptop widths -- class and subject, a template, the
// chapters, Generate, then search the bank and pick a question for one slot.
// Every step must fit and keep its primary action on screen.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'builder_driver.dart';
import 'responsive_harness.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useInMemoryHive();

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('class -> template -> chapters -> generate -> search the bank -> pick fits at $name',
        (tester) async {
      final (api, _) = await pumpBuilder(tester, size);
      await toChaptersStep(tester, size);
      await generate(tester, size);

      // Pick question 27 from the bank: the picker is a sheet over the paper.
      final card = find.byKey(const ValueKey('question-27'));
      await tester.scrollUntilVisible(card, 300, scrollable: find.byType(Scrollable).first);
      final pick = find.descendant(of: card, matching: find.text('Pick'));
      Scrollable.ensureVisible(pick.evaluate().first, alignment: 0.5);
      await tester.pumpAndSettle();
      expectActionReady(tester, find.ancestor(of: pick, matching: find.byWidgetPredicate((w) => w is ButtonStyleButton)),
          size, label: 'Pick on question 27');
      await tester.tap(pick);
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' in the bank picker');

      final searchField = find.widgetWithText(TextField, 'Search the question text');
      expectActionReady(tester, searchField, size, label: 'the bank search field');
      await tester.enterText(searchField, 'force');
      await tester.tap(find.byTooltip('Search'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' after searching the bank');

      final first = fixtureJsonList('search_10_science_3m').first['stem'] as String;
      final tile = find.ancestor(of: find.text(first).first, matching: find.byType(ListTile));
      expectActionReady(tester, tile.first, size, label: 'the first bank result');
      await tester.tap(find.text(first).first);
      await tester.pumpAndSettle();

      expectNoOverflow(tester, where: ' after picking');
      expect(api.requests.where((r) => r.method == 'POST' && r.path.endsWith('/questions/27')).single.status, 200);
      expectActionReady(tester, builderPrimary(), size, label: 'Done: download');
    });
  }
}
