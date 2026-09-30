// The classes and subjects the builder offers must be ones the bank can serve.
//
// Requirements v3: classes 1-10 (6-10 until 2026-09-29; the user, 2026-09-23:
// "skip 11 and 12 for now"), and of those only the classes the bank holds
// questions for. The bank behind it holds nothing for class 11 and cannot build a
// Maths or Science paper for 12, so quick-generate answers 400 "Unable to find
// sufficient questions" -- a dead end a teacher reaches only after choosing a
// class, a subject and a template.
//
// Audit D40 (2026-09-27): the same dead end, by subject. The builder offered
// seven subjects for every class; 21 of those 35 pairs (Hindi, Sanskrit and
// Computer Science 6-10, Social Science 6-9, English 7-8) have no questions,
// and Hindi 8's unit test was "available 0 of 16". It now offers what GET
// /catalog -- the real served bank's, captured in fixtures/catalog.json -- has
// questions for, and names the rest.
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';

import 'fixture_api.dart';

const _phone = Size(375, 812);

/// The fixtures, with the first GET /catalog refused.
class _CatalogDown implements HttpClientAdapter {
  _CatalogDown({required this.status});
  final int? status;
  final FixtureAdapter fixtures = FixtureAdapter();
  int refusals = 0;

  @override
  Future<ResponseBody> fetch(
      RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (!o.uri.path.endsWith('/catalog') || refusals >= 1) {
      return fixtures.fetch(o, requestStream, cancelFuture);
    }
    refusals++;
    if (status == null) {
      throw DioException.connectionError(requestOptions: o, reason: 'host unreachable');
    }
    return ResponseBody.fromString('{"detail":"Internal Server Error"}', status!, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_grades_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });
  tearDownAll(() async => Hive.close());
  setUp(() => LocalStore.instance.box.clear());

  test('the builder knows classes 1-10 and no class above them', () {
    expect(builderGrades, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  });

  test('every class has subjects to offer, EVS from class 3', () {
    for (final grade in builderGrades) {
      expect(builderSubjects(grade), isNotEmpty, reason: 'class $grade');
    }
    expect(builderSubjects(2), isNot(contains('EVS')));
    expect(builderSubjects(3), contains('EVS'));
  });

  Future<void> pump(WidgetTester tester, HttpClientAdapter adapter) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        api: fixtureApi(adapter),
        savePdf: (bytes, name) async {},
        schoolId: 'school_1',
        userId: fixtureTeacherId,
      ),
    ));
    await tester.pumpAndSettle();
  }

  List<String> offered(WidgetTester tester) => [
        for (final chip in tester.widgetList<ChoiceChip>(find.byType(ChoiceChip)))
          (chip.label as Text).data!,
      ].where((l) => !l.startsWith('Class ')).toList();

  String notYet(WidgetTester tester) =>
      tester.widget<Text>(find.descendant(
          of: find.byKey(const ValueKey('subjects-not-yet')), matching: find.byType(Text))).data!;

  testWidgets('a class the bank holds nothing for is not offered', (tester) async {
    // The fixture is the served bank's catalog, which has no class 1-5 yet.
    await pump(tester, FixtureAdapter());
    for (final grade in [1, 2, 3, 4, 5]) {
      expect(find.text('Class $grade'), findsNothing, reason: 'class $grade');
    }
    for (final grade in [6, 7, 8, 9, 10]) {
      expect(find.text('Class $grade'), findsOneWidget, reason: 'class $grade');
    }
  });

  testWidgets('each class offers only the subjects the bank has questions for', (tester) async {
    await pump(tester, FixtureAdapter());
    final want = {
      6: ['Mathematics', 'Science', 'English'],
      7: ['Mathematics', 'Science'],
      8: ['Mathematics', 'Science'],
      9: ['Mathematics', 'Science', 'English'],
      10: ['Mathematics', 'Science', 'Social Science', 'English'],
    };
    for (final MapEntry(key: grade, value: subjects) in want.entries) {
      await tester.tap(find.text('Class $grade'));
      await tester.pumpAndSettle();
      expect(offered(tester), subjects, reason: 'class $grade');
    }
    // 14 of the 35 pairs; the audit's 21 are the rest.
    expect(want.values.fold<int>(0, (n, s) => n + s.length), 14);
    expect(tester.takeException(), isNull);
  });

  testWidgets('the subjects with nothing yet are named, not silently missing', (tester) async {
    await pump(tester, FixtureAdapter());
    await tester.tap(find.text('Class 8'));
    await tester.pumpAndSettle();
    expect(notYet(tester),
        'Social Science, English, Hindi, Sanskrit and Computer Science have no questions for Class 8 yet.');
    await tester.tap(find.text('Class 10'));
    await tester.pumpAndSettle();
    expect(notYet(tester), 'Hindi, Sanskrit and Computer Science have no questions for Class 10 yet.');
  });

  testWidgets('a remembered subject the bank has nothing for is not restored', (tester) async {
    BuilderMemory(fixtureTeacherId).remember(grade: 8, subject: 'Hindi');
    final adapter = FixtureAdapter();
    await pump(tester, adapter);
    expect(find.text('Which class is this paper for?'), findsOneWidget);
    expect(adapter.requests.where((r) => r.path.endsWith('/teacher-templates')), isEmpty);
  });

  testWidgets('a remembered class 12 is not restored either', (tester) async {
    BuilderMemory(fixtureTeacherId).remember(grade: 12, subject: 'English');
    final adapter = FixtureAdapter();
    await pump(tester, adapter);
    expect(find.text('Which class is this paper for?'), findsOneWidget);
    expect(adapter.requests.where((r) => r.path.endsWith('/teacher-templates')), isEmpty);
  });

  testWidgets('a catalog that did not load says so and retries', (tester) async {
    final adapter = _CatalogDown(status: 500);
    await pump(tester, adapter);
    await tester.tap(find.text('Class 10'));
    await tester.pumpAndSettle();
    expect(offered(tester), isEmpty);
    expect(find.text('Retry'), findsOneWidget);
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(offered(tester), ['Mathematics', 'Science', 'Social Science', 'English']);
    expect(adapter.refusals, 1);
  });
}
