import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../core/download/pdf_saver.dart';
import '../../core/local_engine/local_store.dart';
import '../../core/session/current_session.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'calendar_day_notice.dart';
import 'ops_api.dart';
import 'teacher_homework.dart' show TeachingContext;
import 'strings.dart';
import 'package:academicos/core/theme/app_theme.dart';
import '../shared/widgets/shell.dart';
import 'period_line.dart';

const _base = '/curriculum';

/// How a leave request reads in a list: "full day", "periods 3, 5" (SCH-5).
String leaveKindLabel(Map l) => switch (l['kind']) {
      'periods' => 'periods ${((l['periods'] as List?) ?? const []).join(', ')}',
      'first_half' => '1st half',
      'second_half' => '2nd half',
      _ => 'full day',
    };

/// The content type the leave document route takes for a file's name, or
/// null for a kind it refuses (N-3-17: a PDF, JPEG or PNG of at most 2 MB).
String? leaveDocumentType(String name) {
  final n = name.toLowerCase();
  if (n.endsWith('.pdf')) return 'application/pdf';
  if (n.endsWith('.png')) return 'image/png';
  if (n.endsWith('.jpg') || n.endsWith('.jpeg')) return 'image/jpeg';
  return null;
}

const maxLeaveDocumentBytes = 2 * 1024 * 1024;

/// The principal's morning (SCH-5..9): who is in today, leave waiting for a
/// decision, and every period that needs cover -- with the engine's proposal,
/// the candidates and their reasons, and one tap to assign.
class CoverPage extends StatefulWidget {
  const CoverPage({super.key});

  @override
  State<CoverPage> createState() => _CoverPageState();
}

class _CoverPageState extends State<CoverPage> {
  DateTime _day = DateTime.now();
  Map<String, dynamic>? _attendance;
  List<Map<String, dynamic>> _leave = [];
  List<Map<String, dynamic>> _subs = [];
  TeachingContext? _ctx;
  final Map<String, String> _pending = {};
  String? _error;
  bool _saving = false;

