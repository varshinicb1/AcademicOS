// The saved paper's page on the web build, against a server that answers
// the way the backend does (QA pass of 2026-10-01):
//   * P-07: a saved paper can be renamed, deleted, and its questions swapped,
//     picked or removed until it is approved -- in Set B as well (P-10);
//   * P-09/P-22: a colleague who did not write it sees none of that, no
//     "Approve & lock", and a refused download says why;
//   * P-12/P-23: Approve & lock and Send for review change the screen at
//     once -- the chip, the buttons, a confirmation.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/download/pdf_saver.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/data/datasources/api/paper_builder_api.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/presentation/assessment/pages/assessment_review_page.dart';

import '../paper_builder/fixture_api.dart' show fixtureJson;

const _meera = {'id': 'u_meera', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Meera Iyer'};
const _esha = {'id': 'u_esha', 'schoolId': 'school_1', 'role': 'teacher', 'name': 'Esha Thomas'};
const _priya = {'id': 'u_priya', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya Menon'};

Map<String, dynamic> _assessment(String paperId, {String status = 'paperGenerated', String title = 'Half-Yearly Examination'}) =>
    Assessment(
      id: 'asm_1',
      schoolId: 'school_1',
      teacherId: 'u_meera',
      title: title,
      subject: 'Science',
      grade: 10,
      chapterIds: const [],
      blueprint: const Blueprint(
        totalMarks: 80,
        durationMinutes: 180,
        difficulty: DifficultyDistribution(easy: 0.3, medium: 0.5, hard: 0.2),
        bloom: BloomDistribution(remember: 0.2, understand: 0.2, apply: 0.2, analyze: 0.2, evaluate: 0.1, create: 0.1),
        chapterWeights: ChapterWeights(weights: {}),
        competencyWeights: CompetencyWeights(weights: {}),
        sections: [],
      ),
      status: AssessmentStatus.values.byName(status),
      createdAt: DateTime(2026, 10, 1),
      updatedAt: DateTime(2026, 10, 1),
      generatedPaperId: paperId,
    ).toJson();

/// The backend for one paper: its assessment, the paper with sets A and B,
/// and the routes the page calls. Each request is recorded.
class _Server implements HttpClientAdapter {
  static const _json = {Headers.contentTypeHeader: ['application/json']};
  final List<(String, String, Object?)> requests = [];
  late Map<String, dynamic> paper = Map<String, dynamic>.from(fixtureJson('generate_10_science')['paper'] as Map);
  late Map<String, dynamic> assessment = _assessment(paper['id'] as String);
  int downloadStatus = 200;
  int deleteStatus = 200;

  String get paperId => paper['id'] as String;

  ResponseBody _ok(Object b) => ResponseBody.fromString(jsonEncode(b), 200, headers: _json);
  ResponseBody _refuse(int status, String detail) =>
      ResponseBody.fromString(jsonEncode({'detail': detail}), status, headers: _json);

  /// Set B's question 1 replaced, in the paper's own copy of set B as the
  /// server keeps it.
  Map<String, dynamic> _swapSetB() {
    final sets = [for (final s in paper['sets'] as List) jsonDecode(jsonEncode(s)) as Map<String, dynamic>];
    final b = sets.firstWhere((s) => s['setLabel'] == 'B');
    b['sections'][0]['questions'][0]['stem'] = 'A swapped question for Set B';
    b['sections'][0]['questions'][0]['questionId'] = 'q:swapped';
    paper = {...paper, 'sets': sets};
    return b;
  }

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? body, Future<void>? cancel) async {
    final data = o.data is String ? jsonDecode(o.data as String) : o.data;
    requests.add((o.method, o.path, data));
    final p = paperId;
    switch ((o.method, o.path)) {
      case ('GET', '/my-grants'):
        return _ok({'capabilities': []});
      case ('GET', '/assessments/asm_1'):
        return _ok(assessment);
      case ('PUT', '/assessments/asm_1'):
        assessment = Map<String, dynamic>.from(data as Map);
        return _ok(assessment);
      case ('DELETE', '/assessments/asm_1'):
        return deleteStatus == 200
            ? _ok({})
            : _refuse(deleteStatus, 'a paper under review or approved cannot be deleted');
      case ('PATCH', '/assessments/asm_1/approve'):
        assessment = {...assessment, 'status': 'principalApproved'};
        return _ok(assessment);
      case ('GET', '/staff'):
        return _ok([
          {'id': 'u_meera', 'name': 'Meera Iyer'},
          {'id': 'u_suresh', 'name': 'Suresh Rao'},
        ]);
      case ('POST', '/assessments/asm_1/review-request'):
        assessment = {...assessment, 'status': 'underReview'};
        return _ok({'id': 'rev_1', 'state': 'pending'});
    }
    if (o.method == 'GET' && o.path == '/papers/$p') return _ok(paper);
    if (o.method == 'POST' && o.path == '/papers/${p}_set_B/questions/1/swap') {
      final b = _swapSetB();
      return _ok({'paper': b, 'slot': '1', 'replacedQuestionId': 'q:old', 'questionId': 'q:swapped',
        'notes': ['From a recent paper of yours'], 'counts': null});
    }
    if (o.method == 'POST' && o.path == '/papers/$p/export/pdf') {
      return downloadStatus == 200
          ? _ok({'url': '/api/v1/papers/$p/file'})
          : _refuse(downloadStatus, 'Only the author, a reviewer or the principal may download this paper '
              'before the exam is held.');
    }
    if (o.method == 'GET' && o.path == '/papers/$p/file') {
      return ResponseBody.fromBytes(utf8.encode('%PDF-1.4 paper'), 200,
          headers: {Headers.contentTypeHeader: ['application/pdf']});
    }
    return _refuse(501, 'no route for ${o.method} ${o.path}');
  }

  @override
  void close({bool force = false}) {}
}

class _Saver implements PdfSaver {
  final saved = <String>[];
  @override
  Future<void> save(Uint8List bytes, String filename) async => saved.add(filename);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('saved_paper_page_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async => Hive.close());

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  late _Server server;
  late _Saver saver;

  Future<void> open(WidgetTester tester, Map<String, String> user, {_Server? withServer}) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    server = withServer ?? _Server();
    saver = _Saver();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))
      ..httpClientAdapter = server
      ..transformer = SyncTransformer();
    GetIt.instance
      ..registerSingleton<Dio>(dio)
      ..registerSingleton<ApiClient>(ApiClient(dio))
      ..registerSingleton<PaperBuilderApi>(PaperBuilderApi(dio))
      ..registerSingleton<PdfSaver>(saver);
    LocalStore.instance.authUser = Map<String, dynamic>.from(user);
    await tester.pumpWidget(const MaterialApp(home: AssessmentReviewPage(assessmentId: 'asm_1')));
    await tester.pumpAndSettle();
  }

  Future<void> tapVisible(WidgetTester tester, Finder f) async {
    await tester.scrollUntilVisible(f, 300, scrollable: find.byType(Scrollable).first);
    await tester.pumpAndSettle();
    await tester.tap(f);
    await tester.pumpAndSettle();
  }

  Future<List<String>> menuItems(WidgetTester tester) async {
    final menu = find.byTooltip('More actions');
    if (menu.evaluate().isEmpty) return const [];
    await tester.tap(menu);
    await tester.pumpAndSettle();
    final items = [
      for (final e in find.byWidgetPredicate((w) => w is PopupMenuItem<String>).evaluate())
        ((e.widget as PopupMenuItem<String>).child as Text).data!,
    ];
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();
    return items;
  }

  /// The status chip's words, scrolled back to the top of the page first.
  Future<String> chip(WidgetTester tester) async {
    final f = find.byKey(const ValueKey('paper-status'));
    await tester.scrollUntilVisible(f, -300, scrollable: find.byType(Scrollable).first);
    await tester.pumpAndSettle();
    return tester.widget<Text>(find.descendant(of: f, matching: find.byType(Text))).data!;
  }

  testWidgets("the author may change a saved paper: the menu and each question's Swap, Pick, Remove (P-07)",
      (tester) async {
    await open(tester, _meera);
    expect(await menuItems(tester), ['Rename', 'Send for review', 'Enter marks', 'Delete']);
    expect(find.text('Swap'), findsWidgets);
    expect(find.text('Pick'), findsWidgets);
    expect(find.text('Remove'), findsWidgets);
    expect(find.byKey(const ValueKey('approve-lock')), findsNothing, reason: 'a teacher does not lock papers');
  });

  testWidgets('Set B has its own questions and its own Swap (P-10)', (tester) async {
    await open(tester, _meera);
    await tester.tap(find.text('Set B'));
    await tester.pumpAndSettle();
    final q1 = find.byKey(const ValueKey('saved-question-B-1'));
    await tester.tap(find.descendant(of: q1, matching: find.text('Swap')));
    await tester.pumpAndSettle();

    final swap = server.requests.where((r) => r.$2.endsWith('/swap')).single;
    expect(swap.$2, '/papers/${server.paperId}_set_B/questions/1/swap', reason: "the set's own paper id");
    expect(find.text('A swapped question for Set B'), findsOneWidget, reason: 'the paper is read back whole');
    expect(find.text('From a recent paper of yours'), findsOneWidget);
    expect(server.requests.where((r) => r.$1 == 'GET' && r.$2 == '/papers/${server.paperId}'), hasLength(2));
  });

  testWidgets('a colleague sees no change, no lock, and a refused download says why (P-09, P-22)',
      (tester) async {
    final s = _Server()..downloadStatus = 403;
    await open(tester, _esha, withServer: s);
    expect(await menuItems(tester), ['Enter marks']);
    expect(find.text('Swap'), findsNothing);
    expect(find.text('Remove'), findsNothing);
    expect(find.byKey(const ValueKey('ask-review')), findsNothing);
    expect(find.byKey(const ValueKey('approve-lock')), findsNothing);
    expect(find.textContaining('Settings > Profile'), findsNothing);

    await tapVisible(tester, find.byKey(const ValueKey('download-paper')));
    expect(
        find.text('Could not download the paper: Only the author, a reviewer or the principal may download '
            'this paper before the exam is held.'),
        findsOneWidget);
    expect(saver.saved, isEmpty);
  });

  testWidgets('Approve & lock updates the page at once (P-12)', (tester) async {
    final s = _Server()..assessment = _assessment(_Server().paperId, status: 'underReview');
    await open(tester, _priya, withServer: s);
    expect(await chip(tester), 'In review');
    await tapVisible(tester, find.byKey(const ValueKey('approve-lock')));

    expect(server.requests.where((r) => r.$1 == 'PATCH').single.$2, '/assessments/asm_1/approve');
    expect(find.text('Approved and locked: Half-Yearly Examination'), findsOneWidget);
    expect(find.byKey(const ValueKey('approve-lock')), findsNothing);
    expect(find.byKey(const ValueKey('paper-locked')), findsOneWidget);
    expect(find.text('Swap'), findsNothing, reason: 'a locked paper cannot change');
    expect(await chip(tester), 'Approved');
  });

  testWidgets('Send for review: the author is not offered as reviewer, and the page says In review (P-22, P-23)',
      (tester) async {
    await open(tester, _meera);
    expect(await chip(tester), 'Ready');
    await tapVisible(tester, find.byKey(const ValueKey('ask-review')));
    await tester.tap(find.byKey(const ValueKey('review-reviewer')));
    await tester.pumpAndSettle();
    expect(find.text('Meera Iyer'), findsNothing, reason: 'the server refuses an author reviewing her own paper');
    await tester.tap(find.text('Suresh Rao').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    expect(server.requests.where((r) => r.$2.endsWith('/review-request')).single.$3, {'reviewerId': 'u_suresh'});
    expect(await chip(tester), 'In review');
    expect(find.byKey(const ValueKey('ask-review')), findsNothing);
    expect(await menuItems(tester), isNot(contains('Send for review')));
  });

  testWidgets('Rename saves the new title on the paper as the server holds it (P-07)', (tester) async {
    await open(tester, _meera);
    await tester.tap(find.byTooltip('More actions'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rename'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('rename-paper-title')), 'Class 10 Science Half-Yearly 2026');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    final put = server.requests.where((r) => r.$1 == 'PUT').single;
    expect((put.$3 as Map)['title'], 'Class 10 Science Half-Yearly 2026');
    final reads = server.requests.where((r) => r.$1 == 'GET' && r.$2 == '/assessments/asm_1').length;
    expect(reads, 2, reason: 'read again just before the PUT, so a swap since is not undone');
    expect(find.text('Class 10 Science Half-Yearly 2026'), findsWidgets);
  });

  testWidgets("Delete asks first, and a refusal is shown in the server's words (P-07)", (tester) async {
    final s = _Server()..deleteStatus = 409;
    await open(tester, _meera, withServer: s);
    await tester.tap(find.byTooltip('More actions'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete'));
    await tester.pumpAndSettle();
    expect(find.text('Delete "Half-Yearly Examination"?'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('confirm-delete-paper')));
    await tester.pumpAndSettle();

    expect(server.requests.where((r) => r.$1 == 'DELETE').single.$2, '/assessments/asm_1');
    expect(find.text('Could not delete it: a paper under review or approved cannot be deleted'), findsOneWidget);
    expect(find.byType(AssessmentReviewPage), findsOneWidget, reason: 'still there');
  });

  testWidgets('a downloaded paper is named for its class, title and set (P-24)', (tester) async {
    await open(tester, _meera);
    await tapVisible(tester, find.byKey(const ValueKey('download-paper')));
    expect(saver.saved, ['class_10_science_half_yearly_examination_set_a_paper.pdf']);
  });
}
