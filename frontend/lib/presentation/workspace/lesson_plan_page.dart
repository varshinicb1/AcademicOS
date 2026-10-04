import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/readable.dart';
import '../shared/widgets/common_widgets.dart';
import 'notice.dart';
import 'ops_api.dart';
import 'strings.dart';
import '../shared/widgets/shell.dart';

const _base = '/curriculum';

/// The year, its sections and who teaches what: everything the page needs
/// before a section and subject are chosen.
class _PlanSchool {
  final String yearId;
  final List<Map<String, dynamic>> sections;
  final List<Map<String, dynamic>> allocations;
  const _PlanSchool(this.yearId, this.sections, this.allocations);

  Map<String, dynamic> section(String id) => sections.firstWhere((s) => s['id'] == id);

  String sectionLabel(String id) {
    final s = section(id);
    return '${s['gradeNumber']}-${s['name']}';
  }

  Map<String, dynamic>? allocation(String sectionId, String subjectId) =>
      allocations.where((a) => a['sectionId'] == sectionId && a['subjectId'] == subjectId).firstOrNull;
}

/// Lesson plans (SCH-4, audit N-3-1 / N-67-5): a section's dated plan for
/// one subject, made on the web. The section's chosen book and its chapters
/// are shown with which of them can be planned (a chapter needs approved
/// subtopics); "Make the plan" times every subtopic against the year's
/// periods (`teaching-time-estimates`) and then places the lessons on the
/// section's own week (`schedule` with `sectionId`). The result says how
/// many lessons were dated and names everything left without a date, and
/// why. Until this page a school set up on the web had no plan at all, so
/// "Today's lessons", pace and the behind-plan alert were always empty.
/// For the principal and a teacher given the timetable permission.
class LessonPlanPage extends StatefulWidget {
  const LessonPlanPage({super.key});

  @override
  State<LessonPlanPage> createState() => _LessonPlanPageState();
}

class _LessonPlanPageState extends State<LessonPlanPage> {
  late Future<_PlanSchool> _future = _load();
  String? _sectionId;
  String? _subjectId;
  Future<List<Map<String, dynamic>>>? _subjects;

  static Future<_PlanSchool> _load() async {
    final years = await Ops.list('$_base/academic-years', query: {'school_id': CurrentSession.schoolId});
    if (years.isEmpty) throw OpsError(409, tr('Your school has no academic year set up yet.'));
    years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
    final yearId = years.last['id'] as String;
    final sections = await Ops.list('$_base/academic-years/$yearId/sections');
    final allocations = await Ops.list('$_base/academic-years/$yearId/allocations');
    return _PlanSchool(yearId, sections, allocations);
  }

