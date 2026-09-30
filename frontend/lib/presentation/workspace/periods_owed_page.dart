import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'notice.dart';
import 'ops_api.dart';
import 'strings.dart';

const _base = '/curriculum';
const _weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/// "2026-10-05 (Mon)".
String _day(String iso) {
  final d = DateTime.tryParse(iso);
  return d == null ? iso : '$iso (${tr(_weekdays[d.weekday - 1])})';
}

class _CoverSchool {
  final String yearId;
  final String start;
  final String end;
  final List<Map<String, dynamic>> sections;
  final Map<String, String> subjectNames;
  const _CoverSchool(this.yearId, this.start, this.end, this.sections, this.subjectNames);

  String sectionLabel(String id) {
    final s = sections.where((x) => x['id'] == id).firstOrNull;
    return s == null ? id : '${s['gradeNumber']}-${s['name']}';
  }

  String subjectName(String id) => subjectNames[id] ?? id;
}

/// Periods owed (SCH-7, audit N-3-11): a period lost to an absence with no
/// substitute, a supervised or combined class, or a closure is a debt of
/// its section and subject. Here the school pays it back: each owed period
/// with the make-up slots the engine proposes (the section free, its teacher
/// free and under the day's maximum), or waived with a reason; a short-notice
/// closure for the whole school or some classes; and the year's cover
/// figures with the debt per section and subject. Until this page the web
/// could only create the debt ("Lose the period") and never recover it.
class PeriodsOwedPage extends StatefulWidget {
  const PeriodsOwedPage({super.key});

  @override
  State<PeriodsOwedPage> createState() => _PeriodsOwedPageState();
}

class _PeriodsOwedPageState extends State<PeriodsOwedPage> {
  late Future<_CoverSchool> _future = _load();

  static Future<_CoverSchool> _load() async {
    final years = await Ops.list('$_base/academic-years', query: {'school_id': CurrentSession.schoolId});
    if (years.isEmpty) throw OpsError(409, tr('Your school has no academic year set up yet.'));
    years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
    final year = years.last;
    final yearId = year['id'] as String;
    final sections = await Ops.list('$_base/academic-years/$yearId/sections');
    final names = <String, String>{};
    for (final g in {for (final s in sections) s['gradeId'] as String}) {
      for (final subj in await Ops.list('$_base/grades/$g/subjects')) {
        names[subj['id'] as String] = subj['name'] as String;
      }
    }
    return _CoverSchool(yearId, year['startDate'] as String, year['endDate'] as String, sections, names);
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(tr('Periods owed')),
          bottom: TabBar(isScrollable: true, tabs: [
            Tab(text: tr('Owed')),
            Tab(text: tr('Close a day')),
            Tab(text: tr('The year')),
          ]),
        ),
        body: FutureBuilder<_CoverSchool>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
            if (snap.hasError) {
              return ErrorDisplay(message: serverErrorMessage(snap.error!),
                  onRetry: () => setState(() { _future = _load(); }));
            }
            final school = snap.data!;
            return TabBarView(children: [
              _OwedTab(school: school),
              _ClosureTab(school: school),
              _YearTab(school: school),
            ]);
          },
        ),
      ),
    );
  }
}

// ------------------------------------------------------------------ owed

class _OwedTab extends StatefulWidget {
  final _CoverSchool school;
  const _OwedTab({required this.school});

  @override
  State<_OwedTab> createState() => _OwedTabState();
}

class _OwedTabState extends State<_OwedTab> {
  String _status = 'owed';
  late Future<List<Map<String, dynamic>>> _future = _load();

  Future<List<Map<String, dynamic>>> _load() =>
      Ops.list('$_base/academic-years/${widget.school.yearId}/lost-periods', query: {'status': _status});

  void _reload() => setState(() { _future = _load(); });

  Future<void> _makeUp(Map<String, dynamic> lost) async {
    final done = await showDialog<bool>(context: context, builder: (_) => _MakeUpDialog(lost: lost));
    if (done == true) _reload();
  }

