// Real widget-level UI test for a real gap found in front of a real school
// demo: there was no way to add a student to the roster at all before their
// first evaluation. Uses real LocalStore persistence, not mocked state, so
// a regression (e.g. the dialog stops actually saving) fails this test.
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
    env = await RealTestEnv.init('classes_page_test_');
    env.registerGetIt();
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
  });

  testWidgets('a fresh roster shows a real empty state with a working Add student action', (tester) async {
    await tester.pumpWidget(wrapForTest(const ClassesPage()));
    await tester.pumpAndSettle();

    expect(find.text('No students yet'), findsOneWidget);
    expect(find.text('Add student'), findsWidgets, reason: 'both the empty-state action and the FAB');
  });

  testWidgets('adding a student via the dialog actually persists it and it appears in the roster', (tester) async {
    await tester.pumpWidget(wrapForTest(const ClassesPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.widgetWithText(FloatingActionButton, 'Add student'));
    await tester.pumpAndSettle();

    expect(find.text('Add student'), findsWidgets, reason: 'the dialog title, on top of the FAB behind it');
    await tester.enterText(find.widgetWithText(TextFormField, 'Student name *'), 'Rohan Verma');
    await tester.tap(find.widgetWithText(FilledButton, 'Add'));
    await tester.pumpAndSettle();

    // Real persistence check, not just a UI assertion -- the actual roster
    // source every other real screen (Mastery, Scan & Grade) reads from.
    final ids = LocalStore.instance.allNamedStudentIds();
    expect(ids.any((id) => LocalStore.instance.studentName(id) == 'Rohan Verma'), isTrue,
        reason: 'the new student must be real, queryable data, not just a transient dialog result');

    expect(find.text('Rohan Verma'), findsOneWidget, reason: 'must appear in the roster immediately, no reload needed');
    expect(find.text('not yet evaluated'), findsOneWidget,
        reason: 'a freshly-added student with zero evaluations must never show a scary "0% mastery" badge');
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
    addTearDown(() {
      for (final unregister in [
        () => GetIt.I.unregister<Dio>(),
        () => GetIt.I.unregister<AuthApi>(),
        () => GetIt.I.unregister<CurriculumApi>(),
        () => GetIt.I.unregister<ConsentApi>(),
      ]) {
        try {
          unregister();
        } catch (_) {
          // Not registered in this wiring -- which is the point.
        }
      }
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
