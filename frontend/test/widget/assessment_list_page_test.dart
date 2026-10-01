// The Papers list (QA pass of 2026-10-01):
//   * P-06: a paper saved in the builder was missing from the list until a
//     browser reload -- the list stays alive under the builder and loaded
//     once. It is read again whenever it is the page on screen again.
//   * P-15, P-16: the empty text names the real button; each row shows the
//     printed marks (79 after a removal, not the template's 80), the author
//     and the date, and "Class 10".
//   * P-14: no icon-only duplicate of "New paper".
//
// A real AssessmentBloc on the real (offline) ApiClient, as the other list
// tests do; the rows are written to the real Hive-backed store.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/session/current_session.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/presentation/assessment/pages/assessment_list_page.dart';
import 'package:academicos/presentation/blocs/assessment_bloc.dart';

import '../support/real_di.dart';

Assessment _paper(String id, String title, {Map<String, dynamic> metadata = const {}}) => Assessment(
      id: id,
      schoolId: CurrentSession.schoolId,
      teacherId: CurrentSession.userId,
      title: title,
      subject: 'Mathematics',
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
      createdAt: DateTime(2026, 10, 1, 9),
      updatedAt: DateTime(2026, 10, 1, 9),
      metadata: metadata,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('assessment_list_page_test_');
    env.registerGetIt();
  });

  tearDownAll(() async => env.dispose());

  setUp(() {
    for (final a in LocalStore.instance.allAssessments()) {
      LocalStore.instance.deleteAssessment(a['id'] as String);
    }
  });

  /// The list under a router, as the app nests it: the builder is a route
  /// above it, and the list's own state survives underneath.
  Future<GoRouter> pumpRouted(WidgetTester tester, AssessmentBloc bloc) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final router = GoRouter(initialLocation: '/assessment', routes: [
      // Inside a shell, as app_router.dart nests every page.
      ShellRoute(
        builder: (_, __, child) => child,
        routes: [
          GoRoute(
            path: '/assessment',
            builder: (_, __) => const AssessmentListPage(),
            routes: [
              GoRoute(path: 'build', builder: (_, __) => const Scaffold(body: Text('The builder'))),
            ],
          ),
          GoRoute(path: '/home', builder: (_, __) => const Scaffold(body: Text('Today'))),
        ],
      ),
    ]);
    addTearDown(router.dispose);
    await tester.pumpWidget(BlocProvider<AssessmentBloc>.value(
      value: bloc,
      child: MaterialApp.router(routerConfig: router),
    ));
    await tester.pumpAndSettle();
    return router;
  }

  testWidgets('a paper saved in the builder is in the list on the way back (P-06)', (tester) async {
    LocalStore.instance.upsertAssessment(_paper('a1', 'Unit Test').toJson());
    final router = await pumpRouted(tester, env.buildAssessmentBloc());
    expect(find.text('Unit Test'), findsOneWidget);

    router.push('/assessment/build');
    await tester.pumpAndSettle();
    expect(find.text('The builder'), findsOneWidget);
    // The builder saves a paper on the server.
    LocalStore.instance.upsertAssessment(_paper('a2', 'Half-Yearly Examination').toJson());

    router.pop();
    await tester.pumpAndSettle();
    expect(find.text('Half-Yearly Examination'), findsOneWidget, reason: 'read again on the way back');

    // The sidebar's way back: go, from another destination.
    router.go('/home');
    await tester.pumpAndSettle();
    LocalStore.instance.upsertAssessment(_paper('a3', 'Annual Examination').toJson());
    router.go('/assessment');
    await tester.pumpAndSettle();
    expect(find.text('Annual Examination'), findsOneWidget);
  });

  testWidgets('Refresh and pull-to-refresh read the list again', (tester) async {
    final router = await pumpRouted(tester, env.buildAssessmentBloc());
    expect(router.state.uri.path, '/assessment');
    expect(find.text('No papers yet. Start one with New paper.'), findsOneWidget, reason: 'P-15');

    LocalStore.instance.upsertAssessment(_paper('a1', 'Unit Test').toJson());
    await tester.tap(find.byTooltip('Refresh'));
    await tester.pumpAndSettle();
    expect(find.text('Unit Test'), findsOneWidget);

    LocalStore.instance.upsertAssessment(_paper('a2', 'Class test').toJson());
    await tester.fling(find.text('Unit Test'), const Offset(0, 400), 1000);
    await tester.pumpAndSettle();
    expect(find.text('Class test'), findsOneWidget);
  });

  testWidgets('a row shows the printed marks, the author and the date (P-16)', (tester) async {
    LocalStore.instance.upsertAssessment(
        _paper('a1', 'Half-Yearly Examination', metadata: {'authorName': 'Meera Iyer', 'paperMarks': 79}).toJson());
    LocalStore.instance.upsertAssessment(_paper('a2', 'Unit Test').toJson());
    await pumpRouted(tester, env.buildAssessmentBloc());

    expect(find.text('Mathematics · Class 10 · 79 marks'), findsOneWidget, reason: 'not the blueprint 80');
    expect(find.text('Meera Iyer · 1 Oct 2026'), findsOneWidget);
    expect(find.text('Mathematics · Class 10 · 80 marks'), findsOneWidget, reason: 'no paperMarks: the blueprint');
    expect(find.text('1 Oct 2026'), findsOneWidget, reason: 'no author name sent: the date alone');
    expect(find.textContaining('Grade'), findsNothing);
  });

  testWidgets('one New paper, and a Quick paper with words (P-14)', (tester) async {
    await pumpRouted(tester, env.buildAssessmentBloc());
    expect(find.byTooltip('Create assessment'), findsNothing);
    expect(find.text('New paper'), findsOneWidget);
    expect(find.text('Quick paper'), findsOneWidget);
  });
}
