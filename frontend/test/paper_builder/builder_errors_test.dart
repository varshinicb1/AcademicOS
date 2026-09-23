// Task 803: what the guided builder tells a teacher when its own server call
// fails, branch by branch.
//
// The re-audit of the live release (2026-09-23) found the builder mapping its
// failures with a SECOND mapper (paper_builder_api's apiErrorMessage) that had
// no 401, 403 or 404 branch at all: a teacher whose session had expired inside
// the builder was told "The server answered 401. Try again." -- which is the
// one thing that cannot work -- and one who lacked access to the school they
// were building for was told the same about 403. Task 802 removed exactly that
// defect everywhere else; these tests pin it removed here too, by asserting the
// sentence on the step, not the function's return value.
//
// Every failure below is a real Dio failure through the real PaperBuilderApi:
// the adapter answers the status a backend would, and Dio raises the
// DioException a browser would see.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';

import 'fixture_api.dart';

const _phone = Size(375, 812);

/// Everything the builder asks the server for.
bool _everything(String path) => true;

/// A backend that refuses the requests [where] matches and hands every other
/// one to the captured fixtures.
///
/// [status] `null` means no answer came back at all (the browser could not
/// reach the host) -- the one case that is genuinely about the connection.
/// After [times] refusals the refused route answers normally again, which is
/// how a Retry is shown to have really gone back to the server.
class _Refusing implements HttpClientAdapter {
  _Refusing({this.status, this.body, this.where = _everything, this.times = -1});

  final int? status;
  final Object? body;
  final bool Function(String path) where;
  final int times;

  final FixtureAdapter fixtures = FixtureAdapter();
  int refusals = 0;

  @override
  Future<ResponseBody> fetch(
      RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (!where(o.uri.path) || (times >= 0 && refusals >= times)) {
      return fixtures.fetch(o, requestStream, cancelFuture);
    }
    refusals++;
    if (status == null) {
      throw DioException.connectionError(requestOptions: o, reason: 'failed host lookup');
    }
    return ResponseBody.fromString(jsonEncode(body ?? const <String, dynamic>{}), status!,
        headers: {
          Headers.contentTypeHeader: ['application/json'],
        });
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // The builder's memory is the app's Hive box; in memory, as the flow test
  // opens it, so a widget test's fake clock never waits on real file I/O.
  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_errors_test_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async => Hive.close());

  setUp(() => LocalStore.instance.box.clear());

  Finder primary() => find.byKey(const ValueKey('builder-primary'));

  /// The builder, opened on a phone browser against [adapter].
  Future<void> pump(WidgetTester tester, _Refusing adapter) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        api: fixtureApi(adapter),
        savePdf: (bytes, name) async {},
        schoolId: 'school_1',
        userId: fixtureTeacherId,
      ),
    ));
    await tester.pumpAndSettle();
  }

  /// Class 10 Science, then "Next" -- which is where the builder first asks
  /// the server for anything (the teacher's templates).
  Future<void> reachTemplates(WidgetTester tester) async {
    await tester.tap(find.text('Class 10'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Science'));
    await tester.pumpAndSettle();
    await tester.tap(primary());
    await tester.pumpAndSettle();
  }

  /// [expected] is the whole sentence on the step, and the step still offers
  /// the action that tries again.
  void expectTemplatesSay(WidgetTester tester, String expected) {
    expect(find.text('Could not load templates: $expected'), findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Try again'), findsOneWidget);
    expect(tester.takeException(), isNull);
  }

  group('a failed template load says what actually happened', () {
    testWidgets('401: the session is over, not "the server answered 401"', (tester) async {
      await pump(tester, _Refusing(status: 401, body: {'detail': 'Not authenticated'}));
      await reachTemplates(tester);
      expectTemplatesSay(tester, "You're signed out — sign in again");
    });

    testWidgets('403 with no reason: the account lacks access', (tester) async {
      await pump(tester, _Refusing(status: 403));
      await reachTemplates(tester);
      expectTemplatesSay(tester, "You don't have access to that");
    });

    testWidgets("403 for a school the teacher is not in keeps the server's reason", (tester) async {
      const refused = 'You are not a teacher at this school';
      await pump(tester, _Refusing(status: 403, body: {'detail': refused}));
      await reachTemplates(tester);
      expectTemplatesSay(tester, refused);
    });

    testWidgets('404: the server has no record of it', (tester) async {
      await pump(tester, _Refusing(status: 404));
      await reachTemplates(tester);
      expectTemplatesSay(tester, 'The server has no record of it — it may have been removed');
    });

    testWidgets('500: the server failed, and it is worth trying again', (tester) async {
      await pump(tester, _Refusing(status: 500));
      await reachTemplates(tester);
      expectTemplatesSay(tester, 'The server had a problem (HTTP 500) — try again shortly');
    });

    testWidgets('no answer at all: the connection, said only here', (tester) async {
      await pump(tester, _Refusing());
      await reachTemplates(tester);
      expectTemplatesSay(tester, "Couldn't reach the server — check your connection");
    });
  });

  testWidgets('Try again really retries: the second call succeeds and the templates appear',
      (tester) async {
    final adapter = _Refusing(status: 500, times: 1);
    await pump(tester, adapter);
    await reachTemplates(tester);
    expectTemplatesSay(tester, 'The server had a problem (HTTP 500) — try again shortly');

    await tester.tap(find.widgetWithText(OutlinedButton, 'Try again'));
    await tester.pumpAndSettle();

    expect(adapter.refusals, 1);
    expect(find.textContaining('Could not load templates'), findsNothing);
    final preset =
        (fixtureJson('templates_10_science')['presets'] as List).first as Map<String, dynamic>;
    expect(find.text(preset['name'] as String), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('a template the server no longer has: the chapters step says so, and offers the retry',
      (tester) async {
    // The templates list loads; the availability check for the chosen
    // template 404s, as it would for a template a colleague has just deleted.
    final adapter = _Refusing(status: 404, where: (p) => p.endsWith('/availability'));
    await pump(tester, adapter);
    await reachTemplates(tester);

    final preset =
        (fixtureJson('templates_10_science')['presets'] as List).first as Map<String, dynamic>;
    final use = find.descendant(
      of: find.ancestor(of: find.text(preset['name'] as String), matching: find.byType(Card)),
      matching: find.text('Use'),
    );
    await tester.scrollUntilVisible(use, 200, scrollable: find.byType(Scrollable).first);
    await tester.pumpAndSettle();
    await tester.tap(use);
    await tester.pumpAndSettle();

    expect(
        find.text(
            'Could not check the bank: The server has no record of it — it may have been removed'),
        findsOneWidget);
    expect(find.widgetWithText(TextButton, 'Check again'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
