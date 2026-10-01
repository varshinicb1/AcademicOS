// The Timetable page (SCH-2/3, SCH-8, ADM-1): allocations with a co-teacher,
// a lab and double periods; rooms and when one is out of use; the bell typed
// as lines; the periods a teacher cannot teach; generating with a preview
// before publishing; a section's week, edited by hand with periods locked and
// every clash the server finds listed (audit N-3-5).
//
// Until this page the school's timetable could be set only through the API
// or a CSV import: the web had no allocation grid, no bell, no rooms and no
// way to run the solver. The fake backend answers in the server's shapes and
// records what the page sends.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/timetable_admin_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';
import '../support/semantics_labels.dart';

const _phone = Size(375, 812);

class _Backend implements HttpClientAdapter {
  final List<(String, String, dynamic)> sent = [];
  Map<String, dynamic> solveAnswer = {
    'status': 'solved', 'applied': false, 'problems': <String>[], 'kept': 40, 'movedOrAdded': 4,
    'removed': 2, 'seconds': 1.5, 'entries': <dynamic>[],
  };
  int? roomClosureStatus;
  bool weekClash = false;

  static const _json = {Headers.contentTypeHeader: ['application/json']};

  ResponseBody _ok(Object body) => ResponseBody.fromString(jsonEncode(body), 200, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    final path = o.path;
    if (o.method != 'GET') sent.add((o.method, path, o.data));
    switch ((o.method, path)) {
      case ('GET', '/curriculum/academic-years'):
        return _ok([{'id': 'ay_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'}]);
      case ('GET', '/curriculum/academic-years/ay_1/sections'):
        return _ok([
          {'id': 'sec_a', 'gradeId': 'g10', 'gradeNumber': 10, 'name': 'A', 'academicYearId': 'ay_1', 'studentCount': 30},
          {'id': 'sec_b', 'gradeId': 'g10', 'gradeNumber': 10, 'name': 'B', 'academicYearId': 'ay_1', 'studentCount': 28},
        ]);
      case ('GET', '/staff'):
        return _ok([
          {'id': 't_ana', 'name': 'Ana', 'role': 'teacher'},
          {'id': 't_dev', 'name': 'Dev', 'role': 'teacher'},
        ]);
      case ('GET', '/curriculum/grades/g10/subjects'):
        return _ok([
          {'id': 'sci', 'gradeId': 'g10', 'name': 'Science'},
          {'id': 'mat', 'gradeId': 'g10', 'name': 'Maths'},
        ]);
      case ('GET', '/curriculum/academic-years/ay_1/allocations'):
        return _ok([
          {'id': 'al_1', 'academicYearId': 'ay_1', 'sectionId': 'sec_a', 'subjectId': 'sci', 'teacherId': 't_ana',
            'periodsPerWeek': 6, 'coTeacherId': null, 'roomKind': 'lab', 'doublePeriods': 1},
        ]);
      case ('PUT', '/curriculum/sections/sec_a/allocations/sci'):
        return _ok({'id': 'al_1', 'academicYearId': 'ay_1', 'sectionId': 'sec_a', 'subjectId': 'sci',
          ...Map<String, dynamic>.from(o.data as Map)});
      case ('GET', '/curriculum/rooms'):
        return _ok([
          {'id': 'room_lab', 'name': 'Lab 1', 'kind': 'lab', 'capacity': 40},
          {'id': 'room_1', 'name': 'Room 1', 'kind': 'classroom', 'capacity': null},
        ]);
      case ('GET', '/curriculum/academic-years/ay_1/room-unavailability'):
        return _ok([
          {'roomId': 'room_lab', 'slots': [{'dayOfWeek': 0, 'period': 1}]},
        ]);
      case ('POST', '/curriculum/rooms'):
        return _ok({'id': 'room_new', ...Map<String, dynamic>.from(o.data as Map)});
      case ('PUT', '/curriculum/academic-years/ay_1/room-unavailability/room_lab'):
        if (roomClosureStatus != null) {
          return ResponseBody.fromString(
              jsonEncode({'detail': 'the timetable uses this room then: Monday period 2 (10-A); move those periods first'}),
              roomClosureStatus!, headers: _json);
        }
        return _ok({'roomId': 'room_lab', ...Map<String, dynamic>.from(o.data as Map)});
      case ('GET', '/curriculum/academic-years/ay_1/bell-schedules'):
        return _ok([
          {'id': 'bell_1', 'academicYearId': 'ay_1', 'name': 'Main', 'days': [0, 1, 2, 3, 4, 5], 'isDefault': true,
            'teachingPeriods': 2, 'slots': [
              {'start': '08:00', 'end': '08:45', 'kind': 'teaching', 'period': 1},
              {'start': '08:45', 'end': '09:05', 'kind': 'break', 'period': null},
              {'start': '09:05', 'end': '09:50', 'kind': 'teaching', 'period': 2},
            ]},
        ]);
      case ('POST', '/curriculum/academic-years/ay_1/bell-schedules'):
        return _ok({'id': 'bell_2', ...Map<String, dynamic>.from(o.data as Map)});
      case ('POST', '/curriculum/academic-years/ay_1/timetable/solve'):
        final apply = (o.data as Map)['apply'] == true;
        return _ok({...solveAnswer, 'applied': apply && solveAnswer['status'] == 'solved'});
      case ('PUT', '/curriculum/sections/sec_a/timetable'):
        if (weekClash) {
          return ResponseBody.fromString(jsonEncode({'detail': {
            'message': 'the timetable has clashes; nothing was changed',
            'clashes': [
              'Tuesday period 2: the teacher already teaches 10-B then',
              'Science gets 7 periods a week here but is allocated 6',
            ],
          }}), 409, headers: _json);
        }
        final entries = ((o.data as Map)['entries'] as List).cast<Map>();
        return _ok({
          'sectionId': 'sec_a', 'bellScheduleId': 'bell_1',
          'entries': [
            for (final (i, e) in entries.indexed)
              {'id': 'tt_new_$i', 'sectionId': 'sec_a', ...e, 'teacherId': e['teacherId'] ?? 't_ana',
                'coTeacherId': null, 'subjectName': 'Science', 'teacherName': 'Ana'},
          ],
          'gaps': <dynamic>[],
        });
      case ('GET', '/curriculum/academic-years/ay_1/teacher-unavailability'):
        return _ok([
          {'teacherId': 't_ana', 'slots': [{'dayOfWeek': 0, 'period': 1}, {'dayOfWeek': 0, 'period': 2}]},
        ]);
      case ('PUT', '/curriculum/academic-years/ay_1/teacher-unavailability/t_dev'):
        return _ok({'teacherId': 't_dev', ...Map<String, dynamic>.from(o.data as Map)});
      case ('GET', '/curriculum/sections/sec_a/timetable'):
        return _ok({
          'sectionId': 'sec_a', 'bellScheduleId': 'bell_1',
          'entries': [
            {'id': 'tt_1', 'sectionId': 'sec_a', 'dayOfWeek': 0, 'period': 1, 'subjectId': 'sci', 'teacherId': 't_ana',
              'coTeacherId': 't_dev', 'roomId': 'room_lab', 'locked': false, 'subjectName': 'Science',
              'teacherName': 'Ana', 'coTeacherName': 'Dev', 'roomName': 'Lab 1', 'sectionName': '10-A'},
          ],
          'gaps': [{'subjectId': 'sci', 'allocated': 6, 'timetabled': 1}],
        });
    }
    return ResponseBody.fromString(jsonEncode({'detail': 'no route ${o.method} $path'}), 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('timetable_page_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    // Bounded, as test/support/real_di.dart does: hive's close can wait on a
    // lock another test file left behind (the known lock-queue flake).
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('timetable_admin_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  group('the bell typed as lines', () {
    test('teaching periods, breaks, and a single-digit hour', () {
      expect(parseBellSlots('8:00-8:45\n08:45 - 09:05 break\n\n09:05-09:50').slots, [
        {'start': '08:00', 'end': '08:45', 'kind': 'teaching'},
        {'start': '08:45', 'end': '09:05', 'kind': 'break'},
        {'start': '09:05', 'end': '09:50', 'kind': 'teaching'},
      ]);
    });
    test('a line that is not a slot is named', () {
      expect(parseBellSlots('08:00-08:45\nlunch').error, startsWith('Line 2'));
      expect(parseBellSlots('  \n').error, startsWith('Add at least one slot'));
    });
    test('a bell reads back as the same lines', () {
      const text = '08:00-08:45\n08:45-09:05 break\n09:05-09:50';
      expect(bellSlotsText(parseBellSlots(text).slots), text);
    });
  });

  Future<void> pump(WidgetTester tester) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: TimetableAdminPage()));
    await tester.pumpAndSettle();
  }

  Future<void> openTab(WidgetTester tester, String name) async {
    // The tab strip scrolls at phone width: bring the tab into view first.
    final tab = find.widgetWithText(Tab, name);
    await tester.ensureVisible(tab);
    await tester.pumpAndSettle();
    await tester.tap(tab);
    await tester.pumpAndSettle();
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  Future<void> choose(WidgetTester tester, String key, String item) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
    await tester.tap(find.text(item).last);
    await tester.pumpAndSettle();
  }

  testWidgets('a subject is given a co-teacher, keeping its lab and double period', (tester) async {
    await pump(tester);
    await choose(tester, 'alloc-section', '10-A');
    expect(find.text('Science'), findsOneWidget);
    expect(find.text('Maths'), findsOneWidget);
    expect(tester.takeException(), isNull, reason: 'the grid fits a phone');

    await choose(tester, 'alloc-co-sci', 'Dev');
    await tapKey(tester, 'alloc-save-sci');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('PUT', '/curriculum/sections/sec_a/allocations/sci'));
    expect(body, {'teacherId': 't_ana', 'periodsPerWeek': 6, 'coTeacherId': 't_dev', 'roomKind': 'lab', 'doublePeriods': 1});
    expect(find.text('Saved'), findsOneWidget);
  });

  testWidgets('a screen reader hears each allocation field by name (QA S-22)', (tester) async {
    final semantics = tester.ensureSemantics();
    await pump(tester);
    await choose(tester, 'alloc-section', '10-A');
    expect(textFieldLabels(tester), containsAll(['Periods a week', 'Double periods']));
    for (final label in ['Teacher', 'Co-teacher', 'Needs a room']) {
      expect(find.bySemanticsLabel(RegExp('^$label')), findsWidgets, reason: label);
    }
    semantics.dispose();
  });

  testWidgets('more double periods than the week holds is caught before sending', (tester) async {
    await pump(tester);
    await choose(tester, 'alloc-section', '10-A');
    await tester.enterText(find.byKey(const ValueKey('alloc-doubles-sci')), '4');
    await tapKey(tester, 'alloc-save-sci');
    expect(find.text('Double periods take two periods each, within the periods a week.'), findsOneWidget);
    expect(backend.sent, isEmpty);
  });

  testWidgets('a preview shows the changes and publishing sends apply', (tester) async {
    await pump(tester);
    await openTab(tester, 'Generate');
    final publish = find.byKey(const ValueKey('solve-publish'));
    expect(tester.widget<FilledButton>(publish).onPressed, isNull, reason: 'nothing to publish before a preview');
    await tapKey(tester, 'solve-preview');
    expect(find.text('A week that meets every rule:'), findsOneWidget);
    expect(find.textContaining('keeps 40, moves or adds 4, removes 2 periods'), findsOneWidget);
    expect((backend.sent.single.$3 as Map)['apply'], isFalse);

    await tapKey(tester, 'solve-publish');
    expect((backend.sent.last.$3 as Map)['apply'], isTrue);
    expect(find.text('Published. Teachers have been told.'), findsOneWidget);
  });

  testWidgets('a week no timetable can meet lists why and cannot be published', (tester) async {
    backend.solveAnswer = {
      'status': 'infeasible', 'applied': false, 'kept': 0, 'movedOrAdded': 0, 'removed': 0, 'seconds': 0.1,
      'entries': <dynamic>[],
      'problems': ['Science for 10-A needs a lab and the school has none: add one under Rooms, or clear the subject\'s room kind'],
    };
    await pump(tester);
    await openTab(tester, 'Generate');
    await tapKey(tester, 'solve-preview');
    expect(find.text('No week can meet every rule yet:'), findsOneWidget);
    expect(find.textContaining('needs a lab and the school has none'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('solve-publish'))).onPressed, isNull);
  });

  testWidgets('rooms show their closures, and a refused closure says why', (tester) async {
    backend.roomClosureStatus = 409;
    await pump(tester);
    await openTab(tester, 'Rooms');
    expect(find.text('Lab 1'), findsOneWidget);
    expect(find.text('lab · 1 periods out of use'), findsOneWidget);
    await tester.tap(find.byTooltip('Out of use: Lab 1'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('closed-0-2')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('closed-save')));
    await tester.pumpAndSettle();
    final (_, _, body) = backend.sent.single;
    expect((body as Map)['slots'], containsAll([{'dayOfWeek': 0, 'period': 1}, {'dayOfWeek': 0, 'period': 2}]));
    expect(find.textContaining('the timetable uses this room then: Monday period 2 (10-A)'), findsOneWidget);
  });

  testWidgets('a room is added with its kind', (tester) async {
    await pump(tester);
    await openTab(tester, 'Rooms');
    await tapKey(tester, 'room-add');
    await tester.enterText(find.byKey(const ValueKey('room-name')), 'Chemistry lab');
    await tester.tap(find.byKey(const ValueKey('room-kind')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('lab').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('room-save')));
    await tester.pumpAndSettle();
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('POST', '/curriculum/rooms'));
    expect(body, {'name': 'Chemistry lab', 'kind': 'lab'});
  });

  testWidgets('a bell typed wrong is caught; typed right it is sent as slots', (tester) async {
    await pump(tester);
    await openTab(tester, 'Bell');
    expect(find.text('Main (default)'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('bell-name')), 'Junior');
    await tester.enterText(find.byKey(const ValueKey('bell-slots')), '08:00-08:40\nrecess');
    await tapKey(tester, 'bell-save');
    expect(find.textContaining('Line 2'), findsOneWidget);
    expect(backend.sent, isEmpty);

    await tester.enterText(find.byKey(const ValueKey('bell-slots')), '08:00-08:40\n08:40-09:00 break\n09:00-09:40');
    await tapKey(tester, 'bell-save');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('POST', '/curriculum/academic-years/ay_1/bell-schedules'));
    expect((body as Map)['name'], 'Junior');
    expect((body['slots'] as List).length, 3);
  });

  testWidgets("a section's week shows the co-teacher and the lab", (tester) async {
    await pump(tester);
    await openTab(tester, 'Week');
    await choose(tester, 'week-section', '10-A');
    expect(find.text('Science\nAna\n+ Dev\nLab 1'), findsOneWidget);
    expect(find.textContaining('Still to place: 1 of 6'), findsOneWidget);
  });

  Future<void> openWeek(WidgetTester tester) async {
    await openTab(tester, 'Week');
    await choose(tester, 'week-section', '10-A');
  }

  // A cell is tapped on its text: the DataCell's ink takes the tap there.
  Future<void> tapCell(WidgetTester tester, int day, int period) async {
    final text = find.descendant(of: find.byKey(ValueKey('week-cell-$day-$period')), matching: find.byType(Text)).first;
    await tester.ensureVisible(text);
    await tester.tap(text);
    await tester.pumpAndSettle();
  }

  Future<void> editCell(WidgetTester tester, int day, int period, {String? subject, bool lock = false}) async {
    await tapCell(tester, day, period);
    if (subject != null) await choose(tester, 'cell-subject', subject);
    if (lock) {
      await tester.tap(find.byKey(const ValueKey('cell-locked')));
      await tester.pumpAndSettle();
    }
    await tester.tap(find.byKey(const ValueKey('cell-apply')));
    await tester.pumpAndSettle();
  }

  testWidgets('a period is added and locked, and the whole week is saved at once', (tester) async {
    await pump(tester);
    await openWeek(tester);
    expect(find.byKey(const ValueKey('week-save')), findsNothing, reason: 'nothing to save before an edit');
    await editCell(tester, 1, 2, subject: 'Science (6 a week)', lock: true);
    expect(find.byIcon(Icons.lock_outline), findsOneWidget);
    expect(find.textContaining('Still to place: 2 of 6'), findsOneWidget);
    await tapKey(tester, 'week-save');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('PUT', '/curriculum/sections/sec_a/timetable'));
    expect((body as Map)['entries'], [
      {'dayOfWeek': 0, 'period': 1, 'subjectId': 'sci', 'teacherId': 't_ana', 'roomId': 'room_lab', 'locked': false},
      {'dayOfWeek': 1, 'period': 2, 'subjectId': 'sci', 'teacherId': null, 'roomId': null, 'locked': true},
    ]);
    expect(find.text('Saved: 2 periods'), findsOneWidget);
    expect(find.byKey(const ValueKey('week-save')), findsNothing);
  });

  testWidgets('a week the school refuses lists every clash and keeps the edit', (tester) async {
    backend.weekClash = true;
    await pump(tester);
    await openWeek(tester);
    await editCell(tester, 1, 2, subject: 'Science (6 a week)');
    await tapKey(tester, 'week-save');
    expect(find.text('Not saved: 2 clashes. The week is kept as it was.'), findsOneWidget);
    expect(find.text('• Tuesday period 2: the teacher already teaches 10-B then'), findsOneWidget);
    expect(find.text('• Science gets 7 periods a week here but is allocated 6'), findsOneWidget);
    expect(find.byKey(const ValueKey('week-save')), findsOneWidget, reason: 'the edit is kept to fix and save again');
  });

  testWidgets('a period is made free, and discarding brings the saved week back', (tester) async {
    await pump(tester);
    await openWeek(tester);
    await editCell(tester, 0, 1, subject: 'Free period');
    expect(find.text('Science\nAna\n+ Dev\nLab 1'), findsNothing);
    await tapKey(tester, 'week-discard');
    expect(find.text('Science\nAna\n+ Dev\nLab 1'), findsOneWidget);
    expect(backend.sent, isEmpty);
  });

  testWidgets('the periods a teacher cannot teach are shown and saved', (tester) async {
    await pump(tester);
    await openTab(tester, 'Availability');
    expect(find.text('2 periods they cannot teach'), findsOneWidget);
    expect(find.text('Can teach every period'), findsOneWidget);
    await tester.tap(find.byTooltip('Periods they cannot teach: Dev'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('unavail-2-1')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('unavail-save')));
    await tester.pumpAndSettle();
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('PUT', '/curriculum/academic-years/ay_1/teacher-unavailability/t_dev'));
    expect(body, {'slots': [{'dayOfWeek': 2, 'period': 1}]});
  });

  for (final (name, screen) in [
    ('390 px', (size: const Size(390, 844), textScale: 1.0)),
    ('390 px at 1.3x text', (size: const Size(390, 844), textScale: 1.3)),
    ('1280 px', (size: const Size(1280, 800), textScale: 1.0)),
  ]) {
    testWidgets('the Week and Availability tabs fit at $name', (tester) async {
      await pumpPage(tester, const TimetableAdminPage(), screen);
      await openWeek(tester);
      expectNoOverflow(tester, where: ' on the week');
      await tapCell(tester, 1, 2);
      await choose(tester, 'cell-subject', 'Science (6 a week)');
      expectNoOverflow(tester, where: ' in the period dialog');
      await tester.tap(find.byKey(const ValueKey('cell-apply')));
      await tester.pumpAndSettle();
      await scrollToAndExpectReady(tester, find.byKey(const ValueKey('week-save')), screen, label: 'Save the week');
      backend.weekClash = true;
      await tapKey(tester, 'week-save');
      expectNoOverflow(tester, where: ' with the clashes listed');
      await tapKey(tester, 'week-discard');
      await openTab(tester, 'Availability');
      expectNoOverflow(tester, where: ' on availability');
      await tester.tap(find.byTooltip('Periods they cannot teach: Ana'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester, where: ' in the availability dialog');
    });
  }
}
