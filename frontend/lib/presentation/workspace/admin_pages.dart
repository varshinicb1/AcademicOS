import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../core/download/pdf_saver.dart';

import '../../data/datasources/api/api_error.dart';
import '../../core/session/current_session.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';
import 'package:academicos/core/theme/app_theme.dart';
import '../shared/widgets/shell.dart';

/// Papers waiting for review (EX-6): the reviewer approves one for the
/// principal or sends it back with what to change.
class ReviewsPage extends StatefulWidget {
  const ReviewsPage({super.key});

  @override
  State<ReviewsPage> createState() => _ReviewsPageState();
}

class _ReviewsPageState extends State<ReviewsPage> {
  String _state = 'pending';
  late Future<List<Map<String, dynamic>>> _future = _fetch();

  Future<List<Map<String, dynamic>>> _fetch() => Ops.list('/paper-reviews', query: {'state': _state});

  Future<void> _decide(Map<String, dynamic> r, String decision) async {
    String? comment;
    if (decision == 'changes') {
      final c = TextEditingController();
      final ok = await showDialog<bool>(context: context, builder: (_) => AlertDialog(
        title: const Text('What should change?'),
        content: TextField(controller: c, minLines: 3, maxLines: 6, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(tr('Cancel'))),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Send back')),
        ],
      ));
      if (ok != true) return;
      comment = c.text.trim();
    }
    try {
      await Ops.post('/assessments/${r['assessmentId']}/review-decision',
          body: {'decision': decision, if (comment != null) 'comment': comment});
      setState(() { _future = _fetch(); });
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Paper reviews')), actions: [
        SegmentedButton<String>(
          segments: const [ButtonSegment(value: 'pending', label: Text('Waiting')),
            ButtonSegment(value: '', label: Text('All'))],
          selected: {_state},
          onSelectionChanged: (s) => setState(() {
            _state = s.first;
            _future = _fetch();
          }),
        ),
        const SizedBox(width: 12),
      ]),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: snap.error.toString());
          if (snap.data!.isEmpty) {
            return const EmptyState(icon: Icons.rate_review_outlined, title: 'Nothing to review',
                message: 'Papers a colleague sends you for review appear here.');
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final r in snap.data!)
              AppCard(
                margin: const EdgeInsets.only(bottom: 10),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Text(r['title'], style: Theme.of(context).textTheme.titleSmall)),
                    ChipTag(label: r['state']),
                  ]),
                  if (r['requestNote'] != null) Text('Note: ${r['requestNote']}'),
                  if (r['comment'] != null) Text('Review: ${r['comment']}'),
                  Text('Reviewer: ${r['reviewerName']} · asked ${(r['requestedAt'] as String).substring(0, 10)}',
                      style: Theme.of(context).textTheme.bodySmall),
                  if (r['state'] == 'pending')
                    Wrap(spacing: 8, children: [
                      TextButton(onPressed: () => context.push('/assessment/${r['assessmentId']}'),
                          child: const Text('Open paper')),
                      if (r['reviewerId'] == CurrentSession.userId || CurrentSession.role == 'principal') ...[
                        OutlinedButton(onPressed: () => _decide(r, 'changes'), child: const Text('Ask for changes')),
                        FilledButton(onPressed: () => _decide(r, 'approve'),
                            // The principal's approval is the final one: it locks the paper.
                            child: Text(CurrentSession.role == 'principal'
                                ? 'Approve and lock' : 'Approve for principal')),
                      ],
                    ]),
                ]),
              ),
          ]);
        },
      ),
    );
  }
}

/// Bulk import and export (M1.6, INT-3): paste a CSV or choose a .csv or
/// Excel file, see every row's outcome before anything is written, then
/// apply. Templates and exports copy as CSV or download as Excel.
class ImportPage extends StatefulWidget {
  const ImportPage({super.key});

  @override
  State<ImportPage> createState() => _ImportPageState();
}

