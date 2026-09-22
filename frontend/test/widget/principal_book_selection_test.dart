// Widget test: the principal admin uses the subject's CHOSEN book edition,
// never the first book the server lists.
//
// PRD 12.7 (decided 2026-09-18): "Book edition: one per subject per year,
// chosen by the school." The 2026-09-21 audit found the admin page used
// books.first.id in three places -- assigning a teacher, pushing a schedule
// and loading the Sequence Reorder tab -- so with a second book on a subject
// the page acted on whichever row SQLite returned first.
//
// Here the subject has two books and the FIRST one listed is not the chosen
// one: every action must reach 'book_chosen'. Same technique as
// principal_coverage_tab_test.dart: a real Dio whose interceptor answers each
// path with the backend's response shape (schemas.py), no network.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/presentation/admin/pages/principal_admin_page.dart';

import '../support/real_di.dart';

Map<String, Object?> _book(String id, String title, {required bool selected}) => {
      'id': id,
      'subjectId': 'subj_math',
      'boardId': 'board_cbse',
      'title': title,
      'publisher': null,
      'status': 'ready',
      'selected': selected,
    };

class _Backend extends Interceptor {
  final requests = <RequestOptions>[];
  // Which book the server holds as the edition; PUT selected-book changes it.
  String chosen = 'book_chosen';
  int previousScheduled = 0;

  List<Map<String, Object?>> get _books => [
        _book('book_first', 'Mathematics (listed first)', selected: chosen == 'book_first'),
        _book('book_chosen', 'Mathematics (chosen edition)', selected: chosen == 'book_chosen'),
      ];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    requests.add(options);
    final path = options.path;
    Object? body;
    var status = 200;
    if (path == '/curriculum/academic-years') {
      body = [
        {'id': 'academicYear_1', 'label': '2026-27', 'startDate': '2026-04-01', 'endDate': '2027-03-31'},
      ];
    } else if (path.endsWith('/grades')) {
      body = [
        {'id': 'grade_10', 'number': 10, 'section': null},
      ];
    } else if (path == '/curriculum/grades/grade_10/subjects') {
      body = [
        {'id': 'subj_math', 'gradeId': 'grade_10', 'name': 'Mathematics', 'code': null},
      ];
    } else if (path == '/curriculum/subjects/subj_math/books') {
      body = _books;
    } else if (path == '/curriculum/subjects/subj_math/selected-book' && options.method == 'GET') {
      body = _books.firstWhere((b) => b['id'] == chosen);
    } else if (path == '/curriculum/subjects/subj_math/selected-book' && options.method == 'PUT') {
      final previous = chosen;
      chosen = (options.data as Map)['bookId'] as String;
      body = {
        'book': _books.firstWhere((b) => b['id'] == chosen),
        'previousBookId': previous,
        'previousBookScheduledLessons': previousScheduled,
        'warning': previousScheduled > 0
            ? '$previousScheduled lessons this year are still scheduled from the old book.'
            : null,
      };
    } else if (path == '/curriculum/boards') {
      body = [
        {'id': 'board_cbse', 'name': 'CBSE', 'code': 'CBSE'},
      ];
    } else if (path == '/auth/users') {
      final role = options.queryParameters['role'];
      body = role == 'teacher'
          ? [
              {
                'id': 'teacher_1',
                'schoolId': 'school_1',
                'name': 'Tara Teacher',
                'email': 't@school.invalid',
                'role': 'teacher'
              },
            ]
          : <Object>[];
    } else if (path == '/curriculum/teacher-assignments') {
      body = {'id': 'ta_1', 'teacherId': 'teacher_1', 'bookId': (options.data as Map)['bookId']};
    } else if (path.startsWith('/curriculum/books/') && path.endsWith('/schedule/push')) {
      body = {'lessonsPushed': 2, 'lessonsDropped': <String>[], 'periodsPerWeek': 5};
    } else if (path.startsWith('/curriculum/books/') && (path.endsWith('/units') || path.endsWith('/chapters'))) {
      body = <Object>[];
    } else {
      status = 404;
      body = {'detail': 'not found'};
    }
    final response = Response(requestOptions: options, statusCode: status, data: body);
    if (status < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(statusCode: status, requestOptions: options, response: response));
    }
  }

  Iterable<RequestOptions> to(String pathPart) => requests.where((r) => r.path.contains(pathPart));
}

