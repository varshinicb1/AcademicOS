// QA pass of 2026-10-01: the builder's sets, its quick paper and its checks
//   * P-10: Set B said "Set B is Set A reordered. Swap or pick on Set A;
//     every set follows" -- untrue (the sets print different questions) and
//     a garbled Set B question could not be changed. Set B is edited by its
//     own paper id, which the server takes (paper_template_routes.py:
//     PaperStore.family resolves `<id>_set_B`).
//   * P-13: before generating, the competency share is Set A's; it says so.
//   * P-14: "Quick paper (CBSE pattern)" opened the last template used.
//   * P-18: a short paper says the marks it reaches, without a green tick
//     beside the gaps, and offers only fixes that can close one.
//   * P-35: the template line on the chapters step wraps.
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';

import '../responsive/builder_driver.dart';
import '../responsive/responsive_harness.dart';

const _setBStem = 'A question only Set B prints, swapped in';

/// The captured answers, plus the one capture there is none for: a swap on
/// Set B's own id, answered with Set B as the server returns it.
class _WithSetEdits extends FixtureAdapter {
  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final id = fixtureJson('generate_10_science')['paper']['id'] as String;
    final path = o.uri.path.replaceFirst('/api/v1', '');
    if (o.method == 'POST' && path == '/papers/${id}_set_B/questions/1/swap') {
      requests.add(Recorded(o.method, path, const {}, null, 200));
      final b = jsonDecode(jsonEncode(fixtureJson('paper_10_science_set_b'))) as Map<String, dynamic>;
      b['sections'][0]['questions'][0]['stem'] = _setBStem;
      b['sections'][0]['questions'][0]['questionId'] = 'q:set-b-swapped';
      return ResponseBody.fromString(
          jsonEncode({'paper': b, 'slot': '1', 'replacedQuestionId': 'q:old', 'questionId': 'q:set-b-swapped',
            'notes': ['Taken from outside the chosen chapters'], 'counts': null}),
          200,
          headers: {Headers.contentTypeHeader: ['application/json']});
    }
    return super.fetch(o, requestStream, cancelFuture);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useAppFonts();
  useInMemoryHive();

  testWidgets('Set B has its own questions and its own Swap (P-10)', (tester) async {
    useScreen(tester, laptopScreen);
    final adapter = _WithSetEdits();
    await tester.pumpWidget(appForTest(PaperBuilderPage(
      api: fixtureApi(adapter),
      savePdf: (bytes, name) async {},
      schoolId: 'school_1',
      userId: fixtureTeacherId,
    )));
    await tester.pumpAndSettle();
    await toChaptersStep(tester, laptopScreen);
    await generate(tester, laptopScreen);
    final setAStem = fixtureJson('generate_10_science')['paper']['sections'][0]['questions'][0]['stem'] as String;
    // P-33: the section's own "Section A" is not printed twice.
    expect(find.text('Section A - Objective (MCQ / assertion-reason) · 20 marks'), findsOneWidget);
    expect(find.textContaining('Section A · Section A'), findsNothing);

    await tester.tap(find.text('Set B'));
    await tester.pumpAndSettle();
    expect(find.text('Set B has its own questions in the same sections and marks. Swap or Pick here changes '
        'Set B only; Remove takes the question in the same place out of every set.'), findsOneWidget);

    await tester.tap(find.descendant(of: find.byKey(const ValueKey('question-1')), matching: find.text('Swap')));
    await tester.pumpAndSettle();
    final id = fixtureJson('generate_10_science')['paper']['id'] as String;
    expect(adapter.requests.where((r) => r.path.endsWith('/swap')).single.path, '/papers/${id}_set_B/questions/1/swap');
    expect(find.text(_setBStem), findsOneWidget);
    expect(find.text('Taken from outside the chosen chapters'), findsOneWidget);

    await tester.tap(find.text('Set A'));
    await tester.pumpAndSettle();
    expect(find.text(setAStem), findsOneWidget, reason: 'Set A is not touched by a Set B swap');
    expect(find.text('Taken from outside the chosen chapters'), findsNothing, reason: "Set B's note stays on Set B");
  });

  testWidgets('before generating, the competency share is said to be Set A\'s (P-13)', (tester) async {
    useScreen(tester, laptopScreen);
    await tester.pumpWidget(appForTest(PaperBuilderPage(
      api: fixtureApi(_CompetencyAdapter()),
      savePdf: (bytes, name) async {},
      schoolId: 'school_1',
      userId: fixtureTeacherId,
    )));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Class 10'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Science'));
    await tester.pumpAndSettle();
    await tester.tap(builderPrimary());
    await tester.pumpAndSettle();
    final halfYearly = (fixtureJson('templates_10_science')['presets'] as List)
        .firstWhere((p) => p['examType'] == 'half_yearly') as Map;
    await tapVisible(tester, cardButton(halfYearly['name'] as String, 'Use'));
    final line = find.byKey(const ValueKey('availability-competency'));
    expect(find.descendant(of: line, matching: find.textContaining('Set A:')), findsNothing, reason: 'one set');
    await tapVisible(tester, find.text('A, B, C'));
    await tester.scrollUntilVisible(line, -200, scrollable: find.byType(Scrollable).first);
    expect(find.descendant(of: line, matching: find.textContaining('Set A: Competency-based')), findsOneWidget);
    expect(find.byKey(const ValueKey('competency-other-sets')), findsOneWidget);

    // P-18, on the same check (two sections short, the share 76%): the
    // marks reached in one sentence, no green tick beside the gaps, and no
    // fix that cannot close one.
    expect(find.text('The paper would print 62 of 80 marks — 18 short.'), findsOneWidget);
    expect(find.descendant(of: line, matching: find.byIcon(Icons.check_circle_outline)), findsNothing);
    expect(find.text('Section B - Very short answer needs 6 × 2-mark, 3 fit from the whole syllabus.'), findsOneWidget);
    expect(find.text('Print this section without OR choices.'), findsNothing,
        reason: 'fewer ORs never fill a compulsory question');
    expect(find.textContaining('Ask for 3 question(s) instead of 6'), findsOneWidget);
  });

  testWidgets('Quick paper opens the CBSE annual pattern even when another template was used last (P-14)',
      (tester) async {
    BuilderMemory(fixtureTeacherId)
        .remember(grade: 10, subject: 'Science', templateId: 'preset:cbse:10:science:half_yearly');
    final (api, _) = await pumpBuilder(tester, laptopScreen, quick: true);
    expect(find.textContaining('Class 10 Science - Annual Examination'), findsOneWidget);
    expect(find.textContaining('Half-Yearly'), findsNothing);
    // P-35: the template line wraps; cut at two lines, a phone read
    // "Half-Yearly Examination · 80 marks · 1…".
    final line = tester.widget<Text>(find.byKey(const ValueKey('scope-template')));
    expect((line.maxLines, line.overflow), (null, null));
    expect(api.requests.where((r) => r.status >= 400), isEmpty, reason: '${api.requests}');
  });
}

/// The whole-syllabus check with the server's competency report in it.
class _CompetencyAdapter extends FixtureAdapter {
  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (o.method == 'POST' && o.uri.path.endsWith('/availability')) {
      return ResponseBody.fromString(jsonEncode(fixtureJson('availability_10_science_all_competency')), 200,
          headers: {Headers.contentTypeHeader: ['application/json']});
    }
    return super.fetch(o, requestStream, cancelFuture);
  }
}
