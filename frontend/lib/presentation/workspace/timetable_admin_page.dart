import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

const _base = '/curriculum';
const _dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const roomKinds = ['classroom', 'lab', 'hall', 'other'];

/// A bell typed as lines, one slot a line: "08:00-08:45" is a teaching
/// period, "11:00-11:20 break" (or assembly, zero) is not. Returns the slots
/// the bell-schedule route takes, or throws [FormatException] naming the
/// line. The server checks order and overlap; this only reads the text.
List<Map<String, String>> parseBellSlots(String text) {
  final slots = <Map<String, String>>[];
  final line = RegExp(r'^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})(?:\s+(teaching|break|assembly|zero))?$');
  var n = 0;
  for (final raw in text.split('\n')) {
    final t = raw.trim();
    n++;
    if (t.isEmpty) continue;
    final m = line.firstMatch(t);
    if (m == null) {
      throw FormatException('Line $n: write a slot as 08:00-08:45, or 11:00-11:20 break');
    }
    String hhmm(String v) => v.length == 4 ? '0$v' : v;
    slots.add({'start': hhmm(m.group(1)!), 'end': hhmm(m.group(2)!), 'kind': m.group(3) ?? 'teaching'});
  }
  if (slots.isEmpty) throw const FormatException('Add at least one slot, such as 08:00-08:45');
  return slots;
}

/// The same bell back as lines, for editing.
String bellSlotsText(List<dynamic> slots) => [
      for (final s in slots.cast<Map>())
        '${s['start']}-${s['end']}${s['kind'] == 'teaching' ? '' : ' ${s['kind']}'}'
    ].join('\n');

