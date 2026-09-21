import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;

import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import 'corpus_downloader.dart';

/// Loads the real CBSE/NCERT question corpus into memory once, and answers
/// the same catalog/chapter/search queries the deployed backend does. No
/// network required at load time -- this is the on-device replacement for
/// /catalog, /catalog/{subject}/{grade}/chapters and /questions/search.
///
/// Prefers a real downloaded corpus (corpus_downloader.dart -- checksum-
/// verified, from a public GitHub Release, freshenable after install)
/// over the bundled asset (assets/corpus/questions.json, frozen at build
/// time) when one exists and still passes re-verification. Falls back to
/// the bundled asset otherwise -- the app must work immediately after
/// install with zero network, downloading only ever adds/updates data, it
/// is never a requirement.
class CorpusRepository {
  CorpusRepository._();
  static final CorpusRepository instance = CorpusRepository._();

  List<Question>? _questions;
  bool _fromDownload = false;
  int _skippedRows = 0;
  bool get isLoaded => _questions != null;
  bool get loadedFromDownload => _fromDownload;

  /// Rows the loaded corpus could not decode. Zero for a healthy corpus.
  int get skippedRows => _skippedRows;

  Future<void> ensureLoaded() async {
    if (_questions != null) return;
    await reload();
  }

  /// Re-reads from disk/assets even if already loaded -- called after a
  /// fresh download completes so the newly-fetched corpus takes effect
  /// without requiring an app restart.
  Future<void> reload() async {
    // Any failure anywhere in the downloaded-file path -- disk I/O, a
    // path_provider platform hiccup, a corrupted/stale file that fails to
    // parse, an unexpected schema Question.fromJson rejects -- must fall
    // back to the always-present bundled asset, never crash corpus
    // loading. This whole block runs before runApp() (via
    // service_locator.dart's initDependencies()), so anything that
    // escapes uncaught here leaves the app on its native white splash
    // forever -- a real regression this fixed (an earlier version only
    // wrapped the existence/checksum check, not the actual read+parse).
    final downloaded = await _tryLoadDownloaded();
    if (downloaded != null) {
      _questions = downloaded.questions;
      _skippedRows = downloaded.skipped;
      _fromDownload = true;
      return;
    }
    _fromDownload = false;
    // The bundled asset gets the same guarantee. It used to be parsed
    // unguarded, so one row Question.fromJson rejected kept the app on its
    // splash screen -- latent while every bundled row decoded, not once
    // the SQP/CBE merge adds rows (all 1,834 SQP rows lacked competencyIds
    // and bloomLevel before normalisation).
    try {
      final parsed = _parse(await rootBundle.loadString('assets/corpus/questions.json'));
      _questions = parsed.questions;
      _skippedRows = parsed.skipped;
    } catch (err) {
      // Unreadable JSON or a missing asset. Start with an empty corpus rather
      // than hang on the splash screen: the catalog comes back empty and
      // Settings reports 0 questions, which is at least visible.
      debugPrint('corpus: bundled asset could not be read: $err');
      _questions = const [];
      _skippedRows = 0;
    }
  }

  /// The downloaded corpus, or null when there is none or it cannot be
  /// used. A download with no readable row counts as unusable, so the
  /// bundled asset is served instead of an empty corpus.
  Future<ParsedCorpus?> _tryLoadDownloaded() async {
    try {
      final downloaded = await CorpusDownloader.currentDownloadedFile();
      if (downloaded == null) return null;
      final parsed = _parse(await downloaded.readAsString());
      if (parsed.questions.isEmpty) return null;
      return parsed;
    } catch (_) {
      return null;
    }
  }

  /// Decode every row that can be decoded, and count the rest.
  ///
  /// One row Question.fromJson rejected used to throw out of the whole parse.
  /// For the bundled asset that ran before runApp(), so a single malformed
  /// question kept the app on its splash screen for good. A bad row now costs
  /// that one question and is counted in [skippedRows]. Logged once per parse
  /// rather than once per row: the unnormalised SQP bank would have been
  /// 1,834 rejected rows, each a line of startup log.
  static ParsedCorpus _parse(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final rows = (data['questions'] as List?) ?? const [];
    final out = <Question>[];
    var skipped = 0;
    Object? firstError;
    Object? firstId;
    for (final e in rows) {
      try {
        out.add(Question.fromJson(Map<String, dynamic>.from(e as Map)));
      } catch (err) {
        if (skipped == 0) {
          firstError = err;
          firstId = e is Map ? e['id'] : null;
        }
        skipped++;
      }
    }
    if (skipped > 0) {
      debugPrint('corpus: skipped $skipped of ${rows.length} rows '
          'Question.fromJson rejected; first ($firstId): $firstError');
    }
    return ParsedCorpus(out, skipped);
  }

