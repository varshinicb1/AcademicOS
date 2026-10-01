import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/owner_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/shell.dart';
import 'ops_api.dart';
import 'strings.dart';

/// An owner's schools side by side (ROLE-4): each linked school's term at a
/// glance -- papers set, syllabus taught against plan, cover filled -- as
/// numbers only. Opening a school makes the session that school's principal,
/// with its own pages and nothing of the others'.
class OwnerOverviewPage extends StatefulWidget {
  const OwnerOverviewPage({super.key});

  @override
  State<OwnerOverviewPage> createState() => _OwnerOverviewPageState();
}

class _OwnerOverviewPageState extends State<OwnerOverviewPage> {
  late Future<Map<String, dynamic>> _future = Ops.map('/owner/overview');
  void _reload() => setState(() { _future = Ops.map('/owner/overview'); });

  Future<void> _open(String schoolId) async {
    try {
      await OwnerSession.choose(schoolId);
      if (mounted) context.go('/school');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _link() async {
    final code = TextEditingController();
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Link another school'),
      content: SizedBox(width: 420, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text("Enter the owner link code that school's principal gave you. It works once."),
        const SizedBox(height: 8),
        TextField(key: const Key('owner-link-code'), controller: code, autofocus: true,
            decoration: const InputDecoration(labelText: 'Owner link code', hintText: 'own_...')),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Link')),
      ],
    ));
    if (ok != true || code.text.trim().isEmpty) return;
    try {
      final school = await OwnerSession.redeem(code.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Linked ${(school['name'] as String?) ?? school['schoolId']}.')));
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  static String _count(Object? n) => n == null ? '–' : '$n';

  Widget _metric(BuildContext context, String label, String value, [String? detail]) {
    final theme = Theme.of(context);
    return SizedBox(
      width: 170,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(value, style: theme.textTheme.headlineSmall),
        Text(label, style: theme.textTheme.bodySmall),
        if (detail != null) Text(detail, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
      ]),
    );
  }

  Widget _school(BuildContext context, Map<String, dynamic> s) {
    final theme = Theme.of(context);
    final pace = s['syllabusPacePct'];
    final cover = s['coverFilledPct'];
    return AppCard(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text((s['name'] as String?) ?? (s['schoolId'] as String), style: theme.textTheme.titleMedium)),
          FilledButton.tonal(onPressed: () => _open(s['schoolId'] as String), child: const Text('Open')),
        ]),
        if (s['period'] != null)
          Text('${s['period']} · ${s['periodStart']} to ${s['periodEnd']}', style: theme.textTheme.bodySmall),
        const SizedBox(height: 12),
        Wrap(spacing: 16, runSpacing: 12, children: [
          _metric(context, 'papers set this term', _count(s['papersThisTerm'])),
          _metric(context, 'syllabus taught against plan', pace == null ? '–' : '$pace%',
              s['syllabusPlanned'] == null ? null : '${s['syllabusTaught']} of ${s['syllabusPlanned']} lessons'
                  '${(s['rowsBehind'] ?? 0) > 0 ? ' · ${s['rowsBehind']} behind' : ''}'),
          _metric(context, 'cover filled', cover == null ? '–' : '$cover%',
              s['coverRequested'] == null ? null : '${s['coverFilled']} of ${s['coverRequested']} requests'),
        ]),
        if (s['note'] != null) ...[
          const SizedBox(height: 8),
          Text(s['note'] as String, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        ],
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: const Text('Your schools'), actions: [
        IconButton(tooltip: 'Refresh', icon: const Icon(Icons.refresh), onPressed: _reload),
      ]),
      floatingActionButton: FloatingActionButton.extended(
          onPressed: _link, icon: const Icon(Icons.add_link), label: const Text('Link another school')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          final schools = ((snap.data!['schools'] as List?) ?? const [])
              .map((e) => Map<String, dynamic>.from(e as Map)).toList();
          if (schools.isEmpty) {
            return const EmptyState(icon: Icons.domain_disabled_outlined, title: 'No schools linked',
                message: "Ask a school's principal for an owner link code, then link it here.");
          }
          return ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 96), children: [
            Text('Each school on its own: its numbers this term. Open a school to work in it as its principal.',
                style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 12),
            for (final s in schools) _school(context, s),
          ]);
        },
      ),
    );
  }
}

