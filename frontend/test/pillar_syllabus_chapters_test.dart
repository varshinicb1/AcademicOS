// The offline client and the server must agree about where chapters live.
//
// GET /syllabus/{subject}/{grade} gained a top-level `chapters` list for the
// classes whose CBSE units are marks weightage and own no chapters (the eight
// files fb0107a rewrote). Nothing in CI compares LocalPillarApi's shape with
// the server's, so this test is the detection: it decodes a server-shaped body
// and asserts the client reads both places.
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('a syllabus names chapters the units do not own', () {
    final s = Syllabus.fromJson({
      'subject': 'Mathematics',
      'grade': 6,
      'totalMarks': 80,
      'source': 'Ganita Prakash (NCF-SE)',
      'units': [
        {'unitNo': 'I', 'name': 'Number Sense and Patterns', 'marks': 15, 'chapterNames': []},
      ],
      'chapters': [
        {'id': 'mathematics-6/number-play', 'name': 'Number Play'},
        {'id': 'mathematics-6/lines-and-angles', 'name': 'Lines and Angles'},
      ],
    });
    expect(s.units.single.chapterNames, isEmpty);
    expect(s.chapters.map((c) => c.id), contains('mathematics-6/number-play'));
    expect(s.chapterNames, ['Number Play', 'Lines and Angles']);
  });

  test('a class whose units own their chapters still reads them', () {
    final s = Syllabus.fromJson({
      'subject': 'Science',
      'grade': 10,
      'totalMarks': 80,
      'source': 'CBSE',
      'units': [
        {'unitNo': 'I', 'name': 'Chemical Substances', 'marks': 25,
         'chapterNames': ['Chemical Reactions and Equations']},
      ],
    });
    expect(s.chapters, isEmpty);
    expect(s.chapterNames, ['Chemical Reactions and Equations']);
  });
}