  @visibleForTesting
  static ParsedCorpus parseQuestionsForTest(String raw) => _parse(raw);

  List<Question> get all {
    final q = _questions;
    if (q == null) {
      throw StateError('CorpusRepository not loaded -- call ensureLoaded() first');
    }
    return q;
  }

  /// Mirrors GET /api/v1/catalog
  List<CatalogEntryData> catalog() {
    final groups = <String, List<Question>>{};
    for (final q in all) {
      final key = '${q.subject}|${q.grade}';
      groups.putIfAbsent(key, () => []).add(q);
    }
    final entries = groups.entries.map((e) {
      final qs = e.value;
      final chapters = qs.expand((q) => q.chapterIds).toSet();
      final marks = qs.map((q) => q.marks).toSet().toList()..sort();
      return CatalogEntryData(
        subject: qs.first.subject,
        grade: qs.first.grade,
        questionCount: qs.length,
        chapters: chapters.length,
        marksAvailable: marks,
      );
    }).toList()
      ..sort((a, b) => b.questionCount.compareTo(a.questionCount));
    return entries;
  }

  /// Mirrors GET /api/v1/catalog/{subject}/{grade}/chapters
  List<ChapterEntryData> chapters(String subject, int grade) {
    final qs = all.where((q) => q.subject == subject && q.grade == grade);
    final groups = <String, List<Question>>{};
    for (final q in qs) {
      for (final cid in q.chapterIds) {
        groups.putIfAbsent(cid, () => []).add(q);
      }
    }
    return groups.entries.map((e) {
      final marks = e.value.map((q) => q.marks).toSet().toList()..sort();
      final name = e.value.first.tags.isNotEmpty ? e.value.first.tags.first : e.key;
      return ChapterEntryData(
        chapterId: e.key,
        chapterName: name,
        questionCount: e.value.length,
        marksAvailable: marks,
      );
    }).toList()
      ..sort((a, b) => b.questionCount.compareTo(a.questionCount));
  }

  /// Mirrors POST /api/v1/questions/search
  List<Question> search(QuestionSearchParams params) {
    var results = all.where((q) => q.subject == params.subject && q.grade == params.grade);
    if (params.chapterIds != null && params.chapterIds!.isNotEmpty) {
      final wanted = params.chapterIds!.toSet();
      results = results.where((q) => q.chapterIds.any(wanted.contains));
    }
    if (params.bloomLevels != null && params.bloomLevels!.isNotEmpty) {
      final wanted = params.bloomLevels!.toSet();
      results = results.where((q) => wanted.contains(q.bloomLevel));
    }
    if (params.difficulties != null && params.difficulties!.isNotEmpty) {
      final wanted = params.difficulties!.toSet();
      results = results.where((q) => wanted.contains(q.difficulty));
    }
    if (params.types != null && params.types!.isNotEmpty) {
      final wanted = params.types!.toSet();
      results = results.where((q) => wanted.contains(q.type));
    }
    if (params.minMarks != null) {
      results = results.where((q) => q.marks >= params.minMarks!);
    }
    if (params.maxMarks != null) {
      results = results.where((q) => q.marks <= params.maxMarks!);
    }
    if (params.minQualityScore != null) {
      results = results.where((q) => q.qualityScore >= params.minQualityScore!);
    }
    if (params.keyword != null && params.keyword!.trim().isNotEmpty) {
      final kw = params.keyword!.toLowerCase();
      results = results.where((q) => q.stem.toLowerCase().contains(kw));
    }
    var list = results.toList();
    if (params.offset != null) {
      list = list.skip(params.offset!).toList();
    }
    if (params.limit != null) {
      list = list.take(params.limit!).toList();
    }
    return list;
  }
}

/// What a corpus parse produced: the rows that decoded, and how many did not.
class ParsedCorpus {
  const ParsedCorpus(this.questions, this.skipped);
  final List<Question> questions;
  final int skipped;
}

class CatalogEntryData {
  final String subject;
  final int grade;
  final int questionCount;
  final int chapters;
  final List<int> marksAvailable;
  CatalogEntryData({
    required this.subject,
    required this.grade,
    required this.questionCount,
    required this.chapters,
    required this.marksAvailable,
  });
}

class ChapterEntryData {
  final String chapterId;
  final String chapterName;
  final int questionCount;
  final List<int> marksAvailable;
  ChapterEntryData({
    required this.chapterId,
    required this.chapterName,
    required this.questionCount,
    required this.marksAvailable,
  });
}
