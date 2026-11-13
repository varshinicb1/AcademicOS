import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../core/download/pdf_saver.dart';

import '../../data/datasources/api/api_error.dart';
import '../../core/session/current_session.dart';
import '../admin/widgets/password_reset.dart';
import '../shared/readable.dart';
import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/copyable_value.dart';
import 'ops_api.dart';
import 'owner_pages.dart';
import 'strings.dart';
import 'package:academicos/core/theme/app_theme.dart';
import '../shared/widgets/shell.dart';

/// Papers waiting for review (EX-6): the reviewer approves one for the
/// principal or sends it back with what to change. The principal's "Waiting"
/// also holds the papers a colleague approved for them (the server marks
/// those rows `awaitingPrincipal`), each with the "Approve & lock" that is
/// the last step.
class ReviewsPage extends StatefulWidget {
  const ReviewsPage({super.key});

  @override
  State<ReviewsPage> createState() => _ReviewsPageState();
}

/// The words a review's state is shown in on its chip, never the wire value.
String reviewStateLabel(Map<String, dynamic> r) => switch (r['state']) {
      'pending' => 'Waiting',
      'approved' when r['awaitingPrincipal'] == true => 'Approved by reviewer',
      'approved' => 'Approved',
      'changes_requested' => 'Changes asked',
      'withdrawn' => 'Withdrawn',
      final s => '$s',
    };

class _ReviewsPageState extends State<ReviewsPage> {
  String _state = 'pending';
  late Future<List<Map<String, dynamic>>> _future = _fetch();
  final Set<String> _busy = {};

  Future<List<Map<String, dynamic>>> _fetch() => Ops.list('/paper-reviews', query: {'state': _state});

  void _reload() => setState(() {
        _future = _fetch();
      });

  Future<void> _decide(Map<String, dynamic> r, String decision) async {
    String? comment;
    if (decision == 'changes') {
      comment = await showDialog<String>(context: context, builder: (_) => const _ChangesDialog());
      if (comment == null || !mounted) return;
    }
    await _run(r, () async {
      await Ops.post('/assessments/${r['assessmentId']}/review-decision',
          body: {'decision': decision, if (comment != null) 'comment': comment});
      return decision == 'changes'
          ? tr('Sent back to the author with your comments')
          : CurrentSession.role == 'principal'
              ? trf('Approved and locked: {title}', {'title': r['title']})
              : tr('Approved; the principal has been told');
    });
  }

  /// The principal's approval of a paper a colleague approved for them:
  /// it locks the paper (PATCH /assessments/{id}/approve).
  Future<void> _approveAndLock(Map<String, dynamic> r) => _run(r, () async {
        await Ops.patch('/assessments/${r['assessmentId']}/approve');
        return trf('Approved and locked: {title}', {'title': r['title']});
      });

