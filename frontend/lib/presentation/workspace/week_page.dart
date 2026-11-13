import 'package:flutter/material.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'calendar_day_notice.dart';
import 'ops_api.dart';
import 'strings.dart';
import '../shared/widgets/shell.dart';

const _dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/// The week (TA-2, SA-1): what is coming up (holidays, half days, exam
/// windows and working days, exams, duties and homework due -- the same
/// events as the calendar link), a teacher's own
/// load, and the timetable as a grid of days by periods with the bell's
/// times. Each part loads on its own, so one failing does not blank the page.
///
/// Redesigned 2026-10-04: the timetable was a plain table that left the right of a wide window
/// empty and was a horizontal scroll on a phone. It is now a full-width grid, coloured by subject,
/// with today's column and the period under way marked; on a phone it is one day at a time, picked
/// from a row of day chips.
class WeekPage extends StatefulWidget {
  const WeekPage({super.key});

  @override
  State<WeekPage> createState() => _WeekPageState();
}

class _WeekPageState extends State<WeekPage> {
  late Future<Map<String, dynamic>> _week;
  late Future<List<Map<String, dynamic>>> _coming;
  Future<Map<String, dynamic>>? _load;

  bool get _student => CurrentSession.role == 'student';

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  void _fetch() {
    _week = Ops.map('/curriculum/my-timetable');
    _coming = Ops.list('/my-calendar');
    _load = _student ? null : Ops.map('/my-load');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('My week'))),
      body: RefreshIndicator(
        onRefresh: () async => setState(_fetch),
        child: ListView(
          padding: const EdgeInsets.only(bottom: 32),
          children: [
            _Centered(child: _WeekHeader(week: _week)),
            _Centered(child: _SectionTitle(tr('Coming up'))),
            _Centered(
              child: FutureBuilder<List<Map<String, dynamic>>>(
                future: _coming,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
                  if (snap.hasError) return _Notice(serverErrorMessage(snap.error!));
                  final items = snap.data!;
                  if (items.isEmpty) return _Notice(tr('Nothing in the next six weeks'));
                  return _ComingList(items);
                },
              ),
            ),
            if (_load != null) ...[
              _Centered(child: _SectionTitle(tr('My load'))),
              _Centered(
                child: FutureBuilder<Map<String, dynamic>>(
                  future: _load,
                  builder: (context, snap) {
                    if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
                    if (snap.hasError) return _Notice(serverErrorMessage(snap.error!));
                    return _LoadCard(snap.data!);
                  },
                ),
              ),
            ],
            _Centered(child: _SectionTitle(tr('Timetable'))),
            _Centered(
              child: FutureBuilder<Map<String, dynamic>>(
                future: _week,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
                  if (snap.hasError) {
                    return ErrorDisplay(message: serverErrorMessage(snap.error!),
                        onRetry: () => setState(_fetch));
                  }
                  final d = snap.data!;
                  if ((d['entries'] as List).isEmpty) {
                    return EmptyState(icon: Icons.calendar_view_week, title: tr('No timetable yet'),
                        message: tr('The school has not published a timetable for you yet.'));
                  }
                  return _Timetable(d, student: _student);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Keeps a page's content to a readable width and centred, instead of hugging the left edge of a wide window.
class _Centered extends StatelessWidget {
  final Widget child;
  const _Centered({required this.child});

  @override
  Widget build(BuildContext context) => Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1080),
          // Full width up to the cap, so a heading starts at the cards' left edge instead of centring.
          child: SizedBox(
            width: double.infinity,
            child: Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: child),
          ),
        ),
      );
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(2, 24, 0, 10),
        child: Text(text, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
      );
}

/// The dates of the week being shown, Monday first: this week, or next week from Sunday on (the
/// timetable on a Sunday is Monday's).
List<DateTime> weekDates(DateTime now) {
  final today = DateTime(now.year, now.month, now.day);
  final monday = today.add(Duration(days: now.weekday == DateTime.sunday ? 1 : 1 - now.weekday));
  return [for (var i = 0; i < 7; i++) monday.add(Duration(days: i))];
}

/// Minutes after midnight for "08:45", or null for anything else.
int? clockMinutes(String? hhmm) {
  final m = RegExp(r'^(\d{1,2}):(\d{2})').firstMatch(hhmm ?? '');
  return m == null ? null : int.parse(m[1]!) * 60 + int.parse(m[2]!);
}

