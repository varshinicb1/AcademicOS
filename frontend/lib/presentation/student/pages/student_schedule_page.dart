import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

enum _ViewMode { overview, day, week, month }

/// §18: the student portal -- "what's being taught, what's completed,
/// upcoming, progress. A reduced subset, no management controls." per the
/// master build prompt. Everything here is read-only: no mark-complete
/// action (that's `my_schedule_page.dart`'s teacher-only tap-to-mark
/// sheet), no reschedule, no curriculum editing -- this screen cannot
/// write anything.
///
/// Features Day/Week/Month calendar views kept consistent with the overview,
/// allowing students to track daily, weekly, and monthly syllabus coverage
/// alongside their subject progress metrics.
///
/// Placed outside `MainShell`'s drawer navigation on purpose: every one of
/// MainShell's nav destinations (Assessments, Evaluate, Teacher, Principal,
/// ...) is teacher/principal-only and most are principal-gated server-side
/// -- showing that drawer to a student would offer actions that only ever
/// 403.
///
/// Online-only, like every other curriculum/schedule screen this session
/// built -- the offline on-device engine has no local mirror of this data.
class StudentSchedulePage extends StatefulWidget {
  const StudentSchedulePage({super.key});

  @override
  State<StudentSchedulePage> createState() => _StudentSchedulePageState();
}

class _StudentSchedulePageState extends State<StudentSchedulePage> {
  static const _offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

  _ViewMode _viewMode = _ViewMode.overview;
  DateTime _day = DateTime.now();
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay = DateTime.now();

  late Future<_StudentScheduleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  static String _iso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  static DateTime _mondayOnOrBefore(DateTime d) => d.subtract(Duration(days: d.weekday - 1));
  static DateTime _sundayOnOrAfter(DateTime d) => d.add(Duration(days: 7 - d.weekday));

