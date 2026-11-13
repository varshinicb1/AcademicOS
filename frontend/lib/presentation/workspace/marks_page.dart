import 'package:flutter/material.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'teacher_homework.dart' show TeachingContext;
import '../shared/readable.dart';
import 'strings.dart';

/// Marks entry for a paper sat on paper (EX-8): one section's students by
/// the paper's questions, typed cell by cell, then the analysis by question,
/// chapter, topic and class.
class MarksPage extends StatefulWidget {
  final String paperId;

  /// The paper's class, when the page that opened this knows it; read from
  /// the paper otherwise. Only that class's sections are offered.
  final int? grade;
  const MarksPage({super.key, required this.paperId, this.grade});

  @override
  State<MarksPage> createState() => _MarksPageState();
}

class _MarksPageState extends State<MarksPage> {
  TeachingContext? _ctx;
  late int? _grade = widget.grade;
  String? _section;
  Map<String, dynamic>? _grid;
  Map<String, dynamic>? _analysis;
  final Map<(String, String), TextEditingController> _cells = {};
  final Set<String> _absent = {};
  final Set<String> _dirty = {};
  String? _error;
  bool _saving = false;

  /// Save was pressed with a bad mark on the grid; the list of bad marks
  /// says so until they are fixed.
  bool _saveRefused = false;

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) => setState(() => _ctx = c), onError: (e) => setState(() => _error = serverErrorMessage(e)));
    if (_grade == null) {
      Ops.map('/papers/${widget.paperId}').then((p) {
        final grade = (p['metadata'] as Map?)?['grade'];
        if (mounted && grade is int) setState(() => _grade = grade);
      }, onError: (e) {
        // Every section stays on offer; say why the list is not narrowed.
        if (mounted) setState(() => _error = trf("Could not read the paper's class: {problem}", {'problem': serverErrorMessage(e)}));
      });
    }
  }

  @override
  void dispose() {
    for (final c in _cells.values) {
      c.dispose();
    }
    super.dispose();
  }

  /// The sections that can have sat this paper: its class's ("10-A" for a
  /// class 10 paper). 6-A was offered for a class 10 paper (QA P-20).
  Map<String, String> _sections(TeachingContext ctx) {
    final g = _grade;
    if (g == null) return ctx.sectionLabels;
    return {
      for (final e in ctx.sectionLabels.entries)
        if (e.value.startsWith('$g-')) e.key: e.value,
    };
  }

  Future<void> _load() async {
    if (_section == null) return;
    try {
      final g = await Ops.map('/papers/${widget.paperId}/marks', query: {'sectionId': _section});
      final a = await Ops.map('/papers/${widget.paperId}/analysis', query: {'sectionId': _section});
      for (final c in _cells.values) {
        c.dispose();
      }
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

  static String _number(num v) => v == v.roundToDouble() ? '${v.toInt()}' : '$v';

  /// What is wrong with one typed cell, naming it the way the grid's header
  /// and the class register do -- "A3 for Asha: 5 is more than 4" -- or null
  /// when it is empty or a mark the question can take. The server named an
  /// internal question id, and only once Save was pressed (QA P-20, P-19).
  String? _cellProblem(Map row, Map question) {
    if (_absent.contains(row['studentId'])) return null;
    final text = _cells[(row['studentId'] as String, question['questionId'] as String)]?.text.trim() ?? '';
    if (text.isEmpty) return null;
    final where = trf('{question} for {student}', {'question': question['number'], 'student': row['name']});
    final v = double.tryParse(text);
    if (v == null) return trf('{where}: "{text}" is not a number', {'where': where, 'text': text});
    final max = (question['maxMarks'] as num?) ?? 0;
    if (v < 0) return trf('{where}: marks cannot be below 0', {'where': where});
    if (v > max) return trf('{where}: {marks} is more than {max}', {'where': where, 'marks': _number(v), 'max': _number(max)});
    return null;
  }

  /// Every bad cell on the grid, in reading order.
  List<String> _problems() {
    final g = _grid;
    if (g == null) return const [];
    final questions = (g['questions'] as List).cast<Map>();
    return [
      for (final r in (g['rows'] as List).cast<Map>())
        for (final q in questions)
          if (_cellProblem(r, q) case final problem?) problem,
    ];
  }

  Future<void> _save() async {
    // Caught here, before anything is sent: the server refused the whole
    // save for one cell and named it by an internal id.
    if (_problems().isNotEmpty) {
      setState(() => _saveRefused = true);
      return;
    }
    final entries = <Map<String, dynamic>>[];
    for (final e in _cells.entries) {
      final (sid, qid) = e.key;
      if (!_dirty.contains(sid) || _absent.contains(sid) || e.value.text.trim().isEmpty) continue;
      entries.add({'studentId': sid, 'questionId': qid, 'marks': double.parse(e.value.text.trim())});
    }
    final rows = (_grid!['rows'] as List).cast<Map>();
    final absent = [for (final r in rows) if (_absent.contains(r['studentId']) && r['absent'] != true) r['studentId']];
    final present = [for (final r in rows) if (!_absent.contains(r['studentId']) && r['absent'] == true) r['studentId']];
    setState(() {
      _saving = true;
      _saveRefused = false;
      _error = null;
    });
    try {
      final saved = await Ops.send('PUT', '/papers/${widget.paperId}/marks', query: {'sectionId': _section},
          body: {'entries': entries, 'absent': absent, 'present': present}, label: 'Marks for this paper');
      await _load();
      // Students without parental consent are left out by name, and the
      // rest are saved (v3 audit N-4-5: one of them refused the whole class).
      final missing = saved is Map ? ((saved['withoutConsent'] as List?) ?? const []).cast<String>() : const <String>[];
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            duration: Duration(seconds: missing.isEmpty ? 4 : 10),
            content: Text(missing.isEmpty
                ? tr('Marks saved')
                : trf('Marks saved, except for {names}: no parental consent is on file yet. '
                    'Record it under Classes, then enter their marks.', {'names': missing.join(', ')}))));
      }
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
    final problems = _problems();
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(tr('Marks')),
          actions: [
            if (g != null)
              FilledButton(onPressed: _saving || _dirty.isEmpty && _absentChanged() == 0 ? null : _save,
                  child: Text(tr('Save'))),
            const SizedBox(width: 12),
          ],
          bottom: TabBar(tabs: [Tab(text: tr('Enter')), Tab(text: tr('Analysis'))]),
        ),
        body: Column(children: [
          if (ctx != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: _sections(ctx).isEmpty
                  ? Text(
                      trf('Your school has no Class {grade} section set up, so marks for this paper '
                          'cannot be entered yet.', {'grade': _grade}),
                      key: const ValueKey('no-sections'))
                  : DropdownButton<String>(
                      key: const ValueKey('marks-section'),
                      value: _sections(ctx).containsKey(_section) ? _section : null,
                      hint: Text(tr('Choose a section')),
                      items: [
                        for (final e in _sections(ctx).entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
                      ],
                      onChanged: (v) {
                        setState(() => _section = v);
                        _load();
                      },
                    ),
            ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(_error!, key: const ValueKey('marks-error'), style: TextStyle(color: theme.colorScheme.error)),
            ),
          // Named as they are typed, not only when Save is pressed.
          if (problems.isNotEmpty)
            Padding(
              key: const ValueKey('marks-problems'),
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                if (_saveRefused)
                  Text(problems.length == 1
                          ? tr('Fix this before saving:')
                          : trf('Fix these {n} marks before saving:', {'n': problems.length}),
                      style: TextStyle(color: theme.colorScheme.error, fontWeight: FontWeight.w600)),
                for (final p in problems.take(3)) Text(p, style: TextStyle(color: theme.colorScheme.error)),
                if (problems.length > 3)
                  Text(trf('and {n} more, outlined in the grid', {'n': problems.length - 3}),
                      style: TextStyle(color: theme.colorScheme.error)),
              ]),
            ),
          Expanded(
            child: g == null
                ? EmptyState(icon: Icons.grid_on, title: tr('Choose a section'),
                    message: tr('Its students and this paper\'s questions appear as a grid.'))
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
            DataColumn(label: Text(tr('Student'))),
            DataColumn(label: Text(tr('Absent'))),
            for (final q in questions) DataColumn(label: Text('${q['number']}\n/${q['maxMarks']}')),
            DataColumn(label: Text(tr('Total'))),
          ],
          rows: [
            for (final r in rows)
              DataRow(cells: [
                DataCell(Text(r['name'])),
                DataCell(Semantics(
                  label: trf('{student} absent', {'student': r['name']}),
                  child: Checkbox(
                    value: _absent.contains(r['studentId']),
                    onChanged: (on) => setState(() => on == true ? _absent.add(r['studentId']) : _absent.remove(r['studentId'])),
                  ),
                )),
                for (final q in questions)
                  DataCell(SizedBox(
                    width: 48,
                    // Each cell says which question and whose mark it is: a
                    // screen reader heard 38 unnamed fields per row (QA P-28).
                    child: Semantics(
                      label: trf('{question} for {student}, out of {max}', {'question': q['number'], 'student': r['name'], 'max': q['maxMarks']}),
                      child: TextField(
                        key: ValueKey('mark-${r['studentId']}-${q['questionId']}'),
                        controller: _cells[(r['studentId'] as String, q['questionId'] as String)],
                        enabled: !_absent.contains(r['studentId']),
                        keyboardType: TextInputType.number,
                        // A bad mark is outlined as it is typed; the line
                        // above the grid says what is wrong with it.
                        decoration: InputDecoration(
                          isDense: true,
                          errorText: _cellProblem(r, q) == null ? null : '',
                          errorStyle: const TextStyle(height: 0, fontSize: 0),
                        ),
                        onChanged: (_) => setState(() => _dirty.add(r['studentId'])),
                      ),
                    ),
                  )),
                DataCell(Text(_totalText(r), key: ValueKey('total-${r['studentId']}'))),
              ]),
          ],
        ),
      ),
    );
  }

  /// A row is graded only once every question has a mark. A partly entered
  /// row has no total and reads "Incomplete", not a grade (v3 audit N-2-10:
  /// 5 of 38 cells read 5.0 and band E).
  static String _totalText(Map r) {
    if (r['total'] != null) return '${r['total']} (${r['band']})';
    final marks = (r['marks'] as Map?) ?? const {};
    return r['absent'] != true && marks.isNotEmpty ? tr('Incomplete') : '-';
  }

  Widget _analysisView() {
    final a = _analysis;
    if (a == null) return const LoadingIndicator();
    final s = Map<String, dynamic>.from(a['summary'] as Map);
    final theme = Theme.of(context);
    return ListView(padding: const EdgeInsets.all(16), children: [
      Wrap(spacing: 12, runSpacing: 12, children: [
        StatCard(label: tr('Class average'), value: s['meanPercent'] == null ? '-' : '${s['meanPercent']}%', icon: Icons.bar_chart, color: theme.colorScheme.primary),
        StatCard(label: tr('Median'), value: s['medianPercent'] == null ? '-' : '${s['medianPercent']}%', icon: Icons.align_vertical_center, color: theme.colorScheme.primary),
        StatCard(label: tr('Absent'), value: trf('{n} of {total}', {'n': s['absent'], 'total': s['students']}), icon: Icons.person_off_outlined, color: theme.colorScheme.outline),
      ]),
      if (((s['incomplete'] as num?) ?? 0) > 0)
        Padding(padding: const EdgeInsets.only(top: 8),
            child: Text(
                trf('Incomplete: {n}, left out of the average and the grade bands until every question has a mark',
                    {'n': s['incomplete']}),
                key: const ValueKey('incomplete-note'))),
      const SizedBox(height: 12),
      Text(tr('Grade bands'), style: theme.textTheme.titleSmall),
      Wrap(spacing: 6, children: [
        for (final e in Map<String, dynamic>.from(s['bands'] as Map).entries) Chip(label: Text('${e.key}: ${e.value}')),
      ]),
      if ((a['weakest'] as List).isNotEmpty)
        Padding(padding: const EdgeInsets.only(top: 12),
            child: Text(trf('Re-teach first: {chapters}', {'chapters': (a['weakest'] as List).join(', ')}), style: theme.textTheme.titleSmall)),
      SectionHeader(title: tr('By question')),
      for (final q in (a['questions'] as List).cast<Map>())
        ListTile(
          dense: true,
          title: Text('${q['number']}${q['chapter'] != null ? ' · ${q['chapter']}' : ''}'),
          subtitle: Text(trf('{n} marked · mean {mean} of {max}', {'n': q['attempted'], 'mean': q['mean'] ?? '-', 'max': q['maxMarks']})),
          trailing: SizedBox(width: 120, child: LinearProgressIndicator(value: (q['facility'] as num?)?.toDouble() ?? 0)),
        ),
      ..._groups(tr('By chapter'), a['chapters'] as List?),
      ..._groups(tr('By topic'), a['topics'] as List?),
    ]);
  }

  /// Chapters or topics, weakest first as the server sorts them.
  static List<Widget> _groups(String title, List? groups) => [
        if (groups != null && groups.isNotEmpty) ...[
          SectionHeader(title: title),
          for (final c in groups.cast<Map>())
            ListTile(dense: true, title: Text(c['name']), subtitle: Text(plural((c['questions'] as num).toInt(), 'question')),
                trailing: Text(c['facility'] == null ? '-' : '${((c['facility'] as num) * 100).round()}%')),
        ],
      ];
}
