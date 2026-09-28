// Settings shows no network UI the build cannot honestly back.
//
// The offline build's Settings used to show "Server & Sync" -- a Manual
// Sync that pushed and pulled assessments over Dio, and a Server URL field
// nothing ever read (SyncService takes its base from the ACADEMICOS_API
// dart-define). It also offered "Download Data" and a Sarvam API key, both
// of which need INTERNET, which the release manifest does not declare.
//
// The page reads the compile-time ACADEMICOS_OFFLINE flag, so this file
// asserts whichever build it was compiled as. Run it both ways:
//   flutter test test/widget/settings_page_network_test.dart
//   flutter test --dart-define=ACADEMICOS_OFFLINE=true test/widget/settings_page_network_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'package:academicos/core/sync/network_policy.dart';
import 'package:academicos/presentation/settings/pages/settings_page.dart';

import '../support/real_di.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('settings_page_network_test_');
    PackageInfo.setMockInitialValues(
      appName: 'AcademicOS',
      packageName: 'com.vidyuthlabs.academicos',
      version: '1.0.0',
      buildNumber: '1',
      buildSignature: '',
    );
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
  });

  Future<void> pumpSettings(WidgetTester tester) async {
    // Tall enough that the ListView builds every section, not just the
    // first screenful.
    tester.view.physicalSize = const Size(1080, 12000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(wrapForTest(const SettingsPage()));
    await tester.pumpAndSettle();
  }

  testWidgets('the Server URL field is gone from every build -- nothing ever read it', (tester) async {
    await pumpSettings(tester);
    expect(find.text('Server URL'), findsNothing);
  });

  testWidgets(
      kOfflineBuild
          ? 'offline build: no Server & Sync section, no Manual Sync'
          : 'web build: Server & Sync still offers Manual Sync',
      (tester) async {
    await pumpSettings(tester);
    const expected = kOfflineBuild ? findsNothing : findsOneWidget;
    expect(find.text('Server & Sync'), expected);
    expect(find.text('Manual Sync'), expected);
    expect(find.text('Sync History'), expected);
  });

  testWidgets('Backup & Restore is local and stays in every build', (tester) async {
    await pumpSettings(tester);
    expect(find.text('Backup & Restore'), findsOneWidget);
  });

  testWidgets('network-only features are hidden, not left broken, in the offline build', (tester) async {
    await pumpSettings(tester);
    // Both need INTERNET, which the release manifest does not declare.
    // Neither was ever offered by the web build.
    expect(find.text('Download Data'), kOfflineBuild && kOfflineBuildHasInternet ? findsOneWidget : findsNothing);
    expect(find.text('Sarvam API Key (optional)'),
        kOfflineBuild && kOfflineBuildHasInternet ? findsOneWidget : findsNothing);
  });
}
