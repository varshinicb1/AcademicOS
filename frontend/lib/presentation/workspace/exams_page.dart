import 'package:flutter/material.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'teacher_homework.dart' show TeachingContext;
import 'strings.dart';
import '../shared/widgets/shell.dart';

/// The principal's exam planning (EX-7): exams, each one's datesheet, the
/// invigilation roster (filled automatically, editable), and publishing.
class ExamsPage extends StatefulWidget {
  const ExamsPage({super.key});

  @override
  State<ExamsPage> createState() => _ExamsPageState();
}

class _ExamsPageState extends State<ExamsPage> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/exams');
  void _reload() => setState(() { _future = Ops.list('/exams'); });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Exams'))),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: const Text('New exam'),
        onPressed: () async {
          if (await showDialog<bool>(context: context, builder: (_) => const _NewExamDialog()) == true) _reload();
        },
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: snap.error.toString(), onRetry: _reload);
          if (snap.data!.isEmpty) {
            return const EmptyState(icon: Icons.event_note, title: 'No exams yet',
                message: 'Create an exam, place its papers on the datesheet, and fill the invigilation roster.');
          }
          return ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 96), children: [
            for (final e in snap.data!)
              AppCard(
                margin: const EdgeInsets.only(bottom: 10),
                onTap: () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => ExamDetailPage(examId: e['id'])))
                    .then((_) => _reload()),
                child: ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(e['name']),
                  subtitle: Text('${e['startDate']} to ${e['endDate']} · classes ${(e['grades'] as List).join(', ')} · '
                      '${(e['papers'] as List).length} papers'),
                  trailing: ChipTag(label: e['status']),
                ),
              ),
          ]);
        },
      ),
    );
  }
}

class _NewExamDialog extends StatefulWidget {
  const _NewExamDialog();

  @override
  State<_NewExamDialog> createState() => _NewExamDialogState();
}

class _NewExamDialogState extends State<_NewExamDialog> {
  final _name = TextEditingController();
  DateTimeRange? _range;
  final Set<int> _grades = {};
  String? _error;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('New exam'),
      content: SizedBox(
        width: 460,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          TextField(controller: _name, onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: 'Name, e.g. Half-yearly')),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(_range == null ? 'Choose dates' : '${isoDate(_range!.start)} to ${isoDate(_range!.end)}'),
            trailing: const Icon(Icons.date_range),
            onTap: () async {
              final r = await showDateRangePicker(context: context, firstDate: DateTime.now().subtract(const Duration(days: 30)),
                  lastDate: DateTime.now().add(const Duration(days: 365)));
              if (r != null) setState(() => _range = r);
            },
          ),
          const Text('Classes'),
          Wrap(spacing: 6, children: [
            for (var g = 1; g <= 12; g++)
              FilterChip(label: Text('$g'), selected: _grades.contains(g),
                  onSelected: (on) => setState(() => on ? _grades.add(g) : _grades.remove(g))),
          ]),
          if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ]),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(
          onPressed: _name.text.trim().isEmpty || _range == null || _grades.isEmpty ? null : () async {
            try {
              await Ops.post('/exams', body: {'name': _name.text.trim(), 'startDate': isoDate(_range!.start),
                'endDate': isoDate(_range!.end), 'grades': _grades.toList()..sort()});
              if (context.mounted) Navigator.pop(context, true);
            } catch (e) {
              setState(() => _error = serverErrorMessage(e));
            }
          },
          child: const Text('Create'),
        ),
      ],
    );
  }
}

class ExamDetailPage extends StatefulWidget {
  final String examId;
  const ExamDetailPage({super.key, required this.examId});

  @override
  State<ExamDetailPage> createState() => _ExamDetailPageState();
}

