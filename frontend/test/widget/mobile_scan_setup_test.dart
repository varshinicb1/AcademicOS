// Real widget-level UI test for a real gap found in front of a real school
// demo: Scan & Grade's student field was bare free text with nothing
// pre-filled -- a live demo showed an empty form with no student to pick,
// even though the real 10-student demo roster existed the whole time.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/mobile_scan/pages/mobile_scan_page.dart';

import '../support/real_di.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('mobile_scan_setup_test_');
    env.registerGetIt();
    // Safe here (unlike inside a testWidgets body) -- setUpAll runs outside
    // flutter_test's per-test fake-async zone, so this real, heavy I/O
    // (full corpus load + 5 real generated papers + ~50 real evaluations)
    // can actually complete. See scan_history_page_test.dart for the case
    // where this needed tester.runAsync() instead.
    await DemoSeeder.seedIfEmpty();
  });

  tearDownAll(() async {
    await env.dispose();
  });

  testWidgets(
    'the setup screen pre-fills a real student from the real roster, not an empty free-text field',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const MobileScanPage()));
      await tester.pumpAndSettle();

      final roster = LocalStore.instance.allNamedStudentIds()..sort();
      expect(roster, isNotEmpty, reason: 'demo seeding must have produced a real, named roster');
      final firstName = LocalStore.instance.studentName(roster.first);

      expect(find.text(firstName), findsWidgets,
          reason: 'a real roster student must be pre-selected, not an empty text field');
      expect(find.widgetWithText(TextField, 'Student name'), findsNothing,
          reason: 'the free-text entry must be hidden by default when a real roster exists');

      // The real assessment picker must also default to a real assessment
      // (already existed before this fix, but must not have regressed).
      expect(find.textContaining('Class X'), findsWidgets,
          reason: 'a real demo-seeded assessment must be pre-selected');
    },
  );

  testWidgets('choosing "Add new student" reveals the free-text fields for a genuinely new student', (tester) async {
    await tester.pumpWidget(wrapForTest(const MobileScanPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    // The dropdown menu opens scrolled to keep the *currently selected*
    // student visible near the button -- with a real ~10-student demo
    // roster, that scrolls "+ Add new student" (the last item) out of the
    // menu's own hit-testable viewport even though it already exists in the
    // tree. ensureVisible() scrolls the menu's internal Scrollable so the
    // tap actually lands on it, rather than on the menu's backdrop.
    await tester.ensureVisible(find.text('+ Add new student').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('+ Add new student').last);
    await tester.pumpAndSettle();

    expect(find.widgetWithText(TextField, 'Student name'), findsOneWidget,
        reason: 'must still be possible to scan a brand-new student not yet on the roster');
  });
}