class _ImportPageState extends State<ImportPage> {
  static const _kinds = ['sections', 'teachers', 'students', 'parents', 'allocations', 'holidays'];
  static const _exports = ['sections', 'people', 'allocations', 'holidays', 'timetable'];
  String _kind = 'sections';
  final _csv = TextEditingController();
  // A chosen Excel workbook, sent as it is; editing the text box drops it.
  Uint8List? _xlsx;
  String? _fileName;
  Map<String, dynamic>? _result;
  String? _error;
  bool _busy = false;

  Future<void> _run({required bool apply}) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final r = await Ops.post('/admin/import/$_kind',
          body: _xlsx != null ? {'xlsx': base64Encode(_xlsx!)} : {'csv': _csv.text},
          query: {'dryRun': (!apply).toString()});
      setState(() => _result = Map<String, dynamic>.from(r as Map));
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    } finally {
      setState(() => _busy = false);
    }
  }

  Future<void> _choose() async {
    try {
      final picked = await FilePicker.pickFiles(type: FileType.custom, allowedExtensions: ['csv', 'xlsx']);
      if (picked == null || picked.files.isEmpty) return;
      final f = picked.files.single;
      final bytes = await f.readAsBytes();
      setState(() {
        _result = null;
        _fileName = f.name;
        if (f.name.toLowerCase().endsWith('.xlsx')) {
          _xlsx = bytes;
          _csv.clear();
        } else {
          _xlsx = null;
          _csv.text = utf8.decode(bytes, allowMalformed: true);
        }
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _download(String path, String name) async {
    try {
      final bytes = await Ops.bytes(path, query: {'format': 'xlsx'});
      await GetIt.I<PdfSaver>().save(bytes, '$name.xlsx');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _copy(String path, String what) async {
    try {
      final text = await Ops.get(path);
      await Clipboard.setData(ClipboardData(text: text.toString()));
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$what copied as CSV')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final r = _result;
    final counts = r == null ? null : Map<String, dynamic>.from(r['counts'] as Map);
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Import & export'))),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const SectionHeader(title: 'Import', subtitle: 'Nothing is written until you apply. People get invites, never accounts.'),
        Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          DropdownButton<String>(value: _kind, items: [for (final k in _kinds) DropdownMenuItem(value: k, child: Text(k))],
              onChanged: (v) => setState(() {
                    _kind = v!;
                    _result = null;
                  })),
          TextButton.icon(onPressed: () => _copy('/admin/import/$_kind/template', 'Template'),
              icon: const Icon(Icons.copy), label: const Text('Copy template')),
          TextButton.icon(onPressed: () => _download('/admin/import/$_kind/template', '$_kind-template'),
              icon: const Icon(Icons.grid_on_outlined), label: const Text('Excel template')),
          OutlinedButton.icon(onPressed: _busy ? null : _choose,
              icon: const Icon(Icons.upload_file), label: const Text('Choose a .csv or Excel file')),
        ]),
        if (_xlsx != null)
          ListTile(
            leading: const Icon(Icons.grid_on_outlined),
            title: Text('Excel file: $_fileName'),
            subtitle: const Text('Its first sheet is imported, in the same columns as the template.'),
            trailing: IconButton(tooltip: 'Remove', icon: const Icon(Icons.close),
                onPressed: () => setState(() { _xlsx = null; _fileName = null; _result = null; })),
          )
        else
          TextField(controller: _csv, minLines: 8, maxLines: 20, style: const TextStyle(fontFamily: 'monospace'),
              decoration: const InputDecoration(hintText: 'Paste CSV here, header first')),
        const SizedBox(height: 8),
        Wrap(spacing: 8, children: [
          OutlinedButton(onPressed: _busy ? null : () => _run(apply: false), child: const Text('Check')),
          FilledButton(onPressed: _busy || r == null || counts!['error'] != 0 || r['applied'] == true
              ? null : () => _run(apply: true), child: const Text('Apply')),
        ]),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 8),
            child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
        if (r != null) ...[
          const SizedBox(height: 12),
          Text(r['applied'] == true
              ? 'Imported: ${counts!['ok']} done, ${counts['skip']} already there.'
              : '${counts!['ok']} to do · ${counts['skip']} already there · ${counts['error']} to fix'),
          for (final row in (r['rows'] as List).cast<Map>())
            ListTile(
              dense: true,
              leading: Icon(switch (row['status']) { 'ok' => Icons.check_circle, 'skip' => Icons.remove_circle_outline, _ => Icons.error },
                  color: switch (row['status']) { 'ok' => AppColors.success, 'skip' => theme.disabledColor, _ => theme.colorScheme.error }),
              title: Text('Row ${row['row']}: ${row['message']}'),
              subtitle: row['inviteCode'] != null ? SelectableText('Invite code: ${row['inviteCode']}') : null,
            ),
        ],
        const SizedBox(height: 24),
        const SectionHeader(title: 'Export', subtitle: 'In the import columns, so an edited export imports back.'),
        for (final k in _exports)
          ListTile(
            dense: true,
            title: Text(k),
            trailing: Wrap(spacing: 8, children: [
              TextButton(onPressed: () => _copy('/admin/export/$k', k), child: const Text('Copy CSV')),
              TextButton(onPressed: () => _download('/admin/export/$k', k), child: const Text('Excel')),
            ]),
          ),
      ]),
    );
  }
}

