// R-C4 (EX-3): the main builder sent no tier, so a Foundation or Advanced
// paper could only be made from the quick dialog. The builder now offers the
// three versions where the server's availability check says one could print
// other questions, and sends the teacher's choice with the generate request.
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/paper_builder_api.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';

import 'fixture_api.dart';

Future<void> settle(WidgetTester tester, Future<Object?> call) async {
  final done = call.then((_) {});
  await tester.pumpAndSettle();
  await done;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_tier_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async {
    await Hive.close();
  });

  setUp(() => LocalStore.instance.box.clear());

  Future<(PaperBuilderController, FixtureAdapter)> halfYearly(WidgetTester tester) async {
    final adapter = FixtureAdapter();
    final c = PaperBuilderController(
      api: fixtureApi(adapter),
      schoolId: 'school_1',
      memory: BuilderMemory(fixtureTeacherId),
      savePdf: (_, __) async {},
    );
    addTearDown(c.dispose);
    await settle(tester, c.start());
    c.pickGrade(10);
    c.pickSubject('Science');
    await settle(tester, c.confirmClassSubject());
    final half = c.templates!.presets.firstWhere((t) => t.id == 'preset:cbse:10:science:half_yearly');
    await settle(tester, c.useTemplate(half));
    return (c, adapter);
  }

  Map<String, dynamic> lastGenerate(FixtureAdapter adapter) => Map<String, dynamic>.from(
      adapter.requests.lastWhere((r) => r.path == '/papers/generate-from-template').body as Map);

  testWidgets('where the bank judges the levels, the chosen version is sent', (tester) async {
    final (c, adapter) = await halfYearly(tester);
    c.availability = AvailabilityView.fromJson({
      ...fixtureJson('availability_10_science_half'),
      'tiers': {'available': true, 'sentence': ''},
    });
    expect(c.tierChoice, isTrue);
    c.setTier('advanced');
    await settle(tester, c.generate());
    expect(c.paper, isNotNull, reason: c.generateError);
    expect(lastGenerate(adapter)['tier'], 'advanced');
  });

  testWidgets('where it judges none, no version is offered and none is sent', (tester) async {
    final (c, adapter) = await halfYearly(tester);
    c.availability = AvailabilityView.fromJson({
      ...fixtureJson('availability_10_science_half'),
      'tiers': {'available': false, 'sentence': 'No question of these marks has a judged difficulty.'},
    });
    expect(c.tierChoice, isFalse);
    c.setTier('foundation');          // left over from another template
    await settle(tester, c.generate());
    expect(lastGenerate(adapter).containsKey('tier'), isFalse);
  });
}
