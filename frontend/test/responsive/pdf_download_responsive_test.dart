// Task 801: downloading the paper and the answer-key PDFs at phone, tablet
// and laptop widths. The builder's last step hands both PDFs for every set to
// PdfSaver (a browser download on the web); its button must be on screen and
// big enough to hit, and the "downloaded" lines it adds must not overflow.
// A paper reopened from the teacher's list downloads from the review page's
// Export card instead; that card is checked the same way.
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/download/pdf_saver.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/data/datasources/api/paper_builder_api.dart' show parsePaper;
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart' show GeneratedPaper;
import 'package:academicos/presentation/assessment/pages/assessment_review_page.dart';

import '../support/fake_server.dart';
import 'builder_driver.dart';
import 'responsive_harness.dart';

class _Saver implements PdfSaver {
  final saved = <String>[];
  @override
  Future<void> save(Uint8List bytes, String filename) async => saved.add(filename);
}

/// The captured Class 10 Science paper as the review page receives it.
(Assessment, GeneratedPaper) _reviewedPaper() {
  final paper = parsePaper(Map<String, dynamic>.from(fixtureJson('generate_10_science')['paper'] as Map));
  final now = DateTime(2026, 9, 22);
  final assessment = Assessment(
    id: paper.assessmentId,
    schoolId: 'school_1',
    teacherId: fixtureTeacherId,
    title: paper.metadata.assessmentTitle,
    subject: 'Science',
    grade: 10,
    chapterIds: const [],
    blueprint: const Blueprint(
      totalMarks: 80,
      durationMinutes: 180,
      difficulty: DifficultyDistribution(easy: 0.3, medium: 0.5, hard: 0.2),
      bloom: BloomDistribution(remember: 0.2, understand: 0.2, apply: 0.2, analyze: 0.2, evaluate: 0.1, create: 0.1),
      chapterWeights: ChapterWeights(weights: {}),
      competencyWeights: CompetencyWeights(weights: {}),
      sections: [],
    ),
    status: AssessmentStatus.paperGenerated,
    createdAt: now,
    updatedAt: now,
  );
  return (assessment, paper);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useAppFonts();
  useInMemoryHive();

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('Download paper + answer key is on screen and saves both PDFs at $name', (tester) async {
      final (_, saved) = await pumpBuilder(tester, size);
      await toChaptersStep(tester, size);
      await generate(tester, size);

      await tester.tap(builderPrimary());
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' on the download step');
      expect(find.text('Your paper is saved'), findsOneWidget);
      expect(builderPrimaryLabel(tester), 'Download paper + answer key');
      expectActionReady(tester, builderPrimary(), size, label: 'Download paper + answer key');

      await tester.tap(builderPrimary());
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' after downloading');
      // The captured paper has two sets: both PDFs for each.
      expect(saved.files.map((f) => f.$1).toList(), [
        'class_10_science_half_yearly_examination_set_a_paper.pdf',
        'class_10_science_half_yearly_examination_set_a_answer_key.pdf',
        'class_10_science_half_yearly_examination_set_b_paper.pdf',
        'class_10_science_half_yearly_examination_set_b_answer_key.pdf',
      ]);
      for (final f in saved.files) {
        expect(String.fromCharCodes(f.$2.take(5)), '%PDF-');
      }
      expect(find.text('Paper (Set A) downloaded'), findsOneWidget);
      expect(find.text('Answer key (Set B) downloaded'), findsOneWidget);
      expectActionReady(tester, builderPrimary(), size, label: 'Download again');
      // The secondary actions on this step are phone-sized too.
      for (final label in ['Open in my papers', 'Make another like this']) {
        final button = find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));
        await scrollToAndExpectReady(tester, button, size, label: label);
      }
    });

    testWidgets('a reopened paper: Export Answer Key then Download Answer Key fit and download at $name',
        (tester) async {
      final (assessment, paper) = _reviewedPaper();
      // ApiClient asks for /export/answerKey (ExportFormat.name); the server
      // takes that spelling too (assessment/routes.py export_paper). The
      // answer is the one captured for the builder's export of this paper.
      final server = FakeServer({
        'POST /papers/${paper.id}/export/answerKey': (200, fixtureJson('export_10_science_answer_key')),
        'GET /papers/${paper.id}/file': (200, '%PDF-1.4 answer key'.codeUnits),
      });
      final dio = fakeDio(server);
      final saver = _Saver();
      GetIt.I
        ..registerSingleton<ApiClient>(ApiClient(dio))
        ..registerSingleton<PillarApi>(PillarApi(dio))
        ..registerSingleton<PdfSaver>(saver);
      addTearDown(GetIt.I.reset);

      await pumpPage(tester,
          AssessmentReviewPage(assessmentId: assessment.id, assessment: assessment, paper: paper), size);
      expectNoOverflow(tester, where: ' on the review page');

      Finder button(String label) =>
          find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));
      // The Export card is below all 39 questions: a long way down on a phone.
      await tester.scrollUntilVisible(find.text('Export PDF'), 800,
          maxScrolls: 200, scrollable: find.byType(Scrollable).first);
      await scrollToAndExpectReady(tester, button('Export PDF'), size, label: 'Export PDF');
      final exportKey = button('Export Answer Key & Marking Scheme');
      await scrollToAndExpectReady(tester, exportKey, size, label: 'Export Answer Key');

      await tester.tap(exportKey);
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' after exporting the answer key');
      final download = button('Download Answer Key');
      await scrollToAndExpectReady(tester, download, size, label: 'Download Answer Key');
      await tester.tap(download);
      await tester.pumpAndSettle();
      expect(saver.saved, ['${paper.id}_answer_key.pdf']);
      expect(server.requests, ['POST /papers/${paper.id}/export/answerKey', 'GET /papers/${paper.id}/file']);
      expectNoOverflow(tester, where: ' after downloading');
    });
  }
}
