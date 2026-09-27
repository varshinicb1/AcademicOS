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

import 'package:academicos/core/di/service_locator.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/paper_builder_api.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/pages/paper_builder_page.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';
import 'package:academicos/presentation/paper_builder/widgets/bank_picker.dart';
import 'package:academicos/presentation/paper_builder/widgets/finish_step.dart';
import 'package:academicos/presentation/paper_builder/widgets/template_step.dart';

import 'fixture_api.dart';

const _phone = Size(375, 812);

/// Runs a controller call the way a tap on a step runs it: the frames are
/// pumped while the request is in flight, and only then is the call's own
/// result awaited.
///
/// Awaiting the call directly instead does not come back -- inside a widget
/// test nothing advances the clock the response stream needs. Measured
/// 2026-09-23: written that way these tests hung on the first await until the
/// run was killed; pumped, each finishes in under a second.
Future<void> settle(WidgetTester tester, Future<Object?> call) async {
  final done = call.then((_) {});
  await tester.pumpAndSettle();
  await done;
}

/// Everything the builder asks the server for once a class is chosen. The
/// catalog it reads on opening is left out: its refusal is the first step's
/// own sentence (builder_grades_test.dart), and refusing it here would stop
/// every test before the step it is about.
bool _everything(String path) => !path.endsWith('/catalog');

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

/// The fixtures, except that the template LIST fails once, the first time it
/// is asked for after a template has been saved: the transient 500 that lands
/// on the refresh a save does (PaperBuilderController._refreshTemplateLists),
/// while the save the teacher asked for succeeded. The next refresh goes
/// through, which is how a banner that outlived its failure shows up.
class _RefreshFails implements HttpClientAdapter {
  final FixtureAdapter fixtures = FixtureAdapter();
  bool _saved = false;
  int refusals = 0;

