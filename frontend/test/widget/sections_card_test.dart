// The principal manages each class's sections from the Roster tab (M1.1).
//
// Until M1.1 a section was only a label on a grade: a student was enrolled in
// "Grade 10", and nothing on the web could add, name or list a section. The
// fake backend below holds its sections like the server does and applies the
// server's rules (a name the class already has in any case, a section with
// students, a class's last section), so the card is tested against answers of
// the real shape, refusals included.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/widgets/sections_card.dart';

const _phone = Size(375, 812);

final _grades = [
  GradeSummary.fromJson({'id': 'g_10', 'number': 10}),
  GradeSummary.fromJson({'id': 'g_9', 'number': 9}),
];

final _teachers = [
  AuthUser.fromJson({'id': 'u_ana', 'schoolId': 's', 'name': 'Ana Teacher', 'email': 'ana@example.com', 'role': 'teacher'}),
];

class _Backend extends Interceptor {
  final List<Map<String, dynamic>> sections = [
    {'id': 'sec_9a', 'academicYearId': 'ay_1', 'gradeId': 'g_9', 'gradeNumber': 9, 'name': 'A', 'studentCount': 0},
    {'id': 'sec_10a', 'academicYearId': 'ay_1', 'gradeId': 'g_10', 'gradeNumber': 10, 'name': 'A', 'studentCount': 2},
  ];
  final List<String> calls = [];
  bool failList = false;
  int _n = 0;

  void _answer(RequestInterceptorHandler h, RequestOptions o, int status, Object? body) {
    final r = Response(requestOptions: o, statusCode: status, data: body);
    if (status < 400) {
      h.resolve(r);
    } else {
      h.reject(DioException.badResponse(statusCode: status, requestOptions: o, response: r));
    }
  }

  String? _nameTaken(String gradeId, String name, {String? except}) {
    for (final s in sections.where((s) => s['gradeId'] == gradeId && s['id'] != except)) {
      if ((s['name'] as String).toLowerCase() == name.toLowerCase()) {
        return "this class already has a section named '${s['name']}'";
      }
    }
    return null;
  }

  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    calls.add('${o.method} ${o.path}');
    final body = o.data is Map ? Map<String, dynamic>.from(o.data as Map) : <String, dynamic>{};
    if (o.method == 'GET' && o.path == '/curriculum/academic-years/ay_1/sections') {
      if (failList) return _answer(h, o, 500, {'detail': 'Internal Server Error'});
      final sorted = [...sections]..sort((a, b) {
          final byGrade = (a['gradeNumber'] as int).compareTo(b['gradeNumber'] as int);
          return byGrade != 0 ? byGrade : (a['name'] as String).compareTo(b['name'] as String);
        });
      return _answer(h, o, 200, [for (final s in sorted) {...s}]);
    }
    final create = RegExp(r'^/curriculum/grades/([^/]+)/sections$').firstMatch(o.path);
    if (o.method == 'POST' && create != null) {
      final gradeId = create.group(1)!;
      final taken = _nameTaken(gradeId, body['name'] as String);
      if (taken != null) return _answer(h, o, 422, {'detail': taken});
      final s = {
        'id': 'sec_${++_n}', 'academicYearId': 'ay_1', 'gradeId': gradeId,
        'gradeNumber': gradeId == 'g_10' ? 10 : 9, 'name': body['name'],
        'classTeacherId': body['classTeacherId'], 'studentCount': 0,
      };
      sections.add(s);
      return _answer(h, o, 200, s);
    }
    if (o.path.startsWith('/curriculum/sections/')) {
      final id = o.path.split('/').last;
      final i = sections.indexWhere((s) => s['id'] == id);
      if (i < 0) return _answer(h, o, 404, {'detail': 'section not found'});
      final s = sections[i];
      if (o.method == 'DELETE') {
        if (sections.where((x) => x['gradeId'] == s['gradeId']).length <= 1) {
          return _answer(h, o, 409, {'detail': 'a class keeps at least one section; rename this one instead'});
        }
        if ((s['studentCount'] as int) > 0) {
          return _answer(h, o, 409, {
            'detail': '${s['studentCount']} student(s) are enrolled in this section; enroll them in another section first'
          });
        }
        sections.removeAt(i);
        return _answer(h, o, 200, {'ok': true});
      }
      if (o.method == 'PATCH') {
        final taken = _nameTaken(s['gradeId'] as String, body['name'] as String, except: id);
        if (taken != null) return _answer(h, o, 422, {'detail': taken});
        sections[i] = {...s, 'name': body['name'], 'classTeacherId': body['classTeacherId']};
        return _answer(h, o, 200, sections[i]);
      }
    }
    _answer(h, o, 404, {'detail': 'no route ${o.method} ${o.path}'});
  }
}

CurriculumApi _api(_Backend b) =>
    CurriculumApi(Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(b));