/// Question-bank API keys (D38): mint (shown once), list, revoke. A key can
/// be limited to some classes and subjects (API-3); the server then serves it
/// only those, and refuses a request for any other with a 403.
class ApiKeysPage extends StatefulWidget {
  const ApiKeysPage({super.key});

  @override
  State<ApiKeysPage> createState() => _ApiKeysPageState();
}

class _ApiKeysPageState extends State<ApiKeysPage> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/api-keys');
  void _reload() => setState(() { _future = Ops.list('/api-keys'); });

  // Only the scopes a route checks. `papers:create` and `curriculum:read`
  // gated nothing and the server now refuses them as "not available yet"
  // (N-67-10), so offering them would only produce an error.
  static const _scopes = ['questions:read', 'facets:read'];

  Future<void> _mint() async {
    final label = TextEditingController();
    final subjects = TextEditingController();
    final scopes = <String>{..._scopes};
    final grades = <int>{};
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
      title: const Text('New API key'),
      content: SizedBox(width: 460, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        TextField(controller: label, decoration: const InputDecoration(labelText: 'Who is it for?')),
        for (final s in _scopes)
          CheckboxListTile(dense: true, value: scopes.contains(s), title: Text(s),
              onChanged: (on) => set(() => on == true ? scopes.add(s) : scopes.remove(s))),
        const SizedBox(height: 8),
        const Text('Only these classes (none ticked: every class)'),
        Wrap(spacing: 4, children: [
          for (var g = 1; g <= 12; g++)
            FilterChip(label: Text('$g'), selected: grades.contains(g),
                onSelected: (on) => set(() => on ? grades.add(g) : grades.remove(g))),
        ]),
        TextField(controller: subjects, decoration: const InputDecoration(
            labelText: 'Only these subjects (optional)', hintText: 'e.g. Science, Mathematics')),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: scopes.isEmpty ? null : () => Navigator.pop(ctx, true), child: const Text('Create')),
      ],
    )));
    if (ok != true) return;
    final onlySubjects = subjects.text.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
    try {
      final k = await Ops.post('/api-keys', body: {'label': label.text.trim().isEmpty ? 'Unnamed' : label.text.trim(),
        'scopes': scopes.toList(),
        if (grades.isNotEmpty) 'grades': grades.toList()..sort(),
        if (onlySubjects.isNotEmpty) 'subjects': onlySubjects});
      if (!mounted) return;
      await showDialog(context: context, builder: (_) => AlertDialog(
        title: const Text('Copy the key now'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('It is shown this once. Send it as the X-API-Key header.'),
          const SizedBox(height: 8),
          SelectableText(k['key'] as String, style: const TextStyle(fontFamily: 'monospace')),
        ]),
        actions: [
          TextButton(onPressed: () => Clipboard.setData(ClipboardData(text: k['key'] as String)), child: const Text('Copy')),
          FilledButton(onPressed: () => Navigator.pop(context), child: const Text('Done')),
        ],
      ));
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  /// " · classes 9, 10 · Science", or nothing for a key with no limits.
  static String _limitsText(Map<String, dynamic> k) {
    final grades = (k['grades'] as List?) ?? const [];
    final subjects = (k['subjects'] as List?) ?? const [];
    return [
      if (grades.isNotEmpty) ' · classes ${grades.join(', ')}',
      if (subjects.isNotEmpty) ' · ${subjects.join(', ')}',
    ].join();
  }

  /// The key's requests per minute over the last few minutes, the same count
  /// its quota is enforced on (`GET /api-keys/{id}/usage`).
  Future<void> _showUsage(Map<String, dynamic> k) async {
    List<Map<String, dynamic>> rows;
    try {
      rows = await Ops.list('/api-keys/${k['id']}/usage');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      return;
    }
    if (!mounted) return;
    final total = rows.fold<int>(0, (s, r) => s + (r['count'] as num).toInt());
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${k['label']} · usage'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(rows.isEmpty
              ? 'No requests in the last few minutes. Last used ${k['lastUsedAt'] ?? 'never'}.'
              : '$total requests in the last few minutes; the quota is ${k['quotaPerMinute']} a minute.'),
          const SizedBox(height: 8),
          for (final r in rows) Text('${r['windowStart']}: ${r['count']}'),
        ]),
        actions: [TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Close'))],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('API keys'))),
      floatingActionButton: FloatingActionButton.extended(onPressed: _mint, icon: const Icon(Icons.key), label: const Text('New key')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: snap.error.toString(), onRetry: _reload);
          if (snap.data!.isEmpty) {
            return const EmptyState(icon: Icons.key_off, title: 'No keys',
                message: 'A key lets a partner app search and fetch questions from your question bank.');
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final k in snap.data!)
              ListTile(
                // N-67-10: the principal sees what a key is used for, not only that it exists.
                onTap: () => _showUsage(k),
                title: Text('${k['label']} · ${k['prefix']}…'),
                subtitle: Text('${(k['scopes'] as List).join(', ')}${_limitsText(k)} · '
                    'last used ${k['lastUsedAt'] ?? 'never'} · tap for usage'),
                trailing: k['active'] == true
                    ? TextButton(
                        onPressed: () async {
                          await Ops.delete('/api-keys/${k['id']}');
                          _reload();
                        },
                        child: const Text('Revoke'))
                    : const ChipTag(label: 'Revoked'),
              ),
          ]);
        },
      ),
    );
  }
}

