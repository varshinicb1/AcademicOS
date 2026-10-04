import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/session/current_session.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import '../../workspace/notice.dart';
import '../../workspace/ops_api.dart';
import '../../workspace/strings.dart';
import '../setup_wizard_logic.dart';

/// "Set up your school": one guided flow that captures what a school needs
/// before its first paper and configures it as it goes, instead of five
/// screens the principal has to find. Each step saves when it is continued, so
/// closing the browser loses nothing and the wizard reopens where it stopped.
///
/// The steps: the school's identity (what every paper prints), its classes and
/// sections, its year, calendar, terms and bell, its teachers, each subject's
/// weekly periods, and last a real first paper. A teacher can only be given a
/// subject once they have accepted the invite, so that step sets the periods
/// now and the teacher where one has already joined; the rest is finished
/// from the timetable page as each teacher joins.
class SetupWizardPage extends StatefulWidget {
  /// Today, for the default school year; a test passes a fixed date.
  final DateTime? today;

  /// Picks the logo image; a test passes one that returns bytes directly.
  final Future<(Uint8List, String, String)?> Function()? pickLogo;

  const SetupWizardPage({super.key, this.today, this.pickLogo});

  @override
  State<SetupWizardPage> createState() => _SetupWizardPageState();
}

enum _Step { welcome, school, classes, calendar, teachers, subjects, paper, done }

const _stepTitles = {
  _Step.welcome: 'Welcome',
  _Step.school: 'Your school',
  _Step.classes: 'Classes and sections',
  _Step.calendar: 'Year, terms and bell',
  _Step.teachers: 'Teachers',
  _Step.subjects: 'Subjects and periods',
  _Step.paper: 'Your first paper',
  _Step.done: 'All set',
};

class _ClassInfo {
  final int grade;
  final String gradeId;
  final List<String> sections;
  List<Map<String, dynamic>> subjects = [];
  _ClassInfo(this.grade, this.gradeId, this.sections);
}

class _SubjectLoad {
  final int grade;
  final String subject;
  String? teacherEmail;
  int periods;
  _SubjectLoad(this.grade, this.subject, this.periods);
}

class _SetupWizardPageState extends State<SetupWizardPage> {
  _Step _step = _Step.welcome;
  final _scroll = ScrollController();
  bool _busy = false;
  bool _loading = true;
  String? _error;
  String? _loadError;
  bool _wasComplete = false;

  // school
  final _name = TextEditingController();
  final _address = TextEditingController();
  final _affiliation = TextEditingController();
  Uint8List? _logoPreview;
  bool _hasLogo = false;

  // classes
  final Map<int, int> _sections = {for (final g in wizardDefaultGrades) g: 1};

  // calendar
  late CalendarDraft _calendar;
  late final TextEditingController _yearStart, _yearEnd, _bellStart;
  final List<TextEditingController> _termName = [], _termStart = [], _termEnd = [];

  // set up (from the server)
  String? _yearId;
  List<_ClassInfo> _classes = [];
  List<String> _setupNotes = [];

  // teachers
  final List<(TextEditingController, TextEditingController)> _teacherRows = [];
  List<String> _inviteLines = [];
  List<Map<String, dynamic>> _staff = [];

  // subjects
  final List<_SubjectLoad> _loads = [];

  // paper
  int _paperGrade = 10;
  String _paperSubject = 'Mathematics';
  String? _paperAssessmentId;
  String? _paperSummary;
  List<String> _paperWarnings = [];

  @override
  void initState() {
    super.initState();
    final y = schoolYearFor(widget.today ?? DateTime.now());
    _calendar = CalendarDraft(start: y.start, end: y.end);
    _yearStart = TextEditingController(text: _calendar.start);
    _yearEnd = TextEditingController(text: _calendar.end);
    _bellStart = TextEditingController(text: _calendar.bell.startsAt);
    _syncTermControllers();
    _addTeacherRow();
    _resume();
  }

  @override
  void dispose() {
    _scroll.dispose();
    for (final c in [_name, _address, _affiliation, _yearStart, _yearEnd, _bellStart]) {
      c.dispose();
    }
    for (final c in [..._termName, ..._termStart, ..._termEnd]) {
      c.dispose();
    }
    for (final (a, b) in _teacherRows) {
      a.dispose();
      b.dispose();
    }
    super.dispose();
  }

