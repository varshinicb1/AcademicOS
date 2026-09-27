import 'package:flutter/material.dart';

import '../../../data/datasources/api/pillar_api.dart';

/// What the school is paying for, per term: which classes have had a paper
/// set, the time the product saved on them, and what its question bank holds
/// for the classes it sells.
///
/// PRD 12.6 gives the principal four metrics, two of them "this term" -- (a)
/// exam coverage and (b) time saved, labelled estimated -- and decision 11
/// compares time saved per term. The figures come from `GET /paper-timing`
/// (the term covering the school's today) and `GET /catalog`.
///
/// Rules this card exists to keep:
///  * a zero that means "nothing has been measured" never prints as a
///    measurement. "0 minutes saved per paper" reads as a finding; it is
///    arithmetic on an empty set;
///  * the server's own caveat about the DECLARED baseline is rendered
///    verbatim beside the saving, because that number gets quoted at people;
///  * all-time figures are never labelled "this term" -- with no term covering
///    today the server's note says so, verbatim;
///  * the one line read without opening anything carries the gap: which
///    classes have no paper yet, or that the school has not declared its
///    classes and so the gap cannot be listed.
class InsightsCard extends StatelessWidget {
  const InsightsCard({
    super.key,
    required this.timing,
    required this.catalog,
    this.onSetBaseline,
  });

  final PaperTiming timing;
  final Catalog catalog;

  /// Sets (minutes) or clears (null) the term's own baseline. Absent, the
  /// card offers no way to change it.
  final Future<void> Function(double? minutes)? onSetBaseline;

  /// The classes this release serves. A principal deciding whether to renew
  /// should not be shown Class 12 Odissi beside their own classes when we
  /// cannot set a paper for it (docs/product-scorecard.md, "Classes in
  /// scope").
  static const _grades = [6, 7, 8, 9, 10];

  static const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  /// "2026-04-01" -> "1 Apr 2026"; anything else is shown as it came.
  static String _date(String iso) {
    final d = DateTime.tryParse(iso);
    return d == null ? iso : '${d.day} ${_months[d.month - 1]} ${d.year}';
  }

  static String _papers(int n) => n == 1 ? '1 paper' : '$n papers';

  /// One line a principal can read without opening anything: how much the
  /// bank holds for the classes we sell, and how many of those pairs have
  /// nothing at all. The gap is stated, not left to be inferred from a list
  /// nobody expands.
  static String _bankSummary(List<CatalogEntry> rows) {
    if (rows.isEmpty) return 'No questions for any class yet.';
    final total = rows.fold<int>(0, (s, e) => s + e.questionCount);
    final empty = rows.where((e) => e.questionCount == 0).length;
    final gap = empty == 0
        ? ''
        : ', $empty of ${rows.length} class-subject pairs with no questions yet';
    return '$total questions across ${rows.length} class-subject pairs$gap.';
  }

