import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import '../widgets/book_edition_card.dart';
import '../widgets/calendar_rules_card.dart';
import '../widgets/insights_card.dart';
import '../widgets/invites_panel.dart';
import '../widgets/pending_topics_card.dart';
import '../widgets/school_setup_card.dart';
import '../widgets/sections_card.dart';
import '../widgets/terms_card.dart';

/// The console's tabs, in display order. The TabBar, the TabBarView and every
/// jump between tabs are all derived from this list, so reordering or adding
/// a tab cannot silently re-point a button: the delayed lesson's
/// 'Reschedule' used to call animateTo(2) -- the Coverage tab it sits on --
/// because Reschedule had moved to index 4 (audit 2026-09-21).
enum _AdminTab {
  roster('Roster', Icons.people_alt_outlined),
  masterCalendar('Master Calendar', Icons.calendar_month_outlined),
  coverage('Coverage & Pace', Icons.analytics_outlined),
  sequence('Sequence Reorder', Icons.low_priority_outlined),
  reschedule('Reschedule', Icons.edit_calendar_outlined),
  calendarSetup('Calendar & Setup', Icons.settings_suggest_outlined);

  const _AdminTab(this.label, this.icon);
  final String label;
  final IconData icon;
}

/// Shown when a subject has no chosen edition: no book at all, or several and
/// none chosen yet (the server's 404 on GET .../selected-book).
const _noEditionMessage =
    'That subject has no chosen book edition yet -- choose one under Book editions on the Roster tab.';