/// The school's timetable, set up in one place (REQUIREMENTS SCH-2/3,
/// ADM-1): who teaches what to which section (with a co-teacher, a lab and
/// double periods, SCH-8), the rooms and when a room is out of use, the
/// bell, the generated week with its changes shown before publishing, and
/// each section's week. For the principal, and a teacher given the timetable
/// admin permission (M1.4).
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
      length: 5,
      child: Scaffold(
        appBar: AppBar(
          title: Text(tr('Timetable')),
          bottom: TabBar(isScrollable: true, tabs: [
            Tab(text: tr('Allocations')),
            Tab(text: tr('Rooms')),
            Tab(text: tr('Bell')),
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
              _RoomsTab(data: data),
              _BellTab(data: data),
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
        decoration: InputDecoration(labelText: tr('Section'), border: const OutlineInputBorder()),
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
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
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
                decoration: InputDecoration(labelText: tr('Periods a week'), border: const OutlineInputBorder()),
              ),
            ),
            SizedBox(
              width: 180,
              child: DropdownButtonFormField<String?>(
                key: ValueKey('alloc-room-$id'),
                initialValue: _roomKind,
                isExpanded: true,
                decoration: InputDecoration(labelText: tr('Needs a room'), border: const OutlineInputBorder()),
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
                decoration: InputDecoration(labelText: tr('Double periods'), border: const OutlineInputBorder()),
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
    final bells = await Ops.list('$_base/academic-years/${widget.data.yearId}/bell-schedules')
        .catchError((Object e) {
      setState(() => _error = serverErrorMessage(e));
      return <Map<String, dynamic>>[];
    });
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
    final List<Map<String, String>> slots;
    try {
      slots = parseBellSlots(_slots.text);
    } on FormatException catch (e) {
      setState(() => _error = e.message);
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
              decoration: InputDecoration(labelText: tr('Name'), border: const OutlineInputBorder())),
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
              border: const OutlineInputBorder(),
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

  Future<void> _solve({required bool apply}) async {
    final maxDay = int.tryParse(_maxDay.text.trim()), maxRow = int.tryParse(_maxRow.text.trim());
    if (maxDay == null || maxDay < 1 || maxDay > 12 || maxRow == null || maxRow < 1 || maxRow > 12) {
      setState(() => _error = tr('A teacher\'s most a day and in a row are whole numbers from 1 to 12.'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final r = await Ops.post('$_base/academic-years/${widget.data.yearId}/timetable/solve', body: {
        'apply': apply,
        'keepExisting': _keep,
        'maxPerDay': maxDay,
        'maxConsecutive': maxRow,
        'timeLimitSeconds': 60,
      });
      if (mounted) setState(() => _result = Map<String, dynamic>.from(r as Map));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = _result;
    final solved = r?['status'] == 'solved';
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text(tr('Generate a clash-free week for every section from the allocations, rooms and bell. '
          'Preview first: nothing changes until you publish.'), style: theme.textTheme.bodySmall),
      const Gap(12),
      Wrap(spacing: 12, runSpacing: 12, children: [
        SizedBox(width: 180, child: TextField(key: const ValueKey('solve-max-day'), controller: _maxDay,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(labelText: tr('Most a day per teacher'), border: const OutlineInputBorder()))),
        SizedBox(width: 180, child: TextField(key: const ValueKey('solve-max-row'), controller: _maxRow,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(labelText: tr('Most in a row'), border: const OutlineInputBorder()))),
      ]),
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: Text(tr('Keep the current week where possible')),
        value: _keep,
        onChanged: (v) => setState(() => _keep = v),
      ),
      if (_error != null) ...[_errorText(context, _error!), const Gap(8)],
      Wrap(spacing: 8, children: [
        FilledButton.tonal(key: const ValueKey('solve-preview'), onPressed: _busy ? null : () => _solve(apply: false),
            style: phoneTapTarget(context), child: Text(tr('Preview'))),
        FilledButton(key: const ValueKey('solve-publish'), onPressed: _busy || !solved || r?['applied'] == true
            ? null : () => _solve(apply: true),
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
      ],
    ]);
  }
}

// ------------------------------------------------------------------ week

class _WeekTab extends StatefulWidget {
  final _SchoolData data;
  const _WeekTab({required this.data});

  @override
  State<_WeekTab> createState() => _WeekTabState();
}

class _WeekTabState extends State<_WeekTab> {
  String? _sectionId;
  Future<(Map<String, dynamic>, Map<String, dynamic>?)>? _future;

  Future<(Map<String, dynamic>, Map<String, dynamic>?)> _load(String sectionId) async {
    final week = await Ops.map('$_base/sections/$sectionId/timetable');
    final bells = await Ops.list('$_base/academic-years/${widget.data.yearId}/bell-schedules');
    return (week, bells.where((b) => b['id'] == week['bellScheduleId']).firstOrNull);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(padding: const EdgeInsets.all(16), children: [
      DropdownButtonFormField<String>(
        key: const ValueKey('week-section'),
        initialValue: _sectionId,
        isExpanded: true,
        decoration: InputDecoration(labelText: tr('Section'), border: const OutlineInputBorder()),
        items: [
          for (final s in widget.data.sections)
            DropdownMenuItem(value: s['id'] as String, child: Text(widget.data.sectionLabel(s['id'] as String))),
        ],
        onChanged: (id) => setState(() {
          _sectionId = id;
          _future = id == null ? null : _load(id);
        }),
      ),
      const Gap(12),
      if (_future != null)
        FutureBuilder(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
            if (snap.hasError) return _errorText(context, serverErrorMessage(snap.error!));
            final (week, bell) = snap.data!;
            if (bell == null) return Text(tr('Set up the bell first.'));
            final entries = (week['entries'] as List).cast<Map>();
            final days = (bell['days'] as List).cast<int>();
            final periods = bell['teachingPeriods'] as int;
            String cell(int d, int p) {
              final e = entries.where((x) => x['dayOfWeek'] == d && x['period'] == p).firstOrNull;
              if (e == null) return '';
              return [
                e['subjectName'] ?? '',
                e['teacherName'] ?? '',
                if (e['coTeacherName'] != null) '+ ${e['coTeacherName']}',
                if (e['roomName'] != null) e['roomName'],
              ].where((s) => '$s'.isNotEmpty).join('\n');
            }
            final gaps = (week['gaps'] as List).cast<Map>().where((g) => g['timetabled'] != g['allocated']);
            return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  key: const ValueKey('week-grid'),
                  dataRowMaxHeight: 88,
                  columns: [const DataColumn(label: Text('')), for (final d in days) DataColumn(label: Text(tr(_dayNames[d])))],
                  rows: [
                    for (var p = 1; p <= periods; p++)
                      DataRow(cells: [
                        DataCell(Text('P$p')),
                        for (final d in days) DataCell(Text(cell(d, p), style: theme.textTheme.bodySmall)),
                      ]),
                  ],
                ),
              ),
              for (final g in gaps)
                Text('${tr('Still to place')}: ${g['timetabled']} ${tr('of')} ${g['allocated']} '
                    '${tr('periods a week for a subject')}'),
            ]);
          },
        ),
    ]);
  }
}
