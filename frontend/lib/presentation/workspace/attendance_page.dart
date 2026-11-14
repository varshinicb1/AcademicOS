import 'package:flutter/material.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/shell.dart';
import 'dashboard_card.dart' show friendlyDate;
import 'ops_api.dart';
import 'strings.dart';

/// The words for each status, in the order the register offers them (ATT-1).
const attendanceStatuses = ['present', 'late', 'absent', 'excused'];

String attendanceLabel(String status) => switch (status) {
      'present' => tr('Present'),
      'late' => tr('Late'),
      'absent' => tr('Absent'),
      'excused' => tr('On leave'),
      _ => status,
    };

/// A class's daily register (ATT-1): the class teacher, the section's other
/// teachers and the principal take it for today. A parent hears at once when
/// their child is marked absent.
class AttendanceRegisterPage extends StatefulWidget {
  const AttendanceRegisterPage({super.key});

  @override
  State<AttendanceRegisterPage> createState() => _AttendanceRegisterPageState();
}

class _AttendanceRegisterPageState extends State<AttendanceRegisterPage> {
  Map<String, String>? _sections; // section id -> "10-B", the caller's own
  String? _section;
  Map<String, dynamic>? _register;
  final Map<String, String> _status = {};
  String? _error, _note;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadSections();
  }

  Future<void> _loadSections() async {
    try {
      final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
      if (years.isEmpty) throw OpsError(409, 'Your school has no academic year set up yet.');
      years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
      final yearId = years.last['id'] as String;
      final sections = await Ops.list('/curriculum/academic-years/$yearId/sections');
      final labels = {for (final s in sections) s['id'] as String: '${s['gradeNumber']}-${s['name']}'};
      Set<String> mine;
      if (CurrentSession.role == 'principal') {
        mine = labels.keys.toSet();
      } else {
        final allocs = await Ops.list('/curriculum/academic-years/$yearId/allocations');
        mine = {
          for (final s in sections)
            if (s['classTeacherId'] == CurrentSession.userId) s['id'] as String,
          for (final a in allocs)
            if (a['teacherId'] == CurrentSession.userId) a['sectionId'] as String,
        };
      }
      final ids = mine.toList()..sort((a, b) => (labels[a] ?? a).compareTo(labels[b] ?? b));
      if (!mounted) return;
      setState(() => _sections = {for (final id in ids) id: labels[id] ?? id});
      if (ids.isNotEmpty) _load(ids.first);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _load(String sectionId) async {
    setState(() {
      _section = sectionId;
      _register = null;
      _error = null;
      _note = null;
      _status.clear();
    });
    try {
      final r = await Ops.map('/sections/$sectionId/attendance');
      if (!mounted || _section != sectionId) return;
      setState(() => _take(r));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  void _take(Map<String, dynamic> r) {
    _register = r;
    _status.clear();
    for (final row in (r['rows'] as List).cast<Map>()) {
      // An untaken register starts with everyone present: the teacher marks
      // only the few who are not.
      _status[row['studentId'] as String] = (row['status'] as String?) ?? 'present';
    }
  }

  Future<void> _save() async {
    final sectionId = _section;
    if (sectionId == null) return;
    setState(() {
      _saving = true;
      _error = null;
      _note = null;
    });
    try {
      final r = await Ops.put('/sections/$sectionId/attendance', body: {
        'entries': [for (final e in _status.entries) {'studentId': e.key, 'status': e.value}],
      }) as Map;
      if (!mounted) return;
      final saved = Map<String, dynamic>.from(r);
      final left = (saved['withoutConsent'] as List).cast<String>();
      setState(() {
        _take(saved);
        _note = left.isEmpty
            ? tr('Register saved. Parents of absent students have been told.')
            : '${tr('Register saved, except for students with no parental consent on file')}: ${left.join(', ')}. '
                '${tr('Record their consent under Classes, then save again.')}';
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sections = _sections;
    final r = _register;
    final absent = _status.values.where((s) => s == 'absent').length;
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Class register'))),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (CurrentSession.role == 'principal') SchoolAttendanceOverview(onOpen: _load),
        if (sections == null && _error == null) const SizedBox(height: 120, child: LoadingIndicator()),
        if (sections != null && sections.isEmpty)
          EmptyState(icon: Icons.groups_outlined, title: tr('No classes to take'),
              message: tr('You take the register for the classes you teach or are class teacher of.')),
        if (sections != null && sections.length > 1)
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final e in sections.entries)
              ChoiceChip(label: Text(e.value), selected: _section == e.key, onSelected: (_) => _load(e.key)),
          ]),
        if (_error != null)
          Padding(padding: const EdgeInsets.only(top: 12),
              child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
        if (_section != null && r == null && _error == null) const SizedBox(height: 120, child: LoadingIndicator()),
        if (r != null) ...[
          const SizedBox(height: 12),
          Text('${r['sectionName']} · ${friendlyDate('${r['date']}')}', style: theme.textTheme.titleMedium),
          Text(r['taken'] == true ? tr('Taken. Change any row and save again.') : tr('Not taken yet. Everyone starts as present.'),
              style: theme.textTheme.bodySmall),
          if ((r['rows'] as List).isEmpty)
            Padding(padding: const EdgeInsets.only(top: 12), child: Text(tr('No students in this class yet.'))),
          for (final row in (r['rows'] as List).cast<Map>())
            _StudentRow(
              key: ValueKey('register-${row['studentId']}'),
              name: row['name'] as String,
              status: _status[row['studentId']] ?? 'present',
              onChanged: (s) => setState(() => _status[row['studentId'] as String] = s),
            ),
          if (_note != null)
            Padding(padding: const EdgeInsets.only(top: 12), child: Text(_note!)),
          const SizedBox(height: 16),
          if ((r['rows'] as List).isNotEmpty)
            FilledButton.icon(
              key: const ValueKey('save-register'),
              onPressed: _saving ? null : _save,
              icon: const Icon(Icons.save_outlined),
              label: Text(absent == 0 ? tr('Save: everyone present') : '${tr('Save')}: $absent ${tr('absent')}'),
            ),
        ],
      ]),
    );
  }
}

class _StudentRow extends StatelessWidget {
  final String name;
  final String status;
  final ValueChanged<String> onChanged;
  const _StudentRow({super.key, required this.name, required this.status, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 8, runSpacing: 4, children: [
        SizedBox(width: 160, child: Text(name, overflow: TextOverflow.ellipsis)),
        for (final s in attendanceStatuses)
          ChoiceChip(
            label: Text(attendanceLabel(s)),
            selected: status == s,
            onSelected: (_) => onChanged(s),
          ),
      ]),
    );
  }
}

