import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The days that run differently, on the principal's Calendar & Setup tab
/// (v3 audit N-3-19): a half day, an exam window, or a weekly off made a
/// working day (a compensatory Saturday).
///
/// The calendar knew only weekly offs, alternate Saturdays and closures, so
/// none of these could be entered. Each is a calendar row the day view, cover,
/// the lesson plans and the apps read: a half day keeps periods 1 to its last
/// one, an exam window stops teaching for the classes chosen (every class when
/// none is), and a working day runs the timetable of the weekday chosen. The
/// lesson plans it touches move when it is added, and back when it is
/// removed. The server judges the request (an exam window's classes must be
/// this year's; a working day must be an off day) and its sentence is shown.
class CalendarDaysCard extends StatefulWidget {
  final CurriculumApi api;
  final String academicYearId;

  /// The year's class numbers, for an exam window's choice.
  final List<int> grades;
  final void Function(String message) onMessage;

  /// Called after a day is added, so the list and the counts are read again.
  final VoidCallback? onChanged;

  const CalendarDaysCard({
    super.key,
    required this.api,
    required this.academicYearId,
    required this.grades,
    required this.onMessage,
    this.onChanged,
  });

  @override
  State<CalendarDaysCard> createState() => _CalendarDaysCardState();
}

class _CalendarDaysCardState extends State<CalendarDaysCard> {
  static const _kinds = {'half_day': 'Half day', 'exam_window': 'Exam window', 'working_day': 'Working day'};

  String _kind = 'half_day';
  final _label = TextEditingController();
  final _date = TextEditingController();
  final _end = TextEditingController();
  int _lastPeriod = 4;
  final Set<int> _grades = {};
  int _weekday = 0;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _label.dispose();
    _date.dispose();
    _end.dispose();
    super.dispose();
  }

  static bool _isDate(String s) => s.length == 10 && DateTime.tryParse(s) != null;

  /// The sentence to show before sending, or null when the form is fit to send.
  String? _check(String label, String date, String end) {
    if (label.isEmpty) return 'Give the day a name, such as "PTM" or "Half-yearly exams".';
    if (!_isDate(date)) return 'Enter the date as YYYY-MM-DD.';
    if (end.isNotEmpty && !_isDate(end)) return 'Enter the last day as YYYY-MM-DD, or leave it empty.';
    if (end.isNotEmpty && end.compareTo(date) < 0) return 'The last day is before the first.';
    return null;
  }

  Future<void> _add() async {
    final label = _label.text.trim(), date = _date.text.trim();
    final end = _kind == 'working_day' ? '' : _end.text.trim();
    final problem = _check(label, date, end);
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final h = await widget.api.addHoliday(
        widget.academicYearId,
        date: date,
        label: label,
        kind: _kind,
        endDate: end.isEmpty ? null : end,
        lastPeriod: _kind == 'half_day' ? _lastPeriod : null,
        grades: _kind == 'exam_window' ? (_grades.toList()..sort()) : null,
        timetableWeekday: _kind == 'working_day' ? _weekday : null,
      );
      final moved = h.lessonsMoved ?? 0;
      widget.onMessage('"$label" added (${h.describe}).'
          '${moved > 0 ? ' $moved lessons moved to fit it.' : ''}');
      _label.clear();
      _end.clear();
      widget.onChanged?.call();
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pick(TextEditingController field) async {
    final now = DateTime.tryParse(field.text.trim()) ?? DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 2),
    );
    if (picked != null) {
      setState(() => field.text = '${picked.year.toString().padLeft(4, '0')}-'
          '${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}');
    }
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

  String get _help => switch (_kind) {
        'half_day' => 'Only the periods up to the last one are held. The later periods need no cover, and '
            'lessons planned in them move to the next period.',
        'exam_window' => 'Teaching stops for the classes chosen (every class when none is). The school stays '
            'open; lessons planned in the window move after it.',
        _ => 'A weekly off or an off Saturday becomes a working day that runs one weekday\'s timetable. '
            'Lessons come forward into it.',
      };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    return AppCard(
      key: const ValueKey('calendar-days-card'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Half days, exam windows and working days',
              style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(8),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final e in _kinds.entries)
              ChoiceChip(
                key: ValueKey('day-kind-${e.key}'),
                label: Text(e.value),
                selected: _kind == e.key,
                onSelected: _busy ? null : (_) => setState(() => _kind = e.key),
              ),
          ]),
          const Gap(8),
          Text(_help, style: muted),
          const Gap(8),
          TextField(
            key: const ValueKey('day-label'),
            controller: _label,
            decoration: InputDecoration(
                labelText: _kind == 'exam_window' ? 'Name (e.g. Half-yearly exams)' : 'Name (e.g. PTM)'),
          ),
          const Gap(8),
          _dateField(_kind == 'working_day' ? 'Date' : 'First day', _date, const ValueKey('day-date')),
          if (_kind != 'working_day') ...[
            const Gap(8),
            _dateField('Last day (optional)', _end, const ValueKey('day-end')),
          ],
          const Gap(8),
          if (_kind == 'half_day')
            DropdownButtonFormField<int>(
              key: const ValueKey('day-last-period'),
              initialValue: _lastPeriod,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Last period held'),
              items: [for (var p = 1; p <= 10; p++) DropdownMenuItem(value: p, child: Text('Period $p'))],
              onChanged: _busy ? null : (v) => setState(() => _lastPeriod = v ?? _lastPeriod),
            ),
          if (_kind == 'exam_window') ...[
            Text('Classes', style: theme.textTheme.bodyMedium),
            const Gap(4),
            if (widget.grades.isEmpty)
              Text('No classes this year yet: the window will stop every class.', style: muted)
            else
              Wrap(spacing: 8, runSpacing: 8, children: [
                for (final g in widget.grades)
                  FilterChip(
                    key: ValueKey('day-grade-$g'),
                    label: Text('Class $g'),
                    selected: _grades.contains(g),
                    onSelected: _busy ? null : (on) => setState(() => on ? _grades.add(g) : _grades.remove(g)),
                  ),
              ]),
            const Gap(4),
            Text(_grades.isEmpty ? 'None chosen: every class.' : '', style: muted),
          ],
          if (_kind == 'working_day')
            DropdownButtonFormField<int>(
              key: const ValueKey('day-weekday'),
              initialValue: _weekday,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Runs the timetable of'),
              items: [
                for (var d = 0; d < 6; d++) DropdownMenuItem(value: d, child: Text(HolidayInfo.weekdayNames[d])),
              ],
              onChanged: _busy ? null : (v) => setState(() => _weekday = v ?? _weekday),
            ),
          if (_error != null) ...[
            const Gap(8),
            Text(_error!, key: const ValueKey('day-error'), style: TextStyle(color: theme.colorScheme.error)),
          ],
          const Gap(12),
          FilledButton.icon(
            key: const ValueKey('day-add'),
            onPressed: _busy ? null : _add,
            style: phoneTapTarget(context),
            icon: _busy
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.add_circle_outline),
            label: Text('Add ${_kinds[_kind]!.toLowerCase()}'),
          ),
        ],
      ),
    );
  }
}
