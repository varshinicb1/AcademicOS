// The phone must label an NCERT Exemplar question as NCERT Exemplar.
//
// `QuestionSourceConverter.fromJson` maps any value it does not know to
// `ncertTextbook`, so an Exemplar record that the converter did not list would
// silently show as "NCERT Textbook". The record below is a real one from
// academicos-data/corpus/ncert-exemplar/questions.json (built by
// scripts/build_exemplar_bank.py): Exemplar class 6 maths, unit 2, question 2,
// keyed "(D)" in the book's answers file feep1an.pdf.
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/domain/entities/enums.dart';
import 'package:academicos/domain/entities/question.dart';

const _record = r'''{
  "id": "exemplar:q:6:mathematics:2:-:2",
  "questionBankId": "ncert-exemplar:class6-mathematics/feep102.pdf",
  "subject": "Mathematics",
  "grade": 6,
  "chapterIds": [],
  "competencyIds": [],
  "bloomLevel": "understand",
  "difficulty": "easy",
  "type": "mcq",
  "stem": "The number of diagonals in a septagon is",
  "stemLatex": "",
  "parts": [
    {
      "id": "exemplar:q:6:mathematics:2:-:2:p1",
      "partNumber": 1,
      "text": "",
      "textLatex": "",
      "marks": 1,
      "answerType": "singleChoice",
      "options": [
        "21",
        "42",
        "7",
        "14"
      ],
      "correctOption": "d",
      "expectedAnswer": "(D) 14",
      "alternativeAnswers": []
    }
  ],
  "answerScheme": {
    "totalMarks": 1,
    "markingPoints": [
      {
        "id": "exemplar:q:6:mathematics:2:-:2:mp1",
        "description": "(D) 14",
        "marks": 1,
        "keyword": "",
        "isRequired": true,
        "synonyms": []
      }
    ],
    "rubricLevels": [],
    "commonErrors": [],
    "alternativeAnswers": [],
    "modelAnswer": "(D) 14",
    "modelAnswerLatex": "",
    "hasPartialCredit": false,
    "metadata": {
      "answerPage": 3,
      "answerFile": "feep1an.pdf"
    },
    "provenance": "ncert_exemplar_answer",
    "sourcePaperCode": "",
    "sourceDocumentId": "feep1an.pdf"
  },
  "estimatedTimeMinutes": 2,
  "marks": 1,
  "language": "en",
  "source": "ncert_exemplar",
  "qualityScore": 0.9,
  "tags": [
    "Geometry",
    "Multiple Choice Questions"
  ],
  "createdAt": "2026-09-22T00:00:00Z",
  "updatedAt": "2026-09-22T00:00:00Z",
  "metadata": {
    "exemplarChapter": {
      "number": 2,
      "title": "Geometry",
      "exercise": null
    },
    "exemplarTextbook": "pre-2024",
    "sectionKind": "mcq_single",
    "sectionLabel": "Multiple Choice Questions",
    "questionNumber": "2",
    "optionLabels": [
      "A",
      "B",
      "C",
      "D"
    ],
    "correctOptions": [
      "d"
    ],
    "multipleCorrect": false,
    "marksBasis": "assigned_by_section_kind",
    "answerDocumentId": "ncert-exemplar:class6-mathematics/feep1an.pdf"
  },
  "diagramAssetId": null,
  "mapAssetId": null,
  "graphAssetId": null,
  "tableAssetId": null,
  "provenance": {
    "sourceDocumentId": "ncert-exemplar:class6-mathematics/feep102.pdf",
    "pageNumber": 4,
    "boundingBox": null,
    "method": "pdf_native",
    "confidence": 0.9
  },
  "rights": {
    "origin": "NCERT",
    "redistribution": "unknown",
    "basis": "",
    "attribution": "NCERT, Exemplar Problems, Class VI Mathematics"
  },
  "calibration": {
    "measured": false,
    "sampleSize": 0,
    "facility": null,
    "discrimination": null,
    "basis": "assigned"
  },
  "version": 1,
  "supersededBy": null,
  "reviewState": "published"
}''';

void main() {
  test('ncert_exemplar decodes to its own source, not ncertTextbook', () {
    const converter = QuestionSourceConverter();
    expect(converter.fromJson('ncert_exemplar'), QuestionSource.ncertExemplar);
    expect(converter.fromJson('ncert_exemplar'), isNot(QuestionSource.ncertTextbook));
    expect(converter.toJson(QuestionSource.ncertExemplar), 'ncert_exemplar');
  });

  test('a built Exemplar record decodes through Question.fromJson', () {
    final q = Question.fromJson(jsonDecode(_record) as Map<String, dynamic>);
    expect(q.source, QuestionSource.ncertExemplar);
    expect(q.parts.single.options, ['21', '42', '7', '14']);
    expect(q.parts.single.correctOption, 'd');
    expect(q.answerScheme.modelAnswer, '(D) 14');
  });
}
