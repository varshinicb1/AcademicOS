// Task 902: the guided paper builder, driven end to end the way a teacher on
// a phone browser uses it (375 x 812), against the real backend's captured
// answers (fixture_api.dart says how they were captured).
//
// What these pin:
//   * class/subject -> CBSE preset -> chapters -> generate -> swap one
//     question -> pick one from the bank -> remove one -> sets -> download,
//     where the download produces both PDFs (paper + answer key) for every
//     set, then "Make another like this" asks for fresh questions;
//   * ticking chapters sends one availability check, not one per tick;
//   * the section editor refuses a mismatched total, says why, and offers
//     the one-tap fix -- no request is sent until the total matches;
//   * gaps are on screen BEFORE Generate, and a paper the bank cannot fill
//     at all (Class 7 Mathematics, which the served bank has no questions for)
//     is never offered for generation;
//   * no step overflows at 375 px and the primary action is always on screen;
//   * the last class, subject and template are remembered per teacher.
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/api_error.dart';
import 'package:academicos/data/datasources/api/paper_builder_api.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';
import 'package:academicos/presentation/paper_builder/widgets/section_editor.dart';

import 'fixture_api.dart';

const _phone = Size(375, 812);

class _Saved {
  final List<(String, List<int>)> files = [];
  Future<void> call(Uint8List bytes, String name) async => files.add((name, bytes));
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // The builder remembers the teacher's last choices in the app's Hive box
  // (LocalStore). A file-backed box writes on real I/O, which a widget
  // test's fake clock never completes: the next test's Hive call then waits
  // on it forever. The same box, opened in memory, completes its writes in
  // microtasks -- the builder reads and writes it exactly as in the app.
  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('paper_builder_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async {
    await Hive.close();
  });

  setUp(() => LocalStore.instance.box.clear());

  Future<(FixtureAdapter, _Saved)> pumpBuilder(WidgetTester tester, {bool quick = false}) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final adapter = FixtureAdapter();
    final saved = _Saved();
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        quick: quick,
        api: fixtureApi(adapter),
        savePdf: saved.call,
        schoolId: 'school_1',
        userId: fixtureTeacherId,
      ),
    ));
    await tester.pumpAndSettle();
    return (adapter, saved);
  }

  Finder primary() => find.byKey(const ValueKey('builder-primary'));

  String primaryLabel(WidgetTester tester) =>
      tester.widget<Text>(find.descendant(of: primary(), matching: find.byType(Text))).data!;

  bool primaryEnabled(WidgetTester tester) => tester.widget<ButtonStyleButton>(primary()).onPressed != null;

  /// The primary action is fully on the 375 x 812 screen, and nothing on the
  /// step overflowed (a RenderFlex overflow is reported as an exception).
  void expectPhoneReady(WidgetTester tester) {
    expect(tester.takeException(), isNull);
    final r = tester.getRect(primary());
    expect(r.left >= 0 && r.top >= 0 && r.right <= _phone.width && r.bottom <= _phone.height, isTrue,
        reason: 'primary action at $r must be on a 375x812 screen');
  }

  /// Scrolls [f] to the middle of the screen (clear of the pinned bottom
  /// bar, as a teacher's thumb would) and taps it.
  Future<void> tapVisible(WidgetTester tester, Finder f) async {
    await tester.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
    Scrollable.ensureVisible(f.evaluate().first, alignment: 0.5);
    await tester.pumpAndSettle();
    await tester.tap(f);
    await tester.pumpAndSettle();
  }

  /// Taps [label] on question [slot]'s card, scrolling the card into the
  /// middle of the screen first (the list builds cards lazily).
  Future<void> tapOnQuestion(WidgetTester tester, String slot, String label) async {
    final card = find.byKey(ValueKey('question-$slot'));
    await tester.scrollUntilVisible(card, 300, scrollable: find.byType(Scrollable).first);
    final button = find.descendant(of: card, matching: find.text(label));
    Scrollable.ensureVisible(button.evaluate().first, alignment: 0.5);
    await tester.pumpAndSettle();
    await tester.tap(button);
    await tester.pumpAndSettle();
  }

  /// Ticks each of [labels] the way a teacher runs a thumb down the list:
  /// one tap after another, without waiting for the bank check between.
  Future<void> tickQuickly(WidgetTester tester, Iterable<String> labels) async {
    for (final label in labels) {
      final f = find.text(label);
      await tester.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
      Scrollable.ensureVisible(f.evaluate().first, alignment: 0.5);
      await tester.pump();
      await tester.tap(f);
      await tester.pump(const Duration(milliseconds: 100));
    }
    await tester.pump(PaperBuilderController.availabilityDebounce);
    await tester.pumpAndSettle();
  }

  Finder cardButton(String cardText, String button) => find.descendant(
        of: find.ancestor(of: find.text(cardText), matching: find.byType(Card)),
        matching: find.text(button),
      );

  List<Recorded> calls(FixtureAdapter a, String method, bool Function(String) path) =>
      a.requests.where((r) => r.method == method && path(r.path)).toList();

  testWidgets('Class 10 Science half-yearly: preset -> chapters -> generate -> swap -> pick -> download, on a phone',
      (tester) async {
    final (api, saved) = await pumpBuilder(tester);
    final halfYearly = (fixtureJson('templates_10_science')['presets'] as List)
        .firstWhere((p) => p['examType'] == 'half_yearly') as Map;

    // Step 1: nothing remembered, so class and subject first.
    expect(find.text('Which class is this paper for?'), findsOneWidget);
    expect(primaryEnabled(tester), isFalse);
    expectPhoneReady(tester);
    await tester.tap(find.text('Class 10'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Science'));
    await tester.pumpAndSettle();
    await tester.tap(primary());
    await tester.pumpAndSettle();

    // Step 2: templates, CBSE patterns with marks, time and sections.
    expect(find.text('CBSE patterns'), findsOneWidget);
    expect(find.text('Class 10 · Science'), findsOneWidget);
    expectPhoneReady(tester);
    await tester.scrollUntilVisible(find.text(halfYearly['name'] as String), 200,
        scrollable: find.byType(Scrollable).first);
    expect(find.textContaining('80 marks · 180 min · 39 questions · Suggested pattern'), findsOneWidget);
    expect(find.textContaining('80 marks · 180 min · 39 questions · CBSE board pattern'), findsOneWidget);
    await tapVisible(tester, cardButton(halfYearly['name'] as String, 'Use'));

    // Step 3: the whole syllabus fills every section.
    expect(find.text('Ready: every section can be filled from the whole syllabus.'), findsOneWidget);
    expect(primaryLabel(tester), 'Generate paper');
    expectPhoneReady(tester);

    // A half-yearly paper covers the first half of the book: tick those
    // chapters. The check re-runs, and the gap is on screen before Generate.
    final names = {
      for (final c in fixtureJsonList('chapters_10_science')) c['chapterId'] as String: c['chapterName'] as String,
    };
    final checksBefore = calls(api, 'POST', (p) => p.endsWith('/availability')).length;
    await tickQuickly(tester, [for (final id in halfYearChapters) names[id]!]);
    final checks = calls(api, 'POST', (p) => p.endsWith('/availability')).skip(checksBefore).toList();
    expect(checks, hasLength(1), reason: 'six ticks, one check: $checks');
    expect(((checks.single.body as Map)['scope'] as Map)['chapterIds'], unorderedEquals(halfYearChapters));
    await tester.scrollUntilVisible(find.byKey(const ValueKey('availability-summary')), -200,
        scrollable: find.byType(Scrollable).first);
    expect(find.text('1 of 5 sections cannot be filled from 6 chapters.'), findsOneWidget);
    expect(find.text('Section E - Source / case based needs 3 × 4-mark, 0 fit from these chapters.'),
        findsOneWidget);
    // How short, in marks (QA P-18): A 20 + B 12 + C 21 + D 15, and E none.
    expect(find.text('The paper would print 68 of 80 marks — 12 short.'), findsOneWidget);
    expect(primaryLabel(tester), 'Generate anyway (1 section short)');
    expect(calls(api, 'POST', (p) => p.contains('generate')), isEmpty, reason: 'gaps are shown BEFORE generating');
    expectPhoneReady(tester);

    // One tap on the server's "widen the chapters" fix: whole syllabus again.
    await tapVisible(tester, find.text('Add the chapters that hold 10 more such question(s).'));
    await tester.scrollUntilVisible(find.byKey(const ValueKey('availability-summary')), -200,
        scrollable: find.byType(Scrollable).first);
    expect(find.text('Ready: every section can be filled from the whole syllabus.'), findsOneWidget);

    // Two sets, then Generate.
    await tapVisible(tester, find.text('A, B'));
    await tester.tap(primary());
    await tester.pumpAndSettle();
    final gen = calls(api, 'POST', (p) => p == '/papers/generate-from-template').single;
    expect(gen.body, containsPair('templateId', halfYearly['id']));
    expect(gen.body, containsPair('setCount', 2));
    expect(gen.body, containsPair('allowGaps', false), reason: 'the check said complete; a new gap must be refused');
    expect(gen.status, 200);

    // Step 4: the paper, with live totals.
    final generated = fixtureJson('generate_10_science')['paper'] as Map;
    final q1Before = (generated['sections'][0]['questions'][0]['stem'] as String);
    final q1After = (fixtureJson('swap_10_science')['paper']['sections'][0]['questions'][0]['stem'] as String);
    expect(find.text('80 / 80 marks · 39 questions · Class 10 Science'), findsOneWidget);
    expect(find.text(q1Before), findsOneWidget);
    expectPhoneReady(tester);

    // Swap question 1: the server's next best question takes its place.
    await tapOnQuestion(tester, '1', 'Swap');
    expect(calls(api, 'POST', (p) => p.endsWith('/questions/1/swap')).single.status, 200);
    await tester.scrollUntilVisible(find.byKey(const ValueKey('question-1')), -200,
        scrollable: find.byType(Scrollable).first);
    expect(find.text(q1After), findsOneWidget);
    expect(find.text(q1Before), findsNothing);

    // Pick question 27 from the bank: 3-mark, keyed questions only.
    final search = fixtureJsonList('search_10_science_3m');
    final pickedStem = fixtureJson('pick_10_science')['paper']['sections'][2]['questions'][0]['stem'] as String;
    await tapOnQuestion(tester, '27', 'Pick');
    final searched = calls(api, 'POST', (p) => p == '/questions/search').single;
    expect(searched.body, allOf(containsPair('minMarks', 3), containsPair('maxMarks', 3)));
    expect(find.textContaining('Has answer key'), findsWidgets);
    await tester.tap(find.text(search.first['stem'] as String).first);
    await tester.pumpAndSettle();
    final pick = calls(api, 'POST', (p) => p.endsWith('/questions/27')).single;
    expect(pick.body, {'questionId': search.first['id']});
    await tester.scrollUntilVisible(find.byKey(const ValueKey('question-27')), 200,
        scrollable: find.byType(Scrollable).first);
    expect(find.text(pickedStem), findsOneWidget);
    expectPhoneReady(tester);

    // Remove the first long answer: asked first, then off the paper and
    // every set; the totals drop and Section D shows as short.
    final removedSlot = fixtureJson('remove_10_science')['slot'] as String;
    final removedStem = (fixtureJson('pick_10_science')['paper']['sections'] as List)
        .expand((s) => s['questions'] as List)
        .firstWhere((q) => '${q['displayNumber']}' == removedSlot)['stem'] as String;
    await tapOnQuestion(tester, removedSlot, 'Remove');
    expect(find.text('Remove Q$removedSlot?'), findsOneWidget);
    expect(find.textContaining('drops to 75 marks, its OR choice goes with it'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('confirm-remove')));
    await tester.pumpAndSettle();
    expect(calls(api, 'DELETE', (p) => p.endsWith('/questions/$removedSlot')).single.status, 200);
    expect(find.text(removedStem), findsNothing);
    await tester.scrollUntilVisible(find.byKey(const ValueKey('paper-totals')), -2000,
        scrollable: find.byType(Scrollable).first);
    expect(find.text('75 / 80 marks · 38 questions · Class 10 Science'), findsOneWidget);
    expect(find.text('• Section D - Long answer: 2 of 3 questions (you removed 1)'), findsOneWidget);
    expectPhoneReady(tester);

    // Set B, fetched fresh because set A was edited.
    await tester.scrollUntilVisible(find.text('Set B'), -300, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('Set B'));
    await tester.pumpAndSettle();
    expect(calls(api, 'GET', (p) => p.endsWith('_set_B')).single.status, 200);
    // Set B prints its own questions, and says so (QA P-10: "Set B is Set
    // A reordered" was untrue, and a Set B question could not be changed).
    expect(find.byKey(const ValueKey('set-explained')), findsOneWidget);
    expect(find.textContaining('reordered'), findsNothing);
    expect(find.text('Swap'), findsWidgets, reason: 'Set B is edited by its own id');
    await tester.tap(find.text('Set A'));
    await tester.pumpAndSettle();

    // Step 5: download both PDFs for both sets.
    await tester.tap(primary());
    await tester.pumpAndSettle();
    expect(find.text('Your paper is saved'), findsOneWidget);
    expect(find.text('Make and save another like this'), findsOneWidget);
    expectPhoneReady(tester);
    await tester.tap(primary());
    await tester.pumpAndSettle();
    expect(calls(api, 'POST', (p) => p.endsWith('/export/pdf')).length, 2);
    expect(calls(api, 'POST', (p) => p.endsWith('/export/answer-key')).length, 2);
    expect(saved.files.map((f) => f.$1).toList(), [
      'class_10_science_half_yearly_examination_set_a_paper.pdf',
      'class_10_science_half_yearly_examination_set_a_answer_key.pdf',
      'class_10_science_half_yearly_examination_set_b_paper.pdf',
      'class_10_science_half_yearly_examination_set_b_answer_key.pdf',
    ]);
    for (final f in saved.files) {
      expect(String.fromCharCodes(f.$2.take(5)), '%PDF-');
    }
    expect(find.text('Paper (Set A) downloaded'), findsOneWidget);
    expect(find.text('Answer key (Set B) downloaded'), findsOneWidget);
    // "Make another like this": same template and chapters, with the
    // questions of the paper just made (swap, pick and removal included)
    // sent as the ones to avoid. The server's answer is a full 80-mark
    // paper sharing 4 of its 45 questions with the last one, each named.
    final lastPaper = (fixtureJson('remove_10_science')['paper']['sections'] as List)
        .expand((s) => s['questions'] as List)
        .expand((q) => [q['questionId'], if (q['internalChoiceQuestionId'] != null) q['internalChoiceQuestionId']])
        .cast<String>()
        .toList()
      ..sort();
    await tester.tap(find.text('Make and save another like this'));
    await tester.pumpAndSettle();
    final another = calls(api, 'POST', (p) => p == '/papers/generate-from-template').last;
    expect(another.status, 200);
    expect(another.body, containsPair('templateId', halfYearly['id']));
    expect((another.body as Map)['avoidQuestionIds'], lastPaper);
    final freshQ1 = fixtureJson('generate_10_science_another')['paper']['sections'][0]['questions'][0]['stem'] as String;
    expect(find.text('80 / 80 marks · 39 questions · Class 10 Science'), findsOneWidget);
    expect(find.byKey(const ValueKey('paper-short')), findsNothing);
    expect(find.text(freshQ1), findsOneWidget);
    expect(freshQ1, isNot(q1After));

    // Every request had a captured answer: no check was sent for a
    // selection the teacher only passed through.
    final failed = api.requests.where((r) => r.status >= 400).toList();
    expect(failed, isEmpty, reason: '$failed');

    // Remembered for next time.
    final memory = BuilderMemory(fixtureTeacherId);
    expect((memory.grade, memory.subject, memory.templateId), (10, 'Science', halfYearly['id']));
  });

  testWidgets('a remembered class, subject and template: offered, not chosen; then one tap to the chapters',
      (tester) async {
    BuilderMemory(fixtureTeacherId)
        .remember(grade: 10, subject: 'Science', templateId: 'preset:cbse:10:science:half_yearly');
    final (api, _) = await pumpBuilder(tester);
    // A new paper starts at the class (QA P-25), with the last one a tap away.
    expect(find.text('Which class is this paper for?'), findsOneWidget);
    expect(api.requests.where((r) => r.path.endsWith('/teacher-templates')), isEmpty);
    expect(find.text('Continue where you left off'), findsOneWidget);
    expectPhoneReady(tester);
    await tester.tap(find.text('Continue with Class 10 Science'));
    await tester.pumpAndSettle();
    expect(find.text('Class 10 · Science'), findsOneWidget);
    expect(primaryLabel(tester), 'Use "Class 10 Science - Half-Yearly Examination"');
    expectPhoneReady(tester);
    await tester.tap(primary());
    await tester.pumpAndSettle();
    expect(find.text('Ready: every section can be filled from the whole syllabus.'), findsOneWidget);
    expect(api.requests.where((r) => r.status >= 400), isEmpty, reason: '${api.requests}');
  });

  testWidgets('Quick paper (CBSE pattern) opens on the class\'s CBSE annual pattern', (tester) async {
    BuilderMemory(fixtureTeacherId).remember(grade: 10, subject: 'Science');
    final (api, _) = await pumpBuilder(tester, quick: true);
    expect(find.text('Quick paper (CBSE pattern)'), findsOneWidget);
    expect(find.textContaining('Class 10 Science - Annual Examination'), findsOneWidget);
    expect(primaryLabel(tester), 'Generate paper');
    expect(calls(api, 'POST', (p) => Uri.decodeComponent(p).endsWith('preset:cbse:10:science:annual/availability')),
        hasLength(1));
    expectPhoneReady(tester);
  });

  testWidgets('the section editor refuses a mismatched total, says why, and saves once it matches',
      (tester) async {
    BuilderMemory(fixtureTeacherId).remember(grade: 10, subject: 'Science');
    final (api, _) = await pumpBuilder(tester);
    await tester.tap(find.text('Continue with Class 10 Science'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('New template'));
    await tester.pumpAndSettle();

    // The captured request: "Weekly check", 25 marks, A 10x1, B 4x3 (= 22).
    final editorList = find.descendant(of: find.byType(SectionEditor), matching: find.byType(Scrollable)).first;
    Future<Finder> reach(Finder f) async {
      await tester.scrollUntilVisible(f, 150, scrollable: editorList);
      Scrollable.ensureVisible(f.evaluate().first, alignment: 0.4);
      await tester.pumpAndSettle();
      return f;
    }

    await tester.enterText(await reach(find.widgetWithText(TextField, 'Template name')), 'Weekly check');
    await tester.enterText(await reach(find.byKey(const ValueKey('editor-total'))), '25');
    await tester.enterText(await reach(find.widgetWithText(TextField, 'Section A title')), 'Section A');
    await tester.enterText(await reach(find.widgetWithText(TextField, 'Section B title')), 'Section B');
    await tester.tap(await reach(find.byTooltip('Fewer section B questions')));
    await tester.pumpAndSettle();
    await tester.tap(await reach(find.byTooltip('More section B marks each')));
    await tester.pumpAndSettle();

    expect(find.text('Running total: 22 of 25 marks'), findsOneWidget);
    expect(find.text('Sections add up to 22 marks but the total is 25.'), findsOneWidget);
    final save = find.byKey(const ValueKey('editor-save'));
    expect(tester.widget<FilledButton>(save).onPressed, isNull);
    await tester.tap(save, warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(calls(api, 'POST', (p) => p.endsWith('/teacher-templates')), isEmpty,
        reason: 'a mismatched total is shown inline, never sent to fail');
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('Set the total to 22'));
    await tester.pumpAndSettle();
    expect(find.text('Running total: 22 of 22 marks'), findsOneWidget);
    await tester.tap(save);
    await tester.pumpAndSettle();

    final created = calls(api, 'POST', (p) => p.endsWith('/teacher-templates')).single;
    expect(created.status, 200);
    final body = created.body as Map;
    expect((body['name'], body['totalMarks'], body['durationMinutes']), ('Weekly check', 22, 45));
    expect([for (final s in body['sections'] as List) (s['title'], s['questionCount'], s['marksEach'])],
        [('Section A', 10, 1), ('Section B', 4, 3)]);
    // Saved, listed under "mine", and in use for this paper.
    expect(find.textContaining('Weekly check · 22 marks · 45 min'), findsOneWidget);
    expect(find.byKey(const ValueKey('availability-summary')), findsOneWidget);
    expect(api.requests.where((r) => r.status >= 400), isEmpty, reason: '${api.requests}');
    expectPhoneReady(tester);
  });

  testWidgets('Class 7 Mathematics unit test: the gaps are shown before generating, and nothing is offered',
      (tester) async {
    final (api, _) = await pumpBuilder(tester);
    await tester.tap(find.text('Class 7'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Mathematics'));
    await tester.pumpAndSettle();
    await tester.tap(primary());
    await tester.pumpAndSettle();
    final unit = (fixtureJson('templates_7_maths')['presets'] as List)
        .firstWhere((p) => p['examType'] == 'unit_test') as Map;
    await tapVisible(tester, cardButton(unit['name'] as String, 'Use'));

    await tickQuickly(tester, ['Integers', 'Fractions and Decimals']);
    expect(find.text('No questions in the bank yet'), findsWidgets);
    await tester.scrollUntilVisible(find.byKey(const ValueKey('availability-summary')), -200,
        scrollable: find.byType(Scrollable).first);
    expect(find.text('The bank has nothing for this paper in 2 chapters yet.'), findsOneWidget);
    expect(find.text('Section A - Objective needs 6 × 1-mark, 0 fit from these chapters.'), findsOneWidget);
    expect(find.byKey(const ValueKey('availability-marks')), findsNothing, reason: 'nothing at all can print');
    expect(find.byKey(const ValueKey('availability-competency')), findsNothing);
    expect(find.text('The bank has no Class 7 Mathematics questions yet.'), findsWidgets);
    expect(primaryLabel(tester), 'Nothing to generate yet');
    expect(primaryEnabled(tester), isFalse);
    expect(calls(api, 'POST', (p) => p.contains('generate')), isEmpty);
    expectPhoneReady(tester);
  });

  group('the API layer reads the real responses', () {
    test('server errors become sentences: pydantic 422, the 400 with its report', () {
      expect(serverErrorMessage(dioError(fixtureJson('create_template_mismatch'), 422)),
          'sections add up to 22 marks but the total is 25 (Section A 10x1=10, Section B 4x3=12)');
      expect(serverErrorMessage(dioError(fixtureJson('generate_7_maths_refused'), 400)),
          'no question in the bank fits this template');
    });

    test('rule Q1: a bank question without a verified key cannot be offered', () {
      final real = Map<String, dynamic>.from(fixtureJsonList('search_10_science_3m').first);
      expect(BankItem.fromJson(real).hasAnswerKey, isTrue);
      // The same record with its scheme emptied -- a provenance label alone
      // does not count (QuestionBank.has_answer_key).
      final unkeyed = {...real, 'answerScheme': {'modelAnswer': '  ', 'markingPoints': [], 'provenance': 'cbse_marking_scheme'}};
      expect(BankItem.fromJson(unkeyed).hasAnswerKey, isFalse);
    });

    test('the generated paper parses whole: 39 questions, 80 marks, sets A and B', () {
      final r = TemplatePaperResult.fromJson(fixtureJson('generate_10_science'));
      expect(r.paper.sections.expand((s) => s.questions), hasLength(39));
      expect(r.paper.sections.fold<int>(0, (s, x) => s + x.totalMarks), 80);
      expect(r.paper.sets.map((s) => s.setLabel), ['A', 'B']);
    });
  });
}
