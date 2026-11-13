import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../shared/readable.dart';

import '../../data/datasources/api/api_error.dart';
import '../../core/session/current_session.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'photos_ui.dart';
import 'strings.dart';
import 'package:academicos/core/theme/app_theme.dart';
import '../shared/widgets/shell.dart';

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
    if (years.isEmpty) throw OpsError(409, tr('Your school has no academic year set up yet.'));
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
      appBar: destinationAppBar(context, title: Text(tr('Homework'))),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final made = await showDialog<bool>(context: context, builder: (_) => const _CreateHomeworkDialog());
          if (made == true) _reload();
        },
        icon: const Icon(Icons.add),
        label: Text(tr('Set homework')),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          final items = snap.data!;
          if (items.isEmpty) {
            return EmptyState(icon: Icons.assignment_outlined, title: tr('No homework yet'),
                message: tr('Set homework from the question bank for the sections you teach.'));
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
                    Text('${h['subjectName']} · ${(h['sectionNames'] as List).join(', ')} · '
                        '${trf('due {date}', {'date': readableDate(h['dueDate'])})}',
                        style: theme.textTheme.bodySmall),
                  ])),
                  ChipTag(label: trf('{in}/{of} in · {marked} marked',
                      {'in': h['submitted'], 'of': h['students'], 'marked': h['graded']})),
                  const SizedBox(width: 8),
                  if (h['status'] != 'published') ChipTag(label: tr(h['status'] as String)),
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
  final Set<String> _types = {};
  final Set<String> _difficulties = {};
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
        if (_title.text.isEmpty && s['subtopicName'] != null) _title.text = trf('Practice: {topic}', {'topic': s['subtopicName']});
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
        if (_types.isNotEmpty) 'types': _types.toList(),
        if (_difficulties.isNotEmpty) 'difficulties': _difficulties.toList(),
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
      title: Text(tr('Set homework')),
      content: SizedBox(
        width: 620,
        child: ctx == null
            ? (_error != null ? Text(_error!) : const SizedBox(height: 120, child: LoadingIndicator()))
            : SingleChildScrollView(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                  if (subjects.isEmpty)
                    Text(tr('You have no teaching allocations this year. Ask the principal to allocate your subjects.')),
                  DropdownButtonFormField<String>(
                    initialValue: _subjectId,
                    decoration: InputDecoration(labelText: tr('Subject')),
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
                      decoration: InputDecoration(labelText: tr('Title'))),
                  TextField(controller: _instructions, decoration: InputDecoration(labelText: tr('Instructions (optional)'))),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(trf('Due {date}', {'date': isoDate(_due)})),
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
                    label: Text(tr('Suggest from the lesson')),
                  ),
                  if (_suggestion != null) ...[
                    const SizedBox(height: 8),
                    if (_suggestion!['lessonFound'] == true)
                      Text(trf('Lesson on {date}: {chapter} · {topic}', {'date': _suggestion!['date'],
                          'chapter': _suggestion!['chapterName'], 'topic': _suggestion!['subtopicName']}),
                          style: theme.textTheme.bodySmall),
                    if (_suggestion!['note'] != null)
                      Text(_suggestion!['note'], style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error)),
                    const SizedBox(height: 6),
                    Text(tr('Chapters'), style: theme.textTheme.labelLarge),
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
                      Text(trf('Questions (or leave none ticked to pick {n} from the chapters)', {'n': _count}),
                          style: theme.textTheme.labelLarge),
                      for (final q in (_suggestion!['questions'] as List).cast<Map>())
                        CheckboxListTile(
                          dense: true,
                          value: _questions.contains(q['id']),
                          onChanged: (on) => setState(() => on == true ? _questions.add(q['id']) : _questions.remove(q['id'])),
                          title: Text(q['stem'], maxLines: 2, overflow: TextOverflow.ellipsis),
                          subtitle: Text('${q['type']} · ${plural((q['marks'] as num).toInt(), 'mark')}'),
                        ),
                    ],
                    Wrap(spacing: 6, children: [
                      for (final t in const [('mcq', 'MCQ'), ('very_short_answer', 'Very short'),
                        ('short_answer', 'Short'), ('long_answer', 'Long')])
                        FilterChip(label: Text(tr(t.$2)), selected: _types.contains(t.$1),
                            onSelected: (on) => setState(() => on ? _types.add(t.$1) : _types.remove(t.$1))),
                    ]),
                    // TA-4: how hard; none ticked means any.
                    Wrap(spacing: 6, children: [
                      for (final d in const [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
                        FilterChip(key: Key('difficulty-${d.$1}'), label: Text(tr(d.$2)),
                            selected: _difficulties.contains(d.$1),
                            onSelected: (on) => setState(() => on ? _difficulties.add(d.$1) : _difficulties.remove(d.$1))),
                    ]),
                    Row(children: [
                      Text(tr('Pick')),
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
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(
          onPressed: _busy || _subjectId == null || _sections.isEmpty || _title.text.trim().isEmpty ||
                  (_questions.isEmpty && _chapters.isEmpty)
              ? null
              : _create,
          child: Text(tr('Set and notify students')),
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(trf('Reminded {n} students', {'n': r['reminded']}))));
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
        if (hw['status'] == 'draft') TextButton(onPressed: () => _act('publish'), child: Text(tr('Publish'))),
        if (hw['status'] == 'published') ...[
          TextButton(onPressed: () => _act('remind'), child: Text(tr('Remind'))),
          TextButton(onPressed: () => _act('close'), child: Text(tr('Close'))),
        ],
      ]),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text('${hw['subjectName']} · ${(hw['sectionNames'] as List).join(', ')} · '
            '${trf('due {date}', {'date': readableDate(hw['dueDate'])})} · '
            '${trf('{q} questions, {m} marks', {'q': hw['questionCount'], 'm': hw['totalMarks']})} · ${tr(hw['status'] as String)}'),
        const SizedBox(height: 12),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(columns: [
            DataColumn(label: Text(tr('Student'))), DataColumn(label: Text(tr('Status'))),
            DataColumn(label: Text(tr('Marks'))), DataColumn(label: Text(tr('To check'))), const DataColumn(label: Text('')),
          ], rows: [
            for (final r in _rows)
              DataRow(cells: [
                DataCell(Text(r['studentName'])),
                DataCell(Text(tr({'not_submitted': 'Not submitted', 'submitted': 'Submitted', 'graded': 'Marked'}[r['status']]!) +
                    (r['late'] == true ? ' (${tr('late')})' : ''))),
                DataCell(Text(r['status'] == 'graded'
                    ? '${r['marks']}/${r['maxMarks']}'
                    : (r['autoMarks'] != null ? trf('{n} so far', {'n': r['autoMarks']}) : '-'))),
                DataCell(Text(r['needsReview'] > 0 ? '${r['needsReview']}' : '')),
                DataCell(r['status'] == 'not_submitted'
                    ? const SizedBox()
                    : TextButton(
                        onPressed: () async {
                          final done = await showDialog<bool>(context: context,
                              builder: (_) => _GradeDialog(homework: hw, row: r));
                          if (done == true) _load();
                        },
                        child: Text(r['status'] == 'graded' ? tr('Review') : tr('Mark')))),
              ]),
          ]),
        ),
        if (_rows.isEmpty) Text(tr('No students in these sections yet.'), style: theme.textTheme.bodySmall),
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
        setState(() => _error = tr('Enter a number for every question'));
        return;
      }
      marks[e.key] = v;
    }
    try {
      await Ops.send('POST', '/homework/${widget.homework['id']}/submissions/${widget.row['studentId']}/grade',
          body: {'marks': marks, if (_feedback.text.trim().isNotEmpty) 'feedback': _feedback.text.trim()},
          label: trf('Marks for {name}', {'name': widget.row['studentName'] ?? tr('a student')}));
      if (mounted) Navigator.pop(context, true);
    } on OpsQueued catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
      Navigator.pop(context, false);
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
            Text(trf('Answer: {answer}', {'answer': answers[e['questionId']] ?? tr('(blank)')}), style: theme.textTheme.bodySmall),
            if ((e['modelAnswer'] ?? '').toString().isNotEmpty)
              Text(trf('Model: {answer}', {'answer': e['modelAnswer']}),
                  style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic)),
            Row(children: [
              SizedBox(width: 90, child: TextField(controller: _marks[e['questionId']],
                  decoration: InputDecoration(suffixText: '/${e['maxMarks']}'))),
              const SizedBox(width: 12),
              if (e['needsReview'] == true) ChipTag(label: tr('Check this'), color: AppColors.warning),
              const SizedBox(width: 8),
              Expanded(child: Text(e['reasoning'] ?? '', style: theme.textTheme.bodySmall, maxLines: 2)),
            ]),
            const Divider(),
          ],
          if ((widget.row['photoIds'] as List? ?? const []).isNotEmpty) ...[
            Text(tr('Written work'), style: theme.textTheme.titleSmall),
            const SizedBox(height: 6),
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (final id in (widget.row['photoIds'] as List).cast<String>())
                PhotoThumb(path: '/homework/${widget.homework['id']}/submissions/${widget.row['studentId']}/photos/$id'),
            ]),
            const Divider(),
          ],
          TextField(controller: _feedback, decoration: InputDecoration(labelText: tr('Feedback (optional)'))),
          if (_error != null) Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
        ])),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(onPressed: _save, child: Text(tr('Save marks'))),
      ],
    );
  }
}
