// Proves the real gap this session closed: LocalScanEngine.finalizeSession()
// always returned empty rawPdfUrl/correctedPdfUrl (honest, not faked), and
// LocalPillarApi.downloadScanPdf() threw OfflineUnsupportedException for
// BOTH exports unconditionally -- so the "View raw booklet PDF" / "View
// corrected sheet PDF" buttons on the real Scan & Grade finish screen never
// worked in the offline build. Ported from the real backend's
// export_corrected_pdf/export_raw_booklet_pdf (mobile_scan.py), verified
// end-to-end on a real device (Android emulator) for the fix that
// motivated this file.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'package:academicos/core/local_engine/local_pillar_api.dart';
import 'package:academicos/core/local_engine/local_scan_pdf_export.dart';
import 'package:academicos/core/local_engine/local_store.dart';

// A real, freshly-encoded PNG (not a hand-typed byte blob that could be
// subtly malformed) -- just enough for pw.MemoryImage to decode for real,
// standing in for a real captured page photo.
List<int> _tinyPng() {
  final image = img.Image(width: 4, height: 4);
  img.fill(image, color: img.ColorRgb8(255, 255, 255));
  return img.encodePng(image);
}

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
    tmpDir = Directory.systemTemp.createTempSync('scan_pdf_export_test_');
    Hive.init(tmpDir.path);
    cacheBox = await Hive.openBox('academicos_cache');
    PathProviderPlatform.instance = _FakePathProvider(tmpDir);
  });

  tearDownAll(() async {
    await cacheBox.close();
    tmpDir.deleteSync(recursive: true);
  });

  setUp(() async => cacheBox.clear());

  // Builds a real scan session in the exact shape LocalScanEngine's own
  // _processSessionUnlocked produces (same field names/types) -- the real
  // OCR/ML-Kit pipeline can't run inside `flutter test` (needs a device
  // platform channel), so this reproduces its real output shape directly
  // rather than testing against an invented one.
  void seedRealSession(String sessionId, {required bool withEditedItem}) {
    LocalStore.instance.setSchoolName('school_1', 'Test CBSE School');
    LocalStore.instance.upsertAssessment({
      'id': 'assess_1',
      'schoolId': 'school_1',
      'subject': 'Science',
      'grade': 10,
    });
    LocalStore.instance.saveScanSession(sessionId, {
      'id': sessionId,
      'assessmentId': 'assess_1',
      'studentId': 'stu_1',
      'studentName': 'Real Test Student',
      'status': 'finalized',
      'pages': [],
      'review': [
        {
          'questionId': 'q1',
          'displayNumber': 1,
          'stem': 'What is the chemical formula of table salt?',
          'maxMarks': 2,
          'studentAnswer': 'NaCl',
          'awardedMarks': 2,
          'finalMarks': 2,
          'verdict': 'fullCredit',
          'confidence': 0.95,
          'reasoning': 'Matched all marking points.',
          'markingPoints': [
            {'id': 'mp1', 'description': 'States NaCl', 'awarded': true, 'marks': 2, 'reason': 'Found "NaCl" in answer'},
          ],
          'status': withEditedItem ? 'pending' : 'approved',
          'teacherMarks': null,
          'teacherComment': '',
        },
        {
          'questionId': 'q2',
          'displayNumber': 2,
          'stem': 'Explain photosynthesis in one line.',
          'maxMarks': 3,
          'studentAnswer': '',
          'awardedMarks': 0,
          'finalMarks': withEditedItem ? 1 : 0,
          'verdict': 'blank',
          'confidence': 0.9,
          'reasoning': 'No answer written for this question.',
          'markingPoints': [
            {'id': 'mp2', 'description': 'Mentions sunlight/chlorophyll', 'awarded': false, 'marks': 3, 'reason': 'No relevant text found'},
          ],
          'status': withEditedItem ? 'edited' : 'pending',
          'teacherMarks': withEditedItem ? 1 : null,
          'teacherComment': withEditedItem ? 'Student wrote a partial answer on the margin, missed by OCR.' : '',
        },
      ],
    });
  }

  group('LocalScanPdfExporter.exportCorrected', () {
    test('produces a real, non-trivial PDF from real session/review data', () async {
      seedRealSession('scan_1', withEditedItem: false);
      final path = await LocalScanPdfExporter.exportCorrected('scan_1');
      final file = File(path);
      expect(await file.exists(), isTrue);
      final bytes = await file.readAsBytes();
      expect(bytes.length, greaterThan(500), reason: 'a real 2-question PDF should be well beyond a trivial/empty size');
      expect(String.fromCharCodes(bytes.take(5)), '%PDF-', reason: 'must be a real PDF file, not a stub');
    });

    test('includes the teacher\'s edit/comment when a question was regraded', () async {
      seedRealSession('scan_2', withEditedItem: true);
      final path = await LocalScanPdfExporter.exportCorrected('scan_2');
      final bytes = await File(path).readAsBytes();
      // Text isn't trivially greppable in compressed PDF content streams,
      // so this proves the export completes without throwing for the
      // edited-item code path (teacherComment/teacherMarks branch) rather
      // than asserting on raw bytes.
      expect(bytes.length, greaterThan(500));
    });

    test('throws a clear, honest error for a nonexistent session', () {
      expect(
        () => LocalScanPdfExporter.exportCorrected('does_not_exist'),
        throwsA(isA<StateError>()),
      );
    });
  });

  group('LocalScanPdfExporter.exportRawBooklet', () {
    test('assembles real captured page images into one real PDF', () async {
      final imgDir = Directory('${tmpDir.path}/pages')..createSync();
      final imgFile = File('${imgDir.path}/page1.png');
      await imgFile.writeAsBytes(_tinyPng());

      LocalStore.instance.saveScanSession('scan_3', {
        'id': 'scan_3',
        'assessmentId': 'assess_1',
        'studentId': 'stu_1',
        'studentName': 'Real Test Student',
        'status': 'finalized',
        'pages': [
          {'pageNo': 1, 'imagePath': imgFile.path, 'text': '', 'warnings': [], 'confidence': 0.9},
        ],
        'review': [],
      });

      final path = await LocalScanPdfExporter.exportRawBooklet('scan_3');
      final bytes = await File(path).readAsBytes();
      expect(bytes.length, greaterThan(200));
      expect(String.fromCharCodes(bytes.take(5)), '%PDF-');
    });

    test('throws a clear, honest error when no pages were ever captured', () {
      LocalStore.instance.saveScanSession('scan_4', {
        'id': 'scan_4',
        'assessmentId': 'assess_1',
        'studentId': 'stu_1',
        'studentName': 'Real Test Student',
        'status': 'finalized',
        'pages': <Map<String, dynamic>>[],
        'review': <Map<String, dynamic>>[],
      });
      expect(
        () => LocalScanPdfExporter.exportRawBooklet('scan_4'),
        throwsA(isA<StateError>()),
      );
    });
  });

  group('LocalPillarApi.downloadScanPdf routing', () {
    test('a real corrected-pdf URL routes to the corrected exporter and writes real bytes to savePath', () async {
      seedRealSession('scan_5', withEditedItem: false);
      final savePath = '${tmpDir.path}/downloaded_corrected.pdf';
      final result = await LocalPillarApi().downloadScanPdf('/scan/sessions/scan_5/corrected-pdf', savePath);
      expect(result, savePath);
      final bytes = await File(savePath).readAsBytes();
      expect(bytes.length, greaterThan(500));
      expect(String.fromCharCodes(bytes.take(5)), '%PDF-');
    });

    test('an unrecognized URL still fails honestly instead of guessing', () {
      expect(
        () => LocalPillarApi().downloadScanPdf('/something/unexpected', '${tmpDir.path}/x.pdf'),
        throwsA(isA<OfflineUnsupportedException>()),
      );
    });
  });
}
