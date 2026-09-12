import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// §18: the student portal -- "what's being taught, what's completed,
/// upcoming, progress. A reduced subset, no management controls." per the
/// master build prompt. Everything here is read-only: no mark-complete
/// action (that's `my_schedule_page.dart`'s teacher-only tap-to-mark
/// sheet), no reschedule, no curriculum editing -- this screen cannot
/// write anything.
///
/// A first, deliberately simple cut: a real per-subject progress summary
/// up top (from `GET /my-progress`) and a real, dated list of this class's
/// lessons for a 4-week window (2 weeks back, 2 weeks ahead -- "upcoming"
/// and recently "completed" both fit in that, matching the transcript's
/// own phrasing) below it, from `GET /my-class-schedule`. Not the same
/// Day/Week/Month/Year granularity `my_schedule_page.dart` has -- that's
/// a real, smaller follow-up once this simpler view is confirmed useful;
/// building the full four-view calendar twice (once per audience) before
/// either has real users would be premature.
///
/// Placed outside `MainShell`'s drawer navigation on purpose: every one of
/// MainShell's nav destinations (Assessments, Evaluate, Teacher, Principal,
/// ...) is teacher/principal-only and most are principal-gated server-side
/// -- showing that drawer to a student would offer actions that only ever
/// 403. A dedicated student navigation shell is real, separate, future
/// work (same class of gap as the still-missing admin-web surface noted
/// elsewhere in this app).
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

  late Future<_StudentScheduleData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  static String _iso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

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
    // The most recently-started academic year is "current" -- schools
    // don't run two at once, and this avoids guessing at a "status=active"
    // convention the backend doesn't actually enforce.
    years.sort((a, b) => a.startDate.compareTo(b.startDate));
    final currentYear = years.last;

    final now = DateTime.now();
    final start = now.subtract(const Duration(days: 14));
    final end = now.add(const Duration(days: 14));

    final results = await Future.wait([
      api.myProgress(academicYearId: currentYear.id),
      api.myClassSchedule(startDate: _iso(start), endDate: _iso(end)),
    ]);
    return _StudentScheduleData(
      progress: results[0] as MyProgress,
      lessons: results[1] as List<MyClassScheduleEntry>,
    );
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
          : FutureBuilder<_StudentScheduleData>(
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
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (data.progress != null && data.progress!.subjects.isNotEmpty) ...[
                        Text('Progress', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                        const Gap(8),
                        ...data.progress!.subjects.map((s) => _progressCard(theme, s)),
                        const Gap(12),
                      ],
                      Text('Lessons', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
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
                  ),
                );
              },
            ),
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
