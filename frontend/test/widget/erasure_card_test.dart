// The principal's erasure card (NFR-1; src/academicos/assessment/erasure.py):
// it lists students, parents and closed accounts (never staff), shows what an
// erasure deletes and what stays, sends nothing until the name is typed, and
// says what the server said when an erasure could not finish.
//
// A real Dio whose interceptor answers instead of the network
// (test/support/fake_server.dart).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/presentation/admin/widgets/erasure_card.dart';

import '../support/fake_server.dart';

Map<String, Object> _user(String id, String name, String role) =>
    {'id': id, 'schoolId': 'school_1', 'name': name, 'email': '$id@example.com', 'role': role};

final _people = [
  _user('u_asha', 'Asha Kumar', 'student'),
  _user('u_meena', 'Meena Kumar', 'parent'),
  _user('u_ana', 'Ana Teacher', 'teacher'),
  _user('u_ravi', 'Ravi Shah', 'left:student'),
];

final _preview = {
  'userId': 'u_asha', 'name': 'Asha Kumar', 'role': 'student', 'closed': false,
  'parts': [
    {'part': 'consent', 'label': 'Parental consent record', 'count': 1},
    {'part': 'scans', 'label': 'Scanned answer sheets', 'count': 2},
    {'part': 'learner_events', 'label': 'Learning event log', 'count': 0},
    {'part': 'report_files', 'label': 'Progress report PDFs', 'count': 0},
    {'part': 'account', 'label': 'The account', 'count': 1},
  ],
  'kept': [
    {'what': 'Audit log', 'why': 'append-only, kept by law'},
  ],
};

class _Capture extends Interceptor {
  final List<Object?> bodies = [];
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.method == 'POST') bodies.add(options.data);
    handler.next(options);
  }
}

Future<_Capture> _pump(WidgetTester tester, Object eraseRoute) async {
  final capture = _Capture();
  final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))
    ..interceptors.add(capture)
    ..interceptors.add(FakeServer({
      'GET /auth/users': (200, _people),
      'GET /auth/users/u_asha/erasure': (200, _preview),
      'POST /auth/users/u_asha/erasure': eraseRoute,
    }));
  await tester.pumpWidget(MaterialApp(
      home: Scaffold(
          body: SingleChildScrollView(child: ErasureCard(api: AuthApi(dio), today: DateTime(2026, 10, 1))))));
  await tester.pumpAndSettle();
  return capture;
}

Future<void> _pickAsha(WidgetTester tester) async {
  await tester.tap(find.byType(DropdownButtonFormField<String>));
  await tester.pumpAndSettle();
  await tester.tap(find.textContaining('Asha Kumar').last);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('lists students, parents and closed accounts, never staff', (tester) async {
    await _pump(tester, (200, {'parts': <Object>[]}));
    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    expect(find.textContaining('Asha Kumar'), findsWidgets);
    expect(find.textContaining('Meena Kumar'), findsWidgets);
    expect(find.textContaining('Closed student'), findsWidgets);
    expect(find.textContaining('Ana Teacher'), findsNothing);
  });

  testWidgets('shows what goes and what stays; erases only once the name is typed', (tester) async {
    final capture = await _pump(tester, (200, {
      'parts': [
        {'part': 'consent', 'label': 'Parental consent record', 'count': 1},
        {'part': 'scans', 'label': 'Scanned answer sheets', 'count': 2},
        {'part': 'account', 'label': 'The account', 'count': 1},
      ],
    }));
    await _pickAsha(tester);
    expect(find.text('Scanned answer sheets'), findsOneWidget);
    // Only what is held is listed; the empty places are counted in one line.
    expect(find.text('Learning event log'), findsNothing);
    expect(find.text('Nothing is held in the other 2 places checked.'), findsOneWidget);
    expect(find.textContaining('Audit log: append-only'), findsOneWidget);

    await tester.tap(find.text("Erase Asha Kumar's data"));
    await tester.pumpAndSettle();
    final erase = find.widgetWithText(FilledButton, 'Erase');
    expect(tester.widget<FilledButton>(erase).onPressed, isNull);
    await tester.enterText(find.byType(TextField), 'asha  kumar ');
    await tester.pump();
    // The name alone is not enough: whose request it is is chosen, never defaulted.
    expect(tester.widget<FilledButton>(erase).onPressed, isNull);
    await tester.tap(find.text('The school'));
    await tester.pump();
    expect(tester.widget<FilledButton>(erase).onPressed, isNotNull);
    await tester.tap(erase);
    await tester.pumpAndSettle();

    expect(capture.bodies, [
      {'requestedBy': 'school', 'requestReceivedOn': '2026-10-01', 'confirmName': 'asha  kumar'},
    ]);
    expect(find.textContaining("Asha Kumar's data is erased: 4 records and files deleted"), findsOneWidget);
  });

  testWidgets('an erasure that could not finish says what the server said', (tester) async {
    final capture = await _pump(tester, (503, {
      'detail': 'the erasure is not finished: marked answer sheets could not be erased yet. '
          'Run the erasure again to finish it.',
    }));
    await _pickAsha(tester);
    await tester.tap(find.text("Erase Asha Kumar's data"));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Asha Kumar');
    await tester.tap(find.text('A parent or guardian'));
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Erase'));
    await tester.pumpAndSettle();
    expect(find.textContaining('marked answer sheets could not be erased yet'), findsOneWidget);
    expect(find.textContaining('is erased'), findsNothing);
    // What is left is counted again, beside the server's sentence.
    expect(capture.bodies.single, containsPair('requestedBy', 'parent'));
    expect(find.text("Erase Asha Kumar's data"), findsOneWidget);
  });
}
