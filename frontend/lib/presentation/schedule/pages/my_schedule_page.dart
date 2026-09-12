import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// "What do I teach today" -- §15 of the master build prompt, the first
/// teacher-facing screen for the new curriculum/calendar/scheduling work
/// this backend now does for real (src/academicos/curriculum/scheduling.py).
///
/// Online-only for now: the offline on-device engine
/// (core/local_engine/) has no local mirror of curriculum/schedule data at
/// all -- there is no Topic/Subtopic/ScheduledLesson concept in Hive, only
/// in the real server's SQLite store. Every other online-only screen in
/// this app degrades to a local equivalent; this one has none yet, so it
/// honestly says so rather than pretending to work offline. A real
/// day-by-day navigator: the default view is today, with simple
/// forward/back arrows to check other days (e.g. tomorrow's prep, or
/// yesterday's coverage) -- no calendar picker yet, since a teacher's real
/// question is almost always "today" or "the next couple of days".
class MySchedulePage extends StatefulWidget {
  const MySchedulePage({super.key});

  @override
  State<MySchedulePage> createState() => _MySchedulePageState();
}

class _MySchedulePageState extends State<MySchedulePage> {
  DateTime _date = DateTime.now();
  late Future<List<MyScheduleEntry>> _future;

  static const _offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  String get _isoDate =>
      '${_date.year.toString().padLeft(4, '0')}-${_date.month.toString().padLeft(2, '0')}-${_date.day.toString().padLeft(2, '0')}';

  Future<List<MyScheduleEntry>> _load() {
    return GetIt.I<CurriculumApi>().mySchedule(startDate: _isoDate, endDate: _isoDate);
  }

  void _shiftDay(int delta) {
    setState(() {
      _date = _date.add(Duration(days: delta));
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('My Schedule')),
      body: _offlineMode
          ? const EmptyState(
              icon: Icons.cloud_off,
              title: 'Needs a connection',
              message: 'Your teaching schedule lives on the school\'s server and isn\'t '
                  'available in this offline app yet.',
            )
          : Column(
              children: [
                _dayNav(theme),
                const Divider(height: 1),
                Expanded(
                  child: FutureBuilder<List<MyScheduleEntry>>(
                    future: _future,
                    builder: (context, snap) {
                      if (snap.connectionState != ConnectionState.done) {
                        return const LoadingIndicator(message: 'Loading your schedule…');
                      }
                      if (snap.hasError) {
                        return ErrorDisplay(
                          message: 'Could not load your schedule. Check your connection.',
                          onRetry: () => setState(() => _future = _load()),
                        );
                      }
                      final lessons = snap.data ?? const [];
                      if (lessons.isEmpty) {
                        return EmptyState(
                          icon: Icons.event_available_outlined,
                          title: 'No lessons scheduled',
                          message: _isToday(_date)
                              ? 'Nothing scheduled for you today -- either a free '
                                'period, or your subjects haven\'t been scheduled yet.'
                              : 'Nothing scheduled for you on this day.',
                        );
                      }
                      return RefreshIndicator(
                        onRefresh: () async => setState(() => _future = _load()),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: lessons.length,
                          itemBuilder: (context, i) => _lessonCard(theme, lessons[i]),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Widget _dayNav(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Row(
        children: [
          IconButton(icon: const Icon(Icons.chevron_left), onPressed: () => _shiftDay(-1)),
          Expanded(
            child: Center(
              child: Text(
                _isToday(_date) ? 'Today, ${_formatDate(_date)}' : _formatDate(_date),
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
              ),
            ),
          ),
          IconButton(icon: const Icon(Icons.chevron_right), onPressed: () => _shiftDay(1)),
        ],
      ),
    );
  }

  Widget _lessonCard(ThemeData theme, MyScheduleEntry lesson) {
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, shape: BoxShape.circle),
            child: Icon(Icons.menu_book_outlined, color: theme.colorScheme.onPrimaryContainer, size: 22),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lesson.subtopicName,
                    style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(2),
                Text(
                  [lesson.subjectName, lesson.chapterName, lesson.topicName]
                      .where((s) => s.isNotEmpty)
                      .join(' · '),
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          ChipTag(label: lesson.status),
        ],
      ),
    );
  }

  static bool _isToday(DateTime d) {
    final now = DateTime.now();
    return d.year == now.year && d.month == now.month && d.day == now.day;
  }

  static String _formatDate(DateTime d) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    return '${days[d.weekday - 1]}, ${months[d.month - 1]} ${d.day}';
  }
}
