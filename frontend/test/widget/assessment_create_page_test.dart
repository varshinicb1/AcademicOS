// Real widget-level UI test guarding a real bug a real user hit: selecting
// a chapter in assessment creation for any subject other than Science
// showed a single disabled placeholder reading "Chapter selection depends
// on subject -- pick Science for the pilot question bank." -- and even for
// Science, the hardcoded list passed display names ("Chemical Reactions and
// Equations") straight through as chapterIds, which never matched the real
// corpus's slug-format ids ("chemical-reactions-equations"), so selecting a
// chapter silently filtered every real question out. Fixed by loading real
// chapters via PillarApi.chapters() (the same real source syllabus_page.dart
// already uses) for every subject the corpus actually has data for.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/presentation/assessment/pages/assessment_create_page.dart';

import '../support/real_di.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('assessment_create_test_');
    env.registerGetIt();
    await CorpusRepository.instance.ensureLoaded();
    await DemoSeeder.seedIfEmpty();
  });

  tearDownAll(() async {
    await env.dispose();
  });

  // Every step's own "Next" control row is present in the widget tree at
  // once (Flutter's vertical Stepper builds a controlsBuilder result per
  // step, collapsed rather than removed for inactive ones), so find.text
  // ('Next') is ambiguous. The step TITLE, by contrast, is always visible
  // and wired to onStepTapped -- jumping straight there is both simpler
  // and more robust than chaining "Next" taps.
  Future<void> goToChaptersStep(WidgetTester tester) async {
    await tester.tap(find.text('Chapters'));
    await tester.pumpAndSettle();
  }

  testWidgets(
    'Science (the only subject with real chapter tagging in the bundled corpus) shows real, selectable chapters',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await goToChaptersStep(tester);

      expect(
        find.textContaining('Chapter selection depends on subject'),
        findsNothing,
        reason: 'the old hardcoded, permanently-disabled placeholder must never show again',
      );

      final realChapters = CorpusRepository.instance.chapters('Science', 10);
      expect(realChapters, isNotEmpty,
          reason: 'the bundled corpus must have real Science Grade 10 chapters for this test to mean anything');
      expect(find.text(realChapters.first.chapterName), findsOneWidget,
          reason: 'a real chapter name from the real corpus must actually render');

      // The chapter must be a real, tappable checkbox (not disabled).
      final tile = find.widgetWithText(CheckboxListTile, realChapters.first.chapterName);
      final checkbox = tester.widget<CheckboxListTile>(tile);
      expect(checkbox.onChanged, isNotNull, reason: 'a real chapter must be selectable, not disabled');
    },
  );

  testWidgets(
    'Mathematics now has real chapter tagging in the bundled corpus and shows real, selectable chapters',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(DropdownButtonFormField<String>).last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Mathematics').last);
      await tester.pumpAndSettle();

      await goToChaptersStep(tester);

      final mathChapters = CorpusRepository.instance.chapters('Mathematics', 10);
      expect(mathChapters, isNotEmpty,
          reason: 'confirms Mathematics Grade 10 now has real chapter tags');
      expect(
        find.textContaining('Chapter selection depends on subject'),
        findsNothing,
        reason: 'the old hardcoded, permanently-disabled placeholder must never show again',
      );
      expect(find.text(mathChapters.first.chapterName), findsOneWidget,
          reason: 'must render real math chapter name');
    },
  );

  testWidgets(
    'a subject with no chapter tagging in the bundled corpus (Hindi) shows an honest explanation, never the old disabled placeholder or a silent blank screen',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(DropdownButtonFormField<String>).last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Hindi').last);
      await tester.pumpAndSettle();

      await goToChaptersStep(tester);

      expect(CorpusRepository.instance.chapters('Hindi', 10), isEmpty,
          reason: 'confirms Hindi currently has no chapter tags in corpus');
      expect(
        find.textContaining('Chapter selection depends on subject'),
        findsNothing,
        reason: 'the old hardcoded, permanently-disabled placeholder must never show again',
      );
      expect(find.textContaining('No chapters found for Hindi'), findsOneWidget,
          reason: 'must honestly explain why, not silently show nothing or a fake list');
      expect(find.textContaining('leaving chapters empty draws from every question'), findsOneWidget,
          reason: 'must tell the teacher they can still proceed');
    },
  );

  testWidgets(
    'selecting a chapter stores the real chapterId (slug), not a display name that would match nothing',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await goToChaptersStep(tester);

      final realChapters = CorpusRepository.instance.chapters('Science', 10);
      final first = realChapters.first;

      await tester.tap(find.widgetWithText(CheckboxListTile, first.chapterName));
      await tester.pumpAndSettle();

      final checkbox = tester.widget<CheckboxListTile>(find.widgetWithText(CheckboxListTile, first.chapterName));
      expect(checkbox.value, isTrue);

      // Confirm the real chapterId (a slug like "chemical-reactions-equations")
      // actually matches real questions -- proving this is the id that gets
      // sent, not the old display-name string that matched nothing.
      final matching = CorpusRepository.instance.all
          .where((q) => q.subject == 'Science' && q.grade == 10 && q.chapterIds.contains(first.chapterId));
      expect(matching, isNotEmpty,
          reason: 'the real chapterId must actually match real questions in the corpus');
    },
  );

  group('§21 subtopic filter (CurriculumApi.topicsForChapter is online-only -- '
      'these tests never expand the picker, so no live network call is triggered; '
      'the parsing/fetch logic itself is covered by curriculum_api_test.dart)', () {
    testWidgets('is hidden entirely with no chapter selected', (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await goToChaptersStep(tester);

      expect(find.text('Filter by subtopic (optional)'), findsNothing,
          reason: 'nothing to filter by subtopic within until at least one chapter is picked');
    });

    testWidgets('appears, collapsed, once a chapter is selected', (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await goToChaptersStep(tester);

      final realChapters = CorpusRepository.instance.chapters('Science', 10);
      await tester.tap(find.widgetWithText(CheckboxListTile, realChapters.first.chapterName));
      await tester.pumpAndSettle();

      expect(find.text('Filter by subtopic (optional)'), findsOneWidget);
      expect(find.text('Leave empty to draw from the whole chapter'), findsOneWidget,
          reason: 'an unexpanded, unfetched picker must say the filter is optional, not show a blank/loading state');
    });

    testWidgets('disappears again once every selected chapter is deselected', (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await goToChaptersStep(tester);

      final realChapters = CorpusRepository.instance.chapters('Science', 10);
      final tile = find.widgetWithText(CheckboxListTile, realChapters.first.chapterName);
      await tester.tap(tile);
      await tester.pumpAndSettle();
      expect(find.text('Filter by subtopic (optional)'), findsOneWidget);

      await tester.tap(tile); // deselect
      await tester.pumpAndSettle();
      expect(find.text('Filter by subtopic (optional)'), findsNothing);
    });
  });
}
