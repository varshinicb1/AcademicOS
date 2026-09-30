// Task 801: today's lessons and marking one taught, at phone, tablet and
// laptop widths. The Today page (its New paper action and today's lessons,
// since the 2026-10-01 review) and the schedule itself -- Day, Week and
// Month -- must fit, and the Yes button of the "Did you teach this?" sheet
// must be on screen and big enough to hit.
//
// A real Dio whose interceptor answers the curriculum routes in the shape the
// server returns (MyScheduleEntry, curriculum/schemas.py), no network.
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/home/pages/today_page.dart';
import 'package:academicos/presentation/schedule/pages/my_schedule_page.dart';

import 'responsive_harness.dart';

String _today() {
  final d = DateTime.now();
  return '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}

const _longLesson = 'Image formation by a concave mirror for different positions of the object';
const _secondLesson = 'Displacement and double displacement reactions';

/// Today's three lessons, with names as long as the real CBSE Class 10
/// Science ones; marking one taught changes what the next GET returns.
class _Schedule extends Interceptor {
  final statuses = {'lesson_1': 'scheduled', 'lesson_2': 'scheduled', 'lesson_3': 'completed'};
  final patches = <Object?>[];

  /// Every request this fixture had no answer for, as "METHOD /path".
  ///
  /// Asserted empty after each test. A page that calls a route the fixture
  /// does not serve catches the DioException and renders an empty or error
  /// state, which fits any screen and overflows nothing -- so without this
  /// the test would keep passing while measuring a blank page (review of
  /// 2026-09-23).
  final rejected = <String>[];

  Map<String, Object?> _lesson(String id, String chapter, String topic, String subtopic) => {
        'lessonId': id,
        'date': _today(),
        'status': statuses[id],
        'note': id == 'lesson_3' ? 'Finished with the ray diagram practice sheet' : null,
        'bookId': 'book_1',
        'bookTitle': 'Science - Textbook for Class X',
        'subjectName': 'Science',
        'chapterName': chapter,
        'topicName': topic,
        'subtopicId': 'st_$id',
        'subtopicName': subtopic,
      };

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.method == 'GET' && options.path == '/curriculum/my-schedule') {
      handler.resolve(Response(requestOptions: options, statusCode: 200, data: [
        _lesson('lesson_1', 'Light - Reflection and Refraction', 'Reflection of light by spherical mirrors',
            _longLesson),
        _lesson('lesson_2', 'Chemical Reactions and Equations', 'Types of chemical reactions', _secondLesson),
        _lesson('lesson_3', 'Life Processes', 'Nutrition', 'Autotrophic nutrition'),
      ]));
      return;
    }
    if (options.method == 'PATCH' && options.path.startsWith('/curriculum/scheduled-lessons/')) {
      patches.add(options.data);
      statuses[options.path.split('/').last] = (options.data as Map)['status'] as String;
      handler.resolve(Response(requestOptions: options, statusCode: 200, data: null));
      return;
    }
    // The Today page's other cards: nothing waiting, no papers yet.
    if (options.method == 'GET' &&
        const {'/curriculum/my-day', '/paper-reviews', '/homework', '/assessments'}.contains(options.path)) {
      handler.resolve(Response(requestOptions: options, statusCode: 200, data: <Object>[]));
      return;
    }
    rejected.add('${options.method} ${options.path}');
    handler.reject(DioException.badResponse(
        statusCode: 404,
        requestOptions: options,
        response: Response(requestOptions: options, statusCode: 404, data: {'detail': 'not found'})));
  }
}

Finder _button(String label) =>
    find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));

Finder _tappable(String text) => find.ancestor(of: find.text(text), matching: find.byType(InkWell)).first;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useAppFonts();

  // The Today page reads LocalStore; an in-memory box keeps its reads inside
  // a widget test's fake clock (see paper_builder_flow_test.dart).
  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('responsive_today_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });
  tearDownAll(() async => Hive.close());

  late _Schedule server;
  setUp(() async {
    await LocalStore.instance.box.clear();
    server = _Schedule();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(server);
    GetIt.I.registerSingleton<CurriculumApi>(CurriculumApi(dio));
    GetIt.I.registerSingleton<Dio>(dio);   // the Today page reads through Ops
  });
  tearDown(() {
    // Before the reset, so a page that quietly fell back to an empty state
    // fails the test that was meant to prove it fits. See [_Schedule.rejected].
    expect(server.rejected, isEmpty,
        reason: 'the page asked for routes this fixture does not serve, so whatever those calls fill was '
            'empty or errored on the screen this test just measured');
    GetIt.I.reset();
  });

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets("the Today page fits and New paper and today's lessons are ready at $name", (tester) async {
      await pumpPage(tester, const TodayPage(), size);
      expectNoOverflow(tester);
      expectActionReady(tester, _button('New paper'), size, label: 'New paper');
      expectActionReady(tester, _tappable(_longLesson), size, label: "today's first lesson");
    });

    testWidgets("today's lessons fit and one is marked taught with Yes at $name", (tester) async {
      await pumpPage(tester, const MySchedulePage(), size);
      expectNoOverflow(tester, where: ' on the day view');
      expectActionReady(tester, _tappable(_longLesson), size, label: "today's first lesson");

      await tester.tap(find.text(_longLesson));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' in the mark sheet');
      expect(find.text('Did you teach this?'), findsOneWidget);
      expectActionReady(tester, _button('Yes'), size, label: 'Yes');
      expectActionReady(tester, _button('No'), size, label: 'No');

      await tester.enterText(find.widgetWithText(TextField, 'Note (optional)'), 'Covered with the ray box');
      await tester.pumpAndSettle();
      await tester.tap(_button('Yes'));
      await tester.pumpAndSettle();
      expect(server.patches, [
        {'status': 'completed', 'note': 'Covered with the ray box'},
      ]);
      expect(find.text('Did you teach this?'), findsNothing, reason: 'the sheet closes on success');
      expect(find.descendant(of: _tappable(_longLesson), matching: find.text('completed')), findsOneWidget,
          reason: 'the reloaded day shows the new mark on that lesson');
      expectNoOverflow(tester, where: ' after marking');
    });

    for (final view in ['Week', 'Month']) {
      testWidgets("the $view view fits with the day's lessons under the calendar at $name", (tester) async {
        await pumpPage(tester, const MySchedulePage(), size);
        await tester.tap(find.text(view));
        await tester.pumpAndSettle();
        expectNoOverflow(tester, where: ' on the $view view');

        // Under a month grid on a short screen the list may need a scroll;
        // the lesson must then be reachable and tappable.
        await tester.scrollUntilVisible(find.text(_secondLesson), 200, scrollable: find.byType(Scrollable).last);
        await tester.pumpAndSettle();
        expectActionReady(tester, _tappable(_secondLesson), size, label: 'a lesson under the $view calendar');
      });
    }
  }
}
