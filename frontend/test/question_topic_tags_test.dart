// A question's taxonomy tags (scripts/tag_question_bank.py --topics) must
// decode on the phone, and a record without them -- every bank the tagger has
// not run over -- must decode exactly as before. `Question.fromJson` throws on
// a missing required field, so the tag fields are optional with empty
// defaults, never required.
//
// The record is a real one from academicos-data/corpus/ncert-exemplar/
// questions.json: exemplar:q:10:mathematics:5:5.1:16, with the tags the
// tagger wrote onto it.
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/domain/entities/question.dart';

const _untagged = r'''{
  "id": "exemplar:q:10:mathematics:5:5.1:16",
  "questionBankId": "ncert-exemplar:class10-mathematics/jeep205.pdf",
  "subject": "Mathematics",
  "grade": 10,
  "chapterIds": [],
  "competencyIds": [],
  "bloomLevel": "understand",
  "difficulty": "easy",
  "type": "mcq",
  "stem": "The sum of first 16 terms of the AP: 10, 6, 2,... is",
  "stemLatex": "",
  "parts": [],
  "answerScheme": {
    "totalMarks": 1,
    "markingPoints": [],
    "rubricLevels": [],
    "commonErrors": [],
    "alternativeAnswers": [],
    "modelAnswer": "(A) –320",
    "modelAnswerLatex": "",
    "hasPartialCredit": false
  },
  "estimatedTimeMinutes": 2,
  "marks": 1,
  "language": "en",
  "source": "ncert_exemplar",
  "qualityScore": 0.9,
  "tags": [],
  "createdAt": "2026-09-22T00:00:00Z",
  "updatedAt": "2026-09-22T00:00:00Z"
}''';

Map<String, dynamic> _json() => jsonDecode(_untagged) as Map<String, dynamic>;

void main() {
  test('a record without tag fields decodes with empty tags', () {
    final q = Question.fromJson(_json());
    expect(q.taxonomyChapterId, isNull);
    expect(q.topicIds, isEmpty);
    expect(q.subtopicIds, isEmpty);
    expect(q.tagConfidence, isEmpty);
    expect(q.tagMethod, isNull);
  });

  test('a tagged record decodes its chapter, topic and confidence', () {
    final json = _json()
      ..['taxonomyChapterId'] = 'mathematics-10/arithmetic-progressions'
      ..['topicIds'] = ['mathematics-10/arithmetic-progressions/sum-of-first-n-terms-of-an-ap']
      ..['subtopicIds'] = <String>[]
      ..['tagConfidence'] = {'chapter': 0.9294, 'topic': 0.9082, 'subtopic': null}
      ..['tagMethod'] = 'tfidf_textbook_v1';
    final q = Question.fromJson(jsonDecode(jsonEncode(json)) as Map<String, dynamic>);
    expect(q.taxonomyChapterId, 'mathematics-10/arithmetic-progressions');
    expect(q.topicIds, ['mathematics-10/arithmetic-progressions/sum-of-first-n-terms-of-an-ap']);
    expect(q.subtopicIds, isEmpty);
    expect(q.tagConfidence['chapter'], 0.9294);
    expect(q.tagConfidence['subtopic'], isNull);
    expect(q.tagMethod, 'tfidf_textbook_v1');
  });
}