/// A subject's colour: the same subject is the same colour on every day and every page, and the common
/// subjects keep their own.
Color subjectColor(String subject) {
  const palette = [
    Color(0xFFC2410C), Color(0xFF1D4ED8), Color(0xFF0B7A5A), Color(0xFF7C3AED),
    Color(0xFFB45309), Color(0xFF0E7490), Color(0xFFBE185D), Color(0xFF4D7C0F),
  ];
  final key = subject.toLowerCase().trim();
  const fixed = {
    'mathematics': 1, 'maths': 1, 'math': 1, 'science': 2, 'english': 0, 'hindi': 4,
    'social science': 3, 'social studies': 3, 'computer': 5, 'computer science': 5, 'evs': 7,
  };
  final named = fixed[key];
  if (named != null) return palette[named];
  var h = 0;
  for (final c in key.codeUnits) {
    h = (h * 31 + c) & 0x7fffffff;
  }
  return palette[h % palette.length];
}

/// The week's dates, and how much is in it.
class _WeekHeader extends StatelessWidget {
  final Future<Map<String, dynamic>> week;
  const _WeekHeader({required this.week});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dates = weekDates(DateTime.now());
    final first = dates.first, last = dates[5];
    final range = first.month == last.month
        ? '${first.day} – ${last.day} ${tr(_months[last.month - 1])}'
        : '${first.day} ${tr(_months[first.month - 1])} – ${last.day} ${tr(_months[last.month - 1])}';
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 16, 0, 0),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(range, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 2),
        FutureBuilder<Map<String, dynamic>>(
          future: week,
          builder: (context, snap) {
            final entries = snap.hasData ? (snap.data!['entries'] as List).cast<Map>() : const <Map>[];
            if (entries.isEmpty) return Text(tr('This week'), style: theme.textTheme.bodyMedium);
            final subjects = {for (final e in entries) e['subjectName']}.length;
            return Text(trf('{n} lessons · {s} subjects', {'n': entries.length, 's': subjects}),
                style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant));
          },
        ),
      ]),
    );
  }
}

/// "Mon 8 Jun", or Today/Tomorrow, then the times or the last day.
String calendarWhen(Map item, DateTime today) {
  final d = DateTime.parse(item['date'] as String);
  final day = DateTime(today.year, today.month, today.day);
  final gap = DateTime(d.year, d.month, d.day).difference(day).inDays;
  String label(DateTime x) => '${tr(_dayNames[x.weekday - 1])} ${x.day} ${tr(_months[x.month - 1])}';
  final when = gap == 0 ? tr('Today') : gap == 1 ? tr('Tomorrow') : label(d);
  final end = item['endDate'] as String?;
  if (end != null && end != item['date']) return '$when – ${label(DateTime.parse(end))}';
  final start = item['startTime'] as String?;
  if (start != null) return '$when · $start–${item['endTime'] ?? ''}';
  return when;
}

/// The next few things in one card: a date badge, what it is, and when. More than five fold away.
class _ComingList extends StatefulWidget {
  final List<Map<String, dynamic>> items;
  const _ComingList(this.items);

  @override
  State<_ComingList> createState() => _ComingListState();
}

class _ComingListState extends State<_ComingList> {
  static const _shown = 5;
  bool _all = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final items = widget.items;
    final visible = _all ? items : items.take(_shown).toList();
    return AppCard(
      padding: const EdgeInsets.symmetric(vertical: 6),
      margin: EdgeInsets.zero,
      child: Column(children: [
        for (var i = 0; i < visible.length; i++) ...[
          if (i > 0) Divider(height: 1, indent: 76, color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5)),
          _ComingTile(visible[i]),
        ],
        if (items.length > _shown)
          TextButton(
            key: const ValueKey('week-coming-toggle'),
            onPressed: () => setState(() => _all = !_all),
            child: Text(_all ? tr('Show fewer') : '${tr('Show all')} (${items.length})'),
          ),
      ]),
    );
  }
}

