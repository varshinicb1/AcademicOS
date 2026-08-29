import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Pillar 5 — Teacher Intelligence: actions, not marks.
class GapAnalysisPage extends StatefulWidget {
  final String assessmentId;
  const GapAnalysisPage({super.key, this.assessmentId = ''});

  @override
  State<GapAnalysisPage> createState() => _GapAnalysisPageState();
}

class _GapAnalysisPageState extends State<GapAnalysisPage> {
  final _controller = TextEditingController();
  Future<ClassInsights>? _future;

  // Real gap found on-device: this required a teacher to know and type a
  // raw assessment ID (a generated string like 'assess_...') with no way
  // to see or pick from their real evaluated assessments. Sourcing a real
  // recent list from LocalStore -- same fix pattern as the Mastery page's
  // student picker.
  //
  // Real bug found and fixed: filtering on status == 'evaluated' alone isn't
  // proof real per-student evaluation data exists on THIS device. SyncService
  // only syncs assessment-level metadata (including status) between devices,
  // never the underlying evaluations/mastery -- so an assessment pulled from
  // another teacher's device (or after a reinstall) can genuinely carry
  // status:'evaluated' with zero local evaluations, which used to auto-select
  // and permanently dead-end on "No evaluated sheets yet for this
  // assessment." Gating on real local evidence (evaluationsFor is non-empty)
  // instead means the picker only ever offers assessments this page can
  // actually show something real for.
  List<Map<String, dynamic>> get _evaluatedAssessments => LocalStore.instance
      .allAssessments()
      .where((a) => a['status'] == 'evaluated')
      .where((a) => LocalStore.instance.evaluationsFor(a['id'] as String).isNotEmpty)
      .toList();

  @override
  void initState() {
    super.initState();
    _controller.text = widget.assessmentId;
    if (widget.assessmentId.isNotEmpty) {
      _load();
    } else {
      final real = _evaluatedAssessments;
      if (real.isNotEmpty) {
        _controller.text = real.first['id'] as String;
        _load();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _load() {
    setState(() {
      _future = GetIt.I<PillarApi>().classInsights(_controller.text.trim());
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Reached via a nested route ('/analytics/gaps' under '/analytics'),
      // same canPop quirk fixed for the Planner — see shell.dart's
      // forceShellLeading docstring.
      appBar: AppBar(leading: forceShellLeading(context), title: const Text('Teacher Insights')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      labelText: 'Assessment ID',
                      hintText: 'assess_…',
                      isDense: true,
                    ),
                    onSubmitted: (_) => _load(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton(onPressed: _load, child: const Text('Analyse')),
              ],
            ),
          ),
          if (_evaluatedAssessments.isNotEmpty)
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  for (final a in _evaluatedAssessments)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ActionChip(
                        label: Text(a['title'] as String? ?? a['id'] as String),
                        onPressed: () {
                          _controller.text = a['id'] as String;
                          _load();
                        },
                      ),
                    ),
                ],
              ),
            ),
          const SizedBox(height: 8),
          Expanded(child: _body()),
        ],
      ),
    );
  }

  Widget _body() {
    if (_future == null) {
      return const EmptyState(
        icon: Icons.insights_outlined,
        title: 'Class insights',
        message: 'Enter the ID of an assessment whose answer sheets have been evaluated.',
      );
    }
    return FutureBuilder<ClassInsights>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const LoadingIndicator(message: 'Aggregating class performance…');
        }
        if (snap.hasError) {
          return ErrorDisplay(message: '${snap.error}', onRetry: _load);
        }
        final ci = snap.data!;
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          children: [
            AppCard(
              color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.35),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(ci.headline,
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 6),
                  Text('${ci.students} students · class average ${ci.averagePercentage}%'),
                ],
              ),
            ),
            if (ci.sharedMistakes.isNotEmpty) ...[
              const SectionHeader(
                  title: 'Shared mistakes',
                  subtitle: 'The same marking point missed by multiple students'),
              ...ci.sharedMistakes.map((m) => AppCard(
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(m.markingPoint,
                                  style: const TextStyle(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 2),
                              Text(m.conceptName,
                                  style: TextStyle(
                                      fontSize: 12,
                                      color: Theme.of(context).colorScheme.onSurfaceVariant)),
                            ],
                          ),
                        ),
                        ChipTag(
                            label: '${m.percentage.round()}% of class',
                            color: Colors.deepOrange),
                      ],
                    ),
                  )),
            ],
            const SectionHeader(
                title: 'Recommended actions',
                subtitle: 'Ranked by how much class learning is at stake'),
            ...ci.concepts.map((c) => AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(c.conceptName,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600, fontSize: 15)),
                          ),
                          ChipTag(
                            label: '${(c.classAccuracy * 100).round()}%',
                            color: c.classAccuracy < 0.6 ? Colors.red : Colors.green,
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(c.recommendation),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.schedule, size: 14),
                          const SizedBox(width: 4),
                          Text('~${c.estimatedMinutes} min',
                              style: const TextStyle(fontSize: 12)),
                          const SizedBox(width: 16),
                          if (c.atRiskStudents.isNotEmpty)
                            Expanded(
                              child: Text(
                                'at risk: ${c.atRiskStudents.map(LocalStore.instance.studentName).join(", ")}',
                                style: TextStyle(
                                    fontSize: 12,
                                    color: Theme.of(context).colorScheme.onSurfaceVariant),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                )),
          ],
        );
      },
    );
  }
}
