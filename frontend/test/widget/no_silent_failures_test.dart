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
//
// A real Dio whose interceptor answers instead of the network, the technique
// of schedule_mark_error_test.dart (no mocking library, see pubspec.yaml).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/presentation/admin/widgets/invites_panel.dart';
import 'package:academicos/presentation/analytics/pages/principal_page.dart';
import 'package:academicos/presentation/question_bank/pages/question_bank_page.dart';

/// Answers `(method, path)` with [routes]' status and body; a route mapped to
/// a DioExceptionType is a request that never got an answer.
class _Server extends Interceptor {
  final Map<String, Object> routes;
  _Server(this.routes);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final route = routes['${options.method} ${options.path}'];
    if (route is DioExceptionType) {
      handler.reject(DioException(requestOptions: options, type: route));
      return;
    }
    final (status, body) = route as (int, Object?);
    final response = Response(requestOptions: options, statusCode: status, data: body);
    if (status < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(
          statusCode: status, requestOptions: options, response: response));
    }
  }
}

Dio _dio(Map<String, Object> routes) =>
    Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(_Server(routes));

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
      expect(find.textContaining('HTTP 500'), findsOneWidget);
      expect(find.textContaining('connection'), findsNothing);
    });

    testWidgets('a create that never got an answer blames the connection', (tester) async {
      await pumpAndCreate(tester, DioExceptionType.connectionError);
      expect(find.textContaining("Couldn't reach the server — check your connection"), findsOneWidget);
    });
  });
}