  Future<void> _waive(Map<String, dynamic> lost) async {
    final done = await showDialog<bool>(context: context, builder: (_) => _WaiveDialog(lost: lost));
    if (done == true) _reload();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final school = widget.school;
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text(tr('A period lost to an absence with no subject teacher, or to a closure, is owed to its section. '
          'Make it up in a free period, or waive it with a reason.'), style: theme.textTheme.bodySmall),
      const Gap(12),
      SegmentedButton<String>(
        key: const ValueKey('owed-status'),
        segments: [
          ButtonSegment(value: 'owed', label: Text(tr('Owed'))),
          ButtonSegment(value: 'compensated', label: Text(tr('Made up'))),
          ButtonSegment(value: 'waived', label: Text(tr('Waived'))),
        ],
        selected: {_status},
        style: phoneSegmentTapTarget(context),
        onSelectionChanged: (v) => setState(() {
          _status = v.first;
          _future = _load();
        }),
      ),
      const Gap(12),
      FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
          if (snap.hasError) {
            return Notice(kind: NoticeKind.danger, title: serverErrorMessage(snap.error!),
                action: OutlinedButton(onPressed: _reload, child: Text(tr('Try again'))));
          }
          final rows = snap.data!;
          if (rows.isEmpty) {
            return Text(
              switch (_status) {
                'owed' => tr('Nothing is owed: every lost period has been made up or waived.'),
                'compensated' => tr('No period has been made up yet.'),
                _ => tr('No period has been waived.'),
              },
              key: const ValueKey('owed-empty'),
              style: theme.textTheme.bodyMedium,
            );
          }
          // One card per section and subject: the debt is theirs.
          final groups = <String, List<Map<String, dynamic>>>{};
          for (final r in rows) {
            groups.putIfAbsent('${r['sectionId']}|${r['subjectId']}', () => []).add(r);
          }
          final keys = groups.keys.toList()
            ..sort((a, b) => school.sectionLabel(a.split('|')[0]).compareTo(school.sectionLabel(b.split('|')[0])));
          return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            for (final k in keys)
              AppCard(
                key: ValueKey('owed-group-$k'),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${school.sectionLabel(k.split('|')[0])} · ${school.subjectName(k.split('|')[1])}: '
                      '${groups[k]!.length} ${switch (_status) {
                        'owed' => tr('owed'),
                        'compensated' => tr('made up'),
                        _ => tr('waived'),
                      }}', style: theme.textTheme.titleSmall),
                  const Gap(4),
                  for (final lost in groups[k]!..sort((a, b) => '${a['date']}${a['period']}'.compareTo('${b['date']}${b['period']}')))
                    _LostRow(lost: lost, onMakeUp: () => _makeUp(lost), onWaive: () => _waive(lost)),
                ]),
              ),
          ]);
        },
      ),
    ]);
  }
}

class _LostRow extends StatelessWidget {
  final Map<String, dynamic> lost;
  final VoidCallback onMakeUp;
  final VoidCallback onWaive;
  const _LostRow({required this.lost, required this.onMakeUp, required this.onWaive});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final id = lost['id'];
    final status = lost['status'];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Wrap(
        spacing: 8,
        runSpacing: 4,
        crossAxisAlignment: WrapCrossAlignment.center,
        alignment: WrapAlignment.spaceBetween,
        children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
            Text('${_day(lost['date'] as String)} · ${tr('period')} ${lost['period']}', style: theme.textTheme.bodyMedium),
            Text(
              status == 'compensated'
                  ? '${tr('Made up on')} ${_day(lost['compensationDate'] as String)} · ${tr('period')} ${lost['compensationPeriod']}'
                  : '${lost['reason']}',
              style: theme.textTheme.bodySmall,
            ),
          ]),
          if (status == 'owed')
            Wrap(spacing: 8, children: [
              TextButton(key: ValueKey('owed-waive-$id'), onPressed: onWaive, style: phoneTapTarget(context),
                  child: Text(tr('Waive'))),
              OutlinedButton(key: ValueKey('owed-makeup-$id'), onPressed: onMakeUp, style: phoneTapTarget(context),
                  child: Text(tr('Make up'))),
            ]),
        ],
      ),
    );
  }
}

