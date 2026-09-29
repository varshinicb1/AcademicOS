import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../../core/constants/release_scope.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';
import 'terms_card.dart';

/// A new school's first step on the web: its academic year and the CBSE
/// classes this release serves, with their subjects, books and chapters, and
/// how many sections each class has (M1.1; 1 gives each class section A).
///
/// The admin console opened on "No curriculum yet. Seed the curriculum ..."
/// and nothing on the web could seed it -- only the API could (audit D27), so
/// a school onboarded the documented way had no classes, no calendar and no
/// term. This runs the same idempotent seed the API offers
/// (POST /curriculum/seed/cbse), one class at a time: a class that fails can
/// be retried and the ones already set up are reused, not duplicated.
class SchoolSetupCard extends StatefulWidget {
  final CurriculumApi api;

  /// The school's year, when one exists without classes: its label and dates
  /// are reused so the seed adds classes to it rather than a second year.
  final AcademicYearSummary? year;
  final VoidCallback onDone;

  /// Today, for the default year; a test passes a fixed date.
  final DateTime? today;

  const SchoolSetupCard({super.key, required this.api, required this.onDone, this.year, this.today});

  /// The CBSE session containing [today]: 1 April to 31 March, labelled
  /// "2026-27".
  static (String, String, String) sessionFor(DateTime today) {
    final first = today.month >= 4 ? today.year : today.year - 1;
    final label = '$first-${((first + 1) % 100).toString().padLeft(2, '0')}';
    return (label, '$first-04-01', '${first + 1}-03-31');
  }

  static const maxSectionsPerClass = 10;

  /// The sections a class set up with [count] sections has: A, B, C, ...
  static List<String> sectionNames(int count) =>
      [for (var i = 0; i < count; i++) String.fromCharCode('A'.codeUnitAt(0) + i)];

  @override
  State<SchoolSetupCard> createState() => _SchoolSetupCardState();
}

class _SchoolSetupCardState extends State<SchoolSetupCard> {
  late final TextEditingController _label;
  late final TextEditingController _start;
  late final TextEditingController _end;
  final _sections = TextEditingController(text: '1');
  // The name printed at the top of every paper (EX-5, audit D41).
  final _schoolName = TextEditingController();
  bool _busy = false;
  String? _progress;
  String? _error;
  final List<String> _done = [];

  @override
  void initState() {
    super.initState();
    final y = widget.year;
    final (label, start, end) = SchoolSetupCard.sessionFor(widget.today ?? DateTime.now());
    _label = TextEditingController(text: y?.label.isNotEmpty == true ? y!.label : label);
    _start = TextEditingController(text: y?.startDate ?? start);
    _end = TextEditingController(text: y?.endDate ?? end);
  }

