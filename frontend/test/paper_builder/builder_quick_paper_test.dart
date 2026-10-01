// Audit D57: a quick Science 10 paper asked for 40 marks printed 28, and the
// web said so only after the paper was saved (where it said anything).
//
// The builder's "Quick paper by total marks" asks the server for a preview
// first: what the paper would hold -- all the marks, rebalanced where the
// bank cannot fill a section, or, where the bank truly cannot, the shortfall
// section by section -- and saves only when the teacher says so. The answers
// are the real backend's (scripts/capture_paper_builder_fixtures.py).
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';
import 'package:academicos/presentation/paper_builder/widgets/quick_paper_dialog.dart';

import 'fixture_api.dart';

/// The fixtures, plus quick-generate answered from its captures by subject,
/// marks and preview.
class _QuickAdapter implements HttpClientAdapter {
  final FixtureAdapter fixtures = FixtureAdapter();
  final List<Map<String, dynamic>> quick = [];

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final path = o.uri.path.replaceFirst('/api/v1', '');
    final body = o.data is String ? jsonDecode(o.data as String) : o.data;
    if (o.method == 'POST' && path == '/papers/quick-generate' && body is Map) {
      quick.add(Map<String, dynamic>.from(body));
      final name = switch ((body['subject'], body['totalMarks'], body['preview'])) {
        ('Science', 40, true) => 'quick_preview_10_science_40',
        ('Science', 40, false) => 'quick_10_science_40',
        ('Social Science', 80, true) => 'quick_preview_10_social_80',
        _ => null,
      };
      if (name == null) return _json(501, {'detail': 'no captured quick paper for $body'});
      return _json(200, fixtureJson(name));
    }
    return fixtures.fetch(o, requestStream, cancelFuture);
  }

  ResponseBody _json(int status, Object body) => ResponseBody.fromString(jsonEncode(body), status, headers: {
        Headers.contentTypeHeader: ['application/json'],
      });

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_quick_paper_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async {
    await Hive.close();
  });

  setUp(() => LocalStore.instance.box.clear());

  Future<(PaperBuilderController, _QuickAdapter)> open(WidgetTester tester, String subject) async {
    tester.view.physicalSize = const Size(900, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final adapter = _QuickAdapter();
    final c = PaperBuilderController(
      api: fixtureApi(adapter),
      schoolId: 'school_1',
      memory: BuilderMemory(fixtureTeacherId),
      savePdf: (_, __) async {},
    )
      ..grade = 10
      ..subject = subject;
    addTearDown(c.dispose);
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => TextButton(onPressed: () => showQuickPaperDialog(context, c), child: const Text('open')),
        ),
      ),
    ));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    return (c, adapter);
  }

  String text(WidgetTester tester, String key) => tester.widget<Text>(find.byKey(ValueKey(key))).data!;

  testWidgets('Science 10 at 40 marks: the preview holds all 40, and only Save saves it', (tester) async {
    final (c, adapter) = await open(tester, 'Science');
    await tester.tap(find.byKey(const ValueKey('quick-check')));
    await tester.pumpAndSettle();

    expect(adapter.quick.single['preview'], isTrue);
    final preview = fixtureJson('quick_preview_10_science_40');
    final layout = [
      for (final s in preview['sections'] as List)
        '${s['label']} ${(s['questions'] as List).length} × ${(s['questions'] as List).first['marks']}',
    ].join(', ');
    expect(text(tester, 'quick-preview-total'), 'Holds all 40 marks: 19 questions, $layout.');
    expect(find.textContaining('To make the 40 marks asked for'), findsOneWidget);
    expect(find.text('Save this paper'), findsOneWidget);
    expect(c.paper, isNull, reason: 'nothing saved by a preview');

    await tester.tap(find.byKey(const ValueKey('quick-save')));
    await tester.pumpAndSettle();
    final saved = adapter.quick.last;
    expect(saved['preview'], isFalse);
    expect(saved['totalMarks'], 40);
    expect(saved['teacherSeconds'], isA<num>());
    expect(c.step, BuilderStep.paper);
    expect(c.paperMarks, 40);
    expect(c.quickMarksAsked, 40);
    expect(c.fromTemplate, isFalse);
    expect(find.byType(QuickPaperDialog), findsNothing);
  });

  testWidgets('Social Science 10 at 80 marks: the shortfall by section is shown before anything is saved',
      (tester) async {
    final (c, adapter) = await open(tester, 'Social Science');
    await tester.tap(find.byKey(const ValueKey('quick-marks-80')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('quick-check')));
    await tester.pumpAndSettle();

    expect(text(tester, 'quick-preview-total'),
        'Holds 18 of the 80 marks asked for: the bank cannot make up the rest.');
    expect(find.text('Sections the bank cannot fill:'), findsOneWidget);
    for (final s in fixtureJson('quick_preview_10_social_80')['shortfall'] as List) {
      expect(find.textContaining('• Section ${s['label']} (${s['name']}): ${s['printed']} of ${s['asked']}'),
          findsOneWidget, reason: '$s');
    }
    expect(find.text('Save it short (18 of 80 marks)'), findsOneWidget);
    expect(adapter.quick.where((b) => b['preview'] == false), isEmpty);
    expect(c.paper, isNull);

    // A change of marks drops the check: it is never saved for other choices.
    await tester.tap(find.byKey(const ValueKey('quick-marks-40')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('quick-preview')), findsNothing);
    expect(find.byKey(const ValueKey('quick-check')), findsOneWidget);
  });
}
