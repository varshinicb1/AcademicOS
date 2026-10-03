import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'notice.dart';
import 'ops_api.dart';
import 'strings.dart';
import '../shared/widgets/shell.dart';

const _base = '/curriculum';
const _dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const roomKinds = ['classroom', 'lab', 'hall', 'other'];

/// A bell typed as lines, one slot a line: "08:00-08:45" is a teaching
/// period, "11:00-11:20 break" (or assembly, zero) is not. Returns the slots
/// the bell-schedule route takes, or the sentence naming the line that is
/// not a slot. The server checks order and overlap; this only reads the text.
({List<Map<String, String>> slots, String? error}) parseBellSlots(String text) {
  final slots = <Map<String, String>>[];
  final line = RegExp(r'^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})(?:\s+(teaching|break|assembly|zero))?$');
  var n = 0;
  for (final raw in text.split('\n')) {
    final t = raw.trim();
    n++;
    if (t.isEmpty) continue;
    final m = line.firstMatch(t);
    if (m == null) {
      return (slots: const [], error: 'Line $n: write a slot as 08:00-08:45, or 11:00-11:20 break');
    }
    String hhmm(String v) => v.length == 4 ? '0$v' : v;
    slots.add({'start': hhmm(m.group(1)!), 'end': hhmm(m.group(2)!), 'kind': m.group(3) ?? 'teaching'});
  }
  if (slots.isEmpty) return (slots: const [], error: 'Add at least one slot, such as 08:00-08:45');
  return (slots: slots, error: null);
}

/// The same bell back as lines, for editing.
String bellSlotsText(List<dynamic> slots) => [
      for (final s in slots.cast<Map>())
        '${s['start']}-${s['end']}${s['kind'] == 'teaching' ? '' : ' ${s['kind']}'}'
    ].join('\n');

/// The school's timetable, set up in one place (REQUIREMENTS SCH-2/3,
/// ADM-1): who teaches what to which section (with a co-teacher, a lab and
/// double periods, SCH-8), the rooms and when a room is out of use, the
/// bell, the periods each teacher cannot teach, the generated week with its
/// changes shown before publishing, and each section's week -- edited by
/// hand, with periods locked against the next generation and every clash
/// the server finds listed (audit N-3-5). For the principal, and a teacher
/// given the timetable admin permission (M1.4).
class TimetableAdminPage extends StatefulWidget {
  const TimetableAdminPage({super.key});

  @override
  State<TimetableAdminPage> createState() => _TimetableAdminPageState();
}

class _SchoolData {
  final String yearId;
  final List<Map<String, dynamic>> sections;
  final List<Map<String, dynamic>> staff;
  const _SchoolData(this.yearId, this.sections, this.staff);

  String sectionLabel(String id) {
    final s = sections.where((x) => x['id'] == id).firstOrNull;
    return s == null ? id : '${s['gradeNumber']}-${s['name']}';
  }

  String staffName(String? id) =>
      id == null ? tr('No one') : (staff.where((x) => x['id'] == id).firstOrNull?['name'] as String? ?? id);
}

class _TimetableAdminPageState extends State<TimetableAdminPage> {
  late Future<_SchoolData> _future = _load();

  static Future<_SchoolData> _load() async {
    final years = await Ops.list('$_base/academic-years', query: {'school_id': CurrentSession.schoolId});
    if (years.isEmpty) throw OpsError(409, tr('Your school has no academic year set up yet.'));
    years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
    final yearId = years.last['id'] as String;
    final sections = await Ops.list('$_base/academic-years/$yearId/sections');
    final staff = await Ops.list('/staff');
    return _SchoolData(yearId, sections, staff);
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 7,
      child: Scaffold(
        appBar: destinationAppBar(context,
          title: Text(tr('Timetable')),
          bottom: TabBar(isScrollable: true, tabs: [
            Tab(text: tr('Allocations')),
            Tab(text: tr('Groups')),
            Tab(text: tr('Rooms')),
            Tab(text: tr('Bell')),
            Tab(text: tr('Availability')),
            Tab(text: tr('Generate')),
            Tab(text: tr('Week')),
          ]),
        ),
        body: FutureBuilder<_SchoolData>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
            if (snap.hasError) {
              return ErrorDisplay(
                message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = _load(); }),
              );
            }
            final data = snap.data!;
            if (data.sections.isEmpty) {
              return EmptyState(icon: Icons.table_chart_outlined, title: tr('No sections yet'),
                  message: tr('Set up the classes and their sections first.'));
            }
            return TabBarView(children: [
              _AllocationsTab(data: data),
              _GroupsTab(data: data),
              _RoomsTab(data: data),
              _BellTab(data: data),
              _AvailabilityTab(data: data),
              _GenerateTab(data: data),
              _WeekTab(data: data),
            ]);
          },
        ),
      ),
    );
  }
}

Widget _errorText(BuildContext context, String message) =>
    Text(message, style: TextStyle(color: Theme.of(context).colorScheme.error));

// ------------------------------------------------------------------ allocations

class _AllocationsTab extends StatefulWidget {
  final _SchoolData data;
  const _AllocationsTab({required this.data});

  @override
  State<_AllocationsTab> createState() => _AllocationsTabState();
}

class _AllocationsTabState extends State<_AllocationsTab> {
  String? _sectionId;
  Future<(List<Map<String, dynamic>>, Map<String, Map<String, dynamic>>)>? _future;

  Future<(List<Map<String, dynamic>>, Map<String, Map<String, dynamic>>)> _loadSection(String sectionId) async {
    final section = widget.data.sections.firstWhere((s) => s['id'] == sectionId);
    final subjects = await Ops.list('$_base/grades/${section['gradeId']}/subjects');
    final allocs = await Ops.list('$_base/academic-years/${widget.data.yearId}/allocations');
    return (subjects, {
      for (final a in allocs.where((a) => a['sectionId'] == sectionId)) a['subjectId'] as String: a
    });
  }

  void _pick(String? id) => setState(() {
        _sectionId = id;
        _future = id == null ? null : _loadSection(id);
      });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text(tr('Who teaches each subject to a section, how often, with whom and where.'),
          style: theme.textTheme.bodySmall),
      const Gap(12),
      DropdownButtonFormField<String>(
        key: const ValueKey('alloc-section'),
        initialValue: _sectionId,
        isExpanded: true,
        decoration: InputDecoration(labelText: tr('Section')),
        items: [
          for (final s in widget.data.sections)
            DropdownMenuItem(value: s['id'] as String, child: Text(widget.data.sectionLabel(s['id'] as String))),
        ],
        onChanged: _pick,
      ),
      const Gap(12),
      if (_future != null)
        FutureBuilder(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
            if (snap.hasError) {
              return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: () => _pick(_sectionId));
            }
            final (subjects, allocs) = snap.data!;
            if (subjects.isEmpty) return Text(tr('This class has no subjects yet.'));
            return Column(children: [
              for (final subj in subjects)
                _AllocationRow(
                  key: ValueKey('alloc-${subj['id']}'),
                  data: widget.data,
                  sectionId: _sectionId!,
                  subject: subj,
                  current: allocs[subj['id']],
                ),
            ]);
          },
        ),
    ]);
  }
}

class _AllocationRow extends StatefulWidget {
  final _SchoolData data;
  final String sectionId;
  final Map<String, dynamic> subject;
  final Map<String, dynamic>? current;
  const _AllocationRow({super.key, required this.data, required this.sectionId, required this.subject, this.current});

  @override
  State<_AllocationRow> createState() => _AllocationRowState();
}

