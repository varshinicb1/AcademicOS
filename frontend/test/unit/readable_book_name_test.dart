// The Lesson plans card showed a seeded book as "CBSE Class 10 Science —
// official curriculum (CBSE Curriculum 2025-26, Science_Sec_2025-26.pdf, Class X
// Course Structure)": the seed's source note, file name and all.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/presentation/shared/readable.dart';

void main() {
  test('a seeded book loses its source note', () {
    expect(bookName('CBSE Class 10 Science — official curriculum '
            '(CBSE Curriculum 2025-26, Science_Sec_2025-26.pdf, Class X Course Structure)'),
        'CBSE Class 10 Science — official curriculum');
    expect(bookName('CBSE Class 3 EVS — official curriculum (NCERT)'), 'CBSE Class 3 EVS — official curriculum');
  });

  test("a school's own book title is left as it was", () {
    expect(bookName('Science (New edition)'), 'Science (New edition)');
    expect(bookName('Lakhmir Singh Science 10'), 'Lakhmir Singh Science 10');
  });
}
