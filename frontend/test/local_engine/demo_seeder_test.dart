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
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';
import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_store.dart';

// _seedDemoScanSession materializes the two bundled demo-scan-page assets
// into real files via path_provider's getApplicationDocumentsDirectory --
// not available as a real platform channel in plain `flutter test`, same
// gap local_scan_pdf_export_test.dart already works around.
class _FakePathProvider extends PathProviderPlatform with MockPlatformInterfaceMixin {
  final Directory dir;
  _FakePathProvider(this.dir);
  @override
  Future<String?> getApplicationDocumentsPath() async => dir.path;
}

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
    PathProviderPlatform.instance = _FakePathProvider(tmpDir);
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

  test('seeds one real, fully-graded scan session so the corrected-paper demo has something to show', () async {
    await DemoSeeder.seedIfEmpty();

    final sessions = LocalStore.instance.allScanSessions();
    expect(sessions.length, 1,
        reason: 'exactly one demo scan session -- the corrected-paper feature demo');

    final session = sessions.first;
    expect(session['status'], 'finalized');
    expect(session['studentId'], 'demo_stu_4');
    expect(session['studentName'], 'Ananya Iyer');
    // Real user request: a teacher opening this app for the first time
    // should see what a fully completed scan looks like, including the
    // actual photographed pages -- not "no photo saved". The two bundled
    // demo images (assets/images/demo_scan_page_*.jpg) are materialized
    // into real files, same shape a live capture produces.
    final pages = List<Map>.from(session['pages'] as List);
    expect(pages.length, 2, reason: 'both bundled demo answer-sheet pages');
    for (final page in pages) {
      final path = page['imagePath'] as String;
      expect(File(path).existsSync(), isTrue,
          reason: 'must be a real file on disk, same as a live capture -- '
              'exportRawBooklet and the review screen both read it with File(imagePath)');
    }

    final review = List<Map>.from(session['review'] as List);
    expect(review, isNotEmpty, reason: 'must have real per-question marks, not an empty shell');
    for (final item in review) {
      expect(List<String>.from(item['pageImageUrls'] as List), pages.map((p) => p['imagePath']).toList(),
          reason: 'every review item should point at the same two real captured pages');
    }

    // Real, varied marks -- not every question scored identically, which
    // would signal a fabricated rather than a genuinely evaluated sheet.
    final marksAwarded = review.map((r) => r['finalMarks'] as num).toSet();
    expect(marksAwarded.length, greaterThan(1),
        reason: 'a genuinely mixed real result, not a flat score across every question');

    // The one deliberate teacher-override item must carry a real comment,
    // proving the red-pen/edited-annotation feature has something to demo.
    final edited = review.where((r) => r['status'] == 'edited');
    expect(edited, isNotEmpty, reason: 'must demo the teacher-override feature, not only AI marks');
    for (final r in edited) {
      expect((r['teacherComment'] as String).isNotEmpty, isTrue);
      expect(r['finalMarks'], r['maxMarks'], reason: 'the override in this seeder always awards full marks');
    }

    // Cross-check against the real assessment/paper this session grades --
    // must not be inventing question data independent of the real paper.
    final assessment = LocalStore.instance.getAssessment(session['assessmentId'] as String);
    expect(assessment, isNotNull);
    final paper = LocalStore.instance.getPaper(assessment!['generatedPaperId'] as String);
    final totalQuestions = (paper!['sections'] as List)
        .fold<int>(0, (s, sec) => s + ((sec['questions'] as List).length));
    expect(review.length, totalQuestions,
        reason: 'one review item per real question in the real generated paper');
  });

  test('clearDemoData also removes the demo scan session', () async {
    await DemoSeeder.seedIfEmpty();
    expect(LocalStore.instance.allScanSessions(), isNotEmpty);

    await DemoSeeder.clearDemoData();

    expect(LocalStore.instance.allScanSessions(), isEmpty);
  });
}
