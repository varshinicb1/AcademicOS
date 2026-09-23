import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../data/datasources/api/paper_builder_api.dart';
import '../../data/datasources/api/pillar_api.dart' show ChapterEntry;
import '../../domain/repositories/requests.dart' show GeneratedPaper, GeneratedQuestion;
import 'builder_memory.dart';

enum BuilderStep { classSubject, template, scope, paper, finish }

/// Hands a finished PDF to the teacher. On the web build this is
/// `Printing.sharePdf`, which the browser turns into a download; tests pass
/// a recorder.
typedef PdfSaver = Future<void> Function(Uint8List bytes, String filename);

/// The CBSE classes a teacher can set a paper for, and each class's subjects.
/// Presets exist for classes 6-10's main subjects (template_presets.py); the
/// rest start from a template the teacher builds, never a dead end.
///
/// 6-10, not 6-12: the first release serves those classes (the user, 2026-09-23).
/// The bank holds nothing at all for class 11 and no Maths or Science paper for
/// 12 -- correctness-first left only board questions whose answer key was
/// verified -- so offering them ended in "Unable to find sufficient questions"
/// after a teacher had chosen a class, a subject and a template. A class we
/// cannot serve is not offered until we can.
const builderGrades = [6, 7, 8, 9, 10];

/// The senior-school branch is unreachable while [builderGrades] stops at 10.
/// It is kept, not deleted: it is the subject list classes 11-12 come back
/// with, and rebuilding it from memory later would be worse than reading it.
List<String> builderSubjects(int grade) => grade >= 11
    ? const ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'Accountancy', 'Business Studies',
        'Economics', 'History', 'Political Science', 'Geography', 'English', 'Hindi', 'Computer Science']
    : const ['Mathematics', 'Science', 'Social Science', 'English', 'Hindi', 'Sanskrit', 'Computer Science'];

/// The whole builder's state: one class, one flow, no page owns a copy.
///
/// Every server call goes through [PaperBuilderApi], and every failure
/// becomes a sentence on the step it happened on ([apiErrorMessage]) with the
/// action that retries it -- never a blank screen or a raw exception.
class PaperBuilderController extends ChangeNotifier {
  final PaperBuilderApi api;
  final String schoolId;
  final BuilderMemory memory;
  final PdfSaver savePdf;

  /// "Quick paper (CBSE pattern)": the builder with the class's CBSE annual
  /// preset already chosen, so the teacher lands on the chapters.
  final bool quick;

  PaperBuilderController({
    required this.api,
    required this.schoolId,
    required this.memory,
    required this.savePdf,
    this.quick = false,
  });

  BuilderStep step = BuilderStep.classSubject;
  int? grade;
  String? subject;

  TemplateLists? templates;
  bool loadingTemplates = false;
  String? templatesError;
  PaperTemplateView? template;

  List<ChapterEntry> chapters = const [];
  bool loadingChapters = false;
  String? chaptersError;
  final Set<String> chapterIds = {};
  bool fillFromOutsideScope = false;
  int setCount = 1;

  AvailabilityView? availability;
  bool checking = false;
  String? availabilityError;
  int _ticket = 0;

  /// How long a chapter tick waits for the next one before the bank is
  /// checked. Ticking six chapters for a half-yearly paper sent six checks,
  /// five of them for selections the teacher was only passing through;
  /// now it sends one. Generate stays off while a check is waiting.
  static const availabilityDebounce = Duration(milliseconds: 400);
  Timer? _debounce;
  Completer<void>? _waiting;

  bool generating = false;
  String? generateError;
  TemplatePaperResult? result;
  GeneratedPaper? paper;

  /// The sections the paper was generated from: what "short" is measured
  /// against after a question is removed.
  List<TemplateSectionView> _paperSections = const [];

  /// Questions removed from each section (by section id), for the gap line.
  final Map<String, int> removedBySection = {};

  /// Set label -> paper id, from the generated paper (A is the paper itself).
  Map<String, String> setIds = const {};
  String viewingSet = 'A';
  final Map<String, GeneratedPaper> _setPapers = {};
  bool loadingSet = false;
  String? setError;

  final Set<String> busySlots = {};
  final Map<String, String> slotErrors = {};
  final Map<String, List<String>> slotNotes = {};

  bool downloading = false;
  String? downloadError;
  final List<String> downloaded = [];

