import 'package:flutter/material.dart';

import '../../../data/datasources/api/pillar_api.dart';

/// What the school is paying for, in two numbers: the time the product saved
/// on papers, and what its question bank holds for the classes it sells.
///
/// Both come from endpoints that have worked and been principal-gated since
/// before the first release -- `GET /paper-timing` and `GET /catalog` -- and
/// that no screen called until now. Four audits running, wiring them up was
/// the cheapest improvement available and it was never done.
///
/// Two rules this card exists to keep:
///  * a zero that means "nothing has been measured" never prints as a
///    measurement. "0 minutes saved per paper" reads as a finding; it is
///    arithmetic on an empty set;
///  * the server's own caveat about the DECLARED baseline is rendered
///    verbatim beside the saving, because that number gets quoted at people.
class InsightsCard extends StatelessWidget {
  const InsightsCard({super.key, required this.timing, required this.catalog});

  final PaperTiming timing;
  final Catalog catalog;

  /// The classes this release serves. A principal deciding whether to renew
  /// should not be shown Class 12 Odissi beside their own classes when we
  /// cannot set a paper for it (docs/product-scorecard.md, "Classes in
  /// scope").
  static const _grades = [6, 7, 8, 9, 10];

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

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rows = [
      for (final e in catalog.entries)
        if (_grades.contains(e.grade)) e,
    ]..sort((a, b) => a.grade == b.grade
        ? a.subject.compareTo(b.subject)
        : a.grade.compareTo(b.grade));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Time saved', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            if (timing.nothingMeasuredYet)
              Text(
                'No paper has been generated through the web app yet, so there is '
                'nothing to measure. This fills in as your teachers set papers.',
                style: theme.textTheme.bodyMedium,
              )
            else ...[
              Text('${timing.papers} papers set through the web app',
                  style: theme.textTheme.bodyMedium),
              const SizedBox(height: 4),
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
            const Divider(height: 24),
            // Collapsed by default: this card sits at the top of the Coverage
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
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        e.questionCount == 0
                            ? 'Class ${e.grade} ${e.subject}: no questions yet'
                            : 'Class ${e.grade} ${e.subject}: ${e.questionCount} questions, '
                                '${e.chapters} chapters, marks '
                                '${e.marksAvailable.join(", ")}',
                        style: theme.textTheme.bodyMedium,
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
