// Widget test: a principal goes from a freshly seeded chapter to real,
// approved topics without leaving the admin console.
//
// Measured on a fresh school 2026-09-22: seeding gave 58 chapters and
// GET /chapters/{id}/topics answered [] for every one of them, so the
// subtopic filter, micro-scheduling and coverage worked for no school but
// school_1. Seeding now proposes a real breakdown from the committed
// decomposition template -- but as PENDING proposals, because they came from
// another school's approved work or a textbook's headings and approving them
// is this principal's decision.
//
// So two things have to hold here: the proposals are SHOWN with their source
// before anything is accepted, and one action accepts a whole chapter (46
// chapters reviewed one proposal at a time is a setup nobody finishes).
//
// Same technique as principal_book_selection_test.dart: a real Dio whose
// interceptor answers each path with the backend's response shape
// (curriculum/schemas.py), no network.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import '../support/real_di.dart';

Map<String, Object?> _proposal(String id, String name,
        {String? parent, String? description}) =>
    {
      'id': id,
      'runId': 'extrun_1',
      'entityType': parent == null ? 'topic' : 'subtopic',
      'proposedName': name,
      'proposedDescription': description,
      'proposedParent': parent,
      'sequence': 0,
      'confidence': 1.0,
      'status': 'pending',
      'editedName': null,
      'materializedId': null,
    };

class _Backend extends Interceptor {
  final requests = <RequestOptions>[];
  // Flipped by approve-all, exactly as the server behaves: an approved run
  // leaves the pending list because its proposals are real topics now.
  bool approved = false;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    requests.add(options);
    final path = options.path;
    Object? body;
    var status = 200;
    if (path == '/curriculum/academic-years') {
      body = [
        {'id': 'academicYear_1', 'label': '2026-27', 'startDate': '2026-04-01',
         'endDate': '2027-03-31'},
      ];
    } else if (path.endsWith('/grades')) {
      body = [
        {'id': 'grade_10', 'number': 10, 'section': null},
      ];
    } else if (path == '/curriculum/grades/grade_10/subjects') {
      body = [
        {'id': 'subj_science', 'gradeId': 'grade_10', 'name': 'Science', 'code': null},
      ];
    } else if (path == '/curriculum/subjects/subj_science/selected-book') {
      body = {
        'id': 'book_science', 'subjectId': 'subj_science', 'boardId': 'board_cbse',
        'title': 'CBSE Class X Science', 'publisher': null, 'status': 'ready', 'selected': true,
      };
    } else if (path == '/curriculum/books/book_science/chapters') {
      body = [
        {'id': 'chapter_1', 'canonicalId': 'book_science:chapter:chemical-reactions-equations',
         'unitId': 'unit_1', 'name': 'Chemical Reactions and Equations', 'seq': 0},
        {'id': 'chapter_2', 'canonicalId': 'book_science:chapter:our-environment',
         'unitId': 'unit_1', 'name': 'Our Environment', 'seq': 1},
      ];
    } else if (path == '/curriculum/chapters/chapter_1/proposed-topics') {
      body = approved
          ? <Object>[]
          : [
              {
                'run': {
                  'id': 'extrun_1', 'schoolId': 'school_1', 'bookId': 'book_science',
                  'chapterId': 'chapter_1', 'sourceHash': null, 'model': null,
                  'promptVersion': 'template:ncert-textbook-headings',
                  'createdAt': '2026-09-22T00:00:00Z', 'status': 'pending',
                },
                'proposals': [
                  _proposal('p_topic', 'Chemical Equations'),
                  _proposal('p_sub', 'Balancing Chemical Equations',
                      parent: 'p_topic', description: 'NCERT section 1.1'),
                ],
              },
            ];
    } else if (path == '/curriculum/chapters/chapter_2/proposed-topics') {
      // A chapter no template covered: it must not be offered for approval.
      body = <Object>[];
    } else if (path == '/curriculum/chapters/chapter_1/topics/approve-all') {
      approved = true;
      body = {
        'chapterId': 'chapter_1', 'runsApproved': 1, 'topicsCreated': 1,
        'subtopicsCreated': 1, 'topicIds': ['topic_1'], 'subtopicIds': ['subtopic_1'],
      };
    } else if (path.startsWith('/curriculum/books/') && path.endsWith('/units')) {
      body = <Object>[];
    } else if (path == '/curriculum/subjects/subj_science/books') {
      body = <Object>[];
    } else if (path == '/auth/users') {
      body = <Object>[];
    } else {
      status = 404;
      body = {'detail': 'not found'};
    }
    final response = Response(requestOptions: options, statusCode: status, data: body);
    if (status < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(
          statusCode: status, requestOptions: options, response: response));
    }
  }

  Iterable<RequestOptions> to(String pathPart) =>
      requests.where((r) => r.path.contains(pathPart));
}