class _AllocationRowState extends State<_AllocationRow> {
  late String? _teacher = widget.current?['teacherId'] as String?;
  late String? _coTeacher = widget.current?['coTeacherId'] as String?;
  late String? _roomKind = widget.current?['roomKind'] as String?;
  late final _periods = TextEditingController(text: '${widget.current?['periodsPerWeek'] ?? ''}');
  late final _doubles = TextEditingController(text: '${widget.current?['doublePeriods'] ?? 0}');
  late Map<String, dynamic>? _saved = widget.current;
  bool _busy = false;
  String? _error;
  String? _note;

  @override
  void dispose() {
    _periods.dispose();
    _doubles.dispose();
    super.dispose();
  }

  String get _url => '$_base/sections/${widget.sectionId}/allocations/${widget.subject['id']}';

  Future<void> _save() async {
    final periods = int.tryParse(_periods.text.trim());
    final doubles = int.tryParse(_doubles.text.trim().isEmpty ? '0' : _doubles.text.trim());
    if (periods == null || periods < 1 || periods > 60) {
      setState(() => _error = tr('Periods a week is a whole number from 1 to 60.'));
      return;
    }
    if (doubles == null || doubles < 0 || doubles * 2 > periods) {
      setState(() => _error = tr('Double periods take two periods each, within the periods a week.'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _note = null;
    });
    try {
      final saved = await Ops.put(_url, body: {
        'teacherId': _teacher,
        'periodsPerWeek': periods,
        'coTeacherId': _coTeacher,
        'roomKind': _roomKind,
        'doublePeriods': doubles,
      });
      if (!mounted) return;
      setState(() {
        _saved = Map<String, dynamic>.from(saved as Map);
        _note = tr('Saved');
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _remove() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Ops.delete(_url);
      if (!mounted) return;
      setState(() {
        _saved = null;
        _teacher = null;
        _coTeacher = null;
        _roomKind = null;
        _periods.text = '';
        _doubles.text = '0';
        _note = tr('Removed');
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _staffPicker(String label, String? value, ValueChanged<String?> onChanged, Key key) {
    final staff = widget.data.staff;
    return DropdownButtonFormField<String?>(
      key: key,
      initialValue: staff.any((s) => s['id'] == value) ? value : null,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: [
        DropdownMenuItem<String?>(value: null, child: Text(tr('No one'))),
        for (final s in staff)
          DropdownMenuItem<String?>(value: s['id'] as String, child: Text(s['name'] as String, overflow: TextOverflow.ellipsis)),
      ],
      onChanged: _busy ? null : onChanged,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final id = widget.subject['id'];
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(widget.subject['name'] as String, style: theme.textTheme.titleSmall),
          const Gap(8),
          Wrap(spacing: 12, runSpacing: 12, children: [
            SizedBox(width: 240, child: _staffPicker(tr('Teacher'), _teacher, (v) => setState(() => _teacher = v), ValueKey('alloc-teacher-$id'))),
            SizedBox(width: 240, child: _staffPicker(tr('Co-teacher'), _coTeacher, (v) => setState(() => _coTeacher = v), ValueKey('alloc-co-$id'))),
            SizedBox(
              width: 140,
              child: TextField(
                key: ValueKey('alloc-periods-$id'),
                controller: _periods,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: tr('Periods a week')),
              ),
            ),
            SizedBox(
              width: 180,
              child: DropdownButtonFormField<String?>(
                key: ValueKey('alloc-room-$id'),
                initialValue: _roomKind,
                isExpanded: true,
                decoration: InputDecoration(labelText: tr('Needs a room')),
                items: [
                  DropdownMenuItem<String?>(value: null, child: Text(tr('Its own classroom'))),
                  for (final k in roomKinds) DropdownMenuItem<String?>(value: k, child: Text(tr(k))),
                ],
                onChanged: _busy ? null : (v) => setState(() => _roomKind = v),
              ),
            ),
            SizedBox(
              width: 140,
              child: TextField(
                key: ValueKey('alloc-doubles-$id'),
                controller: _doubles,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: tr('Double periods')),
              ),
            ),
          ]),
          if (_error != null) ...[const Gap(8), _errorText(context, _error!)],
          const Gap(8),
          Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
            FilledButton(
              key: ValueKey('alloc-save-$id'),
              onPressed: _busy ? null : _save,
              style: phoneTapTarget(context),
              child: Text(tr('Save')),
            ),
            if (_saved != null)
              TextButton(onPressed: _busy ? null : _remove, style: phoneTapTarget(context), child: Text(tr('Remove'))),
            if (_note != null) Text(_note!, style: theme.textTheme.bodySmall),
          ]),
        ]),
      ),
    );
  }
}

// ------------------------------------------------------------------ groups

/// "Hindi (Ana), Sanskrit (Dev)": a group's lanes as one line.
String groupLanesLine(List<dynamic> lanes) => [
      for (final l in lanes.cast<Map>())
        '${l['subjectName'] ?? l['subjectId']}${l['teacherName'] == null ? '' : ' (${l['teacherName']})'}'
            '${l['roomName'] == null ? '' : ', ${l['roomName']}'}',
    ].join('; ');

/// Elective groups and combined classes (SCH-8, audit N-3-20): the students
/// of one class's sections split into parallel lanes taught at the same
/// time by different teachers, or sections taught together by one teacher
/// in one room. Generating the timetable places each as one block.
class _GroupsTab extends StatefulWidget {
  final _SchoolData data;
  const _GroupsTab({required this.data});

  @override
  State<_GroupsTab> createState() => _GroupsTabState();
}

class _GroupsTabState extends State<_GroupsTab> {
  late Future<(List<Map<String, dynamic>>, List<Map<String, dynamic>>)> _future = _load();
  String? _error;

  Future<(List<Map<String, dynamic>>, List<Map<String, dynamic>>)> _load() async {
    final groups = await Ops.list('$_base/academic-years/${widget.data.yearId}/teaching-groups');
    final rooms = await Ops.list('$_base/rooms');
    return (groups, rooms);
  }

  void _reload() => setState(() { _future = _load(); });

  Future<void> _add(List<Map<String, dynamic>> rooms) async {
    final body = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _GroupDialog(data: widget.data, rooms: rooms),
    );
    if (body == null) return;
    try {
      await Ops.post('$_base/academic-years/${widget.data.yearId}/teaching-groups', body: body);
      setState(() => _error = null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _delete(Map<String, dynamic> group) async {
    try {
      await Ops.delete('$_base/teaching-groups/${group['id']}');
      setState(() => _error = null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<(List<Map<String, dynamic>>, List<Map<String, dynamic>>)>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final (groups, rooms) = snap.data!;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text(tr('Electives split a class\'s students into parallel lanes taught at the same time; a combined '
              'class teaches sections together. Generating the timetable places each as one block.'),
              style: theme.textTheme.bodySmall),
          if (_error != null) ...[const Gap(8), _errorText(context, _error!)],
          const Gap(8),
          if (groups.isEmpty) Text(tr('No groups yet.'), style: theme.textTheme.bodySmall),
          for (final g in groups)
            ListTile(
              key: ValueKey('group-${g['id']}'),
              contentPadding: EdgeInsets.zero,
              leading: Icon(g['kind'] == 'elective' ? Icons.call_split : Icons.groups_outlined),
              title: Text(g['name'] as String),
              subtitle: Text('${g['kind'] == 'elective' ? tr('Elective') : tr('Combined class')} · '
                  '${(g['sectionNames'] as List).join(', ')} · ${g['periodsPerWeek']} ${tr('a week')}, '
                  '${(g['periods'] as List).length} ${tr('placed')}\n${groupLanesLine(g['lanes'] as List)}'),
              isThreeLine: true,
              trailing: IconButton(tooltip: '${tr('Remove')} ${g['name']}', icon: const Icon(Icons.delete_outline),
                  onPressed: () => _delete(g)),
            ),
          const Gap(8),
          FilledButton.tonalIcon(
            key: const ValueKey('group-add'),
            onPressed: () => _add(rooms),
            style: phoneTapTarget(context),
            icon: const Icon(Icons.add),
            label: Text(tr('Add a group')),
          ),
        ]);
      },
    );
  }
}

