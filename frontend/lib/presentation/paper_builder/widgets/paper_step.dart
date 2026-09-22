import 'package:flutter/material.dart';

import '../../../domain/repositories/requests.dart' show GeneratedQuestion, GeneratedSection;
import '../paper_builder_controller.dart';
import 'bank_picker.dart';

/// Step 4: the generated paper, question by question, with Swap (the next
/// best question for the slot, from the server) and Pick (the teacher's own
/// choice from the bank). The paper is already saved; every change is saved
/// to it and to every set as it is made.
class PaperStep extends StatelessWidget {
  final PaperBuilderController c;
  const PaperStep({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final paper = c.shownPaper;
    final header = _Header(c: c);
    if (paper == null) {
      return ListView(padding: const EdgeInsets.all(16), children: [
        header,
        if (c.loadingSet) const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())),
        if (c.setError != null)
          Text('Could not load Set ${c.viewingSet}: ${c.setError}',
              style: TextStyle(color: Theme.of(context).colorScheme.error)),
      ]);
    }
    final rows = <Widget Function()>[
      () => header,
      for (final s in paper.sections) ...[
        () => _SectionHeading(s: s),
        for (final q in s.questions) () => _QuestionCard(c: c, q: q, editable: c.viewingSet == 'A'),
      ],
    ];
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      itemCount: rows.length,
      itemBuilder: (_, i) => rows[i](),
    );
  }
}

class _Header extends StatelessWidget {
  final PaperBuilderController c;
  const _Header({required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = c.result!;
    final expected = c.template?.totalMarks ?? c.paperMarks;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Text(r.paper.metadata.assessmentTitle, style: theme.textTheme.titleMedium),
      Text(
        '${c.paperMarks} / $expected marks · ${c.paperQuestions} questions · Class ${c.grade} ${c.subject}',
        key: const ValueKey('paper-totals'),
        style: theme.textTheme.bodyMedium,
      ),
      Text('Saved to your papers. Changes below are saved as you make them.',
          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
      if (r.gaps.isNotEmpty)
        Container(
          margin: const EdgeInsets.only(top: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: theme.colorScheme.errorContainer, borderRadius: BorderRadius.circular(12)),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('This paper is short:', style: theme.textTheme.titleSmall),
            for (final g in r.gaps)
              Text('• ${g.title}: ${g.filled} of ${g.needed} questions', style: theme.textTheme.bodySmall),
            TextButton(
              onPressed: () => c.goTo(BuilderStep.scope),
              style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
              child: const Text('Fix the gaps and generate again'),
            ),
          ]),
        ),
      for (final w in c.paper?.warnings ?? const <String>[])
        Padding(padding: const EdgeInsets.only(top: 6), child: Text('⚠ $w', style: theme.textTheme.bodySmall)),
      if (c.setIds.length > 1) ...[
        const SizedBox(height: 10),
        SegmentedButton<String>(
          segments: [for (final l in c.setIds.keys) ButtonSegment(value: l, label: Text('Set $l'))],
          selected: {c.viewingSet},
          onSelectionChanged: (s) => c.showSet(s.first),
        ),
        if (c.viewingSet != 'A')
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text('Set ${c.viewingSet} is Set A reordered. Swap or pick on Set A; every set follows.',
                style: theme.textTheme.bodySmall),
          ),
      ],
      const SizedBox(height: 8),
    ]);
  }
}

class _SectionHeading extends StatelessWidget {
  final GeneratedSection s;
  const _SectionHeading({required this.s});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 16, bottom: 4),
      child: Text('Section ${s.label} · ${s.name} · ${s.totalMarks} marks',
          style: theme.textTheme.titleSmall?.copyWith(color: theme.colorScheme.primary, fontWeight: FontWeight.w700)),
    );
  }
}

class _QuestionCard extends StatelessWidget {
  final PaperBuilderController c;
  final GeneratedQuestion q;
  final bool editable;
  const _QuestionCard({required this.c, required this.q, required this.editable});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final slot = '${q.displayNumber}';
    final orSlot = '${q.displayNumber}_OR';
    final busy = c.busySlots.contains(slot) || c.busySlots.contains(orSlot);
    final error = c.slotErrors[slot] ?? c.slotErrors[orSlot];
    final notes = [...?c.slotNotes[slot], ...?c.slotNotes[orSlot]];
    return Card(
      key: ValueKey('question-$slot'),
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 10, 8, 4),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${q.displayNumber}.', style: theme.textTheme.titleSmall),
            const SizedBox(width: 8),
            Expanded(child: Text(q.stem)),
            const SizedBox(width: 8),
            Text('[${q.marks}]', style: theme.textTheme.labelLarge),
          ]),
          for (final p in q.parts)
            Padding(
              padding: const EdgeInsets.only(left: 24, top: 4),
              child: Text('(${p.partNumber}) ${p.text}', style: theme.textTheme.bodyMedium),
            ),
          if (q.internalChoiceText != null) ...[
            Padding(
              padding: const EdgeInsets.only(top: 6, bottom: 2),
              child: Center(child: Text('OR', style: theme.textTheme.labelLarge)),
            ),
            Padding(padding: const EdgeInsets.only(left: 24), child: Text(q.internalChoiceText!)),
          ],
          for (final n in notes)
            Padding(padding: const EdgeInsets.only(top: 4), child: Text(n, style: theme.textTheme.bodySmall)),
          if (error != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(error, style: TextStyle(color: theme.colorScheme.error)),
            ),
          if (editable)
            Wrap(spacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
              if (busy) const Padding(
                padding: EdgeInsets.all(12),
                child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
              ),
              TextButton.icon(
                onPressed: busy ? null : () => c.swap(slot),
                icon: const Icon(Icons.swap_horiz),
                label: const Text('Swap'),
                style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
              ),
              TextButton.icon(
                onPressed: busy ? null : () => _pick(context, slot),
                icon: const Icon(Icons.manage_search),
                label: const Text('Pick'),
                style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
              ),
              if (q.internalChoiceText != null)
                TextButton(
                  onPressed: busy ? null : () => c.swap(orSlot),
                  style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
                  child: const Text('Swap OR'),
                ),
            ]),
        ]),
      ),
    );
  }

  Future<void> _pick(BuildContext context, String slot) async {
    final id = await showBankPicker(context, c, slot: slot, marks: q.marks);
    if (id != null) await c.pick(slot, id);
  }
}
