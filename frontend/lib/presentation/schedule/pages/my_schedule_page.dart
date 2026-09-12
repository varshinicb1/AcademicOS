import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

enum _ViewMode { day, week, month, year }

/// "What do I teach today" -- §11-15 of the master build prompt, the
/// teacher-facing screen for the new curriculum/calendar/scheduling work
/// this backend now does for real (src/academicos/curriculum/scheduling.py).
/// Four kept-consistent granularities (Day/Week/Month/Year) over the same
/// real, dated `GET /my-schedule` data -- never a separate view-specific
/// data source that could drift from the others. Also where §15's
/// completion tracking lives: tapping a lesson opens a deliberately
/// trivial YES/NO + optional note sheet -- no curriculum re-selection,
/// per the transcript's own instruction.
///
/// Reuses `table_calendar` (already a dependency, already used by the
/// real exam-date Planner in daily_planner_page.dart) for Week/Month
/// rather than hand-rolling a calendar grid -- same package, a different,
/// separate `TableCalendar` instance, no shared state with the exam
/// planner (deliberately: that's a different feature, see this class's
/// own module-level note in the requirements matrix).
///
/// Online-only for now: the offline on-device engine
/// (core/local_engine/) has no local mirror of curriculum/schedule data at
/// all -- there is no Topic/Subtopic/ScheduledLesson concept in Hive, only
/// in the real server's SQLite store. Every other online-only screen in
/// this app degrades to a local equivalent; this one has none yet, so it
/// honestly says so rather than pretending to work offline.
class MySchedulePage extends StatefulWidget {
  const MySchedulePage({super.key});

  @override
  State<MySchedulePage> createState() => _MySchedulePageState();
}

class _MySchedulePageState extends State<MySchedulePage> {
  _ViewMode _viewMode = _ViewMode.day;

  DateTime _day = DateTime.now();          // Day view's anchor date
  DateTime _focusedDay = DateTime.now();   // Week/Month calendar's focused page
  DateTime? _selectedDay = DateTime.now(); // Which day's lessons show below the Week/Month grid
  int _yearFocus = DateTime.now().year;    // Year view's focused year

  late Future<List<MyScheduleEntry>> _future;

  static const _offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  static String _iso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  static DateTime _mondayOnOrBefore(DateTime d) => d.subtract(Duration(days: d.weekday - 1));
  static DateTime _sundayOnOrAfter(DateTime d) => d.add(Duration(days: 7 - d.weekday));

  (DateTime, DateTime) _currentRange() {
    switch (_viewMode) {
      case _ViewMode.day:
        return (_day, _day);
      case _ViewMode.week:
        return (_mondayOnOrBefore(_focusedDay), _sundayOnOrAfter(_focusedDay));
      case _ViewMode.month:
        final firstOfMonth = DateTime(_focusedDay.year, _focusedDay.month, 1);
        final lastOfMonth = DateTime(_focusedDay.year, _focusedDay.month + 1, 0);
        // Padded to full weeks -- table_calendar's month grid shows a few
        // leading/trailing days from adjacent months, and they should
        // carry real event markers too, not appear falsely empty.
        return (_mondayOnOrBefore(firstOfMonth), _sundayOnOrAfter(lastOfMonth));
      case _ViewMode.year:
        return (DateTime(_yearFocus, 1, 1), DateTime(_yearFocus, 12, 31));
    }
  }

  Future<List<MyScheduleEntry>> _load() {
    final (start, end) = _currentRange();
    return GetIt.I<CurriculumApi>().mySchedule(startDate: _iso(start), endDate: _iso(end));
  }

  void _setViewMode(_ViewMode mode) {
    setState(() {
      _viewMode = mode;
      _future = _load();
    });
  }

  void _shiftDay(int delta) {
    setState(() {
      _day = _day.add(Duration(days: delta));
      _future = _load();
    });
  }

