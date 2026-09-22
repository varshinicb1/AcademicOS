// Settings is the only place a teacher can see what the phone is serving.
// Skipped rows and a rejected download used to reach nothing but one
// debugPrint line in logcat, so a download that lost 1,834 SQP rows would
// have shown "Corpus updated" and a healthy-looking count. These pin the
// wording Settings shows for each state.
import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/core/local_engine/corpus_status.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('corpusSourceLine', () {
    test('a clean bundled corpus shows source and count only', () {
      expect(
        corpusSourceLine(loaded: true, fromDownload: false, count: 3286, skipped: 0, rejection: null),
        'Corpus source: bundled with app (3286 questions)',
      );
    });

    test('skipped rows are named next to the count', () {
      expect(
        corpusSourceLine(loaded: true, fromDownload: true, count: 5100, skipped: 20, rejection: null),
        'Corpus source: downloaded (5100 questions, 20 rows unreadable)',
      );
    });

    test('a rejected download is reported, not hidden behind "bundled"', () {
      expect(
        corpusSourceLine(
          loaded: true,
          fromDownload: false,
          count: 3286,
          skipped: 0,
          rejection: const DownloadRejection(skipped: 1834, total: 5120),
        ),
        'Corpus source: bundled with app (3286 questions) -- '
        'last download rejected: 1834 of 5120 rows unreadable',
      );
    });

    test('before the corpus loads the count is unknown', () {
      expect(
        corpusSourceLine(loaded: false, fromDownload: false, count: 0, skipped: 0, rejection: null),
        'Corpus source: bundled with app (? questions)',
      );
    });
  });

  group('corpusReloadMessage', () {
    test('a used download reports its count', () {
      expect(
        corpusReloadMessage(fromDownload: true, count: 5100, skipped: 0, rejection: null),
        'Corpus updated -- 5100 questions now available.',
      );
    });

    test('a used download with skipped rows says how many', () {
      expect(
        corpusReloadMessage(fromDownload: true, count: 5100, skipped: 20, rejection: null),
        'Corpus updated -- 5100 questions now available (20 rows unreadable).',
      );
    });

    test('a rejected download never says "Corpus updated"', () {
      final msg = corpusReloadMessage(
        fromDownload: false,
        count: 3286,
        skipped: 0,
        rejection: const DownloadRejection(skipped: 1834, total: 5120),
      );
      expect(msg, isNot(contains('Corpus updated')));
      expect(msg,
          'Download not used: 1834 of 5120 rows unreadable. Still serving the bundled 3286 questions.');
    });

    test('an unreadable download file is reported as not used', () {
      expect(
        corpusReloadMessage(
            fromDownload: false, count: 3286, skipped: 0, rejection: const DownloadRejection.unreadable()),
        'Download not used: the file could not be read. Still serving the bundled 3286 questions.',
      );
    });
  });
}
