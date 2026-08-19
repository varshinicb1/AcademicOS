import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;

import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';

/// Loads the real, bundled CBSE/NCERT question corpus (assets/corpus/questions.json
/// -- exported straight from the same production pipeline the live API reads
/// from) into memory once, and answers the same catalog/chapter/search
/// queries the deployed backend does. No network, no server -- this is the
/// on-device replacement for /catalog, /catalog/{subject}/{grade}/chapters
/// and /questions/search.
class CorpusRepository {
  CorpusRepository._();
  static final CorpusRepository instance = CorpusRepository._();

  List<Question>? _questions;
  bool get isLoaded => _questions != null;

  Future<void> ensureLoaded() async {
    if (_questions != null) return;
    final raw = await rootBundle.loadString('assets/corpus/questions.json');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final list = (data['questions'] as List)
        .map((e) => Question.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
    _questions = list;
  }

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
