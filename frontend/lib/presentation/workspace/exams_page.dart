import 'package:flutter/material.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'teacher_homework.dart' show TeachingContext;
import 'strings.dart';
import '../shared/widgets/shell.dart';

/// The principal's exam planning (EX-7): exams, each one's datesheet, the
/// invigilation roster (filled automatically, editable), and publishing.
class ExamsPage extends StatefulWidget {
  /// Today, for the year a new exam goes in; a test passes a fixed date.
  final DateTime? today;

  const ExamsPage({super.key, this.today});

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
          if (await showDialog<bool>(context: context, builder: (_) => _NewExamDialog(today: widget.today)) == true) _reload();
        },
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
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
  /// Today, for the year an exam goes in; a test passes a fixed date.
  final DateTime? today;
  const _NewExamDialog({this.today});

  @override
  State<_NewExamDialog> createState() => _NewExamDialogState();
}

/// The year an exam goes in, and the classes it has.
typedef _ExamYear = ({String label, DateTime start, DateTime end, List<int> grades});

class _NewExamDialogState extends State<_NewExamDialog> {
  final _name = TextEditingController();
  DateTime get _today => widget.today ?? DateTime.now();
  late final Future<_ExamYear?> _year = _loadYear();
  DateTimeRange? _range;
  final Set<int> _grades = {};
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  /// The year holding today, else the next one, else the latest: an exam
  /// must fall inside a year (the server refuses one that does not, with
  /// "no academic year contains the exam's start date"). Null: none at all.
  Future<_ExamYear?> _loadYear() async {
    final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
    if (years.isEmpty) return null;
    final today = isoDate(_today);
    years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
    final year = years.where((y) => (y['startDate'] as String).compareTo(today) <= 0 &&
            (y['endDate'] as String).compareTo(today) >= 0).firstOrNull ??
        years.where((y) => (y['startDate'] as String).compareTo(today) > 0).firstOrNull ??
        years.last;
    final sections = await Ops.list('/curriculum/academic-years/${year['id']}/sections');
    final grades = {for (final s in sections) (s['gradeNumber'] as num).toInt()}.toList()..sort();
    return (label: year['label'] as String, start: DateTime.parse(year['startDate'] as String),
        end: DateTime.parse(year['endDate'] as String), grades: grades);
  }

  /// The picker opens on a week inside the year: from today when the year
  /// holds today, else from its first day.
  DateTimeRange _initialRange(_ExamYear y) {
    final day = DateTime(_today.year, _today.month, _today.day);
    final from = day.isBefore(y.start) || day.isAfter(y.end) ? y.start : day;
    final to = from.add(const Duration(days: 6));
    return DateTimeRange(start: from, end: to.isAfter(y.end) ? y.end : to);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_ExamYear?>(
      future: _year,
      builder: (context, snap) {
        final loading = snap.connectionState != ConnectionState.done;
        final year = snap.data;
        return AlertDialog(
          title: const Text('New exam'),
          content: SizedBox(
            width: 460,
            child: loading
                ? const SizedBox(height: 120, child: LoadingIndicator())
                : snap.hasError
                    ? Text(serverErrorMessage(snap.error!), style: TextStyle(color: Theme.of(context).colorScheme.error))
                    : year == null
                        ? SchoolNotSetUp(
                            why: 'An exam goes inside the school year, and there is none yet.',
                            beforeOpen: () => Navigator.pop(context))
                        : _form(context, year),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
            if (year != null)
              FilledButton(
                key: const ValueKey('exam-create'),
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
      },
    );
  }

  Widget _form(BuildContext context, _ExamYear year) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      TextField(key: const ValueKey('exam-name'), controller: _name, onChanged: (_) => setState(() {}),
          decoration: const InputDecoration(labelText: 'Name, e.g. Half-yearly')),
      ListTile(
        key: const ValueKey('exam-dates'),
        contentPadding: EdgeInsets.zero,
        title: Text(_range == null ? 'Choose dates' : '${isoDate(_range!.start)} to ${isoDate(_range!.end)}'),
        subtitle: Text('Within ${year.label}: ${isoDate(year.start)} to ${isoDate(year.end)}', style: muted),
        trailing: const Icon(Icons.date_range),
        onTap: () async {
          // Only days of the year can be picked.
          final r = await showDateRangePicker(context: context, firstDate: year.start, lastDate: year.end,
              initialDateRange: _range ?? _initialRange(year));
          if (r != null) setState(() => _range = r);
        },
      ),
      const Text('Classes'),
      if (year.grades.isEmpty)
        Text('${year.label} has no classes yet.', style: muted)
      else
        Wrap(spacing: 6, children: [
          for (final g in year.grades)
            FilterChip(key: ValueKey('exam-class-$g'), label: Text('$g'), selected: _grades.contains(g),
                onSelected: (on) => setState(() => on ? _grades.add(g) : _grades.remove(g))),
        ]),
      if (_error != null) Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
    ]);
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
    TeachingContext.load().then((c) { if (mounted) setState(() => _ctx = c); },
        onError: (Object e) { if (mounted) setState(() => _error = serverErrorMessage(e)); });
    _load();
  }

  Future<void> _load() async {
    try {
      final e = await Ops.map('/exams/${widget.examId}');
      if (!mounted) return;
      setState(() => _exam = e);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  void _show(Object msg) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg.toString())));
  }

  Future<void> _auto() async {
    try {
      final e = await Ops.post('/exams/${widget.examId}/invigilation/auto');
      if (!mounted) return;
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
      if (!mounted) return;
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
      if (!mounted) return;
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
