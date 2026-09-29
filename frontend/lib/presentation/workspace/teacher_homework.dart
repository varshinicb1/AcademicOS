import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../data/datasources/api/api_error.dart';
import '../../core/session/current_session.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';

/// What a teacher teaches this year, for pickers: sections, subjects and
/// the allocations joining them (the principal sees all of them).
class TeachingContext {
  final String yearId;
  final Map<String, String> sectionLabels;      // section id -> "10-B"
  final Map<String, String> subjectNames;       // subject id -> "Science"
  final List<Map<String, dynamic>> allocations; // the caller's (or all, for the principal)

  TeachingContext(this.yearId, this.sectionLabels, this.subjectNames, this.allocations);

  static Future<TeachingContext> load() async {
    final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
    if (years.isEmpty) throw OpsError(409, 'Your school has no academic year set up yet.');
    years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
    final yearId = years.last['id'] as String;
    final sections = await Ops.list('/curriculum/academic-years/$yearId/sections');
    final labels = {for (final s in sections) s['id'] as String: '${s['gradeNumber']}-${s['name']}'};
    final gradeIds = {for (final s in sections) s['gradeId'] as String};
    final names = <String, String>{};
    for (final g in gradeIds) {
      for (final subj in await Ops.list('/curriculum/grades/$g/subjects')) {
        names[subj['id'] as String] = subj['name'] as String;
      }
    }
    var allocs = await Ops.list('/curriculum/academic-years/$yearId/allocations');
    if (CurrentSession.role != 'principal') {
      allocs = allocs.where((a) => a['teacherId'] == CurrentSession.userId).toList();
    }
    return TeachingContext(yearId, labels, names, allocs);
  }
}

class TeacherHomeworkPage extends StatefulWidget {
  const TeacherHomeworkPage({super.key});

  @override
  State<TeacherHomeworkPage> createState() => _TeacherHomeworkPageState();
}

class _TeacherHomeworkPageState extends State<TeacherHomeworkPage> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/homework');

  void _reload() => setState(() { _future = Ops.list('/homework'); });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Homework')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final made = await showDialog<bool>(context: context, builder: (_) => const _CreateHomeworkDialog());
          if (made == true) _reload();
        },
        icon: const Icon(Icons.add),
        label: const Text('Set homework'),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: snap.error.toString(), onRetry: _reload);
          final items = snap.data!;
          if (items.isEmpty) {
            return const EmptyState(icon: Icons.assignment_outlined, title: 'No homework yet',
                message: 'Set homework from the question bank for the sections you teach.');
          }
          return ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 96), children: [
            for (final h in items)
              AppCard(
                margin: const EdgeInsets.only(bottom: 10),
                onTap: () => context.push('/school/homework/${h['id']}').then((_) => _reload()),
                child: Row(children: [
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(h['title'], style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Text('${h['subjectName']} · ${(h['sectionNames'] as List).join(', ')} · due ${h['dueDate']}',
                        style: theme.textTheme.bodySmall),
                  ])),
                  ChipTag(label: '${h['submitted']}/${h['students']} in · ${h['graded']} marked'),
                  const SizedBox(width: 8),
                  if (h['status'] != 'published') ChipTag(label: h['status']),
                ]),
              ),
          ]);
        },
      ),
    );
  }
}

class _CreateHomeworkDialog extends StatefulWidget {
  const _CreateHomeworkDialog();

  @override
  State<_CreateHomeworkDialog> createState() => _CreateHomeworkDialogState();
}

