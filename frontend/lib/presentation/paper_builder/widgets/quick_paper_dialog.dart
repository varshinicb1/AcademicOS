import 'package:flutter/material.dart';

import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../paper_builder_controller.dart';

/// Opens the quick paper dialog for the builder's class and subject.
Future<void> showQuickPaperDialog(BuildContext context, PaperBuilderController c) {
  if (c.chapters.isEmpty && !c.loadingChapters) c.loadChapters();
  return showDialog<void>(context: context, builder: (_) => QuickPaperDialog(c: c));
}

/// A paper of any total, at a level: the server makes the marks asked for
/// whenever the bank can, moving a section the bank cannot fill to marks it
/// holds, and says what it changed. "Check the bank" shows what the paper
/// would hold -- the marks, the layout, and any section the bank cannot fill
/// -- BEFORE anything is saved; "Save" then makes that paper (audit D57: a
/// quick Science 10 paper asked for 40 marks printed 28, and said so only
/// after it was saved).
class QuickPaperDialog extends StatefulWidget {
  final PaperBuilderController c;
  const QuickPaperDialog({super.key, required this.c});

  static const marksChoices = [20, 25, 40, 50, 80];
  static const levels = {
    'foundation': 'Foundation',
    'standard': 'Standard',
    'advanced': 'Advanced',
  };

  @override
  State<QuickPaperDialog> createState() => _QuickPaperDialogState();
}

class _QuickPaperDialogState extends State<QuickPaperDialog> {
  int _marks = 40;
  String _tier = 'standard';
  int _sets = 1;
  final Set<String> _chapters = {};
  QuickPaperResult? _preview;
  bool _checking = false;
  bool _saving = false;
  String? _error;
  int _ticket = 0;

  PaperBuilderController get c => widget.c;

  /// Any change makes the last check stale: it is dropped, never saved.
  void _changed(VoidCallback f) => setState(() {
        f();
        _preview = null;
        _error = null;
        ++_ticket;
      });

  Future<void> _check() async {
    final ticket = ++_ticket;
    setState(() {
      _checking = true;
      _error = null;
    });
    try {
      final r = await c.previewQuick(
          totalMarks: _marks, tier: _tier, chapterIds: _chapters.toList(), setCount: _sets);
      if (!mounted || ticket != _ticket) return;
      setState(() => _preview = r);
    } catch (e) {
      if (!mounted || ticket != _ticket) return;
      setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted && ticket == _ticket) setState(() => _checking = false);
    }
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await c.generateQuick(totalMarks: _marks, tier: _tier, chapterIds: _chapters.toList(), setCount: _sets);
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  // The chapters arrive while the dialog is open.
  @override
  Widget build(BuildContext context) => ListenableBuilder(listenable: c, builder: (context, _) => _dialog(context));