  @override
  Future<ResponseBody> fetch(
      RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final path = o.uri.path;
    if (_saved && o.method == 'GET' && path.endsWith('/teacher-templates') && refusals < 1) {
      refusals++;
      return ResponseBody.fromString(jsonEncode(const <String, dynamic>{}), 500, headers: {
        Headers.contentTypeHeader: ['application/json'],
      });
    }
    if (o.method == 'POST' && path.endsWith('/teacher-templates')) _saved = true;
    return fixtures.fetch(o, requestStream, cancelFuture);
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
  ///
  /// [interceptors] go on the Dio the builder's API is built from, exactly as
  /// service_locator.dart puts them on the app's.
  Future<void> pump(WidgetTester tester, _Refusing adapter,
      {List<Interceptor> interceptors = const []}) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: PaperBuilderPage(
        api: fixtureApi(adapter, interceptors: interceptors),
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

  /// [expected] is the whole sentence on the step; [retry] is whether the
  /// step offers the action that tries again.
  ///
  /// It is offered only where sending the same request again could succeed
  /// (api_error.dart's [isRetryable]): a 401, 403 or 404 is refused the same
  /// way every time, so a "Try again" there is a button that cannot work,
  /// and on a 401 it competes with the session interceptor already sending
  /// the teacher to Sign in. Task 803's own brief asked for a Retry on every
  /// branch and the helper it told this builder to adopt says the opposite;
  /// the helper wins, four other screens already read it that way, and
  /// PaperBuilderController's class doc records the decision.
  void expectTemplatesSay(WidgetTester tester, String expected, {required bool retry}) {
    expect(find.text('Could not load templates: $expected'), findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Try again'), retry ? findsOneWidget : findsNothing);
    expect(tester.takeException(), isNull);
  }

  group('a failed template load says what actually happened', () {
    // The 401 branch is the one with no button, so the sentence is only half
    // of what a teacher gets: the other half is the session interceptor
    // clearing the dead token and sending them to Sign in. That half is the
    // whole reason this branch may go without a Retry, so it is tested here
    // rather than assumed -- with the production sessionInterceptor() on the
    // builder's Dio, as service_locator.dart installs it (line 87; the
    // builder's PaperBuilderApi is built from that same sl<Dio>()). Without
    // it this test would read identically in a build where the interceptor
    // had been dropped and the teacher was left on a dead screen: a sentence,
    // no button, and nothing happening.
    //
    // bounceToLogin()'s observable effect here is the cleared token; the
    // GoRouter half needs a registered router, which a widget test has none
    // of (the call is already guarded for exactly that -- it runs before
    // app_router.dart registers one at startup too).
    testWidgets('401: the session is over, and the session interceptor ends it', (tester) async {
      LocalStore.instance.authToken = 'a-session-the-server-no-longer-honours';
      await pump(tester, _Refusing(status: 401, body: {'detail': 'Not authenticated'}),
          interceptors: [sessionInterceptor()]);
      await reachTemplates(tester);
      expectTemplatesSay(tester, "You're signed out — sign in again", retry: false);
      expect(LocalStore.instance.authToken, isNull,
          reason: 'the interceptor must clear the dead session and bounce to Sign in -- '
              'that recovery is why this branch is allowed no Retry button');
    });

    testWidgets('401 says the same thing on the step with no interceptor in the way',
        (tester) async {
      await pump(tester, _Refusing(status: 401, body: {'detail': 'Not authenticated'}));
      await reachTemplates(tester);
      expectTemplatesSay(tester, "You're signed out — sign in again", retry: false);
    });

    testWidgets('403 with no reason: the account lacks access', (tester) async {
      await pump(tester, _Refusing(status: 403));
      await reachTemplates(tester);
      expectTemplatesSay(tester, "You don't have access to that", retry: false);
    });

    testWidgets("403 for a school the teacher is not in keeps the server's reason", (tester) async {
      const refused = 'You are not a teacher at this school';
      await pump(tester, _Refusing(status: 403, body: {'detail': refused}));
      await reachTemplates(tester);
      expectTemplatesSay(tester, refused, retry: false);
    });

    testWidgets('404: the server has no record of it', (tester) async {
      await pump(tester, _Refusing(status: 404));
      await reachTemplates(tester);
      expectTemplatesSay(tester, 'The server has no record of it — it may have been removed', retry: false);
    });

    testWidgets('500: the server failed, and it is worth trying again', (tester) async {
      await pump(tester, _Refusing(status: 500));
      await reachTemplates(tester);
      expectTemplatesSay(tester, 'The server had a problem (HTTP 500) — try again shortly', retry: true);
    });

    testWidgets('no answer at all: the connection, said only here', (tester) async {
      await pump(tester, _Refusing());
      await reachTemplates(tester);
      expectTemplatesSay(tester, "Couldn't reach the server — check your connection", retry: true);
    });
  });

  testWidgets('Try again really retries: the second call succeeds and the templates appear',
      (tester) async {
    final adapter = _Refusing(status: 500, times: 1);
    await pump(tester, adapter);
    await reachTemplates(tester);
    expectTemplatesSay(tester, 'The server had a problem (HTTP 500) — try again shortly', retry: true);

    await tester.tap(find.widgetWithText(OutlinedButton, 'Try again'));
    await tester.pumpAndSettle();

    expect(adapter.refusals, 1);
    expect(find.textContaining('Could not load templates'), findsNothing);
    final preset =
        (fixtureJson('templates_10_science')['presets'] as List).first as Map<String, dynamic>;
    expect(find.text(preset['name'] as String), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('a template the server no longer has: the chapters step says so, and sends them back',
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
    // No "Check again": a template a colleague has just deleted answers 404
    // to every check that follows, so the button would only teach the teacher
    // to press it. The recovery is already on the step -- "Change" on the
    // template row (the one below the class/subject banner's own), back to
    // the templates that do exist -- and it works:
    expect(find.widgetWithText(TextButton, 'Check again'), findsNothing);
    await tester.tap(find.widgetWithText(TextButton, 'Change').last);
    await tester.pumpAndSettle();
    expect(find.text('CBSE patterns'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  /// Scrolls [f] into view and taps it (the steps are ListViews: a widget
  /// below the fold is not in the tree at all, so it can be neither found
  /// nor tapped).
  Future<void> tapVisible(WidgetTester tester, Finder f) async {
    await tester.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
    Scrollable.ensureVisible(f.evaluate().first, alignment: 0.5);
    await tester.pumpAndSettle();
    await tester.tap(f);
    await tester.pumpAndSettle();
  }

  /// "Use" on the Class 10 Science half-yearly preset: the one the fixtures
  /// captured a bank check for, so the chapters step it lands on is the step
  /// a teacher actually sees.
  Future<void> useHalfYearly(WidgetTester tester) async {
    final preset = (fixtureJson('templates_10_science')['presets'] as List)
        .firstWhere((p) => p['examType'] == 'half_yearly') as Map;
    await tapVisible(
        tester,
        find.descendant(
          of: find.ancestor(of: find.text(preset['name'] as String), matching: find.byType(Card)),
          matching: find.text('Use'),
        ));
  }

  // The chapters step (scope_step.dart). This is where a 401 lands once the
  // templates step has succeeded -- the commonest way a teacher meets an
  // expired session inside the builder -- and until now nothing pinned what
  // it offers: an unconditional `OutlinedButton.icon(onPressed: c.loadChapters)`
  // put back here would leave the whole suite green.
  group('a failed chapter load offers the recovery that works, and only that', () {
    testWidgets('403: the sentence, the fallback, and no button that cannot work', (tester) async {
      await pump(tester, _Refusing(status: 403, where: (p) => p.endsWith('/chapters')));
      await reachTemplates(tester);
      await useHalfYearly(tester);

      // The bank check itself went through, so the step can still do the one
      // thing it offers instead of the chapter list.
      expect(find.text('Ready: every section can be filled from the whole syllabus.'),
          findsOneWidget);
      await tester.scrollUntilVisible(
          find.text("Could not load chapters: You don't have access to that"), 200,
          scrollable: find.byType(Scrollable).first);
      expect(find.text('You can still generate from the whole syllabus.'), findsOneWidget);
      expect(find.widgetWithText(OutlinedButton, 'Try again'), findsNothing,
          reason: 'a 403 answers the same way every time; the fallback above IS the recovery');
      expect(tester.takeException(), isNull);
    });

    testWidgets('500: the same shape, with the button -- and it really reloads', (tester) async {
      final adapter = _Refusing(status: 500, where: (p) => p.endsWith('/chapters'), times: 1);
      await pump(tester, adapter);
      await reachTemplates(tester);
      await useHalfYearly(tester);

      await tester.scrollUntilVisible(
          find.text('Could not load chapters: The server had a problem (HTTP 500) — try again shortly'),
          200,
          scrollable: find.byType(Scrollable).first);
      await tapVisible(tester, find.widgetWithText(OutlinedButton, 'Try again'));

      expect(adapter.refusals, 1);
      expect(find.textContaining('Could not load chapters'), findsNothing);
      await tester.scrollUntilVisible(find.text('Whole syllabus (all chapters)'), 200,
          scrollable: find.byType(Scrollable).first);
      expect(tester.takeException(), isNull);
    });
  });

  // The bank picker (bank_picker.dart), the fourth site caaf8e6 changed and
  // the second with no test: `retry: true` put back in its `_message` call
  // would also leave the suite green. Pumped on its own, as the sheet opens:
  // it searches the moment it is built.
  group('a failed bank search in the picker', () {
    Future<void> pumpPicker(WidgetTester tester, _Refusing adapter) async {
      tester.view.physicalSize = _phone;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final c = PaperBuilderController(
        api: fixtureApi(adapter),
        schoolId: 'school_1',
        memory: BuilderMemory(fixtureTeacherId),
        savePdf: (bytes, name) async {},
      );
      addTearDown(c.dispose);
      c.grade = 10;
      c.subject = 'Science';
      await tester.pumpWidget(
          MaterialApp(home: Scaffold(body: BankPicker(c: c, slot: '27', marks: 3))));
      await tester.pumpAndSettle();
    }

    testWidgets('403: no "Try again" on a search the server refuses every time', (tester) async {
      await pumpPicker(tester, _Refusing(status: 403));
      expect(find.text("Could not search the bank: You don't have access to that"), findsOneWidget);
      expect(find.widgetWithText(TextButton, 'Try again'), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets('500: the button is there, and the retry brings the questions', (tester) async {
      final adapter = _Refusing(status: 500, times: 1);
      await pumpPicker(tester, adapter);
      expect(
          find.text('Could not search the bank: The server had a problem (HTTP 500) — try again shortly'),
          findsOneWidget);

      await tester.tap(find.widgetWithText(TextButton, 'Try again'));
      await tester.pumpAndSettle();

      expect(adapter.refusals, 1);
      expect(find.textContaining('Could not search the bank'), findsNothing);
      expect(find.text(fixtureJsonList('search_10_science_3m').first['stem'] as String),
          findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });

  // The finish step (finish_step.dart). It was not touched by caaf8e6 and
  // kept the sentence the deleted apiErrorMessage was written for -- one run
  // on into the next ("...You don't have access to that Tap Download to try
  // again."), telling a teacher whose session had expired to press the one
  // button the server refuses every time.
  group('a failed download says whether pressing Download again is worth it', () {
    /// A saved paper, reached through the real controller (the finish step
    /// needs `result`), with the finish step on screen.
    Future<PaperBuilderController> downloaded(WidgetTester tester, _Refusing adapter) async {
      tester.view.physicalSize = _phone;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final c = PaperBuilderController(
        api: fixtureApi(adapter),
        schoolId: 'school_1',
        memory: BuilderMemory(fixtureTeacherId),
        savePdf: (bytes, name) async {},
      );
      addTearDown(c.dispose);
      c.grade = 10;
      c.subject = 'Science';
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: AnimatedBuilder(
            animation: c,
            builder: (_, __) => c.result == null ? const SizedBox.shrink() : FinishStep(c: c),
          ),
        ),
      ));
      await settle(tester, c.loadTemplates());
      await settle(
          tester,
          c.useTemplate(
              c.templates!.presets.firstWhere((t) => t.examType == 'half_yearly')));
      await settle(tester, c.generate());
      expect(c.result, isNotNull, reason: 'the paper must be saved before it can be downloaded');
      await settle(tester, c.downloadAll());
      return c;
    }

    testWidgets('403: one sentence, and no instruction to press Download again', (tester) async {
      final c = await downloaded(tester, _Refusing(status: 403, where: (p) => p.contains('/export/')));
      expect(c.downloadRetryable, isFalse);
      expect(find.text("Download failed: You don't have access to that."), findsOneWidget);
      expect(find.textContaining('Tap Download to try again'), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets('500: the sentence ends, and Download is worth pressing again', (tester) async {
      final c = await downloaded(tester, _Refusing(status: 500, where: (p) => p.contains('/export/')));
      expect(c.downloadRetryable, isTrue);
      expect(
          find.text('Download failed: The server had a problem (HTTP 500) — try again shortly. '
              'Tap Download to try again.'),
          findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });

  // A failure that is NOT the failure of what the teacher asked for: the save
  // or duplicate went through, and the list refresh behind it did not. Until
  // 2026-09-23 the step showed that banner INSTEAD of the templates, so a
  // transient 500 on the refresh took away the whole list the teacher was
  // reading -- and, because the success path never cleared the field, left it
  // taken away after the next refresh had quietly reloaded it.
  group('a refresh that fails behind a save keeps the list the teacher has', () {
    /// The template step alone: `saveTemplate` sends the teacher on to the
    /// chapters, and what is pinned here is what the template step shows --
    /// the step they came from, and go back to with "Change".
    Future<void> pumpStep(WidgetTester tester, PaperBuilderController c) async {
      tester.view.physicalSize = _phone;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(body: AnimatedBuilder(animation: c, builder: (_, __) => TemplateStep(c: c))),
      ));
      await tester.pumpAndSettle();
    }

    /// The real controller for class 10 Science, its step pumped and its
    /// templates loaded.
    Future<PaperBuilderController> loaded(WidgetTester tester, HttpClientAdapter adapter) async {
      final c = PaperBuilderController(
        api: fixtureApi(adapter),
        schoolId: 'school_1',
        memory: BuilderMemory(fixtureTeacherId),
        savePdf: (bytes, name) async {},
      );
      addTearDown(c.dispose);
      c.grade = 10;
      c.subject = 'Science';
      await pumpStep(tester, c);
      await settle(tester, c.loadTemplates());
      return c;
    }

    /// The draft the fixtures were captured for: "Weekly check", 22 marks,
    /// A 10x1 + B 4x3 (the create route answers only a matching total).
    PaperTemplateView draft() => PaperTemplateView(
          name: 'Weekly check',
          grade: 10,
          subject: 'Science',
          totalMarks: 22,
          durationMinutes: 45,
          sections: [
            TemplateSectionView(title: 'Section A', questionCount: 10, marksEach: 1),
            TemplateSectionView(title: 'Section B', questionCount: 4, marksEach: 3),
          ],
        );

    String presetName() =>
        ((fixtureJson('templates_10_science')['presets'] as List).first as Map)['name'] as String;

    testWidgets('the banner is above the templates, not instead of them', (tester) async {
      final adapter = _RefreshFails();
      final c = await loaded(tester, adapter);
      expect(find.text(presetName()), findsOneWidget);

      await settle(tester, c.saveTemplate(draft(), asNew: false, ownerId: fixtureTeacherId));

      expect(adapter.refusals, 1, reason: 'the save succeeded; only the refresh behind it failed');
      expect(find.text('Could not load templates: The server had a problem (HTTP 500) — try again shortly'),
          findsOneWidget);
      // Still there: the groups, and the templates the step already held.
      expect(find.text('My templates'), findsOneWidget);
      expect(find.text('CBSE patterns'), findsOneWidget);
      expect(find.text(presetName()), findsOneWidget);
      // A 500 can pass next time, so this one does offer the reload.
      expect(find.widgetWithText(OutlinedButton, 'Try again'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a later refresh that succeeds takes the banner away', (tester) async {
      final c = await loaded(tester, _RefreshFails());
      await settle(tester, c.saveTemplate(draft(), asNew: false, ownerId: fixtureTeacherId));
      expect(find.textContaining('Could not load templates'), findsOneWidget);

      // The next save's refresh goes through. The banner has been answered.
      await settle(tester, c.saveTemplate(draft(), asNew: false, ownerId: fixtureTeacherId));

      expect(find.textContaining('Could not load templates'), findsNothing);
      expect(c.templatesError, isNull);
      expect(find.text('Weekly check'), findsOneWidget, reason: 'the reloaded list holds the saved template');
      expect(tester.takeException(), isNull);
    });
  });
}
