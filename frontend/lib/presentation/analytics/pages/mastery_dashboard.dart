import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Pillar 3 — Learning Intelligence: what the student actually knows.
class MasteryDashboard extends StatefulWidget {
  final String? studentId;
  const MasteryDashboard({super.key, this.studentId});

  @override
  State<MasteryDashboard> createState() => _MasteryDashboardState();
}

class _MasteryDashboardState extends State<MasteryDashboard> {
  late Future<StudentMastery> _future;
  late String _studentId;

  // Real bug found on-device: this used to default to a hardcoded
  // 'stu_meera' with a 3-item dropdown of fake names (Asha/Ravi/Meera)
  // that matched no real student -- a teacher testing the demo saw "No
  // knowledge yet" with no way to pick any of the 10 real evaluated demo
  // students. LocalStore.allStudentIdsWithMastery() already existed but
  // was never wired up here.
  List<String> get _realStudentIds => LocalStore.instance.allStudentIdsWithMastery();

  @override
  void initState() {
    super.initState();
    final real = _realStudentIds;
    _studentId = widget.studentId ?? (real.isNotEmpty ? real.first : 'stu_meera');
    _future = GetIt.I<PillarApi>().knowledge(_studentId);
  }

  void _reload(String studentId) {
    setState(() {
      _studentId = studentId;
      _future = GetIt.I<PillarApi>().knowledge(studentId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // Reached via a nested route ('/analytics/mastery' under '/analytics'),
        // same canPop quirk fixed for the Planner — see shell.dart's
        // forceShellLeading docstring.
        leading: forceShellLeading(context),
        title: const Text('Mastery'),
        actions: [
          PopupMenuButton<String>(
            initialValue: _studentId,
            onSelected: _reload,
            itemBuilder: (_) {
              final real = _realStudentIds;
              return [
                for (final id in real)
                  PopupMenuItem(value: id, child: Text(LocalStore.instance.studentName(id))),
                if (real.isEmpty) const PopupMenuItem(value: 'stu_meera', child: Text('Meera (no real data yet)')),
              ];
            },
            // Real accessibility bug found by audit: PopupMenuButton doesn't
            // enforce a minimum tap-target size when given a `child:` --
            // that only happens on its default IconButton path -- so this
            // was ~24-28px tall (well under the 48px minimum) despite being
            // the primary control for switching students on this screen.
            child: SizedBox(
              height: 48,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(LocalStore.instance.studentName(_studentId)),
                    const Icon(Icons.arrow_drop_down),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
      body: FutureBuilder<StudentMastery>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Loading knowledge state…');
          }
          if (snap.hasError) {
            return ErrorDisplay(
              message: 'Could not load mastery: ${snap.error}',
              onRetry: () => _reload(_studentId),
            );
          }
          final m = snap.data!;
          if (m.concepts.isEmpty) {
            return const EmptyState(
              icon: Icons.psychology_outlined,
              title: 'No knowledge yet',
              message: 'Evaluate an answer sheet for this student to build their mastery profile.',
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              AppCard(
                child: Row(
                  children: [
                    ProgressRing(
                      progress: m.overallMastery,
                      size: 72,
                      child: Text('${(m.overallMastery * 100).round()}%',
                          style: const TextStyle(fontWeight: FontWeight.w700)),
                    ),
                    const SizedBox(width: 20),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Overall mastery',
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 4),
                          Text('${m.concepts.length} concepts with assessment evidence'),
                          if (m.weakConcepts.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            // Real accessibility bug found by audit: these
                            // chips carried no text beyond the bare concept
                            // name -- red tint was the ONLY signal these are
                            // the "weak" ones, invisible to a color-blind
                            // teacher or a screen reader (which just reads
                            // the concept name, same as any other list).
                            Text('Weak concepts',
                                style: Theme.of(context).textTheme.labelSmall
                                    ?.copyWith(color: Theme.of(context).colorScheme.error)),
                            const SizedBox(height: 4),
                            Wrap(
                              spacing: 6,
                              runSpacing: 4,
                              children: m.weakConcepts
                                  .map((c) => ChipTag(label: c, color: Colors.red.shade400))
                                  .toList(),
                            ),
                            const SizedBox(height: 12),
                            FilledButton.icon(
                              onPressed: () => context.push('/practice/$_studentId'),
                              icon: const Icon(Icons.auto_awesome, size: 18),
                              label: const Text('Generate targeted practice'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SectionHeader(title: 'Concepts', subtitle: 'Mastery blends accuracy, recency, retention and higher-Bloom transfer'),
              ...m.concepts.map(_conceptTile),
            ],
          );
        },
      ),
    );
  }

  Widget _conceptTile(ConceptMastery c) {
    final color = c.mastery >= 0.85
        ? Colors.green
        : c.mastery >= 0.55
            ? Colors.orange
            : Colors.red;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(c.conceptName,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
              ),
              ChipTag(label: c.status, color: color),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: c.mastery,
              minHeight: 8,
              backgroundColor: color.withValues(alpha: 0.15),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'mastery ${(c.mastery * 100).round()}%  ·  retention ${(c.retention * 100).round()}%  ·  ${c.evidenceCount} attempts',
            style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}
