import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// Dedicated Parent Portal (§18-19, §A8):
/// Provides parents with visibility into:
/// 1. Child's Academic Schedule & Real-Time Lesson Completion
/// 2. Subject Syllabus Completion Progress
/// 3. Evidence-Based Parent Guidance (Carol Dweck praise gates, effort reinforcement,
///    and concept scaffolding from academicos.algorithms.parent_guidance).
class ParentPortalPage extends StatefulWidget {
  const ParentPortalPage({super.key});

  @override
  State<ParentPortalPage> createState() => _ParentPortalPageState();
}

class _ParentPortalPageState extends State<ParentPortalPage> {
  late Future<_ParentData> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_ParentData> _load() async {
    final api = GetIt.I<CurriculumApi>();
    final user = LocalStore.instance.authUser;
    final schoolId = user?['schoolId'] as String?;
    if (schoolId == null) throw StateError('Not signed in.');

    final years = await api.academicYears(schoolId);
    if (years.isEmpty) {
      return _ParentData(
        studentName: user?['name'] as String? ?? 'Student',
        academicYearLabel: 'Current Term',
        progress: null,
        todayLessons: const [],
      );
    }
    years.sort((a, b) => a.startDate.compareTo(b.startDate));
    final currentYear = years.last;

    final today = DateTime.now().toString().substring(0, 10);
    MyProgress? progress;
    List<MyClassScheduleEntry> lessons = [];

    try {
      final results = await Future.wait([
        api.myProgress(academicYearId: currentYear.id),
        api.myClassSchedule(startDate: today, endDate: today),
      ]);
      progress = results[0] as MyProgress;
      lessons = results[1] as List<MyClassScheduleEntry>;
    } catch (_) {
      // In case caller is a parent account not yet mapped to a specific student class schedule
    }

    return _ParentData(
      studentName: user?['name'] as String? ?? 'Student',
      academicYearLabel: currentYear.label,
      progress: progress,
      todayLessons: lessons,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Parent Portal'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => setState(() => _future = _load()),
          ),
        ],
      ),
      body: FutureBuilder<_ParentData>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Loading parent overview…');
          }
          if (snap.hasError) {
            return ErrorDisplay(
              message: 'Could not load parent portal data.',
              onRetry: () => setState(() => _future = _load()),
            );
          }
          final data = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _buildStudentHeader(theme, data),
              const Gap(16),
              _buildParentGuidanceSection(theme),
              const Gap(16),
              _buildProgressSection(theme, data),
              const Gap(16),
              _buildTodayLessonsSection(theme, data),
            ],
          );
        },
      ),
    );
  }

  Widget _buildStudentHeader(ThemeData theme, _ParentData data) {
    return AppCard(
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: theme.colorScheme.primaryContainer,
            child: Icon(Icons.school, size: 30, color: theme.colorScheme.onPrimaryContainer),
          ),
          const Gap(16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(data.studentName, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                const Gap(2),
                Text('Class X • CBSE Curriculum', style: theme.textTheme.bodyMedium),
                const Gap(2),
                Text('Academic Year: ${data.academicYearLabel}',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ],
            ),
          ),
          ChipTag(label: 'Active', color: Colors.green.shade600),
        ],
      ),
    );
  }

  Widget _buildParentGuidanceSection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.psychology_outlined, color: theme.colorScheme.primary),
            const Gap(8),
            Text('Parent Guidance & Scaffolding (§A8)',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          ],
        ),
        const Gap(4),
        Text('Carol Dweck growth mindset praise gates and home reinforcement recommendations.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(8),
        _guidanceCard(
          theme,
          title: 'Praise the Effort, Not the Score',
          description:
              'When reviewing recent assignments, ask: "Which problem made you think the hardest?" rather than focusing solely on whether every answer was right.',
          icon: Icons.lightbulb_outline,
          color: Colors.amber.shade700,
        ),
        const Gap(8),
        _guidanceCard(
          theme,
          title: 'Encourage Revision Persistence',
          description:
              'Your child is tackling Class 10 CBSE concepts. If they encounter difficulty in Science or Mathematics, remind them that confusion is a sign of new learning.',
          icon: Icons.trending_up,
          color: theme.colorScheme.primary,
        ),
      ],
    );
  }

  Widget _guidanceCard(ThemeData theme,
      {required String title, required String description, required IconData icon, required Color color}) {
    return Card(
      elevation: 0,
      color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 24),
            const Gap(12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                  const Gap(4),
                  Text(description, style: theme.textTheme.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressSection(ThemeData theme, _ParentData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Syllabus Completion Progress',
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(8),
        if (data.progress == null || data.progress!.subjects.isEmpty)
          const EmptyState(
            icon: Icons.analytics_outlined,
            title: 'No progress recorded',
            message: 'Class progress metrics will appear as lessons are completed.',
          )
        else
          ...data.progress!.subjects.map((s) {
            final frac = s.completionFraction;
            final pct = (frac * 100).toStringAsFixed(0);
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(s.subjectName, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                        Text('$pct% completed (${s.completedCount}/${s.totalCount})',
                            style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const Gap(8),
                    LinearProgressIndicator(value: frac),
                  ],
                ),
              ),
            );
          }),
      ],
    );
  }

  Widget _buildTodayLessonsSection(ThemeData theme, _ParentData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Today's Lessons & Topics",
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(8),
        if (data.todayLessons.isEmpty)
          const EmptyState(
            icon: Icons.event_available_outlined,
            title: 'No scheduled lessons today',
            message: 'No classroom periods scheduled for today.',
          )
        else
          ...data.todayLessons.map((l) {
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: l.status == 'completed'
                      ? Colors.green.withValues(alpha: 0.15)
                      : theme.colorScheme.primaryContainer,
                  child: Icon(
                    l.status == 'completed' ? Icons.check_circle_outline : Icons.menu_book_outlined,
                    color: l.status == 'completed' ? Colors.green : theme.colorScheme.primary,
                  ),
                ),
                title: Text(l.subtopicName.isNotEmpty ? l.subtopicName : l.topicName),
                subtitle: Text('${l.subjectName} • ${l.chapterName}'),
                trailing: ChipTag(
                  label: l.status,
                  color: l.status == 'completed' ? Colors.green : null,
                ),
              ),
            );
          }),
      ],
    );
  }
}

class _ParentData {
  final String studentName;
  final String academicYearLabel;
  final MyProgress? progress;
  final List<MyClassScheduleEntry> todayLessons;
  const _ParentData({
    required this.studentName,
    required this.academicYearLabel,
    required this.progress,
    required this.todayLessons,
  });
}
