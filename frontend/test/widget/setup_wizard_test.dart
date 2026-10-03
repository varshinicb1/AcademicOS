// The setup wizard: one guided flow from a bare school to its first paper.
//
// The fake backend answers in the server's shapes and records every write, so
// the test checks what the wizard SENT (the setup body, the import CSVs, the
// paper request), not only what it showed.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/onboarding/pages/setup_wizard_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

class _Server implements HttpClientAdapter {
  final List<({String method, String path, Object? data, Map<String, dynamic> query})> writes = [];
  bool classesExist = false;
  String? profileName;
  bool paperShort = false;
  bool setupFails = false;
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  ResponseBody _ok(Object? body) => ResponseBody.fromString(jsonEncode(body), 200, headers: _json);
  ResponseBody _err(int status, String detail) =>
      ResponseBody.fromString(jsonEncode({'detail': detail}), status, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method != 'GET') {
      writes.add((method: o.method, path: o.path, data: o.data, query: Map.of(o.queryParameters)));
    }
    switch ((o.method, o.path)) {
      case ('GET', '/curriculum/school-profile'):
        return _ok({'name': profileName, 'address': null, 'affiliation': null, 'hasLogo': false});
      case ('GET', '/curriculum/academic-years'):
        return _ok([
          if (classesExist)
            {'id': 'ay_1', 'schoolId': 'school_1', 'label': '2026-27', 'startDate': '2026-04-01',
              'endDate': '2027-03-31', 'status': 'draft'},
        ]);
      case ('GET', '/staff'):
        return _ok([
          {'id': 'p_1', 'name': 'Farida Khan', 'role': 'principal', 'email': 'farida@school.in'},
          if (writes.any((w) => w.path == '/admin/import/teachers'))
            {'id': 't_1', 'name': 'Anita Rao', 'role': 'teacher', 'email': 'anita@school.in'},
        ]);
      case ('PUT', '/curriculum/school-profile'):
        return _ok({});
      case ('POST', '/curriculum/school-setup'):
        if (setupFails) return _err(422, 'term 2 falls outside the year');
        classesExist = true;
        return _ok({'academicYear': {'id': 'ay_1'}, 'classes': <Object>[], 'created': ['the academic year 2026-27'],
          'alreadyExisted': <Object>[], 'skipped': <Object>[]});
      case ('GET', '/curriculum/academic-years/ay_1/grades'):
        return _ok([{'id': 'g_9', 'number': 9}, {'id': 'g_10', 'number': 10}]);
      case ('GET', '/curriculum/academic-years/ay_1/sections'):
        return _ok([
          {'id': 's9a', 'gradeId': 'g_9', 'name': 'A'},
          {'id': 's10a', 'gradeId': 'g_10', 'name': 'A'},
          {'id': 's10b', 'gradeId': 'g_10', 'name': 'B'},
        ]);
      case ('GET', '/curriculum/grades/g_9/subjects'):
      case ('GET', '/curriculum/grades/g_10/subjects'):
        return _ok([{'name': 'Mathematics'}, {'name': 'Science'}, {'name': 'Hindi'}]);
      case ('POST', '/admin/import/teachers'):
        return _ok({'rows': [
          {'row': 2, 'status': 'ok', 'message': 'invite Anita Rao as a teacher', 'inviteCode': 'ABC123'},
        ]});
      case ('POST', '/admin/import/allocations'):
        return _ok({'rows': <Object>[]});
      case ('POST', '/papers/quick-generate'):
        return _ok({'assessmentId': 'a_1', 'totalMarks': 80,
          'warnings': paperShort ? ['Section C holds 6 of 8 marks'] : <Object>[]});
    }
    return _err(404, 'not found: ${o.method} ${o.path}');
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Server server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('setup_wizard_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = server);
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Farida Khan'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('setup_wizard_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pumpWizard(WidgetTester tester) async {
    useScreen(tester, phoneScreen);
    await tester.pumpWidget(appForTest(SetupWizardPage(today: DateTime(2026, 10, 3))));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
  }

  Future<void> tap(WidgetTester tester, String key) async {
    final f = find.byKey(ValueKey(key));
    await tester.ensureVisible(f);
    await tester.tap(f);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pumpAndSettle();
  }

  Future<void> type(WidgetTester tester, String key, String text) async {
    final f = find.byKey(ValueKey(key));
    await tester.ensureVisible(f);
    await tester.enterText(f, text);
    await tester.pump();
  }

  Map<String, dynamic> body(String method, String path) => Map<String, dynamic>.from(
      server.writes.lastWhere((w) => w.method == method && w.path == path).data as Map);

  testWidgets('a bare school goes from welcome to a first paper, and the server got what was typed',
      (tester) async {
    await pumpWizard(tester);
    expect(find.text('Welcome'), findsOneWidget);
    await tap(tester, 'wizard-next');

    // School: a name is required, and it is what is saved.
    expect(find.text('Your school'), findsOneWidget);
    await tap(tester, 'wizard-next');
    expect(find.byKey(const ValueKey('wizard-error')), findsOneWidget);
    expect(find.textContaining('needs a name'), findsOneWidget);
    await type(tester, 'wizard-name', 'Green Valley School');
    await type(tester, 'wizard-affiliation', 'CBSE Affiliation No. 1234567');
    await tap(tester, 'wizard-next');
    expect(body('PUT', '/curriculum/school-profile'),
        {'name': 'Green Valley School', 'address': null, 'affiliation': 'CBSE Affiliation No. 1234567'});

    // Classes: 9 and 10 are chosen for you; a second section for Class 10.
    expect(find.text('Classes and sections'), findsOneWidget);
    expect(tester.widget<CheckboxListTile>(find.byKey(const ValueKey('wizard-class-9'))).value, isTrue);
    expect(tester.widget<CheckboxListTile>(find.byKey(const ValueKey('wizard-class-8'))).value, isFalse);
    await tap(tester, 'wizard-sections-more-10');
    expect(find.text('A, B'), findsOneWidget);
    await tap(tester, 'wizard-next');

    // Calendar: the Indian school year around "today" is filled in.
    expect(find.text('Year, terms and bell'), findsOneWidget);
    expect(tester.widget<TextField>(find.byKey(const ValueKey('wizard-year-start'))).controller!.text, '2026-04-01');
    await tap(tester, 'wizard-saturdays');
    await tap(tester, 'wizard-next');
    final setup = body('POST', '/curriculum/school-setup');
    expect(setup['startDate'], '2026-04-01');
    expect(setup['endDate'], '2027-03-31');
    expect(setup['classes'], [
      {'grade': 9, 'sections': ['A']},
      {'grade': 10, 'sections': ['A', 'B']},
    ]);
    expect(setup['weeklyOffDays'], ['sunday']);
    expect(setup['secondAndFourthSaturdaysOff'], isTrue);
    expect((setup['terms'] as List).length, 2);
    expect((setup['bell'] as Map)['periods'], 8);

    // Teachers: one invite, sent for real (dryRun=false), its code shown.
    expect(find.text('Teachers'), findsOneWidget);
    expect(find.byKey(const ValueKey('wizard-setup-result')), findsOneWidget);
    expect(find.textContaining('Class 10: 2 section(s), 3 subjects'), findsOneWidget);
    await type(tester, 'wizard-teacher-name-0', 'Anita Rao');
    await type(tester, 'wizard-teacher-email-0', 'Anita@School.in');
    await tap(tester, 'wizard-next');
    final invite = server.writes.lastWhere((w) => w.path == '/admin/import/teachers');
    expect(invite.query['dryRun'], 'false');
    expect((invite.data as Map)['csv'], 'name,email\nAnita Rao,anita@school.in');

    // Subjects: a teacher has joined, so each subject can be given one.
    expect(find.text('Subjects and periods'), findsOneWidget);
    expect(find.byKey(const ValueKey('wizard-teacher-10-Science')), findsOneWidget);
    await tap(tester, 'wizard-p-more-10-Science');
    expect(tester.widget<Text>(find.byKey(const ValueKey('wizard-p-10-Science'))).data, '7');
    await tap(tester, 'wizard-next');
    final allocation = (server.writes.lastWhere((w) => w.path == '/admin/import/allocations').data as Map)['csv']
        as String;
    expect(allocation.split('\n').first, 'grade,section,subject,teacher_email,periods_per_week');
    expect(allocation, contains('10,A,Science,,7'));
    expect(allocation, contains('10,B,Science,,7'), reason: 'every section of the class gets the subject');
    expect(allocation, contains('9,A,Mathematics,,6'));

    // First paper.
    expect(find.text('Your first paper'), findsOneWidget);
    await tap(tester, 'wizard-next');
    final paper = body('POST', '/papers/quick-generate');
    expect(paper['grade'], 10);
    expect(paper['subject'], 'Mathematics');
    expect(paper['totalMarks'], 80);
    expect(find.byKey(const ValueKey('wizard-paper-ready')), findsOneWidget);
    expect(find.byKey(const ValueKey('wizard-open-paper')), findsOneWidget);
    await tap(tester, 'wizard-next');
    expect(find.text('All set'), findsOneWidget);
    expect(find.textContaining('Green Valley School'), findsOneWidget);
    expectNoOverflow(tester);
  });

  testWidgets('a refusal from the server is shown and the wizard stays on the step', (tester) async {
    server.setupFails = true;
    server.profileName = 'Green Valley School';
    await pumpWizard(tester);
    // A saved name skips the school step.
    expect(find.text('Classes and sections'), findsOneWidget);
    await tap(tester, 'wizard-next');
    await tap(tester, 'wizard-next');
    expect(find.text('Year, terms and bell'), findsOneWidget);
    expect(find.byKey(const ValueKey('wizard-error')), findsOneWidget);
    expect(find.textContaining('term 2 falls outside the year'), findsOneWidget);
    expect(find.text('Year, terms and bell'), findsOneWidget, reason: 'still on the step that failed');
  });

  testWidgets('a calendar that cannot be sent is caught before it is sent', (tester) async {
    server.profileName = 'Green Valley School';
    await pumpWizard(tester);
    await tap(tester, 'wizard-next'); // classes -> calendar
    await type(tester, 'wizard-term-end-0', '2026-03-01');
    await tap(tester, 'wizard-next');
    expect(find.textContaining('Term 1 ends before it starts'), findsOneWidget);
    expect(server.writes.where((w) => w.path == '/curriculum/school-setup'), isEmpty);
  });

  testWidgets('a school that is already set up reopens at its teachers, not at the start', (tester) async {
    server
      ..profileName = 'Green Valley School'
      ..classesExist = true;
    await pumpWizard(tester);
    expect(find.text('Teachers'), findsOneWidget);
    expect(find.text('Welcome'), findsNothing);
  });

  testWidgets('a short paper says which sections fell short', (tester) async {
    server
      ..profileName = 'Green Valley School'
      ..classesExist = true
      ..paperShort = true;
    await pumpWizard(tester);
    await tap(tester, 'wizard-skip'); // teachers later
    await tap(tester, 'wizard-next'); // subjects saved
    expect(find.text('Your first paper'), findsOneWidget);
    await tap(tester, 'wizard-next');
    expect(find.textContaining('Section C holds 6 of 8 marks'), findsOneWidget);
  });
}
