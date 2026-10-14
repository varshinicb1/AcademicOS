import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/constants/release_scope.dart';
import '../../data/datasources/api/api_error.dart';
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
/// Presets exist for classes 1-10's main subjects (template_presets.py: CBSE
/// patterns for 9-10, suggested school patterns below); the rest start from a
/// template the teacher builds, never a dead end.
///
/// 1-10, not 1-12 (the user, 2026-09-23: "skip 11 and 12 for now"). Which of
/// them the builder offers is [PaperBuilderController.offeredGrades]: only a
/// class the bank holds questions for, so a teacher never chooses a class,
/// a subject and a template to end at "Unable to find sufficient questions".
const builderGrades = releaseGrades;

/// The subjects the builder knows how to offer for a class, in the order it
/// shows them. What it actually offers is the part of this list the bank holds
/// questions for ([PaperBuilderController.subjectsFor]): offered unconditionally,
/// 21 of the 35 class 6-10 pairs led a teacher to a template and then to
/// "no question in the bank fits" (audit D40, 2026-09-27).
///
/// The senior-school branch is unreachable while [builderGrades] stops at 10.
/// It is kept, not deleted: it is the subject list classes 11-12 come back
/// with, and rebuilding it from memory later would be worse than reading it.
///
/// Classes 1-5 have the subjects NCERT publishes a book for: EVS from class 3
/// ("The World Around Us"), so class 1 is never told EVS has no questions.
List<String> builderSubjects(int grade) => grade >= 11
    ? const ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'Accountancy', 'Business Studies',
        'Economics', 'History', 'Political Science', 'Geography', 'English', 'Hindi', 'Computer Science']
    : grade >= 6
        ? const ['Mathematics', 'Science', 'Social Science', 'English', 'Hindi', 'Sanskrit', 'Computer Science']
        : grade >= 3
            ? const ['Mathematics', 'EVS', 'English', 'Hindi']
            : const ['Mathematics', 'English', 'Hindi'];

/// The whole builder's state: one class, one flow, no page owns a copy.
///
/// Every server call goes through [PaperBuilderApi], and every failure
/// becomes a sentence on the step it happened on ([serverErrorMessage], the
/// app's one mapper) with the action that retries it -- never a blank screen
/// or a raw exception.
///
/// "With the action that retries it" means only where sending the same
/// request again could work ([isRetryable]), which each error below carries
/// as its own `...Retryable` flag. Task 803's brief asked for a Retry on
/// every branch, the expired session and the refused school included; the
/// helper the same task told this builder to adopt says the opposite
/// (api_error.dart: "a Retry button there only teaches the user to click
/// it"), and the helper wins. A 401/403/404/409/422 is refused again every
/// time, so a Retry there is a button that cannot work -- and for 401 the
/// session interceptor is already sending the teacher to Sign in, which the
/// button would compete with. Each of those branches has a real recovery
/// already on the screen: Sign in for the expired session, "Change" back to
/// the template step for a template a colleague deleted, another class or
/// subject for a school the account is not in. The message stands on its
/// own there and no button is drawn. Four other screens already read the
/// helper this way (gap_analysis.dart, mastery_dashboard.dart,
/// principal_page.dart, student_schedule_page.dart).
class PaperBuilderController extends ChangeNotifier {
  final PaperBuilderApi api;
  final String schoolId;
  final BuilderMemory memory;
  final PdfSaver savePdf;

  /// "Quick paper (CBSE pattern)": the builder with the class's CBSE annual
  /// preset already chosen, so the teacher lands on the chapters.
  final bool quick;

  /// The time now; tests pass a clock they move.
  final DateTime Function() clock;

  PaperBuilderController({
    required this.api,
    required this.schoolId,
    required this.memory,
    required this.savePdf,
    this.quick = false,
    DateTime Function()? clock,
  }) : clock = clock ?? DateTime.now {
    _sessionStart = this.clock();
  }

  /// When the teacher started on the paper being made: the builder opening,
  /// then each paper generated (the next one starts there). Every generate
  /// request sends the time since, which the server subtracts from the
  /// baseline as the teacher's own time on the paper (audit D49: "time
  /// saved" was the baseline less server compute, 0.02-0.15 s).
  late DateTime _sessionStart;

  /// Seconds the teacher has spent on the paper being made.
  double get teacherSeconds => clock().difference(_sessionStart).inMilliseconds / 1000;

  /// Called once a paper is generated: the next paper's time starts now.
  void restartTeacherClock() => _sessionStart = clock();

  BuilderStep step = BuilderStep.classSubject;
  int? grade;
  String? subject;

