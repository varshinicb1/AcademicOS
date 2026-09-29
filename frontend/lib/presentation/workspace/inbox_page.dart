import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// The caller's notifications (NTF-1): newest first, unread marked, and the
/// settings -- quiet hours, language, and push/email per kind.
class InboxPage extends StatefulWidget {
  const InboxPage({super.key});

  @override
  State<InboxPage> createState() => _InboxPageState();
}

class _InboxPageState extends State<InboxPage> {
  late Future<Map<String, dynamic>> _future = Ops.map('/notifications');

  void _reload() => setState(() { _future = Ops.map('/notifications'); });

  Future<void> _open(Map<String, dynamic> n) async {
    if (n['read'] != true) {
      try {
        await Ops.send('POST', '/notifications/${n['id']}/read', label: 'Mark a notification read');
      } catch (_) {
        // not-a-failure: marking as read is a courtesy; opening the notification must not wait on it
      }
    }
    final link = n['link'] as String?;
    if (!mounted) return;
    _reload();
    final target = _route(link);
    if (target != null) context.push(target);
  }

  /// A notification's link names a server page; map the ones the web has.
  String? _route(String? link) {
    if (link == null) return null;
    if (link.startsWith('/my-homework')) return '/school${link.split('?').first}';
    if (link.startsWith('/homework/')) return '/school/homework';
    if (link.startsWith('/my-day') || link.startsWith('/cover')) return '/school/my-day';
    if (link.startsWith('/my-exams')) return '/school/my-exams';
    if (link.startsWith('/assessments/')) return '/school/reviews';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(tr('Notifications')), actions: [
        TextButton(
          onPressed: () async {
            final messenger = ScaffoldMessenger.of(context);
            try {
              await Ops.send('POST', '/notifications/read-all', label: 'Mark all notifications read');
              _reload();
            } catch (e) {
              messenger.showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
            }
          },
          child: Text(tr('Mark all read')),
        ),
        IconButton(
          tooltip: 'Settings',
          icon: const Icon(Icons.tune),
          onPressed: () => showDialog(context: context, builder: (_) => const _PreferencesDialog()),
        ),
      ]),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: snap.error.toString(), onRetry: _reload);
          final items = (snap.data!['items'] as List).cast<Map>();
          if (items.isEmpty) {
            return const EmptyState(icon: Icons.notifications_none, title: 'Nothing yet',
                message: 'Homework, cover duties, marks and exam news will appear here.');
          }
          return RefreshIndicator(
            onRefresh: () async => _reload(),
            child: ListView.separated(
              itemCount: items.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) {
                final n = Map<String, dynamic>.from(items[i]);
                final unread = n['read'] != true;
                return ListTile(
                  leading: Icon(unread ? Icons.circle : Icons.circle_outlined, size: 12,
                      color: unread ? theme.colorScheme.primary : theme.disabledColor),
                  title: Text(n['title'] ?? '', style: TextStyle(fontWeight: unread ? FontWeight.w600 : FontWeight.normal)),
                  subtitle: Text(n['body'] ?? ''),
                  trailing: Text(_when(n['createdAt'] as String?), style: theme.textTheme.bodySmall),
                  onTap: () => _open(n),
                );
              },
            ),
          );
        },
      ),
    );
  }

  String _when(String? iso) {
    final t = iso == null ? null : DateTime.tryParse(iso)?.toLocal();
    if (t == null) return '';
    final d = DateTime.now().difference(t);
    if (d.inMinutes < 1) return 'now';
    if (d.inHours < 1) return '${d.inMinutes}m';
    if (d.inDays < 1) return '${d.inHours}h';
    return '${t.day}/${t.month}';
  }
}

class _PreferencesDialog extends StatefulWidget {
  const _PreferencesDialog();

  @override
  State<_PreferencesDialog> createState() => _PreferencesDialogState();
}

class _PreferencesDialogState extends State<_PreferencesDialog> {
  Map<String, dynamic>? _prefs;
  String? _error;

  @override
  void initState() {
    super.initState();
    Ops.map('/notification-preferences').then((p) => setState(() => _prefs = p),
        onError: (e) => setState(() => _error = serverErrorMessage(e)));
  }

  Future<void> _save(Map<String, dynamic> body) async {
    try {
      final p = await Ops.put('/notification-preferences', body: body);
      setState(() {
        _prefs = Map<String, dynamic>.from(p as Map);
        _error = null;
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _pickTime(String field) async {
    final parts = (_prefs![field] as String).split(':');
    final t = await showTimePicker(context: context,
        initialTime: TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1])));
    if (t != null) {
      await _save({field: '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}'});
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = _prefs;
    return AlertDialog(
      title: const Text('Notification settings'),
      content: SizedBox(
        width: 520,
        child: p == null
            ? (_error != null ? Text(_error!) : const SizedBox(height: 80, child: LoadingIndicator()))
            : SingleChildScrollView(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Quiet hours'),
                    subtitle: const Text('No push notifications in this window; they arrive after it.'),
                    trailing: Wrap(spacing: 8, children: [
                      OutlinedButton(onPressed: () => _pickTime('quietStart'), child: Text('From ${p['quietStart']}')),
                      OutlinedButton(onPressed: () => _pickTime('quietEnd'), child: Text('To ${p['quietEnd']}')),
                    ]),
                  ),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Language'),
                    trailing: SegmentedButton<String>(
                      segments: const [ButtonSegment(value: 'en', label: Text('English')),
                        ButtonSegment(value: 'hi', label: Text('हिन्दी'))],
                      selected: {p['language'] as String},
                      onSelectionChanged: (s) => _save({'language': s.first}),
                    ),
                  ),
                  const Divider(),
                  for (final k in (p['kinds'] as List).cast<Map>())
                    Row(children: [
                      Expanded(child: Text(k['label'] as String)),
                      const Text('Push'),
                      Checkbox(value: k['push'] as bool,
                          onChanged: (v) => _save({'kinds': [{'kind': k['kind'], 'push': v}]})),
                      const Text('Email'),
                      Checkbox(value: k['email'] as bool,
                          onChanged: (v) => _save({'kinds': [{'kind': k['kind'], 'email': v}]})),
                    ]),
                ]),
              ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Done'))],
    );
  }
}
