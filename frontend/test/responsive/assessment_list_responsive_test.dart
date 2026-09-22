// Task 801: the teacher's list of papers -- the way in to both paper flows
// (Quick paper and New Assessment) -- at phone, tablet and laptop widths.
// Its two AppBar actions are the only route to a paper from this screen on a
// phone, so they have to be thumb-sized as well as on screen.
//
// A real AssessmentBloc wired to the real (offline) ApiClient, as
// assessment_review_page_test.dart does: this test is about layout, so what
// matters is that the real page builds with a real, empty school list.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/presentation/assessment/pages/assessment_list_page.dart';

import '../support/real_di.dart';
import 'responsive_harness.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('responsive_assessment_list_test_');
    env.registerGetIt();
  });

  tearDownAll(() async => env.dispose());

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('the assessments list fits and both ways to a new paper are ready at $name', (tester) async {
      useScreen(tester, size);
      await tester.pumpWidget(wrapForTest(const AssessmentListPage(), bloc: env.buildAssessmentBloc()));
      await tester.pumpAndSettle();

      expectNoOverflow(tester);
      expectActionReady(tester, find.byTooltip('Quick paper (CBSE pattern)'), size, label: 'Quick paper');
      expectActionReady(tester, find.byTooltip('Create assessment'), size, label: 'Create assessment');
      expectActionReady(tester, find.byType(FloatingActionButton), size, label: 'New Assessment');
    });
  }
}