  bool get _disposed => _isDisposed;
  bool _isDisposed = false;

  @override
  void dispose() {
    _debounce?.cancel();
    _isDisposed = true;
    super.dispose();
  }

  void _changed() {
    if (!_disposed) notifyListeners();
  }

  // ---------------------------------------------------------------- start

  /// Opens where the teacher left off: a remembered class and subject go
  /// straight to the templates (one tap to change), a remembered template is
  /// pre-selected so "Next" is the only tap left.
  Future<void> start() async {
    final g = memory.grade, s = memory.subject;
    if (g != null && s != null && builderSubjects(g).contains(s)) {
      grade = g;
      subject = s;
      step = BuilderStep.template;
      _changed();
      await loadTemplates();
    }
  }

  void pickGrade(int g) {
    if (grade == g) return;
    grade = g;
    if (subject != null && !builderSubjects(g).contains(subject)) subject = null;
    _resetFromTemplates();
    _changed();
  }

  void pickSubject(String s) {
    subject = s;
    _resetFromTemplates();
    _changed();
  }

  void _resetFromTemplates() {
    templates = null;
    templatesError = null;
    template = null;
    _resetFromScope();
  }

  void _resetFromScope() {
    chapters = const [];
    chaptersError = null;
    chapterIds.clear();
    fillFromOutsideScope = false;
    availability = null;
    availabilityError = null;
    _resetPaper();
  }

  void _resetPaper() {
    result = null;
    paper = null;
    generateError = null;
    setIds = const {};
    viewingSet = 'A';
    _setPapers.clear();
    busySlots.clear();
    slotErrors.clear();
    slotNotes.clear();
    removedBySection.clear();
    _paperSections = const [];
    downloaded.clear();
    downloadError = null;
  }

  bool get canLeaveClassSubject => grade != null && subject != null;

  Future<void> confirmClassSubject() async {
    if (!canLeaveClassSubject) return;
    memory.remember(grade: grade!, subject: subject!, templateId: memory.templateId);
    step = BuilderStep.template;
    _changed();
    if (templates == null) await loadTemplates();
  }

  void goTo(BuilderStep s) {
    step = s;
    _changed();
  }

  void back() {
    if (step.index == 0) return;
    step = BuilderStep.values[step.index - 1];
    _changed();
  }

  // ------------------------------------------------------------ templates

  Future<void> loadTemplates() async {
    if (grade == null || subject == null) return;
    loadingTemplates = true;
    templatesError = null;
    _changed();
    try {
      templates = await api.listTemplates(schoolId, grade: grade!, subject: subject!);
      final remembered = memory.templateId;
      template ??= templates!.all.where((t) => t.id == remembered).firstOrNull;
      if (quick && template == null) {
        template = templates!.presets.where((t) => t.examType == 'annual').firstOrNull ??
            templates!.presets.firstOrNull;
      }
    } catch (e) {
      templatesError = apiErrorMessage(e);
    } finally {
      loadingTemplates = false;
      _changed();
    }
    if (quick && template != null && step == BuilderStep.template) await useTemplate(template!);
  }

  void selectTemplate(PaperTemplateView t) {
    template = t;
    _changed();
  }

  /// "Use": the template for this paper. The chapters start from the
  /// template's own saved scope, if it has one.
  Future<void> useTemplate(PaperTemplateView t) async {
    final sameTemplate = template?.id == t.id && availability != null;
    template = t;
    memory.remember(grade: grade!, subject: subject!, templateId: t.id);
    if (!sameTemplate) {
      _resetFromScope();
      chapterIds.addAll(t.scopeChapterIds);
    }
    step = BuilderStep.scope;
    _changed();
    await Future.wait([if (chapters.isEmpty) loadChapters(), checkAvailability()]);
  }

