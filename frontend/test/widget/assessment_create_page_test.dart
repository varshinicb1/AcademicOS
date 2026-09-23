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
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/assessment/pages/assessment_create_page.dart';

import '../support/real_di.dart';

/// GET /curriculum/chapters/by-slug/... answered with the payload the real
/// route really returns, or with its real 404. Records what was asked for.
class _SubtopicBackend extends Interceptor {
  final List<String> paths = [];
  String? notSetUpDetail;

  /// When set, every request fails with this status and no body: a 500, a
  /// 502 from a proxy, a Render cold start that ran past the client's
  /// timeout. Everything the route can answer EXCEPT its own 404 -- the only
  /// reply that says anything about the school's curriculum.
  int? failWithStatus;

  /// When set, the FIRST request is not answered until this completes -- the
  /// only way to reproduce a teacher changing subject or grade while a
  /// subtopic fetch is still in flight (a real server takes time; this fake
  /// otherwise answers within the same microtask).
  Completer<void>? holdFirstResponse;

  /// Per-path payloads, so two requests can be told apart by what came back
  /// and not only by the path recorded. Falls back to the captured fixture.
  final Map<String, List<Map<String, dynamic>>> topicsByPath = {};

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    paths.add(options.path);
    final isFirst = paths.length == 1;
    if (!options.path.startsWith('/curriculum/chapters/by-slug/')) {
      return handler.reject(DioException.badResponse(
          statusCode: 404, requestOptions: options,
          response: Response(requestOptions: options, statusCode: 404)));
    }
    final failure = failWithStatus;
    if (failure != null) {
      return handler.reject(DioException.badResponse(
          statusCode: failure, requestOptions: options,
          response: Response(requestOptions: options, statusCode: failure)));
    }
    if (notSetUpDetail != null) {
      return handler.reject(DioException.badResponse(
        statusCode: 404,
        requestOptions: options,
        response: Response(requestOptions: options, statusCode: 404,
            data: {'detail': notSetUpDetail}),
      ));
    }
    final body = topicsByPath[options.path] ?? _fixtureTopics();
    final answer = Response(
        requestOptions: options, statusCode: 200, data: body);
    final hold = isFirst ? holdFirstResponse : null;
    if (hold != null) {
      hold.future.then((_) => handler.resolve(answer));
      return;
    }
    handler.resolve(answer);
  }
}

/// True only in a build made with --dart-define=ACADEMICOS_OFFLINE=true --
/// the standalone Android app, which has no server to ask.
const _offlineBuild = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

/// Captured from the real route by tests/test_curriculum_subtopic_filter.py,
/// which also fails when the route's shape drifts from this file.
List<Map<String, dynamic>> _fixtureTopics() =>
    (jsonDecode(File('test/fixtures/chapter_subtopics_by_slug.json').readAsStringSync())
            as List)
        .cast<Map<String, dynamic>>();

/// The same captured payload with every subtopic's tagged-question count
/// replaced, so a test can render the state the feature is meant to reach
/// (questions actually tagged) as well as the one real data is in today.
List<Map<String, dynamic>> _withTaggedCounts(
        List<Map<String, dynamic>> topics, int count) =>
    [
      for (final topic in topics)
        {
          ...topic,
          'subtopics': [
            for (final sub in (topic['subtopics'] as List).cast<Map<String, dynamic>>())
              {...sub, 'taggedQuestionCount': count},
          ],
        },
    ];

