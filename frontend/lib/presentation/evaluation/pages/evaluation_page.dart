import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Pillar 2 — teacher review queue.
///
/// The teacher never sees raw OCR or starts from zero: each answer arrives
/// pre-scored with the marking points that were and weren't met, a confidence
/// figure, and any transcription warnings. They approve, adjust, or comment.
class EvaluationPage extends StatefulWidget {
  final String answerSheetId;
  const EvaluationPage({super.key, required this.answerSheetId});

  @override
  State<EvaluationPage> createState() => _EvaluationPageState();
}

class _EvaluationPageState extends State<EvaluationPage> {
  SheetEvaluation? _sheet;
  bool _loading = false;
  String? _error;

  final Map<String, int> _adjusted = {};
  final Set<String> _approved = {};
  int _index = 0;

  bool get _hasSheet => _sheet != null && _sheet!.evaluations.isNotEmpty;

  Future<void> _runDemoEvaluation() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = GetIt.I<PillarApi>();
      final questions = await api.searchQuestionsRaw(
          subject: 'Science', grade: 10, limit: 12);
      if (questions.isEmpty) {
        throw Exception('Question bank is empty — ingest papers first.');
      }
      // Answers of mixed quality so the review queue shows the full range of
      // verdicts (full / partial / no credit) rather than a uniform result.
      final answers = <String, String>{};
      const optionLetters = ['A', 'B', 'C', 'D'];
      for (var i = 0; i < questions.length; i++) {
        final q = questions[i];
        final id = q['id'] as String;
        final scheme = (q['answerScheme'] ?? {}) as Map;
        final metadata = (scheme['metadata'] ?? {}) as Map;
        final points = (scheme['markingPoints'] ?? []) as List;
        final keywords =
            points.map((p) => (p as Map)['keyword']?.toString() ?? '').toList();
        // MCQs are scored by option letter, not by restating the option text —
        // a synthetic prose answer like "the answer involves salt and water"
        // is not something a real student writes and evaluate.py correctly
        // can't match it to a letter, so build a letter answer here instead.
        final correctOption = metadata['correctOption']?.toString();
        final isObjective = metadata['objective'] == true && correctOption != null && correctOption.isNotEmpty;

        if (i % 3 == 0) {
          answers[id] = 'Not attempted.';
        } else if (i % 3 == 1) {
          if (isObjective) {
            final wrong = optionLetters.firstWhere((o) => o != correctOption,
                orElse: () => optionLetters.first);
            answers[id] = '($wrong)';
          } else {
            answers[id] = keywords.isEmpty
                ? 'Partial explanation given.'
                : 'The answer involves ${keywords.take(1).join(", ")}.';
          }
        } else {
          if (isObjective) {
            answers[id] = '($correctOption)';
          } else {
            answers[id] = keywords.isEmpty
                ? 'A full explanation of the concept is given here.'
                : 'The answer involves ${keywords.join(", ")}, explained fully.';
          }
        }
      }
      final result = await api.evaluateSheet(
        assessmentId: 'review_demo',
        studentId: widget.answerSheetId,
        questions: questions,
        answers: answers,
      );
      setState(() {
        _sheet = result;
        _index = 0;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('AI Evaluation'),
        actions: [
          if (_hasSheet)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Text('${_approved.length}/${_sheet!.evaluations.length} approved',
                    style: theme.textTheme.bodySmall),
              ),
            ),
        ],
      ),
      body: _loading
          ? const LoadingIndicator(message: 'Evaluating answers…')
          : !_hasSheet
              ? _intro(theme)
              : _reviewBody(theme),
    );
  }

  Widget _intro(ThemeData theme) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Question-by-question review',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const Gap(8),
              const Text(
                  'Each answer is scored against the marking scheme before you see '
                  'it. You approve, adjust the marks, or leave a comment — never '
                  'start from a blank page.'),
              const Gap(12),
              ...[
                'Marks traced to named marking points',
                'Confidence shown per answer; low confidence is flagged',
                'Transcription warnings surfaced, not hidden',
              ].map((t) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(children: [
                      const Icon(Icons.check_circle, size: 16, color: Colors.green),
                      const Gap(8),
                      Expanded(child: Text(t)),
                    ]),
                  )),
              const Gap(14),
              FilledButton.icon(
                onPressed: _runDemoEvaluation,
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Evaluate a sample answer sheet'),
              ),
              const Gap(6),
              Text(
                'Uses real questions and marking schemes from the bank. '
                'Scanned-sheet capture runs through Sarvam Vision on the backend.',
                style: theme.textTheme.bodySmall,
              ),
              const Gap(14),
              OutlinedButton.icon(
                onPressed: () => context.push('/scan'),
                icon: const Icon(Icons.document_scanner_outlined),
                label: const Text('Scan a real answer booklet'),
              ),
              const Gap(6),
              Text(
                'Photograph each page of an actual answer booklet — crop, '
                'lighting fix, OCR, and AI scoring run automatically, then '
                'you swipe-review every answer before it\'s final.',
                style: theme.textTheme.bodySmall,
              ),
            ],
          ),
        ),
        if (_error != null)
          AppCard(
            color: theme.colorScheme.errorContainer.withValues(alpha: 0.35),
            child: Text(_error!),
          ),
      ],
    );
  }

  Widget _reviewBody(ThemeData theme) {
    final sheet = _sheet!;
    final ev = sheet.evaluations[_index];
    final awarded = _adjusted[ev.questionId] ?? ev.awardedMarks;
    final approved = _approved.contains(ev.questionId);

    return Column(
      children: [
        LinearProgressIndicator(
          value: (_index + 1) / sheet.evaluations.length,
          minHeight: 3,
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: Row(
            children: [
              Text('Question ${_index + 1} of ${sheet.evaluations.length}',
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600)),
              const Spacer(),
              ChipTag(
                label: '${sheet.totalAwarded}/${sheet.totalMax} total',
                color: theme.colorScheme.primary,
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Question', style: theme.textTheme.labelMedium
                        ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                    const Gap(4),
                    SelectableText(ev.stem.isEmpty ? '(question text unavailable)' : ev.stem,
                        style: theme.textTheme.bodyMedium),
                    const Gap(12),
                    Text("Student's answer", style: theme.textTheme.labelMedium
                        ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                    const Gap(4),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: SelectableText(
                        ev.studentAnswer.isEmpty ? '(no answer submitted)' : ev.studentAnswer,
                        style: theme.textTheme.bodyMedium
                            ?.copyWith(fontStyle: FontStyle.italic),
                      ),
                    ),
                  ],
                ),
              ),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text('$awarded / ${ev.maxMarks}',
                            style: theme.textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w700)),
                        const Gap(12),
                        ChipTag(
                            label: ev.verdict, color: _verdictColor(ev.verdict)),
                        const Spacer(),
                        ChipTag(
                          label: '${(ev.confidence * 100).round()}% confident',
                          color: ev.needsReview ? Colors.orange : Colors.green,
                        ),
                      ],
                    ),
                    const Gap(10),
                    Text(ev.reasoning),
                    if (ev.needsReview) ...[
                      const Gap(8),
                      Row(children: [
                        const Icon(Icons.flag, size: 15, color: Colors.orange),
                        const Gap(6),
                        Expanded(
                          child: Text('Flagged for your review — low confidence',
                              style: theme.textTheme.bodySmall
                                  ?.copyWith(color: Colors.orange.shade800)),
                        ),
                      ]),
                    ],
                  ],
                ),
              ),
              if (ev.ocrWarnings.isNotEmpty)
                AppCard(
                  color: Colors.orange.withValues(alpha: 0.10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Transcription warnings',
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w600)),
                      const Gap(4),
                      ...ev.ocrWarnings.map((w) => Text('• $w',
                          style: theme.textTheme.bodySmall)),
                    ],
                  ),
                ),
              if (ev.markingPoints.isNotEmpty)
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Marking points',
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w600)),
                      const Gap(6),
                      ...ev.markingPoints.map((m) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  m.awarded ? Icons.check_circle : Icons.cancel,
                                  size: 17,
                                  color: m.awarded ? Colors.green : Colors.red,
                                ),
                                const Gap(8),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(m.description),
                                      Text(m.reason,
                                          style: theme.textTheme.bodySmall),
                                    ],
                                  ),
                                ),
                                Text('${m.marks}',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600)),
                              ],
                            ),
                          )),
                    ],
                  ),
                ),
              if (ev.misconceptions.isNotEmpty)
                AppCard(
                  color: Colors.deepOrange.withValues(alpha: 0.08),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Likely misconceptions',
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w600)),
                      const Gap(4),
                      ...ev.misconceptions.map((m) => Text('• $m')),
                    ],
                  ),
                ),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Adjust marks',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w600)),
                    Slider(
                      value: awarded.toDouble().clamp(0, ev.maxMarks.toDouble()),
                      min: 0,
                      max: ev.maxMarks.toDouble(),
                      divisions: ev.maxMarks,
                      label: '$awarded',
                      onChanged: (v) => setState(
                          () => _adjusted[ev.questionId] = v.round()),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Row(
              children: [
                OutlinedButton(
                  onPressed: _index > 0 ? () => setState(() => _index--) : null,
                  child: const Text('Back'),
                ),
                const Gap(10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: () {
                      setState(() {
                        _approved.add(ev.questionId);
                        if (_index < sheet.evaluations.length - 1) _index++;
                      });
                    },
                    icon: Icon(approved ? Icons.check : Icons.thumb_up_alt_outlined),
                    label: Text(approved ? 'Approved — next' : 'Approve & next'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Color _verdictColor(String v) => switch (v) {
        'fullCredit' => Colors.green,
        'partialCredit' => Colors.orange,
        'blank' => Colors.grey,
        _ => Colors.red,
      };
}
