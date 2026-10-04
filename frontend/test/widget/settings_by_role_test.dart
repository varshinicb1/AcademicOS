// Settings offers a student or a parent only what they can use (audit 2026-10-04): the paper template,
// the class list and the assessment sync open pages the server refuses them, and Rate App, Notifications
// and Auto Sync did nothing.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/sync/network_policy.dart';
import 'package:academicos/presentation/settings/pages/settings_page.dart';

import '../support/real_di.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('settings_by_role_test_');
    PackageInfo.setMockInitialValues(
        appName: 'AcademicOS', packageName: 'x', version: '1.0.0', buildNumber: '1', buildSignature: '');
  });
  tearDownAll(() async => env.dispose());

  Future<void> pump(WidgetTester tester, String role) async {
    LocalStore.instance.authUser = {'id': 'u1', 'schoolId': 's1', 'role': role, 'name': 'Test'};
    addTearDown(() => LocalStore.instance.authUser = null);
    tester.view.physicalSize = const Size(1080, 12000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(wrapForTest(const SettingsPage()));
    await tester.pumpAndSettle();
  }

  for (final role in ['student', 'parent']) {
    testWidgets('a $role is not offered staff tiles', (tester) async {
      await pump(tester, role);
      expect(find.text('School branding'), findsNothing);
      expect(find.text('Classes'), findsNothing);
      expect(find.text('Manual Sync'), findsNothing);
      expect(find.text('Profile'), findsOneWidget);
      expect(find.text('Theme'), findsOneWidget);
    });
  }

  testWidgets('a teacher keeps them', (tester) async {
    await pump(tester, 'teacher');
    expect(find.text('School branding'), findsOneWidget);
    expect(find.text('Classes'), findsOneWidget);
    if (!kOfflineBuild) expect(find.text('Manual Sync'), findsOneWidget);
  });

  testWidgets('no one is offered the toggles and tiles that did nothing', (tester) async {
    await pump(tester, 'principal');
    expect(find.text('Rate App'), findsNothing);
    expect(find.text('Auto Sync'), findsNothing);
    expect(find.text('Notifications'), findsNothing);
  });
}