class _MakeUpDialog extends StatefulWidget {
  final Map<String, dynamic> lost;
  const _MakeUpDialog({required this.lost});

  @override
  State<_MakeUpDialog> createState() => _MakeUpDialogState();
}

class _MakeUpDialogState extends State<_MakeUpDialog> {
  late final Future<List<Map<String, dynamic>>> _options =
      Ops.list('$_base/lost-periods/${widget.lost['id']}/compensation-options');
  Map<String, dynamic>? _picked;
  bool _busy = false;
  String? _error;

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Ops.post('$_base/lost-periods/${widget.lost['id']}/compensate',
          body: {'date': _picked!['date'], 'period': _picked!['period']});
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${tr('Make up')} ${_day(widget.lost['date'] as String)} · ${tr('period')} ${widget.lost['period']}'),
      content: SizedBox(
        width: 480,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _options,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const SizedBox(height: 80, child: LoadingIndicator());
            if (snap.hasError) return Notice(kind: NoticeKind.danger, title: serverErrorMessage(snap.error!));
            final options = snap.data!;
            return SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(options.isEmpty
                    ? tr('No period in the next three weeks has both the section and its teacher free.')
                    : tr('Periods in the next three weeks when the section and its teacher are both free:'),
                    style: Theme.of(context).textTheme.bodySmall),
                const Gap(8),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  for (final o in options)
                    ChoiceChip(
                      key: ValueKey('makeup-${o['date']}-${o['period']}'),
                      label: Text('${_day(o['date'] as String)} · P${o['period']}'),
                      selected: _picked == o,
                      onSelected: (v) => setState(() => _picked = v ? o : null),
                    ),
                ]),
                if (_error != null) ...[const Gap(12), Notice(kind: NoticeKind.danger, title: _error!)],
              ]),
            );
          },
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(key: const ValueKey('makeup-save'), onPressed: _picked == null || _busy ? null : _save,
            child: Text(tr('Make it up then'))),
      ],
    );
  }
}

class _WaiveDialog extends StatefulWidget {
  final Map<String, dynamic> lost;
  const _WaiveDialog({required this.lost});

  @override
  State<_WaiveDialog> createState() => _WaiveDialogState();
}

class _WaiveDialogState extends State<_WaiveDialog> {
  final _reason = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _reason.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Ops.post('$_base/lost-periods/${widget.lost['id']}/waive', body: {'reason': _reason.text.trim()});
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${tr('Waive')} ${_day(widget.lost['date'] as String)} · ${tr('period')} ${widget.lost['period']}'),
      content: SizedBox(
        width: 440,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(tr('The section will not get this period back. Say why; it is kept in the audit log.'),
              style: Theme.of(context).textTheme.bodySmall),
          const Gap(8),
          TextField(
            key: const ValueKey('waive-reason'),
            controller: _reason,
            autofocus: true,
            maxLength: 500,
            decoration: InputDecoration(labelText: tr('Reason'), hintText: tr('Covered in the revision week')),
            onChanged: (_) => setState(() {}),
          ),
          if (_error != null) ...[const Gap(8), Notice(kind: NoticeKind.danger, title: _error!)],
        ]),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(key: const ValueKey('waive-save'),
            onPressed: _reason.text.trim().isEmpty || _busy ? null : _save, child: Text(tr('Waive'))),
      ],
    );
  }
}

// ------------------------------------------------------------------ closure

class _ClosureTab extends StatefulWidget {
  final _CoverSchool school;
  const _ClosureTab({required this.school});

  @override
  State<_ClosureTab> createState() => _ClosureTabState();
}