  void _syncTermControllers() {
    for (final c in [..._termName, ..._termStart, ..._termEnd]) {
      c.dispose();
    }
    _termName.clear();
    _termStart.clear();
    _termEnd.clear();
    for (final t in _calendar.terms) {
      _termName.add(TextEditingController(text: t.name));
      _termStart.add(TextEditingController(text: t.start));
      _termEnd.add(TextEditingController(text: t.end));
    }
  }

  void _addTeacherRow() => _teacherRows.add((TextEditingController(), TextEditingController()));

  /// Reopen where the principal stopped: a saved name skips the school step,
  /// existing classes skip the class and calendar steps.
  Future<void> _resume() async {
    try {
      final profile = await Ops.map('/curriculum/school-profile');
      _name.text = profile['name'] as String? ?? '';
      _address.text = profile['address'] as String? ?? '';
      _affiliation.text = profile['affiliation'] as String? ?? '';
      _hasLogo = profile['hasLogo'] == true;
      final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
      if (years.isNotEmpty) {
        years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
        _yearId = years.last['id'] as String;
        await _loadClasses();
      }
      _staff = await Ops.list('/staff');
      // A school whose checklist is complete is told so, not taken back through the teachers step.
      // The checklist is a courtesy here: if it cannot be read the wizard resumes as before.
      var complete = false;
      try {
        final status = await Ops.map('/setup-status');
        final steps = (status['steps'] as List?) ?? const [];
        complete = steps.isNotEmpty && steps.every((x) => (x as Map)['done'] == true);
      } catch (_) {
        // not-a-failure: the checklist only decides whether to open on "ready"; the steps themselves report their own failures.
      }
      if (!mounted) return;
      setState(() {
        _loading = false;
        _wasComplete = complete;
        if (complete && _classes.isNotEmpty) {
          _step = _Step.done;
        } else if (_classes.isNotEmpty) {
          _step = _Step.teachers;
        } else if (_name.text.trim().isNotEmpty) {
          _step = _Step.classes;
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _loadError = serverErrorMessage(e);
      });
    }
  }

  Future<void> _loadClasses() async {
    final id = _yearId;
    if (id == null) return;
    final grades = await Ops.list('/curriculum/academic-years/$id/grades');
    final sections = await Ops.list('/curriculum/academic-years/$id/sections');
    final out = <_ClassInfo>[];
    for (final g in grades) {
      final number = g['number'] as int;
      final names = [
        for (final s in sections)
          if (s['gradeId'] == g['id']) s['name'] as String,
      ]..sort();
      final info = _ClassInfo(number, g['id'] as String, names);
      info.subjects = await Ops.list('/curriculum/grades/${g['id']}/subjects');
      out.add(info);
    }
    out.sort((a, b) => a.grade.compareTo(b.grade));
    _classes = out;
    _paperGrade = out.any((c) => c.grade == 10) ? 10 : (out.isEmpty ? 10 : out.last.grade);
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
    } catch (e) {
      _fail(serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Shows [message] above the step and scrolls to it: the person pressed the
  /// button at the bottom of a long step and the refusal is at the top.
  void _fail(String message) {
    if (!mounted) return;
    setState(() => _error = message);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) _scroll.jumpTo(0);
    });
  }

