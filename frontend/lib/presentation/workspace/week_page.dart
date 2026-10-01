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
          padding: const EdgeInsets.only(bottom: 24),
          children: [
            SectionHeader(title: tr('Coming up')),
            FutureBuilder<List<Map<String, dynamic>>>(
              future: _coming,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
                if (snap.hasError) return _Notice(serverErrorMessage(snap.error!));
                final items = snap.data!;
                if (items.isEmpty) return _Notice(tr('Nothing in the next six weeks'));
                return Column(children: [for (final i in items) _ComingTile(i)]);
              },
            ),
            if (_load != null) ...[
              SectionHeader(title: tr('My load')),
              FutureBuilder<Map<String, dynamic>>(
                future: _load,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
                  if (snap.hasError) return _Notice(serverErrorMessage(snap.error!));
                  return _LoadCard(snap.data!);
                },
              ),
            ],
            SectionHeader(title: tr('Timetable')),
            FutureBuilder<Map<String, dynamic>>(
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
                return _Grid(d, student: _student);
              },
            ),
          ],
        ),
      ),
    );
  }
}

/// "Mon 8 Jun", or Today/Tomorrow, then the times or the last day.
String calendarWhen(Map item, DateTime today) {
  final d = DateTime.parse(item['date'] as String);
  final day = DateTime(today.year, today.month, today.day);
  final gap = DateTime(d.year, d.month, d.day).difference(day).inDays;
  String label(DateTime x) => '${tr(_dayNames[x.weekday - 1])} ${x.day} ${_months[x.month - 1]}';
  final when = gap == 0 ? tr('Today') : gap == 1 ? tr('Tomorrow') : label(d);
  final end = item['endDate'] as String?;
  if (end != null && end != item['date']) return '$when – ${label(DateTime.parse(end))}';
  final start = item['startTime'] as String?;
  if (start != null) return '$when · $start–${item['endTime'] ?? ''}';
  return when;
}

class _ComingTile extends StatelessWidget {
  final Map<String, dynamic> item;
  const _ComingTile(this.item);

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      leading: Icon(calendarKindIcons[item['kind']] ?? Icons.event_outlined),
      title: Text(item['title'] as String? ?? ''),
      subtitle: Text(calendarWhen(item, DateTime.now())),
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
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${load['periodsPerWeek'] ?? 0} ${tr('periods a week')}', style: theme.textTheme.titleMedium),
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
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Text(text, style: Theme.of(context).textTheme.bodyMedium),
      );
}

class _Grid extends StatelessWidget {
  final Map<String, dynamic> d;
  final bool student;
  const _Grid(this.d, {required this.student});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final entries = (d['entries'] as List).cast<Map>();
    final bell = d['bellSchedule'] as Map?;
    final times = <int, String>{
      for (final s in ((bell?['slots'] as List?) ?? const []).cast<Map>())
        if (s['period'] != null) s['period'] as int: '${s['start']}-${s['end']}',
    };
    final days = ((bell?['days'] as List?)?.cast<int>() ?? [0, 1, 2, 3, 4, 5]).toList()..sort();
    final periods = {for (final e in entries) e['period'] as int, ...times.keys}.toList()..sort();
    final cell = <(int, int), Map>{for (final e in entries) (e['dayOfWeek'] as int, e['period'] as int): e};
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.all(12),
      child: DataTable(
        columnSpacing: 14,
        dataRowMinHeight: 52,
        dataRowMaxHeight: 64,
        columns: [
          const DataColumn(label: Text('')),
          for (final day in days) DataColumn(label: Text(tr(_dayNames[day]))),
        ],
        rows: [
          for (final p in periods)
            DataRow(cells: [
              DataCell(Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('P$p', style: theme.textTheme.labelLarge),
                if (times[p] != null) Text(times[p]!, style: theme.textTheme.bodySmall),
              ])),
              for (final day in days)
                DataCell(cell[(day, p)] == null
                    ? const Text('')
                    : Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(cell[(day, p)]!['subjectName'] ?? '', style: theme.textTheme.bodyMedium),
                        Text((student ? cell[(day, p)]!['teacherName'] : cell[(day, p)]!['sectionName']) ?? '',
                            style: theme.textTheme.bodySmall),
                      ])),
            ]),
        ],
      ),
    );
  }
}
