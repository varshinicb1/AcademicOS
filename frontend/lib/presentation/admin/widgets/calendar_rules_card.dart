import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The "Academic Calendar Rules" card on the principal's Calendar & Setup tab:
/// weekly off day(s) and the Saturday rule, submitted as a create (no saved
/// calendar yet) or an update (PUT) through [onSubmit].
///
/// The menus offer the common choices, but the backend accepts more than they
/// hold: several weekly off days (['saturday', 'sunday']) and Saturday rules
/// such as 'first_third' or '1st,3rd'. Before 2026-09-22 a saved calendar
/// outside the menus left the dropdowns on their default, so pressing
/// "Update Calendar" PUT 'sunday' / 'none' and silently dropped the saved
/// rule. A saved value the menus can't hold is now added to its menu as a
/// "Saved: ..." entry and selected, so an untouched Update re-sends it.
class CalendarRulesCard extends StatefulWidget {
  final CalendarInfo? saved;
  final bool busy;
  final void Function(List<String> weeklyOffDays, String alternateSaturdayRule) onSubmit;

  const CalendarRulesCard({super.key, required this.saved, required this.busy, required this.onSubmit});

  @override
  State<CalendarRulesCard> createState() => _CalendarRulesCardState();
}

class _CalendarRulesCardState extends State<CalendarRulesCard> {
  // Values exactly as the backend's CreateCalendarRequest takes them. Several
  // weekly off days travel as one comma-joined menu value.
  static const _weeklyOffChoices = {'sunday': 'Sunday (Default)', 'saturday': 'Saturday', 'friday': 'Friday'};
  static const _ruleChoices = {
    'none': 'None (All working)',
    'second_fourth': '2nd & 4th Saturdays Off',
    'all': 'All Saturdays Off',
  };

  String _weeklyOff = 'sunday';
  String _rule = 'none';
  // Bumped on every sync so the dropdowns (which read initialValue once)
  // are rebuilt showing the freshly saved values.
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    _syncFromSaved();
  }

  @override
  void didUpdateWidget(CalendarRulesCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.saved, widget.saved)) _syncFromSaved();
  }

  String? get _savedWeeklyOff => widget.saved?.weeklyOffDays.join(',');

  String? get _savedRule {
    final rule = widget.saved?.alternateSaturdayRule;
    // The same rule, spelled the way the menu spells it.
    return rule == '2nd,4th' ? 'second_fourth' : rule;
  }

  void _syncFromSaved() {
    _generation++;
    final saved = widget.saved;
    if (saved == null) {
      // No calendar (e.g. a different year): back to a value the menu holds.
      if (!_weeklyOffChoices.containsKey(_weeklyOff)) _weeklyOff = 'sunday';
      if (!_ruleChoices.containsKey(_rule)) _rule = 'none';
      return;
    }
    _weeklyOff = _savedWeeklyOff!;
    _rule = _savedRule!;
  }

  bool get _savedOutsideMenus =>
      widget.saved != null &&
      (!_weeklyOffChoices.containsKey(_savedWeeklyOff) || !_ruleChoices.containsKey(_savedRule));

  String _dayName(String d) => d.isEmpty ? d : d[0].toUpperCase() + d.substring(1);

  /// Every menu entry ellipsizes rather than overflow. Without this and the
  /// `isExpanded: true` below, the field sizes itself to its widest entry --
  /// '2nd & 4th Saturdays Off' -- which is wider than a 375 px phone's card
  /// and overflowed it by 118 px (Task 801, review of 2026-09-22). Same shape
  /// as the console's own _dropdown<T> helper.
  static Widget _entry(String text) => Text(text, overflow: TextOverflow.ellipsis);

  List<DropdownMenuItem<String>> _weeklyOffItems() {
    final items = [
      for (final e in _weeklyOffChoices.entries) DropdownMenuItem(value: e.key, child: _entry(e.value)),
    ];
    final saved = _savedWeeklyOff;
    if (saved != null && !_weeklyOffChoices.containsKey(saved)) {
      final days = widget.saved!.weeklyOffDays;
      items.add(DropdownMenuItem(
        value: saved,
        child: _entry('Saved: ${days.isEmpty ? 'no weekly off day' : days.map(_dayName).join(' & ')}'),
      ));
    }
    return items;
  }

  List<DropdownMenuItem<String>> _ruleItems() {
    final items = [
      for (final e in _ruleChoices.entries) DropdownMenuItem(value: e.key, child: _entry(e.value)),
    ];
    final saved = _savedRule;
    if (saved != null && !_ruleChoices.containsKey(saved)) {
      items.add(DropdownMenuItem(value: saved, child: _entry('Saved: $saved')));
    }
    return items;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final saved = widget.saved;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Academic Calendar Rules', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(8),
          if (saved != null) ...[
            Text(
              'Saved: weekly off ${saved.weeklyOffDays.join(', ')}; '
              'Saturday rule ${saved.alternateSaturdayRule}',
              style: theme.textTheme.bodySmall,
            ),
            if (_savedOutsideMenus)
              Text(
                'The saved rules include a choice the standard menus do not offer; it is '
                'selected below as "Saved: ..." and kept on Update unless you pick another.',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
            const Gap(8),
          ],
          DropdownButtonFormField<String>(
            key: ValueKey('weekly-off-$_generation'),
            initialValue: _weeklyOff,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Weekly Off Day', border: OutlineInputBorder()),
            items: _weeklyOffItems(),
            onChanged: (v) => setState(() => _weeklyOff = v ?? 'sunday'),
          ),
          const Gap(12),
          DropdownButtonFormField<String>(
            key: ValueKey('alt-sat-$_generation'),
            initialValue: _rule,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Alternate Saturday Rule', border: OutlineInputBorder()),
            items: _ruleItems(),
            onChanged: (v) => setState(() => _rule = v ?? 'none'),
          ),
          const Gap(12),
          FilledButton.icon(
            onPressed: widget.busy
                ? null
                : () => widget.onSubmit(
                    _weeklyOff.split(',').where((d) => d.isNotEmpty).toList(), _rule),
            style: phoneTapTarget(context),
            icon: widget.busy
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.calendar_month),
            label: Text(saved == null ? 'Initialize Calendar' : 'Update Calendar'),
          ),
        ],
      ),
    );
  }
}
