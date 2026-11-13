import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/readable.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'practice_page.dart';
import 'photos_ui.dart';
import 'strings.dart';
import 'package:academicos/core/theme/app_theme.dart';
import '../shared/widgets/shell.dart';

/// A student's homework (SA-2): what is due, then each homework's
/// questions to answer in the app, and the marks and model answers once it
/// is marked.
class MyHomeworkPage extends StatefulWidget {
  const MyHomeworkPage({super.key});

  @override
  State<MyHomeworkPage> createState() => _MyHomeworkPageState();
}

class _MyHomeworkPageState extends State<MyHomeworkPage> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/my-homework');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('My homework'))),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = Ops.list('/my-homework'); }));
          }
          final items = snap.data!;
          if (items.isEmpty) {
            return EmptyState(icon: Icons.assignment_turned_in_outlined, title: tr('No homework'),
                message: tr('When your teacher sets homework it appears here.'));
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final h in items) HomeworkStatusTile(item: h,
                onTap: () => context.push('/school/my-homework/${h['id']}')
                    .then((_) => setState(() { _future = Ops.list('/my-homework'); }))),
          ]);
        },
      ),
    );
  }
}

/// One homework's line: title, subject, due date and where the student
/// stands. Shared with the parent's view of a child.
class HomeworkStatusTile extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback? onTap;
  const HomeworkStatusTile({super.key, required this.item, this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final status = item['myStatus'] as String;
    final overdue = item['overdue'] == true;
    final (label, color) = switch (status) {
      'graded' => (trf('Marked: {marks}/{total}', {'marks': _fmt(item['marks']), 'total': item['totalMarks']}),
          AppColors.success),
      'submitted' => (tr('Submitted, waiting for marks'), theme.colorScheme.primary),
      _ => (tr(overdue ? 'Overdue' : 'Not submitted'), overdue ? theme.colorScheme.error : theme.colorScheme.outline),
    };
    return AppCard(
      onTap: onTap,
      margin: const EdgeInsets.only(bottom: 10),
      child: Row(children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(item['title'] ?? '', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text(trf('{subject} · due {date}', {'subject': item['subjectName'], 'date': readableDate(item['dueDate'] as String)}),
                style: theme.textTheme.bodySmall),
          ]),
        ),
        ChipTag(label: label, color: color),
      ]),
    );
  }
}

String _fmt(Object? n) => n is num ? (n == n.roundToDouble() ? n.toInt().toString() : n.toStringAsFixed(1)) : '-';

class HomeworkDetailPage extends StatefulWidget {
  final String homeworkId;
  /// Set when a parent opens a child's homework (SA-6/SA-7): read it, and for
  /// a class 1-5 child ([young]) answer it together and hand it in.
  final String? childId;
  final String? childName;
  /// Classes 1-5: larger text, and the parent may hand it in (SA-7).
  final bool young;
  const HomeworkDetailPage({super.key, required this.homeworkId, this.childId, this.childName, this.young = false});

  @override
  State<HomeworkDetailPage> createState() => _HomeworkDetailPageState();
}

class _HomeworkDetailPageState extends State<HomeworkDetailPage> {
  Map<String, dynamic>? _hw;
  String? _error;
  final Map<String, TextEditingController> _answers = {};
  bool _sending = false;