  /// Runs one decision on [r], says what happened and reloads the list, or
  /// shows the server's reason when it refused.
  Future<void> _run(Map<String, dynamic> r, Future<String> Function() action) async {
    final id = '${r['id']}';
    setState(() => _busy.add(id));
    try {
      final done = await action();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(done)));
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } finally {
      if (mounted) setState(() => _busy.remove(id));
    }
  }

  @override
  Widget build(BuildContext context) {
    final principal = CurrentSession.role == 'principal';
    final toggle = SegmentedButton<String>(
      segments: [ButtonSegment(value: 'pending', label: Text(tr('Waiting'))),
        ButtonSegment(value: '', label: Text(tr('All')))],
      selected: {_state},
      onSelectionChanged: (s) => setState(() {
        _state = s.first;
        _future = _fetch();
      }),
    );
    // On a phone the toggle sits under the title: beside it, it left the title no room at all.
    final narrow = MediaQuery.sizeOf(context).width < 600;
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Paper reviews')),
          actions: narrow ? null : [toggle, const SizedBox(width: 12)],
          bottom: narrow
              ? PreferredSize(preferredSize: const Size.fromHeight(52),
                  child: Padding(padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                      child: Align(alignment: Alignment.centerLeft, child: toggle)))
              : null),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          if (snap.data!.isEmpty) {
            return EmptyState(icon: Icons.rate_review_outlined, title: tr('Nothing to review'),
                message: tr(principal
                    ? 'Papers sent to you for review, and papers a colleague approved for you, appear here.'
                    : 'Papers a colleague sends you for review appear here.'));
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            for (final r in snap.data!) _row(context, r, principal),
          ]);
        },
      ),
    );
  }

  Widget _row(BuildContext context, Map<String, dynamic> r, bool principal) {
    final theme = Theme.of(context);
    final busy = _busy.contains('${r['id']}');
    final pending = r['state'] == 'pending';
    // A colleague approved it for the principal; the paper is not locked yet.
    final awaitingPrincipal = r['state'] == 'approved' && r['awaitingPrincipal'] == true;
    final decides = r['reviewerId'] == CurrentSession.userId || principal;
    final asked = '${r['requestedAt'] ?? ''}';
    return AppCard(
      key: ValueKey('review-${r['id']}'),
      margin: const EdgeInsets.only(bottom: 10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text('${r['title']}', style: theme.textTheme.titleSmall)),
          ChipTag(label: tr(reviewStateLabel(r))),
        ]),
        if (r['requestNote'] != null) Text(trf('Note: {note}', {'note': r['requestNote']})),
        if (r['comment'] != null) Text(trf('Review: {comment}', {'comment': r['comment']})),
        Text(trf('Reviewer: {name} · asked {date}',
                {'name': r['reviewerName'], 'date': asked.length >= 10 ? readableDate(asked.substring(0, 10)) : asked}),
            style: theme.textTheme.bodySmall),
        if (awaitingPrincipal && principal)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(trf('{name} approved it for you. Approving locks the paper.', {'name': r['reviewerName']}),
                style: theme.textTheme.bodySmall),
          ),
        if (pending || awaitingPrincipal)
          Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
            TextButton(
                // The paper page can approve or lock it too: the list is
                // read again on the way back.
                onPressed: () => context.push('/assessment/${r['assessmentId']}').then((_) {
                      if (mounted) _reload();
                    }),
                child: Text(tr('Open paper'))),
            if (pending && decides) ...[
              OutlinedButton(onPressed: busy ? null : () => _decide(r, 'changes'),
                  child: Text(tr('Ask for changes'))),
              FilledButton(onPressed: busy ? null : () => _decide(r, 'approve'),
                  // The principal's approval is the final one: it locks the paper.
                  child: Text(tr(principal ? 'Approve & lock' : 'Approve for principal'))),
            ],
            if (awaitingPrincipal && principal)
              FilledButton.icon(
                key: ValueKey('approve-lock-${r['id']}'),
                onPressed: busy ? null : () => _approveAndLock(r),
                icon: const Icon(Icons.verified),
                label: Text(tr('Approve & lock')),
              ),
            if (busy) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
          ]),
      ]),
    );
  }
}

/// Asks the reviewer what should change, and pops with the comment. It pops
/// with its own context: popping with the reviews page's closed the page
/// behind it and left this open, so nothing was ever sent (QA P-08).
class _ChangesDialog extends StatefulWidget {
  const _ChangesDialog();

  @override
  State<_ChangesDialog> createState() => _ChangesDialogState();
}