/// The same captured payload with every subtopic name prefixed, so a test can
/// tell which of two responses the picker is actually rendering.
List<Map<String, dynamic>> _prefixSubtopicNames(
        List<Map<String, dynamic>> topics, String prefix) =>
    [
      for (final topic in topics)
        {
          ...topic,
          'subtopics': [
            for (final sub in (topic['subtopics'] as List).cast<Map<String, dynamic>>())
              {...sub, 'name': '$prefix${sub['name']}'},
          ],
        },
    ];

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
      // A chapter NAME is not unique in the bundled corpus: the display name
      // comes from a question's first tag, and the 2026-09-21 bank rebuild left
      // two Science 10 chapters both reading "Acids, Bases and Salts" (and two
      // Physics 12 ones "Current Electricity"). The chapter ID is the unique
      // handle, so these assertions check that at least one tile renders it and
      // act on the first.
      expect(find.text(realChapters.first.chapterName), findsWidgets,
          reason: 'a real chapter name from the real corpus must actually render');

      // The chapter must be a real, tappable checkbox (not disabled).
      final tile = find.widgetWithText(CheckboxListTile, realChapters.first.chapterName).first;
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
      expect(find.text(mathChapters.first.chapterName), findsWidgets,
          reason: 'must render real math chapter name');
    },
  );

  testWidgets(
    'Grade 12 Physics shows real, selectable chapters from Senior Secondary corpus',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();

      // Change Grade to 12
      await tester.tap(find.byType(DropdownButtonFormField<int>).first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Grade 12').last);
      await tester.pumpAndSettle();

      await goToChaptersStep(tester);

      final physicsChapters = CorpusRepository.instance.chapters('Physics', 12);
      expect(physicsChapters, isNotEmpty,
          reason: 'confirms Physics Grade 12 has real chapter tags');
      expect(find.text(physicsChapters.first.chapterName), findsWidgets,
          reason: 'must render real Physics Grade 12 chapter name');
    },
  );

  testWidgets(
    'a subject with no chapter tagging in the bundled corpus (Sanskrit) shows an honest explanation, never the old disabled placeholder or a silent blank screen',
    (tester) async {
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(DropdownButtonFormField<String>).last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Sanskrit').last);
      await tester.pumpAndSettle();

      await goToChaptersStep(tester);

      expect(CorpusRepository.instance.chapters('Sanskrit', 10), isEmpty,
          reason: 'confirms Sanskrit currently has no chapter tags in corpus');
      expect(
        find.textContaining('Chapter selection depends on subject'),
        findsNothing,
        reason: 'the old hardcoded, permanently-disabled placeholder must never show again',
      );
      expect(find.textContaining('No chapters found for Sanskrit'), findsOneWidget,
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

      await tester.tap(find.widgetWithText(CheckboxListTile, first.chapterName).first);
      await tester.pumpAndSettle();

      final checkbox = tester.widget<CheckboxListTile>(
          find.widgetWithText(CheckboxListTile, first.chapterName).first);
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

  group('§21 subtopic filter, collapsed (the picker is online-only; these '
      'tests never expand it, so no network call is triggered -- the expanded '
      'picker has its own group below, against a captured backend payload)', () {
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
      await tester.tap(find.widgetWithText(CheckboxListTile, realChapters.first.chapterName).first);
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
      final tile = find.widgetWithText(CheckboxListTile, realChapters.first.chapterName).first;
      await tester.tap(tile);
      await tester.pumpAndSettle();
      expect(find.text('Filter by subtopic (optional)'), findsOneWidget);

      await tester.tap(tile); // deselect
      await tester.pumpAndSettle();
      expect(find.text('Filter by subtopic (optional)'), findsNothing);
    });
    // Two of these three assert the collapsed header is PRESENT, which is
    // only true when the picker exists at all. The offline build drops it
    // (_buildSubtopicFilter returns nothing), so the whole group is about a
    // widget that is not in that tree -- same reason the expanded group
    // below skips. What the offline build must do instead is asserted by
    // 'the offline build hides the subtopic filter and calls nothing'.
  }, skip: _offlineBuild ? 'the picker does not exist in the offline build' : null);

  // The regression this file's newest group exists for: the picker held a
  // SYLLABUS slug ("chemical-reactions-equations") and called the route that
  // wants the school's own `chap_` id, so it found a subtopic exactly never.
  // Real Dio + an interceptor answering with a payload captured from the
  // real route (test/fixtures/chapter_subtopics_by_slug.json, re-captured
  // and diffed by tests/test_curriculum_subtopic_filter.py) -- no network,
  // no hand-written JSON.
  group('§21 subtopic filter, expanded against a captured backend payload', () {
    late _SubtopicBackend backend;

    setUp(() {
      backend = _SubtopicBackend();
      final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))
        ..interceptors.add(backend);
      if (GetIt.I.isRegistered<CurriculumApi>()) GetIt.I.unregister<CurriculumApi>();
      GetIt.I.registerSingleton<CurriculumApi>(CurriculumApi(dio));
    });

    tearDown(() {
      if (GetIt.I.isRegistered<CurriculumApi>()) GetIt.I.unregister<CurriculumApi>();
    });

    /// Selects the first real Science 10 chapter and opens the picker.
    Future<ChapterEntryData> expandPicker(WidgetTester tester) async {
      tester.view.physicalSize = const Size(1600, 3000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await goToChaptersStep(tester);

      // `.first` on both sides deliberately: the bundled corpus labels two
      // Science 10 chapters "Acids, Bases and Salts" (it takes the display
      // name from the question's first tag, and the 2026-09-21 bank rebuild
      // left those tags pointing at another chapter), so a name is not a
      // unique handle. The list is sorted by question count, so the first
      // entry and the first tile are the same chapter either way.
      final chapter = CorpusRepository.instance.chapters('Science', 10).first;
      await tester.tap(find.widgetWithText(CheckboxListTile, chapter.chapterName).first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Filter by subtopic (optional)'));
      await tester.pumpAndSettle();
      return chapter;
    }

    testWidgets('asks for the chapter by its syllabus slug, subject and grade', (tester) async {
      final chapter = await expandPicker(tester);

      expect(backend.paths, hasLength(1));
      expect(
        backend.paths.single,
        '/curriculum/chapters/by-slug/Science/10/${chapter.chapterId}/topics',
        reason: 'the slug is the only chapter id this page has; sending it to '
            '/chapters/{chap_id}/topics is the bug that made this picker useless',
      );
    });

    // A paper drawn from more than one chapter is the normal case on this
    // screen, and the picker used to fetch only on onExpansionChanged --
    // which fires when the tile OPENS and never again. Tick a second chapter
    // with the picker already open and the ExpansionTile keeps its expanded
    // state across the rebuild (same widget type, same slot), so that
    // chapter's section rendered as SizedBox.shrink(): no spinner, no
    // message, no request. The teacher saw one chapter's subtopics and read
    // the other's silence as "that chapter has none".
    testWidgets('a chapter ticked while the picker is already open fetches and '
        'renders its own subtopics', (tester) async {
      final chapters = CorpusRepository.instance.chapters('Science', 10);
      expect(chapters.length, greaterThan(1),
          reason: 'this test is about a second chapter, so the corpus must have one');
      // A chapter NAME is not a unique handle in the bundled corpus (the
      // 2026-09-21 rebuild left two Science 10 chapters both reading "Acids,
      // Bases and Salts"), and this test taps by name -- so take the first
      // later chapter whose name identifies exactly one tile.
      final second = chapters.skip(1).firstWhere(
          (c) =>
              c.chapterName != chapters.first.chapterName &&
              chapters.where((o) => o.chapterName == c.chapterName).length == 1,
          orElse: () => throw StateError(
              'no Science 10 chapter after the first has a unique name'));
      backend.topicsByPath[
              '/curriculum/chapters/by-slug/Science/10/${second.chapterId}/topics'] =
          _prefixSubtopicNames(_fixtureTopics(), 'Second chapter: ');

      final first = await expandPicker(tester);
      expect(backend.paths,
          ['/curriculum/chapters/by-slug/Science/10/${first.chapterId}/topics']);

      // Tick the second chapter WITHOUT collapsing the picker.
      await tester.tap(find.widgetWithText(CheckboxListTile, second.chapterName).first);
      await tester.pumpAndSettle();

      expect(backend.paths, [
        '/curriculum/chapters/by-slug/Science/10/${first.chapterId}/topics',
        '/curriculum/chapters/by-slug/Science/10/${second.chapterId}/topics',
      ], reason: 'the second chapter must be asked for, not silently skipped');

      final firstSubtopic = ((_fixtureTopics().first['subtopics'] as List).first
          as Map<String, dynamic>)['name'] as String;
      expect(find.text('Second chapter: $firstSubtopic'), findsOneWidget,
          reason: 'the second chapter\'s own subtopics must render, not a blank row');
      expect(find.text(firstSubtopic), findsOneWidget,
          reason: 'and the first chapter\'s must still be there');
    });

    testWidgets('shows the real subtopics the backend returned, under their topics',
        (tester) async {
      await expandPicker(tester);

      final fixture = _fixtureTopics();
      expect(fixture, isNotEmpty);
      for (final topic in fixture) {
        for (final sub in (topic['subtopics'] as List).cast<Map<String, dynamic>>()) {
          expect(find.text(sub['name'] as String), findsOneWidget,
              reason: 'every captured subtopic must actually render');
        }
      }
      expect(find.textContaining('no subtopic breakdown available yet'), findsNothing);
    });

    testWidgets('a subtopic can be ticked, and it is the backend id that gets ticked',
        (tester) async {
      await expandPicker(tester);
      final first = ((_fixtureTopics().first['subtopics'] as List).first
          as Map<String, dynamic>);

      await tester.tap(find.widgetWithText(CheckboxListTile, first['name'] as String));
      await tester.pumpAndSettle();

      final tile = tester.widget<CheckboxListTile>(
          find.widgetWithText(CheckboxListTile, first['name'] as String));
      expect(tile.value, isTrue);
      expect(find.text('1 subtopic selected'), findsOneWidget,
          reason: 'the collapsed summary must count the real selection');
    });

    // Both subtopic caches are keyed by chapter slug alone, and a slug is
    // only unique within one subject and grade: English has a
    // "reading-comprehension" chapter in Grade 10 AND Grade 9 (that is the
    // real bundled corpus, asserted below -- it was Grade 12 until the
    // release's rebuilt bank dropped the SQP/CBE grades, and 9/10 is the
    // pair that slug really spans now). Clearing the caches on a grade
    // change is therefore not enough -- a request already in flight used to
    // land afterwards and write Grade 10's topics back under that slug, and
    // the containsKey short-circuit then served them as Grade 9's, without
    // ever asking the server about Grade 9.
    testWidgets('a fetch that lands after the teacher changes grade is discarded, '
        'and the new grade is asked for its own subtopics', (tester) async {
      tester.view.physicalSize = const Size(1600, 3000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      const slug = 'reading-comprehension';
      // `where`, not `.first`: Grade 9 English carries two chapters in the
      // release's bank and only one of them is the shared slug.
      final grade10 = CorpusRepository.instance.chapters('English', 10)
          .where((c) => c.chapterId == slug).toList();
      final grade9 = CorpusRepository.instance.chapters('English', 9)
          .where((c) => c.chapterId == slug).toList();
      expect(grade10, hasLength(1));
      expect(grade9, hasLength(1),
          reason: 'this test only means something while the same slug really is a '
              'chapter of two different grades in the bundled corpus');

      final held = Completer<void>();
      backend.holdFirstResponse = held;
      backend.topicsByPath['/curriculum/chapters/by-slug/English/9/$slug/topics'] =
          _prefixSubtopicNames(_fixtureTopics(), 'Grade 9: ');

      await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
      await tester.pumpAndSettle();

      Future<void> pickSubject(String subject) async {
        await tester.tap(find.byType(DropdownButtonFormField<String>).last);
        await tester.pumpAndSettle();
        await tester.tap(find.text(subject).last);
        await tester.pumpAndSettle();
      }

      // An unanswered fetch leaves a CircularProgressIndicator spinning, and
      // pumpAndSettle never returns while one is animating -- so every step
      // taken while the Grade 10 request is deliberately in flight pumps
      // fixed frames instead.
      Future<void> settleWhileFetching() async {
        await tester.pump();
        await tester.pump(const Duration(seconds: 1));
      }

      Future<void> selectChapterAndExpandPicker(String chapterName,
          {required bool fetchInFlight}) async {
        await goToChaptersStep(tester);
        await tester.tap(find.widgetWithText(CheckboxListTile, chapterName).first);
        await tester.pumpAndSettle();
        await tester.tap(find.text('Filter by subtopic (optional)'));
        if (fetchInFlight) {
          await settleWhileFetching();
        } else {
          await tester.pumpAndSettle();
        }
      }

      await pickSubject('English');
      await selectChapterAndExpandPicker(grade10.first.chapterName,
          fetchInFlight: true);
      expect(backend.paths,
          ['/curriculum/chapters/by-slug/English/10/$slug/topics'],
          reason: 'the Grade 10 fetch is in flight and deliberately unanswered');

      // The teacher changes her mind mid-fetch.
      await tester.tap(find.text('Basic Information'));
      await settleWhileFetching();
      await tester.tap(find.byType(DropdownButtonFormField<int>).first);
      await settleWhileFetching();
      await tester.tap(find.text('Grade 9').last);
      await tester.pumpAndSettle();

      // Only now does the Grade 10 answer arrive.
      held.complete();
      await tester.pumpAndSettle();

      await selectChapterAndExpandPicker(grade9.first.chapterName,
          fetchInFlight: false);

      expect(backend.paths, [
        '/curriculum/chapters/by-slug/English/10/$slug/topics',
        '/curriculum/chapters/by-slug/English/9/$slug/topics',
      ], reason: 'the stale Grade 10 answer must not have populated the cache, '
          'or Grade 9 would silently reuse it and never be requested');

      final firstSubtopic = ((_fixtureTopics().first['subtopics'] as List).first
          as Map<String, dynamic>)['name'] as String;
      expect(find.text('Grade 9: $firstSubtopic'), findsOneWidget,
          reason: 'the picker must show what the server said about Grade 9');
      expect(find.text(firstSubtopic), findsNothing,
          reason: 'Grade 10\'s subtopics must not be offered for a Grade 9 chapter');
    });

    // Task 115's required behaviour 4 ("selecting subtopics actually narrows
    // question search") is NOT met on real data and this pair of tests is
    // what stops that being silent. The picker now finds real subtopics, but
    // question_subtopic_links has 0 rows in every real school
    // (academicos-data/curriculum/curriculum.sqlite: 417 subtopics, 0 links,
    // measured 2026-09-23), and POST /questions/search intersects on exactly
    // that table -- so ticking a subtopic took a real Class 10 Science
    // chapter from 102 questions to 0 with nothing on screen to explain it.
    // The captured payload carries taggedQuestionCount 0 throughout, which is
    // the true state, so the warning below is asserted against real data.
    testWidgets('warns that ticking a subtopic would empty the paper while '
        'nothing is tagged', (tester) async {
      await expandPicker(tester);

      final captured = [
        for (final t in _fixtureTopics())
          for (final s in (t['subtopics'] as List).cast<Map<String, dynamic>>())
            s['taggedQuestionCount'],
      ];
      expect(captured, isNotEmpty);
      expect(captured, everyElement(0),
          reason: 'this test only means something while the real route really '
              'reports nothing tagged; if tagging ships, re-capture the fixture');

      expect(find.textContaining('No questions are tagged to these subtopics yet'),
          findsOneWidget);
      expect(find.textContaining('produces an empty paper'), findsOneWidget,
          reason: 'the consequence is what a teacher acts on, not the bare fact');
      expect(find.textContaining('no questions tagged yet'), findsWidgets,
          reason: 'each subtopic carries its own count, so a partly-tagged '
              'chapter is readable row by row and not just in aggregate');
    });

    testWidgets('shows each subtopic\'s real tagged-question count once there is one',
        (tester) async {
      final chapter = CorpusRepository.instance.chapters('Science', 10).first;
      backend.topicsByPath[
              '/curriculum/chapters/by-slug/Science/10/${chapter.chapterId}/topics'] =
          _withTaggedCounts(_fixtureTopics(), 7);

      await expandPicker(tester);

      expect(find.textContaining('7 questions tagged'), findsWidgets);
      expect(find.textContaining('No questions are tagged to these subtopics yet'),
          findsNothing,
          reason: 'the warning is about an empty result, not about the picker');
    });

    // A 404 is the school's own state and is cached as an answer (above). A
    // 500, a 502, a dropped connection or a cold start past the 90s Dio
    // timeout is not: it says nothing about the curriculum. Writing an empty
    // topic list for one would print "<chapter>: no subtopic breakdown
    // available yet" -- a claim about what the school teaches, made off a
    // timeout -- and, because the fetch short-circuits on an already-cached
    // slug, would block every later attempt for the rest of the session.
    testWidgets('a transient failure is not reported as "no subtopic breakdown", '
        'and the chapter is still refetchable afterwards', (tester) async {
      backend.failWithStatus = 500;
      final chapter = await expandPicker(tester);
      final path = '/curriculum/chapters/by-slug/Science/10/${chapter.chapterId}/topics';
      expect(backend.paths, [path]);

      expect(find.textContaining('no subtopic breakdown available yet'), findsNothing,
          reason: 'a 500 is not evidence that this chapter has no subtopics');
      expect(find.textContaining('Could not load subtopics'), findsOneWidget,
          reason: 'the row must say what actually happened, and that it can be retried');

      // Collapse and re-expand with the server healthy again.
      await tester.tap(find.text('Filter by subtopic (optional)'));
      await tester.pumpAndSettle();
      backend.failWithStatus = null;
      await tester.tap(find.text('Filter by subtopic (optional)'));
      await tester.pumpAndSettle();

      expect(backend.paths, [path, path],
          reason: 'a failed slug must not be cached as an answer, or re-opening '
              'the picker would never ask again');
      final firstSubtopic = ((_fixtureTopics().first['subtopics'] as List).first
          as Map<String, dynamic>)['name'] as String;
      expect(find.text(firstSubtopic), findsOneWidget);
      expect(find.textContaining('Could not load subtopics'), findsNothing);
    });

    testWidgets('tapping the failed row retries it in place', (tester) async {
      backend.failWithStatus = 503; // what a Render instance waking up sends
      await expandPicker(tester);
      expect(backend.paths, hasLength(1));

      backend.failWithStatus = null;
      await tester.tap(find.textContaining('Could not load subtopics'));
      await tester.pumpAndSettle();

      expect(backend.paths, hasLength(2),
          reason: 'the retry the row offers has to actually make a request');
      final firstSubtopic = ((_fixtureTopics().first['subtopics'] as List).first
          as Map<String, dynamic>)['name'] as String;
      expect(find.text(firstSubtopic), findsOneWidget);
      expect(find.textContaining('Could not load subtopics'), findsNothing);
    });

    testWidgets('a class the school has not set up shows the server\'s instruction, '
        'not an empty picker', (tester) async {
      // The real sentence the route sends a TEACHER (the majority reader of
      // this screen): every remedy is principal-gated, so it names the
      // person who can act, not a console she would be refused from.
      backend.notSetUpDetail =
          'Ask your principal to set up Class 10 Science, then you can filter by subtopic';
      await expandPicker(tester);

      expect(
          find.text(
              'Ask your principal to set up Class 10 Science, then you can filter by subtopic'),
          findsOneWidget,
          reason: 'an empty list reads as "this chapter has no subtopics", which is a '
              'different fact with a different action');
      expect(find.textContaining('no subtopic breakdown available yet'), findsNothing);
    });
  }, skip: _offlineBuild ? 'the picker does not exist in the offline build' : null);

  // Only means something under --dart-define=ACADEMICOS_OFFLINE=true (the
  // flag the real APK builds with), same convention as
  // test/local_engine/paper_delivery_test.dart. The offline build has no
  // local Topic/Subtopic data and must never reach a server, so the filter
  // is absent rather than present-and-broken.
  testWidgets('the offline build hides the subtopic filter and calls nothing',
      (tester) async {
    final backend = _SubtopicBackend();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))
      ..interceptors.add(backend);
    if (GetIt.I.isRegistered<CurriculumApi>()) GetIt.I.unregister<CurriculumApi>();
    GetIt.I.registerSingleton<CurriculumApi>(CurriculumApi(dio));
    addTearDown(() {
      if (GetIt.I.isRegistered<CurriculumApi>()) GetIt.I.unregister<CurriculumApi>();
    });

    await tester.pumpWidget(wrapForTest(const AssessmentCreatePage()));
    await tester.pumpAndSettle();
    await goToChaptersStep(tester);
    final chapter = CorpusRepository.instance.chapters('Science', 10).first;
    await tester.tap(find.widgetWithText(CheckboxListTile, chapter.chapterName).first);
    await tester.pumpAndSettle();

    expect(find.text('Filter by subtopic (optional)'),
        _offlineBuild ? findsNothing : findsOneWidget);
    expect(backend.paths, isEmpty,
        reason: 'nothing is fetched until the picker is expanded, and in the '
            'offline build there is nothing to expand');
  });
}