class _ClosureTabState extends State<_ClosureTab> {
  late DateTime _date = _clamp(DateTime.now());
  bool _wholeSchool = true;
  final Set<String> _sections = {};
  final _reason = TextEditingController();
  bool _busy = false;
  String? _error;
  Map<String, dynamic>? _result;

  DateTime _clamp(DateTime d) {
    final first = DateTime.parse(widget.school.start), last = DateTime.parse(widget.school.end);
    return d.isBefore(first) ? first : (d.isAfter(last) ? last : d);
  }

  @override
  void dispose() {
    _reason.dispose();
    super.dispose();
  }

  String get _who => _wholeSchool
      ? tr('the whole school')
      : ([for (final id in _sections) widget.school.sectionLabel(id)]..sort()).join(', ');

  Future<void> _close() async {
    final sure = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${tr('Close')} ${_day(isoDate(_date))} ${tr('for')} $_who?'),
        content: Text(_wholeSchool
            ? tr('Every period that day becomes a period owed, cover booked for it is cancelled, '
                'the day goes on the calendar as a holiday and lesson plans move past it.')
            : tr('These classes\' periods that day become periods owed and their lesson plans move past it. '
                'The calendar keeps the day for everyone else.')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(tr('Cancel'))),
          FilledButton(key: const ValueKey('closure-confirm'), onPressed: () => Navigator.pop(context, true),
              child: Text(tr('Close the day'))),
        ],
      ),
    );
    if (sure != true) return;
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
    });
    try {
      final r = await Ops.post('$_base/academic-years/${widget.school.yearId}/closures', body: {
        'date': isoDate(_date),
        'reason': _reason.text.trim(),
        if (!_wholeSchool) 'sectionIds': (_sections.toList()..sort()),
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
    final school = widget.school;
    final ready = _reason.text.trim().isNotEmpty && (_wholeSchool || _sections.isNotEmpty) && !_busy;
    final r = _result;
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text(tr('A day lost at short notice (rain, an event, an exam hall), or found out after the fact.'),
          style: theme.textTheme.bodySmall),
      const Gap(12),
      Align(
        alignment: Alignment.centerLeft,
        child: OutlinedButton.icon(
          key: const ValueKey('closure-date'),
          icon: const Icon(Icons.calendar_today_outlined),
          label: Text(_day(isoDate(_date))),
          style: phoneTapTarget(context),
          onPressed: () async {
            final d = await showDatePicker(context: context, initialDate: _date,
                firstDate: DateTime.parse(school.start), lastDate: DateTime.parse(school.end));
            if (d != null) setState(() => _date = d);
          },
        ),
      ),
      const Gap(12),
      SegmentedButton<bool>(
        key: const ValueKey('closure-scope'),
        segments: [
          ButtonSegment(value: true, label: Text(tr('Whole school'))),
          ButtonSegment(value: false, label: Text(tr('Some classes'))),
        ],
        selected: {_wholeSchool},
        style: phoneSegmentTapTarget(context),
        onSelectionChanged: (v) => setState(() => _wholeSchool = v.first),
      ),
      if (!_wholeSchool && school.sections.isEmpty) ...[
        const Gap(8),
        Text(tr('The school has no sections yet.'), style: theme.textTheme.bodyMedium),
      ],
      if (!_wholeSchool) ...[
        const Gap(8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final s in school.sections)
            FilterChip(
              key: ValueKey('closure-section-${s['id']}'),
              label: Text(school.sectionLabel(s['id'] as String)),
              selected: _sections.contains(s['id']),
              onSelected: (v) => setState(() => v ? _sections.add(s['id'] as String) : _sections.remove(s['id'])),
            ),
        ]),
      ],
      const Gap(12),
      TextField(
        key: const ValueKey('closure-reason'),
        controller: _reason,
        maxLength: 200,
        decoration: InputDecoration(labelText: tr('Reason'), hintText: tr('Heavy rain')),
        onChanged: (_) => setState(() {}),
      ),
      Text(_wholeSchool
          ? tr('Every period that day becomes a period owed and the day goes on the calendar as a holiday.')
          : tr('Only these classes lose the day; the calendar keeps it for everyone else.'),
          style: theme.textTheme.bodySmall),
      const Gap(12),
      Align(
        alignment: Alignment.centerLeft,
        child: FilledButton(key: const ValueKey('closure-save'), onPressed: ready ? _close : null,
            style: phoneTapTarget(context), child: Text(tr('Close the day'))),
      ),
      if (_busy) ...[const Gap(12), const LinearProgressIndicator()],
      if (_error != null) ...[
        const Gap(12),
        Notice(kind: NoticeKind.danger, title: tr('The day was not closed.'), lines: [_error!]),
      ],
      if (r != null) ...[
        const Gap(12),
        Notice(
          key: const ValueKey('closure-result'),
          kind: NoticeKind.success,
          title: '${r['lostPeriods']} ${tr('periods are now owed.')}',
          lines: [
            if (r['holidayAdded'] == true) tr('The day is on the calendar as a holiday.'),
            '${r['plansReflowed']} ${tr('lesson plans moved past the day.')}',
          ],
        ),
      ],
    ]);
  }
}