/// A new group: its kind, name and periods a week, the class and the
/// sections it takes, and its lanes (one for a combined class). Pops the
/// POST body, or null when cancelled.
class _GroupDialog extends StatefulWidget {
  final _SchoolData data;
  final List<Map<String, dynamic>> rooms;
  const _GroupDialog({required this.data, required this.rooms});

  @override
  State<_GroupDialog> createState() => _GroupDialogState();
}

typedef _Lane = ({String? subjectId, String? teacherId, String? roomId});

class _GroupDialogState extends State<_GroupDialog> {
  String _kind = 'elective';
  final _name = TextEditingController();
  final _periods = TextEditingController(text: '3');
  String? _gradeId;
  Future<List<Map<String, dynamic>>>? _subjects;
  final Set<String> _sections = {};
  List<_Lane> _lanes = [for (var i = 0; i < 2; i++) (subjectId: null, teacherId: null, roomId: null)];
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _periods.dispose();
    super.dispose();
  }

  void _pickClass(String? gradeId) => setState(() {
        _gradeId = gradeId;
        _sections.clear();
        _lanes = [for (final _ in _lanes) (subjectId: null, teacherId: null, roomId: null)];
        _subjects = gradeId == null ? null : Ops.list('$_base/grades/$gradeId/subjects');
      });

  void _pickKind(String? kind) => setState(() {
        _kind = kind ?? 'elective';
        final n = _kind == 'combined' ? 1 : 2;
        _lanes = [for (var i = 0; i < n; i++) i < _lanes.length ? _lanes[i] : (subjectId: null, teacherId: null, roomId: null)];
      });

  void _setLane(int i, _Lane lane) => setState(() => _lanes = [...(_lanes..[i] = lane)]);

  void _save() {
    final periods = int.tryParse(_periods.text.trim());
    final String? problem = _name.text.trim().isEmpty
        ? tr('Give the group a name, such as Third language.')
        : periods == null || periods < 1 || periods > 60
            ? tr('Periods a week is a whole number from 1 to 60.')
            : _sections.length < (_kind == 'combined' ? 2 : 1)
                ? (_kind == 'combined' ? tr('A combined class joins two sections or more.') : tr('Choose its sections.'))
                : _lanes.any((l) => l.subjectId == null)
                    ? tr('Choose a subject for every lane.')
                    : null;
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.pop(context, {
      'kind': _kind,
      'name': _name.text.trim(),
      'periodsPerWeek': periods,
      'sectionIds': [for (final s in widget.data.sections) if (_sections.contains(s['id'])) s['id']],
      'lanes': [
        for (final l in _lanes) {'subjectId': l.subjectId, 'teacherId': l.teacherId, 'roomId': l.roomId},
      ],
    });
  }

  Widget _lane(int i, List<Map<String, dynamic>> subjects) {
    final lane = _lanes[i];
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
        SizedBox(
          width: 170,
          child: DropdownButtonFormField<String?>(
            key: ValueKey('group-lane-subject-$i'),
            initialValue: lane.subjectId,
            isExpanded: true,
            decoration: InputDecoration(labelText: '${tr('Subject')} ${i + 1}'),
            items: [
              for (final s in subjects)
                DropdownMenuItem<String?>(value: s['id'] as String, child: Text(s['name'] as String, overflow: TextOverflow.ellipsis)),
            ],
            onChanged: (v) => _setLane(i, (subjectId: v, teacherId: lane.teacherId, roomId: lane.roomId)),
          ),
        ),
        SizedBox(
          width: 170,
          child: DropdownButtonFormField<String?>(
            key: ValueKey('group-lane-teacher-$i'),
            initialValue: lane.teacherId,
            isExpanded: true,
            decoration: InputDecoration(labelText: tr('Teacher')),
            items: [
              DropdownMenuItem<String?>(value: null, child: Text(tr('No one'))),
              for (final s in widget.data.staff)
                DropdownMenuItem<String?>(value: s['id'] as String, child: Text(s['name'] as String, overflow: TextOverflow.ellipsis)),
            ],
            onChanged: (v) => _setLane(i, (subjectId: lane.subjectId, teacherId: v, roomId: lane.roomId)),
          ),
        ),
        SizedBox(
          width: 150,
          child: DropdownButtonFormField<String?>(
            key: ValueKey('group-lane-room-$i'),
            initialValue: lane.roomId,
            isExpanded: true,
            decoration: InputDecoration(labelText: tr('Room')),
            items: [
              DropdownMenuItem<String?>(value: null, child: Text(tr('Its own classroom'))),
              for (final r in widget.rooms)
                DropdownMenuItem<String?>(value: r['id'] as String, child: Text(r['name'] as String, overflow: TextOverflow.ellipsis)),
            ],
            onChanged: (v) => _setLane(i, (subjectId: lane.subjectId, teacherId: lane.teacherId, roomId: v)),
          ),
        ),
        if (_kind == 'elective' && _lanes.length > 2)
          IconButton(tooltip: '${tr('Remove lane')} ${i + 1}', icon: const Icon(Icons.close),
              onPressed: () => setState(() => _lanes = [..._lanes]..removeAt(i))),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final grades = <String, int>{
      for (final s in widget.data.sections) s['gradeId'] as String: (s['gradeNumber'] as num?)?.toInt() ?? 0,
    };
    final classSections = [for (final s in widget.data.sections) if (s['gradeId'] == _gradeId) s];
    return AlertDialog(
      title: Text(tr('Add a group')),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            DropdownButtonFormField<String>(
              key: const ValueKey('group-kind'),
              initialValue: _kind,
              isExpanded: true,
              decoration: InputDecoration(labelText: tr('Kind')),
              items: [
                DropdownMenuItem(value: 'elective', child: Text(tr('Elective: parallel lanes at the same time'))),
                DropdownMenuItem(value: 'combined', child: Text(tr('Combined class: sections taught together'))),
              ],
              onChanged: _pickKind,
            ),
            const Gap(8),
            TextField(key: const ValueKey('group-name'), controller: _name,
                decoration: InputDecoration(labelText: tr('Name'), hintText: tr('Third language'))),
            const Gap(8),
            TextField(key: const ValueKey('group-periods'), controller: _periods, keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: tr('Periods a week'))),
            const Gap(8),
            DropdownButtonFormField<String>(
              key: const ValueKey('group-class'),
              initialValue: _gradeId,
              isExpanded: true,
              decoration: InputDecoration(labelText: tr('Class')),
              items: [
                for (final e in (grades.entries.toList()..sort((a, b) => a.value - b.value)))
                  DropdownMenuItem(value: e.key, child: Text('${tr('Class')} ${e.value}')),
              ],
              onChanged: _pickClass,
            ),
            if (_gradeId != null) ...[
              const Gap(8),
              Wrap(spacing: 8, children: [
                for (final s in classSections)
                  FilterChip(
                    key: ValueKey('group-section-${s['id']}'),
                    label: Text(widget.data.sectionLabel(s['id'] as String)),
                    selected: _sections.contains(s['id']),
                    onSelected: (v) => setState(() => v ? _sections.add(s['id'] as String) : _sections.remove(s['id'])),
                  ),
              ]),
              FutureBuilder<List<Map<String, dynamic>>>(
                future: _subjects,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
                  if (snap.hasError) return _errorText(context, serverErrorMessage(snap.error!));
                  return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    for (var i = 0; i < _lanes.length; i++) _lane(i, snap.data!),
                    if (_kind == 'elective')
                      TextButton.icon(
                        key: const ValueKey('group-lane-add'),
                        onPressed: () => setState(() => _lanes = [..._lanes, (subjectId: null, teacherId: null, roomId: null)]),
                        icon: const Icon(Icons.add),
                        label: Text(tr('Add a lane')),
                      ),
                  ]);
                },
              ),
            ],
            if (_error != null) ...[const Gap(8), _errorText(context, _error!)],
          ]),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(key: const ValueKey('group-save'), onPressed: _save, child: Text(tr('Add'))),
      ],
    );
  }
}

