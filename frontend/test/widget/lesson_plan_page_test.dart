// Lesson plans (SCH-4, audit N-3-1 / N-67-5): a section's dated plan for one
// subject, made on the web. Until this page frontend/lib had no call to
// `teaching-time-estimates` or `POST /books/{id}/schedule`, so a school set up
// on the web had 0 lessons and "Today's lessons" was always empty.
//
// The fake backend answers in the server's shapes (curriculum/schemas.py) and
// records what the page sends: the estimates are sized from the section's own
// allocation, and the plan is the section's (`sectionId`), made again with
// `force` when one exists. Every layout is checked at 390 and 1280 px.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/lesson_plan_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

const _narrow = (size: Size(390, 844), textScale: 1.0);
const _narrowLarge = (size: Size(390, 844), textScale: 1.3);
const _wide = (size: Size(1280, 800), textScale: 1.0);

class _Backend implements HttpClientAdapter {
  final List<(String, String, Map<String, dynamic>, dynamic)> sent = [];
  final rejected = <String>[];
  List<Map<String, dynamic>> lessons = [];
  ({int status, Object body})? estimatesAnswer;

  static const _json = {Headers.contentTypeHeader: ['application/json']};
  ResponseBody _ok(Object body) => ResponseBody.fromString(jsonEncode(body), 200, headers: _json);
  ResponseBody _err(int status, String detail) =>
      ResponseBody.fromString(jsonEncode({'detail': detail}), status, headers: _json);

