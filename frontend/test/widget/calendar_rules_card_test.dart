// The principal's "Academic Calendar Rules" card must never PUT a rule the
// principal did not choose. The 2026-09-22 review found that a calendar saved
// through the API with a rule the menus don't offer ('first_third', or both
// Saturday and Sunday off) left the dropdowns on 'sunday' / 'none', so an
// untouched "Update Calendar" silently overwrote the saved rule.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/widgets/calendar_rules_card.dart';

CalendarInfo _calendar({List<String> weeklyOffDays = const ['sunday'], String rule = 'none'}) =>
    CalendarInfo.fromJson({
      'id': 'cal_1',
      'academicYearId': 'year_1',
      'weeklyOffDays': weeklyOffDays,
      'alternateSaturdayRule': rule,
    });

class _Submitted {
  List<String>? weeklyOffDays;
  String? rule;
}

Future<_Submitted> _pump(WidgetTester tester, CalendarInfo? saved) async {
  final submitted = _Submitted();
  await tester.pumpWidget(MaterialApp(
    home: Scaffold(
      body: SingleChildScrollView(
        child: CalendarRulesCard(
          saved: saved,
          busy: false,
          onSubmit: (days, rule) {
            submitted.weeklyOffDays = days;
            submitted.rule = rule;
          },
        ),
      ),
    ),
  ));
  return submitted;
}

void main() {
  testWidgets("an untouched Update keeps a saved 'first_third' rule", (tester) async {
    final submitted = await _pump(tester, _calendar(rule: 'first_third'));

    expect(find.text('Saved: first_third'), findsOneWidget);
    expect(find.textContaining('standard menus do not offer'), findsOneWidget);

    await tester.tap(find.text('Update Calendar'));
    expect(submitted.weeklyOffDays, ['sunday']);
    expect(submitted.rule, 'first_third');
  });

  testWidgets('an untouched Update keeps two saved weekly off days', (tester) async {
    final submitted = await _pump(tester, _calendar(weeklyOffDays: ['saturday', 'sunday']));

    expect(find.text('Saved: Saturday & Sunday'), findsOneWidget);

    await tester.tap(find.text('Update Calendar'));
    expect(submitted.weeklyOffDays, ['saturday', 'sunday']);
    expect(submitted.rule, 'none');
  });

  testWidgets('the principal can still switch away from the saved rule', (tester) async {
    final submitted = await _pump(tester, _calendar(rule: 'first_third'));

    await tester.tap(find.text('Saved: first_third'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('All Saturdays Off').last);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Update Calendar'));
    expect(submitted.rule, 'all');
  });

  testWidgets("'2nd,4th' is the menu's 2nd & 4th entry, with no extra item", (tester) async {
    final submitted = await _pump(tester, _calendar(weeklyOffDays: ['friday'], rule: '2nd,4th'));

    expect(find.text('2nd & 4th Saturdays Off'), findsOneWidget);
    expect(find.textContaining('Saved: 2nd'), findsNothing);
    expect(find.textContaining('standard menus do not offer'), findsNothing);

    await tester.tap(find.text('Update Calendar'));
    expect(submitted.weeklyOffDays, ['friday']);
    expect(submitted.rule, 'second_fourth');
  });

  testWidgets('with no saved calendar it initializes with the defaults', (tester) async {
    final submitted = await _pump(tester, null);

    await tester.tap(find.text('Initialize Calendar'));
    expect(submitted.weeklyOffDays, ['sunday']);
    expect(submitted.rule, 'none');
  });
}
