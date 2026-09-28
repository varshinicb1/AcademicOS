// Task 801: the principal's console at phone, tablet and laptop widths. All
// six tabs the console declares are driven here, not just the two the first
// pass covered (review of 2026-09-22): Roster (inviting teachers is how
// anyone joins a school), Master Calendar, Coverage & Pace, Sequence Reorder,
// Reschedule and Calendar & Setup. The four beyond Roster and Coverage are
// write surfaces -- date fields, grade/subject dropdowns, drag-to-reorder --
// so "read-only on a phone is acceptable" does not cover them and each is
// rendered and used at 375 px here.
//
// The Coverage & Pace dashboard is fed the payload
// GET /curriculum/reporting/coverage really returns
// (test/fixtures/coverage_report.json, drift-checked by
// tests/test_curriculum_coverage_fixture.py). On a phone the dashboard is for
// reading and the one action on it, Reschedule on an overdue lesson, must
// still be reachable, hit, and land on a Reschedule tab that also fits.
//
// Same technique as principal_coverage_tab_test.dart: a real Dio whose
// interceptor answers each path with the backend's response shape.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import 'responsive_harness.dart';

final _coverage = jsonDecode(File('test/fixtures/coverage_report.json').readAsStringSync());

Map<String, Object?> _delayedLesson(String id, String date, int days, String chapter, String subtopic) => {
      'lessonId': id,
      'scheduledDate': date,
      'daysOverdue': days,
      'gradeNumber': 7,
      'subjectName': 'Mathematics',
      'chapterName': chapter,
      'topicName': '$chapter basics',
      'subtopicName': subtopic,
      'teacherId': 'teacher_1',
      'teacherName': 'Tara Teacher',
    };

/// DelayedTopicsReportResponse (curriculum/schemas.py) for the fixture's
/// school: its two overdue Mathematics lessons.
final _delayed = {
  'schoolId': 'school_1',
  'academicYearId': 'academicYear_1',
  'asOfDate': '2026-09-14',
  'delayedCount': 2,
  'delayedLessons': [
    _delayedLesson('lesson_overdue_integers', '2026-09-03', 11, 'Integers', 'Integers part 3'),
    _delayedLesson('lesson_overdue_fractions', '2026-09-10', 4, 'Fractions', 'Fractions part 2'),
  ],
};

/// Today, as the backend spells a date. The Master Calendar opens on
/// DateTime.now(), so a lesson only lands on the open day if it carries
/// today's date -- a hard-coded one makes that tab permanently empty and the
/// test stops proving the lesson cards fit.
final _today = DateTime.now().toString().substring(0, 10);

Map<String, Object?> _lesson(String id, int period, String status, String subtopic) => {
      'id': id,
      'academicYearId': 'academicYear_1',
      'bookId': 'book:math:7',
      'subtopicId': 'subtopic:$subtopic',
      'scheduledDate': _today,
      'periodNumber': period,
      'status': status,
      'note': status == 'skipped' ? 'Teacher absent' : null,
    };

