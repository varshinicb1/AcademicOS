// AI reading of homework photos (TA-4): the teacher's marking dialog fills in
// the marks AI suggests for answers written on paper, says they are
// suggestions, shows what was read, and can ask for a reading now. The save
// is still the teacher's: the marks sent are what the boxes hold.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/teacher_homework.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

final _hw = {
  'id': 'hw_1', 'title': 'Light practice', 'subjectName': 'Science', 'sectionNames': ['10-A'],
  'dueDate': '2026-06-03', 'questionCount': 2, 'totalMarks': 3, 'status': 'published',
  'questions': [
    {'id': 'q1', 'stem': 'Which mirror always gives a virtual image?', 'marks': 1},
    {'id': 'q3', 'stem': 'State two laws of reflection.', 'marks': 2},
  ],
};

const _done = {
  'status': 'done', 'note': null,
  'readings': [
    {'questionId': 'q3', 'answerText': 'angle of incidence = angle of reflection', 'awardedMarks': 2, 'maxMarks': 2,
      'verdict': 'fullCredit', 'confidence': 0.8, 'reasoning': 'both laws stated',
      'warnings': ['handwriting partly unclear']},
  ],
};

Map<String, dynamic> _row({Map? reading}) => {
      'studentId': 'stu_1', 'studentName': 'Asha', 'sectionId': 'sec_a', 'status': 'submitted', 'late': false,
      'attempts': 1, 'autoMarks': 1, 'marks': null, 'maxMarks': 3, 'needsReview': 1,
      'answers': {'q1': 'A'}, 'feedback': null, 'photoIds': ['ph_1'],
      'evaluations': [
        {'questionId': 'q1', 'awardedMarks': 1, 'maxMarks': 1, 'verdict': 'fullCredit', 'reasoning': 'correct option',
          'needsReview': false},
        {'questionId': 'q3', 'awardedMarks': 0, 'maxMarks': 2, 'verdict': 'blank', 'reasoning': 'written on paper',
          'needsReview': true},
      ],
      'photoReading': reading,
    };

class _Backend implements HttpClientAdapter {
  Map? reading;
  Map<String, dynamic>? graded;
  int readRequests = 0;
  int polls = 0;
  static const _json = {Headers.contentTypeHeader: ['application/json']};
  ResponseBody _ok(Object? b, [int code = 200]) => ResponseBody.fromString(jsonEncode(b), code, headers: _json);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    const base = '/homework/hw_1/submissions/stu_1';
    switch ('${o.method} ${o.path}') {
      case 'GET /homework/hw_1':
        return _ok(_hw);
      case 'GET /homework/hw_1/submissions':
        return _ok([_row(reading: reading)]);
      case 'POST $base/read-photos':
        readRequests++;
        return _ok({'status': 'reading', 'note': null, 'readings': []}, 202);
      case 'GET $base/photo-reading':
        polls++;
        return _ok(_done);
      case 'POST $base/grade':
        graded = Map<String, dynamic>.from(o.data as Map);
        return _ok(_row());
    }
    return ResponseBody.fromString('{"detail":"no route"}', 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('hw_photo_reading_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
    LocalStore.instance.authUser = {'id': 't_1', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Ana'};
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
      print('homework_photo_reading_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  // Dio answers on real futures: let them run, then draw what they changed.
  Future<void> settle(WidgetTester tester) async {
    for (var i = 0; i < 3; i++) {
      await tester.pump(const Duration(milliseconds: 50));
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 100)));
    }
    await tester.pump();
  }

  Future<void> openDialog(WidgetTester tester, {double width = 390}) async {
    tester.view.physicalSize = Size(width, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: TeacherHomeworkDetailPage(homeworkId: 'hw_1')));
    await settle(tester);
    await tester.ensureVisible(find.text('Mark'));
    await tester.tap(find.text('Mark'));
    await settle(tester);
  }

  TextField markBox(WidgetTester tester, String suffix, int index) =>
      tester.widgetList<TextField>(find.byType(TextField)).elementAt(index);

  testWidgets('a reading already done fills the written answer with its suggestion, labelled as one',
      (tester) async {
    backend.reading = _done;
    await openDialog(tester);
    expect(find.text('AI suggestion: check it'), findsOneWidget);
    expect(find.text('Read from the photo: angle of incidence = angle of reflection'), findsOneWidget);
    expect(find.text('AI suggests 2/2: both laws stated'), findsOneWidget);
    expect(find.text('handwriting partly unclear'), findsOneWidget);
    // q1 was typed in the app and keeps the evaluator's mark; q3 takes the suggestion
    expect(markBox(tester, '/1', 0).controller!.text, '1');
    expect(markBox(tester, '/2', 1).controller!.text, '2');
    expect(tester.takeException(), isNull, reason: 'fits a phone');

    await tester.tap(find.text('Save marks'));
    await settle(tester);
    expect(backend.graded!['marks'], {'q1': 1.0, 'q3': 2.0});
  });

  testWidgets('the teacher asks for a reading, sees it under way, and gets the suggestion', (tester) async {
    await openDialog(tester, width: 1280);
    expect(find.text('AI suggestion: check it'), findsNothing);
    expect(markBox(tester, '/2', 1).controller!.text, '0');

    await tester.tap(find.byKey(const Key('read-photos')));
    await settle(tester);
    expect(backend.readRequests, 1);
    expect(find.text('Reading the photos. This takes a minute or two.'), findsOneWidget);

    await tester.pump(const Duration(seconds: 6));
    await settle(tester);
    expect(backend.polls, 1);
    expect(find.text('AI suggestion: check it'), findsOneWidget);
    expect(markBox(tester, '/2', 1).controller!.text, '2');
    expect(find.text('Read the photos again'), findsOneWidget);
  });
}
