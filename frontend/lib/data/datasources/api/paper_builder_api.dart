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
import 'pillar_api.dart' show Catalog, ChapterEntry;

// Every failure this client raises is turned into a sentence by the shared
// serverErrorMessage (api_error.dart), which the builder's screens import.
// This file used to carry a mapper of its own; it had no 401, 403 or 404
// branch, so a teacher whose session expired inside the builder was told
// "The server answered 401. Try again." (re-audit of 2026-09-23). The two
// FastAPI shapes it did read and the shared one did not -- a `detail` object
// carrying `message` (the 400/409 of generate-from-template, with its
// availability report) and pydantic's "Value error, " prefix -- moved into
// serverErrorMessage rather than being kept here twice.

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

  /// The competency-based share of the paper this check would print, against
  /// CBSE's 50% (Task 125). Null from a server before the check existed.
  final CompetencyCheckView? competency;

  /// Whether a Foundation/Advanced version could differ, and why not. Null
  /// from a server before the check existed.
  final TierCheckView? tiers;

  AvailabilityView.fromJson(Map<String, dynamic> j)
      : complete = j['complete'] as bool? ?? false,
        bankQuestions = j['bankQuestions'] as int? ?? 0,
        keyedQuestions = j['keyedQuestions'] as int? ?? 0,
        sections = _maps(j['sections']).map(SectionAvailabilityView.fromJson).toList(),
        scopeNotes = List<String>.from(j['scopeNotes'] ?? const []),
        competency = j['competency'] is Map
            ? CompetencyCheckView.fromJson(Map<String, dynamic>.from(j['competency'] as Map))
            : null,
        tiers = j['tiers'] is Map ? TierCheckView.fromJson(Map<String, dynamic>.from(j['tiers'] as Map)) : null;

  List<SectionAvailabilityView> get short => sections.where((s) => s.isShort).toList();

  /// Nothing at all can be printed: generation refuses this (400), so the
  /// builder must not offer to try.
  bool get nothingFits => sections.every((s) => s.filled == 0);
}

/// The server's `CompetencyCheck` (paper_templates.py). `status` is `meets`,
/// `below_scope` (widening the chapters would reach 50%), `below_choice` (the
/// bank has enough; swap or pick them in) or `below_bank` (the bank cannot).
/// The sentences are the server's, shown as they come.
class CompetencyCheckView {
  final String status;
  final double share;
  final String summary;
  final String detail;
  final String counted;

  CompetencyCheckView.fromJson(Map<String, dynamic> j)
      : status = j['status'] as String? ?? '',
        share = (j['share'] as num?)?.toDouble() ?? 0,
        summary = j['summary'] as String? ?? '',
        detail = j['detail'] as String? ?? '',
        counted = j['counted'] as String? ?? '';

  bool get belowTarget => status != 'meets';
}

/// The server's `TierCheck`: whether a tier could change the paper, and the
/// sentence saying why not.
class TierCheckView {
  final bool available;
  final String sentence;

  TierCheckView.fromJson(Map<String, dynamic> j)
      : available = j['available'] as bool? ?? false,
        sentence = j['sentence'] as String? ?? '';
}