  static const _months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];
  static const _weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  String _formatDate(DateTime d) => '${_weekdays[d.weekday - 1]}, ${_months[d.month - 1]} ${d.day}';
  bool _isToday(DateTime d) => _sameDay(d, DateTime.now());
  bool _sameDay(DateTime a, DateTime b) => a.year == b.year && a.month == b.month && a.day == b.day;

  (DateTime, DateTime) _currentRange() {
    switch (_viewMode) {
      case _ViewMode.overview:
        final now = DateTime.now();
        return (now.subtract(const Duration(days: 14)), now.add(const Duration(days: 14)));
      case _ViewMode.day:
        return (_day, _day);
      case _ViewMode.week:
        return (_mondayOnOrBefore(_focusedDay), _sundayOnOrAfter(_focusedDay));
      case _ViewMode.month:
        final firstOfMonth = DateTime(_focusedDay.year, _focusedDay.month, 1);
        final lastOfMonth = DateTime(_focusedDay.year, _focusedDay.month + 1, 0);
        return (_mondayOnOrBefore(firstOfMonth), _sundayOnOrAfter(lastOfMonth));
    }
  }

  Future<_StudentScheduleData> _load() async {
    final api = GetIt.I<CurriculumApi>();
    final schoolId = LocalStore.instance.authUser?['schoolId'] as String?;
    if (schoolId == null) {
      throw StateError('Not signed in.');
    }
    final years = await api.academicYears(schoolId);
    if (years.isEmpty) {
      return const _StudentScheduleData(progress: null, lessons: []);
    }
    years.sort((a, b) => a.startDate.compareTo(b.startDate));
    final currentYear = years.last;

    final (start, end) = _currentRange();

    final results = await Future.wait([
      api.myProgress(academicYearId: currentYear.id),
      api.myClassSchedule(startDate: _iso(start), endDate: _iso(end)),
    ]);
    return _StudentScheduleData(
      progress: results[0] as MyProgress,
      lessons: results[1] as List<MyClassScheduleEntry>,
    );
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

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('My Class')),
      body: _offlineMode
          ? const EmptyState(
              icon: Icons.cloud_off,
              title: 'Needs a connection',
              message: 'Your class schedule lives on the school\'s server and isn\'t '
                  'available in this offline app yet.',
            )
          : Column(
              children: [
                _viewModeSelector(theme),
                const Divider(height: 1),
                Expanded(
                  child: FutureBuilder<_StudentScheduleData>(
                    future: _future,
                    builder: (context, snap) {
                      if (snap.connectionState != ConnectionState.done) {
                        return const LoadingIndicator(message: 'Loading your class…');
                      }
                      if (snap.hasError) {
                        final err = snap.error;
                        final notEnrolled = err is DioException && err.response?.statusCode == 404;
                        return EmptyState(
                          icon: Icons.school_outlined,
                          title: notEnrolled ? 'Not enrolled yet' : 'Could not load',
                          message: notEnrolled
                              ? 'Your school hasn\'t enrolled you in a class yet -- ask your '
                                'principal to add you.'
                              : 'Check your connection and try again.',
                        );
                      }
                      final data = snap.data!;
                      return RefreshIndicator(
                        onRefresh: () async => setState(() => _future = _load()),
                        child: _buildBody(theme, data),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Widget _viewModeSelector(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: SegmentedButton<_ViewMode>(
        segments: const [
          ButtonSegment(value: _ViewMode.overview, label: Text('Overview')),
          ButtonSegment(value: _ViewMode.day, label: Text('Day')),
          ButtonSegment(value: _ViewMode.week, label: Text('Week')),
          ButtonSegment(value: _ViewMode.month, label: Text('Month')),
        ],
        selected: {_viewMode},
        onSelectionChanged: (sel) => _setViewMode(sel.first),
      ),
    );
  }

  Widget _buildBody(ThemeData theme, _StudentScheduleData data) {
    switch (_viewMode) {
      case _ViewMode.overview:
        return _overviewBody(theme, data);
      case _ViewMode.day:
        return _dayBody(theme, data.lessons);
      case _ViewMode.week:
      case _ViewMode.month:
        return _calendarBody(theme, data.lessons);
    }
  }

  // -------------------- Overview --------------------

  Widget _overviewBody(ThemeData theme, _StudentScheduleData data) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (data.progress != null && data.progress!.subjects.isNotEmpty) ...[
          Text('Progress', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(8),
          ...data.progress!.subjects.map((s) => _progressCard(theme, s)),
          const Gap(12),
        ],
        Text('Recent & Upcoming Lessons',
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(8),
        if (data.lessons.isEmpty)
          const EmptyState(
            icon: Icons.event_available_outlined,
            title: 'Nothing here',
            message: 'No lessons in the last two weeks or the next two.',
          )
        else
          ...data.lessons.map((l) => _lessonCard(theme, l)),
      ],
    );
  }

  // -------------------- Day --------------------

  Widget _dayBody(ThemeData theme, List<MyClassScheduleEntry> lessons) {
    final dayLessons = lessons.where((l) => _sameDay(DateTime.parse(l.date), _day)).toList();
    return Column(
      children: [
        _dayNav(theme),
        const Divider(height: 1),
        Expanded(
          child: dayLessons.isEmpty
              ? EmptyState(
                  icon: Icons.event_available_outlined,
                  title: 'No lessons scheduled',
                  message: _isToday(_day)
                      ? 'No lessons scheduled for your class today.'
                      : 'Nothing scheduled on ${_formatDate(_day)}.',
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: dayLessons.length,
                  itemBuilder: (context, i) => _lessonCard(theme, dayLessons[i]),
                ),
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

  Widget _calendarBody(ThemeData theme, List<MyClassScheduleEntry> lessons) {
    final selected = _selectedDay ?? _focusedDay;
    final dayLessons = lessons.where((l) => _sameDay(DateTime.parse(l.date), selected)).toList();
    return Column(
      children: [
        Card(
          margin: const EdgeInsets.all(12),
          child: TableCalendar<MyClassScheduleEntry>(
            firstDay: DateTime.now().subtract(const Duration(days: 365)),
            lastDay: DateTime.now().add(const Duration(days: 365)),
            focusedDay: _focusedDay,
            calendarFormat: _viewMode == _ViewMode.week ? CalendarFormat.week : CalendarFormat.month,
            availableCalendarFormats: {
              (_viewMode == _ViewMode.week ? CalendarFormat.week : CalendarFormat.month): '',
            },
            headerStyle: const HeaderStyle(formatButtonVisible: false),
            selectedDayPredicate: (d) => _sameDay(d, selected),
            eventLoader: (day) =>
                lessons.where((l) => _sameDay(DateTime.parse(l.date), day)).toList(),
            onDaySelected: (sel, foc) => setState(() {
              _selectedDay = sel;
              _focusedDay = foc;
            }),
            onPageChanged: (foc) => setState(() {
              _focusedDay = foc;
              _future = _load();
            }),
            calendarStyle: CalendarStyle(
              markerDecoration:
                  BoxDecoration(color: theme.colorScheme.primary, shape: BoxShape.circle),
            ),
          ),
        ),
        Expanded(
          child: dayLessons.isEmpty
              ? EmptyState(
                  icon: Icons.event_available_outlined,
                  title: 'No lessons',
                  message: 'Nothing scheduled on ${_formatDate(selected)}.',
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: dayLessons.length,
                  itemBuilder: (context, i) => _lessonCard(theme, dayLessons[i]),
                ),
        ),
      ],
    );
  }

  Widget _progressCard(ThemeData theme, SubjectProgress s) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(s.subjectName, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              Text('${s.completedCount} / ${s.totalCount} taught',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ],
          ),
          const Gap(8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: s.completionFraction,
              minHeight: 6,
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
              valueColor: AlwaysStoppedAnimation(theme.colorScheme.primary),
            ),
          ),
        ],
      ),
    );
  }

  Widget _lessonCard(ThemeData theme, MyClassScheduleEntry lesson) {
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, shape: BoxShape.circle),
            child: Icon(_statusIcon(lesson.status), color: theme.colorScheme.onPrimaryContainer, size: 20),
          ),
          const Gap(12),
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
                const Gap(2),
                Text(lesson.date, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
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
        return null;
    }
  }
}

class _StudentScheduleData {
  final MyProgress? progress;
  final List<MyClassScheduleEntry> lessons;
  const _StudentScheduleData({required this.progress, required this.lessons});
}
