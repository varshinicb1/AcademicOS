// Real widget-level UI test guarding the single highest-severity bug found
// this session: AssessmentReviewPage's _exportPdf()/_openDelivery() used to
// read widget.paper/widget.assessment directly, which are null on every
// navigation path except the just-generated flow -- every OTHER path
// (reopening from the assessment list, from Today, after a reload) relies
// on _reopen() populating _fetchedAssessment/_fetchedPaper instead. build()
// already resolved via `?? _fetched...`, so the page LOOKED fine, but the
// Export/Deliver buttons silently no-op'd on every reopened assessment.
// This test reproduces exactly that "reopened" shape (assessment: null,
// paper: null, only assessmentId set -- the shape every real navigation
// path except assessment-creation actually uses) against a real,
// demo-seeded assessment, through a real AssessmentBloc wired to a real
// (offline) ApiClient -- no mocks, so a regression of this exact bug fails
// this test the same way it silently failed for a real teacher on-device.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/domain/repositories/requests.dart';
import 'package:academicos/presentation/assessment/pages/assessment_review_page.dart';

import '../support/real_di.dart';

/// A real assessment's question list is long (16 real CBSE questions with
/// full stems) -- the "Export & Approve" card sits well below the default
/// test viewport (800x600), and ListView only builds children near the
/// current viewport. Without this, `find.text('Export PDF')` finds nothing
/// not because the button is broken, but because it was never built at all
/// -- confirmed by dumping every real Text widget actually in the tree after
/// pumpAndSettle() and seeing the list cut off mid-questions. Real fix:
/// actually scroll the list until the target exists, the same way a real
/// teacher would.
Future<void> _scrollUntilVisible(WidgetTester tester, Finder finder) async {
  for (var i = 0; i < 30; i++) {
    if (finder.evaluate().isNotEmpty) break;
    await tester.drag(find.byType(ListView), const Offset(0, -300));
    await tester.pump();
  }
  if (finder.evaluate().isEmpty) {
    throw StateError('$finder never became visible after scrolling');
  }
  // Being IN the tree isn't the same as being fully within the hittable
  // viewport (it can be built but still clipped at the very edge, which is
  // exactly what happened here -- the tap missed with a "hit test warning").
  // ensureVisible nudges it fully into view now that it actually exists.
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;
  late String realAssessmentId;

  setUpAll(() async {
    env = await RealTestEnv.init('assessment_review_test_');
    env.registerGetIt();
    await DemoSeeder.seedIfEmpty();
    // Any seeded assessment with a real generated paper works -- pick the
    // first, matching how a teacher would reopen it from the assessment list.
    realAssessmentId = LocalStore.instance.allAssessments().first['id'] as String;
  });

  tearDownAll(() async {
    await env.dispose();
  });

  testWidgets(
    'a reopened assessment (paper/assessment both null, matching every real navigation path) '
    'renders its real content after _reopen() resolves',
    (tester) async {
      final bloc = env.buildAssessmentBloc();
      await tester.pumpWidget(wrapForTest(
        AssessmentReviewPage(assessmentId: realAssessmentId),
        bloc: bloc,
      ));

      // First frame: _reopen() is in flight, spinner shown, not the real bug
      // scenario yet -- the regression only shows once real data has loaded.
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      await tester.pumpAndSettle();

      expect(find.byType(CircularProgressIndicator), findsNothing,
          reason: '_reopen() must have completed and resolved real data');
      expect(find.text('This assessment could not be opened.'), findsNothing);

      await _scrollUntilVisible(tester, find.text('Export PDF'));
      expect(find.text('Export PDF'), findsOneWidget,
          reason: 'the real Export & Approve card must render once _fetchedPaper is populated');
    },
  );

  testWidgets(
    'tapping Export PDF on a reopened assessment actually exports -- the exact regression this test exists for',
    (tester) async {
      final bloc = env.buildAssessmentBloc();
      await tester.pumpWidget(wrapForTest(
        AssessmentReviewPage(assessmentId: realAssessmentId),
        bloc: bloc,
      ));
      await tester.pumpAndSettle();

      expect(find.text('Preview, print or email'), findsNothing,
          reason: 'must not appear before a real export has happened');

      await _scrollUntilVisible(tester, find.text('Export PDF'));
      await tester.tap(find.text('Export PDF'));
      await tester.pump();
      expect(find.text('Exporting…'), findsOneWidget,
          reason: 'the bloc dispatch must actually start a real export, not silently no-op');

      // Same real-I/O-inside-fake-async-zone issue as DemoSeeder: the real
      // export renders an actual PDF (LocalPdfExporter -> package:pdf, real
      // font/glyph work), which pumpAndSettle's fake clock never lets
      // resolve. runAsync steps outside that zone so the real Future can
      // actually complete; confirmed necessary -- pumpAndSettle alone timed
      // out here every time before this fix.
      await tester.runAsync(() async {
        for (var i = 0; i < 100; i++) {
          if (find.text('Preview, print or email').evaluate().isNotEmpty) return;
          await Future<void>.delayed(const Duration(milliseconds: 50));
          await tester.pump();
        }
      });

      expect(find.text('This assessment could not be opened.'), findsNothing);
      expect(find.text('Preview, print or email'), findsOneWidget,
          reason: 'a real PDF must have been exported and _exportedUrl set -- '
              'this is the exact button that silently never appeared before the fix');
    },
  );

  testWidgets(
    'Export Answer Key & Marking Scheme button is rendered and tappable',
    (tester) async {
      final bloc = env.buildAssessmentBloc();
      await tester.pumpWidget(wrapForTest(
        AssessmentReviewPage(assessmentId: realAssessmentId),
        bloc: bloc,
      ));
      await tester.pumpAndSettle();

      await _scrollUntilVisible(tester, find.text('Export Answer Key & Marking Scheme'));
      expect(find.text('Export Answer Key & Marking Scheme'), findsOneWidget);
    },
  );

  testWidgets(
    'parallel sets switcher renders and internal choice OR block displays',
    (tester) async {
      final bloc = env.buildAssessmentBloc();
      final setAPaper = LocalStore.instance.getPaper(
        LocalStore.instance.allAssessments().first['generatedPaperId'] as String,
      );
      expect(setAPaper, isNotNull);

      // Create a test paper with internal choice and parallel sets
      const testQ1 = GeneratedQuestion(
        questionId: 'q1',
        displayNumber: 1,
        stem: 'Define photosynthesis in green plants.',
        stemLatex: '',
        parts: const [],
        marks: 3,
        bloomLevel: 'understand',
        difficulty: 'medium',
        type: 'shortAnswer',
        internalChoiceText: 'Explain the light-dependent reaction step by step.',
        isCompetency: true,
      );

      final sectionA = GeneratedSection(
        sectionId: 'sec_1',
        label: 'A',
        name: 'Short Answer',
        questions: [testQ1],
        totalMarks: 3,
      );

      final mockSetA = GeneratedPaper(
        id: 'test_set_a',
        assessmentId: realAssessmentId,
        sections: [sectionA],
        formattedContent: '',
        formattedContentLatex: '',
        answerKey: const {'q1': 'Light-dependent and dark reaction steps.'},
        setLabel: 'A',
        metadata: PaperMetadata(
          assessmentTitle: 'Class X Science Test',
          schoolName: 'Test School',
          subject: 'Science',
          grade: 10,
          totalMarks: 3,
          durationMinutes: 45,
          generatedAt: DateTime.now(),
          generatedBy: 'AcademicOS',
          version: '1.0',
          setLabel: 'A',
          tier: 'standard',
        ),
      );

      final mockSetB = mockSetA.copyWith(
        id: 'test_set_b',
        setLabel: 'B',
        metadata: mockSetA.metadata.copyWith(setLabel: 'B'),
      );

      final multiSetPaper = mockSetA.copyWith(sets: [mockSetA, mockSetB]);

      await tester.pumpWidget(wrapForTest(
        AssessmentReviewPage(
          assessmentId: realAssessmentId,
          paper: multiSetPaper,
        ),
        bloc: bloc,
      ));
      await tester.pumpAndSettle();

      // Parallel sets switcher
      expect(find.text('Parallel Question Sets (2 Sets)'), findsOneWidget);
      expect(find.text('Set A'), findsOneWidget);
      expect(find.text('Set B'), findsOneWidget);

      // Question stem and internal choice
      expect(find.text('Define photosynthesis in green plants.'), findsOneWidget);
      expect(find.text('OR'), findsOneWidget);
      expect(find.text('Explain the light-dependent reaction step by step.'), findsOneWidget);

      // Competency tag (CBQ)
      expect(find.text('CBQ'), findsOneWidget);

      // Switch to Set B
      await tester.tap(find.text('Set B'));
      await tester.pumpAndSettle();
      expect(find.text('SET B'), findsOneWidget);
    },
  );
}
