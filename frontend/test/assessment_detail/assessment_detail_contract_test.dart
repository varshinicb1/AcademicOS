// The teacher's assessment detail screen reads a freshly generated paper back
// over HTTP, and it used to fail on one: "type 'Null' is not a subtype of type
// 'String'" (minified to `type 'minified:EN'` in a release web build), with
// all three of its calls answering 200.
//
// The cause was a data contract, not a server failure. `PaperMetadata` declared
// `required String schoolName`, but the backend's `school_name` is
// `Optional[str] = None` and is only filled from a teacher template's header --
// a paper generated from a CBSE preset has none. The paper builder survived the
// same body because it does not call `GeneratedPaper.fromJson` directly: its
// `parsePaper` patched `schoolName` in first. Two entry points, one model, and
// only one of them knew.
//
// So these tests replay the real bodies through BOTH entry points and require
// them to agree. The bodies are what the backend actually answered, captured by
//
//   PYTHONPATH=src PYTHONIOENCODING=utf-8 python scripts/capture_assessment_detail_fixtures.py
//
// on the flow the bug was found on: Class 10 -> Mathematics -> the "Class 10
// Mathematics - Unit Test" CBSE preset -> generate -> open in my papers. A body
// written by hand would agree with the model by construction and prove nothing.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/paper_builder_api.dart' show parsePaper;
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart';

Map<String, dynamic> _fixture(String name) => Map<String, dynamic>.from(
    jsonDecode(File('test/assessment_detail/fixtures/$name.json').readAsStringSync()) as Map);

List<dynamic> _fixtureList(String name) =>
    jsonDecode(File('test/assessment_detail/fixtures/$name.json').readAsStringSync()) as List;

void main() {
  group('GET /papers/{id} for a template-generated paper', () {
    test('the fixture still has the nulls that broke the screen', () {
      // Guards the tests below: if a later backend change starts filling these
      // in, the fixture stops covering the case it was captured for and this
      // says so instead of the suite going quietly green.
      final paper = _fixture('paper_10_maths_unit_test');
      expect(paper['setLabel'], isNull);
      expect(paper['formattedContentLatex'], '');
      expect((paper['metadata'] as Map)['schoolName'], isNull,
          reason: 'the field this whole file exists for');
      final firstQuestion = (paper['sections'] as List).first['questions'].first;
      expect(firstQuestion['internalChoiceText'], isNull);
      expect(firstQuestion['internalChoiceQuestionId'], isNull);
    });

    test('parses through the shared model, the way ApiClient.getPaper does', () {
      final paper = GeneratedPaper.fromJson(_fixture('paper_10_maths_unit_test'));

      expect(paper.metadata.schoolName, isNull,
          reason: 'null means "no template header"; the exporters fall back');
      expect(paper.setLabel, isNull);
      expect(paper.formattedContentLatex, '');
      expect(paper.sections.map((s) => s.label), ['A', 'B', 'C']);
      expect(paper.sections.expand((s) => s.questions), isNotEmpty);
      expect(paper.metadata.assessmentTitle, 'Unit Test');
      expect(paper.metadata.grade, 10);
      expect(paper.metadata.subject, 'Mathematics');
    });

    test('both entry points read it the same way', () {
      // The drift this file exists to prevent: the detail screen parses the
      // paper raw, the builder parses it through parsePaper. Same bytes, so
      // same paper -- anything either one patches has to be invisible here.
      final direct = GeneratedPaper.fromJson(_fixture('paper_10_maths_unit_test'));
      final viaBuilder = parsePaper(_fixture('paper_10_maths_unit_test'));
      // Field by field before the whole object: a paper's == failure prints
      // every question twice, which says nothing about which field moved.
      expect(direct.metadata.schoolName, viaBuilder.metadata.schoolName,
          reason: 'the field the builder used to patch in');
      expect(direct.metadata, viaBuilder.metadata);
      expect(direct, viaBuilder);
    });

    test('the same paper inside a generate-from-template response parses too', () {
      final gen = _fixture('generate_from_template_10_maths_unit_test');
      final paper = GeneratedPaper.fromJson(
          Map<String, dynamic>.from(gen['paper'] as Map));
      expect(paper.metadata.schoolName, isNull);
      expect(paper.id, isNotEmpty);
    });
  });

  group('GET /assessments for the same assessment', () {
    test('the single assessment parses with every optional field null', () {
      final json = _fixture('assessment_10_maths_unit_test');
      // The nulls the screen arrives with, kept honest the same way.
      for (final key in ['scheduledAt', 'completedAt', 'templateId',
                         'totalStudents', 'evaluatedCount']) {
        expect(json[key], isNull, reason: key);
      }
      expect(json['grade'], isA<int>());

      final assessment = Assessment.fromJson(json);
      expect(assessment.grade, 10);
      expect(assessment.subject, 'Mathematics');
      expect(assessment.scheduledAt, isNull);
      expect(assessment.completedAt, isNull);
      expect(assessment.templateId, isNull);
      expect(assessment.totalStudents, isNull);
      expect(assessment.evaluatedCount, isNull);
      // What the detail screen follows to fetch the paper.
      expect(assessment.generatedPaperId, isNotNull);
      expect(assessment.generatedPaperId, isNotEmpty);
    });

    test('the blueprint keeps the competency share the backend sent', () {
      // `competency_percentage` is a float on the wire (0.5 = half the paper).
      // Read into an `int?` it silently became 0, which is a different paper.
      final json = _fixture('assessment_10_maths_unit_test');
      expect(json['blueprint']['competencyPercentage'], 0.5);
      expect(Assessment.fromJson(json).blueprint.competencyPercentage, 0.5);
    });

    test('the school list the screen also loads parses', () {
      final list = _fixtureList('assessments_by_school');
      expect(list, isNotEmpty);
      final parsed = list
          .map((e) => Assessment.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
      expect(parsed.map((a) => a.subject), everyElement('Mathematics'));
    });
  });
}