  String get _base => widget.childId == null ? '/my-homework' : '/children/${widget.childId}/homework';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final hw = await Ops.map('$_base/${widget.homeworkId}');
      final given = Map<String, dynamic>.from(hw['answers'] as Map? ?? {});
      for (final q in (hw['questions'] as List).cast<Map>()) {
        _answers.putIfAbsent(q['id'] as String, () => TextEditingController(text: given[q['id']]?.toString() ?? ''));
      }
      setState(() => _hw = hw);
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _submit() async {
    setState(() => _sending = true);
    try {
      final hw = await Ops.send('POST', '$_base/${widget.homeworkId}/submit',
          body: {'answers': {for (final e in _answers.entries) e.key: e.value.text.trim()}},
          label: trf('Answers for {title}', {'title': _hw?['title'] ?? tr('homework')})
              + (widget.childName == null ? '' : ' (${widget.childName})'));
      setState(() => _hw = Map<String, dynamic>.from(hw as Map));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
            _hw!['myStatus'] == 'graded'
                ? trf('Marked: {marks}/{total}', {'marks': _fmt(_hw!['marks']), 'total': _hw!['totalMarks']})
                : tr('Sent to your teacher'))));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final hw = _hw;
    final theme = Theme.of(context);
    if (hw == null) {
      return Scaffold(appBar: AppBar(), body: _error != null ? ErrorDisplay(message: _error!) : const LoadingIndicator());
    }
    final graded = hw['myStatus'] == 'graded';
    // A parent answers only for a young child; an older child's is read-only.
    final open = hw['status'] == 'published' && !graded && (widget.childId == null || widget.young);
    final evals = {for (final e in (hw['evaluations'] as List).cast<Map>()) e['questionId']: e};
    final mq = MediaQuery.of(context);
    return MediaQuery(
      // Classes 1-5 read larger (SA-7); a larger system setting is kept.
      data: widget.young && mq.textScaler.scale(1) < 1.25 ? mq.copyWith(textScaler: const TextScaler.linear(1.25)) : mq,
      child: Scaffold(
      appBar: AppBar(title: Text(widget.childName == null ? (hw['title'] ?? 'Homework') : '${hw['title']} · ${widget.childName}')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (widget.childId != null && widget.young)
          Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(
              trf('Do this together: read each question to {name}, let them answer, and hand it in.',
                  {'name': widget.childName ?? tr('your child')}),
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.primary))),
        Text(trf('{subject} · due {date} · {marks} marks', {'subject': hw['subjectName'],
            'date': readableDate(hw['dueDate'] as String), 'marks': hw['totalMarks']}), style: theme.textTheme.bodyMedium),
        if ((hw['instructions'] as String? ?? '').isNotEmpty)
          Padding(padding: const EdgeInsets.only(top: 8), child: Text(hw['instructions'])),
        if (graded)
          AppCard(
            margin: const EdgeInsets.symmetric(vertical: 12),
            color: AppColors.success.withValues(alpha: 0.08),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(trf('Marks: {marks} / {total}', {'marks': _fmt(hw['marks']), 'total': hw['totalMarks']}),
                  style: theme.textTheme.titleMedium),
              if (hw['feedback'] != null) Padding(padding: const EdgeInsets.only(top: 6), child: Text(trf('Teacher: {feedback}', {'feedback': hw['feedback']}))),
            ]),
          ),
        const SizedBox(height: 8),
        for (final (i, q) in (hw['questions'] as List).cast<Map>().indexed)
          AppCard(
            margin: const EdgeInsets.only(bottom: 12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(trf(q['marks'] == 1 ? 'Q{n}. ({marks} mark)' : 'Q{n}. ({marks} marks)', {'n': i + 1, 'marks': q['marks']}),
                  style: theme.textTheme.labelLarge),
              const SizedBox(height: 6),
              Text(q['stem'] ?? ''),
              for (final part in (q['parts'] as List? ?? const []).cast<Map>())
                Padding(padding: const EdgeInsets.only(top: 4), child: Text('(${part['partNumber']}) ${part['text']}')),
              const SizedBox(height: 8),
              if (q['type'] == 'mcq')
                _OptionPicker(controller: _answers[q['id']]!, enabled: open)
              else
                TextField(
                  controller: _answers[q['id']],
                  enabled: open,
                  minLines: q['type'] == 'long_answer' ? 5 : 2,
                  maxLines: 12,
                  decoration: InputDecoration(hintText: tr('Your answer')),
                ),
              if (evals[q['id']] != null) _EvalLine(e: Map<String, dynamic>.from(evals[q['id']]!)),
            ]),
          ),
        if (widget.childId == null) MyHomeworkPhotos(homeworkId: widget.homeworkId, editable: open),
        const SizedBox(height: 12),
        if (open)
          FilledButton.icon(
            onPressed: _sending ? null : _submit,
            icon: const Icon(Icons.send),
            label: Text(tr(hw['myStatus'] == 'submitted' ? 'Send again' : 'Submit')),
          ),
        if (hw['status'] == 'closed' && !graded)
          Text(tr('This homework is closed.')),
      ]),
    ));
  }
}