class _CreateHomeworkDialogState extends State<_CreateHomeworkDialog> {
  TeachingContext? _ctx;
  String? _error;
  String? _subjectId;
  final Set<String> _sections = {};
  final _title = TextEditingController();
  final _instructions = TextEditingController();
  DateTime _due = DateTime.now().add(const Duration(days: 2));
  Map<String, dynamic>? _suggestion;
  final Set<String> _chapters = {};
  final Set<String> _questions = {};
  int _count = 5;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) => setState(() => _ctx = c), onError: (e) => setState(() => _error = serverErrorMessage(e)));
  }

  List<Map<String, dynamic>> get _mine =>
      _ctx!.allocations.where((a) => a['subjectId'] == _subjectId).toList();

  Future<void> _suggest() async {
    if (_subjectId == null || _sections.isEmpty) return;
    setState(() => _busy = true);
    try {
      final s = await Ops.map('/homework/suggestion', query: {'sectionId': _sections.first, 'subjectId': _subjectId});
      setState(() {
        _suggestion = s;
        _chapters
          ..clear()
          ..addAll(s['lessonFound'] == true && s['note'] == null
              ? (s['bankChapters'] as List).map((c) => c['chapterId'] as String)
              : const <String>[]);
        _questions
          ..clear()
          ..addAll((s['questions'] as List).take(5).map((q) => q['id'] as String));
        if (_title.text.isEmpty && s['subtopicName'] != null) _title.text = 'Practice: ${s['subtopicName']}';
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    } finally {
      setState(() => _busy = false);
    }
  }

  Future<void> _create() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Ops.post('/homework', body: {
        'subjectId': _subjectId, 'sectionIds': _sections.toList(), 'title': _title.text.trim(),
        'instructions': _instructions.text.trim(), 'dueDate': isoDate(_due),
        'questionIds': _questions.toList(), 'chapterIds': _chapters.toList(), 'count': _count,
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ctx = _ctx;
    final theme = Theme.of(context);
    final subjects = ctx == null ? <String>{} : {for (final a in ctx.allocations) a['subjectId'] as String};
    return AlertDialog(
      title: const Text('Set homework'),
      content: SizedBox(
        width: 620,
        child: ctx == null
            ? (_error != null ? Text(_error!) : const SizedBox(height: 120, child: LoadingIndicator()))
            : SingleChildScrollView(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                  if (subjects.isEmpty)
                    const Text('You have no teaching allocations this year. Ask the principal to allocate your subjects.'),
                  DropdownButtonFormField<String>(
                    initialValue: _subjectId,
                    decoration: const InputDecoration(labelText: 'Subject'),
                    items: [for (final s in subjects)
                      DropdownMenuItem(value: s, child: Text(ctx.subjectNames[s] ?? s))],
                    onChanged: (v) => setState(() {
                      _subjectId = v;
                      _sections.clear();
                      _suggestion = null;
                    }),
                  ),
                  if (_subjectId != null) ...[
                    const SizedBox(height: 8),
                    Wrap(spacing: 8, children: [
                      for (final a in _mine)
                        FilterChip(
                          label: Text(ctx.sectionLabels[a['sectionId']] ?? a['sectionId']),
                          selected: _sections.contains(a['sectionId']),
                          onSelected: (on) => setState(() => on ? _sections.add(a['sectionId']) : _sections.remove(a['sectionId'])),
                        ),
                    ]),
                  ],
                  TextField(controller: _title, onChanged: (_) => setState(() {}),
                      decoration: const InputDecoration(labelText: 'Title')),
                  TextField(controller: _instructions, decoration: const InputDecoration(labelText: 'Instructions (optional)')),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text('Due ${isoDate(_due)}'),
                    trailing: const Icon(Icons.edit_calendar),
                    onTap: () async {
                      final d = await showDatePicker(context: context, initialDate: _due,
                          firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 180)));
                      if (d != null) setState(() => _due = d);
                    },
                  ),
                  OutlinedButton.icon(
                    onPressed: _sections.isEmpty || _busy ? null : _suggest,
                    icon: const Icon(Icons.auto_awesome),
                    label: const Text("Suggest from the lesson"),
                  ),
                  if (_suggestion != null) ...[
                    const SizedBox(height: 8),
                    if (_suggestion!['lessonFound'] == true)
                      Text('Lesson on ${_suggestion!['date']}: ${_suggestion!['chapterName']} · ${_suggestion!['subtopicName']}',
                          style: theme.textTheme.bodySmall),
                    if (_suggestion!['note'] != null)
                      Text(_suggestion!['note'], style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error)),
                    const SizedBox(height: 6),
                    Text('Chapters', style: theme.textTheme.labelLarge),
                    Wrap(spacing: 6, runSpacing: 4, children: [
                      for (final c in (_suggestion!['bankChapters'] as List).cast<Map>())
                        FilterChip(
                          label: Text('${c['chapterName']} (${c['questionCount']})'),
                          selected: _chapters.contains(c['chapterId']),
                          onSelected: (on) => setState(() => on ? _chapters.add(c['chapterId']) : _chapters.remove(c['chapterId'])),
                        ),
                    ]),
                    if ((_suggestion!['questions'] as List).isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text('Questions (or leave none ticked to pick $_count from the chapters)', style: theme.textTheme.labelLarge),
                      for (final q in (_suggestion!['questions'] as List).cast<Map>())
                        CheckboxListTile(
                          dense: true,
                          value: _questions.contains(q['id']),
                          onChanged: (on) => setState(() => on == true ? _questions.add(q['id']) : _questions.remove(q['id'])),
                          title: Text(q['stem'], maxLines: 2, overflow: TextOverflow.ellipsis),
                          subtitle: Text('${q['type']} · ${q['marks']} marks'),
                        ),
                    ],
                    Row(children: [
                      const Text('Pick'),
                      Expanded(child: Slider(value: _count.toDouble(), min: 1, max: 20, divisions: 19,
                          label: '$_count', onChanged: (v) => setState(() => _count = v.round()))),
                      Text('$_count'),
                    ]),
                  ],
                  if (_error != null)
                    Padding(padding: const EdgeInsets.only(top: 8),
                        child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
                ]),
              ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          onPressed: _busy || _subjectId == null || _sections.isEmpty || _title.text.trim().isEmpty ||
                  (_questions.isEmpty && _chapters.isEmpty)
              ? null
              : _create,
          child: const Text('Set and notify students'),
        ),
      ],
    );
  }
}

