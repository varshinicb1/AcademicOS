import 'package:flutter/material.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'teacher_homework.dart' show TeachingContext;
import 'strings.dart';
import '../shared/widgets/shell.dart';

/// A section's progress (TA-6): per chapter, how many students are at each
/// status; the students who need help. For the section's teachers and the
/// principal only.
class ClassProgressPage extends StatefulWidget {
  const ClassProgressPage({super.key});

  @override
  State<ClassProgressPage> createState() => _ClassProgressPageState();
}

class _ClassProgressPageState extends State<ClassProgressPage> {
  TeachingContext? _ctx;
  String? _section;
  Map<String, dynamic>? _data;
  String? _error;

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) {
      if (!mounted) return;
      setState(() => _ctx = c);
      // Open on the first class: the page showed only the class chips and a
      // blank body until one was picked (E2E run, 2026-10-01).
      final first = _classes(c);
      if (first.isNotEmpty && _section == null) _load(first.first);
    }, onError: (Object e) => setState(() => _error = serverErrorMessage(e)));
  }

  /// The sections this caller follows, in label order: every section for
  /// the principal, the ones they teach for a teacher.
  List<String> _classes(TeachingContext ctx) {
    final ids = CurrentSession.role == 'principal'
        ? ctx.sectionLabels.keys.toSet()
        : {for (final a in ctx.allocations) a['sectionId'] as String};
    return ids.toList()..sort((a, b) => (ctx.sectionLabels[a] ?? a).compareTo(ctx.sectionLabels[b] ?? b));
  }

  Future<void> _load(String sectionId) async {
    if (!mounted) return;
    setState(() {
      _section = sectionId;
      _data = null;
      _error = null;
    });
    try {
      final d = await Ops.map('/sections/$sectionId/progress');
      if (mounted && _section == sectionId) setState(() => _data = d);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ctx = _ctx;
    final mine = ctx == null ? const <String>[] : _classes(ctx);
    final d = _data;
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Class progress'))),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (ctx != null)
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final sid in mine)
              ChoiceChip(label: Text(ctx.sectionLabels[sid] ?? sid), selected: _section == sid, onSelected: (_) => _load(sid)),
          ]),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 12),
            child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
        if (_section != null && d == null && _error == null) const SizedBox(height: 120, child: LoadingIndicator()),
        if (d != null) ...[
          const SizedBox(height: 12),
          Text('${d['sectionName']} · ${d['students']} students', style: theme.textTheme.titleMedium),
          if ((d['chapters'] as List).isEmpty)
            const Padding(padding: EdgeInsets.only(top: 12),
                child: Text('No marked homework, tests or practice yet for this class.')),
          if ((d['needingHelp'] as List).isNotEmpty) ...[
            SectionHeader(title: tr('Students who need help'), subtitle: 'Visible to you and the principal only'),
            for (final s in (d['needingHelp'] as List).cast<Map>())
              ListTile(dense: true, title: Text(s['name']),
                  subtitle: Text('Needs work: ${(s['needsWork'] as List).join(', ')}')),
          ],
          SectionHeader(title: tr('By chapter'), subtitle: 'Weakest first'),
          for (final c in (d['chapters'] as List).cast<Map>())
            ExpansionTile(
              title: Text('${c['subject']} · ${c['name']}'),
              subtitle: Text(_counts(Map<String, dynamic>.from(c['counts'] as Map), c['studentsWithEvidence'] as int)),
              trailing: SizedBox(width: 110, child: LinearProgressIndicator(value: (c['meanMastery'] as num?)?.toDouble() ?? 0)),
              children: [
                for (final t in (c['topics'] as List).cast<Map>())
                  ListTile(dense: true, title: Text(t['name']),
                      subtitle: Text(_counts(Map<String, dynamic>.from(t['counts'] as Map), t['studentsWithEvidence'] as int)),
                      trailing: SizedBox(width: 90, child: LinearProgressIndicator(value: (t['meanMastery'] as num?)?.toDouble() ?? 0))),
              ],
            ),
        ],
      ]),
    );
  }

  String _counts(Map<String, dynamic> c, int total) =>
      '$total students · ${c['mastered']} mastered · ${c['developing']} getting there · '
      '${c['needs_work']} need work · ${c['early']} too early';
}
