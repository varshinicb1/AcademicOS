// Three web screens, each fed a failing server, each must say what failed
// (Task 802). One per kind of failure the shared error path maps:
//
//  * Question bank (question search): a FastAPI validation 422 -- detail is a
//    list. The page showed `'$e'`, i.e. Dio's "DioException [bad response]:
//    This exception was thrown because the response has a status code of
//    422" paragraph.
//  * School Intelligence (principal dashboard): a 401 -- the page showed the
//    same Dio paragraph for a session that had simply ended.
//  * Invites (principal admin console): a 500 on "Create invite" and a
//    request that never got an answer. auth_api mapped every status it did
//    not know to "Could not reach the server", so a principal was told to
//    check a connection that was fine.
//  * Subtopic picker (Create Assessment): a failed topic fetch was stored as
//    an empty list and read "no subtopic breakdown yet".
//  * auth_api itself: a 422 whose detail is a list crashed the `as String?`
//    cast, and a 401 on an invite call said "Incorrect email or password".
//
// The consent save and the parent portal also need the Hive-backed
// LocalStore; they live in no_silent_failures_stored_test.dart.
//
// A real Dio whose interceptor answers instead of the network
// (test/support/fake_server.dart; no mocking library, see pubspec.yaml).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/presentation/admin/widgets/invites_panel.dart';
import 'package:academicos/presentation/analytics/pages/principal_page.dart';
import 'package:academicos/presentation/assessment/pages/assessment_create_page.dart';
import 'package:academicos/presentation/question_bank/pages/question_bank_page.dart';

import '../support/fake_server.dart';

Dio _dio(Map<String, Object> routes) => fakeDio(FakeServer(routes));