  void _go(_Step step) {
    setState(() {
      _step = step;
      _error = null;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) _scroll.jumpTo(0);
    });
  }

  _Step get _previous => _Step.values[(_step.index - 1).clamp(0, _Step.values.length - 1)];

  // ------------------------------------------------------------------ steps

  Future<void> _saveSchool() => _run(() async {
        final name = _name.text.trim();
        if (name.isEmpty) throw StateError('Your school needs a name: it is printed on every paper.');
        await Ops.put('/curriculum/school-profile', body: {
          'name': name,
          'address': _address.text.trim().isEmpty ? null : _address.text.trim(),
          'affiliation': _affiliation.text.trim().isEmpty ? null : _affiliation.text.trim(),
        });
        _go(_Step.classes);
      });

  Future<void> _pickLogo() => _run(() async {
        final picked = await (widget.pickLogo ?? _defaultPick)();
        if (picked == null) return;
        final (bytes, name, mime) = picked;
        final parts = mime.split('/');
        if (_name.text.trim().isNotEmpty) {
          await Ops.put('/curriculum/school-profile', body: {
            'name': _name.text.trim(),
            'address': _address.text.trim().isEmpty ? null : _address.text.trim(),
            'affiliation': _affiliation.text.trim().isEmpty ? null : _affiliation.text.trim(),
          });
        } else {
          throw StateError('Type the school name first; the logo is saved with it.');
        }
        await Ops.post('/curriculum/school-profile/logo', body: FormData.fromMap({
          'file': MultipartFile.fromBytes(bytes, filename: name,
              contentType: DioMediaType(parts.first, parts.length > 1 ? parts[1] : 'png')),
        }));
        if (mounted) setState(() { _logoPreview = bytes; _hasLogo = true; });
      });

  static Future<(Uint8List, String, String)?> _defaultPick() async {
    final file = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 800);
    if (file == null) return null;
    final bytes = await file.readAsBytes();
    final lower = file.name.toLowerCase();
    return (bytes, file.name, lower.endsWith('.jpg') || lower.endsWith('.jpeg') ? 'image/jpeg' : 'image/png');
  }

  void _readCalendarFields() {
    _calendar
      ..start = _yearStart.text.trim()
      ..end = _yearEnd.text.trim();
    _calendar.bell.startsAt = _bellStart.text.trim();
    for (var i = 0; i < _calendar.terms.length; i++) {
      _calendar.terms[i]
        ..name = _termName[i].text.trim().isEmpty ? 'Term ${i + 1}' : _termName[i].text.trim()
        ..start = _termStart[i].text.trim()
        ..end = _termEnd[i].text.trim();
    }
  }

  Future<void> _setUp() => _run(() async {
        _readCalendarFields();
        final problems = calendarProblems(_calendar);
        if (problems.isNotEmpty) throw StateError(problems.join(' '));
        final r = await Ops.post('/curriculum/school-setup',
            body: schoolSetupBody(sectionsByGrade: _sections, calendar: _calendar)) as Map;
        _yearId = (r['academicYear'] as Map)['id'] as String;
        _setupNotes = [
          for (final k in ['created', 'alreadyExisted', 'skipped']) ...[for (final l in (r[k] as List? ?? [])) '$l'],
        ];
        await _loadClasses();
        _staff = await Ops.list('/staff');
        _go(_Step.teachers);
      });

  List<TeacherRow> get _teacherInput =>
      [for (final (n, e) in _teacherRows) (name: n.text, email: e.text)];

  Future<void> _inviteTeachers() => _run(() async {
        final rows = _teacherInput;
        final problems = teacherRowProblems(rows);
        if (problems.isNotEmpty) {
          throw StateError(problems.entries.map((e) => 'Row ${e.key} ${e.value}.').join(' '));
        }
        final csv = teachersCsv(rows);
        if (csv.split('\n').length > 1) {
          final plan = await Ops.post('/admin/import/teachers',
              body: {'csv': csv, 'academicYearId': _yearId}, query: {'dryRun': 'false'}) as Map;
          _inviteLines = [
            for (final row in (plan['rows'] as List))
              if ((row as Map)['status'] == 'ok')
                '${row['message']}${row['inviteCode'] != null ? ' - code ${row['inviteCode']}' : ''}'
              else
                '${row['message']}',
          ];
        }
        _staff = await Ops.list('/staff');
        _prepareLoads();
        _go(_Step.subjects);
      });

  void _prepareLoads() {
    final kept = {for (final l in _loads) '${l.grade}|${l.subject}': l};
    _loads.clear();
    for (final c in _classes) {
      for (final s in c.subjects) {
        final subject = s['name'] as String;
        _loads.add(kept['${c.grade}|$subject'] ?? _SubjectLoad(c.grade, subject, defaultPeriodsPerWeek(subject)));
      }
    }
  }

  List<Map<String, dynamic>> get _joinedTeachers =>
      _staff.where((s) => s['role'] == 'teacher' && (s['email'] as String? ?? '').isNotEmpty).toList();

  Future<void> _saveSubjects() => _run(() async {
        final rows = [
          for (final l in _loads)
            (grade: l.grade, subject: l.subject, teacherEmail: l.teacherEmail, periods: l.periods),
        ];
        final csv = allocationsCsv(rows, {for (final c in _classes) c.grade: c.sections});
        if (rows.isNotEmpty) {
          await Ops.post('/admin/import/allocations',
              body: {'csv': csv, 'academicYearId': _yearId}, query: {'dryRun': 'false'});
        }
        _go(_Step.paper);
      });

  Future<void> _firstPaper() => _run(() async {
        final r = await Ops.post('/papers/quick-generate', body: {
          'subject': _paperSubject,
          'grade': _paperGrade,
          'totalMarks': 80,
          'title': '$_paperSubject, Class $_paperGrade: first paper',
        }) as Map;
        final warnings = [for (final w in (r['warnings'] as List? ?? [])) '$w'];
        setState(() {
          _paperAssessmentId = r['assessmentId'] as String?;
          _paperWarnings = warnings;
          _paperSummary = '${r['totalMarks'] ?? 80} marks';
        });
      });

  // ------------------------------------------------------------------ build

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Set up your school'))),
      body: _loading
          ? const LoadingIndicator()
          : _loadError != null
              ? ErrorDisplay(message: _loadError!, onRetry: () {
                  setState(() {
                    _loading = true;
                    _loadError = null;
                  });
                  _resume();
                })
              : Column(children: [
                  _progress(theme),
                  Expanded(
                    child: ListView(
                      key: ValueKey('wizard-step-${_step.name}'),
                      controller: _scroll,
                      padding: const EdgeInsets.all(16),
                      children: [
                        Text(tr(_stepTitles[_step]!), style: theme.textTheme.titleLarge),
                        const Gap(12),
                        // Above the step, not below it: on a long step the
                        // refusal would sit off-screen under the fields.
                        if (_error != null) ...[
                          Notice(key: const ValueKey('wizard-error'), kind: NoticeKind.danger,
                              title: tr('That did not go through'), lines: [_error!.replaceFirst('Bad state: ', '')]),
                          const Gap(12),
                        ],
                        ..._body(theme),
                      ],
                    ),
                  ),
                  _footer(),
                ]),
    );
  }

  Widget _progress(ThemeData theme) {
    final shown = _step.index.clamp(1, 6);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        LinearProgressIndicator(
            key: const ValueKey('wizard-progress'),
            value: _step == _Step.welcome ? 0 : (_step == _Step.done ? 1 : shown / 6)),
        const Gap(4),
        if (_step != _Step.welcome && _step != _Step.done)
          Text('${tr('Step')} $shown ${tr('of')} 6', style: theme.textTheme.bodySmall),
      ]),
    );
  }

  Widget _footer() {
    final first = _step == _Step.welcome;
    final last = _step == _Step.done;
    final skip = switch (_step) {
      _Step.teachers => (label: 'Add teachers later', go: _Step.subjects),
      _Step.paper => (label: 'Skip the paper', go: _Step.done),
      _ => null,
    };
    // The main action is a full-width button, with Back and the skip link on a
    // row beneath it: three buttons side by side do not fit a 375 px phone.
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              key: const ValueKey('wizard-next'),
              style: phoneTapTarget(context),
              onPressed: _busy ? null : _onNext,
              child: _busy
                  ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(tr(_nextLabel)),
            ),
          ),
          if (!first && !last || skip != null)
            Row(children: [
              if (!first && !last && _step != _Step.paper)
                TextButton(key: const ValueKey('wizard-back'),
                    onPressed: _busy ? null : () => _go(_previous), style: phoneTapTarget(context),
                    child: Text(tr('Back'))),
              const Spacer(),
              if (skip != null)
                TextButton(key: const ValueKey('wizard-skip'),
                    onPressed: _busy
                        ? null
                        : () {
                            if (_step == _Step.teachers) _prepareLoads();
                            _go(skip.go);
                          },
                    style: phoneTapTarget(context), child: Text(tr(skip.label))),
            ]),
        ]),
      ),
    );
  }

  String get _nextLabel => switch (_step) {
        _Step.welcome => "Let's begin",
        _Step.school => 'Save and continue',
        _Step.classes => 'Continue',
        _Step.calendar => 'Set up my school',
        _Step.teachers => 'Send invites and continue',
        _Step.subjects => 'Save and continue',
        _Step.paper => _paperAssessmentId == null ? 'Make my first paper' : 'Finish',
        _Step.done => 'Go to my school',
      };

  void _onNext() {
    switch (_step) {
      case _Step.welcome:
        _go(_Step.school);
      case _Step.school:
        _saveSchool();
      case _Step.classes:
        if (_sections.isEmpty) {
          _fail('Choose at least one class.');
        } else {
          _go(_Step.calendar);
        }
      case _Step.calendar:
        _setUp();
      case _Step.teachers:
        _inviteTeachers();
      case _Step.subjects:
        _saveSubjects();
      case _Step.paper:
        if (_paperAssessmentId == null) {
          _firstPaper();
        } else {
          _go(_Step.done);
        }
      case _Step.done:
        context.go('/school');
    }
  }

  List<Widget> _body(ThemeData theme) => switch (_step) {
        _Step.welcome => _welcome(theme),
        _Step.school => _school(theme),
        _Step.classes => _classesStep(theme),
        _Step.calendar => _calendarStep(theme),
        _Step.teachers => _teachersStep(theme),
        _Step.subjects => _subjectsStep(theme),
        _Step.paper => _paperStep(theme),
        _Step.done => _doneStep(theme),
      };

  List<Widget> _welcome(ThemeData theme) => [
        Text(tr('About ten minutes, and your school will be ready to make question papers for classes 9 and 10.'),
            style: theme.textTheme.bodyLarge),
        const Gap(12),
        for (final line in const [
          'Your school name and logo, as they print on papers',
          'The classes and sections you teach',
          'The year, terms, weekly off days and the bell',
          'Your teachers, invited by email',
          'The periods each subject gets each week',
          'A first real paper, made from the question bank',
        ])
          ListTile(dense: true, contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.check_circle_outline), title: Text(tr(line))),
        const Gap(8),
        Text(tr('Everything saves as you go. You can stop and come back, and change any of it later.'),
            style: theme.textTheme.bodySmall),
      ];

  List<Widget> _school(ThemeData theme) => [
        Text(tr('Printed at the top of every paper, answer key and report.'), style: theme.textTheme.bodySmall),
        const Gap(12),
        TextField(key: const ValueKey('wizard-name'), controller: _name, maxLength: 120,
            decoration: InputDecoration(labelText: tr('School name'), hintText: 'Sunrise Public School')),
        const Gap(8),
        TextField(key: const ValueKey('wizard-address'), controller: _address, maxLength: 200,
            decoration: InputDecoration(labelText: tr('Address (optional)'))),
        const Gap(8),
        TextField(key: const ValueKey('wizard-affiliation'), controller: _affiliation, maxLength: 120,
            decoration: InputDecoration(
                labelText: tr('Affiliation line (optional)'), hintText: 'CBSE Affiliation No. 1234567')),
        const Gap(12),
        Row(children: [
          if (_logoPreview != null)
            Image.memory(_logoPreview!, key: const ValueKey('wizard-logo'), height: 56)
          else
            const Icon(Icons.image_outlined, size: 40),
          const Gap(12),
          Expanded(
            child: FilledButton.tonalIcon(
              key: const ValueKey('wizard-logo-upload'),
              onPressed: _busy ? null : _pickLogo,
              style: phoneTapTarget(context),
              icon: const Icon(Icons.upload_outlined),
              label: Text(_hasLogo ? tr('Change the logo') : tr('Add a logo (optional)')),
            ),
          ),
        ]),
      ];

  List<Widget> _classesStep(ThemeData theme) => [
        Text(tr('Which classes does your school have, and how many sections in each?'),
            style: theme.textTheme.bodyMedium),
        const Gap(4),
        Text(tr('Classes 9 and 10 are chosen for you. Each class comes with its CBSE subjects, books and chapters.'),
            style: theme.textTheme.bodySmall),
        const Gap(12),
        for (final g in wizardGrades)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(children: [
              Expanded(
                child: CheckboxListTile(
                  key: ValueKey('wizard-class-$g'),
                  contentPadding: EdgeInsets.zero,
                  value: _sections.containsKey(g),
                  title: Text('${tr('Class')} $g'),
                  onChanged: (on) => setState(() {
                    if (on == true) {
                      _sections[g] = 1;
                    } else {
                      _sections.remove(g);
                    }
                  }),
                ),
              ),
              if (_sections.containsKey(g)) ...[
                IconButton(
                  key: ValueKey('wizard-sections-less-$g'),
                  tooltip: tr('Fewer sections'),
                  onPressed: _sections[g]! > 1 ? () => setState(() => _sections[g] = _sections[g]! - 1) : null,
                  icon: const Icon(Icons.remove_circle_outline),
                ),
                SizedBox(
                  width: 96,
                  child: Text(sectionNames(_sections[g]!).join(', '),
                      key: ValueKey('wizard-sections-$g'), textAlign: TextAlign.center),
                ),
                IconButton(
                  key: ValueKey('wizard-sections-more-$g'),
                  tooltip: tr('More sections'),
                  onPressed: _sections[g]! < maxSectionsPerClass
                      ? () => setState(() => _sections[g] = _sections[g]! + 1)
                      : null,
                  icon: const Icon(Icons.add_circle_outline),
                ),
              ],
            ]),
          ),
      ];

  static const _days = [
    ('monday', 'Mon'), ('tuesday', 'Tue'), ('wednesday', 'Wed'), ('thursday', 'Thu'),
    ('friday', 'Fri'), ('saturday', 'Sat'), ('sunday', 'Sun'),
  ];

  Widget _dateField(String key, TextEditingController c, String label) => TextField(
        key: ValueKey(key),
        controller: c,
        keyboardType: TextInputType.datetime,
        decoration: InputDecoration(labelText: tr(label), hintText: 'YYYY-MM-DD'),
      );

  List<Widget> _calendarStep(ThemeData theme) => [
        Text(tr('These are the usual CBSE settings. Change only what is different at your school.'),
            style: theme.textTheme.bodySmall),
        const Gap(12),
        Text(tr('School year'), style: theme.textTheme.titleSmall),
        const Gap(4),
        Row(children: [
          Expanded(child: _dateField('wizard-year-start', _yearStart, 'First day')),
          const Gap(8),
          Expanded(child: _dateField('wizard-year-end', _yearEnd, 'Last day')),
        ]),
        const Gap(16),
        Text(tr('Weekly off days'), style: theme.textTheme.titleSmall),
        Wrap(spacing: 6, children: [
          for (final (id, label) in _days)
            FilterChip(
              key: ValueKey('wizard-off-$id'),
              label: Text(tr(label)),
              selected: _calendar.weeklyOff.contains(id),
              onSelected: (on) => setState(() => on ? _calendar.weeklyOff.add(id) : _calendar.weeklyOff.remove(id)),
            ),
        ]),
        SwitchListTile(
          key: const ValueKey('wizard-saturdays'),
          contentPadding: EdgeInsets.zero,
          title: Text(tr('Second and fourth Saturdays are off')),
          value: _calendar.secondFourthSaturdays,
          onChanged: (v) => setState(() => _calendar.secondFourthSaturdays = v),
        ),
        const Gap(8),
        Text(tr('Terms'), style: theme.textTheme.titleSmall),
        for (var i = 0; i < _calendar.terms.length; i++) ...[
          const Gap(4),
          Row(children: [
            Expanded(flex: 3, child: TextField(key: ValueKey('wizard-term-name-$i'), controller: _termName[i],
                decoration: InputDecoration(labelText: tr('Name')))),
            const Gap(8),
            Expanded(flex: 4, child: _dateField('wizard-term-start-$i', _termStart[i], 'Starts')),
            const Gap(8),
            Expanded(flex: 4, child: _dateField('wizard-term-end-$i', _termEnd[i], 'Ends')),
          ]),
        ],
        const Gap(16),
        Text(tr('Bell'), style: theme.textTheme.titleSmall),
        const Gap(4),
        Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          _stepper('wizard-periods', 'Periods a day', _calendar.bell.periods, 1, 12,
              (v) => _calendar.bell.periods = v),
          _stepper('wizard-minutes', 'Minutes each', _calendar.bell.periodMinutes, 20, 90,
              (v) => _calendar.bell.periodMinutes = v, step: 5),
          SizedBox(width: 130, child: TextField(key: const ValueKey('wizard-bell-start'), controller: _bellStart,
              decoration: InputDecoration(labelText: tr('First bell'), hintText: '08:00'))),
          _stepper('wizard-break-after', 'Break after period', _calendar.bell.breakAfterPeriod, 0, 12,
              (v) => _calendar.bell.breakAfterPeriod = v),
        ]),
      ];

  Widget _stepper(String key, String label, int value, int min, int max, void Function(int) set, {int step = 1}) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Text('${tr(label)}: '),
      IconButton(key: ValueKey('$key-less'), tooltip: '${tr('Fewer')}: ${tr(label)}',
          onPressed: value - step >= min ? () => setState(() => set(value - step)) : null,
          icon: const Icon(Icons.remove_circle_outline)),
      Text('$value', key: ValueKey(key)),
      IconButton(key: ValueKey('$key-more'), tooltip: '${tr('More')}: ${tr(label)}',
          onPressed: value + step <= max ? () => setState(() => set(value + step)) : null,
          icon: const Icon(Icons.add_circle_outline)),
    ]);
  }

  List<Widget> _teachersStep(ThemeData theme) => [
        if (_setupNotes.isNotEmpty)
          Notice(key: const ValueKey('wizard-setup-result'), kind: NoticeKind.success,
              title: tr('Your school is set up'),
              lines: [
                for (final c in _classes)
                  '${tr('Class')} ${c.grade}: ${c.sections.length} ${tr('section(s)')}, ${c.subjects.length} ${tr('subjects')}',
              ]),
        const Gap(12),
        Text(tr('Invite your teachers. Each gets an email-style code to join; you give subjects to them on the next step or later.'),
            style: theme.textTheme.bodyMedium),
        const Gap(8),
        for (var i = 0; i < _teacherRows.length; i++)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(children: [
              Expanded(child: TextField(key: ValueKey('wizard-teacher-name-$i'), controller: _teacherRows[i].$1,
                  decoration: InputDecoration(labelText: tr('Name')))),
              const Gap(8),
              Expanded(child: TextField(key: ValueKey('wizard-teacher-email-$i'), controller: _teacherRows[i].$2,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(labelText: tr('Email')))),
            ]),
          ),
        TextButton.icon(
          key: const ValueKey('wizard-add-teacher'),
          onPressed: () => setState(_addTeacherRow),
          icon: const Icon(Icons.person_add_alt),
          label: Text(tr('Add another teacher')),
        ),
        Text(tr('Have a long list? Use the import page after setup: it reads a spreadsheet.'),
            style: theme.textTheme.bodySmall),
        if (_inviteLines.isNotEmpty) ...[
          const Gap(12),
          Notice(kind: NoticeKind.info, title: tr('Invites'), lines: _inviteLines),
        ],
      ];

  List<Widget> _subjectsStep(ThemeData theme) {
    final teachers = _joinedTeachers;
    return [
      Text(tr('How many periods a week does each subject get? These shape the timetable.'),
          style: theme.textTheme.bodyMedium),
      const Gap(4),
      Text(
          teachers.isEmpty
              ? tr('No teacher has joined yet, so subjects are set without a teacher. Give each subject its teacher on the Timetable page once they join.')
              : tr('Choose a teacher where one has joined; the rest can be given later.'),
          key: const ValueKey('wizard-subjects-note'), style: theme.textTheme.bodySmall),
      const Gap(8),
      for (final c in _classes) ...[
        Text('${tr('Class')} ${c.grade}', style: theme.textTheme.titleSmall),
        for (final load in _loads.where((l) => l.grade == c.grade))
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(children: [
              Expanded(flex: 3, child: Text(load.subject)),
              if (teachers.isNotEmpty)
                Expanded(
                  flex: 4,
                  child: DropdownButtonFormField<String?>(
                    key: ValueKey('wizard-teacher-${load.grade}-${load.subject}'),
                    initialValue: load.teacherEmail,
                    isExpanded: true,
                    decoration: InputDecoration(labelText: tr('Teacher')),
                    items: [
                      DropdownMenuItem<String?>(value: null, child: Text(tr('Not yet'))),
                      for (final t in teachers)
                        DropdownMenuItem<String?>(
                            value: t['email'] as String, child: Text((t['name'] as String?) ?? t['email'] as String)),
                    ],
                    onChanged: (v) => setState(() => load.teacherEmail = v),
                  ),
                ),
              const Gap(8),
              IconButton(key: ValueKey('wizard-p-less-${load.grade}-${load.subject}'),
                  tooltip: '${tr('Fewer periods')}: ${load.subject}',
                  onPressed: load.periods > 1 ? () => setState(() => load.periods--) : null,
                  icon: const Icon(Icons.remove_circle_outline)),
              SizedBox(width: 24, child: Text('${load.periods}', textAlign: TextAlign.center,
                  key: ValueKey('wizard-p-${load.grade}-${load.subject}'))),
              IconButton(key: ValueKey('wizard-p-more-${load.grade}-${load.subject}'),
                  tooltip: '${tr('More periods')}: ${load.subject}',
                  onPressed: load.periods < 12 ? () => setState(() => load.periods++) : null,
                  icon: const Icon(Icons.add_circle_outline)),
            ]),
          ),
        const Gap(8),
      ],
    ];
  }

  List<Widget> _paperStep(ThemeData theme) {
    final grades = _classes.where((c) => c.grade >= 9).map((c) => c.grade).toList();
    final offered = grades.isEmpty ? const [9, 10] : grades;
    return [
      Text(tr('Make a real paper from the question bank, to see it end to end.'), style: theme.textTheme.bodyMedium),
      const Gap(12),
      Row(children: [
        Expanded(
          child: DropdownButtonFormField<int>(
            key: const ValueKey('wizard-paper-grade'),
            isExpanded: true,
            initialValue: offered.contains(_paperGrade) ? _paperGrade : offered.last,
            decoration: InputDecoration(labelText: tr('Class')),
            items: [for (final g in offered) DropdownMenuItem(value: g, child: Text('${tr('Class')} $g'))],
            onChanged: _paperAssessmentId != null ? null : (v) => setState(() => _paperGrade = v ?? _paperGrade),
          ),
        ),
        const Gap(12),
        Expanded(
          child: DropdownButtonFormField<String>(
            key: const ValueKey('wizard-paper-subject'),
            isExpanded: true,
            initialValue: _paperSubject,
            decoration: InputDecoration(labelText: tr('Subject')),
            items: [for (final s in coreSubjects) DropdownMenuItem(value: s, child: Text(tr(s)))],
            onChanged: _paperAssessmentId != null ? null : (v) => setState(() => _paperSubject = v ?? _paperSubject),
          ),
        ),
      ]),
      const Gap(12),
      if (_paperAssessmentId != null) ...[
        Notice(key: const ValueKey('wizard-paper-ready'), kind: NoticeKind.success,
            title: tr('Your first paper is ready'), lines: [if (_paperSummary != null) _paperSummary!]),
        if (_paperWarnings.isNotEmpty) ...[
          const Gap(8),
          Notice(kind: NoticeKind.warning, title: tr('Worth knowing'), lines: firstFew(_paperWarnings)),
        ],
        const Gap(8),
        FilledButton.tonal(
          key: const ValueKey('wizard-open-paper'),
          style: phoneTapTarget(context),
          onPressed: () => context.push('/assessment/$_paperAssessmentId'),
          child: Text(tr('Open the paper')),
        ),
      ] else
        Text(tr('If the bank holds too few questions for a subject, you will be told exactly which sections fall short.'),
            style: theme.textTheme.bodySmall),
    ];
  }

  List<Widget> _doneStep(ThemeData theme) => [
        Notice(kind: NoticeKind.success, title: tr('Your school is ready'), lines: [
          if (_name.text.trim().isNotEmpty) _name.text.trim(),
          for (final c in _classes) '${tr('Class')} ${c.grade}: ${c.sections.join(', ')}',
        ]),
        const Gap(12),
        Text(tr('Next, from the School page: give each subject its teacher on the Timetable page once teachers join, add students, and make papers from the Papers menu. The Guide in the menu walks through each.'),
            style: theme.textTheme.bodyMedium),
        const Gap(8),
        TextButton(
          key: const ValueKey('wizard-open-guide'),
          onPressed: () => context.go('/school/guide'),
          child: Text(tr('Open the Guide')),
        ),
        if (_wasComplete)
          TextButton(
            key: const ValueKey('wizard-review-steps'),
            onPressed: () => setState(() => _step = _Step.school),
            child: Text(tr('Change something')),
          ),
      ];
}