  /// Saves a template from the section editor and makes it this paper's.
  ///
  /// A new template is created. Editing one of the teacher's own saves it in
  /// place. Anything else (a preset, a colleague's shared template) is
  /// "Save as new": duplicate first, then update the copy -- the duplicate
  /// keeps a preset's generated instructions marked generated, so the
  /// printed instructions follow the edited sections instead of repeating
  /// the preset's old lines (see _printed_instructions on the server).
  Future<PaperTemplateView> saveTemplate(PaperTemplateView draft,
      {required bool asNew, String? ownerId}) async {
    PaperTemplateView saved;
    if (draft.id.isEmpty) {
      saved = await api.createTemplate(schoolId, draft);
    } else if (!asNew && !draft.isPreset && draft.ownerId == ownerId) {
      saved = await api.updateTemplate(schoolId, draft);
    } else {
      final copy = await api.duplicateTemplate(schoolId, draft.id, name: draft.name);
      saved = await api.updateTemplate(
          schoolId,
          PaperTemplateView.fromJson(copy.raw).copyWith(
            name: draft.name,
            totalMarks: draft.totalMarks,
            durationMinutes: draft.durationMinutes,
            sections: draft.sections,
          ));
    }
    await _refreshTemplateLists();
    await useTemplate(saved);
    return saved;
  }

  Future<PaperTemplateView> duplicate(PaperTemplateView t) async {
    final copy = await api.duplicateTemplate(schoolId, t.id);
    await _refreshTemplateLists();
    template = copy;
    _changed();
    return copy;
  }

  Future<void> _refreshTemplateLists() async {
    try {
      templates = await api.listTemplates(schoolId, grade: grade!, subject: subject!);
    } catch (_) {
      // The save itself succeeded; the list refreshes on the next visit.
    }
  }

  // ----------------------------------------------------------------- scope

  Future<void> loadChapters() async {
    loadingChapters = true;
    chaptersError = null;
    _changed();
    try {
      chapters = await api.chapters(subject!, grade!);
    } catch (e) {
      chaptersError = apiErrorMessage(e);
    } finally {
      loadingChapters = false;
      _changed();
    }
  }

  /// Chapters grouped under their CBSE unit, in syllabus order.
  List<(String, List<ChapterEntry>)> get chaptersByUnit {
    final out = <(String, List<ChapterEntry>)>[];
    for (final c in chapters) {
      final unit = c.unitName ?? 'Chapters';
      if (out.isEmpty || out.last.$1 != unit) out.add((unit, []));
      out.last.$2.add(c);
    }
    return out;
  }

  /// Ticks a chapter; the bank is checked once the teacher pauses
  /// ([availabilityDebounce]). Until then the step says it is checking and
  /// Generate is off, so a paper is never generated against the answer for
  /// an older selection.
  Future<void> toggleChapter(String id) {
    chapterIds.contains(id) ? chapterIds.remove(id) : chapterIds.add(id);
    _debounce?.cancel();
    ++_ticket; // an answer on its way is for the selection before this tick
    checking = true;
    availabilityError = null;
    _changed();
    final waiting = _waiting ??= Completer<void>();
    _debounce = Timer(availabilityDebounce, checkAvailability);
    return waiting.future;
  }

  Future<void> useAllChapters() {
    chapterIds.clear();
    return checkAvailability();
  }

  void setSets(int n) {
    setCount = n;
    _changed();
  }

  /// The template's availability for the chosen chapters: the server's own
  /// selection run dry (Task 904), so what it says is what Generate prints.
  /// Re-run on every change; an answer to an older selection is dropped
  /// when a newer one is already on its way.
  Future<void> checkAvailability() async {
    _debounce?.cancel();
    final waiting = _waiting;
    _waiting = null;
    try {
      await _check();
    } finally {
      if (waiting != null && !waiting.isCompleted) waiting.complete();
    }
  }

  Future<void> _check() async {
    final t = template;
    if (t == null) return;
    final ticket = ++_ticket;
    checking = true;
    availabilityError = null;
    _changed();
    try {
      final a = await api.availability(schoolId, t.id,
          chapterIds: chapterIds.toList(), fillFromOutsideScope: fillFromOutsideScope);
      if (ticket != _ticket) return;
      availability = a;
    } catch (e) {
      if (ticket != _ticket) return;
      availabilityError = apiErrorMessage(e);
    } finally {
      if (ticket == _ticket) {
        checking = false;
        _changed();
      }
    }
  }