void main() {
  tearDown(() => GetIt.instance.reset());

  testWidgets('question bank: a 422 list names the field and the reason', (tester) async {
    GetIt.instance.registerSingleton<PillarApi>(PillarApi(_dio({
      'GET /catalog': (422, {
        'detail': [
          {'loc': ['query', 'subject'], 'msg': 'Field required', 'type': 'missing'},
        ],
      }),
    })));
    await tester.pumpWidget(const MaterialApp(home: QuestionBankPage()));
    await tester.pumpAndSettle();

    expect(find.textContaining('subject: Field required'), findsOneWidget);
    expect(find.textContaining('DioException'), findsNothing);
  });

  testWidgets('principal dashboard: a 401 says the session ended, not a Dio dump', (tester) async {
    GetIt.instance.registerSingleton<PillarApi>(PillarApi(_dio({
      'GET /insights/school/sunrise': (401, {'detail': 'Not authenticated'}),
    })));
    await tester.pumpWidget(const MaterialApp(home: PrincipalPage(schoolId: 'sunrise')));
    await tester.pumpAndSettle();

    expect(find.textContaining("You're signed out — sign in again"), findsOneWidget);
    expect(find.textContaining('DioException'), findsNothing);
    // Retrying cannot bring a dead session back; the router's 401 handler
    // is what sends the user to Sign in.
    expect(find.text('Retry'), findsNothing);
  });

  group('invites panel', () {
    Future<void> pumpAndCreate(WidgetTester tester, Object createRoute) async {
      final api = AuthApi(_dio({
        'GET /auth/invites': (200, <Object>[]),
        'POST /auth/invites': createRoute,
      }));
      await tester.pumpWidget(MaterialApp(
          home: Scaffold(body: SingleChildScrollView(child: InvitesPanel(api: api)))));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Create invite'));
      await tester.pumpAndSettle();
    }

    testWidgets('an empty list says so and what to do next', (tester) async {
      // The list is empty and nothing failed: an empty state, not an error.
      await tester.pumpWidget(MaterialApp(
          home: Scaffold(
              body: SingleChildScrollView(
                  child: InvitesPanel(api: AuthApi(_dio({'GET /auth/invites': (200, <Object>[])})))))));
      await tester.pumpAndSettle();
      expect(find.textContaining('No invites yet'), findsOneWidget);
      expect(find.textContaining('Create one'), findsOneWidget);
      expect(find.textContaining('Could not'), findsNothing);
    });

    testWidgets('a 500 on create says the server failed, not the connection', (tester) async {
      await pumpAndCreate(tester, (500, null));
      expect(find.textContaining('The server had a problem'), findsOneWidget);
      expect(find.textContaining('connection'), findsNothing);
    });

    testWidgets('a create that never got an answer blames the connection', (tester) async {
      await pumpAndCreate(tester, DioExceptionType.connectionError);
      expect(find.textContaining("Couldn't reach the server — check your connection"), findsOneWidget);
    });
  });

  group('subtopic picker (Create Assessment)', () {
    const chapterId = 'chemical-reactions-equations';
    const chapterName = 'Chemical Reactions and Equations';
    // The by-slug route: /catalog hands this page a syllabus slug, never the
    // school's own `chap_` id, so the picker asks for the slug within a
    // subject and grade (feat/product-calendar).
    const topicsPath = 'GET /curriculum/chapters/by-slug/Science/10/$chapterId/topics';

    /// Opens the Chapters step, ticks the one chapter and expands the
    /// subtopic filter, which is what fires topicsForChapter.
    Future<FakeServer> pumpAndExpand(WidgetTester tester, Object topicsRoute) async {
      GetIt.instance.registerSingleton<PillarApi>(PillarApi(_dio({
        'GET /catalog/Science/10/chapters': (200, [
          {'chapterId': chapterId, 'chapterName': chapterName, 'questionCount': 12},
        ]),
      })));
      final server = FakeServer({topicsPath: topicsRoute});
      GetIt.instance.registerSingleton<CurriculumApi>(CurriculumApi(fakeDio(server)));
      await tester.pumpWidget(const MaterialApp(home: AssessmentCreatePage()));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Chapters'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(CheckboxListTile, chapterName));
      await tester.pumpAndSettle();
      final filter = find.text('Filter by subtopic (optional)');
      await tester.ensureVisible(filter);
      await tester.pumpAndSettle();
      await tester.tap(filter);
      await tester.pumpAndSettle();
      return server;
    }

    testWidgets('a failed topic fetch says it failed and offers Retry, not "no subtopics"', (tester) async {
      final server = await pumpAndExpand(tester, (500, null));

      expect(find.textContaining('Could not load subtopics for $chapterName'), findsOneWidget);
      expect(find.textContaining('The server had a problem'), findsOneWidget);
      expect(find.textContaining('no subtopic breakdown yet'), findsNothing,
          reason: 'a server failure is not a chapter without subtopics');

      // Retrying sends the request again (the failure was not cached as an
      // empty list, which would have made the retry a no-op). The whole row
      // is the retry affordance, hence "(tap to retry)".
      final retry = find.textContaining('Could not load subtopics for $chapterName');
      await tester.ensureVisible(retry);
      await tester.tap(retry);
      await tester.pumpAndSettle();
      expect(server.requests.where((r) => r == topicsPath), hasLength(2));
    });

    testWidgets('a 403 names the access problem, not an empty chapter', (tester) async {
      await pumpAndExpand(tester, (403, null));
      expect(
          find.textContaining(
              "Could not load subtopics for $chapterName -- You don't have access to that"),
          findsOneWidget);
      expect(find.textContaining('no subtopic breakdown yet'), findsNothing);
    });

    testWidgets('an empty 200 is the honest "no subtopic breakdown yet"', (tester) async {
      // The control case: the empty state still exists for a chapter the
      // server really has no topics for.
      await pumpAndExpand(tester, (200, <Object>[]));
      expect(find.textContaining('$chapterName: no subtopic breakdown yet'), findsOneWidget);
      expect(find.textContaining('Could not load subtopics'), findsNothing);
    });
  });

  group('auth_api error mapping', () {
    Future<AuthException> failure(Future<Object?> Function(AuthApi api) call, Map<String, Object> routes) async {
      try {
        await call(AuthApi(_dio(routes)));
      } on AuthException catch (e) {
        return e;
      }
      fail('expected an AuthException');
    }

    test('a 422 whose detail is a list names the field instead of crashing the cast', () async {
      // Before Task 802 `data['detail'] as String?` threw a TypeError here,
      // which the sign-in form reported as a network fault.
      final e = await failure(
          (api) => api.login(email: 'not-an-email', password: 'x'),
          {
            'POST /auth/login': (422, {
              'detail': [
                {'loc': ['body', 'email'], 'msg': 'value is not a valid email address', 'type': 'value_error'},
              ],
            }),
          });
      expect(e.message, 'email: value is not a valid email address');
    });

    test('a 422 list on create invite is reported the same way', () async {
      final e = await failure(
          (api) => api.createInvite(role: 'teacher', expiresInDays: 400),
          {
            'POST /auth/invites': (422, {
              'detail': [
                {'loc': ['body', 'expiresInDays'], 'msg': 'Input should be less than or equal to 90'},
              ],
            }),
          });
      expect(e.message, contains('expiresInDays: Input should be less than or equal to 90'));
      expect(e.message, isNot(contains('reach the server')));
    });

    test('a 401 on the invite calls is a session that ended, not a wrong password', () async {
      final create = await failure((api) => api.createInvite(role: 'teacher'),
          {'POST /auth/invites': (401, {'detail': 'Not authenticated'})});
      expect(create.message, "You're signed out — sign in again");
      expect(create.message, isNot(contains('Incorrect email or password')));

      final revoke = await failure((api) => api.revokeInvite('ABC123'),
          {'DELETE /auth/invites/ABC123': (401, {'detail': 'Not authenticated'})});
      expect(revoke.message, "You're signed out — sign in again");
    });

    test('a 401 on sign-in is still the wrong-credentials sentence', () async {
      final withDetail = await failure((api) => api.login(email: 'a@b.in', password: 'wrong'),
          {'POST /auth/login': (401, {'detail': 'Incorrect email or password.'})});
      expect(withDetail.message, 'Incorrect email or password.');
      final bare = await failure((api) => api.login(email: 'a@b.in', password: 'wrong'),
          {'POST /auth/login': (401, null)});
      expect(bare.message, 'Incorrect email or password.');
    });

    test('a 500 on sign-in says the server failed, not the connection', () async {
      final e = await failure((api) => api.login(email: 'a@b.in', password: 'pw12345678'),
          {'POST /auth/login': (500, null)});
      expect(e.message, contains('The server had a problem'));
      expect(e.message, isNot(contains('connection')));
    });
  });
}