class _ComingTile extends StatelessWidget {
  final Map<String, dynamic> item;
  const _ComingTile(this.item);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final date = DateTime.tryParse(item['date'] as String? ?? '');
    final today = DateTime.now();
    final isToday = date != null && date.year == today.year && date.month == today.month && date.day == today.day;
    final accent = isToday ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      child: Row(children: [
        Container(
          width: 48,
          padding: const EdgeInsets.symmetric(vertical: 6),
          decoration: BoxDecoration(
            color: accent.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(children: [
            Text(date == null ? '' : tr(_dayNames[date.weekday - 1]).toUpperCase(),
                style: theme.textTheme.labelSmall?.copyWith(color: accent, fontWeight: FontWeight.w700)),
            Text(date == null ? '' : '${date.day}',
                style: theme.textTheme.titleMedium?.copyWith(color: accent, fontWeight: FontWeight.w800, height: 1.1)),
          ]),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(item['title'] as String? ?? '', style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text(calendarWhen(item, DateTime.now()),
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ]),
        ),
        Icon(calendarKindIcons[item['kind']] ?? Icons.event_outlined, size: 20, color: theme.colorScheme.onSurfaceVariant),
      ]),
    );
  }
}

class _LoadCard extends StatelessWidget {
  final Map<String, dynamic> load;
  const _LoadCard(this.load);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final days = (load['daysTaught'] as Map?)?.map((k, v) => MapEntry(int.parse('$k'), v as int)) ?? {};
    final busiest = days.entries.isEmpty ? null : days.entries.reduce((a, b) => b.value > a.value ? b : a);
    final classes = ((load['classes'] as List?) ?? const []).cast<Map>();
    return AppCard(
      margin: EdgeInsets.zero,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(trf('{n} periods a week', {'n': load['periodsPerWeek'] ?? 0}), style: theme.textTheme.titleMedium),
        if (busiest != null)
          Text('${tr('Busiest day')}: ${tr(_dayNames[busiest.key])} (${busiest.value})',
              style: theme.textTheme.bodySmall),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final c in classes)
            Chip(label: Text('${c['sectionName']} ${c['subjectName']} · ${c['periodsPerWeek']}')),
        ]),
        const SizedBox(height: 8),
        Text('${tr('Covers this week')}: ${load['coversThisWeek'] ?? 0}  ·  '
            '${tr('Exam duties ahead')}: ${load['invigilationsAhead'] ?? 0}',
            style: theme.textTheme.bodyMedium),
      ]),
    );
  }
}

class _Notice extends StatelessWidget {
  final String text;
  const _Notice(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Text(text, style: Theme.of(context).textTheme.bodyMedium),
      );
}

/// The time of one period, from its own section's bell, as the server
/// sends it with each entry (audit N-3-15); null when it sent none.
String? entryTime(Map e) => e['startTime'] == null ? null : '${e['startTime']}-${e['endTime']}';

/// Each row's label time. A teacher's periods can sit on two bells (a junior
/// wing's and the main one), so a row is labelled with the time its own
/// periods share; a row whose periods differ gets no label time (each cell
/// then shows its own), and an empty row takes the bell's.
Map<int, String?> rowTimes(List<Map> entries, Map<int, String> bellTimes, Iterable<int> periods) => {
      for (final p in periods)
        p: () {
          final own = {for (final e in entries) if (e['period'] == p && entryTime(e) != null) entryTime(e)!};
          return own.length == 1 ? own.single : own.isEmpty ? bellTimes[p] : null;
        }(),
    };

/// The timetable: a grid of days across and periods down where there is room, and one day at a time,
/// picked from a row of day chips, on a phone.
class _Timetable extends StatefulWidget {
  final Map<String, dynamic> d;
  final bool student;
  const _Timetable(this.d, {required this.student});

  @override
  State<_Timetable> createState() => _TimetableState();
}

class _TimetableState extends State<_Timetable> {
  /// 0 = Monday. Opens on today, or Monday on a day with no school.
  late int _day = _todayIndex(DateTime.now()) ?? 0;
  late final List<int> _days;
  late final List<int> _periods;
  late final Map<int, String?> _times;
  late final Map<(int, int), Map> _cell;

  /// Today's column (0 = Monday), or null on a Sunday.
  static int? _todayIndex(DateTime now) => now.weekday > 6 ? null : now.weekday - 1;

