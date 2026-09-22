/// Client for the guided paper builder (Task 902): a teacher's paper
/// templates and CBSE presets, the availability check, generating a paper
/// from a template, and swapping or picking one question on the saved paper.
///
/// The server side is Tasks 901/903/904 (paper_template_routes.py). Plain
/// classes, like pillar_api.dart, not freezed: these shapes are read by one
/// screen family, and a build_runner cycle per field would slow exactly the
/// iteration this UI needs. Section and template JSON is kept whole
/// ([TemplateSectionView.raw], [PaperTemplateView.raw]) and only the fields
/// the builder edits are overridden on the way back, so a field this client
/// does not model (difficulty mix, competency share, header) survives an
/// edit instead of being silently reset to its default.
library;

import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../../domain/repositories/requests.dart' show GeneratedPaper;
import 'pillar_api.dart' show ChapterEntry;

/// What the server said, in words a teacher can act on.
///
/// FastAPI answers three shapes: `{"detail": "text"}`, `{"detail":
/// {"message": ...}}` (the 400/409 of generate-from-template, which carry the
/// availability report too), and a list of pydantic errors (`{"detail":
/// [{"msg": "Value error, sections add up to 22 marks ..."}]}`). A bare
/// `DioException.toString()` shows none of them -- it prints "bad response"
/// and a status code, which is a dead end for a teacher.
String apiErrorMessage(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    final detail = data is Map ? data['detail'] : null;
    if (detail is String && detail.trim().isNotEmpty) return detail;
    if (detail is Map && detail['message'] is String) return detail['message'] as String;
    if (detail is List && detail.isNotEmpty) {
      return detail
          .map((e) => e is Map ? '${e['msg'] ?? e}' : '$e')
          .map((m) => m.replaceFirst(RegExp(r'^Value error, '), ''))
          .join('; ');
    }
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'The server took too long to answer. Check your connection and try again.';
      case DioExceptionType.connectionError:
        return 'Could not reach the server. Check your connection and try again.';
      default:
        final code = error.response?.statusCode;
        return code == null ? 'The request failed. Try again.' : 'The server answered $code. Try again.';
    }
  }
  return '$error';
}

