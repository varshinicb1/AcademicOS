// The principal's console shows the two numbers the product is renewed on.
//
// GET /api/v1/paper-timing and GET /api/v1/catalog have worked, been
// principal-gated and returned honest payloads for four audits, and no screen
// in the app called either. A number that exists only in an API is a number
// the person paying for the product never sees.
//
// What these pin, beyond "it renders": a zero that means "nothing measured
// yet" must not print as a measurement, and the server's own caveat about the
// declared baseline travels with the saving it qualifies.
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/presentation/admin/widgets/insights_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const _caveat = 'the baseline is DECLARED, not measured -- nothing here watches '
    'a teacher work. Treat the saving as a management estimate, not an '
    'engineering claim.';

PaperTiming _timing({int papers = 12, Map<String, dynamic> extra = const {}}) =>
    PaperTiming.fromJson({
      'papers': papers,
      'medianGenerationSeconds': 0.24,
      'baselineMinutesPerPaper': 45,
      'baselineProvenance': 'declared by the school',
      'estimatedMinutesSavedPerPaper': 44.9,
      'estimatedMinutesSavedTotal': 538.8,
      'measured': ['generationSeconds'],
      'declared': ['baselineMinutesPerPaper'],
      'caveat': _caveat,
      ...extra,
    });

/// What GET /paper-timing sends for a term: the principal's own figures for
/// the term that covers today.
Map<String, dynamic> _term({double? baseline}) => {
      'scope': 'term',
      'scopeNote': null,
      'term': {'id': 'term_1', 'name': 'Term 1', 'startDate': '2026-04-01',
               'endDate': '2026-09-30', 'manualBaselineMinutes': baseline},
      'examCoverage': {
        'covered': [{'grade': 10, 'subject': 'Science', 'papers': 12}],
        'notYet': [{'grade': 9, 'subject': 'Science'},
                   {'grade': 10, 'subject': 'Mathematics'}],
        'unattributed': 0,
        'classesDeclared': true,
      },
    };

Catalog _catalog() => Catalog.fromJson({
      'totalQuestions': 4859,
      'entries': [
        {'subject': 'Mathematics', 'grade': 6, 'questionCount': 446, 'chapters': 11,
         'marksAvailable': [1, 2, 3, 5]},
        {'subject': 'Science', 'grade': 6, 'questionCount': 247, 'chapters': 13,
         'marksAvailable': [1, 2, 3, 5]},
        {'subject': 'Hindi', 'grade': 6, 'questionCount': 0, 'chapters': 0,
         'marksAvailable': <int>[]},
      ],
    });