  /// Subjects with questions, by class, from GET /catalog. Null until it loads.
  Map<int, Set<String>>? _stocked;
  bool loadingCatalog = false;
  String? catalogError;
  bool catalogRetryable = false;

  TemplateLists? templates;
  bool loadingTemplates = false;
  String? templatesError;
  bool templatesRetryable = false;
  PaperTemplateView? template;

  List<ChapterEntry> chapters = const [];
  bool loadingChapters = false;
  String? chaptersError;
  bool chaptersRetryable = false;
  final Set<String> chapterIds = {};
  bool fillFromOutsideScope = false;
  int setCount = 1;

  /// 'foundation', 'standard' or 'advanced' (R-C4). Offered only where the
  /// availability check says a version could differ ([tierChoice]).
  String tier = 'standard';

  AvailabilityView? availability;
  bool checking = false;
  String? availabilityError;
  bool availabilityRetryable = false;
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

  /// "Pick the questions yourself": the paper is made from exactly the
  /// questions in [picked] (POST /papers/generate-from-ids), not from a
  /// template. The scope step shows the bank to pick from instead of the
  /// template's chapters. The web had no way to do this at all (audit D57:
  /// the live bundle called generate-from-ids 0 times).
  bool handPicked = false;
  final List<BankItem> picked = [];

  /// The marks a quick paper (by total marks and level) was asked for; null
  /// for a paper made another way.
  int? quickMarksAsked;

  /// Whether this paper came from a template ("Make another like this"
  /// needs one).
  bool get fromTemplate => !handPicked && quickMarksAsked == null;

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
  bool downloadRetryable = false;
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

  /// The class and subject of the teacher's last paper, offered on the first
  /// step as "Continue where you left off"; null when there is none the bank
  /// can still set a paper in.
  ({int grade, String subject})? lastTime;

  /// A new paper starts at the class and subject, with the last paper's
  /// offered as one tap ([continueLastTime]). It used to reopen the last
  /// paper's class, subject and template at step 2, which a teacher setting
  /// a different paper took for a mistake (QA P-25). "Quick paper" is the
  /// exception: it is the one-tap way to a paper, so a remembered class goes
  /// straight to its CBSE pattern.
  Future<void> start() async {
    await loadCatalog();
    final g = memory.grade, s = memory.subject;
    if (g == null || s == null || !subjectsFor(g).contains(s)) return;
    if (!quick) {
      lastTime = (grade: g, subject: s);
      _changed();
      return;
    }
    grade = g;
    subject = s;
    step = BuilderStep.template;
    _changed();
    await loadTemplates();
  }

  /// "Continue where you left off": the last class and subject, on to the
  /// templates with the last template chosen -- "Use" is the only tap left.
  Future<void> continueLastTime() async {
    final last = lastTime;
    if (last == null) return;
    if (grade != last.grade || subject != last.subject) {
      grade = last.grade;
      subject = last.subject;
      _resetFromTemplates();
    }
    step = BuilderStep.template;
    _changed();
    if (templates == null) await loadTemplates();
  }

  /// Which subjects the bank can set a paper in, read once per builder.
  Future<void> loadCatalog() async {
    loadingCatalog = true;
    catalogError = null;
    catalogRetryable = false;
    _changed();
    try {
      final catalog = await api.catalog();
      final stocked = <int, Set<String>>{};
      for (final e in catalog.entries) {
        if (e.questionCount > 0) stocked.putIfAbsent(e.grade, () => {}).add(e.subject);
      }
      _stocked = stocked;
    } catch (e) {
      catalogError = serverErrorMessage(e);
      catalogRetryable = isRetryable(e);
    } finally {
      loadingCatalog = false;
      _changed();
    }
  }

  /// The classes offered: every [builderGrades] class while the catalog loads,
  /// then only those the bank holds questions for -- a class with nothing to
  /// set a paper from is not offered (audit D22, D40).
  List<int> get offeredGrades => [
        for (final g in builderGrades)
          if (_stocked == null || (_stocked![g]?.isNotEmpty ?? false)) g,
      ];

  /// The subjects offered for [grade]: [builderSubjects] that the bank holds
  /// questions for. Empty until the catalog has loaded -- never the whole list
  /// as a guess, which is the dead end this exists to close.
  List<String> subjectsFor(int grade) {
    if (!builderGrades.contains(grade)) return const [];
    final stocked = _stocked?[grade];
    if (stocked == null) return const [];
    return [for (final s in builderSubjects(grade)) if (stocked.contains(s)) s];
  }