/// A student's attendance record (ATT-1): the share of days attended, the
/// counts, and the recent days they were not simply present. [path] is the
/// student's own (`/my-attendance-record`) or a parent's child's.
class AttendanceRecordView extends StatelessWidget {
  final String path;
  const AttendanceRecordView({super.key, required this.path});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: Ops.map(path),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!));
        final d = snap.data!;
        if ((d['daysTaken'] as int) == 0) {
          return EmptyState(icon: Icons.how_to_reg_outlined, title: tr('No attendance yet'),
              message: tr('Days appear here once the class teacher takes the register.'));
        }
        final theme = Theme.of(context);
        final counts = Map<String, dynamic>.from(d['counts'] as Map);
        final percent = d['percent'] as num?;
        return ListView(padding: const EdgeInsets.all(16), children: [
          if (percent != null)
            Text('${percent.toStringAsFixed(percent % 1 == 0 ? 0 : 1)}% ${tr('of school days attended')}',
                style: theme.textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text('${d['daysTaken']} ${tr('days taken')} · '
              '${[for (final s in attendanceStatuses) '${counts[s] ?? 0} ${attendanceLabel(s).toLowerCase()}'].join(' · ')}',
              style: theme.textTheme.bodyMedium),
          if ((d['recent'] as List).isNotEmpty) ...[
            SectionHeader(title: tr('Days away or late'), subtitle: tr('Most recent first')),
            for (final day in (d['recent'] as List).cast<Map>())
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(day['status'] == 'absent' ? Icons.event_busy_outlined : Icons.schedule_outlined,
                    color: theme.colorScheme.onSurfaceVariant),
                title: Text(friendlyDate('${day['date']}')),
                subtitle: Text([attendanceLabel('${day['status']}'), if ((day['note'] as String? ?? '').isNotEmpty) day['note']]
                    .join(' · ')),
              ),
          ],
        ]);
      },
    );
  }
}