/// The server's paper JSON, made readable by the shared [GeneratedPaper]
/// model.
///
/// This used to also fill in `metadata.schoolName`, which a paper generated
/// from a template leaves null. That made this the only parse that survived
/// such a paper: the assessment detail screen reads the same body straight
/// through `GeneratedPaper.fromJson` and threw on it. `schoolName` is
/// nullable on the model now, so nothing here may patch it back -- the two
/// paths have to produce the same paper from the same bytes, which
/// test/assessment_detail/assessment_detail_contract_test.dart holds them to.
///
/// What is left fills fields the server gives defaults for anyway, kept for
/// papers stored before those defaults existed.
GeneratedPaper parsePaper(Map<String, dynamic> j) {
  Map<String, dynamic> fix(Map<String, dynamic> p) {
    final m = Map<String, dynamic>.from(p);
    final meta = Map<String, dynamic>.from(m['metadata'] as Map);
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

  /// A paper made another way than from a template (hand-picked, quick):
  /// whole by construction, so no gaps.
  TemplatePaperResult.ofPaper(this.paper)
      : assessmentId = paper.assessmentId,
        complete = true,
        gaps = const [],
        notes = const [];

  TemplatePaperResult.fromJson(Map<String, dynamic> j)
      : paper = parsePaper(Map<String, dynamic>.from(j['paper'] as Map)),
        assessmentId = j['assessmentId'] as String? ?? '',
        complete = j['complete'] as bool? ?? false,
        gaps = _maps(j['gaps']).map(SectionAvailabilityView.fromJson).toList(),
        notes = List<String>.from(j['notes'] ?? const []);
}

/// One section of the layout asked for that a quick paper prints short
/// because the bank cannot fill it (the server's SectionShortfall, D57).
class SectionShortfallView {
  final String label;
  final String name;
  final int marksEach;
  final int asked;
  final int printed;
  final int missingMarks;
  final int available;
  final String reason;

  SectionShortfallView.fromJson(Map<String, dynamic> j)
      : label = j['label'] as String? ?? '',
        name = j['name'] as String? ?? '',
        marksEach = j['marksEach'] as int? ?? 0,
        asked = j['asked'] as int? ?? 0,
        printed = j['printed'] as int? ?? 0,
        missingMarks = j['missingMarks'] as int? ?? 0,
        available = j['available'] as int? ?? 0,
        reason = j['reason'] as String? ?? '';
}

/// POST /papers/quick-generate's answer: the paper, the marks asked for and,
/// when the bank cannot make them, each section that prints short. A
/// [preview] was not saved.
class QuickPaperResult {
  final GeneratedPaper paper;
  final int marksAsked;
  final bool preview;
  final List<SectionShortfallView> shortfall;

  /// How many of the questions this version (level) prints have a
  /// difficulty measured from the marks teachers entered, which the level
  /// ranked on (EX-3); null from a server that does not count them.
  final int? difficultyMeasured;

  /// Whether a level can change this paper at all, and the server's
  /// sentence about this version's difficulty.
  final bool? tiersAvailable;
  final String? difficultySentence;

  QuickPaperResult.fromJson(Map<String, dynamic> j)
      : paper = parsePaper(j),
        marksAsked = j['marksAsked'] as int? ?? 0,
        preview = j['preview'] as bool? ?? false,
        shortfall = _maps(j['shortfall']).map(SectionShortfallView.fromJson).toList(),
        difficultyMeasured = j['difficultyMeasured'] as int?,
        tiersAvailable = j['tiersAvailable'] as bool?,
        difficultySentence = List<String>.from(j['warnings'] ?? const [])
            .where((w) => RegExp(r'^(Foundation|Standard|Advanced) version: ').hasMatch(w))
            .firstOrNull;

  int get marksHeld => paper.metadata.totalMarks;
  bool get holdsAll => marksHeld >= marksAsked;

  /// "A 12 × 1, B 1 × 2, ..." -- the layout the paper prints.
  String get layout => [
        for (final s in paper.sections)
          if (s.questions.isNotEmpty) '${s.label} ${s.questions.length} × ${s.questions.first.marks}',
      ].join(', ');
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

  // Paths with an id are written out in full, not via _base(): the
  // frontend/backend contract test reads each call's literal path.
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
    final r = await _dio.put('/schools/${Uri.encodeComponent(schoolId)}/teacher-templates/${Uri.encodeComponent(t.id)}', data: t.toDraftJson());
    return PaperTemplateView.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<PaperTemplateView> duplicateTemplate(String schoolId, String templateId, {String? name}) async {
    final r = await _dio.post('/schools/${Uri.encodeComponent(schoolId)}/teacher-templates/${Uri.encodeComponent(templateId)}/duplicate',
        data: {if (name != null) 'name': name});
    return PaperTemplateView.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  /// Every class-subject pair the bank holds questions for. The builder offers
  /// a subject only when its class has a row here (audit D40).
  Future<Catalog> catalog() async {
    final r = await _dio.get('/catalog', options: Options(receiveTimeout: const Duration(minutes: 5)));
    return Catalog.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  Future<List<ChapterEntry>> chapters(String subject, int grade) async {
    final r = await _dio.get('/catalog/${Uri.encodeComponent(subject)}/$grade/chapters',
        options: Options(receiveTimeout: const Duration(minutes: 5)));
    return (r.data as List).map((e) => ChapterEntry.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<AvailabilityView> availability(String schoolId, String templateId,
      {required List<String> chapterIds, bool fillFromOutsideScope = false}) async {
    final r = await _dio.post('/schools/${Uri.encodeComponent(schoolId)}/teacher-templates/${Uri.encodeComponent(templateId)}/availability', data: {
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
    double? teacherSeconds,
  }) async {
    final r = await _dio.post('/papers/generate-from-template',
        data: {
          'templateId': templateId,
          'scope': {'chapterIds': chapterIds},
          'setCount': setCount,
          'allowGaps': allowGaps,
          'fillFromOutsideScope': fillFromOutsideScope,
          if (avoidQuestionIds.isNotEmpty) 'avoidQuestionIds': avoidQuestionIds,
          // The teacher's time on this paper (time saved is the baseline less
          // it, server-side; audit D49).
          if (teacherSeconds != null) 'teacherSeconds': teacherSeconds,
        },
        options: Options(receiveTimeout: const Duration(minutes: 3)));
    return TemplatePaperResult.fromJson(Map<String, dynamic>.from(r.data as Map));
  }

  /// A paper of exactly [questionIds], in that order within each marks
  /// section (POST /papers/generate-from-ids): the hand-picked paper. The
  /// server refuses (404) an id its bank for the class does not hold rather
  /// than print the paper without it (audit D57).
  Future<GeneratedPaper> generateFromIds({
    required String subject,
    required int grade,
    required List<String> questionIds,
    String? title,
    double? teacherSeconds,
  }) async {
    final r = await _dio.post('/papers/generate-from-ids',
        data: {
          'subject': subject,
          'grade': grade,
          'questionIds': questionIds,
          if (title != null) 'title': title,
          if (teacherSeconds != null) 'teacherSeconds': teacherSeconds,
        },
        options: Options(receiveTimeout: const Duration(minutes: 3)));
    return parsePaper(Map<String, dynamic>.from(r.data as Map));
  }

  /// A quick paper of [totalMarks] (POST /papers/quick-generate): the server
  /// rebalances a section the bank cannot fill so the paper holds the marks
  /// whenever the bank can, and otherwise names the shortfall by section.
  /// [preview] saves nothing -- the builder shows the answer before the
  /// teacher saves it (audit D57).
  Future<QuickPaperResult> quickGenerate({
    required String subject,
    required int grade,
    required int totalMarks,
    String tier = 'standard',
    List<String> chapterIds = const [],
    int setCount = 1,
    bool preview = false,
    double? teacherSeconds,
  }) async {
    final r = await _dio.post('/papers/quick-generate',
        data: {
          'subject': subject,
          'grade': grade,
          'totalMarks': totalMarks,
          'tier': tier,
          'chapterIds': chapterIds,
          'setCount': setCount,
          'preview': preview,
          if (teacherSeconds != null) 'teacherSeconds': teacherSeconds,
        },
        options: Options(receiveTimeout: const Duration(minutes: 3)));
    return QuickPaperResult.fromJson(Map<String, dynamic>.from(r.data as Map));
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

  /// Bank questions for a class; [marks] null is any marks.
  Future<List<BankItem>> searchBank({
    required String subject,
    required int grade,
    required int? marks,
    List<String> chapterIds = const [],
    String? keyword,
    int limit = 60,
  }) async {
    final r = await _dio.post('/questions/search', data: {
      'subject': subject,
      'grade': grade,
      if (marks != null) 'minMarks': marks,
      if (marks != null) 'maxMarks': marks,
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
