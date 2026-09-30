// Task 801: the teacher's list of papers -- the way in to both paper flows
// (Quick paper and New Assessment) -- at phone, tablet and laptop widths.
// Its two AppBar actions are the only route to a paper from this screen on a
// phone, so they have to be thumb-sized as well as on screen.
//
// The list itself is seeded rather than left empty. An empty list renders the
// centred "No assessments yet" text (assessment_list_page._buildList), so a
// test run against it proves the AppBar and the FAB fit and nothing at all
// about the row that has to survive 375 px: `Row [Expanded(title + subtitle),
// ChipTag(status)]`, an unbounded chip beside an Expanded -- the same shape
// as the Delayed Topics row this task had to fix (review of 2026-09-23). The
// two rows below carry the longest title and the longest status name a real
// school produces.
//
// A real AssessmentBloc wired to the real (offline) ApiClient, as
// assessment_review_page_test.dart does: the rows come back through the real
// repository from the real Hive-backed store, seeded the way the offline
// engine itself writes them (LocalApiClient.createAssessment ->
// LocalStore.upsertAssessment).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/session/current_session.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/presentation/assessment/pages/assessment_list_page.dart';
import 'package:academicos/core/theme/app_theme.dart';

import '../support/real_di.dart';
import 'responsive_harness.dart';

/// The longest title a CBSE school really gives a paper, and the longest
/// AssessmentStatus name (`questionOptimized`/`principalApproved`, 17
/// characters) -- the widest the row's chip can get.
const _longTitle = 'Class 10 Science Half-Yearly Examination 2026-27';
const _shortTitle = 'Class 7 Maths Unit Test 1';

Assessment _assessment(String id, String title, AssessmentStatus status, int grade, String subject) {
  final now = DateTime(2026, 9, 22);
  return Assessment(
    id: id,
    schoolId: CurrentSession.schoolId,
    teacherId: CurrentSession.userId,
    title: title,
    subject: subject,
    grade: grade,
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
    status: status,
    createdAt: now,
    updatedAt: now,
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useAppFonts();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('responsive_assessment_list_test_');
    // Before the assessments are written: CurrentSession reads the school id
    // off the registered ApiClient (LocalApiClient -> the device identity),
    // so the rows have to be keyed with GetIt already wired or the page's own
    // load finds none of them.
    env.registerGetIt();
    for (final a in [
      _assessment('assessment_long', _longTitle, AssessmentStatus.questionOptimized, 10, 'Science'),
      _assessment('assessment_short', _shortTitle, AssessmentStatus.draft, 7, 'Mathematics'),
    ]) {
      LocalStore.instance.upsertAssessment(a.toJson());
    }
  });

  tearDownAll(() async => env.dispose());

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('the assessments list fits and both ways to a new paper are ready at $name', (tester) async {
      useScreen(tester, size);
      await tester.pumpWidget(wrapForTest(const AssessmentListPage(),
          bloc: env.buildAssessmentBloc(), theme: AppTheme.lightTheme));
      await tester.pumpAndSettle();

      expectNoOverflow(tester);
      // The seeded rows, not the empty-state text: the row with the long
      // title and the widest status chip is the one that can overflow.
      expect(find.text('No assessments yet.\nTap "New Assessment" to build one with the AI Assessment Designer.'),
          findsNothing);
      expect(find.text(_longTitle), findsOneWidget);
      expect(find.text('Science · Grade 10 · 80 marks'), findsOneWidget);
      expect(find.text(AssessmentStatus.questionOptimized.name), findsOneWidget);
      expect(find.text(_shortTitle), findsOneWidget);

      // The whole row, chip included, stays inside the screen -- a chip
      // pushed past the right edge is the failure this row's shape invites.
      final chip = tester.getRect(find.text(AssessmentStatus.questionOptimized.name));
      expect(chip.right, lessThanOrEqualTo(size.size.width),
          reason: 'the status chip ends at ${chip.right.toStringAsFixed(0)} on a '
              '${size.size.width.toInt()} px screen');

      expectActionReady(tester, find.byTooltip('Quick paper (CBSE pattern)'), size, label: 'Quick paper');
      expectActionReady(tester, find.byTooltip('Create assessment'), size, label: 'Create assessment');
      expectActionReady(tester, find.byType(FloatingActionButton), size, label: 'New paper');
    });
  }

  testWidgets('in a desktop-UA browser at phone width both AppBar icons are still 48 px', (tester) async {
    // The same two icons on the density a desktop browser narrowed to 375 px
    // gets (`compact`, -8 -8), which the tests above cannot reach because
    // flutter_test pins the platform to android (review of 2026-09-23).
    await withDesktopDensity(() async {
      useScreen(tester, phoneScreen);
      await tester.pumpWidget(wrapForTest(const AssessmentListPage(),
          bloc: env.buildAssessmentBloc(), theme: AppTheme.lightTheme));
      await tester.pumpAndSettle();
      expectNoOverflow(tester);
      expectActionReady(tester, find.byTooltip('Quick paper (CBSE pattern)'), phoneScreen,
          label: 'Quick paper on a desktop density');
      expectActionReady(tester, find.byTooltip('Create assessment'), phoneScreen,
          label: 'Create assessment on a desktop density');
    });
  });
}