  /// Applies a scope fix in place. A fix that changes the template (marks,
  /// count, type, ORs, the competency rule) is returned as an edited draft
  /// instead, for the section editor to show and the teacher to save -- the
  /// paper's total changes with it, and that is theirs to confirm.
  Future<PaperTemplateView?> applyFix(SectionAvailabilityView section, SectionFixView fix) async {
    switch (fix.kind) {
      case 'widen_scope':
        await useAllChapters();
        return null;
      case 'fill_from_outside_scope':
        fillFromOutsideScope = true;
        await checkAvailability();
        return null;
    }
    final t = template!;
    final sections = <TemplateSectionView>[];
    for (final (i, s) in t.sections.indexed) {
      final id = s.id.isNotEmpty ? s.id : 's${i + 1}';
      if (id != section.sectionId) {
        sections.add(s);
        continue;
      }
      switch (fix.kind) {
        case 'change_marks':
          sections.add(s.copyWith(marksEach: fix.marksEach));
        case 'reduce_count':
          if ((fix.questionCount ?? 0) > 0) sections.add(s.copyWith(questionCount: fix.questionCount));
        case 'reduce_choices':
          sections.add(s.copyWith(choiceCount: fix.choiceCount));
        case 'relax_type':
          sections.add(s.copyWith(questionTypes: fix.questionTypes));
        case 'relax_competency':
          sections.add(s.copyWith(dropCompetencyRule: true));
        default:
          sections.add(s);
      }
    }
    final draft = t.copyWith(sections: sections);
    return draft.copyWith(totalMarks: draft.sectionMarks);
  }

  // -------------------------------------------------------------- generate

  bool get canGenerate =>
      template != null && availability != null && !checking && !generating && !availability!.nothingFits;

  /// [avoid]: questions to print again only where the bank has nothing
  /// else ("Make another like this").
  Future<void> generate({List<String> avoid = const []}) async {
    if (!canGenerate) return;
    generating = true;
    generateError = null;
    _changed();
    try {
      final r = await api.generate(
        templateId: template!.id,
        chapterIds: chapterIds.toList(),
        setCount: setCount,
        // The teacher has seen the gaps on this screen; Generate with gaps
        // showing is their "print it short". Without them, a gap that
        // appeared since the check is still refused (409), not printed.
        allowGaps: !availability!.complete,
        fillFromOutsideScope: fillFromOutsideScope,
        avoidQuestionIds: avoid,
      );
      _resetPaper();
      result = r;
      paper = r.paper;
      _paperSections = template!.sections;
      setIds = {
        (r.paper.setLabel ?? 'A'): r.paper.id,
        for (final s in r.paper.sets) (s.setLabel ?? s.metadata.setLabel ?? '?'): s.id,
      };
      for (final s in r.paper.sets) {
        _setPapers[s.setLabel ?? '?'] = s;
      }
      step = BuilderStep.paper;
    } catch (e) {
      generateError = apiErrorMessage(e);
    } finally {
      generating = false;
      _changed();
    }
  }

  /// "Make another like this": the same template and chapters, fresh
  /// questions, as a new saved paper. Generation is deterministic, so
  /// without the list the same template and chapters print the same paper
  /// again; with it, this paper's questions (as the teacher left it, swaps
  /// and removals included) are printed only where the bank has nothing
  /// else, and the server's notes name each one.
  Future<void> makeAnother() async {
    final previous = onPaper.toList()..sort();
    step = BuilderStep.scope;
    _changed();
    await generate(avoid: previous);
  }

  GeneratedPaper? get shownPaper => viewingSet == 'A' ? paper : _setPapers[viewingSet];

  int get paperMarks => paper?.sections.fold<int>(0, (s, x) => s + x.totalMarks) ?? 0;
  int get paperQuestions => paper?.sections.fold<int>(0, (s, x) => s + x.questions.length) ?? 0;

  /// Shows another set. A set is edited through set A (the server applies a
  /// swap or pick to every set), so a set shown after an edit is fetched
  /// fresh rather than read from the generate response.
  Future<void> showSet(String label) async {
    viewingSet = label;
    setError = null;
    _changed();
    if (label == 'A' || _setPapers[label] != null) return;
    loadingSet = true;
    _changed();
    try {
      _setPapers[label] = await api.getPaper(setIds[label]!);
    } catch (e) {
      setError = apiErrorMessage(e);
    } finally {
      loadingSet = false;
      _changed();
    }
  }

