import 'corpus_repository.dart';

/// The words Settings uses to say what the phone is serving.
///
/// skippedRows and downloadRejection used to reach nothing but a debugPrint
/// line in logcat, which no teacher reads. A download that dropped its 1,834
/// unnormalised SQP rows would have shown "Corpus updated" beside a
/// plausible count, which is the quietly wrong answer this app treats as
/// worse than an error. Kept as plain functions of the repository's state so
/// each wording is pinned by a unit test rather than a widget test.

/// The subtitle of the Settings "Download Data" tile.
String corpusSourceLine({
  required bool loaded,
  required bool fromDownload,
  required int count,
  required int skipped,
  required DownloadRejection? rejection,
}) {
  final source = fromDownload ? 'downloaded' : 'bundled with app';
  final counted = loaded ? '$count questions' : '? questions';
  final unreadable = skipped > 0 ? ', $skipped rows unreadable' : '';
  final line = 'Corpus source: $source ($counted$unreadable)';
  return rejection == null ? line : '$line -- last download rejected: ${rejection.reason}';
}

/// The snackbar shown after a download finishes and the corpus reloads.
String corpusReloadMessage({
  required bool fromDownload,
  required int count,
  required int skipped,
  required DownloadRejection? rejection,
}) {
  if (!fromDownload) {
    final why = rejection?.reason ?? 'the downloaded file was not found or failed its checksum';
    return 'Download not used: $why. Still serving the bundled $count questions.';
  }
  final unreadable = skipped > 0 ? ' ($skipped rows unreadable)' : '';
  return 'Corpus updated -- $count questions now available$unreadable.';
}

/// [corpusSourceLine] for the live repository.
String corpusSourceLineFor(CorpusRepository repo) => corpusSourceLine(
      loaded: repo.isLoaded,
      fromDownload: repo.loadedFromDownload,
      count: repo.isLoaded ? repo.all.length : 0,
      skipped: repo.skippedRows,
      rejection: repo.downloadRejection,
    );

/// [corpusReloadMessage] for the live repository, after reload().
String corpusReloadMessageFor(CorpusRepository repo) => corpusReloadMessage(
      fromDownload: repo.loadedFromDownload,
      count: repo.all.length,
      skipped: repo.skippedRows,
      rejection: repo.downloadRejection,
    );