  /// The subjects the builder knows but the bank has nothing for in [grade],
  /// so the step can say so instead of leaving a teacher to wonder where
  /// Hindi went.
  List<String> notYetFor(int grade) {
    if (_stocked == null || !builderGrades.contains(grade)) return const [];
    final offered = subjectsFor(grade).toSet();
    return [for (final s in builderSubjects(grade)) if (!offered.contains(s)) s];
  }

  void pickGrade(int g) {
    if (grade == g) return;
    grade = g;
    if (subject != null && !subjectsFor(g).contains(subject)) subject = null;
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
    templatesRetryable = false;
    template = null;
    handPicked = false;
    picked.clear();
    _resetFromScope();
  }

  void _resetFromScope() {
    chapters = const [];
    chaptersError = null;
    chaptersRetryable = false;
    chapterIds.clear();
    fillFromOutsideScope = false;
    tier = 'standard';
    availability = null;
    availabilityError = null;
    availabilityRetryable = false;
    _resetPaper();
  }

  void _resetPaper() {
    result = null;
    paper = null;
    quickMarksAsked = null;
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
    downloadRetryable = false;
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
    templatesRetryable = false;
    _changed();
    try {
      templates = await api.listTemplates(schoolId, grade: grade!, subject: subject!);
      if (quick && template == null) {
        // "Quick paper (CBSE pattern)" is the class's CBSE annual pattern,
        // whatever was used last: the remembered template won, so it opened
        // a class 8 periodic test or a teacher's own class test (QA P-14).
        template = templates!.presets.where((t) => t.examType == 'annual').firstOrNull ??
            templates!.presets.firstOrNull;
      }
      final remembered = memory.templateId;
      template ??= templates!.all.where((t) => t.id == remembered).firstOrNull;
    } catch (e) {
      templatesError = serverErrorMessage(e);
      templatesRetryable = isRetryable(e);
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
    final sameTemplate = template?.id == t.id && availability != null && !handPicked;
    handPicked = false;
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
      // Cleared here, not only in loadTemplates: a refresh that succeeds
      // after one that failed has answered the banner's question. Left set,
      // it outlived its failure -- the template step went on saying the list
      // could not be loaded over the list it had just reloaded, until the
      // teacher hit "Try again" or changed class.
      templatesError = null;
      templatesRetryable = false;
    } catch (e) {
      // The save itself succeeded, so this is not the save's failure -- but a
      // list that quietly stayed as it was is its own: the template the
      // teacher just saved would simply not be in it. The template step says
      // why, above the list it still has, with the "Try again" that reloads
      // it where trying again can work.
      templatesError = serverErrorMessage(e);
      templatesRetryable = isRetryable(e);
    }
  }

  // ----------------------------------------------------------------- scope