  String get _date => isoDate(_day);

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) {
      if (mounted) setState(() => _ctx = c);
    }, onError: (Object e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    });
    _load();
  }

  Future<void> _load() async {
    try {
      final a = await Ops.map('$_base/teacher-attendance', query: {'date': _date});
      final l = await Ops.list('$_base/leave-requests', query: {'status': 'pending'});
      final s = await Ops.list('$_base/substitutions', query: {'from': _date, 'to': _date});
      if (!mounted) return;
      setState(() {
        _attendance = a;
        _leave = l;
        _subs = s;
        _pending.clear();
        _error = null;
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  String _name(String? id) {
    if (id == null) return '-';
    final row = (_attendance?['rows'] as List? ?? const []).cast<Map>().where((r) => r['teacherId'] == id);
    return row.isEmpty ? id : row.first['name'] as String;
  }

  Future<void> _saveAttendance() async {
    setState(() => _saving = true);
    try {
      final out = await Ops.put('$_base/teacher-attendance', query: {'date': _date}, body: {
        'marks': [for (final e in _pending.entries) {'teacherId': e.key, 'status': e.value}],
      });
      final opened = (out['substitutions'] as List).length;
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(opened == 0
            ? 'Attendance saved'
            : 'Attendance saved. $opened periods need cover; substitutes have been proposed.')));
      }
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _decide(String id, bool approve) async {
    try {
      await Ops.post('$_base/leave-requests/$id/decision', body: {'approve': approve});
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  /// The supporting document a teacher attached to their request (N-3-17).
  Future<void> _openDocument(Map<String, dynamic> leave) async {
    try {
      final bytes = await Ops.bytes('$_base/leave-requests/${leave['id']}/document');
      final doc = Map<String, dynamic>.from(leave['document'] as Map);
      await GetIt.I<PdfSaver>().save(bytes, doc['name'] as String? ?? 'leave-document');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _assign(Map<String, dynamic> sub) async {
    final done = await showDialog<bool>(context: context,
        builder: (_) => _AssignDialog(sub: sub, name: _name));
    if (done == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    const statuses = {
      'present': 'Present', 'late': 'Late', 'absent': 'Absent', 'first_half_absent': 'Absent 1st half',
      'second_half_absent': 'Absent 2nd half',
    };
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Attendance & cover')), actions: [
        // A period run as "Lose the period" is owed; this is where it is paid back.
        IconButton(
          tooltip: tr('Periods owed'),
          icon: const Icon(Icons.restore_outlined),
          onPressed: () => context.push('/school/periods-owed'),
        ),
        TextButton.icon(
          icon: const Icon(Icons.calendar_today),
          label: Text(_date),
          onPressed: () async {
            final d = await showDatePicker(context: context, initialDate: _day,
                firstDate: DateTime.now().subtract(const Duration(days: 60)),
                lastDate: DateTime.now().add(const Duration(days: 60)));
            if (d != null) {
              setState(() => _day = d);
              _load();
            }
          },
        ),
      ]),
      body: _error != null
          ? ErrorDisplay(message: _error!, onRetry: _load)
          : _attendance == null
              ? const LoadingIndicator()
              : ListView(padding: const EdgeInsets.all(16), children: [
                  SectionHeader(
                    title: 'Staff attendance',
                    subtitle: 'Marking someone absent opens cover for their periods at once.',
                    action: FilledButton(
                      onPressed: _pending.isEmpty || _saving ? null : _saveAttendance,
                      child: Text(_pending.isEmpty ? 'Saved' : 'Save ${_pending.length}'),
                    ),
                  ),
                  for (final r in (_attendance!['rows'] as List).cast<Map>())
                    ListTile(
                      title: Text(r['name']),
                      subtitle: r['status'] == 'on_leave' ? const Text('On approved leave') : null,
                      trailing: r['status'] == 'on_leave'
                          ? const ChipTag(label: 'On leave')
                          : DropdownButton<String>(
                              value: _pending[r['teacherId']] ??
                                  (statuses.containsKey(r['status']) ? r['status'] as String : null),
                              hint: const Text('Not marked'),
                              items: [for (final e in statuses.entries)
                                DropdownMenuItem(value: e.key, child: Text(e.value))],
                              onChanged: (v) => setState(() => _pending[r['teacherId'] as String] = v!),
                            ),
                    ),
                  if (_leave.isNotEmpty) ...[
                    const SectionHeader(title: 'Leave waiting for you'),
                    for (final l in _leave)
                      ListTile(
                        title: Text('${_name(l['teacherId'])}: ${l['startDate']}'
                            '${l['endDate'] != l['startDate'] ? ' to ${l['endDate']}' : ''} (${leaveKindLabel(l)})'),
                        subtitle: Text(l['reason'] ?? ''),
                        trailing: Wrap(spacing: 8, children: [
                          if (l['document'] != null)
                            IconButton(
                              key: Key('leave-document-${l['id']}'),
                              tooltip: 'Open ${(l['document'] as Map)['name']}',
                              icon: const Icon(Icons.attach_file),
                              onPressed: () => _openDocument(l),
                            ),
                          OutlinedButton(onPressed: () => _decide(l['id'], false), child: const Text('Reject')),
                          FilledButton(onPressed: () => _decide(l['id'], true), child: const Text('Approve')),
                        ]),
                      ),
                  ],
                  SectionHeader(title: 'Cover on $_date', subtitle: '${_subs.length} periods'),
                  if (_subs.isEmpty) Text('No periods need cover.', style: theme.textTheme.bodySmall),
                  for (final s in _subs)
                    ListTile(
                      leading: CircleAvatar(child: Text('${s['period']}')),
                      title: Text('${_ctx?.sectionLabels[s['sectionId']] ?? s['sectionId']} · '
                          '${_ctx?.subjectNames[s['subjectId']] ?? ''} · for ${_name(s['absentTeacherId'])}'),
                      subtitle: Text(switch (s['status']) {
                        'accepted' => 'Covered by ${_name(s['substituteId'])}',
                        'proposed' => 'Proposed: ${_name(s['substituteId'])} (not accepted yet)',
                        'resolved' => 'Run as ${s['mode']}',
                        'cancelled' => 'Cancelled',
                        _ => 'No substitute yet',
                      }),
                      trailing: s['status'] == 'cancelled' || s['status'] == 'resolved'
                          ? null
                          : TextButton(onPressed: () => _assign(s), child: const Text('Assign')),
                    ),
                ]),
    );
  }
}

class _AssignDialog extends StatefulWidget {
  final Map<String, dynamic> sub;
  final String Function(String?) name;
  const _AssignDialog({required this.sub, required this.name});

  @override
  State<_AssignDialog> createState() => _AssignDialogState();
}

class _AssignDialogState extends State<_AssignDialog> {
  late final Future<List<Map<String, dynamic>>> _cands =
      Ops.list('$_base/substitutions/${widget.sub['id']}/candidates');
  String? _error;

  Future<void> _do(Map<String, dynamic> body) async {
    try {
      await Ops.post('$_base/substitutions/${widget.sub['id']}/assign', body: body);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Period ${widget.sub['period']}: who covers?'),
      content: SizedBox(
        width: 520,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _cands,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const SizedBox(height: 100, child: LoadingIndicator());
            if (snap.hasError) return Text(snap.error.toString());
            return Column(mainAxisSize: MainAxisSize.min, children: [
              if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              if (snap.data!.isEmpty) const Text('Nobody is free this period.'),
              for (final c in snap.data!.take(8))
                ListTile(
                  title: Text(widget.name(c['teacherId'])),
                  subtitle: Text((c['reasons'] as List).join(' · ')),
                  trailing: c['qualified'] == true ? const ChipTag(label: 'Teaches it', color: AppColors.success) : null,
                  onTap: () => _do({'substituteId': c['teacherId']}),
                ),
              const Divider(),
              Wrap(spacing: 8, children: [
                OutlinedButton(onPressed: () => _do({'mode': 'supervised'}), child: const Text('Supervised')),
                OutlinedButton(onPressed: () => _do({'mode': 'combined'}), child: const Text('Combine classes')),
                OutlinedButton(onPressed: () => _do({'mode': 'lost'}), child: const Text('Lose the period')),
              ]),
            ]);
          },
        ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
    );
  }
}

/// A teacher's day (SCH-9 check-in, SCH-6 duties): today's periods as they
/// will run, substitution duties to accept or decline, and "I'm here".
class MyDayPage extends StatefulWidget {
  const MyDayPage({super.key});

  @override
  State<MyDayPage> createState() => _MyDayPageState();
}

class _MyDayPageState extends State<MyDayPage> {
  List<Map<String, dynamic>>? _rows;
  List<Map<String, dynamic>> _duties = [];
  List<Map<String, dynamic>> _leave = [];
  List<Map<String, dynamic>> _lessons = [];
  // The calendar's word on today: a holiday, a half day, an exam window.
  List<Map<String, dynamic>> _calendarDay = [];
  TeachingContext? _ctx;
  String? _error;
  // The school's class and subject labels failing to load no longer blanks
  // the day: each row carries its own names, so the day shows with a note.
  String? _ctxError;
  // Today's mark: the register's own row (GET my-attendance), so a check-in
  // made on another device, or the principal's mark, shows too. Kept on this
  // device as well, so the button reads right before the load answers
  // (QA S-12: "I'm here" was offered again every time My day opened).
  late String? _checkedIn = LocalStore.instance.checkInFor(CurrentSession.userId, _today);

  String get _today => isoDate(DateTime.now());

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) {
      if (mounted) setState(() => _ctx = c);
    }, onError: (Object e) {
      if (mounted) setState(() => _ctxError = serverErrorMessage(e));
    });
    _load();
  }

  Future<void> _load() async {
    try {
      final rows = (await Ops.get('$_base/my-day', query: {'date': _today}) as List)
          .map((e) => Map<String, dynamic>.from(e as Map)).toList();
      final duties = await Ops.list('$_base/substitutions', query: {'from': _today,
        'to': isoDate(DateTime.now().add(const Duration(days: 7)))});
      final leave = await Ops.list('$_base/leave-requests');
      final lessons = await Ops.list('$_base/my-schedule', query: {'start_date': _today, 'end_date': _today});
      final calendar = await Ops.list('/my-calendar', query: {'days': 1});
      final mine = await Ops.map('$_base/my-attendance');
      final mark = mine['status'] as String?;
      if (mark != null && mark != 'unmarked' && mark != 'on_leave') {
        LocalStore.instance.setCheckIn(CurrentSession.userId, _today, mark);
      }
      if (!mounted) return;
      setState(() {
        if (mark != null && mark != 'unmarked' && mark != 'on_leave') _checkedIn = mark;
        _rows = rows;
        _calendarDay = calendarDayItems(calendar, _today);
        _duties = duties;
        _lessons = lessons;
        _leave = leave.where((l) => l['teacherId'] == CurrentSession.userId &&
            (l['endDate'] as String).compareTo(_today) >= 0).toList();
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  /// Leave in three taps (TA-3): Apply for leave, Today or Tomorrow, Apply.
  /// Today is chosen when the dialog opens; other days are one more tap.
  Future<void> _applyForLeave() async {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final tomorrow = today.add(const Duration(days: 1));
    DateTimeRange? range = DateTimeRange(start: today, end: today);
    var pick = 'today';
    var kind = 'full_day';
    final reason = TextEditingController();
    final handover = TextEditingController();
    // Named periods (SCH-5): the teacher's own periods on the day, from their
    // week; the API took kind 'periods' but the web offered only halves.
    final named = <int>{};
    Map<String, dynamic>? week;
    String? weekError;
    try {
      week = await Ops.map('$_base/my-timetable');
    } catch (e) {
      weekError = serverErrorMessage(e);
    }
    List<int> periodsOn(DateTime day) {
      final mine = <int>{
        for (final e in ((week?['entries'] as List?) ?? const []).cast<Map>())
          if (e['dayOfWeek'] == day.weekday - 1) e['period'] as int,
      };
      if (mine.isNotEmpty) return mine.toList()..sort();
      final bell = <int>{
        for (final s in (((week?['bellSchedule'] as Map?)?['slots'] as List?) ?? const []).cast<Map>())
          if (s['period'] != null) s['period'] as int,
      };
      return bell.isNotEmpty ? (bell.toList()..sort()) : [for (var p = 1; p <= 8; p++) p];
    }
    // An optional supporting document (N-3-17), sent once the request exists.
    String? docName;
    Uint8List? docBytes;
    String? docError;
    if (!mounted) return;
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
      title: Text(tr('Apply for leave')),
      content: SizedBox(width: 440, child: Column(mainAxisSize: MainAxisSize.min, children: [
        Wrap(spacing: 8, runSpacing: 8, children: [
          ChoiceChip(
            key: const Key('leave-today'),
            label: Text(tr('Today')),
            selected: pick == 'today',
            onSelected: (_) => set(() {
              pick = 'today';
              range = DateTimeRange(start: today, end: today);
            }),
          ),
          ChoiceChip(
            key: const Key('leave-tomorrow'),
            label: Text(tr('Tomorrow')),
            selected: pick == 'tomorrow',
            onSelected: (_) => set(() {
              pick = 'tomorrow';
              range = DateTimeRange(start: tomorrow, end: tomorrow);
            }),
          ),
          ChoiceChip(
            key: const Key('leave-other'),
            avatar: const Icon(Icons.date_range, size: 18),
            label: Text(pick == 'other' && range != null
                ? '${isoDate(range!.start)} – ${isoDate(range!.end)}'
                : tr('Other days')),
            selected: pick == 'other',
            onSelected: (_) async {
              final r = await showDateRangePicker(context: ctx, firstDate: today.subtract(const Duration(days: 1)),
                  lastDate: today.add(const Duration(days: 180)));
              if (r != null) {
                set(() {
                  pick = 'other';
                  range = r;
                });
              }
            },
          ),
        ]),
        const SizedBox(height: 12),
        // Chips, not a segmented button: four choices do not fit a phone's dialog.
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final k in const {'full_day': 'Full day', 'first_half': '1st half', 'second_half': '2nd half',
            'periods': 'Periods'}.entries)
            ChoiceChip(
              key: Key('leave-kind-${k.key}'),
              label: Text(tr(k.value)),
              selected: kind == k.key,
              onSelected: (_) => set(() => kind = k.key),
            ),
        ]),
        if (kind == 'periods') ...[
          const SizedBox(height: 8),
          if (range != null && isoDate(range!.start) != isoDate(range!.end))
            Text(tr('Named periods are one day\'s leave: choose a single day.'),
                style: TextStyle(color: Theme.of(ctx).colorScheme.error))
          else if (range != null) ...[
            if (weekError != null) Text(weekError, style: Theme.of(ctx).textTheme.bodySmall),
            Wrap(spacing: 6, runSpacing: 6, children: [
              for (final p in periodsOn(range!.start))
                FilterChip(
                  key: Key('leave-period-$p'),
                  label: Text('P$p'),
                  selected: named.contains(p),
                  onSelected: (on) => set(() => on ? named.add(p) : named.remove(p)),
                ),
            ]),
          ],
        ],
        TextField(controller: reason, decoration: InputDecoration(labelText: tr('Reason (optional)'))),
        TextField(controller: handover, minLines: 2, maxLines: 4,
            decoration: InputDecoration(labelText: tr('Note for whoever covers (optional)'))),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: OutlinedButton.icon(
            key: const Key('leave-attach'),
            icon: const Icon(Icons.attach_file),
            label: Text(docName ?? tr('Attach a document (optional)'), overflow: TextOverflow.ellipsis),
            onPressed: () async {
              try {
                final picked = await FilePicker.pickFiles(type: FileType.custom,
                    allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png']);
                if (picked == null || picked.files.isEmpty) return;
                final f = picked.files.single;
                final bytes = await f.readAsBytes();
                set(() {
                  if (leaveDocumentType(f.name) == null) {
                    docError = tr('Attach a PDF, or a JPEG or PNG photo.');
                  } else if (bytes.length > maxLeaveDocumentBytes) {
                    docError = tr('A document may be at most 2 MB.');
                  } else {
                    docName = f.name;
                    docBytes = bytes;
                    docError = null;
                  }
                });
              } catch (e) {
                set(() => docError = serverErrorMessage(e));
              }
            },
          ),
        ),
        if (docError != null)
          Text(docError!, style: TextStyle(color: Theme.of(ctx).colorScheme.error)),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(
            key: const Key('leave-apply'),
            onPressed: range == null ||
                    (kind == 'periods' && (named.isEmpty || isoDate(range!.start) != isoDate(range!.end)))
                ? null
                : () => Navigator.pop(ctx, true),
            child: Text(tr('Apply'))),
      ],
    )));
    if (ok != true || range == null) return;
    Map<String, dynamic> leave;
    try {
      leave = Map<String, dynamic>.from(await Ops.post('$_base/leave-requests', body: {
        'startDate': isoDate(range!.start), 'endDate': isoDate(range!.end), 'kind': kind,
        if (kind == 'periods') 'periods': (named.toList()..sort()),
        'reason': reason.text.trim().isEmpty ? 'Leave' : reason.text.trim(),
        if (handover.text.trim().isNotEmpty) 'handoverNote': handover.text.trim(),
      }) as Map);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
      return;
    }
    var said = tr('Leave applied; the principal has been asked');
    if (docBytes != null && leave['id'] != null) {
      final type = leaveDocumentType(docName!)!.split('/');
      try {
        await GetIt.I<Dio>().post('$_base/leave-requests/${leave['id']}/document',
            data: FormData.fromMap({
              'file': MultipartFile.fromBytes(docBytes!, filename: docName, contentType: DioMediaType(type[0], type[1])),
            }));
      } catch (e) {
        said = '$said. ${tr('The document was not attached')}: ${serverErrorMessage(e)}';
      }
    }
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(said)));
    _load();
  }

  /// Mark today's lesson taught, partly taught or not (TA-1). Not taught or
  /// partly taught plans the subtopic again at the next free period.
  Future<void> _markLesson(String id, String status) async {
    String? note;
    if (status == 'skipped' || status == 'partly') {
      final c = TextEditingController();
      final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
        title: Text(status == 'skipped' ? tr('Why was it not taught?') : tr('What is left to teach?')),
        content: TextField(controller: c, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(tr('Save'))),
        ],
      ));
      if (ok != true) return;
      note = c.text.trim().isEmpty ? null : c.text.trim();
    }
    try {
      await Ops.send('PATCH', '$_base/scheduled-lessons/$id', body: {'status': status, if (note != null) 'note': note},
          label: 'Lesson marked $status');
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _cancelLeave(String id) async {
    try {
      await Ops.post('$_base/leave-requests/$id/cancel');
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _checkIn() async {
    try {
      final r = await Ops.post('$_base/my-attendance');
      final status = r['status'] as String;
      LocalStore.instance.setCheckIn(CurrentSession.userId, _today, status);
      if (mounted) setState(() => _checkedIn = status);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _respond(String id, bool accept) async {
    try {
      await Ops.send('POST', '$_base/substitutions/$id/respond', body: {'accept': accept},
          label: accept ? 'Accept cover' : 'Decline cover');
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    const kinds = {
      'regular': 'Your period', 'substitute': 'Covering', 'supervised': 'Supervising', 'combined': 'Combined class',
      'away': 'On leave', 'makeup': 'Make-up period', 'lost': 'Cancelled', 'uncovered': 'Needs cover',
      'exam': 'Exam', 'co_teacher': 'Co-teacher away',
    };
    final pending = _duties.where((d) => d['status'] == 'proposed').toList();
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('My day')), actions: [
        FilledButton.tonalIcon(
          key: const Key('check-in'),
          onPressed: _checkedIn == null ? _checkIn : null,
          icon: const Icon(Icons.how_to_reg),
          label: Text(_checkedIn == null ? "I'm here" : 'Marked ${_checkedIn!.replaceAll('_', ' ')}'),
        ),
        const SizedBox(width: 12),
      ]),
      body: _error != null
          ? ErrorDisplay(message: _error!, onRetry: _load)
          : _rows == null
              ? const LoadingIndicator()
              : ListView(padding: const EdgeInsets.all(16), children: [
                  CalendarDayNotice(_calendarDay),
                  if (_ctxError != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(_ctxError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                    ),
                  if (pending.isNotEmpty) ...[
                    SectionHeader(title: tr('Cover asked of you')),
                    for (final d in pending)
                      // The buttons go under the text, not beside it: three of
                      // them in `trailing` left a 390 px phone a one-word-wide
                      // title (re-measure, 2026-10-01).
                      ListTile(
                        title: Text('${d['date']} · period ${d['period']} · '
                            '${_ctx?.sectionLabels[d['sectionId']] ?? d['sectionId']}'),
                        subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text([
                            _ctx?.subjectNames[d['subjectId']] ?? '',
                            if (d['handoverNote'] != null) '${tr('Note')}: ${d['handoverNote']}',
                          ].where((s) => s.isNotEmpty).join('\n')),
                          const SizedBox(height: 8),
                          Wrap(spacing: 8, runSpacing: 6, children: [
                            OutlinedButton(onPressed: () => _respond(d['id'], false), child: Text(tr('Decline'))),
                            FilledButton(onPressed: () => _respond(d['id'], true), child: Text(tr('Accept'))),
                          ]),
                        ]),
                      ),
                  ],
                  if (_lessons.isNotEmpty) ...[
                    SectionHeader(title: tr("Today's lessons")),
                    for (final l in _lessons)
                      ListTile(
                        title: Text('${l['sectionName'] ?? ''} ${l['subjectName']}: ${l['subtopicName']}'),
                        subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('${l['chapterName']} · ${l['topicName']}'),
                          const SizedBox(height: 8),
                          l['status'] == 'scheduled'
                              ? Wrap(spacing: 6, runSpacing: 6, children: [
                                  OutlinedButton(onPressed: () => _markLesson(l['lessonId'] as String, 'skipped'),
                                      child: Text(tr('Not taught'))),
                                  OutlinedButton(onPressed: () => _markLesson(l['lessonId'] as String, 'partly'),
                                      child: Text(tr('Partly'))),
                                  FilledButton(onPressed: () => _markLesson(l['lessonId'] as String, 'completed'),
                                      child: Text(tr('Taught'))),
                                ])
                              : ChipTag(label: l['status'] == 'skipped'
                                  ? tr('Not taught')
                                  : (l['note'] as String? ?? '').startsWith('Partly') ? tr('Partly taught') : tr('Taught')),
                        ]),
                      ),
                  ],
                  SectionHeader(
                    title: 'My leave',
                    action: OutlinedButton.icon(onPressed: _applyForLeave, icon: const Icon(Icons.event_busy),
                        label: Text(tr('Apply for leave'))),
                  ),
                  for (final l in _leave)
                    ListTile(
                      dense: true,
                      title: Text('${l['startDate']}${l['endDate'] != l['startDate'] ? ' to ${l['endDate']}' : ''} · '
                          '${leaveKindLabel(l)}${l['document'] != null ? ' · ${tr('document attached')}' : ''}'),
                      subtitle: Text(l['reason'] ?? ''),
                      trailing: Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                        ChipTag(label: l['status'] as String),
                        if (l['status'] == 'pending' || l['status'] == 'approved')
                          TextButton(onPressed: () => _cancelLeave(l['id'] as String), child: Text(tr('Cancel'))),
                      ]),
                    ),
                  SectionHeader(
                    title: tr('Today'),
                    subtitle: [
                      '${_rows!.length} periods',
                      if (_rows!.any((r) => r['changed'] == true))
                        '${_rows!.where((r) => r['changed'] == true).length} ${tr('changed')}',
                      nextPeriodLine(_rows!.cast<Map>(), DateTime.now(),
                              what: (r) => r['sectionName'] as String? ?? '') ??
                          '',
                    ].where((s) => s.isNotEmpty).join(' · '),
                  ),
                  if (_rows!.isEmpty) const Text('No periods today.'),
                  for (final r in _rows!)
                    ListTile(
                      leading: CircleAvatar(child: Text('${r['period']}')),
                      title: Text('${r['sectionName'] ?? _ctx?.sectionLabels[r['sectionId']] ?? r['sectionId']} · '
                          '${r['subjectName'] ?? _ctx?.subjectNames[r['subjectId']] ?? ''}'),
                      subtitle: Text([
                        periodWhenWhere(r),
                        if (r['note'] != null && r['kind'] != 'regular') r['note'] as String,
                      ].where((s) => s.isNotEmpty).join(' · ')),
                      trailing: ChipTag(
                          label: kinds[r['kind']] ?? r['kind'],
                          color: r['changed'] == true ? Theme.of(context).colorScheme.tertiary : null),
                    ),
                ]),
    );
  }
}
