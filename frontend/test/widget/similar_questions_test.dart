// Task 906: the server prints two hand-picked questions that look like the
// same question (POST /papers/generate, /papers/generate-from-ids) instead
// of refusing them, and names each pair on the paper it returns. Before the
// client read `warnings`/`similarPairs`, a teacher who picked twins got a
// paper with both and no word about it -- worse than the old 422. These
// tests pin the three things that close that: the model keeps the fields,
// the requests send `rejectSimilar`, and the review page shows each pair
// with "Keep both" / "Swap one".
//
// The review page talks to a real (offline) LocalApiClient for everything
// except the one call under test: the on-device engine has no swap (it
// refuses by name, see LocalApiClient.swapPaperQuestion), so a subclass
// records the swap the page asks for and answers it with the paper the
// server would return -- the only stand-in in this file.
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/core/local_engine/local_pillar_api.dart' show OfflineUnsupportedException;
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/domain/repositories/requests.dart';
import 'package:academicos/presentation/assessment/pages/assessment_review_page.dart';

import '../support/real_di.dart';

class _SwapRecordingApiClient extends LocalApiClient {
  final List<(String, String)> swaps = [];
  GeneratedPaper Function(String paperId, String slot)? answer;

  @override
  Future<GeneratedPaper> swapPaperQuestion(String paperId, String slot) async {
    swaps.add((paperId, slot));
    final a = answer;
    if (a == null) throw Exception('409: no alternative in this scope for question $slot');
    return a(paperId, slot);
  }
}

GeneratedQuestion _q(String id, int n, String stem) => GeneratedQuestion(
      questionId: id,
      displayNumber: n,
      stem: stem,
      stemLatex: '',
      parts: const [],
      marks: 2,
      bloomLevel: 'apply',
      difficulty: 'medium',
      type: 'shortAnswer',
    );

const _twinA = 'cbse:q:src:f319c93abeb1185b0864d200:9';
const _twinB = 'cbse:q:src:b23bc2e537566a04afbf4415:15';
const _warning = 'questions $_twinA and $_twinB look like the same question -- keep both, or swap one';