  @override
  void dispose() {
    _label.dispose();
    _start.dispose();
    _end.dispose();
    _sections.dispose();
    _schoolName.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    final label = _label.text.trim(), start = _start.text.trim(), end = _end.text.trim();
    final s = DateTime.tryParse(start), e = DateTime.tryParse(end);
    if (label.isEmpty || s == null || e == null || start.length != 10 || end.length != 10) {
      setState(() => _error = 'Give the year a name and its first and last day as YYYY-MM-DD.');
      return;
    }
    if (!e.isAfter(s)) {
      setState(() => _error = 'The year ends before it starts.');
      return;
    }
    final perClass = int.tryParse(_sections.text.trim());
    if (perClass == null || perClass < 1 || perClass > SchoolSetupCard.maxSectionsPerClass) {
      setState(() => _error = 'Sections per class is a whole number from 1 to ${SchoolSetupCard.maxSectionsPerClass}.');
      return;
    }
    final wanted = SchoolSetupCard.sectionNames(perClass);
    final schoolName = _schoolName.text.trim();
    setState(() {
      _busy = true;
      _error = null;
      _done.clear();
    });
    if (schoolName.isNotEmpty) {
      try {
        await widget.api.setSchoolName(schoolName);
      } catch (err) {
        if (!mounted) return;
        setState(() {
          _busy = false;
          _error = 'The school\'s name was not saved: ${serverErrorMessage(err)} Nothing else was set up yet.';
        });
        return;
      }
    }
    for (final (i, grade) in releaseGrades.indexed) {
      setState(() => _progress = 'Setting up Class $grade (${i + 1} of ${releaseGrades.length})...');
      try {
        final r = await widget.api.seedCbseClass(grade: grade, yearLabel: label, startDate: start, endDate: end);
        if (perClass > 1) {
          // A class is seeded with section A. The rest are added unless the
          // class has them already, so pressing again after a failure adds
          // only what is missing. Read after this class's seed, which is what
          // made its A.
          final existing = await widget.api.sections(r.academicYearId);
          final have = {
            for (final sec in existing.where((sec) => sec.gradeId == r.gradeId)) sec.name.toUpperCase()
          };
          for (final name in wanted.where((n) => !have.contains(n))) {
            await widget.api.createSection(r.gradeId, name: name);
          }
        }
        _done.add('Class $grade: ${r.subjectsSeeded} subjects, ${r.chaptersSeeded} chapters'
            '${perClass > 1 ? ', sections ${wanted.first}-${wanted.last}' : ''}');
      } catch (err) {
        if (!mounted) return;
        setState(() {
          _busy = false;
          _progress = null;
          _error = 'Class $grade was not set up: ${serverErrorMessage(err)} '
              '${_done.isEmpty ? '' : 'The classes before it are set up; '}Press the button again to continue.';
        });
        return;
      }
    }
    if (!mounted) return;
    setState(() {
      _busy = false;
      _progress = null;
    });
    widget.onDone();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    final classes = '${releaseGrades.first} to ${releaseGrades.last}';
    return AppCard(
      key: const ValueKey('school-setup-card'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Set up your school year', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(4),
          Text(
            'Creates the academic year and CBSE classes $classes with their subjects, books, '
            'chapters and sections. Then add your calendar rules and terms on Calendar & Setup, and '
            'choose each subject\'s book edition and each section\'s class teacher on Roster.',
            style: muted,
          ),
          const Gap(12),
          TextField(
            key: const ValueKey('setup-school-name'),
            controller: _schoolName,
            enabled: !_busy,
            decoration: const InputDecoration(
              labelText: 'School name',
              hintText: 'Sunrise Public School',
              helperText: 'Printed at the top of every paper. You can change it later on the School tab.',
              border: OutlineInputBorder(),
            ),
          ),
          const Gap(12),
          TextField(
            key: const ValueKey('setup-label'),
            controller: _label,
            enabled: !_busy,
            decoration: const InputDecoration(labelText: 'Academic year', hintText: '2026-27', border: OutlineInputBorder()),
          ),
          const Gap(12),
          TextField(
            key: const ValueKey('setup-start'),
            controller: _start,
            enabled: !_busy,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(labelText: 'First day', hintText: 'YYYY-MM-DD', border: OutlineInputBorder()),
          ),
          const Gap(12),
          TextField(
            key: const ValueKey('setup-end'),
            controller: _end,
            enabled: !_busy,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(labelText: 'Last day', hintText: 'YYYY-MM-DD', border: OutlineInputBorder()),
          ),
          if (_start.text.isNotEmpty && _end.text.isNotEmpty) ...[
            const Gap(4),
            Text('${TermsCard.readable(_start.text.trim())} to ${TermsCard.readable(_end.text.trim())}', style: muted),
          ],
          const Gap(12),
          TextField(
            key: const ValueKey('setup-sections'),
            controller: _sections,
            enabled: !_busy,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Sections per class',
              helperText: '1 gives each class section A; 3 gives A, B and C. You can add more later.',
              border: OutlineInputBorder(),
            ),
          ),
          if (_progress != null) ...[
            const Gap(12),
            Text(_progress!, key: const ValueKey('setup-progress')),
            const Gap(4),
            const LinearProgressIndicator(),
          ],
          for (final line in _done) Text(line, style: muted),
          if (_error != null) ...[
            const Gap(8),
            Text(_error!, key: const ValueKey('setup-error'), style: TextStyle(color: theme.colorScheme.error)),
          ],
          const Gap(12),
          FilledButton.icon(
            key: const ValueKey('setup-run'),
            onPressed: _busy ? null : _run,
            style: phoneTapTarget(context),
            icon: const Icon(Icons.school_outlined),
            label: Text('Set up classes $classes'),
          ),
        ],
      ),
    );
  }
}