// ------------------------------------------------------------------ rooms

class _RoomsTab extends StatefulWidget {
  final _SchoolData data;
  const _RoomsTab({required this.data});

  @override
  State<_RoomsTab> createState() => _RoomsTabState();
}

class _RoomsTabState extends State<_RoomsTab> {
  late Future<(List<Map<String, dynamic>>, Map<String, List<dynamic>>)> _future = _load();
  String? _error;

  Future<(List<Map<String, dynamic>>, Map<String, List<dynamic>>)> _load() async {
    final rooms = await Ops.list('$_base/rooms');
    final closed = await Ops.list('$_base/academic-years/${widget.data.yearId}/room-unavailability');
    return (rooms, {for (final r in closed) r['roomId'] as String: r['slots'] as List<dynamic>});
  }

  void _reload() => setState(() { _future = _load(); });

  Future<void> _add() async {
    final name = TextEditingController();
    final capacity = TextEditingController();
    var kind = 'classroom';
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(builder: (context, setDialog) => AlertDialog(
            title: Text(tr('Add a room')),
            content: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(key: const ValueKey('room-name'), controller: name,
                  decoration: InputDecoration(labelText: tr('Name'), hintText: 'Lab 1')),
              const Gap(8),
              DropdownButtonFormField<String>(
                key: const ValueKey('room-kind'),
                initialValue: kind,
                decoration: InputDecoration(labelText: tr('Kind')),
                items: [for (final k in roomKinds) DropdownMenuItem(value: k, child: Text(tr(k)))],
                onChanged: (v) => setDialog(() => kind = v ?? 'classroom'),
              ),
              const Gap(8),
              TextField(controller: capacity, keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: tr('Capacity (optional)'))),
            ]),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context, false), child: Text(tr('Cancel'))),
              FilledButton(key: const ValueKey('room-save'), onPressed: () => Navigator.pop(context, true), child: Text(tr('Add'))),
            ],
          )),
    );
    if (ok != true) return;
    try {
      await Ops.post('$_base/rooms', body: {
        'name': name.text.trim(),
        'kind': kind,
        if (int.tryParse(capacity.text.trim()) != null) 'capacity': int.parse(capacity.text.trim()),
      });
      setState(() => _error = null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _delete(Map<String, dynamic> room) async {
    try {
      await Ops.delete('$_base/rooms/${room['id']}');
      setState(() => _error = null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _closures(Map<String, dynamic> room, List<dynamic> current) async {
    final List<Map<String, dynamic>> bells;
    try {
      bells = await Ops.list('$_base/academic-years/${widget.data.yearId}/bell-schedules');
    } catch (e) {
      // The load failed: say why, not "set up the bell first".
      if (mounted) setState(() => _error = serverErrorMessage(e));
      return;
    }
    if (!mounted) return;
    final bell = bells.where((b) => b['isDefault'] == true).firstOrNull ?? bells.firstOrNull;
    if (bell == null) {
      setState(() => _error = tr('Set up the bell first: a period means nothing until the school has periods.'));
      return;
    }
    final days = (bell['days'] as List).cast<int>();
    final periods = bell['teachingPeriods'] as int;
    final picked = {for (final s in current.cast<Map>()) '${s['dayOfWeek']}:${s['period']}'};
    final saved = await showDialog<Set<String>>(
      context: context,
      builder: (context) => StatefulBuilder(builder: (context, setDialog) => AlertDialog(
            title: Text('${room['name']}: ${tr('out of use')}'),
            content: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columnSpacing: 8,
                columns: [const DataColumn(label: Text('')), for (final d in days) DataColumn(label: Text(tr(_dayNames[d])))],
                rows: [
                  for (var p = 1; p <= periods; p++)
                    DataRow(cells: [
                      DataCell(Text('P$p')),
                      for (final d in days)
                        DataCell(Checkbox(
                          key: ValueKey('closed-$d-$p'),
                          value: picked.contains('$d:$p'),
                          onChanged: (v) => setDialog(() => v == true ? picked.add('$d:$p') : picked.remove('$d:$p')),
                        )),
                    ]),
                ],
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
              FilledButton(key: const ValueKey('closed-save'), onPressed: () => Navigator.pop(context, picked), child: Text(tr('Save'))),
            ],
          )),
    );
    if (saved == null) return;
    try {
      await Ops.put('$_base/academic-years/${widget.data.yearId}/room-unavailability/${room['id']}', body: {
        'slots': [
          for (final s in saved)
            {'dayOfWeek': int.parse(s.split(':')[0]), 'period': int.parse(s.split(':')[1])}
        ],
      });
      setState(() => _error = null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<(List<Map<String, dynamic>>, Map<String, List<dynamic>>)>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final (rooms, closed) = snap.data!;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text(tr('Labs and halls a subject can ask for, and when a room is out of use.'),
              style: Theme.of(context).textTheme.bodySmall),
          if (_error != null) ...[const Gap(8), _errorText(context, _error!)],
          const Gap(8),
          for (final r in rooms)
            ListTile(
              key: ValueKey('room-${r['id']}'),
              contentPadding: EdgeInsets.zero,
              leading: Icon(r['kind'] == 'lab' ? Icons.science_outlined : Icons.meeting_room_outlined),
              title: Text(r['name'] as String),
              subtitle: Text('${tr(r['kind'] as String)}'
                  '${(closed[r['id']] ?? const []).isEmpty ? '' : ' · ${(closed[r['id']]!).length} ${tr('periods out of use')}'}'),
              trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                IconButton(tooltip: '${tr('Out of use')}: ${r['name']}', icon: const Icon(Icons.event_busy_outlined),
                    onPressed: () => _closures(r, closed[r['id']] ?? const [])),
                IconButton(tooltip: '${tr('Remove')} ${r['name']}', icon: const Icon(Icons.delete_outline),
                    onPressed: () => _delete(r)),
              ]),
            ),
          const Gap(8),
          FilledButton.tonalIcon(
            key: const ValueKey('room-add'),
            onPressed: _add,
            style: phoneTapTarget(context),
            icon: const Icon(Icons.add),
            label: Text(tr('Add a room')),
          ),
        ]);
      },
    );
  }
}

// ------------------------------------------------------------------ bell

class _BellTab extends StatefulWidget {
  final _SchoolData data;
  const _BellTab({required this.data});

  @override
  State<_BellTab> createState() => _BellTabState();
}