GeneratedPaper _paper(String assessmentId, List<GeneratedQuestion> qs,
        {List<String> warnings = const [], List<List<String>> pairs = const []}) =>
    GeneratedPaper(
      id: 'paper_twins',
      assessmentId: assessmentId,
      sections: [
        GeneratedSection(sectionId: 's1', label: 'A', name: 'Short Answer', questions: qs, totalMarks: 2 * qs.length),
      ],
      formattedContent: '',
      formattedContentLatex: '',
      answerKey: const {},
      metadata: PaperMetadata(
        assessmentTitle: 'Quadratics check',
        schoolName: 'Test School',
        subject: 'Mathematics',
        grade: 10,
        totalMarks: 2 * qs.length,
        durationMinutes: 30,
        generatedAt: DateTime(2026, 9, 22),
        generatedBy: 'AcademicOS',
        version: '1.0',
      ),
      warnings: warnings,
      similarPairs: pairs,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('the model carries the server fields', () {
    test('GeneratedPaper reads warnings and similarPairs, and defaults them empty', () {
      // The shape POST /papers/generate-from-ids sends (camelCase keys).
      Map<String, dynamic> wire({bool withPairs = true}) => {
            'id': 'paper_twins',
            'assessmentId': 'asm',
            'sections': [
              {
                'sectionId': 's1', 'label': 'A', 'name': 'Short Answer', 'totalMarks': 4,
                'questions': [
                  for (final (i, id) in [_twinA, _twinB].indexed)
                    {
                      'questionId': id, 'displayNumber': i + 1, 'stem': 'x', 'stemLatex': '',
                      'parts': [], 'marks': 2, 'bloomLevel': 'apply', 'difficulty': 'medium',
                      'type': 'shortAnswer',
                    },
                ],
              },
            ],
            'formattedContent': '',
            'formattedContentLatex': '',
            'answerKey': {},
            'metadata': {
              'assessmentTitle': 't', 'schoolName': 's', 'subject': 'Mathematics', 'grade': 10,
              'totalMarks': 4, 'durationMinutes': 30, 'generatedAt': '2026-09-22T00:00:00',
              'generatedBy': 'AcademicOS', 'version': '1.0',
            },
            if (withPairs) 'warnings': [_warning],
            if (withPairs) 'similarPairs': [[_twinA, _twinB]],
          };
      // Through jsonEncode/jsonDecode, so the maps are typed as Dio hands them over.
      GeneratedPaper parse(Map<String, dynamic> j) =>
          GeneratedPaper.fromJson(jsonDecode(jsonEncode(j)) as Map<String, dynamic>);
      final paper = parse(wire());
      expect(paper.warnings, [_warning]);
      expect(paper.similarPairs, [[_twinA, _twinB]]);
      final old = parse(wire(withPairs: false));
      expect(old.warnings, isEmpty, reason: 'a paper read back later (or an older server) has neither field');
      expect(old.similarPairs, isEmpty);
    });

    test('both hand-picked requests send rejectSimilar, false unless asked', () {
      const ids = GenerateFromIdsRequest(questionIds: [_twinA, _twinB], subject: 'Mathematics');
      expect(ids.toJson()['rejectSimilar'], isFalse);
      expect(ids.copyWith(rejectSimilar: true).toJson()['rejectSimilar'], isTrue);
    });

    test('the offline client refuses a swap by name instead of a bare connection error', () async {
      await expectLater(LocalApiClient().swapPaperQuestion('p', '2'),
          throwsA(isA<OfflineUnsupportedException>()));
    });
  });

  group('the review page shows each similar pair', () {
    late RealTestEnv env;
    late String assessmentId;
    late _SwapRecordingApiClient api;

    setUpAll(() async {
      env = await RealTestEnv.init('similar_questions_test_');
      api = _SwapRecordingApiClient();
      GetIt.I.registerSingleton<ApiClient>(api);
      env.registerGetIt();
      await DemoSeeder.seedIfEmpty();
      assessmentId = LocalStore.instance.allAssessments().first['id'] as String;
    });

    tearDownAll(() async {
      await env.dispose();
    });

    setUp(() {
      api.swaps.clear();
      api.answer = null;
    });

    List<GeneratedQuestion> twins() => [
          _q(_twinA, 1, 'If 3/2 is a root of kx^2 - x - 2 = 0, find k.'),
          _q(_twinB, 2, 'If 3/2 is a root of kx^2 - x - 2 = 0, find the value of k.'),
          _q('o0', 3, 'Find the discriminant of 2x^2 - 4x + 3 = 0.'),
        ];

    Future<void> pumpPage(WidgetTester tester, GeneratedPaper paper) async {
      await tester.pumpWidget(wrapForTest(
        AssessmentReviewPage(assessmentId: assessmentId, paper: paper),
        bloc: env.buildAssessmentBloc(),
      ));
      await tester.pumpAndSettle();
    }

    testWidgets('a pair is named by question number, with Keep both and Swap one', (tester) async {
      await pumpPage(tester, _paper(assessmentId, twins(), warnings: [_warning], pairs: [[_twinA, _twinB]]));
      expect(find.text('Similar questions'), findsOneWidget);
      expect(find.textContaining('Questions 1 and 2 look like the same question'), findsOneWidget);
      expect(find.text(_warning), findsOneWidget);
      expect(find.text('Keep both'), findsOneWidget);
      expect(find.text('Swap one'), findsOneWidget);
    });

    testWidgets('Keep both hides the pair and changes nothing on the paper', (tester) async {
      await pumpPage(tester, _paper(assessmentId, twins(), warnings: [_warning], pairs: [[_twinA, _twinB]]));
      await tester.tap(find.text('Keep both'));
      await tester.pumpAndSettle();
      expect(find.text('Similar questions'), findsNothing);
      expect(api.swaps, isEmpty);
      expect(find.text('If 3/2 is a root of kx^2 - x - 2 = 0, find the value of k.'), findsOneWidget);
    });

    testWidgets('Swap one asks the server to swap the later question and shows the new paper', (tester) async {
      final original = _paper(assessmentId, twins(), warnings: [_warning], pairs: [[_twinA, _twinB]]);
      api.answer = (paperId, slot) {
        final qs = twins();
        qs[1] = _q('cbse:q:new', 2, 'Solve x^2 - 5x + 6 = 0 by factorisation.');
        // The swap route returns the stored paper, which carries no pairs.
        return _paper(assessmentId, qs);
      };
      await pumpPage(tester, original);
      await tester.tap(find.text('Swap one'));
      await tester.pumpAndSettle();
      expect(api.swaps, [('paper_twins', '2')]);
      expect(find.text('Similar questions'), findsNothing);
      expect(find.text('Solve x^2 - 5x + 6 = 0 by factorisation.'), findsOneWidget);
      expect(find.text('If 3/2 is a root of kx^2 - x - 2 = 0, find the value of k.'), findsNothing);
    });

    testWidgets('an OR alternative is swapped by its _OR slot', (tester) async {
      final qs = [
        _q(_twinA, 1, 'If 3/2 is a root of kx^2 - x - 2 = 0, find k.')
            .copyWith(internalChoiceQuestionId: _twinB, internalChoiceText: 'If 3/2 is a root of kx^2 - x - 2 = 0, find the value of k.'),
        _q('o0', 2, 'Find the discriminant of 2x^2 - 4x + 3 = 0.'),
      ];
      await pumpPage(tester, _paper(assessmentId, qs, warnings: [_warning], pairs: [[_twinA, _twinB]]));
      expect(find.textContaining('Questions 1 and 1 (OR) look like the same question'), findsOneWidget);
      await tester.tap(find.text('Swap one'));
      await tester.pumpAndSettle();
      expect(api.swaps, [('paper_twins', '1_OR')]);
    });

    testWidgets('a failed swap says why and keeps the pair on screen', (tester) async {
      await pumpPage(tester, _paper(assessmentId, twins(), warnings: [_warning], pairs: [[_twinA, _twinB]]));
      await tester.tap(find.text('Swap one'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Could not swap question 2'), findsOneWidget);
      expect(find.text('Similar questions'), findsOneWidget);
    });

    testWidgets('a paper with no similar pairs shows no card', (tester) async {
      await pumpPage(tester, _paper(assessmentId, twins()));
      expect(find.text('Similar questions'), findsNothing);
    });
  });
}