  bool _sameDay(DateTime a, DateTime b) => a.year == b.year && a.month == b.month && a.day == b.day;

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
                _viewModeSelector(theme),
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
                      switch (_viewMode) {
                        case _ViewMode.day:
                          return _dayBody(theme, lessons);
                        case _ViewMode.week:
                        case _ViewMode.month:
                          return _calendarBody(theme, lessons);
                        case _ViewMode.year:
                          return _yearBody(theme, lessons);
                      }
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Widget _viewModeSelector(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: SegmentedButton<_ViewMode>(
        segments: const [
          ButtonSegment(value: _ViewMode.day, label: Text('Day')),
          ButtonSegment(value: _ViewMode.week, label: Text('Week')),
          ButtonSegment(value: _ViewMode.month, label: Text('Month')),
          ButtonSegment(value: _ViewMode.year, label: Text('Year')),
        ],
        selected: {_viewMode},
        onSelectionChanged: (sel) => _setViewMode(sel.first),
      ),
    );
  }

  // -------------------- Day --------------------

  Widget _dayBody(ThemeData theme, List<MyScheduleEntry> lessons) {
    return Column(
      children: [
        _dayNav(theme),
        const Divider(height: 1),
        Expanded(
          child: lessons.isEmpty
              ? EmptyState(
                  icon: Icons.event_available_outlined,
                  title: 'No lessons scheduled',
                  message: _isToday(_day)
                      ? 'Nothing scheduled for you today -- either a free '
                        'period, or your subjects haven\'t been scheduled yet.'
                      : 'Nothing scheduled for you on this day.',
                )
              : _lessonList(lessons),
        ),
      ],
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
                _isToday(_day) ? 'Today, ${_formatDate(_day)}' : _formatDate(_day),
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
              ),
            ),
          ),
          IconButton(icon: const Icon(Icons.chevron_right), onPressed: () => _shiftDay(1)),
        ],
      ),
    );
  }

  // -------------------- Week / Month --------------------

  Widget _calendarBody(ThemeData theme, List<MyScheduleEntry> lessons) {
    final selected = _selectedDay ?? _focusedDay;
    final dayLessons = lessons.where((l) => _sameDay(DateTime.parse(l.date), selected)).toList();
    return Column(
      children: [
        Card(
          margin: const EdgeInsets.all(12),
          child: TableCalendar<MyScheduleEntry>(
            firstDay: DateTime.now().subtract(const Duration(days: 365)),
            lastDay: DateTime.now().add(const Duration(days: 365)),
            focusedDay: _focusedDay,
            calendarFormat: _viewMode == _ViewMode.week ? CalendarFormat.week : CalendarFormat.month,
            availableCalendarFormats: {
              (_viewMode == _ViewMode.week ? CalendarFormat.week : CalendarFormat.month): '',
            },
            headerStyle: const HeaderStyle(formatButtonVisible: false),
            selectedDayPredicate: (d) => _sameDay(d, selected),
            eventLoader: (day) => lessons.where((l) => _sameDay(DateTime.parse(l.date), day)).toList(),
            onDaySelected: (sel, foc) => setState(() {
              _selectedDay = sel;
              _focusedDay = foc;
            }),
            onPageChanged: (foc) => setState(() {
              _focusedDay = foc;
              _future = _load();
            }),
            calendarStyle: CalendarStyle(
              markerDecoration: BoxDecoration(color: theme.colorScheme.primary, shape: BoxShape.circle),
            ),
          ),
        ),
        Expanded(
          child: dayLessons.isEmpty
              ? EmptyState(
                  icon: Icons.event_available_outlined,
                  title: 'No lessons',
                  message: 'Nothing scheduled for you on ${_formatDate(selected)}.',
                )
              : _lessonList(dayLessons),
        ),
      ],
    );
  }

  // -------------------- Year --------------------

  Widget _yearBody(ThemeData theme, List<MyScheduleEntry> lessons) {
    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    final countsByMonth = List<int>.filled(12, 0);
    for (final l in lessons) {
      final d = DateTime.parse(l.date);
      if (d.year == _yearFocus) countsByMonth[d.month - 1]++;
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.chevron_left),
                onPressed: () => setState(() {
                  _yearFocus--;
                  _future = _load();
                }),
              ),
              Expanded(
                child: Center(
                  child: Text('$_yearFocus', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.chevron_right),
                onPressed: () => setState(() {
                  _yearFocus++;
                  _future = _load();
                }),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2, mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 1.6,
            ),
            itemCount: 12,
            itemBuilder: (context, i) {
              final count = countsByMonth[i];
              return AppCard(
                margin: EdgeInsets.zero,
                onTap: () => setState(() {
                  _viewMode = _ViewMode.month;
                  _focusedDay = DateTime(_yearFocus, i + 1, 1);
                  _selectedDay = _focusedDay;
                  _future = _load();
                }),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(monthNames[i], style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                    const Gap(4),
                    Text(
                      count == 0 ? 'No lessons' : '$count lesson${count == 1 ? '' : 's'}',
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  // -------------------- Shared lesson list/card/mark sheet --------------------

  Widget _lessonList(List<MyScheduleEntry> lessons) {
    return RefreshIndicator(
      onRefresh: () async => setState(() => _future = _load()),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: lessons.length,
        itemBuilder: (context, i) => _lessonCard(context, Theme.of(context), lessons[i]),
      ),
    );
  }

  Widget _lessonCard(BuildContext context, ThemeData theme, MyScheduleEntry lesson) {
    return AppCard(
      onTap: () => _openMarkSheet(context, lesson),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, shape: BoxShape.circle),
            child: Icon(_statusIcon(lesson.status), color: theme.colorScheme.onPrimaryContainer, size: 22),
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
                if (lesson.note != null && lesson.note!.isNotEmpty) ...[
                  const Gap(6),
                  Text('"${lesson.note}"',
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant, fontStyle: FontStyle.italic)),
                ],
              ],
            ),
          ),
          ChipTag(label: lesson.status, color: _statusColor(theme, lesson.status)),
        ],
      ),
    );
  }

  IconData _statusIcon(String status) {
    switch (status) {
      case 'completed':
        return Icons.check_circle_outline;
      case 'skipped':
        return Icons.remove_circle_outline;
      default:
        return Icons.menu_book_outlined;
    }
  }

  Color? _statusColor(ThemeData theme, String status) {
    switch (status) {
      case 'completed':
        return Colors.green.shade600;
      case 'skipped':
        return theme.colorScheme.error;
      default:
        return null; // ChipTag's own default (primaryContainer)
    }
  }

  /// The §15 deliverable itself: YES/NO + optional note, nothing else --
  /// no re-picking the subtopic, no editing the schedule. Reloads the
  /// current view on success so the card reflects the real, persisted mark
  /// rather than an optimistic local guess.
  Future<void> _openMarkSheet(BuildContext context, MyScheduleEntry lesson) async {
    final noteController = TextEditingController(text: lesson.note ?? '');
    var saving = false;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
            Future<void> mark(String status) async {
              setSheetState(() => saving = true);
              try {
                final note = noteController.text.trim();
                await GetIt.I<CurriculumApi>()
                    .markLesson(lesson.lessonId, status: status, note: note.isEmpty ? null : note);
                if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                if (mounted) setState(() => _future = _load());
              } catch (_) {
                setSheetState(() => saving = false);
                if (sheetContext.mounted) {
                  ScaffoldMessenger.of(sheetContext).showSnackBar(
                    const SnackBar(content: Text('Could not save -- check your connection and try again.')),
                  );
                }
              }
            }

            final theme = Theme.of(sheetContext);
            return Padding(
              padding: EdgeInsets.only(
                left: 20, right: 20, top: 20,
                bottom: 20 + MediaQuery.of(sheetContext).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(lesson.subtopicName, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                  const Gap(4),
                  Text('Did you teach this?', style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  const Gap(16),
                  TextField(
                    controller: noteController,
                    decoration: const InputDecoration(
                      labelText: 'Note (optional)',
                      border: OutlineInputBorder(),
                    ),
                    maxLines: 2,
                    enabled: !saving,
                  ),
                  const Gap(16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: saving ? null : () => mark('skipped'),
                          icon: const Icon(Icons.close),
                          label: const Text('No'),
                        ),
                      ),
                      const Gap(12),
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: saving ? null : () => mark('completed'),
                          icon: saving
                              ? const SizedBox(width: 16, height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Icon(Icons.check),
                          label: const Text('Yes'),
                        ),
                      ),
                    ],
                  ),
                  if (lesson.status != 'scheduled') ...[
                    const Gap(8),
                    Center(
                      child: TextButton(
                        onPressed: saving ? null : () => mark('scheduled'),
                        child: const Text('Undo mark'),
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        );
      },
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
