// The Quick Paper used to take the first eleven search hits whatever their
// marks; generatePaper then dropped each one that fitted no section. These
// pin the replacement: every section is filled from questions of its own
// marks, and no question is placed twice.
import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:flutter_test/flutter_test.dart';

Question _q(String id, int marks) => Question.fromJson({
      'id': id, 'questionBankId': 'b', 'subject': 'Science', 'grade': 9,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'Question $id', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': {
        'totalMarks': marks, 'markingPoints': <dynamic>[], 'rubricLevels': <dynamic>[],
        'commonErrors': <String>[], 'alternativeAnswers': <String>[],
        'modelAnswer': 'a', 'modelAnswerLatex': '',
      },
      'estimatedTimeMinutes': 2, 'marks': marks, 'language': 'en',
      'source': 'cbse_question_bank', 'qualityScore': 0.8, 'tags': <String>[],
      'createdAt': '2026-09-19T00:00:00.000Z', 'updatedAt': '2026-09-19T00:00:00.000Z',
    });

SectionBlueprint _s(String id, int marks, int count) => SectionBlueprint(
      id: id, label: id, name: id, marksPerQuestion: marks, questionCount: count,
      totalMarks: marks * count, allowedBloomLevels: const [BloomLevel.understand],
      allowedDifficulties: const [Difficulty.easy]);

void main() {
  test('each section is filled from questions of its own marks', () {
    // Eleven one-markers first: take(11) would have filled only the MCQ section.
    final pool = [
      for (var i = 0; i < 11; i++) _q('one$i', 1),
      for (var i = 0; i < 3; i++) _q('two$i', 2),
      for (var i = 0; i < 3; i++) _q('three$i', 3),
    ];
    final picked = selectForSections(pool, [_s('A', 1, 5), _s('B', 2, 3), _s('C', 3, 3)]);
    expect(picked.where((q) => q.marks == 1), hasLength(5));
    expect(picked.where((q) => q.marks == 2), hasLength(3));
    expect(picked.where((q) => q.marks == 3), hasLength(3));
  });

  test('a question is never used twice', () {
    final pool = [_q('a', 1), _q('b', 1)];
    final picked = selectForSections(pool, [_s('A', 1, 2), _s('A2', 1, 2)]);
    expect(picked.map((q) => q.id).toSet(), hasLength(picked.length));
  });
}