class _BellTabState extends State<_BellTab> {
  late Future<List<Map<String, dynamic>>> _future = _load();
  final _name = TextEditingController(text: 'Main');
  final _slots = TextEditingController();
  final Set<int> _days = {0, 1, 2, 3, 4, 5};
  String? _editingId;
  String? _error;
  bool _busy = false;

  Future<List<Map<String, dynamic>>> _load() => Ops.list('$_base/academic-years/${widget.data.yearId}/bell-schedules');

  void _reload() => setState(() { _future = _load(); });

  @override
  void dispose() {
    _name.dispose();
    _slots.dispose();
    super.dispose();
  }

  void _edit(Map<String, dynamic>? b) => setState(() {
        _editingId = b?['id'] as String?;
        _name.text = b?['name'] as String? ?? 'Main';
        _slots.text = b == null ? '' : bellSlotsText(b['slots'] as List);
        _days
          ..clear()
          ..addAll(b == null ? {0, 1, 2, 3, 4, 5} : (b['days'] as List).cast<int>());
        _error = null;
      });

  Future<void> _save() async {
    final (:slots, :error) = parseBellSlots(_slots.text);
    if (error != null) {
      setState(() => _error = error);
      return;
    }
    if (_days.isEmpty) {
      setState(() => _error = tr('Choose the days the school teaches.'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final body = {'name': _name.text.trim(), 'days': (_days.toList()..sort()), 'slots': slots};
    try {
      if (_editingId == null) {
        await Ops.post('$_base/academic-years/${widget.data.yearId}/bell-schedules', body: body);
      } else {
        await Ops.put('$_base/bell-schedules/$_editingId', body: body);
      }
      _edit(null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _makeDefault(Map<String, dynamic> b) async {
    try {
      await Ops.put('$_base/bell-schedules/${b['id']}', body: {'makeDefault': true});
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final bells = snap.data!;
        return ListView(padding: const EdgeInsets.all(16), children: [
          for (final b in bells)
            ListTile(
              key: ValueKey('bell-${b['id']}'),
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.schedule_outlined),
              title: Text('${b['name']}${b['isDefault'] == true ? ' (${tr('default')})' : ''}'),
              subtitle: Text('${b['teachingPeriods']} ${tr('periods')} · '
                  '${(b['days'] as List).map((d) => tr(_dayNames[d as int])).join(', ')}'),
              trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                if (b['isDefault'] != true)
                  IconButton(tooltip: tr('Make default'), icon: const Icon(Icons.star_outline), onPressed: () => _makeDefault(b)),
                IconButton(tooltip: '${tr('Edit')} ${b['name']}', icon: const Icon(Icons.edit_outlined), onPressed: () => _edit(b)),
              ]),
            ),
          const Gap(12),
          Text(_editingId == null ? tr('Add a bell') : tr('Edit the bell'), style: theme.textTheme.titleSmall),
          const Gap(8),
          TextField(key: const ValueKey('bell-name'), controller: _name,
              decoration: InputDecoration(labelText: tr('Name'))),
          const Gap(8),
          Wrap(spacing: 8, children: [
            for (var d = 0; d < 7; d++)
              FilterChip(
                label: Text(tr(_dayNames[d])),
                selected: _days.contains(d),
                onSelected: (v) => setState(() => v ? _days.add(d) : _days.remove(d)),
              ),
          ]),
          const Gap(8),
          TextField(
            key: const ValueKey('bell-slots'),
            controller: _slots,
            maxLines: 10,
            minLines: 5,
            decoration: InputDecoration(
              labelText: tr('Slots, one a line'),
              hintText: '08:00-08:45\n08:45-09:30\n09:30-09:50 break',
            ),
          ),
          if (_error != null) ...[const Gap(8), _errorText(context, _error!)],
          const Gap(8),
          Wrap(spacing: 8, children: [
            FilledButton(key: const ValueKey('bell-save'), onPressed: _busy ? null : _save,
                style: phoneTapTarget(context), child: Text(tr('Save the bell'))),
            if (_editingId != null)
              TextButton(onPressed: () => _edit(null), style: phoneTapTarget(context), child: Text(tr('Cancel'))),
          ]),
        ]);
      },
    );
  }
}

// ------------------------------------------------------------------ generate


class _GenerateTab extends StatefulWidget {
  final _SchoolData data;
  const _GenerateTab({required this.data});

  @override
  State<_GenerateTab> createState() => _GenerateTabState();
}

/// One period of the generated week's diff as a line: "Mon P3: Science
/// (Ana) → Maths (Bala)", with "free" for a period added or emptied.
String periodChangeLine(Map change) {
  String holds(Map? p) {
    if (p == null) return tr('free');
    final teacher = p['teacherName'] as String?;
    final room = p['roomName'] as String?;
    return [
      '${p['subjectName'] ?? p['subjectId']}${teacher == null ? '' : ' ($teacher)'}',
      if (room != null) room,
    ].join(', ');
  }

  return '${tr(_dayNames[change['dayOfWeek'] as int])} P${change['period']}: '
      '${holds(change['before'] as Map?)} → ${holds(change['after'] as Map?)}';
}

class _GenerateTabState extends State<_GenerateTab> {
  final _maxDay = TextEditingController(text: '7');
  final _maxRow = TextEditingController(text: '4');
  bool _keep = true;
  bool _busy = false;
  Map<String, dynamic>? _result;
  String? _error;
  @override
  void dispose() {
    _maxDay.dispose();
    _maxRow.dispose();
    super.dispose();
  }

  /// Generates a week and shows it without writing; the server keeps it
  /// under a preview id, and publishing writes exactly that week (N-3-6).
  Future<void> _preview() async {
    final maxDay = int.tryParse(_maxDay.text.trim()), maxRow = int.tryParse(_maxRow.text.trim());
    if (maxDay == null || maxDay < 1 || maxDay > 12 || maxRow == null || maxRow < 1 || maxRow > 12) {
      setState(() => _error = tr('A teacher\'s most a day and in a row are whole numbers from 1 to 12.'));
      return;
    }
    await _send(() => Ops.post('$_base/academic-years/${widget.data.yearId}/timetable/solve', body: {
          'apply': false,
          'keepExisting': _keep,
          'maxPerDay': maxDay,
          'maxConsecutive': maxRow,
          'timeLimitSeconds': 60,
        }));
  }

  Future<void> _publish() async {
    final id = _result?['previewId'] as String?;
    if (id == null) return;
    final ok = await _send(
        () => Ops.post('$_base/academic-years/${widget.data.yearId}/timetable/previews/$id/publish'));
    // A stale or replaced preview cannot be published: preview again first.
    if (!ok && mounted) setState(() => _result = {...?_result, 'previewId': null});
  }

  Future<bool> _send(Future<dynamic> Function() call) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final r = await call();
      if (mounted) setState(() => _result = Map<String, dynamic>.from(r as Map));
      return true;
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
      return false;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }


  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = _result;
    final solved = r?['status'] == 'solved';
    final changes = ((r?['changes'] as List?) ?? const []).cast<Map>();
    final bySection = <String, List<Map>>{};
    for (final c in changes) {
      bySection.putIfAbsent(c['sectionId'] as String, () => []).add(c);
    }
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text(tr('Generate a clash-free week for every section from the allocations, rooms and bell. '
          'Preview first: nothing changes until you publish, and publishing writes exactly the week previewed.'),
          style: theme.textTheme.bodySmall),
      const Gap(12),
      Wrap(spacing: 12, runSpacing: 12, children: [
        SizedBox(width: 180, child: TextField(key: const ValueKey('solve-max-day'), controller: _maxDay,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(labelText: tr('Most a day per teacher')))),
        SizedBox(width: 180, child: TextField(key: const ValueKey('solve-max-row'), controller: _maxRow,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(labelText: tr('Most in a row')))),
      ]),
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: Text(tr('Keep the current week where possible')),
        value: _keep,
        onChanged: (v) => setState(() => _keep = v),
      ),
      if (_error != null) ...[_errorText(context, _error!), const Gap(8)],
      Wrap(spacing: 8, children: [
        FilledButton.tonal(key: const ValueKey('solve-preview'), onPressed: _busy ? null : _preview,
            style: phoneTapTarget(context), child: Text(tr('Preview'))),
        FilledButton(key: const ValueKey('solve-publish'),
            onPressed: _busy || !solved || r?['applied'] == true || r?['previewId'] == null ? null : _publish,
            style: phoneTapTarget(context), child: Text(tr('Publish'))),
      ]),
      if (_busy) ...[const Gap(12), const LinearProgressIndicator()],
      if (r != null) ...[
        const Gap(16),
        Text(key: const ValueKey('solve-status'),
            switch (r['status']) {
              'solved' when r['applied'] == true => tr('Published. Teachers have been told.'),
              'solved' => tr('A week that meets every rule:'),
              'infeasible' => tr('No week can meet every rule yet:'),
              'timeout' => tr('No week found in time:'),
              _ => tr('Nothing to generate yet:'),
            },
            style: theme.textTheme.titleSmall),
        if (solved)
          Text('${tr('keeps')} ${r['kept']}, ${tr('moves or adds')} ${r['movedOrAdded']}, '
              '${tr('removes')} ${r['removed']} ${tr('periods')} (${r['seconds']} s)'),
        for (final p in (r['problems'] as List? ?? const [])) Text('- $p'),
        if (solved && changes.isEmpty) Text(key: const ValueKey('solve-no-changes'), tr('No period changes.')),
        if (changes.isNotEmpty) ...[
          const Gap(8),
          Text('${changes.length} ${tr('periods change')}:', style: theme.textTheme.titleSmall),
          // Section by section, each period's before and after.
          for (final MapEntry(key: sectionId, value: rows) in bySection.entries)
            ExpansionTile(
              key: ValueKey('solve-changes-$sectionId'),
              tilePadding: EdgeInsets.zero,
              childrenPadding: const EdgeInsets.only(bottom: 8),
              expandedCrossAxisAlignment: CrossAxisAlignment.start,
              title: Text('${rows.first['sectionName'] ?? widget.data.sectionLabel(sectionId)}: '
                  '${rows.length} ${tr('periods')}'),
              children: [for (final c in rows) Text(periodChangeLine(c), style: theme.textTheme.bodySmall)],
            ),
        ],
      ],
    ]);
  }
}

