// The teacher's My day and the student's Today as the apps show them (v3
// audit areas 4 and 5): each period's time and room, what changed, the
// handover note for whoever covers, "Partly" for a lesson, the next period,
// and an inbox link for every kind the server sends. Neither page had a
// widget test.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/workspace/cover_pages.dart';
import 'package:academicos/presentation/workspace/inbox_page.dart';
import 'package:academicos/presentation/workspace/period_line.dart';
import 'package:academicos/presentation/workspace/student_today_page.dart';
import 'package:academicos/presentation/workspace/week_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

const _day = '[{"sectionId":"s10a","period":1,"subjectId":"sci","teacherId":"u1","kind":"regular",'
    '"sectionName":"10-A","subjectName":"Science","startTime":"08:00","endTime":"08:45","changed":false},'
    '{"sectionId":"s9a","period":3,"subjectId":"mat","teacherId":"u1","kind":"substitute","roomId":"r1",'
    '"roomName":"Physics Lab","sectionName":"9-A","subjectName":"Mathematics","startTime":"10:00",'
    '"endTime":"10:45","changed":true,"note":"Worksheet 3 is on my desk"}]';

class _Server implements HttpClientAdapter {
  final List<RequestOptions> posted = [];
  final List<RequestOptions> put = [];
  final Map<String, String> answers = {
    '/curriculum/my-day': _day,
    '/curriculum/my-attendance': '{"teacherId":"u1","name":"Tara Teacher","status":"unmarked"}',
    '/curriculum/substitutions': '[{"id":"sub1","date":"2026-10-02","sectionId":"s9a","period":3,"subjectId":"mat",'
        '"absentTeacherId":"u2","substituteId":"u1","status":"proposed","mode":"substitute",'
        '"handoverNote":"Worksheet 3 is on my desk"}]',
    '/curriculum/leave-requests': '[]',
    '/curriculum/my-schedule': '[{"lessonId":"l1","date":"2026-10-01","status":"scheduled","sectionName":"10-A",'
        '"subjectName":"Science","chapterName":"Light","topicName":"Mirrors","subtopicName":"Concave mirrors"}]',
    '/curriculum/academic-years': '[]',
    '/my-homework': '[]',
    '/my-exams': '{"exams":[]}',
    '/my-calendar': '[{"kind":"holiday","title":"Sports day","date":"2026-10-05"},'
        '{"kind":"invigilation","title":"Invigilation: 10-A Science","date":"2026-10-08",'
        '"startTime":"09:30","endTime":"11:00"}]',
    '/my-load': '{"periodsPerWeek":24,"maxInOneDay":6,"daysTaught":{"0":6,"1":4},'
        '"classes":[{"sectionName":"10-A","subjectName":"Science","periodsPerWeek":6}],'
        '"coversThisWeek":2,"invigilationsAhead":1}',
    '/curriculum/my-timetable': '{"role":"teacher","entries":[{"dayOfWeek":0,"period":1,'
        '"subjectName":"Science","sectionName":"10-A"}],"bellSchedule":{"slots":'
        '[{"period":1,"start":"08:00","end":"08:45"}],"days":[0,1,2,3,4,5]}}',
  };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method == 'POST') posted.add(o);
    if (o.method == 'PUT') put.add(o);
    final post = o.path == '/curriculum/my-attendance'
        ? '{"teacherId":"u1","name":"Tara Teacher","status":"present"}'
        : '{}';
    return ResponseBody.fromString(o.method == 'POST' ? post : (answers[o.path] ?? '[]'), 200,
        headers: {Headers.contentTypeHeader: ['application/json']});
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('app_day_pages_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  late _Server server;

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'u1', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Tara Teacher'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // not-a-failure: the box file is released when the test process exits
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pump(WidgetTester tester, Widget page, {Size size = const Size(390, 1600)}) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.lightTheme, home: page));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    for (var i = 0; i < 3; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
  }

  testWidgets('My day: each period with its time and room, what changed, the note and Partly', (tester) async {
    await pump(tester, const MyDayPage());
    expect(tester.takeException(), isNull);
    expect(find.textContaining('08:00–08:45'), findsOneWidget);
    expect(find.textContaining('10:00–10:45 · Physics Lab'), findsOneWidget);
    expect(find.textContaining('Worksheet 3 is on my desk'), findsWidgets, reason: 'the handover reaches the cover');
    expect(find.textContaining('1 changed'), findsOneWidget);
    expect(find.text('Partly'), findsOneWidget);
    expect(find.text('Covering'), findsOneWidget);
    // The lesson's buttons sit under it: on a 390 px phone the title keeps the
    // row's width instead of wrapping one word a line beside three buttons.
    final title = tester.getSize(find.textContaining('Concave mirrors').first);
    expect(title.width, greaterThan(250));
  });

  testWidgets('Leave for today in three taps (TA-3)', (tester) async {
    await pump(tester, const MyDayPage());
    final apply = find.text('Apply for leave');
    await tester.scrollUntilVisible(apply, 200);
    await tester.tap(apply); // 1
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.byKey(const Key('leave-today')), findsOneWidget, reason: 'today is chosen as the dialog opens');
    await tester.tap(find.byKey(const Key('leave-apply'))); // 2: leave for today
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 50));
    final sent = server.posted.where((o) => o.path == '/curriculum/leave-requests').toList();
    expect(sent, hasLength(1));
    final now = DateTime.now();
    final today = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    expect((sent.single.data as Map)['startDate'], today);
    expect((sent.single.data as Map)['endDate'], today);
  });

  // v3 audit N-3-17: the web offered only a full day and the two halves,
  // though the API took named periods.
  testWidgets('Leave for named periods: the teacher picks them from their day', (tester) async {
    await pump(tester, const MyDayPage());
    final apply = find.text('Apply for leave');
    await tester.scrollUntilVisible(apply, 200);
    await tester.tap(apply);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.byKey(const Key('leave-attach')), findsOneWidget, reason: 'a document can go with it');
    await tester.tap(find.byKey(const Key('leave-kind-periods')));
    await tester.pump(const Duration(milliseconds: 100));
    final applyButton = tester.widget<FilledButton>(find.byKey(const Key('leave-apply')));
    expect(applyButton.onPressed, isNull, reason: 'no period chosen yet');
    await tester.tap(find.byKey(const Key('leave-period-1')));
    await tester.pump(const Duration(milliseconds: 100));
    await tester.tap(find.byKey(const Key('leave-apply')));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 50));
    final sent = server.posted.where((o) => o.path == '/curriculum/leave-requests').toList();
    expect(sent, hasLength(1));
    expect((sent.single.data as Map)['kind'], 'periods');
    expect((sent.single.data as Map)['periods'], [1]);
  });

  testWidgets('The principal sees named periods and the document on a request', (tester) async {
    LocalStore.instance.authUser = {'id': 'p1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
    server.answers['/curriculum/academic-years'] = '[{"id":"y1","startDate":"2026-04-01","endDate":"2027-03-31"}]';
    server.answers['/curriculum/teacher-attendance'] =
        '{"date":"2026-10-01","rows":[{"teacherId":"u2","name":"Ana","status":"unmarked"}],"substitutions":[]}';
    server.answers['/curriculum/leave-requests'] = '[{"id":"l1","teacherId":"u2","startDate":"2026-10-02",'
        '"endDate":"2026-10-02","kind":"periods","periods":[3,5],"reason":"doctor","status":"pending",'
        '"document":{"contentType":"application/pdf","name":"certificate.pdf","size":2048,"uploadedAt":"x"}}]';
    await pump(tester, const CoverPage());
    expect(tester.takeException(), isNull);
    expect(find.textContaining('(periods 3, 5)'), findsOneWidget);
    expect(find.byKey(const Key('leave-document-l1')), findsOneWidget);
    expect(find.byTooltip('Open certificate.pdf'), findsOneWidget);
  });

  // SCH-6/SCH-7: the cover desk's own rules. The dialog sends every rule,
  // so saving one never turns another off.
  testWidgets('The principal turns on make-up booking and the answer time', (tester) async {
    LocalStore.instance.authUser = {'id': 'p1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
    server.answers['/curriculum/academic-years'] = '[{"id":"y1","startDate":"2026-04-01","endDate":"2027-03-31"}]';
    server.answers['/curriculum/teacher-attendance'] = '{"date":"2026-10-01","rows":[],"substitutions":[]}';
    server.answers['/curriculum/staff-policy'] = '{"autoApprove":true,"maxAutoDays":2,"minNoticeDays":1,'
        '"annualAllowanceDays":12,"checkInGraceMinutes":10,"checkInReminder":true,"autoCompensate":false,'
        '"substituteAnswerMinutes":0,"firstBell":"08:00"}';
    await pump(tester, const CoverPage(), size: const Size(1280, 1600));
    expect(tester.takeException(), isNull);
    expect(find.textContaining('You book make-up periods.'), findsOneWidget);
    await tester.tap(find.text('Change'));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.byKey(const Key('rule-makeup')));
    await tester.pump(const Duration(milliseconds: 100));
    await tester.enterText(find.widgetWithText(TextField, 'Pass a substitution on if not answered in'), '20');
    await tester.tap(find.byKey(const Key('rule-save')));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 50));
    final sent = server.put.where((o) => o.path == '/curriculum/staff-policy').toList();
    expect(sent, hasLength(1));
    final body = sent.single.data as Map;
    expect(body['autoCompensate'], isTrue);
    expect(body['substituteAnswerMinutes'], 20);
    expect(body['autoApprove'], isTrue, reason: 'the other rules go back as they were');
    expect(body['checkInReminder'], isTrue);
  });

  test('a leave reads as its kind', () {
    expect(leaveKindLabel({'kind': 'periods', 'periods': [3, 5]}), 'periods 3, 5');
    expect(leaveKindLabel({'kind': 'first_half'}), '1st half');
    expect(leaveKindLabel({'kind': 'full_day'}), 'full day');
    expect(leaveDocumentType('Scan.JPG'), 'image/jpeg');
    expect(leaveDocumentType('certificate.pdf'), 'application/pdf');
    expect(leaveDocumentType('note.docx'), isNull);
  });

  // "I'm here" went back to "I'm here" every time My day opened, inviting a
  // second check-in and saying nothing of the first (QA S-12, 2026-10-01).
  testWidgets("I'm here stays marked when My day opens again", (tester) async {
    await pump(tester, const MyDayPage());
    await tester.tap(find.byKey(const Key('check-in')));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 300)));
    await tester.pump(const Duration(milliseconds: 50));
    expect(find.text('Marked present'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await pump(tester, const MyDayPage());
    expect(find.text('Marked present'), findsOneWidget, reason: 'today\'s check-in is remembered');
    expect(find.text("I'm here"), findsNothing);
    expect(server.posted.where((o) => o.path == '/curriculum/my-attendance'), hasLength(1));
  });

  testWidgets('a check-in made on another device shows as marked', (tester) async {
    LocalStore.instance.setCheckIn('u1', '2000-01-01', 'present');   // nothing remembered for today here
    server.answers['/curriculum/my-attendance'] = '{"teacherId":"u1","name":"Tara Teacher","status":"present"}';
    await pump(tester, const MyDayPage());
    expect(find.text('Marked present'), findsOneWidget, reason: "the register's own row, not this device's memory");
    expect(find.text("I'm here"), findsNothing);
    expect(server.posted.where((o) => o.path == '/curriculum/my-attendance'), isEmpty);
  });

  testWidgets("another day's check-in does not mark today", (tester) async {
    LocalStore.instance.setCheckIn('u1', '2000-01-01', 'present');
    await pump(tester, const MyDayPage());
    expect(find.text("I'm here"), findsOneWidget);
  });

  testWidgets('Today: the student sees times, the room and a changed period', (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    await pump(tester, const StudentTodayPage());
    expect(tester.takeException(), isNull);
    expect(find.textContaining('08:00–08:45'), findsOneWidget);
    expect(find.textContaining('Physics Lab'), findsOneWidget);
    expect(find.text('Changed'), findsOneWidget);
  });

  // The timetable is a day-by-period grid where there is room, one day at a time on a phone (week_page.dart).
  const wide = Size(1100, 1800);

  testWidgets('Week: what is coming up, my load, then the timetable (TA-2)', (tester) async {
    await pump(tester, const WeekPage(), size: wide);
    expect(tester.takeException(), isNull);
    expect(find.text('Coming up'), findsOneWidget);
    expect(find.text('Sports day'), findsOneWidget);
    expect(find.text('Invigilation: 10-A Science'), findsOneWidget);
    expect(find.textContaining('09:30–11:00'), findsOneWidget);
    expect(find.text('24 periods a week'), findsOneWidget);
    expect(find.text('Busiest day: Mon (6)'), findsOneWidget);
    expect(find.textContaining('Covers this week: 2'), findsOneWidget);
    expect(find.text('10-A Science · 6'), findsOneWidget);
    expect(find.text('P1'), findsOneWidget, reason: 'the grid is still there');
  });

  testWidgets("Week: each period shows its own section's bell time (N-3-15)", (tester) async {
    // Two Junior periods and one Main period; the bell sent is Main's. The
    // grid used to label every row with Main's times.
    server.answers['/curriculum/my-timetable'] = '{"role":"teacher","entries":['
        '{"dayOfWeek":0,"period":1,"subjectName":"Science","sectionName":"6-A","startTime":"08:20","endTime":"09:00"},'
        '{"dayOfWeek":1,"period":2,"subjectName":"Science","sectionName":"6-A","startTime":"09:00","endTime":"09:40"},'
        '{"dayOfWeek":2,"period":2,"subjectName":"Maths","sectionName":"10-A","startTime":"08:45","endTime":"09:25"}],'
        '"bellSchedule":{"slots":[{"period":1,"start":"08:05","end":"08:45"},'
        '{"period":2,"start":"08:45","end":"09:25"}],"days":[0,1,2,3,4,5]}}';
    await pump(tester, const WeekPage(), size: wide);
    expect(tester.takeException(), isNull);
    expect(find.text('08:20-09:00'), findsOneWidget, reason: "P1 is taught only on the Junior bell");
    expect(find.text('08:05-08:45'), findsNothing, reason: "Main's P1 time is nobody's here");
    // P2 is on both bells: the row has no one time, each period shows its own.
    expect(find.text('09:00-09:40'), findsOneWidget);
    expect(find.text('08:45-09:25'), findsOneWidget);
  });

  test('a row takes the time its periods share, else none', () {
    final entries = [
      {'period': 1, 'startTime': '08:20', 'endTime': '09:00'},
      {'period': 2, 'startTime': '09:00', 'endTime': '09:40'},
      {'period': 2, 'startTime': '08:45', 'endTime': '09:25'},
    ];
    expect(rowTimes(entries, {1: '08:05-08:45', 2: '08:45-09:25', 3: '09:25-10:05'}, [1, 2, 3]),
        {1: '08:20-09:00', 2: null, 3: '09:25-10:05'});
  });

  // v3 audit N-3-19: the apps never said a day was a holiday, a half day or
  // in an exam window; only the calendar feed carried holidays.
  String iso(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  void calendarCovering(_Server server, DateTime from) {
    final first = iso(from), last = iso(from.add(const Duration(days: 1)));
    server.answers['/my-calendar'] = '[{"kind":"half_day","title":"Half day: PTM (periods 1-4)","date":"$first",'
        '"endDate":"$last"},{"kind":"exam_window","title":"Exam window: Unit test 1 (class 10)","date":"$first",'
        '"endDate":"$last"},{"kind":"homework","title":"Homework due: Light","date":"$first"}]';
  }

  testWidgets('Today: the student is told the day is a half day in an exam window', (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    calendarCovering(server, DateTime.now());
    await pump(tester, const StudentTodayPage());
    expect(tester.takeException(), isNull);
    expect(find.byKey(const ValueKey('calendar-day-notice')), findsOneWidget);
    expect(find.text('Half day: PTM (periods 1-4)'), findsOneWidget);
    expect(find.text('Exam window: Unit test 1 (class 10)'), findsOneWidget);
    expect(find.text('Homework due: Light'), findsNothing, reason: 'the notice says how the day runs, nothing else');
  });

  testWidgets('My day: the teacher is told today is a half day', (tester) async {
    calendarCovering(server, DateTime.now());
    await pump(tester, const MyDayPage());
    expect(tester.takeException(), isNull);
    expect(find.text('Half day: PTM (periods 1-4)'), findsOneWidget);
  });

  testWidgets('Week: half days, exam windows and working days are coming up', (tester) async {
    server.answers['/my-calendar'] = '[{"kind":"half_day","title":"Half day: PTM (periods 1-4)","date":"2026-10-12"},'
        '{"kind":"exam_window","title":"Exam window: Half-yearly (class 10)","date":"2026-10-20",'
        '"endDate":"2026-10-24"},{"kind":"working_day","title":"Working day: Rain day (Monday\'s timetable)",'
        '"date":"2026-10-31"}]';
    await pump(tester, const WeekPage());
    expect(tester.takeException(), isNull);
    expect(find.text('Half day: PTM (periods 1-4)'), findsOneWidget);
    expect(find.text('Exam window: Half-yearly (class 10)'), findsOneWidget);
    expect(find.text("Working day: Rain day (Monday's timetable)"), findsOneWidget);
    expect(find.byIcon(Icons.timelapse), findsOneWidget);
    expect(find.byIcon(Icons.edit_calendar), findsOneWidget);
    expect(find.byIcon(Icons.event_available), findsOneWidget);
  });

  testWidgets('Week: a student gets no load section', (tester) async {
    LocalStore.instance.authUser = {'id': 's1', 'schoolId': 'school_1', 'role': 'student', 'name': 'Asha'};
    await pump(tester, const WeekPage());
    expect(tester.takeException(), isNull);
    expect(find.text('My load'), findsNothing);
    expect(find.text('Sports day'), findsOneWidget);
  });

  test('when a calendar item happens', () {
    final today = DateTime(2026, 10, 1);
    expect(calendarWhen({'date': '2026-10-01'}, today), 'Today');
    expect(calendarWhen({'date': '2026-10-02', 'startTime': '09:30', 'endTime': '11:00'}, today),
        'Tomorrow · 09:30–11:00');
    expect(calendarWhen({'date': '2026-10-05', 'endDate': '2026-10-09'}, today), 'Mon 5 Oct – Fri 9 Oct');
  });

  test('the next period and its countdown', () {
    final rows = [
      {'period': 1, 'startTime': '08:00', 'kind': 'regular'},
      {'period': 3, 'startTime': '10:00', 'kind': 'substitute', 'sectionName': '9-A'},
      {'period': 4, 'startTime': '11:00', 'kind': 'lost'},
    ];
    expect(nextPeriodLine(rows, DateTime(2026, 10, 1, 9, 35), what: (r) => r['sectionName'] as String? ?? ''),
        'Next: period 3 at 10:00 · 9-A (in 25 min)');
    expect(nextPeriodLine(rows, DateTime(2026, 10, 1, 10, 30)), isNull, reason: 'a lost period is nobody\'s next');
    expect(periodWhenWhere({'startTime': '08:00', 'endTime': '08:45', 'roomName': 'Lab'}), '08:00–08:45 · Lab');
    expect(periodWhenWhere({}), '');
  });

  test('every link the server sends opens a page', () {
    const links = ['/my-exams', '/my-homework/h1', '/assessments/a1', '/my-day?date=2026-10-01', '/week',
      '/dashboard', '/homework/h1', '/cover?date=2026-10-01', '/school/term-report', '/my-timetable',
      '/my-children', '/leave', '/homework', '/my-learning'];
    for (final l in links) {
      expect(inboxRoute(l, 'teacher'), isNotNull, reason: l);
    }
    expect(inboxRoute('/cover?date=2026-10-01', 'principal'), '/school/cover');
    expect(inboxRoute('/cover?date=2026-10-01', 'teacher'), '/school/my-day');
    expect(inboxRoute('/assessments/a1', 'teacher'), '/assessment/a1');
    expect(inboxRoute('/my-timetable', 'student'), '/school/week');
    expect(inboxRoute('/leave', 'teacher'), '/school/my-day');
  });
}