class _OptionPicker extends StatefulWidget {
  final TextEditingController controller;
  final bool enabled;
  const _OptionPicker({required this.controller, required this.enabled});

  @override
  State<_OptionPicker> createState() => _OptionPickerState();
}

class _OptionPickerState extends State<_OptionPicker> {
  @override
  Widget build(BuildContext context) {
    return Wrap(spacing: 8, children: [
      for (final o in const ['A', 'B', 'C', 'D'])
        ChoiceChip(
          label: Text(o),
          selected: widget.controller.text == o,
          onSelected: widget.enabled ? (_) => setState(() => widget.controller.text = o) : null,
        ),
    ]);
  }
}

class _EvalLine extends StatelessWidget {
  final Map<String, dynamic> e;
  const _EvalLine({required this.e});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${_fmt(e['awardedMarks'])} / ${e['maxMarks']}', style: theme.textTheme.titleSmall),
        if ((e['modelAnswer'] ?? '').toString().isNotEmpty)
          Text(trf('Model answer: {answer}', {'answer': e['modelAnswer']}), style: theme.textTheme.bodySmall),
      ]),
    );
  }
}

/// Learning progress (SA-3) for the caller or, with [path], anyone the
/// caller may see (a parent's child: `/children/{id}/learning`).
class LearningPage extends StatelessWidget {
  final String path;
  final String title;
  const LearningPage({super.key, this.path = '/my-learning', this.title = 'My progress'});

  @override
  Widget build(BuildContext context) {
    // The student's own progress is a navigation destination; a parent's
    // view of a child's is a page pushed over the family page.
    final destination = path == '/my-learning';
    return Scaffold(
        appBar: AppBar(
            leading: destination ? forceShellLeading(context) : null,
            automaticallyImplyLeading: !destination,
            title: Text(title)),
        body: LearningView(path: path));
  }
}

class LearningView extends StatefulWidget {
  final String path;
  const LearningView({super.key, required this.path});

  @override
  State<LearningView> createState() => _LearningViewState();
}

class _LearningViewState extends State<LearningView> {
  late Future<Map<String, dynamic>> _future = Ops.map(widget.path);

  static const _statusLabel = {
    'not_started': 'Not started', 'early': 'Too early to say', 'needs_work': 'Needs work',
    'developing': 'Getting there', 'mastered': 'Mastered',
  };

