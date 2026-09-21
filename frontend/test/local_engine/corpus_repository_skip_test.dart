// One row Question.fromJson rejects used to throw out of the whole corpus
// parse. The bundled-asset parse was not guarded and runs before runApp(),
// so a single malformed row left the app on its native splash screen for
// good. The merge design measured how close that is: all 1,834 SQP rows
// lack competencyIds and bloomLevel, 259 CBE rows have parts with no
// textLatex (docs/superpowers/specs/2026-09-21-question-bank-merge-design.md
// section 1). These tests prove a bad row now costs only that row, and --
// because skipping would otherwise hide a bad merge -- that the corpus the
// app actually bundles decodes every one of its rows.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:academicos/core/local_engine/corpus_downloader.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _good(String id) => {
      'id': id, 'questionBankId': 'b', 'subject': 'Science', 'grade': 7,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'Why is the sky blue?', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': {
        'totalMarks': 1, 'markingPoints': <dynamic>[], 'rubricLevels': <dynamic>[],
        'commonErrors': <String>[], 'alternativeAnswers': <String>[],
        'modelAnswer': 'Scattering', 'modelAnswerLatex': '',
      },
      'estimatedTimeMinutes': 2, 'marks': 1, 'language': 'en',
      'source': 'cbse_question_bank', 'qualityScore': 0.8, 'tags': <String>[],
      'createdAt': '2026-09-19T00:00:00.000Z', 'updatedAt': '2026-09-19T00:00:00.000Z',
    };

/// The rows of the corpus the APK actually ships, read through the same
/// asset bundle reload() uses.
Future<List<Map<String, dynamic>>> _bundledRows() async {
  final raw = await rootBundle.loadString('assets/corpus/questions.json');
  final rows = (jsonDecode(raw) as Map<String, dynamic>)['questions'] as List;
  return [for (final r in rows) Map<String, dynamic>.from(r as Map)];
}

/// Writes [body] where CorpusDownloader looks for an accepted download,
/// with a matching checksum so currentDownloadedFile() trusts it.
Future<void> _writeDownload(Directory dir, String body) async {
  final bytes = utf8.encode(body);
  final file = File('${dir.path}/corpus_downloaded.json');
  await file.writeAsBytes(bytes);
  await File('${file.path}.sha256').writeAsString(sha256.convert(bytes).toString());
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('a row Question.fromJson rejects is skipped and counted', () {
    final bad = _good('bad')..remove('competencyIds');
    final raw = jsonEncode({'questions': [_good('a'), bad, _good('b')]});
    final result = CorpusRepository.parseQuestionsForTest(raw);
    expect(result.questions.map((q) => q.id), ['a', 'b']);
    expect(result.skipped, 1);
  });

  test('a corpus with no readable row yields zero questions, not an exception', () {
    final bad = _good('bad')..remove('stemLatex');
    final result = CorpusRepository.parseQuestionsForTest(jsonEncode({'questions': [bad]}));
    expect(result.questions, isEmpty);
    expect(result.skipped, 1);
  });

  test('the bundled corpus decodes every row -- none is silently skipped', () async {
    // Skipping keeps the app alive, but it would also hide a merge that
    // wrote rows the phone cannot read. This is where that gets loud.
    final rows = await _bundledRows();
    final result = CorpusRepository.parseQuestionsForTest(jsonEncode({'questions': rows}));
    expect(result.skipped, 0);
    expect(result.questions.length, rows.length);
    expect(rows.length, greaterThan(3000));
  });

  test('a real row reshaped like an SQP row costs that row, not the corpus', () async {
    final rows = (await _bundledRows()).take(40).toList();
    // The measured SQP defect: no competencyIds and no bloomLevel.
    final victim = rows[17]
      ..remove('competencyIds')
      ..remove('bloomLevel');
    final result = CorpusRepository.parseQuestionsForTest(jsonEncode({'questions': rows}));
    expect(result.skipped, 1);
    expect(result.questions.length, 39);
    expect(result.questions.map((q) => q.id), isNot(contains(victim['id'])));
    expect(result.questions.map((q) => q.id),
        [for (final r in rows) if (!identical(r, victim)) r['id']]);
  });

  group('reload()', () {
    late Directory tmpDir;

    setUp(() {
      tmpDir = Directory.systemTemp.createTempSync('corpus_skip_test_');
      CorpusDownloader.debugDirectoryOverride = tmpDir;
    });

    tearDown(() {
      CorpusDownloader.debugDirectoryOverride = null;
      tmpDir.deleteSync(recursive: true);
    });

    test('a download with one bad row is still used, and the row is counted', () async {
      final rows = (await _bundledRows()).take(25).toList();
      rows[3].remove('competencyIds');
      await _writeDownload(tmpDir, jsonEncode({'questions': rows}));

      await CorpusRepository.instance.reload();

      expect(CorpusRepository.instance.loadedFromDownload, isTrue);
      expect(CorpusRepository.instance.all.length, 24);
      expect(CorpusRepository.instance.skippedRows, 1);
    });

    test('a download with no readable row falls back to the bundled asset', () async {
      final bad = _good('bad')..remove('competencyIds');
      await _writeDownload(tmpDir, jsonEncode({'questions': [bad]}));

      await CorpusRepository.instance.reload();

      expect(CorpusRepository.instance.loadedFromDownload, isFalse);
      expect(CorpusRepository.instance.all.length, greaterThan(3000));
      expect(CorpusRepository.instance.skippedRows, 0,
          reason: "the rejected download's count must not leak onto the bundled corpus");
    });

    group('with a substituted bundled asset', () {
      // The splash-screen path itself: no download, so reload() parses the
      // bundled asset -- the branch that used to run unguarded before
      // runApp(). The asset channel is replaced so the APK's asset can be
      // made bad without touching the real file.
      const assetKey = 'assets/corpus/questions.json';
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;

      void serveAsset(String body) {
        rootBundle.evict(assetKey);
        messenger.setMockMessageHandler('flutter/assets', (message) async {
          final key = utf8.decode(message!.buffer.asUint8List());
          if (key != assetKey) return null;
          return ByteData.sublistView(utf8.encode(body));
        });
      }

      tearDown(() {
        messenger.setMockMessageHandler('flutter/assets', null);
        rootBundle.evict(assetKey);
      });

      test('one bad bundled row costs that row, and reload() does not throw', () async {
        final rows = (await _bundledRows()).take(10).toList();
        final bad = Map<String, dynamic>.from(rows.first)
          ..['id'] = 'sqp-shaped'
          ..remove('competencyIds')
          ..remove('bloomLevel');
        serveAsset(jsonEncode({'questions': [...rows, bad]}));

        await CorpusRepository.instance.reload();

        expect(CorpusRepository.instance.loadedFromDownload, isFalse);
        expect(CorpusRepository.instance.all.map((q) => q.id),
            [for (final r in rows) r['id']]);
        expect(CorpusRepository.instance.skippedRows, 1);
      });

      test('an unreadable bundled asset loads an empty corpus instead of throwing', () async {
        serveAsset('{"questions": [');

        await CorpusRepository.instance.reload();

        expect(CorpusRepository.instance.isLoaded, isTrue);
        expect(CorpusRepository.instance.all, isEmpty);
        expect(CorpusRepository.instance.skippedRows, 0);
      });
    });
  });
}