// ------------------------------------------------------------------ the year

class _YearTab extends StatefulWidget {
  final _CoverSchool school;
  const _YearTab({required this.school});

  @override
  State<_YearTab> createState() => _YearTabState();
}

class _YearTabState extends State<_YearTab> {
  late Future<Map<String, dynamic>> _future = _load();

  Future<Map<String, dynamic>> _load() => Ops.map('$_base/academic-years/${widget.school.yearId}/cover-summary',
      query: {'from': widget.school.start, 'to': widget.school.end});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final school = widget.school;
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) {
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Notice(kind: NoticeKind.danger, title: serverErrorMessage(snap.error!),
                action: OutlinedButton(onPressed: () => setState(() { _future = _load(); }),
                    child: Text(tr('Try again')))),
          );
        }
        final s = snap.data!;
        final debt = (s['debt'] as List).cast<Map>().toList()
          ..sort((a, b) => school.sectionLabel(a['sectionId'] as String).compareTo(school.sectionLabel(b['sectionId'] as String)));
        final figures = [
          (tr('Cover asked for'), s['substitutionsRequested']),
          (tr('Filled'), s['filled']),
          (tr('Supervised'), s['supervised']),
          (tr('Unfilled'), s['unfilled']),
          (tr('Periods lost'), s['lost']),
          (tr('Made up'), s['compensated']),
          (tr('Still owed'), s['owed']),
        ];
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text('${tr('Cover and lost periods from')} ${school.start} ${tr('to')} ${school.end}.',
              style: theme.textTheme.bodySmall),
          const Gap(12),
          Wrap(spacing: 12, runSpacing: 12, children: [
            for (final (label, value) in figures)
              SizedBox(
                width: 150,
                child: AppCard(
                  margin: EdgeInsets.zero,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('$value', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600)),
                    Text(label, style: theme.textTheme.bodySmall),
                  ]),
                ),
              ),
          ]),
          const Gap(16),
          Text(tr('By section and subject'), style: theme.textTheme.titleSmall),
          const Gap(4),
          if (debt.isEmpty) Text(tr('No period has been lost this year.'), style: theme.textTheme.bodyMedium),
          for (final d in debt)
            Padding(
              key: ValueKey('debt-${d['sectionId']}-${d['subjectId']}'),
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(children: [
                Expanded(child: Text('${school.sectionLabel(d['sectionId'] as String)} · '
                    '${school.subjectName(d['subjectId'] as String)}')),
                Text('${d['owed']} ${tr('owed')} · ${d['compensated']} ${tr('made up')} · ${d['waived']} ${tr('waived')}',
                    style: theme.textTheme.bodySmall),
              ]),
            ),
        ]);
      },
    );
  }
}
