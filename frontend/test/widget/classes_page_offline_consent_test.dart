// The offline build's consent promise, in a file of its own: recording
// parental consent writes to the device and makes no HTTP call.
//
// Its own file because it shares hive's single 'academicos_cache' box:
// after classes_page_test.dart's earlier widget tests, a write they left
// queued holds hive's lock-queue turn, and this test's first write waited
// forever (a 10-minute timeout on every run; alone it passes in a second).
// test/support/real_di.dart describes the same lock-queue flake at close().
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/di/service_locator.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/consent_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/settings/pages/classes_page.dart';

import '../support/real_di.dart';
import '../support/recording_http_adapter.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('classes_page_offline_consent_test_');
    env.registerGetIt();
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
  });

  // DPDP Act 2023: a consent record names a student and their guardian -- a
  // minor's personal data. Until 2026-09-22 recording one here also fired
  // POST /consent at the backend from the offline build, guarded only by
  // isRegistered<ConsentApi>(), which was always true. Wired exactly as the
  // offline build wires DI (registerNetworkClients, offline: true), with a
  // transport that counts every request that gets out.
  testWidgets('offline build: recording consent writes to the device and makes no HTTP call', (tester) async {
    final transport = RecordingHttpAdapter();
    registerNetworkClients(GetIt.I, offline: true, httpClientAdapter: transport);
    addTearDown(() async {
      // The offline wiring registers the Dio and none of the server APIs --
      // which is the point -- so unregister only what is there. (A bare
      // unregister of an absent type fails asynchronously in this get_it,
      // past any synchronous try/catch.)
      if (GetIt.I.isRegistered<Dio>()) await GetIt.I.unregister<Dio>();
      if (GetIt.I.isRegistered<AuthApi>()) await GetIt.I.unregister<AuthApi>();
      if (GetIt.I.isRegistered<CurriculumApi>()) await GetIt.I.unregister<CurriculumApi>();
      if (GetIt.I.isRegistered<ConsentApi>()) await GetIt.I.unregister<ConsentApi>();
    });

    await tester.pumpWidget(wrapForTest(const ClassesPage()));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FloatingActionButton, 'Add student'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextFormField, 'Student name *'), 'Meera Iyer');
    await tester.tap(find.widgetWithText(FilledButton, 'Add'));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Parental consent required — tap to record'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextFormField, 'Parent/guardian name *'), 'Lakshmi Iyer');
    await tester.enterText(find.widgetWithText(TextFormField, 'How consent was obtained *'),
        'Signed admission form, clause 4');
    await tester.tap(find.widgetWithText(FilledButton, 'Record consent'));
    await tester.pumpAndSettle();
    // Let any fire-and-forget request the page started actually run.
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();

    final id = LocalStore.instance
        .allNamedStudentIds()
        .firstWhere((i) => LocalStore.instance.studentName(i) == 'Meera Iyer');
    final consent = LocalStore.instance.getConsent(id);
    expect(consent, isNotNull, reason: 'the record must live in the on-device store');
    expect(consent!['guardianName'], 'Lakshmi Iyer');
    expect(consent['method'], 'Signed admission form, clause 4');
    expect(find.byTooltip('Parental consent on file'), findsOneWidget);
    expect(transport.requests, isEmpty,
        reason: 'no request may leave the device: got ${transport.requests.map((r) => '${r.method} ${r.path}').toList()}');
  });
}