// ------------------------------------------------------------------ availability

/// The teacher-level constraint the generator honours: periods a teacher
/// cannot teach (a part-timer's mornings, a standing duty), in the default
/// bell's numbering, as the route stores them.
class _AvailabilityTab extends StatefulWidget {
  final _SchoolData data;
  const _AvailabilityTab({required this.data});

  @override
  State<_AvailabilityTab> createState() => _AvailabilityTabState();
}

class _AvailabilityTabState extends State<_AvailabilityTab> {
  late Future<(Map<String, dynamic>?, Map<String, List<Map>>)> _future = _load();
  String? _error;

  Future<(Map<String, dynamic>?, Map<String, List<Map>>)> _load() async {
    final bells = await Ops.list('$_base/academic-years/${widget.data.yearId}/bell-schedules');
    final rows = await Ops.list('$_base/academic-years/${widget.data.yearId}/teacher-unavailability');
    final bell = bells.where((b) => b['isDefault'] == true).firstOrNull ?? bells.firstOrNull;
    return (bell, {for (final r in rows) r['teacherId'] as String: (r['slots'] as List).cast<Map>()});
  }

  void _reload() => setState(() { _future = _load(); });

  Future<void> _edit(Map<String, dynamic> teacher, Map<String, dynamic> bell, List<Map> current) async {
    final days = (bell['days'] as List).cast<int>();
    final periods = bell['teachingPeriods'] as int;
    final picked = {for (final s in current) '${s['dayOfWeek']}:${s['period']}'};
    final saved = await showDialog<Set<String>>(
      context: context,
      builder: (context) => StatefulBuilder(builder: (context, setDialog) => AlertDialog(
            title: Text('${teacher['name']}: ${tr('cannot teach')}'),
            content: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columnSpacing: 8,
                columns: [const DataColumn(label: Text('')), for (final d in days) DataColumn(label: Text(tr(_dayNames[d])))],
                rows: [
                  for (var p = 1; p <= periods; p++)
                    DataRow(cells: [
                      DataCell(Text('P$p')),
                      for (final d in days)
                        DataCell(Checkbox(
                          key: ValueKey('unavail-$d-$p'),
                          value: picked.contains('$d:$p'),
                          onChanged: (v) => setDialog(() => v == true ? picked.add('$d:$p') : picked.remove('$d:$p')),
                        )),
                    ]),
                ],
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
              FilledButton(key: const ValueKey('unavail-save'), onPressed: () => Navigator.pop(context, picked),
                  child: Text(tr('Save'))),
            ],
          )),
    );
    if (saved == null) return;
    try {
      await Ops.put('$_base/academic-years/${widget.data.yearId}/teacher-unavailability/${teacher['id']}', body: {
        'slots': [
          for (final s in saved)
            {'dayOfWeek': int.parse(s.split(':')[0]), 'period': int.parse(s.split(':')[1])}
        ],
      });
      setState(() => _error = null);
      _reload();
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<(Map<String, dynamic>?, Map<String, List<Map>>)>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final (bell, busy) = snap.data!;
        if (bell == null) {
          return EmptyState(icon: Icons.schedule_outlined, title: tr('No bell yet'),
              message: tr('Set up the bell first: a period means nothing until the school has periods.'));
        }
        if (widget.data.staff.isEmpty) {
          return EmptyState(icon: Icons.person_outline, title: tr('No teachers yet'),
              message: tr('Invite or import the teachers first.'));
        }
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text(tr('Periods a teacher cannot teach. Generating the timetable leaves them free.'),
              style: Theme.of(context).textTheme.bodySmall),
          if (_error != null) ...[const Gap(8), _errorText(context, _error!)],
          const Gap(8),
          for (final t in widget.data.staff)
            ListTile(
              key: ValueKey('unavail-${t['id']}'),
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.person_outline),
              title: Text(t['name'] as String),
              subtitle: Text((busy[t['id']] ?? const []).isEmpty
                  ? tr('Can teach every period')
                  : '${busy[t['id']]!.length} ${tr('periods they cannot teach')}'),
              trailing: IconButton(
                tooltip: '${tr('Periods they cannot teach')}: ${t['name']}',
                icon: const Icon(Icons.event_busy_outlined),
                onPressed: () => _edit(t, bell, busy[t['id']] ?? const []),
              ),
            ),
        ]);
      },
    );
  }
}

// ------------------------------------------------------------------ week