class _ExamDetailPageState extends State<ExamDetailPage> {
  Map<String, dynamic>? _exam;
  TeachingContext? _ctx;
  List<String> _unfilled = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) => setState(() => _ctx = c), onError: (Object e) => setState(() => _error = serverErrorMessage(e)));
    _load();
  }

  Future<void> _load() async {
    try {
      final e = await Ops.map('/exams/${widget.examId}');
      setState(() => _exam = e);
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  void _show(Object msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg.toString())));

  Future<void> _auto() async {
    try {
      final e = await Ops.post('/exams/${widget.examId}/invigilation/auto');
      setState(() {
        _exam = Map<String, dynamic>.from(e as Map);
        _unfilled = (e['unfilled'] as List).cast<String>();
      });
    } catch (e) {
      _show(serverErrorMessage(e));
    }
  }

  Future<void> _publish() async {
    try {
      final e = await Ops.post('/exams/${widget.examId}/publish');
      setState(() => _exam = Map<String, dynamic>.from(e as Map));
      _show('Published. Students and invigilators have been told.');
    } catch (e) {
      _show(serverErrorMessage(e));
    }
  }

  Future<void> _addPaper() async {
    final exam = _exam!;
    final subjects = _ctx?.subjectNames ?? const {};
    final byGrade = <int, Map<String, String>>{};
    for (final a in _ctx?.allocations ?? const <Map<String, dynamic>>[]) {
      final label = _ctx!.sectionLabels[a['sectionId']] ?? '';
      final grade = int.tryParse(label.split('-').first);
      if (grade != null) byGrade.putIfAbsent(grade, () => {})[a['subjectId']] = subjects[a['subjectId']] ?? '';
    }
    int? grade;
    String? subjectId;
    DateTime? day;
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
      title: const Text('Add a paper'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        DropdownButtonFormField<int>(
          initialValue: grade, decoration: const InputDecoration(labelText: 'Class'),
          items: [for (final g in (exam['grades'] as List).cast<int>()) DropdownMenuItem(value: g, child: Text('$g'))],
          onChanged: (v) => set(() { grade = v; subjectId = null; }),
        ),
        DropdownButtonFormField<String>(
          key: ValueKey(grade), initialValue: subjectId, decoration: const InputDecoration(labelText: 'Subject'),
          items: [for (final e in (byGrade[grade] ?? const {}).entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
          onChanged: (v) => set(() => subjectId = v),
        ),
        ListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(day == null ? 'Date' : isoDate(day!)),
          trailing: const Icon(Icons.event),
          onTap: () async {
            final d = await showDatePicker(context: ctx, initialDate: DateTime.parse(exam['startDate']),
                firstDate: DateTime.parse(exam['startDate']), lastDate: DateTime.parse(exam['endDate']));
            if (d != null) set(() => day = d);
          },
        ),
      ]),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: grade == null || subjectId == null || day == null ? null : () => Navigator.pop(ctx, true),
            child: const Text('Add')),
      ],
    )));
    if (ok != true) return;
    final papers = [
      for (final p in (exam['papers'] as List).cast<Map>())
        {'grade': p['grade'], 'subjectId': p['subjectId'], 'date': p['date'], 'startTime': p['startTime'], 'endTime': p['endTime']},
      {'grade': grade, 'subjectId': subjectId, 'date': isoDate(day!)},
    ];
    try {
      final e = await Ops.put('/exams/${widget.examId}/datesheet', body: {'papers': papers});
      setState(() => _exam = Map<String, dynamic>.from(e as Map));
    } catch (e) {
      _show(serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final e = _exam;
    if (e == null) {
      return Scaffold(appBar: AppBar(), body: _error != null ? ErrorDisplay(message: _error!) : const LoadingIndicator());
    }
    final theme = Theme.of(context);
    final papers = (e['papers'] as List).cast<Map>();
    final duties = (e['duties'] as List).cast<Map>();
    return Scaffold(
      appBar: AppBar(title: Text(e['name']), actions: [
        if (e['status'] != 'published') TextButton(onPressed: papers.isEmpty ? null : _publish, child: const Text('Publish')),
      ]),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        SectionHeader(title: 'Datesheet', subtitle: '${e['startDate']} to ${e['endDate']}',
            action: OutlinedButton.icon(onPressed: _addPaper, icon: const Icon(Icons.add), label: const Text('Paper'))),
        if (papers.isEmpty) Text('No papers yet.', style: theme.textTheme.bodySmall),
        for (final p in papers)
          ListTile(dense: true, title: Text('Class ${p['grade']} · ${p['subjectName']}'),
              subtitle: Text('${p['date']} · ${p['startTime']}-${p['endTime']}')),
        SectionHeader(title: 'Invigilation', subtitle: '${duties.where((d) => d['teacherId'] != null).length} of ${duties.length} rooms covered',
            action: FilledButton.tonal(onPressed: papers.isEmpty ? null : _auto, child: const Text('Fill automatically'))),
        for (final u in _unfilled)
          Text('No one free: $u', style: TextStyle(color: theme.colorScheme.error)),
        for (final d in duties)
          ListTile(dense: true,
              title: Text('${d['date']} ${d['startTime']} · ${d['sectionName']} · ${d['subjectName']}'),
              trailing: Text(d['teacherName'] ?? 'Nobody yet')),
      ]),
    );
  }
}