  Future<void> loadChapters() async {
    loadingChapters = true;
    chaptersError = null;
    chaptersRetryable = false;
    _changed();
    try {
      chapters = await api.chapters(subject!, grade!);
    } catch (e) {
      chaptersError = serverErrorMessage(e);
      chaptersRetryable = isRetryable(e);
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
    availabilityRetryable = false;
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

  /// Whether to offer Foundation and Advanced: the server's tier check says a
  /// version could print other questions. Where it cannot, the builder says
  /// why instead (scope_step.dart), and every paper is the Standard one.
  bool get tierChoice => availability?.tiers?.available ?? false;

  void setTier(String t) {
    tier = t;
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
    availabilityRetryable = false;
    _changed();
    try {
      final a = await api.availability(schoolId, t.id,
          chapterIds: chapterIds.toList(), fillFromOutsideScope: fillFromOutsideScope);
      if (ticket != _ticket) return;
      availability = a;
    } catch (e) {
      if (ticket != _ticket) return;
      availabilityError = serverErrorMessage(e);
      availabilityRetryable = isRetryable(e);
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
        teacherSeconds: teacherSeconds,
        tier: tierChoice ? tier : 'standard',
      );
      restartTeacherClock();
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
      generateError = serverErrorMessage(e);
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

  // ------------------------------------------------------------ hand-picked

  /// "Pick the questions yourself": the bank instead of a template, for the
  /// class and subject already chosen.
  Future<void> startHandPicked() async {
    if (grade == null || subject == null) return;
    handPicked = true;
    template = null;
    availability = null;
    generateError = null;
    step = BuilderStep.scope;
    _changed();
    if (chapters.isEmpty) await loadChapters();
  }

  bool isPicked(String id) => picked.any((q) => q.id == id);

  /// Adds [q] to the paper; a question without a verified answer key cannot
  /// be printed (rule Q1), and one already picked is not added twice.
  void addPick(BankItem q) {
    if (!q.hasAnswerKey || isPicked(q.id)) return;
    picked.add(q);
    generateError = null;
    _changed();
  }

  void removePick(String id) {
    picked.removeWhere((q) => q.id == id);
    generateError = null;
    _changed();
  }

  int get pickedMarks => picked.fold(0, (s, q) => s + q.marks);

  bool get canGenerateFromPicked => handPicked && picked.isNotEmpty && !generating;

  /// The paper of exactly [picked], saved like any other. The server groups
  /// the questions into sections by marks; nothing is added or dropped, and
  /// an id it cannot print is refused by name (shown on this step).
  Future<void> generateFromPicked() async {
    if (!canGenerateFromPicked) return;
    generating = true;
    generateError = null;
    _changed();
    try {
      final p = await api.generateFromIds(
        subject: subject!,
        grade: grade!,
        questionIds: [for (final q in picked) q.id],
        title: 'Class $grade $subject test',
        teacherSeconds: teacherSeconds,
      );
      restartTeacherClock();
      _resetPaper();
      result = TemplatePaperResult.ofPaper(p);
      paper = p;
      // What "short" is measured against after a removal: the paper as made.
      _paperSections = [
        for (final s in p.sections)
          TemplateSectionView(
            id: s.sectionId,
            title: 'Section ${s.label} · ${s.name}',
            questionCount: s.questions.length,
            marksEach: s.questions.isEmpty ? 0 : s.questions.first.marks,
          ),
      ];
      setIds = {(p.setLabel ?? 'A'): p.id};
      step = BuilderStep.paper;
    } catch (e) {
      generateError = serverErrorMessage(e);
    } finally {
      generating = false;
      _changed();
    }
  }

  // ------------------------------------------------------------ quick paper

  /// What a quick paper of [totalMarks] at [tier] would hold, from the
  /// server, without saving anything: the marks it makes and, where the bank
  /// cannot make them, the shortfall by section -- shown before the teacher
  /// saves it (audit D57).
  Future<QuickPaperResult> previewQuick({
    required int totalMarks,
    required String tier,
    List<String> chapterIds = const [],
    int setCount = 1,
  }) =>
      api.quickGenerate(
        subject: subject!,
        grade: grade!,
        totalMarks: totalMarks,
        tier: tier,
        chapterIds: chapterIds,
        setCount: setCount,
        preview: true,
      );

  /// Saves the quick paper the preview showed and opens it for review.
  /// Throws (for the dialog to say) when the server refuses.
  Future<void> generateQuick({
    required int totalMarks,
    required String tier,
    List<String> chapterIds = const [],
    int setCount = 1,
  }) async {
    generating = true;
    generateError = null;
    _changed();
    try {
      final r = await api.quickGenerate(
        subject: subject!,
        grade: grade!,
        totalMarks: totalMarks,
        tier: tier,
        chapterIds: chapterIds,
        setCount: setCount,
        teacherSeconds: teacherSeconds,
      );
      restartTeacherClock();
      _resetPaper();
      handPicked = false;
      template = null;
      quickMarksAsked = totalMarks;
      result = TemplatePaperResult.ofPaper(r.paper);
      paper = r.paper;
      _paperSections = [
        for (final s in r.paper.sections)
          TemplateSectionView(
            id: s.sectionId,
            title: 'Section ${s.label} · ${s.name}',
            questionCount: s.questions.length,
            marksEach: s.questions.isEmpty ? 0 : s.questions.first.marks,
          ),
      ];
      setIds = {
        (r.paper.setLabel ?? 'A'): r.paper.id,
        for (final s in r.paper.sets) (s.setLabel ?? s.metadata.setLabel ?? '?'): s.id,
      };
      for (final s in r.paper.sets) {
        _setPapers[s.setLabel ?? '?'] = s;
      }
      step = BuilderStep.paper;
    } finally {
      generating = false;
      _changed();
    }
  }

  GeneratedPaper? get shownPaper => viewingSet == 'A' ? paper : _setPapers[viewingSet];

  int get paperMarks => paper?.sections.fold<int>(0, (s, x) => s + x.totalMarks) ?? 0;
  int get paperQuestions => paper?.sections.fold<int>(0, (s, x) => s + x.questions.length) ?? 0;

  /// Shows another set. A set shown after an edit is fetched fresh rather
  /// than read from the generate response: a removal reaches every set.
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
      setError = serverErrorMessage(e);
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

  /// The key a slot's busy state, error and notes are kept under: the slot
  /// itself on Set A, "B:7" on Set B -- each set has its own question 7.
  String slotKey(String slot) => viewingSet == 'A' ? slot : '$viewingSet:$slot';

  /// The paper id an edit on the set on screen goes to. Sets B and C print
  /// their own questions (the server's `setOverlap` is 0), so each is edited
  /// by its own id; the "Set B is Set A reordered" this replaced was untrue
  /// and left a garbled Set B question with no way to change it (QA P-10).
  String? get _shownId => viewingSet == 'A' ? paper?.id : setIds[viewingSet];

  /// Removes question [slot] (with its OR) or only an alternative
  /// ("7_OR"). The server takes the question in the same place out of every
  /// set, so the sets stay the same paper in shape. The numbers after it
  /// move up, so notes and errors kept under the old numbers are dropped.
  Future<void> remove(String slot) async {
    final shown = shownPaper;
    final id = _shownId;
    final key = slotKey(slot);
    if (shown == null || id == null || busySlots.contains(key)) return;
    final sectionId = shown.sections
        .firstWhere((s) => s.questions.any((q) => '${q.displayNumber}' == slot.split('_').first))
        .sectionId;
    busySlots.add(key);
    slotErrors.remove(key);
    _changed();
    try {
      final r = await api.remove(id, slot);
      _setPapers.clear();
      if (viewingSet == 'A') {
        paper = r.paper;
      } else {
        _setPapers[viewingSet] = r.paper;
        // Set A lost its question in the same place.
        paper = await api.getPaper(paper!.id);
      }
      downloaded.clear();
      slotNotes.clear();
      slotErrors.clear();
      if (!slot.endsWith('_OR')) removedBySection[sectionId] = (removedBySection[sectionId] ?? 0) + 1;
    } catch (e) {
      slotErrors[key] = serverErrorMessage(e);
    } finally {
      busySlots.remove(key);
      _changed();
    }
  }

  Future<void> swap(String slot) => _edit(slot, (id) => api.swap(id, slot));

  Future<void> pick(String slot, String questionId) => _edit(slot, (id) => api.pick(id, slot, questionId));

  Future<void> _edit(String slot, Future<PaperEditResult> Function(String paperId) call) async {
    final id = _shownId;
    final key = slotKey(slot);
    if (paper == null || id == null || busySlots.contains(key)) return;
    busySlots.add(key);
    slotErrors.remove(key);
    _changed();
    try {
      final r = await call(id);
      if (viewingSet == 'A') {
        paper = r.paper;
        // A set that had to repeat the old question changed with it.
        _setPapers.clear();
      } else {
        _setPapers[viewingSet] = r.paper;
      }
      slotNotes[key] = r.notes;
      downloaded.clear();
    } catch (e) {
      slotErrors[key] = serverErrorMessage(e);
    } finally {
      busySlots.remove(key);
      _changed();
    }
  }

  /// Every question id on Set A, ORs included -- what "Make another like
  /// this" asks the server to avoid.
  Set<String> get onPaper => _questionIds(paper);

  /// The same for the set on screen -- what the picker must not offer again.
  Set<String> get onShownPaper => _questionIds(shownPaper);

  static Set<String> _questionIds(GeneratedPaper? p) => {
        for (final s in p?.sections ?? const [])
          for (final GeneratedQuestion q in s.questions) ...[
            q.questionId,
            if (q.internalChoiceQuestionId != null) q.internalChoiceQuestionId!,
          ],
      };

  /// The marks the paper would print with the bank as it stands, against
  /// the template's total -- "58 of 80" -- once the check has run. A section
  /// that cannot be filled prints what it has; "attempt any N" counts N.
  ({int reached, int total})? get marksReach {
    final a = availability, t = template;
    if (a == null || t == null) return null;
    final sections = {for (final (i, s) in t.sections.indexed) s.id.isNotEmpty ? s.id : 's${i + 1}': s};
    var reached = 0;
    for (final s in a.sections) {
      final attempts = sections[s.sectionId]?.attemptCount ?? s.needed;
      reached += (s.filled < attempts ? s.filled : attempts) * s.marksEach;
    }
    return (reached: reached, total: t.totalMarks);
  }

  // --------------------------------------------------------------- finish

  /// Downloads the paper PDF and its answer-key PDF, for every set.
  Future<void> downloadAll() async {
    if (paper == null || downloading) return;
    downloading = true;
    downloadError = null;
    downloadRetryable = false;
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
      downloadError = serverErrorMessage(e);
      downloadRetryable = isRetryable(e);
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