/// A section's week and what it needs: the bell, the class's subjects, this
/// section's allocations (who teaches each, how often, in what kind of
/// room), the school's rooms, and the periods the section spends in its
/// groups -- the group's, not editable here (N-3-20).
class _WeekData {
  final Map<String, dynamic>? bell;
  final List<Map<String, dynamic>> subjects;
  final Map<String, Map<String, dynamic>> allocations; // subject id -> allocation
  final List<Map<String, dynamic>> rooms;
  final Map<(int, int), Map> groupPeriods; // (day, period) -> the group's period
  const _WeekData(this.bell, this.subjects, this.allocations, this.rooms, this.groupPeriods);

  String subjectName(String id) => subjects.where((s) => s['id'] == id).firstOrNull?['name'] as String? ?? id;
  String? roomName(String? id) => id == null ? null : rooms.where((r) => r['id'] == id).firstOrNull?['name'] as String?;
}

/// One period of the week being edited, in the PUT's own shape: a null
/// teacher is the allocation's teacher. The co-teacher is shown only: the
/// server takes it from the allocation.
typedef _Cell = ({String subjectId, String? teacherId, String? roomId, bool locked, String? coTeacherId});

class _WeekTab extends StatefulWidget {
  final _SchoolData data;
  const _WeekTab({required this.data});

  @override
  State<_WeekTab> createState() => _WeekTabState();
}

class _WeekTabState extends State<_WeekTab> {
  String? _sectionId;
  Future<_WeekData>? _future;
  // The week as edited here, (day, period) -> period; saved all at once.
  Map<(int, int), _Cell> _cells = {};
  bool _dirty = false;
  bool _saving = false;
  String? _error;
  List<String> _clashes = const [];
  String? _note;

  Future<_WeekData> _load(String sectionId) async {
    final section = widget.data.sections.firstWhere((s) => s['id'] == sectionId);
    final week = await Ops.map('$_base/sections/$sectionId/timetable');
    final bells = await Ops.list('$_base/academic-years/${widget.data.yearId}/bell-schedules');
    final subjects = await Ops.list('$_base/grades/${section['gradeId']}/subjects');
    final allocs = await Ops.list('$_base/academic-years/${widget.data.yearId}/allocations');
    final rooms = await Ops.list('$_base/rooms');
    _take(week);
    return _WeekData(bells.where((b) => b['id'] == week['bellScheduleId']).firstOrNull, subjects,
        {for (final a in allocs.where((a) => a['sectionId'] == sectionId)) a['subjectId'] as String: a}, rooms,
        {for (final g in ((week['groupPeriods'] as List?) ?? const []).cast<Map>()) (g['dayOfWeek'] as int, g['period'] as int): g});
  }

  /// The server's week becomes the one being edited.
  void _take(Map<String, dynamic> week) {
    _cells = {
      for (final e in (week['entries'] as List).cast<Map>())
        (e['dayOfWeek'] as int, e['period'] as int): (
          subjectId: e['subjectId'] as String,
          teacherId: e['teacherId'] as String?,
          roomId: e['roomId'] as String?,
          locked: e['locked'] == true,
          coTeacherId: e['coTeacherId'] as String?,
        ),
    };
    _dirty = false;
  }

  void _pick(String? id) => setState(() {
        _sectionId = id;
        _future = id == null ? null : _load(id);
        _error = null;
        _clashes = const [];
        _note = null;
      });

  Future<void> _editCell(_WeekData w, int day, int period) async {
    final result = await showDialog<({_Cell? cell})>(
      context: context,
      builder: (_) => _CellDialog(
        title: '${tr(_dayNames[day])}, ${tr('period')} $period',
        current: _cells[(day, period)],
        week: w,
        staff: widget.data.staff,
      ),
    );
    if (result == null) return;
    setState(() {
      if (result.cell == null) {
        _cells.remove((day, period));
      } else {
        _cells[(day, period)] = result.cell!;
      }
      _dirty = true;
      _clashes = const [];
      _error = null;
      _note = null;
    });
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
      _clashes = const [];
      _note = null;
    });
    final keys = _cells.keys.toList()..sort((a, b) => a.$1 != b.$1 ? a.$1 - b.$1 : a.$2 - b.$2);
    try {
      final saved = await Ops.put('$_base/sections/$_sectionId/timetable', body: {
        'entries': [
          for (final k in keys)
            {
              'dayOfWeek': k.$1,
              'period': k.$2,
              'subjectId': _cells[k]!.subjectId,
              'teacherId': _cells[k]!.teacherId,
              'roomId': _cells[k]!.roomId,
              'locked': _cells[k]!.locked,
            },
        ],
      });
      if (!mounted) return;
      setState(() {
        _take(Map<String, dynamic>.from(saved as Map));
        _note = '${tr('Saved')}: ${_cells.length} ${tr('periods')}';
      });
    } on OpsError catch (e) {
      // A 409 names every clash; the server kept the old week.
      if (mounted) setState(() { _error = serverErrorMessage(e); _clashes = e.clashes; });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _staffName(String? id) =>
      widget.data.staff.where((x) => x['id'] == id).firstOrNull?['name'] as String? ?? '';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(padding: const EdgeInsets.all(16), children: [
      DropdownButtonFormField<String>(
        key: const ValueKey('week-section'),
        initialValue: _sectionId,
        isExpanded: true,
        decoration: InputDecoration(
          labelText: tr('Section'),
          helperText: _dirty ? tr('Save or discard the changes to choose another section.') : null,
        ),
        items: [
          for (final s in widget.data.sections)
            DropdownMenuItem(value: s['id'] as String, child: Text(widget.data.sectionLabel(s['id'] as String))),
        ],
        onChanged: _dirty ? null : _pick,
      ),
      const Gap(12),
      if (_future == null)
        Text(tr('Choose a section to see and change its week.'), style: theme.textTheme.bodySmall)
      else
        FutureBuilder<_WeekData>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
            if (snap.hasError) {
              return Notice(kind: NoticeKind.danger, title: serverErrorMessage(snap.error!),
                  action: OutlinedButton(onPressed: () => _pick(_sectionId), child: Text(tr('Try again'))));
            }
            final w = snap.data!;
            final bell = w.bell;
            if (bell == null) return Text(tr('Set up the bell first.'));
            final days = (bell['days'] as List).cast<int>();
            final periods = bell['teachingPeriods'] as int;
            String cell(_Cell c) {
              final alloc = w.allocations[c.subjectId];
              final teacher = c.teacherId ?? alloc?['teacherId'] as String?;
              final co = c.coTeacherId;
              return [
                w.subjectName(c.subjectId),
                _staffName(teacher),
                if (co != null && co != teacher) '+ ${_staffName(co)}',
                w.roomName(c.roomId) ?? '',
              ].where((s) => s.isNotEmpty).join('\n');
            }
            final placed = <String, int>{};
            for (final c in _cells.values) {
              placed[c.subjectId] = (placed[c.subjectId] ?? 0) + 1;
            }
            final short = [
              for (final a in w.allocations.values)
                if ((placed[a['subjectId']] ?? 0) != a['periodsPerWeek'])
                  '${tr('Still to place')}: ${placed[a['subjectId']] ?? 0} ${tr('of')} ${a['periodsPerWeek']} '
                      '${tr('periods a week for')} ${w.subjectName(a['subjectId'] as String)}',
            ];
            return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(tr('Tap a period to change or lock it. Nothing is saved until you save the week; '
                  'the school first checks every teacher and room against the other sections.'),
                  style: theme.textTheme.bodySmall),
              const Gap(8),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  key: const ValueKey('week-grid'),
                  dataRowMaxHeight: 88,
                  showCheckboxColumn: false,
                  columns: [const DataColumn(label: Text('')), for (final d in days) DataColumn(label: Text(tr(_dayNames[d])))],
                  rows: [
                    for (var p = 1; p <= periods; p++)
                      DataRow(cells: [
                        DataCell(Text('P$p')),
                        for (final d in days)
                          DataCell(
                            Container(
                              key: ValueKey('week-cell-$d-$p'),
                              constraints: const BoxConstraints(minWidth: 64, minHeight: 40),
                              alignment: Alignment.centerLeft,
                              child: _cells[(d, p)] == null && w.groupPeriods[(d, p)] != null
                                  ? Row(mainAxisSize: MainAxisSize.min, children: [
                                      Icon(Icons.groups_outlined, size: 14, semanticLabel: tr('Group'),
                                          color: theme.colorScheme.primary),
                                      const Gap(4),
                                      Text('${w.groupPeriods[(d, p)]!['groupName']}\n'
                                          '${groupLanesLine(w.groupPeriods[(d, p)]!['lanes'] as List)}',
                                          style: theme.textTheme.bodySmall),
                                    ])
                                  : _cells[(d, p)] == null
                                  ? Text(tr('Free'), style: theme.textTheme.bodySmall?.copyWith(
                                      color: theme.colorScheme.onSurfaceVariant))
                                  : Row(mainAxisSize: MainAxisSize.min, children: [
                                      Text(cell(_cells[(d, p)]!), style: theme.textTheme.bodySmall),
                                      if (_cells[(d, p)]!.locked) ...[
                                        const Gap(4),
                                        Icon(Icons.lock_outline, size: 14, semanticLabel: tr('Locked'),
                                            color: theme.colorScheme.primary),
                                      ],
                                    ]),
                            ),
                            // A group's period is changed with its group, not here.
                            onTap: _saving || w.groupPeriods[(d, p)] != null ? null : () => _editCell(w, d, p),
                          ),
                      ]),
                  ],
                ),
              ),
              for (final line in short) Text(line, style: theme.textTheme.bodySmall),
              if (_error != null) ...[
                const Gap(12),
                Notice(
                  key: const ValueKey('week-clashes'),
                  kind: NoticeKind.danger,
                  title: _clashes.isEmpty
                      ? _error!
                      : '${tr('Not saved')}: ${_clashes.length} ${tr('clashes. The week is kept as it was.')}',
                  lines: _clashes,
                ),
              ],
              if (_note != null) ...[const Gap(8), Text(_note!, style: theme.textTheme.bodySmall)],
              if (_dirty) ...[
                const Gap(12),
                Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                  FilledButton(key: const ValueKey('week-save'), onPressed: _saving ? null : _save,
                      style: phoneTapTarget(context), child: Text(tr('Save the week'))),
                  TextButton(key: const ValueKey('week-discard'), onPressed: _saving ? null : () => _pick(_sectionId),
                      style: phoneTapTarget(context), child: Text(tr('Discard changes'))),
                ]),
              ],
              if (_saving) ...[const Gap(12), const LinearProgressIndicator()],
            ]);
          },
        ),
    ]);
  }
}