/// The signed-in student's own attendance.
class MyAttendancePage extends StatelessWidget {
  const MyAttendancePage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: destinationAppBar(context, title: Text(tr('My attendance'))),
        body: const AttendanceRecordView(path: '/my-attendance-record'),
      );
}

/// The principal's view across the school (ATT-1 oversight): today's
/// registers, the classes still to take one, and the students below the
/// attendance floor this year. Tapping a class opens its register below.
class SchoolAttendanceOverview extends StatefulWidget {
  const SchoolAttendanceOverview({super.key, required this.onOpen});

  final void Function(String sectionId) onOpen;

  @override
  State<SchoolAttendanceOverview> createState() => _SchoolAttendanceOverviewState();
}

class _SchoolAttendanceOverviewState extends State<SchoolAttendanceOverview> {
  Map<String, dynamic>? _data;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final d = await Ops.map('/admin/attendance/overview');
      if (mounted) setState(() => _data = d);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (_error != null) {
      return Padding(padding: const EdgeInsets.only(bottom: 12),
          child: Text(_error!, style: TextStyle(color: theme.colorScheme.error)));
    }
    final d = _data;
    if (d == null) return const SizedBox(height: 80, child: LoadingIndicator());
    final sections = (d['sections'] as List).cast<Map>().where((s) => (s['enrolled'] as num) > 0).toList();
    final missing = sections.where((s) => s['taken'] != true).toList();
    final low = (d['belowFloor'] as List).cast<Map>();
    final floor = (d['floor'] as num).toStringAsFixed(0);
    return Card(
      key: const ValueKey('school-attendance'),
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(tr('Across the school today'), style: theme.textTheme.titleMedium),
          const SizedBox(height: 4),
          Text('${sections.length - missing.length}/${sections.length} ${tr('classes taken')} · '
              '${d['awayToday']} ${tr('absent')}'),
          if (missing.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(tr('Not taken yet. Tap a class to take it.'), style: theme.textTheme.bodySmall),
            const SizedBox(height: 4),
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (final s in missing)
                ActionChip(
                  key: ValueKey('missing-${s['sectionId']}'),
                  avatar: const Icon(Icons.pending_actions_outlined, size: 18),
                  label: Text(s['sectionName'] as String),
                  onPressed: () => widget.onOpen(s['sectionId'] as String),
                ),
            ]),
          ],
          const SizedBox(height: 16),
          Text('${tr('Students below the attendance floor this year')} ($floor%): ${d['belowFloorTotal']}',
              style: theme.textTheme.titleSmall),
          if (low.isEmpty)
            Padding(padding: const EdgeInsets.only(top: 4),
                child: Text(tr('Nobody, over at least 10 school days taken.'), style: theme.textTheme.bodySmall)),
          for (final x in low)
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              title: Text(x['name'] as String),
              subtitle: Text('${x['sectionName']} · ${x['daysTaken']} ${tr('days taken')}'),
              trailing: Text('${(x['percent'] as num).toStringAsFixed(0)}%',
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.error)),
            ),
        ]),
      ),
    );
  }
}