  void _pickSection(_PlanSchool school, String? id) => setState(() {
        _sectionId = id;
        _subjectId = null;
        _subjects = id == null ? null : Ops.list('$_base/grades/${school.section(id)['gradeId']}/subjects');
      });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Lesson plans'))),
      body: FutureBuilder<_PlanSchool>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = _load(); }));
          }
          final school = snap.data!;
          if (school.sections.isEmpty) {
            return EmptyState(icon: Icons.menu_book_outlined, title: tr('No sections yet'),
                message: tr('Set up the classes and their sections first.'));
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text(tr('A dated plan for one section and subject: every approved subtopic of the book is given its '
                'share of the year\'s periods, then placed on the section\'s own timetable.'),
                style: Theme.of(context).textTheme.bodySmall),
            const Gap(12),
            DropdownButtonFormField<String>(
              key: const ValueKey('plan-section'),
              initialValue: _sectionId,
              isExpanded: true,
              decoration: InputDecoration(labelText: tr('Section')),
              items: [
                for (final s in school.sections)
                  DropdownMenuItem(value: s['id'] as String, child: Text(school.sectionLabel(s['id'] as String))),
              ],
              onChanged: (id) => _pickSection(school, id),
            ),
            const Gap(12),
            if (_subjects != null)
              FutureBuilder<List<Map<String, dynamic>>>(
                key: ValueKey('plan-subjects-$_sectionId'),
                future: _subjects,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
                  if (snap.hasError) {
                    return Notice(kind: NoticeKind.danger, title: serverErrorMessage(snap.error!));
                  }
                  final subjects = snap.data!;
                  if (subjects.isEmpty) return Text(tr('This class has no subjects yet.'));
                  String label(Map<String, dynamic> subj) {
                    final a = school.allocation(_sectionId!, subj['id'] as String);
                    return a == null
                        ? '${subj['name']} · ${tr('no periods set')}'
                        : '${subj['name']} · ${a['periodsPerWeek']} ${tr('a week')}';
                  }
                  return DropdownButtonFormField<String>(
                    key: ValueKey('plan-subject-$_sectionId'),
                    initialValue: _subjectId,
                    isExpanded: true,
                    decoration: InputDecoration(labelText: tr('Subject')),
                    items: [
                      for (final subj in subjects)
                        DropdownMenuItem(value: subj['id'] as String, child: Text(label(subj))),
                    ],
                    onChanged: (id) => setState(() => _subjectId = id),
                  );
                },
              ),
            if (_sectionId != null && _subjectId != null) ...[
              const Gap(16),
              _PlanPanel(
                key: ValueKey('plan-$_sectionId-$_subjectId'),
                yearId: school.yearId,
                sectionId: _sectionId!,
                sectionLabel: school.sectionLabel(_sectionId!),
                subjectId: _subjectId!,
                allocation: school.allocation(_sectionId!, _subjectId!),
              ),
            ],
            // N-67-5: or every section at once.
            if (CurrentSession.role == 'principal') ...[
              const Gap(24),
              _PlanAll(yearId: school.yearId),
            ],
          ]);
        },
      ),
    );
  }
}

/// The chosen book, its chapters, and the plan the section has now.
class _BookView {
  final Map<String, dynamic>? book;
  final List<({Map<String, dynamic> chapter, List<Map<String, dynamic>> topics})> chapters;
  final List<Map<String, dynamic>> lessons;
  const _BookView(this.book, this.chapters, this.lessons);

  static int subtopicCount(List<Map<String, dynamic>> topics) =>
      topics.fold(0, (n, t) => n + ((t['subtopics'] as List?)?.length ?? 0));

  int get readyChapters => chapters.where((c) => subtopicCount(c.topics) > 0).length;

  /// Subtopic id -> "Chapter: subtopic", to name what the plan left undated.
  Map<String, String> get subtopicNames => {
        for (final c in chapters)
          for (final t in c.topics)
            for (final st in (t['subtopics'] as List? ?? const []).cast<Map>())
              st['id'] as String: '${c.chapter['name']}: ${st['name']}',
      };
}

class _PlanPanel extends StatefulWidget {
  final String yearId;
  final String sectionId;
  final String sectionLabel;
  final String subjectId;
  final Map<String, dynamic>? allocation;

  const _PlanPanel({
    super.key,
    required this.yearId,
    required this.sectionId,
    required this.sectionLabel,
    required this.subjectId,
    required this.allocation,
  });

  @override
  State<_PlanPanel> createState() => _PlanPanelState();
}

class _PlanPanelState extends State<_PlanPanel> {
  late Future<_BookView> _future = _loadBook();
  bool _busy = false;
  // D35: fit what is left to teach into the periods left.
  bool _fit = false;
  String? _step;
  String? _error;
  Map<String, dynamic>? _estimates;
  Map<String, dynamic>? _plan;

  Future<_BookView> _loadBook() async {
    final Map<String, dynamic> book;
    try {
      book = await Ops.map('$_base/subjects/${widget.subjectId}/selected-book');
    } on OpsError catch (e) {
      // 404: no edition chosen yet -- a fact about the school, said on the page.
      if (e.status == 404) return const _BookView(null, [], []);
      rethrow;
    }
    final bookId = book['id'] as String;
    final chapters = await Ops.list('$_base/books/$bookId/chapters');
    final topics = await Future.wait([for (final c in chapters) Ops.list('$_base/chapters/${c['id']}/topics')]);
    final lessons = await Ops.list('$_base/books/$bookId/schedule',
        query: {'academic_year_id': widget.yearId, 'sectionId': widget.sectionId});
    return _BookView(book, [
      for (var i = 0; i < chapters.length; i++) (chapter: chapters[i], topics: topics[i]),
    ], lessons);
  }

