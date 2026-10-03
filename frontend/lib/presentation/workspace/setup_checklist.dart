import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// One step of setting a school up, as the server reads it from the school's own data
/// (GET /setup-status): what it is, how far it is, where it is done.
typedef SetupStep = ({String key, String title, String detail, String path, bool done});

/// A new school's setup level, on the principal's School page: a percentage, and every
/// step with where it stands -- School name, Classes, Terms, Teachers, a teacher for each
/// subject, Timetable, Students, a first paper -- each a link.
///
/// A new principal landed on a dashboard of zeros with no word on what to do first, and
/// class setup was found only by guessing "Invite people" (QA S-09, 2026-10-01). The level
/// is computed by the server on every read, from what the school actually has, so it
/// cannot go stale or be ticked by hand. The card goes away once every step is done.
class SetupChecklistCard extends StatefulWidget {
  const SetupChecklistCard({super.key});

  @override
  State<SetupChecklistCard> createState() => _SetupChecklistCardState();
}

class _Status {
  final List<SetupStep> steps;
  final int percent;
  final String? nextKey;
  const _Status(this.steps, this.percent, this.nextKey);
}

class _SetupChecklistCardState extends State<SetupChecklistCard> {
  late Future<_Status> _future = _load();

  static Future<_Status> _load() async {
    final r = await Ops.map('/setup-status');
    return _Status([
      for (final s in (r['steps'] as List).cast<Map>())
        (key: s['key'] as String, title: s['title'] as String, detail: s['detail'] as String,
          path: s['path'] as String, done: s['done'] == true),
    ], (r['percent'] as num).toInt(), r['nextKey'] as String?);
  }

  void _reload() {
    if (!mounted) return;
    setState(() {
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<_Status>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const SizedBox.shrink();
        if (snap.hasError) {
          return Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Text('${tr('The setup checklist could not load')}: ${serverErrorMessage(snap.error!)}',
                key: const ValueKey('setup-checklist-error'),
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error)),
          );
        }
        final status = snap.data!;
        final steps = status.steps;
        final done = steps.where((s) => s.done).length;
        if (done == steps.length) return const SizedBox.shrink();
        final next = steps.firstWhere((s) => s.key == status.nextKey, orElse: () => steps.firstWhere((s) => !s.done));
        return AppCard(
          key: const ValueKey('setup-checklist'),
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(tr('Set up your school'), style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text('$done ${tr('of')} ${steps.length} ${tr('done')}. ${tr('Next')}: ${tr(next.title)}.',
                style: theme.textTheme.bodySmall),
            const SizedBox(height: 8),
            Semantics(
              label: '${status.percent} percent set up',
              child: LinearProgressIndicator(
                  key: const ValueKey('setup-progress'),
                  value: status.percent / 100, minHeight: 6, borderRadius: BorderRadius.circular(3)),
            ),
            const SizedBox(height: 4),
            Text('${status.percent}% ${tr('set up')}',
                key: const ValueKey('setup-percent'), style: theme.textTheme.bodySmall),
            const SizedBox(height: 8),
            FilledButton.icon(
              key: const ValueKey('setup-wizard-start'),
              style: phoneTapTarget(context),
              onPressed: () => context.push('/school/setup').then((_) => _reload()),
              icon: const Icon(Icons.auto_fix_high_outlined),
              label: Text(done == 0 ? tr('Start guided setup') : tr('Continue guided setup')),
            ),
            const SizedBox(height: 4),
            for (final s in steps)
              ListTile(
                key: ValueKey('setup-step-${s.key}'),
                contentPadding: EdgeInsets.zero,
                leading: Icon(s.done ? Icons.check_circle : Icons.radio_button_unchecked,
                    color: s.done ? AppColors.success : theme.colorScheme.onSurfaceVariant,
                    semanticLabel: s.done ? tr('Done') : tr('Not done yet')),
                title: Text(tr(s.title),
                    style: s.done ? TextStyle(color: theme.colorScheme.onSurfaceVariant) : null),
                subtitle: Text(tr(s.detail)),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push(s.path).then((_) => _reload()),
              ),
          ]),
        );
      },
    );
  }
}
