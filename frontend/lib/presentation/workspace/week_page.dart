import 'package:flutter/material.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

const _dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/// The week (TA-2, SA-1): a teacher's periods across their sections, or a
/// student's section's week, as a grid of days by periods with the bell's
/// times.
class WeekPage extends StatefulWidget {
  const WeekPage({super.key});

  @override
  State<WeekPage> createState() => _WeekPageState();
}

class _WeekPageState extends State<WeekPage> {
  late Future<Map<String, dynamic>> _future = Ops.map('/curriculum/my-timetable');

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final student = CurrentSession.role == 'student';
    return Scaffold(
      appBar: AppBar(title: Text(tr('My week'))),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = Ops.map('/curriculum/my-timetable'); }));
          }
          final d = snap.data!;
          final entries = (d['entries'] as List).cast<Map>();
          if (entries.isEmpty) {
            return EmptyState(icon: Icons.calendar_view_week, title: tr('No timetable yet'),
                message: tr('The school has not published a timetable for you yet.'));
          }
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
            child: SingleChildScrollView(
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
            ),
          );
        },
      ),
    );
  }
}