/// Staff permissions (M1.4): the principal makes a teacher an admin for one
/// area -- leave and cover, exams, people, the timetable -- for the whole
/// school or only some classes, and takes it back.
class GrantsPage extends StatefulWidget {
  const GrantsPage({super.key});

  @override
  State<GrantsPage> createState() => _GrantsPageState();
}

class _GrantsPageState extends State<GrantsPage> {
  late Future<(List<Map<String, dynamic>>, List<Map<String, dynamic>>, List<Map<String, dynamic>>)> _future = _load();
  List<Map<String, dynamic>> _left = const [];

  Future<(List<Map<String, dynamic>>, List<Map<String, dynamic>>, List<Map<String, dynamic>>)> _load() async {
    final teachers = await Ops.list('/auth/users', query: {'role': 'teacher'});
    final grants = await Ops.list('/admin/grants');
    final mine = await Ops.map('/my-grants');
    final caps = (mine['available'] as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
    // The accounts the school has closed, so one closed by mistake can be reopened.
    _left = await Ops.list('/auth/users', query: {'role': 'left'});
    return (teachers, grants, caps);
  }

  /// Someone has left the school: their sign-in stops working at once and
  /// their admin access ends; their papers, marks and history stay (N-67-8).
  Future<void> _close(Map<String, dynamic> person) async {
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: Text("Close ${person['name']}'s account?"),
      content: const Text('Use this when someone has left the school. They are signed out everywhere and '
          'cannot sign in again, and any admin access they had ends. Their papers, marks and history '
          'stay. You can reopen the account later.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
          onPressed: () => Navigator.pop(ctx, true),
          child: const Text('Close account'),
        ),
      ],
    ));
    if (ok != true) return;
    try {
      await Ops.post('/auth/users/${person['id']}/close');
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _reopen(Map<String, dynamic> person) async {
    try {
      await Ops.post('/auth/users/${person['id']}/reopen');
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  void _reload() => setState(() { _future = _load(); });

  Future<void> _grant(Map<String, dynamic> teacher, List<Map<String, dynamic>> caps) async {
    String? cap;
    final grades = <int>{};
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
      title: Text('Make ${teacher['name']} an admin'),
      content: SizedBox(width: 460, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        RadioGroup<String>(
          groupValue: cap,
          onChanged: (v) => set(() => cap = v),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            for (final c in caps)
              RadioListTile<String>(dense: true, value: c['capability'] as String, title: Text(c['label'] as String)),
          ]),
        ),
        const SizedBox(height: 8),
        const Text('Only for these classes (none ticked: the whole school)'),
        const SizedBox(height: 2),
        Text("An admin limited to some classes acts only on those classes' sections. "
            'School-wide pages and actions stay with you.',
            style: Theme.of(ctx).textTheme.bodySmall),
        Wrap(spacing: 4, children: [
          for (var g = 1; g <= 12; g++)
            FilterChip(label: Text('$g'), selected: grades.contains(g),
                onSelected: (on) => set(() => on ? grades.add(g) : grades.remove(g))),
        ]),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: cap == null ? null : () => Navigator.pop(ctx, true), child: const Text('Grant')),
      ],
    )));
    if (ok != true) return;
    try {
      await Ops.post('/admin/grants', body: {'userId': teacher['id'], 'capability': cap,
        if (grades.isNotEmpty) 'scope': {'grades': grades.toList()..sort()}});
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Staff permissions'))),
      body: FutureBuilder(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: snap.error.toString(), onRetry: _reload);
          final (teachers, grants, caps) = snap.data!;
          if (teachers.isEmpty) {
            return const EmptyState(icon: Icons.people_outline, title: 'No teachers yet',
                message: 'Invite teachers first; then you can make any of them an admin for one area.');
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final t in teachers)
              AppCard(
                margin: const EdgeInsets.only(bottom: 10),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Text(t['name'], style: Theme.of(context).textTheme.titleSmall)),
                    TextButton.icon(onPressed: () => _grant(t, caps), icon: const Icon(Icons.add), label: const Text('Grant')),
                    PopupMenuButton<String>(
                      tooltip: 'More for ${t['name']}',
                      onSelected: (_) => _close(t),
                      itemBuilder: (_) => const [
                        PopupMenuItem(value: 'close', child: Text('Close account (left the school)')),
                      ],
                    ),
                  ]),
                  Wrap(spacing: 6, runSpacing: 4, children: [
                    for (final g in grants.where((g) => g['userId'] == t['id']))
                      InputChip(
                        label: Text(((g['scope'] as Map)['grades'] as List?) == null
                            ? g['label'].toString().split(':').first
                            : '${g['label'].toString().split(':').first} (classes ${((g['scope'] as Map)['grades'] as List).join(', ')})'),
                        onDeleted: () async {
                          await Ops.delete('/admin/grants/${g['id']}');
                          _reload();
                        },
                      ),
                  ]),
                ]),
              ),
            if (_left.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text('Closed accounts', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              for (final person in _left)
                AppCard(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: Row(children: [
                    Expanded(child: Text(person['name'] as String)),
                    TextButton(onPressed: () => _reopen(person), child: const Text('Reopen')),
                  ]),
                ),
            ],
          ]);
        },
      ),
    );
  }
}