  bool get _isPrincipal => CurrentSession.role == 'principal';

  /// The principal's own click approves the topics proposed from the book's headings, chapter by
  /// chapter, for the chapters that have none approved. It used to be a step on another tab of the
  /// admin console, and a school that had not found it saw a page that could not plan anything.
  /// Returns the book as it is afterwards, or null if it failed (the error is on the page).
  Future<_BookView?> _approveTopics(_BookView view) async {
    final todo = [
      for (final c in view.chapters)
        if (_BookView.subtopicCount(c.topics) == 0) c.chapter['id'] as String,
    ];
    setState(() {
      _busy = true;
      _error = null;
      _step = tr("Approving the book's proposed topics...");
    });
    try {
      for (final id in todo) {
        await Ops.post('$_base/chapters/$id/topics/approve-all');
        if (!mounted) return null;
      }
      final fresh = await _loadBook();
      if (!mounted) return null;
      setState(() {
        _future = Future.value(fresh);
      });
      return fresh;
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
      return null;
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _step = null;
        });
      }
    }
  }

  Future<void> _approveAndMake(_BookView view) async {
    final fresh = await _approveTopics(view);
    if (fresh != null && fresh.readyChapters > 0 && mounted) await _make(fresh);
  }

  Future<void> _make(_BookView view) async {
    final bookId = view.book!['id'] as String;
    final query = {'academic_year_id': widget.yearId};
    setState(() {
      _busy = true;
      _error = null;
      _estimates = null;
      _plan = null;
      _step = tr('Timing each subtopic against the year\'s periods...');
    });
    try {
      // Sized from this section's own week (N-3-8), not the school-wide slots.
      final estimates = await Ops.post('$_base/books/$bookId/teaching-time-estimates', query: query,
          body: {'periodsPerWeek': widget.allocation!['periodsPerWeek'], 'sectionId': widget.sectionId});
      if (!mounted) return;
      setState(() {
        _estimates = Map<String, dynamic>.from(estimates as Map);
        _step = tr('Placing the lessons on the section\'s week...');
      });
      final plan = await Ops.post('$_base/books/$bookId/schedule', query: query,
          body: {'sectionId': widget.sectionId, 'force': view.lessons.isNotEmpty, if (_fit) 'fitToPeriodsLeft': true});
      if (!mounted) return;
      setState(() {
        _plan = Map<String, dynamic>.from(plan as Map);
        _future = _loadBook();
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<_BookView>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
        if (snap.hasError) {
          return Notice(kind: NoticeKind.danger, title: serverErrorMessage(snap.error!),
              action: OutlinedButton(onPressed: () => setState(() { _future = _loadBook(); }),
                  child: Text(tr('Try again'))));
        }
        final view = snap.data!;
        final book = view.book;
        if (book == null) {
          return Notice(
            key: const ValueKey('plan-no-book'),
            kind: NoticeKind.warning,
            title: tr('This subject has no chosen book yet.'),
            lines: [tr('Choose its edition under Book editions on the admin console\'s Roster tab, then come back.')],
            action: CurrentSession.role == 'principal'
                ? TextButton(onPressed: () => context.push('/admin'), child: Text(tr('Open the admin console')))
                : null,
          );
        }
        final alloc = widget.allocation;
        final ready = view.readyChapters;
        final notReady = view.chapters.where((c) => _BookView.subtopicCount(c.topics) == 0).toList();
        final lessons = view.lessons;
        final taught = lessons.where((l) => l['status'] == 'completed').length;
        final skipped = lessons.where((l) => l['status'] == 'skipped').length;
        final dated = lessons.where((l) => l['status'] != 'unscheduled').map((l) => l['date'] as String).toList()..sort();
        // A principal can approve the book's proposed topics from here, so a book with none approved
        // is a step away from a plan, not a dead end.
        final needsApproval = notReady.isNotEmpty && _isPrincipal;
        final canMake = !_busy && alloc != null && (ready > 0 || needsApproval);
        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          AppCard(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(bookName(book['title'] as String), style: theme.textTheme.titleSmall),
              if (book['publisher'] != null) Text(book['publisher'] as String, style: theme.textTheme.bodySmall),
              const Gap(8),
              Text(key: const ValueKey('plan-current'),
                  lessons.isEmpty
                      ? '${widget.sectionLabel}: ${tr('no plan yet.')}'
                      : '${widget.sectionLabel}: ${lessons.length} ${tr('lessons')}'
                          '${dated.isEmpty ? '' : ', ${dated.first} ${tr('to')} ${dated.last}'}'
                          ' · $taught ${tr('taught')} · $skipped ${tr('not taught')}'),
              Text(alloc == null
                  ? tr('No periods a week set for this subject in this section.')
                  : '${alloc['periodsPerWeek']} ${tr('periods a week, from the allocation')}',
                  style: theme.textTheme.bodySmall),
            ]),
          ),
          if (alloc == null) ...[
            Notice(kind: NoticeKind.warning, title: tr('Set who teaches it and how many periods a week first.'),
                lines: [tr('On the Timetable page, Allocations tab. The plan is sized from that number.')]),
            const Gap(12),
          ],
          Text('${tr('Chapters')} ($ready ${tr('of')} ${view.chapters.length} ${tr('ready to plan')})',
              style: theme.textTheme.titleSmall),
          const Gap(4),
          if (view.chapters.isEmpty) Text(tr('This book has no chapters yet.')),
          for (final c in view.chapters)
            _ChapterRow(name: c.chapter['name'] as String, topics: c.topics),
          if (notReady.isNotEmpty) ...[
            const Gap(8),
            Notice(
              key: const ValueKey('plan-topics-waiting'),
              kind: NoticeKind.info,
              title: '${notReady.length} ${tr("chapters have topics waiting to be approved.")}',
              lines: [
                _isPrincipal
                    ? tr("They come from the book's own headings. Approving them lets those chapters be dated.")
                    : tr('Your principal approves the book\'s topics. Until then these chapters are left out of the plan.'),
              ],
              action: _isPrincipal
                  ? OutlinedButton(
                      key: const ValueKey('plan-approve-topics'),
                      onPressed: _busy ? null : () => _approveTopics(view),
                      child: Text(tr('Approve their topics')),
                    )
                  : null,
            ),
          ],
          const Gap(16),
          if (lessons.isNotEmpty) ...[
            Text(tr('Making the plan again keeps every lesson marked taught or not taught, and every day that has passed; '
                'only what is still to be taught is placed again.'), style: theme.textTheme.bodySmall),
            const Gap(8),
          ],
          CheckboxListTile(
            key: const ValueKey('plan-fit'),
            contentPadding: EdgeInsets.zero,
            value: _fit,
            onChanged: _busy ? null : (v) => setState(() => _fit = v ?? false),
            title: Text(tr('Fit the syllabus into the periods left')),
            subtitle: Text(tr('If the year has fewer periods left than the subtopics need, each gets proportionally '
                "fewer (at least one), so every subtopic is dated. The book's estimates are not changed.")),
          ),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton(
              key: const ValueKey('plan-make'),
              onPressed: !canMake ? null : (ready == 0 ? () => _approveAndMake(view) : () => _make(view)),
              style: phoneTapTarget(context),
              child: Text(ready == 0 && needsApproval
                  ? tr('Approve the topics and make the plan')
                  : lessons.isEmpty ? tr('Make the plan') : tr('Make the plan again')),
            ),
          ),
          if (_busy) ...[
            const Gap(12),
            const LinearProgressIndicator(),
            if (_step != null) ...[const Gap(4), Text(_step!, style: theme.textTheme.bodySmall)],
          ],
          if (_error != null) ...[
            const Gap(12),
            Notice(key: const ValueKey('plan-error'), kind: NoticeKind.danger,
                title: tr('The plan was not made.'), lines: [_error!]),
          ],
          if (_plan != null) ...[
            const Gap(12),
            _PlanResult(plan: _plan!, estimates: _estimates, names: view.subtopicNames),
          ],
        ]);
      },
    );
  }
}

