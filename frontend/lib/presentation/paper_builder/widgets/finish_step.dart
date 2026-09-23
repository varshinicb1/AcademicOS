import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../paper_builder_controller.dart';

/// Step 5: the paper is saved; download the paper and its answer key (every
/// set), open it in the teacher's list, or make another from the same
/// template and chapters.
class FinishStep extends StatelessWidget {
  final PaperBuilderController c;
  const FinishStep({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = c.result!;
    final sets = c.setIds.keys.toList();
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Row(children: [
          Icon(Icons.check_circle, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text('Your paper is saved', style: theme.textTheme.titleMedium)),
        ]),
        const SizedBox(height: 4),
        Text('${r.paper.metadata.assessmentTitle} · Class ${c.grade} ${c.subject} · ${c.paperMarks} marks'
            '${sets.length > 1 ? ' · Sets ${sets.join(', ')}' : ''}'),
        if (r.gaps.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text('This paper is short in ${r.gaps.map((g) => g.title).join(', ')}.',
                style: TextStyle(color: theme.colorScheme.error)),
          ),
        const SizedBox(height: 16),
        Text(
          sets.length > 1
              ? 'Download gives you the paper and the answer key for each set, as PDFs.'
              : 'Download gives you the paper and its answer key, as two PDFs.',
          style: theme.textTheme.bodyMedium,
        ),
        for (final d in c.downloaded)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Row(children: [
              Icon(Icons.download_done, size: 18, color: theme.colorScheme.primary),
              const SizedBox(width: 6),
              Expanded(child: Text('$d downloaded')),
            ]),
          ),
        if (c.downloadError != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            // The sentence ends here, not in the mapper: serverErrorMessage's
            // branches have no full stop of their own, and the retry clause is
            // added only where sending the same request again could work (see
            // PaperBuilderController's class doc). Until 2026-09-23 this line
            // ran the two together -- "You don't have access to that Tap
            // Download to try again." -- which on a 401 or 403 pointed the
            // teacher at the one action the server refuses every time.
            child: Text(
                'Download failed: ${c.downloadError}.'
                '${c.downloadRetryable ? ' Tap Download to try again.' : ''}',
                style: TextStyle(color: theme.colorScheme.error)),
          ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: () => GoRouter.maybeOf(context)?.go('/assessment/${r.assessmentId}'),
          icon: const Icon(Icons.folder_open),
          label: const Text('Open in my papers'),
          style: OutlinedButton.styleFrom(minimumSize: const Size(0, 48)),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: c.generating ? null : c.makeAnother,
          icon: const Icon(Icons.replay),
          label: const Text('Make another like this'),
          style: OutlinedButton.styleFrom(minimumSize: const Size(0, 48)),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: () => c.goTo(BuilderStep.paper),
          style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
          child: const Text('Back to the questions'),
        ),
      ],
    );
  }
}