/// The principal's owner access (ROLE-4), on Staff and access: link an owner
/// over several schools with a code shown once, see who holds owner access,
/// and end it. An owner acts in the school with a principal's rights.
class OwnerLinksCard extends StatefulWidget {
  const OwnerLinksCard({super.key});

  @override
  State<OwnerLinksCard> createState() => _OwnerLinksCardState();
}

class _OwnerLinksCardState extends State<OwnerLinksCard> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/owner-links');
  void _reload() => setState(() { _future = Ops.list('/owner-links'); });

  Future<void> _create() async {
    final label = TextEditingController();
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Link an owner'),
      content: SizedBox(width: 440, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('An owner runs several schools from one account. Once linked, they can open this school '
            "with a principal's rights and see its numbers beside their other schools. Nothing of this school "
            'is shown inside another. You can end their access at any time.'),
        const SizedBox(height: 8),
        TextField(controller: label, decoration: const InputDecoration(labelText: 'Who is it for?')),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Create code')),
      ],
    ));
    if (ok != true) return;
    try {
      final link = Map<String, dynamic>.from(await Ops.post('/owner-links', body: {'label': label.text.trim()}) as Map);
      if (!mounted) return;
      final code = link['code'] as String;
      await showDialog<void>(context: context, builder: (ctx) => AlertDialog(
        title: const Text('Copy the code now'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('It is shown this once and works once, until ${(link['expiresAt'] as String).substring(0, 10)}. '
              'The owner enters it under Create account (or Link another school if they already have an account).'),
          const SizedBox(height: 8),
          SelectableText(code, style: const TextStyle(fontFamily: 'monospace')),
        ]),
        actions: [
          TextButton(onPressed: () => Clipboard.setData(ClipboardData(text: code)), child: const Text('Copy')),
          FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
        ],
      ));
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _revoke(Map<String, dynamic> link) async {
    final linked = link['status'] == 'linked';
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: Text(linked ? "End ${link['ownerName'] ?? 'this owner'}'s access?" : 'Withdraw this code?'),
      content: Text(linked
          ? 'They lose this school at once, on their next click. Their other schools are not affected.'
          : 'The code stops working. No one has used it yet.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
          onPressed: () => Navigator.pop(ctx, true),
          child: Text(linked ? 'End access' : 'Withdraw'),
        ),
      ],
    ));
    if (ok != true) return;
    try {
      await Ops.delete('/owner-links/${link['id']}');
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  static String _describe(Map<String, dynamic> l) {
    final who = (l['label'] as String?)?.isNotEmpty == true ? '${l['label']} · ' : '';
    switch (l['status']) {
      case 'linked':
        return '$who${l['ownerName']} (${l['ownerEmail']}) · linked ${(l['redeemedAt'] as String).substring(0, 10)}';
      case 'open':
        return '${who}code ${l['codeHint']}… · not used yet · expires ${(l['expiresAt'] as String).substring(0, 10)}';
      case 'expired':
        return '${who}code ${l['codeHint']}… · expired unused';
      default:
        return '$who${l['ownerName'] ?? 'code ${l['codeHint']}…'} · ended ${((l['revokedAt'] as String?) ?? '').split('T').first}';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      key: const Key('owner-links-card'),
      margin: const EdgeInsets.only(bottom: 16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text('Owner access', style: theme.textTheme.titleSmall)),
          TextButton.icon(onPressed: _create, icon: const Icon(Icons.add_link), label: const Text('Link an owner')),
        ]),
        Text('An owner of several schools, with a principal\'s rights here.', style: theme.textTheme.bodySmall),
        FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Padding(padding: EdgeInsets.all(8), child: LinearProgressIndicator());
            }
            if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
            final links = snap.data!.where((l) => l['status'] == 'linked' || l['status'] == 'open').toList();
            if (links.isEmpty) {
              return Padding(padding: const EdgeInsets.only(top: 8),
                  child: Text('No owner is linked.', style: theme.textTheme.bodySmall));
            }
            return Column(children: [
              for (final l in links)
                ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(l['status'] == 'linked' ? Icons.domain : Icons.pending_outlined),
                  title: Text(_describe(l)),
                  trailing: TextButton(onPressed: () => _revoke(l),
                      child: Text(l['status'] == 'linked' ? 'End access' : 'Withdraw')),
                ),
            ]);
          },
        ),
      ]),
    );
  }
}
