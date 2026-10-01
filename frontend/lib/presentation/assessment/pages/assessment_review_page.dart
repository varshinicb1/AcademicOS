import 'dart:io';

import 'package:flutter/foundation.dart' show ValueListenable;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:get_it/get_it.dart';

import '../../../core/constants/wording.dart';
import '../../../core/download/paper_download.dart';
import '../../../core/download/pdf_saver.dart';
import '../../../core/local_engine/local_api_client.dart' show AssessmentLockedException;
import '../../../data/datasources/api/api_client.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';
import '../../paper_builder/widgets/bank_picker.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import '../widgets/paper_actions.dart';
import '../widgets/paper_delivery_sheet.dart';
import 'package:academicos/core/theme/app_theme.dart';

/// A saved paper: its questions set by set, what can still be changed on it
/// (until it is approved, by whoever may change it -- [PaperPermissions]),
/// its downloads, and the review and approval that lock it.
class AssessmentReviewPage extends StatefulWidget {
  final String assessmentId;
  final Assessment? assessment;
  final GeneratedPaper? paper;
  final List<String> gaps;
  final List<String> warnings;

  const AssessmentReviewPage({
    super.key,
    required this.assessmentId,
    this.assessment,
    this.paper,
    this.gaps = const [],
    this.warnings = const [],
  });

  @override
  State<AssessmentReviewPage> createState() => _AssessmentReviewPageState();
}

/// What a download fetches.
enum _Export { paper, answerKey, docx }

class _AssessmentReviewPageState extends State<AssessmentReviewPage> {
  final Set<_Export> _exporting = {};
  String? _error;
  int _selectedSetIndex = 0;

  Assessment? _fetchedAssessment;
  GeneratedPaper? _fetchedPaper;
  bool _reopening = false;
  String? _reopenError;

  // What this page changed since it was opened: a rename, a review request
  // or an approval (the assessment), and any question edit (the paper,
  // read back whole). They win over what the page was opened with -- the
  // chip said "Ready" and "In review" after the server had moved on (QA
  // P-12, P-23).
  Assessment? _changedAssessment;
  GeneratedPaper? _editedPaper;

  bool _approving = false;
  String? _approveError;

  // Similar-question pairs (Task 906). The server prints two hand-picked
  // questions that look alike instead of refusing them, and names each pair
  // on the paper it returns (GeneratedPaper.similarPairs). The teacher
  // decides: "Keep both" hides the pair, "Swap one" asks the server for the
  // next best question in the later one's slot.
  final Set<int> _keptPairs = {};
  int? _swappingPair;
  String? _swapError;
  int? _swapErrorPair;

  // Question edits on the saved paper, keyed "<set>:<slot>" ("B:7_OR").
  final Set<String> _busySlots = {};
  final Map<String, String> _slotErrors = {};
  final Map<String, List<String>> _slotNotes = {};

  // Exported files, by "<paper id>:<kind>": the delivery sheet previews the
  // offline build's local copy instead of asking a server it has not got.
  final Map<String, String> _exported = {};

  late final ValueListenable<Set<String>> _grants = myGrants();

  GeneratedPaper? get _paper => _editedPaper ?? widget.paper ?? _fetchedPaper;
  Assessment? get _assessment => _changedAssessment ?? _fetchedAssessment ?? widget.assessment;

  @override
  void initState() {
    super.initState();
    _grants.addListener(_grantsChanged);
    if (widget.assessment == null || widget.paper == null) {
      _reopen();
    }
  }

  @override
  void dispose() {
    _grants.removeListener(_grantsChanged);
    super.dispose();
  }

  void _grantsChanged() {
    if (mounted) setState(() {});
  }

  // Router `extra` (widget.assessment/widget.paper) only survives while the
  // in-memory object from the generation flow is still around — reopening an
  // assessment from the list later, or after a reload, arrives with neither.
  // Assessment.generatedPaperId is what links the two back together.
  Future<void> _reopen() async {
    setState(() {
      _reopening = true;
      _reopenError = null;
    });
    try {
      final api = GetIt.I<ApiClient>();
      final assessment = await api.getAssessment(widget.assessmentId);
      final paperId = assessment.generatedPaperId;
      if (paperId == null || paperId.isEmpty) {
        throw Exception('This assessment has no generated paper yet.');
      }
      final paper = await api.getPaper(paperId);
      if (!mounted) return;
      setState(() {
        _fetchedAssessment = assessment;
        _fetchedPaper = paper;
        _reopening = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _reopenError = serverErrorMessage(e);
        _reopening = false;
      });
    }
  }

