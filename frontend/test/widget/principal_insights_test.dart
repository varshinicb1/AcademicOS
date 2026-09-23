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

PaperTiming _timing({int papers = 12}) => PaperTiming.fromJson({
      'papers': papers,
      'medianGenerationSeconds': 0.24,
      'baselineMinutesPerPaper': 45,
      'baselineProvenance': 'declared by the school',
      'estimatedMinutesSavedPerPaper': 44.9,
      'estimatedMinutesSavedTotal': 538.8,
      'measured': ['generationSeconds'],
      'declared': ['baselineMinutesPerPaper'],
      'caveat': _caveat,
    });

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
}