class TeacherHomeworkDetailPage extends StatefulWidget {
  final String homeworkId;
  const TeacherHomeworkDetailPage({super.key, required this.homeworkId});

  @override
  State<TeacherHomeworkDetailPage> createState() => _TeacherHomeworkDetailPageState();
}

class _TeacherHomeworkDetailPageState extends State<TeacherHomeworkDetailPage> {
  Map<String, dynamic>? _hw;
  List<Map<String, dynamic>> _rows = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final hw = await Ops.map('/homework/${widget.homeworkId}');
      final rows = await Ops.list('/homework/${widget.homeworkId}/submissions');
      setState(() {
        _hw = hw;
        _rows = rows;
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _act(String what) async {
    try {
      final r = await Ops.post('/homework/${widget.homeworkId}/$what');
      if (mounted && what == 'remind') {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Reminded ${r['reminded']} students')));
      }
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final hw = _hw;
    if (hw == null) {
      return Scaffold(appBar: AppBar(), body: _error != null ? ErrorDisplay(message: _error!) : const LoadingIndicator());
    }
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(hw['title']), actions: [
        if (hw['status'] == 'draft') TextButton(onPressed: () => _act('publish'), child: const Text('Publish')),
        if (hw['status'] == 'published') ...[
          TextButton(onPressed: () => _act('remind'), child: const Text('Remind')),
          TextButton(onPressed: () => _act('close'), child: const Text('Close')),
        ],
      ]),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text('${hw['subjectName']} · ${(hw['sectionNames'] as List).join(', ')} · due ${hw['dueDate']} · '
            '${hw['questionCount']} questions, ${hw['totalMarks']} marks · ${hw['status']}'),
        const SizedBox(height: 12),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(columns: const [
            DataColumn(label: Text('Student')), DataColumn(label: Text('Status')),
            DataColumn(label: Text('Marks')), DataColumn(label: Text('To check')), DataColumn(label: Text('')),
          ], rows: [
            for (final r in _rows)
              DataRow(cells: [
                DataCell(Text(r['studentName'])),
                DataCell(Text({'not_submitted': 'Not submitted', 'submitted': 'Submitted', 'graded': 'Marked'}[r['status']]! +
                    (r['late'] == true ? ' (late)' : ''))),
                DataCell(Text(r['status'] == 'graded'
                    ? '${r['marks']}/${r['maxMarks']}'
                    : (r['autoMarks'] != null ? '${r['autoMarks']} so far' : '-'))),
                DataCell(Text(r['needsReview'] > 0 ? '${r['needsReview']}' : '')),
                DataCell(r['status'] == 'not_submitted'
                    ? const SizedBox()
                    : TextButton(
                        onPressed: () async {
                          final done = await showDialog<bool>(context: context,
                              builder: (_) => _GradeDialog(homework: hw, row: r));
                          if (done == true) _load();
                        },
                        child: Text(r['status'] == 'graded' ? 'Review' : 'Mark'))),
              ]),
          ]),
        ),
        if (_rows.isEmpty) Text('No students in these sections yet.', style: theme.textTheme.bodySmall),
      ]),
    );
  }
}

