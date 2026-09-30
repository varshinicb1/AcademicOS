import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The "Terms" card on the principal's Calendar & Setup tab.
///
/// Exam coverage and time saved are counted per term (PRD decision 11), and a
/// school declares its own terms because CBSE schools split the year
/// differently. Until 2026-09-28 the web had no way to declare one: a school
/// set up the documented way had no term, so the per-term views read "all
/// time" and a term's baseline could not be set (audit D27).
///
/// Lists the year's terms and adds, edits and removes them through the
/// curriculum term routes. The server is the one judge of a term (inside the
/// year, no overlap by even a day, no repeated name) and its sentence is shown
/// as it comes; the card checks only what it can say sooner -- a date that is
/// not a date, or an end before the start.
class TermsCard extends StatefulWidget {
  final CurriculumApi api;
  final AcademicYearSummary year;
  final void Function(String message) onMessage;

  /// Called after a term is added, changed or removed, so figures counted
  /// per term can be read again.
  final VoidCallback? onChanged;

  const TermsCard({super.key, required this.api, required this.year, required this.onMessage, this.onChanged});

  /// The usual CBSE split of [start]..[end]: Term 1 to 30 September, Term 2
  /// from 1 October. A year with no 1 October strictly inside it is halved.
  static (String, String, String, String) twoTerms(String start, String end) {
    final s = DateTime.parse(start), e = DateTime.parse(end);
    var split = DateTime(s.month < 10 ? s.year : s.year + 1, 10, 1);
    if (!split.isAfter(s) || split.isAfter(e)) {
      split = s.add(Duration(days: e.difference(s).inDays ~/ 2 + 1));
    }
    return (start, iso(split.subtract(const Duration(days: 1))), iso(split), end);
  }

  static String iso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  static const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  /// "2026-04-01" -> "1 Apr 2026".
  static String readable(String isoDate) {
    final d = DateTime.tryParse(isoDate);
    return d == null ? isoDate : '${d.day} ${_months[d.month - 1]} ${d.year}';
  }

  @override
  State<TermsCard> createState() => _TermsCardState();
}

class _TermsCardState extends State<TermsCard> {
  List<TermInfo>? _terms;
  String? _loadError;
  bool _busy = false;