void main() {
  test('the next letter skips the ones a class has, whatever their case', () {
    expect(SectionsCard.nextLetter([]), 'A');
    expect(SectionsCard.nextLetter(['A', 'b', 'Rose']), 'C');
  });

  Future<(List<String>, List<List<SectionSummary>>)> pump(WidgetTester tester, _Backend backend) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final messages = <String>[];
    final loads = <List<SectionSummary>>[];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: SectionsCard(
            api: _api(backend),
            academicYearId: 'ay_1',
            grades: _grades,
            teachers: _teachers,
            onMessage: messages.add,
            onLoaded: loads.add,
          ),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    return (messages, loads);
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  testWidgets('each class lists its sections in class order, with counts and class teachers', (tester) async {
    final backend = _Backend();
    backend.sections[1]['classTeacherId'] = 'u_ana';
    final (_, loads) = await pump(tester, backend);
    expect(tester.takeException(), isNull, reason: 'the card fits a phone');
    expect(find.text('Class 9'), findsOneWidget);
    expect(find.text('Class 10'), findsOneWidget);
    expect(find.text('9-A'), findsOneWidget);
    expect(find.text('10-A'), findsOneWidget);
    expect(find.text('No students yet · No class teacher'), findsOneWidget);
    expect(find.text('2 students · Class teacher: Ana Teacher'), findsOneWidget);
    expect(tester.getTopLeft(find.text('9-A')).dy, lessThan(tester.getTopLeft(find.text('10-A')).dy));
    expect([for (final s in loads.single) s.label], ['9-A', '10-A'],
        reason: 'the enroll form is handed the same list');
  });

  testWidgets('a section is added with the next free letter and a class teacher', (tester) async {
    final backend = _Backend();
    final (messages, loads) = await pump(tester, backend);
    await tapKey(tester, 'section-add-g_10');
    expect(find.text('New section in Class 10'), findsOneWidget);
    expect(tester.widget<TextField>(find.byKey(const ValueKey('section-name'))).controller!.text, 'B');

    await tester.tap(find.byKey(const ValueKey('section-teacher')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ana Teacher').last);
    await tester.pumpAndSettle();
    await tapKey(tester, 'section-save');

    expect(backend.calls, contains('POST /curriculum/grades/g_10/sections'));
    final added = backend.sections.last;
    expect((added['name'], added['classTeacherId']), ('B', 'u_ana'));
    expect(messages, ['Section 10-B added.']);
    expect(find.text('10-B'), findsOneWidget);
    expect([for (final s in loads.last) s.label], ['9-A', '10-A', '10-B']);
  });

  testWidgets("a name the class already has is refused in the dialog, as the server says it", (tester) async {
    final backend = _Backend();
    await pump(tester, backend);
    await tapKey(tester, 'section-add-g_10');
    await tester.enterText(find.byKey(const ValueKey('section-name')), 'a');
    await tapKey(tester, 'section-save');
    expect(find.text("this class already has a section named 'A'"), findsOneWidget);
    expect(find.text('New section in Class 10'), findsOneWidget, reason: 'the dialog stays open to fix it');
    expect(backend.sections, hasLength(2));

    await tester.enterText(find.byKey(const ValueKey('section-name')), '   ');
    await tapKey(tester, 'section-save');
    expect(find.text('Give the section a name, such as A or Rose.'), findsOneWidget);
  });

  testWidgets('a section is renamed and its class teacher cleared', (tester) async {
    final backend = _Backend();
    backend.sections[1]['classTeacherId'] = 'u_ana';
    final (messages, _) = await pump(tester, backend);
    await tester.tap(find.byTooltip('Edit 10-A'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('section-name')), 'Rose');
    await tester.tap(find.byKey(const ValueKey('section-teacher')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('No class teacher').last);
    await tester.pumpAndSettle();
    await tapKey(tester, 'section-save');
    expect(backend.calls, contains('PATCH /curriculum/sections/sec_10a'));
    expect((backend.sections[1]['name'], backend.sections[1]['classTeacherId']), ('Rose', null));
    expect(messages, ['Section 10-Rose saved.']);
    expect(find.text('10-Rose'), findsOneWidget);
  });

  testWidgets("removing is confirmed first, and the server's refusal is named", (tester) async {
    final backend = _Backend()
      ..sections.add({'id': 'sec_10b', 'academicYearId': 'ay_1', 'gradeId': 'g_10', 'gradeNumber': 10,
        'name': 'B', 'studentCount': 0});
    final (messages, _) = await pump(tester, backend);

    await tester.tap(find.byTooltip('Remove 10-A'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Remove'));
    await tester.pumpAndSettle();
    expect(messages.last, 'Could not remove 10-A: 2 student(s) are enrolled in this section; '
        'enroll them in another section first');
    expect(find.text('10-A'), findsOneWidget);

    await tester.tap(find.byTooltip('Remove 10-B'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keep'));
    await tester.pumpAndSettle();
    expect(backend.sections, hasLength(3));
    await tester.tap(find.byTooltip('Remove 10-B'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Remove'));
    await tester.pumpAndSettle();
    expect(messages.last, 'Section 10-B removed.');
    expect(find.text('10-B'), findsNothing);
  });

  testWidgets('a failed load says so and retries', (tester) async {
    final backend = _Backend()..failList = true;
    final (_, loads) = await pump(tester, backend);
    expect(find.textContaining('Could not load the sections'), findsOneWidget);
    expect(loads, isEmpty);
    backend.failList = false;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('10-A'), findsOneWidget);
    expect(loads, hasLength(1));
  });
}
