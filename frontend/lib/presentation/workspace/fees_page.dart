import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../core/download/pdf_saver.dart';
import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/shell.dart';
import 'dashboard_card.dart' show friendlyDate;
import 'ops_api.dart';
import 'strings.dart';

/// Whole paise as "Rs 1,500" or "Rs 1,500.50", grouped the Indian way.
String formatRupees(int paise) {
  final r = paise ~/ 100, p = paise % 100;
  final digits = '$r';
  String grouped;
  if (digits.length <= 3) {
    grouped = digits;
  } else {
    final head = digits.substring(0, digits.length - 3);
    final tail = digits.substring(digits.length - 3);
    final parts = <String>[];
    for (var i = head.length; i > 0; i -= 2) {
      parts.insert(0, head.substring(i - 2 < 0 ? 0 : i - 2, i));
    }
    grouped = '${parts.join(',')},$tail';
  }
  return 'Rs $grouped${p == 0 ? '' : '.${p.toString().padLeft(2, '0')}'}';
}

String feeStatusLabel(String s) => switch (s) {
      'paid' => tr('Paid'),
      'part_paid' => tr('Part paid'),
      'due' => tr('Due'),
      'overdue' => tr('Overdue'),
      _ => s,
    };

const _methods = ['cash', 'upi', 'bank', 'cheque', 'other'];

String _methodLabel(String m) => switch (m) {
      'cash' => tr('Cash'),
      'upi' => 'UPI',
      'bank' => tr('Bank transfer'),
      'cheque' => tr('Cheque'),
      _ => tr('Other'),
    };

/// One student's fees (FEE-1): each fee, what is paid and still owed, and
/// the receipts. [path] is the student's own, a parent's child's, or the
/// school's view of one student.
class FeeStatementView extends StatefulWidget {
  final String path;
  /// The school's view: a button to record a payment.
  final bool canRecord;
  const FeeStatementView({super.key, required this.path, this.canRecord = false});

  @override
  State<FeeStatementView> createState() => _FeeStatementViewState();
}

class _FeeStatementViewState extends State<FeeStatementView> {
  late Future<Map<String, dynamic>> _future = Ops.map(widget.path);

  void _reload() => setState(() => _future = Ops.map(widget.path));

  Future<void> _record(Map<String, dynamic> s) async {
    final saved = await showDialog<bool>(context: context, builder: (_) => _PaymentDialog(statement: s));
    if (saved == true && mounted) _reload();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final s = snap.data!;
        final theme = Theme.of(context);
        final rows = (s['rows'] as List).cast<Map>();
        final receipts = (s['receipts'] as List).cast<Map>();
        if (rows.isEmpty && receipts.isEmpty) {
          return EmptyState(icon: Icons.receipt_long_outlined, title: tr('No fees yet'),
              message: tr('Fees appear here once the school sets them for this class.'));
        }
        final overdue = s['overduePaise'] as int;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text('${formatRupees(s['balancePaise'] as int)} ${tr('to pay')}', style: theme.textTheme.headlineSmall),
          if (overdue > 0)
            Text('${formatRupees(overdue)} ${tr('overdue')}', style: TextStyle(color: theme.colorScheme.error)),
          Text('${tr('Paid so far')}: ${formatRupees(s['paidPaise'] as int)}'
              '${(s['concessionPaise'] as int) > 0 ? ' · ${tr('Concession')}: ${formatRupees(s['concessionPaise'] as int)}' : ''}',
              style: theme.textTheme.bodyMedium),
          if (widget.canRecord) ...[
            const SizedBox(height: 12),
            Align(alignment: Alignment.centerLeft, child: FilledButton.icon(
              key: const ValueKey('record-payment'),
              onPressed: rows.isEmpty ? null : () => _record(s),
              icon: const Icon(Icons.add_card_outlined),
              label: Text(tr('Record a payment')),
            )),
          ],
          SectionHeader(title: tr('Fees')),
          for (final r in rows)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text('${(r['head'] as Map)['name']}'),
              subtitle: Text('${formatRupees((r['head'] as Map)['amountPaise'] as int)} · ${tr('due')} '
                  '${friendlyDate('${(r['head'] as Map)['dueDate']}')}'
                  '${(r['balancePaise'] as int) > 0 ? ' · ${formatRupees(r['balancePaise'] as int)} ${tr('left')}' : ''}'),
              trailing: ChipTag(label: feeStatusLabel('${r['status']}')),
            ),
          if (receipts.isNotEmpty) ...[
            SectionHeader(title: tr('Receipts')),
            for (final p in receipts)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.receipt_outlined),
                title: Text('${tr('Receipt')} ${p['receiptNo']} · ${formatRupees(p['amountPaise'] as int)}'),
                subtitle: Text([
                  '${p['feeHeadName']}',
                  friendlyDate('${p['paidOn']}'),
                  _methodLabel('${p['method']}'),
                  if ('${p['reference']}'.isNotEmpty) '${p['reference']}',
                ].join(' · ')),
              ),
          ],
        ]);
      },
    );
  }
}

