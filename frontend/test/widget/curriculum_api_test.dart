// Plain JSON-parsing tests for curriculum_api.dart's TopicWithSubtopics/
// SubtopicSummary -- the models assessment_create_page.dart's subtopic
// picker (see §21's subtopicIds filter) reads. No Dio mocking library is
// available in this project (mocktail was explicitly removed -- see
// pubspec.yaml's own comment -- for a freezed conflict), so this verifies
// the real parsing logic directly against the real backend response shape
// (`TopicWithSubtopicsResponse`/`SubtopicResponse` in
// src/academicos/curriculum/schemas.py) rather than a network round trip.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';

void main() {
  group('SubtopicSummary.fromJson', () {
    test('parses id and name', () {
      final s = SubtopicSummary.fromJson({'id': 'st_1', 'name': 'Balancing equations'});
      expect(s.id, 'st_1');
      expect(s.name, 'Balancing equations');
    });
  });

  group('TopicWithSubtopics.fromJson', () {
    test('parses a topic with real nested subtopics, matching the backend '
        'shape (TopicResponse fields + a subtopics list)', () {
      final t = TopicWithSubtopics.fromJson({
        'id': 't_1',
        'canonicalId': 'cbse:10:science:chemical-reactions:chemical-equations',
        'chapterId': 'chemical-reactions-and-equations',
        'name': 'Chemical Equations',
        'seq': 0,
        'sourceType': 'llm_proposed',
        'subtopics': [
          {'id': 'st_1', 'name': 'Writing chemical equations'},
          {'id': 'st_2', 'name': 'Balancing chemical equations'},
        ],
      });
      expect(t.id, 't_1');
      expect(t.name, 'Chemical Equations');
      expect(t.subtopics, hasLength(2));
      expect(t.subtopics.map((s) => s.name), containsAll(['Writing chemical equations', 'Balancing chemical equations']));
    });

    test('a topic with no approved subtopics yet parses to an empty list, not a crash', () {
      final t = TopicWithSubtopics.fromJson({
        'id': 't_2', 'canonicalId': 'x', 'chapterId': 'y', 'name': 'Topic with nothing approved',
        'seq': 0, 'sourceType': 'manual',
      });
      expect(t.subtopics, isEmpty);
    });
  });
}
