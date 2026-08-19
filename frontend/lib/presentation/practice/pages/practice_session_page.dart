import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Pillar 4 — Personalized remediation: weak concept -> practice -> mastery update.
class PracticeSessionPage extends StatefulWidget {
  final String sessionId;   // student id in this flow
  const PracticeSessionPage({super.key, this.sessionId = 'stu_meera'});

  @override
  State<PracticeSessionPage> createState() => _PracticeSessionPageState();
}

class _PracticeSessionPageState extends State<PracticeSessionPage> {
  PracticeSetView? _set;
  PracticeResultView? _result;
  final Map<String, TextEditingController> _answers = {};
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    for (final c in _answers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
    });
    try {
      final s = await GetIt.I<PillarApi>().generatePractice(widget.sessionId);
      for (final i in s.items) {
        _answers.putIfAbsent(i.questionId, () => TextEditingController());
      }
      setState(() => _set = s);
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submit() async {
    final s = _set;
    if (s == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final res = await GetIt.I<PillarApi>().submitPractice(
        s.id,
        {for (final e in _answers.entries) e.key: e.value.text},
      );
      setState(() => _result = res);
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: Text('Practice — ${widget.sessionId}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Targeted practice',
                    style: Theme.of(context).textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 6),
                const Text('Generates questions only for this student\'s weakest concepts, '
                    'easiest first. Submitting updates their mastery.'),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _busy ? null : _generate,
                  icon: const Icon(Icons.auto_awesome),
                  label: Text(_set == null ? 'Generate practice set' : 'Regenerate'),
                ),
              ],
            ),
          ),
          if (_error != null)
            AppCard(
              color: Theme.of(context).colorScheme.errorContainer.withValues(alpha: 0.4),
              child: Text(_error!),
            ),
          if (_busy) const Padding(padding: EdgeInsets.all(24), child: LoadingIndicator()),
          if (_set != null) ...[
            for (final w in _set!.warnings)
              AppCard(
                color: Colors.orange.withValues(alpha: 0.10),
                child: Row(children: [
                  const Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                  const SizedBox(width: 8),
                  Expanded(child: Text(w, style: const TextStyle(fontSize: 13))),
                ]),
              ),
            SectionHeader(
                title: 'Questions',
                subtitle: '${_set!.items.length} items · ${_set!.totalMarks} marks'),
            ..._set!.items.map((i) => AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        ChipTag(label: i.difficulty),
                        const SizedBox(width: 6),
                        ChipTag(label: '${i.marks}m'),
                      ]),
                      const SizedBox(height: 8),
                      Text(i.stem),
                      const SizedBox(height: 10),
                      TextField(
                        controller: _answers[i.questionId],
                        minLines: 2,
                        maxLines: 5,
                        decoration: const InputDecoration(
                          labelText: 'Answer',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                    ],
                  ),
                )),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: _busy ? null : _submit,
              icon: const Icon(Icons.check),
              label: const Text('Submit for AI evaluation'),
              style: FilledButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
            ),
          ],
          if (_result != null) ...[
            const SectionHeader(title: 'Result'),
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${_result!.score}/${_result!.maxScore}  (${_result!.percentage}%)',
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w700)),
                  const Divider(height: 20),
                  ..._result!.outcomes.map((o) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(children: [
                          Expanded(child: Text(o.conceptName)),
                          Text('${(o.masteryBefore * 100).round()}% → '
                              '${(o.masteryAfter * 100).round()}%'),
                          const SizedBox(width: 8),
                          ChipTag(
                            label: '${o.delta >= 0 ? "+" : ""}${(o.delta * 100).round()}',
                            color: o.delta > 0 ? Colors.green : Colors.grey,
                          ),
                        ]),
                      )),
                  const SizedBox(height: 10),
                  Text(_result!.nextAction,
                      style: const TextStyle(fontStyle: FontStyle.italic)),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
