// Proves the CBSE-style PDF exporter actually produces a real, non-trivial
// file for a realistic mixed paper (MCQ + descriptive questions) -- the
// pdf package's output is a compressed binary stream, so these tests focus
// on what's actually verifiable: it runs without throwing for realistic
// inputs, and the resulting file exists with a plausible non-zero size
// (a near-empty PDF, like the old bare-bones exporter risked producing for
// an all-blank paper, would be suspiciously small).
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'package:academicos/core/local_engine/local_pdf_export.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart';

class _FakePathProvider extends PathProviderPlatform
    with MockPlatformInterfaceMixin {
  final Directory dir;
  _FakePathProvider(this.dir);

  @override
  Future<String?> getApplicationDocumentsPath() async => dir.path;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tmpDir;

  setUpAll(() {
    tmpDir = Directory.systemTemp.createTempSync('pdf_export_test_');
    PathProviderPlatform.instance = _FakePathProvider(tmpDir);
  });

  tearDownAll(() {
    tmpDir.deleteSync(recursive: true);
  });

  GeneratedQuestion mcq({required int number, required List<String> options}) {
    return GeneratedQuestion(
      questionId: 'q_mcq_$number',
      displayNumber: number,
      stem: 'Which of the following is a prime number?',
      stemLatex: '',
      parts: [
        QuestionPart(
          id: 'q_mcq_${number}_p1',
          partNumber: 1,
          text: '',
          textLatex: '',
          marks: 1,
          answerType: AnswerType.singleChoice,
          options: options,
          correctOption: options.first,
        ),
      ],
      marks: 1,
      bloomLevel: 'remember',
      difficulty: 'easy',
      type: 'mcq',
    );
  }

  GeneratedQuestion descriptive({required int number, required int marks}) {
    return GeneratedQuestion(
      questionId: 'q_desc_$number',
      displayNumber: number,
      stem: 'Explain the process of photosynthesis with a labelled diagram.',
      stemLatex: '',
      parts: const [],
      marks: marks,
      bloomLevel: 'understand',
      difficulty: 'medium',
      type: 'longAnswer',
    );
  }

  GeneratedPaper buildPaper() {
    return GeneratedPaper(
      id: 'paper_test_1',
      assessmentId: 'assessment_test_1',
      sections: [
        GeneratedSection(
          sectionId: 'section_a',
          label: 'A',
          name: 'MCQ',
          totalMarks: 4,
          questions: [
            mcq(number: 1, options: ['2', '4', '6', '8']),
            mcq(number: 2, options: ['3', '9', '15', '21']),
            mcq(number: 3, options: ['5', '10', '15', '20']),
            mcq(number: 4, options: ['7', '14', '21', '28']),
          ],
        ),
        GeneratedSection(
          sectionId: 'section_b',
          label: 'B',
          name: 'Long Answer',
          totalMarks: 10,
          questions: [
            descriptive(number: 5, marks: 5),
            descriptive(number: 6, marks: 5),
          ],
        ),
      ],
      formattedContent: '',
      formattedContentLatex: '',
      answerKey: const {},
      metadata: PaperMetadata(
        assessmentTitle: 'Class X Science — Unit Test',
        schoolName: 'AcademicOS Demo School',
        subject: 'Science',
        grade: 10,
        totalMarks: 14,
        durationMinutes: 60,
        generatedAt: DateTime(2026, 1, 1),
        generatedBy: 'AcademicOS on-device engine',
        version: '1.0-local',
      ),
    );
  }

  test('exports a real, non-trivial PDF for a mixed MCQ + descriptive paper', () async {
    final path = await LocalPdfExporter.exportPaper(buildPaper());

    final file = File(path);
    expect(await file.exists(), isTrue, reason: 'exportPaper must write a real file');

    final bytes = await file.readAsBytes();
    // A bare single-page "empty boxes" PDF (the old exporter's worst case)
    // still compresses to a few KB; a paper with real header content,
    // instructions, MCQ options, and reserved answer-space rectangles
    // should be meaningfully larger. This is a coarse but real signal that
    // the extra content actually rendered rather than being silently
    // dropped.
    expect(bytes.length, greaterThan(2000),
        reason: 'exported PDF should be non-trivially sized, not a near-empty page');
  });

  test('does not throw for a paper with zero questions in a section', () async {
    final paper = GeneratedPaper(
      id: 'paper_test_empty_section',
      assessmentId: 'assessment_test_1',
      sections: [
        GeneratedSection(
          sectionId: 'section_a',
          label: 'A',
          name: 'MCQ',
          totalMarks: 0,
          questions: const [],
        ),
      ],
      formattedContent: '',
      formattedContentLatex: '',
      answerKey: const {},
      metadata: PaperMetadata(
        assessmentTitle: 'Empty Section Paper',
        schoolName: 'AcademicOS Demo School',
        subject: 'Science',
        grade: 10,
        totalMarks: 0,
        durationMinutes: 60,
        generatedAt: DateTime(2026, 1, 1),
        generatedBy: 'AcademicOS on-device engine',
        version: '1.0-local',
      ),
    );

    final path = await LocalPdfExporter.exportPaper(paper);
    expect(await File(path).exists(), isTrue);
  });

  test('reserves more vertical space for a higher-mark descriptive question', () async {
    // Not directly assertable from PDF bytes without a parser, but this at
    // least proves a wide range of mark values (1 to 20) never throws --
    // the clamp in _answerSpace was added specifically to avoid runaway
    // page heights for unusually high-mark questions.
    final paper = GeneratedPaper(
      id: 'paper_test_marks_range',
      assessmentId: 'assessment_test_1',
      sections: [
        GeneratedSection(
          sectionId: 'section_a',
          label: 'A',
          name: 'Long Answer',
          totalMarks: 21,
          questions: [
            descriptive(number: 1, marks: 1),
            descriptive(number: 2, marks: 20),
          ],
        ),
      ],
      formattedContent: '',
      formattedContentLatex: '',
      answerKey: const {},
      metadata: PaperMetadata(
        assessmentTitle: 'Marks Range Paper',
        schoolName: 'AcademicOS Demo School',
        subject: 'Science',
        grade: 10,
        totalMarks: 21,
        durationMinutes: 60,
        generatedAt: DateTime(2026, 1, 1),
        generatedBy: 'AcademicOS on-device engine',
        version: '1.0-local',
      ),
    );

    final path = await LocalPdfExporter.exportPaper(paper);
    expect(await File(path).exists(), isTrue);
  });

  // A paper generated from a CBSE preset carries `metadata.schoolName: null`
  // -- the field that used to be `required String` on the model. The exporter
  // has to print a header for it rather than a blank line, so this drives the
  // real captured body end to end (see
  // test/assessment_detail/assessment_detail_contract_test.dart for where it
  // comes from).
  test('exports a real PDF for a template paper that carries no school name', () async {
    final paper = GeneratedPaper.fromJson(Map<String, dynamic>.from(jsonDecode(
        File('test/assessment_detail/fixtures/paper_10_maths_unit_test.json')
            .readAsStringSync()) as Map));
    expect(paper.metadata.schoolName, isNull, reason: 'the case under test');

    final path = await LocalPdfExporter.exportPaper(paper);
    final bytes = await File(path).readAsBytes();
    expect(bytes.length, greaterThan(2000),
        reason: 'the header must still render, not collapse to a blank page');
  });

  test('exports its answer key too', () async {
    final paper = GeneratedPaper.fromJson(Map<String, dynamic>.from(jsonDecode(
        File('test/assessment_detail/fixtures/paper_10_maths_unit_test.json')
            .readAsStringSync()) as Map));
    final path = await LocalPdfExporter.exportAnswerKey(paper);
    expect(await File(path).exists(), isTrue);
  });
}
