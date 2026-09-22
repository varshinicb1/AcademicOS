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
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Text('Which class is this paper for?', style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final g in builderGrades)
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
        else
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final s in builderSubjects(c.grade!))
              ChoiceChip(
                label: Text(s),
                selected: c.subject == s,
                onSelected: (_) => c.pickSubject(s),
                materialTapTargetSize: MaterialTapTargetSize.padded,
              ),
          ]),
      ],
    );
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
