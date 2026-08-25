// Proves report card generation is real: aggregates a real student's real
// evaluated assessments and mastery record into a real, non-trivial PDF --
// the "report card generation" feature the user explicitly requested and
// that had never been built.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_report_card.dart';
import 'package:academicos/core/local_engine/local_report_card_pdf_export.dart';
import 'package:academicos/core/local_engine/local_store.dart';

class _FakePathProvider extends PathProviderPlatform with MockPlatformInterfaceMixin {
  final Directory dir;
  _FakePathProvider(this.dir);
  @override
  Future<String?> getApplicationDocumentsPath() async => dir.path;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tmpDir;
  late Box cacheBox;

  setUpAll(() async {
    tmpDir = Directory.systemTemp.createTempSync('report_card_test_');
    Hive.init(tmpDir.path);
    cacheBox = await Hive.openBox('academicos_cache');
    PathProviderPlatform.instance = _FakePathProvider(tmpDir);
  });

  tearDownAll(() async {
    await cacheBox.close();
    tmpDir.deleteSync(recursive: true);
  });

  setUp(() async {
    await cacheBox.clear();
  });

  test('aggregates a real student\'s real evaluations across subjects, not invented data', () async {
    await DemoSeeder.seedIfEmpty();

    final data = LocalReportCardService.generate('demo_stu_1');

    expect(data.studentName, isNot('demo_stu_1'), reason: 'must resolve the real persisted name, not the raw id');
    expect(data.schoolName, isNotEmpty);
    expect(data.subjects, isNotEmpty, reason: 'demo_stu_1 has real evaluated assessments across multiple subjects');

    // Cross-check one subject's totals directly against LocalStore -- the
    // report card must not invent numbers independently of real storage.
    final mathAssessments = LocalStore.instance
        .allAssessments()
        .where((a) => a['subject'] == 'Mathematics')
        .toList();
    var expectedAwarded = 0, expectedMax = 0;
    for (final a in mathAssessments) {
      for (final e in LocalStore.instance.evaluationsFor(a['id'] as String)) {
        if (e['studentId'] == 'demo_stu_1') {
          expectedAwarded += (e['totalAwarded'] as num).toInt();
          expectedMax += (e['totalMax'] as num).toInt();
        }
      }
    }
    final mathRow = data.subjects.firstWhere((s) => s.subject == 'Mathematics');
    expect(mathRow.totalAwarded, expectedAwarded);
    expect(mathRow.totalMax, expectedMax);
  });

  test('a student with zero evaluations gets an honest empty report, not fabricated marks', () async {
    await DemoSeeder.seedIfEmpty();
    final data = LocalReportCardService.generate('a_student_who_does_not_exist');
    expect(data.subjects, isEmpty);
    expect(data.overallPercentage, 0.0);
  });

  test('exports a real, non-trivial PDF file', () async {
    await DemoSeeder.seedIfEmpty();
    final data = LocalReportCardService.generate('demo_stu_1');
    final path = await LocalReportCardPdfExporter.export(data);

    final file = File(path);
    expect(await file.exists(), isTrue);
    final bytes = await file.readAsBytes();
    expect(bytes.length, greaterThan(1000), reason: 'a real subject table + mastery section should not compress to almost nothing');
  });
}