class _PaymentDialog extends StatefulWidget {
  final Map<String, dynamic> statement;
  const _PaymentDialog({required this.statement});

  @override
  State<_PaymentDialog> createState() => _PaymentDialogState();
}

class _PaymentDialogState extends State<_PaymentDialog> {
  String? _head, _error;
  String _method = 'cash';
  final _amount = TextEditingController(), _reference = TextEditingController();
  bool _saving = false;

  List<Map> get _rows => (widget.statement['rows'] as List).cast<Map>();

  @override
  void initState() {
    super.initState();
    final open = _rows.where((r) => (r['balancePaise'] as int) > 0).toList();
    if (open.isNotEmpty) _pick('${(open.first['head'] as Map)['id']}');
  }

  void _pick(String id) {
    _head = id;
    final row = _rows.firstWhere((r) => (r['head'] as Map)['id'] == id);
    final left = row['balancePaise'] as int;
    _amount.text = left > 0 ? '${left ~/ 100}' : '';
  }

  @override
  void dispose() {
    _amount.dispose();
    _reference.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final rupees = double.tryParse(_amount.text.trim().replaceAll(',', ''));
    if (_head == null || rupees == null || rupees <= 0) {
      setState(() => _error = tr('Choose the fee and enter the amount received, in rupees.'));
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await Ops.post('/fees/payments', body: {
        'studentId': widget.statement['studentId'], 'feeHeadId': _head, 'amountPaise': (rupees * 100).round(),
        'method': _method, 'reference': _reference.text.trim(),
      });
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${tr('Record a payment')}: ${widget.statement['studentName']}'),
      content: SizedBox(width: 420, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        DropdownButtonFormField<String>(
          key: const ValueKey('payment-fee'),
          initialValue: _head,
          decoration: InputDecoration(labelText: tr('Fee')),
          items: [
            for (final r in _rows)
              DropdownMenuItem(value: '${(r['head'] as Map)['id']}', child: Text('${(r['head'] as Map)['name']}')),
          ],
          onChanged: (v) => v == null ? null : setState(() => _pick(v)),
        ),
        TextField(
          key: const ValueKey('payment-amount'),
          controller: _amount,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(labelText: tr('Amount received (rupees)')),
        ),
        DropdownButtonFormField<String>(
          initialValue: _method,
          decoration: InputDecoration(labelText: tr('Paid by')),
          items: [for (final m in _methods) DropdownMenuItem(value: m, child: Text(_methodLabel(m)))],
          onChanged: (v) => setState(() => _method = v ?? 'cash'),
        ),
        TextField(
          controller: _reference,
          maxLength: 80,
          decoration: InputDecoration(labelText: tr('Reference (cheque or transaction number)')),
        ),
        if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
      ]))),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(tr('Cancel'))),
        FilledButton(key: const ValueKey('save-payment'), onPressed: _saving ? null : _save, child: Text(tr('Save'))),
      ],
    );
  }
}

