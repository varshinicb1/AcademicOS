import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The "Sections" card on the principal's Roster tab (M1.1).
///
/// Until M1.1 a section was only a label on a grade, so a student was enrolled
/// in "Grade 10" and nothing could be listed or scheduled per section. Every
/// class now has at least one section ("10-A"); this card lists them with
/// their student counts and class teachers, and adds, renames and removes
/// them. The server is the one judge (a name the class already has, a section
/// that still has students, a class's last section) and its sentence is shown
/// as it comes.
class SectionsCard extends StatefulWidget {
  final CurriculumApi api;
  final String academicYearId;
  final List<GradeSummary> grades;

  /// Who can be named class teacher.
  final List<AuthUser> teachers;
  final void Function(String message) onMessage;

  /// Called with the year's sections each time they load, so the enroll form
  /// beside this card offers the same list.
  final void Function(List<SectionSummary> sections)? onLoaded;

  const SectionsCard({
    super.key,
    required this.api,
    required this.academicYearId,
    required this.grades,
    required this.teachers,
    required this.onMessage,
    this.onLoaded,
  });

  /// The first letter from A that none of [taken] uses, ignoring case; "A"
  /// when all 26 are taken (the server then says the name is in use).
  static String nextLetter(Iterable<String> taken) {
    final used = {for (final t in taken) t.trim().toUpperCase()};
    for (var c = 'A'.codeUnitAt(0); c <= 'Z'.codeUnitAt(0); c++) {
      final letter = String.fromCharCode(c);
      if (!used.contains(letter)) return letter;
    }
    return 'A';
  }

  @override
  State<SectionsCard> createState() => _SectionsCardState();
}

class _SectionsCardState extends State<SectionsCard> {
  List<SectionSummary>? _sections;
  String? _loadError;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(SectionsCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.academicYearId != widget.academicYearId) _load();
  }

  Future<void> _load() async {
    setState(() {
      _loadError = null;
      _sections = null;
    });
    try {
      final sections = await widget.api.sections(widget.academicYearId);
      if (!mounted) return;
      setState(() => _sections = sections);
      widget.onLoaded?.call(sections);
    } catch (e) {
      if (mounted) setState(() => _loadError = serverErrorMessage(e));
    }
  }

  String? _teacherName(String? id) {
    if (id == null) return null;
    return widget.teachers.where((t) => t.id == id).firstOrNull?.name ?? 'a staff member';
  }

  String _describe(SectionSummary s) {
    final students = switch (s.studentCount) {
      0 => 'No students yet',
      1 => '1 student',
      final n => '$n students',
    };
    final teacher = _teacherName(s.classTeacherId);
    return '$students · ${teacher == null ? 'No class teacher' : 'Class teacher: $teacher'}';
  }

  Future<void> _add(GradeSummary grade, List<SectionSummary> ofGrade) async {
    final saved = await showDialog<SectionSummary>(
      context: context,
      builder: (context) => _SectionDialog(
        title: 'New section in Class ${grade.number}',
        initialName: SectionsCard.nextLetter(ofGrade.map((s) => s.name)),
        teachers: widget.teachers,
        save: (name, teacherId, _) => widget.api.createSection(grade.id, name: name, classTeacherId: teacherId),
      ),
    );
    if (saved == null) return;
    widget.onMessage('Section ${saved.label} added.');
    await _load();
  }

  Future<void> _edit(SectionSummary s) async {
    final saved = await showDialog<SectionSummary>(
      context: context,
      builder: (context) => _SectionDialog(
        title: 'Edit ${s.label}',
        initialName: s.name,
        initialTeacherId: s.classTeacherId,
        teachers: widget.teachers,
        save: (name, teacherId, teacherChanged) => widget.api
            .updateSection(s.id, name: name, changeClassTeacher: teacherChanged, classTeacherId: teacherId),
      ),
    );
    if (saved == null) return;
    widget.onMessage('Section ${saved.label} saved.');
    await _load();
  }

  Future<void> _remove(SectionSummary s) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Remove ${s.label}?'),
        content: const Text('A section can be removed once no student is enrolled in it. '
            'A class keeps at least one section.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Keep')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Remove')),
        ],
      ),
    );
    if (ok != true) return;
    setState(() => _busy = true);
    try {
      await widget.api.deleteSection(s.id);
      widget.onMessage('Section ${s.label} removed.');
      await _load();
    } catch (e) {
      widget.onMessage('Could not remove ${s.label}: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    final sections = _sections;
    final grades = [...widget.grades]..sort((a, b) => a.number.compareTo(b.number));
    return AppCard(
      key: const ValueKey('sections-card'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Sections', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(4),
          Text('Each class has at least one section, and a student is enrolled in one. '
              'Name a class teacher for each.', style: muted),
          const Gap(12),
          if (_loadError != null) ...[
            Text('Could not load the sections: $_loadError', style: TextStyle(color: theme.colorScheme.error)),
            const Gap(8),
            OutlinedButton(onPressed: _load, style: phoneTapTarget(context), child: const Text('Retry')),
          ] else if (sections == null)
            const LinearProgressIndicator()
          else
            for (final grade in grades) ...[
              Text('Class ${grade.number}', style: theme.textTheme.labelLarge),
              for (final s in sections.where((s) => s.gradeId == grade.id))
                ListTile(
                  key: ValueKey('section-${s.id}'),
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.groups_outlined),
                  title: Text(s.label),
                  subtitle: Text(_describe(s)),
                  trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                    IconButton(
                      tooltip: 'Edit ${s.label}',
                      icon: const Icon(Icons.edit_outlined),
                      onPressed: _busy ? null : () => _edit(s),
                    ),
                    IconButton(
                      tooltip: 'Remove ${s.label}',
                      icon: const Icon(Icons.delete_outline),
                      onPressed: _busy ? null : () => _remove(s),
                    ),
                  ]),
                ),
              TextButton.icon(
                key: ValueKey('section-add-${grade.id}'),
                onPressed: _busy ? null : () => _add(grade, sections.where((s) => s.gradeId == grade.id).toList()),
                style: phoneTapTarget(context),
                icon: const Icon(Icons.add),
                label: Text('Add a section to Class ${grade.number}'),
              ),
              const Gap(8),
            ],
        ],
      ),
    );
  }
}

