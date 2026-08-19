import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Pillar 6 — Principal Intelligence: school health, not individual questions.
class PrincipalPage extends StatefulWidget {
  final String schoolId;
  const PrincipalPage({super.key, this.schoolId = 'school_1'});

  @override
  State<PrincipalPage> createState() => _PrincipalPageState();
}

class _PrincipalPageState extends State<PrincipalPage> {
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
      _future = GetIt.I<PillarApi>().schoolInsights(widget.schoolId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // Reached via a nested route ('/analytics/school' under '/analytics'),
        // same canPop quirk fixed for the Planner — see shell.dart's
        // forceShellLeading docstring.
        leading: forceShellLeading(context),
        title: const Text('School Intelligence'),
        actions: [IconButton(onPressed: _load, icon: const Icon(Icons.refresh))],
      ),
      body: FutureBuilder<SchoolInsights>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Rolling up school performance…');
          }
          if (snap.hasError) {
            return ErrorDisplay(message: '${snap.error}', onRetry: _load);
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
                          color: s.averageMastery < 0.6 ? Colors.red : Colors.green)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: StatCard(
                          label: 'Students',
                          value: '${s.students}',
                          icon: Icons.groups,
                          color: Colors.blue)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: StatCard(
                          label: 'Assessments',
                          value: '${s.assessments}',
                          icon: Icons.assignment,
                          color: Colors.indigo)),
                ],
              ),
              const SizedBox(height: 8),
              const SectionHeader(title: 'By subject'),
              ...s.subjects.map((sub) => AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${sub.subject} — Grade ${sub.grade}',
                            style: const TextStyle(
                                fontWeight: FontWeight.w600, fontSize: 15)),
                        const SizedBox(height: 10),
                        _bar(context, 'Mastery', sub.averageMastery),
                        const SizedBox(height: 8),
                        _bar(context, 'Curriculum coverage', sub.curriculumCoverage),
                        if (sub.weakestConcept != null) ...[
                          const SizedBox(height: 10),
                          Row(children: [
                            const Icon(Icons.trending_down, size: 15, color: Colors.red),
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
                      color: Colors.orange.withValues(alpha: 0.08),
                      child: Row(children: [
                        const Icon(Icons.priority_high, color: Colors.orange),
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
