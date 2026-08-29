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
    throw StateError('${finder.description} never became visible after scrolling');
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
      // THE regression: with the old widget.paper-only read, _exportPdf()
      // returned immediately (paper == null) and this button never appeared.
      expect(find.text('Preview, print or email'), findsOneWidget,
          reason: 'a real PDF must have been exported and _exportedUrl set -- '
              'this is the exact button that silently never appeared before the fix');
    },
  );
}