  @override
  void initState() {
    super.initState();
    final entries = (widget.d['entries'] as List).cast<Map>();
    final bell = widget.d['bellSchedule'] as Map?;
    final bellTimes = <int, String>{
      for (final s in ((bell?['slots'] as List?) ?? const []).cast<Map>())
        if (s['period'] != null) s['period'] as int: '${s['start']}-${s['end']}',
    };
    _days = ((bell?['days'] as List?)?.cast<int>() ?? [0, 1, 2, 3, 4, 5]).toList()..sort();
    final all = {for (final e in entries) e['period'] as int, ...bellTimes.keys}.toList()..sort();
    _times = rowTimes(entries, bellTimes, all);
    _cell = {for (final e in entries) (e['dayOfWeek'] as int, e['period'] as int): e};
    // A period nothing is taught in all week, at the start or the end of the day, is left out: an empty
    // first or last row is noise. One in the middle stays, as a gap in the day.
    final taught = [for (final p in all) if (_days.any((d) => _cell[(d, p)] != null)) p];
    _periods = taught.isEmpty ? all : [for (final p in all) if (p >= taught.first && p <= taught.last) p];
    if (!_days.contains(_day)) _day = _days.first;
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
        builder: (context, box) => box.maxWidth >= 720 ? _wide(context) : _narrow(context),
      );

  bool _rowEmpty(int p) => _days.every((d) => _cell[(d, p)] == null);

  Widget _wide(BuildContext context) {
    final theme = Theme.of(context);
    final dates = weekDates(DateTime.now());
    final today = _todayIndex(DateTime.now());
    return AppCard(
      margin: EdgeInsets.zero,
      padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
      child: Column(children: [
        Row(children: [
          const SizedBox(width: 78),
          for (final day in _days)
            Expanded(
              child: _DayHead(name: tr(_dayNames[day]), date: dates[day].day, today: day == today),
            ),
        ]),
        const SizedBox(height: 8),
        for (final p in _periods)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: IntrinsicHeight(
              child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                SizedBox(
                  width: 78,
                  child: Padding(
                    padding: const EdgeInsets.only(left: 4, top: 8),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('P$p', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
                      if (_times[p] != null)
                        Text(_times[p]!,
                            style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                    ]),
                  ),
                ),
                if (_rowEmpty(p))
                  // Nothing is taught in this period on any day: one band across the week, not six cells.
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 3),
                      child: _PeriodCell(
                          entry: null, student: widget.student, rowTime: _times[p], isToday: false, gap: true),
                    ),
                  )
                else
                  for (final day in _days)
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 3),
                        child: _PeriodCell(
                          entry: _cell[(day, p)],
                          student: widget.student,
                          rowTime: _times[p],
                          isToday: day == today,
                          gap: false,
                        ),
                      ),
                    ),
              ]),
            ),
          ),
      ]),
    );
  }

  Widget _narrow(BuildContext context) {
    final theme = Theme.of(context);
    final dates = weekDates(DateTime.now());
    final today = _todayIndex(DateTime.now());
    final lessons = [for (final p in _periods) (p, _cell[(_day, p)])];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(
        height: 64,
        child: Row(children: [
          for (final day in _days)
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 3),
                child: _DayChip(
                  key: ValueKey('week-day-$day'),
                  name: tr(_dayNames[day]),
                  date: dates[day].day,
                  selected: day == _day,
                  today: day == today,
                  onTap: () => setState(() => _day = day),
                ),
              ),
            ),
        ]),
      ),
      const SizedBox(height: 12),
      if (lessons.every((l) => l.$2 == null))
        _Notice(tr('No lessons'))
      else
        for (final (p, e) in lessons)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: IntrinsicHeight(child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              SizedBox(
                width: 64,
                child: Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('P$p', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
                    if (_timeOf(e, p) != null)
                      Text(_timeOf(e, p)!.replaceAll('-', '\n'),
                          style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  ]),
                ),
              ),
              Expanded(
                child: _PeriodCell(
                  entry: e,
                  student: widget.student,
                  rowTime: _times[p],
                  isToday: _day == today,
                  gap: e == null,
                  roomy: true,
                ),
              ),
            ])),
          ),
    ]);
  }

  /// A period's own time (its section's bell), else the row's.
  String? _timeOf(Map? e, int p) => (e == null ? null : entryTime(e)) ?? _times[p];
}