late _Backend _backend;

Future<void> _openPage(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1600, 2400);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(wrapForTest(const PrincipalAdminPage()));
  await tester.pumpAndSettle();
}

Future<void> _openTab(WidgetTester tester, String label) async {
  await tester.tap(find.text(label));
  await tester.pumpAndSettle();
}

/// Opens the dropdown found by [field] and picks [item] from its menu.
Future<void> _pick(WidgetTester tester, Finder field, String item) async {
  await tester.ensureVisible(field);
  await tester.pumpAndSettle();
  await tester.tap(field);
  await tester.pumpAndSettle();
  await tester.tap(find.text(item).last);
  await tester.pumpAndSettle();
}

Finder _dropdownLabelled(String label) => find.ancestor(
      of: find.text(label),
      matching: find.byWidgetPredicate((w) => w is DropdownButtonFormField),
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('principal_book_selection_test_');
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
    _backend = _Backend();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(_backend);
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

  testWidgets('assigning a teacher assigns the chosen edition, not the first book', (tester) async {
    await _openPage(tester);
    final assignCard = find.ancestor(of: find.text('Assign Teacher'), matching: find.byType(Column)).first;
    await _pick(tester, find.descendant(of: assignCard, matching: _dropdownLabelled('Teacher')),
        'Tara Teacher (t@school.invalid)');
    await _pick(tester, find.descendant(of: assignCard, matching: _dropdownLabelled('Grade')), 'Grade 10');
    await _pick(tester, find.descendant(of: assignCard, matching: _dropdownLabelled('Subject')), 'Mathematics');

    await tester.tap(find.text('Assign Teacher'));
    await tester.pumpAndSettle();

    final posts = _backend.to('/curriculum/teacher-assignments').toList();
    expect(posts, hasLength(1));
    expect((posts.single.data as Map)['bookId'], 'book_chosen',
        reason: "books.first.id was 'book_first', the row SQLite happened to return first");
  });

  testWidgets('Sequence Reorder loads the chosen edition, not the first book', (tester) async {
    await _openPage(tester);
    await _openTab(tester, 'Sequence Reorder');
    await _pick(tester, _dropdownLabelled('Select Grade'), 'Grade 10');
    await _pick(tester, _dropdownLabelled('Select Subject'), 'Mathematics');

    expect(_backend.to('/curriculum/books/book_chosen/units'), isNotEmpty);
    expect(_backend.to('/curriculum/books/book_first/'), isEmpty);
  });

  testWidgets('a PUSH shifts the chosen edition, not the first book', (tester) async {
    await _openPage(tester);
    await _openTab(tester, 'Reschedule');
    await _pick(tester, _dropdownLabelled('Grade').last, 'Grade 10');
    await _pick(tester, _dropdownLabelled('Subject').last, 'Mathematics');
    final push = find.text('Push Subsequent Lessons');
    await tester.ensureVisible(push);
    await tester.pumpAndSettle();
    await tester.tap(push);
    await tester.pumpAndSettle();

    expect(_backend.to('/curriculum/books/book_chosen/schedule/push'), hasLength(1));
    expect(_backend.to('/curriculum/books/book_first/'), isEmpty);
  });

  testWidgets('the book picker shows the chosen edition and changes it, reporting the old schedule', (tester) async {
    _backend.previousScheduled = 12;
    await _openPage(tester);
    final card = find.byKey(const ValueKey('book-editions-card'));
    await _pick(tester, find.descendant(of: card, matching: _dropdownLabelled('Grade')), 'Grade 10');

    final picker = find.byKey(const ValueKey('book-edition-subj_math'));
    expect(find.descendant(of: picker, matching: find.text('Mathematics (chosen edition)')), findsOneWidget,
        reason: 'the server marks book_chosen selected; the picker must show it, not the first book');

    await _pick(tester, picker, 'Mathematics (listed first)');

    final puts = _backend.requests.where((r) => r.method == 'PUT' && r.path.endsWith('/selected-book')).toList();
    expect(puts, hasLength(1));
    expect((puts.single.data as Map)['bookId'], 'book_first');
    expect(find.textContaining('12 lessons this year are still scheduled from the old book'), findsOneWidget,
        reason: 'the schedule belongs to the old book; the principal is told, not left to find out');
  });
}
