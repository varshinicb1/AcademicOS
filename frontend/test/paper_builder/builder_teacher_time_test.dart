// Audit D49: "time saved" was the declared baseline times the paper count.
// What was recorded as the time to produce a paper was the server's compute
// (0.02-0.15 s); the teacher's time in the builder was timed nowhere.
//
// The builder now measures it: from opening (and after that, from the last
// paper it generated) to asking for the paper, and sends it with the
// generate request, where the server subtracts it from the baseline.
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/paper_builder/builder_memory.dart';
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';

import 'fixture_api.dart';

/// Runs a controller call with frames pumped while its request is in flight
/// (see builder_errors_test.dart's `settle`).
Future<void> settle(WidgetTester tester, Future<Object?> call) async {
  final done = call.then((_) {});
  await tester.pumpAndSettle();
  await done;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    Hive.init(Directory.systemTemp.createTempSync('builder_teacher_time_').path);
    await Hive.openBox('academicos_cache', bytes: Uint8List(0));
  });

  tearDownAll(() async {
    await Hive.close();
  });

  setUp(() => LocalStore.instance.box.clear());

  testWidgets('each generate request carries the teacher\'s time since opening, or since the last paper',
      (tester) async {
    var now = DateTime(2026, 10, 1, 9);
    final adapter = FixtureAdapter();
    final c = PaperBuilderController(
      api: fixtureApi(adapter),
      schoolId: 'school_1',
      memory: BuilderMemory(fixtureTeacherId),
      savePdf: (_, __) async {},
      clock: () => now,
    );
    addTearDown(c.dispose);
    await settle(tester, c.start());
    c.pickGrade(10);
    c.pickSubject('Science');
    await settle(tester, c.confirmClassSubject());
    final half = c.templates!.presets.firstWhere((t) => t.id == 'preset:cbse:10:science:half_yearly');
    await settle(tester, c.useTemplate(half));

    now = now.add(const Duration(minutes: 12, seconds: 30));
    await settle(tester, c.generate());
    expect(c.paper, isNotNull, reason: c.generateError);
    final sent = adapter.requests.lastWhere((r) => r.path == '/papers/generate-from-template');
    expect((sent.body as Map)['teacherSeconds'], 750.0);

    // The next paper's time starts when this one was generated.
    now = now.add(const Duration(minutes: 3));
    expect(c.teacherSeconds, 180.0);
  });
}
