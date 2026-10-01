// A school can declare its terms, and set up its classes, from the web.
//
// Audit D27 (2026-09-27): the live bundle's only curriculum term call was the
// baseline PUT, so a school set up the documented way had no term: exam
// coverage and time saved read "all time" and a term's baseline could not be
// set. And the admin console opened a new school on "No curriculum yet. Seed
// the curriculum ..." with nothing on the web that could.
//
// The fake backend below holds its terms like the server does and applies the
// server's rules (inside the year, no overlap, no repeated name), so the card
// is tested against answers of the real shape, refusals included.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/constants/release_scope.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/widgets/school_setup_card.dart';
import 'package:academicos/presentation/admin/widgets/terms_card.dart';

const _phone = Size(375, 812);

final _year = AcademicYearSummary.fromJson(
    {'id': 'ay_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'});

class _Backend extends Interceptor {
  final List<Map<String, dynamic>> terms = [];
  final List<String> calls = [];
  final List<Map<String, dynamic>> seeds = [];
  // (gradeId, name): as the server keeps them, a seeded class starts with A.
  final List<(String, String)> sections = [];
  final List<(String, String)> sectionsAdded = [];
  int? failSeedAt;
  bool failProfile = false;
  Map<String, dynamic>? profile;
  int _n = 0;

  void _answer(RequestInterceptorHandler h, RequestOptions o, int status, Object? body) {
    final r = Response(requestOptions: o, statusCode: status, data: body);
    if (status < 400) {
      h.resolve(r);
    } else {
      h.reject(DioException.badResponse(statusCode: status, requestOptions: o, response: r));
    }
  }

  String? _refusal(Map body, {String? except}) {
    final s = body['startDate'] as String, e = body['endDate'] as String, name = body['name'] as String;
    if (s.compareTo(_year.startDate) < 0 || e.compareTo(_year.endDate) > 0) {
      return 'term $s .. $e falls outside the academic year (${_year.startDate} .. ${_year.endDate})';
    }
    for (final t in terms.where((t) => t['id'] != except)) {
      if ((t['name'] as String).toLowerCase() == name.toLowerCase()) {
        return "this academic year already has a term named '${t['name']}'";
      }
      if (s.compareTo(t['endDate']) <= 0 && (t['startDate'] as String).compareTo(e) <= 0) {
        return "term $s .. $e overlaps '${t['name']}' (${t['startDate']} .. ${t['endDate']})";
      }
    }
    return null;
  }

  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    calls.add('${o.method} ${o.path}');
    final body = o.data is Map ? Map<String, dynamic>.from(o.data as Map) : <String, dynamic>{};
    if (o.method == 'GET' && o.path == '/curriculum/academic-years/ay_1/terms') {
      return _answer(h, o, 200, [for (final t in terms) {...t}]);
    }
    if (o.method == 'POST' && o.path == '/curriculum/academic-years/ay_1/terms') {
      final no = _refusal(body);
      if (no != null) return _answer(h, o, 422, {'detail': no});
      final t = {'id': 'term_${++_n}', 'schoolId': 's', 'academicYearId': 'ay_1', ...body};
      terms.add(t);
      return _answer(h, o, 200, t);
    }
    if (o.path.startsWith('/curriculum/terms/')) {
      final id = o.path.split('/').last;
      final i = terms.indexWhere((t) => t['id'] == id);
      if (i < 0) return _answer(h, o, 404, {'detail': 'term not found'});
      if (o.method == 'DELETE') {
        terms.removeAt(i);
        return _answer(h, o, 200, {'ok': true});
      }
      final no = _refusal(body, except: id);
      if (no != null) return _answer(h, o, 422, {'detail': no});
      terms[i] = {...terms[i], ...body};
      return _answer(h, o, 200, terms[i]);
    }
    if (o.method == 'POST' && o.path == '/curriculum/seed/cbse') {
      if (body['grade'] == failSeedAt) return _answer(h, o, 500, {'detail': 'Internal Server Error'});
      seeds.add(body);
      final gradeId = 'g_${body['grade']}';
      if (!sections.any((x) => x.$1 == gradeId)) sections.add((gradeId, 'A'));
      return _answer(h, o, 200, {
        'boardId': 'b', 'academicYearId': 'ay_1', 'gradeId': 'g_${body['grade']}', 'grade': body['grade'],
        'subjectsSeeded': 5, 'unitsSeeded': 10, 'chaptersSeeded': 14, 'subjectsSkipped': <String>[],
      });
    }
    if (o.path == '/curriculum/school-profile') {
      if (o.method == 'GET') {
        return _answer(h, o, 200, profile ?? {'name': null, 'address': null, 'affiliation': null, 'hasLogo': false});
      }
      if (failProfile) return _answer(h, o, 422, {'detail': 'the school\'s name is at most 120 characters'});
      profile = {...?profile, ...body};
      return _answer(h, o, 200, profile);
    }
    if (o.method == 'GET' && o.path == '/curriculum/academic-years/ay_1/sections') {
      return _answer(h, o, 200, [
        for (final (i, (g, name)) in sections.indexed)
          {'id': 'sec_$i', 'academicYearId': 'ay_1', 'gradeId': g, 'gradeNumber': int.parse(g.substring(2)),
            'name': name, 'studentCount': 0}
      ]);
    }
    final addSection = RegExp(r'^/curriculum/grades/([^/]+)/sections$').firstMatch(o.path);
    if (o.method == 'POST' && addSection != null) {
      final g = addSection.group(1)!, name = body['name'] as String;
      if (sections.contains((g, name))) {
        return _answer(h, o, 422, {'detail': "this class already has a section named '$name'"});
      }
      sections.add((g, name));
      sectionsAdded.add((g, name));
      return _answer(h, o, 200, {'id': 'sec_new', 'academicYearId': 'ay_1', 'gradeId': g,
        'gradeNumber': int.parse(g.substring(2)), 'name': name, 'studentCount': 0});
    }
    _answer(h, o, 404, {'detail': 'no route ${o.method} ${o.path}'});
  }
}