late _Backend _backend;

Finder _dropdownLabelled(String label) => find.ancestor(
      of: find.text(label),
      matching: find.byWidgetPredicate((w) => w is DropdownButtonFormField),
    );

Future<void> _pick(WidgetTester tester, Finder field, String item) async {
  await tester.ensureVisible(field);
  await tester.pumpAndSettle();
  await tester.tap(field);
  await tester.pumpAndSettle();
  await tester.tap(find.text(item).last);
  await tester.pumpAndSettle();
}

/// Opens the Sequence tab and picks the grade/subject the proposals sit under.
Future<Finder> _openProposals(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1600, 3000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(wrapForTest(const PrincipalAdminPage()));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Sequence Reorder'));
  await tester.pumpAndSettle();

  final card = find.ancestor(
      of: find.text('Proposed topics'), matching: find.byType(Column)).first;
  await _pick(tester, find.descendant(of: card, matching: _dropdownLabelled('Grade')), 'Grade 10');
  await _pick(tester, find.descendant(of: card, matching: _dropdownLabelled('Subject')), 'Science');
  return card;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('principal_pending_topics_test_');
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
    _backend = _Backend();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))
      ..interceptors.add(_backend);
    await GetIt.instance.reset();
    GetIt.instance
      ..registerSingleton<CurriculumApi>(CurriculumApi(dio))
      ..registerSingleton<AuthApi>(AuthApi(dio));
    LocalStore.instance.authUser = {
      'id': 'u_principal',
      'schoolId': 'school_1',
      'name': 'Principal',
      'email': 'principal@school.invalid',
      'role': 'principal',
    };
  });

  testWidgets('a chapter with pending proposals shows them and names their source',
      (tester) async {
    await _openProposals(tester);

    expect(find.text('1 of 2 chapters have proposals waiting.'), findsOneWidget);
    expect(find.text('Chemical Reactions and Equations'), findsOneWidget);
    // The chapter no template covered is not offered -- it has nothing to approve.
    expect(find.text('Our Environment'), findsNothing);
    expect(
      find.textContaining('the NCERT textbook\'s own numbered section headings'),
      findsOneWidget,
    );

    await tester.tap(find.text('Chemical Reactions and Equations'));
    await tester.pumpAndSettle();
    expect(find.text('Chemical Equations'), findsOneWidget);
    expect(find.text('• Balancing Chemical Equations'), findsOneWidget);
    expect(find.text('NCERT section 1.1'), findsOneWidget);

    // Nothing has been approved by merely looking at it.
    expect(_backend.to('approve-all'), isEmpty);
  });

  testWidgets('approve all for a chapter creates its topics and clears the proposal',
      (tester) async {
    await _openProposals(tester);
    await tester.tap(find.text('Chemical Reactions and Equations'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Approve all for this chapter'));
    await tester.pumpAndSettle();

    final approve = _backend.to('/chapters/chapter_1/topics/approve-all');
    expect(approve, hasLength(1));
    expect(approve.first.method, 'POST');
    expect(
      find.textContaining('Approved 1 topics and 1 subtopics'),
      findsOneWidget,
    );
    // The card re-read the server rather than assuming: the chapter is gone
    // from the waiting list because its proposals are real topics now.
    expect(find.text('Chemical Reactions and Equations'), findsNothing);
    expect(
      find.textContaining('No chapter of this subject is waiting for approval'),
      findsOneWidget,
    );
  });
}