class _ChapterRow extends StatelessWidget {
  final String name;
  final List<Map<String, dynamic>> topics;
  const _ChapterRow({required this.name, required this.topics});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final subtopics = _BookView.subtopicCount(topics);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: Text(name, style: theme.textTheme.bodyMedium)),
        const Gap(12),
        Text(
          subtopics == 0
              ? tr('topics not approved yet')
              : '${topics.length} ${tr('topics')} · $subtopics ${tr('subtopics')}',
          style: theme.textTheme.bodySmall?.copyWith(
              color: subtopics == 0 ? theme.colorScheme.onSurfaceVariant : null),
        ),
      ]),
    );
  }
}

/// What "Make the plan" did: the lessons dated, what was kept, and every
/// subtopic left without a date -- by name, with the reason.
class _PlanResult extends StatelessWidget {
  final Map<String, dynamic> plan;
  final Map<String, dynamic>? estimates;
  final Map<String, String> names;
  const _PlanResult({required this.plan, required this.estimates, required this.names});

  List<String> _named(String field) =>
      [for (final id in (plan[field] as List? ?? const [])) names[id] ?? '$id'];

  @override
  Widget build(BuildContext context) {
    final created = plan['lessonsCreated'] as int? ?? 0;
    final first = plan['firstScheduledDate'] as String?;
    final last = plan['lastScheduledDate'] as String?;
    final kept = (plan['lessonsKept'] as int? ?? 0);
    final past = (plan['pastLessonsKept'] as int? ?? 0);
    final all = plan['allSubtopicsScheduled'] != false;
    final unscheduled = _named('subtopicsUnscheduled');
    final partly = _named('subtopicsPartiallyScheduled');
    final noEstimate = _named('subtopicsWithoutEstimate');
    final leftOut = [for (final c in (plan['chaptersWithoutSubtopics'] as List? ?? const [])) '$c'];
    final skippedUnits = [for (final u in (estimates?['unitsSkippedNoSubtopics'] as List? ?? const [])) '$u'];
    final short = estimates?['periodsShort'] as int? ?? 0;
    final compressed = [
      for (final c in (plan['subtopicsCompressed'] as List? ?? const []).cast<Map>())
        '${names[c['subtopicId']] ?? c['subtopicId']}: ${c['periodsNeeded']} → ${c['periodsPlanned']} ${tr('periods')}',
    ];
    return Column(key: const ValueKey('plan-result'), crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Notice(
        kind: all ? NoticeKind.success : NoticeKind.warning,
        title: '$created ${tr('lessons dated')}'
            '${first == null ? '' : ', $first ${tr('to')} $last'}.',
        lines: [
          '${plan['subtopicsScheduled']} ${tr('subtopics have all their periods.')}',
          if (kept > 0) '$kept ${tr('lessons already marked taught or not taught were kept.')}',
          if (past > 0) '$past ${tr('lessons on days that have passed were kept.')}',
          if (plan['warning'] != null) plan['warning'] as String,
        ],
      ),
      // D119: a chapter with no approved subtopic is not in the plan at all.
      if (leftOut.isNotEmpty) ...[
        const Gap(8),
        Notice(key: const ValueKey('plan-chapters-left-out'), kind: NoticeKind.warning,
            title: '${leftOut.length} ${tr('chapters are not in the plan: they have no approved subtopics.')}',
            lines: firstFew(leftOut)),
      ],
      if (unscheduled.isNotEmpty) ...[
        const Gap(8),
        Notice(kind: NoticeKind.warning,
            title: '${unscheduled.length} ${tr('subtopics have no date: the year ran out of periods for this subject.')}',
            lines: firstFew(unscheduled)),
      ],
      if (partly.isNotEmpty) ...[
        const Gap(8),
        Notice(kind: NoticeKind.warning,
            title: '${partly.length} ${tr('subtopics got only some of their periods before the year ends.')}',
            lines: firstFew(partly)),
      ],
      if (noEstimate.isNotEmpty) ...[
        const Gap(8),
        Notice(kind: NoticeKind.warning,
            title: '${noEstimate.length} ${tr('subtopics have no time estimate, so they were not placed.')}',
            lines: firstFew(noEstimate)),
      ],
      if (skippedUnits.isNotEmpty) ...[
        const Gap(8),
        Notice(kind: NoticeKind.info,
            title: tr('Units with no approved subtopics were left out of the plan:'),
            lines: firstFew(skippedUnits)),
      ],
      // D35: what fitting the plan into the periods left took away.
      if (plan['fitNote'] != null) ...[
        const Gap(8),
        Notice(key: const ValueKey('plan-fitted'), kind: NoticeKind.info,
            title: '${tr('Fitted to the periods left')}: ${plan['fitNote']}.',
            lines: firstFew(compressed)),
      ],
      if (short > 0) ...[
        const Gap(8),
        Notice(kind: NoticeKind.info,
            title: '${tr('The subtopics need')} ${estimates!['periodsAllocated']} ${tr('periods; the year has')} '
                '${estimates!['totalSubjectPeriods']}.'),
      ],
    ]);
  }
}

