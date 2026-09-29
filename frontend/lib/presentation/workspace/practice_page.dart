import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// Starts a practice set on the student's weakest chapters -- or the one
/// named -- and opens it (SA-4).
Future<void> startPractice(BuildContext context, {String? subject, String? chapterId}) async {
  try {
    final p = await Ops.post('/my-practice', body: {
      if (subject != null) 'subject': subject,
      if (chapterId != null) 'chapterIds': [chapterId],
    });
    if (context.mounted) context.push('/school/practice/${p['id']}');
  } catch (e) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
  }
}

/// One practice set: answer, submit, see the marks and model answers.
class PracticePage extends StatefulWidget {
  final String practiceId;
  const PracticePage({super.key, required this.practiceId});

  @override
  State<PracticePage> createState() => _PracticePageState();
}

class _PracticePageState extends State<PracticePage> {
  Map<String, dynamic>? _set;
  String? _error;
  final Map<String, String> _answers = {};
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final p = await Ops.map('/my-practice/${widget.practiceId}');
      setState(() => _set = p);
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      final p = await Ops.send('POST', '/my-practice/${widget.practiceId}/submit', body: {'answers': _answers},
          label: 'Practice answers');
      setState(() => _set = Map<String, dynamic>.from(p as Map));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = _set;
    if (p == null) {
      return Scaffold(appBar: AppBar(title: const Text('Practice')),
          body: _error != null ? ErrorDisplay(message: _error!) : const LoadingIndicator());
    }
    final theme = Theme.of(context);
    final done = p['submittedAt'] != null;
    final evals = {for (final e in (p['evaluations'] as List).cast<Map>()) e['questionId']: e};
    return Scaffold(
      appBar: AppBar(title: Text('Practice: ${p['subject']}')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (done)
          AppCard(
            margin: const EdgeInsets.only(bottom: 12),
            color: Colors.green.withValues(alpha: 0.08),
            child: Row(children: [
              Expanded(child: Text('You got ${p['marks']} of ${p['maxMarks']}', style: theme.textTheme.titleMedium)),
              FilledButton.tonal(onPressed: () => startPractice(context, subject: p['subject'] as String),
                  child: Text(tr('Practise again'))),
            ]),
          ),
        for (final (i, q) in (p['questions'] as List).cast<Map>().indexed)
          AppCard(
            margin: const EdgeInsets.only(bottom: 12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Q${i + 1}. (${q['marks']} mark${q['marks'] == 1 ? '' : 's'})', style: theme.textTheme.labelLarge),
              const SizedBox(height: 6),
              Text(q['stem'] ?? ''),
              const SizedBox(height: 8),
              if (q['type'] == 'mcq')
                Wrap(spacing: 8, children: [
                  for (final o in const ['A', 'B', 'C', 'D'])
                    ChoiceChip(
                      label: Text(o),
                      selected: (done ? (p['answers'] as Map)[q['id']] : _answers[q['id']]) == o,
                      onSelected: done ? null : (_) => setState(() => _answers[q['id'] as String] = o),
                    ),
                ])
              else
                TextField(
                  enabled: !done,
                  minLines: 2,
                  maxLines: 8,
                  controller: done ? TextEditingController(text: (p['answers'] as Map)[q['id']]?.toString() ?? '') : null,
                  onChanged: (v) => _answers[q['id'] as String] = v,
                  decoration: const InputDecoration(border: OutlineInputBorder(), hintText: 'Your answer'),
                ),
              if (evals[q['id']] != null) ...[
                const SizedBox(height: 8),
                Text('${evals[q['id']]!['awardedMarks']} / ${evals[q['id']]!['maxMarks']}', style: theme.textTheme.titleSmall),
                if ((evals[q['id']]!['modelAnswer'] ?? '').toString().isNotEmpty)
                  Text('Model answer: ${evals[q['id']]!['modelAnswer']}', style: theme.textTheme.bodySmall),
              ],
            ]),
          ),
        if (!done)
          FilledButton.icon(onPressed: _busy ? null : _submit, icon: const Icon(Icons.check), label: Text(tr('Check my answers'))),
      ]),
    );
  }
}
