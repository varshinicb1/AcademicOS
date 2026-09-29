import 'package:flutter/material.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'teacher_homework.dart' show TeachingContext;
import 'strings.dart';

/// Marks entry for a paper sat on paper (EX-8): one section's students by
/// the paper's questions, typed cell by cell, then the analysis by question,
/// chapter and class.
class MarksPage extends StatefulWidget {
  final String paperId;
  const MarksPage({super.key, required this.paperId});

  @override
  State<MarksPage> createState() => _MarksPageState();
}

class _MarksPageState extends State<MarksPage> {
  TeachingContext? _ctx;
  String? _section;
  Map<String, dynamic>? _grid;
  Map<String, dynamic>? _analysis;
  final Map<(String, String), TextEditingController> _cells = {};
  final Set<String> _absent = {};
  final Set<String> _dirty = {};
  String? _error;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) => setState(() => _ctx = c), onError: (e) => setState(() => _error = serverErrorMessage(e)));
  }

  Future<void> _load() async {
    if (_section == null) return;
    try {
      final g = await Ops.map('/papers/${widget.paperId}/marks', query: {'sectionId': _section});
      final a = await Ops.map('/papers/${widget.paperId}/analysis', query: {'sectionId': _section});
      _cells.clear();
      _absent.clear();
      _dirty.clear();
      for (final r in (g['rows'] as List).cast<Map>()) {
        if (r['absent'] == true) _absent.add(r['studentId']);
        final marks = Map<String, dynamic>.from(r['marks'] as Map);
        for (final q in (g['questions'] as List).cast<Map>()) {
          final v = marks[q['questionId']];
          _cells[(r['studentId'] as String, q['questionId'] as String)] =
              TextEditingController(text: v == null ? '' : (v as num).toString());
        }
      }
      setState(() {
        _grid = g;
        _analysis = a;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _save() async {
    final entries = <Map<String, dynamic>>[];
    for (final e in _cells.entries) {
      final (sid, qid) = e.key;
      if (!_dirty.contains(sid) || _absent.contains(sid) || e.value.text.trim().isEmpty) continue;
      final v = double.tryParse(e.value.text.trim());
      if (v == null) {
        setState(() => _error = 'Marks must be numbers');
        return;
      }
      entries.add({'studentId': sid, 'questionId': qid, 'marks': v});
    }
    final rows = (_grid!['rows'] as List).cast<Map>();
    final absent = [for (final r in rows) if (_absent.contains(r['studentId']) && r['absent'] != true) r['studentId']];
    final present = [for (final r in rows) if (!_absent.contains(r['studentId']) && r['absent'] == true) r['studentId']];
    setState(() => _saving = true);
    try {
      await Ops.send('PUT', '/papers/${widget.paperId}/marks', query: {'sectionId': _section},
          body: {'entries': entries, 'absent': absent, 'present': present}, label: 'Marks for this paper');
      await _load();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Marks saved')));
    } on OpsQueued catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ctx = _ctx;
    final g = _grid;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Marks'),
          actions: [
            if (g != null)
              FilledButton(onPressed: _saving || _dirty.isEmpty && _absentChanged() == 0 ? null : _save,
                  child: Text(tr('Save'))),
            const SizedBox(width: 12),
          ],
          bottom: const TabBar(tabs: [Tab(text: 'Enter'), Tab(text: 'Analysis')]),
        ),
        body: Column(children: [
          if (ctx != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: DropdownButton<String>(
                value: _section,
                hint: const Text('Choose a section'),
                items: [for (final e in ctx.sectionLabels.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
                onChanged: (v) {
                  setState(() => _section = v);
                  _load();
                },
              ),
            ),
          if (_error != null) Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          Expanded(
            child: g == null
                ? const EmptyState(icon: Icons.grid_on, title: 'Choose a section',
                    message: 'Its students and this paper\'s questions appear as a grid.')
                : TabBarView(children: [_gridView(g), _analysisView()]),
          ),
        ]),
      ),
    );
  }

  int _absentChanged() {
    if (_grid == null) return 0;
    return (_grid!['rows'] as List).cast<Map>().where((r) => (r['absent'] == true) != _absent.contains(r['studentId'])).length;
  }

  Widget _gridView(Map<String, dynamic> g) {
    final questions = (g['questions'] as List).cast<Map>();
    final rows = (g['rows'] as List).cast<Map>();
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SingleChildScrollView(
        child: DataTable(
          columnSpacing: 12,
          columns: [
            const DataColumn(label: Text('Student')),
            const DataColumn(label: Text('Absent')),
            for (final q in questions) DataColumn(label: Text('${q['number']}\n/${q['maxMarks']}')),
            const DataColumn(label: Text('Total')),
          ],
          rows: [
            for (final r in rows)
              DataRow(cells: [
                DataCell(Text(r['name'])),
                DataCell(Checkbox(
                  value: _absent.contains(r['studentId']),
                  onChanged: (on) => setState(() => on == true ? _absent.add(r['studentId']) : _absent.remove(r['studentId'])),
                )),
                for (final q in questions)
                  DataCell(SizedBox(
                    width: 48,
                    child: TextField(
                      controller: _cells[(r['studentId'] as String, q['questionId'] as String)],
                      enabled: !_absent.contains(r['studentId']),
                      keyboardType: TextInputType.number,
                      onChanged: (_) => setState(() => _dirty.add(r['studentId'])),
                    ),
                  )),
                DataCell(Text(r['total'] == null ? '-' : '${r['total']} (${r['band']})')),
              ]),
          ],
        ),
      ),
    );
  }

  Widget _analysisView() {
    final a = _analysis;
    if (a == null) return const LoadingIndicator();
    final s = Map<String, dynamic>.from(a['summary'] as Map);
    final theme = Theme.of(context);
    return ListView(padding: const EdgeInsets.all(16), children: [
      Wrap(spacing: 12, runSpacing: 12, children: [
        StatCard(label: 'Class average', value: s['meanPercent'] == null ? '-' : '${s['meanPercent']}%', icon: Icons.bar_chart, color: theme.colorScheme.primary),
        StatCard(label: 'Median', value: s['medianPercent'] == null ? '-' : '${s['medianPercent']}%', icon: Icons.align_vertical_center, color: theme.colorScheme.primary),
        StatCard(label: 'Absent', value: '${s['absent']} of ${s['students']}', icon: Icons.person_off_outlined, color: theme.colorScheme.outline),
      ]),
      const SizedBox(height: 12),
      Text('Grade bands', style: theme.textTheme.titleSmall),
      Wrap(spacing: 6, children: [
        for (final e in Map<String, dynamic>.from(s['bands'] as Map).entries) Chip(label: Text('${e.key}: ${e.value}')),
      ]),
      if ((a['weakest'] as List).isNotEmpty)
        Padding(padding: const EdgeInsets.only(top: 12),
            child: Text('Re-teach first: ${(a['weakest'] as List).join(', ')}', style: theme.textTheme.titleSmall)),
      const SectionHeader(title: 'By question'),
      for (final q in (a['questions'] as List).cast<Map>())
        ListTile(
          dense: true,
          title: Text('${q['number']}${q['chapter'] != null ? ' · ${q['chapter']}' : ''}'),
          subtitle: Text('${q['attempted']} marked · mean ${q['mean'] ?? '-'} of ${q['maxMarks']}'),
          trailing: SizedBox(width: 120, child: LinearProgressIndicator(value: (q['facility'] as num?)?.toDouble() ?? 0)),
        ),
      if ((a['chapters'] as List).isNotEmpty) ...[
        SectionHeader(title: tr('By chapter')),
        for (final c in (a['chapters'] as List).cast<Map>())
          ListTile(dense: true, title: Text(c['name']), subtitle: Text('${c['questions']} questions'),
              trailing: Text(c['facility'] == null ? '-' : '${((c['facility'] as num) * 100).round()}%')),
      ],
    ]);
  }
}

/// Asks a colleague to review a paper (EX-6), from the paper's own page.
Future<void> requestReview(BuildContext context, String assessmentId) async {
  final staff = await Ops.list('/staff');
  if (!context.mounted) return;
  String? reviewer;
  final note = TextEditingController();
  final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
    title: const Text('Send for review'),
    content: SizedBox(width: 420, child: Column(mainAxisSize: MainAxisSize.min, children: [
      DropdownButtonFormField<String>(
        initialValue: reviewer,
        decoration: const InputDecoration(labelText: 'Reviewer (HOD or a colleague)'),
        items: [for (final s in staff) DropdownMenuItem(value: s['id'] as String, child: Text(s['name'] as String))],
        onChanged: (v) => set(() => reviewer = v),
      ),
      TextField(controller: note, decoration: const InputDecoration(labelText: 'Note (optional)')),
    ])),
    actions: [
      TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
      FilledButton(onPressed: reviewer == null ? null : () => Navigator.pop(ctx, true), child: const Text('Send')),
    ],
  )));
  if (ok != true || !context.mounted) return;
  try {
    await Ops.post('/assessments/$assessmentId/review-request',
        body: {'reviewerId': reviewer, if (note.text.trim().isNotEmpty) 'note': note.text.trim()});
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Sent for review; the reviewer has been told')));
    }
  } catch (e) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
  }
}