  /// Every section printing fewer questions than the template asks for --
  /// a gap generation left, or one the teacher made with Remove -- in
  /// template order. Stays on screen until the paper is generated again.
  List<({String title, int printed, int needed, int removed})> get shortSections {
    final p = paper;
    if (p == null) return const [];
    final printed = {for (final s in p.sections) s.sectionId: s.questions.length};
    return [
      for (final (i, s) in _paperSections.indexed)
        if ((printed[s.id.isNotEmpty ? s.id : 's${i + 1}'] ?? 0) < s.questionCount)
          (
            title: s.title,
            printed: printed[s.id.isNotEmpty ? s.id : 's${i + 1}'] ?? 0,
            needed: s.questionCount,
            removed: removedBySection[s.id.isNotEmpty ? s.id : 's${i + 1}'] ?? 0,
          ),
    ];
  }

  /// Removes question [slot] (with its OR) or only an alternative
  /// ("7_OR"), from the paper and every set. The numbers after it move up,
  /// so notes and errors kept under the old numbers are dropped.
  Future<void> remove(String slot) async {
    final p = paper;
    if (p == null || busySlots.contains(slot)) return;
    final sectionId = p.sections
        .firstWhere((s) => s.questions.any((q) => '${q.displayNumber}' == slot.split('_').first))
        .sectionId;
    busySlots.add(slot);
    slotErrors.remove(slot);
    _changed();
    try {
      final r = await api.remove(p.id, slot);
      paper = r.paper;
      _setPapers.clear();
      downloaded.clear();
      slotNotes.clear();
      slotErrors.clear();
      if (!slot.endsWith('_OR')) removedBySection[sectionId] = (removedBySection[sectionId] ?? 0) + 1;
    } catch (e) {
      slotErrors[slot] = apiErrorMessage(e);
    } finally {
      busySlots.remove(slot);
      _changed();
    }
  }

  void _edited(PaperEditResult r) {
    paper = r.paper;
    // Every other set changed on the server too.
    _setPapers.clear();
    slotNotes[r.slot] = r.notes;
    downloaded.clear();
  }

  Future<void> swap(String slot) => _edit(slot, () => api.swap(paper!.id, slot));

  Future<void> pick(String slot, String questionId) => _edit(slot, () => api.pick(paper!.id, slot, questionId));

  Future<void> _edit(String slot, Future<PaperEditResult> Function() call) async {
    if (paper == null || busySlots.contains(slot)) return;
    busySlots.add(slot);
    slotErrors.remove(slot);
    _changed();
    try {
      _edited(await call());
    } catch (e) {
      slotErrors[slot] = apiErrorMessage(e);
    } finally {
      busySlots.remove(slot);
      _changed();
    }
  }

  /// Every question id on the paper, ORs included -- what the picker must
  /// not offer again.
  Set<String> get onPaper => {
        for (final s in paper?.sections ?? const [])
          for (final GeneratedQuestion q in s.questions) ...[
            q.questionId,
            if (q.internalChoiceQuestionId != null) q.internalChoiceQuestionId!,
          ],
      };

  // --------------------------------------------------------------- finish

  /// Downloads the paper PDF and its answer-key PDF, for every set.
  Future<void> downloadAll() async {
    if (paper == null || downloading) return;
    downloading = true;
    downloadError = null;
    downloaded.clear();
    _changed();
    final base = _fileBase();
    try {
      for (final e in setIds.entries) {
        final suffix = setIds.length > 1 ? '_set_${e.key.toLowerCase()}' : '';
        await savePdf(await api.pdfBytes(e.value), '$base${suffix}_paper.pdf');
        downloaded.add('Paper${setIds.length > 1 ? ' (Set ${e.key})' : ''}');
        _changed();
        await savePdf(await api.pdfBytes(e.value, answerKey: true), '$base${suffix}_answer_key.pdf');
        downloaded.add('Answer key${setIds.length > 1 ? ' (Set ${e.key})' : ''}');
        _changed();
      }
    } catch (e) {
      downloadError = apiErrorMessage(e);
    } finally {
      downloading = false;
      _changed();
    }
  }

  /// The template's name as a file name ("class_10_science_half_yearly_
  /// examination"): the name a teacher gave it, or the preset's, which
  /// already says the class and subject.
  String _fileBase() {
    final slug = (template?.name ?? 'class ${grade ?? ''} ${subject ?? ''} paper')
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9]+'), '_')
        .replaceAll(RegExp(r'^_+|_+$'), '');
    return slug.isEmpty ? 'paper' : slug;
  }
}