Future<void> _pump(WidgetTester tester, Widget card) async {
  await tester.pumpWidget(MaterialApp(home: Scaffold(body: ListView(children: [card]))));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('time saved is shown with the caveat the server sends', (tester) async {
    await _pump(tester, InsightsCard(timing: _timing(), catalog: _catalog()));
    expect(find.textContaining('45'), findsWidgets);        // the baseline
    expect(find.textContaining('12 papers'), findsOneWidget);
    expect(find.textContaining(_caveat), findsOneWidget);
  });

  testWidgets('no paper yet reads as not measured, not as zero saved', (tester) async {
    await _pump(tester, InsightsCard(timing: _timing(papers: 0), catalog: _catalog()));
    expect(find.textContaining('No paper has been generated'), findsOneWidget);
    expect(find.textContaining('0 minutes saved'), findsNothing);
    expect(find.textContaining('minutes saved per paper'), findsNothing);
  });

  testWidgets('the bank summary states the gap without being opened', (tester) async {
    // The detail is collapsed (it pushed the Coverage tab's own summary off a
    // 375 px phone), so the ONE line a principal reads unopened has to carry
    // the gap: a pair with no questions that only appears inside an expander
    // reads as "not applicable" to someone deciding whether to buy.
    await _pump(tester, InsightsCard(timing: _timing(), catalog: _catalog()));
    expect(find.textContaining('693 questions across 3 class-subject pairs'),
        findsOneWidget);
    expect(find.textContaining('1 of 3 class-subject pairs with no questions yet'),
        findsOneWidget);
  });

  testWidgets('opening the bank shows every class and subject, gaps included',
      (tester) async {
    await _pump(tester, InsightsCard(timing: _timing(), catalog: _catalog()));
    await tester.tap(find.text('Question bank'));
    await tester.pumpAndSettle();
    expect(find.textContaining('446'), findsOneWidget);
    expect(find.textContaining('Class 6 Hindi: no questions yet'), findsOneWidget);
  });

  testWidgets('a class this release does not serve is not listed', (tester) async {
    final catalog = Catalog.fromJson({
      'totalQuestions': 10,
      'entries': [
        {'subject': 'Mathematics', 'grade': 6, 'questionCount': 10, 'chapters': 1,
         'marksAvailable': [1]},
        {'subject': 'Odissi', 'grade': 12, 'questionCount': 31, 'chapters': 0,
         'marksAvailable': [2]},
      ],
    });
    await _pump(tester, InsightsCard(timing: _timing(), catalog: catalog));
    expect(find.textContaining('Odissi'), findsNothing);
  });
  // --------------------------------------------------------------- per term
  // PRD 12.6: exam coverage and time saved are "this term"; decision 11
  // compares time saved per term. Audit 2026-09-26 scored 5.1 "still
  // absent": one all-time count, no class, no subject, no term.

  testWidgets('the card names the term it reports and its dates', (tester) async {
    await _pump(tester, InsightsCard(timing: _timing(extra: _term()), catalog: _catalog()));
    expect(find.textContaining('Term 1'), findsWidgets);
    expect(find.textContaining('1 Apr 2026'), findsOneWidget);
    expect(find.textContaining('30 Sep 2026'), findsOneWidget);
  });

  testWidgets('exam coverage states unopened which classes have no paper yet',
      (tester) async {
    await _pump(tester, InsightsCard(timing: _timing(extra: _term()), catalog: _catalog()));
    expect(find.textContaining('12 papers set this term'), findsOneWidget);
    expect(find.textContaining('2 of 3 class-subject pairs have no paper yet'),
        findsOneWidget);
    await tester.tap(find.text('Exam coverage'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Class 10 Science: 12 papers'), findsOneWidget);
    expect(find.textContaining('Class 9 Science: no paper yet'), findsOneWidget);
    expect(find.textContaining('Class 10 Mathematics: no paper yet'), findsOneWidget);
  });

  testWidgets('with no classes declared it says it cannot list what is missing',
      (tester) async {
    final extra = {..._term(), 'examCoverage': {
      'covered': [{'grade': 10, 'subject': 'Science', 'papers': 12}],
      'notYet': <Map<String, dynamic>>[], 'unattributed': 0, 'classesDeclared': false}};
    await _pump(tester, InsightsCard(timing: _timing(extra: extra), catalog: _catalog()));
    expect(find.textContaining('have no paper yet'), findsNothing);
    expect(find.textContaining('Set up your classes'), findsOneWidget);
  });

  testWidgets('papers it could not match to a class are said, not hidden', (tester) async {
    final t = _term();
    final extra = {...t, 'examCoverage': {
      ...(t['examCoverage'] as Map<String, dynamic>), 'unattributed': 2}};
    await _pump(tester, InsightsCard(timing: _timing(extra: extra), catalog: _catalog()));
    expect(find.textContaining('2 papers could not be matched to a class'), findsOneWidget);
  });

  testWidgets('with no term covering today the server note is shown verbatim',
      (tester) async {
    const note = 'No term of this school covers 2026-09-27, so these figures are '
        'for all time. Declare the school’s terms in calendar setup.';
    final extra = {'scope': 'allTime', 'scopeNote': note, 'term': null,
      'examCoverage': {'covered': <Map<String, dynamic>>[], 'notYet': <Map<String, dynamic>>[],
        'unattributed': 0, 'classesDeclared': false}};
    await _pump(tester, InsightsCard(
        timing: _timing(extra: extra), catalog: _catalog(), onSetBaseline: (_) async {}));
    expect(find.textContaining(note), findsOneWidget);
    expect(find.textContaining('this term'), findsNothing);
    // No term, nothing to set a term's baseline on.
    expect(find.text("Set this term's baseline"), findsNothing);
  });

  testWidgets("the principal sets the term's baseline", (tester) async {
    double? saved = -1;
    await _pump(tester, InsightsCard(
        timing: _timing(extra: _term()), catalog: _catalog(),
        onSetBaseline: (m) async => saved = m));
    await tester.tap(find.text("Set this term's baseline"));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '0');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(find.textContaining('between 1 and 600'), findsOneWidget);
    expect(saved, -1);
    await tester.enterText(find.byType(TextField), '60');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(saved, 60);
  });

  testWidgets("a term's own baseline can be cleared", (tester) async {
    double? saved = -1;
    await _pump(tester, InsightsCard(
        timing: _timing(extra: _term(baseline: 60)), catalog: _catalog(),
        onSetBaseline: (m) async => saved = m));
    await tester.tap(find.text("Change this term's baseline"));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Use the default'));
    await tester.pumpAndSettle();
    expect(saved, isNull);
  });

  testWidgets('a baseline that fails to save says why', (tester) async {
    await _pump(tester, InsightsCard(
        timing: _timing(extra: _term()), catalog: _catalog(),
        onSetBaseline: (_) async => throw Exception('network down')));
    await tester.tap(find.text("Set this term's baseline"));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '60');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Could not save the baseline'), findsOneWidget);
  });
}
