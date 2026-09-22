// A marking point with an empty keyword and no synonyms has nothing to match,
// so it is never awarded -- and the descriptive confidence formula
// `0.9 - 0.5 * (1 - |2 * ratio - 1|)` gives a total miss the same 0.9 as a
// full match. So every keyword-less descriptive answer used to score 0 at 0.9
// confidence with no review flag. This is not only a CBE/SQP concern: on
// 2026-09-22, 1,248 of the 2,544 descriptive board-paper questions in the
// bundled corpus had no keyword on any marking point.
//
// The synthetic scheme is built from JSON maps: AnswerScheme.toJson() leaves
// nested MarkingPoint objects rather than maps (no explicitToJson), so feeding
// it back into Question.fromJson would fail its `as Map` cast.
import 'package:academicos/core/local_engine/answer_evaluation.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/domain/entities/question.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _schemeJson() => {
      'totalMarks': 2,
      'markingPoints': [
        {'id': 'mp1', 'description': 'Scattering of sunlight by air',
         'marks': 2, 'keyword': '', 'isRequired': true},
      ],
      'rubricLevels': <dynamic>[], 'commonErrors': <String>[],
      'alternativeAnswers': <String>[],
      'modelAnswer': 'Scattering of sunlight by air', 'modelAnswerLatex': '',
    };

Question _question() => Question.fromJson({
      'id': 'q1', 'questionBankId': 'b', 'subject': 'Science', 'grade': 7,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'Why is the sky blue?', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': _schemeJson(), 'estimatedTimeMinutes': 2, 'marks': 2,
      'language': 'en', 'source': 'cbse_question_bank', 'qualityScore': 0.8,
      'tags': <String>[], 'createdAt': '2026-09-19T00:00:00.000Z',
      'updatedAt': '2026-09-19T00:00:00.000Z',
    });

bool _keywordless(AnswerScheme s) =>
    s.markingPoints.isNotEmpty &&
    s.markingPoints.every((p) =>
        p.keyword.trim().isEmpty && p.synonyms.every((x) => x.trim().isEmpty));

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('a scheme with nothing to match is sent for review, not scored 0 confidently', () {
    final scheme = AnswerScheme.fromJson(_schemeJson());
    final result = evaluateAnswer(_question(), scheme,
        'Because blue light is scattered more by the atmosphere.');
    expect(result.needsReview, isTrue);
    expect(result.confidence, lessThan(0.5));
    expect(result.awardedMarks, 0);
    expect(result.reasoning, contains('Scattering of sunlight by air'),
        reason: 'the teacher needs the official value point to mark it by hand');
  });

  test('a scheme with a real keyword is still scored, not sent for review', () {
    final json = _schemeJson();
    (json['markingPoints'] as List).first['keyword'] = 'scattering';
    final scheme = AnswerScheme.fromJson(json);
    final result = evaluateAnswer(_question(), scheme,
        'Because of scattering of blue light by the atmosphere.');
    expect(result.awardedMarks, 2);
    expect(result.verdict, 'fullCredit');
    expect(result.needsReview, isFalse);
  });

  test('every keyword-less descriptive question in the bundled corpus goes to review', () async {
    await CorpusRepository.instance.ensureLoaded();
    final unscorable = CorpusRepository.instance.all
        .where((q) =>
            q.answerScheme.metadata['objective'] != true && _keywordless(q.answerScheme))
        .toList();
    expect(unscorable, isNotEmpty,
        reason: 'the bundled corpus is expected to still carry keyword-less schemes; '
            'if the bank no longer has any, this sweep proves nothing and should be revisited');

    final confidentMisses = <String>[];
    for (final q in unscorable) {
      // A fixed, plainly non-blank English answer, so every row reaches the
      // descriptive path. (The Hindi model answers cannot be used here: the
      // Dart blank check only counts ASCII letters and digits, so a
      // Devanagari-only answer takes the 'blank' path before scoring.)
      final result = evaluateAnswer(q, q.answerScheme,
          'The student wrote a full sentence answer to this question here.');
      if (!result.needsReview || result.confidence >= 0.5) confidentMisses.add(q.id);
    }
    expect(confidentMisses, isEmpty,
        reason: '${confidentMisses.length} of ${unscorable.length} keyword-less questions '
            'were still scored confidently, e.g. ${confidentMisses.take(3)}');
  });
}
