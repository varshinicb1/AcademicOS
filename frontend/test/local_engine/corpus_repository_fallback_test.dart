// Proves the real regression found and fixed: CorpusRepository.reload()
// used to only guard the download EXISTENCE/checksum check, not the
// subsequent read+parse -- so a downloaded file that passed its checksum
// but contained corrupted/malformed JSON (or an unexpected schema
// Question.fromJson rejects) threw uncaught, straight out of main() before
// runApp() -- the app's native white splash screen never got replaced.
// This test reproduces that exact scenario and proves the fix: it must
// fall back to the bundled asset cleanly, never throw.
import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:academicos/core/local_engine/corpus_downloader.dart';
import 'package:academicos/core/local_engine/corpus_repository.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tmpDir;

  setUp(() {
    tmpDir = Directory.systemTemp.createTempSync('corpus_repo_test_');
    CorpusDownloader.debugDirectoryOverride = tmpDir;
  });

  tearDown(() {
    CorpusDownloader.debugDirectoryOverride = null;
    tmpDir.deleteSync(recursive: true);
  });

  test('a "downloaded" file with corrupted content that still passes its own '
      'checksum falls back to the bundled asset instead of throwing', () async {
    // Simulates the real regression: a file whose bytes genuinely match
    // their own recorded checksum (so currentDownloadedFile() accepts it)
    // but whose CONTENT is not valid corpus JSON -- disk corruption after
    // a good write, or any future bug in the download-time validation.
    final corruptedBytes = utf8.encode('{"this is not": "a real corpus shape"');
    final hash = sha256.convert(corruptedBytes).toString();
    final targetFile = File('${tmpDir.path}/corpus_downloaded.json');
    await targetFile.writeAsBytes(corruptedBytes);
    await File('${targetFile.path}.sha256').writeAsString(hash);

    // Must not throw -- this exact call, unguarded, is what left the app
    // on a white screen forever before the fix.
    await CorpusRepository.instance.reload();

    expect(CorpusRepository.instance.isLoaded, isTrue);
    expect(CorpusRepository.instance.loadedFromDownload, isFalse,
        reason: 'a corrupted downloaded file must not be trusted -- bundled asset is the real fallback');
    expect(CorpusRepository.instance.all, isNotEmpty);
  });

  test('a "downloaded" file containing valid JSON but the wrong shape '
      '(no questions array) also falls back cleanly', () async {
    final wrongShapeBytes = utf8.encode(jsonEncode({'not_questions': []}));
    final hash = sha256.convert(wrongShapeBytes).toString();
    final targetFile = File('${tmpDir.path}/corpus_downloaded.json');
    await targetFile.writeAsBytes(wrongShapeBytes);
    await File('${targetFile.path}.sha256').writeAsString(hash);

    await CorpusRepository.instance.reload();

    expect(CorpusRepository.instance.isLoaded, isTrue);
    expect(CorpusRepository.instance.loadedFromDownload, isFalse);
    expect(CorpusRepository.instance.all, isNotEmpty);
  });

  test('no downloaded file at all loads the bundled asset normally (baseline)', () async {
    await CorpusRepository.instance.reload();

    expect(CorpusRepository.instance.isLoaded, isTrue);
    expect(CorpusRepository.instance.loadedFromDownload, isFalse);
    expect(CorpusRepository.instance.all.length, greaterThan(3000));
  });
}