  PaperPermissions _permissions(Assessment a) => PaperPermissions.of(a, grants: _grants.value);

  /// Swap, pick and remove need the server's template API, which the offline
  /// build does not have; there they are not offered at all.
  bool _canEditQuestions(Assessment a) =>
      !PaperPermissions.onDevice &&
      GetIt.I.isRegistered<PaperBuilderApi>() &&
      paperIsEditable(a) &&
      _permissions(a).mayChange;

  @override
  Widget build(BuildContext context) {
    final assessment = _assessment;
    final paper = _paper;
    final activePaper = (paper != null && paper.sets.isNotEmpty && _selectedSetIndex >= 0 && _selectedSetIndex < paper.sets.length)
        ? paper.sets[_selectedSetIndex]
        : paper;

    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: Text(assessment?.title ?? 'Paper'),
        actions: [if (assessment != null) _menu(context, assessment, paper)],
      ),
      body: _reopening
          ? const Center(child: CircularProgressIndicator())
          : assessment == null || paper == null || activePaper == null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          _reopenError ?? 'This assessment could not be opened.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: _reopen,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildSummaryCard(context, assessment, activePaper),
                    if (paper.sets.length > 1) _buildSetSwitcher(paper),
                    if (paperIsEditable(assessment) && _permissions(assessment).mayChange)
                      ..._buildSimilarPairCards(context, paper),
                    if (widget.gaps.isNotEmpty) _buildIssuesCard(context, 'Coverage gaps', widget.gaps, AppColors.warning),
                    if (widget.warnings.isNotEmpty) _buildIssuesCard(context, 'Warnings', widget.warnings, AppColors.danger),
                    const SizedBox(height: 8),
                    for (final section in activePaper.sections)
                      _buildSectionCard(context, assessment, paper, activePaper, section),
                    const SizedBox(height: 16),
                    _buildExportCard(context, assessment, paper, activePaper),
                  ],
                ),
    );
  }

  /// The ⋮ menu: only what this person may do with this paper now.
  Widget _menu(BuildContext context, Assessment assessment, GeneratedPaper? paper) {
    const offline = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
    final can = _permissions(assessment);
    final editable = paperIsEditable(assessment);
    final items = <PopupMenuEntry<String>>[
      if (editable && can.mayChange) const PopupMenuItem(value: 'rename', child: Text('Rename')),
      // Review and marks entry are school workflows on the web build only.
      if (!offline && editable && can.mayAskForReview && assessment.status != AssessmentStatus.underReview)
        const PopupMenuItem(value: 'review', child: Text('Send for review')),
      if (!offline && paper != null) const PopupMenuItem(value: 'marks', child: Text('Enter marks')),
      if (can.mayDelete) const PopupMenuItem(value: 'delete', child: Text('Delete')),
    ];
    if (items.isEmpty) return const SizedBox.shrink();
    return PopupMenuButton<String>(
      tooltip: 'More actions',
      onSelected: (v) async {
        switch (v) {
          case 'rename':
            final renamed = await renamePaper(context, assessment);
            if (renamed != null && mounted) setState(() => _changedAssessment = renamed);
          case 'review':
            await _askForReview(assessment);
          case 'marks':
            context.push('/school/marks/${paper!.id}', extra: {'grade': paper.metadata.grade});
          case 'delete':
            if (await deletePaper(context, assessment) && context.mounted) {
              if (Navigator.of(context).canPop()) {
                Navigator.of(context).pop();
              } else {
                GoRouter.maybeOf(context)?.go('/assessment');
              }
            }
        }
      },
      itemBuilder: (_) => items,
    );
  }

  Future<void> _askForReview(Assessment assessment) async {
    if (await requestReview(context, assessment.id, authorId: assessment.teacherId) && mounted) {
      // The server moved it to "underReview"; say so here as well (QA P-23).
      setState(() => _changedAssessment =
          assessment.copyWith(status: AssessmentStatus.underReview, updatedAt: DateTime.now()));
    }
  }

  static String _setLabel(GeneratedPaper paper, int i) =>
      paper.sets[i].setLabel ?? String.fromCharCode(65 + i);

  /// The label of the set on screen, or null for a paper with one set.
  String? _activeSetLabel(GeneratedPaper paper) => paper.sets.length > 1
      ? _setLabel(paper, _selectedSetIndex.clamp(0, paper.sets.length - 1))
      : null;

  Widget _buildSetSwitcher(GeneratedPaper paper) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.copy_all, size: 20),
                const SizedBox(width: 8),
                // Expanded so the heading wraps: unbounded, it ran 156 px off
                // a 375 px phone's card (Task 801).
                Expanded(
                  child: Text('${paper.sets.length} sets',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                ),
              ],
            ),
            const SizedBox(height: 4),
            // Plain and true: each set has its own questions, so their
            // difficulty and competency share can differ (QA P-32).
            Text('Each set prints its own questions in the same sections and marks. '
                'Choose a set to read it, change it or download it.',
                key: const ValueKey('sets-explained'),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
            const SizedBox(height: 10),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: SegmentedButton<int>(
                segments: [
                  for (var i = 0; i < paper.sets.length; i++)
                    ButtonSegment<int>(value: i, label: Text('Set ${_setLabel(paper, i)}')),
                ],
                selected: {_selectedSetIndex.clamp(0, paper.sets.length - 1)},
                onSelectionChanged: (set) => setState(() => _selectedSetIndex = set.first),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static int _marksOf(GeneratedPaper p) => p.sections.fold<int>(0, (s, x) => s + x.totalMarks);

  Widget _buildSummaryCard(BuildContext context, Assessment assessment, GeneratedPaper paper) {
    final set = _paper == null ? null : _activeSetLabel(_paper!);
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(assessment.title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
              ),
              if (set != null) ...[
                ChipTag(label: 'SET $set', color: Theme.of(context).colorScheme.tertiaryContainer),
                const SizedBox(width: 8),
              ],
              ChipTag(key: const ValueKey('paper-status'), label: assessment.status.label),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(spacing: 16, runSpacing: 4, children: [
            Text('${paper.metadata.subject} · Class ${paper.metadata.grade}'),
            // What is printed: a removed question takes its marks with it.
            Text(marksText(_marksOf(paper)), key: const ValueKey('paper-marks')),
            Text('${paper.metadata.durationMinutes} minutes'),
            if (paper.metadata.tier != null)
              Text('Tier: ${paper.metadata.tier!.toUpperCase()}'),
          ]),
        ],
      ),
    );
  }

  /// The printed slot of [questionId] on [paper] -- "7", or "7_OR" for an OR
  /// alternative, the key POST /papers/{id}/questions/{slot}/swap takes --
  /// or null once it is no longer on the paper (a swap took it off).
  static String? _slotOf(GeneratedPaper paper, String questionId) {
    for (final section in paper.sections) {
      for (final q in section.questions) {
        if (q.questionId == questionId) return '${q.displayNumber}';
        if (q.internalChoiceQuestionId == questionId) return '${q.displayNumber}_OR';
      }
    }
    return null;
  }

  static String _slotLabel(String slot) =>
      slot.endsWith('_OR') ? '${slot.substring(0, slot.length - 3)} (OR)' : slot;

  /// One card per similar pair still on the paper. The pairs come from the
  /// paper generation returned (a paper read back later carries none), and
  /// a pair drops out once the teacher keeps both or either question is
  /// swapped off the paper.
  List<Widget> _buildSimilarPairCards(BuildContext context, GeneratedPaper paper) {
    final original = widget.paper;
    if (original == null) return const [];
    final cards = <Widget>[];
    for (var i = 0; i < original.similarPairs.length; i++) {
      final pair = original.similarPairs[i];
      if (pair.length != 2 || _keptPairs.contains(i)) continue;
      final first = _slotOf(paper, pair[0]);
      final second = _slotOf(paper, pair[1]);
      if (first == null || second == null) continue;
      cards.add(_buildSimilarPairCard(context, paper, i, first, second,
          i < original.warnings.length ? original.warnings[i] : null));
    }
    return cards;
  }

  Widget _buildSimilarPairCard(BuildContext context, GeneratedPaper paper, int index,
      String first, String second, String? serverWarning) {
    const color = AppColors.warning;
    final busy = _swappingPair == index;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        color: color.withValues(alpha: 0.08),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Similar questions', style: TextStyle(fontWeight: FontWeight.w600, color: color)),
            const SizedBox(height: 6),
            Text('Questions ${_slotLabel(first)} and ${_slotLabel(second)} look like the same question. '
                'Keep both if you meant to set them, or swap ${_slotLabel(second)} for another question.'),
            if (serverWarning != null) ...[
              const SizedBox(height: 4),
              Text(serverWarning,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant)),
            ],
            if (_swapError != null && _swapErrorPair == index) ...[
              const SizedBox(height: 6),
              Text(_swapError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 10),
            Wrap(
              spacing: 12,
              runSpacing: 8,
              children: [
                OutlinedButton(
                  onPressed: busy ? null : () => setState(() => _keptPairs.add(index)),
                  child: const Text('Keep both'),
                ),
                FilledButton.tonalIcon(
                  onPressed: _swappingPair != null ? null : () => _swapOne(paper, index, second),
                  icon: busy
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.swap_horiz),
                  label: Text(busy ? 'Swapping…' : 'Swap one'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _swapOne(GeneratedPaper paper, int index, String slot) async {
    setState(() {
      _swappingPair = index;
      _swapError = null;
      _swapErrorPair = null;
    });
    try {
      final updated = await GetIt.I<ApiClient>().swapPaperQuestion(paper.id, slot);
      if (!mounted) return;
      setState(() {
        _editedPaper = updated;
        _swappingPair = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _swapError = 'Could not swap question ${_slotLabel(slot)}: ${serverErrorMessage(e)}';
        _swapErrorPair = index;
        _swappingPair = null;
      });
    }
  }

  Widget _buildIssuesCard(BuildContext context, String title, List<String> items, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        color: color.withValues(alpha: 0.08),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.w600, color: color)),
            const SizedBox(height: 6),
            for (final item in items)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text('• $item', style: const TextStyle(fontSize: 13)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionCard(BuildContext context, Assessment assessment, GeneratedPaper family,
      GeneratedPaper shown, GeneratedSection section) {
    // A preset's section is already named "Section A - Objective": the
    // heading read "Section A — Section A - Objective" (E2E run, 2026-10-01).
    final heading = sectionHeading(section.label, section.name, separator: ' — ');
    final editing = _canEditQuestions(assessment);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$heading (${marksText(section.totalMarks)})',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
            const Divider(),
            for (final q in section.questions)
              _buildQuestion(context, family, shown, q, editing: editing),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestion(BuildContext context, GeneratedPaper family, GeneratedPaper shown, GeneratedQuestion q,
      {required bool editing}) {
    final theme = Theme.of(context);
    final set = _activeSetLabel(family) ?? 'A';
    final slot = '${q.displayNumber}';
    final orSlot = '${q.displayNumber}_OR';
    final busy = _busySlots.contains('$set:$slot') || _busySlots.contains('$set:$orSlot');
    final error = _slotErrors['$set:$slot'] ?? _slotErrors['$set:$orSlot'];
    final notes = [...?_slotNotes['$set:$slot'], ...?_slotNotes['$set:$orSlot']];
    final hasOr = q.internalChoiceText != null && q.internalChoiceText!.isNotEmpty;
    ButtonStyle compact() => TextButton.styleFrom(minimumSize: const Size(0, 44));
    return Padding(
      key: ValueKey('saved-question-$set-$slot'),
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 28, child: Text('${q.displayNumber}.', style: const TextStyle(fontWeight: FontWeight.w600))),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(q.stem),
                    if (hasOr) ...[
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: theme.colorScheme.outlineVariant),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('OR', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 11, color: theme.colorScheme.primary)),
                            const SizedBox(height: 2),
                            Text(q.internalChoiceText!, style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 13)),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  ChipTag(label: '${q.marks}m'),
                  if (q.isCompetency) ...[
                    const SizedBox(height: 4),
                    ChipTag(label: 'CBQ', color: AppColors.info.withValues(alpha: 0.15)),
                  ],
                ],
              ),
            ],
          ),
          for (final n in notes)
            Padding(
              padding: const EdgeInsets.only(left: 28, top: 4),
              child: Text(n, style: theme.textTheme.bodySmall),
            ),
          if (error != null)
            Padding(
              padding: const EdgeInsets.only(left: 28, top: 4),
              child: Text(error, style: TextStyle(color: theme.colorScheme.error)),
            ),
          if (editing)
            Padding(
              padding: const EdgeInsets.only(left: 20),
              child: Wrap(spacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
                if (busy)
                  const Padding(
                    padding: EdgeInsets.all(12),
                    child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                  ),
                TextButton.icon(
                  onPressed: busy ? null : () => _swap(family, shown, slot),
                  icon: const Icon(Icons.swap_horiz),
                  label: const Text('Swap'),
                  style: compact(),
                ),
                TextButton.icon(
                  onPressed: busy ? null : () => _pick(family, shown, slot, q.marks),
                  icon: const Icon(Icons.manage_search),
                  label: const Text('Pick'),
                  style: compact(),
                ),
                TextButton.icon(
                  onPressed: busy ? null : () => _remove(family, shown, q, slot),
                  icon: const Icon(Icons.remove_circle_outline),
                  label: const Text('Remove'),
                  style: compact(),
                ),
                if (hasOr) ...[
                  TextButton(
                    onPressed: busy ? null : () => _swap(family, shown, orSlot),
                    style: compact(),
                    child: const Text('Swap OR'),
                  ),
                  TextButton(
                    onPressed: busy ? null : () => _remove(family, shown, q, orSlot),
                    style: compact(),
                    child: const Text('Remove OR'),
                  ),
                ],
              ]),
            ),
        ],
      ),
    );
  }

  // ------------------------------------------------------------ edits

  /// Runs one edit on the set on screen (each set has its own questions;
  /// the server takes the set's own paper id), then reads the paper back
  /// whole: a removal renumbers every set, and a question a set had to
  /// repeat changes wherever it prints.
  Future<void> _edit(GeneratedPaper family, String set, String slot,
      Future<List<String>> Function(PaperBuilderApi api) call) async {
    final key = '$set:$slot';
    if (_busySlots.contains(key)) return;
    setState(() {
      _busySlots.add(key);
      _slotErrors.remove(key);
    });
    try {
      final notes = await call(GetIt.I<PaperBuilderApi>());
      final fresh = await GetIt.I<ApiClient>().getPaper(family.id);
      if (!mounted) return;
      setState(() {
        _editedPaper = fresh;
        _slotNotes[key] = notes;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _slotErrors[key] = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busySlots.remove(key));
    }
  }

  Future<void> _swap(GeneratedPaper family, GeneratedPaper shown, String slot) => _edit(
      family, _activeSetLabel(family) ?? 'A', slot, (api) async => (await api.swap(shown.id, slot)).notes);

  Future<void> _pick(GeneratedPaper family, GeneratedPaper shown, String slot, int marks) async {
    final source = BankPickerSource(
      api: GetIt.I<PaperBuilderApi>(),
      subject: shown.metadata.subject,
      grade: shown.metadata.grade,
      chapterIds: _assessment?.chapterIds ?? const [],
      onPaper: {
        for (final s in shown.sections)
          for (final q in s.questions) ...[q.questionId, if (q.internalChoiceQuestionId != null) q.internalChoiceQuestionId!],
      },
    );
    final id = await showBankPickerFor(context, source, slot: slot, marks: marks);
    if (id == null || !mounted) return;
    await _edit(family, _activeSetLabel(family) ?? 'A', slot,
        (api) async => (await api.pick(shown.id, slot, id)).notes);
  }

  /// Asks first, and says what the paper loses: a removal renumbers the
  /// paper, takes the same place out of every set, and only a Pick brings
  /// a question back.
  Future<void> _remove(GeneratedPaper family, GeneratedPaper shown, GeneratedQuestion q, String slot) async {
    final alternative = slot.endsWith('_OR');
    final sets = family.sets.length > 1;
    final what = alternative
        ? 'Q${q.displayNumber} will print without its OR choice.'
        : 'The paper drops to ${marksText(_marksOf(shown) - q.marks)}'
            '${q.internalChoiceText != null ? ', its OR choice goes with it,' : ''}'
            ' and the questions after it are renumbered.'
            '${sets ? ' Every set loses its question in the same place.' : ''}';
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(alternative ? 'Remove the OR choice of Q${q.displayNumber}?' : 'Remove Q${q.displayNumber}?'),
        content: Text(what),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Keep it')),
          FilledButton(
            key: const ValueKey('confirm-remove'),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Remove'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    final set = _activeSetLabel(family) ?? 'A';
    await _edit(family, set, slot, (api) async {
      await api.remove(shown.id, slot);
      // The numbers after it moved: notes kept under the old ones are stale.
      _slotNotes.clear();
      _slotErrors.clear();
      return const [];
    });
  }

  // ---------------------------------------------------- export & approve

  Widget _buildExportCard(BuildContext context, Assessment assessment, GeneratedPaper family, GeneratedPaper paper) {
    const offline = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
    final can = _permissions(assessment);
    final editable = paperIsEditable(assessment);
    final set = _activeSetLabel(family);
    final which = set == null ? '' : 'Set $set ';
    Widget busyIcon(_Export kind, IconData icon) => _exporting.contains(kind)
        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
        : Icon(icon);
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Download & approve', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          if (set != null) ...[
            const SizedBox(height: 4),
            Text('These download Set $set. Choose another set above for its own files.',
                style: Theme.of(context).textTheme.bodySmall),
          ],
          const SizedBox(height: 12),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(_error!, key: const ValueKey('export-error'), style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          // One press, one file (QA P-24: "Export PDF" used to reveal a
          // second "Download Paper PDF" button instead of downloading).
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              FilledButton.icon(
                key: const ValueKey('download-paper'),
                onPressed: _exporting.contains(_Export.paper) ? null : () => _download(assessment, paper, set, _Export.paper),
                style: phoneTapTarget(context),
                icon: busyIcon(_Export.paper, Icons.picture_as_pdf),
                label: Text('Download ${which}paper (PDF)'),
              ),
              FilledButton.tonalIcon(
                key: const ValueKey('download-answer-key'),
                onPressed: _exporting.contains(_Export.answerKey)
                    ? null
                    : () => _download(assessment, paper, set, _Export.answerKey),
                style: phoneTapTarget(context),
                icon: busyIcon(_Export.answerKey, Icons.fact_check),
                label: Text('Download ${which}answer key (PDF)'),
              ),
              // An editable Word copy (EX-5), from the server; the offline
              // build renders PDF only.
              if (!offline)
                OutlinedButton.icon(
                  key: const ValueKey('download-docx'),
                  onPressed: _exporting.contains(_Export.docx) ? null : () => _download(assessment, paper, set, _Export.docx),
                  style: phoneTapTarget(context),
                  icon: busyIcon(_Export.docx, Icons.description_outlined),
                  label: Text('Download ${which}as Word (.docx)'),
                ),
              OutlinedButton.icon(
                onPressed: () => _openDelivery(assessment, paper),
                style: phoneTapTarget(context),
                icon: const Icon(Icons.outgoing_mail),
                label: const Text('Preview, print or email'),
              ),
            ],
          ),
          if (editable && !offline && can.mayAskForReview && assessment.status != AssessmentStatus.underReview) ...[
            const SizedBox(height: 8),
            // A review names its reviewer, who is notified; a bare status
            // change put the paper "under review" with nobody reviewing it.
            OutlinedButton.icon(
              key: const ValueKey('ask-review'),
              onPressed: () => _askForReview(assessment),
              icon: const Icon(Icons.rate_review),
              label: const Text('Ask a colleague to review'),
            ),
          ],
          if (editable && assessment.status == AssessmentStatus.underReview) ...[
            const SizedBox(height: 8),
            const Row(children: [
              Icon(Icons.rate_review, size: 16),
              SizedBox(width: 8),
              Expanded(child: Text('In review: the reviewer has been asked to look at it.')),
            ]),
          ],
          if (editable && can.mayApprove) ...[
            const Divider(height: 28),
            Text('Approval', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            const Text(
              'Approving locks the question selection and paper content — nothing can quietly '
              'change after this without a new, explicitly logged correction.',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 10),
            if (_approveError != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(_approveError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ),
            FilledButton.icon(
              key: const ValueKey('approve-lock'),
              onPressed: _approving ? null : () => _approvePaper(assessment),
              icon: _approving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.verified),
              label: Text(_approving ? 'Approving…' : 'Approve & lock paper'),
            ),
          ] else if (!editable) ...[
            const Divider(height: 28),
            Row(children: [
              const Icon(Icons.lock, size: 16, color: AppColors.success),
              const SizedBox(width: 8),
              Expanded(child: Text('Approved — paper is locked (${assessment.status.label}).',
                  key: const ValueKey('paper-locked'),
                  style: const TextStyle(fontWeight: FontWeight.w600))),
            ]),
          ],
        ],
      ),
    );
  }

  Future<void> _approvePaper(Assessment assessment) async {
    setState(() {
      _approving = true;
      _approveError = null;
    });
    try {
      // Gated on a real role: the device's Settings > Profile role offline,
      // a real authenticated principal login online.
      final updated = await GetIt.I<ApiClient>().approveAssessment(assessment.id);
      if (!mounted) return;
      // The answer is the locked paper: the chip, the button and the lock
      // line follow it now, not after a reload (QA P-12).
      setState(() {
        _changedAssessment = updated;
        _approving = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Approved and locked: ${updated.title}')),
      );
    } on AssessmentLockedException catch (e) {
      if (!mounted) return;
      setState(() {
        _approving = false;
        _approveError = serverErrorMessage(e);
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _approving = false;
        _approveError = 'Could not approve: ${serverErrorMessage(e)}';
      });
    }
  }

  PdfSaver get _saver => GetIt.I.isRegistered<PdfSaver>() ? GetIt.I<PdfSaver>() : PdfSaver.platform();

  /// Renders [kind] for [paper] (the set on screen) and hands the file over
  /// in one press: on the web a download, through the app's own Dio with the
  /// session token (/papers/{id}/file is staff-only and a browser tab sends
  /// none); offline, the local PDF to the platform's share/view sheet. The
  /// file is named for the paper ([paperFileName]). A refusal -- a colleague
  /// who may not take the paper away gets 403 -- is shown in the server's
  /// words (QA P-09).
  Future<void> _download(Assessment assessment, GeneratedPaper paper, String? set, _Export kind) async {
    setState(() {
      _exporting.add(kind);
      _error = null;
    });
    final what = switch (kind) {
      _Export.paper => 'the paper',
      _Export.answerKey => 'the answer key',
      _Export.docx => 'the Word file',
    };
    try {
      final api = GetIt.I<ApiClient>();
      final name = paperFileName(
        title: assessment.title,
        grade: paper.metadata.grade,
        subject: paper.metadata.subject,
        set: set,
        kind: kind == _Export.answerKey ? 'answer_key' : 'paper',
        extension: kind == _Export.docx ? 'docx' : 'pdf',
      );
      if (kind == _Export.docx) {
        await _saver.save(await api.downloadPaperDocx(paper.id), name);
        return;
      }
      final path = await api.exportPaper(paper.id, kind == _Export.answerKey ? ExportFormat.answerKey : ExportFormat.pdf);
      _exported['${paper.id}:${kind.name}'] = path;
      if (PaperPermissions.onDevice) {
        // The on-device engine answers with the rendered file's path.
        await _saver.save(await File(path).readAsBytes(), name);
      } else {
        await downloadPaperPdf(api, _saver, paper.id, answerKey: kind == _Export.answerKey, filename: name);
      }
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not download $what: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _exporting.remove(kind));
    }
  }

  /// Preview, print or email the set on screen. The sheet reads the PDF the
  /// server rendered, or the offline build's local copy, so the paper is
  /// exported first if it has not been yet.
  Future<void> _openDelivery(Assessment assessment, GeneratedPaper paper) async {
    var local = _exported['${paper.id}:${_Export.paper.name}'];
    if (local == null) {
      setState(() {
        _exporting.add(_Export.paper);
        _error = null;
      });
      try {
        local = await GetIt.I<ApiClient>().exportPaper(paper.id, ExportFormat.pdf);
        _exported['${paper.id}:${_Export.paper.name}'] = local;
      } catch (e) {
        if (mounted) setState(() => _error = 'Could not prepare the paper: ${serverErrorMessage(e)}');
        return;
      } finally {
        if (mounted) setState(() => _exporting.remove(_Export.paper));
      }
    }
    if (!mounted) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: false,
      builder: (_) => PaperDeliverySheet(
        paperId: paper.id,
        paperTitle: assessment.title,
        subject: paper.metadata.subject,
        grade: paper.metadata.grade,
        schoolName: assessment.schoolId,
        // The on-device engine's export is a file path; the server's a URL.
        localFilePath: PaperPermissions.onDevice ? local : null,
      ),
    );
  }
}
