import 'package:flutter/material.dart';

import '../paper_builder_controller.dart';

/// Step 1: which class and subject. Chips, not dropdowns: every choice is one
/// tap and all of them are visible at once on a phone.
class ClassSubjectStep extends StatelessWidget {
  final PaperBuilderController c;
  const ClassSubjectStep({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final last = c.lastTime;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        // A new paper starts here; the last paper's class and subject are
        // one tap away, never chosen for the teacher (QA P-25).
        if (last != null && c.grade == null)
          Card(
            key: const ValueKey('builder-continue'),
            margin: const EdgeInsets.only(bottom: 16),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Continue where you left off', style: theme.textTheme.titleSmall),
                const SizedBox(height: 2),
                Text(
                    'Class ${last.grade} · ${last.subject}'
                    '${c.memory.templateId != null ? ', with the template you used last' : ''}.',
                    style: theme.textTheme.bodySmall),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: c.continueLastTime,
                    style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
                    icon: const Icon(Icons.arrow_forward),
                    label: Text('Continue with Class ${last.grade} ${last.subject}'),
                  ),
                ),
              ]),
            ),
          ),
        Text('Which class is this paper for?', style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final g in c.offeredGrades)
            ChoiceChip(
              label: Text('Class $g'),
              selected: c.grade == g,
              onSelected: (_) => c.pickGrade(g),
              materialTapTargetSize: MaterialTapTargetSize.padded,
            ),
        ]),
        const SizedBox(height: 24),
        Text('Subject', style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        if (c.grade == null)
          Text('Choose a class first.', style: TextStyle(color: theme.colorScheme.onSurfaceVariant))
        else if (c.loadingCatalog)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Row(children: [
              SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
              SizedBox(width: 12),
              Text('Checking which subjects have questions...'),
            ]),
          )
        else if (c.catalogError != null)
          _CatalogError(c: c)
        else ...[
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final s in c.subjectsFor(c.grade!))
              ChoiceChip(
                label: Text(s),
                selected: c.subject == s,
                onSelected: (_) => c.pickSubject(s),
                materialTapTargetSize: MaterialTapTargetSize.padded,
              ),
          ]),
          if (c.notYetFor(c.grade!).isNotEmpty)
            Padding(
              key: const ValueKey('subjects-not-yet'),
              padding: const EdgeInsets.only(top: 12),
              child: Text(
                _notYet(c.subjectsFor(c.grade!).isEmpty, c.notYetFor(c.grade!), c.grade!),
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
            ),
        ],
      ],
    );
  }

  /// "Hindi, Sanskrit and Computer Science have no questions for Class 8 yet."
  static String _notYet(bool none, List<String> subjects, int grade) {
    if (none) return 'The question bank has no questions for Class $grade yet.';
    final list = subjects.length == 1
        ? subjects.first
        : '${subjects.sublist(0, subjects.length - 1).join(', ')} and ${subjects.last}';
    final verb = subjects.length == 1 ? 'has' : 'have';
    return '$list $verb no questions for Class $grade yet.';
  }
}

/// The catalog did not load: the sentence, and Retry where retrying can work.
class _CatalogError extends StatelessWidget {
  final PaperBuilderController c;
  const _CatalogError({required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(c.catalogError!, style: TextStyle(color: theme.colorScheme.error)),
      if (c.catalogRetryable)
        Padding(
          padding: const EdgeInsets.only(top: 8),
          child: OutlinedButton(
            onPressed: c.loadCatalog,
            style: OutlinedButton.styleFrom(minimumSize: const Size(88, 44)),
            child: const Text('Retry'),
          ),
        ),
    ]);
  }
}

/// The class and subject in force, with the one tap that changes them --
/// shown at the top of every later step.
class ClassSubjectBanner extends StatelessWidget {
  final PaperBuilderController c;
  const ClassSubjectBanner({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(children: [
      Icon(Icons.school_outlined, size: 20, color: theme.colorScheme.primary),
      const SizedBox(width: 8),
      Expanded(
        child: Text('Class ${c.grade} · ${c.subject}',
            style: theme.textTheme.titleSmall, overflow: TextOverflow.ellipsis),
      ),
      TextButton(
        onPressed: () => c.goTo(BuilderStep.classSubject),
        style: TextButton.styleFrom(minimumSize: const Size(64, 44)),
        child: const Text('Change'),
      ),
    ]);
  }
}
