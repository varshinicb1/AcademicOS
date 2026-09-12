// Real widget-level UI test for a real gap found in front of a real school
// demo: there was no way to add a student to the roster at all before their
// first evaluation. Uses real LocalStore persistence, not mocked state, so
// a regression (e.g. the dialog stops actually saving) fails this test.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/settings/pages/classes_page.dart';

import '../support/real_di.dart';

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
}