  Widget _dialog(BuildContext context) {
    final theme = Theme.of(context);
    final p = _preview;
    return AlertDialog(
      title: Text('Quick paper · Class ${c.grade} ${c.subject}'),
      scrollable: true,
      content: SizedBox(
        width: 560,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Total marks', style: theme.textTheme.titleSmall),
          Wrap(spacing: 6, children: [
            for (final m in QuickPaperDialog.marksChoices)
              ChoiceChip(
                key: ValueKey('quick-marks-$m'),
                label: Text('$m'),
                selected: _marks == m,
                onSelected: (_) => _changed(() => _marks = m),
              ),
          ]),
          const SizedBox(height: 12),
          Text('Level', style: theme.textTheme.titleSmall),
          Wrap(spacing: 6, children: [
            for (final e in QuickPaperDialog.levels.entries)
              ChoiceChip(
                key: ValueKey('quick-tier-${e.key}'),
                label: Text(e.value),
                selected: _tier == e.key,
                onSelected: (_) => _changed(() => _tier = e.key),
              ),
          ]),
          const SizedBox(height: 12),
          Text('Sets', style: theme.textTheme.titleSmall),
          Wrap(spacing: 6, children: [
            for (final n in const [1, 2, 3])
              ChoiceChip(
                label: Text(n == 1 ? '1 set' : n == 2 ? 'A, B' : 'A, B, C'),
                selected: _sets == n,
                onSelected: (_) => _changed(() => _sets = n),
              ),
          ]),
          const SizedBox(height: 12),
          Text(_chapters.isEmpty ? 'Chapters: the whole syllabus' : 'Chapters: ${_chapters.length} chosen',
              style: theme.textTheme.titleSmall),
          if (c.chapters.isNotEmpty)
            Wrap(spacing: 6, runSpacing: 4, children: [
              for (final ch in c.chapters)
                FilterChip(
                  label: Text(ch.chapterName, overflow: TextOverflow.ellipsis),
                  selected: _chapters.contains(ch.chapterId),
                  onSelected: (on) => _changed(() => on ? _chapters.add(ch.chapterId) : _chapters.remove(ch.chapterId)),
                ),
            ]),
          const SizedBox(height: 16),
          if (_checking) const LinearProgressIndicator(),
          if (p != null) _PreviewSummary(result: p),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(_error!, key: const ValueKey('quick-error'), style: TextStyle(color: theme.colorScheme.error)),
            ),
        ]),
      ),
      actions: [
        TextButton(onPressed: _saving ? null : () => Navigator.of(context).pop(), child: const Text('Cancel')),
        if (p == null)
          FilledButton(
            key: const ValueKey('quick-check'),
            onPressed: _checking ? null : _check,
            child: const Text('Check the bank'),
          )
        else
          FilledButton(
            key: const ValueKey('quick-save'),
            onPressed: _saving ? null : _save,
            child: Text(_saving
                ? 'Saving…'
                : p.holdsAll
                    ? 'Save this paper'
                    : 'Save it short (${p.marksHeld} of ${p.marksAsked} marks)'),
          ),
      ],
    );
  }
}

/// What the paper would hold: the marks, the layout, what the server
/// changed, and every section the bank cannot fill.
class _PreviewSummary extends StatelessWidget {
  final QuickPaperResult result;
  const _PreviewSummary({required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = result;
    final questions = r.paper.sections.fold<int>(0, (s, x) => s + x.questions.length);
    return Container(
      key: const ValueKey('quick-preview'),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: r.holdsAll ? theme.colorScheme.surfaceContainerHighest : theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(
          r.holdsAll
              ? 'Holds all ${r.marksAsked} marks: $questions questions, ${r.layout}.'
              : 'Holds ${r.marksHeld} of the ${r.marksAsked} marks asked for: the bank cannot make up the rest.',
          key: const ValueKey('quick-preview-total'),
          style: theme.textTheme.titleSmall,
        ),
        // The level's basis (EX-3): how many questions had a difficulty
        // measured from marks teachers entered.
        if (r.difficultySentence case final s?)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(s, key: const ValueKey('quick-difficulty'), style: theme.textTheme.bodySmall),
          ),
        if (r.shortfall.isNotEmpty) ...[
          const SizedBox(height: 6),
          Text('Sections the bank cannot fill:', style: theme.textTheme.bodyMedium),
          for (final s in r.shortfall)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                '• Section ${s.label} (${s.name}): ${s.printed} of ${s.asked} × ${s.marksEach} marks, '
                '${s.missingMarks} marks short -- ${s.reason}.',
                style: theme.textTheme.bodySmall,
              ),
            ),
        ],
        for (final w in r.paper.warnings)
          if (w != r.difficultySentence)
            Padding(padding: const EdgeInsets.only(top: 4), child: Text('⚠ $w', style: theme.textTheme.bodySmall)),
        const SizedBox(height: 4),
        Text('Nothing is saved until you save it.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
      ]),
    );
  }
}
