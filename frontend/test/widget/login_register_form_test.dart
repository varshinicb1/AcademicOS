// Registration is by invite since 2026-09-21 (src/academicos/assessment/
// users.py): the server takes the new account's school and role from a
// principal-issued invite code. Before that this form asked for a school id
// and the server believed it, so anyone who knew a school's id joined it as a
// teacher. These tests pin the form's default path to the invite code, keep
// the first principal's path (school id + key) a separate, visible choice, and
// check the pre-filling links; and they check the principal's invite panel talks to the real
// invite routes.
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/presentation/admin/widgets/invites_panel.dart';
import 'package:academicos/presentation/auth/pages/login_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> _openRegister(WidgetTester tester) async {
  await tester.pumpWidget(const MaterialApp(home: LoginPage()));
  await tester.tap(find.text('Create account').first);
  await tester.pumpAndSettle();
}

/// Answers the invite routes from memory, recording what was called, so the
/// panel runs its real AuthApi calls without a server.
class _FakeInviteServer extends Interceptor {
  final List<String> calls = [];
  final List<Map<String, dynamic>> rows = [
    {
      'code': 'open-code-1234567890ab', 'role': 'teacher', 'email': null,
      'expiresAt': '2026-10-06T00:00:00+00:00', 'createdAt': '2026-09-22T00:00:00+00:00',
      'createdBy': 'user_p', 'status': 'open', 'usedBy': null, 'usedAt': null, 'revokedAt': null,
    },
    {
      'code': 'used-code-1234567890ab', 'role': 'student', 'email': 'asha@example.com',
      'expiresAt': '2026-10-06T00:00:00+00:00', 'createdAt': '2026-09-21T00:00:00+00:00',
      'createdBy': 'user_p', 'status': 'used', 'usedBy': 'user_s',
      'usedAt': '2026-09-21T10:00:00+00:00', 'revokedAt': null,
    },
  ];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    calls.add('${options.method} ${options.path}');
    Object? data;
    if (options.method == 'GET' && options.path == '/auth/invites') {
      data = rows;
    } else if (options.method == 'DELETE' && options.path.startsWith('/auth/invites/')) {
      final code = options.path.split('/').last;
      final row = rows.firstWhere((r) => r['code'] == code);
      row['status'] = 'revoked';
      row['revokedAt'] = '2026-09-22T12:00:00+00:00';
      data = row;
    }
    handler.resolve(Response(requestOptions: options, statusCode: 200, data: data));
  }
}

void main() {
  testWidgets('the default register path asks for an invite code, not a school id or role',
      (tester) async {
    await _openRegister(tester);

    expect(find.byKey(const Key('register-invite-code')), findsOneWidget);
    expect(find.widgetWithText(TextFormField, 'Invite code'), findsOneWidget);
    // Nothing on the default path lets the caller name a school or pick a role.
    expect(find.widgetWithText(TextFormField, 'School ID'), findsNothing);
    expect(find.byKey(const Key('register-school-id')), findsNothing);
    expect(find.text('Teacher'), findsNothing);
    expect(find.text('Student'), findsNothing);
    // The school-setup path is offered up front (it used to be a collapsed
    // row under the password, which principals never found), but not chosen.
    expect(find.text('Set up my school'), findsOneWidget);
    expect(find.byKey(const Key('register-principal-key')), findsNothing);
  });

  testWidgets('"Set up my school" swaps the invite code for school id + key, first',
      (tester) async {
    await _openRegister(tester);
    await tester.tap(find.text('Set up my school'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('register-school-id')), findsOneWidget);
    expect(find.byKey(const Key('register-principal-key')), findsOneWidget);
    expect(find.byKey(const Key('register-invite-code')), findsNothing);
    // School ID and key come before the person's own details.
    final schoolY = tester.getTopLeft(find.byKey(const Key('register-school-id'))).dy;
    final nameY = tester.getTopLeft(find.widgetWithText(TextFormField, 'Your name')).dy;
    expect(schoolY, lessThan(nameY));
  });

  testWidgets('a school-setup link opens on that path with the school ID filled', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginPage(schoolId: 'stmarys-hyd')));
    await tester.pumpAndSettle();
    final field = tester.widget<TextFormField>(find.byKey(const Key('register-school-id')));
    expect(field.controller!.text, 'stmarys-hyd');
    expect(find.byKey(const Key('register-invite-code')), findsNothing);
  });

  testWidgets('an invite link opens Create account with the code filled', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginPage(inviteCode: 'abc123XYZ')));
    await tester.pumpAndSettle();
    final field = tester.widget<TextFormField>(find.byKey(const Key('register-invite-code')));
    expect(field.controller!.text, 'abc123XYZ');
  });

  testWidgets('sign-in shows neither invite nor school fields', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginPage()));
    expect(find.byKey(const Key('register-invite-code')), findsNothing);
    expect(find.byKey(const Key('register-school-id')), findsNothing);
    expect(find.text('Set up my school'), findsNothing);
  });

  testWidgets('the invite panel lists invites and withdraws an open one', (tester) async {
    final server = _FakeInviteServer();
    final dio = Dio(BaseOptions(baseUrl: 'http://invites.test/api/v1'))..interceptors.add(server);
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: ListView(children: [InvitesPanel(api: AuthApi(dio))])),
    ));
    await tester.pumpAndSettle();

    expect(server.calls, ['GET /auth/invites']);
    expect(find.textContaining('open-code-1234567890ab'), findsOneWidget);
    expect(find.textContaining('Used 2026-09-21'), findsOneWidget);
    // Only the open invite can be withdrawn.
    expect(find.text('Withdraw'), findsOneWidget);

    await tester.tap(find.text('Withdraw'));
    await tester.pumpAndSettle();

    expect(server.calls, contains('DELETE /auth/invites/open-code-1234567890ab'));
    expect(find.text('Withdraw'), findsNothing);
    expect(find.textContaining('Withdrawn 2026-09-22'), findsOneWidget);
  });
}
