import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// A question-bank API key's webhooks (API-6): the partner's HTTPS URL that
/// hears `questions.added` -- new questions, chapter by chapter, that the key
/// may read -- with the signing secret shown once, and each webhook's
/// delivery log (status, attempts, the receiver's last answer).
class WebhooksPage extends StatefulWidget {
  const WebhooksPage({super.key, required this.keyId, this.keyLabel = ''});

  final String keyId;
  final String keyLabel;

  @override
  State<WebhooksPage> createState() => _WebhooksPageState();
}

class _WebhooksPageState extends State<WebhooksPage> {
  late Future<List<Map<String, dynamic>>> _future = _load();
  final Map<String, Future<List<Map<String, dynamic>>>> _logs = {};

  String get _base => '/api-keys/${widget.keyId}/webhooks';

  Future<List<Map<String, dynamic>>> _load() => Ops.list(_base);

  void _reload() => setState(() {
        _future = _load();
        _logs.clear();
      });

  Future<void> _add() async {
    final url = TextEditingController();
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Add a webhook'),
      content: SizedBox(width: 480, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('The partner\'s HTTPS address. It is told when new questions this key may read are added, '
            'chapter by chapter: question ids only, never question text and never anything about a student.'),
        const SizedBox(height: 8),
        TextField(key: const Key('webhook-url'), controller: url, autofocus: true,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(labelText: 'URL', hintText: 'https://partner.example/acos-hook')),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Add')),
      ],
    ));
    if (ok != true || url.text.trim().isEmpty) return;
    try {
      final hook = Map<String, dynamic>.from(
          await Ops.post(_base, body: {'url': url.text.trim(), 'events': ['questions.added']}) as Map);
      if (!mounted) return;
      final secret = hook['secret'] as String;
      await showDialog<void>(context: context, builder: (ctx) => AlertDialog(
        title: const Text('Copy the signing secret now'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('It is shown this once. The partner checks the X-AcademicOS-Signature header of every '
              'delivery with it (docs/question-bank-api.md, "Webhooks").'),
          const SizedBox(height: 8),
          SelectableText(secret, style: const TextStyle(fontFamily: 'monospace')),
        ]),
        actions: [
          TextButton(onPressed: () => Clipboard.setData(ClipboardData(text: secret)), child: const Text('Copy')),
          FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
        ],
      ));
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  Future<void> _revoke(Map<String, dynamic> hook) async {
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Revoke this webhook?'),
      content: Text('${hook['url']} stops hearing from AcademicOS at once, and anything not yet delivered is cancelled.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
          onPressed: () => Navigator.pop(ctx, true),
          child: const Text('Revoke'),
        ),
      ],
    ));
    if (ok != true) return;
    try {
      await Ops.delete('$_base/${hook['id']}');
      _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  void _toggleLog(String hookId) => setState(() {
        if (_logs.containsKey(hookId)) {
          _logs.remove(hookId);
        } else {
          _logs[hookId] = Ops.list('$_base/$hookId/deliveries');
        }
      });

  /// "Science 10 · life-processes · 3 questions".
  static String _what(Map<String, dynamic> d) => [
        if (d['subject'] != null) '${d['subject']}${d['grade'] == null ? '' : ' ${d['grade']}'}',
        if (d['chapterId'] != null) d['chapterId'],
        '${d['questionCount']} question${d['questionCount'] == 1 ? '' : 's'}',
      ].join(' · ');

  static String _outcome(Map<String, dynamic> d) {
    final tries = '${d['attempts']} attempt${d['attempts'] == 1 ? '' : 's'}';
    switch (d['status']) {
      case 'delivered':
        return 'Delivered (${d['lastStatusCode']}) · $tries';
      case 'pending':
        return (d['attempts'] as num) == 0
            ? 'Waiting to send'
            : 'Retrying at ${(d['nextAttemptAt'] as String?)?.replaceFirst('T', ' ').substring(0, 16) ?? 'soon'} · $tries · ${d['lastError']}';
      case 'failed':
        return 'Failed · $tries · ${d['lastError']}';
      default:
        return 'Cancelled · ${d['lastError']}';
    }
  }

  Widget _log(BuildContext context, String hookId) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _logs[hookId],
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Padding(padding: EdgeInsets.all(8), child: LinearProgressIndicator());
        }
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: () => _toggleLog(hookId));
        if (snap.data!.isEmpty) {
          return const Padding(padding: EdgeInsets.all(8), child: Text('Nothing sent yet: an event is made when new questions are added.'));
        }
        return Column(children: [
          for (final d in snap.data!)
            ListTile(
              dense: true,
              leading: Icon(switch (d['status']) {
                'delivered' => Icons.check_circle_outline,
                'pending' => Icons.schedule,
                'failed' => Icons.error_outline,
                _ => Icons.block,
              }),
              title: Text(_what(d)),
              subtitle: Text('${(d['createdAt'] as String).replaceFirst('T', ' ').substring(0, 16)} · ${_outcome(d)}'),
            ),
        ]);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(widget.keyLabel.isEmpty ? 'Webhooks' : 'Webhooks · ${widget.keyLabel}')),
      floatingActionButton: FloatingActionButton.extended(
          onPressed: _add, icon: const Icon(Icons.webhook), label: const Text('Add webhook')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          if (snap.data!.isEmpty) {
            return const EmptyState(icon: Icons.webhook, title: 'No webhooks',
                message: 'A webhook tells a partner app when new questions it may read are added, '
                    'instead of it asking again and again.');
          }
          return ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 96), children: [
            for (final h in snap.data!)
              AppCard(
                margin: const EdgeInsets.only(bottom: 12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Text(h['url'] as String, style: theme.textTheme.titleSmall)),
                    if (h['active'] == true)
                      TextButton(onPressed: () => _revoke(h), child: const Text('Revoke'))
                    else
                      const ChipTag(label: 'Revoked'),
                  ]),
                  Text('${(h['events'] as List).join(', ')} · secret ${h['secretHint']}… · '
                      'added ${(h['createdAt'] as String).substring(0, 10)}', style: theme.textTheme.bodySmall),
                  TextButton.icon(
                    onPressed: () => _toggleLog(h['id'] as String),
                    icon: Icon(_logs.containsKey(h['id']) ? Icons.expand_less : Icons.expand_more),
                    label: const Text('Deliveries'),
                  ),
                  if (_logs.containsKey(h['id'])) _log(context, h['id'] as String),
                ]),
              ),
          ]);
        },
      ),
    );
  }
}
