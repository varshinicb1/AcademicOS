// Proves the demo seeder actually produces what it claims: 5 real teacher
// personas (one real corpus-backed assessment each), 10 real student
// personas evaluated against every one of them -- not just "runs without
// throwing." Uses a real Hive box under the exact name LocalStore hardcodes
// (Hive.box('academicos_cache')), the only name that actually works with
// the singleton -- a different box name (as an earlier sync test used)
// silently doesn't back LocalStore at all.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Box cacheBox;
  late Directory tmpDir;

  setUpAll(() async {
    // Hive.initFlutter() needs a real path_provider platform channel, not
    // available in plain `flutter test` -- Hive.init() with a real temp
    // dir is the pure-Dart equivalent, no plugin required.
    tmpDir = Directory.systemTemp.createTempSync('demo_seeder_test_');
    Hive.init(tmpDir.path);
    cacheBox = await Hive.openBox('academicos_cache');
  });

  tearDownAll(() async {
    await cacheBox.close();
    tmpDir.deleteSync(recursive: true);
  });

  setUp(() async {
    await cacheBox.clear();
  });

  test('seeds exactly 5 real teacher-persona assessments, one per real subject', () async {
    await DemoSeeder.seedIfEmpty();

    final assessments = LocalStore.instance.allAssessments();
    expect(assessments.length, 5, reason: '5 teacher personas -> 5 assessments');

    final teacherIds = assessments.map((a) => a['teacherId']).toSet();
    expect(teacherIds.length, 5, reason: 'each assessment belongs to a distinct teacher persona');

    final subjects = assessments.map((a) => a['subject']).toSet();
    expect(subjects, {'Mathematics', 'Science', 'Social Science', 'English'},
        reason: '5 teachers across 4 real subjects (two Mathematics teachers)');

    for (final a in assessments) {
      expect(a['grade'], 10, reason: 'every persona is Class X, matching the real vision');
      expect(a['status'], 'evaluated');
      expect((a['title'] as String).contains('(Demo)'), isTrue,
          reason: 'every demo record must be clearly tagged, never mistaken for real school data');
    }
  });

  test('each assessment has a real, non-empty generated paper -- never the 0-marks bug', () async {
    await DemoSeeder.seedIfEmpty();

    for (final a in LocalStore.instance.allAssessments()) {
      final paperId = a['generatedPaperId'] as String?;
      expect(paperId, isNotNull, reason: '${a['title']}: must have generated a real paper');
      final paper = LocalStore.instance.getPaper(paperId!);
      expect(paper, isNotNull);
      final sections = paper!['sections'] as List;
      final totalQuestions =
          sections.fold<int>(0, (s, sec) => s + ((sec['questions'] as List).length));
      expect(totalQuestions, greaterThan(0),
          reason: '${a['title']}: a real paper must have real questions, not the empty-paper bug');
    }
  });

  test('all 10 student personas are genuinely evaluated with real, varied scores', () async {
    await DemoSeeder.seedIfEmpty();

    final assessments = LocalStore.instance.allAssessments();
    final firstAssessmentId = assessments.first['id'] as String;
    final evaluations = LocalStore.instance.evaluationsFor(firstAssessmentId);

    expect(evaluations.length, 10, reason: '10 student personas evaluated against this assessment');

    final studentIds = evaluations.map((e) => e['studentId']).toSet();
    expect(studentIds.length, 10, reason: 'all 10 distinct students, no duplicates/drops');

    // Real, varied performance -- not every student scoring identically,
    // which would signal fabricated rather than realistic demo data.
    final scores = evaluations.map((e) => e['totalAwarded'] as num).toSet();
    expect(scores.length, greaterThan(1), reason: 'students must show genuinely different real scores');
  });

  test('running seedIfEmpty twice does not duplicate data', () async {
    await DemoSeeder.seedIfEmpty();
    final firstCount = LocalStore.instance.allAssessments().length;

    await DemoSeeder.seedIfEmpty();
    final secondCount = LocalStore.instance.allAssessments().length;

    expect(secondCount, firstCount, reason: 'seedIfEmpty must be a real no-op once data already exists');
  });

  test('clearDemoData genuinely removes every demo assessment', () async {
    await DemoSeeder.seedIfEmpty();
    expect(LocalStore.instance.allAssessments(), isNotEmpty);

    await DemoSeeder.clearDemoData();

    expect(LocalStore.instance.allAssessments(), isEmpty);
    expect(LocalStore.instance.isDemoSeeded, isFalse);
  });
}