  /// The exam coverage line, read unopened.
  String _coverageSummary() {
    final cov = timing.examCoverage;
    final when = timing.isTerm ? 'this term' : 'so far';
    final set = '${_papers(timing.papers)} set $when.';
    if (!cov.classesDeclared) {
      return '$set Set up your classes and subjects for this year in calendar '
          'setup to see which are still without one.';
    }
    final pairs = cov.covered.length + cov.notYet.length;
    if (cov.notYet.isEmpty) return '$set Every class-subject pair has at least one.';
    return '$set ${cov.notYet.length} of $pairs class-subject pairs have no paper yet.';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rows = [
      for (final e in catalog.entries)
        if (_grades.contains(e.grade)) e,
    ]..sort((a, b) => a.grade == b.grade
        ? a.subject.compareTo(b.subject)
        : a.grade.compareTo(b.grade));
    final term = timing.term;
    final cov = timing.examCoverage;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (timing.isTerm && term != null) ...[
              Text(term.name, style: theme.textTheme.titleMedium),
              Text('${_date(term.startDate)} to ${_date(term.endDate)}',
                  style: theme.textTheme.bodySmall),
            ] else ...[
              Text('All time', style: theme.textTheme.titleMedium),
              if (timing.scopeNote != null)
                Text(timing.scopeNote!, style: theme.textTheme.bodySmall),
            ],
            const Divider(height: 24),
            // Collapsed, like the bank below: the summary carries the gap.
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              title: Text('Exam coverage', style: theme.textTheme.titleMedium),
              subtitle: Text(_coverageSummary(), style: theme.textTheme.bodyMedium),
              children: [
                for (final c in cov.covered)
                  _line(theme, 'Class ${c.grade} ${c.subject}: ${_papers(c.papers)}'),
                for (final c in cov.notYet)
                  _line(theme, 'Class ${c.grade} ${c.subject}: no paper yet'),
              ],
            ),
            if (cov.unattributed > 0)
              Text(
                '${_papers(cov.unattributed)} could not be matched to a class: '
                'they were set before papers recorded their class.',
                style: theme.textTheme.bodySmall,
              ),
            const Divider(height: 24),
            Text('Time saved', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            if (timing.nothingMeasuredYet)
              Text(
                timing.isTerm
                    ? 'No paper has been generated this term yet, so there is nothing '
                        'to measure. This fills in as your teachers set papers.'
                    : 'No paper has been generated through the web app yet, so there is '
                        'nothing to measure. This fills in as your teachers set papers.',
                style: theme.textTheme.bodyMedium,
              )
            else ...[
              Text(
                '${timing.estimatedMinutesSavedPerPaper.toStringAsFixed(0)} minutes '
                'saved per paper, ${timing.estimatedMinutesSavedTotal.toStringAsFixed(0)} '
                'in total, against a baseline of '
                '${timing.baselineMinutesPerPaper.toStringAsFixed(0)} minutes a paper '
                '(${timing.baselineProvenance}).',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 4),
              Text('Generation itself took a median of '
                  '${timing.medianGenerationSeconds.toStringAsFixed(2)} seconds.',
                  style: theme.textTheme.bodySmall),
              const SizedBox(height: 8),
              Text(timing.caveat,
                  style: theme.textTheme.bodySmall
                      ?.copyWith(fontStyle: FontStyle.italic)),
            ],
            if (timing.isTerm && term != null && onSetBaseline != null)
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: () => _editBaseline(context, term),
                  child: Text(term.manualBaselineMinutes == null
                      ? "Set this term's baseline"
                      : "Change this term's baseline"),
                ),
              ),
            const Divider(height: 24),
            // Collapsed by default: this card sits at the end of the Coverage
            // & Pace tab, and ten class-subject rows expanded pushed that
            // tab's own summary off a 375 px phone -- the responsive suite
            // caught it. The headline stays visible; the detail is one tap.
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              title: Text('Question bank', style: theme.textTheme.titleMedium),
              subtitle: Text(_bankSummary(rows), style: theme.textTheme.bodyMedium),
              children: [
                for (final e in rows)
                  _line(
                    theme,
                    e.questionCount == 0
                        ? 'Class ${e.grade} ${e.subject}: no questions yet'
                        : 'Class ${e.grade} ${e.subject}: ${e.questionCount} questions, '
                            '${e.chapters} chapters, marks '
                            '${e.marksAvailable.join(", ")}',
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  static Widget _line(ThemeData theme, String text) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Align(
          alignment: Alignment.centerLeft,
          child: Text(text, style: theme.textTheme.bodyMedium),
        ),
      );

  Future<void> _editBaseline(BuildContext context, TimingTerm term) async {
    final result = await showDialog<_BaselineChoice>(
      context: context,
      builder: (_) => _BaselineDialog(term: term),
    );
    if (result == null || !context.mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await onSetBaseline!(result.minutes);
    } catch (e) {
      // Said, not swallowed: an unsaved baseline would otherwise leave the
      // principal quoting the old saving believing it is the new one.
      messenger.showSnackBar(
          SnackBar(content: Text('Could not save the baseline: ${serverErrorMessage(e)}')));
    }
  }
}

/// What the dialog returned: the minutes to set, or null to clear.
class _BaselineChoice {
  const _BaselineChoice(this.minutes);
  final double? minutes;
}

class _BaselineDialog extends StatefulWidget {
  const _BaselineDialog({required this.term});
  final TimingTerm term;

  @override
  State<_BaselineDialog> createState() => _BaselineDialogState();
}

class _BaselineDialogState extends State<_BaselineDialog> {
  late final TextEditingController _minutes = TextEditingController(
      text: widget.term.manualBaselineMinutes?.toStringAsFixed(0) ?? '');
  String? _error;

  @override
  void dispose() {
    _minutes.dispose();
    super.dispose();
  }

  void _save() {
    final value = double.tryParse(_minutes.text.trim());
    // The server's bound: one sitting of at most 10 hours.
    if (value == null || value < 1 || value > 600) {
      setState(() => _error = 'Enter the minutes, between 1 and 600.');
      return;
    }
    Navigator.of(context).pop(_BaselineChoice(value));
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text("${widget.term.name}'s baseline"),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('How many minutes does a teacher at this school take to set '
              'a full paper and its answer key by hand? Time saved this term is '
              'measured against it, and says it is your figure.'),
          const SizedBox(height: 16),
          TextField(
            controller: _minutes,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: 'Minutes per paper',
              errorText: _error,
            ),
            onSubmitted: (_) => _save(),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        if (widget.term.manualBaselineMinutes != null)
          TextButton(
            onPressed: () => Navigator.of(context).pop(const _BaselineChoice(null)),
            child: const Text('Use the default'),
          ),
        FilledButton(onPressed: _save, child: const Text('Save')),
      ],
    );
  }
}
