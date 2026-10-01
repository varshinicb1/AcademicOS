// Invite people (QA 2026-10-01): the code is shown, Copy says it copied
// (S-07), and a parent is invited for a named child (S-06).
//
// The "Invite created" dialog painted the code in a font the web build does
// not bundle, so the principal saw only Copy buttons, and neither said
// whether it had worked. And the panel offered Teacher and Student only: a
// parent could be invited by bulk import alone, though the API's
// /students/{id}/guardian-invites existed.
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/presentation/admin/widgets/invites_panel.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class _Server extends Interceptor {
  final List<String> calls = [];
  final List<Object?> bodies = [];

  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    calls.add('${o.method} ${o.path}');
    bodies.add(o.data);
    Object? data;
    if (o.method == 'GET' && o.path == '/auth/invites') {
      data = <Object>[];
    } else if (o.method == 'GET' && o.path == '/auth/users') {
      data = [
        {'id': 's_ravi', 'schoolId': 'sch', 'name': 'Ravi Shah', 'email': 'ravi@x.in', 'role': 'student'},
        {'id': 's_asha', 'schoolId': 'sch', 'name': 'Asha Kumar', 'email': 'asha@x.in', 'role': 'student'},
      ];
    } else if (o.method == 'POST' && o.path == '/auth/invites') {
      data = {
        'code': 'TEACH-code-1234', 'role': 'teacher', 'email': 'new@x.in',
        'expiresAt': '2026-10-15T00:00:00+00:00', 'createdAt': '2026-10-01T00:00:00+00:00',
        'createdBy': 'p', 'status': 'open',
      };
    } else if (o.method == 'POST' && o.path == '/students/s_asha/guardian-invites') {
      data = {'code': 'PARENT-code-5678', 'studentId': 's_asha', 'relation': 'mother', 'email': null,
        'expiresAt': '2026-10-15T00:00:00+00:00'};
    }
    h.resolve(Response(requestOptions: o, statusCode: 200, data: data));
  }
}

void main() {
  late _Server server;
  late List<String> clipboard;

  setUp(() {
    server = _Server();
    clipboard = [];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform, (call) async {
      if (call.method == 'Clipboard.setData') clipboard.add((call.arguments as Map)['text'] as String);
      return null;
    });
  });

  tearDown(() => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(SystemChannels.platform, null));

  Future<void> pumpPanel(WidgetTester tester) async {
    tester.view.physicalSize = const Size(900, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final dio = Dio(BaseOptions(baseUrl: 'http://invites.test/api/v1'))..interceptors.add(server);
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: SingleChildScrollView(child: InvitesPanel(api: AuthApi(dio)))),
    ));
    await tester.pumpAndSettle();
  }

  testWidgets('the created invite shows its code, and Copy says it copied', (tester) async {
    await pumpPanel(tester);
    await tester.tap(find.byKey(const ValueKey('invite-create')));
    await tester.pumpAndSettle();

    expect(find.text('Invite created'), findsOneWidget);
    final code = tester.widget<SelectableText>(find.byKey(const ValueKey('copyable-value')));
    expect(code.data, 'TEACH-code-1234');
    expect(code.style?.fontFamily, isNot('monospace'), reason: 'a family the web build does not bundle');

    await tester.tap(find.byKey(const ValueKey('copyable-copy')));
    await tester.pump();
    expect(clipboard, ['TEACH-code-1234']);
    expect(find.text('Invite code copied.'), findsOneWidget);
    expect(find.text('Copied'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('invite-copy-link')));
    await tester.pump();
    expect(clipboard.last, endsWith('/#/login?invite=TEACH-code-1234'));
    expect(find.text('Invite link copied.'), findsOneWidget);
  });

  testWidgets('a parent is invited for the child chosen, with their relation', (tester) async {
    await pumpPanel(tester);
    await tester.tap(find.text('Parent'));
    await tester.pumpAndSettle();
    expect(server.calls, contains('GET /auth/users'));

    // No child chosen: nothing is sent.
    await tester.tap(find.byKey(const ValueKey('invite-create')));
    await tester.pumpAndSettle();
    expect(find.text('Choose the child this parent is for.'), findsOneWidget);
    expect(server.calls.where((c) => c.startsWith('POST')), isEmpty);

    await tester.tap(find.byKey(const ValueKey('invite-child')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Asha Kumar').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('invite-create')));
    await tester.pumpAndSettle();

    expect(server.calls, contains('POST /students/s_asha/guardian-invites'));
    final body = server.bodies[server.calls.indexOf('POST /students/s_asha/guardian-invites')] as Map;
    expect(body['relation'], 'mother');
    expect(find.textContaining("Give this code to the Asha Kumar's mother"), findsOneWidget);
    expect(tester.widget<SelectableText>(find.byKey(const ValueKey('copyable-value'))).data, 'PARENT-code-5678');
  });
}