List<Map<String, dynamic>> _maps(Object? v) =>
    ((v ?? const []) as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();

/// One section of a template as the builder edits it.
class TemplateSectionView {
  final Map<String, dynamic> raw;
  final String id;
  final String title;
  final int questionCount;
  final int marksEach;
  final int? attemptCount;
  final int choiceCount;
  final List<String> questionTypes;

  TemplateSectionView({
    this.raw = const {},
    this.id = '',
    required this.title,
    required this.questionCount,
    required this.marksEach,
    this.attemptCount,
    this.choiceCount = 0,
    this.questionTypes = const [],
  });

  factory TemplateSectionView.fromJson(Map<String, dynamic> j) => TemplateSectionView(
        raw: j,
        id: j['id'] as String? ?? '',
        title: j['title'] as String? ?? '',
        questionCount: j['questionCount'] as int? ?? 0,
        marksEach: j['marksEach'] as int? ?? 0,
        attemptCount: j['attemptCount'] as int?,
        choiceCount: j['choiceCount'] as int? ?? 0,
        questionTypes: List<String>.from(j['questionTypes'] ?? const []),
      );

  /// The marks this section adds to the total: only attempted questions
  /// count (CBSE "attempt any N"); an OR choice adds nothing. Same rule as
  /// the server's TemplateSection.marks, so the running total the editor
  /// shows is the one the save is checked against.
  int get marks => (attemptCount ?? questionCount) * marksEach;

  TemplateSectionView copyWith({
    String? title,
    int? questionCount,
    int? marksEach,
    int? choiceCount,
    List<String>? questionTypes,
    bool dropCompetencyRule = false,
  }) {
    final r = Map<String, dynamic>.from(raw);
    if (dropCompetencyRule) r['competencyShare'] = null;
    return TemplateSectionView(
      raw: r,
      id: id,
      title: title ?? this.title,
      questionCount: questionCount ?? this.questionCount,
      marksEach: marksEach ?? this.marksEach,
      attemptCount: attemptCount,
      choiceCount: choiceCount ?? this.choiceCount,
      questionTypes: questionTypes ?? this.questionTypes,
    );
  }

  Map<String, dynamic> toJson() => {
        ...raw,
        if (id.isNotEmpty) 'id': id,
        'title': title,
        'questionCount': questionCount,
        'marksEach': marksEach,
        'attemptCount': attemptCount,
        // Never more ORs than questions: the server refuses that, and a
        // count lowered in the editor must not strand a stale choice count.
        'choiceCount': choiceCount > questionCount ? questionCount : choiceCount,
        'questionTypes': questionTypes,
      };
}

class PaperTemplateView {
  final Map<String, dynamic> raw;
  final String id;
  final String name;
  final int grade;
  final String subject;
  final String examType;
  final int totalMarks;
  final int durationMinutes;
  final List<TemplateSectionView> sections;
  final List<String> scopeChapterIds;
  final bool isPreset;
  final bool shared;
  final String ownerId;
  final String patternStatus;
  final String source;

  PaperTemplateView({
    this.raw = const {},
    this.id = '',
    required this.name,
    required this.grade,
    required this.subject,
    this.examType = 'custom',
    required this.totalMarks,
    required this.durationMinutes,
    required this.sections,
    this.scopeChapterIds = const [],
    this.isPreset = false,
    this.shared = false,
    this.ownerId = '',
    this.patternStatus = 'teacher',
    this.source = '',
  });

  factory PaperTemplateView.fromJson(Map<String, dynamic> j) => PaperTemplateView(
        raw: j,
        id: j['id'] as String? ?? '',
        name: j['name'] as String? ?? '',
        grade: j['grade'] as int? ?? 0,
        subject: j['subject'] as String? ?? '',
        examType: j['examType'] as String? ?? 'custom',
        totalMarks: j['totalMarks'] as int? ?? 0,
        durationMinutes: j['durationMinutes'] as int? ?? 0,
        sections: _maps(j['sections']).map(TemplateSectionView.fromJson).toList(),
        scopeChapterIds: List<String>.from((j['scope'] as Map?)?['chapterIds'] ?? const []),
        isPreset: j['isPreset'] as bool? ?? false,
        shared: j['shared'] as bool? ?? false,
        ownerId: j['ownerId'] as String? ?? '',
        patternStatus: j['patternStatus'] as String? ?? 'teacher',
        source: j['source'] as String? ?? '',
      );

  int get sectionMarks => sections.fold(0, (s, x) => s + x.marks);
  int get questionCount => sections.fold(0, (s, x) => s + x.questionCount);

  /// "A 20×1 · B 6×2 · C 7×3" -- the pattern at a glance on a card.
  String get sectionSummary => [
        for (final (i, s) in sections.indexed)
          '${String.fromCharCode(65 + i)} ${s.questionCount}×${s.marksEach}'
              '${s.choiceCount > 0 ? ' (${s.choiceCount} OR)' : ''}',
      ].join(' · ');

  PaperTemplateView copyWith({
    String? name,
    int? totalMarks,
    int? durationMinutes,
    List<TemplateSectionView>? sections,
  }) =>
      PaperTemplateView(
        raw: raw,
        id: id,
        name: name ?? this.name,
        grade: grade,
        subject: subject,
        examType: examType,
        totalMarks: totalMarks ?? this.totalMarks,
        durationMinutes: durationMinutes ?? this.durationMinutes,
        sections: sections ?? this.sections,
        scopeChapterIds: scopeChapterIds,
        isPreset: isPreset,
        shared: shared,
        ownerId: ownerId,
        patternStatus: patternStatus,
        source: source,
      );

  /// The body POST/PUT /teacher-templates take (PaperTemplateDraft). The
  /// instructions and header travel back unchanged: the server keeps a
  /// preset's generated instructions generated only while the text is
  /// untouched (see update_teacher_template).
  Map<String, dynamic> toDraftJson() => {
        'name': name,
        'grade': grade,
        'subject': subject,
        'examType': examType,
        'totalMarks': totalMarks,
        'durationMinutes': durationMinutes,
        'instructions': raw['instructions'] ?? '',
        if (raw['header'] != null) 'header': raw['header'],
        'sections': sections.map((s) => s.toJson()).toList(),
        'scope': raw['scope'] ?? {'chapterIds': scopeChapterIds},
      };
}

class TemplateLists {
  final List<PaperTemplateView> presets;
  final List<PaperTemplateView> mine;
  final List<PaperTemplateView> shared;

  TemplateLists({required this.presets, required this.mine, required this.shared});

  factory TemplateLists.fromJson(Map<String, dynamic> j) => TemplateLists(
        presets: _maps(j['presets']).map(PaperTemplateView.fromJson).toList(),
        mine: _maps(j['mine']).map(PaperTemplateView.fromJson).toList(),
        shared: _maps(j['shared']).map(PaperTemplateView.fromJson).toList(),
      );

  Iterable<PaperTemplateView> get all => [...mine, ...shared, ...presets];
}

/// One change that closes (part of) a section's gap, carrying the value to
/// apply -- the server names the setting so the builder can offer it as a
/// single tap (paper_templates.SectionFix).
class SectionFixView {
  final String kind;
  final String label;
  final int available;
  final int? marksEach;
  final int? questionCount;
  final int? choiceCount;
  final List<String>? questionTypes;

  SectionFixView.fromJson(Map<String, dynamic> j)
      : kind = j['kind'] as String? ?? '',
        label = j['label'] as String? ?? '',
        available = j['available'] as int? ?? 0,
        marksEach = j['marksEach'] as int?,
        questionCount = j['questionCount'] as int?,
        choiceCount = j['choiceCount'] as int?,
        questionTypes = j['questionTypes'] == null ? null : List<String>.from(j['questionTypes'] as List);

  /// Fixes that change only this paper's scope, not the template.
  bool get changesScope => kind == 'widen_scope' || kind == 'fill_from_outside_scope';
}

class SectionAvailabilityView {
  final String sectionId;
  final String title;
  final int marksEach;
  final int needed;
  final int available;
  final int shortfall;
  final int filled;
  final int borrowed;
  final int outsideScopeAvailable;
  final int withoutKey;
  final int choicesNeeded;
  final int choicesFilled;
  final String reason;
  final List<String> notes;
  final List<SectionFixView> fixes;

  SectionAvailabilityView.fromJson(Map<String, dynamic> j)
      : sectionId = j['sectionId'] as String? ?? '',
        title = j['title'] as String? ?? '',
        marksEach = j['marksEach'] as int? ?? 0,
        needed = j['needed'] as int? ?? 0,
        available = j['available'] as int? ?? 0,
        shortfall = j['shortfall'] as int? ?? 0,
        filled = j['filled'] as int? ?? 0,
        borrowed = j['borrowed'] as int? ?? 0,
        outsideScopeAvailable = j['outsideScopeAvailable'] as int? ?? 0,
        withoutKey = j['withoutKey'] as int? ?? 0,
        choicesNeeded = j['choicesNeeded'] as int? ?? 0,
        choicesFilled = j['choicesFilled'] as int? ?? 0,
        reason = j['reason'] as String? ?? '',
        notes = List<String>.from(j['notes'] ?? const []),
        fixes = _maps(j['fixes']).map(SectionFixView.fromJson).toList();

  bool get isShort => shortfall > 0;
}

class AvailabilityView {
  final bool complete;
  final int bankQuestions;
  final int keyedQuestions;
  final List<SectionAvailabilityView> sections;
  final List<String> scopeNotes;

  AvailabilityView.fromJson(Map<String, dynamic> j)
      : complete = j['complete'] as bool? ?? false,
        bankQuestions = j['bankQuestions'] as int? ?? 0,
        keyedQuestions = j['keyedQuestions'] as int? ?? 0,
        sections = _maps(j['sections']).map(SectionAvailabilityView.fromJson).toList(),
        scopeNotes = List<String>.from(j['scopeNotes'] ?? const []);

  List<SectionAvailabilityView> get short => sections.where((s) => s.isShort).toList();

  /// Nothing at all can be printed: generation refuses this (400), so the
  /// builder must not offer to try.
  bool get nothingFits => sections.every((s) => s.filled == 0);
}

/// The server's paper JSON, made readable by the shared [GeneratedPaper]
/// model. Two fields generate-from-template leaves null that the model
/// requires: `schoolName` (blank header -> the PDF falls back to the school's
/// branding name) and a set's `formattedContent*`. Filled with '' here rather
/// than loosening the shared model under every other screen.
GeneratedPaper parsePaper(Map<String, dynamic> j) {
  Map<String, dynamic> fix(Map<String, dynamic> p) {
    final m = Map<String, dynamic>.from(p);
    final meta = Map<String, dynamic>.from(m['metadata'] as Map);
    meta['schoolName'] ??= '';
    meta['generatedBy'] ??= 'AcademicOS';
    meta['version'] ??= '1.0';
    m['metadata'] = meta;
    m['formattedContent'] ??= '';
    m['formattedContentLatex'] ??= '';
    m['answerKey'] ??= <String, dynamic>{};
    m['sets'] = _maps(m['sets']).map(fix).toList();
    return m;
  }

  return GeneratedPaper.fromJson(fix(j));
}

class TemplatePaperResult {
  final GeneratedPaper paper;
  final String assessmentId;
  final bool complete;
  final List<SectionAvailabilityView> gaps;
  final List<String> notes;

  TemplatePaperResult.fromJson(Map<String, dynamic> j)
      : paper = parsePaper(Map<String, dynamic>.from(j['paper'] as Map)),
        assessmentId = j['assessmentId'] as String? ?? '',
        complete = j['complete'] as bool? ?? false,
        gaps = _maps(j['gaps']).map(SectionAvailabilityView.fromJson).toList(),
        notes = List<String>.from(j['notes'] ?? const []);
}

class PaperEditResult {
  final GeneratedPaper paper;
  final String slot;
  final String replacedQuestionId;
  final String questionId;
  final List<String> notes;

  PaperEditResult.fromJson(Map<String, dynamic> j)
      : paper = parsePaper(Map<String, dynamic>.from(j['paper'] as Map)),
        slot = j['slot'] as String? ?? '',
        replacedQuestionId = j['replacedQuestionId'] as String? ?? '',
        questionId = j['questionId'] as String? ?? '',
        notes = List<String>.from(j['notes'] ?? const []);
}

/// The paper after a question (or only its OR alternative) was taken off.
/// Numbers after it moved up, so every slot key the client held is stale.
class PaperRemoveResult {
  final GeneratedPaper paper;
  final String slot;
  final List<String> removedQuestionIds;

  PaperRemoveResult.fromJson(Map<String, dynamic> j)
      : paper = parsePaper(Map<String, dynamic>.from(j['paper'] as Map)),
        slot = j['slot'] as String? ?? '',
        removedQuestionIds = List<String>.from(j['removedQuestionIds'] ?? const []);
}

/// A bank question as the picker shows it.
class BankItem {
  final String id;
  final String stem;
  final int marks;
  final String type;
  final List<String> chapterIds;
  final bool hasAnswerKey;

  BankItem.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String? ?? '',
        stem = j['stem'] as String? ?? '',
        marks = j['marks'] as int? ?? 0,
        type = j['type'] as String? ?? '',
        chapterIds = List<String>.from(j['chapterIds'] ?? const []),
        hasAnswerKey = hasVerifiedKey(j);

  /// Rule Q1, the same content check the server applies
  /// (QuestionBank.has_answer_key): a model answer or a marking point with
  /// actual text -- never a provenance label alone. The server refuses an
  /// unkeyed pick (422) anyway; checking here means the picker never offers
  /// one in the first place.
  static bool hasVerifiedKey(Map<String, dynamic> j) {
    final scheme = (j['answerScheme'] as Map?) ?? const {};
    if (((scheme['modelAnswer'] as String?) ?? '').trim().isNotEmpty) return true;
    for (final pt in (scheme['markingPoints'] as List?) ?? const []) {
      if (pt is Map && (((pt['description'] ?? pt['text']) as String?) ?? '').trim().isNotEmpty) {
        return true;
      }
    }
    return false;
  }
}

class PaperBuilderApi {
  final Dio _dio;
  PaperBuilderApi(this._dio);

  String _base(String schoolId) => '/schools/${Uri.encodeComponent(schoolId)}/teacher-templates';

  Future<TemplateLists> listTemplates(String schoolId, {required int grade, required String subject}) async {
    final r = await _dio.get(_base(schoolId), queryParameters: {'grade': grade, 'subject': subject});
    return TemplateLists.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<PaperTemplateView> createTemplate(String schoolId, PaperTemplateView draft) async {
    final r = await _dio.post(_base(schoolId), data: draft.toDraftJson());
    return PaperTemplateView.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<PaperTemplateView> updateTemplate(String schoolId, PaperTemplateView t) async {
    final r = await _dio.put('${_base(schoolId)}/${Uri.encodeComponent(t.id)}', data: t.toDraftJson());
    return PaperTemplateView.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<PaperTemplateView> duplicateTemplate(String schoolId, String templateId, {String? name}) async {
    final r = await _dio.post('${_base(schoolId)}/${Uri.encodeComponent(templateId)}/duplicate',
        data: {if (name != null) 'name': name});
    return PaperTemplateView.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<List<ChapterEntry>> chapters(String subject, int grade) async {
    final r = await _dio.get('/catalog/${Uri.encodeComponent(subject)}/$grade/chapters',
        options: Options(receiveTimeout: const Duration(minutes: 5)));
    return (r.data as List).map((e) => ChapterEntry.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<AvailabilityView> availability(String schoolId, String templateId,
      {required List<String> chapterIds, bool fillFromOutsideScope = false}) async {
    final r = await _dio.post('${_base(schoolId)}/${Uri.encodeComponent(templateId)}/availability', data: {
      'scope': {'chapterIds': chapterIds},
      'fillFromOutsideScope': fillFromOutsideScope,
    });
    return AvailabilityView.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<TemplatePaperResult> generate({
    required String templateId,
    required List<String> chapterIds,
    int setCount = 1,
    bool allowGaps = false,
    bool fillFromOutsideScope = false,
    List<String> avoidQuestionIds = const [],
  }) async {
    final r = await _dio.post('/papers/generate-from-template',
        data: {
          'templateId': templateId,
          'scope': {'chapterIds': chapterIds},
          'setCount': setCount,
          'allowGaps': allowGaps,
          'fillFromOutsideScope': fillFromOutsideScope,
          if (avoidQuestionIds.isNotEmpty) 'avoidQuestionIds': avoidQuestionIds,
        },
        options: Options(receiveTimeout: const Duration(minutes: 3)));
    return TemplatePaperResult.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<GeneratedPaper> getPaper(String paperId) async {
    final r = await _dio.get('/papers/${Uri.encodeComponent(paperId)}');
    return parsePaper(Map<String, dynamic>.from(r.data as Map));
  }

  Future<PaperEditResult> swap(String paperId, String slot) async {
    final r = await _dio.post(
        '/papers/${Uri.encodeComponent(paperId)}/questions/${Uri.encodeComponent(slot)}/swap');
    return PaperEditResult.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<PaperEditResult> pick(String paperId, String slot, String questionId) async {
    final r = await _dio.post(
        '/papers/${Uri.encodeComponent(paperId)}/questions/${Uri.encodeComponent(slot)}',
        data: {'questionId': questionId});
    return PaperEditResult.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  /// Takes question [slot] ("7", with its OR) or only an alternative
  /// ("7_OR") off the paper and every set.
  Future<PaperRemoveResult> remove(String paperId, String slot) async {
    final r = await _dio.delete(
        '/papers/${Uri.encodeComponent(paperId)}/questions/${Uri.encodeComponent(slot)}');
    return PaperRemoveResult.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<List<BankItem>> searchBank({
    required String subject,
    required int grade,
    required int marks,
    List<String> chapterIds = const [],
    String? keyword,
    int limit = 60,
  }) async {
    final r = await _dio.post('/questions/search', data: {
      'subject': subject,
      'grade': grade,
      'minMarks': marks,
      'maxMarks': marks,
      if (chapterIds.isNotEmpty) 'chapterIds': chapterIds,
      if (keyword != null && keyword.trim().isNotEmpty) 'keyword': keyword.trim(),
      'limit': limit,
    });
    return (r.data as List).map((e) => BankItem.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  /// Renders the paper (or its answer key) on the server and fetches the PDF
  /// through this authenticated client. Opening the returned URL in a
  /// browser tab instead would send no bearer token and answer 401 -- the
  /// file route is auth-gated like every paper route.
  Future<Uint8List> pdfBytes(String paperId, {bool answerKey = false}) async {
    final r = await _dio.post(
        '/papers/${Uri.encodeComponent(paperId)}/export/${answerKey ? 'answer-key' : 'pdf'}',
        options: Options(receiveTimeout: const Duration(minutes: 2)));
    final url = (r.data as Map)['url'] as String;
    // The server answers "/api/v1/papers/..."; this client's base URL already
    // ends in /api/v1.
    final path = url.startsWith('/api/v1') ? url.substring('/api/v1'.length) : url;
    final f = await _dio.get<List<int>>(path, options: Options(responseType: ResponseType.bytes));
    return Uint8List.fromList(f.data ?? const []);
  }
}