/// School Admin console (§2, §11-14, §17, §32):
/// 1. Roster: Invite teachers and students (the only way anyone joins a
///    school, see InvitesPanel), manage each class's sections and class
///    teachers (M1.1), choose each subject's book edition (PRD 12.7), assign
///    teachers to it and enroll students into sections.
///    Every action below uses the subject's chosen edition, never the first
///    book listed.
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
  String? _enrollSectionId;
  bool _enrollingStudent = false;
  // The year's sections, as SectionsCard last loaded them: the enroll form
  // offers the same list. Bumping the version reloads the card, so its
  // student counts follow an enrollment.
  List<SectionSummary> _sections = [];
  int _sectionsVersion = 0;

  List<SubjectSummary> _subjectsForAssignGrade = [];
  bool _loadingSubjects = false;

  // --- Coverage Reporting State ---
  CoverageReport? _coverageReport;
  // The two figures the school renews on. Loaded with the Coverage tab
  // because that is the tab a principal opens to ask "is this working".
  PaperTiming? _timing;
  Catalog? _catalog;
  String? _insightsError;
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
  // Left blank, the server uses the subject's stored period allocation.
  final _pushPeriodsController = TextEditingController();
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
  // The weekly-off / Saturday-rule choices live in CalendarRulesCard.
  bool _creatingCalendar = false;
  // The year's saved calendar, once loaded: its presence turns "Initialize"
  // into "Update" (a second create is a 409; PUT corrects it in place).
  CalendarInfo? _calendar;
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
  // Why the last calendar load failed, kept on the card: the snackbar is
  // gone in seconds while the summary stays missing.
  String? _calendarLoadError;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _AdminTab.values.length, vsync: this);
    _tabController.addListener(() {
      final tab = _AdminTab.values[_tabController.index];
      if (tab == _AdminTab.masterCalendar && _masterLessons.isEmpty && !_loadingMasterCalendar) {
        _loadMasterCalendar();
      } else if (tab == _AdminTab.coverage && _coverageReport == null && !_loadingReporting) {
        _loadReporting();
      } else if (tab == _AdminTab.calendarSetup && _workingDaysSummary == null && !_loadingWorkingDays) {
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
    _pushPeriodsController.dispose();
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
    return _AdminData(academicYearId: currentYear.id, year: currentYear, grades: grades,
        teachers: teachers, students: students);
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
      // Separately, and deliberately not inside the Future.wait above: these
      // two read the question bank and the timing log, not the calendar, so a
      // school with no academic year set up still gets them, and a failure
      // here must not blank the coverage report beside it.
      _loadInsights();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _reportingError = serverErrorMessage(e);
        _loadingReporting = false;
      });
    }
  }

  Future<void> _loadInsights() async {
    try {
      final pillarApi = GetIt.I<PillarApi>();
      final results = await Future.wait([pillarApi.paperTiming(), pillarApi.catalog()]);
      if (!mounted) return;
      setState(() {
        _timing = results[0] as PaperTiming;
        _catalog = results[1] as Catalog;
        _insightsError = null;
      });
    } catch (e) {
      if (!mounted) return;
      // Named, not swallowed: a principal who cannot see these should know
      // the request failed rather than read an empty card as "nothing yet".
      setState(() => _insightsError = serverErrorMessage(e));
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
    } catch (e) {
      // An empty subject dropdown after a failed load read as "this class
      // has no subjects" (Task 802 audit); say that it failed, and why.
      if (mounted) setState(() => _loadingSubjects = false);
      _showMessage('Could not load subjects: ${serverErrorMessage(e)}');
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
    } catch (e) {
      if (mounted) setState(() => _loadingPushSubjects = false);
      _showMessage('Could not load subjects: ${serverErrorMessage(e)}');
    }
  }

  Future<void> _submitAssignTeacher() async {
    if (_assignTeacherId == null || _assignSubjectId == null) return;
    setState(() => _assigningTeacher = true);
    try {
      final book = await GetIt.I<CurriculumApi>().selectedBook(_assignSubjectId!);
      if (book == null) {
        _showMessage(_noEditionMessage);
        return;
      }
      await GetIt.I<CurriculumApi>().assignTeacher(teacherId: _assignTeacherId!, bookId: book.id);
      _showMessage('Teacher assigned successfully.');
      setState(() {
        _assignTeacherId = null;
        _assignSubjectId = null;
      });
    } catch (e) {
      _showMessage('Could not assign teacher: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _assigningTeacher = false);
    }
  }

  Future<void> _submitEnrollStudent() async {
    if (_enrollStudentId == null || _enrollSectionId == null) return;
    setState(() => _enrollingStudent = true);
    try {
      await GetIt.I<CurriculumApi>().enrollStudent(studentId: _enrollStudentId!, sectionId: _enrollSectionId!);
      final section = _sections.where((s) => s.id == _enrollSectionId).firstOrNull;
      _showMessage(section == null ? 'Student enrolled.' : 'Student enrolled in ${section.label}.');
      setState(() {
        _enrollStudentId = null;
        _enrollSectionId = null;
        _sectionsVersion++;
      });
    } catch (e) {
      _showMessage('Could not enroll student: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _enrollingStudent = false);
    }
  }

  Future<void> _submitPushSchedule() async {
    if (_pushSubjectId == null || _academicYearId == null) {
      _showMessage('Select a subject to push.');
      return;
    }
    final periodsText = _pushPeriodsController.text.trim();
    final periodsPerWeek = periodsText.isEmpty ? null : int.tryParse(periodsText);
    if (periodsText.isNotEmpty && (periodsPerWeek == null || periodsPerWeek <= 0)) {
      _showMessage('Periods per week must be a positive whole number, or left blank.');
      return;
    }
    setState(() => _pushing = true);
    try {
      final book = await GetIt.I<CurriculumApi>().selectedBook(_pushSubjectId!);
      if (book == null) {
        _showMessage(_noEditionMessage);
        return;
      }
      final res = await GetIt.I<CurriculumApi>().pushSchedule(
        bookId: book.id,
        academicYearId: _academicYearId!,
        fromDate: _pushDateController.text.trim(),
        reason: _pushReasonController.text.trim(),
        periodsPerWeek: periodsPerWeek,
      );
      _showMessage(res.summary);
      _loadReporting();
    } catch (e) {
      _showMessage('Could not push schedule: ${serverErrorMessage(e)}');
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
      await GetIt.I<CurriculumApi>().rescheduleLesson(lessonId, newDate: targetDate, reason: reason);
      _showMessage('Lesson rescheduled successfully.');
      _adjustLessonIdController.clear();
      _loadReporting();
    } catch (e) {
      _showMessage('Could not reschedule lesson: ${serverErrorMessage(e)}');
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
      _showMessage('Could not load school schedule: ${serverErrorMessage(e)}');
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
      _showMessage('Could not load subjects: ${serverErrorMessage(e)}');
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
      final book = await api.selectedBook(subjectId);
      if (book == null) {
        _showMessage(_noEditionMessage);
      } else {
        final bookId = book.id;
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
      _showMessage('Could not load curriculum: ${serverErrorMessage(e)}');
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
      _showMessage('Could not update sequence: ${serverErrorMessage(e)}');
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
      _showMessage('Could not update sequence: ${serverErrorMessage(e)}');
    }
  }

  Future<void> _submitCreateCalendar(List<String> weeklyOffDays, String altSatRule) async {
    if (_academicYearId == null) return;
    final updating = _calendar != null;
    setState(() => _creatingCalendar = true);
    try {
      final api = GetIt.I<CurriculumApi>();
      if (updating) {
        await api.updateCalendar(_academicYearId!,
            weeklyOffDays: weeklyOffDays, alternateSaturdayRule: altSatRule);
      } else {
        await api.createCalendar(_academicYearId!,
            weeklyOffDays: weeklyOffDays, alternateSaturdayRule: altSatRule);
      }
      _showMessage(updating ? 'Academic Calendar updated.' : 'Academic Calendar initialized successfully.');
      _loadCalendarSetup();
    } catch (e) {
      _showMessage('Could not ${updating ? 'update' : 'initialize'} calendar: ${serverErrorMessage(e)}');
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
      _showMessage('Could not set period configuration: ${serverErrorMessage(e)}');
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
      _showMessage('Could not add holiday: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _addingHoliday = false);
    }
  }

  Future<void> _deleteHoliday(HolidayInfo h) async {
    if (_academicYearId == null) return;
    try {
      await GetIt.I<CurriculumApi>().deleteHoliday(_academicYearId!, h.id);
      _showMessage('Holiday "${h.label}" removed.');
      _loadCalendarSetup();
    } catch (e) {
      _showMessage('Could not remove holiday: ${serverErrorMessage(e)}');
    }
  }

  Future<void> _loadCalendarSetup() async {
    if (_academicYearId == null) return;
    setState(() => _loadingWorkingDays = true);
    try {
      final api = GetIt.I<CurriculumApi>();
      final cal = await api.getCalendar(_academicYearId!);
      if (mounted) {
        setState(() {
          _calendar = cal;
          _calendarLoadError = null;
          // Cleared before the reads below, so a failed or calendar-less
          // reload never leaves an earlier load's count on screen as if it
          // described the calendar now saved.
          _workingDaysSummary = null;
          _holidaysList = [];
        });
      }
      if (cal == null) return;
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
    } catch (e) {
      // A missing calendar is not an error here (getCalendar turns its 404
      // into null, handled above). What lands here is a real failure --
      // chiefly /working-days' 404 for a saved calendar holding a value
      // calendar.py now rejects (a legacy 'Sun', an unparseable Saturday
      // rule), whose detail names that value. Swallowing it left "Saved: ..."
      // and "Update Calendar" on screen with no count and no reason.
      final message = serverErrorMessage(e);
      if (mounted) {
        setState(() {
          _calendarLoadError = message;
          _workingDaysSummary = null;
          _holidaysList = [];
        });
      }
      _showMessage('Could not load calendar: $message');
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
          tabs: [
            for (final tab in _AdminTab.values) Tab(text: tab.label, icon: Icon(tab.icon)),
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
              message: 'Could not load school admin data: ${serverErrorMessage(snap.error!)}',
              onRetry: () => setState(() { _future = _load(); }),
            );
          }
          final data = snap.data!;
          if (data.grades.isEmpty) {
            // Invites do not depend on the curriculum: a new school's
            // principal has to be able to bring in teachers first. The
            // setup card is the web's way to seed the classes, which only
            // the API had (audit D27).
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                SchoolSetupCard(
                  api: GetIt.I<CurriculumApi>(),
                  year: data.year,
                  onDone: () {
                    _showMessage('Classes set up. Add your calendar rules and terms on Calendar & Setup.');
                    setState(() { _future = _load(); });
                  },
                ),
                const Gap(16),
                const InvitesPanel(),
              ],
            );
          }
          return TabBarView(
            controller: _tabController,
            children: [
              for (final tab in _AdminTab.values)
                switch (tab) {
                  _AdminTab.roster => _buildRosterTab(theme, data),
                  _AdminTab.masterCalendar => _buildMasterCalendarTab(theme, data),
                  _AdminTab.coverage => _buildCoverageTab(theme),
                  _AdminTab.sequence => _buildSequenceTab(theme, data),
                  _AdminTab.reschedule => _buildRescheduleTab(theme, data),
                  _AdminTab.calendarSetup => _buildCalendarSetupTab(theme, data),
                },
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
        const InvitesPanel(),
        const Gap(24),
        SectionsCard(
          key: ValueKey('sections-card-$_sectionsVersion'),
          api: GetIt.I<CurriculumApi>(),
          academicYearId: data.academicYearId!,
          grades: data.grades,
          teachers: data.teachers,
          onMessage: _showMessage,
          onLoaded: (sections) {
            if (!mounted) return;
            setState(() {
              _sections = sections;
              if (!sections.any((s) => s.id == _enrollSectionId)) _enrollSectionId = null;
            });
          },
        ),
        const Gap(24),
        Text('Book editions', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('One book per subject for the year, chosen by the school. Scheduling, assigning and reordering use it.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const Gap(12),
        BookEditionCard(key: const ValueKey('book-editions-card'), grades: data.grades, onMessage: _showMessage),
        const Gap(24),
        Text('Assign a teacher', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text("A teacher is assigned to the subject's chosen book edition.",
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
                style: phoneTapTarget(context),
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
        Text('The section a student is in. Enrolling a student again moves them.',
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
              _dropdown<SectionSummary>(
                key: ValueKey('enroll-section-$_sectionsVersion-${_sections.length}'),
                label: 'Class and section',
                value: _sections.where((s) => s.id == _enrollSectionId).firstOrNull,
                items: _sections,
                itemLabel: (s) => s.label,
                onChanged: (s) => setState(() => _enrollSectionId = s?.id),
              ),
              const Gap(16),
              FilledButton(
                onPressed: (_enrollingStudent || _enrollStudentId == null || _enrollSectionId == null)
                    ? null
                    : _submitEnrollStudent,
                style: phoneTapTarget(context),
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
          style: phoneTapTarget(context),
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
            children: [
              // Expanded, not spaceBetween: unbounded, the heading and the
              // date ran 211 px off a 375 px phone (Task 801). The date still
              // sits at the right-hand end on a wide screen.
              Expanded(
                child: Text('Academic Year Progress',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              ),
              const Gap(8),
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
              // Flexible, not Expanded: the heading and its count chip
              // together are wider than a 375 px phone (Task 801), so the
              // heading needs a bound to wrap against -- but Expanded is a
              // tight fit, which would make the heading eat every spare pixel
              // and shove the "N overdue" chip to the far right of the card on
              // a laptop, away from the number it counts. Loose keeps the
              // heading at its natural width whenever it fits.
              Flexible(
                child: Text('Delayed Topics',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              ),
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
          const Gap(16),
          // Below the coverage report, not above it: this tab is named
          // Coverage & Pace, and the card at the top pushed the tab's own
          // subject rows off a 375 px phone (the responsive suite caught it).
          // These are the two figures a school renews on -- time saved, and
          // what the bank holds for the classes we sell -- from endpoints
          // that have been principal-gated since before the first release
          // with no caller in any screen.
          if (_timing != null && _catalog != null)
            InsightsCard(
              timing: _timing!,
              catalog: _catalog!,
              // The card reports a save that fails; a saved one reloads the
              // card so the saving is measured against the new baseline.
              onSetBaseline: (minutes) async {
                await GetIt.I<PillarApi>().setTermBaseline(_timing!.term!.id, minutes);
                await _loadInsights();
              },
            )
          else if (_insightsError != null)
            ErrorDisplay(
              message: 'Could not load time saved and bank coverage: $_insightsError',
              onRetry: _loadInsights,
            ),
        ],
      ),
    );
  }

  /// The headline figures are the backend's own (overallCoveragePct,
  /// overallPacePct and the counts behind them), never re-derived here: the
  /// old client-side pace summed per-subject counts it had failed to parse,
  /// got 0 planned, and fell back to 100% for a school 89 lessons behind.
  Widget _buildSummaryStats(ThemeData theme, CoverageReport rep, DelayedTopicsReport del) {
    final pace = rep.overallPace;
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);

    return Row(
      children: [
        Expanded(
          child: AppCard(
            child: Column(
              children: [
                Text('${rep.overallCoveragePct.toStringAsFixed(1)}%',
                    style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold, color: theme.colorScheme.primary)),
                const Gap(4),
                Text('Syllabus Covered', style: theme.textTheme.bodySmall),
                Text('${rep.completedLessons} of ${rep.totalLessons} lessons taught', style: muted),
              ],
            ),
          ),
        ),
        const Gap(8),
        Expanded(
          child: AppCard(
            child: Column(
              children: [
                Text(_paceText(pace),
                    style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: pace == null
                            ? theme.colorScheme.onSurfaceVariant
                            : (pace >= 90 ? Colors.green : Colors.orange))),
                const Gap(4),
                Text('Overall Pace', style: theme.textTheme.bodySmall),
                Text(
                    pace == null
                        ? 'No lessons due yet'
                        : '${rep.completedToDate} of ${rep.plannedToDate} due lessons taught',
                    style: muted),
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

  /// '—' when no lesson was due yet: the backend reports pace 100.0 then,
  /// which would read as "on track" for a subject nobody has started.
  static String _paceText(double? pace) => pace == null ? '—' : '${pace.toStringAsFixed(1)}%';

  Widget _buildSubjectCoverageCard(ThemeData theme, SubjectCoverage sub) {
    final varianceColor = sub.variance >= 0 ? Colors.green : Colors.red;
    final pace = sub.pace;
    final paceClause = pace == null
        ? 'no lessons due yet'
        : '${sub.completedToDate} of ${sub.plannedToDate} due to date · pace ${_paceText(pace)}';
    return AppCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        title: Row(
          children: [
            Expanded(
              child: Text('Grade ${sub.gradeNumber} · ${sub.subjectName}',
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            ),
            ChipTag(
              label: '${sub.coveragePct.toStringAsFixed(1)}% covered',
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
              Text(
                  'Teacher: ${sub.teacherName ?? "Unassigned"} · '
                  '${sub.completedLessons}/${sub.totalLessons} lessons taught · $paceClause',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const Gap(6),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: (sub.coveragePct / 100).clamp(0.0, 1.0),
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
                Text('${ch.completedLessons}/${ch.totalLessons}', style: theme.textTheme.bodySmall),
                const Gap(12),
                Text('${ch.coveragePct.toStringAsFixed(0)}%',
                    style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600)),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  /// A delayed lesson and the one action on it. The overdue chip and
  /// Reschedule sit beside the lesson on a wide screen and under it on a
  /// phone: side by side they are laid out at their natural width, which
  /// left 15 px too little for the lesson on a 375 px screen (Task 801).
  Widget _buildDelayedLessonCard(ThemeData theme, DelayedLesson dl) {
    final lesson = Column(
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
    );
    final overdue = ChipTag(label: '${dl.daysOverdue}d overdue', color: theme.colorScheme.error);
    final reschedule = TextButton(
      onPressed: () {
        _adjustLessonIdController.text = dl.lessonId;
        _tabController.animateTo(_AdminTab.reschedule.index);
      },
      // The one action on the coverage dashboard, so it is phone-sized.
      style: phoneTapTarget(context),
      child: const Text('Reschedule'),
    );

    return AppCard(
      child: LayoutBuilder(
        builder: (context, constraints) => constraints.maxWidth < 420
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  lesson,
                  const Gap(4),
                  // Wrap, not Row: the chip and the button drop onto separate
                  // lines rather than overflow when the text is scaled up.
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [overdue, reschedule],
                  ),
                ],
              )
            : Row(
                children: [
                  Expanded(child: lesson),
                  const Gap(8),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [overdue, const Gap(4), reschedule],
                  ),
                ],
              ),
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
              const Gap(12),
              TextFormField(
                controller: _pushPeriodsController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Periods per week (optional)',
                  hintText: "Leave blank to use the subject's stored allocation",
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(16),
              FilledButton.icon(
                onPressed: _pushing ? null : _submitPushSchedule,
                style: phoneTapTarget(context),
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
                style: phoneTapTarget(context),
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
                    // Changing the day is this tab's primary action, and a
                    // TextButton's M3 minimum is 40 px -- under the 44 a thumb
                    // reliably hits. The two arrows either side already get
                    // their 48 from _IconButtonDefaultsM3.
                    style: phoneTapTarget(context),
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
        const Gap(24),
        // A chapter cannot be delivered below chapter level until its topics
        // are real, so the approval step belongs next to the sequence, not on
        // a screen of its own.
        //
        // Below the sequence, not above it, for the same reason InsightsCard
        // sits at the end of Coverage & Pace: at the top this card pushed the
        // tab's own grade/subject rows and its units list off a 375 px phone
        // at 1.3x text, which the responsive suite caught.
        PendingTopicsCard(grades: data.grades, onMessage: _showMessage),
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
        CalendarRulesCard(
          saved: _calendar,
          busy: _creatingCalendar,
          onSubmit: _submitCreateCalendar,
        ),
        const Gap(16),
        if (data.year != null) ...[
          TermsCard(
            api: GetIt.I<CurriculumApi>(),
            year: data.year!,
            onMessage: _showMessage,
            // Exam coverage and time saved on the Coverage tab are per term.
            onChanged: _loadInsights,
          ),
          const Gap(16),
        ],
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
                style: phoneTapTarget(context),
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
                // isExpanded + ellipsis, as _dropdown<T> does: without them the
                // field sizes itself to its widest entry, 'School Event (still
                // a working day)', and runs off a 375 px phone (Task 801).
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Holiday Kind', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'public', child: Text('Public Holiday', overflow: TextOverflow.ellipsis)),
                  DropdownMenuItem(value: 'school', child: Text('School Holiday', overflow: TextOverflow.ellipsis)),
                  DropdownMenuItem(value: 'emergency', child: Text('Emergency Closure', overflow: TextOverflow.ellipsis)),
                  // The one kind that does NOT remove a teaching day.
                  DropdownMenuItem(
                      value: 'event', child: Text('School Event (still a working day)', overflow: TextOverflow.ellipsis)),
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
                style: phoneTapTarget(context),
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
              ] else if (_calendarLoadError != null)
                Text('Working days could not be computed: $_calendarLoadError',
                    style: TextStyle(color: theme.colorScheme.error))
              else
                const Text('Initialize the academic calendar above to compute teaching days.'),
              if (_holidaysList.isNotEmpty) ...[
                const Gap(8),
                const Divider(),
                const Gap(8),
                Text('Configured Holidays (${_holidaysList.length}):',
                    style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(4),
                ..._holidaysList.map(
                  (h) => Row(
                    children: [
                      Expanded(
                        child: Text(
                            '• ${h.date}${h.endDate != null ? ' to ${h.endDate}' : ''}: ${h.label} (${h.kind})',
                            style: theme.textTheme.bodySmall),
                      ),
                      IconButton(
                        tooltip: 'Remove holiday',
                        visualDensity: VisualDensity.compact,
                        icon: const Icon(Icons.delete_outline, size: 18),
                        onPressed: () => _deleteHoliday(h),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _dropdown<T>({
    Key? key,
    required String label,
    required T? value,
    required List<T> items,
    required String Function(T) itemLabel,
    required void Function(T?) onChanged,
  }) {
    return DropdownButtonFormField<T>(
      key: key,
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
  final AcademicYearSummary? year;
  final List<GradeSummary> grades;
  final List<AuthUser> teachers;
  final List<AuthUser> students;
  const _AdminData({required this.academicYearId, this.year, required this.grades, required this.teachers, required this.students});
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
