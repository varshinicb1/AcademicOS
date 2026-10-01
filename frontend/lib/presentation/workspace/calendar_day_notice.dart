// The school calendar's say about one day (v3 audit N-3-19): a holiday, a
// half day, an exam window or a compensatory working day, from the caller's
// own calendar (`GET /my-calendar`). The apps listed holidays only in the
// calendar feed; the student's Today said "A holiday, a weekly off, or no
// timetable yet" whatever the day was.
import 'package:flutter/material.dart';

import '../shared/widgets/common_widgets.dart';

/// The icon for each kind of calendar item, shared by the week's "Coming up"
/// list and the day pages.
const calendarKindIcons = <String, IconData>{
  'holiday': Icons.beach_access_outlined,
  'half_day': Icons.timelapse,
  'exam_window': Icons.edit_calendar,
  'working_day': Icons.event_available,
  'exam': Icons.edit_note,
  'invigilation': Icons.visibility_outlined,
  'cover': Icons.swap_horiz,
  'homework': Icons.assignment_outlined,
};

const _dayKinds = {'holiday', 'half_day', 'exam_window', 'working_day'};

/// The calendar items that say how `isoDay` runs: holidays, half days, exam
/// windows and working days whose dates cover it.
List<Map<String, dynamic>> calendarDayItems(List<Map<String, dynamic>> items, String isoDay) => [
      for (final i in items)
        if (_dayKinds.contains(i['kind']) &&
            (i['date'] as String).compareTo(isoDay) <= 0 &&
            ((i['endDate'] ?? i['date']) as String).compareTo(isoDay) >= 0)
          i,
    ];

/// One card listing the day's calendar items; nothing when there are none.
class CalendarDayNotice extends StatelessWidget {
  final List<Map<String, dynamic>> items;
  const CalendarDayNotice(this.items, {super.key});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    return AppCard(
      key: const ValueKey('calendar-day-notice'),
      margin: const EdgeInsets.only(bottom: 12),
      color: theme.colorScheme.secondaryContainer,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        for (final i in items)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(children: [
              Icon(calendarKindIcons[i['kind']] ?? Icons.event_outlined),
              const SizedBox(width: 12),
              Expanded(child: Text(i['title'] as String? ?? '')),
            ]),
          ),
      ]),
    );
  }
}
