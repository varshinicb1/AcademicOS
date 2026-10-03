import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/shell.dart';
import 'guide_content.dart';

/// Where the Guide lives. Under /school with the other workspace pages; the
/// side navigation lists it on its own row, above Settings.
const guidePath = '/school/guide';

/// Whether [role] has a Guide: every signed-in role of the online product.
/// The offline Android build has no school server, so the pages the Guide
/// leads to are not there.
bool guideAvailableFor(String role) =>
    !const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false) && guideRoles.contains(role);

/// The question mark at the end of a page's app bar ([destinationAppBar]):
/// opens the Guide. Nothing for a role with no guide, or outside a router (a
/// page mounted alone in a test).
class GuideButton extends StatelessWidget {
  const GuideButton({super.key});

  @override
  Widget build(BuildContext context) {
    if (!guideAvailableFor(signedInRole()) || GoRouter.maybeOf(context) == null) return const SizedBox.shrink();
    return IconButton(
      key: const ValueKey('guide-button'),
      tooltip: 'Guide',
      icon: const Icon(Icons.help_outline),
      onPressed: () => context.go(guidePath),
    );
  }
}

/// The Guide: the jobs the signed-in role does most, each opening to a few
/// numbered steps and a Take me there button that goes to the page that does
/// it (guide_content.dart).
class GuidePage extends StatelessWidget {
  const GuidePage({super.key, this.role});

  /// Whose guide to show; the signed-in role when null.
  final String? role;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final who = role ?? signedInRole();
    final jobs = guideJobsFor(who);
    return Scaffold(
      appBar: destinationAppBar(context, title: const Text('Guide'), guide: false),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: [
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                if (jobs.isEmpty)
                  Text('Sign in to see the guide for your role.', style: theme.textTheme.bodyLarge)
                else ...[
                  Text('What a ${guideRoleName(who)} does most', style: theme.textTheme.titleLarge),
                  const SizedBox(height: 6),
                  Text(
                    'Open a job to see its steps. Take me there opens the page where you do it.',
                    style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  ),
                  if (who == 'principal' || who == 'teacher') ...[
                    const SizedBox(height: 4),
                    Text(
                      'Pages you use less often are in the menu under More${who == 'principal' ? ' and Setup' : ''}.',
                      style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                  ],
                  const SizedBox(height: 16),
                  for (final job in jobs) _JobCard(job: job),
                ],
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _JobCard extends StatelessWidget {
  const _JobCard({required this.job});

  final GuideJob job;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return AppCard(
      padding: EdgeInsets.zero,
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        key: PageStorageKey('guide-job-${job.id}'),
        leading: Icon(job.icon, color: colors.primary),
        title: Text(job.title, style: theme.textTheme.titleMedium),
        subtitle: Text(job.summary, style: theme.textTheme.bodySmall),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (var i = 0; i < job.steps.length; i++) _Step(number: i + 1, text: job.steps[i]),
          const SizedBox(height: 8),
          FilledButton.icon(
            key: ValueKey('guide-go-${job.id}'),
            onPressed: () => context.go(job.route),
            style: phoneTapTarget(context),
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Take me there'),
          ),
        ],
      ),
    );
  }
}

/// One numbered step: the number in a small ember-tinted circle, then the
/// sentence.
class _Step extends StatelessWidget {
  const _Step({required this.number, required this.text});

  final int number;
  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
          padding: const EdgeInsets.symmetric(horizontal: 4),
          alignment: Alignment.center,
          decoration: BoxDecoration(color: colors.primaryContainer, borderRadius: BorderRadius.circular(12)),
          child: Text('$number',
              style: theme.textTheme.labelMedium?.copyWith(color: colors.onPrimaryContainer, fontWeight: FontWeight.w600)),
        ),
        const SizedBox(width: 12),
        Expanded(child: Text(text, style: theme.textTheme.bodyMedium)),
      ]),
    );
  }
}