/// The signed-in student's own fees.
class MyFeesPage extends StatelessWidget {
  const MyFeesPage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: destinationAppBar(context, title: Text(tr('My fees'))),
        body: const FeeStatementView(path: '/my-fees'),
      );
}

/// The school's fees (FEE-1): the year's fees per class, and each class's
/// dues, from which a student's statement opens to record a payment.
class FeesAdminPage extends StatefulWidget {
  const FeesAdminPage({super.key});

  @override
  State<FeesAdminPage> createState() => _FeesAdminPageState();
}

class _FeesAdminPageState extends State<FeesAdminPage> {
  String? _year, _section, _error;
  Map<String, String> _sections = const {};
  List<int> _grades = const [];
  List<Map<String, dynamic>>? _heads, _dues;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
      if (years.isEmpty) throw OpsError(409, 'Your school has no academic year set up yet.');
      years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
      final year = years.last['id'] as String;
      final sections = await Ops.list('/curriculum/academic-years/$year/sections');
      final heads = await Ops.list('/fees/heads', query: {'academicYearId': year});
      final labels = {for (final s in sections) s['id'] as String: '${s['gradeNumber']}-${s['name']}'};
      final ids = labels.keys.toList()..sort((a, b) => labels[a]!.compareTo(labels[b]!));
      if (!mounted) return;
      setState(() {
        _year = year;
        _sections = {for (final id in ids) id: labels[id]!};
        _grades = {for (final s in sections) s['gradeNumber'] as int}.toList()..sort();
        _heads = heads;
      });
      if (ids.isNotEmpty) _openSection(ids.first);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _openSection(String id) async {
    setState(() {
      _section = id;
      _dues = null;
    });
    try {
      final d = await Ops.list('/fees/sections/$id');
      if (mounted && _section == id) setState(() => _dues = d);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _addHead() async {
    final year = _year;
    if (year == null) return;
    final added = await showDialog<bool>(context: context, builder: (_) => _HeadDialog(yearId: year, grades: _grades));
    if (added == true && mounted) _load();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: destinationAppBar(context, title: Text(tr('Fees')),
            bottom: TabBar(isScrollable: true, tabs: [
              Tab(text: tr('School')),
              Tab(text: tr('Dues by class')),
              Tab(text: tr('Fees per class')),
            ])),
        body: _error != null
            ? ErrorDisplay(message: _error!, onRetry: () {
                setState(() => _error = null);
                _load();
              })
            : _heads == null
                ? const LoadingIndicator()
                : TabBarView(children: [
                    const FeesOverviewView(),
                    ListView(padding: const EdgeInsets.all(16), children: [
                      Wrap(spacing: 8, runSpacing: 8, children: [
                        for (final e in _sections.entries)
                          ChoiceChip(label: Text(e.value), selected: _section == e.key, onSelected: (_) => _openSection(e.key)),
                      ]),
                      const SizedBox(height: 12),
                      if (_section != null && _dues == null) const SizedBox(height: 120, child: LoadingIndicator()),
                      if (_dues != null && _dues!.isEmpty) Text(tr('No students in this class yet.')),
                      for (final d in _dues ?? const <Map<String, dynamic>>[])
                        ListTile(
                          key: ValueKey('dues-${d['studentId']}'),
                          contentPadding: EdgeInsets.zero,
                          title: Text('${d['name']}'),
                          subtitle: Text('${formatRupees(d['balancePaise'] as int)} ${tr('to pay')}'
                              '${(d['overduePaise'] as int) > 0 ? ' · ${formatRupees(d['overduePaise'] as int)} ${tr('overdue')}' : ''}'),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () async {
                            await Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => Scaffold(
                                appBar: AppBar(title: Text('${d['name']}')),
                                body: FeeStatementView(path: '/fees/students/${d['studentId']}', canRecord: true))));
                            if (mounted && _section != null) _openSection(_section!);
                          },
                        ),
                    ]),
                    ListView(padding: const EdgeInsets.all(16), children: [
                      Align(alignment: Alignment.centerLeft, child: FilledButton.icon(
                        key: const ValueKey('add-fee'),
                        onPressed: _addHead,
                        icon: const Icon(Icons.add),
                        label: Text(tr('Add a fee')),
                      )),
                      if (_heads!.isEmpty)
                        Padding(padding: const EdgeInsets.only(top: 12),
                            child: Text(tr('No fees set for this year yet.'), style: theme.textTheme.bodyMedium)),
                      for (final h in _heads!)
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text('${h['name']}'),
                          subtitle: Text('${h['grade'] == null ? tr('Every class') : '${tr('Class')} ${h['grade']}'} · '
                              '${formatRupees(h['amountPaise'] as int)} · ${tr('due')} ${friendlyDate('${h['dueDate']}')}'),
                        ),
                    ]),
                  ]),
      ),
    );
  }
}