class _DayHead extends StatelessWidget {
  final String name;
  final int date;
  final bool today;
  const _DayHead({required this.name, required this.date, required this.today});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final fg = today ? theme.colorScheme.onPrimary : theme.colorScheme.onSurfaceVariant;
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: today ? theme.colorScheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text(name, style: theme.textTheme.labelLarge?.copyWith(color: fg, fontWeight: FontWeight.w700)),
          const SizedBox(width: 6),
          Text('$date', style: theme.textTheme.labelLarge?.copyWith(color: fg.withValues(alpha: 0.8))),
        ]),
      ),
    );
  }
}

class _DayChip extends StatelessWidget {
  final String name;
  final int date;
  final bool selected, today;
  final VoidCallback onTap;
  const _DayChip({super.key, required this.name, required this.date, required this.selected, required this.today,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final primary = theme.colorScheme.primary;
    final fg = selected ? theme.colorScheme.onPrimary : theme.colorScheme.onSurface;
    return Semantics(
      button: true,
      selected: selected,
      label: '$name $date',
      excludeSemantics: true,
      child: Material(
        color: selected ? primary : theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Container(
            decoration: today && !selected
                ? BoxDecoration(borderRadius: BorderRadius.circular(14), border: Border.all(color: primary, width: 1.5))
                : null,
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              Text(name, style: theme.textTheme.labelMedium?.copyWith(color: fg.withValues(alpha: 0.85))),
              Text('$date', style: theme.textTheme.titleMedium?.copyWith(color: fg, fontWeight: FontWeight.w800)),
            ]),
          ),
        ),
      ),
    );
  }
}

/// One period of one day: coloured by its subject, with the teacher (or the class, for a teacher). A period
/// with nothing in it is a quiet dot, or, when the whole row is empty, a free-period band.
class _PeriodCell extends StatelessWidget {
  final Map? entry;
  final bool student, isToday, gap, roomy;
  final String? rowTime;
  const _PeriodCell({required this.entry, required this.student, required this.rowTime, required this.isToday,
      required this.gap, this.roomy = false});

  /// Today's period that is under way now (needs its time).
  bool get _now {
    final e = entry;
    if (e == null || !isToday) return false;
    final t = entryTime(e) ?? rowTime;
    if (t == null) return false;
    final parts = t.split('-');
    final start = clockMinutes(parts.first), end = parts.length > 1 ? clockMinutes(parts.last) : null;
    final n = DateTime.now();
    final minutes = n.hour * 60 + n.minute;
    return start != null && end != null && minutes >= start && minutes < end;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final e = entry;
    if (e == null) {
      return Container(
        constraints: BoxConstraints(minHeight: roomy ? 52 : 60),
        alignment: roomy ? Alignment.centerLeft : Alignment.center,
        padding: roomy ? const EdgeInsets.symmetric(horizontal: 14) : null,
        decoration: gap
            ? BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35))
            : null,
        child: Text(gap || roomy ? tr('Free') : '·',
            style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant.withValues(alpha: gap || roomy ? 0.8 : 0.4))),
      );
    }
    final subject = (e['subjectName'] ?? '') as String;
    final who = ((student ? e['teacherName'] : e['sectionName']) ?? '') as String;
    final own = entryTime(e);
    final accent = subjectColor(subject);
    final dark = theme.brightness == Brightness.dark;
    final now = _now;
    return Container(
      constraints: BoxConstraints(minHeight: roomy ? 52 : 60),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: dark ? 0.20 : 0.10),
        borderRadius: BorderRadius.circular(10),
        border: now ? Border.all(color: accent, width: 1.6) : null,
      ),
      clipBehavior: Clip.antiAlias,
      child: IntrinsicHeight(
        child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Container(width: 4, color: accent),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(9, 7, 8, 7),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(subject,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700)),
                if (who.isNotEmpty)
                  Text(who,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                // A period on a different bell from its row's shows its own time.
                if (own != null && own != rowTime && !roomy)
                  Text(own, style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                if (now)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(tr('Now'),
                        style: theme.textTheme.labelSmall?.copyWith(color: accent, fontWeight: FontWeight.w800)),
                  ),
              ]),
            ),
          ),
        ]),
      ),
    );
  }
}
