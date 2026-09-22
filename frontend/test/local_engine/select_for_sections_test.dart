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

  test("pickForSections keeps each section's picks apart, so a short one is visible", () {
    // Two sections of the same marks: counting a flat list by marks could not
    // tell which of them came out short.
    final pool = [_q('a', 1), _q('b', 1), _q('c', 1)];
    final picks = pickForSections(pool, [_s('A', 1, 2), _s('A2', 1, 2)]);
    expect(picks.map((p) => p.length), [2, 1]);
  });

  test('the shortfall message names every short section', () {
    final e = InsufficientQuestionsException('English', 10, const [
      SectionShortfall(sectionId: 'B', marksPerQuestion: 2, wanted: 3, found: 0),
      SectionShortfall(sectionId: 'C', marksPerQuestion: 3, wanted: 3, found: 1),
    ]);
    expect(e.toString(), contains('Only 0 of 3 two-mark questions for English class 10'));
    expect(e.toString(), contains('Only 1 of 3 three-mark questions for English class 10'));
  });

  // The dialog sends 25, 40, 50 or 80 (assessment_list_page.dart), and
  // QuickPaperRequest defaults to 80. Fixed 5+6+9 = 20-mark sections printed
  // every one of them over 20 marks of questions.
  for (final total in const [20, 25, 40, 50, 80]) {
    test('the $total-mark Quick Paper sections add up to $total', () {
      final sections = quickPaperSections(total);
      expect(sections.fold<int>(0, (s, x) => s + x.marksPerQuestion * x.questionCount), total);
      for (final x in sections) {
        expect(x.totalMarks, x.marksPerQuestion * x.questionCount, reason: 'section ${x.id}');
        expect(x.questionCount, greaterThan(0), reason: 'section ${x.id}');
      }
    });
  }

  test('20 marks keeps the original 5 + 3 + 3 layout', () {
    expect(quickPaperSections(20).map((s) => s.questionCount), [5, 3, 3]);
  });

  test('a total too small for every section still adds up', () {
    for (var total = 1; total < 20; total++) {
      final sections = quickPaperSections(total);
      expect(sections.fold<int>(0, (s, x) => s + x.totalMarks), total, reason: '$total marks');
    }
  });
}