class _HeadDialog extends StatefulWidget {
  final String yearId;
  final List<int> grades;
  const _HeadDialog({required this.yearId, required this.grades});

  @override
  State<_HeadDialog> createState() => _HeadDialogState();
}

class _HeadDialogState extends State<_HeadDialog> {
  final _name = TextEditingController(), _amount = TextEditingController();
  int? _grade;
  DateTime? _due;
  String? _error;
  bool _saving = false;

  @override
  void dispose() {
    _name.dispose();
    _amount.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final rupees = double.tryParse(_amount.text.trim().replaceAll(',', ''));
    if (_name.text.trim().isEmpty || rupees == null || rupees <= 0 || _due == null) {
      setState(() => _error = tr('Give the fee a name, an amount in rupees and a due date.'));
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await Ops.post('/fees/heads', body: {
        'academicYearId': widget.yearId, 'grade': _grade, 'name': _name.text.trim(),
        'amountPaise': (rupees * 100).round(), 'dueDate': isoDate(_due!),
      });
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(tr('Add a fee')),
      content: SizedBox(width: 420, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(key: const ValueKey('fee-name'), controller: _name, maxLength: 80,
            decoration: InputDecoration(labelText: tr('Name, e.g. Tuition, term 1'))),
        DropdownButtonFormField<int?>(
          initialValue: _grade,
          decoration: InputDecoration(labelText: tr('Class')),
          items: [
            DropdownMenuItem<int?>(value: null, child: Text(tr('Every class'))),
            for (final g in widget.grades) DropdownMenuItem<int?>(value: g, child: Text('${tr('Class')} $g')),
          ],
          onChanged: (v) => setState(() => _grade = v),
        ),
        TextField(key: const ValueKey('fee-amount'), controller: _amount,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(labelText: tr('Amount (rupees)'))),
        const SizedBox(height: 8),
        Align(alignment: Alignment.centerLeft, child: OutlinedButton.icon(
          onPressed: () async {
            final now = DateTime.now();
            final picked = await showDatePicker(context: context, initialDate: _due ?? now,
                firstDate: DateTime(now.year - 1), lastDate: DateTime(now.year + 2));
            if (picked != null) setState(() => _due = picked);
          },
          icon: const Icon(Icons.event_outlined),
          label: Text(_due == null ? tr('Due date') : friendlyDate(isoDate(_due!))),
        )),
        if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
      ]))),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(tr('Cancel'))),
        FilledButton(key: const ValueKey('save-fee'), onPressed: _saving ? null : _save, child: Text(tr('Save'))),
      ],
    );
  }
}