  /// The term being edited, or null when the form adds one.
  TermInfo? _editing;
  final _name = TextEditingController();
  final _start = TextEditingController();
  final _end = TextEditingController();
  String? _formError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(TermsCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.year.id != widget.year.id) _load();
  }

  @override
  void dispose() {
    _name.dispose();
    _start.dispose();
    _end.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loadError = null;
      _terms = null;
    });
    try {
      final terms = await widget.api.terms(widget.year.id);
      terms.sort((a, b) => a.startDate.compareTo(b.startDate));
      if (mounted) setState(() => _terms = terms);
    } catch (e) {
      if (mounted) setState(() => _loadError = serverErrorMessage(e));
    }
  }

  void _edit(TermInfo? t) {
    setState(() {
      _editing = t;
      _formError = null;
      _name.text = t?.name ?? '';
      _start.text = t?.startDate ?? '';
      _end.text = t?.endDate ?? '';
    });
  }

  /// The sentence to show before sending, or null when the form is fit to send.
  String? _check(String name, String start, String end) {
    if (name.isEmpty) return 'Give the term a name, such as "Term 1".';
    final s = DateTime.tryParse(start), e = DateTime.tryParse(end);
    if (s == null || start.length != 10) return 'Enter the start date as YYYY-MM-DD.';
    if (e == null || end.length != 10) return 'Enter the end date as YYYY-MM-DD.';
    if (e.isBefore(s)) return 'The term ends before it starts.';
    return null;
  }

  Future<void> _save() async {
    final name = _name.text.trim(), start = _start.text.trim(), end = _end.text.trim();
    final problem = _check(name, start, end);
    if (problem != null) {
      setState(() => _formError = problem);
      return;
    }
    final editing = _editing;
    setState(() {
      _busy = true;
      _formError = null;
    });
    try {
      if (editing == null) {
        await widget.api.createTerm(widget.year.id, name: name, startDate: start, endDate: end);
        widget.onMessage('Term "$name" added.');
      } else {
        await widget.api.updateTerm(editing.id, name: name, startDate: start, endDate: end);
        widget.onMessage('Term "$name" saved.');
      }
      _edit(null);
      await _load();
      widget.onChanged?.call();
    } catch (e) {
      if (mounted) setState(() => _formError = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _addUsualTwo() async {
    final (s1, e1, s2, e2) = TermsCard.twoTerms(widget.year.startDate, widget.year.endDate);
    setState(() {
      _busy = true;
      _formError = null;
    });
    try {
      await widget.api.createTerm(widget.year.id, name: 'Term 1', startDate: s1, endDate: e1);
      await widget.api.createTerm(widget.year.id, name: 'Term 2', startDate: s2, endDate: e2);
      widget.onMessage('Term 1 and Term 2 added.');
    } catch (e) {
      if (mounted) setState(() => _formError = serverErrorMessage(e));
    } finally {
      // Reloaded whatever happened: if Term 1 went in and Term 2 did not, the
      // list says so rather than the button offering to add both again.
      await _load();
      widget.onChanged?.call();
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _remove(TermInfo t) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Remove ${t.name}?'),
        content: const Text('Papers are not deleted. Exam coverage and time saved stop being '
            'counted for these dates, and the term\'s own baseline is removed with it.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Keep')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Remove')),
        ],
      ),
    );
    if (ok != true) return;
    setState(() => _busy = true);
    try {
      await widget.api.deleteTerm(t.id);
      widget.onMessage('Term "${t.name}" removed.');
      if (_editing?.id == t.id) _edit(null);
      await _load();
      widget.onChanged?.call();
    } catch (e) {
      widget.onMessage('Could not remove ${t.name}: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pick(TextEditingController field) async {
    final first = DateTime.parse(widget.year.startDate), last = DateTime.parse(widget.year.endDate);
    final now = DateTime.tryParse(field.text.trim()) ?? first;
    final picked = await showDatePicker(
      context: context,
      initialDate: now.isBefore(first) ? first : (now.isAfter(last) ? last : now),
      firstDate: first,
      lastDate: last,
    );
    if (picked != null) setState(() => field.text = TermsCard.iso(picked));
  }

  Widget _dateField(String label, TextEditingController c, Key key) => TextField(
        key: key,
        controller: c,
        keyboardType: TextInputType.datetime,
        decoration: InputDecoration(
          labelText: label,
          hintText: 'YYYY-MM-DD',
          suffixIcon: IconButton(
            tooltip: 'Choose $label',
            icon: const Icon(Icons.event),
            onPressed: _busy ? null : () => _pick(c),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    final year = widget.year;
    final terms = _terms;
    return AppCard(
      key: const ValueKey('terms-card'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Terms', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(4),
          Text(
            'Exam coverage and time saved are counted per term. '
            '${year.label.isEmpty ? 'This year' : year.label} runs ${TermsCard.readable(year.startDate)} '
            'to ${TermsCard.readable(year.endDate)}.',
            style: muted,
          ),
          const Gap(12),
          if (_loadError != null) ...[
            Text('Could not load the terms: $_loadError', style: TextStyle(color: theme.colorScheme.error)),
            const Gap(8),
            OutlinedButton(onPressed: _load, style: phoneTapTarget(context), child: const Text('Retry')),
          ] else if (terms == null)
            const LinearProgressIndicator()
          else ...[
            if (terms.isEmpty) ...[
              const Text('No terms yet. Most CBSE schools use two.', key: ValueKey('terms-empty')),
              const Gap(8),
              Builder(builder: (context) {
                final (s1, e1, s2, e2) = TermsCard.twoTerms(year.startDate, year.endDate);
                return FilledButton.tonalIcon(
                  key: const ValueKey('terms-add-two'),
                  onPressed: _busy ? null : _addUsualTwo,
                  style: phoneTapTarget(context),
                  icon: const Icon(Icons.playlist_add),
                  label: Text('Add Term 1 (${TermsCard.readable(s1)} - ${TermsCard.readable(e1)}) and '
                      'Term 2 (${TermsCard.readable(s2)} - ${TermsCard.readable(e2)})'),
                );
              }),
              const Gap(12),
            ],
            for (final t in terms)
              ListTile(
                key: ValueKey('term-${t.id}'),
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.date_range_outlined),
                title: Text(t.name),
                subtitle: Text('${TermsCard.readable(t.startDate)} - ${TermsCard.readable(t.endDate)}'),
                trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                  IconButton(
                    tooltip: 'Edit ${t.name}',
                    icon: const Icon(Icons.edit_outlined),
                    onPressed: _busy ? null : () => _edit(t),
                  ),
                  IconButton(
                    tooltip: 'Remove ${t.name}',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: _busy ? null : () => _remove(t),
                  ),
                ]),
              ),
            const Gap(8),
            Text(_editing == null ? 'Add a term' : 'Edit ${_editing!.name}',
                style: theme.textTheme.labelLarge),
            const Gap(8),
            TextField(
              key: const ValueKey('term-name'),
              controller: _name,
              decoration: const InputDecoration(labelText: 'Name', hintText: 'Term 1'),
            ),
            const Gap(12),
            _dateField('Start date', _start, const ValueKey('term-start')),
            const Gap(12),
            _dateField('End date', _end, const ValueKey('term-end')),
            if (_formError != null) ...[
              const Gap(8),
              Text(_formError!, key: const ValueKey('term-error'), style: TextStyle(color: theme.colorScheme.error)),
            ],
            const Gap(12),
            Wrap(spacing: 8, runSpacing: 8, children: [
              FilledButton.icon(
                key: const ValueKey('term-save'),
                onPressed: _busy ? null : _save,
                style: phoneTapTarget(context),
                icon: _busy
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : Icon(_editing == null ? Icons.add : Icons.save_outlined),
                label: Text(_editing == null ? 'Add term' : 'Save term'),
              ),
              if (_editing != null)
                TextButton(onPressed: _busy ? null : () => _edit(null), style: phoneTapTarget(context), child: const Text('Cancel')),
            ]),
          ],
        ],
      ),
    );
  }
}
