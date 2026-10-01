// The paper screens' counts and names (QA pass of 2026-10-01): "1 marks",
// "1 chapters", "Section A · Section A - Objective" (P-33), and a downloaded
// paper named `paper_fafce43ab953.docx` (P-24).
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/constants/wording.dart';
import 'package:academicos/core/download/paper_download.dart';

void main() {
  test('counts read as words', () {
    expect(marksText(1), '1 mark');
    expect(marksText(79), '79 marks');
    expect(questionsText(1), '1 question');
    expect(counted(1, 'chapter'), '1 chapter');
    expect(counted(5, 'chapter'), '5 chapters');
    expect(counted(2, 'child', 'children'), '2 children');
  });

  test("a section's heading names its letter once", () {
    expect(sectionHeading('A', 'Section A - Objective'), 'Section A - Objective');
    expect(sectionHeading('B', 'Short answer'), 'Section B · Short answer');
    expect(sectionHeading('C', 'Long answer', separator: ' — '), 'Section C — Long answer');
  });

  test('a downloaded paper is named for its class, subject, title and set', () {
    expect(paperFileName(title: 'Half-Yearly Examination', grade: 10, subject: 'Mathematics', set: 'B'),
        'class_10_mathematics_half_yearly_examination_set_b_paper.pdf');
    expect(paperFileName(title: 'Class 10 Science - Annual Examination', grade: 10, subject: 'Science',
            kind: 'answer_key'),
        'class_10_science_annual_examination_answer_key.pdf', reason: 'the class is not said twice');
    expect(paperFileName(title: 'Unit Test', grade: 6, subject: 'Science', extension: 'docx'),
        'class_6_science_unit_test_paper.docx');
  });
}
