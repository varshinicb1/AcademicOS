import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/session/current_session.dart';
import '../../../core/sync/network_policy.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import 'package:academicos/core/theme/app_theme.dart';

/// Pillar 6 — Principal Intelligence: school health, not individual questions.
class PrincipalPage extends StatefulWidget {
  /// Null means the signed-in user's own school -- the only one the server
  /// answers for. A fixed default here ('demo_school' until Task 604) got
  /// every real school a 403 (re-audit, 2026-09-22).
  final String? schoolId;
  const PrincipalPage({super.key, this.schoolId});

  @override
  State<PrincipalPage> createState() => _PrincipalPageState();
}

class _PrincipalPageState extends State<PrincipalPage> {
  String get _schoolId => widget.schoolId ?? CurrentSession.schoolId;

  late Future<SchoolInsights> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    // Block body, not an arrow: `() => _future = ...` returns the Future,
    // and setState rejects a callback that returns anything.
    setState(() {
      _future = GetIt.I<PillarApi>().schoolInsights(_schoolId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // A destination of the side navigation: the menu on a phone and no
        // back arrow (shell.dart's forceShellLeading).
        leading: forceShellLeading(context),
        title: const Text('School insights'),
        actions: [
          // §14/§18's missing piece: real assignment/enrollment, so the
          // teacher and student schedule screens this session built have
          // anything real to show for a real school. The admin console is
          // the school's server's roster and calendar: the offline build has
          // neither, and registers no API to reach them.
          if (!kOfflineBuild)
            IconButton(
              tooltip: 'Assign teachers & students',
              onPressed: () => context.push('/admin'),
              icon: const Icon(Icons.admin_panel_settings_outlined),
            ),
          IconButton(tooltip: 'Refresh', onPressed: _load, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: FutureBuilder<SchoolInsights>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Rolling up school performance…');
          }
          if (snap.hasError) {
            return ErrorDisplay(
              message: 'Could not load school performance: ${serverErrorMessage(snap.error!)}',
              // A 401/403 would only be refused again (Task 802).
              onRetry: isRetryable(snap.error!) ? _load : null,
            );
          }
          final s = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Row(
                children: [
                  Expanded(
                      child: StatCard(
                          label: 'Avg mastery',
                          value: '${(s.averageMastery * 100).round()}%',
                          icon: Icons.school,
                          color: s.averageMastery < 0.6 ? AppColors.danger : AppColors.success)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: StatCard(
                          label: 'Students',
                          value: '${s.students}',
                          icon: Icons.groups,
                          color: AppColors.info)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: StatCard(
                          label: 'Assessments',
                          value: '${s.assessments}',
                          icon: Icons.assignment,
                          color: AppColors.accent)),
                ],
              ),
              if (s.studentsWithEvidence != null) ...[
                const SizedBox(height: 8),
                Text(
                  key: const ValueKey('insights-evidence'),
                  '${s.students} ${s.students == 1 ? 'student is' : 'students are'} enrolled; with evidence: '
                  '${s.studentsWithEvidence} (marked papers, marked homework or finished practice). '
                  'Mastery is measured over those.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              const SizedBox(height: 8),
              const SectionHeader(title: 'By subject'),
              ...s.subjects.map((sub) => AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${sub.subject} · Class ${sub.grade}',
                            style: const TextStyle(
                                fontWeight: FontWeight.w600, fontSize: 15)),
                        const SizedBox(height: 10),
                        _bar(context, 'Mastery', sub.averageMastery),
                        const SizedBox(height: 8),
                        _bar(context, 'Curriculum coverage', sub.curriculumCoverage),
                        if (sub.weakestConcept != null) ...[
                          const SizedBox(height: 10),
                          Row(children: [
                            const Icon(Icons.trending_down, size: 15, color: AppColors.danger),
                            const SizedBox(width: 6),
                            Expanded(child: Text('Weakest: ${sub.weakestConcept}')),
                          ]),
                        ],
                      ],
                    ),
                  )),
              if (s.interventions.isNotEmpty) ...[
                const SectionHeader(
                    title: 'Recommended interventions',
                    subtitle: 'Where leadership attention changes outcomes'),
                ...s.interventions.map((i) => AppCard(
                      color: AppColors.warning.withValues(alpha: 0.08),
                      child: Row(children: [
                        const Icon(Icons.priority_high, color: AppColors.warning),
                        const SizedBox(width: 10),
                        Expanded(child: Text(i)),
                      ]),
                    )),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _bar(BuildContext context, String label, double value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 12))),
          Text('${(value * 100).round()}%', style: const TextStyle(fontSize: 12)),
        ]),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(value: value, minHeight: 7),
        ),
      ],
    );
  }
}