CurriculumApi _api(_Backend b) =>
    CurriculumApi(Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(b));

void main() {
  group('the usual two terms', () {
    test('a CBSE session splits at 1 October', () {
      expect(TermsCard.twoTerms('2026-04-01', '2027-03-31'),
          ('2026-04-01', '2026-09-30', '2026-10-01', '2027-03-31'));
      expect(TermsCard.twoTerms('2026-06-01', '2027-03-31'),
          ('2026-06-01', '2026-09-30', '2026-10-01', '2027-03-31'));
    });
    test('a year with no 1 October inside it is halved', () {
      expect(TermsCard.twoTerms('2026-10-01', '2027-03-31'),
          ('2026-10-01', '2026-12-30', '2026-12-31', '2027-03-31'));
    });
    test('the session for a date runs April to March', () {
      expect(SchoolSetupCard.sessionFor(DateTime(2026, 9, 28)), ('2026-27', '2026-04-01', '2027-03-31'));
      expect(SchoolSetupCard.sessionFor(DateTime(2027, 2, 1)), ('2026-27', '2026-04-01', '2027-03-31'));
      expect(SchoolSetupCard.sessionFor(DateTime(2099, 4, 1)), ('2099-00', '2099-04-01', '2100-03-31'));
    });
  });

  Future<List<String>> pumpTerms(WidgetTester tester, _Backend backend) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final messages = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: TermsCard(api: _api(backend), year: _year, onMessage: messages.add),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    return messages;
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  testWidgets('a year with no term offers the usual two, and adds them', (tester) async {
    final backend = _Backend();
    await pumpTerms(tester, backend);
    expect(find.byKey(const ValueKey('terms-empty')), findsOneWidget);
    expect(find.textContaining('Add Term 1 (1 Apr 2026 - 30 Sep 2026) and Term 2 (1 Oct 2026 - 31 Mar 2027)'),
        findsOneWidget);
    expect(tester.takeException(), isNull, reason: 'the long button fits a phone');

    await tapKey(tester, 'terms-add-two');
    expect([for (final t in backend.terms) (t['name'], t['startDate'], t['endDate'])], [
      ('Term 1', '2026-04-01', '2026-09-30'),
      ('Term 2', '2026-10-01', '2027-03-31'),
    ]);
    expect(find.text('1 Apr 2026 - 30 Sep 2026'), findsOneWidget);
    expect(find.text('1 Oct 2026 - 31 Mar 2027'), findsOneWidget);
    expect(find.byKey(const ValueKey('terms-add-two')), findsNothing);
  });

  testWidgets('a term is added from the form, and a date that is not one is caught first', (tester) async {
    final backend = _Backend();
    final messages = await pumpTerms(tester, backend);
    await tester.enterText(find.byKey(const ValueKey('term-name')), 'Term 1');
    await tester.enterText(find.byKey(const ValueKey('term-start')), '2026-04-01');
    await tester.enterText(find.byKey(const ValueKey('term-end')), '30/09/2026');
    await tapKey(tester, 'term-save');
    expect(find.text('Enter the end date as YYYY-MM-DD.'), findsOneWidget);
    expect(backend.calls.where((c) => c.startsWith('POST')), isEmpty);

    await tester.enterText(find.byKey(const ValueKey('term-end')), '2026-09-30');
    await tapKey(tester, 'term-save');
    expect(backend.terms.single['name'], 'Term 1');
    expect(messages, ['Term "Term 1" added.']);
    expect(find.text('1 Apr 2026 - 30 Sep 2026'), findsOneWidget);
  });

  testWidgets("the server's refusal is shown as it says it", (tester) async {
    final backend = _Backend()
      ..terms.add({'id': 'term_a', 'name': 'Term 1', 'startDate': '2026-04-01', 'endDate': '2026-09-30'});
    await pumpTerms(tester, backend);
    await tester.enterText(find.byKey(const ValueKey('term-name')), 'Term 2');
    await tester.enterText(find.byKey(const ValueKey('term-start')), '2026-09-15');
    await tester.enterText(find.byKey(const ValueKey('term-end')), '2027-03-31');
    await tapKey(tester, 'term-save');
    expect(find.textContaining("overlaps 'Term 1' (2026-04-01 .. 2026-09-30)"), findsOneWidget);
    expect(backend.terms, hasLength(1));
  });

  testWidgets('a term is edited in place and removed after a confirmation', (tester) async {
    final backend = _Backend()
      ..terms.add({'id': 'term_a', 'name': 'Term 1', 'startDate': '2026-04-01', 'endDate': '2026-09-30'});
    final messages = await pumpTerms(tester, backend);
    await tester.tap(find.byTooltip('Edit Term 1'));
    await tester.pumpAndSettle();
    expect(find.text('Edit Term 1'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('term-name')), 'First term');
    await tapKey(tester, 'term-save');
    expect(backend.calls, contains('PUT /curriculum/terms/term_a'));
    expect(backend.terms.single['name'], 'First term');
    expect(find.text('First term'), findsOneWidget);

    await tester.tap(find.byTooltip('Remove First term'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keep'));
    await tester.pumpAndSettle();
    expect(backend.terms, hasLength(1));
    await tester.tap(find.byTooltip('Remove First term'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Remove'));
    await tester.pumpAndSettle();
    expect(backend.terms, isEmpty);
    expect(messages.last, 'Term "First term" removed.');
    expect(find.byKey(const ValueKey('terms-empty')), findsOneWidget);
  });

  Future<(bool Function(), _Backend)> pumpSetup(WidgetTester tester, {int? failAt}) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final backend = _Backend()..failSeedAt = failAt;
    var done = false;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: SchoolSetupCard(api: _api(backend), today: DateTime(2026, 9, 28), onDone: () => done = true),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    return (() => done, backend);
  }

  // Every class the release serves (1-10 since requirements v3), in order.
  testWidgets('a new school sets up classes 1 to 10 in this session', (tester) async {
    final (done, backend) = await pumpSetup(tester);
    expect(find.text('Set up classes 1 to 10'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tapKey(tester, 'setup-run');
    expect([for (final s in backend.seeds) s['grade']], releaseGrades);
    expect(backend.seeds.map((s) => (s['academicYearLabel'], s['startDate'], s['endDate'])).toSet(),
        {('2026-27', '2026-04-01', '2027-03-31')});
    expect(done(), isTrue);
    expect(backend.sectionsAdded, isEmpty, reason: 'one section per class is the A every class starts with');
    expect(backend.calls.where((c) => c.contains('/sections')), isEmpty);
  });

  testWidgets('three sections per class gives every class A, B and C', (tester) async {
    final (done, backend) = await pumpSetup(tester);
    await tester.enterText(find.byKey(const ValueKey('setup-sections')), '3');
    await tapKey(tester, 'setup-run');
    expect(done(), isTrue);
    for (final g in releaseGrades) {
      expect([for (final (grade, name) in backend.sections) if (grade == 'g_$g') name], ['A', 'B', 'C']);
    }
    expect(backend.sectionsAdded, hasLength(2 * releaseGrades.length),
        reason: 'B and C for every class; A comes with the seed');
  });

  testWidgets('a section count that is not 1 to 10 is caught before anything is sent', (tester) async {
    final (done, backend) = await pumpSetup(tester);
    for (final bad in ['0', '11', 'two']) {
      await tester.enterText(find.byKey(const ValueKey('setup-sections')), bad);
      await tapKey(tester, 'setup-run');
      expect(find.text('Sections per class is a whole number from 1 to 10.'), findsOneWidget);
    }
    expect(backend.calls, isEmpty);
    expect(done(), isFalse);
  });

  testWidgets('pressing again after a failure adds only the sections still missing', (tester) async {
    final (done, backend) = await pumpSetup(tester, failAt: 8);
    await tester.enterText(find.byKey(const ValueKey('setup-sections')), '2');
    await tapKey(tester, 'setup-run');
    // Class 8 fails: the classes before it got their B.
    final before = [for (final g in releaseGrades) if (g < 8) ('g_$g', 'B')];
    expect(backend.sectionsAdded, before);
    backend.failSeedAt = null;
    await tapKey(tester, 'setup-run');
    expect(done(), isTrue);
    expect(backend.sectionsAdded, [for (final g in releaseGrades) ('g_$g', 'B')]);
  });

  testWidgets("the school's name is saved first, so its first papers print it", (tester) async {
    final (done, backend) = await pumpSetup(tester);
    await tester.enterText(find.byKey(const ValueKey('setup-school-name')), 'Sunrise Public School');
    await tapKey(tester, 'setup-run');
    expect(done(), isTrue);
    expect(backend.profile?['name'], 'Sunrise Public School');
    final put = backend.calls.indexOf('PUT /curriculum/school-profile');
    final firstSeed = backend.calls.indexOf('POST /curriculum/seed/cbse');
    expect(put, isNonNegative);
    expect(put, lessThan(firstSeed));
  });

  testWidgets("a name the server refuses stops the setup before any class", (tester) async {
    final (done, backend) = await pumpSetup(tester);
    backend.failProfile = true;
    await tester.enterText(find.byKey(const ValueKey('setup-school-name')), 'x');
    await tapKey(tester, 'setup-run');
    expect(find.textContaining("The school's name was not saved"), findsOneWidget);
    expect(backend.seeds, isEmpty);
    expect(done(), isFalse);
  });

  testWidgets('a class that fails is named, and pressing again continues', (tester) async {
    final (done, backend) = await pumpSetup(tester, failAt: 8);
    await tapKey(tester, 'setup-run');
    final before = [for (final g in releaseGrades) if (g < 8) g];
    expect([for (final s in backend.seeds) s['grade']], before);
    expect(find.textContaining('Class 8 was not set up'), findsOneWidget);
    expect(find.textContaining('Press the button again to continue.'), findsOneWidget);
    expect(done(), isFalse);

    backend.failSeedAt = null;
    await tapKey(tester, 'setup-run');
    // The seed is idempotent, so the classes before 8 again reuse what is there.
    expect([for (final s in backend.seeds) s['grade']], [...before, ...releaseGrades]);
    expect(done(), isTrue);
  });
}