/// The year's fees across the school (FEE-1 oversight): billed, collected
/// and owed, each class, and the students with an overdue balance, largest
/// first, with the full list as an Excel file.
class FeesOverviewView extends StatefulWidget {
  const FeesOverviewView({super.key});

  @override
  State<FeesOverviewView> createState() => _FeesOverviewViewState();
}

class _FeesOverviewViewState extends State<FeesOverviewView> {
  Map<String, dynamic>? _data;
  String? _error;
  bool _downloading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final d = await Ops.map('/fees/overview');
      if (mounted) setState(() => _data = d);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _download() async {
    setState(() => _downloading = true);
    try {
      final bytes = await Ops.bytes('/fees/defaulters/export', query: {'format': 'xlsx'});
      await GetIt.I<PdfSaver>().save(bytes, 'fee-defaulters.xlsx');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
      }
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (_error != null) {
      return ErrorDisplay(message: _error!, onRetry: () {
        setState(() => _error = null);
        _load();
      });
    }
    final d = _data;
    if (d == null) return const LoadingIndicator();
    final classes = (d['classes'] as List).cast<Map>();
    final late = (d['defaulters'] as List).cast<Map>();
    final pct = d['collectedPercent'] as num?;
    Widget figure(String label, int paise, {bool alert = false}) => Padding(
          padding: const EdgeInsets.only(right: 24, bottom: 8),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
            Text(label, style: theme.textTheme.bodySmall),
            Text(formatRupees(paise), style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600, color: alert && paise > 0 ? theme.colorScheme.error : null)),
          ]),
        );
    return ListView(key: const ValueKey('fees-overview'), padding: const EdgeInsets.all(16), children: [
      Text(tr('This year so far'), style: theme.textTheme.titleMedium),
      const SizedBox(height: 8),
      Wrap(children: [
        figure(tr('Billed'), (d['totalPaise'] as int) - (d['concessionPaise'] as int)),
        figure(tr('Collected'), d['paidPaise'] as int),
        figure(tr('To collect'), d['balancePaise'] as int),
        figure(tr('Overdue'), d['overduePaise'] as int, alert: true),
      ]),
      if (pct != null) Text('${pct.toStringAsFixed(pct % 1 == 0 ? 0 : 1)}% ${tr('collected')}'),
      const SizedBox(height: 16),
      Row(children: [
        Expanded(child: Text('${tr('Overdue')}: ${d['defaultersTotal']} ${tr('students')}',
            style: theme.textTheme.titleSmall)),
        if ((d['defaultersTotal'] as int) > 0)
          TextButton.icon(
            key: const ValueKey('download-defaulters'),
            onPressed: _downloading ? null : _download,
            icon: const Icon(Icons.download_outlined),
            label: Text(tr('Excel')),
          ),
      ]),
      if (late.isEmpty)
        Text(tr('Nobody has an overdue fee.'), style: theme.textTheme.bodySmall),
      for (final x in late)
        ListTile(
          dense: true,
          contentPadding: EdgeInsets.zero,
          title: Text('${x['name']}'),
          subtitle: Text('${x['sectionName']} · ${(x['overdueHeads'] as List).join(', ')}'),
          trailing: Text(formatRupees(x['overduePaise'] as int),
              style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.error)),
        ),
      const SizedBox(height: 16),
      Text(tr('By class'), style: theme.textTheme.titleSmall),
      for (final c in classes)
        ListTile(
          dense: true,
          contentPadding: EdgeInsets.zero,
          title: Text('${c['sectionName']}'),
          subtitle: Text('${formatRupees(c['paidPaise'] as int)} ${tr('collected')} · '
              '${formatRupees(c['balancePaise'] as int)} ${tr('to pay')}'),
          trailing: (c['studentsOverdue'] as int) > 0
              ? Text('${c['studentsOverdue']} ${tr('overdue')}', style: TextStyle(color: theme.colorScheme.error))
              : null,
        ),
    ]);
  }
}