class _GradeDialog extends StatefulWidget {
  final Map<String, dynamic> homework;
  final Map<String, dynamic> row;
  const _GradeDialog({required this.homework, required this.row});

  @override
  State<_GradeDialog> createState() => _GradeDialogState();
}

class _GradeDialogState extends State<_GradeDialog> {
  final Map<String, TextEditingController> _marks = {};
  late final _feedback = TextEditingController(text: widget.row['feedback'] ?? '');
  String? _error;

  @override
  void initState() {
    super.initState();
    for (final e in (widget.row['evaluations'] as List).cast<Map>()) {
      _marks[e['questionId']] = TextEditingController(text: '${e['awardedMarks']}');
    }
  }

  Future<void> _save() async {
    final marks = <String, double>{};
    for (final e in _marks.entries) {
      final v = double.tryParse(e.value.text.trim());
      if (v == null) {
        setState(() => _error = 'Enter a number for every question');
        return;
      }
      marks[e.key] = v;
    }
    try {
      await Ops.post('/homework/${widget.homework['id']}/submissions/${widget.row['studentId']}/grade',
          body: {'marks': marks, if (_feedback.text.trim().isNotEmpty) 'feedback': _feedback.text.trim()});
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final questions = {for (final q in (widget.homework['questions'] as List).cast<Map>()) q['id']: q};
    final answers = Map<String, dynamic>.from(widget.row['answers'] as Map);
    return AlertDialog(
      title: Text('${widget.row['studentName']}'),
      content: SizedBox(
        width: 640,
        child: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          for (final e in (widget.row['evaluations'] as List).cast<Map>()) ...[
            Text(questions[e['questionId']]?['stem'] ?? e['questionId'], style: theme.textTheme.bodyMedium),
            Text('Answer: ${answers[e['questionId']] ?? '(blank)'}', style: theme.textTheme.bodySmall),
            if ((e['modelAnswer'] ?? '').toString().isNotEmpty)
              Text('Model: ${e['modelAnswer']}', style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic)),
            Row(children: [
              SizedBox(width: 90, child: TextField(controller: _marks[e['questionId']],
                  decoration: InputDecoration(suffixText: '/${e['maxMarks']}'))),
              const SizedBox(width: 12),
              if (e['needsReview'] == true) const ChipTag(label: 'Check this', color: Colors.orange),
              const SizedBox(width: 8),
              Expanded(child: Text(e['reasoning'] ?? '', style: theme.textTheme.bodySmall, maxLines: 2)),
            ]),
            const Divider(),
          ],
          TextField(controller: _feedback, decoration: const InputDecoration(labelText: 'Feedback (optional)')),
          if (_error != null) Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
        ])),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(onPressed: _save, child: const Text('Save marks')),
      ],
    );
  }
}