/// Adds or edits one section: its name and class teacher. Saves through
/// [save], saying whether the class teacher was changed, and stays open with
/// the server's sentence when it refuses.
class _SectionDialog extends StatefulWidget {
  final String title;
  final String initialName;
  final String? initialTeacherId;
  final List<AuthUser> teachers;
  final Future<SectionSummary> Function(String name, String? classTeacherId, bool classTeacherChanged) save;

  const _SectionDialog({
    required this.title,
    required this.initialName,
    required this.teachers,
    required this.save,
    this.initialTeacherId,
  });

  @override
  State<_SectionDialog> createState() => _SectionDialogState();
}

class _SectionDialogState extends State<_SectionDialog> {
  late final TextEditingController _name = TextEditingController(text: widget.initialName);
  late String? _teacherId = widget.initialTeacherId;

  /// A class teacher who is not in [widget.teachers] (the principal, say): kept
  /// as an option of its own, so opening the dialog never changes it.
  bool get _currentIsUnlisted =>
      widget.initialTeacherId != null && !widget.teachers.any((t) => t.id == widget.initialTeacherId);
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final name = _name.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Give the section a name, such as A or Rose.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final saved = await widget.save(name, _teacherId, _teacherId != widget.initialTeacherId);
      if (mounted) Navigator.pop(context, saved);
    } catch (e) {
      if (mounted) {
        setState(() {
          _saving = false;
          _error = serverErrorMessage(e);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AlertDialog(
      title: Text(widget.title),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            key: const ValueKey('section-name'),
            controller: _name,
            maxLength: 20,
            decoration: const InputDecoration(labelText: 'Section name', hintText: 'A'),
          ),
          const Gap(8),
          DropdownButtonFormField<String?>(
            key: const ValueKey('section-teacher'),
            initialValue: _teacherId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Class teacher'),
            items: [
              const DropdownMenuItem<String?>(value: null, child: Text('No class teacher')),
              if (_currentIsUnlisted)
                DropdownMenuItem<String?>(value: widget.initialTeacherId, child: const Text('Current class teacher')),
              for (final t in widget.teachers)
                DropdownMenuItem<String?>(value: t.id, child: Text(t.name, overflow: TextOverflow.ellipsis)),
            ],
            onChanged: _saving ? null : (v) => setState(() => _teacherId = v),
          ),
          if (_error != null) ...[
            const Gap(8),
            Text(_error!, key: const ValueKey('section-error'), style: TextStyle(color: theme.colorScheme.error)),
          ],
        ],
      ),
      actions: [
        TextButton(onPressed: _saving ? null : () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          key: const ValueKey('section-save'),
          onPressed: _saving ? null : _save,
          child: _saving
              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Save'),
        ),
      ],
    );
  }
}
