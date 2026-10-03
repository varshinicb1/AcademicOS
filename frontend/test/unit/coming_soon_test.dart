// A feature that is not switched on yet is "Coming soon", not an error: the server answers 501
// (never 503, which says "try again"), and every screen's error text goes through
// serverErrorMessage, so one mapping covers them all.
import 'package:academicos/data/datasources/api/api_error.dart';
import 'package:academicos/presentation/shared/widgets/common_widgets.dart';
import 'package:academicos/presentation/workspace/ops_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

DioException _answer(int status, Map<String, Object?> body) => DioException(
    requestOptions: RequestOptions(path: '/x'),
    response: Response(requestOptions: RequestOptions(path: '/x'), statusCode: status, data: body));

void main() {
  test("the AI features say Coming soon, not the administrator's instruction", () {
    final m = serverErrorMessage(_answer(501, {
      'detail': 'AI features (scan reading, AI marking) are not enabled for this school. Ask your administrator.',
      'code': 'llm_not_enabled'
    }));
    expect(m, startsWith('Coming soon'));
    expect(m, contains('AI marking and scan reading'));
    expect(m, isNot(contains('administrator')));
  });

  test('another unavailable feature carries its own sentence', () {
    final m = serverErrorMessage(_answer(501, {
      'detail': 'Google sign-in is not set up for this school; use your password',
      'code': 'not_available'
    }));
    expect(m, 'Coming soon: Google sign-in is not set up for this school; use your password');
  });

  test('a real fault is still a fault', () {
    expect(serverErrorMessage(_answer(503, {'detail': 'x'})), 'x');
    expect(serverErrorMessage(_answer(500, {})), contains('The server had a problem'));
    expect(isComingSoonMessage(serverErrorMessage(_answer(500, {}))), isFalse);
  });

  test("the same mapping applies to the workspace pages' own errors", () {
    final e = OpsError.from(_answer(501, {'detail': 'not enabled', 'code': 'llm_not_enabled'}));
    expect(e.status, 501);
    expect(serverErrorMessage(e), startsWith('Coming soon'));
  });

  testWidgets('the full-page card is calm: no red Error, no Retry', (tester) async {
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(body: ErrorDisplay(message: comingSoonMessage(code: 'llm_not_enabled'), onRetry: () {}))));
    expect(find.byKey(const ValueKey('coming-soon')), findsOneWidget);
    expect(find.text('Error'), findsNothing);
    expect(find.byType(FilledButton), findsNothing);
    expect(find.textContaining('AI marking and scan reading'), findsOneWidget);
  });

  testWidgets('a real error keeps its red card and its Retry', (tester) async {
    await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: ErrorDisplay(message: 'The server had a problem', onRetry: () {}))));
    expect(find.text('Error'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
  });
}
