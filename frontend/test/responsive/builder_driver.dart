// Drives the guided paper builder (/assessment/build, Task 902) for the
// Task 801 responsive tests, against the real backend's captured answers
// (../paper_builder/fixture_api.dart says how they were captured). The
// builder's own flow test pins what each step does at 375 px; these reuse
// its fixtures to check the same steps fit a tablet and a laptop too.
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';

import '../paper_builder/fixture_api.dart';
import 'responsive_harness.dart';

export '../paper_builder/fixture_api.dart';

class SavedPdfs {
  final List<(String, List<int>)> files = [];
  Future<void> call(Uint8List bytes, String name) async => files.add((name, bytes));
}

/// The builder keeps the teacher's last choices in the app's Hive box; an
/// in-memory box completes its writes inside a widget test's fake clock (a
/// file-backed one never does -- see paper_builder_flow_test.dart).
void useInMemoryHive() {
  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('responsive_builder_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });
  tearDownAll(() async => Hive.close());
  setUp(() => LocalStore.instance.box.clear());
}

Future<(FixtureAdapter, SavedPdfs)> pumpBuilder(WidgetTester tester, Size size, {bool quick = false}) async {
  useScreen(tester, size);
  final adapter = FixtureAdapter();
  final saved = SavedPdfs();
  await tester.pumpWidget(appForTest(PaperBuilderPage(
    quick: quick,
    api: fixtureApi(adapter),
    savePdf: saved.call,
    schoolId: 'school_1',
    userId: fixtureTeacherId,
  )));
  await tester.pumpAndSettle();
  return (adapter, saved);
}

/// The builder's one "move the paper forward" button, pinned to the bottom.
Finder builderPrimary() => find.byKey(const ValueKey('builder-primary'));

String builderPrimaryLabel(WidgetTester tester) =>
    tester.widget<Text>(find.descendant(of: builderPrimary(), matching: find.byType(Text))).data!;

/// Scrolls [f] to the middle of the screen, clear of the pinned bottom bar,
/// and taps it.
Future<void> tapVisible(WidgetTester tester, Finder f) async {
  await tester.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
  Scrollable.ensureVisible(f.evaluate().first, alignment: 0.5);
  await tester.pumpAndSettle();
  await tester.tap(f);
  await tester.pumpAndSettle();
}

Finder cardButton(String cardText, String button) => find.descendant(
      of: find.ancestor(of: find.text(cardText), matching: find.byType(Card)),
      matching: find.text(button),
    );

/// Class 10 Science, the half-yearly CBSE preset, the whole syllabus:
/// leaves the builder on the chapters step with Generate ready.
Future<void> toChaptersStep(WidgetTester tester, Size size) async {
  expectNoOverflow(tester, where: ' on class & subject');
  expectActionReady(tester, find.ancestor(of: find.text('Class 10'), matching: find.byType(ChoiceChip)), size,
      label: 'the Class 10 choice');
  await tester.tap(find.text('Class 10'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Science'));
  await tester.pumpAndSettle();
  expectActionReady(tester, builderPrimary(), size, label: 'Next: choose a template');
  await tester.tap(builderPrimary());
  await tester.pumpAndSettle();

  expectNoOverflow(tester, where: ' on templates');
  expectActionReady(tester, builderPrimary(), size, label: 'the template step primary');
  final halfYearly = (fixtureJson('templates_10_science')['presets'] as List)
      .firstWhere((p) => p['examType'] == 'half_yearly') as Map;
  final use = cardButton(halfYearly['name'] as String, 'Use');
  await tester.scrollUntilVisible(use, 200, scrollable: find.byType(Scrollable).first);
  Scrollable.ensureVisible(use.evaluate().first, alignment: 0.5);
  await tester.pumpAndSettle();
  expectActionReady(tester, find.ancestor(of: use, matching: find.byWidgetPredicate((w) => w is ButtonStyleButton)),
      size, label: 'Use on the half-yearly pattern');
  await tester.tap(use);
  await tester.pumpAndSettle();

  expectNoOverflow(tester, where: ' on chapters');
  expect(find.text('Ready: every section can be filled from the whole syllabus.'), findsOneWidget);
  expect(builderPrimaryLabel(tester), 'Generate paper');
  expectActionReady(tester, builderPrimary(), size, label: 'Generate paper');
}

/// From the chapters step: Generate, and land on the paper.
Future<void> generate(WidgetTester tester, Size size) async {
  await tester.tap(builderPrimary());
  await tester.pumpAndSettle();
  expectNoOverflow(tester, where: ' on the paper');
  expect(find.text('80 / 80 marks · 39 questions · Class 10 Science'), findsOneWidget);
  expectActionReady(tester, builderPrimary(), size, label: 'Done: download');
}
