import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// The missing piece that made every backend milestone this session built
/// (teacher assignment, student enrollment) usable only via curl/Postman:
/// a real admin screen for a principal to actually assign a teacher to a
/// book and enroll a student in a class. Without this, `my_schedule_page`
/// and `student_schedule_page` are both real and correct but permanently
/// empty for a real school, since nothing else in the app can create a
/// `TeacherAssignment` or `StudentEnrollment` row.
///
/// Deliberately minimal -- two real forms, not a full admin console. The
/// rest of the admin-web surface (calendar setup, period configuration,
/// rescheduling, a school-wide calendar view) still doesn't exist; this
/// is the first real screen of it, picked because it's the one that
/// actually unblocks the rest of what's already built.
class PrincipalAdminPage extends StatefulWidget {
  const PrincipalAdminPage({super.key});

  @override
  State<PrincipalAdminPage> createState() => _PrincipalAdminPageState();
}

class _PrincipalAdminPageState extends State<PrincipalAdminPage> {
  late Future<_AdminData> _future;

  String? _assignTeacherId;
  String? _assignGradeId;
  String? _assignSubjectId;
  bool _assigningTeacher = false;

  String? _enrollStudentId;
  String? _enrollGradeId;
  bool _enrollingStudent = false;

  List<SubjectSummary> _subjectsForAssignGrade = [];
  bool _loadingSubjects = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
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
      return _AdminData(grades: const [], teachers: teachers, students: students);
    }
    years.sort((a, b) => a.startDate.compareTo(b.startDate));
    final grades = await curriculumApi.grades(years.last.id);
    return _AdminData(grades: grades, teachers: teachers, students: students);
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
      _showMessage('Assigned.');
      setState(() {
        _assignTeacherId = null;
        _assignSubjectId = null;
      });
    } catch (e) {
      _showMessage('Could not assign: $e');
    } finally {
      if (mounted) setState(() => _assigningTeacher = false);
    }
  }

  Future<void> _submitEnrollStudent() async {
    if (_enrollStudentId == null || _enrollGradeId == null) return;
    setState(() => _enrollingStudent = true);
    try {
      await GetIt.I<CurriculumApi>().enrollStudent(studentId: _enrollStudentId!, gradeId: _enrollGradeId!);
      _showMessage('Enrolled.');
      setState(() {
        _enrollStudentId = null;
        _enrollGradeId = null;
      });
    } catch (e) {
      _showMessage('Could not enroll: $e');
    } finally {
      if (mounted) setState(() => _enrollingStudent = false);
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
      appBar: AppBar(leading: forceShellLeading(context), title: const Text('School Admin')),
      body: FutureBuilder<_AdminData>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Loading school roster…');
          }
          if (snap.hasError) {
            return ErrorDisplay(
              message: 'Could not load the school roster. Check your connection.',
              onRetry: () => setState(() => _future = _load()),
            );
          }
          final data = snap.data!;
          if (data.grades.isEmpty) {
            return const EmptyState(
              icon: Icons.school_outlined,
              title: 'No curriculum yet',
              message: 'Seed the curriculum for this school before assigning teachers or students.',
            );
          }
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
                          : const Text('Assign'),
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
                          : const Text('Enroll'),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
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
  final List<GradeSummary> grades;
  final List<AuthUser> teachers;
  final List<AuthUser> students;
  const _AdminData({required this.grades, required this.teachers, required this.students});
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