  Map<String, dynamic> _lesson(int i, String status) => {
        'id': 'les_$i', 'schoolId': 'school_1', 'academicYearId': 'ay_1', 'bookId': 'book_sci',
        'subtopicId': i.isEven ? 'st_1' : 'st_2', 'date': '2026-10-${(i + 1).toString().padLeft(2, '0')}',
        'status': status, 'createdAt': '2026-09-30T08:00:00Z', 'sectionId': 'sec_a',
      };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    final path = o.path;
    if (o.method != 'GET') sent.add((o.method, path, Map<String, dynamic>.from(o.queryParameters), o.data));
    switch ((o.method, path)) {
      case ('GET', '/curriculum/academic-years'):
        return _ok([{'id': 'ay_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'}]);
      case ('GET', '/curriculum/academic-years/ay_1/sections'):
        return _ok([
          {'id': 'sec_a', 'gradeId': 'g10', 'gradeNumber': 10, 'name': 'A', 'academicYearId': 'ay_1', 'studentCount': 30},
          {'id': 'sec_b', 'gradeId': 'g10', 'gradeNumber': 10, 'name': 'B', 'academicYearId': 'ay_1', 'studentCount': 28},
        ]);
      case ('GET', '/curriculum/academic-years/ay_1/allocations'):
        return _ok([
          {'id': 'al_1', 'academicYearId': 'ay_1', 'sectionId': 'sec_a', 'subjectId': 'sci', 'teacherId': 't_ana',
            'periodsPerWeek': 6, 'coTeacherId': null, 'roomKind': null, 'doublePeriods': 0},
        ]);
      case ('GET', '/curriculum/grades/g10/subjects'):
        return _ok([
          {'id': 'sci', 'gradeId': 'g10', 'name': 'Science'},
          {'id': 'mat', 'gradeId': 'g10', 'name': 'Maths'},
        ]);
      case ('GET', '/curriculum/subjects/sci/selected-book'):
        return _ok({'id': 'book_sci', 'subjectId': 'sci', 'boardId': 'cbse', 'title': 'Science - Textbook for Class X',
          'publisher': 'NCERT', 'status': 'ready', 'selected': true});
      case ('GET', '/curriculum/subjects/mat/selected-book'):
        return _err(404, 'this subject has no book, or several and none chosen: choose its edition first');
      case ('GET', '/curriculum/books/book_sci/chapters'):
        return _ok([
          {'id': 'ch_1', 'canonicalId': 'c1', 'unitId': 'u1', 'name': 'Chemical Reactions and Equations', 'seq': 1},
          {'id': 'ch_2', 'canonicalId': 'c2', 'unitId': 'u1', 'name': 'Light - Reflection and Refraction', 'seq': 2},
        ]);
      case ('GET', '/curriculum/chapters/ch_1/topics'):
        return _ok([
          {'id': 't_1', 'canonicalId': 't1', 'chapterId': 'ch_1', 'name': 'Chemical equations', 'seq': 1,
            'sourceType': 'template', 'subtopics': [
              {'id': 'st_1', 'canonicalId': 's1', 'topicId': 't_1', 'name': 'Balancing a chemical equation', 'seq': 1,
                'sourceType': 'template'},
              {'id': 'st_2', 'canonicalId': 's2', 'topicId': 't_1', 'name': 'Types of chemical reactions', 'seq': 2,
                'sourceType': 'template'},
            ]},
        ]);
      case ('GET', '/curriculum/chapters/ch_2/topics'):
        return _ok([]);
      case ('GET', '/curriculum/books/book_sci/schedule'):
        return _ok(lessons);
      case ('POST', '/curriculum/books/book_sci/teaching-time-estimates'):
        final a = estimatesAnswer;
        if (a != null) return ResponseBody.fromString(jsonEncode(a.body), a.status, headers: _json);
        return _ok({
          'academicYearId': 'ay_1', 'bookId': 'book_sci', 'periodsPerWeek': 6, 'periodMinutes': 40,
          'calendarWeeks': 52, 'totalSubjectPeriods': 12, 'totalInstructionalMinutes': 480,
          'unitsSkippedNoSubtopics': ['Unit 3: Natural Phenomena'], 'estimatesCreated': 2,
          'periodsAllocated': 14, 'periodsShort': 2, 'fitsInYear': false,
        });
      case ('POST', '/curriculum/books/book_sci/schedule'):
        lessons = [for (var i = 0; i < 12; i++) _lesson(i, 'scheduled')];
        return _ok({
          'academicYearId': 'ay_1', 'bookId': 'book_sci', 'periodsPerWeek': 6, 'teachingDaysAvailable': 12,
          'lessonsCreated': 12, 'subtopicsScheduled': 1, 'subtopicsPartiallyScheduled': <String>[],
          'subtopicsUnscheduled': ['st_2'], 'subtopicsWithoutEstimate': <String>[],
          'firstScheduledDate': '2026-10-01', 'lastScheduledDate': '2026-10-12', 'teachingPeriodsAvailable': 12,
          'lessonsKept': 0, 'pastLessonsKept': 0, 'allSubtopicsScheduled': false,
          'warning': '1 of 2 subtopics have no date: the year has 12 Science periods left and the estimates need 14.',
          'sectionId': 'sec_a',
        });
    }
    rejected.add('${o.method} $path');
    return _err(404, 'no route ${o.method} $path');
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('lesson_plan_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
  });

  tearDown(() async {
    expect(backend.rejected, isEmpty, reason: 'the page called a route the fake does not serve');
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('lesson_plan_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> choose(WidgetTester tester, Finder field, String item) async {
    await tester.ensureVisible(field);
    await tester.tap(field);
    await tester.pumpAndSettle();
    await tester.tap(find.text(item).last);
    await tester.pumpAndSettle();
  }

  Future<void> pickScience(WidgetTester tester) async {
    await choose(tester, find.byKey(const ValueKey('plan-section')), '10-A');
    await choose(tester, find.byKey(const ValueKey('plan-subject-sec_a')), 'Science · 6 a week');
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  testWidgets('the book, its chapters and which of them can be planned are shown', (tester) async {
    await pumpPage(tester, const LessonPlanPage(), _narrow);
    await pickScience(tester);
    expect(find.text('Science - Textbook for Class X'), findsOneWidget);
    expect(find.text('10-A: no plan yet.'), findsOneWidget);
    expect(find.text('6 periods a week, from the allocation'), findsOneWidget);
    expect(find.text('Chapters (1 of 2 ready to plan)'), findsOneWidget);
    expect(find.text('1 topics · 2 subtopics'), findsOneWidget);
    expect(find.text('no approved subtopics'), findsOneWidget);
    expect(find.textContaining('chapters have no approved subtopics'), findsOneWidget);
    expect(find.text('Make the plan'), findsOneWidget);
  });

  testWidgets('making the plan times the subtopics from the allocation, then dates the section\'s lessons',
      (tester) async {
    await pumpPage(tester, const LessonPlanPage(), _narrow);
    await pickScience(tester);
    await tapKey(tester, 'plan-make');

    final (m1, p1, q1, b1) = backend.sent[0];
    expect((m1, p1), ('POST', '/curriculum/books/book_sci/teaching-time-estimates'));
    expect(q1, {'academic_year_id': 'ay_1'});
    expect(b1, {'periodsPerWeek': 6}, reason: "the section's own allocation, not a school-wide one");
    final (m2, p2, q2, b2) = backend.sent[1];
    expect((m2, p2), ('POST', '/curriculum/books/book_sci/schedule'));
    expect(q2, {'academic_year_id': 'ay_1'});
    expect(b2, {'sectionId': 'sec_a', 'force': false});

    // The result: what was dated, and every subtopic left without a date, by name.
    expect(find.text('12 lessons dated, 2026-10-01 to 2026-10-12.'), findsOneWidget);
    expect(find.textContaining('the year has 12 Science periods left'), findsOneWidget);
    expect(find.textContaining('1 subtopics have no date'), findsOneWidget);
    expect(find.text('• Chemical Reactions and Equations: Types of chemical reactions'), findsOneWidget);
    expect(find.text('• Unit 3: Natural Phenomena'), findsOneWidget);
    expect(find.text('The subtopics need 14 periods; the year has 12.'), findsOneWidget);
    // The plan on the page is re-read: the section now has one.
    expect(find.textContaining('10-A: 12 lessons, 2026-10-01 to 2026-10-12'), findsOneWidget);
    expect(find.text('Make the plan again'), findsOneWidget);
  });

  testWidgets('a section that already has a plan is planned again with force', (tester) async {
    backend.lessons = [for (var i = 0; i < 3; i++) backend._lesson(i, i == 0 ? 'completed' : 'scheduled')];
    await pumpPage(tester, const LessonPlanPage(), _narrow);
    await pickScience(tester);
    expect(find.textContaining('1 taught · 0 not taught'), findsOneWidget);
    expect(find.textContaining('Making the plan again keeps every lesson marked taught'), findsOneWidget);
    await tapKey(tester, 'plan-make');
    expect(backend.sent[1].$4, {'sectionId': 'sec_a', 'force': true});
  });

  testWidgets("the server's refusal is shown, and nothing is claimed", (tester) async {
    backend.estimatesAnswer = (status: 404, body: {
      'detail': 'academic year ay_1 has no period configuration set yet -- create one first (POST .../period-configuration)'
    });
    await pumpPage(tester, const LessonPlanPage(), _narrow);
    await pickScience(tester);
    await tapKey(tester, 'plan-make');
    expect(find.byKey(const ValueKey('plan-error')), findsOneWidget);
    expect(find.textContaining('has no period configuration set yet'), findsOneWidget);
    expect(find.byKey(const ValueKey('plan-result')), findsNothing);
    expect(backend.sent.length, 1, reason: 'no schedule without estimates');
  });

  testWidgets('a subject with no chosen book, or no periods, cannot be planned', (tester) async {
    await pumpPage(tester, const LessonPlanPage(), _narrow);
    await choose(tester, find.byKey(const ValueKey('plan-section')), '10-A');
    await choose(tester, find.byKey(const ValueKey('plan-subject-sec_a')), 'Maths · no periods set');
    expect(find.byKey(const ValueKey('plan-no-book')), findsOneWidget);
    expect(find.byKey(const ValueKey('plan-make')), findsNothing);

    await choose(tester, find.byKey(const ValueKey('plan-section')), '10-B');
    await choose(tester, find.byKey(const ValueKey('plan-subject-sec_b')), 'Science · no periods set');
    expect(find.text('Set who teaches it and how many periods a week first.'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('plan-make'))).onPressed, isNull);
  });

  for (final (name, screen) in [('390 px', _narrow), ('390 px at 1.3x text', _narrowLarge), ('1280 px', _wide)]) {
    testWidgets('nothing overflows at $name, before and after a plan is made', (tester) async {
      await pumpPage(tester, const LessonPlanPage(), screen);
      expectNoOverflow(tester, where: ' on the empty page');
      await pickScience(tester);
      expectNoOverflow(tester, where: ' with the book shown');
      await scrollToAndExpectReady(tester, find.byKey(const ValueKey('plan-make')), screen, label: 'Make the plan');
      await tester.tap(find.byKey(const ValueKey('plan-make')));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' with the result shown');
    });
  }
}
