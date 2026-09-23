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

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    paths.add(options.path);
    if (!options.path.startsWith('/curriculum/chapters/by-slug/')) {
      return handler.reject(DioException.badResponse(
          statusCode: 404, requestOptions: options,
          response: Response(requestOptions: options, statusCode: 404)));
    }
    if (notSetUpDetail != null) {
      return handler.reject(DioException.badResponse(
        statusCode: 404,
        requestOptions: options,
        response: Response(requestOptions: options, statusCode: 404,
            data: {'detail': notSetUpDetail}),
      ));
    }
    handler.resolve(Response(
        requestOptions: options, statusCode: 200, data: _fixtureTopics()));
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
      expect(find.text(physicsChapters.first.chapterName), findsOneWidget,
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

    testWidgets('a class the school has not set up shows the server\'s instruction, '
        'not an empty picker', (tester) async {
      backend.notSetUpDetail =
          'Set up Class 10 Science under Curriculum to filter by subtopic';
      await expandPicker(tester);

      expect(find.text('Set up Class 10 Science under Curriculum to filter by subtopic'),
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