  Color _color(String status, ThemeData t) => switch (status) {
        'mastered' => AppColors.success,
        'developing' => AppColors.warning,
        'needs_work' => t.colorScheme.error,
        _ => t.colorScheme.outline,
      };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) {
          return ErrorDisplay(message: serverErrorMessage(snap.error!),
              onRetry: () => setState(() { _future = Ops.map(widget.path); }));
        }
        final d = snap.data!;
        final subjects = (d['subjects'] as List).cast<Map>();
        if (subjects.isEmpty) {
          return EmptyState(icon: Icons.insights_outlined, title: tr('No marked work yet'),
              message: tr('Progress appears here once homework, tests or practice are marked.'));
        }
        final revise = (d['reviseNext'] as List).cast<Map>();
        final weeks = (d['weekly'] as List).cast<Map>();
        return ListView(padding: const EdgeInsets.all(16), children: [
          if (revise.isNotEmpty) ...[
            SectionHeader(title: tr('Revise next')),
            for (final r in revise)
              ListTile(
                leading: const Icon(Icons.replay),
                title: Text(r['topicName'] ?? r['chapterName']),
                subtitle: Text('${r['subject']} · ${r['reason']}'),
                // A student practises their own weak chapter; a parent's view has no button.
                trailing: widget.path == '/my-learning'
                    ? TextButton(
                        onPressed: () => startPractice(context, subject: r['subject'] as String, chapterId: r['chapterId'] as String),
                        child: Text(tr('Practise')))
                    : null,
              ),
          ],
          SectionHeader(title: tr('Week by week')),
          SizedBox(
            height: 90,
            child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
              for (final w in weeks)
                Expanded(
                  child: Tooltip(
                    message: w['average'] == null
                        ? trf('Week of {date}: no marked work', {'date': readableDate(w['weekStart'] as String)})
                        : trf('Week of {date}: {pct}% over {n} answers', {
                            'date': readableDate(w['weekStart'] as String),
                            'pct': ((w['average'] as num) * 100).round(),
                            'n': w['answered'],
                          }),
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      height: w['average'] == null ? 4 : 8 + 72 * (w['average'] as num).toDouble(),
                      color: w['average'] == null ? theme.dividerColor : theme.colorScheme.primary,
                    ),
                  ),
                ),
            ]),
          ),
          const SizedBox(height: 16),
          for (final s in subjects) ...[
            SectionHeader(title: trf('{subject} · class {grade}', {'subject': s['subject'], 'grade': s['grade']}),
                subtitle: tr(_statusLabel[s['status']] ?? s['status'] as String)),
            for (final c in (s['chapters'] as List).cast<Map>())
              ExpansionTile(
                title: Text(c['chapterName']),
                subtitle: Text(c['evidenceCount'] == 0
                    ? tr('Not started')
                    : trf('{status} · {n} answers',
                        {'status': tr(_statusLabel[c['status']] ?? c['status'] as String), 'n': c['evidenceCount']})),
                trailing: SizedBox(
                  width: 120,
                  child: LinearProgressIndicator(
                    value: (c['mastery'] as num?)?.toDouble() ?? 0,
                    color: _color(c['status'] as String, theme),
                  ),
                ),
                children: [
                  for (final t in (c['topics'] as List).cast<Map>())
                    ListTile(
                      dense: true,
                      title: Text(t['topicName']),
                      subtitle: Text(trf('{status} · {n} answers',
                          {'status': tr(_statusLabel[t['status']] ?? t['status'] as String), 'n': t['evidenceCount']})),
                      trailing: SizedBox(width: 100, child: LinearProgressIndicator(
                          value: (t['mastery'] as num?)?.toDouble() ?? 0, color: _color(t['status'] as String, theme))),
                    ),
                ],
              ),
          ],
        ]);
      },
    );
  }
}

/// Published exams: a student's datesheet, a teacher's invigilation duties.
class MyExamsPage extends StatelessWidget {
  const MyExamsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Exams'))),
      body: FutureBuilder<Map<String, dynamic>>(
        future: Ops.map('/my-exams'),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!));
          final exams = (snap.data!['exams'] as List).cast<Map>();
          if (exams.isEmpty) {
            return EmptyState(icon: Icons.event_available_outlined, title: tr('No exams published'),
                message: tr('Datesheets and duties appear here once the school publishes them.'));
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final e in exams) ...[
              SectionHeader(title: e['name'], subtitle: trf('{start} to {end}', {'start': e['startDate'], 'end': e['endDate']})),
              for (final p in (e['papers'] as List).cast<Map>().where((_) => (e['duties'] as List).isEmpty))
                ListTile(leading: const Icon(Icons.description_outlined), title: Text(p['subjectName']),
                    subtitle: Text('${p['date']} · ${p['startTime']}-${p['endTime']}'),
                    // SA-4: exam preparation, for a paper still to come and only for the student.
                    trailing: CurrentSession.role == 'student' &&
                            (p['date'] as String).compareTo(isoDate(DateTime.now())) >= 0
                        ? TextButton(
                            key: ValueKey('prepare-${p['id']}'),
                            onPressed: () => startPractice(context, examPaperId: p['id'] as String),
                            child: Text(tr('Prepare')))
                        : null),
              for (final d in (e['duties'] as List).cast<Map>())
                ListTile(leading: const Icon(Icons.visibility_outlined),
                    title: Text('${d['sectionName']} · ${d['subjectName']}'),
                    subtitle: Text('${d['date']} · ${d['startTime']}-${d['endTime']}')),
            ],
          ]);
        },
      ),
    );
  }
}