/// One period, edited: the subject (or a free period), who teaches it (the
/// allocation's teacher unless another is picked), the room, and whether it
/// is locked against the next generation. Pops `(cell: null)` for a free
/// period, and null when cancelled.
class _CellDialog extends StatefulWidget {
  final String title;
  final _Cell? current;
  final _WeekData week;
  final List<Map<String, dynamic>> staff;
  const _CellDialog({required this.title, required this.current, required this.week, required this.staff});

  @override
  State<_CellDialog> createState() => _CellDialogState();
}

class _CellDialogState extends State<_CellDialog> {
  late String? _subject = widget.current?.subjectId;
  // The allocation's own teacher is the null choice ("allocated"), not a
  // second item: a period they teach opens on that choice.
  late String? _teacher = widget.current?.teacherId ==
          widget.week.allocations[widget.current?.subjectId]?['teacherId']
      ? null
      : widget.current?.teacherId;
  late String? _room = widget.current?.roomId;
  late bool _locked = widget.current?.locked ?? false;

  @override
  Widget build(BuildContext context) {
    final w = widget.week;
    final alloc = _subject == null ? null : w.allocations[_subject];
    final kind = alloc?['roomKind'] as String?;
    final rooms = [for (final r in w.rooms) if (kind == null || r['kind'] == kind) r];
    final allocTeacher = widget.staff.where((s) => s['id'] == alloc?['teacherId']).firstOrNull?['name'];
    return AlertDialog(
      title: Text(widget.title),
      content: SizedBox(
        width: 420,
        child: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            if (w.allocations.isEmpty)
              Text(tr('This section has no allocations yet: set them on the Allocations tab first.')),
            DropdownButtonFormField<String?>(
              key: const ValueKey('cell-subject'),
              initialValue: _subject,
              isExpanded: true,
              decoration: InputDecoration(labelText: tr('Subject')),
              items: [
                DropdownMenuItem<String?>(value: null, child: Text(tr('Free period'))),
                for (final a in w.allocations.values)
                  DropdownMenuItem<String?>(
                    value: a['subjectId'] as String,
                    child: Text('${w.subjectName(a['subjectId'] as String)} (${a['periodsPerWeek']} ${tr('a week')})',
                        overflow: TextOverflow.ellipsis),
                  ),
              ],
              onChanged: (v) => setState(() {
                _subject = v;
                _teacher = null;
                _room = null;
              }),
            ),
            if (_subject != null) ...[
              const Gap(8),
              DropdownButtonFormField<String?>(
                key: ValueKey('cell-teacher-$_subject'),
                initialValue: widget.staff.any((s) => s['id'] == _teacher) ? _teacher : null,
                isExpanded: true,
                decoration: InputDecoration(labelText: tr('Teacher')),
                items: [
                  DropdownMenuItem<String?>(value: null,
                      child: Text(allocTeacher == null ? tr('The allocation\'s teacher') : '$allocTeacher (${tr('allocated')})',
                          overflow: TextOverflow.ellipsis)),
                  for (final s in widget.staff)
                    if (s['id'] != alloc?['teacherId'])
                      DropdownMenuItem<String?>(value: s['id'] as String,
                          child: Text(s['name'] as String, overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (v) => setState(() => _teacher = v),
              ),
              const Gap(8),
              DropdownButtonFormField<String?>(
                key: ValueKey('cell-room-$_subject'),
                initialValue: rooms.any((r) => r['id'] == _room) ? _room : null,
                isExpanded: true,
                decoration: InputDecoration(
                    labelText: kind == null ? tr('Room') : '${tr('Room')} (${tr('needs a')} ${tr(kind)})'),
                items: [
                  DropdownMenuItem<String?>(value: null, child: Text(tr('Its own classroom'))),
                  for (final r in rooms)
                    DropdownMenuItem<String?>(value: r['id'] as String,
                        child: Text(r['name'] as String, overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (v) => setState(() => _room = v),
              ),
              SwitchListTile(
                key: const ValueKey('cell-locked'),
                contentPadding: EdgeInsets.zero,
                title: Text(tr('Locked')),
                subtitle: Text(tr('Generating the timetable again keeps this period where it is.')),
                value: _locked,
                onChanged: (v) => setState(() => _locked = v),
              ),
            ],
          ]),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(
          key: const ValueKey('cell-apply'),
          onPressed: () => Navigator.pop(context, (
            cell: _subject == null
                ? null
                : (subjectId: _subject!, teacherId: _teacher, roomId: _room, locked: _locked,
                    coTeacherId: alloc?['coTeacherId'] as String?),
          )),
          child: Text(tr('Apply')),
        ),
      ],
    );
  }
}

