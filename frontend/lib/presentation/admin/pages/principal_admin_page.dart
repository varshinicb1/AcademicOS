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

  // --- Master Calendar State ---
  DateTime _masterCalendarDate = DateTime.now();
  List<ScheduledLessonSummary> _masterLessons = [];
  bool _loadingMasterCalendar = false;

  // --- Sequence Reorder State ---
  String? _seqGradeId;
  String? _seqSubjectId;
  List<SubjectSummary> _seqSubjects = [];
  bool _loadingSeqSubjects = false;
  List<UnitSummary> _seqUnits = [];
  List<ChapterSummary> _seqChapters = [];
  bool _loadingSeqContent = false;
  int _seqMode = 0; // 0: units, 1: chapters

  // --- Calendar & Period Setup State ---
  int _weeklyOffDay = 7; // Sunday
  String _altSatRule = 'none';
  bool _creatingCalendar = false;
  final _periodMinutesController = TextEditingController(text: '45');
  bool _savingPeriodMinutes = false;
  final _holidayDateController = TextEditingController(
    text: DateTime.now().toString().substring(0, 10),
  );
  final _holidayLabelController = TextEditingController();
  String _holidayKind = 'public';
  final _holidayEndDateController = TextEditingController();
  bool _addingHoliday = false;
  WorkingDaysSummary? _workingDaysSummary;
  bool _loadingWorkingDays = false;
  List<HolidayInfo> _holidaysList = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    _tabController.addListener(() {
      if (_tabController.index == 1 && _masterLessons.isEmpty && !_loadingMasterCalendar) {
        _loadMasterCalendar();
      } else if (_tabController.index == 2 && _coverageReport == null && !_loadingReporting) {
        _loadReporting();
      } else if (_tabController.index == 5 && _workingDaysSummary == null && !_loadingWorkingDays) {
        _loadCalendarSetup();
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
    _periodMinutesController.dispose();
    _holidayDateController.dispose();
    _holidayLabelController.dispose();
    _holidayEndDateController.dispose();
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

  Future<void> _loadMasterCalendar() async {
    setState(() => _loadingMasterCalendar = true);
    try {
      final start = _masterCalendarDate.subtract(const Duration(days: 14)).toString().substring(0, 10);
      final end = _masterCalendarDate.add(const Duration(days: 14)).toString().substring(0, 10);
      final lessons = await GetIt.I<CurriculumApi>().schoolSchedule(startDate: start, endDate: end);
      if (mounted) setState(() => _masterLessons = lessons);
    } catch (e) {
      _showMessage('Could not load school schedule: $e');
    } finally {
      if (mounted) setState(() => _loadingMasterCalendar = false);
    }
  }

  Future<void> _onSeqGradeChanged(String? gradeId) async {
    setState(() {
      _seqGradeId = gradeId;
      _seqSubjectId = null;
      _seqSubjects = [];
      _seqUnits = [];
      _seqChapters = [];
    });
    if (gradeId == null) return;
    setState(() => _loadingSeqSubjects = true);
    try {
      final subs = await GetIt.I<CurriculumApi>().subjects(gradeId);
      if (mounted) setState(() => _seqSubjects = subs);
    } catch (e) {
      _showMessage('Could not load subjects: $e');
    } finally {
      if (mounted) setState(() => _loadingSeqSubjects = false);
    }
  }

  Future<void> _onSeqSubjectChanged(String? subjectId) async {
    setState(() {
      _seqSubjectId = subjectId;
      _seqUnits = [];
      _seqChapters = [];
    });
    if (subjectId == null) return;
    setState(() => _loadingSeqContent = true);
    try {
      final api = GetIt.I<CurriculumApi>();
      final books = await api.books(subjectId);
      if (books.isNotEmpty) {
        final bookId = books.first.id;
        final units = await api.units(bookId);
        final chapters = await api.chapters(bookId);
        units.sort((a, b) => a.seq.compareTo(b.seq));
        chapters.sort((a, b) => a.seq.compareTo(b.seq));
        if (mounted) {
          setState(() {
            _seqUnits = units;
            _seqChapters = chapters;
          });
        }
      }
    } catch (e) {
      _showMessage('Could not load curriculum: $e');
    } finally {
      if (mounted) setState(() => _loadingSeqContent = false);
    }
  }

  Future<void> _reorderUnit(int oldIndex, int newIndex) async {
    if (oldIndex < newIndex) newIndex -= 1;
    final item = _seqUnits.removeAt(oldIndex);
    _seqUnits.insert(newIndex, item);
    setState(() {});
    try {
      await GetIt.I<CurriculumApi>().setUnitSequence(item.id, newIndex);
      _showMessage('Unit "${item.name}" sequence updated to #$newIndex');
    } catch (e) {
      _showMessage('Could not update sequence: $e');
    }
  }

  Future<void> _reorderChapter(int oldIndex, int newIndex) async {
    if (oldIndex < newIndex) newIndex -= 1;
    final item = _seqChapters.removeAt(oldIndex);
    _seqChapters.insert(newIndex, item);
    setState(() {});
    try {
      await GetIt.I<CurriculumApi>().setChapterSequence(item.id, newIndex);
      _showMessage('Chapter "${item.name}" sequence updated to #$newIndex');
    } catch (e) {
      _showMessage('Could not update sequence: $e');
    }
  }

  Future<void> _submitCreateCalendar() async {
    if (_academicYearId == null) return;
    setState(() => _creatingCalendar = true);
    try {
      await GetIt.I<CurriculumApi>().createCalendar(
        _academicYearId!,
        weeklyOffDays: [_weeklyOffDay],
        alternateSaturdayRule: _altSatRule,
      );
      _showMessage('Academic Calendar initialized successfully.');
      _loadCalendarSetup();
    } catch (e) {
      _showMessage('Could not initialize calendar: $e');
    } finally {
      if (mounted) setState(() => _creatingCalendar = false);
    }
  }

  Future<void> _submitSavePeriodDuration() async {
    if (_academicYearId == null) return;
    final mins = int.tryParse(_periodMinutesController.text.trim());
    if (mins == null || mins <= 0) {
      _showMessage('Enter valid period duration in minutes.');
      return;
    }
    setState(() => _savingPeriodMinutes = true);
    try {
      await GetIt.I<CurriculumApi>().setPeriodConfiguration(_academicYearId!, periodMinutes: mins);
      _showMessage('Period duration configured: $mins minutes.');
    } catch (e) {
      _showMessage('Could not set period configuration: $e');
    } finally {
      if (mounted) setState(() => _savingPeriodMinutes = false);
    }
  }

  Future<void> _submitAddHoliday() async {
    if (_academicYearId == null) return;
    final date = _holidayDateController.text.trim();
    final label = _holidayLabelController.text.trim();
    final end = _holidayEndDateController.text.trim();
    if (date.isEmpty || label.isEmpty) {
      _showMessage('Please provide date and holiday label.');
      return;
    }
    setState(() => _addingHoliday = true);
    try {
      await GetIt.I<CurriculumApi>().addHoliday(
        _academicYearId!,
        date: date,
        label: label,
        kind: _holidayKind,
        endDate: end.isEmpty ? null : end,
      );
      _showMessage('Holiday "$label" added.');
      _holidayLabelController.clear();
      _loadCalendarSetup();
    } catch (e) {
      _showMessage('Could not add holiday: $e');
    } finally {
      if (mounted) setState(() => _addingHoliday = false);
    }
  }

  Future<void> _loadCalendarSetup() async {
    if (_academicYearId == null) return;
    setState(() => _loadingWorkingDays = true);
    try {
      final api = GetIt.I<CurriculumApi>();
      final results = await Future.wait([
        api.getWorkingDays(_academicYearId!),
        api.listHolidays(_academicYearId!),
      ]);
      if (mounted) {
        setState(() {
          _workingDaysSummary = results[0] as WorkingDaysSummary;
          _holidaysList = results[1] as List<HolidayInfo>;
        });
      }
    } catch (_) {
      // Ignored if calendar not yet created
    } finally {
      if (mounted) setState(() => _loadingWorkingDays = false);
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
          isScrollable: true,
          controller: _tabController,
          tabs: const [
            Tab(text: 'Roster', icon: Icon(Icons.people_alt_outlined)),
            Tab(text: 'Master Calendar', icon: Icon(Icons.calendar_month_outlined)),
            Tab(text: 'Coverage & Pace', icon: Icon(Icons.analytics_outlined)),
            Tab(text: 'Sequence Reorder', icon: Icon(Icons.low_priority_outlined)),
            Tab(text: 'Reschedule', icon: Icon(Icons.edit_calendar_outlined)),
            Tab(text: 'Calendar & Setup', icon: Icon(Icons.settings_suggest_outlined)),
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
              _buildMasterCalendarTab(theme, data),
              _buildCoverageTab(theme),
              _buildSequenceTab(theme, data),
              _buildRescheduleTab(theme, data),
              _buildCalendarSetupTab(theme, data),
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

  // ==================== TAB 4: MASTER CALENDAR (§11-14) ====================

  Widget _buildMasterCalendarTab(ThemeData theme, _AdminData data) {
    final curDateStr = _masterCalendarDate.toString().substring(0, 10);
    final dayLessons = _masterLessons.where((l) => l.scheduledDate == curDateStr).toList();
    final totalScheduled = _masterLessons.where((l) => l.status == 'scheduled').length;
    final totalCompleted = _masterLessons.where((l) => l.status == 'completed').length;
    final totalSkipped = _masterLessons.where((l) => l.status == 'skipped').length;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('School-Wide Master Calendar', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                  const Gap(2),
                  Text('Master schedule of all lessons across all subjects and grades (§11-14).',
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh Schedule',
              onPressed: _loadingMasterCalendar ? null : _loadMasterCalendar,
            ),
          ],
        ),
        const Gap(12),
        AppCard(
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.chevron_left),
                onPressed: () {
                  setState(() => _masterCalendarDate = _masterCalendarDate.subtract(const Duration(days: 1)));
                  _loadMasterCalendar();
                },
              ),
              Expanded(
                child: Center(
                  child: TextButton.icon(
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: _masterCalendarDate,
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2030),
                      );
                      if (picked != null) {
                        setState(() => _masterCalendarDate = picked);
                        _loadMasterCalendar();
                      }
                    },
                    icon: const Icon(Icons.calendar_today, size: 18),
                    label: Text(
                      'Date: $curDateStr',
                      style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.chevron_right),
                onPressed: () {
                  setState(() => _masterCalendarDate = _masterCalendarDate.add(const Duration(days: 1)));
                  _loadMasterCalendar();
                },
              ),
            ],
          ),
        ),
        const Gap(12),
        Row(
          children: [
            Expanded(
              child: AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Completed', style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.primary)),
                    Text('$totalCompleted', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
            const Gap(8),
            Expanded(
              child: AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Scheduled', style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.secondary)),
                    Text('$totalScheduled', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
            const Gap(8),
            Expanded(
              child: AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Skipped', style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.error)),
                    Text('$totalSkipped', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
          ],
        ),
        const Gap(16),
        Text('Lessons for $curDateStr (${dayLessons.length})',
            style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(8),
        if (_loadingMasterCalendar)
          const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
        else if (dayLessons.isEmpty)
          const EmptyState(
            icon: Icons.event_busy_outlined,
            title: 'No lessons scheduled',
            message: 'No lessons scheduled across the school for this date.',
          )
        else
          ...dayLessons.map((l) {
            Color statusColor;
            IconData statusIcon;
            if (l.status == 'completed') {
              statusColor = Colors.green;
              statusIcon = Icons.check_circle_outline;
            } else if (l.status == 'skipped') {
              statusColor = theme.colorScheme.error;
              statusIcon = Icons.cancel_outlined;
            } else {
              statusColor = theme.colorScheme.primary;
              statusIcon = Icons.schedule_outlined;
            }
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: statusColor.withValues(alpha: 0.12),
                  child: Icon(statusIcon, color: statusColor),
                ),
                title: Text('Period ${l.periodNumber} • Subtopic: ${l.subtopicId.split(':').last}'),
                subtitle: Text('Book: ${l.bookId.split(':').last} • Status: ${l.status}${l.note != null ? " (${l.note})" : ""}'),
                trailing: Text(l.status.toUpperCase(), style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 11)),
              ),
            );
          }),
      ],
    );
  }

  // ==================== TAB 5: SEQUENCE REORDER (§13) ====================

  Widget _buildSequenceTab(ThemeData theme, _AdminData data) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Curriculum Delivery Sequence', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('Drag and drop units or chapters to reorder delivery sequence (§13).',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _dropdown<GradeSummary>(
                label: 'Select Grade',
                value: data.grades.where((g) => g.id == _seqGradeId).firstOrNull,
                items: data.grades,
                itemLabel: (g) => g.label,
                onChanged: (g) => _onSeqGradeChanged(g?.id),
              ),
              if (_loadingSeqSubjects) ...[
                const Gap(8),
                const LinearProgressIndicator(),
              ],
              if (_seqSubjects.isNotEmpty) ...[
                const Gap(12),
                _dropdown<SubjectSummary>(
                  label: 'Select Subject',
                  value: _seqSubjects.where((s) => s.id == _seqSubjectId).firstOrNull,
                  items: _seqSubjects,
                  itemLabel: (s) => s.name,
                  onChanged: (s) => _onSeqSubjectChanged(s?.id),
                ),
              ],
            ],
          ),
        ),
        const Gap(16),
        if (_loadingSeqContent)
          const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
        else if (_seqUnits.isNotEmpty || _seqChapters.isNotEmpty) ...[
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 0, label: Text('Units Sequence'), icon: Icon(Icons.view_agenda_outlined)),
              ButtonSegment(value: 1, label: Text('Chapters Sequence'), icon: Icon(Icons.list_alt_outlined)),
            ],
            selected: {_seqMode},
            onSelectionChanged: (set) => setState(() => _seqMode = set.first),
          ),
          const Gap(16),
          if (_seqMode == 0) ...[
            Text('Reorder Units (${_seqUnits.length})', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const Gap(4),
            Text('Hold and drag handle on the right to reorder sequence.', style: theme.textTheme.bodySmall),
            const Gap(8),
            ReorderableListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _seqUnits.length,
              // ignore: deprecated_member_use
              onReorder: _reorderUnit,
              itemBuilder: (context, index) {
                final u = _seqUnits[index];
                return Card(
                  key: ValueKey(u.id),
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text('${index + 1}'),
                    ),
                    title: Text(u.name),
                    subtitle: Text('Unit ${u.unitNo} • ${u.marks} marks'),
                    trailing: const Icon(Icons.drag_handle),
                  ),
                );
              },
            ),
          ] else ...[
            Text('Reorder Chapters (${_seqChapters.length})', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const Gap(4),
            Text('Hold and drag handle on the right to reorder sequence.', style: theme.textTheme.bodySmall),
            const Gap(8),
            ReorderableListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _seqChapters.length,
              // ignore: deprecated_member_use
              onReorder: _reorderChapter,
              itemBuilder: (context, index) {
                final c = _seqChapters[index];
                return Card(
                  key: ValueKey(c.id),
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text('${index + 1}'),
                    ),
                    title: Text(c.name),
                    subtitle: Text('ID: ${c.canonicalId}'),
                    trailing: const Icon(Icons.drag_handle),
                  ),
                );
              },
            ),
          ],
        ] else if (_seqSubjectId != null) ...[
          const EmptyState(
            icon: Icons.menu_book_outlined,
            title: 'No units found',
            message: 'No units or chapters found for this subject book.',
          ),
        ],
      ],
    );
  }

  // ==================== TAB 6: CALENDAR & PERIOD SETUP (§8, §10) ====================

  Widget _buildCalendarSetupTab(ThemeData theme, _AdminData data) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Calendar & Period Configuration', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('Setup academic calendar rules, period durations, and block holidays (§8, §10).',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Academic Calendar Rules', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const Gap(8),
              DropdownButtonFormField<int>(
                initialValue: _weeklyOffDay,
                decoration: const InputDecoration(labelText: 'Weekly Off Day', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 7, child: Text('Sunday (Default)')),
                  DropdownMenuItem(value: 6, child: Text('Saturday')),
                  DropdownMenuItem(value: 5, child: Text('Friday')),
                ],
                onChanged: (v) => setState(() => _weeklyOffDay = v ?? 7),
              ),
              const Gap(12),
              DropdownButtonFormField<String>(
                initialValue: _altSatRule,
                decoration: const InputDecoration(labelText: 'Alternate Saturday Rule', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'none', child: Text('None (All working)')),
                  DropdownMenuItem(value: 'second_fourth', child: Text('2nd & 4th Saturdays Off')),
                  DropdownMenuItem(value: 'all', child: Text('All Saturdays Off')),
                ],
                onChanged: (v) => setState(() => _altSatRule = v ?? 'none'),
              ),
              const Gap(12),
              FilledButton.icon(
                onPressed: _creatingCalendar ? null : _submitCreateCalendar,
                icon: _creatingCalendar
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.calendar_month),
                label: const Text('Initialize Calendar'),
              ),
            ],
          ),
        ),
        const Gap(16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Period Duration Configuration', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const Gap(8),
              TextField(
                controller: _periodMinutesController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Period Duration (minutes)',
                  helperText: 'Standard teaching period duration in minutes (e.g. 45).',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(12),
              FilledButton.icon(
                onPressed: _savingPeriodMinutes ? null : _submitSavePeriodDuration,
                icon: _savingPeriodMinutes
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.timer_outlined),
                label: const Text('Save Period Duration'),
              ),
            ],
          ),
        ),
        const Gap(16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Add Block Holiday', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const Gap(8),
              TextField(
                controller: _holidayDateController,
                decoration: const InputDecoration(labelText: 'Date (YYYY-MM-DD)', border: OutlineInputBorder()),
              ),
              const Gap(12),
              TextField(
                controller: _holidayLabelController,
                decoration: const InputDecoration(labelText: 'Holiday Label (e.g. Diwali Vacation)', border: OutlineInputBorder()),
              ),
              const Gap(12),
              DropdownButtonFormField<String>(
                initialValue: _holidayKind,
                decoration: const InputDecoration(labelText: 'Holiday Kind', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'public', child: Text('Public Holiday')),
                  DropdownMenuItem(value: 'school', child: Text('School Holiday')),
                  DropdownMenuItem(value: 'emergency', child: Text('Emergency Closure')),
                ],
                onChanged: (v) => setState(() => _holidayKind = v ?? 'public'),
              ),
              const Gap(12),
              TextField(
                controller: _holidayEndDateController,
                decoration: const InputDecoration(labelText: 'End Date (Optional, for range)', border: OutlineInputBorder()),
              ),
              const Gap(12),
              FilledButton.icon(
                onPressed: _addingHoliday ? null : _submitAddHoliday,
                icon: _addingHoliday
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.add_circle_outline),
                label: const Text('Add Holiday'),
              ),
            ],
          ),
        ),
        const Gap(16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text('Teaching Days Computation (§10)',
                        style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: _loadingWorkingDays ? null : _loadCalendarSetup,
                  ),
                ],
              ),
              const Gap(8),
              if (_loadingWorkingDays)
                const LinearProgressIndicator()
              else if (_workingDaysSummary != null) ...[
                Text('Total Days: ${_workingDaysSummary!.totalDays}'),
                const Gap(4),
                Text('Working Days: ${_workingDaysSummary!.workingDays}',
                    style: TextStyle(color: theme.colorScheme.primary, fontWeight: FontWeight.bold)),
                const Gap(4),
                Text('Holidays: ${_workingDaysSummary!.holidayCount}'),
                const Gap(4),
                Text('Weekly Offs: ${_workingDaysSummary!.weeklyOffCount}'),
                const Gap(4),
                Text('Alternate Saturdays Off: ${_workingDaysSummary!.alternateSaturdayOffCount}'),
              ] else
                const Text('Initialize the academic calendar above to compute teaching days.'),
              if (_holidaysList.isNotEmpty) ...[
                const Gap(8),
                const Divider(),
                const Gap(8),
                Text('Configured Holidays (${_holidaysList.length}):',
                    style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(4),
                ..._holidaysList.map(
                  (h) => Text('• ${h.date}: ${h.label} (${h.kind})', style: theme.textTheme.bodySmall),
                ),
              ],
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