class _Backend extends Interceptor {
  /// Every request this fixture had no answer for, as "METHOD /path".
  ///
  /// Asserted empty after each test. Without it a tab that calls a route the
  /// fixture does not serve catches the DioException, renders an empty or
  /// error state, and passes every "fits and the action is ready" check --
  /// an empty tab overflows nothing. Six tabs load several endpoints each,
  /// so the odds of one silently 404ing are not small, and a silently wrong
  /// screen is worse than an error (review of 2026-09-23;
  /// quick_paper_responsive_test.dart already checked its fixture this way).
  final rejected = <String>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final path = options.path;
    Object? body;
    var status = 200;
    if (path == '/curriculum/schedule') {
      body = [
        _lesson('lesson_1', 1, 'completed', 'integers-part-1'),
        _lesson('lesson_2', 3, 'scheduled', 'integers-part-2'),
        _lesson('lesson_3', 5, 'skipped', 'fractions-part-1'),
      ];
    } else if (path.endsWith('/subjects')) {
      body = [
        {'id': 'subject_math_7', 'name': 'Mathematics'},
        {'id': 'subject_science_7', 'name': 'Science'},
      ];
    } else if (path.endsWith('/books')) {
      body = [
        {'id': 'book_math_7', 'subjectId': 'subject_math_7', 'title': 'Mathematics Grade 7'},
      ];
    } else if (path.endsWith('/selected-book')) {
      // The chosen edition (feat/product-calendar). Every tab that schedules,
      // assigns or reorders now asks for this before it asks for units or
      // chapters, so a fixture that does not serve it leaves those lists
      // empty -- which is what `rejected` exists to catch.
      final subjectId = path.split('/')[3];
      body = {
        'id': 'book_$subjectId', 'subjectId': subjectId, 'boardId': 'board_cbse',
        'title': subjectId == 'subject_science_7' ? 'Science Grade 7' : 'Mathematics Grade 7',
        'selected': true,
      };
    } else if (path.endsWith('/proposed-topics')) {
      // No chapter of this fixture has topics waiting for approval; the
      // pending-topics card on Sequence Reorder renders its empty state.
      body = <Object>[];
    } else if (path == '/curriculum/boards') {
      body = [
        {'id': 'board_cbse', 'name': 'CBSE'},
      ];
    } else if (path.endsWith('/units')) {
      body = [
        {'id': 'unit_1', 'canonicalId': 'u:math:7:1', 'bookId': 'book_math_7', 'unitNo': '1', 'name': 'Number System', 'marks': 20, 'seq': 0},
        {'id': 'unit_2', 'canonicalId': 'u:math:7:2', 'bookId': 'book_math_7', 'unitNo': '2', 'name': 'Algebra', 'marks': 15, 'seq': 1},
      ];
    } else if (path.endsWith('/chapters')) {
      body = [
        {'id': 'chapter_1', 'canonicalId': 'c:math:7:integers', 'unitId': 'unit_1', 'name': 'Integers', 'seq': 0},
        {'id': 'chapter_2', 'canonicalId': 'c:math:7:fractions', 'unitId': 'unit_1', 'name': 'Fractions and Decimals', 'seq': 1},
      ];
    } else if (path.endsWith('/calendar')) {
      body = {
        'id': 'calendar_1',
        'academicYearId': 'academicYear_1',
        'weeklyOffDays': ['sunday'],
        'alternateSaturdayRule': 'second_fourth',
      };
    } else if (path.endsWith('/working-days')) {
      body = {
        'academicYearId': 'academicYear_1',
        'totalDays': 304, 'workingDays': 243, 'weeklyOffCount': 44,
        'alternateSaturdayOffCount': 10, 'holidayCount': 7, 'dates': <String>[],
      };
    } else if (path.endsWith('/terms')) {
      // The Terms card on Calendar & Setup (audit D27).
      body = [
        {'id': 'term_1', 'schoolId': 'school_1', 'academicYearId': 'academicYear_1', 'name': 'Term 1',
         'startDate': '2026-06-01', 'endDate': '2026-09-30', 'manualBaselineMinutes': null},
      ];
    } else if (path.endsWith('/holidays')) {
      body = [
        {'id': 'holiday_1', 'calendarId': 'calendar_1', 'date': '2026-10-20', 'label': 'Diwali Vacation', 'kind': 'public', 'endDate': '2026-10-24'},
      ];
    } else if (path == '/curriculum/academic-years') {
      body = [
        {'id': 'academicYear_1', 'label': '2026-27', 'startDate': '2026-06-01', 'endDate': '2027-03-31'},
      ];
    } else if (path.endsWith('/grades')) {
      body = [
        {'id': 'grade_7', 'number': 7, 'section': null},
        {'id': 'grade_10', 'number': 10, 'section': null},
      ];
    } else if (path.endsWith('/sections')) {
      // Two sections of Class 10, so the Roster's Sections card is measured
      // with more than one row per class.
      body = [
        {'id': 'section_7a', 'academicYearId': 'academicYear_1', 'gradeId': 'grade_7', 'gradeNumber': 7,
          'name': 'A', 'classTeacherId': null, 'studentCount': 0},
        {'id': 'section_10a', 'academicYearId': 'academicYear_1', 'gradeId': 'grade_10', 'gradeNumber': 10,
          'name': 'A', 'classTeacherId': null, 'studentCount': 31},
        {'id': 'section_10b', 'academicYearId': 'academicYear_1', 'gradeId': 'grade_10', 'gradeNumber': 10,
          'name': 'Rose', 'classTeacherId': null, 'studentCount': 1},
      ];
    } else if (path == '/auth/users') {
      body = <Object>[];
    } else if (path == '/auth/invites') {
      body = [
        {
          'code': 'open-code-1234567890ab', 'role': 'teacher', 'email': 'new.science.teacher@school.example',
          'expiresAt': '2026-10-06T00:00:00+00:00', 'createdAt': '2026-09-22T00:00:00+00:00',
          'createdBy': 'u_principal', 'status': 'open', 'usedBy': null, 'usedAt': null, 'revokedAt': null,
        },
      ];
    } else if (path == '/curriculum/reporting/coverage') {
      body = _coverage;
    } else if (path == '/curriculum/reporting/delayed-topics') {
      body = _delayed;
    } else {
      status = 404;
      body = {'detail': 'not found'};
      rejected.add('${options.method} $path');
    }
    final response = Response(requestOptions: options, statusCode: status, data: body);
    if (status < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(statusCode: status, requestOptions: options, response: response));
    }
  }
}

