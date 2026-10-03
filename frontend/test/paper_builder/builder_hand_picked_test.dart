// Audit D57: no web screen made a paper from exactly the questions a teacher
// chose -- the live bundle called POST /papers/generate-from-ids 0 times; the
// web could only pick into the slots of a paper a template had made. And the
// route itself dropped an id it could not print without a word.
//
// The builder now has "Pick the questions yourself": the class's bank,
// filtered by chapter, marks and words; the questions picked so far with
// their total; and Generate, which sends exactly those ids. The answers are
// the real backend's (fixture_api.dart; captured by
// scripts/capture_paper_builder_fixtures.py on the served bank).
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';

import 'fixture_api.dart';

const _phone = Size(375, 812);

/// The captured generate-from-ids request (its ids) from the manifest.
List<String> _capturedIds() => List<String>.from(((fixtureJson('manifest')['responses'] as List)
        .firstWhere((r) => r['file'] == 'generate_from_ids_10_science.json') as Map)['body']['questionIds']
    as List);

/// The fixtures, plus the hand-pick step's answers: the whole-bank search,
/// and generate-from-ids for exactly the captured ids (404 for any other
/// list, as the server answers an id it cannot print).
class _HandPickAdapter implements HttpClientAdapter {
  final FixtureAdapter fixtures = FixtureAdapter();
  final List<Map<String, dynamic>> generated = [];
  bool unknownNext = false;

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final path = o.uri.path.replaceFirst('/api/v1', '');
    final body = o.data is String ? jsonDecode(o.data as String) : o.data;
    if (o.method == 'POST' && path == '/questions/search' && body is Map && body['minMarks'] == null) {
      return _json(200, jsonDecode(File('test/paper_builder/fixtures/search_10_science_any.json').readAsStringSync()));
    }
    if (o.method == 'POST' && path == '/papers/generate-from-ids' && body is Map) {
      generated.add(Map<String, dynamic>.from(body));
      final ids = List<String>.from(body['questionIds'] as List);
      if (ids.join(',') == _capturedIds().join(',')) return _json(200, fixtureJson('generate_from_ids_10_science'));
      return _json(404, fixtureJson('generate_from_ids_10_science_unknown'));
    }
    return fixtures.fetch(o, requestStream, cancelFuture);
  }

  ResponseBody _json(int status, Object body) => ResponseBody.fromString(jsonEncode(body), status, headers: {
        Headers.contentTypeHeader: ['application/json'],
      });

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_hand_picked_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async {
    await Hive.close();
  });

  setUp(() => LocalStore.instance.box.clear());

  Finder primary() => find.byKey(const ValueKey('builder-primary'));
  String primaryLabel(WidgetTester tester) =>
      tester.widget<Text>(find.descendant(of: primary(), matching: find.byType(Text))).data!;

  Future<void> tapVisible(WidgetTester tester, Finder f) async {
    await tester.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
    Scrollable.ensureVisible(f.evaluate().first, alignment: 0.5);
    await tester.pumpAndSettle();
    await tester.tap(f);
    await tester.pumpAndSettle();
  }

  testWidgets('pick questions from the bank, and the paper prints exactly those, on a phone', (tester) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    BuilderMemory(fixtureTeacherId).remember(grade: 10, subject: 'Science');
    final adapter = _HandPickAdapter();
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        api: fixtureApi(adapter),
        savePdf: (_, __) async {},
        schoolId: 'school_1',
        userId: fixtureTeacherId,
      ),
    ));
    await tester.pumpAndSettle();
    // A new paper starts at the class (QA P-25); the remembered one is a tap away.
    await tester.tap(find.text('Continue with Class 10 Science'));
    await tester.pumpAndSettle();

    // The template step offers the bank instead of a template.
    await tapVisible(tester, find.byKey(const ValueKey('hand-pick')));
    expect(find.text('Step 3 of 5 · Questions'), findsOneWidget);
    expect(find.text('No question picked yet. Add them from the bank below.'), findsOneWidget);
    expect(primaryLabel(tester), 'Pick questions to make the paper');
    expect(tester.widget<ButtonStyleButton>(primary()).onPressed, isNull);

    final ids = _capturedIds();
    for (final id in ids) {
      await tapVisible(tester, find.descendant(of: find.byKey(ValueKey('bank-$id')), matching: find.byTooltip('Add to the paper')));
    }
    await tester.scrollUntilVisible(find.byKey(const ValueKey('hand-pick-total')), -300,
        scrollable: find.byType(Scrollable).first);
    expect(find.text('Your paper: 2 questions, 2 marks'), findsOneWidget);
    expect(primaryLabel(tester), 'Generate paper (2 questions, 2 marks)');
    expect(tester.takeException(), isNull);

    await tester.tap(primary());
    await tester.pumpAndSettle();
    final sent = adapter.generated.single;
    expect(sent['questionIds'], ids, reason: 'exactly the questions picked, in order');
    expect(sent['subject'], 'Science');
    expect(sent['grade'], 10);
    expect(sent['teacherSeconds'], isA<num>());

    // The saved paper, ready to review, swap, pick or remove.
    expect(find.text('Step 4 of 5 · Review paper'), findsOneWidget);
    expect(find.byKey(const ValueKey('paper-totals')), findsOneWidget);
    expect(tester.widget<Text>(find.byKey(const ValueKey('paper-totals'))).data, startsWith('2 / 2 marks · 2 questions'));
    expect(find.byKey(const ValueKey('paper-short')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('an id the bank cannot print is refused by name, on the step', (tester) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    BuilderMemory(fixtureTeacherId).remember(grade: 10, subject: 'Science');
    final adapter = _HandPickAdapter();
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        api: fixtureApi(adapter),
        savePdf: (_, __) async {},
        schoolId: 'school_1',
        userId: fixtureTeacherId,
      ),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continue with Class 10 Science'));  // QA P-25: a new paper starts at the class
    await tester.pumpAndSettle();
    await tapVisible(tester, find.byKey(const ValueKey('hand-pick')));
    // Only the first of the two: a list the server did not capture is
    // answered with its refusal, as the server answers an id it cannot print.
    final first = _capturedIds().first;
    await tapVisible(tester, find.descendant(of: find.byKey(ValueKey('bank-$first')), matching: find.byTooltip('Add to the paper')));
    await tester.tap(primary());
    await tester.pumpAndSettle();
    expect(find.text('Step 3 of 5 · Questions'), findsOneWidget);
    await tester.scrollUntilVisible(find.byKey(const ValueKey('hand-pick-error')), -300,
        scrollable: find.byType(Scrollable).first);
    expect(tester.widget<Text>(find.byKey(const ValueKey('hand-pick-error'))).data,
        contains('no-such-id-xyz'));
  });
}
