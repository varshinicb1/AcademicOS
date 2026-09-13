import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// School Admin console (§2, §11-14, §17, §32):
/// 1. Roster: Assign teachers to books and enroll students into grades.
/// 2. Coverage & Pace: Planned vs. actually-taught lessons, coverage %,
///    pace %, period variance, and overdue delayed topics for school management.
/// 3. Reschedule: Disruption handling via PUSH (shifting subsequent lessons
///    forward past a closure) and ADJUST (rescheduling a single lesson to a new date).
class PrincipalAdminPage extends StatefulWidget {
  const PrincipalAdminPage({super.key});

  @override
  State<PrincipalAdminPage> createState() => _PrincipalAdminPageState();
}

class _PrincipalAdminPageState extends State<PrincipalAdminPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late Future<_AdminData> _future;

  String? _academicYearId;

  // --- Roster Form State ---
  String? _assignTeacherId;
  String? _assignGradeId;
  String? _assignSubjectId;
  bool _assigningTeacher = false;

  String? _enrollStudentId;
  String? _enrollGradeId;
  bool _enrollingStudent = false;

  List<SubjectSummary> _subjectsForAssignGrade = [];
  bool _loadingSubjects = false;

  // --- Coverage Reporting State ---
  CoverageReport? _coverageReport;
  DelayedTopicsReport? _delayedTopicsReport;
  bool _loadingReporting = false;
  String? _reportingError;

  // --- Reschedule Form State ---
  String? _pushGradeId;
  String? _pushSubjectId;
  List<SubjectSummary> _pushSubjects = [];
  bool _loadingPushSubjects = false;
  final _pushDateController = TextEditingController(
    text: DateTime.now().toString().substring(0, 10),
  );
  final _pushReasonController = TextEditingController(text: 'Unexpected school closure');
  bool _pushing = false;

  final _adjustLessonIdController = TextEditingController();
  final _adjustDateController = TextEditingController(
    text: DateTime.now().add(const Duration(days: 1)).toString().substring(0, 10),
  );
  final _adjustReasonController = TextEditingController(text: 'Rescheduled to working day');
  bool _adjusting = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() {
      if (_tabController.index == 1 && _coverageReport == null && !_loadingReporting) {
        _loadReporting();
      }
    });
    _future = _load();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _pushDateController.dispose();
    _pushReasonController.dispose();
    _adjustLessonIdController.dispose();
    _adjustDateController.dispose();
    _adjustReasonController.dispose();
    super.dispose();
  }

  Future<_AdminData> _load() async {
    final curriculumApi = GetIt.I<CurriculumApi>();
    final authApi = GetIt.I<AuthApi>();
    final schoolId = LocalStore.instance.authUser?['schoolId'] as String?;
    if (schoolId == null) throw StateError('Not signed in.');

    final results = await Future.wait([
      curriculumApi.academicYears(schoolId),
      authApi.usersForSchool(role: 'teacher'),
      authApi.usersForSchool(role: 'student'),
    ]);
    final years = results[0] as List<AcademicYearSummary>;
    final teachers = results[1] as List<AuthUser>;
    final students = results[2] as List<AuthUser>;

    if (years.isEmpty) {
      return _AdminData(academicYearId: null, grades: const [], teachers: teachers, students: students);
    }
    years.sort((a, b) => a.startDate.compareTo(b.startDate));
    final currentYear = years.last;
    _academicYearId = currentYear.id;

    final grades = await curriculumApi.grades(currentYear.id);
    return _AdminData(academicYearId: currentYear.id, grades: grades, teachers: teachers, students: students);
  }

  Future<void> _loadReporting() async {
    if (_academicYearId == null) return;
    setState(() {
      _loadingReporting = true;
      _reportingError = null;
    });
    try {
      final curriculumApi = GetIt.I<CurriculumApi>();
      final results = await Future.wait([
        curriculumApi.coverageReport(academicYearId: _academicYearId!),
        curriculumApi.delayedTopics(academicYearId: _academicYearId!),
      ]);
      if (!mounted) return;
      setState(() {
        _coverageReport = results[0] as CoverageReport;
        _delayedTopicsReport = results[1] as DelayedTopicsReport;
        _loadingReporting = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _reportingError = '$e';
        _loadingReporting = false;
      });
    }
  }

  Future<void> _loadSubjectsForGrade(String gradeId) async {
    setState(() {
      _loadingSubjects = true;
      _subjectsForAssignGrade = [];
      _assignSubjectId = null;
    });
    try {
      final subjects = await GetIt.I<CurriculumApi>().subjects(gradeId);
      if (!mounted) return;
      setState(() {
        _subjectsForAssignGrade = subjects;
        _loadingSubjects = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loadingSubjects = false);
    }
  }

  Future<void> _loadPushSubjects(String gradeId) async {
    setState(() {
      _loadingPushSubjects = true;
      _pushSubjects = [];
      _pushSubjectId = null;
    });
    try {
      final subjects = await GetIt.I<CurriculumApi>().subjects(gradeId);
      if (!mounted) return;
      setState(() {
        _pushSubjects = subjects;
        _loadingPushSubjects = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loadingPushSubjects = false);
    }
  }

  Future<void> _submitAssignTeacher() async {
    if (_assignTeacherId == null || _assignSubjectId == null) return;
    setState(() => _assigningTeacher = true);
    try {
      final books = await GetIt.I<CurriculumApi>().books(_assignSubjectId!);
      if (books.isEmpty) {
        _showMessage('That subject has no book yet -- seed the curriculum first.');
        return;
      }
      await GetIt.I<CurriculumApi>().assignTeacher(teacherId: _assignTeacherId!, bookId: books.first.id);
      _showMessage('Teacher assigned successfully.');
      setState(() {
        _assignTeacherId = null;
        _assignSubjectId = null;
      });
    } catch (e) {
      _showMessage('Could not assign teacher: $e');
    } finally {
      if (mounted) setState(() => _assigningTeacher = false);
    }
  }

  Future<void> _submitEnrollStudent() async {
    if (_enrollStudentId == null || _enrollGradeId == null) return;
    setState(() => _enrollingStudent = true);
    try {
      await GetIt.I<CurriculumApi>().enrollStudent(studentId: _enrollStudentId!, gradeId: _enrollGradeId!);
      _showMessage('Student enrolled successfully.');
      setState(() {
        _enrollStudentId = null;
        _enrollGradeId = null;
      });
    } catch (e) {
      _showMessage('Could not enroll student: $e');
    } finally {
      if (mounted) setState(() => _enrollingStudent = false);
    }
  }

  Future<void> _submitPushSchedule() async {
    if (_pushSubjectId == null || _academicYearId == null) {
      _showMessage('Select a subject to push.');
      return;
    }
    setState(() => _pushing = true);
    try {
      final books = await GetIt.I<CurriculumApi>().books(_pushSubjectId!);
      if (books.isEmpty) {
        _showMessage('Subject has no books scheduled.');
        return;
      }
      final res = await GetIt.I<CurriculumApi>().pushSchedule(
        bookId: books.first.id,
        academicYearId: _academicYearId!,
        afterDate: _pushDateController.text.trim(),
        reason: _pushReasonController.text.trim(),
      );
      final count = res['pushedCount'] ?? 0;
      _showMessage('Schedule pushed successfully: $count lessons shifted.');
      _loadReporting();
    } catch (e) {
      _showMessage('Could not push schedule: $e');
    } finally {
      if (mounted) setState(() => _pushing = false);
    }
  }

  Future<void> _submitAdjustLesson() async {
    final lessonId = _adjustLessonIdController.text.trim();
    final targetDate = _adjustDateController.text.trim();
    final reason = _adjustReasonController.text.trim();
    if (lessonId.isEmpty || targetDate.isEmpty) {
      _showMessage('Provide Lesson ID and target date.');
      return;
    }
    setState(() => _adjusting = true);
    try {
      await GetIt.I<CurriculumApi>().rescheduleLesson(lessonId, targetDate: targetDate, reason: reason);
      _showMessage('Lesson rescheduled successfully.');
      _adjustLessonIdController.clear();
      _loadReporting();
    } catch (e) {
      _showMessage('Could not reschedule lesson: $e');
    } finally {
      if (mounted) setState(() => _adjusting = false);
    }
  }

  void _showMessage(String text) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        leading: forceShellLeading(context),
        title: const Text('School Admin Console'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Roster', icon: Icon(Icons.people_alt_outlined)),
            Tab(text: 'Coverage & Pace', icon: Icon(Icons.analytics_outlined)),
            Tab(text: 'Reschedule', icon: Icon(Icons.edit_calendar_outlined)),
          ],
        ),
      ),
      body: FutureBuilder<_AdminData>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Loading school admin data…');
          }
          if (snap.hasError) {
            return ErrorDisplay(
              message: 'Could not load school admin data. Check your connection.',
              onRetry: () => setState(() => _future = _load()),
            );
          }
          final data = snap.data!;
          if (data.grades.isEmpty) {
            return const EmptyState(
              icon: Icons.school_outlined,
              title: 'No curriculum yet',
              message: 'Seed the curriculum for this school before assigning teachers or viewing reports.',
            );
          }
          return TabBarView(
            controller: _tabController,
            children: [
              _buildRosterTab(theme, data),
              _buildCoverageTab(theme),
              _buildRescheduleTab(theme, data),
            ],
          );
        },
      ),
    );
  }

  // ==================== TAB 1: ROSTER ====================

  Widget _buildRosterTab(ThemeData theme, _AdminData data) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Assign a teacher', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('Which real book a teacher is scheduled to teach.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _dropdown<AuthUser>(
                label: 'Teacher',
                value: data.teachers.where((t) => t.id == _assignTeacherId).firstOrNull,
                items: data.teachers,
                itemLabel: (t) => '${t.name} (${t.email})',
                onChanged: (t) => setState(() => _assignTeacherId = t?.id),
              ),
              const Gap(12),
              _dropdown<GradeSummary>(
                label: 'Grade',
                value: data.grades.where((g) => g.id == _assignGradeId).firstOrNull,
                items: data.grades,
                itemLabel: (g) => g.label,
                onChanged: (g) {
                  setState(() => _assignGradeId = g?.id);
                  if (g != null) _loadSubjectsForGrade(g.id);
                },
              ),
              const Gap(12),
              if (_loadingSubjects)
                const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: LinearProgressIndicator())
              else
                _dropdown<SubjectSummary>(
                  label: 'Subject',
                  value: _subjectsForAssignGrade.where((s) => s.id == _assignSubjectId).firstOrNull,
                  items: _subjectsForAssignGrade,
                  itemLabel: (s) => s.name,
                  onChanged: (s) => setState(() => _assignSubjectId = s?.id),
                ),
              const Gap(16),
              FilledButton(
                onPressed: (_assigningTeacher || _assignTeacherId == null || _assignSubjectId == null)
                    ? null
                    : _submitAssignTeacher,
                child: _assigningTeacher
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Assign Teacher'),
              ),
            ],
          ),
        ),
        const Gap(24),
        Text('Enroll a student', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('Which real class a student belongs to.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _dropdown<AuthUser>(
                label: 'Student',
                value: data.students.where((s) => s.id == _enrollStudentId).firstOrNull,
                items: data.students,
                itemLabel: (s) => '${s.name} (${s.email})',
                onChanged: (s) => setState(() => _enrollStudentId = s?.id),
              ),
              const Gap(12),
              _dropdown<GradeSummary>(
                label: 'Grade',
                value: data.grades.where((g) => g.id == _enrollGradeId).firstOrNull,
                items: data.grades,
                itemLabel: (g) => g.label,
                onChanged: (g) => setState(() => _enrollGradeId = g?.id),
              ),
              const Gap(16),
              FilledButton(
                onPressed: (_enrollingStudent || _enrollStudentId == null || _enrollGradeId == null)
                    ? null
                    : _submitEnrollStudent,
                child: _enrollingStudent
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Enroll Student'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ==================== TAB 2: COVERAGE & PACE ====================

  Widget _buildCoverageTab(ThemeData theme) {
    if (_loadingReporting) {
      return const LoadingIndicator(message: 'Calculating coverage & pace metrics…');
    }
    if (_reportingError != null) {
      return ErrorDisplay(
        message: 'Could not load coverage report: $_reportingError',
        onRetry: _loadReporting,
      );
    }
    if (_coverageReport == null || _delayedTopicsReport == null) {
      return Center(
        child: FilledButton.icon(
          onPressed: _loadReporting,
          icon: const Icon(Icons.refresh),
          label: const Text('Load Coverage Report'),
        ),
      );
    }

    final rep = _coverageReport!;
    final del = _delayedTopicsReport!;

    return RefreshIndicator(
      onRefresh: _loadReporting,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Academic Year Progress', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              Text('As of ${rep.asOfDate}', style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ],
          ),
          const Gap(12),
          _buildSummaryStats(theme, rep, del),
          const Gap(20),
          Text('Subject-wise Coverage & Variance', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(8),
          ...rep.subjects.map((sub) => _buildSubjectCoverageCard(theme, sub)),
          const Gap(24),
          Row(
            children: [
              Text('Delayed Topics', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              const Gap(8),
              ChipTag(
                label: '${del.delayedCount} overdue',
                color: del.delayedCount > 0 ? theme.colorScheme.error : Colors.green,
              ),
            ],
          ),
          const Gap(8),
          if (del.delayedLessons.isEmpty)
            const AppCard(
              child: Text('All scheduled lessons are currently on track or completed.'),
            )
          else
            ...del.delayedLessons.map((dl) => _buildDelayedLessonCard(theme, dl)),
        ],
      ),
    );
  }

  Widget _buildSummaryStats(ThemeData theme, CoverageReport rep, DelayedTopicsReport del) {
    final totalCompleted = rep.subjects.fold<int>(0, (sum, s) => sum + s.completedCount);
    final totalPlanned = rep.subjects.fold<int>(0, (sum, s) => sum + s.plannedCount);
    final overallPace = totalPlanned == 0 ? 100.0 : (totalCompleted / totalPlanned * 100.0);

    return Row(
      children: [
        Expanded(
          child: AppCard(
            child: Column(
              children: [
                Text('$totalCompleted', style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold, color: theme.colorScheme.primary)),
                const Gap(4),
                Text('Completed Lessons', style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ),
        const Gap(8),
        Expanded(
          child: AppCard(
            child: Column(
              children: [
                Text('${overallPace.toStringAsFixed(1)}%',
                    style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: overallPace >= 90 ? Colors.green : Colors.orange)),
                const Gap(4),
                Text('Overall Pace %', style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ),
        const Gap(8),
        Expanded(
          child: AppCard(
            child: Column(
              children: [
                Text('${del.delayedCount}',
                    style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: del.delayedCount > 0 ? theme.colorScheme.error : Colors.green)),
                const Gap(4),
                Text('Overdue Topics', style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSubjectCoverageCard(ThemeData theme, SubjectCoverage sub) {
    final varianceColor = sub.variance >= 0 ? Colors.green : Colors.red;
    return AppCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        title: Row(
          children: [
            Expanded(
              child: Text(sub.subjectName, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            ),
            ChipTag(
              label: '${sub.coveragePercent.toStringAsFixed(1)}% covered',
              color: theme.colorScheme.primary,
            ),
            const Gap(6),
            ChipTag(
              label: '${sub.variance >= 0 ? "+" : ""}${sub.variance} var',
              color: varianceColor,
            ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Teacher: ${sub.teacherName ?? "Unassigned"} · ${sub.completedCount}/${sub.totalCount} lessons',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const Gap(6),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: sub.totalCount == 0 ? 0 : sub.completedCount / sub.totalCount,
                  minHeight: 6,
                  backgroundColor: theme.colorScheme.surfaceContainerHighest,
                ),
              ),
            ],
          ),
        ),
        children: sub.chapters.map((ch) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
            child: Row(
              children: [
                Expanded(
                  child: Text(ch.chapterName, style: theme.textTheme.bodySmall),
                ),
                Text('${ch.completedCount}/${ch.totalCount}', style: theme.textTheme.bodySmall),
                const Gap(12),
                Text('${ch.coveragePercent.toStringAsFixed(0)}%',
                    style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600)),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildDelayedLessonCard(ThemeData theme, DelayedLesson dl) {
    return AppCard(
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(dl.subtopicName, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(2),
                Text('${dl.subjectName} · ${dl.chapterName}',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                const Gap(2),
                Text('Scheduled: ${dl.scheduledDate} · Teacher: ${dl.teacherName ?? "Unassigned"}',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              ChipTag(
                label: '${dl.daysOverdue}d overdue',
                color: theme.colorScheme.error,
              ),
              const Gap(4),
              TextButton(
                onPressed: () {
                  _adjustLessonIdController.text = dl.lessonId;
                  _tabController.animateTo(2); // Jump to reschedule tab
                },
                child: const Text('Reschedule'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==================== TAB 3: RESCHEDULE ====================

  Widget _buildRescheduleTab(ThemeData theme, _AdminData data) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Shift Schedule After Disruption (PUSH)', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('When school closures or unexpected events delay teaching, shift all subsequent lessons forward to the next available working days.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _dropdown<GradeSummary>(
                label: 'Grade',
                value: data.grades.where((g) => g.id == _pushGradeId).firstOrNull,
                items: data.grades,
                itemLabel: (g) => g.label,
                onChanged: (g) {
                  setState(() => _pushGradeId = g?.id);
                  if (g != null) _loadPushSubjects(g.id);
                },
              ),
              const Gap(12),
              if (_loadingPushSubjects)
                const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: LinearProgressIndicator())
              else
                _dropdown<SubjectSummary>(
                  label: 'Subject',
                  value: _pushSubjects.where((s) => s.id == _pushSubjectId).firstOrNull,
                  items: _pushSubjects,
                  itemLabel: (s) => s.name,
                  onChanged: (s) => setState(() => _pushSubjectId = s?.id),
                ),
              const Gap(12),
              TextFormField(
                controller: _pushDateController,
                decoration: const InputDecoration(
                  labelText: 'Disruption Date (YYYY-MM-DD)',
                  hintText: 'Lessons on or after this date will shift',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(12),
              TextFormField(
                controller: _pushReasonController,
                decoration: const InputDecoration(
                  labelText: 'Reason for Disruption',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(16),
              FilledButton.icon(
                onPressed: _pushing ? null : _submitPushSchedule,
                icon: _pushing
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.fast_forward_outlined),
                label: const Text('Push Subsequent Lessons'),
              ),
            ],
          ),
        ),
        const Gap(24),
        Text('Adjust Single Lesson (ADJUST)', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('Move an individual delayed or rescheduled lesson to a specific new working day.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _adjustLessonIdController,
                decoration: const InputDecoration(
                  labelText: 'Lesson ID',
                  hintText: 'Select Reschedule from Delayed Topics or paste ID',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(12),
              TextFormField(
                controller: _adjustDateController,
                decoration: const InputDecoration(
                  labelText: 'New Target Date (YYYY-MM-DD)',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(12),
              TextFormField(
                controller: _adjustReasonController,
                decoration: const InputDecoration(
                  labelText: 'Reason for Adjustment',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(16),
              FilledButton.icon(
                onPressed: _adjusting ? null : _submitAdjustLesson,
                icon: _adjusting
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.edit_calendar),
                label: const Text('Reschedule Single Lesson'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _dropdown<T>({
    required String label,
    required T? value,
    required List<T> items,
    required String Function(T) itemLabel,
    required void Function(T?) onChanged,
  }) {
    return DropdownButtonFormField<T>(
      initialValue: value,
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      isExpanded: true,
      items: items
          .map((item) => DropdownMenuItem<T>(value: item, child: Text(itemLabel(item), overflow: TextOverflow.ellipsis)))
          .toList(),
      onChanged: onChanged,
    );
  }
}

class _AdminData {
  final String? academicYearId;
  final List<GradeSummary> grades;
  final List<AuthUser> teachers;
  final List<AuthUser> students;
  const _AdminData({required this.academicYearId, required this.grades, required this.teachers, required this.students});
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