/// Every section's plan in one action (N-67-5), for the principal: the
/// topics proposed when the school was seeded are approved (only with the
/// box ticked -- it is the principal's approval), each book is timed against
/// the year, and each section's lessons are laid on its own week.
class _PlanAll extends StatefulWidget {
  final String yearId;
  const _PlanAll({required this.yearId});

  @override
  State<_PlanAll> createState() => _PlanAllState();
}

class _PlanAllState extends State<_PlanAll> {
  bool _approve = true;
  bool _fit = false;      // D35
  bool _busy = false;
  Map<String, dynamic>? _result;
  String? _error;
  // Whether the result in hand was asked for with the box ticked: what to do
  // about a plan with no lessons depends on it.
  bool _approveAsked = true;

  Future<void> _run() async {
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
      _approveAsked = _approve;
    });
    try {
      final r = await Ops.post('$_base/academic-years/${widget.yearId}/lesson-plans',
          body: {'approveProposedTopics': _approveAsked, if (_fit) 'fitToPeriodsLeft': true});
      if (mounted) setState(() => _result = Map<String, dynamic>.from(r as Map));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = _result;
    final plans = ((r?['plans'] as List?) ?? const []).cast<Map>();
    final missed = ((r?['notPlanned'] as List?) ?? const []).cast<String>();
    final lessons = plans.fold<int>(0, (n, p) => n + (p['lessonsCreated'] as int? ?? 0));
    // A plan with no lessons, and why. "7 plans made, 0 lessons dated" with
    // the approve box unticked said neither (QA S-14, 2026-10-01): a plan with
    // no lesson, no warning and no subtopic waiting for an estimate is a book
    // with no approved topics.
    String label(Map p) => '${p['sectionName']} ${p['subjectName']}';
    final empty = [for (final p in plans) if ((p['lessonsCreated'] as int? ?? 0) == 0) p];
    final noTopics = [
      for (final p in empty)
        if (p['warning'] == null && (p['subtopicsWithoutEstimate'] as int? ?? 0) == 0) label(p)
    ];
    final otherEmpty = [
      for (final p in empty)
        if (p['warning'] != null || (p['subtopicsWithoutEstimate'] as int? ?? 0) > 0)
          '${label(p)}: ${p['warning'] ?? '${p['subtopicsWithoutEstimate']} '
              '${tr('subtopics have no time estimate, so they were not placed.')}'}'
    ];
    return AppCard(
      key: const ValueKey('plan-all'),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(tr('Plan every section'), style: theme.textTheme.titleSmall),
        Text(tr('Every section and subject with periods a week gets its dated plan from its book.'),
            style: theme.textTheme.bodySmall),
        CheckboxListTile(
          key: const ValueKey('plan-all-approve'),
          contentPadding: EdgeInsets.zero,
          value: _approve,
          onChanged: _busy ? null : (v) => setState(() => _approve = v ?? false),
          title: Text(tr("Approve the topics proposed for each chapter (from the NCERT book's own headings)")),
        ),
        CheckboxListTile(
          key: const ValueKey('plan-all-fit'),
          contentPadding: EdgeInsets.zero,
          value: _fit,
          onChanged: _busy ? null : (v) => setState(() => _fit = v ?? false),
          title: Text(tr('Fit each syllabus into the periods left (fewer periods per subtopic, at least one)')),
        ),
        FilledButton(
          key: const ValueKey('plan-all-run'),
          onPressed: _busy ? null : _run,
          style: phoneTapTarget(context),
          child: Text(tr('Plan every section')),
        ),
        if (_busy) ...[const Gap(8), const LinearProgressIndicator()],
        if (_error != null) ...[
          const Gap(8),
          Notice(kind: NoticeKind.danger, title: tr('The plans were not made.'), lines: [_error!]),
        ],
        if (r != null) ...[
          const Gap(8),
          Text(key: const ValueKey('plan-all-result'),
              '${plans.length} ${tr('plans made')}, $lessons ${tr('lessons dated')}'
              '${(r['subtopicsCreated'] as int? ?? 0) > 0 ? ' · ${r['subtopicsCreated']} ${tr('subtopics approved')}' : ''}'),
          for (final m in missed) Text('• $m', style: theme.textTheme.bodySmall),
          // D119: each plan names the chapters it left out (no approved subtopics).
          for (final p in plans)
            if ((p['chaptersWithoutSubtopics'] as List? ?? const []).isNotEmpty)
              Text(key: ValueKey('plan-all-left-out-${p['sectionId']}-${p['subjectName']}'),
                  '• ${p['sectionName']} ${p['subjectName']}: '
                  '${(p['chaptersWithoutSubtopics'] as List).length} ${tr('chapters not in the plan (no approved subtopics)')}: '
                  '${firstFew([for (final c in p['chaptersWithoutSubtopics'] as List) '$c']).join(', ')}',
                  style: theme.textTheme.bodySmall),
          // D35: each fitted plan says what fitting it took away.
          for (final p in plans)
            if (p['fitNote'] != null)
              Text(key: ValueKey('plan-all-fitted-${p['sectionId']}-${p['subjectName']}'),
                  '• ${p['sectionName']} ${p['subjectName']}: ${p['fitNote']}',
                  style: theme.textTheme.bodySmall),
          if (noTopics.isNotEmpty) ...[
            const Gap(8),
            Notice(
              key: const ValueKey('plan-all-no-topics'),
              kind: NoticeKind.warning,
              title: noTopics.length == plans.length
                  ? tr('No lesson was dated: the books have no approved topics yet.')
                  : noTopics.length == 1
                      ? tr('1 plan has no lessons: its book has no approved topics yet.')
                      : '${noTopics.length} ${tr('plans have no lessons: their books have no approved topics yet.')}',
              lines: [
                _approveAsked
                    ? tr('No proposed topics were waiting on these books. Add or approve their topics under Proposed '
                        'topics, on the admin console\'s Sequence Reorder tab, then plan again.')
                    : tr('Tick "Approve the topics proposed for each chapter" above and press Plan every section '
                        'again.'),
                ...firstFew(noTopics),
              ],
            ),
          ],
          if (otherEmpty.isNotEmpty) ...[
            const Gap(8),
            Notice(
              kind: NoticeKind.warning,
              title: otherEmpty.length == 1
                  ? tr('1 plan has no lessons:')
                  : '${otherEmpty.length} ${tr('plans have no lessons:')}',
              lines: firstFew(otherEmpty),
            ),
          ],
        ],
      ]),
    );
  }
}
