// Real on-device teacher-flow walkthrough, driven by integration_test
// (the standard Flutter on-device testing tool) rather than blind adb
// pixel-coordinate taps -- widget-aware finders (find.text/find.byIcon)
// don't drift when layout shifts, and any uncaught exception during a
// pump fails the test with a real stack trace instead of silently landing
// on a dead-end screen. Run against the exact same build flags as the
// shipped APK:
//   flutter test integration_test/teacher_flow_test.dart -d <deviceId>
//     --dart-define=ACADEMICOS_OFFLINE=true --dart-define=ACADEMICOS_SEED_DEMO=true
//
// Everything lives in ONE testWidgets(): app.main() re-registers GetIt
// singletons on every call (confirmed real: a second call threw "Type
// AppDatabase is already registered inside GetIt"), so it can only run
// once per test process -- this drives the whole walkthrough in one pass
// instead of restarting the app per assertion.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:academicos/main.dart' as app;
import 'package:academicos/core/local_engine/local_store.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('full teacher walkthrough: launch, every drawer destination, assessment data',
      (tester) async {
    final findings = <String>[];

    Future<void> settle(WidgetTester tester) =>
        tester.pumpAndSettle(const Duration(milliseconds: 300));

    Future<void> openDrawer(WidgetTester tester) async {
      final menu = find.byIcon(Icons.menu);
      if (menu.evaluate().isEmpty) {
        findings.add('BUG: hamburger menu icon not found on current screen');
        return;
      }
      await tester.tap(menu.first);
      await settle(tester);
    }

    Future<void> navigateTo(WidgetTester tester, String label) async {
      await openDrawer(tester);
      final item = find.widgetWithText(ListTile, label);
      if (item.evaluate().isEmpty) {
        findings.add('BUG: drawer has no "$label" destination (or drawer failed to open)');
        return;
      }
      await tester.tap(item.first);
      await settle(tester);
    }

    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 10));

    // ---- 1. App launches, demo data is real ----
    expect(find.text('Today'), findsOneWidget, reason: 'home page must load without crashing');
    final assessments = LocalStore.instance.allAssessments();
    expect(assessments.length, 5, reason: 'demo seeder must have populated 5 real assessments');

    // ---- 2. Every drawer destination opens without a crash ----
    const destinations = [
      'Today', 'Syllabus', 'Assessments', 'Planner', 'Questions',
      'Evaluate', 'Mastery', 'Teacher', 'Principal',
    ];
    for (final label in destinations) {
      await navigateTo(tester, label);
      final exception = tester.takeException();
      if (exception != null) {
        findings.add('CRASH on "$label": $exception');
      }
      if (find.byType(Scaffold).evaluate().isEmpty) {
        findings.add('BUG: "$label" rendered no Scaffold at all (blank screen)');
      }
    }

    // ---- 3. Assessments list: known real bug (hardcoded wrong teacherId) ----
    await navigateTo(tester, 'Assessments');
    await settle(tester);
    if (find.text('No assessments yet.').evaluate().isNotEmpty) {
      findings.add(
          'BUG: Assessments list shows empty state despite 5 real seeded assessments -- '
          'assessment_list_page.dart hardcodes _teacherId=\'teacher_1\', matching none of '
          'the demo seeder\'s real teacher IDs (demo_teacher_1..5)');
    }

    // ---- 4. Settings page loads ----
    await navigateTo(tester, 'Today');
    await openDrawer(tester);
    final settingsTile = find.widgetWithText(ListTile, 'Settings');
    if (settingsTile.evaluate().isEmpty) {
      findings.add('BUG: drawer has no Settings entry (or drawer failed to open)');
    } else {
      await tester.tap(settingsTile.first);
      await settle(tester);
      final exception = tester.takeException();
      if (exception != null) findings.add('CRASH on Settings: $exception');
      if (find.text('Settings').evaluate().isEmpty) {
        findings.add('BUG: Settings page did not render its title');
      }
    }

    // Print every finding as one block so a single test run reports
    // everything real that's broken, not just the first failure.
    // ignore: avoid_print
    print('\n===== STRESS TEST FINDINGS (${findings.length}) =====');
    for (final f in findings) {
      // ignore: avoid_print
      print('- $f');
    }
    // ignore: avoid_print
    print('===== END FINDINGS =====\n');

    expect(findings, isEmpty, reason: findings.join('\n'));
  });
}
