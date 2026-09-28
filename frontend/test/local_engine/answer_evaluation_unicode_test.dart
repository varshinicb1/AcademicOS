// A Hindi-medium student writes in Devanagari. The blank check used to count
// only [a-zA-Z0-9], so a Devanagari-only answer took the 'blank' path: 0 marks
// at 0.95 confidence with no review flag -- a correct answer zeroed silently.
// And the keyword tokeniser only kept [A-Za-z] runs, so even a non-blank Hindi
// answer could never match one of the 213 bundled questions whose marking
// points carry a Devanagari keyword (measured 2026-09-22). These tests use two
// real rows -- Hindi-medium CBSE board-paper questions -- pinned in
// test/fixtures/hindi_board_rows.json, because the 2026-09-28 bank serves no
// board paper in Hindi (the language returns with milestone M6).
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/answer_evaluation.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/domain/entities/question.dart';
import 'package:flutter_test/flutter_test.dart';

// Every marking point is keyword-less and its model answer is Devanagari only
// (no ASCII letter or digit) -- the row the Task 10 sweep found scored 'blank'.
const _keywordlessHindiId = 'cbse:q:src:de9d7a7a1c777974c1dd9138:13';
// Two keyed points: 'प्रबल' (2 marks) and 'दुबिल' (1 mark), total 3.
const _keyedHindiId = 'cbse:q:src:fad6500a5a65bba203f49410:28';

final _pinnedRows = [
  for (final row in (jsonDecode(File('test/fixtures/hindi_board_rows.json').readAsStringSync())
      as Map<String, dynamic>)['questions'] as List<dynamic>)
    Question.fromJson(row as Map<String, dynamic>),
];

Question _row(String id) => _pinnedRows.firstWhere((q) => q.id == id,
    orElse: () => throw StateError('$id is not in test/fixtures/hindi_board_rows.json'));

bool _hasAsciiAlnum(String s) => RegExp(r'[A-Za-z0-9]').hasMatch(s);

Map<String, dynamic> _schemeJson({List<dynamic>? markingPoints, Map<String, dynamic>? metadata}) => {
      'totalMarks': 2,
      'markingPoints': markingPoints ?? <dynamic>[],
      'rubricLevels': <dynamic>[], 'commonErrors': <String>[],
      'alternativeAnswers': <String>[],
      'modelAnswer': '', 'modelAnswerLatex': '',
      'metadata': metadata ?? <String, dynamic>{},
    };

Question _question(Map<String, dynamic> scheme) => Question.fromJson({
      'id': 'q1', 'questionBankId': 'b', 'subject': 'Science', 'grade': 7,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'stem', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': scheme, 'estimatedTimeMinutes': 2, 'marks': 2,
      'language': 'en', 'source': 'cbse_question_bank', 'qualityScore': 0.8,
      'tags': <String>[], 'createdAt': '2026-09-19T00:00:00.000Z',
      'updatedAt': '2026-09-19T00:00:00.000Z',
    });

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() => CorpusRepository.instance.ensureLoaded());

  test('a Devanagari-only answer to a real Hindi question is not blank', () {
    final q = _row(_keywordlessHindiId);
    final answer = q.answerScheme.modelAnswer;
    expect(_hasAsciiAlnum(answer), isFalse,
        reason: 'the test needs an answer with no ASCII letter or digit at all');
    final result = evaluateAnswer(q, q.answerScheme, answer);
    expect(result.verdict, isNot('blank'));
    expect(result.reasoning, isNot('No answer written for this question.'));
    // Keyword-less scheme: unscorable, so it must reach the teacher.
    expect(result.needsReview, isTrue);
    expect(result.confidence, lessThan(0.5));
  });

  test('whitespace and punctuation only (Devanagari danda included) is still blank', () {
    final q = _row(_keywordlessHindiId);
    for (final answer in ['', '   ', ' . . . ', ' । ॥ , ? - ']) {
      final result = evaluateAnswer(q, q.answerScheme, answer);
      expect(result.verdict, 'blank', reason: 'answer "$answer"');
      expect(result.needsReview, isFalse);
    }
  });

  test('a Devanagari keyword matches a Devanagari answer containing it', () {
    final q = _row(_keyedHindiId);
    final keywords = q.answerScheme.markingPoints.map((p) => p.keyword).toList();
    expect(keywords, ['प्रबल', 'दुबिल'],
        reason: 'the bundled row changed; pick another keyed Hindi row');

    const partial = 'प्रबल अम्ल जल में अधिक आयन देते हैं।';
    expect(_hasAsciiAlnum(partial), isFalse);
    final one = evaluateAnswer(q, q.answerScheme, partial);
    expect(one.markingPoints.first.awarded, isTrue);
    expect(one.markingPoints.last.awarded, isFalse);
    expect(one.awardedMarks, 2);
    expect(one.verdict, 'partialCredit');

    const full = 'प्रबल अम्ल जल में अधिक आयन देते हैं, दुबिल अम्ल कम आयन देते हैं।';
    final both = evaluateAnswer(q, q.answerScheme, full);
    expect(both.awardedMarks, 3);
    expect(both.verdict, 'fullCredit');
  });

  test('a keyword is matched as a whole Devanagari word, not a fragment', () {
    final q = _row(_keyedHindiId);
    // 'प्रबलता' contains 'प्रबल' but is a different word; the English path
    // matches whole words too ('light' does not match 'lightning').
    final result = evaluateAnswer(q, q.answerScheme, 'इस अम्ल की प्रबलता अधिक है।');
    expect(result.awardedMarks, 0);
  });

  test('a scheme with no marking points gives noCredit, never "Partial Credit" on 0 marks', () {
    final scheme = _schemeJson();
    final q = _question(scheme);
    final result = evaluateAnswer(q, q.answerScheme,
        'Because blue light is scattered more by the atmosphere.');
    expect(result.awardedMarks, 0);
    expect(result.verdict, 'noCredit');
    expect(result.needsReview, isTrue);
  });

  test('an objective question with no key gives noCredit, never "Partial Credit" on 0 marks', () {
    final scheme = _schemeJson(
      markingPoints: [
        {'id': 'mp1', 'description': 'correct option selected', 'marks': 1,
         'keyword': 'correct option selected', 'isRequired': true},
      ],
      metadata: {'objective': true},
    );
    final q = _question(scheme);
    final result = evaluateAnswer(q, q.answerScheme, '(B)');
    expect(result.awardedMarks, 0);
    expect(result.verdict, 'noCredit');
    expect(result.needsReview, isTrue);
  });
}