Finder _button(String label) =>
    find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));

/// The console's tab strip scrolls sideways on a phone, so a tab has to be
/// scrolled to before it can be checked and tapped. [find.widgetWithText] and
/// not [find.text]: 'Reschedule' is both a tab and a button on the coverage
/// dashboard.
Future<void> _openTab(WidgetTester tester, String label, Screen size) async {
  final tab = find.widgetWithText(Tab, label);
  await tester.ensureVisible(tab);
  await tester.pumpAndSettle();
  expectActionReady(tester, tab, size, label: 'the $label tab');
  await tester.tap(tab);
  await tester.pumpAndSettle();
  expectNoOverflow(tester, where: ' on the $label tab');
}

/// The scrollable body of whichever tab is open. A tab's ListView builds its
/// cards lazily, so anything below the fold has to be scrolled to before it
/// exists to be found at all.
Finder _openTabList() => find.descendant(of: find.byType(TabBarView), matching: find.byType(Scrollable)).last;

/// Picks [option] from the DropdownButtonFormField labelled [label] the way a
/// principal does: tap the field, tap the item in the menu that opens.
///
/// byWidgetPredicate and not byType: these fields are generic
/// (DropdownButtonFormField<GradeSummary>), and byType matches on the exact
/// runtimeType, so it finds none of them.
Future<void> _pickFromDropdown(WidgetTester tester, String label, String option) async {
  final field = find.ancestor(
      of: find.text(label), matching: find.byWidgetPredicate((w) => w is DropdownButtonFormField));
  await tester.ensureVisible(field.first);
  await tester.pumpAndSettle();
  await tester.tap(field.first);
  await tester.pumpAndSettle();
  // The menu paints its own copy of every item over the field's; the last
  // match is the one in the open menu.
  await tester.tap(find.text(option).last);
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useAppFonts();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('responsive_principal_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });
  tearDownAll(() async => Hive.close());

  late _Backend backend;
  setUp(() async {
    // Awaited: an unawaited clear() lands after the writes below and wipes them.
    await LocalStore.instance.box.clear();
    LocalStore.instance.authUser = {
      'id': 'u_principal',
      'schoolId': 'school_1',
      'name': 'Principal',
      'email': 'principal@school.invalid',
      'role': 'principal',
    };
    backend = _Backend();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(backend);
    GetIt.I
      ..registerSingleton<CurriculumApi>(CurriculumApi(dio))
      ..registerSingleton<AuthApi>(AuthApi(dio));
  });
  tearDown(() {
    // Before the reset, so a tab that quietly fell back to an empty state
    // fails the test that was meant to prove it fits. See [_Backend.rejected].
    expect(backend.rejected, isEmpty,
        reason: 'the console asked for routes this fixture does not serve, so whatever those calls fill '
            'was empty or errored on the screen this test just measured');
    GetIt.I.reset();
  });

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('the Roster tab fits and Create invite is ready at $name', (tester) async {
      await pumpPage(tester, const PrincipalAdminPage(), size);
      expectNoOverflow(tester, where: ' on the Roster tab');
      expect(find.textContaining('open-code-1234567890ab'), findsOneWidget);
      await scrollToAndExpectReady(tester, _button('Create invite'), size, label: 'Create invite');
      await scrollToAndExpectReady(tester, _button('Withdraw'), size, label: 'Withdraw');
      expectNoOverflow(tester, where: ' after scrolling the Roster tab');
    });

    testWidgets('the Coverage & Pace dashboard fits and Reschedule is reachable at $name', (tester) async {
      await pumpPage(tester, const PrincipalAdminPage(), size);
      // The tab row scrolls sideways on a phone; the tab must still be hit.
      final tab = find.text('Coverage & Pace');
      await tester.ensureVisible(tab);
      await tester.pumpAndSettle();
      expectActionReady(tester, find.ancestor(of: tab, matching: find.byType(Tab)), size,
          label: 'the Coverage & Pace tab');
      await tester.tap(tab);
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' on the Coverage & Pace tab');
      expect(find.text('33.3%'), findsOneWidget);
      expect(find.text('22.2%'), findsOneWidget);
      expect(find.textContaining('Grade 7 · Mathematics'), findsOneWidget);

      // A subject opened to its chapters.
      await tester.tap(find.textContaining('Grade 7 · Mathematics'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' with a subject opened');

      // The delayed lessons are below the subject cards; the list builds them
      // lazily, so scroll the dashboard itself rather than the tab strip.
      final dashboard = find.descendant(of: find.byType(RefreshIndicator), matching: find.byType(Scrollable)).first;
      await scrollUntilPresent(tester, find.widgetWithText(TextButton, 'Reschedule'), dashboard);
      await scrollToAndExpectReady(tester, find.widgetWithText(TextButton, 'Reschedule').first, size,
          label: 'Reschedule on an overdue lesson');
      expectNoOverflow(tester, where: ' at the delayed lessons');

      if (size.size.width > phone.width) {
        // The heading is Flexible (loose), not Expanded (tight): a tight fit
        // makes "Delayed Topics" swallow the whole row and throws its
        // "2 overdue" chip out to the card's right edge, 1 000 px from the
        // heading it counts, on a laptop (review of 2026-09-22). Loose leaves
        // the heading its natural width wherever the pair fits.
        await scrollUntilPresent(tester, find.text('Delayed Topics'), dashboard);
        final chip = tester.getRect(find.text('2 overdue'));
        expect(chip.left, lessThan(size.size.width / 2),
            reason: 'the overdue chip starts at ${chip.left.toStringAsFixed(0)} on a '
                '${size.size.width.toInt()} px screen: it must stay beside the heading it counts, in the '
                'left half of the card, not out at the right-hand edge');
      }

      // The one phone action on the dashboard navigates to the Reschedule
      // tab with the lesson id filled in. Tapping it is only useful if the
      // screen it lands on also fits the phone, so follow it through.
      await tester.tap(find.widgetWithText(TextButton, 'Reschedule').first);
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' after Reschedule opened the Reschedule tab');
      await scrollUntilPresent(tester, _button('Reschedule Single Lesson'), _openTabList());
      await scrollToAndExpectReady(tester, _button('Reschedule Single Lesson'), size,
          label: 'Reschedule Single Lesson');
      expect(find.text('lesson_overdue_integers'), findsOneWidget,
          reason: 'Reschedule must carry the overdue lesson id into the Lesson ID field');
    });

    testWidgets('the Master Calendar tab fits and its day can be changed at $name', (tester) async {
      await pumpPage(tester, const PrincipalAdminPage(), size);
      await _openTab(tester, 'Master Calendar', size);

      // The three status tallies and the day's lessons, as the school sees them.
      expect(find.text('Completed'), findsOneWidget);
      expect(find.text('Skipped'), findsOneWidget);
      expect(find.textContaining('Lessons for $_today (3)'), findsOneWidget);
      expect(find.textContaining('Period 1'), findsOneWidget);

      // Changing the day is this tab's primary action: the date button and the
      // two arrows either side of it.
      await scrollToAndExpectReady(tester, _button('Date: $_today'), size, label: 'the date picker button');
      await scrollToAndExpectReady(tester, find.widgetWithIcon(IconButton, Icons.chevron_right), size,
          label: 'the next-day arrow');
      await tester.tap(find.widgetWithIcon(IconButton, Icons.chevron_right));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' after stepping the Master Calendar a day on');
    });

    testWidgets('the Sequence Reorder tab fits and can be driven at $name', (tester) async {
      await pumpPage(tester, const PrincipalAdminPage(), size);
      await _openTab(tester, 'Sequence Reorder', size);

      await _pickFromDropdown(tester, 'Select Grade', 'Grade 7');
      expectNoOverflow(tester, where: ' after picking a grade on Sequence Reorder');
      await _pickFromDropdown(tester, 'Select Subject', 'Mathematics');
      expectNoOverflow(tester, where: ' after picking a subject on Sequence Reorder');

      // The units list and the two-segment switch above it -- the widest fixed
      // row on this tab, and the only way to reach the chapters list.
      expect(find.text('Number System'), findsOneWidget);
      await scrollToAndExpectReady(tester, find.widgetWithText(SegmentedButton<int>, 'Chapters Sequence'), size,
          label: 'the Units/Chapters switch');
      await tester.tap(find.text('Chapters Sequence'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' with the chapters sequence shown');
      expect(find.text('Fractions and Decimals'), findsOneWidget);
    });

    testWidgets('the Reschedule tab fits and both its actions are ready at $name', (tester) async {
      await pumpPage(tester, const PrincipalAdminPage(), size);
      await _openTab(tester, 'Reschedule', size);

      // PUSH needs a grade and a subject before it can run.
      await _pickFromDropdown(tester, 'Grade', 'Grade 7');
      expectNoOverflow(tester, where: ' after picking a grade on Reschedule');
      await _pickFromDropdown(tester, 'Subject', 'Mathematics');
      expectNoOverflow(tester, where: ' after picking a subject on Reschedule');

      await scrollToAndExpectReady(tester, _button('Push Subsequent Lessons'), size,
          label: 'Push Subsequent Lessons');
      await scrollUntilPresent(tester, _button('Reschedule Single Lesson'), _openTabList());
      await scrollToAndExpectReady(tester, _button('Reschedule Single Lesson'), size,
          label: 'Reschedule Single Lesson');
      expectNoOverflow(tester, where: ' after scrolling the Reschedule tab');
    });

    testWidgets('the Calendar & Setup tab fits and its four actions are ready at $name', (tester) async {
      await pumpPage(tester, const PrincipalAdminPage(), size);
      await _openTab(tester, 'Calendar & Setup', size);

      await scrollToAndExpectReady(tester, _button('Update Calendar'), size, label: 'Update Calendar');
      await scrollUntilPresent(tester, _button('Add term'), _openTabList());
      expect(find.byKey(const ValueKey('term-term_1')), findsOneWidget);
      await scrollToAndExpectReady(tester, _button('Add term'), size, label: 'Add term');
      await scrollUntilPresent(tester, _button('Save Period Duration'), _openTabList());
      await scrollToAndExpectReady(tester, _button('Save Period Duration'), size, label: 'Save Period Duration');
      await scrollUntilPresent(tester, _button('Add Holiday'), _openTabList());
      await scrollToAndExpectReady(tester, _button('Add Holiday'), size, label: 'Add Holiday');

      // The saved calendar's computed teaching days and its holidays, at the
      // foot of the tab -- the widest rows on it.
      await scrollUntilPresent(tester, find.textContaining('Working Days: 243'), _openTabList());
      // The whole line, not just the label: 'Diwali Vacation' also appears in
      // the Add Holiday field's hint.
      expect(find.text('• 2026-10-20 to 2026-10-24: Diwali Vacation (public)'), findsOneWidget);
      expectNoOverflow(tester, where: ' after scrolling the Calendar & Setup tab');
    });
  }

  testWidgets('in a desktop-UA browser at phone width Reschedule is still 44 px tall', (tester) async {
    // Reschedule on an overdue lesson is the one action on the coverage
    // dashboard, and it is a TextButton -- M3 gives those a 64x40 minimum,
    // so it carries its own minimumSize. That minimum is reduced by the
    // theme's visual density, and a desktop browser narrowed to 375 px (how
    // this task's screenshots were taken) gets `compact`, -8 px in each
    // direction: without the button's own visualDensity it renders 36 px
    // tall there. flutter_test pins the platform to android, so no other
    // test in this file can see it (review of 2026-09-23).
    await withDesktopDensity(() async {
      await pumpPage(tester, const PrincipalAdminPage(), phoneScreen);
      final tab = find.text('Coverage & Pace');
      await tester.ensureVisible(tab);
      await tester.pumpAndSettle();
      await tester.tap(tab);
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' on the Coverage & Pace tab at a desktop density');

      final dashboard = find.descendant(of: find.byType(RefreshIndicator), matching: find.byType(Scrollable)).first;
      await scrollUntilPresent(tester, find.widgetWithText(TextButton, 'Reschedule'), dashboard);
      await scrollToAndExpectReady(tester, find.widgetWithText(TextButton, 'Reschedule').first, phoneScreen,
          label: 'Reschedule on a desktop density');
    });
  });

  testWidgets('on a laptop Create invite keeps the compact height the desktop console ships', (tester) async {
    // The console is where the width-blind tap-target style did most of its
    // damage: fourteen of the roughly fifteen actions it silently grew on a
    // 1280 px screen are on these six tabs (review of 2026-09-23). Create
    // invite stands for the family -- same FilledButton metrics as Withdraw,
    // Update Calendar, Add Holiday and the rest -- and is measured against a
    // bare FilledButton pumped in the same theme at the same density.
    await withDesktopDensity(() async {
      final shipped = await themeButtonHeight(tester, laptopScreen);
      await pumpPage(tester, const PrincipalAdminPage(), laptopScreen);
      expectNoOverflow(tester, where: ' on the Roster tab at a laptop width');
      final create = tester.getRect(paintedTarget(tester, _button('Create invite'))).height;
      expect(create, shipped,
          reason: 'Create invite draws ${create.toStringAsFixed(0)} px tall on a 1280 px screen; an '
              'unstyled button in the same theme draws ${shipped.toStringAsFixed(0)} px. Task 801 asks '
              'for 44 px targets on the phone layout, not on a laptop.');
    });
  });
}
