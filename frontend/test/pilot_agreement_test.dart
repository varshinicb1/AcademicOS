// The Phase 1 pilot agreement on the web console: a principal whose school has
// not accepted it sees it before any page, accepts with the exact text's
// version and fingerprint, and then the page opens; a school that has accepted,
// a teacher, and a server that cannot be asked all go straight to the page.
import 'dart:convert';

import 'package:academicos/presentation/pilot/pilot_agreement_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

const _text = '# AcademicOS Phase 1 Pilot Agreement\n\n## Part A. Pilot terms and conditions\n\n'
    '1. What Phase 1 is. Phase 1 is the first pilot.\n\n## Part B. Confidentiality (mutual non-disclosure)\n\n'
    '11. What is confidential. Anything not public.\n';

/// The agreement routes, from memory; records what was sent.
class _FakeServer implements HttpClientAdapter {
  _FakeServer({this.accepted = false, this.broken = false});

  bool accepted;
  final bool broken;
  final List<String> sent = [];

  Map<String, dynamic> _agreement() => {
        'version': 'phase1-v1',
        'title': 'AcademicOS Phase 1 Pilot Agreement',
        'text': _text,
        'sha256': 'a' * 64,
        'schoolName': 'Sunrise School',
        'accepted': accepted
            ? {
                'schoolLegalName': 'Sunrise Public School Society', 'signatoryName': 'Priya Sharma',
                'designation': 'Principal', 'acceptedEmail': 'p@example.com',
                'acceptedAt': '2026-10-04T12:00:00+00:00', 'version': 'phase1-v1',
              }
            : null,
      };

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    sent.add('${o.method} ${o.path}${o.data == null ? '' : ' ${jsonEncode(o.data)}'}');
    if (broken) throw DioException.connectionError(requestOptions: o, reason: 'no network');
    if (o.method == 'POST' && o.path == '/pilot-agreement/accept') accepted = true;
    return ResponseBody.fromString(jsonEncode(_agreement()), 200, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  @override
  void close({bool force = false}) {}
}

Widget _app(String role, {String user = 'user_p'}) => MaterialApp(
      home: PilotAgreementGate(
        role: role,
        userId: user,
        child: const Scaffold(body: Text('School overview')),
      ),
    );

void main() {
  late _FakeServer server;

  void serve(_FakeServer s) {
    server = s;
    if (GetIt.I.isRegistered<Dio>()) GetIt.I.unregister<Dio>();
    GetIt.I.registerSingleton<Dio>(Dio()..httpClientAdapter = s);
  }

  setUp(resetPilotAgreementRun);
  tearDown(() {
    if (GetIt.I.isRegistered<Dio>()) GetIt.I.unregister<Dio>();
  });

  testWidgets('a principal accepts the agreement before the console opens', (tester) async {
    tester.view.physicalSize = const Size(1280, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    serve(_FakeServer());
    await tester.pumpWidget(_app('principal'));
    await tester.pumpAndSettle();

    expect(find.text('School overview'), findsNothing);
    expect(find.text('Welcome to the AcademicOS Phase 1 pilot'), findsOneWidget);
    expect(find.text('Part B. Confidentiality (mutual non-disclosure)'), findsOneWidget);
    // The school's name is offered as its legal name; nothing is sent until both boxes are ticked.
    expect(find.widgetWithText(TextField, 'Sunrise School'), findsOneWidget);
    final agree = find.byKey(const Key('pilot-agree'));
    expect(tester.widget<ButtonStyleButton>(agree).onPressed, isNull);

    await tester.enterText(find.byKey(const Key('pilot-legal-name')), 'Sunrise Public School Society');
    await tester.enterText(find.byKey(const Key('pilot-signatory')), 'Priya Sharma');
    await tester.tap(find.byKey(const Key('pilot-read')));
    await tester.pump();
    expect(tester.widget<ButtonStyleButton>(agree).onPressed, isNull, reason: 'both boxes are needed');
    await tester.tap(find.byKey(const Key('pilot-authorised')));
    await tester.pump();
    expect(find.text('I am authorised to accept it for Sunrise Public School Society.'), findsOneWidget);
    await tester.tap(agree);
    await tester.pumpAndSettle();

    final post = server.sent.singleWhere((s) => s.startsWith('POST /pilot-agreement/accept'));
    final sentBody = jsonDecode(post.substring(post.indexOf('{'))) as Map;
    expect(sentBody, {
      'version': 'phase1-v1', 'sha256': 'a' * 64, 'schoolLegalName': 'Sunrise Public School Society',
      'signatoryName': 'Priya Sharma', 'designation': 'Principal', 'agree': true,
    });
    expect(find.text('School overview'), findsOneWidget);

    // The shell is rebuilt on every page: the server is not asked again this run.
    final asked = server.sent.length;
    await tester.pumpWidget(_app('principal'));
    await tester.pumpAndSettle();
    expect(find.text('School overview'), findsOneWidget);
    expect(server.sent.length, asked);
  });

  testWidgets('a school that has accepted opens straight away', (tester) async {
    serve(_FakeServer(accepted: true));
    await tester.pumpWidget(_app('principal'));
    await tester.pumpAndSettle();
    expect(find.text('School overview'), findsOneWidget);
    expect(server.sent, ['GET /pilot-agreement']);
  });

  testWidgets('a teacher is never asked', (tester) async {
    serve(_FakeServer());
    await tester.pumpWidget(_app('teacher', user: 'user_t'));
    await tester.pumpAndSettle();
    expect(find.text('School overview'), findsOneWidget);
    expect(server.sent, isEmpty);
  });

  testWidgets('when the server cannot be asked, the pages open', (tester) async {
    serve(_FakeServer(broken: true));
    await tester.pumpWidget(_app('principal'));
    await tester.pumpAndSettle();
    expect(find.text('School overview'), findsOneWidget);
  });

  testWidgets('Settings shows who accepted it and when', (tester) async {
    serve(_FakeServer(accepted: true));
    await tester.pumpWidget(const MaterialApp(home: PilotAgreementPage()));
    await tester.pumpAndSettle();
    expect(find.text('Accepted for Sunrise Public School Society'), findsOneWidget);
    expect(find.textContaining('By Priya Sharma, Principal, on 4 Oct 2026'), findsOneWidget);
    expect(find.byKey(const Key('pilot-agree')), findsNothing);
  });
}
