// Task 125, steps 10: the builder's chapters step (step 3) says the paper's
// competency-based share against CBSE's 50% and why no Foundation/Advanced
// version is offered -- BEFORE the teacher generates, while the chapters can
// still change.
//
// The availability answers are real, captured in-process on the served bank
// (scripts/capture_paper_builder_fixtures.py --only ...): the half-yearly
// Class 10 Science preset on the six chapters the flow test ticks and on the
// whole syllabus, and the Class 6 Science annual preset. Every other request
// goes to the committed fixtures.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/paper_builder_api.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';

import 'fixture_api.dart';

const _phone = Size(375, 812);

/// The committed fixtures, with the Task 125 captures for the availability
/// checks and the Class 6 Science lists they need.
class _WithCompetency implements HttpClientAdapter {
  final FixtureAdapter fixtures = FixtureAdapter();
  final List<String> answered = [];

  @override
  Future<ResponseBody> fetch(
      RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    // The preset id's colons arrive percent-encoded, as FixtureAdapter knows.
    final path = Uri.decodeComponent(o.uri.path);
    String? name;
    if (o.method == 'POST' && path.endsWith('preset:cbse:10:science:half_yearly/availability')) {
      final body = o.data is String ? jsonDecode(o.data as String) : o.data;
      final chapters = (((body as Map?)?['scope'] as Map?)?['chapterIds'] as List?) ?? const [];
      name = chapters.isEmpty
          ? 'availability_10_science_all_competency'
          : 'availability_10_science_half_competency';
    } else if (o.method == 'POST' && path.endsWith('preset:cbse:6:science:annual/availability')) {
      name = 'availability_6_science_annual_all';
    } else if (o.method == 'GET' && path.endsWith('/teacher-templates') &&
        o.uri.queryParameters['grade'] == '6') {
      name = 'templates_6_science';
    } else if (o.method == 'GET' && path.endsWith('/catalog/Science/6/chapters')) {
      name = 'chapters_6_science';
    }
    if (name == null) return fixtures.fetch(o, requestStream, cancelFuture);
    answered.add(name);
    final text = File('test/paper_builder/fixtures/$name.json').readAsStringSync();
    return ResponseBody.fromString(text, 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_competency_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });
  tearDownAll(() async => Hive.close());
  setUp(() => LocalStore.instance.box.clear());

  Finder primary() => find.byKey(const ValueKey('builder-primary'));

  Future<_WithCompetency> pumpBuilder(WidgetTester tester) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final adapter = _WithCompetency();
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        api: fixtureApi(adapter),
        savePdf: (bytes, name) async {},
        schoolId: 'school_1',
        userId: fixtureTeacherId,
      ),
    ));
    await tester.pumpAndSettle();
    return adapter;
  }

  void expectPhoneReady(WidgetTester tester) {
    expect(tester.takeException(), isNull);
    final r = tester.getRect(primary());
    expect(r.left >= 0 && r.top >= 0 && r.right <= _phone.width && r.bottom <= _phone.height, isTrue,
        reason: 'primary action at $r must be on a 375x812 screen');
  }

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

  Future<void> openPreset(WidgetTester tester, String grade, String presetName) async {
    await tester.tap(find.text('Class $grade'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Science'));
    await tester.pumpAndSettle();
    await tester.tap(primary());
    await tester.pumpAndSettle();
    await tapVisible(tester, cardButton(presetName, 'Use'));
  }

  String textOf(WidgetTester tester, String key) => tester
      .widgetList<Text>(find.descendant(of: find.byKey(ValueKey(key)), matching: find.byType(Text), matchRoot: true))
      .map((t) => t.data ?? '')
      .join('\n');

  Future<void> scrollTo(WidgetTester tester, String key) => tester.scrollUntilVisible(
      find.byKey(ValueKey(key)), -200, scrollable: find.byType(Scrollable).first);

  testWidgets('step 3 shows the competency share before Generate, and it follows the chapters',
      (tester) async {
    final api = await pumpBuilder(tester);
    final halfYearly = (fixtureJson('templates_10_science')['presets'] as List)
        .firstWhere((p) => p['examType'] == 'half_yearly') as Map;
    await openPreset(tester, '10', halfYearly['name'] as String);

    // The whole syllabus: 25 of 33, CBSE's 50% met.
    await scrollTo(tester, 'availability-competency');
    expect(textOf(tester, 'availability-competency'),
        allOf(contains('Competency-based: 25 of 33 questions (76%)'), contains('CBSE asks for at least 50%.')));

    // The tier sentence sits with the paper's versions.
    await tester.scrollUntilVisible(find.byKey(const ValueKey('availability-tiers')), 200,
        scrollable: find.byType(Scrollable).first);
    expect(textOf(tester, 'availability-tiers'), contains('Foundation and Advanced versions are not offered'));

    // Six chapters: the share falls, and the line says what widening would give.
    final names = {
      for (final c in fixtureJsonList('chapters_10_science')) c['chapterId'] as String: c['chapterName'] as String,
    };
    for (final id in halfYearChapters) {
      final f = find.text(names[id]!);
      await tester.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
      Scrollable.ensureVisible(f.evaluate().first, alignment: 0.5);
      await tester.pump();
      await tester.tap(f);
      await tester.pump(const Duration(milliseconds: 100));
    }
    await tester.pump(PaperBuilderController.availabilityDebounce);
    await tester.pumpAndSettle();
    await scrollTo(tester, 'availability-competency');
    final line = textOf(tester, 'availability-competency');
    expect(line, contains('Competency-based: 8 of 30 questions (27%)'));
    expect(line, contains("Below CBSE's 50%. The whole syllabus would give 25 of 33 (76%)."));
    expect(api.fixtures.requests.where((r) => r.path.contains('generate')), isEmpty,
        reason: 'the share is shown BEFORE generating');
    expectPhoneReady(tester);
  });

  testWidgets('a bank that cannot reach 50% says so on the step, not only in the notes', (tester) async {
    await pumpBuilder(tester);
    await openPreset(tester, '6', 'Class 6 Science - Annual Examination');
    await scrollTo(tester, 'availability-competency');
    final line = textOf(tester, 'availability-competency');
    expect(line, contains('Competency-based: 11 of 37 questions (30%)'));
    expect(line, contains('The Class 6 Science bank cannot reach it with this template'));
    // It is on the panel itself, never inside the collapsed notes.
    expect(find.ancestor(of: find.byKey(const ValueKey('availability-competency')),
        matching: find.byType(ExpansionTile)), findsNothing);
    expectPhoneReady(tester);
  });

  test('a report captured before the check parses with no competency and no tiers', () {
    final a = AvailabilityView.fromJson(fixtureJson('availability_10_science_all'));
    expect(a.competency, isNull);
    expect(a.tiers, isNull);
    final b = AvailabilityView.fromJson(fixtureJson('availability_10_science_half_competency'));
    expect(b.competency!.status, 'below_scope');
    expect(b.competency!.belowTarget, isTrue);
    expect(b.tiers!.available, isFalse);
  });
}