class _ChangesDialogState extends State<_ChangesDialog> {
  final _comment = TextEditingController();

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final text = _comment.text.trim();
    return AlertDialog(
      title: Text(tr('What should change?')),
      content: SizedBox(
        width: 420,
        child: TextField(
          key: const ValueKey('review-comment'),
          controller: _comment,
          minLines: 3,
          maxLines: 6,
          autofocus: true,
          decoration: InputDecoration(
            labelText: tr('What should change?'),
            hintText: tr('What the author should fix before it is approved'),
          ),
          onChanged: (_) => setState(() {}),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        // The server refuses an empty comment ("say what to change").
        FilledButton(
          onPressed: text.isEmpty ? null : () => Navigator.pop(context, text),
          child: Text(tr('Send back')),
        ),
      ],
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
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(trf('{what} copied as CSV', {'what': tr(what)}))));
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
        SectionHeader(title: tr('Import'), subtitle: tr('Nothing is written until you apply. People get invites, never accounts.')),
        Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          DropdownButton<String>(value: _kind, items: [for (final k in _kinds) DropdownMenuItem(value: k, child: Text(tr(k)))],
              onChanged: (v) => setState(() {
                    _kind = v!;
                    _result = null;
                  })),
          TextButton.icon(onPressed: () => _copy('/admin/import/$_kind/template', 'Template'),
              icon: const Icon(Icons.copy), label: Text(tr('Copy template'))),
          TextButton.icon(onPressed: () => _download('/admin/import/$_kind/template', '$_kind-template'),
              icon: const Icon(Icons.grid_on_outlined), label: Text(tr('Excel template'))),
          OutlinedButton.icon(onPressed: _busy ? null : _choose,
              icon: const Icon(Icons.upload_file), label: Text(tr('Choose a .csv or Excel file'))),
        ]),
        if (_xlsx != null)
          ListTile(
            leading: const Icon(Icons.grid_on_outlined),
            title: Text(trf('Excel file: {name}', {'name': _fileName})),
            subtitle: Text(tr('Its first sheet is imported, in the same columns as the template.')),
            trailing: IconButton(tooltip: tr('Remove'), icon: const Icon(Icons.close),
                onPressed: () => setState(() { _xlsx = null; _fileName = null; _result = null; })),
          )
        else
          TextField(controller: _csv, minLines: 8, maxLines: 20, style: const TextStyle(fontFamily: 'monospace'),
              decoration: InputDecoration(hintText: tr('Paste CSV here, header first'))),
        const SizedBox(height: 8),
        Wrap(spacing: 8, children: [
          OutlinedButton(onPressed: _busy ? null : () => _run(apply: false), child: Text(tr('Check'))),
          FilledButton(onPressed: _busy || r == null || counts!['error'] != 0 || r['applied'] == true
              ? null : () => _run(apply: true), child: Text(tr('Apply import'))),
        ]),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 8),
            child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
        if (r != null) ...[
          const SizedBox(height: 12),
          Text(r['applied'] == true
              ? trf('Imported: {ok} done, {skip} already there.', {'ok': counts!['ok'], 'skip': counts['skip']})
              : trf('{ok} to do · {skip} already there · {error} to fix',
                  {'ok': counts!['ok'], 'skip': counts['skip'], 'error': counts['error']})),
          for (final row in (r['rows'] as List).cast<Map>())
            ListTile(
              dense: true,
              leading: Icon(switch (row['status']) { 'ok' => Icons.check_circle, 'skip' => Icons.remove_circle_outline, _ => Icons.error },
                  color: switch (row['status']) { 'ok' => AppColors.success, 'skip' => theme.disabledColor, _ => theme.colorScheme.error }),
              title: Text(trf('Row {n}: {message}', {'n': row['row'], 'message': row['message']})),
              subtitle: row['inviteCode'] != null ? SelectableText(trf('Invite code: {code}', {'code': row['inviteCode']})) : null,
            ),
        ],
        const SizedBox(height: 24),
        // "In the import columns, so an edited export imports back" was not
        // true of people: there is no people import, and the people export
        // pasted into the teachers import invited its students as teachers
        // (QA S-08). Each export now says how it goes back in, if it does.
        SectionHeader(title: tr('Export'),
            subtitle: tr('Sections, allocations and holidays export in their import\'s columns, so an edited '
                'file imports back.')),
        for (final k in _exports)
          ListTile(
            dense: true,
            title: Text(tr(k)),
            subtitle: switch (k) {
              'people' => Text(tr('One list with a role column. To import people, split it by role and '
                  'use the teachers, students or parents import for each part; a teachers import does '
                  'not take students or parents.')),
              'timetable' => Text(tr('For reading and printing. Change the timetable under Timetable.')),
              _ => null,
            },
            trailing: Wrap(spacing: 8, children: [
              TextButton(onPressed: () => _copy('/admin/export/$k', k), child: Text(tr('Copy CSV'))),
              TextButton(onPressed: () => _download('/admin/export/$k', k), child: Text(tr('Excel'))),
            ]),
          ),
      ]),
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
      title: Text(trf("Close {name}'s account?", {'name': person['name']})),
      content: Text(tr('Use this when someone has left the school. They are signed out everywhere and '
          'cannot sign in again, and any admin access they had ends. Their papers, marks and history '
          'stay. You can reopen the account later.')),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
          onPressed: () => Navigator.pop(ctx, true),
          child: Text(tr('Close account')),
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

  /// "Leave, attendance and substitutions (class 10)", or the area alone
  /// when it covers the whole school.
  static String _grantLabel(Map g) {
    final area = g['label'].toString().split(':').first;
    final grades = ((g['scope'] as Map?)?['grades'] as List?) ?? const [];
    return grades.isEmpty ? area : '$area (${classesLabel(grades)})';
  }

  /// Taking an admin area away is one tap on the chip's x, so it asks first
  /// and says what the teacher loses (QA S-18).
  Future<void> _revokeGrant(Map<String, dynamic> teacher, Map g) async {
    final ok = await confirmAction(context,
        title: trf('Take this away from {name}?', {'name': teacher['name']}),
        message: trf('{name} can no longer act as an admin for {area}. Their pages for it '
            'close at once. You can give it again with Grant.', {'name': teacher['name'], 'area': _grantLabel(g)}),
        confirmLabel: tr('Take it away'));
    if (!ok) return;
    try {
      await Ops.delete('/admin/grants/${g['id']}');
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _grant(Map<String, dynamic> teacher, List<Map<String, dynamic>> caps) async {
    String? cap;
    final grades = <int>{};
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
      title: Text(trf('Make {name} an admin', {'name': teacher['name']})),
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
        Text(tr('Only for these classes (none ticked: the whole school)')),
        const SizedBox(height: 2),
        Text(tr("An admin limited to some classes acts only on those classes' sections. "
            'School-wide pages and actions stay with you.'),
            style: Theme.of(ctx).textTheme.bodySmall),
        Wrap(spacing: 4, children: [
          for (var g = 1; g <= 12; g++)
            FilterChip(label: Text('$g'), selected: grades.contains(g),
                onSelected: (on) => set(() => on ? grades.add(g) : grades.remove(g))),
        ]),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: cap == null ? null : () => Navigator.pop(ctx, true), child: Text(tr('Grant'))),
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
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          final (teachers, grants, caps) = snap.data!;
          // ROLE-4: the school's own principal links an owner here. An owner
          // acting in the school does not: the server refuses it.
          final ownerAccess = CurrentSession.role == 'principal' && !CurrentSession.isOwner;
          if (teachers.isEmpty) {
            final none = EmptyState(icon: Icons.people_outline, title: tr('No teachers yet'),
                message: tr('Invite teachers first; then you can make any of them an admin for one area.'));
            if (!ownerAccess) return none;
            return ListView(padding: const EdgeInsets.all(16), children: [const OwnerLinksCard(), none]);
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            if (ownerAccess) const OwnerLinksCard(),
            for (final t in teachers)
              AppCard(
                margin: const EdgeInsets.only(bottom: 10),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Text(t['name'], style: Theme.of(context).textTheme.titleSmall)),
                    TextButton.icon(onPressed: () => _grant(t, caps), icon: const Icon(Icons.add), label: Text(tr('Grant'))),
                    PopupMenuButton<String>(
                      key: ValueKey('staff-more-${t['id']}'),
                      tooltip: trf('More for {name}', {'name': t['name']}),
                      onSelected: (choice) => choice == 'reset'
                          ? resetPasswordFlow(context, userId: t['id'] as String, name: t['name'] as String)
                          : _close(t),
                      itemBuilder: (_) => [
                        // A teacher who forgot their password (QA S-05).
                        if (canResetPasswords) PopupMenuItem(value: 'reset', child: Text(tr('Reset password'))),
                        PopupMenuItem(value: 'close', child: Text(tr('Close account (left the school)'))),
                      ],
                    ),
                  ]),
                  Wrap(spacing: 6, runSpacing: 4, children: [
                    for (final g in grants.where((g) => g['userId'] == t['id']))
                      InputChip(
                        label: Text(_grantLabel(g)),
                        deleteButtonTooltipMessage: tr('Take this away'),
                        onDeleted: () => _revokeGrant(t, g),
                      ),
                  ]),
                ]),
              ),
            if (_left.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(tr('Closed accounts'), style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              for (final person in _left)
                AppCard(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: Row(children: [
                    Expanded(child: Text(person['name'] as String)),
                    TextButton(onPressed: () => _reopen(person), child: Text(tr('Reopen'))),
                  ]),
                ),
            ],
          ]);
        },
      ),
    );
  }
}
